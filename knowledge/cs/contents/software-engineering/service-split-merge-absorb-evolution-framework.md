# Service Split, Merge, and Absorb Evolution Framework

> 한 줄 요약: 서비스 evolution은 항상 split만이 답이 아니며, cognitive load, ownership, dependency shape, economics를 보고 split, merge, absorb, retire 중 어떤 경로가 맞는지 판단하는 프레임이 필요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Team Cognitive Load and Boundary Design](./team-cognitive-load-boundary-design.md)
> - [Service Portfolio Lifecycle Governance](./service-portfolio-lifecycle-governance.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)
> - [Brownfield Modularization Strategy](./brownfield-modularization-strategy.md)
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)

> retrieval-anchor-keywords:
> - service split
> - service merge
> - absorb service
> - service consolidation
> - boundary evolution
> - reverse migration
> - service sprawl
> - merge decision

## 핵심 개념

서비스 경계는 한번 정하면 끝나는 것이 아니다.
시간이 지나면 어떤 경계는 더 쪼개야 하고, 어떤 경계는 다시 합쳐야 하며, 어떤 기능은 플랫폼에 흡수되는 편이 낫다.

가능한 evolution path 예:

- split: 한 서비스에서 책임 분리
- merge: 두 서비스의 경계를 다시 합침
- absorb: 플랫폼/상위 경로로 흡수
- retire: 가치가 줄어 없앰

즉 service evolution은 구조 미학이 아니라 **경계를 계속 재조정하는 운영 활동**이다.

---

## 깊이 들어가기

### 1. split 신호와 merge 신호는 다르다

split이 맞는 경우:

- 서로 다른 change cadence
- 다른 owner or on-call boundary 필요
- contract volatility가 너무 높음
- domain invariants가 충돌함

merge가 맞는 경우:

- 항상 함께 배포됨
- independent operation 이득이 거의 없음
- cognitive load보다 coordination cost가 더 큼
- network and contract overhead만 늘어남

즉 microservice count는 목표가 아니라 결과다.

### 2. absorb는 플랫폼과 제품 경계를 다시 그리는 선택이다

어떤 기능은 별도 서비스보다 platform capability로 흡수하는 편이 낫다.

예:

- 공통 auth adapter
- 배포/rollout control 기능
- metadata registration

하지만 도메인 rule까지 플랫폼에 흡수하면 중앙 비대화가 생긴다.
그래서 absorb 결정은 단순 consolidation이 아니라 **capability boundary 재설계**다.

### 3. service sprawl은 종종 merge 또는 retire의 신호다

서비스가 많아지는 것은 자연스럽지만, 다음이 반복되면 경계를 다시 봐야 한다.

- owner가 약함
- low-traffic인데 운영 표면이 큼
- contract만 많고 독립 가치가 적음
- release와 incident에서 항상 묶여 움직임

이때 "이미 쪼갰으니 유지"는 sunk-cost 사고일 수 있다.

### 4. evolution 결정은 socio-technical 문제다

split/merge/absorb 판단은 코드 의존성만 보면 안 된다.

같이 봐야 할 것:

- 팀 구조
- on-call burden
- handoff frequency
- platform capability maturity
- portfolio lifecycle stage

좋은 경계도 팀 구조가 바뀌면 나쁜 경계가 될 수 있다.

### 5. evolution에는 migration path와 cleanup plan이 필요하다

split은 새 contract와 ownership handoff가 필요하고,
merge는 duplicate path cleanup과 service retirement가 필요하다.

즉 구조 변경은 diagram 수정이 아니라 **migration + lifecycle work**다.

---

## 실전 시나리오

### 시나리오 1: 두 개의 작은 서비스가 항상 같이 움직인다

독립 배포도 거의 안 하고 장애도 항상 함께 난다면, merge가 더 낫다.
이 경우 contract overhead와 on-call surface를 줄일 수 있다.

### 시나리오 2: 한 서비스 안에서 두 도메인이 충돌한다

change cadence와 owner가 다르고 rollout risk도 다르다면 split이 맞을 수 있다.

### 시나리오 3: 임시 service가 플랫폼 capability로 변한다

처음엔 별도 실험 서비스였지만 결국 여러 팀이 공통으로 쓰게 된다면, absorb path와 platform ownership reframe이 필요하다.

---

## 코드로 보기

```yaml
service_evolution_review:
  current_state: two_small_services
  signals:
    always_co_deployed: true
    independent_incidents: false
    coordination_cost: high
  decision: merge
  cleanup:
    - retire_duplicate_api
    - unify_oncall
```

좋은 evolution review는 split/merge를 선호도 싸움이 아니라 신호 기반 결정으로 만든다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| split | 독립성이 늘 수 있다 | 운영 표면이 커진다 | 경계와 cadence가 명확히 다를 때 |
| merge | coordination cost를 줄인다 | 내부 복잡도가 늘 수 있다 | 과분할된 경계일 때 |
| absorb | 공통 capability를 단순화한다 | 플랫폼 비대화 위험이 있다 | 공통화 가치가 크고 domain specificity가 낮을 때 |

service split, merge, and absorb evolution framework의 목적은 서비스 수를 늘리거나 줄이는 것이 아니라, **현재 조직과 도메인과 운영 비용에 맞는 경계를 다시 찾는 것**이다.

---

## 꼬리질문

- 이 경계는 독립성보다 coordination cost를 더 키우고 있지 않은가?
- merge 후보 서비스가 사실상 하나처럼 움직이고 있지 않은가?
- absorb하려는 기능이 공통 capability인가, 숨은 도메인 로직인가?
- split/merge 이후 cleanup과 retirement까지 포함한 plan이 있는가?

## 한 줄 정리

Service split, merge, and absorb evolution framework는 서비스 경계를 고정된 진리로 보지 않고, 조직 구조와 도메인 변화와 운영 비용에 맞춰 재구성하는 판단 프레임이다.
