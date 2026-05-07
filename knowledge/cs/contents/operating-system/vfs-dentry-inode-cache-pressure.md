---
schema_version: 3
title: VFS Dentry Inode Cache Pressure
concept_id: operating-system/vfs-dentry-inode-cache-pressure
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- vfs-dentry-inode
- cache-pressure
- metadata-heavy-workload
- dcache-icache-reclaim
aliases:
- VFS dentry inode cache pressure
- metadata-heavy workload
- dcache icache reclaim
- slab pressure filesystem
- path lookup cache
- inode dentry memory
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/slab-allocator-kernel-memory-pressure.md
- contents/operating-system/page-cache-active-inactive-reclaim-debugging.md
- contents/operating-system/overlayfs-copy-up-container-layering-debugging.md
- contents/operating-system/oom-killer-cgroup-memory-pressure.md
- contents/operating-system/psi-pressure-stall-information-runtime-debugging.md
symptoms:
- metadata-heavy workload에서 dentry/inode cache가 slab pressure와 reclaim cost를 키운다.
- file content cache가 아니라 path lookup metadata cache가 memory pressure의 숨은 원인이다.
- OverlayFS나 많은 small files workload에서 inode/dentry cache가 커진다.
expected_queries:
- dentry와 inode cache는 path lookup을 빠르게 하지만 slab pressure를 만들 수 있어?
- metadata-heavy workload에서 VFS cache pressure를 어떻게 진단해?
- dcache icache growth가 OOM이나 reclaim latency의 hidden cause가 될 수 있어?
- OverlayFS copy-up과 dentry/inode cache pressure는 어떻게 연결돼?
contextual_chunk_prefix: |
  이 문서는 VFS dentry와 inode cache가 path lookup을 빠르게 하지만 metadata-heavy workload에서는
  slab memory pressure와 reclaim cost를 동시에 키울 수 있다는 playbook이다.
---
# VFS Dentry, Inode Cache Pressure

> 한 줄 요약: dentry와 inode cache는 파일 경로 탐색을 빠르게 하지만, metadata-heavy workload에서는 슬랩 압박과 reclaim 비용을 동시에 키울 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Slab Allocator, Kernel Memory Pressure](./slab-allocator-kernel-memory-pressure.md)
> - [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)

> retrieval-anchor-keywords: dentry, inode cache, VFS, metadata-heavy, path lookup, /proc/sys/fs/dentry-state, /proc/sys/fs/inode-state, shrinker

## 핵심 개념

VFS는 파일 경로를 찾고, inode와 dentry 캐시는 그 탐색을 빠르게 만든다. 문제는 metadata churn이 많아지면 이 cache가 커지고, 커널 메모리 압박과 reclaim 경합을 만들 수 있다는 점이다.

- `dentry`: 경로명과 inode를 이어주는 디렉터리 항목이다
- `inode`: 파일 메타데이터를 담는 자료구조다
- `VFS`: 다양한 파일 시스템을 공통 인터페이스로 묶는 계층이다

왜 중요한가:

- `open`, `stat`, `ls`, `find` 같은 작업이 많으면 metadata cache가 커진다
- 파일 수가 많고 수명이 짧으면 dentry/inode churn이 심해진다
- cache가 커지면 유저 메모리와 별개로 slab pressure를 만들 수 있다

이 문서는 [Slab Allocator, Kernel Memory Pressure](./slab-allocator-kernel-memory-pressure.md)를 파일 시스템 메타데이터 관점으로 좁혀 본다.

## 깊이 들어가기

### 1. dentry와 inode는 경로 탐색의 속도장치다

같은 파일 경로를 반복해서 열면 cache hit가 이득을 준다.

- 경로 탐색이 빨라진다
- 시스템 콜의 실제 작업량이 줄어든다
- metadata-heavy workload에 특히 유리하다

### 2. metadata churn은 cache를 흔든다

- 수많은 짧은 파일 생성/삭제
- 자주 바뀌는 로그 로테이션
- 대형 repository checkout
- container image unpack

이런 패턴은 dentry/inode cache를 크게 흔든다.

### 3. cache pressure는 슬랩과 함께 봐야 한다

inode/dentry cache는 slab 위에 쌓인다.

- `/proc/sys/fs/dentry-state`
- `/proc/sys/fs/inode-state`
- `slabtop`

이 조합으로 metadata cache pressure를 보아야 한다.

### 4. cache가 커진다고 무조건 문제는 아니다

재사용이 많으면 cache는 좋다. 문제는 회수 압박과 경합이 생길 때다.

## 실전 시나리오

### 시나리오 1: 파일 수가 많은 서버에서 메모리가 점점 줄어든다

가능한 원인:

- dentry/inode cache가 커졌다
- metadata churn이 많다
- reclaim이 잘 안 된다

진단:

```bash
cat /proc/sys/fs/dentry-state
cat /proc/sys/fs/inode-state
slabtop -o
```

### 시나리오 2: `open`/`stat`는 빠른데 시스템 메모리가 압박받는다

가능한 원인:

- metadata cache hit가 높아도 총량이 너무 크다
- inode/dentry slab이 회수되지 않는다
- 다른 커널 캐시와 경쟁한다

### 시나리오 3: 배치가 끝난 뒤에도 cache가 안 내려간다

가능한 원인:

- cache lifetime이 길다
- shrinker가 즉시 회수하지 못한다
- slab pressure가 누적된다

## 코드로 보기

### metadata cache 상태 확인

```bash
cat /proc/sys/fs/dentry-state
cat /proc/sys/fs/inode-state
```

### dentry/inode churn 감각

```text
many file opens and path lookups
  -> dentry/inode cache grows
  -> metadata lookup gets faster
  -> memory pressure may rise
```

### 단순 점검

```bash
find /var/log -type f | wc -l
slabtop | head
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| cache 유지 | 경로 탐색이 빠르다 | kernel memory pressure가 늘 수 있다 | 일반 파일 서버 |
| 적극적 회수 | 메모리를 확보한다 | metadata lookup이 느려질 수 있다 | 압박 해소 필요 |
| metadata churn 감소 | 근본 문제를 줄인다 | 앱/배치 수정이 필요하다 | 장기 최적화 |

## 꼬리질문

> Q: dentry와 inode cache는 왜 중요한가요?
> 핵심: 파일 경로 탐색과 메타데이터 접근을 빠르게 하기 때문이다.

> Q: 왜 slab pressure와 같이 보나요?
> 핵심: 이 cache들이 slab 위에 쌓이기 때문이다.

> Q: metadata-heavy workload는 어떤 것인가요?
> 핵심: 파일 생성/삭제/조회가 매우 많은 패턴이다.

## 한 줄 정리

dentry와 inode cache는 VFS 성능의 핵심이지만, metadata churn이 크면 슬랩 압박과 reclaim 비용이 함께 커진다.
