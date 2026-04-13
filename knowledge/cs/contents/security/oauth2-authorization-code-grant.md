# OAuth2 Authorization Code Grant

> 한 줄 요약: Authorization Code Grant는 브라우저가 직접 토큰을 받지 않고, 인가 코드를 통해 서버가 안전하게 토큰을 교환하는 표준 흐름이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md)
> - [OAuth PAR / JAR Basics](./oauth-par-jar-basics.md)
> - [Open Redirect Hardening](./open-redirect-hardening.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - [Email Magic-Link Threat Model](./email-magic-link-threat-model.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)

retrieval-anchor-keywords: OAuth2 authorization code grant, PKCE, redirect URI, state, code exchange, authorization server, token endpoint, callback, front-channel, back-channel, browser auth

---

## 핵심 개념

OAuth2는 "로그인 프로토콜"이라기보다 **리소스 접근 위임 프레임워크**다.  
그중 Authorization Code Grant는 서버 사이드에서 가장 흔하게 쓰는 흐름이다.

핵심은 이렇다.

- 사용자는 외부 IdP에서 로그인한다
- 브라우저는 인가 코드를 받는다
- 우리 서버가 그 코드를 토큰으로 교환한다
- 우리 서비스는 그 결과로 내부 세션/JWT를 발급한다

왜 이렇게 복잡하게 하느냐가 핵심이다.

- 브라우저가 access token을 직접 다루면 탈취 위험이 커진다
- code exchange를 서버로 넘기면 client secret, PKCE, redirect URI 검증을 함께 적용할 수 있다
- 외부 인증과 내부 권한을 분리할 수 있다

---

## 깊이 들어가기

### 1. 흐름

전형적인 흐름은 아래와 같다.

```text
User -> Browser -> Authorization Server
     <- login consent
     <- authorization code
Browser -> Backend callback
Backend -> Authorization Server token endpoint
Backend <- access token / refresh token / id token
Backend -> own session/JWT issuance
```

핵심은 `code`를 직접 토큰으로 바꾸는 주체가 서버라는 점이다.  
이렇게 하면 토큰 발급에 필요한 민감 정보와 검증 로직을 서버에 묶을 수 있다.

### 2. PKCE가 왜 필요한가

PKCE(Proof Key for Code Exchange)는 code 탈취 공격을 막기 위한 추가 장치다.

문제 상황:

- 누군가 authorization code를 가로챘다
- code만 있으면 토큰 교환을 시도할 수 있다

PKCE는 이를 막는다.

1. 클라이언트가 `code_verifier`를 생성한다
2. 그 해시값인 `code_challenge`를 인증 요청에 함께 보낸다
3. 나중에 code를 교환할 때 원본 `code_verifier`를 제시해야 한다
4. Authorization Server는 둘이 맞는지 검증한다

즉 code를 훔쳐도 verifier 없이는 토큰 교환이 안 된다.

### 3. redirect URI와 state

`redirect_uri`는 고정 검증 대상이어야 한다.

- 정확히 등록된 URI만 허용해야 한다
- 와일드카드나 느슨한 비교는 open redirect 사고로 이어진다

`state`는 CSRF와 요청 연동을 위한 값이다.

- 사용자가 처음 로그인 요청을 보낸 흐름과
- callback으로 돌아오는 흐름이

같은 세션에서 시작된 것인지 확인한다.

### 4. backend integration boundary

OAuth2의 책임과 우리 서비스의 책임을 분리해야 한다.

OAuth2/IdP가 책임지는 것:

- 사용자의 외부 신원 확인
- 외부 계정의 기본 프로필 제공
- 인가 코드와 토큰 교환

우리 서비스가 책임지는 것:

- 내부 사용자 계정 매핑
- role/permission 부여
- 내부 세션/JWT 발급
- 권한 해제/정지/탈퇴 처리

이 경계를 섞으면 보통 사고가 난다.

- 외부 이메일 인증만으로 관리자 권한을 준다
- 외부 토큰을 내부 API 권한 모델로 그대로 복사한다
- IdP가 바뀌면 내부 권한까지 흔들린다

### 5. Spring Security와 연결

Spring Security에서는 OAuth2 login이 끝난 뒤 authenticated principal을 받아 내부 사용자와 연결하는 구성이 흔하다.  
그 다음에 우리 시스템의 세션이나 JWT를 별도로 발급할 수 있다.

이 부분은 [Spring Security 아키텍처](../spring/spring-security-architecture.md)와 함께 보면 연결이 쉽다.

### 6. front-channel이 아니라 flow 전체를 봐야 한다

Authorization Code Grant는 브라우저에서 시작하지만 브라우저가 전부가 아니다.

- authorization request가 노출된다
- code가 callback으로 이동한다
- token exchange는 back-channel에서 일어난다
- callback 이후 내부 세션/JWT 발급이 이어진다

이 구간마다 다른 공격이 붙는다.

- request 단계: open redirect, request parameter tampering
- code 단계: interception, replay, callback mix-up
- token 단계: refresh leak, storage leak, audience broadening

### 7. PAR/JAR가 필요한 이유

고보안 환경에서는 Authorization Code Grant만으로는 request 변조와 노출이 충분히 줄지 않을 수 있다.

- PAR는 authorization request를 먼저 서버로 보내 front-channel 노출을 줄인다
- JAR는 request object 자체를 서명해서 파라미터 변조를 줄인다

둘은 [OAuth PAR / JAR Basics](./oauth-par-jar-basics.md)에서 자세히 다룬다.

### 8. magic link와의 경계

email magic link는 사용자 입장에서는 편하지만, security boundary는 authorization code 흐름과 비슷한 면이 있다.

- 짧은 수명
- 일회성 소비
- callback 이후 세션 발급

그래서 login UX가 편하다고 검증이 사라지면 안 된다.

---

## 실전 시나리오

### 시나리오 1: authorization code가 탈취됨

원인:

- redirect URI가 느슨하다
- PKCE가 없다
- code 재사용 검증이 없다

대응:

- redirect URI를 정확히 등록한다
- PKCE를 쓴다
- code는 1회성으로 처리한다

### 시나리오 2: 소셜 로그인은 되는데 내부 권한이 꼬임

원인:

- 외부 IdP의 이메일 검증을 내부 권한 부여로 착각한다
- 사내 계정/외부 계정을 같은 테이블로 뭉갠다

대응:

- 외부 계정은 identity mapping까지만 맡긴다
- 내부 role은 별도 테이블로 관리한다

### 시나리오 3: SPA에서 토큰을 직접 들고 다니며 사고가 남

원인:

- 브라우저가 access token을 오래 보관한다
- XSS에 취약하다

대응:

- authorization code + PKCE 흐름을 쓴다
- 토큰은 서버에서 받아 세션 또는 HttpOnly cookie로 처리한다

### 시나리오 4: redirect URI가 맞아 보이는데 code가 다른 곳으로 감

원인:

- exact match 대신 prefix match를 썼다
- nested redirect를 허용했다
- open redirect가 섞였다

대응:

- redirect URI를 사전 등록하고 exact match로 검사한다
- redirect destination을 서버가 결정한다
- callback과 최종 redirect를 분리한다

### 시나리오 5: 브라우저가 token을 너무 오래 들고 있음

원인:

- SPA가 access token을 오래 보관한다
- XSS나 storage leak 경로가 있다

대응:

- 짧은 access token과 refresh rotation을 쓴다
- browser storage 전략을 다시 잡는다
- 가능하면 HttpOnly cookie 또는 BFF를 검토한다

### 시나리오 6: callback이 갑자기 실패함

체크할 순서:

1. redirect URI 등록값 확인
2. state 일치 여부 확인
3. authorization server clock skew 확인
4. token endpoint 네트워크/TLS 확인
5. scope 동의 화면 변경 여부 확인

---

## 코드로 보기

### 1. Spring Security OAuth2 로그인 설정

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/", "/login", "/public/**").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2Login(oauth2 -> oauth2
                .userInfoEndpoint(userInfo -> userInfo
                    .userService(customOAuth2UserService())
                )
                .successHandler(oAuth2SuccessHandler())
            )
            .build();
    }
}
```

### 2. 외부 사용자와 내부 사용자 매핑

```java
public class OAuth2SuccessHandler implements AuthenticationSuccessHandler {

    @Override
    public void onAuthenticationSuccess(HttpServletRequest request,
                                        HttpServletResponse response,
                                        Authentication authentication) throws IOException {
        OAuth2User oauthUser = (OAuth2User) authentication.getPrincipal();
        String email = (String) oauthUser.getAttributes().get("email");

        UserAccount account = userAccountService.findOrCreateByEmail(email);
        String internalToken = internalTokenService.issue(account.getId(), account.getRoles());

        response.sendRedirect("/auth/success?token=" + URLEncoder.encode(internalToken, StandardCharsets.UTF_8));
    }
}
```

실무에서는 query string으로 토큰을 넘기기보다 HttpOnly cookie나 서버 세션으로 처리하는 편이 낫다.

### 3. PKCE 개념 코드

```java
String codeVerifier = randomUrlSafeString();
String codeChallenge = base64UrlSha256(codeVerifier);

String authorizeUrl = UriComponentsBuilder
    .fromUriString("https://auth.example.com/oauth2/authorize")
    .queryParam("client_id", "client-123")
    .queryParam("redirect_uri", "https://app.example.com/callback")
    .queryParam("response_type", "code")
    .queryParam("scope", "openid profile email")
    .queryParam("state", state)
    .queryParam("code_challenge", codeChallenge)
    .queryParam("code_challenge_method", "S256")
    .build(true)
    .toUriString();
```

### 4. state / verifier / exact redirect 저장 개념

```java
public void beginLogin(String flowId) {
    String state = stateService.issue(flowId);
    String verifier = pkceStore.save(flowId);
    redirectRegistry.requireExactMatch("https://app.example.com/callback");
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| Authorization Code Grant | code를 서버가 교환하므로 비교적 안전하다 | 흐름이 복잡하다 | 웹/SPA/모바일 대부분 |
| Implicit Grant | 과거에 단순했다 | 토큰 노출 위험이 커서 비권장 | 사실상 새 설계에는 잘 쓰지 않는다 |
| PKCE 포함 | code 탈취 방어가 된다 | 구현과 검증 포인트가 늘어난다 | public client, SPA, mobile |
| 내부 세션 발급 | 강제 로그아웃과 권한 제어가 쉽다 | 서버 상태를 관리해야 한다 | 브라우저 중심 서비스 |
| 내부 JWT 발급 | 수평 확장에 유리하다 | 폐기와 추적이 어렵다 | API 중심 서비스 |

핵심 판단 기준은 다음이다.

- 브라우저가 토큰을 직접 보관해야 하는가
- 외부 IdP 신원을 어디까지 신뢰할 것인가
- 내부 권한 모델은 누가 소유하는가
- code/code_verifier/state 검증을 어디서 끝낼 것인가
- PAR/JAR가 필요한 고보안 client인지
- refresh token은 rotation하고 reuse detection을 둬야 하는지

---

## 꼬리질문

> Q: Authorization Code Grant가 왜 직접 access token을 받는 방식보다 안전한가?
> 의도: code 교환과 브라우저 노출 분리를 이해하는지 확인
> 핵심: 브라우저가 민감 토큰을 직접 다루지 않기 때문이다.

> Q: PKCE는 왜 필요한가?
> 의도: code interception attack 이해 여부 확인
> 핵심: code를 훔쳐도 verifier 없이는 토큰 교환을 못 하게 한다.

> Q: OAuth2와 로그인은 같은 말인가?
> 의도: 프로토콜과 사용자 경험을 구분하는지 확인
> 핵심: OAuth2는 위임 프레임워크이고, 로그인은 그 위에서 구현되는 UX다.

> Q: 외부 IdP 이메일 인증만 믿고 내부 관리자 권한을 줄 수 있나?
> 의도: 외부 신원 확인과 내부 인가를 분리하는지 확인
> 핵심: 안 된다. 내부 권한은 내부 도메인이 소유해야 한다.

## 한 줄 정리

OAuth2 Authorization Code Grant는 외부 신원을 안전하게 받아오고, PKCE와 redirect/state 검증으로 code 탈취를 막으면서, 내부 세션/JWT와 권한 모델은 우리 서비스가 따로 책임지게 하는 흐름이다.
