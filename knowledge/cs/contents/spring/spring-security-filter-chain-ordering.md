---
schema_version: 3
title: "Spring Security Filter Chain Ordering: 여러 보안 검사 순서를 정하는 규칙"
concept_id: spring/spring-security-filter-chain-ordering
canonical: false
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
review_feedback_tags:
- security-filter-chain
- ordering
- security-filter-order
- addfilterbefore
aliases:
- Spring Security filter chain ordering
- security filter order
- addFilterBefore
- addFilterAfter
- BearerTokenAuthenticationFilter order
intents:
- deep_dive
linked_paths:
- contents/spring/spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md
- contents/spring/spring-security-filter-chain.md
- contents/spring/spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card.md
- contents/security/auth-failure-response-401-403-404.md
- contents/security/session-cookie-jwt-basics.md
forbidden_neighbors:
- contents/spring/spring-mvc-controller-basics.md
expected_queries:
- Spring Security filter order는 왜 중요해?
- addFilterBefore와 addFilterAfter 기준 필터를 어떻게 고르지?
- JWT filter를 UsernamePasswordAuthenticationFilter 앞에 둬야 하는지 헷갈려
- ExceptionTranslationFilter와 AuthorizationFilter 순서를 어떻게 이해해?
contextual_chunk_prefix: |
  이 문서는 학습자가 여러 보안 검사가 있을 때 어느 게 먼저고 어느 게
  뒤인지 정하는 규칙 — Spring Security filter chain ordering — 을 깊이
  잡는 deep_dive다. 보안 검사 순서, 어느 검사 먼저 어느 게 뒤, 순서 정하는
  규칙, 여러 보안 검사가 있을 때 어느 게 먼저고 어느 게 뒤인지 정하는 규칙,
  addFilterBefore vs addFilterAfter, filter ordering 같은 자연어 paraphrase가
  본 문서의 ordering 규칙에 매핑된다.
---
# Spring Security Filter Chain Ordering

> 한 줄 요약: Spring Security는 여러 필터가 순서대로 쌓인 체인이므로, 어떤 필터가 먼저 실행되는지를 모르면 인증 실패와 권한 실패를 구분하기 어렵다.

**난이도: 🔴 Advanced**

관련 문서:

- [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)
- [Spring JWT 필터에서 `filterChain.doFilter(...)` 전후에 무슨 일이 일어날까](./spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card.md)
- [Spring Security 기초: 인증과 인가의 흐름 잡기](./spring-security-basics.md)
- [Spring Security 아키텍처](./spring-security-architecture.md)
- [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
- [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](./spring-onceperrequestfilter-async-error-dispatch-traps.md)
- [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
- [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)
- [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)

retrieval-anchor-keywords: security filter chain ordering, spring security filter chain ordering, security filter order, filter order 401 403, admin 302 403 spring security, admin 302 login final 403, savedrequest filter chain order, jwt filter order, exception translation filter order, addfilterbefore, addfilterafter, add filter before usernamepasswordauthenticationfilter, add filter after usernamepasswordauthenticationfilter, usernamepasswordauthenticationfilter 앞, usernamepasswordauthenticationfilter 뒤, bearer token filter order, bearertokenauthenticationfilter 앞, bearertokenauthenticationfilter 뒤, jwt filter 어디에 둬요, bearer token 기준점

## 입문 브리지

이 문서는 `필터가 정확히 어느 순서로 도는가`, `예외 번역 필터가 앞뒤 어디에 있는가`, `JWT filter를 어느 기준 필터 앞에 둘 것인가`처럼 **이미 Security 큰 그림을 안다는 전제** 위에서 읽는 advanced 문서다.

basics 체크포인트: `security filter chain`이 "보안 필터 묶음"이라는 감각, `302 /login`과 `403`의 차이, 세션 로그인에서 `SavedRequest`가 "원래 주소 메모"라는 설명이 바로 떠오르지 않으면 이 문서보다 [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md), [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md), [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md)부터 먼저 본다.

처음 보는 용어가 아직 많다면 이 문서에 바로 들어오지 말고 아래 순서로 내려가는 편이 안전하다.

특히 advanced ordering 문서에 바로 들어왔는데 머릿속에 먼저 "`302 /login`이랑 `403`이 왜 갈리죠?"가 떠오른다면, 처음 30초는 `ExceptionTranslationFilter`만 기준으로 잡아 두면 된다.

| 지금 인증 상태 | `ExceptionTranslationFilter`가 붙이는 마지막 갈래 | 브라우저에서 자주 보이는 결과 | 한 줄 해석 |
|---|---|---|---|
| 아직 비로그인, 또는 인증이 유효하지 않음 | `AuthenticationEntryPoint` | `302 /login` 또는 API면 `401` | "먼저 로그인 필요" |
| 로그인은 됐지만 권한이 부족함 | `AccessDeniedHandler` | `403` | "누군지는 알지만 이 자원 권한은 없음" |
| 로그인 후 원래 URL로 다시 돌아가는 중 | entry point 자체보다 `RequestCache`/`SavedRequest`가 같이 보임 | `302`가 한 번 더 보일 수 있음 | "권한 실패라기보다 로그인 전 주소 메모 재생" |
| 브라우저에서 `302 -> login -> final 403`으로 이어짐 | `AuthenticationEntryPoint`로 로그인 화면까지 보낸 뒤, 재진입 요청에서는 `AccessDeniedHandler`가 마지막 `403`을 만든다 | 처음엔 `302 /login`, 로그인 성공 후 원래 `/admin` 복귀, 마지막엔 `403` | "첫 요청은 비로그인 분기, 재진입 요청은 권한 부족 분기" |

이 미니 표는 beginner용 분기 표고, 이 문서의 본론은 "그 갈래가 **필터 순서 어디에서** 결정되는가"를 보는 것이다.

즉 `302 -> login -> final 403`은 한 번에 같은 필터 결과가 아니라, `SavedRequest`로 원래 URL에 재진입한 뒤 **다시 읽힌 두 번째 보안 판단**까지 이어 붙인 장면이다.

| 지금 떠오르는 질문 | 먼저 갈 문서 | 여기로 다시 올라오는 시점 |
|---|---|---|
| "`security filter chain`이 뭐예요?", "`Filter`/`Interceptor`가 왜 다른가요?" | [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md) | "세 칸 역할은 알겠고, 이제 Security chain 안쪽 순서를 보고 싶다" |
| "`/admin`이 `302 /login`으로 튀어요", "`403`이랑 뭐가 달라요?" | [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md) | "`302`는 인증 전, `403`은 권한 단계라는 건 알겠고 그걸 만드는 필터 순서가 궁금하다" |
| "로그인은 성공했는데 마지막에만 `403`이 나요", "`SavedRequest`가 왜 보이죠?" | [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md) | "`SavedRequest`와 role mapping 문제를 분리했고, 이제 어느 필터가 그 분기를 만드는지 보고 싶다" |

`security filter chain`을 처음 배우는데 아직 큰 그림이 안 잡혔다면 이 문서보다 [Spring Security 기초: 인증과 인가의 흐름 잡기](./spring-security-basics.md)를 먼저 본다.

- 기초 문서에서 먼저 잡을 질문: "보안 필터 묶음이 컨트롤러보다 왜 먼저 도는가?"
- 이 문서로 다시 올라올 질문: "그래서 어느 필터가 먼저 돌고, 그 순서가 `302`/`401`/`403` 분기를 어떻게 바꾸는가?"

## `addFilterBefore` / `addFilterAfter`와 `UsernamePasswordAuthenticationFilter` / `BearerTokenAuthenticationFilter` 기준점 브리지

`addFilterAfter`, "`UsernamePasswordAuthenticationFilter` 앞에 둬요 뒤에 둬요?", "`JWT filter`를 어디에 꽂죠?", "`jwt filter 어디에 둬요`" 같은 검색으로 들어왔다면 이 섹션이 가장 짧은 entry다.

먼저 beginner 감각으로는 기준 필터를 둘로 나누면 된다.

- `UsernamePasswordAuthenticationFilter`: 폼 로그인 인증을 처리하는 기준 필터
- `BearerTokenAuthenticationFilter`: `Authorization: Bearer ...`를 읽는 bearer token 인증 기준 필터

즉 "`JWT filter 어디에 둬요`"라는 질문은 사실 한 문장으로 끝나지 않는다.
**폼 로그인 app에서 JWT를 보조적으로 붙이는지, bearer token API에서 JWT가 주인공인지**에 따라 기준점이 달라진다.

| 지금 앱의 인증 중심 | 먼저 붙일 기준 필터 | 초급 해석 |
|---|---|---|
| `formLogin()` 중심 웹 앱 | `UsernamePasswordAuthenticationFilter` | "로그인 폼 인증 전후 어디에 둘까?" |
| `oauth2ResourceServer().jwt()` 중심 API | `BearerTokenAuthenticationFilter` | "bearer token 인증 전후 어디에 둘까?" |
| 둘 다 있는 혼합 앱 | 체인별 기준 필터를 따로 본다 | "`/admin/**`와 `/api/**`가 같은 기준점을 쓰지 않을 수 있다" |

| 코드에서 보인 표현 | ordering 질문을 초급 문장으로 바꾸면 | 이 문서에서 이어서 볼 포인트 |
|---|---|---|
| `.addFilterBefore(customFilter, UsernamePasswordAuthenticationFilter.class)` | "로그인 필터가 돌기 전에 인증 재료를 먼저 준비해야 하나?" | 앞단 인증 재료 준비, `SecurityContext` 세팅 시점 |
| `.addFilterAfter(customFilter, UsernamePasswordAuthenticationFilter.class)` | "로그인 필터가 끝난 뒤 결과를 보고 후속 처리를 해야 하나?" | 인증 성공/실패 뒤 후처리, 예외 번역과의 거리 |
| `.addFilterBefore(customFilter, BearerTokenAuthenticationFilter.class)` | "bearer token을 읽기 전에 헤더/tenant/context를 먼저 정리해야 하나?" | bearer token 인증 전 선행 준비 |
| `.addFilterAfter(customFilter, BearerTokenAuthenticationFilter.class)` | "bearer token 인증이 끝난 뒤 claim/authority 결과를 보고 후처리해야 하나?" | JWT 인증 결과 기반 후처리 |

핵심은 메서드 이름이 아니라 **기준 필터 앞뒤에서 무엇이 이미 끝났는가**다.

```text
form-login chain
custom filter before UsernamePasswordAuthenticationFilter
-> 아직 기준 로그인 필터 전
-> 인증 재료 준비 / 토큰 해석 / 선행 검사 쪽 질문

UsernamePasswordAuthenticationFilter
-> username/password 기반 인증 시도

custom filter after UsernamePasswordAuthenticationFilter
-> 기준 로그인 필터 후
-> 결과 기반 후처리 / 추가 검사 / 후속 기록 쪽 질문
```

```text
bearer-token chain
custom filter before BearerTokenAuthenticationFilter
-> 아직 bearer token 인증 전
-> 헤더 정규화 / tenant 선택 / 선행 차단 쪽 질문

BearerTokenAuthenticationFilter
-> Authorization 헤더에서 bearer token 추출 및 검증 시도

custom filter after BearerTokenAuthenticationFilter
-> bearer token 인증 후
-> claim 기반 후처리 / 감사 로그 / 추가 인가 재료 준비
```

아직 "`Filter`랑 security chain이 어떻게 다른가요?"가 먼저라면 [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)에서 앞뒤 감각부터 잡고 다시 올라온다.
반대로 큰 그림은 이미 있고 "`어느 필터를 기준점으로 잡아야 하지?`"가 핵심이면 이 문서의 코드 예시와 시나리오를 바로 읽으면 된다.

초급자 기준 안전한 첫 답은 이것이다.

- "`로그인 폼`이 기준이면 `UsernamePasswordAuthenticationFilter` 앞뒤로 생각한다."
- "`Authorization: Bearer` JWT API가 기준이면 `BearerTokenAuthenticationFilter` 앞뒤로 생각한다."
- Spring Security가 이미 bearer token 인증을 제공하는 경우에는 custom JWT filter를 억지로 끼우기보다 `oauth2ResourceServer().jwt()`와 converter/decoder 쪽 설정으로 끝낼 수 있는지 먼저 본다.

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
        .addFilterBefore(tenantRoutingFilter(), BearerTokenAuthenticationFilter.class)
        .oauth2ResourceServer(oauth2 -> oauth2.jwt())
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

- bearer token API인데 기준점을 `UsernamePasswordAuthenticationFilter`로 잡아 필터 위치가 어긋났다
- `BearerTokenAuthenticationFilter`보다 앞에서 준비해야 할 일을 뒤에 뒀다
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
        .securityMatcher("/api/**")
        .csrf(csrf -> csrf.disable())
        .addFilterBefore(tenantRoutingFilter(), BearerTokenAuthenticationFilter.class)
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/actuator/health").permitAll()
            .anyRequest().authenticated()
        )
        .oauth2ResourceServer(oauth2 -> oauth2.jwt())
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
