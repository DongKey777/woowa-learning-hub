---
schema_version: 3
title: Gap Lock과 Next-Key Lock
concept_id: database/gap-lock-next-key-lock
canonical: true
category: database
difficulty: advanced
doc_role: primer
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- gap-lock-next-key-lock
- innodb-phantom-prevention
- select-for-update-insert-blocked
aliases:
- gap lock
- next-key lock
- innodb gap locking
- phantom read prevention
- select for update insert blocked
- range lock
- insert intention wait
- record lock vs gap lock
- Gap Lock과 Next-Key Lock
- 범위 잠금
symptoms:
- SELECT FOR UPDATE를 걸었는데 없는 row나 범위 안 insert가 왜 막히는지 설명하지 못하고 있어
- MySQL REPEATABLE READ에서 phantom을 줄이려고 record뿐 아니라 gap까지 잠그는 이유가 헷갈려
- 같은 SQL이라도 index path에 따라 lock footprint가 달라지는 것을 놓치고 있어
intents:
- definition
- deep_dive
- troubleshooting
prerequisites:
- database/transaction-isolation-locking
- database/index-and-explain
next_docs:
- database/gap-lock-starvation-and-fairness
- database/mysql-empty-result-locking-reads
- database/mysql-explain-range-locking-primer
- database/mysql-repeatable-read-safe-range-checklist
linked_paths:
- contents/database/transaction-isolation-locking.md
- contents/database/index-and-explain.md
- contents/database/mysql-empty-result-locking-reads.md
- contents/database/gap-lock-starvation-and-fairness.md
- contents/database/phantom-safe-booking-patterns-primer.md
- contents/database/mysql-explain-range-locking-primer.md
- contents/database/mysql-repeatable-read-safe-range-checklist.md
confusable_with:
- database/mysql-empty-result-locking-reads
- database/gap-lock-starvation-and-fairness
- database/mysql-explain-range-locking-primer
forbidden_neighbors: []
expected_queries:
- MySQL InnoDB gap lock과 next-key lock은 record lock과 어떻게 달라?
- SELECT FOR UPDATE 범위 조회 뒤 다른 insert가 막히는 이유를 설명해줘
- Repeatable Read에서 phantom read를 줄이려고 gap까지 잠그는 원리는 뭐야?
- index path가 달라지면 next-key lock 범위도 달라지는 이유는 뭐야?
- gap lock, next-key lock, insert intention wait를 초보자에게 어떻게 연결해서 설명해?
contextual_chunk_prefix: |
  이 문서는 MySQL InnoDB의 gap lock, next-key lock, record lock, insert intention wait가 range locking과 phantom prevention에 어떻게 쓰이는지 설명하는 advanced primer다.
  gap lock, next-key lock, SELECT FOR UPDATE insert blocked, range lock 같은 자연어 질문이 본 문서에 매핑된다.
---
# Gap Lock과 Next-Key Lock

**난이도: 🔴 Advanced**

> 신입 백엔드 개발자가 InnoDB 동시성 제어를 설명할 때 필요한 핵심 정리

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [락의 기본 복습](#락의-기본-복습)
- [Gap Lock이란](#gap-lock이란)
- [Next-Key Lock이란](#next-key-lock이란)
- [어떤 상황에서 걸리는가](#어떤-상황에서-걸리는가)
- [SQL 예시](#sql-예시)
- [운영에서 확인할 것](#운영에서-확인할-것)
- [관련 문서](#관련-문서)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

retrieval-anchor-keywords: gap lock, next-key lock, phantom read prevention, select for update insert blocked, range lock, repeatable read locking, InnoDB gap locking, insert intention wait, record lock vs gap lock, locking range by index, overlap enforcement fallback, MySQL overlap locking

## 왜 중요한가

MySQL InnoDB에서는 단순히 row 하나만 잠그는 것처럼 보여도, 실제로는 **범위 사이의 공간(gap)** 까지 잠글 수 있다.

이걸 이해하지 못하면 다음 같은 현상을 설명하기 어렵다.

- `SELECT ... FOR UPDATE`를 걸었는데 왜 다른 insert가 막히는가
- 같은 조건 조회인데 왜 어떤 경우는 대기가 생기는가
- Repeatable Read에서 왜 phantom을 줄이려고 더 넓게 잠그는가

---

## 락의 기본 복습

락은 동시에 같은 데이터를 만질 때 충돌을 막기 위한 장치다.

기본적으로는 다음처럼 생각하면 된다.

- record lock: 특정 row 자체를 잠금
- gap lock: row와 row 사이의 빈 구간을 잠금
- next-key lock: record lock + gap lock의 조합

이 개념은 주로 InnoDB의 범위 잠금에서 중요하다.

---

## Gap Lock이란

Gap Lock은 **레코드와 레코드 사이의 빈 공간**을 잠그는 방식이다.

예를 들어 `id = 10`, `id = 20` 사이의 구간이 잠기면, 그 사이에 새 row가 들어오는 것을 막을 수 있다.

목적:

- 범위 조회 중에 새로운 row가 끼어드는 상황을 줄임
- phantom read를 완화하는 데 도움

주의점:

- 실제 row를 잠그는 것이 아니라 빈 구간을 잠그는 개념이라 직관적이지 않다
- 조건과 인덱스 사용 여부에 따라 잠금 범위가 달라질 수 있다

---

## Next-Key Lock이란

Next-Key Lock은 **특정 레코드와 그 앞 gap을 함께 잠그는 방식**이다.

쉽게 말해:

- row 하나만 잡는 것이 아니라
- 그 row가 속한 구간까지 같이 잠그는 것에 가깝다

이 방식은 Repeatable Read에서 phantom을 줄이기 위해 사용된다.

즉 범위 조회를 두 번 했을 때 중간에 새 row가 끼어들 가능성을 낮추려는 목적이 있다.

---

## 어떤 상황에서 걸리는가

대표적으로 아래 상황을 떠올리면 된다.

- `SELECT ... FOR UPDATE`
- 범위 조건을 가진 수정/조회
- 인덱스를 타는 조건에서의 정렬된 범위 잠금

중요한 점은 **인덱스를 어떻게 타느냐**에 따라 잠금 범위가 달라질 수 있다는 것이다.

예:

```sql
SELECT *
FROM orders
WHERE member_id = 10
  AND status = 'WAITING'
FOR UPDATE;
```

이 쿼리가 적절한 인덱스를 타면 필요한 범위만 잠글 수 있지만, 인덱스가 없거나 부적절하면 더 넓게 잠글 수 있다.

---

## SQL 예시

### 예시 1. 범위 조회가 insert를 막는 경우

```sql
START TRANSACTION;

SELECT *
FROM tickets
WHERE seat_no BETWEEN 10 AND 20
FOR UPDATE;
```

이 상태에서 다른 세션이 같은 범위 안에 새 row를 넣으려 하면 대기할 수 있다.

### 예시 2. 인덱스 유무에 따른 차이

```sql
CREATE INDEX idx_tickets_seat_no
ON tickets (seat_no);
```

인덱스가 있으면 잠금 범위가 비교적 명확해질 수 있다.  
반대로 적절한 인덱스가 없으면 스캔 범위가 커지면서 불필요하게 많은 구간이 잠길 수 있다.

### 예시 3. 동시 insert 시나리오

```sql
INSERT INTO tickets (seat_no, status)
VALUES (15, 'RESERVED');
```

다른 트랜잭션이 앞서 `seat_no BETWEEN 10 AND 20 FOR UPDATE`를 잡고 있으면 대기할 수 있다.

---

## 운영에서 확인할 것

실무에서는 다음을 함께 본다.

- 어떤 격리수준인지
- 해당 쿼리가 인덱스를 타는지
- `FOR UPDATE`가 정말 필요한지
- 락 대기가 길어지는지
- 데드락이 같이 발생하는지

특히 범위 잠금은 성능 문제로 이어질 수 있다.  
개별 row 충돌보다 더 넓은 구간이 막히면, 동시성이 급격히 떨어질 수 있다.

---

## 관련 문서

- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [Deadlock Case Study](./deadlock-case-study.md)

---

## 면접에서 자주 나오는 질문

### Q. Gap Lock은 왜 필요한가요?

- 범위 조회 중에 새로운 row가 끼어드는 상황을 줄이기 위해 필요하다.

### Q. Next-Key Lock은 무엇인가요?

- 특정 레코드와 그 앞 gap을 함께 잠그는 방식이다.

### Q. Gap Lock과 Row Lock의 차이는 무엇인가요?

- Row Lock은 특정 row 자체를 잠그고, Gap Lock은 row 사이의 빈 구간을 잠근다.

### Q. 왜 인덱스가 중요하나요?

- 인덱스를 어떻게 타느냐에 따라 잠금 범위가 달라져서, 불필요한 대기를 줄이는 데 큰 영향을 주기 때문이다.
