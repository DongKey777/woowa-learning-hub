# Statistics, Histograms, and Cardinality Estimation

> 한 줄 요약: 옵티마이저는 감으로 인덱스를 고르지 않고 통계로 고르기 때문에, 통계가 틀리면 좋은 인덱스도 나쁜 계획으로 보인다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: statistics, histogram, cardinality estimation, persistent statistics, selectivity, ANALYZE TABLE, optimizer cost model, skewed distribution

## 핵심 개념

- 관련 문서:
  - [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)
  - [MySQL Optimizer Hints and Index Merge](./mysql-optimizer-hints-index-merge.md)
  - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)

옵티마이저는 "이 인덱스가 좋아 보인다"는 직감으로 실행 계획을 고르지 않는다.  
통계와 비용 모델을 바탕으로 cardinality를 추정한다.

그래서 이 문서의 핵심은 하나다.

- 인덱스가 있어도 통계가 틀리면 안 탈 수 있다
- 통계가 좋으면 복잡한 쿼리도 더 나은 계획을 고를 수 있다
- skew가 크면 histogram이 도움이 될 수 있다

## 깊이 들어가기

### 1. cardinality estimation이 왜 중요한가

cardinality는 "조건을 만족하는 row가 얼마나 남는가"에 대한 추정이다.  
이 값이 틀리면 다음이 전부 틀어진다.

- 인덱스 선택
- 조인 순서
- nested loop vs hash join 경로
- filesort/temporary table 선택

### 2. 통계는 실제 분포의 근사치다

DB는 모든 row를 매번 세지 않는다.  
대신 샘플링과 누적 통계로 대략의 분포를 본다.

그래서 다음 상황이 오면 어긋날 수 있다.

- 최근 데이터가 급증했다
- 특정 tenant나 status에 쏠림이 생겼다
- 오래된 통계가 남아 있다

### 3. histogram은 skew를 보정하는 도구다

모든 컬럼에 histogram이 필요한 건 아니지만, 분포가 심하게 치우친 컬럼은 도움이 될 수 있다.

- `status`처럼 값 종류가 적지만 한쪽으로 몰리는 컬럼
- `country`, `tenant_id`, `category`처럼 편중이 큰 컬럼

하지만 histogram도 만능은 아니다.

- 관리가 필요하다
- 쿼리 특성을 모르면 오히려 복잡도를 늘린다

### 4. persistent statistics는 왜 필요한가

통계가 재시작마다 흔들리면 계획도 흔들린다.  
지속 통계를 유지하면 예측 가능성이 높아진다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `statistics`
- `histogram`
- `cardinality estimation`
- `persistent statistics`
- `selectivity`
- `ANALYZE TABLE`
- `optimizer cost model`

## 실전 시나리오

### 시나리오 1. 같은 쿼리가 배포 후 갑자기 느려졌다

코드는 안 바뀌었는데 데이터 분포가 바뀌면 통계가 더 이상 맞지 않을 수 있다.  
이때는 인덱스보다 먼저 ANALYZE와 통계를 본다.

### 시나리오 2. status 조건이 너무 흔해져 인덱스가 안 탄다

예전에는 `status='PAID'`가 희귀했는데 이제는 대부분이라면, 선택도가 낮아져 인덱스 효과가 줄 수 있다.  
통계는 이 변화를 따라가야 한다.

### 시나리오 3. 조인 순서가 이상하다

잘못된 cardinality estimation은 조인 순서를 바꿔버린다.  
결과적으로 큰 테이블이 먼저 와서 비용이 폭증할 수 있다.

## 코드로 보기

### 통계 확인

```sql
SHOW TABLE STATUS LIKE 'orders';
SHOW INDEX FROM orders;
```

### 통계 갱신

```sql
ANALYZE TABLE orders;
```

### histogram 적용

```sql
ANALYZE TABLE orders UPDATE HISTOGRAM ON status WITH 32 BUCKETS;
```

### plan 비교

```sql
EXPLAIN ANALYZE
SELECT id, status
FROM orders
WHERE status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 자동 통계에 의존 | 관리가 쉽다 | 분포 변화에 늦을 수 있다 | 안정적인 데이터 |
| ANALYZE 주기화 | 계획 정확도를 높인다 | 운영 시점 비용이 있다 | 데이터가 자주 바뀔 때 |
| histogram 사용 | skew를 더 잘 잡는다 | 관리와 검증이 필요하다 | 편중 분포가 심할 때 |
| 인덱스 재설계 | 근본 개선이 가능하다 | DDL 비용이 든다 | 통계만으로 해결 안 될 때 |

핵심은 옵티마이저가 틀렸다고 탓하기 전에, **그 옵티마이저가 보고 있는 통계가 현실과 맞는지**를 확인하는 것이다.

## 꼬리질문

> Q: cardinality estimation이 왜 중요한가요?
> 의도: 비용 모델의 기반을 이해하는지 확인
> 핵심: 인덱스와 조인 계획이 그 추정치에 의존한다

> Q: histogram은 언제 도움이 되나요?
> 의도: 분포 편중 문제를 아는지 확인
> 핵심: 특정 값에 데이터가 많이 몰릴 때다

> Q: ANALYZE TABLE은 왜 자주 언급되나요?
> 의도: 통계 갱신의 실전 의미를 이해하는지 확인
> 핵심: 오래된 통계를 현실에 맞춰 다시 잡아주기 때문이다

## 한 줄 정리

statistics와 histogram은 옵티마이저의 눈이고, 그 눈이 흐려지면 인덱스와 조인 계획이 전부 틀어질 수 있다.
