# Operational Readiness Drills and Change Safety

> 한 줄 요약: operational readiness는 체크리스트를 채웠다고 증명되지 않고, rollback, kill switch, degraded mode, restore, comms flow를 실제로 연습해 본 evidence가 있어야 하며, 그 evidence가 change safety의 risk tier와 rollout speed를 결정해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Operational Readiness Drills and Change Safety](./README.md#operational-readiness-drills-and-change-safety)
> - [Production Readiness Review](./production-readiness-review.md)
> - [Rollout Approval Workflow](./rollout-approval-workflow.md)
> - [Runbook, Playbook, Automation Boundaries](./runbook-playbook-automation-boundaries.md)
> - [Kill Switch Fast-Fail Ops](./kill-switch-fast-fail-ops.md)
> - [Release Policy, Change Freeze, and Error Budget Coupling](./release-policy-change-freeze-error-budget-coupling.md)
> - [Rollout Guardrail Profiles, Auto-Pause, and Manual Resume](./rollout-guardrail-profiles-auto-pause-resume.md)

> retrieval-anchor-keywords:
> - operational readiness drill
> - change safety
> - readiness evidence
> - rollback drill
> - game day
> - launch rehearsal
> - kill switch drill
> - risk tier

## 핵심 개념

운영 준비가 되었다는 말은 문서가 있다는 뜻이 아니다.
실제 사고가 났을 때 팀이 안전하게 멈추고, 되돌리고, 축소 운영하고, 커뮤니케이션할 수 있어야 한다.

그래서 readiness는 evidence로 봐야 한다.

예:

- rollback drill 수행 여부
- canary pause 훈련 여부
- kill switch 작동 검증
- 복구 책임자 연락 체계 검증
- degraded mode 사용자 영향 확인

즉 operational readiness는 review 문서가 아니라 **실행 가능한 change safety 능력**이다.

---

## 깊이 들어가기

### 1. checklist는 필요하지만 evidence가 더 중요하다

PRR checklist가 모두 채워져도, 실제로 rollback을 한 번도 안 해봤다면 운영 준비가 되었다고 보기 어렵다.

좋은 evidence 예:

- 최근 90일 내 rollback rehearsal
- runbook 기반 on-call drill
- restore time 측정 결과
- comms template 실제 점검
- config rollback or feature disable rehearsal

즉 readiness는 존재 여부보다 **검증 이력**이 중요하다.

### 2. risk tier마다 요구되는 drill이 달라야 한다

모든 변경에 같은 수준의 rehearsal을 요구하면 과하다.
반대로 핵심 경로에 가벼운 checklist만 적용하면 위험하다.

예시:

- low risk: observability sanity check
- medium risk: canary + rollback rehearsal
- high risk: kill switch + restore + communication drill
- critical migration: cutover rehearsal + reconciliation evidence

change safety는 균일 절차가 아니라 **risk-calibrated readiness**다.

### 3. drill 결과는 rollout speed와 approval depth를 바꿔야 한다

연습을 했다는 사실만 저장하면 의미가 약하다.
결과가 실제 gate에 반영돼야 한다.

예:

- rollback 미검증 -> full rollout 금지
- kill switch 미검증 -> side-effect 기능 일부 사용자만 허용
- comms flow 미검증 -> business-hour launch only
- restore time 초과 -> additional approval 필요

즉 drill은 교육이 아니라 **배포 조건을 조정하는 evidence**다.

### 4. evidence에는 유효 기간이 있다

한 번 drill했다고 영원히 안전한 것은 아니다.

evidence가 금방 낡는 경우:

- 팀 교체
- 시스템 구조 변경
- external dependency 변경
- config/control plane 변경

그래서 readiness evidence는 보통 expiry를 붙여 관리하는 편이 좋다.

### 5. drill은 실제 위험을 낮추되, 실제 위험을 만들면 안 된다

좋은 drill은 production-like하지만 통제된다.

원칙:

- blast radius 제한
- clear abort condition
- observer assigned
- rollback owner 지정
- business communication 준비

drill이 통제되지 않으면, rehearsal이 아니라 새로운 incident가 된다.

---

## 실전 시나리오

### 시나리오 1: 새 결제 플로우를 출시한다

성공 경로 테스트만으로는 부족하다.
PG 장애 시 kill switch, fallback 안내, operator comms까지 rehearsal해야 한다.

### 시나리오 2: 중요한 config 변경을 배포한다

코드가 안 바뀌어도 retry/timeout 조정은 큰 사고를 만들 수 있다.
config rollback drill이 없으면 high-risk로 봐야 한다.

### 시나리오 3: 새 데이터 마이그레이션 cutover를 앞둔다

reconciliation evidence와 rollback window rehearsal이 없으면 readiness가 낮다.
cutover 당일에 처음 해보는 절차가 있으면 안 된다.

---

## 코드로 보기

```yaml
change_safety:
  risk_tier: high
  required_evidence:
    - rollback_drill_within_90d
    - kill_switch_verified
    - comms_flow_checked
  rollout_limits:
    initial_canary_percent: 5
    business_hours_only: true
  block_if:
    - no_recent_readiness_drill
```

좋은 change safety 모델은 위험도와 증거와 rollout 제한을 함께 묶는다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| checklist 중심 | 운영이 단순하다 | 실제 대응 능력을 과신할 수 있다 | low-risk 변경 |
| drill 중심 | 현실적이다 | 시간과 준비가 든다 | high-risk 변경 |
| evidence-based rollout | 안전성과 속도의 균형이 좋다 | 모델 설계가 필요하다 | 성숙한 조직 |

operational readiness drills의 목적은 팀을 시험하는 것이 아니라, **변경이 실제 사고가 되었을 때도 안전하게 다룰 수 있다는 근거를 미리 확보하는 것**이다.

---

## 꼬리질문

- 이 변경의 risk tier는 무엇이고 어떤 drill evidence가 필요한가?
- 최근 drill 결과가 지금 구조에도 여전히 유효한가?
- rollout speed와 approval depth가 readiness evidence에 따라 달라지는가?
- runbook은 있는데 실제로 써 본 적도 있는가?

## 한 줄 정리

Operational readiness drills and change safety는 운영 준비를 문서 존재가 아니라 실제 drill evidence로 판단하고, 그 결과를 rollout 속도와 승인 강도에 반영하는 방식이다.
