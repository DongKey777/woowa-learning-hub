---
schema_version: 3
title: Migration Scorecards
concept_id: software-engineering/migration-scorecards
canonical: true
category: software-engineering
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- migration
- scorecard
- readiness
- cutover
aliases:
- Migration Scorecards
- migration readiness scorecard
- cutover score
- wave exit criteria metrics
- shadow diff adoption scorecard
- migration risk dashboard
symptoms: []
intents:
- comparison
- design
- troubleshooting
prerequisites:
- software-engineering/migration-wave-governance
- software-engineering/consumer-migration-playbook
next_docs:
- software-engineering/migration-stop-loss-governance
- software-engineering/strangler-verification-shadow-traffic-metrics
- software-engineering/data-migration-cutover
linked_paths:
- contents/software-engineering/strangler-fig-migration-contract-cutover.md
- contents/software-engineering/strangler-verification-shadow-traffic-metrics.md
- contents/software-engineering/consumer-migration-playbook-contract-adoption.md
- contents/software-engineering/brownfield-strangler-org-model.md
- contents/software-engineering/backward-compatibility-test-gates.md
- contents/software-engineering/data-migration-rehearsal-reconciliation-cutover.md
- contents/software-engineering/migration-wave-governance-decision-rights.md
- contents/software-engineering/migration-stop-loss-scope-reduction-governance.md
confusable_with:
- software-engineering/migration-wave-governance
- software-engineering/consumer-migration-playbook
- software-engineering/migration-stop-loss-governance
forbidden_neighbors: []
expected_queries:
- migration scorecard는 무엇을 보고 다음 wave나 cutover를 판단하는 운영 도구인지 설명해줘
- consumer adoption, shadow diff rate, contract coverage, rollback readiness를 scorecard로 어떻게 묶어?
- migration scorecard와 wave governance, consumer playbook, stop-loss 문서는 각각 어떤 질문에 답해?
- scorecard 숫자가 나쁠 때 fix and recompare, communication 강화, rollback runbook 보강 같은 행동으로 연결하는 방법은?
- migration 후반에는 deprecation progress와 retirement readiness를 scorecard에 어떻게 추가해야 해?
contextual_chunk_prefix: |
  이 문서는 migration readiness, risk, adoption, shadow diff, rollback readiness를 scorecard로 정량화해 wave exit와 cutover 판단을 돕는 advanced chooser이다.
---
# Migration Scorecards

> 한 줄 요약: `이 전환이 지금 얼마나 준비됐는지 어떤 숫자로 보죠?`처럼 상태 판단 기준이 흐릴 때 먼저 보는 문서로, migration scorecard를 준비도와 위험도를 함께 점수화하는 운영 도구로 정리한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Strangler Verification, Shadow Traffic Metrics](./strangler-verification-shadow-traffic-metrics.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [Brownfield Strangler Org Model](./brownfield-strangler-org-model.md)
> - [Backwards Compatibility Test Gates](./backward-compatibility-test-gates.md)
> - [Data Migration Rehearsal, Reconciliation, Cutover](./data-migration-rehearsal-reconciliation-cutover.md)
> - [Migration Wave Governance and Decision Rights](./migration-wave-governance-decision-rights.md)

> retrieval-anchor-keywords:
> - migration scorecard
> - migration readiness
> - cutover score
> - consumer readiness
> - shadow diff
> - rollback readiness
> - adoption progress
> - migration risk
> - migration wave
> - wave exit criteria

## 먼저 이 문서가 맞는 질문인지

scorecard 문서는 `누가 결정하나`보다 `무엇을 보고 결정하나`에 답한다.

| 지금 막힌 질문 | 먼저 볼 문서 | 이 문서가 아닌 이유 |
|---|---|---|
| `전환 준비도를 어떤 숫자로 보죠?`, `exit criteria를 대시보드로 보고 싶어요` | 이 문서 | 없음 |
| `누가 다음 wave 승인해요?`, `누가 pause authority예요?` | [Migration Wave Governance and Decision Rights](./migration-wave-governance-decision-rights.md) | 권한 설계가 핵심이다 |
| `consumer를 어떤 순서로 옮겨요?` | [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md) | rollout 순서/협업 계획이 핵심이다 |
| `지금 계속할지 scope를 줄일지` | [Migration Stop-Loss and Scope Reduction Governance](./migration-stop-loss-scope-reduction-governance.md) | portfolio-level stop rule이 핵심이다 |

- 짧게 외우면 `scorecard = 상태 숫자`, `governance = 권한`, `playbook = 순서`, `stop-loss = 중단/축소 기준`이다.

## 핵심 개념

전환 작업은 길고 복잡해서 "느낌상 괜찮다"로 판단하면 위험하다.
scorecard는 전환의 상태를 몇 개의 축으로 나눠, 준비도와 위험을 동시에 보여준다.

예:

- consumer adoption
- shadow diff rate
- contract test coverage
- rollback readiness
- observability readiness
- deprecated path usage
- reconciliation diff rate

즉 scorecard는 migration의 **건강검진표**다.

---

## 깊이 들어가기

### 1. scorecard는 전환의 진행과 안전을 동시에 본다

진행도만 보면 너무 낙관적일 수 있다.
안전만 보면 전환이 안 끝난다.

둘 다 봐야 한다.

### 2. 항목은 행동으로 연결돼야 한다

점수만 있고 다음 행동이 없으면 의미가 없다.

예:

- shadow diff 높음 -> fix and recompare
- consumer adoption 낮음 -> communication 강화
- rollback readiness 낮음 -> runbook 보강
- rehearsal 시간 초과 -> cutover plan 재설계

### 3. scorecard는 팀 간 공용 언어가 된다

전환은 여러 팀이 함께 움직인다.

scorecard가 있으면:

- 제품 팀은 채택률을 본다
- 플랫폼 팀은 안정성을 본다
- 운영 팀은 rollback과 observability를 본다

### 4. scorecard는 정적이어선 안 된다

초기와 후반 전환에서 보는 축이 다를 수 있다.

초기:

- readiness
- ownership
- shadow compare

후반:

- adoption
- deprecation progress
- retirement readiness

### 5. scorecard는 registry와 연동해야 한다

소비자, 계약, 서비스 소유권과 연결되지 않으면 scorecard는 숫자만 남는다.

---

## 실전 시나리오

### 시나리오 1: API를 새 버전으로 옮긴다

scorecard로 채택률과 실패율을 같이 본다.

### 시나리오 2: 레거시를 strangler로 잘라낸다

deprecation path 사용량과 shadow diff를 같이 본다.

### 시나리오 3: 전환이 오래 걸린다

scorecard가 없으면 어디가 막혔는지 모른다.

---

## 코드로 보기

```yaml
migration_scorecard:
  consumer_adoption: 72
  shadow_diff_rate: 0.4
  rollback_ready: true
  deprecation_usage: 18
```

scorecard는 현황판이 아니라 **의사결정 도구**여야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 감 기반 판단 | 빠르다 | 오판하기 쉽다 | 매우 작은 전환 |
| scorecard | 상태가 보인다 | 설계가 필요하다 | 큰 전환 |
| scorecard + gates | 실행까지 연결된다 | 운영이 복잡하다 | 고위험 migration |

migration scorecard는 전환의 진척과 위험을 함께 보는 **정량화된 운영 표**다.

---

## 꼬리질문

- 어떤 지표가 전환 성공을 말하는가?
- 어떤 점수면 rollout을 멈춰야 하는가?
- scorecard는 누가 업데이트하는가?
- 후반 전환에 맞춰 항목을 바꿀 것인가?

## 다음 읽기

- [Migration Wave Governance and Decision Rights](./migration-wave-governance-decision-rights.md): scorecard 숫자를 실제 advance/pause 권한과 연결할 때 읽는다.
- [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md): consumer adoption 지표를 rollout 순서와 fallback 계획으로 풀어낸다.
- [Migration Stop-Loss and Scope Reduction Governance](./migration-stop-loss-scope-reduction-governance.md): scorecard가 계속 나빠질 때 어떤 조건에서 방향을 바꿀지 본다.

## 한 줄 정리

Migration scorecards는 전환의 진행도와 안전성을 정량화해, cutover와 deprecation의 판단을 돕는 운영 도구다.
