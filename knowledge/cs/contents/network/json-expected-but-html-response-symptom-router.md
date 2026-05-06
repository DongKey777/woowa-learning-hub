---
schema_version: 3
title: JSON 기대했는데 HTML 응답이 옴 원인 라우터
concept_id: network/json-expected-but-html-response-symptom-router
canonical: false
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/roomescape
review_feedback_tags:
- response-owner-attribution
- final-url-vs-body-owner
- accept-vs-content-type
aliases:
- json 대신 html 응답
- api가 html을 받아요
- accept json인데 html 옴
- login html 200이 와요
- gateway html 응답
- 응답이 html 페이지로 와요
- body가 doctype html로 시작해요
symptoms:
- fetch나 axios로 API를 호출했는데 JSON 대신 login HTML이나 에러 HTML이 내려온다
- Accept는 application/json인데 Response Content-Type이 text/html로 보인다
- DevTools에서는 200처럼 보이는데 body를 열어 보니 로그인 페이지나 Bad Gateway HTML이다
- response preview 첫 줄이 `<!DOCTYPE html>`이나 `<html`로 시작해서 JSON 파싱 전에 이미 이상하다
- Postman에서는 JSON인데 브라우저 fetch에서는 HTML이 와서 인증·쿠키 문제인지 헷갈린다
intents:
- symptom
- troubleshooting
prerequisites:
- network/http-status-codes-basics
- network/http-request-response-headers-basics
next_docs:
- security/browser-401-vs-302-login-redirect-guide
- security/cookie-scope-mismatch-guide
- network/request-timing-decomposition
- network/devtools-waterfall-primer
linked_paths:
- contents/network/browser-devtools-response-body-ownership-checklist.md
- contents/network/gateway-json-vs-app-json-tiny-card.md
- contents/network/cdn-error-html-vs-app-json-decision-card.md
- contents/network/browser-devtools-502-504-app-500-decision-card.md
- contents/network/ssr-view-render-vs-json-api-response-basics.md
- contents/network/cross-origin-cookie-credentials-cors-primer.md
- contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md
- contents/security/fetch-credentials-vs-cookie-scope.md
- contents/security/cookie-scope-mismatch-guide.md
confusable_with:
- network/fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser
- network/browser-devtools-blocked-canceled-failed-symptom-router
- network/ssr-view-render-vs-json-api-response-basics
forbidden_neighbors:
expected_queries:
- API 응답이 JSON이 아니라 HTML로 오면 어디부터 봐야 해?
- fetch가 성공처럼 보이는데 login 페이지 HTML이 내려오는 이유가 뭐야?
- Accept는 json인데 왜 text/html 응답이 오지?
- Bad Gateway HTML이 오는데 앱 에러인지 프록시 에러인지 어떻게 구분해?
- 브라우저에서 200 응답인데 body가 로그인 페이지면 무슨 문제야?
contextual_chunk_prefix: |
  이 문서는 학습자가 JSON을 기대한 호출에서 HTML이 돌아왔을 때 login
  redirect, gateway 기본 페이지, CDN 에러 화면, 원래 SSR 응답을 증상에서
  원인으로 가르게 하는 symptom_router다. 파싱 전에 html 문서가 보임,
  final URL이 달라짐, body 첫 줄이 Bad Gateway, API 대신 로그인 화면이 옴,
  브라우저에서만 text/html이 섞임 같은 자연어 paraphrase가 본 문서의
  분기에 매핑된다.
retrieval-anchor-keywords: json 대신 html 응답, accept json인데 html 옴, login html 200 why, bad gateway html api, text/html api response, html response first check, 브라우저 api html 왜, what is html instead of json, fetch credentials login html, final url login html
---

# JSON 기대했는데 HTML 응답이 옴 원인 라우터

> 한 줄 요약: JSON 대신 HTML이 왔다는 사실만으로 원인은 하나가 아니다. 먼저 `final URL`, `Status`, `Content-Type`, preview 첫 줄을 묶어 보면 login redirect인지, gateway/CDN 에러인지, 원래 HTML endpoint를 친 것인지 빠르게 갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools Response Body Ownership Checklist](./browser-devtools-response-body-ownership-checklist.md) - body 첫 줄과 final URL을 같이 읽는 체크리스트
- [Browser 401 vs 302 Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) - login HTML `200`으로 숨는 인증 문제 분기
- [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md) - 원래 HTML endpoint를 친 경우의 큰 그림

## 어떤 증상에서 이 문서를 펴는가

- `fetch`나 `axios`는 성공처럼 보이는데 body를 열어 보니 로그인 화면 HTML이 나온다.
- `Accept: application/json`을 보냈는데 `Content-Type: text/html`로 돌아온다.
- `502`, `403`, `200`처럼 status는 제각각인데 공통으로 HTML 조각이 보인다.

처음에는 "서버가 JSON 직렬화를 실패했나?"라고 생각하기 쉽지만, 이 증상은 응답 *소유자*가 누구인지부터 나눠야 빨리 풀린다.

## 가능한 원인

1. login redirect를 따라가서 최종 login HTML `200`만 본 경우다. `/api/**`를 호출했는데 final URL이 `/login`으로 바뀌었거나 preview에 `<form`, `login`, `password`가 보이면 이 갈래부터 본다. 다음 문서: [Browser 401 vs 302 Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
2. 쿠키나 credential이 안 실려서 원래 API가 익명 요청으로 처리된 경우다. Application 탭에는 cookie가 있어도 실제 request `Cookie` header가 비어 있거나 cross-origin `fetch`에서 `credentials`가 빠지면 login HTML이나 auth page가 섞일 수 있다. 다음 문서: [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md), [Fetch Credentials vs Cookie Scope](../security/fetch-credentials-vs-cookie-scope.md)
3. gateway나 reverse proxy가 upstream 실패를 기본 HTML로 대신 말한 경우다. `502`/`504`와 함께 `Bad Gateway`, `Gateway Timeout` 같은 짧은 문구가 보이면 앱 JSON 계약보다 앞단 local reply 후보가 더 크다. 다음 문서: [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md), [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
4. CDN이나 WAF가 branded HTML 에러 페이지를 내려준 경우다. `403`/`429`/`503`에 vendor 문구, `Server`, `Via`, `CF-Ray`, `X-Cache` 같은 헤더가 같이 보이면 origin app보다 edge 정책을 먼저 의심한다. 다음 문서: [CDN Error HTML vs App Error JSON Decision Card](./cdn-error-html-vs-app-json-decision-card.md)
5. 애초에 JSON API가 아니라 SSR 페이지나 잘못된 endpoint를 친 경우다. final URL이 그대로이고 `text/html`이 서비스 화면 마크업처럼 보이면 숨은 auth redirect보다 HTML endpoint 호출 가능성이 높다. 다음 문서: [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)

## 빠른 자기 진단

1. original URL과 final URL을 같이 본다. `/api/** -> /login`이면 login redirect 갈래고, final URL이 그대로면 HTML endpoint나 gateway surface를 먼저 의심한다.
2. `Status`와 preview 첫 줄을 묶는다. `200 + login form`은 숨은 redirect 후보, `502/504 + Bad Gateway`는 proxy 후보, `403/429 + vendor 문구`는 CDN/WAF 후보다.
3. response `Content-Type`과 request `Accept`를 같이 본다. `Accept: application/json`인데 `Content-Type: text/html`이면 body 파싱 전에 이미 "기대한 것과 실제 응답이 어긋났다"는 사실을 고정할 수 있다.
4. request `Cookie` header와 `fetch credentials`를 본다. cookie가 비어 있거나 cross-origin 요청에서 credential 전달이 막히면 auth redirect 결과 HTML만 마지막에 보일 수 있다.
5. `Server`, `Via`, `X-Request-Id`, waterfall `Waiting`을 확인한다. 앞단 흔적이 강하고 `Waiting`이 길면 app 로직보다 proxy timeout 쪽으로, 헤더가 평범하고 final URL도 그대로면 endpoint/SSR 쪽으로 간다.

## 자주 하는 오해

- `Accept: application/json`이면 서버가 반드시 JSON을 보내 준다고 보면 안 된다. 인증 리다이렉트나 프록시 기본 에러 페이지는 이 계약을 무시하고 HTML을 반환할 수 있다.
- 브라우저 Network 탭의 `200`만 보고 성공이라고 결론내리면 안 된다. 최종 URL과 preview 첫 줄이 더 직접적인 증거다.
- HTML이 왔다고 항상 앱 컨트롤러 문제라고 보면 안 된다. CDN, WAF, gateway가 더 앞에서 응답을 끝낼 수 있다.

## 안전한 다음 한 걸음

- login form 흔적이 보이면 [Browser 401 vs 302 Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)로 넘어가 인증 경로를 먼저 자른다.
- cookie 저장과 전송이 헷갈리면 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)와 [Fetch Credentials vs Cookie Scope](../security/fetch-credentials-vs-cookie-scope.md)를 이어서 본다.
- gateway/CDN 흔적이 강하면 [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)와 [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)로 내려간다.

## 한 줄 정리

JSON 대신 HTML이 오면 파싱 에러부터 보지 말고 `final URL -> status -> content-type -> preview 첫 줄` 순서로 읽어, login redirect인지 앞단 HTML인지 원래 HTML endpoint인지 먼저 고정한다.
