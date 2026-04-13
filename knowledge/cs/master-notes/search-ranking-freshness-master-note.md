# Search Ranking Freshness Master Note

> 한 줄 요약: search ranking freshness is the tradeoff between relevance and how quickly new truth becomes searchable.

**Difficulty: Advanced**

> retrieval-anchor-keywords: ranking, freshness, recency boost, relevance, inverted index, near real-time indexing, query cache, hot query, stale results, search pipeline, recrawling, reindexing, shard, boosting

> related docs:
> - [Search 시스템 설계](../contents/system-design/search-system-design.md)
> - [Distributed Cache Design](../contents/system-design/distributed-cache-design.md)
> - [Cache-Control Practical](../contents/network/cache-control-practical.md)
> - [Replica lag / read-after-write strategies](../contents/database/replica-lag-read-after-write-strategies.md)
> - [CDC / Debezium / Outbox / Binlog](../contents/database/cdc-debezium-outbox-binlog.md)
> - [Query Tuning Checklist](../contents/database/query-tuning-checklist.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Search is not only retrieval.
It is retrieval plus ordering plus freshness.

If a system is relevant but stale, it feels wrong.
If it is fresh but poorly ranked, it feels noisy.

The right balance depends on the product.

## 깊이 들어가기

### 1. Ranking and freshness are separate signals

Ranking decides what should come first.
Freshness decides how quickly new or changed documents become visible.

Read with:

- [Search 시스템 설계](../contents/system-design/search-system-design.md)

### 2. Freshness depends on the ingest path

If search is updated through:

- batch indexing
- CDC
- outbox relay
- near real-time pipeline

the lag budget is different.

Read with:

- [CDC / Debezium / Outbox / Binlog](../contents/database/cdc-debezium-outbox-binlog.md)

### 3. Cache and replica lag can make search look stale even if indexing is fine

The search API may serve:

- cached queries
- stale replicas
- stale index shards

Read with:

- [Distributed Cache Design](../contents/system-design/distributed-cache-design.md)
- [Replica lag / read-after-write strategies](../contents/database/replica-lag-read-after-write-strategies.md)

### 4. Hot queries can distort the freshness budget

Popular searches can keep old cache entries alive or stress a single shard.

That is why query caching and ranking need to be measured together.

## 실전 시나리오

### 시나리오 1: new post does not appear in search for minutes

Likely cause:

- batch index lag
- CDC backlog
- stale query cache

### 시나리오 2: search results are fresh but poorly ranked

Likely cause:

- ranking signal missing
- recency boost too weak
- popularity bias too strong

### 시나리오 3: deleted content still appears

Likely cause:

- stale shard
- cache invalidation missing
- soft delete not propagated

## 코드로 보기

### Ranking signal sketch

```text
score = text_match + recency_boost + popularity_boost + personalization_boost
```

### Freshness checkpoint sketch

```java
public record IndexCheckpoint(String shard, long offset, Instant updatedAt) {}
```

### Search cache key sketch

```text
search:v3:tenant:{tenantId}:query:{normalizedQuery}:filters:{hash}
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Batch indexing | Simple operation | Higher lag | Offline or low-change data |
| Near real-time indexing | Better freshness | More moving parts | News, feeds, commerce |
| Heavy ranking | Better relevance | More compute and tuning | High-value discovery |
| Aggressive caching | Lower latency | Staleness risk | Popular repeated queries |

## 꼬리질문

> Q: Why is ranking separate from freshness?
> Intent: checks search-system decomposition.
> Core: the best result and the newest result are not always the same thing.

> Q: Why can search look stale even when indexing is working?
> Intent: checks cache and replication awareness.
> Core: the query path may still serve stale cache or replica data.

> Q: Why do hot queries matter?
> Intent: checks load concentration awareness.
> Core: a few popular queries can dominate cache, shard, and indexing pressure.

## 한 줄 정리

Search freshness is the pipeline question, and ranking is the relevance question; both must be tuned together.
