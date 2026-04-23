# Platform Team, Product Team, and Business Capability Boundaries

> 한 줄 요약: 플랫폼 팀과 제품 팀의 경계는 업무 범위만이 아니라, 어떤 business capability를 공통화하고 어떤 capability를 제품 소유로 둘지 정하는 문제다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [BFF Boundaries and Client-Specific Aggregation](./bff-boundaries-client-specific-aggregation.md)
> - [Platform Control Plane and Delegation Boundaries](./platform-control-plane-delegation-boundaries.md)
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)
> - [Team APIs and Interaction Modes in Architecture](./team-apis-interaction-modes-architecture.md)

> retrieval-anchor-keywords:
> - platform team
> - product team
> - business capability mapping
> - internal platform
> - golden path
> - domain ownership
> - org boundary
> - capability catalog

## 핵심 개념

플랫폼 팀은 "공통 도구를 만드는 팀"으로만 보면 부족하다.
더 정확히는, 여러 제품 팀이 반복하지 않아도 되는 capability를 안전하게 제공하는 팀이다.

반대로 제품 팀은 단순히 기능을 만드는 팀이 아니라, 사용자 가치와 도메인 결정을 책임지는 팀이다.

이 둘의 경계는 조직도보다 **business capability map**에서 더 잘 드러난다.

---

## 깊이 들어가기

### 1. capability mapping은 시스템 경계와 조직 경계를 잇는다

비즈니스 capability는 "조직이 수행해야 하는 핵심 능력"이다.

예:

- 주문 생성
- 결제 승인
- 배송 추적
- 고객 알림
- 정산

이 capability를 기준으로 보면, 어떤 부분은 공통 플랫폼이 맡고 어떤 부분은 제품 팀이 소유해야 하는지 보인다.

### 2. 플랫폼 팀은 골든 패스를 제공해야 한다

플랫폼 팀의 목표는 제품 팀이 반복적으로 겪는 마찰을 줄이는 것이다.
이때 어디까지를 platform control plane이 맡고 어디부터를 제품 판단으로 남길지 경계를 명확히 해야 한다.

예:

- 템플릿과 scaffold
- 공통 인증/권한
- 배포 파이프라인
- observability 기본값
- service catalog 연동

하지만 플랫폼이 모든 것을 흡수하면 제품 팀의 도메인 판단까지 빼앗게 된다.

### 3. 제품 팀이 소유해야 하는 것

제품 팀은 다음을 책임져야 한다.

- 사용자 흐름
- 비즈니스 규칙
- 도메인 모델
- 계약 변화의 우선순위
- 고객 영향 판단

즉 플랫폼이 "움직이기 쉽게" 만들고, 제품이 "무엇을 움직일지" 결정한다.

### 4. boundary가 어긋나면 두 가지 문제가 생긴다

- 플랫폼이 제품 로직을 떠안으면 공통화가 과해진다
- 제품이 플랫폼 책임을 떠안으면 중복과 운영 부채가 커진다

이런 어긋남은 기술보다 조직 의사결정에서 먼저 드러난다.

### 5. capability map은 정적인 문서가 아니다

능력 맵은 다음이 바뀔 때 업데이트해야 한다.

- 조직 개편
- 서비스 분리
- BFF 추가
- ACL 도입
- service ownership 변경

그래서 capability mapping은 ADR, service catalog, on-call 정보와 같이 관리되어야 한다.

---

## 실전 시나리오

### 시나리오 1: 인증 기능은 플랫폼이 맡는다

로그인, 토큰 검증, 공통 권한 체크는 플랫폼이 제공할 수 있다.
하지만 "어떤 권한이 이 제품에 맞는가"는 제품 팀이 결정해야 한다.

### 시나리오 2: 주문 도메인과 배송 도메인이 섞인다

배송 상태를 플랫폼 공통 로직으로 넣기 시작하면, 제품 팀의 도메인 판단이 사라진다.
이때 capability map이 경계를 다시 보여준다.

### 시나리오 3: BFF가 늘어나며 중복이 생긴다

BFF는 제품 팀의 요구를 반영하지만, 인증/관측/라우팅 같은 공통 capability는 플랫폼이 제공해야 한다.
이 구분이 없으면 BFF마다 같은 기능이 복제된다.

---

## 코드로 보기

```yaml
capabilities:
  platform:
    - identity
    - deployment
    - observability
    - service catalog
  product:
    - pricing
    - checkout
    - order_lifecycle
    - customer_notifications
```

이런 맵은 책임 전가가 아니라, 소유 경계를 명확히 하는 데 써야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 플랫폼 최소화 | 제품 팀 자율성이 높다 | 중복이 많아진다 | 조직이 작을 때 |
| 플랫폼 확대 | 반복을 줄인다 | 중앙 집중이 생긴다 | 규모가 커질 때 |
| capability map 기반 분리 | 경계가 명확하다 | 지속 관리가 필요하다 | 여러 팀이 함께 성장할 때 |

경계는 조직의 권한 문제가 아니라, **누가 어떤 capability의 최종 책임자인가**의 문제다.

---

## 꼬리질문

- 어떤 capability는 공통화하고 어떤 capability는 제품 소유로 둘 것인가?
- 플랫폼 팀이 제공하는 golden path는 어디까지여야 하는가?
- capability map은 service catalog와 어떻게 연결되는가?
- 제품 팀이 플랫폼의 경계까지 침범하고 있지는 않은가?

## 한 줄 정리

플랫폼 팀과 제품 팀의 경계는 기능 목록이 아니라 business capability의 소유권을 어떻게 나눌지 정하는 구조적 선택이다.
