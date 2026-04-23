# Threshold Override Governance

> 한 줄 요약: workflow-specific threshold override는 공통 default가 workflow의 위험도나 volume shape를 왜곡할 때만 허용하고, requester/metric owner/policy owner의 승인 분리를 거친 time-boxed 설정으로 다루며, `expires_at`, renewal cap, scorecard review 없이는 지속될 수 없게 해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Candidate Promotion Thresholds](./shadow-candidate-promotion-thresholds.md)
> - [Mirror Lag SLA Calibration](./mirror-lag-sla-calibration.md)
> - [Shadow Promotion Snapshot Schema Fields](./shadow-promotion-snapshot-schema-fields.md)
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)
> - [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)
> - [Emergency Misclassification Signals](./emergency-misclassification-signals.md)

> retrieval-anchor-keywords:
> - threshold override governance
> - workflow specific threshold override
> - shadow threshold override
> - promotion threshold override approval
> - workflow threshold exception
> - threshold override approver matrix
> - threshold override expiry
> - threshold override renewal cap
> - threshold override review cadence
> - threshold override registry
> - threshold override lineage
> - mirror breach threshold override
> - fast track threshold exception
> - migration backfill threshold override
> - low volume high risk threshold tuning
> - break glass threshold segmentation

## 핵심 개념

[Shadow Candidate Promotion Thresholds](./shadow-candidate-promotion-thresholds.md)의 공통 default는 팀마다 다른 해석을 줄이고 scorecard 비교 가능성을 유지하기 위한 것이다.
그래서 workflow-specific override는 "현장이 힘들다"는 감각만으로 열어 두면 안 되고, **공통 모델이 특정 workflow를 구조적으로 잘못 읽는 경우**에만 허용해야 한다.

좋은 override governance는 세 가지를 같이 묶는다.

- 언제 override가 정당한가
- 누가 approve하고 누가 veto할 수 있는가
- 언제 자동으로 끝나고, 연장 시 무엇을 다시 증명해야 하는가

즉 threshold override는 자유로운 tuning이 아니라, **공통 rule을 잠시 비틀되 다시 default로 돌아오게 만드는 time-boxed governance object**다.

---

## 깊이 들어가기

### 1. override는 default rule의 현실 적합성이 깨질 때만 허용해야 한다

허용 가능한 대표 경우는 다음과 같다.

| 허용 사유 | 왜 default가 왜곡되는가 | 보통 건드리는 값 |
|---|---|---|
| high-criticality / audit-required workflow | event 수가 작아도 governance risk가 크다 | `fast_track` 진입 조건, `mirror_breach` 허용치 |
| low-volume but high-risk workflow | `manual_request_count`, `distinct_days`가 recurrence를 과소평가한다 | `promote` tier 최소 count, incident 가중치 |
| temporary migration / backfill wave | 정상 운영 분모가 일시적으로 바뀐다 | 평가 window, cadence, `distinct_days` 해석 |
| break-glass / emergency path 분리 | emergency path가 normal path score를 오염시킨다 | threshold 완화가 아니라 별도 denominator/profile |

반대로 다음은 override 사유가 되면 안 된다.

- 팀이 common default를 귀찮아해서 local optimization을 하고 싶을 때
- 계측 품질이 약한데 threshold만 완화해 false positive를 숨길 때
- `synthetic_request_key_ratio`, `unresolved_source_ref_ratio` 같은 quality cap을 우회하고 싶을 때
- replacement path 없이 같은 override를 계속 연장하려 할 때

핵심은 override가 friction 해소가 아니라 **모델 보정**이어야 한다는 점이다.

### 2. override는 범위와 수명에 따라 class를 나눠야 한다

모든 override를 한 bucket으로 묶으면 approval과 expiry가 흐려진다.
보통은 아래처럼 분리하는 편이 안정적이다.

| class | 적용 범위 | 기본 수명 | review cadence | 메모 |
|---|---|---|---|---|
| `workflow_profile_override` | 단일 workflow, steady-state risk profile | 최대 90일 | monthly | 반복되면 permanent profile 승격 검토 |
| `temporary_wave_override` | migration/backfill/cutover 기간 | wave 종료 시점 또는 최대 30일 | weekly | `wave_exit_criteria`와 같이 닫아야 한다 |
| `emergency_provisional_override` | incident / break-glass 직후 | 최대 72시간 | next-business-day + incident closeout | 연장은 예외가 아니라 escalation이다 |

중요한 점은 "permanent override"를 기본 class로 두지 않는 것이다.
steady-state에서 계속 필요한 차이라면 override로 살려 두기보다, 공통 rule set의 profile 분기나 공식 policy 재설계로 흡수하는 편이 낫다.

### 3. 승인자는 request자와 분리되고, metric owner가 반드시 들어가야 한다

threshold override는 단순 정책 예외가 아니라 scorecard comparability를 바꾸는 일이다.
그래서 request자 혼자 승인하면 안 된다.

권장 approval matrix:

| scope | request자 | 필수 검토자 | 최종 승인자 |
|---|---|---|---|
| 단일 팀 / 단일 workflow | workflow owner | metric owner, local policy steward | local stewardship forum |
| 여러 팀에 걸친 shared workflow | workflow owner 또는 platform owner | metric owner, 영향 받는 domain owner들 | domain stewardship forum |
| 공통 default나 shared scorecard 해석을 바꾸는 경우 | workflow owner 또는 platform governance | metric owner, policy owner, architecture representative | architecture council / governance council |
| emergency provisional | incident commander | policy owner, metric owner | incident commander가 즉시 열 수 있으나 24시간 내 policy owner ratify 필수 |

여기서 metric owner가 빠지면 "이 override가 정말 workflow 특성 때문인지, 단순히 나쁜 계측 때문인지"를 구분하기 어렵다.
또한 request자와 최종 승인자를 분리해야 override가 local convenience로 굳는 것을 막을 수 있다.

### 4. override record는 rule diff와 종료 조건을 함께 남겨야 한다

override가 review 가능한 governance object가 되려면 최소 아래 필드를 남기는 편이 좋다.

- `override_id`
- `base_rule_ref`
- `workflow_key`
- `scope`
- `changed_threshold_fields`
- `baseline_values`
- `override_values`
- `allowed_because`
- `requested_by`
- `approved_by`
- `approved_at`
- `start_at`
- `expires_at`
- `review_every`
- `renewal_count`
- `exit_criteria`
- `fallback_on_expiry`
- `evidence_refs`

이 record는 prose 설명보다 **diff 가능한 config lineage**에 가깝게 남겨야 한다.
특히 [Shadow Promotion Snapshot Schema Fields](./shadow-promotion-snapshot-schema-fields.md)의 `promotion_rule_ref` 또는 별도 `threshold_override_ref`로 연결되면, 나중에 어떤 shadow candidate가 default rule이 아니라 override rule에 의해 승격됐는지 replay하기 쉬워진다.

### 5. expiry는 선택 필드가 아니라 hard gate여야 한다

override가 쌓이는 가장 흔한 이유는 `expires_at`이 비어 있거나, 만료돼도 실제로는 계속 쓰이기 때문이다.
그래서 enforcement는 다음처럼 두는 편이 좋다.

- 모든 override는 `expires_at` 필수, `null` 금지
- 만료 시 기본 동작은 `revert_to_default_threshold`
- 연장은 새 승인으로만 가능하고, 기존 record에 `renewal_count += 1`을 남긴다
- `renewal_count > 1` 또는 age가 class 최대 수명을 넘으면 forum escalation
- review에서 `exit_criteria` 진척이 없으면 extension이 아니라 redesign / officialization backlog로 넘긴다

즉 좋은 expiry는 "검토 예정"이 아니라, **재승인 없이는 살아남지 못하는 상태**를 뜻한다.

### 6. review는 count 확인이 아니라 renewal 정당성 검증이어야 한다

review cadence에서 봐야 할 것은 단순 age만이 아니다.

| review 질문 | 왜 필요한가 |
|---|---|
| 아직도 workflow shape mismatch가 실제로 존재하는가 | 원인 자체가 사라졌는데 override만 남는 것을 막는다 |
| override가 false positive / false negative를 줄였는가 | tuning이 실제로 모델 품질을 개선했는지 본다 |
| quality cap을 우회하지 않았는가 | 편한 local rule이 되지 않게 한다 |
| replacement path나 official profile 작업이 진행 중인가 | 영구 연장을 구조 개선으로 치환한다 |
| 같은 owner가 같은 사유로 반복 renewal 중인가 | 팀 문제보다 policy/profile 설계 문제를 찾게 한다 |

이 review 결과는 [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)의 scorecard와 연결돼야 한다.
즉 `expiring_soon`, `expired_but_active`, `renewal_count`, `same_owner_repeat`, `same_rule_repeat` 같은 panel이 있어야 override governance가 실제로 작동한다.

### 7. enforcement는 문서가 아니라 default-fallback와 forum gate로 끝나야 한다

사람이 잊어도 override가 계속 살아남지 않게 하려면 운영 장치를 같이 두는 편이 좋다.

- registry validation: `expires_at`, `approved_by`, `fallback_on_expiry` 없으면 저장 거부
- packet annotation: review packet과 catalog entry에 active override 여부를 노출
- scorecard panel: expiring/expired override, renewal concentration, shared-rule override count 표시
- forum gate: 두 번째 renewal부터는 local forum이 아니라 상위 governance forum으로 자동 escalation

특히 emergency provisional override는 [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)처럼 normal denominator와 분리해 보여야 한다.
그렇지 않으면 emergency를 핑계로 permanent threshold relaxation이 숨어 버린다.

---

## 실전 시나리오

### 시나리오 1: low-volume deprecation waiver workflow

waiver 요청 수는 월 1~2건뿐이지만, tier0 path에서 spreadsheet allowlist가 authoritative state다.
이 경우 `manual_request_count` 공통 default를 낮춘 `workflow_profile_override`는 허용 가능하다.
다만 workflow owner 혼자 결정하지 말고 metric owner와 policy owner가 같이 승인해야 한다.

### 시나리오 2: migration backfill 기간의 temporary override

2주 동안 backfill과 cutover rehearsal이 겹쳐 `distinct_days`와 mirror breach가 일시적으로 튄다.
이 경우 `temporary_wave_override`를 열 수 있지만, `wave_exit_criteria`와 `expires_at`이 없으면 허용하면 안 된다.
wave 종료 후 자동 revert되지 않으면 burn-down debt로 바로 잡혀야 한다.

### 시나리오 3: incident 직후 emergency provisional override

incident commander가 normal fast-track threshold를 우회해 즉시 shadow backlog에 올려야 할 수 있다.
이 경우는 72시간짜리 provisional override로 열 수 있다.
하지만 다음 영업일 review에서 ratify되지 않으면 종료되고, 재연장은 architecture/governance escalation로 올리는 편이 안전하다.

---

## 코드로 보기

```yaml
threshold_override:
  override_id: thr-ovr-041
  base_rule_ref: shadow-candidate-promotion-thresholds/default-v1
  workflow_key: tier0_deprecation_waiver_allowlist
  class: workflow_profile_override
  scope: single_workflow_shared_audit_path
  changed_threshold_fields:
    fast_track.manual_request_count_gte: 1
    promote.distinct_days_gte: 1
  baseline_values:
    fast_track.manual_request_count_gte: 2
    promote.distinct_days_gte: 2
  override_values:
    fast_track.manual_request_count_gte: 1
    promote.distinct_days_gte: 1
  allowed_because:
    - low_volume_high_risk
    - authoritative_off_plane_state
  unchanged_caps:
    - synthetic_request_key_ratio_gt_0_3
    - unresolved_source_ref_ratio_gt_0_2
  requested_by: payments-workflow-owner
  approved_by:
    - metrics-steward
    - platform-policy-owner
    - architecture-council
  start_at: 2026-04-14
  expires_at: 2026-05-14
  review_every: weekly
  renewal_count: 0
  exit_criteria:
    - allowlist_moved_to_control_plane
    - off_plane_sheet_retired
  fallback_on_expiry: revert_to_default_threshold
  evidence_refs:
    - override-scorecard-2026-04
    - packet-shadow-waiver-012
```

좋은 override record는 "왜 예외를 줬는가"뿐 아니라 "어떻게 default로 돌아갈 것인가"를 구조적으로 보여 준다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| override 금지 | 비교 가능성이 높다 | 실제 high-risk / low-volume workflow를 놓친다 | 매우 드문 규제 고정 경로 |
| local override 허용, 승인 약함 | 빠르다 | local optimization과 영구 예외가 쌓인다 | 피하는 편이 좋다 |
| time-boxed governed override | 현실 적합성과 comparability를 같이 잡는다 | registry와 review discipline이 필요하다 | 기본 권장 |
| 반복 override를 공식 profile로 승격 | 장기 운영이 안정적이다 | 공통 rule 설계 비용이 든다 | 같은 override가 재발할 때 |

threshold override governance의 목적은 tuning 자유도를 주는 것이 아니라, **공통 default를 깨야 하는 순간을 좁게 정의하고 그 예외가 다시 default로 수렴하게 만드는 것**이다.

---

## 꼬리질문

- 이 override는 workflow 특성 보정인가, 단순 local convenience인가?
- requester와 approver, metric owner가 분리돼 있는가?
- `expires_at`과 `fallback_on_expiry` 없이 사실상 permanent override를 열고 있지는 않은가?
- 같은 workflow가 renewal을 반복한다면 override가 아니라 공식 profile 재설계가 필요한 것 아닌가?
- quality cap은 그대로 두고 threshold만 조정했는가, 아니면 계측 품질 문제를 숨기고 있는가?

## 한 줄 정리

Threshold override governance는 workflow별 threshold 예외를 좁은 허용 사유, 분리된 승인권, 강제 expiry/review, default fallback으로 묶어 common scorecard comparability를 지키면서도 실제 workflow 위험도를 왜곡하지 않게 만드는 운영 규약이다.
