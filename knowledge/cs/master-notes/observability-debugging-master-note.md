# Observability Debugging Master Note

> 한 줄 요약: observability debugging is the craft of turning logs, metrics, traces, and profiles into one causal story.

## 이 노트의 역할

이 노트는 `observability` 군집의 **대표 노트**다.

- 먼저 이 노트로 logs / metrics / traces / profiles를 어떻게 엮어 디버깅할지 본다.
- incident timeline, containment, rollback, runbook 쪽으로 넘어가면 [Observability to Incident Master Note](./observability-to-incident-master-note.md)를 이어서 본다.

**Difficulty: Advanced**

> retrieval-anchor-keywords: traceId, spanId, structured log, histogram, p99, RED metrics, USE metrics, JFR, eBPF, perf, strace, correlation, cardinality, saturation, cache miss, error budget

> related docs:
> - [cache, message, observability](../contents/software-engineering/cache-message-observability.md)
> - [eBPF, perf, strace production tracing](../contents/operating-system/ebpf-perf-strace-production-tracing.md)
> - [JFR / JMC performance playbook](../contents/language/java/jfr-jmc-performance-playbook.md)
> - [Spring Observability / Micrometer / Tracing](../contents/spring/spring-observability-micrometer-tracing.md)
> - [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md)
> - [Slow Query Analysis Playbook](../contents/database/slow-query-analysis-playbook.md)
> - [Query Tuning Checklist](../contents/database/query-tuning-checklist.md)
> - [Topic Map](../rag/topic-map.md)
> - [Retrieval Anchor Keywords](../rag/retrieval-anchor-keywords.md)

## 핵심 개념

Observability is not the data itself.

It is the ability to answer:

- what happened
- where
- when
- how often
- and why it happened

Good debugging uses multiple evidence types because each one answers a different part of the causal chain.

## 깊이 들어가기

### 1. Logs, metrics, traces, and profiles do different jobs

- logs explain an event
- metrics show trend and severity
- traces show request path
- profiles show time spent in execution

If one is missing, diagnosis becomes guesswork.

### 2. Correlation is not causation

Two metrics moving together do not prove a root cause.

To debug correctly, you usually need:

- a request timeline
- a system timeline
- a recent deploy or config change
- one or two phase-specific measurements

### 3. Cardinality is a hidden observability cost

High-cardinality labels can make metrics expensive or unusable.

So the instrumentation must keep identity rich enough for debugging but bounded enough for storage.

### 4. Production debugging is multi-layer

A slow request can be:

- app queueing
- GC pause
- DB lock wait
- network retry
- kernel scheduling

That is why cross-domain tracing matters:

- [eBPF, perf, strace production tracing](../contents/operating-system/ebpf-perf-strace-production-tracing.md)
- [Spring Observability / Micrometer / Tracing](../contents/spring/spring-observability-micrometer-tracing.md)

## 실전 시나리오

### 시나리오 1: logs show errors but metrics are flat

Likely cause:

- one failure path is hidden behind retries
- only a subset of requests is failing

### 시나리오 2: latency is high but traces look normal

Likely cause:

- queueing before trace start
- DB waits not instrumented
- kernel or pool wait outside the span

### 시나리오 3: deploy made p99 worse

Likely cause:

- JIT warmup reset
- cache cold start
- new allocation pattern
- different query plan

### 시나리오 4: debugging data exists but cannot be connected

Likely cause:

- missing traceId
- missing correlationId
- inconsistent log schema

## 코드로 보기

### Structured log sketch

```java
log.info("payment_failed orderId={} userId={} traceId={} reason={}",
    orderId, userId, traceId, reason);
```

### Micrometer timer sketch

```java
Timer.Sample sample = Timer.start(registry);
try {
    service.handle(request);
} finally {
    sample.stop(Timer.builder("request.latency").register(registry));
}
```

### Trace-friendly envelope

```java
public record RequestContext(String traceId, String spanId, String requestId) {}
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| More logs | Better context | Noise and storage cost | Rare or critical paths |
| Better metrics | Easier alerting | Less detail | Fleet-wide health |
| Deeper tracing | Better causality | Instrumentation overhead | Distributed systems |
| Profiling on demand | Deep runtime insight | Requires skill and setup | Performance incidents |

## 꼬리질문

> Q: Why are metrics not enough for debugging?
> Intent: checks causality awareness.
> Core: metrics show trends, but not the request path or local cause.

> Q: Why is tracing useful in distributed systems?
> Intent: checks cross-service causality understanding.
> Core: tracing connects one request across many hops.

> Q: Why can observability fail even when data exists?
> Intent: checks correlation and labeling discipline.
> Core: without shared IDs or schemas, evidence cannot be stitched together.

> Q: Why is profiling part of observability?
> Intent: checks full-stack debugging awareness.
> Core: profiles show where execution time actually went.

## 한 줄 정리

Observability debugging is about stitching together evidence from multiple layers until the system’s behavior becomes one coherent causal chain.
