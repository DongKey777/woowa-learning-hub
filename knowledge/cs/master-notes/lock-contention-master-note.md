# Lock Contention Master Note

> 한 줄 요약: lock contention is what happens when too many operations compete for the same protected state and the wait becomes the bottleneck.

**Difficulty: Advanced**

> retrieval-anchor-keywords: lock contention, lock wait, deadlock, gap lock, next-key lock, hotspot row, critical section, optimistic lock, pessimistic lock, throughput collapse, tail latency

> related docs:
> - [트랜잭션 격리수준과 락](../contents/database/transaction-isolation-locking.md)
> - [Deadlock Case Study](../contents/database/deadlock-case-study.md)
> - [Gap Lock과 Next-Key Lock](../contents/database/gap-lock-next-key-lock.md)
> - [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md)
> - [Query Tuning Checklist](../contents/database/query-tuning-checklist.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Lock contention is not just "many threads".
It is "many operations need the same exclusive access".

The bottleneck can be:

- one row
- one index range
- one cached object
- one executor lock
- one resource pool

## 깊이 들어가기

### 1. Hotspots create queues

If every request needs the same row or range, throughput becomes wait-time bound.

### 2. Lock wait is different from query time

A query can be syntactically fast but operationally slow because it is blocked on a lock.

Read with:

- [트랜잭션 격리수준과 락](../contents/database/transaction-isolation-locking.md)

### 3. Deadlock is contention plus ordering failure

Read with:

- [Deadlock Case Study](../contents/database/deadlock-case-study.md)

### 4. Range locks expand contention

Read with:

- [Gap Lock과 Next-Key Lock](../contents/database/gap-lock-next-key-lock.md)

### 5. Transaction scope makes contention worse

Long transaction boundaries hold locks longer and increase queue depth.

Read with:

- [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md)

## 실전 시나리오

### 시나리오 1: one stock row becomes the bottleneck

Likely cause:

- hotspot row
- pessimistic locking on every request

### 시나리오 2: throughput drops after adding a range query

Likely cause:

- gap or next-key lock
- wider critical section

### 시나리오 3: lock wait time rises but CPU stays moderate

Likely cause:

- queueing on contention, not compute

## 코드로 보기

### Lock hotspot sketch

```text
single row -> many writers -> serial queue -> p99 spike
```

### Optimistic conflict

```java
if (!entity.versionMatches(expectedVersion)) {
    throw new OptimisticLockException();
}
```

### Pessimistic lock

```java
repository.findByIdForUpdate(id);
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Optimistic lock | High concurrency | Retry on conflict | Low-contention writes |
| Pessimistic lock | Strong protection | More waiting | Hot critical data |
| Range lock | Protects invariants | Broad contention | Sequence or uniqueness rules |
| Shard the hotspot | Removes contention | More complexity | Scale-out hotspot paths |

## 꼬리질문

> Q: Why can low CPU still mean a lock problem?
> Intent: checks wait-vs-work understanding.
> Core: threads can be blocked, not computing.

> Q: Why do range locks increase contention?
> Intent: checks gap/next-key awareness.
> Core: the lock covers more than a single row.

> Q: When does optimistic locking fail?
> Intent: checks conflict and retry reasoning.
> Core: it fails when write conflicts are frequent and retries pile up.

## 한 줄 정리

Lock contention is the throughput collapse caused by too many operations waiting on the same protected state, and the fix is to narrow, shard, or redesign the critical section.
