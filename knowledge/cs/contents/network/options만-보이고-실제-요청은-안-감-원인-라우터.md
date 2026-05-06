---
schema_version: 3
title: OPTIONS만 보이고 실제 요청은 안 감 원인 라우터
concept_id: network/options-only-no-actual-request-symptom-router
canonical: false
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
- preflight-before-auth
- options-401-403-405
- cors-vs-mixed-content
aliases:
- options만 보여요
- preflight만 가고 post가 안 가요
- actual request가 안 보여요
- options 요청 뒤에 post가 없어요
- cors 같은데 실제 api 호출이 안 나가요
symptoms:
- 'DevTools Network 탭에서 `OPTIONS` 요청만 보이고 같은 path의 실제 `GET`/`POST`/`PUT` 요청이 아예 안 보인다'
- 콘솔에는 CORS 에러가 뜨는데 API 서버 로그에는 본 요청이 도착한 흔적이 없어 어디서 막혔는지 헷갈린다
- '`OPTIONS`가 `401`, `403`, `405`처럼 실패한 뒤 actual 요청이 안 나가서 인증 문제인지 preflight 문제인지 구분이 안 된다'
intents:
- symptom
- troubleshooting
prerequisites:
- network/browser-devtools-blocked-canceled-failed-symptom-router
- security/fetch-credentials-vs-cookie-scope
next_docs:
- network/browser-devtools-blocked-canceled-failed-symptom-router
- security/fetch-credentials-vs-cookie-scope
- security/auth-failure-response-401-403-404
- security/browser-401-vs-302-login-redirect-guide
linked_paths:
- contents/network/browser-devtools-options-preflight-vs-actual-failure-mini-card.md
- contents/network/browser-devtools-blocked-mixed-content-vs-cors-mini-card.md
- contents/network/browser-devtools-error-path-cors-vs-actual-401-403-bridge.md
- contents/network/cross-origin-cookie-credentials-cors-primer.md
- contents/security/preflight-debug-checklist.md
- contents/security/cors-samesite-preflight.md
- contents/security/spring-security-options-primer.md
confusable_with:
- network/browser-devtools-blocked-canceled-failed-symptom-router
- security/fetch-credentials-vs-cookie-scope
- security/auth-failure-response-401-403-404
forbidden_neighbors:
expected_queries:
- 네트워크 탭에 OPTIONS만 뜨고 실제 POST가 안 보이면 어디부터 봐야 해?
- CORS 에러가 뜨는데 서버 로그에 본 요청이 없을 때 무엇을 의심해야 해?
- OPTIONS가 401이나 403으로 끝나고 actual request가 안 나가면 인증 문제야 preflight 문제야?
- 브라우저에서 preflight만 실패하고 API 본 호출이 안 갈 때 어떻게 분기해?
- 같은 path에 OPTIONS만 있고 GET이나 POST가 없을 때 원인을 어떻게 좁혀?
contextual_chunk_prefix: |
  이 문서는 학습자가 Network 탭에서 사전 확인 요청만 보이고 본 API 호출이
  이어지지 않을 때, 어디에서 전송이 멈췄는지 증상에서 원인으로 잇는 network
  symptom_router다. 허용 확인 단계에서 멈춤, 본문 호출 전 차단, 같은 경로에
  실제 row 없음, CORS로 보이지만 서버까지 못 감, OPTIONS 응답에서 끝남 같은
  자연어 표현이 preflight 헤더 누락, 브라우저 정책 차단, OPTIONS 보호 정책
  분기와 다음 문서 추천에 매핑된다.
---

# OPTIONS만 보이고 실제 요청은 안 감 원인 라우터

## 한 줄 요약

> 이 장면은 보통 "API 인증이 틀렸다"보다 브라우저가 본 요청을 보내기 전에 허용 확인 단계에서 멈춘 경우가 많다. 먼저 같은 path에 actual 요청 row가 정말 없는지부터 고정하면 길을 덜 잃는다.

## 가능한 원인

1. 가장 흔한 갈래는 preflight 허용 조건이 맞지 않는 경우다. `OPTIONS`에 대해 `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`가 기대와 어긋나면 브라우저는 actual 요청을 보내지 않을 수 있다. 다음 문서: [Preflight Debug Checklist](../security/preflight-debug-checklist.md), [CORS, SameSite, Preflight](../security/cors-samesite-preflight.md)
2. 서버나 보안 필터가 `OPTIONS`를 일반 API처럼 막는 경우다. `OPTIONS 401`, `403`, `405`가 보이면 bearer token 자체보다 proxy, security filter, routing이 preflight를 별도로 허용하는지 먼저 본다. 다음 문서: [Spring Security OPTIONS Primer](../security/spring-security-options-primer.md), [Browser DevTools `OPTIONS` Preflight vs Actual Request Failure 미니 카드](./browser-devtools-options-preflight-vs-actual-failure-mini-card.md)
3. 실제로는 `(blocked)` 계열 브라우저 정책 문제인데 학습자가 `OPTIONS` row만 보고 CORS 설정 문제로 단정한 경우다. mixed content, 확장 프로그램 차단, 브라우저 정책 차단이면 서버 설정을 오래 봐도 풀리지 않는다. 다음 문서: [Browser DevTools `(blocked)` / `canceled` / `(failed)` 원인 라우터](./browser-devtools-blocked-canceled-failed-symptom-router.md), [Browser DevTools `(blocked)` Mixed Content vs CORS 미니 카드](./browser-devtools-blocked-mixed-content-vs-cors-mini-card.md)
4. preflight가 아니라 actual 요청 실패를 잘못 읽은 경우도 있다. `OPTIONS` 뒤에 `POST`나 `GET` row가 실제로 보이면 이제 질문은 CORS가 아니라 auth, cookie, redirect 해석으로 바뀐다. 다음 문서: [Fetch Credentials vs Cookie Scope](../security/fetch-credentials-vs-cookie-scope.md), [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md), [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)

## 빠른 자기 진단

1. 먼저 같은 path에 actual `GET`/`POST`/`PUT` row가 생겼는지 본다. 없으면 preflight lane이고, 있으면 이 문서보다 actual 응답 해석 문서가 맞다.
2. `OPTIONS` row의 `Status`, response headers, console 문구를 한 번에 묶는다. `405`면 라우팅이나 method 허용, `401`이나 `403`이면 security filter나 gateway policy, allow 헤더 누락이면 CORS 설정 분기로 바로 좁혀진다.
3. 콘솔에 `blocked by CORS policy`인지 `Mixed Content`인지 구체 문구가 있는지 확인한다. 둘 다 "안 갔다"처럼 보여도 수정 지점이 완전히 다르다.
4. 서버 로그를 볼 때는 actual endpoint 로그만 찾지 말고 `OPTIONS` 자체가 들어왔는지도 본다. `OPTIONS` 흔적이 없으면 브라우저 정책이나 앞단 차단이 더 앞쪽일 수 있다.
5. `OPTIONS` 뒤에 actual row가 하나라도 보이면 여기서 멈춘다. 그 순간부터는 `credentials`, cookie scope, auth response, hidden login redirect를 읽는 쪽이 더 빠르다.

## 다음 학습

- preflight와 actual request를 DevTools row 기준으로 바로 나누려면 [Browser DevTools `OPTIONS` Preflight vs Actual Request Failure 미니 카드](./browser-devtools-options-preflight-vs-actual-failure-mini-card.md)
- `OPTIONS-only` 분기를 더 자세히 따라가려면 [Preflight Debug Checklist](../security/preflight-debug-checklist.md)
- request cookie가 비었는지와 CORS 응답 읽기 문제를 나누려면 [Fetch Credentials vs Cookie Scope](../security/fetch-credentials-vs-cookie-scope.md)
- 실제로는 login redirect나 auth failure인 경우를 보려면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
