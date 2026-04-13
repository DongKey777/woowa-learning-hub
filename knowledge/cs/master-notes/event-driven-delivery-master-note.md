# Event-Driven Delivery Master Note

> 한 줄 요약: event-driven delivery is about moving work safely across time, process boundaries, and failure modes without losing the business fact.

**Difficulty: Advanced**

> retrieval-anchor-keywords: outbox, inbox, at-least-once, idempotent consumer, delivery semantics, replay, dead letter queue, ordering, duplicate event, transactional event listener, broker outage, eventual consistency, correlation id

> related docs:
> - [Domain Events, Outbox, Inbox](../contents/software-engineering/outbox-inbox-domain-events.md)
> - [Spring EventListener, TransactionalEventListener, and Outbox](../contents/spring/spring-eventlistener-transaction-phase-outbox.md)
> - [Outbox, Saga, Eventual Consistency](../contents/database/outbox-saga-eventual-consistency.md)
> - [cache, message, observability](../contents/software-engineering/cache-message-observability.md)
> - [Idempotency Key and Deduplication](../contents/database/idempotency-key-and-deduplication.md)
> - [Workflow Orchestration / Saga Design](../contents/system-design/workflow-orchestration-saga-design.md)
> - [API Design / Error Handling](../contents/software-engineering/api-design-error-handling.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

Event-driven delivery is not "send a message and hope".

It is a delivery contract that says:

- what happened
- when it is safe to publish
- how duplicates are handled
- how failures are retried
- who owns ordering and reconciliation

Delivery semantics matter more than broker branding.

## 깊이 들어가기

### 1. The event is a fact, not a command

The business fact should survive delivery changes.

- `OrderPlaced`
- `PaymentApproved`
- `StockReserved`

These are facts.

Commands like `SendEmailNow` are not facts.

### 2. Outbox turns delivery into a recoverable process

If you publish after commit without outbox, a process crash can lose the event.

Outbox makes the DB record and the event record commit together.

Read with:

- [Domain Events, Outbox, Inbox](../contents/software-engineering/outbox-inbox-domain-events.md)
- [Spring EventListener, TransactionalEventListener, and Outbox](../contents/spring/spring-eventlistener-transaction-phase-outbox.md)

### 3. Inbox makes consumers safe under replay

At-least-once delivery means duplicates are normal.

Inbox or dedupe storage lets consumers safely ignore repeats.

Read with:

- [Idempotency Key and Deduplication](../contents/database/idempotency-key-and-deduplication.md)

### 4. Ordering is local, not global

Global ordering is expensive and often unnecessary.

Usually the right question is:

- what must be ordered?
- by which key?
- what happens if ordering is lost?

That choice should be explicit in the event design.

## 실전 시나리오

### 시나리오 1: broker outage after DB commit

Without outbox, the event can disappear.
With outbox, the relay can retry later.

### 시나리오 2: consumer processes the same message twice

Without dedupe, side effects duplicate.
With inbox or idempotent handlers, the duplicate is harmless.

### 시나리오 3: event schema changes break old consumers

The problem is contract compatibility, not only serialization.

### 시나리오 4: downstream service is slow

If delivery is synchronous, the upstream path slows down.
If delivery is async, retries and DLQ policy matter more.

## 코드로 보기

### Outbox record sketch

```java
@Transactional
public void placeOrder(OrderCommand command) {
    Order order = orderRepository.save(Order.create(command));
    outboxRepository.save(OutboxEvent.of("OrderPlaced", order.getId()));
}
```

### Idempotent consumer sketch

```java
public void handle(EventEnvelope envelope) {
    if (processedEventRepository.existsByEventId(envelope.eventId())) {
        return;
    }
    domainService.apply(envelope);
    processedEventRepository.save(new ProcessedEvent(envelope.eventId()));
}
```

### Correlation-friendly envelope

```java
public record EventEnvelope(
    String eventId,
    String eventType,
    String correlationId,
    String causationId,
    Instant occurredAt,
    Map<String, Object> payload
) {}
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Synchronous call | Simple to reason about | Tight coupling | Small, critical flows |
| Async event | Loose coupling | Eventual consistency | Fan-out or cross-service work |
| Outbox | Durable publish path | More components | Production-grade delivery |
| Inbox | Safe retries | Extra storage | At-least-once consumers |
| DLQ | Failure isolation | Manual recovery | Poison messages or persistent errors |

## 꼬리질문

> Q: Why is at-least-once the normal delivery model?
> Intent: checks distributed failure realism.
> Core: brokers prefer retrying over dropping messages.

> Q: Why do we need an outbox if the database commit succeeded?
> Intent: checks commit-publish gap awareness.
> Core: the process may fail before publish.

> Q: Why is ordering hard in event systems?
> Intent: checks key-scoped ordering understanding.
> Core: ordering is usually only guaranteed within a partition or key.

> Q: Why is idempotency a consumer concern too?
> Intent: checks end-to-end reliability.
> Core: duplicates can happen regardless of the broker.

## 한 줄 정리

Event-driven delivery is safe only when publication, replay, and duplicate handling are designed as one reliability path.
