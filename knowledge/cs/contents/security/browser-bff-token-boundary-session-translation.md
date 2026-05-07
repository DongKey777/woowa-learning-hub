---
schema_version: 3
title: Browser / BFF Token Boundary / Session Translation
concept_id: security/browser-bff-token-boundary-session-translation
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- BFF token handler pattern
- browser server token boundary
- session translation
- server-side token storage
aliases:
- BFF token handler pattern
- browser server token boundary
- session translation
- server-side token storage
- opaque browser session
- refresh token on server
- SPA BFF auth
- token handler
- downstream token cache
- browser to backend boundary
- elevated session
- step-up session
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/browser-bff-session-boundary-primer.md
- contents/security/oauth2-authorization-code-grant.md
- contents/security/logout-scope-primer.md
- contents/security/browser-storage-threat-model-for-tokens.md
- contents/security/csrf-in-spa-bff-architecture.md
- contents/security/oidc-id-token-userinfo-boundaries.md
- contents/security/oauth-par-jar-basics.md
- contents/security/oauth-client-authentication-private-key-jwt-mtls.md
- contents/security/oidc-backchannel-logout-session-coherence.md
- contents/security/step-up-session-coherence-auth-assurance.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Browser / BFF Token Boundary / Session Translation 핵심 개념을 설명해줘
- BFF token handler pattern가 왜 필요한지 알려줘
- Browser / BFF Token Boundary / Session Translation 실무 설계 포인트는 뭐야?
- BFF token handler pattern에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Browser / BFF Token Boundary / Session Translation를 다루는 deep_dive 문서다. 브라우저와 서버 경계에서 가장 중요한 질문은 "토큰을 누가 직접 보관하고 누가 외부 IdP 및 downstream API를 대신 호출하는가"이며, BFF는 쿠키 세션과 서버 측 token cache를 이용해 browser-visible credential을 줄이는 대신 CSRF, logout, session mapping을 더 엄격하게 설계해야 한다. 검색 질의가 BFF token handler pattern, browser server token boundary, session translation, server-side token storage처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Browser / BFF Token Boundary / Session Translation

> 한 줄 요약: 브라우저와 서버 경계에서 가장 중요한 질문은 "토큰을 누가 직접 보관하고 누가 외부 IdP 및 downstream API를 대신 호출하는가"이며, BFF는 쿠키 세션과 서버 측 token cache를 이용해 browser-visible credential을 줄이는 대신 CSRF, logout, session mapping을 더 엄격하게 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - `[primer bridge]` [Browser BFF Session Boundary Primer](../system-design/browser-bff-session-boundary-primer.md)
> - `[primer bridge]` [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - `[primer bridge]` [Logout Scope Primer](./logout-scope-primer.md)
> - `[deep dive]` [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
> - `[deep dive]` [OIDC, ID Token, UserInfo](./oidc-id-token-userinfo-boundaries.md)
> - `[deep dive]` [OAuth PAR / JAR Basics](./oauth-par-jar-basics.md)
> - `[deep dive]` [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)
> - `[deep dive]` [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)
> - `[deep dive]` [Step-Up Session Coherence / Auth Assurance](./step-up-session-coherence-auth-assurance.md)
> - `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md)
> - `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - `[deep dive]` [Session Store Design at Scale](../system-design/session-store-design-at-scale.md)
> - `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md)

retrieval-anchor-keywords: BFF token handler pattern, browser server token boundary, session translation, server-side token storage, opaque browser session, refresh token on server, SPA BFF auth, token handler, downstream token cache, browser to backend boundary, elevated session, step-up session, session store outage, PAR, JAR, pushed authorization request, request object, device code flow, cross-device login, confidential client, token endpoint client auth, private_key_jwt, mTLS client auth, OIDC login, ID token vs UserInfo, claim normalization, external identity mapping, issuer subject mapping, browser server boundary catalog, security readme browser server boundary, browser bff primer bridge, session translation deep dive, bff session recovery route, browser session route ladder

---

## 핵심 개념

브라우저 인증 설계에서 자주 놓치는 질문이 있다.

- 브라우저가 access token을 직접 들고 있는가
- refresh token은 어디에 있는가
- 외부 IdP token을 누가 교환하고 보관하는가
- downstream API 호출은 누가 대신하는가

BFF 구조의 핵심은 "브라우저에 가능한 한 적은 credential만 노출하고, 서버가 세션과 token translation을 맡는다"는 점이다.

즉 브라우저가 보는 것은 보통:

- opaque session cookie
- anti-CSRF token
- 최소한의 UI 상태

반대로 서버가 맡는 것은:

- provider refresh/access token 보관
- audience별 downstream token 발급/교환
- logout 및 revocation 반영
- 민감 claim 정규화

---

## 깊이 들어가기

### 1. browser-visible token과 server-side token은 분리해서 생각해야 한다

브라우저에 토큰을 직접 두면 장점도 있다.

- 구조가 단순하다
- 브라우저가 API를 직접 호출한다
- 서버는 stateless해지기 쉽다

하지만 비용도 크다.

- XSS 시 token dump 가능성
- refresh token을 브라우저에 둘지 말지 계속 고민해야 함
- provider token scope가 브라우저까지 새어 나감
- logout와 revoke가 느슨해짐

BFF는 이 문제를 줄이기 위해 브라우저에는 session reference만 주고, 실제 provider token은 서버에 둔다.

### 2. session translation이란 "브라우저 세션을 downstream token 호출로 번역하는 것"이다

사용자 요청 흐름을 이렇게 본다.

1. 브라우저는 BFF session cookie를 보낸다
2. BFF는 session id로 서버 측 token set을 찾는다
3. 필요하면 refresh 또는 token exchange를 수행한다
4. downstream API에는 audience가 좁은 token만 보낸다

핵심은 브라우저 session과 downstream API token이 1:1 동일물이 아니라는 점이다.

이 번역 계층이 있어야:

- provider token scope를 좁힐 수 있다
- 서비스별 audience token으로 분리할 수 있다
- browser-visible credential을 줄일 수 있다

### 3. BFF가 있다면 refresh token은 서버 소유 자산으로 보는 편이 안전하다

실무에서 가장 큰 경계는 refresh token이다.

좋은 기본값:

- browser: refresh token 비노출
- BFF: refresh token 서버측 저장
- session cookie: token reference 또는 session id만 표현

주의점:

- session store 탈취 시 provider token도 함께 위험해질 수 있다
- cookie 세션이 생기므로 CSRF 방어가 필수다
- session store encryption, rotation, scoped access control이 필요하다

브라우저에서 credential을 치우는 순간 외부 IdP와 token exchange를 수행하는 주체는 BFF 자신이다. 즉 BFF가 confidential client가 되며, 그다음 질문은 token endpoint에서 `client_secret_basic` 대신 `private_key_jwt`나 mTLS를 쓸지다. 이 선택지는 [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)로 이어진다.

### 4. cookie만 옮겼다고 경계가 자동으로 좋아지지는 않는다

"브라우저에 JWT 안 두고 cookie로 바꿨다"는 말은 절반만 맞다.

좋아지는 점:

- token dump surface 감소
- provider token을 JS에서 직접 읽기 어려움

새로 생기는 책임:

- CSRF 방어
- session fixation 방어
- BFF와 downstream 간 auth context 전달
- logout propagation

즉 BFF는 위험을 없애는 게 아니라 위험 모양을 바꾼다.

같이 볼 문서:

- authorization request가 front-channel을 지날 때 request tampering을 더 줄이고 싶다면 [OAuth PAR / JAR Basics](./oauth-par-jar-basics.md)
- browser token을 숨긴 뒤 server-side client proof를 어떻게 둘지 정해야 하면 [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)
- 브라우저가 없는 CLI, TV, 콘솔에서 cross-device 승인을 설계해야 한다면 [OAuth Device Code Flow / Security Model](./oauth-device-code-flow-security.md)

### 5. downstream audience는 브라우저 세션과 분리해 좁혀야 한다

나쁜 패턴:

- BFF가 브라우저 세션에 묶인 하나의 광범위 access token을 모든 downstream API에 재사용

더 나은 패턴:

- downstream 서비스별 audience token 발급
- 필요한 scope만 token exchange
- user context와 service context를 분리

이렇게 해야 특정 서비스 호출 token이 다른 서비스로 재사용되는 사고를 줄일 수 있다.

### 6. provider claim과 local session state를 그대로 일치시킨다고 생각하면 위험하다

IdP claim은 로그인 사실과 일부 profile 정보에 가깝다.
우리 앱의 로컬 권한, tenant membership, feature entitlement와는 다를 수 있다.

BFF는 보통 여기서 normalization 계층을 둔다.

- provider subject 매핑
- local user/tenant lookup
- internal session state 생성
- downstream용 최소 auth context 생성

즉 BFF는 단순 proxy가 아니라 trust translation layer다.
`id token`과 `UserInfo`를 어디까지 신원 증거로 보고, 어디서부터 내부 role/tenant를 붙일지는 [OIDC, ID Token, UserInfo](./oidc-id-token-userinfo-boundaries.md)에서 별도로 정리한다.

### 7. logout는 브라우저 탭 하나를 지우는 것으로 끝나지 않는다

BFF 구조에서 logout를 설계할 때는 최소 네 가지를 본다.

- browser session cookie 삭제
- 서버 측 token cache/session store 무효화
- provider refresh token revoke 여부
- federated logout 여부

브라우저에서 cookie만 지웠다고 서버 token cache가 남아 있으면 보안상 반쯤만 로그아웃한 것이다.

### 8. observability 없이 session translation은 디버깅이 불가능하다

최소한 아래 매핑은 보이는 편이 좋다.

- browser session id
- local user id
- provider subject / issuer
- refresh family id
- downstream audience token issuance count

이 정보가 없으면 "왜 특정 탭에서만 다시 로그인되나", "왜 어떤 API만 401이 나나"를 못 푼다.

---

## 실전 시나리오

### 시나리오 1: SPA가 외부 access token을 그대로 들고 내부 API를 직접 호출한다

문제:

- 브라우저 노출 면적이 커진다
- provider scope가 내부 서비스까지 새어 들어온다

대응:

- browser-visible credential을 opaque session으로 줄인다
- BFF에서 provider token을 서버 측으로 이동한다
- 내부 API는 audience가 좁은 downstream token만 받는다

### 시나리오 2: BFF를 도입했는데 CSRF가 다시 생겼다

문제:

- 브라우저가 cookie 세션을 자동 전송한다

대응:

- anti-CSRF token, SameSite, Origin 검증을 함께 둔다
- 상태 변경 endpoint와 읽기 endpoint를 분리한다
- "BFF가 있으니 CSRF 없다"는 가정을 버린다

### 시나리오 3: 로그아웃했는데 어떤 탭은 계속 살아 있고 일부 API는 계속 호출된다

문제:

- cookie 삭제와 서버 token cache 무효화가 분리돼 있다
- downstream token issuance cache가 남아 있다

대응:

- browser session, server token cache, refresh family를 같이 끊는다
- logout path를 session mapping 기준으로 테스트한다

---

## 코드로 보기

### 1. BFF session translation 개념

```java
public DownstreamToken resolveToken(SessionCookie sessionCookie, String audience) {
    BrowserSession session = sessionStore.find(sessionCookie.value());
    TokenSet tokenSet = providerTokenStore.findBySessionId(session.id());

    if (tokenSet.isExpiringSoon()) {
        tokenSet = oauthClient.refresh(tokenSet.refreshToken());
        providerTokenStore.save(session.id(), tokenSet);
    }

    return tokenExchangeService.exchangeForAudience(tokenSet.accessToken(), audience);
}
```

핵심은 브라우저가 직접 provider token을 소유하지 않는다는 점이다.

### 2. browser-visible 상태 예시

```text
session_cookie = opaque session reference
csrf_token = browser-readable anti-CSRF value
no provider refresh token in browser
```

### 3. 설계 체크리스트

```text
1. 브라우저가 직접 보관하는 credential과 서버가 보관하는 token을 분리했는가
2. refresh token은 서버 소유 자산으로 보호되는가
3. downstream audience별 token issuance를 분리하는가
4. logout 시 browser session과 server-side token cache가 함께 무효화되는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| browser-held access token | 구조가 단순하다 | XSS와 scope leakage 위험이 크다 | 아주 단순한 public API |
| browser-held access + refresh token | 재인증 UX가 좋다 | 장기 credential이 브라우저에 노출된다 | 가능하면 피한다 |
| BFF session + server-side tokens | browser 노출 면적이 줄고 translation이 가능하다 | session store, CSRF, logout 설계가 복잡하다 | 대부분의 웹앱, enterprise SSO |
| BFF + audience별 token exchange | 가장 안전한 분리가 가능하다 | token exchange 운영과 observability가 필요하다 | multi-API, 민감 데이터, 세밀한 권한 분리 |

판단 기준은 이렇다.

- 브라우저에 provider token이 보여도 되는가
- downstream API audience를 분리할 필요가 있는가
- CSRF와 session store 운영을 감당할 수 있는가
- logout coherence 요구가 강한가

---

## 꼬리질문

> Q: BFF의 핵심 가치는 무엇인가요?
> 의도: 단순 API aggregation이 아니라 auth boundary를 이해하는지 확인
> 핵심: 브라우저에는 session reference만 두고, 서버가 provider/downstream token을 번역해 관리하는 것이다.

> Q: BFF를 쓰면 refresh token을 브라우저에 둬도 되나요?
> 의도: boundary ownership을 구분하는지 확인
> 핵심: 보통은 서버에 두는 편이 안전하다. 브라우저에는 session cookie만 두는 구조가 일반적이다.

> Q: BFF가 있으면 CSRF가 사라지나요?
> 의도: 위험 모양이 바뀌는 점을 이해하는지 확인
> 핵심: 아니다. cookie 기반 세션이면 CSRF 방어가 다시 중요하다.

> Q: BFF로 옮겼으면 token endpoint client auth는 자동 해결되나요?
> 의도: browser storage 문제와 confidential client auth를 분리하는지 확인
> 핵심: 아니다. 브라우저 밖으로 token을 숨기는 것과 BFF가 `private_key_jwt`/mTLS 같은 방식으로 자신을 증명하는 것은 별도 설계이며, 다음 문서는 [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)다.

> Q: browser session과 downstream token을 왜 분리하나요?
> 의도: token translation의 필요를 아는지 확인
> 핵심: audience 축소, scope 최소화, browser-visible credential 축소를 위해서다.

## 한 줄 정리

BFF 인증 설계의 핵심은 브라우저가 세션 reference만 들고, 실제 provider/downstream token은 서버가 audience별로 번역하고 보호하는 token boundary를 만드는 것이다.
