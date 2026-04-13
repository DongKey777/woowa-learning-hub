# Caching Invalidation Master Note

> 한 줄 요약: cache design succeeds when we define what can be stale, what must be fresh, and who is responsible for removing bad data when the truth changes.

**Difficulty: Advanced**

> retrieval-anchor-keywords: cache invalidation, stale read, cache-aside, write-through, write-behind, TTL, jitter, hot key, stampede, warm-up, versioned key, stale-while-revalidate, read-after-write, CDN, local cache

> related docs:
> - [Distributed Cache Design](../contents/system-design/distributed-cache-design.md)
> - [Spring Cache Abstraction Traps](../contents/spring/spring-cache-abstraction-traps.md)
> - [Cache-Control Practical](../contents/network/cache-control-practical.md)
> - [cache message observability](../contents/software-engineering/cache-message-observability.md)
> - [Replica lag / read-after-write strategies](../contents/database/replica-lag-read-after-write-strategies.md)
> - [Idempotency, Retry, Consistency Boundaries](../contents/software-engineering/idempotency-retry-consistency-boundaries.md)
> - [DNS TTL Cache Failure Patterns](../contents/network/dns-ttl-cache-failure-patterns.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
> - [Retrieval Anchor Keywords](../rag/retrieval-anchor-keywords.md)

## 핵심 개념

Caching is a consistency boundary with a failure mode.

If the cached value is wrong, the system can be:

- fast and wrong
- stale but acceptable
- fresh enough after a short delay
- instantly consistent only for a narrow scope

The right caching strategy begins with one question:

- What exact staleness is acceptable for this read path?

## 깊이 들어가기

### 1. Cache-aside is simple but not free

Cache-aside is popular because the application controls read-through and write invalidation.

It fails when:

- invalidation is missed
- TTL is too long
- two writers race
- many keys expire at once

Use with:

- [Distributed Cache Design](../contents/system-design/distributed-cache-design.md)
- [cache message observability](../contents/software-engineering/cache-message-observability.md)

### 2. Write-through and write-behind change the tradeoff

Write-through gives more immediate coherence.
Write-behind improves write latency but increases recovery complexity.

That is why this is not just a cache question.
It is a durability and recovery question too.

### 3. TTL is a policy, not a solution

TTL is useful when:

- freshness can be approximate
- invalidation paths are hard
- the business can tolerate short staleness

TTL is weak when:

- reads must reflect writes immediately
- price or permission data changes frequently
- stale values can cause financial or security bugs

### 4. Stale data often comes from another boundary

If a write hits the primary DB but the read comes from:

- a replica
- a CDN
- a local cache
- a Spring cache layer

then invalidation and replication delay matter as much as the cache itself.

Read with:

- [Replica lag / read-after-write strategies](../contents/database/replica-lag-read-after-write-strategies.md)
- [Cache-Control Practical](../contents/network/cache-control-practical.md)
- [Spring Cache Abstraction Traps](../contents/spring/spring-cache-abstraction-traps.md)

## 실전 시나리오

### 시나리오 1: profile changed but the screen shows the old value

Likely cause:

- cache key not invalidated
- replica lag
- CDN still serving the old object

### 시나리오 2: hot key melts the cache node

Likely cause:

- no request coalescing
- no warm-up
- no jitter on TTL

### 시나리오 3: cache invalidation works in dev but not in prod

Likely cause:

- multiple cache layers
- missed event propagation
- local cache not cleared

### 시나리오 4: cache stampede after mass expiration

Likely cause:

- synchronized TTL
- too many identical keys expiring together

## 코드로 보기

### Cache-aside with versioned key

```java
public Profile getProfile(long userId) {
    String key = "user:" + userId + ":profile:v2";
    Profile cached = cache.get(key);
    if (cached != null) {
        return cached;
    }

    Profile profile = repository.findProfile(userId);
    cache.put(key, profile, Duration.ofMinutes(5));
    return profile;
}
```

### TTL jitter

```java
Duration base = Duration.ofMinutes(5);
Duration jitter = Duration.ofSeconds(ThreadLocalRandom.current().nextInt(0, 30));
Duration ttl = base.plus(jitter);
```

### Invalidation event

```java
public void onProfileUpdated(ProfileUpdated event) {
    cache.evict("user:" + event.userId() + ":profile:v2");
}
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| TTL only | Easy to operate | Stale reads | Non-critical data |
| Explicit invalidation | Fresher data | More moving parts | User-visible mutable data |
| Versioned keys | Safer rollout | Orphaned old keys | Schema or contract changes |
| Stale-while-revalidate | Smooth latency | Temporary staleness | Read-heavy UI paths |
| Local + distributed cache | Faster hot path | More coherence work | High-traffic services |

## 꼬리질문

> Q: Why is cache invalidation hard?
> Intent: checks multi-layer coherence awareness.
> Core: the truth can change in multiple places and on different schedules.

> Q: Why can TTL be dangerous?
> Intent: checks freshness vs simplicity tradeoff.
> Core: TTL may keep stale data alive longer than the business can tolerate.

> Q: Why do hot keys matter?
> Intent: checks load concentration awareness.
> Core: one popular key can overload one cache node or one backend shard.

> Q: Why is read-after-write harder with replicas and caches?
> Intent: checks visibility semantics.
> Core: the write and the read may travel through different replication or invalidation paths.

## 한 줄 정리

Cache invalidation is really the decision about how much stale truth we can afford before the system stops being correct enough.
