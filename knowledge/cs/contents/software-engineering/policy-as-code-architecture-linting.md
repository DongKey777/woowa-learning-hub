# Policy as Code and Architecture Linting

> 한 줄 요약: policy as code는 아키텍처 규칙을 사람의 기억이 아니라 기계가 검증하는 규정으로 바꾸고, architecture linting은 그 규정을 PR과 CI에서 강제하는 방식이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [Runbook, Playbook, Automation Boundaries](./runbook-playbook-automation-boundaries.md)
> - [Architectural Governance Operating Model](./architectural-governance-operating-model.md)
> - [Incident Feedback to Policy and Ownership Closure](./incident-feedback-policy-ownership-closure.md)
> - [Policy as Code Rollout and Adoption Stages](./policy-as-code-rollout-adoption-stages.md)
> - [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)

> retrieval-anchor-keywords:
> - policy as code
> - architecture linting
> - static analysis
> - rule enforcement
> - dependency rule
> - CI gate
> - PR check
> - governance automation
> - policy adoption
> - shadow path
> - override debt

## 핵심 개념

아키텍처 규칙은 문서에만 있으면 쉽게 잊힌다.
policy as code는 이 규칙을 실행 가능한 코드로 만들어, PR과 CI에서 자동으로 확인하게 한다.

예:

- 서비스는 다른 서비스의 내부 패키지를 import하지 않는다
- BFF는 도메인 쓰기 로직을 포함하지 않는다
- deprecated API는 특정 시점 이후 새 소비자를 받지 않는다
- 특정 계층은 DB를 직접 접근하지 않는다

즉 linting은 스타일 검사보다 넓은 의미의 **구조 검증**이다.

---

## 깊이 들어가기

### 1. linting은 문법 검사보다 규칙 집행이다

일반 lint는 코드 스타일을 검사한다.
architecture lint는 설계 규칙을 검사한다.

예:

- import 방향
- 패키지 경계
- 금지된 호출
- 계약 버전 규칙
- 생성자/의존성 주입 정책

### 2. policy는 선언적이어야 유지된다

규칙을 코드에 박아 넣되, 너무 절차적으로 만들면 유지가 어렵다.

좋은 policy는 다음을 만족한다.

- 읽기 쉽다
- 위반 이유가 명확하다
- 예외를 최소화한다
- 새 규칙을 추가하기 쉽다

즉 policy as code는 단순 if문 모음이 아니라 **의도 표현**이어야 한다.

### 3. architecture lint는 레벨별로 나눠야 한다

보통 다음처럼 나눈다.

- fast lint: PR에서 빠르게 검사
- deep lint: CI에서 더 넓게 검사
- scheduled lint: nightly 또는 주기적 전체 점검

이렇게 해야 속도와 커버리지를 같이 잡을 수 있다.

### 4. 예외는 반드시 기록돼야 한다

규칙은 예외가 생길 수 있다.
하지만 예외가 구두로 허용되면 정책은 금방 무너진다.

예외 관리 요소:

- 왜 예외인지
- 누가 승인했는지
- 언제 재검토할지
- 대체 통제가 있는지

이 문맥은 [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)와 연결된다.

### 5. policy as code는 governance의 자동화 버전이다

규칙을 코드로 옮기면 팀이 커져도 일관성을 유지하기 쉽다.

특히 다음에 유용하다.

- 보안 규정
- 배포 정책
- 계약 호환성
- 서비스 경계
- 온콜 운영 기준

---

## 실전 시나리오

### 시나리오 1: 모듈 간 직접 참조를 막는다

모듈러 모놀리스에서 다른 모듈의 내부 패키지를 import하면 CI가 실패한다.

### 시나리오 2: BFF가 도메인 쓰기를 넣는다

BFF가 write path를 포함하면 정책 위반으로 잡아야 한다.

### 시나리오 3: deprecated API를 새로 사용한다

새 코드에서 deprecated endpoint를 사용하면 PR 단계에서 경고 또는 실패를 낸다.

---

## 코드로 보기

```yaml
rules:
  - id: no-internal-module-import
    scope: backend
    when: import
    forbid: "..internal.."
  - id: bff-read-only
    scope: bff
    forbid: write_service_calls
```

정책은 문서가 아니라 **검사 가능한 계약**이어야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 문서 기반 규칙 | 쉽다 | 지켜지기 어렵다 | 초반 |
| policy as code | 강제력 있다 | 초기 비용이 든다 | 경계가 중요한 팀 |
| layered linting | 속도와 깊이를 같이 잡는다 | 운영이 복잡하다 | 대규모 조직 |

architecture linting은 개발자 경험을 해치기 위한 장치가 아니라, **경계가 무너지는 속도를 늦추는 안전장치**다.

---

## 꼬리질문

- 어떤 규칙은 PR에서, 어떤 규칙은 nightly에서 검사할 것인가?
- 예외 승인은 어떻게 기록할 것인가?
- lint 위반과 실제 장애의 연결을 측정할 수 있는가?
- policy가 너무 많아 생산성을 해치지는 않는가?

## 한 줄 정리

Policy as code와 architecture linting은 아키텍처 원칙을 CI에서 강제해, 사람의 기억에 의존하지 않고 경계 붕괴를 막는 방법이다.
