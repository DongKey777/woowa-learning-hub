---
schema_version: 3
title: '`STATELESS`인데 `JSESSIONID`가 생겨요 원인 라우터'
concept_id: spring/stateless-jsessionid-hidden-session-cause-router
canonical: false
category: spring
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 80
mission_ids:
  - missions/roomescape
  - missions/shopping-cart
review_feedback_tags:
  - stateless-hidden-session
  - requestcache-hidden-session
  - securitycontextrepository-session-boundary
aliases:
  - stateless인데 jsessionid 생김
  - hidden session spring security
  - api인데 세션 쿠키가 생김
  - request cache 때문에 세션 생김
  - spring security hidden jsessionid
  - sessioncreationpolicy stateless cookie
symptoms:
  - SessionCreationPolicy.STATELESS로 설정했는데도 응답에 JSESSIONID가 생겨요
  - REST API라고 생각했는데 401 대신 login redirect와 세션 쿠키가 같이 보여요
  - SavedRequest를 안 쓴 줄 알았는데 로그인 전 URL이 기억되고 세션이 생겨요
  - form login이나 oauth2Login을 붙인 뒤부터 API 요청에도 hidden session이 숨어든 것 같아요
intents:
  - symptom
  - troubleshooting
prerequisites:
  - security/session-cookie-jwt-basics
next_docs:
  - security/browser-401-vs-302-login-redirect-guide
  - spring/spring-admin-session-cookie-flow-primer
  - security/cookie-scope-mismatch-guide
  - security/fetch-credentials-vs-cookie-scope
linked_paths:
  - contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md
  - contents/security/browser-401-vs-302-login-redirect-guide.md
  - contents/security/cookie-scope-mismatch-guide.md
  - contents/security/fetch-credentials-vs-cookie-scope.md
  - contents/spring/spring-admin-session-cookie-flow-primer.md
  - contents/spring/spring-api-401-vs-browser-302-beginner-bridge.md
  - contents/spring/spring-security-requestcache-savedrequest-boundaries.md
  - contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md
confusable_with:
  - spring/login-state-not-persisted-cause-router
  - spring/spring-admin-session-cookie-flow-primer
  - security/browser-401-vs-302-login-redirect-guide
forbidden_neighbors: []
expected_queries:
  - Spring Security에서 STATELESS로 뒀는데 왜 JSESSIONID 쿠키가 생겨?
  - API 체인이라고 생각했는데 401 대신 로그인 redirect와 세션이 같이 보이면 어디부터 봐야 해?
  - RequestCache나 SavedRequest 때문에 hidden session이 생기는 장면을 초급 기준으로 어떻게 가를까?
  - formLogin이나 oauth2Login을 붙인 뒤 API 요청에도 세션이 숨어드는 이유를 설명해 줄 수 있어?
  - SessionCreationPolicy.STATELESS인데도 로그인 전 URL 복귀가 보이면 무엇이 세션을 만든 거야?
contextual_chunk_prefix: |
  이 문서는 Spring Security에서 "`STATELESS`인데 `JSESSIONID`가 생겨요",
  "API인데 login redirect와 세션 쿠키가 같이 보여요", "SavedRequest를 안
  쓴 줄 알았는데 원래 URL이 기억돼요", "form login을 붙인 뒤 hidden
  session이 숨어든 것 같아요" 같은 학습자 증상을 request cache /
  SavedRequest, browser용 security chain 혼입, SecurityContext 저장 경계,
  cookie 전송 착시 갈래로 나누는 symptom_router다.
---

# `STATELESS`인데 `JSESSIONID`가 생겨요 원인 라우터

## 한 줄 요약

> `SessionCreationPolicy.STATELESS`는 "Security가 세션을 인증 저장소로 쓰지 않겠다"에 가깝지, 앱 전체가 절대 세션을 만들지 않는다는 뜻은 아니다.

## 가능한 원인

1. **`RequestCache`와 `SavedRequest`가 브라우저 복귀 UX를 위해 세션을 만들었다.** 보호 URL 접근 뒤 `/login`으로 튀고, 로그인 후 원래 URL 복귀가 보이면 hidden session의 첫 후보는 이 갈래다. 이 경우는 [Spring Security `RequestCache` / `SavedRequest` Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)로 이어진다.
2. **API 체인에 브라우저용 login 흐름이 섞였다.** `/api/**`도 `302 /login`이나 login HTML을 받는다면 stateless 자체보다 chain 분리와 entry point 계약이 더 가까운 원인일 수 있다. 이 갈래는 [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](./spring-api-401-vs-browser-302-beginner-bridge.md)와 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)로 간다.
3. **현재 요청의 인증 저장 경계가 session 기반으로 남아 있다.** custom login, form login, oauth2Login, `SecurityContextRepository` 설정 때문에 현재 요청 인증이 session에 저장될 수 있다. 이 경우는 [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)와 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)를 같이 본다.
4. **세션 생성이 아니라 cookie/redirect 관측을 잘못 읽고 있다.** `Application` 탭에 쿠키가 보여도 같은 실패 요청의 `Cookie` header가 비면 전송 문제고, cross-origin `fetch`면 `credentials`가 먼저다. 이 갈래는 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md), [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md), [Fetch Credentials vs Cookie Scope](../security/fetch-credentials-vs-cookie-scope.md)로 분기한다.

## 빠른 자기 진단

1. 응답에 `Set-Cookie: JSESSIONID`가 실제로 찍혔는지, 아니면 기존 쿠키를 브라우저가 계속 보여 주는지만 먼저 분리한다.
2. 같은 실패 장면이 `302 /login` 또는 login HTML `200`이면 API stateless 위반보다 `RequestCache`와 브라우저 redirect 갈래를 먼저 본다.
3. `/api/**`와 `/admin/**`가 같은 `SecurityFilterChain`을 타는지 확인한다. 섞여 있으면 browser 정책이 API까지 번지기 쉽다.
4. custom filter에서 `SecurityContextHolder`만 채웠는지, 저장소까지 session 경계를 열었는지 분리한다. 이 차이를 놓치면 "`STATELESS`인데 왜 유지되지?"와 "`왜 쿠키가 생기지?`"가 한 문제처럼 보인다.

## 다음 학습

- login redirect와 hidden session이 한 문장에 같이 보이면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)부터 본다.
- 쿠키 저장과 서버 복원 경계를 다시 잡으려면 [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)로 간다.
- `SavedRequest`와 원래 URL 복귀가 핵심이면 [Spring Security `RequestCache` / `SavedRequest` Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)를 잇는다.
- `STATELESS`와 repository 책임을 정확히 나누고 싶으면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)를 본다.
