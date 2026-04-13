# SLA, SLO Ownership Model

> 한 줄 요약: SLA와 SLO는 숫자만 정하는 것이 아니라, 누구의 책임인지와 어떤 경계에서 관리되는지까지 포함하는 소유권 모델이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [On-Call Ownership Boundaries](./on-call-ownership-boundaries.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Release Policy, Change Freeze, and Error Budget Coupling](./release-policy-change-freeze-error-budget-coupling.md)
> - [Production Readiness Review](./production-readiness-review.md)
> - [Service Maturity Model](./service-maturity-model.md)

> retrieval-anchor-keywords:
> - SLA
> - SLO
> - error budget
> - ownership model
> - service objective
> - reliability target
> - support boundary
> - accountability

## 핵심 개념

SLA/SLO는 운영 지표처럼 보이지만, 실제로는 책임 경계를 드러낸다.

- SLO: 내부 목표, 운영 팀의 약속
- SLA: 외부 또는 조직 간 약속, 위반 시 영향이 있는 계약

즉 숫자보다 중요한 건 **누가 무엇을 책임지는가**다.

---

## 깊이 들어가기

### 1. SLO는 서비스 성숙도의 일부다

성숙한 서비스는 단순 기능이 아니라 reliability target을 가진다.

### 2. ownership boundary와 맞춰야 한다

한 SLO를 여러 팀이 나눠 책임지면 아무도 최종 책임을 지지 않는다.

좋은 기준:

- 하나의 SLO는 하나의 service owner
- 하위 의존성은 supporting owner
- 플랫폼 공통 문제는 platform owner

### 3. SLA는 외부 약속이므로 더 보수적이어야 한다

SLO는 내부 개선 목표로 쓸 수 있지만, SLA는 고객 영향이 있다.

그래서:

- SLO는 운영 변경에 따라 조정 가능
- SLA는 계약과 커뮤니케이션이 필요

### 4. error budget은 release policy와 연결된다

이 문맥은 [Release Policy, Change Freeze, and Error Budget Coupling](./release-policy-change-freeze-error-budget-coupling.md)와 연결된다.

### 5. review와 PRR에서 함께 봐야 한다

새 서비스나 큰 변경을 론칭할 때, SLO가 없는 상태로 나가면 운영 책임이 흐려진다.

---

## 실전 시나리오

### 시나리오 1: 주문 서비스 SLO를 정한다

latency, availability, error rate를 owner와 함께 묶는다.

### 시나리오 2: 플랫폼 서비스와 제품 서비스가 섞여 있다

SLO 책임 경계를 나눠야 한다.

### 시나리오 3: SLA 위반이 반복된다

기능 개선보다 capacity, rollback, alerting을 먼저 봐야 한다.

---

## 코드로 보기

```yaml
slo:
  owner: commerce-team
  availability: 99.9
  latency_p95_ms: 300
  error_budget_policy: freeze_on_burn
```

SLO는 숫자만이 아니라 ownership과 policy를 같이 가져야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| SLO 없음 | 단순하다 | 책임이 흐린다 | 초기 |
| 서비스별 SLO | 명확하다 | 관리가 필요하다 | 운영 서비스 |
| SLO + error budget policy | 강력하다 | 정책이 복잡하다 | 성숙한 조직 |

SLA/SLO ownership model은 reliability 숫자를 누가 책임지는지 명확히 하는 경계 설계다.

---

## 꼬리질문

- SLO는 누구의 책임인가?
- SLA와 SLO를 어떻게 분리할 것인가?
- error budget 소진 시 누가 release를 멈추는가?
- 하위 의존성 문제를 어떻게 반영할 것인가?

## 한 줄 정리

SLA/SLO ownership model은 reliability 목표를 서비스 책임과 연결해, 어떤 팀이 어떤 수준의 안정성을 보장하는지 명확히 하는 구조다.
