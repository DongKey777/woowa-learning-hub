---
schema_version: 3
title: FOR UPDATE 0건 뒤 중복 insert 원인 라우터
concept_id: database/for-update-zero-row-duplicate-insert-symptom-router
canonical: false
category: database
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/shopping-cart
- missions/lotto
- missions/roomescape
review_feedback_tags:
- empty-result-locking-misread
- unique-backstop-missing
- read-committed-precheck-assumption
aliases:
- for update zero row duplicate router
- empty result duplicate insert router
- 0건 for update 뒤 중복 저장
- 없으면 insert 했는데 둘 다 성공
- for update 넣었는데 둘 다 insert
- select for update 0건 경쟁 분기
symptoms:
- SELECT FOR UPDATE 를 넣었는데도 같은 key insert 가 둘 다 성공한다
- 없으면 insert 하려고 먼저 조회했는데 중복 row 가 생기거나 duplicate key 가 갑자기 늘었다
- MySQL 에서 READ COMMITTED 로 바꾼 뒤 exact-key pre-check 가 더 이상 안 막히는 것처럼 보인다
- FOR UPDATE 결과가 0건이면 그 자리가 예약된 줄 알았는데 동시 요청이 같이 insert 까지 간다
intents:
- symptom
- troubleshooting
prerequisites:
- database/lock-basics
- database/transaction-basics
next_docs:
- database/unique-vs-locking-read-duplicate-primer
- database/postgresql-serializable-retry-playbook
- database/read-committed-vs-repeatable-read-vs-serializable-decision-guide
- database/phantom-safe-booking-patterns-primer
linked_paths:
- contents/database/empty-result-locking-cheat-sheet-postgresql-mysql.md
- contents/database/exact-key-pre-check-decision-card.md
- contents/database/for-share-vs-for-update-duplicate-check-note.md
- contents/database/mysql-rc-duplicate-check-pitfall-note.md
- contents/database/postgresql-exact-key-precheck-contrast-card.md
- contents/database/unique-vs-locking-read-duplicate-primer.md
confusable_with:
- database/duplicate-key-then-not-found-symptom-router
- database/overlapping-bookings-both-succeed-symptom-router
- database/unique-vs-locking-read-duplicate-primer
forbidden_neighbors:
- contents/database/duplicate-key-then-not-found-symptom-router.md
- contents/database/overlapping-bookings-both-succeed-symptom-router.md
expected_queries:
- SELECT FOR UPDATE 결과가 0건인데 왜 같은 key insert 가 둘 다 성공해?
- 없으면 insert 패턴에서 pre-check 를 했는데도 duplicate 가 나는 원인을 어떻게 나눠?
- MySQL READ COMMITTED 로 바꾼 뒤 duplicate key 가 늘면 어디부터 봐야 해?
- exact key 조회 후 insert 했는데 0건이 잠금을 보장하지 않는 이유가 뭐야?
- FOR UPDATE 넣었는데 중복 저장이 생기면 unique 문제인지 격리수준 문제인지 어떻게 분기해?
contextual_chunk_prefix: |
  이 문서는 exact-key insert-if-absent 흐름에서 SELECT ... FOR UPDATE가 0건을
  반환했는데도 같은 key insert가 둘 다 진행되거나 duplicate key가 갑자기 늘어날 때,
  UNIQUE backstop 부재, empty-result locking 오해, MySQL READ COMMITTED 전환,
  overlap 문제를 exact-key 문제로 잘못 본 경우로 나눠 주는 symptom_router다.
  0건 for update 뒤 중복 저장, 없으면 insert가 샌다, RC로 내린 뒤 duplicate 증가,
  빈 결과가 예약된 줄 알았다 같은 자연어 표현이 이 문서의 분기와 연결된다.
---

# FOR UPDATE 0건 뒤 중복 insert 원인 라우터

## 한 줄 요약

> `SELECT ... FOR UPDATE`가 `0건`이었다는 사실만으로는 빈 자리가 예약되지 않는다. 보통은 `UNIQUE` backstop이 없었는지, empty-result locking을 과대평가했는지, MySQL `READ COMMITTED` 전환으로 앞단 queue가 사라졌는지, 사실은 overlap 문제를 exact-key 문제처럼 다룬 것인지부터 갈라야 한다.

## 가능한 원인

1. exact key를 닫는 `UNIQUE`나 PK가 없다. pre-check는 앞단 관찰일 뿐이고 마지막 승패는 write 시점 제약이 정하므로, 제약이 없으면 둘 다 `INSERT`에 성공할 수 있다. 이 경우 [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)로 가서 backstop을 먼저 고정한다.
2. `0건 FOR UPDATE`가 빈 자리를 잠갔다고 오해했다. existing row는 잠글 수 있어도 missing key나 absence 자체는 portable하게 예약되지 않으므로, exact-key든 overlap이든 `조회 -> 없으면 insert` 흐름은 그대로 경쟁한다. 이 분기는 [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)와 [FOR SHARE vs FOR UPDATE Duplicate Check Note](./for-share-vs-for-update-duplicate-check-note.md)로 이어진다.
3. MySQL에서 `REPEATABLE READ`가 만들어 주던 앞단 queue 체감이 `READ COMMITTED`에서 사라졌다. RR에서는 같은 key slot 주변이 잠깐 줄 서는 것처럼 보여도 RC에서는 더 많은 요청이 `INSERT`까지 같이 도착하므로 duplicate key가 더 자주 surface될 수 있다. 이 분기는 [MySQL RC Duplicate-Check Pitfall Note](./mysql-rc-duplicate-check-pitfall-note.md)와 [Read Committed vs Repeatable Read vs Serializable 결정 가이드](./read-committed-vs-repeatable-read-vs-serializable-decision-guide.md)로 이어진다.
4. 사실은 exact-key duplicate가 아니라 overlap이나 집합 규칙 문제다. 같은 시간대 예약, 활성 claim 총량, 범위 겹침 같은 문제를 `(없으면 insert)` exact-key처럼 풀면 `FOR UPDATE 0건` 착시가 반복된다. 이 경우 [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)와 [겹치는 예약 동시 성공 원인 라우터](./overlapping-bookings-both-succeed-symptom-router.md)로 이동해 arbitration surface를 다시 정한다.

## 빠른 자기 진단

1. 먼저 business truth가 exact key인지 적는다. `(coupon_id, member_id)`처럼 한 key 충돌이면 exact-key 분기고, 시간 범위나 합계 제한이면 exact-key 문서가 아니라 집합 규칙 문서로 가야 한다.
2. exact key라면 해당 컬럼 조합에 `UNIQUE` 또는 PK가 실제로 있는지 확인한다. 없다면 pre-check보다 제약 추가가 먼저다.
3. 제약이 있는데도 최근부터 duplicate key가 더 많이 보이면 격리수준과 엔진 변경을 본다. 특히 MySQL에서 RR에서 RC로 내렸다면 pre-check queue 체감이 줄었을 가능성이 크다.
4. 마지막으로 loser 신호가 무엇인지 본다. 진짜 duplicate row가 생겼는지, 아니면 `duplicate key`가 더 빨리 드러난 것인지, 혹은 `SELECT` 경로만 stale했는지를 나눠야 다음 처방이 맞는다.

## 다음 학습

- exact-key duplicate correctness를 어떤 수단이 책임지는지 먼저 고정하려면 [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)를 본다.
- `0건 FOR UPDATE`가 왜 빈 자리를 portable하게 예약하지 못하는지 엔진별로 비교하려면 [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)를 이어서 읽는다.
- PostgreSQL에서 absence 자체를 직렬화해야 하는 집합 규칙이라면 [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)로 가서 retry envelope를 확인한다.
- 문제의 본질이 overlap이나 예약 충돌이라면 [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)로 이동해 exact-key가 아닌 write-time arbitration 패턴을 선택한다.
