# Fetch Credentials vs Cookie Scope

> 한 줄 요약: `credentials: "include"`는 "브라우저가 credential을 실어도 된다"는 요청 옵션일 뿐이다. 실제 cookie가 붙으려면 cookie scope도 맞아야 하고, JavaScript가 응답을 읽으려면 서버 CORS credential 정책도 따로 맞아야 한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [CORS 기초](./cors-basics.md)
> - [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
> - [CORS, SameSite, Preflight](./cors-samesite-preflight.md)
> - [CORS Credential Pitfalls / Allowlist Design](./cors-credential-pitfalls-allowlist.md)
> - [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
> - [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
> - [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: fetch credentials include cookie scope, credentials include cookie not sent, fetch include cookie missing, fetch credentials vs cors, credentials include vs Access-Control-Allow-Credentials, CORS credential policy cookie scope, Access-Control-Allow-Credentials not sending cookie, cookie stored but fetch request missing Cookie, same-origin vs same-site fetch credentials, app.example.com api.example.com credentials include, cross-origin cookie request beginner, browser auth cookie debugging, fetch Set-Cookie ignored, CORS allow credentials exact origin, cookie visible devtools but not sent fetch

## 먼저 잡을 mental model

브라우저 인증 디버깅에서는 "쿠키를 보낸다"라는 말을 세 단계로 나눠야 한다.

1. JavaScript 요청이 credential을 포함해도 되는가?
2. 그 cookie가 이 URL에 붙을 수 있는 scope인가?
3. 서버 응답을 JavaScript가 읽어도 되는 CORS 정책인가?

세 질문은 서로 대신해 주지 않는다.

| 관문 | 묻는 질문 | 주로 보는 것 | 실패하면 보이는 장면 |
|---|---|---|---|
| `fetch` credential mode | 이 요청이 브라우저 credential을 포함해도 되나? | `credentials: "omit" / "same-origin" / "include"` | cross-origin 요청의 `Cookie` header가 비어 있다 |
| cookie scope | 이 cookie가 이 host/path/site에 붙을 수 있나? | `Domain`, `Path`, `SameSite`, `Secure`, host-only 여부 | `Application`에는 보이지만 실패 요청에는 안 붙는다 |
| CORS credential policy | credential이 섞인 cross-origin 응답을 JS가 읽어도 되나? | `Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials`, `Vary: Origin` | 요청은 갔는데 콘솔에는 CORS 에러가 난다 |

즉 `credentials: "include"`를 넣었다고 CORS가 해결되지 않고, CORS를 열었다고 cookie scope가 자동으로 넓어지지 않는다.

---

## `credentials` 옵션은 무엇을 바꾸나

`fetch`의 `credentials`는 브라우저가 자동으로 관리하는 credential, 특히 cookie를 요청에 포함할지 결정한다. 이 문서에서는 cookie 디버깅에 집중한다.

| 값 | beginner 감각 | 주의할 점 |
|---|---|---|
| `omit` | cookie 같은 브라우저 credential을 보내지 않는다 | login API처럼 cookie가 필요한 호출에 쓰면 인증 상태가 안 간다 |
| `same-origin` | 기본값이다. 정확히 같은 origin일 때만 보낸다 | sibling subdomain은 same-site일 수 있어도 same-origin은 아니다 |
| `include` | cross-origin 요청에도 credential을 포함할 수 있게 한다 | cookie scope와 CORS 응답 정책이 맞아야 실제로 성공한다 |

응답이 `Set-Cookie`를 내려주는 흐름도 같이 봐야 한다.
cross-origin `fetch`에서 cookie 저장을 기대한다면 credential mode, CORS credential 응답, cookie 속성(`Secure`, `SameSite`, `Domain`, `Path`)이 모두 맞아야 한다.
DevTools에 cookie rejection reason이 보이면 그 메시지를 먼저 따른다.

예를 들어 프론트가 `https://app.example.com`, API가 `https://api.example.com`이면 origin이 다르다.

```js
fetch("https://api.example.com/me")
```

이 기본 요청은 cross-origin cookie 전송을 기대하기 어렵다. cookie 기반 인증 API라면 보통 아래처럼 명시한다.

```js
fetch("https://api.example.com/me", {
  credentials: "include"
})
```

하지만 여기까지는 첫 번째 관문만 지난 것이다.

---

## CORS credential 정책은 무엇을 바꾸나

서버는 credential이 포함된 cross-origin 응답을 브라우저 JavaScript가 읽어도 된다고 명시해야 한다.

```http
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
Vary: Origin
```

여기서 중요한 점은 두 가지다.

- `Access-Control-Allow-Origin: *`는 credential 응답과 같이 쓰면 안 된다.
- `Access-Control-Allow-Credentials: true`는 cookie를 "붙여 주는" 헤더가 아니다. 이미 credential이 포함된 요청/응답을 JS에 노출해도 된다고 허용하는 쪽에 가깝다.

그래서 이런 혼란이 생긴다.

| 관찰 | 가능한 해석 |
|---|---|
| 서버 로그에는 `/me`가 `200`으로 찍힘 | 네트워크 요청 자체는 도착했을 수 있다 |
| 브라우저 콘솔에는 CORS 에러 | JS가 응답을 읽는 단계에서 막혔을 수 있다 |
| request `Cookie` header가 비어 있음 | CORS보다 앞 단계인 `fetch credentials` 또는 cookie scope 문제일 수 있다 |

CORS는 "응답 읽기"의 문제이고, cookie scope는 "요청에 cookie가 붙는가"의 문제다.

---

## cookie scope는 무엇을 바꾸나

cookie가 브라우저에 저장돼 있어도 모든 요청에 붙는 것은 아니다.
브라우저는 매 요청마다 `Domain`, `Path`, `SameSite`, `Secure`를 보고 전송 여부를 다시 판단한다.

예를 들어 login이 아래처럼 끝났다고 하자.

```http
Set-Cookie: session=abc123; Path=/; HttpOnly; Secure
```

`Domain`이 없으면 보통 이 cookie는 응답을 준 정확한 host에 묶이는 host-only cookie다.
`https://auth.example.com/login`에서 받은 host-only cookie는 `https://api.example.com/me`에 붙지 않는다.

반대로 subdomain 사이에서 공유하려면 의도적으로 scope를 맞춰야 한다.

```http
Set-Cookie: session=abc123; Domain=example.com; Path=/; HttpOnly; Secure; SameSite=Lax
```

이 설정도 만능은 아니다.

- `Path=/auth`면 `/api/me`에는 안 붙는다.
- cross-site iframe이나 partner domain 호출이면 `SameSite=None; Secure`가 필요할 수 있다.
- `Secure` cookie는 HTTPS 요청에만 붙는다.

즉 `credentials: "include"`는 cookie scope를 무시하는 버튼이 아니다.

---

## 한 장면으로 보는 디버깅

### 장면 1: `credentials: "include"`가 빠진 경우

| 항목 | 관찰 |
|---|---|
| 프론트 | `https://app.example.com` |
| API | `https://api.example.com/me` |
| 요청 코드 | `fetch("https://api.example.com/me")` |
| 실패 요청 | `Cookie` header가 비어 있음 |

먼저 의심할 것은 default `same-origin`이다.
`app.example.com`과 `api.example.com`은 같은 site일 수 있어도 origin은 다르다.

후보 수정:

```js
fetch("https://api.example.com/me", {
  credentials: "include"
})
```

그다음 서버 CORS와 cookie scope를 이어 확인한다.

### 장면 2: CORS credential 정책이 빠진 경우

| 항목 | 관찰 |
|---|---|
| 실패 요청 | `Cookie: session=abc123`가 실제로 실림 |
| 서버 로그 | `/me`가 `200` 또는 `401`로 찍힘 |
| 브라우저 콘솔 | CORS 에러로 JS가 응답을 못 읽음 |

이때는 cookie 전송보다 응답 노출 정책이 더 의심된다.

```http
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
Vary: Origin
```

허용 origin은 `*`가 아니라 실제 프론트 origin이어야 한다.

### 장면 3: cookie scope가 틀린 경우

| 항목 | 관찰 |
|---|---|
| 요청 코드 | `credentials: "include"` 있음 |
| CORS 응답 | exact origin + credentials 허용 |
| DevTools `Application` | cookie가 `auth.example.com` 아래 보임 |
| 실패 요청 | `https://api.example.com/me`에 `Cookie` header가 없음 |

이때는 `fetch`나 CORS보다 cookie scope를 먼저 본다.

- host-only cookie인가?
- `Domain=example.com`이 필요한 구조인가?
- `Path`가 `/auth`처럼 너무 좁지 않은가?
- cross-site 맥락인데 `SameSite=Lax`/`Strict`로 막히지 않았나?

이 분해는 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)에서 더 자세히 본다.

---

## 가장 흔한 혼동

### 1. "`Access-Control-Allow-Credentials: true`면 cookie가 자동으로 가나요?"

아니다.

이 헤더는 서버가 브라우저에게 credentialed response를 허용한다고 말하는 쪽이다.
request에 cookie를 붙일지는 `fetch` credential mode와 cookie scope가 먼저 결정한다.

### 2. "`credentials: include`를 넣었는데 왜 아직 CORS 에러가 나나요?"

`credentials: "include"`는 요청 옵션이다.
서버 응답에는 여전히 exact `Access-Control-Allow-Origin`과 `Access-Control-Allow-Credentials: true`가 필요하다.

### 3. "`SameSite`와 `same-origin`은 같은 말인가요?"

아니다.

| 비교 | 예시 | 뜻 |
|---|---|---|
| same-origin | `https://app.example.com` -> `https://app.example.com` | scheme, host, port가 모두 같다 |
| same-site | `https://app.example.com` -> `https://api.example.com` | 보통 같은 registrable domain 묶음이다 |

`fetch` default인 `same-origin`은 sibling subdomain을 같은 origin으로 보지 않는다.
반면 cookie `SameSite`는 origin이 아니라 site 맥락을 본다.

### 4. "Postman에서는 되는데 브라우저만 안 돼요"

Postman은 브라우저 CORS 정책과 cookie scope 자동 판단을 똑같이 적용하지 않는다.
브라우저 auth 문제는 반드시 DevTools `Network`에서 실제 request `Cookie` header와 CORS 응답 헤더를 같이 봐야 한다.

---

## 실전 확인 순서

1. 호출 URL이 같은 origin인지, sibling subdomain인지, 완전히 다른 site인지 적는다.
2. `fetch`에 `credentials: "include"`가 필요한 cross-origin 호출인지 본다.
3. 실패한 요청의 raw request header에 `Cookie`가 실제로 있는지 확인한다.
4. `Cookie`가 없으면 `Application > Cookies`의 `Domain`, `Path`, `SameSite`, `Secure`를 요청 URL과 비교한다.
5. `Cookie`가 있는데 JS가 응답을 못 읽으면 `Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials`, `Vary: Origin`을 본다.
6. 서버가 새 cookie를 내려줘야 하는 흐름이면 응답의 `Set-Cookie`와 브라우저의 cookie rejection reason도 같이 확인한다.
7. cookie가 실제로 실렸고 응답도 읽히는데 여전히 익명이면 서버 session store나 BFF translation 문제로 넘어간다.

이 순서의 핵심은 "CORS부터 고치자"가 아니라, request 전송과 response 읽기와 cookie scope를 따로 관찰하는 것이다.

---

## 다음 단계

- cookie가 저장됐지만 특정 host/path/site 요청에 안 붙는 문제는 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 이어 간다.
- preflight, `SameSite=None`, `Vary: Origin`, CORS allowlist 운영까지 더 깊게 보려면 [CORS, SameSite, Preflight](./cors-samesite-preflight.md)를 본다.
- credentialed CORS allowlist 설계 자체는 [CORS Credential Pitfalls / Allowlist Design](./cors-credential-pitfalls-allowlist.md)로 내려간다.
- cookie가 붙는데도 `302 -> /login`이나 login HTML fallback이 보이면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)를 본다.

## 한 줄 정리

브라우저 cookie auth 디버깅은 `fetch`가 credential을 허용했는지, cookie scope가 요청 URL에 맞는지, 서버 CORS credential 정책이 응답 읽기를 허용했는지를 세 칸으로 나누면 빠르게 좁혀진다.
