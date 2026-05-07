---
schema_version: 3
title: "Browser XHR/fetch vs page navigation DevTools 1분 비교 카드"
concept_id: network/browser-fetch-vs-page-navigation-redirect-trace-card
canonical: true
category: network
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 87
mission_ids: []
review_feedback_tags:
- fetch-vs-page-navigation
- login-redirect-trace
- api-contract-vs-page-ux
aliases:
- fetch vs page navigation redirect
- xhr login redirect trace
- api got login html
- page navigation vs fetch
- hidden login html 200
- devtools 302 login row
symptoms:
- XHR/fetch가 login HTML 200을 받았는데 API 성공 JSON으로 오해한다
- page navigation redirect와 API fetch redirect follow를 같은 UX 성공 기준으로 읽는다
- DevTools 마지막 200 row만 보고 원래 /api 요청도 200이었다고 결론낸다
intents:
- comparison
- troubleshooting
- symptom
prerequisites:
- network/redirect-vs-forward-vs-spa-navigation-basics
- network/browser-devtools-response-body-ownership-checklist
next_docs:
- network/fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser
- network/fetch-redirected-response-url-opaqueredirect-mini-card
- network/fetch-redirect-error-choice-card
- network/login-redirect-hidden-jsessionid-savedrequest-primer
- security/browser-401-vs-302-login-redirect-guide
linked_paths:
- contents/network/fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser.md
- contents/network/fetch-redirected-response-url-opaqueredirect-mini-card.md
- contents/network/fetch-redirect-error-choice-card.md
- contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md
- contents/network/redirect-vs-forward-vs-spa-navigation-basics.md
- contents/network/browser-devtools-waterfall-primer.md
- contents/network/browser-devtools-response-body-ownership-checklist.md
- contents/security/browser-401-vs-302-login-redirect-guide.md
confusable_with:
- network/fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser
- network/fetch-redirected-response-url-opaqueredirect-mini-card
- network/redirect-vs-forward-vs-spa-navigation-basics
- security/browser-401-vs-302-login-redirect-guide
forbidden_neighbors: []
expected_queries:
- "fetch가 302를 따라가서 login HTML 200을 받은 것과 page navigation redirect를 어떻게 구분해?"
- "DevTools에서 Type document와 xhr fetch를 먼저 봐야 하는 이유가 뭐야?"
- "API 호출이 200 text/html login page를 받으면 JSON 성공이 아니라는 점을 설명해줘"
- "302 /login row와 최종 200 HTML row를 Network 탭에서 어떻게 나눠 읽어?"
- "fetch response.redirected response.url과 DevTools redirect chain을 같이 보는 법을 알려줘"
contextual_chunk_prefix: |
  이 문서는 Browser DevTools에서 page navigation(document) redirect와
  XHR/fetch redirect follow를 Type, Status Code, Location, final
  Content-Type, Response body 기준으로 나누어 API가 login HTML 200을
  먹는 hidden auth failure를 판독하는 beginner chooser다.
---
# Browser XHR/fetch vs page navigation DevTools 1분 비교 카드

> 한 줄 요약: 같은 `302 -> /login -> 200 HTML`도 page load와 XHR/fetch는 DevTools에서 먼저 봐야 하는 칸이 다르므로, `Type`, `Status Code`, `Location`, 최종 `Content-Type` 순서로 읽으면 "화면 이동"과 "API가 login HTML을 먹은 것"을 빠르게 분리할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Fetch Auth Failure Chooser: `401 JSON` vs `302 /login` vs 숨은 Login HTML `200`](./fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser.md)
- [Fetch `response.redirected` vs `response.url` vs `opaqueredirect` 미니 카드](./fetch-redirected-response-url-opaqueredirect-mini-card.md)
- [Fetch `redirect: "error"` tiny card](./fetch-redirect-error-choice-card.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md)
- [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
- [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- [network 카테고리 인덱스](./README.md)
- [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)

retrieval-anchor-keywords: browser fetch vs page navigation redirect, xhr vs fetch vs page navigation devtools, /api/me to /login trace, page navigation vs fetch login redirect, devtools waterfall redirect trace, fetch got login html instead of json, xhr redirected to login, why page moves but fetch does not, login redirect side by side, browser redirect chain beginner, devtools 302 login row, 302 to login then 200 html, devtools fields first reveal redirect, 헷갈 fetch page navigation, 왜 api가 login html 200을 받아요

## 핵심 개념

같은 incident라도 질문 축이 다르다.

- page navigation: 브라우저가 주소창과 화면을 실제로 옮겼는가
- XHR/fetch: 코드가 최종 `Response`에서 무엇을 받았는가
- DevTools Network: 첫 줄이 `302`였는지, 마지막 줄이 `200 text/html`인지

즉 `/api/me -> /login`을 한 문장으로 "redirect 났다"라고만 묶으면, page UX와 API 계약이 섞인다. beginner는 먼저 **누가 이동했는지**, **코드가 무엇을 받았는지**, **Network에서 어느 줄이 증거인지**를 따로 적는 편이 안전하다.

## 먼저 보는 칸 1표

| 요청 종류 | DevTools에서 첫 5초에 볼 칸 | 여기서 가장 먼저 드러나는 것 | 초급자 첫 문장 |
|---|---|---|---|
| page load (`Type: document`) | row의 `Status Code`, `Location`, 다음 row `Name/URL` | `302 -> /login` 뒤 브라우저가 실제로 login page를 열었다 | "페이지 이동 redirect다" |
| XHR/fetch (`Type: xhr` 또는 `fetch`) | 원래 API row의 `Status Code`, 최종 row의 `Content-Type`, `Preview/Response` 첫 줄 | API 호출이 redirect follow 뒤 login HTML `200`으로 끝났을 수 있다 | "API 성공이 아니라 login HTML fallback일 수 있다" |

짧게 외우면 이렇다.

- page load는 `Location`이 먼저다
- XHR/fetch는 최종 `Content-Type: text/html`이 먼저다
- 둘 다 헷갈리면 `Type` 열로 `document`와 `xhr/fetch`를 먼저 가른다

## 한눈에 보기

| 같은 incident를 보는 창 | 보통 먼저 보이는 것 | 첫 해석 | 바로 다음 확인 |
|---|---|---|---|
| 주소창 page navigation | `/orders`를 열었더니 주소창이 `/login`으로 바뀜 | 브라우저가 redirect를 따라 새 page로 이동했다 | `302`와 `Location` row가 있었는지 |
| XHR/fetch 기본 `follow` | 코드에서는 최종 `200 text/html` 또는 `response.url === "/login"` | API 성공이 아니라 login page까지 따라간 결과일 수 있다 | `Content-Type`, `response.redirected`, final URL |
| `fetch("/api/me", { redirect: "manual" })` | `opaqueredirect` 같은 제한 신호 | redirect는 있었지만 코드는 중간 정보를 거의 안 본다 | 실제 `302` row는 DevTools에서 본다 |
| DevTools Network | `GET /api/me -> 302`, 다음 줄 `GET /login -> 200` | redirect 증거는 row 두 줄로 남고, 최종 body는 login HTML일 수 있다 | 어떤 줄이 initiator였는지, page 요청인지 XHR인지 |

짧게 외우면 이렇다.

- page navigation은 "브라우저가 옮겨 갔나"
- XHR/fetch는 "코드가 마지막에 뭘 받았나"
- waterfall은 "중간 `302`와 최종 `200`이 몇 줄로 보이나"

## `302 -> /login -> 200 HTML`을 어떤 칸에서 먼저 잡나

| DevTools 칸 | page load에서 읽는 법 | XHR/fetch에서 읽는 법 |
|---|---|---|
| `Type` | `document`면 화면 이동 후보다 | `xhr`/`fetch`면 API 계약 후보다 |
| `Status Code` | 첫 row `302`가 보이면 redirect 원인은 거의 여기서 먼저 드러난다 | 첫 row `302`를 못 봤더라도 원래 API row를 열면 숨은 redirect 흔적을 찾을 수 있다 |
| `Response Headers > Location` | `/login`이면 "왜 페이지가 이동했는가" 질문으로 간다 | `/login`이면 "왜 API가 page UX 정책을 탔는가" 질문으로 간다 |
| 최종 row의 `Content-Type` | `text/html`이어도 page는 자연스러울 수 있다 | `text/html`이면 JSON 기대와 충돌한다. 여기서 가장 빨리 이상 신호가 난다 |
| `Preview`/`Response` | login form HTML이면 "도착한 화면"을 본 것이다 | login form HTML이면 "API 데이터가 아니라 login page를 먹었다"는 뜻이다 |

브라우저/버전마다 열 이름이나 row 묶음 표시는 조금 다를 수 있다. 하지만 초급자 첫 판독 기준은 대체로 같다.

## 같은 `/api/me -> /login`을 세 언어로 번역하기

| 관점 | 같은 장면을 이렇게 적는다 | beginner 메모 |
|---|---|---|
| page navigation | "`GET /orders`가 `302 /login` 뒤 login page로 열렸다" | 주소창 이동이 핵심이다 |
| XHR/fetch `follow` | "`fetch('/api/me')`는 성공처럼 끝났지만 body는 login HTML이다" | 화면 이동이 아니라 API 계약 오염이 핵심이다 |
| DevTools waterfall | "`/api/me` row는 `302`, 다음 `/login` row는 `200 text/html`" | 증거 줄을 따로 본다 |

여기서 중요한 차이는 이것이다. page navigation에서는 redirect가 **의도된 UX**일 수 있지만, JSON API `fetch`에서는 같은 redirect가 **숨은 실패 표면**일 수 있다. 그래서 같은 `/login` 도착이라도 page와 API를 같은 성공 기준으로 읽으면 안 된다.

## DevTools에서는 줄이 이렇게 보인다

보통 Network 탭에서는 아래처럼 보인다.

```text
1. GET /api/me    302 Found      Location: /login
2. GET /login     200 OK         Content-Type: text/html
```

이 두 줄을 beginner는 아래처럼 읽으면 된다.

- 1번 줄: redirect를 지시한 원인 줄
- 2번 줄: 브라우저가 따라가서 도착한 최종 줄

브라우저와 버전에 따라 waterfall 세부 표시는 조금 다를 수 있지만, 핵심은 같다. XHR/fetch 코드에서 `200`만 먼저 보이더라도 Network에는 보통 **원인 줄(`302`)과 도착 줄(`200`)이 분리**되어 남는다. page navigation row인지 XHR/fetch row인지는 `Type`, `Initiator`, `Content-Type`을 같이 보면 더 덜 헷갈린다.

## 1분 판독 순서

1. `Type` 열을 보고 `document`인지 `xhr/fetch`인지 먼저 가른다.
2. 원래 요청 row의 `Status Code`가 `302`인지 확인한다.
3. `Response Headers > Location`이 `/login`인지 본다.
4. 최종 row에서 `Content-Type`이 `text/html`인지 확인한다.
5. `Preview` 첫 줄이 login form이면 "redirect follow 끝 HTML"로 적는다.

한 줄 기억법:

- page load: `302`와 `Location`이 먼저 힌트다
- XHR/fetch: 최종 `200 text/html`이 먼저 이상 신호다

## 흔한 오해와 함정

- page가 `/login`으로 갔으니 XHR/fetch도 자동으로 화면을 옮긴다고 생각한다. XHR/fetch는 응답을 받는 것이지, page navigation 자체를 대신하지는 않는다.
- XHR/fetch가 `200`을 받았으니 API 성공이라고 단정한다. login HTML `200`은 hidden redirect follow 결과일 수 있다.
- `manual`이면 `Location`을 코드에서 그대로 읽을 수 있다고 기대한다. beginner 기준으로는 DevTools row가 더 직접적인 증거다.
- DevTools 마지막 줄만 보고 "원래 `/api/me`도 `200`이었다"고 읽는다. redirect chain에서는 원인 줄과 도착 줄을 분리해야 한다.

## 실무에서 쓰는 모습

가장 흔한 세 장면을 한 번에 붙이면 아래 같다.

| 장면 | 브라우저/코드에서 보이는 것 | 안전한 첫 문장 |
|---|---|---|
| 주소창으로 보호 페이지 진입 | `/orders`를 열자 `/login`으로 이동 | page redirect UX가 작동했다 |
| XHR/fetch `"/api/me"`가 `200 text/html` | 코드에서는 성공처럼 보이지만 body가 login page다 | API가 성공한 게 아니라 redirect follow 결과일 수 있다 |
| `fetch("/api/me", { redirect: "error" })`가 실패 | redirect를 계약 위반으로 끊어 냈다 | 숨은 login HTML 성공 표면을 막으려는 선택이다 |

20초 판독 순서는 이렇다.

1. 이 요청이 주소창 page인지 `/api/**` `fetch`인지 먼저 적는다.
2. DevTools에서 `302` 원인 줄과 최종 `200` 도착 줄이 둘 다 있는지 본다.
3. XHR/fetch라면 final `Content-Type`이 JSON인지 HTML인지 본다.
4. API 계약을 지키고 싶으면 `manual` 추적 또는 `error` fail-fast 중 무엇이 맞는지 고른다.

## 더 깊이 가려면

- `401 JSON`, `302 /login`, 숨은 login HTML `200` 셋을 먼저 분리하려면 [Fetch Auth Failure Chooser: `401 JSON` vs `302 /login` vs 숨은 Login HTML `200`](./fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser.md)
- `follow`에서 `response.redirected`, `response.url`을 어떻게 읽는지 다시 고정하려면 [Fetch `response.redirected` vs `response.url` vs `opaqueredirect` 미니 카드](./fetch-redirected-response-url-opaqueredirect-mini-card.md)
- redirect를 곧바로 실패로 취급할지 결정하려면 [Fetch `redirect: "error"` tiny card](./fetch-redirect-error-choice-card.md)
- login redirect와 `SavedRequest`, cookie 전송 분기를 넓게 보려면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- waterfall 구간 이름 자체가 헷갈리면 [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)

## 한 줄 정리

같은 `/api/me -> /login` incident라도 page navigation은 "브라우저가 옮겨 갔는가", `fetch`는 "코드가 최종으로 무엇을 받았는가", DevTools waterfall은 "`302` 원인 줄과 `200` 도착 줄이 어떻게 남는가"를 각각 따로 읽는 것이 핵심이다.
