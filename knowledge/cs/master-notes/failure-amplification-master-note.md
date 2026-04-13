# Failure Amplification Master Note

> 한 줄 요약: failure amplification is when a small fault turns into a large outage because retries, queues, caches, and timeouts all push in the wrong direction.

**Difficulty: Advanced**

> retrieval-anchor-keywords: failure amplification, retry storm, thundering herd, stampede, reconnect storm, queue growth, circuit breaker, backpressure, timeout, cascading failure, saturation, tail latency

> related docs:
> - [Retry, Timeout, Idempotency Master Note](./retry-timeout-idempotency-master-note.md)
> - [Latency Debugging Master Note](./latency-debugging-master-note.md)
> - [Queue Backpressure Master Note](./queue-backpressure-master-note.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](../contents/network/connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Distributed Cache Design](../contents/system-design/distributed-cache-design.md)
> - [Load Balancer 헬스체크 실패 패턴](../contents/network/load-balancer-healthcheck-failure-patterns.md)
> - [Socket Buffer Autotuning, Backpressure](../contents/operating-system/socket-buffer-autotuning-backpressure.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Failure amplification is not a single bug.
It is a system dynamic.

A small slowdown or failure can grow because:

- retries add load
- caches expire together
- queues keep accepting work
- timeouts are too long
- health checks are too shallow
- reconnects happen in sync

## 깊이 들어가기

### 1. Retry is the most common amplifier

Retries help only when the system has spare capacity and the failure is transient.

Read with:

- [Retry, Timeout, Idempotency Master Note](./retry-timeout-idempotency-master-note.md)

### 2. Stampede and thundering herd are amplification patterns

Many clients converge on one expired key or one restarted service.

Read with:

- [Distributed Cache Design](../contents/system-design/distributed-cache-design.md)
- [Load Balancer 헬스체크 실패 패턴](../contents/network/load-balancer-healthcheck-failure-patterns.md)

### 3. Backpressure and circuit breakers are anti-amplifiers

If the system cannot shed load or stop calling sick dependencies, small faults spread.

Read with:

- [Connection Keep-Alive, Load Balancing, Circuit Breaker](../contents/network/connection-keepalive-loadbalancing-circuit-breaker.md)
- [Queue Backpressure Master Note](./queue-backpressure-master-note.md)

### 4. Tail latency can trigger amplification

Long tail requests occupy workers longer, which increases queueing and makes the next wave worse.

Read with:

- [Latency Debugging Master Note](./latency-debugging-master-note.md)

## 실전 시나리오

### 시나리오 1: a slow DB causes system-wide slowdown

Likely cause:

- longer transactions
- connection pool saturation
- retries on top of slow queries

### 시나리오 2: cache miss turns into DB storm

Likely cause:

- synchronized TTL
- no request coalescing

### 시나리오 3: one failed backend causes a larger outage

Likely cause:

- no circuit breaker
- repeated retries
- health check too slow to recover routing

## 코드로 보기

### Amplification chain sketch

```text
slowdown -> timeout -> retry -> more load -> longer queue -> more timeout
```

### Anti-amplification guard

```java
if (circuitBreaker.isOpen()) {
    return fallback();
}
```

### Cache stampede guard

```java
cache.get(key, singleFlightLoader);
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Retry | Hides transient faults | Can amplify load | Idempotent operations |
| Circuit breaker | Stops cascades | Can reject too early | Sick downstreams |
| Backpressure | Protects core system | Some work is delayed/rejected | Saturated pipelines |
| Longer timeout | Fewer false failures | More resource occupancy | Low-failure background jobs |

## 꼬리질문

> Q: Why can a small slowdown become a large outage?
> Intent: checks system-dynamics awareness.
> Core: retries, queues, and timeouts can multiply the original fault.

> Q: What pattern most often amplifies failures?
> Intent: checks practical incident understanding.
> Core: retry storms and stampedes are common amplifiers.

> Q: What stops amplification?
> Intent: checks mitigation design.
> Core: backpressure, circuit breakers, and bounded queues.

## 한 줄 정리

Failure amplification is the cascade where small faults gain power from retries, cache misses, queue growth, and slow failure detection, so the fix is to break the cascade early.
