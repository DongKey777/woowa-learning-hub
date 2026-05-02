---
schema_version: 2
title: "Cookie Scope Mismatch Guide"
concept_id: "security/cookie-scope-mismatch-guide"
difficulty: beginner
doc_role: deep_dive
level: beginner
aliases:
  - cookie scope mismatch
  - cookie stored not sent
  - Domain Path SameSite mismatch
  - host-only cookie
  - login loop cookie scope
expected_queries:
  - cookie scope mismatch는 어떻게 확인해?
  - Domain Path SameSite가 안 맞아서 cookie가 request에 안 붙는 경우를 어디서 봐?
  - host-only cookie와 subdomain cookie 차이가 login loop에 왜 중요해?
  - Application에 cookie가 저장됐는데 요청에 안 실리면 어떤 범위를 봐?
acceptable_neighbors:
  - contents/security/fetch-credentials-vs-cookie-scope.md
  - contents/security/cookie-failure-three-way-splitter.md
  - contents/security/browser-401-vs-302-login-redirect-guide.md
companion_neighbors:
  - contents/security/secure-cookie-behind-proxy-guide.md
  - contents/security/duplicate-cookie-name-shadowing.md
forbidden_neighbors:
  - contents/security/jwt-deep-dive.md
---

# Cookie Scope Mismatch Guide

> 한 줄 요약: 브라우저에 cookie가 "저장돼 있다"와 현재 요청에 cookie가 "실려 간다"는 다른 문제다. `Domain`, `Path`, `SameSite`, subdomain 범위가 안 맞으면 login 직후에도 다시 `/login`으로 튈 수 있다.

**난이도: 🟢 Beginner**

> 초보자 return box:
> - cross-origin / CORS 혼란에서 들어왔다면 먼저 [Cross-Origin Cookie, `fetch credentials`, CORS 입문](../network/cross-origin-cookie-credentials-cors-primer.md)으로 돌아가 `origin` / `site` / `credentials`를 다시 고정한다.
> - request `Cookie` header가 비는 장면까지 확인했다면 이 문서를 읽고, 다음 분기는 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 복귀한다.

관련 문서:
- [Cross-Origin Cookie, `fetch credentials`, CORS 입문](../network/cross-origin-cookie-credentials-cors-primer.md)
- [Cookie DevTools Field Checklist Primer](./cookie-devtools-field-checklist-primer.md)
- [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
- [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
- [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./wrong-scheme-vs-wrong-origin-redirect-shortcut.md)
- [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)
- [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)
- [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
- [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md)
- [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md)

retrieval-anchor-keywords: cookie scope mismatch, cookie stored not sent, request cookie header missing, host-only cookie, domain path samesite mismatch, application vs network cookie check, login loop cookie scope, fetch credentials cookie scope, callback cookie naming confusion, 왜 callback은 되는데 다음 요청은 anonymous, 처음 배우는데 쿠키가 왜 안 가요, cookie는 있는데 왜 다시 로그인, location header http chooser, next request url becomes http, proxy scheme drift vs cookie scope

## 이 문서를 먼저 읽는 이유

이 문서는 broad 첫 hop이 아니라, [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)에서 `cookie-header gate`를 통과한 뒤 읽는 `cookie-not-sent` deep dive다. 즉 같은 실패 요청 기준으로 `Application` 저장값은 있는데 request `Cookie` header가 비는 장면이 먼저 확인됐을 때만 내려온다.

다만 초보자는 request `Cookie` header가 비는 순간 바로 `Domain`/`Path`/`SameSite`만 파기 쉽다.
여기서 한 번만 더 나누면 덜 헷갈린다.

| request `Cookie` header가 비는 장면 | 먼저 확인할 것 | 지금 바로 갈 문서 | 읽고 난 뒤 복귀 |
|---|---|---|---|
| actual `GET`/`POST`가 아예 없고 `OPTIONS`만 실패한다 | preflight가 actual request를 막았는지 | [Preflight Debug Checklist](./preflight-debug-checklist.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| actual request는 있는데 cross-origin `fetch` 코드가 `credentials: "include"` 없이 나간다 | cookie scope 전에 request option이 빠졌는지 | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) | 이 문서로 돌아와 `Domain`/`Path`/`SameSite`를 계속 본다 |
| actual request도 있고 `credentials: "include"`도 있는데 `Cookie`가 비어 있다 | 그때부터 scope mismatch를 본다 | 이 문서 계속 읽기 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

한 줄 규칙:

- actual request가 없으면 아직 cookie scope 문서로 확정하지 않는다.
- actual request가 있어도 `credentials` handoff를 한 번 거친 뒤에 `Domain`/`Path`/`SameSite`를 본다.
- `Access-Control-Allow-Credentials`는 request에 cookie를 "붙여 주는" 설정이 아니라 응답 읽기 정책이다.

## 거울 chooser: `Location`이나 다음 요청 URL이 `http://...`로 꺾이면

초보자가 가장 많이 헷갈리는 지점은 "request `Cookie`가 비었으니 곧바로 scope mismatch"라고 단정하는 것이다.
하지만 login 직후 `Location`이나 다음 요청 URL이 `http://...`로 내려가면, cookie scope보다 **proxy가 원래 HTTPS 요청을 HTTP로 오해하게 만든 갈래**가 더 먼저다.

| 내가 먼저 본 증거 | cookie scope 본론을 계속 읽나? | 지금 바로 갈 문서 | 읽고 난 뒤 복귀 |
|---|---|---|---|
| login 응답 `Location`이 `http://app.example.com/...`처럼 내려온다 | 아니다 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| redirect 뒤 첫 요청 URL이 `http://...`라서 `Secure` cookie가 안 붙는다 | 아니다 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| `http://...`로 꺾이는지, internal host로 바뀌는지 둘 다 헷갈린다 | 아니다 | [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./wrong-scheme-vs-wrong-origin-redirect-shortcut.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| redirect와 다음 요청 URL은 계속 `https://...`인데 request `Cookie`만 비어 있다 | 그렇다 | 이 문서에서 `Domain` / `Path` / host-only cookie를 계속 본다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

한 줄 규칙:

- `http://...`가 보이면 `Domain`/`Path`보다 먼저 wrong-scheme/proxy branch를 확인한다.
- redirect와 다음 요청 URL이 계속 HTTPS일 때만 cookie scope 본론을 계속 읽는다.

## 왜 "cookie는 있는데 안 간다"가 생기나

초보자가 가장 자주 하는 오해는 이것이다.

- 개발자도구 `Application > Cookies`에 session cookie가 보인다
- 그런데 보호 페이지나 `/api/me`는 계속 익명처럼 본다
- 그래서 "서버가 쿠키를 무시하나?"라고 생각한다

실제로는 서버까지 가기 전에, **브라우저가 그 요청에 cookie를 붙이지 않았을 수 있다.**

브라우저는 매 요청마다 대략 이렇게 판단한다.

1. 이 요청 host가 cookie `Domain` 범위 안에 있나?
2. 이 요청 URL path가 cookie `Path` 범위 안에 있나?
3. 이 요청이 cookie `SameSite` 정책에 맞나?
4. 지금 내가 보고 있는 cookie가 정확히 어느 subdomain에 저장된 건가?

즉 `cookie exists`와 `cookie sent`는 다른 단계다.

---

## Application vs Network first check

속성 이름을 외우기 전에, 실패한 요청 하나만 잡고 두 화면만 비교한다.

> 체크 순서:
> `Application > Cookies`는 "브라우저가 저장했는가"
> `Network > 실패한 요청 > Request Headers > Cookie`는 "그 요청에 실제로 보냈는가"

정확히 어떤 칸을 열어야 할지 헷갈리면 [Cookie DevTools Field Checklist Primer](./cookie-devtools-field-checklist-primer.md)에서 `Name` / `Domain` / `Path` / `SameSite` / `Secure` / `HttpOnly` / `Expires`와 `Request URL`을 어떤 순서로 비교하는지 먼저 보고 오면 된다.

초보자용 10초 checklist:

1. login 직후 다시 튕긴 "바로 그 요청"을 `Network`에서 고른다.
2. `Application > Cookies`에서 cookie가 보이는지 본다.
3. 같은 요청의 request `Cookie` header가 비었는지 바로 확인한다.
4. request `Cookie` header가 비면 이 문서에서 `Domain`/`Path`/`SameSite`/subdomain 범위를 읽고, header가 있으면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)로 이동한다.

| `Application` | `Network` | 초보자용 첫 결론 | 다음 문서 |
|---|---|---|---|
| cookie가 안 보임 | request `Cookie`도 없음 | 저장 단계부터 실패했을 수 있다 | [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) |
| cookie가 보임 | request `Cookie`가 비어 있음 | transport/scope 문제를 먼저 본다 | 이 문서 계속 읽기 |
| cookie가 보임 | request `Cookie`도 있음 | cookie scope보다 server/session mapping 쪽이 더 가깝다 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |

핵심 mental model 한 줄:

- `Application`은 "보관함"
- `Network`는 "출입 기록"

보관함에 출입증이 있어도, 그 문을 통과한 기록이 없으면 아직 서버 문제로 넘어갈 단계가 아니다.

여기서 request `Cookie`가 비어 있더라도 바로 `SameSite`만 의심하지는 않는다.
먼저 "actual request가 있었는가 -> cross-origin이면 `credentials: \"include\"`가 있었는가 -> 그다음에 scope가 맞는가" 순서로 한 칸씩 내려간다.

## 어디로 돌아갈지 먼저 고정

다음 갈래를 다시 고를 때는:

- [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md)
- [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)
- [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)
- network/security/spring 경계가 같이 섞이면 [RAG: Cross-Domain Bridge Map](../../rag/cross-domain-bridge-map.md)

---

## 먼저 10초 판별표

이 표는 [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md)의 3갈래 용어를 맞춘 버전이다. 이 문서는 `stored but not sent`만 자세히 푼다.

| 지금 보이는 현상 | 3-way 분기 용어 | 먼저 볼 것 |
|---|---|---|
| login 응답 뒤 cookie는 생겼는데 다음 요청에 다시 `/login` | `stored but not sent` | Network 탭의 실제 `Cookie` 헤더 |
| `Application`에는 `auth.example.com`의 `session`이 보이는데 요청은 `app.example.com/api/me`로 나간다 | `stored but not sent` | `auth.example.com`(저장 host), `app.example.com`(요청 host), `Domain` 값부터 1줄 비교 |
| cookie가 `auth.example.com` 아래에는 보이는데 `app.example.com`에서 안 먹음 | `stored but not sent` | cookie의 `Domain`과 저장된 host |
| `Application`에는 `auth.example.com` cookie가 보이는데 `app.example.com/api/me` 요청 `Cookie`가 비어 있음 | `stored but not sent` | 저장 host, 요청 host, `Domain`(없음/`example.com`)을 한 줄로 비교 |
| `/auth/callback` 직후에는 괜찮아 보이는데 `/api/me`에서 튕김 | `stored but not sent` | cookie `Path`와 실제 요청 path. 이름 혼동이면 먼저 [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md) |
| 외부 사이트/iframe/embedded flow에서만 로그인 루프 | `stored but not sent` | 요청이 same-site인지 cross-site인지 |

---

## callback 이름 혼동 신호

아래 둘이 같이 보이면 scope 표를 더 파기 전에 [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md)로 먼저 우회한다.

- callback에서 잠깐 쓰는 cookie와 app session cookie가 같은 이름처럼 보인다
- `auth.example.com/callback`은 성공했는데 `app.example.com` 첫 요청이 anonymous다

## 비슷해 보여도 다른 갈래

아래 장면은 이 문서의 `stored but not sent` 본론으로 바로 내려가기보다 detour를 먼저 타는 편이 안전하다.

| 지금 보이는 장면 | 이 문서의 본론인가? | 먼저 갈 문서 |
|---|---|---|
| raw `Cookie` header에 `session=...; session=...`처럼 같은 이름이 두 번 보임 | 아니다. 중복 이름 shadowing detour다 | [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md) |
| cookie 헤더는 실제로 실리는데도 계속 익명처럼 보임 | 아니다. `sent but anonymous` 갈래다 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| response `Set-Cookie`가 막히거나 `Application`에 cookie가 아예 안 보임 | 아니다. 저장 단계 detour다 | [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) |

detour를 끝내면 다시 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아와 같은 symptom anchor에서 다음 칸을 고른다.

---

## detour에서 복귀하는 return to Browser / Session Troubleshooting Path

cookie scope detour에서 원인을 확인했다면, side path를 더 파기 전에 아래 사다리로 같은 자리로 복귀한다.
초보자 return path wording은 항상 `return to Browser / Session Troubleshooting Path`이고, 실제 복귀 순서는 [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)다.

| 단계 | 왜 이 단계로 복귀하나 | 링크 |
|---|---|---|
| 1. `primer` | login redirect와 `SavedRequest`가 어떤 기억을 남기는지 다시 고정 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| 2. `primer bridge` | `401`/`302`, login HTML fallback, cookie 누락 증상을 한 표로 다시 분기 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| 3. `catalog` | 다음 symptom 갈래를 category navigator에서 다시 선택 | [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

---

## 서버 버그 의심 전에 30초 교차검증

아래 두 줄을 **같은 실패 요청 기준으로** 나란히 본다.

| 비교 대상 | 확인 질문 | 바로 내릴 결론 |
|---|---|---|
| `Application > Cookies` 저장값 | cookie가 브라우저 저장소에 있나? | "저장" 증거일 뿐, 전송 증거는 아님 |
| `Network`의 request `Cookie` header | 그 실패 요청에 cookie가 실제로 실렸나? | 이 줄이 비면 먼저 cookie scope 문제를 본다 |

초보자용 판단 규칙:

- `Application`에는 있는데 request `Cookie` header가 없으면, 서버 session 버그로 단정하지 않는다.
- request `Cookie` header까지 확인된 뒤에만 server session/BFF mapping 문제로 내려간다.

---

## 가장 중요한 mental model

cookie를 "열쇠"보다 "출입증"으로 생각하면 쉽다.

- 브라우저는 출입증을 서랍에 저장할 수 있다
- 하지만 모든 문에 그 출입증을 보여 주지는 않는다
- 문마다 허용 범위가 다르면, 저장된 출입증이 있어도 못 들어간다

여기서 문을 여는 조건이 `Domain`, `Path`, `SameSite`다.

| 질문 | 보는 속성 | 틀리면 보이는 증상 |
|---|---|---|
| 이 host에 보내도 되나? | `Domain` 또는 host-only 여부 | subdomain 하나에서만 login이 유지됨 |
| 이 URL path에 보내도 되나? | `Path` | login callback 뒤 다른 page/API에서 풀림 |
| 이 요청 맥락에서 보내도 되나? | `SameSite` | 외부 사이트/iframe/fetch에서만 풀림 |
| 내가 보고 있는 cookie가 어디 저장된 거지? | 저장된 subdomain | cookie는 보이는데 다른 subdomain 요청에는 안 실림 |

핵심 한 줄:

- `Application` 탭은 "저장 여부"
- `Network` 탭의 request header는 "전송 여부"

login loop를 볼 때는 항상 "보관"보다 "전송"을 먼저 확인한다.

---

## 한 장면으로 보는 "cookie는 있는데 login loop"

아래는 초보자가 가장 많이 겪는 흐름이다.

| 단계 | 브라우저에서 보이는 것 | 실제 의미 |
|---|---|---|
| 1. login 응답 | `Set-Cookie: session=abc123; Path=/; HttpOnly; Secure` | 서버는 cookie를 저장하라고 했다 |
| 2. `Application > Cookies` | `auth.example.com` 아래에 `session=abc123`가 보인다 | cookie가 **auth host 기준으로 저장**됐다 |
| 3. 다음 이동 | 브라우저가 `https://app.example.com/dashboard`로 이동한다 | 이제 요청 host가 바뀌었다 |
| 4. 실패한 요청 | request `Cookie` header가 비어 있다 | 저장은 됐지만 **이 요청에는 안 붙었다** |
| 5. 서버 응답 | `302 -> /login` 또는 `/api/me`가 익명 응답 | 서버는 session cookie를 보지 못했다 |

겉으로 보면 "방금 cookie가 생겼는데 왜 또 로그인하지?"처럼 보이지만,
실제 원인은 대개 이 중 하나다.

- host가 달라져 `Domain` 범위를 벗어났다
- path가 달라져 `Path` 범위를 벗어났다
- 요청 맥락이 cross-site라 `SameSite`에 막혔다

즉 login loop는 종종 "cookie가 없다"가 아니라 **그 요청에 붙는 cookie가 없다**는 뜻이다.

---

## `Domain`과 subdomain mismatch

### 1. `Domain`이 없으면 host-only cookie다

서버가 이렇게 보냈다고 하자.

```http
Set-Cookie: session=abc123; Path=/; HttpOnly; Secure
```

여기서 `Domain`이 빠져 있으면, 브라우저는 보통 **현재 응답을 준 정확한 host에만** cookie를 붙인다.

예를 들어 login이 `https://auth.example.com/login`에서 끝났다면:

- `auth.example.com` 요청에는 cookie를 보낼 수 있다
- `app.example.com` 요청에는 보내지 않는다
- `api.example.com` 요청에도 보내지 않는다

그래서 "cookie는 분명 생겼는데 앱에서 다시 로그인 화면으로 간다"가 생긴다.

### 2. subdomain mismatch는 대개 `SameSite`보다 `Domain` 문제다

초보자는 자주 이렇게 생각한다.

- `auth.example.com`과 `app.example.com`이 다르다
- 그러니 `SameSite`가 막았겠지

하지만 이 둘은 **different origin**일 수 있어도, 보통은 **same-site**다.
즉 sibling subdomain 문제는 먼저 `Domain` 또는 host-only cookie를 의심하는 편이 맞다.

### 3. 가장 흔한 예시

| login이 끝난 곳 | 이후 요청이 가는 곳 | cookie 설정 | 결과 |
|---|---|---|---|
| `auth.example.com` | `auth.example.com/me` | `Domain` 없음 | 동작할 수 있다 |
| `auth.example.com` | `app.example.com/me` | `Domain` 없음 | cookie가 안 실려 login loop |
| `auth.example.com` | `app.example.com/me` | `Domain=example.com` | subdomain 간 공유 가능 |

실무에서는 "cookie가 보인다"보다 "어느 host 아래에 보이느냐"가 더 중요하다.

---

## `Path` mismatch

브라우저는 cookie `Path`와 요청 URL path를 비교해서, prefix가 맞는 경우에만 cookie를 붙인다.

예를 들어:

```http
Set-Cookie: session=abc123; Path=/auth; HttpOnly; Secure
```

이 cookie는 대략 다음처럼 동작한다.

| 요청 URL | cookie 전송 여부 |
|---|---|
| `/auth/callback` | 전송됨 |
| `/auth/me` | 전송됨 |
| `/api/me` | 전송 안 됨 |
| `/dashboard` | 전송 안 됨 |

그래서 이런 증상이 나온다.

1. login callback은 성공한 것처럼 보인다
2. 직후 `/api/me` 또는 `/dashboard`로 이동한다
3. 해당 요청에는 cookie가 안 실린다
4. 서버는 익명으로 보고 다시 `/login`으로 보낸다

초보자 눈에는 "방금 로그인했는데 왜 또 풀리지?"처럼 보이지만, 실제로는 **callback path에서만 유효한 cookie**였던 것이다.

### callback 이름 혼동이면 `Path`보다 역할 분리부터 본다

아래 두 문장을 같은 뜻으로 읽고 있다면 scope 표를 더 파기 전에 문서 갈래를 바꾼다.

- callback에서 잠깐 쓰는 cookie와 app session cookie가 **같은 이름처럼 보인다**
- `auth.example.com/callback`은 성공했는데 `app.example.com` 첫 요청이 anonymous다

이때는 "`Path`가 좁아서 안 갔나?"를 바로 묻기보다, 먼저 [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md)에서 **callback 확인용 cookie인지, 이후 요청의 main session cookie인지** 역할을 가른다. 역할을 나눈 뒤:

- callback에서만 실패하면 [SameSite Login Callback Primer](./samesite-login-callback-primer.md)
- `auth -> app` handoff 뒤 첫 요청이 anonymous면 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)
- 다시 broad triage로 돌아가려면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

---

## `SameSite` mismatch

`SameSite`는 "이 cookie를 cross-site 요청에도 보낼지"를 정한다.
여기서 중요한 점은 `SameSite`가 **host**가 아니라 **site**를 본다는 것이다.

짧게 보면:

| 값 | 의미 | beginner 감각 |
|---|---|---|
| `Strict` | cross-site 맥락에 거의 안 보냄 | 가장 보수적, 외부 진입/임베드에 잘 깨짐 |
| `Lax` | top-level 이동 같은 일부 흐름만 허용 | 일반 웹앱 기본값으로 자주 본다 |
| `None; Secure` | cross-site에도 보냄 | 외부 연동, iframe, cross-site flow에 필요할 수 있다 |

### 흔한 오해: subdomain이 다르면 무조건 `SameSite` 문제인가?

아니다.

`app.example.com`과 `api.example.com`은:

- same-origin은 아님
- 하지만 보통 same-site다

반면 `app.example.com`과 `login.partner.net`은 cross-site다.

| 비교 대상 | same-origin? | same-site? | 먼저 의심할 것 |
|---|---|---|---|
| `app.example.com` vs `api.example.com` | 아니오 | 예 | `Domain`, CORS, credential 설정 |
| `auth.example.com` vs `app.example.com` | 아니오 | 예 | host-only cookie, `Domain` |
| `app.example.com` vs `login.partner.net` | 아니오 | 아니오 | `SameSite`, external redirect/iframe |

### `SameSite` 때문에 login loop가 잘 보이는 장면

- 외부 portal 안 iframe으로 앱을 열었다
- 다른 site에서 `fetch`/XHR로 app API를 부른다
- external IdP나 partner site를 경유한 뒤 특정 요청에서만 세션이 안 붙는다

이때는 cookie가 저장돼 있어도, 브라우저가 "이건 cross-site 맥락이니 안 보낸다"라고 판단할 수 있다.
redirect와 다음 요청 URL이 계속 `https://...`인데 external IdP/iframe 경로에서만 이 장면이 보이면 [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)에서 `SameSite=None; Secure` 문제와 proxy `X-Forwarded-Proto` mismatch를 먼저 분리하면 된다. 반대로 login 직후 `Location`이 `http://...`로 바뀌면 이 문서보다 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)가 더 가깝다.

---

## `Domain` / `Path` / `SameSite`를 한 표로 비교

| 무엇이 안 맞나 | cookie는 어디엔가 보이나? | 어느 순간 빠지나 | 초보자용 기억 문장 |
|---|---|---|---|
| `Domain` | 보일 수 있다 | 다른 host나 sibling subdomain 요청 | "저장된 host가 다르면 못 간다" |
| `Path` | 보일 수 있다 | callback 밖 다른 URL path | "cookie는 자기 path prefix 밖으로 안 간다" |
| `SameSite` | 보일 수 있다 | iframe, external redirect 뒤 요청, cross-site fetch | "site 맥락이 다르면 브라우저가 막을 수 있다" |

이 표의 핵심은 단순하다.

- 세 경우 모두 `Application` 탭에는 cookie가 보일 수 있다
- 하지만 실패는 항상 **다음 request header에서** 드러난다

체크를 하나 끝낼 때마다 다음 문서를 새로 찾기보다, 같은 symptom 자리로 다시 붙는 편이 덜 헷갈린다.

| 방금 확인한 것 | 초보자용 다음 한 걸음 | 같은 자리 복귀 |
|---|---|---|
| `Domain` | 저장 host와 request host를 한 줄로 다시 적어 본다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| `Path` | callback path와 실제 API/page path를 한 줄로 다시 적어 본다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| `SameSite` | same-site인지 cross-site인지 먼저 한 줄로 다시 적어 본다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

---

## DevTools에서 딱 세 군데만 비교한다

초보자는 `Application` 탭만 보고 끝내기 쉽다.
실제로는 아래 세 칸을 순서대로 비교해야 원인이 보인다.

| 어디서 보나 | 확인할 질문 | 예시 |
|---|---|---|
| login 응답의 `Set-Cookie` | 서버가 어떤 범위로 저장하라고 했나? | `Domain`, `Path`, `SameSite`가 무엇인가 |
| `Application > Cookies` | 브라우저가 어느 host 아래 저장했나? | `auth.example.com` 아래에만 보이나 |
| 실패한 다음 요청의 `Cookie` header | 그 cookie가 실제로 전송됐나? | `Cookie: session=abc123`가 있나 없나 |

이 세 칸을 나란히 보면 분리가 쉽다.

- `Set-Cookie`는 있었는데 저장이 안 됐다면 저장 단계 문제다
- 저장은 됐는데 next request `Cookie` header가 없으면 scope 문제다
- `Cookie` header도 있었는데 계속 익명처럼 보이면 서버 session/BFF mapping 문제다

---

## 가장 많이 헷갈리는 조합

### 1. "cookie는 있는데 session이 없다"

이 문장은 둘 중 하나다.

- 실제로 request에 cookie가 안 실렸다
- cookie는 실렸지만 서버 session/BFF mapping이 사라졌다

초보자는 이 둘을 자주 섞는다.
먼저 `Network` 탭에서 `Cookie` request header를 보고, 거기에도 없으면 browser scope 문제다.

### 2. "CORS를 열었는데 왜 cookie가 안 가지?"

CORS와 cookie scope는 다른 문제다.

- CORS: 브라우저가 응답을 읽어도 되는가
- cookie scope: 브라우저가 cookie를 붙여도 되는가

즉 CORS가 맞아도 `Domain`, `Path`, `SameSite`가 틀리면 cookie는 안 갈 수 있다.
여기에 `fetch` 요청 옵션까지 섞이면 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)에서 `credentials: "include"`, `Access-Control-Allow-Credentials`, cookie scope를 세 칸으로 먼저 나누면 된다.

### 3. "cookie가 auth 서브도메인에 보이는데 앱은 왜 익명이지?"

이건 `SameSite`보다 먼저 host-only cookie를 의심한다.
특히 login 전용 host와 app host를 나눠 둔 구조에서 자주 나온다.

### 4. "같은 이름 cookie가 두 개 보이는데 어느 쪽이 진짜지?"

이건 단순 scope mismatch보다 한 단계 더 좁은 문제일 수 있다.

- 같은 이름 cookie가 서로 다른 `Domain`/`Path`로 같이 남아 있을 수 있다
- 특정 route에서만 old session이 shadowing하며 login loop를 만들 수 있다

이 경우는 [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md)에서 `Path`/`Domain`별 중복 이름 cookie가 왜 헷갈리는지 따로 분리해 보면 좋다.
배포 중 scope를 `/app -> /`나 host-only -> shared domain으로 옮긴 직후라면 [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)에서 old scope별 expired `Set-Cookie`를 정확히 어떻게 보내야 하는지까지 이어서 보면 된다.

---

## 실전 확인 순서

1. login 응답 하나를 고르고 `Set-Cookie`에서 `Domain`, `Path`, `SameSite`를 먼저 적어 둔다.
2. `Application > Cookies`에서 cookie가 어느 host 아래 저장됐는지 본다.
3. 같은 실패 요청 하나를 고르고 `Network` 탭에서 request `Cookie` header가 실제로 있었는지 본다.
4. request host와 cookie `Domain`이 맞는지 본다.
5. request path와 cookie `Path`가 맞는지 본다.
6. 그 요청이 same-site인지 cross-site인지 보고 `SameSite`를 비교한다.
7. `Application` 저장값과 request `Cookie` header를 비교해 "저장됨 vs 전송됨"을 분리한다.
8. cookie가 실제로 실렸는데도 익명처럼 보이면 그때 서버 session/BFF mapping 문제로 넘어간다.

이 순서로 보면 "cookie는 있는데 왜 또 로그인하지?"를 브라우저 범위 문제와 서버 상태 문제로 분리할 수 있다.

---

## 다음 단계

- `Domain` / `Path` / `SameSite` 중 하나를 확인하고 나면 같은 symptom anchor로 바로 복귀한다: [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path).
- login-loop 맥락을 다시 넓혀 잡아야 하면 복귀 사다리를 탄다: [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) -> [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path).
- `302 -> /login`, `SavedRequest`, login HTML fallback이 같이 보이면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)로 이어 가면 된다.
- callback cookie 이름이 같아 보여서 "이게 callback용인지 app session용인지"부터 흔들리면 [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md)로 한 칸 올라간 뒤, 같은 anchor인 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 복귀한다.
- cookie/session/JWT 자체가 아직 섞여 보이면 [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)부터 다시 맞춘다.
- cross-site credential, `fetch`, preflight까지 같이 얽히면 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)로 먼저 분리한 뒤 [CORS, SameSite, Preflight](./cors-samesite-preflight.md)로 내려간다.

## 다음 단계 (계속 2)

- cookie는 실제로 실리는데 server-side에서만 세션이 끊기면 [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)을 본다.

## 한 줄 정리

login loop에서 중요한 질문은 "cookie가 보이느냐"가 아니라 "이 요청의 host/path/site 조건에서 그 cookie가 실제로 전송되느냐"다. `Domain`, `Path`, `SameSite`, subdomain 범위를 먼저 분리하면 원인을 훨씬 빨리 좁힐 수 있다.
