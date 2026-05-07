---
schema_version: 3
title: Shopping Cart Order Ownership Authorization Bridge
concept_id: security/shopping-cart-order-ownership-authorization-bridge
canonical: false
category: security
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: mixed
source_priority: 78
mission_ids:
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- shopping-cart
- ownership-authorization
- idor-bola
- order-access
aliases:
- shopping cart order ownership authorization
- 장바구니 주문 ownership 인가
- 남의 주문 조회 403 404
- order idor bola bridge
- valid login is not enough order access
symptoms:
- 로그인한 사용자가 다른 사용자의 주문 ID를 넣으면 어떻게 막아야 할지 모르겠다
- orders.read 권한이 있으면 모든 주문을 볼 수 있는지 헷갈린다
- 남의 주문 조회를 403으로 줄지 404로 숨길지 리뷰에서 막혔다
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- security/permission-checks-rest-flows-primer
- security/role-vs-scope-vs-ownership-primer
next_docs:
- security/idor-bola-patterns-and-fixes
- security/auth-failure-response-401-403-404
- security/resource-level-authz-decision-practice
linked_paths:
- contents/security/permission-checks-rest-flows-primer.md
- contents/security/role-vs-scope-vs-ownership-primer.md
- contents/security/auth-failure-response-401-403-404.md
- contents/security/idor-bola-patterns-and-fixes.md
- contents/security/resource-level-authz-decision-practice.md
- contents/software-engineering/shopping-cart-checkout-service-layer-bridge.md
confusable_with:
- security/role-vs-scope-vs-ownership-primer
- security/permission-checks-rest-flows-primer
- security/idor-bola-patterns-and-fixes
forbidden_neighbors:
- contents/database/shopping-cart-order-complete-read-your-writes-bridge.md
expected_queries:
- shopping-cart에서 남의 주문 ID 조회를 ownership authorization으로 설명해줘
- 로그인됐고 orders.read scope가 있어도 남의 주문을 못 보는 이유가 뭐야?
- order ownership mismatch를 403으로 줄지 404로 숨길지 어떻게 판단해?
- 장바구니 주문 접근 권한을 role scope ownership으로 나눠줘
contextual_chunk_prefix: |
  이 문서는 shopping-cart order ownership authorization mission_bridge다.
  logged in but cannot access another user's order, valid scope but ownership
  mismatch, IDOR/BOLA, 403 vs 404 concealment 같은 질문을 shopping-cart
  주문 접근 보안 경계로 매핑한다.
---
# Shopping Cart Order Ownership Authorization Bridge

> 한 줄 요약: 로그인과 주문 접근 허용은 다르다. shopping-cart 주문 조회는 role/scope 다음에 ownership을 반드시 확인해야 한다.

**난이도: Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "로그인한 사용자가 다른 사용자의 주문 ID를 넣으면 어떻게 막아야 하나요?" | `/orders/{id}` 직접 호출, order id 조작 | 인증 여부 다음에 resource ownership을 반드시 확인한다 |
| "`orders.read` 권한이 있으면 모든 주문을 볼 수 있나요?" | scope/role과 객체 소유자가 섞인 권한 설계 | action permission과 object-level authorization을 분리한다 |
| "남의 주문 조회는 403인가요, 404로 숨겨야 하나요?" | 주문 존재 노출 정책 결정 | mismatch 자체를 드러낼지 concealment할지 제품 보안 정책으로 정한다 |

## CS concept 매핑

| shopping-cart 장면 | security 개념 |
|---|---|
| 로그인한 사용자가 `/orders/{id}`를 호출 | authenticated request |
| `orders.read` 같은 API 권한 확인 | scope / action permission |
| 주문의 `memberId`가 현재 사용자와 다름 | ownership mismatch |
| 존재 자체를 숨기기 위해 404 반환 | concealment policy |
| order id만 바꿔 남의 주문을 보는 버그 | IDOR / BOLA |

## 리뷰 신호

- "로그인했는데 왜 이 주문은 못 보나요?"는 authn과 ownership을 나누라는 말이다.
- "`orders.read` scope가 있으면 전체 주문 조회인가요?"는 scope와 object ownership을 구분하라는 질문이다.
- "남의 주문이면 403인가 404인가요?"는 제품 보안 정책과 concealment를 결정하라는 뜻이다.
- "repository에서 찾은 뒤 memberId를 비교하나요?"는 resource-level authorization 위치를 확인하라는 신호다.

## 판단 순서

1. principal이 있는지 확인한다.
2. endpoint action을 호출할 permission/scope가 있는지 확인한다.
3. 조회한 order가 현재 principal의 소유인지 확인한다.
4. mismatch를 `403`으로 드러낼지 `404`로 숨길지 정책을 정한다.

이 순서를 코드에 드러내면 shopping-cart의 order detail, payment detail, refund history API가 단순 "로그인 필요" 수준에서 멈추지 않는다.
