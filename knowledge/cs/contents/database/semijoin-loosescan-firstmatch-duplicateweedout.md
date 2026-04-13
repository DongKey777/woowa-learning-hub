# Semi-Join, LooseScan, FirstMatch, DuplicateWeedout

> 한 줄 요약: `IN`과 `EXISTS`는 문법 차이보다 semi-join으로 어떻게 변환되느냐가 더 중요하고, 그중 LooseScan은 특정 인덱스 패턴에서 강력하다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: semijoin, loosescan, firstmatch, duplicateweedout, semi-join transformation, optimizer_switch, subquery optimization, loose index scan

## 핵심 개념

- 관련 문서:
  - [Hash Join, Materialization, Join Buffer](./hash-join-materialization-join-buffer.md)
  - [MySQL Optimizer Hints and Index Merge](./mysql-optimizer-hints-index-merge.md)
  - [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
  - [인덱스와 실행 계획](./index-and-explain.md)

MySQL 옵티마이저는 `IN (subquery)`나 `EXISTS`를 단순히 서브쿼리로만 보지 않는다.  
조건이 맞으면 semi-join으로 변환해 더 나은 실행 전략을 고른다.

대표 전략은 다음이다.

- FirstMatch
- LooseScan
- DuplicateWeedout
- Materialization

이 문서는 이 이름들을 외우는 게 아니라, **어떤 데이터 분포와 인덱스 구조에서 어떤 전략이 유리한지**를 설명한다.

## 깊이 들어가기

### 1. semi-join이 풀려야 하는 문제

서브쿼리 결과가 단순 존재 확인만 필요할 때, 매 row마다 다시 계산하면 비싸다.  
semi-join은 "존재하면 된다"는 조건을 이용해 중복 계산을 줄인다.

예:

```sql
SELECT *
FROM orders o
WHERE o.user_id IN (
  SELECT u.id
  FROM users u
  WHERE u.status = 'ACTIVE'
);
```

### 2. FirstMatch는 빨리 한 번 찾고 멈춘다

FirstMatch는 조인된 후보를 찾는 즉시 다음 단계로 넘어간다.  
즉 "중복 확인을 최대한 빨리 끝내자"는 전략이다.

유리한 상황:

- 매칭 가능성이 높다
- 같은 outer row에 대해 많은 inner row를 더 볼 필요가 없다

### 3. LooseScan은 인덱스의 정렬성을 이용한다

LooseScan은 인덱스에서 필요한 값만 건너뛰며 읽는 전략으로 이해하면 좋다.  
특정 그룹/중복 제거 패턴에서 효과가 좋다.

중요 포인트:

- 인덱스 순서가 semi-join 조건과 맞아야 한다
- 범위를 통째로 다 읽기보다 "필요한 대표값"만 빠르게 찾는 느낌이다

### 4. DuplicateWeedout은 중복을 나중에 거른다

중복 후보를 먼저 수집한 뒤, 중복을 제거하는 전략이다.  
즉 계산은 덜 똑똑해 보여도, 특정 분포에서는 안정적이다.

### 5. 어떤 전략이 선택되는가

옵티마이저는 통계와 비용을 보고 전략을 고른다.

- FirstMatch: 빨리 끊는 게 유리할 때
- LooseScan: 인덱스 정렬성을 활용할 수 있을 때
- DuplicateWeedout: 중복 제거를 별도로 하는 게 나을 때
- Materialization: 서브쿼리를 미리 만들어 두는 편이 나을 때

### 6. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `semijoin`
- `loosescan`
- `firstmatch`
- `duplicateweedout`
- `semi-join transformation`
- `loose index scan`

## 실전 시나리오

### 시나리오 1. `IN (subquery)`가 갑자기 느려졌다

통계가 바뀌면서 옵티마이저가 semi-join 대신 다른 경로를 택할 수 있다.  
이때는 `EXPLAIN`으로 실제 선택된 전략을 봐야 한다.

### 시나리오 2. 인덱스는 있는데 LooseScan이 안 나온다

정렬 조건, 그룹 조건, 선행 컬럼 구조가 맞지 않으면 LooseScan이 선택되지 않는다.  
이건 인덱스가 "있느냐"보다 "semi-join에 맞느냐"의 문제다.

### 시나리오 3. duplicate 제거가 예상보다 비싸다

중복이 많은 분포에서는 DuplicateWeedout이 메모리와 임시 저장을 더 쓸 수 있다.  
이 경우 서브쿼리 재작성이나 인덱스 재배치가 필요하다.

## 코드로 보기

### semi-join 관찰

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

### optimizer_switch 비교

```sql
SET SESSION optimizer_switch='semijoin=on,loosescan=on,firstmatch=on,duplicateweedout=on';
SET SESSION optimizer_switch='semijoin=off';
```

### 인덱스 감각

```sql
CREATE INDEX idx_users_status_id ON users (status, id);
```

이런 인덱스 구조가 LooseScan이나 semi-join 판단에 영향을 줄 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| FirstMatch | 빨리 멈출 수 있다 | 분포가 안 맞으면 이득이 적다 | 매칭률이 높은 semi-join |
| LooseScan | 인덱스 정렬을 잘 활용한다 | 인덱스 구조 제약이 크다 | 중복/그룹 패턴 |
| DuplicateWeedout | 안정적이다 | 중간 결과 비용이 생긴다 | 중복이 많은 경우 |
| Materialization | 재사용에 유리하다 | 임시 저장 비용이 있다 | 서브쿼리 결과가 반복될 때 |

핵심은 `IN`과 `EXISTS`를 문법으로 보지 말고, **옵티마이저가 어떤 semi-join 전략을 쓸지** 보는 것이다.

## 꼬리질문

> Q: semi-join은 왜 중요한가요?
> 의도: 서브쿼리 최적화의 핵심을 아는지 확인
> 핵심: 존재 확인만 필요한 쿼리를 더 싸게 바꿀 수 있다

> Q: LooseScan은 언제 유리한가요?
> 의도: 인덱스 정렬성과 semi-join의 관계를 아는지 확인
> 핵심: 인덱스 순서로 필요한 값만 건너뛸 수 있을 때다

> Q: FirstMatch와 DuplicateWeedout의 차이는 무엇인가요?
> 의도: 전략별 중복 처리 차이를 이해하는지 확인
> 핵심: 한쪽은 빨리 멈추고, 다른 쪽은 중복을 수집 후 제거한다

## 한 줄 정리

semi-join 전략은 `IN`/`EXISTS`를 실제 실행으로 바꾸는 핵심이며, LooseScan은 인덱스 정렬이 맞을 때 특히 강력하다.
