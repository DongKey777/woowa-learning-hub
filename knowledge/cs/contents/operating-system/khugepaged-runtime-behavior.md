# khugepaged, Runtime Behavior

> 한 줄 요약: khugepaged는 THP를 배경에서 collapse하려는 커널 스레드라서, 메모리 지역성과 fragmentation 상태에 따라 성능 이득도, latency spike도 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [THP, Huge Pages, TLB Latency](./thp-huge-pages-tlb-latency.md)
> - [THP `madvise` Modes, Runtime Tuning](./thp-madvise-modes-runtime-tuning.md)
> - [Compaction, Fragmentation, Latency](./compaction-fragmentation-latency.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)

> retrieval-anchor-keywords: khugepaged, collapse, scan, collapse_huge_page, AnonHugePages, khugepaged/scan_sleep_millisecs, khugepaged/pages_to_scan, THP collapse

## 핵심 개념

khugepaged는 THP를 위해 background에서 small pages를 huge page로 collapse하려는 커널 스레드다. 이 스레드가 하는 일은 성능 최적화지만, 상황에 따라 background compaction처럼 느껴질 수 있다.

- `khugepaged`: THP collapse를 시도하는 커널 스레드다
- `collapse`: 작은 페이지를 큰 페이지로 합치는 동작이다
- `scan`: collapse 가능한 영역을 찾는 작업이다

왜 중요한가:

- 평균 성능은 좋아질 수 있다
- background scan과 collapse가 latency에 간섭할 수 있다
- fragmentation이 심하면 기대한 이득이 안 나올 수 있다

이 문서는 [THP, Huge Pages, TLB Latency](./thp-huge-pages-tlb-latency.md)와 [Compaction, Fragmentation, Latency](./compaction-fragmentation-latency.md)를 배경 스레드 관점으로 묶는다.

## 깊이 들어가기

### 1. khugepaged는 검사와 collapse를 반복한다

커널은 계속 huge page로 만들 수 있는 영역을 찾는다.

- scan 대상이 많으면 비용이 든다
- collapse 가능성이 낮으면 낭비가 생긴다
- hot region에서만 이득이 크다

### 2. background 작업이지만 완전히 공짜는 아니다

- CPU를 쓴다
- page table과 page migration을 건드릴 수 있다
- latency-sensitive workload에서는 간섭이 될 수 있다

### 3. fragmentation이 높으면 효과가 줄어든다

- huge page로 collapse할 연속 공간이 없다
- compaction을 동반할 수 있다
- tail latency를 흔들 수 있다

### 4. tunable이 관찰 포인트다

- `pages_to_scan`
- `scan_sleep_millisecs`

이 값들은 khugepaged의 배경 부담과 직접 연결된다.

## 실전 시나리오

### 시나리오 1: THP를 켰는데도 huge page가 잘 안 늘어난다

가능한 원인:

- fragmentation이 심하다
- khugepaged가 collapse하기 어렵다
- hot region이 너무 분산되어 있다

진단:

```bash
cat /sys/kernel/mm/transparent_hugepage/khugepaged/pages_to_scan
cat /sys/kernel/mm/transparent_hugepage/khugepaged/scan_sleep_millisecs
grep -E 'AnonHugePages|HugePages' /proc/meminfo
```

### 시나리오 2: 평균 성능은 좋아졌는데 간헐적 spike가 있다

가능한 원인:

- collapse burst
- compaction과 겹침
- background scan이 CPU를 건드림

### 시나리오 3: 노드가 오래 돌수록 THP 효과가 약해진다

가능한 원인:

- fragment accumulation
- page migration 실패
- hot/cold region 분리 실패

## 코드로 보기

### khugepaged 관련 값 확인

```bash
cat /sys/kernel/mm/transparent_hugepage/khugepaged/pages_to_scan
cat /sys/kernel/mm/transparent_hugepage/khugepaged/scan_sleep_millisecs
```

### huge page 상태 확인

```bash
grep -E 'AnonHugePages|HugePages' /proc/meminfo
```

### 단순 모델

```text
background scan
  -> candidate pages found
  -> collapse attempted
  -> success or extra stall
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| khugepaged 활성 | TLB 이득 가능 | background cost 존재 | 대형 워킹셋 |
| scan 완화 | 간섭을 줄인다 | huge page 이득이 줄 수 있다 | latency-sensitive |
| THP 비활성 | 예측 가능 | TLB 최적화 포기 | 꼬리 지연 우선 |

## 꼬리질문

> Q: khugepaged는 무엇을 하나요?
> 핵심: small pages를 huge page로 collapse하려고 배경에서 스캔한다.

> Q: 왜 latency를 건드릴 수 있나요?
> 핵심: scan과 collapse가 CPU, migration, compaction을 사용하기 때문이다.

> Q: THP가 늘지 않으면 무엇을 보나요?
> 핵심: fragmentation, khugepaged tunable, hot region 분포를 본다.

## 한 줄 정리

khugepaged는 THP collapse를 배경에서 수행하는 스레드이며, fragment가 심하면 이득보다 background latency 비용이 더 두드러질 수 있다.
