# Browser `401` vs `302` Login Redirect Guide

> 한 줄 요약: 브라우저 앱에서 보이는 `302 -> /login`은 종종 raw `401`을 브라우저 UX로 감싼 `browser 401 -> 302 /login bounce`이고, 초보자가 말하는 `hidden session`은 대개 cookie reference는 보이지만 서버가 auth/session을 못 복원하는 장면을 뜻한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)
> - [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
> - [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
> - [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
> - [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)
> - [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md)
> - [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: browser 401 vs 302, login redirect guide, raw 401 vs 302 redirect, browser 401 302 /login bounce, browser login redirect instead of 401, 401 302 bounce beginner, login loop beginner guide, login loop beginner entrypoint, saved request example, SavedRequest original URL memory, saved request bounce, saved request bounce beginner route, savedrequest symptom splitter, redirect memory vs missing cookie, saved request vs cookie not sent, savedrequest vs session missing, request cache example, session cookie example, hidden session, hidden JSESSIONID, JSESSIONID login redirect, cookie exists but session missing, cookie 있는데 다시 로그인, cookie 있는데 다시 로그인 beginner route, browser gets html login page, fetch gets login page instead of 401, api returns 302 login, browser auth redirect primer, browser session cookie redirect, oauth login redirect vs api 401, security readme browser session troubleshooting, login redirect primer first, beginner auth entry route, secure cookie behind proxy, proxy cookie primer, login redirect becomes http, x-forwarded-proto login loop, X-Forwarded-Host redirect, post-login redirect wrong origin, Location header wrong host, proxy cookie return path, browser session troubleshooting return path

## 이 문서 다음에 보면 좋은 문서

- `cookie 있는데 다시 로그인`, `saved request bounce`, `hidden session`, `browser 401 -> 302 /login bounce`가 같이 보이면 beginner entry route는 같다. 먼저 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)으로 alias를 맞춘 뒤 이 문서로 돌아온다.
- raw `401`, `403`, concealment `404` 의미 자체가 헷갈리면 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)로 먼저 내려가 상태 코드 의미를 고정하는 편이 안전하다.
- `Application > Cookies`에는 cookie가 보이는데 다음 request `Cookie` header가 비어 있거나, `auth`/`app`/`api` subdomain 이동 뒤 login loop가 나면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)에서 `Domain`, `Path`, `SameSite`, host-only cookie 문제를 먼저 분리한다.
- login 응답 직후 `Location`이 `http://...`로 바뀌거나, `localhost`에서는 되는데 ALB/Nginx/ingress 뒤에서만 `Secure` cookie가 빠지면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)에서 TLS termination, `X-Forwarded-Proto`, app의 proxy header 신뢰를 먼저 본다.
- login 응답 직후 `Location`이나 OAuth `redirect_uri`가 `app-internal`, `localhost`, staging host처럼 wrong origin으로 바뀌면 [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)에서 `X-Forwarded-Host`, host preservation, absolute URL builder를 먼저 본다.
- cross-origin `fetch`에서 `credentials: "include"`와 CORS credential 헤더, cookie scope가 한꺼번에 섞이면 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)에서 request 전송과 response 읽기를 먼저 나눠 본다.
- `cookie`, `session`, `JWT`가 아직 한 덩어리처럼 보이면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md) -> [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md) 순으로 올라가 상태 저장 위치부터 다시 맞춘다.
- `SavedRequest`, `saved request bounce`, `원래 URL 복귀`가 더 깊게 궁금하면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)을 한 번 거친 뒤 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)로 이어 간다.
- `hidden session`, `cookie exists but session missing`이 더 궁금하면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)을 한 번 거친 뒤 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md), [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md) 순으로 좁힌다.
- route를 다시 고르려면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아가고, beginner entry route 전체를 다시 타려면 [Network README: Browser Session Spring Auth](../network/README.md#network-bridge-browser-session-auth)로 돌아간다.

---

## 먼저 세 표현을 분리한다

| 자주 하는 말 | 먼저 이렇게 읽는다 | 안전한 다음 문서 |
|---|---|---|
| `browser 401 -> 302 /login bounce`, `API가 login HTML을 받음` | raw `401` auth failure가 browser redirect UX로 감싸진 장면일 수 있다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인` | browser에는 cookie/session reference가 보이지만 서버는 그 값으로 auth/session을 아직 또는 더 이상 못 찾는 장면일 수 있다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| `SavedRequest`, `saved request bounce`, `원래 URL 복귀` | 로그인 상태가 아니라 로그인 전 원래 URL을 기억하는 navigation memory다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |

`SavedRequest`가 보인다고 바로 Spring `RequestCache` 설정부터 볼 필요는 없다.
먼저 "원래 URL을 기억한 문제"인지, "로그인 뒤 인증 상태가 유지되지 않는 문제"인지 나눈다.

| 지금 보이는 증상 | 더 가까운 축 | 첫 확인 | 안전한 다음 문서 |
|---|---|---|---|
| 로그인 후 원래 URL로 한 번 돌아가고 `200`으로 끝남 | 정상 redirect memory | `POST /login` 다음 `Location`과 최종 status | 더 깊게 필요할 때만 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) |
| 로그인 후 원래 URL로 갔다가 곧바로 다시 `/login` | `SavedRequest`는 동작했지만 auth persistence가 깨졌을 수 있음 | 원래 URL 재요청에 `Cookie` header가 실렸는지 | cookie가 비면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), cookie가 실리면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) |
| `Application > Cookies`에는 보이지만 request `Cookie` header가 비어 있음 | missing-cookie / scope 문제 | `Domain`, `Path`, `SameSite`, `Secure`, subdomain 이동 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| login 직후 redirect `Location`이나 다음 요청 URL이 `http://...`로 내려감 | proxy가 원래 HTTPS를 앱에 제대로 전달하지 못했을 수 있음 | `X-Forwarded-Proto`, TLS termination, `Secure` cookie 재전송 여부 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| login 직후 redirect `Location`이나 OAuth `redirect_uri`의 host가 wrong origin으로 내려감 | 앱이 public origin 대신 내부 host를 기준으로 absolute URL을 만들었을 수 있음 | raw `Host`, `X-Forwarded-Host`, host preservation, public base URL | [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md) |
| request `Cookie` header는 있는데 서버가 anonymous로 봄 | server session 또는 BFF mapping 문제 | session id lookup, session store, BFF token/session mapping | [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) |

---

## 먼저 10초 판별표

| 지금 보이는 현상 | 보통 뜻하는 것 | 먼저 확인할 것 |
|---|---|---|
| 보호된 HTML 페이지에 들어가자마자 `302 -> /login` | 브라우저용 로그인 UX일 수 있다. 실질적으로는 "지금 인증 안 됨"에 가깝다 | page 요청인지, API 요청인지 |
| 로그인 성공 후 원래 URL로 다시 `302` | `SavedRequest`가 원래 URL로 복귀시키는 정상 흐름일 수 있다 | 로그인 직후 다음 요청이 `200`으로 끝나는지 |
| cookie가 있는데도 다시 `302 -> /login` | cookie는 남았지만 서버 session/BFF mapping이 사라졌을 수 있다 | cookie가 실제로 전송됐는지, 서버가 그 값을 찾는지 |
| `fetch('/api/me')`가 JSON `401` 대신 login HTML을 받음 | 브라우저 redirect 정책이 API 계약에 섞였을 가능성이 크다 | 응답 `Location`, 최종 `Content-Type`, filter chain 분리 |

초보자에게 가장 중요한 한 줄은 이것이다.

- `401`은 `인증이 안 됨`이라는 HTTP 의미다.
- `302`는 `다른 URL로 가라`는 브라우저 navigation 지시다.
- 브라우저 앱은 종종 `401` 상황을 바로 보여 주지 않고 `302 /login`으로 감싼다.

즉 `302`는 원인 그 자체라기보다, 인증 실패를 사용자 화면 흐름으로 바꿔 보여 주는 껍데기일 때가 많다.

---

## 왜 브라우저는 raw `401` 대신 `302`를 자주 보나

브라우저 페이지 요청은 보통 "보호 페이지에 갔더니 로그인 화면으로 이동"하는 UX를 기대한다.

그래서 서버나 framework는 자주 이렇게 동작한다.

1. 현재 요청이 인증되지 않았다고 판단한다.
2. raw `401`을 그대로 보여 주는 대신 login page로 `302` redirect한다.
3. 로그인 성공 후 원래 가려던 URL로 다시 보낸다.

반면 API 클라이언트나 모바일 SDK는 보통 redirect보다 raw `401` JSON을 기대한다.

즉 같은 "인증 안 됨"이라도 바깥 표현이 달라질 수 있다.

- browser page flow: `302 -> /login`
- API flow: raw `401`

핵심은 `상태 코드 숫자`만 보지 말고, **누가 호출했고 어떤 UX를 기대하는 요청인지**를 먼저 보는 것이다.

---

## `302`가 정상인 경우와 문제인 경우

### 1. 정상인 경우: 보호 페이지로 들어가서 login page로 이동

브라우저 웹앱에서 아래 흐름은 이상하지 않다.

```http
GET /orders/42
< 302 Found
< Location: /login
< Set-Cookie: JSESSIONID=abc123; HttpOnly; Secure
```

이 장면은 대개 "아직 인증 안 됨"을 브라우저 친화적으로 표현한 것이다.

- 사용자는 login page로 간다
- framework는 원래 URL을 어딘가에 기억할 수 있다
- 로그인 후 다시 `/orders/42`로 보내려 한다

여기서 중요한 점은 `JSESSIONID`가 생겼다고 곧바로 "로그인 성공"이 아니라는 점이다.
이 cookie는 로그인 전 navigation memory나 CSRF/session 관리를 위해 먼저 만들어질 수도 있다.

### 2. 정상인 경우: login 뒤 원래 URL로 복귀

```http
POST /login
Cookie: JSESSIONID=abc123
< 302 Found
< Location: /orders/42
```

이 흐름은 `SavedRequest`가 "아까 가려던 URL이 `/orders/42`였지"를 기억했다가 복귀시키는 장면일 수 있다.

즉 `SavedRequest`는 보통:

- 로그인 상태 자체를 저장하는 장치가 아니라
- 원래 가려던 URL을 기억하는 navigation memory다

### 3. 문제인 경우: API가 login HTML을 받아 버림

```http
GET /api/me
< 302 Found
< Location: /login
...
GET /login
< 200 OK
< Content-Type: text/html
```

프론트엔드 `fetch`나 API client는 보통 JSON `401`을 기대한다.
그런데 browser chain이 API route까지 덮으면 redirect를 따라간 뒤 login HTML을 받게 된다.

이 경우 문제의 본질은 대개:

- "권한이 왜 없지?"보다
- "browser용 redirect 정책이 API 계약에 섞였다"에 가깝다

---

## `SavedRequest` 예시로 보는 login loop

`SavedRequest`를 초보자 눈높이로 보면 아주 단순하다.

- "로그인 전 원래 가려던 URL 메모"

브라우저 login loop는 자주 아래 순서로 보인다.

1. 사용자가 `/admin/report`에 간다.
2. 서버가 인증되지 않았다고 판단하고 `302 -> /login`을 보낸다.
3. 동시에 "원래 요청은 `/admin/report`"였다는 메모를 남긴다.
4. 사용자가 로그인한다.
5. 서버가 메모를 보고 다시 `/admin/report`로 `302` 보낸다.
6. 그런데 다음 요청에서도 인증이 유지되지 않으면 또 `302 -> /login`으로 돌아간다.

즉 loop의 원인은 `SavedRequest` 자체보다 보통 그 뒤쪽이다.

- session이 저장되지 않았다
- session cookie가 안 실렸다
- 다른 domain/path/subdomain으로 가며 cookie가 빠졌다
- 서버 session store에서 해당 session id를 찾지 못했다

`SavedRequest`는 loop를 눈에 보이게 만들 뿐, 근본 원인은 로그인 상태 유지 실패인 경우가 많다.

---

## session cookie 예시로 보는 "cookie는 있는데 왜 또 로그인하지?"

초보자가 가장 자주 헷갈리는 문장은 이것이다.

`브라우저 개발자도구에 cookie가 있는데 왜 다시 /login으로 가지?`

핵심은 cookie가 "살아 있는 인증 상태 그 자체"가 아니라 **서버가 해석해야 하는 손잡이(reference)** 일 수 있다는 점이다.

예를 들어:

```http
GET /orders/42
Cookie: JSESSIONID=abc123
< 302 Found
< Location: /login
```

브라우저 입장에서는 cookie를 잘 보냈다.
하지만 서버는 아래 이유로 여전히 익명처럼 볼 수 있다.

- `abc123` session이 이미 만료됐다
- session store 재시작/장애로 매핑이 사라졌다
- cookie `Path`/`Domain`/`SameSite`가 기대와 달라 실제 요청에는 안 실렸다
- BFF라면 cookie는 왔지만 서버-side token/session mapping이 사라졌다

그래서 초보자용 규칙은 이렇다.

- `cookie exists` != `authenticated`
- `saved request exists` != `session is healthy`

초보자가 말하는 `hidden session`은 대개 위 장면처럼 "cookie reference는 보이는데 서버는 auth/session 상태를 못 복원한다"를 가리킨다.

둘 다 "주변 단서"일 뿐, 실제 인증 성립은 서버가 principal/session mapping을 복원할 수 있을 때만 된다.

---

## 브라우저 page 요청과 API 요청을 분리해서 봐야 하는 이유

같은 `/login` redirect라도 page 요청과 API 요청은 기대 계약이 다르다.

| 요청 종류 | 기대 계약 | 흔한 실패 모습 |
|---|---|---|
| 브라우저 page navigation | `302 -> /login` 후 로그인 화면 이동 | login loop, 원래 URL 복귀 실패 |
| XHR / `fetch` / REST API | raw `401` 또는 `403` JSON | login HTML 수신, redirect 따라가다 의미 상실 |

그래서 `401 vs 302`를 볼 때는 먼저 이 질문을 던진다.

1. 이 요청은 화면 이동용인가, API용인가?
2. 지금 cookie/session reference가 실제로 서버에서 해석되는가?
3. login 후 원래 URL 복귀 메모인 `SavedRequest`가 끼어 있는가?

이 세 질문이 분리되면 `302`, login loop, hidden session mismatch가 한 덩어리로 보이지 않는다.

---

## 실전 체크리스트

1. 네트워크 탭에서 첫 응답이 raw `401`인지, `302 Location: /login`인지 본다.
2. 그 요청이 page navigation인지 `fetch`/API인지 구분한다.
3. login 전후로 cookie 값이 생기거나 바뀌는지, login 직후 redirect `Location`이 `https://...`인지 `http://...`인지 같이 본다.
4. login 성공 후 원래 URL로 돌아간다면 `SavedRequest` 흐름을 의심한다.
5. request `Cookie` header가 비면 cookie scope 또는 proxy `Secure` cookie 갈래로 먼저 나눈다.
6. request `Cookie` header가 실리는데도 다시 `/login`이면 서버 session/BFF mapping lookup을 의심한다.
7. API가 HTML login page를 받으면 browser용 redirect 정책이 API 체인에 섞였는지 본다.

이 체크리스트만 익혀도 초보자가 `401 문제`, `302 UX`, `session persistence 문제`를 서로 다른 축으로 분리하기 훨씬 쉬워진다.

---

## 다음 단계

| 지금 확인한 첫 관찰 | 다음 한 걸음 |
|---|---|
| request `Cookie` header가 비어 있고 `Domain`/`Path`/`SameSite`/subdomain 이동이 먼저 의심된다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| login 직후 redirect `Location`이 `http://...`로 내려가거나 proxy/LB 뒤에서만 `Secure` cookie가 빠진다 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| cross-origin `fetch`와 `credentials: "include"`, CORS credential 헤더가 한 번에 섞였다 | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) |
| request `Cookie` header는 실리는데 서버가 계속 anonymous로 본다 | [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) |
| route를 다시 고르고 싶다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

이 문서는 beginner용 symptom splitter다.
즉 "redirect/navigation memory 쪽인가", "cookie scope 쪽인가", "proxy `Secure` cookie 쪽인가", "server session/BFF mapping 쪽인가"를 가르는 데까지만 쓰고, 다음 갈래는 위 표로 내려가는 편이 가장 안전하다.

---

## 꼬리질문

> Q: `302 -> /login`이면 항상 문제인가요?
> 의도: browser UX redirect와 실제 장애를 구분하는지 확인
> 핵심: 보호된 page 요청에서는 정상일 수 있다. API라면 계약 불일치일 가능성이 크다.

> Q: `SavedRequest`는 로그인 상태를 저장하나요?
> 의도: navigation memory와 authentication state를 분리하는지 확인
> 핵심: 보통 아니다. 원래 가려던 URL을 기억하는 장치에 가깝다.

> Q: cookie가 보이면 로그인된 것 아닌가요?
> 의도: cookie handle과 서버-side session 해석을 구분하는지 확인
> 핵심: 아니다. cookie는 reference일 뿐이고, 서버가 그 값을 해석하지 못하면 다시 익명처럼 보일 수 있다.

> Q: 왜 브라우저는 `401` 대신 login HTML을 보기도 하나요?
> 의도: browser redirect 체인과 API 계약 차이를 이해하는지 확인
> 핵심: framework가 인증 실패를 브라우저 navigation UX로 감싸면서 redirect를 따라간 결과일 수 있다.

## 한 줄 정리

브라우저에서 보이는 `302 -> /login`은 종종 raw `401`의 browser UX 버전이고, `SavedRequest`는 원래 URL 메모, session cookie는 서버가 해석해야 하는 reference라는 점을 분리하면 login loop를 훨씬 빨리 읽을 수 있다.
