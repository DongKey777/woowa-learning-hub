---
schema_version: 3
title: Spring HandlerMethodReturnValueHandler Chain
concept_id: spring/handlermethodreturnvaluehandler-chain
canonical: true
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
review_feedback_tags:
- handlermethodreturnvaluehandler-chain
- handlermethodreturnvaluehandler
- mvc-return-value
- handler
aliases:
- HandlerMethodReturnValueHandler
- Spring MVC return value handler
- ResponseEntity handler
- RequestResponseBodyMethodProcessor
- ResponseBodyEmitterReturnValueHandler
- StreamingResponseBodyReturnValueHandler
- response commit timing
intents:
- deep_dive
- troubleshooting
linked_paths:
- contents/spring/spring-mvc-request-lifecycle.md
- contents/spring/spring-requestbody-responsebodyadvice-pipeline.md
- contents/spring/spring-responsebodyadvice-streaming-types.md
- contents/spring/spring-content-negotiation-pitfalls.md
- contents/spring/spring-mvc-async-deferredresult-callable-dispatch.md
- contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md
- contents/spring/spring-mvc-exception-resolver-chain-contract.md
expected_queries:
- Spring MVC 컨트롤러 반환값은 어떤 handler chain이 처리해?
- ResponseEntity와 @ResponseBody plain object는 내부 경로가 어떻게 달라?
- HandlerMethodReturnValueHandler가 async나 streaming 반환값을 어떻게 분기해?
- response commit 이후에는 왜 exception resolver가 응답을 바꾸기 어려워?
contextual_chunk_prefix: |
  이 문서는 Spring MVC HandlerMethodReturnValueHandler chain이 controller
  return value를 model/view, body write, async, streaming 경로로 해석하는 방식을
  설명한다. ResponseEntity, @ResponseBody, ProblemDetail, Callable,
  DeferredResult, ResponseBodyEmitter, SseEmitter, StreamingResponseBody와
  response commit timing을 연결하는 deep dive다.
---
# Spring `HandlerMethodReturnValueHandler` Chain

> 한 줄 요약: Spring MVC에서 컨트롤러 반환값은 그대로 응답이 되는 것이 아니라 `HandlerMethodReturnValueHandler` 체인이 model/view, body write, async/streaming 중 어느 경로로 보낼지 결정한 결과이므로, body pipeline과 response commit 시점까지 같이 이해해야 disconnect와 에러 계약이 왜 달라지는지 풀린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline](./spring-requestbody-responsebodyadvice-pipeline.md)
> - [Spring `ResponseBodyAdvice` on Streaming Types: `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`](./spring-responsebodyadvice-streaming-types.md)
> - [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)

retrieval-anchor-keywords: HandlerMethodReturnValueHandler, ResponseEntity, @ResponseBody, HttpEntityMethodProcessor, RequestResponseBodyMethodProcessor, ModelAndViewMethodReturnValueHandler, ViewNameMethodReturnValueHandler, ResponseBodyEmitterReturnValueHandler, StreamingResponseBodyReturnValueHandler, ResponseBodyAdvice, response commit timing, flushBuffer, broken pipe, client abort, disconnect handling

## 핵심 개념

컨트롤러 메서드가 `return`했다고 해서 HTTP 응답이 이미 완성된 것은 아니다.

Spring MVC는 반환값을 별도 체인으로 해석한 뒤, 크게 세 갈래 중 하나로 보낸다.

- model/view 경로: `ModelAndView`, view name, `View`를 만든다
- body 경로: `ResponseEntity`, `@ResponseBody`, `ProblemDetail` 등을 body write 파이프라인으로 보낸다
- async/streaming 경로: `Callable`, `DeferredResult`, `ResponseBodyEmitter`, `StreamingResponseBody`처럼 응답 시점을 뒤로 미루거나 여러 조각으로 쓴다

즉 핵심은 타입 이름이 아니라, **어떤 return value handler가 이 반환값에 어떤 HTTP 계약을 부여했는가**다.

## 깊이 들어가기

### 1. 반환값 handler는 MVC의 마지막 의미 결정 단계다

메서드 인자가 `HandlerMethodArgumentResolver` 체인으로 채워지듯, 반환값도 `HandlerMethodReturnValueHandler` 체인이 맡는다.

여기서 실제로 결정되는 것은 "자바 객체를 어떻게 볼 것인가"가 아니다.

- 아직 view resolution이 필요한가
- 이미 response를 직접 다루는가
- 지금 쓰는가, 나중에 쓰는가

이 단계가 끝나면 `ModelAndViewContainer`는 보통 둘 중 하나가 된다.

- model/view 정보가 채워진다
- `requestHandled=true`가 되어 "응답은 이미 직접 처리 중"이라고 표시된다

그래서 같은 `String`도 맥락에 따라 전혀 다르게 끝난다.

- `@Controller` + `String` -> 대개 view name
- `@ResponseBody`/`@RestController` + `String` -> 대개 plain text body

### 2. 대표 handler를 묶어서 보면 헷갈림이 줄어든다

| 반환값 형태 | 대표 handler | 무엇을 결정하는가 | 결과 |
|---|---|---|---|
| `ModelAndView`, `View` | `ModelAndViewMethodReturnValueHandler` 등 | model/view 렌더링 경로 | view resolver 또는 직접 view render |
| `String` view name | `ViewNameMethodReturnValueHandler` | 문자열을 view name으로 해석 | 템플릿/페이지 렌더링 |
| `HttpEntity`, `ResponseEntity` | `HttpEntityMethodProcessor` | status, headers, body를 함께 소유 | 직접 HTTP 응답 작성 |
| `@ResponseBody`, `@RestController` plain object, `ProblemDetail` | `RequestResponseBodyMethodProcessor` | body write 경로 선택 | `HttpMessageConverter` 직렬화 |
| `Callable`, `WebAsyncTask`, `DeferredResult` | async 계열 handler | 즉시 쓰지 않고 나중에 완료 | servlet async + redispatch |
| `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody` | streaming 계열 handler | body를 여러 조각 또는 스트림으로 작성 | early commit 가능성이 높음 |

핵심은 `ResponseEntity`와 plain object가 "둘 다 JSON 응답"처럼 보일 수 있어도, 내부적으로는 다른 handler가 다른 책임을 가진다는 점이다.

### 3. body 응답의 실제 파이프라인은 handler 선택 다음부터 시작된다

body 경로에서는 보통 다음 순서로 흐른다.

```text
controller return
-> HandlerMethodReturnValueHandler 선택
-> (ResponseEntity면 status/headers 먼저 반영)
-> content negotiation / HttpMessageConverter 선택
-> ResponseBodyAdvice.beforeBodyWrite
-> HttpMessageConverter.write
-> servlet response buffer flush
-> response commit
-> socket write 중 disconnect 가능
```

여기서 중요한 포인트는 두 가지다.

1. return value handler가 body 경로를 골라야 그 다음 converter/advice가 개입한다.
2. response commit은 컨트롤러 리턴 시점이 아니라, 실제 bytes가 buffer 밖으로 밀려나가는 시점에 더 가깝다.

즉 "응답을 만든다"는 말 안에도 의미 해석, 직렬화, 실제 네트워크 write가 분리되어 있다.

### 4. `ResponseEntity`는 body wrapper가 아니라 응답 모델이다

`ResponseEntity`를 반환하면 handler는 다음을 함께 본다.

- HTTP status
- headers
- body

그래서 plain object 반환과 가장 큰 차이는 "바디만 넘기는가"가 아니라, **컨트롤러가 HTTP 메타데이터의 ownership까지 가져가는가**다.

예를 들어 `ResponseEntity<Void>`는 body가 없어도 의미가 충분하다.

- `204 No Content`
- `Location` 헤더만 있는 응답
- 캐시 무효화 같은 헤더 중심 응답

즉 이 경우는 converter보다 먼저 HTTP 계약이 거의 완성된다.

### 5. `ResponseBodyAdvice`는 pre-write 훅이지 post-commit 훅이 아니다

반환값이 body로 해석된 뒤에는 `ResponseBodyAdvice`가 공통 envelope, `ProblemDetail` 표준화, 헤더 조정 같은 후처리를 할 수 있다.

하지만 이 지점에서 아직 중요한 제약이 남아 있다.

- advice는 선택된 converter와 media type 문맥 안에서 동작한다
- advice가 끝난 뒤 실제 byte write는 converter가 한다
- advice는 "클라이언트가 진짜로 이 바이트를 받았는가"를 보장하지 못한다

즉 `beforeBodyWrite`는 강력하지만, 어디까지나 **직렬화 직전의 마지막 조정 지점**이다.

그래서 global envelope를 만들 때도 `String`, `Resource`, streaming 응답을 같이 감싸려 하면 쉽게 깨진다.

### 6. response commit 시점은 생각보다 늦고, 한번 지나가면 되돌리기 어렵다

가장 흔한 오해는 "컨트롤러가 `return`했으니 이미 응답이 나갔다"는 것이다.

실제로는 다음 조건 중 하나에서 commit이 발생한다.

- response buffer가 차서 컨테이너가 flush한다
- 코드가 `flushBuffer()` 또는 streaming write를 유도한다
- message converter가 큰 body를 쓰며 사실상 바로 flush된다
- 요청 종료 시 컨테이너가 최종 flush한다

commit 전에는 비교적 유연하다.

- status/headers를 바꿀 수 있다
- body write 전에 예외가 나면 resolver나 error path가 개입할 여지가 있다

commit 후에는 성격이 달라진다.

- 헤더와 상태 코드를 사실상 다시 쓸 수 없다
- partial body가 이미 나갔다면 JSON error contract로 갈아엎기 어렵다
- 남는 것은 connection close, log, metrics, tracing 같은 사후 관측이 많다

즉 "왜 어떤 예외는 `ProblemDetail`로 오고 어떤 예외는 그냥 socket error로 끝나지?"라는 질문은 대부분 commit 경계에서 갈린다.

### 7. disconnect는 controller return보다 write 시점에서 더 자주 드러난다

클라이언트나 프록시가 이미 연결을 닫았더라도 서버는 당장 모를 수 있다.

특히 다음 패턴이 흔하다.

1. 비즈니스 로직은 정상 종료
2. Spring이 return value handler와 converter를 거쳐 응답을 쓰려 함
3. 첫 write 또는 다음 flush에서 broken pipe / connection reset이 드러남

즉 disconnect는 "실패가 어디서 났는가"보다, **서버가 언제 peer 종료를 관측했는가**의 문제다.

이 차이는 streaming에서 더 커진다.

- `SseEmitter`, `ResponseBodyEmitter`, `StreamingResponseBody`는 첫 chunk로 빨리 commit될 수 있다
- 이후 chunk write에서 disconnect가 드러나면 정상적인 API 에러 envelope로 바꾸기 어렵다
- async worker는 일을 끝냈어도, 이미 응답 채널은 unusable할 수 있다

그래서 disconnect handling은 return value handler와 network lifecycle을 같이 봐야 풀린다.

### 8. 진단은 "어느 층에서 실패했는가"로 자르는 것이 빠르다

| 관측 증상 | 먼저 의심할 층 | 왜 그런가 |
|---|---|---|
| `String`이 JSON이 아니라 view처럼 동작 | return value handler 선택 | 같은 타입도 view/body 맥락이 다르다 |
| `ResponseEntity` 상태 코드는 맞는데 body 포맷이 이상함 | converter 또는 `ResponseBodyAdvice` | handler 이후 body pipeline 문제다 |
| 공통 envelope가 `String` 응답에서만 깨짐 | converter 선택과 advice 변환 | `StringHttpMessageConverter` 경로일 수 있다 |
| 예외가 `ProblemDetail` 대신 broken pipe로 남음 | response commit 이후 write 실패 | HTTP 계약 일부가 이미 나갔을 수 있다 |
| async 응답이 늦게 끝나며 간헐적 disconnect | async/streaming handler + network timeout | 작업 완료와 응답 가능성이 분리된다 |

## 실전 시나리오

### 시나리오 1: `String`을 리턴했는데 JSON이 아니라 뷰 이름처럼 동작한다

return value handler가 view name 경로로 해석한 것이다.

문제의 핵심은 `String` 자체가 아니라, 그 문자열을 누가 처리했는가다.

### 시나리오 2: `ResponseEntity<Void>`는 body가 없는데도 응답이 "완성"된다

이 경우는 body가 비어 있어도 status와 headers만으로 HTTP 의미가 충분하다.

즉 converter가 핵심이 아니라 handler가 응답 계약을 먼저 닫아 버린 셈이다.

### 시나리오 3: `ProblemDetail`은 잘 오는데 어떤 예외는 소켓 에러만 남는다

commit 전 예외는 `ProblemDetail` 같은 오류 계약으로 번역될 수 있다.

하지만 partial write 이후 실패라면 이미 응답 일부가 밖으로 나갔을 수 있어, 같은 방식으로 복구되지 않는다.

### 시나리오 4: `StreamingResponseBody`는 첫 바이트는 빠른데 중간에 broken pipe가 난다

스트리밍 응답은 첫 chunk에서 빠르게 commit될 수 있다.

그래서 중간 disconnect는 보통 "응답 생성 실패"라기보다 "이미 열린 스트림 write 실패"로 보인다.

## 코드로 보기

### plain object

```java
@GetMapping("/orders/{id}")
public OrderResponse get(@PathVariable Long id) {
    return orderService.find(id);
}
```

### explicit HTTP response

```java
@GetMapping("/orders/{id}")
public ResponseEntity<OrderResponse> get(@PathVariable Long id) {
    return ResponseEntity.ok()
            .header("X-Request-Handled-By", "controller")
            .body(orderService.find(id));
}
```

### ambiguous `String`

```java
@Controller
public class PageController {

    @GetMapping("/home")
    public String home() {
        return "home";
    }
}
```

### streaming response

```java
@GetMapping("/download")
public ResponseEntity<StreamingResponseBody> download() {
    StreamingResponseBody body = outputStream -> {
        outputStream.write("chunk-1\n".getBytes(StandardCharsets.UTF_8));
        outputStream.flush();
        outputStream.write("chunk-2\n".getBytes(StandardCharsets.UTF_8));
    };

    return ResponseEntity.ok(body);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| plain object + `@ResponseBody` | 단순하다 | status/header 제어가 덜 직접적이다 | 일반 JSON API |
| `ResponseEntity` | HTTP 응답 의미가 명확하다 | 코드가 조금 더 장황하다 | 상태/헤더를 직접 제어할 때 |
| `String` view name | 서버 렌더링에 자연스럽다 | REST 맥락에선 가장 헷갈린다 | 템플릿 렌더링 |
| async/streaming 반환 타입 | 긴 작업과 스트리밍에 적합하다 | commit/disconnect/timeout 모델이 복잡하다 | SSE, 다운로드, 장시간 처리 |

핵심은 반환값을 "메서드 리턴값"이 아니라, **MVC가 HTTP 의미와 응답 lifecycle로 번역하는 입력**으로 보는 것이다.

## 꼬리질문

> Q: `ResponseEntity`가 plain object 반환과 다른 점은 무엇인가?
> 의도: 반환값의 HTTP ownership 이해 확인
> 핵심: body뿐 아니라 status와 headers까지 함께 표현한다.

> Q: return value handler와 message converter의 차이는 무엇인가?
> 의도: 의미 해석과 직렬화 구분 확인
> 핵심: 전자는 어떤 HTTP 경로로 갈지 정하고, 후자는 실제 바이트로 쓴다.

> Q: response commit 시점이 중요한 이유는 무엇인가?
> 의도: 오류 계약 경계 이해 확인
> 핵심: commit 전에는 응답을 바꿀 여지가 있지만, commit 후에는 partial response나 socket error로 성격이 달라진다.

> Q: disconnect가 왜 controller return 시점이 아니라 write 시점에서 자주 드러나는가?
> 의도: network lifecycle 관측 시점 이해 확인
> 핵심: peer 종료는 대개 첫 write/flush 때 관측되기 때문이다.

## 한 줄 정리

컨트롤러 반환값은 그대로 응답이 되는 것이 아니라, `HandlerMethodReturnValueHandler` 체인이 HTTP 의미와 body write 경로를 정하고, 그 뒤의 commit/disconnect 경계가 최종 관측 결과를 바꾼다.
