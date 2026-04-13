# Identity Propagation Master Note

> 한 줄 요약: identity propagation is the work of carrying who the caller is across proxies, services, jobs, and logs without losing or widening trust.

**Difficulty: Advanced**

> retrieval-anchor-keywords: identity propagation, principal, trace context, SecurityContext, JWT, mTLS, SPIFFE, forwarded headers, tenant context, impersonation, auth propagation, correlation id

> related docs:
> - [Authentication vs Authorization](../contents/security/authentication-vs-authorization.md)
> - [JWT 깊이 파기](../contents/security/jwt-deep-dive.md)
> - [OAuth2 Authorization Code Grant](../contents/security/oauth2-authorization-code-grant.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)
> - [Forwarded / X-Forwarded-For / X-Real-IP Trust Boundary](../contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
> - [Spring Security 아키텍처](../contents/spring/spring-security-architecture.md)
> - [멀티 테넌트 SaaS 격리 설계](../contents/system-design/multi-tenant-saas-isolation-design.md)

## 핵심 개념

Identity propagation is not just "pass the user id along".

You must preserve:

- authenticity
- scope
- audience
- tenant context
- auditability

If any of these are widened accidentally, downstream policy becomes unsafe.

## 깊이 들어가기

### 1. Human identity and workload identity are different

User identity is often browser or session based.
Workload identity is often mTLS or signed token based.

Read with:

- [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)

### 2. Propagation across proxies must use trusted boundaries

Headers like `X-Forwarded-For` or `Forwarded` must only be interpreted after trusted normalization.

Read with:

- [Forwarded / X-Forwarded-For / X-Real-IP Trust Boundary](../contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)

### 3. Spring Security context is thread-bound

When execution hops threads, identity does not automatically follow.
That is why async, scheduler, and batch jobs need explicit propagation strategy.

Read with:

- [Spring Security 아키텍처](../contents/spring/spring-security-architecture.md)
- [Spring Scheduler / Async Boundaries](../contents/spring/spring-scheduler-async-boundaries.md)

### 4. Tenant context is part of identity

In multi-tenant systems, principal alone is not enough.
The tenant scope and resource ownership must be preserved too.

Read with:

- [멀티 테넌트 SaaS 격리 설계](../contents/system-design/multi-tenant-saas-isolation-design.md)

## 실전 시나리오

### 시나리오 1: async job loses the user context

Likely cause:

- SecurityContext not propagated
- MDC not copied

### 시나리오 2: forwarded IP is spoofed

Likely cause:

- untrusted proxy hop
- raw headers treated as truth

### 시나리오 3: service call has the right token but wrong tenant

Likely cause:

- identity propagated without tenant scope

## 코드로 보기

### Principal sketch

```java
public record Principal(String userId, String tenantId, Set<String> scopes) {}
```

### Thread-bound context note

```java
SecurityContext context = SecurityContextHolder.getContext();
```

### Header propagation sketch

```java
requestHeaders.set("X-Request-User", principal.userId());
requestHeaders.set("X-Tenant-Id", principal.tenantId());
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Pass raw user id | Simple | Unsafe and incomplete | Never for trust decisions |
| Signed JWT propagation | Stronger identity | Revocation complexity | APIs and service calls |
| mTLS + SPIFFE | Strong workload identity | Certificate ops | Service mesh or zero-trust setups |
| Thread-local propagation | Easy within a request | Fails across async boundaries | Small synchronous flows |

## 꼬리질문

> Q: Why is passing only the user id not enough?
> Intent: checks authenticity and scope awareness.
> Core: a bare id has no proof, no audience, and no tenant context.

> Q: Why does identity disappear across async boundaries?
> Intent: checks thread-bound context understanding.
> Core: thread-local state does not follow the work automatically.

> Q: Why are forwarded headers dangerous?
> Intent: checks trust-boundary awareness.
> Core: they can be spoofed unless a trusted proxy chain normalizes them.

## 한 줄 정리

Identity propagation is the safe transfer of caller identity and scope across every boundary where trust could otherwise be lost or widened.
