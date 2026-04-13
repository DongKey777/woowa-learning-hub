# Auth, Session, Token Master Note

> 한 줄 요약: authentication is really a storage and transport problem under a trust boundary, so the right answer depends on where state lives and who can replay it.

## 이 노트의 역할

이 노트는 `auth / session / token` 군집의 **대표 노트**다.

- 먼저 이 노트로 세션, 쿠키, JWT, refresh token의 큰 그림을 잡는다.
- 브라우저 위협 모델을 더 깊게 보고 싶으면 [Browser Session Security Master Note](./browser-session-security-master-note.md)를 이어서 본다.
- 프론트엔드와 백엔드 경계 설계를 더 보고 싶으면 [Browser Auth Frontend Backend Master Note](./browser-auth-frontend-backend-master-note.md)를 이어서 본다.
- 서비스 간 identity와 trust boundary를 더 보고 싶으면 [Trust and Identity Master Note](./trust-and-identity-master-note.md)와 [Trust Boundary Proxy Master Note](./trust-boundary-proxy-master-note.md)를 이어서 본다.

**Difficulty: Advanced**

> retrieval-anchor-keywords: session cookie, HttpOnly, SameSite, CSRF, JWT, refresh token rotation, bearer token, token revocation, session fixation, localStorage, PKCE, OIDC, logout, replay

> related docs:
> - [Authentication vs Authorization](../contents/security/authentication-vs-authorization.md)
> - [JWT Deep Dive](../contents/security/jwt-deep-dive.md)
> - [OAuth2 Authorization Code Grant](../contents/security/oauth2-authorization-code-grant.md)
> - [OIDC ID Token / UserInfo Boundaries](../contents/security/oidc-id-token-userinfo-boundaries.md)
> - [HTTP State, Session, Cache](../contents/network/http-state-session-cache.md)
> - [CORS / SameSite / Preflight](../contents/security/cors-samesite-preflight.md)
> - [XSS / CSRF / Spring Security](../contents/security/xss-csrf-spring-security.md)
> - [Spring Security Architecture](../contents/spring/spring-security-architecture.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Authentication is not one thing.
It is the combination of:

- proving identity
- carrying that proof across requests
- revoking it when needed
- preventing replay and theft

The practical choice is usually between:

- server session
- opaque token
- JWT
- browser cookie

The best answer depends on whether the client is:

- browser
- mobile app
- server-to-server
- internal admin tool

## 깊이 들어가기

### 1. Session, cookie, and token are different layers

Use the terms carefully:

- session: server-side state
- cookie: browser transport mechanism
- token: self-contained proof or lookup key

A browser session often uses a cookie to carry a session id.
A JWT system often uses a cookie or `Authorization` header to carry the token.

### 2. Browser security is mostly about theft paths

The token location matters more than the token format.

Common problems:

- `localStorage` leaks through XSS
- non-HttpOnly cookies are script-readable
- missing `SameSite` increases CSRF risk
- overly broad CORS and permissive preflight weaken trust boundaries

Useful docs:

- [CORS / SameSite / Preflight](../contents/security/cors-samesite-preflight.md)
- [XSS / CSRF / Spring Security](../contents/security/xss-csrf-spring-security.md)
- [HTTP State, Session, Cache](../contents/network/http-state-session-cache.md)

### 3. JWT solves transport, not lifecycle

JWT is good for signed claims and stateless verification.
It does not magically solve:

- logout
- forced sign-out
- role change propagation
- stolen token replay

That is why JWT often needs:

- short-lived access tokens
- refresh token rotation
- revocation or denylist support

Read with:

- [JWT Deep Dive](../contents/security/jwt-deep-dive.md)
- [OAuth2 Authorization Code Grant](../contents/security/oauth2-authorization-code-grant.md)
- [OIDC ID Token / UserInfo Boundaries](../contents/security/oidc-id-token-userinfo-boundaries.md)

### 4. Session is simpler when the server must control state

Sessions are often a better fit when:

- logout must be immediate
- permissions change frequently
- browser app is first-party only
- centralized control matters more than distributed verification

## 실전 시나리오

### 시나리오 1: SPA login

Usually needs:

- OAuth2 authorization code flow
- PKCE
- a careful decision about cookie vs header transport

### 시나리오 2: admin logout must be immediate

JWT-only designs often struggle here.
You may need:

- server-side revocation
- short access token TTL
- refresh token tracking

### 시나리오 3: browser cookie auth keeps getting CSRF bugs

The bug is usually not the cookie itself.
It is the missing combination of:

- `HttpOnly`
- `SameSite`
- CSRF token or double-submit strategy

### 시나리오 4: service-to-service auth is confused with user auth

This is where the trust boundary shifts.
Use:

- [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)
- [Spring Security Architecture](../contents/spring/spring-security-architecture.md)

## 코드로 보기

### Spring cookie settings for safer browser auth

```java
ResponseCookie cookie = ResponseCookie.from("refresh_token", token)
    .httpOnly(true)
    .secure(true)
    .sameSite("Strict")
    .path("/")
    .maxAge(Duration.ofDays(14))
    .build();
```

### Refresh token rotation sketch

```java
public TokenPair rotate(String refreshToken) {
    RefreshRecord record = refreshStore.findActive(refreshToken)
        .orElseThrow(() -> new IllegalStateException("invalid refresh token"));

    record.revoke();
    refreshStore.save(record);

    String newAccess = issuer.issueAccess(record.userId());
    String newRefresh = issuer.issueRefresh(record.userId());
    refreshStore.save(new RefreshRecord(record.userId(), newRefresh));

    return new TokenPair(newAccess, newRefresh);
}
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Session cookie | Easy revocation | Server state | Traditional web apps |
| JWT access token | Fast verification | Hard logout | Distributed APIs |
| Opaque token | Simple revocation | Lookup on every request | High-control environments |
| HttpOnly cookie | Safer against XSS theft | CSRF handling needed | Browser auth |
| Header bearer token | Flexible for APIs | Easier to leak in logs | Non-browser clients |

## 꼬리질문

> Q: Why is JWT not automatically more secure than a session?
> Intent: checks format-vs-risk understanding.
> Core: JWT is only a signed proof; theft and lifecycle remain hard.

> Q: Why do HttpOnly and SameSite matter?
> Intent: checks browser trust boundary knowledge.
> Core: they reduce script access and cross-site replay.

> Q: Why is refresh token rotation important?
> Intent: checks replay detection awareness.
> Core: it limits the damage of a stolen refresh token.

> Q: When should service-to-service auth not reuse user auth?
> Intent: checks boundary separation.
> Core: machine identity and user identity have different revocation and trust models.

## 한 줄 정리

Auth design is about choosing the right state boundary, transport boundary, and replay boundary for the client you actually have.
