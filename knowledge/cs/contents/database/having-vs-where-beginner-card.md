---
schema_version: 3
title: HAVING vs WHERE 초보자 비교 카드
concept_id: database/having-vs-where-beginner-card
canonical: true
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- having-vs-where-beginner
- row-filter-vs-group-filter
- aggregate-filter-basics
aliases:
- having vs where
- where vs having 차이
- having 언제 써요
- where 언제 써요
- sql 집계 조건 초보
- group by having beginner
- aggregate filter basics
- row filter vs group filter
- HAVING WHERE 차이
- COUNT WHERE error
symptoms:
- COUNT, SUM, AVG 같은 집계 결과 조건을 WHERE에 넣으려 하고 있어
- 행을 먼저 거를 조건과 그룹을 만든 뒤 거를 조건을 구분하지 못하고 있어
- WHERE와 HAVING을 아무 데나 써도 된다고 생각해 SQL 의미가 바뀌고 있어
intents:
- comparison
- definition
- troubleshooting
prerequisites:
- database/sql-aggregate-groupby-basics
- database/sql-joins-and-query-order
next_docs:
- database/group-by-order-by-different-axis-mysql-postgresql-bridge
- database/distinct-vs-group-by-beginner-card
- database/join-row-increase-distinct-symptom-card
linked_paths:
- contents/database/sql-aggregate-groupby-basics.md
- contents/database/sql-joins-and-query-order.md
- contents/database/sql-reading-relational-modeling-primer.md
- contents/database/group-by-order-by-different-axis-mysql-postgresql-bridge.md
- contents/database/distinct-vs-group-by-beginner-card.md
- contents/database/join-row-increase-distinct-symptom-card.md
- contents/spring/spring-data-jpa-basics.md
confusable_with:
- database/sql-aggregate-groupby-basics
- database/distinct-vs-group-by-beginner-card
- database/group-by-order-by-different-axis-mysql-postgresql-bridge
forbidden_neighbors: []
expected_queries:
- WHERE와 HAVING의 차이를 행 필터와 그룹 필터 기준으로 설명해줘
- COUNT(*) > 3 같은 집계 조건을 WHERE가 아니라 HAVING에 써야 하는 이유는 뭐야?
- WHERE와 HAVING을 같이 쓰는 SQL은 어떤 논리 순서로 읽어야 해?
- 개별 행 조건과 집계 결과 조건을 초보자 기준으로 어떻게 구분해?
- GROUP BY HAVING을 처음 배우는데 FROM WHERE GROUP BY HAVING SELECT 순서를 알려줘
contextual_chunk_prefix: |
  이 문서는 WHERE는 그룹 전 row filter, HAVING은 GROUP BY 후 aggregate/group filter라는 차이를 설명하는 beginner chooser다.
  having vs where, group by having, aggregate filter, COUNT WHERE error 같은 자연어 질문이 본 문서에 매핑된다.
---
# HAVING vs WHERE 초보자 비교 카드

> 한 줄 요약: 개별 행을 먼저 거를 조건이면 `WHERE`, `GROUP BY`로 묶은 뒤 집계 결과를 거를 조건이면 `HAVING`으로 고르면 초보자 실수가 크게 줄어든다.

**난이도: 🟢 Beginner**

관련 문서:

- [SQL 집계 함수와 GROUP BY 기초](./sql-aggregate-groupby-basics.md)
- [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
- [SQL 읽기와 관계형 모델링 기초](./sql-reading-relational-modeling-primer.md)
- [database 카테고리 인덱스](./README.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

retrieval-anchor-keywords: having vs where, where vs having 차이, having 언제 써요, where 언제 써요, sql 집계 조건 초보, group by having beginner, count where error, having 뭐예요, sql 처음 having where, aggregate filter basics, row filter vs group filter, what is having in sql

## 핵심 개념

초보자 기준으로는 한 문장만 먼저 잡으면 된다.

- `WHERE`는 **행(row)을 먼저 거른다**
- `HAVING`은 **그룹(group)을 만든 뒤 그 결과를 거른다**

그래서 집계 함수 `COUNT`, `SUM`, `AVG` 결과를 조건으로 걸고 싶다면 보통 `HAVING` 쪽이다.

입문자가 자주 막히는 이유는 SQL을 적는 순서와 DB가 이해하는 논리 순서가 다르기 때문이다. 쿼리에는 `SELECT`가 먼저 보이지만, 보통 논리적으로는 `FROM -> WHERE -> GROUP BY -> HAVING -> SELECT` 순서로 읽는 편이 안전하다.

## 한눈에 보기

| 지금 걸고 싶은 조건 | 먼저 고를 절 | 이유 |
|---|---|---|
| `status = 'PAID'` 인 주문만 보기 | `WHERE` | 아직 개별 주문 행을 거르는 단계다 |
| 고객별 주문 수가 3건 이상인 고객만 보기 | `HAVING` | `COUNT(*)`는 그룹을 만든 뒤 계산된다 |
| 2025년 주문만 모아서 고객별 건수 보기 | `WHERE` + `HAVING` | 먼저 행을 줄이고, 그다음 집계 결과를 거른다 |

```sql
SELECT customer_id, COUNT(*)
FROM orders
WHERE created_at >= '2025-01-01'
GROUP BY customer_id
HAVING COUNT(*) >= 3;
```

이 쿼리는 `2025년 주문 행`을 먼저 줄인 뒤, `고객별로 묶고`, 마지막에 `3건 이상인 고객 그룹`만 남긴다.

## 1분 결정 규칙

질문을 두 단계로 자르면 된다.

1. 내가 지금 고르려는 대상이 **주문 한 건, 직원 한 명, 댓글 한 줄** 같은 개별 행인가?
2. 아니면 **부서별 평균, 고객별 주문 수, 날짜별 매출 합계** 같은 집계 결과인가?

첫 번째면 `WHERE`, 두 번째면 `HAVING`이다.

헷갈리면 조건 문장에 집계 함수 이름이 들어가는지 먼저 본다.

- `price > 10000` -> 보통 `WHERE`
- `COUNT(*) > 3` -> 보통 `HAVING`
- `AVG(score) >= 90` -> 보통 `HAVING`

단, 집계 함수가 없더라도 `GROUP BY` 뒤의 그룹 자체를 제한하려는 의도라면 `HAVING`을 쓸 수 있다. 초보자 첫 규칙은 "집계 결과 조건이면 `HAVING`"으로 잡고, 나머지 예외는 follow-up 문서에서 넓히는 편이 안전하다.

## 왜 헷갈리나

가장 흔한 혼동은 "`WHERE COUNT(*) > 3` 쓰면 안 되나요?"다. 안 되는 이유는 `WHERE`가 `COUNT(*)`보다 먼저 적용되기 때문이다.

예를 들어 고객별 주문 수를 구하는 쿼리에서는:

1. `FROM orders`로 주문 행을 모은다.
2. `WHERE`가 있으면 개별 주문 행을 먼저 제거한다.
3. `GROUP BY customer_id`로 고객별 그룹을 만든다.
4. `COUNT(*)`를 계산한다.
5. `HAVING COUNT(*) >= 3`으로 그룹을 남길지 결정한다.

즉 `WHERE` 시점에는 아직 "고객별 주문 수"라는 값이 존재하지 않는다. 그래서 `HAVING`이 필요한 것이다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 위험한가 | 더 안전한 첫 대응 |
|---|---|---|
| "`WHERE`와 `HAVING`은 거의 같은데 아무 데나 써도 되죠?" | 필터 시점이 달라 결과 의미가 바뀐다 | 행 조건인지 집계 조건인지 먼저 말로 구분한다 |
| "`COUNT(*) > 3`도 조건이니까 `WHERE`에 쓰면 되죠?" | 집계값은 그룹 생성 뒤에야 생긴다 | `HAVING COUNT(*) > 3`으로 옮긴다 |
| "`HAVING`만 쓰면 `WHERE`는 필요 없죠?" | 원래 줄일 수 있는 행을 늦게 줄여 읽기와 의도가 흐려진다 | 행 조건은 먼저 `WHERE`에 둔다 |
| "MySQL에서 되면 항상 맞는 문법이죠?" | 제품별 허용 범위나 최적화 방식은 다를 수 있다 | beginner 규칙은 논리 순서 기준으로 잡고, 제품 차이는 필요할 때 따로 확인한다 |

## 실무에서 쓰는 모습

가장 흔한 패턴은 `WHERE`와 `HAVING`을 같이 쓰는 경우다.

```sql
SELECT department, AVG(salary)
FROM employees
WHERE employment_status = 'ACTIVE'
GROUP BY department
HAVING AVG(salary) >= 5000;
```

- `WHERE employment_status = 'ACTIVE'`는 퇴사자를 먼저 뺀다.
- `GROUP BY department`는 부서별로 묶는다.
- `HAVING AVG(salary) >= 5000`은 평균 급여가 기준 이상인 부서만 남긴다.

즉 `WHERE`는 재료를 고르고, `HAVING`은 요약 결과를 고른다고 이해하면 된다. 이 비유는 시작점으로는 좋지만, 실제 DB는 "재료통"과 "완성품 통" 두 개를 따로 들고 있는 것이 아니라 논리 처리 순서대로 조건을 해석한다는 점까지 함께 기억해야 한다.

## 더 깊이 가려면

- 집계 함수와 `GROUP BY` 기본기를 같이 다시 보려면 → [SQL 집계 함수와 GROUP BY 기초](./sql-aggregate-groupby-basics.md)
- 실행 순서 관점에서 `FROM -> WHERE -> GROUP BY -> HAVING`을 더 보려면 → [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
- `SELECT`가 왜 이런 순서로 읽히는지 큰 그림부터 다시 잡으려면 → [SQL 읽기와 관계형 모델링 기초](./sql-reading-relational-modeling-primer.md)
- Spring/JPA 코드에서 집계 쿼리가 어디서 만들어지는지 연결하려면 → [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

## 면접/시니어 질문 미리보기

> Q: `WHERE`와 `HAVING`의 차이를 초보자에게 어떻게 설명하시겠어요?
> 의도: 문법 암기보다 행 조건과 집계 조건을 구분하는지 확인
> 핵심: `WHERE`는 그룹 만들기 전 행 필터, `HAVING`은 그룹 만든 뒤 집계 결과 필터다.

> Q: `WHERE`와 `HAVING`을 같이 쓰는 이유는 무엇인가요?
> 의도: 필터 시점과 의도를 나눠 설명할 수 있는지 확인
> 핵심: 먼저 개별 행을 줄일 조건은 `WHERE`에 두고, 그 후 그룹 집계 결과를 남길 조건은 `HAVING`에 둔다.

## 한 줄 정리

`한 줄 한 줄 먼저 고를 조건`이면 `WHERE`, `묶어서 계산한 결과를 고를 조건`이면 `HAVING`으로 결정하면 초보자 대부분의 혼동을 줄일 수 있다.
