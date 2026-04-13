# Experimentation / A/B Testing Platform 설계

> 한 줄 요약: 실험 플랫폼은 사용자 배정을 안정적으로 관리하고, 지표 수집과 분석을 통해 제품 변경의 효과를 검증하는 의사결정 시스템이다.

retrieval-anchor-keywords: experimentation platform, A/B testing, bucketing, randomization, guardrail metrics, experiment assignment, statistical power, holdout, feature rollout, analysis pipeline

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [Recommendation / Feed Ranking Architecture](./recommendation-feed-ranking-architecture.md)
> - [Search 시스템 설계](./search-system-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)

## 핵심 개념

실험 플랫폼은 단순히 트래픽을 반반 나누는 기능이 아니다.  
실전에서는 아래를 함께 관리한다.

- 안정적인 사용자 배정
- 실험군/대조군 충돌 방지
- 지표 수집과 정제
- 통계적 유의성 판단
- guardrail metric
- ramp up / ramp down

즉, experimentation은 제품 변경을 과학적으로 검증하는 운영 인프라다.

## 깊이 들어가기

### 1. 무엇을 실험하는가

흔한 대상:

- UI 변경
- 추천 알고리즘
- 검색 랭킹
- pricing 페이지
- notification cadence

실험은 기능을 켜는 문제가 아니라, **비즈니스 지표에 어떤 변화가 생겼는지 확인하는 문제**다.

### 2. Capacity Estimation

예:

- DAU 1,000만
- 하루 100개 실험
- 요청당 5개 assignment lookup

이 정도면 assignment path가 아주 가벼워야 한다.  
실험 시스템이 느리면 제품 path 전체를 망친다.

봐야 할 숫자:

- assignment QPS
- exposure count
- conversion window
- sample size
- analysis latency

### 3. Assignment 모델

실험 배정은 안정적이어야 한다.

- stable bucketing
- mutually exclusive layer
- holdout group
- user-level vs session-level assignment

같은 사용자는 같은 버킷에 들어가야 분석이 깨지지 않는다.

### 4. Metric design

실험에는 primary metric과 guardrail metric이 필요하다.

- primary: 전환율, 클릭률, retention
- guardrail: latency, error rate, revenue, churn

좋아 보이는 실험이 시스템을 망가뜨리면 안 된다.

### 5. Exposure와 분석

실험 결과는 노출 기준으로 봐야 한다.

- assigned
- exposed
- converted

노출되지 않은 실험 대상까지 포함하면 결론이 왜곡된다.

### 6. 데이터 정합성

분석이 틀어지는 흔한 이유:

- logging missing
- assignment drift
- metric definition change
- late arrival

그래서 experiment event와 metric event를 함께 설계해야 한다.

### 7. Ramp와 종료

실험은 시작보다 종료가 어렵다.

- 1%
- 10%
- 50%
- 100%

문제 있으면 즉시 rollback한다.  
성공하면 holdout을 남기거나 전면 적용한다.

## 실전 시나리오

### 시나리오 1: 추천 변경 실험

문제:

- 새 랭킹 모델이 전환율을 올리는지 알아야 한다

해결:

- stable bucketing
- primary/guardrail metric
- ramp up

### 시나리오 2: 가격 페이지 실험

문제:

- 가격 노출 방식이 구매율에 영향을 준다

해결:

- user-level assignment
- revenue guardrail
- 충분한 sample size 확보

### 시나리오 3: 분석 지연

문제:

- 결과가 늦게 들어와 판단이 늦다

해결:

- metrics pipeline 최적화
- late event 보정
- near-real-time dashboard

## 코드로 보기

```pseudo
function assign(userId, experiment):
  bucket = hash(userId + experiment.id) % 10000
  return experiment.armFor(bucket)

function recordExposure(userId, experiment, arm):
  logExposure(userId, experiment.id, arm)
```

```java
public String bucketFor(long userId, String experimentId) {
    return bucketer.assign(userId, experimentId);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| User-level bucketing | 분석이 안정적이다 | 전환이 느릴 수 있다 | 대부분 |
| Session-level bucketing | 반응이 빠르다 | 노이즈가 크다 | 짧은 실험 |
| Central assignment | 일관성이 좋다 | latency가 생긴다 | 공통 플랫폼 |
| Client assignment | 빠르다 | 조작 가능성 | 경량 실험 |
| Holdout group | 장기 효과 측정 가능 | 매출 기회 손실 | 성숙한 조직 |

핵심은 실험이 단순한 반반 분할이 아니라 **배정, 측정, 해석, 롤백을 포함한 의사결정 시스템**이라는 점이다.

## 꼬리질문

> Q: feature flag와 experimentation platform은 어떻게 다른가요?
> 의도: 운영 제어와 실험 검증 구분 확인
> 핵심: flag는 기능 제어, experimentation은 효과 검증이 중심이다.

> Q: 왜 stable bucketing이 중요한가요?
> 의도: 분석 일관성 이해 확인
> 핵심: 같은 사용자가 여러 arm에 흔들리면 실험 결과가 왜곡된다.

> Q: primary metric과 guardrail metric은 왜 둘 다 필요한가요?
> 의도: 단일 지표 함정 이해 확인
> 핵심: 목표를 올려도 시스템을 해치지 않는지 봐야 한다.

> Q: exposure와 assignment의 차이는 무엇인가요?
> 의도: 실험 분석 기준 이해 확인
> 핵심: 배정은 대상, 노출은 실제 본 사용자다.

## 한 줄 정리

Experimentation / A/B testing platform은 사용자 배정과 metric 분석을 안정화해 제품 변경의 효과를 신뢰성 있게 검증하는 시스템이다.

