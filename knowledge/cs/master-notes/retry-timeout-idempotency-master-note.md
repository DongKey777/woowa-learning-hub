# Retry, Timeout, Idempotency Master Note

> 한 줄 요약: retries only work when the timeout budget, backoff, and idempotency model are designed together; otherwise they just amplify the failure.

**Difficulty: Advanced**

> retrieval-anchor-keywords: timeout budget, connect timeout, read timeout, write timeout, retry storm, exponential backoff, jitter, circuit breaker, idempotency key, dedupe, at-least-once, duplicate charge, retry-after, replay

> related docs:
> - [Timeout Types: connect / read / write](../contents/network/timeout-types-connect-read-write.md)
> - [Timeout, Retry, Backoff Practical](../contents/network/timeout-retry-backoff-practical.md)
> - [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](../contents/spring/spring-resilience4j-retry-circuit-breaker-bulkhead.md)
> - [HTTP Methods and REST Idempotency](../contents/network/http-methods-rest-idempotency.md)
> - [Idempotency Key and Deduplication](../contents/database/idempotency-key-and-deduplication.md)
> - [Idempotency, Retry, Consistency Boundaries](../contents/software-engineering/idempotency-retry-consistency-boundaries.md)
> - [Payment System Ledger / Idempotency / Reconciliation](../contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md)
> - [API Gateway / Auth / Rate Limit Chain](../contents/network/api-gateway-auth-rate-limit-chain.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Timeout, retry, and idempotency are a single design problem.

If you choose only one, the system usually fails in a different way:

- no timeout -> stuck resources
- timeout without retry -> poor resilience
- retry without idempotency -> duplicate side effects
- retry without backoff -> retry storm

The right budget is not "as long as possible".
It is "long enough for normal variance, short enough to fail before the whole queue is damaged."

## 깊이 들어가기

### 1. Timeout is a budget, not a number

Different timeout types mean different failure modes:

- connect timeout: cannot establish a connection
- read timeout: server is too slow to respond
- write timeout: request cannot be sent in time

These should not be conflated.
See:

- [Timeout Types: connect / read / write](../contents/network/timeout-types-connect-read-write.md)

### 2. Retries need backoff and jitter

Without backoff:

- every client retries at the same time
- the backend gets hammered
- latency gets worse
- more retries trigger

With jitter, the system avoids synchronized bursts.

Useful companion:

- [Timeout, Retry, Backoff Practical](../contents/network/timeout-retry-backoff-practical.md)

### 3. Idempotency is the duplicate-side-effect shield

If the operation can be retried, it needs a way to detect duplicates.

Common patterns:

- idempotency key stored with the request result
- dedupe table with unique constraint
- ledger entry with reconciliation
- message consumer deduplication

See:

- [Idempotency Key and Deduplication](../contents/database/idempotency-key-and-deduplication.md)
- [Payment System Ledger / Idempotency / Reconciliation](../contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md)

### 4. Retrying the wrong layer is dangerous

If the client, gateway, service, and DB all retry independently, the effective load can multiply.

That is why retry policy should be explicit about:

- which layer owns the retry
- which errors are retryable
- which operations are safe to replay
- how many attempts are allowed

## 실전 시나리오

### 시나리오 1: duplicate payment charge

Cause:

- request timed out after the charge succeeded
- client retried without idempotency

Fix:

- idempotency key
- ledger lookup
- reconciliation

### 시나리오 2: retry storm after partial outage

Cause:

- all callers retry at once
- no jitter
- no circuit breaker

### 시나리오 3: timeout is too short

Cause:

- normal latency variance is mistaken for failure
- valid requests are aborted

### 시나리오 4: timeout is too long

Cause:

- threads stay occupied
- queue grows
- recovery becomes slower

## 코드로 보기

### Idempotent request handling sketch

```java
@Transactional
public PaymentResult charge(ChargeCommand command) {
    return idempotencyRepository.findByKey(command.idempotencyKey())
        .map(IdempotencyRecord::result)
        .orElseGet(() -> {
            PaymentResult result = paymentGateway.charge(command);
            idempotencyRepository.save(new IdempotencyRecord(command.idempotencyKey(), result));
            return result;
        });
}
```

### Retry policy sketch

```java
RetryConfig config = RetryConfig.custom()
    .maxAttempts(3)
    .waitDuration(Duration.ofMillis(200))
    .enableExponentialBackoff(2.0)
    .retryExceptions(IOException.class)
    .build();
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Retry | Higher success rate | More load | Idempotent, transient failures |
| Fail fast | Protects resources | More user-visible failures | High-concurrency systems |
| Longer timeout | Fewer false failures | More resource occupancy | Slow but reliable operations |
| Idempotency key | Safe replay | Storage and lookup cost | Any side-effecting request |
| Circuit breaker | Stops cascading failure | Extra state and tuning | Downstream instability |

## 꼬리질문

> Q: Why is retry without idempotency dangerous?
> Intent: checks side-effect awareness.
> Core: the same operation can execute twice and create duplicates.

> Q: Why is timeout a budget problem?
> Intent: checks resource-occupancy thinking.
> Core: the timeout controls how long threads and connections stay occupied.

> Q: Why do we need jitter?
> Intent: checks load-smoothing awareness.
> Core: jitter spreads retries so they do not pile up at the same instant.

> Q: Why is at-least-once delivery not enough by itself?
> Intent: checks distributed systems reliability semantics.
> Core: at-least-once still requires consumer-side deduplication.

## 한 줄 정리

Retries are only safe when the timeout budget, backoff shape, and idempotency storage agree on what "the same request" means.
