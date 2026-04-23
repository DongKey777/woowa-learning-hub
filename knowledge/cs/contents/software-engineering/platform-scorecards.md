# Platform Scorecards

> 한 줄 요약: platform scorecards는 플랫폼 채택률만 보는 표가 아니라, **normal-path health, break-glass visibility, governance spillover**를 나란히 보여 주며 어떤 개선이 제품 문제인지, 비상 운영 문제인지, 정책 debt 문제인지 구분하게 만드는 운영 패널이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Platform Scorecards](./README.md#platform-scorecards)
> - [Platform Paved Road Trade-offs](./platform-paved-road-tradeoffs.md)
> - [Service Template Trade-offs](./service-template-tradeoffs.md)
> - [Service Bootstrap Governance](./service-bootstrap-governance.md)
> - [Service Maturity Model](./service-maturity-model.md)
> - [Ownership Metadata Quality](./ownership-metadata-quality.md)
> - [Platform Control Plane and Delegation Boundaries](./platform-control-plane-delegation-boundaries.md)
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)
> - [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)
> - [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)
> - [Break-Glass Reentry Governance](./break-glass-reentry-governance.md)
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)

> retrieval-anchor-keywords:
> - platform scorecard
> - platform adoption
> - developer experience
> - exception usage
> - paved road adoption
> - platform reliability
> - platform health
> - self-service metrics
> - platform scorecard panel template
> - normal path health panel
> - break-glass visibility panel
> - governance spillover panel
> - platform exception scorecard
> - break glass reentry lag
> - override spillover metrics

## 핵심 개념

플랫폼은 만들어 놓는 것보다 잘 쓰이게 하는 것이 더 어렵다.

scorecard는 플랫폼의 성공을 한 가지 숫자로 재지 않는다.

- 채택률
- 만족도
- 우회 경로 비율
- provisioning time
- incident rate
- exception count

을 함께 본다.

좋은 scorecard는 특히 아래 세 질문을 같은 화면에서 분리해 답해야 한다.

- 평시 official path가 건강한가
- emergency / break-glass가 얼마나 자주, 얼마나 오래 켜지는가
- override와 shadow 징후가 governance backlog로 번지고 있는가

즉 platform scorecard는 **플랫폼 제품의 운영 성과표이자 triage panel**이다.

---

## 깊이 들어가기

### 1. 채택률만 보면 안 된다

많이 쓰인다고 좋은 플랫폼은 아니다.

우회 사용이 많으면:

- 정책이 너무 강하거나
- 기능이 부족하거나
- 문서가 부족할 수 있다

### 2. reliability와 DX를 같이 본다

플랫폼이 안정적이어도 쓰기 어렵다면 실패다.
반대로 쓰기 쉬워도 자주 깨지면 실패다.

### 3. exception ratio는 중요한 신호다

예외 경로가 많아지면 paved road가 맞지 않는다는 뜻일 수 있다.

### 4. scorecard는 panel을 나눠야 해석이 안 섞인다

한 장의 숫자판에 모든 예외를 섞으면 질문이 뒤틀린다.

- `manual_path_ratio`는 평시 normal path leakage를 봐야 한다
- `break_glass_request_count`는 incident와 emergency pressure를 봐야 한다
- override aging과 재분류 건수는 governance debt를 봐야 한다

같은 count라도 어느 panel에 놓이느냐에 따라 action owner가 달라진다.

### 5. concrete panel template은 세 칸이면 충분하다

권장 기본 배치는 아래와 같다.

| panel | 운영 질문 | 대표 metric | 해석 포인트 | 기본 owner | 바로 연결할 drilldown |
|---|---|---|---|---|---|
| `normal_path_health` | 평시 공식 경로가 건강한가 | `paved_road_adoption_rate`, `manual_path_ratio`, `median_provision_time_minutes`, `template_success_rate`, `p95_platform_api_error_rate` | adoption이 높아도 `manual_path_ratio`가 오르면 DX나 기본 flow가 새고 있다는 뜻이다 | platform PM, bootstrap owner | template별 실패, team별 onboarding friction, top manual workflow |
| `break_glass_visibility` | 비상 운영이 얼마나 자주, 얼마나 오래 켜지는가 | `break_glass_request_count`, `share_of_total_requests`, `median_reentry_lag_hours`, `overdue_reentry_count`, `unauthorized_break_glass_count`, `break_glass_audit_log_coverage` | request 수보다 `reentry` 지연과 unauthorized 사용이 더 강한 위험 신호다 | on-call owner, policy owner | incident별 reentry 상태, policy key별 반복 activation, audit gap |
| `governance_spillover` | 예외가 구조적 debt로 번지고 있는가 | `open_override_count`, `override_over_30d_ratio`, `repeat_policy_override_count`, `break_glass_to_shadow_reclassified_count`, `ownerless_exception_ratio`, `shadow_candidate_count` | normal path 문제와 emergency 문제를 넘어서 policy scope, ownership, redesign backlog 문제를 드러낸다 | governance forum, platform architect | override registry, shadow catalog, policy redesign backlog |

핵심은 세 panel을 "한 점수"로 합치지 않는 것이다.
normal-path가 빨간데 break-glass는 초록이면 DX 문제일 수 있고,
normal-path는 초록인데 governance spillover가 붉으면 예외를 숨기며 운영하고 있을 가능성이 높다.

### 6. 분모를 섞지 말아야 panel이 정직해진다

같은 `manual` 작업이라도 panel마다 분모가 달라야 한다.

| panel | 기본 분모 | 포함해야 할 것 | 제외하거나 분리해야 할 것 |
|---|---|---|---|
| `normal_path_health` | `normal_eligible_requests` | normal official flow, shadow/manual leakage | authorized break-glass, drills, recovery backfill |
| `break_glass_visibility` | `authorized_break_glass_events` 또는 total request sidecar | authorized break-glass, overdue reentry, audit coverage | routine override, drill은 별도 segment 또는 하위 row |
| `governance_spillover` | `open_overrides_and_reclassified_items` | aged override, repeated policy, ownerless item, shadow candidate | 순수 incident count 자체는 제외하고 spillover된 결과만 포함 |

이 분리가 없으면 incident가 많았던 주에 `manual_path_ratio`가 거짓으로 튀거나,
반대로 break-glass를 숨겨 scorecard가 깨끗해 보이는 왜곡이 생긴다.

### 7. panel template은 threshold보다 action mapping이 더 중요하다

지표가 있으면:

- 어떤 기본 경로를 개선할지
- 어디서 우회가 생기는지
- 어떤 팀이 플랫폼 가치를 못 느끼는지

를 볼 수 있다.

권장 해석은 다음처럼 단순하게 닫을 수 있다.

| panel 상태 | 우선 의심할 것 | 기본 액션 |
|---|---|---|
| `normal_path_health`만 악화 | template UX, bootstrap friction, paved road 기능 부족 | onboarding 개선, top manual workflow 제품화 |
| `break_glass_visibility`만 악화 | incident 빈도, unsafe rollout, reentry discipline 부족 | reentry review, incident/policy postmortem 연결 |
| `governance_spillover`만 악화 | override 회수 실패, policy scope drift, owner 공백 | override burn-down escalation, policy redesign |
| 세 panel이 함께 악화 | platform product/operating model mismatch | capability boundary 재설계, roadmap 재우선순위 |

### 8. scorecard는 platform maturity와 연결된다

이 문맥은 [Service Maturity Model](./service-maturity-model.md)과 연결된다.
초기에는 `normal_path_health` 위주로 시작해도 되지만, 플랫폼이 커질수록 break-glass와 spillover panel을 붙여야 scorecard가 governance 도구가 된다.

---

## 실전 시나리오

### 시나리오 1: 플랫폼 도입률이 낮다

문서, onboarding, defaults를 다시 봐야 한다.

### 시나리오 2: 도입률은 높은데 break-glass panel이 붉다

플랫폼을 억지로 많이 쓰고 있을 수는 있다.
incident 중 수동 activation이 반복되고 `median_reentry_lag_hours`가 길다면, 채택률이 아니라 운영 안전성이 문제다.

### 시나리오 3: 예외가 많이 발생하고 governance spillover도 쌓인다

golden path나 bootstrap policy가 너무 딱딱한지, 아니면 override registry와 owner handoff가 비어 있는지 함께 확인한다.

### 시나리오 4: 플랫폼은 안정적인데 만족도가 낮다

DX, 속도, self-service 흐름을 개선해야 한다.

---

## 코드로 보기

```yaml
platform_scorecard:
  period: 2026-W15
  panel_layout:
    normal_path_health:
      question: "평시 공식 경로가 건강한가?"
      denominator_scope: normal_eligible_requests
      metrics:
        paved_road_adoption_rate: 0.89
        manual_path_ratio: 0.04
        median_provision_time_minutes: 7
        template_success_rate: 0.97
        p95_platform_api_error_rate: 0.008
      action_if_red:
        - bootstrap_flow_review
        - top_manual_workflow_productization
    break_glass_visibility:
      question: "비상 운영이 얼마나 자주, 얼마나 오래 켜지는가?"
      denominator_scope: authorized_break_glass_events
      metrics:
        break_glass_request_count: 6
        share_of_total_requests: 0.01
        median_reentry_lag_hours: 5.5
        overdue_reentry_count: 1
        unauthorized_break_glass_count: 0
        break_glass_audit_log_coverage: 1.0
      action_if_red:
        - reentry_slo_review
        - incident_policy_drilldown
    governance_spillover:
      question: "예외가 구조적 debt로 번지고 있는가?"
      denominator_scope: open_overrides_and_reclassified_items
      metrics:
        open_override_count: 14
        override_over_30d_ratio: 0.36
        repeat_policy_override_count: 5
        break_glass_to_shadow_reclassified_count: 2
        ownerless_exception_ratio: 0.0
        shadow_candidate_count: 3
      action_if_red:
        - override_burn_down_review
        - policy_redesign_backlog
```

이 템플릿을 쓰면 한 주의 문제 신호를 한 숫자로 숨기지 않고,
"제품 경로 개선", "비상 운영 복귀", "거버넌스 debt 회수"를 다른 owner에게 바로 넘길 수 있다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 KPI | 보기 쉽다 | 왜곡된다 | 초기 |
| 멀티 metric scorecard | 균형이 좋다 | 해석이 필요하다 | 플랫폼이 커질 때 |
| panel template + action loop | 해석이 선명하고 owner 연결이 쉽다 | 분모 설계와 cadence가 필요하다 | 성숙한 플랫폼 |

platform scorecards는 플랫폼을 "있다/없다"가 아니라 **잘 작동하는 제품**으로 보기 위한 도구다.

---

## 꼬리질문

- 채택률 외에 무엇을 봐야 하는가?
- normal-path health와 break-glass visibility를 왜 분리해서 봐야 하는가?
- governance spillover panel에는 어떤 debt만 올려야 하는가?
- 예외 비율이 높다는 건 무엇을 의미하는가?
- scorecard 결과를 누가 행동으로 옮기는가?
- 플랫폼 만족도를 어떻게 정량화할 것인가?

## 한 줄 정리

Platform scorecards는 플랫폼의 채택, 안정성, DX, 예외 사용량을 한데 묶되, **normal-path health, break-glass visibility, governance spillover를 side-by-side panel로 분리해** 어떤 운영 문제가 어디로 escalation되어야 하는지 보여 주는 scorecard다.
