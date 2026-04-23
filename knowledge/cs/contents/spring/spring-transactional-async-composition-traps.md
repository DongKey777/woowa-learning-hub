# Spring `@Transactional` and `@Async` Composition Traps

> 한 줄 요약: `@Transactional`과 `@Async`를 함께 쓴다고 해서 하나의 논리적 작업이 유지되는 것은 아니며, 스레드가 바뀌는 순간 트랜잭션 소유권과 실패 전파가 갈라진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)
> - [Spring EventListener, TransactionalEventListener, and Outbox](./spring-eventlistener-transaction-phase-outbox.md)
> - [Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls](./spring-transaction-synchronization-aftercommit-pitfalls.md)
> - [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)

retrieval-anchor-keywords: transactional async, @Transactional @Async, async transaction boundary, transaction thread local, after commit async, async rollback, self invocation async transaction, fire and forget side effect

## 핵심 개념

Spring 트랜잭션은 보통 현재 스레드에 묶인다.

반면 `@Async`는 실행 스레드를 바꾼다.

그래서 이 둘을 조합할 때 가장 중요한 사실은 단순하다.

- 호출자 트랜잭션이 async 스레드로 자동 전파되지 않는다
- async 작업의 예외가 호출자에게 자동으로 롤백 신호가 되지 않는다
- 같은 클래스 내부 호출이면 `@Transactional`, `@Async` 둘 다 프록시를 못 탈 수 있다

즉 이 문제는 "어노테이션을 몇 개 붙였나"가 아니라, **실제로 어느 스레드에서 어떤 프록시를 거쳐 실행되느냐**의 문제다.

## 깊이 들어가기

### 1. 호출 형태마다 실제 경계가 다르다

대표적인 패턴을 나누면 감각이 빨라진다.

| 호출 형태 | 실제 의미 |
|---|---|
| `@Transactional` 메서드가 `@Async` 메서드를 호출 | async 작업은 원래 트랜잭션 밖의 별도 스레드에서 돈다 |
| `@Async` 메서드 안에서 `@Transactional` 메서드를 외부 빈으로 호출 | async 스레드 안에서 새 트랜잭션이 열릴 수 있다 |
| 한 메서드에 `@Async`와 `@Transactional`을 함께 선언 | 트랜잭션이 적용되더라도 caller tx가 이어지는 게 아니라 worker thread 경계에서 별개로 적용된다 |
| 같은 클래스 내부에서 `this.asyncTxMethod()` 호출 | 프록시를 안 타서 async도 tx도 기대와 다를 수 있다 |

핵심은 "둘 다 붙였으니 둘 다 된다"가 아니라, **프록시 경로와 스레드 경로가 무엇인가**다.

### 2. `@Transactional` 안에서 바로 `@Async` side effect를 던지면 정합성이 깨질 수 있다

다음 코드는 흔하지만 위험하다.

```java
@Transactional
public void placeOrder(OrderCommand command) {
    orderRepository.save(command.toEntity());
    notificationService.sendAsync(command.userId());
}
```

왜 문제일까.

- 주문 트랜잭션은 아직 커밋 전일 수 있다
- async 알림은 별도 스레드에서 먼저 실행될 수 있다
- 나중에 주문이 롤백돼도 알림은 이미 발송됐을 수 있다

즉 `@Async`는 "나중에"가 아니라, **원래 트랜잭션과 분리된 다른 경계**다.

### 3. async 작업의 실패는 원래 트랜잭션을 되돌리지 못한다

async 메서드가 실패해도 호출자는 이미 반환했을 수 있다.

따라서 다음이 중요하다.

- `void` async는 `AsyncUncaughtExceptionHandler`나 내부 관측이 없으면 실패가 잘 안 보인다
- `Future` / `CompletableFuture`를 쓰면 호출자가 실패를 관측할 수 있지만, 이미 caller tx와는 경계가 분리됐다
- async 내부 DB 쓰기는 독립 커밋일 수 있다

즉 실패 전파 모델이 동기 호출과 완전히 다르다.

### 4. "커밋 후에만 async로 하고 싶다"면 경계를 두 단계로 나눠야 한다

주문 저장이 확정된 뒤에만 느린 후속 작업을 실행하고 싶다면 보통 아래 패턴이 더 안전하다.

- 트랜잭션 안에서 도메인 이벤트 발행
- `@TransactionalEventListener(AFTER_COMMIT)`로 커밋 후 실행
- 필요하면 그 리스너 안에서 `@Async`로 넘김

```java
@Transactional
public void placeOrder(OrderCommand command) {
    Order order = orderRepository.save(command.toEntity());
    applicationEventPublisher.publishEvent(new OrderPlacedEvent(order.getId()));
}
```

```java
@Async("applicationTaskExecutor")
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void on(OrderPlacedEvent event) {
    notificationSender.send(event.orderId());
}
```

이 패턴도 완전한 전달 보장을 의미하진 않는다.

프로세스 장애와 재시도 신뢰성이 중요하면 outbox가 더 강한 선택이다.

### 5. `@Async`와 `@Transactional`을 같은 메서드에 붙여도 caller tx가 이어지지 않는다

외부에서 프록시를 통해 진입한다면 worker thread에서 메서드가 실행될 수 있고, 그 안에서 트랜잭션이 열릴 수 있다.

하지만 중요한 건 아래다.

- caller thread의 트랜잭션과 동일하지 않다
- rollback fate를 공유하지 않는다
- MDC, `SecurityContext`, request scope도 별도 전파 설계가 필요하다

즉 이 조합은 "비동기 + 별도 트랜잭션"에 가깝지, **하나의 넓은 트랜잭션**이 아니다.

### 6. 테스트는 async 경계를 자주 숨긴다

`@Transactional` 테스트 안에서 async 코드를 검증하면 다음이 자주 섞인다.

- 테스트 메서드의 롤백
- async 스레드의 독립 쓰기
- 타이밍 이슈 때문에 보였다 안 보였다 하는 상태

그래서 async + transaction 경로는 테스트에서 특히 다음이 중요하다.

- await 전략
- 관측 가능한 실패 채널
- DB 정리 방식
- caller tx와 worker tx를 구분한 assertion

## 실전 시나리오

### 시나리오 1: 주문은 롤백됐는데 이메일은 발송됐다

트랜잭션 안에서 바로 `@Async` 알림을 호출했을 가능성이 높다.

느린 side effect는 커밋 후 경계로 옮겨야 한다.

### 시나리오 2: async 내부 저장은 성공했는데 원래 서비스는 실패했다

worker thread에서 열린 독립 트랜잭션이 이미 커밋됐을 수 있다.

즉 "같은 유스케이스니까 같이 롤백되겠지"라는 기대가 틀린 것이다.

### 시나리오 3: `@Async @Transactional` 메서드를 만들었는데 아무것도 안 되는 것 같다

같은 클래스 내부 호출로 프록시를 못 탔을 수 있다.

이 경우는 async도 tx도 적용되지 않거나 일부만 적용될 수 있다.

### 시나리오 4: 테스트에서는 되는데 운영에서만 간헐적으로 후속 작업이 누락된다

async 예외가 호출자에게 드러나지 않고, 모니터링도 없을 수 있다.

이때는 "비동기라서 언젠가 되겠지"보다, 실패 관측과 재시도 책임을 먼저 정해야 한다.

## 코드로 보기

### 위험한 직접 조합

```java
@Service
public class OrderService {

    private final NotificationService notificationService;

    @Transactional
    public void placeOrder(Order order) {
        orderRepository.save(order);
        notificationService.sendAsync(order.getUserId());
    }
}
```

### async 메서드에서 별도 트랜잭션 시작

```java
@Service
public class NotificationService {

    @Async("applicationTaskExecutor")
    @Transactional
    public void sendAsync(Long userId) {
        notificationLogRepository.save(new NotificationLog(userId));
    }
}
```

이 코드는 worker thread에서 새 트랜잭션을 열 수 있지만, caller tx와 운명을 같이하지는 않는다.

### 커밋 후 async 처리

```java
@Component
public class OrderPlacedListener {

    @Async("applicationTaskExecutor")
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void on(OrderPlacedEvent event) {
        notificationSender.send(event.orderId());
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 트랜잭션 안에서 동기 후속 처리 | 정합성이 단순하다 | 응답 시간과 트랜잭션 길이가 늘어난다 | 짧고 필수적인 후속 작업 |
| 트랜잭션 안에서 즉시 `@Async` 호출 | 호출 경로는 짧다 | 롤백과 분리되고 실패 추적이 어렵다 | 중요도가 낮은 fire-and-forget 작업 |
| `AFTER_COMMIT` + `@Async` | 커밋 확정 후 비동기화가 가능하다 | 프로세스 장애 시 전달 보장은 약하다 | 알림, 캐시, 느린 후속 처리 |
| outbox relay | 신뢰성과 재시도가 강하다 | 구현과 운영이 더 복잡하다 | 중요한 외부 전송, 통합 이벤트 |

핵심은 `@Transactional`과 `@Async`를 함께 붙이는 것보다, **어떤 작업이 같은 commit fate를 공유해야 하는지**를 먼저 정하는 것이다.

## 꼬리질문

> Q: `@Transactional` 메서드가 `@Async` 메서드를 호출하면 왜 원래 트랜잭션이 이어지지 않는가?
> 의도: thread-bound transaction 이해 확인
> 핵심: 트랜잭션은 보통 현재 스레드에 묶이고, async는 다른 스레드에서 실행되기 때문이다.

> Q: `@Async @Transactional` 메서드를 한 곳에 같이 붙이면 무엇을 기대해야 하고 무엇을 기대하면 안 되는가?
> 의도: 복합 어노테이션 오해 교정
> 핵심: worker thread에서 별도 트랜잭션은 가능할 수 있지만 caller tx 연속성은 기대하면 안 된다.

> Q: 커밋 후에만 알림을 보내고 싶다면 어떤 패턴이 더 안전한가?
> 의도: side effect 경계 설계 확인
> 핵심: `@TransactionalEventListener(AFTER_COMMIT)`나 outbox를 고려한다.

> Q: async 실패가 운영에서 특히 위험한 이유는 무엇인가?
> 의도: failure visibility 이해 확인
> 핵심: 호출자가 이미 반환해 버려 예외가 쉽게 보이지 않고 재시도 책임도 모호해지기 때문이다.

## 한 줄 정리

`@Transactional`과 `@Async`를 같이 쓸 때 중요한 것은 어노테이션 조합이 아니라, 스레드가 갈라지는 순간 commit fate와 실패 전파가 함께 갈라진다는 사실이다.
