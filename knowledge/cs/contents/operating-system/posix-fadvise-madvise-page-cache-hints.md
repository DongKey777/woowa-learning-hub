# posix_fadvise, madvise, Page Cache Hints

> 한 줄 요약: `posix_fadvise()`와 `madvise()`는 page cache와 readahead를 완전히 지배하는 스위치가 아니라, streaming scan의 cache pollution을 줄이고 mmap/read 경로의 접근 의도를 커널에 전달하는 힌트 계층이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)
> - [readahead tuning, page cache](./readahead-tuning-page-cache.md)
> - [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)
> - [Workingset Refault, Page Cache Reclaim, Runtime Debugging](./workingset-refault-page-cache-reclaim-debugging.md)
> - [Page Cache Active/Inactive Reclaim, Hot-Page Debugging](./page-cache-active-inactive-reclaim-debugging.md)

> retrieval-anchor-keywords: posix_fadvise, madvise, POSIX_FADV_DONTNEED, POSIX_FADV_WILLNEED, POSIX_FADV_SEQUENTIAL, POSIX_FADV_RANDOM, MADV_DONTNEED, MADV_SEQUENTIAL, page cache hints, cache pollution, drop-behind

## 핵심 개념

커널은 access pattern을 어느 정도 추정하지만, 모든 워크로드를 정확히 맞추지는 못한다. `posix_fadvise()`와 `madvise()`는 애플리케이션이 "이건 순차 읽기다", "이 구간은 이제 안 쓴다", "곧 접근할 것 같다" 같은 힌트를 주는 인터페이스다.

- `posix_fadvise()`: file descriptor 기반 buffered I/O에 대한 힌트다
- `madvise()`: mapped memory range에 대한 힌트다
- `WILLNEED`: 곧 쓸 가능성을 미리 알린다
- `DONTNEED`: 당분간 안 쓸 가능성을 알린다
- `SEQUENTIAL` / `RANDOM`: readahead와 caching 판단에 영향을 준다

왜 중요한가:

- 큰 scan job이 API의 hot page cache를 오염시키는 것을 줄일 수 있다
- `mmap` 기반 워크로드의 fault/readahead 성격을 조정할 수 있다
- direct I/O까지 가지 않고도 buffered I/O의 간섭을 완화할 수 있다

## 깊이 들어가기

### 1. `posix_fadvise()`는 "정책 강제"가 아니라 "의도 전달"이다

이 힌트는 binding contract가 아니라 기대치 전달이다.

- 커널은 hint를 참고하지만 그대로 따를 의무는 없다
- workload, memory pressure, kernel version에 따라 체감이 달라질 수 있다
- correctness가 아니라 performance tuning 도구로 봐야 한다

즉 `fadvise` 호출 자체를 정답으로 보지 말고, refault와 cache churn이 실제로 줄었는지를 봐야 한다.

### 2. `SEQUENTIAL`, `RANDOM`, `WILLNEED`, `DONTNEED`는 성격이 다르다

운영에서 자주 쓰는 감각은 이렇다.

- `POSIX_FADV_SEQUENTIAL`: 순차 접근 의도, readahead에 유리
- `POSIX_FADV_RANDOM`: 랜덤 접근 의도, 과한 readahead를 줄이는 데 도움
- `POSIX_FADV_WILLNEED`: 가까운 미래 접근, prefetch 힌트
- `POSIX_FADV_DONTNEED`: 이미 다 쓴 구간을 drop-behind 하고 싶을 때

특히 streaming scan은 읽고 지나간 구간에 `DONTNEED`를 주는 방식이 cache pollution 완화에 유용할 수 있다.

주의:

- partial page discard는 기대만큼 깔끔하지 않을 수 있다
- dirty page는 먼저 안정화되지 않으면 바로 버려지지 않을 수 있다

### 3. `madvise()`는 `mmap` 경로에서 의미가 다르다

`madvise()`는 mapped range에 대해 메모리 관점 힌트를 준다.

- `MADV_SEQUENTIAL`, `MADV_RANDOM`, `MADV_WILLNEED`: 접근 패턴 힌트
- `MADV_DONTNEED`: 해당 range를 당분간 안 쓸 것을 알림

하지만 file-backed mapping과 anonymous mapping의 체감은 다르다.

- file-backed shared mapping: 다시 접근 시 file contents에서 재구성될 수 있다
- private anonymous mapping: 다시 접근 시 zero-fill-on-demand 성격이 더 강하다

즉 `posix_fadvise()`와 `madvise()`는 둘 다 hint이지만, 하나는 fd 경로, 하나는 mapping 경로라는 차이가 중요하다.

### 4. hint는 refault와 같이 검증해야 한다

좋은 hint는 결과적으로 다음을 줄여야 한다.

- 불필요한 readahead
- inactive file ballooning
- workingset refault
- API hot page eviction

그래서 tuning은 함수 호출 자체보다, `workingset*`, `pgscan`, `Inactive(file)`, PSI memory pressure의 변화를 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 대용량 export가 끝난 뒤 API cache hit가 무너진다

가능한 원인:

- scan job이 읽고 지나간 page를 계속 cache에 남긴다
- hot page가 inactive reclaim으로 밀려난다
- background batch와 API가 같은 page cache 예산을 공유한다

대응 감각:

- streaming reader에 `POSIX_FADV_SEQUENTIAL`
- 이미 사용한 범위에 `POSIX_FADV_DONTNEED`
- refault와 inactive file 변화를 같이 본다

### 시나리오 2: `mmap` 기반 index reader가 cold fault를 길게 만든다

가능한 원인:

- 접근 패턴과 기본 readahead가 안 맞는다
- `MADV_RANDOM`/`MADV_WILLNEED`를 줄 만한 구간이 분명하다
- `mmap` 자체보다 cache hint 부족이 문제다

### 시나리오 3: `DONTNEED`를 썼는데도 cache가 바로 안 빠지는 것 같다

가능한 원인:

- dirty page가 먼저 writeback되어야 한다
- partial page range여서 효과가 약하다
- reclaim pressure가 낮아 즉시 체감이 약하다

이 경우는 hint가 "버튼을 누르면 즉시 사라지는 명령"이 아니라는 점을 기억해야 한다.

## 코드로 보기

### fd 기반 hint

```c
posix_fadvise(fd, 0, 0, POSIX_FADV_SEQUENTIAL);
posix_fadvise(fd, consumed_offset, consumed_len, POSIX_FADV_DONTNEED);
```

### mmap 기반 hint

```c
madvise(addr, len, MADV_SEQUENTIAL);
madvise(addr, cold_len, MADV_DONTNEED);
```

### mental model

```text
streaming scan
  -> tell kernel this is sequential
  -> consume region
  -> hint that consumed region is no longer needed
  -> preserve hotter cache for latency-sensitive paths
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 기본값 유지 | 단순하다 | mixed workload에서 cache pollution이 커질 수 있다 | 일반적 workload |
| `fadvise` 기반 drop-behind | hot cache를 지키기 쉽다 | 측정 없이 쓰면 효과가 약하거나 불안정할 수 있다 | streaming scan |
| `madvise` tuning | mmap workload에 잘 맞는다 | mapping 성격에 따라 체감이 다르다 | index/search/file mapping |
| direct I/O | cache 오염을 크게 줄인다 | 앱 복잡도와 I/O semantics가 달라진다 | strong isolation 필요 |

## 꼬리질문

> Q: `posix_fadvise()`는 kernel이 꼭 따라야 하나요?
> 핵심: 아니다. 의도 전달용 hint이며 correctness가 아니라 performance tuning 도구다.

> Q: `POSIX_FADV_DONTNEED`를 주면 dirty page도 바로 사라지나요?
> 핵심: 아니다. dirty page는 먼저 안정화되어야 하고, partial page discard도 기대만큼 즉시 동작하지 않을 수 있다.

> Q: `mmap` workload에는 왜 `madvise()`를 따로 보나요?
> 핵심: fd 경로가 아니라 mapped range 기준으로 fault/readahead 성격을 조정해야 하기 때문이다.

## 한 줄 정리

`posix_fadvise()`와 `madvise()`는 buffered I/O와 `mmap`의 page cache 간섭을 줄이는 힌트 도구이며, 좋은 사용법은 "호출했다"가 아니라 "refault와 churn이 실제로 줄었다"로 검증된다.
