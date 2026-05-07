---
schema_version: 3
title: Roomescape Member / Admin Auth Boundary Bridge
concept_id: spring/roomescape-member-admin-auth-boundary-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: mixed
source_priority: 78
mission_ids:
- missions/roomescape
- missions/spring-roomescape
review_feedback_tags:
- roomescape
- admin-auth
- member-auth-boundary
- spring-security
aliases:
- roomescape member admin auth boundary
- roomescape 관리자 회원 인증 경계
- roomescape admin member security bridge
- 로그인했는데 admin 403
- member role access bridge
symptoms:
- roomescape에서 로그인은 된 것 같은데 관리자 API가 403으로 끝난다
- member 저장, session 복원, role check, controller 권한 검사를 한 문제로 섞어 본다
- CORS나 redirect 문제처럼 보이지만 실제로는 인증/인가 경계가 다르다
intents:
- mission_bridge
- troubleshooting
- design
prerequisites:
- security/auth-failure-response-401-403-404
- spring/spring-security-filter-chain-ordering
next_docs:
- spring/roomescape-admin-login-final-403-securitycontext-bridge
- spring/securitycontextrepository-sessioncreationpolicy-boundaries
- security/role-vs-scope-vs-ownership-primer
linked_paths:
- contents/security/auth-failure-response-401-403-404.md
- contents/spring/spring-security-filter-chain-ordering.md
- contents/spring/roomescape-admin-login-final-403-securitycontext-bridge.md
- contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md
- contents/security/role-vs-scope-vs-ownership-primer.md
- contents/spring/spring-admin-302-login-vs-403-beginner-bridge.md
confusable_with:
- spring/roomescape-admin-login-final-403-securitycontext-bridge
- spring/securitycontextrepository-sessioncreationpolicy-boundaries
- security/auth-failure-response-401-403-404
forbidden_neighbors:
- contents/security/cors-basics.md
expected_queries:
- roomescape member admin 로그인 권한 경계를 CS 개념으로 연결해줘
- roomescape에서 로그인은 됐는데 admin API가 403이면 무엇을 봐야 해?
- member 저장과 SecurityContext 복원과 role check를 어떻게 나눠?
- 302 login redirect와 403 forbidden을 roomescape 관리자 흐름으로 설명해줘
contextual_chunk_prefix: |
  이 문서는 roomescape member/admin 인증 인가 경계를 Spring Security 개념과
  연결하는 mission_bridge다. 로그인 성공, admin 403, member role, session
  restore, SecurityContext, 302 login redirect 같은 미션 질문을 authn/authz
  response boundary로 매핑한다.
---
# Roomescape Member / Admin Auth Boundary Bridge

> 한 줄 요약: roomescape 관리자 접근 문제는 "회원이 저장됐나", "다음 요청에서 인증이 복원됐나", "관리자 권한이 허용됐나"를 분리해야 한다.

**난이도: Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "로그인은 된 것 같은데 관리자 API가 403으로 끝나요" | roomescape member/admin 권한 분리 | authentication 성공과 authorization 실패를 분리한다 |
| "member 저장, session 복원, role check가 한 문제처럼 보여요" | 로그인 후 다음 요청에서 관리자 접근 실패 | principal 복원과 role/authority 매핑을 순서대로 확인한다 |
| "CORS나 redirect 문제처럼 보이는데 실제 status가 헷갈려요" | 브라우저 admin 요청 디버깅 | Network에서 `302`, `401`, `403` 중 무엇이 먼저인지 본다 |

## CS concept 매핑

| roomescape 장면 | CS 개념 |
|---|---|
| 로그인 요청이 성공한다 | authentication |
| 다음 요청에서 사용자를 다시 찾는다 | session / SecurityContext persistence |
| admin API에서 거절된다 | authorization |
| 로그인 페이지로 간다 | unauthenticated entry point |
| `403`이 나온다 | authenticated but forbidden |

## 리뷰 신호

- "로그인은 성공했는데 왜 admin은 403인가요?"는 로그인 성공과 권한 부여를 섞어 보는 신호다.
- "쿠키가 있는데 다시 로그인으로 가요"는 role check보다 SecurityContext 복원 문제일 수 있다.
- "CORS 에러처럼 보여요"는 브라우저 노출 문제와 서버 auth 응답을 먼저 분리해야 한다.

## 분기 순서

1. Network 탭에서 실제 status가 `302`, `401`, `403` 중 무엇인지 본다.
2. 다음 요청에 cookie/session이 실리는지 본다.
3. 서버가 session에서 principal을 복원하는지 본다.
4. principal의 role/authority가 admin rule과 맞는지 본다.

이 순서가 잡히면 roomescape member 저장 로직, session 복원, role mapping, controller access rule을 한꺼번에 고치지 않게 된다.
