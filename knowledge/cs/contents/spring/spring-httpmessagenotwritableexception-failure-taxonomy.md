# Spring `HttpMessageNotWritableException` Failure Taxonomy

> 한 줄 요약: `HttpMessageNotWritableException`는 "converter를 못 골랐는가", "converter는 골랐지만 serialize에서 막혔는가", "first flush에서 commit이 넘어갔는가", "일부 body를 이미 내보낸 뒤 잘렸는가"를 분리해서 읽어야만 pre-commit 오류와 post-commit partial response를 구분할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
> - [Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline](./spring-requestbody-responsebodyadvice-pipeline.md)
> - [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)
> - [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
> - [Spring `ProblemDetail` vs `/error` Handoff Matrix](./spring-problemdetail-vs-error-handoff-matrix.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)

retrieval-anchor-keywords: HttpMessageNotWritableException, no converter for return value, preset Content-Type, converter selection failure, no suitable converter, response serialization failure, Could not write JSON, JsonProcessingException, first flush, flush failure, response commit, response committed already, partial write, partial response, truncated JSON, invalid JSON document, /error handoff, ProblemDetail, DefaultHandlerExceptionResolver, ResponseEntityExceptionHandler, ClientAbortException, AsyncRequestNotUsableException

## 핵심 개념

`HttpMessageNotWritableException`를 하나의 500 bucket으로 묶으면 retrieval이 자꾸 틀린다.

같은 예외 이름이 전혀 다른 시점을 가리킬 수 있기 때문이다.

- converter 선택 실패: 아직 bytes를 하나도 만들지 못했다
- serialization 실패: converter는 골랐지만 body를 완성하지 못했다
- flush 실패: 첫 바이트를 내보내는 경계에서 commit ownership을 잃었다
- partial-write 실패: 일부 body를 이미 보낸 뒤 문서가 잘렸다

즉 먼저 봐야 할 질문은 두 개다.

1. converter가 실제로 선택됐는가?
2. first byte 또는 commit 경계를 이미 넘었는가?

이 두 질문으로 나누면 retrieval label도 선명해진다.

- `hmnwe.converter-selection.pre-commit`
- `hmnwe.serialization.pre-commit`
- `hmnwe.flush.post-commit`
- `hmnwe.partial-write.post-commit`

## 소스 기준 체크포인트

Spring MVC body write 경로를 소스 기준으로 줄이면 대략 이 순서다.

```text
return value handler
-> media type negotiation
-> canWrite(...) converter 탐색
-> ResponseBodyAdvice.beforeBodyWrite(...)
-> converter.write(...)
   -> writeInternal(...)
   -> serializer / generator
   -> flush 또는 buffer drain
-> commit 이후에는 resolver가 새 body ownership을 잃음
```

여기서 taxonomy를 가르는 체크포인트는 다음 네 군데다.

- `AbstractMessageConverterMethodProcessor.writeWithMessageConverters(...)`
  - media type과 converter를 고른다
  - 끝까지 못 고르면 경우에 따라 `HttpMessageNotWritableException` 또는 `HttpMediaTypeNotAcceptableException`이 된다
- `ResponseBodyAdvice.beforeBodyWrite(...)`
  - converter 선택 뒤, 실제 직렬화 직전 마지막 pre-write 훅이다
- `HttpMessageConverter.write(...)` / `writeInternal(...)`
  - 실제 serialization이 일어난다
- `DefaultHandlerExceptionResolver.handleHttpMessageNotWritable(...)`
  - `response.isCommitted()==false`면 500 `sendError(...)`를 시도하지만, 이미 commit됐으면 경고만 남기고 새 오류 body를 포기한다

## Failure Taxonomy

| variant | 실패 지점 | 전형적 신호 | commit 상태 | retrieval 해석 |
|---|---|---|---|---|
| converter-selection | converter loop를 끝까지 돌았지만 쓸 converter가 없음 | `No converter for [...] with preset Content-Type ...` | pre-commit | media type / return type / converter 등록 문제 |
| serialization | converter는 골랐고 `writeInternal(...)` 안에서 직렬화가 실패 | `Could not write JSON: ...` 같은 메시지 | 보통 pre-commit | object graph / serializer / advice 변형 문제 |
| flush | 직렬화는 어느 정도 진행됐고 first flush 또는 buffer drain에서 commit 경계가 닫힘 | `response committed already`, first-byte 직후 오류 | post-commit 경계 | 더 이상 `ProblemDetail`/`/error` ownership이 약함 |
| partial-write | 일부 body를 이미 썼고 뒤에서 예외가 남음 | truncated JSON, 반쯤 내려간 응답, broken pipe 동반 | 확정 post-commit | partial response / transport integrity 문제 |

## 1. Converter-Selection Variant

이 variant는 가장 "이른" `HttpMessageNotWritableException`이다.

아직 serializer까지 가지도 못했다.

대표 패턴은 다음과 같다.

- `Content-Type`이 이미 preset됐거나
- `produces`/`PRODUCIBLE_MEDIA_TYPES_ATTRIBUTE`로 media type이 사실상 고정됐는데
- 그 media type과 return value 타입 조합을 처리할 converter가 없다

이때는 Spring이 converter loop를 다 돌고도 쓸 수단을 못 찾아 `HttpMessageNotWritableException`를 던진다.

중요한 점은 "converter를 못 골랐다"와 "406 negotiation 실패"가 같지 않다는 점이다.

- preset `Content-Type` 또는 고정 producible type이 있으면 `HttpMessageNotWritableException`
- 그런 고정 계약이 없고 단지 `Accept`를 못 맞췄다면 `HttpMediaTypeNotAcceptableException`

즉 retrieval에서 `No converter for ... with preset Content-Type`가 보이면, 이건 serialization/flush가 아니라 **selection failure**로 잘라야 한다.

### 흔한 원인

- `ResponseBodyAdvice`가 body 타입을 바꿨는데 선택된 converter가 그 새 타입을 못 씀
- `produces = "text/csv"`를 걸었지만 CSV converter를 등록하지 않음
- `ResponseEntity`로 header를 강하게 preset했는데 return body 타입이 그 media type과 맞지 않음

### retrieval cue

- `No converter for`
- `preset Content-Type`
- `selected media type`
- `canWrite` mismatch

## 2. Serialization Variant

이 variant는 converter는 골랐지만 body를 bytes로 바꾸는 과정에서 실패한 경우다.

여기서는 `ResponseBodyAdvice.beforeBodyWrite(...)`까지 끝났고, 이제 실제 serializer가 돈다.

대표 신호는 다음과 같다.

- `Could not write JSON: ...`
- serializer 내부 `JsonProcessingException` 계열 원인
- converter-specific marshalling failure

이 variant는 retrieval에서 pre-commit으로 잡는 것이 기본값이다.

이유는 아직 response 전체를 갈아엎을 여지가 남아 있는 경우가 많기 때문이다.

- `ResponseEntityExceptionHandler`가 새 오류 body를 만들 수 있다
- `DefaultHandlerExceptionResolver`가 500 `sendError(...)`를 시도할 수 있다
- unresolved면 `/error` handoff 후보도 남는다

다만 "serialization 문제 = 항상 `HttpMessageNotWritableException`"는 아니다.

예를 들어 Jackson의 일부 type-definition 계열은 `HttpMessageConversionException`으로 튈 수 있다.

즉 retrieval은 `Could not write JSON` 같은 signal과 top-level exception family를 함께 봐야 한다.

### 흔한 원인

- 순환 참조나 lazy proxy가 serialize 도중 터짐
- custom serializer가 특정 필드 shape를 처리하지 못함
- advice가 envelope를 씌우며 serializer가 예상하지 못한 타입으로 바꿈

### retrieval cue

- `Could not write JSON`
- `JsonProcessingException`
- `beforeBodyWrite`
- `response not committed`

## 3. Flush Variant

이 variant는 가장 헷갈리는 경계다.

converter와 serializer는 어느 정도 일을 했지만, first flush 또는 servlet buffer drain 시점에 response ownership이 닫힌다.

이때 중요한 사실은 "예외 이름"보다 `response.isCommitted()` 결과다.

- committed 전이면 아직 500 또는 `ProblemDetail` 재작성 여지가 있다
- committed 후면 `DefaultHandlerExceptionResolver`는 경고만 남기고 새 body를 포기한다

실무에서 보이는 shape는 흔히 이렇다.

- `Response already committed. Ignoring: ...`
- `Ignoring exception, response committed already: HttpMessageNotWritableException`
- first-byte latency는 찍혔는데 곧바로 write/flush 실패 로그가 이어짐

이 variant는 retrieval에서 **post-commit boundary case**로 태깅하는 편이 안전하다.

왜냐하면 여기서는 이미 HTTP 계약의 ownership이 socket/write 쪽으로 넘어갔을 가능성이 크기 때문이다.

### 흔한 원인

- 큰 body가 servlet buffer를 처음 넘기면서 commit됨
- 첫 flush 시점에 client/proxy가 이미 끊어져 있었음
- synchronous body처럼 보여도 실제 문제는 first-byte 이후 transport 계층에서 드러남

### retrieval cue

- `response committed already`
- `first flush`
- `flushBuffer`
- `first byte`

## 4. Partial-Write Variant

이 variant는 post-commit이 확정된 형태다.

일부 body가 이미 내려갔고, 그 뒤 나머지를 쓰다가 실패한다.

그래서 이 경우의 핵심은 더 이상 "에러 응답을 어떻게 만들까"가 아니다.

핵심은 **partial response가 이미 나갔는가**다.

대표 징후는 다음과 같다.

- 클라이언트가 잘린 JSON, 닫히지 않은 배열, 반쯤 내려간 파일을 봄
- access log status는 200/206/500처럼 보이지만 payload integrity가 깨짐
- 서버 로그에는 `HttpMessageNotWritableException`와 함께 broken pipe, `ClientAbortException`, `ClosedChannelException` 같은 transport signal이 붙기도 함

이 variant는 retrieval에서 resolver 문맥보다 transport/observability 문맥으로 보내야 한다.

- `ProblemDetail` 재작성 불가
- `/error` handoff 불가
- truncated document detection, reconnect, retry, framing 전략이 더 중요

### 흔한 원인

- JSON 객체 일부는 성공적으로 써졌는데 뒤 필드 serialize에서 실패
- NDJSON/streaming이 아닌 "단일 JSON 문서"를 길게 쓰다가 중간에 실패
- 클라이언트가 중간에 연결을 끊어 후반부 write가 실패

### retrieval cue

- `partial response`
- `truncated JSON`
- `broken pipe`
- `client abort`

## 빠른 판별 순서

```text
1. 로그에 "No converter for ... with preset Content-Type"가 있는가?
   -> yes: converter-selection / pre-commit

2. converter는 골랐고 "Could not write JSON"가 보이는가?
   -> yes: serialization 후보

3. 동시에 "response committed already" 또는 first-byte 이후 write 실패가 보이는가?
   -> yes: flush 또는 partial-write 쪽으로 승격

4. 실제 payload가 일부라도 내려갔는가?
   -> yes: partial-write
   -> no 또는 불명: flush boundary
```

retrieval이 이 순서를 따르면 "`HttpMessageNotWritableException` = 그냥 500 직렬화 에러" 같은 오분류를 크게 줄일 수 있다.

## 왜 `ProblemDetail` 문맥과 transport 문맥을 분리해야 하나

pre-commit 두 variant는 아직 MVC error ownership이 살아 있다.

- converter-selection
- serialization

이 둘은 `ProblemDetail`, `ResponseEntityExceptionHandler`, `/error` handoff 문서로 보내는 게 맞다.

반대로 post-commit 두 variant는 ownership이 transport 쪽으로 기운다.

- flush
- partial-write

이 둘은 disconnect, first-byte, servlet buffer, partial response observability 문서로 연결해야 한다.

즉 같은 `HttpMessageNotWritableException`라도 retrieval의 후속 문서는 달라져야 한다.

## 주의: post-commit에서는 top-level exception이 바뀔 수 있다

문서 이름은 `HttpMessageNotWritableException` taxonomy지만, 실제 운영 로그는 post-commit으로 갈수록 순수 `HttpMessageNotWritableException`만 남지 않는다.

같이 튀는 것들이 많다.

- `ClientAbortException`
- `EofException`
- `ClosedChannelException`
- `AsyncRequestNotUsableException`

따라서 retrieval은 예외 이름 단일 키보다 **converter/write phase + commit state + transport cause**를 함께 색인하는 편이 맞다.

## 꼬리질문

> Q: `No converter for ... with preset Content-Type`는 왜 406이 아니라 `HttpMessageNotWritableException`로 봐야 하나?
> 의도: selection failure와 negotiation failure 구분 확인
> 핵심: 이미 media type 계약이 고정된 뒤라 "원하는 타입을 못 찾았다"가 아니라 "정해진 계약을 쓸 converter가 없다"가 되기 때문이다.

> Q: `Could not write JSON`가 보이면 항상 pre-commit이라고 말해도 되는가?
> 의도: serialization과 commit 경계 구분 확인
> 핵심: 기본값은 pre-commit이지만, `response committed already`나 partial payload 증거가 있으면 flush/partial-write로 재분류해야 한다.

> Q: 왜 flush variant와 partial-write variant를 따로 두는가?
> 의도: post-commit 세분화 이유 확인
> 핵심: 둘 다 post-commit이지만, partial-write는 이미 payload integrity가 깨진 사실이 확정돼 대응 우선순위가 더 transport 쪽으로 이동하기 때문이다.

> Q: post-commit `HttpMessageNotWritableException`를 `@ExceptionHandler`로 복구하려 하면 왜 안 먹히는가?
> 의도: resolver ownership 종료 이해 확인
> 핵심: commit 이후에는 status/header/body ownership이 이미 닫혀 새 오류 body를 안전하게 덮어쓸 수 없기 때문이다.

## 한 줄 정리

`HttpMessageNotWritableException`는 예외 이름 하나로 묶지 말고 `converter-selection` / `serialization` / `flush` / `partial-write`로 갈라서, 앞의 둘은 pre-commit MVC 오류로, 뒤의 둘은 post-commit write/transport 문제로 읽어야 retrieval이 정확해진다.
