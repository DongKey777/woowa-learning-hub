---
schema_version: 3
title: Transaction Lost Update Mission Drill
concept_id: database/transaction-lost-update-mission-drill
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
- transaction
- lost-update
- concurrency
- mission-drill
aliases:
- transaction lost update mission drill
- lost update transaction drill
- 장바구니 수량 동시 수정 드릴
- 예약 중복 생성 트랜잭션 드릴
- optimistic lock version CAS practice
symptoms:
- '@Transactional이 있으면 동시성도 자동으로 안전하다고 생각한다'
- 두 요청이 같은 수량을 읽고 저장해 하나의 업데이트가 사라진다
- roomescape 중복 예약과 shopping-cart 수량 lost update를 같은 문제로 뭉갠다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- database/transaction-basics
- database/transaction-isolation-basics
next_docs:
- database/roomescape-reservation-concurrency-bridge
- database/shopping-cart-cart-item-quantity-lost-update-version-cas-bridge
- operating-system/shared-state-race-condition-mission-drill
linked_paths:
- contents/database/transaction-basics.md
- contents/database/transaction-isolation-basics.md
- contents/database/lock-basics.md
- contents/database/roomescape-reservation-concurrency-bridge.md
- contents/database/shopping-cart-cart-item-quantity-lost-update-version-cas-bridge.md
- contents/operating-system/shared-state-race-condition-mission-drill.md
confusable_with:
- database/transaction-basics
- database/roomescape-reservation-concurrency-bridge
- database/shopping-cart-cart-item-quantity-lost-update-version-cas-bridge
forbidden_neighbors:
- contents/operating-system/thread-safety-and-race-condition.md
expected_queries:
- '@Transactional과 lost update를 미션 예제로 연습하고 싶어'
- 장바구니 수량 동시 수정이 왜 하나만 반영되는지 드릴로 풀어줘
- roomescape 중복 예약과 shopping-cart lost update 차이를 문제로 비교해줘
- transaction이 있으면 동시성도 자동 해결되는지 판단하는 drill을 줘
contextual_chunk_prefix: |
  이 문서는 transaction lost update mission drill이다. @Transactional,
  commit/rollback, isolation, lock, optimistic version, cart quantity lost
  update, duplicate reservation 같은 질문을 DB transaction concurrency
  판별 문제로 매핑한다.
---
# Transaction Lost Update Mission Drill

> 한 줄 요약: transaction은 실패 범위를 묶지만, 동시에 같은 값을 바꾸는 충돌까지 자동으로 해결하지는 않는다.

**난이도: Beginner**

## 문제 1

상황:

```text
두 요청이 cart_item quantity=1을 읽고 각각 +1을 저장해 최종 quantity가 2가 됐다.
```

답:

lost update다. 기대가 3이라면 optimistic lock version, atomic update, pessimistic lock 같은 충돌 제어가 필요하다.

## 문제 2

상황:

```text
reservation 중복 검사를 SELECT로 하고 바로 INSERT한다. 두 요청이 동시에 통과한다.
```

답:

중복 생성 race다. transaction만으로 충분하지 않을 수 있고, unique constraint나 locking/read strategy가 필요하다.

## 문제 3

상황:

```text
@Transactional이 붙었으니 재고 차감은 무조건 안전하다고 말한다.
```

답:

불충분하다. rollback 범위는 생겼지만, 동시 요청 충돌을 어떻게 감지/직렬화할지는 별도 설계다.

## 빠른 체크

| 신호 | 먼저 볼 것 |
|---|---|
| 같이 성공/실패해야 함 | transaction boundary |
| 같은 row 값을 덮어씀 | lost update |
| 존재하지 않으면 insert | unique constraint / lock |
| 충돌 시 재시도 가능 | optimistic version / CAS |
