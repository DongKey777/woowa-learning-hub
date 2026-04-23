# Policy Object Pattern: 도메인 결정을 객체로 만든다

> 한 줄 요약: Policy Object 패턴은 "무엇을 할지"보다 "어떤 규칙으로 판단할지"를 객체로 분리해, 복잡한 비즈니스 결정을 명시적으로 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [전략 패턴](./strategy-pattern.md)
> - [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)
> - [Specification Pattern](./specification-pattern.md)
> - [Specification vs Query Service Boundary](./specification-vs-query-service-boundary.md)
> - [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)
> - [Domain Service vs Pattern Abuse](./domain-service-vs-pattern-abuse.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Policy Object는 도메인 규칙을 담은 객체다.  
전략과 비슷하지만, 더 자주 **판단/결정/허용 여부**를 표현한다.

backend에서 정책 객체가 잘 맞는 곳은 다음과 같다.

- 환불 가능 여부
- 배송비 부과 기준
- 회원 혜택 적용 기준
- 주문 취소 수수료 계산

### Retrieval Anchors

- `policy object pattern`
- `business rule object`
- `decision object`
- `refund policy`
- `pricing policy`
- `policy object vs strategy`
- `policy object vs state`
- `policy object vs specification`
- `boolean specification`
- `rich decision result`
- `decision result object`
- `rule evaluation object`

---

## 깊이 들어가기

### 1. 전략과 정책은 비슷하지만 초점이 다르다

전략은 알고리즘 교체에, 정책은 규칙 판단에 더 가깝다.

| 구분 | 전략 패턴 | Policy Object |
|---|---|---|
| 초점 | 행동 방식 | 규칙과 판정 |
| 반환 | 계산 결과 또는 동작 | 허용/거절/등급/금액 |
| 대표 예 | 결제 수단, 정렬 방식 | 환불 규정, 취소 수수료 |

### 2. 정책은 도메인 언어를 드러낸다

`if (days < 7 && paid && !shipped)` 같은 코드는 조건식일 뿐이다.  
`RefundPolicy.canRefund(order)`는 도메인 언어다.

### 3. 정책 객체는 테스트 단위가 좋다

정책은 입력과 기대 결과가 분명해서 테스트하기 쉽다.

- 특정 등급이면 할인 가능
- 특정 기간이 지나면 환불 불가
- 특정 배송 단계면 취소 수수료 부과

### 4. Policy Object와 Specification은 반환 책임이 다르다

둘 다 "규칙 평가 객체"처럼 보이지만, 실제로는 다른 질문에 답한다.

| 구분 | Specification | Policy Object |
|---|---|---|
| 핵심 질문 | 이 조건을 만족하는가 | 어떤 결정을 내려야 하는가 |
| 반환 | `boolean` | decision/result object |
| 강점 | `AND`/`OR`/`NOT` 조합, 검색/필터/guard | 허용 여부 + 이유 + 금액 + 후속 액션 |
| 호출자 부담 | 통과/실패 이후 해석을 다시 조립해야 한다 | 결과를 그대로 소비하면 된다 |
| 대표 예 | 환불 대상자인가 | 환불 가능 여부와 수수료는 얼마인가 |

`RefundEligibleSpecification`이 `true`를 돌려줘도 수수료, 거절 사유, 안내 문구는 아직 없다.  
그 정보를 호출자가 다시 계산해야 한다면, 규칙은 결국 다른 곳으로 다시 흩어진다.

---

## 실전 시나리오

### 시나리오 1: 환불 정책

결제 수단, 배송 상태, 주문 시점에 따라 환불 가능 여부와 수수료가 달라진다.

### 시나리오 2: 배송비 정책

지역, 금액, 회원 등급, 프로모션 여부를 정책 객체로 묶으면 계산이 명확해진다.

### 시나리오 3: 승인 정책

관리자 승인, 자동 승인, 예외 승인 조건을 정책으로 분리하면 규칙 변경이 쉬워진다.

---

## 코드로 보기

### 정책 객체

```java
public interface RefundPolicy {
    RefundDecision evaluate(Order order);
}

public record RefundDecision(boolean allowed, int fee, String reason) {}

public class StandardRefundPolicy implements RefundPolicy {
    @Override
    public RefundDecision evaluate(Order order) {
        if (order.isShipped()) {
            return new RefundDecision(false, 0, "shipped already");
        }
        if (order.daysSincePurchase() > 7) {
            return new RefundDecision(false, 0, "refund window expired");
        }
        return new RefundDecision(true, 1000, "ok");
    }
}
```

### 사용처

```java
@Service
public class RefundService {
    private final RefundPolicy refundPolicy;

    public RefundService(RefundPolicy refundPolicy) {
        this.refundPolicy = refundPolicy;
    }

    public RefundDecision refund(Order order) {
        RefundDecision decision = refundPolicy.evaluate(order);
        if (!decision.allowed()) {
            throw new IllegalStateException(decision.reason());
        }
        return decision;
    }
}
```

### Specification과의 경계

```java
public class RefundEligibleSpecification implements Specification<Order> {
    @Override
    public boolean isSatisfiedBy(Order order) {
        return !order.isShipped() && order.daysSincePurchase() <= 7;
    }
}
```

Specification이 참/거짓에 집중한다면, Policy Object는 판단 결과 전체를 담을 수 있다.

### 둘을 함께 쓰는 구조

```java
public class StandardRefundPolicy implements RefundPolicy {
    private final Specification<Order> refundable =
        order -> !order.isShipped() && order.daysSincePurchase() <= 7;

    @Override
    public RefundDecision evaluate(Order order) {
        if (!refundable.isSatisfiedBy(order)) {
            return new RefundDecision(false, 0, "NOT_REFUNDABLE");
        }

        int fee = order.isExpress() ? 3000 : 1000;
        return new RefundDecision(true, fee, "STANDARD_REFUND");
    }
}
```

이 구조의 핵심은 역할 분리다.

- 조건 조합만 재사용하면 Specification으로 충분하다.
- 사유, 수수료, 후속 처리 코드까지 한 번에 넘겨야 하면 Policy Object가 더 자연스럽다.
- Policy Object가 내부적으로 Specification을 사용해도 괜찮다. 공개 계약이 rich decision이면 여전히 Policy Object다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| if-else | 직접적이다 | 규칙이 커지면 지저분해진다 | 아주 단순한 정책 |
| Policy Object | 규칙과 결과/설명을 함께 담는다 | 객체 수가 늘 수 있다 | 판정 결과가 풍부할 때 |
| Specification | 조합과 필터링이 쉽다 | 결과값이 boolean에 가깝다 | 조건 충족 여부만 중요할 때 |

판단 기준은 다음과 같다.

- 정책이 "가능/불가능"만 말하면 Specification도 충분하다
- 정책이 이유, 금액, 레벨 같은 결과를 내면 Policy Object가 더 낫다
- 정책이 알고리즘 전체를 바꾸면 전략을 본다

---

## 꼬리질문

> Q: Policy Object와 Strategy는 같은 건가요?
> 의도: 둘의 목적 차이를 단순히 이름 차이로 보지 않는지 확인한다.
> 핵심: Strategy는 실행 방식을, Policy Object는 도메인 판정을 더 강조한다.

> Q: Policy Object를 쓰면 도메인 서비스가 필요 없나요?
> 의도: 규칙 객체와 오케스트레이션 객체를 구분하는지 확인한다.
> 핵심: 아니다. 정책은 판정을 담당하고 서비스는 흐름을 조립한다.

> Q: 정책이 복잡해지면 어디까지 객체로 분리해야 하나요?
> 의도: 추상화 과잉을 경계하는지 확인한다.
> 핵심: 변경 이유가 다를 때만 쪼갠다.

## 한 줄 정리

Policy Object 패턴은 복잡한 도메인 결정을 객체로 만들어 규칙과 결과를 명시적으로 다루게 한다.
