# Immutable Builder and Wither Patterns: 불변 객체를 안전하게 갱신하기

> 한 줄 요약: Immutable Builder는 복잡한 객체 생성을 안정적으로 만들고, Wither는 불변 객체를 조금씩 바꿔 새 인스턴스를 만드는 패턴이다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [빌더 (Builder)](./builder-pattern.md)
> - [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md)
> - [Composition over Inheritance](./composition-over-inheritance-practical.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

불변 객체는 backend에서 안전한 기본값이다.  
하지만 필드가 많아지면 생성자 하나로는 만들기 어렵고, 수정도 새 객체 생성으로 바뀐다.

이때 자주 쓰는 두 가지가 있다.

- Immutable Builder: 복잡한 객체를 단계적으로 생성
- Wither: 기존 불변 객체를 바탕으로 일부 필드만 바꾼 새 객체 생성

### Retrieval Anchors

- `immutable builder`
- `wither pattern`
- `value object update`
- `copy with modification`
- `fluent construction`

---

## 깊이 들어가기

### 1. 불변성은 생성이 불편해진다는 대가를 가진다

불변 객체의 장점은 분명하다.

- 상태 변경이 예측 가능하다
- 멀티스레드에서 안전하다
- 테스트가 단순하다

하지만 필드가 늘면 객체 생성이 힘들어진다.  
Builder는 이 불편을 풀어준다.

### 2. Wither는 작은 변경을 표현한다

`withX(...)` 또는 `toBuilder()` 같은 방식은 기존 객체를 보존하면서 일부만 바꾼 새 객체를 만든다.

- `withAddress`
- `withStatus`
- `withDiscount`

이 패턴은 특히 value object와 aggregate snapshot에 잘 맞는다.

### 3. mutable builder와 구분해야 한다

Builder가 내부적으로 가변 상태를 가진다고 해서 최종 객체도 가변일 필요는 없다.
중요한 건 **최종 산출물이 불변인지**다.

---

## 실전 시나리오

### 시나리오 1: 주문 명세 생성

주문 요청이 복잡하면 builder로 생성 부담을 낮출 수 있다.

### 시나리오 2: 상태 변경 후 새 객체 생성

배송 주소, 결제 상태, 할인 금액처럼 일부만 바뀌는 경우 wither가 자연스럽다.

### 시나리오 3: 테스트 픽스처

기본값이 많은 객체를 만들 때 builder가 특히 유용하다.

---

## 코드로 보기

### Immutable Builder

```java
public final class OrderSnapshot {
    private final Long orderId;
    private final String status;
    private final int totalAmount;

    private OrderSnapshot(Builder builder) {
        this.orderId = builder.orderId;
        this.status = builder.status;
        this.totalAmount = builder.totalAmount;
    }

    public static class Builder {
        private Long orderId;
        private String status;
        private int totalAmount;

        public Builder orderId(Long orderId) {
            this.orderId = orderId;
            return this;
        }

        public Builder status(String status) {
            this.status = status;
            return this;
        }

        public Builder totalAmount(int totalAmount) {
            this.totalAmount = totalAmount;
            return this;
        }

        public OrderSnapshot build() {
            return new OrderSnapshot(this);
        }
    }
}
```

### Wither

```java
public final class ShippingAddress {
    private final String city;
    private final String street;

    public ShippingAddress withCity(String city) {
        return new ShippingAddress(city, this.street);
    }
}
```

### toBuilder

```java
public final class PricePolicy {
    public Builder toBuilder() {
        return new Builder()
            .rate(this.rate)
            .discount(this.discount);
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 생성자 | 가장 단순하다 | 파라미터가 많아지면 읽기 어렵다 | 필드가 적을 때 |
| Builder | 복잡한 생성에 강하다 | 코드가 늘어난다 | 옵션이 많을 때 |
| Wither | 불변성을 유지한다 | 객체 복사가 반복된다 | 일부 필드만 갱신할 때 |

판단 기준은 다음과 같다.

- 필드가 많으면 Builder
- 일부 필드만 바꾸면 Wither
- 불변성이 핵심이면 mutable setter를 피한다

---

## 꼬리질문

> Q: Builder를 쓰면 항상 좋은가요?
> 의도: 패턴을 기본값으로 남용하지 않는지 확인한다.
> 핵심: 필드가 적으면 생성자나 정적 팩토리가 더 낫다.

> Q: Wither와 setter는 어떻게 다른가요?
> 의도: 불변성과 가변성의 차이를 아는지 확인한다.
> 핵심: Wither는 새 객체를 만들고, setter는 기존 객체를 바꾼다.

> Q: toBuilder는 언제 유용한가요?
> 의도: 복제 기반 수정의 장점을 아는지 확인한다.
> 핵심: 기존 상태를 보존한 채 일부만 변경할 때 유용하다.

## 한 줄 정리

Immutable Builder는 복잡한 불변 객체 생성을 돕고, Wither는 불변 객체를 안전하게 변형하는 수단이다.

