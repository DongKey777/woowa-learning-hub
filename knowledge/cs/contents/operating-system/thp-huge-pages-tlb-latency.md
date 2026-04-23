# THP, Huge Pages, TLB Latency

> 한 줄 요약: huge page는 TLB miss를 줄여 성능을 올릴 수 있지만, 잘못 켜면 compaction과 fault stall이 지연을 더 키울 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TLB and Page Table Walk Bridge](./tlb-page-table-walk-bridge.md)
> - [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)
> - [NUMA Production Debugging](./numa-production-debugging.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)

> retrieval-anchor-keywords: THP, transparent huge pages, huge pages, AnonHugePages, TLB miss, compaction, khugepaged, dTLB-load-misses, madvise

## 핵심 개념

TLB는 가상 주소를 물리 주소로 바꾸는 캐시다. 페이지 수가 많아질수록 TLB miss 가능성이 높아지고, 그만큼 주소 변환 비용이 늘어난다. Huge page는 더 큰 페이지 크기를 써서 TLB 압력을 줄인다.

- 일반 페이지는 보통 4KB 단위다
- huge page는 보통 2MB 단위다
- THP(`Transparent Huge Pages`)는 애플리케이션이 따로 huge page를 요청하지 않아도 커널이 자동으로 큰 페이지를 만들도록 시도한다

왜 중요한가:

- 메모리 집합이 큰 JVM, DB, 캐시 서버에서 TLB miss가 성능을 흔든다
- huge page는 throughput을 올릴 수 있지만, 메모리 단편화와 compaction 비용이 생길 수 있다
- latency 민감한 서버에서는 "빠른 평균"과 "느린 꼬리"가 동시에 보일 수 있다

이 문서는 [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)에서 본 메모리 지역성과 fault를, huge page 관점으로 더 좁혀서 본다.

## 깊이 들어가기

### 1. TLB miss는 단순 캐시 미스가 아니다

TLB miss는 데이터 자체가 아니라 **주소 변환**이 늦어진다는 뜻이다.

- 페이지가 많을수록 변환 항목이 커진다
- 랜덤 접근이 많을수록 TLB locality가 깨진다
- 큰 워킹셋은 TLB를 더 압박한다

즉 huge page는 메모리 크기를 늘리는 것이 아니라, **주소 변환 표의 압박을 줄이는 방법**이다.

### 2. THP는 편하지만 예측이 어렵다

THP는 운영을 편하게 만들 수 있지만, 내부적으로는 다음 작업이 수반된다.

- 페이지 병합
- compaction
- memory reclaim
- huge page 분해(splitting)

그래서 THP는 "그냥 켜면 좋은 기능"이 아니다. 워크로드가 memory-friendly할 때 강하고, fragmentation이 심하면 지연을 키울 수 있다.

### 3. huge page의 이득과 비용

이득:

- TLB miss 감소
- 메모리 대형 워킹셋에서 throughput 개선
- 일부 DB/JVM에서 CPU 효율 개선

비용:

- compaction stall 가능성
- memory fragmentation 악화
- page split 비용
- latency spike 가능성

### 4. `madvise()`와 `always`는 의미가 다르다

THP 정책은 보통 다음처럼 본다.

- `always`: 최대한 자동으로 huge page를 만든다
- `madvise`: 앱이 원할 때만 huge page를 시도한다
- `never`: THP를 쓰지 않는다

운영에서 중요한 것은 "켜짐/꺼짐"이 아니라 **어떤 워크로드에 어떤 정책이 맞는가**다.

## 실전 시나리오

### 시나리오 1: JVM 힙은 커졌는데 CPU 효율이 좋아지지 않는다

가능한 원인:

- heap은 커졌지만 TLB miss가 병목이다
- THP가 너무 공격적으로 compaction을 일으킨다
- GC와 page split이 겹친다

진단:

```bash
cat /sys/kernel/mm/transparent_hugepage/enabled
cat /sys/kernel/mm/transparent_hugepage/defrag
grep -E 'AnonHugePages|HugePages|Hugepagesize' /proc/meminfo
cat /proc/<pid>/smaps_rollup | grep -E 'AnonHugePages|Rss|Pss'
```

### 시나리오 2: latency spike가 간헐적으로 생긴다

가능한 원인:

- compaction이 burst로 발생한다
- huge page 확보를 위해 커널이 오래 막힌다
- 메모리 단편화가 심해서 THP 생성이 어렵다

진단:

```bash
grep -E 'compact|thp' /proc/vmstat
perf stat -p <pid> -e dTLB-load-misses,dTLB-loads,minor-faults -- sleep 30
```

### 시나리오 3: DB나 캐시 서버가 더 느려졌다

가능한 원인:

- big pages로 이득을 보지만 latency가 더 중요하다
- 워크로드가 랜덤 접근 위주라 huge page 이득이 적다
- NUMA locality와 함께 봐야 한다

이때는 [NUMA Production Debugging](./numa-production-debugging.md)과 같이 봐야 한다. huge page가 좋아도 원격 메모리를 많이 타면 손해다.

## 코드로 보기

### THP 정책 확인

```bash
cat /sys/kernel/mm/transparent_hugepage/enabled
cat /sys/kernel/mm/transparent_hugepage/defrag
```

### 프로세스가 huge page를 얼마나 쓰는지 확인

```bash
grep -R "AnonHugePages" /proc/<pid>/smaps 2>/dev/null | head
cat /proc/<pid>/smaps_rollup | grep AnonHugePages
```

### 앱이 huge page를 원할 때의 힌트

```c
// 의사 코드: 특정 메모리 구간에 huge page를 유도
void *p = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
madvise(p, len, MADV_HUGEPAGE);
```

### TLB 압박을 보는 perf 샘플

```bash
perf stat -p <pid> -e dTLB-load-misses,dTLB-loads,iTLB-load-misses,minor-faults -- sleep 30
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| THP `always` | 자동화가 쉽다 | compaction stall 위험 | throughput 우선 워크로드 |
| THP `madvise` | 제어가 쉽다 | 앱 수정/운영 판단 필요 | latency-sensitive 서비스 |
| THP `never` | 예측 가능하다 | TLB 이득을 놓친다 | 꼬리 지연이 더 중요한 경우 |
| explicit huge pages | 확실하게 쓴다 | 운영 복잡도가 높다 | DB, 특수 메모리 집약 앱 |

핵심은 huge page 자체가 아니라, **주소 변환 비용과 compaction 비용 중 무엇이 더 비싼가**다.

## 꼬리질문

> Q: huge page는 왜 TLB에 유리한가요?
> 핵심: 한 번의 TLB entry가 더 많은 메모리를 커버하기 때문이다.

> Q: THP가 항상 좋은가요?
> 핵심: 아니다. compaction과 fragmentation 때문에 latency가 나빠질 수 있다.

> Q: `madvise(MADV_HUGEPAGE)`는 무엇을 보장하나요?
> 핵심: 보장이 아니라 힌트다. 커널이 상황에 따라 결정한다.

> Q: huge page를 켰는데도 CPU가 안 줄면 왜 그런가요?
> 핵심: 병목이 TLB가 아니라 reclaim, lock, I/O, NUMA일 수 있다.

## 한 줄 정리

THP와 huge page는 TLB 압력을 줄이는 강력한 수단이지만, compaction과 fragmentation 비용이 커지면 latency 서버에서는 역효과가 날 수 있다.
