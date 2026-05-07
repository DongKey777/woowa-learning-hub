---
schema_version: 3
title: "Fetch `redirect: \"error\"` tiny card"
concept_id: network/fetch-redirect-error-choice-card
canonical: true
category: network
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 86
mission_ids: []
review_feedback_tags:
- fetch-redirect-mode-choice
- api-contract-fail-fast
- hidden-login-html
aliases:
- fetch redirect error
- redirect error mode
- fetch redirect follow manual error
- api got login html
- redirect should fail fast
- fetch login redirect contract
symptoms:
- redirect: error를 redirect 정보를 더 자세히 보는 모드로 오해한다
- JSON API가 /login HTML 200을 받는 숨은 성공 표면을 follow로 계속 삼킨다
- page redirect UX와 API contract redirect 금지를 같은 기준으로 처리한다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- network/fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser
- network/fetch-redirected-response-url-opaqueredirect-mini-card
next_docs:
- network/browser-fetch-vs-page-navigation-redirect-trace-card
- network/login-redirect-hidden-jsessionid-savedrequest-primer
- network/ssr-view-render-vs-json-api-response-basics
- security/browser-401-vs-302-login-redirect-guide
linked_paths:
- contents/network/fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser.md
- contents/network/fetch-redirected-response-url-opaqueredirect-mini-card.md
- contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md
- contents/network/ssr-view-render-vs-json-api-response-basics.md
- contents/security/browser-401-vs-302-login-redirect-guide.md
confusable_with:
- network/fetch-redirected-response-url-opaqueredirect-mini-card
- network/browser-fetch-vs-page-navigation-redirect-trace-card
- network/fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser
- security/browser-401-vs-302-login-redirect-guide
forbidden_neighbors: []
expected_queries:
- "fetch redirect error는 redirect를 자세히 보기 위한 옵션이 아니라 fail-fast 옵션이야?"
- "JSON API에서 /login redirect가 나오면 follow manual error 중 무엇을 써야 해?"
- "API가 hidden login HTML 200을 받는 문제를 redirect: error로 어떻게 드러내?"
- "page navigation redirect와 fetch API contract redirect 금지는 어떻게 달라?"
- "fetch redirect mode follow manual error를 beginner 기준으로 비교해줘"
contextual_chunk_prefix: |
  이 문서는 fetch redirect mode 중 follow, manual, error를 API JSON 계약,
  /login redirect, hidden login HTML 200, fail-fast 처리 기준으로 고르는
  beginner chooser다.
---
# Fetch `redirect: "error"` tiny card

> 한 줄 요약: `fetch`에서 redirect가 나오면 안 되는 JSON/API 계약이라면 `redirect: "error"`가 가장 깔끔한 선택이고, 최종 도착지만 읽으면 되는 경우는 `follow`, redirect 자체를 DevTools와 함께 추적하려는 경우는 `manual`이 더 잘 맞는다.

**난이도: 🟢 Beginner**

관련 문서:

- [Network README](./README.md#fetch-redirecterror-tiny-card)
- [Fetch Auth Failure Chooser: `401 JSON` vs `302 /login` vs 숨은 Login HTML `200`](./fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser.md)
- [Fetch `response.redirected` vs `response.url` vs `opaqueredirect` 미니 카드](./fetch-redirected-response-url-opaqueredirect-mini-card.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)

retrieval-anchor-keywords: fetch redirect error, redirect error mode beginner, when to use redirect error, fetch redirect follow manual error, api got login html, redirect should fail fast, fetch login redirect contract, fetch redirect error vs manual, fetch redirect error vs follow, fetch 401 vs 302 vs login html, hidden login html 200 fail fast, 302 login should fail fetch, 언제 redirect error 써요, 왜 login html 대신 실패로 받고 싶어요, beginner fetch redirect choice

## 핵심 개념

이 카드는 "`redirect: \"error\"`는 redirect를 더 자세히 보는 모드인가요?"라는 질문을 먼저 끊는다.

- 아니다. `error`는 **redirect를 관찰하는 모드**보다 **redirect를 계약 위반으로 취급하는 모드**에 가깝다.
- 그래서 API가 JSON을 줘야 하는데 `/login` HTML로 새어 들어오면, `follow`로 성공처럼 읽기보다 `error`로 바로 실패시키는 편이 더 선명할 수 있다.

짧게 외우면 이렇다.

- `follow` = 최종 결과를 계속 받는다
- `manual` = redirect가 있었음을 제한적으로 관찰한다
- `error` = redirect가 나오면 그 자리에서 실패로 본다

## 한눈에 보기

| 지금 원하는 것 | 가장 잘 맞는 모드 | 왜 이렇게 읽나 |
|---|---|---|
| 최종 body가 더 중요하고, 중간 redirect는 브라우저 기본 동작에 맡겨도 된다 | `follow` | 마지막 도착 응답을 그대로 받기 쉽다 |
| redirect가 있었는지 추적하고 DevTools에서 실제 `302` row를 함께 볼 생각이다 | `manual` | 코드에서는 `opaqueredirect` 같은 제한 신호만 보고, 실제 `Location`은 네트워크 trace로 본다 |
| API 계약상 redirect가 오면 안 되고, login HTML `200` 같은 숨은 성공 표면을 막고 싶다 | `error` | redirect를 조용히 따라가지 않고 바로 실패로 올린다 |

beginner 기준 핵심 질문은 하나다.

- "이 호출에서 redirect는 정상 흐름인가, 아니면 계약 위반인가?"

이 질문에 "계약 위반"이라고 답하면 `error`가 가장 깨끗하다.

먼저 분기표를 하나 더 붙이면 더 덜 헷갈린다.

| 먼저 보인 장면 | 첫 해석 | `redirect: "error"`가 특히 잘 맞는가 |
|---|---|---|
| raw `401` + JSON body | redirect 문제가 아니라 auth failure 계약이다 | 보통 아니다. 먼저 `401` body와 auth lane을 본다 |
| 첫 row `302 /login` | browser login redirect가 섞였다 | 그렇다. API 계약에서 redirect를 금지하고 싶을 때 선명하다 |
| 최종 login HTML `200` | 숨은 redirect follow 결과일 수 있다 | 그렇다. 다음부터는 조용한 follow 대신 실패로 드러내기 좋다 |

즉 이 카드는 "`401`/`302`/login HTML `200` 중 어느 장면인가"를 먼저 고른 뒤, 그중 redirect lane에서 `error`를 쓰는 이유를 설명하는 follow-up 카드다.

## 언제 `error`가 가장 깔끔한가

### 1. JSON API인데 login HTML이 섞이면 안 될 때

예를 들어 프런트가 `/api/me`에서 JSON을 기대하는데, 인증이 풀리면 서버가 `/login`으로 redirect시키는 장면이 있다.

- `follow`면 마지막 login HTML `200`이 먼저 보여서 "성공했는데 body가 이상하다"처럼 읽힐 수 있다.
- `error`면 redirect 자체를 실패로 받아서 "이 API 계약이 page redirect에 오염됐다"는 사실이 더 빨리 드러난다.

그래서 "`API got login HTML 200`이 너무 자주 디버깅된다"면 `error`가 좋은 초급 방어선이 된다.

### 2. 브라우저 page 이동과 API 호출을 분리하고 싶을 때

브라우저 page 요청은 redirect를 자연스럽게 따라가도 된다. 하지만 `fetch` API 호출까지 같은 규칙으로 읽으면 page UX와 API 계약이 섞인다.

- page navigation은 `/login`으로 보내는 UX가 자연스러울 수 있다.
- API 호출은 `401` JSON이나 명시적 에러 계약이 더 자연스럽다.

이 경계를 코드에서 강하게 드러내고 싶다면 `error`가 잘 맞는다.

### 3. "redirect가 오면 안 된다"를 테스트나 래퍼 규칙으로 못 박고 싶을 때

공용 fetch 래퍼나 테스트 헬퍼에서 아래 의도를 분명히 할 수 있다.

- 이 함수는 JSON만 받는다
- redirect가 오면 정상 복구가 아니라 버그/인증 누수로 본다

이때 `manual`보다 `error`가 더 직선적이다. `manual`은 "redirect가 왔음을 관찰하고 다음 판단을 내가 한다"에 가깝고, `error`는 "redirect면 여기서 중단"에 가깝다.

## 흔한 오해와 함정

- `error`가 redirect 정보를 더 많이 준다고 생각한다. 아니다. 목적은 정보 수집보다 fail-fast다.
- `manual`이면 `302 Location`을 코드에서 다 읽을 수 있다고 기대한다. beginner 기준으로는 DevTools trace가 더 직접적이다.
- 모든 fetch를 `error`로 고정하려 한다. 정상적인 page-like fetch나 최종 리소스만 중요할 때는 `follow`가 더 단순하다.
- `follow`가 나쁘고 `error`가 항상 더 좋다고 생각한다. 핵심은 계약이다. redirect가 정상 흐름이면 `follow`가 맞고, 금지해야 할 흐름이면 `error`가 맞다.

## 실무에서 쓰는 모습

가장 흔한 비교 예시는 아래다.

| 호출 장면 | `follow`에서 보이는 것 | `manual`에서 보이는 것 | `error`에서 얻는 장점 |
|---|---|---|---|
| `fetch("/api/me")`가 인증 만료로 `/login`으로 감 | 최종 login HTML `200`, 또는 `response.url === "/login"` | `opaqueredirect`로 redirect 흔적만 보고 실제 `302`는 DevTools에서 확인 | API 계약 위반을 바로 실패로 처리해 숨은 성공 표면을 줄인다 |
| 폼 제출 후 결과 페이지 HTML을 받아도 되는 호출 | 최종 결과 페이지를 그대로 받는다 | 중간 redirect 추적에는 쓸 수 있으나 보통 과하다 | 실패로 보면 오히려 정상 UX를 깨뜨릴 수 있다 |
| redirect 버그를 재현 중인 디버깅 세션 | 마지막 도착지만 보여 준다 | redirect 존재를 분리해서 보기 쉽다 | 계약 위반 여부를 빨리 확인할 수 있다 |

safe next step도 이 기준으로 잡으면 된다.

1. 먼저 [Fetch Auth Failure Chooser: `401 JSON` vs `302 /login` vs 숨은 Login HTML `200`](./fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser.md)에서 지금 장면이 raw `401`, 첫 `302`, 숨은 login HTML `200` 중 무엇인지 고른다.
2. JSON/API 호출인데 redirect lane으로 확인되면 `error`로 숨은 login HTML 성공 표면을 없앤다.
3. 왜 redirect가 떴는지 추적해야 하면 그다음 `manual`과 DevTools Network 탭으로 실제 `302` row를 본다.
4. page redirect UX 자체를 이해해야 하면 login redirect primer로 돌아간다.

## 더 깊이 가려면

- raw `401 JSON`, 첫 `302 /login`, 숨은 login HTML `200`을 먼저 구분하려면 [Fetch Auth Failure Chooser: `401 JSON` vs `302 /login` vs 숨은 Login HTML `200`](./fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser.md)
- `follow`에서 `response.redirected`, `response.url`, `opaqueredirect`를 어떤 칸에서 읽는지 다시 고정하려면 [Fetch `response.redirected` vs `response.url` vs `opaqueredirect` 미니 카드](./fetch-redirected-response-url-opaqueredirect-mini-card.md)
- login redirect와 `SavedRequest`, hidden login HTML `200` 전체 흐름은 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- "`API가 HTML을 받아요`가 진짜 HTML endpoint인지 숨은 auth redirect인지"를 분리하려면 [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- browser redirect UX와 API auth failure 계약을 더 직접적으로 자르려면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)

## 한 줄 정리

`redirect: "error"`는 redirect를 더 자세히 보기 위한 옵션이 아니라, redirect가 오면 안 되는 API 계약을 가장 빠르게 실패로 드러내는 선택이다.
