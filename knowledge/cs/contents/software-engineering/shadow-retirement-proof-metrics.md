---
schema_version: 3
title: Shadow Retirement Proof Metrics
concept_id: software-engineering/shadow-retirement-proof-metrics
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- shadow-process
- retirement-proof
- scorecard
- verification
aliases:
- shadow retirement proof metrics
- shadow process closed vs retired
- manual_path_ratio zero
- retirement hard gates
- shadow retirement scorecard
- shadow retirement 증빙 지표
symptoms:
- shadow process ticket을 closed로 표시했지만 manual_path_ratio, exception burndown, audit_log_coverage, recurrence 부재를 확인하지 않아
- weighted score가 높다는 이유로 off-plane source나 recurrence hard gate failure를 덮고 retired로 전이해
- verification window가 workflow cadence를 충분히 지나지 않았는데 조용했다는 이유만으로 retirement를 선언해
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/shadow-process-catalog-retirement
- software-engineering/shadow-catalog-lifecycle-states
next_docs:
- software-engineering/shadow-retirement-scorecard-schema
- software-engineering/shadow-catalog-reopen-successor-rules
- software-engineering/shadow-lifecycle-scorecard-metrics
linked_paths:
- contents/software-engineering/shadow-process-catalog-and-retirement.md
- contents/software-engineering/shadow-catalog-lifecycle-states.md
- contents/software-engineering/shadow-process-catalog-entry-schema.md
- contents/software-engineering/shadow-retirement-scorecard-schema.md
- contents/software-engineering/shadow-catalog-reopen-and-successor-rules.md
- contents/software-engineering/manual-path-ratio-instrumentation.md
- contents/software-engineering/shadow-lifecycle-scorecard-metrics.md
- contents/software-engineering/break-glass-path-segmentation.md
- contents/software-engineering/override-burndown-review-cadence-scorecards.md
- contents/software-engineering/shadow-process-officialization-absorption-criteria.md
- contents/software-engineering/consumer-exception-operating-model.md
- contents/software-engineering/consumer-exception-state-machine-review-cadence.md
- contents/software-engineering/consumer-exception-registry-quality-automation.md
confusable_with:
- software-engineering/shadow-retirement-scorecard-schema
- software-engineering/shadow-lifecycle-scorecard-metrics
- software-engineering/shadow-catalog-reopen-successor-rules
forbidden_neighbors: []
expected_queries:
- shadow process에서 closed와 retired를 구분하려면 어떤 hard gate metrics를 통과해야 해?
- manual_path_ratio, exception_burndown_remaining, audit_log_coverage는 각각 어떤 retirement 착시를 막아?
- authoritative_off_plane_artifact_count와 recurrence_after_closure가 0이어야 retired로 볼 수 있는 이유는?
- retirement proof를 weighted total score보다 hard gate matrix로 보는 이유를 설명해줘
- verification window를 calendar day가 아니라 workflow cadence와 실제 event 기준으로 잡는 방법은?
contextual_chunk_prefix: |
  이 문서는 shadow process를 retired로 닫기 전에 replacement adoption, manual_path_ratio, exception burndown, audit log coverage, off-plane state, mirror breach, recurrence hard gate를 검증하는 advanced playbook이다.
---
# Shadow Retirement Proof Metrics

> 한 줄 요약: shadow process를 `closed`로 표시했다고 retirement가 증명되는 것은 아니며, `manual_path_ratio = 0`, old-path exception burndown 완료, `audit_log_coverage = 1.0`, off-plane state 제거, recurrence 부재를 같은 scorecard와 threshold로 통과해야 비로소 `retired`라고 말할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)
> - [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Retirement Scorecard Schema](./shadow-retirement-scorecard-schema.md)
> - [Shadow Catalog Reopen and Successor Rules](./shadow-catalog-reopen-and-successor-rules.md)
> - [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)
> - [Shadow Lifecycle Scorecard Metrics](./shadow-lifecycle-scorecard-metrics.md)
> - [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)
> - [Consumer Exception Operating Model](./consumer-exception-operating-model.md)
> - [Consumer Exception State Machine and Review Cadence](./consumer-exception-state-machine-review-cadence.md)
> - [Consumer Exception Registry Quality and Automation](./consumer-exception-registry-quality-automation.md)

> retrieval-anchor-keywords:
> - shadow retirement proof metrics
> - shadow retirement scorecard schema
> - retirement metric proof patterns
> - shadow retirement scorecard
> - shadow process closed vs retired
> - shadow retirement threshold
> - verification pending exit gate
> - manual_path_ratio zero
> - exception burndown retirement
> - audit log coverage retirement
> - shadow retirement exit signals
> - recurrence after closure
> - authoritative off plane artifact count
> - replacement adoption rate
> - audit trail coverage official path
> - shadow retirement evidence
> - prove shadow path retired
> - false closure shadow process
> - shadow process verification window
> - retirement verification health
> - retirement baseline snapshot
> - reopen after recurrence
> - successor after recurrence

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Shadow Retirement Proof Metrics](./README.md#shadow-retirement-proof-metrics)
> - 다음 단계: [Shadow Retirement Scorecard Schema](./shadow-retirement-scorecard-schema.md)

## 핵심 개념

shadow process에서 가장 흔한 착시는 "티켓을 닫았으니 정리됐다"는 판단이다.
하지만 실제 retirement는 다음이 같이 보여야 한다.

- 공식 replacement path가 실제 요청을 처리한다
- DM, sheet, local file 같은 old path가 더 이상 authoritative source가 아니다
- old path에 묶여 있던 override, waiver, allowlist가 baseline 대비 모두 소거됐다
- 공식 path를 탄 eligible request마다 actor/action/reason이 audit log에 남는다
- 같은 shadow signal이 verification window 동안 재발하지 않는다

즉 retirement proof는 문서 상태가 아니라 **사용 행태와 예외 부채 소거와 추적 가능성과 재발 여부를 같이 보는 증빙**이다.

---

## 깊이 들어가기

### 1. `closed`와 `retired`는 다르다

`closed`는 보통 다음 중 하나를 뜻한다.

- catalog entry에 종료 메모를 남겼다
- replacement runbook/control plane이 배포됐다
- owner가 "이제 안 쓴다"고 보고했다

반면 `retired`는 더 강한 주장이다.

- old path가 실제 요청을 더 이상 먹지 않는다
- off-plane artifact가 source of truth 역할을 하지 않는다
- recurrence가 observation window 동안 다시 나타나지 않는다

그래서 shadow catalog에서는 `closed`를 verdict로 쓰기보다, `verification_pending`과 `retired`를 분리해 두는 편이 안전하다.

### 2. retirement 판정은 weighted total score보다 hard gate가 먼저다

shadow retirement scorecard는 종합 점수 한 줄보다 hard gate를 먼저 보는 편이 좋다.
가중 합계는 보기 편하지만, recurrence 1건이나 off-plane source 1개를 다른 지표 개선으로 가려 버릴 수 있다.
포트폴리오 대시보드에서 `verification_pending` health를 요약할 때도 이 원칙은 그대로 유지해야 하며, [Shadow Lifecycle Scorecard Metrics](./shadow-lifecycle-scorecard-metrics.md)처럼 status bucket과 failed gate matrix를 쓰되 lifecycle verdict는 hard gate로만 넘기는 편이 안전하다.

권장 방식:

- hard gate: 하나라도 fail이면 `retired` 불가
- supporting trend: replacement path 건강도와 운영 부담을 보는 보조 축

즉 "점수가 87점이라 거의 retired" 같은 문장은 dashboard 설명에는 쓸 수 있어도, lifecycle state 전이 근거로는 약하다.

### 3. proof scorecard에는 최소 일곱 개의 hard metric이 필요하다

| 증명 축 | metric | 기본 threshold | 왜 필요한가 |
|---|---|---|---|
| 공식 경로 채택 | `replacement_adoption_rate` | `1.0` for eligible requests in window | replacement가 실제로 old path를 대체했는지 본다 |
| 수동 경로 사용 | `manual_path_ratio` | `0` | DM/sheet/off-plane path가 아직 실제 요청을 먹는지 본다 |
| 예외 부채 소거 | `exception_burndown_remaining` | `0` from retirement baseline snapshot | old path를 전제로 시작한 override/waiver/allowlist가 하나도 남지 않았는지 본다 |
| 공식 감사 추적 | `audit_log_coverage` | `1.0` for eligible official-path requests | 공식 경로가 request마다 actor/action/reason을 남기는지 본다 |
| off-plane authoritative state | `authoritative_off_plane_artifact_count` | `0` | shadow path의 핵심 상태 저장소가 남아 있는지 본다 |
| mirror discipline | `mirror_breach_count` | `0` | DM에서 결정 후 공식 plane 반영이 늦는 hidden state가 남았는지 본다 |
| recurrence | `recurrence_after_closure` | `0` | 같은 candidate key가 다시 나타나는지 본다 |

여기서 `manual_path_ratio`와 `mirror_breach_count`의 numerator/denominator 규칙은 [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)처럼 공통 계측 문서에 고정해 두는 편이 좋다.
반대로 `exception_burndown_remaining`은 retirement decision 시점에 찍어 둔 baseline snapshot과 [Consumer Exception State Machine and Review Cadence](./consumer-exception-state-machine-review-cadence.md), [Consumer Exception Registry Quality and Automation](./consumer-exception-registry-quality-automation.md)의 상태 검증을 같이 써야 해석이 흔들리지 않는다.
또한 `audit_log_coverage`는 [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)처럼 normal path와 emergency path의 denominator를 분리한 뒤 계산해야 "긴급 예외를 조용히 숨긴 100%"를 피할 수 있다.

### 4. `manual_path_ratio`, exception burndown, audit-log coverage는 서로 다른 착시를 막는다

shadow retirement에서 가장 위험한 오판은 한 지표만 좋아진 것을 전체 retirement로 해석하는 것이다.
세 신호는 각각 다른 종류의 착시를 막는다.

| exit signal | 막는 착시 | fail일 때 의미 |
|---|---|---|
| `manual_path_ratio` | "DM이 줄었으니 shadow path가 끝났다" | 실제 request가 여전히 off-plane으로 새고 있다 |
| `exception_burndown_remaining` | "예외는 곧 닫힐 테니 retirement를 먼저 선언해도 된다" | old path를 전제로 한 waiver/allowlist/deprecation exception이 아직 살아 있다 |
| `audit_log_coverage` | "공식 tool만 열어 두면 사용 증빙도 자동으로 생긴다" | 공식 path가 실제로 쓰이더라도 actor, decision, reason을 나중에 재구성할 수 없다 |

세 지표는 각각 flow removal, debt removal, traceability restoration을 본다.
셋 중 하나라도 빠지면 shadow path는 사라진 것이 아니라 다른 곳으로 숨었을 가능성이 높다.

### 5. exception burndown과 audit-log coverage는 계산 규칙을 문장으로 남겨야 한다

두 지표는 이름만 catalog에 적어 두면 팀마다 다른 숫자가 나온다.
그래서 exit signal에는 계산식과 completeness rule을 같이 남기는 편이 안전하다.

```text
exception_burndown_remaining
  = count(distinct exception_id
      where baseline_old_path_dependency = true
        and status in {proposed, approved, active, expiring, blocked})
```

```text
audit_log_coverage
  = count(distinct request_id
      where eligible_for_official_path = true
        and official_audit_record_present = true
        and audit_record_complete = true)
    / count(distinct request_id where eligible_for_official_path = true)
```

실무에서 같이 고정할 규칙:

- `baseline_old_path_dependency`는 `verification_pending` 진입 시점이나 retirement decision 시점에 snapshot으로 고정한다
- 새로 발견된 old-path exception은 분모에서 빼지 말고 reopen 또는 successor entry로 처리한다
- `audit_record_complete`는 최소 `request_id`, `actor`, `action`, `target_or_policy_key`, `decision_or_outcome`, `reason`, `occurred_at`를 포함한다
- 고위험 workflow라면 `approval_ref`, `artifact_hash`, `runbook_version`까지 completeness rule에 넣는 편이 좋다

여기서 reopen과 successor를 가르는 기준은 단순히 "재발했다"가 아니라, 같은 path와 같은 replacement continuity를 계속 주장할 수 있는가다.
이 판단 기준과 predecessor/history 규칙은 [Shadow Catalog Reopen and Successor Rules](./shadow-catalog-reopen-and-successor-rules.md)처럼 별도 문서로 고정해 두는 편이 좋다.

hard gate는 `exception_burndown_remaining == 0`과 `audit_log_coverage == 1.0`이고, completion percentage나 missing-field count는 trend panel에 두는 편이 맞다.

### 6. supporting trend는 verdict 보조용으로만 쓴다

다음 지표는 retirement 자체를 증명하기보다, replacement path가 건강한지 보는 보조 축이다.

- `official_path_lead_time_p50` / `p95`
- `official_path_success_rate`
- `redirect_to_official_rate`
- `shadow_candidate_count`
- `operator_manual_steps_per_request`

예를 들어 `manual_path_ratio == 0`, `exception_burndown_remaining == 0`, `audit_log_coverage == 1.0`이어도 official path lead time이 기존보다 크게 악화되면, shadow recurrence가 곧 다시 생길 가능성이 높다.
하지만 이 경우도 상태는 우선 `retired`가 아니라 `verification_pending` 유지 또는 재개선 backlog로 처리하는 편이 낫다.

### 7. threshold는 calendar day가 아니라 workflow cadence에 맞춰야 한다

검증 창은 "30일"처럼 고정 숫자만으로 잡으면 안 된다.
드문 workflow는 조용해서 retired처럼 보이고, 자주 도는 workflow는 반대로 너무 빨리 결론이 나기 쉽다.

권장 규칙:

| workflow 성격 | 기본 verification window |
|---|---|
| 일상적 approval / exception / support 흐름 | `30일` 그리고 `2회 연속 review cadence` 중 더 긴 쪽 |
| release / rollout / cutover 흐름 | `실제 이벤트 2회` 또는 `실제 1회 + rehearsal 1회` |
| 월간 / 분기성 governance 흐름 | `1 full business cycle`과 `마감 경계 1회 통과` |
| 희귀하지만 고위험인 emergency 흐름 | 침묵만으로 retired 판정 금지, `drill evidence + artifact audit` 필수 |

핵심은 "충분히 오래 조용했는가"가 아니라, **그 workflow가 실제로 다시 일어날 기회를 충분히 거쳤는가**다.

### 8. 다음 상황은 무조건 `retired`를 막아야 한다

- hard metric 중 하나라도 측정 불가다
- eligible request가 0이라 `replacement_adoption_rate`와 `manual_path_ratio`가 무의미하다
- retirement baseline snapshot이 없어 `exception_burndown_remaining`를 검증할 수 없다
- `audit_log_coverage < 1.0` 이거나 `audit_record_complete` 규칙이 정해지지 않았다
- 공식 tool은 열렸지만 sheet/notion/local file이 여전히 authoritative source다
- `recurrence_after_closure > 0` 이다
- old path를 전제로 한 open exception, allowlist, manual checklist가 남아 있다

이때 권장 상태는 보통 다음 둘 중 하나다.

- `verification_pending`: replacement는 열렸지만 증빙 window가 아직 부족하다
- `blocked`: telemetry 결손, owner 부재, artifact 회수 실패처럼 구조적 이유로 증빙 자체가 안 된다

즉 "증거가 없으니 retired로 치자"가 아니라, **증거가 없으면 retired로 못 간다**가 기본 규칙이다.

### 9. break-glass는 shadow와 분리된 공식 예외여야 한다

많은 조직이 "긴급 시 DM"을 fallback로 남겨 두고 retired라고 적는다.
이건 보통 가짜 종료다.

진짜 retirement가 되려면:

- break-glass path가 공식 policy에 명시돼 있어야 한다
- owner, expires_at, audit trail이 있어야 한다
- scorecard에서 normal path와 separate denominator로 측정돼야 한다

문서에 없는 emergency DM을 남겨 두었다면 old shadow path를 다른 이름으로 보존한 것에 가깝다.

### 10. catalog entry에는 metric 이름만이 아니라 threshold와 window까지 저장해야 한다

[Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)의 `retirement_tracking`에는 보통 다음이 같이 들어가야 한다.

- `scorecard_schema_ref`
- `verification_metric`
- `threshold_rule`
- `verification_window`
- `verification_source`
- `baseline_snapshot_ref`
- `audit_log_rule`
- `recurrence_check_at`
- `last_verdict_record`

`verification_metric = manual_path_ratio`만 적고 threshold를 안 남기면, 어느 팀은 `0`, 어느 팀은 `5% 미만`을 같은 retired로 해석하게 된다.
또 `exception_burndown_remaining`를 적으면서 baseline snapshot ref를 안 남기면, 어떤 예외를 "남아 있는 debt"로 봐야 하는지 팀마다 달라진다.
`audit_log_coverage`도 completeness rule 없이 적으면, 어느 팀은 actor/action만 있으면 pass라고 보고 어느 팀은 reason/approval_ref 누락을 fail로 본다.
그래서 entry에는 "무슨 지표를 볼 것인가"뿐 아니라 **어느 숫자와 어느 기간을 통과해야 하는가**를 같이 남겨야 한다.
실제 scorecard artifact shape는 [Shadow Retirement Scorecard Schema](./shadow-retirement-scorecard-schema.md)처럼 `scorecard_schema_version`, `verification_window`, `hard_gates`, `verdict_record`를 고정해 두는 편이 예시 drift를 줄인다.

### 11. 권장 verdict rule은 단순해야 한다

권장 판정은 다음처럼 두는 편이 안정적이다.

```text
retired if and only if:
  all hard gates pass
  and verification window is satisfied
  and recurrence_after_closure == 0
else:
  remain verification_pending or move back to *_in_progress / blocked
```

이 규칙의 장점은 간단하다.

- review forum이 해석을 덜 놓친다
- reopen 이유가 분명하다
- 대시보드 점수와 lifecycle state를 섞어 쓰지 않게 된다

---

## 실전 시나리오

### 시나리오 1: DM 승인은 없어졌지만 spreadsheet가 여전히 source of truth다

이 경우 `manual_path_ratio`가 낮아져도 `authoritative_off_plane_artifact_count > 0` 이므로 retired가 아니다.
shadow state 저장소가 남아 있기 때문이다.

### 시나리오 2: 최근 2주간 조용하지만 eligible request도 없었다

이 경우 지표가 0처럼 보여도 proof가 아니다.
verification window가 workflow cadence를 충분히 통과하지 못했으므로 `verification_pending`이 맞다.

### 시나리오 3: DM 요청은 사라졌지만 old-path waiver 2건이 아직 active다

이 경우 `manual_path_ratio == 0`이어도 `exception_burndown_remaining = 2` 이므로 retired가 아니다.
official path가 열렸더라도 old path를 전제로 한 부채가 남아 있으면 종료가 아니라 병행 운영이다.

### 시나리오 4: 공식 tool은 쓰이지만 승인 사유와 actor가 audit log에 반쯤 빠진다

이 경우 `audit_log_coverage < 1.0` 이므로 retired 판정이 약하다.
shadow path가 사라진 것이 아니라, 나중에 누가 어떤 판단을 했는지 재구성하지 못하는 blind spot이 남아 있기 때문이다.

### 시나리오 5: monthly review에서 닫았는데 다음 달 같은 policy key로 다시 DM 요청이 생겼다

이 경우 `recurrence_after_closure = 1` 이므로 retired를 유지하면 안 된다.
같은 entry를 reopen하거나 successor entry를 만들고 predecessor를 링크해야 한다.

### 시나리오 6: release cutover 절차라 실사용 빈도가 낮다

이 경우 30일 무사고만으로 retired를 선언하면 안 된다.
적어도 실제 cutover 한 번과 rehearsal 한 번, 또는 실제 이벤트 두 번을 old path 없이 통과해야 한다.

---

## 코드로 보기

```yaml
shadow_retirement_scorecard:
  scorecard_schema_version: shadow-retirement-scorecard-v1
  scorecard_id: shadow-deprecation-dm-001:2026-05-closeout
  catalog_id: shadow-deprecation-dm-001
  computed_at: 2026-05-01T09:00:00+09:00
  baseline_snapshot_ref: ex-baseline-2026-04-01
  source_refs:
    - kind: override_scorecard
      ref: override-scorecard-2026-q2
    - kind: audit_export
      ref: audit-export-2026-05-01
  verification_window:
    window_id: vp-2026-04
    rule: longer_of_30d_or_2_review_cadences
    cadence_basis: monthly_exception_review
    started_at: 2026-04-01T00:00:00+09:00
    ends_at: 2026-05-01T00:00:00+09:00
    minimum_cycles_required: 1
    cycles_observed: 1
    eligible_request_count: 24
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
        measured_at: 2026-05-01T09:00:00+09:00
        sample_size: 24
      measurement_status: complete
      evidence_refs:
        - replacement-adoption-export-2026-04
      pass: true
    manual_path_ratio:
      metric_key: manual_path_ratio
      threshold_rule:
        operator: eq
        target: 0.0
        unit: ratio
      measurement:
        value: 0.0
        measured_at: 2026-05-01T09:00:00+09:00
        sample_size: 24
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
        measured_at: 2026-05-01T09:00:00+09:00
      measurement_status: complete
      baseline_snapshot_ref: ex-baseline-2026-04-01
      evidence_refs:
        - exception-registry-2026-05-01
      pass: true
    audit_log_coverage:
      metric_key: audit_log_coverage
      threshold_rule:
        operator: eq
        target: 1.0
        unit: ratio
      measurement:
        value: 1.0
        measured_at: 2026-05-01T09:00:00+09:00
        sample_size: 24
      measurement_status: complete
      completeness_rule: actor+action+reason+outcome+request_id+timestamp
      evidence_refs:
        - audit-export-2026-05-01
      pass: true
    authoritative_off_plane_artifact_count:
      metric_key: authoritative_off_plane_artifact_count
      threshold_rule:
        operator: eq
        target: 0
        unit: count
      measurement:
        value: 0
        measured_at: 2026-05-01T09:00:00+09:00
      measurement_status: complete
      evidence_refs:
        - artifact-inventory-2026-05-01
      pass: true
    mirror_breach_count:
      metric_key: mirror_breach_count
      threshold_rule:
        operator: eq
        target: 0
        unit: count
      measurement:
        value: 0
        measured_at: 2026-05-01T09:00:00+09:00
      measurement_status: complete
      evidence_refs:
        - mirror-lag-report-2026-05-01
      pass: true
    recurrence_after_closure:
      metric_key: recurrence_after_closure
      threshold_rule:
        operator: eq
        target: 0
        unit: count
      measurement:
        value: 0
        measured_at: 2026-05-01T09:00:00+09:00
      measurement_status: complete
      evidence_refs:
        - recurrence-scan-2026-05-01
      pass: true
  supporting_trends:
    official_path_lead_time_p50_minutes: 18
    official_path_success_rate: 0.99
    exception_burndown_completion: 1.0
    shadow_candidate_count: 0
  verdict_record:
    status: retired
    decided_at: 2026-05-01T10:00:00+09:00
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
    outcome_ref: shadow-review-2026-05-01-03
```

중요한 점은 `verdict_record.status: retired`보다 위에 있는 hard gate와 `verification_window.window_satisfied`가 먼저라는 것이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 종료 메모만 남김 | 가장 빠르다 | 가짜 종료가 많다 | 피하는 편이 좋다 |
| percentage trend 중심 scorecard | 대시보드가 보기 쉽다 | recurrence와 off-plane source를 가릴 수 있다 | 건강도 모니터링 |
| hard gate + cadence window | retired 판정이 선명하다 | 계측 discipline이 필요하다 | 실제 retirement 판정 |

retirement proof의 목적은 숫자를 많이 만드는 것이 아니라, **shadow path가 정말 사라졌는지 거짓 없이 말할 수 있게 하는 것**이다.

---

## 꼬리질문

- `manual_path_ratio == 0`만 보지 않고 authoritative artifact 제거까지 같이 보고 있는가?
- `exception_burndown_remaining`의 baseline snapshot이 review forum에 고정돼 있는가?
- `audit_log_coverage`가 actor/action/reason completeness까지 포함하는가?
- verification window가 calendar가 아니라 workflow cadence를 반영하는가?
- eligible request가 0인 조용한 기간을 증빙으로 착각하고 있지는 않은가?
- recurrence가 생기면 reopen rule이 자동으로 연결되는가?
- break-glass를 shadow fallback과 구분해 공식 policy로 분리했는가?

## 한 줄 정리

Shadow Retirement Proof Metrics는 shadow process를 "닫았다"고 적는 수준을 넘어서, `manual_path_ratio`, exception burndown, audit-log coverage, off-plane state 제거, recurrence 부재를 같은 hard gate로 통과했을 때만 `retired`라고 판정하게 만드는 검증 scorecard다.
