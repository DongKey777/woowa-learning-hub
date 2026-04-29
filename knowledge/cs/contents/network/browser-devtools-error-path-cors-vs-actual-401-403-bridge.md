# Browser DevTools에서 CORS처럼 보이지만 actual `401`/`403`이 있는 경우: Error-Path CORS 브리지

> 한 줄 요약: DevTools `Network`에 actual `GET`/`POST`의 `401`/`403`이 이미 보이는데 콘솔은 계속 CORS만 말하면, "요청 자체가 막혔다"가 아니라 "실제 auth failure가 error-path CORS에 가려졌다"를 먼저 의심해야 한다.

**난이도: 🟡 Intermediate**

> 문서 역할: 이 문서는 beginner가 `OPTIONS-only preflight failure`를 이미 한 번 가른 뒤, `actual request exists + console CORS` 장면을 DevTools 증거 순서로 다시 읽게 만드는 intermediate bridge다.

> target query shape: `network tab 401 but console cors`, `actual request exists cors 403`, `devtools cors masks 401`, `왜 network에는 403인데 프론트는 cors래요`

관련 문서:

- [Browser DevTools `OPTIONS` Preflight vs Actual Request Failure 미니 카드](./browser-devtools-options-preflight-vs-actual-failure-mini-card.md)
- [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)
- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [Error-Path CORS Primer](../security/error-path-cors-primer.md)
- [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md)
- [Preflight Debug Checklist](../security/preflight-debug-checklist.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: devtools error path cors bridge, network tab 401 but console cors, network tab 403 but console cors, actual request exists cors error, actual post 401 cors, actual post 403 cors, cors masks actual 401, cors masks actual 403, why network shows 401 but frontend sees cors, why network shows 403 but frontend sees cors, error-path cors devtools, actual request exists console cors, preflight passed then cors then 401, 왜 cors인데 network 401, 왜 cors인데 network 403

## 먼저 잡는 mental model

이 장면은 pure preflight failure와 다르다.

- `OPTIONS`만 실패하고 actual `POST`가 없으면: 아직 actual auth failure를 읽지 않는다
- actual `POST`나 `GET`가 이미 보이면: 요청은 서버까지 갔다
- 그 actual row가 `401`/`403`인데 콘솔은 CORS라고 하면: **actual auth failure + 응답 노출 실패**를 같이 본다

짧게 줄이면 아래 한 문장이다.

```text
console CORS보다 actual request row 존재 여부가 먼저고, actual 401/403이 보이면 auth lane을 버리지 않는다
```

## 20초 분기표

| 지금 보이는 증거 | 먼저 읽는 결론 | safe next step |
|---|---|---|
| `OPTIONS /api/orders 401/403`, actual `POST /api/orders` 없음 | preflight failure 후보다 | [Preflight Debug Checklist](../security/preflight-debug-checklist.md) |
| `OPTIONS 204` 뒤 actual `POST /api/orders 401` | preflight는 통과했고 actual auth failure다 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md) |
| actual `POST /api/orders 403`가 보이는데 콘솔은 CORS라고 한다 | actual authz failure가 error-path CORS에 가려졌을 수 있다 | [Error-Path CORS Primer](../security/error-path-cors-primer.md) -> [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md) |
| actual request는 보이지만 request `Cookie` header가 비어 있다 | auth failure 해석보다 credential 전달 경로가 먼저다 | [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md) |

## DevTools에서 보는 순서

### 1. 같은 path의 actual row가 실제로 생겼는가

이 문서의 첫 gate는 이것 하나다.

- 없으면 preflight lane
- 있으면 actual lane

`OPTIONS 401`과 actual `POST 401`은 같은 숫자여도 같은 질문이 아니다.

### 2. actual row의 status가 `401`인지 `403`인지 읽는다

actual request가 이미 보이면 그때부터는 status 해석을 미루지 않는다.

- actual `401`: 인증 부재, 만료 세션, 잘못된 bearer token 같은 authn lane 후보
- actual `403`: principal은 있지만 role/scope/ownership에서 거절된 authz lane 후보

이 의미 자체는 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md)로 바로 넘기면 된다.

### 3. 그런데 콘솔이 CORS만 말하면 "응답 읽기 실패"를 한 겹 더 붙인다

여기서 beginner가 자주 오진한다.

- Network에는 actual `401`/`403`이 보인다
- 서버 로그에도 그 status가 남는다
- 그런데 프런트 코드는 body/status를 기대만큼 못 읽고 CORS처럼 본다

이 장면은 보통 "요청이 안 갔다"가 아니라 "실제 error response에 CORS 허용 헤더가 빠져 JS 노출이 막혔다"는 질문에 가깝다.

즉 결론은 둘 중 하나가 아니라 둘 다다.

- actual auth failure가 있었다
- 그 failure surface가 error-path CORS 때문에 프런트에서 흐려졌다

## 왜 초보자가 여기서 헷갈리나

초보자는 콘솔 문구를 가장 강한 증거로 읽기 쉽다. 하지만 이 장면에서는 `Network`의 actual row가 더 먼저다.

| 먼저 믿은 증거 | 흔한 오해 | 더 안전한 해석 |
|---|---|---|
| console `blocked by CORS policy` | 요청이 서버까지 안 갔다 | actual row가 보이면 이미 갔다 |
| actual `401`만 봄 | 프런트도 같은 `401` body를 읽었을 것이다 | error-path CORS면 JS는 못 읽을 수 있다 |
| `OPTIONS 204`만 봄 | CORS는 완전히 끝났다 | actual error response에도 CORS 헤더가 계속 필요할 수 있다 |

## 30초 예시

프런트에서 아래 요청을 보낸다고 하자.

```js
fetch("https://api.example.com/orders", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer expired-token"
  },
  credentials: "include",
  body: JSON.stringify({ itemId: 1 })
});
```

DevTools에서 두 장면은 전혀 다르게 읽어야 한다.

| 장면 | Network에 보이는 것 | 브라우저/프런트에서 보이는 것 | 첫 결론 |
|---|---|---|---|
| A | `OPTIONS /orders 403`, actual `POST /orders` 없음 | console CORS | preflight failure다 |
| B | `OPTIONS /orders 204`, actual `POST /orders 401` | console CORS, JS는 `401` body 접근 실패 | actual auth failure가 error-path CORS에 가려졌을 수 있다 |

장면 B에서 다음 한 칸은 "token/session이 왜 `401`이 났는가"와 "왜 error response에 CORS 헤더가 빠졌는가"를 분리해서 보는 것이다.

## 자주 하는 말 바꾸기

- "`CORS라서 auth는 아닌 것 같아요`" 대신 "`actual request가 이미 보여서 auth lane도 같이 봐야겠어요`"
- "`Network에 401이 있으니 프런트도 401을 읽었겠네요`" 대신 "`error-path CORS면 Network 숫자와 JS 가시성이 다를 수 있어요`"
- "`preflight가 204였으니 CORS는 끝났어요`" 대신 "`actual error response에도 CORS 정책이 이어지는지 보겠어요`"

## 다음 단계 handoff

| 지금 확인된 사실 | 다음 문서 | 이유 |
|---|---|---|
| actual `401`이 보인다 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md) | authn 의미를 먼저 고정한다 |
| actual `403`이 보인다 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md) | authz 의미를 먼저 고정한다 |
| actual `401`/`403`이 보이는데 console CORS가 같이 뜬다 | [Error-Path CORS Primer](../security/error-path-cors-primer.md) | error response CORS 누락을 별도 축으로 본다 |
| actual request 자체가 안 보인다 | [Preflight Debug Checklist](../security/preflight-debug-checklist.md) | 아직 auth failure lane이 아니다 |
| actual request는 보이지만 request `Cookie`가 비어 있다 | [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md) | auth 해석보다 credential 전송 여부가 먼저다 |

## 한 줄 정리

DevTools에서 actual `401`/`403` row가 이미 보이면 console CORS 문구만 보고 preflight lane으로 돌아가지 말고, actual auth failure와 error-path CORS masking을 함께 읽어야 한다.
