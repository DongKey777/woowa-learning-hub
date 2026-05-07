---
schema_version: 3
title: Shadow Promotion Snapshot Schema Fields
concept_id: software-engineering/shadow-promotion-snapshot-schema-fields
canonical: true
category: software-engineering
difficulty: advanced
doc_role: primer
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- shadow-process
- promotion-snapshot
- schema
- provenance
aliases:
- shadow promotion snapshot schema fields
- promotion_snapshot block
- promotion snapshot minimum fields
- catalog entry promotion tier confidence
- shadow intake provenance
- shadow 승격 스냅샷 필드
symptoms:
- promotion_tier와 promotion_confidence만 남기고 shadow_candidate_key, rule_ref, window, threshold_snapshot이 없어 왜 catalog에 들어왔는지 replay할 수 없어
- fast_track hard gate와 confidence cap을 packet summary에서 숨겨 forum이 승격 이유를 다시 추측해
intents:
- definition
- design
- deep_dive
prerequisites:
- software-engineering/shadow-candidate-promotion-thresholds
- software-engineering/shadow-process-catalog-entry-schema
next_docs:
- software-engineering/break-glass-segmentation
- software-engineering/shadow-review-packet-template
- software-engineering/shadow-packet-automation-mapping
linked_paths:
- contents/software-engineering/shadow-candidate-promotion-thresholds.md
- contents/software-engineering/shadow-process-catalog-entry-schema.md
- contents/software-engineering/shadow-review-packet-template.md
- contents/software-engineering/shadow-packet-automation-mapping.md
- contents/software-engineering/shadow-process-detection-signals.md
- contents/software-engineering/manual-path-ratio-instrumentation.md
- contents/software-engineering/mirror-lag-sla-calibration.md
confusable_with:
- software-engineering/shadow-candidate-promotion-thresholds
- software-engineering/shadow-review-packet-template
- software-engineering/shadow-process-catalog-entry-schema
forbidden_neighbors: []
expected_queries:
- shadow promotion_snapshot에는 tier, confidence, evaluated_at, shadow_candidate_key, rule_ref, window를 왜 남겨야 해?
- promotion tier와 target_state.decision은 왜 intake provenance와 future decision으로 분리해야 해?
- threshold_snapshot에 manual_request_count, distinct_days, signal families, mirror breach, confidence cap ratio를 남기는 이유는?
- review packet에 promotion_threshold_summary와 promotion_evidence_refs를 최소 projection으로 보여야 forum이 무엇을 재현할 수 있어?
- fast_track entry에서 triggered_conditions와 reason_codes가 비어 있으면 어떤 문제가 생겨?
contextual_chunk_prefix: |
  이 문서는 shadow candidate 승격 판정을 replay 가능한 provenance로 남기기 위해 catalog entry의 promotion_snapshot과 review packet projection 필드를 정의하는 advanced primer이다.
---
# Shadow Promotion Snapshot Schema Fields

> 한 줄 요약: shadow candidate가 어떤 tier와 confidence로 catalog에 들어왔는지 나중에 다시 추측하지 않으려면, catalog entry에는 replay 가능한 `promotion_snapshot` block을, review packet에는 그 block의 최소 projection을 같은 의미로 남겨야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Candidate Promotion Thresholds](./shadow-candidate-promotion-thresholds.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Review Packet Template](./shadow-review-packet-template.md)
> - [Shadow Packet Automation Mapping](./shadow-packet-automation-mapping.md)
> - [Shadow Process Detection Signals](./shadow-process-detection-signals.md)
> - [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)
> - [Mirror Lag SLA Calibration](./mirror-lag-sla-calibration.md)

> retrieval-anchor-keywords:
> - shadow promotion snapshot schema fields
> - promotion snapshot minimum fields
> - promotion_snapshot block
> - catalog entry promotion tier confidence
> - review packet promotion snapshot
> - promotion threshold snapshot evidence
> - promotion rule ref
> - shadow candidate promotion provenance
> - threshold summary packet field
> - tier confidence evidence refs
> - fast track promotion evidence
> - shadow intake projection

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Shadow Promotion Snapshot Schema Fields](./README.md#shadow-promotion-snapshot-schema-fields)
> - 다음 단계: [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)

## 핵심 개념

[Shadow Candidate Promotion Thresholds](./shadow-candidate-promotion-thresholds.md)가 승격 규칙을 정의해도, 실제 catalog entry와 review packet에 그 판단 흔적이 안 남으면 forum은 다음 질문을 다시 감으로 풀게 된다.

- 왜 이 항목이 `watchlist`가 아니라 `promote`였는가
- 왜 confidence가 `high`가 아니라 `medium`이었는가
- 어떤 threshold 숫자와 evidence가 그 판단을 만들었는가

그래서 promotion 정보는 prose 메모가 아니라 `promotion_snapshot`이라는 별도 schema block으로 남기는 편이 좋다.
이 block의 목적은 "승격되었다"를 적는 것이 아니라, **승격 판정을 replay 가능한 provenance로 보존하는 것**이다.

---

## 깊이 들어가기

### 1. `promotion_snapshot`은 target decision이 아니라 intake provenance다

`target_state.decision`은 앞으로 이 shadow process를 `retire`, `absorb`, `officialize`, `temporary_hold` 중 어디로 보낼지에 대한 결정이다.
반면 `promotion_snapshot`은 이 항목이 왜 catalog intake 대상이 되었는지를 설명한다.

둘을 섞으면 이런 문제가 생긴다.

- `promote/high`와 `absorb`가 같은 종류의 decision처럼 보인다
- threshold evidence가 `signal_evidence[]`와 review note에 흩어져 replay가 어려워진다
- packet generator가 승격 이유를 다시 추론해야 한다

따라서 승격 provenance는 `signal_evidence[]`의 자유 서술이나 `review.decision_question`에 끼워 넣지 말고, **별도 `promotion_snapshot` block**으로 고정하는 편이 안전하다.

### 2. catalog entry 최소 필드는 tier와 confidence를 재현 가능하게 해야 한다

catalog entry에서 promotion snapshot 최소 필드는 다음 정도가 적절하다.

| field group | 최소 필드 | 왜 필요한가 |
|---|---|---|
| 판정 결과 | `promotion_snapshot.tier`, `promotion_snapshot.confidence`, `promotion_snapshot.evaluated_at` | 어떤 시점에 어떤 분류가 내려졌는지 고정한다 |
| provenance | `promotion_snapshot.shadow_candidate_key`, `promotion_snapshot.rule_ref`, `promotion_snapshot.window` | 어떤 bundle과 어떤 threshold rule로 평가했는지 replay한다 |
| threshold snapshot | `promotion_snapshot.threshold_snapshot.manual_request_count`, `distinct_days`, `distinct_signal_families`, `mirror_breach_ratio`, `authoritative_off_plane_state`, `incident_linked` | tier 판정에 쓰인 핵심 recurrence/risk signal을 남긴다 |
| confidence cap snapshot | `promotion_snapshot.threshold_snapshot.synthetic_request_key_ratio`, `unresolved_source_ref_ratio` | confidence가 왜 capped됐는지 나중에 설명하게 한다 |
| trigger / evidence | `promotion_snapshot.triggered_conditions[]`, `promotion_snapshot.reason_codes[]`, `promotion_snapshot.evidence_refs[]` | 숫자만으로 설명되지 않는 fast-track gate와 human-readable 근거를 연결한다 |

여기서 중요한 점은 raw telemetry 전체를 복사하는 것이 아니다.
최소 필드는 **tier와 confidence를 만든 threshold-driving fact만** 남기면 된다.

특히 `fast_track`이나 workflow override가 들어간 경우에는 `triggered_conditions[]`가 꼭 필요하다.
예를 들어 `single_person_dependency_on_tier0_path`, `incident_linked`, `authoritative_off_plane_state` 같은 조건은 숫자 몇 개만으로는 복원되지 않기 때문이다.

### 3. review packet 최소 필드는 forum이 "왜 지금 이 안건인가"를 다시 읽게 해야 한다

review packet은 catalog entry 전체를 복사하지 않아도 되지만, promotion provenance를 너무 줄이면 intake decision이 다시 흔들린다.

권장 최소 packet field는 다음과 같다.

| packet field | source | 왜 필요한가 |
|---|---|---|
| `promotion_tier` | `promotion_snapshot.tier` | 이 row가 `observe/watchlist/promote/fast_track` 중 어디서 올라왔는지 즉시 보여 준다 |
| `promotion_confidence` | `promotion_snapshot.confidence` | 증거 강도와 data-quality cap 유무를 빠르게 읽게 한다 |
| `promotion_window` | `promotion_snapshot.window` | 어떤 기간의 recurrence를 기준으로 봤는지 고정한다 |
| `promotion_rule_ref` | `promotion_snapshot.rule_ref` | default threshold인지 workflow override인지 forum이 알게 한다 |
| `promotion_threshold_summary` | summarize `promotion_snapshot.threshold_snapshot` + `triggered_conditions[]` | 승격 근거를 숫자와 gate 중심으로 한 줄에 압축한다 |
| `promotion_reason_summary` | summarize `promotion_snapshot.reason_codes[]` | 사람이 읽을 때 왜 승격됐는지 빠르게 이해하게 한다 |
| `promotion_evidence_refs` | `promotion_snapshot.evidence_refs[]` | packet에서 바로 drill-down할 anchor를 남긴다 |

이 필드들은 특히 `intake-and-retriage`, `decision-needed` section에서 minimum contract로 보는 편이 좋다.
`execution-risk`, `verification-and-closeout` section에서는 full summary를 축약할 수 있지만, source entry에 남아 있는 `promotion_snapshot`을 임의로 지우거나 새로 해석해선 안 된다.

### 4. packet summary는 짧아야 하지만 cap과 hard gate는 숨기면 안 된다

`promotion_threshold_summary`는 장문 prose보다 아래처럼 deterministic한 형식이 낫다.

```text
req=4 / days=3 / signals=2 / mirror=0.75 / off_plane_authoritative=false / caps=none
```

confidence가 capped된 경우에는 그 사실을 summary에 바로 보여 주는 편이 좋다.

```text
req=5 / days=4 / signals=2 / mirror=0.40 / caps=synthetic_request_key_ratio>0.3
```

마찬가지로 `fast_track`이면 hard gate를 summary나 `promotion_reason_summary`에서 숨기지 않는 편이 좋다.

```text
tier=fast_track / gates=incident_linked,single_person_dependency_on_tier0_path
```

즉 packet은 짧아질 수는 있어도, **tier를 만든 decisive fact를 삭제해서는 안 된다**.

### 5. 최소 validation rule을 같이 두어야 packet이 거짓으로 풍부해지지 않는다

다음 정도는 schema/packet quality gate로 함께 두는 편이 좋다.

- `promotion_snapshot.tier`가 있으면 `shadow_candidate_key`, `rule_ref`, `window`도 같이 있어야 한다
- `promotion_snapshot.confidence`가 `medium` 이상이면 confidence cap 관련 field도 빠지지 않아야 한다
- `intake-and-retriage` 또는 `decision-needed` packet row에서 `promotion_tier`가 있으면 `promotion_threshold_summary`와 최소 1개 `promotion_evidence_refs`가 같이 있어야 한다
- packet은 `promotion_reason_summary`를 생성할 수 없더라도 `promotion_threshold_summary`를 prose로 대신 추측하지 말고 `projection_status: degraded`로 내려야 한다

이 검증 규칙이 있어야 `promote/high` 같은 label이 evidence 없는 badge로 변질되지 않는다.

---

## 코드로 보기

```yaml
shadow_catalog_entry:
  catalog_id: shadow-release-approval-001
  title: manual_release_override_via_slack_dm
  promotion_snapshot:
    tier: promote
    confidence: medium
    evaluated_at: 2026-04-14T09:30:00+09:00
    shadow_candidate_key: rollout_override|freeze_window|growth-platform|dm_approval
    rule_ref: shadow-candidate-promotion-thresholds/default-v1
    window:
      label: last_30_days
      start_at: 2026-03-15
      end_at: 2026-04-13
    threshold_snapshot:
      manual_request_count: 4
      distinct_days: 3
      distinct_signal_families: 2
      mirror_breach_ratio: 0.75
      authoritative_off_plane_state: false
      incident_linked: false
      synthetic_request_key_ratio: 0.0
      unresolved_source_ref_ratio: 0.0
    triggered_conditions:
      - distinct_signal_families_gte_2
      - mirror_breach_ratio_gte_0_5
    reason_codes:
      - repeated_across_multiple_days
      - multi_signal_evidence
    evidence_refs:
      - override-scorecard-2026-q2
      - INC-482-review
```

```yaml
shadow_review_packet:
  packet_template_version: shadow-review-minimum-v1
  catalog_id: shadow-release-approval-001
  lifecycle_state: decision_pending
  promotion_tier: promote
  promotion_confidence: medium
  promotion_window: last_30_days (2026-03-15..2026-04-13)
  promotion_rule_ref: shadow-candidate-promotion-thresholds/default-v1
  promotion_threshold_summary: req=4 / days=3 / signals=2 / mirror=0.75 / caps=none
  promotion_reason_summary:
    - repeated_across_multiple_days
    - multi_signal_evidence
  promotion_evidence_refs:
    - override-scorecard-2026-q2
    - INC-482-review
  decision_question: absorb 경로로 승인하고 control plane 필드 추가를 backlog로 받을 것인가
  next_review_at: 2026-04-21
```

이렇게 두면 catalog entry는 replay 가능한 provenance를 보존하고, review packet은 forum이 읽을 최소 근거만 안정적으로 노출한다.

---

## 꼬리질문

- `promotion_tier`와 `promotion_confidence`만 있고 어떤 threshold rule을 썼는지는 빠져 있지 않은가?
- confidence cap을 만든 `synthetic_request_key_ratio`, `unresolved_source_ref_ratio`가 누락돼 있지 않은가?
- `fast_track` entry인데 어떤 hard gate가 발동했는지 `triggered_conditions[]`가 비어 있지 않은가?
- packet row에 threshold summary 없이 badge만 남아 forum이 승격 이유를 다시 추측하고 있지 않은가?
- evidence ref가 없어 packet에서 원문 scorecard/incident를 다시 찾기 어려워지지 않는가?

## 한 줄 정리

Shadow promotion snapshot schema fields는 shadow candidate 승격을 `tier/confidence` label로만 남기지 않고, catalog entry의 `promotion_snapshot`과 review packet의 최소 projection으로 threshold snapshot evidence를 재현 가능하게 고정하는 문서다.
