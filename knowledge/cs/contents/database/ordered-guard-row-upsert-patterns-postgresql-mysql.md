---
schema_version: 3
title: Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL
concept_id: database/ordered-guard-row-upsert-patterns-postgresql-mysql
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 93
mission_ids: []
review_feedback_tags:
- guard-row
- upsert-ordering
- deadlock
- postgresql-mysql
aliases:
- ordered guard row upsert
- ordered upsert plus lock
- pre-seeded guard row
- guard row creation race
- guard creation deadlock
- exact pk lock after upsert
- PostgreSQL on conflict guard row
- MySQL on duplicate key guard row
- canonical guard ordering
- guard row bootstrap
symptoms:
- guard row가 아직 없을 수 있는 sparse key space에서 생성 race와 multi-key deadlock을 줄여야 해
- PostgreSQL ON CONFLICT나 MySQL ON DUPLICATE KEY UPDATE를 lock 획득 shortcut으로 쓰다가 plan order drift와 deadlock이 생겨
- pre-seeded guard row와 ordered upsert plus lock 중 어떤 protocol이 hot path에 맞는지 결정해야 해
intents:
- design
- troubleshooting
prerequisites:
- database/guard-row-scope-design-multi-day-bookings
- database/upsert-contention-unique-index-locking
next_docs:
- database/shared-pool-guard-design-room-type-inventory
- database/deadlock-case-study
- database/transaction-retry-serialization-failure-patterns
linked_paths:
- contents/database/guard-row-scope-design-multi-day-bookings.md
- contents/database/shared-pool-guard-design-room-type-inventory.md
- contents/database/upsert-contention-unique-index-locking.md
- contents/database/engine-fallbacks-overlap-enforcement.md
- contents/database/mysql-empty-result-locking-reads.md
- contents/database/mysql-gap-lock-blind-spots-read-committed.md
- contents/database/deadlock-case-study.md
- contents/database/transaction-retry-serialization-failure-patterns.md
confusable_with:
- database/upsert-contention-unique-index-locking
- database/guard-row-scope-design-multi-day-bookings
- database/deadlock-case-study
forbidden_neighbors: []
expected_queries:
- guard row를 runtime에 만들 때 pre-seed와 ordered upsert plus lock 중 무엇이 안전해?
- PostgreSQL ON CONFLICT나 MySQL ON DUPLICATE KEY UPDATE로 guard row를 만들 때 deadlock을 줄이는 순서를 알려줘
- sparse guard key creation에서 existence phase와 lock phase를 분리해야 하는 이유가 뭐야?
- multi-key guard row를 canonical order로 잠그지 않으면 어떤 deadlock이 생겨?
- pre-seeded guard row가 hot path에서 missing row branch를 제거해 주는 장점을 설명해줘
contextual_chunk_prefix: |
  이 문서는 guard row가 없는 sparse key space에서 pre-seeded guard row와 ordered upsert-plus-lock protocol로 PostgreSQL/MySQL multi-key deadlock을 줄이는 advanced playbook이다.
  guard row creation race, ordered upsert plus lock, canonical guard ordering, exact PK lock after upsert 질문이 본 문서에 매핑된다.
---
# Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL

> 한 줄 요약: guard row를 미리 심어 두면 hot path는 "기존 row를 canonical order로 잠그는 문제"로 단순해지고, 런타임 생성이 필요하다면 `upsert`는 존재 보장 단계로만 보고 exact-PK lock을 같은 순서로 다시 잡아야 PostgreSQL/MySQL 모두에서 plan-order drift와 guard-creation deadlock을 줄일 수 있다.

**난이도: 🔴 Advanced**

관련 문서:

- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Shared-Pool Guard Design for Room-Type Inventory](./shared-pool-guard-design-room-type-inventory.md)
- [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [MySQL Empty-Result Locking Reads](./mysql-empty-result-locking-reads.md)
- [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md)
- [Deadlock Case Study](./deadlock-case-study.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)

retrieval-anchor-keywords: ordered guard row upsert, ordered upsert plus lock, pre-seeded guard row, guard row pre-seeding, guard row creation race, guard creation deadlock, guard row bootstrap, exact pk lock after upsert, PostgreSQL on conflict guard row, PostgreSQL on conflict deadlock, PostgreSQL deterministic upsert, MySQL on duplicate key guard row, MySQL duplicate key deadlock, insert select row order nondeterministic, plan order drift, canonical guard ordering, sparse guard key creation, room day guard preseed, guard row touch update, duplicate key shared lock deadlock

## 핵심 개념

guard row 패턴의 본질은 "대표 row를 하나 만든다"가 아니라, **경쟁하는 write path가 같은 guard key 집합을 같은 순서로 직렬화한다**는 계약이다.

문제는 guard row가 아직 없을 수 있다는 점이다.

- 이미 row가 있으면: 기존 row를 잠그는 문제다
- row가 없으면: **생성 자체가 lock protocol의 일부**가 된다
- 두 세션이 같은 key 집합을 다른 순서로 생성하면: business row를 건드리기 전에도 deadlock이 난다

그래서 먼저 분리해야 할 질문은 세 가지다.

1. key universe가 bounded 해서 미리 seed할 수 있는가
2. on-demand 생성이 필요하다면, 존재 보장과 실제 lock 획득을 어떻게 분리할 것인가
3. 엔진별 duplicate-key path가 어떤 잠금과 deadlock trap을 추가하는가

## 먼저 보는 결론

| 패턴 | hot path에서 하는 일 | 강한 점 | 주된 함정 | 잘 맞는 상황 |
|---|---|---|---|---|
| pre-seeded guard row | sorted key를 exact PK로 바로 lock | lock surface가 가장 예측 가능하다 | seed horizon, 빈 bucket lifecycle, 대량 seed 비용 | `room_id + day`, `room_type_id + day`처럼 key space가 bounded 한 경우 |
| ordered upsert-plus-lock | sorted key 순서로 missing row 생성 후, 같은 순서로 다시 lock | sparse / future-unbounded key도 다룰 수 있다 | set-based statement가 lock 순서를 숨기고, 생성 경합이 deadlock으로 바뀔 수 있다 | key가 드물게 생기거나 미래 horizon을 미리 다 못 심는 경우 |

핵심 차이는 단순히 "선행 작업이 있느냐"가 아니다.

- pre-seeded는 **missing-row branch를 hot path에서 제거**한다
- ordered upsert-plus-lock은 **creation race를 protocol 안으로 끌어들인다**

## 패턴 1. Pre-Seeded Guard Rows

pre-seeding은 guard row를 admission 시점이 아니라 별도 seed/extend job에서 미리 만들어 두는 방식이다.

예:

- 숙박 재고라면 `room_id + stay_day`를 앞으로 365일 선행 생성
- pooled inventory라면 `property_id + room_type_id + stay_day` 버킷을 horizon 단위로 선행 생성
- quota shard라면 tenant별 stripe row를 서비스 시작 시 한 번 생성

hot path는 단순하다.

1. 요청에서 guard key 집합을 계산한다
2. 중복 key를 제거한다
3. 전역 canonical order로 정렬한다
4. **기존 row만 exact PK search로 잠근다**
5. 잠근 상태에서 invariant를 재검사하고 detail row / counter / ledger를 갱신한다

이 패턴이 강한 이유:

- missing-row용 `INSERT` 분기가 없다
- MySQL에서는 unique index + unique search condition lock이 record 단위로 좁아지기 쉽다
- PostgreSQL/MySQL 모두에서 duplicate-key path를 hot path에서 피한다
- deadlock 분석이 "누가 어떤 기존 key를 어느 순서로 잡았나"로 단순해진다

대신 비용도 분명하다.

- seed horizon을 늘리는 배치가 필요하다
- sparse key space에서는 빈 row가 많아질 수 있다
- 너무 공격적으로 row를 삭제하면 결국 런타임 생성 race가 다시 들어온다

중요한 운영 규칙:

> pre-seeding을 택했다면 hot bucket row를 create/delete로 churn시키지 말고, row identity는 오래 유지하는 편이 낫다.

guard row를 "필요할 때 만들고 release 때 바로 삭제"하는 식으로 쓰면, 이름만 pre-seed일 뿐 실제로는 on-demand creation deadlock을 그대로 되살린다.

## 패턴 2. Ordered Upsert-Plus-Lock

key space가 sparse 하거나 future horizon을 미리 전부 seed하기 어렵다면 런타임 생성이 필요하다.

이때 안전한 기본 계약은 다음 두 단계다.

1. **existence phase**: missing guard row를 sorted order로 만든다
2. **lock phase**: 같은 sorted order로 exact PK lock을 다시 잡는다

즉 `upsert`를 "이 statement가 곧 lock 획득"이라고 생각하기보다, **존재 보장 단계**로 보는 쪽이 더 안전하다.

권장 프로토콜:

1. 요청에서 guard key 집합을 계산한다
2. 같은 요청 안의 중복 key를 제거한다
3. `(tenant_id, scope_kind, scope_id, bucket_start)` 같은 전역 규칙으로 정렬한다
4. 정렬된 순서대로 `upsert` 하여 row 존재를 보장한다
5. 정렬된 순서대로 exact PK `SELECT ... FOR UPDATE` 또는 엔진 동등 수단으로 다시 잠근다
6. 잠근 상태에서 overlap / capacity / active predicate를 재검사한다
7. detail row / counter / ledger를 갱신한다

왜 4와 5를 굳이 나누나?

- existence DML과 locking read는 엔진 내부 lock path가 다르다
- set-based `upsert`가 client가 기대한 순서 그대로 lock을 잡는다고 가정하기 어렵다
- explicit second lock phase가 있어야 "현재 어느 key까지 직렬화되었는지"를 설명하기 쉽다

최적화는 그 다음 문제다.  
먼저 계약을 단순하게 만든 뒤, 충분한 재현 테스트가 있을 때만 존재 보장과 lock 획득을 합치는 편이 낫다.

## 왜 single bulk statement가 함정이 되나

ordered protocol의 가장 흔한 실패는 "내가 key를 정렬했으니 statement도 그 순서로 잠근다"고 믿는 것이다.

### 1. SQL set DML은 client list order를 보장하지 않는다

`WHERE key IN (...)`, `INSERT ... SELECT`, multi-row `VALUES`는 모두 set-oriented 형태다.

- source row order가 plan에 따라 달라질 수 있다
- 같은 SQL이라도 optimizer가 다른 접근 경로를 고를 수 있다
- concurrent wait가 끼면 lock 획득 시점이 application이 기대한 순서와 벌어질 수 있다

즉 "key를 정렬해서 넘겼다"와 "DB가 그 순서로 lock을 잡았다"는 같은 말이 아니다.

### 2. PostgreSQL의 plan-order pitfall

PostgreSQL 문서는 `SELECT` 결과 순서를 `ORDER BY` 없이 보장하지 않는다고 본다.  
또 `FOR UPDATE`류 locking clause는 row를 **얻는 대로 잠근다**.

여기서 더 까다로운 점이 있다.

- `READ COMMITTED`에서 `ORDER BY`와 locking clause를 함께 쓰면
- 정렬 후 lock 대기에 들어갔다가
- 깨어난 뒤 ordering column 값이 바뀌어 결과가 "out of order"처럼 보일 수 있다고 문서가 경고한다

즉 PostgreSQL에서 multi-key lock ordering은

- 단순 `IN (...) FOR UPDATE`에도 기대기 어렵고
- `ORDER BY`만 붙여도 wait/recheck가 끼면 직관과 달라질 수 있다

그래서 가장 보수적인 기본값은 **정렬된 key를 one-key-at-a-time으로 처리하는 것**이다.

### 3. MySQL의 plan-order pitfall

MySQL 문서는 `INSERT ... SELECT`의 `SELECT`가 `ORDER BY` 없이는 nondeterministic order를 반환한다고 적는다.  
또 `INSERT ... SELECT ON DUPLICATE KEY UPDATE`는 source row order를 항상 보장할 수 없어서 statement-based replication에서 unsafe로 분류된다.

이 말이 guard creation에 주는 의미는 단순하다.

- `INSERT ... SELECT`로 guard row를 대량 생성하면서
- 그 source order를 lock ordering의 일부로 기대하면 안 된다

특히 overlap probe 결과나 temporary source table을 그대로 feeding 하는 방식은,  
select plan이 바뀌는 순간 deadlock surface도 같이 흔들린다.

### 4. 실무 권장선

ordered acquisition이 정말 중요하다면:

- 정렬된 key list를 애플리케이션 메모리나 temp table에 **ordinal과 함께 materialize**하고
- 그 ordinal 또는 full PK 순서대로 처리한다

특히 hot path에서는 batch SQL 한 방보다 **예측 가능한 row-at-a-time loop**가 더 안전한 경우가 많다.

## PostgreSQL에서 특히 조심할 점

### 1. `ON CONFLICT DO UPDATE`는 atomic하지만, statement 내부 중복 key는 허용하지 않는다

PostgreSQL 문서는 `INSERT ... ON CONFLICT DO UPDATE`를 deterministic statement로 설명한다.  
같은 statement가 **같은 기존 row를 두 번 affect 하면 안 된다**는 뜻이다.

guard key 집합 안에 같은 key가 두 번 들어오면:

- "나중에 같은 row를 또 touch하면 되겠지"가 아니라
- statement 자체가 cardinality violation으로 실패할 수 있다

따라서 ordered upsert 이전에 **request-local dedupe**가 필수다.

### 2. `DO UPDATE`는 나중에 update를 건너뛰어도 candidate row lock에는 참여한다

PostgreSQL 문서는 `ON CONFLICT DO UPDATE ... WHERE ...`에서  
실제 `UPDATE`가 일어나지 않아도 **candidate conflicting row는 lock 된다**고 설명한다.

즉 아래 같은 "조건부 no-op touch"는 가볍지 않다.

- `WHERE false`에 가까운 가드
- 실제 값 변경이 거의 없는 touch update
- lock만 얻고 싶어서 `DO UPDATE`를 남용하는 패턴

결론:

- PostgreSQL에서 `DO UPDATE`를 lock shortcut으로 쓰면 lock graph에 정식 참여한다
- 설계 설명력이 더 필요하면 `DO NOTHING`으로 existence만 보장하고, explicit `SELECT ... FOR UPDATE`로 lock phase를 분리하는 편이 낫다

### 3. guard creation deadlock은 여전히 "순서 문제"다

예를 들어 두 세션이 같은 key 두 개를 반대 순서로 확보한다고 하자.

- 세션 A: `k1 -> k2`
- 세션 B: `k2 -> k1`

둘 다 첫 key는 만들거나 잠그는 데 성공할 수 있다.  
그 뒤 두 번째 key에서 서로 상대의 row lock 해제를 기다리면, PostgreSQL도 일반적인 row-level deadlock으로 끝난다.

즉 PostgreSQL의 `ON CONFLICT`가 atomic하다고 해서 **multi-key ordering problem**이 사라지지는 않는다.

## MySQL에서 특히 조심할 점

### 1. pre-seeded row를 exact PK로 잠그는 이점이 특히 크다

MySQL InnoDB 문서는 unique index에 대한 unique search condition이면,  
locking read가 **record lock만** 잡고 앞 gap은 잠그지 않는다고 설명한다.

즉 pre-seeded guard row를 full PK로 찾는 패턴은:

- scan range가 좁고
- gap/next-key 부작용이 적고
- empty-result locking myth에 기대지 않아도 된다

MySQL에서 pre-seeding이 특히 매력적인 이유가 여기 있다.

### 2. plain `INSERT` + duplicate retry는 guard creation path에서 더 위험하다

MySQL 문서는 plain `INSERT`에서 duplicate-key error가 나면  
중복된 index record에 **shared lock**이 잡히고, 여러 세션이 같은 row를 두고 경합하면 이 shared lock 자체가 deadlock을 만들 수 있다고 설명한다.

즉 guard row 생성에서:

- `INSERT`
- duplicate면 예외 잡고 재시도

같은 패턴은 hot key에서 꽤 나쁜 기본값이다.

### 3. `ON DUPLICATE KEY UPDATE`는 duplicate path를 exclusive lock으로 바꾼다

같은 MySQL 문서는 `INSERT ... ON DUPLICATE KEY UPDATE`가  
duplicate row에 대해 shared lock이 아니라 **exclusive lock**을 잡는다고 설명한다.

그래서 MySQL에서 on-demand guard creation을 해야 한다면:

- plain `INSERT`/retry보다
- `ON DUPLICATE KEY UPDATE`가 duplicate path lock semantics 면에서 더 낫다

하지만 여기서 끝이 아니다.

- 세션마다 key 순서가 다르면 여전히 deadlock이 날 수 있고
- duplicate primary key와 duplicate unique key는 lock footprint가 다르며
- guard table에 여러 unique key가 있으면 arbitration surface가 흐려진다

그래서 MySQL guard table은 가능하면 **하나의 canonical PK/UNIQUE**만 중심으로 두는 편이 낫다.

### 4. `INSERT ... SELECT ON DUPLICATE KEY UPDATE`는 특히 피하는 편이 낫다

MySQL 문서가 source row order를 보장하지 못한다고 직접 말하는 조합이다.

guard acquisition 관점에서 이 조합의 문제:

- row existence 생성 순서를 select plan이 결정한다
- source order drift가 곧 deadlock surface drift가 된다
- statement-based replication safety 이슈까지 붙는다

즉 ordered guard creation이 필요할 때는,  
MySQL에서는 source `SELECT`가 아니라 **이미 정렬된 key feed**를 쓰는 편이 훨씬 예측 가능하다.

## 안전한 기본 프로토콜

### Pre-seeded protocol

```text
sorted_keys = unique(guard_keys(request)).sort()

for key in sorted_keys:
  SELECT ... FROM guard WHERE full_primary_key = :key FOR UPDATE

recheck_invariant_under_lock()
write_detail_rows_and_guard_side_effects()
```

특징:

- hot path에 create branch가 없다
- 정확한 PK lock만 사용한다
- deadlock 원인이 거의 전부 ordering bug로 환원된다

### Ordered upsert-plus-lock protocol

```text
sorted_keys = unique(guard_keys(request)).sort()

for key in sorted_keys:
  ensure_guard_exists(key)
  -- PostgreSQL: INSERT ... ON CONFLICT DO NOTHING
  -- MySQL:      INSERT ... ON DUPLICATE KEY UPDATE pk = pk

for key in sorted_keys:
  SELECT ... FROM guard WHERE full_primary_key = :key FOR UPDATE

recheck_invariant_under_lock()
write_detail_rows_and_guard_side_effects()
```

특징:

- 존재 보장과 lock 획득을 분리해 reasoning이 쉽다
- batch SQL보다 round trip은 늘 수 있다
- 대신 deadlock 분석과 engine portability가 좋아진다

## 언제 어떤 패턴을 고를까

| 질문 | pre-seeded 쪽이 유리 | ordered upsert-plus-lock 쪽이 유리 |
|---|---|---|
| key space가 bounded 한가 | 그렇다 | 아니다 |
| 미래 horizon을 배치로 확장할 수 있는가 | 그렇다 | 어렵다 |
| hot path latency와 predictability가 최우선인가 | 그렇다 | contention이 낮을 때만 |
| key가 드물게만 생기나 | 빈 row가 너무 많아질 수 있다 | 그렇다 |
| 엔진 차이를 최소화하고 싶은가 | 그렇다 | 가능하지만 protocol discipline이 더 필요 |

실무 기본값은 보통 이렇다.

- `room_id + day`, `room_type_id + day`처럼 버킷이 자연스럽고 horizon이 제한되면: **pre-seed**
- tenant-defined quota bucket, sparse tag guard처럼 key가 미리 다 안 보이면: **ordered upsert-plus-lock**

그리고 hot key 경합이 높아질수록:

- set-based bulk upsert보다
- canonical order를 설명 가능한 protocol이 더 중요해진다

## 자주 나오는 안티패턴

### "없으면 만들고 끝, lock은 다음 statement에서 알아서 맞겠지"

guard creation과 lock acquisition 사이가 protocol로 연결되지 않으면,  
missing-row race만 해결하고 multi-key ordering bug는 그대로 남는다.

### "`WHERE key IN (...) FOR UPDATE`에 key를 정렬해서 넣었으니 괜찮다"

application list order와 실제 lock order는 다를 수 있다.

### "MySQL은 duplicate면 예외 잡고 다시 시도하면 된다"

plain `INSERT` duplicate path의 shared lock deadlock trap을 과소평가한 것이다.

### "pre-seed는 비효율적이니 release 때 guard row를 바로 삭제하자"

delete/create churn은 creation race를 다시 들여온다.

## 한 줄 정리

guard row에서 진짜 중요한 것은 `upsert` 문법이 아니라 **같은 guard key 집합을 같은 순서로 존재 보장하고, 같은 순서로 다시 잠근 뒤, 그 아래에서만 invariant를 판정하는 것**이다.  
bounded key space면 pre-seeding이 가장 단순하고, on-demand 생성이 필요해도 ordered upsert-plus-lock을 두 단계 protocol로 유지해야 PostgreSQL/MySQL 모두에서 deadlock 설명력이 좋아진다.
