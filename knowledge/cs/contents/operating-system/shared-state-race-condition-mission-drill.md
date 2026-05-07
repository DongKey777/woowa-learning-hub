---
schema_version: 3
title: Shared State Race Condition Mission Drill
concept_id: operating-system/shared-state-race-condition-mission-drill
canonical: false
category: operating-system
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
- race-condition
- shared-state
- thread-safety
- mission-drill
aliases:
- shared state race condition mission drill
- 공유 상태 race condition 드릴
- singleton bean mutable state race
- reservation counter lost update
- shopping cart quantity race drill
symptoms:
- singleton Bean이나 service 필드에 mutable state를 두고 요청마다 값이 꼬인다
- 동시에 장바구니 수량을 바꾸면 업데이트가 사라지는 것처럼 보인다
- race condition과 DB lost update, thread safety를 한 번에 섞어 본다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- operating-system/thread-safety-and-race-condition
- operating-system/atomic-vs-lock
next_docs:
- database/roomescape-reservation-concurrency-bridge
- database/shopping-cart-cart-item-quantity-lost-update-version-cas-bridge
- spring/shopping-cart-current-cart-singleton-bean-scope-bridge
linked_paths:
- contents/operating-system/thread-safety-and-race-condition.md
- contents/operating-system/atomic-vs-lock.md
- contents/database/roomescape-reservation-concurrency-bridge.md
- contents/database/shopping-cart-cart-item-quantity-lost-update-version-cas-bridge.md
- contents/spring/shopping-cart-current-cart-singleton-bean-scope-bridge.md
- contents/spring/baseball-game-state-singleton-bean-scope-bridge.md
confusable_with:
- operating-system/thread-safety-and-race-condition
- operating-system/atomic-vs-lock
- database/shopping-cart-cart-item-quantity-lost-update-version-cas-bridge
forbidden_neighbors:
- contents/software-engineering/service-layer-basics.md
expected_queries:
- singleton bean mutable state race condition을 문제로 연습하고 싶어
- 장바구니 수량 동시 수정이 thread race인지 DB lost update인지 어떻게 구분해?
- roomescape 예약 동시 생성과 shared state race를 비교해줘
- thread safety와 database concurrency를 미션 예제로 드릴해줘
contextual_chunk_prefix: |
  이 문서는 shared state race condition mission drill이다. singleton Bean
  mutable field, concurrent request, cart quantity lost update, reservation
  duplicate creation, thread race vs database lost update 같은 미션 질문을
  OS thread safety 판별 문제로 매핑한다.
---
# Shared State Race Condition Mission Drill

> 한 줄 요약: 여러 요청이 같은 변경 가능한 값을 공유하면, 코드 안 race인지 DB 안 lost update인지 먼저 분리해야 한다.

**난이도: Beginner**

## 문제 1

상황:

```text
Spring singleton service 필드에 currentCart를 저장하고 요청마다 갱신한다.
```

답:

thread safety 문제가 맞다. 여러 요청 thread가 같은 service instance의 mutable field를 공유하므로 사용자 간 상태가 섞일 수 있다.

## 문제 2

상황:

```text
cart_item row의 quantity를 두 요청이 동시에 읽고 각각 +1 저장해 하나만 반영된다.
```

답:

DB lost update 쪽이 더 가깝다. Java shared field 문제가 아니라 같은 row를 읽고 쓰는 transaction concurrency 문제다.

## 문제 3

상황:

```text
reservation 생성 가능 여부를 메모리 Set으로만 확인하고 DB unique constraint가 없다.
```

답:

둘 다 위험하다. 메모리 Set은 multi-thread/multi-instance에서 안전하지 않고, 최종 중복 방지는 DB constraint나 lock 같은 저장소 경계가 필요하다.

## 빠른 체크

| 신호 | 먼저 볼 개념 |
|---|---|
| service field가 요청 사이에 변함 | thread safety |
| 같은 DB row 수량이 덮어써짐 | lost update |
| 같은 slot reservation이 두 개 생김 | uniqueness / transaction |
| counter 한 값만 안전하게 올림 | atomic 후보 |
