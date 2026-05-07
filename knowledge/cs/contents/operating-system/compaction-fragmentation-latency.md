---
schema_version: 3
title: Compaction Fragmentation Latency
concept_id: operating-system/compaction-fragmentation-latency
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- compaction-fragmentation-latency
- memory-compaction-fragmentation
- latency
- buddy-allocator-order
aliases:
- memory compaction fragmentation latency
- buddy allocator order allocation
- compact_stall
- page migration latency
- THP compaction spike
- memory fragmentation
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/thp-huge-pages-tlb-latency.md
- contents/operating-system/kswapd-vs-direct-reclaim-latency.md
- contents/operating-system/major-minor-page-faults-runtime-diagnostics.md
- contents/operating-system/memory-management-numa-page-replacement-thrashing.md
- contents/operating-system/page-table-overhead-memory-footprint.md
- contents/operating-system/psi-pressure-stall-information-runtime-debugging.md
symptoms:
- allocation path에서 compaction이나 compact_stall이 발생하며 latency spike가 보인다.
- THP나 high-order allocation 때문에 page migration과 fragmentation 비용이 튄다.
- free memory는 있어 보이지만 contiguous page를 못 찾아 stall이 난다.
expected_queries:
- memory compaction과 fragmentation이 latency spike를 만드는 이유는?
- buddy allocator high-order allocation과 compact_stall을 어떻게 해석해?
- THP allocation이 compaction을 유발해 tail latency를 키울 수 있어?
- free memory가 있어도 contiguous page 부족으로 stall이 나는 상황을 설명해줘
contextual_chunk_prefix: |
  이 문서는 compaction이 흩어진 page를 모아 high-order allocation을 만족시키는 작업이지만
  fragmentation이 심하면 page migration과 compact_stall 자체가 latency spike가 된다는 점을
  운영 증상과 연결한다.
---
# Compaction, Fragmentation, Latency

> 한 줄 요약: compaction은 흩어진 페이지를 모으는 작업이지만, fragmentation이 심하면 그 자체가 latency spike가 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [THP, Huge Pages, TLB Latency](./thp-huge-pages-tlb-latency.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)
> - [Page Table Overhead, Memory Footprint](./page-table-overhead-memory-footprint.md)

> retrieval-anchor-keywords: compaction, fragmentation, buddy allocator, order allocation, migrate pages, memory fragmentation, CMA, latency spike, compact_stall

## 핵심 개념

Linux 메모리 allocator는 연속된 큰 블록을 필요로 할 때가 있다. 메모리가 조각나 있으면 큰 연속 공간을 만들기 위해 compaction이 필요하다.

- `fragmentation`: 메모리가 흩어져 큰 연속 블록이 만들기 어려운 상태다
- `compaction`: 페이지를 이동시켜 연속 공간을 만드는 작업이다
- `order allocation`: 여러 페이지가 연속된 블록 할당이다

왜 중요한가:

- huge page, DMA, 큰 buffer 할당은 fragmentation에 민감하다
- compaction은 backend 작업 같지만 latency를 직접 흔든다
- fragmentation이 심하면 allocation이 늦고 실패할 수 있다

이 문서는 [THP, Huge Pages, TLB Latency](./thp-huge-pages-tlb-latency.md)와 [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)를 묶어 compaction 비용을 본다.

## 깊이 들어가기

### 1. fragmentation은 "메모리가 부족하다"와 다르다

총 메모리가 남아도 연속 공간이 없으면 큰 할당은 어렵다.

- free memory가 충분해 보일 수 있다
- order-0는 되는데 큰 order는 실패할 수 있다
- compaction이 필요한 상황이 늘어난다

### 2. compaction은 페이지를 옮기는 비용이 있다

페이지 이동은 단순 정리가 아니다.

- data copy가 필요하다
- page lock과 migration이 걸린다
- 요청 경로에 들어오면 latency가 튄다

### 3. THP와 fragmentation은 서로 맞물린다

THP는 큰 페이지를 만들기 위해 compaction을 요구할 수 있다.

- huge page를 만들려다 compaction이 발생한다
- fragmentation이 심할수록 THP가 불안정해진다
- latency 서버에서는 기대보다 손해가 클 수 있다

### 4. fragmentation은 workload 패턴으로 악화된다

- 작은 객체를 오래 유지한다
- 크고 작은 allocation이 섞인다
- 메모리를 자주 allocate/free한다

## 실전 시나리오

### 시나리오 1: 메모리 사용률이 높지 않은데 huge allocation이 실패한다

가능한 원인:

- fragmentation이 심하다
- 연속 공간이 없다
- compaction이 따라잡지 못한다

진단:

```bash
grep -E 'compact|allocstall' /proc/vmstat
cat /proc/buddyinfo
cat /proc/pagetypeinfo | head -n 40
```

### 시나리오 2: latency spike가 특정 시점에만 보인다

가능한 원인:

- compaction burst
- THP collapse/split
- direct reclaim과 겹침

### 시나리오 3: 노드를 오래 돌릴수록 큰 할당이 불안해진다

가능한 원인:

- 장기 fragmentation 누적
- GC나 cache churn
- mixed-size allocation 패턴

## 코드로 보기

### fragment/compaction 상태 확인

```bash
cat /proc/buddyinfo
cat /proc/pagetypeinfo | head -n 30
grep -E 'compact|migrate' /proc/vmstat
```

### 감각 모델

```text
many small allocations and frees
  -> memory becomes fragmented
  -> large contiguous allocation needs compaction
  -> compaction can stall and hurt latency
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| compaction 허용 | 큰 연속 공간을 만든다 | latency spike 가능 | huge page/DMA |
| fragmentation 방치 | 즉시 비용이 없다 | 큰 할당 실패 위험 | 비권장 |
| THP 정책 조정 | compaction 압박을 줄일 수 있다 | TLB 이득이 줄 수 있다 | latency-sensitive |
| memory headroom 확보 | compaction 빈도 감소 | 자원 효율 저하 | 핵심 인프라 |

## 꼬리질문

> Q: fragmentation은 왜 문제인가요?
> 핵심: 총 메모리가 있어도 큰 연속 공간이 없을 수 있기 때문이다.

> Q: compaction은 왜 느린가요?
> 핵심: 페이지를 옮기고 잠그는 작업이 들어가기 때문이다.

> Q: THP와 어떤 관계가 있나요?
> 핵심: huge page 생성이 compaction을 유발하거나 악화시킬 수 있다.

## 한 줄 정리

compaction은 fragmented memory를 복구하는 수단이지만, fragmentation이 심할수록 그 자체가 latency spike와 allocation 실패의 원인이 된다.
