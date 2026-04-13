# Mediator vs Observer vs Pub/Sub

> 한 줄 요약: Mediator는 동료 객체들의 상호작용을 중앙에서 조율하고, Observer는 상태 변화를 알리며, Pub/Sub는 발행자와 구독자를 브로커로 분리한다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [옵저버 (Observer)](./observer.md)
> - [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)
> - [Saga / Coordinator](./saga-coordinator-pattern-language.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)

---

## 핵심 개념

세 패턴은 모두 "객체 간 관계를 느슨하게 만든다"는 점에서 비슷해 보인다.  
하지만 초점이 다르다.

- Mediator: 여러 객체의 상호작용 규칙을 중앙 객체가 조율한다
- Observer: 한 객체의 상태 변화가 여러 관찰자에게 전달된다
- Pub/Sub: 발행자와 구독자를 브로커가 연결한다

backend에서는 이 차이가 중요하다.

- Mediator는 화면 컴포넌트, 워크플로, 라우팅, 승인 흐름에 잘 맞는다
- Observer는 상태 변경 알림, 도메인 이벤트, 캐시 무효화에 잘 맞는다
- Pub/Sub는 비동기 확장, 서비스 분리, 대규모 이벤트 전파에 잘 맞는다

### Retrieval Anchors

- `mediator pattern workflow`
- `observer state change notification`
- `pubsub broker decoupling`
- `orchestration coordination`
- `application event listener`

---

## 깊이 들어가기

### 1. Mediator는 동료 객체 사이의 직접 연결을 줄인다

Mediator는 객체들이 서로를 직접 알지 않도록 만든다.  
대신 모든 상호작용을 중간 조율자가 책임진다.

이 구조는 다음 같은 곳에서 유용하다.

- 주문 생성 화면에서 배송지, 쿠폰, 결제 수단을 함께 조정할 때
- 승인 워크플로에서 여러 입력 상태를 합쳐 다음 액션을 결정할 때
- 복잡한 조건 분기를 중앙에서 통제하고 싶을 때

### 2. Observer는 "상태 변화"가 출발점이다

Observer는 누가 무엇을 결정하는지보다, **상태가 바뀌었을 때 누가 반응하는가**가 핵심이다.

- 주문 완료 후 포인트 적립
- 회원 등급 변경 후 혜택 갱신
- 결제 실패 후 알림 발송

Observer는 반응이 핵심이고, Mediator는 조정이 핵심이다.

### 3. Pub/Sub는 브로커가 경계를 만든다

Pub/Sub는 발행자와 구독자가 서로를 모르고, 메시지 브로커가 연결한다.

- 서비스 간 비동기 연동
- 이벤트 스트림 처리
- 장애 격리와 확장성 확보

Observer가 "같은 프로세스 안의 반응"에 가깝다면, Pub/Sub는 "시스템 간 전파"에 가깝다.

---

## 실전 시나리오

### 시나리오 1: 주문 생성 UI

배송지 변경, 쿠폰 선택, 결제 수단 선택이 서로 영향을 주면 Mediator가 자연스럽다.

### 시나리오 2: 주문 완료 후 후속 작업

포인트 적립, 메일 발송, 통계 집계는 Observer나 ApplicationEvent로 충분하다.

### 시나리오 3: 서비스 간 통지

재고 서비스, 알림 서비스, 검색 인덱스 갱신처럼 서로 느슨하게 연결된 시스템은 Pub/Sub가 맞다.

---

## 코드로 보기

### Mediator

```java
public interface OrderMediator {
    void onCouponSelected(String couponId);
    void onShippingAddressChanged(String address);
    void onPaymentMethodChanged(String paymentMethod);
}

public class CheckoutMediator implements OrderMediator {
    private final CheckoutForm form;

    public CheckoutMediator(CheckoutForm form) {
        this.form = form;
    }

    @Override
    public void onCouponSelected(String couponId) {
        form.recalculateTotal();
    }

    @Override
    public void onShippingAddressChanged(String address) {
        form.revalidateDeliveryFee();
    }

    @Override
    public void onPaymentMethodChanged(String paymentMethod) {
        form.refreshAvailableInstallments();
    }
}
```

### Observer

```java
public class Order {
    private final List<OrderListener> listeners = new ArrayList<>();

    public void addListener(OrderListener listener) {
        listeners.add(listener);
    }

    public void complete() {
        // 상태 변경
        listeners.forEach(listener -> listener.onCompleted(this));
    }
}
```

### Pub/Sub

```java
public record OrderCompletedEvent(Long orderId, Long userId) {}

@Component
public class OrderCompletedPublisher {
    private final ApplicationEventPublisher publisher;

    public void publish(OrderCompletedEvent event) {
        publisher.publishEvent(event);
    }
}
```

Mediator는 조율, Observer는 통지, Pub/Sub는 전파다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 직접 참조 | 단순하다 | 결합도가 높다 | 객체 수가 매우 적을 때 |
| Mediator | 상호작용 규칙이 한곳에 모인다 | 중앙 객체가 비대해질 수 있다 | 여러 컴포넌트가 서로 얽힐 때 |
| Observer | 상태 변화 후속 작업 분리가 쉽다 | 순서와 실패가 복잡할 수 있다 | 같은 프로세스 내부 통지 |
| Pub/Sub | 확장성과 분리가 좋다 | 운영과 추적 비용이 커진다 | 서비스 간 비동기 연동 |

판단 기준은 다음과 같다.

- 객체들 사이의 대화 자체를 정리하려면 Mediator
- 상태 변화에 반응하게 하려면 Observer
- 시스템 경계를 넘겨야 하면 Pub/Sub

---

## 꼬리질문

> Q: Mediator와 Observer를 헷갈리면 어떤 문제가 생기나요?
> 의도: 조정과 통지를 구분하는지 확인한다.
> 핵심: Mediator는 흐름을 결정하고, Observer는 결정된 결과를 듣는다.

> Q: Spring ApplicationEvent는 Observer인가요, Pub/Sub인가요?
> 의도: 구현과 사용 감각을 분리하는지 확인한다.
> 핵심: 내부적으로는 Observer 느낌이지만, 사용자는 Pub/Sub처럼 느낀다.

> Q: Mediator가 너무 커지면 어떻게 하나요?
> 의도: 중앙 조율자가 God Object가 될 수 있음을 아는지 확인한다.
> 핵심: 워크플로를 더 작은 단계나 상태 머신으로 나눈다.

## 한 줄 정리

Mediator는 상호작용을 중앙에서 조율하고, Observer는 상태 변화를 통지하며, Pub/Sub는 브로커로 시스템을 느슨하게 연결한다.

