# Capacity Estimation Master Note

> 한 줄 요약: capacity estimation is a model for turning product assumptions into resource budgets before the system starts failing under real traffic.

**Difficulty: Advanced**

> retrieval-anchor-keywords: back of envelope, QPS, p95, p99, headroom, peak factor, throughput, storage growth, bandwidth, memory budget, connection count, shard sizing, hot key, queue depth, saturation

> related docs:
> - [Back-of-Envelope Estimation](../contents/system-design/back-of-envelope-estimation.md)
> - [System Design Framework](../contents/system-design/system-design-framework.md)
> - [Rate Limiter Design](../contents/system-design/rate-limiter-design.md)
> - [Distributed Cache Design](../contents/system-design/distributed-cache-design.md)
> - [load average, CPU saturation](../contents/operating-system/run-queue-load-average-cpu-saturation.md)
> - [OOM Killer, cgroup Memory Pressure](../contents/operating-system/oom-killer-cgroup-memory-pressure.md)
> - [Hikari Connection Pool Tuning](../contents/database/hikari-connection-pool-tuning.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Topic Map](../rag/topic-map.md)

## 핵심 개념

Capacity estimation is not exact math.

It is a structured guess that answers:

- how much load is expected
- what the hot path costs
- where the headroom must stay
- what breaks first when we are wrong

The result should be a decision, not a perfectly precise number.

## 깊이 들어가기

### 1. Estimate the shape of load

First estimate:

- average traffic
- peak traffic
- burst factor
- read/write ratio
- request size
- data growth per day

### 2. Convert demand into resource buckets

Each request consumes:

- CPU
- memory
- connections
- storage I/O
- bandwidth
- queue capacity

That is why one request path can look fine in QPS terms and still fail on memory or connection count.

### 3. Headroom is part of the design

If the design uses 90 to 95 percent of a resource under peak, it is already fragile.

We want room for:

- retry storms
- failover
- cache miss spikes
- deploy rollouts
- noisy neighbors

### 4. Estimation must connect to the bottleneck

If the hottest bottleneck is DB connections, increasing CPU does not help.
If the bottleneck is memory pressure, more threads may hurt.

Read with:

- [Hikari Connection Pool Tuning](../contents/database/hikari-connection-pool-tuning.md)
- [OOM Killer, cgroup Memory Pressure](../contents/operating-system/oom-killer-cgroup-memory-pressure.md)
- [run queue, load average, CPU saturation](../contents/operating-system/run-queue-load-average-cpu-saturation.md)

## 실전 시나리오

### 시나리오 1: expected QPS fits, but the service still fails

Likely missed dimension:

- connection count
- memory growth
- downstream latency
- queue saturation

### 시나리오 2: the cache looks cheap until hot key traffic arrives

Likely missed dimension:

- per-key concentration
- request coalescing cost
- invalidation spikes

### 시나리오 3: one region needs more capacity than the others

Likely missed dimension:

- traffic skew
- failover reserve
- replication lag

### 시나리오 4: batch job meets prod traffic and causes overload

Likely missed dimension:

- shared pool contention
- I/O interference
- peak overlap

## 코드로 보기

### Simple capacity worksheet

```text
QPS peak = average QPS * burst factor
db connections needed = concurrent requests * db time / request time slice
storage growth per month = daily growth * 30
safe headroom = 1 - peak_utilization
```

### Rough throughput estimate

```java
double peakQps = averageQps * burstFactor;
double latencySeconds = p95LatencyMillis / 1000.0;
double concurrency = peakQps * latencySeconds;
```

### Guardrail example

```yaml
capacity:
  cpu_headroom: 30%
  memory_headroom: 25%
  db_connection_headroom: 20%
  queue_headroom: 40%
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Conservative estimate | Safer launch | More infra cost | New systems |
| Aggressive estimate | Lower spend | Higher outage risk | Prototypes or controlled pilots |
| Per-service sizing | Better fit | More planning work | Mature architectures |
| Shared pool sizing | Simpler ops | Noisy neighbor risk | Smaller systems |

## 꼬리질문

> Q: Why is capacity estimation useful if it is only approximate?
> Intent: checks systems judgment.
> Core: rough models are enough to reveal the first bottleneck and the required headroom.

> Q: What is the biggest mistake in capacity planning?
> Intent: checks bottleneck awareness.
> Core: sizing one resource while ignoring the real one that fails first.

> Q: Why is headroom important?
> Intent: checks operational margin thinking.
> Core: production needs room for bursts, retries, and failure recovery.

> Q: Why do latency numbers matter in capacity planning?
> Intent: checks queueing math awareness.
> Core: concurrency is demand multiplied by time in system.

## 한 줄 정리

Capacity estimation is the bridge from product assumptions to resource budgets, and the safest plan keeps enough headroom for the first thing that goes wrong.
