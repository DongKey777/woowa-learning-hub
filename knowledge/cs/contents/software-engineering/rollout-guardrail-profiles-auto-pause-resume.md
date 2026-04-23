# Rollout Guardrail Profiles, Auto-Pause, and Manual Resume

> 한 줄 요약: rollout governance가 실전에서 작동하려면 모든 변경에 같은 기준을 쓰는 대신 change archetype과 service criticality에 따라 guardrail profile을 나누고, 자동 pause와 사람의 resume 판단을 분리해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Rollout Approval Workflow](./rollout-approval-workflow.md)
> - [Release Policy, Change Freeze, and Error Budget Coupling](./release-policy-change-freeze-error-budget-coupling.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Service Criticality Tiering and Control Intensity](./service-criticality-tiering-control-intensity.md)
> - [Operational Readiness Drills and Change Safety](./operational-readiness-drills-and-change-safety.md)
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)

> retrieval-anchor-keywords:
> - rollout guardrail
> - auto pause
> - manual resume
> - rollout profile
> - canary threshold
> - release guardrail
> - pause rule
> - control profile

## 핵심 개념

모든 배포를 같은 canary rule과 같은 관측 기준으로 다루면 guardrail이 너무 약하거나 너무 무거워진다.

그래서 실전에서는 rollout guardrail profile을 나누는 편이 낫다.

예:

- config change
- schema / contract change
- side-effect path change
- data migration cutover
- UI-only change

즉 rollout guardrail은 단일 수치가 아니라 **변경 유형별 control profile**이다.

---

## 깊이 들어가기

### 1. profile은 change type과 service criticality를 같이 본다

같은 config change라도 critical payment path와 low-risk internal tool은 다르게 다뤄야 한다.

그래서 profile은 보통 다음 입력으로 정한다.

- change archetype
- service criticality
- rollback difficulty
- blast radius
- observability quality

### 2. auto-pause와 manual-resume을 분리해야 한다

자동화는 멈추는 데는 강하지만, 다시 여는 판단은 맥락이 필요하다.

좋은 패턴:

- auto pause: error rate, drift signal, business KPI 급락
- human resume: 원인 이해, mitigations 적용, residual risk 판단

즉 guardrail은 완전 자동배포보다 **자동 차단 + 사람 승인 재개**가 더 현실적인 경우가 많다.

### 3. threshold는 기술 지표만이 아니라 business signal도 봐야 한다

5xx, latency만 보고 괜찮다고 해도 실제 전환율이나 결제 성공률이 무너지면 pause해야 할 수 있다.

profile별 signal 예:

- API change: parse error, unknown field fallback, 5xx
- payment flow: success rate, retry spike, charge duplication
- migration cutover: diff rate, replay failure, backlog age

### 4. false positive를 줄이려면 profile별 warm-up window가 필요하다

변경 직후 짧은 흔들림을 모두 incident로 보면 guardrail fatigue가 생긴다.

그래서 보통 다음을 둔다.

- warm-up duration
- minimum sample size
- sustained breach window
- manual acknowledge path

좋은 guardrail은 민감하되 성급하지 않아야 한다.

### 5. profile도 운영 학습을 통해 바뀌어야 한다

가드레일 profile은 한 번 정하고 끝나는 규칙이 아니다.
incident와 false positive 데이터를 보고 조정해야 한다.

즉 rollout guardrail도 policy 제품처럼 versioned되어야 한다.

---

## 실전 시나리오

### 시나리오 1: schema change canary

parse error와 fallback rate가 기준을 넘으면 auto pause하고, consumer matrix와 drift signal을 본 뒤 사람이 재개 여부를 판단한다.

### 시나리오 2: config-only change

retry/timeout 조정은 코드가 안 바뀌어도 위험할 수 있으므로, dedicated config profile과 staged rollout이 필요하다.

### 시나리오 3: low-risk UI text change

모든 heavy guardrail을 태우면 delivery가 느려진다.
lightweight profile로 충분할 수 있다.

---

## 코드로 보기

```yaml
rollout_profile:
  type: schema_change
  service_tier: 3
  auto_pause_if:
    - parse_error_rate > 0
    - unknown_enum_fallback_rate > 0.1%
  manual_resume_requires:
    - owner_ack
    - drift_review
    - mitigation_applied
```

좋은 profile은 멈춤 기준과 재개 기준을 같이 적는다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 guardrail | 운영이 단순하다 | 과소/과잉 통제가 생긴다 | 아주 작은 조직 |
| profile-based guardrail | 현실적이다 | 설계 비용이 든다 | 여러 변경 유형이 있을 때 |
| profile + auto pause + human resume | 안전과 속도의 균형이 좋다 | 운영 discipline이 필요하다 | 성숙한 release 운영 |

rollout guardrail profile의 목적은 복잡성을 늘리는 것이 아니라, **변경의 실제 위험도에 맞는 pause/resume 구조를 주는 것**이다.

---

## 꼬리질문

- 현재 guardrail은 change archetype과 service criticality를 반영하는가?
- auto pause는 되어도 manual resume 기준은 명확한가?
- business signal이 빠진 채 기술 지표만 보고 있지는 않은가?
- false positive와 missed incident를 profile tuning에 반영하고 있는가?

## 한 줄 정리

Rollout guardrail profiles, auto-pause, and manual resume는 변경 유형과 서비스 중요도에 맞는 제어 프로파일을 적용해 배포를 더 안전하고 덜 경직되게 만드는 운영 모델이다.
