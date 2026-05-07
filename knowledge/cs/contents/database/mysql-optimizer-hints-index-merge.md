---
schema_version: 3
title: MySQL Optimizer Hints and Index Merge
concept_id: database/mysql-optimizer-hints-index-merge
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- mysql-optimizer
- optimizer-hints
- index-merge
- plan-stability
aliases:
- MySQL optimizer hints
- USE INDEX
- FORCE INDEX
- IGNORE INDEX
- index merge
- index_merge_intersect
- index_merge_union
- optimizer switch
- MySQL 힌트 언제 쓰나요
- index merge가 느려요
symptoms:
- MySQL optimizer가 index_merge plan을 골랐는데 rows와 filesort 비용이 커져 query latency가 튀고 있어
- FORCE INDEX나 USE INDEX로 급한 장애를 넘겼지만 데이터 분포 변화 뒤 힌트가 기술 부채가 되었어
- 통계 왜곡, stale stats, join order drift 때문에 plan을 힌트로 좁힐지 ANALYZE와 index 재설계를 할지 판단해야 해
intents:
- deep_dive
- troubleshooting
prerequisites:
- database/index-and-explain
- database/query-tuning-checklist
next_docs:
- database/optimizer-trace-reading
- database/optimizer-switch-plan-stability-invisible-indexes
- database/statistics-histograms-cardinality-estimation
linked_paths:
- contents/database/index-and-explain.md
- contents/database/query-tuning-checklist.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/sql-joins-and-query-order.md
- contents/database/optimizer-trace-reading.md
- contents/database/optimizer-switch-plan-stability-invisible-indexes.md
- contents/database/statistics-histograms-cardinality-estimation.md
confusable_with:
- database/optimizer-trace-reading
- database/optimizer-switch-plan-stability-invisible-indexes
- database/statistics-histograms-cardinality-estimation
forbidden_neighbors: []
expected_queries:
- MySQL index_merge plan이 언제 도움이 되고 언제 느려지는지 설명해줘
- FORCE INDEX를 임시 조치로 쓸 때 어떤 운영 부채와 재검증 기준을 남겨야 해?
- optimizer hint를 넣기 전에 ANALYZE TABLE이나 통계 왜곡을 먼저 봐야 하는 이유가 뭐야?
- USE INDEX, FORCE INDEX, IGNORE INDEX의 차이를 plan stability 관점에서 알려줘
- index_merge_intersection이 composite index보다 느릴 수 있는 상황을 예시로 설명해줘
contextual_chunk_prefix: |
  이 문서는 MySQL optimizer hints, FORCE INDEX, USE INDEX, IGNORE INDEX, index_merge plan을 통계 왜곡과 plan drift 관점에서 다루는 advanced deep dive다.
  index merge가 느림, 힌트 언제 쓰나요, optimizer switch, stale stats 질문이 본 문서에 매핑된다.
---
# MySQL Optimizer Hints and Index Merge

> 한 줄 요약: 옵티마이저는 똑똑하지만 완벽하지 않다. 잘못된 실행 계획을 읽고, 필요할 때만 힌트로 좁히는 감각이 중요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인덱스와 실행 계획](./index-and-explain.md)
> - [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
> - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
> - [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)

---

> retrieval-anchor-keywords:
> - MySQL optimizer hints
> - USE INDEX
> - FORCE INDEX
> - IGNORE INDEX
> - index merge
> - index_merge_intersect
> - index_merge_union
> - optimizer switch

## 핵심 개념

MySQL 옵티마이저는 통계와 비용 모델을 바탕으로 실행 계획을 고른다. 대부분의 경우 이 선택이 맞지만, 항상 최선은 아니다.

이 문서에서 다룰 핵심은 세 가지다.

1. 옵티마이저가 왜 잘못된 계획을 고르는가
2. `index_merge`가 언제 유용하고 언제 독이 되는가
3. 힌트를 언제 쓰고 언제 쓰지 말아야 하는가

힌트는 정답이 아니라 **의도를 강제로 드러내는 도구**다. 기본 설계를 대신하는 수단이 아니다.

---

## 깊이 들어가기

### 1. 옵티마이저는 통계에 의존한다

실행 계획은 현재 데이터 분포를 정확히 안다는 가정 위에서 만들어진다. 그런데 실제 운영에서는 다음이 자주 어긋난다.

- 테이블 분포가 급격히 바뀜
- 통계가 오래됨
- 특정 조건의 선택도가 예상과 다름
- 조인 순서가 데이터 성장 후에 역전됨

이 때문에 처음엔 빠르던 쿼리가, 데이터가 커진 뒤 갑자기 느려질 수 있다.

### 2. `index_merge`는 여러 인덱스를 합치는 전략이다

MySQL은 `OR` 조건이나 일부 교집합 조건에서 여러 인덱스를 합쳐 사용할 수 있다.

대표적인 형태는 다음과 같다.

- `union`
- `sort_union`
- `intersection`

예를 들어 아래 쿼리가 있다고 하자.

```sql
SELECT id, status, created_at
FROM orders
WHERE user_id = 1001 OR status = 'PAID';
```

인덱스가 아래처럼 분리되어 있다면:

```sql
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
```

옵티마이저는 `index_merge`를 고려할 수 있다.

```text
type: index_merge
key: idx_orders_user_id,idx_orders_status
Extra: Using union(idx_orders_user_id,idx_orders_status); Using where
```

이 방식은 종종 좋지만, 항상 좋은 것은 아니다. 두 인덱스에서 찾은 결과를 합치는 비용이 커지면 풀스캔보다 느려질 수 있다.

### 3. 힌트는 계획을 좁히는 장치다

MySQL에는 두 종류의 힌트 감각이 있다.

- 테이블/인덱스 힌트: `USE INDEX`, `FORCE INDEX`, `IGNORE INDEX`
- 옵티마이저 힌트: `/*+ ... */` 형태의 주석 힌트

예:

```sql
SELECT /*+ INDEX(o idx_orders_user_status_created_at) */
       o.id, o.status, o.created_at
FROM orders o
WHERE o.user_id = 1001
  AND o.status = 'PAID'
ORDER BY o.created_at DESC
LIMIT 20;
```

또는 특정 인덱스를 강제할 수 있다.

```sql
SELECT id, status, created_at
FROM orders FORCE INDEX (idx_orders_user_status_created_at)
WHERE user_id = 1001
  AND status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

하지만 힌트는 보수적으로 써야 한다. 데이터 분포가 다시 바뀌면 힌트가 오히려 발목을 잡는다.

### 4. `ANALYZE TABLE`은 종종 첫 번째 대응이다

계획이 이상하면 무조건 힌트부터 넣기보다, 통계 갱신 여부를 먼저 본다.

```sql
ANALYZE TABLE orders;
```

통계가 오래된 상태였다면, 힌트 없이도 계획이 좋아질 수 있다.

---

## 실전 시나리오

### 시나리오 1: `index_merge`가 오히려 느려짐

운영에서 아래 쿼리가 있다고 하자.

```sql
SELECT *
FROM orders
WHERE user_id = 1001 OR status = 'FAILED';
```

데이터가 커지면서 `status='FAILED'`가 전체의 18%를 차지하게 됐다. 그러면 `index_merge`로 많이 긁어오느니 차라리 한쪽 인덱스만 타는 편이 나을 수 있다.

이 경우의 교훈은 이렇다.

- 조건문이 인덱스 가능하다고 해서 항상 빠른 것은 아니다
- `OR`는 index merge를 유도하지만, 결과 집합이 크면 비용이 폭증한다
- 부분집합이 큰 컬럼은 힌트로 억지 제어하지 말고 쿼리 자체를 다시 설계해야 한다

### 시나리오 2: 운영자가 임시 힌트로 장애를 넘김

새 배포 후 조인 순서가 바뀌어 응답 시간이 40ms에서 3s로 튀었다. 원인은 통계 왜곡과 join order 선택이었다.

이때 임시 조치로는 힌트를 써서 회복시킬 수 있다.

하지만 장기적으로는:

- 통계 갱신
- 인덱스 재설계
- 조인 쿼리 구조 수정

이 필요하다.

### 시나리오 3: `FORCE INDEX`가 새 데이터 분포에서 독이 됨

처음에는 `FORCE INDEX`로 빠르게 해결했지만, 나중에 데이터가 바뀌며 그 인덱스가 더 이상 최선이 아니게 된다. 그 순간 힌트는 기술 부채가 된다.

---

## 코드로 보기

### 테이블 예시

```sql
CREATE TABLE orders (
  id BIGINT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL,
  total_amount DECIMAL(12,2) NOT NULL,
  INDEX idx_orders_user_id (user_id),
  INDEX idx_orders_status (status),
  INDEX idx_orders_user_status_created_at (user_id, status, created_at)
);
```

### 실행 계획 비교

```sql
EXPLAIN
SELECT id, status, created_at
FROM orders
WHERE user_id = 1001
  AND status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

잘못된 계획:

```text
type: index_merge
key: idx_orders_user_id,idx_orders_status
rows: 18340
Extra: Using intersection(...); Using filesort
```

개선된 계획:

```text
type: range
key: idx_orders_user_status_created_at
rows: 20
Extra: Using where; Using index
```

### 강제 힌트 예시

```sql
SELECT /*+ INDEX(o idx_orders_user_status_created_at) */
       o.id, o.status, o.created_at
FROM orders o
WHERE o.user_id = 1001
  AND o.status = 'PAID'
ORDER BY o.created_at DESC
LIMIT 20;
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 옵티마이저 기본 선택 | 유지보수가 쉽다 | 통계가 틀리면 오판할 수 있다 | 일반적인 운영 쿼리 |
| `index_merge` | `OR` 조건을 자연스럽게 처리한다 | 결과 집합이 크면 느릴 수 있다 | 조건 분산이 작을 때 |
| `FORCE INDEX` | 계획을 즉시 고정할 수 있다 | 데이터 분포 변화에 취약하다 | 장애를 임시로 우회할 때 |
| 쿼리/인덱스 재설계 | 장기적으로 안정적이다 | 시간과 검증이 필요하다 | 반복되는 느린 쿼리 |

핵심 기준은 간단하다. **힌트는 응급처치, 설계는 치료다.**

---

## 꼬리질문

> Q: index merge가 있으면 복합 인덱스는 필요 없나요?
> 의도: index_merge와 compound index의 역할 구분 여부 확인
> 핵심: index_merge는 임시 우회일 뿐, 정확한 접근 경로는 복합 인덱스가 더 낫다

> Q: FORCE INDEX를 영구 해법으로 쓰면 왜 위험한가요?
> 의도: 운영 변화에 따른 계획 붕괴 인식 여부 확인
> 핵심: 데이터 분포가 바뀌면 고정 계획이 오히려 병목이 된다

> Q: 통계 갱신과 힌트 중 무엇을 먼저 보나요?
> 의도: 문제 진단 순서 확인
> 핵심: 통계와 실행 계획을 먼저 확인하고, 힌트는 마지막 수단으로 둔다

---

## 한 줄 정리

옵티마이저 힌트는 계획을 고정하는 수단이 아니라, 잘못된 선택을 임시로 좁히는 도구다. index merge는 유용하지만 복합 인덱스를 대체하지 못한다.
