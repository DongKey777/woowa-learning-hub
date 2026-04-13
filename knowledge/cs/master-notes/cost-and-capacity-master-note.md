# Cost and Capacity Master Note

> 한 줄 요약: cost and capacity planning is about sizing the system so reliability is affordable and the first bottleneck is visible before customers feel it.

**Difficulty: Advanced**

> retrieval-anchor-keywords: capacity planning, cost model, headroom, throughput, bottleneck, resource budget, utilization, peak factor, forecast, cloud cost, qps, memory budget, connection budget

> related docs:
> - [Back-of-Envelope 추정법](../contents/system-design/back-of-envelope-estimation.md)
> - [Billing / Usage Metering System 설계](../contents/system-design/billing-usage-metering-system-design.md)
> - [OOM Killer, cgroup Memory Pressure](../contents/operating-system/oom-killer-cgroup-memory-pressure.md)
> - [run queue, load average, CPU saturation](../contents/operating-system/run-queue-load-average-cpu-saturation.md)
> - [Hikari Connection Pool Tuning](../contents/database/hikari-connection-pool-tuning.md)
> - [Rate Limiter 설계](../contents/system-design/rate-limiter-design.md)

## 핵심 개념

Capacity is the maximum useful work the system can sustain.
Cost is what it takes to keep that capacity available with headroom.

Good planning answers:

- which resource fails first
- how much headroom is required
- how much it costs to stay safe
- which metric tells us we are close to the cliff

## 깊이 들어가기

### 1. Capacity is multi-dimensional

You can have enough CPU but not enough connections, memory, or I/O.

### 2. Headroom is part of the price

Operating at 100% is not a real plan.
Reserve room for spikes, retries, failover, and deploys.

### 3. Billing and usage reveal demand

Usage metering tells you what customers actually consume, which can help estimate future capacity.

Read with:

- [Billing / Usage Metering System 설계](../contents/system-design/billing-usage-metering-system-design.md)

### 4. Use back-of-envelope math to find bottlenecks

Read with:

- [Back-of-Envelope 추정법](../contents/system-design/back-of-envelope-estimation.md)

### 5. Budget the shared resources

Connections, queues, and cgroup limits often fail before raw CPU does.

Read with:

- [OOM Killer, cgroup Memory Pressure](../contents/operating-system/oom-killer-cgroup-memory-pressure.md)
- [run queue, load average, CPU saturation](../contents/operating-system/run-queue-load-average-cpu-saturation.md)

## 실전 시나리오

### 시나리오 1: utilization looks fine but incidents increase

Likely cause:

- no headroom
- hidden bottleneck in connection or memory budget

### 시나리오 2: cost rises faster than traffic

Likely cause:

- overprovisioning
- duplicated infrastructure
- poor right-sizing

### 시나리오 3: database connection pool becomes the limit

Likely cause:

- concurrent request growth
- transaction times too long

## 코드로 보기

### Capacity sketch

```text
peak qps * p95 latency = concurrency
concurrency -> memory + connection + cpu budget
```

### Cost guardrail sketch

```yaml
capacity:
  cpu_headroom: 30%
  memory_headroom: 25%
  db_connection_headroom: 20%
```

### Utilization check

```bash
vmstat 1
ss -s
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Tight capacity | Lower spend | Less resilience | Stable low-risk services |
| Generous headroom | Safer | Higher cost | Customer-facing critical paths |
| Elastic scale | Flexible | Operational complexity | Variable traffic |
| Fixed sizing | Predictable | Less adaptable | Small steady workloads |

## 꼬리질문

> Q: Why does capacity planning affect reliability?
> Intent: checks headroom and failure margin.
> Core: without headroom, small spikes become incidents.

> Q: Why is cost not just a finance question?
> Intent: checks operational economics.
> Core: overprovisioning and underprovisioning both affect reliability.

> Q: Why can one resource bottleneck the whole system?
> Intent: checks multi-dimensional capacity thinking.
> Core: CPU, memory, connections, and I/O are all separate limits.

## 한 줄 정리

Cost and capacity planning is the discipline of buying enough headroom to keep the first bottleneck visible without paying for more than the system actually needs.
