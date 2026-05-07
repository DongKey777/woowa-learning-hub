---
schema_version: 3
title: Shadow Lifecycle Scorecard Metrics
concept_id: software-engineering/shadow-lifecycle-scorecard-metrics
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
- scorecard
- lifecycle-metrics
- dashboard
aliases:
- shadow lifecycle scorecard metrics
- shadow lifecycle dashboard
- lifecycle_state aging dashboard
- blocked duration dashboard
- hold expiry dashboard
- shadow 생명주기 스코어카드
symptoms:
- shadow catalog 건강도를 total entry count만 보고 decision_pending 정체, blocked orphan, overdue hold, proof gap을 구분하지 못해
- lifecycle_state_age_days는 보지만 temporary_hold의 expires_at, blocked의 escalation SLA, verification_pending의 metric freshness를 별도 clock으로 보지 않아
- verification_pending을 단일 점수로 합쳐 manual_path_ratio fail이나 audit log gap 같은 hard gate를 다른 개선 지표로 덮어
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/shadow-catalog-lifecycle-states
- software-engineering/shadow-catalog-review-cadence-profiles
next_docs:
- software-engineering/shadow-candidate-promotion-thresholds
- software-engineering/shadow-retirement-proof-metrics
- software-engineering/shadow-retirement-scorecard-schema
linked_paths:
- contents/software-engineering/shadow-process-catalog-and-retirement.md
- contents/software-engineering/shadow-process-catalog-entry-schema.md
- contents/software-engineering/shadow-catalog-lifecycle-states.md
- contents/software-engineering/shadow-catalog-review-cadence-profiles.md
- contents/software-engineering/shadow-temporary-hold-exit-criteria.md
- contents/software-engineering/manual-path-ratio-instrumentation.md
- contents/software-engineering/mirror-lag-sla-calibration.md
- contents/software-engineering/shadow-retirement-proof-metrics.md
- contents/software-engineering/shadow-retirement-scorecard-schema.md
- contents/software-engineering/override-burndown-review-cadence-scorecards.md
confusable_with:
- software-engineering/shadow-catalog-review-cadence-profiles
- software-engineering/shadow-retirement-proof-metrics
- software-engineering/shadow-retirement-scorecard-schema
forbidden_neighbors: []
expected_queries:
- shadow lifecycle scorecard는 total count보다 lifecycle aging, blocked duration, hold expiry, retirement verification health를 왜 나눠 봐야 해?
- lifecycle_state_age_days와 state_clock_breach를 함께 두면 state별 queue discipline 붕괴를 어떻게 볼 수 있어?
- blocked panel에서 blocker_owner, blocked_from_state, blocker_class를 보여야 orphan backlog를 찾을 수 있는 이유는?
- temporary_hold dashboard는 age보다 expires_at risk bucket과 extension_count를 왜 중심에 둬야 해?
- verification_pending health를 hard gate matrix로 보지 않고 단일 점수로 합치면 어떤 closure 오류가 생겨?
contextual_chunk_prefix: |
  이 문서는 shadow catalog scorecard를 lifecycle aging, blocked duration, hold expiry, retirement verification health 패널로 나눠 backlog 정체와 가짜 retirement를 드러내는 advanced metrics playbook이다.
---
# Shadow Lifecycle Scorecard Metrics

> 한 줄 요약: shadow catalog scorecard는 총량보다 `lifecycle_state`별 aging, `blocked_duration`, `hold_time_to_expiry`, `retirement_verification_health`를 분리해 보여 줘야 backlog 정체, parking-lot hold, blocker orphan, 가짜 retirement를 동시에 드러낼 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)
> - [Shadow Catalog Review Cadence Profiles](./shadow-catalog-review-cadence-profiles.md)
> - [Temporary Hold Exit Criteria](./shadow-temporary-hold-exit-criteria.md)
> - [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)
> - [Mirror Lag SLA Calibration](./mirror-lag-sla-calibration.md)
> - [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)
> - [Shadow Retirement Scorecard Schema](./shadow-retirement-scorecard-schema.md)
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)

> retrieval-anchor-keywords:
> - shadow lifecycle scorecard metrics
> - shadow lifecycle dashboard
> - lifecycle_state aging dashboard
> - blocked duration dashboard
> - hold expiry dashboard
> - retirement verification health
> - shadow backlog aging
> - blocked shadow age bucket
> - hold overdue risk
> - expires_at risk bucket
> - verification pending health panel
> - shadow dashboard slice
> - shadow review forum heatmap
> - shadow state sla breach
> - overdue hold count
> - blocker duration by owner
> - proof freshness dashboard
> - retirement gate matrix
> - shadow process portfolio heatmap
> - shadow retirement scorecard schema

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Shadow Lifecycle Scorecard Metrics](./README.md#shadow-lifecycle-scorecard-metrics)
> - 다음 단계: [Shadow Candidate Promotion Thresholds](./shadow-candidate-promotion-thresholds.md)

## 핵심 개념

shadow catalog의 건강도는 총 entry 수 한 줄로 읽으면 거의 항상 오판한다.
같은 20건이라도 실제 문제는 완전히 다를 수 있다.

- `decision_pending`이 오래 쌓인 것일 수 있다
- `blocked`가 owner 없이 방치된 것일 수 있다
- `temporary_hold`가 만료됐는데도 parking lot처럼 남은 것일 수 있다
- `verification_pending`이 proof 부족인데도 곧 `retired`처럼 보고되는 것일 수 있다

그래서 shadow lifecycle scorecard는 최소 네 질문을 따로 보여 줘야 한다.

- 지금 어느 `lifecycle_state`가 오래 정체돼 있는가
- `blocked`는 어디서 얼마나 오래 막혔고 누가 못 풀고 있는가
- `temporary_hold`는 언제 만료되고 몇 번 연장됐는가
- `verification_pending`은 정말 retirement proof에 가까운가, 아니면 증빙 결손인가

즉 좋은 scorecard는 단순 inventory가 아니라 **state backlog, control-state risk, proof health를 함께 보이는 운영 패널**이다.

---

## 깊이 들어가기

### 1. scorecard는 stock, control risk, proof health를 분리해야 한다

권장 panel family는 다음 네 가지다.

| panel family | 핵심 질문 | 이 panel이 없으면 숨는 실패 |
|---|---|---|
| lifecycle aging | 어느 상태 backlog가 멈춰 있는가 | flat total count 뒤의 state별 정체 |
| blocked duration | blocker가 어디서 얼마나 오래 풀리지 않는가 | 구조 문제를 단순 age로 오해 |
| hold expiry | bounded pause가 parking lot로 변했는가 | overdue hold와 repeated extension 은폐 |
| retirement verification health | `verification_pending`이 proof를 쌓는 중인가, 증거가 비어 있는가 | `closed`와 `retired` 혼동 |

이 네 패널은 서로 대체 관계가 아니다.
예를 들어 lifecycle aging만 보면 `temporary_hold`가 오래됐다는 사실은 보여도, 그 hold가 내일 만료되는지 이미 5일 overdue인지 알 수 없다.
반대로 verification health만 보면 proof gap은 보여도, 왜 entry가 계속 `verification_pending`에 밀려 있는지 state-level backlog를 읽기 어렵다.

### 2. 공통 metric은 state age와 state-specific clock 둘 다 가져야 한다

scorecard의 공통 기반 metric은 다음 두 축이다.

```text
lifecycle_state_age_days
  = now - lifecycle_state_entered_at
```

```text
state_clock_breach
  = true if current state exceeded its governing clock
```

여기서 중요한 점은 모든 상태를 같은 age rule로 재지 않는 것이다.

- `decision_pending`: review cadence clock 기준으로 본다
- `blocked`: `blocked_since`와 escalation SLA 기준으로 본다
- `temporary_hold`: age보다 `expires_at` 기준이 우선이다
- `verification_pending`: verification window와 metric freshness 기준으로 본다

즉 `lifecycle_state_age_days`는 공통 비교용이고, 실제 위험 노출은 `state_clock_breach`가 담당한다.
이 기준선은 [Shadow Catalog Review Cadence Profiles](./shadow-catalog-review-cadence-profiles.md)의 상태별 cadence와 연결돼야 한다.

### 3. lifecycle aging 패널은 state별 정체를 먼저 드러내야 한다

권장 핵심 metric:

| metric | 의미 | 기본 해석 |
|---|---|---|
| `entries_by_lifecycle_state` | 상태별 열린 entry 수 | backlog가 어디에 쌓이는지 본다 |
| `lifecycle_state_age_p50` / `p95` | 상태 진입 후 경과 시간 중앙값 / 상위 95% | 극단적 장기 정체를 본다 |
| `state_clock_breach_count` | 상태별 SLA breach 수 | 단순 오래됨이 아니라 운영 위반을 본다 |
| `age_bucket_distribution` | `0-7d / 8-30d / 31-60d / 60d+` 또는 상태별 bucket | 포트폴리오 분포를 본다 |
| `reopen_or_bounce_rate_30d` | 같은 entry가 상태를 되돌아간 비율 | false progress를 본다 |

권장 slice:

- `lifecycle_state`
- `decision`
- `review_forum`
- `domain` 또는 `process_family`
- `criticality_tier`

추천 시각화:

- stacked bar: 상태별 age bucket
- heatmap: `review_forum x lifecycle_state`별 breach count
- small multiple: `decision`별 `p95 state age`

핵심은 "오래된 shadow entry가 몇 개인가"가 아니라, **어느 상태의 queue discipline이 무너졌는가**를 보이게 하는 것이다.

### 4. blocked 패널은 generic age가 아니라 unblock 책임을 보여 줘야 한다

`blocked`는 늦어진 일이 아니라 구조적으로 막힌 일이다.
그래서 block panel은 duration과 ownership을 같이 드러내야 한다.

권장 핵심 metric:

```text
blocked_duration_days
  = now - blocked_since
```

| metric | 의미 | 기본 해석 |
|---|---|---|
| `blocked_count` | 현재 `blocked` 상태 entry 수 | 구조적 정체의 총량 |
| `blocked_duration_p50` / `p95` | blocked 지속 시간 | unblock 속도와 tail risk |
| `blocked_over_escalation_sla_count` | SLA를 넘긴 blocked 수 | 상위 forum 개입이 필요한 수 |
| `ownerless_blocked_count` | `blocker_owner` 또는 ETA가 비어 있는 blocked 수 | orphan backlog 탐지 |
| `blocked_from_state_distribution` | 어떤 진행 상태에서 막혔는가 | retire/absorb/officialize 중 어디서 자주 멈추는지 |
| `blocker_class_distribution` | owner gap, control plane gap, dependency wait, policy approval 등 | 구조 원인 분류 |
| `blocked_clear_rate_30d` | 지난 30일간 unblock된 비율 | queue 회복력 |

권장 slice:

- `blocked_from_state`
- `blocker_class`
- `blocker_owner`
- `escalation_forum`
- `review_forum`

추천 시각화:

- heatmap: `blocked_from_state x blocker_class`
- ranking table: longest blocked entries by `blocker_owner`
- trend line: `blocked_count` vs `blocked_clear_rate_30d`

이 패널의 목적은 `blocked`를 늙은 backlog로 취급하지 않고, **어느 구조 결손이 계속 unblock을 막는지 바로 보이게 하는 것**이다.

### 5. hold expiry 패널은 age보다 expiry risk와 extension drift를 보여 줘야 한다

`temporary_hold`는 오래된 것보다 overdue인지가 더 중요하다.
그래서 hold panel은 `expires_at` 중심으로 설계하는 편이 맞다.

권장 핵심 metric:

```text
hold_days_to_expiry
  = expires_at - now
```

| metric | 의미 | 기본 해석 |
|---|---|---|
| `holds_expired_open_count` | 만료됐지만 여전히 `temporary_hold`인 수 | parking lot hold 직접 탐지 |
| `holds_expiring_in_2bd_count` | 2영업일 내 만료 예정 hold 수 | 즉시 review 필요 |
| `hold_days_to_expiry_p50` | 남은 hold 여유 기간 중앙값 | 전체 포트폴리오의 만료 압박 |
| `hold_extension_count_distribution` | extension 횟수 분포 | repeated hold 탐지 |
| `holds_with_extension_count_ge_2` | 두 번 이상 연장된 hold 수 | temporary 가정 붕괴 신호 |
| `missed_hold_review_count` | expiry 이전 review를 놓친 hold 수 | cadence discipline 실패 |
| `hold_resume_state_distribution` | hold 해제 후 어디로 복귀하는가 | retire/absorb/officialize queue 연결 |

권장 risk bucket:

- `overdue`
- `0-2bd`
- `3-7bd`
- `8bd+`

권장 slice:

- `hold_reason`
- `resume_state`
- `extension_count`
- `review_forum`
- `domain` 또는 `process_family`

추천 시각화:

- risk board: expiry bucket별 hold count
- table: overdue hold with `hold_reason`, `resume_state`, `extension_count`
- bar chart: `hold_reason x extension_count>=2`

이 패널이 있어야 [Temporary Hold Exit Criteria](./shadow-temporary-hold-exit-criteria.md)에서 말하는 `expire / extend / escalate` 판단이 실제 review queue로 이어진다.

### 6. retirement verification health 패널은 단일 점수보다 hard gate matrix가 우선이다

`verification_pending` health를 한 줄 score로 만들면 `manual_path_ratio` fail을 `audit_log_coverage` 개선으로 덮어 버리기 쉽다.
그래서 lifecycle verdict는 여전히 [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)의 hard gate를 따라야 하고, dashboard는 그 건강도를 matrix로 보여 주는 편이 좋다.
실무에서는 이 panel이 [Shadow Retirement Scorecard Schema](./shadow-retirement-scorecard-schema.md)의 `hard_gates.*.pass`, `verification_window.window_satisfied`, `verdict_record.status`를 그대로 읽어 집계하게 만드는 편이 field drift를 줄인다.

권장 핵심 metric:

| metric | 의미 | 기본 해석 |
|---|---|---|
| `verification_pending_count` | 현재 proof 수집 중인 entry 수 | closeout workload 규모 |
| `verification_hard_gate_pass_count` | hard gate 중 현재 pass한 개수 | readiness 근접도 참고값 |
| `verification_ready_count` | 모든 hard gate pass + window 충족 entry 수 | retirement 후보 |
| `verification_telemetry_gap_count` | metric freshness, baseline snapshot, audit completeness가 비는 entry 수 | proof 불능 상태 |
| `verification_metric_freshness_hours` | 마지막 proof metric 갱신 시점 이후 경과 시간 | stale telemetry 탐지 |
| `verification_window_remaining_days` | closeout window 종료까지 남은 시간 | premature close 방지 |
| `recurrence_detected_count` | verification 중 재발이 관찰된 entry 수 | false closure 탐지 |
| `failed_gate_distribution` | 어느 hard gate가 주로 fail하는가 | 구조 개선 우선순위 |

추천 status bucket:

- `ready_to_retire`
- `window_running`
- `gate_failed`
- `telemetry_gap`
- `recurrence_seen`

권장 slice:

- `verification_metric_family`
- `replacement_path`
- `review_forum`
- `decision`
- `process_family`

추천 시각화:

- hard gate matrix: entry 또는 process family별 pass/fail
- status donut: verification health bucket 분포
- freshness histogram: `verification_metric_freshness_hours`

중요한 규칙은 하나다.
`verification_hard_gate_pass_count = 6/7` 같은 값은 dashboard 보조 설명일 뿐이고, lifecycle state를 `retired`로 넘기는 근거는 아니다.

### 7. dashboard slice는 owner 기준만이 아니라 forum과 state lineage까지 보여야 한다

shadow lifecycle scorecard에서 자주 놓치는 slice는 `review_forum`과 `blocked_from_state`다.
owner별 정렬만 보면 구조 문제를 개인 bottleneck으로 오해하기 쉽다.

최소 공통 slice 권장안:

| slice | 왜 필요한가 |
|---|---|
| `review_forum` | 어느 governance venue가 backlog를 회수하지 못하는지 본다 |
| `decision` | retire/absorb/officialize track 중 어디가 막히는지 본다 |
| `process_family` | 같은 유형의 shadow path recurrence를 묶어 본다 |
| `criticality_tier` | 같은 age라도 위험도가 다름을 반영한다 |
| `blocked_from_state` | 어느 execution track에서 block이 시작됐는지 본다 |
| `resume_state` | hold가 어떤 실행 queue로 되돌아가는지 본다 |
| `verification_metric_family` | proof health 결손이 계측 문제인지 adoption 문제인지 본다 |

특히 `review_forum x lifecycle_state`, `blocker_class x blocked_from_state`, `hold_reason x resume_state`, `failed_gate x process_family` 조합은 운영 병목을 빠르게 드러낸다.

### 8. scorecard는 flow strip를 같이 붙여야 aging 원인을 읽을 수 있다

stock panel만 보면 age가 왜 커졌는지 잘 안 보인다.
그래서 최소한 아래 flow metric을 보조 패널로 같이 두는 편이 좋다.

- `entered_state_count_30d`
- `exited_state_count_30d`
- `state_transition_count_30d`
- `reopened_after_retired_count_30d`
- `hold_to_blocked_transition_count_30d`

예를 들어 `blocked_count`가 높아도 `exited_state_count_30d`가 빠르게 늘면 recovery 중일 수 있다.
반대로 total count는 평평해도 `hold_to_blocked` 전이가 늘면 운영 품질은 나빠지고 있다.

즉 aging panel은 stock을, flow strip는 **왜 그 aging이 생겼는지**를 설명한다.

### 9. 권장 운영 질문은 패널마다 달라야 한다

| 패널 | review forum이 바로 물어야 할 질문 |
|---|---|
| lifecycle aging | 어느 상태 backlog가 state SLA를 가장 많이 깨고 있는가 |
| blocked duration | 어떤 blocker class와 forum이 unblock 속도를 가장 크게 깎는가 |
| hold expiry | 어떤 hold가 이미 temporary 가정을 잃었는가 |
| retirement verification health | proof가 부족한가, 아니면 재발 때문에 truly retired가 불가능한가 |

좋은 scorecard는 숫자 해설보다 action prompt가 분명하다.
그래야 panel이 보고용 그림이 아니라 forum agenda로 이어진다.

---

## 코드로 보기

```yaml
shadow_lifecycle_scorecard:
  lifecycle_aging:
    state_age_buckets:
      decision_pending:
        over_sla: 4
        p95_days: 18
      blocked:
        over_sla: 6
        p95_days: 27
  blocked_duration:
    by_blocker_class:
      owner_gap:
        blocked_count: 3
        p95_days: 21
      control_plane_gap:
        blocked_count: 2
        p95_days: 34
  hold_expiry:
    overdue_open_count: 2
    expiring_in_2bd_count: 5
    extension_count_ge_2: 3
  retirement_verification_health:
    ready_to_retire: 2
    gate_failed: 4
    telemetry_gap: 1
    failed_gates:
      manual_path_ratio: 2
      audit_log_coverage: 3
      recurrence_after_closure: 1
```

좋은 scorecard는 lifecycle을 예쁘게 채색하는 것이 아니라, **어느 shadow entry가 왜 멈췄고 어떤 forum이 바로 움직여야 하는지**를 드러내는 데 목적이 있다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| total count only | 만들기 쉽다 | 거의 모든 control-state 위험을 숨긴다 | 권장하지 않음 |
| state aging panel | backlog 정체가 보인다 | hold overdue와 proof gap을 충분히 못 본다 | 초기 가시화 |
| 4-panel lifecycle scorecard | aging, blocker, hold, verification을 함께 본다 | schema discipline과 metric freshness가 필요하다 | shadow catalog 운영이 본격화될 때 |
| 4-panel scorecard + flow strip | action 우선순위까지 읽힌다 | 운영 해석이 더 필요하다 | portfolio governance가 성숙할 때 |

shadow lifecycle scorecard의 목적은 점수를 예쁘게 만드는 것이 아니라, **state별 정체와 control-state 위험과 retirement proof 건강도를 같은 운영 언어로 보이게 만드는 것**이다.

---

## 꼬리질문

- 지금 shadow backlog는 총량이 문제인가, 특정 `lifecycle_state`의 aging이 문제인가?
- `blocked` 중 가장 긴 항목은 어떤 `blocked_from_state`와 `blocker_class`에 몰려 있는가?
- overdue hold와 `extension_count >= 2` hold를 누가 언제 재판정하는가?
- `verification_pending` 중 proof가 거의 끝난 항목과 telemetry gap 때문에 멈춘 항목을 구분해 보고 있는가?
- 이 scorecard가 `review_forum` agenda와 실제 escalation clock으로 이어지는가?

## 한 줄 정리

Shadow Lifecycle Scorecard Metrics는 shadow catalog를 총량으로 보지 않고, lifecycle aging, blocked duration, hold expiry, retirement verification health를 분리한 대시보드로 backlog 정체와 가짜 종료를 동시에 드러내게 하는 운영 문서다.
