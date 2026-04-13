# Async Context Propagation Master Note

> 한 줄 요약: async context propagation is the work of carrying security, trace, and request metadata across thread and task boundaries without accidental loss or widening.

**Difficulty: Advanced**

> retrieval-anchor-keywords: async context propagation, SecurityContext, MDC, trace context, thread pool, @Async, @Scheduled, coroutine context, thread local, executor, request context, principal

> related docs:
> - [Spring Scheduler / Async Boundaries](../contents/spring/spring-scheduler-async-boundaries.md)
> - [Spring Observability / Micrometer / Tracing](../contents/spring/spring-observability-micrometer-tracing.md)
> - [Identity Propagation Master Note](./identity-propagation-master-note.md)
> - [Spring Security 아키텍처](../contents/spring/spring-security-architecture.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Async boundaries break thread-local assumptions.
When work moves to another executor, you must decide what context follows:

- security principal
- trace id
- request id
- tenant id
- logging correlation data

If you do not propagate explicitly, the async task becomes operationally anonymous.

## 깊이 들어가기

### 1. Thread-local context is not portable

`SecurityContext`, `MDC`, and similar storage are often thread-bound.

Read with:

- [Spring Scheduler / Async Boundaries](../contents/spring/spring-scheduler-async-boundaries.md)
- [Spring Security 아키텍처](../contents/spring/spring-security-architecture.md)

### 2. Propagation must be selective

Not every piece of request data should cross every async hop.
Propagate what is needed, not everything.

### 3. Observability depends on it

Without trace/context propagation, logs and spans cannot be joined.

Read with:

- [Spring Observability / Micrometer / Tracing](../contents/spring/spring-observability-micrometer-tracing.md)

### 4. Async jobs need explicit ownership

If context is missing, you must still know which tenant or user caused the work.

Read with:

- [Identity Propagation Master Note](./identity-propagation-master-note.md)

## 실전 시나리오

### 시나리오 1: async task logs show empty user

Likely cause:

- MDC not copied
- SecurityContext not propagated

### 시나리오 2: scheduled job updates the wrong tenant

Likely cause:

- context not carried into scheduled executor

### 시나리오 3: trace breaks at async boundary

Likely cause:

- observation context not wrapped around executor task

## 코드로 보기

### Context wrapper sketch

```java
Runnable wrapped = () -> {
    MDC.put("traceId", traceId);
    try {
        delegate.run();
    } finally {
        MDC.clear();
    }
};
```

### Async service sketch

```java
@Async
public CompletableFuture<Void> sendMail() {
    // propagate only the needed context
    return CompletableFuture.completedFuture(null);
}
```

### Propagation rule

```text
capture context -> submit to executor -> restore -> clear
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| No propagation | Simple | Anonymous work | Rarely acceptable |
| Full propagation | Easy debugging | Leaks too much context | Small internal systems |
| Selective propagation | Safer | Needs plumbing | Production async systems |
| Dedicated context object | Clear ownership | More code | Large async pipelines |

## 꼬리질문

> Q: Why does async break SecurityContext?
> Intent: checks thread-bound state understanding.
> Core: the work runs on a different thread and thread-local state does not follow automatically.

> Q: Why should propagation be selective?
> Intent: checks security and hygiene.
> Core: not all request data should cross every boundary.

> Q: Why does observability depend on async propagation?
> Intent: checks trace continuity.
> Core: spans and logs need the same context to correlate events.

## 한 줄 정리

Async context propagation is the controlled transfer of security and observability metadata across executor boundaries so background work remains attributable and safe.
