# Hash Join, Materialization, Join Buffer

> 한 줄 요약: 인덱스가 없거나 재사용이 많을 때 옵티마이저는 nested loop만 고집하지 않고, 해시와 물질화를 써서 반복 비용을 줄인다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: hash join, materialization, join buffer, block nested loop, subquery materialization, optimizer_switch, EXPLAIN ANALYZE, derived table, temporary table

## 핵심 개념

- 관련 문서:
  - [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
  - [MySQL Optimizer Hints and Index Merge](./mysql-optimizer-hints-index-merge.md)
  - [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md)
  - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)

MySQL 실행 계획에서 `Using join buffer (hash join)`이나 `materialization`이 보이면,  
옵티마이저가 "인덱스로 한 건씩 찌르는 방식"보다 "한 번 만들어 놓고 많이 재사용하는 방식"이 낫다고 판단했다는 뜻이다.

이 둘의 핵심 차이는 다음과 같다.

- hash join: 한쪽 입력을 해시 테이블로 만들고 다른 쪽을 probe한다
- materialization: 서브쿼리나 derived table 결과를 임시 구조로 고정해 재사용한다

## 깊이 들어가기

### 1. nested loop join만으로는 부족하다

전통적인 조인은 바깥 테이블의 각 row마다 안쪽 테이블을 찾는 nested loop에 의존한다.  
안쪽 테이블에 좋은 인덱스가 있으면 빠르지만, 없으면 반복 비용이 폭발한다.

이때 옵티마이저는 다른 경로를 본다.

- 인덱스 기반 반복 조회
- block nested loop
- hash join
- materialization

### 2. hash join은 "큰 테이블 조인"이 아니라 "적절한 조인"이다

hash join은 보통 equi-join에서 유리하다.  
작은 입력을 메모리에 해시 테이블로 만들고, 큰 입력을 probe한다.

장점:

- 반복 인덱스 lookup을 줄일 수 있다
- 인덱스가 약한 조인에서 유리할 수 있다

주의점:

- 메모리를 쓴다
- 너무 크면 spill 가능성이 있다
- 범위 조인이나 비등가 조인에는 맞지 않을 수 있다

### 3. materialization은 중간 결과를 "한 번만" 만들기다

서브쿼리나 derived table을 매번 다시 계산하면 비용이 커진다.  
그래서 옵티마이저는 필요한 경우 결과를 임시 테이블처럼 만들어 재사용한다.

예를 들면:

- `IN (SELECT ...)`
- 반복 참조되는 derived table
- 비용상 미리 만들어 두는 편이 나을 때

이건 단순 임시 테이블이 아니라, **재계산 대신 저장**하는 전략이다.

### 4. join buffer는 block nested loop와 hash join의 기반 감각이다

`Using join buffer`는 인덱스만으로 처리하지 않고 join buffer를 쓴다는 신호다.  
MySQL 버전에 따라 block nested loop나 hash join 식으로 드러날 수 있다.

중요한 것은 이름보다도,

- 인덱스 lookup 반복을 줄이려는가
- 메모리 안에서 join 후보를 모아두려는가
- temporary / buffer 사용이 커졌는가

를 읽는 것이다.

### 5. optimizer_switch로 비교 실험을 할 수 있다

예상 계획이 이상하면 힌트나 스위치로 비교해 볼 수 있다.

- `materialization=on/off`
- `subquery_materialization_cost_based=on`
- join 관련 힌트 또는 인덱스 힌트

다만 실험은 진단용이어야 하고, 영구 해법이어선 안 된다.

### 6. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `hash join`
- `materialization`
- `join buffer`
- `block nested loop`
- `subquery materialization`
- `optimizer_switch`
- `EXPLAIN ANALYZE`

## 실전 시나리오

### 시나리오 1. 조인 컬럼에 인덱스가 없는데도 쿼리를 살려야 한다

레거시 테이블을 바로 고치기 어렵다면 hash join이나 join buffer 전략이 임시로 도움이 될 수 있다.  
이때는 인덱스를 추가할지, 쿼리 구조를 바꿀지, 메모리 기반 조인을 받아들일지 판단해야 한다.

### 시나리오 2. `IN (SELECT ...)`이 느려졌다

서브쿼리를 매번 다시 돌리는 것보다 materialization이 나을 수 있다.  
특히 같은 결과를 여러 번 재사용하는 구조라면 materialization이 효과적이다.

### 시나리오 3. join plan이 바뀌면서 메모리 사용이 늘었다

hash join은 빨라질 수 있지만, 메모리와 spill 비용도 같이 본다.  
그래서 "빠르다"만 보고 끝내면 안 되고, `rows`, `Extra`, 실제 실행 시간을 같이 봐야 한다.

## 코드로 보기

### hash join과 materialization 관찰

```sql
EXPLAIN ANALYZE
SELECT e.id, d.dept_name
FROM employees e
JOIN departments d
  ON e.dept_id = d.id
WHERE e.hire_date >= '2024-01-01';
```

실행 계획에서 볼 수 있는 신호:

- `Using join buffer (hash join)`
- `materialize`
- `Using temporary`

### 서브쿼리 materialization 비교

```sql
EXPLAIN
SELECT *
FROM orders o
WHERE o.user_id IN (
  SELECT u.id
  FROM users u
  WHERE u.status = 'ACTIVE'
);
```

비교 실험:

```sql
SET optimizer_switch='materialization=OFF';
-- 다시 EXPLAIN
SET optimizer_switch='materialization=ON';
```

### 조인 버퍼 감각 확인

```sql
SELECT /*+ SET_VAR(join_buffer_size=262144) */
       e.id, d.dept_name
FROM employees e
JOIN departments d
  ON e.dept_id = d.id;
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| nested loop + 인덱스 | 단순하고 예측 가능하다 | 인덱스가 없으면 급격히 느려진다 | 조인 키 인덱스가 좋을 때 |
| hash join | 반복 lookup을 줄인다 | 메모리와 spill을 쓴다 | equi-join, 인덱스가 약할 때 |
| materialization | 재계산을 피한다 | 임시 저장 비용이 있다 | 서브쿼리/derived table 재사용 시 |
| 힌트로 강제 | 진단이 쉽다 | 데이터 분포가 바뀌면 독이 된다 | 임시 분석 및 긴급 조치 |

핵심은 특정 알고리즘을 선호하는 게 아니라, **반복 계산을 줄이는 방향이 현재 데이터 분포에서 이득인지**를 보는 것이다.

## 꼬리질문

> Q: hash join은 언제 가장 잘 맞나요?
> 의도: 조인 알고리즘 선택 기준 이해 확인
> 핵심: 인덱스가 약한 equi-join에서 반복 lookup을 줄일 때 유리하다

> Q: materialization은 왜 느려질 수도 있나요?
> 의도: 임시 저장의 비용 이해 여부 확인
> 핵심: 결과를 저장하는 비용과 메모리/디스크 spill이 생길 수 있다

> Q: join buffer가 보이면 무조건 나쁜 건가요?
> 의도: 실행 계획 신호를 절대화하지 않는지 확인
> 핵심: 나쁜 신호가 아니라, 옵티마이저가 다른 실행 전략을 택했다는 뜻이다

## 한 줄 정리

hash join과 materialization은 인덱스 반복 조회가 비싸질 때 반복 비용을 줄이는 전략이고, join buffer는 그 선택이 실행되는 메모리 공간이다.
