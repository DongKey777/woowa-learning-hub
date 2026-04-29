# Browser DevTools Response Body Ownership 체크리스트

> 한 줄 요약: DevTools에서 body가 보일 때는 먼저 `Status`, `Content-Type`, response preview 3칸으로 "app JSON인지, gateway JSON인지, login HTML인지, CDN 에러 HTML인지, gateway 기본 페이지인지"를 가르면 HTML-only 추정 실수를 크게 줄일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Gateway JSON vs App JSON Tiny Card](./gateway-json-vs-app-json-tiny-card.md)
- [CDN Error HTML vs App Error JSON Decision Card](./cdn-error-html-vs-app-json-decision-card.md)
- [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- [API Gateway Auth Failure Surface Map: `401`/`403`, `302`, Login HTML 구분 입문](./api-gateway-auth-failure-surface-map.md)
- [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- [Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer](../spring/spring-custom-error-dto-to-problemdetail-handoff-primer.md)
- [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: devtools response body ownership, gateway json vs app json, proxy json error devtools, login html instead of json, gateway default page devtools, response preview checklist, api response body beginner, why html instead of json, why gateway returns json, application/json but not app, gateway problem+json vs app error contract, vendor error envelope example, 처음 devtools body, 헷갈리는 login html, browser devtools response owner

## 핵심 개념

처음에는 body 내용을 길게 읽지 말고 "누가 이 말을 하고 있나"만 가르면 된다.

- app JSON: 애플리케이션이 자기 계약대로 데이터를 돌려주는 장면 후보
- login HTML: 인증 실패 뒤 redirect follow나 page 응답이 섞인 장면 후보
- CDN 에러 HTML: edge/CDN이 바깥에서 막거나 대신 응답한 장면 후보
- gateway 기본 페이지: reverse proxy나 gateway가 upstream 대신 실패를 말한 장면 후보

초급자가 자주 헷갈리는 이유는 다섯 장면 모두 DevTools `Response` 탭에서는 그냥 "본문"처럼 보이기 때문이다.
그래서 body를 읽기 전에 아래 3칸을 먼저 묶는다.

1. `Status`
2. `Content-Type`
3. response preview 첫 1~2줄

## 한눈에 보기

| DevTools에서 보이는 조합 | 초급자 첫 해석 | body owner 후보 | 안전한 다음 질문 |
|---|---|---|---|
| `200` + `application/json` + `{` 로 시작 | app이 자기 JSON 계약을 돌려줬을 가능성이 크다 | app | 필드 모양이 서비스 공통 응답 포맷과 맞는가 |
| `502`/`503`/`504` + `application/json` + vendor/common 에러 필드 | HTML이 아니어도 gateway/proxy local reply JSON일 수 있다 | gateway/proxy JSON | `Server`/`Via`/vendor header와 app 공통 필드가 어느 쪽에 가까운가 |
| `200` 또는 `302 -> 200` + `text/html` + login form/title | API 성공보다 login page를 따라간 결과일 수 있다 | login page / auth flow | 최종 URL이 `/login`인가, redirect row가 있었는가 |
| `403`/`429`/`503` + `text/html` + vendor branded error 문구 | CDN/WAF/edge가 바깥에서 막았을 수 있다 | CDN/edge | `Server`/`Via`/vendor header가 보이는가 |
| `502`/`504` + `text/html` + 매우 짧은 기본 HTML | gateway나 reverse proxy 기본 페이지 후보가 크다 | gateway/proxy | upstream timeout/connection 문제였는가 |

짧게 외우면 이렇게 보면 된다.

```text
JSON 모양 + application/json -> app 계약 후보
502/503/504 + application/json -> gateway JSON 후보도 같이 열기
login form/html + /login 흔적 -> auth/login HTML 후보
브랜드된 edge 에러 html -> CDN 후보
짧은 Bad Gateway/Gateway Timeout html -> gateway 기본 페이지 후보
```

`502`/`504` JSON에서 `title/detail/status`와 `errorCode/message/traceId`를 30초 안에 가르고 싶다면 [Gateway JSON vs App JSON Tiny Card](./gateway-json-vs-app-json-tiny-card.md)를 바로 붙여 읽으면 된다.

## 1분 체크리스트

### 1. `Status`로 장면을 먼저 자른다

| `Status` | 먼저 붙이는 라벨 |
|---|---|
| `200` | 일단 성공 응답처럼 보이지만, body owner는 아직 모른다 |
| `302`가 앞에 있고 마지막이 `200` | final body만 보지 말고 redirect chain을 의심한다 |
| `401`/`403` | auth/edge 거절일 수 있다 |
| `502`/`504` | gateway/proxy 응답 후보를 먼저 연다 |

핵심은 `200`만 보고 app 성공이라고 확정하지 않는 것이다.
특히 `fetch`/XHR에서는 숨은 `302 -> /login -> 200 HTML`이 final row만 남길 수 있다.

### 2. `Content-Type`으로 app 데이터와 page 계열을 가른다

| `Content-Type` | 초급자 첫 해석 |
|---|---|
| `application/json` | app data/error payload 후보가 크지만, `502`/`503`/`504`이면 gateway JSON도 같이 연다 |
| `text/html` | page, login form, CDN 에러 페이지, gateway 기본 페이지 후보를 연다 |
| 없음 또는 이상한 값 | download, opaque response, edge rewrite 같은 예외 문맥도 열어 둔다 |

여기서 중요한 점은 `application/json`만 보고도 "무조건 app"이라고 확정하지 않는다는 것이다.
특히 `502`/`503`/`504`와 같이 오면 `application/json`도 "gateway가 자기 에러 envelope을 JSON으로 준 것일 수 있으니 preview와 header를 더 보라"는 신호가 된다.
`text/html` 역시 login인지 gateway인지 단독 확정이 아니라, preview로 owner를 더 좁히라는 신호에 가깝다.

### 3. response preview 첫 1~2줄을 본다

길게 읽지 말고 아래처럼 표지판만 본다.

| preview 첫 인상 | 첫 owner 후보 |
|---|---|
| `{ "errorCode": ... }`, `{ "timestamp": ... }`, `{ "message": ... }` | app JSON |
| `{ "error": "bad_gateway" }`, `{ "status": 504, ... }`, `application/problem+json`인데 vendor/common 문맥이 강함 | gateway/proxy JSON |
| `<html>`, `<form`, `sign in`, `login`, `password` | login HTML |
| `error 403`, `access denied`, `request could not be satisfied`, vendor branding | CDN/WAF/edge HTML |
| `bad gateway`, `gateway timeout`, 단색 기본 HTML | gateway/proxy 기본 페이지 |

preview는 완전한 증거라기보다 **누구 말투인지 보는 첫 힌트**다.

## JSON owner를 이렇게 읽는다

### 1. app JSON

보통 이런 조합이 나온다.

- `Status: 200`, `400`, `401`, `404`, `500`
- `Content-Type: application/json`
- preview가 `{ ... }`로 시작

초급자 first pass는 아래 한 줄이면 충분하다.

"브라우저가 page를 받은 게 아니라 app 계약 payload를 받은 장면이구나."

이때는 redirect보다 JSON shape, 공통 `errorCode`, `message`, 요청 ID 같은 app 계약을 먼저 본다.

### 2. gateway/proxy JSON

gateway가 항상 기본 HTML만 준다고 외우면 초급자 분기가 쉽게 틀어진다.
일부 gateway, edge, API proxy는 local reply를 `application/json`이나 `application/problem+json`으로 내려보내기도 한다.

보통 이런 조합이 나온다.

- `Status: 502`, `503`, `504`
- `Content-Type: application/json` 또는 `application/problem+json`
- preview에 vendor/common 에러 필드나 gateway 쪽 문구가 먼저 보인다

초급자 first pass는 아래 한 줄이면 충분하다.

"JSON이라고 app로 확정하지 말고, 이 5xx JSON이 gateway 말투인지 app 말투인지 먼저 가르자."

이때는 아래 단서를 같이 묶는다.

- status가 app 내부 예외보다 gateway 계열 `502`/`503`/`504`에 가깝다
- `Server`, `Via`, vendor header가 눈에 띈다
- 서비스 공통 `errorCode`/`traceId` 규칙보다 generic `status`, `title`, `detail` 또는 vendor field가 더 강하다

## payload 미니 예시 3개

처음 질문은 "JSON이면 다 app 에러 아닌가요?"다. 아래 3개를 나란히 보면 **필드 말투**가 다르다.

| 장면 | payload 예시 | 초급자 첫 해석 |
|---|---|---|
| app 커스텀 계약 | `{ "errorCode": "ORDER_NOT_FOUND", "message": "주문 42를 찾을 수 없습니다.", "traceId": "9f1c2a7e" }` | 도메인 `errorCode`와 서비스 문장이 보이면 app JSON 후보가 강하다 |
| gateway generic `problem+json` | `{ "type": "about:blank", "title": "Gateway Timeout", "status": 504, "detail": "Upstream service did not respond in time." }` | `type/title/status/detail`만 있고 `504`면 app보다 gateway local reply 후보를 같이 연다 |
| vendor/gateway envelope | `{ "error": "upstream_failure", "reason": "connection reset before headers", "request_id": "gw-12ab34cd", "upstream": "order-service" }` | `reason`, `request_id`, `upstream`가 먼저 보이면 운영용 gateway/vendor envelope 후보가 강하다 |

짧게 외우면 `errorCode/message/traceId -> app`, `type/title/status/detail -> generic problem+json`, `error/reason/request_id -> vendor envelope`이다. 그래도 필드만 보지 말고 **status와 `Server`/`Via`를 같이 묶어 owner를 본다**.

## HTML owner를 이렇게 읽는다

### 3. login HTML

보통 이런 조합이 나온다.

- 최종 `Status: 200`
- `Content-Type: text/html`
- preview에 `login`, `sign in`, `<form`, `password` 같은 단어

초급자가 자주 틀리는 지점은 "`200`이니까 API 성공"이라고 읽는 것이다.
하지만 이 장면은 자주 아래 흐름의 마지막 결과다.

```text
/api/me -> 302 Found -> /login -> 200 text/html
```

즉 owner를 "원래 API"로 잡기보다 "브라우저가 따라간 login page"로 먼저 잡는 편이 안전하다.

### 4. CDN 에러 HTML

보통 이런 조합이 나온다.

- `Status: 403`, `429`, `503` 같은 edge 계열 상태
- `Content-Type: text/html`
- preview에 CDN/WAF vendor 문구나 branded error 문구

이때는 app controller보다 앞단 edge 정책을 먼저 연다.
예를 들면 rate limit, geo/block, bot protection, WAF, edge auth 같은 문맥이다.

초급자 first pass 문장은 이 정도면 된다.

"서비스 HTML이라기보다 edge vendor가 대신 보여 주는 거절 페이지 같아 보인다."

### 5. gateway 기본 페이지

보통 이런 조합이 나온다.

- `Status: 502` 또는 `504`
- `Content-Type: text/html`
- preview가 매우 짧고 `Bad Gateway`, `Gateway Timeout` 같은 기본 문구

이 장면은 app business JSON보다 proxy/gateway가 upstream 문제를 대신 말한 장면 후보가 크다.
그래서 controller 코드만 먼저 파기보다 timeout, upstream 연결, reverse proxy local reply를 먼저 본다.

## 흔한 오해와 함정

- `200`이면 무조건 app 성공이라고 생각한다. login HTML `200`은 hidden redirect 결과일 수 있다.
- `application/json`이면 무조건 app이라고 생각한다. `502`/`503`/`504`에서는 gateway JSON local reply도 충분히 있을 수 있다.
- `text/html`이면 전부 같은 HTML이라고 생각한다. login page, CDN error page, gateway 기본 페이지는 owner가 다르다.
- JSON이면 무조건 정상이라고 생각한다. app JSON 에러 payload도 충분히 있을 수 있다.
- preview를 길게 읽느라 시간을 쓴다. 초급자 첫 pass에서는 첫 1~2줄과 핵심 단어만 보면 된다.
- `502`/`504`인데도 app 응답 포맷을 찾으려 한다. 이 조합은 gateway 기본 페이지 후보를 먼저 보는 편이 빠르다.
- CDN branded page를 app의 커스텀 에러 페이지로 착각한다. vendor 흔적과 상태 코드를 같이 봐야 한다.

## 실무에서 쓰는 모습

| 장면 | DevTools에서 보이는 것 | 첫 메모 |
|---|---|---|
| A | `200`, `application/json`, body가 `{ "id": 42 }` | app JSON 응답 후보 |
| B | `504`, `application/problem+json`, preview에 `title: Gateway Timeout` | gateway/proxy JSON 후보 |
| C | `200`, `text/html`, preview에 login form | API 성공보다 login redirect follow 결과 후보 |
| D | `403`, `text/html`, branded error 문구 | CDN/WAF/edge 거절 후보 |
| E | `504`, `text/html`, 짧은 기본 HTML | gateway timeout 기본 페이지 후보 |

이 네 장면을 처음부터 정확히 원인 확정하려고 하지 말고, incident 메모를 이렇게 남기면 충분하다.

1. `Status`
2. `Content-Type`
3. preview 첫 단어
4. owner 후보 한 줄

예:

```text
504 / application/json / "Gateway Timeout" / gateway JSON local reply 후보
504 / text/html / "Gateway Timeout" / gateway 기본 페이지 후보
200 / text/html / "login" / 숨은 redirect 뒤 login HTML 후보
```

## 더 깊이 가려면

- login HTML `200`이 왜 API 성공이 아닐 수 있는지 이어서 보려면 [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- `502`/`504`에서 gateway 기본 페이지와 app 실패를 더 정확히 가르려면 [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- auth failure가 `401`/`403`, `302`, login HTML `200`으로 어떻게 달라 보이는지 보려면 [API Gateway Auth Failure Surface Map: `401`/`403`, `302`, Login HTML 구분 입문](./api-gateway-auth-failure-surface-map.md)
- header 기준으로 CDN/proxy/app 흔적을 더 붙여 읽고 싶으면 [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- browser page auth UX와 raw auth 계약 차이를 보려면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- branded CDN 에러 HTML과 app-owned JSON만 30초 안에 먼저 가르고 싶으면 [CDN Error HTML vs App Error JSON Decision Card](./cdn-error-html-vs-app-json-decision-card.md)

## 면접/시니어 질문 미리보기

**Q. DevTools에서 HTML body가 보이면 왜 먼저 owner를 가려야 하나요?**  
같은 `text/html`이어도 login page, CDN error page, gateway 기본 페이지가 모두 섞여 보일 수 있어서, owner를 틀리면 조사 시작점이 완전히 달라진다.

**Q. login HTML `200`은 왜 API 성공으로 읽으면 안 되나요?**  
보호된 API가 먼저 `302`로 `/login`으로 보냈고, 브라우저가 그 redirect를 따라간 최종 page일 수 있기 때문이다.

**Q. `502`/`504`에서 response preview가 짧은 기본 HTML이면 무엇을 뜻하나요?**  
app JSON 에러보다 gateway/proxy가 upstream 문제를 대신 말한 기본 페이지 후보가 크다는 뜻이다.

## 한 줄 정리

DevTools body owner를 빠르게 가르려면 `Status`로 장면을 자르고, `Content-Type`으로 JSON vs HTML을 나눈 뒤, response preview 첫 1~2줄로 app JSON, gateway JSON, login HTML, CDN 에러 HTML, gateway 기본 페이지를 구분하면 된다.
