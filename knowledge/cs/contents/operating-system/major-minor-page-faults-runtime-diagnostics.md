# Major, Minor Page Faults, Runtime Diagnostics

> 한 줄 요약: page fault는 단순히 "메모리에 없었다"는 뜻이 아니라, 서버가 왜 멈칫했는지 보여주는 가장 직접적인 런타임 신호다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [mmap, sendfile, splice, zero-copy](./mmap-sendfile-splice-zero-copy.md)
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: major page fault, minor page fault, pgfault, pgmajfault, copy-on-write, demand paging, smaps_rollup, perf stat, mincore

## 핵심 개념

page fault는 프로세스가 접근한 가상 주소의 페이지가 현재 바로 쓸 수 없는 상태일 때 발생한다. 문제는 "fault가 났다"가 아니라, **어떤 종류의 fault가 얼마나 자주 나느냐**가 서버 지연을 만든다는 점이다.

- `minor page fault`: 디스크 I/O 없이 처리 가능한 fault다. page cache, anonymous page 준비, copy-on-write 전개 같은 경우가 여기에 들어간다.
- `major page fault`: 디스크 I/O가 필요한 fault다. 파일을 실제로 읽어와야 하므로 훨씬 비싸다.
- `copy-on-write`: fork 이후 실제 write가 발생할 때 페이지를 복제하는 메커니즘이다.
- `demand paging`: 필요한 순간에만 페이지를 가져오는 방식이다.

왜 중요한가:

- 평균 CPU 사용률은 낮은데 p99가 튀는 현상을 설명할 수 있다.
- JVM, mmap, 동적 로딩, 큰 설정 파일, cold start에서 자주 보인다.
- "메모리가 많아 보이는데 왜 느리지?"라는 질문에 fault 관점이 답이 된다.

이 문서는 [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)에서 다룬 메모리 압박을, 운영 중에는 어떻게 측정하고 해석하는지에 집중한다.

## 깊이 들어가기

### 1. minor fault와 major fault의 차이는 지연의 성질이 다르다

minor fault는 대개 커널 내부 작업과 메모리 매핑 조정으로 끝난다. 반면 major fault는 블록 I/O와 스케줄링이 섞인다.

- minor fault는 많이 나도 영향이 작을 수 있다
- major fault는 적게 나도 tail latency를 크게 흔든다
- 같은 fault 수라도 워크로드에 따라 체감이 다르다

즉 fault 수만 보는 것이 아니라 fault의 종류를 함께 봐야 한다.

### 2. `mmap()`과 파일 접근은 page fault를 숨기기도, 드러내기도 한다

`mmap()`은 파일을 메모리처럼 다루게 해주지만, 실제 데이터는 페이지 단위로 fault를 통해 들어온다.

- 순차 접근은 page fault가 예측 가능하다
- 랜덤 접근은 fault 패턴이 거칠어진다
- 메모리 압박이 있으면 이미 있던 페이지도 다시 fault를 유발할 수 있다

이 점은 [mmap, sendfile, splice, zero-copy](./mmap-sendfile-splice-zero-copy.md)와 연결된다. `mmap()`은 복사 비용을 줄일 수 있지만, fault 비용을 무시하면 안 된다.

### 3. major fault가 비싼 진짜 이유

디스크 I/O만 비싼 것이 아니다. major fault에는 다음이 겹친다.

- 페이지를 찾고 고정하는 커널 작업
- I/O 요청 제출과 완료 대기
- lock 경쟁
- wakeup과 context switch

그래서 major fault는 단일 I/O 지연이 아니라, **커널이 페이지를 서비스하는 전체 파이프라인 지연**으로 봐야 한다.

### 4. copy-on-write는 "쓰기 첫 순간"에만 비싸다

fork 직후 자식이 메모리를 많이 읽기만 하면 싸게 보인다. 하지만 write가 시작되면 페이지 복제가 생긴다.

- 읽기 위주 자식 프로세스는 대체로 minor fault 중심이다
- write-heavy forked worker는 COW fault가 급증할 수 있다
- 대형 힙이나 큰 캐시를 가진 프로세스에서 이 차이가 크다

서버에서 "기동은 빠른데 첫 요청만 유독 느리다"면 COW와 lazy mapping을 같이 의심해야 한다.

## 실전 시나리오

### 시나리오 1: cold start 직후 첫 요청만 느리다

가능한 원인:

- class loading, dynamic linking, config read로 major fault가 몰린다
- `mmap()`된 데이터가 아직 올라오지 않았다
- fork 이후 COW가 터진다

진단:

```bash
perf stat -p <pid> -e minor-faults,major-faults,context-switches -- sleep 10
cat /proc/<pid>/status | grep -E 'VmRSS|VmSize|Threads'
cat /proc/<pid>/smaps_rollup | grep -E 'Rss|Pss|AnonHugePages|Shared_Clean|Private_Dirty'
```

판단 포인트:

- major fault가 시작 구간에만 몰리는가
- `VmSize`는 큰데 `VmRSS`는 작은가
- `smaps_rollup`에서 shared/private 비율이 어떻게 보이는가

### 시나리오 2: 트래픽은 일정한데 p99가 간헐적으로 튄다

가능한 원인:

- 특정 요청 경로가 큰 파일을 랜덤하게 읽는다
- page cache가 압박받아 파일-backed page가 밀린다
- swap 또는 reclaim이 fault를 더 비싸게 만든다

진단:

```bash
grep -E 'pgfault|pgmajfault' /proc/vmstat
vmstat 1
iostat -x 1
```

### 시나리오 3: fork 기반 worker가 메모리만큼 느려진다

가능한 원인:

- COW로 인해 write 첫 순간에 페이지 복제가 폭발한다
- parent가 큰 메모리 상태에서 fork를 반복한다
- child가 바로 dirty page를 많이 만든다

진단:

```bash
strace -f -ttT -e trace=fork,vfork,clone,mmap,mprotect,brk -p <pid>
perf stat -p <pid> -e minor-faults,major-faults,page-faults -- sleep 30
```

### 시나리오 4: `mmap()`으로 바꿨는데 오히려 더 느려졌다

가능한 이유:

- random access가 많아 fault가 증가한다
- working set이 메모리보다 커졌다
- page cache가 재사용되지 않는다

이때는 "복사 줄이기"보다 "접근 패턴 줄이기"가 먼저다.

## 코드로 보기

### fault 카운터를 보는 가장 간단한 방법

```bash
perf stat -p <pid> -e minor-faults,major-faults,page-faults -- sleep 30
```

`page-faults`는 총합, `minor-faults`와 `major-faults`는 종류를 나눈 값이다. 총합만 보고도, major 비율을 보면 위험도를 금방 알 수 있다.

### 메모리 맵 상태 확인

```bash
cat /proc/<pid>/maps
cat /proc/<pid>/smaps_rollup
```

`maps`는 어디가 매핑되었는지, `smaps_rollup`은 실제 RSS와 private/shared 구성을 보는 데 좋다.

### prefault와 접근 예측

```c
// 의사 코드: 시작 직후 fault를 줄이려는 경우
void *p = mmap(NULL, len, PROT_READ, MAP_PRIVATE, fd, 0);
madvise(p, len, MADV_WILLNEED);
```

주의점:

- prefault는 초기 지연을 줄일 수 있지만, 무조건 좋은 것은 아니다
- 실제로 안 쓸 페이지까지 다 가져오면 메모리 낭비가 된다

### 접근 여부를 확인하는 힌트

```c
// mincore는 페이지가 현재 resident인지 확인하는 데 쓰인다
unsigned char vec[pages];
mincore(addr, len, vec);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| prefault | 첫 요청 지연을 줄인다 | 메모리 사용이 앞당겨진다 | cold start 민감한 서버 |
| `mmap()` | 복사 비용이 적다 | page fault 예측이 어려울 수 있다 | 큰 읽기 중심 파일 |
| `read()` 배치 | fault와 I/O를 단순화한다 | 복사 비용이 늘 수 있다 | 단순하고 안정적인 경로 |
| COW 활용 | fork가 싸게 시작된다 | 첫 write가 비싸다 | worker pre-fork 모델 |

운영에서는 "fault를 없애기"보다 "fault가 언제, 얼마나 비싸게 나는지"를 관리하는 편이 현실적이다.

## 꼬리질문

> Q: minor fault도 문제인가요?
> 핵심: 보통 major fault보다 덜 비싸지만, 빈도가 많으면 누적 지연이 된다.

> Q: 왜 major fault가 서버 tail latency를 흔드나요?
> 핵심: 디스크 I/O와 스케줄링 대기가 섞여 한 번의 접근이 길어지기 때문이다.

> Q: `mmap()`을 쓰면 page fault가 사라지나요?
> 핵심: 아니오. 오히려 fault를 접근 모델의 일부로 받아들여야 한다.

> Q: `perf stat`의 page-faults만 보면 충분한가요?
> 핵심: 아니다. minor/major 비율, RSS, smaps, I/O를 같이 봐야 한다.

## 한 줄 정리

page fault는 메모리 부족의 흔적이 아니라 서버가 지연을 만드는 경로이며, major fault와 COW를 구분해서 봐야 원인을 제대로 잡을 수 있다.
