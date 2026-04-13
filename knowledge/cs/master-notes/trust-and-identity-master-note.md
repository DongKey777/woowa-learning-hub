# Trust and Identity Master Note

> 한 줄 요약: trust and identity are the base layer for every other authorization, routing, and policy decision in a distributed system.

**Difficulty: Advanced**

> retrieval-anchor-keywords: identity, trust boundary, mTLS, SPIFFE, JWT, session, principal, tenant membership, origin, proxy trust, workload identity, revocation, attestation, authz

> related docs:
> - [Authentication vs Authorization](../contents/security/authentication-vs-authorization.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)
> - [JWT Deep Dive](../contents/security/jwt-deep-dive.md)
> - [OAuth2 Authorization Code Grant](../contents/security/oauth2-authorization-code-grant.md)
> - [Forwarded / X-Forwarded-For / X-Real-IP Trust Boundary](../contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
> - [TLS, Load Balancing, Proxy](../contents/network/tls-loadbalancing-proxy.md)
> - [멀티 테넌트 SaaS 격리 설계](../contents/system-design/multi-tenant-saas-isolation-design.md)
> - [Spring Security Architecture](../contents/spring/spring-security-architecture.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Identity answers who or what is calling.
Trust answers which claims and hops we are willing to believe.

Every distributed policy depends on both:

- browser auth
- service auth
- tenant isolation
- forwarded headers
- proxy behavior

If the identity source is weak, every downstream decision becomes fragile.

## 깊이 들어가기

### 1. User identity and workload identity are different

People log in.
Workloads attest.

Read with:

- [Authentication vs Authorization](../contents/security/authentication-vs-authorization.md)
- [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)

### 2. Trust boundaries move at proxies

When TLS terminates or headers are rewritten, the boundary has changed.

Read with:

- [Forwarded / X-Forwarded-For / X-Real-IP Trust Boundary](../contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
- [TLS, Load Balancing, Proxy](../contents/network/tls-loadbalancing-proxy.md)

### 3. Tokens are not identity by themselves

JWT, session ids, and OAuth codes are carriers.
The trust decision comes from how they are issued, rotated, and validated.

Read with:

- [JWT Deep Dive](../contents/security/jwt-deep-dive.md)
- [OAuth2 Authorization Code Grant](../contents/security/oauth2-authorization-code-grant.md)

### 4. Identity must align with authorization scope

The principal is useless without scope, tenant, audience, and resource ownership.

Read with:

- [Spring Security Architecture](../contents/spring/spring-security-architecture.md)
- [멀티 테넌트 SaaS 격리 설계](../contents/system-design/multi-tenant-saas-isolation-design.md)

## 실전 시나리오

### 시나리오 1: a forwarded header is spoofed

Likely cause:

- proxy trust boundary not enforced

### 시나리오 2: service identity is valid but the action is forbidden

Likely cause:

- workload identity and authorization scope disagree

### 시나리오 3: user login succeeded but tenant access failed

Likely cause:

- principal authenticated without tenant membership resolution

## 코드로 보기

### Principal sketch

```java
public record Principal(String subject, String tenantId, Set<String> scopes) {}
```

### Trust check sketch

```java
if (!trustedProxySet.contains(remoteAddr)) {
    clientIp = remoteAddr;
}
```

### mTLS policy sketch

```yaml
principals:
  - "spiffe://prod.example.com/ns/payments/sa/orders-api"
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Session identity | Simple revocation | Server state | Browser apps |
| JWT identity | Distributed verification | Revocation burden | APIs and services |
| mTLS identity | Strong transport trust | Certificate ops | Service-to-service traffic |
| Proxy-derived identity | Easier routing | Trust boundary risk | Controlled edge environments |

## 꼬리질문

> Q: Why is identity not the same as authorization?
> Intent: checks security layer separation.
> Core: identity says who; authorization says what that identity may do.

> Q: Why do proxies affect trust?
> Intent: checks boundary shifting.
> Core: a proxy can rewrite or terminate information that downstream code relies on.

> Q: Why is mTLS useful but not sufficient?
> Intent: checks layered security understanding.
> Core: mTLS proves transport identity, not business permission.

## 한 줄 정리

Trust and identity are the substrate beneath every other security and routing choice, so boundary mistakes at this layer echo everywhere downstream.
