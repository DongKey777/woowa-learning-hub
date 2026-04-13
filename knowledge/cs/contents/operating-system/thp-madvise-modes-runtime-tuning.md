# THP `madvise` Modes, Runtime Tuning

> 한 줄 요약: THP의 `madvise` 계열 모드는 앱이 huge page를 언제, 어디에 기대할지 조절하는 힌트이며, 잘 고르면 latency와 throughput 사이 균형을 맞출 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [THP, Huge Pages, TLB Latency](./thp-huge-pages-tlb-latency.md)
> - [Compaction, Fragmentation, Latency](./compaction-fragmentation-latency.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [Page Table Overhead, Memory Footprint](./page-table-overhead-memory-footprint.md)
> - [NUMA Auto Balancing, Runtime Debugging](./numa-autobalancing-runtime-debugging.md)

> retrieval-anchor-keywords: MADV_HUGEPAGE, MADV_NOHUGEPAGE, THP madvise, hugepage hint, khugepaged, defrag, transparent huge pages, runtime tuning

## 핵심 개념

THP는 애플리케이션이 따로 요청하지 않아도 커널이 huge page를 만들 수 있게 하는 기능이다. `madvise` 모드는 앱이 특정 구간에 huge page를 기대한다고 힌트를 주는 방식이다.

- `MADV_HUGEPAGE`: huge page를 선호한다고 힌트한다
- `MADV_NOHUGEPAGE`: huge page를 피하고 싶다고 힌트한다
- `THP madvise mode`: 커널이 앱 힌트를 참고해 huge page를 만들 수 있는 정책이다

왜 중요한가:

- 모든 메모리 구간이 huge page에 적합한 것은 아니다
- 특정 hot region만 huge page로 두고 나머지는 피할 수 있다
- latency-sensitive 서버에서 THP의 영향 범위를 줄이는 데 유용하다

이 문서는 [THP, Huge Pages, TLB Latency](./thp-huge-pages-tlb-latency.md)보다 더 구체적으로 `madvise` 기반 정책을 다룬다.

## 깊이 들어가기

### 1. `madvise`는 힌트다

`MADV_HUGEPAGE`는 보장 명령이 아니라 선호 신호다.

- hot region에만 적용할 수 있다
- 모든 매핑에 일괄 적용하지 않아도 된다
- 커널이 상황에 따라 거절할 수 있다

### 2. `MADV_NOHUGEPAGE`는 latency 회피용일 수 있다

THP 생성이나 compaction이 부담인 구간은 huge page를 피하고 싶을 수 있다.

- fragmentation이 심한 구간
- 짧은 수명 객체가 많은 구간
- 예측 가능한 latency가 더 중요한 경로

### 3. 선택적으로 적용하는 것이 핵심이다

THP는 지역적으로 좋아도 전역적으로는 나쁠 수 있다.

- heap 전체에 적용하지 않는다
- hot array나 buffer pool에만 적용한다
- cold region에는 피하는 것이 나을 수 있다

### 4. `always`와 `madvise`는 운영 철학이 다르다

- `always`: 커널이 최대한 자동으로 최적화한다
- `madvise`: 앱이 의도를 더 명확하게 표현한다

## 실전 시나리오

### 시나리오 1: heap 일부만 huge page로 쓰고 싶다

가능한 원인:

- 전체 heap에 THP를 주면 compaction 비용이 커진다
- hot region만 집중적으로 크다
- cold region은 huge page 이점이 작다

### 시나리오 2: `madvise`를 넣었는데 효과가 작다

가능한 원인:

- fragment가 심하다
- reclaim이 많다
- NUMA locality가 안 맞는다

### 시나리오 3: huge page를 켜니 평균은 좋아졌는데 꼬리가 나빠졌다

가능한 원인:

- compaction stall
- page split
- fault burst

이때는 [Compaction, Fragmentation, Latency](./compaction-fragmentation-latency.md)와 같이 본다.

## 코드로 보기

### `madvise` 힌트 예시

```c
void *p = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
madvise(p, len, MADV_HUGEPAGE);
```

### 반대 힌트 예시

```c
madvise(p, len, MADV_NOHUGEPAGE);
```

### THP 상태 확인

```bash
cat /sys/kernel/mm/transparent_hugepage/enabled
cat /sys/kernel/mm/transparent_hugepage/defrag
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `MADV_HUGEPAGE` | hot region 최적화 | 커널이 거절할 수 있다 | 큰 hot array |
| `MADV_NOHUGEPAGE` | compaction 회피 | TLB 이득을 놓친다 | latency-sensitive cold region |
| `always` | 관리가 간단 | 전역 compaction 부담 | throughput 우선 |
| `never` | 예측 가능 | TLB 효율 저하 | 꼬리 지연 우선 |

## 꼬리질문

> Q: `MADV_HUGEPAGE`는 무엇을 보장하나요?
> 핵심: 보장이 아니라 커널에 대한 선호 힌트다.

> Q: `MADV_NOHUGEPAGE`는 왜 쓰나요?
> 핵심: compaction과 fragmentation을 피하고 싶은 구간에 쓴다.

> Q: THP는 전체에 켜야 하나요?
> 핵심: 아니다. hot region에만 선택적으로 쓰는 편이 낫다.

## 한 줄 정리

THP `madvise` 모드는 huge page의 이득을 필요한 구간에만 집중시키는 선택 도구이며, latency-sensitive 앱에서 특히 유용하다.
