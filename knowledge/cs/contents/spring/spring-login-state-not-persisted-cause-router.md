---
schema_version: 3
title: 로그인 유지가 안 돼요 원인 라우터
concept_id: spring/login-state-not-persisted-cause-router
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
  - securitycontext-save-vs-restore
  - savedrequest-vs-session-auth
  - jwt-per-request-auth
aliases:
  - 로그인했는데 다시 로그인됨
  - next request anonymous spring
  - cookie 있는데 다시 로그인
  - SecurityContextHolder 넣었는데 다음 요청 anonymous
  - spring login state not persisted
  - JWT 넣었는데 인증이 유지 안 됨
symptoms:
  - 로그인은 성공했는데 다음 요청에서 다시 anonymous로 보여요
  - 브라우저에 JSESSIONID나 쿠키가 있는데도 관리자 페이지를 누르면 다시 로그인하래요
  - custom JWT filter에서 인증한 것 같은데 다음 API 호출에서는 @AuthenticationPrincipal이 비어 있어요
  - 로그인 직후 원래 페이지로 돌아오지 못하거나 /login으로 다시 튀어서 로그인 유지가 안 되는 것처럼 보여요
intents:
  - symptom
  - troubleshooting
prerequisites:
  - security/session-cookie-jwt-basics
next_docs:
  - security/browser-401-vs-302-login-redirect-guide
  - security/cookie-scope-mismatch-guide
  - spring/spring-admin-session-cookie-flow-primer
  - spring/spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card
linked_paths:
  - contents/security/browser-401-vs-302-login-redirect-guide.md
  - contents/security/cookie-scope-mismatch-guide.md
  - contents/spring/spring-admin-session-cookie-flow-primer.md
  - contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md
  - contents/spring/spring-security-requestcache-savedrequest-boundaries.md
  - contents/spring/spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card.md
  - contents/spring/spring-securitycontext-propagation-async-reactive-boundaries.md
confusable_with:
  - security/browser-401-vs-302-login-redirect-guide
  - spring/spring-admin-session-cookie-flow-primer
  - spring/spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card
forbidden_neighbors:
  - contents/spring/spring-securitycontext-propagation-async-reactive-boundaries.md
expected_queries:
  - Spring에서 로그인 성공 뒤 다음 요청이 다시 anonymous면 어디부터 나눠서 봐야 해?
  - JSESSIONID가 보이는데도 왜 관리자 페이지에서 다시 로그인하라고 할까?
  - custom JWT filter로 인증했는데 다음 API 호출에서는 principal이 비는 이유를 어떻게 진단해?
  - cookie가 저장된 것처럼 보이는데 서버가 로그인 사용자를 못 찾을 때 무슨 갈래로 봐야 해?
  - 로그인 유지가 안 되는 게 SavedRequest 문제인지 세션 복원 문제인지 처음에 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 Spring에서 "로그인은 성공했는데 다음 요청이 anonymous예요",
  "cookie 있는데 다시 로그인돼요", "JSESSIONID가 보이는데 왜 관리자 페이지가
  다시 /login으로 가요", "JWT filter에서 인증했는데 principal이 비어요" 같은
  학습자 증상을 cookie 전송 누락 / session 저장-복원 경계 / SavedRequest
  redirect 혼동 / bearer token 인증 누락으로 나누는 symptom_router다. 로그인
  유지 실패, next request anonymous, post-login principal missing 같은 검색을
  원인별 다음 문서로 보내는 입구로 사용한다.
---

# 로그인 유지가 안 돼요 원인 라우터

## 한 줄 요약

> 로그인 유지 실패는 대개 "로그인 성공 자체"보다 다음 요청에 인증 재료가 실렸는지, 서버가 그 재료로 사용자를 다시 복원했는지, 아니면 redirect 흐름을 다른 문제로 읽었는지를 못 나눈 상태다.

## 가능한 원인

1. **브라우저가 로그인 흔적을 다음 요청에 안 보낸다.** Application 탭에는 쿠키가 보여도 실제 request `Cookie` header가 비면 서버는 로그인 사용자를 복원할 재료가 없다. 이때는 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)와 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)로 가서 `Domain`, `Path`, `SameSite`, `credentials`를 먼저 나눈다.
2. **현재 요청에서는 인증했지만 다음 요청용 저장 경계가 비어 있다.** 커스텀 로그인이나 필터에서 `SecurityContextHolder`만 채우고 끝내면 그 요청 안에서는 로그인처럼 보여도 다음 요청에서는 다시 anonymous가 될 수 있다. 이 갈래는 [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)와 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 이어진다.
3. **실패 원인이 로그인 유지가 아니라 redirect 흐름이다.** `/admin` 요청이 `302 /login`으로 튀거나 로그인 뒤 원래 주소 복귀가 꼬이면, anonymous 복원 실패가 아니라 `SavedRequest`와 entry point 흐름을 잘못 읽은 경우가 많다. 이때는 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)와 [Spring Security `RequestCache` / `SavedRequest` Boundaries](./spring-security-requestcache-savedrequest-boundaries.md) 쪽이 더 가깝다.
4. **세션 대신 bearer token 체인인데 매 요청 인증 구성이 비었다.** JWT API에서는 다음 요청마다 `Authorization` 헤더를 다시 읽어 `SecurityContext`를 채워야 한다. 토큰은 보내는데 `@AuthenticationPrincipal`이 비거나 custom filter 위치가 어긋나면 [Spring JWT 필터에서 `filterChain.doFilter(...)` 전후에 무슨 일이 일어날까](./spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card.md)로 내려가 before/after 구간을 다시 본다.

## 빠른 자기 진단

1. 같은 실패 요청의 Network 탭에서 request `Cookie` 헤더나 `Authorization` 헤더가 실제로 실렸는지 먼저 본다. 저장소에 보이는 값만 보고 판단하면 `cookie-missing`과 `server-anonymous`가 섞인다.
2. 응답이 `302 /login`이거나 login HTML `200`으로 끝나면 인증 복원보다 redirect 분기가 먼저다. 이때는 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)로 가서 `redirect / navigation memory`인지 `server-anonymous`인지 먼저 고정한다.
3. request 헤더에 쿠키는 있는데 서버가 다음 요청에서 다시 anonymous라면 세션 저장과 복원 경계를 본다. 로그인 핸들러, `SecurityContextRepository`, `SessionCreationPolicy`를 같이 읽어야 한다.
4. 브라우저 쿠키가 아니라 bearer token API라면 세션 유지라는 표현부터 다시 잡는다. 이 경우는 매 요청 재인증이 정상 경로라서 [Spring JWT 필터에서 `filterChain.doFilter(...)` 전후에 무슨 일이 일어날까](./spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card.md)와 필터 순서를 먼저 본다.
5. 같은 요청 안의 `@Async`, scheduler, reactive 경계에서만 principal이 사라지면 다음 요청 문제가 아니라 context propagation 문제일 수 있다. 이때는 [Spring SecurityContext Propagation across Async / Reactive Boundaries](./spring-securitycontext-propagation-async-reactive-boundaries.md)로 분기한다.

## 다음 학습

- 브라우저에서 `302 /login`, login HTML, hidden session이 먼저 보였으면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)부터 본다.
- 쿠키는 저장됐는데 request에 안 실리면 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)로 가서 scope와 `credentials`를 확인한다.
- 쿠키는 실리는데 서버가 로그인 사용자를 복원하지 못하면 [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)와 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)를 잇는다.
- JWT API에서만 principal이 비면 [Spring JWT 필터에서 `filterChain.doFilter(...)` 전후에 무슨 일이 일어날까](./spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card.md)를 보고 필터 책임을 다시 고정한다.
