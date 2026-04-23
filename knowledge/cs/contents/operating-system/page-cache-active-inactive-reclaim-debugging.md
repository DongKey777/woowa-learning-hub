# Page Cache Active/Inactive Reclaim, Hot-Page Debugging

> 한 줄 요약: page cache 장애는 단순히 캐시 크기가 부족한 문제가 아니라, hot file page가 active 쪽에 남지 못하고 inactive reclaim으로 계속 밀려나는 구조의 문제로 보는 편이 정확하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Workingset Refault, Page Cache Reclaim, Runtime Debugging](./workingset-refault-page-cache-reclaim-debugging.md)
> - [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)
> - [posix_fadvise, madvise, Page Cache Hints](./posix-fadvise-madvise-page-cache-hints.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)
> - [readahead tuning, page cache](./readahead-tuning-page-cache.md)
> - [memory.low vs memory.min, Reclaim Protection](./memory-low-min-reclaim-protection.md)

> retrieval-anchor-keywords: active_file, inactive_file, page cache reclaim, active list, inactive list, hot page, file cache pressure, pgactivate, pgdeactivate, page promotion, page demotion

## 핵심 개념

page cache는 "파일을 캐시에 넣는다"에서 끝나지 않는다. 실제 운영에서는 어떤 페이지가 hot해서 더 오래 보호받는지, 어떤 페이지가 cold로 판단돼 reclaim 후보로 떨어지는지가 더 중요하다. active/inactive file cache 모델은 이 감각을 잡는 데 유용하다.

- `active(file)`: 최근 반복 접근돼 좀 더 보호받는 file page 쪽으로 이해할 수 있다
- `inactive(file)`: reclaim 후보에 더 가까운 file page 쪽으로 이해할 수 있다
- `promotion`: 다시 많이 쓰여 active 쪽으로 올라가는 흐름이다
- `demotion`: 차갑다고 판단돼 inactive 쪽으로 내려가는 흐름이다
- `reclaim`: inactive 쪽부터 회수해 메모리를 확보하는 경로다

왜 중요한가:

- 같은 page cache miss라도 cold start와 hot page eviction은 의미가 다르다
- batch scan이 API hot page를 inactive로 밀어낼 수 있다
- `workingset refault`는 결과이고, active/inactive 균형은 그 결과가 나오기 전의 구조다

## 깊이 들어가기

### 1. hot page는 "있느냐"보다 "남아 있느냐"가 중요하다

서버는 필요한 파일을 한 번 읽는 것보다, 반복적으로 읽는 hot file page가 계속 메모리에 남는 것이 더 중요하다.

- config/template/static metadata
- 자주 읽는 index segment
- 반복 접근되는 small file set

이런 페이지가 inactive 쪽으로 밀려나기 시작하면, 이후에는 같은 파일을 계속 다시 읽으며 p99가 흔들린다.

### 2. active/inactive는 완벽한 진실이 아니라 운영용 mental model이다

커널 내부 구현은 버전과 설정에 따라 진화하지만, 운영 판단에서는 다음 감각이 여전히 유효하다.

- 반복 접근되는 page는 더 오래 보호된다
- 순차 스캔 같은 페이지는 reclaim 후보로 더 빨리 밀려날 수 있다
- 보호와 회수의 균형이 깨지면 hot page churn이 생긴다

즉 active/inactive는 "왜 캐시가 남지 않았는가"를 설명하는 실전용 모델이다.

### 3. readahead와 scan workload가 inactive를 부풀릴 수 있다

대용량 순차 읽기는 의도치 않게 많은 file page를 cache에 넣고, 곧바로 reclaim 후보로 만든다.

- `Inactive(file)`가 빠르게 늘어난다
- hot page가 보호받기 전에 같이 밀릴 수 있다
- 이후 `workingset refault`가 뒤따른다

그래서 readahead와 cache 보호 정책은 항상 같이 봐야 한다.

### 4. cgroup 보호선이 file cache에도 영향을 준다

`memory.low`, `memory.min`, `memory.high`는 anon memory만이 아니라 file cache working set에도 영향을 준다.

- 보호가 약하면 active file도 쉽게 흔들린다
- tmpfs/shmem 경쟁이 커지면 file cache 여유가 줄어든다
- 특정 cgroup만 hot page churn을 겪을 수 있다

즉 page cache 문제도 결국 reclaim policy 문제다.

## 실전 시나리오

### 시나리오 1: 야간 batch 이후 API의 file read p99가 나빠진다

가능한 원인:

- 순차 batch가 많은 page를 inactive 쪽으로 밀어 넣는다
- hot page가 보호되지 못하고 같이 밀린다
- 다음 요청에서 refault와 storage read가 늘어난다

진단:

```bash
grep -E 'Active\\(file\\)|Inactive\\(file\\)|Cached' /proc/meminfo
grep -E 'pgactivate|pgdeactivate|workingset|pgscan|pgsteal' /proc/vmstat
cat /proc/pressure/memory
```

판단 포인트:

- batch 시간대에 `Inactive(file)`가 급격히 늘어나는가
- `pgdeactivate`와 `workingset` 계열이 같이 오른 뒤 refault가 붙는가
- batch와 API가 같은 cgroup/file cache를 공유하는가

### 시나리오 2: 메모리는 남아 보이는데 캐시 hit가 불안정하다

가능한 원인:

- free memory 절대량보다 reclaim 정책이 공격적이다
- `memory.high` 근처에서 file cache가 먼저 흔들린다
- tmpfs/shmem이 같은 예산을 잠식한다

이 경우는 메모리 "용량"보다 page cache "보호 정책"을 먼저 의심하는 편이 맞다.

### 시나리오 3: readahead를 키웠더니 순차 배치는 빨라졌지만 OLTP는 느려졌다

가능한 원인:

- 순차 read 효율은 좋아졌지만 cache pollution이 커졌다
- inactive file이 빠르게 쌓였다
- hot small-file set이 active에 남지 못했다

즉 readahead 최적화는 단일 워크로드가 아니라 공존 workload 기준으로 판단해야 한다.

## 코드로 보기

### 노드 관점에서 active/inactive file 보기

```bash
grep -E 'Active\\(file\\)|Inactive\\(file\\)|Cached' /proc/meminfo
grep -E 'pgactivate|pgdeactivate|workingset|pgscan|pgsteal' /proc/vmstat
```

### cgroup 관점으로 좁히기

```bash
cat /sys/fs/cgroup/memory.stat | rg 'active_file|inactive_file|workingset|pgscan|pgsteal'
cat /sys/fs/cgroup/memory.events
cat /sys/fs/cgroup/memory.pressure
```

### mental model

```text
hot repeated file access
  -> should stay protected longer

large scan/readahead burst
  -> fills inactive side
  -> reclaim starts
  -> hot pages may get displaced
  -> refault and read latency rise
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 더 큰 메모리 여유 | hot page 보호가 쉬워진다 | 비용이 든다 | file cache working set이 큰 경우 |
| `memory.low`/`memory.min` 보호 | 중요한 cache를 지킬 수 있다 | 다른 그룹 압박이 커질 수 있다 | API 보호 우선 |
| readahead 축소 | pollution을 줄일 수 있다 | 순차 throughput이 줄 수 있다 | mixed workload |
| direct I/O/분리 볼륨 | cache 간섭을 줄인다 | 앱/운영 복잡도가 오른다 | batch scan과 OLTP 공존 |

## 꼬리질문

> Q: `workingset refault`와 active/inactive는 어떤 관계인가요?
> 핵심: active/inactive 균형이 깨져 hot page가 밀려난 결과가 refault로 드러나는 경우가 많다.

> Q: `Inactive(file)`가 크면 무조건 나쁜가요?
> 핵심: 아니다. scan workload에서는 자연스러울 수 있지만, hot page churn과 같이 보이면 문제다.

> Q: page cache 문제는 결국 메모리 부족인가요?
> 핵심: 항상 그런 것은 아니다. 보호 정책, readahead, workload 혼재 때문에 hot page가 잘못 밀려나는 구조일 수 있다.

## 한 줄 정리

page cache는 용량만이 아니라 어떤 file page를 active 쪽에 남겨 두느냐의 문제이며, hot page가 inactive reclaim으로 밀리기 시작하면 읽기 p99가 급격히 흔들린다.
