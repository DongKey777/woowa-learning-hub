# Command Handler Pattern: 명령을 유스케이스 단위로 처리하기

> 한 줄 요약: Command Handler 패턴은 입력 명령을 하나의 유스케이스로 받아 검증, 실행, 결과 반환을 한 흐름으로 묶는다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [Command Pattern Undo Queue](./command-pattern-undo-queue.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)
> - [Unit of Work Pattern](./unit-of-work-pattern.md)
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)

---

## 핵심 개념

Command Handler는 애플리케이션 서비스의 흔한 형태다.  
입력 Command 하나를 받아 그 유스케이스를 처리한다.

- validate input
- load aggregate
- execute business rule
- persist change
- return result

즉 "명령 객체를 받는 서비스"를 뜻한다.

### Retrieval Anchors

- `command handler`
- `application command`
- `use case handler`
- `validate execute persist`
- `command side`

---

## 깊이 들어가기

### 1. Command와 Handler를 분리하면 읽기 쉬워진다

Command는 무엇을 할지, Handler는 어떻게 처리할지에 가깝다.

- Command: 데이터 캡슐
- Handler: 실행 로직

### 2. 단순 서비스보다 경계가 선명하다

Handler는 보통 한 유스케이스에 대응한다.

- PlaceOrderCommandHandler
- CancelOrderCommandHandler
- ApprovePaymentCommandHandler

이 구조는 CQRS와 잘 맞는다.

### 3. 과하면 service explosion이 될 수 있다

유스케이스가 잘게 쪼개지는 건 좋지만, 너무 작은 handler만 남으면 흐름이 분산된다.

---

## 실전 시나리오

### 시나리오 1: 주문 생성

명령을 받아 주문 aggregate를 로드하고 저장하는 흐름에 적합하다.

### 시나리오 2: 결제 승인

외부 응답을 처리하고 상태를 전이시킬 때도 자연스럽다.

### 시나리오 3: 배치 요청 처리

스케줄러가 command를 만들어 handler를 호출하는 구조가 잘 맞는다.

---

## 코드로 보기

### Command

```java
public record PlaceOrderCommand(Long userId, List<Long> itemIds) {}
```

### Handler

```java
@Service
public class PlaceOrderCommandHandler {
    private final OrderRepository repository;

    public OrderId handle(PlaceOrderCommand command) {
        Order order = Order.place(command.userId(), command.itemIds());
        repository.save(order);
        return order.getId();
    }
}
```

### Controller

```java
@RestController
public class OrderController {
    private final PlaceOrderCommandHandler handler;

    @PostMapping("/orders")
    public OrderId place(@RequestBody PlaceOrderRequest request) {
        return handler.handle(request.toCommand());
    }
}
```

Command Handler는 유스케이스를 한 문장처럼 읽히게 만든다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 service | 단순하다 | 메서드가 섞이기 쉽다 | 작은 시스템 |
| Command Handler | 유스케이스가 선명하다 | 클래스 수가 늘어난다 | 명령 중심 시스템 |
| 이벤트 핸들러 | 비동기 확장이 쉽다 | 순서/정합성이 약하다 | 발생 후 반응 |

판단 기준은 다음과 같다.

- 입력 하나가 유스케이스 하나면 handler가 좋다
- 읽기와 쓰기를 구분할 때 command handler가 자연스럽다
- 명령 객체와 결과 객체를 분리하면 테스트가 쉬워진다

---

## 꼬리질문

> Q: Command Handler와 Application Service는 같은가요?
> 의도: 이름보다 역할을 구분하는지 확인한다.
> 핵심: 거의 같은 감각이지만 command 중심이면 handler라는 이름이 더 명확하다.

> Q: handler가 너무 많아지면 문제인가요?
> 의도: 과도한 쪼개기를 경계하는지 확인한다.
> 핵심: 너무 작으면 흐름을 파악하기 어려워진다.

> Q: CQRS에서 handler가 중요한 이유는 무엇인가요?
> 의도: command side의 경계를 이해하는지 확인한다.
> 핵심: 쓰기 유스케이스를 명확히 분리하기 때문이다.

## 한 줄 정리

Command Handler는 하나의 명령을 하나의 유스케이스로 처리하는 애플리케이션 계층 패턴이다.

