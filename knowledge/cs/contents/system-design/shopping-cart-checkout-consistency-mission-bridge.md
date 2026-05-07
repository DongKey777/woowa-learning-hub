---
schema_version: 3
title: Shopping Cart Checkout Consistency Mission Bridge
concept_id: system-design/shopping-cart-checkout-consistency-mission-bridge
canonical: false
category: system-design
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: mixed
source_priority: 78
mission_ids:
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- shopping-cart
- checkout-consistency
- idempotency
- read-after-write
aliases:
- shopping cart checkout consistency bridge
- 장바구니 checkout consistency bridge
- checkout version idempotency read after write
- 주문 완료가 안 보이는 checkout 설계
- duplicate checkout stale confirmation bridge
symptoms:
- checkout 요청이 timeout 뒤 재시도되면 주문이나 결제가 두 번 생길까 봐 불안하다
- 주문 생성은 성공했는데 확인 화면에서 방금 주문이 안 보인다
- cart version, idempotency key, read-after-write를 한 흐름으로 연결하지 못한다
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- system-design/consistency-idempotency-async-workflow-foundations
- system-design/checkout-consistency-walkthrough
next_docs:
- system-design/payment-system-ledger-idempotency-reconciliation-design
- database/shopping-cart-payment-idempotency-stock-bridge
- spring/shopping-cart-order-complete-after-commit-outbox-bridge
linked_paths:
- contents/system-design/checkout-consistency-walkthrough.md
- contents/system-design/consistency-idempotency-async-workflow-foundations.md
- contents/system-design/write-order-vs-precondition-primer.md
- contents/system-design/writes-follow-reads-primer.md
- contents/system-design/read-after-write-consistency-basics.md
- contents/database/shopping-cart-payment-idempotency-stock-bridge.md
- contents/spring/shopping-cart-order-complete-after-commit-outbox-bridge.md
confusable_with:
- system-design/checkout-consistency-walkthrough
- system-design/consistency-idempotency-async-workflow-foundations
- database/shopping-cart-payment-idempotency-stock-bridge
forbidden_neighbors:
- contents/design-pattern/shopping-cart-checkout-pattern-decision-guide.md
expected_queries:
- shopping-cart checkout consistency를 system design 관점으로 연결해줘
- cart version idempotency key read after write를 한 흐름으로 설명해줘
- 주문은 됐는데 확인 화면에 안 보이는 문제를 checkout 설계로 풀어줘
- 중복 결제와 stale confirmation을 동시에 막는 checkout bridge가 필요해
contextual_chunk_prefix: |
  이 문서는 shopping-cart checkout consistency mission_bridge다. cart version,
  expected version, idempotency key, duplicate checkout retry, read-after-write
  confirmation, order complete not visible 같은 미션 질문을 system design의
  consistency/idempotency/read path 문제로 매핑한다.
---
# Shopping Cart Checkout Consistency Mission Bridge

> 한 줄 요약: checkout은 "최신 장바구니로 한 번만 결제하고, 성공 직후 그 주문을 바로 보여 주는" 세 가지 일관성 질문을 동시에 갖는다.

**난이도: Intermediate**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "checkout timeout 뒤 다시 누르면 주문이나 결제가 두 번 생길까 봐 불안해요" | 장바구니 결제 승인 재시도 | idempotency key와 replay-safe retry로 같은 시도를 식별한다 |
| "주문 생성은 성공했는데 확인 화면에서 방금 주문이 안 보여요" | checkout 완료 직후 stale confirmation | read-after-write consistency와 읽기 경로를 같이 본다 |
| "cart version, idempotency key, outbox가 한 흐름으로 연결이 안 돼요" | 결제 전 장바구니 변경, 결제 승인, 후속 작업 처리 | checkout을 precondition, 중복 방지, commit 후 읽기, async handoff로 나눈다 |

## CS concept 매핑

| shopping-cart 장면 | system design 개념 |
|---|---|
| 사용자가 본 cart가 checkout 직전에 바뀜 | write precondition / expected version |
| timeout 뒤 checkout 버튼을 다시 누름 | idempotency key / replay-safe retry |
| 결제는 성공했는데 주문 확인 화면이 비어 있음 | read-after-write consistency |
| 주문 완료 후 알림, 재고 차감, 쿠폰 소진이 이어짐 | async workflow / outbox |
| 같은 결제 승인 사실이 API와 webhook으로 모두 들어옴 | event identity / deduplication |

## 리뷰 신호

- "중복 요청이면 그냥 막으면 되나요?"는 idempotent replay와 conflict를 구분하라는 신호다.
- "주문 완료 직후 목록에 안 보입니다"는 쓰기 성공과 읽기 경로가 갈라져 있는지 보라는 말이다.
- "cart version을 왜 확인하나요?"는 사용자가 본 기준선이 아직 유효한지 확인하라는 뜻이다.
- "결제 성공 후 후속 작업 실패는 어떻게 하나요?"는 transaction boundary와 async handoff를 나누라는 뜻이다.

## 판단 순서

1. checkout request가 어떤 cart version을 기준으로 하는지 확인한다.
2. 같은 checkout attempt가 재시도되어도 같은 결과를 재생할 key를 둔다.
3. order/payment commit 뒤 확인 화면은 방금 쓴 데이터를 볼 수 있는 read path를 탄다.
4. 결제 후 부작용은 commit 이후 outbox나 event handoff로 분리할지 결정한다.

이 네 질문이 연결되면 shopping-cart 미션의 checkout 리뷰가 단순 controller/service 논쟁을 넘어 system design 언어로 설명된다.
