# MySQL `EXPLAIN`에서 `Using temporary`가 보여요

> 한 줄 요약: MySQL `EXPLAIN`의 `Using temporary`는 `GROUP BY`, `DISTINCT`, 재정렬 때문에 중간 결과를 한 번 더 모으는 신호이고, 초보자는 "무조건 장애"보다 "왜 중간 정리가 필요했나"를 먼저 보면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [EXPLAIN 첫 판독 미니카드](./explain-first-read-timeout-mini-card.md)
- [인덱스와 실행 계획](./index-and-explain.md)
- [SQL 집계 함수와 GROUP BY 기초](./sql-aggregate-groupby-basics.md)
- [GROUP BY 결과를 왜 다시 ORDER BY 하면 느려지나요?](./group-by-order-by-different-axis-mysql-postgresql-bridge.md)
- [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md)
- [Distinct vs Group By Beginner Card](./distinct-vs-group-by-beginner-card.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: mysql explain using temporary, using temporary what is, explain using temporary beginner, using temporary 왜 보여요, group by using temporary, distinct using temporary, explain 처음 using temporary, temporary table in explain, using temporary 뭐예요, mysql extra using temporary, group by 헷갈려요, explain 중간 결과 정리

## 핵심 개념

`Using temporary`는 **중간 결과를 한 번 모아 두는 단계가 plan에 붙었다**는 신호다.  
초보자는 이를 "갑자기 디스크 파일을 만든다"로 오해하기 쉬운데, 첫 해석은 그보다 단순하다.

- 먼저 묶어야 할 결과가 있다.
- 중복 제거가 필요하다.
- 집계 뒤 다른 기준으로 다시 정렬해야 한다.

즉 핵심 질문은 "`temporary`가 왜 생겼나?"이지, "`무조건 없애야 하나?`"가 아니다.

## 한눈에 보기

| 보이는 모양 | 초보자용 첫 해석 | 첫 질문 |
| --- | --- | --- |
| `GROUP BY status` | 같은 값끼리 다시 묶는다 | 그룹 기준에 맞는 인덱스가 있나 |
| `SELECT DISTINCT status` | 중복 제거가 필요하다 | 정말 distinct가 필요한가 |
| `Using temporary; Using filesort` | 묶은 뒤 다시 정렬한다 | 집계 기준과 정렬 기준이 다른가 |
| `key`는 있는데 `Using temporary`가 남음 | 인덱스가 있어도 중간 정리는 남을 수 있다 | 인덱스와 집계/정렬 축이 맞는가 |

```text
Using temporary
-> 중간 결과 정리 단계 추가
-> group by / distinct / 재정렬 여부 확인
```

## 언제 자주 보이나

### 1. `GROUP BY`

```sql
SELECT status, COUNT(*)
FROM orders
GROUP BY status;
```

같은 `status`끼리 모아야 하므로 중간 집계 작업이 붙기 쉽다.  
초보자에게는 "`status`별로 묶는 통"을 한 번 만드는 장면이라고 설명하면 충분하다. 다만 실제 내부 구현은 엔진/버전에 따라 더 복잡할 수 있다.

### 2. `DISTINCT`

```sql
SELECT DISTINCT status
FROM orders;
```

중복 값을 제거하려면 결과를 한 번 정리해야 한다.  
그래서 `DISTINCT`도 beginner 눈높이에서는 `GROUP BY`와 비슷한 "묶기" 신호로 읽어도 된다.

### 3. 집계 후 다른 기준으로 다시 정렬

```sql
SELECT status, COUNT(*)
FROM orders
GROUP BY status
ORDER BY COUNT(*) DESC;
```

이 장면에서는 묶은 뒤 `COUNT(*)` 기준으로 다시 줄 세워야 해서 `Using temporary; Using filesort`가 같이 보일 수 있다.

## 처음 보는 예시

```sql
EXPLAIN
SELECT status, COUNT(*)
FROM orders
WHERE created_at >= '2026-04-01'
GROUP BY status;
```

```text
+----+-------------+--------+-------+-----------------------+-----------------------+-------+----------------------------------+
| id | select_type | table  | type  | possible_keys         | key                   | rows  | Extra                            |
+----+-------------+--------+-------+-----------------------+-----------------------+-------+----------------------------------+
|  1 | SIMPLE      | orders | range | idx_orders_created_at | idx_orders_created_at | 48000 | Using where; Using temporary     |
+----+-------------+--------+-------+-----------------------+-----------------------+-------+----------------------------------+
```

이 예시는 이렇게 읽으면 충분하다.

- 날짜 필터 인덱스는 탔다.
- 하지만 남은 row를 `status`별로 다시 묶어야 한다.
- 그래서 중간 정리 작업이 하나 더 붙었다.

즉 `Using temporary`는 "인덱스가 하나도 없다"보다 **집계/중복 제거 축이 남아 있다**는 신호다.

## 자주 하는 오해

| 자주 하는 말 | 왜 틀릴 수 있나 | 더 안전한 표현 |
| --- | --- | --- |
| "`Using temporary`면 무조건 장애다" | 집계/중복 제거 쿼리에서는 자연스러울 수 있다 | "중간 정리 비용이 붙었으니 이유를 확인한다" |
| "`Using temporary`면 무조건 디스크를 쓴다" | 메모리 안에서 끝날 수도 있다 | "먼저 뜻하는 바는 중간 결과 저장 필요" |
| "인덱스가 잡혔으니 `temporary`는 이상하다" | 필터용 인덱스와 집계/정렬 경로는 다른 문제다 | `key`와 `Extra`를 분리해서 본다 |
| "`GROUP BY`면 항상 없앨 수 있다" | 요구하는 결과 자체가 집계라 중간 단계가 필요할 수 있다 | 쿼리 목적과 인덱스 정합성을 같이 본다 |

## 다음 한 걸음

| 지금 더 궁금한 것 | 다음 문서 |
| --- | --- |
| `GROUP BY`와 `DISTINCT` 차이부터 헷갈린다 | [Distinct vs Group By Beginner Card](./distinct-vs-group-by-beginner-card.md) |
| "`GROUP BY` 뒤 `ORDER BY COUNT(*)`가 왜 더 느리죠?" | [GROUP BY 결과를 왜 다시 ORDER BY 하면 느려지나요?](./group-by-order-by-different-axis-mysql-postgresql-bridge.md) |
| `Using filesort`도 같이 떠서 더 헷갈린다 | [EXPLAIN 첫 판독 미니카드](./explain-first-read-timeout-mini-card.md), [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md) |
| 집계 SQL을 더 기본부터 보고 싶다 | [SQL 집계 함수와 GROUP BY 기초](./sql-aggregate-groupby-basics.md) |
| spill, temp table 엔진 차이까지 궁금하다 | [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md) |

## 한 줄 정리

MySQL `EXPLAIN`의 `Using temporary`는 중간 결과 정리 단계가 붙었다는 뜻이므로, 초보자는 먼저 `GROUP BY`·`DISTINCT`·재정렬 중 무엇 때문에 생겼는지부터 확인하면 된다.
