# Spring MVC `Flux` Adaptation: `application/json` vs NDJSON and SSE

> 한 줄 요약: Spring MVC에서 `Flux<?>` 같은 multi-value reactive return은 "reactive라서 무조건 streaming"이 아니라, **응답 media type이 item 경계를 표현할 수 있느냐**에 따라 `DeferredResult<List<?>>` 집계 경로와 `ResponseBodyEmitter`/`SseEmitter` 스트리밍 경로로 갈린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
> - [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)
> - [Spring Streaming Client Parsing Matrix: `fetch`, `EventSource`, CLI Line Readers](./spring-streaming-client-parsing-matrix.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)
> - [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)
> - [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)

retrieval-anchor-keywords: Spring MVC Flux adaptation, Spring MVC reactive return value, Flux application/json, Flux NDJSON, Flux SSE, ReactiveTypeHandler, ResponseBodyEmitterReturnValueHandler, DeferredResult<List<?>>, collect Flux to List, application/x-ndjson Spring MVC, application/json aggregate, Flux<ServerSentEvent>, multi-value reactive return, content negotiation reactive stream, blocking writes AsyncTaskExecutor, JsonEmitterSubscriber, SseEmitterSubscriber, fetch ndjson parser, EventSource SSE parser, CLI line reader streaming

---

## 핵심 개념

Spring MVC는 `Flux<OrderEvent>` 자체만 보고 "이건 스트리밍이다"라고 결정하지 않는다.

프레임워크가 실제로 보는 것은 두 축이다.

- source shape: single-value인가 multi-value인가
- wire contract: negotiated media type이 item 경계를 안전하게 표현하는가

그래서 같은 `Flux<T>`도 결과가 갈린다.

| 반환값 | negotiated media type | MVC 내부 적응 | 클라이언트가 받는 shape |
|---|---|---|---|
| `Flux<T>` | `application/json` | `DeferredResult<List<?>>`로 모았다가 한 번에 write | 보통 JSON array |
| `Flux<T>` | `application/x-ndjson` | `ResponseBodyEmitter`로 item마다 write | 줄 단위 JSON record |
| `Flux<ServerSentEvent<T>>` 또는 `Flux<T>` | `text/event-stream` | `SseEmitter`로 event마다 write | SSE event block |

핵심은 `Flux`라는 타입이 아니라 **`application/json`은 완결된 JSON document를, NDJSON/SSE는 item별 framing을 기대한다**는 데 있다.

## 먼저 구분할 것: reactive source와 HTTP 문서 계약은 다르다

`Flux`는 publisher가 여러 값을 낼 수 있다는 뜻이다.
하지만 HTTP 응답이 여러 값을 어떤 문법으로 표현할지는 media type이 정한다.

- `application/json`: 보통 object나 array 하나의 완결된 JSON document
- `application/x-ndjson`: JSON value 하나 + newline이 record 경계
- `text/event-stream`: `data:`, `id:`, 빈 줄로 끝나는 SSE event block이 경계

즉 MVC가 묻는 질문은 "`Flux`인가?"가 아니라 "`이 media type에서 element 하나를 바로 내보내도 클라이언트가 의미 단위로 읽을 수 있는가?`"다.

## 깊이 들어가기

### 1. 분기 지점은 `ResponseBodyEmitterReturnValueHandler`와 `ReactiveTypeHandler`다

Spring MVC annotated controller에서 reactive return type은 `ResponseBodyEmitterReturnValueHandler`가 받고, 실제 적응은 내부의 `ReactiveTypeHandler`가 한다.

공식 문서 기준 동작 요약은 이렇다.

- single-value reactive type은 `DeferredResult`와 비슷하게 적응한다
- multi-value + streaming media type은 `ResponseBodyEmitter`/`SseEmitter`와 비슷하게 적응한다
- multi-value + 그 외 media type은 `DeferredResult<List<?>>`와 비슷하게 적응한다

즉 "MVC가 `Flux`를 이해한다"는 말의 정확한 뜻은, **reactive source를 Servlet async와 emitter 계열로 번역해 준다**는 뜻이지 MVC가 곧 WebFlux가 된다는 뜻은 아니다.

### 2. `application/json`일 때는 item을 흘려 쓰지 않고 먼저 모은다

`ReactiveTypeHandler`는 multi-value source라도 streaming media type이 아니면 `DeferredResultSubscriber`로 구독해서 값을 모은 뒤 완료 시점에 결과를 세팅한다.

이 경로의 의미는 다음과 같다.

- 구독 중엔 요소를 `List`에 모은다
- complete되면 `DeferredResult`에 그 목록을 넣는다
- 이후 MVC의 일반 `HttpMessageConverter` 경로가 최종 JSON document를 한 번에 쓴다

왜 이렇게 하느냐면 `application/json`은 보통 **중간 조각이 아니라 완성된 문서**를 뜻하기 때문이다.

예를 들어 요소를 그대로 순서대로 write하면 wire는 이런 shape가 되기 쉽다.

```json
{"id":1}{"id":2}{"id":3}
```

이건 일반 JSON parser가 기대하는 array가 아니다.
반대로 array를 진짜로 흘려 쓰려면 `[` `,` `]` framing과 중간 실패 처리까지 프레임워크가 별도 소유해야 한다.

Spring MVC는 여기서 "스트리밍처럼 보이게 partially valid JSON을 보내기"보다:

- 일반 JSON client 호환성 유지
- 완결된 document shape 보장
- commit 전까지 기존 body pipeline 유지

를 택한다.

추가로 source가 multi-value였다면 element가 1개여도 결과를 단일 object가 아니라 list shape로 유지한다. 즉 "원래 `Flux`였다는 정보"를 HTTP shape에 반영한다.

### 3. NDJSON는 item 경계가 newline이라서 바로 흘려 보낼 수 있다

`application/x-ndjson`가 협상되면 MVC는 `JsonEmitterSubscriber` 경로를 탄다.

이 경로는 element마다:

- element를 `application/json`으로 직렬화해서 쓴다
- 이어서 `\n`을 쓴다

즉 record framing이 이미 media type 계약에 들어 있으므로, 각 element를 독립 record로 바로 내보내도 wire 문서가 깨지지 않는다.

이 점이 `application/json`과의 본질적 차이다.

- `application/json`: 문서 전체가 닫혀야 안전한 경우가 많다
- `application/x-ndjson`: newline만 오면 그 record는 이미 완결이다

그래서 첫 결과 latency, 메모리 사용량, client incremental parsing 측면에선 NDJSON가 훨씬 자연스럽다.

### 4. SSE는 event block framing이 있으므로 역시 streaming이 성립한다

`text/event-stream`이거나 element type이 `ServerSentEvent`면 MVC는 `SseEmitter` 경로를 탄다.

여기서는 element마다 event block이 완성된다.

- `ServerSentEvent<?>`면 `id`, `event`, `retry`, `comment`, `data`를 SSE 형식으로 적응한다
- plain object라도 SSE event의 payload로 write할 수 있다

SSE도 NDJSON와 마찬가지로 item 경계가 wire format에 내장돼 있다.
그래서 event 하나를 보내는 즉시 클라이언트는 의미 있는 단위 하나를 받을 수 있다.

### 5. 이 차이는 "streaming 가능 여부"가 아니라 "framing ownership" 차이다

세 media type을 같은 축에서 보면 판단 기준이 더 선명해진다.

| media type | item 경계 소유자 | MVC가 multi-value를 바로 흘려 보내기 쉬운가 | 이유 |
|---|---|---|---|
| `application/json` | 보통 전체 document | 아니다 | array/document framing을 따로 관리해야 함 |
| `application/x-ndjson` | newline | 그렇다 | element마다 독립 record를 만들 수 있음 |
| `text/event-stream` | SSE event block | 그렇다 | event block 자체가 streaming grammar임 |

즉 MVC가 `application/json`을 aggregate하는 이유는 reactive를 싫어해서가 아니라, **document framing을 프레임워크가 임의 추측하지 않기 위해서**다.

### 6. MVC에서 `Flux`를 반환해도 write는 여전히 blocking이다

공식 문서도 이 점을 분명히 적는다.

- reactive back pressure는 지원한다
- 하지만 response write 자체는 여전히 blocking이다
- 그래서 write는 별도 `AsyncTaskExecutor` thread에서 수행된다

즉 MVC에서 NDJSON/SSE로 streaming한다고 해서 execution model이 WebFlux처럼 non-blocking I/O로 바뀌는 것은 아니다.

이건 운영 해석에 바로 연결된다.

- 느린 client write는 여전히 Servlet stack 제약을 가진다
- disconnect는 다음 write에서 surface되기 쉽다
- executor sizing을 무시하면 streaming endpoint가 흔들릴 수 있다

### 7. `application/json` 집계는 latency 대신 shape 안정성과 오류 의미를 산다

집계 경로와 streaming 경로의 트레이드오프를 요약하면 이렇다.

| 선택 | 얻는 것 | 잃는 것 |
|---|---|---|
| `application/json` 집계 | 표준 JSON array/object 계약, 일반 REST client 호환성, commit을 늦출 여지 | 첫 결과 latency, 메모리 여유 |
| NDJSON/SSE streaming | 빠른 첫 바이트, item별 incremental parsing, 긴 stream 처리 | early commit, partial failure 복구 어려움, stream-specific client 필요 |

따라서 요구사항이 "브라우저/CLI가 중간 결과를 즉시 본다"면 NDJSON나 SSE가 맞고, "일반 JSON API contract를 유지한다"면 집계가 더 맞다.

## 실전 시나리오

### 시나리오 1: `Flux<OrderDto>`를 반환했는데 프런트가 끝까지 기다린다

대개 `Accept: application/json`이어서 MVC가 `DeferredResult<List<?>>` 경로를 탔기 때문이다.

원인이 `Flux`가 가짜라서가 아니라, **요청한 media type이 non-streaming JSON contract**였던 것이다.

### 시나리오 2: 같은 메서드인데 `produces = application/x-ndjson`로 바꾸자마자 chunk가 보인다

이건 MVC가 갑자기 WebFlux처럼 변한 게 아니다.
단지 NDJSON가 item framing을 제공해서 `ResponseBodyEmitter` streaming 경로가 열린 것이다.

### 시나리오 3: `Flux<ServerSentEvent<?>>`를 MVC 컨트롤러에서 반환했다

SSE 자체는 정상적으로 streaming되지만, 여전히 Servlet stack 위에서 blocking write + async executor 모델을 쓴다.
timeout, disconnect, cleanup 기준은 WebFlux SSE와 다르다.

## 코드로 보기

### 같은 `Flux`라도 media type에 따라 결과가 달라진다

```java
@GetMapping(value = "/orders", produces = MediaType.APPLICATION_JSON_VALUE)
public Flux<OrderResponse> ordersJson() {
    return orderService.streamOrders();
}

@GetMapping(value = "/orders.ndjson", produces = MediaType.APPLICATION_NDJSON_VALUE)
public Flux<OrderResponse> ordersNdjson() {
    return orderService.streamOrders();
}

@GetMapping(value = "/orders.sse", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<OrderResponse>> ordersSse() {
    return orderService.streamOrders()
            .map(order -> ServerSentEvent.builder(order).event("order").build());
}
```

이 세 메서드는 source는 비슷하지만 응답 계약은 다르다.

- JSON endpoint: 완료 후 array shape로 응답
- NDJSON endpoint: element마다 newline-delimited record로 응답
- SSE endpoint: event block마다 응답

### 잘못된 기대: `application/json`인데 chunk마다 `JSON.parse`

```text
Flux<T> returned
-> client requests application/json
-> MVC collects values
-> final JSON document written once
```

이 경우 client가 "중간 chunk를 바로 parse하겠다"는 기대를 가지면 계약이 어긋난다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `Flux<T>` + `application/json` | 기존 REST contract 유지, client 호환성 높음 | 결과가 모일 때까지 기다림 | 일반 조회 API |
| `Flux<T>` + `application/x-ndjson` | item별 JSON 파싱 쉬움, CLI/stream consumer 친화적 | 표준 JSON array client와는 다름 | incremental result feed |
| `Flux<ServerSentEvent<T>>` + `text/event-stream` | 브라우저 `EventSource` 친화적, event metadata 사용 가능 | SSE 전용 운영 고려 필요 | browser push, heartbeat, reconnect |

## 꼬리질문

> Q: 왜 Spring MVC는 `Flux<T>`를 반환해도 `application/json`이면 바로 흘려 쓰지 않는가?
> 의도: media type과 document framing 관계 확인
> 핵심: `application/json`은 보통 완결된 문서를 기대하므로 multi-value source를 `DeferredResult<List<?>>`처럼 모아 안전한 JSON shape로 쓴다.

> Q: NDJSON와 SSE는 왜 같은 `Flux<T>`라도 streaming이 가능한가?
> 의도: item framing 이해 확인
> 핵심: 둘 다 wire format 자체가 item 경계를 제공하므로 element를 바로 보내도 클라이언트가 record/event 단위로 읽을 수 있다.

> Q: MVC에서 `Flux<ServerSentEvent<?>>`를 반환하면 WebFlux와 같은가?
> 의도: execution model 구분 확인
> 핵심: 아니다. MVC는 reactive source를 적응해 줄 뿐 response write는 여전히 blocking이고 별도 async executor thread를 쓴다.

## 한 줄 정리

Spring MVC에서 `Flux`의 운명은 타입명보다 media type이 정한다. `application/json`은 완결 문서라서 모으고, NDJSON와 SSE는 framing이 있으므로 흘려 보낸다.
