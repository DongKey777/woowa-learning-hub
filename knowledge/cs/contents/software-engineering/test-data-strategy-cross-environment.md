# Test Data Strategy Across Environments

> 한 줄 요약: 테스트 데이터 전략은 "샘플을 넣는 일"이 아니라, local, CI, staging, production의 목적이 다를 때 어떤 데이터가 어디까지 진실이어야 하는지 설계하는 문제다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Schema Contract Evolution Across Services](./schema-contract-evolution-cross-service.md)
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)

> retrieval-anchor-keywords:
> - test data strategy
> - environment parity
> - production-like data
> - synthetic data
> - anonymization
> - fixtures
> - seed data
> - data drift

## 핵심 개념

테스트 데이터는 환경마다 역할이 다르다.

- local: 개발자가 빠르게 실험할 수 있어야 한다
- CI: 반복 가능하고 가볍고 결정적이어야 한다
- staging: 운영과 유사한 흐름을 검증해야 한다
- production: 실제 사용자 데이터와 운영 진실이 살아 있다

문제는 이 네 환경을 같은 방식으로 다루면 안 된다는 것이다.
테스트 데이터 전략은 각 환경의 목적에 맞게 **진실의 수준을 다르게 설계**하는 일이다.

---

## 깊이 들어가기

### 1. 환경마다 필요한 진실이 다르다

모든 환경이 production-like일 필요는 없다.

| 환경 | 목표 | 데이터 특성 |
|---|---|---|
| local | 빠른 반복 | 작고 단순함 |
| CI | 결정성 | 고정된 fixture |
| staging | 경로 검증 | 운영 유사 샘플 |
| production | 실제 운영 | 민감 정보 포함 가능 |

핵심은 "가짜냐 진짜냐"가 아니라 **무엇을 검증하려는가**다.

### 2. synthetic data는 유용하지만 분포를 맞춰야 한다

합성 데이터는 개인정보를 피하면서도 테스트를 가능하게 한다.
하지만 값 자체보다 **분포와 조합**이 중요하다.

예:

- 결제 성공/실패 비율
- 주문 상태 전이 패턴
- null/optional 필드 조합
- 지역/언어/권한 조합

합성 데이터가 너무 평평하면 실제 장애를 못 잡는다.

### 3. production data는 복제보다 비식별화가 중요하다

운영 데이터를 테스트 환경으로 가져올 때는 다음이 필수다.

- 마스킹
- 익명화
- 최소 보존
- 접근 통제
- 보관 기간 제한

그렇지 않으면 테스트가 아니라 보안 리스크가 된다.

### 4. fixture는 작게, 시나리오는 따로

fixture를 크게 만들면 유지보수가 어려워진다.
좋은 방식은:

- 공통 seed는 최소화
- 시나리오별 builder 사용
- edge case 전용 fixture 분리
- 재사용보다 가독성 우선

즉 fixture는 진실의 압축본이어야지, 데이터 덤프가 아니어야 한다.

### 5. 데이터 drift를 감시해야 한다

환경 간 데이터가 오래 갈수록 구조와 의미가 어긋난다.

예:

- staging에는 더 이상 존재하지 않는 상태값이 남아 있음
- CI fixture가 새 필드를 반영하지 못함
- local seed가 최신 계약과 다름

이런 drift는 테스트 실패가 아니라, **환경 신뢰도 하락**의 신호다.

---

## 실전 시나리오

### 시나리오 1: CI는 빠르지만 staging만 자꾸 깨진다

원인은 fixture가 아니라 production-like 조합을 못 담는 데 있을 수 있다.
이 경우 staging seed와 contract test를 다시 설계해야 한다.

### 시나리오 2: 테스트는 통과하는데 운영에서만 깨진다

실제 데이터 분포와 edge case가 fixture에 반영되지 않은 것이다.
합성 데이터의 분포와 null 조합을 다시 맞춰야 한다.

### 시나리오 3: 개인정보 때문에 데이터를 못 쓴다

이 경우 raw copy보다 anonymized snapshot과 synthetic augmentation을 함께 쓰는 편이 낫다.

---

## 코드로 보기

```java
public class TestDataFactory {
    public static OrderScenario pendingPayment() {
        return new OrderScenario("PENDING", true, "KR", null);
    }

    public static OrderScenario paidWithShipping() {
        return new OrderScenario("PAID", false, "KR", "SHIPPED");
    }
}
```

중요한 건 값의 수가 아니라, 의미 있는 상태 조합을 재현할 수 있느냐이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 작은 고정 fixture | 빠르다 | 현실성이 낮다 | CI |
| production-like snapshot | 경로 검증이 좋다 | 비식별화 비용이 든다 | staging |
| synthetic generation | 유연하다 | 분포 왜곡이 쉽다 | 대규모 시나리오 |

데이터 전략의 핵심은 "많이"가 아니라 **환경 목적과 맞는 신뢰도**다.

---

## 꼬리질문

- 각 환경에서 어떤 진실이 꼭 필요하며 무엇은 버려도 되는가?
- fixture와 실제 운영 데이터의 차이를 어떻게 감시할 것인가?
- 비식별화와 재현성 사이 균형은 어떻게 잡을 것인가?
- staging 실패가 실제 배포 실패를 얼마나 잘 예측하는가?

## 한 줄 정리

테스트 데이터 전략은 환경별 목적에 맞게 진실의 수준과 분포를 다르게 설계해, 재현성과 안전성을 동시에 확보하는 일이다.
