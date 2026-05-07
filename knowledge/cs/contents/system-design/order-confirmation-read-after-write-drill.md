---
schema_version: 3
title: Order Confirmation Read After Write Drill
concept_id: system-design/order-confirmation-read-after-write-drill
canonical: false
category: system-design
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- read-after-write
- order-confirmation
- stale-read
- recent-write-routing
aliases:
- order confirmation read after write drill
- 주문 완료 직후 안 보임 드릴
- read your writes confirmation page
- stale order confirmation exercise
- recent write primary fallback drill
symptoms:
- 주문이나 예약 생성은 성공했는데 바로 다음 화면에서 방금 데이터가 안 보인다
- 목록 조회 replica나 cache 때문에 성공 직후 stale read가 발생한다
- retry나 새로고침보다 read path를 먼저 봐야 하는지 헷갈린다
intents:
- drill
- troubleshooting
- design
prerequisites:
- system-design/read-after-write-consistency-basics
- system-design/writes-follow-reads-primer
next_docs:
- system-design/read-after-write-routing-primer
- system-design/shopping-cart-checkout-consistency-mission-bridge
- database/shopping-cart-order-complete-read-your-writes-bridge
linked_paths:
- contents/system-design/read-after-write-consistency-basics.md
- contents/system-design/writes-follow-reads-primer.md
- contents/system-design/read-after-write-routing-primer.md
- contents/system-design/shopping-cart-checkout-consistency-mission-bridge.md
- contents/database/shopping-cart-order-complete-read-your-writes-bridge.md
- contents/system-design/monotonic-reads-and-session-guarantees-primer.md
confusable_with:
- system-design/read-after-write-consistency-basics
- system-design/read-after-write-routing-primer
- system-design/writes-follow-reads-primer
forbidden_neighbors:
- contents/database/shopping-cart-payment-idempotency-stock-bridge.md
expected_queries:
- 주문 완료 직후 방금 주문이 안 보이는 문제를 드릴로 연습하고 싶어
- read after write와 stale confirmation을 어떻게 구분해?
- shopping-cart order confirmation stale read를 system design으로 설명해줘
- 예약 생성 성공 직후 목록에 안 보일 때 read path부터 보는 기준은?
contextual_chunk_prefix: |
  이 문서는 order confirmation read-after-write drill이다. order created
  but not visible, reservation saved but list stale, replica lag, cache stale,
  recent-write routing, primary fallback, read-your-writes 같은 질문을
  system design 판별 문제로 매핑한다.
---
# Order Confirmation Read After Write Drill

> 한 줄 요약: 성공 직후 확인 화면이 비어 있으면 쓰기 실패보다 읽기 경로가 방금 쓴 데이터를 볼 수 있는지 먼저 본다.

**난이도: Beginner**

## 문제 1

상황:

```text
POST /orders는 201을 반환했지만 바로 이동한 GET /orders/{id}가 404다.
```

답:

read-after-write 문제 후보가 맞다. write path는 성공했지만 read path가 replica/cache를 타면서 아직 새 row를 못 볼 수 있다.

## 문제 2

상황:

```text
주문 완료 화면만 primary read로 보내고 일반 목록은 replica read를 유지한다.
```

답:

recent-write routing 후보가 된다. 모든 읽기를 primary로 바꾸지 않고, 방금 쓴 사용자의 확인 경로만 강하게 읽는다.

## 문제 3

상황:

```text
사용자가 새로고침하면 언젠가 보이니 retry 버튼만 둔다.
```

답:

운영 우회는 될 수 있지만 설계 설명은 약하다. 성공 응답 직후의 사용자 경험이 중요하면 read path 보장을 명시해야 한다.

## 빠른 체크

| 신호 | 먼저 볼 것 |
|---|---|
| 성공 직후만 안 보임 | read-after-write |
| 오래 지나도 안 보임 | write failure / routing bug |
| 다른 기기에서는 보임 | session guarantee |
| 목록만 늦음 | cache/replica invalidation |
