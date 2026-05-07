---
schema_version: 3
title: Golden Path Escape Hatch Policy
concept_id: software-engineering/golden-path-escape-hatch-policy
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- golden-path
- escape-hatch
- platform-governance
- policy-as-code
aliases:
- Golden Path Escape Hatch Policy
- golden path escape hatch
- paved road exception policy
- platform guardrail exception
- policy gated escape hatch
- 표준 경로 예외 승인 정책
symptoms:
- golden path가 너무 엄격해 legacy integration, regulatory requirement, high-throughput case가 unofficial bypass로 빠져
- escape hatch가 너무 쉬워 expiry, review, ADR, approval 없이 영구 예외와 platform drift가 늘어나
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/platform-paved-road
- software-engineering/policy-as-code
next_docs:
- software-engineering/platform-policy-override-governance
- software-engineering/service-template-tradeoffs
- software-engineering/prototype-spike-productionization
linked_paths:
- contents/software-engineering/platform-paved-road-tradeoffs.md
- contents/software-engineering/service-template-tradeoffs.md
- contents/software-engineering/architecture-review-anti-patterns.md
- contents/software-engineering/policy-as-code-architecture-linting.md
- contents/software-engineering/service-maturity-model.md
- contents/software-engineering/prototype-spike-productionization-boundaries.md
- contents/software-engineering/platform-policy-ownership-override-governance.md
confusable_with:
- software-engineering/platform-paved-road
- software-engineering/platform-policy-override-governance
- software-engineering/architecture-exception-process
forbidden_neighbors: []
expected_queries:
- golden path를 유지하면서 정당한 예외를 escape hatch로 승인하려면 어떤 정책이 필요해?
- paved road가 너무 엄격하면 왜 unofficial bypass가 생기고 어떻게 공식 예외 경로로 흡수해야 해?
- escape hatch에 reason, owner, approval, expiry, review date를 넣어야 하는 이유를 설명해줘
- 예외가 많아졌을 때 scorecard로 golden path 자체를 개선해야 하는 신호는 뭐야?
- policy as code와 exception registry로 platform guardrail 예외를 추적하는 방법을 알려줘
contextual_chunk_prefix: |
  이 문서는 golden path와 platform paved road의 기본 경로를 유지하면서 필요한 예외를 approval, expiry, ADR, policy gate로 통제하는 advanced playbook이다.
---
# Golden Path Escape Hatch Policy

> 한 줄 요약: golden path는 기본 경로를 쉽게 만들지만, 예외가 필요한 팀을 막지 않도록 escape hatch 정책을 같이 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Platform Paved Road Trade-offs](./platform-paved-road-tradeoffs.md)
> - [Service Template Trade-offs](./service-template-tradeoffs.md)
> - [Architecture Review Anti-Patterns](./architecture-review-anti-patterns.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Service Maturity Model](./service-maturity-model.md)
> - [Prototype, Spike, and Productionization Boundaries](./prototype-spike-productionization-boundaries.md)
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)

> retrieval-anchor-keywords:
> - golden path
> - escape hatch
> - exception policy
> - paved road
> - platform guardrail
> - approved exception
> - exception workflow
> - deviation control

## 핵심 개념

Golden path는 대부분의 팀이 안전하고 빠르게 일하도록 돕는다.
하지만 모든 팀이 같은 길을 쓸 수는 없다.

escape hatch는 정당한 예외를 처리하는 공식 경로다.

핵심은 예외를 허용하느냐가 아니라, **예외를 통제 가능하게 허용하느냐**다.

---

## 깊이 들어가기

### 1. golden path는 기본값이고, escape hatch는 예외 경로다

기본 경로:

- 표준 배포
- 표준 관측성
- 표준 인증

예외 경로:

- legacy integration
- regulatory requirement
- high-throughput special case
- experimental prototype

experimental prototype 예외라면 만료 날짜와 productionization 조건이 같이 있어야 한다.

### 2. 예외는 승인 없이 열리면 안 된다

정당한 예외인지 보려면:

- 왜 기본 경로를 못 쓰는가
- 언제까지 예외가 필요한가
- 무엇이 대체 경로인가
- 누가 승인하는가

### 3. escape hatch는 임시가 되어야 한다

예외는 영구 구조가 되기 쉽다.

그래서:

- expiry date
- review date
- ADR 기록
- compliance check

가 필요하다.

### 4. 정책은 friction을 적절히 유지해야 한다

예외가 너무 쉽다면 기본 경로의 의미가 사라진다.
너무 어렵다면 팀은 우회한다.

즉 escape hatch는 **억제 가능한 마찰**이어야 한다.

### 5. policy as code로 예외를 추적한다

예외가 많을수록 문서로만 관리하면 실패한다.

그래서 policy gate와 registry가 필요하다.

---

## 실전 시나리오

### 시나리오 1: 외부 규제로 기본 경로를 못 쓴다

정당한 예외를 승인하고, 만료와 대체 계획을 붙인다.

### 시나리오 2: 특정 팀이 성능 때문에 우회한다

예외를 허용하되, 기준을 문서화하고 재평가한다.

### 시나리오 3: 예외가 너무 많아졌다

escape hatch 사용 현황을 scorecard로 보고, paved road를 개선한다.

---

## 코드로 보기

```yaml
exception:
  reason: legacy_partner
  approved_by: platform-team
  expires_at: 2026-07-01
```

예외는 숨기는 것이 아니라 관리하는 것이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| strict golden path | 표준화가 쉽다 | 우회가 생긴다 | 단순한 팀 |
| loose escape hatch | 유연하다 | 정책이 흐려진다 | 초기 플랫폼 |
| golden path + policy-gated escape hatch | 균형이 좋다 | 운영이 필요하다 | 성숙한 조직 |

golden path escape hatch policy는 표준 경로를 살리면서도 필요한 예외를 공식적으로 다루는 장치다.

---

## 꼬리질문

- 어떤 예외는 허용하고 어떤 예외는 막을 것인가?
- 예외 만료를 어떻게 강제할 것인가?
- 우회 경로가 많아질 때 기본 경로를 어떻게 개선할 것인가?
- 예외 승인과 ADR 기록을 어떻게 연결할 것인가?

## 한 줄 정리

Golden path escape hatch policy는 표준 경로를 유지하면서도 필요한 예외를 공식적이고 만료 가능한 경로로 통제하는 정책이다.
