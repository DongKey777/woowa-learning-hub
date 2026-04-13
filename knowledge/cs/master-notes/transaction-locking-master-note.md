# Transaction Locking Master Note

> 한 줄 요약: transaction locking is about protecting invariants under concurrency while avoiding deadlocks, long waits, and accidental over-locking.

**Difficulty: Advanced**

> retrieval-anchor-keywords: isolation level, lock wait, deadlock, gap lock, next-key lock, phantom read, write skew, SELECT FOR UPDATE, optimistic lock, pessimistic lock, rollback, lock timeout

> related docs:
> - [Transaction Isolation and Locking](../contents/database/transaction-isolation-locking.md)
> - [Deadlock Case Study](../contents/database/deadlock-case-study.md)
> - [Gap Lock and Next-Key Lock](../contents/database/gap-lock-next-key-lock.md)
> - [Write Skew / Phantom Read Case Studies](../contents/database/write-skew-phantom-read-case-studies.md)
> - [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md)
> - [Connection Pool / Transaction Propagation / Bulk Write](../contents/database/connection-pool-transaction-propagation-bulk-write.md)
> - [Query Tuning Checklist](../contents/database/query-tuning-checklist.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Locking is not just "prevent concurrent writes."
It is a policy for preserving invariants when two transactions want incompatible views of the same state.

The main question is not whether to lock.
It is:

- what must be serialized
- at what scope
- for how long
- and with what retry behavior

## 깊이 들어가기

### 1. Isolation and locking are linked

The isolation level tells you what anomalies are acceptable.
The lock strategy tells you how the database enforces that contract.

Read with:

- [Transaction Isolation and Locking](../contents/database/transaction-isolation-locking.md)

### 2. Gap and next-key locks protect ranges, not just rows

Range-based invariants often need more than row-level locking.
This is why a `SELECT ... FOR UPDATE` can block inserts in adjacent ranges.

Read with:

- [Gap Lock and Next-Key Lock](../contents/database/gap-lock-next-key-lock.md)

### 3. Deadlock is a lock-ordering problem

Deadlock is usually not "DB is broken."
It is "two code paths lock the same resources in different orders."

Read with:

- [Deadlock Case Study](../contents/database/deadlock-case-study.md)

### 4. Long transactions make locks expensive

The longer a transaction stays open, the longer it blocks everyone else.
That is why app-layer transaction boundaries and DB lock behavior must be designed together.

Read with:

- [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md)
- [Connection Pool / Transaction Propagation / Bulk Write](../contents/database/connection-pool-transaction-propagation-bulk-write.md)

## 실전 시나리오

### 시나리오 1: stock reservation blocks inserts

Likely cause:

- range lock over the seat or stock interval
- index choice widening the lock

### 시나리오 2: deadlock appears after a new code path

Likely cause:

- lock order changed
- batch and online traffic overlap

### 시나리오 3: lock wait grows but query itself looks fast

Likely cause:

- connection pool starvation
- transaction is waiting, not executing

## 코드로 보기

### Pessimistic lock

```java
@Transactional
public void reserveStock(Long productId, int quantity) {
    Product product = productRepository.findByIdForUpdate(productId);
    product.reserve(quantity);
}
```

### Lock-order discipline

```text
1. sort ids
2. lock in ascending order
3. update
4. commit quickly
```

### Retry on lock conflict

```java
for (int attempt = 1; attempt <= 3; attempt++) {
    try {
        service.reserve();
        break;
    } catch (DeadlockLoserDataAccessException e) {
        backoff(attempt);
    }
}
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Row lock | Narrow protection | Misses range invariants | Simple point updates |
| Range lock | Protects gaps | More blocking | Inventory, scheduling, uniqueness |
| Optimistic lock | Less waiting | Retry complexity | Low-conflict writes |
| Pessimistic lock | Stronger safety | More contention | High-value critical section |

## 꼬리질문

> Q: Why can a query be fast but the transaction still be slow?
> Intent: checks queueing and lock wait separation.
> Core: the system can spend time waiting for locks or connections.

> Q: Why do gap locks exist?
> Intent: checks range-consistency understanding.
> Core: they help protect invariants that span empty key ranges.

> Q: Why is deadlock often solved by retry?
> Intent: checks operational resilience.
> Core: the database may choose one victim and the application must safely replay it.

## 한 줄 정리

Transaction locking is the art of making concurrent invariants safe without turning your database into a permanently waiting queue.
