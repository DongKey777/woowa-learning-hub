# Quota Rate Limit Fairness Master Note

> 한 줄 요약: quota and rate limit fairness are about preventing one actor from consuming a shared budget faster than the system or other tenants can tolerate.

**Difficulty: Advanced**

> retrieval-anchor-keywords: quota, fairness, burst, token bucket, sliding window, admission control, tenant limit, API key limit, backpressure, noisy neighbor, throttling, starvation, priority, share

> related docs:
> - [Rate Limiter 설계](../contents/system-design/rate-limiter-design.md)
> - [멀티 테넌트 SaaS 격리 설계](../contents/system-design/multi-tenant-saas-isolation-design.md)
> - [CFS Scheduler, Nice, CPU Fairness](../contents/operating-system/cfs-scheduler-nice-cpu-fairness.md)
> - [run queue, load average, CPU saturation](../contents/operating-system/run-queue-load-average-cpu-saturation.md)
> - [API Gateway / Auth / Rate Limit Chain](../contents/network/api-gateway-auth-rate-limit-chain.md)
> - [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](../contents/spring/spring-resilience4j-retry-circuit-breaker-bulkhead.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Quota is the budget.
Fairness is the rule for distributing that budget.

They are not the same thing.

- quota says how much is allowed
- fairness says who gets served first and who gets slowed down

Without fairness, quotas can still let one tenant dominate the shared path.

## 깊이 들어가기

### 1. Burst and sustained rate need separate treatment

A user may be allowed to burst briefly but still be capped over time.

Read with:

- [Rate Limiter 설계](../contents/system-design/rate-limiter-design.md)

### 2. Fairness is also a scheduling problem

At OS level, CFS tries to share CPU fairly.
At app level, limiter and queue policy must do the same thing for requests.

Read with:

- [CFS Scheduler, Nice, CPU Fairness](../contents/operating-system/cfs-scheduler-nice-cpu-fairness.md)
- [run queue, load average, CPU saturation](../contents/operating-system/run-queue-load-average-cpu-saturation.md)

### 3. Edge and app limits should agree

Gateway limits prevent obvious abuse.
App limits enforce business fairness like tenant quotas or user entitlements.

Read with:

- [API Gateway / Auth / Rate Limit Chain](../contents/network/api-gateway-auth-rate-limit-chain.md)

### 4. Retry and bulkhead can preserve fairness

Without bulkhead, one hot path can consume everything.
Without retry discipline, failures can become unfair load amplification.

Read with:

- [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](../contents/spring/spring-resilience4j-retry-circuit-breaker-bulkhead.md)

## 실전 시나리오

### 시나리오 1: one tenant uses up all shared capacity

Likely cause:

- shared quota without per-tenant fairness
- no concurrency isolation

### 시나리오 2: small customers get starved by a large batch user

Likely cause:

- queue scheduling missing priorities
- burst path not separated from steady path

### 시나리오 3: throttling is too strict and hurts good traffic

Likely cause:

- quota model too blunt
- no adaptive burst allowance

## 코드로 보기

### Token bucket sketch

```text
capacity = 100
refill = 10/sec
allow if tokens > 0
```

### Tenant-aware limiter key

```text
tenant:{tenantId}:endpoint:{name}
```

### Fair scheduling sketch

```text
serve tenants round-robin with per-tenant cap
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Hard quota | Predictable spend | Can reject useful bursts | Billing or strict limits |
| Soft quota | Better UX | Less strict control | Consumer-facing APIs |
| Weighted fairness | Better tenant balance | More tuning | Multi-tenant platforms |
| Global limiter only | Simple | Noisy neighbor risk | Small single-tenant services |

## 꼬리질문

> Q: Why is fairness different from quota?
> Intent: checks scheduling and policy separation.
> Core: quota is the amount; fairness is the allocation rule.

> Q: Why can retries hurt fairness?
> Intent: checks load amplification awareness.
> Core: retries can let one failing client consume even more shared budget.

> Q: Why should rate limiting align with CPU fairness ideas?
> Intent: checks cross-layer reasoning.
> Core: both are about preventing one actor from monopolizing shared capacity.

## 한 줄 정리

Quota and fairness together decide not just how much work is allowed, but which traffic gets protected when the system is under pressure.
