---
schema_version: 3
title: "Browser DevTools 저장됨 vs 전송됨 vs 재사용됨 판독 드릴 3문제"
concept_id: network/browser-devtools-stored-sent-reused-tracing-drill
canonical: true
category: network
difficulty: intermediate
doc_role: drill
level: intermediate
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- devtools-stored-sent-reused
- browser-storage-request-header-cache
- intermediate-tracing-drill
aliases:
- stored vs sent vs reused drill
- application vs network tracing practice
- cookie stored but not sent drill
- localstorage token authorization drill
- cache storage vs 304 practice
- devtools storage request cache drill
symptoms:
- Application 탭에 cookie나 token이 보이면 request header에도 갔다고 단정한다
- Cache Storage entry 존재와 이번 row의 HTTP cache 304 재사용을 같은 증거로 읽는다
- 401을 보자마자 token 만료로 결론내고 Authorization header 전송 여부를 확인하지 않는다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- network/browser-devtools-application-storage-1minute-card
- network/browser-devtools-cache-trace-primer
next_docs:
- network/application-tab-vs-request-cookie-header-mini-card
- network/cookie-vs-localstorage-token-storage-choice-card
- network/service-worker-vs-http-cache-devtools-primer
- security/cookie-scope-mismatch-guide
linked_paths:
- contents/network/browser-devtools-application-storage-1minute-card.md
- contents/network/application-tab-vs-request-cookie-header-mini-card.md
- contents/network/browser-devtools-cache-trace-primer.md
- contents/network/service-worker-vs-http-cache-devtools-primer.md
- contents/network/cookie-vs-localstorage-token-storage-choice-card.md
- contents/security/cookie-scope-mismatch-guide.md
confusable_with:
- network/browser-devtools-application-storage-1minute-card
- network/application-tab-vs-request-cookie-header-mini-card
- network/browser-devtools-cache-trace-primer
- network/service-worker-vs-http-cache-devtools-primer
- network/cookie-vs-localstorage-token-storage-choice-card
forbidden_neighbors: []
expected_queries:
- "DevTools에서 저장됨 전송됨 재사용됨을 구분하는 연습 문제를 풀고 싶어"
- "Application에 cookie가 있는데 request Cookie header가 비는 장면을 드릴로 설명해줘"
- "localStorage token은 있는데 Authorization header가 없는 401을 어떻게 판독해?"
- "Cache Storage entry와 304 Not Modified를 섞지 않는 연습을 하고 싶어"
- "Application 탭과 Network 탭 증거를 한 줄씩 분리해서 읽는 법을 훈련해줘"
contextual_chunk_prefix: |
  이 문서는 DevTools Application stored evidence, Network request header
  sent evidence, 304/from cache/from ServiceWorker reused evidence를 세
  문제로 분리해 읽게 하는 intermediate drill 문서다.
---
# Browser DevTools 저장됨 vs 전송됨 vs 재사용됨 판독 드릴 3문제

> 한 줄 요약: `Application` 탭에서 저장된 것, `Network` 탭에서 실제 전송된 것, cache나 Service Worker로 재사용된 것을 같은 뜻으로 읽지 않게 만드는 3문제 추적 드릴이다.

**난이도: 🟡 Intermediate**

관련 문서:

- [Network README](./README.md#browser-devtools-저장됨-vs-전송됨-vs-재사용됨-판독-드릴-3문제)
- [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md)
- [Application 탭에는 Cookie가 보이는데 Request `Cookie` 헤더는 비는 이유 미니 카드](./application-tab-vs-request-cookie-header-mini-card.md)
- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md)
- [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)

retrieval-anchor-keywords: stored vs sent vs reused drill, application vs network tracing practice, devtools 저장됨 전송됨 재사용됨, cookie stored but not sent drill, localstorage token but no authorization drill, cache storage vs 304 practice, 처음 devtools 판독 연습, 왜 application 에는 있는데 요청엔 없어요, 왜 304 인데 body 가 보여요, stored sent reused beginner bridge, browser devtools practice intermediate, what is stored vs sent vs reused

## 먼저 잡는 멘탈 모델

이 드릴은 세 문장을 구분하는 연습이다.

- 저장됨 = 브라우저 안 어딘가에 값이나 응답이 남아 있다
- 전송됨 = 이번 요청에 실제 header나 body로 실렸다
- 재사용됨 = 이번 응답 body를 브라우저가 기존 사본에서 다시 썼다

여기서 비유는 "창고, 배송, 재고 재사용" 정도까지만 맞다. 실제 브라우저는 cookie scope, `credentials`, validator, Service Worker 같은 규칙으로 판단하므로, 저장돼 있다고 자동 전송되거나 재사용된다고 단정하면 안 된다.

## 한눈에 보는 판독표

| 지금 본 위치 | 먼저 붙일 라벨 | 아직 확정하면 안 되는 것 |
|---|---|---|
| `Application > Cookies` | 저장됨 후보 | 이번 요청 `Cookie` header 전송 |
| `Application > Local Storage` | 저장됨 후보 | `Authorization` header 조립 성공 |
| `Application > Cache Storage` | 저장됨 후보 | 이번 row가 그 entry를 실제로 사용함 |
| `Network > Request Headers` | 전송됨 증거 | 서버가 인증/처리를 성공했는지 |
| `Network > Status 304`, `from memory cache`, `from disk cache`, `from ServiceWorker` | 재사용됨 후보 | 저장소 종류와 인증 상태 |

짧게 줄이면 `Application = stored`, `Request Headers = sent`, `Status/Size/Waterfall = reused`다.

## 문제 1. Cookie는 저장됐는데 `/me` 요청에는 안 실린다

### 장면

- `Application > Cookies > https://api.example.com`에 `SID=abc`가 보인다
- 실패한 row는 `GET https://api.example.com/me`
- `Request Headers`에 `Cookie`가 없다
- 프런트 코드는 `fetch("https://api.example.com/me")`만 호출했다

### 질문

무엇이 **저장됨**, 무엇이 **전송 안 됨**, 첫 원인 후보는 무엇인가?

### 정답 판독

- 저장됨: `SID` cookie
- 전송 안 됨: 이번 `/me` 요청의 request `Cookie` header
- 첫 원인 후보: cross-origin `fetch`라면 `credentials: "include"` 누락, 아니면 `Domain`/`Path`/`SameSite`/`Secure` 불일치

### 왜 이 문제가 bridge인가

Beginner 단계에서는 "`Application`에 cookie가 있다"까지 읽는다. 여기서는 한 칸 더 가서 "같은 row의 request header에 없으니 저장 성공과 전송 성공을 분리해야 한다"를 몸에 익힌다.

## 문제 2. `localStorage`에 토큰은 있는데 API 요청은 `401`이다

### 장면

- `Application > Local Storage`에 `accessToken=eyJ...`가 있다
- 실패한 row는 `GET /api/orders`
- `Request Headers`에 `Authorization`이 없다
- 응답은 `401 Unauthorized`

### 질문

무엇이 **저장됨**, 무엇이 **전송 안 됨**, 초급자가 가장 먼저 멈춰야 할 오해는 무엇인가?

### 정답 판독

- 저장됨: 브라우저 `localStorage` 안의 access token 문자열
- 전송 안 됨: 이번 요청의 `Authorization` header
- 멈춰야 할 오해: "`localStorage`에 있으니 브라우저가 자동으로 보냈겠지"

`localStorage` 값은 cookie와 다르게 브라우저가 자동 전송하지 않는다. 프런트 코드가 직접 읽어서 header를 붙여야 한다. 그래서 이 장면의 첫 질문은 토큰 만료보다 먼저 "request interceptor나 fetch wrapper가 header를 실제로 조립했나"다.

## 문제 3. `Cache Storage`에도 있고 `304`도 보인다

### 장면

- `Application > Cache Storage`에 `/app.js` entry가 있다
- 같은 URL row가 `304 Not Modified`로 찍힌다
- request에는 `If-None-Match`가 있다
- row에는 `from ServiceWorker` 표시는 없다

### 질문

무엇이 **저장됨**, 무엇이 **재사용됨**, 무엇을 아직 섞으면 안 되는가?

### 정답 판독

- 저장됨: `Cache Storage` entry 하나가 존재한다는 사실
- 재사용됨: 이번 `304` row에서는 브라우저 HTTP cache의 기존 body를 재사용했을 가능성이 높다
- 아직 섞으면 안 되는 것: `Cache Storage` entry 존재와 이번 row의 body 출처

이 장면에서 확정 가능한 것은 "`304`와 validator가 있으니 서버에 재검증 후 기존 body를 계속 써도 된다고 확인했다"까지다. `from ServiceWorker`가 보이지 않는다면 Service Worker 경로라고 바로 단정하지 않는 편이 안전하다.

## 자주 틀리는 이유

| 잘못 붙이는 문장 | 왜 틀리나 | 더 안전한 문장 |
|---|---|---|
| "`Application`에 있으니 요청에도 갔다" | 저장과 전송은 다른 단계다 | "`Application`에는 있고, 이 요청 header에는 없다" |
| "`401`이니 토큰이 없거나 만료됐다" | 값 존재와 header 전송을 아직 안 봤다 | "`Authorization` header 유무부터 보자" |
| "`Cache Storage`에 있으니 `304`도 Service Worker 때문이다" | `304`는 HTTP cache 재검증 신호다 | "`304`와 `from ServiceWorker`는 따로 확인한다" |

이 드릴의 핵심은 "한 줄 결론을 너무 빨리 말하지 않는 습관"이다. 저장소 화면, request header, cache signal을 각자 한 줄씩 적으면 오진이 크게 줄어든다.

## 다음 한 걸음

- cookie 전송 조건을 더 정확히 자르고 싶으면 [Application 탭에는 Cookie가 보이는데 Request `Cookie` 헤더는 비는 이유 미니 카드](./application-tab-vs-request-cookie-header-mini-card.md)
- 토큰 저장 위치 선택까지 이어 가려면 [Cookie vs `localStorage` 토큰 저장 선택 카드](./cookie-vs-localstorage-token-storage-choice-card.md)
- `304`와 `from memory cache`를 더 정밀하게 읽으려면 [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- `Cache Storage`와 `from ServiceWorker`를 붙여 보고 싶으면 [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md)

## 한 줄 정리

DevTools 판독에서 `stored`, `sent`, `reused`를 같은 뜻으로 읽지 말고, `Application`, `Request Headers`, `Status/Size/Waterfall`를 각각 다른 증거 칸으로 분리하면 초급 오진이 크게 줄어든다.
