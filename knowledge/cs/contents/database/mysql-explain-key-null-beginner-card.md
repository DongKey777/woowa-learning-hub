---
schema_version: 3
title: MySQL EXPLAIN key NULL Beginner Card
concept_id: database/mysql-explain-key-null-beginner-card
canonical: true
category: database
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- mysql-explain
- index-basics
- query-tuning
- beginner-card
aliases:
- mysql explain key null
- explain key null beginner
- key null what is
- explain no index chosen
- possible keys vs key
- explain 인덱스 안 타요
- key null 뭐예요
- 함수 때문에 인덱스 안 타요
- 타입 변환 때문에 key null
symptoms:
- MySQL EXPLAIN에서 key가 NULL로 보여 실제 사용 인덱스가 없는지 헷갈려
- possible_keys는 있는데 key NULL이라 후보 인덱스와 실제 선택을 구분하지 못하고 있어
- WHERE 컬럼에 함수나 타입 변환을 써서 인덱스가 있어도 plan에서 선택되지 않아
intents:
- definition
- troubleshooting
prerequisites:
- database/index-basics
- database/index-and-explain
next_docs:
- database/mysql-explain-type-all-beginner-card
- database/generated-columns-functional-index-migration
- database/query-tuning-checklist
linked_paths:
- contents/database/index-and-explain.md
- contents/database/index-basics.md
- contents/database/generated-columns-functional-index-migration.md
- contents/database/query-tuning-checklist.md
- contents/spring/spring-data-jpa-basics.md
- contents/database/mysql-explain-type-all-beginner-card.md
- contents/database/covering-index-composite-ordering.md
- contents/database/jdbc-jpa-mybatis-basics.md
confusable_with:
- database/mysql-explain-type-all-beginner-card
- database/index-and-explain
- database/query-tuning-checklist
forbidden_neighbors: []
expected_queries:
- MySQL EXPLAIN에서 key NULL은 인덱스가 아예 없다는 뜻이야?
- possible_keys는 있는데 key가 NULL이면 초보자는 어디부터 확인해야 해?
- WHERE 컬럼에 LOWER 같은 함수를 쓰면 왜 key NULL이 나올 수 있어?
- type ALL과 key NULL이 같이 보일 때 full scan 원인을 어떻게 줄여 봐?
- EXPLAIN 처음 볼 때 key, possible_keys, rows를 어떤 순서로 해석해?
contextual_chunk_prefix: |
  이 문서는 MySQL EXPLAIN의 key NULL을 실제 사용 인덱스 없음으로 읽고 possible_keys, WHERE shape, 함수, 타입 변환을 점검하는 beginner symptom card다.
  key null 뭐예요, explain 인덱스 안 타요, possible_keys와 key 차이 질문이 본 문서에 매핑된다.
---
# MySQL `EXPLAIN`에서 `key = NULL`이 보여요

> 한 줄 요약: MySQL `EXPLAIN`의 `key = NULL`은 "실제로 탄 인덱스가 없다"는 뜻이고, 초보자는 먼저 `WHERE` 조건 컬럼, 함수 사용, 타입 변환을 점검하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [인덱스와 실행 계획](./index-and-explain.md)
- [인덱스 기초](./index-basics.md)
- [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md)
- [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: mysql explain key null, key = null what is, explain key null beginner, explain 인덱스 안 타요, mysql explain why key null, where 조건인데 key null, explain 처음 key null, key null 뭐예요, explain no index chosen, mysql explain actual key null, 함수 때문에 인덱스 안 타요, 타입 변환 때문에 key null

## 핵심 개념

`key`는 **MySQL이 실제로 고른 인덱스 이름**이다.  
그래서 `key = NULL`은 "후보 인덱스가 있더라도 이번 plan에서는 그 인덱스를 타지 않았다"는 뜻으로 읽으면 된다.

초보자 첫 반응은 "`인덱스를 안 만들었나?`"지만, 그게 전부는 아니다.

- 인덱스 자체가 없을 수 있다.
- 인덱스는 있어도 `WHERE` 조건식 모양 때문에 못 탈 수 있다.
- 데이터 양이 작아서 MySQL이 full scan이 더 싸다고 볼 수도 있다.

이 카드는 "왜 `key = NULL`이 나왔는지"를 처음 3분 안에 줄이는 entrypoint다.

## 한눈에 보기

| 지금 보이는 것 | 초보자용 첫 해석 | 먼저 적을 메모 |
| --- | --- | --- |
| `key = NULL` | 실제 사용 인덱스가 없다 | 인덱스 유무와 조건식 모양 확인 |
| `possible_keys`도 `NULL` | 후보 인덱스 자체가 약하다 | `WHERE` 컬럼 인덱스부터 확인 |
| `possible_keys`는 있는데 `key = NULL` | 인덱스는 있어도 못 탔을 수 있다 | 함수, 타입 변환, 너무 넓은 조건 확인 |
| `key = NULL` + `type = ALL` | 넓게 훑는 scan 후보다 | full scan 원인부터 적는다 |

```text
key = NULL
-> 실제 사용 인덱스 없음
-> 인덱스 부재인지, 조건식 모양 문제인지 분리
```

## 가장 흔한 이유 3가지

### 1. 조건 컬럼에 맞는 인덱스가 없다

가장 단순한 경우다.

```sql
SELECT *
FROM orders
WHERE status = 'PAID';
```

`status` 인덱스가 없으면 `key = NULL`은 자연스럽다.  
이때는 "옵티마이저가 이상하다"보다 **찾는 컬럼에 길이 없는지**부터 보는 편이 맞다.

### 2. 함수나 계산식이 인덱스 모양을 깨고 있다

```sql
SELECT *
FROM member
WHERE LOWER(email) = 'alice@example.com';
```

`email` 인덱스가 있어도 `LOWER(email)`처럼 컬럼에 함수를 씌우면 일반 B-Tree 인덱스를 바로 못 쓰는 경우가 흔하다.  
MySQL 버전과 설계에 따라 generated column이나 functional index로 풀 수 있지만, 그 판단은 follow-up 문서에서 본다.

### 3. 타입 변환이나 너무 넓은 조건 때문에 이득이 작다

```sql
SELECT *
FROM orders
WHERE created_at >= '2020-01-01';
```

인덱스가 있어도 대부분의 row를 읽어야 하면 MySQL이 full scan을 더 싸다고 볼 수 있다.  
또한 문자열 컬럼에 숫자를 비교하는 식의 암묵적 타입 변환도 인덱스 사용을 흔들 수 있다.

## 처음 보는 예시

```sql
EXPLAIN
SELECT id, status, created_at
FROM orders
WHERE status = 'PAID';
```

```text
+----+-------------+--------+------+---------------+------+--------+-------------+
| id | select_type | table  | type | possible_keys | key  | rows   | Extra       |
+----+-------------+--------+------+---------------+------+--------+-------------+
|  1 | SIMPLE      | orders | ALL  | NULL          | NULL | 850000 | Using where |
+----+-------------+--------+------+---------------+------+--------+-------------+
```

이 장면의 초보자용 첫 문장은 이 정도면 충분하다.

- `status` 조건에 맞는 인덱스 경로가 안 보인다.
- 그래서 많은 row를 훑는 방향으로 plan이 잡혔다.
- 다음 확인 대상은 `status` 인덱스 유무와 조건식 모양이다.

## 자주 하는 오해

| 자주 하는 말 | 왜 틀릴 수 있나 | 더 안전한 표현 |
| --- | --- | --- |
| "`key = NULL`이면 인덱스가 아예 없다" | 인덱스가 있어도 이번 plan에서 안 쓸 수 있다 | "이번 실행 계획에서는 인덱스를 안 탔다" |
| "`possible_keys`가 있으면 결국 탈 거다" | 후보와 실제 선택은 다르다 | `possible_keys`와 `key`를 구분해서 본다 |
| "`key = NULL`이면 무조건 장애다" | 작은 테이블이나 넓은 조건에서는 scan이 합리적일 수도 있다 | "느린지 여부는 `rows`, 데이터 크기, 체감 시간까지 같이 본다" |
| "인덱스만 추가하면 끝" | 함수, 타입 변환, 조회 패턴이 문제일 수 있다 | `WHERE` shape를 같이 본다 |

## 다음 한 걸음

| 지금 함께 보이는 신호 | 바로 이어서 볼 문서 |
| --- | --- |
| `type = ALL`도 같이 보인다 | [MySQL `EXPLAIN`에서 `type = ALL`이 보여요](./mysql-explain-type-all-beginner-card.md) |
| 함수, `%like`, 타입 변환이 의심된다 | [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md) |
| `ORDER BY` 때문에 정렬이 따로 붙는다 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) |
| SQL이 어디서 나온 건지부터 헷갈린다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |

## 한 줄 정리

MySQL `EXPLAIN`의 `key = NULL`은 "이번 plan에서 실제 사용 인덱스가 없다"는 뜻이므로, 초보자는 먼저 인덱스 유무보다 `WHERE` 조건식 모양까지 함께 확인해야 한다.
