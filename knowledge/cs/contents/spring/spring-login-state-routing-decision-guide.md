---
schema_version: 3
title: 'Spring 로그인 유지 분기 결정 가이드: SavedRequest vs 세션 복원 vs JWT 재인증'
concept_id: spring/login-state-routing-decision-guide
canonical: false
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids:
  - missions/roomescape
review_feedback_tags:
  - savedrequest-vs-session-context
  - jwt-vs-session-auth
  - login-loop-triage
aliases:
  - spring 로그인 유지 분기
  - savedrequest 세션 복원 차이
  - jwt 재인증 세션 로그인 구분
  - 302 login anonymous 다음 요청 분리
  - requestcache securitycontextrepository 차이
  - principal 비어 있음 분기
  - login loop triage spring
symptoms:
  - 로그인은 성공한 것 같은데 redirect 문제인지 세션 복원 문제인지 모르겠어요
  - 브라우저 로그인 이슈와 JWT 필터 이슈가 같은 문제처럼 보여서 어디부터 봐야 할지 헷갈려요
  - 다음 요청에서 principal이 비는 장면을 SavedRequest, session, bearer token 중 무엇으로 읽어야 할지 모르겠어요
intents:
  - comparison
  - troubleshooting
prerequisites:
  - security/session-cookie-jwt-basics
next_docs:
  - security/browser-401-vs-302-login-redirect-guide
  - spring/spring-admin-session-cookie-flow-primer
  - spring/login-state-not-persisted-cause-router
  - spring/spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card
linked_paths:
  - contents/security/browser-401-vs-302-login-redirect-guide.md
  - contents/spring/spring-admin-session-cookie-flow-primer.md
  - contents/spring/spring-login-state-not-persisted-cause-router.md
  - contents/spring/spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card.md
  - contents/spring/spring-security-requestcache-savedrequest-boundaries.md
  - contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md
confusable_with:
  - security/browser-401-vs-302-login-redirect-guide
  - spring/spring-admin-session-cookie-flow-primer
  - spring/login-state-not-persisted-cause-router
  - spring/spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card
forbidden_neighbors: []
expected_queries:
  - Spring에서 로그인 뒤 꼬일 때 SavedRequest 문제인지 세션 복원 문제인지 JWT 문제인지 처음에 어떻게 갈라?
  - 브라우저가 /login으로 튀는 경우와 다음 요청에서 anonymous가 되는 경우를 어떤 기준으로 나눠 봐야 해?
  - principal이 비는 장면이 브라우저 세션 이슈인지 bearer token 재인증 누락인지 빠르게 판단하는 법이 있어?
  - 로그인 유지 실패를 request cache, session restore, jwt filter 셋 중 어디로 먼저 보내야 해?
  - Spring Security 학습 중 login loop와 API principal missing을 같은 축에서 구분해 설명해 줄 수 있어?
contextual_chunk_prefix: |
  이 문서는 Spring 학습자가 로그인 유지 실패를 SavedRequest redirect 문제,
  브라우저 세션 복원 문제, JWT bearer token 재인증 문제 중 어디로 먼저
  보내야 하는지 결정하는 chooser다. /login으로 튄다, next request anonymous,
  principal이 비어 있다, login loop와 API 인증 누락이 같은 문제처럼 보인다는
  질문을 redirect memory / session restore / per-request auth 세 갈래로
  정리하는 입구 문서다.
---

# Spring 로그인 유지 분기 결정 가이드: SavedRequest vs 세션 복원 vs JWT 재인증

## 한 줄 요약

> `/login`으로 튀는 브라우저 문제면 SavedRequest 갈래, 쿠키는 있는데 다음 요청이 anonymous면 세션 복원 갈래, API에서 `Authorization`을 매번 다시 읽어야 하면 JWT 재인증 갈래로 먼저 자르면 된다.

## 결정 매트릭스

| 지금 보이는 장면 | 먼저 볼 갈래 | 왜 이 갈래가 먼저인가 |
| --- | --- | --- |
| 보호 URL 접근 후 `302 /login`이나 login HTML `200`이 보인다 | SavedRequest / redirect | 로그인 성공 여부보다 "원래 주소 복귀" 흐름이 먼저 꼬였을 가능성이 크다 |
| 브라우저 쿠키는 있는데 다음 요청에서 다시 anonymous다 | 세션 복원 | request `Cookie` header와 서버의 `SecurityContext` 복원이 이어졌는지 봐야 한다 |
| JWT API에서 `@AuthenticationPrincipal`이 비거나 custom filter가 의심된다 | JWT 재인증 | 세션 유지가 아니라 요청마다 bearer token을 다시 읽는 구성이 핵심이다 |
| `/admin`과 `/api`가 같은 체인에 섞여서 어떤 증상인지 애매하다 | 브라우저냐 API냐 먼저 분리 | redirect UX와 per-request auth를 같은 증상으로 읽으면 오진이 커진다 |
| 로그인은 됐고 원래 URL로도 돌아왔지만 마지막 권한 검사만 실패한다 | SavedRequest가 아니라 권한/역할 매핑 후속 문서 | 복귀 성공과 권한 실패는 다른 원인이라 분리해야 한다 |

짧게 기억하면 `주소 복귀`, `다음 요청 복원`, `매 요청 재인증` 세 축이다.

## 흔한 오선택

`JSESSIONID`가 보인다는 이유만으로 전부 세션 복원 문제로 가면 redirect 메모인 `SavedRequest`를 놓치기 쉽다. 학습자가 "`왜 login 갔다가 다시 홈으로 와요?`"라고 말하면 인증 저장보다 브라우저 이동 흐름이 먼저다.

"principal이 비었다"는 표현만 보고 전부 JWT 필터 문제로 몰아가도 오선택이다. 브라우저 관리자 페이지라면 쿠키 전송 누락이나 세션 복원이 먼저일 수 있다. 반대로 bearer token API라면 세션 유지라는 표현 자체가 맞지 않을 때가 많다.

"로그인 성공 후 마지막 `403`"도 이 문서의 종착점은 아니다. 원래 URL 복귀까지 성공했다면 SavedRequest와 세션 복원보다 역할 매핑이나 인가 규칙을 보는 편이 빠르다.

## 다음 학습

- `/login` redirect, login HTML `200`, 원래 주소 복귀가 핵심이면 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- 브라우저 쿠키와 세션, `SecurityContext`가 어떻게 이어지는지 먼저 잡으려면 [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)
- 증상 중심으로 cookie 누락, session 복원, SavedRequest 혼동을 빠르게 갈라 보려면 [로그인 유지가 안 돼요 원인 라우터](./spring-login-state-not-persisted-cause-router.md)
- bearer token 요청에서 `doFilter(...)` 전후 책임을 보려면 [Spring JWT 필터에서 `filterChain.doFilter(...)` 전후에 무슨 일이 일어날까](./spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card.md)
