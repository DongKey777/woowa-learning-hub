---
schema_version: 3
title: "Gateway Buffering vs Spring Early Reject"
concept_id: network/gateway-buffering-vs-spring-early-reject
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- gateway-buffering-upload
- spring-security-early-reject
- request-body-observability
aliases:
- gateway buffering vs spring early reject
- proxy_request_buffering spring upload
- AuthenticationEntryPoint upload 401
- unread body observability
- request body bytes received vs consumed
- upload early reject bridge
symptoms:
- Spring Security는 3ms 만에 401을 만들었는데 edge에서는 2GB upload 후 401로 보여 서로 모순이라고 생각한다
- proxy_request_buffering on/off가 Spring early reject의 wire-level 절약 여부를 바꾸는 점을 놓친다
- request bytes received와 app consumed body를 같은 지표로 해석한다
- 499 after spring reject를 client disconnect와 unread body cleanup 없이 읽는다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- network/expect-100-continue-proxy-request-buffering
- network/http-request-body-drain-early-reject-keepalive-reuse
next_docs:
- network/proxy-to-container-upload-cleanup-matrix
- network/multipart-parsing-vs-auth-reject-boundary
- network/network-spring-request-lifecycle-timeout-disconnect-bridge
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
- spring/security-exceptiontranslation-entrypoint-accessdeniedhandler
linked_paths:
- contents/network/expect-100-continue-proxy-request-buffering.md
- contents/network/http-request-body-drain-early-reject-keepalive-reuse.md
- contents/network/proxy-to-container-upload-cleanup-matrix.md
- contents/network/multipart-parsing-vs-auth-reject-boundary.md
- contents/network/api-gateway-auth-rate-limit-chain.md
- contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
- contents/network/servlet-container-abort-surface-map-tomcat-jetty-undertow.md
- contents/spring/spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md
- contents/spring/spring-mvc-request-lifecycle.md
confusable_with:
- network/expect-100-continue-proxy-request-buffering
- network/http-request-body-drain-early-reject-keepalive-reuse
- network/multipart-parsing-vs-auth-reject-boundary
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
- network/proxy-to-container-upload-cleanup-matrix
forbidden_neighbors: []
expected_queries:
- "Spring Security는 빠르게 401을 만들었는데 gateway는 긴 upload 후 401로 보이는 이유는?"
- "proxy_request_buffering on이면 Spring early reject가 upload 절약으로 이어지지 않을 수 있어?"
- "request body bytes received와 consumed body를 업로드 early reject에서 어떻게 구분해?"
- "Expect 100-continue와 gateway buffering과 AuthenticationEntryPoint를 한 체인으로 설명해줘"
- "499 after Spring reject가 보이면 unread body cleanup과 client disconnect를 어떻게 봐?"
contextual_chunk_prefix: |
  이 문서는 large upload path에서 gateway/proxy buffering, Expect:
  100-continue, Spring Security early reject, AuthenticationEntryPoint,
  unread body drain/close, edge access log bytes를 함께 보는 advanced playbook이다.
---
# Gateway Buffering vs Spring Early Reject

> 한 줄 요약: 업로드 경로에서 `Expect: 100-continue`, gateway request buffering, Spring Security/filter early reject, unread-body cleanup는 하나의 체인이다. 어느 홉이 body를 실제로 읽었는지 분리해 관측하지 않으면 edge의 긴 upload와 Spring의 빠른 `401/403`을 동시에 보고도 원인을 거꾸로 해석하게 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)
> - [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
> - [Proxy-to-Container Upload Cleanup Matrix](./proxy-to-container-upload-cleanup-matrix.md)
> - [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md)
> - [API Gateway Auth Rate Limit Chain](./api-gateway-auth-rate-limit-chain.md)
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
> - [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](../spring/spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
> - [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)

retrieval-anchor-keywords: gateway buffering vs spring early reject, Expect 100-continue spring security, proxy_request_buffering spring upload, unread body observability, upload early reject bridge, request body bytes received vs consumed, AuthenticationEntryPoint upload 401, filter chain early reject body drain, gateway 401 after full upload, 499 after spring reject, unread request body metrics, upload path bridge

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

업로드 early reject를 볼 때는 상태 코드보다 먼저 **누가 언제 body를 읽었는지**를 고정해야 한다.

같은 요청도 서로 다른 팀은 이렇게 본다.

- edge 팀: upload 12초, `401`, request bytes 2GB, keep-alive 미재사용
- Spring 팀: Security filter에서 3ms 만에 `AuthenticationEntryPoint` 호출, controller 미진입

둘 다 사실일 수 있다.  
핵심은 Spring의 "빠른 reject"가 **애플리케이션 내부 판단 시점**이고, gateway buffering 여부는 **네트워크 상 실제 upload 낭비 시점**을 결정한다는 점이다.

### Retrieval Anchors

- `gateway buffering vs spring early reject`
- `Expect 100-continue spring security`
- `proxy_request_buffering spring upload`
- `unread body observability`
- `AuthenticationEntryPoint upload 401`
- `request body bytes received vs consumed`
- `499 after spring reject`

## 깊이 들어가기

### 1. 업로드 경로에는 최소 네 개의 시계가 있다

업로드 요청 하나를 보면 시계가 네 개로 분리된다.

1. client가 body를 실제로 보내는 시계
2. gateway/proxy가 body를 버퍼링하거나 upstream으로 흘리는 시계
3. Spring Security/filter가 reject를 결정하는 시계
4. unread body를 drain하거나 connection을 close하는 cleanup 시계

이 네 개를 한 값으로 뭉개면 오해가 생긴다.

- Spring 로그는 "빠른 401"
- edge access log는 "긴 upload 후 401"
- client는 "전송 다 했는데 거절당함"

이 셋이 동시에 성립할 수 있다.

### 2. `Expect: 100-continue`는 reject 위치를 앞당길 수 있지만, ownership을 바꾸진 않는다

`Expect: 100-continue`가 있으면 client는 header만 먼저 보내고 본문 전송을 잠깐 미룰 수 있다.

하지만 실제 효과는 누가 이 handshake를 끝까지 존중하느냐에 달려 있다.

- gateway가 header만 보고 `401/403/413/429`를 돌리면 upload 낭비가 거의 없다
- gateway가 `Expect`를 무시하거나 짧은 대기 후 client가 body를 그냥 보내면 낭비가 다시 생긴다
- gateway가 body를 버퍼링한 뒤에만 upstream으로 넘기면 Spring의 빠른 reject는 wire-level 절약으로 이어지지 않는다

즉 `Expect: 100-continue`는 "문법 지원"보다 **reject ownership을 누구에게 둘 것인가**의 문제다.

### 3. Spring Security/filter early reject는 MVC보다 앞이지만, edge보다 앞은 아니다

Spring Security의 `ExceptionTranslationFilter`와 custom auth filter는 controller보다 앞에서 `401/403`을 만들 수 있다.

그래서 다음은 맞다.

- `@RequestBody` binding이나 controller 진입 전에 reject할 수 있다
- `AuthenticationEntryPoint`가 빠르게 응답을 만들 수 있다
- app 내부 CPU/DB 낭비를 줄일 수 있다

하지만 다음은 별개다.

- client upload를 얼마나 줄였는가
- gateway가 이미 body를 읽었는가
- unread body cleanup을 누가 맡았는가

특히 `proxy_request_buffering on`이면 Spring filter chain이 아무리 빨라도 edge 관점에서는 "body를 다 받은 뒤 reject"가 될 수 있다.

### 4. 가장 자주 헷갈리는 케이스는 "Spring은 early, 네트워크는 late"다

다음 흐름을 보자.

```text
client
-> gateway(headers 수신)
-> gateway(body 2GB 전부 buffering)
-> upstream Spring Security filter
-> AuthenticationEntryPoint 401
```

이 경우:

- Spring은 controller 전에 막았으니 early reject라고 느낀다
- 그러나 네트워크 관점에서는 body가 이미 다 들어왔으니 late reject다
- unread body cleanup은 gateway가 이미 끝냈을 수 있어 app에는 거의 안 보인다

즉 "Spring early reject"와 "upload path early reject"는 같은 말이 아니다.

### 5. buffering off에서야 Spring reject와 unread body가 직접 만난다

`proxy_request_buffering off`라면 body가 upstream으로 바로 흐를 수 있다.

이때 Spring filter chain이 header만 보고 reject하면 비로소 upload 절약 여지가 생긴다.  
하지만 client가 이미 body를 보내기 시작했다면 남은 문제가 바로 unread body다.

- proxy가 남은 body를 대신 drain할 수 있다
- servlet container가 읽지 않은 바이트를 정리할 수 있다
- drain 대신 connection을 닫아 keep-alive 재사용을 포기할 수 있다

그래서 buffering off는 "Spring이 빨리 막는다"로 끝나지 않고, **reject 후 byte cleanup 정책**까지 포함해야 한다.

### 6. 관측 포인트를 `bytes received`와 `bytes consumed`로 분리해야 한다

upload 경로에서 가장 중요한 분리는 아래 둘이다.

- `request_body_bytes_received_edge`: edge/gateway가 client로부터 받은 바이트
- `request_body_bytes_consumed_app`: Spring app 또는 container가 실제로 읽은 바이트

이 둘을 분리하지 않으면 다음을 설명할 수 없다.

- edge는 2GB를 받았는데 app은 0B만 읽음
- app은 401을 5ms에 만들었는데 connection occupancy는 12초
- controller 미진입인데 499와 broken pipe가 같이 뜸

추가로 아래 축도 같이 남겨야 한다.

- `expect_continue_present`
- `continue_sent_by` = gateway | origin | none
- `early_reject_stage` = gateway | security-filter | servlet-filter | mvc | controller
- `unread_body_cleanup` = buffered-already | drain | close | unknown
- `unread_body_drain_ms`
- `response_committed_before_body_end`
- `connection_reused`

### 7. edge status와 Spring status는 phase가 다르면 동시에 참일 수 있다

대표적인 조합:

| edge 관측 | Spring 관측 | 실제 의미 |
|---|---|---|
| 긴 `401`, upload bytes 큼 | Security filter 3ms `401` | gateway가 먼저 body를 읽고 Spring은 나중에 빠르게 거절 |
| `499` | `AuthenticationEntryPoint` 호출 흔적 있음 | reject 후 client가 업로드를 멈추거나 drain 중 이탈 |
| `413` at gateway | Spring 로그 없음 | size limit가 app 이전 홉에서 끝남 |
| `200` 또는 handler success | edge `499` / broken pipe | first byte 이후 disconnect, reject 문제가 아니라 late write 문제 |

이때 한쪽 로그만 보면 blame이 틀어진다.

### 8. 가장 실용적인 운영 질문은 "어디서 막을지"보다 "어디까지 읽은 뒤 막는지"다

업로드 API에서 진짜로 정해야 할 것은 다음이다.

- auth/quota/ACL을 gateway에서 끝낼지, Spring Security에서 끝낼지
- `Expect: 100-continue`를 end-to-end로 살릴지
- buffering을 endpoint별로 끌지 켤지
- reject 후 남은 body를 drain할지 close할지
- edge와 app에 어떤 phase marker를 찍을지

정답은 하나가 아니다.  
다만 "Spring filter에서 막으니 early reject" 같은 표현은 phase를 숨겨서 운영 판단을 망친다.

## 실전 시나리오

### 시나리오 1: 2GB 업로드가 끝난 뒤 401이 오는데, Spring은 controller 미진입이다

우선 의심할 것:

- gateway request buffering on
- auth 판단이 gateway가 아니라 Spring Security에 있음
- edge는 body 전부 수신 후 upstream 전달

이 경우 app 튜닝보다 **reject 위치를 gateway 쪽으로 올릴지**, 아니면 direct upload/presigned upload로 구조를 바꿀지 먼저 검토해야 한다.

### 시나리오 2: `Expect: 100-continue`를 넣었는데도 업로드 낭비가 줄지 않는다

원인 후보:

- gateway가 `Expect`를 무시하거나 upstream에 전달하지 않음
- client library가 짧게 기다리다 body를 그냥 전송
- Spring Security reject는 빠르지만 buffering on이라 wire savings 없음

즉 `Expect` 헤더 존재만으로는 충분하지 않고, **누가 final reject를 먼저 만들었는지**를 봐야 한다.

### 시나리오 3: Spring은 401, edge는 499와 긴 request time

가능한 해석:

- Spring filter가 reject 응답을 만들었다
- client는 이미 body를 보내는 중이었다
- proxy/container가 unread body를 정리하는 동안 client가 연결을 끊었다

이때 499를 auth bug로 보기보다 unread-body cleanup과 client upload 동작을 같이 봐야 한다.

### 시나리오 4: controller latency는 낮은데 ingress 대역폭과 connection occupancy가 높다

대개 다음이 숨어 있다.

- app은 body를 거의 읽지 않음
- gateway가 buffering으로 upload burden을 떠안음
- reject는 Spring에서 하지만 비용은 edge가 냄

즉 app APM만 보고 "문제없다"고 결론 내리면 틀린다.

## 코드로 보기

### 업로드 path phase map

```text
1. headers received at edge
2. Expect present? continue sent by whom?
3. body bytes received at edge
4. body bytes forwarded upstream
5. Spring security/filter reject decided
6. response committed
7. unread body cleanup: buffered-already | drain | close
8. client disconnect or request complete
9. connection reused or dropped
```

### Spring filter에서 남길 최소 로그 필드

```text
request_id=...
path=/upload
expect_continue=true|false
early_reject_stage=security-filter
decision_status=401
controller_entered=false
request_body_bytes_consumed_app=0
response_committed=false|true
```

이 로그만으로는 충분하지 않다.  
반드시 edge 측 로그와 같은 `request_id`로 아래 값이 이어져야 한다.

```text
request_id=...
request_body_bytes_received_edge=2147483648
request_body_bytes_forwarded_upstream=16384
continue_sent_by=gateway|origin|none
unread_body_cleanup=drain|close|buffered-already
unread_body_drain_ms=...
connection_reused=true|false
edge_status=401|499|413
```

### 판단용 체크리스트

```text
- reject를 누가 만들었는가: gateway or Spring?
- client는 body를 실제로 얼마나 보냈는가?
- gateway는 body를 얼마나 받았고 얼마나 upstream에 넘겼는가?
- Spring은 body를 한 바이트라도 읽었는가?
- reject 후 unread body는 drain했는가 close했는가?
- edge status와 app status가 서로 다른 phase를 말하는가?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| gateway에서 auth + buffering on | app 보호가 쉽고 구현이 단순하다 | upload 낭비를 완전히 줄이진 못할 수 있다 | 일반 파일 업로드, app 보호 우선 |
| gateway에서 auth + `Expect` 적극 활용 | body 낭비를 가장 잘 줄인다 | client/proxy 호환성과 운영 설정이 까다롭다 | 매우 큰 업로드, 명확한 헤더 기반 auth |
| buffering off + Spring Security early reject | app 판단을 빠르게 반영할 수 있다 | unread body drain/close와 backpressure를 app 체인이 더 직접 맞는다 | header-only auth, low-latency reject가 중요할 때 |
| Spring/controller 쪽 늦은 reject | 구현이 단순해 보인다 | body parsing 이후 거절로 upload 비용과 혼선이 커진다 | 작은 JSON 요청 정도 |
| direct upload / presigned upload | app과 gateway의 upload 부담을 줄인다 | 제어 평면이 분리되어 설계가 복잡하다 | 매우 큰 object upload |

핵심은 "누가 status를 만들었는가"보다 **누가 body 비용을 부담했는가**를 같이 보는 것이다.

## 꼬리질문

> Q: Spring Security가 controller 전에 막았는데 왜 upload는 이미 끝난 것처럼 보이나요?
> 핵심: controller 전과 network ingress 전은 다르다. gateway buffering이 body를 이미 다 읽었을 수 있다.

> Q: `Expect: 100-continue`를 쓰면 unread body 문제는 사라지나요?
> 핵심: 줄어들 수는 있지만 client/proxy가 body를 이미 보내기 시작하면 reject 후 drain 또는 close 결정은 여전히 필요하다.

> Q: 어떤 지표 하나를 먼저 만들면 좋나요?
> 핵심: `request_body_bytes_received_edge`와 `request_body_bytes_consumed_app`를 같은 request id로 분리해 남기는 것이 가장 가치가 크다.

## 한 줄 정리

업로드 early reject의 진짜 쟁점은 Spring이 빨리 `401/403`을 냈는지가 아니라, gateway buffering과 `Expect: 100-continue` 아래에서 **누가 body를 읽고 누가 unread body를 정리했는지**를 같은 요청 기준으로 관측했는가다.
