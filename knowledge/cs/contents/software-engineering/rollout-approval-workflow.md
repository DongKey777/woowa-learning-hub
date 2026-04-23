# Rollout Approval Workflow

> 한 줄 요약: rollout approval workflow는 배포를 승인하는 절차가 아니라, 위험, 관측성, rollback, ownership, communication을 함께 검토해 언제 풀지 결정하는 운영 흐름이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Release Policy, Change Freeze, and Error Budget Coupling](./release-policy-change-freeze-error-budget-coupling.md)
> - [Production Readiness Review](./production-readiness-review.md)
> - [Backward Compatibility Test Gates](./backward-compatibility-test-gates.md)
> - [Golden Path Escape Hatch Policy](./golden-path-escape-hatch-policy.md)
> - [Contract Drift Detection and Rollout Governance](./contract-drift-detection-rollout-governance.md)
> - [Operational Readiness Drills and Change Safety](./operational-readiness-drills-and-change-safety.md)
> - [Rollout Guardrail Profiles, Auto-Pause, and Manual Resume](./rollout-guardrail-profiles-auto-pause-resume.md)

> retrieval-anchor-keywords:
> - rollout approval
> - release approval workflow
> - canary gate
> - rollout checklist
> - approval chain
> - launch approval
> - risk review
> - rollout governance
> - rollout pause
> - drift approval gate
> - risk tier
> - change safety

## 핵심 개념

rollout approval workflow는 "배포해도 되냐"를 묻는 절차가 아니다.
정확히는 "어떤 조건에서 얼마나 안전하게 풀 수 있는가"를 묻는 절차다.

검토 항목:

- change size
- blast radius
- contract compatibility
- observability readiness
- rollback plan
- owner/on-call readiness
- customer communication
- risk tier and drill evidence

즉 approval workflow는 **배포를 통제하는 운영 게이트**다.

---

## 깊이 들어가기

### 1. approval은 사람 한 명이 하는 승인이 아니다

역할이 나뉘어야 한다.

- 기술 승인
- 운영 승인
- 위험 승인
- 필요 시 제품/비즈니스 승인

### 2. approval workflow는 단계형이어야 한다

예:

1. 자동 gate 통과
2. owner review
3. PRR 확인
4. risk tier 확인
5. canary 승인
6. full rollout 승인

### 3. 긴급 배포와 일반 배포를 구분해야 한다

hotfix나 kill switch 관련 변경은 별도 경로가 필요하다.

### 4. approval은 scorecard와 연결되어야 한다

scorecard가 있으면 승인 판단이 쉬워진다.

이 문맥은 [Migration Scorecards](./migration-scorecards.md)와도 연결된다.

### 5. approval workflow는 과하면 병목이 된다

너무 많은 승인 단계는 배포를 늦춘다.

그래서 자동화 가능한 것은 policy as code로 먼저 넘겨야 한다.

---

## 실전 시나리오

### 시나리오 1: 새 기능을 일부 사용자에게만 푼다

owner와 운영이 함께 canary gate를 본 뒤 승인한다.

### 시나리오 2: 중요한 변경이지만 rollback이 어렵다

PRR과 compatibility gate가 통과해야 한다.

### 시나리오 3: 긴급 수정이 들어왔다

긴급 경로로 승인하되, 사후 리뷰를 남긴다.

---

## 코드로 보기

```yaml
rollout_approval:
  gates:
    - contract_check
    - prr_complete
    - rollback_verified
  approvers:
    - service_owner
    - oncall
```

approval workflow는 배포를 늦추는 절차가 아니라, **위험을 통제된 상태로 풀기 위한 흐름**이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 수동 승인 | 유연하다 | 느리다 | 고위험 변경 |
| 자동 승인 | 빠르다 | 신호를 놓칠 수 있다 | low-risk 변경 |
| hybrid approval | 균형이 좋다 | 설계가 필요하다 | 성숙한 조직 |

rollout approval workflow는 배포 권한 관리가 아니라 **리스크 기반 출시 관리**다.

---

## 꼬리질문

- 어떤 gate는 자동이고 어떤 gate는 사람이 승인하는가?
- 긴급 배포 경로는 어떻게 분리할 것인가?
- 승인 기준은 scorecard와 연결되는가?
- 승인 후 실제 rollout 결과를 어떻게 학습할 것인가?

## 한 줄 정리

Rollout approval workflow는 배포를 허용하는 절차가 아니라, 위험과 readiness를 함께 확인해 안전하게 풀어주는 운영 게이트다.
