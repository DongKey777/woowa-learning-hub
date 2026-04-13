# Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline

> 한 줄 요약: `RequestBodyAdvice`와 `ResponseBodyAdvice`는 HTTP body를 읽고 쓰는 마지막 가로채기 지점이라, 로깅·암호화·표준화에는 유용하지만 body 소비와 converter 순서를 잘못 건드리면 쉽게 망가진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)
> - [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
> - [Spring ProblemDetail Error Response Design](./spring-problemdetail-error-response-design.md)

retrieval-anchor-keywords: RequestBodyAdvice, ResponseBodyAdvice, HttpMessageConverter, beforeBodyRead, afterBodyRead, beforeBodyWrite, controller advice, request body interception, response body interception

## 핵심 개념

`RequestBodyAdvice`와 `ResponseBodyAdvice`는 HTTP body를 `HttpMessageConverter`가 처리하기 전후에 끼어드는 확장점이다.

- request body를 읽기 전/후
- response body를 쓰기 전/후

즉, 요청과 응답의 마지막 변환 단계를 감싸는 고급 훅이다.

## 깊이 들어가기

### 1. request body advice는 역직렬화 전후를 본다

```java
public class LoggingRequestBodyAdvice implements RequestBodyAdvice {
}
```

이 지점은 request stream을 다루므로 조심해야 한다.

### 2. response body advice는 직렬화 전후를 본다

```java
public class ProblemDetailResponseAdvice implements ResponseBodyAdvice<Object> {
}
```

이 지점은 response format standardization에 유용하다.

### 3. converter보다 앞이나 뒤에서 동작한다

이 문맥은 [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)와 [Spring ConversionService, Formatter, and Binder Pipeline](./spring-conversion-service-formatter-binder-pipeline.md)와 같이 봐야 한다.

### 4. body를 소비하는 작업은 위험하다

request body를 한번 읽어 버리면 downstream에서 못 읽을 수 있다.

### 5. 에러 표준화와 잘 맞는다

`ProblemDetail`로 변환하는 규칙을 response advice에서 공통화할 수 있다.

## 실전 시나리오

### 시나리오 1: 모든 응답을 공통 envelope로 감싸고 싶다

ResponseBodyAdvice가 유용하다.

### 시나리오 2: 요청 payload를 로그에 남기고 싶다

RequestBodyAdvice나 별도 filter가 필요할 수 있지만, body 소비 주의가 필요하다.

### 시나리오 3: 암호화된 body를 복호화해야 한다

converter 이전 단계에서 처리해야 할 수 있다.

### 시나리오 4: validation 에러와 success body를 같이 표준화하고 싶다

ProblemDetail과 조합해서 계약을 설계한다.

## 코드로 보기

### ResponseBodyAdvice

```java
@ControllerAdvice
public class ApiEnvelopeAdvice implements ResponseBodyAdvice<Object> {

    @Override
    public boolean supports(MethodParameter returnType, Class<? extends HttpMessageConverter<?>> converterType) {
        return true;
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

핵심은 advice를 "만능 후킹"으로 보지 말고, **HttpMessageConverter 바로 주변의 마지막 변환층**으로 보는 것이다.

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

> Q: filter와 advice의 차이는 무엇인가?
> 의도: 서블릿 vs MVC 변환층 구분 확인
> 핵심: filter는 raw request, advice는 body converter 근처다.

## 한 줄 정리

RequestBodyAdvice와 ResponseBodyAdvice는 HttpMessageConverter 전후를 가로채는 마지막 body 확장점이라, 표준화와 변환에 강하지만 스트림 소비를 조심해야 한다.
