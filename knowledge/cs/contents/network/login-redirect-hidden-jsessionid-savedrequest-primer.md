# Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문

> 한 줄 요약: 브라우저 로그인 흐름에서는 `302 Location`, `Set-Cookie: JSESSIONID`, 원래 URL을 기억하는 `SavedRequest`가 한 묶음으로 보이기 쉽고, 초보자가 말하는 `hidden session`은 대개 "cookie는 보이는데 서버가 auth/session을 아직 못 복원하는 상태"를 가리킨다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)
> - [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
> - [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)
> - [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)
> - [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
> - [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)

retrieval-anchor-keywords: login redirect primer, browser login redirect, 302 login flow, browser 401 302 /login bounce, 302 Found Location Set-Cookie, Set-Cookie on redirect response, hidden session, hidden JSESSIONID, hidden session beginner bridge, hidden JSESSIONID next step, why JSESSIONID before login, JSESSIONID after login, HttpOnly JSESSIONID, cookie exists but session missing, cookie 있는데 다시 로그인, cookie 있는데 다시 로그인 primer, cookie 있는데 다시 로그인 beginner route, SavedRequest beginner bridge, SavedRequest original URL memory, saved request bounce, saved request bounce primer, saved request bounce beginner route, saved request bounce entry route, post-login redirect original URL, original URL after login, request cache beginner route, login loop primer, login loop first step, login loop beginner entrypoint, next request anonymous after login, 401 302 bounce starter, browser page redirect vs api 401, login redirect spring security bridge

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

### 먼저 세 표현을 분리한다

| 자주 하는 말 | beginner mental model | 이 문서 다음 안전한 한 걸음 |
|---|---|---|
| `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login` | browser에는 cookie/session reference가 보이지만 서버는 아직 또는 더 이상 auth/session 상태를 못 찾는 장면을 뭉뚱그려 부르는 말인 경우가 많다 | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) |
| `browser 401 -> 302 /login bounce`, `API가 login HTML을 받음` | raw `401` auth failure가 browser redirect UX로 감싸진 장면일 수 있다 | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) |
| `SavedRequest`, `saved request bounce`, `원래 URL 복귀` | 로그인 상태가 아니라 로그인 전 원래 URL을 기억하는 navigation memory다 | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) |

### Retrieval Anchors

- `login redirect primer`
- `302 login flow`
- `hidden JSESSIONID`
- `SavedRequest beginner bridge`
- `saved request bounce`
- `post-login redirect original URL`
- `cookie 있는데 다시 로그인`

---

## 먼저 10초 판별표

| 지금 보이는 현상 | 먼저 이렇게 읽는다 | 다음 확인 포인트 |
|---|---|---|
| 보호 페이지 요청 직후 `302 Location: /login` | 브라우저용 로그인 UX일 수 있다 | page 요청인지 API 요청인지 |
| `302` 응답에 `Set-Cookie: JSESSIONID=...`가 있다 | redirect 응답에서도 browser는 cookie를 저장할 수 있다 | login 전 임시 session인지 |
| 로그인 직후 원래 URL로 다시 `302` 된다 | `SavedRequest`가 원래 URL 복귀를 시도하는 장면일 수 있다 | 그 다음 요청이 `200`인지 다시 `302`인지 |
| `hidden session`처럼 cookie가 있는데 또 `/login`으로 간다 | cookie 존재와 인증 성립은 다르다 | cookie가 실제 전송됐는지, 서버가 session을 찾았는지 |
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

---

## 다음 문서 라우팅

- `cookie 있는데 다시 로그인`, `saved request bounce` 둘 다 beginner entry route는 이 문서 -> [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)다. route를 다시 고르려면 [Network README: Browser Session Spring Auth](./README.md#network-bridge-browser-session-auth), [Security README: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)로 돌아간다.
- `cookie`, `session`, `JWT` 기본 용어가 아직 흐리면 [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) -> [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) 순으로 먼저 본다.
- `browser 401 -> 302 /login bounce`, `API가 login HTML을 받음`을 사례 중심으로 다시 읽고 싶으면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)로 먼저 간다.
- `SavedRequest`, `saved request bounce`, `browser 401 -> 302 /login bounce`, 원래 URL 복귀 우선순위를 framework 관점에서 보고 싶으면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)를 한 번 거친 뒤 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)로 이어 간다.
- `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login`이 핵심이면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)를 한 번 거친 뒤 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 넘어간다.
- cookie는 보이는데 browser/BFF/session store 경계가 헷갈리면 [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)도 함께 본다.

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
