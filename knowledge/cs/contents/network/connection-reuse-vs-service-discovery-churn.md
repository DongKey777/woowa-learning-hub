---
schema_version: 3
title: "Connection Reuse vs Service Discovery Churn"
concept_id: network/connection-reuse-vs-service-discovery-churn
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 83
mission_ids: []
review_feedback_tags:
- connection-reuse-discovery-churn
- stale-endpoint-routing
- pool-refresh-dns-ttl
aliases:
- connection reuse service discovery churn
- stale routing
- stale endpoint
- DNS change pool refresh
- backend rotation keep-alive
- endpoint update connection pool
symptoms:
- DNS나 service registry는 바뀌었는데 app connection pool이 오래된 endpoint를 계속 친다
- backend rotation 직후 일부 요청만 실패하는데 DNS TTL만 보고 opened connection lifetime을 놓친다
- connection reuse 최적화가 service discovery refresh와 충돌하는 장면을 보지 못한다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- network/connection-keepalive-loadbalancing-circuit-breaker
- network/dns-ttl-cache-failure-patterns
next_docs:
- network/idle-timeout-mismatch-lb-proxy-app
- network/dns-negative-caching-nxdomain-behavior
- network/http2-http3-connection-reuse-coalescing
- network/connection-pool-starvation-stale-idle-reuse-debugging
linked_paths:
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/network/idle-timeout-mismatch-lb-proxy-app.md
- contents/network/dns-ttl-cache-failure-patterns.md
- contents/network/dns-negative-caching-nxdomain-behavior.md
- contents/network/http2-http3-connection-reuse-coalescing.md
confusable_with:
- network/dns-ttl-cache-failure-patterns
- network/dns-negative-caching-nxdomain-behavior
- network/connection-pool-starvation-stale-idle-reuse-debugging
- network/http2-http3-connection-reuse-coalescing
- network/idle-timeout-mismatch-lb-proxy-app
forbidden_neighbors: []
expected_queries:
- "Service discovery가 바뀌었는데 connection pool이 stale endpoint를 계속 쓰는 이유가 뭐야?"
- "DNS TTL과 pool idle lifetime과 endpoint refresh interval을 어떻게 맞춰야 해?"
- "backend rotation 뒤 일부 요청만 실패하면 connection reuse와 discovery churn을 어떻게 의심해?"
- "새 주소는 알아도 옛 keep-alive connection을 계속 쓰는 상태를 어떻게 진단해?"
- "Blue-green canary 배포에서 pool refresh가 늦으면 어떤 장애가 생겨?"
contextual_chunk_prefix: |
  이 문서는 connection reuse, service discovery churn, DNS TTL,
  endpoint refresh, stale routing, backend rotation, pool idle eviction,
  validation on borrow를 연결하는 advanced operational playbook이다.
---
# Connection Reuse vs Service Discovery Churn

> 한 줄 요약: connection reuse는 handshake를 아끼지만, service discovery가 자주 바뀌는 환경에서는 오래된 연결이 새 라우팅 현실과 어긋날 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
> - [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)
> - [DNS Negative Caching, NXDOMAIN Behavior](./dns-negative-caching-nxdomain-behavior.md)
> - [HTTP/2, HTTP/3 Connection Reuse, Coalescing](./http2-http3-connection-reuse-coalescing.md)

retrieval-anchor-keywords: connection reuse, service discovery churn, stale routing, DNS change, pool refresh, endpoint update, keep-alive, stale endpoint, backend rotation

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

connection reuse는 매 요청마다 새 연결을 만들지 않기 위해 존재한다.

- latency가 줄어든다
- resource 사용이 줄어든다
- TCP/TLS 비용이 낮아진다

하지만 서비스 디스커버리 churn이 심하면 오래된 연결이 **이미 바뀐 endpoint 현실을 모를 수 있다**.

### Retrieval Anchors

- `connection reuse`
- `service discovery churn`
- `stale routing`
- `DNS change`
- `pool refresh`
- `endpoint update`
- `keep-alive`
- `stale endpoint`
- `backend rotation`

## 깊이 들어가기

### 1. 왜 reuse가 필요한가

연결을 새로 맺는 비용은 작지 않다.

- connect latency
- TLS handshake
- kernel/socket overhead
- CPU and queue cost

reuse는 이런 비용을 줄여 준다.

### 2. 왜 churn과 충돌하나

service discovery가 자주 바뀌면:

- 새 endpoint가 등록된다
- 기존 endpoint가 내려간다
- DNS나 registry가 갱신된다

그런데 connection pool은 이미 열린 소켓을 계속 믿을 수 있다.

### 3. stale endpoint가 왜 생기나

- DNS cache가 오래 남는다
- pool이 idle connection을 오래 보유한다
- backend rotation이 발생했는데 validation이 없다

결과적으로 "새 주소는 알아도 옛 연결을 계속 쓰는" 상태가 된다.

### 4. connection reuse와 discovery refresh를 어떻게 맞추나

좋은 방향:

- pool idle eviction
- DNS TTL과 pool lifetime 정렬
- service discovery refresh 주기 확인
- health check와 validation on borrow

핵심은 connection reuse가 service discovery를 무시하지 않게 하는 것이다.

### 5. 언제 특히 위험한가

- k8s pod IP가 자주 바뀌는 환경
- blue-green/canary 배포
- 외부 API endpoint가 바뀌는 경우
- multi-region failover

## 실전 시나리오

### 시나리오 1: DNS는 바뀌었는데 앱은 옛 서버를 계속 친다

pool이 오래된 connection을 재사용하고 있을 수 있다.  
이때는 [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)도 같이 봐야 한다.

### 시나리오 2: backend가 교체됐는데 일부 요청만 실패한다

stale endpoint와 connection reuse가 충돌할 수 있다.

### 시나리오 3: 서비스 디스커버리 갱신 직후 latency가 출렁인다

pool refresh와 discovery refresh가 비동기일 수 있다.

## 코드로 보기

### 점검 포인트

```text
- pool idle timeout
- DNS TTL
- endpoint refresh interval
- validation on borrow
```

### 운영 관찰

```bash
dig api.example.com
ss -tan state established
```

### 개념 비교

```text
reuse: faster, cheaper
churn: fresher, safer routing
problem: stale connection to stale endpoint
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 강한 connection reuse | 비용이 낮다 | stale routing 위험이 있다 | 안정적인 backend |
| 자주 refresh | 최신 라우팅을 반영한다 | handshake 비용이 늘어난다 | churn이 큰 환경 |
| reuse + validation | 둘의 균형이 좋다 | 구현이 복잡하다 | 운영 안정성이 중요한 경우 |

핵심은 connection reuse를 포기하는 것이 아니라 **discovery churn과의 위상 차이를 줄이는 것**이다.

## 꼬리질문

> Q: connection reuse와 service discovery churn이 왜 충돌하나요?
> 핵심: 연결은 오래 살아 있는데 라우팅 현실은 이미 바뀌었을 수 있기 때문이다.

> Q: stale endpoint는 어떻게 생기나요?
> 핵심: DNS cache, pool reuse, backend rotation이 맞물려 생긴다.

> Q: 어떻게 줄이나요?
> 핵심: pool eviction과 discovery refresh를 정렬하고 validation을 넣는다.

## 한 줄 정리

connection reuse는 비용을 줄이지만 service discovery churn이 큰 환경에서는 stale endpoint를 계속 믿지 않도록 refresh와 validation을 같이 설계해야 한다.
