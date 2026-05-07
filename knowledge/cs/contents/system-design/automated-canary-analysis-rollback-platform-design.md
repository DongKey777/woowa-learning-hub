---
schema_version: 3
title: Automated Canary Analysis / Rollback Platform 설계
concept_id: system-design/automated-canary-analysis-rollback-platform-design
canonical: false
category: system-design
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- automated canary analysis
- rollback platform
- guardrail metrics
- error budget burn
aliases:
- automated canary analysis
- rollback platform
- guardrail metrics
- error budget burn
- canary score
- promotion gate
- rollback trigger
- release health
- progressive delivery
- deployment analysis
- resilience validation
- rollback safety
symptoms:
- Automated Canary Analysis / Rollback Platform 설계 관련 장애나 마이그레이션 리스크가 발생해 단계별 대응이 필요하다
intents:
- troubleshooting
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/traffic-shadowing-progressive-cutover-design.md
- contents/system-design/feature-flag-control-plane-design.md
- contents/system-design/api-gateway-control-plane-design.md
- contents/system-design/distributed-tracing-pipeline-design.md
- contents/system-design/metrics-pipeline-tsdb-design.md
- contents/system-design/backpressure-and-load-shedding-design.md
- contents/system-design/failure-injection-resilience-validation-platform-design.md
- contents/system-design/deploy-rollback-safety-compatibility-envelope-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Automated Canary Analysis / Rollback Platform 설계 장애 대응 순서를 알려줘
- automated canary analysis 복구 설계 체크리스트가 뭐야?
- Automated Canary Analysis / Rollback Platform 설계에서 blast radius를 어떻게 제한해?
- automated canary analysis 운영 리스크를 줄이는 방법은?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Automated Canary Analysis / Rollback Platform 설계를 다루는 playbook 문서다. automated canary analysis와 rollback 플랫폼은 새 버전의 오류율, 지연, 자원 포화, 비즈니스 가드레일을 자동 평가해 승격 여부를 결정하고, 이상 징후 시 빠르게 되돌리는 운영 제어 시스템이다. 검색 질의가 automated canary analysis, rollback platform, guardrail metrics, error budget burn처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Automated Canary Analysis / Rollback Platform 설계

> 한 줄 요약: automated canary analysis와 rollback 플랫폼은 새 버전의 오류율, 지연, 자원 포화, 비즈니스 가드레일을 자동 평가해 승격 여부를 결정하고, 이상 징후 시 빠르게 되돌리는 운영 제어 시스템이다.

retrieval-anchor-keywords: automated canary analysis, rollback platform, guardrail metrics, error budget burn, canary score, promotion gate, rollback trigger, release health, progressive delivery, deployment analysis, resilience validation, rollback safety

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
> - [Distributed Tracing Pipeline 설계](./distributed-tracing-pipeline-design.md)
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
> - [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md)
> - [Failure Injection / Resilience Validation Platform 설계](./failure-injection-resilience-validation-platform-design.md)
> - [Deploy Rollback Safety / Compatibility Envelope 설계](./deploy-rollback-safety-compatibility-envelope-design.md)

## 핵심 개념

canary는 단순히 "1%만 보내 본다"가 아니다.
중요한 것은 그 1%가 괜찮은지 **누가, 어떤 기준으로, 얼마나 빨리** 판단하느냐다.

실전에서는 다음을 같이 풀어야 한다.

- candidate와 baseline 비교
- route / tenant / region 단위 차이 분석
- latency, error, saturation, business metric 가드레일
- 자동 promotion / pause / rollback
- false positive와 false negative 균형

즉, canary analysis는 배포 도구의 부가기능이 아니라 **승격 의사결정을 자동화하는 운영 분석 제어 평면**이다.

## 깊이 들어가기

### 1. 왜 단순 threshold가 부족한가

새 버전의 5xx 비율만 보면 놓치는 것이 많다.

- 평균은 같아도 p99만 나빠질 수 있다
- 특정 tenant나 특정 route만 깨질 수 있다
- 에러는 없지만 retry amplification으로 downstream이 무너질 수 있다
- 비즈니스 metric이 조용히 나빠질 수 있다

그래서 canary는 여러 신호를 묶어 점수화하거나 단계별 gate를 두는 편이 많다.

### 2. Capacity Estimation

예:

- 전체 요청 20만 QPS
- canary 대상 5%
- 비교 대상 metric 수 200개
- 1분/5분/15분 관찰 창

이때 봐야 할 숫자:

- canary sample size
- decision latency
- route-level cardinality
- rollback-to-recovery 시간
- noisy metric 비율

표본이 너무 작으면 판단이 흔들리고, 너무 크면 blast radius가 커진다.

### 3. Analysis control plane

보통 구조는 다음과 같다.

```text
Deploy / Flag / Router
  -> Canary Policy Store
  -> Metric / Trace Fetcher
  -> Baseline Comparator
  -> Guardrail Scorer
  -> Promotion / Pause / Rollback Actuator
```

이 제어 평면이 관리해야 하는 것은 단순 비율이 아니다.

- baseline이 무엇인지
- 비교할 metric과 가중치
- tenant/route/region별 분리 여부
- 자동 승격 조건과 수동 승인 경계
- 분석 실패 시 기본 동작

### 4. Baseline 선택

baseline을 어떻게 잡느냐가 매우 중요하다.

선택지:

- 직전 stable 버전과 비교
- 동일 시간대 historical baseline과 비교
- region/tenant 내 control group과 비교
- candidate vs primary 동시 비교

트래픽 계절성이나 시간대 효과가 크면 historical baseline만으로는 오판할 수 있다.

### 5. Guardrail metric 구성

보통 아래 층을 나눈다.

- **안정성**: 5xx, timeout, crash, retry
- **성능**: p95, p99, queue lag, CPU, memory
- **품질**: diff mismatch, empty result, policy deny 비율
- **비즈니스**: conversion, capture rate, approval rate

모든 metric을 같은 중요도로 보면 안 된다.
결제 승인율 저하는 CPU 상승보다 훨씬 치명적일 수 있다.

### 6. Rollback trigger와 hysteresis

자동 rollback은 강력하지만 너무 민감하면 배포가 불가능해진다.

필요한 장치:

- minimum observation window
- multi-window confirmation
- severity별 trigger
- cool-down period
- hysteresis

즉, 한 번의 spike로 바로 뒤집지 않되, 명백한 이상은 빠르게 끊어야 한다.

### 7. Observability-rich analysis

좋은 canary 시스템은 숫자만 보는 것이 아니라 맥락까지 붙인다.

- trace exemplar
- route / tenant / region 태그
- candidate version
- upstream dependency graph
- deployment change set

이렇게 해야 "candidate가 왜 나쁜지"를 바로 추적할 수 있다.

## 실전 시나리오

### 시나리오 1: API 서버 새 버전 배포

문제:

- 2% canary는 통과했지만 일부 route의 p99가 급증한다

해결:

- route 단위로 baseline과 비교한다
- p99와 retry ratio를 같이 본다
- 특정 route만 fail-open 또는 rollback한다

### 시나리오 2: 검색 ranking 모델 교체

문제:

- 에러는 없지만 클릭률과 empty result 비율이 살짝 나빠진다

해결:

- 품질 metric과 비즈니스 metric을 guardrail에 포함한다
- trace와 diff 결과를 함께 본다
- 전체 rollback 대신 candidate exposure를 줄인다

### 시나리오 3: region별 배포

문제:

- APAC에서는 정상인데 EU tenant만 성능이 나빠진다

해결:

- region / tenant slice별 점수를 계산한다
- 승격은 slice 단위로 분리한다
- 문제가 있는 slice만 pause 또는 rollback한다

## 코드로 보기

```pseudo
function evaluateCanary(release):
  metrics = metricsFetcher.load(release.window, release.dimensions)
  score = scorer.compare(metrics.baseline, metrics.candidate)
  if score.severeFailure():
    actuator.rollback(release)
  elif score.pass():
    actuator.promote(release)
  else:
    actuator.pause(release)

function scoreLatency(baseline, candidate):
  return compareP95P99(baseline, candidate, tolerance=release.policy.latencyTolerance)
```

```java
public AnalysisDecision analyze(CanaryRelease release) {
    GuardrailReport report = guardrailService.evaluate(release);
    return decisionEngine.decide(report, release.policy());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Manual canary review | 단순하다 | 느리고 편향이 생긴다 | 작은 팀, 저빈도 배포 |
| Threshold-based auto gate | 구현이 쉽다 | 미묘한 regressions를 놓친다 | 초기 시스템 |
| Weighted guardrail scoring | 유연하다 | 정책 설계가 어렵다 | 다수 서비스 운영 |
| Full auto rollback | 대응이 빠르다 | false positive가 무섭다 | 명확한 SLO, mature observability |
| Slice-aware analysis | blast radius를 줄인다 | 차원 폭발이 생길 수 있다 | 멀티 tenant / multi-region |

핵심은 automated canary analysis가 canary 비율 조정이 아니라 **release health를 자동 평가하고 promotion/rollback을 결정하는 운영 분석 플랫폼**이라는 점이다.

## 꼬리질문

> Q: shadowing이 있으면 canary analysis는 덜 중요하지 않나요?
> 의도: shadow와 실제 응답 경로 차이 이해 확인
> 핵심: shadow는 correctness 힌트를 주지만, 실제 사용자 응답 경로의 latency, saturation, retries는 canary에서 따로 봐야 한다.

> Q: 왜 single metric threshold로 충분하지 않나요?
> 의도: 다차원 가드레일 이해 확인
> 핵심: 오류는 없어도 p99, retry amplification, business metric이 나빠질 수 있기 때문이다.

> Q: auto rollback이 너무 민감하면 어떻게 하나요?
> 의도: hysteresis와 false positive 이해 확인
> 핵심: observation window, multi-window confirmation, cool-down 같은 안정화 장치가 필요하다.

> Q: baseline은 항상 직전 버전이면 되나요?
> 의도: 비교 대상 선택 감각 확인
> 핵심: 시간대 효과나 tenant mix가 크면 control group이나 slice-aware baseline이 더 적절할 수 있다.

## 한 줄 정리

Automated canary analysis와 rollback 플랫폼은 candidate release의 운영 품질을 다차원 guardrail로 평가해 승격, 정지, 롤백을 자동화하는 운영 의사결정 시스템이다.
