# Multi-Tenant Noisy Neighbor Master Note

> 한 줄 요약: noisy neighbor problems happen when one tenant's burst, queue, cache, or query behavior spills into another tenant's budget.

**Difficulty: Advanced**

> retrieval-anchor-keywords: noisy neighbor, multi-tenant, tenant isolation, shared resource, fairness, quota, cache hot key, queue backlog, shared schema, rate limit, CPU saturation, cost isolation

> related docs:
> - [멀티 테넌트 SaaS 격리 설계](../contents/system-design/multi-tenant-saas-isolation-design.md)
> - [Rate Limiter 설계](../contents/system-design/rate-limiter-design.md)
> - [분산 캐시 설계](../contents/system-design/distributed-cache-design.md)
> - [CFS Scheduler, Nice, CPU Fairness](../contents/operating-system/cfs-scheduler-nice-cpu-fairness.md)
> - [run queue, load average, CPU saturation](../contents/operating-system/run-queue-load-average-cpu-saturation.md)
> - [Queue Backpressure Master Note](./queue-backpressure-master-note.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Noisy neighbor is not only a CPU problem.

It can be:

- hot tenant cache usage
- queue backlog
- DB connection pressure
- expensive query shape
- rate limit abuse
- storage or bandwidth burst

The fix is to isolate, cap, or schedule fairly.

## 깊이 들어가기

### 1. Fairness is a system property

The OS tries to share CPU fairly.
The platform should do the same for tenant budgets.

Read with:

- [CFS Scheduler, Nice, CPU Fairness](../contents/operating-system/cfs-scheduler-nice-cpu-fairness.md)

### 2. Quotas are not enough without enforcement points

If the tenant quota is only in billing but not in queue, cache, or gateway, the neighbor still hurts others.

Read with:

- [Rate Limiter 설계](../contents/system-design/rate-limiter-design.md)

### 3. Shared schema amplifies blast radius

In a shared schema, a bad query or runaway batch can affect many tenants.

Read with:

- [멀티 테넌트 SaaS 격리 설계](../contents/system-design/multi-tenant-saas-isolation-design.md)

### 4. Cache hot keys are tenant neighbors too

A single tenant's hot key can force DB fallback for everyone else if cache and queue are shared.

Read with:

- [분산 캐시 설계](../contents/system-design/distributed-cache-design.md)

## 실전 시나리오

### 시나리오 1: one tenant's batch slows everyone down

Likely cause:

- shared worker pool
- no tenant-aware concurrency cap

### 시나리오 2: one tenant's cache key dominates memory

Likely cause:

- hot key
- no eviction or per-tenant cache budget

### 시나리오 3: one tenant's query pattern saturates DB

Likely cause:

- missing tenant-specific rate limit
- no resource class separation

## 코드로 보기

### Tenant quota sketch

```text
tenant A: 100 rps
tenant B: 20 rps
tenant C: 5 concurrent jobs
```

### Fair queue sketch

```text
round-robin by tenant, then by priority
```

### Cache key isolation

```text
tenant:{tenantId}:resource:{id}
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Strict quotas | Strong protection | More rejections | Shared platforms |
| Soft quotas | Better UX | Less isolation | Early-stage SaaS |
| Tenant-specific pools | Good fairness | More resources | Larger tenants |
| Shared pools | Efficient | Noisy neighbor risk | Small deployments |

## 꼬리질문

> Q: Why is noisy neighbor not only a CPU issue?
> Intent: checks multi-resource thinking.
> Core: cache, queue, DB, and network can all be monopolized.

> Q: Why do quotas need enforcement points?
> Intent: checks practical isolation.
> Core: a quota that is only measured but not enforced does not protect neighbors.

> Q: Why do shared schemas worsen the blast radius?
> Intent: checks data isolation awareness.
> Core: one bad query can touch many tenants' rows and indexes.

## 한 줄 정리

Noisy neighbor is a fairness failure across shared resources, and it only disappears when isolation is enforced at every hot path.
