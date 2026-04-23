# Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`

> 한 줄 요약: Spring Security의 401/403은 MVC 예외 처리가 아니라 filter chain 안의 exception translation 계약이 결정한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)
> - [Spring Security `RequestCache` / `SavedRequest` Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
> - [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
> - [Spring ProblemDetail Error Response Design](./spring-problemdetail-error-response-design.md)
> - [Spring OAuth2 + JWT 통합](./spring-oauth2-jwt-integration.md)

retrieval-anchor-keywords: ExceptionTranslationFilter, AuthenticationEntryPoint, AccessDeniedHandler, 401 vs 403, security exception translation, authenticationexception, accessdeniedexception, login redirect, bearer token error

## 핵심 개념

Spring Security에서 인증/인가 실패가 어떻게 HTTP 응답으로 바뀌는지는 `ExceptionTranslationFilter`가 책임진다.

핵심 분기는 아래 두 가지다.

- 인증이 필요하거나 인증이 유효하지 않다 -> `AuthenticationEntryPoint`
- 이미 인증됐지만 권한이 부족하다 -> `AccessDeniedHandler`

즉 401/403 문제는 대개 controller advice가 아니라 **security filter chain에서 예외를 어떤 계약으로 번역하느냐**의 문제다.

이 경계를 놓치면 흔한 오해가 생긴다.

- `@RestControllerAdvice`가 401/403도 잡아 줄 거라고 생각한다
- JWT 필터에서 아무 예외나 던져도 Security가 알아서 변환할 거라고 생각한다
- 인증 실패와 권한 실패를 같은 JSON 포맷으로 만들었는데, 실제로는 302 redirect가 섞여 나온다

## 깊이 들어가기

### 1. Security 예외는 DispatcherServlet 앞에서 난다

보안 필터는 MVC보다 앞단에서 동작한다.

```text
request
-> DelegatingFilterProxy
-> FilterChainProxy
-> authentication / authorization filters
-> ExceptionTranslationFilter
-> DispatcherServlet
```

그래서 Security 예외는 MVC `HandlerExceptionResolver` 체인보다 먼저 정리되는 경우가 많다.

즉 "예외 응답 통일"을 하고 싶다면 MVC advice만 보는 것으로는 부족하다.

### 2. 401과 403의 기준은 단순 문자열이 아니다

대략적인 판단 기준은 다음과 같다.

- 인증이 없거나 잘못됐다 -> 401 성격 -> `AuthenticationEntryPoint`
- 인증은 됐지만 권한이 부족하다 -> 403 성격 -> `AccessDeniedHandler`

하지만 실제로는 더 미묘하다.

익명 사용자 요청에서 `AccessDeniedException`이 발생해도, Security는 이를 "로그인이 필요하다"로 보고 entry point를 태울 수 있다.

즉 예외 타입 이름만 보는 것이 아니라, **현재 인증 상태를 함께 본다**.

### 3. `ExceptionTranslationFilter`는 모든 예외를 잡는 만능 필터가 아니다

이 필터가 주로 다루는 것은 다음이다.

- `AuthenticationException`
- `AccessDeniedException`

따라서 custom JWT filter가 임의의 `RuntimeException`을 던지면, 기대한 401/403이 아니라 500으로 새어 나갈 수 있다.

이 경우 보통 선택지는 두 가지다.

- 적절한 Security 예외 타입으로 변환해서 던진다
- 필터 안에서 entry point / denied handler를 직접 호출한다

핵심은 "에러를 던졌다"가 아니라, **Security가 이해하는 예외 경계 안에 있는가**다.

### 4. 브라우저와 API는 같은 실패라도 응답 전략이 다르다

form login 기반 웹 앱이라면 인증 실패 시 로그인 페이지 redirect가 자연스럽다.

반면 API 서버에서는 보통 JSON body와 401/403이 필요하다.

즉 같은 `AuthenticationEntryPoint`라도 역할이 다르다.

- 브라우저 UI: 로그인 redirect
- REST API: JSON / `ProblemDetail`
- resource server: `WWW-Authenticate` 헤더 포함

그래서 API와 웹을 한 애플리케이션에서 함께 운영하면, 체인 분리나 경로별 예외 번역 전략이 필요하다.

### 5. MVC error contract와 Security error contract는 별도로 맞춰야 한다

운영 관점에서는 클라이언트가 아래를 일관되게 보길 원한다.

- 에러 코드
- 메시지
- trace correlation
- `ProblemDetail` 구조

하지만 구현 포인트는 분리된다.

- MVC 예외 -> `@RestControllerAdvice` / `HandlerExceptionResolver`
- Security 예외 -> `AuthenticationEntryPoint` / `AccessDeniedHandler`

즉 응답 포맷은 통일할 수 있어도, **통일을 구현하는 지점은 다르다**.

## 실전 시나리오

### 시나리오 1: API인데 로그인 페이지로 302 redirect가 뜬다

대개 form login용 entry point가 API 경로에도 적용된 것이다.

이 경우는 controller advice 문제가 아니라, API 체인에 맞는 entry point가 없다는 뜻이다.

### 시나리오 2: JWT가 잘못됐는데 500이 떨어진다

custom filter에서 `RuntimeException`을 던졌거나, 예외가 `ExceptionTranslationFilter` 바깥에서 처리됐을 가능성이 높다.

JWT 인증 실패는 보통 `AuthenticationException` 계열로 번역되거나, entry point에서 직접 응답해야 한다.

### 시나리오 3: 로그인 안 한 요청이 401 대신 403으로 보인다

익명 사용자 처리, anonymous 설정, custom denied handler 구성이 얽혔을 수 있다.

핵심은 "누가 현재 principal로 간주되는가"와 "어느 핸들러가 최종 응답을 만들었는가"다.

### 시나리오 4: 도메인 예외는 `ProblemDetail`인데 보안 예외만 다른 포맷이다

흔한 현상이다.

해결은 MVC advice를 더 늘리는 것이 아니라, entry point와 denied handler도 같은 에러 포맷을 사용하도록 맞추는 것이다.

## 코드로 보기

### JSON 기반 `AuthenticationEntryPoint`

```java
public class ApiAuthenticationEntryPoint implements AuthenticationEntryPoint {

    @Override
    public void commence(
            HttpServletRequest request,
            HttpServletResponse response,
            AuthenticationException authException) throws IOException {
        response.setStatus(HttpStatus.UNAUTHORIZED.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.getWriter().write("""
            {"code":"UNAUTHORIZED","message":"authentication is required"}
            """);
    }
}
```

### JSON 기반 `AccessDeniedHandler`

```java
public class ApiAccessDeniedHandler implements AccessDeniedHandler {

    @Override
    public void handle(
            HttpServletRequest request,
            HttpServletResponse response,
            AccessDeniedException accessDeniedException) throws IOException {
        response.setStatus(HttpStatus.FORBIDDEN.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.getWriter().write("""
            {"code":"FORBIDDEN","message":"access is denied"}
            """);
    }
}
```

### SecurityFilterChain 연결

```java
@Bean
SecurityFilterChain apiChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/api/**")
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .exceptionHandling(ex -> ex
            .authenticationEntryPoint(new ApiAuthenticationEntryPoint())
            .accessDeniedHandler(new ApiAccessDeniedHandler())
        )
        .build();
}
```

### custom filter에서 직접 entry point 사용

```java
try {
    Authentication authentication = tokenService.authenticate(token);
    SecurityContextHolder.getContext().setAuthentication(authentication);
} catch (AuthenticationException ex) {
    authenticationEntryPoint.commence(request, response, ex);
    return;
}
filterChain.doFilter(request, response);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 기본 entry point / denied handler 사용 | 설정이 단순하다 | API 포맷 일관성이 약할 수 있다 | 기본 웹 로그인 |
| 전역 JSON 핸들러 사용 | 클라이언트 계약이 명확하다 | 브라우저 redirect UX와 충돌할 수 있다 | REST API 중심 |
| 체인별 예외 번역 분리 | 경계가 명확하다 | 설정이 복잡해진다 | API + web 혼합 서비스 |
| 필터에서 직접 응답 작성 | 세밀한 제어가 가능하다 | Security 계약을 우회하기 쉽다 | 특수한 custom auth 흐름 |

핵심은 401/403을 "상태 코드 숫자"가 아니라, **보안 실패를 번역하는 책임 분리**로 보는 것이다.

## 꼬리질문

> Q: `@RestControllerAdvice`가 401/403을 항상 처리하지 못하는 이유는 무엇인가?
> 의도: filter chain과 MVC 경계 이해 확인
> 핵심: Security 예외는 DispatcherServlet 이전 단계에서 번역될 수 있다.

> Q: `AuthenticationEntryPoint`와 `AccessDeniedHandler`의 차이는 무엇인가?
> 의도: 인증 실패와 권한 실패 구분 확인
> 핵심: 전자는 로그인/인증 필요 상황, 후자는 인증 후 권한 부족 상황이다.

> Q: custom JWT filter에서 아무 런타임 예외나 던지면 왜 위험한가?
> 의도: exception translation 계약 이해 확인
> 핵심: `ExceptionTranslationFilter`가 기대하는 보안 예외 타입 밖으로 새면 500이 될 수 있다.

> Q: API와 웹 페이지가 같은 entry point를 쓰면 어떤 문제가 생길 수 있는가?
> 의도: 응답 전략 분리 이해 확인
> 핵심: API는 JSON이 필요한데 웹 redirect가 섞일 수 있다.

## 한 줄 정리

Spring Security의 401/403은 `ExceptionTranslationFilter`가 entry point와 denied handler로 번역한 결과이므로, MVC 예외 처리와는 별도 경계로 설계해야 한다.
