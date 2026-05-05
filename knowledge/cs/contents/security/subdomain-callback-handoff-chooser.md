---
schema_version: 3
title: Subdomain Callback Handoff Chooser
concept_id: security/subdomain-callback-handoff-chooser
canonical: true
category: security
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/roomescape
review_feedback_tags:
- shared-cookie-vs-handoff-branch
- callback-trace-order
- first-app-request-anonymous
aliases:
- subdomain callback handoff chooser
- callback capture three traces
- set-cookie location first app request
- shared cookie vs handoff chooser
- callback success but app first request anonymous
- auth app subdomain chooser
- callback trace capture bridge
- one-time handoff branch
- shared-domain cookie branch
- social login callback anonymous chooser
- app session handoff return path
- oauth callback capture beginner
- 처음 배우는 callback trace
- 이거 뭐예요 callback handoff
- subdomain callback handoff chooser basics
symptoms:
- auth.example.com callback은 성공했는데 app.example.com 첫 요청이 비로그인이에요
- shared cookie 문제인지 handoff 누락인지 감이 안 와요
- callback 응답에서 Set-Cookie와 Location 중 무엇을 먼저 봐야 하는지 모르겠어요
intents:
- comparison
prerequisites:
- security/oauth2-oidc-social-login-primer
- security/login-callback-artifact-cheat-sheet
next_docs:
- security/cookie-scope-mismatch-guide
- security/subdomain-login-callback-boundaries
- security/samesite-login-callback-primer
linked_paths:
- contents/security/oauth2-oidc-social-login-primer.md
- contents/security/login-callback-artifact-cheat-sheet.md
- contents/security/subdomain-login-callback-boundaries.md
- contents/security/cookie-scope-mismatch-guide.md
- contents/security/samesite-login-callback-primer.md
- contents/network/http-https-basics.md
confusable_with:
- security/subdomain-login-callback-boundaries
- security/samesite-login-callback-primer
- security/social-login-to-local-session-bridge
forbidden_neighbors:
- contents/security/cookie-scope-mismatch-guide.md
- contents/security/social-login-to-local-session-bridge.md
expected_queries:
- auth.example.com callback은 성공했는데 app.example.com 첫 요청이 익명이야
- shared-domain cookie 구조랑 handoff 구조를 어떻게 구분해?
- callback response에서 set-cookie랑 location 중 뭐부터 봐야 해?
- subdomain social login 뒤 app_session이 안 생기면 어디서 갈라 봐야 해
- 처음 배우는데 callback handoff trace를 세 줄로 읽는 법을 알려줘
- auth 서브도메인 로그인 후 app 첫 요청 anonymous 원인 분기
contextual_chunk_prefix: |
  이 문서는 auth 서브도메인 callback은 성공했지만 app 첫 요청이 익명으로 보일 때, shared-domain cookie 구조인지 one-time handoff 뒤 app_session을 만드는 구조인지 골라 주는 chooser다. callback 응답에서 무엇을 심었나, 어디로 넘겼나, redirect 뒤 첫 app 요청이 무엇을 들고 갔나, shared cookie 기대 경로, handoff 교환 route, app-local session 생성 지점 같은 자연어 paraphrase가 본 문서의 분기 기준에 매핑된다.
---
# Subdomain Callback Handoff Chooser

> 한 줄 요약: `auth.example.com/callback`은 성공했는데 `app.example.com` 첫 요청이 anonymous라면, 먼저 "shared-domain cookie를 기대한 구조인지"와 "one-time handoff 뒤 app-local session을 만드는 구조인지"를 갈라 본다.

**난이도: 🟢 Beginner**

관련 문서:

- [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)
- [Login Callback Artifact Cheat Sheet](./login-callback-artifact-cheat-sheet.md)
- [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)
- [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
- [SameSite Login Callback Primer](./samesite-login-callback-primer.md)
- [HTTP와 HTTPS 기초](../network/http-https-basics.md)
- [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)
- [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: subdomain callback handoff chooser, callback capture three traces, set-cookie location first app request, shared cookie vs handoff chooser, callback success but app first request anonymous, auth app subdomain chooser, callback trace capture bridge, one-time handoff branch, shared-domain cookie branch, social login callback anonymous chooser, app session handoff return path, oauth callback capture beginner, 처음 배우는 callback trace, 이거 뭐예요 callback handoff, subdomain callback handoff chooser basics

## 먼저 잡는 mental model

초보자는 이 장면을 자주 한 문장으로 묶어 말한다.

- `auth.example.com/callback`은 성공했다
- 브라우저도 `302`를 따라 `app.example.com`으로 갔다
- 그런데 app 첫 요청은 anonymous다

여기서 첫 질문은 "`SameSite`인가요?"가 아니라 아래 둘 중 어느 구조를 기대했는가다.

1. `auth`가 shared-domain session cookie를 바로 만들어 `app`도 그 cookie를 읽는 구조
2. `auth`는 callback만 끝내고, `app`이 one-time handoff를 받아 자기 `app_session`을 새로 만드는 구조

이 둘을 먼저 갈라야 `Domain` 문제와 handoff 누락을 덜 섞는다.

## 20초 chooser

| 지금 캡처에서 먼저 보이는 것 | 더 가까운 구조 | 안전한 다음 문서 |
|---|---|---|
| callback request와 app request에서 둘 다 `session`이 보이는데 같은 cookie인지 역할이 헷갈린다 | shared/handoff 판단 전에 role split부터 필요 | [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md) |
| callback 응답에 `Set-Cookie: session=...; Domain=example.com` 같은 shared cookie가 보인다 | shared-domain cookie scope | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| callback 응답에는 shared cookie가 없고 `Location: https://app.example.com/login/complete?handoff=...` 같은 한 번짜리 artifact가 보인다 | one-time handoff -> app-local session | [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) |
| `auth_session`은 보이는데 `app_session`은 끝까지 안 생긴다 | handoff 또는 app local session creation | [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) |
| `auth`와 `app`만 오갈 때 깨지는데 external IdP/iframe은 아니다 | shared cookie scope 또는 handoff 모델 | 이 chooser에서 한 줄 고른 뒤 shared cookie 기대면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), handoff 기대면 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) |
| external IdP callback이나 iframe 경유에서만 깨진다 | cross-site callback/SameSite | [SameSite Login Callback Primer](./samesite-login-callback-primer.md) |

## callback capture 3개만으로 먼저 고르는 tiny bridge

초보자에게는 긴 HAR보다 아래 3줄이 더 빠르다.

1. callback 응답의 `Set-Cookie`
2. callback 응답의 `Location`
3. redirect 뒤 `app` 첫 요청

이 3개를 한 줄로 읽으면 "shared cookie를 기대한 구조인지"와 "handoff를 기대한 구조인지"를 거의 바로 고를 수 있다.

### 먼저 이렇게 캡처한다

| raw trace | 어디서 잡나 | 이 문서에서 보는 질문 |
|---|---|---|
| callback 응답 `Set-Cookie` | `auth.example.com/callback` response headers | callback이 공용 session을 심었나, 아니면 callback 전용 artifact만 남겼나 |
| callback 응답 `Location` | 같은 callback response headers | app 화면으로 바로 보냈나, `login/complete` 같은 교환 route로 보냈나 |
| 첫 `app` 요청 | redirect 직후 `app.example.com` request row | app이 shared cookie를 바로 들고 갔나, handoff redemption을 먼저 했나 |

이 문서의 분기는 세 줄을 "무엇을 심었나 -> 어디로 넘겼나 -> app이 무엇을 들고 갔나" 순서로 읽는 데 맞춰져 있다.

## trace를 branch로 읽는 표

| raw trace 3개에서 보는 것 | shared-domain cookie 쪽으로 기운다 | one-time handoff 쪽으로 기운다 | 안전한 다음 문서 |
|---|---|---|---|
| `Set-Cookie` | `Set-Cookie: session=...; Domain=example.com`처럼 parent/shared cookie가 보인다 | callback 응답에 shared cookie가 없거나 `auth` 전용 cookie만 보인다 | shared cookie 같으면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), handoff 같으면 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) |
| `Location` | `Location: https://app.example.com/home`처럼 바로 app 화면으로 간다 | `Location: https://app.example.com/login/complete?handoff=...`처럼 redemption route가 보인다 | `Location`만으로 모호하면 아래 `첫 app 요청`까지 같이 본다 |
| 첫 `app` 요청 | 첫 요청부터 `Cookie: session=...` 같은 shared cookie가 실려야 한다 | 첫 요청은 `/login/complete`나 교환 endpoint일 수 있고, 그 뒤 `app_session`이 생겨야 한다 | shared cookie가 안 실리면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), handoff 이후 `app_session`이 안 생기면 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) |

한 줄 기억법:

- `Set-Cookie`가 "무엇을 심었는지"
- `Location`이 "어디로 넘겼는지"
- 첫 app 요청이 "실제로 어떤 artifact를 들고 갔는지"

를 보여 준다.

## 30초 trace 판독 예시

| trace 묶음 | 먼저 내릴 결론 | 왜 그렇게 읽나 |
|---|---|---|
| `Set-Cookie: session=shared123; Domain=example.com` + `Location: https://app.example.com/home` + 첫 `app` 요청에 `Cookie: session=shared123` 기대 | shared-domain cookie branch | callback 응답이 이미 공용 로그인 artifact를 심었고, app은 그 cookie를 바로 읽어야 한다 |
| `Location: https://app.example.com/login/complete?handoff=abc` + 첫 `app` 요청이 `/login/complete?handoff=abc` | handoff branch | auth 쪽 성공을 app이 한 번 교환해 자기 세션으로 바꾸는 구조다 |
| `Set-Cookie`는 `auth_session`만 있고 `Location`은 app으로 갔지만 첫 `app` 요청에는 relevant cookie도 handoff route도 없음 | handoff 또는 branch 누락 의심 | auth callback 성공과 app 로그인 completion 사이 artifact가 비어 있다. 이때는 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)에서 redemption/app-local session 생성을 먼저 본다 |

## `auth.example.com/callback -> app.example.com` 미니 trace walkthrough

아래 표는 beginner가 Network 탭에서 가장 먼저 맞춰 볼 3-hop trace다.
질문은 항상 "`이번 hop에서 app이 기대하는 cookie/artifact가 무엇인가`" 하나면 된다.

| hop | 브라우저에서 보이는 요청/응답 | 이 hop에서 기대하는 cookie/artifact | 안 보이면 먼저 의심할 것 |
|---|---|---|---|
| 1 | `GET https://auth.example.com/callback?code=...&state=...` | callback request `Cookie`에 `login_state`, `oauth_txn` 같은 callback 검증용 artifact | external IdP return이라 `SameSite`/`Path` 때문에 callback용 cookie가 안 돌아온 경우 |
| 2 | callback 응답 `302 Location: https://app.example.com/...` | 둘 중 하나가 보여야 한다. `Set-Cookie: session=...; Domain=example.com` 같은 shared cookie, 또는 `Location: .../login/complete?handoff=...` 같은 one-time handoff artifact | shared cookie도 handoff도 없는데 app으로만 넘기면 branch 누락 가능성 |
| 3 | redirect 뒤 첫 `GET https://app.example.com/...` | shared pattern이면 request `Cookie`에 `session=...`, handoff pattern이면 `/login/complete?handoff=...` 뒤 `Set-Cookie: app_session=...` 생성 | request `Cookie`가 비면 scope 문제, cookie는 왔는데 anonymous면 app local session 복원 문제 |

한 줄로 읽으면 이렇다.

- callback request는 `auth`가 자기 검증용 artifact를 다시 읽는 hop이다.
- callback response는 `app`으로 넘길 최종 artifact를 심는 hop이다.
- 첫 `app` hop은 shared cookie를 바로 읽거나, handoff를 교환해 `app_session`을 만드는 hop이다.

## 15초 branch 메모

| 세 줄을 보고 적는 메모 | 먼저 고를 branch |
|---|---|
| "`Set-Cookie`가 이미 parent-domain session을 심었다" | shared-domain cookie |
| "`Location`이 `login/complete` 같은 교환 route로 보낸다" | one-time handoff |
| "첫 `app` 요청이 home/api인데 relevant cookie가 없다" | shared cookie 기대였는데 scope mismatch 가능성 우선 |
| "첫 `app` 요청 자체가 redemption route다" | handoff branch |

여기까지 적었는데도 구조가 안 잡히면 [Login Callback Artifact Cheat Sheet](./login-callback-artifact-cheat-sheet.md)로 한 칸 올라가 artifact 이름부터 다시 맞춘다.

## 이 bridge를 언제 쓰나

- HAR 전체를 읽기 전에 Network 탭의 callback row 하나와 첫 app row 하나만 빨리 보고 싶을 때
- `SameSite`, `Domain`, `session lookup`, `handoff`가 한 문장에 섞여 있을 때
- 리뷰 코멘트가 "`callback은 성공인데 app 첫 요청이 anonymous`" 정도로만 남아 있을 때
- 처음 배우는데 "이거 뭐예요, 뭘 캡처해야 하죠?" 상태에서 세 줄만 먼저 모으고 싶을 때

반대로 external IdP popup/iframe/cross-site 경유가 핵심이면 이 bridge보다 [SameSite Login Callback Primer](./samesite-login-callback-primer.md)에서 same-site/cross-site를 먼저 고정하는 편이 안전하다.

## 두 패턴을 가장 짧게 비교

| 질문 | shared-domain cookie | one-time handoff |
|---|---|---|
| `auth`가 만든 cookie가 `app` 요청에도 바로 실려야 하나 | 보통 예 | 보통 아니다 |
| 가장 먼저 보는 증거 | callback 응답의 `Set-Cookie` `Domain` | callback 뒤 `Location`의 handoff route나 code |
| app 첫 요청에서 기대하는 것 | shared `session` cookie | `login/complete` 같은 redemption 뒤 생성된 `app_session` |
| 초보자 오해 | "`Domain`만 넓히면 다 끝난다" | "`auth` cookie가 app에 안 가니 실패다" |

## 아주 짧은 예시

### 1. shared-domain cookie를 기대한 구조

```http
302 Found
Location: https://app.example.com/home
Set-Cookie: session=shared123; Domain=example.com; Path=/; HttpOnly; Secure
```

다음 기대:

- `app.example.com` 첫 요청에 `Cookie: session=shared123`

이 기대가 깨지면 먼저 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 간다.

### 2. one-time handoff를 기대한 구조

```http
302 Found
Location: https://app.example.com/login/complete?handoff=abc123
```

다음 기대:

- `app`이 handoff를 한 번 소모한다
- 그 뒤 `Set-Cookie: app_session=...`를 만든다

이 기대가 깨지면 먼저 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)로 간다.

## common confusion

- `auth_session`이 `app.example.com`에 안 간다고 곧바로 실패는 아니다. handoff 구조라면 정상일 수 있다.
- sibling subdomain 이동은 same-origin이 아니어도 same-site일 수 있다. 그래서 무조건 `SameSite=None`부터 보는 것은 빠른 점프다.
- callback 성공과 app 로그인 완료는 같은 이벤트가 아닐 수 있다.

## primer -> primer bridge ladder

1. 이 chooser에서 shared cookie 기대인지 handoff 기대인지 먼저 고른다.
2. shared cookie 기대면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), handoff 기대면 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)로 한 칸만 내려간다.
3. 읽다가 `access token`, `id token`, 내부 session 역할이 다시 섞이면 [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)로 한 칸 되돌아간다.
4. callback capture 세 줄만 다시 모으고 싶으면 이 문서의 `callback capture 3개` 표로 되돌아온다.
5. 이 symptom을 beginner ladder 전체에서 다시 위치시키고 싶으면 [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)로 먼저 올라간다.
6. 갈래를 다시 잃으면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아온다.

## 한 줄 정리

이 chooser는 callback capture 3줄(`Set-Cookie`, `Location`, 첫 `app` 요청)만으로 shared-domain cookie branch와 one-time handoff branch를 먼저 고르고, 바로 다음 문서 한 장으로만 내려가도록 만든 beginner entrypoint다.

| 방금 고른 갈래 | 다음 한 걸음 | beginner return path |
|---|---|---|
| shared-domain cookie 기대 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)에서 `Domain`/host-only/`Path`를 먼저 확인 | 한 칸만 읽고 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아온다 |
| one-time handoff 기대 | [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)에서 callback 뒤 `Location`, `app_session`, redemption을 확인 | handoff branch를 끝내면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 복귀한다 |
| external IdP callback/iframe 경유만 의심 | [SameSite Login Callback Primer](./samesite-login-callback-primer.md)에서 same-site/cross-site를 먼저 분리 | cross-site branch를 본 뒤에도 복귀점은 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)다 |
