# Shadow Retirement Scorecard Schema

> 한 줄 요약: shadow retirement proof를 문서마다 다른 key로 적기 시작하면 `verification_pending`과 `retired` 판정이 drift하므로, scorecard record는 `verification_window`, `hard_gates`, `verdict_record`를 canonical field set으로 고정해 entry schema, proof example, lifecycle dashboard, review outcome이 같은 사실을 서로 다른 projection으로 읽게 해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)
> - [Shadow Lifecycle Scorecard Metrics](./shadow-lifecycle-scorecard-metrics.md)
> - [Shadow Review Outcome Template](./shadow-review-outcome-template.md)
> - [Shadow Packet Automation Mapping](./shadow-packet-automation-mapping.md)
> - [Shadow Catalog Reopen and Successor Rules](./shadow-catalog-reopen-and-successor-rules.md)
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)
> - [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)
> - [Mirror Lag SLA Calibration](./mirror-lag-sla-calibration.md)

> retrieval-anchor-keywords:
> - shadow retirement scorecard schema
> - retirement scorecard yaml json
> - shadow retirement hard gate schema
> - verification window schema
> - verdict record schema
> - threshold_rule canonical field
> - hard_gates canonical contract
> - retirement closeout record
> - verification_pending schema alignment
> - shadow docs example alignment
> - retirement proof json example
> - scorecard verdict recording
> - hard gate threshold object
> - scorecard schema version
> - last verdict record

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Shadow Retirement Scorecard Schema](./README.md#shadow-retirement-scorecard-schema)
> - 다음 단계: [Shadow Catalog Reopen and Successor Rules](./shadow-catalog-reopen-and-successor-rules.md)

## 핵심 개념

shadow retirement 문서가 많아질수록 같은 사실을 다른 이름으로 적는 문제가 생긴다.
어떤 문서는 `threshold`, 어떤 문서는 `exit_condition`, 어떤 문서는 `verdict`만 남기면 forum과 dashboard가 같은 closeout을 다르게 읽게 된다.

그래서 scorecard schema의 핵심은 계산식을 새로 만드는 것이 아니라, 아래 세 묶음을 같은 key로 고정하는 데 있다.

- `verification_window`: 언제부터 언제까지 어떤 cadence를 통과해야 하는가
- `hard_gates`: 어떤 metric이 어떤 threshold rule로 pass/fail/null인가
- `verdict_record`: 이번 evaluation이 어떤 상태를 기록했고 다음 lifecycle state를 무엇으로 남기는가

즉 이 문서는 metric 의미를 정의하는 proof 문서의 대체물이 아니라, **그 의미를 YAML/JSON에 어떻게 고정해 적을지 정하는 record contract**다.

---

## 깊이 들어가기

### 1. scorecard record는 "대시보드 숫자"가 아니라 "한 번의 closeout 판정"이어야 한다

한 scorecard record는 다음 셋을 함께 묶는다.

- 하나의 `catalog_id`
- 하나의 verification window
- 하나의 verdict

이 셋을 분리해 버리면 같은 hard gate를 어느 window에서 본 것인지, 현재 verdict가 어떤 forum outcome과 연결되는지 흐려진다.
그래서 scorecard는 장기 trend 시계열의 한 줄이면서 동시에 **그 시점의 authoritative evaluation snapshot**이어야 한다.

### 2. top-level field는 식별, 증빙 창, gate 결과, 판정 기록으로 나누는 편이 안정적이다

권장 top-level field set:

| field | required | 의미 |
|---|---|---|
| `scorecard_schema_version` | required | 문서 간 동일 shape를 강제하는 schema version |
| `scorecard_id` | required | 한 번의 evaluation attempt 식별자 |
| `catalog_id` | required | 어떤 shadow entry의 closeout인지 연결 |
| `computed_at` | required | 이 scorecard가 계산된 시각 |
| `baseline_snapshot_ref` | required | exception burndown 등 baseline 비교의 기준 |
| `source_refs[]` | recommended | 어떤 scorecard/export/audit artifact를 읽었는지 |
| `verification_window` | required | closeout window 자체의 규칙과 충족 여부 |
| `hard_gates` | required | hard gate별 threshold, measurement, pass/fail/null |
| `supporting_trends` | optional | verdict 보조용 건강도 지표 |
| `verdict_record` | required | 이번 evaluation이 기록한 최종 상태와 이유 |

여기서 중요한 점은 `supporting_trends`가 있어도 `verdict_record`는 오직 `verification_window`와 `hard_gates`를 기준으로만 기록해야 한다는 것이다.

### 3. `verification_window`는 날짜만이 아니라 cadence rule까지 같이 남겨야 한다

권장 field:

| field | required | 의미 |
|---|---|---|
| `window_id` | required | verification cycle 식별자 |
| `rule` | required | 예: `longer_of_30d_or_2_review_cadences` |
| `cadence_basis` | required | 어떤 review/operational cadence를 기준으로 보는지 |
| `started_at` | required | 창 시작 시각 |
| `ends_at` | required | 창 종료 시각 |
| `minimum_cycles_required` | required | 최소 통과해야 할 cadence/event 수 |
| `cycles_observed` | required | 실제 관측한 cadence/event 수 |
| `eligible_request_count` | required | 이 window에서 proof 대상이 된 request 수 |
| `window_satisfied` | required | 지금 이 window를 retirement 판정 근거로 써도 되는가 |

`started_at`과 `ends_at`만 남기고 `rule`과 `cadence_basis`를 빼면, monthly governance flow와 daily approval flow가 같은 30일 window로 오해된다.
shadow retirement에서는 조용한 기간이 아니라 **충분한 workflow 기회가 지나갔는가**가 중요하므로, window는 항상 rule을 포함해야 한다.

### 4. `hard_gates`는 metric map으로 두고, 각 gate가 같은 내부 shape를 가져야 한다

권장 metric key는 [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)의 hard gate 이름을 그대로 쓴다.

- `replacement_adoption_rate`
- `manual_path_ratio`
- `exception_burndown_remaining`
- `audit_log_coverage`
- `authoritative_off_plane_artifact_count`
- `mirror_breach_count`
- `recurrence_after_closure`

각 gate의 공통 field는 다음 정도가 적절하다.

| field | required | 의미 |
|---|---|---|
| `metric_key` | required | gate key의 self-description |
| `threshold_rule` | required | 어떤 operator와 target을 통과해야 하는가 |
| `measurement` | required | 현재 측정값과 관측 시각 |
| `measurement_status` | required | `complete`, `partial`, `missing` 중 하나 |
| `evidence_refs[]` | required | pass/fail 근거 artifact |
| `pass` | required | `true`, `false`, `null` |

`threshold_rule` 권장 하위 field:

- `operator`: `eq`, `lte`, `gte`
- `target`
- `unit`

`measurement` 권장 하위 field:

- `value`
- `measured_at`
- `sample_size`

gate별 확장 field도 허용하는 편이 좋다.

- `exception_burndown_remaining.baseline_snapshot_ref`
- `audit_log_coverage.completeness_rule`
- `recurrence_after_closure.lookback_ref`

핵심 규칙은 두 가지다.

- `measurement_status != complete`이면 `pass`는 `null`로 둔다
- `pass = null`인 gate가 하나라도 있으면 `verdict_record.status = retired`를 쓰지 않는다

### 5. `verdict_record`는 한 줄 label이 아니라 왜 그 state를 찍었는지 남겨야 한다

권장 field:

| field | required | 의미 |
|---|---|---|
| `status` | required | `retired`, `verification_pending`, `blocked`, `reopen_required` |
| `decided_at` | required | 이 verdict를 기록한 시각 |
| `recorded_by` | required | forum, automation, reviewer 등 기록 주체 |
| `decision_basis` | required | hard gate / window / telemetry / recurrence 기준 요약 |
| `reason_codes[]` | required | 왜 이 verdict가 나왔는지 machine-readable 이유 |
| `next_lifecycle_state` | required | catalog가 실제로 가져갈 다음 state |
| `outcome_ref` | recommended | review outcome record 또는 closeout memo ref |

`decision_basis`는 보통 다음 booleans를 가지는 편이 좋다.

- `all_hard_gates_passed`
- `verification_window_satisfied`
- `telemetry_complete`
- `recurrence_check_passed`

`reason_codes[]`는 prose 대신 운영 분류를 남기는 자리다.
예:

- `all_hard_gates_pass`
- `window_running`
- `gate_failed:manual_path_ratio`
- `telemetry_gap:audit_log_coverage`
- `recurrence_detected`

이 구조가 있어야 lifecycle dashboard는 `verdict_record.status`를 bucket으로 집계하고, review outcome은 같은 verdict를 append-only history로 복사할 수 있다.

### 6. entry, proof, dashboard, outcome은 같은 scorecard를 서로 다르게 projection해야 한다

문서별 권장 projection:

| consumer | 반드시 재사용할 canonical field |
|---|---|
| catalog entry schema | `scorecard_schema_ref`, 계획된 `verification_window`, 최신 `verdict_record` 요약 |
| retirement proof example | full `verification_window`, full `hard_gates`, full `verdict_record` |
| lifecycle dashboard | `hard_gates.*.pass`, `verification_window.window_satisfied`, `verdict_record.status` 집계 |
| review outcome template | 승인된 `verdict_record`와 `outcome_ref`를 append-only delta로 기록 |
| reopen/successor history | `scorecard_id`, `baseline_snapshot_ref`, `window_id`를 `retirement_attempts[]`에 보존 |

즉 dashboard가 새 key를 invent하거나 outcome이 `retired=true` 같은 축약형만 남기기 시작하면 canonical schema가 깨진다.

### 7. canonical schema는 full artifact와 summary field를 구분해야 한다

모든 consumer가 full scorecard를 그대로 들고 있을 필요는 없다.
대신 요약 필드를 만들더라도 원본 scorecard로 역참조할 수 있어야 한다.

권장 원칙:

- full artifact는 `shadow_retirement_scorecard`
- catalog entry에는 `scorecard_schema_ref`와 `last_verdict_record` 같은 summary만 둔다
- dashboard는 raw gate detail 대신 집계치만 보여 주되, breakdown drilldown은 원본 key명을 그대로 쓴다
- review outcome은 `field_updates.retirement_tracking.last_verdict_record`에 verdict 요약을 복사하고 `outcome_ref`를 남긴다

이렇게 해야 entry row가 과하게 비대해지지 않으면서도, 증빙 원문과 summary 사이의 drift를 줄일 수 있다.

---

## 코드로 보기

```yaml
shadow_retirement_scorecard:
  scorecard_schema_version: shadow-retirement-scorecard-v1
  scorecard_id: shadow-release-approval-001:2026-05-closeout
  catalog_id: shadow-release-approval-001
  computed_at: 2026-05-31T09:00:00+09:00
  baseline_snapshot_ref: baseline-2026-05-01
  source_refs:
    - kind: override_scorecard
      ref: override-scorecard-2026-q2
    - kind: audit_export
      ref: audit-export-2026-05-31
    - kind: exception_registry_snapshot
      ref: exception-registry-2026-05-31
  verification_window:
    window_id: vp-2026-05
    rule: longer_of_30d_or_2_review_cadences
    cadence_basis: monthly_exception_review
    started_at: 2026-05-01T00:00:00+09:00
    ends_at: 2026-05-31T23:59:59+09:00
    minimum_cycles_required: 1
    cycles_observed: 1
    eligible_request_count: 42
    window_satisfied: true
  hard_gates:
    replacement_adoption_rate:
      metric_key: replacement_adoption_rate
      threshold_rule:
        operator: eq
        target: 1.0
        unit: ratio
      measurement:
        value: 1.0
        measured_at: 2026-05-31T09:00:00+09:00
        sample_size: 42
      measurement_status: complete
      evidence_refs:
        - replacement-adoption-export-2026-05
      pass: true
    manual_path_ratio:
      metric_key: manual_path_ratio
      threshold_rule:
        operator: eq
        target: 0.0
        unit: ratio
      measurement:
        value: 0.0
        measured_at: 2026-05-31T09:00:00+09:00
        sample_size: 42
      measurement_status: complete
      evidence_refs:
        - override-scorecard-2026-q2
      pass: true
    exception_burndown_remaining:
      metric_key: exception_burndown_remaining
      threshold_rule:
        operator: eq
        target: 0
        unit: count
      measurement:
        value: 0
        measured_at: 2026-05-31T09:00:00+09:00
      measurement_status: complete
      baseline_snapshot_ref: baseline-2026-05-01
      evidence_refs:
        - exception-registry-2026-05-31
      pass: true
    audit_log_coverage:
      metric_key: audit_log_coverage
      threshold_rule:
        operator: eq
        target: 1.0
        unit: ratio
      measurement:
        value: 1.0
        measured_at: 2026-05-31T09:00:00+09:00
        sample_size: 42
      measurement_status: complete
      completeness_rule: request_id+actor+action+reason+decision_or_outcome+occurred_at
      evidence_refs:
        - audit-export-2026-05-31
      pass: true
    authoritative_off_plane_artifact_count:
      metric_key: authoritative_off_plane_artifact_count
      threshold_rule:
        operator: eq
        target: 0
        unit: count
      measurement:
        value: 0
        measured_at: 2026-05-31T09:00:00+09:00
      measurement_status: complete
      evidence_refs:
        - artifact-inventory-2026-05-31
      pass: true
    mirror_breach_count:
      metric_key: mirror_breach_count
      threshold_rule:
        operator: eq
        target: 0
        unit: count
      measurement:
        value: 0
        measured_at: 2026-05-31T09:00:00+09:00
      measurement_status: complete
      evidence_refs:
        - mirror-lag-report-2026-05-31
      pass: true
    recurrence_after_closure:
      metric_key: recurrence_after_closure
      threshold_rule:
        operator: eq
        target: 0
        unit: count
      measurement:
        value: 0
        measured_at: 2026-05-31T09:00:00+09:00
      measurement_status: complete
      evidence_refs:
        - recurrence-scan-2026-05-31
      pass: true
  supporting_trends:
    official_path_lead_time_p50_minutes: 16
    official_path_success_rate: 0.99
    operator_manual_steps_per_request: 0.2
  verdict_record:
    status: retired
    decided_at: 2026-05-31T10:00:00+09:00
    recorded_by: domain_stewardship_forum
    decision_basis:
      all_hard_gates_passed: true
      verification_window_satisfied: true
      telemetry_complete: true
      recurrence_check_passed: true
    reason_codes:
      - all_hard_gates_pass
      - window_satisfied
      - no_recurrence_detected
    next_lifecycle_state: retired
    outcome_ref: shadow-review-2026-05-31-01
```

같은 shape를 JSON으로 직렬화하면 다음처럼 읽힌다.

```json
{
  "scorecard_schema_version": "shadow-retirement-scorecard-v1",
  "scorecard_id": "shadow-release-approval-001:2026-05-closeout",
  "catalog_id": "shadow-release-approval-001",
  "computed_at": "2026-05-31T09:00:00+09:00",
  "baseline_snapshot_ref": "baseline-2026-05-01",
  "verification_window": {
    "window_id": "vp-2026-05",
    "rule": "longer_of_30d_or_2_review_cadences",
    "cadence_basis": "monthly_exception_review",
    "started_at": "2026-05-01T00:00:00+09:00",
    "ends_at": "2026-05-31T23:59:59+09:00",
    "minimum_cycles_required": 1,
    "cycles_observed": 1,
    "eligible_request_count": 42,
    "window_satisfied": true
  },
  "hard_gates": {
    "manual_path_ratio": {
      "metric_key": "manual_path_ratio",
      "threshold_rule": {
        "operator": "eq",
        "target": 0.0,
        "unit": "ratio"
      },
      "measurement": {
        "value": 0.0,
        "measured_at": "2026-05-31T09:00:00+09:00",
        "sample_size": 42
      },
      "measurement_status": "complete",
      "evidence_refs": [
        "override-scorecard-2026-q2"
      ],
      "pass": true
    }
  },
  "verdict_record": {
    "status": "retired",
    "decided_at": "2026-05-31T10:00:00+09:00",
    "recorded_by": "domain_stewardship_forum",
    "decision_basis": {
      "all_hard_gates_passed": true,
      "verification_window_satisfied": true,
      "telemetry_complete": true,
      "recurrence_check_passed": true
    },
    "reason_codes": [
      "all_hard_gates_pass",
      "window_satisfied",
      "no_recurrence_detected"
    ],
    "next_lifecycle_state": "retired",
    "outcome_ref": "shadow-review-2026-05-31-01"
  }
}
```

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 문서마다 예시 key를 자유롭게 둠 | 쓰기는 빠르다 | closeout, dashboard, outcome이 서로 다른 말을 한다 | 피하는 편이 좋다 |
| canonical scorecard schema | 문서 간 projection이 맞고 자동화가 쉬워진다 | field discipline이 필요하다 | 기본 권장안 |
| canonical schema + summary projection 분리 | entry는 가볍고 scorecard는 풍부하다 | 원본 ref 관리가 필요하다 | shadow governance가 상시 운영될 때 |

canonical schema의 목적은 YAML을 예쁘게 만드는 것이 아니라, **retirement 판정 근거를 문서마다 다른 말로 새로 쓰지 않게 막는 것**이다.

---

## 꼬리질문

- `verification_window`에 날짜만 있고 cadence rule이 빠져 있지 않은가?
- hard gate마다 `threshold_rule`과 `measurement_status`가 같이 남는가?
- `pass = null`인 telemetry gap을 `false`나 `0`으로 뭉개고 있지 않은가?
- `verdict_record.status`가 dashboard bucket과 review outcome에서 같은 값을 재사용하는가?
- reopen/successor를 만들 때 과거 `scorecard_id`와 `window_id`를 append-only로 보존하는가?

## 한 줄 정리

Shadow Retirement Scorecard Schema는 shadow retirement hard gate, verification window, verdict recording을 같은 key 집합으로 고정해 entry schema, proof scorecard, lifecycle dashboard, review outcome이 서로 해석 없이 이어지게 만드는 canonical contract다.
