---
schema_version: 3
title: Team Cognitive Load and Boundary Design
concept_id: software-engineering/team-cognitive-load-boundary-design
canonical: false
category: software-engineering
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- cognitive-load-boundary-fit
- team-topology-boundary-review
- service-sprawl-coordination-cost
aliases:
- team cognitive load
- cognitive load boundary design
- ownership load
- service sprawl
- collaboration load
- boundary fitness
- team topology boundary
- 운영 부담 기준 경계
- 팀 인지 부하
- 서비스 경계가 무거워요
- handoff 많은 구조
symptoms:
- 서비스를 나눴는데 오히려 팀이 알아야 할 것과 협업 상대가 너무 많아졌어요
- 같은 변경마다 여러 팀 승인이 필요해서 경계가 맞는지 의심돼요
- 플랫폼이 복잡도를 줄여 주는 건지 다른 방식으로 부담을 늘리는 건지 판단이 안 돼요
intents:
- deep_dive
prerequisites:
- software-engineering/organizational-coupling-conway-effects
- software-engineering/service-ownership-catalog-boundaries
- software-engineering/domain-capability-heatmap
next_docs:
- software-engineering/service-split-merge-absorb-evolution-framework
- software-engineering/brownfield-strangler-org-model
- software-engineering/architectural-governance-operating-model
linked_paths:
- contents/software-engineering/organizational-coupling-conway-effects.md
- contents/software-engineering/platform-team-product-team-capability-boundaries.md
- contents/software-engineering/service-ownership-catalog-boundaries.md
- contents/software-engineering/domain-capability-heatmap.md
- contents/software-engineering/brownfield-strangler-org-model.md
- contents/software-engineering/architectural-governance-operating-model.md
- contents/software-engineering/service-split-merge-absorb-evolution-framework.md
confusable_with:
- software-engineering/organizational-coupling-conway-effects
- software-engineering/platform-team-product-team-capability-boundaries
- software-engineering/service-split-merge-absorb-evolution-framework
forbidden_neighbors: []
expected_queries:
- 팀 인지 부하 관점에서 서비스 경계를 다시 봐야 한다는 말은 정확히 뭘 측정하라는 거야?
- 마이크로서비스를 늘렸는데 협업 비용만 커진 상황을 cognitive load로 어떻게 설명해?
- 서비스 수보다 handoff와 승인 체인이 더 중요하다는 말을 사례로 이해하고 싶어
- 플랫폼 팀이 복잡도를 줄여 주는지 오히려 경계를 더 무겁게 만드는지 어떻게 구분해?
- 경계 재설계를 시작해야 하는 신호를 팀 운영 관점에서 정리해줘
contextual_chunk_prefix: |
  이 문서는 서비스 경계나 팀 토폴로지를 논의할 때 기술 구조보다 팀의
  cognitive load를 먼저 보자는 deep dive다. 서비스 수는 적은데 승인 체인과
  handoff가 너무 많다, 팀이 알아야 할 API와 운영 범위가 계속 늘어난다,
  플랫폼이 accidental complexity를 줄이는지 새 규칙만 더하는지 헷갈린다
  같은 표현을 경계 품질, coordination cost, ownership load 기준으로
  해석하도록 돕는다.
---
# Team Cognitive Load and Boundary Design

> 한 줄 요약: 좋은 서비스 경계는 기술적으로만 예쁜 구조가 아니라, 해당 팀이 지속적으로 이해하고 운영할 수 있는 cognitive load 안에 들어오도록 설계된 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Organizational Coupling and Conway Effects](./organizational-coupling-conway-effects.md)
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Domain Capability Heatmap](./domain-capability-heatmap.md)
> - [Brownfield Strangler Org Model](./brownfield-strangler-org-model.md)
> - [Architectural Governance Operating Model](./architectural-governance-operating-model.md)
> - [Service Split, Merge, and Absorb Evolution Framework](./service-split-merge-absorb-evolution-framework.md)

> retrieval-anchor-keywords:
> - cognitive load
> - team boundary design
> - team topology
> - ownership load
> - service sprawl
> - operational burden
> - boundary fitness
> - collaboration load

## 핵심 개념

서비스를 잘게 나누거나 책임을 예쁘게 분리했다고 해서 항상 좋은 구조는 아니다.
그 구조를 실제 팀이 이해하고, 변경하고, 운영할 수 있어야 한다.

그래서 boundary design은 기술 경계와 함께 다음도 봐야 한다.

- 팀이 알아야 할 도메인 수
- 운영해야 할 서비스 수
- 승인과 협업이 필요한 상대 수
- 장애 시 동시에 호출해야 하는 팀 수

즉 boundary의 품질은 코드 구조뿐 아니라 **지속 가능한 인지 부하**로 평가해야 한다.

---

## 깊이 들어가기

### 1. intrinsic load와 extraneous load를 구분해야 한다

어떤 복잡도는 도메인 자체에서 온다.
하지만 어떤 복잡도는 경계와 도구와 프로세스가 불필요하게 만든다.

예:

- intrinsic: 정산 규칙 자체의 복잡성
- extraneous: 서비스가 너무 잘게 쪼개져 있어서 알아야 할 API가 많음

좋은 설계는 도메인 복잡도를 없애지 못해도, **불필요한 인지 비용**은 줄여 준다.

### 2. 서비스 수보다 협업 면적이 더 중요하다

한 팀이 10개 서비스를 가져도 내부 일관성이 높으면 감당 가능할 수 있다.
반대로 3개 서비스만 있어도 승인 체인과 외부 의존이 많으면 어렵다.

봐야 할 신호:

- cross-team PR 빈도
- 승인 대기 시간
- 장애 시 호출되는 팀 수
- 소유권 handoff 횟수

즉 load는 repo 수보다 **조정 비용**에 더 크게 좌우된다.

### 3. 플랫폼은 cognitive load를 줄여야 한다

플랫폼 팀의 역할은 제품 팀의 판단을 대신하는 것이 아니라, 우발적인 복잡도를 덜어 주는 것이다.

예:

- 배포 경로 표준화
- 기본 관측성 제공
- catalog와 ownership 자동화
- config validation 제공

좋은 플랫폼은 제품 팀의 도메인 판단 공간을 남겨 두면서 운영 부하를 줄인다.

### 4. boundary는 시간이 지나면 다시 무거워진다

처음에는 적절했던 구조도 다음 때문에 부담이 커질 수 있다.

- 새로운 연동 증가
- 소유권 변경
- 레거시 공존
- hotfix 빈도 증가

그래서 boundary는 한 번 정하고 끝내지 말고, cognitive load 관점으로 다시 측정해야 한다.

### 5. 재설계 신호를 조기에 봐야 한다

다음 신호가 반복되면 경계를 의심해야 한다.

- 같은 변경에 세 팀 이상이 항상 필요함
- on-call이 특정 개인에게 과도하게 몰림
- 서비스 catalog가 실제와 다름
- 팀원이 특정 시스템 전체를 아무도 설명 못 함

이건 개인 역량 문제가 아니라 **경계 설계 문제**일 가능성이 크다.

---

## 실전 시나리오

### 시나리오 1: 한 팀이 12개 서비스를 운영한다

서비스 수 자체보다, 그중 몇 개가 같은 도메인과 도구를 공유하는지가 중요하다.
공통 운영 모델이 없다면 load가 급격히 늘어난다.

### 시나리오 2: 작은 기능 변경에도 세 팀 승인 필요

이 경우 문제는 개발 속도가 아니라 boundary가 협업 비용을 너무 크게 만든 것이다.

### 시나리오 3: 플랫폼이 모든 설계를 강제한다

일부 accidental complexity는 줄지만, 도메인에 맞지 않는 단일 경로를 강제하면 다른 형태의 인지 부하가 생긴다.

---

## 코드로 보기

```yaml
team_boundary_review:
  team: commerce-checkout
  owned_services: 5
  critical_dependencies: 9
  recurring_handoffs_per_release: 4
  oncall_scope: [checkout, payment-adapter, promo-bff]
  action: split_operational_load_before_domain_split
```

좋은 boundary review는 서비스 수보다 실제 조정 비용과 운영 부담을 드러내야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 더 세밀한 분리 | 책임이 또렷해질 수 있다 | 협업 비용이 늘 수 있다 | 경계가 명확하고 팀 역량이 충분할 때 |
| 더 큰 경계 | 이해가 쉬울 수 있다 | 내부 복잡도가 커질 수 있다 | 서비스 수가 과하게 늘었을 때 |
| platform + boundary review | 지속적으로 균형을 잡는다 | 측정과 조율이 필요하다 | 성장 조직 |

team cognitive load 관점은 "서비스를 몇 개로 나눌까"보다, **이 구조를 팀이 지속적으로 소화할 수 있는가**를 먼저 묻는다.

---

## 꼬리질문

- 우리 팀의 인지 부하는 도메인 자체 때문인가, 경계 설계 때문인가?
- cross-team handoff가 너무 잦은 변경은 무엇인가?
- 플랫폼이 줄여 줘야 할 accidental complexity는 무엇인가?
- 지금 경계는 팀이 바뀐 뒤에도 여전히 맞는가?

## 한 줄 정리

Team cognitive load and boundary design은 서비스 경계를 기술 미학이 아니라 팀이 지속적으로 이해하고 운영할 수 있는 부담 수준으로 평가해야 한다는 관점이다.
