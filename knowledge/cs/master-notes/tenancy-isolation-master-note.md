# Tenancy Isolation Master Note

> 한 줄 요약: tenancy isolation is the discipline of making one tenant's scale, mistakes, and permissions unable to escape its boundary.

**Difficulty: Advanced**

> retrieval-anchor-keywords: multi-tenant, tenant isolation, noisy neighbor, shared schema, separate schema, separate database, RBAC, data residency, tenant context, cache key prefix, queue partition, authorization boundary

> related docs:
> - [멀티 테넌트 SaaS 격리 설계](../contents/system-design/multi-tenant-saas-isolation-design.md)
> - [Rate Limiter 설계](../contents/system-design/rate-limiter-design.md)
> - [Distributed Cache Design](../contents/system-design/distributed-cache-design.md)
> - [Authentication vs Authorization](../contents/security/authentication-vs-authorization.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)
> - [Spring Security Architecture](../contents/spring/spring-security-architecture.md)
> - [Partition Pruning and Hot/Cold Data](../contents/database/partition-pruning-hot-cold-data.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

Tenant isolation is not one control.
It is a stack of controls across identity, data, compute, cache, and queue layers.

The main goal is to stop:

- data leaks
- noisy neighbor effects
- runaway cost
- policy bypass

## 깊이 들어가기

### 1. Identity and authorization are the front line

Authentication answers who the caller is.
Authorization answers what that caller can do inside a tenant.

Read with:

- [Authentication vs Authorization](../contents/security/authentication-vs-authorization.md)
- [Spring Security Architecture](../contents/spring/spring-security-architecture.md)

### 2. Data isolation can be shared, split, or fully separated

Tenant boundaries may use:

- shared schema
- separate schema
- separate database

The tighter the boundary, the easier it is to contain risk, but the higher the operational cost.

Read with:

- [멀티 테넌트 SaaS 격리 설계](../contents/system-design/multi-tenant-saas-isolation-design.md)

### 3. Cache and queue isolation are easy to forget

If the tenant id is missing from a cache key or queue partition, data and load can bleed across customers.

Read with:

- [Distributed Cache Design](../contents/system-design/distributed-cache-design.md)
- [Rate Limiter 설계](../contents/system-design/rate-limiter-design.md)

### 4. Network identity is not tenant identity

mTLS and SPIFFE can identify a service workload, but tenant authorization still needs application-level enforcement.

Read with:

- [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)

## 실전 시나리오

### 시나리오 1: one tenant dominates CPU and queue time

Likely cause:

- no tenant-aware rate limiting
- shared workers with no bulkhead

### 시나리오 2: one tenant can read another tenant's data

Likely cause:

- tenant filter missing
- authorization only checks role, not tenant membership

### 시나리오 3: cache hits leak across tenants

Likely cause:

- tenant prefix missing from cache key

## 코드로 보기

### Tenant context sketch

```java
public record TenantContext(String tenantId, String userId, Set<String> roles) {}
```

### Tenant-scoped cache key

```text
tenant:{tenantId}:user:{userId}:profile
```

### Authorization guard

```java
if (!tenantContext.tenantId().equals(resource.tenantId())) {
    throw new AccessDeniedException("cross-tenant access");
}
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Shared schema | Cheap and simple | Stronger leakage risk | Small tenants, early stage |
| Separate schema | Better isolation | More ops complexity | Medium tenants |
| Separate database | Strongest isolation | Highest cost | Enterprise or regulated tenants |
| Shared queue | Simple pipeline | Noisy neighbor risk | Low-risk async work |
| Tenant-partitioned queue | Fairness | More routing complexity | Production multi-tenant systems |

## 꼬리질문

> Q: Why is authorization more important than authentication in multi-tenant systems?
> Intent: checks boundary enforcement.
> Core: knowing who the user is is not enough; you must know which tenant and which scope applies.

> Q: Why do caches need tenant prefixes?
> Intent: checks cross-tenant leakage awareness.
> Core: without tenant scoping, one customer's data can overwrite another's.

> Q: Why does mTLS not solve tenant isolation by itself?
> Intent: checks identity-layer vs business-layer separation.
> Core: mTLS can tell you the service identity, not the tenant authorization.

## 한 줄 정리

Tenancy isolation is end-to-end boundary control, from identity and authorization down to cache keys, queues, and data placement.
