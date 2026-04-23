# Spring MVC Exception Resolver Chain Contract

> 한 줄 요약: Spring MVC의 예외 처리는 단일 핸들러가 아니라 resolver chain의 계약이며, 어떤 resolver가 잡는지에 따라 API 오류 형식과 상태 코드가 달라진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
> - [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
> - [Spring `BasicErrorController`, `ErrorAttributes`, and Whitelabel Error Boundaries](./spring-basicerrorcontroller-errorattributes-whitelabel-boundaries.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Proxy Local Reply vs Upstream Error Attribution](../network/proxy-local-reply-vs-upstream-error-attribution.md)

retrieval-anchor-keywords: HandlerExceptionResolver, ExceptionResolver chain, @ExceptionHandler, @ControllerAdvice, DefaultHandlerExceptionResolver, ResponseStatusExceptionResolver, error contract

## 핵심 개념

Spring MVC는 예외를 하나의 방법으로만 처리하지 않는다.

대표적으로 다음 resolver가 체인으로 동작한다.

- `ExceptionHandlerExceptionResolver`
- `ResponseStatusExceptionResolver`
- `DefaultHandlerExceptionResolver`

그리고 `@ControllerAdvice` / `@ExceptionHandler`가 이 체인 안에서 핵심 역할을 한다.

즉, 예외 응답은 "예외가 났다"로 끝나는 게 아니라, **어떤 resolver가 어떤 순서로 잡았는지**의 결과다.

## 깊이 들어가기

### 1. resolver chain은 책임 분리다

예외를 한 곳에서 다 처리하려고 하면 오히려 유연성이 떨어진다.

- 애노테이션 기반 예외 처리
- 상태 코드 기반 변환
- 기본 servlet / spring 예외 처리

이렇게 나뉘어 있다.

### 2. `@ExceptionHandler`는 가장 구체적인 수단이다

```java
@RestControllerAdvice
public class ApiExceptionAdvice {

    @ExceptionHandler(OrderNotFoundException.class)
    public ResponseEntity<ErrorResponse> handle(OrderNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(new ErrorResponse("ORDER_NOT_FOUND", ex.getMessage()));
    }
}
```

이건 특정 예외를 특정 형식으로 바꾸는 명시적 계약이다.

### 3. `ResponseStatusExceptionResolver`는 상태 코드 중심이다

`ResponseStatusException`이나 `@ResponseStatus` 계열은 간단하지만, 에러 바디 표준화는 직접 해줘야 한다.

### 4. `DefaultHandlerExceptionResolver`는 MVC 기본 예외를 처리한다

대표적으로 type mismatch, method not allowed, missing parameter 같은 기본 MVC 예외가 여기에 걸릴 수 있다.

### 5. resolver 우선순위가 중요하다

같은 예외라도 어떤 resolver가 먼저 잡느냐에 따라 응답이 달라질 수 있다.

그래서 API 계약이 중요한 서비스에서는 resolver 우선순위와 advice 범위를 문서화해야 한다.

## 실전 시나리오

### 시나리오 1: 예외는 났는데 상태 코드가 기대와 다르다

대개 다음 중 하나다.

- `@ExceptionHandler`가 안 잡았다
- `@ResponseStatus`가 선점했다
- 기본 resolver가 먼저 처리했다

### 시나리오 2: JSON 에러 대신 HTML 에러 페이지가 나온다

`@RestControllerAdvice` 대신 `@ControllerAdvice`만 썼거나, 반환 타입이 뷰로 해석될 수 있다.

### 시나리오 3: validation 예외와 도메인 예외가 같은 포맷으로 안 나온다

이건 의도일 수도 있고, 계약 미정의일 수도 있다.

- validation은 입력 실패
- domain exception은 비즈니스 규칙 실패

같은 포맷으로 만들지 별도 분리할지 정해야 한다.

### 시나리오 4: Security 예외는 MVC advice에서 안 잡힌다

보안 예외는 보통 필터 체인과 더 가까운 곳에서 발생한다.

이 문제는 [Spring Security 아키텍처](./spring-security-architecture.md)와 같이 봐야 한다.

## 코드로 보기

### ExceptionHandler

```java
@RestControllerAdvice
public class GlobalApiAdvice {

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ErrorResponse> handleIllegalArgument(IllegalArgumentException ex) {
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("INVALID_ARGUMENT", ex.getMessage()));
    }
}
```

### ResponseStatusException

```java
throw new ResponseStatusException(HttpStatus.NOT_FOUND, "order not found");
```

### custom resolver is rare but possible

```java
public class MyExceptionResolver implements HandlerExceptionResolver {
    @Override
    public ModelAndView resolveException(
            HttpServletRequest request,
            HttpServletResponse response,
            Object handler,
            Exception ex) {
        return null;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `@ExceptionHandler` | 가장 명시적이다 | advice가 많아지면 산만하다 | API error contract |
| `@ResponseStatus` | 간단하다 | 바디 표준화가 약하다 | 아주 단순한 예외 |
| custom resolver | 전역 제어가 가능하다 | 복잡하고 드물다 | 특수한 MVC 정책 |
| 기본 resolver | 자동으로 처리된다 | 계약이 약하다 | 기본 MVC 예외 |

핵심은 예외를 "잡는 것"보다, **어떤 오류 계약으로 번역할 것인가**다.

## 꼬리질문

> Q: HandlerExceptionResolver 체인이 필요한 이유는 무엇인가?
> 의도: 예외 처리 분리 이해 확인
> 핵심: 여러 종류의 예외를 다른 전략으로 번역하기 위해서다.

> Q: `@ExceptionHandler`가 `@ResponseStatus`보다 선호되는 이유는 무엇인가?
> 의도: 응답 포맷 통제 이해 확인
> 핵심: 상태 코드와 바디를 함께 제어하기 쉽다.

> Q: MVC 예외와 Security 예외가 왜 다르게 느껴지는가?
> 의도: 필터와 MVC 경계 이해 확인
> 핵심: 보안 예외는 보통 필터 체인에서 먼저 난다.

> Q: 기본 resolver만 믿으면 어떤 문제가 생기는가?
> 의도: error contract 인식 확인
> 핵심: 상태 코드와 에러 포맷이 일관되지 않을 수 있다.

## 한 줄 정리

Spring MVC 예외 처리는 resolver chain이 만드는 계약이므로, 어떤 예외를 어떤 resolver가 번역하는지 먼저 정해야 한다.
