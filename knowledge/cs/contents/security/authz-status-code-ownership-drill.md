---
schema_version: 3
title: AuthZ Status Code Ownership Drill
concept_id: security/authz-status-code-ownership-drill
canonical: false
category: security
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
review_feedback_tags:
- authz-status-code
- ownership
- 401-403-404
- review-drill
aliases:
- authz status code ownership drill
- 401 403 404 ownership drill
- 권한 상태코드 소유권 드릴
- 로그인 됐는데 403 문제
- 남의 주문 404 concealment drill
symptoms:
- 401, 403, 404를 인증/인가/소유권 기준으로 빠르게 구분하고 싶다
- 로그인은 됐는데 admin이나 order 접근이 막히는 문제를 예제로 연습하고 싶다
- ownership mismatch를 403으로 줄지 404로 숨길지 판단이 느리다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- security/auth-failure-response-401-403-404
- security/role-vs-scope-vs-ownership-primer
next_docs:
- security/roomescape-admin-authz-status-code-bridge
- security/shopping-cart-order-ownership-authorization-bridge
- security/resource-level-authz-decision-practice
linked_paths:
- contents/security/auth-failure-response-401-403-404.md
- contents/security/role-vs-scope-vs-ownership-primer.md
- contents/security/roomescape-admin-authz-status-code-bridge.md
- contents/security/shopping-cart-order-ownership-authorization-bridge.md
- contents/security/resource-level-authz-decision-practice.md
- contents/security/idor-bola-patterns-and-fixes.md
confusable_with:
- security/auth-failure-response-401-403-404
- security/role-vs-scope-vs-ownership-primer
- security/resource-level-authz-decision-practice
forbidden_neighbors:
- contents/security/cors-basics.md
expected_queries:
- 401 403 404 ownership을 문제로 연습하고 싶어
- 로그인됐는데 admin 403과 남의 주문 404를 어떻게 구분해?
- authz status code drill로 role scope ownership 판단해줘
- roomescape shopping-cart 보안 응답 코드 예제 문제를 줘
contextual_chunk_prefix: |
  이 문서는 authz status code ownership drill이다. 401, 403, 404,
  authenticated but forbidden, ownership mismatch, concealment, admin role,
  order IDOR 같은 질문을 짧은 보안 판별 문제로 매핑한다.
---
# AuthZ Status Code Ownership Drill

> 한 줄 요약: 먼저 principal이 있는지 보고, 다음에 action 권한, 마지막에 resource ownership을 본다.

**난이도: Beginner**

## 문제 1

상황:

```text
쿠키 없이 admin API를 호출했더니 login page로 redirect된다.
```

답:

인증 실패 흐름이다. API라면 `401`, browser page flow라면 `302` login redirect로 나타날 수 있다.

## 문제 2

상황:

```text
일반 회원으로 로그인한 뒤 roomescape admin reservation API를 호출하면 403이다.
```

답:

인가 실패다. principal은 있지만 admin role/authority가 부족한 상태다.

## 문제 3

상황:

```text
shopping-cart에서 사용자 A가 사용자 B의 order id로 상세 조회를 시도한다.
```

답:

ownership mismatch다. 정책에 따라 `403`으로 거절하거나 존재 은닉을 위해 `404`로 숨길 수 있다.

## 빠른 체크

| 질문 | 응답 후보 |
|---|---|
| 누구인지 모르는가 | `401` / browser `302` |
| 누구인지는 알지만 기능 권한이 없는가 | `403` |
| 객체가 내 소유가 아닌가 | `403` 또는 concealment `404` |
| 진짜 없는 id인가 | `404` |
