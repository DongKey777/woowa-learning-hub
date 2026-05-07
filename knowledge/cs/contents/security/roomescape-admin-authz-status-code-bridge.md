---
schema_version: 3
title: Roomescape Admin AuthZ Status Code Bridge
concept_id: security/roomescape-admin-authz-status-code-bridge
canonical: false
category: security
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
- admin-authz
- status-code
- 401-403-404
aliases:
- roomescape admin authz status code bridge
- 룸이스케이프 관리자 권한 상태코드 bridge
- admin 401 403 404 roomescape
- 로그인 됐는데 admin 403
- roomescape role ownership status code
symptoms:
- roomescape 관리자 API에서 로그인은 된 것 같은데 403이 나온다
- admin 권한이 없는 사용자에게 401, 403, 404 중 무엇을 줄지 헷갈린다
- Spring Security 설정 문제와 보안 응답 코드 정책을 섞어 본다
intents:
- mission_bridge
- troubleshooting
- design
prerequisites:
- security/auth-failure-response-401-403-404
- security/role-vs-scope-vs-ownership-primer
next_docs:
- spring/roomescape-member-admin-auth-boundary-bridge
- spring/roomescape-admin-login-final-403-securitycontext-bridge
- security/permission-checks-rest-flows-primer
linked_paths:
- contents/security/auth-failure-response-401-403-404.md
- contents/security/role-vs-scope-vs-ownership-primer.md
- contents/security/permission-checks-rest-flows-primer.md
- contents/spring/roomescape-member-admin-auth-boundary-bridge.md
- contents/spring/roomescape-admin-login-final-403-securitycontext-bridge.md
- contents/spring/spring-security-filter-chain-ordering.md
confusable_with:
- security/auth-failure-response-401-403-404
- spring/roomescape-member-admin-auth-boundary-bridge
- spring/roomescape-admin-login-final-403-securitycontext-bridge
forbidden_neighbors:
- contents/security/cors-basics.md
expected_queries:
- roomescape admin API 401 403 404를 security 관점으로 설명해줘
- 로그인됐는데 관리자 API가 403이면 인증과 인가 중 무엇을 봐야 해?
- roomescape admin 권한 없음 응답 코드를 어떻게 고를지 bridge가 필요해
- Spring Security 설정과 auth failure response를 어떻게 나눠 봐?
contextual_chunk_prefix: |
  이 문서는 roomescape admin authz status code mission_bridge다. admin API
  403, login redirect, valid session but forbidden, 401 vs 403 vs 404,
  role check, Spring Security filter chain 같은 질문을 보안 응답 코드와
  Roomescape 관리자 권한 경계로 매핑한다.
---
# Roomescape Admin AuthZ Status Code Bridge

> 한 줄 요약: roomescape 관리자 API 실패는 "누구인지 모름", "누구인지는 알지만 admin이 아님", "존재를 숨김"을 먼저 나눠야 한다.

**난이도: Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "로그인은 된 것 같은데 관리자 API가 403이에요" | 일반 회원이 admin URL을 호출한 장면 | principal 존재와 admin authority 허용을 분리한다 |
| "admin 권한이 없으면 401, 403, 404 중 무엇을 줘야 하나요?" | 관리자 리소스 응답 코드 정책 | 인증 실패, 인가 실패, 존재 은닉을 다른 응답 의미로 본다 |
| "Spring Security 설정 문제와 응답 코드 정책이 섞여요" | filter chain 디버깅과 API 계약 설계가 동시에 나온 상황 | 설정이 principal을 만들었는지와 정책이 어떤 status를 택하는지 나눈다 |

## CS concept 매핑

| roomescape 장면 | security 개념 | 보통 응답 |
|---|---|---|
| 로그인 세션이 없거나 만료됨 | authentication failure | `401` 또는 browser flow에서는 `302` |
| 일반 회원이 admin API 호출 | authorization failure | `403` |
| 남의 resource 존재를 숨김 | concealment / ownership policy | `404` 가능 |
| role 이름이 rule과 안 맞음 | authority mapping failure | 대개 `403` |
| 쿠키가 안 실려 principal이 없음 | session continuity failure | `401` / `302` |

## 리뷰 신호

- "로그인은 됐는데 왜 admin이 안 되나요?"는 인증 성공과 인가 허용을 분리하라는 신호다.
- "CORS 같아 보입니다"는 Network status와 actual response를 먼저 보라는 말이다.
- "403을 401로 바꾸면 되나요?"는 principal 생성 여부를 먼저 확인하라는 질문이다.
- "관리자 리소스를 404로 숨길까요?"는 concealment 정책이 있는지 확인해야 한다.

## 판단 순서

1. request에서 principal이 만들어졌는지 본다.
2. principal의 role/authority가 admin rule과 맞는지 본다.
3. 특정 resource ownership이나 concealment 정책이 있는지 본다.
4. browser redirect와 API JSON response를 같은 문제로 뭉개지 않는다.

이 순서를 따르면 Spring Security 설정 디버깅과 보안 응답 코드 설계를 한꺼번에 고치지 않게 된다.
