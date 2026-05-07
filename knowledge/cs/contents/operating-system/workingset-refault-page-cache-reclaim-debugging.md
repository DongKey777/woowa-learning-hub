---
schema_version: 3
title: Workingset Refault Page Cache Reclaim Debugging
concept_id: operating-system/workingset-refault-page-cache-reclaim-debugging
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- workingset-refault-page
- cache-reclaim
- workingset-refault
- page-cache-refault
aliases:
- workingset refault
- page cache refault
- hot page reclaimed
- refault distance
- cache thrash debugging
- page cache reclaim signal
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/page-cache-active-inactive-reclaim-debugging.md
- contents/operating-system/page-cache-thrash-vs-direct-io.md
- contents/operating-system/memory-reclaim-cgroup-v2-proactive-reclaim.md
- contents/operating-system/readahead-tuning-page-cache.md
- contents/operating-system/kswapd-vs-direct-reclaim-latency.md
symptoms:
- memory pressure에서 많이 reclaimed 된 것보다 hot page를 곧바로 다시 읽는 refault가 문제다.
- page cache가 부족한지 access pattern이 cache와 맞지 않는지 구분해야 한다.
- workingset refault가 증가하며 disk I/O와 p99 latency가 함께 오른다.
expected_queries:
- workingset refault는 방금 지운 hot page를 곧바로 다시 읽고 있다는 신호야?
- page cache reclaim debugging에서 refault를 왜 중요하게 봐?
- cache thrash와 direct I/O 선택 전 workingset refault를 어떻게 확인해?
- memory.reclaim 후 refault가 늘면 workload impact를 어떻게 해석해?
contextual_chunk_prefix: |
  이 문서는 memory pressure에서 중요한 질문이 얼마나 많이 지웠는가보다 방금 지운 hot page를
  곧바로 다시 읽고 있느냐라고 보고, workingset refault를 page cache reclaim 품질 signal로 설명한다.
---
# Workingset Refault, Page Cache Reclaim, Runtime Debugging

> 한 줄 요약: 메모리 압박에서 진짜 중요한 질문은 "얼마나 많이 지웠는가"보다 "방금 지운 hot page를 곧바로 다시 읽고 있나"이며, workingset refault는 그 힌트를 준다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Swap-In, Reclaim, and Major Fault Path Primer](./swap-in-reclaim-fault-path-primer.md)
> - [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)
> - [Page Cache Active/Inactive Reclaim, Hot-Page Debugging](./page-cache-active-inactive-reclaim-debugging.md)
> - [posix_fadvise, madvise, Page Cache Hints](./posix-fadvise-madvise-page-cache-hints.md)
> - [memory.reclaim, Cgroup v2 Proactive Reclaim](./memory-reclaim-cgroup-v2-proactive-reclaim.md)
> - [memory.high vs memory.max, Cgroup Behavior](./memory-high-vs-memory-max-cgroup-behavior.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [readahead tuning, page cache](./readahead-tuning-page-cache.md)

> retrieval-anchor-keywords: workingset, refault, workingset_refault_file, workingset_activate_file, page cache reclaim, refault distance, cold-page refault, hot cache churn, reclaim-induced major fault, pgscan, pgsteal, file cache pressure

## 핵심 개념

메모리 reclaim은 페이지를 얼마나 많이 치웠는지만으로 평가하면 부족하다. 중요한 것은 치운 페이지가 실제로 차갑게 식은 데이터였는지, 아니면 잠깐 밀려났다가 곧바로 다시 필요한 hot data였는지다. workingset refault는 이 두 경우를 구분하는 데 도움을 준다.

- `reclaim`: 메모리 압박 시 page cache나 익명 메모리를 회수하는 경로다
- `refault`: 한 번 밀려난 페이지가 다시 필요해져 fault로 돌아오는 상황이다
- `workingset`: 최근 실제로 쓰이는 hot page 집합이라는 감각적 모델이다
- `pgscan` / `pgsteal`: 얼마나 적극적으로 스캔하고 회수했는지 보는 지표다

왜 중요한가:

- OOM은 없는데 p99가 나빠지는 "느린 장애"를 설명할 수 있다
- nightly batch, backup, large scan이 API hot cache를 밀어내는지 판단할 수 있다
- `memory.high`가 너무 공격적이거나 page cache working set이 limit보다 작은지 큰지 감이 생긴다

## 깊이 들어가기

### 1. page fault가 많다고 다 나쁜 것은 아니다

cold start나 순차 스캔은 page fault가 많아도 꼭 문제는 아니다. 문제는 방금 밀어낸 hot page를 곧바로 다시 읽어야 하는 상황이다.

- 처음 읽는 파일은 cold miss일 수 있다
- 대용량 순차 스캔은 의도적인 cache bypass에 가깝게 해석할 수 있다
- 반면 refault가 빠르게 반복되면 hot working set이 보호되지 못한다는 뜻일 수 있다

그래서 `pgfault` 숫자만으로는 부족하고 reclaim과 refault를 같이 봐야 한다.

### 2. refault는 "이 페이지를 지우면 안 됐을지도 모른다"는 신호다

커널은 최근에 밀어낸 페이지에 대한 흔적을 남겨 두고, 그것이 짧은 시간 안에 다시 돌아오면 workingset 후보로 본다. 이 지점이 운영에서 유용한 이유는 reclaim의 질을 보여 주기 때문이다.

- 스캔은 많지만 refault가 낮다: 차가운 페이지를 잘 밀고 있을 가능성
- 스캔과 refault가 같이 높다: hot cache churn 가능성
- refault 뒤 activation도 높다: 다시 돌아온 페이지가 실제로 hot했다는 힌트

즉 refault는 "메모리가 부족하다"를 넘어서 "어떤 종류의 부족인가"를 설명하는 도구다.

### 3. cgroup memory pressure는 refault를 더 교묘하게 만든다

노드 전체는 여유가 있어도 특정 cgroup이 `memory.high`나 `memory.max` 근처면 그 그룹의 file cache만 먼저 흔들릴 수 있다.

- 호스트 전체 free memory만 보면 멀쩡해 보인다
- 하지만 해당 cgroup 안에서는 working set 보존이 깨진다
- 결과적으로 특정 서비스만 page cache miss와 refault를 반복한다

이 패턴은 "노드는 괜찮은데 이 컨테이너만 느린" 상황에서 특히 중요하다.

### 4. tmpfs와 page cache도 서로 무관하지 않다

tmpfs/shmem usage가 커지면 같은 cgroup 안의 page cache 보호 여지가 줄어든다.

- 임시 렌더 파일이나 `/dev/shm` 사용량이 증가한다
- file cache가 밀리고 hot page refault가 늘 수 있다
- 겉으로는 "메모리 많이 썼다"인데 실제 체감은 "파일 읽기 p99가 나빠졌다"로 나타난다

즉 refault는 파일 I/O 문제와 메모리 문제를 연결하는 중간 언어다.

## 실전 시나리오

### 시나리오 1: 배치가 도는 시간만 API 읽기 p99가 튄다

가능한 원인:

- 대용량 스캔이 hot page cache를 밀어낸다
- `workingset*` 계열 counter가 같이 증가한다
- refault 때문에 같은 파일을 다시 storage에서 읽는다

진단:

```bash
grep -E 'workingset|pgscan|pgsteal|pgfault|pgmajfault' /proc/vmstat
cat /proc/pressure/memory
iostat -x 1
```

판단 포인트:

- 배치 시간대에 `workingset` 계열과 `pgscan`이 같이 오르는가
- 메모리 pressure와 storage read가 동시에 오르는가
- 순차 batch가 API hot file과 같은 volume/cache를 공유하는가

### 시나리오 2: OOM은 없는데 `memory.high`를 넘는 동안만 계속 느리다

가능한 원인:

- reclaim이 반복되며 hot file page를 지운다
- file cache가 살아남지 못하고 refault가 누적된다
- PSI memory pressure가 느린 장애로 먼저 나타난다

진단:

```bash
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.high
cat /sys/fs/cgroup/memory.events
cat /sys/fs/cgroup/memory.stat | rg 'workingset|pgscan|pgsteal|file|shmem'
cat /sys/fs/cgroup/memory.pressure
```

### 시나리오 3: deploy 직후 fault가 많아도 잠시 후 안정된다

이 경우는 꼭 문제라고 볼 수 없다.

- cold start로 한 번 읽고 끝나는 패턴일 수 있다
- refault보다 초기 fault가 크고 시간이 지나며 안정된다
- steady state에서도 refault가 계속 높을 때가 진짜 위험 신호다

즉 "fault가 많다"와 "cache churn이 심하다"를 구분해야 한다.

## 코드로 보기

### 노드 단위 counter 보기

```bash
watch -n 1 "grep -E 'workingset|pgscan|pgsteal|pgfault|pgmajfault' /proc/vmstat"
```

### cgroup 단위로 좁히기

```bash
watch -n 1 "cat /sys/fs/cgroup/memory.stat | rg 'workingset|pgscan|pgsteal|file|shmem'; echo; cat /sys/fs/cgroup/memory.pressure"
```

### 해석 감각

```text
scan/steal rises
  + refault stays low
    -> 상대적으로 차가운 페이지를 회수 중일 가능성
  + refault rises
    -> hot working set churn 가능성
  + PSI memory pressure rises
    -> 느린 장애가 사용자 지연으로 번지는 중
```

주의:

- counter 이름은 커널 버전에 따라 조금 다를 수 있다
- 절대값보다 workload 시간축과 함께 보는 것이 중요하다

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 메모리 여유 확대 | refault churn을 직접 줄인다 | 비용이 든다 | hot cache가 분명히 큰 경우 |
| `memory.low`/`memory.min` 보호 | 중요한 cgroup의 cache를 지키기 쉽다 | 다른 workload 압박이 커질 수 있다 | API 보호 우선 |
| batch 스케줄 분리 | 간섭 원인을 줄인다 | 운영 조율이 필요하다 | mixed workload |
| direct I/O 또는 캐시 우회 | cache pollution을 줄일 수 있다 | 앱 복잡도와 latency 특성이 바뀐다 | 큰 순차 스캔 |

## 꼬리질문

> Q: page fault가 많으면 곧바로 문제라고 봐야 하나요?
> 핵심: 아니다. cold start나 순차 스캔은 정상일 수 있고, reclaim과 refault 패턴이 더 중요하다.

> Q: workingset refault가 높다는 것은 무엇을 뜻하나요?
> 핵심: 방금 밀어낸 페이지가 다시 필요해졌다는 뜻이라 hot cache churn 가능성을 시사한다.

> Q: 노드 메모리는 남는데 특정 서비스만 느릴 수 있나요?
> 핵심: 그렇다. cgroup memory pressure가 그 서비스의 file cache만 먼저 흔들 수 있다.

## 한 줄 정리

workingset refault는 메모리 압박을 단순 용량 문제가 아니라 "hot page를 잘못 밀어내고 있는가"의 문제로 읽게 해 주는 운영 지표다.
