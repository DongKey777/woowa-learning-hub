# Spring `ResponseBodyAdvice` on Streaming Types: `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`

> 한 줄 요약: global JSON envelope를 `ResponseBodyAdvice`로 통일하고 싶어도 `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`는 별도 return value handler가 ownership을 가져가므로 advice가 적용되지 않거나 handler 선택 자체가 바뀌며, 억지로 감싸면 `text/event-stream`, NDJSON, binary stream 같은 wire contract를 깨뜨리기 쉽다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `HandlerMethodReturnValueHandler` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
> - [Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline](./spring-requestbody-responsebodyadvice-pipeline.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)
> - [Spring `HttpMessageNotWritableException` Failure Taxonomy](./spring-httpmessagenotwritableexception-failure-taxonomy.md)
> - [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)

retrieval-anchor-keywords: ResponseBodyAdvice, global response envelope, api envelope, response envelope, ResponseBodyEmitter, SseEmitter, StreamingResponseBody, ResponseEntity<ResponseBodyEmitter>, ResponseEntity<SseEmitter>, ResponseEntity<StreamingResponseBody>, ResponseBodyEmitterReturnValueHandler, StreamingResponseBodyReturnValueHandler, RequestResponseBodyMethodProcessor, HttpEntityMethodProcessor, beforeBodyWrite, streaming return type, streaming wire contract, text/event-stream envelope, NDJSON envelope, binary stream envelope, handler selection, http-message-converter

## 핵심 개념

이 주제에서 가장 먼저 버려야 할 오해는 "`ResponseBodyAdvice`는 모든 응답의 마지막 공통 훅"이라는 생각이다.

실제로는 두 단계가 분리되어 있다.

1. 어떤 `HandlerMethodReturnValueHandler`가 반환값 ownership을 가져갈지 결정
2. 그 handler가 body write 경로라면, 그 안에서 `HttpMessageConverter`와 `ResponseBodyAdvice`가 개입

따라서 streaming 타입은 "advice에서 특별 취급하면 된다"보다 먼저 **애초에 어느 handler가 선택되는가**를 봐야 한다.

## 먼저 결론

| 반환 형태 | 실제 ownership | `ResponseBodyAdvice` 적용 여부 | envelope를 억지로 씌울 때 깨지는 것 |
|---|---|---|---|
| `@ResponseBody Foo` | `RequestResponseBodyMethodProcessor` | 적용됨 | 보통 JSON/String converter 조합 |
| `ResponseEntity<Foo>` | `HttpEntityMethodProcessor` | 적용됨 | 상태 코드/헤더는 유지되지만 body 타입 mismatch 가능 |
| `ResponseBodyEmitter`, `SseEmitter`, `ResponseEntity<ResponseBodyEmitter>`, `ResponseEntity<SseEmitter>` | `ResponseBodyEmitterReturnValueHandler` | 적용되지 않음 | `text/event-stream`, NDJSON, plain-text record framing |
| `StreamingResponseBody`, `ResponseEntity<StreamingResponseBody>` | `StreamingResponseBodyReturnValueHandler` | 적용되지 않음 | file/binary stream, CSV/export/download byte layout |

핵심은 `ResponseEntity<...>`로 한 번 더 감싸도 streaming handler가 그 형태를 직접 지원한다는 점이다. 즉 "일단 `ResponseEntity`니까 advice가 다시 돌겠지"라고 보면 틀린다.

## 깊이 들어가기

### 1. advice는 handler 선택 이후에만 의미가 있다

`ResponseBodyAdvice.beforeBodyWrite(...)`는 `AbstractMessageConverterMethodProcessor` 계열에서 `HttpMessageConverter.write(...)` 직전에 호출된다.

즉 다음 경로에서만 의미가 있다.

- `@ResponseBody` plain object
- 일반 `ResponseEntity<T>`
- `ProblemDetail`, error DTO 같은 finite body

반대로 handler 선택이 아예 다른 클래스로 가면, advice를 붙일 자리가 없다.

### 2. `ResponseBodyEmitter`와 `SseEmitter`는 converter를 써도 advice를 거치지 않는다

많이 헷갈리는 지점이 여기다.

- `ResponseBodyEmitter`는 각 `send(...)`마다 `HttpMessageConverter`를 사용한다
- `SseEmitter`도 내부적으로는 emitter handler를 통해 payload를 쓴다

그래서 겉으로 보면 "`HttpMessageConverter`를 쓰니 `ResponseBodyAdvice`도 당연히 돌겠지"처럼 보인다.

하지만 실제 ownership은 `ResponseBodyEmitterReturnValueHandler`가 가져가고, 이 경로는 `AbstractMessageConverterMethodProcessor`의 `beforeBodyWrite(...)` 체인을 타지 않는다.

즉 emitter 계열에서 벌어지는 일은 다음에 가깝다.

```text
return ResponseBodyEmitter or SseEmitter
-> ResponseBodyEmitterReturnValueHandler 선택
-> 내부 handler가 send(...)마다 converter.write(...)
-> flush / async lifecycle callback
```

여기엔 global `ResponseBodyAdvice`가 끼어들 공통 pre-write 지점이 없다.

따라서 "모든 응답을 advice로 envelope 처리했는데 왜 SSE는 안 감싸지지?"라는 질문의 답은, **그 응답이 advice 파이프라인을 지나지 않기 때문**이다.

### 3. `StreamingResponseBody`는 더 직접적이라 advice를 붙일 수도 없다

`StreamingResponseBody`는 `OutputStream`을 직접 쓰는 callback 계약이다.

즉 경로는 대략 이렇게 된다.

```text
return StreamingResponseBody
-> StreamingResponseBodyReturnValueHandler 선택
-> callback이 OutputStream에 직접 write/flush
```

여기엔 `HttpMessageConverter`도, `ResponseBodyAdvice`도 없다.

따라서 binary 다운로드, CSV export, zip stream, large file relay 같은 경로에 JSON envelope를 붙이려는 발상 자체가 맞지 않는다.

앞에 `{ "data": ... }` 같은 bytes를 한 번만 써도 파일 헤더와 checksum, parser 기대값이 즉시 깨질 수 있다.

### 4. top-level return type을 envelope DTO로 바꾸면 streaming handler 선택이 사라진다

이건 운영에서 실제로 자주 나는 설계 실수다.

예를 들어 다음을 기대하면 안 된다.

```java
public ApiEnvelope<ResponseBodyEmitter> stream() { ... }
public ApiEnvelope<StreamingResponseBody> download() { ... }
```

이 순간 top-level return type은 더 이상 `ResponseBodyEmitter`나 `StreamingResponseBody`가 아니다.

그러면 Spring은 streaming handler로 가지 않고, 일반 body serialization 경로로 해석하려 할 수 있다. 그 결과는 대개 다음 중 하나다.

- `HttpMessageNotWritableException`
- emitter/streaming 객체를 이상한 JSON 객체처럼 직렬화하려다 실패
- 아예 기대한 `text/event-stream`/download contract가 성립하지 않음

즉 **streaming semantics는 top-level return type 선택에서 이미 결정**되며, advice는 그 결정을 뒤집는 복구 레이어가 아니다.

### 5. wire contract를 유지하려면 envelope를 HTTP root가 아니라 stream protocol 안에 넣어야 한다

global envelope가 보통 하고 싶은 일은 세 가지다.

- 공통 metadata 전달
- success/error shape 일관화
- trace/request id 같은 부가 정보 노출

streaming endpoint에서는 이 요구를 JSON root envelope가 아니라 **해당 프로토콜의 허용 범위 안에서** 풀어야 한다.

| 타입 | 안전한 방법 | 피해야 할 방법 |
|---|---|---|
| `SseEmitter` | 첫 `meta` event, `id:`/`event:`/`retry:` 필드, HTTP header | `text/event-stream` 위에 JSON root envelope 강제 |
| `ResponseBodyEmitter` + NDJSON | 첫 record를 `{"type":"meta",...}`로 명시, 이후 record도 명확한 union schema 사용 | NDJSON header만 두고 전체를 `{"data":[...]}`처럼 감싸기 |
| `ResponseBodyEmitter` + plain text | 첫 line에 metadata를 명시하거나 헤더로 분리 | line stream 앞에 JSON envelope prefix 삽입 |
| `StreamingResponseBody` | 헤더, query, sidecar metadata endpoint, 사전 handshake | binary body 앞뒤에 envelope bytes 덧붙이기 |

핵심은 "공통 shape를 포기하라"가 아니라, **HTTP 응답 루트 envelope와 stream protocol payload schema를 분리하라**는 것이다.

### 6. `ResponseEntity<StreamingType>`는 헤더/상태 조정용이지 advice 복귀 스위치가 아니다

`ResponseEntity<SseEmitter>`나 `ResponseEntity<StreamingResponseBody>`는 여전히 유용하다.

- 상태 코드 조정
- `Cache-Control`, `Content-Disposition`, `X-Accel-Buffering` 같은 헤더 추가
- content type 명시

하지만 이 wrapper의 의미는 HTTP 메타데이터 ownership이지, "다시 일반 JSON body 경로로 보내기"가 아니다.

즉 이런 조합은 안전하다.

- `ResponseEntity.ok().contentType(TEXT_EVENT_STREAM).body(emitter)`
- `ResponseEntity.ok().header(CONTENT_DISPOSITION, ...).body(streamingBody)`

반대로 이런 기대는 틀린다.

- `ResponseEntity`니까 `ResponseBodyAdvice`가 자동으로 envelope를 씌워 줄 것이다
- streaming body 일부가 나간 뒤 예외가 나면 `ProblemDetail`로 다시 바꿀 수 있다

### 7. global envelope 정책은 whitelist가 blacklist보다 안전하다

실무에선 `supports(...)`를 넓게 열어 두고 예외 케이스를 계속 빼는 방식이 오래 못 버틴다.

더 안전한 기준은 이렇다.

- finite JSON DTO만 envelope 대상으로 본다
- `String`, `Resource`, `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`는 처음부터 raw contract bucket으로 둔다
- "streaming이지만 metadata를 같이 주고 싶다"는 요구는 해당 stream schema에서 해결한다

즉 global advice는 "모든 성공 응답"이 아니라 **"JSON document로 닫히는 성공 응답"** 에만 적용하는 편이 덜 깨진다.

## 실전 시나리오

### 시나리오 1: 공통 API envelope를 넣었더니 `EventSource`가 갑자기 파싱을 못 한다

대개 `SseEmitter` endpoint를 일반 JSON success contract로 통일하려 한 경우다.

SSE client는 `text/event-stream` field grammar를 기대한다. 이 경로에서 필요한 metadata는 `meta` event나 header로 보내야지, HTTP root를 JSON으로 바꾸면 안 된다.

### 시나리오 2: `ResponseEntity<SseEmitter>`면 `ResponseBodyAdvice`가 적용될 줄 알았다

틀린 기대다.

`ResponseEntity<SseEmitter>`는 여전히 emitter 전용 handler가 가져간다. 얻는 것은 상태 코드와 헤더 조정이고, 잃는 것은 없다. 다만 advice는 여전히 적용되지 않는다.

### 시나리오 3: 다운로드 endpoint에도 성공 envelope를 맞추고 싶다

`StreamingResponseBody`나 `Resource` 계열은 JSON envelope와 같은 bucket이 아니다.

다운로드 metadata가 필요하면 다음을 먼저 고려한다.

- `Content-Disposition`, checksum, version header
- 다운로드 전 metadata endpoint
- export job polling 후 signed URL or file URL handoff

파일 bytes 앞에 envelope를 붙이는 것은 형식 손상에 가깝다.

### 시나리오 4: NDJSON stream에 "status"도 같이 섞고 싶다

가능하지만 protocol을 명시해야 한다.

예를 들어 첫 줄을 metadata record로 두고 이후 줄을 data record로 두는 식은 가능하다.

```json
{"type":"meta","requestId":"r-123"}
{"type":"item","id":1}
{"type":"item","id":2}
```

이건 NDJSON contract 안의 schema 설계이지, `ResponseBodyAdvice`가 HTTP root에 envelope를 씌우는 일이 아니다.

## 코드로 보기

### finite JSON 응답만 envelope 대상으로 고정하기

```java
@ControllerAdvice
public class ApiEnvelopeAdvice implements ResponseBodyAdvice<Object> {

    @Override
    public boolean supports(MethodParameter returnType,
                            Class<? extends HttpMessageConverter<?>> converterType) {
        return MappingJackson2HttpMessageConverter.class.isAssignableFrom(converterType)
                && !hasRawContract(returnType);
    }

    private boolean hasRawContract(MethodParameter returnType) {
        Class<?> rawType = returnType.getParameterType();
        ResolvableType resolvableType = ResolvableType.forMethodParameter(returnType);
        Class<?> bodyType = ResponseEntity.class.isAssignableFrom(rawType)
                ? resolvableType.getGeneric(0).resolve()
                : rawType;

        return bodyType != null && (
                ResponseBodyEmitter.class.isAssignableFrom(bodyType) ||
                StreamingResponseBody.class.isAssignableFrom(bodyType) ||
                Resource.class.isAssignableFrom(bodyType)
        );
    }

    @Override
    public Object beforeBodyWrite(Object body,
                                  MethodParameter returnType,
                                  MediaType selectedContentType,
                                  Class<? extends HttpMessageConverter<?>> selectedConverterType,
                                  ServerHttpRequest request,
                                  ServerHttpResponse response) {
        return ApiEnvelope.success(body);
    }
}
```

중요한 점은 두 가지다.

- 실제 streaming 타입은 원래 advice 경로를 타지 않으므로, 이 검사는 주로 정책 명시와 refactor 방어선 역할을 한다
- envelope 정책을 converter whitelist 중심으로 두면 `String`, download, streaming처럼 raw contract가 필요한 엔드포인트를 덜 건드린다

### `SseEmitter`에서 metadata를 protocol 안으로 넣기

```java
@GetMapping(value = "/prices", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public SseEmitter prices() {
    SseEmitter emitter = new SseEmitter(60_000L);

    executor.execute(() -> {
        try {
            emitter.send(SseEmitter.event()
                    .name("meta")
                    .data(Map.of("requestId", "r-123", "schema", "price-stream-v1")));

            emitter.send(SseEmitter.event()
                    .name("price")
                    .id("evt-1")
                    .data(Map.of("symbol", "AAPL", "price", 210.4)));

            emitter.complete();
        }
        catch (IOException ex) {
            emitter.completeWithError(ex);
        }
    });

    return emitter;
}
```

이 방식은 envelope 요구를 버리는 것이 아니라, **SSE가 이해하는 단위로 metadata를 옮기는 것**이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| global `ResponseBodyAdvice` envelope | finite JSON 응답을 중앙집중식으로 통일하기 쉽다 | streaming/binary/raw contract에는 맞지 않는다 | 일반 REST JSON 성공 응답 |
| stream별 protocol metadata | wire contract를 보존하면서 metadata를 보낼 수 있다 | client schema가 조금 더 복잡해진다 | SSE, NDJSON, long-lived stream |
| 헤더 + sidecar metadata endpoint | body format을 가장 안전하게 보존한다 | metadata 조회가 한 단계 늘 수 있다 | download/export/file relay |

## 꼬리질문

> Q: `ResponseBodyEmitter`도 `HttpMessageConverter`를 쓰는데 왜 `ResponseBodyAdvice`가 안 도는가?
> 의도: converter 사용과 advice 적용 경로를 분리해 이해하는지 확인
> 핵심: emitter 계열은 별도 return value handler가 ownership을 가져가고, 그 내부 write는 `AbstractMessageConverterMethodProcessor`의 `beforeBodyWrite(...)` 체인을 타지 않기 때문이다.

> Q: `ResponseEntity<SseEmitter>`면 advice가 다시 적용되는가?
> 의도: `ResponseEntity` wrapper 의미를 정확히 이해하는지 확인
> 핵심: 아니다. 상태 코드와 헤더 조정은 가능하지만, 여전히 emitter 전용 handler가 처리한다.

> Q: streaming endpoint에도 metadata를 통일하고 싶으면 어떻게 해야 하는가?
> 의도: envelope 요구를 protocol 설계로 옮기는 사고 확인
> 핵심: SSE event, NDJSON record, header, sidecar endpoint처럼 해당 wire contract가 허용하는 채널을 써야 한다.

> Q: `ApiEnvelope<StreamingResponseBody>`가 왜 위험한가?
> 의도: top-level return type이 handler selection에 미치는 영향 확인
> 핵심: top-level 타입이 바뀌면 Spring이 더 이상 streaming handler를 선택하지 못하고, 일반 serialization 경로로 해석하려다 contract가 깨질 수 있다.

## 한 줄 정리

`ResponseBodyAdvice`는 "모든 응답을 마지막에 감싸는 훅"이 아니라 message-converter body 경로의 pre-write hook이므로, `ResponseBodyEmitter`·`SseEmitter`·`StreamingResponseBody`는 별도 streaming contract로 설계하고 envelope 요구는 그 protocol 안으로 옮겨야 wire를 망치지 않는다.
