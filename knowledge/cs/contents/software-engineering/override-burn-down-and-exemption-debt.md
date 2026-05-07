---
schema_version: 3
title: Override Burn-Down and Exemption Debt
concept_id: software-engineering/override-burndown-exemption-debt
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- override
- exemption
- waiver
- governance-debt
aliases:
- Override Burn-Down and Exemption Debt
- override burn down
- exemption debt
- waiver debt
- exception backlog
- override aging burn-down
symptoms:
- 만료일 없는 override, 반복 owner의 예외, permanent exemption, migration 끝났는데도 남은 waiver가 registry 없이 흩어져 있어
- override count만 줄이고 왜 생겼는지, 왜 오래 남는지, 어떤 policy나 platform UX를 바꿔야 다시 안 생기는지 보지 않아
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/platform-policy-override-governance
- software-engineering/consumer-exception-state-machine
next_docs:
- software-engineering/override-burndown-scorecards
- software-engineering/migration-stop-loss-governance
- software-engineering/architecture-exception-process
linked_paths:
- contents/software-engineering/platform-policy-ownership-override-governance.md
- contents/software-engineering/backward-compatibility-waiver-consumer-exception-governance.md
- contents/software-engineering/migration-stop-loss-scope-reduction-governance.md
- contents/software-engineering/architecture-exception-process.md
- contents/software-engineering/service-portfolio-lifecycle-governance.md
- contents/software-engineering/consumer-exception-state-machine-review-cadence.md
- contents/software-engineering/override-burndown-review-cadence-scorecards.md
confusable_with:
- software-engineering/platform-policy-override-governance
- software-engineering/consumer-exception-model
- software-engineering/migration-stop-loss-governance
forbidden_neighbors: []
expected_queries:
- override와 exemption을 age, scope, repeated owner, exit condition 기준으로 burn-down debt로 관리하는 방법은?
- compatibility waiver, policy override, migration exemption은 닫는 전략이 어떻게 달라?
- repeated override owner가 개인 문제가 아니라 policy, runway, ownership boundary, platform UX 문제일 수 있는 이유가 뭐야?
- override registry에는 owner, created_at, expires_at, compensating control, exit condition을 왜 남겨야 해?
- override burn-down은 count 줄이기가 아니라 governance health improvement라는 의미를 설명해줘
contextual_chunk_prefix: |
  이 문서는 override와 exemption을 age, repeated owner, scope, exit condition이 있는 governance debt로 보고 registry와 burn-down cadence로 회수하는 advanced playbook이다.
---
# Override Burn-Down and Exemption Debt

> 한 줄 요약: override와 exemption은 필요하지만 쌓여 두면 policy와 migration과 deprecation을 모두 느리게 만들기 때문에, age, scope, repeated owner, exit condition을 기준으로 burn-down 대상 부채로 관리해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)
> - [Backward Compatibility Waivers and Consumer Exception Governance](./backward-compatibility-waiver-consumer-exception-governance.md)
> - [Migration Stop-Loss and Scope Reduction Governance](./migration-stop-loss-scope-reduction-governance.md)
> - [Architecture Exception Process](./architecture-exception-process.md)
> - [Service Portfolio Lifecycle Governance](./service-portfolio-lifecycle-governance.md)
> - [Consumer Exception State Machine and Review Cadence](./consumer-exception-state-machine-review-cadence.md)
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)

> retrieval-anchor-keywords:
> - override burn down
> - exemption debt
> - waiver debt
> - exception backlog
> - override aging
> - exemption registry
> - debt burn down
> - override closure

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Override Burn-Down and Exemption Debt](./README.md#override-burn-down-and-exemption-debt)
> - 다음 단계: [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)

## 핵심 개념

override는 예외적이어야 하지만, 실제 조직에서는 점점 쌓인다.
문제는 이 override가 각각은 작아 보여도 전체적으로는 governance drift를 만든다는 점이다.

대표적 증상:

- 만료일 없는 override
- 같은 팀의 반복 예외
- 이유가 불명확한 permanent exemption
- migration 끝났는데도 안 닫힌 waiver

즉 override는 허용 여부보다 **언제 어떻게 태워 없앨지**가 중요하다.

---

## 깊이 들어가기

### 1. override는 나이(age)만으로도 위험 신호가 된다

오래된 override는 보통 세 가지 중 하나다.

- 아무도 닫을 책임을 안 짐
- 사실상 permanent support가 됨
- 원래 정책이나 구조가 잘못됨

그래서 override age는 대표적인 burn-down 우선순위 기준이다.

### 2. repeated override owner는 구조 문제 신호일 수 있다

항상 같은 팀이나 같은 서비스만 예외를 요청한다면, 개인 문제가 아니라 다음을 의심해야 한다.

- policy가 현실과 안 맞음
- migration runway가 부족함
- ownership boundary가 어긋남
- platform control plane DX가 나쁨

즉 burn-down은 individual cleanup이 아니라 **패턴 분석**이기도 하다.

### 3. burn-down은 registry와 cadence가 있어야 한다

override를 이슈 티켓에만 흩어 놓으면 전체 규모가 안 보인다.

필요한 것:

- exemption registry
- owner
- created_at / expires_at
- compensating control
- exit condition
- burn-down review cadence

이 구조가 있어야 override debt를 portfolio처럼 볼 수 있다.

### 4. burn-down 전략은 유형별로 달라야 한다

예:

- compatibility waiver: consumer migration 완료
- policy override: rule scope 조정 또는 remediation 완료
- migration exemption: wave exit 또는 stop-loss decision
- permanent carve-out: explicit reclassification

모든 override를 동일한 check list로 닫으려 하면 실패한다.

### 5. burn-down 목표는 숫자 줄이기보다 구조 개선이다

override count만 줄이면 안 된다.
정말 중요한 건 다음이다.

- 왜 생겼는가
- 왜 오래 남는가
- 무엇을 바꾸면 다시 안 생기는가

즉 burn-down은 cleanup sprint가 아니라 **governance health improvement**다.

---

## 실전 시나리오

### 시나리오 1: deprecated API waiver가 계속 연장된다

이건 consumer inertia일 수도 있지만, replacement path가 실제로 어렵거나 support contract가 약한 문제일 수 있다.

### 시나리오 2: 특정 policy override가 20개 이상 쌓였다

이 경우 각 override를 하나씩 비난할 것이 아니라, rule scope와 platform UX를 먼저 다시 봐야 한다.

### 시나리오 3: migration exemption이 많아 전환이 안 끝난다

burn-down review 없이 migration scorecard만 봐서는 왜 안 끝나는지 알기 어렵다.

---

## 코드로 보기

```yaml
override_registry:
  - id: ex-204
    type: policy_override
    owner: growth-team
    age_days: 74
    exit_condition: migrate_to_staged_rollout
    burn_down_priority: high
```

좋은 registry는 override가 왜 아직 살아 있는지 설명해야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| override만 기록 | 최소 관리다 | debt가 회수되지 않는다 | 초기 |
| age-based burn-down | 오래된 debt를 보인다 | 원인 분석이 부족할 수 있다 | 기본 모델 |
| pattern-based burn-down | 구조 문제를 잡는다 | 운영 분석이 필요하다 | 성숙 조직 |

override burn-down의 목적은 예외를 부끄럽게 만드는 것이 아니라, **예외를 계속 필요로 만드는 구조를 드러내고 줄이는 것**이다.

---

## 꼬리질문

- 가장 오래된 override는 왜 아직 살아 있는가?
- repeated override owner가 있다면 개인이 아니라 구조 문제 아닌가?
- exit condition 없이 살아 있는 exemption이 몇 개인가?
- burn-down 결과가 policy 변경과 migration planning으로 이어지는가?

## 한 줄 정리

Override burn-down and exemption debt는 예외를 개별 허용건이 아니라 age와 패턴과 exit condition을 가진 조직 부채로 보고 체계적으로 회수하는 운영 방식이다.
