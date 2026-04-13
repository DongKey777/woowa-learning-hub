# Page Cache Thrash vs Direct I/O

> 한 줄 요약: page cache thrash는 캐시가 계속 밀려나는 상황이고, direct I/O는 그 경로를 아예 우회하는 선택이지만 둘 다 워크로드와 맞지 않으면 더 느려질 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [mmap, sendfile, splice, zero-copy](./mmap-sendfile-splice-zero-copy.md)
> - [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)
> - [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)

> retrieval-anchor-keywords: page cache thrash, direct I/O, O_DIRECT, readahead, cache eviction, cache pollution, buffered I/O, storage workload, working set

## 핵심 개념

page cache thrash는 파일 I/O가 page cache에 남아 있는 이득보다, 서로 다른 작업이 cache를 계속 밀어내는 비용이 더 커지는 상태다. direct I/O는 이런 cache 경로를 우회해 페이지 캐시 오염을 줄이려는 선택이다.

- `page cache`: 파일 I/O의 핵심 캐시다
- `thrash`: 캐시가 계속 교체되어 히트율이 무너지는 상태다
- `direct I/O`: 커널 page cache를 거치지 않는 I/O다
- `readahead`: 순차 읽기를 미리 가져오는 최적화다

왜 중요한가:

- 큰 배치가 캐시를 밀어내면 API latency가 튈 수 있다
- direct I/O는 캐시를 보호하지만 버퍼링 이득을 포기한다
- 같은 스토리지라도 접근 패턴에 따라 정답이 달라진다

이 문서는 [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)와 [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)를 파일 I/O 관점으로 묶는다.

## 깊이 들어가기

### 1. thrash는 "캐시가 나쁘다"는 뜻이 아니다

page cache는 잘 쓰면 강력하다. 문제는 서로 다른 워크로드가 같은 캐시 공간을 놓고 경쟁할 때다.

- 순차 배치가 cache를 밀어낸다
- 그 뒤 API가 다시 같은 파일을 읽으며 디스크를 친다
- 히트율이 떨어지고 tail latency가 튄다

### 2. direct I/O는 해결책이 아니라 경로 변경이다

direct I/O는 cache를 우회한다.

- page cache 오염을 줄일 수 있다
- cache thrash로 인한 간섭을 낮출 수 있다
- 하지만 앱이 버퍼링을 직접 책임져야 한다

즉 direct I/O는 "더 빠른 I/O"가 아니라 "덜 섞이는 I/O"일 수 있다.

### 3. readahead와 access pattern은 같이 봐야 한다

순차 접근에는 readahead가 좋다. 랜덤 접근에는 오히려 쓸모없는 I/O를 유발할 수 있다.

- 순차 batch job: page cache + readahead가 유리
- 랜덤 OLTP: direct I/O를 검토할 수 있다
- 혼합 워크로드: 캐시 분리나 스토리지 분리가 필요하다

### 4. cache hit ratio보다 중요한 것은 간섭이다

히트율이 높아도 중요한 page를 밀어내면 체감은 나빠진다. 그래서 운영에서는 단순 hit ratio보다 "누가 누구를 밀어냈는가"를 봐야 한다.

## 실전 시나리오

### 시나리오 1: 대용량 배치 이후 API가 느려진다

가능한 원인:

- batch read가 page cache를 밀어낸다
- API가 다시 디스크를 친다
- readahead가 배치 패턴과 맞는다

진단:

```bash
iostat -x 1
vmstat 1
cat /proc/meminfo | grep -E 'Cached|Dirty|Writeback'
```

### 시나리오 2: page cache를 없앴는데도 느리다

가능한 원인:

- direct I/O로 바꾸며 버퍼링 이득을 잃었다
- 작은 I/O가 많아 syscall과 completion overhead가 늘었다
- 앱이 backpressure를 직접 관리하지 못한다

### 시나리오 3: 로그/배치가 끝난 뒤도 디스크가 계속 바쁘다

가능한 원인:

- dirty writeback이 밀린다
- cache thrash와 writeback이 겹친다
- reclaim과 I/O가 함께 비틀린다

이 경우는 [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)와 같이 본다.

## 코드로 보기

### direct I/O 의도

```c
int fd = open("data.bin", O_RDONLY | O_DIRECT);
```

주의점:

- 정렬과 버퍼 조건이 까다롭다
- 일반 buffered I/O보다 다루기 어렵다

### page cache 경로 점검

```bash
cat /proc/vmstat | grep -E 'pgfault|pgmajfault|pgscan|pgsteal'
```

### 캐시 간섭 감각

```text
batch job reads huge file
  -> page cache evicts hot pages
  -> OLTP rereads from disk
  -> tail latency spikes
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| buffered I/O | 단순하고 캐시를 잘 쓴다 | cache thrash에 취약하다 | 일반 파일 I/O |
| direct I/O | cache pollution을 줄인다 | 버퍼링 직접 관리 필요 | DB, 특수 스토리지 경로 |
| readahead 최적화 | 순차 읽기에 강하다 | 랜덤에 약하다 | 배치/스트리밍 |
| workload 분리 | 간섭을 줄인다 | 운영 비용이 든다 | 혼합 트래픽 |

## 꼬리질문

> Q: page cache thrash와 direct I/O는 어떤 관계인가요?
> 핵심: thrash를 줄이기 위해 direct I/O를 택할 수 있지만, 반대로 성능을 잃을 수도 있다.

> Q: direct I/O가 항상 빠른가요?
> 핵심: 아니다. 캐시 이득을 포기하는 대신 간섭을 줄이는 선택이다.

> Q: cache hit ratio가 높으면 안심해도 되나요?
> 핵심: 아니다. 중요한 hot page를 밀어내면 체감은 나빠질 수 있다.

## 한 줄 정리

page cache thrash는 워크로드 간 간섭 문제이고, direct I/O는 그 간섭을 줄이는 경로일 뿐 언제나 더 빠른 해법은 아니다.
