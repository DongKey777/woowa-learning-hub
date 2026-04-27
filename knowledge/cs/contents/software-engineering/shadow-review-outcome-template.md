# Shadow Review Outcome Template

> 한 줄 요약: shadow review forum의 출력이 자유 형식 회의록이면 다음 packet과 state transition이 끊기므로, outcome record는 `source_packet_ref`, `from_state -> to_state`, `field_updates`, `owner/clock`, `verification follow-up`을 남기는 최소 decision template여야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Review Packet Template](./shadow-review-packet-template.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)
> - [Shadow Catalog Review Cadence Profiles](./shadow-catalog-review-cadence-profiles.md)
> - [Shadow Catalog Reopen and Successor Rules](./shadow-catalog-reopen-and-successor-rules.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)
> - [Temporary Hold Exit Criteria](./shadow-temporary-hold-exit-criteria.md)
> - [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)
> - [Shadow Retirement Scorecard Schema](./shadow-retirement-scorecard-schema.md)
> - [Decision Revalidation and Supersession Lifecycle](./decision-revalidation-supersession-lifecycle.md)
> - [Architecture Council and Domain Stewardship Cadence](./architecture-council-domain-stewardship-cadence.md)

> retrieval-anchor-keywords:
> - shadow review outcome template
> - shadow decision record
> - post forum decision record
> - review outcome minimum fields
> - packet input output symmetry
> - state transition output
> - shadow state transition record
> - source packet ref
> - field updates decision record
> - shadow forum closeout
> - to_state from_state
> - decision owner due_at next_review_at
> - follow up evidence required
> - shadow governance outcome template
> - append only review history
> - retirement verdict record

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Shadow Review Outcome Template](./README.md#shadow-review-outcome-template)
> - 다음 단계: [Shadow Forum Escalation Rules](./shadow-forum-escalation-rules.md)

## 핵심 개념

shadow review packet이 forum에 던지는 질문이라면, outcome template는 그 질문에 대한 **authoritative answer**다.

문제가 생기는 지점은 여기다.
packet은 표준화했는데 forum 결과를 자유 형식 회의록으로 남기면, 다음 주 packet generator는 prose를 해석해 state를 다시 추측해야 한다.
그러면 같은 entry가 week마다 다른 언어로 기록되고, `temporary_hold`와 `blocked`, `absorb 승인`과 `verification 연장` 같은 차이가 흐려진다.

그래서 outcome record는 회의 메모가 아니라 최소한 아래를 남기는 **post-forum decision contract**여야 한다.

- 어떤 packet에 대한 결정이었는가
- 현재 state에서 어떤 state로 옮겼는가
- 어떤 필드가 authoritative하게 바뀌었는가
- 누가 언제까지 follow-up을 맡는가
- 다음 closeout 전에 어떤 evidence가 더 필요할까

즉 shadow governance에서 packet과 outcome은 따로 노는 문서가 아니라, **같은 field 체계의 입력과 출력**이다.

---

## Template Insertion Points

shadow review outcome template는 회의 끝나고 남기는 한 줄 메모가 아니다.
같은 field 묶음이 아래 지점에 반복 노출돼야 symmetry가 유지된다.

- forum closeout log: 안건별 `decision_outcome`, `to_state`, `next_review_at`를 남긴다.
- catalog entry `history.decision_records[]`: append-only로 forum 결과를 적재한다.
- state transition event stream: automation이 `from_state`, `to_state`, `due_at`를 읽어 후속 queue를 만든다.
- next review packet generator: 직전 packet에 `field_updates`를 적용해 다음 projection을 렌더링한다.
- escalation memo: local forum에서 council로 올릴 때 같은 field명을 그대로 재사용한다.

삽입 지점을 맞춰 두면 packet, state machine, agenda, escalation note가 서로 다른 말을 하지 않는다.

---

## 깊이 들어가기

### 1. outcome record는 회의 요약이 아니라 authoritative delta여야 한다

회의에서는 긴 토론이 오갈 수 있다.
하지만 catalog 운영이 실제로 필요로 하는 것은 "무슨 말이 오갔는가"보다 "무엇이 바뀌었는가"다.

그래서 outcome template는 다음 원칙을 따르는 편이 좋다.

- packet은 현재 snapshot projection이다.
- outcome은 forum이 승인한 변경 사항과 다음 clock을 기록한다.
- narrative minutes는 따로 남겨도 되지만 canonical record는 structured field여야 한다.
- 다음 packet은 outcome record를 해석 없이 재생성할 수 있어야 한다.

즉 output이 prose 중심이면 사람이 없을 때 state transition이 끊기고, output이 delta 중심이면 packet과 automation이 같은 source를 읽을 수 있다.

### 2. 최소 outcome field는 packet의 field group을 대칭으로 받아야 한다

| field group | 최소 필드 | packet 쪽 의미 | outcome 쪽 의미 |
|---|---|---|---|
| identity / source | `outcome_id`, `source_packet_ref`, `catalog_id`, `forum`, `decided_at` | 어떤 안건을 올렸는지 식별 | 어떤 packet이 어떤 forum에서 닫혔는지 식별 |
| decision prompt | `decision_question`, `decision_outcome`, `decision_rationale` | forum이 풀어야 할 질문 | 그 질문에 대해 실제로 내려진 답 |
| state transition | `from_state`, `to_state`, `state_transition_reason` | packet이 보여 준 현재 상태 | forum 이후 authoritative한 다음 상태 |
| authoritative delta | `field_updates` | packet이 projection한 core field 묶음 | 어떤 필드가 유지/수정/추가됐는지 같은 field명으로 기록 |
| ownership / clock | `decision_owner`, `due_at`, `next_review_at`, `escalation_forum` | 현재 owner와 review clock | 이제 누가 움직이고 언제 다시 올라오는지 확정 |
| follow-up proof | `follow_up_evidence_required`, `verification_metric`, `exit_condition` | 다음 단계에서 확인할 evidence와 종료 조건 | 다음 packet 전에 새로 수집돼야 할 증빙 |

중요한 점은 output이 input보다 더 화려해야 한다는 뜻이 아니다.
오히려 packet과 outcome이 같은 field group을 공유해야 다음 packet을 다시 만들 때 해석 비용이 없어진다.

### 3. `field_updates`가 대칭성의 핵심이다

많은 forum 결과가 `approved absorb`, `keep monitoring`, `hold 연장`처럼 적힌다.
이 정도 문장만으로는 다음 packet generator가 실제로 무엇을 바꿔야 하는지 모른다.

그래서 outcome에는 최소한 `field_updates`가 필요하다.
이 블록에는 entry schema와 packet에서 쓰는 **동일한 field명**으로 변경값을 남긴다.

예:

- `target_decision: absorb`
- `target_system_or_process: rollout_override_registry`
- `replacement_path: registry_request_for_release_override`
- `blockers: [registry_missing_freeze_override_field]`
- `hold_reason: quarter_end_freeze`
- `expires_at: 2026-05-02`
- `verification_metric: manual_path_ratio`

핵심 규칙은 간단하다.

- output 전용 별칭을 만들지 않는다.
- packet/entry schema에 있는 field명을 그대로 쓴다.
- 바뀐 값만 delta로 남기되, 다음 packet이 읽어야 하는 값은 빠뜨리지 않는다.

이렇게 해야 input packet과 output record가 진짜로 symmetric해진다.

### 4. `decision_outcome`만으로는 state transition을 추론하게 두면 안 된다

`decision_outcome`은 label일 뿐이다.
실제 운영에는 transition이 더 중요하다.

예를 들어:

- `extend_hold`는 `temporary_hold -> temporary_hold`일 수 있다.
- `escalate_to_absorb`는 `decision_pending -> blocked`일 수도 있고 `temporary_hold -> absorb_in_progress`일 수도 있다.
- `retire_approved`는 `verification_pending -> retired`여야 의미가 닫힌다.

그래서 최소 record에는 항상 아래가 같이 있어야 한다.

- `from_state`
- `to_state`
- `state_transition_reason`

state transition을 prose에서 역추론하게 만들면 dashboard, cadence, reopen rule이 모두 흔들린다.

### 5. control state별 조건부 필드는 free-text memo보다 우선한다

core field만으로 충분하지 않은 경우가 있다.
특히 `temporary_hold`, `blocked`, `verification_pending`, `retired -> reopen` 전이는 조건부 필드가 필요하다.

권장 확장 규칙:

- hold 연장: `hold_reason`, `expires_at`, `resume_state`, `resume_trigger`
- blocked 진입: `blocked_from_state`, `blockers`, `blocker_owner`, `escalation_forum`
- verification closeout: `verification_metric`, `threshold_rule`, `verification_window`, `verification_evidence_ref`, `verdict_record`, `recurrence_check_at`
- reopen / successor: `reopen_reason`, `predecessor_catalog_id`, `successor_catalog_id`

여기서도 규칙은 같다.
별도 memo 문장을 늘리기보다 entry schema와 lifecycle 문서가 이미 쓰는 field명을 그대로 outcome에 실어야 한다.
특히 retirement closeout outcome이라면 [Shadow Retirement Scorecard Schema](./shadow-retirement-scorecard-schema.md)의 `verdict_record` shape를 그대로 복사해 `field_updates.retirement_tracking.last_verdict_record`에 넣는 편이 좋다.

### 6. outcome record는 append-only여야 다음 forum이 히스토리를 읽을 수 있다

forum이 결정을 바꿀 수는 있다.
하지만 이전 outcome를 조용히 수정하면, 다음 review는 "왜 방향이 바뀌었는지"를 잃어버린다.

그래서 운영 규칙은 보통 다음이 적절하다.

- 같은 안건의 후속 결정은 새 `outcome_id`로 append한다.
- clerical correction이 필요하면 `supersedes_outcome_id` 같은 링크로 정정한다.
- reopen이나 successor 분기는 새 outcome에 lineage를 남긴다.

즉 outcome template의 목적은 회의 결과를 예쁘게 적는 것이 아니라, **decision history를 packet-friendly하게 누적하는 것**이다.

---

## 코드로 보기

```yaml
shadow_review_outcome:
  outcome_template_version: shadow-review-outcome-minimum-v1
  outcome_id: shadow-review-2026-04-21-02
  source_packet_ref: shadow-review-packet-2026-04-21-02
  catalog_id: shadow-release-approval-001
  forum: domain-stewardship-shadow-review
  decided_at: 2026-04-21T10:30:00+09:00
  decision_question: absorb 경로로 승인하고 registry 필드 추가를 backlog로 받을 것인가
  decision_outcome: approve_absorb_with_followups
  decision_rationale: auditability risk가 높고 registry 확장이 가장 작은 replacement다
  from_state: decision_pending
  to_state: absorb_in_progress
  state_transition_reason: absorb 경로는 확정하고 세부 필드 보강은 follow-up action으로 분리한다
  field_updates:
    target_decision: absorb
    target_system_or_process: rollout_override_registry
    replacement_path: registry_request_for_release_override
    blockers:
      - registry_missing_freeze_override_field
    blocker_owner: platform-governance
  decision_owner: platform-governance
  due_at: 2026-04-30
  next_review_at: 2026-05-05
  follow_up_evidence_required:
    - registry_field_added
    - first_team_cutover_complete
  verification_metric: manual_path_ratio
  exit_condition: manual_path_ratio_zero_for_30d
```

이 record만 있으면 다음 packet generator는 entry를 다시 읽을 때 prose 해석 없이 어떤 state와 field를 보여 줘야 하는지 판단할 수 있다.

retirement closeout을 기록할 때는 같은 원칙으로 scorecard verdict를 복사한다.

```yaml
field_updates:
  retirement_tracking:
    verification_window:
      rule: longer_of_30d_or_2_review_cadences
      cadence_basis: monthly_exception_review
      minimum_cycles_required: 1
    last_verdict_record:
      status: retired
      decided_at: 2026-05-31T10:00:00+09:00
      reason_codes:
        - all_hard_gates_pass
        - window_satisfied
        - no_recurrence_detected
      outcome_ref: shadow-review-2026-05-31-01
```

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 자유 형식 회의록 | 작성이 빠르다 | 다음 packet과 automation이 prose를 해석해야 한다 | 피하는 편이 좋다 |
| 최소 outcome template | state transition과 owner/clock이 안정된다 | field discipline이 필요하다 | 기본 운영 모델 |
| outcome template + append-only history | revalidation, reopen, escalation audit이 쉬워진다 | 기록 체계 설계가 필요하다 | shadow governance를 실제로 굴릴 때 |

shadow review outcome template의 목적은 회의 결과를 남기는 것이 아니라, **packet input과 state-transition output을 같은 계약으로 닫아 다음 review와 automation이 해석 없이 이어지게 만드는 것**이다.

---

## 꼬리질문

- forum 결과만 읽고도 `from_state -> to_state`를 바로 알 수 있는가?
- `decision_outcome` 뒤에 실제 `field_updates`가 남아 있는가?
- 다음 packet generator가 prose를 읽지 않고도 review row를 다시 만들 수 있는가?
- `temporary_hold`, `blocked`, `verification_pending` 전이가 조건부 필드까지 같이 남는가?
- later reversal이나 reopen이 이전 outcome를 덮어쓰기 없이 append-only로 보이는가?

## 한 줄 정리

Shadow review outcome template는 shadow forum의 결정을 자유 형식 회의록이 아니라 packet과 같은 field 체계의 append-only decision record로 남겨, state transition과 다음 review packet이 해석 없이 이어지게 만드는 문서다.
