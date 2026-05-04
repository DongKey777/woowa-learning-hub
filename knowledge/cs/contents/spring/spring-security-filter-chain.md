---
schema_version: 3
title: Spring Security Filter Chain
concept_id: spring/spring-security-filter-chain
canonical: false
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
aliases:
- Spring Security filter chain
- SecurityFilterChain
- DelegatingFilterProxy
- ExceptionTranslationFilter
- AuthorizationFilter
intents:
- deep_dive
linked_paths:
- contents/spring/spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md
- contents/spring/spring-security-filter-chain-ordering.md
- contents/security/auth-failure-response-401-403-404.md
- contents/spring/spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card.md
- contents/security/session-cookie-jwt-basics.md
forbidden_neighbors:
- contents/spring/spring-mvc-controller-basics.md
expected_queries:
- Spring Security filter chain은 어떤 순서로 인증과 인가를 처리해?
- ExceptionTranslationFilter가 401과 403을 어떻게 가르지?
- permitAll인데 invalid bearer token 때문에 401이 나는 이유가 뭐야?
- SecurityFilterChain과 서블릿 Filter는 어떻게 연결돼?
contextual_chunk_prefix: |
  이 문서는 보안 검사를 어떤 순서로 줄세워서 요청마다 통과시키는지, Spring
  Security filter chain의 인증 → 인가 → 예외 변환 흐름을 학습자가 깊이
  이해하는 deep_dive다. 보안 검사 순서, 어떤 검사 먼저, 요청마다 통과
  시키는 흐름, filter chain order, ExceptionTranslationFilter 같은 자연어
  paraphrase가 본 문서의 핵심 메커니즘에 매핑된다.
---

# Spring Security Filter Chain

> 한 줄 요약: Spring Security는 "체크리스트를 도는 인터셉터"가 아니라 서블릿 필터 체인 앞단에 끼워진 **별도의 필터 체인**이고, 인증과 인가는 체인 안의 서로 다른 단계에서 서로 다른 책임으로 돈다 — 이 순서를 이해해야 401과 403의 경계, JWT/OAuth 흐름, `permitAll()`이 통하지 않는 이유를 설명할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring Actuator Exposure Security](./spring-actuator-exposure-security.md)
> - [Spring CORS / Security vs MVC Ownership](./spring-cors-security-vs-mvc-ownership.md)
> - [JWK Rotation / Cache Invalidation / `kid` Rollover](../security/jwk-rotation-cache-invalidation-kid-rollover.md)

### Retrieval Anchors

- `Spring Security filter chain`
- `SecurityFilterChain`
- `DelegatingFilterProxy`
- `FilterChainProxy`
- `SecurityContextHolder`
- `UsernamePasswordAuthenticationFilter`
- `BearerTokenAuthenticationFilter`
- `ExceptionTranslationFilter`
- `FilterSecurityInterceptor`
- `AuthorizationFilter`
- `AccessDeniedHandler`
- `AuthenticationEntryPoint`
- `JWT filter chain`
- `OAuth2 resource server`
- `인증 vs 인가`
- `Spring Security 체인 순서`

## 핵심 개념

Spring Security가 헷갈리는 이유는 "애플리케이션 필터가 아니다"라는 점이 잘 설명되지 않아서다.

- 서블릿 컨테이너는 한 줄짜리 필터 체인을 돈다. 그 중 한 칸이 `DelegatingFilterProxy` = **Spring Security로 향하는 문** 하나다
- `DelegatingFilterProxy`가 호출하는 실체는 `FilterChainProxy`다. 이 친구는 내부에 **여러 개의 `SecurityFilterChain`** 을 들고 있고, 요청 URL 패턴에 따라 그 중 하나를 고른다
- 고른 체인은 10~15개의 **security 전용 필터**로 이뤄져 있다. 각 필터가 인증/인가/세션/CSRF/CORS를 한 단계씩 담당한다

즉 "Spring Security를 건드린다"는 건 보통 이 `SecurityFilterChain` 한 개의 필터 순서와 구성을 바꾼다는 뜻이다. 애플리케이션의 서블릿 필터를 건드리는 게 아니다.

그리고 중요한 한 마디: **인증과 인가는 같은 필터가 아니다.** 인증 필터는 체인 앞쪽에서 `SecurityContext`에 principal을 심는다. 인가 필터(`AuthorizationFilter` / 구버전 `FilterSecurityInterceptor`)는 체인 맨 끝에서 그 context를 읽어 접근 여부를 판단한다. 이 경계가 401과 403을 가른다.

## 깊이 들어가기

### 1. 체인의 표준 순서 (대략)

패턴에 따라 달라지지만, 전형적인 순서는 다음과 같다 (Spring Security 6 기준).

1. `DisableEncodeUrlFilter` — 세션 ID를 URL에 붙이는 걸 막는다
2. `WebAsyncManagerIntegrationFilter` — 비동기 요청에 SecurityContext 전파
3. `SecurityContextHolderFilter` — 요청 시작/끝에 `SecurityContextHolder`를 초기화/정리
4. `HeaderWriterFilter` — 보안 응답 헤더(X-Frame-Options 등)
5. `CorsFilter` — CORS preflight 처리
6. `CsrfFilter` — CSRF 토큰 검증
7. `LogoutFilter` — `/logout` 요청을 가로채 세션/쿠키 정리
8. **인증 필터들** — `UsernamePasswordAuthenticationFilter`, `BearerTokenAuthenticationFilter`, `BasicAuthenticationFilter`, `OAuth2LoginAuthenticationFilter` 중 구성된 것
9. `RequestCacheAwareFilter` — 인증 후 원래 요청으로 되돌리는 post-login 리다이렉트 지원
10. `SecurityContextHolderAwareRequestFilter` — 서블릿 API 수준에 principal 노출
11. `AnonymousAuthenticationFilter` — 인증 실패 시 익명 principal 주입
12. `SessionManagementFilter` — 세션 정책(동시 로그인 등)
13. **`ExceptionTranslationFilter`** — 체인 뒤에서 던진 예외를 401/403으로 번역
14. **`AuthorizationFilter`** — 최종 접근 제어 판정

여기서 질문이 생긴다: **왜 예외 번역 필터가 인가 필터 앞에 있을까?**

답은 단순하다. 인가 필터가 던지는 `AccessDeniedException`/`AuthenticationException`을 캐치하려면, 예외 번역 필터가 **그 위에** 있어야 한다. Spring Security의 필터 체인은 Russian doll이어서, 앞에 있는 필터가 뒤 필터를 호출한 후 그 결과를 감싼다. 즉 `ExceptionTranslationFilter`는 "뒤 필터를 try로 감싸고 catch해서 HTTP 응답으로 번역"하는 역할이다.

### 2. 401 vs 403 — 어디서 갈라지나

`ExceptionTranslationFilter`가 두 예외를 받으면 다음과 같이 분기한다.

- `AuthenticationException` → 아직 인증되지 않았다는 뜻 → `AuthenticationEntryPoint`로 보낸다 (기본값: 401 또는 로그인 페이지)
- `AccessDeniedException` + 익명 사용자 → 동일하게 `AuthenticationEntryPoint` → 401
- `AccessDeniedException` + 이미 인증된 사용자 → `AccessDeniedHandler` → 403

즉 "로그인은 했는데 권한이 없다"는 403이고, "토큰이 없다/유효하지 않다"는 401이다. 403에서 "로그인해 봐라"라는 메시지를 돌려주는 건 잘못된 구현이다.

Customization 포인트:
- 401 응답 본문을 바꾸고 싶다 → `AuthenticationEntryPoint` 구현 교체
- 403 응답 본문을 바꾸고 싶다 → `AccessDeniedHandler` 구현 교체

### 3. JWT / OAuth2 Resource Server 흐름

JWT 기반 리소스 서버는 `UsernamePasswordAuthenticationFilter` 대신 `BearerTokenAuthenticationFilter`가 인증을 맡는다.

```
클라이언트 → Authorization: Bearer eyJ... 헤더 포함
  ↓
BearerTokenAuthenticationFilter
  ↓ BearerTokenResolver가 헤더에서 토큰 추출
  ↓ AuthenticationManager → JwtAuthenticationProvider
  ↓ JwtDecoder(예: NimbusJwtDecoder) → JWKS로 서명 검증, exp/nbf/iss/aud 확인
  ↓ 성공 시 JwtAuthenticationToken을 SecurityContext에 저장
  ↓ 체인 나머지 통과
AuthorizationFilter → @PreAuthorize / authorizeHttpRequests 규칙 판정
```

핵심 포인트:

- **JWKS 캐시**: `JwtDecoder`가 발급자의 JWKS 엔드포인트를 주기적으로 fetch한다. 키 로테이션 시 기존 토큰이 갑자기 실패할 수 있으므로 캐시 TTL과 grace period가 중요하다
- **`iss`/`aud` 검증**: 기본 decoder는 `iss`만 검증한다. `aud` 검증은 `OAuth2TokenValidator`를 수동으로 추가해야 한다 — 많은 팀이 이걸 잊는다
- **리프레시 토큰은 리소스 서버에 없다**: 리프레시는 인증 서버(authorization server) 책임이다. 리소스 서버는 access token만 검증한다

### 4. `permitAll()`이 안 통하는 흔한 원인

```java
http.authorizeHttpRequests(auth -> auth
    .requestMatchers("/public/**").permitAll()
    .anyRequest().authenticated());
```

이렇게 써도 `/public/hello`가 401이 나는 경우가 있다. 원인은 **`BearerTokenAuthenticationFilter`가 체인의 앞쪽에서 먼저 동작**하기 때문이다.

- 요청에 Authorization 헤더가 **포함된 채** `/public/hello`로 왔다면, 인증 필터가 토큰을 검증한다
- 토큰이 만료/무효 → `InvalidBearerTokenException` → 401
- `AuthorizationFilter`까지 도달하지도 못하고 401이 나간다

즉 `permitAll()`은 "인가는 스킵"이라는 뜻이고, **인증 시도 자체를 스킵하진 않는다**. 완전히 뚫린 공개 엔드포인트를 원한다면 패턴을 `SecurityFilterChain` 수준에서 **다른 체인**으로 분리하거나, `BearerTokenResolver`가 해당 경로에서 토큰을 무시하게 구성해야 한다.

## 실전 시나리오

### 시나리오 1: "로그인은 됐는데 403이 계속 나요"

인증은 성공했지만 인가 단계에서 막힌 것. 원인 후보:

- `@PreAuthorize("hasRole('ADMIN')")`에 달린 역할이 토큰/principal의 authorities와 **prefix 불일치**: Spring Security는 `hasRole("ADMIN")` 검사 시 내부적으로 `ROLE_ADMIN` 권한을 찾는다. 토큰에 `ADMIN`만 있으면 일치하지 않는다
- JWT scope가 Spring의 `GrantedAuthority`로 매핑되지 않음 — `JwtAuthenticationConverter`를 커스터마이즈해야 한다

### 시나리오 2: Preflight CORS가 CSRF 필터에서 거부된다

CORS preflight(`OPTIONS`)가 CSRF 필터에서 막힌다. 원인: `CorsFilter`가 `CsrfFilter`보다 **앞**에 있어야 preflight가 CSRF 검증을 우회할 수 있다. `http.cors()`를 호출하지 않았거나 별도 `CorsFilter`를 엉뚱한 위치에 끼웠다면 순서가 뒤집힌다.

처방: `http.cors(cors -> cors.configurationSource(...))`로 `CorsFilter`를 Spring Security가 관리하게 하고, 순서는 DSL이 알아서 잡게 둔다.

### 시나리오 3: Actuator가 외부에 노출됐다

`/actuator/**`가 인증 없이 접근 가능해졌다. 원인: `SecurityFilterChain`이 둘 이상 정의되어 있고, actuator 체인이 먼저 매칭되면서 `permitAll()`로 설정되어 있다.

처방: `@Order`를 명시하고, actuator 체인은 **더 좁은** request matcher와 **강한** 인증 규칙을 갖게 한다. 기본 체인이 먼저 매칭되지 않게 한다.

## 코드로 보기

```java
@Configuration
@EnableWebSecurity
class SecurityConfig {

    @Bean
    SecurityFilterChain api(HttpSecurity http) throws Exception {
        return http
            .securityMatcher("/api/**")
            .csrf(csrf -> csrf.disable())  // stateless API
            .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(HttpMethod.GET, "/api/health").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt.jwtAuthenticationConverter(jwtAuthConverter())))
            .exceptionHandling(eh -> eh
                .authenticationEntryPoint(new Http401EntryPoint())
                .accessDeniedHandler(new Http403AccessDeniedHandler()))
            .build();
    }

    @Bean
    JwtAuthenticationConverter jwtAuthConverter() {
        JwtGrantedAuthoritiesConverter authorities = new JwtGrantedAuthoritiesConverter();
        authorities.setAuthoritiesClaimName("scope");
        authorities.setAuthorityPrefix("ROLE_");  // hasRole()과 맞추려고
        JwtAuthenticationConverter converter = new JwtAuthenticationConverter();
        converter.setJwtGrantedAuthoritiesConverter(authorities);
        return converter;
    }
}
```

중요한 건 `JwtAuthenticationConverter`를 명시했다는 것이다. 기본값은 `SCOPE_` prefix를 붙이므로 `hasRole("ADMIN")`과 맞지 않는다. prefix를 일치시키지 않으면 "토큰에는 admin이 있는데 403이 난다"는 현상이 생긴다.

## 트레이드오프

| 구성 | 장점 | 비용 |
|---|---|---|
| 단일 `SecurityFilterChain` | 순서 단순, 디버깅 쉬움 | 복잡한 앱에서 조건 분기 늘어남 |
| 여러 `SecurityFilterChain` (`@Order`) | 경로별 독립 구성 | 매칭 순서 실수 = 의도치 않은 public exposure |
| Stateful 세션 + CSRF | 전통적 웹, 안정 | REST API에 부적합 |
| Stateless JWT | SPA/API 친화 | 토큰 폐기 어려움, 블랙리스트 설계 필요 |

## 꼬리질문

- 401과 403을 결정하는 건 어느 필터인가? 두 응답이 뒤섞이면 어떤 문제가 생기나?
- `BearerTokenAuthenticationFilter`가 `AuthorizationFilter` 앞에 있는 이유는?
- `permitAll()`을 건 엔드포인트에 만료된 JWT가 딸려오면 어떤 응답이 나가는가? 왜?
- JWT의 `aud` 검증을 수동으로 추가해야 하는 이유는 뭔가?
- `@PreAuthorize("hasRole('ADMIN')")`가 동작하려면 토큰의 authorities는 정확히 어떻게 매핑되어야 하나?

## 한 줄 정리

Spring Security는 서블릿 체인 안에 들어간 **별도의 필터 체인**이고, 인증(앞쪽 필터)과 인가(뒤쪽 필터)는 분리되어 있다. 401과 403, `permitAll()`의 한계, JWT 흐름은 이 순서를 이해하면 전부 같은 모델로 설명된다.
