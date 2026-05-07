---
schema_version: 3
title: Read-Before-Write Race Timeline Across MySQL and PostgreSQL
concept_id: database/read-before-write-race
canonical: true
category: database
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 91
mission_ids: []
review_feedback_tags:
- duplicate-check
- check-then-insert
- unique-constraint
- upsert
- mysql-postgresql
aliases:
- read before write race
- check then insert race
- select then insert race
- duplicate check race
- mysql vs postgresql duplicate race
- 조회 후 insert 경쟁
- 없으면 insert 패턴
- 먼저 select 하고 insert
- unique constraint loser
- upsert conflict branch
symptoms:
- SELECT로 먼저 없음을 확인했는데 동시에 INSERT가 들어오면 중복이나 duplicate key가 발생하는 이유를 설명해야 해
- MySQL READ COMMITTED와 REPEATABLE READ에서 check-then-insert 동작 차이를 비교해야 해
- PostgreSQL empty-result locking read가 부재를 예약하는지 헷갈려 해
intents:
- definition
- comparison
- troubleshooting
prerequisites:
- database/transaction-isolation-locking
- database/primary-foreign-key-basics
next_docs:
- database/unique-vs-locking-read-duplicate-primer
- database/upsert-contention-unique-index-locking
- database/mysql-rc-duplicate-check-pitfall-note
- database/postgresql-vs-mysql-isolation-cheat-sheet
linked_paths:
- contents/database/unique-vs-locking-read-duplicate-primer.md
- contents/database/postgresql-vs-mysql-isolation-cheat-sheet.md
- contents/database/empty-result-locking-cheat-sheet-postgresql-mysql.md
- contents/database/mysql-rc-duplicate-check-pitfall-note.md
- contents/database/mysql-rr-exact-key-probe-visual-guide.md
- contents/database/upsert-contention-unique-index-locking.md
- contents/database/insert-if-absent-retry-outcome-guide.md
confusable_with:
- database/unique-vs-locking-read-duplicate-primer
- database/empty-result-locking-cheat-sheet-postgresql-mysql
- database/insert-if-absent-retry-outcome-guide
forbidden_neighbors: []
expected_queries:
- SELECT로 먼저 조회하고 없으면 INSERT하는 코드가 왜 race condition을 만들 수 있어?
- MySQL과 PostgreSQL에서 check then insert duplicate race 타임라인을 비교해줘
- READ COMMITTED와 REPEATABLE READ에서 없으면 insert 패턴이 어떻게 다르게 보이나?
- empty result FOR UPDATE가 absence lock을 잡는다고 생각하면 왜 위험해?
- UNIQUE constraint와 upsert가 read-before-write race의 최종 판정을 맡는다는 뜻이 뭐야?
contextual_chunk_prefix: |
  이 문서는 SELECT 후 INSERT, check-then-insert, read-before-write race를 MySQL과 PostgreSQL 격리수준별 타임라인으로 설명하는 beginner bridge다.
  duplicate key, unique violation, upsert conflict branch, empty-result locking read 질문이 본 문서에 매핑된다.
---
# Read-Before-Write Race Timeline Across MySQL and PostgreSQL

> 한 줄 요약: `SELECT`로 먼저 확인하고 `INSERT`하는 경로는 MySQL과 PostgreSQL 모두에서 race window가 남고, RC/RR 차이는 "앞단 queue가 얼마나 생기느냐"에 더 가깝다. 최종 승자는 `UNIQUE`나 upsert가 write 시점에 정한다.

**난이도: 🟢 Beginner**

관련 문서:

- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [PostgreSQL vs MySQL Isolation Cheat Sheet](./postgresql-vs-mysql-isolation-cheat-sheet.md)
- [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)
- [MySQL RC Duplicate-Check Pitfall Note](./mysql-rc-duplicate-check-pitfall-note.md)
- [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: read before write race, check then insert race, select then insert race, mysql vs postgresql duplicate race, mysql rc rr duplicate race, postgres rc rr duplicate race, unique vs upsert outcome, on conflict do nothing timeline, on duplicate key update timeline, check-before-insert primer, beginner duplicate race timeline, read-before-write race timeline, 없으면 insert race, 조회 후 insert 경쟁, read before write race timeline mysql postgresql basics

## 먼저 잡을 멘탈모델

초보자는 이 문제를 "빈 의자를 보고 앉으려는 두 사람"으로 보면 쉽다.

1. 둘 다 먼저 의자가 비어 있는지 본다.
2. 둘 다 "비었다"고 볼 수 있다.
3. 둘 다 앉으러 달린다.
4. 마지막에 누가 실제로 앉았는지는 **의자 자체의 규칙**이 정한다.

DB로 옮기면 대응은 이렇다.

- 먼저 보는 행동: `SELECT`
- 실제로 앉는 행동: `INSERT`
- 의자 자체의 규칙: `UNIQUE` 또는 upsert가 타는 unique index

핵심 기억법:

> check-then-insert의 위험은 "읽을 때 비어 보였다"와 "쓸 때도 비어 있다"가 같은 뜻이 아니라는 점이다.

## 30초 결론표

| 질문 | 짧은 답 |
|---|---|
| MySQL RC에서 `SELECT` 후 `INSERT`는 안전한가 | 아니오. 둘 다 `0 row`를 보고 `INSERT`까지 갈 수 있다 |
| MySQL RR에서 좀 더 안전해 보이는 이유는 | exact-key probe에서 같은 key slot 주변 queue가 잠깐 생길 수 있어서다 |
| PostgreSQL RC/RR에서 `0 row FOR UPDATE`가 부재를 예약하나 | 보통 아니다. `0 row`면 잠근 row도 없다 |
| 최종적으로 중복을 막는 것은 무엇인가 | `UNIQUE` 또는 upsert가 사용하는 unique index |
| upsert를 쓰면 check-then-insert race가 줄어드나 | 그렇다. 읽기-쓰기 사이 분기 대신 write 시점 arbitration으로 모은다 |

## 한눈에 비교

| 엔진 / 격리수준 | check-then-insert 앞단에서 보이는 모습 | `UNIQUE`가 있으면 loser가 주로 보는 것 | upsert를 쓰면 loser가 주로 보는 것 |
|---|---|---|---|
| PostgreSQL `READ COMMITTED` | `0 row` locking read가 부재를 예약하지 못해 둘 다 `INSERT`까지 갈 수 있다 | unique violation (`23505`) | `DO NOTHING`이면 조용히 skip, `DO UPDATE`면 conflict branch로 update |
| PostgreSQL `REPEATABLE READ` | snapshot은 고정되지만 empty-result lock은 아니다. 둘 다 "없다"를 보고 달릴 수 있다 | unique violation (`23505`) | RC와 비슷하게 conflict branch로 모인다 |
| MySQL `READ COMMITTED` | search gap queue를 기대하기 어려워 둘 다 `INSERT`까지 가기 쉽다 | duplicate key (`1062`) | `ON DUPLICATE KEY UPDATE` update path로 모이거나 대기 후 update |
| MySQL `REPEATABLE READ` | exact-key + matching index path면 잠깐 queue가 생길 수 있지만 보너스에 가깝다 | duplicate key (`1062`) 또는 pre-probe/insert 대기 뒤 duplicate | update path로 모이거나 대기 후 update |

이 표를 읽는 포인트는 두 가지다.

- RC/RR 차이는 주로 **pre-read가 얼마나 queue를 만들어 주는가**에서 드러난다.
- `UNIQUE`와 upsert 차이는 주로 **loser가 어떤 결과를 받는가**에서 드러난다.

## 왜 race가 생기나

가장 흔한 코드는 이런 모양이다.

```sql
SELECT 1
FROM coupon_issue
WHERE coupon_id = :coupon_id
  AND member_id = :member_id;

INSERT INTO coupon_issue(coupon_id, member_id)
VALUES (:coupon_id, :member_id);
```

또는 locking read를 붙여도 본질은 비슷하다.

```sql
SELECT 1
FROM coupon_issue
WHERE coupon_id = :coupon_id
  AND member_id = :member_id
FOR UPDATE;
```

문제는 `SELECT`와 `INSERT`가 **같은 순간**이 아니라는 점이다.
사이에 다른 트랜잭션이 같은 key를 먼저 넣으면, 먼저 읽은 결과는 바로 낡을 수 있다.

## 공통 타임라인: `UNIQUE`가 없으면 왜 위험한가

| 시점 | 트랜잭션 A | 트랜잭션 B |
|---|---|---|
| t1 | `SELECT` -> `0 row` |  |
| t2 |  | `SELECT` -> `0 row` |
| t3 | `INSERT` |  |
| t4 |  | `INSERT` |
| t5 | 둘 다 성공 가능 | 둘 다 성공 가능 |

그래서 "먼저 확인했으니 괜찮다"는 말은 제약이 없으면 틀릴 수 있다.

## 공통 타임라인: `UNIQUE`가 있으면 누가 지나

```sql
ALTER TABLE coupon_issue
ADD CONSTRAINT uq_coupon_issue_coupon_member
UNIQUE (coupon_id, member_id);
```

| 시점 | 트랜잭션 A | 트랜잭션 B |
|---|---|---|
| t1 | `SELECT` -> `0 row` |  |
| t2 |  | `SELECT` -> `0 row` |
| t3 | `INSERT` 성공 |  |
| t4 |  | 같은 key `INSERT` 시도 |
| t5 | commit | duplicate / unique violation 또는 conflict branch |

핵심:

- 둘 다 읽기에서는 이길 수 있다
- write에서는 둘 다 이길 수 없다
- 이 마지막 판정은 `UNIQUE`가 한다

## 엔진별 타임라인

### 1. PostgreSQL `READ COMMITTED`

초보자용으로 가장 보수적으로 읽으면 이렇다.

- `SELECT`는 statement snapshot을 본다
- `SELECT ... FOR UPDATE`가 `0 row`면 잠근 row가 없다
- 그래서 absence check를 예약했다고 읽으면 안 된다

타임라인:

| 시점 | A | B |
|---|---|---|
| t1 | `SELECT ... FOR UPDATE` -> `0 row` |  |
| t2 |  | `SELECT ... FOR UPDATE` -> `0 row` |
| t3 | `INSERT` 성공 |  |
| t4 |  | `INSERT` -> `23505` 또는 `ON CONFLICT` branch |

기억할 점:

- PostgreSQL RC에서 read-before-write race는 매우 "정직하게" 드러난다
- empty-result locking read가 부재를 잠갔다고 기대하지 않는다

### 2. PostgreSQL `REPEATABLE READ`

헷갈리기 쉬운 지점은 snapshot이 고정된다는 사실이다.
하지만 snapshot 고정과 "없는 row 예약"은 같은 말이 아니다.

타임라인:

| 시점 | A | B |
|---|---|---|
| t1 | tx 시작, `SELECT` -> `0 row` |  |
| t2 |  | tx 시작, `SELECT` -> `0 row` |
| t3 | `INSERT` 성공 |  |
| t4 | commit |  |
| t5 |  | 같은 key `INSERT` -> `23505` 또는 `ON CONFLICT` branch |

기억할 점:

- RR이라도 "둘 다 없다고 읽는" 장면은 가능하다
- RR이 plain read를 안정적으로 보이게 해도, check-then-insert race를 없애 주는 것은 아니다

### 3. MySQL `READ COMMITTED`

초보자 기준 핵심은 한 줄이다.

> RC에서는 exact-key pre-check가 same-key insert를 앞에서 잘 줄 세워 줄 것이라고 기대하면 안 된다.

타임라인:

| 시점 | A | B |
|---|---|---|
| t1 | `SELECT ... FOR UPDATE` -> `0 row` |  |
| t2 |  | `SELECT ... FOR UPDATE` -> `0 row` |
| t3 | `INSERT` 성공 |  |
| t4 |  | `INSERT` -> `1062` 또는 `ON DUPLICATE KEY UPDATE` path |

운영에서 보이는 것:

- RC 전환 뒤 duplicate key 로그가 늘 수 있다
- 이것은 종종 `UNIQUE`가 약해진 것이 아니라, 앞단 queue가 줄어든 결과다

### 4. MySQL `REPEATABLE READ`

이 레벨은 초보자가 가장 오해하기 쉽다.

## 엔진별 타임라인 (계속 2)

- exact-key
- full unique key equality
- matching index path

이 세 가지가 맞으면 same-key insert가 잠깐 기다리는 장면이 나올 수 있다.

타임라인:

| 시점 | A | B |
|---|---|---|
| t1 | `SELECT ... FOR UPDATE` exact-key probe |  |
| t2 | 같은 key slot 주변 queue 형성 가능 |  |
| t3 | `INSERT` 성공 | B가 pre-probe 또는 insert에서 대기 가능 |
| t4 | commit | B가 duplicate 또는 upsert update path로 진행 |

하지만 이 장면을 계약으로 외우면 위험하다.

- RC로 내리면 흔들린다
- 함수/정렬/인덱스 경로가 바뀌면 흔들린다
- 다른 writer가 probe 없이 바로 `INSERT`하면 read-before-write 가정이 흔들린다

즉 MySQL RR은 "앞단 안내선"이 될 수는 있어도, 최종 안전성의 주인공은 아니다.

## `UNIQUE`와 upsert의 차이

### `UNIQUE` + plain `INSERT`

각 엔진의 전형적인 write path:

```sql
INSERT INTO coupon_issue(coupon_id, member_id)
VALUES (?, ?);
```

loser가 주로 받는 결과:

| 엔진 | 대표 결과 |
|---|---|
| PostgreSQL | `23505` unique violation |
| MySQL | `1062` duplicate key |

초보자 해석:

- winner는 row를 만들었다
- loser는 "이미 있음"을 예외로 받는다

### upsert

PostgreSQL:

```sql
INSERT INTO coupon_issue(coupon_id, member_id)
VALUES (?, ?)
ON CONFLICT (coupon_id, member_id) DO NOTHING;
```

MySQL:

```sql
INSERT INTO coupon_issue(coupon_id, member_id)
VALUES (?, ?)
ON DUPLICATE KEY UPDATE member_id = VALUES(member_id);
```

upsert에서 달라지는 점:

- loser가 항상 duplicate 예외를 바깥으로 보지 않을 수 있다
- conflict를 statement 안에서 흡수한다
- 하지만 arbitration 자체는 여전히 unique index가 한다

## upsert outcome 비교

| write 방식 | PostgreSQL에서 loser가 보통 받는 것 | MySQL에서 loser가 보통 받는 것 | 초보자 해석 |
|---|---|---|---|
| plain `INSERT` + `UNIQUE` | `23505` | `1062` | "이미 승자가 있다" |
| `ON CONFLICT DO NOTHING` | 0 row inserted | 해당 없음 | "졌지만 조용히 물러남" |
| `ON CONFLICT DO UPDATE` | update path | 해당 없음 | "졌지만 winner row에 합류해 update" |
| `ON DUPLICATE KEY UPDATE` | 해당 없음 | update path | "졌지만 duplicate를 statement 안에서 흡수" |

핵심:

- `UNIQUE` only: loser signal이 예외로 바깥에 잘 보인다
- upsert: loser signal이 SQL 안으로 들어가 결과가 더 단순해질 수 있다
- 둘 다 승자 판정 surface는 unique index다

## 흔한 오해

- "`REPEATABLE READ`면 check-then-insert가 안전하다"
  - 아니다. MySQL RR은 일부 exact-key path에서 덜 터져 보일 뿐이고, PostgreSQL RR도 absence reservation이 아니다.
- "`SELECT ... FOR UPDATE`를 붙였으니 없는 row도 잠겼다"
  - PostgreSQL에서는 보통 틀리고, MySQL도 엔진/인덱스 경로 의존성이 크다.
- "upsert면 race가 아예 사라진다"
  - read-before-write race는 줄지만, hot key lock 경합과 update path 비용은 남는다.
- "RC에서 duplicate가 늘면 DB가 더 unsafe해졌다"
  - 제약은 그대로일 수 있다. 단지 duplicate 경쟁이 더 눈에 보이게 surface됐을 수 있다.

## 언제 무엇을 고르면 되나

| 상황 | beginner-safe 기본 선택 |
|---|---|
| exact duplicate를 막고 싶다 | `UNIQUE` 먼저 |
| duplicate 예외를 매번 애플리케이션에서 분기하기 싫다 | upsert 검토 |
| MySQL RR pre-probe가 잘 먹는 것 같아 보인다 | 보조 최적화로만 보고 계약은 `UNIQUE`에 둔다 |
| PostgreSQL에서 "없음"까지 더 강하게 직렬화하고 싶다 | RR이 아니라 별도 invariant surface나 `SERIALIZABLE` + retry를 검토 |

## 꼬리질문

> Q. 왜 MySQL RR에서는 check-then-insert가 덜 새는 것처럼 보이나요?
> 의도: same-key slot queue와 hard correctness를 분리하는지 확인
> 핵심: exact-key probe가 같은 index slot 주변 queue를 잠깐 만들 수 있지만, 그것은 보조 효과이고 최종 판정은 `UNIQUE`가 한다.

> Q. PostgreSQL RR도 snapshot이 고정되는데 왜 race가 남나요?
> 의도: snapshot stability와 absence reservation을 구분하는지 확인
> 핵심: 같은 snapshot을 본다고 해서 "없는 row" 자체를 잠그는 것은 아니기 때문이다.

> Q. upsert를 쓰면 어떤 점이 달라지나요?
> 의도: duplicate 예외 노출과 write-time arbitration 차이를 아는지 확인
> 핵심: read-before-write 분기를 줄이고 loser를 SQL statement 안에서 흡수할 수 있지만, unique index arbitration 자체는 그대로다.

## 한 줄 정리

MySQL과 PostgreSQL 모두에서 check-then-insert race의 본질은 "`읽을 때 비어 보였음` != `쓸 때도 비어 있음`"이고, RC/RR 차이는 앞단 queue 체감의 차이에 가깝다. 최종 승자와 loser outcome은 `UNIQUE`와 upsert가 write 시점에 정한다.
