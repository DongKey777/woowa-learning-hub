# Spring `ProblemDetail` Before-After Commit Matrix

> 한 줄 요약: `ProblemDetail`이 나올 수 있는지는 예외 이름보다 먼저 "response가 아직 commit되지 않았고 여전히 쓸 수 있는가"로 갈리며, commit 이후 실패는 resolver 문제가 아니라 transport/write 문제로 해석해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `ProblemDetail` Error Response Design](./spring-problemdetail-error-response-design.md)
> - [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
> - [Spring Async Timeout vs Disconnect Decision Tree](./spring-async-timeout-disconnect-decision-tree.md)
> - [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
> - [Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline](./spring-requestbody-responsebodyadvice-pipeline.md)
> - [Spring `HttpMessageNotWritableException` Failure Taxonomy](./spring-httpmessagenotwritableexception-failure-taxonomy.md)
> - [Spring `ProblemDetail` vs `/error` Handoff Matrix](./spring-problemdetail-vs-error-handoff-matrix.md)
> - [Spring `BasicErrorController`, `ErrorAttributes`, and Whitelabel Error Boundaries](./spring-basicerrorcontroller-errorattributes-whitelabel-boundaries.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)

retrieval-anchor-keywords: ProblemDetail, response commit, response committed, before commit, after commit, commit boundary matrix, /error handoff, servlet error dispatch, HandlerExceptionResolver, ResponseEntityExceptionHandler, DefaultHandlerExceptionResolver, ErrorResponse, ErrorResponseException, HttpMessageNotWritableException, converter selection failure, serialization failure, first flush, partial write, truncated JSON, AsyncRequestTimeoutException, AsyncRequestNotUsableException, broken pipe, client abort, disconnected client, StreamingResponseBody, ResponseBodyEmitter, SseEmitter, resetBuffer, sendError, ClientAbortException, EofException, ClosedChannelException, DisconnectedClientHelper

## 핵심 개념

`ProblemDetail` 가능 여부는 예외 클래스 이름 하나로 정해지지 않는다.

항상 두 축을 같이 봐야 한다.

- 번역 축: `@ExceptionHandler`, `ResponseEntityExceptionHandler`, `ErrorResponse`, `/error` fallback 중 하나가 그 실패를 HTTP 오류로 번역할 수 있는가
- 전송 축: response가 아직 commit되지 않았고, write channel도 usable한가

이 둘 중 하나라도 깨지면 `ProblemDetail` 후보는 사라진다.

- commit 전: resolver나 fallback path가 status/body를 다시 쓸 수 있다
- commit 후: status/header는 사실상 닫힌다
- response unusable: `AsyncRequestNotUsableException`, disconnected client처럼 아예 더 쓸 채널이 없다

즉 "`ProblemDetail`을 만들 수 있는 예외인가?"보다 먼저 "`ProblemDetail`을 실어 보낼 수 있는 response인가?"를 물어야 한다.

## commit 경계에서 실제로 달라지는 것

Spring MVC 소스 기준으로 보면 경계가 분명하다.

- `DispatcherServlet.processHandlerException(...)`는 response가 아직 commit되지 않았다면 content type/body buffer를 비우고 resolver chain을 다시 태울 수 있다
- `ResponseEntityExceptionHandler.handleExceptionInternal(...)`는 response가 이미 commit된 경우 `null`을 돌려 더 이상 응답을 덮어쓰지 않는다
- `DefaultHandlerExceptionResolver.handleErrorResponse(...)`도 commit 전에는 `sendError(...)`를 호출하지만, commit 후에는 "response committed already" 경고만 남긴다
- async write wrapper는 write failure, container `onError`, async completion 뒤 재사용을 `AsyncRequestNotUsableException`으로 묶어 response unusable 상태를 명시한다

즉 같은 예외라도 "언제 드러났는가"에 따라 의미가 달라진다.

```text
handler mapping / binding / controller / advice / converter
-> 예외 발생
-> (미commit) DispatcherServlet.processHandlerException(...)
-> resolver chain 또는 /error fallback
-> ProblemDetail 후보 유지
```

```text
first byte flush / buffer overflow / streaming send
-> response committed
-> 이후 write/flush에서 예외
-> resolver가 와도 status/body 재작성 불가 또는 response unusable
-> broken pipe / connection reset / AsyncRequestNotUsableException / partial response
```

## 이 matrix를 읽는 법

- `가능`: commit 전이라 `ProblemDetail`로 번역될 여지가 남아 있다
- `조건부`: 예외 종류만으론 부족하고, 첫 바이트가 이미 나갔는지 확인해야 한다
- `불가`: commit됐거나 response가 unusable해서 socket/write 문제로 봐야 한다

## Before-After Commit Matrix

| 실패 구간 | 대표 예외/신호 | 최초 관측 지점 | `ProblemDetail` 가능성 | 왜 그렇게 갈리나 |
|---|---|---|---|---|
| handler mapping, method mismatch, media type mismatch, binding/validation 실패 | `NoHandlerFoundException`, `NoResourceFoundException`, `HttpRequestMethodNotSupportedException`, `HttpMediaTypeNotSupportedException`, `MissingServletRequestParameterException`, `MethodArgumentNotValidException`, `HandlerMethodValidationException` | body write 전 dispatcher 단계 | 가능 | Spring MVC 기본 예외 상당수는 `ErrorResponse` 축에 올라가며, response가 untouched 상태라 resolver 또는 `/error`가 최종 body를 고를 수 있다 |
| controller/service 예외가 body write 전에 발생 | custom domain exception, `ErrorResponseException`, `@ExceptionHandler` 대상 예외 | handler 실행 중 | 가능 | `@ExceptionHandler`나 `ResponseEntityExceptionHandler`가 status와 `ProblemDetail` body를 함께 만들 수 있다 |
| async timeout이 첫 바이트 전에 발생 | `AsyncRequestTimeoutException` | async redispatch timeout | 가능 | timeout도 여전히 HTTP 오류로 번역 가능한 예외라서, response가 미commit이면 503 `ProblemDetail` 후보로 남는다 |
| `ResponseBodyAdvice`, converter 선택, serialization 단계에서 실패하지만 아직 미commit | `HttpMediaTypeNotAcceptableException`, `HttpMessageNotWritableException`, advice 내부 예외 | return value handling / converter write 직전 | 조건부 | 예외 자체는 번역 가능하지만, 실제로 첫 write/flush 전인지 확인해야 한다. 미commit이면 dispatcher가 buffer를 비우고 다시 오류 경로를 탈 수 있다 |
| `HttpMessageNotWritableException`가 partial write 뒤 드러남 | JSON serialization error on flush, converter write 중간 실패 | converter write 이후 flush | 불가 | 예외 이름은 같아도 이미 commit됐다면 `handleExceptionInternal(...)`가 빠지고, 남는 것은 partial body나 write failure다 |
| resolver chain 밖으로 튕겼지만 servlet error dispatch로 아직 넘어갈 수 있음 | unresolved MVC exception, `sendError(...)` 경로 | `/error` fallback 진입 직전 | 가능 | Boot fallback path도 결국 uncommitted response를 전제로 작동한다. 이 축이 살아 있으면 `ProblemDetail` 같은 표준 body로 재구성할 여지가 있다 |
| streaming endpoint가 시작되기 전 setup 단계 실패 | 첫 `emitter.send(...)` 전 예외, 첫 `flush()` 전 `StreamingResponseBody` 준비 실패 | streaming return value setup | 조건부 | headers/status는 아직 바꿀 수 있을 수 있지만, first-byte가 이미 나갔는지 여부가 결정적이다 |
| `StreamingResponseBody`, `ResponseBodyEmitter`, `SseEmitter`가 첫 send/flush 뒤 실패 | `IOException`, `ClientAbortException`, broken pipe, connection reset | subsequent send/write/flush | 불가 | stream은 이미 commit됐고, `completeWithError(...)`도 JSON 재작성기가 아니라 async lifecycle 종료 신호에 가깝다 |
| async response가 write failure나 container `onError` 뒤 unusable 상태가 됨 | `AsyncRequestNotUsableException`, disconnected client signal | wrapped response write, async listener `onError` | 불가 | Spring은 이 상태를 "response not usable"로 본다. `ResponseEntityExceptionHandler`는 `null`, `DefaultHandlerExceptionResolver`는 no-op로 빠진다 |

## 회색 지대 3개

### 1. `HttpMessageNotWritableException`는 예외 이름만으로 분류하면 틀린다

이 예외는 commit 경계를 가르는 대표 사례다.

- converter 선택 직후, 첫 바이트 전 -> 아직 `ProblemDetail` 후보
- converter가 일부 bytes를 밀어낸 뒤 -> 더 이상 `ProblemDetail`로 갈아엎을 수 없음

즉 "직렬화 예외 = 500 `ProblemDetail`"로 외우면 안 된다.

세부 4분할은 [Spring `HttpMessageNotWritableException` Failure Taxonomy](./spring-httpmessagenotwritableexception-failure-taxonomy.md)에서 따로 정리한다.

### 2. `AsyncRequestTimeoutException`도 streaming 이후에는 색이 바뀐다

async timeout은 원칙적으로 503 오류 후보다.

하지만 SSE나 스트리밍 다운로드가 이미 첫 event/chunk를 보냈다면, 그 뒤 timeout/close는 새로운 오류 body가 아니라 열린 채널 종료에 가깝다.

즉 async timeout도 "언제 timeout이 surface됐는가"를 봐야 한다.

### 3. `completeWithError(...)`는 error contract 복구 버튼이 아니다

`ResponseBodyEmitter` 계열에서 흔한 오해다.

- commit 전 -> async result를 오류로 마감하며 error path로 이어질 수 있다
- commit 후 -> 이미 열린 stream을 끝내는 신호일 뿐, `ProblemDetail` 재작성 보장은 없다

특히 `ResponseBodyEmitter`는 `send(...)`마다 flush하고, `StreamingResponseBody`는 애플리케이션 `flush()` 또는 callback 종료 시 flush되므로 commit 시점이 생각보다 빨리 온다.

## 운영에서 바로 쓰는 판별법

### 1. 로그에 `Response already committed`가 보이면 빨간 구간이다

이 메시지가 보이면 resolver 문제가 아니라 commit 경계를 이미 넘은 것이다.

다음에 볼 것은 `@ExceptionHandler` 구현이 아니라:

- 첫 바이트가 언제 나갔는지
- streaming/flush cadence가 어땠는지
- client disconnect가 먼저였는지

### 2. `AsyncRequestNotUsableException`는 transport 신호로 읽는다

이 예외는 "적절한 `ProblemDetail`을 못 만들었다"보다 "이제 response에 쓸 수 없다"에 가깝다.

따라서 이 신호가 보이면 분류 우선순위는:

- client abort / proxy timeout / async completion race
- SSE heartbeat 부재
- streaming producer cancellation 누락

순으로 잡는 편이 맞다.

### 3. `ProblemDetail`이 안 보인다고 resolver 등록만 의심하면 늦다

먼저 다음 질문을 던져야 한다.

```text
1. 예외가 first byte 전이었는가 후였는가?
2. response가 commit됐는가?
3. 채널이 이미 unusable했는가?
4. 그 다음에야 resolver/advice/error dispatch 구성이 충분한가?
```

## 주의: "가능"은 "자동"이 아니다

이 matrix의 `가능`은 "Spring이 아직 `ProblemDetail`로 번역할 수 있는 물리적 상태다"라는 뜻이지, 애플리케이션이 반드시 RFC 9457 body를 보낸다는 뜻은 아니다.

실제 출력은 여전히 애플리케이션 계약에 달려 있다.

- `@RestControllerAdvice` + `ResponseEntityExceptionHandler`를 쓰는가
- custom `@ExceptionHandler`가 `ProblemDetail` 또는 `ErrorResponse`를 반환하는가
- Boot `/error` fallback도 같은 오류 포맷으로 맞춰 두었는가

즉 번역 축이 비어 있으면, commit 전이어도 단순 `sendError(...)`나 기본 error JSON/HTML로 끝날 수 있다.

## 꼬리질문

> Q: 왜 같은 `HttpMessageNotWritableException`인데 어떤 요청은 500 `ProblemDetail`, 어떤 요청은 socket error처럼 끝나는가?
> 의도: commit 경계와 write 시점 구분 확인
> 핵심: 예외 이름보다 first byte 전/후가 먼저 갈리기 때문이다.

> Q: `AsyncRequestNotUsableException`를 application exception처럼 다루면 왜 안 되는가?
> 의도: response unusable 상태 이해 확인
> 핵심: 이 예외는 "오류 body를 만들지 못했다"보다 "더 이상 쓸 response가 없다"를 뜻한다.

> Q: `/error` fallback은 언제까지 `ProblemDetail` 후보인가?
> 의도: fallback path와 commit 경계 이해 확인
> 핵심: servlet error dispatch도 response가 아직 commit되지 않았을 때만 최종 body ownership을 가질 수 있다.

> Q: streaming endpoint에서 `completeWithError(...)`를 호출하면 왜 항상 JSON 오류로 안 바뀌는가?
> 의도: emitter lifecycle과 commit 경계 이해 확인
> 핵심: 이미 첫 event/chunk가 나간 뒤라면 그 호출은 계약 재작성보다 stream 종료 신호에 가깝다.

## 한 줄 정리

`ProblemDetail` 여부는 예외 종류보다 먼저 "response가 아직 uncommitted + usable한가"로 갈리며, commit 이후 실패는 resolver chain이 아니라 write/disconnect lifecycle로 해석해야 한다.
