---
schema_version: 3
title: Read Committed vs Repeatable Read Anomalies
concept_id: database/read-committed-repeatable-read-anomalies
canonical: true
category: database
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- isolation-level
- read-committed
- repeatable-read
- phantom-read
- business-invariant
aliases:
- read committed vs repeatable read
- RC vs RR anomaly
- non-repeatable read
- phantom read
- snapshot isolation anomaly
- gap locking disabled
- 격리 수준 이상 현상
- 트랜잭션 격리 수준 비교
- repeatable read phantom
- read committed latest read
symptoms:
- Read Committed와 Repeatable Read의 차이를 최신성 대 관측 일관성 기준으로 설명해야 해
- RR이면 phantom이나 write skew가 전부 막힌다고 오해하고 있어
- 격리수준만 높이면 재고나 예약 같은 비즈니스 불변식이 자동으로 보호되는지 묻고 있어
intents:
- comparison
- definition
- deep_dive
prerequisites:
- database/transaction-isolation-locking
- database/gap-lock-next-key-lock
next_docs:
- database/write-skew-phantom-read-case-studies
- database/mysql-gap-lock-blind-spots-read-committed
- database/postgresql-vs-mysql-isolation-cheat-sheet
linked_paths:
- contents/database/transaction-isolation-locking.md
- contents/database/gap-lock-next-key-lock.md
- contents/database/write-skew-phantom-read-case-studies.md
- contents/database/mysql-gap-lock-blind-spots-read-committed.md
- contents/database/postgresql-vs-mysql-isolation-cheat-sheet.md
confusable_with:
- database/transaction-isolation-locking
- database/gap-lock-next-key-lock
- database/isolation-anomaly-cheat-sheet
- database/range-invariant-enforcement-write-skew-phantom
forbidden_neighbors: []
expected_queries:
- Read Committed와 Repeatable Read는 어떤 이상 현상이 다르게 남아?
- 트랜잭션 격리수준을 RC에서 RR로 올리면 phantom read가 항상 없어져?
- Repeatable Read가 비즈니스 불변식까지 자동으로 지켜준다고 보면 왜 틀려?
- 최신성이 중요한 화면과 일관성이 중요한 배치는 격리수준을 어떻게 다르게 봐야 해?
- MySQL에서 READ COMMITTED로 내리면 gap lock 기반 absence check가 왜 흔들릴 수 있어?
contextual_chunk_prefix: |
  이 문서는 Read Committed와 Repeatable Read의 anomaly 차이를 non-repeatable read, phantom read, snapshot, gap lock, business invariant 관점으로 비교하는 chooser다.
  트랜잭션 격리수준 비교, RC/RR 차이, repeatable read phantom 질문이 본 문서에 매핑된다.
---
# Read Committed와 Repeatable Read의 이상 현상 비교

> 한 줄 요약: Read Committed는 최신성을, Repeatable Read는 관측 일관성을 더 챙기지만, 둘 다 비즈니스 불변식을 자동으로 지켜주지는 않는다.

**난이도: 🔴 Advanced**

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md), [Write Skew and Phantom Read Case Studies](./write-skew-phantom-read-case-studies.md), [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md)
retrieval-anchor-keywords: read committed, repeatable read, non-repeatable read, phantom read, snapshot isolation, gap locking disabled, overlap check phantom, 트랜잭션 격리 수준 이상 현상, isolation level anomaly intro, 격리 수준 phantom non-repeatable dirty, transaction isolation anomaly primer, isolation primer beginner, read committed repeatable read 큰 그림, 트랜잭션 격리 수준 처음 배우는데, isolation locking primer 입문

## 핵심 개념

Read Committed와 Repeatable Read는 둘 다 자주 쓰이지만, 보장 범위가 다르다.

왜 중요한가:

- 같은 쿼리를 다시 읽었을 때 결과가 달라질 수 있는지 이해해야 한다
- 범위 조회와 상태 전이에서 어떤 이상 현상이 남는지 알아야 한다
- 격리수준은 정합성 정책이지, 모든 버그를 막는 만능키가 아니다

핵심 차이는 “현재 커밋된 값만 볼 것인가”와 “한 트랜잭션 내에서 같은 그림을 계속 볼 것인가”다.

## 깊이 들어가기

### 1. Read Committed의 특징

Read Committed는 매 쿼리 시점에 커밋된 값을 본다.

- 장점: 최신성이 좋다
- 단점: 같은 트랜잭션 안에서 읽을 때 결과가 바뀔 수 있다

즉 읽는 시점마다 현재에 맞춰진다.

### 2. Repeatable Read의 특징

Repeatable Read는 한 트랜잭션 안에서 같은 row를 다시 읽으면 같은 값을 보게 하려 한다.

- 장점: 반복 조회의 일관성이 좋다
- 단점: phantom 같은 범위 문제는 구현에 따라 더 복잡하다

즉 한 트랜잭션 안에서 시간의 흔들림이 줄어든다.

### 3. 어떤 이상 현상이 남는가

Read Committed에서는 Non-repeatable Read와 Phantom Read가 더 쉽게 나타난다.  
Repeatable Read에서는 row-level 재조회는 안정적이지만, 범위 불변식은 gap lock이나 별도 제약이 필요하다.

특히 MySQL InnoDB에서는 `REPEATABLE READ`의 locking range scan이 next-key/gap lock으로 overlap absence-check를 보조하던 경우가 있다.  
이 경로를 `READ COMMITTED`로 내리면 search/scan gap protection이 사라져, 같은 `SELECT ... FOR UPDATE`가 다시 phantom insert를 허용할 수 있다.

### 4. 비즈니스 불변식은 별도다

격리수준이 높아져도 다음은 자동으로 보장되지 않는다.

- 재고가 음수가 되지 않는가
- 당직 의사가 최소 1명 남는가
- 좌석이 중복 배정되지 않는가

이런 문제는 락, 제약조건, 원자적 업데이트가 같이 필요하다.

## 실전 시나리오

### 시나리오 1: Read Committed에서 목록이 바뀜

트랜잭션 동안 같은 목록 쿼리를 두 번 읽었더니 결과가 달라진다.  
이건 이상이 아니라 그 격리수준의 성질이다.

### 시나리오 2: Repeatable Read에서 조회는 같지만 불변식은 깨짐

같은 트랜잭션 안에서는 같은 row를 다시 읽어도 일관되지만, 다른 row를 조합한 규칙은 깨질 수 있다.

### 시나리오 3: 관리자 화면과 정산 배치의 요구가 다름

화면은 최신성이 중요하고, 정산은 반복 조회 일관성이 중요하다.  
같은 격리수준을 전부에 적용하면 오히려 비용만 커질 수 있다.

## 코드로 보기

```sql
-- Read Committed에서는 같은 트랜잭션에서도 결과가 바뀔 수 있다
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
START TRANSACTION;
SELECT status FROM orders WHERE id = 1;
SELECT status FROM orders WHERE id = 1;
COMMIT;
```

```sql
-- Repeatable Read에서는 같은 row 재조회가 더 안정적이다
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT status FROM orders WHERE id = 1;
SELECT status FROM orders WHERE id = 1;
COMMIT;
```

격리수준은 “무엇이 바뀌지 않게 느껴지는가”를 정하는 선택이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| Read Committed | 최신성이 좋다 | 재조회가 흔들린다 | 조회 중심 OLTP |
| Repeatable Read | 반복 조회가 안정적이다 | 범위 불변식은 별도 처리 필요 | 업무 배치/조회 일관성 |
| 더 강한 제약 + 낮은 격리 | 성능이 좋을 수 있다 | 모델링이 필요하다 | 불변식이 명확할 때 |
| Serializable | 가장 강하다 | 비용이 크다 | 정말 중요한 정합성 |

## 꼬리질문

> Q: Read Committed와 Repeatable Read의 핵심 차이는 무엇인가요?
> 의도: 각 격리수준의 관측 단위를 아는지 확인
> 핵심: RC는 쿼리마다 현재를 보고, RR은 트랜잭션 내 일관성을 더 지킨다

> Q: Repeatable Read면 phantom read가 완전히 사라지나요?
> 의도: 구현 차이와 범위 문제를 아는지 확인
> 핵심: 범위 불변식은 gap lock이나 제약조건이 추가로 필요할 수 있다

> Q: 격리수준만 높이면 비즈니스 버그가 다 해결되나요?
> 의도: 격리와 불변식의 차이를 아는지 확인
> 핵심: 아니다, 도메인 제약과 원자적 갱신이 같이 필요하다

## 한 줄 정리

Read Committed는 최신성을, Repeatable Read는 트랜잭션 내 일관성을 더 주지만, 둘 다 비즈니스 불변식을 자동으로 완성하지는 않는다.
