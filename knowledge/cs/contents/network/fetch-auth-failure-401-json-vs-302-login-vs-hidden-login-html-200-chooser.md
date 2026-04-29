# Fetch Auth Failure Chooser: `401 JSON` vs `302 /login` vs 숨은 Login HTML `200`

> 한 줄 요약: `fetch`에서 인증이 깨졌을 때는 raw `401 JSON`, 첫 응답 `302 /login`, redirect를 따라간 뒤 보이는 login HTML `200`이 같은 층이 아니므로, "원래 계약"과 "브라우저가 최종으로 보여 준 표면"을 분리해서 읽어야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Fetch `response.redirected` vs `response.url` vs `opaqueredirect` 미니 카드](./fetch-redirected-response-url-opaqueredirect-mini-card.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- [API Gateway Auth Failure Surface Map: `401`/`403`, `302`, Login HTML 구분 입문](./api-gateway-auth-failure-surface-map.md)
- [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](../spring/spring-api-401-vs-browser-302-beginner-bridge.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: fetch auth failure chooser, 401 json vs 302 login, login html 200 after fetch, fetch got html instead of json, hidden login html 200, api gets login html, xhr redirected to login, devtools final 200 hides 302 login, why fetch gets html, what is 401 json, 처음 fetch auth failure, 헷갈 302 login 200 html

## 핵심 개념

초보자는 보통 이 셋을 한 문장으로 섞는다.

- `401 JSON`: API가 "인증 안 됨"을 계약대로 직접 말했다
- `302 /login`: 서버가 브라우저를 login 화면으로 보내라고 지시했다
- login HTML `200`: 브라우저가 redirect를 따라간 뒤 마지막에 받은 page다

즉 `200`이 보여도 원래 API 계약이 성공했다는 뜻은 아닐 수 있다. `fetch`에서는 특히 "첫 응답"과 "최종 응답"을 따로 읽어야 한다.

## 한눈에 보기

| 지금 보이는 것 | 먼저 붙일 해석 | API 소비자 관점에서 의미 | safe next step |
|---|---|---|---|
| `401` + `application/json` | raw auth failure | 서버가 JSON 계약으로 실패를 직접 말했다 | 에러 body와 auth header를 본다 |
| 첫 row가 `302` + `Location: /login` | browser login redirect | page UX가 API 호출에 섞였다 | redirect owner와 cookie 전송을 본다 |
| 최종 응답이 `200` + `text/html` + login body | hidden login fallback | API 성공이 아니라 redirect follow 끝 HTML일 수 있다 | final URL, redirect chain, body 첫 줄을 본다 |

짧게 외우면 아래 한 줄이다.

- `401 JSON`은 원래 계약
- `302 /login`은 이동 지시
- login HTML `200`은 마지막 도착점

## 세 경우를 이렇게 고른다

### `401 JSON`

`fetch("/api/me")`가 바로 `401`과 JSON body를 주면 가장 해석이 단순하다.

- 프론트 코드는 auth failure를 직접 처리하면 된다
- login page HTML과 API data 계약이 섞이지 않았다
- `message`, `errorCode`, `WWW-Authenticate` 같은 실패 단서를 볼 수 있다

### `302 /login`

DevTools 첫 응답 row에 `302`와 `Location: /login`이 보이면, 브라우저용 redirect 정책이 먼저 작동한 것이다.

- page 요청이라면 자연스러울 수 있다
- API 호출이라면 "redirect를 따라가도 되는가"부터 다시 봐야 한다
- cookie가 실제로 실렸는지 함께 확인해야 한다

### 숨은 login HTML `200`

코드에서는 `200`만 보이는데 body가 `<html>`이고 제목이 `login`이면, 앞단 `302`가 접혀 있을 가능성이 크다.

- `response.url`이 `/login`으로 바뀌었는지 본다
- `Content-Type`이 `application/json`이 아니라 `text/html`인지 본다
- 성공 UI를 띄우기 전에 원래 API 계약이 깨졌는지 확인한다

## 흔한 오해와 함정

- `200`이면 성공이라고 단정한다. `fetch`에서는 login HTML fallback일 수 있다.
- `302 /login`을 보면 `401`이 아예 없었다고 생각한다. auth failure가 browser UX로 번역됐을 수 있다.
- `Application`에 cookie가 보이면 인증도 정상이라고 생각한다. 저장, 전송, 서버 복원은 다른 질문이다.
- page 요청과 `/api/**` 요청을 같은 기준으로 본다. page는 redirect UX가 자연스럽고, API는 raw `401 JSON`이 더 선명하다.

## 실무에서 쓰는 모습

가장 안전한 20초 판독 순서는 아래다.

1. 요청 URL이 page인지 `/api/**`인지 먼저 본다.
2. Network 첫 row에 `401`인지 `302`인지 본다.
3. 마지막 응답이 HTML이면 final URL과 body 첫 줄을 본다.
4. cookie가 필요한 구조면 같은 요청의 `Request Headers > Cookie`를 본다.

예를 들어 `fetch("/api/me")` 결과가 `200 text/html`이면, 먼저 "내 API가 성공했다"가 아니라 "redirect를 따라 login page에 도착했나?"를 묻는 편이 맞다.

## 더 깊이 가려면

- `response.redirected`, `response.url`, `opaqueredirect` 신호를 더 정확히 읽으려면 [Fetch `response.redirected` vs `response.url` vs `opaqueredirect` 미니 카드](./fetch-redirected-response-url-opaqueredirect-mini-card.md)
- login redirect, `SavedRequest`, cookie 전송 분기를 한 장 더 넓게 보려면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- HTML 응답 자체가 원래 page인지 숨은 fallback인지 가르려면 [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- browser `302 /login`과 session/cookie branch를 더 직접적으로 고르려면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)

## 한 줄 정리

`fetch` auth failure에서는 `401 JSON`은 원래 실패 계약, `302 /login`은 이동 지시, login HTML `200`은 redirect를 따라간 최종 표면이므로 셋을 같은 성공/실패 한 칸에 넣지 않는 것이 핵심이다.
