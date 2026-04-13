# Resource Exhaustion Master Note

> 한 줄 요약: resource exhaustion is what happens when a system keeps accepting work after one of its finite budgets has already run out.

**Difficulty: Advanced**

> retrieval-anchor-keywords: OOMKilled, file descriptor leak, ephemeral port exhaustion, conntrack full, thread pool saturation, memory pressure, cgroup throttle, disk full, swap storm, backpressure, queue growth, native memory, RSS, kernel limit

> related docs:
> - [OOM Killer, cgroup Memory Pressure](../contents/operating-system/oom-killer-cgroup-memory-pressure.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](../contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md)
> - [run queue, load average, CPU saturation](../contents/operating-system/run-queue-load-average-cpu-saturation.md)
> - [NAT, conntrack, ephemeral port exhaustion](../contents/network/nat-conntrack-ephemeral-port-exhaustion.md)
> - [Connection Keepalive, Load Balancing, Circuit Breaker](../contents/network/connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Executor Sizing / Queue / Rejection Policy](../contents/language/java/executor-sizing-queue-rejection-policy.md)
> - [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](../contents/spring/spring-resilience4j-retry-circuit-breaker-bulkhead.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

Resource exhaustion is not one thing.

It can be:

- memory exhaustion
- file descriptor exhaustion
- thread exhaustion
- connection exhaustion
- port exhaustion
- disk or inode exhaustion
- queue exhaustion

The symptom is often misleading.

- the app is "slow"
- the pod is "restarting"
- requests are "timing out"
- DB is "down"

But the real issue is often that one finite resource has crossed its safe budget.

## 깊이 들어가기

### 1. Every budget has a different failure shape

- memory exhaustion often becomes reclaim, swapping, then OOM
- fd exhaustion prevents new opens or sockets
- thread exhaustion turns work into queueing delay
- port exhaustion blocks outbound connections
- disk exhaustion breaks writes, logs, and temp files

The trick is to identify which budget is being consumed fastest.

### 2. Saturation is the early warning

Before hard failure, the system usually shows pressure:

- rising queue length
- rising latency
- growing RSS or heap
- increased context switching
- growing conntrack table
- dirty page buildup

That is the point to intervene.

### 3. Containment matters more than raw scale

Adding more workers, more retries, or larger pools can make the failure worse.

Containment tools include:

- backpressure
- bulkhead
- admission control
- rate limiting
- tighter timeouts
- bounded queues

### 4. The OS and the app share the same budget

When Java heap grows, the node can still die because of:

- native memory
- thread stacks
- page cache
- mmap
- kernel tables

That is why OS-level resource docs matter together:

- [OOM Killer, cgroup Memory Pressure](../contents/operating-system/oom-killer-cgroup-memory-pressure.md)
- [File Descriptor, Socket, Syscall Cost, and Server Impact](../contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md)

## 실전 시나리오

### 시나리오 1: pod keeps restarting with `OOMKilled`

Likely causes:

- heap too large for cgroup limit
- native memory spike
- direct buffer growth
- memory pressure from another process

### 시나리오 2: outbound calls suddenly fail

Likely causes:

- ephemeral port exhaustion
- conntrack table full
- too many keepalive connections

### 시나리오 3: logs stop or temp file writes fail

Likely causes:

- disk full
- inode exhaustion
- permission or mount pressure

### 시나리오 4: CPU is not maxed, but latency explodes

Likely causes:

- thread pool saturation
- lock contention
- kernel throttle
- queue buildup

## 코드로 보기

### Bounded executor sketch

```java
ThreadPoolExecutor executor = new ThreadPoolExecutor(
    8,
    32,
    30, TimeUnit.SECONDS,
    new ArrayBlockingQueue<>(200),
    new ThreadPoolExecutor.AbortPolicy()
);
```

### Simple resource guard

```java
if (queue.size() > 150) {
    throw new TooBusyException("system under pressure");
}
```

### OS triage commands

```bash
ps -eo pid,rss,vsz,comm --sort=-rss | head
ss -s
cat /proc/sys/net/netfilter/nf_conntrack_count
df -h
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Bigger pool | Absorbs bursts | More contention | Short-lived spikes |
| Smaller pool | Bounded damage | More queueing | Stability-first services |
| Unlimited queue | Easy to accept work | Latency blow-up | Rarely, only with strict upstream control |
| Backpressure | Protects core service | Rejects some traffic | Any saturated system |
| Horizontal scale | More total capacity | More moving parts | Sustained load growth |

## 꼬리질문

> Q: Why can a system fail before CPU is fully used?
> Intent: checks queue and non-CPU resource awareness.
> Core: memory, sockets, ports, or threads may exhaust first.

> Q: Why does adding workers sometimes make exhaustion worse?
> Intent: checks saturation and contention understanding.
> Core: more workers can increase memory, context switching, and downstream pressure.

> Q: Why is OOM only one kind of resource failure?
> Intent: checks multi-resource thinking.
> Core: many failures come from fd, port, disk, or queue limits.

> Q: What is the best first defense?
> Intent: checks operational judgment.
> Core: bound the work, then reject or shed load before the system collapses.

## 한 줄 정리

Resource exhaustion is a budgeting problem, and the safest response is to bound the work before the resource budget is completely gone.
