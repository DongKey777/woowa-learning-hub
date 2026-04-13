# Edge Request Lifecycle Master Note

> 한 줄 요약: the edge request lifecycle is the path from client to backend and back again, and every hop can change trust, latency, and failure semantics.

**Difficulty: Advanced**

> retrieval-anchor-keywords: request lifecycle, edge, reverse proxy, API gateway, TLS termination, header normalization, traceId, 401, 403, 429, 502, 503, 504, ingress, egress

> related docs:
> - [Spring MVC 요청 생명주기](../contents/spring/spring-mvc-request-lifecycle.md)
> - [API Gateway, Reverse Proxy 운영 포인트](../contents/network/api-gateway-reverse-proxy-operational-points.md)
> - [API Gateway Auth Rate Limit Chain](../contents/network/api-gateway-auth-rate-limit-chain.md)
> - [Load Balancer 헬스체크 실패 패턴](../contents/network/load-balancer-healthcheck-failure-patterns.md)
> - [Spring Observability / Micrometer / Tracing](../contents/spring/spring-observability-micrometer-tracing.md)
> - [Timeout types: connect/read/write](../contents/network/timeout-types-connect-read-write.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

The request lifecycle is not just "controller -> service -> DB".
At the edge, it is:

- DNS and connection setup
- TLS and proxy termination
- header normalization and trust decisions
- auth and rate limit
- routing and backend selection
- app execution
- response shaping and caching

If one hop is wrong, the bug often looks like a different layer's fault.

## 깊이 들어가기

### 1. The edge rewrites trust

The first trusted point is often the proxy or gateway, not the client.
That means forwarded headers, client IP, and protocol metadata need normalization.

Read with:

- [API Gateway, Reverse Proxy 운영 포인트](../contents/network/api-gateway-reverse-proxy-operational-points.md)
- [API Gateway Auth Rate Limit Chain](../contents/network/api-gateway-auth-rate-limit-chain.md)

### 2. Timeouts must be layered

Different hops have different budgets:

- connect timeout
- read timeout
- backend processing timeout
- gateway timeout

If these are inconsistent, retries and 504s become misleading.

### 3. The app lifecycle begins after the edge

Spring MVC request handling happens only after the request survives the edge path.
That is why edge issues often masquerade as app bugs.

Read with:

- [Spring MVC 요청 생명주기](../contents/spring/spring-mvc-request-lifecycle.md)

### 4. Observability should follow the hop chain

You want one trace id across:

- gateway
- service
- DB
- downstream calls

Read with:

- [Spring Observability / Micrometer / Tracing](../contents/spring/spring-observability-micrometer-tracing.md)

## 실전 시나리오

### 시나리오 1: client sees 504, app logs show nothing

Likely cause:

- timeout at proxy or load balancer
- upstream not reached

### 시나리오 2: client IP-based rate limit misfires

Likely cause:

- forwarded header not trusted
- proxy chain not normalized

### 시나리오 3: request succeeds in Postman but not browser

Likely cause:

- CORS, SameSite, credentialed request mismatch

## 코드로 보기

### Edge flow sketch

```text
client -> dns -> lb -> gateway -> service -> db -> response
```

### Spring request entry

```java
@RestController
public class OrderController {
    @GetMapping("/orders/{id}")
    public OrderDto get(@PathVariable Long id) {
        return service.get(id);
    }
}
```

### Trace propagation

```java
log.info("traceId={} path=/orders/{}", traceId, id);
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Edge auth/rate limit | Protects backend early | Adds gateway policy complexity | Public APIs |
| App-only control | Simple app flow | Weak edge protection | Small internal systems |
| Tight timeouts | Fast failure | More false positives | Latency-sensitive paths |
| Loose timeouts | Fewer false failures | More queued work | Rare slow workflows |

## 꼬리질문

> Q: Why does the same failure look different at the edge and in the app?
> Intent: checks hop-specific failure semantics.
> Core: the edge can fail before the app ever sees the request.

> Q: Why do we normalize headers at the gateway?
> Intent: checks trust-boundary awareness.
> Core: downstream services should not trust raw client-supplied hop data.

> Q: Why do timeouts need to be layered?
> Intent: checks end-to-end budget thinking.
> Core: each hop has its own processing and waiting budget.

## 한 줄 정리

The edge request lifecycle is the full hop chain that transforms a client packet into an application request, and each hop needs explicit trust, timeout, and observability rules.
