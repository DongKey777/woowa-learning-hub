# Spring EventListener, TransactionalEventListener, and Outbox

> 한 줄 요약: 이벤트를 "언제" 처리하느냐는 단순한 실행 시점 문제가 아니라, 트랜잭션 경계와 정합성 경계를 어디에 둘지 결정하는 문제다.

**난이도: 🔴 Advanced**

관련 문서:

- [Spring `@TransactionalEventListener` Outside Transactions and `fallbackExecution`](./spring-transactionaleventlistener-fallbackexecution-no-transaction-boundaries.md)
- [Spring `@EventListener` Ordering and Async Traps](./spring-eventlistener-ordering-async-traps.md)
- [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
- [옵저버, Pub/Sub, ApplicationEvent](../design-pattern/observer-pubsub-application-events.md)
- [Domain Events, Outbox, Inbox](../software-engineering/outbox-inbox-domain-events.md)
- [Change Data Capture / Outbox Relay 설계](../system-design/change-data-capture-outbox-relay-design.md)

---

retrieval-anchor-keywords: spring eventlistener, transactionaleventlistener, after_commit before_commit, outbox pattern spring, event listener transaction boundary, fallbackexecution, no transaction event listener, 이벤트 트랜잭션 경계, outbox 언제 써요, after commit 왜 써요

## 핵심 개념

Spring에서 이벤트를 다루는 방식은 크게 두 갈래다.

- `@EventListener`는 이벤트가 발행되면 즉시 리스너를 실행한다.
- `@TransactionalEventListener`는 현재 트랜잭션의 단계에 맞춰 리스너를 실행한다.

이 차이는 단순히 "조금 늦게 실행되느냐"가 아니다.

- `@EventListener`는 트랜잭션 바깥에서도 즉시 실행될 수 있다.
- `@TransactionalEventListener`는 `BEFORE_COMMIT`, `AFTER_COMMIT`, `AFTER_ROLLBACK`, `AFTER_COMPLETION` 같은 phase를 기준으로 실행된다.

즉, 이벤트 리스너는 "도메인 사실에 반응하는 코드"처럼 보이지만 실제로는 **정합성을 어디까지 같은 트랜잭션 안에서 보장할지**를 정하는 장치다.

이 주제를 이해할 때 가장 중요한 질문은 이거다.

- 이벤트를 발행하는 순간과 처리하는 순간이 같아야 하는가?
- 트랜잭션이 커밋되기 전에만 반응해야 하는가?
- 커밋이 끝난 뒤에만 안전하게 후속 작업을 할 수 있는가?

이 질문에 따라 `@EventListener`, `@TransactionalEventListener`, Outbox를 다르게 선택해야 한다.

---

## 깊이 들어가기

### 1. `@EventListener`는 즉시 반응한다

`@EventListener`는 Spring 애플리케이션 이벤트가 발행되면 바로 실행된다.

```java
@Component
public class OrderEventListener {

    @EventListener
    public void on(OrderPlacedEvent event) {
        notificationService.sendOrderPlaced(event.orderId());
    }
}
```

이 방식의 장점은 단순함이다.

- 트랜잭션과 무관하게 즉시 반응한다.
- 구현이 간결하다.
- 도메인 내부의 "즉시 후속 처리"에 쓰기 쉽다.

하지만 단점도 크다.

- 이벤트를 발행한 트랜잭션이 롤백돼도 이미 리스너가 실행됐을 수 있다.
- DB 상태와 외부 부작용이 어긋날 수 있다.
- 저장 전 검증, 저장 후 후속 처리, 롤백 시 정리 같은 경계를 표현하기 어렵다.

즉, `@EventListener`는 **트랜잭션 정합성과 분리된 즉시 반응**이 필요할 때만 쓰는 편이 안전하다.

### 2. `@TransactionalEventListener`는 트랜잭션 단계에 맞춘다

`@TransactionalEventListener`는 이벤트가 발행된 순간이 아니라, 현재 트랜잭션이 어느 단계인지 보고 실행 시점을 정한다.

```java
@Component
public class OrderTransactionalEventListener {

    @TransactionalEventListener(phase = TransactionPhase.BEFORE_COMMIT)
    public void beforeCommit(OrderPlacedEvent event) {
        validateInventorySnapshot(event.orderId());
    }

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void afterCommit(OrderPlacedEvent event) {
        notificationService.sendOrderPlaced(event.orderId());
    }
}
```

핵심은 phase다.

- `BEFORE_COMMIT`: 커밋 직전, 같은 트랜잭션 안에서 실행된다.
- `AFTER_COMMIT`: 커밋이 끝난 뒤 실행된다.
- `AFTER_ROLLBACK`: 롤백 이후 실행된다.
- `AFTER_COMPLETION`: 커밋/롤백과 무관하게 종료 후 실행된다.

이 차이는 실무에서 아주 중요하다.

- DB 상태를 보고 최종 검증해야 하면 `BEFORE_COMMIT`
- 외부 알림, 캐시 무효화, 검색 반영처럼 커밋된 사실만 보면 되는 작업은 `AFTER_COMMIT`
- 실패 보상이나 정리 작업은 `AFTER_ROLLBACK`

### 3. `BEFORE_COMMIT`과 `AFTER_COMMIT`의 의미는 다르다

둘은 둘 다 `@TransactionalEventListener`지만, 책임이 다르다.

`BEFORE_COMMIT`은 아직 롤백될 수 있는 구간이다.

- 같은 트랜잭션의 DB 상태를 읽을 수 있다.
- 커밋 전에 마지막 검증을 넣기에 좋다.
- 하지만 외부 시스템 호출은 여전히 위험하다.

`AFTER_COMMIT`은 커밋이 확정된 뒤다.

- 이미 커밋된 사실을 기준으로 부수 효과를 실행한다.
- 캐시, 알림, 검색 인덱스, 외부 연동 같은 작업에 적합하다.
- 다만 이 시점부터는 트랜잭션을 되돌릴 수 없다.

그래서 `AFTER_COMMIT`은 "안전한 후속 처리"처럼 보이지만, 실제로는 **정합성을 비동기로 넘기는 경계**다.

### 4. Outbox는 "이벤트를 DB에 먼저 저장"하는 전략이다

`@TransactionalEventListener(AFTER_COMMIT)`는 후속 처리에 좋지만, 여전히 프로세스 장애나 브로커 장애에서 이벤트 유실 위험이 남는다.

그럴 때 Outbox를 쓴다.

- 업무 데이터와 함께 outbox 테이블에 이벤트를 저장한다.
- 같은 트랜잭션으로 커밋한다.
- 별도 릴레이가 outbox를 읽어 외부 시스템에 발행한다.

이 구조는 [Domain Events, Outbox, Inbox](../software-engineering/outbox-inbox-domain-events.md)와 [Outbox, Saga, Eventual Consistency](../database/outbox-saga-eventual-consistency.md)에서 다룬다.

핵심 차이는 이렇다.

- `@TransactionalEventListener(AFTER_COMMIT)`는 Spring 애플리케이션 내부의 후속 처리에 유리하다.
- Outbox는 프로세스 경계와 브로커 장애까지 고려한 더 강한 신뢰성을 준다.

### 5. 어떤 실패가 생기는가

이 주제는 실패 시나리오를 모르면 절반만 이해한 것이다.

#### 실패 시나리오 1: `@EventListener`가 너무 일찍 실행됨

트랜잭션이 롤백될 수 있는데도 이미 이메일을 보내버릴 수 있다.

```java
@Transactional
public void placeOrder(Order order) {
    orderRepository.save(order);
    applicationEventPublisher.publishEvent(new OrderPlacedEvent(order.getId()));
    if (order.isInvalid()) {
        throw new IllegalStateException("invalid order");
    }
}
```

이 경우 `@EventListener`는 이벤트를 바로 받아 실행할 수 있으므로, 주문은 롤백됐는데 알림은 발송되는 버그가 생긴다.

#### 실패 시나리오 2: `AFTER_COMMIT`인데도 외부 작업이 실패함

커밋은 끝났지만 알림 발송이나 캐시 갱신이 실패할 수 있다.

- DB는 맞다.
- 외부 상태는 틀릴 수 있다.
- 그래서 재시도와 idempotency가 필요하다.

#### 실패 시나리오 3: `BEFORE_COMMIT`에서 오래 걸리는 작업을 함

커밋 직전에 외부 API를 호출하면 트랜잭션이 길어진다.

- 락 점유 시간이 늘어난다.
- p99가 튄다.
- 다른 요청이 밀린다.

이 경우는 [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)와 같이 봐야 한다.

#### 실패 시나리오 4: Outbox 없이 "커밋 후 publish"만 함

DB 커밋과 메시지 발행 사이에 프로세스가 죽으면 이벤트가 유실된다.

이게 바로 Outbox를 쓰는 대표적 이유다.

---

## 실전 시나리오

### 시나리오 1: 주문 생성 후 알림은 커밋 뒤에만 보내고 싶다

주문이 실제로 커밋되기 전에는 알림을 보내면 안 된다.

- `@EventListener`는 너무 빠를 수 있다.
- `@TransactionalEventListener(AFTER_COMMIT)`가 더 적합하다.

### 시나리오 2: 커밋 전에 재고를 한 번 더 확인하고 싶다

DB에 저장은 했지만, 커밋 직전에 최종 검증이 필요할 수 있다.

- 이때는 `BEFORE_COMMIT`이 맞다.
- 단, 무거운 로직이나 외부 호출은 피해야 한다.

### 시나리오 3: 검색 색인이나 푸시 알림은 유실되면 안 된다

이건 `AFTER_COMMIT`만으로는 부족할 수 있다.

- 프로세스 장애
- 브로커 장애
- 리스너 예외

까지 고려해야 하므로 Outbox가 더 적합하다.

### 시나리오 4: 이벤트를 두 번 받아도 안전해야 한다

메시지 중복은 현실적인 전제다.

- 알림은 중복 발송되면 안 된다.
- 검색 색인은 같은 문서를 다시 넣어도 안전해야 한다.
- 결제는 절대 두 번 처리되면 안 된다.

그래서 `@TransactionalEventListener`든 Outbox든 결국 소비자 멱등성이 중요하다.

---

## 코드로 보기

### 1. `@EventListener`와 `@TransactionalEventListener` 비교

```java
public record OrderPlacedEvent(Long orderId) {}

@Component
public class OrderEventHandlers {

    @EventListener
    public void onImmediately(OrderPlacedEvent event) {
        log.info("immediate reaction: {}", event.orderId());
    }

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void afterCommit(OrderPlacedEvent event) {
        log.info("after commit: {}", event.orderId());
    }
}
```

### 2. BEFORE_COMMIT에서 검증하고 AFTER_COMMIT에서 후속 처리하기

```java
@Component
public class OrderLifecycleListener {

    @TransactionalEventListener(phase = TransactionPhase.BEFORE_COMMIT)
    public void validate(OrderPlacedEvent event) {
        inventoryValidator.validateSnapshot(event.orderId());
    }

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void notify(OrderPlacedEvent event) {
        notificationService.sendOrderPlaced(event.orderId());
    }
}
```

### 3. Outbox를 함께 쓰는 예시

```java
@Entity
public class OutboxEvent {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String eventType;
    private String aggregateId;
    private String payload;
    private boolean published;
}

@Transactional
public void placeOrder(Order order) {
    orderRepository.save(order);
    outboxRepository.save(OutboxEventBuilder.from(new OrderPlacedEvent(order.getId())));
}
```

별도 릴레이는 outbox를 읽고 브로커에 발행한다.

```java
@Scheduled(fixedDelay = 1000)
public void relay() {
    List<OutboxEvent> events = outboxRepository.findUnpublished();
    for (OutboxEvent event : events) {
        messagePublisher.publish(event.getEventType(), event.getPayload());
        event.markPublished();
    }
}
```

이 구조의 장점은 DB 저장과 이벤트 저장을 같은 트랜잭션으로 묶는다는 점이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `@EventListener` | 단순하고 빠르다 | 트랜잭션 정합성과 분리되기 쉽다 | 즉시 반응이 중요할 때 |
| `@TransactionalEventListener(BEFORE_COMMIT)` | 커밋 직전 검증이 가능하다 | 외부 호출이 길어지면 트랜잭션이 무거워진다 | 마지막 검증이 필요할 때 |
| `@TransactionalEventListener(AFTER_COMMIT)` | 커밋 후 후속 처리에 적합하다 | 프로세스 장애 시 유실 위험이 있다 | 알림, 캐시, 색인 반영 |
| Outbox | 유실에 강하고 재시도 설계가 쉽다 | 릴레이와 운영 비용이 추가된다 | 정합성이 중요하고 유실이 치명적일 때 |

판단 기준은 단순하다.

- 트랜잭션 안에서 끝나야 하면 `BEFORE_COMMIT`
- 커밋 후에만 안전하면 `AFTER_COMMIT`
- 유실까지 막아야 하면 Outbox
- 그냥 즉시 반응이면 `@EventListener`

---

## 꼬리질문

> Q: `@EventListener`와 `@TransactionalEventListener(AFTER_COMMIT)`의 핵심 차이는 무엇인가?
> 의도: 이벤트 실행 시점과 트랜잭션 경계 이해 확인
> 핵심: 즉시 실행인지, 커밋 후 실행인지가 다르다

> Q: `BEFORE_COMMIT`에서 외부 API 호출을 하면 왜 위험한가?
> 의도: 트랜잭션 길이와 락 점유 이해 확인
> 핵심: 커밋 전 작업이 길어져 전체 트랜잭션 비용이 커진다

> Q: Outbox가 `AFTER_COMMIT`보다 더 강한 이유는 무엇인가?
> 의도: 유실 방지와 프로세스 장애 대응 이해 확인
> 핵심: DB 커밋과 이벤트 기록을 같은 트랜잭션으로 묶기 때문이다

> Q: 이벤트는 왜 멱등해야 하는가?
> 의도: 메시징 중복과 재시도 전제 이해 확인
> 핵심: 메시지는 중복될 수 있으므로 같은 이벤트를 다시 받아도 안전해야 한다

> Q: `@TransactionalEventListener`를 쓴다고 해서 Outbox가 필요 없나?
> 의도: Spring 내부 이벤트와 외부 정합성 구분 확인
> 핵심: 프로세스 장애와 브로커 장애까지 막으려면 Outbox가 여전히 필요할 수 있다

---

## 한 줄 정리

이벤트 리스너는 단순 후속 처리가 아니라, 트랜잭션 안에서 반응할지 밖에서 반응할지, 그리고 유실을 어떻게 막을지 정하는 정합성 설계 도구다.
