# Statistics, Histograms, and Cardinality Estimation

> 한 줄 요약: 옵티마이저는 감으로 인덱스를 고르지 않고 통계로 고르기 때문에, 통계가 틀리면 좋은 인덱스도 나쁜 계획으로 보인다.
>
> 관련 문서:
> - [인덱스와 실행 계획](./index-and-explain.md)
> - [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
> - [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md)
> - [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)
> - [MySQL Optimizer Hints and Index Merge](./mysql-optimizer-hints-index-merge.md)
> - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
>
> retrieval-anchor-keywords:
> - statistics
> - histogram
> - cardinality estimation
> - persistent statistics
> - selectivity
> - ANALYZE TABLE
> - optimizer cost model
> - skewed distribution
> - rows estimate wrong
> - rows estimate too high
> - rows estimate too low
> - explain rows mismatch
> - explain analyze actual rows
> - optimizer misestimate
> - stale statistics
> - plan drift
> - query plan changed after deploy
> - wrong join order statistics
> - wrong index choice statistics
> - histogram skew
> - tenant skew
> - 데이터 분포 바뀌어서 실행 계획 달라짐
> - rows 추정치 틀림
> - 통계 오래됨
> - analyze table 언제
> - plan drift 왜 생김

**난이도: 🔴 Advanced**

## 이 문서 다음에 보면 좋은 문서

- `type`, `key`, `rows`, `Extra`를 어디서부터 읽어야 할지 아직 헷갈리면 [인덱스와 실행 계획](./index-and-explain.md)과 [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)로 먼저 돌아가는 편이 안전하다.
- `Using filesort`, `Using temporary`, `ICP` 같은 `Extra` 신호 자체가 주증상이면 [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md)에서 정렬 경로와 임시 테이블 이유를 먼저 분리한다.
- skew가 특정 secondary index 유지 비용이나 write path와 같이 엮여 있으면 [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)을 이어 본다.
- 운영 중 즉시 triage 순서가 먼저 필요하면 [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)으로 내려간다.

## 이 문서가 맡는 EXPLAIN 범위

이 문서는 "`EXPLAIN`은 읽었는데 왜 `rows` 추정치와 실제가 어긋나는가"를 설명하는 통계 entry다.
즉 접근 경로의 문법보다 cardinality estimation과 plan drift를 먼저 해석할 때 붙는다.

| 보이는 신호 | 여기서 바로 보는 것 | 먼저 돌아갈 문서 |
| --- | --- | --- |
| `rows` 추정치가 실제와 크게 다르거나 `EXPLAIN ANALYZE` actual rows가 튐 | cardinality estimation, selectivity, histogram, stale statistics | [쿼리 튜닝 체크리스트](./query-tuning-checklist.md), [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md) |
| 배포 후 SQL은 같은데 plan만 흔들림 | 데이터 분포 변화, `ANALYZE TABLE`, persistent statistics, skew | [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md), [MySQL Optimizer Hints and Index Merge](./mysql-optimizer-hints-index-merge.md) |
| `Using filesort`, `Using temporary`, `ICP`가 주증상이고 `rows` mismatch는 부차적임 | 이 문서보다 `Extra` 해석이 먼저 | [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md), [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) |
| `type = ALL`, `key = NULL`, predicate가 sargable 한지부터 의심됨 | 통계 이전의 접근 경로 문제 | [인덱스와 실행 계획](./index-and-explain.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| DB time이 아니라 앱 레이어 병목일 수도 있음 | 통계 문제로 과잉 해석하지 말고 triage 순서 점검 | [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |

## 핵심 개념

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
