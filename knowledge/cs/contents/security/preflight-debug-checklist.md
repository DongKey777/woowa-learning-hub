# Preflight Debug Checklist

> 한 줄 요약: 브라우저에서 `OPTIONS` preflight가 실패하면 실제 `GET`/`POST`/`PUT` API 호출은 아예 안 나갈 수 있다. junior 디버깅의 첫 갈림길은 "지금 막힌 게 preflight인가, 실제 API auth failure인가"를 먼저 나누는 것이다.

**난이도: 🟢 Beginner**

> 문서 역할: 이 문서는 browser CORS symptom과 actual API auth failure가 한 문장처럼 섞일 때 끼워 넣는 beginner `primer bridge`다. `OPTIONS 401/403`과 actual `401/403`을 같은 뜻으로 읽지 않게 만들고, 어디까지가 CORS/preflight 책임이고 어디부터가 API auth 책임인지 빠르게 가르는 entrypoint다.

> `1차 질문(고정)`: Network에서 `OPTIONS`만 실패하고 actual `GET`/`POST`가 없나, 아니면 actual request가 실제로 보이나?

관련 문서:
- [CORS 기초](./cors-basics.md)
- [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
- [Error-Path CORS Primer](./error-path-cors-primer.md)
- [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md#symptom-first-branch-table-cors-vs-auth)
- [CORS, SameSite, Preflight](./cors-samesite-preflight.md)
- [Cross-Origin Cookie, `fetch credentials`, CORS 입문](../network/cross-origin-cookie-credentials-cors-primer.md)
- [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: preflight debug checklist, options-only vs actual request, options 401 not auth, preflight failed actual request not sent, error path cors primer, beginner preflight primer, browser preflight error, 왜 options만 보이나요, devtools network 30초 예시, preflight 다음 어디로 가나

## 먼저 10초 분기표

| 지금 Network에서 먼저 볼 것 | 1차 해석 | 바로 할 일 |
|---|---|---|
| `OPTIONS`만 있고 같은 path의 actual `GET`/`POST`/`PUT`가 없다 | preflight가 막혀서 실제 API는 아직 안 나갔다 | CORS, `OPTIONS` 허용, proxy/filter 차단부터 본다 |
| `OPTIONS` 뒤에 actual `GET`/`POST`/`PUT`가 실제로 보인다 | preflight는 통과했고 이제 actual 응답을 읽어야 한다 | actual request의 `401`/`403`을 auth/authz 의미로 본다 |

한 줄 규칙은 이것만 기억하면 된다.

- `OPTIONS-only`면 auth를 파기하기 전에 preflight lane으로 간다.
- actual request가 보일 때만 그 요청의 `401`/`403`을 auth failure로 읽는다.

## 여기서 CORS 분석을 멈추는 순간

이 문서는 `OPTIONS-only`인지 확인하는 entrypoint다. 아래 셋 중 하나가 보이면 이 문서에서 더 깊게 CORS만 파지 말고, browser-session troubleshooting path로 다시 올라가 다음 branch를 고른다.

| 이 장면이 보이면 | 이제 뜻이 바뀐다 | 다음 이동 |
|---|---|---|
| 같은 path의 actual `GET`/`POST`/`PUT`가 실제로 생겼다 | preflight-only 문제가 아니다 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) 또는 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)로 내려간 뒤 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 복귀 |
| actual request는 보이는데 콘솔/JS에서는 여전히 CORS처럼 막힌다 | actual auth failure가 error-path CORS에 가려졌을 수 있다 | [Error-Path CORS Primer](./error-path-cors-primer.md)로 handoff한 뒤 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 복귀 |
| `OPTIONS`는 해결됐는데도 cookie가 안 붙거나 login/session 문장이 남는다 | preflight보다 session/cookie branch가 앞에 선다 | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md), [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md), [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

초보자용 stop rule:

- actual request가 보이는 순간부터는 `OPTIONS` status를 붙잡고 있지 않는다.
- `OPTIONS`가 해결된 뒤 남는 증상은 대개 auth, cookie, session, redirect branch다.
- 길을 잃으면 바로 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아가 symptom row를 다시 고른다.

## 이 문서를 먼저 읽는 이유

초보자가 CORS 이슈를 auth 이슈로 오해하는 장면은 보통 비슷하다.

- 콘솔에는 CORS 에러가 뜬다
- Network에는 `OPTIONS`가 `401`이나 `403`으로 실패해 있다
- 그래서 "`Authorization` token이 틀렸나?"부터 의심한다

하지만 이 순서는 자주 거꾸로다.

- `OPTIONS`가 실패하면 실제 API 요청이 아직 안 나갔을 수 있다
- 그러면 token, session, role을 파기 전에 preflight부터 고쳐야 한다
- 반대로 preflight가 통과한 뒤 actual `GET`/`POST`가 `401`/`403`이면 그때는 auth failure를 봐야 한다

즉 beginner 규칙은 아주 단순하다.

- **`OPTIONS`만 실패하고 actual request가 없으면 preflight 문제**
- **actual request가 보이고 그 응답이 `401`/`403`이면 auth 문제**

---

## 먼저 잡을 mental model

브라우저 cross-origin 호출은 한 번에 한 요청처럼 보여도 실제로는 두 단계일 수 있다.

| 단계 | 브라우저가 묻는 질문 | 보통 보이는 요청 | 여기서 실패하면 |
|---|---|---|---|
| preflight | "이 origin에서 이런 method/header로 보내도 되나?" | `OPTIONS /api/...` | actual `GET`/`POST`/`PUT`가 아예 안 나갈 수 있다 |
| actual request | "이제 진짜 API를 호출한다" | `GET`, `POST`, `PUT`, `DELETE` | 그때의 `401`/`403`은 실제 auth/authz 판단일 수 있다 |

핵심은 `OPTIONS`와 actual request가 같은 의미가 아니라는 점이다.

- preflight는 **허용 여부 확인**
- actual request는 **비즈니스 API 호출**

그래서 `OPTIONS 401`은 종종 "사용자 인증 실패"가 아니라,
**auth filter나 proxy가 preflight probe를 막았다**는 뜻이다.

---

## Symptom-First Branch Table (CORS vs Auth)

두 문서([Preflight Debug Checklist](./preflight-debug-checklist.md#먼저-10초-분기표), [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md#먼저-10초-분기표))에서 같은 분기표를 유지한다.

| Network에서 보이는 장면 | 먼저 읽는 뜻 | 첫 액션 | 다음 문서 |
|---|---|---|---|
| `OPTIONS /api/orders`만 있고 `POST /api/orders`가 없다 | preflight failure라서 actual request가 안 나갔다 | CORS/preflight 설정, `OPTIONS` 허용, proxy 차단부터 본다 | 이 문서에서 계속 본다 |
| `OPTIONS`는 `200`/`204`, 그 다음 `POST`가 `401` | preflight는 통과했고 actual auth failure가 났다 | token/session 유효성부터 확인한다 | [Auth Failure Responses `401/403/404`](./auth-failure-response-401-403-404.md#actual-request가-보일-때-읽는-10초-판별표) |
| `OPTIONS`는 `200`/`204`, 그 다음 `POST`가 `403` | actual request는 갔고 authz deny가 났다 | permission/ownership/scope를 확인한다 | [Auth Failure Responses `401/403/404`](./auth-failure-response-401-403-404.md#actual-request가-보일-때-읽는-10초-판별표) |
| 콘솔에는 CORS 에러인데 Network에는 actual `POST` `401`도 보인다 | 실제 auth failure가 CORS 누락으로 가려졌을 수 있다 | error path CORS header 누락과 auth 원인을 같이 본다 | [Error-Path CORS Primer](./error-path-cors-primer.md) |
| Postman/curl은 되는데 브라우저만 실패하고 Network에 `OPTIONS`가 보인다 | browser-only preflight/CORS 문제일 가능성이 높다 | 브라우저 preflight와 응답 헤더를 본다 | 이 문서의 체크리스트로 내려간다 |

---

## 30초 DevTools Network 미니 예시 (공통)

아래 3칸만 보면 초보자도 preflight lane과 auth lane을 바로 분리할 수 있다.

> 30초 mental model:
> `status` 숫자를 먼저 읽지 말고 `요청 method` -> `실제 요청 존재 여부` -> actual request의 `status` 순서로 본다.

| 장면 | 요청 method | 실제 요청 존재 여부 | 지금 읽는 status | 1차 결론 |
|---|---|---|---|---|
| 예시 A | `OPTIONS` | 같은 path의 `POST /api/orders`가 없음 | `401` | actual API는 아직 안 나갔다. preflight 차단으로 먼저 읽는다 |
| 예시 B | `OPTIONS` 다음에 `POST /api/orders`가 있음 | actual request가 실제로 보임 | `POST`의 `401` | preflight는 통과했고 actual auth failure를 봐야 한다 |
| 예시 C | `OPTIONS` 다음에 `POST /api/orders`가 있음 | actual request가 실제로 보이지만 응답 body는 브라우저에서 차단됨 | `POST`의 `401` + 콘솔 CORS 에러 | preflight 문제가 아니라 actual auth failure가 error-path CORS 누락에 가려진 경우다. [Error-Path CORS Primer](./error-path-cors-primer.md)로 handoff한다 |

초보자용 한 줄 해석:

- `OPTIONS 401`만 보고 인증 실패로 단정하지 않는다.
- 같은 path의 actual `GET`/`POST`가 실제로 보일 때만 그 요청의 `401`/`403`을 auth 의미로 읽는다.
- actual request는 보이는데 응답이 브라우저에서 막히면 preflight lane이 아니라 error-path CORS lane으로 넘긴다.

헷갈리면 읽는 순서를 고정하면 된다.

1. `요청 method`가 `OPTIONS`인지 먼저 본다.
2. 같은 path의 actual `POST`/`GET`이 뒤에 실제로 생겼는지 본다.
3. actual request가 있을 때만 그 request의 `status`를 auth 의미로 읽는다.

초보자가 가장 많이 하는 실수는 `status 401`만 먼저 보고 "`인증 실패네`"라고 단정하는 것이다.
이 문서와 [Auth Failure Responses `401/403/404`](./auth-failure-response-401-403-404.md#30초-devtools-network-미니-예시-공통)는 같은 3칸을 같은 순서로 보게 만들어 그 오해를 줄인다.

---

## 언제 preflight가 생기나

모든 cross-origin 요청이 preflight를 만드는 것은 아니다.
하지만 아래 같은 조합이면 junior가 자주 맞닥뜨린다.

- `Content-Type: application/json`
- `Authorization` 같은 custom header
- `PUT`, `DELETE`, 일부 `PATCH`

예를 들어 아래 요청은 preflight가 붙기 쉽다.

```js
fetch("https://api.example.com/orders", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJ..."
  },
  body: JSON.stringify({ itemId: 1 })
})
```

브라우저는 먼저 대략 이런 `OPTIONS`를 보낼 수 있다.

```http
OPTIONS /orders HTTP/1.1
Origin: https://app.example.com
Access-Control-Request-Method: POST
Access-Control-Request-Headers: authorization, content-type
```

이 probe가 통과해야 actual `POST /orders`가 이어진다.

---

## 체크리스트 1: 같은 URL에 `OPTIONS`와 actual request가 둘 다 있는지 본다

DevTools Network에서 해당 path를 찾고 먼저 이것만 본다.

- `OPTIONS /api/...`
- 그 뒤의 actual `GET`/`POST`/`PUT`

actual request가 아예 없으면 auth 디버깅으로 바로 내려가면 안 된다.

## 체크리스트 2: actual request가 없으면 preflight lane으로 간다

이때는 질문이 바뀐다.

- `OPTIONS` status가 `401`, `403`, `404`, `405`인가?
- `Access-Control-Allow-Origin`이 빠졌나?
- `Access-Control-Allow-Methods`에 actual method가 없나?
- `Access-Control-Allow-Headers`에 `authorization`, `content-type` 같은 requested header가 빠졌나?
- reverse proxy, gateway, security filter가 `OPTIONS`를 막았나?

여기서 특히 자주 보는 장면은 이것이다.

- Spring Security나 API gateway가 `OPTIONS`에도 auth를 강제한다
- Nginx/ingress가 `OPTIONS`를 upstream까지 넘기지 않는다
- CORS config가 success path에만 있고 error path에는 없다

## 체크리스트 3: `OPTIONS 401/403`이면 "token이 틀렸다"로 바로 읽지 않는다

preflight는 actual API 호출 전에 일어나는 허용 확인이다.
즉 `OPTIONS 401/403`은 종종 다음 뜻이다.

- 브라우저가 아직 actual API를 호출하지 못했다
- auth middleware가 preflight probe를 잘못 보호했다
- 사용자의 실제 bearer token/session validity와는 아직 별개다

초보자 규칙:

- **`OPTIONS 401/403`은 먼저 preflight 차단으로 읽는다**
- **actual `POST`/`GET` `401/403`을 봤을 때만 auth failure로 읽는다**

## 체크리스트 4: actual request가 있으면 그때 auth lane으로 간다

Network에 actual request가 보이면 이제 HTTP 의미를 읽는다.

| actual response | 먼저 읽는 뜻 | 다음 문서 |
|---|---|---|
| `401` | 인증이 성립하지 않았다 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) |
| `403` | 인증은 됐지만 권한이 부족하다 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) |
| `404`가 특히 grant 직후에도 남는다 | preflight가 아니라 actual concealment `404` 또는 stale deny branch일 수 있다 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md#symptom-first-branch-table-cors-vs-auth) |
| request `Cookie`가 비어 있다 | auth failure 전에 cookie scope/fetch 문제일 수 있다 | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) |
| browser page가 `/login`으로 튄다 | raw API auth failure가 browser redirect UX로 감싸졌을 수 있다 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |

actual request가 보이는 순간부터는 이 문서를 더 깊게 파지 말고, [Symptom-First Branch Table (CORS vs Auth)](#symptom-first-branch-table-cors-vs-auth)로 한 번만 올라가서 auth lane으로 다시 탄다.

## 체크리스트 4-1: 여기서 browser-session path로 다시 탄다

- `grant했는데 403/404가 계속`이면 preflight 이슈가 아니라 stale deny/cached concealment 후보로 읽는다.
- 그 경우 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md#symptom-first-branch-table-cors-vs-auth)에서 같은 분기표를 다시 본 뒤 [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)로 내려간다.
- cookie, login redirect, hidden session 문장이 더 크면 CORS 해석을 여기서 멈추고 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아가 browser/session row를 다시 고른다.

## 체크리스트 5: actual `401`/`403`인데 콘솔이 여전히 CORS라고 말하면 error path CORS도 본다

이 장면이 생각보다 흔하다.

1. preflight는 통과한다
2. actual request가 서버에 도달한다
3. 서버가 실제로 `401` 또는 `403`을 반환한다
4. 그런데 error response에는 `Access-Control-Allow-Origin`이 빠져 있다
5. 브라우저 JavaScript는 그 응답을 읽지 못해 결국 CORS 에러처럼 보인다

즉 이 경우는:

- **실제 auth failure가 맞고**
- **그 auth failure가 CORS에 의해 가려진 것**이다

이때는 auth 원인과 error-path CORS 설정을 둘 다 봐야 한다. 이 장면만 따로 다시 묶고 싶으면 [Error-Path CORS Primer](./error-path-cors-primer.md)로 내려가면 된다.

---

## 한 장면으로 비교하기

### 장면 A: preflight failure

```http
OPTIONS /api/orders 401
Origin: https://app.example.com
Access-Control-Request-Method: POST
Access-Control-Request-Headers: authorization, content-type
```

그리고 그 뒤에 `POST /api/orders`가 아예 없다.

이때의 해석:

- 실제 주문 API는 호출되지 않았다
- auth token의 유효성부터 의심할 단계가 아니다
- `OPTIONS` 허용, CORS allow headers/methods, proxy/security filter를 먼저 본다

### 장면 B: actual auth failure

```http
OPTIONS /api/orders 204
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: POST
Access-Control-Allow-Headers: authorization, content-type

POST /api/orders 401
WWW-Authenticate: Bearer realm="api"
```

이때의 해석:

- preflight는 통과했다
- actual API가 호출됐다
- 이제는 실제 auth failure를 봐야 한다

### 장면 C: auth failure가 CORS에 가려진 경우

```http
OPTIONS /api/orders 204
Access-Control-Allow-Origin: https://app.example.com

POST /api/orders 401
// error response에는 Access-Control-Allow-Origin 없음
```

이때의 해석:

- actual `401`은 이미 발생했다
- 하지만 브라우저는 JS에 그 응답을 노출하지 못한다
- auth 원인과 error response CORS 누락을 같이 고쳐야 한다

---

## 가장 흔한 혼동

### 1. "`OPTIONS 401`이면 내 bearer token이 만료된 거죠?"

대개 그렇게 바로 결론 내리면 안 된다.
preflight는 actual request 전에 일어나는 허용 확인이고, actual API auth 판단과는 층이 다르다.

### 2. "Postman은 되는데 브라우저만 안 되면 서버 auth는 정상 아닌가요?"

Postman/curl은 브라우저 CORS/preflight 규칙을 강제하지 않는다.
그래서 browser-only failure면 preflight/CORS 문제를 따로 봐야 한다.

### 3. "`OPTIONS`를 auth 없이 열면 보안 구멍 아닌가요?"

보통 아니다.
preflight probe를 통과시켜도 actual `POST`/`GET`는 여전히 auth를 요구할 수 있다.
`OPTIONS` 허용은 "실제 호출을 허용하겠다"가 아니라 "브라우저가 시도해 볼 수 있게 하겠다"에 가깝다.

### 4. "콘솔이 CORS라고 했으니 auth는 아닌 거죠?"

그것도 아니다.
actual `401`/`403`이 있었는데 error response CORS header가 빠져 있어서 브라우저가 CORS처럼 보여 줄 수도 있다.

---

## follow-up 한 장

| 지금 이 문서를 읽고 남은 질문 | 다음 한 장만 읽기 | 그다음 복귀 |
|---|---|---|
| Spring Security에서 `OPTIONS 401/403`을 어떻게 풀어야 할지 감이 안 온다 | `[follow-up]` [Spring Security OPTIONS Primer](./spring-security-options-primer.md) | `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| SOP/CORS 용어부터 다시 잡아야 한다 | `[primer]` [CORS 기초](./cors-basics.md) | `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| `credentials: "include"`, cookie scope, credential policy가 같이 섞인다 | `[follow-up]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) | `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| actual request `401`/`403` 의미를 auth/authz 관점에서 더 나눠야 한다 | `[follow-up]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) | `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

## re-branch와 catalog return

| 지금 이 문서를 읽고 남은 질문 | 다음 한 장만 읽기 | 그다음 복귀 |
|---|---|---|
| `grant했는데 403/404가 계속`이라 cached `404`/stale deny 같아 보인다 | `[re-branch]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md#symptom-first-branch-table-cors-vs-auth) | auth symptom table에서 actual request branch를 다시 고정한 뒤 [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)로 내려간다 |
| preflight cache, SameSite, allowlist 설계까지 더 깊게 봐야 한다 | `[deep dive]` [CORS, SameSite, Preflight](./cors-samesite-preflight.md) | `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| symptom 기준으로 갈래를 다시 고르고 싶다 | `[catalog]` [Security README: 증상별 바로 가기](./README.md#증상별-바로-가기) | `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

이 문서에서 분기만 끝났다면, follow-up 한 장을 읽은 뒤에는 다시 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아와 다음 갈래를 고르면 된다.

## 한 줄 정리

Network에 `OPTIONS`만 실패하고 actual request가 없으면 preflight부터 고치고, actual `GET`/`POST`가 보인 뒤의 `401`/`403`부터 auth failure로 읽는다.
