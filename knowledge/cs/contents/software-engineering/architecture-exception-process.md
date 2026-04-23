# Architecture Exception Process

> 한 줄 요약: architecture exception process는 원칙을 무시하는 허가가 아니라, 왜 원칙을 못 지키는지 기록하고 기간과 보상을 붙여 관리하는 절차다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Architecture Review Anti-Patterns](./architecture-review-anti-patterns.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [Golden Path Escape Hatch Policy](./golden-path-escape-hatch-policy.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Decision Revalidation and Supersession Lifecycle](./decision-revalidation-supersession-lifecycle.md)

> retrieval-anchor-keywords:
> - architecture exception
> - waiver
> - exception process
> - policy override
> - compensating control
> - expiry date
> - review date
> - deviation approval

## 핵심 개념

아키텍처 원칙은 모두에게 동일하게 적용하고 싶지만, 현실에는 예외가 생긴다.

architecture exception process는 그 예외를 문서화, 승인, 추적, 만료시키는 절차다.

즉 예외는 "허용"이 아니라 **관리 대상**이다.

---

## 깊이 들어가기

### 1. 예외는 구체적이어야 한다

좋은 예외에는 다음이 있어야 한다.

- 왜 필요한가
- 어떤 원칙을 어기는가
- 얼마나 오래 필요한가
- compensating control은 무엇인가
- 누가 승인하는가

### 2. 예외는 원칙보다 강하면 안 된다

예외가 많아지면 원칙이 사라진다.

그래서 예외는:

- 숫자로 추적
- 기간으로 제한
- 정기 재검토

해야 한다.

### 3. exception process는 ADR과 연결되어야 한다

예외가 허용된 이유와 대안 비교는 ADR에 남겨야 한다.

이 문맥은 [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)와 연결된다.
예외가 반복 연장된다면 decision 자체의 재검토 trigger로 봐야 한다.

### 4. compensating control이 필요하다

원칙을 완전히 못 지키는 경우, 다른 통제를 둬야 한다.

예:

- 추가 모니터링
- short TTL
- manual approval
- limited scope

### 5. 예외는 ownership과 함께 가야 한다

누가 이 예외를 유지하고 닫는지 명확해야 한다.

---

## 실전 시나리오

### 시나리오 1: 특수한 배포 방식이 필요하다

기본 배포 정책을 못 쓰는 경우, 예외로 승인하고 만료일을 붙인다.

### 시나리오 2: 외부 규제 때문에 아키텍처 원칙을 어긴다

보상 통제와 문서화를 함께 둬야 한다.

### 시나리오 3: 예외가 계속 연장된다

예외는 다시 검토하고, 원칙을 고치거나 대체 경로를 마련해야 한다.

---

## 코드로 보기

```yaml
exception_request:
  rule: no-direct-db-access
  reason: legacy_reporting
  expiry: 2026-06-30
  compensating_control: extra_review
```

예외는 명시적이어야 하고, 끝이 보여야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 암묵적 예외 | 빠르다 | 추적이 안 된다 | 거의 없음 |
| 수동 예외 프로세스 | 유연하다 | 누락이 생길 수 있다 | 작은 팀 |
| workflow 기반 예외 | 통제력이 높다 | 운영이 필요하다 | 성숙한 조직 |

architecture exception process는 원칙을 깨는 면허가 아니라, **원칙 예외를 통제하는 절차**다.

---

## 꼬리질문

- 어떤 예외는 받아들이고 어떤 예외는 거절할 것인가?
- 예외 만료를 어떻게 강제할 것인가?
- compensating control은 충분한가?
- 예외 누적을 어떻게 측정할 것인가?

## 한 줄 정리

Architecture exception process는 아키텍처 원칙 위반을 허가하는 것이 아니라, 기간과 보상 통제를 붙여 예외를 안전하게 운영하는 절차다.
