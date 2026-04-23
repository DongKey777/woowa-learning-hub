# Spring `BasicErrorController`, `ErrorAttributes`, and Whitelabel Error Boundaries

> 한 줄 요약: Spring Boot의 기본 오류 응답은 MVC 예외 처리의 바깥에서도 작동하는 fallback 경로이므로, `BasicErrorController`, `ErrorAttributes`, whitelabel error page 경계를 모르면 왜 어떤 요청은 advice를 타고 어떤 요청은 기본 에러로 떨어지는지 헷갈리기 쉽다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `ProblemDetail` vs `/error` Handoff Matrix](./spring-problemdetail-vs-error-handoff-matrix.md)
> - [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
> - [Spring `ProblemDetail` Error Response Design](./spring-problemdetail-error-response-design.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
> - [Spring Startup Bean Graph Debugging Playbook](./spring-startup-bean-graph-debugging-playbook.md)

retrieval-anchor-keywords: BasicErrorController, ErrorAttributes, whitelabel error page, /error endpoint, /error handoff, servlet error dispatch, response committed, ErrorMvcAutoConfiguration, ErrorPageFilter, default error response, spring boot error handling, fallback error path

## 핵심 개념

Spring MVC 예외 처리를 공부하면 보통 `@ExceptionHandler`, `@ControllerAdvice`, `HandlerExceptionResolver` 체인을 먼저 본다.

하지만 Spring Boot 애플리케이션에는 또 다른 오류 경로가 있다.

- `/error`
- `BasicErrorController`
- `ErrorAttributes`
- whitelabel error page

이건 단순한 "기본 페이지"가 아니라, **MVC 예외 처리에서 못 잡은 실패를 마지막으로 응답으로 바꾸는 fallback 경로**다.

그래서 실무에서 자주 생기는 혼란은 이런 것이다.

- 어떤 예외는 내가 만든 advice가 처리한다
- 어떤 예외는 갑자기 Boot 기본 JSON이나 HTML로 나온다
- 브라우저에선 whitelabel page가 보이는데 API 호출에선 JSON이 보인다

즉 오류 응답을 이해하려면 MVC resolver chain뿐 아니라, **그 바깥의 Boot fallback error path**까지 같이 봐야 한다.

## 깊이 들어가기

### 1. 모든 실패가 `@ControllerAdvice`로 끝나지는 않는다

다음 경우에는 MVC advice만으로 설명이 부족할 수 있다.

- 컨트롤러 이전 필터 단계 실패
- 응답 렌더링 중 실패
- 매핑 실패 후 기본 오류 경로 진입
- 예외가 resolver chain에서 최종적으로 처리되지 않음

이때 Boot는 `/error` 경로를 통해 기본 오류 응답을 만들 수 있다.

즉 `BasicErrorController`는 보통 **마지막 fallback controller**처럼 이해하면 된다.

### 2. `ErrorAttributes`가 오류 모델을 만든다

기본 오류 응답에는 보통 아래 정보가 들어간다.

- timestamp
- status
- error
- path
- message

이런 payload를 구성하는 중심 중 하나가 `ErrorAttributes`다.

즉 `BasicErrorController`가 "어떻게 응답할지"를 담당한다면, `ErrorAttributes`는 **무엇을 담을지**를 만든다.

그래서 오류 응답을 커스터마이징할 때는 단순 advice 추가만이 아니라,

- 기본 fallback path도 바꿀 것인지
- ErrorAttributes를 바꿀 것인지

를 함께 봐야 한다.

### 3. HTML과 JSON이 다르게 느껴지는 이유는 content negotiation 때문이다

같은 `/error` 경로라도 브라우저와 API 클라이언트는 다른 응답을 받을 수 있다.

- 브라우저 요청: HTML/whitelabel page
- API 요청: JSON body

즉 "에러 처리 로직이 두 개다"라기보다, **동일한 fallback error path가 content negotiation에 따라 다르게 보이는 것**일 수 있다.

### 4. Security와 MVC fallback error는 경계가 다르다

보안 실패는 보통 filter chain에서 먼저 정리된다.

그래서 401/403은 `AuthenticationEntryPoint`, `AccessDeniedHandler`가 응답을 만들고, `/error`까지 오지 않을 수 있다.

반면 컨트롤러나 MVC 처리 중 발생한 예외는 resolver chain 또는 `/error`로 이어질 수 있다.

즉 "왜 보안 예외는 whitelabel 안 뜨지?" 같은 질문은 당연한 것이다.

### 5. whitelabel page는 편의이자 함정이다

개발 중에는 기본 에러 페이지가 유용하다.

하지만 운영/API 관점에서는 함정이 될 수 있다.

- HTML page가 API 계약을 깨뜨린다
- 내부 정보가 과하게 드러날 수 있다
- 에러 응답 형식이 팀 표준과 어긋난다

따라서 기본 fallback을 어디까지 허용할지 정책이 필요하다.

### 6. 오류 계약을 진짜 통일하려면 fallback path까지 봐야 한다

팀이 `ProblemDetail`이나 공통 error envelope를 쓰고 싶다면,

- controller advice만 맞추는 것으로 충분한가
- 기본 `/error` 경로도 같은 계약으로 맞출 것인가

를 결정해야 한다.

그렇지 않으면 평소엔 표준 error contract가 나오다가, 특정 실패에서는 기본 Boot error JSON이나 HTML이 튀어나올 수 있다.

## 실전 시나리오

### 시나리오 1: 대부분의 API는 ProblemDetail인데 가끔 기본 JSON 에러가 나온다

그 예외가 MVC advice에서 처리되지 못하고 `/error` fallback path로 갔을 수 있다.

### 시나리오 2: 브라우저에서만 whitelabel error page가 보인다

같은 fallback error path라도 HTML 응답으로 협상됐을 가능성이 높다.

### 시나리오 3: 401/403은 `/error`를 안 타는 것 같다

보안 실패가 filter chain에서 이미 응답 처리됐기 때문이다.

### 시나리오 4: 운영 장애 때 stack trace 대신 너무 빈약한 error body만 보인다

fallback error path의 속성/노출 정책 때문일 수 있다.

이때는 `ErrorAttributes`와 Boot error 설정을 함께 봐야 한다.

## 코드로 보기

### 기본 fallback 경로 감각

```text
request
-> filter chain
-> DispatcherServlet
-> handler / resolver chain
-> if unresolved or fallback needed
-> /error
-> BasicErrorController
```

### ErrorAttributes 커스터마이징 예

```java
@Component
public class ApiErrorAttributes extends DefaultErrorAttributes {

    @Override
    public Map<String, Object> getErrorAttributes(
            WebRequest webRequest,
            ErrorAttributeOptions options) {
        Map<String, Object> attributes = super.getErrorAttributes(webRequest, options);
        attributes.put("service", "order-api");
        return attributes;
    }
}
```

### 기본 노출 정책 예시

```properties
server.error.include-message=never
server.error.include-binding-errors=never
server.error.include-stacktrace=never
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 기본 `BasicErrorController` 사용 | 설정이 단순하다 | 팀 표준 오류 계약과 어긋날 수 있다 | 초기 개발, 단순 서비스 |
| `@ControllerAdvice` 중심 커스터마이징 | MVC 예외 계약을 통제하기 쉽다 | fallback `/error`까지 자동으로 통일되진 않는다 | 대부분의 API 예외 처리 |
| `ErrorAttributes`/`/error`까지 맞춤 | fallback path까지 일관성이 생긴다 | 설계 포인트가 늘어난다 | 오류 계약 표준화가 중요한 서비스 |
| whitelabel 유지 | 개발 편의가 좋다 | 운영/API에는 부적합할 수 있다 | 로컬 개발, 단순 브라우저 앱 |

핵심은 오류 응답을 MVC advice만의 문제로 보지 않고, **resolver chain 밖의 fallback error path까지 포함한 계약**으로 보는 것이다.

## 꼬리질문

> Q: `BasicErrorController`는 언제 등장하는가?
> 의도: fallback error path 이해 확인
> 핵심: MVC 예외 처리 밖에서 마지막 fallback 오류 응답이 필요할 때 `/error` 경로에서 등장한다.

> Q: `ErrorAttributes`의 역할은 무엇인가?
> 의도: 오류 모델 구성 이해 확인
> 핵심: fallback error response에 담길 속성 모델을 만든다.

> Q: 왜 어떤 요청은 HTML whitelabel이고 어떤 요청은 JSON인가?
> 의도: content negotiation과 fallback error path 이해 확인
> 핵심: 같은 `/error` 경로라도 요청 협상 결과에 따라 다르게 응답할 수 있기 때문이다.

> Q: 왜 401/403은 종종 `/error`와 별개로 느껴지는가?
> 의도: security vs mvc error boundary 확인
> 핵심: 보안 실패는 filter chain에서 먼저 처리될 수 있기 때문이다.

## 한 줄 정리

Spring Boot의 기본 오류 응답은 MVC advice의 대체가 아니라, advice 바깥 실패까지 받아내는 fallback error path다.
