---
schema_version: 3
title: Browser Storage Threat Model for Tokens
concept_id: security/browser-storage-threat-model-for-tokens
canonical: true
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- browser-token-storage-threat-model
- xss-vs-csrf-storage-choice
- refresh-token-boundary
aliases:
- browser storage threat model for tokens
- token storage threat model
- localStorage vs cookie token
- HttpOnly cookie vs localStorage
- refresh token cookie
- access token memory only
- browser token storage
- xss token theft
- csrf automatic cookie send
- 토큰 어디에 저장
- localStorage에 JWT 저장 위험
symptoms:
- JWT나 access token을 localStorage, sessionStorage, cookie 중 어디에 저장해야 하는지 공격면 기준으로 못 고르겠어
- HttpOnly cookie는 XSS에 강하지만 CSRF를 다시 봐야 한다는 말이 헷갈려
- refresh token과 access token을 같은 저장소에 두면 피해 범위가 왜 커지는지 모르겠어
intents:
- design
- comparison
prerequisites:
- network/cookie-session-jwt-browser-flow-primer
- security/xss-csrf-basics
next_docs:
- security/signed-cookies-server-sessions-jwt-tradeoffs
- security/csrf-in-spa-bff-architecture
- security/oauth-client-authentication-private-key-jwt-mtls
- system-design/browser-bff-session-boundary-primer
linked_paths:
- contents/network/cookie-session-jwt-browser-flow-primer.md
- contents/security/session-cookie-jwt-basics.md
- contents/security/xss-csrf-basics.md
- contents/security/signed-cookies-server-sessions-jwt-tradeoffs.md
- contents/security/jwt-deep-dive.md
- contents/security/csrf-in-spa-bff-architecture.md
- contents/security/oauth-client-authentication-private-key-jwt-mtls.md
- contents/system-design/browser-bff-session-boundary-primer.md
- contents/spring/spring-oauth2-jwt-integration.md
confusable_with:
- security/signed-cookies-server-sessions-jwt-tradeoffs
- security/csrf-in-spa-bff-architecture
- system-design/browser-bff-session-boundary-primer
- security/xss-csrf-basics
forbidden_neighbors: []
expected_queries:
- JWT를 localStorage에 저장하는 것이 XSS 관점에서 왜 위험한지 설명해줘
- HttpOnly cookie에 token을 넣으면 XSS와 CSRF 공격면이 어떻게 달라져?
- access token은 memory-only, refresh token은 HttpOnly cookie로 나누는 이유가 뭐야?
- sessionStorage와 IndexedDB가 token 저장에 안전한 중간지대가 아닌 이유는 뭐야?
- 브라우저 token storage는 편의성이 아니라 threat model 선택이라는 뜻을 설명해줘
contextual_chunk_prefix: |
  이 문서는 browser token storage를 localStorage, sessionStorage, IndexedDB, HttpOnly cookie, memory-only로 비교하며 XSS token theft와 CSRF automatic cookie send 사이의 threat model tradeoff를 다루는 advanced deep dive다.
  JWT localStorage risk, HttpOnly cookie CSRF, refresh token storage, access token memory only, token handler pattern, BFF session translation 같은 자연어 설계 질문이 본 문서에 매핑된다.
---
# Browser Storage Threat Model for Tokens

> 한 줄 요약: token storage는 편의성 문제가 아니라 공격면 선택 문제다. localStorage, sessionStorage, IndexedDB, cookie는 각각 XSS와 CSRF에 다른 모양으로 노출된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - `[primer]` [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - `[primer]` [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md)
> - `[primer]` [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
> - `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
> - `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
> - `[follow-up]` [Signed Cookies / Server Sessions / JWT Tradeoffs](./signed-cookies-server-sessions-jwt-tradeoffs.md)
> - `[deep dive]` [JWT 깊이 파기](./jwt-deep-dive.md)
> - `[deep dive]` [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - `[deep dive]` [CORS, SameSite, Preflight](./cors-samesite-preflight.md)
> - `[deep dive]` [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
> - `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - `[deep dive]` [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)
> - `[deep dive]` [Spring OAuth2 + JWT 통합](../spring/spring-oauth2-jwt-integration.md)
> - `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)
> - `[catalog]` [Security README: Browser / Server Boundary deep dive catalog](./README.md#browser--server-boundary-deep-dive-catalog)

retrieval-anchor-keywords: browser storage, localStorage, sessionStorage, IndexedDB, HttpOnly cookie, token theft, XSS, CSRF, refresh token cookie, bearer token, storage threat model, token handler pattern, BFF session translation, server-side confidential client, token endpoint client auth, private_key_jwt, mTLS client auth, browser server boundary catalog, security readme browser server boundary, browser session troubleshooting path, browser session troubleshooting safe next step, primer follow-up deep dive ladder, primer bridge deep dive ladder, beginner auth storage entrypoint, safe next step before deep dive, auth storage primer bridge
retrieval-anchor-keywords: when to stop and branch auth storage, login loop stop and branch, beginner login loop return path, auth storage login loop beginner warning, login loop primer bridge return, auth storage deep dive stop here, login loop before storage deep dive, cookie header missing before storage, safe next step login loop, browser session primer bridge return

---

> **When to stop and branch**
>
> - 이 문서는 `storage` 설계 비교용 `deep dive`다. 지금 증상이 `로그인 직후 다시 /login`, `cookie는 보이는데 또 로그인`, `SavedRequest`/redirect loop 라면 여기서 더 내려가지 말고 beginner route로 먼저 돌아간다.
> - 가장 안전한 순서는 `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)다. 이 route가 storage deep dive 전에 밟는 `safe next step`이다.
> - 그 route에서 `request Cookie` header가 실제로 비는 것으로 보이면 이 문서가 아니라 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)를 먼저 본다.
> - `request Cookie`는 실리는데도 browser-visible token / cookie / BFF storage trade-off를 설계해야 할 때만 이 문서로 돌아온다.

## 핵심 개념

브라우저에 token을 어디에 저장할지는 단순한 구현 디테일이 아니다.
그 선택은 누가 token을 읽을 수 있는지, 누가 자동으로 보낼 수 있는지, 탈취 후 재사용이 얼마나 쉬운지를 결정한다.

대표적인 저장소는 다음과 같다.

- `localStorage`: JS에서 읽기 쉽다
- `sessionStorage`: 탭 단위로 분리되지만 JS 접근 가능하다
- `IndexedDB`: 구조화 저장이 가능하지만 JS 접근 가능하다
- `HttpOnly cookie`: JS로 읽기 어렵지만 브라우저가 자동 전송할 수 있다

따라서 핵심 질문은 "어디가 편한가"가 아니라 "어떤 공격을 더 두려워하는가"다.

---

## 깊이 들어가기

### 1. localStorage의 공격면

localStorage는 개발이 쉽다.

- 코드에서 바로 읽는다
- SPA와 잘 맞는다
- 전송을 직접 제어할 수 있다

하지만 XSS가 한 번 생기면 token이 바로 새어 나간다.

- `window.localStorage.getItem(...)`을 읽는다
- 악성 스크립트가 외부로 전송한다
- refresh token까지 넣으면 피해가 커진다

즉 localStorage는 "저장"에는 편하지만 "탈취"에 약하다.

### 2. cookie의 공격면

HttpOnly cookie는 JS로 읽기 어렵다.

장점:

- XSS로 즉시 토큰을 덤핑하기 어렵다
- 서버가 session-like 경험을 제공하기 쉽다

단점:

- 브라우저가 자동으로 보낼 수 있다
- CSRF 방어가 다시 중요해진다
- SameSite 설정과 origin 검증이 필요하다

즉 cookie는 "읽기"보다 "자동 전송"이 문제다.

### 3. sessionStorage와 IndexedDB는 안전한 중간지대가 아니다

둘 다 JS로 접근 가능하다.

- XSS에는 여전히 취약하다
- 브라우저 종료/탭 종료 행동이 다르다
- 복잡한 앱에서 토큰 관리가 애매해진다

그래서 "localStorage보다 나으니 충분히 안전하다"는 결론은 위험하다.

### 4. access token과 refresh token의 저장 위치는 다를 수 있다

실무에서는 종종 혼합한다.

- access token은 memory-only 또는 짧은 수명
- refresh token은 HttpOnly cookie

이렇게 하면 access token 탈취 기간을 줄이면서, refresh token은 CSRF 경계를 같이 설계할 수 있다.

다만 refresh token이나 code exchange를 브라우저 밖으로 옮기는 순간, 그 서버/BFF가 token endpoint에서 자신을 어떻게 증명할지도 따로 정해야 한다. 즉 storage 경계와 confidential client auth 경계는 다른 질문이며, follow-up은 [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)로 이어진다.

### 5. memory-only도 만능은 아니다

메모리 저장은 새로고침에 약하고, 앱 상태 동기화가 어렵다.

- 페이지 리로드 시 token이 사라질 수 있다
- 멀티탭에서 상태가 분리된다
- 백그라운드 갱신이 복잡해진다

그래서 "memory-only가 항상 최고"가 아니라, 유실과 재인증 UX를 같이 봐야 한다.

---

## 실전 시나리오

### 시나리오 1: XSS가 터졌는데 localStorage token이 털림

문제:

- 공격자가 스크립트를 주입한다
- token을 바로 읽어 외부로 보낸다

대응:

- XSS를 먼저 막는다
- 토큰 저장 위치를 HttpOnly cookie로 옮길지 검토한다
- access token 수명을 짧게 가져간다

### 시나리오 2: HttpOnly cookie로 바꿨더니 CSRF가 다시 생김

문제:

- 브라우저가 자동으로 cookie를 실어 보낸다

대응:

- CSRF token을 추가한다
- SameSite와 Origin 검증을 같이 둔다
- 상태 변경 요청을 더 엄격히 잠근다

### 시나리오 3: refresh token을 localStorage에 넣었다가 오래 살아남음

문제:

- refresh token은 장기 bearer credential인데 JS 접근 가능하다

대응:

- refresh token은 보통 cookie 또는 서버 저장소로 옮긴다
- rotation과 reuse detection을 함께 쓴다

---

## 코드로 보기

### 1. localStorage 저장 예시

```javascript
localStorage.setItem("access_token", token);
```

이 방식은 단순하지만 XSS 방어가 더 중요해진다.

### 2. HttpOnly cookie 개념

```http
Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Lax; Path=/auth/refresh
```

이 방식은 JS 읽기를 막지만 CSRF 대응이 필요하다.

### 3. memory-only access token 개념

```javascript
let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}
```

이 방식은 새로고침과 탭 동기화 문제가 있다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| localStorage | 구현이 쉽다 | XSS에 매우 약하다 | 비권장, 매우 제한적 상황 |
| sessionStorage | 탭 단위로 분리된다 | JS 접근 가능, XSS에 취약 | 낮은 위험의 임시 상태 |
| IndexedDB | 구조화 저장이 가능하다 | JS 접근 가능, 복잡하다 | 일반 token 저장엔 신중 |
| HttpOnly cookie | JS 노출을 줄인다 | CSRF 대응이 필요하다 | 브라우저 기반 서비스 |
| memory-only | 탈취면이 줄어든다 | 재시작/새로고침에 약하다 | 짧은 수명 access token |

판단 기준은 이렇다.

- XSS를 더 두려워하는가
- CSRF를 더 두려워하는가
- 토큰 재발급 UX를 얼마나 허용하는가
- 브라우저에서 token을 꼭 직접 읽어야 하는가

---

## 꼬리질문

> Q: localStorage가 왜 위험한가요?
> 의도: JS 접근성과 XSS의 관계를 아는지 확인
> 핵심: 스크립트가 읽어서 즉시 탈취할 수 있기 때문이다.

> Q: HttpOnly cookie는 왜 항상 더 안전하지 않나요?
> 의도: CSRF와 자동 전송 위험을 이해하는지 확인
> 핵심: 브라우저가 자동으로 보내므로 CSRF 방어가 필요하다.

> Q: access token과 refresh token을 같은 저장소에 넣어도 되나요?
> 의도: 수명과 피해 범위를 분리하는지 확인
> 핵심: 보통은 분리하고, refresh token은 더 엄격하게 다룬다.

> Q: refresh token을 서버로 옮기면 browser storage 문제는 끝인가요?
> 의도: storage 선택과 server-side client authentication을 분리하는지 확인
> 핵심: 아니다. 브라우저 밖으로 옮긴 뒤에는 그 서버/BFF의 token endpoint auth 방식을 [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)에서 이어 결정해야 한다.

> Q: memory-only 저장은 왜 운영이 어려울 수 있나요?
> 의도: UX와 복구 문제를 이해하는지 확인
> 핵심: 새로고침 시 사라지고 멀티탭/복구가 불편하다.

## 한 줄 정리

브라우저 token storage는 "어디에 넣을까"가 아니라 "XSS와 CSRF 중 어떤 공격면을 더 줄일까"의 선택이다.
