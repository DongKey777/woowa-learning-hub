---
schema_version: 3
title: Shadow Review Packet Template
concept_id: software-engineering/shadow-review-packet-template
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
- review-packet
- governance
- decision-contract
aliases:
- shadow review packet template
- shadow review packet minimum fields
- shadow catalog forum agenda
- review packet projection
- decision ready packet
- shadow review 패킷 템플릿
symptoms:
- shadow catalog entry를 forum마다 다른 필드와 자유 서술로 읽어 decision, execution-risk, verification 질문이 매번 흔들려
- packet에 decision_question이 없어 회의가 상태 보고로 끝나고 target_decision, owner, due date가 남지 않아
- temporary_hold와 blocked를 구분하는 hold_reason, expires_at, blocked_since, escalation_forum이 없어 control state가 섞여
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/shadow-process-catalog-entry-schema
- software-engineering/shadow-catalog-lifecycle-states
next_docs:
- software-engineering/shadow-packet-automation-mapping
- software-engineering/shadow-review-outcome-template
- software-engineering/shadow-promotion-snapshot-schema-fields
linked_paths:
- contents/software-engineering/shadow-process-catalog-entry-schema.md
- contents/software-engineering/shadow-promotion-snapshot-schema-fields.md
- contents/software-engineering/shadow-packet-automation-mapping.md
- contents/software-engineering/shadow-catalog-lifecycle-states.md
- contents/software-engineering/shadow-review-outcome-template.md
- contents/software-engineering/shadow-process-catalog-and-retirement.md
- contents/software-engineering/shadow-process-officialization-absorption-criteria.md
- contents/software-engineering/manual-path-ratio-instrumentation.md
- contents/software-engineering/override-burndown-review-cadence-scorecards.md
- contents/software-engineering/architecture-council-domain-stewardship-cadence.md
confusable_with:
- software-engineering/shadow-process-catalog-entry-schema
- software-engineering/shadow-packet-automation-mapping
- software-engineering/shadow-review-outcome-template
forbidden_neighbors: []
expected_queries:
- shadow review packet은 catalog entry 전체 복사본이 아니라 forum decision에 필요한 최소 projection이어야 하는 이유는?
- packet 최소 필드로 catalog_id, lifecycle_state, signal_summary, promotion snapshot, blockers, verification_metric, decision_question을 왜 넣어야 해?
- shadow review agenda를 intake, decision-needed, execution-risk, verification-closeout으로 나누면 어떤 질문이 고정돼?
- temporary_hold와 blocked가 섞이지 않게 packet에 hold_reason, expires_at, blocked_from_state, escalation_forum을 어떻게 노출해?
- review packet output까지 outcome template로 표준화해야 state machine과 다음 packet이 끊기지 않는 이유는?
contextual_chunk_prefix: |
  이 문서는 shadow catalog entry를 forum decision에 필요한 최소 projection으로 압축하고 intake, decision-needed, execution-risk, verification agenda를 고정하는 advanced playbook이다.
---
# Shadow Review Packet Template

> 한 줄 요약: shadow catalog entry를 forum마다 다른 감으로 읽지 않으려면, review packet은 entry schema의 전체 복사본이 아니라 decision에 필요한 최소 projection이어야 하고, agenda도 `decision / execution-risk / verification` 구간으로 고정해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Promotion Snapshot Schema Fields](./shadow-promotion-snapshot-schema-fields.md)
> - [Shadow Packet Automation Mapping](./shadow-packet-automation-mapping.md)
> - [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)
> - [Shadow Review Outcome Template](./shadow-review-outcome-template.md)
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)
> - [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)
> - [Architecture Council and Domain Stewardship Cadence](./architecture-council-domain-stewardship-cadence.md)

> retrieval-anchor-keywords:
> - shadow review packet template
> - shadow review packet minimum fields
> - shadow catalog forum agenda
> - review packet projection
> - catalog entry to packet row
> - packet field fallback
> - shadow governance forum
> - decision ready packet
> - blocked hold verification agenda
> - shadow review outcome template
> - shadow entry review checklist
> - promotion threshold summary
> - promotion confidence packet field
> - review packet items
> - shadow catalog agenda shape
> - forum decision packet
> - shadow review template

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Shadow Review Packet Template](./README.md#shadow-review-packet-template)
> - 다음 단계: [Shadow Packet Automation Mapping](./shadow-packet-automation-mapping.md)

## 핵심 개념

shadow catalog entry schema가 잘 정의돼 있어도 review forum이 매번 다른 필드를 보고 판단하면 결과는 들쭉날쭉해진다.

그래서 필요한 것이 `review packet`이다.
여기서 packet의 목적은 entry를 길게 복붙하는 것이 아니라, **이번 회의에서 결정하거나 회수해야 할 것만 압축해 동일한 질문 순서로 보여 주는 것**이다.

좋은 shadow review packet은 최소 세 가지를 동시에 만족해야 한다.

- entry identity와 현재 lifecycle state가 한눈에 보인다
- 왜 지금 이 forum 안건이 되었는지 evidence와 blocker가 요약된다
- 이번 회의가 내려야 할 decision과 다음 follow-up이 분명하다

즉 packet은 문서 요약본이 아니라 **forum decision contract**다.

---

## Template Insertion Points

shadow review packet template는 회의 자료 한 장에만 쓰이는 양식이 아니다.
같은 필드 묶음이 다음 지점에서 재사용돼야 drift가 줄어든다.

- catalog entry `review.review_packet_items`: packet에 어떤 projection을 노출할지 정의한다.
- stewardship forum agenda: 각 안건 row를 같은 packet field로 정렬한다.
- escalation packet: local forum에서 architecture council로 올릴 때 같은 field명을 유지한다.
- verification closeout note: `verification_metric`, `recurrence_check_at`, `exit_decision`을 그대로 재사용한다.

삽입 지점을 맞춰 두면 entry schema, review forum, escalation memo가 서로 다른 말을 하지 않는다.
field별 source path와 fallback을 어떻게 고정할지는 [Shadow Packet Automation Mapping](./shadow-packet-automation-mapping.md)처럼 별도 문서로 분리해 두면 template와 generator 구현이 섞이지 않는다.

---

## 깊이 들어가기

### 1. review packet은 schema의 축약본이 아니라 decision projection이어야 한다

entry schema는 detection부터 retirement까지 전부 담는다.
반면 review packet은 "이번 review에 필요한 부분"만 보여 준다.

따라서 packet 설계 원칙은 다음이 적절하다.

- schema 원문은 source of truth로 두고, packet은 projection으로 만든다
- forum이 바뀌어도 field 이름은 유지한다
- long narrative보다 `decision question`과 `next action`을 먼저 둔다
- packet이 없어도 entry를 찾을 수 있게 `catalog_id`와 원문 링크를 남긴다

좋은 packet은 정보량이 적은 것이 아니라, **판단 순서가 고정된 것**이다.

### 2. 최소 packet 필드는 "이 항목을 왜 지금 봐야 하는가"를 답해야 한다

shadow review packet의 최소 필드는 아래 정도가 적절하다.

| 필드 묶음 | 최소 필드 | 왜 필요한가 |
|---|---|---|
| identity | `catalog_id`, `title`, `current_path`, `current_owner` | 어떤 shadow entry를 다루는지 고정한다 |
| current state | `lifecycle_state`, `target_decision`, `state_changed_at` | 지금 어느 단계에서 왜 forum에 올라왔는지 보여 준다 |
| evidence snapshot | `signal_summary`, `evidence_window`, `repeat_count`, `latest_evidence_ref` | anecdote가 아니라 반복 signal인지 판별한다 |
| promotion snapshot | `promotion_tier`, `promotion_confidence`, `promotion_window`, `promotion_rule_ref`, `promotion_threshold_summary`, `promotion_reason_summary`, `promotion_evidence_refs` | 왜 이 entry가 watchlist가 아니라 promote/fast_track로 올라왔는지 replay 가능한 근거로 보여 준다 |
| risk / impact | `risk_summary`, `failure_if_unavailable`, `single_person_dependency` | 우선순위와 escalation 필요성을 맞춘다 |
| replacement / execution | `target_system_or_process`, `replacement_path`, `blockers`, `blocker_owner` | retire/absorb/officialize 실행 가능성을 점검한다 |
| verification / next step | `verification_metric`, `exit_condition`, `decision_question`, `next_review_at` | 이번 회의 출력과 다음 회수 시점을 명확히 한다 |

여기서 중요한 것은 field 수보다 빠지면 안 되는 질문이다.

- 무엇을 검토하는가
- 왜 지금 검토하는가
- 무엇이 막고 있는가
- 이 forum이 지금 결정해야 할 것은 무엇인가
- 다음 review 전에 무엇이 바뀌어야 하는가

특히 intake 또는 `decision-needed` row라면 `promotion_tier`와 `promotion_confidence`만 보여 주고 끝내지 않는 편이 좋다.
같은 row에 `promotion_threshold_summary`, `promotion_reason_summary`, `promotion_evidence_refs`까지 같이 보여 줘야 forum이 승격 이유를 다시 추측하지 않는다.
이 projection의 최소 필드와 quality gate는 [Shadow Promotion Snapshot Schema Fields](./shadow-promotion-snapshot-schema-fields.md)에서 별도 contract로 고정하는 편이 안전하다.

### 3. forum별 자유 서술을 허용하면 `temporary_hold`와 `blocked`가 섞인다

shadow catalog review가 자주 흔들리는 이유는 hold와 blocked를 같은 "진행 중 문제"로 읽기 때문이다.

그래서 packet에는 control state를 강제로 구분하는 field가 필요하다.

- `lifecycle_state`
- `hold_reason` / `expires_at`
- `blocked_from_state` / `blocked_since`
- `escalation_forum`

이 네 가지가 없으면 forum은 "왜 멈췄는지"보다 "대충 안 풀리고 있다"만 읽게 된다.
결과적으로 의도된 pause와 구조적 blocker가 같은 urgency로 취급된다.

### 4. agenda는 entry 나열이 아니라 decision type별 queue여야 한다

좋은 shadow review forum agenda는 lifecycle state를 그대로 읽되, 회의 시간은 decision type별로 묶는다.

권장 agenda shape:

| agenda section | 포함할 상태 | forum이 물어야 할 핵심 질문 | 기대 출력 |
|---|---|---|---|
| intake / re-triage | `detected`, `cataloged` | 이 entry가 review 대상이 될 정도로 evidence가 충분한가 | catalog 유지 / 추가 evidence 요청 / drop |
| decision needed | `decision_pending` | retire / absorb / officialize / hold 중 무엇이 맞는가 | `target_decision`, owner, due date |
| execution risk | `temporary_hold`, `blocked`, `*_in_progress` | 왜 멈췄고 누가 풀며 어느 forum으로 올릴 것인가 | unblock action, escalation, resume date |
| verification / closeout | `verification_pending`, recurrence가 보인 `retired` | exit condition과 recurrence window가 충족됐는가 | retire 승인 / verification 연장 / reopen |

핵심은 안건을 많이 나누는 것이 아니라, **회의 질문을 섹션마다 고정하는 것**이다.
그래야 같은 entry가 다른 주의 회의에서 전혀 다른 기준으로 평가되지 않는다.

### 5. packet에는 `decision question`이 반드시 한 줄로 있어야 한다

많은 review packet이 상태 요약만 있고 실제 질문이 없다.
그러면 forum은 토론은 오래 하지만 output이 약해진다.

따라서 packet마다 아래 중 하나가 명시돼야 한다.

- `decision_question`: 이번 회의에서 어떤 결정을 내려야 하는가
- `approval_needed`: 어떤 승인 또는 판정이 필요한가
- `escalation_needed`: 어느 조건 때문에 상위 forum 판단이 필요한가

예:

- `이 항목을 retire 대신 absorb로 전환할 것인가?`
- `temporary_hold를 연장할 것인가, resume_state로 복귀시킬 것인가?`
- `verification_pending 종료 기준으로 manual_path_ratio_zero_for_30d를 인정할 것인가?`

질문이 없으면 packet은 보고 자료로 끝난다.

### 6. verification 구간 packet은 detection 구간 packet과 달라야 한다

같은 template를 쓰더라도 강조점은 lifecycle state에 따라 달라진다.

- detection / decision 단계: signal evidence와 risk 요약 비중이 높다
- execution 단계: blocker, owner, due date, escalation 정보 비중이 높다
- verification 단계: `verification_metric`, `parallel_run_until`, `recurrence_check_at` 비중이 높다

즉 최소 template는 공통 필드를 유지하되, agenda section에 따라 spotlight field를 달리 두는 편이 좋다.

### 7. forum output도 template화해야 consistency가 닫힌다

packet만 표준화하고 회의 결과를 자유 서술로 남기면 다음 주 review가 또 흔들린다.

최소 출력 필드:

- `decision_outcome`
- `decision_owner`
- `due_at`
- `state_transition`
- `follow_up_evidence_required`
- `next_review_at`

입력 packet과 출력 record가 같은 field 체계를 공유해야 실제로 state machine과 README catalog가 끊기지 않는다.
이 출력 record의 최소 필드와 `source_packet_ref`, `from_state`, `to_state`, `field_updates` 규칙은 [Shadow Review Outcome Template](./shadow-review-outcome-template.md)처럼 별도 문서로 고정해 두는 편이 좋다.

---

## 최소 Packet 예시

```yaml
shadow_review_packet:
  packet_template_version: shadow-review-minimum-v1
  catalog_id: shadow-release-approval-001
  title: manual_release_override_via_slack_dm
  current_path: slack_dm
  current_owner: release-manager
  lifecycle_state: decision_pending
  target_decision: absorb
  state_changed_at: 2026-04-14
  signal_summary:
    families:
      - off_plane_approval
      - repeated_override
    evidence_window: last_30_days
    repeat_count: 5
    latest_evidence_ref: INC-482-review
  risk_summary:
    operational: high
    auditability: high
    single_person_dependency: true
    failure_if_unavailable: release_blocked
  target_system_or_process: rollout_override_registry
  replacement_path: registry_request_for_release_override
  blockers:
    - registry_missing_freeze_override_field
  blocker_owner: platform-governance
  verification_metric: manual_path_ratio
  exit_condition: manual_path_ratio_zero_for_30d
  decision_question: absorb 경로로 승인하고 control plane 필드 추가를 backlog로 받을 것인가
  next_review_at: 2026-04-21
  source_entry_ref: shadow-process-catalog-entry-schema
```

이 packet만 읽어도 forum은 "무엇을 왜 지금 결정해야 하는가"를 바로 파악할 수 있어야 한다.

---

## Forum Agenda 예시

```yaml
shadow_review_forum:
  forum: domain-stewardship-shadow-review
  cadence: weekly
  sections:
    - name: intake-and-retriage
      include_states: [detected, cataloged]
      expected_output:
        - keep_in_catalog
        - request_more_evidence
        - drop_candidate
    - name: decision-needed
      include_states: [decision_pending]
      expected_output:
        - target_decision
        - owner
        - due_at
    - name: execution-risk
      include_states:
        - temporary_hold
        - blocked
        - retire_in_progress
        - absorb_in_progress
        - officialize_in_progress
      expected_output:
        - unblock_action
        - escalation_forum
        - next_review_at
    - name: verification-and-closeout
      include_states: [verification_pending, retired]
      expected_output:
        - retire_approved
        - verification_extended
        - reopen_required
```

agenda의 목적은 안건을 예쁘게 정렬하는 것이 아니라, 각 상태에서 어떤 질문과 출력이 나와야 하는지 고정하는 데 있다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 자유 형식 review memo | 작성이 빠르다 | forum마다 다른 기준이 생긴다 | 피하는 편이 좋다 |
| 최소 review packet | 비교와 판단이 쉬워진다 | packet discipline이 필요하다 | 기본 운영 모델 |
| packet + sectioned agenda + output template | state transition 품질이 높다 | 회의 운영 체계가 필요하다 | shadow governance를 실제로 굴릴 때 |

shadow review packet template의 목적은 회의 자료를 늘리는 것이 아니라, **shadow entry review를 같은 질문, 같은 출력, 같은 follow-up 구조로 고정해 catalog 운영 일관성을 만드는 것**이다.

---

## 꼬리질문

- 이 forum은 entry마다 다른 자료를 들고 와서 비교가 어려워지지 않는가?
- packet에 `decision_question`이 없어 토론만 길어지고 있지 않은가?
- `temporary_hold`와 `blocked`를 서로 다른 output으로 처리하고 있는가?
- verification 구간 packet에 manual path ratio와 recurrence check가 실제로 들어가는가?
- local forum에서 council escalation로 넘어갈 때 field명이 바뀌어 handoff가 끊기지 않는가?

## 한 줄 정리

Shadow review packet template는 shadow catalog entry를 forum decision에 맞게 압축한 최소 projection과 agenda section 규칙을 정의해, shadow review가 사람마다 다른 감이 아니라 같은 운영 계약으로 굴러가게 만드는 문서다.
