---
schema_version: 3
title: SameSite Login Callback Primer
concept_id: security/samesite-login-callback-primer
canonical: true
category: security
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 70
mission_ids: []
review_feedback_tags:
- samesite login callback primer
- same-origin same-site cross-site login primer
- social login same-site vs same-origin
- external idp callback samesite
aliases:
- samesite login callback primer
- same-origin same-site cross-site login primer
- social login same-site vs same-origin
- external idp callback samesite
- iframe login samesite beginner
- auth.example.com app.example.com same-site
- sibling subdomain not cross-site
- samesite 뭐예요
- samesite login callback primer basics
- samesite login callback primer beginner
- samesite login callback primer intro
- security basics
symptoms: []
intents:
- definition
- deep_dive
prerequisites: []
next_docs: []
linked_paths:
- contents/security/oauth2-oidc-social-login-primer.md
- contents/security/social-login-to-local-session-bridge.md
- contents/security/cookie-rejection-reason-primer.md
- contents/security/samesite-none-cross-site-login-primer.md
- contents/security/subdomain-callback-handoff-chooser.md
- contents/security/secure-cookie-behind-proxy-guide.md
- contents/security/fetch-credentials-vs-cookie-scope.md
- contents/security/callback-cookie-name-splitter.md
- contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md
- contents/security/subdomain-login-callback-boundaries.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- SameSite Login Callback Primer 핵심 개념을 설명해줘
- samesite login callback primer가 왜 필요한지 알려줘
- SameSite Login Callback Primer 실무 설계 포인트는 뭐야?
- samesite login callback primer에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 SameSite Login Callback Primer를 다루는 primer 문서다. login callback에서 `SameSite`를 볼 때는 `same-origin`이 아니라 `same-site`를 먼저 봐야 한다. `auth.example.com`과 `app.example.com`은 origin은 달라도 보통 same-site이고, external IdP callback이나 partner iframe은 cross-site일 수 있다. 검색 질의가 samesite login callback primer, same-origin same-site cross-site login primer, social login same-site vs same-origin, external idp callback samesite처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# SameSite Login Callback Primer

> 한 줄 요약: login callback에서 `SameSite`를 볼 때는 `same-origin`이 아니라 `same-site`를 먼저 봐야 한다. `auth.example.com`과 `app.example.com`은 origin은 달라도 보통 same-site이고, external IdP callback이나 partner iframe은 cross-site일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- `[primer]` [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)
- `[primer]` [Social Login To Local Session Bridge](./social-login-to-local-session-bridge.md)
- `[primer]` [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md)
- `[follow-up]` [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)
- `[follow-up]` [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)
- `[follow-up]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
- `[follow-up]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
- `[follow-up]` [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md)
- `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
- `[catalog]` [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)
- `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: samesite login callback primer, same-origin same-site cross-site login primer, social login same-site vs same-origin, external idp callback samesite, iframe login samesite beginner, auth.example.com app.example.com same-site, sibling subdomain not cross-site, samesite 뭐예요, samesite login callback primer basics, samesite login callback primer beginner, samesite login callback primer intro, security basics, beginner security, 처음 배우는데 samesite login callback primer, samesite login callback primer 입문
retrieval-anchor-keywords: callback cookie vs app session cookie, same-site handoff vs cross-site callback, social login local session bridge, browser session troubleshooting return path, callback cookie role split, one-time callback cookie vs main session cookie, 처음 배우는데 samesite callback
retrieval-anchor-keywords: external idp iframe sibling subdomain chooser, callback next step one doc, cross-site vs same-site handoff, beginner callback return to readme, same-site callback mental model

## 이 문서의 자리부터 잡기

초보자는 아래 문장을 거의 같은 뜻으로 읽기 쉽다.

- "`auth.example.com`과 `app.example.com`이 다른데 왜 `SameSite` 문제는 아니라는 거죠?"
- "구글 callback은 cross-site라면서, callback 뒤 `app.example.com` 첫 요청은 왜 또 same-site라고 하나요?"
- "partner iframe 안에서만 로그인 유지가 안 되는데 subdomain 문제와 뭐가 다른가요?"

이 문서는 그 혼란을 풀기 위한 entrypoint다.

- `same-origin`, `same-site`, `cross-site` 용어부터 짧게 맞춘다.
- 한 login flow 안에 **cross-site callback**과 **same-site handoff**가 같이 들어올 수 있다는 점을 분리한다.
- `SameSite`가 맞는 장면과, `Domain`/session handoff/proxy를 먼저 봐야 하는 장면을 갈라 준다.
- callback용 cookie와 main session cookie가 같은 이름으로 보여 역할이 섞이면 [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md)에서 먼저 분리한다.

반대로 질문이 처음부터 아래 쪽이라면 이 문서가 첫 entrypoint는 아니다.

- `fetch`, `credentials: "include"`, `Access-Control-Allow-Credentials`, CORS가 섞인 질문
- XHR/API 응답을 JS가 읽지 못하는 문제

그 경우는 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)로 바로 가는 편이 빠르다.

질문이 "`code`/`state`/`id token`은 알겠는데 callback 뒤 우리 앱 session이 언제 생기나요?"처럼 callback 용어와 app 로그인 완료 기준이 한 문장으로 섞이면 [Social Login To Local Session Bridge](./social-login-to-local-session-bridge.md)로 한 칸 돌아가 local session 생성 단계를 먼저 고정한다.

## 세 장면을 한 번에 고르는 첫 분기

이 문서는 세 장면을 섞지 않게 만드는 entrypoint다.

| 지금 가장 먼저 보이는 장면 | 먼저 붙잡을 질문 | 다음 한 장 |
|---|---|---|
| external IdP callback에서 `state mismatch`, callback loop, callback 400이 난다 | callback용 cookie가 cross-site return에서 다시 필요했나 | [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md) |
| partner iframe 안에서만 로그인 유지가 안 된다 | iframe이 third-party / cross-site 맥락이 되었나 | [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md) |
| `auth.example.com/callback`은 성공인데 `app.example.com` 첫 요청이 anonymous다 | callback 뒤 handoff가 same-site인데 scope/session 연결이 어긋났나 | [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md) |
| login 뒤 redirect가 `http://...`로 꺾인다 | app이 HTTPS를 HTTP로 오해했나 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |

한 갈래만 읽고 막히면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아와 다음 branch를 다시 고른다.

---

## 가장 먼저 구분할 세 단어

`SameSite`는 이름 때문에 `same-origin`과 자주 섞이지만, 브라우저가 보는 질문이 다르다.

| 용어 | 브라우저가 주로 보는 것 | 예시 | 이 문서에서 기억할 한 줄 |
|---|---|---|---|
| same-origin | scheme + host + port가 모두 같은가 | `https://app.example.com` -> `https://app.example.com/api/me` | CORS, SOP, `fetch` 기본 동작에서 더 자주 나온다 |
| same-site | 같은 site 묶음인가 | `https://auth.example.com` -> `https://app.example.com` | origin은 달라도 same-site일 수 있다 |
| cross-site | site가 달라졌는가 | `https://accounts.google.com` -> `https://auth.example.com/callback` | `SameSite` cookie 전송 규칙이 바로 문제된다 |

핵심은 이것이다.

- `same-origin`은 더 좁은 말이다.
- sibling subdomain은 **same-origin은 아니어도 same-site일 수 있다.**
- `SameSite`는 이름 그대로 **site 기준**으로 cookie 전송을 본다.

---

## 어떤 cookie가 어느 hop에서 필요한지 먼저 본다

login flow에서는 cookie가 하나만 있는 것이 아니다.

| cookie / artifact | 주로 어디서 다시 필요하나 | 여기서 빠지면 보이는 장면 |
|---|---|---|
| `login_state`, `oauth_txn` 같은 callback용 cookie | `auth.example.com/callback` | callback에서 `state mismatch`, 400, callback loop |
| shared session cookie | `app.example.com` 첫 요청 | callback은 성공인데 app 첫 요청이 anonymous |
| iframe 안 세션 cookie | partner iframe 안의 `app.example.com` 요청 | 독립 탭에서는 되는데 iframe 안에서만 로그인 유지 실패 |
| one-time handoff code | callback 뒤 `app`의 login completion route | cookie보다 handoff redemption이 먼저 깨짐 |

즉 "cookie가 안 붙는다"는 말만으로는 부족하다.
**어느 cookie가 어느 단계에서 다시 필요했는지**를 먼저 분리해야 한다.

---

## 한 로그인 플로우 안에 cross-site와 same-site가 같이 들어온다

social login 한 번을 timeline으로 보면 이렇다.

| 단계 | 예시 이동 | same-origin? | same-site? | 먼저 볼 것 |
|---|---|---|---|---|
| 1 | `app.example.com` -> `auth.example.com/login` | 아니다 | 보통 그렇다 | `SameSite`보다 `Domain`/host-only/flow 설계 |
| 2 | `accounts.google.com` -> `auth.example.com/callback` | 아니다 | 아니다 | callback용 cookie의 `SameSite` |
| 3 | `auth.example.com` -> `app.example.com/home` | 아니다 | 보통 그렇다 | shared cookie 또는 session handoff |

이 표가 이 문서의 핵심이다.

- **외부 IdP에서 돌아오는 callback 단계는 cross-site일 수 있다.**
- **callback 뒤 sibling subdomain으로 넘어가는 handoff 단계는 same-site일 수 있다.**

그래서 한 login flow 안에서도:

- callback용 cookie는 `SameSite=None; Secure`가 필요할 수 있고
- app session 쪽은 `Domain` 또는 handoff 모델이 더 중요할 수 있다

를 동시에 볼 수 있다.

---

## 장면 1: `auth.example.com`과 `app.example.com`만 보고 있다

이 장면에서 초보자는 "host가 다르니 cross-site 아닌가요?"라고 묻기 쉽다.

보통은 아니다.

- origin은 다르다
- 하지만 site는 같을 수 있다

그래서 아래 같은 장면은 `SameSite=None`보다 다른 질문이 더 먼저다.

```text
auth.example.com/callback  ->  302  ->  app.example.com/home
```

이때 먼저 볼 것은 보통 이것이다.

| 먼저 볼 질문 | 이유 |
|---|---|
| shared cookie에 `Domain=example.com`이 필요한가 | host-only cookie면 `app.example.com`에 안 간다 |
| `Path`가 너무 좁은가 | callback path에서만 보이고 app 첫 화면에서는 빠질 수 있다 |
| shared session 대신 handoff 모델인가 | `auth` 성공과 `app` 로그인 완료는 별도 단계일 수 있다 |

이 경우는 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)가 다음 문서다.

---

## 장면 2: external IdP가 `auth.example.com/callback`으로 돌아온다

이 장면은 cross-site일 수 있다.

```text
accounts.google.com  ->  auth.example.com/callback
```

여기서 `auth.example.com/callback`이 기존 transaction cookie를 다시 읽어야 하면,
브라우저는 `SameSite` 규칙과 callback 모양(top-level navigation인지, iframe/embedded인지)을 함께 본다.

대표 장면은 이렇다.

```http
Set-Cookie: login_state=xyz; Path=/auth; HttpOnly; Secure; SameSite=Lax
```

이 cookie가 external IdP return에서 다시 필요하면 `Lax`/`Strict`와 callback 형태를 함께 봐야 한다.

- top-level `GET` callback이면 `Lax`로도 충분한 흐름이 있다
- iframe, embedded login, 추가 cross-site request까지 살아야 하면 `SameSite=None; Secure`가 필요할 수 있다

즉 이 장면의 핵심은:

- 문제가 `auth` callback 자체에서 터진다
- `state mismatch`, callback loop, callback 400처럼 보이기 쉽다
- "subdomain이 달라서"가 아니라 **external site를 거쳐 돌아와서** 생길 수 있다

이 경우는 [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)로 이어 보면 된다.

---

## 장면 3: partner portal iframe 안에서만 로그인 유지가 안 된다

이 장면도 cross-site로 보는 편이 맞다.

```text
https://partner.com/page
  iframe -> https://app.example.com
```

app를 단독 탭으로 열면 잘 되는데 iframe 안에서만 cookie가 빠지면,
브라우저가 이를 third-party / cross-site 맥락으로 보고 `SameSite`를 막는지 먼저 본다.

| 관찰 | 먼저 읽는 해석 |
|---|---|
| 독립 탭에서는 정상 | app 자체 세션 모델은 크게 틀리지 않았을 수 있다 |
| partner iframe 안에서만 cookie 누락 | embedded context의 `SameSite` 전송 규칙이 더 가깝다 |
| redirect는 계속 `https://...` | proxy보다는 cross-site iframe 쪽이 더 가깝다 |

이 장면도 `SameSite=None; Secure` 후보가 되지만,
필요한 cookie만 열고 CSRF 경계는 따로 다시 봐야 한다.

---

## 먼저 10초 판별표

| 지금 보이는 현상 | 먼저 의심할 것 | 이유 |
|---|---|---|
| `auth.example.com`과 `app.example.com` 사이 이동에서만 깨진다 | `Domain`, host-only, handoff | different origin이지만 same-site일 수 있다 |
| external IdP callback에서만 `state mismatch`나 callback loop가 난다 | callback cookie의 `SameSite` | IdP return은 cross-site일 수 있다 |
| partner iframe 안에서만 세션이 안 붙는다 | embedded cookie의 `SameSite=None; Secure` | iframe은 cross-site 맥락이 되기 쉽다 |
| redirect가 `http://...`로 꺾인다 | proxy / scheme 전달 | 이 문서보다 proxy 문서가 먼저다 |
| 질문이 `fetch`, CORS, `credentials: "include"`부터 시작한다 | fetch/CORS bridge | `SameSite`와 다른 질문이다 |

---

## 초보자가 가장 자주 섞는 오해

### 1. "`auth.example.com`과 `app.example.com`은 host가 다르니 무조건 cross-site죠?"

그렇지 않다.

- same-origin은 아닐 수 있다
- same-site일 수 있다

그래서 subdomain handoff 장면에서는 `SameSite`보다 `Domain`/hardened handoff가 먼저인 경우가 많다.

### 2. "social login이면 전부 `SameSite=None`부터 넣어야 하나요?"

아니다.

- external IdP callback에서 필요한 cookie만 그럴 수 있다
- callback 뒤 `auth -> app` handoff는 same-site라서 다른 원인이 더 흔하다
- `None`은 넓게 여는 설정이라 필요한 cookie에만 제한적으로 둔다

### 3. "`SameSite`와 `fetch credentials`는 같은 이야기 아닌가요?"

아니다.

- `SameSite`는 브라우저의 cookie 전송 규칙이다
- `fetch credentials`는 JS 요청 옵션과 CORS 읽기 경계 쪽이다

즉 API/XHR 기준 질문이면 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)가 먼저다.

### 4. "cookie가 request에 실렸는데도 서버가 anonymous면 그래도 `SameSite` 문제인가요?"

보통 아니다.

이때는 브라우저 전송보다:

- session lookup
- handoff redemption
- BFF/session translation

같은 서버 측 복원 단계를 더 먼저 본다.

### 5. "`SameSite=None`이면 끝인가요?"

아니다.

- `Secure`가 같이 필요하다
- cross-site cookie를 열면 CSRF 경계도 같이 봐야 한다

---

## 다음 단계와 복귀 경로

| 지금 내 장면 | 다음 문서 |
|---|---|
| external IdP callback, iframe, partner portal 경로에서만 cookie가 빠진다 | [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md) |
| 증상 문장에 "`auth.example.com/callback`은 성공인데 `app.example.com` 첫 요청이 anonymous"가 들어 있다 | [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md) |
| login 뒤 redirect가 `http://...`로 바뀐다 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| DevTools에 `This Set-Cookie was blocked...`가 뜬다 | [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) |
| 증상 문장에 "`OAuth2`/`OIDC`/`id token`/session cookie가 한 번에 헷갈린다"가 들어 있다 | [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md) |
| callback cookie와 app-local session 생성이 같은 단계처럼 느껴진다 | [Social Login To Local Session Bridge](./social-login-to-local-session-bridge.md) |
| 질문이 `fetch`/CORS/API credential부터 시작한다 | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) |

---

## 첫 진단 뒤 복귀하는 browser/session route

첫 분기만 끝났다면 바로 deep dive로 내려가기보다, 같은 login-loop 기준점으로 한 번 복귀하는 편이 초보자에게 덜 헷갈린다.

| 단계 | 왜 이 단계로 복귀하나 | 링크 |
|---|---|---|
| 1. `primer` | login redirect와 `SavedRequest` 기준점을 다시 맞춘다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| 2. `primer bridge` | `401`/`302`, login HTML fallback, cookie 누락을 다시 분기한다 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| 3. `catalog` | beginner ladder에서 현재 위치를 다시 맞춘다 | [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) |
| 4. `catalog` | 다음 갈래를 navigator에서 다시 고른다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

## 한 칸만 더 가고 바로 돌아오는 규칙

- external IdP callback, iframe, partner portal 쪽으로 좁혀졌으면: [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)까지 본 뒤 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아온다.
- 증상 문장에 "`auth.example.com/callback`은 성공인데 `app.example.com` 첫 요청이 anonymous"가 남아 있으면: [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)로 한 칸 옮겨 shared cookie 기대인지 handoff 기대인지 먼저 고른 뒤 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아온다.
- 증상 문장에 "`OAuth2`/`OIDC`/`id token`/session cookie 역할이 한 문장처럼 섞인다"가 남아 있으면: [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)로 한 칸 돌아가 용어 층부터 다시 자른 뒤 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)에서 branch를 다시 고른다.
- redirect가 `http://...`로 꺾이거나 질문이 XHR/API credential로 바뀌었으면: 각각 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md), [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)로 옮긴 뒤 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아온다.

## 한 줄 정리

SameSite login callback 디버깅에서는 "`origin`이 다른가?"보다 "`site`가 다른가?"를 먼저 본다. external IdP return과 iframe은 cross-site일 수 있지만, callback 뒤 sibling subdomain handoff는 same-site일 수 있으므로 `SameSite`, `Domain`, session handoff를 한 단계씩 따로 봐야 덜 섞인다.
