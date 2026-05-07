---
schema_version: 3
title: "Browser DevTools `OPTIONS` Preflight vs Actual Request Failure 미니 카드"
concept_id: network/browser-devtools-options-preflight-vs-actual-failure-mini-card
canonical: false
category: network
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 75
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- preflight-before-auth
- actual-request-presence
- cors-vs-auth-surface
aliases:
- devtools options preflight vs actual request
- options only vs actual request
- preflight blocked beginner
- options 401 not auth
- actual post 401 auth failure
- devtools cors preflight card
- 왜 options만 보여요
- actual request 안 보여요
- beginner devtools preflight
- preflight vs actual failure
- cors options first check
- what is preflight in devtools
symptoms:
- "Network 탭에 `OPTIONS`만 보이고 실제 `GET`이나 `POST`는 안 보여서 요청이 출발도 못 한 건지 모르겠다"
- "`OPTIONS 401`만 보고 인증 실패로 이해했는데 실제 요청이 아예 안 나간 건 아닌지 헷갈린다"
- 콘솔에는 CORS 에러가 뜨는데 actual request row가 있는지 없는지부터 어떻게 읽어야 할지 막힌다
intents:
- drill
prerequisites:
- network/cross-origin-cookie-credentials-cors-primer
- network/browser-devtools-first-checklist-1minute-card
next_docs:
- network/browser-devtools-error-path-cors-vs-actual-401-403-bridge
- security/preflight-debug-checklist
- network/fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser
linked_paths:
- contents/network/browser-devtools-blocked-mixed-content-vs-cors-mini-card.md
- contents/network/browser-devtools-error-path-cors-vs-actual-401-403-bridge.md
- contents/network/cross-origin-cookie-credentials-cors-primer.md
- contents/network/browser-devtools-first-checklist-1minute-card.md
- contents/security/preflight-debug-checklist.md
- contents/security/auth-failure-response-401-403-404.md
confusable_with:
- network/browser-devtools-blocked-mixed-content-vs-cors-mini-card
- network/fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser
- security/preflight-debug-checklist
forbidden_neighbors:
- contents/network/cross-origin-cookie-credentials-cors-primer.md
expected_queries:
- "preflight만 401이고 post는 아예 안 보일 때 어디서 끊긴 거야?"
- "Network 탭에 options만 있고 실제 요청이 없으면 무엇부터 확인해?"
- "CORS 에러가 뜨는데 actual api row가 안 찍히면 preflight 문제로 봐도 돼?"
- "options는 실패했는데 get/post가 안 나가는 상황을 devtools에서 어떻게 읽어?"
- "preflight 차단이랑 실제 인증 실패를 한 화면에서 구분하는 법이 뭐야?"
contextual_chunk_prefix: |
  이 문서는 학습자가 DevTools에서 `OPTIONS` preflight와 actual
  `GET`/`POST`를 구분하지 못해 CORS 차단과 실제 인증 실패를 섞을 때
  빠르게 분기하도록 돕는 network drill이다. options만 보임, actual
  request가 안 보임, preflight 401인지 auth 401인지 헷갈림, 콘솔은
  CORS인데 실제 row가 있나 같은 자연어 표현이 먼저 볼 증거 순서에
  매핑되도록 설계했다.
---
# Browser DevTools `OPTIONS` Preflight vs Actual Request Failure 미니 카드

> 한 줄 요약: DevTools에서 `OPTIONS`가 실패했다고 해서 곧바로 "API 요청이 실패했다"로 읽으면 자주 틀리고, 먼저 `actual GET/POST가 실제로 보이는지`부터 가르면 preflight 차단과 실제 인증/권한 실패를 분리할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools `(blocked)` Mixed Content vs CORS 미니 카드](./browser-devtools-blocked-mixed-content-vs-cors-mini-card.md)
- [Browser DevTools에서 CORS처럼 보이지만 actual `401`/`403`이 있는 경우: Error-Path CORS 브리지](./browser-devtools-error-path-cors-vs-actual-401-403-bridge.md)
- [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)
- [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- [Preflight Debug Checklist](../security/preflight-debug-checklist.md)
- [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: devtools options preflight vs actual request, options only vs actual request, preflight blocked beginner, options 401 not auth, actual post 401 auth failure, devtools cors preflight card, 왜 options만 보여요, actual request 안 보여요, beginner devtools preflight, preflight vs actual failure, cors options first check, what is preflight in devtools

## 핵심 개념

초급자가 가장 자주 섞는 문장은 이것이다.

- "`OPTIONS`가 `401`이니까 인증 실패네요"
- "콘솔에 CORS가 뜨니까 actual API도 실패했네요"

하지만 DevTools에서는 먼저 **실제 요청이 출발했는지**를 봐야 한다.

- `OPTIONS`만 있고 actual `GET`/`POST`가 없으면: preflight 확인 단계에서 막힌 것이다
- actual `GET`/`POST`가 보이면: 이제 그 actual request의 `401`/`403`을 읽어야 한다

짧게 외우면 아래 한 줄이면 된다.

```text
OPTIONS status보다 actual request 존재 여부를 먼저 본다
```

## 한눈에 보기

| DevTools에서 먼저 보이는 장면 | 초급자 첫 해석 | 지금 실패한 것 | 다음 문서 |
|---|---|---|---|
| `OPTIONS /api/orders`만 있고 `POST /api/orders`가 없다 | preflight 차단 후보 | actual 요청은 아직 안 나갔을 수 있다 | [Preflight Debug Checklist](../security/preflight-debug-checklist.md) |
| `OPTIONS` 뒤에 `POST /api/orders`가 있고, `POST`가 `401`이다 | preflight는 통과했고 actual auth failure를 봐야 한다 | actual 요청 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md) |
| `OPTIONS` 뒤에 actual `POST`도 있고 콘솔은 CORS 에러를 말한다 | actual failure가 error-path CORS에 가려졌을 수 있다 | actual 요청 + 응답 노출 | [Browser DevTools에서 CORS처럼 보이지만 actual `401`/`403`이 있는 경우: Error-Path CORS 브리지](./browser-devtools-error-path-cors-vs-actual-401-403-bridge.md), [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md) |
| request `Cookie`가 비어 있고 actual request는 보인다 | preflight보다 cookie/credentials 갈래가 먼저다 | actual 요청의 credential 전송 | [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md) |

## DevTools에서 읽는 순서

1. 같은 path에 `OPTIONS`가 있는지 본다.
2. 그 뒤에 actual `GET`/`POST`/`PUT` row가 실제로 생겼는지 본다.
3. actual row가 없으면 `OPTIONS` status를 preflight lane으로 읽는다.
4. actual row가 있으면 그 row의 `401`/`403`/`404`를 읽는다.
5. actual row가 `401`/`403`인데 콘솔은 CORS라고 하면 [Browser DevTools에서 CORS처럼 보이지만 actual `401`/`403`이 있는 경우: Error-Path CORS 브리지](./browser-devtools-error-path-cors-vs-actual-401-403-bridge.md)로 내려가고, auth 의미는 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md)에서 먼저 고정한다.

이 순서가 중요한 이유는, `OPTIONS 401`과 `POST 401`이 같은 질문에 답하지 않기 때문이다.

- `OPTIONS 401`: 브라우저의 허용 확인이 막혔을 수 있다
- `POST 401`: 실제 API 인증이 성립하지 않았을 수 있다

브라우저/프록시/보안 필터 설정에 따라 `OPTIONS`가 `200` 또는 `204`로 보이는 경우가 흔하지만, 구체적인 숫자는 제품과 설정에 따라 달라질 수 있다. beginner 관점에서는 **숫자보다 actual request 존재 여부**가 더 안전한 첫 단서다.

## 흔한 오해와 함정

- `OPTIONS 401`만 보고 bearer token이 틀렸다고 단정한다. actual 요청이 아직 안 나갔을 수 있다.
- 콘솔에 CORS가 보이면 actual request가 절대 안 갔다고 단정한다. actual request는 갔는데 응답 노출만 막힌 경우도 있다.
- actual `401`/`403` row가 보이는데도 계속 preflight lane으로만 읽는다. 이때는 auth lane과 error-path CORS lane을 같이 봐야 한다.
- `OPTIONS`와 `POST`를 같은 실패 row로 읽는다. 전자는 확인 단계, 후자는 실제 비즈니스 호출이다.
- request `Cookie`가 비어 있는 장면을 전부 preflight 탓으로 돌린다. actual request가 보이면 `credentials`나 cookie scope를 먼저 잘라야 할 수 있다.

헷갈리면 문장을 이렇게 고치면 된다.

- "인증 실패네요" 대신 "먼저 actual 요청이 있었는지 볼게요"
- "CORS라서 다 안 갔네요" 대신 "actual row가 있는지부터 확인할게요"

## 실무에서 쓰는 모습

프런트에서 아래처럼 cross-origin JSON 요청을 보낸다고 하자.

```js
fetch("https://api.example.com/orders", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer ..."
  },
  body: JSON.stringify({ itemId: 1 })
});
```

DevTools에서 두 장면을 구분해야 한다.

| 장면 | Network에 보이는 것 | 첫 결론 |
|---|---|---|
| A | `OPTIONS /orders` `401`, actual `POST /orders` 없음 | actual 주문 요청은 아직 안 나갔다. preflight 차단부터 본다 |
| B | `OPTIONS /orders` `204`, `POST /orders` `401` | preflight는 통과했다. 이제 actual 인증 실패를 본다 |

비유로는 "`OPTIONS`는 출입구에서 규칙 확인, actual request는 실제 입장"이라고 볼 수 있다. 다만 이 비유는 입문용일 뿐이고, 실제 원인은 브라우저 CORS 처리, 프록시, 보안 필터 설정처럼 여러 층에 있을 수 있다.

## 더 깊이 가려면

- preflight 응답 헤더와 `OPTIONS` 허용 여부를 더 자세히 보려면 [Preflight Debug Checklist](../security/preflight-debug-checklist.md)
- actual `401`/`403`의 의미를 auth/authz 관점에서 가르려면 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md)
- actual `401`/`403`이 있는데 콘솔은 CORS를 말하는 중간 장면을 DevTools 증거 순서로 다시 읽으려면 [Browser DevTools에서 CORS처럼 보이지만 actual `401`/`403`이 있는 경우: Error-Path CORS 브리지](./browser-devtools-error-path-cors-vs-actual-401-403-bridge.md)
- cookie, `credentials`, CORS를 같은 지도에서 다시 잡으려면 [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)
- `(blocked)`와 콘솔 문구를 먼저 자르고 싶다면 [Browser DevTools `(blocked)` Mixed Content vs CORS 미니 카드](./browser-devtools-blocked-mixed-content-vs-cors-mini-card.md)

## 한 줄 정리

DevTools에서 `OPTIONS` 실패를 봤을 때는 status 숫자보다 먼저 actual `GET`/`POST` row가 실제로 존재하는지 확인해야 preflight 차단과 실제 API 실패를 분리할 수 있다.
