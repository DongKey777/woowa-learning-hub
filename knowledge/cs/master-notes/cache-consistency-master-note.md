# Cache Consistency Master Note

> 한 줄 요약: cache consistency is the problem of keeping fast reads useful when the truth moves elsewhere.

**Difficulty: Advanced**

> retrieval-anchor-keywords: cache consistency, stale read, invalidation, write-through, write-behind, cache-aside, TTL, jitter, read-after-write, replica lag, stampede, versioned key, stale-while-revalidate

> related docs:
> - [분산 캐시 설계](../contents/system-design/distributed-cache-design.md)
> - [Spring Cache Abstraction Traps](../contents/spring/spring-cache-abstraction-traps.md)
> - [Cache-Control 실전](../contents/network/cache-control-practical.md)
> - [Replica lag / read-after-write strategies](../contents/database/replica-lag-read-after-write-strategies.md)
> - [DNS TTL Cache Failure Patterns](../contents/network/dns-ttl-cache-failure-patterns.md)
> - [cache, message, observability](../contents/software-engineering/cache-message-observability.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Cache consistency is not binary.

The real question is:

- how stale can the cached value be
- who invalidates it
- when does the reader fall back
- what happens during stampede or failover

Fast cache reads are only useful if the stale window is bounded.

## 깊이 들어가기

### 1. Cache-aside is simple, but invalidation is the hard part

Read with:

- [분산 캐시 설계](../contents/system-design/distributed-cache-design.md)

The app owns the read-through and the invalidation path, which makes races visible.

### 2. Replica lag and cache lag stack together

If the DB replica is behind and the cache still holds the old value, read-after-write can fail twice.

Read with:

- [Replica lag / read-after-write strategies](../contents/database/replica-lag-read-after-write-strategies.md)

### 3. Versioned keys are safer than blind overwrite

Versioned keys reduce the chance of race-based stale reads, especially during schema or contract changes.

### 4. TTL is a policy, not a guarantee

TTL bounds stale time, but it does not force freshness immediately.
Use jitter to avoid synchronized expiry.

### 5. Observability closes the loop

Cache hit ratio, eviction rate, miss latency, and stampede counts should all be visible.

Read with:

- [cache, message, observability](../contents/software-engineering/cache-message-observability.md)

## 실전 시나리오

### 시나리오 1: profile update shows old data

Likely cause:

- cache invalidation missed
- replica lag
- client reused stale CDN response

### 시나리오 2: cache eviction causes DB spike

Likely cause:

- stampede
- synchronized TTL
- missing request coalescing

### 시나리오 3: Spring cache works locally but not in prod

Likely cause:

- multiple cache layers
- wrong key derivation
- proxy or CDN caching

## 코드로 보기

### Cache-aside sketch

```java
Profile cached = cache.get(key);
if (cached != null) return cached;
Profile profile = repository.findProfile(id);
cache.put(key, profile, Duration.ofMinutes(5));
return profile;
```

### Invalidation sketch

```java
@Transactional
public void updateProfile(ProfileUpdate cmd) {
    repository.save(cmd.toEntity());
    cache.evict("user:" + cmd.userId() + ":profile:v2");
}
```

### TTL jitter

```java
Duration ttl = Duration.ofMinutes(5)
    .plusSeconds(ThreadLocalRandom.current().nextInt(0, 30));
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| TTL-only | Easy to operate | Stale reads are common | Low-risk data |
| Explicit invalidation | Fresher reads | More race handling | Mutable user-facing data |
| Versioned keys | Safer rollout | Orphaned old keys | Schema or contract changes |
| Stale-while-revalidate | Smooth latency | Temporary staleness | Read-heavy UI |

## 꼬리질문

> Q: Why is cache invalidation harder than cache lookup?
> Intent: checks coherence awareness.
> Core: reads are local, but truth changes elsewhere and must be propagated.

> Q: Why can replica lag and cache lag combine badly?
> Intent: checks multi-layer freshness awareness.
> Core: both layers can serve old truth at the same time.

> Q: Why is TTL not enough for correctness-sensitive data?
> Intent: checks stale-window reasoning.
> Core: TTL bounds age but does not guarantee immediate freshness after writes.

## 한 줄 정리

Cache consistency is the discipline of bounding staleness and making invalidation, fallback, and observability explicit.
