---
schema_version: 3
title: 트랜잭션 기초
concept_id: database/transaction-basics
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- transaction
- commit
- rollback
- acid
aliases:
- transaction
- commit
- rollback
- ACID
- 트랜잭션
- 커밋
- 롤백
- all or nothing
- 다 되거나 다 취소
- 여러 SQL 작업을 하나로 묶기
- SQL 여러 개 같이 성공 같이 실패
symptoms:
- 주문 저장과 재고 차감을 같이 성공하거나 같이 실패하게 묶어야 하는 이유가 흐리다
- '@Transactional이 있으면 동시성 문제도 자동으로 해결된다고 생각한다'
- commit과 rollback이 언제 결정되는지 service method 경계와 연결하지 못한다
intents:
- definition
prerequisites:
- database/database-first-step-bridge
next_docs:
- database/transaction-isolation-basics
- database/lock-basics
- spring/transactional-basics
linked_paths:
- contents/database/database-first-step-bridge.md
- contents/database/transaction-isolation-basics.md
- contents/database/lock-basics.md
- contents/database/jdbc-jpa-mybatis-basics.md
- contents/database/mission-code-reading-db-checklist.md
- contents/spring/spring-transactional-basics.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- transaction이 뭐야?
- 트랜잭션이 뭐야?
- commit이랑 rollback은 뭐야?
- 주문 저장과 재고 차감은 왜 같은 트랜잭션으로 묶어?
- 여러 SQL 작업을 하나로 묶어서 다 되거나 다 취소되게 하는 게 뭐야?
contextual_chunk_prefix: |
  이 문서는 데이터베이스 입문자가 주문 저장과 재고 차감처럼 여러 변경을 왜
  한 묶음으로 commit하거나 rollback해야 하는지 처음 잡는 primer다. 같이
  성공하거나 같이 실패, transaction이 뭐야, commit rollback 차이,
  @transactional 전에 트랜잭션 그림, 실패 범위 묶기, 여러 SQL 작업을 하나로
  묶어서 다 되거나 다 취소되게 하는 원리 같은 자연어 질문이 이 문서의 기본
  경계 감각에 매핑된다.
---
# 트랜잭션 기초 (Transaction Basics)

> 한 줄 요약: 트랜잭션은 "여기까지 같이 성공하거나 같이 실패한다"를 정하는 묶음이다. `deadlock`, `retry`, `savepoint`는 이 primer의 본문보다 다음 관련 문서 가지에 가깝다.

**난이도: 🟢 Beginner**

## 미션 진입 증상

| 미션 장면 | 이 문서에서 먼저 잡을 질문 |
|---|---|
| 주문 저장은 됐는데 재고 차감에서 예외가 난다 | 어디까지 같이 rollback할 것인가 |
| 예약 생성 중 중복 예외가 난다 | 저장 실패를 같은 transaction outcome으로 묶을 것인가 |
| `@Transactional`을 붙였는데 동시 수정이 꼬인다 | 실패 범위와 동시성 제어를 분리해 봤는가 |

관련 문서:

- [Database First-Step Bridge](./database-first-step-bridge.md)
- [Database README: 빠른 시작](./README.md#빠른-시작)
- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- [락 기초](./lock-basics.md)
- [Spring @Transactional 기초](../spring/spring-transactional-basics.md)
- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- [미션 코드 독해용 DB 체크리스트](./mission-code-reading-db-checklist.md)

retrieval-anchor-keywords: transaction basics, transaction beginner, commit rollback basics, transaction vs isolation, what is transaction, 트랜잭션이 뭐예요, 트랜잭션 처음, commit rollback 이 뭐예요, @transactional 헷갈려요, 주문 저장 재고 차감 같이 취소, deadlock 은 나중에, transaction basics next step

## 먼저 잡을 그림

트랜잭션은 여러 DB 변경을 하나의 사건처럼 묶는 단위다. 초보자는 "같이 `commit`하거나 같이 `rollback`할 범위"로 먼저 이해하면 된다.

```text
주문 저장
  -> 재고 차감
  -> 둘 다 끝나면 commit
  -> 하나라도 실패하면 rollback
```

이 문서의 질문은 하나다. "무엇을 같이 되돌릴까?"

| 지금 보이는 문제 | 이 문서가 먼저 답하는가? | 왜 그런가 |
|---|---|---|
| 주문 저장과 재고 차감이 같이 취소되어야 한다 | 예 | 실패 단위를 묶는 문제다 |
| `commit`은 했는데 마지막 재고가 두 번 팔렸다 | 아니오 | 동시성 충돌은 다음 단계 문제다 |
| `save()`는 보이는데 SQL이 안 보인다 | 아니오 | 접근 기술 구분이 먼저다 |

예를 들어 주문 저장은 성공했는데 재고 차감에서 예외가 나면, beginner가 먼저 기대해야 하는 결과는 "둘 다 남지 않는다"다. 반대로 "동시에 두 명이 마지막 재고를 집었다"는 문제는 같은 트랜잭션 설명만으로 끝나지 않는다.

## 자주 섞이는 오해

트랜잭션 입문에서는 아래 두 오해만 먼저 끊어도 충분하다.

| 헷갈리는 말 | beginner-first 해석 | 바로 이어질 문서 |
|---|---|---|
| "`@Transactional`이 있으니 동시성도 자동 해결되겠죠?" | 아니다. 트랜잭션은 실패 범위를 묶고, 동시성 충돌 방지는 격리 수준/락 설계가 따로 필요하다 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md), [락 기초](./lock-basics.md) |
| "`@Transactional`이 붙은 줄에서 바로 commit되나요?" | 보통은 메서드 경계가 끝날 때 commit/rollback이 결정된다 | [Spring @Transactional 기초](../spring/spring-transactional-basics.md) |

```text
@Transactional
createOrder()
  -> 주문 저장
  -> 재고 차감
  -> 메서드 끝에서 commit 또는 rollback
```

이 그림은 "어디까지 같이 되돌릴까"를 설명할 뿐이고, "동시에 누가 마지막 재고를 가져가나"까지 자동으로 보장해 주지는 않는다.

비유를 쓰면 트랜잭션은 "같이 묶인 묶음 배송"에 가깝지만, 이 비유는 `all-or-nothing`까지만 설명한다. 먼저 배송 버튼을 누른 사람이 누구냐는 락과 격리 수준 쪽 질문이다.

## 코드에서 보는 순서

처음 코드 독해에서는 아래 세 군데만 보면 된다.

| 먼저 볼 곳 | 초보자용 첫 해석 | 왜 여기서 시작하나 |
|---|---|---|
| service 메서드의 `@Transactional` | 경계를 선언하는 표식이다 | 어디까지 한 묶음인지 먼저 보인다 |
| 그 안에서 호출하는 repository/mapper | 실제 DB 변경 위치다 | 무엇이 함께 취소되는지 연결된다 |
| 트랜잭션 안의 외부 API/오래 걸리는 로직 | 경계가 길어질 수 있는 지점이다 | DB와 무관한 대기가 섞였는지 확인할 수 있다 |

핵심은 "`트랜잭션이 있다`"와 "`동시성 문제가 없다`"를 같은 뜻으로 읽지 않는 것이다.

처음 코드에서 확인할 질문도 셋이면 충분하다.

- 실패하면 같이 되돌려야 하는 DB 변경이 무엇인가?
- 그 변경이 정말 같은 service 경계 안에 모여 있는가?
- 외부 API 호출처럼 오래 걸리는 작업이 같이 묶여 있지는 않은가?

## 여기서 멈추는 기준

beginner primer에서는 아래 단어가 보여도 길게 풀지 않는다.

| 먼저 보인 단어 | 지금 이 문서에서 할 일 | 다음 문서 |
|---|---|---|
| `deadlock`, `lock wait`, `retry` | 동시성/충돌 follow-up이라는 것만 확인한다 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md), [락 기초](./lock-basics.md) |
| `savepoint` | 부분 롤백 세부라는 것만 확인한다 | [Savepoint Rollback, Lock Retention, and Escalation Edge Cases](./savepoint-lock-retention-edge-cases.md) |
| `40001` | 재시도 문서가 필요한 상태라는 것만 확인한다 | [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md) |

입문 목표는 아래 한 줄이면 충분하다.

- 트랜잭션은 "같이 되돌릴 범위"를 정한다.
- "동시에 누가 먼저 이기나"는 다음 문서로 넘긴다.

## 한 줄 정리

트랜잭션 기초의 핵심은 "무엇을 같이 `commit`/`rollback`할까"를 먼저 고정하는 것이고, 충돌 대응이나 재시도 전략은 관련 follow-up 문서로 넘기는 것이다.
