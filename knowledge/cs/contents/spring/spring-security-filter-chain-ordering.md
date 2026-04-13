# Spring Security Filter Chain Ordering

> 한 줄 요약: Spring Security는 여러 필터가 순서대로 쌓인 체인이므로, 어떤 필터가 먼저 실행되는지를 모르면 인증 실패와 권한 실패를 구분하기 어렵다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)
> - [Spring Actuator Exposure and Security](./spring-actuator-exposure-security.md)

retrieval-anchor-keywords: SecurityFilterChain, filter order, OncePerRequestFilter, UsernamePasswordAuthenticationFilter, BearerTokenAuthenticationFilter, DelegatingFilterProxy, CORS, CSRF, exception translation filter

## 핵심 개념

Spring Security는 단일 필터가 아니라 filter chain이다.

- 앞단 필터가 인증 정보를 만들고
- 중간 필터가 세션/토큰/CSRF를 다루고
- 뒤쪽 필터가 인가와 예외 변환을 다룬다

순서를 잘못 잡으면 다음 문제가 생긴다.

- 토큰 필터가 너무 늦게 실행된다
- CORS/CSRF가 먼저 막는다
- 예외 번역이 Security 밖으로 새어 나간다

## 깊이 들어가기

### 1. DelegatingFilterProxy가 Spring 필터로 연결한다

서블릿 컨테이너의 필터와 Spring Bean을 연결하는 다리 역할이다.

### 2. SecurityFilterChain은 요청별 체인 선택이다

하나의 애플리케이션에 여러 체인이 있을 수 있다.

```java
@Bean
SecurityFilterChain apiChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/api/**")
        .addFilterBefore(jwtFilter(), UsernamePasswordAuthenticationFilter.class)
        .build();
}
```

### 3. 필터 순서는 인증 의미를 바꾼다

토큰 필터가 너무 뒤에 있으면 이미 다른 필터가 요청을 차단했을 수 있다.

그래서 다음이 중요하다.

- CORS
- CSRF
- authentication
- authorization
- exception translation

### 4. `OncePerRequestFilter`는 중복 실행을 피한다

같은 요청에서 여러 번 타지 않게 하려면 유용하다.

### 5. 예외 번역 필터가 없으면 401/403이 흔들린다

Security는 예외를 적절한 HTTP 응답으로 바꾸는 단계까지 포함한다.

이게 없으면 컨트롤러 advice로 새어 나갈 수 있다.

## 실전 시나리오

### 시나리오 1: JWT 필터를 넣었는데 계속 401이다

원인 후보:

- 필터 순서가 틀렸다
- 토큰 헤더를 읽기 전에 CORS/CSRF가 막는다
- `SecurityContext`에 authentication을 넣지 않았다

### 시나리오 2: 관리자 API만 막힌다

인가 필터와 role mapping이 문제일 수 있다.

### 시나리오 3: 특정 경로만 다른 필터 체인을 타야 한다

`securityMatcher`로 체인을 분리해야 한다.

### 시나리오 4: 필터에서 예외가 난 뒤 응답 형식이 이상하다

Security의 exception translation과 MVC advice의 경계가 섞였을 수 있다.

## 코드로 보기

### 필터 순서

```java
@Bean
SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    return http
        .csrf(csrf -> csrf.disable())
        .addFilterBefore(jwtAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class)
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/actuator/health").permitAll()
            .anyRequest().authenticated()
        )
        .build();
}
```

### custom filter

```java
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        filterChain.doFilter(request, response);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 filter chain | 단순하다 | 경로별 정책 분리가 약하다 | 작은 서비스 |
| 다중 SecurityFilterChain | 경로별 정책이 명확하다 | 순서가 복잡해진다 | API와 web 혼합 |
| `OncePerRequestFilter` | 중복 실행을 막는다 | 순서를 해결하진 않는다 | token/auth filter |
| 수동 filter 등록 | 제어가 쉽다 | Spring Security 계약을 깨기 쉽다 | 특수한 경우 |

핵심은 필터를 "하나 더 넣는 것"이 아니라, **어떤 보안 단계가 먼저 완료돼야 하는지**다.

## 꼬리질문

> Q: Spring Security에서 필터 순서가 중요한 이유는 무엇인가?
> 의도: 인증/인가 플로우 이해 확인
> 핵심: 앞단 필터가 뒤단의 전제를 만든다.

> Q: `securityMatcher`는 무엇을 해결하는가?
> 의도: 경로별 체인 분리 이해 확인
> 핵심: 요청 경로에 따라 다른 SecurityFilterChain을 선택한다.

> Q: `OncePerRequestFilter`를 쓰는 이유는 무엇인가?
> 의도: 중복 실행 방지 이해 확인
> 핵심: 한 요청당 한 번만 실행되게 한다.

> Q: Security 예외와 MVC 예외는 왜 다르게 다뤄지는가?
> 의도: 필터 vs MVC 경계 확인
> 핵심: Security는 DispatcherServlet 이전 단계다.

## 한 줄 정리

Spring Security의 필터 체인은 순서가 곧 의미이므로, 어떤 필터가 인증과 예외 번역을 먼저 책임지는지 명확히 해야 한다.
