---
schema_version: 3
title: NUMA Auto Balancing Runtime Debugging
concept_id: operating-system/numa-autobalancing-runtime-debugging
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- numa-autobalancing
- numa-auto-balancing
- automatic-numa-balancing
- numa-hint-fault
aliases:
- NUMA auto balancing debugging
- automatic NUMA balancing
- NUMA hint fault
- page migration latency
- remote memory access
- autonuma runtime
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/memory-management-numa-page-replacement-thrashing.md
- contents/operating-system/numa-production-debugging.md
- contents/operating-system/numa-first-touch-remote-memory-locality-debugging.md
- contents/operating-system/autonuma-vs-manual-locality-tradeoffs.md
- contents/operating-system/major-minor-page-faults-runtime-diagnostics.md
symptoms:
- AutoNUMA가 page migration과 hint fault를 늘려 오히려 latency를 키우는 workload가 있다.
- remote memory access가 줄어드는지, migration cost가 더 큰지 runtime에서 확인해야 한다.
- manual locality tuning과 automatic balancing 중 어느 쪽이 맞는지 판단해야 한다.
expected_queries:
- NUMA auto balancing은 항상 memory locality를 좋게 만들어?
- hint fault와 page migration이 latency를 키우는지 어떻게 디버깅해?
- AutoNUMA와 first-touch cpuset manual locality tuning을 어떻게 비교해?
- remote memory access와 page migration cost를 운영 지표로 어떻게 봐?
contextual_chunk_prefix: |
  이 문서는 NUMA auto balancing이 memory locality를 자동으로 좋게 만들려는 시도지만
  workload에 따라 hint fault와 page migration 비용이 remote access 절감보다 커져 latency를
  키울 수 있다는 runtime debugging playbook이다.
---
# NUMA Auto Balancing, Runtime Debugging

> 한 줄 요약: NUMA auto balancing은 메모리를 "자동으로 더 좋게" 만들려는 시도지만, 워크로드에 따라 page migration과 hint fault가 오히려 지연을 키울 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)
> - [NUMA Production Debugging](./numa-production-debugging.md)
> - [NUMA First-Touch, Remote Memory, Locality Debugging](./numa-first-touch-remote-memory-locality-debugging.md)
> - [AutoNUMA vs Manual Locality Trade-offs](./autonuma-vs-manual-locality-tradeoffs.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [THP, Huge Pages, TLB Latency](./thp-huge-pages-tlb-latency.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)

> retrieval-anchor-keywords: autoNUMA, numa balancing, numa_hint_faults, numa_pages_migrated, page migration, local memory, remote memory, memory locality

## 핵심 개념

NUMA auto balancing은 스레드가 실제로 많이 접근하는 메모리를 더 가까운 NUMA 노드로 옮기려는 커널 기능이다. 목적은 locality를 개선하는 것이지만, 실제로는 page migration과 hint fault가 추가 비용을 만든다.

- `AutoNUMA`: 자동으로 메모리 위치를 재조정하려는 메커니즘이다
- `hint fault`: 커널이 페이지 접근 패턴을 알아내기 위해 일부 fault를 유도하는 방식이다
- `page migration`: 페이지를 다른 NUMA 노드로 옮기는 작업이다
- `local memory`: 현재 CPU와 가까운 메모리다
- `remote memory`: 다른 NUMA 노드에 있는 메모리다

왜 중요한가:

- CPU는 남아 보여도 remote memory 때문에 느릴 수 있다
- AutoNUMA가 도움이 되는 서버도 있지만, latency 민감한 경로에서는 흔들릴 수 있다
- JVM, DB, 큰 heap 서버는 locality 변화가 바로 tail latency로 드러난다

이 문서는 [NUMA Production Debugging](./numa-production-debugging.md)과 [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)를 더 운영 관점으로 이어준다.

## 깊이 들어가기

### 1. AutoNUMA는 locality를 추정하는 기능이다

커널은 모든 페이지의 "정답 위치"를 미리 알 수 없다. 그래서 접근 패턴을 보고 자주 쓰는 페이지를 더 가까운 쪽으로 옮기려 한다.

- 자주 쓰는 데이터는 local memory로 옮기려 한다
- 잘못 추정하면 migration 비용만 늘어난다
- 짧은 생명주기의 데이터에는 오히려 불리할 수 있다

### 2. page migration은 공짜가 아니다

페이지를 옮기는 동안 다음 비용이 생긴다.

- old page와 new page를 동시에 관리한다
- 잠금과 복사 비용이 생긴다
- fault와 migration이 tail latency를 만들 수 있다

즉 AutoNUMA는 "더 가까이 배치"라는 이득과 "옮기느라 드는 비용"을 같이 봐야 한다.

### 3. hint fault는 관찰을 위한 비용이다

커널은 실제 접근을 추적하기 위해 hint fault를 사용한다. 이 과정은 locality 판단에는 좋지만, 애플리케이션 관점에서는 추가 fault처럼 보인다.

### 4. 모든 워크로드가 AutoNUMA에 잘 맞지는 않는다

- 대형 JVM heap
- 대용량 DB buffer pool
- CPU affinity가 강한 서버
- 짧고 bursty한 요청이 많은 API

이런 경우는 auto balancing이 이득보다 변동성을 더 키울 수 있다.

## 실전 시나리오

### 시나리오 1: CPU 사용률은 낮은데 p99가 흔들린다

가능한 원인:

- remote memory access가 많다
- AutoNUMA migration이 계속 일어난다
- hot page가 잘못된 NUMA 노드에 있다

진단:

```bash
numastat -p <pid>
cat /proc/<pid>/numa_maps | head
cat /proc/vmstat | grep -E 'numa_hint_faults|numa_pages_migrated'
```

### 시나리오 2: 워커를 늘렸더니 오히려 느려졌다

가능한 원인:

- 스레드가 다른 소켓 사이를 오간다
- 메모리 locality가 깨진다
- migration이 캐시 locality까지 흔든다

### 시나리오 3: 특정 시간대에만 간헐적 지연이 보인다

가능한 원인:

- AutoNUMA의 재배치 주기와 부하가 겹친다
- background migration이 burst와 충돌한다
- page fault와 reclaim이 함께 흔들린다

이 경우는 [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)와 같이 본다.

## 코드로 보기

### AutoNUMA 관련 상태 확인

```bash
cat /proc/sys/kernel/numa_balancing
numactl --show
```

### 프로세스별 locality 확인

```bash
cat /proc/<pid>/numa_maps | sed -n '1,20p'
numastat -p <pid>
```

### migration 감각을 보는 의사 코드

```text
access pattern observed
  -> hot pages estimated
  -> page migration scheduled
  -> locality improves or extra stall appears
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| AutoNUMA on | locality 개선 가능 | migration 비용이 든다 | locality가 중요한 대형 서버 |
| AutoNUMA off | 예측 가능성이 높다 | remote memory를 방치할 수 있다 | latency 민감 경로 |
| manual placement | 제어가 정밀하다 | 운영 복잡도 높다 | DB/JVM 핵심 서버 |

## 꼬리질문

> Q: AutoNUMA는 왜 항상 좋은가요?
> 핵심: 항상 좋지 않다. 잘못된 migration은 오히려 지연을 키운다.

> Q: hint fault는 왜 생기나요?
> 핵심: 커널이 실제 접근 패턴을 학습하기 위해서다.

> Q: NUMA 문제를 CPU 문제와 어떻게 구분하나요?
> 핵심: CPU는 남아 있는데 remote memory와 page migration이 늘면 NUMA를 의심한다.

## 한 줄 정리

NUMA auto balancing은 locality를 개선하려는 기능이지만, production에서는 migration 비용과 hint fault 때문에 오히려 tail latency를 흔들 수 있다.
