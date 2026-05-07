---
schema_version: 3
title: Callback Cookie Name Splitter
concept_id: security/callback-cookie-name-splitter
canonical: false
category: security
difficulty: beginner
doc_role: deep_dive
level: beginner
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- callback cookie name splitter
- callback cookie vs duplicate cookie
- callback cookie same name as session
- callback cookie vs app session cookie
aliases:
- callback cookie name splitter
- callback cookie vs duplicate cookie
- callback cookie same name as session
- callback cookie vs app session cookie
- same name different role
- callback 400 loop
- app first request anonymous
- social login handoff cookie confusion
- callback verification cookie vs main session cookie
- auth callback session name collision
- 왜 같은 이름인데 역할이 달라
- 왜 callback은 되는데 app은 anonymous
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/samesite-login-callback-primer.md
- contents/security/subdomain-callback-handoff-chooser.md
- contents/security/subdomain-login-callback-boundaries.md
- contents/security/social-login-to-local-session-bridge.md
- contents/security/duplicate-cookie-name-shadowing.md
- contents/security/cookie-scope-mismatch-guide.md
- contents/network/cookie-session-jwt-browser-flow-primer.md
- contents/security/oauth-login-state-cookie-cleanup.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Callback Cookie Name Splitter 핵심 개념을 설명해줘
- callback cookie name splitter가 왜 필요한지 알려줘
- Callback Cookie Name Splitter 실무 설계 포인트는 뭐야?
- callback cookie name splitter에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Callback Cookie Name Splitter를 다루는 deep_dive 문서다. login callback용 one-time cookie와 main session cookie가 같은 이름을 써도, 둘은 같은 역할이 아니다. 먼저 "이 cookie가 callback 확인용인지, 이후 요청의 로그인 유지용인지"를 갈라야 `SameSite`, `Domain`, duplicate shadowing을 헷갈리지 않는다. 검색 질의가 callback cookie name splitter, callback cookie vs duplicate cookie, callback cookie same name as session, callback cookie vs app session cookie처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Callback Cookie Name Splitter

> 한 줄 요약: login callback용 one-time cookie와 main session cookie가 같은 이름을 써도, 둘은 같은 역할이 아니다. 먼저 "이 cookie가 callback 확인용인지, 이후 요청의 로그인 유지용인지"를 갈라야 `SameSite`, `Domain`, duplicate shadowing을 헷갈리지 않는다.

**난이도: 🟢 Beginner**

관련 문서:
- [SameSite Login Callback Primer](./samesite-login-callback-primer.md)
- [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)
- [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)
- [Social Login To Local Session Bridge](./social-login-to-local-session-bridge.md)
- [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md)
- [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
- [Cookie / Session / JWT Browser Flow Primer](../network/cookie-session-jwt-browser-flow-primer.md)
- [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)
- [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: callback cookie name splitter, callback cookie vs duplicate cookie, callback cookie same name as session, callback cookie vs app session cookie, same name different role, callback 400 loop, app first request anonymous, social login handoff cookie confusion, callback verification cookie vs main session cookie, auth callback session name collision, 왜 같은 이름인데 역할이 달라, 왜 callback은 되는데 app은 anonymous, beginner callback cookie primer, raw cookie header duplicate name, callback cookie name splitter basics

> 초보자 20초 route box:
> - social login callback은 성공했는데 `auth -> app` handoff 뒤 첫 요청이 anonymous라면 먼저 [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)에서 shared cookie 기대인지 handoff 기대인지 고른다.
> - 그런데 trace 안에서 callback 검증용 cookie와 main session cookie가 둘 다 `session`처럼 보여 역할 자체가 섞이면 이 문서 표부터 본다.
> - 갈래를 하나 정한 뒤에는 항상 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아가 다음 분기를 다시 고른다.

## 먼저 잡을 mental model

초보자는 아래 두 문장을 같은 뜻으로 읽기 쉽다.

- "`session` cookie가 callback에서 한 번 쓰였다"
- "`session` cookie가 이후 페이지에서도 로그인 유지에 쓰인다"

하지만 실제로는 다를 수 있다.

- callback에서만 잠깐 읽고 버리는 one-time cookie일 수 있다
- 이후 요청마다 계속 쓰는 main session cookie일 수 있다
- 둘이 **우연히 같은 이름**을 쓰고 있을 수도 있다

핵심은 이것이다.

- 이름이 같아도 먼저 **역할**을 갈라야 한다

social login handoff를 넣어 아주 짧게 그리면 보통 이렇다.

```text
external IdP -> auth.example.com/callback -> app.example.com/login/complete or /home
```

이때 초보자가 자주 섞는 두 cookie는 보통 아래 둘이다.

| 먼저 갈라야 할 것 | 왜 존재하나 | 보통 언제 다시 보나 |
|---|---|---|
| callback 검증용 cookie | `state`나 transaction을 callback에서 다시 확인하려고 | `/callback` 근처 한 번 |
| main session cookie | app가 이후 요청마다 로그인 사용자를 복원하려고 | `/home`, `/api/me`, 다음 navigation마다 |

이 표에서 기억할 한 줄:

- callback 성공과 app 로그인 완료는 같은 장면이 아닐 수 있다

---

## 한눈에 갈라보는 decision card

| 지금 보이는 현상 | 먼저 떠올릴 질문 | 다음 문서 |
|---|---|---|
| callback에서만 `state mismatch`, 400, loop가 난다 | 이 cookie는 callback 확인용인가 | [SameSite Login Callback Primer](./samesite-login-callback-primer.md) |
| callback host/path를 옮긴 뒤 old `login_state`가 남아 보인다 | 역할 혼동보다 old callback scope cleanup이 필요한가 | [OAuth Login State Cookie Cleanup](./oauth-login-state-cookie-cleanup.md) |
| callback은 성공인데 app 첫 요청이 anonymous다 | callback용 cookie와 app session cookie를 같은 것으로 착각했나 | [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) |
| raw `Cookie` header에 같은 이름이 두 번 보인다 | 역할 혼동이 아니라 실제 duplicate shadowing인가 | [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md) |
| `Application > Cookies`에는 보이는데 실패 요청 header에는 안 실린다 | 이름보다 `Domain`/`Path`/`SameSite` scope 문제인가 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |

초보자용 한 줄 규칙은 이것이다.

- callback 근처에서 한 번만 쓰이면 "역할 분리"부터 본다.
- 실패한 요청 raw `Cookie` header에 같은 이름이 두 번 찍히면 그때 "duplicate header shadowing"으로 내려간다.

---

## 같은 이름이어도 질문은 두 개다

| 질문 | callback용 cookie | main session cookie |
|---|---|---|
| 왜 존재하나 | callback이 진짜 내가 시작한 login flow인지 확인 | 이후 요청에서 로그인 사용자를 다시 찾기 위해 |
| 언제 다시 필요하나 | `.../callback` 근처 한 번 | 보호 페이지, API, 다음 navigation마다 반복 |
| 실패하면 보이는 장면 | `state mismatch`, callback 400, callback loop | callback은 끝났는데 첫 페이지가 anonymous, `/login` 재진입 |
| 먼저 보는 축 | cross-site callback, `SameSite`, callback path | `Domain`, `Path`, subdomain handoff, server session lookup |

이 표에서 기억할 한 줄은 이것이다.

- callback용 cookie가 살아도 main session이 없을 수 있고, 반대도 가능하다

---

## social login handoff에서 특히 왜 헷갈리나

`auth.example.com/callback`과 `app.example.com`을 오가는 trace에서는 같은 이름 `session`이 보여도 실제로는 아래 둘 중 하나일 수 있다.

| 브라우저에서 본 장면 | 성급한 해석 | 더 안전한 해석 |
|---|---|---|
| callback request에 `Cookie: session=cb123`이 있다 | "이미 app 로그인 session이 있다" | callback 검증용 one-time cookie일 수 있다 |
| callback 뒤 app 첫 요청에 `Cookie: session=app999`를 기대한다 | "callback에서 본 session이 그대로 와야 한다" | handoff 뒤 app가 새 session을 발급하는 구조일 수 있다 |
| callback에서는 `session`이 보였는데 app 요청에는 안 보인다 | "브라우저가 session을 잃어버렸다" | callback용 cookie는 auth host 전용이고, app는 별도 session을 기다리는 구조일 수 있다 |

그래서 social login handoff 디버깅에서는 순서를 이렇게 잡는 편이 안전하다.

1. callback에서 본 `session`이 검증용인지부터 자른다.
2. 그다음 app가 shared cookie를 바로 기대하는지, handoff 뒤 local session을 새로 만드는지 고른다.
3. 그 뒤에야 `Domain`, `Path`, `SameSite`, duplicate shadowing을 세부 원인으로 내려간다.

`auth` 성공을 `app` local session으로 번역하는 전체 그림이 아직 흐리면 [Social Login To Local Session Bridge](./social-login-to-local-session-bridge.md)를 먼저 본다.
shared cookie 기대인지 handoff 기대인지부터 빨리 고르고 싶으면 [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)로 간다.

---

## 가장 흔한 혼동 장면

예를 들어 브라우저 trace가 이렇게 보일 수 있다.

```text
accounts.google.com -> auth.example.com/callback -> app.example.com/home
```

그리고 쿠키 이름은 둘 다 `session`처럼 보인다.

| 실제 역할 | 초보자가 잘못 읽는 문장 | 더 정확한 해석 |
|---|---|---|
| callback 검사용 `session` | "session이 있으니 app도 로그인됐겠네" | 아직 callback 검증만 끝났을 수 있다 |
| app 로그인 유지용 `session` | "callback에서 안 보였으니 세션이 아예 없네" | callback용 cookie와 별도일 수 있다 |

즉 "이름이 같다"는 사실만으로는 아래를 알 수 없다.

- 어느 host/path에서 쓰이는지
- 한 번만 쓰는지 계속 쓰는지
- callback 검증용인지, app session 복원용인지

---

## duplicate shadowing과는 무엇이 다른가

둘 다 "같은 이름" 이야기라 자주 섞인다.

| 헷갈리는 주제 | 핵심 질문 | 대표 신호 |
|---|---|---|
| 역할 분리 실패 | 이 cookie가 callback 확인용인지 main session용인지 | callback 성공과 app 로그인 완료를 같은 사건으로 읽는다 |
| duplicate cookie shadowing | 같은 이름 cookie가 서로 다른 scope로 동시에 전송되나 | `Cookie: session=...; session=...` 처럼 중복 전송이 보인다 |

따라서 순서는 이렇게 잡는 편이 안전하다.

1. 먼저 이 cookie의 역할이 callback용인지 session용인지 자른다.
2. 그다음 실제로 같은 이름 cookie가 둘 이상 전송되는지 본다.

raw `Cookie` header에 같은 이름이 두 번 안 보인다면, 지금 문제는 shadowing보다 **역할 혼동**일 수 있다.

---

## 같은 이름을 보면 꼭 묻는 세 질문

| 질문 | 이유 |
|---|---|
| 이 cookie는 callback request에서만 읽히나, 이후 app request에서도 읽히나 | one-time artifact인지 session인지 바로 갈린다 |
| 실패 장면이 callback 400/loop인가, app 첫 요청 anonymous인가 | callback 단계 실패와 session 단계 실패를 분리한다 |
| raw `Cookie` header에 같은 이름이 두 번 실리나 | 역할 혼동인지, 실제 duplicate shadowing인지 갈린다 |

이 세 질문만 해도 beginner 기준으로 절반은 정리된다.

---

## common confusion

- "`session`이라는 이름이면 다 같은 session 아닌가요?"
  - 아니다. 이름보다 역할과 재사용 시점을 먼저 본다.
- "callback에서 cookie가 보였으니 app 로그인도 끝난 거죠?"
  - 아니다. callback 검증과 app session 생성은 별도 단계일 수 있다.
- "같은 이름이니까 무조건 duplicate cookie 문제죠?"
  - 아니다. header 중복이 없으면 naming confusion일 수도 있다.

---

## 한 줄 정리

이 문서는 "같은 이름인데 같은 역할인가?"를 먼저 가르는 primer bridge다.

| 지금 정리된 결론 | 다음 한 걸음 |
|---|---|
| external IdP callback에서만 깨진다 | [SameSite Login Callback Primer](./samesite-login-callback-primer.md) |
| social login handoff 전체가 아직 흐리다 | [Social Login To Local Session Bridge](./social-login-to-local-session-bridge.md) |
| `auth -> app`에서 shared cookie인지 handoff인지부터 모르겠다 | [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md) |
| callback은 성공인데 `auth -> app` handoff 뒤 anonymous다 | [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) |
| 같은 이름 cookie가 실제로 중복 전송된다 | [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md) |
| 저장은 보이는데 실패 요청에 cookie가 안 간다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| 갈래를 다시 잃었다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

초보자 기준 복귀 경로는 README anchor 두 개만 기억하면 충분하다.

- "지금 이 문서가 너무 세부적으로 느껴진다"면 먼저 [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)로 올라가 `primer -> primer bridge -> deep dive` 순서를 다시 맞춘다.
- 세부 문서에서 막히면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아와 callback 실패인지, cookie-not-sent인지, server-mapping-missing인지 다시 고른다.
