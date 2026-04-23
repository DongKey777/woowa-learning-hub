# 상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기

> 한 줄 요약: 상태 패턴은 if-else로 흩어진 상태 전이를 객체로 끌어올려, 결제와 워크플로 같은 도메인 흐름을 명시적으로 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [전략 패턴](./strategy-pattern.md)
> - [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)
> - [State Pattern vs State Machine Library vs Workflow Engine](./state-machine-library-vs-state-pattern.md)
> - [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
> - [Command Pattern, Undo, Queue](./command-pattern-undo-queue.md)
> - [Semantic Lock and Pending State Pattern](./semantic-lock-pending-state-pattern.md)
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

상태 패턴(State Pattern)은 **객체의 행위가 내부 상태에 따라 달라질 때**, 상태를 분리해서 다루는 패턴이다.  
핵심은 "지금 상태에서 무엇을 할 수 있는가"를 코드에 직접 드러내는 것이다.

결제, 주문, 승인, 출고, 정산 같은 backend 워크플로는 상태 전이가 많다.
이때 `if (status == ...)`가 커지기 시작하면 다음 문제가 생긴다.

- 상태별 허용 동작이 흩어진다
- 잘못된 전이를 막기 어렵다
- 테스트가 상태 분기별로 복잡해진다
- 도메인 규칙이 문자열 비교로 숨어버린다

상태 패턴은 이 문제를 **상태 객체 + 전이 규칙**으로 바꾼다.

### Retrieval Anchors

- `order payment state machine`
- `workflow transition guard`
- `state vs strategy`
- `state vs policy object`
- `pending authorized captured failed`
- `backend domain workflow`
- `pending state pattern`
- `semantic lock`
- `state pattern enough`
- `local aggregate state`
- `state machine library vs workflow engine`

---

## 깊이 들어가기

### 1. 상태와 전략은 비슷하지만 대상이 다르다

전략 패턴은 "어떤 알고리즘을 고를까"에 가깝고, 상태 패턴은 "지금 객체가 어떤 모드에 있나"에 가깝다.

| 구분 | 전략 패턴 | 상태 패턴 |
|---|---|---|
| 초점 | 알고리즘 선택 | 상태 전이 |
| 변경 주체 | 호출자가 전략을 선택 | 객체가 상태를 바꾼다 |
| 의미 | 교체 가능한 정책 | 시점에 따라 달라지는 행위 |

즉 결제 수단 선택은 전략일 수 있지만, 결제 진행 단계는 상태 패턴이 더 자연스럽다.

### 2. 워크플로는 상태 전이가 도메인 규칙이다

주문이 `CREATED -> PAYMENT_PENDING -> AUTHORIZED -> CAPTURED -> SHIPPED`로 흘러간다고 해보자.
이 순서는 단순한 데이터가 아니라 **비즈니스 규칙**이다.

상태 패턴을 쓰면 다음을 명시할 수 있다.

- 어떤 상태에서 어떤 행동이 가능한가
- 전이 전후에 어떤 검증이 필요한가
- 실패 시 어떤 상태로 돌아가는가
- 보상 로직이 필요한가

### 3. 상태 패턴은 이벤트와 함께 쓰일 때 강해진다

주문 상태 변경 자체는 상태 패턴이 책임지고, 그 결과로 발생하는 알림/포인트/캐시 무효화는 이벤트로 뺄 수 있다.
이렇게 나누면 정합성과 확장성을 함께 챙길 수 있다.

---

## 실전 시나리오

### 시나리오 1: 결제 승인과 캡처

카드 결제는 보통 한 번에 끝나지 않는다.

1. 주문 생성
2. 결제 승인 요청
3. PG 승인 응답 수신
4. 캡처 요청
5. 정산 완료

이 흐름을 상태 객체로 나누면, `승인 전 캡처` 같은 잘못된 호출을 초기에 막을 수 있다.

### 시나리오 2: 관리자 승인 워크플로

휴가 승인, 환불 승인, 상품 등록 승인처럼 상태가 바뀌기 전에 심사가 들어가는 도메인에도 잘 맞는다.

### 시나리오 3: 분산 시스템의 보상 전이

외부 PG나 배송 API처럼 실패 가능성이 있는 시스템과 연동할 때, 전이 실패를 명시하면 운영 로그와 재처리가 쉬워진다.

---

## 코드로 보기

### Before: 상태가 if-else에 묻힌다

```java
public class OrderService {
    public void handle(Order order, String action) {
        if (order.isCreated() && "PAY".equals(action)) {
            order.markPaymentPending();
            return;
        }
        if (order.isPaymentPending() && "APPROVE".equals(action)) {
            order.markAuthorized();
            return;
        }
        if (order.isAuthorized() && "CAPTURE".equals(action)) {
            order.markCaptured();
            return;
        }
        throw new IllegalStateException("invalid transition");
    }
}
```

### After: 상태 객체가 전이를 책임진다

```java
public interface OrderState {
    OrderState pay(Order order);
    OrderState approve(Order order);
    OrderState capture(Order order);
    OrderState cancel(Order order);
}

public final class CreatedState implements OrderState {
    @Override
    public OrderState pay(Order order) {
        order.requestPayment();
        return new PaymentPendingState();
    }

    @Override
    public OrderState approve(Order order) {
        throw new IllegalStateException("payment is not pending");
    }

    @Override
    public OrderState capture(Order order) {
        throw new IllegalStateException("payment is not approved");
    }

    @Override
    public OrderState cancel(Order order) {
        order.cancel();
        return new CanceledState();
    }
}

public class Order {
    private OrderState state = new CreatedState();

    public void pay() {
        state = state.pay(this);
    }

    public void approve() {
        state = state.approve(this);
    }
}
```

상태 객체는 단순히 `enum`을 대체하는 것이 아니라, **상태별 규칙을 응집시키는 역할**을 한다.

### Spring 서비스와 연결하면

```java
@Service
public class PaymentWorkflowService {
    public void onPgApproved(Order order) {
        order.approve();
        // 이후 이벤트 발행 또는 저장
    }
}
```

상태 패턴이 도메인 규칙을 맡고, 트랜잭션과 이벤트는 바깥에서 조립하는 편이 안정적이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `if-else` | 가장 단순하다 | 전이가 늘수록 깨진다 | 상태가 거의 없을 때 |
| `enum + switch` | 상태가 보인다 | 규칙이 커지면 비대해진다 | 전이가 작고 고정적일 때 |
| 상태 패턴 | 상태별 행위를 응집한다 | 클래스 수가 늘어난다 | 전이가 많고 규칙이 자주 바뀔 때 |
| 상태 머신 라이브러리 | 이벤트/가드/전이 표를 읽기 쉽다 | durable timer/recovery는 따로 설계해야 한다 | 상태/이벤트 조합이 밀집할 때 |
| 워크플로 엔진 | 복잡한 흐름을 표현한다 | 도입 비용이 크다 | 승인, 보상, 재시도까지 복잡할 때 |

판단 기준은 간단하다.

- 상태 전이가 도메인 규칙이면 상태 패턴을 먼저 본다
- 전이 matrix가 복잡하지만 실행 ownership이 한 서비스 안에 있으면 상태 머신 라이브러리를 본다
- 전이보다 계산식이 중요하면 전략을 본다
- 흐름이 길고 외부 연동이 많으면 워크플로나 사가를 검토한다

로컬 전이, 전이 표 관리, durable orchestration의 경계는 [State Pattern vs State Machine Library vs Workflow Engine](./state-machine-library-vs-state-pattern.md)에서 이어서 보면 된다.

---

## 꼬리질문

> Q: 상태 패턴과 전략 패턴을 어떻게 구분하나요?
> 의도: "교체 가능한 정책"과 "현재 상태"를 분리해서 보는지 확인한다.
> 핵심: 전략은 호출자가 고르고, 상태는 객체가 스스로 바뀐다.

> Q: 상태 패턴을 쓰면 enum이 필요 없나요?
> 의도: 패턴이 자료형 자체를 완전히 대체한다고 오해하지 않는지 확인한다.
> 핵심: enum은 식별자, 상태 객체는 규칙을 담는 그릇이다.

> Q: 결제 워크플로에 상태 패턴만 쓰면 충분한가요?
> 의도: 패턴을 단독 해법으로 보지 않는지 확인한다.
> 핵심: 상태는 전이를 다루고, 재시도/보상/알림은 이벤트나 사가가 맡는 편이 낫다.

## 한 줄 정리

상태 패턴은 결제와 워크플로의 전이 규칙을 객체로 분리해, 잘못된 상태 변경을 코드 구조로 막는 패턴이다.
