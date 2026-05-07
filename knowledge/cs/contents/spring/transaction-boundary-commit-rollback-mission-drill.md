---
schema_version: 3
title: Transaction Boundary Commit / Rollback Mission Drill
concept_id: spring/transaction-boundary-commit-rollback-mission-drill
canonical: false
category: spring
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- transaction-boundary
- commit-rollback
- service-layer
- transactional-test
aliases:
- transaction boundary mission drill
- commit rollback boundary drill
- 트랜잭션 경계 드릴
- @Transactional mission exercise
- service transaction drill
symptoms:
- 어느 service 메서드에 @Transactional을 붙여야 하는지 모르겠다
- 예외가 나면 어디까지 rollback되어야 하는지 코드에서 바로 안 보인다
- 테스트에서 flush와 commit을 같은 검증으로 취급한다
intents:
- drill
- troubleshooting
- design
prerequisites:
- spring/transactional-basics
- database/transaction-basics
next_docs:
- spring/roomescape-transactional-boundary-bridge
- spring/shopping-cart-payment-transaction-boundary-bridge
- software-engineering/transactional-test-rollback-vs-commit-boundary-card
linked_paths:
- contents/spring/spring-transactional-basics.md
- contents/database/transaction-basics.md
- contents/spring/roomescape-transactional-boundary-bridge.md
- contents/spring/shopping-cart-payment-transaction-boundary-bridge.md
- contents/software-engineering/transactional-test-rollback-vs-commit-boundary-card.md
- contents/software-engineering/testtransaction-vs-commit-choice-mini-card.md
confusable_with:
- spring/transactional-basics
- database/transaction-basics
- software-engineering/transactional-test-rollback-vs-commit-boundary-card
forbidden_neighbors:
- contents/software-engineering/dummy-vs-stub-beginner-mini-card.md
expected_queries:
- 미션 코드에서 @Transactional 경계를 문제로 연습하고 싶어
- service 메서드 중 어디가 commit owner인지 드릴로 풀어줘
- 예외가 나면 예약 저장과 결제 요청이 어디까지 rollback돼야 해?
- flush와 commit 차이를 미션 트랜잭션 테스트로 연습하고 싶어
contextual_chunk_prefix: |
  이 문서는 Spring @Transactional 경계를 미션 코드 상황으로 연습하는 drill이다.
  commit owner, rollback boundary, service method, roomescape reservation,
  shopping-cart payment, flush vs commit 같은 표현을 트랜잭션 경계 판단 문제로
  매핑한다.
---
# Transaction Boundary Commit / Rollback Mission Drill

> 한 줄 요약: 트랜잭션 경계는 repository마다 붙이는 장식이 아니라, 하나의 유스케이스가 함께 성공하거나 함께 실패해야 하는 범위다.

**난이도: Beginner**

## 문제 1

```text
reserve()가 예약 저장, 포인트 차감, 알림 전송을 한 메서드에서 수행한다.
```

답:

예약 저장과 포인트 차감은 같은 business state transition이면 같은 transaction 후보가 될 수 있다. 알림 전송은 외부 I/O라 commit 이후 outbox나 after-commit 경계로 분리하는 편이 안전하다.

## 문제 2

```text
checkout()이 order 저장 전에 payment API를 호출하고, 실패하면 DB 작업은 없다.
```

답:

외부 승인과 로컬 DB commit을 하나의 rollback으로 착각하면 안 된다. 승인 결과를 어떻게 기록하고 실패 보상을 어떻게 할지 별도 설계가 필요하다.

## 문제 3

```text
@DataJpaTest에서 flush가 성공했으니 AFTER_COMMIT listener도 검증됐다고 본다.
```

답:

아니다. `flush`는 SQL 동기화이고 `commit`은 트랜잭션 확정이다. commit 이후 동작은 별도 commit-visible 테스트로 본다.

## 빠른 체크

| 질문 | 판단 |
|---|---|
| 한 유스케이스의 상태 변경인가 | service/application method 경계 |
| 외부 I/O가 섞였는가 | commit 밖으로 분리 후보 |
| 테스트가 rollback 안쪽만 보는가 | commit-visible 보강 후보 |
| 여러 repository가 각각 commit하는가 | transaction owner 불명확 신호 |
