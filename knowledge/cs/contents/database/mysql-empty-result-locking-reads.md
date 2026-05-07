---
schema_version: 3
title: MySQL Empty-Result Locking Reads
concept_id: database/mysql-empty-result-locking-reads
canonical: true
category: database
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 92
mission_ids: []
review_feedback_tags:
- gap-lock
- locking-read
- empty-result
- predicate-lock-myth
aliases:
- mysql empty result locking read
- select for update zero rows
- select for share zero rows
- nonexistence lock myth
- zero row gap lock
- absence serialization mysql
- where clause is not predicate lock
- FOR UPDATE 0 row
- 없는 row를 잠그나요
- 결과가 없는데 락이 잡히나요
symptoms:
- SELECT FOR UPDATE나 FOR SHARE가 0 row를 돌려줬는데 없는 row 전체가 잠겼다고 해석하고 있어
- overlap predicate가 비었으니 논리적 부재가 보호된다고 믿고 insert race를 설계하고 있어
- READ COMMITTED 전환 뒤 empty-result locking read가 phantom insert를 막지 못해 중복이나 겹침이 생겨
intents:
- troubleshooting
- deep_dive
prerequisites:
- database/gap-lock-next-key-lock
- database/transaction-isolation-locking
next_docs:
- database/mysql-gap-lock-blind-spots-read-committed
- database/mysql-explain-range-locking-primer
- database/overlap-predicate-index-design-booking-tables
linked_paths:
- contents/database/gap-lock-next-key-lock.md
- contents/database/mysql-gap-lock-blind-spots-read-committed.md
- contents/database/read-committed-vs-repeatable-read-anomalies.md
- contents/database/overlap-predicate-index-design-booking-tables.md
- contents/database/write-skew-phantom-read-case-studies.md
- contents/database/range-invariant-enforcement-write-skew-phantom.md
- contents/database/transaction-boundary-isolation-locking-decision-framework.md
- contents/database/mysql-explain-range-locking-primer.md
confusable_with:
- database/gap-lock-next-key-lock
- database/mysql-gap-lock-blind-spots-read-committed
- database/range-invariant-enforcement-write-skew-phantom
forbidden_neighbors: []
expected_queries:
- MySQL에서 SELECT FOR UPDATE가 0 row면 없는 row 자체가 잠긴 거야?
- empty result locking read와 gap lock, next-key lock의 실제 보호 범위를 설명해줘
- READ COMMITTED에서 0 row FOR UPDATE가 phantom insert를 못 막는 이유가 뭐야?
- overlap check에서 WHERE 절 전체가 아니라 chosen index path가 잠기는 이유를 알려줘
- FOR SHARE와 FOR UPDATE가 empty result에서는 얼마나 다르게 동작해?
contextual_chunk_prefix: |
  이 문서는 MySQL SELECT FOR UPDATE, FOR SHARE가 0 row를 반환할 때 nonexistence 전체를 잠근다는 착각을 교정하는 advanced symptom router다.
  empty-result locking read, zero row gap lock, 없는 row를 잠그나요, WHERE predicate lock myth 질문이 본 문서에 매핑된다.
---
# MySQL Empty-Result Locking Reads

> 한 줄 요약: `SELECT ... FOR UPDATE`나 `FOR SHARE`가 `0 row`를 돌려줘도, MySQL이 잠그는 것은 보통 "WHERE 절의 부재"가 아니라 많아야 **스캔한 인덱스 gap/next-key**다. `READ COMMITTED`에서는 그 보호도 일반적으로 사라진다.

**난이도: 🔴 Advanced**

관련 문서:

- [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
- [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md)
- [Read Committed vs Repeatable Read Anomalies](./read-committed-vs-repeatable-read-anomalies.md)
- [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md)
- [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md)
- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)
- [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)

retrieval-anchor-keywords: mysql empty result locking read, select for update zero rows, select for share zero rows, mysql lock nonexistence, nonexistence lock myth, empty result gap lock, zero row gap lock, next-key successor lock, no rows for update insert race, no rows for share insert race, repeatable read gap lock, read committed no gap lock, overlap probe zero rows, absence serialization mysql, where clause is not predicate lock

## 핵심 개념

`FOR UPDATE`와 `FOR SHARE`가 `0 row`를 돌려줄 때 가장 먼저 버려야 하는 오해는 이것이다.

> "결과가 없으니, 이제 그 부재 자체가 잠겼다."

MySQL InnoDB가 실제로 기억하는 것은 보통 **논리식 자체**가 아니라 **스캔한 인덱스 경로**다.

- 찾은 row가 있으면 그 index record를 잠근다
- `REPEATABLE READ`/`SERIALIZABLE`에서 range scan이면 그 주변 gap/next-key도 잠글 수 있다
- `READ COMMITTED`에서는 search/scan gap lock이 일반적으로 꺼진다

즉 `0 row` 결과는 "아무것도 안 잠갔다"와 "부재 전체를 잠갔다" 사이 어딘가다.  
남는 보호가 있다면 그것은 **스캔한 B-tree 구간에 대한 insert 억제**이지, 추상적인 `WHERE predicate` 전체에 대한 predicate lock이 아니다.

## 0 rows일 때 실제로 남는 락 표면

| 락 계층 | `FOR SHARE` | `FOR UPDATE` | `0 row`일 때 실제 의미 |
|---|---|---|---|
| table intention lock | `IS` | `IX` | table-level lock과의 호환성 신호일 뿐이다. row 부재를 직렬화하지는 않는다 |
| matching record lock | shared record lock | exclusive record lock | 결과가 `0 row`면 잠글 실제 record가 없다 |
| scanned gap / next-key (`REPEATABLE READ`/`SERIALIZABLE`) | 가능 | 가능 | 스캔한 인덱스 interval에 대한 insert를 막을 수 있다 |
| scanned gap (`READ COMMITTED`) | 일반적으로 없음 | 일반적으로 없음 | `0 row`면 미래 insert에 대한 실질 보호가 거의 없다 |

핵심은 마지막 두 줄이다.  
empty-result locking read의 의미는 "없는 row를 잠근다"가 아니라, **스캔 도중 밟은 gap을 잠글 수도 있다**는 쪽에 가깝다.

## `FOR UPDATE`와 `FOR SHARE`는 empty-result에서 무엇이 다른가

찾은 row가 있을 때는 차이가 분명하다.

- `FOR UPDATE`: 이후 update/delete까지 염두에 둔 exclusive 성격
- `FOR SHARE`: 읽은 row가 바뀌지 않게 shared 성격으로 보호

하지만 결과가 비어 있고 보호가 gap/next-key 쪽으로만 남는 순간, 차이는 크게 줄어든다.

- gap lock은 insert 억제 용도다
- gap lock끼리는 shared/exclusive 구분을 business 의미로 기대하면 안 된다
- 그래서 `0 row` 상황에서 "`FOR UPDATE`니까 `FOR SHARE`보다 absence를 더 세게 잠갔다"고 해석하면 틀리기 쉽다

즉 empty-result에서 중요한 차이는 `UPDATE`냐 `SHARE`냐보다도,

1. 어떤 인덱스를 스캔했는지
2. 현재 isolation level이 무엇인지
3. 그 scan surface가 실제 conflict surface와 맞는지

에 더 크게 달려 있다.

## 왜 팀이 nonexistence locking을 과대평가하나

### 1. 문서의 "lock the nonexistence" 표현을 일반화한다

MySQL 문서는 next-key locking으로 **nonexistence를 잠글 수 있다**고 설명한다.  
이 말은 "어떤 `WHERE` 절이든 `0 row`를 보면 그 부재가 예약된다"는 뜻이 아니다.

문서가 가리키는 것은 더 좁다.

- ordered index를 따라 읽는다
- successor 쪽 next-key/gap이 잡힌다
- 그 same ordered key로 들어오는 insert를 막는다

즉 **인덱스된 중복 체크의 좁은 케이스**를 설명하는 문장이지, arbitrary predicate 전체를 predicate lock으로 올려준다는 보장이 아니다.

### 2. 팀은 `WHERE` 절을 잠금 계약으로 착각한다

애플리케이션은 보통 이렇게 생각한다.

```sql
SELECT id
FROM booking
WHERE room_id = :room_id
  AND status IN ('HELD', 'CONFIRMED')
  AND start_at < :requested_end
  AND end_at > :requested_start
FOR UPDATE;
```

결과가 `0 row`면 팀은 흔히 "`겹치는 예약이 없다`를 잠갔다"고 말한다.  
하지만 InnoDB가 잠그는 것은 **overlap predicate 전체**가 아니라 **실제로 탄 인덱스 scan path**다.

그래서 같은 논리 규칙이라도 다음에 따라 보호 범위가 달라진다.

- `(room_id, start_at)`를 탔는지
- `(room_id, end_at)`를 탔는지
- `status`가 index prefix에 있는지
- optimizer가 계획을 바꿨는지

잠금 계약을 `WHERE` 절로 읽으면 과대평가가 시작된다.

### 3. `REPEATABLE READ`에서 우연히 버틴 경험을 일반화한다

`REPEATABLE READ`에서는 next-key/gap lock이 있어서 특정 index range의 insert가 실제로 막힐 수 있다.  
그래서 테스트에서는 absence-check가 "되는 것처럼" 보인다.

하지만 그건 보통 아래가 우연히 맞아떨어진 결과다.

- 적절한 인덱스를 탔다
- 모든 writer가 같은 probe를 먼저 실행했다
- active predicate가 경로마다 같았다

이 경험을 "MySQL은 `0 row FOR UPDATE`로 nonexistence를 잠근다"로 일반화하면, `READ COMMITTED` 전환이나 plan drift 때 바로 깨진다.

### 4. `FOR UPDATE`를 predicate lock처럼 상상한다

`FOR UPDATE`라는 이름 때문에 팀은 "강한 잠금"을 상상한다.  
하지만 empty-result에서는 강도가 아니라 **surface 정렬**이 더 중요하다.

- row가 없으면 row lock 강도는 의미가 줄어든다
- 남는 것이 gap/next-key라면, 그건 "이 인덱스 구간 insert 금지"에 가깝다
- 논리 규칙 전체를 막는 predicate lock은 아니다

## 실전 시나리오

### 시나리오 1. exact duplicate check는 좁게만 해석한다

```sql
SELECT 1
FROM user_email
WHERE email = :email
FOR SHARE;
-- 0 row
```

이 패턴을 narrow uniqueness check로 쓰는 경우가 있다.  
여기서 기대할 수 있는 최대치는 "같은 ordered key로 들어오는 duplicate insert를 successor gap이 막아 줄 수 있다" 정도다.

하지만 이것도 과대해석하면 안 된다.

- `READ COMMITTED`에서는 search gap lock을 기대하면 안 된다
- exact unique-key duplicate 방지의 진짜 backstop은 locking read가 아니라 `UNIQUE(email)`이다
- 이 패턴을 overlap, active predicate, 부분 집합 부재 체크로 일반화하면 안 된다

즉 이 경우에도 "부재 전체를 잠갔다"가 아니라 **같은 key duplicate를 좁게 보조했다**로 읽어야 한다.

### 시나리오 2. overlap query는 logical absence lock이 아니다

```sql
SELECT id
FROM booking
WHERE room_id = :room_id
  AND status IN ('HELD', 'CONFIRMED')
  AND start_at < :requested_end
  AND end_at > :requested_start
FOR UPDATE;
-- 0 row
```

여기서 `0 row`가 의미하는 것은 "겹치는 booking predicate 전체를 봉인했다"가 아니다.

가능한 실제 보호:

- 선택된 index scan path가 지나간 gap으로의 insert 억제
- 그 path 위의 특정 prefix에 대한 serialization 보조

보호하지 못할 수 있는 것:

- 다른 scan 축에서 들어오는 logical overlap
- 기존 row의 status 변경으로 active set 안으로 들어오는 경우
- mixed write path가 probe 없이 바로 insert/update하는 경우
- `READ COMMITTED`에서의 phantom insert

그래서 overlap invariant는 base table empty-result locking read 하나로 닫힌다고 보면 안 된다.

### 시나리오 3. `READ COMMITTED` 전환 후 갑자기 중복이 생긴다

RR에서 오래 버티던 코드가 RC에서 깨지는 이유는 자주 이것이다.

1. `SELECT ... FOR UPDATE`가 `0 row`를 본다
2. 팀은 "이제 부재가 잠겼다"고 믿는다
3. RC에서는 search gap lock이 일반적으로 없어서 다른 세션 insert가 통과한다
4. 두 트랜잭션이 모두 성공한다

즉 RC는 "없음"을 더 이상 직렬화해 주지 않는다.  
이때 드러나는 것은 isolation이 약해졌다는 사실뿐 아니라, 원래 설계가 **storage-path 우연성**에 기대고 있었다는 점이다.

## 실무 판단 기준

다음처럼 읽으면 실수를 줄일 수 있다.

| 질문 | 안전한 해석 |
|---|---|
| `0 row FOR UPDATE/FOR SHARE`면 missing row가 잠겼나 | 아니다. 많아야 scanned gap/next-key가 남는다 |
| `FOR UPDATE`가 `FOR SHARE`보다 nonexistence를 더 세게 막나 | empty-result gap-only 상황에서는 그 차이를 크게 기대하면 안 된다 |
| `WHERE` 절 전체가 보호되나 | 아니다. 실제 보호 단위는 chosen index path다 |
| RC에서도 같은 의미인가 | 아니다. search/scan gap protection이 일반적으로 사라진다 |

설계 쪽 기본 원칙은 이렇다.

- exact duplicate는 `UNIQUE` 제약으로 닫는다
- discrete overlap은 slot row + unique로 번역한다
- continuous overlap/capacity는 guard row나 ledger로 arbitration surface를 만든다
- `0 row` locking read는 predicate-safe invariant의 1차 수단이 아니라, 좁은 scan-surface 보조 수단으로만 본다

## 확인할 때 무엇을 봐야 하나

empty-result locking read가 실제로 무엇을 잠갔는지 헷갈리면, SQL 텍스트가 아니라 **실제 lock footprint**를 봐야 한다.

- `EXPLAIN`으로 어떤 index path를 탔는지 확인
- `READ COMMITTED`인지 `REPEATABLE READ`인지 확인
- `performance_schema.data_locks`나 lock wait로 gap/next-key가 실제로 생겼는지 확인
- 다른 writer path가 같은 arbitration surface를 통과하는지 확인

특히 `0 row` 결과만 보고 "absence locked"라고 서술하는 것은 가장 위험한 요약이다.

## 한 줄 정리

MySQL에서 `SELECT ... FOR UPDATE`나 `FOR SHARE`가 `0 row`를 돌려줄 때 남는 보호는 보통 **스캔한 인덱스 gap/next-key**일 뿐이며, 그마저도 `READ COMMITTED`에서는 일반적으로 사라진다.  
팀이 과대평가하는 지점은 "부재 전체"를 잠근다고 믿는 순간이다.
