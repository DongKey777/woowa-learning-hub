# Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries

> 한 줄 요약: `Filter`, `HandlerInterceptor`, `@ControllerAdvice`는 모두 요청을 가로채지만, 서블릿/핸들러/예외 처리라는 서로 다른 층에서 책임이 갈린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
> - [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)

retrieval-anchor-keywords: filter, handlerinterceptor, controlleradvice, restcontrolleradvice, exceptionresolver, servlet filter, dispatcherservlet, request lifecycle, cross-cutting boundary

## 핵심 개념

이 세 가지는 모두 공통 관심사를 다루지만 위치가 다르다.

- `Filter`: 서블릿 컨테이너 레벨
- `HandlerInterceptor`: Spring MVC 핸들러 레벨
- `@ControllerAdvice`: 컨트롤러 예외 처리 레벨

이 차이를 모르고 "전역 처리"라고 한곳에 몰아넣으면 다음이 뒤엉킨다.

- 인증/인가
- 요청 로깅
- 공통 헤더 처리
- 예외 변환
- 응답 포맷 표준화

핵심은 "무엇을 막을 것인가"와 "어느 층에서 막을 것인가"를 분리하는 것이다.

## 깊이 들어가기

### 1. `Filter`는 DispatcherServlet 이전이다

`Filter`는 서블릿 요청 자체를 가로챈다.

```text
container
  -> Filter
  -> DispatcherServlet
  -> HandlerMapping
  -> Controller
```

이 위치 덕분에 `Filter`는 다음에 적합하다.

- 인증/인가의 전처리
- CORS
- request/response wrapping
- 공통 trace header

반대로 MVC 핸들러 정보를 모르기 때문에, 컨트롤러 메서드와 강하게 결합된 로직은 넣기 어렵다.

### 2. `HandlerInterceptor`는 MVC 핸들러 전후다

인터셉터는 컨트롤러를 실행하기 전과 후를 다룬다.

```java
public class LoggingInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        request.setAttribute("startedAt", System.currentTimeMillis());
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        long startedAt = (Long) request.getAttribute("startedAt");
        log.info("elapsed = {}", System.currentTimeMillis() - startedAt);
    }
}
```

적합한 용도는 다음이다.

- 요청 단위 메타데이터 수집
- locale, tenant, user-agent 추적
- 컨트롤러 실행 시간 측정

하지만 인증 실패를 인터셉터에서 끝내려는 습관은 조심해야 한다.

- Security는 보통 필터 체인이 먼저다
- 인터셉터는 이미 컨트롤러 진입 이후 맥락이다
- 보안 정책과 MVC 로직이 섞일 수 있다

### 3. `@ControllerAdvice`는 예외 변환과 바인딩 오류를 잡는다

`@ControllerAdvice`는 컨트롤러에서 터진 예외를 일관된 응답으로 바꾸는 곳이다.

```java
@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ErrorResponse> handleIllegalArgument(IllegalArgumentException ex) {
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("INVALID_ARGUMENT", ex.getMessage()));
    }
}
```

이 레이어의 핵심은 예외를 "처리"하는 것이지, 요청 흐름을 "막는" 것이 아니다.

### 4. 예외 번역은 컨트롤러와 핸들러의 계약이다

Spring MVC에서 `HandlerExceptionResolver`가 예외를 응답으로 바꾼다.

이때 `@ControllerAdvice`는 사실상 예외 번역 정책의 중심이다.

- 어떤 예외를 400으로 바꿀지
- 어떤 예외를 404로 바꿀지
- 어떤 예외를 500으로 남길지
- 에러 코드 포맷을 어디서 표준화할지

이 계약이 없으면 컨트롤러마다 예외 응답이 달라진다.

## 실전 시나리오

### 시나리오 1: 인증은 필터인데 로깅은 인터셉터에 넣었다

이건 꽤 좋은 분리다.

- 인증 실패는 필터에서 막는다
- 요청 처리 시간은 인터셉터에서 잰다
- 비즈니스 예외는 `@ControllerAdvice`에서 바꾼다

### 시나리오 2: 인터셉터에서 예외를 삼켰다

이렇게 하면 예외 처리 계약이 깨질 수 있다.

- 컨트롤러는 성공했다고 착각할 수 있다
- `@ControllerAdvice`가 못 본다
- 응답 상태가 일관되지 않을 수 있다

### 시나리오 3: `@ControllerAdvice`가 있는데도 HTML 에러 페이지가 나온다

원인 후보:

- advice 패키지 스캔 범위가 다르다
- `@RestControllerAdvice` 대신 `@ControllerAdvice`를 쓰고 응답 바디를 안 붙였다
- 요청 경로가 API가 아니라 view resolver 경로로 간다

이건 [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)와 같이 봐야 한다.

### 시나리오 4: 필터에서 request body를 읽어 버렸다

서블릿 request body는 한 번 읽으면 소모될 수 있다.

- 로깅 필터가 body를 읽고
- 이후 컨트롤러가 `@RequestBody`를 못 읽는 사고가 난다

이 경우는 request wrapping이나 content caching이 필요하다.

## 코드로 보기

### Filter

```java
@Component
public class TraceFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        try {
            MDC.put("path", httpRequest.getRequestURI());
            chain.doFilter(request, response);
        } finally {
            MDC.remove("path");
        }
    }
}
```

### Interceptor

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new LoggingInterceptor());
    }
}
```

### ControllerAdvice

```java
@RestControllerAdvice
public class GlobalExceptionAdvice {

    @ExceptionHandler(OrderNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleOrderNotFound(OrderNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(new ErrorResponse("ORDER_NOT_FOUND", ex.getMessage()));
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `Filter` | 가장 앞단에서 제어한다 | MVC 문맥이 없다 | 인증, CORS, 헤더 |
| `HandlerInterceptor` | 요청 단위 공통 로직에 적합하다 | 보안/예외 계약과 섞기 쉽다 | 로깅, metric, locale |
| `@ControllerAdvice` | 예외 응답을 표준화한다 | 예외 번역에만 집중해야 한다 | API 에러 포맷 |
| `AOP` | 비즈니스 계층 공통화가 쉽다 | MVC 요청 경계와는 다르다 | service layer 횡단 관심사 |

핵심은 도구 비교가 아니라, **어떤 계층의 계약을 바꾸고 싶은가**다.

## 꼬리질문

> Q: `Filter`와 `HandlerInterceptor`의 가장 큰 차이는 무엇인가?
> 의도: 실행 계층 이해 확인
> 핵심: `Filter`는 서블릿, 인터셉터는 MVC 핸들러 레벨이다.

> Q: 인증 실패를 인터셉터가 아니라 필터에서 다루는 이유는 무엇인가?
> 의도: 보안 경계 이해 확인
> 핵심: 보안은 DispatcherServlet 이전에서 처리하는 편이 자연스럽다.

> Q: `@ControllerAdvice`는 무엇을 표준화하는가?
> 의도: 예외 번역 역할 이해 확인
> 핵심: 컨트롤러 예외를 일관된 HTTP 응답으로 바꾼다.

> Q: 필터에서 request body를 읽으면 왜 위험한가?
> 의도: 서블릿 I/O 동작 이해 확인
> 핵심: 이후 `@RequestBody`가 같은 body를 다시 못 읽을 수 있다.

## 한 줄 정리

`Filter`는 서블릿 전처리, `HandlerInterceptor`는 MVC 전후 처리, `@ControllerAdvice`는 예외 번역이므로 각각의 경계를 섞지 않아야 한다.
