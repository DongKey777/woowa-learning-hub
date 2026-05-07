---
schema_version: 3
title: Service Criticality Tiering and Control Intensity
concept_id: software-engineering/service-criticality-tiering
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- service-governance
- criticality
- control-profile
- readiness
aliases:
- service criticality tiering
- control intensity by service tier
- governance intensity profile
- service risk tier
- operational rigor by criticality
- 서비스 중요도 티어링
symptoms:
- 모든 서비스에 같은 PRR, drill, on-call, rollout gate를 적용해 핵심 서비스에는 약하고 낮은 중요도 서비스에는 과한 통제가 생겨
- traffic만 보고 service criticality를 정해 revenue impact, legal risk, blast radius, manual workaround 가능성을 놓쳐
- service stage와 criticality tier를 같은 축으로 봐서 temporary service의 높은 위험이나 active service의 낮은 위험을 설명하지 못해
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/service-portfolio-lifecycle-governance
- software-engineering/sla-slo-ownership-model
next_docs:
- software-engineering/rollout-guardrail-profiles
- software-engineering/production-readiness-review
- software-engineering/on-call-ownership-boundaries
linked_paths:
- contents/software-engineering/service-portfolio-lifecycle-governance.md
- contents/software-engineering/operational-readiness-drills-and-change-safety.md
- contents/software-engineering/production-readiness-review.md
- contents/software-engineering/sla-slo-ownership-model.md
- contents/software-engineering/on-call-ownership-boundaries.md
- contents/software-engineering/support-operating-models-self-service-office-hours-oncall.md
confusable_with:
- software-engineering/service-portfolio-lifecycle-governance
- software-engineering/service-maturity-model
- software-engineering/rollout-guardrail-profiles
forbidden_neighbors: []
expected_queries:
- service criticality tier는 traffic보다 business impact와 blast radius 기준으로 어떻게 나눠야 해?
- tier 0부터 tier 3까지 control intensity를 PRR, rollout, drill, on-call 기준으로 다르게 두는 예시를 알려줘
- service stage와 criticality tier를 혼동하면 lifecycle governance에서 어떤 문제가 생겨?
- 낮은 중요도 서비스에 과한 PRR을 줄이고 핵심 서비스에는 강한 evidence를 요구하려면 어떻게 설계해?
- criticality tier가 시간이 지나 바뀔 때 control profile을 재평가하는 운영 흐름을 설명해줘
contextual_chunk_prefix: |
  이 문서는 서비스의 business impact, dependency centrality, recovery urgency에 따라 criticality tier를 나누고 review, drill, rollout, on-call control intensity를 조정하는 advanced playbook이다.
---
# Service Criticality Tiering and Control Intensity

> 한 줄 요약: 모든 서비스를 같은 수준으로 review, on-call, PRR, drill, rollout gate에 태우면 비효율이 크므로, service criticality를 tier로 나누고 그에 맞는 control intensity를 정해야 lifecycle governance와 delivery speed가 함께 유지된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Portfolio Lifecycle Governance](./service-portfolio-lifecycle-governance.md)
> - [Operational Readiness Drills and Change Safety](./operational-readiness-drills-and-change-safety.md)
> - [Production Readiness Review](./production-readiness-review.md)
> - [SLA, SLO Ownership Model](./sla-slo-ownership-model.md)
> - [On-Call Ownership Boundaries](./on-call-ownership-boundaries.md)
> - [Support Operating Models: Self-Service, Office Hours, On-Call](./support-operating-models-self-service-office-hours-oncall.md)

> retrieval-anchor-keywords:
> - service criticality
> - criticality tier
> - control intensity
> - governance intensity
> - risk tier by service
> - operational rigor
> - service tiering
> - control profile

## 핵심 개념

서비스는 모두 운영 중일 수 있지만, 모두 같은 중요도를 갖지는 않는다.
그런데 governance와 readiness를 모든 서비스에 동일하게 적용하면 보통 두 가지가 생긴다.

- 핵심 서비스에는 기준이 약하다
- 중요도가 낮은 서비스에는 절차가 과하다

그래서 service criticality tiering은 서비스의 business impact, dependency centrality, recovery urgency에 따라 tier를 나누고,
각 tier마다 control intensity를 다르게 둔다.

예:

- tier 0: experimental / temporary
- tier 1: active but non-critical
- tier 2: important shared service
- tier 3: critical customer-facing path

즉 criticality는 우열이 아니라 **어떤 통제 강도를 적용할지 정하는 입력값**이다.

---

## 깊이 들어가기

### 1. criticality는 traffic보다 impact를 본다

호출량이 많다고 항상 critical한 것은 아니다.
반대로 낮은 traffic라도 실패 비용이 매우 큰 서비스가 있다.

봐야 할 것:

- revenue/customer impact
- legal/compliance risk
- blast radius
- manual workaround 가능성
- downstream dependency count

즉 criticality는 운영 현실의 위험 모델이다.

### 2. tier마다 control profile이 달라야 한다

예를 들어 다음이 달라질 수 있다.

- PRR required 여부
- rollout canary granularity
- readiness drill 주기
- on-call 강도
- SLO rigor
- exception approval level

핵심은 "더 중요한 서비스일수록 더 많은 문서"가 아니라,
**더 중요한 서비스일수록 더 강한 evidence와 safer default**를 요구하는 것이다.

### 3. stage와 criticality는 다른 축이다

temporary service도 매우 critical해질 수 있고,
active service라도 criticality는 낮을 수 있다.

그래서 portfolio stage와 criticality tier는 함께 관리해야 한다.

예:

- temporary + tier 0
- active + tier 1
- active + tier 3
- sunset + tier 2

이 구분이 있어야 lifecycle governance가 현실적이 된다.

### 4. control intensity는 시간이 지나며 바뀔 수 있다

criticality는 영구 레이블이 아니다.

예:

- pilot가 성공해 핵심 user flow에 붙음
- old shared service usage가 줄어 비중이 낮아짐
- new workaround가 생겨 recovery urgency가 낮아짐

그래서 tier도 periodic review와 incident data를 통해 재평가돼야 한다.

### 5. over-tiering과 under-tiering 둘 다 위험하다

너무 많은 tier는 관리가 어려워지고,
너무 적은 tier는 실제 차이를 못 담는다.

좋은 모델은 대개 소수 tier에 다음을 연결한다.

- control checklist
- required evidence
- escalation path
- policy gate strength

즉 tier는 분류 체계가 아니라 **운영 강도 프로파일**이어야 한다.

---

## 실전 시나리오

### 시나리오 1: 내부 admin 도구가 갑자기 중요해진다

호출량은 낮아도 사고 대응의 핵심이면 criticality를 올려야 한다.
그에 따라 on-call, audit, rollout gate도 강화해야 한다.

### 시나리오 2: 낮은 중요도 서비스에 PRR이 너무 무겁다

같은 양식과 승인 체계를 강요하면 delivery cost만 커진다.
tier 1 수준으로 가볍게 줄이는 편이 낫다.

### 시나리오 3: shared platform service가 사실상 tier 3다

사용자와 직접 붙지 않아도 blast radius가 크다면, customer-facing이 아니라고 낮은 tier에 두면 안 된다.

---

## 코드로 보기

```yaml
service_control_profile:
  service: feature-flag-control
  criticality_tier: 2
  controls:
    prr: required
    rollout: canary
    drill_frequency: quarterly
    oncall: 24x7
```

좋은 tiering 모델은 서비스 이름보다 control profile을 먼저 보여 준다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| uniform control | 운영이 단순하다 | 과잉/과소 통제가 동시에 생긴다 | 아주 작은 조직 |
| criticality tiering | 현실적이다 | 모델 정의가 필요하다 | 여러 서비스가 있을 때 |
| tier + evidence-based control | 속도와 안전의 균형이 좋다 | 운영 discipline이 필요하다 | 성숙한 조직 |

service criticality tiering의 목적은 계급을 만드는 것이 아니라, **서비스마다 다른 실패 비용을 control intensity에 정확히 반영하는 것**이다.

---

## 꼬리질문

- 이 서비스는 traffic이 아니라 impact 기준으로 몇 tier인가?
- stage와 criticality를 서로 혼동하고 있지 않은가?
- tier에 따라 PRR, drill, on-call, rollout gate가 실제로 달라지는가?
- 시간이 지나 criticality가 바뀌었는데 control profile은 그대로 남아 있지 않은가?

## 한 줄 정리

Service criticality tiering and control intensity는 서비스의 실패 비용과 중심성을 기준으로 tier를 나누고, 그에 맞는 review·readiness·rollout 강도를 적용하는 운영 모델이다.
