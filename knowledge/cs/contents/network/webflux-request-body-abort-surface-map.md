---
schema_version: 3
title: "WebFlux Request-Body Abort Surface Map"
concept_id: network/webflux-request-body-abort-surface-map
canonical: true
category: network
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- webflux
- request-body-abort
- reactor-netty
aliases:
- WebFlux request body abort map
- Reactor Netty AbortedException
- request.receive abort
- ServerWebInputException failed to read HTTP message
- DataBufferLimitException
- ContentTooLargeException
- WebFlux multipart truncation
- request body cancel before handler
symptoms:
- WebFlux에도 servlet ClientAbortException MultipartException dialect가 그대로 나온다고 기대한다
- transport AbortedException, codec DecodingException, framework ServerWebInputException을 같은 층으로 본다
- handler 전에 터졌는지 여부를 annotation signature와 subscribe 시점 없이 판단한다
- functional endpoint와 annotation style의 wrapper surface 차이를 놓친다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/servlet-container-abort-surface-map-tomcat-jetty-undertow
- network/network-spring-request-lifecycle-timeout-disconnect-bridge
next_docs:
- network/webflux-cancel-lag-tuning
- network/sse-webflux-streaming-cancel-after-first-byte
- spring/reactive-blocking-bridge-boundedelastic-block-traps
- spring/request-lifecycle-timeout-disconnect-cancellation-bridges
linked_paths:
- contents/network/servlet-container-abort-surface-map-tomcat-jetty-undertow.md
- contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md
- contents/network/multipart-parsing-vs-auth-reject-boundary.md
- contents/network/webflux-cancel-lag-tuning.md
- contents/network/sse-webflux-streaming-cancel-after-first-byte.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
- contents/network/fin-rst-half-close-eof-semantics.md
- contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md
- contents/spring/spring-reactive-blocking-bridge-boundedelastic-block-traps.md
confusable_with:
- network/servlet-container-abort-surface-map-tomcat-jetty-undertow
- network/webflux-cancel-lag-tuning
- network/sse-webflux-streaming-cancel-after-first-byte
- spring/reactive-blocking-bridge-boundedelastic-block-traps
forbidden_neighbors: []
expected_queries:
- "WebFlux request body abort는 Reactor Netty AbortedException부터 어떻게 surface돼?"
- "ServerWebInputException과 DecodingException, DataBufferLimitException 차이는?"
- "WebFlux에서 handler 전에 request body read가 터졌는지 어떻게 판단해?"
- "annotation WebFlux와 functional endpoint에서 body abort wrapper가 다를 수 있어?"
- "Servlet ClientAbortException과 WebFlux AbortedException surface를 비교해줘"
contextual_chunk_prefix: |
  이 문서는 WebFlux/Reactor Netty request body abort에서 AbortedException,
  IOException, DecodingException, DataBufferLimitException, ServerWebInputException,
  ContentTooLargeException surface를 연결하는 advanced bridge다.
---
# WebFlux Request-Body Abort Surface Map

> 한 줄 요약: Reactor Netty/WebFlux에서 request-read EOF/reset, truncated multipart, pre-handler cancel은 servlet container 전용 `ClientAbortException`/`MultipartException` dialect 대신 `AbortedException`/`IOException` -> `DecodingException`/`DataBufferLimitException` -> `ServerWebInputException`/`ContentTooLargeException` 계층으로 surface된다. 다만 어떤 시그니처가 body를 언제 subscribe하느냐에 따라 "handler 전에 터졌는가" 경계가 달라진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md)
> - [WebFlux Cancel-Lag Tuning](./webflux-cancel-lag-tuning.md)
> - [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [FIN, RST, Half-Close, EOF](./fin-rst-half-close-eof-semantics.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring Reactive Blocking Bridge and `boundedElastic` Traps](../spring/spring-reactive-blocking-bridge-boundedelastic-block-traps.md)

retrieval-anchor-keywords: webflux request body abort map, reactor netty abortedexception, connection has been closed, request.receive abort, reactorserverhttprequest getbody receive, request body eof webflux, request body reset webflux, serverwebinputexception failed to read http message, contenttoolargeexception, payloadtoolargeexception, getmultipartdata abort, requestpart abort before handler, part event cancel, multipartparser could not find end of body, defaultserverwebexchange cleanupmultipart, raw request body abort webflux, functional endpoint bodytomono abort, request body cancel before handler, webflux multipart truncation

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

Servlet stack에서는 container dialect가 먼저 보이지만, WebFlux stack에서는 보통 아래 세 층으로 나눠 보는 편이 정확하다.

| 층 | 대표 표면 | 뜻 |
|---|---|---|
| Reactor Netty transport | `AbortedException`, raw `IOException`, `ClosedChannelException` 계열 | socket/channel이 request body ingress 중 닫히거나 reset됐다 |
| Spring codec / parser | `DecodingException`, `DataBufferLimitException` | body는 들어왔지만 JSON/multipart parser가 EOF, truncation, limit 초과를 읽었다 |
| WebFlux invocation wrapper | `ServerWebInputException`, `ContentTooLargeException` | 위 parser error를 WebFlux가 handler contract용 예외로 번역했다 |

여기서 핵심 함정은 두 가지다.

- WebFlux에는 servlet의 `ClientAbortException`, `MultipartException`, `swallowAbortedUploads` 같은 container-specific 이름과 knob이 기본 축이 아니다
- "handler 전에 터졌다"는 사실도 stack이 아니라 **argument shape와 누가 먼저 subscribe했는가**에 따라 달라진다

| access path | user handler 진입 전 body를 실제로 읽는가 | 흔한 표면 |
|---|---|---|
| `@RequestBody Foo`, `@RequestPart MetaData`, plain `Part`/`FilePart` | 대체로 그렇다 | raw `AbortedException`/`IOException`, `ServerWebInputException`, `ContentTooLargeException` |
| `@RequestBody Mono<Foo>`, `@RequestBody Flux<PartEvent>` | 아니다. handler는 lazy publisher를 먼저 받는다 | subscribe 시점에 raw abort 또는 `ServerWebInputException` |
| `ServerWebExchange.getMultipartData()`, `ServerRequest.multipartData()` | 그렇다. caller가 body parse를 강제한다 | raw `DecodingException`, raw `DataBufferLimitException` |
| `ServerHttpRequest.getBody()` | 누가 subscribe하느냐에 달린다 | raw `AbortedException`/`IOException` |

### Retrieval Anchors

- `webflux request body abort map`
- `reactor netty abortedexception`
- `request.receive abort`
- `serverwebinputexception failed to read http message`
- `getmultipartdata abort`
- `requestpart abort before handler`
- `part event cancel`
- `contenttoolargeexception`
- `multipartparser could not find end of body`

## 깊이 들어가기

### 1. WebFlux request body는 결국 Reactor Netty `receive()`다

Spring의 `ReactorServerHttpRequest#getBody()`는 Reactor Netty `HttpServerRequest.receive()`를 그대로 감싼다.  
즉 raw request-body 경로에는 servlet container의 별도 exception dialect나 `request.getParts()` 같은 entrypoint가 없다.

- raw `Flux<DataBuffer>`를 읽으면 transport signal을 거의 그대로 본다
- request body를 아직 아무도 subscribe하지 않았다면, 그 시점엔 parser error도 없다
- 해석의 첫 질문은 "지금 본 예외가 transport error인가, codec/parser error인가"다

WebFlux request-read 문제는 container map보다 **transport -> codec -> framework wrapper** 순서로 역추적하는 편이 빠르다.

### 2. mid-body EOF/reset은 Reactor Netty에서 먼저 `AbortedException`/`IOException`로 보인다

Reactor Netty server 쪽에선 channel이 request ingress 도중 닫히면 `HttpServerOperations.onInboundClose()`가 `AbortedException("Connection has been closed")`를 만든다.  
`FluxReceive`는 `ClosedChannelException`을 `AbortedException`으로 감싸지만, 그 외 `IOException`류는 대체로 raw하게 유지한다.

실전 감각은 이렇다.

- channel inactive 기반 조기 close: `AbortedException("Connection has been closed")`
- low-level reset/broken pipe 계열: raw `IOException` 또는 `AbortedException` helper로 분류 가능한 message
- 이 단계에서는 아직 `ServerWebInputException`이 아니다

즉 request body EOF/reset이 항상 Spring wrapper 이름으로 예쁘게 정리되길 기대하면 안 된다.  
raw `AbortedException`이 보이면 "decoder가 번역하기도 전에 transport가 먼저 끊겼다"는 쪽을 먼저 본다.

### 3. WebFlux는 모든 read error를 같은 방식으로 번역하지 않는다

annotation 기반 WebFlux에서 `AbstractMessageReaderArgumentResolver`는 아래 둘만 특별 취급한다.

- `DecodingException` -> `ServerWebInputException("Failed to read HTTP message")`
- `DataBufferLimitException` -> `ContentTooLargeException`

반대로 아래는 그대로 둔다.

- `AbortedException`
- raw `IOException`
- 그 외 transport-level failure

그래서 plain `@RequestBody Foo` 기준으로는 아래처럼 읽으면 된다.

| top-level 표면 | 보통 뜻 |
|---|---|
| raw `AbortedException`/`IOException` | body read 중 transport close/reset |
| `ServerWebInputException` + cause `DecodingException` | parser가 truncation/malformed body를 읽었다 |
| `ContentTooLargeException` + cause `DataBufferLimitException` | memory/part/body size limit 초과 |

functional endpoint도 조금 다르다.

- `DefaultServerRequest.bodyToMono()` / `bodyToFlux()`는 `DecodingException`만 `ServerWebInputException`으로 바꾼다
- `DataBufferLimitException`은 annotation resolver처럼 `ContentTooLargeException`으로 감싸지지 않는다

즉 같은 body라도 annotation style과 functional style이 **wrapper surface를 완전히 같게 맞춰 주지는 않는다**.

### 4. "before handler code" 경계는 시그니처가 결정한다

WebFlux에서 가장 많이 놓치는 차이는 plain argument와 reactive wrapper argument의 경계다.

- `@RequestBody Foo`
- `@RequestPart MetaData`
- `@RequestPart Part`

이 경로는 resolver가 body read를 마쳐야 값을 만들 수 있으므로, 실패하면 user method에 진입하기 전 끊긴다.

반면 아래는 lazy publisher를 handler에 넘긴다.

- `@RequestBody Mono<Foo>`
- `@RequestBody Flux<DataBuffer>`
- `@RequestBody Flux<PartEvent>`
- `@RequestPart Mono<MetaData>`

이 경우 handler method는 먼저 시작되고, 실제 request read/parse failure는 그 publisher가 subscribe되는 시점에 보인다.

즉 같은 endpoint라도

- plain value signature면 "pre-handler abort"
- reactive wrapper signature면 "handler 내부 reactive chain에서 본 abort"

로 surface가 옮겨갈 수 있다.  
사건이 바뀐 게 아니라 **subscription boundary가 바뀐 것**이다.

### 5. multipart structural abort는 Spring multipart parser가 직접 `DecodingException`으로 만든다

WebFlux multipart는 servlet `request.getParts()`가 아니라 Spring의 `DefaultPartHttpMessageReader` / `PartEventHttpMessageReader` + `MultipartParser` 조합으로 읽는다.

이 parser는 구조적 truncation을 직접 `DecodingException`으로 만든다.

- 첫 boundary 없음 -> `Could not find first boundary`
- headers 끝 없음 -> `Could not find end of headers`
- body 끝 boundary 없음 -> `Could not find end of body`
- boundary header 없음 -> `No multipart boundary found in Content-Type`

즉 WebFlux multipart abort map의 핵심은 servlet-style `MultipartException`이 아니라 **parser가 만든 `DecodingException`과 limit exception**이다.

### 6. `@RequestPart`는 named part를 고르기 전에 전체 multipart map을 먼저 만든다

`RequestPartMethodArgumentResolver`는 먼저 `exchange.getMultipartData()`를 호출해 `MultiValueMap<String, Part>`를 만든 다음, 그 안에서 requested part를 찾는다.

이 말은 곧 다음을 뜻한다.

- `@RequestPart("meta") MetaData`는 named part decode 전에 whole-request multipart parse가 먼저 돈다
- multipart boundary truncation이나 part-count / size 문제는 controller method body 전에 터질 수 있다
- part 내부 JSON decode failure와, whole-request multipart structural failure는 서로 다른 층이다

경로를 나누면 다음과 같다.

| 사건 | 흔한 표면 |
|---|---|
| multipart 구조 자체가 깨짐 | raw `DecodingException` 또는 raw `DataBufferLimitException` from `getMultipartData()` path |
| named part는 찾았지만 part 내부 JSON/XML decode 실패 | `ServerWebInputException` + cause `DecodingException` |
| named part가 아예 없음 | `MissingRequestValueException` 계열 |

여기서 "raw"라고 한 이유는 `getMultipartData()` path가 `AbstractMessageReaderArgumentResolver.handleReadError()`를 통하지 않기 때문이다.  
즉 `@RequestPart`에선 **whole-map parse failure**와 **part payload decode failure**의 wrapper가 다를 수 있다.

### 7. multipart cleanup도 servlet과 다르게 읽어야 한다

`DefaultServerWebExchange.getMultipartData()`는 성공적으로 multipart map이 materialize됐을 때만 `multipartRead=true`를 세우고, `cleanupMultipart()`는 그때 수집된 `Part`들에 대해 `delete()`를 호출한다.

이 말은 곧:

- 성공적으로 `Part`가 만들어진 뒤 cleanup은 `cleanupMultipart()`가 담당
- parse 중간 abort, cancel, temp-file partial state cleanup은 `PartGenerator` dispose/error path가 담당

즉 WebFlux multipart cleanup은 servlet의 `cleanupMultipart(part.delete)`와 닮은 부분도 있지만, parse 도중 abort cleanup은 reader/generator state machine 쪽 책임이 더 크다.

### 8. `Flux<PartEvent>` cancel은 parse failure와 별개로 봐야 한다

`Flux<PartEvent>` 경로는 aggregated `MultiValueMap`보다 훨씬 cancel-sensitive 하다.

- `PartEventHttpMessageReader`도 구조적 truncation에는 `DecodingException`을 낸다
- 하지만 downstream consumer가 중간에 cancel하면 parser는 `onCancel`로 state를 dispose하고 upstream request read를 멈춘다
- 이때 남은 parts가 materialize되지 않는 것은 정상적인 cancellation path이지, 꼭 parse error라는 뜻은 아니다

Spring docs도 `PartEvent.content()`는 **끝까지 consume, relay, 또는 release**하라고 못 박는다.  
즉 `Flux<PartEvent>` 쪽은 `multipart abort`와 `consumer cancel`을 같은 bucket으로 섞으면 안 된다.

### 9. early reject는 servlet의 swallow/drain map보다 cancel/discard map에 가깝다

WebFilter나 HandlerFilterFunction이 body를 읽기 전에 `401/403/413`을 결정할 수 있다.  
이때 Reactor Netty 쪽 관심사는 servlet container의 `maxSwallowSize` 같은 knob이 아니라 inbound cancel/dispose다.

실전 번역:

- filter가 response를 빨리 끝내면, unread inbound는 Reactor Netty operation termination 쪽에서 discard/dispose 경로를 탄다
- body를 읽지 않은 early reject에서 봐야 할 단서는 `ClientAbortException`보다 cancel, channel inactive, raw abort signal이다
- 그래서 reactive stack에서는 "누가 unread body를 얼마나 swallow했는가"보다 "누가 먼저 subscribe/cancel했는가"가 더 중요하다

즉 servlet map이 drain/swallow cleanup 중심이라면, WebFlux map은 **subscription/cancel/discard 중심**이라고 보는 편이 맞다.

## 실전 시나리오

### 시나리오 1: edge는 `499`, controller 로그는 없고 origin에 raw `AbortedException("Connection has been closed")`만 남는다

plain `@RequestBody Foo` 또는 `request.getBody()` subscriber가 request ingress 중 transport close를 직접 본 패턴일 수 있다.  
decoder가 `DecodingException`으로 번역할 만큼 body를 다 읽지 못했기 때문에 `ServerWebInputException`도 안 보일 수 있다.

### 시나리오 2: 같은 endpoint인데 `Foo`를 `Mono<Foo>`로 바꿨더니 abort가 handler 내부 `flatMap` 체인에서 보인다

incident가 달라진 게 아니라 signature boundary가 바뀐 것이다.  
이전에는 resolver가 pre-handler로 body를 읽었고, 지금은 handler가 lazy publisher를 받은 뒤 subscribe하면서 error를 본다.

### 시나리오 3: `@RequestPart("meta") MetaData` controller는 아예 안 탔는데 cause가 `Could not find end of body`다

named part decode 전에 `exchange.getMultipartData()`가 whole-request multipart parse를 먼저 돌렸기 때문이다.  
즉 이건 part 내부 JSON decode failure가 아니라 multipart structural truncation이다.

### 시나리오 4: auth/DLP WebFilter가 `exchange.getMultipartData()`를 먼저 만지고 `401`을 반환한다

controller 미진입이어도 request body는 이미 parse를 시작했다.  
temp file, part limit, parser abort, cleanup 책임이 filter 단계까지 앞당겨진다.

### 시나리오 5: `Flux<PartEvent>` 업로드에서 첫 file chunk만 보고 consumer가 취소했다

이건 multipart parser failure가 아니라 consumer cancel이다.

- 남은 parts는 materialize되지 않을 수 있다
- unconsumed `DataBuffer` release/relay가 중요하다
- parser error가 없다고 body handling이 끝난 건 아니다

## 코드로 보기

### triage 순서

```text
1. top-level simple name이 AbortedException / IOException / DecodingException / ServerWebInputException / ContentTooLargeException 중 무엇인지 본다
2. access path가 @RequestBody plain value인지, reactive wrapper인지, @RequestPart인지, getMultipartData()인지 고정한다
3. controller 진입 전인지 후인지보다 "누가 publisher를 처음 subscribe했는가"를 먼저 확인한다
4. multipart라면 구조적 parse failure인지, named part decode failure인지, consumer cancel인지 분리한다
5. functional endpoint인지 annotation endpoint인지 확인해 DataBufferLimitException wrapper 차이를 감안한다
6. filter가 formData()/multipartData()를 먼저 읽었는지 확인한다
```

### surface map

| 보이는 표면 | 보통 어느 층인가 | 첫 해석 |
|---|---|---|
| raw `AbortedException("Connection has been closed")` | Reactor Netty transport | mid-body close, channel inactive, decoder 번역 전 abort |
| raw `IOException` with reset/broken-pipe flavor | Reactor Netty transport | transport reset or read-side I/O failure |
| `DecodingException("Could not find end of body")` | multipart parser | multipart boundary/body truncation |
| `ServerWebInputException("Failed to read HTTP message")` | WebFlux resolver wrapper | `DecodingException`을 annotation/functional body reader가 번역했다 |
| `ContentTooLargeException` | annotation resolver wrapper | `DataBufferLimitException` 기반 limit 초과 |
| raw `DataBufferLimitException` | direct exchange access or functional/raw path | multipart/body limit 초과가 wrapper 없이 올라왔다 |
| cancel only, parser error 없음 | downstream cancellation | `Flux<PartEvent>` 또는 raw body consumer가 중간에 멈췄다 |

### signature boundary 기억법

```text
plain value argument:
  body read must finish before method invocation

reactive wrapper argument:
  method gets a lazy publisher first
  body read error appears when that publisher is subscribed

exchange.getMultipartData()/multipartData():
  caller itself becomes the pre-handler body reader
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| plain `@RequestBody Foo` / plain `@RequestPart` | fail-fast, pre-handler classification이 선명함 | large/streaming body에 덜 유연함 | body를 다 읽은 뒤 business logic을 시작하는 API |
| `Mono<Foo>` / `Flux<PartEvent>` | backpressure와 cancel 제어가 명시적 | failure 위치가 handler 내부로 이동해 triage가 어려워짐 | streaming upload, relay, progressive validation |
| `getMultipartData()` aggregate | 다루기 쉬운 `MultiValueMap` | whole-request parse와 temp-file lifecycle을 앞당김 | 작은 multipart를 한 번에 검증/매핑할 때 |
| `Flux<PartEvent>` streaming | part-by-part 처리와 빠른 stop에 유리 | release/cancel hygiene를 직접 챙겨야 함 | large upload, pass-through relay, partial processing |

## 꼬리질문

- `@RequestBody Foo`와 `@RequestBody Mono<Foo>`는 같은 abort를 왜 다른 위치에서 보나?
- `@RequestPart`와 `Flux<PartEvent>`는 multipart truncation과 consumer cancel을 어떻게 구분하나?
- functional endpoint에서 `DataBufferLimitException`과 annotation endpoint의 `ContentTooLargeException` 차이를 대시보드에서 어떻게 통일해 볼까?

## 한 줄 정리

WebFlux request-body abort를 읽을 때는 container dialect를 찾기보다 `request.receive()` transport signal, codec/parser가 만든 `DecodingException`, 그리고 resolver가 붙인 `ServerWebInputException`/`ContentTooLargeException`의 세 층을 분리해야 한다. 그리고 "handler 전에 터졌다"는 말도 stack 종류보다 **plain 값인지 lazy publisher인지, 누가 먼저 subscribe했는지**로 다시 정의해야 한다.
