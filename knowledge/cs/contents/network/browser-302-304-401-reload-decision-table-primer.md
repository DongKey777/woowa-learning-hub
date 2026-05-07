---
schema_version: 3
title: Browser 302 vs 304 vs 401 새로고침 분기표
concept_id: network/browser-302-304-401-reload-decision-table-primer
canonical: true
category: network
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 93
mission_ids:
- missions/spring-roomescape
- missions/shopping-cart
- missions/backend
review_feedback_tags:
- browser-reload-status-debugging
- redirect-cache-auth-triage
- devtools-network-reading
aliases:
- browser 302 304 401 reload
- 302 vs 304 vs 401
- 새로고침 302 304 401
- Location vs If-None-Match
- login redirect vs cache revalidation
- final html 200 hides 302
- DevTools reload decision table
symptoms:
- 새로고침 뒤 302, 304, 401을 모두 비슷한 재요청으로 읽고 있어
- 304를 redirect처럼 해석하거나 302를 cache 문제로 보고 있어
- fetch가 login HTML 200을 받아 API 성공처럼 보이는 장면에서 원래 302를 놓치고 있어
intents:
- troubleshooting
- comparison
prerequisites:
- network/http-status-codes-basics
- network/http-request-response-headers-basics
next_docs:
- network/redirect-vs-forward-vs-spa-navigation-basics
- network/http-caching-conditional-request-basics
- security/browser-401-vs-302-login-redirect-guide
- network/browser-devtools-reload-hard-reload-disable-cache-primer
linked_paths:
- contents/network/http-status-codes-basics.md
- contents/network/redirect-vs-forward-vs-spa-navigation-basics.md
- contents/network/post-redirect-get-prg-beginner-primer.md
- contents/network/browser-devtools-reload-hard-reload-disable-cache-primer.md
- contents/network/http-caching-conditional-request-basics.md
- contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md
- contents/network/http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md
- contents/security/browser-401-vs-302-login-redirect-guide.md
confusable_with:
- network/redirect-vs-forward-vs-spa-navigation-basics
- network/http-caching-conditional-request-basics
- security/browser-401-vs-302-login-redirect-guide
- network/post-redirect-get-prg-beginner-primer
forbidden_neighbors: []
expected_queries:
- 새로고침 뒤 302, 304, 401이 보이면 DevTools에서 무엇부터 봐야 해?
- 302와 304를 Location 헤더와 validator로 어떻게 구분해?
- 401은 브라우저가 자동으로 login redirect를 하는 상태 코드야?
- fetch가 login HTML 200을 받았는데 API 성공이 아닐 수 있는 이유는 뭐야?
- POST 303 GET 304 흐름에서 303과 304는 각각 어떤 질문이야?
contextual_chunk_prefix: |
  이 문서는 browser reload symptom chooser로, 302 redirect, 304 cache revalidation, 401 auth failure를 Location header, validator header, auth header 기준으로 분기한다.
  새로고침 뒤 login으로 이동, 같은 URL 304, raw 401, final login HTML 200 hides 302 같은 자연어 질문이 본 문서에 매핑된다.
---
# Browser `302` vs `304` vs `401` 새로고침 분기표

> 한 줄 요약: page reload 뒤 DevTools에 `302`, `304`, `401`이 보일 때는 "다른 URL로 이동시키는가, 기존 body를 다시 쓰는가, 인증 안 됐다고 멈추는가"를 먼저 갈라 읽으면 덜 헷갈린다.

**난이도: 🟢 Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "새로고침했더니 302, 304, 401이 다 보여서 같은 재요청처럼 보여요" | 로그인 후 예약 목록, 장바구니 페이지 새로고침 | redirect, cache 재검증, 인증 실패를 상태 코드별로 분리한다 |
| "fetch는 200인데 응답 body가 로그인 HTML이라 API 성공인지 모르겠어요" | 세션 만료 뒤 AJAX 요청 | 최종 200 뒤에 숨은 302 login redirect 여부를 DevTools row로 확인한다 |
| "304를 redirect처럼 보고 캐시 문제와 로그인 문제를 섞고 있어요" | browser reload trace 판독 | `Location`, validator, auth header 중 무엇이 먼저 보이는지 자른다 |

관련 문서:

- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md)
- [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)
- [Browser DevTools 새로고침 분기표: normal reload, hard reload, empty cache and hard reload](./browser-devtools-reload-hard-reload-disable-cache-primer.md)
- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [HTTP 캐시 재사용 vs 연결 재사용 vs 세션 유지 입문](./http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md)
- [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: browser 302 vs 304 vs 401, reload decision table, devtools redirect vs revalidation, page reload login redirect, 304 revalidation beginner, 401 unauthorized beginner, location header vs if-none-match, same url different next request, 새로고침했는데 로그인으로 가요, 처음 배우는데 302 304 401 차이, fetch redirect follow login html 200, devtools final 200 hides 302 login, xhr login html instead of json

## 핵심 개념

초급자가 가장 많이 섞는 이유는 셋 다 "새로고침 뒤 뭔가 한 번 더 일어났다"처럼 보이기 때문이다.

- `302`는 브라우저가 **다른 URL로 한 번 더 가게 만드는 신호**다.
- `304`는 브라우저가 **기존 cache body를 계속 쓰게 만드는 신호**다.
- `401`은 서버가 **지금 인증이 안 됐다고 직접 말하는 신호**다.

즉 셋은 같은 종류의 상태 코드가 아니다.

- `302`: 다음 목적지를 바꾼다
- `304`: body를 다시 받을지 말지를 바꾼다
- `401`: 로그인/인증 해석을 요구한다

이 문서를 읽을 때 beginner가 한 줄만 더 기억하면 훨씬 덜 섞인다.

- `302`는 **다른 URL** 질문이다.
- `304`는 **같은 URL body 재사용** 질문이다.
- `401`은 **이동이 아니라 인증 실패** 질문이다.

새로고침 뒤 follow-up decision을 한 줄로 외우면 이렇다.

- `302`면 `Location`을 본다
- `304`면 validator를 본다
- `401`이면 redirect가 아니라 auth failure인지 본다

## 한눈에 보기

| status | 브라우저의 바로 다음 동작 | DevTools에서 먼저 보는 칸 | 초급자 첫 해석 |
|---|---|---|---|
| `302 Found` | `Location`을 따라 다음 URL로 이동 요청을 만든다 | 첫 row의 `Status`, `Response Headers > Location`, 다음 row URL | redirect다. "같은 페이지를 다시 읽은 것"보다 "다른 URL로 보냈다"에 가깝다 |
| `304 Not Modified` | 기존 cache body를 재사용한다 | 같은 URL row, `Request Headers > If-None-Match` 또는 `If-Modified-Since`, `Location` 없음 | revalidation이다. 서버 왕복은 있었지만 body는 다시 안 받았다 |
| `401 Unauthorized` | HTTP 자체로는 자동 이동하지 않는다 | `Status 401`, `Location` 없음, 필요하면 `WWW-Authenticate` | raw unauthenticated다. 그다음 login 화면 이동은 앱이나 브라우저 UX 정책이 덧씌운 결과일 수 있다 |

같은 reload에서 초급자가 가장 먼저 버려야 할 오해는 이것이다.

- `302`를 보면 곧바로 cache 문제라고 생각한다
- `304`를 보면 redirect 한 번 탄 것처럼 읽는다
- `401`을 보면 항상 브라우저가 자동으로 `/login`으로 간다고 생각한다

## DevTools에서 먼저 볼 4칸

새로고침 뒤 Network 탭을 볼 때는 아래 4칸만 먼저 확인하면 된다.

| 확인 칸 | `302`일 때 보이는 것 | `304`일 때 보이는 것 | `401`일 때 보이는 것 |
|---|---|---|---|
| `Status` | `302` | `304` | `401` |
| `Response Headers` | `Location`이 핵심 | `ETag`, `Last-Modified`, `Cache-Control`이 핵심 | `WWW-Authenticate` 또는 auth error body가 힌트 |
| `Request Headers` | 다음 요청에서 `Cookie`가 실렸는지 같이 볼 수 있다 | `If-None-Match`, `If-Modified-Since`가 보이기 쉽다 | `Cookie`, `Authorization`이 비었는지 본다 |
| 다음 row | URL이 바뀌거나 `/login` 같은 후속 요청이 이어진다 | 보통 같은 URL이고 cached body를 다시 쓴다 | raw `401`이면 후속 row가 없을 수 있고, 앱이 처리하면 별도 login 요청이 생길 수 있다 |

짧은 판독 규칙:

1. 다음 row URL이 바뀌면 `302`부터 의심한다.
2. 같은 URL이고 validator가 보이면 `304`부터 의심한다.
3. `Location`이 없고 `401`이면 redirect보다 auth failure부터 읽는다.

## `POST -> 303 -> GET -> 304`와는 어떻게 다를까

새로고침 문서에서 beginner가 자주 묻는 follow-up은 "`그럼 `303`은 왜 여기 표에 없어요?`"다. 이유는 간단하다. 이 문서는 **reload 뒤 보인 `302`/`304`/`401`을 먼저 자르는 문서**이고, `303`은 보통 form submit 마무리인 PRG 흐름에서 먼저 등장한다.

| 지금 장면 | 먼저 붙일 이름 | 다음 문서 |
|---|---|---|
| 새로고침 뒤 `/login`으로 이동 | `302` reload/redirect 장면 | [HTTP 상태 코드 기초](./http-status-codes-basics.md) |
| 새로고침 뒤 같은 URL `304` | cache revalidation 장면 | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) |
| 제출 직후 `POST -> 303 -> GET` | PRG 장면 | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) |

짧게 말하면 `303`은 "`왜 `POST` 다음에 `GET`이 보여요?`"를 푸는 문서로 보내고, 이 문서는 "`새로고침 뒤 왜 `/login`, `304`, `401`이 보여요?`"를 푸는 entry다.

## 페이지 새로고침에서 자주 보는 세 장면

### 1. 새로고침했더니 `/login`으로 간다

```text
GET /orders/42   -> 302 Found
Location: /login
GET /login       -> 200 OK
```

이 장면은 cache보다 redirect 흐름이 먼저다.
질문은 "`304`였나?"가 아니라 "왜 보호 페이지가 login redirect를 탔나?"다.

### 2. 새로고침했더니 같은 URL이 `304`다

```text
GET /app.js
If-None-Match: "v7"

304 Not Modified
```

이 장면은 다른 곳으로 간 것이 아니라, 같은 URL을 재검증한 뒤 기존 body를 다시 쓴 것이다.
질문은 "왜 login으로 갔나?"가 아니라 "이 리소스가 왜 revalidation 대상이었나?"다.

### 3. 새로고침했더니 raw `401`이 보인다

```text
GET /api/me -> 401 Unauthorized
```

이 장면은 HTTP가 인증 실패를 직접 말한 것이다.
브라우저 page UX에서 `/login`으로 보내는 경우와 달리, 여기서는 `Location`이 없을 수 있다.

초급자용 한 줄 비교:

- `/login`으로 이어지면 `302`
- 같은 URL cached body 재사용이면 `304`
- 에러로 멈추면 `401`

## 흔한 오해와 함정

### `401`과 `302 -> /login`을 같은 뜻으로 말한다

비슷한 상황에서 나올 수는 있지만 같은 장면은 아니다.

- raw `401`은 서버의 직접 응답이다
- `302 -> /login`은 browser navigation이 한 번 더 붙은 모습이다

### `304`를 "서버가 다른 페이지를 줬다"로 읽는다

아니다.
`304`는 새 body를 안 보낸 것이다.
브라우저는 기존 cache 사본을 다시 쓴다.

### redirect row와 최종 row를 섞어 본다

Network 탭에서는 `302` row와 그다음 `200` row를 분리해서 봐야 한다.
최종 row만 보면 "왜 갑자기 login HTML `200`이 왔지?"처럼 보일 수 있다.

`fetch`/XHR에서도 같은 함정이 있다.
브라우저가 redirect를 따라간 뒤 최종 `/login` HTML `200`만 코드나 DevTools에 먼저 보일 수 있어서, 원래 API가 `302`였다는 사실을 놓치기 쉽다.

### page 요청과 API 요청을 같은 기준으로 읽는다

page 요청은 `302 -> /login` UX가 흔하고, API 요청은 raw `401` 계약이 더 흔하다.
같은 새로고침이어도 어떤 URL을 다시 불렀는지 먼저 봐야 한다.

## 더 깊이 가려면

- 새로고침 종류 자체가 헷갈리면 [Browser DevTools 새로고침 분기표: normal reload, hard reload, empty cache and hard reload](./browser-devtools-reload-hard-reload-disable-cache-primer.md)
- `304`의 validator와 cache policy를 더 자세히 보려면 [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- `302` login redirect와 `SavedRequest` 복귀를 이어서 보려면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- `fetch`/XHR가 숨은 `302 -> /login -> 200 HTML`을 어떻게 final response처럼 보이게 하는지 이어서 보려면 [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- raw `401`과 browser `302 /login` UX 차이를 더 정확히 보려면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)

## 면접/시니어 질문 미리보기

**Q. `304`는 에러인가요?**
아니다. cache revalidation 결과로 기존 body를 계속 써도 된다는 뜻이다.

**Q. 브라우저에서 `401`이면 항상 `/login`으로 redirect되나요?**
아니다. HTTP 자체는 redirect를 강제하지 않는다. `/login` 이동은 앱이나 보안 설정이 덧붙이는 흐름일 수 있다.

**Q. `302`와 `304`를 가장 빠르게 구분하는 방법은 무엇인가요?**
`Location`이 있으면 `302` 쪽, validator와 같은 URL 재검증이면 `304` 쪽부터 본다.

## 한 줄 정리

새로고침 뒤 `302`는 "다른 URL로 가라", `304`는 "기존 body를 계속 써라", `401`은 "지금 인증이 안 됐다"이므로 DevTools에서 `Location`, validator, auth header를 같은 순서로 보면 된다.
