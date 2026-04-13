# Spring `@EventListener` Ordering and Async Traps

> 한 줄 요약: `@EventListener`는 순서와 비동기 실행을 쉽게 조합할 수 있지만, 트랜잭션 경계와 실행 순서를 같이 설계하지 않으면 이벤트가 먼저 가거나 유실처럼 보일 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring EventListener, TransactionalEventListener, and Outbox](./spring-eventlistener-transaction-phase-outbox.md)
> - [Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls](./spring-transaction-synchronization-aftercommit-pitfalls.md)
> - [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)
> - [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)

retrieval-anchor-keywords: EventListener, async event listener, order annotation, transactional event listener, application event publisher, listener ordering, @Async, event phase, idempotency, event publication

## 핵심 개념

Spring 이벤트는 단순 publish/subscribe가 아니다.

이벤트 리스너는 다음 축을 함께 봐야 한다.

- 동기냐 비동기냐
- 어떤 순서로 실행되느냐
- 트랜잭션 안에서 처리되느냐
- 실패가 어떻게 보이느냐

`@EventListener`는 편하지만, 여기에 `@Order`와 `@Async`를 섞는 순간 사고 가능성이 커진다.

## 깊이 들어가기

### 1. `@EventListener`는 기본적으로 동기 실행이다

```java
@Component
public class OrderEventListener {

    @EventListener
    public void on(OrderPlacedEvent event) {
        notificationService.send(event.orderId());
    }
}
```

기본적으로 publish한 스레드에서 바로 실행된다.

- 구현이 단순하다
- 호출 순서를 따라가기가 쉽다
- 하지만 리스너가 길어지면 publish 경로를 잡아먹는다

### 2. `@Order`는 리스너 실행 순서를 정한다

여러 리스너가 같은 이벤트를 받으면 순서를 정할 수 있다.

```java
@Component
@Order(1)
public class ValidateOrderListener {

    @EventListener
    public void on(OrderPlacedEvent event) {
        inventoryChecker.validate(event.orderId());
    }
}

@Component
@Order(2)
public class NotifyOrderListener {

    @EventListener
    public void on(OrderPlacedEvent event) {
        notificationService.send(event.orderId());
    }
}
```

하지만 여기서 중요한 건 순서가 **같은 스레드, 같은 publish 흐름 안에서만** 의미를 가진다는 점이다.

### 3. `@Async`가 붙으면 순서 감각이 깨진다

`@Async`가 붙은 이벤트 리스너는 별도 executor에서 실행된다.

```java
@Async
@EventListener
public void on(OrderPlacedEvent event) {
    notificationService.send(event.orderId());
}
```

이 경우 주의할 점은 다음이다.

- 호출자 스레드와 분리된다
- 순서 보장이 약해진다
- 예외가 publish 호출자에게 바로 전달되지 않는다
- 트랜잭션과 연결되어 있지 않을 수 있다

즉, `@Order`와 `@Async`를 같이 쓰면 "순서가 있으니 안전하다"는 직관이 깨진다.

### 4. 트랜잭션 이벤트와 일반 이벤트를 섞지 말아야 한다

`@EventListener`는 즉시 반응하고, `@TransactionalEventListener`는 phase에 묶인다.

두 가지를 같은 흐름에 섞으면 다음 문제가 생긴다.

- 어떤 리스너는 커밋 전에 실행된다
- 어떤 리스너는 커밋 뒤에 실행된다
- `@Async`가 붙은 리스너는 더 늦게 실행된다

결과적으로 "이 이벤트는 처리됐다"고 말하기 어려워진다.

이 문맥은 [Spring EventListener, TransactionalEventListener, and Outbox](./spring-eventlistener-transaction-phase-outbox.md)와 같이 봐야 한다.

### 5. 이벤트 리스너는 멱등해야 한다

리스너가 여러 번 불릴 수 있다고 가정해야 한다.

- 재시도
- 중복 publish
- 비동기 지연
- 장애 후 replay

그래서 리스너는 side effect를 만들더라도 멱등성이 있어야 한다.

## 실전 시나리오

### 시나리오 1: 리스너 A가 끝나기도 전에 리스너 B가 실행됐다

대개 다음 중 하나다.

- `@Async`가 섞였다
- 서로 다른 이벤트 타입이다
- 순서 보장이 필요한데 별도 executor가 달랐다

### 시나리오 2: 이벤트 publish는 성공했는데 후속 작업이 안 보인다

비동기 리스너는 호출자 입장에서 성공처럼 보이지만 실제 작업은 실패했을 수 있다.

대응:

- future/exception handler를 붙인다
- 실패 metric을 남긴다
- 중요한 후속 작업이면 큐나 outbox를 쓴다

### 시나리오 3: `@EventListener`가 트랜잭션 전에 외부 호출을 했다

이건 [Spring EventListener, TransactionalEventListener, and Outbox](./spring-eventlistener-transaction-phase-outbox.md)에서 다룬 전형적 문제다.

- 주문은 롤백됐다
- 알림만 발송됐다

### 시나리오 4: `@Order`가 있는데도 원하는 순서가 아니다

순서는 리스너들 사이에서만 의미가 있다.

- `@Async`가 끼면 스케줄링 순서가 바뀔 수 있다
- 리스너가 다른 스레드풀을 쓰면 더 예측하기 어렵다

## 코드로 보기

### 동기 리스너 순서

```java
@Component
@Order(1)
public class FirstListener {

    @EventListener
    public void on(OrderPlacedEvent event) {
        log.info("first");
    }
}
```

```java
@Component
@Order(2)
public class SecondListener {

    @EventListener
    public void on(OrderPlacedEvent event) {
        log.info("second");
    }
}
```

### 비동기 리스너

```java
@Async("applicationTaskExecutor")
@EventListener
public void on(OrderPlacedEvent event) {
    notificationService.send(event.orderId());
}
```

### 트랜잭션 이벤트로 옮기는 예

```java
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void onAfterCommit(OrderPlacedEvent event) {
    notificationService.send(event.orderId());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `@EventListener` | 단순하고 즉시 실행된다 | 트랜잭션 정합성이 약하다 | 가벼운 내부 이벤트 |
| `@Order` | 실행 순서를 표현할 수 있다 | 비동기와 섞이면 약해진다 | 순차 후처리 |
| `@Async` | publish 경로를 짧게 만든다 | 실패와 순서 추적이 어렵다 | 느린 후속 작업 |
| `@TransactionalEventListener` | 트랜잭션 단계에 맞춘다 | phase를 잘못 고르면 위험하다 | 정합성이 중요한 후속 작업 |

핵심은 이벤트를 발행하는 것보다, **이벤트 처리 완료의 의미를 어떻게 정의하느냐**다.

## 꼬리질문

> Q: `@Order`는 언제 의미가 있고 언제 의미가 약해지는가?
> 의도: 동기/비동기 실행 차이 확인
> 핵심: 같은 publish 흐름 안에서만 의미가 강하다.

> Q: `@Async`가 붙은 `@EventListener`에서 가장 먼저 문제가 되는 것은 무엇인가?
> 의도: 실행 분리 이해 확인
> 핵심: 순서, 예외 전파, 트랜잭션 경계다.

> Q: `@EventListener`와 `@TransactionalEventListener`를 섞으면 왜 복잡해지는가?
> 의도: 이벤트 정합성 이해 확인
> 핵심: 커밋 전/후가 섞여 "언제 완료됐는지"가 불명확해진다.

> Q: 이벤트 리스너는 왜 멱등해야 하는가?
> 의도: 중복 처리 전제 이해 확인
> 핵심: 재시도와 중복 publish가 현실적으로 가능하기 때문이다.

## 한 줄 정리

Spring 이벤트는 순서, 비동기, 트랜잭션 경계를 함께 봐야 하며, `@Order`와 `@Async`를 섞을수록 멱등성과 관측성이 중요해진다.
