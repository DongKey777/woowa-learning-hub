---
schema_version: 3
title: "Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB"
concept_id: network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- proxy-vendor
- symptom-translation
- incident-attribution
aliases:
- Nginx symptom translation
- Envoy symptom translation
- ALB symptom translation
- proxy symptom mapping
- Envoy response_code_details
- ALB 460
- Nginx 499
- response flags
symptoms:
- Nginx 499를 app이 반환한 status로 해석한다
- Envoy local reply 503을 upstream app capacity issue로만 본다
- ALB 502를 app HTTP handler bug로 단정하고 target connection/protocol issue를 놓친다
- vendor별 access log/error log/response flag 필드 없이 HTTP status 숫자만 본다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/proxy-local-reply-vs-upstream-error-attribution
- network/service-mesh-local-reply-timeout-reset-attribution
next_docs:
- network/mesh-adaptive-concurrency-local-reply-metrics-tuning
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
- network/gateway-buffering-vs-spring-early-reject
- network/load-balancer-healthcheck-failure-patterns
linked_paths:
- contents/network/proxy-local-reply-vs-upstream-error-attribution.md
- contents/network/service-mesh-local-reply-timeout-reset-attribution.md
- contents/network/adaptive-concurrency-limiter-latency-signal-gateway-mesh.md
- contents/network/mesh-adaptive-concurrency-local-reply-metrics-tuning.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
- contents/network/gateway-buffering-vs-spring-early-reject.md
- contents/network/http-request-body-drain-early-reject-keepalive-reuse.md
- contents/network/connection-draining-vs-fin-rst-graceful-close.md
- contents/network/load-balancer-healthcheck-failure-patterns.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
confusable_with:
- network/proxy-local-reply-vs-upstream-error-attribution
- network/service-mesh-local-reply-timeout-reset-attribution
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
- network/load-balancer-healthcheck-failure-patterns
forbidden_neighbors: []
expected_queries:
- "Nginx Envoy ALB는 같은 upstream 문제를 어떻게 다르게 로그로 보여줘?"
- "Nginx 499 Envoy response flags ALB target_status_code를 generic category로 번역해줘"
- "Envoy local reply 503과 upstream app 503을 어떻게 구분해?"
- "ALB 502가 app handler bug가 아니라 target connection error일 수 있는 이유는?"
- "vendor-specific proxy symptom translation table이 incident blame에 왜 필요해?"
contextual_chunk_prefix: |
  이 문서는 Nginx, Envoy, ALB의 499/502/503/504, response flags,
  response_code_details, ALB target fields를 generic proxy attribution으로 번역하는
  advanced playbook이다.
---
# Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB

> 한 줄 요약: 같은 upstream 문제도 Nginx, Envoy, ALB는 서로 다른 코드와 로그 표면으로 보여 준다. 증상을 vendor별 표현으로 번역하지 못하면 팀 간 blame이 어긋난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
> - [Service Mesh Local Reply, Timeout, Reset Attribution](./service-mesh-local-reply-timeout-reset-attribution.md)
> - [Adaptive Concurrency Limiter, Latency Signal, Gateway/Mesh](./adaptive-concurrency-limiter-latency-signal-gateway-mesh.md)
> - [Mesh Adaptive Concurrency, Local Reply, Metrics Tuning](./mesh-adaptive-concurrency-local-reply-metrics-tuning.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
> - [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
> - [Connection Draining vs FIN, RST, Graceful Close](./connection-draining-vs-fin-rst-graceful-close.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)

retrieval-anchor-keywords: Nginx symptom translation, Envoy symptom translation, ALB symptom translation, buffered upload reject, upload 401 499 split, nginx request_completion, envoy response_code_details, envoy connection termination details, ALB 460, elb_status_code target_status_code, actions_executed, 499, local reply, upstream reset, target response error, response flags, proxy symptom mapping, vendor-specific proxy logs, adaptive concurrency shedding, route timeout local reply, no healthy upstream, local origin transport failure

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

운영자가 보는 "같은 장애"는 proxy/vendor마다 표면이 다르다.

- Nginx: `499`, `502`, `upstream prematurely closed connection`
- Envoy: local reply, response flags, upstream reset reason
- ALB: target timeout, 502/503/504, target connection error

그래서 실제 triage는 network 원인 분석 전에 **표면 증상 번역표**가 필요하다.

### Retrieval Anchors

- `Nginx symptom translation`
- `Envoy symptom translation`
- `ALB symptom translation`
- `buffered upload reject`
- `nginx request_completion`
- `envoy response_code_details`
- `ALB 460`
- `target_status_code`
- `499`
- `upstream reset`
- `response flags`
- `target response error`
- `proxy symptom mapping`
- `adaptive concurrency shedding`
- `route timeout local reply`
- `no healthy upstream`

## 깊이 들어가기

### 1. HTTP status 숫자만 보면 vendor 차이를 놓친다

예를 들어 `502`라도:

- Nginx는 invalid upstream response
- Envoy는 upstream reset translated response
- ALB는 target connection/protocol issue

처럼 의미가 다를 수 있다.

### 2. Nginx는 access log와 error log 조합이 중요하다

Nginx는:

- access log status
- upstream status/time
- error log 문구

를 같이 봐야 원인이 드러난다.

특히 `499`는 app status가 아니라 client abort 관찰 결과라는 점이 중요하다.

### 3. Envoy/mesh는 response flags와 local reply reason이 핵심이다

Envoy 계열은:

- local reply 여부
- response flags
- upstream transport failure reason
- stream reset reason

같은 부가 필드가 없으면 status만으로는 거의 해석이 안 된다.

### 4. ALB는 target health와 front-door behavior를 같이 봐야 한다

ALB는 앱 로그와 1:1 대응이 약하다.

- target group health
- target response latency
- connection error / timeout
- client-facing code

를 같이 봐야 한다.

즉 ALB는 app보다는 **target selection과 edge transport 관점**이 강하다.

### 5. vendor translation table이 없으면 blame이 틀어진다

전형적인 혼선:

- Nginx 499를 app 499처럼 오해
- Envoy local reply 503을 upstream app capacity issue로 오해
- ALB 502를 app HTTP handler bug로 단정

그래서 incident 대응엔 "vendor symptom → generic category" 매핑이 필요하다.

### Symptom Mapping Tables

#### Table 1. Client-facing symptom -> vendor surface

| Generic Category | Nginx에서 흔한 표면 | Envoy에서 흔한 표면 | ALB에서 흔한 표면 |
|------------------|--------------------|---------------------|-------------------|
| client abort | `499` | downstream disconnect / reset 후 local surface | `460` 또는 edge-generated close 성격으로 보이고 target 로그는 비어 있을 수 있음 |
| local timeout | `504` + upstream timeout 문구 | local reply 504 / timeout flags | 504 계열 timeout |
| no healthy upstream | 502/503 또는 upstream unavailable surface | local reply 503 / no healthy upstream | target unhealthy / 503 성격 |
| upstream reset | `502` + upstream prematurely closed | upstream reset, response flags | 502/connection error 성격 |
| local rate limit / shedding | local 429/503 | local reply 429/503 | edge/local policy surface |

#### Table 2. 먼저 확인할 로그/메트릭 축

| Vendor | 먼저 볼 것 | 왜 중요한가 |
|--------|------------|--------------|
| Nginx | access status + upstream status/time + error log 문구 | 숫자만으론 499/502 원인 구분이 안 됨 |
| Envoy | response flags + local reply reason + upstream reset detail | status code만으로는 local/app 구분이 거의 안 됨 |
| ALB | target health + target response timing + edge status | app 로그와 1:1 대응이 약해서 target 선택 관점이 중요 |

#### Table 3. Mesh overload / local reply-specific crosswalk

| Generic Cause | Envoy/mesh focus | Nginx/ingress surface | ALB/front door surface | Distinguishing clue |
|---------------|------------------|-----------------------|------------------------|---------------------|
| adaptive concurrency shedding | limit drop, local reject/local reply reason, upstream time 거의 0 | 503/429와 매우 짧은 upstream time | 503/edge 5xx인데 target app은 비교적 건강 | app saturation metric이 같은 비율로 오르지 않음 |
| local rate limit | local rate limit counters, policy hit | 429 또는 503 | edge policy/WAF block | principal/route별 token depletion이 보임 |
| route timeout before app reply | route timeout, deadline budget mismatch | 504 + timeout 문구 | 504 / target timeout | app 성공 로그가 뒤늦게 남을 수 있음 |
| no healthy upstream / drain gap | cluster health drop, endpoint churn | rollout 중 502/503 | unhealthy target / 503 | target/app 로그가 거의 없음 |
| local origin transport failure | mTLS/connect/reset failure detail | 502/bad gateway 계열 | 502/connection error | request가 app까지 가지 않았을 수 있음 |

#### Table 4. Generic remap에서 절대 잃지 말아야 할 축

| Axis | Example values | 왜 중요한가 |
|------|----------------|-------------|
| response source | local reply / translated upstream failure / upstream app response | 같은 503이어도 owner가 다르다 |
| failure phase | before connect / after headers / during stream / after client disconnect | app이 실행됐는지와 결과가 어디서 사라졌는지 알려 준다 |
| retry stance | safe / budgeted / unsafe | retry amplification을 막는다 |
| traffic class | health, control plane, unary user API, batch/streaming | adaptive concurrency tuning은 누가 보호되고 희생됐는지와 연결된다 |

### 6. buffered upload reject와 `499`/`401` split은 vendor field를 같이 봐야 한다

업로드 reject incident에서는 status 숫자보다 먼저 아래 질문을 고정해야 한다.

- 누가 request body를 실제로 들고 있었는가
- reject decision은 local reply였는가, upstream 응답이었는가
- client가 reject를 읽고 떠났는가, 읽기 전에 끊었는가
- unread body cleanup이 drain이었는가, close였는가, 이미 edge buffering으로 끝났는가

#### Table 5. Buffered upload reject surface map

| Generic Question | Nginx에서 볼 축 | Envoy에서 볼 축 | ALB에서 볼 축 |
|------------------|-----------------|-----------------|---------------|
| edge/local tier가 body를 잡고 `401/413`을 만들었는가 | `status=401/413`인데 `upstream_status=-`, `$request_length`와 `$request_time`은 클 수 있음 | `response_code=401/413`, `%UPSTREAM_HOST%=-`, `%BYTES_RECEIVED%`는 크고 `%RESPONSE_CODE_DETAILS%`는 local deny 성격 | `elb_status_code=401/413`, `target_status_code=-`, `actions_executed`가 auth/fixed-response/WAF 성격, `received_bytes`가 큼 |
| app은 요청을 못 봤는데 upload 시간은 길었는가 | `proxy_request_buffering on`이면 edge가 body를 오래 잡고 upstream 시간은 비거나 짧을 수 있음 | buffer/ext_authz 경로면 upstream 연결 전에도 `%BYTES_RECEIVED%`와 `%DURATION%`이 길어질 수 있음 | POST upload 시간은 WAF 연결 여부에 따라 `request_processing_time` 또는 `target_processing_time`에 치우쳐 보일 수 있음 |
| reject 후 client가 떠나 split이 생겼는가 | 최종 access status는 `499`로 바뀌고, reject 흔적은 `upstream_status`나 error log 문맥에 남을 수 있음 | `499` 대신 downstream disconnect/reset flag와 deny detail이 같이 남는다 | `499` 대신 `401`과 `460` 축으로 갈라지며, target 미도달이면 `target_status_code=-`가 유지된다 |

#### Table 6. `499`/`401` split crosswalk

| 해석 질문 | Nginx | Envoy | ALB |
|-----------|-------|-------|-----|
| reject가 성공적으로 전달됐는가 | `status=401/413` + `$request_completion=OK`면 reject 응답이 끝까지 나간 쪽이다 | deny/local reply detail은 있는데 downstream disconnect flag가 없으면 전달된 쪽이다 | `elb_status_code=401/413`이고 client-close 계열 코드가 없으면 전달된 쪽이다 |
| reject decision은 있었지만 client가 먼저 떠났는가 | access는 `499`, 내부 판단 흔적은 `upstream_status=401` 또는 local error log 문맥으로 남을 수 있다 | `%RESPONSE_FLAGS%`의 downstream disconnect 계열과 `%RESPONSE_CODE_DETAILS%`의 deny/local reply reason을 함께 봐야 한다 | `499`는 없고 보통 `elb_status_code=460`이 client-abort 축을 맡는다. `401`과 `460`은 같은 사건의 다른 phase일 수 있다 |
| upstream/origin을 탔는지 edge local로 끝났는지 어떻게 가르나 | `upstream_status=-`면 edge/local, `upstream_status=401`이면 upstream/origin까지 탔을 가능성이 높다 | `%UPSTREAM_HOST%`, upstream transport/reset detail, local reply detail로 local vs upstream을 가른다 | `target_status_code=-`면 target 미도달, `target_status_code`가 채워지면 target/origin phase를 본 것이다 |

#### Table 7. Drain-vs-close observability field map

| Vendor | 우선 남겨야 할 필드 | drain / delivered 쪽 해석 | close / abort 쪽 해석 |
|--------|----------------------|---------------------------|-----------------------|
| Nginx | `$status`, `$request_length`, `$request_time`, `$request_completion`, `$upstream_status`, `$upstream_response_time`, `$sent_http_connection` | `$request_completion=OK`이고 reject status가 남으면 응답 전달과 cleanup이 끝난 쪽에 가깝다 | `$request_completion`이 비거나 `499`, `Connection: close` 쪽이면 close/abort 해석이 맞다 |
| Envoy | `%BYTES_RECEIVED%`, `%BYTES_SENT%`, `%DURATION%`, `%RESPONSE_DURATION%`, `%RESPONSE_FLAGS%`, `%RESPONSE_CODE_DETAILS%`, `%CONNECTION_TERMINATION_DETAILS%` | local reply detail은 있으나 downstream termination flag가 없으면 drain 또는 buffered-already 쪽이다 | downstream disconnect/reset flag, connection termination detail이 있으면 close/abort 쪽이다 |
| ALB | `received_bytes`, `sent_bytes`, `request_processing_time`, `target_processing_time`, `response_processing_time`, `elb_status_code`, `target_status_code`, `actions_executed`, `error_reason` | reject code와 bytes/timing이 남고 client-close 계열 code가 없으면 전달된 reject로 본다 | `460`, `400`, `000` 같은 edge-generated close/abort 성격과 timing/bytes 조합으로 추정해야 하며, 직접적인 drain flag는 없다 |

ALB는 특히 POST body 시간 분배를 조심해야 한다.

- AWS WAF가 붙은 ALB는 POST body 전송 시간을 `request_processing_time` 쪽에 더 반영한다.
- WAF가 없는 ALB는 같은 POST body 시간을 `target_processing_time` 쪽에 더 반영할 수 있다.

그래서 "target_processing_time이 길다 = target이 느리다"로 바로 읽으면 buffered upload reject를 target blame으로 잘못 번역할 수 있다.

운영용 generic schema로는 아래 다섯 축이면 충분하다.

- `body_owner` = edge-buffered | upstream-streaming
- `decision_status` = 401 | 413 | 429 | 503 ...
- `decision_source` = local-reply | upstream-app | translated-upstream-failure
- `downstream_outcome` = delivered | client-abort | unknown
- `cleanup_mode` = buffered-already | drain | close | unknown

### 7. generic category로 재분류하는 습관이 중요하다

예:

- client abort
- local timeout
- no healthy upstream
- upstream reset
- protocol mismatch
- transport close before response

이렇게 재분류하면 vendor가 달라도 공통 원인 모델로 대화할 수 있다.

## 실전 시나리오

### 시나리오 1: 팀 A는 499를 보고 app bug라 하고, 팀 B는 아니라 한다

Nginx symptom translation이 없는 상태일 수 있다.

### 시나리오 2: mesh migration 후 503이 늘었는데 app 팀은 요청을 못 봤다

Envoy local reply나 sidecar rejection을 app 503으로 오해한 패턴일 수 있다.

### 시나리오 3: ALB 502가 뜨는데 app은 200 로그를 남긴다

target selection/timeout/connection error가 user-facing code를 바꾼 것일 수 있다.

### 시나리오 4: vendor를 바꾼 뒤 에러율 대시보드가 달라 보인다

실제 장애가 아니라 표면 증상 번역 방식이 바뀐 것일 수 있다.

## 코드로 보기

### 관찰 포인트

```text
- Nginx: $status $request_length $request_time $request_completion $upstream_status $upstream_response_time $sent_http_connection
- Envoy: %RESPONSE_FLAGS% %RESPONSE_CODE_DETAILS% %UPSTREAM_TRANSPORT_FAILURE_REASON% %BYTES_RECEIVED% %BYTES_SENT% %CONNECTION_TERMINATION_DETAILS%
- ALB: elb_status_code target_status_code actions_executed error_reason received_bytes request_processing_time target_processing_time response_processing_time
- generic category remapping: body_owner / decision_source / downstream_outcome / cleanup_mode
```

### 운영 감각

```text
raw vendor symptom -> generic category -> retry / blame / mitigation
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| vendor-native triage | 세부 원인을 잘 본다 | 팀 간 공통 언어가 약하다 | 운영 심층 분석 |
| generic category remap | 협업과 비교가 쉽다 | 일부 vendor 세부 정보가 희석된다 | incident 공통 대응 |
| status-code only triage | 단순하다 | vendor 차이를 거의 못 본다 | 권장되지 않음 |
| enriched proxy logs | 원인 추적이 좋다 | 수집 비용이 늘어난다 | 운영 중요 경로 |

핵심은 vendor마다 다른 증상을 그대로 비교하지 않고 **generic failure category로 번역해서** 보는 것이다.

## 꼬리질문

> Q: 같은 502라도 Nginx와 ALB에서 의미가 같나요?
> 핵심: 아니다. vendor마다 어떤 상황을 502로 surface하는지 다를 수 있다.

> Q: 왜 499를 특별히 조심해야 하나요?
> 핵심: Nginx 계열에선 client abort 관찰 결과지, app이 499를 반환했다는 뜻이 아니기 때문이다.

> Q: vendor symptom translation이 왜 필요한가요?
> 핵심: proxy를 바꾸거나 계층이 늘어날수록 같은 원인이 다른 표면 코드로 보이기 때문이다.

## 한 줄 정리

proxy/vendor별 symptom translation table이 없으면 같은 장애도 전혀 다른 문제처럼 보이므로, raw symptom을 generic failure category로 다시 맵핑해 보는 습관이 필요하다.
