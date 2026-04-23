# Metrics Pipeline / TSDB 설계

> 한 줄 요약: metrics pipeline과 TSDB는 대규모 시계열 데이터를 수집, 집계, 보관, 조회해 운영 가시성을 제공하는 시스템이다.

retrieval-anchor-keywords: metrics pipeline, tsdb, time series, cardinality, rollup, retention, scrape, ingest, downsampling, prometheus, observability, trace exemplar, service latency, canary metric, guardrail dashboard, alert reevaluation, restated metric

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Distributed Tracing Pipeline 설계](./distributed-tracing-pipeline-design.md)
> - [Automated Canary Analysis / Rollback Platform 설계](./automated-canary-analysis-rollback-platform-design.md)
> - [Alert Re-Evaluation / Correction 설계](./alert-reevaluation-correction-design.md)
> - [Dashboard Restatement UX 설계](./dashboard-restatement-ux-design.md)

## 핵심 개념

메트릭 시스템은 로그를 예쁘게 그리는 도구가 아니다.  
실전에서는 다음을 동시에 만족해야 한다.

- 초당 수십만 샘플 수집
- 높은 cardinality 제어
- 빠른 최근 구간 조회
- 롤업과 장기 보관
- 알람과 대시보드
- 장애 시에도 관측 가능성 유지

즉, metrics pipeline은 운영의 신경계다.

## 깊이 들어가기

### 1. Metrics는 숫자보다 패턴이다

대표 metric 유형:

- counter
- gauge
- histogram
- summary

이때 중요한 건 "무엇을 측정할지"가 아니라, **어떤 질문에 답할지**다.

- error rate가 올라가는가
- p95 latency가 나빠지는가
- 특정 tenant만 느린가
- 리전 하나만 흔들리는가

### 2. Capacity Estimation

예:

- 1,000개 서비스
- 서비스당 500 metrics
- 10초마다 scrape

이러면 label 조합에 따라 폭발할 수 있다.  
cardinality가 높아지면 저장보다 index와 query가 더 무거워진다.

봐야 할 숫자:

- samples/sec
- unique series count
- ingest lag
- query latency
- retention storage

### 3. 파이프라인 구조

```text
App / Exporter
  -> Collector / Scraper
  -> Buffer / Queue
  -> Ingest
  -> TSDB
  -> Rollup / Downsample
  -> Query API / Alerting
```

collector는 수집, TSDB는 저장과 압축, query layer는 조회를 담당한다.

### 4. Cardinality와 label 설계

가장 큰 함정은 label explosion이다.

나쁜 예:

- user_id
- request_id
- trace_id

좋은 예:

- service
- route
- status
- region
- tenant tier

cardinality가 너무 높으면 TSDB가 사실상 로그 저장소가 된다.

### 5. Retention과 downsampling

메트릭은 최근일수록 촘촘하게, 오래될수록 거칠게 보관한다.

- raw 7일
- 1분 rollup 30일
- 1시간 rollup 1년

이렇게 해야 운영성과 비용을 같이 잡을 수 있다.

### 6. Query model

자주 쓰는 질의:

- 최근 5분 p95 latency
- 지난 24시간 error rate
- 특정 region의 1시간 트렌드

문제를 더 빨리 좁히려면 metric에서 exemplar나 trace link를 통해 느린 요청의 trace로 점프할 수 있어야 한다.
TSDB는 시계열 범위 질의에 최적화되어야 하며, arbitrary join은 피하는 편이 낫다.

### 7. Alerting

알람은 데이터가 아니라 정책이다.

- threshold
- anomaly detection
- burn rate
- multi-window alert

알람이 너무 많으면 사람이 무시한다.  
그래서 noisy metric을 줄이고, severity를 나눠야 한다.

## 실전 시나리오

### 시나리오 1: API latency 급증

문제:

- p95가 상승했는데 어느 지점인지 알아야 한다

해결:

- region, route, status label로 slice
- 최근 구간 raw metric 조회

### 시나리오 2: cardinality 폭발

문제:

- 새 label 추가 후 저장소가 급격히 커진다

해결:

- high-cardinality label 차단
- sample / aggregate 정책 적용

### 시나리오 3: 장기 추세 분석

문제:

- 1년치 패턴을 보고 싶다

해결:

- downsampled rollup 조회
- raw와 rollup을 분리

## 코드로 보기

```pseudo
function record(metricName, labels, value):
  series = normalize(metricName, labels)
  buffer.append(series, value, now())

function query(range, selector):
  return tsdb.select(range, selector)
```

```java
public void observe(String metric, Map<String, String> labels, double value) {
    metricsClient.record(metric, sanitize(labels), value);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Pull-based scrape | 운영이 단순하다 | pull 대상 관리 필요 | Prometheus 스타일 |
| Push-based ingest | edge/short-lived job에 좋다 | 신뢰성 관리 필요 | batch/ephemeral jobs |
| Raw-only storage | 단순하다 | 비용이 크다 | 짧은 보관 |
| Rollup-heavy storage | 저렴하다 | 세밀함이 줄어든다 | 장기 추세 |
| High-cardinality labels | 디버깅이 쉽다 | 비용이 폭발한다 | 제한적으로만 |

핵심은 metrics가 단순 저장이 아니라 **운영 판단을 위한 시간축 데이터 인프라**라는 점이다.

## 꼬리질문

> Q: metrics와 logs는 어떻게 다른가요?
> 의도: 관측성 데이터의 역할 구분 확인
> 핵심: metrics는 집계된 숫자, logs는 사건 기록이다.

> Q: cardinality가 왜 문제인가요?
> 의도: TSDB 비용 구조 이해 확인
> 핵심: series 수가 늘수록 저장, 인덱스, 쿼리 비용이 함께 커진다.

> Q: rollup을 왜 하나요?
> 의도: 장기 보관과 비용 trade-off 이해 확인
> 핵심: 오래된 데이터는 세밀함보다 추세가 중요하다.

> Q: 알람이 너무 많을 때 어떻게 하나요?
> 의도: 운영 노이즈 제어 이해 확인
> 핵심: severity, burn rate, dedup, suppression이 필요하다.

## 한 줄 정리

Metrics pipeline / TSDB는 high-cardinality 시계열 데이터를 효율적으로 수집하고 rollup해, 운영 판단과 알람을 가능하게 하는 인프라다.
