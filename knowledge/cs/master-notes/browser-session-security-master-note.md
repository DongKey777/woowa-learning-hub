# Browser Session Security Master Note

> 한 줄 요약: browser session security is the art of making sure the browser can carry login state without letting attackers read it, force it, fix it, or replay it.

## 이 노트의 역할

이 노트는 `auth / session / token` 군집의 **보조 노트**다.

- 먼저 [Auth, Session, Token Master Note](./auth-session-token-master-note.md)로 세션/토큰/쿠키의 전체 구조를 잡는다.
- 그 다음 이 노트에서 브라우저 위협 모델만 더 깊게 본다.
- 브라우저 callback이 없는 CLI / TV / 콘솔 login이면 이 노트 대신 [OAuth Device Code Flow / Security Model](../contents/security/oauth-device-code-flow-security.md)로 분기한다.
- browser redirect는 맞지만 authorization request hardening이 먼저면 [OAuth PAR / JAR Basics](../contents/security/oauth-par-jar-basics.md)로 먼저 내려간다.

집중 범위:

- `HttpOnly`, `SameSite`, CSRF, CSP, clickjacking
- session fixation, rotation, revoke
- 브라우저 저장소와 쿠키의 공격 표면

**Difficulty: Advanced**

> retrieval-anchor-keywords: HttpOnly, SameSite, CSRF, XSS, clickjacking, CSP, session fixation, session rotation, refresh token rotation, browser session, session store, PKCE, OAuth2 code flow, device code flow, browserless login, cross-device login, PAR, JAR, pushed authorization request, request object, authorization request hardening, logout

> related docs:
> - [HTTP State, Session, Cache](../contents/network/http-state-session-cache.md)
> - [Browser Storage Threat Model for Tokens](../contents/security/browser-storage-threat-model-for-tokens.md)
> - [Signed Cookies / Server Sessions / JWT Tradeoffs](../contents/security/signed-cookies-server-sessions-jwt-tradeoffs.md)
> - [Session Fixation, Clickjacking, CSP](../contents/security/session-fixation-clickjacking-csp.md)
> - [Session Revocation at Scale](../contents/security/session-revocation-at-scale.md)
> - [XSS / CSRF / Spring Security](../contents/security/xss-csrf-spring-security.md)
> - [CORS, SameSite, Preflight](../contents/security/cors-samesite-preflight.md)
> - [OAuth2 Authorization Code Grant](../contents/security/oauth2-authorization-code-grant.md)
> - [OAuth Device Code Flow / Security Model](../contents/security/oauth-device-code-flow-security.md)
> - [OAuth PAR / JAR Basics](../contents/security/oauth-par-jar-basics.md)
> - [PKCE Failure Modes Recovery](../contents/security/pkce-failure-modes-recovery.md)
> - [Spring Security Architecture](../contents/spring/spring-security-architecture.md)
> - [Authentication vs Authorization](../contents/security/authentication-vs-authorization.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

Browser session security is not just authentication.

It is the combination of:

- how the browser stores state
- who can read that state
- who can send it automatically
- how the server rotates and revokes it
- how the UI prevents hostile framing or script injection

If any one of those pieces is weak, the session becomes a liability.

## 깊이 들어가기

### 1. Storage choice changes the attack surface

If the session or token is readable by JavaScript, XSS becomes a direct theft path.

If the browser sends the credential automatically, CSRF becomes the main risk.

So the storage question is really a threat-model question.

### 2. SameSite and CORS solve different problems

- CORS controls whether the browser may read a cross-origin response
- SameSite controls whether the browser will attach cookies to the request

That is why a browser flow can succeed in Postman and fail in the real browser.

### 3. Session fixation is about identity reuse

A secure login should rotate the session identifier after authentication.

If the ID stays the same, an attacker who prepared the session beforehand may be able to ride along after login.

### 4. Clickjacking and CSP protect different layers

- clickjacking is about misleading the user interface
- CSP is about constraining what scripts and frames can run

They both belong in the browser session story because an attacker who can frame or script the app can often turn a valid session into a stolen one.

### 5. Revocation and rotation are part of the design, not an afterthought

A session is only secure if it can be ended quickly:

- password change
- account disable
- suspicious device
- logout all devices

That means rotation, session versioning, and server-side invalidation all matter.

### 6. OAuth2 code flow and PKCE reduce browser exposure

If the browser gets an authorization code instead of raw tokens, the backend can keep more control over token issuance and storage.

PKCE further reduces interception risk in code flow scenarios.

Branch here when the flow no longer matches a browser session:

- browserless or cross-device login: [OAuth Device Code Flow / Security Model](../contents/security/oauth-device-code-flow-security.md)
- request signing or pushed authorization request before browser hardening: [OAuth PAR / JAR Basics](../contents/security/oauth-par-jar-basics.md)

## 실전 시나리오

### 시나리오 1: login works, but API calls lose the cookie in the browser

Check:

- `SameSite`
- credentials mode in fetch/XHR
- CORS allow credentials
- domain and path scope

### 시나리오 2: logout appears to work, but the old session still functions elsewhere

That is usually a revocation problem:

- session store not shared
- refresh token not rotated
- session version not checked

### 시나리오 3: XSS hits a page that stores tokens in JavaScript-accessible storage

If the token is in localStorage or sessionStorage, theft is straightforward.

### 시나리오 4: a malicious iframe tricks the user into clicking a sensitive action

This is a framing problem, not an auth problem.

Use frame blocking and a policy that prevents UI embedding where it should not exist.

## 코드로 보기

### Cookie and session hardening

```java
ResponseCookie cookie = ResponseCookie.from("session_id", sessionId)
    .httpOnly(true)
    .secure(true)
    .sameSite("Lax")
    .path("/")
    .build();
```

### Spring Security session fixation and headers

```java
@Bean
SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .sessionManagement(session -> session
            .sessionFixation(sessionFixation -> sessionFixation.migrateSession())
        )
        .headers(headers -> headers
            .frameOptions(frame -> frame.deny())
            .contentSecurityPolicy(csp -> csp
                .policyDirectives("default-src 'self'; frame-ancestors 'none'")
            )
        )
        .build();
}
```

### Session revocation sketch

```java
public void logoutAllDevices(Long userId) {
    userRepository.bumpSessionVersion(userId);
    refreshTokenRepository.revokeAllByUserId(userId);
    sessionStore.deleteAllByUserId(userId);
}
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Server session + cookie | Strong revoke control | Shared state needed | Browser-first apps |
| HttpOnly cookie + CSRF | Better script protection | CSRF rules become mandatory | Same-site or BFF flows |
| JWT in browser storage | Simple API integration | Easier theft and revocation pain | Limited cases, short TTL |
| OAuth2 code + PKCE + backend exchange | Better boundary control | More backend work | Higher-risk browser apps |
| Session versioning | Fast global revoke | Token/session shape must support it | Sensitive accounts |

The right choice depends on which attack you are least willing to tolerate.

## 꼬리질문

> Q: Why is `HttpOnly` not enough by itself?
> Intent: checks CSRF awareness.
> Core: the browser may still send the cookie automatically.

> Q: Why do we rotate the session ID on login?
> Intent: checks session fixation understanding.
> Core: the old pre-auth session must not survive as the authenticated one.

> Q: Why are CORS and SameSite different?
> Intent: checks browser policy separation.
> Core: CORS is about reading responses; SameSite is about sending cookies.

> Q: Why does browser session security include revocation?
> Intent: checks lifecycle thinking.
> Core: a credential is only safe if it can be invalidated quickly when compromised.

## 한 줄 정리

Browser session security is a boundary problem: keep the browser state usable for the user but hostile to theft, replay, fixation, and cross-site abuse.
