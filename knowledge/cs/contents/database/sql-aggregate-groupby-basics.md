---
schema_version: 3
title: SQL Aggregate Functions and GROUP BY Basics
concept_id: database/sql-aggregate-groupby-basics
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- sql
- aggregate
- group-by
- having
- beginner
aliases:
- SQL aggregate beginner
- GROUP BY basics
- count sum avg
- HAVING clause
- aggregate function
- WHERE vs HAVING
- DISTINCT vs GROUP BY
- group by null
- sql 통계 쿼리
- 집계 함수 입문
symptoms:
- GROUP BY와 집계 함수가 여러 행을 하나의 요약값으로 줄인다는 감각이 없어
- WHERE에 COUNT 조건을 쓰려 하거나 HAVING과 WHERE 차이를 헷갈려 해
- GROUP BY에 없는 컬럼을 SELECT에 넣어도 되는지 MySQL 동작 때문에 혼란스러워 해
intents:
- definition
- drill
- comparison
prerequisites:
- database/sql-join-basics
- database/sql-relational-modeling-basics
next_docs:
- database/having-vs-where-beginner-card
- database/distinct-vs-group-by-beginner-card
- database/sql-joins-and-query-order
linked_paths:
- contents/database/having-vs-where-beginner-card.md
- contents/database/distinct-vs-group-by-beginner-card.md
- contents/database/sql-joins-and-query-order.md
- contents/database/index-and-explain.md
- contents/spring/spring-data-jpa-basics.md
confusable_with:
- database/having-vs-where-beginner-card
- database/distinct-vs-group-by-beginner-card
- database/result-row-explosion-debugging
forbidden_neighbors: []
expected_queries:
- SQL GROUP BY와 COUNT SUM AVG 같은 aggregate function을 처음 배우는데 쉽게 설명해줘
- WHERE와 HAVING은 실행 순서가 어떻게 달라서 COUNT 조건은 HAVING에 써야 해?
- GROUP BY에 없는 컬럼을 SELECT에 넣으면 왜 비결정적인 결과가 될 수 있어?
- COUNT star와 COUNT column은 NULL 처리 때문에 어떤 차이가 있어?
- DISTINCT와 GROUP BY는 둘 다 중복을 줄여 보이는데 의미가 어떻게 달라?
contextual_chunk_prefix: |
  이 문서는 SQL aggregate function, GROUP BY, COUNT/SUM/AVG, HAVING, WHERE vs HAVING을 beginner primer로 설명한다.
  집계 함수 입문, group by 기초, sql 통계 쿼리, DISTINCT vs GROUP BY 질문이 본 문서에 매핑된다.
---
# SQL 집계 함수와 GROUP BY 기초

> 한 줄 요약: 집계 함수는 여러 행을 하나의 요약값으로 줄이는 함수이고, GROUP BY는 특정 컬럼 기준으로 행을 묶어 그룹별 집계를 가능하게 하는 절이다.

**난이도: 🟢 Beginner**

관련 문서:

- [HAVING vs WHERE 초보자 비교 카드](./having-vs-where-beginner-card.md)
- [DISTINCT vs GROUP BY 초보자 비교 카드](./distinct-vs-group-by-beginner-card.md)
- [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
- [인덱스와 실행 계획](./index-and-explain.md)
- [database 카테고리 인덱스](./README.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

retrieval-anchor-keywords: sql aggregate beginner, group by 처음 배우는데, count sum avg 입문, having 절 설명, group by 기초, sql 집계 함수 입문, 집계 함수가 뭐예요, select group by order, having vs where 차이, sql 통계 쿼리 입문, sql aggregate groupby basics basics, sql aggregate groupby basics beginner, sql aggregate groupby basics intro, database basics, beginner database

## 핵심 개념

**집계 함수(aggregate function)** 는 여러 행을 하나의 값으로 요약한다. 대표적인 것은 다섯 가지다:

- `COUNT(*)` — 행 수
- `SUM(컬럼)` — 합계
- `AVG(컬럼)` — 평균
- `MAX(컬럼)` — 최댓값
- `MIN(컬럼)` — 최솟값

**`GROUP BY`** 는 집계 함수의 짝이다. 특정 컬럼 기준으로 행을 묶고, 묶음(그룹)별로 집계 함수를 적용한다.

입문자가 자주 헷갈리는 지점:

- `GROUP BY`가 있으면 `SELECT` 절에는 집계 함수 또는 `GROUP BY`에 나열된 컬럼만 올 수 있다
- `WHERE`는 그룹을 만들기 전에 필터링하고, `HAVING`은 그룹이 만들어진 후에 필터링한다
- `COUNT(*)`와 `COUNT(컬럼)` 은 다르다 — `COUNT(컬럼)`은 NULL 값이 있는 행을 세지 않는다

## 한눈에 보기

```sql
SELECT department, COUNT(*), AVG(salary)
FROM employees
WHERE hire_year >= 2020
GROUP BY department
HAVING AVG(salary) > 50000
ORDER BY AVG(salary) DESC;
```

실행 순서: `FROM` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `ORDER BY`

이 순서를 모르면 "왜 `WHERE`에 집계 함수를 못 쓰는지"가 이해되지 않는다.

## 상세 분해

**`WHERE` vs `HAVING`**:

- `WHERE department = 'tech'` — 그룹 묶기 전에 개별 행 필터. 집계 함수를 조건으로 쓸 수 없다.
- `HAVING COUNT(*) > 5` — 그룹 묶은 후 그룹 단위 필터. 집계 함수를 조건으로 쓸 수 있다.

`HAVING`을 언제 써야 하는지 1분 decision card로 다시 잡고 싶다면 [HAVING vs WHERE 초보자 비교 카드](./having-vs-where-beginner-card.md)를 먼저 보면 된다.

**`GROUP BY` + `NULL`**:

NULL을 가진 행은 하나의 그룹으로 묶인다. 예를 들어 부서가 NULL인 직원들이 여러 명이면 NULL 그룹으로 모인다. 의도치 않은 집계가 생길 수 있으므로 NULL 여부를 먼저 확인하는 것이 좋다.

**`DISTINCT` vs `GROUP BY`**:

중복을 제거하는 `SELECT DISTINCT`와 `GROUP BY`는 결과가 같을 때도 있지만 의미가 다르다. 집계 함수 없이 유일한 값 목록만 필요하면 `DISTINCT`, 그룹별 요약이 필요하면 `GROUP BY`가 적합하다.
이 구분만 빠르게 다시 잡고 싶다면 [DISTINCT vs GROUP BY 초보자 비교 카드](./distinct-vs-group-by-beginner-card.md)를 먼저 보면 된다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "`WHERE`에서 `COUNT(*) > 10` 조건을 쓰면 된다" | `WHERE`는 그룹 집계 전에 실행되므로 집계 함수를 쓸 수 없다 | `HAVING COUNT(*) > 10` 으로 바꾼다 |
| "`GROUP BY`에 없는 컬럼을 `SELECT`에 써도 된다" | MySQL에서는 `ONLY_FULL_GROUP_BY` 설정이 꺼져 있으면 허용되지만 결과가 비결정적이다 | 집계 함수나 `GROUP BY` 컬럼만 `SELECT`에 넣는 것을 원칙으로 한다 |
| "`COUNT(*)`와 `COUNT(id)`는 항상 같다" | `id`에 NULL이 없으면 같지만, NULL이 있는 컬럼을 세면 COUNT 값이 달라진다 | NULL 가능 컬럼을 셀 때는 의도를 명확히 한다 |

## 실무에서 쓰는 모습

**(1) 대시보드 통계** — 날짜별 주문 건수, 월별 매출 합계 등 보고서 쿼리에서 가장 흔히 쓰인다. `GROUP BY DATE(created_at)` 처럼 날짜 함수와 조합한다.

**(2) 조건부 집계** — 특정 상태인 행만 세고 싶을 때 `COUNT(CASE WHEN status = 'done' THEN 1 END)` 패턴을 사용한다. 여러 조건의 집계를 한 쿼리로 뽑을 때 유용하다.

## 더 깊이 가려면

- 쿼리 실행 순서와 복잡한 조인 + 집계 조합 → [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
- `GROUP BY` 컬럼에 인덱스가 어떻게 작용하는지 → [인덱스와 실행 계획](./index-and-explain.md)

## 면접/시니어 질문 미리보기

> Q: `WHERE`와 `HAVING`의 차이를 설명해 주세요.
> 의도: SQL 실행 순서와 각 절의 역할을 이해하는지 확인
> 핵심: `WHERE`는 그룹 집계 전 개별 행 필터이고 `HAVING`은 그룹 집계 후 그룹 단위 필터다. 집계 함수 조건은 반드시 `HAVING`에 써야 한다.

> Q: `GROUP BY` 없이 `COUNT(*)`만 쓰면 어떻게 되나요?
> 의도: 집계 함수의 동작 방식을 아는지 확인
> 핵심: 테이블 전체가 하나의 그룹이 되어 전체 행 수 하나를 반환한다.

## 한 줄 정리

집계 함수는 여러 행을 하나의 값으로 줄이고, `GROUP BY`는 그룹을 나누며, `HAVING`은 그룹 집계 결과를 필터링한다.
