---
schema_version: 3
title: Policy Candidate Backlog Scoring and Priority
concept_id: software-engineering/policy-candidate-backlog
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
- backlog
- prioritization
- governance
aliases:
- Policy Candidate Backlog Scoring and Priority
- policy candidate backlog
- policy scoring
- policy prioritization matrix
- policy adoption queue
- guardrail candidate scoring
symptoms:
- policy 후보를 impact, readiness, friction, dependency unlock으로 나누지 않고 loudest request나 특정 개인 취향으로 adoption queue를 정해
- high impact지만 remediation/owner/metadata가 부족한 policy를 바로 enforcement로 보내거나, dependency unlocker policy를 낮게 평가해 후속 guardrail이 막혀
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/policy-as-code-adoption-order
- software-engineering/policy-as-code-rollout-stages
next_docs:
- software-engineering/platform-policy-override-governance
- software-engineering/override-burndown-exemption-debt
- software-engineering/incident-feedback-policy-ownership-closure
linked_paths:
- contents/software-engineering/policy-as-code-adoption-order-and-sequencing.md
- contents/software-engineering/policy-as-code-rollout-adoption-stages.md
- contents/software-engineering/policy-as-code-architecture-linting.md
- contents/software-engineering/incident-feedback-policy-ownership-closure.md
- contents/software-engineering/architecture-council-domain-stewardship-cadence.md
- contents/software-engineering/platform-policy-ownership-override-governance.md
- contents/software-engineering/override-burn-down-and-exemption-debt.md
confusable_with:
- software-engineering/policy-as-code-adoption-order
- software-engineering/policy-as-code-rollout-stages
- software-engineering/platform-policy-override-governance
forbidden_neighbors: []
expected_queries:
- policy candidate backlog을 impact, readiness, friction, dependency unlock 기준으로 scoring하는 방법을 알려줘
- high impact policy라도 readiness가 낮으면 prepare-next나 visibility-first로 보내야 하는 이유가 뭐야?
- ownership metadata required 같은 dependency enabler가 flashy rule보다 adoption queue 앞에 올 수 있는 이유는?
- policy priority와 rollout stage는 각각 무엇을 먼저 다룰지와 얼마나 강하게 적용할지를 어떻게 나눠?
- incident-driven policy와 platform baseline policy 후보를 backlog review에서 재평가하는 방법은?
contextual_chunk_prefix: |
  이 문서는 policy-as-code 후보를 impact, readiness, friction, dependency unlock으로 점수화해 adoption queue, rollout wave, next action을 정하는 advanced playbook이다.
---
# Policy Candidate Backlog Scoring and Priority

> 한 줄 요약: policy-as-code adoption order를 실제로 운영하려면 규칙 후보를 감으로 고르지 말고, impact, readiness, friction, dependency unlock을 함께 점수화해 adoption queue와 rollout wave를 정해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Policy as Code Adoption Order and Sequencing](./policy-as-code-adoption-order-and-sequencing.md)
> - [Policy as Code Rollout and Adoption Stages](./policy-as-code-rollout-adoption-stages.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Incident Feedback to Policy and Ownership Closure](./incident-feedback-policy-ownership-closure.md)
> - [Architecture Council and Domain Stewardship Cadence](./architecture-council-domain-stewardship-cadence.md)
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)
> - [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)

> retrieval-anchor-keywords:
> - policy candidate backlog
> - policy candidate backlog scoring
> - policy scoring
> - policy priority
> - policy prioritization matrix
> - policy adoption queue
> - policy adoption wave
> - governance backlog
> - guardrail candidate
> - incident-driven policy
> - dependency unlock policy
> - remediation cost
> - readiness friction scoring
> - policy backlog order

## 핵심 개념

조직에는 policy 후보가 항상 많다.

예:

- deprecated API 신규 사용 차단
- ownership metadata 필수화
- high-risk config staged rollout 강제
- contract drift pause rule

문제는 무엇부터 자동화할지 정하는 기준이 없으면, loudest request나 특정 개인 취향이 우선된다는 점이다.

그래서 policy candidate도 backlog로 보고 scoring하는 편이 좋다.

좋은 backlog scoring은 세 가지 질문에 답해야 한다.

- 이 규칙이 실제 위험을 얼마나 줄이는가
- 지금 조직이 이 규칙을 흡수할 준비가 되었는가
- 이 규칙이 다음 policy wave를 열어 주는 선행 조건인가

즉 이 문서는 [Policy as Code Adoption Order and Sequencing](./policy-as-code-adoption-order-and-sequencing.md)의 "어떤 순서로 갈 것인가"를, 후보 backlog 수준의 점수와 우선순위 규칙으로 풀어낸 것이다.

---

## 깊이 들어가기

### 1. priority는 impact, readiness, friction을 분리해서 본다

가장 흔한 실패는 중요도와 도입 가능성을 한 숫자에 섞어 버리는 것이다.
이러면 "매우 중요하지만 아직 준비 안 된 정책"과 "효과는 중간이지만 지금 바로 켤 수 있는 정책"이 구분되지 않는다.

보통은 다음 네 축으로 나누는 편이 실용적이다.

- impact: incident relevance, blast radius reduction, compliance exposure
- readiness: ownership, metadata/registry, remediation clarity
- friction: false-positive risk, exception pressure, rollout disruption
- dependency unlock: 이 규칙이 다른 policy를 가능하게 만드는가

핵심은 `impact가 높다`와 `지금 넣을 수 있다`를 분리하고, adoption order 관점에서 `unlocker인가`를 따로 보는 것이다.

### 2. scoring rubric은 1~5점보다 질문 정의가 더 중요하다

점수만 있으면 숫자 놀음이 되기 쉽다.
각 축에 대해 무엇을 물을지 먼저 고정해야 한다.

| 축 | 낮은 점수 | 높은 점수 | 대표 질문 |
|---|---|---|---|
| impact | 국소적 불편 감소 수준 | 반복 incident, 큰 blast radius, 강한 규제 리스크 감소 | "막으면 실제로 사고와 손실이 줄어드는가?" |
| readiness | owner 없음, metadata 없음, remediation 모호 | owner 명확, metadata 준비, 해결 경로 짧음 | "위반했을 때 바로 고칠 수 있는가?" |
| friction | false positive 높음, 예외 폭증 예상, 교육 비용 큼 | 판단 기준 명확, override 적음, 팀이 이해 가능 | "강제했을 때 shadow path가 늘지 않는가?" |
| dependency unlock | 단독 규칙 | 다른 guardrail 다수를 여는 기반 정책 | "이걸 먼저 해야 다음 정책이 쉬워지는가?" |

예를 들면 `ownership metadata required`는 직접적인 incident 감소 점수는 중간일 수 있지만, dependency unlock 점수가 높다.
반대로 `domain-specific business guardrail`은 impact 주장만 크고 readiness와 friction이 낮게 나올 수 있다.

### 3. adoption order는 flashy rule보다 dependency unlocker를 먼저 올린다

한쪽만 보면 왜곡된다.

정책 backlog에는 보통 네 종류의 후보가 섞여 들어온다.

- dependency-enabler: ownership metadata, criticality tier, lifecycle stage metadata
- platform baseline: observability baseline, forbidden import, required config profile
- incident-driven: 반복 사고에서 직접 도출된 차단 규칙
- lifecycle-driven: deprecation, sunset, migration close-out guardrail

adoption order에서는 보통 다음 순서를 권장한다.

- wave 1: objective하고 local하며 dependency unlock 성격이 있는 규칙
- wave 2: lifecycle, rollout, exception governance와 결합된 운영 규칙
- wave 3: business semantics가 강하고 팀 해석 차이가 큰 규칙

즉 backlog priority가 높은 후보여도, adoption wave는 뒤쪽일 수 있다.
이 구분이 없으면 "중요하니 지금 hard block"이라는 위험한 결론으로 튄다.

### 4. priority band는 next action까지 함께 가져가야 한다

backlog scoring의 목적은 순번표를 만드는 것이 아니라, 후보마다 다음 행동을 정하는 것이다.

실무에서는 보통 이렇게 나눈다.

| band | 조건 예시 | 다음 행동 |
|---|---|---|
| now | impact 높음, readiness 높음, friction 낮음 | [Policy as Code Rollout and Adoption Stages](./policy-as-code-rollout-adoption-stages.md)에 따라 visibility 또는 warning 진입 |
| prepare-next | impact 높음, readiness 부족 | owner/metadata/remediation gap 해소 |
| visibility-first | readiness는 충분하지만 friction이 불확실 | read-only 탐지와 false-positive 계측부터 시작 |
| hold | owner 없음, semantics 논쟁 큼, override debt 예상 | 문서화 후 cadence review에서 재평가 |

즉 score가 높다고 항상 바로 enforcement로 가는 것이 아니라, 어떤 준비 작업이 필요한지 backlog action이 붙어야 한다.

### 5. low score 후보를 버리는 것도 중요하다

정책 후보가 있다고 다 지금 해야 하는 것은 아니다.

예:

- domain semantics 논쟁이 심함
- remediation path가 없음
- owner가 없음
- override path만 폭증할 가능성이 큼

이런 후보는 문서화만 해 두고 나중에 재평가하는 편이 낫다.

여기서 중요한 것은 "정책이 틀렸다"가 아니라 "지금 queue 앞에 두면 안 된다"를 분명히 구분하는 것이다.

### 6. score는 정적이 아니라 재평가 대상이다

incident가 나거나 metadata가 정리되면 score가 바뀔 수 있다.
그래서 cadence review가 필요하다.

예:

- ownership metadata 정비 후 adoption feasibility 상승
- repeated incident 후 urgency 상승
- platform UX 개선 후 friction 감소

보통 backlog review 때는 score 변화 원인을 함께 기록하는 편이 좋다.

- 왜 impact가 올라갔는가
- readiness를 올리기 위해 어떤 선행 작업이 끝났는가
- friction을 낮춘 UX/doc/tooling 개선이 있었는가

### 7. backlog와 rollout stage를 연결해야 한다

priority가 높아도 바로 hard block으로 가는 것은 아니다.
backlog priority는 rollout stage와 함께 봐야 한다.

즉:

- high priority + high readiness -> warning/soft block 진입
- high priority + low readiness -> visibility only
- low priority + high complexity -> backlog hold

즉 `priority`는 무엇을 먼저 다룰지, `stage`는 얼마나 강하게 적용할지를 나타낸다.

---

## 실전 시나리오

### 시나리오 1: ownership metadata policy가 flashy policy보다 먼저 온다

ownership metadata 강제는 직접적인 incident 차단처럼 보이지 않아도, 이후 escalation policy, deprecation policy, criticality-based rollout policy를 여는 기반이다.
그래서 dependency unlock 점수 때문에 queue 앞쪽으로 갈 수 있다.

### 시나리오 2: incident 뒤에 다들 policy를 하나씩 제안한다

이럴수록 scoring이 필요하다.
바로 구현하지 말고 impact와 readiness를 분리해서 본다.
반복 사고와 직접 연결되더라도 remediation path가 없으면 `prepare-next`로 보내는 편이 낫다.

### 시나리오 3: platform team이 baseline policy를 계속 늘린다

incident relevance가 낮고 friction만 큰 후보는 backlog 뒤로 미뤄야 한다.

### 시나리오 4: deprecation block policy가 갑자기 가능해진다

registry와 stage metadata가 갖춰지면 dependency readiness가 올라가 priority가 급상승할 수 있다.

---

## 코드로 보기

```yaml
policy_backlog:
  scoring_formula: impact + readiness + dependency_unlock - friction
  candidates:
    - id: ownership_metadata_required
      type: dependency_enabler
      impact: 4
      readiness: 5
      friction: 1
      dependency_unlock: 3
      priority_score: 11
      adoption_wave: wave_1
      next_action: warning_stage
    - id: block_new_consumers_for_deprecated_api
      type: lifecycle_guardrail
      impact: 5
      readiness: 4
      friction: 2
      dependency_unlock: 2
      priority_score: 9
      adoption_wave: wave_1
      next_action: visibility_stage
    - id: domain_specific_fallback_semantics
      type: business_semantic_guardrail
      impact: 3
      readiness: 2
      friction: 4
      dependency_unlock: 0
      priority_score: 1
      adoption_wave: wave_3
      next_action: hold_and_revisit
```

좋은 backlog는 규칙의 옳고 그름보다 지금 할 가치, 준비도, 그리고 sequencing상 위치를 같이 보여 준다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| ad-hoc 후보 선정 | 빠르다 | 우선순위가 흔들린다 | 초기 |
| scored backlog | 일관성이 높다 | scoring 기준 합의가 필요하다 | 여러 후보가 있을 때 |
| scored backlog + adoption wave | 도입 순서가 안정적이다 | unlocker를 먼저 챙겨야 한다 | policy-as-code 확장기 |
| scored backlog + cadence review | 학습이 반영된다 | 운영 discipline이 필요하다 | 성숙한 governance 운영 |

policy candidate backlog scoring의 목적은 관료화를 늘리는 것이 아니라, **guardrail 도입 순서를 논쟁 대신 더 명시적인 판단으로 바꾸는 것**이다.

---

## 꼬리질문

- 이 policy는 중요한가, 지금 가능한가, 다음 wave를 여는 기반인가?
- impact와 readiness를 한 숫자로 뭉개고 있지는 않은가?
- dependency unlocker 정책이 flashy policy보다 뒤로 밀리고 있지는 않은가?
- low score 후보를 보류하는 기준과 재평가 cadence가 있는가?
- priority와 rollout stage가 분리돼 관리되고 있는가?

## 한 줄 정리

Policy candidate backlog scoring and priority는 policy-as-code 후보를 impact, readiness, friction, dependency unlock 기준으로 정리해, 어떤 guardrail을 어느 adoption wave와 rollout stage로 보낼지 더 일관되게 결정하는 방식이다.
