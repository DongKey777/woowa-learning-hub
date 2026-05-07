---
schema_version: 3
title: Shopping Cart Order Item Snapshot Table Bridge
concept_id: database/shopping-cart-order-item-snapshot-table-bridge
canonical: false
category: database
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: mixed
source_priority: 78
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- shopping-cart
- order-snapshot
- table-modeling
- checkout-consistency
aliases:
- shopping cart order item snapshot table
- order snapshot table bridge
- 장바구니 주문 스냅샷 테이블
- checkout order item modeling
- cart item copy to order item
symptoms:
- 주문 완료 후 장바구니 상품이 바뀌면 과거 주문 금액도 바뀌어 보인다
- cart item과 order item을 같은 테이블처럼 다뤄 checkout 시점 기록이 보존되지 않는다
- 결제 총액 재검증과 주문 snapshot 저장을 같은 책임으로 섞는다
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- database/sql-relational-modeling-basics
- software-engineering/shopping-cart-order-snapshot-from-cart-bridge
next_docs:
- database/transaction-basics
- spring/shopping-cart-payment-transaction-boundary-bridge
- software-engineering/shopping-cart-checkout-total-revalidation-source-of-truth-bridge
linked_paths:
- contents/database/sql-reading-relational-modeling-primer.md
- contents/database/transaction-basics.md
- contents/software-engineering/shopping-cart-order-snapshot-from-cart-bridge.md
- contents/spring/shopping-cart-payment-transaction-boundary-bridge.md
- contents/software-engineering/shopping-cart-checkout-total-revalidation-source-of-truth-bridge.md
- contents/software-engineering/shopping-cart-checkout-service-layer-bridge.md
confusable_with:
- software-engineering/shopping-cart-order-snapshot-from-cart-bridge
- software-engineering/shopping-cart-checkout-total-revalidation-source-of-truth-bridge
- spring/shopping-cart-payment-transaction-boundary-bridge
forbidden_neighbors:
- contents/database/pagination-offset-vs-seek.md
expected_queries:
- shopping-cart 주문 완료 시 cart item을 order item snapshot으로 왜 복사해야 해?
- 장바구니 상품이 바뀌어도 과거 주문 금액이 보존되려면 table을 어떻게 나눠?
- checkout 총액 재검증과 order snapshot 저장을 DB 모델링으로 연결해줘
- cart item과 order item을 같은 row로 쓰면 어떤 문제가 생겨?
contextual_chunk_prefix: |
  이 문서는 shopping-cart checkout에서 cart item을 order item snapshot table로
  복사해야 하는 이유를 database modeling과 연결하는 mission_bridge다.
  주문 완료, 과거 가격 보존, cart item 변경, order snapshot, checkout total
  revalidation 같은 질문을 저장 모델과 transaction boundary로 매핑한다.
---
# Shopping Cart Order Item Snapshot Table Bridge

> 한 줄 요약: 주문은 "현재 장바구니를 계속 참조하는 것"이 아니라 checkout 순간의 상품, 수량, 가격을 주문 기록으로 복사해 보존하는 모델에 가깝다.

**난이도: Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "주문 완료 후 장바구니 상품이 바뀌면 과거 주문 금액도 바뀌어 보여요" | order가 cart item/current product를 계속 참조하는 모델 | 주문 시점의 상품, 수량, 가격을 order item snapshot으로 복사한다 |
| "cart item과 order item을 같은 테이블처럼 다뤄도 되나요?" | 장바구니 lifecycle과 주문 이력 lifecycle이 섞인 DB 설계 | 현재 구매 후보와 확정된 과거 사실을 다른 table/model로 본다 |
| "총액 재검증과 주문 snapshot 저장을 같은 책임으로 섞고 있어요" | checkout command 처리와 order persistence 경계 | 서버 재계산 후 그 결과를 transaction 안에서 snapshot으로 굳힌다 |

## CS concept 매핑

| shopping-cart 장면 | DB 개념 |
|---|---|
| 장바구니 상품을 주문으로 확정 | state transition |
| 주문 시점 가격 보존 | snapshot |
| cart item 삭제 후 주문 조회 | historical record |
| 결제 직전 금액 재검증 | source of truth |
| order/order_item 저장 | transaction boundary |

## 왜 같은 row를 계속 참조하면 위험한가

장바구니는 "현재 구매 후보"이고 주문은 "확정된 과거 사실"이다.
상품 가격이나 수량이 checkout 후 바뀌어도 과거 주문의 금액과 항목은 바뀌면 안 된다.

그래서 checkout 시점에는 보통:

1. cart item을 다시 읽고 가격/수량을 검증한다.
2. order row를 만든다.
3. order_item snapshot row를 만든다.
4. cart를 비우거나 상태를 바꾼다.

## 흔한 리뷰 신호

- "주문 상세가 cart를 계속 따라가요"는 snapshot 부재 신호다.
- "총액은 request 값으로 믿고 저장해요"는 source of truth 문제가 있다.
- "cart 삭제하면 주문도 사라져요"는 lifecycle이 다른 데이터를 같은 모델로 묶은 신호다.
