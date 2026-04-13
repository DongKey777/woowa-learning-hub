# Transaction Boundary Master Note

> 한 줄 요약: a transaction boundary is the line where a business invariant becomes durable, and everything outside that line must be treated as a side effect.

## 이 노트의 역할

이 노트는 `consistency` 군집의 **보조 노트**다.

- 먼저 [Consistency Boundary Master Note](./consistency-boundary-master-note.md)로 invariant와 eventual consistency의 큰 그림을 본다.
- 그 다음 이 노트에서 commit line, `afterCommit`, `REQUIRES_NEW`, multiple transaction manager 같은 **트랜잭션 경계 자체**를 깊게 본다.

**Difficulty: Advanced**

> retrieval-anchor-keywords: commit boundary, transactional boundary, propagation, REQUIRES_NEW, afterCommit, transaction synchronization, flush, long transaction, connection pool, outbox, saga pivot, multiple transaction manager, rollback rule

> related docs:
> - [@Transactional Deep Dive](../contents/spring/transactional-deep-dive.md)
> - [Spring Transaction Propagation: Nested / REQUIRES_NEW Case Studies](../contents/spring/spring-transaction-propagation-nested-requires-new-case-studies.md)
> - [Spring Transaction Synchronization / afterCommit Pitfalls](../contents/spring/spring-transaction-synchronization-aftercommit-pitfalls.md)
> - [Spring Multiple Transaction Managers / Qualifier Boundaries](../contents/spring/spring-multiple-transaction-managers-qualifier-boundaries.md)
> - [Transaction Case Studies](../contents/database/transaction-case-studies.md)
> - [Transaction Timeout vs Lock Timeout](../contents/database/transaction-timeout-vs-lock-timeout.md)
> - [Transaction Heartbeat / Long-Running Job Locking](../contents/database/transaction-heartbeat-long-running-job-locking.md)
> - [Spring Open Session in View Tradeoffs](../contents/spring/spring-open-session-in-view-tradeoffs.md)
> - [Spring EventListener / TransactionalEventListener / Outbox](../contents/spring/spring-eventlistener-transaction-phase-outbox.md)
> - [Saga Pivot Transaction Design](../contents/database/saga-pivot-transaction-design.md)
> - [Transactional Inbox / Dedup Design](../contents/database/transactional-inbox-dedup-design.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

A transaction boundary is not the same thing as `@Transactional`.

The annotation is just one way to express a boundary. The real question is:

- what must be atomic together
- what can safely happen after commit
- what must be isolated from rollback
- what must never live inside a long-running transaction

The boundary should follow the business invariant, not the convenience of the call stack.

## 깊이 들어가기

### 1. The boundary should wrap the invariant, not the whole workflow

If a business rule says "either inventory is reserved and payment is recorded, or neither is", that is the transaction boundary.

If the workflow also sends email, calls an external API, or emits analytics, those are side effects and usually belong outside the commit line.

### 2. `afterCommit` is where the handoff starts

Anything that must see committed data should run after commit:

- publish an event
- enqueue a job
- trigger a cache refresh
- notify another bounded context

Doing those inside the transaction makes the side effect part of the failure domain.

### 3. `REQUIRES_NEW` changes the boundary, not just the annotation

`REQUIRES_NEW` is useful when a smaller unit must survive the outer rollback:

- audit trails
- compensation records
- outbox writes that must not disappear with the business transaction

That is powerful, but it also makes reasoning harder because you now have multiple commit points.

### 4. Multiple transaction managers mean multiple boundaries

If one request touches two datasources, the apparent "single transaction" may actually be two separate local transactions.

That is where consistency bugs appear:

- one database commits and the other fails
- rollback rules are different
- propagation feels correct but the resource boundary is not

### 5. Long transactions are usually boundary mistakes

When network calls, heavy CPU work, or slow I/O happen inside a transaction:

- locks last longer
- pool slots stay occupied
- deadlocks become more likely
- retries hurt more

That is a sign the boundary is too wide.

## 실전 시나리오

### 시나리오 1: audit row survives even though the order rolled back

That is often a deliberate `REQUIRES_NEW` choice.

The question is not "why did it survive" but "was the survival intentional and documented?"

### 시나리오 2: a service call inside a transaction makes the pool exhaust

The transaction boundary is covering work that does not need atomicity.

Move remote calls outside the boundary and keep only local state changes inside it.

### 시나리오 3: an outbox message disappears with the business rollback

The outbox write is probably inside the wrong boundary, or it is in the wrong datasource.

### 시나리오 4: a batch job holds locks while waiting for another system

The job boundary and the DB boundary are not aligned.

Split the job into "load, decide, commit, hand off" phases.

## 코드로 보기

### Transactional boundary around the invariant

```java
@Service
public class OrderService {

    private final OrderRepository orderRepository;

    @Transactional
    public void placeOrder(PlaceOrderCommand command) {
        Order order = orderRepository.save(Order.create(command));
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                publishOrderCreated(order.getId());
            }
        });
    }
}
```

### Separate boundary for audit or outbox

```java
@Transactional
public void settlePayment(PaymentCommand command) {
    Payment payment = paymentRepository.save(Payment.of(command));
    outboxRepository.save(OutboxEvent.of("PAYMENT_SETTLED", payment.getId()));
}

@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void handlePaymentSettled(PaymentSettledEvent event) {
    notificationClient.notify(event.paymentId());
}
```

### A quick boundary check

```text
If rollback would make the side effect wrong, move the side effect out.
If rollback would make the domain state wrong, keep it inside.
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| One wide transaction | Easy local reasoning | Long locks and pool pressure | Small, bounded workflows |
| Narrow transaction + afterCommit | Better failure isolation | More orchestration | Event-driven and async handoff |
| `REQUIRES_NEW` | Independent commit | Harder mental model | Audit, outbox, compensation |
| Multiple local transactions | Scales better | Consistency work shifts to app | Multi-resource workflows |
| Open Session in View | Convenient lazy loading | Boundary becomes blurry | Legacy read-heavy web apps |

The decision is usually about which failure you are willing to own.

## 꼬리질문

> Q: Why is `@Transactional` not the same as a transaction boundary?
> Intent: checks whether the boundary is understood as a business decision.
> Core: the annotation is only one implementation detail of the boundary.

> Q: Why should side effects often happen after commit?
> Intent: checks failure-domain separation.
> Core: a rolled-back transaction must not have already triggered the real-world side effect.

> Q: When is `REQUIRES_NEW` a good idea?
> Intent: checks whether the candidate can name commit-separation cases.
> Core: audit, outbox, and compensation records are classic examples.

> Q: Why do long transactions often mean the boundary is wrong?
> Intent: checks lock and pool awareness.
> Core: the transaction is holding resources while doing work that does not need atomicity.

## 한 줄 정리

A good transaction boundary keeps only the invariant inside the commit line and pushes everything else into explicit post-commit work.
