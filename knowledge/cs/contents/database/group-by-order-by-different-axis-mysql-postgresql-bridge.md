# `GROUP BY` 결과를 왜 다시 `ORDER BY` 하면 느려지나요?

> 한 줄 요약: `GROUP BY`로 묶는 축과 `ORDER BY`로 줄 세우는 축이 다르면, DB는 보통 "먼저 집계하고 그 결과를 다시 정렬"해야 해서 인덱스 한 번만으로 끝내기 어려워진다.

**난이도: 🟡 Intermediate**

관련 문서:

- [SQL 집계 함수와 GROUP BY 기초](./sql-aggregate-groupby-basics.md)
- [MySQL `EXPLAIN`에서 `Using temporary`가 보여요](./mysql-explain-using-temporary-beginner-card.md)
- [인덱스와 실행 계획](./index-and-explain.md)
- [PostgreSQL plan node 한 장 카드](./postgresql-plan-node-mini-card.md)
- [PostgreSQL `EXPLAIN ANALYZE` 용어 미니 브리지](./postgresql-explain-analyze-terms-mini-bridge.md)
- [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: group by order by why slow, group by order by different key, using temporary using filesort why, mysql group by order by 느려요, postgresql group by order by sort, 집계 기준과 정렬 기준이 달라요, group by 결과 다시 order by, count desc 정렬 왜 느려요, max created_at desc group by slow, beginner next step group by order by, intermediate bridge group by order by, 왜 group by 후 order by 느린가, group by order by basics, what is using temporary using filesort

## 먼저 멘탈모델

`GROUP BY`는 "같은 값을 한 바구니에 모으기"이고, `ORDER BY`는 "결과를 한 줄로 다시 세우기"다.

둘의 기준이 같으면 한 번에 끝날 여지가 있다.
하지만 기준이 다르면 DB는 보통 아래 순서를 밟는다.

```text
row 읽기
-> 그룹 만들기
-> 그룹별 계산 마치기
-> 계산된 결과를 다른 기준으로 다시 정렬
```

예를 들어 `status`별 주문 수를 구한 뒤 `COUNT(*) DESC`로 정렬하면,
인덱스는 원래 row 순서만 알고 있고 "계산이 끝난 뒤의 count 값 순서"는 미리 갖고 있지 않다.

비유는 여기까지만 안전하다.
실제 엔진은 hash aggregate, sort aggregate, temporary table, sort node처럼 더 다양한 구현을 고르며, 데이터 분포와 버전에 따라 plan은 달라질 수 있다.

## 언제 한 번에 끝나고, 언제 다시 정렬하나

| SQL 모양 | 인덱스로 한 번에 끝날 가능성 | 이유 |
| --- | --- | --- |
| `GROUP BY status ORDER BY status` | 비교적 있다 | 묶는 축과 정렬 축이 같다 |
| `GROUP BY status ORDER BY status DESC` | 경우에 따라 있다 | 같은 축이지만 엔진과 인덱스 방향 조건을 함께 봐야 한다 |
| `GROUP BY status ORDER BY COUNT(*) DESC` | 보통 낮다 | `COUNT(*)`는 집계가 끝나야 생기는 값이다 |
| `GROUP BY customer_id ORDER BY MAX(created_at) DESC` | 보통 낮다 | `MAX(created_at)`를 그룹마다 계산한 뒤 다시 줄 세워야 한다 |
| `GROUP BY DATE(created_at) ORDER BY DATE(created_at)` | 종종 낮다 | 함수 적용 때문에 원본 인덱스 순서를 그대로 못 쓸 수 있다 |

초보자 다음 단계에서 중요한 질문은 이것이다.

> 지금 정렬하는 값이 "원래 row에 있던 컬럼"인가, 아니면 "집계가 끝난 뒤에 생긴 값"인가?

뒤쪽이면 인덱스 한 번으로 끝나기 어려운 경우가 많다.

## MySQL에서는 보통 이렇게 보인다

MySQL은 `EXPLAIN`의 `Extra` 칸에서 신호를 먼저 준다.

```sql
SELECT status, COUNT(*) AS order_count
FROM orders
WHERE created_at >= '2026-01-01'
GROUP BY status
ORDER BY order_count DESC;
```

이런 쿼리에서는 MySQL 8.x 계열에서 자주 아래 같은 해석이 나온다.

- `Using temporary`: 그룹 결과를 한 번 모아 두는 단계가 붙었다
- `Using filesort`: 그 그룹 결과를 `order_count DESC` 기준으로 다시 정렬한다

핵심은 "`인덱스가 아예 없다`"가 아니라 "`집계 축`과 `정렬 축`이 달라서 중간 결과 재정리가 남았다"는 점이다.

반대로 아래처럼 같은 축이면 더 단순해진다.

```sql
SELECT status
FROM orders
WHERE created_at >= '2026-01-01'
GROUP BY status
ORDER BY status;
```

물론 이것도 항상 최적은 아니다.
필터 조건, 인덱스 선행 컬럼, row 수가 맞지 않으면 MySQL은 여전히 다른 경로를 고를 수 있다.

## PostgreSQL에서는 같은 현상이 다른 이름으로 보인다

PostgreSQL은 `Using temporary` 같은 문구보다 plan node 이름으로 보여 주는 편이다.

같은 질문을 PostgreSQL에서 보면 보통 아래 조합 중 하나를 먼저 만난다.

| 먼저 보이는 node | 초보자 다음 단계 해석 |
| --- | --- |
| `HashAggregate` | 먼저 그룹을 만들었다 |
| `GroupAggregate` | 정렬된 입력이나 정렬 단계를 바탕으로 그룹을 만들었다 |
| `Sort` | 집계 결과나 입력을 다시 줄 세우고 있다 |
| `Incremental Sort` | 일부 정렬 이점을 활용하지만 추가 정렬이 여전히 필요하다 |

예를 들어 `GROUP BY status ORDER BY COUNT(*) DESC`라면 PostgreSQL 14+에서는 흔히 이런 그림이 나온다.

```text
Seq Scan or Index Scan
-> HashAggregate
-> Sort (key: count(*) DESC)
```

이건 MySQL의 `Using temporary; Using filesort`와 1:1 번역은 아니다.
그래도 learner 관점에서는 같은 질문으로 읽으면 된다.

- 먼저 그룹을 만들었나
- 그 뒤에 다시 `Sort`가 붙었나
- 정렬 기준이 집계 후 값인가

## 예시 하나로 감각 붙이기

아래 쿼리는 "고객별 마지막 주문 시각"을 구한 뒤, 최근 고객부터 보고 싶다는 뜻이다.

```sql
SELECT customer_id, MAX(created_at) AS last_order_at
FROM orders
GROUP BY customer_id
ORDER BY last_order_at DESC
LIMIT 10;
```

이 쿼리에서 인덱스 `INDEX(customer_id, created_at)`가 있더라도 초보자가 바로 기대하면 안 되는 점이 있다.

1. 인덱스는 `customer_id`별 row를 찾는 데 도움을 줄 수 있다.
2. 하지만 `last_order_at`는 그룹 계산이 끝난 뒤에 확정된다.
3. 그래서 "상위 10개 고객"을 뽑으려면 계산된 결과를 다시 비교해야 한다.

즉 인덱스가 "집계까지는 도와줄 수 있어도, 집계 결과 순위"까지 항상 대신해 주는 것은 아니다.

## 자주 헷갈리는 포인트

| 자주 하는 말 | 왜 위험한가 | 더 안전한 표현 |
| --- | --- | --- |
| "`GROUP BY` 컬럼에 인덱스가 있으면 `ORDER BY`도 자동으로 해결된다" | 정렬 기준이 집계 후 값이면 별개 문제다 | 인덱스가 집계 입력을 돕더라도 결과 재정렬은 남을 수 있다 |
| "`Using filesort`면 디스크 정렬이라서 무조건 나쁘다" | 메모리 안에서 끝날 수도 있고, 핵심은 추가 정렬 단계 존재다 | 먼저 "인덱스 순서로 못 끝났다"로 읽는다 |
| "PostgreSQL에는 `Using temporary`가 없으니 같은 문제가 아니다" | node 이름만 다를 뿐 비슷한 추가 작업이 있을 수 있다 | `HashAggregate` 뒤 `Sort`가 붙는지 본다 |
| "`ORDER BY status`와 `ORDER BY COUNT(*)`는 비슷하다" | 하나는 원래 컬럼, 다른 하나는 집계 후 계산값이다 | 정렬 기준이 원본 컬럼인지 계산 결과인지 먼저 구분한다 |

## 다음으로 어디를 보면 좋은가

- `Using temporary`, `Using filesort` 자체가 아직 낯설면 [MySQL `EXPLAIN`에서 `Using temporary`가 보여요](./mysql-explain-using-temporary-beginner-card.md)
- `GROUP BY`, `HAVING` 기본기부터 다시 잡고 싶으면 [SQL 집계 함수와 GROUP BY 기초](./sql-aggregate-groupby-basics.md)
- PostgreSQL에서 `Sort`, `HashAggregate`, `GroupAggregate` 이름이 낯설면 [PostgreSQL plan node 한 장 카드](./postgresql-plan-node-mini-card.md), [PostgreSQL `EXPLAIN ANALYZE` 용어 미니 브리지](./postgresql-explain-analyze-terms-mini-bridge.md)
- 인덱스 컬럼 순서와 정렬 축을 더 구체적으로 보고 싶으면 [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)

## 한 줄 정리

`GROUP BY`와 `ORDER BY`의 기준이 다르면, MySQL이든 PostgreSQL이든 보통 "먼저 집계하고 나중에 다시 정렬"하는 단계가 붙기 때문에 인덱스만으로 한 번에 끝나지 않는 경우가 많다.
