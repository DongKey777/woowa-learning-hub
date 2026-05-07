---
schema_version: 3
title: "API Gateway Auth Failure Surface Map: 401/403, 302, Login HTML"
concept_id: network/api-gateway-auth-failure-surface-map
canonical: false
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 90
mission_ids:
- missions/spring-roomescape
- missions/shopping-cart
- missions/backend
review_feedback_tags:
- gateway-auth-failure
- login-html-200
- response-surface-map
aliases:
- API gateway auth failure map
- gateway 401 vs app 401
- gateway 403 vs app 403
- raw 401 JSON vs login HTML 200
- raw 401 vs 302 login
- API got login HTML
- final HTML 200 not API success
symptoms:
- API 스펙의 raw 401/403과 브라우저에서 보이는 302 login redirect 또는 최종 login HTML 200을 서로 모순된 결과로 읽는다
- fetch/XHR이 redirect를 따라가 마지막 login page 200만 받았는데 API 성공으로 오해한다
- gateway local reply/rewrite와 upstream pass-through를 구분하지 않아 누가 auth failure 표면을 바꿨는지 추적하지 못한다
intents:
- symptom
- troubleshooting
prerequisites:
- network/http-status-codes-basics
- network/browser-devtools-response-body-ownership-checklist
next_docs:
- network/ssr-view-render-vs-json-api-response-basics
- network/proxy-local-reply-vs-upstream-error-attribution
- security/browser-401-vs-302-login-redirect-guide
linked_paths:
- contents/network/http-status-codes-basics.md
- contents/network/browser-devtools-response-body-ownership-checklist.md
- contents/network/ssr-view-render-vs-json-api-response-basics.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/proxy-local-reply-vs-upstream-error-attribution.md
- contents/security/browser-401-vs-302-login-redirect-guide.md
- contents/spring/spring-api-401-vs-browser-302-beginner-bridge.md
confusable_with:
- network/browser-devtools-response-body-ownership-checklist
- network/ssr-view-render-vs-json-api-response-basics
- network/proxy-local-reply-vs-upstream-error-attribution
- security/browser-401-vs-302-login-redirect-guide
forbidden_neighbors: []
expected_queries:
- API는 401 JSON이어야 하는데 브라우저에서는 login HTML 200이 오는 이유는?
- Gateway auth failure가 raw 401 403, 302 login, final HTML 200으로 다르게 보일 수 있어?
- final HTML 200은 API success가 아니라 redirect를 따라간 login page일 수 있다는 걸 설명해줘
- gateway가 만든 401과 app이 만든 401을 DevTools와 로그에서 어떻게 구분해?
- API Gateway auth failure surface를 결정 층 표면 층 호출자 층으로 나눠줘
contextual_chunk_prefix: |
  이 문서는 API Gateway 앞단 auth failure가 raw 401/403 JSON, 302 login redirect,
  final login HTML 200으로 다르게 표면화되는 증상을 라우팅한다. 결정 주체, 표면 변환,
  호출자 종류를 분리해 gateway local reply와 upstream pass-through를 구분한다.
---
# API Gateway Auth Failure Surface Map: `401`/`403`, `302`, Login HTML 구분 입문

> 한 줄 요약: gateway 앞단의 auth 거절은 raw API 계약으로 `401`/`403` JSON이 그대로 보일 수도 있고, 브라우저 UX나 프록시 rewrite가 끼면서 `302 -> /login` 또는 최종 login HTML `200`처럼 번역돼 보일 수도 있으니, 먼저 "누가 거절했고 누가 표면을 바꿨는가"를 분리해서 읽어야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
- [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](../spring/spring-api-401-vs-browser-302-beginner-bridge.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: api gateway auth failure map, gateway 401 vs app 401, gateway 403 vs app 403, raw 401 json vs login html 200, raw 401 vs 302 login, api got login html 200, fetch got login html 200, fetch auth failure html instead of json, final 200 login page after auth failure, final html 200 != api success, proxy rewrite auth response, browser redirect hides 401, edge auth reject beginner, 왜 api가 html을 받아요, gateway local reply auth

## 핵심 개념

초보자가 가장 많이 섞는 장면은 이것이다.

- API 문서에는 `401` 또는 `403`이라고 적혀 있다
- 브라우저에서는 `/login`으로 튄다
- DevTools 마지막 줄은 login HTML `200`처럼 보인다
- gateway 로그에는 auth reject가 먼저 남아 있다

이 네 장면은 서로 모순이 아닐 수 있다.
하나의 요청을 서로 다른 층이 다르게 보여 준 것일 수 있다.

먼저 3층으로 나누면 덜 헷갈린다.

1. **결정 층**: 누가 막았는가
   gateway auth filter인지, upstream API인지
2. **표면 층**: 밖으로 어떤 모양으로 보였는가
   raw `401`, raw `403`, `302 -> /login`, final login HTML `200`
3. **호출자 층**: 누가 그 응답을 받았는가
   브라우저 page인지, `fetch`/XHR인지, 모바일 앱인지

핵심은 "`401`이 맞냐 `302`가 맞냐"가 아니다.
"**원래 auth 결정**"과 "**사용자가 본 최종 표면**"을 분리해서 읽는 것이 먼저다.

## 한눈에 보기

| 지금 보이는 표면 | 초보자용 첫 해석 | 실제 auth 결정이 있었을 가능성 | 먼저 확인할 것 |
|---|---|---|---|
| raw `401 Unauthorized` + JSON body | 인증 정보가 없거나 만료됐다고 직접 말한 것이다 | gateway 또는 API 둘 다 가능 | `Content-Type`, JSON 에러 body, gateway access log, upstream access log |
| raw `403 Forbidden` | 인증은 됐지만 권한이 없다고 직접 말한 것이다 | gateway 또는 API 둘 다 가능 | role/scope 체크 위치, gateway policy, app authz log |
| `302 Found` + `Location: /login` | browser UX가 auth failure를 login 이동으로 감쌌다 | 원래는 `401` 계열 판단이었을 가능성이 크다 | page 요청인지, API 요청인지, redirect owner |
| 최종 login HTML `200 OK` | 성공이 아니라 hidden redirect 결과일 수 있다 | 앞에서 `302 -> /login` 또는 auth rewrite가 있었을 수 있다 | 최종 URL, redirect 체인, `Content-Type: text/html` |
| 같은 `/api/**` 호출이 어떤 때는 raw `401` JSON, 어떤 때는 login HTML `200` | auth 실패 원인은 비슷하지만 표면 계약이 달라졌다 | API client에는 raw `401`, 브라우저 fetch에는 redirect follow가 섞였을 수 있다 | 호출자가 브라우저인지 `curl`인지, 첫 응답 status, redirect follow 여부 |

짧게 외우면 이렇다.

- raw `401/403`은 **계약이 바로 보인 표면**
- `302`는 **브라우저 이동 UX가 끼어든 표면**
- login HTML `200`은 **redirect를 따라간 마지막 도착점**
- 초보자 handoff는 `final HTML 200 != API success`
- "`API got login HTML 200` vs `raw 401 JSON`"은 서로 다른 장애 둘이라기보다, 같은 auth 실패가 다른 호출자 계약으로 번역된 경우부터 의심한다

## 상세 분해

### 1. raw `401`과 raw `403`은 "누가 막았는지"가 아직 안 보인다

초보자는 `401`을 보면 곧바로 "앱이 거절했구나"라고 읽기 쉽다.
하지만 gateway도 `401`/`403`을 직접 만들 수 있다.

예를 들어:

- gateway가 JWT 검증 실패로 `401`
- gateway가 scope 부족으로 `403`
- upstream API가 세션 만료로 `401`
- upstream API가 역할 부족으로 `403`

즉 숫자만 같다고 source가 같은 것은 아니다.

### 2. browser page 요청은 raw `401` 대신 `302 /login`으로 감싸 보이기 쉽다

브라우저 page 요청에서는 "에러 메시지 표시"보다 "로그인 화면으로 이동" UX가 더 자연스럽다.

그래서 같은 auth failure라도:

- API 클라이언트에는 raw `401`
- 브라우저 page에는 `302 -> /login`

처럼 갈라져 보일 수 있다.

이때 `302`는 auth 의미를 없앤 것이 아니라, auth 실패를 **이동 지시로 번역한 표면**에 가깝다.

### 3. `fetch`/XHR는 최종 login HTML `200`만 보여 줄 수 있다

브라우저가 redirect를 자동으로 따라가면 아래처럼 보일 수 있다.

```text
GET /api/me      -> 302 Found
Location: /login
GET /login       -> 200 OK
Content-Type: text/html
```

프론트 코드나 DevTools에서 마지막 줄만 먼저 보면:

- "API가 `200` 성공했네"
- "왜 JSON 대신 HTML이 오지?"

처럼 읽기 쉽다.

하지만 실제 의미는 "API 성공"보다 "**auth failure 뒤 login page로 이동했다**"에 더 가깝다.

## beginner symptom bridge

### 4. "`API got login HTML 200` vs `raw 401 JSON`"은 같은 query family로 묶어 본다

입문자가 실제로 던지는 질문은 대개 둘 중 하나다.

- "`curl`에서는 `401` JSON인데 브라우저에서는 login HTML `200`이 와요"
- "`API가 왜 HTML을 줘요?`"

이 둘은 따로따로 외우기보다 한 symptom family로 묶는 편이 빠르다.

| learner symptom | 먼저 붙일 해석 | safe next doc |
|---|---|---|
| `curl`/Postman에서는 raw `401` JSON | API 계약이 직접 보인다 | [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](../spring/spring-api-401-vs-browser-302-beginner-bridge.md) |
| 브라우저 `fetch`에서는 login HTML `200` | redirect follow 뒤 마지막 login page를 받은 것일 수 있다 | [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md) |
| 같은 엔드포인트인데 브라우저와 API client 표면이 다르다 | auth 원인보다 호출자 계약 차이를 먼저 의심한다 | 이 문서 -> 위 두 문서 순서로 분기 |

초급자 mental model은 한 줄이면 충분하다.

- raw `401` JSON은 "실패 사실이 직접 보이는 표면"
- login HTML `200`은 "실패 뒤 이동한 도착점"

그래서 `200`이라는 숫자만 보고 success로 읽으면 오진이 커진다.

첫 질문이 "`왜 auth 실패가 HTML로 보이지?`"라면 [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)부터 보고,
"`이 HTML이 login redirect 때문인지, gateway/app owner가 누구인지`"를 더 가르려면 [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)를 바로 붙이면 된다.

## gateway가 표면을 바꾸는 방식

### 5. gateway rewrite와 upstream 응답 pass-through를 따로 봐야 한다

gateway는 크게 두 방식으로 auth 실패를 밖으로 보낼 수 있다.

| 방식 | 무슨 뜻인가 | 초보자용 감각 |
|---|---|---|
| pass-through | upstream이 만든 `401/403`을 거의 그대로 전달 | app 계약이 바깥까지 보인다 |
| local reply / rewrite | gateway가 직접 `401/403`을 만들거나 `302` 등으로 바꾼다 | edge 정책이 바깥 표면을 결정한다 |

그래서 "API 스펙에는 `401`인데 브라우저에서는 `/login`으로 간다"는 말은 틀린 관찰이 아니다.
단지 raw 계약 위에 browser/gateway 표면 번역이 한 겹 더 있는 것이다.

### 6. `401`과 `403`의 beginner 기준은 먼저 유지하고, source는 그다음에 본다

헷갈릴 때도 기본 뜻은 유지하는 편이 안전하다.

- `401`: 아직 인증이 안 됨
- `403`: 인증은 됐지만 권한이 안 됨

그 다음에만 source를 붙인다.

- gateway가 만든 `401`인가
- app이 만든 `401`인가
- gateway가 만든 `403`인가
- app이 만든 `403`인가

이 순서를 바꾸면 "`302`를 보았으니 `403`는 아닌가?" 같은 불필요한 혼동이 커진다.

## 흔한 오해와 함정

- `302 /login`을 보면 raw `401`이 없었다고 생각한다.
  실제로는 auth failure가 browser UX redirect로 번역됐을 수 있다.

- 최종 login HTML `200`을 보면 API 성공으로 읽는다.
  redirect follow 뒤 마지막 page 응답만 본 것일 수 있다.

- gateway 로그에 `401`이 있으니 upstream은 절대 안 봐도 된다고 생각한다.
  pass-through인지 local reply인지 먼저 구분해야 한다.

- `403`이 보이면 무조건 앱 권한 로직 문제라고 생각한다.
  gateway policy, scope filter, WAF/edge authz도 `403`을 만들 수 있다.

- page 요청과 API 요청을 같은 기대 계약으로 읽는다.
  page는 login 이동 UX가 흔하고, API는 raw `401/403` 계약이 더 흔하다.

## 실무에서 쓰는 모습

가장 단순한 20초 판독 순서는 아래다.

| 순서 | 지금 볼 것 | 왜 먼저 보나 |
|---|---|---|
| 1 | 요청이 page인지 `/api/**` 같은 data 요청인지 | browser redirect UX가 자연스러운지 먼저 가른다 |
| 2 | 첫 응답 status와 `Location` | raw `401/403`인지, `302 /login`인지 바로 갈린다 |
| 3 | 최종 응답 URL과 `Content-Type` | login HTML `200`이 hidden redirect 결과인지 본다 |
| 4 | gateway 로그에 upstream 미도달인지, local reply인지 | edge가 표면을 만들었는지 app이 만들었는지 좁힌다 |
| 5 | upstream app 로그 존재 여부 | pass-through인지 edge-generated인지 더 분리한다 |

특히 "`API got login HTML 200` vs `raw 401 JSON`" query family는 2번과 3번만 정확히 봐도 절반은 정리된다.

- 첫 응답이 raw `401` JSON이면 API 계약 쪽이다.
- 첫 응답이 `302 /login`이고 마지막이 HTML `200`이면 browser redirect 쪽이다.

짧은 예시는 아래처럼 읽는다.

| 장면 | 더 안전한 해석 |
|---|---|
| 브라우저 주소창으로 `/orders` 진입 후 `302 -> /login` | page auth failure를 login UX로 감싼 장면일 수 있다 |
| `fetch('/api/me')` 결과가 login HTML `200` | API 성공이 아니라 숨은 redirect 뒤 login page 도착일 수 있다 |
| 모바일 앱이 raw `401`을 받음 | 브라우저 UX 없이 auth 계약이 그대로 드러난 장면일 수 있다 |
| 같은 엔드포인트를 브라우저에서는 `/login`, `curl`에서는 `401`로 봄 | 호출자에 따라 표면이 다르게 번역된 것이다 |

## 더 깊이 가려면

- `401`/`403`/`302` 기본 계약부터 다시 잡으려면 [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- "`왜 JSON 대신 login HTML이 보이지?`"를 먼저 자르려면 [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- DevTools에서 login HTML, gateway JSON, app JSON owner를 먼저 가르려면 [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- login HTML `200`이 hidden redirect 결과로 보이는 흐름은 [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- browser redirect와 cookie/session 분기는 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- gateway가 직접 응답을 만들었는지 blame을 더 정확히 가르려면 [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- gateway와 reverse proxy의 auth/rate-limit 책임 경계는 [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)

## 면접/시니어 질문 미리보기

**Q. 브라우저에서는 `/login`으로 가는데 API 문서에는 왜 `401`이라고 적혀 있나요?**
raw auth 계약은 `401`인데, browser page UX나 gateway rewrite가 그 실패를 `302 /login`으로 감싸 보여 줄 수 있기 때문이다.

**Q. 최종 응답이 login HTML `200`이면 성공인가요?**
아니다. 앞단의 `302`를 따라간 마지막 도착점일 수 있어서, 원래 API 계약은 실패였을 가능성이 있다.

**Q. `403`은 항상 애플리케이션 권한 로직이 만든 것인가요?**
아니다. gateway나 edge policy도 `403`을 만들 수 있으므로, upstream pass-through인지 local reply인지 먼저 본다.

## 한 줄 정리

gateway auth 실패를 읽을 때는 raw `401/403` 계약, browser의 `302 /login` UX, redirect 뒤 login HTML `200`을 같은 층으로 섞지 말고 "누가 막았고 누가 표면을 바꿨는가" 순서로 분리하면 된다.
