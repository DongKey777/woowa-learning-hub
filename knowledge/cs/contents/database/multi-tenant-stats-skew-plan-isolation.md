# Multi-Tenant Statistics Skew, Plan Drift, and Query Isolation

> 한 줄 요약: shared-table 멀티테넌시에서는 큰 tenant 하나의 데이터 분포가 전체 테이블 통계를 왜곡해, 작은 tenant 쿼리 계획까지 흔들 수 있다.

**난이도: 🔴 Advanced**

관련 문서:

- [Multi-Tenant Table Design, Tenant-First Indexing, and Hotspot Control](./multi-tenant-tenant-id-index-topology.md)
- [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)
- [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)
- [Histogram Drift와 Auto Analyze Threshold](./histogram-drift-auto-analyze-thresholds.md)
- [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)

retrieval-anchor-keywords: multi tenant statistics skew, tenant plan drift, shared table cardinality, tenant histogram skew, noisy neighbor query plan, plan isolation, backend saas query tuning

## 핵심 개념

shared-table 멀티테넌시의 통계 문제는 단순한 row 수 불균형이 아니다.

큰 tenant 하나가:

- status 분포
- created_at 최신성
- 특정 prefix cardinality

를 바꿔 버리면, optimizer는 전체 테이블 평균으로 계획을 짠다.  
그 결과 작은 tenant의 쿼리도 "큰 tenant 기준 현실"에 끌려갈 수 있다.

즉 멀티테넌트에서는 noisy neighbor가 CPU나 IO뿐 아니라 **optimizer statistics**에도 존재한다.

## 깊이 들어가기

### 1. shared-table 통계는 tenant별 현실을 평균내 버린다

예를 들어 `orders(tenant_id, status, created_at)`에서:

- tenant A는 `PAID` 95%
- tenant B는 `PAID` 5%

일 수 있다.

하지만 global histogram/cardinality는 이 둘을 섞어 본다.  
그래서 특정 tenant의 query shape에서는 실제 selectivity와 optimizer 추정이 크게 어긋날 수 있다.

### 2. tenant-first index가 있어도 통계 문제는 남을 수 있다

`(tenant_id, status, created_at)` 인덱스를 잡으면 scan 범위는 좋아진다.  
하지만 여전히 planner가 보는 것은 전체 인덱스 통계다.

문제가 드러나는 경우:

- 일부 tenant만 최근 데이터가 폭증
- 특정 tenant만 특정 status 값 쏠림
- 특정 tenant query만 LIMIT/ORDER 패턴이 다름

즉 index topology는 기본이고, 그 위에 **tenant-specific distribution drift**를 추가로 봐야 한다.

### 3. hot tenant는 작은 tenant 쿼리의 plan까지 흔들 수 있다

운영에서 흔한 현상:

- VIP tenant 데이터가 급증
- auto analyze가 global 분포 기준으로 통계 갱신
- small tenant 목록 조회가 갑자기 다른 plan을 탐

사용자는 "왜 우리 고객 쿼리가 느려졌지?"라고 보지만, 원인은 다른 tenant의 분포 변화일 수 있다.

### 4. 해결은 단순 ANALYZE만이 아니다

가능한 대응:

- tenant-first composite index 재설계
- skew 컬럼 histogram 조정
- query shape 분리
- hot tenant split-out
- summary/read model 분리

핵심은 optimizer misestimate를 "인덱스가 없다"가 아니라, **분포가 tenant별로 다르다**는 문제로 보는 것이다.

### 5. query isolation이 필요할 때가 있다

같은 논리 API라도 tenant 규모가 크게 다르면 같은 SQL이 최선이 아닐 수 있다.

예:

- small tenant는 index nested path가 적합
- huge tenant는 summary/read model이나 다른 access path가 적합

이 경우는 query isolation을 검토할 수 있다.

- tenant tier별 query path
- dedicated read model
- heavy tenant 전용 cluster/routing

즉 멀티테넌트에서는 SQL 한 줄보다 **tenant class별 접근 전략**이 더 현실적일 수 있다.

### 6. slow query debugging 때 tenant dimension을 빼면 원인을 놓친다

같은 endpoint라도 다음을 같이 봐야 한다.

- tenant_id
- tenant 규모 tier
- 해당 tenant의 status 분포
- 최근 growth rate

tenant dimension이 없으면 "가끔 느리다"로 보이던 현상이 사실은 "큰 tenant에서만 재현"되는 경우를 놓친다.

## 실전 시나리오

### 시나리오 1. 소형 고객 목록 조회가 어느 날 느려짐

원인:

- 대형 tenant 데이터 증가로 global stats 변화
- optimizer가 다른 plan 선택

대응:

- tenant-aware slow query grouping
- histogram/ANALYZE 점검
- heavy tenant 분리 여부 검토

### 시나리오 2. 특정 tenant만 LIMIT 쿼리가 유독 느림

그 tenant에서는 `status='READY'` 비율이 매우 높아, 일반 tenant와 완전히 다른 selectivity를 가진다.

이 경우는:

- dedicated query path
- queue/read model 분리

가 더 낫다.

### 시나리오 3. 운영자는 인덱스를 추가했는데도 일부 tenant 성능이 계속 흔들림

문제는 인덱스 부재가 아니라 distribution mismatch일 수 있다.

이때는 stats skew와 hot tenant isolation을 같이 봐야 한다.

## 코드로 보기

```sql
EXPLAIN ANALYZE
SELECT id, status, created_at
FROM orders
WHERE tenant_id = ?
  AND status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

```text
같이 저장할 디버깅 차원
- tenant_id
- tenant tier
- rows examined
- chosen index
- actual rows vs estimated rows
```

```sql
ANALYZE TABLE orders;
```

ANALYZE는 시작점이 될 수 있지만, 큰 tenant가 shared-table 통계를 계속 흔드는 구조라면 query isolation이나 split-out이 더 근본적인 해결책일 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| global stats에만 의존 | 단순하다 | tenant skew를 숨긴다 | tenant 규모가 비슷할 때 |
| tenant-first index | 기본 locality를 준다 | 분포 차이까지 해결하진 못한다 | shared-table 기본 설계 |
| tenant-aware query isolation | 큰 tenant 대응이 좋다 | 코드/운영 경로가 늘어난다 | tenant 규모 편차가 클 때 |
| hot tenant split-out | 근본적 격리가 가능하다 | migration 비용이 크다 | 일부 tenant가 압도적으로 클 때 |

## 꼬리질문

> Q: shared-table에서 왜 큰 tenant 하나가 작은 tenant 쿼리 계획까지 흔들 수 있나요?
> 의도: global statistics의 평균화 문제를 이해하는지 확인
> 핵심: optimizer가 tenant별이 아니라 전체 분포 기준으로 추정하기 때문이다

> Q: tenant-first index만으로 충분하지 않은 이유는 무엇인가요?
> 의도: topology와 statistics를 구분하는지 확인
> 핵심: scan 범위는 좋아져도 tenant별 selectivity 차이와 global stats 왜곡은 남을 수 있다

> Q: 언제 query isolation이나 split-out을 검토하나요?
> 의도: tuning과 architecture의 경계를 아는지 확인
> 핵심: 일부 tenant만 분포와 workload가 완전히 달라 shared-table 평균으로 감당이 안 될 때다

## 한 줄 정리

shared-table 멀티테넌시의 plan 문제는 인덱스 부족만이 아니라, 큰 tenant가 전체 통계를 왜곡해 다른 tenant query까지 흔드는 statistics skew에 있다.
