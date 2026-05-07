---
schema_version: 3
title: Index Condition Pushdown, Filesort, Temporary Table
concept_id: database/index-condition-pushdown-filesort-temporary-table
canonical: true
category: database
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- explain-extra-icp-filesort-temporary
- key-used-but-still-slow
- mysql-extra-symptom-route
aliases:
- index condition pushdown
- ICP
- filesort
- temporary table
- using temporary
- using filesort
- using index condition
- key used but using filesort
- key used but using temporary
- mysql explain extra
symptoms:
- MySQL EXPLAIN에서 key는 잡혔는데 Extra에 Using filesort나 Using temporary가 남아 있어
- Using index condition이 보이지만 ICP가 기대만큼 row fetch를 줄이지 못하는 것 같아
- GROUP BY, DISTINCT, ORDER BY 때문에 temporary/filesort/spill 신호를 어디 문서로 이어갈지 모르겠어
intents:
- troubleshooting
- deep_dive
prerequisites:
- database/index-and-explain
- database/covering-index-composite-ordering
next_docs:
- database/sort-buffer-temp-table-spill
- database/temp-table-engine-spill-behavior
- database/mysql-optimizer-hints-index-merge
- database/slow-query-analysis-playbook
linked_paths:
- contents/database/index-and-explain.md
- contents/database/covering-index-composite-ordering.md
- contents/database/query-tuning-checklist.md
- contents/database/sort-buffer-temp-table-spill.md
- contents/database/temp-table-engine-choice-spill-behavior.md
- contents/database/mysql-optimizer-hints-index-merge.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/mysql-explain-using-temporary-beginner-card.md
- contents/database/statistics-histograms-cardinality-estimation.md
confusable_with:
- database/index-and-explain
- database/covering-index-composite-ordering
- database/query-tuning-checklist
forbidden_neighbors: []
expected_queries:
- MySQL EXPLAIN에서 key는 잡혔는데 Using filesort나 Using temporary가 남으면 무엇을 봐야 해?
- Index Condition Pushdown은 인덱스 단계에서 어떤 조건을 먼저 걸러내는 최적화야?
- Using temporary와 Using filesort는 GROUP BY, DISTINCT, ORDER BY에서 왜 같이 보일 수 있어?
- rows 추정은 괜찮은데 Extra가 나쁘면 어떤 symptom route로 가야 해?
- 복합 인덱스가 있는데 ORDER BY가 인덱스 순서로 끝나지 못하는 이유를 설명해줘
contextual_chunk_prefix: |
  이 문서는 MySQL EXPLAIN Extra의 Using index condition, Using filesort, Using temporary 신호를 보고 key는 잡혔지만 여전히 느린 쿼리를 라우팅하는 advanced symptom router다.
  index condition pushdown, Using filesort, Using temporary, key used but still slow 같은 자연어 질문이 본 문서에 매핑된다.
---
# Index Condition Pushdown, Filesort, Temporary Table

> 한 줄 요약: 인덱스가 있어도 쿼리는 빠르지 않을 수 있다. MySQL이 어떤 조건을 인덱스 단계에서 걸러내고, 언제 정렬과 임시 테이블을 만들며, 왜 그 선택이 느려지는지를 읽을 수 있어야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인덱스와 실행 계획](./index-and-explain.md)
> - [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
> - [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
> - [Sort Buffer, Temporary Table, and Spill Behavior](./sort-buffer-temp-table-spill.md)
> - [Temporary Table Engine Choice and Spill Behavior](./temp-table-engine-choice-spill-behavior.md)
> - [MySQL Optimizer Hints and Index Merge](./mysql-optimizer-hints-index-merge.md)
> - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
>
> retrieval-anchor-keywords:
> - index condition pushdown
> - ICP
> - filesort
> - temporary table
> - using temporary
> - using filesort
> - using temporary using filesort
> - covering index
> - optimizer trace
> - EXPLAIN extra
> - EXPLAIN ANALYZE
> - order by limit slow
> - group by using temporary
> - mysql explain extra using filesort
> - mysql explain extra using temporary
> - composite index but filesort
> - index exists but order by slow
> - index exists but group by slow
> - icp not applied
> - using index condition
> - using index condition using where
> - key used but using filesort
> - key used but using temporary
> - explain extra using index condition
> - explain extra using filesort
> - explain extra using temporary
> - rows estimate looks fine but extra is bad
> - group by distinct temporary table
> - sort elimination failed
> - explain symptom route filesort temporary
> - 인덱스 있는데 정렬 느림
> - 복합 인덱스인데 filesort
> - key는 잡혔는데 filesort
> - key는 잡혔는데 temporary
> - extra 컬럼 해석
> - explain extra filesort temporary
> - rows는 괜찮은데 extra가 나쁨
> - using temporary 왜 생김
> - mysql 실행 계획 extra 해석

## 이 문서 다음에 보면 좋은 문서

- `Extra` 컬럼을 더 기본부터 읽고 싶으면 [인덱스와 실행 계획](./index-and-explain.md)으로 먼저 내려가서 `type`, `rows`, `key`, `Extra`를 같이 본다.
- `ORDER BY`, 커버링 인덱스, 복합 인덱스 순서가 왜 filesort를 줄이는지 이어서 보려면 [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)와 [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)가 바로 붙는다.
- `Using filesort`, `Using temporary`가 실제로 memory에서 끝나는지 disk spill로 번졌는지까지 보고 싶다면 [Sort Buffer, Temporary Table, and Spill Behavior](./sort-buffer-temp-table-spill.md), [Temporary Table Engine Choice and Spill Behavior](./temp-table-engine-choice-spill-behavior.md)를 이어 읽는다.
- 옵티마이저가 이상한 인덱스를 고르는 상황까지 들어가려면 [MySQL Optimizer Hints and Index Merge](./mysql-optimizer-hints-index-merge.md)를, 실제 장애 대응 순서를 먼저 잡아야 하면 [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)을 본다.

## 이 문서가 맡는 EXPLAIN 범위

이 문서는 `EXPLAIN`에서 접근 경로 자체보다 `Extra` 신호가 먼저 눈에 들어오는 상황을 맡는다.
즉 "`key`는 잡혔는데 왜 여전히 느린가"를 설명하는 entry다.

| 보이는 신호 | 여기서 바로 보는 것 | 먼저 돌아갈 문서 |
| --- | --- | --- |
| `key`는 잡혔는데 `Extra`에 `Using filesort`가 남음 | 정렬이 인덱스 순서로 끝나지 않는 이유, `ORDER BY`와 복합 인덱스 순서 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| `Using temporary` 또는 `Using temporary; Using filesort`가 보임 | `GROUP BY`, `DISTINCT`, 조인 후 재배열 때문에 임시 테이블이 생기는 이유 | [쿼리 튜닝 체크리스트](./query-tuning-checklist.md), [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |
| `Using index condition`이 보이거나 ICP가 기대보다 약함 | 인덱스 단계 predicate pushdown, 선행 컬럼 선택도, 조건식 모양 | [인덱스와 실행 계획](./index-and-explain.md), [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) |
| `type = ALL`, `key = NULL`, `possible_keys`도 빈약함 | 이 문서 범위보다 앞단의 접근 경로 문제 | [인덱스와 실행 계획](./index-and-explain.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| `rows` 추정치가 실제와 계속 다르거나 배포 후 plan drift가 남 | 통계와 cardinality estimation 문제 | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) |

## 핵심 개념

이 문서는 MySQL 실행 계획에서 자주 보이는 세 가지 신호를 같이 읽는 방법을 다룬다.

- `Index Condition Pushdown (ICP)`은 인덱스를 읽는 중에 가능한 조건을 먼저 걸러내는 최적화다.
- `Using filesort`는 MySQL이 인덱스 순서만으로 정렬을 끝내지 못하고 별도 정렬 작업을 수행한다는 뜻이다.
- `Using temporary`는 중간 결과를 임시 테이블에 담아야 한다는 뜻이다.

이 세 개는 독립된 문제가 아니라 자주 같이 나타난다.  
예를 들어 복합 인덱스가 있어도:

- 조건이 인덱스 앞쪽 컬럼에 잘 안 맞으면 `ICP`가 약해지고
- `ORDER BY`가 인덱스 순서와 어긋나면 `filesort`가 생기고
- `GROUP BY`, `DISTINCT`, 파생 테이블, 복잡한 조인이 있으면 `temporary`가 추가된다

즉 성능 문제를 볼 때는 “인덱스가 있냐 없냐”보다 “인덱스를 얼마나 끝까지 활용하느냐”를 봐야 한다.

## 깊이 들어가기

### 1. Index Condition Pushdown은 무엇인가

ICP는 **스토리지 엔진이 인덱스를 읽는 중에 조건을 더 빨리 걸러내는 방식**이다.

보통 인덱스 레코드를 읽은 뒤 서버 레이어로 올려서 조건을 판단하지만, ICP가 적용되면 가능한 조건을 인덱스 단계에서 먼저 검사한다.  
이렇게 하면 테이블 본문까지 덜 올라가도 되므로 랜덤 I/O와 불필요한 row fetch를 줄일 수 있다.

ICP가 잘 먹는 상황:

- 복합 인덱스의 선행 컬럼으로 범위를 좁힌 뒤 뒤쪽 컬럼 조건을 추가로 거를 때
- `WHERE a = ? AND b LIKE 'prefix%'`처럼 인덱스와 잘 맞는 조건이 있을 때

ICP가 약한 상황:

- 함수가 걸린 조건
- 인덱스와 무관한 계산식
- 선행 컬럼이 비어 있어서 인덱스 탐색 자체가 넓어질 때

### 2. filesort는 “정렬 알고리즘”보다 “정렬 경로”를 봐야 한다

`Using filesort`는 이름 때문에 디스크 정렬처럼 느껴지지만, 실제 의미는 **인덱스 순서로 바로 정렬하지 못해서 별도 정렬 로직을 쓴다**는 뜻이다.

중요한 포인트는 다음과 같다.

- 메모리 안에서 끝날 수도 있고, 큰 결과면 디스크로 spill 될 수도 있다
- 인덱스로 정렬 가능하면 filesort를 피할 수 있다
- `ORDER BY` 컬럼 순서, 방향, `WHERE` 조건과의 조합이 핵심이다

예를 들어 아래는 인덱스와 잘 맞을 수 있다.

```sql
SELECT id, user_id, created_at
FROM orders
WHERE user_id = 1001
ORDER BY created_at DESC
LIMIT 20;
```

반대로 아래는 filesort가 생기기 쉽다.

```sql
SELECT id, user_id, created_at
FROM orders
WHERE status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

status만으로는 created_at 순서를 인덱스 그대로 유지하기 어렵기 때문이다.

### 3. Using temporary는 언제 생기는가

`Using temporary`는 MySQL이 중간 결과를 임시 테이블에 담는다는 뜻이다.

대표적인 원인은 다음과 같다.

- `GROUP BY`가 인덱스 순서와 맞지 않을 때
- `DISTINCT`가 인덱스로 바로 처리되지 않을 때
- 정렬과 집계가 함께 필요할 때
- 조인 후 중간 결과를 다시 재배열해야 할 때

임시 테이블은 항상 나쁜 것은 아니지만, 결과가 커지면 메모리 사용과 디스크 쓰기 비용이 커진다.  
그래서 `Using temporary`는 “무조건 제거”보다 “왜 생겼는지 확인”이 더 중요하다.

### 4. 옵티마이저는 왜 이런 선택을 하는가

MySQL 옵티마이저는 통계 정보와 비용 모델을 바탕으로 가장 싸다고 판단되는 계획을 고른다.  
그런데 데이터 분포가 달라지거나 통계가 오래되면 다음 같은 일이 생긴다.

- 인덱스는 있어도 `range` 대신 넓은 `index scan`을 고른다
- 정렬 비용을 과소평가해서 `filesort`가 커진다
- 집계 결과가 많아져도 `temporary` 비용을 낮게 본다

즉 실행 계획은 “문법의 결과”가 아니라 “현재 데이터와 통계의 추정치”다.  
그래서 `ANALYZE TABLE`, 인덱스 재설계, 쿼리 재작성, 힌트 사용을 순서대로 검토해야 한다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 도움이 되는 키워드는 아래다.

- `ICP`
- `Index Condition Pushdown`
- `Using filesort`
- `Using temporary`
- `EXPLAIN Extra`
- `ORDER BY filesort`
- `GROUP BY temporary table`
- `MySQL optimizer cost`
- `EXPLAIN ANALYZE`

## 실전 시나리오

### 시나리오 1: 인덱스가 있는데도 목록 조회가 느리다

증상:

- `WHERE user_id = ?`는 빠른데
- `ORDER BY created_at DESC LIMIT 20`를 붙이면 느려진다

원인 후보:

- 인덱스 컬럼 순서가 `user_id, created_at`가 아님
- 정렬 컬럼 방향이 인덱스와 맞지 않음
- 결과 집합이 너무 커서 filesort 비용이 커짐

보는 순서:

1. `EXPLAIN`에서 `key`, `rows`, `Extra`를 본다
2. `Using filesort`가 있는지 확인한다
3. 가능하면 `(user_id, created_at)` 복합 인덱스로 바꿔본다

### 시나리오 2: 그룹핑 쿼리가 갑자기 무거워졌다

증상:

- `GROUP BY status`가 있는 집계가 느려짐
- `Using temporary`가 보임

원인 후보:

- 그룹 기준과 인덱스 순서가 안 맞음
- `DISTINCT`와 `ORDER BY`가 동시에 들어감
- 집계 전 중간 row 수가 너무 큼

해결 방향:

- 집계 전에 필터를 더 강하게 건다
- 그룹 기준과 맞는 복합 인덱스를 검토한다
- 정말 필요한 컬럼만 집계한다

### 시나리오 3: 복합 인덱스가 있는데도 ICP가 잘 안 보인다

증상:

- 복합 인덱스는 존재하지만 `Extra`가 기대만큼 좋지 않다

원인 후보:

- 선행 컬럼이 선택도를 충분히 못 줄인다
- 후행 조건이 함수나 변환 때문에 인덱스 단계에서 못 걸러진다
- 옵티마이저가 다른 경로가 더 싸다고 판단한다

이때는 인덱스를 더 늘리기보다, 조건식을 먼저 손보는 게 더 싸다.

## 코드로 보기

### 1. 기본 테이블 예시

```sql
CREATE TABLE orders (
  id BIGINT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  INDEX idx_orders_user_created_at (user_id, created_at),
  INDEX idx_orders_status_created_at (status, created_at)
);
```

### 2. ICP가 기대되는 형태

```sql
EXPLAIN
SELECT id, user_id, status, created_at
FROM orders
WHERE user_id = 1001
  AND created_at >= '2026-01-01'
  AND status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

예상 포인트:

- `key`: `idx_orders_user_created_at`
- `Extra`: `Using index condition; Using where`

이 경우 MySQL은 인덱스를 읽는 도중에 걸릴 수 있는 조건을 최대한 먼저 걸러낸다.

### 3. filesort가 나타나는 형태

```sql
EXPLAIN
SELECT id, user_id, status, created_at
FROM orders
WHERE status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

예상 포인트:

- `Extra`: `Using filesort`

status만으로는 created_at 정렬을 그대로 만족시키기 어렵기 때문이다.

### 4. temporary table이 나타나는 형태

```sql
EXPLAIN
SELECT status, COUNT(*)
FROM orders
GROUP BY status
ORDER BY COUNT(*) DESC;
```

예상 포인트:

- `Extra`: `Using temporary; Using filesort`

집계 결과를 묶고 다시 정렬해야 해서 임시 테이블과 별도 정렬이 같이 나올 수 있다.

### 5. EXPLAIN ANALYZE로 실제 확인

```sql
EXPLAIN ANALYZE
SELECT id, user_id, status, created_at
FROM orders
WHERE user_id = 1001
  AND created_at >= '2026-01-01'
ORDER BY created_at DESC
LIMIT 20;
```

여기서는 추정 row와 실제 row, 실행 시간, 정렬 단계의 비용 차이를 함께 본다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| ICP를 잘 타는 복합 인덱스 | row fetch를 줄인다 | 인덱스 설계가 까다롭다 | 조건이 많고 조회가 자주 반복될 때 |
| filesort 허용 | 쿼리 구조를 단순하게 유지한다 | 결과가 크면 느리다 | 결과가 작거나 일회성 조회일 때 |
| temporary table 허용 | 복잡한 집계/정렬을 쉽게 처리한다 | 메모리/디스크 비용이 든다 | GROUP BY, DISTINCT, 파생 결과가 필요한 경우 |
| 인덱스로 정렬 해결 | 정렬 비용이 줄어든다 | 복합 인덱스가 커지고 쓰기 비용이 늘 수 있다 | ORDER BY가 핵심 경로일 때 |
| 힌트 사용 | 당장 계획을 좁힐 수 있다 | 데이터 분포 변화에 취약하다 | 임시 완화책이 필요할 때 |
| 쿼리 재작성 | 근본 원인을 줄일 수 있다 | 코드 영향 범위가 있다 | 반복적으로 느린 쿼리일 때 |

핵심은 `filesort`와 `temporary`를 무조건 없애는 것이 아니다.  
결과가 작고 빈도가 낮으면 허용할 수 있고, 핵심 경로라면 인덱스로 우회하는 편이 낫다.

## 꼬리질문

> Q: ICP가 있으면 무조건 빠른가요?
> 의도: 인덱스 최적화의 한계를 아는지 확인
> 핵심: 아니다. 조건이 인덱스에 잘 맞아야 하고, 선택도와 결과 크기가 중요하다.

> Q: filesort가 나오면 항상 문제인가요?
> 의도: Extra 문자열을 절대 진리로 보지 않는지 확인
> 핵심: 아니다. 결과가 작으면 감당 가능하지만, 핵심 경로면 정렬 경로를 다시 설계해야 한다.

> Q: `Using temporary`는 왜 생기나요?
> 의도: 집계/정렬/중간 결과의 의미 이해 확인
> 핵심: GROUP BY, DISTINCT, 복잡한 조인, 파생 결과를 중간에 보관해야 할 때 생긴다.

> Q: 인덱스를 추가했는데 `Using filesort`가 그대로인 이유는?
> 의도: 복합 인덱스와 정렬 조건의 관계 이해 확인
> 핵심: ORDER BY 컬럼 순서, 방향, WHERE 조건과 인덱스 순서가 맞지 않으면 정렬을 인덱스로 끝내지 못한다.

> Q: `EXPLAIN`만 보면 충분한가요?
> 의도: 실제 실행과 추정의 차이를 아는지 확인
> 핵심: 아니다. 가능하면 `EXPLAIN ANALYZE`와 실제 운영 데이터도 같이 봐야 한다.

## 한 줄 정리

ICP는 인덱스 단계에서 먼저 거를 수 있는 조건을 최대한 밀어 넣는 최적화이고, filesort와 temporary table은 MySQL이 인덱스만으로 정렬·집계를 끝내지 못할 때 쓰는 우회 경로다. 그래서 성능은 “인덱스가 있냐”보다 “정렬, 집계, 조건이 인덱스와 얼마나 잘 맞느냐”로 봐야 한다.
