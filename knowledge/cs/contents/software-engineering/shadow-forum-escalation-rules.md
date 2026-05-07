---
schema_version: 3
title: Shadow Forum Escalation Rules
concept_id: software-engineering/shadow-forum-escalation-rules
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- shadow-process
- escalation
- architecture-council
- stewardship
aliases:
- shadow forum escalation rules
- local stewardship vs architecture council
- blocked shadow escalation
- shadow governance routing
- council escalation threshold
- shadow 포럼 에스컬레이션 규칙
symptoms:
- 모든 shadow entry를 architecture council로 올려 governance 병목을 만들거나 high-blast 항목을 local forum이 너무 오래 붙잡아
- blocked_duration, impacted_domains, affected_teams, shared control plane change 같은 escalation threshold와 clock이 없어 ownerless backlog가 늙어
- council escalation packet에 blast radius와 requested action이 없어 상위 forum이 다시 사실 수집부터 하게 돼
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/architecture-council-cadence
- software-engineering/shadow-catalog-review-cadence-profiles
next_docs:
- software-engineering/shadow-catalog-lifecycle-states
- software-engineering/shadow-review-packet-template
- software-engineering/shadow-review-outcome-template
linked_paths:
- contents/software-engineering/architecture-council-domain-stewardship-cadence.md
- contents/software-engineering/shadow-catalog-review-cadence-profiles.md
- contents/software-engineering/shadow-catalog-lifecycle-states.md
- contents/software-engineering/shadow-review-packet-template.md
- contents/software-engineering/shadow-review-outcome-template.md
- contents/software-engineering/shadow-process-catalog-entry-schema.md
- contents/software-engineering/shadow-process-officialization-absorption-criteria.md
- contents/software-engineering/shadow-lifecycle-scorecard-metrics.md
- contents/software-engineering/shadow-temporary-hold-exit-criteria.md
- contents/software-engineering/support-sla-escalation-contracts.md
- contents/software-engineering/break-glass-path-segmentation.md
confusable_with:
- software-engineering/architecture-council-cadence
- software-engineering/shadow-catalog-review-cadence-profiles
- software-engineering/support-sla-escalation-contracts
forbidden_neighbors: []
expected_queries:
- shadow entry를 local stewardship에 남길지 architecture council로 올릴지 어떤 threshold와 clock으로 정해?
- blocked_duration이 5영업일을 넘거나 impacted_domains가 2개 이상이면 council_next_cycle로 올리는 이유는?
- high-blast release approval, deprecation bypass, shared source of truth shadow path는 왜 council_immediate가 필요해?
- shadow escalation packet에는 catalog_id, lifecycle_state, blocked_since, affected_teams, requested_council_action을 왜 넣어야 해?
- council escalation이 윗선 보고가 아니라 decision owner와 decision height를 바꾸는 state transition인 이유를 설명해줘
contextual_chunk_prefix: |
  이 문서는 shadow entry를 local stewardship forum과 architecture council 사이에서 authority boundary, blocked duration, blast radius, shared dependency 기준으로 라우팅하는 advanced escalation playbook이다.
---
# Shadow Forum Escalation Rules

> 한 줄 요약: shadow entry는 모두 architecture council로 올리는 것이 아니라, local stewardship forum이 끝낼 수 있는 범위를 먼저 고정하고, `blocked_duration`, `impacted_domains`, `affected_teams`, `shared-control-plane change`, `missed unblock ETA` 같은 threshold를 넘는 항목만 정해진 clock으로 council에 올려야 backlog orphan과 governance 병목을 동시에 줄일 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Architecture Council and Domain Stewardship Cadence](./architecture-council-domain-stewardship-cadence.md)
> - [Shadow Catalog Review Cadence Profiles](./shadow-catalog-review-cadence-profiles.md)
> - [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)
> - [Shadow Review Packet Template](./shadow-review-packet-template.md)
> - [Shadow Review Outcome Template](./shadow-review-outcome-template.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)
> - [Shadow Lifecycle Scorecard Metrics](./shadow-lifecycle-scorecard-metrics.md)
> - [Temporary Hold Exit Criteria](./shadow-temporary-hold-exit-criteria.md)
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)
> - [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)

> retrieval-anchor-keywords:
> - shadow forum escalation rules
> - local stewardship vs architecture council
> - shadow escalation threshold
> - blocked shadow escalation
> - high blast radius shadow entry
> - shadow governance routing
> - stewardship forum escalation clock
> - architecture council escalation clock
> - blocked_duration threshold
> - impacted_domains affected_teams
> - shared control plane change
> - missed unblock eta
> - shadow escalation packet
> - shadow review forum handoff
> - shadow governance red line
> - escalation class immediate next cycle
> - blocked orphan council escalation
> - release override shadow council
> - cutover shadow escalation
> - deprecation bypass shadow escalation

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Shadow Forum Escalation Rules](./README.md#shadow-forum-escalation-rules)
> - 다음 단계: [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)

## 핵심 개념

local stewardship forum의 목적은 shadow backlog를 빠르게 소화하는 것이다.
architecture council의 목적은 shared standard, cross-domain risk, portfolio-level unblock을 다루는 것이다.

문제는 둘 사이 경계가 "느낌상 위험해 보이면 올린다"로 남을 때 생긴다.

- local forum은 high-blast 항목을 오래 붙잡고
- council은 로컬 항목까지 떠안아 병목이 되고
- `blocked` entry는 owner 없는 orphan backlog로 늙는다

그래서 shadow governance에는 escalation reason이 아니라 **escalation threshold와 clock**이 필요하다.

핵심 질문은 단순하다.

- 이 항목이 아직 local stewardship authority 안에 있는가?
- 아니면 clock, blast radius, shared dependency 중 하나가 이미 council 범위로 넘어갔는가?

즉 forum escalation rule은 회의 예절이 아니라 **decision routing contract**다.

---

## 깊이 들어가기

### 1. local stewardship이 끝낼 수 있는 범위를 먼저 고정한다

아래 조건을 모두 만족하면 local stewardship forum이 계속 owner로 남아도 된다.

| 판정 축 | local stewardship 유지 조건 | council로 올려야 하는 방향 |
|---|---|---|
| 영향 범위 | `impacted_domains == 1` | `impacted_domains >= 2` |
| 팀 확산 | 같은 shadow path를 쓰는 팀이 `1개 팀` | `affected_teams >= 3` 또는 서로 다른 stewardship forum 2개 이상 |
| blocker 성격 | 로컬 팀이 푸는 execution blocker | shared platform, registry, audit, policy 변경 필요 |
| unblock clock | `1 영업일` 안에 `blocker_owner`와 ETA가 있다 | `1 영업일` 안에 owner 또는 ETA가 없다 |
| duration | unblock 예상이 `5 영업일` 이내다 | `blocked_duration > 5 영업일` |
| rollback 범위 | 같은 forum 권한 안에서 되돌릴 수 있다 | rollback이나 cutover가 다른 도메인 승인 없이는 안 된다 |

중요한 점은 "중요해 보여서 council"이 아니라, **authority boundary를 넘는 순간 council**이라는 것이다.

### 2. escalation은 `local_keep`, `council_next_cycle`, `council_immediate` 세 단계로 나누는 편이 안정적이다

| escalation class | 언제 쓰는가 | forum clock |
|---|---|---|
| `local_keep` | single-domain, short-lived, owner/ETA가 명확한 blocker | 기존 local stewardship cadence 유지 |
| `council_next_cycle` | shared dependency가 보이거나 `blocked_duration > 5 영업일`인 항목 | `다음 council slot`, 가능하면 `5 영업일` 이내 |
| `council_immediate` | high-blast-radius, production gate, compliance/audit bypass, ownerless red-risk blocker | `당일` 또는 `1 영업일` 이내 |

이 세 단계를 분리하면 local forum은 불필요한 과잉 escalation을 줄이고,
council은 정말 빨리 받아야 할 안건을 agenda 맨 앞으로 올릴 수 있다.

### 3. `blocked`는 age bucket만이 아니라 quality gate로 escalation한다

`blocked` entry는 오래된 것보다 **누가 언제 풀 것인지가 없는 것**이 더 위험하다.

권장 blocked escalation band는 아래와 같다.

| blocked 상태 | local stewardship 기대 행동 | council escalation rule |
|---|---|---|
| `0-1 영업일` | `blocked_from_state`, `blockers`, `blocker_owner`, ETA를 채운다 | high-blast 항목인데 owner/ETA가 비어 있으면 즉시 council |
| `2-5 영업일` | unblock 실험과 dependency follow-up을 local forum에서 추적한다 | shared dependency가 드러나면 다음 council slot에 packet 예약 |
| `6-10 영업일` | local forum은 더 이상 단독 owner가 아니다 | 같은 주 council agenda에 반드시 올린다 |
| `>10 영업일` 또는 `missed_eta_count >= 2` | portfolio-level unblock이 필요하다고 본다 | council이 decision owner를 맡고 local forum은 execution follow-up만 맡는다 |

즉 `blocked_duration > 5 영업일`은 경고선이고,
`>10 영업일` 또는 ETA 두 번 미스는 **local ownership 상실선**이다.

### 4. high-blast-radius shadow entry는 "영향이 넓다"가 아니라 구체적 choke point를 가진다

다음 중 하나라도 맞으면 `high_blast_radius = true`로 보고 `council_immediate`가 적절하다.

| red-line trigger | concrete threshold | 왜 local forum으로 충분하지 않은가 |
|---|---|---|
| cross-domain choke point | `impacted_domains >= 2` 이고 같은 change window를 공유한다 | 한 도메인 판단으로는 rollback/priority를 정할 수 없다 |
| shared control plane gap | registry, policy, audit log, rollout gate 같은 shared plane 변경 없이는 shadow path를 못 줄인다 | local fix가 아니라 standard or platform backlog 조정이 필요하다 |
| production gate shadow | release approval, cutover go/no-go, deprecation bypass, emergency break-glass 같은 gate를 shadow path가 쥔다 | 잘못되면 여러 서비스가 동시에 멈추거나 우회가 굳는다 |
| shared source of truth | off-plane spreadsheet/DM가 `affected_teams >= 3`의 authoritative source다 | 이미 local workaround가 아니라 shared governance defect다 |
| red-risk orphan blocker | `blocker_owner_missing_for > 1 영업일` 또는 `unblock_eta_missing_for > 1 영업일` while high blast | 병목이 아니라 즉시 governance orphan로 취급해야 한다 |

핵심은 high blast radius를 "큰 느낌"으로 말하지 않는 것이다.
반드시 **몇 도메인, 몇 팀, 어떤 shared gate인지**로 적어야 한다.

### 5. repeated shadow spread도 council trigger로 본다

처음엔 single-team workaround였더라도 아래 threshold를 넘기면 local stewardship만으로 보기 어렵다.

| spread signal | council trigger |
|---|---|
| 같은 `process_family`가 다른 stewardship forum으로 번진다 | `impacted_domains >= 2`가 되는 즉시 |
| 같은 shadow path를 쓰는 팀이 늘어난다 | `affected_teams >= 3` |
| hold/blocked가 반복된다 | `extension_count >= 2` 또는 `missed_eta_count >= 2` |
| 공식화/흡수 후에도 같은 우회가 재발한다 | `30일` 안에 reopen 또는 repeated exception `>= 2` |

즉 local forum은 "우리 팀 일"일 때까지만 local이다.
같은 shadow family가 조직적 패턴이 되면 council agenda가 맞다.

### 6. local forum에서 council로 올릴 때 packet field를 줄이면 안 된다

좋은 escalation은 "위험해서 올립니다" 한 줄이 아니다.
local stewardship에서 council로 넘길 때는 최소한 아래 필드가 고정돼야 한다.

| field | 왜 필요한가 |
|---|---|
| `catalog_id`, `title`, `lifecycle_state`, `blocked_from_state` | 어떤 항목이 어디서 멈췄는지 식별한다 |
| `blocked_since`, `missed_eta_count`, `next_review_at` | 시간 임계치를 넘겼는지 보여 준다 |
| `impacted_domains`, `affected_teams`, `blast_radius_class` | local vs council authority boundary를 수치로 보여 준다 |
| `shared_dependency_summary`, `target_system_or_process` | platform/policy decision이 필요한지 드러낸다 |
| `local_forum_disposition` | local forum이 이미 무엇을 시도했는지 남긴다 |
| `requested_council_action` | priority 결정인지, standard 변경인지, decision ownership takeover인지 분명히 한다 |

이 field 세트는 [Shadow Review Packet Template](./shadow-review-packet-template.md)의 escalation packet에 바로 꽂히는 projection이어야 한다.
그래야 council이 다시 사실 수집부터 하지 않는다.

### 7. council이 받는 순간도 outcome이 달라져야 한다

council escalation의 목적은 higher-level visibility만이 아니다.
받은 뒤 어떤 kind의 decision을 내려야 하는지도 달라진다.

| council이 받아야 하는 질문 | 기대 output |
|---|---|
| shared backlog를 올릴 것인가 | platform/policy priority 조정 |
| local shadow path를 officialize 또는 absorb로 바꿀 것인가 | `target_decision` 재판정 |
| blocked entry의 decision owner를 council이 가져갈 것인가 | `decision_owner` 변경 |
| stop-loss나 scope reduction이 필요한가 | target scope, due date, downgrade plan 확정 |

즉 escalation은 "윗선 보고"가 아니라 **decision height를 바꾸는 state transition**이다.
그래서 council closeout도 [Shadow Review Outcome Template](./shadow-review-outcome-template.md)처럼 `from_state`, `to_state`, `field_updates`, `decision_owner`를 남겨야 한다.

### 8. worked example로 보면 threshold가 더 선명해진다

#### 예시 A. local stewardship에서 끝내도 되는 경우

상황:

- 한 도메인의 migration sheet가 freeze 때문에 `3 영업일` 멈췄다
- `blocker_owner`는 명확하고 새 ETA도 있다
- 다른 팀은 이 sheet를 쓰지 않는다

판정:

- `local_keep`

이유:

- `impacted_domains == 1`
- `blocked_duration <= 5 영업일`
- shared control plane 변경이 없다

#### 예시 B. 다음 council cycle에 올려야 하는 경우

상황:

- shadow absorb 경로가 shared override registry 필드 부족으로 `6 영업일` blocked 상태다
- 두 도메인이 같은 registry field를 기다린다
- local forum은 unblock 시도를 했지만 priority를 바꿀 권한은 없다

판정:

- `council_next_cycle`

이유:

- `blocked_duration > 5 영업일`
- `impacted_domains >= 2`
- blocker가 shared platform backlog다

#### 예시 C. 즉시 council로 올려야 하는 경우

상황:

- release override 승인과 mute 예외가 슬랙 DM과 spreadsheet에 있고 네 팀이 같은 artifact를 source of truth처럼 본다
- 분기말 release window 중이라 rollback 판단도 이 artifact에 묶여 있다
- registry owner와 unblock ETA가 하루 넘게 비어 있다

판정:

- `council_immediate`

이유:

- `affected_teams >= 3`
- production gate shadow다
- high-blast 항목인데 owner/ETA가 없다

### 9. 한 장 정책으로 요약하면 local autonomy와 council 집중도를 같이 지킬 수 있다

```yaml
shadow_forum_escalation_rules:
  local_keep_if_all:
    - impacted_domains == 1
    - affected_teams <= 2
    - shared_control_plane_change == false
    - blocker_owner_assigned_within <= 1bd
    - unblock_eta_present_within <= 1bd
    - blocked_duration <= 5bd
  council_next_cycle_if_any:
    - blocked_duration > 5bd
    - shared_dependency == true
    - impacted_domains >= 2
    - affected_teams >= 3
    - extension_count >= 2
  council_immediate_if_any:
    - production_gate_shadow == true
    - shared_control_plane_change == true
    - high_blast_radius == true
    - blocker_owner_missing_for > 1bd
    - unblock_eta_missing_for > 1bd
    - missed_eta_count >= 2
  council_takes_decision_owner_if_any:
    - blocked_duration > 10bd
    - missed_eta_count >= 2
    - repeated_exception >= 2 on shared_path
```

중요한 것은 threshold 숫자 자체보다,
**local forum이 언제 ownership을 잃고 council이 언제 decision owner를 가져가는지**가 분명해야 한다는 점이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| 모든 shadow entry를 council로 보냄 | 기준은 단순하다 | 병목이 심하고 local stewardship이 약해진다 | 권장하지 않는다 |
| 정성적 판단만으로 escalation | 유연해 보인다 | 팀마다 기준이 갈리고 orphan backlog가 늦게 드러난다 | 초기 임시 단계 |
| threshold + clock 기반 escalation | routing이 일관되고 backlog 정체가 빨리 보인다 | field discipline과 scorecard가 필요하다 | 권장 기본형 |

shadow forum escalation rule의 목적은 escalation을 늘리는 것이 아니라, **wrong-height decision을 줄이는 것**이다.

---

## 꼬리질문

- local stewardship이 붙잡고 있는 `blocked` entry 중 `5 영업일`을 넘긴 항목이 몇 개인가?
- `high_blast_radius`를 수치로 적지 않고 "중요함"으로만 적는 항목은 없는가?
- council로 올릴 때 `local_forum_disposition`과 `requested_council_action`이 빠지지 않는가?
- `>10 영업일` blocked 항목의 decision owner가 여전히 local forum으로 남아 있지는 않은가?
- 같은 shadow family가 세 팀 이상에 퍼졌는데도 아직 로컬 workaround로 취급하고 있지는 않은가?

## 한 줄 정리

Shadow forum escalation rules는 local stewardship forum이 끝낼 수 있는 single-domain short-blocker와, council이 받아야 하는 cross-domain high-blast shared-defect를 `blocked_duration`, `impacted_domains`, `affected_teams`, owner/ETA clock으로 명확히 갈라 governance backlog를 올바른 높이로 라우팅하는 기준이다.
