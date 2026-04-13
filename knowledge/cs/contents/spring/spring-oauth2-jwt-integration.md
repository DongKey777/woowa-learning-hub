# Spring OAuth2 + JWT 통합

> 한 줄 요약: OAuth2 로그인과 애플리케이션 JWT는 역할이 다르므로, 외부 인증 결과를 내부 토큰으로 바꾸는 경계를 분명히 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)
> - [인증과 인가의 차이](../security/authentication-vs-authorization.md)

---

## 핵심 개념

OAuth2, 세션, JWT는 같은 문제가 아니다.

- OAuth2는 외부 자원 서버/인증 서버와의 위임 및 권한 부여 흐름
- 세션은 서버가 상태를 들고 있는 로그인 상태 유지 방식
- JWT는 클라이언트가 들고 다니는 자체 서명 토큰

실무에서 흔한 구조는 이렇다.

1. 사용자가 Google/GitHub으로 로그인한다.
2. OAuth2 Authorization Code Grant로 외부 인증을 끝낸다.
3. 우리 서비스가 사용자 식별자를 매핑한다.
4. 우리 서비스의 JWT 또는 세션을 발급한다.

중요한 경계는 다음이다.

- 외부 access token은 우리 서비스 인증 토큰이 아니다
- 우리 서비스 JWT는 외부 OAuth2 토큰과 수명, 권한 범위, 폐기 정책이 다르다

---

## 깊이 들어가기

### 1. Authorization Code Grant가 기본인 이유

브라우저 기반 로그인에서는 Authorization Code Grant가 일반적이다.

흐름은 다음과 같다.

```text
Browser -> Authorization Server login
Authorization Server -> redirect with code
Backend -> exchange code for token
Backend -> map user -> issue app token
```

PKCE가 들어가면 코드 탈취 위험을 줄일 수 있다.  
모바일/SPA/브라우저 모두에서 코드가 가로채이는 상황을 가정하면, 코드만으로는 충분하지 않기 때문이다.

여기서 하나 더 중요한 점은, OAuth2 로그인 전체를 “완전 무상태”로 보기 어렵다는 것이다.  
인증 코드 교환과 redirect state 저장 구간은 짧게라도 세션이나 쿠키 저장소를 쓸 수 있고, 우리가 stateless하게 만들고 싶은 건 보통 **로그인 이후의 API 구간**이다.

### 2. 우리 서비스 JWT의 역할

우리 서비스 JWT는 보통 다음 역할을 한다.

- 내부 API 인증
- 사용자 식별자 전달
- stateless-ish한 요청 처리

하지만 JWT는 다음을 자동으로 해결하지 못한다.

- 강제 로그아웃
- 권한 변경 즉시 반영
- 토큰 탈취 대응

그래서 access token과 refresh token을 분리하고, refresh token은 서버에 저장해 폐기 가능하게 만드는 경우가 많다.

### 3. 어디서 JWT를 발급할 것인가

가장 흔한 시점은 OAuth2 로그인 성공 직후다.

- `OAuth2UserService`에서 사용자 매핑
- `AuthenticationSuccessHandler`에서 토큰 발급
- redirect response 혹은 cookie/header로 전달

이때 중요한 건 OAuth2 provider의 토큰을 그대로 내려주지 않는 것이다.  
우리 서비스는 우리 서비스의 정책에 맞는 토큰을 발급해야 한다.

### 4. 전달 방식의 선택

JWT를 클라이언트에 전달하는 방식은 크게 셋이다.

- `Authorization` header
- `HttpOnly Secure SameSite` cookie
- response body

브라우저 웹에서는 쿠키가 편하지만 CSRF를 같이 봐야 한다.  
SPA나 모바일에서는 header가 직관적이지만 storage 탈취 리스크를 관리해야 한다.

이 선택은 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)와 직결된다.

---

## 실전 시나리오

### 시나리오 1: OAuth2 access token을 우리 API 인증에 그대로 썼다

이건 경계가 무너진 설계다.

- 외부 provider 정책에 묶인다
- 만료와 권한 범위가 우리 서비스와 다르다
- 로그아웃/폐기가 어려워진다

해결은 provider token과 app token을 분리하는 것이다.

### 시나리오 2: JWT를 cookie에 넣었는데 CSRF를 놓쳤다

`HttpOnly`는 XSS 위험을 줄이지만 CSRF를 막지 못한다.  
그래서 cookie 기반 JWT는 `SameSite`, CSRF 토큰, CORS 정책까지 같이 봐야 한다.

### 시나리오 3: refresh token을 무상태처럼 다뤘다

refresh token은 보통 저장/폐기 정책이 필요하다.

- DB 저장
- Redis 저장
- device 단위 세션 추적

즉, JWT를 쓴다고 해서 전부 무상태가 되는 게 아니다.  
실제로는 refresh token과 블랙리스트 때문에 상태가 다시 생긴다.

---

## 코드로 보기

### OAuth2 로그인 후 JWT 발급 예시

```java
@Configuration
public class SecurityConfig {

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http,
                                            CustomOAuth2SuccessHandler successHandler) throws Exception {
        return http
            .oauth2Login(oauth2 -> oauth2
                .successHandler(successHandler)
            )
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .build();
    }
}
```

위 예시는 핵심 흐름만 보여준다.  
실제 운영에서는 `oauth2Login()`의 state 저장 방식과 로그인 완료 후 JWT 발급 방식을 분리해서 생각해야 한다. `SessionCreationPolicy.STATELESS`는 보통 API 요청 처리 경계에 적용하고, 인증 코드 교환 구간은 별도의 state 저장 전략이 필요할 수 있다.

```java
@Component
public class CustomOAuth2SuccessHandler implements AuthenticationSuccessHandler {
    private final JwtTokenService jwtTokenService;
    private final UserLinkService userLinkService;

    public CustomOAuth2SuccessHandler(JwtTokenService jwtTokenService, UserLinkService userLinkService) {
        this.jwtTokenService = jwtTokenService;
        this.userLinkService = userLinkService;
    }

    @Override
    public void onAuthenticationSuccess(HttpServletRequest request,
                                        HttpServletResponse response,
                                        Authentication authentication) throws IOException {
        OAuth2User oauth2User = (OAuth2User) authentication.getPrincipal();
        Long userId = userLinkService.findOrCreate(oauth2User);
        String appToken = jwtTokenService.createAccessToken(userId);

        response.setHeader("Authorization", "Bearer " + appToken);
        response.setStatus(HttpServletResponse.SC_OK);
    }
}
```

### JWT 검증 필터 예시

```java
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String token = resolveToken(request);

        if (token != null && jwtTokenService.validate(token)) {
            SecurityContextHolder.getContext().setAuthentication(jwtTokenService.toAuthentication(token));
        }

        filterChain.doFilter(request, response);
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| 세션 + OAuth2 | 폐기와 강제 로그아웃이 쉽다 | 서버 상태가 생긴다 | 전통적인 웹 앱 |
| JWT header + OAuth2 | API/모바일에 잘 맞는다 | 토큰 폐기 설계가 필요하다 | SPA, 모바일, API 서버 |
| JWT cookie + OAuth2 | 브라우저 UX가 좋다 | CSRF 대응이 필요하다 | 웹 중심 서비스 |
| provider token 재사용 | 구현이 단순하다 | 경계가 무너진다 | 거의 비추천 |

핵심 기준은 이렇다.

- 브라우저만 있으면 cookie 방식이 단순해 보이지만 CSRF를 같이 짊어진다
- 모바일/백엔드 중심이면 header 방식이 보통 더 다루기 쉽다
- 어떤 방식이든 refresh token과 폐기 정책은 별도 설계가 필요하다

---

## 꼬리질문

> Q: OAuth2와 JWT를 왜 같은 걸로 보면 안 되는가?
> 의도: 프로토콜과 토큰의 역할 분리 이해 확인
> 핵심: OAuth2는 위임, JWT는 토큰 포맷/운반 방식이다

> Q: `HttpOnly` cookie에 JWT를 넣으면 왜 끝이 아닌가?
> 의도: CSRF 이해 확인
> 핵심: XSS와 CSRF는 다른 축이다

> Q: refresh token을 왜 서버에 저장해야 하는가?
> 의도: 폐기 가능성/상태성 이해 확인
> 핵심: 로그아웃과 탈취 대응을 위해서다

> Q: OAuth2 provider access token을 우리 서비스 인증에 쓰면 뭐가 문제인가?
> 의도: 경계 설계 이해 확인
> 핵심: 우리 서비스 정책과 provider 정책이 분리되지 않는다

---

## 한 줄 정리

OAuth2는 외부 로그인 흐름이고, JWT는 우리 서비스 토큰이다. 둘을 연결하되 경계는 분명히 나눠야 운영이 된다.
