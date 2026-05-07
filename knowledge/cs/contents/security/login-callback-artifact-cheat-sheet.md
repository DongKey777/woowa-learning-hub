---
schema_version: 3
title: Login Callback Artifact Cheat Sheet
concept_id: security/login-callback-artifact-cheat-sheet
canonical: false
category: security
difficulty: beginner
doc_role: deep_dive
level: beginner
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- login callback artifact cheat sheet
- callback artifact glossary
- state nonce login_state oauth_txn difference
- social login callback artifacts beginner
aliases:
- login callback artifact cheat sheet
- callback artifact glossary
- state nonce login_state oauth_txn difference
- social login callback artifacts beginner
- callback success but app anonymous artifact split
- callback cookie vs handoff code vs session cookie
- shared session cookie vs one-time handoff code
- login callback terms beginner
- callback capture chooser link
- callback to local session bridge
- state mismatch which cookie beginner
- oidc nonce vs oauth state beginner
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/oauth2-oidc-social-login-primer.md
- contents/security/social-login-to-local-session-bridge.md
- contents/security/subdomain-callback-handoff-chooser.md
- contents/security/samesite-login-callback-primer.md
- contents/security/oidc-id-token-userinfo-boundaries.md
- contents/network/http-https-basics.md
- contents/security/callback-cookie-name-splitter.md
- contents/security/oauth2-authorization-code-grant.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Login Callback Artifact Cheat Sheet 핵심 개념을 설명해줘
- login callback artifact cheat sheet가 왜 필요한지 알려줘
- Login Callback Artifact Cheat Sheet 실무 설계 포인트는 뭐야?
- login callback artifact cheat sheet에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Login Callback Artifact Cheat Sheet를 다루는 deep_dive 문서다. social login callback에서 자주 보이는 `state`, `nonce`, `login_state`, `oauth_txn`, shared session cookie, one-time handoff code는 전부 "로그인 관련 값"처럼 보여도 쓰는 시점과 책임이 다르다. 먼저 어느 artifact가 어느 hop에서 다시 필요한지 갈라야 `state mismatch`, callback 성공 후 anonymous, 중복 cookie 혼동을 덜 섞는다. 검색 질의가 login callback artifact cheat sheet, callback artifact glossary, state nonce login_state oauth_txn difference, social login callback artifacts beginner처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Login Callback Artifact Cheat Sheet

> 한 줄 요약: social login callback에서 자주 보이는 `state`, `nonce`, `login_state`, `oauth_txn`, shared session cookie, one-time handoff code는 전부 "로그인 관련 값"처럼 보여도 쓰는 시점과 책임이 다르다. 먼저 어느 artifact가 어느 hop에서 다시 필요한지 갈라야 `state mismatch`, callback 성공 후 anonymous, 중복 cookie 혼동을 덜 섞는다.

**난이도: 🟢 Beginner**

관련 문서:

- [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)
- [Social Login To Local Session Bridge](./social-login-to-local-session-bridge.md)
- [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)
- [SameSite Login Callback Primer](./samesite-login-callback-primer.md)
- [OIDC, ID Token, UserInfo](./oidc-id-token-userinfo-boundaries.md)
- [HTTP와 HTTPS 기초](../network/http-https-basics.md)
- [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)

retrieval-anchor-keywords: login callback artifact cheat sheet, callback artifact glossary, state nonce login_state oauth_txn difference, social login callback artifacts beginner, callback success but app anonymous artifact split, callback cookie vs handoff code vs session cookie, shared session cookie vs one-time handoff code, login callback terms beginner, callback capture chooser link, callback to local session bridge, state mismatch which cookie beginner, oidc nonce vs oauth state beginner, login callback artifact cheat sheet basics, login callback artifact cheat sheet beginner, login callback artifact cheat sheet intro

## 먼저 잡는 mental model

브라우저 social login을 아주 짧게 그리면 보통 이렇다.

```text
app -> auth start -> external IdP -> auth callback -> app login complete
```

초보자가 헷갈리는 이유는 이 모든 구간에서 "짧게 사는 값"이 여러 개 나오기 때문이다.

- 어떤 값은 **요청을 시작한 브라우저가 맞는지** 확인한다.
- 어떤 값은 **외부 IdP가 돌려준 로그인 응답이 원래 요청과 같은 묶음인지** 확인한다.
- 어떤 값은 **callback 뒤 app 쪽 로그인 완료**에만 한 번 쓰인다.
- 어떤 값은 **그 이후 모든 요청**에서 계속 로그인 상태를 유지한다.

핵심은 이것이다.

- `state`, `nonce`는 **검증용 값**
- `login_state`, `oauth_txn`은 보통 그 검증용 값을 **브라우저에 잠깐 붙잡아 두는 cookie/transaction row 이름**
- shared session cookie는 **로그인 완료 후 반복 사용**
- one-time handoff code는 **subdomain/app 전환 한 번용**

즉 이름만 보고 "다 같은 세션 값"처럼 읽으면 거의 반드시 한 번은 섞인다.

---

## 20초 glossary 표

| artifact | 가장 짧은 뜻 | 보통 누가 다시 읽나 | 언제 다시 필요하나 | 깨지면 보이는 장면 |
|---|---|---|---|---|
| `state` | "내가 시작한 로그인 요청 맞나"를 묶는 상관관계 값 | callback 처리 서버 | external IdP에서 돌아온 callback 순간 | `state mismatch`, callback 400, login loop |
| `nonce` | "이 ID token이 이번 로그인용으로 발급된 것 맞나"를 묶는 값 | OIDC ID token 검증 서버 | token / ID token 검증 순간 | `nonce` 검증 실패, 토큰 재사용 의심 |
| `login_state` | `state`나 login flow id를 브라우저에 잠깐 저장하는 cookie 이름 예시 | callback endpoint | callback 한 번 | callback에서 cookie가 안 보여 `state`를 비교 못 함 |
| `oauth_txn` | provider, redirect, PKCE, `state` 같은 transaction 묶음을 담는 cookie/서버 row 이름 예시 | callback endpoint 또는 auth server | callback 한 번 | callback은 왔는데 원래 flow 메타데이터를 못 찾음 |
| shared session cookie | `auth`와 `app`이 같이 보거나 parent domain으로 공유하는 로그인 유지용 cookie | 이후의 app/auth 요청들 | callback 이후 반복 | callback 성공 뒤 app 첫 요청 anonymous |
| one-time handoff code | `auth` 성공을 `app` local session으로 바꾸는 일회용 교환권 | app login-complete endpoint | subdomain/app 전환 직후 한 번 | callback 성공, redirect도 됐는데 app session 미생성 |

이 표에서 기억할 한 줄:

- callback에서 한 번 쓰는 artifact와, callback 이후 계속 쓰는 artifact를 분리하면 절반은 정리된다.

---

## 어디서 다시 필요한지 timeline으로 본다

| 단계 | 대표 artifact | 왜 필요한가 | 여기서의 대표 질문 |
|---|---|---|---|
| 로그인 시작 | `state`, `nonce`, PKCE verifier를 서버/브라우저에 저장 | 시작 요청과 callback 응답을 나중에 연결하려고 | "내가 시작한 login flow 맞나?" |
| external IdP -> callback | `login_state`, `oauth_txn` 같은 callback용 cookie 또는 server txn row | 돌아온 `code`, `state`, `id_token`을 원래 흐름과 비교하려고 | "왜 callback에서 `state mismatch`가 나지?" |
| callback -> app 전환 | shared session cookie 또는 one-time handoff code | `auth` 쪽 성공을 `app` 로그인으로 넘기려고 | "callback은 성공인데 왜 app 첫 요청이 anonymous지?" |
| callback 이후 일반 요청 | `app_session`, shared session cookie | 이후 API/page에서 로그인 유지하려고 | "왜 첫 화면 이후에도 계속 `/login`으로 돌아가지?" |

즉 login callback artifact 질문은 보통 아래 둘 중 하나다.

1. callback 검증 artifact가 사라졌나
2. callback 뒤 app 로그인 artifact가 사라졌나

이 둘을 섞으면 `SameSite`, `Domain`, session lookup, handoff 실패가 한 문장 안에 뭉개진다.

---

## `state`와 `nonce`는 어떻게 다른가

둘 다 랜덤 값처럼 보여도 보는 대상이 다르다.

| 항목 | `state` | `nonce` |
|---|---|---|
| 주로 어디서 쓰나 | OAuth2 authorization request / callback | OIDC `id_token` 검증 |
| 막고 싶은 것 | login CSRF, 요청 연동 깨짐 | 다른 로그인에서 발급된 ID token 재주입, replay 혼동 |
| 보통 어디와 비교하나 | callback query의 `state` vs 저장해 둔 값 | ID token claim의 `nonce` vs 저장해 둔 값 |
| 없어도 되는가 | code flow에서는 보통 필수처럼 본다 | OIDC login에서는 매우 중요하다 |
| 초보자 오해 | "`state`만 맞으면 로그인 검증은 끝났다" | "`nonce`는 모바일/앱에서만 필요하다" |

짧게 말하면:

- `state`는 **callback 요청이 내가 시작한 흐름인지**
- `nonce`는 **받은 ID token이 이번 로그인용인지**

를 본다.

그래서 OIDC social login에서는 둘 다 함께 나오는 일이 흔하다.

---

## `login_state`와 `oauth_txn`은 표준 이름이 아니다

이 둘은 RFC 용어라기보다 구현체에서 자주 보이는 **저장소 이름**에 가깝다.

| 이름 | 보통 담는 것 | beginner가 오해하는 점 |
|---|---|---|
| `login_state` | `state`, flow id, redirect after login 같은 최소 상관관계 정보 | "`state` 그 자체와 같은 말"이라고 생각함 |
| `oauth_txn` | provider id, `state`, PKCE verifier, redirect, nonce 등 transaction 묶음 | "oauth_txn cookie만 있으면 app 로그인도 끝난다"라고 생각함 |

중요한 점:

- `state`는 **값**
- `login_state`나 `oauth_txn`은 그 값을 **어딘가에 보관하는 구현 이름**

즉 `state mismatch`가 났다고 해서 query param의 `state`만 보면 안 되고,
실제로 callback endpoint가 읽는 `login_state`/`oauth_txn` cookie 또는 server-side txn row가 살아 있는지도 봐야 한다.

---

## shared session cookie와 one-time handoff code는 무엇이 다른가

`auth.example.com/callback` 뒤 `app.example.com`으로 넘어갈 때 초보자가 가장 많이 섞는 두 artifact다.

| 질문 | shared session cookie | one-time handoff code |
|---|---|---|
| 무엇을 넘기나 | 이미 로그인된 session 자체 또는 공용 session id | "이 사용자를 app 세션으로 바꿔도 된다"는 일회용 증거 |
| 브라우저에 얼마나 남나 | 보통 이후 요청마다 계속 남는다 | 보통 한 번 교환 후 끝난다 |
| `app` 첫 요청에서 기대하는 것 | `Cookie: session=...` 같은 shared cookie | `/login/complete?handoff=...` 또는 POST redemption |
| 실패 장면 | app 첫 요청에 cookie가 없거나 서버가 session을 못 찾음 | redirect는 됐는데 `app_session`이 안 생김 |
| 초보자 오해 | "`Domain`만 넓히면 항상 정답" | "`auth_session`이 app에 안 오니 무조건 실패" |

핵심은 이것이다.

- shared cookie 모델은 **cookie가 app까지 직접 가야 한다**
- handoff 모델은 **auth cookie가 app에 안 가도 정상일 수 있다**

이 분기가 더 필요하면 [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)로 이어 가면 된다. 그 문서는 callback capture 3줄, 즉 `Set-Cookie`, `Location`, 첫 `app` 요청 trace만으로 shared cookie branch와 handoff branch를 고르는 초급용 bridge다.

---

## 아주 짧은 예시 3개

### 1. `state mismatch`

```text
accounts.google.com -> auth.example.com/callback?code=...&state=abc
```

이때 서버는 보통 아래 중 하나를 다시 읽는다.

- `login_state=abc` cookie
- `oauth_txn` 안에 저장된 `state=abc`
- 서버 저장소의 login transaction row

즉 여기서의 핵심 질문은:

- callback request에 비교 대상이 남아 있나

이지, 아직 `app_session`이 있나가 아니다.

### 2. callback은 성공했는데 app 첫 요청 anonymous

```text
auth.example.com/callback -> 302 -> app.example.com/home
```

여기서 먼저 갈리는 질문:

- shared session cookie가 app까지 가야 하는 구조인가
- 아니면 handoff code를 app이 한 번 소모해 자기 session을 만들어야 하는 구조인가

즉 여기서는 `state`보다 **shared cookie vs handoff**가 핵심이다.

### 3. ID token 검증에서 `nonce` 실패

callback query의 `state`는 맞아도, ID token 안 `nonce`가 저장해 둔 값과 다를 수 있다.

이 장면은 보통:

- callback 요청 자체는 돌아왔지만
- OIDC 로그인 응답의 신원 검증까지는 통과하지 못했다

는 뜻에 가깝다.

즉 `state`와 `nonce`는 통과/실패 지점이 다를 수 있다.

---

## 증상별로 가장 먼저 떠올릴 artifact

| 지금 보이는 증상 | 먼저 떠올릴 artifact | 다음 문서 |
|---|---|---|
| `state mismatch`, callback 400, login loop | `state`, `login_state`, `oauth_txn` | [SameSite Login Callback Primer](./samesite-login-callback-primer.md) |
| ID token 검증에서만 실패, `nonce` mismatch | `nonce`, OIDC token validation | [OIDC, ID Token, UserInfo](./oidc-id-token-userinfo-boundaries.md) |
| callback은 성공했는데 local session이 언제 생겨야 하는지 헷갈린다 | callback completion vs app session issuance | [Social Login To Local Session Bridge](./social-login-to-local-session-bridge.md) |
| callback은 성공인데 `app` 첫 요청 anonymous | shared session cookie vs one-time handoff code | [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md) |
| callback용 cookie와 session cookie 이름이 비슷해 혼동됨 | callback artifact role split | [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md) |
| `code`, `state`, PKCE 전체 흐름을 깊게 보고 싶다 | OAuth2 code flow 전체 | [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md) |

---

## common confusion

- "`state`와 `login_state`는 같은 말이죠?"
  - 아니다. `state`는 비교할 값이고, `login_state`는 그 값을 담는 cookie/flow 저장소 이름일 수 있다.
- "`oauth_txn` cookie가 있으니 app도 로그인됐겠죠?"
  - 아니다. 그 cookie는 callback transaction을 복원하는 용도일 수 있다.
- "`nonce`도 결국 `state`랑 같은 CSRF 토큰 아닌가요?"
  - 아니다. `nonce`는 주로 ID token이 이번 로그인용인지 보는 OIDC 쪽 검증값이다.
- "callback 성공이면 session도 자동으로 생기죠?"
  - 아니다. callback 검증 성공과 app local session 생성은 별도 단계일 수 있다.
- "`auth_session`이 app에 안 오면 브라우저가 cookie를 잃어버린 거죠?"
  - handoff 모델이라면 정상일 수 있다. app에 필요한 것은 새 `app_session`일 수 있다.

---

## 한 줄 정리

social login callback에서 `state`와 `nonce`는 검증용 값이고, `login_state`와 `oauth_txn`은 그 검증용 값을 붙잡아 두는 transaction artifact 이름이며, shared session cookie와 one-time handoff code는 callback 이후 app 로그인 완료를 넘기는 방식이다.
