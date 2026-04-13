# Replica Freshness Master Note

> 한 줄 요약: replica freshness is about deciding when a read can tolerate lag and when it must fall back to a source of truth.

**Difficulty: Advanced**

> retrieval-anchor-keywords: replica freshness, read-after-write, lag, primary fallback, sticky session, version token, stale read, replication delay, freshness budget, consistency window

> related docs:
> - [Replica lag / Read-after-write strategies](../contents/database/replica-lag-read-after-write-strategies.md)
> - [Cache Consistency Master Note](./cache-consistency-master-note.md)
> - [Distributed Cache Design](../contents/system-design/distributed-cache-design.md)
> - [authorization caching staleness](../contents/security/authorization-caching-staleness.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Replica freshness is not a property you "have".
It is a budget you spend.

Reads can go to replica only if the business can tolerate the lag window.
Otherwise the system needs:

- primary fallback
- session stickiness
- version routing
- or strict read path control

## 깊이 들어가기

### 1. Replica lag comes from the apply path

The replica may be behind because of log apply, network, or long transactions.

Read with:

- [Replica lag / Read-after-write strategies](../contents/database/replica-lag-read-after-write-strategies.md)

### 2. Freshness budgets vary by endpoint

Login, payment, and admin screens usually need tighter freshness than analytics or browsing pages.

### 3. Cache can hide lag until the user notices

If a cache holds the same stale value, the lag is harder to detect.

Read with:

- [Cache Consistency Master Note](./cache-consistency-master-note.md)

### 4. Authorization state can also be stale

Permission changes often need fresher reads than ordinary content.

Read with:

- [Authorization Caching Staleness](../contents/security/authorization-caching-staleness.md)

## 실전 시나리오

### 시나리오 1: order appears missing right after create

Likely cause:

- replica lag
- read path not routed to primary after write

### 시나리오 2: admin revocation is delayed

Likely cause:

- stale auth cache
- replica freshness too loose

### 시나리오 3: report page is fine but checkout page is not

Likely cause:

- freshness budget differs by endpoint and should be routed differently

## 코드로 보기

### Freshness-aware routing

```text
if recent_write_in_session:
    read from primary
else:
    read from replica
```

### Version token sketch

```java
if (request.version() < currentVersion()) {
    usePrimary();
}
```

### Fallback guard

```java
if (replicaLagTooHigh()) {
    routeToPrimary();
}
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Replica read | Scales reads | Lag risk | Browse-heavy paths |
| Primary fallback | Freshness | Load increase | Critical actions |
| Session sticky | Simple consistency | Uneven load | User-centric apps |
| Version routing | Precise | More complexity | High-value read paths |

## 꼬리질문

> Q: Why is replica freshness a budget?
> Intent: checks lag tolerance reasoning.
> Core: you choose where staleness is acceptable and where it is not.

> Q: Why do different pages need different freshness?
> Intent: checks product/consistency mapping.
> Core: admin and checkout are more sensitive than browse and analytics.

> Q: Why can cache and replica lag combine badly?
> Intent: checks multi-layer staleness.
> Core: stale cache plus stale replica makes the freshness window larger.

## 한 줄 정리

Replica freshness is the routing decision that keeps lag within a tolerated window and falls back to truth when the window is too risky.
