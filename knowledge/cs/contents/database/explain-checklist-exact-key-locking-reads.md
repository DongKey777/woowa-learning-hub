---
schema_version: 3
title: EXPLAIN Checklist for Exact-Key Locking Reads
concept_id: database/explain-checklist-exact-key-locking-reads
canonical: true
category: database
difficulty: beginner
doc_role: playbook
level: beginner
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- exact-key-locking-read-explain
- duplicate-precheck-plan-verification
- unique-key-path-drift
aliases:
- explain checklist exact key locking read
- explain duplicate precheck
- exact key explain beginner
- full unique key equality path
- for update unique index explain
- duplicate pre-check explain
- locking read explain checklist
- exact-key locking read 체크리스트
symptoms:
- SELECT FOR UPDATE를 썼다는 사실만 보고 exact-key lock이라고 가정하고 있어
- duplicate pre-check SQL이 실제로 unique key full equality path를 타는지 확인하지 않았어
- ORM 리팩터링 뒤 lock clause는 남았지만 EXPLAIN key와 rows가 달라진 것을 놓치고 있어
intents:
- troubleshooting
- design
prerequisites:
- database/unique-vs-locking-read-duplicate-primer
- database/index-and-explain
next_docs:
- database/hibernate-sql-log-explain-lock-verification-primer
- database/mysql-rr-exact-key-probe-visual-guide
- database/mysql-explain-range-locking-primer
- database/spring-jpa-exact-key-lock-mapping
linked_paths:
- contents/database/hibernate-sql-log-explain-lock-verification-primer.md
- contents/database/unique-vs-locking-read-duplicate-primer.md
- contents/database/mysql-rr-exact-key-probe-visual-guide.md
- contents/database/mysql-explain-range-locking-primer.md
- contents/database/mysql-rr-exact-key-probe-assumptions-checklist.md
- contents/database/spring-jpa-exact-key-lock-mapping-guide.md
- contents/database/mysql-repeatable-read-safe-range-checklist.md
- contents/database/statistics-histograms-cardinality-estimation.md
- contents/database/index-and-explain.md
confusable_with:
- database/unique-vs-locking-read-duplicate-primer
- database/mysql-explain-range-locking-primer
- database/mysql-rr-exact-key-probe-assumptions-checklist
forbidden_neighbors: []
expected_queries:
- SELECT FOR UPDATE duplicate pre-check가 exact-key unique index를 타는지 EXPLAIN으로 어떻게 확인해?
- 중복 검사 locking read에서 key, type, rows가 어떤 모양이어야 안전해?
- full composite unique key equality path가 깨지면 어떤 EXPLAIN 신호가 보여?
- JPA 쿼리 변경 후 locking read plan drift를 어떻게 점검해?
- FOR SHARE나 FOR UPDATE를 썼는데도 exact-key lock이라고 바로 믿으면 안 되는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 duplicate pre-check locking read가 실제로 intended unique-key full equality path를 타는지 EXPLAIN으로 확인하는 beginner playbook이다.
  exact key locking read, duplicate precheck explain, FOR UPDATE unique index, key type rows checklist 같은 자연어 증상 질문이 본 문서에 매핑된다.
---
# EXPLAIN Checklist for Exact-Key Locking Reads

> 한 줄 요약: exact-key duplicate pre-check를 믿기 전에 `EXPLAIN`으로 정말 **full unique-key equality path**를 타는지 먼저 확인하는 beginner checklist다.

**난이도: 🟢 Beginner**

관련 문서:

- [Hibernate SQL Log + EXPLAIN Lock Verification Primer](./hibernate-sql-log-explain-lock-verification-primer.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- [MySQL EXPLAIN for Range Locking Primer](./mysql-explain-range-locking-primer.md)
- [MySQL RR exact-key probe assumptions checklist](./mysql-rr-exact-key-probe-assumptions-checklist.md)
- [Spring/JPA Exact-Key Lock Mapping Guide](./spring-jpa-exact-key-lock-mapping-guide.md)
- [MySQL REPEATABLE READ Safe-Range Checklist](./mysql-repeatable-read-safe-range-checklist.md)
- [Statistics / Histograms / Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)
- [인덱스와 실행 계획](./index-and-explain.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: explain checklist exact key locking read, explain duplicate precheck, mysql explain analyze duplicate precheck, explain analyze pre-check drift, explain unique key path check, mysql explain for update unique index, exact key explain beginner, full unique key equality explain, duplicate pre-check explain, chosen index path duplicate check, explain before trusting for update, for share explain checklist, jpa duplicate precheck explain, why locking read changed plan, explain key rows type duplicate check

## 핵심 개념

먼저 아주 단순하게 보면 된다.

- `UNIQUE`는 "문이 잠겼는지"를 결정한다.
- locking read pre-check는 "문 앞에서 같은 사람을 먼저 줄 세우는지"를 본다.
- `EXPLAIN`은 "정말 그 문 앞으로 갔는지"를 확인하는 도구다.

즉 `SELECT ... FOR UPDATE`를 썼다는 사실만으로는 부족하다.
입문자용 기억법은 한 줄이다.

> exact-key locking read는 `WHERE` 문장이 아니라 **실제로 고른 unique-key 경로**를 믿어야 한다.

## 30초 체크

| 먼저 볼 것 | 기대하는 모양 | 초보자 해석 |
|---|---|---|
| `key` | intended `UNIQUE` 또는 full composite unique index 이름 | 맞는 책꽂이를 찾고 있다 |
| `type` | 보통 `const`, `ref`, `eq_ref`처럼 좁은 접근 | 거의 한 칸만 확인한다 |
| `rows` | 대개 아주 작다. 보통 `1` 근처 | 넓은 범위를 더듬지 않는다 |
| `Extra` | 불필요한 정렬/넓은 후처리 신호가 없다 | index probe가 단순하다 |

이 네 줄 중 하나라도 어색하면 "duplicate pre-check가 exact-key처럼 동작한다"는 설명은 잠시 멈추는 편이 맞다.

## 왜 이 체크가 필요한가

같은 business 의도라도 SQL 모양이 조금만 바뀌면 실제 접근 경로는 달라질 수 있다.

- full key equality를 그대로 쓰면: intended unique index 한 칸을 찌르기 쉽다
- 함수가 끼면: 다른 경로나 더 넓은 scan으로 미끄러지기 쉽다
- key 일부만 쓰면: exact-key가 아니라 prefix range에 가까워진다
- ORM query refactor가 들어오면: lock clause는 그대로인데 path는 달라질 수 있다

그래서 beginner 기준 질문은 "`FOR UPDATE`를 썼나?"가 아니라 "`EXPLAIN`에서 intended unique-key path가 보이나?"다.

## 예시로 보는 good / suspicious

중복 발급 pre-check가 아래처럼 있다고 가정하자.

```sql
SELECT 1
FROM coupon_issue
WHERE coupon_id = :coupon_id
  AND member_id = :member_id
FOR SHARE;
```

그리고 인덱스는 이렇다.

```sql
UNIQUE KEY uq_coupon_member (coupon_id, member_id)
```

### 기대하는 EXPLAIN 모양

| 항목 | 기대값 예시 | 왜 중요한가 |
|---|---|---|
| `key` | `uq_coupon_member` | intended unique-key path를 실제로 탔다 |
| `type` | `const` / `ref` | full scan이나 넓은 range가 아니다 |
| `rows` | `1` 근처 | exact-key probe에 가깝다 |
| `Extra` | 단순하거나 거의 비어 있음 | 정렬/임시 처리보다 lookup이 중심이다 |

이 장면이면 "적어도 optimizer는 원하던 책꽂이의 같은 칸을 보러 갔다"라고 말할 수 있다.

### 바로 의심해야 하는 EXPLAIN 모양

| 보이는 신호 | 왜 위험한가 | 초보자 다음 행동 |
|---|---|---|
| `key = NULL` | 인덱스 path 자체가 아니다 | exact-key 가정 중지, query/index 다시 본다 |
| `key`가 다른 인덱스 | 다른 칸이나 더 넓은 축을 더듬는다 | intended unique index와 차이를 확인한다 |
| `rows`가 크다 | exact-key보다 range scan일 가능성이 크다 | full-key equality, 통계, index shape를 다시 본다 |
| 함수/정렬/join 때문에 plan이 커졌다 | lock clause는 있어도 path drift가 생긴다 | SQL을 exact-key 전용 query로 분리한다 |

## beginner 체크리스트

### 1. intended unique index 이름을 먼저 적는다

`EXPLAIN`을 보기 전에 머릿속 목표를 먼저 써 둔다.

- 내가 기대하는 인덱스 이름은 무엇인가
- 그 인덱스의 full key는 무엇인가
- 이 query가 그 full key를 equality로 모두 쓰는가

예를 들면:

- intended index: `uq_coupon_member`
- full key: `(coupon_id, member_id)`
- query equality: `coupon_id = ? AND member_id = ?`

이 준비 없이 `EXPLAIN`을 보면 "`인덱스를 썼네`" 수준에서 멈추기 쉽다.

### 2. `key`가 intended unique index인지 본다

가장 먼저 볼 것은 `key`다.

- `key = uq_coupon_member`
  - 좋은 출발점이다
- `key = idx_coupon_id`
  - key 일부만 탄 것일 수 있다
- `key = NULL`
  - exact-key path가 아니다

입문자 기억법:

> "인덱스를 썼다"가 아니라 "원하던 `UNIQUE` 인덱스를 썼다"까지 확인해야 한다.

### 3. full key equality가 실제로 유지됐는지 본다

SQL이 아래처럼 바뀌면 exact-key 가정이 바로 약해질 수 있다.

```sql
WHERE coupon_id = :coupon_id
```

```sql
WHERE LOWER(email) = LOWER(:email)
```

```sql
WHERE coupon_id = :coupon_id
ORDER BY created_at DESC
LIMIT 1
```

이런 query는 business 문장상 비슷해 보여도, physical probe는 다른 경로가 되기 쉽다.

### 4. `rows`를 보고 "거의 한 칸인가"를 묻는다

beginner에게 `rows`는 아주 정교한 숫자보다 "좁은가, 넓은가"가 더 중요하다.

- `rows`가 `1` 근처다
  - exact-key lookup 그림에 가깝다
- `rows`가 크다
  - 이미 exact-key보다 넓은 범위를 읽는다는 뜻일 수 있다

`rows`가 큰데도 "same-key insert를 줄 세우는 exact-key pre-check"라고 설명하면 거의 항상 과장이다.

### 5. `type`과 `Extra`가 query drift를 암시하는지 본다

이 문서에서는 `type`과 `Extra`를 깊게 파고들기보다, path drift 경보등으로만 보면 충분하다.

- `type`이 좁은 lookup처럼 보인다
  - good sign
- `type = range`로 넓어졌다
  - key 일부만 쓰거나 다른 축을 타는지 본다
- `Extra`에 정렬/임시 처리 신호가 눈에 띈다
  - duplicate pre-check 전용 query인지 다시 본다

## beginner 체크리스트 (계속 2)

핵심은 "`FOR UPDATE`/`FOR SHARE`가 붙었는가"보다 "lookup이 아직 단순한가"다.

## plain `EXPLAIN`이면 충분한 때 vs `EXPLAIN ANALYZE`가 아까운 때

입문자 기준 기본값은 `EXPLAIN`부터다. duplicate pre-check 검증의 1차 질문은 보통 "실제 chosen path가 intended unique-key인가?"이기 때문이다.

| 상황 | 먼저 볼 것 | 왜 이걸로 충분한가 / 더 볼 가치가 있는가 |
|---|---|---|
| `key`가 intended `UNIQUE`가 아니거나 `rows`가 이미 크다 | plain `EXPLAIN` | path가 이미 어긋났다. 이때는 actual timing보다 query shape 수정이 먼저다 |
| full-key equality, 단순 단일 테이블 probe, `key/type/rows`가 기대와 거의 같다 | plain `EXPLAIN` | beginner 검증 목적에는 이 정도면 충분하다. "올바른 책꽂이의 거의 한 칸"인지 먼저 답할 수 있다 |
| 문서상으로는 exact-key인데 운영에서 duplicate pre-check 체감이 갑자기 흔들린다 | `EXPLAIN ANALYZE` 추가 검토 | estimates는 좋아 보여도 actual rows가 튀거나 추가 읽기가 숨어 있을 수 있다 |
| 통계 변경, predicate refactor, join/정렬 추가 뒤에 "`rows=1`인데 왜 넓게 읽지?" 같은 의심이 남는다 | `EXPLAIN ANALYZE` 추가 검토 | duplicate pre-check drift가 estimate 단계에서는 안 보이고 actual execution에서만 드러나는 경우가 있다 |

짧은 기억법은 이렇다.

- plain `EXPLAIN`: "어느 책꽂이로 갔는지"를 확인한다
- `EXPLAIN ANALYZE`: "실제로 몇 칸을 더 만졌는지"를 확인한다

### duplicate pre-check drift에서 `EXPLAIN ANALYZE`가 특히 useful한 장면

아래처럼 표면상으로는 exact-key query처럼 보이는데, 실제 실행에서 추가 읽기가 붙는지 의심될 때만 한 번 더 본다.

- `EXPLAIN`의 `key`는 맞는데 운영 lock wait이나 duplicate timing이 예전과 다르다
- histogram/statistics 변경 뒤에 `rows` estimate는 그대로인데 체감 경합이 달라졌다
- ORM refactor 후 SQL shape는 비슷한데 join/filter pushdown 때문에 actual rows가 늘어난 의심이 있다

이때 beginner가 깊게 해석해야 할 것은 많지 않다.

1. `EXPLAIN`의 `key/type/rows`는 여전히 intended path처럼 보이는가
2. `EXPLAIN ANALYZE`의 actual rows도 정말 작게 유지되는가
3. estimate는 작았는데 actual rows만 커졌다면, "pre-check가 문서보다 넓게 읽는다"는 drift 후보로 본다

## plain `EXPLAIN`이면 충분한 때 vs `EXPLAIN ANALYZE`가 아까운 때 (계속 2)

즉 duplicate pre-check 검증은 보통 plain `EXPLAIN`으로 끝나고, `EXPLAIN ANALYZE`는 **estimate와 실제 체감이 엇갈릴 때만 꺼내는 2차 확인**으로 두면 beginner가 덜 흔들린다.

그리고 `EXPLAIN` 결과는 멀쩡한데 운영에서는 "`같은 key queue`가 갑자기 안 보인다"면, plan 자체보다 **mixed write path**가 문제일 수 있다. 그 경우에는 [MySQL RR exact-key probe assumptions checklist](./mysql-rr-exact-key-probe-assumptions-checklist.md)로 넘어가 writer protocol까지 같이 확인하는 편이 빠르다.

## 자주 틀리는 장면

- "`key`만 있으면 충분하다"
  - 아니다. intended unique index인지가 중요하다.
- "`rows = 1`이면 무조건 안전하다"
  - 아니다. correctness backstop은 여전히 `UNIQUE`다.
- "`FOR UPDATE`로 바꾸면 괜찮아진다"
  - empty-result exact-key에서는 lock 세기보다 path 유지가 더 중요하다.
- "JPA 메서드 이름이 같으니 같은 query다"
  - 아니다. JPQL 함수, join, 정렬 추가만으로도 plan이 달라질 수 있다.

## 실무에서 이렇게 적어 두면 덜 흔들린다

코드 리뷰나 문서에 아래 세 줄을 남기면 beginner도 훨씬 덜 헷갈린다.

1. exact-key pre-check의 intended index 이름
2. `EXPLAIN`에서 확인한 `key`, `type`, `rows`
3. "이 pre-check는 queueing 보조일 뿐, correctness는 `UNIQUE`가 맡는다"는 문장

짧은 예시는 이렇다.

```text
Duplicate pre-check assumes EXPLAIN uses uq_coupon_member
key=uq_coupon_member, type=ref, rows=1
Correctness backstop remains UNIQUE(coupon_id, member_id)
```

## 다음에 어디로 가면 좋은가

- "`0 row FOR UPDATE` 자체가 왜 최종 보장이 아니지?"가 궁금하면 [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- Hibernate 로그에 찍힌 실제 SQL을 `EXPLAIN`에 옮기는 절차부터 보고 싶으면 [Hibernate SQL Log + EXPLAIN Lock Verification Primer](./hibernate-sql-log-explain-lock-verification-primer.md)
- RR exact-key queue 그림을 먼저 보고 싶으면 [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- Spring Data JPA query refactor 때문에 path가 흔들리는 장면을 보고 싶으면 [Spring/JPA Exact-Key Lock Mapping Guide](./spring-jpa-exact-key-lock-mapping-guide.md)
- exact-key를 넘어서 range/overlap을 beginner 흐름으로 이어서 보고 싶으면 [MySQL EXPLAIN for Range Locking Primer](./mysql-explain-range-locking-primer.md)
- range/overlap의 RR 가정을 더 엄밀하게 검증하려면 [MySQL REPEATABLE READ Safe-Range Checklist](./mysql-repeatable-read-safe-range-checklist.md)
- `EXPLAIN`의 `type`/`key`/`rows` 자체가 아직 낯설면 [인덱스와 실행 계획](./index-and-explain.md)
- estimate와 actual rows가 왜 엇갈리는지까지 보고 싶으면 [Statistics / Histograms / Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)

## 한 줄 정리

exact-key locking read를 믿으려면 `FOR UPDATE` 자체보다 `EXPLAIN`의 `key/type/rows`가 intended full unique-key path를 가리키는지 먼저 확인해야 하고, 마지막 중복 안전성은 여전히 `UNIQUE`가 책임진다.
