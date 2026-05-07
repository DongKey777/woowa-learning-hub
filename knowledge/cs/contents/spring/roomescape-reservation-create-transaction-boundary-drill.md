---
schema_version: 3
title: Roomescape Reservation Create Transaction Boundary Drill
concept_id: spring/roomescape-reservation-create-transaction-boundary-drill
canonical: false
category: spring
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/spring-roomescape
review_feedback_tags:
- roomescape
- transactional-boundary
- duplicate-reservation
- commit-rollback
aliases:
- roomescape reservation transaction drill
- 룸이스케이프 예약 생성 트랜잭션 드릴
- duplicate reservation transaction boundary
- reservation create rollback commit drill
- Spring transactional roomescape drill
symptoms:
- roomescape 예약 생성 중 예외가 나면 어느 저장이 rollback되는지 헷갈린다
- 중복 예약 검사와 저장을 다른 트랜잭션처럼 다뤄도 되는지 모르겠다
- '@Transactional을 controller에 붙일지 service에 붙일지 리뷰에서 지적받았다'
intents:
- drill
- troubleshooting
- design
prerequisites:
- spring/transactional-basics
- spring/roomescape-transactional-boundary-bridge
next_docs:
- database/roomescape-reservation-concurrency-bridge
- spring/transaction-boundary-commit-rollback-mission-drill
- spring/roomescape-duplicate-reservation-sqlexception-translation-bridge
linked_paths:
- contents/spring/spring-transactional-basics.md
- contents/spring/roomescape-transactional-boundary-bridge.md
- contents/database/roomescape-reservation-concurrency-bridge.md
- contents/spring/transaction-boundary-commit-rollback-mission-drill.md
- contents/spring/roomescape-duplicate-reservation-sqlexception-translation-bridge.md
- contents/database/transaction-basics.md
confusable_with:
- spring/roomescape-transactional-boundary-bridge
- spring/transaction-boundary-commit-rollback-mission-drill
- database/roomescape-reservation-concurrency-bridge
forbidden_neighbors:
- contents/spring/spring-transactional-self-invocation-practice-drill.md
expected_queries:
- roomescape 예약 생성 트랜잭션 경계를 문제로 연습하고 싶어
- 중복 예약 검사와 저장은 같은 transaction에 있어야 해?
- service에 @Transactional을 붙이라는 리뷰가 왜 나왔는지 드릴로 풀어줘
- 예약 생성 중 예외가 나면 commit rollback을 어떻게 판단해?
contextual_chunk_prefix: |
  이 문서는 Spring Roomescape reservation create transaction drill이다.
  duplicate reservation check, save, rollback, commit, service-level
  @Transactional, SQL exception translation 같은 질문을 짧은 판별 문제로
  매핑한다.
---
# Roomescape Reservation Create Transaction Boundary Drill

> 한 줄 요약: 예약 생성은 "가능한지 확인"과 "저장"이 같은 유스케이스 안에서 원자적으로 끝나야 한다.

**난이도: Beginner**

## 문제 1

상황:

```text
service가 중복 예약을 먼저 조회하고, 같은 메서드에서 Reservation을 저장한다.
```

답:

트랜잭션 경계 후보가 맞다. 같은 유스케이스 안에서 조회와 저장이 함께 성공하거나 함께 실패해야 하므로 service method에 transaction boundary를 두는 편이 자연스럽다.

## 문제 2

상황:

```text
중복 예약 조회는 service A, 저장은 service B의 별도 public method에서 각각 @Transactional로 실행된다.
```

답:

읽기와 쓰기 사이에 틈이 생긴다. 단순 코드 분리만으로는 동시 요청 안전성이 생기지 않고, DB unique constraint나 locking 같은 저장소 보장이 필요할 수 있다.

## 문제 3

상황:

```text
예약 저장 후 알림 발송에서 예외가 나서 예약까지 rollback됐다.
```

답:

예약 생성과 알림 발송을 같은 transaction outcome에 묶을지 결정해야 한다. roomescape 기본 단계라면 먼저 예약 저장의 원자성을 지키고, 부가 작업은 after commit 또는 별도 실패 처리 후보로 본다.

## 빠른 체크

| 질문 | 판단 |
|---|---|
| reservation row가 저장되기 전 검증인가 | 같은 유스케이스 transaction 후보 |
| DB unique constraint 위반인가 | exception translation과 conflict 응답 후보 |
| 같은 시간 슬롯 동시 생성인가 | transaction만이 아니라 DB 제약/lock 후보 |
| 저장 후 부가 작업 실패인가 | rollback에 묶을지 분리할지 결정 |
