# Shadow Process Catalog Entry Schema

> 한 줄 요약: shadow process catalog가 inventory로 끝나지 않으려면, 각 항목이 signal evidence, target state, review forum, retirement tracking을 같은 schema 안에서 묶어 detection부터 officialization/retirement까지 이어지게 해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Process Detection Signals](./shadow-process-detection-signals.md)
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)
> - [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)
> - [Shadow Catalog Review Cadence Profiles](./shadow-catalog-review-cadence-profiles.md)
> - [Shadow Catalog Reopen and Successor Rules](./shadow-catalog-reopen-and-successor-rules.md)
> - [Shadow Packet Automation Mapping](./shadow-packet-automation-mapping.md)
> - [Shadow Review Packet Template](./shadow-review-packet-template.md)
> - [Shadow Promotion Snapshot Schema Fields](./shadow-promotion-snapshot-schema-fields.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)
> - [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)
> - [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)
> - [Shadow Retirement Scorecard Schema](./shadow-retirement-scorecard-schema.md)
> - [Architecture Council and Domain Stewardship Cadence](./architecture-council-domain-stewardship-cadence.md)
> - [Incident Feedback to Policy and Ownership Closure](./incident-feedback-policy-ownership-closure.md)
> - [Consumer Exception Registry Templates](./consumer-exception-registry-templates.md)

> retrieval-anchor-keywords:
> - shadow process catalog entry schema
> - shadow catalog template
> - shadow process registry row
> - signal evidence
> - target state
> - review forum
> - shadow review packet
> - review packet items
> - retirement tracking
> - shadow process metadata
> - workaround registry schema
> - shadow review cadence profile
> - catalog to packet projection
> - shadow packet fallback rules
> - catalog intake template
> - shadow catalog state machine
> - lifecycle_state field
> - promotion snapshot fields
> - promotion_snapshot block
> - retirement blocker
> - manual path record
> - manual_path_ratio verification
> - shadow retirement threshold
> - scorecard_schema_ref
> - last_verdict_record
> - lineage root id
> - predecessor successor link
> - reopen history

## 핵심 개념

shadow process catalog entry는 "이런 우회가 있다"를 적는 메모가 아니다.
좋은 entry는 최소 네 가지를 동시에 답해야 한다.

- 어떤 shadow process가 실제로 관찰됐는가
- 그 판단의 근거가 무엇인가
- 다음 상태가 retire / officialize / absorb / hold 중 무엇인가
- 어느 forum이 언제 review하고, 어떤 기준으로 retirement를 닫을 것인가

즉 schema의 목적은 문서 정리가 아니라 **detection, decision, review, retirement를 한 row로 연결하는 것**이다.

---

## 깊이 들어가기

### 1. entry schema는 intake 메모가 아니라 handoff contract여야 한다

shadow process는 보통 detection signal에서 시작하고, review forum을 거쳐, officialization 또는 retirement tracking으로 이어진다.
이 단계마다 다른 양식을 쓰면 정보가 빠진다.

그래서 한 entry 안에서 최소한 다음 handoff를 끊기지 않게 해야 한다.

- detection -> 왜 shadow candidate로 올렸는가
- decision -> 어떤 target state를 택했는가
- review -> 누가 언제 다시 볼 것인가
- retirement -> 무엇이 끝나야 truly closed인가

### 2. identity와 current path는 "무엇을 관리하는지"를 고정한다

catalog entry 첫 부분에는 process identity가 있어야 한다.

권장 필드:

- `catalog_id`
- `title`
- `process_family`
- `domain` / `services`
- `current_owner`
- `current_path`
- `off_plane_artifacts`

여기서 중요한 것은 단순 이름보다 **현재 어떤 비공식 경로가 실제로 쓰이는지**를 남기는 것이다.
예를 들어 `slack_dm`, `personal_sheet`, `local_script`, `oral_runbook` 같은 current path 묘사가 없으면, 나중에 replacement가 생겨도 무엇을 대체해야 하는지 불명확해진다.

### 3. signal evidence block은 suspicion을 evidence로 바꾼다

shadow process entry가 금방 noise가 되는 이유는 "이상한 것 같음"만 적고, 어떤 signal이 얼마나 반복됐는지 남기지 않기 때문이다.

signal evidence block에는 보통 다음을 넣는 편이 좋다.

- `signal_family`
- `source`
- `evidence_window`
- `repeat_count`
- `confidence`
- `evidence_ref`
- `observed_at`

한 번의 anecdote와 반복 패턴은 같은 무게가 아니다.
entry에는 최소 한 개 이상의 evidence row가 있어야 하고, high-impact candidate라면 서로 다른 signal family가 함께 보이는 편이 좋다.

### 4. target state는 분류가 아니라 구조 결정이어야 한다

catalog에 올린 뒤 다음 상태가 비어 있으면 backlog는 그냥 늘어난다.

target state block에는 다음 정도가 들어가야 한다.

- `decision`
- `rationale`
- `target_system_or_process`
- `target_due_at`

`decision` 값은 보통 다음 중 하나다.

- `retire`
- `officialize`
- `absorb`
- `temporary_hold`

핵심은 "없앨지 말지"가 아니라, **어떤 공식 구조 아래로 옮길지**를 기록하는 것이다.
예를 들어 structured data가 핵심이면 `absorb`, 사람 판단 순서와 훈련이 핵심이면 `officialize`가 더 잘 맞는다.

다만 `decision`만으로는 entry가 실제로 어디에 머물러 있는지 알 수 없다.
그래서 실무 schema에는 [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)처럼 `lifecycle_state`를 별도로 두고, `temporary_hold`와 `blocked`를 outcome이 아니라 제어 상태로 기록하는 편이 좋다.

### 5. review forum 필드는 orphan backlog를 막는다

owner만 있고 forum이 없으면, shadow process entry는 누구의 agenda에도 오르지 않는다.

그래서 review 정보는 별도 block으로 두는 편이 좋다.

- `review_forum`
- `review_owner`
- `next_review_at`
- `escalation_forum`
- `review_packet_items`

이때 `next_review_at`은 owner 편의 날짜보다 lifecycle state 기반 운영 약속에 가깝다.
상태별 기본 review frequency, owner expectation, escalation SLA는 [Shadow Catalog Review Cadence Profiles](./shadow-catalog-review-cadence-profiles.md)처럼 별도 profile 문서로 고정해 두는 편이 drift를 줄인다.

특히 `review_forum`은 단순 meeting name이 아니라 decision venue여야 한다.
예:

- local stewardship forum
- override portfolio review
- incident follow-up review
- architecture council

이 필드가 있어야 expiring hold, blocked retirement, repeated recurrence를 어디서 회수할지 명확해진다.
실제 review packet에 어떤 projection을 올려야 일관된 판단이 가능한지는 [Shadow Review Packet Template](./shadow-review-packet-template.md)처럼 별도 template로 고정하고, field별 fallback과 quality gate는 [Shadow Packet Automation Mapping](./shadow-packet-automation-mapping.md)처럼 별도 projection contract로 두는 편이 좋다.

### 6. retirement tracking은 "closed" 선언이 아니라 replacement adoption 증빙이어야 한다

shadow process는 문서에서 닫아도 현실에서 계속 살아남기 쉽다.
그래서 retirement block에는 종료 선언보다 검증 장치가 먼저 들어가야 한다.

권장 필드:

- `replacement_path`
- `exit_condition`
- `scorecard_schema_ref`
- `verification_metric`
- `threshold_rule`
- `verification_window`
- `verification_source`
- `blocker_status`
- `blockers`
- `parallel_run_until`
- `retired_at`
- `recurrence_check_at`
- `last_verdict_record`

예를 들어 "DM 승인 절차 폐기"는 `retired_at`만 적어서는 부족하다.
`manual_path_ratio == 0 for 30d` 같은 exit condition과, 이를 확인할 scorecard source가 같이 있어야 한다.
이때 numerator / denominator와 mirror SLA를 어떤 규칙으로 계산하는지는 [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)처럼 공통 계측 문서에 고정해 두는 편이 좋다.
또한 `verification_metric` 이름만이 아니라 threshold와 verification window를 같이 저장해야 `closed`와 `retired`를 구분할 수 있는데, 그 판정 기준은 [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)처럼 별도 proof 문서로 고정하는 편이 안정적이다.
실제 full scorecard shape는 [Shadow Retirement Scorecard Schema](./shadow-retirement-scorecard-schema.md)처럼 artifact로 두고, entry에는 `scorecard_schema_ref`와 최신 `last_verdict_record` 요약을 남기는 편이 catalog row를 과하게 비대하게 만들지 않으면서도 closeout contract를 유지하게 해 준다.

### 7. schema는 최소 required field와 optional field를 구분해야 한다

현실적으로 모든 entry가 처음부터 완벽할 수는 없다.
대신 required field가 너무 적으면 governance가 굴러가지 않는다.

추천 최소 required set:

- `catalog_id`
- `title`
- `current_owner`
- `current_path`
- `signal_evidence[]`
- `lifecycle_state`
- `target_state.decision`
- `review.review_forum`
- `review.next_review_at`
- `retirement_tracking.exit_condition`

그리고 [Shadow Candidate Promotion Thresholds](./shadow-candidate-promotion-thresholds.md) 규칙으로 catalog에 들어온 entry라면, 아래 promotion snapshot 묶음도 사실상 minimum contract로 보는 편이 좋다.

- `promotion_snapshot.tier`
- `promotion_snapshot.confidence`
- `promotion_snapshot.shadow_candidate_key`
- `promotion_snapshot.rule_ref`
- `promotion_snapshot.window`
- `promotion_snapshot.threshold_snapshot`
- `promotion_snapshot.evidence_refs[]`

이 필드가 비어 있으면 "왜 catalog intake가 되었는가"를 다음 review forum이 다시 추측하게 된다.
필드별 최소 shape와 packet projection 규칙은 [Shadow Promotion Snapshot Schema Fields](./shadow-promotion-snapshot-schema-fields.md)에서 별도로 고정하는 편이 drift를 줄인다.

있으면 좋은 확장 필드:

- `target_state.target_system_or_process`
- `lifecycle.resume_state`
- `lifecycle.blocked_from_state`
- `lifecycle.state_changed_at`
- `lineage.lineage_root_id`
- `lineage.predecessor_catalog_ids[]`
- `history.reopen_events[]`
- `history.retirement_attempts[]`
- `review.escalation_forum`
- `retirement_tracking.verification_metric`
- `retirement_tracking.threshold_rule`
- `retirement_tracking.verification_window`
- `retirement_tracking.scorecard_schema_ref`
- `retirement_tracking.last_verdict_record`
- `retirement_tracking.parallel_run_until`
- `links.runbook`
- `links.incident_refs`

특히 recurrence를 same-entry reopen으로 다룰지 successor로 분리할지 판단하려면, lineage/history 필드를 optional memo가 아니라 운영 contract로 취급해야 한다.
이 기준과 append-only history 규칙은 [Shadow Catalog Reopen and Successor Rules](./shadow-catalog-reopen-and-successor-rules.md)처럼 별도 문서로 고정해 두는 편이 좋다.

### 8. closed 상태는 "문서 업데이트 완료"가 아니라 recurrence guard까지 포함해야 한다

shadow process가 진짜 닫혔는지 보려면 replacement adoption과 recurrence를 같이 봐야 한다.

그래서 closure 판단은 보통 세 단계를 거친다.

1. replacement path가 존재한다
2. manual/off-plane path 사용량이 내려간다
3. 일정 기간 recurrence가 없다

이 셋 중 마지막이 빠지면, shadow process는 종종 같은 이름 또는 다른 이름으로 다시 등장한다.

---

## 최소 필드 묶음

| 필드 묶음 | 핵심 필드 | 왜 필요한가 |
|---|---|---|
| identity | `catalog_id`, `title`, `current_path`, `current_owner` | 무엇을 누가 관리하는지 고정한다 |
| signal evidence | `signal_family`, `source`, `repeat_count`, `confidence` | suspicion을 evidence로 바꾼다 |
| promotion snapshot | `promotion_snapshot.tier`, `promotion_snapshot.confidence`, `promotion_snapshot.threshold_snapshot` | threshold 기반 intake 판정을 replay 가능한 provenance로 남긴다 |
| target state | `decision`, `rationale`, `target_due_at` | 다음 구조 결정을 backlog에 붙인다 |
| review forum | `review_forum`, `next_review_at`, `escalation_forum` | orphan entry를 막고 agenda를 만든다 |
| retirement tracking | `replacement_path`, `exit_condition`, `verification_metric`, `blocker_status` | 닫힘을 선언이 아니라 검증으로 바꾼다 |

---

## 코드로 보기

```yaml
shadow_catalog_entry:
  catalog_id: shadow-release-approval-001
  title: manual_release_override_via_slack_dm
  process_family: approval
  domain: checkout-platform
  services:
    - release-orchestrator
    - deployment-api
  current_owner: release-manager
  current_path:
    trigger: freeze-window rollout exception
    unofficial_channel: slack_dm
    off_plane_artifacts:
      - personal-spreadsheet/release-override-tracker
  signal_evidence:
    - signal_family: repeated_dm_approval
      source: incident_review
      evidence_window: last_30_days
      repeat_count: 5
      confidence: high
      observed_at: 2026-04-12
      evidence_ref: INC-482-review
    - signal_family: repeated_override
      source: override_scorecard
      evidence_window: last_90_days
      repeat_count: 8
      confidence: medium
      observed_at: 2026-04-14
      evidence_ref: override-scorecard-2026-q2
  risk:
    operational: high
    auditability: high
    single_person_dependency: true
    failure_if_unavailable: release_blocked
  target_state:
    decision: absorb
    rationale:
      - structured override data exists
      - audit trail is required
      - same workaround repeats across teams
    target_system_or_process: rollout_override_registry
    target_due_at: 2026-05-15
  review:
    review_forum: domain_stewardship_forum
    review_owner: platform-governance
    next_review_at: 2026-04-21
    escalation_forum: architecture_council
    review_packet_items:
      - signal_evidence
      - replacement_path
      - blocker_status
  retirement_tracking:
    replacement_path: registry_request_for_release_override
    exit_condition: manual_path_ratio_zero_for_30d
    scorecard_schema_ref: shadow-retirement-scorecard-v1
    verification_metric: manual_path_ratio
    threshold_rule:
      operator: eq
      target: 0.0
      unit: ratio
    verification_window:
      rule: longer_of_30d_or_2_review_cadences
      cadence_basis: monthly_exception_review
      minimum_cycles_required: 2
    verification_source: override_scorecard
    blocker_status: open
    blockers:
      - registry_missing_freeze_override_field
    parallel_run_until: 2026-05-01
    retired_at:
    recurrence_check_at: 2026-06-01
    last_verdict_record:
      status: verification_pending
      decided_at: 2026-04-21T10:30:00+09:00
      reason_codes:
        - window_running
  links:
    runbook: release-runbook-v3
    incident_refs:
      - INC-482
      - INC-493
```

좋은 schema는 entry 하나만 읽어도 왜 catalog에 들어왔고, 어디로 보내고, 언제 닫을지를 이해할 수 있게 만든다.

---

## 실전 시나리오

### 시나리오 1: entry에 evidence 없이 "다들 이렇게 한다"만 적혀 있다

이 경우 review forum은 감으로 판단하게 되고, priority가 쉽게 흔들린다.
최소한 signal family와 repeat count와 source를 먼저 채워야 한다.

### 시나리오 2: target state는 absorb인데 review forum이 비어 있다

누가 control plane 변경을 실제 backlog로 받을지 정해지지 않아, catalog만 남고 전환은 진행되지 않는다.

### 시나리오 3: retired_at만 있고 verification metric이 없다

문서상 retirement는 끝났지만, 실제론 DM 승인과 수동 시트가 병행 사용될 가능성이 높다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 메모형 catalog | 작성이 쉽다 | review와 retirement가 끊긴다 | 임시 초기 수집 |
| 최소 schema | entry 비교와 review가 쉬워진다 | 일부 nuance는 덜 담긴다 | 기본 운영 모델 |
| schema + verification field | retirement 진실성을 높인다 | scorecard와 metric 연결이 필요하다 | 성숙한 shadow governance |

shadow catalog entry schema의 목적은 양식을 복잡하게 만드는 것이 아니라, **hidden workaround를 evidence-backed decision record로 바꿔 실제 전환과 종료까지 밀어 주는 것**이다.

---

## 꼬리질문

- 이 entry는 signal evidence 없이 사람 기억에 기대고 있지 않은가?
- target state가 why와 due date 없이 비어 있지 않은가?
- review forum과 next review가 지정돼 실제 agenda로 들어가는가?
- retirement tracking이 retired_at 선언이 아니라 replacement adoption을 검증하는가?
- recurrence check가 없어 shadow process가 다른 이름으로 되살아날 위험은 없는가?

## 한 줄 정리

Shadow process catalog entry schema는 shadow candidate를 evidence, target state, review forum, retirement tracking이 붙은 운영 레코드로 만들어 detection부터 종료까지 끊기지 않게 하는 템플릿이다.
