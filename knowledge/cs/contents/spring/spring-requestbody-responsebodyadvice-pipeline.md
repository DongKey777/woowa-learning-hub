# Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline

> 한 줄 요약: `RequestBodyAdvice`와 `ResponseBodyAdvice`는 HTTP body를 읽기 전/후와 쓰기 직전에 개입하는 마지막 훅이지만, 이들은 return value handler가 body 경로를 고른 뒤 converter 주변에서만 힘을 가지므로 response commit과 disconnect 이후까지 복구할 수는 없다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring `HandlerMethodReturnValueHandler` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
> - [Spring `ResponseBodyAdvice` on Streaming Types: `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`](./spring-responsebodyadvice-streaming-types.md)
> - [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)
> - [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
> - [Spring ProblemDetail Error Response Design](./spring-problemdetail-error-response-design.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)

retrieval-anchor-keywords: RequestBodyAdvice, ResponseBodyAdvice, HandlerMethodReturnValueHandler, HttpMessageConverter, beforeBodyRead, afterBodyRead, beforeBodyWrite, controller advice, request body interception, response body interception, response commit timing, StringHttpMessageConverter, ProblemDetail, body envelope, global response envelope, api envelope, ResponseBodyEmitter, SseEmitter, StreamingResponseBody, streaming wire contract

## 핵심 개념

`RequestBodyAdvice`와 `ResponseBodyAdvice`는 HTTP body를 `HttpMessageConverter`가 처리하기 전후에 끼어드는 확장점이다.

- request body를 읽기 전/후
- response body를 쓰기 직전

즉, 요청과 응답의 마지막 변환 단계를 감싸는 고급 훅이다.

## 깊이 들어가기

### 1. advice는 body 경로 안에서만 동작한다

가장 먼저 구분해야 할 점은, advice가 MVC의 모든 응답을 가로채는 것이 아니라는 점이다.

반드시 앞단에서 이미 다음이 결정되어 있어야 한다.

- 요청 쪽: `@RequestBody` 등으로 body를 읽는 경로인지
- 응답 쪽: `HandlerMethodReturnValueHandler`가 view가 아니라 body write 경로를 선택했는지

즉 advice는 "아무 응답이나 후킹하는 만능 레이어"가 아니라, **body converter 바로 주변에서만 동작하는 세부 확장점**이다.

### 2. request body advice는 역직렬화 전후를 본다

```java
public class LoggingRequestBodyAdvice implements RequestBodyAdvice {
}
```

이 지점은 request stream을 다루므로 조심해야 한다.

### 3. response body advice는 직렬화 직전의 마지막 조정 지점이다

```java
public class ProblemDetailResponseAdvice implements ResponseBodyAdvice<Object> {
}
```

이 지점은 response format standardization에 유용하다.

보통 순서는 다음처럼 본다.

```text
controller return
-> return value handler가 body 경로 선택
-> content negotiation / converter 선택
-> ResponseBodyAdvice.beforeBodyWrite
-> HttpMessageConverter.write
-> response buffer flush
-> response commit
```

따라서 `beforeBodyWrite`는 강력하지만, 여전히 **commit 전 단계**라는 제약을 가진다.

### 4. converter보다 앞이나 뒤에서 동작한다

이 문맥은 [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)와 [Spring ConversionService, Formatter, and Binder Pipeline](./spring-conversion-service-formatter-binder-pipeline.md)와 같이 봐야 한다.

### 5. body를 소비하거나 타입을 갑자기 바꾸는 작업은 위험하다

request body를 한번 읽어 버리면 downstream에서 못 읽을 수 있다.

response 쪽도 비슷한 함정이 있다.

- 이미 `StringHttpMessageConverter`가 선택됐는데 advice에서 임의의 DTO envelope로 바꾸면 converter/type 조합이 어긋날 수 있다
- `Resource`, 파일 다운로드, streaming 응답까지 공통 envelope로 감싸려 하면 오히려 HTTP 계약을 망치기 쉽다

즉 `supports(...)`는 "항상 true"가 아니라, **어떤 converter/return type에만 개입할지 좁히는 정책**이어야 한다.

다만 여기서 한 번 더 분리해야 할 점이 있다. `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`는 "advice가 적용되는데 제외해야 하는 특수 케이스"라기보다, 아예 별도 streaming handler가 ownership을 가져가는 경로다. 이 차이는 [Spring `ResponseBodyAdvice` on Streaming Types: `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`](./spring-responsebodyadvice-streaming-types.md)에서 따로 정리한다.

### 6. 에러 표준화와 잘 맞지만 post-commit 복구는 못 한다

`ProblemDetail`로 변환하는 규칙을 response advice에서 공통화할 수 있다.

다만 이건 어디까지나 bytes가 나가기 전 이야기다.

- body write 전 예외 -> advice, resolver, error contract가 개입할 수 있음
- first byte 이후 write 실패 -> broken pipe, connection reset 같은 socket 계열로 보일 수 있음

즉 advice는 **응답 형식을 정돈하는 도구**이지, commit 이후 disconnect를 되돌리는 도구는 아니다.

## 실전 시나리오

### 시나리오 1: 모든 응답을 공통 envelope로 감싸고 싶다

ResponseBodyAdvice가 유용하다.

### 시나리오 2: 요청 payload를 로그에 남기고 싶다

RequestBodyAdvice나 별도 filter가 필요할 수 있지만, body 소비 주의가 필요하다.

### 시나리오 3: 암호화된 body를 복호화해야 한다

converter 이전 단계에서 처리해야 할 수 있다.

### 시나리오 4: `String` 응답에서만 공통 envelope가 깨진다

selected converter가 `StringHttpMessageConverter`일 수 있다.

이 경우는 advice를 더 똑똑하게 제한하거나, 문자열 대신 일관된 JSON 응답 모델을 쓰는 쪽이 낫다.

### 시나리오 5: validation 에러와 success body를 같이 표준화하고 싶다

ProblemDetail과 조합해서 계약을 설계한다.

## 코드로 보기

### ResponseBodyAdvice

```java
@ControllerAdvice
public class ApiEnvelopeAdvice implements ResponseBodyAdvice<Object> {

    @Override
    public boolean supports(MethodParameter returnType, Class<? extends HttpMessageConverter<?>> converterType) {
        return !StringHttpMessageConverter.class.isAssignableFrom(converterType);
    }

    @Override
    public Object beforeBodyWrite(Object body, MethodParameter returnType, MediaType selectedContentType,
                                  Class<? extends HttpMessageConverter<?>> selectedConverterType,
                                  ServerHttpRequest request, ServerHttpResponse response) {
        return body;
    }
}
```

### RequestBodyAdvice

```java
@ControllerAdvice
public class DecryptionRequestBodyAdvice extends RequestBodyAdviceAdapter {
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| body advice | 중앙집중식 처리 | stream/body 소비 위험 | 표준화, 암호화 |
| controller advice | 예외 처리와 잘 맞는다 | body 자체 변환에는 약하다 | error contract |
| filter | 가장 앞단이다 | converter 문맥이 약하다 | raw request logging |

핵심은 advice를 "만능 후킹"으로 보지 말고, **HttpMessageConverter 바로 주변의 마지막 변환층이자 commit 전 조정 지점**으로 보는 것이다.

## 꼬리질문

> Q: `RequestBodyAdvice`와 `ResponseBodyAdvice`는 어디에 끼어드는가?
> 의도: converter 전후 확장점 이해 확인
> 핵심: HttpMessageConverter 전후다.

> Q: request body advice에서 가장 큰 위험은 무엇인가?
> 의도: body 소비 위험 이해 확인
> 핵심: 요청 body를 한 번 읽으면 downstream에서 못 읽을 수 있다.

> Q: response body advice는 왜 유용한가?
> 의도: 응답 표준화 이해 확인
> 핵심: 공통 envelope나 ProblemDetail 변환에 쓰기 좋다.

> Q: response body advice가 disconnect까지 처리해 주지 못하는 이유는 무엇인가?
> 의도: commit 이후 경계 이해 확인
> 핵심: advice는 직렬화 직전까지만 개입하고, 실제 socket write 실패는 그 뒤에 드러날 수 있기 때문이다.

> Q: filter와 advice의 차이는 무엇인가?
> 의도: 서블릿 vs MVC 변환층 구분 확인
> 핵심: filter는 raw request, advice는 body converter 근처다.

## 한 줄 정리

RequestBodyAdvice와 ResponseBodyAdvice는 HttpMessageConverter 전후를 가로채는 마지막 body 확장점이지만, 힘이 가장 큰 곳은 commit 전까지만이므로 표준화와 변환에 쓰되 body 소비와 post-commit 한계를 같이 봐야 한다.
