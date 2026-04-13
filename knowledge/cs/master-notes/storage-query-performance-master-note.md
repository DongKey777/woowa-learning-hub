# Storage Query Performance Master Note

> 한 줄 요약: storage query performance is about turning a logical lookup into the cheapest possible physical access path.

**Difficulty: Advanced**

> retrieval-anchor-keywords: slow query, full scan, execution plan, EXPLAIN ANALYZE, filesort, temporary table, covering index, selectivity, offset pagination, seek pagination, lock wait, read amplification, B+Tree, buffer pool

> related docs:
> - [느린 쿼리 분석 플레이북](../contents/database/slow-query-analysis-playbook.md)
> - [인덱스와 실행 계획](../contents/database/index-and-explain.md)
> - [쿼리 튜닝 체크리스트](../contents/database/query-tuning-checklist.md)
> - [Index Condition Pushdown, Filesort, Temporary Table](../contents/database/index-condition-pushdown-filesort-temporary-table.md)
> - [Covering Index / Composite Ordering](../contents/database/covering-index-composite-ordering.md)
> - [Pagination: Offset vs Seek](../contents/database/pagination-offset-vs-seek.md)
> - [B+Tree vs LSM-Tree](../contents/database/bptree-vs-lsm-tree.md)
> - [Hikari Connection Pool Tuning](../contents/database/hikari-connection-pool-tuning.md)
> - [Page Cache, Dirty Writeback, fsync](../contents/operating-system/page-cache-dirty-writeback-fsync.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Topic Map](../rag/topic-map.md)

## 핵심 개념

Storage query performance is not only "DB is fast or slow".

It is the sum of:

- access path choice
- index design
- cardinality and selectivity
- row filtering
- sort and group cost
- buffer pool hit ratio
- lock wait
- connection wait

The fastest query is usually the one that reads the fewest physical pages.

## 깊이 들어가기

### 1. Logical SQL becomes physical reads

The same `WHERE` clause can lead to very different work:

- index range scan
- full table scan
- covering index lookup
- filesort and temp table

That is why `EXPLAIN` matters more than intuition.

### 2. Index design is about access path shape

Good index questions:

- is the filter selective?
- does the index order match the sort?
- can the query be covered?
- does a function block index usage?

Useful companions:

- [인덱스와 실행 계획](../contents/database/index-and-explain.md)
- [Index Condition Pushdown, Filesort, Temporary Table](../contents/database/index-condition-pushdown-filesort-temporary-table.md)

### 3. Pagination can dominate the cost

Offset pagination gets slower as the offset grows because the DB still has to skip rows.

Seek pagination usually keeps access bounded and stable.

Read with:

- [Pagination: Offset vs Seek](../contents/database/pagination-offset-vs-seek.md)

### 4. Storage is still physical

Even a good plan can be hurt by:

- cold buffer pool
- dirty writeback
- fsync pressure
- page cache churn
- lock wait from concurrent writers

That is why storage docs and OS docs belong together:

- [Page Cache, Dirty Writeback, fsync](../contents/operating-system/page-cache-dirty-writeback-fsync.md)
- [Hikari Connection Pool Tuning](../contents/database/hikari-connection-pool-tuning.md)

## 실전 시나리오

### 시나리오 1: query is fine in dev but slow in prod

Likely cause:

- data volume difference
- stale statistics
- selectivity change
- different cache warmth

### 시나리오 2: index exists but is not used

Likely cause:

- function on column
- type mismatch
- bad column order
- optimizer choosing a cheaper-looking path

### 시나리오 3: list page slows down as page number increases

Likely cause:

- offset pagination scanning too many rows

### 시나리오 4: query latency rises when writes increase

Likely cause:

- lock contention
- buffer pool churn
- page flush pressure

## 코드로 보기

### EXPLAIN-first workflow

```sql
EXPLAIN ANALYZE
SELECT id, status, created_at
FROM orders
WHERE user_id = 12345
ORDER BY created_at DESC
LIMIT 20;
```

### Seek pagination pattern

```sql
SELECT id, status, created_at
FROM orders
WHERE user_id = 12345
  AND (created_at, id) < (?, ?)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

### Covering index idea

```sql
CREATE INDEX idx_orders_user_created_status
ON orders(user_id, created_at DESC, status);
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Add index | Faster lookups | Slower writes | Stable read patterns |
| Rewrite query | Better physical plan | Code change risk | Bad predicate or sort shape |
| Cache result | Low latency | Staleness | Read-heavy paths |
| Seek pagination | Stable scaling | More complex API | Infinite scroll or feed-like pages |
| Bigger buffer pool | More cache hits | More memory use | Well-sized DB nodes |

## 꼬리질문

> Q: Why can a query be slow even with an index?
> Intent: checks optimizer and access-path understanding.
> Core: the index may not match the filter, sort, or selectivity.

> Q: Why is offset pagination expensive?
> Intent: checks physical access reasoning.
> Core: the DB still traverses and discards many rows.

> Q: Why does write pressure affect read performance?
> Intent: checks storage engine and caching understanding.
> Core: flush, lock, and buffer churn can slow reads too.

> Q: Why do execution plans matter more than query text alone?
> Intent: checks plan-vs-syntax thinking.
> Core: the actual work depends on the chosen physical path.

## 한 줄 정리

Storage query performance is the art of aligning SQL shape, index shape, and physical storage behavior so the database reads the fewest pages possible.
