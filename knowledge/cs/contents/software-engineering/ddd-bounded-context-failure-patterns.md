# DDD Bounded Context Failure Patterns

> 한 줄 요약: 바운디드 컨텍스트는 이름을 나누는 기술이 아니라, 변화와 책임을 분리하는 장치다. 잘못 나누면 분산 모놀리스가 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)
> - [시스템 설계 면접 프레임워크](../system-design/system-design-framework.md)

---

## 핵심 개념

바운디드 컨텍스트는 "도메인 용어가 정확히 같은 의미로 유지되는 경계"다.
겉으로는 패키지 분리처럼 보이지만, 실제 목적은 더 구체적이다.

- 다른 비즈니스 규칙을 하나의 모델에 억지로 넣지 않기
- 변경이 동시에 퍼지는 범위를 줄이기
- 한 팀이 책임질 수 있는 의미 경계를 명확히 하기

실패는 보통 기술이 아니라 **경계 정의가 흐릿할 때** 시작된다.

---

## 깊이 들어가기

### 1. 경계가 잘못되면 용어가 먼저 망가진다

같은 `Order`라도 팀마다 의미가 다를 수 있다.

- 주문 서비스의 `Order`: 결제 전 상태 전이 중심
- 배송 서비스의 `Order`: 출고/배송 상태 중심
- 정산 서비스의 `Order`: 금액과 수수료 계산 중심

이걸 하나의 모델에 우겨 넣으면, 용어가 같아도 규칙이 달라서 코드가 금방 충돌한다.

### 2. 통합 모델의 착각

처음에는 하나의 큰 `Order` 도메인으로 시작하기 쉽다.
문제는 경계가 자라야 할 순간에 보통 이런 반응이 나온다는 점이다.

- 서비스 계층에 조건문이 늘어난다
- 도메인 객체가 다른 서브도메인의 필드를 직접 참조한다
- 모든 변경이 `Order` 하나를 중심으로 퍼진다

이때 모델은 "통합"된 것이 아니라 **서로 다른 규칙이 섞인 상태**다.

### 3. Shared Kernel의 유혹

공통 코드를 하나 만들면 편해 보인다.
하지만 공통 라이브러리가 커질수록 다음 문제가 생긴다.

- 모두가 수정 권한을 가지면서 책임은 흐려진다
- 변경 충돌이 늘어난다
- 사실상 가장 느린 팀의 일정에 맞춰진다

공유는 최소화해야 한다. 공유가 많아질수록 경계는 약해진다.

### 4. ACL이 없으면 외부 모델이 내부를 침식한다

Anti-Corruption Layer(ACL)가 없으면 외부 API나 레거시 DB 스키마가 내부 도메인에 그대로 새어 들어온다.

그 결과:

- 내부 도메인 언어가 외부 용어로 오염된다
- 예외와 상태값이 그대로 퍼진다
- 외부 시스템 변경이 도메인 코드 전체를 흔든다

바운디드 컨텍스트는 "분리"가 핵심이지, 외부와의 연결을 없애는 게 아니다.

---

## 실전 시나리오

### 시나리오 1: 주문과 결제가 한 모델에 섞임

```java
public class Order {
    private PaymentStatus paymentStatus;
    private ShipmentStatus shipmentStatus;
    private RefundStatus refundStatus;
}
```

이 구조는 보기엔 단순하지만, 실제로는 서로 다른 규칙이 한 객체에 섞여 있다.

증상:

- 결제 변경이 배송 규칙을 건드린다
- 환불 정책 변경이 주문 생성 코드까지 흔든다
- 테스트가 한 도메인 테스트가 아니라 통합 시나리오가 된다

### 시나리오 2: 팀 간 용어 충돌

`Cancel`이 한 팀에서는 "주문 취소", 다른 팀에서는 "결제 취소"다.
같은 단어를 다른 의미로 쓰는 순간, 커뮤니케이션 비용이 코드보다 커진다.

### 시나리오 3: 이벤트 이름만 있고 경계는 없음

`OrderPlaced`, `PaymentApproved` 같은 이벤트가 있어도 내부 모델이 하나면 경계가 없다.
이벤트를 썼다는 사실보다, **누가 소유권을 가지는가**가 더 중요하다.

---

## 코드로 보기

### 경계가 없는 모델

```java
public class OrderService {
    public void placeOrder() {
        order.reserveStock();
        order.approvePayment();
        order.requestShipment();
    }
}
```

이 구조는 빨리 만들 수 있지만, 모든 규칙이 한 서비스에 몰린다.

### 경계를 나눈 모델

```java
public class OrderingService {
    public OrderId placeOrder(CreateOrderCommand command) {
        Order order = Order.create(command);
        orderRepository.save(order);
        return order.id();
    }
}

public class PaymentFacade {
    public void approvePayment(OrderId orderId, Money amount) {
        paymentGateway.approve(orderId, amount);
    }
}
```

서로 다른 규칙은 서로 다른 컨텍스트가 소유한다.
연결은 이벤트나 ACL로 한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 하나의 큰 모델 | 시작이 빠르다 | 규칙 충돌이 빠르게 쌓인다 | 매우 단순한 CRUD |
| 바운디드 컨텍스트 분리 | 책임과 변경 범위가 명확하다 | 초기 설계 비용이 있다 | 도메인 규칙이 다르다 |
| Shared Kernel | 공통 코드를 재사용한다 | 결합이 커진다 | 정말 안정적인 공통 개념만 |
| ACL 도입 | 외부 모델 오염을 막는다 | 매핑 비용이 든다 | 외부 시스템이 자주 바뀐다 |

핵심 판단 기준은 "개발자가 편한가"가 아니라, **변경이 어디까지 퍼지는가**다.

---

## 꼬리질문

> Q: 바운디드 컨텍스트를 나누면 항상 좋아지나요?
> 의도: 경계를 기계적으로 쪼개는 오용을 구분하는지 확인
> 핵심: 조직/도메인 복잡도에 비해 과한 분리는 분산 비용만 키운다

> Q: 같은 이름의 객체가 여러 컨텍스트에 존재해도 되나요?
> 의도: 컨텍스트 맥락을 이해하는지 확인
> 핵심: 가능하다. 대신 의미와 소유권이 다르면 별도 모델이어야 한다

> Q: Shared Kernel은 언제 쓰면 안 되나요?
> 의도: 공유 코드의 함정을 아는지 확인
> 핵심: 변경 책임이 불분명하거나 팀 간 속도가 다르면 피하는 편이 낫다

## 한 줄 정리

바운디드 컨텍스트는 도메인 용어를 분리하는 게 아니라, 서로 다른 변화가 서로를 망치지 않도록 책임 경계를 자르는 기술이다.
