---
schema_version: 3
title: tmpfs shmem Cgroup Memory Accounting
concept_id: operating-system/tmpfs-shmem-cgroup-memory-accounting
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- tmpfs-shmem-cgroup
- memory-accounting
- dev-shm-memory
- usage
aliases:
- tmpfs shmem cgroup memory accounting
- /dev/shm memory usage
- tmpfs not disk
- shmem page cache swap
- container shared memory limit
- tmpfs OOM
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/operating-system/oom-killer-cgroup-memory-pressure.md
- contents/operating-system/memory-high-vs-memory-max-cgroup-behavior.md
- contents/operating-system/cgroup-swap-controller-basics.md
- contents/operating-system/deleted-open-file-space-leak-log-rotation.md
- contents/operating-system/overlayfs-copy-up-container-layering-debugging.md
symptoms:
- /dev/shm이나 tmpfs 사용량이 disk가 아니라 cgroup memory limit을 압박한다.
- tmpfs file을 삭제했지만 open fd 때문에 memory accounting이 남는다.
- page cache와 swap policy를 함께 타는 memory-backed filesystem으로 해석해야 한다.
expected_queries:
- tmpfs는 디스크 대신 RAM이라는 말보다 cgroup memory accounting을 어떻게 봐야 해?
- /dev/shm 사용량이 container memory limit과 OOM에 영향을 줄 수 있어?
- tmpfs deleted-open file은 왜 memory pressure로 남을 수 있어?
- shmem, page cache, swap policy가 tmpfs에서 어떻게 연결돼?
contextual_chunk_prefix: |
  이 문서는 tmpfs를 단순 RAM disk가 아니라 cgroup memory limit 안에서 page cache와 swap policy를
  함께 타는 memory-backed filesystem으로 설명한다. /dev/shm, shmem, OOM, deleted-open file을 연결한다.
---
# tmpfs, shmem, /dev/shm, Cgroup Memory Accounting

> 한 줄 요약: tmpfs는 "디스크 대신 RAM" 정도로 끝나는 기능이 아니라, cgroup 메모리 한도 안에서 page cache와 swap 정책을 함께 타는 메모리성 파일 시스템이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [memory.high vs memory.max, Cgroup Behavior](./memory-high-vs-memory-max-cgroup-behavior.md)
> - [cgroup Swap Controller Basics](./cgroup-swap-controller-basics.md)
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - [Workingset Refault, Page Cache Reclaim, Runtime Debugging](./workingset-refault-page-cache-reclaim-debugging.md)
> - [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
> - [Deleted-but-Open Files, Log Rotation, Space Leak Debugging](./deleted-open-file-space-leak-log-rotation.md)

> retrieval-anchor-keywords: tmpfs, shmem, /dev/shm, shared memory, memory.current, memory.stat, shmem counter, tmpfs OOM, container tmpfs, swap-backed tmpfs, tmpfs reclaim

## 핵심 개념

tmpfs는 메모리 기반 파일 시스템이지만 "무료 RAM"이 아니다. tmpfs에 쓴 데이터는 커널 메모리 관리와 cgroup 메모리 accounting 안으로 들어오며, 설정과 환경에 따라 swap으로 밀릴 수도 있다.

- `tmpfs`: 메모리에 기반한 파일 시스템이다
- `shmem`: tmpfs와 공유 메모리 계열이 보이는 커널 accounting 관점이다
- `/dev/shm`: 많은 리눅스 환경에서 tmpfs로 마운트되는 대표 경로다
- `memory.current`: 현재 cgroup이 쓰는 메모리 총량을 보여준다
- `memory.stat`: 파일/익명 메모리/shmem 성격의 사용량을 더 세부적으로 보여준다

왜 중요한가:

- 임시 파일을 tmpfs에 쓰면 디스크 대신 메모리 압박으로 장애가 나타날 수 있다
- `/dev/shm` 크기가 작으면 브라우저 렌더링, IPC, local worker가 이상하게 실패할 수 있다
- tmpfs usage는 "파일"처럼 보여도 실제 운영 영향은 메모리 reclaim, swap, OOM으로 나타난다

## 깊이 들어가기

### 1. tmpfs는 디스크를 우회하지만 메모리 한도는 우회하지 못한다

애플리케이션 입장에서는 그냥 파일처럼 보이지만, tmpfs에 쓴 데이터는 결국 메모리 자원이다.

- 컨테이너의 `memory.current`를 올린다
- `memory.high`를 넘기면 reclaim 압박이 붙을 수 있다
- `memory.max`를 넘으면 OOM이나 allocation failure로 이어질 수 있다

즉 "디스크가 아니라 tmpfs에 쓰니 안전하다"가 아니라 "문제가 디스크가 아니라 메모리 쪽으로 이동한다"에 가깝다.

### 2. `/dev/shm`는 자주 보이지만 자주 과소평가된다

여러 런타임에서 `/dev/shm`는 IPC나 임시 버퍼를 위한 tmpfs다.

- headless browser 렌더링
- 멀티프로세스 worker 간 공유 메모리
- 이미지/문서 처리 라이브러리의 임시 버퍼
- `memfd_create()` 기반 local payload handoff

여기서 중요한 점은 `/tmp`와 `/dev/shm`를 같은 "임시 저장소"로 뭉뚱그리면 안 된다는 것이다. `/tmp`는 디스크일 수도 있지만 `/dev/shm`는 대개 메모리다.

### 3. tmpfs 파일도 삭제 타이밍이 즉시 회수와 같지 않다

tmpfs에 있는 파일도 일반 파일처럼 이름 삭제와 실제 자원 회수가 항상 같은 시점은 아니다.

- 파일을 unlink해도 열린 file descriptor가 남아 있을 수 있다
- mmap된 영역이 살아 있으면 메모리 회수가 늦을 수 있다
- "지웠는데 메모리가 안 줄어요"라는 상황이 생긴다

이때는 파일 이름이 아니라 open fd와 매핑 상태를 봐야 한다.

### 4. tmpfs는 page cache 경쟁과도 연결된다

tmpfs를 많이 쓰면 익명 메모리만 압박하는 것이 아니라, 같은 cgroup 안의 page cache working set과도 경쟁하게 된다.

- tmpfs 사용량이 커지면 hot file cache가 밀릴 수 있다
- refault가 늘고 API latency가 튈 수 있다
- swap이 허용되면 문제를 늦출 수 있지만, 지연은 더 나빠질 수 있다

그래서 tmpfs는 "빠른 임시 저장소"이면서 동시에 "메모리 구조를 바꾸는 선택"이다.

## 실전 시나리오

### 시나리오 1: 업로드 staging을 tmpfs로 옮겼더니 디스크 경보는 사라졌지만 컨테이너가 죽는다

가능한 원인:

- 큰 임시 파일이 `memory.current`를 직접 밀어 올린다
- `memory.high`를 자주 넘으며 reclaim이 심해진다
- `memory.max` 근처에서 OOMKilled가 난다

진단:

```bash
df -h /tmp /dev/shm
du -sh /dev/shm /tmp/myapp 2>/dev/null
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.events
cat /sys/fs/cgroup/memory.stat | rg 'file|shmem|anon'
```

판단 포인트:

- 디스크가 아니라 메모리 이벤트가 먼저 튀는가
- `shmem`이나 file 계열 usage가 임시 작업과 함께 증가하는가
- 업로드 완료 후에도 usage가 바로 안 내려가는가

### 시나리오 2: headless browser나 worker가 `/dev/shm` 관련 오류를 낸다

가능한 원인:

- `/dev/shm`가 너무 작다
- 병렬 worker 수가 공유 메모리 예산보다 많다
- 임시 렌더 버퍼가 예상보다 크다

대응 감각:

- `/dev/shm` 크기를 명시적으로 설계한다
- 병렬도를 tmpfs 예산과 같이 본다
- 정말 메모리 기반이어야 하는지 다시 본다

### 시나리오 3: 파일을 지웠는데 메모리 압박이 남는다

가능한 원인:

- 삭제된 tmpfs 파일을 프로세스가 아직 열고 있다
- mmap이 살아 있다
- 같은 cgroup의 다른 shmem 사용량이 남아 있다

진단:

```bash
lsof +L1 2>/dev/null | rg '/dev/shm|tmpfs'
ls -l /proc/<pid>/fd
cat /proc/<pid>/maps | rg '/dev/shm'
```

## 코드로 보기

### tmpfs 마운트 예시

```bash
mount -t tmpfs -o size=1g,nosuid,nodev tmpfs /mnt/app-tmp
```

### cgroup 메모리와 함께 보기

```bash
watch -n 1 'cat /sys/fs/cgroup/memory.current; echo; cat /sys/fs/cgroup/memory.stat | rg "file|shmem|anon"; echo; cat /sys/fs/cgroup/memory.events'
```

### 설계 감각

```text
heap                 -> GC/allocator 관점 메모리
page cache           -> 파일 I/O 성능 관점 메모리
tmpfs/shmem          -> 파일처럼 보이지만 메모리 한도에 직접 들어오는 저장소
swap                 -> 압박을 늦출 수 있지만 latency를 키울 수 있는 후퇴 공간
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| tmpfs | 빠르고 image/volume 오염이 적다 | 메모리 한도를 직접 먹고 재시작 시 사라진다 | 짧은 임시 버퍼 |
| 디스크 볼륨 | 메모리 압박이 덜하다 | I/O latency와 cleanup 비용이 든다 | 큰 임시 파일, 대용량 staging |
| heap 내부 버퍼 | 코드 흐름이 단순할 수 있다 | GC/native memory 압박이 커질 수 있다 | 아주 작은 임시 데이터 |
| swap 허용 | 급한 압박을 완충한다 | tail latency가 나빠질 수 있다 | burst 완화가 필요할 때 |

## 꼬리질문

> Q: tmpfs에 쓰면 디스크를 안 쓰니까 cgroup 메모리와 무관한가요?
> 핵심: 아니다. tmpfs는 메모리 기반 파일 시스템이므로 메모리 usage와 pressure에 직접 연결된다.

> Q: `/dev/shm`와 `/tmp`는 같은 의미인가요?
> 핵심: 아니다. `/dev/shm`는 보통 tmpfs이고, `/tmp`는 디스크일 수도 메모리일 수도 있다.

> Q: tmpfs 파일을 지우면 바로 메모리가 회수되나요?
> 핵심: 이름은 사라져도 열린 fd나 mmap이 남아 있으면 회수가 늦을 수 있다.

## 한 줄 정리

tmpfs는 빠른 임시 저장소이지만 운영적으로는 "파일 시스템"보다 "메모리 정책과 OOM 경로"로 읽어야 하는 자원이다.
