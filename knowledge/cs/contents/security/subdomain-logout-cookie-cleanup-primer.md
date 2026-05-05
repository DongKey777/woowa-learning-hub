# Subdomain Logout Cookie Cleanup Primer

> 한 줄 요약: `Domain=example.com` shared cookie 구조에서 app-local session handoff 구조로 옮길 때 logout은 "지금 app session 삭제"만으로 끝나지 않는다. **현재 host의 새 session 종료 + 옛 parent-domain cookie tombstone + 서버 쪽 old session 무효화**를 같이 봐야 stale login tail을 줄일 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)

> 문서 역할: `primer`
>
> 팀이 subdomain 간 shared parent-domain cookie를 줄이고, `auth.example.com -> app.example.com` handoff 뒤 각 app이 자기 session을 갖는 구조로 옮길 때 "logout 후 왜 다른 subdomain에서는 아직 로그인처럼 보이나"를 처음 설명하는 entrypoint다.

> 관련 문서:
> - `[primer]` [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)
> - `[primer]` [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)
> - `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
> - `[follow-up primer]` [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)
> - `[follow-up primer]` [__Host- Cookie Migration Primer](./host-cookie-migration-primer.md)
> - `[follow-up primer]` [OAuth Login State Cookie Cleanup](./oauth-login-state-cookie-cleanup.md)
> - `[advanced]` [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)
> - `[primer]` [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
> - `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: subdomain logout cookie cleanup primer, parent-domain cookie logout cleanup, shared cookie to app-local session logout, auth.example.com logout app.example.com still logged in, subdomain logout stale cookie, logout tombstone cleanup beginner, app-local session handoff logout, shared session retirement logout, logout old domain example.com cookie, host-only session plus shared cookie cleanup, logout after cookie scope migration, subdomain cookie tombstone primer, app local session logout old shared cookie survives, logout one-time handoff model, logout migration beginner
retrieval-anchor-keywords: __Host-session logout old shared cookie, app_session logout shared session cleanup, sibling subdomain logout confusion, why logout from one subdomain does not log out another, logout browser cookie cleanup vs server session revoke

## 먼저 이 문서가 맞는지 15초 분기

| 지금 막힌 질문 | 이 문서가 맞는 경우 | 더 가까운 문서 |
|---|---|---|
| "`app.example.com`에서 logout했는데 다른 subdomain은 왜 계속 로그인 같지?" | 현재 host session 종료와 old shared cookie tail을 **같이** 정리해야 할 때 | 이 문서 계속 읽기 |
| "`__Host-`로 옮길 구조 자체를 어떻게 설계하지?" | logout보다 **migration 방향**이 먼저 안 잡혔을 때는 아님 | [__Host- Cookie Migration Primer](./host-cookie-migration-primer.md) |
| "old cookie를 어느 `Domain`/`Path` 조합으로 tombstone 해야 하지?" | logout 의미는 정해졌고 **exact scope cleanup**만 남았을 때는 아님 | [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md) |
| "이건 제품군 전체 로그아웃 정책인가, OIDC back-channel까지 포함한 얘기인가?" | 브라우저 cookie tail보다 **전역 logout semantics**가 핵심이면 아님 | [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md) |

짧은 규칙:

- 이 문서는 "한 subdomain logout이 왜 다른 subdomain 상태를 자동으로 끊지 못하는가"를 설명하는 primer다.
- tombstone header 한 줄의 문법보다 logout 범위와 tail 정리가 먼저 헷갈릴 때 여는 문서다.

## 먼저 잡는 mental model

subdomain 구조 변경 뒤 logout은 보통 출입증이 두 종류라서 헷갈린다.

- 예전 출입증: `Domain=example.com` shared cookie
- 새 출입증: `app.example.com`이 자기 host에서만 쓰는 app-local session cookie

핵심은 이것이다.

- 새 구조로 로그인했다고 옛 shared cookie가 자동으로 없어지지 않는다
- 한 app에서 logout했다고 sibling subdomain의 old cookie가 자동으로 정리되지도 않는다
- 브라우저 정리와 서버 session 종료도 같은 작업이 아니다

초보자용 기억 문장:

- **logout은 "지금 세션 종료"와 "옛 세션 흔적 청소"를 같이 보는 일이다**

---

## 왜 이 문서를 먼저 여나

팀이 이런 전환을 할 때 초보자가 가장 자주 보는 장면은 이렇다.

- `auth.example.com`은 handoff만 하고, `app.example.com`이 `__Host-session`이나 `app_session`을 만든다
- `app.example.com/logout`을 눌렀더니 현재 app에서는 로그아웃된 것처럼 보인다
- 그런데 `admin.example.com`이나 다시 돌아간 `auth.example.com`에서는 아직 로그인처럼 보인다
- DevTools에는 new host-local cookie는 지워졌는데 old `Domain=example.com` cookie row가 남아 있다

이때 자주 생기는 오해:

- "logout endpoint가 현재 app session cookie를 지웠으니 전체가 끝났겠지"

실제로는 아래 셋을 분리해야 한다.

1. 현재 app host의 새 session cookie를 지웠는가
2. 예전에 쓰던 shared parent-domain cookie를 tombstone으로 지웠는가
3. 서버 쪽 old session id나 refresh 계열도 더 못 쓰게 막았는가

---

## 20초 판별표

| 지금 보이는 현상 | 보통 뜻하는 것 | 먼저 할 일 |
|---|---|---|
| `app.example.com/logout` 뒤 현재 탭만 익명이고 다른 subdomain은 계속 로그인 | app-local logout만 됐고 old shared cookie나 다른 host session이 남아 있다 | old `Domain=example.com` cookie 존재 여부 확인 |
| DevTools에 `__Host-session`은 사라졌는데 `session` row가 그대로 남아 있다 | 새 구조 cookie 삭제와 old cookie cleanup이 분리돼 있다 | old cookie scope에 맞는 tombstone 추가 |
| old cookie는 지웠는데 서버가 여전히 old session id를 받아 준다 | 브라우저 cleanup만 하고 server-side revoke를 안 했다 | old session invalidation 또는 version bump 확인 |
| `auth` logout은 되는데 `app` 재방문 시 handoff로 다시 로그인처럼 보인다 | logout 의미와 handoff 재발급 조건이 분리돼 있다 | logout 뒤 handoff source 세션도 닫는지 확인 |

---

## 구조를 먼저 두 칸으로 나눠 본다

| 구조 | 로그인 때 무슨 일이 일어나나 | logout 때 따로 챙길 것 |
|---|---|---|
| old shared-cookie 모델 | `Domain=example.com` cookie 하나를 여러 subdomain이 같이 읽는다 | 그 shared cookie tombstone과 공용 server session 종료 |
| new app-local handoff 모델 | `auth`는 handoff만 넘기고, `app`이 자기 host-local session을 만든다 | 현재 app session 종료 + old shared cookie cleanup + handoff source session 종료 여부 |

중요한 점:

- 새 구조가 app-local이라고 해서 old shared cookie cleanup이 사라지는 것은 아니다
- migration 기간에는 **둘 다 브라우저에 남아 있을 수 있다**

---

## 가장 흔한 예시

### 예전 구조

```http
Set-Cookie: session=shared123; Domain=example.com; Path=/; HttpOnly; Secure; SameSite=Lax
```

### 새 구조

`auth.example.com`은 callback 후 handoff만 넘긴다.

```http
302 Found
Location: https://app.example.com/login/complete?handoff=abc123
```

`app.example.com`은 자기 session을 만든다.

```http
Set-Cookie: __Host-session=app999; Path=/; HttpOnly; Secure; SameSite=Lax
```

이제 `app.example.com/logout`에서 이것만 보내면 반쪽 logout이 될 수 있다.

```http
Set-Cookie: __Host-session=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Secure; SameSite=Lax
```

왜냐하면 old shared cookie가 브라우저에 아직 남아 있을 수 있기 때문이다.

함께 봐야 하는 cleanup은 보통 이렇다.

```http
Set-Cookie: session=; Domain=example.com; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Secure; SameSite=Lax
```

그리고 서버 쪽에서도 old `shared123` 세션을 더 이상 받아 주지 않아야 한다.

---

## logout을 "브라우저 2개 + 서버 1개"로 보면 덜 헷갈린다

| 축 | 무엇을 끝내나 | 실패하면 보이는 장면 |
|---|---|---|
| 현재 host-local cookie cleanup | 지금 app의 현재 로그인 탭/브라우저 상태 | 현재 app만 로그아웃이 안 됨 |
| old shared cookie cleanup | migration 전 구조의 오래된 브라우저 흔적 | 다른 subdomain에서 다시 로그인처럼 보임 |
| server-side session revoke | 브라우저가 old id를 다시 보내더라도 거절하는 안전장치 | cookie는 지워졌는데 race나 stale client가 여전히 통과 |

초보자용 기억:

- 브라우저 쪽은 "출입증 회수"
- 서버 쪽은 "출입 기록 폐기"

둘 중 하나만 하면 tail이 남을 수 있다.

---

## beginner-safe logout 패턴

### 1. 현재 app session은 지금 host에서 지운다

`__Host-...`나 host-only cookie는 그 host 응답에서 tombstone을 보내야 한다.

예:

```http
Set-Cookie: __Host-session=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Secure; SameSite=Lax
```

핵심:

- `__Host-`라면 `Domain`을 쓰지 않는다
- logout 응답을 준 그 host의 cookie만 정리한다

### 2. old shared cookie는 old scope 그대로 tombstone을 보낸다

예전이 `Domain=example.com; Path=/`였다면 delete도 그대로 맞춘다.

```http
Set-Cookie: session=; Domain=example.com; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Secure; SameSite=Lax
```

중요한 점:

- 새 `__Host-session` logout과 old `session` tombstone은 별도 작업이다
- old cookie가 여러 이름이나 `Path`로 남았으면 tombstone도 여러 개 필요하다

정확한 scope matrix는 [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)로 이어진다.

### 3. handoff source까지 끊을지 의미를 정한다

`auth.example.com`이 여전히 살아 있는 로그인 source라면, app logout 후 곧바로 handoff를 다시 발급해 재로그인처럼 보일 수 있다.

그래서 semantics를 먼저 정한다.

| logout 의미 | 보통 필요한 것 |
|---|---|
| 현재 app만 로그아웃 | app-local session만 종료 |
| 이 제품군 전체 로그아웃 | app-local session + old shared cookie + auth source session까지 종료 |
| 보안 사고 대응 로그아웃 | 위 항목 + refresh family나 device session까지 종료 |

이 분기가 더 커지면 [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)로 넘어간다.

---

## common confusion

### 1. "`app/logout`이 성공했으니 다른 subdomain도 끝났겠지"

아니다.

- 현재 app host에서 만든 cookie만 지웠을 수 있다
- old `Domain=example.com` cookie는 여전히 남아 있을 수 있다

### 2. "new app-local 구조면 old shared cookie는 이미 무의미하니 안 지워도 되겠지"

위험하다.

- 서버 일부가 아직 old cookie를 fallback으로 읽을 수 있다
- 브라우저 raw `Cookie` header에 duplicate name이 남아 shadowing을 만들 수도 있다

### 3. "브라우저에서 cookie를 지웠으니 logout은 다 끝났다"

아니다.

- 서버 쪽 old session id, refresh token family, handoff source session이 남아 있으면 tail이 이어질 수 있다

### 4. "`auth` cookie가 app에 안 가니 logout bug다"

handoff 모델이라면 꼭 bug는 아니다.

- `auth` cookie는 auth host 전용일 수 있다
- 중요한 건 logout 뒤 app가 새 handoff를 다시 자동 발급받는 구조인지다

---

## logout rollout 때 보는 짧은 checklist

1. 브라우저 DevTools에서 current app cookie와 old shared cookie row를 분리해서 본다.
2. logout response가 current app cookie tombstone을 보내는지 확인한다.
3. 같은 흐름이나 인접 흐름에서 old shared cookie tombstone도 보내는지 확인한다.
4. 실패 요청 raw `Cookie` header에서 old cookie name이 사라졌는지 본다.
5. 서버가 old session id를 fallback으로 계속 받아 주지 않는지 확인한다.

---

## 어디로 이어서 읽나

- old cookie scope별 tombstone matrix가 필요하면 [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)로 간다.
- shared parent-domain cookie를 `__Host-`나 host-only 구조로 옮기는 큰 그림이 먼저 필요하면 [__Host- Cookie Migration Primer](./host-cookie-migration-primer.md)를 본다.
- `auth` callback과 `app` handoff 구조 자체가 헷갈리면 [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md), [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)로 돌아간다.
- federated logout, refresh family, session coherence까지 넓어지면 [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)로 내려간다.

## 한 줄 정리

`Domain=example.com` shared cookie 구조에서 app-local session handoff 구조로 옮길 때 logout은 "지금 app session 삭제"만으로 끝나지 않는다. **현재 host의 새 session 종료 + 옛 parent-domain cookie tombstone + 서버 쪽 old session 무효화**를 같이 봐야 stale login tail을 줄일 수 있다.
