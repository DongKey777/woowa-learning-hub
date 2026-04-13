# Trust Boundary Proxy Master Note

> 한 줄 요약: a proxy is never neutral; it either preserves, reshapes, or destroys the trust boundary around the request.

**Difficulty: Advanced**

> retrieval-anchor-keywords: trusted proxy, X-Forwarded-For, Forwarded header, X-Real-IP, reverse proxy, API gateway, sidecar proxy, TLS termination, mTLS, host header spoofing, origin trust, load balancer, client IP

> related docs:
> - [Forwarded / X-Forwarded-For / X-Real-IP Trust Boundary](../contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
> - [TLS, Load Balancing, Proxy](../contents/network/tls-loadbalancing-proxy.md)
> - [Service Mesh, Sidecar Proxy](../contents/network/service-mesh-sidecar-proxy.md)
> - [API Gateway / Reverse Proxy Operational Points](../contents/network/api-gateway-reverse-proxy-operational-points.md)
> - [API Gateway / Auth / Rate Limit Chain](../contents/network/api-gateway-auth-rate-limit-chain.md)
> - [HTTPS, HSTS, MITM](../contents/security/https-hsts-mitm.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)
> - [Spring Security Architecture](../contents/spring/spring-security-architecture.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

A proxy can be:

- a traffic router
- a security control point
- a trust translator
- a failure amplifier

The trust boundary changes depending on whether the proxy is:

- edge-facing
- internal
- service mesh sidecar
- CDN
- gateway

If you do not know which proxy you are talking about, you probably do not know which headers to trust either.

## 깊이 들어가기

### 1. Client IP is an assertion, not a fact

The request may pass through multiple hops.

The original client IP can be expressed in:

- `Forwarded`
- `X-Forwarded-For`
- `X-Real-IP`

But only trusted proxies should populate or rewrite those values.

Read with:

- [Forwarded / X-Forwarded-For / X-Real-IP Trust Boundary](../contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)

### 2. TLS termination moves the boundary

When TLS is terminated at a proxy, the proxy can inspect or alter traffic before forwarding it.

That creates both benefits and risks:

- centralized cert management
- routing and observability
- but also a new point that must be trusted

Read with:

- [TLS, Load Balancing, Proxy](../contents/network/tls-loadbalancing-proxy.md)
- [HTTPS, HSTS, MITM](../contents/security/https-hsts-mitm.md)

### 3. Sidecar and mesh proxies are internal trust boundaries

Inside the cluster, proxies still matter because they can:

- enforce mTLS
- attach identity
- collect telemetry
- apply retries or timeouts

Read with:

- [Service Mesh, Sidecar Proxy](../contents/network/service-mesh-sidecar-proxy.md)
- [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)

### 4. Gateways often mix security and policy

The gateway may perform:

- auth
- rate limiting
- header normalization
- routing
- logging

That means mistakes can leak across layers.

Read with:

- [API Gateway / Auth / Rate Limit Chain](../contents/network/api-gateway-auth-rate-limit-chain.md)
- [API Gateway / Reverse Proxy Operational Points](../contents/network/api-gateway-reverse-proxy-operational-points.md)

## 실전 시나리오

### 시나리오 1: spoofed client IP

If the app trusts forwarded headers from an untrusted hop, an attacker can fake source IP or geolocation.

### 시나리오 2: TLS terminates at the proxy, but upstream assumptions still expect end-to-end TLS

This creates a boundary mismatch and often a false sense of encryption coverage.

### 시나리오 3: gateway auth and app auth disagree

The proxy may allow a request while the app still rejects it, or vice versa.

### 시나리오 4: mesh retries hide downstream failure

The proxy can amplify load when retry policy is too aggressive.

## 코드로 보기

### Trusted proxy check sketch

```java
boolean isTrustedProxy(String ip) {
    return trustedProxySet.contains(ip);
}
```

### Header extraction sketch

```java
String clientIp = extractClientIp(request);
if (!isTrustedProxy(request.getRemoteAddr())) {
    clientIp = request.getRemoteAddr();
}
```

### Nginx-style normalization idea

```nginx
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Real-IP $remote_addr;
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Trust only edge proxy | Simple policy | Less flexibility | Small deployments |
| Trust chain of proxies | Works with multi-hop routing | More configuration risk | Real-world infrastructures |
| TLS passthrough | End-to-end crypto | Less gateway visibility | Strict trust models |
| TLS termination at proxy | Easier ops | Proxy becomes trusted boundary | Common production edge |

## 꼬리질문

> Q: Why is `X-Forwarded-For` dangerous if trusted blindly?
> Intent: checks spoofing awareness.
> Core: the client can inject fake headers unless the proxy boundary is enforced.

> Q: What changes when TLS is terminated at a proxy?
> Intent: checks boundary shifts.
> Core: the proxy becomes part of the trust chain and can inspect traffic.

> Q: Why do service mesh proxies matter for security?
> Intent: checks internal trust boundary understanding.
> Core: they can enforce identity and policy between services.

> Q: Why can proxies amplify outages?
> Intent: checks retry and routing side effects.
> Core: retries, buffering, and queueing can multiply downstream pressure.

## 한 줄 정리

Trust-boundary proxies are security devices, routing devices, and failure domains at the same time, so header trust must match the hop you actually control.
