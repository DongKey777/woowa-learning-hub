# Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기

> 한 줄 요약: 초급자는 "외부 API를 트랜잭션 안에 넣을까?"를 propagation 옵션으로 풀기보다, **로컬 DB 변경**, **커밋 후 후속 처리**, **유실되면 안 되는 외부 전달**을 서로 다른 경계로 나눠서 보는 편이 훨씬 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md)
- [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)
- [Spring Beginner Bridge: 외부 승인 성공 뒤 DB 저장이 실패하면 rollback보다 보상 + 멱등성으로 닫기](./spring-payment-approval-db-failure-compensation-idempotency-primer.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
- [Spring Mini Card: 왜 rollback 기반 slice test만으로 `AFTER_COMMIT`를 끝까지 믿기 어려운가](./spring-after-commit-rollback-slice-test-mini-card.md)
- [Spring EventListener / TransactionalEventListener / Outbox](./spring-eventlistener-transaction-phase-outbox.md)
- [트랜잭션 경계 체크리스트 카드](../database/transaction-boundary-external-io-checklist-card.md)
- [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
- [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)
- [Idempotency Key Status Contract Examples](../database/idempotency-key-status-contract-examples.md)

retrieval-anchor-keywords: service layer external io primer, transactional external api beginner, after commit vs outbox beginner, spring service transaction external side effect, 외부 io 트랜잭션 밖, 커밋 후 알림, 결제 승인 트랜잭션 경계, outbox beginner spring, after_commit beginner spring, propagation external side effect, required requires_new external api, flush is not commit external api, jpa flush 외부 호출, 메시지 발행 outbox primer, beginner transaction boundary remote call, service layer side effect split, 주문 생성 결제 승인 트랜잭션 예시, external approval success db failure compensation, payment cancel compensation beginner, approval succeeded but local tx failed, payment idempotency retry bridge

## 먼저 mental model 한 줄

트랜잭션은 **내 DB 상태를 같이 commit/rollback하는 경계**이지, 외부 결제 API나 메시지 브로커까지 같이 되돌리는 마법이 아니다.

초급자는 아래 3개 상자를 먼저 나누면 된다.

- 상자 1. 로컬 DB 변경: `REQUIRED`로 짧게 묶는 메인 트랜잭션
- 상자 2. 커밋 뒤 후속 처리: `AFTER_COMMIT` 이벤트
- 상자 3. 유실되면 안 되는 외부 전달: outbox + 별도 relay

핵심은 "`REQUIRES_NEW`를 어디 붙일까?"가 아니라, **외부 부작용을 메인 DB 트랜잭션과 같은 상자에 넣지 않는 것**이다.

## 30초 선택표

| 지금 요구사항 | 먼저 고를 기본 방향 | 왜 이쪽이 먼저인가 |
|---|---|---|
| 외부 API 응답을 보고 그다음 DB 상태를 정해야 한다 | 외부 호출을 메인 tx 밖으로 빼고, DB 트랜잭션은 앞뒤로 짧게 나눈다 | 외부 지연이 lock/connection 점유 시간으로 번지는 것을 줄인다 |
| 주문 commit 뒤 알림/캐시 무효화 정도만 하면 된다 | `@TransactionalEventListener(AFTER_COMMIT)` | 커밋된 사실에만 반응하게 만들 수 있다 |
| 브로커 발행/통합 이벤트가 유실되면 안 된다 | outbox | app 프로세스 장애까지 고려한 재시도 경로를 만들 수 있다 |
| 감사 로그처럼 "별도 로컬 DB 기록"만 남기고 싶다 | 제한적으로 `REQUIRES_NEW` | 외부 API가 아니라 **독립 로컬 commit**일 때만 의미가 맞는다 |

## 가장 먼저 버려야 할 오해 4개

- `REQUIRES_NEW`를 외부 결제 API 호출에 붙인다고 외부 시스템과 원자적으로 묶이지 않는다.
- `flush()`를 먼저 했다고 외부 API 호출 전 상태가 "확정"된 것은 아니다. `flush`는 commit이 아니다.
- `AFTER_COMMIT`은 "커밋 뒤 실행"이지 "절대 유실 안 됨"을 뜻하지 않는다.
- outbox는 "비동기라서 대충 늦게 보내는 패턴"이 아니라, **전달 사실 자체를 DB에 같이 남기는 패턴**이다.

## 서비스 레이어에서 가장 흔한 3가지 예시

### 예시 1. 결제 승인 응답을 받아야 주문 상태를 정할 수 있다 -> 외부 I/O를 메인 tx 밖으로 둔다

초급자가 가장 자주 쓰는 before 코드는 이런 모양이다.

```java
@Transactional
public void placeOrder(PlaceOrderCommand command) {
    Order order = orderRepository.save(Order.pending(command));
    inventoryService.decrease(command.items());

    PaymentResult result = paymentClient.authorize(command.paymentToken()); // external I/O

    order.markPaid(result.approvalId());
}
```

문제는 간단하다.

- 결제 API가 느려지면 DB 트랜잭션도 같이 길어진다.
- 결제 API가 실패해도 이미 중간 DB 상태가 생겼을 수 있다.
- JPA `flush`를 중간에 넣어도 외부 결제와 같은 원자성은 생기지 않는다.

초급자는 아래처럼 **짧은 DB 트랜잭션 2개 + 외부 호출 1개**로 먼저 나누는 편이 안전하다.

```java
public void placeOrder(PlaceOrderCommand command) {
    Long orderId = orderTxService.createPendingOrder(command); // tx 1

    PaymentResult result = paymentClient.authorize(command.paymentToken()); // tx 밖

    orderTxService.markPaid(orderId, result.approvalId()); // tx 2
}
```

```java
@Service
public class OrderTxService {

    @Transactional
    public Long createPendingOrder(PlaceOrderCommand command) {
        Order order = orderRepository.save(Order.pending(command));
        inventoryService.decrease(command.items());
        return order.getId();
    }

    @Transactional
    public void markPaid(Long orderId, String approvalId) {
        orderRepository.getById(orderId).markPaid(approvalId);
    }
}
```

이 예시에서 propagation 감각은 이 정도면 충분하다.

- 핵심 DB 변경은 기본 `REQUIRED`로 각 짧은 tx 안에 묶는다.
- 외부 결제 API 호출은 propagation 옵션으로 해결하지 않고 아예 tx 밖으로 뺀다.

### 예시 2. 주문 commit 뒤 이메일 발송이면 충분하다 -> `AFTER_COMMIT`

이번에는 "주문이 실제로 저장된 뒤에만 이메일을 보내면 된다"는 상황이다.

이때는 메인 트랜잭션 안에서 메일 API를 바로 부르기보다, 커밋 뒤에 반응하게 분리하는 편이 맞다.

```java
@Transactional
public Long placeOrder(PlaceOrderCommand command) {
    Order order = orderRepository.save(Order.completed(command));
    applicationEventPublisher.publishEvent(new OrderPlacedEvent(order.getId()));
    return order.getId();
}
```

```java
@Component
public class OrderPlacedNotificationListener {

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void on(OrderPlacedEvent event) {
        notificationClient.sendOrderCompleted(event.orderId());
    }
}
```

이 구조가 맞는 이유는 다음과 같다.

- 주문이 롤백되면 알림도 보내지지 않는다.
- 외부 알림 대기가 메인 DB 트랜잭션 길이를 늘리지 않는다.
- 서비스 메서드 설명이 "주문 저장"과 "후속 알림"으로 자연스럽게 분리된다.

단, 여기서도 한계는 분명하다.

- 커밋 직후 프로세스가 죽으면 알림이 빠질 수 있다.
- 알림 실패를 DB rollback으로 되돌릴 수는 없다.

즉 `AFTER_COMMIT`은 **커밋 후 반응**에는 좋지만, **전달 보장**까지 해결하지는 않는다.

### 예시 3. 브로커 발행이 절대 빠지면 안 된다 -> outbox

주문 생성 뒤 Kafka/RabbitMQ 이벤트 발행이 다른 서비스와의 계약이라면, `AFTER_COMMIT`만으로는 불안할 수 있다.

이때는 "보낼 이벤트"를 DB에 같이 저장한다.

```java
@Transactional
public Long placeOrder(PlaceOrderCommand command) {
    Order order = orderRepository.save(Order.completed(command));
    outboxRepository.save(OutboxEvent.orderPlaced(order.getId()));
    return order.getId();
}
```

```java
public void relayPendingEvents() {
    OutboxEvent event = outboxRepository.nextPending();
    messagePublisher.publish(event);
    outboxRepository.markSent(event.getId());
}
```

초급자는 아래 한 줄로 기억하면 된다.

- 메인 tx 안에서는 "브로커에 지금 보냈다"가 아니라, "보내야 할 사실을 DB에 남겼다".

그래서 outbox는 이런 상황에 맞다.

- 다른 시스템이 그 이벤트를 꼭 받아야 한다.
- 프로세스 재시작이나 브로커 장애가 현실적인 전제다.
- 재시도와 멱등성을 운영으로 가져갈 준비가 되어 있다.

## propagation을 어디까지 연결해서 보면 되나

이 주제에서 초급자가 실무에 바로 써먹을 전파 규칙은 3개면 충분하다.

| 규칙 | 초급자용 해석 | 여기서의 역할 |
|---|---|---|
| `REQUIRED` | 같은 DB 유스케이스면 같이 묶는다 | 주문 저장, 재고 차감 같은 메인 write |
| `REQUIRES_NEW` | 별도 로컬 commit을 하나 더 만든다 | 감사 로그처럼 독립 DB 기록 |
| `NOT_SUPPORTED`를 굳이 안 써도 됨 | "외부 I/O는 tx 밖"이라는 구조만 먼저 지켜도 충분하다 | 느린 외부 호출을 메인 tx에 넣지 않는 기본 감각 |

중요한 경고:

- 외부 HTTP/gRPC 호출을 `REQUIRES_NEW` 메서드 안으로 옮겨도 본질은 해결되지 않는다.
- 해결 포인트는 "새 tx를 여는 것"이 아니라 "메인 tx에서 외부 대기를 제거하는 것"이다.

## `flush` 때문에 더 헷갈릴 때 짧게 정리

JPA를 쓰면 이런 오해가 붙는다.

- "`flush()`를 했으니 이제 결제 API를 불러도 안전하겠지?"

아니다.

- `flush`는 SQL을 DB로 밀어내는 시점일 뿐이다.
- 같은 트랜잭션이면 나중에 전체 rollback될 수 있다.
- 외부 결제 API는 그 rollback을 같이 따라오지 않는다.

그래서 `flush -> external API -> commit` 구조는 초보자가 생각하는 "거의 원자적" 상태가 아니다.
이 감각이 헷갈리면 [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)의 `flush는 commit이 아니다` 섹션을 같이 보면 된다.

## 자주 하는 질문 3개

### Q1. 외부 API를 꼭 먼저 호출해야 하면?

가능하면 **트랜잭션 시작 전에** 호출하고, 그 결과를 가지고 짧은 DB 트랜잭션을 연다.

다만 외부 승인 후 DB 저장이 실패할 수 있으므로, 이 경우는 rollback이 아니라 **취소 API/보상 작업**까지 같이 설계해야 한다.

이 장면을 payment 예시로 더 짧게 이어 보고 싶으면 [Spring Beginner Bridge: 외부 승인 성공 뒤 DB 저장이 실패하면 rollback보다 보상 + 멱등성으로 닫기](./spring-payment-approval-db-failure-compensation-idempotency-primer.md)를 보면 된다.

### Q2. `AFTER_COMMIT`이면 outbox 없이도 충분한가?

후속 알림이 빠져도 재전송 정도로 복구 가능하면 충분할 수 있다.
반대로 다른 서비스 계약상 유실이 더 치명적이면 outbox가 맞다.

### Q3. `REQUIRES_NEW`로 메시지 발행 성공 여부를 저장하면 되지 않나?

그건 "발행 성공/실패 기록"을 남기는 데는 쓸 수 있어도, **발행 자체의 전달 보장**을 대신하지는 못한다.

## 여기서 어디로 가면 되나

| 지금 더 필요한 것 | 다음 문서 |
|---|---|
| `@Transactional` 기본 그림이 먼저 필요하다 | [@Transactional 기초](./spring-transactional-basics.md) |
| `REQUIRED` / `REQUIRES_NEW` 차이를 먼저 더 짧게 잡고 싶다 | [Spring Transaction Propagation Beginner Primer](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md) |
| 외부 승인 성공 뒤 DB 저장 실패를 payment 보상/멱등성 관점으로 보고 싶다 | [Spring Beginner Bridge: 외부 승인 성공 뒤 DB 저장이 실패하면 rollback보다 보상 + 멱등성으로 닫기](./spring-payment-approval-db-failure-compensation-idempotency-primer.md) |
| 서비스 경계 자체를 어디에 둘지 더 넓게 보고 싶다 | [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md) |
| 이벤트 phase와 outbox 차이를 더 자세히 보고 싶다 | [Spring EventListener / TransactionalEventListener / Outbox](./spring-eventlistener-transaction-phase-outbox.md) |
| 코드리뷰에서 빠르게 냄새만 찾고 싶다 | [트랜잭션 경계 체크리스트 카드](../database/transaction-boundary-external-io-checklist-card.md) |
| `flush`와 commit 차이 때문에 헷갈린다 | [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md) |

## 한 줄 정리

초급자 기준으로는 "`REQUIRES_NEW`로 외부 API를 감쌀까?"보다, **메인 DB 트랜잭션은 짧게**, **커밋 뒤 반응은 `AFTER_COMMIT`**, **유실되면 안 되는 전달은 outbox**로 나누는 쪽이 정확하다.
