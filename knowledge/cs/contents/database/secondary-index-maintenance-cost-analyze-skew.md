# Secondary Index Maintenance Cost and ANALYZE Statistics Skew

> 한 줄 요약: secondary index는 읽기를 빠르게 하지만, 쓰기 경로에는 매번 세금이 붙고, ANALYZE가 늦으면 옵티마이저는 그 세금을 잘못 계산한다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: secondary index, write amplification, index maintenance cost, ANALYZE TABLE, statistics skew, persistent statistics, histogram, optimizer misestimate, page split

## 핵심 개념

- 관련 문서:
  - [인덱스와 실행 계획](./index-and-explain.md)
  - [MySQL Optimizer Hints and Index Merge](./mysql-optimizer-hints-index-merge.md)
  - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
  - [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)

secondary index는 조회 성능을 높이는 대표 수단이지만, 모든 row 변경에 추가 비용을 붙인다.  
그리고 옵티마이저는 그 비용을 대충 감이 아니라 통계로 계산한다.

그래서 이 주제는 두 축을 같이 봐야 한다.

- secondary index를 하나 더 늘리면 쓰기 경로가 얼마나 무거워지는가
- ANALYZE TABLE이 늦거나 통계가 skew되면 왜 잘못된 실행 계획이 나오는가

## 깊이 들어가기

### 1. secondary index는 왜 비싼가

INSERT/UPDATE/DELETE가 일어날 때 secondary index도 같이 갱신된다.  
즉 데이터 한 줄이 바뀌어도 실제로는 여러 index entry를 만지게 된다.

비용이 붙는 지점은 대략 이렇다.

- 추가 index leaf page 수정
- page split 가능성
- redo/undo 증가
- buffer pool 압박
- unique index면 중복 검사 비용 추가

인덱스가 많을수록 읽기는 편해질 수 있지만, 쓰기에는 계속 세금이 붙는다.

### 2. change buffer가 있어도 공짜는 아니다

secondary index의 일부 변경은 change buffer로 미뤄질 수 있지만,  
그게 maintenance cost를 없애는 것은 아니다.  
나중에 merge 비용이 돌아오고, page가 read되는 순간 더 큰 비용이 몰릴 수 있다.

### 3. ANALYZE TABLE은 왜 필요한가

옵티마이저는 통계로 선택도를 추정한다.  
하지만 데이터 분포가 바뀌면 통계가 현실과 어긋날 수 있다.

예를 들어:

- status 컬럼이 예전엔 균등했는데 지금은 90%가 `PAID`
- 특정 tenant만 데이터가 폭증함
- 삽입 패턴이 바뀌어 index selectivity가 달라짐

이때 ANALYZE TABLE이 늦으면 옵티마이저가 잘못된 인덱스나 조인 순서를 고를 수 있다.

### 4. statistics skew는 왜 위험한가

통계 skew는 "평균적으로는 괜찮아 보이지만 실제 분포는 전혀 다름"을 뜻한다.  
DB는 평균이 아니라 실제 분포를 알아야 하는데, 샘플링이 그 차이를 못 잡으면 문제가 생긴다.

대표 증상:

- 작은 테이블처럼 보여서 풀스캔 선택
- 잘못된 인덱스 선택
- 조인 순서 역전
- LIMIT이 붙은 목록 쿼리가 갑자기 느려짐

### 5. histogram은 skew 완화에 도움이 될 수 있다

MySQL 8.0에서는 필요하면 histogram을 이용해 선택도를 더 잘 추정할 수 있다.  
하지만 이것도 만능은 아니고, 쿼리와 분포를 맞춰서 써야 한다.

### 6. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `secondary index`
- `write amplification`
- `index maintenance cost`
- `ANALYZE TABLE`
- `statistics skew`
- `persistent statistics`
- `histogram`
- `optimizer misestimate`

## 실전 시나리오

### 시나리오 1. 읽기 최적화용 인덱스를 많이 달았더니 쓰기가 느려졌다

목록 API를 살리려고 secondary index를 여러 개 추가했다.  
그런데 주문/로그/포인트 적립 같은 쓰기 경로가 전체적으로 무거워졌다.

이때는 "인덱스 하나 더"가 아니라,  
실제 read pattern을 재정의하고 중복 인덱스를 정리해야 한다.

### 시나리오 2. 같은 쿼리가 어느 날 갑자기 느려진다

데이터 분포가 바뀌었는데 통계는 그대로면, 옵티마이저가 옛날 기준으로 계획을 짤 수 있다.  
결과적으로 좋은 인덱스가 있어도 안 타거나, 나쁜 인덱스를 탈 수 있다.

### 시나리오 3. 특정 상태값에 데이터가 몰리면서 plan이 흔들린다

예전에는 status가 균등했지만, 지금은 `PAID`가 95%라면 선택도는 완전히 달라진다.  
이 경우 ANALYZE TABLE이나 histogram이 필요할 수 있다.

## 코드로 보기

### index 개수와 구조 확인

```sql
SHOW INDEX FROM orders;

SELECT TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX, COLUMN_NAME, CARDINALITY
FROM information_schema.statistics
WHERE table_schema = 'mydb'
  AND table_name = 'orders'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;
```

### 통계 갱신

```sql
ANALYZE TABLE orders;
```

### skew가 있는 컬럼에 histogram 적용

```sql
ANALYZE TABLE orders UPDATE HISTOGRAM ON status WITH 32 BUCKETS;
```

### plan 비교

```sql
EXPLAIN ANALYZE
SELECT id, status, created_at
FROM orders
WHERE status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

### 쓰기 경로 감각

```sql
INSERT INTO orders (id, user_id, status, created_at)
VALUES (900001, 1001, 'PAID', NOW());
```

이 한 줄이 secondary index 개수만큼 추가 작업을 만든다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| secondary index 추가 | 읽기 성능이 좋아진다 | 쓰기 비용이 늘어난다 | 반복 조회가 명확할 때 |
| secondary index 축소 | 쓰기 비용이 줄어든다 | 일부 읽기 쿼리가 느려질 수 있다 | 중복 인덱스가 많을 때 |
| `ANALYZE TABLE` 주기화 | 잘못된 plan을 줄인다 | 운영 이벤트가 생길 수 있다 | 데이터 분포가 자주 바뀔 때 |
| histogram 사용 | skew 추정이 좋아질 수 있다 | 관리가 필요하다 | 특정 값 쏠림이 심할 때 |

핵심은 인덱스를 많이 달아서 끝나는 게 아니라, **쓰기 세금과 통계 정확도를 같이 관리하는 것**이다.

## 꼬리질문

> Q: secondary index가 많으면 왜 쓰기가 느려지나요?
> 의도: write amplification과 page split 비용 이해 여부 확인
> 핵심: 한 row 변경이 여러 index entry 갱신으로 번지기 때문이다

> Q: ANALYZE TABLE은 왜 성능 문제의 첫 번째 대응이 될 수 있나요?
> 의도: 통계 기반 옵티마이저 이해 여부 확인
> 핵심: 인덱스가 있어도 잘못된 통계면 잘못된 계획을 고른다

> Q: histogram은 언제 고려하나요?
> 의도: skew 분포 대응 전략 이해 여부 확인
> 핵심: 특정 값 쏠림이 심하고 선택도 추정이 자주 틀릴 때다

## 한 줄 정리

secondary index는 읽기 성능을 바꾸는 대신 쓰기 비용을 늘리고, ANALYZE TABLE은 그 비용과 선택도를 옵티마이저가 제대로 계산하도록 통계를 다시 맞춰 준다.
