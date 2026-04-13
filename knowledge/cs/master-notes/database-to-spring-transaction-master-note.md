# Database to Spring Transaction Master Note

> 한 줄 요약: Spring transactions are the control plane, but the real correctness boundary still lives in the database, the connection pool, and the transaction isolation model.

**Difficulty: Advanced**

> retrieval-anchor-keywords: @Transactional, proxy, propagation, isolation level, flush, dirty checking, rollback, REQUIRES_NEW, connection pool starvation, deadlock, gap lock, next-key lock, transaction synchronization, outbox

> related docs:
> - [@Transactional Deep Dive](../contents/spring/transactional-deep-dive.md)
> - [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md)
> - [JDBC / JPA / MyBatis](../contents/database/jdbc-jpa-mybatis.md)
> - [JDBC code patterns](../contents/database/jdbc-code-patterns.md)
> - [Transaction Isolation and Locking](../contents/database/transaction-isolation-locking.md)
> - [Gap Lock / Next-Key Lock](../contents/database/gap-lock-next-key-lock.md)
> - [Deadlock Case Study](../contents/database/deadlock-case-study.md)
> - [Connection Pool / Transaction Propagation / Bulk Write](../contents/database/connection-pool-transaction-propagation-bulk-write.md)
> - [Spring EventListener, TransactionalEventListener, and Outbox](../contents/spring/spring-eventlistener-transaction-phase-outbox.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

The Spring transaction annotation is not the transaction itself.

It coordinates:

- when a connection is borrowed
- when flush happens
- when commit or rollback happens
- how nested calls behave

The database still decides:

- what isolation means
- what lock is taken
- whether the write conflicts
- whether the commit succeeds

The connection pool still decides:

- whether the app can even begin another transaction
- how long callers wait
- whether nested work exhausts resources

## 깊이 들어가기

### 1. Proxy, not magic

`@Transactional` usually works through a proxy.

That means:

- self-invocation can bypass it
- private methods do not behave like public proxied entry points
- `new` objects are not managed

This is why the debugging playbook matters:

- [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md)
- [AOP and Proxy Mechanism](../contents/spring/aop-proxy-mechanism.md)

### 2. Flush is not commit

JPA can flush SQL before commit.
So a failure may show up earlier than expected.

This matters when:

- unique constraints are violated
- foreign keys fail
- write order matters

### 3. Isolation level is the real concurrency contract

The database docs are essential here:

- [Transaction Isolation and Locking](../contents/database/transaction-isolation-locking.md)
- [Write Skew / Phantom Read Case Studies](../contents/database/write-skew-phantom-read-case-studies.md)
- [Gap Lock / Next-Key Lock](../contents/database/gap-lock-next-key-lock.md)

Without those, Spring transaction settings are just labels.

### 4. Long transactions turn into pool and lock problems

If you keep a transaction open while doing network calls or slow queries:

- the lock lasts longer
- the connection stays borrowed
- unrelated requests may wait behind it

This is where DB and Spring meet:

- [Slow Query Analysis Playbook](../contents/database/slow-query-analysis-playbook.md)
- [Connection Pool / Transaction Propagation / Bulk Write](../contents/database/connection-pool-transaction-propagation-bulk-write.md)

## 실전 시나리오

### 시나리오 1: checked exception did not roll back

Usually the issue is not the DB.
It is the rollback rule.

### 시나리오 2: `REQUIRES_NEW` made audit logs survive but the business operation failed

That may be correct or wrong.
The point is that the commit boundary changed.

### 시나리오 3: pool exhaustion appears under bulk writes

Likely causes:

- too many concurrent transactions
- long-running locks
- nested propagation creating more checkout pressure

### 시나리오 4: deadlock appears after a schema or query change

Likely causes:

- new lock order
- wider range scan
- missing index
- hot rows now collide more often

## 코드로 보기

### Transactional service with clear boundary

```java
@Service
public class PaymentService {

    private final PaymentRepository paymentRepository;

    @Transactional
    public void pay(PayCommand command) {
        Payment payment = paymentRepository.findByIdForUpdate(command.paymentId());
        payment.markPaid();
    }
}
```

### Outbox at the same commit boundary

```java
@Transactional
public void placeOrder(OrderCommand command) {
    Order order = orderRepository.save(Order.create(command));
    outboxRepository.save(OutboxEvent.of("ORDER_CREATED", order.getId()));
}
```

The application boundary and DB boundary are aligned here.

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| One large transaction | Easy to reason about locally | Locks and contention grow | Small, bounded workflows |
| Smaller transactions | Less blocking | More consistency work | Distributed flows |
| `REQUIRES_NEW` | Commit separation | Harder reasoning | Audit and side records |
| JPA flush + commit discipline | Cleaner abstraction | Surprise SQL timing | Domain-centric app code |
| JDBC direct control | Exact SQL timing | More boilerplate | Performance-sensitive paths |

## 꼬리질문

> Q: Why is `@Transactional` sometimes ineffective?
> Intent: checks proxy and invocation-path understanding.
> Core: the annotation only works when the call crosses the managed proxy boundary.

> Q: Why is flush different from commit?
> Intent: checks ORM and database timing separation.
> Core: flush sends SQL; commit finalizes the transaction.

> Q: Why can a transaction be slow even before the database is slow?
> Intent: checks pool and lock-awareness.
> Core: waiting for a connection or lock is still transaction time.

> Q: Why do isolation-level bugs often look like business bugs?
> Intent: checks correctness boundary thinking.
> Core: the failure is in concurrent visibility, not just in SQL syntax.

## 한 줄 정리

Spring transaction work is really about aligning proxy behavior, DB isolation, and connection management around the same business boundary.
