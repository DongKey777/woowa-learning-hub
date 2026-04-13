# Queue Worker Reliability Master Note

> 한 줄 요약: queue worker reliability is about surviving retries, crashes, poison messages, and deployment churn without losing work or duplicating side effects.

## 이 노트의 역할

이 노트는 `queue reliability` 군집의 **대표 노트**다.

- 먼저 이 노트로 worker lifecycle, idempotency, lease, DLQ, graceful shutdown을 본다.
- producer slowdown, bounded queue, overload signaling을 더 깊게 보려면 [Queue Backpressure Master Note](./queue-backpressure-master-note.md)를 이어서 본다.

**Difficulty: Advanced**

> retrieval-anchor-keywords: worker crash, poison message, ack, retry loop, dead letter queue, visibility timeout, idempotent handler, graceful shutdown, signal handling, queue backlog, concurrency limit, replay, lease, heartbeat

> related docs:
> - [Signals, Process Supervision](../contents/operating-system/signals-process-supervision.md)
> - [Failure Recovery Lifecycle](../contents/operating-system/oom-killer-cgroup-memory-pressure.md)
> - [Spring Batch Chunk Retry Skip](../contents/spring/spring-batch-chunk-retry-skip.md)
> - [Domain Events, Outbox, Inbox](../contents/software-engineering/outbox-inbox-domain-events.md)
> - [Workflow Orchestration / Saga Design](../contents/system-design/workflow-orchestration-saga-design.md)
> - [Timeout, Retry, Backoff Practical](../contents/network/timeout-retry-backoff-practical.md)
> - [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](../contents/spring/spring-resilience4j-retry-circuit-breaker-bulkhead.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

A queue worker is not reliable because it is "running".

It is reliable only when it can:

- recover after crash
- retry safely
- stop gracefully
- handle duplicates
- isolate bad jobs
- keep backlog visible

Reliability is a combination of queue semantics and process semantics.

## 깊이 들어가기

### 1. The worker must own its lifecycle

Workers die, restart, get rolled, and get preempted.

So the process must understand:

- startup warm-up
- heartbeats
- graceful shutdown
- in-flight work drain
- visibility timeout or lease renewal

Read with:

- [Signals, Process Supervision](../contents/operating-system/signals-process-supervision.md)

### 2. Idempotent handlers are non-negotiable

Workers often see at-least-once delivery.

That means:

- ack can fail
- retry can happen after partial success
- reprocessing must be safe

Read with:

- [Domain Events, Outbox, Inbox](../contents/software-engineering/outbox-inbox-domain-events.md)
- [Idempotency Key and Deduplication](../contents/database/idempotency-key-and-deduplication.md)

### 3. Poison messages need containment

One malformed job can block progress if it keeps failing forever.

Typical defenses:

- retry limit
- backoff
- DLQ
- schema validation
- per-message quarantine

### 4. Queue depth is a reliability signal

Backlog is often the first symptom of trouble.

If queue depth rises while worker throughput falls, likely causes are:

- downstream slowdowns
- CPU saturation
- resource leaks
- bad batch sizing
- deployment instability

## 실전 시나리오

### 시나리오 1: worker restarts during processing

Without lease or idempotency, the same job may be processed twice.

### 시나리오 2: one bad message keeps failing

Without DLQ, the worker can spin forever on the same payload.

### 시나리오 3: deployment causes job loss

If the worker stops without draining in-flight tasks, work can be abandoned.

### 시나리오 4: backlog grows even though workers are alive

Likely cause:

- downstream API slow
- DB lock wait
- pool exhaustion
- batch size too small or too large

## 코드로 보기

### Graceful shutdown sketch

```java
@PreDestroy
public void shutdown() {
    draining = true;
    executor.shutdown();
}
```

### Idempotent processing sketch

```java
public void handle(JobMessage message) {
    if (processedJobRepository.existsByMessageId(message.id())) {
        return;
    }
    jobService.apply(message);
    processedJobRepository.save(new ProcessedJob(message.id()));
}
```

### Retry + DLQ policy sketch

```java
if (attempt >= 5) {
    deadLetterQueue.publish(message);
    return;
}
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Fast retry | Quick recovery | Retry storm risk | Transient failures only |
| DLQ after limit | Protects throughput | Manual recovery work | Poison messages |
| Large batches | Better throughput | Bigger rollback scope | Stable, uniform jobs |
| Small batches | Easier recovery | More overhead | Risky or mixed workloads |
| Leases / heartbeats | Safer handoff | More protocol complexity | Long-running jobs |

## 꼬리질문

> Q: Why must queue workers be idempotent?
> Intent: checks duplicate delivery realism.
> Core: retries and crash recovery can replay the same job.

> Q: Why is graceful shutdown important?
> Intent: checks lifecycle management.
> Core: in-flight work can be lost if the process exits too quickly.

> Q: Why is a DLQ not the same as a fix?
> Intent: checks failure containment vs resolution.
> Core: a DLQ isolates bad messages but does not solve the root cause.

> Q: Why does queue backlog matter operationally?
> Intent: checks monitoring and capacity awareness.
> Core: backlog tells you when work is arriving faster than it is being completed.

## 한 줄 정리

Queue worker reliability is about making crash recovery, retries, and shutdown behavior safe enough that the queue can keep moving work without duplicating or dropping it.
