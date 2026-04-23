# Browser Auth Frontend Backend Master Note

> 한 줄 요약: browser auth is a front-end and back-end coordination problem where cookie policy, token storage, and CSRF rules must line up with the trust boundary.

## 이 노트의 역할

이 노트는 `auth / browser flow` 군집의 **보조 노트**다.

- 먼저 [Auth, Session, Token Master Note](./auth-session-token-master-note.md)로 인증 저장/운반 구조를 잡는다.
- 브라우저 자체 위협 모델은 [Browser Session Security Master Note](./browser-session-security-master-note.md)에서 보고,
- 이 노트에서는 `SPA / BFF / 서버 렌더링` 같은 프론트-백엔드 경계 설계를 본다.
- 브라우저 callback이 없는 CLI / TV / 콘솔 login이면 [OAuth Device Code Flow / Security Model](../contents/security/oauth-device-code-flow-security.md)로 분기한다.
- authorization request 자체를 front-channel 밖으로 밀거나 서명해야 하면 [OAuth PAR / JAR Basics](../contents/security/oauth-par-jar-basics.md)로 분기한다.

**Difficulty: Advanced**

> retrieval-anchor-keywords: HttpOnly, SameSite, CSRF, CORS, OAuth2 code flow, PKCE, OIDC login, ID token, UserInfo, external identity mapping, device code flow, browserless login, cross-device login, PAR, JAR, pushed authorization request, request object, session cookie, localStorage, Authorization header, refresh token rotation, logout, browser auth, SPA, BFF

> related docs:
> - [HTTP State, Session, Cache](../contents/network/http-state-session-cache.md)
> - [CORS, SameSite, Preflight](../contents/security/cors-samesite-preflight.md)
> - [OAuth2 Authorization Code Grant](../contents/security/oauth2-authorization-code-grant.md)
> - [OIDC, ID Token, UserInfo](../contents/security/oidc-id-token-userinfo-boundaries.md)
> - [OAuth Device Code Flow / Security Model](../contents/security/oauth-device-code-flow-security.md)
> - [OAuth PAR / JAR Basics](../contents/security/oauth-par-jar-basics.md)
> - [JWT Deep Dive](../contents/security/jwt-deep-dive.md)
> - [XSS / CSRF / Spring Security](../contents/security/xss-csrf-spring-security.md)
> - [Spring Security Architecture](../contents/spring/spring-security-architecture.md)
> - [Authentication vs Authorization](../contents/security/authentication-vs-authorization.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Browser auth is not a single mechanism.
It is the interaction between:

- browser cookie policy
- front-end request behavior
- back-end session or token issuance
- CSRF and XSS defenses
- logout and refresh behavior

The right design depends on whether the client is:

- traditional server-rendered web
- SPA
- BFF
- hybrid app

## 깊이 들어가기

### 1. Cookie, session, and token are different layers

- cookie: browser transport
- session: server-side state
- token: self-contained credential

Read with:

- [HTTP State, Session, Cache](../contents/network/http-state-session-cache.md)

### 2. CORS and SameSite solve different problems

- CORS decides whether the browser may read the response
- SameSite decides whether the browser sends the cookie

That is why a system can "work in Postman" but fail in the browser.

Read with:

- [CORS, SameSite, Preflight](../contents/security/cors-samesite-preflight.md)

### 3. OAuth2 code flow is safer than putting tokens in the browser first

The browser should receive the authorization code, not the access token directly.
The backend can then exchange code for tokens and decide how to persist state.

Read with:

- [OAuth2 Authorization Code Grant](../contents/security/oauth2-authorization-code-grant.md)
- external IdP login에서 `ID token`과 `UserInfo`를 어디까지 신뢰하고 내부 세션/JWT 발급 전에 어떤 매핑 계층을 둘지는 [OIDC, ID Token, UserInfo](../contents/security/oidc-id-token-userinfo-boundaries.md)

Branch here when the OAuth shape changes:

- no browser callback, CLI / TV login, cross-device approval: [OAuth Device Code Flow / Security Model](../contents/security/oauth-device-code-flow-security.md)
- front-channel request exposure or signed request requirement: [OAuth PAR / JAR Basics](../contents/security/oauth-par-jar-basics.md)

### 4. JWT changes the storage burden, not the trust burden

JWT helps with stateless verification, but it does not solve:

- revocation
- theft
- replay
- logout consistency

Read with:

- [JWT Deep Dive](../contents/security/jwt-deep-dive.md)

## 실전 시나리오

### 시나리오 1: SPA login works but API calls lose the cookie

Likely cause:

- `SameSite` mismatch
- credentialed fetch missing
- CORS allowlist mismatch

### 시나리오 2: logout is not immediate

Likely cause:

- JWT-only design
- no server revocation store

### 시나리오 3: browser auth keeps causing CSRF bugs

Likely cause:

- cookie-based auth without CSRF token or equivalent boundary

## 코드로 보기

### Cookie settings

```java
ResponseCookie cookie = ResponseCookie.from("session_id", sessionId)
    .httpOnly(true)
    .secure(true)
    .sameSite("Lax")
    .path("/")
    .build();
```

### Spring CORS setup

```java
registry.addMapping("/api/**")
    .allowedOrigins("https://app.example.com")
    .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
    .allowCredentials(true);
```

### Refresh rotation sketch

```java
TokenPair pair = authService.refresh(oldRefreshToken);
refreshStore.revoke(oldRefreshToken);
refreshStore.save(pair.refreshToken());
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Session cookie | Simple logout | Server state | Traditional browser apps |
| HttpOnly cookie + CSRF | Safer for browser storage | More setup | Same-site or BFF patterns |
| JWT in header | Flexible for APIs | Easier to leak or persist badly | Non-browser clients |
| OAuth2 code + BFF | Strong boundary control | More backend logic | High-security browser apps |

## 꼬리질문

> Q: Why does Postman success not guarantee browser success?
> Intent: checks browser security model awareness.
> Core: the browser applies CORS and cookie policies that Postman does not.

> Q: Why is JWT not a complete browser auth solution?
> Intent: checks lifecycle and revocation understanding.
> Core: JWT does not automatically solve logout or theft response.

> Q: Why are HttpOnly and SameSite important together?
> Intent: checks storage and replay boundary understanding.
> Core: they reduce script access and cross-site replay risk.

## 한 줄 정리

Browser auth works only when cookie policy, token lifecycle, and CORS/CSRF behavior all agree on the same trust boundary.
