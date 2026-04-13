# Fraud / Risk Scoring Pipeline 설계

> 한 줄 요약: fraud and risk scoring pipeline은 거래와 행동 신호를 실시간으로 평가해 사기와 이상행동을 탐지하고 차단하는 의사결정 시스템이다.

retrieval-anchor-keywords: fraud detection, risk scoring, feature pipeline, anomaly detection, chargeback, rule engine, model scoring, alert queue, graph features, real-time decisioning

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
> - [Billing / Usage Metering System 설계](./billing-usage-metering-system-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
> - [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
> - [Rate Limiter 설계](./rate-limiter-design.md)

## 핵심 개념

Fraud scoring은 단순 필터링이 아니다.  
실전에서는 아래를 함께 다뤄야 한다.

- 행동 신호 수집
- feature aggregation
- rule-based decision
- ML scoring
- explainability
- manual review queue
- feedback loop

즉, risk pipeline은 자동화된 보안과 운영 판단을 연결하는 시스템이다.

## 깊이 들어가기

### 1. 무엇을 점수화할 것인가

대상은 보통 다음이다.

- account signup
- login attempt
- payment transaction
- refund request
- coupon abuse
- device / IP reputation

사기 탐지는 하나의 모델로 끝나지 않고, 여러 도메인 시그널을 합친다.

### 2. Capacity Estimation

예:

- 1초당 10만 decision
- decision당 feature fetch 30개
- 일부는 실시간 차단 필요

이 경우 scoring latency가 핵심이다.  
특히 payment나 signup은 수백 ms 안에 결정을 내려야 한다.

봐야 할 숫자:

- decision latency
- false positive rate
- false negative rate
- review queue depth
- model drift

### 3. 파이프라인 구조

```text
Event / Transaction
  -> Feature Aggregation
  -> Rule Engine
  -> ML Scoring
  -> Decision Service
  -> Review / Block / Allow
```

feature aggregation은 배치와 스트리밍을 섞는 경우가 많다.

### 4. Rule engine과 model scoring

보통 rule이 먼저다.

- device mismatch
- velocity check
- IP reputation
- impossible travel

그 다음 모델 점수를 더한다.

- probability of fraud
- anomaly score
- network graph score

rule은 설명이 쉽고 빠르며, 모델은 복잡한 패턴을 잡는다.

### 5. Feedback loop

Fraud 시스템은 정답이 늦게 온다.

- chargeback
- manual review outcome
- user dispute

그래서 학습과 규칙 개선을 위한 feedback loop가 필수다.  
이 흐름이 없으면 모델이 계속 낡는다.

### 6. Explainability

오탐이 나면 사용자 경험과 CS 비용이 커진다.

필요한 것:

- score reason codes
- rule hit list
- feature snapshot
- decision trace

이 정보는 [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)와 연결된다.

### 7. Isolation and fallback

risk engine가 죽으면 결제/가입이 멈출 수 있다.  
그래서 fallback 정책이 필요하다.

- allow on low risk
- block on high risk
- manual review on uncertain

## 실전 시나리오

### 시나리오 1: 신규 계정 생성 폭주

문제:

- 봇 계정이 대량 생성된다

해결:

- velocity rule
- device/IP reputation
- challenge flow

### 시나리오 2: 결제 사기 의심

문제:

- 카드 테스트 패턴이 보인다

해결:

- real-time scoring
- hold decision
- manual review queue

### 시나리오 3: 모델 오탐 증가

문제:

- 정상 사용자를 잘못 막는다

해결:

- feature drift 확인
- rule 완화
- canary rollout

## 코드로 보기

```pseudo
function decide(txn):
  features = featureStore.get(txn.userId, txn.deviceId)
  rules = ruleEngine.evaluate(features, txn)
  score = model.score(features, txn)
  return combine(rules, score)
```

```java
public Decision decide(Transaction txn) {
    RiskFeatures features = featureService.build(txn);
    RiskScore score = scorer.score(features);
    return policyEngine.combine(features, score);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Rules only | 빠르고 설명 가능 | 복잡 패턴 한계 | 초기 방어 |
| ML only | 패턴 탐지 강함 | 설명/운영 어려움 | 성숙한 플랫폼 |
| Hybrid rules + ML | 실무 친화적 | 파이프라인 복잡 | 대부분의 서비스 |
| Block first | 손실 방어 강함 | 오탐 비용 큼 | 고위험 거래 |
| Review first | 사용자 피해 줄임 | 운영 비용 증가 | 고가치/불확실 케이스 |

핵심은 fraud scoring이 단일 모델이 아니라 **실시간 의사결정과 사후 학습이 결합된 운영 시스템**이라는 점이다.

## 꼬리질문

> Q: fraud pipeline에서 가장 중요한 지표는 무엇인가요?
> 의도: 정확도와 운영 trade-off 이해 확인
> 핵심: false positive, false negative, decision latency를 같이 봐야 한다.

> Q: rule engine과 model을 왜 같이 쓰나요?
> 의도: 설명 가능성과 탐지력의 균형 확인
> 핵심: rule은 빠르고 설명 가능하며, 모델은 복잡한 패턴에 강하다.

> Q: feedback loop가 왜 필요한가요?
> 의도: 지연된 정답과 모델 운영 이해 확인
> 핵심: 사기 정답은 나중에 나오므로 지속 학습이 필요하다.

> Q: risk engine이 실패하면 어떻게 하나요?
> 의도: fallback policy 이해 확인
> 핵심: high-risk는 block, low-risk는 allow, uncertain은 review로 나눈다.

## 한 줄 정리

Fraud / risk scoring pipeline은 행동과 거래 신호를 실시간으로 평가해 차단, 보류, 허용을 결정하고, 사후 피드백으로 계속 개선하는 시스템이다.

