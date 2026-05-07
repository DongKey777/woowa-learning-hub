---
schema_version: 3
title: Spring ProblemDetail vs Error Handoff Matrix
concept_id: spring/problemdetail-vs-error-handoff-matrix
canonical: true
category: spring
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- problemdetail-vs-error
- handoff
- error-handoff
- unresolved-mvc-exception
aliases:
- ProblemDetail vs /error
- Spring error handoff
- unresolved MVC exception
- error dispatch handoff
- BasicErrorController fallback
- response commit breaks error dispatch
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/spring/spring-problemdetail-before-after-commit-matrix.md
- contents/spring/spring-httpmessagenotwritableexception-failure-taxonomy.md
- contents/spring/spring-basicerrorcontroller-errorattributes-whitelabel-boundaries.md
- contents/spring/spring-mvc-exception-resolver-chain-contract.md
- contents/spring/spring-handlermethodreturnvaluehandler-chain.md
- contents/spring/spring-requestbody-responsebodyadvice-pipeline.md
- contents/spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md
- contents/spring/spring-servlet-container-disconnect-exception-mapping.md
confusable_with:
- spring/problemdetail-before-after-commit-matrix
- spring/httpmessagenotwritableexception-failure-taxonomy
- spring/basicerrorcontroller-errorattributes-whitelabel-boundaries
- spring/mvc-exception-resolver-chain-contract
symptoms:
- ControllerAdvice가 처리하지 못한 예외가 /error로 넘어갈 때와 안 넘어갈 때가 섞인다.
- BasicErrorController가 기대한 JSON을 만들지 않고 response already committed 로그가 보인다.
- streaming 응답 첫 바이트 이후 예외가 ProblemDetail이나 /error로 변환되지 않는다.
expected_queries:
- Spring ProblemDetail과 /error fallback은 언제 handoff돼?
- unresolved MVC exception이 BasicErrorController로 넘어가지 않는 이유는?
- response commit 이후에는 왜 /error dispatch가 끊겨?
- HandlerExceptionResolver가 최종 응답 ownership을 잡는다는 말이 뭐야?
contextual_chunk_prefix: |
  이 문서는 Spring MVC 예외가 ProblemDetail, HandlerExceptionResolver, Boot /error,
  BasicErrorController 중 어디로 handoff되는지 response commit 전후와 resolver ownership으로
  나누어 진단한다. 첫 바이트 이후에는 오류 응답 계약으로 복구할 수 없다는 점을 강조한다.
---
# Spring `ProblemDetail` vs `/error` Handoff Matrix

> 한 줄 요약: unresolved MVC exception이 Boot `/error` fallback으로 넘어가려면 "resolver chain이 최종 응답 ownership을 잡지 못했고, servlet/container가 아직 error dispatch를 걸 수 있으며, response가 미commit 상태"여야 하고, 첫 바이트 이후에는 그 handoff가 끊긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
> - [Spring `HttpMessageNotWritableException` Failure Taxonomy](./spring-httpmessagenotwritableexception-failure-taxonomy.md)
> - [Spring `BasicErrorController`, `ErrorAttributes`, and Whitelabel Error Boundaries](./spring-basicerrorcontroller-errorattributes-whitelabel-boundaries.md)
> - [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
> - [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
> - [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](./spring-onceperrequestfilter-async-error-dispatch-traps.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)

retrieval-anchor-keywords: ProblemDetail, /error handoff, BasicErrorController, ErrorAttributes, servlet error dispatch, error page, ErrorPageFilter, ErrorPageCustomizer, RequestDispatcher.ERROR_STATUS_CODE, unresolved MVC exception, DispatcherServlet processHandlerException, HandlerExceptionResolver, ResponseEntityExceptionHandler, DefaultHandlerExceptionResolver, sendError, response committed, resetBuffer, first byte commit, HttpMessageNotWritableException, converter selection failure, serialization failure, first flush, partial response, partial write, streaming error dispatch

## 핵심 개념

이 문맥에서 봐야 할 것은 "예외가 났는가"보다 **지금 누가 응답 ownership을 갖고 있는가**다.

- MVC ownership: `@ExceptionHandler`, `ResponseEntityExceptionHandler`, custom resolver가 이미 status/body를 결정했다. 이 경우 `/error`는 개입하지 않는다.
- servlet error-dispatch ownership: resolver가 `sendError(...)`를 호출했거나, resolver chain이 예외를 못 잡아 `DispatcherServlet` 밖으로 다시 던졌다. 이 경우 container 또는 `ErrorPageFilter`가 `/error`로 넘길 수 있다.
- transport ownership: response가 이미 commit됐거나 write channel이 unusable하다. 이 구간으로 넘어가면 `/error` handoff도, `ProblemDetail` 재작성도 사실상 끝난다.

즉 "unresolved MVC exception = 무조건 `BasicErrorController`"가 아니다.

성립 조건이 하나 더 필요하다.

- response가 아직 commit되지 않았을 것

## `/error` handoff가 실제로 붙는 경로

Spring MVC 쪽 분기와 Boot 쪽 분기를 따로 보면 구조가 선명하다.

```text
request
-> DispatcherServlet
-> processHandlerException(...)
   -> resolver가 ResponseEntity/ModelAndView 반환
      -> MVC가 직접 응답 마감
   -> resolver가 sendError(...) 후 empty ModelAndView 반환
      -> servlet error dispatch ownership으로 handoff
   -> resolver chain이 null, 예외 재throw
      -> servlet/container가 예외를 보고 error dispatch 시도
-> /error
-> BasicErrorController
-> ErrorAttributes 기반 JSON/HTML
```

여기서 Boot는 환경에 따라 `/error`를 붙이는 방식이 다르다.

- executable jar / embedded container: `ErrorMvcAutoConfiguration.ErrorPageCustomizer`가 전역 `ErrorPage("/error")`를 등록한다.
- WAR / 외부 servlet container: `ErrorPageFilter`가 예외나 `sendError`를 가로채 `/error`로 forward한다.

둘 다 공통 전제는 같다.

- **response가 아직 commit되지 않았을 것**

## ProblemDetail vs `/error` ownership matrix

| 마지막으로 일어난 일 | MVC 쪽 상태 | response 상태 | Boot `/error` handoff | 최종 결과 |
|---|---|---|---|---|
| `@ExceptionHandler`, custom `ResponseEntityExceptionHandler`, custom resolver가 `ProblemDetail`/`ErrorResponse` body를 만들어 반환 | MVC가 예외를 이미 소비했다 | 미commit | 아니오 | MVC가 직접 `ProblemDetail` 또는 팀 표준 error body를 응답한다 |
| `DefaultHandlerExceptionResolver` 같은 resolver가 `sendError(...)`를 호출하고 empty `ModelAndView`를 반환 | MVC는 status만 servlet error path로 넘겼다 | 미commit | 예 | container 또는 `ErrorPageFilter`가 `/error`로 넘기고, `BasicErrorController`가 `ErrorAttributes` 기반 응답을 만든다 |
| resolver chain이 예외를 끝내 처리하지 못해 `DispatcherServlet.processHandlerException(...)`가 예외를 다시 던진다 | MVC ownership이 비었다 | 미commit | 예 | container/global error page가 `/error`를 dispatch한다 |
| body write 직전 `HttpMessageNotWritableException`, advice 예외, converter 예외가 났지만 아직 첫 바이트 전이다 | 아직 MVC 또는 servlet error path가 ownership을 가져갈 수 있다 | 미commit | 조건부 가능 | earlier advice/resolver가 바로 `ProblemDetail`을 만들 수도 있고, unresolved면 `/error`로 handoff될 수도 있다 |
| 같은 예외가 partial write 또는 first flush 뒤 surface된다 | MVC가 새 body를 만들 ownership을 잃었다 | commit됨 | 아니오 | partial response, container log, socket/write failure로 끝날 수 있다 |
| `StreamingResponseBody`, `ResponseBodyEmitter`, `SseEmitter`가 첫 chunk/event 뒤 실패한다 | stream lifecycle이 이미 시작됐다 | commit됨 | 아니오 | `completeWithError(...)`나 disconnect 로그는 stream 종료 신호이지 `/error` 재진입이 아니다 |
| async write wrapper가 `AsyncRequestNotUsableException`, disconnected client 같은 unusable 상태를 본다 | write channel 자체가 unusable하다 | commit 또는 unusable | 아니오 | transport 문제로 해석해야 하며, `ProblemDetail`/`/error` 재작성 대상이 아니다 |

핵심은 `/error`가 **미처리 예외**만 보는 것이 아니라, **미commit 상태로 servlet error dispatch ownership까지 넘어온 실패**를 본다는 점이다.

특히 `HttpMessageNotWritableException`는 같은 이름 아래 pre-commit selection/serialization과 post-commit flush/partial-write가 섞이므로, 세부 분류는 [Spring `HttpMessageNotWritableException` Failure Taxonomy](./spring-httpmessagenotwritableexception-failure-taxonomy.md)와 같이 봐야 한다.

## commit이 handoff를 끊는 정확한 지점

실제로 handoff를 막는 코드는 여러 층에 흩어져 있다.

| 코드 지점 | 미commit일 때 | commit 이후 |
|---|---|---|
| `DispatcherServlet.processHandlerException(...)` | `resetBuffer()`로 body buffer를 비우고 resolver chain을 다시 태운다 | `resetBuffer()`가 불가하므로 기존 응답을 유지한 채 resolver만 시도한다 |
| `ResponseEntityExceptionHandler.handleExceptionInternal(...)` | `ProblemDetail`/`ResponseEntity`를 계속 만들 수 있다 | `response.isCommitted()`면 `null`을 반환하고 더 이상 덮어쓰지 않는다 |
| `DefaultHandlerExceptionResolver.handleErrorResponse(...)` / `handleHttpMessageNotWritable(...)` | `sendError(...)`로 servlet error dispatch를 요청한다 | committed면 경고만 남기고 `sendError(...)`를 건너뛴다 |
| Boot `ErrorPageFilter.handleErrorStatus(...)` / `handleException(...)` | `/error`로 forward할 수 있다 | `response.isCommitted()`면 forward를 포기한다 |

그래서 "resolver가 안 잡았는데 왜 `BasicErrorController`가 안 나오지?"라는 질문은 대개 다음 중 하나다.

- 첫 바이트가 이미 나갔다
- streaming/SSE가 이미 시작됐다
- client/proxy disconnect로 response가 unusable해졌다
- resolver가 `sendError(...)` 대신 직접 일부 body를 써 버렸다

## 왜 `/error`가 항상 `ProblemDetail`은 아닌가

이 handoff matrix는 ownership을 설명하는 문서다.

결과 포맷은 별개다.

- MVC advice가 직접 처리하면 `ProblemDetail`을 내보내기 쉽다
- `/error`로 넘어가면 기본값은 `BasicErrorController` + `ErrorAttributes` 기반 JSON/HTML이다
- 따라서 fallback까지 `ProblemDetail`로 통일하려면 `/error` 쪽도 따로 맞춰야 한다

즉 "이번 요청이 `ProblemDetail`이 아니었다"와 "이번 요청이 `/error` handoff를 탔다"는 같은 문장이 아니다.

- `ProblemDetail`이 아니어도 `/error`를 탔을 수 있다
- `ProblemDetail`이어도 `/error`를 전혀 안 탔을 수 있다

## 운영에서 바로 쓰는 판별 순서

### 1. 먼저 resolver 성공 여부보다 first byte 여부를 본다

다음 중 하나라도 보이면 `/error` handoff는 거의 끝난 상태다.

- `Response already committed`
- partial body가 이미 내려감
- streaming/SSE 첫 event 전송 완료
- broken pipe / connection reset / `AsyncRequestNotUsableException`

### 2. 그 다음에 ownership을 분류한다

- MVC advice가 이미 응답을 만들었는가
- resolver가 `sendError(...)`로 servlet 쪽에 넘겼는가
- unresolved 예외가 `DispatcherServlet` 밖으로 다시 던져졌는가

이 순서를 뒤집으면 "왜 `/error`가 안 탔는지"를 resolver 설정 문제로만 오해하기 쉽다.

### 3. 마지막으로 포맷 통일 문제를 본다

ownership이 `/error`였더라도, 실제 body는 다음 중 하나일 수 있다.

- Boot 기본 JSON
- whitelabel / custom HTML
- 커스터마이징한 `ErrorAttributes`
- 커스텀 `ErrorController`

즉 handoff와 payload shape는 따로 읽어야 한다.

## 꼬리질문

> Q: unresolved MVC exception이면 항상 `BasicErrorController`까지 가는가?
> 의도: handoff 조건 확인
> 핵심: 아니다. 미commit 상태로 servlet error dispatch ownership이 남아 있을 때만 간다.

> Q: `sendError(...)`는 곧 response commit을 뜻하는가?
> 의도: servlet error dispatch 이해 확인
> 핵심: 여기서는 "더 늦기 전에 container error path로 ownership을 넘긴다"가 더 중요하다. 이미 commit된 뒤에는 그 요청 자체를 할 수 없다.

> Q: 왜 같은 예외가 어떤 요청에서는 `ProblemDetail`, 어떤 요청에서는 `/error` JSON로 끝나는가?
> 의도: ownership vs payload shape 구분 확인
> 핵심: 전자는 MVC advice가 직접 처리한 것이고, 후자는 servlet error dispatch 이후 `BasicErrorController`가 처리했을 수 있다.

> Q: 왜 streaming endpoint는 unresolved 예외여도 `/error`로 잘 안 가는가?
> 의도: commit 이후 handoff 차단 이해 확인
> 핵심: 첫 chunk/event가 이미 나가면 transport ownership이 시작돼 `/error`가 끼어들 수 없다.

## 한 줄 정리

`/error` fallback은 "예외가 unresolved였다"만으로 열리지 않고, **미commit response 위에서 MVC ownership이 비워진 채 servlet error dispatch ownership으로 넘어갈 때만** 성립한다.
