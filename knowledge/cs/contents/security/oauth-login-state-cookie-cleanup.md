---
schema_version: 3
title: OAuth Login State Cookie Cleanup
concept_id: security/oauth-login-state-cookie-cleanup
canonical: false
category: security
difficulty: beginner
doc_role: deep_dive
level: beginner
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- oauth login state cookie cleanup
- social login callback cookie cleanup
- old login_state cookie cleanup
- oauth callback host migration cookie cleanup
aliases:
- oauth login state cookie cleanup
- social login callback cookie cleanup
- old login_state cookie cleanup
- oauth callback host migration cookie cleanup
- oauth callback path migration cookie cleanup
- state mismatch after callback move
- old oauth session cookie survives callback migration
- social login callback migration primer
- callback host changed old cookie remains
- callback path changed old cookie remains
- host-only login state cleanup
- oauth cookie tombstone exact path
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md
- contents/security/samesite-login-callback-primer.md
- contents/security/oauth2-oidc-social-login-primer.md
- contents/security/callback-cookie-name-splitter.md
- contents/security/subdomain-login-callback-boundaries.md
- contents/security/cookie-scope-migration-cleanup.md
- contents/security/duplicate-cookie-name-shadowing.md
- contents/security/host-cookie-migration-primer.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- OAuth Login State Cookie Cleanup 핵심 개념을 설명해줘
- oauth login state cookie cleanup가 왜 필요한지 알려줘
- OAuth Login State Cookie Cleanup 실무 설계 포인트는 뭐야?
- oauth login state cookie cleanup에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 OAuth Login State Cookie Cleanup를 다루는 deep_dive 문서다. OAuth/social login callback host나 path를 옮길 때는 새 `login_state`/session cookie를 발급하는 것과, 예전 callback scope에 남은 old cookie를 지우는 것을 따로 설계해야 한다. 특히 old cookie가 host-only였거나 `Path=/oauth2`처럼 좁았다면, **옛 host/path를 정확히 맞춘 cleanup tombstone**이 없으면 callback loop나 `state mismatch`가 오래 남을 수 있다. 검색 질의가 oauth login state cookie cleanup, social login callback cookie cleanup, old login_state cookie cleanup, oauth callback host migration cookie cleanup처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# OAuth Login State Cookie Cleanup

> 한 줄 요약: OAuth/social login callback host나 path를 옮길 때는 새 `login_state`/session cookie를 발급하는 것과, 예전 callback scope에 남은 old cookie를 지우는 것을 따로 설계해야 한다. 특히 old cookie가 host-only였거나 `Path=/oauth2`처럼 좁았다면, **옛 host/path를 정확히 맞춘 cleanup tombstone**이 없으면 callback loop나 `state mismatch`가 오래 남을 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)

> 문서 역할: `follow-up primer`
>
> broad한 OAuth 입문 문서가 아니라, 이미 social login callback host/path migration을 했거나 `state mismatch`, callback loop, old callback cookie 잔존이 보인 뒤에 여는 문서다. `SameSite` 자체가 처음 헷갈리면 [SameSite Login Callback Primer](./samesite-login-callback-primer.md)를 먼저 보고, duplicate raw header나 old scope tombstone 설계가 핵심이면 이 문서로 내려온다.

> 관련 문서:
> - `[primer]` [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)
> - `[primer]` [SameSite Login Callback Primer](./samesite-login-callback-primer.md)
> - `[primer bridge]` [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md)
> - `[primer]` [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)
> - `[follow-up primer]` [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)
> - `[follow-up primer]` [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md)
> - `[primer]` [Host Cookie Migration Primer](./host-cookie-migration-primer.md)
> - `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: oauth login state cookie cleanup, social login callback cookie cleanup, old login_state cookie cleanup, oauth callback host migration cookie cleanup, oauth callback path migration cookie cleanup, state mismatch after callback move, old oauth session cookie survives callback migration, social login callback migration primer, callback host changed old cookie remains, callback path changed old cookie remains, host-only login state cleanup, oauth cookie tombstone exact path, oauth cookie tombstone exact host, social login cookie cleanup beginner, oauth login state cookie cleanup basics
retrieval-anchor-keywords: oauth callback cookie path shadowing, callback session cookie old path, login_state cookie old path cleanup, auth callback rename cleanup, callback host cutover cookie cleanup, old callback cookie shadows new session, oauth callback duplicate cookie, stale callback transaction after social login deploy, old host cookie cannot be deleted from new host, cleanup old auth host cookie from callback, oauth migration cleanup matrix

## 왜 이 문서를 지금 여나

초보자가 migration 뒤 자주 보는 장면은 이렇다.

- callback URL을 `auth.example.com/callback`에서 `login.example.com/login/oauth2/code/google`로 옮겼다
- 또는 `/oauth2/callback/*`를 `/login/oauth2/code/*`로 바꿨다
- 새 login은 어느 정도 동작하는데 특정 브라우저에서만 callback loop, `state mismatch`, 다시 `/login`이 난다
- DevTools에는 old `login_state`, `oauth_txn`, `session` row가 남아 있다

여기서 핵심 오해는 이것이다.

- callback route를 옮기면 old callback cookie도 자동으로 정리될 것 같지만
- 브라우저는 old cookie가 obsolete인지 스스로 판단하지 않는다
- 서버가 **옛 host/path마다 따로 만료 지시**를 보내야 한다

짧게 말하면:

- **새 callback cookie 발급**과
- **옛 callback cookie 회수**는
- 같은 작업이 아니다

---

## 가장 중요한 mental model

OAuth/social login에는 보통 cookie가 두 층 있다.

| 층 | 대표 예시 | 왜 존재하나 | migration 뒤 남으면 생기는 일 |
|---|---|---|---|
| callback transaction cookie | `login_state`, `oauth_txn`, `PKCE_VERIFIER` | callback이 내가 시작한 login flow인지 확인 | `state mismatch`, callback 400, callback loop |
| main session cookie | `session`, `app_session` | callback 뒤 app 로그인 유지 | callback은 성공인데 첫 화면에서 다시 익명 |

둘 다 cookie라서 같이 섞이기 쉽지만 질문이 다르다.

- callback transaction cookie는 **callback request 한 번**을 통과시키기 위한 것
- main session cookie는 **callback 이후 요청들**에 계속 필요한 것

그래서 callback host/path migration에서는 보통 아래 둘을 따로 본다.

1. old callback transaction cookie cleanup
2. old main session cookie cleanup

초보자용 기억 문장:

- callback 주소를 옮겼다면, 옛 주소에 묶인 출입증도 따로 회수해야 한다

---

## 먼저 15초 판별표

| 지금 보이는 현상 | 더 가까운 원인 | 먼저 할 일 |
|---|---|---|
| external IdP에서 돌아온 직후 `state mismatch`나 callback 400 | old/new callback transaction cookie가 섞였거나 old path cookie가 남았다 | callback request의 `Cookie` header와 old callback cookie `Path` 확인 |
| callback은 성공했는데 첫 app 요청이 anonymous | main session cleanup 또는 handoff가 더 가깝다 | [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)로 분기 |
| login host를 `auth.example.com`에서 `login.example.com`으로 옮긴 뒤 특정 브라우저만 꼬임 | old host-only cookie가 예전 host에 남아 있다 | old host에서 `Domain` 없이 tombstone 보낼 수 있는지 확인 |
| callback path를 `/oauth2/*`에서 `/login/oauth2/*`로 바꾼 뒤 일부 route만 loop | old `Path=/oauth2` 또는 `/auth` cookie가 남아 있다 | old path 그대로 tombstone 추가 |
| raw `Cookie` header에 같은 이름이 두 번 보인다 | 실제 duplicate shadowing이 이미 발생 중이다 | [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md)도 함께 확인 |

---

## 왜 callback migration에서 더 헷갈리나

callback cookie는 보통 짧게 살고, 경로도 좁게 잡는 경우가 많다.

예를 들어 예전 구조가 이랬다고 하자.

```http
Set-Cookie: login_state=old123; Path=/oauth2/callback; HttpOnly; Secure; SameSite=Lax
```

새 구조는 이렇게 바뀌었다.

```http
Set-Cookie: login_state=new999; Path=/login/oauth2/code; HttpOnly; Secure; SameSite=Lax
```

이때 새 cookie만 발급하면 old cookie는 남을 수 있다.
특히 callback 관련 cookie는 아래 이유로 문제를 키운다.

- 이름을 계속 재사용하는 경우가 많다
- callback request에서만 읽으니 일부 route에서만 증상이 난다
- 실패 장면이 session 누락이 아니라 `state mismatch`처럼 보여서 scope 문제로 안 보일 수 있다

즉 migration 뒤 callback 오류는 provider 문제처럼 보이지만, 실제로는 **old callback cookie tail**일 수 있다.

---

## host 이동과 path 이동은 다른 질문이다

| 무엇을 바꿨나 | 먼저 맞춰야 할 cleanup 축 | beginner가 자주 놓치는 점 |
|---|---|---|
| callback host | old host-only 여부, `Domain` | 새 host 응답만으로는 old host-only cookie를 못 지울 수 있다 |
| callback path | old `Path` | `Path=/` 새 cookie가 old `/oauth2` cookie를 자동으로 지우지 않는다 |
| 둘 다 바뀜 | host + `Path` 둘 다 | tombstone도 old scope별로 여러 개 필요할 수 있다 |

핵심은 이것이다.

- host를 옮겼으면 old host cleanup 경로가 있어야 한다
- path를 옮겼으면 old path cleanup이 따로 있어야 한다
- 둘 다 옮겼으면 tombstone도 old scope별로 여러 개 필요할 수 있다

---

## 예시 1: callback path migration

예전 callback cookie가 아래처럼 `/oauth2/callback`에 묶여 있었다고 하자.

```http
Set-Cookie: login_state=old123; Path=/oauth2/callback; HttpOnly; Secure; SameSite=Lax
```

새 callback은 `/login/oauth2/code/google`로 옮겼다.

```http
Set-Cookie: login_state=new999; Path=/login/oauth2/code; HttpOnly; Secure; SameSite=Lax
```

여기서 old cookie cleanup은 따로 필요하다.

```http
Set-Cookie: login_state=; Path=/oauth2/callback; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Secure; SameSite=Lax
```

핵심은 old `Path=/oauth2/callback`를 그대로 맞추는 것이다.

- `Path=/` tombstone이라고 old path cookie가 자동 삭제되지는 않는다
- callback cookie는 일부 path에서만 다시 읽히므로, "가끔만 실패"하는 증상으로 보이기 쉽다

---

## 예시 2: callback host migration

예전 login host가 `auth.example.com`이고 old cookie가 host-only였다고 하자.

```http
Set-Cookie: login_state=old123; Path=/; HttpOnly; Secure; SameSite=Lax
```

이후 login host를 `login.example.com`으로 옮겼다.
새 host에서 아래처럼 새 cookie를 발급할 수는 있다.

```http
Set-Cookie: login_state=new999; Path=/; HttpOnly; Secure; SameSite=Lax
```

하지만 이것만으로 `auth.example.com`의 old host-only cookie는 사라지지 않는다.

old host cleanup은 old host 응답에서 `Domain` 없이 보내야 한다.

```http
Set-Cookie: login_state=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Secure; SameSite=Lax
```

중요한 점은 두 가지다.

- old cookie가 host-only였다면 delete도 `Domain` 없이 보내야 한다
- `login.example.com` 응답만으로는 `auth.example.com` old host-only cookie를 정리하지 못할 수 있다

즉 callback host cutover에서는 **old host cleanup endpoint를 잠시 유지**하는 설계가 자주 필요하다.

---

## cleanup은 callback cookie와 session cookie를 따로 적는다

social login migration에서 자주 생기는 실수는 `login_state`만 지우거나, 반대로 main session만 지우는 것이다.

| old artifact | 흔한 old scope | 필요한 cleanup 질문 |
|---|---|---|
| `login_state`, `oauth_txn` | old callback host/path | callback request 한 번용 cookie를 정확히 회수했나 |
| `session`, `app_session` | old auth host, old shared domain, old app path | callback 이후 로그인 유지용 cookie를 따로 회수했나 |

짧은 실전 규칙:

- callback cookie cleanup과 main session cleanup은 한 장표에 같이 적는다
- "이름이 다르니 대충 지워지겠지"라고 생각하지 않는다
- old scope 하나당 tombstone 하나라는 규칙은 둘 다 같다

정확한 scope matrix 자체가 핵심이면 [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)으로 이어 가면 된다.

---

## rollout 때 beginner-safe한 패턴

1. 현재 브라우저에 남아 있을 old callback cookie 이름과 old scope를 inventory한다.
2. 새 callback host/path에서 필요한 새 cookie를 발급한다.
3. 같은 시기 동안 old host 또는 old path에서 old scope tombstone을 같이 보낸다.
4. callback success 응답, login start 응답, logout 응답처럼 자주 타는 경로에 cleanup을 잠시 유지한다.
5. `Application > Cookies`와 callback request raw `Cookie` header에서 old row가 사라졌는지 확인한다.

특히 beginner에게 중요한 점:

- cleanup을 한 응답만 보지 말고, **실패했던 callback request**에서 old cookie가 정말 빠졌는지 본다
- host cutover라면 "새 host에서 잘 된다"보다 "old host에서도 cleanup이 한 번은 실행된다"가 중요할 수 있다

---

## common confusion

### 1. "callback URL을 바꿨으니 old `login_state`는 자동 무효 아닌가요?"

아니다.

- 브라우저는 old cookie가 obsolete인지 추론하지 않는다
- old scope를 정확히 맞춘 expired `Set-Cookie`가 필요하다

### 2. "새 host에서 delete cookie를 보내면 old host cookie도 지워지죠?"

보통 아니다.

- old cookie가 host-only였다면 old host 응답에서 지워야 한다
- 그래서 host migration에는 old host cleanup endpoint가 남아야 할 수 있다

### 3. "`state mismatch`면 provider 설정 문제 아닌가요?"

그럴 수도 있지만 먼저 old callback cookie tail을 배제해야 한다.

- callback host/path를 바꾼 직후
- 특정 브라우저에만 남고
- old callback cookie row가 보인다면

provider보다 cookie scope cleanup 쪽이 더 가까울 수 있다.

### 4. "callback은 성공했는데 첫 화면이 anonymous면 이 문서 문제인가요?"

항상 그렇지는 않다.

- 이 경우는 callback cookie보다 main session/handoff가 더 중요할 수 있다
- 먼저 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)로 내려가 분리한다

### 5. "`SameSite=None`만 넣으면 migration 문제가 끝나나요?"

아니다.

- `SameSite`는 cross-site 전송 규칙이다
- old host/path cleanup과는 별도 질문이다

즉 callback migration에서는 `SameSite`와 cleanup scope를 동시에 보되, 같은 문제로 섞지 않는 편이 안전하다.

---

## 어디서 확인하나

| 어디서 보나 | 확인할 질문 |
|---|---|
| login start / callback success 응답의 `Set-Cookie` | 새 cookie와 old-scope tombstone이 같이 내려왔나 |
| `Application > Cookies` | old `login_state`/`oauth_txn`/session row가 정말 사라졌나 |
| 실패했던 callback request의 raw `Cookie` header | old callback cookie가 아직 실리나 |
| redirect chain | old host cleanup 경로가 실제로 한 번은 타나 |

가장 중요한 순서는 이것이다.

1. old scope inventory를 적는다
2. cleanup 응답 `Set-Cookie`가 old scope와 exact match인지 본다
3. 실패했던 callback request에서 old cookie가 실제로 빠졌는지 확인한다

---

## 어디로 이어서 읽나

| 지금 남은 질문 | 다음 문서 |
|---|---|
| callback용 cookie와 main session cookie 역할이 아직 섞인다 | [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md) |
| exact domain/path tombstone 설계를 더 자세히 보고 싶다 | [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md) |
| raw `Cookie` header에 같은 이름이 두 번 보인다 | [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md) |
| callback은 성공인데 app 첫 요청이 anonymous다 | [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) |
| 지금 증상을 browser/session 전체 path에서 다시 고르고 싶다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

## 한 줄 정리

OAuth/social login callback migration의 핵심은 "새 callback을 열기"가 아니라 "옛 callback scope를 닫기"까지 같이 끝내는 것이다. old callback host/path에 남은 `login_state`나 session cookie는 자동 정리되지 않으므로, old host-only 여부와 old `Path`를 정확히 맞춘 cleanup tombstone을 별도로 설계해야 beginner가 `state mismatch`와 callback loop를 덜 헷갈린다.
