# Pricing / Plan Management System 설계

> 한 줄 요약: pricing and plan management system은 상품 플랜, 가격 정책, 변경 이력, grandfathering, 과금 연동을 중앙에서 관리하는 상업 정책 시스템이다.

retrieval-anchor-keywords: pricing, plan management, tier, grandfathering, upgrade downgrade, plan catalog, price book, effective date, billing integration, entitlements, offers

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Billing / Usage Metering System 설계](./billing-usage-metering-system-design.md)
> - [Entitlement / Quota 설계](./entitlement-quota-design.md)
> - [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Multi-tenant SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)

## 핵심 개념

Pricing 시스템은 단순 가격표가 아니다.  
실전에서는 아래를 함께 관리한다.

- plan catalog
- price book
- feature entitlements
- effective date
- upgrade / downgrade
- grandfathering
- promo / discount

즉, pricing은 매출 정책과 제품 정책을 동시에 관리하는 시스템이다.

## 깊이 들어가기

### 1. Plan과 price를 분리한다

플랜은 기능 묶음이고, 가격은 그 플랜의 청구 규칙이다.

- plan: 무엇을 포함하는가
- price: 얼마를, 어떤 기간에 청구하는가

같은 plan이 지역이나 계약 조건에 따라 다른 price를 가질 수 있다.

### 2. Capacity Estimation

예:

- 수천 개 plan / offer
- 수백만 tenant
- 자주 있는 가격 조회와 적은 수정

읽기는 많고 쓰기는 적다.  
그래서 versioned snapshot과 cache가 핵심이다.

봐야 할 숫자:

- plan lookup QPS
- price change rate
- contract override count
- cache hit ratio
- billing sync lag

### 3. 데이터 모델

핵심 엔티티:

- plan
- price
- feature bundle
- entitlement
- promotion
- contract override
- effective window

모든 변경은 effective date를 가져야 한다.

### 4. Grandfathering

기존 고객을 새 가격으로 강제 전환하면 분쟁이 생긴다.

- 기존 플랜 유지
- 신규 가입자만 새 가격 적용
- migrate window 제공

grandfathering 정책이 없으면 pricing 변경이 장애가 된다.

### 5. Coupon / promo

프로모션은 복잡도를 크게 올린다.

- percentage discount
- fixed amount discount
- trial extension
- one-time credit

프로모션은 billing과 연결되므로 audit trail이 필요하다.

### 6. Entitlement integration

가격과 기능은 연결된다.

- 플랜이 바뀌면 entitlement가 바뀜
- quota와 overage도 바뀜
- trial → paid 전환

이 부분은 [Entitlement / Quota 설계](./entitlement-quota-design.md)와 함께 봐야 한다.

### 7. Change governance

가격 변경은 민감하다.

- 승인 워크플로우
- audit log
- rollout schedule
- customer communication

이 부분은 [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)와도 닮아 있다.

## 실전 시나리오

### 시나리오 1: 가격 인상

문제:

- 신규 고객만 새 가격을 적용하고 싶다

해결:

- effective date 분리
- existing contract grandfathering

### 시나리오 2: 플랜 업그레이드

문제:

- 사용자가 중간에 상위 플랜으로 바꾼다

해결:

- billing system과 sync
- entitlement 즉시 반영

### 시나리오 3: 엔터프라이즈 계약

문제:

- 표준 price book과 다른 계약이 필요하다

해결:

- contract override
- tenant-specific pricing

## 코드로 보기

```pseudo
function resolvePrice(tenant, plan, date):
  snapshot = catalog.snapshot(date)
  override = contractOverride(tenant)
  return merge(snapshot.plan(plan), override)
```

```java
public Price resolve(TenantId tenantId, PlanId planId, Instant at) {
    return pricingRepository.resolve(tenantId, planId, at);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Single price book | 단순하다 | 유연성이 낮다 | 작은 제품 |
| Versioned catalog | 변경 관리가 쉽다 | 운영 절차 필요 | 실서비스 |
| Contract overrides | enterprise 대응 가능 | 복잡도 증가 | B2B SaaS |
| Grandfathering | 고객 반발이 적다 | 정책이 늘어난다 | 가격 인상 |
| Entitlement-linked pricing | 제품/과금 일관성 | coupling 증가 | 대부분의 SaaS |

핵심은 pricing이 숫자 계산이 아니라 **상품 정책, 청구, entitlement를 연결하는 운영 시스템**이라는 점이다.

## 꼬리질문

> Q: plan과 price는 왜 분리하나요?
> 의도: 상품 정책과 청구 규칙 구분 확인
> 핵심: 같은 플랜이라도 가격 조건이 달라질 수 있기 때문이다.

> Q: grandfathering은 왜 필요한가요?
> 의도: 기존 고객 보호와 변경 관리 이해 확인
> 핵심: 갑작스러운 가격 변경은 고객 이탈과 분쟁을 만든다.

> Q: entitlement와 pricing의 관계는 무엇인가요?
> 의도: 기능과 가격 연결 이해 확인
> 핵심: 플랜이 바뀌면 허용 기능과 quota도 바뀐다.

> Q: 가격 변경을 안전하게 하려면 무엇이 필요한가요?
> 의도: governance와 audit 이해 확인
> 핵심: effective date, 승인, audit trail이 필요하다.

## 한 줄 정리

Pricing / plan management system은 가격, 플랜, entitlement, 계약 오버라이드를 버전화해 안전하게 운영하는 상업 정책 시스템이다.

