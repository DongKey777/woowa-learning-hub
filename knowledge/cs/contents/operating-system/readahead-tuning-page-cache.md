# Readahead Tuning, Page Cache

> 한 줄 요약: readahead는 순차 읽기를 빠르게 만들 수 있지만, 패턴과 어긋나면 쓸모없는 I/O와 page cache 오염을 늘린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [I/O Scheduler, blk-mq Basics](./io-scheduler-blk-mq-basics.md)

> retrieval-anchor-keywords: readahead, read_ahead_kb, page cache, sequential read, random read, cache pollution, blockdev --setra, io pattern

## 핵심 개념

readahead는 커널이 사용자가 곧 읽을 것 같은 데이터를 미리 가져오는 최적화다. 순차 I/O에서는 효과가 좋지만, 랜덤 패턴에서는 불필요한 I/O를 유발할 수 있다.

- `readahead`: 미리 읽어두는 최적화다
- `read_ahead_kb`: 디스크 단위 readahead 크기와 관련된 값이다
- `page cache`: readahead가 채워 넣는 대상이다

왜 중요한가:

- 순차 배치와 스트리밍에서는 throughput을 높일 수 있다
- 랜덤 읽기에서는 cache pollution이 생길 수 있다
- readahead 과다/과소는 모두 성능을 망칠 수 있다

이 문서는 [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)와 [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)를 읽기 패턴 관점에서 잇는다.

## 깊이 들어가기

### 1. readahead는 패턴 기반 추정이다

커널은 현재 접근이 순차라고 판단하면 다음 페이지를 미리 가져온다.

- 순차 읽기에는 이득이 크다
- 중간에 jump가 많으면 효율이 떨어진다
- 잘못된 추정은 쓸모없는 I/O를 만든다

### 2. readahead는 cache hit만 늘리는 게 아니다

미리 가져온 페이지가 실제로 안 쓰이면 오히려 피해가 된다.

- 디스크 대역폭을 소비한다
- page cache를 오염시킨다
- hot data를 밀어낼 수 있다

### 3. 워크로드별로 적절한 크기가 다르다

- 대용량 순차 배치: 큰 readahead가 유리할 수 있다
- OLTP/랜덤 접근: 작은 readahead가 나을 수 있다
- 혼합 워크로드: 기본값이 항상 최선은 아니다

### 4. readahead는 I/O scheduler와도 얽힌다

미리 읽는 양이 장치 큐와 맞지 않으면 기다림이 늘 수 있다.

## 실전 시나리오

### 시나리오 1: 순차 배치가 느리고 디스크가 잘 놀지 않는다

가능한 원인:

- readahead가 너무 작다
- 장치 queue를 충분히 채우지 못한다
- I/O scheduler와 패턴이 안 맞는다

진단:

```bash
blockdev --getra /dev/<dev>
cat /sys/block/<dev>/queue/read_ahead_kb
iostat -x 1
```

### 시나리오 2: 랜덤 읽기에서 page cache가 계속 밀린다

가능한 원인:

- readahead가 과하다
- cache pollution이 심하다
- hot set이 충분히 작지 않다

### 시나리오 3: readahead를 줄였더니 throughput이 급락한다

가능한 원인:

- 원래는 순차 접근이었다
- queue depth가 낮아졌다
- 페이지 미리 읽기의 이득이 컸다

## 코드로 보기

### read-ahead 확인

```bash
cat /sys/block/<dev>/queue/read_ahead_kb
blockdev --getra /dev/<dev>
```

### readahead 감각 모델

```text
sequential access predicted
  -> kernel prefetches pages
  -> throughput improves if prediction is right
  -> cache pollution if prediction is wrong
```

### 커널 페이지 캐시 관찰

```bash
cat /proc/meminfo | grep -E 'Cached|Dirty|Writeback'
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 큰 readahead | 순차 읽기에 좋다 | 랜덤에 독이 될 수 있다 | 배치/스트리밍 |
| 작은 readahead | cache pollution이 줄 수 있다 | throughput이 떨어질 수 있다 | 랜덤 접근 |
| 기본값 유지 | 단순하다 | workload와 안 맞을 수 있다 | 일반 서버 |
| workload별 조정 | 정밀하다 | 운영 복잡도 증가 | 저장장치 튜닝 |

## 꼬리질문

> Q: readahead는 왜 필요한가요?
> 핵심: 순차 읽기에서 디스크와 page cache를 미리 준비하기 위해서다.

> Q: readahead가 왜 문제가 되나요?
> 핵심: 잘못 예측하면 쓸모없는 I/O와 cache pollution을 만든다.

> Q: 랜덤 읽기에는 어떤가요?
> 핵심: 대체로 과한 readahead가 손해를 줄 수 있다.

## 한 줄 정리

readahead는 순차 읽기 최적화이지만, access pattern과 어긋나면 page cache 오염과 불필요한 I/O를 유발한다.
