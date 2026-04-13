# Eventual Consistency Master Note

> 한 줄 요약: eventual consistency is the practical agreement that some data will be stale for a while, so the system must make that staleness visible, bounded, and safe to recover from.

## 이 노트의 역할

이 노트는 `consistency` 군집의 **보조 노트**다.

- 먼저 [Consistency Boundary Master Note](./consistency-boundary-master-note.md)로 어떤 경계를 동기적으로 지켜야 하는지 본다.
- 그 다음 이 노트에서 replica lag, monotonic reads, backfill, replay, reconciliation 같은 **수렴 과정**을 깊게 본다.

**Difficulty: Advanced**

> retrieval-anchor-keywords: eventual consistency, read-your-writes, monotonic reads, replica lag, stale read, session pinning, projection lag, outbox, backfill, reconciliation, read routing, freshness watermark, idempotent replay

> related docs:
> - [Outbox, Saga, Eventual Consistency](../contents/database/outbox-saga-eventual-consistency.md)
> - [Replica Lag / Read After Write Strategies](../contents/database/replica-lag-read-after-write-strategies.md)
> - [Read Your Writes / Session Pinning](../contents/database/read-your-writes-session-pinning.md)
> - [Monotonic Reads / Session Guarantees](../contents/database/monotonic-reads-session-guarantees.md)
> - [Replica Lag Observability / Routing / SLO](../contents/database/replica-lag-observability-routing-slo.md)
> - [Replica Read Routing Anomalies](../contents/database/replica-read-routing-anomalies.md)
> - [Cache / Replica Split Read Inconsistency](../contents/database/cache-replica-split-read-inconsistency.md)
> - [Online Backfill Consistency](../contents/database/online-backfill-consistency.md)
> - [Saga Reservation Consistency](../contents/database/saga-reservation-consistency.md)
> - [Transactional Inbox / Dedup Design](../contents/database/transactional-inbox-dedup-design.md)
> - [Distributed Uniqueness / ID Allocation Consistency](../contents/database/distributed-uniqueness-id-allocation-consistency.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
> - [Retrieval Failure Modes](../rag/retrieval-failure-modes.md)

## 핵심 개념

Eventual consistency is not "it will maybe fix itself".

It is a design promise with three parts:

- the data may be stale for a window
- the staleness window should be understood
- the system should provide a way to converge safely

That promise matters because most real systems cannot afford synchronous global consistency for every write.

## 깊이 들어가기

### 1. Staleness comes from several places

The user sees old data because of different causes:

- replica lag
- async projection lag
- cache TTL
- delayed invalidation
- backfill or replay jobs
- failover rerouting

If you do not identify the source, you cannot choose the right remedy.

### 2. Session guarantees are the user-facing part of consistency

Users usually care less about "strong vs weak" and more about things like:

- if I just wrote it, can I see it?
- if I saw a newer value once, can I go backwards?
- if I refresh, will I lose the thing I just changed?

That is why read-your-writes and monotonic reads matter.

### 3. The system needs a freshness strategy

Common strategies:

- pin the session to the primary after a write
- add a freshness watermark to reads
- route known-sensitive reads away from lagging replicas
- surface stale state explicitly in the UI

This is better than pretending all reads are equally fresh.

### 4. Reconciliation is part of the contract

Eventual consistency is safe only when the system can converge.

That usually means:

- idempotent replay
- deduplication
- outbox or inbox records
- periodic reconciliation jobs

Without a reconciliation path, "eventual" becomes "hopeful".

### 5. Backfill and replay can look like bugs

During migration or batch backfill, stale or partially updated views are expected.

The important part is to isolate the blast radius:

- mark the data as rebuilding
- keep read paths aware of version
- avoid mixing old and new projections without a fence

## 실전 시나리오

### 시나리오 1: I just created an order, but the list page does not show it

Possible causes:

- the list page is reading from a lagging replica
- the search index has not caught up
- the cache still serves the old version

The fix is usually session pinning or a freshness-aware read path.

### 시나리오 2: a user refreshes and sees older data than before

That violates monotonic reads.

The system should avoid routing the user to a worse version than the one already observed.

### 시나리오 3: a backfill job produces temporary inconsistencies

That is acceptable only if the read path knows the dataset is in transition.

### 시나리오 4: a failover makes reads suddenly look "wrong"

The new primary may have a different snapshot horizon than the old one.

This is why failover and consistency need to be discussed together.

## 코드로 보기

### Freshness-aware read routing

```java
public OrderView loadOrder(Long orderId, FreshnessHint hint) {
    if (hint.requireReadYourWrites()) {
        return primaryOrderReadRepository.findById(orderId);
    }
    return replicaOrderReadRepository.findById(orderId);
}
```

### Session pinning sketch

```java
public void markSessionFresh(HttpSession session, Instant writeTime) {
    session.setAttribute("freshnessWatermark", writeTime);
}

public boolean canUseReplica(HttpSession session, Instant replicaLagCutoff) {
    Instant watermark = (Instant) session.getAttribute("freshnessWatermark");
    return watermark == null || !watermark.isAfter(replicaLagCutoff);
}
```

### Reconciliation loop

```text
1. write the source of truth
2. emit the change event
3. rebuild the projection
4. compare source and projection
5. repair mismatches idempotently
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Strong consistency | Simple mental model | Higher latency and coordination cost | Small critical writes |
| Eventual consistency | Better availability and scale | Temporary staleness | Read-heavy, distributed systems |
| Session pinning | Better user perception | More routing complexity | Post-write user flows |
| Explicit freshness watermark | Safer than blind reads | More app logic | Sensitive read-after-write paths |
| Reconciliation jobs | Long-term correctness | Operational overhead | Projections and derived views |

The main question is how much staleness the business can tolerate before the user experience becomes incorrect.

## 꼬리질문

> Q: What is the difference between replica lag and eventual consistency?
> Intent: checks whether lag is understood as one cause, not the whole model.
> Core: replica lag is one source of staleness inside a broader eventual-consistency design.

> Q: Why do read-your-writes and monotonic reads matter?
> Intent: checks user-visible session guarantees.
> Core: they prevent the system from showing a user older state than what they already observed.

> Q: Why is reconciliation required?
> Intent: checks convergence thinking.
> Core: eventual consistency only works if the system can detect and repair divergence.

> Q: Why can backfill create consistency bugs?
> Intent: checks transition-state awareness.
> Core: old and new versions can coexist unless the read path understands the migration fence.

## 한 줄 정리

Eventual consistency is safe only when the system can explain its staleness, bound it for users, and converge it with replay and reconciliation.
