---
schema_version: 3
title: Social Login To Local Session Bridge
concept_id: security/social-login-to-local-session-bridge
canonical: false
category: security
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 85
mission_ids:
- missions/roomescape
review_feedback_tags:
- idp-vs-local-session-boundary
- callback-to-session-translation
- first-request-anonymous-trace
aliases:
- social login local session bridge
- social login local session basics
- external idp to local session
- oauth callback to app session
- oidc callback local cookie issuance
- callback success but app anonymous
- callback local session 뭐예요
- callback 성공인데 app anonymous 왜
- social login callback cookie issuance
- bff login handoff boundary
- auth callback app local session
- idp login to session cookie
- backend for frontend auth bridge
- social login first request anonymous
- app session creation after callback
symptoms:
- 소셜 로그인은 성공했는데 우리 서비스에서는 아직 비로그인처럼 보여요
- callback이 끝났는데 첫 화면 요청이 anonymous로 잡혀요
- id token은 받았는데 local session이 어디서 생기는지 모르겠어요
intents:
- comparison
prerequisites:
- security/oauth2-oidc-social-login-primer
- security/session-cookie-jwt-basics
next_docs:
- security/subdomain-callback-handoff-chooser
- security/browser-bff-token-boundary-session-translation
- security/subdomain-login-callback-boundaries
linked_paths:
- contents/security/oauth2-oidc-social-login-primer.md
- contents/security/oauth2-authorization-code-grant.md
- contents/security/login-callback-artifact-cheat-sheet.md
- contents/security/session-cookie-jwt-basics.md
- contents/security/subdomain-callback-handoff-chooser.md
- contents/security/browser-bff-token-boundary-session-translation.md
- contents/security/csrf-in-spa-bff-architecture.md
- contents/system-design/browser-bff-session-boundary-primer.md
- contents/network/cookie-session-jwt-browser-flow-primer.md
confusable_with:
- security/oauth2-authorization-code-grant
- security/subdomain-callback-handoff-chooser
- security/subdomain-login-callback-boundaries
- security/browser-bff-token-boundary-session-translation
forbidden_neighbors:
- contents/security/session-cookie-jwt-basics.md
expected_queries:
- 소셜 로그인 callback까지 성공했는데 서비스에서는 왜 익명 사용자야?
- 구글 로그인 성공 후 우리 앱 세션은 어디서 만들어져?
- oauth 로그인 뒤 첫 요청이 anonymous로 보이는 이유가 뭐야
- idp 인증과 로컬 세션 생성 차이를 처음부터 설명해줘
- bff가 social login 결과를 app session으로 바꾸는 흐름이 궁금해
- callback 다음에 local user lookup이 왜 필요한가요
- 외부 로그인은 됐는데 app cookie가 안 생길 때 어디를 봐야 해?
contextual_chunk_prefix: |
  이 문서는 external IdP 로그인 성공과 우리 서비스 로그인 완료를 같은 일로 느끼는 학습자에게, callback 이후 local user lookup과 app-local session 발급 사이 경계를 연결해 주는 bridge다. 구글 로그인은 됐는데 왜 첫 화면이 익명인가, callback 다음에 어느 단계에서 내부 계정을 찾나, handoff 뒤 누가 session cookie를 만들나, principal 복원 실패를 어디서 끊어 보나 같은 자연어 paraphrase가 본 문서의 흐름 연결에 매핑된다.
---
# Social Login To Local Session Bridge

> 한 줄 요약: external IdP 로그인 성공은 끝이 아니라 시작이다. callback에서 외부 신원을 확인한 뒤, 우리 앱이 local user를 찾고 session cookie를 발급하거나 BFF가 app-local session으로 한 번 더 번역해야 브라우저의 "로그인됨" 상태가 완성된다.

**난이도: 🟢 Beginner**

관련 문서:

- [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)
- [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
- [Login Callback Artifact Cheat Sheet](./login-callback-artifact-cheat-sheet.md)
- [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
- [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)
- [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
- [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
- [Browser BFF Session Boundary Primer](../system-design/browser-bff-session-boundary-primer.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md)

retrieval-anchor-keywords: social login local session bridge, social login local session basics, external idp to local session, oauth callback to app session, oidc callback local cookie issuance, callback success but app anonymous, callback local session 뭐예요, callback 성공인데 app anonymous 왜, social login callback cookie issuance, bff login handoff boundary, auth callback app local session, idp login to session cookie, backend for frontend auth bridge, social login first request anonymous, app session creation after callback

## 핵심 개념

초보자는 "구글 로그인 성공"과 "우리 서비스 로그인 완료"를 같은 이벤트로 느끼기 쉽다.

하지만 실제로는 두 단계다.

1. external IdP가 "이 사람은 누구다"를 확인한다.
2. 우리 서비스가 그 사람을 자기 local session 상태로 바꾼다.

그래서 callback이 `200`이나 `302`로 끝나도, 그 뒤 local session cookie가 안 생기거나 app이 그 cookie를 못 읽으면 브라우저 입장에서는 아직 로그인 완료가 아니다.

## 한눈에 보기

| 단계 | 누가 책임지나 | 대표 artifact | 여기서 끝나면 안 되는 이유 |
|---|---|---|---|
| login start | browser + auth server | `state`, PKCE verifier, login txn cookie | 아직 외부 IdP로 보내기 전 준비 단계다 |
| external IdP 인증 | Google/Kakao/Naver 같은 IdP | auth code, OIDC login result | 우리 앱의 local role/session은 아직 없다 |
| callback 처리 | auth server 또는 BFF | `code` 교환, `id token` 검증, external identity 확인 | 여기까지는 "외부 로그인 성공"일 뿐이다 |
| local account 매핑 | 우리 앱 backend | local user id, tenant lookup, signup/link decision | 내부 계정이 없으면 app session을 못 만든다 |
| local session 발급 | app backend 또는 BFF | session cookie, app-local session, server-side token mapping | 브라우저가 이후 요청에서 로그인 상태를 유지하려면 꼭 필요하다 |

## 흐름을 5칸으로 나눠 보기

```text
browser
  -> external idp login
  -> /callback
  -> local user lookup/link
  -> set-cookie or handoff
  -> first app request with local session
```

핵심은 `/callback`이 마지막 칸이 아니라는 점이다.

### 1. external IdP는 "누구인가"까지만 알려 준다

IdP는 보통 아래 정도를 알려 준다.

- issuer
- subject(`sub`)
- email/profile claim

하지만 이 정보만으로 우리 서비스의 권한이 자동 결정되지는 않는다.
우리 앱은 이 external identity를 local user, 조직, 권한 모델에 연결해야 한다.

### 2. callback은 외부 결과를 우리 앱 입력으로 바꾸는 지점이다

callback handler는 보통 이런 일을 한다.

- `state`와 transaction cookie를 대조한다
- authorization code를 token으로 교환한다
- 필요하면 `id token`과 `UserInfo`를 확인한다
- external identity를 local user 후보로 매핑한다

즉 callback은 "로그인 끝"이라기보다 "이제 우리 앱 세션을 만들 준비가 됨"에 가깝다.

### 3. local user 매핑이 빠지면 session도 못 만든다

같은 Google 계정이라도 우리 앱에서는 아래가 추가로 필요할 수 있다.

- 이미 가입된 회원인지
- 어떤 tenant 소속인지
- 처음 로그인이라 회원 연결 또는 가입 승인이 필요한지

그래서 callback 성공 뒤에도:

- 회원 연결 화면으로 간다
- onboarding step이 뜬다
- 첫 요청이 anonymous처럼 보인다

같은 현상이 나올 수 있다. 이때는 cookie 문제만 볼 게 아니라 local account linking 단계도 같이 봐야 한다.

## cookie issuance와 handoff를 분리해서 본다

local session을 만드는 방식은 크게 둘이다.

| 패턴 | callback 직후 브라우저가 받는 것 | 첫 app 요청에서 기대하는 것 | 초보자 오해 |
|---|---|---|---|
| callback 서버가 바로 local session cookie 발급 | `Set-Cookie: app_session=...` | 이후 요청에 `app_session` 자동 전송 | "callback 302만 보면 끝났다" |
| auth/BFF가 handoff만 넘기고 app이 local session 생성 | `Location: /login/complete?handoff=...` 같은 일회용 artifact | handoff redemption 뒤 새 `app_session` 생성 | "auth cookie가 app에 안 오니 무조건 실패다" |

짧게 말하면:

- cookie issuance 모델은 callback 응답에서 최종 cookie가 바로 보일 수 있다
- handoff 모델은 callback 성공 뒤 한 번 더 app-local session 생성 단계가 있다

## BFF가 끼면 경계가 어떻게 바뀌나

BFF 구조에서는 외부 IdP token과 browser-visible session을 같은 것으로 보지 않는 편이 안전하다.

| 질문 | BFF가 주로 맡는 것 | browser가 보통 직접 안 보는 것 |
|---|---|---|
| external IdP와 누가 통신하나 | BFF/auth server | provider refresh/access token |
| 브라우저가 무엇으로 로그인 상태를 유지하나 | local session cookie | external provider token 원본 |
| downstream API 호출은 누가 대신하나 | BFF | audience별 server-side token mapping |

즉 BFF가 있다는 말은 보통 아래 뜻이다.

- callback에서 받은 외부 token을 서버가 보관하거나 참조한다
- 브라우저에는 local session cookie만 보여 준다
- 첫 app 요청은 "provider token이 있나"가 아니라 "local session이 복원되나"를 본다

그래서 social login 장애를 볼 때도:

- external login은 성공했는가
- local session cookie가 발급됐는가
- BFF/app이 그 session으로 principal을 복원했는가

를 따로 확인해야 한다.

## 흔한 오해와 함정

### "ID token을 받았으니 로그인은 끝난 것 아닌가요?"

아니다. `id token`은 external identity 증거다.
우리 앱이 local session, role, tenant context를 만들기 전에는 브라우저의 app 로그인 상태가 완성되지 않는다.

### "callback이 302로 끝났으니 쿠키도 당연히 생겼겠죠?"

아니다. `302`는 이동 지시일 뿐이다.
실제로는:

- 최종 session cookie가 callback response에 있었는지
- handoff redemption 뒤 app response에서 cookie가 생겼는지

를 따로 봐야 한다.

### "BFF면 브라우저가 token을 안 보니 디버깅할 게 줄어든다"

줄어드는 것도 있지만, 대신 확인점이 바뀐다.

- session cookie는 생겼는가
- BFF session store 매핑은 살아 있는가
- app 첫 요청에서 principal restore가 되는가

즉 token이 안 보인다고 상태가 단순해지는 것은 아니다.

## 실무에서 쓰는 모습

### 예시 1. callback에서 바로 app session cookie를 만드는 경우

1. 사용자가 Google 로그인 성공
2. `/callback`이 code 교환과 local user lookup 수행
3. 서버가 `Set-Cookie: app_session=...` 발급
4. 브라우저가 다음 `/me` 요청에 그 cookie를 자동 전송

이 경우 첫 app 요청이 anonymous라면 cookie issuance, `Domain`/`Path`, session lookup부터 본다.

### 예시 2. auth subdomain이 handoff만 넘기고 app이 local session을 만드는 경우

1. `auth.example.com/callback`이 external login 결과를 확인
2. `app.example.com/login/complete?handoff=...`로 이동
3. app backend가 handoff를 한 번 소모
4. app이 자기 `app_session` cookie를 발급

이 경우 `auth` cookie가 app에 안 가도 정상일 수 있다.
중요한 것은 마지막에 app-local session이 실제로 생겼는지다.

## 어디서 막혔는지 빠르게 고르는 법

| 지금 보이는 증상 | 먼저 보는 경계 | 다음 문서 |
|---|---|---|
| `state mismatch`, callback 400 | callback transaction 검증 | [Login Callback Artifact Cheat Sheet](./login-callback-artifact-cheat-sheet.md) |
| callback은 성공인데 첫 app 요청이 anonymous | cookie issuance vs handoff | [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md) |
| `auth.example.com`과 `app.example.com` 사이에서만 풀린다 | shared cookie scope vs app-local session | [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) |
| BFF가 provider token을 들고 있어 흐름이 헷갈린다 | browser-visible session vs server-side token mapping | [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) |
| callback 뒤 첫 POST가 `403`이다 | login completion 이후 CSRF 경계 | [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md) |

## 더 깊이 가려면

- social login 용어부터 다시 정리: [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)
- `code`, `state`, PKCE callback 원리: [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
- browser/session 유지 기본기: [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
- BFF가 왜 token과 local session을 분리하는지: [Browser BFF Session Boundary Primer](../system-design/browser-bff-session-boundary-primer.md)

## 면접/시니어 질문 미리보기

> Q: social login callback 성공과 local session 생성은 왜 분리해서 봐야 하나요?
> 의도: external identity 확인과 app state 생성의 책임 경계를 이해하는지 본다.
> 핵심: IdP는 신원만 보장하고, 우리 앱은 local user mapping과 session issuance를 별도로 수행한다.

> Q: BFF 구조에서 브라우저가 provider access token을 직접 안 들고 있으면 무엇이 좋아지나요?
> 의도: browser-visible credential 축소와 새 책임을 함께 이해하는지 본다.
> 핵심: token 노출 면적은 줄지만 session store, CSRF, principal restore, logout coherence를 더 엄격히 관리해야 한다.

## 한 줄 정리

social login이 local app login으로 끝나려면 "external IdP callback 성공" 다음에 "local user 매핑"과 "session cookie 발급 또는 BFF handoff completion"이 반드시 이어져야 한다.
