# Platform Paved Road Trade-offs

> 한 줄 요약: platform paved road는 개발 속도를 높이는 기본 경로지만, 모든 팀을 같은 길로 몰아넣으면 유연성과 제품 요구를 잃을 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Technology Radar and Adoption Governance](./technology-radar-adoption-governance.md)
> - [Configuration Governance and Runtime Safety](./configuration-governance-runtime-safety.md)
> - [Platform Control Plane and Delegation Boundaries](./platform-control-plane-delegation-boundaries.md)

> retrieval-anchor-keywords:
> - paved road
> - golden path
> - platform opinionation
> - platform trade-off
> - developer experience
> - standard path
> - self-service platform
> - guardrail

## 핵심 개념

Paved road는 플랫폼 팀이 제공하는 "가장 쉬운 경로"다.

좋은 paved road는:

- 기본 배포
- 기본 관측성
- 기본 인증
- 기본 알림
- 기본 테스트
- 안전한 설정 변경 경로

을 쉽게 만들어준다.

하지만 플랫폼이 너무 의견이 강하면, paved road가 아니라 **강제된 단일 통로**가 된다.

---

## 깊이 들어가기

### 1. paved road의 목적은 표준화가 아니라 생산성이다

표준화는 수단이고, 목적은 팀들이 반복 작업을 덜 하게 하는 것이다.

그래서 paved road는 다음을 제공해야 한다.

- 쉬운 시작
- 안전한 기본값
- 불필요한 선택 감소
- 운영 일관성

### 2. 너무 강한 platform opinionation은 반발을 부른다

플랫폼이 모든 걸 정해버리면 제품 팀은 우회 경로를 찾는다.

그 결과:

- shadow infra가 생김
- 정책 우회가 늘어남
- 플랫폼 신뢰가 떨어짐

즉 paved road는 편의 장치이지, 창의성 억제 장치가 아니다.

### 3. paved road와 guardrail은 다르다

- paved road: 추천되는 기본 경로
- guardrail: 안전을 위한 제약

둘을 구분해야 한다.

예를 들어:

- paved road: 배포 템플릿 제공
- guardrail: 금지된 배포 패턴 차단

### 4. 예외 경로도 설계해야 한다

기본 경로가 있다고 해서 모든 팀이 거기에만 있어야 하는 것은 아니다.

예외가 필요한 경우:

- 레거시 통합
- 특수 규제
- 고성능 요구
- 외부 플랫폼 종속

이런 예외는 문서화하고 리뷰해야 한다.

### 5. paved road는 플랫폼 팀의 제품이다

이 경로도 지속적으로 개선해야 한다.

또한 radar에서 adopt 상태인 기술일수록 paved road에서 가장 쉽게 쓸 수 있어야 한다.

필요한 피드백:

- 채택률
- 우회 경로 비율
- 배포 실패율
- 개발자 만족도

즉 paved road는 "한 번 만들고 끝"이 아니라 **운영되는 제품**이다.

---

## 실전 시나리오

### 시나리오 1: 기본 배포 템플릿을 제공한다

새 서비스는 템플릿만 쓰면 로그, 메트릭, 알림이 자동으로 붙도록 한다.

### 시나리오 2: 특정 팀이 예외 경로를 요구한다

GPU 작업이나 외부 규제 시스템은 기본 경로를 그대로 쓰기 어렵다.
이때는 예외를 승인하고, 왜 필요한지 ADR로 남긴다.

### 시나리오 3: paved road가 우회 경로를 못 막는다

우회 경로가 많아지면 플랫폼 개선이 아니라 정책/경험 문제다.
이 경우 guardrail과 linting을 같이 본다.

---

## 코드로 보기

```yaml
paved_road:
  deploy: standard_pipeline
  observability: default_stack
  auth: shared_module
  exception_process: adr_required
```

기본 경로는 쉬워야 하고, 예외는 명시적이어야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 강한 paved road | 표준화가 쉽다 | 우회가 생긴다 | 반복 작업이 많을 때 |
| 느슨한 paved road | 유연하다 | 일관성이 약해진다 | 제품 요구가 다양할 때 |
| paved road + guardrail | 균형이 좋다 | 설계가 복잡하다 | 성숙한 플랫폼 팀 |

platform paved road는 모든 것을 강제하는 길이 아니라, **대부분의 팀을 안전하게 빠르게 만드는 경로**여야 한다.

---

## 꼬리질문

- 기본 경로는 너무 강제적이지 않은가?
- 우회 경로는 얼마나 허용할 것인가?
- 플랫폼 제품의 채택률을 어떻게 측정할 것인가?
- 예외 승인은 누가 관리할 것인가?

## 한 줄 정리

Platform paved road는 개발자 경험을 높이는 기본 경로이지만, 예외와 guardrail을 함께 설계해야 강제된 단일 통로로 변질되지 않는다.
