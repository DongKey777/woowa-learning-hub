# Latency Debugging Master Note

> 한 줄 요약: latency debugging is not "making it faster" but finding where the time is spent across queueing, execution, retries, and contention.

**Difficulty: Advanced**

> retrieval-anchor-keywords: p99, p999, tail latency, queueing delay, off-CPU, run queue, thread pool saturation, GC pause, safepoint, slow query, lock contention, connect timeout, retry storm, fsync, cgroup throttle

> related docs:
> - [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md)
> - [Timeout Types: connect / read / write](../contents/network/timeout-types-connect-read-write.md)
> - [Slow Query Analysis Playbook](../contents/database/slow-query-analysis-playbook.md)
> - [eBPF, perf, strace production tracing](../contents/operating-system/ebpf-perf-strace-production-tracing.md)
> - [JFR / JMC performance playbook](../contents/language/java/jfr-jmc-performance-playbook.md)
> - [run queue, load average, CPU saturation](../contents/operating-system/run-queue-load-average-cpu-saturation.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Latency is the sum of many small waits, not a single slow function.

The first question is always:

- Is this queueing?
- Is this actual work?
- Is this amplification from retries or fan-out?
- Is this contention somewhere below the app?

The practical split is:

- client-side delay
- network delay
- application queueing
- runtime pauses
- database wait
- downstream wait
- kernel or storage wait

If you only look at average latency, you miss the real incident pattern: the median stays fine while the tail explodes.

## 깊이 들어가기

### 1. Start from the request timeline

A useful debugging habit is to map one request into phases:

```text
ingress -> app queue -> handler -> DB/downstream -> serialization -> egress
```

Then ask where the time moved when traffic increased.

If the phase is hidden, the usual suspects are:

- thread pool queue
- connection pool wait
- GC or safepoint
- lock contention
- kernel throttling
- downstream timeout and retry

### 2. Separate saturation from slowness

If CPU is high, latency can be caused by CPU saturation or context switching.
If CPU is low, latency can still be caused by waiting.

Common signals:

- high run queue and high load average: CPU pressure
- low CPU but many blocked threads: lock or I/O wait
- heap looks normal but RSS rises: off-heap or page cache pressure
- p50 stable but p99 jumps: tail amplification

### 3. Correlate app, JVM, OS, and DB

The same symptom can come from different layers:

- JVM: GC pause, warmup, deoptimization
- OS: context switch, NUMA, page faults, cgroup throttle
- Network: connect timeout, DNS, HOL blocking, retransmits
- DB: slow query, lock wait, pool starvation, fsync

Use the bridge map and query playbook together:

- [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
- [Query Playbook](../rag/query-playbook.md)

### 4. Retries often make latency worse

Retries are useful only if the system can absorb the extra load.

Bad pattern:

- upstream times out
- client retries immediately
- queue gets longer
- latency rises again
- more retries happen

That is retry amplification, not resilience.

## 실전 시나리오

### 시나리오 1: p99 only spikes under traffic

Likely cause:

- queueing delay
- pool exhaustion
- thread contention
- downstream saturation

### 시나리오 2: CPU is not maxed but the API is slow

Likely cause:

- DB lock wait
- remote dependency latency
- kernel or network wait
- blocked thread pools

### 시나리오 3: latency got worse after a deploy

Likely cause:

- JIT warmup
- connection pool reset
- cache cold start
- new retry path
- different SQL plan

### 시나리오 4: latency is fine until a retry storm begins

Likely cause:

- timeout too aggressive
- retry policy missing jitter
- no circuit breaker
- no admission control

## 코드로 보기

### Basic phase timing in Java

```java
long start = System.nanoTime();

User user = userRepository.findById(userId);
long afterDb = System.nanoTime();

OrderResult result = downstreamClient.call(user);
long afterDownstream = System.nanoTime();

log.info(
    "db={}ms downstream={}ms total={}ms",
    (afterDb - start) / 1_000_000,
    (afterDownstream - afterDb) / 1_000_000,
    (afterDownstream - start) / 1_000_000
);
```

### Operational commands

```bash
jfr start name=latency settings=profile duration=60s filename=latency.jfr
perf top -p <pid>
strace -f -p <pid>
```

These three usually tell us whether the problem is inside the JVM, inside the kernel, or waiting on I/O.

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Short timeout | Fail fast | More false positives | User-facing APIs with fallback |
| Long timeout | Fewer premature failures | Tail latency hides longer | Rare batch jobs |
| Bigger thread pool | Better throughput | More context switching | Bursty but short work |
| Smaller thread pool | Less contention | Queue grows sooner | Stable, well-bounded work |
| Retry | Self-healing | Can amplify load | Idempotent calls only |
| Cache | Lower latency | Staleness risk | Read-heavy paths |

## 꼬리질문

> Q: Why does p99 matter more than average latency?
> Intent: checks whether the candidate understands tail behavior and user-visible pain.
> Core: average hides the worst requests.

> Q: How do you tell queueing from actual slow execution?
> Intent: checks phase decomposition and metrics literacy.
> Core: compare wait time, run queue, pool wait, and service time.

> Q: Why can retries worsen latency?
> Intent: checks amplification awareness.
> Core: retries add load exactly when the system is already stressed.

> Q: Why can heap look fine while latency is bad?
> Intent: checks JVM vs OS vs native memory thinking.
> Core: the bottleneck may be off-heap, lock contention, or kernel waiting.

## 한 줄 정리

Latency debugging is finding the hidden wait, then deciding whether to shrink it, isolate it, or absorb it with a safer fallback.
