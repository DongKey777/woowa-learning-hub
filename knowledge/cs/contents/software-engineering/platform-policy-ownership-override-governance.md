# Platform Policy Ownership and Override Governance

> 한 줄 요약: platform policy는 규칙 문장 자체보다 누가 소유하고 어떻게 바꾸며 어떤 override를 언제까지 허용하는지가 더 중요하고, 이 lifecycle이 없으면 guardrail은 곧 무시되거나 shadow path로 대체된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Platform Policy Ownership and Override Governance](./README.md#platform-policy-ownership-and-override-governance)
> - [Platform Control Plane and Delegation Boundaries](./platform-control-plane-delegation-boundaries.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Golden Path Escape Hatch Policy](./golden-path-escape-hatch-policy.md)
> - [Architecture Exception Process](./architecture-exception-process.md)
> - [Platform Scorecards](./platform-scorecards.md)
> - [Policy as Code Rollout and Adoption Stages](./policy-as-code-rollout-adoption-stages.md)
> - [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)

> retrieval-anchor-keywords:
> - platform policy ownership
> - policy override
> - override governance
> - guardrail ownership
> - exemption registry
> - override expiry
> - policy lifecycle
> - platform rule owner

## 핵심 개념

플랫폼 정책은 보통 "금지 규칙"으로 보이지만, 실제 운영에서는 다음이 더 중요하다.

- 누가 policy owner인가
- 무엇이 change trigger인가
- override는 어떤 유형이 있는가
- override debt를 어떻게 회수하는가

즉 policy는 static rule set이 아니라 **owner와 override를 가진 제품 자산**이다.

---

## 깊이 들어가기

### 1. policy마다 owner와 objective가 있어야 한다

좋은 policy는 왜 존재하는지 설명할 수 있어야 한다.

예:

- no-direct-db-access: boundary protection
- required-metadata-fields: operability
- staged-rollout-for-high-risk-config: change safety

owner가 없으면 다음 문제가 생긴다.

- policy가 낡아도 아무도 바꾸지 않음
- override가 쌓여도 회수 안 됨
- 예외를 어디서 닫아야 하는지 모름

### 2. override는 예외가 아니라 governance 입력이다

override가 발생했다는 사실은 보통 다음 둘 중 하나다.

- 실제로 정당한 특수 상황이 있다
- policy가 현실과 안 맞는다

그러므로 override는 숨길 대상이 아니라 측정해야 할 신호다.

봐야 할 것:

- override count
- same-policy repeated override
- average override age
- no-expiry override ratio

override debt가 크면 policy quality를 다시 봐야 한다.

### 3. override 유형을 나눠야 한다

모든 override를 같은 수준으로 다루면 운영이 과해지거나 약해진다.

예:

- temporary override: migration, incident, pilot
- scoped override: 특정 서비스/환경만 허용
- permanent carve-out: 규제/물리 제약으로 장기 허용

이 구분이 있어야 expiry, review cadence, compensating control이 달라질 수 있다.

### 4. policy change와 override review는 같은 lifecycle 안에 있어야 한다

새 policy를 만들고 끝내면 안 된다.
주기적으로 다음을 봐야 한다.

- policy adoption
- bypass or shadow path
- override accumulation
- false positive / friction
- incident prevention 효과

즉 policy owner는 규칙 수호자가 아니라 **규칙의 경제성과 적합성을 관리하는 steward**다.

### 5. 플랫폼 정책은 platform-product boundary를 드러낸다

정책은 플랫폼이 도메인 의미까지 가져가면 안 된다.

좋은 기준:

- platform policy: minimum safety, metadata, rollout guardrail
- product/local policy: business threshold, customer semantics, domain fallback

이 경계가 흐리면 override가 폭증하거나, 제품 팀이 shadow path를 만든다.

---

## 실전 시나리오

### 시나리오 1: 특정 policy에 override가 반복된다

이건 해당 팀이 말을 안 듣는 문제가 아니라, rule scope가 과하거나 paved road가 현실을 못 따라가는 신호일 수 있다.

### 시나리오 2: migration 때문에 override가 많다

temporary override를 time-boxed로 허용하되, migration wave exit criteria와 함께 닫아야 한다.

### 시나리오 3: policy owner가 바뀌었다

owner handoff가 없으면 override registry와 expiry가 금방 방치된다.
policy도 서비스처럼 ownership handoff가 필요하다.

---

## 코드로 보기

```yaml
platform_policy:
  id: staged_rollout_for_high_risk_change
  owner: platform-governance
  objective: change_safety
  override_types:
    - temporary
    - scoped
  review_every: monthly
  metrics:
    - override_count
    - override_average_age
```

좋은 policy record는 rule text만이 아니라 owner와 review loop를 포함한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| owner 없는 policy | 만들기 쉽다 | 금방 낡는다 | 거의 없음 |
| strict no-override policy | 단순하다 | shadow path가 생긴다 | 매우 드문 규제 상황 |
| owned policy + governed override | 현실적이다 | 운영 discipline이 필요하다 | 성장 조직 |

platform policy ownership and override governance의 목적은 예외를 없애는 것이 아니라, **override를 통해 policy 자체를 더 현실적이고 강한 guardrail로 만드는 것**이다.

---

## 꼬리질문

- 이 policy의 owner와 objective는 명확한가?
- override가 반복된다면 팀 문제가 아니라 policy 문제가 아닌가?
- override expiry와 review cadence가 실제로 관리되는가?
- platform이 business semantics까지 정책으로 잡고 있지는 않은가?

## 한 줄 정리

Platform policy ownership and override governance는 플랫폼 규칙을 owner와 lifecycle과 override debt까지 포함한 제품 자산으로 관리해 guardrail이 현실과 함께 진화하게 만드는 구조다.
