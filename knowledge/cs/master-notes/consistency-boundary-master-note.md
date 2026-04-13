# Consistency Boundary Master Note

> 한 줄 요약: a consistency boundary is the smallest scope in which an invariant must hold synchronously, and everything outside it can relax into eventual consistency.

## 이 노트의 역할

이 노트는 `consistency` 군집의 **대표 노트**다.

- 먼저 이 노트로 strong consistency와 eventual consistency의 경계를 잡는다.
- 트랜잭션 commit line 자체를 더 깊게 보려면 [Transaction Boundary Master Note](./transaction-boundary-master-note.md)를 이어서 본다.
- stale read, replica lag, convergence 관점을 더 깊게 보려면 [Eventual Consistency Master Note](./eventual-consistency-master-note.md)를 이어서 본다.

**Difficulty: Advanced**

> retrieval-anchor-keywords: consistency boundary, write skew, phantom read, isolation level, aggregate, transactional boundary, read-your-writes, stale read, outbox, saga, idempotency, cross-service invariant, cache invalidation, replica lag

> related docs:
> - [Transaction Isolation and Locking](../contents/database/transaction-isolation-locking.md)
> - [Write Skew / Phantom Read Case Studies](../contents/database/write-skew-phantom-read-case-studies.md)
> - [DDD Hexagonal Consistency](../contents/software-engineering/ddd-hexagonal-consistency.md)
> - [Outbox, Saga, Eventual Consistency](../contents/database/outbox-saga-eventual-consistency.md)
> - [Idempotency, Retry, Consistency Boundaries](../contents/software-engineering/idempotency-retry-consistency-boundaries.md)
> - [Distributed Cache Design](../contents/system-design/distributed-cache-design.md)
> - [Payment System Ledger / Idempotency / Reconciliation](../contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

The key mistake is to treat all consistency problems as database problems.

In reality, a consistency boundary can be:

- one row
- one aggregate
- one transaction
- one cache key
- one message
- one business workflow

The boundary is the place where you promise:

- invariants are checked together
- conflicting updates are serialized or rejected
- the user sees a coherent state

Outside the boundary, you usually trade strong consistency for availability, scale, or simpler operations.

## 깊이 들어가기

### 1. Local invariant vs global invariant

Local invariant:

- stock cannot go below zero
- account balance cannot be negative
- an order cannot be paid twice

Global invariant:

- inventory, payment, and shipping all match eventually
- cache, replica, and primary converge
- downstream service eventually receives the same business event

Local invariants belong in one boundary.
Global invariants usually need choreography, saga, or reconciliation.

### 2. Why the database is not the whole answer

Database isolation can protect one transaction boundary, but not the whole workflow.

That is why we pair:

- [Transaction Isolation and Locking](../contents/database/transaction-isolation-locking.md)
- [Outbox, Saga, Eventual Consistency](../contents/database/outbox-saga-eventual-consistency.md)
- [Spring EventListener, TransactionalEventListener, Outbox](../contents/spring/spring-eventlistener-transaction-phase-outbox.md)

The DB makes one state transition safe.
The workflow design makes many transitions eventually correct.

### 3. Replica lag and cache are also boundaries

If a read comes from:

- a replica
- a cache
- a denormalized projection

then the boundary is no longer the primary database.

That means we must define what staleness is acceptable and where read-your-writes matters.

Useful companions:

- [Distributed Cache Design](../contents/system-design/distributed-cache-design.md)
- [Replica lag / read-after-write strategies](../contents/database/replica-lag-read-after-write-strategies.md)
- [Cache message observability](../contents/software-engineering/cache-message-observability.md)

### 4. Cross-service invariants need compensation

Once the invariant spans services, distributed locking is usually the wrong default.

Typical options:

- accept eventual consistency
- split the invariant and enforce parts locally
- add a saga with compensation
- add reconciliation and alerting

## 실전 시나리오

### 시나리오 1: stock reserve and payment

You want:

- reserve inventory once
- charge once
- avoid overselling

The synchronous boundary is usually `reserve` or `payment intent`, not the whole checkout flow.

### 시나리오 2: cache says old value, DB says new value

The invariant is no longer just in the DB.
You need to define:

- how stale the cache may be
- which fields can be stale
- whether the user needs immediate freshness

### 시나리오 3: write skew appears under concurrency

This is the classic sign that the boundary is too weak.
Read the case study together with the isolation docs:

- [Write Skew / Phantom Read Case Studies](../contents/database/write-skew-phantom-read-case-studies.md)
- [Transaction Isolation and Locking](../contents/database/transaction-isolation-locking.md)

### 시나리오 4: payment succeeded but shipping failed

This is not only a failure.
It is a boundary definition problem.

You likely need:

- idempotent step execution
- compensation
- reconciliation

## 코드로 보기

### One invariant, one transaction

```java
@Transactional
public void reserveAndRecord(long productId, int quantity) {
    Product product = productRepository.findByIdForUpdate(productId);
    product.reserve(quantity);
    inventoryEventRepository.save(new InventoryEvent(productId, quantity));
}
```

### Boundary extension with outbox

```java
@Transactional
public void placeOrder(OrderCommand command) {
    Order order = orderRepository.save(Order.create(command));
    outboxRepository.save(OutboxEvent.from(order));
}
```

The transaction protects the local invariant.
The outbox extends the boundary safely into async delivery.

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Strong local boundary | Simple correctness | Lower concurrency | Money, stock, ledger |
| Eventual workflow boundary | Better scale | Harder reasoning | Cross-service process |
| Cache-backed read model | Fast reads | Stale data risk | Read-heavy UIs |
| Saga / compensation | No distributed tx | More code paths | Multi-step business flow |
| Reconciliation | Operational safety net | Delayed detection | Payment, fulfillment, audit |

## 꼬리질문

> Q: What is the difference between a transaction boundary and a consistency boundary?
> Intent: checks whether the candidate can separate DB mechanics from business correctness.
> Core: a transaction is a mechanism; the boundary is the invariant scope.

> Q: Why is write skew a boundary problem?
> Intent: checks concurrency semantics.
> Core: two transactions each see a locally valid state, but the combined effect breaks the invariant.

> Q: Why does caching force us to think about consistency again?
> Intent: checks read-model staleness awareness.
> Core: the read path may no longer observe the primary state immediately.

> Q: When should we use saga instead of a larger transaction?
> Intent: checks distributed workflow judgment.
> Core: when the invariant spans services or slow external systems.

## 한 줄 정리

Consistency boundaries tell us where to be strict, where to relax, and where to compensate when the system crosses a domain edge.
