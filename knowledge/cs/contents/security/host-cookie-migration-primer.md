---
schema_version: 3
title: __Host- Cookie Migration Primer
concept_id: security/host-cookie-migration-primer
canonical: true
category: security
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 70
mission_ids: []
review_feedback_tags:
- __host- cookie migration primer
- __host cookie migration
- host-only cookie migration primer
- shared-domain session to __host cookie
aliases:
- __host- cookie migration primer
- __host cookie migration
- host-only cookie migration primer
- shared-domain session to __host cookie
- domain example.com to __host
- parent-domain cookie to host-only cookie
- host-prefixed session migration
- __host session stale auth state
- __host cookie logout cleanup
- __host cookie cutover
- __host cookie duplicate shadowing
- shared cookie to app-local session
symptoms: []
intents:
- definition
- deep_dive
prerequisites: []
next_docs: []
linked_paths:
- contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md
- contents/security/cookie-scope-migration-cleanup.md
- contents/security/cookie-prefixes-host-secure-primer.md
- contents/security/cookie-scope-mismatch-guide.md
- contents/security/subdomain-logout-cookie-cleanup-primer.md
- contents/security/duplicate-cookie-name-shadowing.md
- contents/security/subdomain-callback-handoff-chooser.md
- contents/security/subdomain-login-callback-boundaries.md
- contents/security/secure-cookie-behind-proxy-guide.md
- contents/security/session-cookie-jwt-basics.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- __Host- Cookie Migration Primer 핵심 개념을 설명해줘
- __host- cookie migration primer가 왜 필요한지 알려줘
- __Host- Cookie Migration Primer 실무 설계 포인트는 뭐야?
- __host- cookie migration primer에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 __Host- Cookie Migration Primer를 다루는 primer 문서다. `__Host-` cookie는 "더 안전한 shared-domain cookie"가 아니라 **한 host에만 묶인 host-only cookie**다. 그래서 migration 핵심은 prefix를 붙이는 것보다, old shared-domain session을 어떻게 끊고 각 host의 새 로그인 상태를 어떻게 만들지 분리하는 데 있다. 검색 질의가 __host- cookie migration primer, __host cookie migration, host-only cookie migration primer, shared-domain session to __host cookie처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# __Host- Cookie Migration Primer

> 한 줄 요약: `__Host-` cookie는 "더 안전한 shared-domain cookie"가 아니라 **한 host에만 묶인 host-only cookie**다. 그래서 migration 핵심은 prefix를 붙이는 것보다, old shared-domain session을 어떻게 끊고 각 host의 새 로그인 상태를 어떻게 만들지 분리하는 데 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)

> 문서 역할: `primer`
>
> `Domain=example.com` session cookie를 `__Host-` host-only cookie로 바꾸려는데 "배포 후 stale auth state가 남지 않게 어떻게 옮기나"가 첫 질문일 때 여는 entrypoint다. duplicate cookie raw header가 이미 잡혔거나 old scope tombstone 설계만 남았다면 [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)으로 바로 내려간다.

> 관련 문서:
> - `[primer bridge]` [Cookie Prefixes Primer: `__Host-` vs `__Secure-`](./cookie-prefixes-host-secure-primer.md)
> - `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
> - `[follow-up primer]` [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)
> - `[primer]` [Subdomain Logout Cookie Cleanup Primer](./subdomain-logout-cookie-cleanup-primer.md)
> - `[follow-up primer]` [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md)
> - `[primer bridge]` [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)
> - `[primer]` [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)
> - `[primer]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
> - `[primer]` [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
> - `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: __host- cookie migration primer, __host cookie migration, host-only cookie migration primer, shared-domain session to __host cookie, domain example.com to __host, parent-domain cookie to host-only cookie, host-prefixed session migration, __host session stale auth state, __host cookie logout cleanup, __host cookie cutover, __host cookie duplicate shadowing, shared cookie to app-local session, host-only session migration beginner, cookie migration without stale auth, __host prefix beginner
retrieval-anchor-keywords: __Host- cookie no Domain Path=/ Secure, __Host cookie cannot be shared across subdomains, __Host cookie handoff pattern, shared-domain cookie retirement, parent-domain cookie tombstone, stale shared session after host-only migration, logout old shared cookie survives, __Host migration safe rollout, __Host cookie devtools checklist

## 먼저 이 문서가 맞는지 15초 분기

| 지금 막힌 질문 | 이 문서가 맞는 경우 | 더 가까운 문서 |
|---|---|---|
| "`__Host-session`으로 바꾸면 subdomain 공유는 어떻게 끊지?" | shared-domain session을 host-local 구조로 **어떻게 옮길지**가 핵심일 때 | 이 문서 계속 읽기 |
| "logout 했는데 다른 subdomain은 왜 아직 로그인 같지?" | migration 자체보다 **logout tail 정리**가 먼저일 때는 아님 | [Subdomain Logout Cookie Cleanup Primer](./subdomain-logout-cookie-cleanup-primer.md) |
| "old cookie를 exact `Domain`/`Path`로 어떻게 지우지?" | 설계보다 **tombstone matrix**가 남았을 때는 아님 | [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md) |
| "raw `Cookie` header에 같은 이름이 두 번 보여" | 구조 전환보다 **중복 전송 원인**을 먼저 좁혀야 할 때는 아님 | [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md) |

짧은 규칙:

- 이 문서는 `__Host-` prefix 규칙 그 자체보다 **shared cookie 모델을 host-only 모델로 바꾸는 큰 그림**을 잡는 entrypoint다.
- cleanup 설계나 logout semantics가 이미 더 구체적으로 보이면 위 follow-up 문서로 바로 내려가는 편이 빠르다.

## 먼저 잡을 mental model

`__Host-`는 이름 decoration이 아니라 **scope contract**다.

브라우저가 supporting browser라면 `__Host-`로 시작하는 cookie에 아래 제약을 기대한다.

- `Secure`가 있어야 한다
- `Path=/`여야 한다
- `Domain`이 있으면 안 된다

그래서 `__Host-` cookie는 이런 뜻에 가깝다.

- 이 cookie는 **지금 응답을 준 그 host만** 쓸 수 있다
- sibling subdomain과 공유하는 parent-domain session 용도가 아니다
- 같은 host 안에서는 path shadowing을 줄이기 쉽다

초보자용 기억 문장:

- `Domain=example.com` session은 "건물 전체 출입증"
- `__Host-session`은 "이 방 호스트 전용 출입증"

즉 migration은 "보안 속성 하나 추가"가 아니라 **공유 구조를 host-local 구조로 바꾸는 일**이다.

---

## 제일 먼저 갈라야 할 질문

| 질문 | `예`면 뜻하는 것 | 먼저 잡을 방향 |
|---|---|---|
| `auth.example.com` login 후 `app.example.com`도 같은 cookie를 바로 읽어야 하나 | 아직 shared-domain session 모델에 기대고 있다 | `__Host-`로 바로 치환하지 말고 handoff/app-local session 설계를 먼저 본다 |
| 각 subdomain이 자기 session을 따로 가져도 되나 | host-only cookie 구조로 갈 수 있다 | 이 문서의 migration 패턴을 따라간다 |
| old `Domain=example.com` cookie가 이미 여러 route에서 보이나 | stale cookie tail이 남아 있을 가능성이 높다 | cleanup inventory와 tombstone 계획을 먼저 만든다 |

핵심 한 줄:

- **cross-subdomain 공유가 필요하면 `__Host-` 하나로 대체할 수 없다**

그 경우는 보통 아래 둘 중 하나다.

1. shared cookie를 계속 쓴다
2. `auth`에서 one-time handoff를 보내고, `app`이 자기 `__Host-` session을 따로 만든다

---

## 왜 stale auth state가 남기 쉬운가

shared-domain session에서 host-only session으로 갈 때 초보자가 자주 놓치는 건 "새 cookie 발급"과 "old auth state 종료"가 별개라는 점이다.

| 배포 후 보이는 장면 | 실제 뜻 | 왜 생기나 |
|---|---|---|
| `app.example.com`은 새 로그인처럼 보이는데 `auth.example.com/logout`만 꼬임 | old shared cookie가 아직 어떤 host에서 읽힌다 | old `Domain=example.com` cookie를 안 지웠다 |
| `app`은 새 `__Host-` cookie를 쓰는데 특정 요청 header에 old `session`도 같이 보인다 | cookie cutover가 반쯤만 끝났다 | 새 이름 추가만 하고 old cookie tombstone을 안 보냈다 |
| 로그아웃했는데 다른 subdomain에서는 잠깐 계속 로그인처럼 보인다 | 브라우저 cookie와 server session invalidation 중 하나만 끝났다 | browser cleanup과 server-side session revoke를 함께 안 했다 |

여기서 중요한 점은 두 가지다.

- old shared-domain cookie는 새 `__Host-` cookie가 생겨도 자동으로 사라지지 않는다
- host가 나뉘면 새 host-local session이 생겼다고 다른 host의 old state까지 자동 종료되지 않는다

---

## beginner-safe migration 패턴은 보통 두 가지다

| 패턴 | 언제 적합한가 | 왜 beginner-safe인가 |
|---|---|---|
| 새 이름으로 병행 발급 후 old cookie retire | 한 host에서 새 `__Host-` cookie를 먼저 안착시킬 수 있다 | old/new 역할을 구분하기 쉬워 duplicate confusion을 줄인다 |
| one-time handoff 후 각 host가 자기 `__Host-` cookie 생성 | subdomain마다 local session이 자연스럽다 | "cookie 공유" 대신 "로그인 완료 전달"로 사고할 수 있다 |

반대로 beginner가 피하면 좋은 패턴은 이렇다.

- old shared cookie 이름을 그대로 유지한 채 `Domain`만 빼고 in-place 교체
- 어떤 host가 어떤 session을 읽는지 정리하지 않은 채 dual-read 기간을 길게 끄는 방식

이 둘은 stale auth state와 duplicate shadowing을 만들기 쉽다.

---

## 패턴 1: 새 이름으로 병행 발급 후 old cookie retire

가장 안전한 시작은 **이름까지 바꾸는 것**이다.

예를 들어 old cookie가 이렇다고 하자.

```http
Set-Cookie: session=old123; Domain=example.com; Path=/; HttpOnly; Secure; SameSite=Lax
```

새 구조에서는 `app.example.com`이 자기 host-local session을 이렇게 만든다.

```http
Set-Cookie: __Host-session=app999; Path=/; HttpOnly; Secure; SameSite=Lax
```

여기서 좋은 점은 명확하다.

- old cookie 이름은 `session`
- new cookie 이름은 `__Host-session`

즉 DevTools와 raw header에서 **누가 old이고 누가 new인지 바로 보인다.**

### rollout 순서

1. 현재 브라우저에 남을 수 있는 old shared cookie 이름과 scope를 inventory한다.
2. 서버는 한동안 `__Host-session`을 우선 읽고, old `session`은 migration fallback으로만 읽는다.
3. login 성공, session refresh, logout 응답에서 new `__Host-session`을 발급한다.
4. 같은 응답에서 old `session; Domain=example.com; Path=/` tombstone을 같이 보낸다.
5. 관측상 old cookie 전송이 사라지면 old fallback read를 제거한다.

### 왜 "새 이름"이 도움이 되나

| 같은 이름 in-place 교체 | 새 이름 병행 |
|---|---|
| header를 봐도 old/new 구분이 어렵다 | 이름만 보고 old/new를 구분할 수 있다 |
| duplicate cookie shadowing이 숨어들기 쉽다 | migration 기간의 역할 구분이 쉽다 |
| rollback 때 무엇을 지워야 하는지 헷갈린다 | tombstone 대상이 분명하다 |

초보자용 기억 문장:

- **scope migration 때는 이름까지 분리하면 디버깅 난도가 크게 낮아진다**

---

## 패턴 2: one-time handoff 후 각 host가 자기 `__Host-` cookie 생성

`auth.example.com`과 `app.example.com`이 둘 다 계속 로그인 상태를 가져야 하지만, shared parent-domain cookie는 없애고 싶다면 보통 handoff 모델이 더 자연스럽다.

흐름은 이렇게 본다.

```text
external IdP -> auth.example.com/callback -> app.example.com/login/complete -> app가 __Host-session 생성
```

이 패턴에서 중요한 점:

- `auth.example.com`의 `__Host-auth_session`은 `app.example.com`에 직접 가지 않는다
- 대신 `auth`가 "로그인 완료 사실"을 one-time artifact로 넘긴다
- `app`은 그 artifact를 한 번 소모하고 자기 `__Host-session`을 만든다

예시:

```http
Set-Cookie: __Host-auth_session=auth777; Path=/; HttpOnly; Secure; SameSite=Lax
Location: https://app.example.com/login/complete?handoff=abc123
```

그리고 `app.example.com`이:

```http
Set-Cookie: __Host-session=app999; Path=/; HttpOnly; Secure; SameSite=Lax
```

이렇게 만들면 각 host가 자기 host-only session만 들고 가므로 shared-domain stale cookie tail을 줄이기 쉽다.

이 모델이 맞는지부터 헷갈리면 [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)와 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)를 먼저 본다.

---

## old shared-domain cookie cleanup은 별도 작업이다

새 `__Host-` cookie를 발급해도 old shared-domain cookie는 자동 삭제되지 않는다.

old cookie가 이거였다면:

```http
Set-Cookie: session=old123; Domain=example.com; Path=/; HttpOnly; Secure; SameSite=Lax
```

cleanup은 old scope를 정확히 맞춰 따로 보내야 한다.

```http
Set-Cookie: session=; Domain=example.com; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Secure; SameSite=Lax
```

초보자가 자주 놓치는 점:

- `__Host-session` 발급과 `session` tombstone은 서로 다른 작업이다
- old cookie가 여러 `Path`나 이름으로 남아 있으면 tombstone도 여러 개 필요할 수 있다

정확한 cleanup matrix가 필요하면 [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)로 내려간다.

---

## logout도 "새 cookie 삭제 + old server state 종료"를 같이 봐야 한다

`__Host-` migration에서 logout tail이 남는 이유는 브라우저 cookie만 지우거나, 반대로 server session만 끊고 브라우저 old cookie를 남기는 식으로 반쪽 정리를 하기 쉽기 때문이다.

| logout에서 해야 할 일 | 왜 필요한가 |
|---|---|
| 현재 host의 `__Host-...` cookie tombstone | 현재 브라우저 host-local 로그인 상태를 끝낸다 |
| old shared-domain cookie tombstone | 브라우저가 예전 session id를 다시 보내지 않게 한다 |
| server-side old session invalidation 또는 version bump | 브라우저 정리가 늦어도 old auth state가 재사용되지 않게 한다 |

초보자용 이해:

- 브라우저 출입증을 회수하고
- 서버 출입 기록도 닫아야 한다

둘 중 하나만 하면 stale auth state가 남을 수 있다.

---

## 바로 써먹는 migration checklist

| 순서 | 확인 질문 | 기대하는 답 |
|---|---|---|
| 1 | 이 서비스는 아직 sibling subdomain shared cookie가 꼭 필요한가 | 아니오, 또는 handoff로 바꿀 수 있다 |
| 2 | 새 cookie 이름을 old와 분리했는가 | 예, `__Host-session`처럼 명확히 분리 |
| 3 | 새 cookie가 `Secure`, `Path=/`, `Domain` 없음 규칙을 만족하는가 | 예 |
| 4 | old shared cookie tombstone을 old scope 그대로 보냈는가 | 예 |
| 5 | logout에서 browser cleanup과 server invalidation을 같이 했는가 | 예 |
| 6 | raw `Cookie` header에서 old shared cookie가 사라졌는가 | 예 |

---

## DevTools에서 무엇을 확인하나

| 어디서 보나 | 확인할 질문 |
|---|---|
| login/refresh/logout 응답의 `Set-Cookie` | 새 `__Host-...` cookie와 old shared-cookie tombstone이 같이 내려왔나 |
| `Application > Cookies` | 현재 host 아래에 `__Host-...`만 남고 old shared cookie row는 사라졌나 |
| 실패했던 요청의 raw `Cookie` header | old `session=...`이 아직 따라오지 않나 |

여기서 자주 보이는 신호:

- `__Host-session`은 생겼는데 old `session`도 같이 보임 -> cleanup 미완료
- `auth` cookie는 있는데 `app` 첫 요청은 anonymous -> handoff/app-local session 경계 확인
- `Secure` cookie인데 특정 환경에서만 안 남음 -> [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)

---

## common confusion

### 1. "`__Host-`면 더 안전한 shared-domain cookie 아닌가요?"

아니다.

- `__Host-`는 `Domain`을 쓸 수 없으므로 shared-domain 용도가 아니다
- host-only cookie로 생각해야 한다

### 2. "old 이름 그대로 `__Host-` 규칙만 맞추면 되죠?"

보통 초보자에게는 더 헷갈린다.

- 이름까지 바꾸면 migration 관측과 cleanup이 쉬워진다
- 같은 이름 in-place 교체는 duplicate tail을 숨기기 쉽다

### 3. "`app`에서 새 `__Host-session`을 만들었으니 `auth` old session도 끝났겠죠?"

아니다.

- host-local 로그인 상태와 old shared-domain 상태는 별개일 수 있다
- logout/revoke/cleanup을 별도로 설계해야 한다

### 4. "parent-domain cookie 하나만 tombstone 보내면 모든 host stale state가 끝나나요?"

브라우저 old cookie 정리에는 도움이 되지만, server-side old session invalidation까지 자동으로 대신하진 않는다.

---

## 다음 단계와 복귀 경로

- old cookie 정리 header를 exact scope로 어떻게 보내야 할지 막히면 [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)
- 이미 raw `Cookie` header에 old/new가 같이 보이면 [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md)
- `auth -> app` 구조 자체를 shared cookie로 볼지 handoff로 볼지 헷갈리면 [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)
- `Application`에는 보이는데 요청에 안 붙는다면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)

복귀 기준:

- cookie cleanup이나 handoff 한 칸을 본 뒤에는 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아와 지금 남은 증상을 다시 고른다.
- subdomain callback 흐름과 session handoff를 다시 넓게 붙이고 싶으면 [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)에서 beginner 사다리로 복귀한다.

## 한 줄 정리

`__Host-` cookie는 "더 안전한 shared-domain cookie"가 아니라 **한 host에만 묶인 host-only cookie**다. 그래서 migration 핵심은 prefix를 붙이는 것보다, old shared-domain session을 어떻게 끊고 각 host의 새 로그인 상태를 어떻게 만들지 분리하는 데 있다.
