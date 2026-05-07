---
schema_version: 3
title: "Proxy Local Reply vs Upstream Error Attribution"
concept_id: network/proxy-local-reply-vs-upstream-error-attribution
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- proxy-local-reply
- upstream-attribution
- gateway-error
aliases:
- proxy local reply
- upstream error attribution
- generated response
- Envoy local reply
- Nginx generated error
- gateway response source
- 502 503 504 attribution
symptoms:
- 사용자가 503을 봤다는 이유만으로 upstream app이 503을 반환했다고 판단한다
- app 로그에는 없는데 edge나 gateway에서 502 503 504 429가 생기는 상황을 설명하지 못한다
- proxy local timeout과 app 성공 로그가 동시에 존재할 때 blame을 잘못 잡는다
- status code만 보고 retry해서 local rate limit이나 auth reject를 악화시킨다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/api-gateway-reverse-proxy-operational-points
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
next_docs:
- network/service-mesh-local-reply-timeout-reset-attribution
- network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb
- network/timeout-budget-propagation-proxy-gateway-service-hop-chain
- network/grpc-status-trailers-transport-error-mapping
linked_paths:
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
- contents/network/grpc-status-trailers-transport-error-mapping.md
- contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md
- contents/network/load-balancer-healthcheck-failure-patterns.md
- contents/network/service-mesh-local-reply-timeout-reset-attribution.md
- contents/network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md
- contents/spring/spring-mvc-exception-resolver-chain-contract.md
confusable_with:
- network/service-mesh-local-reply-timeout-reset-attribution
- network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
- network/grpc-status-trailers-transport-error-mapping
forbidden_neighbors: []
expected_queries:
- "502 503 504가 proxy local reply인지 upstream app 응답인지 어떻게 구분해?"
- "edge는 504인데 app은 200 성공 로그가 있는 상황을 어떻게 해석해?"
- "Envoy local reply와 upstream reset attribution을 어떤 지표로 나눠?"
- "gateway local rate limit 429를 app 429로 오해하면 왜 위험해?"
- "proxy generated response에는 어떤 header나 timing clue가 남아?"
contextual_chunk_prefix: |
  이 문서는 proxy/gateway local reply와 upstream app response attribution,
  502/503/504/429 생성 주체, timeout/reset/rate-limit source-aware retry를
  다루는 advanced playbook이다.
---
# Proxy Local Reply vs Upstream Error Attribution

> 한 줄 요약: `502`, `503`, `504`, `429`가 보여도 그 응답이 upstream app이 만든 것인지 proxy가 local reply로 합성한 것인지 구분하지 못하면 장애 원인을 엉뚱한 서비스에 돌리기 쉽다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [gRPC Status, Trailers, Transport Error Mapping](./grpc-status-trailers-transport-error-mapping.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)
> - [Service Mesh Local Reply, Timeout, Reset Attribution](./service-mesh-local-reply-timeout-reset-attribution.md)
> - [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)
> - [Spring MVC Exception Resolver Chain Contract](../spring/spring-mvc-exception-resolver-chain-contract.md)

retrieval-anchor-keywords: proxy local reply, upstream error attribution, 502 vs 503 vs 504, generated response, envoy local reply, nginx generated error, upstream reset, error source, gateway response, blame isolation

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

프록시와 게이트웨이는 upstream 응답을 그대로 전달만 하지 않는다.  
스스로 응답을 생성할 수도 있다.

- upstream timeout으로 `504`
- no healthy upstream으로 `503`
- protocol error나 invalid response로 `502`
- local rate limit으로 `429`

이 차이를 모르면 "사용자가 503을 봤다 = app이 503을 반환했다"처럼 오해하기 쉽다.

### Retrieval Anchors

- `proxy local reply`
- `upstream error attribution`
- `502 vs 503 vs 504`
- `generated response`
- `envoy local reply`
- `nginx generated error`
- `error source`
- `gateway response`

## 깊이 들어가기

### 1. 같은 HTTP status라도 생성 주체가 다를 수 있다

예를 들어 `503`은 여러 뜻일 수 있다.

- app이 capacity 부족으로 직접 반환
- proxy가 no healthy upstream으로 생성
- rate limit이나 circuit breaker가 local reject

HTTP status 숫자만 보면 이 셋이 모두 같은 `503`으로 보인다.

### 2. local reply는 upstream service time이 0에 가까울 수 있다

proxy가 locally reject하면:

- upstream connection을 아예 안 열었을 수 있다
- app 로그에는 요청이 없을 수 있다
- user는 여전히 5xx/4xx를 본다

그래서 app 팀은 "우리 서비스는 요청을 못 받았다"고 하고, edge 팀은 "사용자는 503을 봤다"고 하는 식의 혼선이 생긴다.

### 3. timeout 기반 local reply는 특히 blame을 어렵게 만든다

예:

- gateway timeout 800ms
- app은 900ms에 200 준비
- user는 504를 봄
- app은 성공 로그를 남김

이 경우 응답 코드를 기준으로 app을 blame하면 틀린다.  
문제는 end-to-end budget과 proxy local timeout 정책일 수 있다.

### 4. gRPC와 HTTP/JSON은 local reply 표면이 다를 수 있다

JSON/REST에서는 502/503/504 같은 HTTP status로 보일 수 있고,  
gRPC에서는 proxy가 HTTP/2 reset이나 translated gRPC status를 만들어 낼 수 있다.

즉 local reply는 프로토콜마다 표면 표현은 달라도 본질은 같다.

- upstream app 응답이 아니다
- proxy/gateway 정책의 결과다

### 5. observability는 error source를 별도 차원으로 남겨야 한다

다음 구분이 중요하다.

- edge-generated response
- sidecar-generated response
- upstream app response
- upstream transport failure translated by proxy

이 차원이 없으면 5xx 대시보드가 오히려 원인 추적을 방해한다.

### 6. retry 정책도 source-aware해야 한다

local reply는 원인에 따라 retry 판단이 다르다.

- no healthy upstream: retry해도 의미가 작을 수 있다
- transient upstream reset: 제한적 retry 가능
- local rate limit: retry는 오히려 해롭다
- local auth reject: retry하면 안 된다

즉 status code만으로 retry하면 안 되고, **누가 만들었는가**를 봐야 한다.
실제 운영에서는 [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)처럼 vendor별 surface 차이까지 번역해야 incident triage가 빨라진다.

## 실전 시나리오

### 시나리오 1: edge는 504 폭증인데 app은 200 성공이 많다

전형적인 gateway local timeout 패턴이다.

### 시나리오 2: 배포 중 503이 늘었는데 app 로그가 비어 있다

no healthy upstream, drain race, readiness mismatch로 proxy가 local reply를 만든 것일 수 있다.

### 시나리오 3: gRPC 클라이언트는 `UNAVAILABLE`을 보는데 서버는 status를 안 남겼다

transport failure를 proxy/client library가 번역한 local surface일 수 있다.

### 시나리오 4: rate limit을 켠 뒤 upstream 429처럼 보인다

실제로는 gateway local rate limit이 만든 응답인데, app 팀이 자기 코드로 오해할 수 있다.

## 코드로 보기

### 관찰 포인트

```text
- upstream cluster selected 여부
- upstream connect / first byte / total time
- response source: local reply or upstream response
- no healthy upstream / timeout / local rate limit counters
```

### 현장 질문

```text
- 이 응답은 upstream app 로그에 존재하는가
- upstream response body/headers가 실제로 있었는가
- proxy가 local timeout / local rate limit / no healthy upstream을 기록했는가
- retry가 source-aware하게 동작하는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| local reply 적극 사용 | 빠른 fail-fast와 일관된 정책 적용이 가능하다 | app와 edge 사이 blame 혼선이 커질 수 있다 | gateway, mesh |
| 모든 오류를 upstream에 넘김 | 책임 경계가 단순해 보인다 | 보호 계층이 약해지고 overload 전파가 커질 수 있다 | 작은 단일 시스템 |
| source-tagged observability | 원인 추적이 빨라진다 | 로그/메트릭 설계가 더 복잡하다 | 운영 성숙도 높은 팀 |
| status-code only dashboards | 단순하다 | local reply와 upstream app 실패를 구분 못 한다 | 초기 단계만 적합 |

핵심은 응답 코드보다 먼저 **누가 그 응답을 만들었는지**를 분리해서 보는 것이다.

## 꼬리질문

> Q: 사용자가 503을 봤으면 app이 503을 반환한 건가요?
> 핵심: 아니다. proxy/gateway가 local reply로 만든 것일 수 있다.

> Q: local reply는 왜 필요한가요?
> 핵심: fail-fast, rate limit, no healthy upstream, timeout 같은 보호 정책을 앞단에서 일관되게 적용하기 위해서다.

> Q: 왜 retry 판단에도 local reply source가 중요하나요?
> 핵심: 같은 status라도 원인이 rate limit, timeout, no healthy upstream인지에 따라 retry 효과가 완전히 다르기 때문이다.

## 한 줄 정리

운영에서 5xx/4xx를 정확히 해석하려면 응답 코드 자체보다, 그 응답이 upstream app 결과인지 proxy가 local reply로 합성한 것인지 먼저 구분해야 한다.
