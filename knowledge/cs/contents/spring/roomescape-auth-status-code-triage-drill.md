---
schema_version: 3
title: Roomescape Auth Status Code Triage Drill
concept_id: spring/roomescape-auth-status-code-triage-drill
canonical: false
category: spring
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/spring-roomescape
review_feedback_tags:
- roomescape
- auth-status-code
- spring-security
- triage-drill
aliases:
- roomescape auth status code drill
- 룸이스케이프 인증 인가 상태코드 드릴
- admin 302 401 403 triage
- SecurityContext 403 drill
- 로그인됐는데 admin forbidden 문제
symptoms:
- roomescape 관리자 API가 302, 401, 403 중 무엇으로 실패하는지 구분하지 못한다
- 로그인은 된 것 같은데 SecurityContext가 다음 요청에서 비어 있다
- CORS처럼 보이는 브라우저 에러와 서버 인증 실패를 섞어 본다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- spring/roomescape-member-admin-auth-boundary-bridge
- security/auth-failure-response-401-403-404
next_docs:
- spring/roomescape-admin-login-final-403-securitycontext-bridge
- spring/securitycontextrepository-sessioncreationpolicy-boundaries
- spring/spring-security-filter-chain-ordering
linked_paths:
- contents/spring/roomescape-member-admin-auth-boundary-bridge.md
- contents/security/auth-failure-response-401-403-404.md
- contents/spring/roomescape-admin-login-final-403-securitycontext-bridge.md
- contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md
- contents/spring/spring-security-filter-chain-ordering.md
- contents/security/cors-basics.md
confusable_with:
- spring/roomescape-member-admin-auth-boundary-bridge
- spring/roomescape-admin-login-final-403-securitycontext-bridge
- security/auth-failure-response-401-403-404
forbidden_neighbors:
- contents/security/cors-basics.md
expected_queries:
- roomescape admin API가 302 401 403 중 뭔지 문제로 구분하고 싶어
- 로그인됐는데 관리자 API가 forbidden이면 어디부터 봐야 해?
- SecurityContext와 session 복원 문제를 짧은 드릴로 풀어줘
- CORS처럼 보이는 auth 실패를 roomescape에서 어떻게 분기해?
contextual_chunk_prefix: |
  이 문서는 Spring Roomescape auth status code triage drill이다. admin
  302 redirect, 401 unauthenticated, 403 forbidden, SecurityContext restore,
  session cookie, CORS-looking browser error 같은 인증/인가 실패를 짧은
  판별 문제로 매핑한다.
---
# Roomescape Auth Status Code Triage Drill

> 한 줄 요약: 관리자 API 실패는 먼저 실제 HTTP status를 보고, 그 다음 인증 복원과 권한 판정을 나눠야 한다.

**난이도: Beginner**

## 문제 1

상황:

```text
관리자 API 호출 결과가 로그인 페이지 HTML로 바뀌어 돌아온다.
```

답:

인증되지 않은 요청으로 처리되어 entry point가 동작했을 가능성이 크다. Network 탭에서 실제 status가 `302`인지, redirect location이 login인지 먼저 본다.

## 문제 2

상황:

```text
로그인 직후 쿠키는 있는데 다음 admin 요청에서 SecurityContext가 비어 있다.
```

답:

role check보다 SecurityContext persistence 문제를 먼저 본다. session cookie가 실리는지, SecurityContextRepository와 SessionCreationPolicy 설정이 맞는지 확인한다.

## 문제 3

상황:

```text
principal은 복원됐지만 admin endpoint에서 403이 나온다.
```

답:

인증은 됐고 인가가 실패한 장면이다. 사용자의 authority/role 이름과 SecurityFilterChain의 matcher rule이 맞는지 본다.

## 빠른 체크

| 실제 신호 | 먼저 볼 곳 |
|---|---|
| `302` login redirect | authentication entry point |
| `401` JSON response | unauthenticated API response contract |
| `403` | authenticated but forbidden |
| browser console CORS 문구 | Network status와 response header부터 확인 |
