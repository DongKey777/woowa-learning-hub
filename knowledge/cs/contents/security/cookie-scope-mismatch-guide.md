# Cookie Scope Mismatch Guide

> 한 줄 요약: 브라우저에 cookie가 "저장돼 있다"와 현재 요청에 cookie가 "실려 간다"는 다른 문제다. `Domain`, `Path`, `SameSite`, subdomain 범위가 안 맞으면 login 직후에도 다시 `/login`으로 튈 수 있다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
> - [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
> - [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md)
> - [CORS, SameSite, Preflight](./cors-samesite-preflight.md)
> - [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: cookie scope mismatch, cookie exists but login loops, cookie exists but no cookie header, cookie stored not sent, host-only cookie, domain path samesite mismatch, subdomain cookie mismatch, login loop cookie scope, cookie exists but session missing, cookie visible in devtools but not sent, application tab cookie but network request missing, auth cookie scope guide, browser cookie scope beginner, Domain Path SameSite beginner, sibling subdomain cookie missing, auth.example.com app.example.com cookie, cookie path too narrow, SameSite login loop, host only cookie login loop

## 이 문서를 먼저 읽는 이유

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

## 먼저 10초 판별표

| 지금 보이는 현상 | 보통 뜻하는 것 | 먼저 볼 것 |
|---|---|---|
| login 응답 뒤 cookie는 생겼는데 다음 요청에 다시 `/login` | cookie 저장은 됐지만 다음 요청에 안 실렸을 수 있다 | Network 탭의 실제 `Cookie` 헤더 |
| cookie가 `auth.example.com` 아래에는 보이는데 `app.example.com`에서 안 먹음 | host-only 또는 `Domain` 범위가 너무 좁다 | cookie의 `Domain`과 저장된 host |
| `/auth/callback` 직후에는 괜찮아 보이는데 `/api/me`에서 튕김 | `Path`가 너무 좁다 | cookie `Path`와 실제 요청 path |
| 외부 사이트/iframe/embedded flow에서만 로그인 루프 | `SameSite`가 cross-site 흐름을 막을 수 있다 | 요청이 same-site인지 cross-site인지 |
| cookie 헤더는 실제로 실리는데도 계속 익명처럼 보임 | 브라우저 scope보다 서버 session/BFF mapping 문제가 더 의심된다 | server session lookup, BFF translation |

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

### 3. "cookie가 auth 서브도메인에 보이는데 앱은 왜 익명이지?"

이건 `SameSite`보다 먼저 host-only cookie를 의심한다.
특히 login 전용 host와 app host를 나눠 둔 구조에서 자주 나온다.

---

## 실전 확인 순서

1. `Application > Cookies`에서 cookie가 어느 host 아래 저장됐는지 본다.
2. 실패한 요청 하나를 고르고 `Network` 탭에서 request `Cookie` header가 실제로 있었는지 본다.
3. request host와 cookie `Domain`이 맞는지 본다.
4. request path와 cookie `Path`가 맞는지 본다.
5. 그 요청이 same-site인지 cross-site인지 보고 `SameSite`를 비교한다.
6. cookie가 실제로 실렸는데도 익명처럼 보이면 그때 서버 session/BFF mapping 문제로 넘어간다.

이 순서로 보면 "cookie는 있는데 왜 또 로그인하지?"를 브라우저 범위 문제와 서버 상태 문제로 분리할 수 있다.

---

## 다음 단계

- `302 -> /login`, `SavedRequest`, login HTML fallback이 같이 보이면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)로 이어 가면 된다.
- cookie/session/JWT 자체가 아직 섞여 보이면 [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)부터 다시 맞춘다.
- cross-site credential, `fetch`, preflight까지 같이 얽히면 [CORS, SameSite, Preflight](./cors-samesite-preflight.md)로 내려간다.
- cookie는 실제로 실리는데 server-side에서만 세션이 끊기면 [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)을 본다.

## 한 줄 정리

login loop에서 중요한 질문은 "cookie가 보이느냐"가 아니라 "이 요청의 host/path/site 조건에서 그 cookie가 실제로 전송되느냐"다. `Domain`, `Path`, `SameSite`, subdomain 범위를 먼저 분리하면 원인을 훨씬 빨리 좁힐 수 있다.
