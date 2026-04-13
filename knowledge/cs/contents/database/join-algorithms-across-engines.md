# Join Algorithms Across Engines: Nested Loop, Hash, and Merge

> 한 줄 요약: 조인은 하나의 정답이 아니라, nested loop는 인덱스 친화형이고 hash는 동등 조인 친화형이며 merge는 정렬 친화형이라는 서로 다른 비용 모델의 선택이다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: nested loop join, hash join, merge join, sort merge join, join algorithm, engine differences, EXPLAIN ANALYZE, sorted inputs

## 핵심 개념

- 관련 문서:
  - [Hash Join, Materialization, Join Buffer](./hash-join-materialization-join-buffer.md)
  - [Semi-Join, LooseScan, FirstMatch, DuplicateWeedout](./semijoin-loosescan-firstmatch-duplicateweedout.md)
  - [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
  - [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)

조인은 "두 테이블을 붙인다"는 같은 문장이지만, 엔진이 붙이는 방식은 다르다.

- nested loop: 바깥 row마다 안쪽을 반복 탐색
- hash join: 한쪽을 해시 테이블로 만들고 다른 쪽을 probe
- merge join: 둘 다 정렬되어 있으면 순서대로 합침

이 차이를 알면 "왜 MySQL은 자꾸 nested loop처럼 보이고, PostgreSQL은 merge join을 고르기도 하는가"를 설명할 수 있다.

## 깊이 들어가기

### 1. nested loop는 왜 오래 살아남았나

nested loop는 단순하고 인덱스와 잘 맞는다.

- outer가 작으면 빠르다
- inner에 좋은 인덱스가 있으면 매우 효율적이다
- 구현이 단순하다

그래서 OLTP에서는 여전히 강력하다.

### 2. hash join은 언제 강한가

hash join은 equi-join에서 특히 강하다.

- 인덱스가 약하거나 없을 때
- 한쪽이 메모리에 들어올 정도로 작을 때
- 반복 lookup을 줄이고 싶을 때

MySQL 8.0의 hash join 설명은 이미 다른 문서에서 다뤘다.  
이 문서는 그보다 merge join과의 감각 차이를 더 강조한다.

### 3. merge join은 왜 정렬 친화형인가

두 입력이 이미 정렬되어 있으면, merge join은 순서대로 앞으로만 가면서 매칭할 수 있다.

유리한 상황:

- 양쪽이 모두 정렬되어 있다
- range join이나 ordering이 중요하다
- 대량 데이터에서 sort 비용을 상쇄할 수 있다

### 4. 엔진마다 주력 알고리즘이 다르다

대부분의 엔진은 역사와 구현 방향이 다르다.

- MySQL: nested loop 중심, 8.0에서 hash join 지원
- PostgreSQL: nested loop, hash join, merge join을 모두 적극적으로 선택
- 엔진마다 실행 계획 신호와 비용 모델이 다르다

그래서 같은 SQL도 엔진이 바뀌면 join 알고리즘이 달라질 수 있다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `nested loop join`
- `hash join`
- `merge join`
- `sort merge join`
- `EXPLAIN ANALYZE`
- `sorted inputs`
- `join algorithm`

## 실전 시나리오

### 시나리오 1. MySQL에서는 nested loop가 자연스럽고 PostgreSQL에서는 merge join이 보인다

양쪽 엔진의 비용 모델이 다르기 때문에 같은 조인이라도 선택이 달라진다.  
이 차이를 "엔진이 다르니까"로 넘기지 말고, 입력 정렬성과 인덱스 유무로 설명할 수 있어야 한다.

### 시나리오 2. 정렬 조건이 붙은 리포트에서 merge join이 빛난다

이미 정렬된 범위 데이터를 붙일 때는 merge join이 매우 자연스럽다.  
반대로 작은 point lookup이면 nested loop가 더 단순하고 빠를 수 있다.

### 시나리오 3. 해시 조인으로 바꾸자 메모리가 늘었다

hash join은 반복 lookup을 줄이지만, 메모리와 spill 비용을 대신 쓴다.  
그래서 "조인 알고리즘 바꾸기"는 항상 메모리/정렬/카디널리티와 함께 봐야 한다.

## 코드로 보기

### nested loop 감각

```sql
EXPLAIN ANALYZE
SELECT o.id, u.name
FROM orders o
JOIN users u ON u.id = o.user_id
WHERE o.created_at >= '2026-04-01';
```

### merge join 감각

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM t1
JOIN t2 ON t1.created_at = t2.created_at
ORDER BY t1.created_at;
```

### hash join 감각

```sql
EXPLAIN ANALYZE
SELECT e.id, d.dept_name
FROM employees e
JOIN departments d
  ON e.dept_id = d.id;
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| nested loop | 단순하고 인덱스 친화적이다 | 큰 outer에서는 반복 비용이 커진다 | OLTP, 작은 outer |
| hash join | 반복 lookup을 줄인다 | 메모리를 쓰고 spill이 가능하다 | equi-join, 인덱스 약함 |
| merge join | 정렬된 입력에 강하다 | 정렬이 안 되어 있으면 비용이 든다 | sorted inputs, range-heavy |

핵심은 조인 알고리즘을 "누가 더 좋다"가 아니라, **입력 형태와 엔진의 비용 모델이 무엇을 선호하는가**로 보는 것이다.

## 꼬리질문

> Q: nested loop가 OLTP에서 여전히 강한 이유는 무엇인가요?
> 의도: 인덱스 친화성과 단순성 이해 여부 확인
> 핵심: 작은 outer와 좋은 inner index에서 매우 효율적이기 때문이다

> Q: merge join은 언제 유리한가요?
> 의도: 정렬된 입력의 가치를 아는지 확인
> 핵심: 이미 정렬된 두 입력을 순서대로 합칠 때다

> Q: 엔진마다 join algorithm 선택이 다른 이유는 무엇인가요?
> 의도: 비용 모델과 구현 차이를 이해하는지 확인
> 핵심: 엔진의 실행 구조와 통계 모델이 다르기 때문이다

## 한 줄 정리

조인 알고리즘은 nested loop, hash, merge가 서로 다른 입력 형태를 최적화하는 선택이고, 엔진은 통계와 정렬 상태를 보고 그중 하나를 고른다.
