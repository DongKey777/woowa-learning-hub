# Storage Engine Behavior Master Note

> 한 줄 요약: storage engine behavior explains why a write is durable, why a read is stale, and why latency spikes even when the SQL itself looks harmless.

**Difficulty: Advanced**

> retrieval-anchor-keywords: redo log, undo log, binlog, group commit, fsync, buffer pool, page cache, dirty writeback, checkpoint, MVCC, consistent read, readahead, direct IO, mmap, durability, snapshot

> related docs:
> - [Group Commit / Binlog / Fsync Durability](../contents/database/group-commit-binlog-fsync-durability.md)
> - [Page Cache / Dirty Writeback / Fsync](../contents/operating-system/page-cache-dirty-writeback-fsync.md)
> - [Mmap vs Read / Page Cache Behavior](../contents/operating-system/mmap-vs-read-page-cache-behavior.md)
> - [Page Cache Thrash vs Direct I/O](../contents/operating-system/page-cache-thrash-vs-direct-io.md)
> - [Readahead Tuning / Page Cache](../contents/operating-system/readahead-tuning-page-cache.md)
> - [MVCC Read View / Consistent Read Internals](../contents/database/mvcc-read-view-consistent-read-internals.md)
> - [Transaction Isolation and Locking](../contents/database/transaction-isolation-locking.md)
> - [Slow Query Analysis Playbook](../contents/database/slow-query-analysis-playbook.md)
> - [Query Tuning Checklist](../contents/database/query-tuning-checklist.md)
> - [Statement Digest and Plan Cache Behavior](../contents/database/statement-digest-and-plan-cache-behavior.md)
> - [Transaction Timeout vs Lock Timeout](../contents/database/transaction-timeout-vs-lock-timeout.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

Storage engine behavior sits below the ORM, below the SQL text, and often below the database process itself.

It determines:

- when data becomes durable
- which version a read sees
- how much of the working set stays hot
- why a simple query may block on I/O

That is why "the database is slow" is too vague to be useful.

## 깊이 들어가기

### 1. Durability is a logging and flush story

The commit path usually touches:

- redo log
- binlog or WAL
- fsync or flush policy
- group commit coordination

If those pieces are tuned for speed instead of durability, the crash semantics change.

### 2. MVCC decides what a reader sees

Consistent reads often use a snapshot or read view.

That means the engine may return an older committed version even though a newer one already exists.

This is not a bug by itself. It is the price of non-blocking reads.

### 3. Page cache and buffer pool are not the same thing

The DB buffer pool and the OS page cache have different responsibilities.

- buffer pool: database-managed hot pages
- page cache: OS-managed file cache behavior

Confusing the two makes tuning look random.

### 4. Readahead and writeback shape latency

Sequential reads can benefit from readahead.

Dirty page writeback can suddenly steal I/O bandwidth and make unrelated queries slower.

That is why storage latency can spike without any SQL change.

### 5. `mmap` and direct I/O change the failure and latency profile

`mmap` can shift cost into page faults and memory pressure.

Direct I/O can bypass some cache behavior but may trade one bottleneck for another.

The right choice depends on access pattern, working set, and durability goals.

## 실전 시나리오

### 시나리오 1: commit returns fast but crash recovery loses data

Check:

- flush policy
- group commit behavior
- replication or binlog durability settings

### 시나리오 2: a read becomes slow after the cache goes cold

Check:

- page cache misses
- readahead effectiveness
- working set size
- disk saturation

### 시나리오 3: a query shows old data even though another session just wrote it

Check:

- MVCC snapshot timing
- isolation level
- transaction boundary placement

### 시나리오 4: latency spikes during heavy write load

Check:

- dirty writeback
- checkpoint pressure
- flush stalls
- lock wait versus I/O wait

## 코드로 보기

### SQL and engine inspection

```sql
SHOW ENGINE INNODB STATUS;
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = ?;
```

### Durable write settings sketch

```text
innodb_flush_log_at_trx_commit = 1
sync_binlog = 1
```

### Operational checks

```bash
iostat -x 1
vmstat 1
cat /proc/meminfo
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Strong flush guarantees | Better crash safety | Higher latency | Critical data paths |
| Relaxed flush policy | Lower write latency | More recovery risk | Controlled or ephemeral data |
| Page cache heavy design | Great read locality | Memory pressure and burstiness | Read-mostly workloads |
| Direct I/O | More predictable storage path | More tuning complexity | Specialized high-throughput systems |
| MVCC consistent read | Non-blocking readers | Stale snapshot semantics | Concurrency-heavy OLTP |

The trade is always between latency, durability, and visibility semantics.

## 꼬리질문

> Q: Why can a committed write still be lost after a crash?
> Intent: checks durability semantics.
> Core: the commit may have returned before the relevant logs were safely flushed.

> Q: Why can a reader see older data than the latest writer?
> Intent: checks MVCC and snapshot awareness.
> Core: consistent reads often use a transaction snapshot rather than the newest page version.

> Q: Why does write pressure sometimes hurt unrelated reads?
> Intent: checks dirty writeback and I/O coupling.
> Core: flushing and checkpoint work can consume the same storage bandwidth.

> Q: Why do page cache and buffer pool matter separately?
> Intent: checks physical memory model awareness.
> Core: the OS cache and the DB cache are tuned by different layers and fail differently.

## 한 줄 정리

Storage engine behavior is the hidden layer that decides durability, snapshot visibility, and physical I/O cost, so it often explains latency and consistency issues that SQL alone cannot.
