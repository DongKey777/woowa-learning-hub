# Spring 예외 처리 기초: @ExceptionHandler와 @ControllerAdvice

> 한 줄 요약: Spring MVC에서 `@ExceptionHandler`는 특정 컨트롤러의 예외를 잡고, `@ControllerAdvice`는 전역에서 예외를 잡아 일관된 오류 응답을 만든다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
- [Spring MVC 컨트롤러 기초](./spring-mvc-controller-basics.md)
- [software-engineering API 설계와 예외 처리](../software-engineering/api-design-error-handling.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring exception handling basics, 스프링 예외 처리 처음, exceptionhandler 입문, controlleradvice 입문, restcontrolleradvice 뭐예요, 전역 예외 처리 입문, spring 오류 응답 통일 방법, 400 404 500 응답 만들기 spring, spring error response 입문, responseentityexceptionhandler 입문, spring 예외 잡는 법, spring 커스텀 예외 입문, spring exception handling basics basics, spring exception handling basics beginner, spring exception handling basics intro

## 핵심 개념

컨트롤러마다 try-catch를 넣으면 같은 패턴의 오류 처리 코드가 여러 곳에 중복된다. Spring MVC는 `@ExceptionHandler`와 `@ControllerAdvice`로 예외를 한 곳에서 통합 처리하는 메커니즘을 제공한다.

- **`@ExceptionHandler`**: 메서드 레벨에 붙이면 해당 컨트롤러에서 발생하는 특정 예외를 처리한다.
- **`@ControllerAdvice`**: 모든 컨트롤러에 걸쳐 예외를 잡는 전역 처리기다. `@RestControllerAdvice`는 `@ControllerAdvice` + `@ResponseBody`를 합친 것으로, JSON 응답을 반환할 때 편하다.

## 한눈에 보기

```text
컨트롤러에서 예외 발생
        ↓
같은 컨트롤러에 @ExceptionHandler가 있으면 → 해당 핸들러 실행
없으면
        ↓
@ControllerAdvice 클래스의 @ExceptionHandler 탐색 → 매칭 핸들러 실행
없으면
        ↓
Spring 기본 오류 처리 (/error 엔드포인트)
```

| 애노테이션 | 범위 | 주 용도 |
|---|---|---|
| `@ExceptionHandler` (컨트롤러 내) | 해당 컨트롤러만 | 컨트롤러 전용 예외 |
| `@ControllerAdvice` | 전체 컨트롤러 | 공통 예외 처리 |
| `@RestControllerAdvice` | 전체 컨트롤러 | JSON API 오류 응답 |

## 상세 분해

- **예외 계층 활용**: `IllegalArgumentException`은 400, `EntityNotFoundException`은 404로 매핑하는 것처럼 예외 종류와 HTTP 상태 코드를 연결한다.
- **`@ResponseStatus`**: 커스텀 예외 클래스에 붙이면 해당 예외 발생 시 자동으로 지정 상태 코드를 응답한다. `@ExceptionHandler`와 같이 쓰면 `@ExceptionHandler` 우선이다.
- **오류 응답 구조 통일**: `{ "code": "MEMBER_NOT_FOUND", "message": "..." }` 형태의 공통 응답 DTO를 만들고, 모든 `@ExceptionHandler`가 이 형태로 반환하면 클라이언트가 일관되게 처리할 수 있다.
- **`ResponseEntityExceptionHandler`**: Spring MVC 기본 예외(`MethodArgumentNotValidException`, `HttpMessageNotReadableException` 등)를 이미 처리해놓은 추상 클래스다. 이걸 상속하면 기본 처리를 커스터마이즈하기 쉽다.
- **예외 계층 우선순위**: 여러 `@ExceptionHandler`가 있을 때 더 구체적인 예외 타입이 먼저 매칭된다.

## 흔한 오해와 함정

**오해 1: `@ControllerAdvice`가 없으면 예외가 클라이언트에게 그대로 노출된다**
Spring Boot는 기본으로 `/error` 엔드포인트와 `BasicErrorController`를 통해 오류 응답을 만들어준다. 다만 HTML 또는 매우 일반적인 JSON으로 응답하므로, API 서버라면 `@RestControllerAdvice`로 직접 제어하는 것이 낫다.

**오해 2: 모든 예외를 `@ExceptionHandler`로 잡아야 한다**
비즈니스 예외는 커스텀 예외 클래스 + `@ControllerAdvice`로 처리하고, Spring 프레임워크 예외는 `ResponseEntityExceptionHandler`를 상속해 처리하는 방식이 깔끔하다.

**오해 3: `@ControllerAdvice` 안의 `@ExceptionHandler`는 해당 advice 클래스의 컨트롤러만 처리한다**
기본적으로 모든 컨트롤러에 적용된다. `basePackages`나 `assignableTypes`를 지정하면 범위를 좁힐 수 있다.

## 실무에서 쓰는 모습

공통 오류 응답 형태를 정하고 `@RestControllerAdvice`로 통합 처리하는 패턴이다.

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MemberNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleMemberNotFound(MemberNotFoundException e) {
        return new ErrorResponse("MEMBER_NOT_FOUND", e.getMessage());
    }

    @ExceptionHandler(IllegalArgumentException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleIllegalArgument(IllegalArgumentException e) {
        return new ErrorResponse("INVALID_INPUT", e.getMessage());
    }
}
```

컨트롤러는 예외를 던지기만 하고, 오류 응답 생성은 `GlobalExceptionHandler`에서 집중 관리한다.

## 더 깊이 가려면

- `DispatcherServlet`이 예외를 어디서 잡아 `@ControllerAdvice`로 넘기는지는 [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)에서 이어서 본다.
- 예외 계층 설계와 체크드/언체크드 예외 전략은 [software-engineering API 설계와 예외 처리](../software-engineering/api-design-error-handling.md)를 참고한다.

## 면접/시니어 질문 미리보기

> Q: `@ControllerAdvice`와 `@RestControllerAdvice`의 차이는?
> 의도: 애노테이션 구성 이해
> 핵심: `@RestControllerAdvice`는 `@ControllerAdvice` + `@ResponseBody`의 조합으로 리턴값이 HTTP 응답 본문(JSON)으로 직렬화된다.

> Q: 같은 예외에 `@ExceptionHandler`가 컨트롤러와 `@ControllerAdvice` 두 곳에 있으면?
> 의도: 우선순위 이해
> 핵심: 컨트롤러 내부의 `@ExceptionHandler`가 우선된다.

> Q: Spring MVC의 기본 예외(예: `MethodArgumentNotValidException`)를 커스터마이즈하려면?
> 의도: `ResponseEntityExceptionHandler` 활용 이해
> 핵심: `ResponseEntityExceptionHandler`를 상속하고 해당 메서드를 오버라이드하면 기본 처리를 커스터마이즈할 수 있다.

## 한 줄 정리

`@ControllerAdvice`에 `@ExceptionHandler`를 모아 오류 응답 형식을 통일하면, 각 컨트롤러는 예외를 던지기만 하고 처리 로직을 한 곳에서 관리할 수 있다.
