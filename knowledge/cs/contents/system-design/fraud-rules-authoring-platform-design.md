---
schema_version: 3
title: Fraud Rules Authoring Platform 설계
concept_id: system-design/fraud-rules-authoring-platform-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- fraud rules authoring
- rule DSL
- policy simulation
- historical replay
aliases:
- fraud rules authoring
- rule DSL
- policy simulation
- historical replay
- canary rules
- thresholds
- scoring rules
- rule versioning
- explainable fraud
- decision tree
- Fraud Rules Authoring Platform 설계
- fraud rules authoring platform design
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/fraud-risk-scoring-pipeline-design.md
- contents/system-design/fraud-case-management-workflow-design.md
- contents/system-design/experimentation-ab-testing-platform-design.md
- contents/system-design/audit-log-pipeline-design.md
- contents/system-design/metrics-pipeline-tsdb-design.md
- contents/system-design/event-bus-control-plane-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Fraud Rules Authoring Platform 설계 설계 핵심을 설명해줘
- fraud rules authoring가 왜 필요한지 알려줘
- Fraud Rules Authoring Platform 설계 실무 트레이드오프는 뭐야?
- fraud rules authoring 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Fraud Rules Authoring Platform 설계를 다루는 deep_dive 문서다. fraud rules authoring platform은 사기 탐지 규칙을 작성, 테스트, 시뮬레이션, 배포, 롤백하는 정책 개발 환경이다. 검색 질의가 fraud rules authoring, rule DSL, policy simulation, historical replay처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Fraud Rules Authoring Platform 설계

> 한 줄 요약: fraud rules authoring platform은 사기 탐지 규칙을 작성, 테스트, 시뮬레이션, 배포, 롤백하는 정책 개발 환경이다.

retrieval-anchor-keywords: fraud rules authoring, rule DSL, policy simulation, historical replay, canary rules, thresholds, scoring rules, rule versioning, explainable fraud, decision tree

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Fraud / Risk Scoring Pipeline 설계](./fraud-risk-scoring-pipeline-design.md)
> - [Fraud Case Management Workflow 설계](./fraud-case-management-workflow-design.md)
> - [Experimentation / A/B Testing Platform 설계](./experimentation-ab-testing-platform-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
> - [Event Bus Control Plane 설계](./event-bus-control-plane-design.md)

## 핵심 개념

사기 규칙은 그냥 if문이 아니다.  
실전에서는 아래를 함께 관리해야 한다.

- rule DSL
- historical simulation
- threshold tuning
- canary deployment
- decision explanation
- rollback and approval

즉, rules platform은 사기 정책을 운영 가능한 소프트웨어로 만드는 환경이다.

## 깊이 들어가기

### 1. rules vs model

모델이 복잡한 패턴을 잡고, 규칙은 명확한 정책을 집행한다.

- rules: velocity, blacklist, impossible travel
- model: anomaly, hidden relation, risk score

둘을 섞으면 설명 가능성과 탐지력이 같이 올라간다.

### 2. Capacity Estimation

예:

- 수천 개 rule
- 초당 수만 decision
- 매일 수십 번의 rule edit

편집은 적고 실행은 많다.  
그래서 authorship path와 runtime path를 분리해야 한다.

봐야 할 숫자:

- rule evaluation latency
- simulation duration
- false positive rate
- false negative rate
- rollback time

### 3. Rule DSL

```text
if device.country != user.country and velocity > 5 then hold
if card.bin in blacklist then reject
if amount > 1000000 and account_age < 7d then review
```

DSL은 비개발자도 읽을 수 있어야 하고, 실행은 안전해야 한다.

### 4. simulation

규칙은 배포 전에 검증해야 한다.

- historical replay
- shadow evaluation
- precision/recall estimate
- impact analysis

이 부분은 [Experimentation / A/B Testing Platform 설계](./experimentation-ab-testing-platform-design.md)와 비슷하다.

### 5. versioning and approval

규칙은 변경 이력이 중요하다.

- draft
- review
- approved
- active
- retired

이력은 [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)로 남겨야 한다.

### 6. runtime integration

규칙은 risk pipeline의 일부로 실행된다.

- pre-check
- score combine
- post-action

이 부분은 [Fraud / Risk Scoring Pipeline 설계](./fraud-risk-scoring-pipeline-design.md)와 연결된다.

### 7. explainability

rules는 설명 가능해야 한다.

- which rule fired
- why it fired
- what value matched
- which version was active

## 실전 시나리오

### 시나리오 1: 새 카드 BIN 차단

문제:

- 특정 카드 대역이 위험하다

해결:

- blacklist rule 추가
- historical replay로 영향 확인

### 시나리오 2: 오탐 증가

문제:

- 정상 거래가 너무 많이 막힌다

해결:

- threshold 완화
- canary rollout
- rollback 준비

### 시나리오 3: rule 충돌

문제:

- 서로 반대되는 규칙이 있다

해결:

- priority
- explicit precedence
- conflict warning

## 코드로 보기

```pseudo
function publishRule(rule):
  validate(rule)
  simulate(rule, historicalData)
  if approval.passed:
    activate(rule.version)

function evaluate(txn):
  fired = ruleEngine.evaluate(txn)
  return combine(fired, riskScore(txn))
```

```java
public RuleVersion publish(RuleDefinition rule) {
    return ruleService.validateAndActivate(rule);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Hard-coded rules | 빠르다 | 운영이 어렵다 | 매우 초기 |
| DSL-based rules | 변경이 쉽다 | 파서와 검증이 필요 | 실서비스 |
| Model-only | 패턴 탐지 강함 | 설명이 약하다 | 고도화 단계 |
| Hybrid rules+model | 실무적이다 | 복잡도 증가 | 대부분 |
| Replay-simulated deploy | 안전하다 | 배포가 느려진다 | 금융/결제 |

핵심은 fraud rules authoring platform이 단순 관리 UI가 아니라 **정책을 안전하게 만들고 검증하는 개발 환경**이라는 점이다.

## 꼬리질문

> Q: rules와 model을 왜 분리하나요?
> 의도: 설명 가능성과 표현력의 차이 이해 확인
> 핵심: 규칙은 명확한 정책, 모델은 복잡한 패턴에 강하다.

> Q: simulation이 왜 필요한가요?
> 의도: 실험 없이 배포하면 생기는 위험 이해 확인
> 핵심: 오탐과 누락의 영향을 미리 봐야 한다.

> Q: rule 충돌은 어떻게 해결하나요?
> 의도: 우선순위와 precedence 이해 확인
> 핵심: 명시적 우선순위와 충돌 경고가 필요하다.

> Q: 왜 audit log가 중요한가요?
> 의도: 정책 변경 추적 이해 확인
> 핵심: 어떤 규칙이 언제 적용됐는지 증명해야 한다.

## 한 줄 정리

Fraud rules authoring platform은 사기 방지 규칙을 시뮬레이션과 승인, 버전 관리로 안전하게 운영하는 정책 개발 환경이다.

