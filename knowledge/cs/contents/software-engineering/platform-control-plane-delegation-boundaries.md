# Platform Control Plane and Delegation Boundaries

> 한 줄 요약: platform control plane은 팀을 중앙에서 통제하는 장치가 아니라, 배포·정책·서비스 생성·설정 변경 같은 공통 제어 지점을 안전하게 제공하되 도메인 판단은 로컬 팀에 남기는 delegation boundary 설계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Platform Control Plane and Delegation Boundaries](./README.md#platform-control-plane-and-delegation-boundaries)
> - [Platform Paved Road Trade-offs](./platform-paved-road-tradeoffs.md)
> - [Golden Path Escape Hatch Policy](./golden-path-escape-hatch-policy.md)
> - [Configuration Governance and Runtime Safety](./configuration-governance-runtime-safety.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)

> retrieval-anchor-keywords:
> - platform control plane
> - delegated autonomy
> - guardrail platform
> - control boundary
> - policy delegation
> - self-service control
> - platform authority
> - local autonomy
> - policy override
> - policy owner

## 핵심 개념

플랫폼이 성숙해질수록 공통 제어 지점이 생긴다.

예:

- 서비스 생성
- 배포 승인 흐름
- 설정 변경 경로
- policy enforcement
- ownership metadata registration

이걸 한데 묶어 보면 platform control plane이라고 볼 수 있다.
중요한 것은 control plane이 **도메인 결정을 대체하면 안 된다**는 점이다.

즉 플랫폼은 "어떻게 안전하게 움직일지"를 제공하고,
제품 팀은 "무엇을 왜 움직일지"를 결정해야 한다.

---

## 깊이 들어가기

### 1. control plane과 execution plane을 구분해야 한다

control plane은 규칙과 권한과 정책을 관리한다.
execution plane은 실제 서비스가 사용자 요청을 처리하는 곳이다.

예:

- control plane: deploy gate, config validation, service catalog update
- execution plane: checkout request 처리, 결제 승인, 추천 계산

이 둘이 섞이면 플랫폼이 비즈니스 로직까지 빨아들이거나, 반대로 각 팀이 제어 규칙을 제멋대로 구현하게 된다.

### 2. 좋은 플랫폼 control은 delegation boundary를 명확히 가진다

플랫폼이 정할 것:

- 공통 필수 metadata
- 최소 observability
- 위험한 config validation
- rollout guardrail

도메인 팀이 정할 것:

- feature semantics
- business thresholds
- customer communication timing
- local fallback policy의 세부 값

즉 control plane은 강한 중앙 통제가 아니라 **강한 공통 안전장치 + 제한된 로컬 자율성**의 구조다.

### 3. over-control은 shadow control plane을 만든다

플랫폼이 너무 많은 결정을 중앙화하면 팀은 우회 경로를 만든다.

예:

- 별도 CI/CD
- 로컬 config 저장소
- 비공식 service registry
- 직접 만든 rollout 스크립트

이런 shadow control plane이 늘어나면 정책은 약해지고 사고 surface는 커진다.

### 4. control plane 자체도 high criticality system이다

설정, 배포, kill switch, 서비스 생성이 한 control plane에 묶이면 그 시스템 자체가 매우 중요해진다.

필요한 것:

- auditability
- break-glass path
- degraded mode
- scoped blast radius
- strong ownership

control plane이 죽으면 제품 서비스보다 더 넓게 마비될 수 있다.

### 5. delegation은 책임 회피가 아니라 contract다

플랫폼이 "각 팀이 알아서 하세요"라고 하면 delegation이 아니라 abandonment다.
좋은 delegation에는 contract가 있다.

예:

- 어떤 필드는 반드시 등록
- 어떤 risk tier는 중앙 approval 필요
- 어떤 override는 expiry 필요
- 어떤 지표는 팀이 책임지고 본다

즉 delegation boundary는 **위임과 책임의 계약면**이다.

---

## 실전 시나리오

### 시나리오 1: 서비스 bootstrap을 중앙화한다

플랫폼은 owner metadata, 기본 observability, 배포 경로를 강제한다.
하지만 서비스의 비즈니스 단계와 rollout 메시지는 제품 팀이 정해야 한다.

### 시나리오 2: 위험한 config를 동적 변경한다

플랫폼 control plane은 validation, audit, staged rollout을 제공한다.
하지만 어떤 값을 선택할지는 도메인 owner가 운영 맥락으로 판단한다.

### 시나리오 3: 플랫폼이 너무 강해서 우회가 늘어난다

이 경우 정책을 더 세게 걸기 전에, control plane이 너무 많은 도메인 결정을 흡수했는지 봐야 한다.

---

## 코드로 보기

```yaml
platform_control_plane:
  platform_owned:
    - metadata_schema
    - policy_gate
    - rollout_guardrail
    - config_validation
  domain_owned:
    - feature_semantics
    - customer_message
    - local_threshold_tuning
  override_policy:
    expiry_required: true
```

좋은 control plane은 중앙 권한과 로컬 판단의 경계를 명확히 적는다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 약한 control plane | 자율성이 높다 | 일관성과 안전성이 약하다 | 작은 조직 |
| 강한 중앙 control | 표준화가 쉽다 | shadow path가 생긴다 | 초기 표준화 단계 |
| delegated control plane | 균형이 좋다 | 경계 설계가 필요하다 | 성장 조직 |

platform control plane의 핵심은 명령 체계가 아니라, **공통 위험은 중앙에서 줄이고 도메인 의미는 현장에 남기는 것**이다.

---

## 꼬리질문

- 플랫폼이 지금 도메인 판단까지 흡수하고 있지는 않은가?
- local override가 필요한 경우 어떤 contract와 expiry를 붙일 것인가?
- control plane 자체의 blast radius는 어떻게 제한하는가?
- shadow control plane이 늘어난다면 기준이 과한 것인가, 경험이 나쁜 것인가?

## 한 줄 정리

Platform control plane and delegation boundaries는 공통 제어와 로컬 자율성을 어디서 나눌지 설계해, 플랫폼이 안전장치는 강하게 제공하되 도메인 의미까지 중앙집중하지 않게 만드는 구조다.
