---
schema_version: 3
title: "Network, Spring Request Lifecycle, Timeout, Disconnect Bridge"
concept_id: network/network-spring-request-lifecycle-timeout-disconnect-bridge
canonical: true
category: network
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- spring-lifecycle
- disconnect-attribution
- timeout-bridge
aliases:
- Spring request lifecycle bridge
- client disconnect Spring MVC
- 499 to Spring mapping
- late write failure Spring
- response commit timing
- servlet async timeout
- reactive cancellation
- Spring early reject body drain
symptoms:
- edge 499와 Spring ClientAbortException을 일대일로 바로 매핑하려 한다
- first byte 전 timeout과 response commit 후 broken pipe를 같은 처리 경로로 본다
- early reject 후 unread request body cleanup ownership을 놓친다
- reactive cancel signal이 producer 작업을 즉시 멈춘다고 가정한다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
- spring/mvc-request-lifecycle
next_docs:
- network/servlet-container-abort-surface-map-tomcat-jetty-undertow
- network/sse-webflux-streaming-cancel-after-first-byte
- spring/request-lifecycle-timeout-disconnect-cancellation-bridges
- network/proxy-local-reply-vs-upstream-error-attribution
linked_paths:
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
- contents/network/servlet-container-abort-surface-map-tomcat-jetty-undertow.md
- contents/network/webflux-request-body-abort-surface-map.md
- contents/network/container-specific-disconnect-logging-recipes-spring-boot.md
- contents/network/http-request-body-drain-early-reject-keepalive-reuse.md
- contents/network/gateway-buffering-vs-spring-early-reject.md
- contents/network/multipart-parsing-vs-auth-reject-boundary.md
- contents/network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md
- contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md
- contents/network/sse-webflux-streaming-cancel-after-first-byte.md
- contents/spring/spring-mvc-request-lifecycle.md
- contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md
- contents/network/proxy-local-reply-vs-upstream-error-attribution.md
confusable_with:
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
- network/servlet-container-abort-surface-map-tomcat-jetty-undertow
- network/sse-webflux-streaming-cancel-after-first-byte
- spring/request-lifecycle-timeout-disconnect-cancellation-bridges
forbidden_neighbors: []
expected_queries:
- "edge 499가 Spring MVC 안에서는 어떤 lifecycle 표면으로 보일 수 있어?"
- "first byte 전 timeout과 response commit 후 broken pipe는 어떻게 달라?"
- "Spring early reject 뒤 남은 request body drain ownership을 어떻게 봐?"
- "WebFlux cancellation이 producer stop까지 늦게 전파되는 이유는?"
- "network timeout disconnect와 Spring servlet async timeout을 한 timeline으로 연결해줘"
contextual_chunk_prefix: |
  이 문서는 edge 499/timeout/late write failure와 Spring MVC servlet dispatch,
  async timeout, response commit, WebFlux cancellation, request body drain을
  연결하는 advanced bridge다.
---
# Network, Spring Request Lifecycle, Timeout, Disconnect Bridge

> 한 줄 요약: 네트워크에서 보이는 upload early reject, `499`, timeout, first byte 지연, late write failure는 Spring 안에 들어오면 servlet dispatch, unread body cleanup, async request, response commit, reactive cancellation 같은 다른 표면으로 바뀐다. 둘을 이어 보지 않으면 같은 장애를 두 팀이 다르게 설명하게 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
> - [WebFlux Request-Body Abort Surface Map](./webflux-request-body-abort-surface-map.md)
> - [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
> - [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
> - [Spring `DisconnectedClientHelper` Breadcrumb Wiring: MVC Download, SSE, Async Late Write](./spring-disconnectedclienthelper-breadcrumb-wiring-mvc-download-sse-async-late-write.md)
> - [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
> - [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)
> - [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
> - [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
> - [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
> - [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](../spring/spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../spring/spring-mvc-async-deferredresult-callable-dispatch.md)
> - [Spring Reactive Blocking Bridge and `boundedElastic` Traps](../spring/spring-reactive-blocking-bridge-boundedelastic-block-traps.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring WebClient Connection Pool and Timeout Tuning](../spring/spring-webclient-connection-pool-timeout-tuning.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
> - [Service Mesh Local Reply, Timeout, Reset Attribution](./service-mesh-local-reply-timeout-reset-attribution.md)
> - [Connection Pool Starvation, Stale Idle Reuse, Debugging](./connection-pool-starvation-stale-idle-reuse-debugging.md)

retrieval-anchor-keywords: Spring request lifecycle bridge, client disconnect spring mvc, client closed request spring, response commit timing, servlet async timeout, reactive cancellation, 499 to Spring mapping, late write failure spring, first byte delay spring, mvc async dispatch timeout, webflux cancel signal, spring early reject body drain, request body abort spring, 499 upload cancel spring, response committed exception spring, broken pipe after commit spring, service mesh local reply, connection pool wait, reactor netty pending acquire, servlet container abort surface map, spring boot disconnect logging, disconnectedclienthelper, disconnect breadcrumb code example, mvc download disconnect breadcrumb, sse disconnect breadcrumb, async late write breadcrumb, tomcat clientabortexception spring, jetty eofexception spring, undertow broken pipe spring, SSE disconnect spring, WebFlux cancel lag, partial flush failure, gateway buffering spring upload

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

같은 사건도 계층마다 다른 이름으로 보인다.

- edge: `499`, `client closed request`, `504`, timeout, first byte delay
- transport: `ECONNRESET`, `EPIPE`, write blocked
- Spring filter/security: controller 도달 전 early reject, unread body cleanup
- Spring MVC: async timeout, error dispatch, committed response 이후 예외
- WebFlux/Reactor: cancel signal, downstream disposal, backpressure

이걸 하나의 lifecycle로 이어 봐야 attribution이 맞는다.
특히 **request body를 다 읽기 전 거절한 경우**와 **response commit 후 늦게 실패한 경우**는 같은 disconnect라도 완전히 다른 경로다.

### Retrieval Anchors

- `Spring request lifecycle bridge`
- `client disconnect spring mvc`
- `client closed request spring`
- `response commit timing`
- `servlet async timeout`
- `reactive cancellation`
- `499 to Spring mapping`
- `late write failure spring`
- `first byte delay spring`
- `spring early reject body drain`
- `request body abort spring`
- `499 upload cancel spring`
- `response committed exception spring`
- `broken pipe after commit spring`

## 깊이 들어가기

### 1. 먼저 요청이 어느 phase에서 끊겼는지 고정해야 한다

| phase | network 표면 | Spring 표면 | 바로 확인할 질문 |
|-------|--------------|-------------|------------------|
| request body ingress | slow upload, `499`, `413`, downstream close | filter/security early reject, body read abort | proxy buffering이 body를 대신 읽었는가, unread body를 drain했는가 |
| handler 실행 중, 아직 미커밋 | TTFB 증가, local `504`, no first byte | controller/filter/converter/exception resolver 지연 | first byte 전에 시간이 어디서 쓰였는가 |
| async handoff 이후 | edge `504`/`499`, app 작업 지속 | `DeferredResult`/`Callable` timeout, late complete | network timeout과 Spring async timeout 중 누가 먼저 끝났는가 |
| response commit 이후 write | partial body, `broken pipe`, `EPIPE` | committed response 이후 `IOException`, flush 실패 | header/first byte가 이미 나갔는가 |
| reactive stream cancel 이후 | downstream close, stream reset | subscriber cancel, disposal, backpressure | cancel 이후에도 block/buffer가 남아 있는가 |

같은 `499`라도 upload 중 disconnect인지, async timeout 뒤 useless work인지, commit 후 late write인지에 따라 해석이 달라진다.

### 2. first byte 전과 response commit 후는 대응 방식이 다르다

Spring 입장에서 중요한 경계:

- 아직 response가 commit되지 않음
- header/first byte가 이미 나감

네트워크 관점에서도 다르다.

- first byte 전 문제: timeout/local reply/error response로 바꾸기 쉽다
- commit 후 문제: status 변경이 어려워 late write failure, broken pipe로 보이기 쉽다

특히 commit 이후에는 `ExceptionResolver`나 에러 핸들러가 개입하더라도 이미 내려간 status/code를 되돌리기 어렵다.
그래서 TTFB 지연과 TTLB/write failure는 Spring 안에서도 다른 코드 경로를 탄다.

### 3. request body read 중 early reject는 app 판단과 wire cleanup이 따로 논다

Spring Security, filter, interceptor, gateway 앞단은 controller에 도달하기 전에도 `401`, `403`, `413`, `429` 같은 응답을 빠르게 결정할 수 있다.

하지만 client가 아직 body를 업로드 중이면 별도의 문제가 남는다.

- proxy나 container가 남은 body를 drain할 수 있다
- drain 대신 connection을 닫아 keep-alive 재사용을 포기할 수 있다
- buffering이 켜져 있으면 Spring은 slow upload를 거의 못 보고 proxy만 긴 업로드를 본다

즉 Spring 로그에 `401`이나 `413`이 보여도 edge에서는:

- upload 중 disconnect라 `499`
- early reject 뒤 body drain 때문에 긴 connection occupancy
- close 정책 때문에 재사용 없는 짧은 연결

같은 다른 표면이 남을 수 있다.  
그래서 early reject는 "controller를 안 탔다"로 끝나는 문제가 아니라, **남은 body를 누가 어떻게 정리했는가**까지 같이 봐야 한다.

### 4. `499`는 Spring 예외 이름으로 바로 매핑되지 않는다

edge에서 client가 먼저 끊어도 Spring app 안에서는:

- filter/security early reject 뒤 upload abort
- request body read 중 abort
- response write 중 `IOException`
- async dispatch 중 timeout/cancel race

처럼 다양한 표면으로 나온다.

즉 `499 = Spring의 어떤 예외 하나`가 아니라, **요청 lifecycle 어느 지점에서 연결이 끊겼는가**를 먼저 봐야 한다.
그래서 edge `499`와 Spring `401` 또는 Spring `200`이 동시에 참일 수도 있다.

여기에 servlet container 차이도 얹힌다.

- Tomcat은 `ClientAbortException`처럼 이름이 선명한 편이다
- Jetty는 `EofException`과 quiet logging으로 더 조용히 보인다
- Undertow는 plain `IOException`, `Stream is closed`, committed-state 예외처럼 메시지/상태로 흩어진다

즉 같은 edge `499`라도 Spring stack trace의 모양은 embedded container에 따라 달라진다.  
container별 예외 dialect는 [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)에서 별도로 본다.

### 5. MVC async는 network timeout과 app timeout이 어긋나기 쉽다

예:

- gateway timeout 800ms
- servlet async timeout 1500ms
- controller는 `DeferredResult`로 계속 일함

이 경우:

- edge는 이미 504/499
- Spring은 아직 작업 중
- 완료 시점에는 late write failure나 useless work가 생김

그래서 network timeout budget과 Spring async timeout을 같이 설계해야 한다.
async completion callback에서 이미 disconnect된 응답에 write하려 하면, app 팀은 "정상 completion"을 남기고 edge는 timeout/abort를 남기는 식으로 시계가 갈라진다.

### 6. WebFlux는 cancel이 더 빨리 보이지만 block이 섞이면 또 다르다

reactive stack에서는 downstream cancel 신호가 비교적 명시적이다.

- subscriber cancel
- operator chain disposal
- backpressure signal

하지만 block이 끼면:

- cancel을 늦게 감지
- boundedElastic queue 안에서 계속 일함
- 네트워크 disconnect와 실제 작업 중단 시점이 벌어짐

즉 reactive라고 해서 자동으로 zombie work가 사라지진 않는다.
특히 `Mono.fromCallable`, blocking JDBC bridge, 큰 buffer 조합은 cancel이 왔어도 이미 예약된 일을 끝까지 밀어 넣기 쉽다.

### 7. response commit 직전과 직후에는 late write 의미가 달라진다

Spring 안에서 first byte 전 지연은 다음에서도 생긴다.

- `HttpMessageConverter` serialization
- compression filter
- `ResponseBodyAdvice`
- exception resolver chain

그래서 app 코드가 짧아도 TTFB는 길 수 있다.
반대로 first byte가 나간 뒤에는 비즈니스 로직이 성공했어도:

- chunk flush 중 `IOException`
- 마지막 byte 직전 reset
- 이미 떠난 caller에 대한 useless serialization

이 late write failure로 남을 수 있다.

즉 "handler가 값을 반환했다"와 "네트워크로 응답을 끝까지 전달했다"는 같은 사건이 아니다.

### 8. observability는 network/span + Spring dispatch 경계를 같이 남겨야 한다

유용한 축:

- request received
- request body first byte / last byte
- early reject decision
- unread body drain complete or connection close
- handler selected
- async started
- first byte committed
- last application byte attempted
- response completed
- client disconnect observed
- cancel propagated to worker / downstream

이걸 안 남기면 "Spring이 느리다"와 "edge가 먼저 끊었다"를 구분하기 어렵다.
특히 early reject와 late write는 **status code만으로는 phase가 안 드러나기 때문에** phase marker가 필요하다.

## 실전 시나리오

### 시나리오 1: upload는 아직 진행 중인데 Spring filter는 이미 `401`/`413`을 냈다

proxy buffering, unread body drain, close 정책에 따라 edge는 `499`, 긴 request time, keep-alive 미재사용으로 보일 수 있다.

### 시나리오 2: edge는 499, Spring은 200 로그

async request나 long serialization이 끝난 뒤 이미 끊긴 연결에 write했을 수 있다.

### 시나리오 3: MVC async를 썼는데 timeout 뒤에도 worker가 계속 돈다

network timeout과 servlet async timeout, downstream cancellation 전파가 안 맞는 패턴일 수 있다.

### 시나리오 4: WebFlux는 cancel이 빠를 줄 알았는데 CPU가 계속 오른다

reactive chain 안에 block/buffer/bridge가 섞여 cancel이 늦게 반영된 패턴일 수 있다.

### 시나리오 5: app 팀은 "response는 빨리 만들었다"고 하는데 edge는 TTFB가 늦다

Spring serialization / advice / compression / first-byte commit 직전 지연일 수 있다.

### 시나리오 6: app은 성공 completion을 남겼는데 운영은 `broken pipe`만 본다

response가 이미 commit된 뒤 caller가 떠나 flush 단계에서 late write failure가 난 패턴일 수 있다.

## 코드로 보기

### Bridge 체크리스트

```text
- edge request start / upstream connect / first byte / total time
- request body first byte / last byte
- early reject 응답 시각과 unread body drain or close 여부
- edge timeout / 499 시각
- Spring handler start / async start / async complete
- response commit 시각
- last application write attempt 시각
- client disconnect 감지 시각
- late write IOException / EPIPE occurrence
- cancel signal received -> actual work stopped latency
```

### 증상별 첫 분기

| 보이는 증상 | 우선 의심할 phase | 첫 확인 포인트 |
|------------|-------------------|----------------|
| edge `499`, Spring `401`/`413` | upload 중 early reject | body를 누가 drain했는가, buffering이 켜져 있었는가 |
| edge `504`, Spring async complete | async timeout mismatch | gateway timeout과 servlet async timeout 순서가 무엇인가 |
| app `200`/success log 뒤 `broken pipe` | commit 후 late write | first byte가 언제 나갔고 어느 flush에서 실패했는가 |
| WebFlux cancel 후에도 CPU 유지 | cancel 이후 blocking work 지속 | 어떤 bridge/buffer가 cancel을 늦추는가 |
| TTFB만 느리고 handler 시간은 짧음 | pre-commit serialization path | converter, advice, compression 중 어디서 멈췄는가 |

### 운영 감각

```text
network symptom
 -> request lifecycle phase
 -> spring surface (mvc/reactive)
 -> cancellation / timeout / response commit 대응

if edge says 499:
  ask "before commit or after commit?"
  if before commit:
    inspect upload / early reject / async timeout path
  else:
    inspect late write / flush failure path
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| fail-fast early reject | 업로드 낭비와 app 실행을 줄인다 | unread body drain/close를 설계하지 않으면 keep-alive와 관측이 꼬인다 | auth, quota, payload guard |
| network-only triage | edge 원인 파악이 빠르다 | app lifecycle과 어긋나기 쉽다 | front-door 장애 |
| app-only triage | 코드 경로를 보기 쉽다 | 499/local reply/late write를 놓치기 쉽다 | handler 중심 장애 |
| bridge observability | attribution이 가장 정확하다 | 계측 포인트 설계가 복잡하다 | 운영 성숙 팀 |
| unified timeout design | zombie work를 줄인다 | 팀 간 합의가 필요하다 | async/streaming 경로 |

핵심은 network symptom과 Spring lifecycle을 따로 보지 않고 **같은 요청의 다른 표면**으로 연결해 보는 것이다.

## 꼬리질문

> Q: edge 499를 Spring 예외 하나로 바로 매핑할 수 있나요?
> 핵심: 아니다. body read, async timeout, response write 시점에 따라 표면이 달라진다.

> Q: Spring filter에서 401/413을 빨리 내려도 왜 edge에 499가 같이 보일 수 있나요?
> 핵심: client가 아직 body를 올리는 중이거나 proxy가 drain/close를 수행하는 동안 disconnect가 관찰될 수 있기 때문이다.

> Q: reactive면 cancellation이 자동으로 해결되나요?
> 핵심: 아니다. block/bridge/buffer가 끼면 cancel이 늦어질 수 있다.

> Q: first byte 전 지연은 app 코드만 보면 되나요?
> 핵심: 아니다. serialization, advice, compression, response commit 직전 지연도 포함될 수 있다.

> Q: app은 200 completion을 남겼는데 broken pipe가 뜨면 성공인가요?
> 핵심: 비즈니스 계산은 끝났을 수 있지만, commit 이후 네트워크 전달은 실패했을 수 있다.

## 한 줄 정리

network와 Spring request lifecycle을 bridge해서 봐야 early reject의 unread body 정리, 499/disconnect, async timeout mismatch, commit 후 late write failure가 같은 요청의 어느 단계에서 생긴 일인지 정확히 설명할 수 있다.
