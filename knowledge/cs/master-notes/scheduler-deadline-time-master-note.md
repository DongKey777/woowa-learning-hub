# Scheduler Deadline Time Master Note

> 한 줄 요약: scheduler and deadline bugs usually come from confusing wall clock time, monotonic time, and queueing delay.

**Difficulty: Advanced**

> retrieval-anchor-keywords: monotonic clock, wall clock, deadline, timeout, drift, NTP, scheduler, async boundary, cron, delay, retry, jitter, clock skew, graceful shutdown

> related docs:
> - [Monotonic Clock, Wall Clock, Timeout, Deadline](../contents/operating-system/monotonic-clock-wall-clock-timeout-deadline.md)
> - [Spring Scheduler / Async Boundaries](../contents/spring/spring-scheduler-async-boundaries.md)
> - [Signals, Process Supervision](../contents/operating-system/signals-process-supervision.md)
> - [Timeout Types: connect / read / write](../contents/network/timeout-types-connect-read-write.md)
> - [Timeout, Retry, Backoff Practical](../contents/network/timeout-retry-backoff-practical.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

Schedulers often fail because humans think in wall-clock time, while systems need monotonic time for deadlines.

The key distinction is:

- wall clock: calendar and human time
- monotonic clock: elapsed time that should not go backwards
- deadline: a point by which work must finish
- timeout: how long we are willing to wait

Mix these up and retries, cron jobs, and async work become flaky.

## 깊이 들어가기

### 1. Deadline is not the same as timeout

Timeout is a budget.
Deadline is a fixed finish point.

For a request that crosses multiple services, deadline propagation matters more than one local timeout.

Read with:

- [Monotonic Clock, Wall Clock, Timeout, Deadline](../contents/operating-system/monotonic-clock-wall-clock-timeout-deadline.md)

### 2. Cron is wall-clock driven

Cron-like jobs care about calendar time.
That means DST, timezone, and clock skew can change behavior.

### 3. Async boundaries create scheduling gaps

Once work crosses into another thread or queue, the local caller no longer controls execution timing.

Read with:

- [Spring Scheduler / Async Boundaries](../contents/spring/spring-scheduler-async-boundaries.md)

### 4. Shutdown needs deadline-aware draining

Processes should stop accepting new work, finish what is in flight, and exit before the platform kills them.

Read with:

- [Signals, Process Supervision](../contents/operating-system/signals-process-supervision.md)

## 실전 시나리오

### 시나리오 1: job runs twice after clock change

Likely cause:

- wall clock jump
- cron schedule boundary shifted

### 시나리오 2: request times out too early on slow downstream

Likely cause:

- local timeout not aligned with propagated deadline

### 시나리오 3: async task keeps running after request is gone

Likely cause:

- deadline not propagated
- background queue ignores caller cancellation

## 코드로 보기

### Deadline propagation sketch

```java
Instant deadline = Instant.now().plusSeconds(2);
if (Instant.now().isAfter(deadline)) {
    throw new TimeoutException();
}
```

### Monotonic elapsed time sketch

```java
long start = System.nanoTime();
doWork();
long elapsedMs = (System.nanoTime() - start) / 1_000_000;
```

### Scheduler guard

```java
if (shutdownRequested.get()) {
    return;
}
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Wall clock schedule | Human-friendly | Timezone / DST sensitivity | Cron jobs |
| Monotonic timeout | Stable elapsed-time measurement | Not calendar-aware | RPC deadlines |
| Fixed delay retry | Simple | Can synchronize badly | Low-stakes tasks |
| Jittered retry | Smears bursts | Harder to reason about | Shared downstreams |

## 꼬리질문

> Q: Why do deadlines matter more than local timeouts in distributed systems?
> Intent: checks end-to-end time budget reasoning.
> Core: each hop consumes part of the same user-visible budget.

> Q: Why is monotonic time preferred for elapsed duration?
> Intent: checks clock-skew awareness.
> Core: monotonic time should not jump when the wall clock changes.

> Q: Why can cron jobs be flaky around timezone changes?
> Intent: checks wall-clock scheduling awareness.
> Core: wall-clock rules move when the calendar changes.

## 한 줄 정리

Schedulers become reliable when deadlines follow monotonic time and cron-style work is kept separate from elapsed-time budgets.
