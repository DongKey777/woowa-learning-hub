# Scheduler Fairness, Page Cache, File System Basics

> 한 줄 요약: 스케줄러 공정성과 page cache는 따로 보이면 단순하지만, 실제 서버에서는 run queue, dirty writeback, reclaim, readahead가 함께 꼬이면서 tail latency를 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [vmstat Counters, Runtime Pressure](./vmstat-counters-runtime-pressure.md)
> - [Dirty Page Ratios, Writeback Tuning](./dirty-page-ratios-writeback-tuning.md)
> - [Readahead Tuning, Page Cache](./readahead-tuning-page-cache.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)
> - [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)

> retrieval-anchor-keywords: scheduler fairness, page cache, file system basics, run queue, dirty writeback, readahead, reclaim, tail latency, starvation

## 핵심 개념

스케줄러는 "누가 CPU를 먼저 쓰는가"만이 아니라, 병목 자원을 어떻게 나눌지 결정한다. page cache는 파일 I/O를 빠르게 만들지만, 메모리 압박이 오면 reclaim과 writeback으로 다시 스케줄 문제를 만든다.

- `fairness`: 공정성이다
- `tail latency`: 느린 꼬리 요청의 지연이다
- `page cache`: 파일 I/O를 메모리로 흡수하는 커널 캐시다
- `readahead`: 순차 읽기 최적화다
- `writeback`: dirty page를 디스크로 밀어내는 작업이다

왜 중요한가:

- CPU가 한가해 보여도 page cache miss와 reclaim 때문에 느릴 수 있다
- 작은 write와 fsync가 많으면 flush burst가 생긴다
- 배치가 cache를 밀어내면 API가 다시 디스크를 치게 된다

이 문서는 [vmstat Counters, Runtime Pressure](./vmstat-counters-runtime-pressure.md), [Dirty Page Ratios, Writeback Tuning](./dirty-page-ratios-writeback-tuning.md), [Readahead Tuning, Page Cache](./readahead-tuning-page-cache.md), [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)와 함께 읽으면 좋다.

## 깊이 들어가기

### 1. fairness는 CPU만의 이야기가 아니다

스케줄러 공정성은 CPU 사용 시간 분배에서 시작하지만, 실제 서비스는 I/O, reclaim, flush와 같이 다른 대기열에서도 공정성이 깨진다.

- 인터랙티브 요청은 짧은 대기열이 중요하다
- 배치 작업은 긴 실행 시간보다 cache와 I/O 간섭이 문제다
- 공정성은 평균보다 starvation과 tail latency로 봐야 한다

### 2. page cache는 좋은 캐시지만, 너무 커지면 경쟁 자원이 된다

- 같은 파일을 여러 프로세스가 읽으면 잘 공유된다
- 메모리가 부족해지면 cache가 reclaim 대상이 된다
- cache thrash가 생기면 오히려 디스크 I/O가 증가한다

### 3. writeback과 readahead가 서로를 흔든다

- 순차 읽기는 readahead가 잘 먹는다
- 순차 쓰기와 dirty page 증가는 writeback burst를 만든다
- 둘이 같은 노드에서 겹치면 latency와 throughput이 같이 흔들린다

### 4. 서버는 "CPU가 아닌 곳"에서 느려질 수 있다

- `r`이 낮아도 `b`가 높을 수 있다
- CPU가 낮아도 flush나 reclaim이 대기열을 만든다
- page cache hit ratio보다 hot set 간섭이 더 중요할 수 있다

## 실전 시나리오

### 시나리오 1: CPU 사용률은 낮은데 특정 요청만 늦다

가능한 원인:

- page cache miss가 난다
- reclaim/direct reclaim이 경로에 들어온다
- writeback과 겹쳐 디스크를 기다린다

진단:

```bash
vmstat 1
cat /proc/vmstat | grep -E 'pgfault|pgmajfault|pgscan|pgsteal'
cat /proc/meminfo | grep -E 'Cached|Dirty|Writeback'
```

### 시나리오 2: 워커 수를 늘렸는데 지연이 더 나빠진다

가능한 원인:

- run queue가 길어진다
- context switch와 cache miss가 늘어난다
- 배치가 page cache를 밀어낸다

### 시나리오 3: 로그를 많이 쓰는 배치 이후 API latency가 튄다

가능한 원인:

- dirty page가 많이 쌓였다
- writeback burst가 발생했다
- page cache thrash가 생겼다

이 경우는 [Dirty Page Ratios, Writeback Tuning](./dirty-page-ratios-writeback-tuning.md)과 [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)와 같이 본다.

## 코드로 보기

### page cache와 파일 흐름

```text
open -> lookup dentry/inode -> read from page cache or disk
write -> dirty page -> writeback -> fsync for durability
```

### 운영 점검 커맨드

```bash
vmstat 1
iostat -x 1
cat /proc/meminfo | grep -E 'Cached|Dirty|Writeback'
```

### 배치 직후 cache 간섭 확인

```bash
cat /proc/vmstat | grep -E 'pgscan|pgsteal|pgfault|pgmajfault'
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 캐시 적극 활용 | 파일 I/O가 빨라진다 | 메모리 압박 시 간섭이 커진다 | 일반 서버 |
| readahead 강화 | 순차 읽기에 강하다 | 랜덤에 불리하다 | 배치/스트리밍 |
| writeback 완화 | flush burst를 줄인다 | 내구성 지연이 커질 수 있다 | write-heavy |
| cache 분리/직접 I/O | 간섭을 줄인다 | 구현과 운영이 복잡하다 | 혼합 워크로드 |

## 꼬리질문

> Q: 스케줄러 공정성과 page cache가 왜 같이 나오나요?
> 핵심: 둘 다 tail latency와 starvation을 만드는 공유 자원 관리 문제이기 때문이다.

> Q: page cache가 크면 항상 좋은가요?
> 핵심: 아니다. hot set을 밀어내면 오히려 느려질 수 있다.

> Q: `fsync()`가 왜 중요하죠?
> 핵심: `write()`와 달리 내구성 경계를 의미하기 때문이다.

> Q: 순차 읽기와 랜덤 읽기의 차이는?
> 핵심: 순차는 readahead가 잘 먹고, 랜덤은 cache 효율이 떨어진다.

## 한 줄 정리

스케줄러 공정성과 page cache는 따로 보면 단순하지만, 실제 서비스에서는 run queue, writeback, reclaim, readahead가 함께 작동해 latency를 만든다.
