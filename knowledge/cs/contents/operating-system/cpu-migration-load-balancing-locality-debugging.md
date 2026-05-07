---
schema_version: 3
title: CPU Migration Load Balancing Locality Debugging
concept_id: operating-system/cpu-migration-load-balancing-locality-debugging
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- cpu-migration-load
- balancing-locality
- cpu-migration-locality
- scheduler-load-balancing
aliases:
- CPU migration locality debugging
- scheduler load balancing
- migration churn
- backend p99 CPU migration
- run queue locality
- task migration cache locality
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/cpu-affinity-irq-affinity-core-locality.md
- contents/operating-system/schedstat-proc-sched-runtime-debugging.md
- contents/operating-system/scheduler-wakeup-latency-runqlat-debugging.md
- contents/operating-system/autonuma-vs-manual-locality-tradeoffs.md
- contents/operating-system/numa-autobalancing-runtime-debugging.md
- contents/operating-system/cfs-scheduler-nice-cpu-fairness.md
symptoms:
- 평균 CPU 사용률은 괜찮은데 migration churn 때문에 cache locality가 깨지고 p99가 흔들린다.
- scheduler가 load balancing을 위해 task를 옮기지만 hot path locality가 손실된다.
- affinity를 완전히 고정하자 load imbalance가 생겨 다른 형태의 latency가 나타난다.
expected_queries:
- CPU migration과 scheduler load balancing은 locality와 어떤 긴장 관계야?
- migration churn이 backend p99 latency를 흔드는지 어떻게 디버깅해?
- schedstat와 runqlat로 task migration wakeup latency를 어떻게 봐?
- CPU affinity를 고정할지 scheduler balancing에 맡길지 판단 기준은?
contextual_chunk_prefix: |
  이 문서는 task를 여러 CPU에 고르게 퍼뜨리는 load balancing과 같은 core에 오래 붙여
  cache/NUMA locality를 살리는 목표가 긴장 관계에 있다는 점을 설명한다. migration churn,
  schedstat, runqlat, backend p99를 연결한다.
---
# CPU Migration, Load Balancing, Locality Debugging

> 한 줄 요약: 태스크를 여러 CPU에 고르게 퍼뜨리는 것과 같은 코어에 오래 붙여 locality를 살리는 것은 서로 긴장 관계에 있고, migration churn이 커지면 평균 CPU가 멀쩡해도 backend p99는 쉽게 흔들린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)
> - [schedstat, /proc/<pid>/sched, Runtime Debugging](./schedstat-proc-sched-runtime-debugging.md)
> - [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)
> - [AutoNUMA vs Manual Locality Trade-offs](./autonuma-vs-manual-locality-tradeoffs.md)
> - [NUMA Auto Balancing, Runtime Debugging](./numa-autobalancing-runtime-debugging.md)
> - [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)

> retrieval-anchor-keywords: cpu migration, load balancing, cache locality, scheduler domain, task migration, hot core, migration churn, run queue rebalance, locality loss, cpu pinning tradeoff

## 핵심 개념

리눅스 스케줄러는 단순히 "빈 CPU에 던진다"로 끝나지 않는다. runnable load를 여러 CPU에 나누려는 힘과, 이미 따뜻한 캐시/TLB/locality를 유지하려는 힘이 동시에 작동한다. migration은 이 둘 사이 균형 장치지만, 과하면 지연을 만든다.

- `migration`: 태스크가 한 CPU에서 다른 CPU로 이동하는 일이다
- `load balancing`: runnable load를 여러 CPU에 나눠 과열된 코어를 줄이는 동작이다
- `locality`: 같은 코어/소켓/NUMA 노드에 머물며 캐시 재사용을 얻는 성질이다
- `migration churn`: 짧은 시간 안에 태스크가 자주 옮겨 다니는 상태다

왜 중요한가:

- CPU 평균은 안정적인데 특정 request p99만 나빠지는 원인을 설명할 수 있다
- event loop, lock owner, softirq completion thread가 migration에 민감하다
- affinity를 너무 세게 주든 너무 느슨하게 두든 둘 다 tail latency를 키울 수 있다

## 깊이 들어가기

### 1. 분산이 항상 좋은 것도, 고정이 항상 좋은 것도 아니다

스케줄러는 한 CPU의 run queue가 길어지면 다른 CPU로 옮기고 싶어 한다. 하지만 이동에는 비용이 있다.

- cache warmth를 잃는다
- TLB/locality가 깨진다
- 같은 데이터를 다시 다른 코어 cache로 불러와야 한다

그래서 migration은 "공짜 load balance"가 아니라 queueing과 locality 사이 교환이다.

### 2. 짧은 태스크일수록 migration 비용이 더 크게 보일 수 있다

작업이 아주 짧은 event-loop handler, small RPC worker, lock handoff task일수록 계산보다 locality 손실이 체감에 더 크게 나온다.

- CPU 실제 계산 시간은 짧다
- migration 후 cache warmup 비중이 커진다
- p99가 average보다 먼저 나빠진다

즉 짧은 interactive task는 throughput보다 placement 품질에 민감하다.

### 3. migration churn은 종종 다른 문제의 2차 증상이다

migration이 많다고 해서 root cause가 migration 자체인 것은 아니다.

- run queue imbalance
- IRQ/worker misalignment
- cpuset 구성 불균형
- cgroup quota로 인한 bursty runnable 패턴

그래서 migration은 단독 지표보다 run queue, affinity, irq locality와 함께 봐야 한다.

### 4. NUMA와 결합되면 비용이 한 단계 더 커진다

다른 CPU로 옮기는 것만이 아니라, 다른 소켓/NUMA 노드로 옮기면 메모리 locality까지 깨질 수 있다.

- remote memory 접근이 늘 수 있다
- page fault/reclaim 비용도 더 나빠질 수 있다
- "CPU는 여유인데 왜 응답이 나빠졌지?"라는 현상이 나온다

즉 CPU migration은 곧 메모리 locality 문제이기도 하다.

## 실전 시나리오

### 시나리오 1: event loop 한두 개가 계속 다른 CPU를 오가며 p99를 만든다

가능한 원인:

- affinity가 너무 넓어 balancing이 과도하다
- 같은 노드의 다른 bursty task가 해당 CPU set을 흔든다
- epoll wakeup 후 locality가 매번 바뀐다

진단:

```bash
cat /proc/<tid>/sched
sudo perf sched timehist -p <pid> -- sleep 10
mpstat -P ALL 1
```

판단 포인트:

- suspect TID의 migration 흔적이 두드러지는가
- run delay와 migration churn이 같이 나타나는가
- 특정 CPU 집합 안에서만 bouncing이 생기는가

### 시나리오 2: affinity를 완화했더니 throughput은 올랐지만 p99가 흔들린다

가능한 원인:

- 분산은 좋아졌지만 cache locality가 깨졌다
- lock owner와 waiter가 다른 코어로 흩어진다
- hot connection state가 같은 코어에 머물지 못한다

### 시나리오 3: IRQ를 분산했는데 오히려 application tail이 늘었다

가능한 원인:

- packet completion과 application worker가 다른 CPU에서 만나 locality를 잃는다
- network softirq와 worker handoff가 더 멀어졌다
- CPU 균형은 좋아졌지만 end-to-end request path locality는 나빠졌다

## 코드로 보기

### per-thread scheduler 상태

```bash
cat /proc/<tid>/sched
```

### timehist로 migration 보기

```bash
sudo perf sched timehist -p <pid> -- sleep 10
```

### CPU 분포 보기

```bash
mpstat -P ALL 1
ps -eLo pid,tid,psr,comm | head
```

### mental model

```text
too little balancing
  -> hot core, long run queue

too much balancing
  -> migration churn, locality loss

best point
  -> enough spread, but stable placement for hot paths
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| aggressive balancing | hot core를 줄인다 | locality 손실이 커질 수 있다 | throughput 우선 |
| stable pinning | cache/locality에 유리하다 | 한 코어 과열 위험이 있다 | low-latency hot path |
| limited cpuset | noisy neighbor를 줄인다 | set 안에서 imbalance가 심해질 수 있다 | workload isolation |
| IRQ/worker alignment | end-to-end locality를 살릴 수 있다 | 설계가 복잡하다 | latency-sensitive networking |

## 꼬리질문

> Q: CPU migration이 많으면 항상 나쁜가요?
> 핵심: 항상 그런 것은 아니지만, 짧고 hot한 backend task에서는 locality 손실과 tail latency로 이어지기 쉽다.

> Q: 한 CPU가 뜨거운 게 더 나쁜가요, migration churn이 더 나쁜가요?
> 핵심: workload에 따라 다르다. 목표는 둘 중 하나를 극단화하는 게 아니라 hot path에 맞는 균형점을 찾는 것이다.

> Q: migration 문제를 볼 때 NUMA를 왜 같이 보나요?
> 핵심: CPU 이동이 메모리 locality 손실까지 함께 만들 수 있기 때문이다.

## 한 줄 정리

스케줄러의 load balancing 문제는 "CPU를 고르게 쓰는가"보다 "backend의 hot path가 locality를 잃지 않으면서도 과열되지 않는가"로 읽는 편이 정확하다.
