---
schema_version: 3
title: Policy as Code Rollout and Adoption Stages
concept_id: software-engineering/policy-as-code-rollout-stages
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- policy-as-code
- rollout
- adoption-stage
- guardrail
aliases:
- Policy as Code Rollout and Adoption Stages
- policy rollout stages
- visibility warning soft block hard block
- policy adoption stage
- lint adoption rollout
- policy soft block hard block
symptoms:
- 새 policy를 visibility나 warning 없이 바로 hard block으로 걸어 false positive와 delivery outage를 만들거나, 반대로 warning만 계속 유지해 행동 변화가 없어
- remediation guide, owner contact, grace period, override path, stage 승격 기준 없이 policy rollout을 운영해 팀이 규칙을 신뢰하지 못해
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/policy-as-code
- software-engineering/platform-policy-override-governance
next_docs:
- software-engineering/policy-as-code-adoption-order
- software-engineering/policy-candidate-backlog
- software-engineering/rollout-guardrail-profiles
linked_paths:
- contents/software-engineering/policy-as-code-architecture-linting.md
- contents/software-engineering/platform-policy-ownership-override-governance.md
- contents/software-engineering/architecture-council-domain-stewardship-cadence.md
- contents/software-engineering/rollout-guardrail-profiles-auto-pause-resume.md
- contents/software-engineering/incident-feedback-policy-ownership-closure.md
- contents/software-engineering/policy-candidate-backlog-scoring-and-priority.md
confusable_with:
- software-engineering/policy-as-code-adoption-order
- software-engineering/policy-candidate-backlog
- software-engineering/rollout-guardrail-profiles
forbidden_neighbors: []
expected_queries:
- policy as code를 visibility, warning, soft block, hard block 단계로 rollout하는 전략을 알려줘
- false positive ratio, override rate, training 완료 같은 stage 승격 기준은 어떻게 잡아?
- warning 단계는 단순 알림이 아니라 remediation guide와 owner support가 필요한 이유가 뭐야?
- soft block은 break-glass나 explicit override를 가진 통제로 언제 쓰는지 설명해줘
- hard block 전에 policy owner, override governance, telemetry, escalation path가 준비돼야 하는 이유는?
contextual_chunk_prefix: |
  이 문서는 policy-as-code를 visibility, warning, soft block, hard block adoption stage로 rollout해 false positive와 override debt를 줄이는 advanced playbook이다.
---
# Policy as Code Rollout and Adoption Stages

> 한 줄 요약: policy as code는 규칙을 한 번에 fail-close로 밀어붙이는 것이 아니라, visibility, warning, soft block, hard block 같은 adoption stage를 거치며 false positive와 override debt를 줄이는 rollout 전략이 필요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)
> - [Architecture Council and Domain Stewardship Cadence](./architecture-council-domain-stewardship-cadence.md)
> - [Rollout Guardrail Profiles, Auto-Pause, and Manual Resume](./rollout-guardrail-profiles-auto-pause-resume.md)
> - [Incident Feedback to Policy and Ownership Closure](./incident-feedback-policy-ownership-closure.md)
> - [Policy Candidate Backlog Scoring and Priority](./policy-candidate-backlog-scoring-and-priority.md)

> retrieval-anchor-keywords:
> - policy as code rollout
> - policy adoption stage
> - visibility mode
> - warning mode
> - soft block
> - hard block
> - policy rollout
> - lint adoption

## 핵심 개념

policy as code가 맞는 방향이어도, 처음부터 hard fail로 걸면 조직이 쉽게 반발한다.
반대로 계속 warning만 주면 실제 행동 변화가 없다.

그래서 실무에서는 보통 adoption stage를 둔다.

- visibility
- warning
- soft block
- hard block

즉 policy rollout은 규칙 작성보다 **조직이 규칙을 흡수하는 단계 설계**가 더 중요하다.

---

## 깊이 들어가기

### 1. visibility 단계는 규칙 정확도를 먼저 본다

초기에는 policy를 fail시키지 않고, 어디서 얼마나 위반되는지 본다.

봐야 할 것:

- 위반 volume
- false positive ratio
- 어떤 팀/서비스에 집중되는가
- 자동 수정 가능한가

이 단계가 없으면 규칙이 현실을 잘못 모델링한 채 강제될 수 있다.

### 2. warning 단계는 학습과 지원을 붙여야 한다

warning만 띄우고 끝내면 무시되기 쉽다.
보통 필요한 것:

- remediation guide
- owner/team contact
- grace period
- exception path

즉 warning은 알림이 아니라 **전환 준비 단계**다.

### 3. soft block은 break-glass를 가진 통제다

soft block은 기본적으로 막지만, 명시적 승인이나 override로 지나갈 수 있다.
이 단계는 다음에 유용하다.

- migration transition
- high-friction new policy
- false positive가 아직 완전히 정리 안 된 경우

즉 soft block은 강한 메시지를 주면서도 조직 충격을 줄인다.

### 4. hard block은 owner/support 체계가 준비된 뒤에 와야 한다

hard block 전에 최소한 다음이 있어야 한다.

- policy owner
- override governance
- remediation documentation
- adoption telemetry
- agreed escalation path

없으면 hard block은 guardrail이 아니라 delivery outage가 될 수 있다.

### 5. stage 승격 기준이 있어야 한다

언제 visibility -> warning -> soft block -> hard block으로 올릴지 정해야 한다.

예:

- false positive < 2%
- override rate 감소
- affected teams training 완료
- repeated incident와의 상관성 확인

즉 policy rollout도 일종의 product rollout이다.

---

## 실전 시나리오

### 시나리오 1: deprecated API 신규 사용 금지 정책을 도입한다

처음엔 visibility로 어디서 위반되는지 보고, 이후 warning과 soft block을 거쳐 hard block으로 전환한다.

### 시나리오 2: high-risk config staged rollout 정책을 도입한다

운영팀이 처음엔 불편해할 수 있으므로, early visibility와 example remediation이 필요하다.

### 시나리오 3: boundary rule이 특정 도메인에서만 많이 깨진다

이 경우 조직 교육보다 rule scope 자체를 조정하거나 migration runway를 먼저 깔아야 할 수 있다.

---

## 코드로 보기

```yaml
policy_rollout:
  rule: block_new_consumers_for_deprecated_api
  current_stage: warning
  next_stage: soft_block
  advance_if:
    false_positive_rate: "< 2%"
    override_rate_trend: down
```

좋은 policy rollout은 rule text보다 stage progression이 명확하다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| immediate hard block | 강제력이 크다 | 반발과 false positive 충격이 크다 | 이미 성숙한 규칙 |
| staged rollout | 현실적이다 | 시간이 든다 | 대부분의 새 policy |
| warning only | 마찰이 적다 | 행동 변화가 약하다 | 초기 탐색 |

policy as code rollout의 핵심은 규칙을 빨리 켜는 것이 아니라, **규칙이 조직 안에서 신뢰받는 통제로 자리 잡게 만드는 것**이다.

---

## 꼬리질문

- 이 policy는 지금 visibility, warning, soft block, hard block 중 어디에 있는가?
- stage를 올릴 근거 지표가 있는가?
- remediation과 override path 없이 block부터 걸고 있지는 않은가?
- rule adoption과 incident reduction이 실제로 연결되는가?

## 한 줄 정리

Policy as code rollout and adoption stages는 규칙을 한 번에 강제하지 않고, 관측-학습-제한-강제의 단계를 거쳐 조직이 guardrail을 흡수하게 만드는 운영 전략이다.
