# mmap vs read, Page Cache Behavior

> 한 줄 요약: `mmap()`과 `read()`는 둘 다 page cache를 쓰지만, fault와 버퍼 복사의 위치가 달라서 서버 체감과 실패 모드가 다르게 나온다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Demand Paging and Page Fault Primer](./demand-paging-page-fault-primer.md)
> - [MAP_SHARED vs MAP_PRIVATE Write Semantics](./mmap-map-shared-vs-map-private-write-semantics.md)
> - [mmap, sendfile, splice, zero-copy](./mmap-sendfile-splice-zero-copy.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [mmap Shared, Truncate, SIGBUS, Coherency Pitfalls](./mmap-shared-truncate-sigbus-coherency-pitfalls.md)
> - [mmap, msync, Hole Punching, File Replace Update Patterns](./mmap-msync-hole-punching-file-replace-update-patterns.md)
> - [posix_fadvise, madvise, Page Cache Hints](./posix-fadvise-madvise-page-cache-hints.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)

> retrieval-anchor-keywords: mmap vs read, page cache, buffered I/O, page fault, demand paging, file-backed page fault, MAP_SHARED vs MAP_PRIVATE, shared mapping dirty page, private mapping COW, MAP_PRIVATE, readahead, cache hit, cache miss, access pattern, lazy loading

## 핵심 개념

`read()`와 `mmap()`은 모두 파일 데이터가 결국 page cache를 거친다는 점에서는 닮았다. 그러나 데이터가 사용자 공간에 언제, 어떤 경로로 보이는지에서 큰 차이가 난다.

- `read()`: 커널이 유저 버퍼로 복사한다
- `mmap()`: 페이지를 주소 공간에 매핑하고 접근 시 fault로 가져온다
- `page cache`: 두 경로 모두에서 핵심 캐시다

왜 중요한가:

- 읽기 패턴에 따라 체감 성능이 크게 달라진다
- fault 위치가 다르므로 latency spike 패턴도 달라진다
- 운영 중에는 "더 빠른 API"보다 "예측 가능한 실패"가 중요할 때가 많다

이 문서는 [mmap, sendfile, splice, zero-copy](./mmap-sendfile-splice-zero-copy.md)를 더 좁혀서, `read()`와 `mmap()`의 page cache 상호작용만 집중해서 본다.

## 깊이 들어가기

### 1. `read()`는 명시적 복사, `mmap()`은 지연된 접근이다

`read()`는 호출 시점에 커널이 데이터를 준비해 유저 버퍼로 복사한다.

`mmap()`은 주소를 매핑할 뿐이고, 실제 페이지는 접근할 때 fault로 들어온다.

- `read()`: 예측 가능성이 높다
- `mmap()`: lazy loading이라 기동이 가벼울 수 있다

### 2. page cache는 둘 다 공유한다

둘 중 무엇을 쓰든 파일 데이터는 page cache에 있을 수 있다.

- 같은 파일을 여러 프로세스가 읽으면 재사용 가능하다
- page cache가 hit하면 `read()`도 `mmap()`도 빠를 수 있다
- page cache가 밀리면 둘 다 느려질 수 있다

즉 차이는 캐시 사용 여부보다, **캐시를 쓰는 시점과 fault/복사 경로**다.

### 3. `mmap()`은 랜덤 접근에서 더 까다롭다

`mmap()`은 자연스럽게 메모리처럼 보이기 때문에, access pattern이 나쁘면 fault가 산발적으로 터진다.

- 파일 전체를 한 번 훑는 스트리밍은 나쁠 수 있다
- 작은 구간을 반복적으로 접근하는 경우는 좋을 수 있다
- 메모리 압박이 있으면 다시 fault가 늘어난다

### 4. `read()`는 버퍼링 제어가 더 명시적이다

`read()`는 chunk size와 buffering 전략이 명확하다.

- batch size를 조절하기 쉽다
- 에러와 retry 경로가 직관적이다
- page fault를 직접 드러내기보다 I/O 경로로 드러낸다

## 실전 시나리오

### 시나리오 1: `mmap()`으로 바꿨는데 첫 응답이 느리다

가능한 원인:

- page fault가 접근 시점에 몰린다
- readahead가 패턴과 맞지 않는다
- working set이 메모리보다 크다

진단:

```bash
perf stat -p <pid> -e minor-faults,major-faults,page-faults -- sleep 30
cat /proc/<pid>/smaps_rollup | grep -E 'Rss|Pss|AnonHugePages'
```

### 시나리오 2: `read()` 경로는 안정적인데 CPU가 더 든다

가능한 원인:

- user/kernel copy 비용이 있다
- chunk를 너무 작게 읽는다
- syscall 횟수가 많다

진단:

```bash
strace -c -p <pid>
perf stat -p <pid> -e instructions,cycles,context-switches -- sleep 30
```

### 시나리오 3: 같은 파일인데 어떤 서버는 `mmap()`이 빠르고 어떤 서버는 느리다

가능한 원인:

- 페이지 캐시 상태가 다르다
- NUMA locality가 다르다
- swap/reclaim pressure가 다르다

이 경우는 [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)와 같이 봐야 한다.

## 코드로 보기

### `read()`의 기본 형태

```c
char buf[8192];
ssize_t n = read(fd, buf, sizeof(buf));
```

### `mmap()`의 기본 형태

```c
char *p = mmap(NULL, len, PROT_READ, MAP_PRIVATE, fd, 0);
```

### 접근 패턴 힌트 주기

```c
// 순차 접근을 커널에 힌트
madvise(p, len, MADV_SEQUENTIAL);
```

### page cache 상태를 보는 커맨드

```bash
free -h
cat /proc/meminfo | grep -E 'Cached|Buffers|Dirty|Writeback'
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `read()` | 예측 가능하다 | 복사 비용이 있다 | 일반 I/O, 안정성 우선 |
| `mmap()` | lazy loading이 쉽다 | fault 패턴이 복잡하다 | 읽기 중심, 큰 파일 |
| readahead 힌트 | 순차 접근에 좋다 | 랜덤 접근에는 덜 맞는다 | 대용량 순차 읽기 |
| 배치 `read()` | syscall을 줄인다 | 버퍼 설계가 필요하다 | 서버 I/O 최적화 |

## 꼬리질문

> Q: `mmap()`과 `read()`는 page cache를 공유하나요?
> 핵심: 그렇다. 차이는 데이터가 사용자 공간에 드러나는 방식이다.

> Q: 왜 `mmap()`은 첫 접근이 느릴 수 있나요?
> 핵심: 실제 데이터가 접근 시점에 page fault로 들어오기 때문이다.

> Q: `read()`는 항상 느린가요?
> 핵심: 아니다. 접근 패턴이 단순하면 더 예측 가능하고 안정적일 수 있다.

> Q: 어떤 경우에 `mmap()`이 더 위험한가요?
> 핵심: 랜덤 접근, 강한 latency 요구, 메모리 압박이 있는 경우다.

## 한 줄 정리

`mmap()`과 `read()`는 모두 page cache를 이용하지만, fault와 복사의 위치가 달라서 성능과 장애 양상이 다르게 나타난다.
