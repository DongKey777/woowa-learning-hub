---
schema_version: 3
title: Deleted Open File Space Leak Log Rotation
concept_id: operating-system/deleted-open-file-space-leak-log-rotation
canonical: true
category: operating-system
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 85
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- deleted-open-file
- space-leak-log
- rotation
- space-leak
aliases:
- deleted open file space leak
- lsof +L1
- log rotation inode still open
- unlinked file disk usage
- tmpfs deleted file leak
- proc pid fd deleted
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/o-cloexec-fd-inheritance-exec-leaks.md
- contents/operating-system/rename-atomicity-directory-fsync-crash-consistency.md
- contents/operating-system/tmpfs-shmem-cgroup-memory-accounting.md
- contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md
- contents/operating-system/sparse-file-fallocate-hole-punching.md
- contents/operating-system/subprocess-fd-hygiene-basics.md
symptoms:
- 파일을 삭제했는데 df 상 disk usage가 줄지 않는다.
- log rotation 후 application이 옛 inode를 계속 열고 있어 공간이 회수되지 않는다.
- tmpfs에서 deleted-but-open file 때문에 memory/cgroup usage가 계속 남는다.
expected_queries:
- 삭제한 파일인데 디스크 공간이 바로 돌아오지 않는 이유는?
- lsof +L1이나 /proc/pid/fd deleted로 log rotation space leak을 어떻게 찾지?
- unlinked file을 process가 계속 열고 있으면 inode와 공간은 언제 해제돼?
- tmpfs deleted open file은 disk leak이 아니라 memory accounting 문제로 볼 수 있어?
contextual_chunk_prefix: |
  이 문서는 file을 unlink해 directory entry가 사라져도 process가 open file description을
  계속 잡고 있으면 inode와 disk/tmpfs space가 회수되지 않는 deleted-but-open space leak을
  log rotation 증상으로 라우팅한다.
---
# Deleted-but-Open Files, Log Rotation, Space Leak Debugging

> 한 줄 요약: 파일을 지웠다고 공간이 바로 돌아오는 것은 아니며, 프로세스가 그 inode를 계속 열고 있으면 디렉터리에서는 사라져도 디스크와 tmpfs 메모리는 계속 점유될 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
> - [Rename Atomicity, Directory fsync, Crash Consistency](./rename-atomicity-directory-fsync-crash-consistency.md)
> - [tmpfs, shmem, /dev/shm, Cgroup Memory Accounting](./tmpfs-shmem-cgroup-memory-accounting.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [Sparse Files, fallocate, Hole Punching](./sparse-file-fallocate-hole-punching.md)

> retrieval-anchor-keywords: deleted open file, unlinked file, disk space leak, lsof +L1, log rotation, inode still open, deleted but open, tmpfs leak, /proc/pid/fd, hidden disk usage

## 핵심 개념

유닉스 계열 파일 수명은 "이름"과 "열린 참조"가 분리된다. 그래서 파일 이름을 `unlink`해도, 어떤 프로세스가 그 파일을 여전히 열고 있으면 실제 inode와 데이터 블록은 남아 있을 수 있다.

- `directory entry`: 사람이 경로로 보는 이름이다
- `inode`: 파일 내용과 메타데이터의 실제 객체다
- `open file`: 프로세스가 그 inode를 여전히 참조하고 있는 상태다
- `unlink`: 이름을 제거하는 동작이지, 열린 참조를 강제로 끊는 동작은 아니다

왜 중요한가:

- 로그 파일을 지웠는데 디스크 사용량이 안 줄어드는 장애를 설명할 수 있다
- tmpfs나 `/dev/shm`에서도 같은 현상이 메모리 pressure로 나타날 수 있다
- 잘못된 log rotation이나 temp-file cleanup이 "숨은 사용량"을 만들 수 있다

## 깊이 들어가기

### 1. 파일 삭제와 공간 회수는 같은 순간이 아니다

운영자가 `rm huge.log`를 했다고 해서 곧바로 블록이 반납되는 것은 아니다.

- path에서는 파일이 안 보인다
- 하지만 프로세스가 fd를 계속 잡고 있으면 inode는 남아 있다
- 마지막 참조가 닫힐 때 실제 공간 회수가 일어난다

그래서 `ls`로는 사라졌는데 `df`는 안 줄어드는 상황이 생긴다.

### 2. log rotation에서 자주 터지는 이유

애플리케이션이 로그 파일을 열어 둔 상태에서 운영자가 파일을 지우거나, rotation 도구가 copy-truncate 대신 예상과 다른 방식을 쓰면 문제가 생길 수 있다.

- old log를 rename했는데 프로세스는 old fd에 계속 append한다
- old log를 unlink했는데 프로세스는 계속 쓰고 있다
- 새 경로는 비어 보이는데 실제 디스크는 old inode가 먹고 있다

즉 "경로 기준 rotation"과 "fd 기준 write target"을 구분해야 한다.

### 3. tmpfs에서도 똑같이 터지지만 증상은 메모리다

tmpfs에 있는 파일을 unlink해도 열린 fd나 mmap이 남아 있으면 사용량이 남을 수 있다.

- 디스크 leak처럼 보이지 않는다
- `memory.current`, `shmem`, OOM 경로로 나타난다
- `/dev/shm`에 쌓이면 브라우저/IPC 워크로드가 이상하게 죽을 수 있다

그래서 deleted-open 문제는 스토리지 문제이자 메모리 문제다.

### 4. 해결은 "지우기"가 아니라 "닫기 또는 재열기"다

운영 대응에서 핵심은 파일 이름 삭제가 아니라 참조 끊기다.

- 프로세스가 fd를 닫게 한다
- 로그 재오픈 신호를 보낸다
- 재시작으로 fd 수명을 끊는다

즉 space leak는 cleanup job보다 lifecycle bug로 보는 편이 맞다.

## 실전 시나리오

### 시나리오 1: 로그를 지웠는데 `df`가 안 줄어든다

가능한 원인:

- 애플리케이션이 deleted inode를 계속 열고 있다
- log rotate 이후 재오픈이 안 됐다
- sidecar/collector가 old file을 쥐고 있다

진단:

```bash
lsof +L1
ls -l /proc/<pid>/fd
readlink /proc/<pid>/fd/<fd>
```

판단 포인트:

- `(deleted)`가 붙은 파일이 큰 크기로 남아 있는가
- 어느 프로세스가 어떤 fd로 쥐고 있는가
- log writer뿐 아니라 collector도 같이 잡고 있는가

### 시나리오 2: `/dev/shm` 파일을 지웠는데 컨테이너 메모리가 안 내려간다

가능한 원인:

- mmap이 살아 있다
- worker가 fd를 닫지 않았다
- tmpfs이므로 디스크가 아니라 shmem 사용량으로 남는다

진단:

```bash
lsof +L1 2>/dev/null | rg '/dev/shm|tmpfs'
cat /sys/fs/cgroup/memory.stat | rg 'shmem|file'
cat /proc/<pid>/maps | rg '/dev/shm'
```

### 시나리오 3: copy-truncate 이후 로그가 뒤엉키거나 usage가 이상하다

가능한 원인:

- writer가 old fd를 그대로 쓴다
- truncate 타이밍과 write가 경쟁한다
- rotation 전략이 애플리케이션 write 모델과 안 맞는다

이 경우는 log rotation 정책을 "경로 이름 관리"가 아니라 "fd 수명 관리" 관점으로 재검토해야 한다.

## 코드로 보기

### 삭제 후에도 열린 fd가 남는 mental model

```text
process opens app.log
  -> fd points to inode X
rm app.log
  -> directory entry removed
  -> fd still points to inode X
process keeps writing
  -> disk/tmpfs usage remains hidden from pathname view
```

### 운영 triage

```bash
lsof +L1
find /proc/*/fd -lname '*deleted*' 2>/dev/null | head
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| rename + reopen rotation | writer 수명과 경로를 맞추기 쉽다 | 애플리케이션 reopen 지원이 필요하다 | 장기 실행 로그 프로세스 |
| copy-truncate | 단순해 보인다 | 경쟁과 hidden usage를 만들 수 있다 | reopen이 어려운 레거시 |
| temp file unlink after open | cleanup가 쉬워 보일 수 있다 | fd가 남으면 hidden usage가 된다 | 짧은 임시 파일에서만 신중히 |
| 재시작으로 fd 정리 | 확실하다 | 서비스 영향이 있다 | 긴급 대응 |

## 꼬리질문

> Q: 파일을 지웠는데 왜 `df`가 안 줄어드나요?
> 핵심: 경로 이름은 사라졌지만 열린 fd가 inode를 계속 참조하고 있어 실제 공간 회수가 안 됐기 때문이다.

> Q: `ls`로 안 보이는데 usage가 남을 수 있나요?
> 핵심: 그렇다. pathname view와 open-file lifetime은 분리되어 있다.

> Q: tmpfs에서도 같은 현상이 있나요?
> 핵심: 있다. 다만 디스크 usage 대신 shmem/memory pressure로 보이는 것이 다르다.

## 한 줄 정리

deleted-open file 문제는 "지웠는데 안 지워진 파일"이 아니라, "이름은 사라졌지만 fd 수명이 아직 끝나지 않은 inode" 문제다.
