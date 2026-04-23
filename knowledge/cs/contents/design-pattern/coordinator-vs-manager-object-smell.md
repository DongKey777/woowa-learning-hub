# Coordinator vs Manager Object Smell

> 한 줄 요약: Coordinator는 명확한 유스케이스 흐름을 조율하지만, Manager는 책임이 뭉개질 때 붙는 이름이 되기 쉽다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Saga / Coordinator](./saga-coordinator-pattern-language.md)
> - [Orchestration vs Choreography Pattern Language](./orchestration-vs-choreography-pattern-language.md)
> - [Command Handler Pattern](./command-handler-pattern.md)
> - [God Object / Spaghetti / Golden Hammer](./god-object-spaghetti-golden-hammer.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Coordinator는 흐름을 조율하는 역할이 분명하다.  
Manager는 이름만으로는 무엇을 하는지 잘 드러나지 않고, 종종 여러 책임의 쓰레기통이 된다.

backend에서 자주 보이는 신호는 다음과 같다.

- `OrderManager`
- `UserManager`
- `WorkflowManager`
- `DataManager`

이름이 Manager인데 실제로는 validation, persistence, orchestration, notification을 다 하면 smell이다.

### Retrieval Anchors

- `coordinator vs manager smell`
- `manager object`
- `orchestrator responsibility`
- `vague naming smell`
- `god service`

---

## 깊이 들어가기

### 1. Coordinator는 목적이 분명하다

Coordinator는 다음 단계 선택과 순서 조정을 책임진다.

- 무엇을 언제 호출할지
- 실패 시 무엇을 되돌릴지
- 어떤 조건에서 다음 단계로 갈지

### 2. Manager는 의미가 너무 넓다

Manager는 너무 많은 것을 담기 쉽다.

- 상태 변경
- 외부 호출
- 쿼리 조립
- 이벤트 발행

이름만 manager이고 실제로는 god service인 경우가 많다.

### 3. 좋은 이름은 설계를 드러낸다

`PlaceOrderCoordinator`, `RefundOrchestrator`, `BillingPolicyManager`처럼 이름 자체가 역할을 드러내야 한다.

---

## 실전 시나리오

### 시나리오 1: 주문 생성

OrderManager보다 PlaceOrderCoordinator가 흐름을 더 잘 드러낸다.

### 시나리오 2: 배치 작업

작업 단계가 분명하면 Coordinator가 적합하다.

### 시나리오 3: 이름이 책임을 숨길 때

Manager라는 이름은 너무 넓으므로, 유스케이스나 정책 이름으로 바꾸는 편이 낫다.

---

## 코드로 보기

### Coordinator

```java
@Service
public class PlaceOrderCoordinator {
    private final InventoryPort inventoryPort;
    private final PaymentPort paymentPort;

    public void place(OrderCommand command) {
        inventoryPort.reserve(command.items());
        paymentPort.pay(command.payment());
    }
}
```

### Manager smell

```java
public class OrderManager {
    public void validate() {}
    public void save() {}
    public void notifyUsers() {}
    public void calculateFees() {}
}
```

### 개선 방향

```java
public class PlaceOrderUseCase { }
public class OrderPolicy { }
public class OrderNotifier { }
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Coordinator | 흐름이 선명하다 | 너무 커질 수 있다 | 유스케이스 조율 |
| Manager | 이름이 익숙하다 | 책임이 흐려진다 | 거의 없음 |
| 분리된 역할 객체 | 읽기 쉽다 | 클래스 수가 늘어난다 | 책임이 여러 개일 때 |

판단 기준은 다음과 같다.

- 조율이면 Coordinator
- 만능이면 smell
- 이름으로 책임을 숨기면 다시 쪼갠다

---

## 꼬리질문

> Q: 왜 Manager라는 이름이 냄새가 되기 쉬운가요?
> 의도: 책임이 넓은 이름의 위험을 아는지 확인한다.
> 핵심: 역할이 불명확해지기 때문이다.

> Q: Coordinator와 service는 어떻게 다르죠?
> 의도: 조율과 유스케이스 실행을 구분하는지 확인한다.
> 핵심: Coordinator는 흐름, service는 작업을 실행한다.

> Q: 이름만 바꾸면 해결되나요?
> 의도: 명명과 구조를 분리하는지 확인한다.
> 핵심: 아니다. 책임도 함께 나눠야 한다.

## 한 줄 정리

Coordinator는 명확한 흐름 조율자이고, Manager는 책임이 뭉개질 때 붙는 냄새 이름이 되기 쉽다.

