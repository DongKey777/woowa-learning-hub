# Authz and Permission Master Note

> 한 줄 요약: authorization is the policy layer that turns identity into allowed actions, and permission models only work when scope, ownership, and tenant boundaries are all explicit.

**Difficulty: Advanced**

> retrieval-anchor-keywords: authorization, permission model, RBAC, ABAC, scope, ownership, principal, policy, privilege escalation, access control, tenant scope, admin scope, deny by default, stale authz cache, stale deny, grant but still denied, 403 after revoke, revoked admin still has access, permission cache stale, revocation tail

> related docs:
> - [인증과 인가의 차이](../contents/security/authentication-vs-authorization.md)
> - [Spring Security 아키텍처](../contents/spring/spring-security-architecture.md)
> - [Permission Model Drift / AuthZ Graph Design](../contents/security/permission-model-drift-authz-graph-design.md)
> - [Authorization Caching Staleness](../contents/security/authorization-caching-staleness.md)
> - [AuthZ Cache Inconsistency / Runtime Debugging](../contents/security/authz-cache-inconsistency-runtime-debugging.md)
> - [Auth Failure Response Contracts: `401` / `403` / `404`](../contents/security/auth-failure-response-401-403-404.md)
> - [Revocation Propagation Lag / Debugging](../contents/security/revocation-propagation-lag-debugging.md)
> - [멀티 테넌트 SaaS 격리 설계](../contents/system-design/multi-tenant-saas-isolation-design.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

Authorization decides what an authenticated identity may do.

The common failure is to stop at "logged in".
Real systems must also answer:

- which tenant applies
- which resource is owned
- which role or scope grants access
- whether the permission is time-bound or cached

Authorization is a policy graph, not a single boolean.

## 깊이 들어가기

### 1. RBAC is not enough by itself

Role-based access control is easy to reason about, but it often becomes too coarse.

Read with:

- [인증과 인가의 차이](../contents/security/authentication-vs-authorization.md)

### 2. Ownership and scope matter

Even if the user has a role, they may only access resources they own or tenant-scoped resources they belong to.

### 3. Permission graphs drift over time

Once permissions become a graph of roles, groups, exceptions, and admin overrides, drift is inevitable.

Read with:

- [Permission Model Drift / AuthZ Graph Design](../contents/security/permission-model-drift-authz-graph-design.md)

### 4. Cached authorization can go stale

If permission checks are cached, revocation and role changes must propagate quickly enough.

If the symptom shows up as `403 after revoke`, `grant but still denied`, or `tenant-specific 403`,
start by separating stale deny from concealment or response-contract drift.
If the symptom is `allowed after revoke`, the same authz graph may still be correct while propagation is late.

Read with:

- [Authorization Caching Staleness](../contents/security/authorization-caching-staleness.md)
- [AuthZ Cache Inconsistency / Runtime Debugging](../contents/security/authz-cache-inconsistency-runtime-debugging.md)
- [Auth Failure Response Contracts: `401` / `403` / `404`](../contents/security/auth-failure-response-401-403-404.md)
- [Revocation Propagation Lag / Debugging](../contents/security/revocation-propagation-lag-debugging.md)

### 5. Tenant scope is a permission boundary

In multi-tenant systems, authorization without tenant scope is a leak waiting to happen.

Read with:

- [멀티 테넌트 SaaS 격리 설계](../contents/system-design/multi-tenant-saas-isolation-design.md)

## 실전 시나리오

### 시나리오 1: user can see another user's order

Likely cause:

- role check only
- ownership check missing

### 시나리오 2: revoked admin still has access

Likely cause:

- stale authorization cache
- token TTL too long

### 시나리오 3: `403 after revoke` or `grant but still denied`

Likely cause:

- negative cache or tenant-scoped cache key is stale
- concealment `404` and real `403` drift are mixed in the response layer

### 시나리오 4: tenant A can read tenant B data

Likely cause:

- tenant scope not enforced at service boundary

## 코드로 보기

### Policy sketch

```java
if (!principal.roles().contains("ADMIN") && !principal.userId().equals(resource.ownerId())) {
    throw new AccessDeniedException("forbidden");
}
```

### Tenant-aware guard

```java
if (!principal.tenantId().equals(resource.tenantId())) {
    throw new AccessDeniedException("cross-tenant");
}
```

### Cached permission check

```text
allow only if cached policy version == current policy version
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| RBAC | Easy to understand | Coarse | Small systems |
| RBAC + ownership | Safer | More checks | Most apps |
| ABAC / policy graph | Flexible | Complex | Large platforms |
| Cached authz | Fast | Staleness risk | High QPS systems |

## 꼬리질문

> Q: Why is authorization more than role checking?
> Intent: checks policy depth.
> Core: ownership, tenant, time, and scope all matter.

> Q: Why do cached permissions fail?
> Intent: checks revocation freshness.
> Core: permission changes can outpace cache invalidation.

> Q: Why is tenant scope part of authorization?
> Intent: checks boundary safety.
> Core: a valid identity can still be out of scope for a tenant.

## 한 줄 정리

Authorization and permission management are the policy graph that turns identity into safe access, and the graph must encode scope, ownership, and tenant boundaries explicitly.
