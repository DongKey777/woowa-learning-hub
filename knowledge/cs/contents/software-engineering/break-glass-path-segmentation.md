# Break-Glass Path Segmentation

> 한 줄 요약: emergency와 official break-glass workflow는 scorecard에서 숨기지 말아야 하지만, shadow retirement proof의 normal-path denominator에 섞으면 `manual_path_ratio`, `replacement_adoption_rate`, `audit_log_coverage` 해석이 깨지므로 별도 segment와 visibility panel로 분리해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)
> - [Platform Scorecards](./platform-scorecards.md)
> - [Golden Path Escape Hatch Policy](./golden-path-escape-hatch-policy.md)
> - [Break-Glass Reentry Governance](./break-glass-reentry-governance.md)
> - [Operational Readiness Drills and Change Safety](./operational-readiness-drills-and-change-safety.md)
> - [Kill Switch and Fast-Fail Ops](./kill-switch-fast-fail-ops.md)
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)
> - [Shadow Process Detection Signals](./shadow-process-detection-signals.md)
> - [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)
> - [Shadow Retirement Scorecard Schema](./shadow-retirement-scorecard-schema.md)

> retrieval-anchor-keywords:
> - break-glass path segmentation
> - emergency workflow scorecard
> - manual_path_ratio denominator
> - break glass denominator exclusion
> - emergency override visibility
> - incident break glass tracking
> - authorized break glass path
> - emergency path segmentation
> - scorecard panel split
> - manual path ratio exception mode
> - shadow retirement denominator split
> - break glass retirement proof
> - replacement adoption denominator
> - audit log coverage denominator split
> - official fallback visibility
> - break glass reentry lag
> - break glass reentry governance
> - break glass owner handoff
> - unauthorized break glass detection

## 핵심 개념

break-glass는 "수동이라서 다 나쁜 경로"가 아니라, **평시 기본 경로가 아닌 비상 모드**다.
그래서 scorecard는 두 질문을 분리해야 한다.

- 정상 control plane을 써야 했던 request 중 몇 건이 manual/shadow path로 샜는가?
- emergency/break-glass가 얼마나 자주 켜졌고, 얼마나 빨리 정상 경로로 복귀했는가?

이 둘을 섞으면 `manual_path_ratio`가 incident volume에 따라 출렁이고, 반대로 분리 없이 빼 버리면 실제 운영 압력이 대시보드에서 사라진다.

즉 break-glass의 목표는 "분모 제외"가 아니라 **별도 segment로 보존하면서 정상 경로 건강도와 분리해 읽는 것**이다.

---

## 깊이 들어가기

### 1. break-glass를 normal denominator에 넣으면 해석이 틀어진다

`manual_path_ratio`는 원래 "공식 normal path를 탔어야 하는 request 중 manual path로 새는 비율"을 보려는 지표다.
그런데 incident 대응, emergency cutover, kill-switch 수동 실행 같은 break-glass request를 같은 분모에 넣으면 두 가지 왜곡이 생긴다.

- incident가 많은 주에 ratio가 급등해도 normal path 품질 문제인지 판단이 안 된다
- 팀이 scorecard를 방어하려고 break-glass 사용 자체를 기록하지 않으려는 유인이 생긴다

그래서 break-glass는 숨겨진 예외가 아니라 **정상 경로와 다른 운영 모드**로 모델링해야 한다.

### 2. 우선 `path_segment`와 `counts_in_manual_path_ratio`를 같이 저장한다

가장 단순한 분리 모델은 다음 두 필드다.

- `path_segment`: request가 어떤 운영 모드에서 처리됐는지
- `counts_in_manual_path_ratio`: normal ratio의 numerator/denominator에 포함되는지

권장 segment 예시는 다음과 같다.

| path_segment | 의미 | normal denominator 포함 | normal numerator 포함 | 반드시 보여 줄 panel |
|---|---|---|---|---|
| `normal_official` | 정상 control plane으로 처리 | 포함 | 제외 | normal path health |
| `manual_shadow` | 공식 normal path가 있었는데 DM/시트/문서 우회로 처리 | 포함 | 포함 | normal path health, shadow review |
| `break_glass_authorized` | incident / emergency 선언 하의 공식 break-glass 실행 | 제외 | 제외 | break-glass usage |
| `break_glass_drill` | game day, readiness drill, training | 제외 | 제외 | drill / readiness |
| `recovery_backfill` | 사고 후 backfill, reconciliation, 상태 복구 | 제외 | 제외 | recovery load |

핵심은 break-glass를 "조용히 제외"하는 것이 아니라, `counts_in_manual_path_ratio=false`이면서도 별도 panel에는 반드시 나타나게 만드는 것이다.

### 3. 포함 규칙은 eligibility가 아니라 mode 전환 근거로 닫아야 한다

분류가 흔들리는 이유는 "수동 작업이면 break-glass"처럼 느슨하게 잡기 때문이다.
다음 근거가 있어야 `break_glass_authorized`로 두는 편이 안전하다.

- `emergency_ref`: incident, sev, change-freeze exception, paging event 같은 공식 근거가 있다
- `approved_break_glass_by`: on-call commander나 policy owner 등 승인 주체가 기록된다
- `reentry_expectation`: 언제 normal path로 돌아올지 deadline이나 follow-up action이 있다
- `scope`: 어떤 서비스/tenant/environment에만 적용되는지 제한이 있다

이 중 핵심 근거가 없으면 emergency가 아니라 routine override일 가능성이 높다.
그 경우는 `manual_shadow`나 일반 override debt로 다시 분류해야 한다.

### 4. normal ratio와 break-glass visibility는 서로 다른 식으로 계산한다

권장 normal ratio는 다음처럼 닫는다.

```text
manual_path_ratio
  = count(distinct request_id
      where path_segment = 'manual_shadow'
        and counts_in_manual_path_ratio = true)
    / count(distinct request_id
      where counts_in_manual_path_ratio = true)
```

즉 numerator와 denominator 모두 **normal control plane이 기대됐던 request만** 본다.

대신 break-glass는 별도 지표를 둔다.

- `break_glass_request_count`
- `break_glass_share_of_total_requests`
- `median_break_glass_reentry_lag_minutes`
- `unauthorized_break_glass_count`
- `repeat_break_glass_by_policy_key`

이렇게 하면 normal path 건전성과 emergency 운영 압력을 동시에 읽을 수 있다.

### 5. shadow retirement proof도 denominator split과 fallback visibility를 같이 가져야 한다

shadow retirement proof에서 특히 흔한 실수는 `manual_path_ratio = 0`만 보고 "fallback이 사라졌다"고 해석하는 것이다.
하지만 official break-glass는 **shadow leakage가 아니라 승인된 fallback mode**이므로 normal-path hard gate 분모에서는 빼되, usage 자체는 따로 증빙해야 한다.

retirement hard gate별 권장 denominator는 다음처럼 닫는 편이 안전하다.

| hard gate | denominator에 포함할 request | break-glass 처리 | 왜 이렇게 보나 |
|---|---|---|---|
| `manual_path_ratio` | `normal_official`, `manual_shadow`처럼 normal path가 기대됐던 request | `break_glass_authorized`, `break_glass_drill`, `recovery_backfill` 제외 | shadow leakage만 측정해야 false fail을 막는다 |
| `replacement_adoption_rate` | replacement path가 실제로 처리할 수 있었던 eligible request | authorized break-glass는 분자/분모 모두 제외 | emergency fallback을 replacement failure로 오인하지 않기 위해 |
| `audit_log_coverage` | 공식 normal path를 탄 eligible request | break-glass는 `break_glass_audit_log_coverage`로 별도 추적 | normal control-plane traceability와 emergency traceability를 분리하기 위해 |

핵심은 "빼고 끝내는 것"이 아니라, **분모에서 뺀 request 수와 품질을 다른 panel에서 강제로 보여 주는 것**이다.
그래서 retirement scorecard에는 normal hard gate 옆에 최소 다음 visibility 묶음이 필요하다.

- `break_glass_request_count`
- `break_glass_audit_log_coverage`
- `break_glass_last_used_at`
- `repeat_break_glass_by_policy_key`
- `unauthorized_break_glass_count`

또한 official label만 붙이면 다 break-glass로 인정하면 안 된다.
`emergency_ref`, `approved_break_glass_by`, `scope`, `reentry_expectation` 중 핵심 근거가 비어 있거나, incident 없이 routine하게 반복되면 `manual_shadow`로 재분류해 retirement denominator에 다시 포함하는 편이 맞다.

```yaml
shadow_retirement_scorecard:
  denominator_scope:
    normal_eligible_request_count: 84
    excluded_segments:
      break_glass_authorized: 3
      break_glass_drill: 2
      recovery_backfill: 4
  hard_gates:
    manual_path_ratio:
      denominator_scope: normal_eligible_only
      measurement:
        value: 0.0
        sample_size: 84
    replacement_adoption_rate:
      denominator_scope: normal_eligible_only
      measurement:
        value: 1.0
        sample_size: 84
    audit_log_coverage:
      denominator_scope: normal_eligible_only
      measurement:
        value: 1.0
        sample_size: 84
  segmented_visibility:
    break_glass:
      request_count: 3
      audit_log_coverage: 1.0
      unauthorized_count: 0
      repeat_policy_keys:
        freeze_window: 2
```

이 구조가 있으면 `manual_path_ratio = 0`이더라도 "공식 fallback이 얼마나 남아 있었는가"를 동시에 말할 수 있다.
반대로 `segmented_visibility.break_glass`가 없으면 팀이 denominator만 깨끗하게 만들고 fallback usage를 통째로 숨길 수 있다.

### 6. scorecard는 한 숫자 대신 panel을 분리해야 한다

좋은 scorecard는 break-glass를 footer에 숨기지 않는다.
보통 세 panel이면 충분하다.

- normal path panel: `manual_path_ratio`, `manual_path_request_count`, `shadow_candidate_count`
- break-glass panel: `break_glass_request_count`, `median_reentry_lag`, `unauthorized_break_glass_count`
- governance spillover panel: `repeat_break_glass_by_policy`, `incident 없는 break-glass`, `break_glass_to_shadow_reclassified_count`

이 구성을 쓰면 "평시 공식 경로가 새는 문제"와 "비상 모드가 과도하게 켜지는 문제"를 같은 scorecard에서 보되, 해석은 서로 섞이지 않는다.

### 7. break-glass가 반복되면 visibility 대상이면서 동시에 redesign 신호다

break-glass를 denominator에서 뺐다고 끝나지 않는다.
다음 패턴은 별도 escalation이 필요하다.

- 특정 policy key에서 incident 없이 break-glass가 반복된다
- 같은 팀이 월별로 비슷한 emergency override를 계속 연다
- reentry lag가 길어 사실상 semi-permanent manual path가 된다
- drill로 태깅했지만 실제로는 운영 의사결정을 대신하고 있다

이때는 break-glass panel에서 끝내지 말고, [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)나 [Shadow Process Detection Signals](./shadow-process-detection-signals.md)로 넘겨 구조 문제로 다루는 편이 맞다.

### 8. drill과 real incident를 같이 빼면 readiness가 가려진다

훈련 traffic도 normal denominator에는 넣지 않는 편이 맞다.
하지만 drill과 real incident를 한 bucket으로 합치면 다음 질문에 답을 못 한다.

- 실제 emergency 사용이 늘어난 것인가?
- readiness drill coverage가 좋아진 것인가?
- drill이 production emergency path와 동일한 control을 검증했는가?

그래서 `break_glass_drill`은 `break_glass_authorized`와 panel을 나누거나 최소한 segment를 분리해 둬야 한다.

### 9. event보다 request fact가 더 중요하다

break-glass도 DM, paging alert, CLI 실행, spreadsheet override row처럼 여러 raw event를 남긴다.
하지만 scorecard는 request fact를 봐야 한다.

```yaml
path_segmented_request_fact:
  request_id: chg-4821
  workflow_family: rollout_override
  policy_key: freeze_window
  path_segment: break_glass_authorized
  counts_in_manual_path_ratio: false
  emergency_ref: inc-771
  approved_break_glass_by: primary-oncall
  scope:
    service: checkout-api
    environment: production
  reentry_deadline: 2026-04-14T11:30:00+09:00
  scorecard_buckets:
    - break_glass_usage
    - emergency_review
```

```yaml
operations_scorecard:
  normal_path:
    eligible_requests: 84
    manual_path_requests: 9
    manual_path_ratio: 0.11
  break_glass:
    authorized_requests: 3
    drill_requests: 2
    median_reentry_lag_minutes: 47
    unauthorized_break_glass_count: 1
  governance_spillover:
    repeat_break_glass_by_policy:
      freeze_window: 2
```

이렇게 두면 emergency request 3건이 보이면서도, normal `manual_path_ratio` 분모 84건은 오염되지 않는다.

---

## 실전 시나리오

### 시나리오 1: sev-1 incident 중 on-call이 break-glass 배포를 승인했다

이 경우 `break_glass_authorized`로 잡고 normal denominator에서는 뺀다.
대신 incident ref와 reentry lag를 scorecard에 남겨 emergency pressure를 보이게 한다.

### 시나리오 2: freeze window인데 incident 없이 release manager가 DM으로 예외를 열어 줬다

이건 break-glass가 아니라 normal path leakage에 가깝다.
공식 경로를 우회한 것이므로 `manual_shadow`나 일반 override로 잡아 `manual_path_ratio` numerator에 포함하는 편이 맞다.

### 시나리오 3: game day drill에서 kill switch를 수동 실행했다

훈련 traffic이므로 normal denominator에는 넣지 않는다.
하지만 `break_glass_drill` panel에서 drill coverage와 control 검증 결과를 보여 줘야 한다.

### 시나리오 4: 매월 같은 vendor migration 때문에 "긴급" allowlist 업데이트를 한다

반복성이 높다면 emergency가 아니라 구조화되지 않은 운영 절차일 가능성이 높다.
이 경우 break-glass count만 보고 넘어가지 말고 shadow candidate 또는 override redesign 대상으로 승격해야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| break-glass를 normal ratio에 포함 | 계산이 단순하다 | incident와 shadow leakage가 섞여 해석이 무너진다 | 권장하지 않음 |
| break-glass를 완전히 제외하고 숨김 | normal ratio는 깨끗해 보인다 | emergency load와 abuse를 놓친다 | 권장하지 않음 |
| segment 분리 + 별도 panel | 해석이 선명하고 governance action으로 연결된다 | 필드와 panel 설계가 더 필요하다 | 성숙한 운영 scorecard |

break-glass path segmentation의 목적은 예외를 감추는 것이 아니라, **정상 경로 건강도와 비상 운영 압력을 다른 질문으로 측정하게 만드는 것**이다.

---

## 꼬리질문

- 어떤 근거가 있어야 `break_glass_authorized`로 분류할 것인가?
- break-glass 사용 후 normal path 복귀 시간을 어떤 SLO로 볼 것인가?
- drill traffic과 real emergency를 scorecard에서 분리하고 있는가?
- shadow retirement proof에서 `manual_path_ratio`, `replacement_adoption_rate`, `audit_log_coverage`가 같은 denominator scope를 공유하는가?
- denominator에서 뺀 official break-glass request 수와 unauthorized count를 별도 panel로 항상 보여 주는가?
- 반복 break-glass를 shadow process 후보나 override redesign backlog로 넘기는가?

## 한 줄 정리

Break-Glass Path Segmentation은 emergency workflow를 scorecard에서 숨기지 않으면서도, normal `manual_path_ratio`와 shadow retirement proof 분모를 오염시키지 않도록 path mode, denominator scope, visibility panel을 분리하는 운영 설계다.
