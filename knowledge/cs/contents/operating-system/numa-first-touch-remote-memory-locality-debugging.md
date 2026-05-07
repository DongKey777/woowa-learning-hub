---
schema_version: 3
title: NUMA First Touch Remote Memory Locality Debugging
concept_id: operating-system/numa-first-touch-remote-memory-locality-debugging
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- numa-first-touch
- remote-memory-locality
- memory-node-placement
- numastat-remote-access
aliases:
- NUMA first touch
- remote memory locality debugging
- memory node placement
- numastat remote access
- CPU memory locality
- first-touch allocation policy
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/operating-system/numa-production-debugging.md
- contents/operating-system/numa-autobalancing-runtime-debugging.md
- contents/operating-system/autonuma-vs-manual-locality-tradeoffs.md
- contents/operating-system/cpu-affinity-irq-affinity-core-locality.md
- contents/operating-system/cpu-migration-load-balancing-locality-debugging.md
- contents/operating-system/cpuset-isolation-noisy-neighbors.md
symptoms:
- CPU는 local core에서 도는 것 같지만 memory가 다른 NUMA node에 first-touch되어 remote latency가 난다.
- worker placement와 memory allocation thread가 달라 locality가 깨진다.
- numastat이나 perf counters로 remote access를 봐야 하는데 CPU affinity만 보고 있다.
expected_queries:
- NUMA first-touch는 memory가 어느 node에 배치되는지를 어떻게 결정해?
- remote memory access는 CPU affinity만 봐서는 왜 해결되지 않아?
- worker placement와 allocation thread를 맞춰 locality를 살리는 방법은?
- NUMA locality debugging에서 numastat과 remote access를 어떻게 해석해?
contextual_chunk_prefix: |
  이 문서는 NUMA 문제를 CPU가 어느 core에서 도는가보다 memory가 어느 node에 처음 배치됐고
  지금 어떤 CPU가 remote로 읽고 있는가의 문제로 본다. first-touch, worker placement,
  CPU/IRQ affinity, cpuset isolation을 연결한다.
---
# NUMA First-Touch, Remote Memory, Locality Debugging

> 한 줄 요약: NUMA 문제는 "CPU가 어느 코어에서 도나"보다 "메모리가 어느 노드에 처음 배치됐고 지금 누가 remote로 읽고 있나"를 봐야 풀리는 경우가 많다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [NUMA Production Debugging](./numa-production-debugging.md)
> - [NUMA Auto Balancing, Runtime Debugging](./numa-autobalancing-runtime-debugging.md)
> - [AutoNUMA vs Manual Locality Trade-offs](./autonuma-vs-manual-locality-tradeoffs.md)
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)
> - [CPU Migration, Load Balancing, Locality Debugging](./cpu-migration-load-balancing-locality-debugging.md)
> - [memory-management, NUMA, page replacement, thrashing](./memory-management-numa-page-replacement-thrashing.md)

> retrieval-anchor-keywords: NUMA first touch, remote memory, local memory, memory locality, numa_maps, numastat, remote faults, first-touch allocation, remote node access, locality debugging

## 핵심 개념

NUMA 서버에서 latency를 깎는 핵심은 "메모리를 local에서 본다"는 것이다. 이때 가장 자주 놓치는 부분이 first-touch allocation이다. 즉, 어느 스레드가 어떤 노드에서 그 페이지를 처음 건드렸는지가 이후 locality를 좌우할 수 있다.

- `first touch`: 페이지가 처음 실제 할당되는 시점의 접근 패턴이다
- `local memory`: 현재 CPU와 같은 NUMA node의 메모리다
- `remote memory`: 다른 NUMA node의 메모리다
- `numa_maps`: 프로세스 메모리 배치 힌트를 보여 주는 인터페이스다

왜 중요한가:

- 초기화 스레드 하나가 거대한 heap/buffer를 한 node에 몰아넣을 수 있다
- 이후 worker가 다른 node에서 접근하면 remote latency가 계속 따라다닌다
- CPU 사용률보다 메모리 거리 때문에 backend p99가 흔들릴 수 있다

## 깊이 들어가기

### 1. first touch는 "초기화 코드"를 운영 문제로 바꾼다

많은 팀이 steady-state worker만 본다. 하지만 메모리 배치는 종종 초기화 순간 이미 결정된다.

- single-thread bootstrap이 거대한 buffer를 만든다
- JVM/native cache warmup이 한 소켓에서 일어난다
- 이후 다수 worker는 다른 소켓에서 remote access를 한다

그래서 first-touch는 코드 스타일이 아니라 production placement 문제다.

### 2. CPU affinity만 맞춰도 끝나지 않는다

특정 CPU에 워커를 고정해도 메모리가 다른 node에 있으면 locality는 여전히 나쁘다.

- CPU pinning은 compute placement다
- NUMA locality는 memory placement다
- 둘을 함께 봐야 실제 remote access가 줄어든다

즉 CPU pinning은 필요조건일 수 있어도 충분조건은 아니다.

### 3. AutoNUMA는 도움도 되고 지터도 만든다

autoNUMA는 remote access를 줄이려 페이지 migration을 시도할 수 있다.

- 잘 맞으면 locality가 좋아진다
- 잘못 맞으면 page migration과 fault overhead가 커진다
- 짧은 latency-sensitive path에서는 지터가 더 중요할 수 있다

그래서 autoNUMA는 "켜면 좋아진다"보다 "어떤 workload에서 더 예측 가능한가"로 봐야 한다.

### 4. remote memory는 lock contention과도 섞인다

같은 shared structure를 여러 node가 건드리면 다음이 동시에 생길 수 있다.

- cache coherence traffic
- remote memory latency
- lock handoff 비용

그래서 NUMA 문제는 memory 문제이면서 lock/scheduling 문제이기도 하다.

## 실전 시나리오

### 시나리오 1: startup 직후부터 특정 서비스 p99가 계속 나쁘다

가능한 원인:

- bootstrap thread가 한 node에만 큰 메모리를 배치했다
- worker는 다른 node들에 분산됐다
- steady state 전부터 remote memory pattern이 굳어졌다

진단:

```bash
numastat -p <pid>
cat /proc/<pid>/numa_maps | head -n 40
numactl --show
```

판단 포인트:

- 특정 node에 메모리 배치가 유난히 쏠렸는가
- worker CPU 분포와 메모리 node 분포가 엇갈리는가

### 시나리오 2: CPU를 잘 분산했는데도 tail latency가 개선되지 않는다

가능한 원인:

- compute placement는 좋아졌지만 memory는 remote다
- migration churn으로 locality가 계속 깨진다
- page cache/file cache 자체가 다른 node에 무겁게 있다

### 시나리오 3: AutoNUMA를 켰더니 평균은 좋아졌는데 지터가 늘었다

가능한 원인:

- page migration/fault overhead가 tail에 더 민감하게 반영됐다
- worker hot path가 짧아 migration 비용이 상대적으로 커졌다
- batch와 API가 같은 node set에서 다른 locality 요구를 가진다

## 코드로 보기

### 핵심 관찰

```bash
numastat -p <pid>
cat /proc/<pid>/numa_maps | head -n 40
```

### mental model

```text
init thread on node 0
  -> first-touch allocates many pages on node 0

workers later run on node 1
  -> remote memory latency becomes steady-state tax
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| single-node first touch | 구현이 단순하다 | remote access를 쉽게 만든다 | 작은 memory footprint |
| NUMA-aware initialization | locality를 개선한다 | init 설계가 복잡해진다 | large heaps/buffers |
| AutoNUMA 활용 | 운영 개입 없이 개선될 수 있다 | migration 지터가 생길 수 있다 | throughput-oriented workloads |
| explicit pinning + placement | 예측 가능성이 높다 | 운영 유연성이 낮아진다 | ultra latency-sensitive paths |

## 꼬리질문

> Q: NUMA 문제를 볼 때 first touch가 왜 중요하나요?
> 핵심: 첫 실제 접근이 페이지 배치를 결정해 이후 remote access 패턴을 오래 끌고 갈 수 있기 때문이다.

> Q: CPU affinity를 걸었는데도 느릴 수 있는 이유는?
> 핵심: CPU는 local이어도 메모리가 remote면 locality 이득이 충분하지 않기 때문이다.

> Q: AutoNUMA는 항상 도움이 되나요?
> 핵심: 아니다. locality를 개선할 수도 있지만 migration/fault 지터를 키울 수도 있다.

## 한 줄 정리

NUMA locality는 steady-state thread placement만이 아니라 first-touch allocation history까지 같이 봐야 제대로 읽힌다.
