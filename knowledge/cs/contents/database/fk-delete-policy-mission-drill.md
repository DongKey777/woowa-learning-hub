---
schema_version: 3
title: Foreign Key Delete Policy Mission Drill
concept_id: database/fk-delete-policy-mission-drill
canonical: false
category: database
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- foreign-key
- delete-policy
- restrict-cascade
- mission-drill
aliases:
- foreign key delete policy mission drill
- FK 삭제 정책 드릴
- restrict cascade soft delete drill
- roomescape member reservation fk drill
- shopping cart order history fk drill
symptoms:
- FK 때문에 부모 row 삭제가 실패했을 때 cascade를 붙이면 되는지 헷갈린다
- 주문/예약 이력을 보존해야 하는데 물리 삭제와 soft delete를 섞어 본다
- FK는 참조 무결성만 보장하고 비즈니스 보존 정책은 따로 봐야 한다는 감각이 약하다
intents:
- drill
- design
- troubleshooting
prerequisites:
- database/primary-foreign-key-basics
- database/roomescape-member-reservation-fk-delete-policy-bridge
next_docs:
- database/foreign-key-cascade-lock-surprises
- database/soft-delete-uniqueness-indexing-lifecycle
- software-engineering/shopping-cart-order-snapshot-from-cart-bridge
linked_paths:
- contents/database/primary-foreign-key-basics.md
- contents/database/roomescape-member-reservation-fk-delete-policy-bridge.md
- contents/database/foreign-key-cascade-lock-surprises.md
- contents/database/soft-delete-uniqueness-indexing-lifecycle.md
- contents/software-engineering/shopping-cart-order-snapshot-from-cart-bridge.md
- contents/database/shopping-cart-order-item-snapshot-table-bridge.md
confusable_with:
- database/primary-foreign-key-basics
- database/foreign-key-cascade-lock-surprises
- database/soft-delete-uniqueness-indexing-lifecycle
forbidden_neighbors:
- contents/database/roomescape-reservation-concurrency-bridge.md
expected_queries:
- FK delete policy를 roomescape shopping-cart 예제로 연습하고 싶어
- 예약이나 주문 이력이 있을 때 restrict cascade soft delete를 어떻게 골라?
- 부모 삭제 실패를 cascade로 해결해도 되는지 드릴로 판단해줘
- foreign key와 비즈니스 이력 보존 정책을 문제로 나눠줘
contextual_chunk_prefix: |
  이 문서는 foreign key delete policy mission drill이다. restrict, cascade,
  soft delete, reservation history, order history, member delete, order item
  snapshot 같은 질문을 참조 무결성과 이력 보존 판단 문제로 매핑한다.
---
# Foreign Key Delete Policy Mission Drill

> 한 줄 요약: FK 삭제 정책은 "DB가 지울 수 있나"보다 "이 이력을 지워도 되는가"를 먼저 묻는다.

**난이도: Beginner**

## 문제 1

상황:

```text
예약이 있는 member를 삭제하려고 하니 FK 오류가 난다.
```

답:

DB가 참조 무결성을 지킨 것이다. 바로 cascade를 붙이기 전에 기존 예약 이력을 보존해야 하는지 먼저 결정해야 한다.

## 문제 2

상황:

```text
주문 삭제 시 order_item도 같이 지우면 구현이 편하다.
```

답:

쇼핑 주문 이력이라면 위험하다. 주문 완료 이력은 감사/환불/CS와 연결될 수 있으므로 snapshot 보존이나 상태 변경이 더 적절할 수 있다.

## 문제 3

상황:

```text
soft delete를 선택했지만 unique constraint는 그대로다.
```

답:

추가 검토가 필요하다. soft-deleted row가 unique key를 계속 점유할지, active row만 unique할지 indexing policy를 정해야 한다.

## 빠른 체크

| 질문 | 후보 |
|---|---|
| 자식 이력을 지워도 되는가 | cascade 가능성 |
| 자식 이력을 보존해야 하는가 | restrict / soft delete / snapshot |
| 삭제된 row도 조회에서 제외해야 하는가 | active predicate |
| unique 재사용이 필요한가 | partial/functional index 또는 policy |
