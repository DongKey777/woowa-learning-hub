# Security (보안)

> 인증과 인가를 섞지 않고, 세션/JWT/OAuth의 역할 경계를 분명히 이해하기 위한 정리

## 카테고리 목차

| # | 주제 | 난이도 | 파일 |
|---|------|--------|------|
| 1 | 인증과 인가의 차이 | 🟡 Intermediate | [authentication-vs-authorization.md](authentication-vs-authorization.md) |
| 2 | 비밀번호 저장: bcrypt / scrypt / argon2 | 🔴 Advanced | [password-storage-bcrypt-scrypt-argon2.md](password-storage-bcrypt-scrypt-argon2.md) |
| 3 | SQL Injection beyond PreparedStatement | 🔴 Advanced | [sql-injection-beyond-preparedstatement.md](sql-injection-beyond-preparedstatement.md) |
| 4 | XSS / CSRF / Spring Security | 🔴 Advanced | [xss-csrf-spring-security.md](xss-csrf-spring-security.md) |
| 5 | HTTPS / HSTS / MITM | 🟡 Intermediate | [https-hsts-mitm.md](https-hsts-mitm.md) |
| 6 | JWT 깊이 파기 | 🔴 Advanced | [jwt-deep-dive.md](jwt-deep-dive.md) |
| 7 | OAuth2 Authorization Code Grant | 🔴 Advanced | [oauth2-authorization-code-grant.md](oauth2-authorization-code-grant.md) |
| 8 | CORS / SameSite / Preflight | 🔴 Advanced | [cors-samesite-preflight.md](cors-samesite-preflight.md) |
| 9 | OIDC, ID Token, UserInfo 경계 | 🔴 Advanced | [oidc-id-token-userinfo-boundaries.md](oidc-id-token-userinfo-boundaries.md) |
| 10 | Secret Rotation / Leak Patterns | 🔴 Advanced | [secret-management-rotation-leak-patterns.md](secret-management-rotation-leak-patterns.md) |
| 11 | Session Fixation / Clickjacking / CSP | 🔴 Advanced | [session-fixation-clickjacking-csp.md](session-fixation-clickjacking-csp.md) |
| 12 | Service-to-Service Auth: mTLS, JWT, SPIFFE | 🔴 Advanced | [service-to-service-auth-mtls-jwt-spiffe.md](service-to-service-auth-mtls-jwt-spiffe.md) |
| 13 | API Key / HMAC Signature / Replay Protection | 🔴 Advanced | [api-key-hmac-signature-replay-protection.md](api-key-hmac-signature-replay-protection.md) |

## 학습 순서 추천

```
인증과 인가의 차이 → 비밀번호 저장 → SQL Injection → XSS/CSRF → HTTPS/HSTS → CORS/SameSite → JWT 깊이 파기 → OAuth2 Authorization Code Grant → OIDC → Spring Security 아키텍처 → API Key / HMAC Signature / Replay Protection → Service-to-Service Auth
```

## 참고

- Spring Security의 필터 체인과 `SecurityContext` 흐름은 [Spring Security 아키텍처](../spring/spring-security-architecture.md)에서 이어서 보면 좋다.
- 세션, 쿠키, JWT의 상태 차이는 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)와 함께 보면 정리가 쉽다.
- JWT 탈취와 갱신 전략은 [JWT 깊이 파기](jwt-deep-dive.md)에서, 외부 로그인과 PKCE 흐름은 [OAuth2 Authorization Code Grant](oauth2-authorization-code-grant.md)에서 이어서 보면 좋다.
- 브라우저 경계 이슈는 [CORS / SameSite / Preflight](cors-samesite-preflight.md), [Session Fixation / Clickjacking / CSP](session-fixation-clickjacking-csp.md)를 같이 보면 더 잘 보인다.
- OIDC 로그인 경계는 [OIDC, ID Token, UserInfo 경계](oidc-id-token-userinfo-boundaries.md)에서 따로 본다.
- 비밀 관리 운영은 [Secret Rotation / Leak Patterns](secret-management-rotation-leak-patterns.md)에서 별도 축으로 보는 편이 좋다.
- 내부 서비스 간 신뢰와 zero-trust 경계는 [Service-to-Service Auth: mTLS, JWT, SPIFFE](service-to-service-auth-mtls-jwt-spiffe.md)와 [Service Mesh, Sidecar Proxy](../network/service-mesh-sidecar-proxy.md)를 같이 보면 좋다.
- 외부 파트너 연동과 webhook 검증은 [API Key / HMAC Signature / Replay Protection](api-key-hmac-signature-replay-protection.md)과 [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)를 같이 보면 좋다.
- 패스워드 저장, SQL 인젝션, XSS/CSRF, HTTPS/HSTS는 인증과 인가가 아닌 "기본 보안 위생" 축으로 같이 읽는 편이 좋다.
- 인증과 인가를 시스템 전체로 설계할 때는 [System Design](../system-design/README.md)에서 요구사항과 보안 경계를 같이 잡는 것이 좋다.
