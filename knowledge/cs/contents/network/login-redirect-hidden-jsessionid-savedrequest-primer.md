# Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문

> 한 줄 요약: 브라우저 로그인 흐름에서는 `302 Location`, `Set-Cookie: JSESSIONID`, 원래 URL을 기억하는 `SavedRequest`가 한 묶음으로 보이기 쉽고, 초보자가 말하는 `hidden session`은 대개 "cookie는 보이는데 서버가 auth/session을 아직 못 복원하는 상태"를 가리킨다.

**난이도: 🟢 Beginner**

관련 문서:
- `[primer]` [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- `[primer]` [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)
- `[primer]` [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- `[primer]` [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)
- `[primer]` [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)
- `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
  - `Application > Cookies`에는 값이 보이는데 같은 실패 요청의 request `Cookie` header가 비면, guide 안의 `Application vs Network 15초 미니 체크`를 먼저 거쳐 `cookie-header gate`를 통과시킨다
- `[primer]` [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)
- `[primer]` [Secure Cookie Behind Proxy Guide](../security/secure-cookie-behind-proxy-guide.md)
- `[rag bridge]` [Cross-Domain Bridge Map](../../rag/cross-domain-bridge-map.md)
- `[deep dive]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md): `Browser / Session Troubleshooting Path`의 redirect/navigation branch를 고른 뒤 들어간다
- `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md): `Browser / Session Troubleshooting Path`의 server persistence branch를 고른 뒤 들어간다
- `[deep dive]` [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)

retrieval-anchor-keywords: login redirect primer, savedrequest beginner bridge, login loop beginner entrypoint, hidden jsessionid, cookie 있는데 다시 로그인, cookie stored but not sent, request cookie header empty, application cookie vs request cookie header, browser 401 302 /login bounce, post-login redirect original url, browser session troubleshooting path, cookie-header gate, 기억 전송 복원 cue, spring deep dive 전 safe next doc, login loop return path

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 10초 판별표](#먼저-10초-판별표)
- [한 번에 보는 브라우저 로그인 redirect 흐름](#한-번에-보는-브라우저-로그인-redirect-흐름)
- [왜 로그인 전에도 `JSESSIONID`가 생기나](#왜-로그인-전에도-jsessionid가-생기나)
- [`SavedRequest`는 무엇이고 무엇이 아닌가](#savedrequest는-무엇이고-무엇이-아닌가)
- [login loop가 생길 때 어디서 끊어 보나](#login-loop가-생길-때-어디서-끊어-보나)
- [page 요청과 API 요청을 분리해서 읽기](#page-요청과-api-요청을-분리해서-읽기)
- [DevTools에서 확인하는 순서](#devtools에서-확인하는-순서)
- [다음 문서 라우팅](#다음-문서-라우팅)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 이 문서가 필요한가

입문자가 browser login 흐름에서 가장 자주 한 덩어리로 묶어 버리는 장면이 있다.

- 보호 페이지에 가니 `302 -> /login`이 뜬다
- 분명 내가 cookie를 직접 넣지 않았는데 `JSESSIONID`가 보인다
- 로그인 직후 다시 원래 URL로 돌아간다
- 그런데 어떤 경우는 다시 `/login`으로 튄다

이때 섞이는 질문은 사실 서로 다르다.

- `302`는 브라우저에게 "다른 URL로 가라"는 navigation 지시다
- `JSESSIONID`는 브라우저가 자동 전송하는 session reference일 수 있다
- `SavedRequest`는 로그인 전 원래 URL을 기억하는 서버 쪽 메모다
- login loop는 위 셋 중 하나가 아니라, 보통 **인증 유지가 안 되거나 page/API 경계가 섞인 결과**다

이 문서는 Spring Security deep dive 전에 browser와 HTTP 관점에서 이 셋을 분리해 두는 primer다.

## 먼저 세 표현을 분리한다

| 자주 하는 말 | beginner mental model | 고정 next-step label | 이 문서 다음 안전한 한 걸음 |
|---|---|---|
| `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login` | browser에는 cookie/session reference가 보이지만 서버는 아직 또는 더 이상 auth/session 상태를 못 찾는 장면을 뭉뚱그려 부르는 말인 경우가 많다 | `server-anonymous` (`복원`, 기존 `server-mapping-missing`) | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) |
| `browser 401 -> 302 /login bounce`, `API가 login HTML을 받음` | raw `401` auth failure가 browser redirect UX로 감싸진 장면일 수 있다 | `browser redirect / API contract` | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) |
| `SavedRequest`, `saved request bounce`, `원래 URL 복귀` | 로그인 상태가 아니라 로그인 전 원래 URL을 기억하는 navigation memory다 | `redirect / navigation memory` | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) |

## 핸드오프 큐: `기억/전송/복원`

`login loop`와 `401 -> 302`가 섞일 때는 아래 3칸으로 먼저 분리한다.

| cue | 지금 확인할 질문 | 안전한 다음 문서 |
|---|---|---|
| `기억` | 로그인 전 원래 URL(`SavedRequest`)을 서버가 기억하고 있나? | 이 문서의 redirect 흐름을 먼저 읽고 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)로 넘어간다 |
| `전송` | 브라우저가 다음 요청의 `Cookie` header에 session reference를 실제로 실었나? | request `Cookie` header가 비면 먼저 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md#application-vs-network-15초-미니-체크)의 `cookie-header gate`에서 `stored` vs `sent`를 고정하고, 그다음 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)로 간다 |
| `복원` | 서버가 받은 cookie reference로 auth/session을 복원했나? | cookie가 실렸는데도 익명이면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)에서 `server-anonymous` 갈래로 넘긴다 |

## Spring deep dive 전에 고정할 safe next doc

이 문서는 Spring deep dive 전에 보는 primer다.
초보자 기준 safe next doc은 먼저 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)다.

## Spring deep dive 전에 고정할 safe next doc (계속 2)

| 지금 막힌 말 | 먼저 고정할 safe next doc | 그다음 문서 |
|---|---|---|
| `SavedRequest`, `saved request bounce`, `원래 URL 복귀` | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)에서 `redirect / navigation memory` branch를 고른다 | [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) |
| `cookie 있는데 다시 로그인`, `hidden session`, `next request anonymous after login` | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)에서 `Application` cookie와 request `Cookie` header를 먼저 가른다 | request `Cookie` header가 비면 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md), 실리면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) |
| `API가 login HTML을 받음`, `browser 401 -> 302 /login bounce` | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)에서 page redirect와 API contract를 먼저 분리한다 | redirect memory면 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md), session persistence면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) |

## Retrieval Anchors

- `login redirect primer`
- `302 login flow`
- `hidden jsessionid`
- `savedrequest beginner bridge`
- `saved request bounce`
- `post-login redirect original URL`
- `cookie 있는데 다시 로그인`
- `application cookie vs request cookie header`

---

## 먼저 10초 판별표

| 지금 보이는 현상 | 먼저 이렇게 읽는다 | 다음 확인 포인트 |
|---|---|---|
| 보호 페이지 요청 직후 `302 Location: /login` | 브라우저용 로그인 UX일 수 있다 | page 요청인지 API 요청인지 |
| `302` 응답에 `Set-Cookie: JSESSIONID=...`가 있다 | redirect 응답에서도 browser는 cookie를 저장할 수 있다 | login 전 임시 session인지 |
| 로그인 직후 원래 URL로 다시 `302` 된다 | `SavedRequest`가 원래 URL 복귀를 시도하는 장면일 수 있다 | 그 다음 요청이 `200`인지 다시 `302`인지 |
| `hidden session`처럼 cookie가 있는데 또 `/login`으로 간다 | cookie 존재와 인증 성립은 다르다 | cookie가 실제 전송됐는지, 서버가 session을 찾았는지 |
| `Application > Cookies`에는 값이 있는데 다음 request `Cookie` header가 비어 있다 | `SavedRequest`보다 먼저 browser cookie 전송/범위 문제를 의심한다 | 먼저 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md#application-vs-network-15초-미니-체크)의 `cookie-header gate`로 가서 `stored` vs `sent`를 고정한 뒤 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md) |
| `fetch('/api/...')`가 JSON `401` 대신 login HTML을 받는다 | browser page redirect 정책이 API 계약에 섞였을 가능성이 크다 | page 체인과 API 체인을 분리했는지 |

초보자용 핵심 규칙은 이것이다.

- `302`는 종종 인증 실패를 browser UX로 감싸는 겉모습이다.
- `JSESSIONID`는 종종 인증 상태 그 자체가 아니라 서버가 찾는 reference다.
- `SavedRequest`는 종종 로그인 후 어디로 돌아갈지 정하는 navigation memory다.

---

## 한 번에 보는 브라우저 로그인 redirect 흐름

전형적인 page navigation 흐름을 HTTP 모양으로 줄이면 아래와 같다.

```http
GET /orders/42 HTTP/1.1
Host: app.example.com

HTTP/1.1 302 Found
Location: /login
Set-Cookie: JSESSIONID=abc123; Path=/; HttpOnly; Secure; SameSite=Lax
```

브라우저는 이 응답 본문을 보여 주지 않아도 두 가지를 할 수 있다.

1. `Location: /login`을 따라간다
2. `Set-Cookie`를 저장한다

즉 redirect 응답도 cookie 저장에 참여한다.

그 다음은 보통 이렇게 이어진다.

```http
GET /login HTTP/1.1
Host: app.example.com
Cookie: JSESSIONID=abc123

HTTP/1.1 200 OK
Content-Type: text/html
```

로그인 폼 제출은 같은 session reference를 들고 갈 수 있다.

```http
POST /login HTTP/1.1
Host: app.example.com
Cookie: JSESSIONID=abc123
Content-Type: application/x-www-form-urlencoded

username=neo&password=secret
```

인증 성공 후에는 원래 URL 복귀를 위해 다시 redirect가 올 수 있다.

```http
HTTP/1.1 302 Found
Location: /orders/42
Set-Cookie: JSESSIONID=def456; Path=/; HttpOnly; Secure; SameSite=Lax
```

여기서 `JSESSIONID`가 바뀌어도 이상하지 않다.
로그인 성공 시 session fixation 방어 때문에 id를 교체할 수 있기 때문이다.
중요한 것은 "바뀌었는가" 자체보다, **마지막 보호 URL 요청에 올바른 cookie가 실려서 서버가 인증 상태를 복원했는가**다.

마지막 요청은 대개 이렇게 끝난다.

```http
GET /orders/42 HTTP/1.1
Host: app.example.com
Cookie: JSESSIONID=def456

HTTP/1.1 200 OK
Content-Type: text/html
```

이 흐름을 한 줄로 읽으면 이렇다.

- 첫 `302`: 인증 안 된 page request를 login UX로 전환
- middle `JSESSIONID`: 로그인 전후 navigation memory와 session continuity를 이어 주는 reference
- login 후 `302`: 원래 URL 복귀
- 마지막 `200`: 이제 서버가 session/security state를 복원한 결과

---

## 왜 로그인 전에도 `JSESSIONID`가 생기나

초보자가 가장 놀라는 지점이 바로 이것이다.

`아직 로그인도 안 했는데 왜 JSESSIONID가 생기지?`

가장 단순한 답은 이렇다.

- 브라우저 로그인 UX는 로그인 전에도 상태를 잠깐 기억해야 할 수 있다
- 그 상태를 서버가 session에 보관하면 browser에는 session id가 먼저 보일 수 있다

즉 `JSESSIONID`가 보인다고 곧바로 아래를 뜻하지는 않는다.

- 로그인 성공
- 사용자 principal이 이미 확정됨
- 권한 검사가 이미 통과됨

오히려 login 전 `JSESSIONID`는 자주 아래 같은 용도일 수 있다.

- 원래 가려던 URL 기억
- 로그인 폼과 그 주변 browser flow 유지
- CSRF token이나 기타 server-side state 연결

또 `HttpOnly`가 켜져 있으면 자바스크립트 `document.cookie`에서는 안 보일 수 있다.
그래도 browser는 요청에 자동으로 붙여 보낸다.

그래서 "hidden `JSESSIONID`"는 보통 두 뜻이 섞여 있다.

- 내가 JS 코드로 넣지 않았는데 browser가 몰래 보내는 것처럼 보인다
- 개발자도구 Storage/Network에는 보이는데 JS에서는 안 보인다

둘 다 이상 동작이라기보다 browser cookie/session 모델의 정상 결과일 수 있다.

---

## `SavedRequest`는 무엇이고 무엇이 아닌가

`SavedRequest`를 아주 낮은 난이도로 줄이면:

- 로그인 전 원래 요청을 기억하는 서버 쪽 메모

브라우저가 보는 것은 보통 이것뿐이다.

- 보호 URL 요청
- login page redirect
- login 성공 후 원래 URL redirect

브라우저는 `SavedRequest` 객체 자체를 보지 않는다.
브라우저가 체감하는 것은 **"왜 로그인 후 저 URL로 다시 가지?"** 라는 결과뿐이다.

중요한 구분:

- `SavedRequest`는 로그인 상태 자체가 아니다
- `SavedRequest`는 browser cache가 아니다
- `SavedRequest`는 프론트엔드 JS 변수도 아니다
- `SavedRequest`는 보통 session과 연결된 navigation memory다

즉 아래 둘은 다른 질문이다.

- `SavedRequest`가 남아 있는가
- 로그인 후 session/security state가 제대로 살아 있는가

그래서 login loop는 자주 이런 모양이 된다.

1. 보호 URL이 저장된다
2. 로그인은 성공한다
3. 원래 URL로 되돌아간다
4. 그런데 다음 요청에서 인증 상태를 복원하지 못한다
5. 다시 `/login`으로 간다

이때 loop를 만드는 핵심 원인은 `SavedRequest` 자체보다 그 뒤쪽 persistence 실패인 경우가 많다.

여기서 초보자가 먼저 확인해야 하는 질문은 하나 더 있다.

- `Application > Cookies`에는 session cookie가 보여도, 같은 실패 요청의 request `Cookie` header에도 실제로 실렸는가?

이 한 칸이 비어 있으면 아직 `server session bug`가 아니라 **`stored` vs `sent`를 다시 가르는 cookie-scope 갈래**다.
즉 `SavedRequest`/login loop entrypoint에서도 먼저 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md#application-vs-network-15초-미니-체크)의 `cookie-header gate`로 가서 `Application` 저장과 request 전송을 분리한 뒤, request `Cookie` header가 비면 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)로 내려가는 것이 안전하다.

---

## login loop가 생길 때 어디서 끊어 보나

loop를 보면 초보자는 자주 "redirect가 문제다"로만 읽는다.
실제로는 아래 순서로 끊어 보면 더 빠르다.

### 1. 첫 `302`는 정상 browser UX인가

- 보호된 HTML page로 들어간 것이라면 자연스러울 수 있다
- API endpoint인데도 같은 흐름이면 경계가 섞였을 가능성이 크다

### 2. redirect 응답의 `Set-Cookie`가 실제로 저장됐는가

- redirect 응답이라도 cookie는 저장될 수 있다
- `Secure`, `Domain`, `Path`, `SameSite` 때문에 저장/전송이 달라질 수 있다

### 3. login POST와 최종 복귀 요청에 cookie가 실제로 실렸는가

- browser Storage에 보이는 것과 request header에 실제로 실리는 것은 별개다
- subdomain, path, cross-origin fetch, `SameSite` 때문에 최종 요청에서 빠질 수 있다

### 4. cookie가 실렸는데도 다시 익명인가

이 경우는 browser보다 서버 쪽 질문에 가깝다.

- session이 만료됐는가
- session store에서 해당 id를 못 찾는가
- login 후 새 session id로 바뀌었는데 이전 값을 보고 있는가
- post-login persistence와 request cache/session 정책이 엇갈렸는가

즉 login loop는 보통 아래 셋 중 하나다.

- browser가 cookie를 못 싣는 문제
- 서버가 session을 못 찾는 문제
- page redirect 정책이 API 경계에 섞인 문제

---

## page 요청과 API 요청을 분리해서 읽기

같은 `302 /login`이라도 page와 API는 기대 계약이 다르다.

| 요청 종류 | 기대 계약 | 흔한 이상 징후 |
|---|---|---|
| 브라우저 page navigation | `302 -> /login` 후 로그인 화면 이동 가능 | 원래 URL 복귀 실패, login loop |
| XHR / `fetch` / REST API | 보통 raw `401`/`403` JSON | login HTML 수신, redirect 따라가다 의미 상실 |

그래서 먼저 이 질문을 던지면 좋다.

1. 지금 요청은 주소창 이동인가, API 호출인가?
2. `302`는 UX 전환으로 읽어야 하나, API 계약 오염으로 읽어야 하나?
3. `SavedRequest`가 필요한 브라우저 page flow인가?

이 구분이 서면 `302`, hidden `JSESSIONID`, `SavedRequest`가 같은 문제처럼 보이지 않는다.

---

## DevTools에서 확인하는 순서

Network 탭과 Application 탭에서 아래 순서대로 보면 대부분 풀린다.

1. 첫 응답이 raw `401`인지 `302 Location: /login`인지 본다.
2. 그 `302` 응답에 `Set-Cookie: JSESSIONID=...`가 있는지 본다.
3. browser가 따라간 다음 요청의 Request Headers에 `Cookie: JSESSIONID=...`가 실제로 실렸는지 본다.
4. login 성공 응답이 다시 `302`를 주는지, `Location`이 원래 URL인지 본다.
5. login 성공 직후 `JSESSIONID`가 그대로인지 바뀌는지 본다.
6. 최종 보호 URL 요청이 `200`으로 끝나는지, 다시 `302 -> /login`으로 되돌아가는지 본다.
7. API 호출이라면 최종 응답 `Content-Type`이 JSON인지 HTML login page인지 확인한다.

초보자에게 특히 중요한 한 줄:

- "Application 탭에 cookie가 보인다"보다 "해당 요청 Header에 cookie가 실제로 실렸다"가 더 결정적이다.
- `Application`에는 보이는데 request `Cookie` header가 비면, 이 문서에서는 더 파지 말고 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md#application-vs-network-15초-미니-체크)의 `cookie-header gate`로 바로 넘긴다.

## `cookie는 있는데 안 실린다` 빠른 branch

이 문서에서 가장 자주 놓치는 갈래는 이것이다.

- `Application > Cookies`에는 값이 보인다
- 그런데 다음 request `Cookie` header는 비어 있다
- 그래서 `SavedRequest`나 server session부터 의심해 버린다

초보자용 안전 분기는 먼저 **전송 실패**와 **서버 복원 실패**를 나누는 것이다.

| 지금 보이는 것 | 먼저 이렇게 읽는다 | 안전한 다음 문서 |
|---|---|---|
| cookie는 보이는데 다음 request `Cookie` header가 비어 있고, subdomain/path 이동 뒤에 특히 잘 깨진다 | browser가 그 요청에는 cookie를 안 붙인 것이다 | 먼저 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md#application-vs-network-15초-미니-체크)의 `cookie-header gate`로 `stored` vs `sent`를 고정한 뒤 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md) |
| cookie는 보이는데 login 직후 redirect `Location`이나 다음 요청 URL이 `http://...`로 내려가고, proxy/LB 뒤에서만 재현된다 | `Secure` cookie와 proxy scheme 전달이 어긋난 것이다 | [Secure Cookie Behind Proxy Guide](../security/secure-cookie-behind-proxy-guide.md) |
| request `Cookie` header는 실제로 실리는데 서버가 계속 anonymous로 본다 | 이제 browser 전송보다 server session/BFF lookup 쪽이 더 가깝다 | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) -> [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) |

---

## 다음 문서 라우팅

- `cookie 있는데 다시 로그인`, `saved request bounce`, `API가 login HTML을 받음`은 이 문서에서 각각 고정 label을 먼저 붙인다: `server-anonymous`(`복원`, 기존 `server-mapping-missing`), `redirect / navigation memory`, `browser redirect / API contract`. `hidden session mismatch`는 여기서 원인명이 아니라 묶음 alias로만 읽고, request `Cookie` header가 비면 먼저 `cookie-missing`(기존 `cookie-not-sent`)으로 다시 자른다. 그다음 beginner entry route는 이 문서 -> [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)다. route를 다시 고르려면 [Network README: Browser Session Spring Auth](./README.md#network-bridge-browser-session-auth), [Security README: Browser / Session Beginner Ladder](../security/README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)로 돌아간다.
- 다음 갈래를 다시 고를 때는 먼저 [Security README: Browser / Session Beginner Ladder](../security/README.md#browser--session-beginner-ladder)로 돌아가 초보자 branch 이름을 다시 맞춘다. 더 넓은 symptom 표가 필요할 때만 [Security README: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)로 한 칸 더 내려간다. 질문이 network/security/spring 경계를 같이 건드리면 [RAG: Cross-Domain Bridge Map](../../rag/cross-domain-bridge-map.md)로 한 칸만 올라간다.

## 기초 용어로 되돌아가기

- `cookie`, `session`, `JWT` 기본 용어가 아직 흐리면 [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) -> [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) 순으로 먼저 본다.
- `browser 401 -> 302 /login bounce`, `API가 login HTML을 받음`을 사례 중심으로 다시 읽고 싶으면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)로 먼저 간다.
- Spring deep dive로 바로 내려가기보다, beginner symptom route는 [Security README: Browser / Session Beginner Ladder](../security/README.md#browser--session-beginner-ladder)로 한 번 돌아와 branch 이름을 다시 고르고 필요할 때만 [Security README: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)로 넓히는 편이 안전하다.

## redirect memory deep dive 전

- `SavedRequest`, `saved request bounce`, `browser 401 -> 302 /login bounce`, 원래 URL 복귀 우선순위를 framework 관점에서 보고 싶으면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)를 한 번 거친 뒤 [Security README: Browser / Session Beginner Ladder](../security/README.md#browser--session-beginner-ladder)로 돌아와 redirect/navigation memory branch를 다시 고르고, 그다음 [Security README: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)에서 symptom 표를 넓힌 뒤 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)로 내려간다.
- `SavedRequest`나 `hidden session`으로 보이더라도 `Application > Cookies`에는 값이 있는데 request `Cookie` header가 비면 redirect/server persistence 문서로 곧바로 내려가지 않는다. 먼저 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md#application-vs-network-15초-미니-체크)의 `cookie-header gate`에서 `stored` vs `sent`를 고정하고, request `Cookie` header가 비면 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md), route를 다시 고르려면 [Security README: Browser / Session Beginner Ladder](../security/README.md#browser--session-beginner-ladder)로 돌아온다.

## cookie 전송 분기

- `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login`이 핵심인데 `Application > Cookies`에는 값이 보여도 request `Cookie` header가 비면 먼저 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md#application-vs-network-15초-미니-체크)의 `cookie-header gate`로 `stored` vs `sent`를 고정한다. 거기서도 `request Cookie header empty`면 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)로 간다. redirect `Location`이나 다음 요청 URL이 `http://...`로 꺾이거나 proxy/LB 뒤에서만 재현되면 [Secure Cookie Behind Proxy Guide](../security/secure-cookie-behind-proxy-guide.md)로 간다.

## server 복원 분기

- `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login`이 핵심이고 request `Cookie` header는 실제로 실리는데 서버가 계속 anonymous라면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)를 한 번 거친 뒤 [Security README: Browser / Session Beginner Ladder](../security/README.md#browser--session-beginner-ladder)에서 `server-anonymous` branch를 다시 고르고, 필요할 때만 [Security README: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)에서 server persistence symptom 표를 넓힌 다음 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 넘어간다.

## browser/BFF 경계로 넘길 때

- cookie는 보이는데 browser/BFF/session store 경계가 헷갈리면 [Security README: Browser / Session Beginner Ladder](../security/README.md#browser--session-beginner-ladder)에서 server session/BFF mapping branch를 다시 고른 뒤 [Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path), [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)도 함께 본다.

---

## 면접에서 자주 나오는 질문

### Q. `302` 응답에도 cookie가 저장될 수 있나요?

- 그렇다. browser는 redirect 응답의 `Set-Cookie`도 저장할 수 있고, 이어지는 요청에 그 cookie를 자동 전송할 수 있다.

### Q. 로그인 전 `JSESSIONID`가 생기면 이미 로그인된 것 아닌가요?

- 아니다. login 전에도 원래 URL 기억, CSRF, 기타 server-side state 연결 때문에 session id가 먼저 생길 수 있다.

### Q. `SavedRequest`는 무엇을 저장하나요?

- 보통 "로그인 전 원래 가려던 요청"에 대한 server-side navigation memory다. 로그인 상태 그 자체와는 다르다.

### Q. cookie가 있는데 왜 다시 `/login`으로 갈 수 있나요?

- cookie 존재만으로 인증이 성립하지 않기 때문이다. 해당 cookie가 실제 요청에 실렸는지, 서버가 그 session/token mapping을 찾았는지가 더 중요하다.

### Q. API도 `302 /login`으로 보내면 안 되나요?

- 브라우저 page UX에는 자연스러울 수 있지만, API 계약에서는 보통 raw `401`/`403`이 더 선명하다. API가 login HTML을 받기 시작하면 boundary가 섞였다는 신호일 수 있다.

## 한 줄 정리

- `SavedRequest`는 원래 URL 기억이고, `Application > Cookies` 저장과 request `Cookie` header 전송은 별개다. login loop에서 cookie가 저장돼 보여도 request `Cookie` header가 비면 먼저 `stored` vs `sent`를 가르는 cookie-scope branch로 가고, 그다음에만 server session 복원을 의심한다.
