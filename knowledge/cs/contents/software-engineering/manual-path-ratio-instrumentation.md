# Manual Path Ratio Instrumentation

> 한 줄 요약: `manual_path_ratio`와 `shadow_candidate_count`를 계산하려면 DM 승인, spreadsheet 상태 저장, off-plane 문서/스크립트 사용을 request 단위 fact로 정규화하고 mirror SLA와 dedupe 규칙을 같이 고정해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)
> - [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)
> - [Mirror Lag SLA Calibration](./mirror-lag-sla-calibration.md)
> - [Shadow Process Detection Signals](./shadow-process-detection-signals.md)
> - [Shadow Candidate Promotion Thresholds](./shadow-candidate-promotion-thresholds.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)
> - [Rollout Approval Workflow](./rollout-approval-workflow.md)
> - [Consumer Exception Registry Quality and Automation](./consumer-exception-registry-quality-automation.md)

> retrieval-anchor-keywords:
> - manual path ratio instrumentation
> - manual_path_ratio formula
> - shadow_candidate_count computation
> - dm approval measurement
> - spreadsheet usage telemetry
> - off plane workflow signal
> - shadow process observability
> - override instrumentation
> - manual approval detection
> - off plane artifact evidence
> - request level normalization
> - mirror SLA metric
> - mirror lag calibration
> - break glass denominator exclusion

## 핵심 개념

`manual_path_ratio`가 자주 흐려지는 이유는 DM message 수, spreadsheet 파일 수, 노션 링크 수를 그대로 세기 때문이다.
이 지표는 message metric이 아니라 **request / override case metric**이어야 한다.

최소한 세 층을 분리해야 한다.

- raw event: DM, sheet edit, off-plane 링크 같은 원시 흔적
- request fact: 한 request가 실제로 manual path를 탔는지 정규화한 결과
- candidate bundle: 같은 workaround가 반복된 묶음

즉 계측의 목적은 "증거를 많이 모으기"가 아니라, **같은 우회가 몇 건의 실제 운영 흐름을 먹고 있는지 계산 가능하게 만드는 것**이다.

---

## 신호 수집 표

| signal family | raw source | manual path로 count하는 조건 | 집계 key | 흔한 false positive |
|---|---|---|---|---|
| `dm_approval` | Slack/Teams DM, private group DM | 승인/예외 결정이 DM 안에서 끝나고, 공식 control plane state transition이 없거나 mirror SLA를 넘겨 반영됨 | `request_id + stage` | 단순 문의, official UI deep link 공유, bot notification |
| `spreadsheet_state` | Google Sheets, Excel Online, Airtable grid | 시트 row/cell이 allowlist, approval, exception state의 authoritative source로 동작함 | `request_id + sheet_row_key` | export sheet, dashboard sheet, read-only report |
| `off_plane_artifact` | Notion, Confluence draft, email thread, local file, ad-hoc script | 운영자가 그 artifact를 봐야만 request를 진행할 수 있고, 핵심 state나 판단 근거가 공식 plane 밖에 남음 | `request_id + artifact_ref + stage` | 공식 runbook 참고 링크, read-only design doc, incident recap |

raw source는 많아도 괜찮지만, scorecard는 최종적으로 `request_id` 기준으로 dedupe되어야 한다.

---

## 깊이 들어가기

### 1. 집계 단위는 message가 아니라 request여야 한다

하나의 release override가 다음 흔적을 동시에 남길 수 있다.

- DM 승인 1건
- spreadsheet row 수정 2회
- 노션 checklist 링크 1회

이걸 그대로 세면 수동 경로 4건처럼 보이지만, 실제로는 request 1건이다.
그래서 계측은 message/event count가 아니라 `distinct request_id` 기준으로 닫아야 한다.

권장 key:

- `request_id`: override id, rollout id, support ticket id 같은 공식 식별자
- `workflow_family`: rollout_override, deprecation_waiver, migration_exception
- `stage`: request, approval, execution, closure

공식 식별자가 없더라도 `"workflow_family + actor + day + target"` 같은 synthetic key를 만들되, synthetic 비율이 높으면 data quality 경고를 띄우는 편이 좋다.

### 2. DM approval은 "대화"가 아니라 off-plane state transition을 잡아야 한다

DM을 count하려면 승인 텍스트가 있다는 사실만으로는 부족하다.
다음 세 조건을 같이 만족해야 signal이 강해진다.

- request reference가 식별된다
- approver identity와 decision timestamp가 보인다
- 같은 결정이 공식 registry나 approval plane에 제때 기록되지 않았다

최소 수집 필드:

- `message_ref`
- `channel_kind` (`dm`, `private_group_dm`)
- `approver`
- `decision` (`approved`, `rejected`, `override_granted`)
- `approved_at`
- `mirrored_to_control_plane`
- `mirror_lag_minutes`

다음은 기본적으로 제외하는 편이 맞다.

- "이건 포털에서 올려 주세요"처럼 공식 경로로 redirect한 DM
- bot이 post한 상태 알림
- 공식 승인 이후 남긴 축약된 확인 메시지

즉 DM approval metric은 chat volume이 아니라 **DM 안에서 끝난 승인 state transition**을 세야 한다.

### 3. spreadsheet usage는 sheet가 authoritative인지 먼저 따져야 한다

spreadsheet는 단순 report일 수도 있고, 실제 운영 control plane일 수도 있다.
둘을 구분하지 않으면 ratio가 금방 오염된다.

count 기준:

- sheet row/cell이 allowlist, rollout window, exception owner, approval state를 결정한다
- 운영자가 sheet를 수정해야 다음 단계로 진행된다
- 공식 registry가 있더라도 반영이 늦어 sheet가 실질 source of truth가 된다

제외 기준:

- 공식 registry export본
- read-only dashboard
- 분기 review용 aggregation sheet
- 이미 registry 기록 후 만들어진 단순 공유용 리스트

추적 필드:

- `sheet_id`
- `worksheet`
- `row_key`
- `edited_by`
- `edited_at`
- `field_role` (`approval_state`, `allowlist`, `exception_log`, `checklist`)
- `mirrored_to_control_plane`
- `mirror_lag_minutes`

핵심은 "sheet를 썼는가"가 아니라 **sheet가 없으면 workflow가 멈추는가**다.

### 4. off-plane workflow signal은 DM과 시트 밖도 포함해야 한다

shadow process는 종종 문서/스크립트/메일로 흩어진다.
그래서 `off_plane_artifact`는 넓게 받되, 역할을 좁게 정의해야 한다.

강한 signal 예:

- 노션 페이지에만 freeze-window override 대상이 적혀 있음
- 로컬 YAML 파일이 rollout allowlist source로 쓰임
- 이메일 thread에서만 exception approval이 이어짐
- ad-hoc script output을 사람 손으로 붙여 넣어 다음 단계 판단을 함

약한 signal 예:

- 공식 runbook 링크를 참고만 함
- architecture doc가 배경 설명만 제공함
- postmortem 링크가 회고에만 쓰임

권장 필드:

- `artifact_type` (`notion`, `confluence`, `email`, `local_file`, `script_output`)
- `artifact_ref`
- `artifact_role` (`approval_input`, `state_store`, `execution_checklist`, `override_log`)
- `required_for_progress`
- `owner_scope`

### 5. raw event를 request fact로 정규화해야 metric이 계산된다

원시 signal은 여러 개여도 scorecard는 request 단위 fact가 필요하다.

```yaml
manual_path_event:
  event_id: evt-2026-04-14-0192
  request_id: rel-4821
  workflow_family: rollout_override
  policy_key: freeze_window
  service: checkout-api
  team: growth-platform
  stage: approval
  source_family: dm_approval
  source_ref: slack://workspace/D123/p1713083012
  evidence_strength: strong
  mirrored_to_control_plane: false
  mirror_lag_minutes:
  observed_at: 2026-04-14T09:11:00+09:00
```

```yaml
manual_path_request_fact:
  request_id: rel-4821
  workflow_family: rollout_override
  policy_key: freeze_window
  eligible_for_official_path: true
  manual_path_used: true
  signal_families:
    - dm_approval
    - spreadsheet_state
  primary_manual_path: dm_approval
  owner_scope: growth-platform
  artifact_refs:
    - slack://workspace/D123/p1713083012
    - gsheets://release-override-tracker/row/418
  mirror_breach: true
  shadow_candidate_key: rollout_override|freeze_window|growth-platform|dm_approval
```

여기서 중요한 점:

- 같은 request의 여러 raw event는 `manual_path_used=true` 한 건으로 합친다
- `signal_families`는 evidence richness를 남기기 위한 필드다
- scorecard는 raw event가 아니라 `manual_path_request_fact`를 본다

### 6. `manual_path_ratio`는 numerator보다 denominator 정의가 더 중요하다

권장 분모는 "공식 경로를 탔어야 하는 eligible request 수"다.
단순히 전체 DM 수나 전체 override 수를 분모로 두면 해석이 흔들린다.

기본 식:

```text
manual_path_ratio
  = count(distinct request_id where eligible_for_official_path = true and manual_path_used = true)
    / count(distinct request_id where eligible_for_official_path = true)
```

권장 세그먼트:

- workflow family별
- policy key별
- team/service별
- stage별 (`approval`, `execution`)

분모에서 별도 분리할 항목:

- training / drill traffic
- backfill / historical import
- governance가 명시적으로 허용한 break-glass emergency path

중요한 점은 이들을 조용히 빼는 것이 아니라, `exception_mode`로 분리해 ratio 해석에 같이 남기는 것이다.
break-glass를 scorecard에서 어떻게 계속 보이게 할지는 [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)처럼 별도 panel 설계를 같이 가져가는 편이 안정적이다.

### 7. `shadow_candidate_count`는 반복 묶음 계산이 있어야 나온다

`manual_path_ratio`는 request 비율이고, `shadow_candidate_count`는 반복 workaround 묶음 수다.
둘은 다른 수준의 metric이다.

먼저 candidate grouping key를 고정한다.

- `workflow_family`
- `policy_key`
- `owner_scope`
- `primary_manual_path`

여기에 필요하면 같은 sheet/doc/approver를 구분하는 `artifact_cluster`를 붙인다.

그다음 각 key에 대해 최소 다음 값을 계산한다.

- `manual_request_count`
- `distinct_days`
- `distinct_signal_families`
- `mirror_breach_count`

기본 판정 예시는 다음처럼 둘 수 있다.

```text
candidate qualifies if:
  manual_request_count >= 3
  and distinct_days >= 2
  and (
    distinct_signal_families >= 2
    or mirror_breach_count / manual_request_count >= 0.5
  )
```

그러면:

```text
shadow_candidate_count
  = count(distinct shadow_candidate_key where qualifies = true)
```

임계값은 조직마다 달라도 괜찮지만, 문서가 아니라 config로 고정돼 있어야 분기별 scorecard가 재현 가능하다.
기본 tier와 confidence cap을 어떤 규칙으로 `observe / watchlist / promote / fast_track`에 매핑할지는 [Shadow Candidate Promotion Thresholds](./shadow-candidate-promotion-thresholds.md)처럼 catalog intake 계약으로 따로 고정해 두는 편이 안정적이다.

### 8. mirror SLA와 dedupe 규칙을 안 정하면 지표가 쉽게 부풀려진다

다음 규칙은 거의 필수다.

- 같은 request/stage/source의 중복 메시지는 1건으로 dedupe
- DM approval은 `mirror_lag_minutes > workflow_sla_minutes`일 때만 manual breach로 승격
- sheet edit는 row가 authoritative일 때만 count
- off-plane doc는 `required_for_progress = true`일 때만 강한 signal로 count
- official system과 off-plane artifact가 모두 있으면, 어떤 쪽이 source of truth인지 필드로 남김

workflow별 `workflow_sla_minutes`를 어떤 band로 고를지와 `soft / hard / structural` breach class를 어떻게 공통화할지는 [Mirror Lag SLA Calibration](./mirror-lag-sla-calibration.md)처럼 별도 calibration 문서로 고정해 두는 편이 안정적이다.

추천 품질 지표:

- `synthetic_request_key_ratio`
- `unresolved_source_ref_ratio`
- `mirror_lag_missing_ratio`
- `manual_signal_reclassified_ratio`

지표 품질이 낮으면 shadow process metric도 곧바로 신뢰를 잃는다.

### 9. scorecard와 catalog가 같은 fact table을 봐야 한다

좋은 운영 모델은 scorecard와 shadow catalog가 서로 다른 숫자를 보지 않는다.

- `manual_path_ratio`는 override scorecard에 들어간다
- `shadow_candidate_count`는 catalog intake backlog를 만든다
- catalog entry의 `verification_metric`은 같은 fact table에서 읽는다

예:

```yaml
shadow_metric_config:
  workflow_family: rollout_override
  workflow_sla_minutes: 30
  candidate_min_repeats: 3
  candidate_min_distinct_days: 2
  candidate_min_confidence: medium
```

```yaml
shadow_scorecard:
  window: last_30_days
  eligible_requests: 28
  manual_path_requests: 9
  manual_path_ratio: 0.32
  shadow_candidate_count: 2
```

이 연결이 있어야 [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)의 `exit_condition: manual_path_ratio_zero_for_30d` 같은 문장이 실제로 검증 가능해진다.

---

## 실전 시나리오

### 시나리오 1: release manager가 DM으로 승인하고 registry는 비어 있다

이 경우 `dm_approval` raw event가 `manual_path_used=true` request fact로 승격된다.
같은 manager와 같은 policy key에서 반복되면 shadow candidate grouping에 들어간다.

### 시나리오 2: spreadsheet는 있지만 nightly export라 운영 결정에는 안 쓰인다

이 경우 `spreadsheet_state` raw event는 남길 수 있어도 manual numerator에는 넣지 않는 편이 맞다.
reporting artifact와 control artifact를 구분해야 한다.

### 시나리오 3: 노션 checklist를 보지 않으면 rollout을 진행할 수 없다

공식 plane 밖 checklist가 사실상 gate 역할을 하므로 `off_plane_artifact`로 count해야 한다.
특히 같은 checklist가 여러 request에서 반복되면 shadow candidate 가능성이 높다.

### 시나리오 4: DM에서 임시 승인 후 5분 안에 공식 registry로 mirror된다

이건 조직이 정한 `workflow_sla_minutes` 안이면 manual breach가 아닐 수 있다.
핵심은 DM 자체가 아니라 **공식 plane 밖에서 state가 얼마나 오래 살아 있었는가**다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| raw signal count | 수집이 쉽다 | `manual_path_ratio`가 크게 왜곡된다 | 아주 초기 탐색 |
| request-level normalization | ratio 계산이 안정적이다 | request key 설계가 필요하다 | 기본 운영 모델 |
| request fact + candidate grouping | scorecard와 shadow catalog가 연결된다 | SLA, dedupe, confidence rule을 같이 운영해야 한다 | 성숙한 governance 조직 |

manual path instrumentation의 목적은 DM이나 sheet를 금지하는 것이 아니라, **공식 plane 밖에서 실제로 결정과 상태가 얼마나 흘러가는지 재현 가능하게 측정하는 것**이다.

---

## 꼬리질문

- raw signal이 아니라 `request_id` 기준 fact table이 있는가?
- DM approval을 chat activity가 아니라 off-plane state transition으로 측정하고 있는가?
- spreadsheet가 report인지 source of truth인지 구분하는 필드가 있는가?
- `shadow_candidate_count`의 grouping key와 threshold가 config로 고정돼 있는가?
- catalog retirement 검증이 scorecard와 같은 numerator / denominator를 보고 있는가?

## 한 줄 정리

Manual Path Ratio Instrumentation은 DM 승인, spreadsheet 상태 저장, off-plane artifact 사용을 request 단위로 정규화해 `manual_path_ratio`와 `shadow_candidate_count`를 같은 evidence base에서 재현 가능하게 만드는 계측 계약이다.
