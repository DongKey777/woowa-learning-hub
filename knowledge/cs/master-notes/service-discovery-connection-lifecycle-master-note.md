# Service Discovery Connection Lifecycle Master Note

> 한 줄 요약: service discovery and connection lifecycle are one problem because discovering a new endpoint is useless unless you can connect, reuse, drain, and retire it safely.

**Difficulty: Advanced**

> retrieval-anchor-keywords: service discovery, DNS TTL, connection draining, keep-alive, health check, connection pool, endpoint rotation, stale connection, failover, circuit breaker, service mesh, sidecar, load balancer

> related docs:
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](../contents/network/connection-keepalive-loadbalancing-circuit-breaker.md)
> - [DNS TTL Cache Failure Patterns](../contents/network/dns-ttl-cache-failure-patterns.md)
> - [Load Balancer 헬스체크 실패 패턴](../contents/network/load-balancer-healthcheck-failure-patterns.md)
> - [Service Mesh, Sidecar Proxy](../contents/network/service-mesh-sidecar-proxy.md)
> - [API Gateway, Reverse Proxy 운영 포인트](../contents/network/api-gateway-reverse-proxy-operational-points.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Service discovery tells you where a service is.
Connection lifecycle tells you whether you can keep using the endpoint safely.

In practice, you need both:

- endpoint discovery
- health validation
- connection reuse
- draining
- stale connection eviction

## 깊이 들어가기

### 1. Discovery is not routing

DNS or registry lookup gives you an address.
It does not guarantee that the address is healthy or that old connections should be reused.

### 2. Keep-alive interacts with discovery

Long-lived connections can keep talking to old instances even after discovery has changed.

Read with:

- [Connection Keep-Alive, Load Balancing, Circuit Breaker](../contents/network/connection-keepalive-loadbalancing-circuit-breaker.md)

### 3. Health checks and draining matter

Discovered endpoints should be introduced and retired gradually.

Read with:

- [Load Balancer 헬스체크 실패 패턴](../contents/network/load-balancer-healthcheck-failure-patterns.md)

### 4. DNS TTL is a discovery cache policy

Discovery is often cached in resolvers, clients, proxies, and OS layers.

Read with:

- [DNS TTL Cache Failure Patterns](../contents/network/dns-ttl-cache-failure-patterns.md)

### 5. mTLS and sidecars change connection identity

In service mesh setups, the connection may be identity-bound to the workload rather than just the IP.

Read with:

- [Service Mesh, Sidecar Proxy](../contents/network/service-mesh-sidecar-proxy.md)
- [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)

## 실전 시나리오

### 시나리오 1: pod replaced, clients still hit old instance

Likely cause:

- stale connection pool
- DNS cache not expired
- draining not configured

### 시나리오 2: discovery shows healthy, but requests fail

Likely cause:

- health check too shallow
- instance ready but dependency not ready

### 시나리오 3: rollout causes reconnect storm

Likely cause:

- too many clients rotating at once
- no jitter or backoff

## 코드로 보기

### Discovery plus pool sketch

```text
resolve endpoint -> check health -> open/reuse connection -> drain old -> evict stale
```

### DNS observability

```bash
dig service.example.com
ss -tnp
```

### Pool policy sketch

```java
pool.evictIdleConnections();
pool.updateTargets(discoveredEndpoints);
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Fast discovery refresh | Quick failover | More churn | Dynamic environments |
| Long-lived connections | Lower handshake cost | Stale endpoint risk | Stable backends |
| Aggressive draining | Safer rollout | More reconnects | Planned deployment |
| Sticky connections | Better locality | Uneven load | Stateful or affinity-heavy paths |

## 꼬리질문

> Q: Why is service discovery not enough by itself?
> Intent: checks endpoint lifecycle awareness.
> Core: a discovered endpoint can still be stale, unhealthy, or draining.

> Q: Why do old connections survive discovery changes?
> Intent: checks connection reuse understanding.
> Core: connection pools keep using established sockets until evicted.

> Q: Why are DNS TTL and draining related?
> Intent: checks rollout and cache interaction.
> Core: both govern how quickly traffic moves away from old instances.

## 한 줄 정리

Service discovery and connection lifecycle must be designed together so endpoints can be found, reused, drained, and retired without breaking traffic.
