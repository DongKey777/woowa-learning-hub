# Durability Recovery Master Note

> 한 줄 요약: durability and recovery are the same contract viewed from two different moments - write-time safety and crash-time reconstruction.

**Difficulty: Advanced**

> retrieval-anchor-keywords: WAL, redo log, undo log, checkpoint, crash recovery, fsync, dirty page, doublewrite, recovery time, durability, log sequence number, checkpoint age, torn page

> related docs:
> - [Redo Log, Undo Log, Checkpoint, Crash Recovery](../contents/database/redo-log-undo-log-checkpoint-crash-recovery.md)
> - [Page Cache, Dirty Writeback, fsync](../contents/operating-system/page-cache-dirty-writeback-fsync.md)
> - [Transaction Isolation and Locking](../contents/database/transaction-isolation-locking.md)
> - [느린 쿼리 분석 플레이북](../contents/database/slow-query-analysis-playbook.md)
> - [Online Schema Change Strategies](../contents/database/online-schema-change-strategies.md)
> - [OOM Killer, cgroup Memory Pressure](../contents/operating-system/oom-killer-cgroup-memory-pressure.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Topic Map](../rag/topic-map.md)

## 핵심 개념

Durability is not "the data exists somewhere."
It is "after a crash, the system can reconstruct a correct state."

That implies two different costs:

- write-time cost: `fsync`, logging, flush ordering
- recovery-time cost: replay, rollback, checkpoint scanning

If you optimize only one side, the other side gets worse.

## 깊이 들어가기

### 1. Redo makes writes recoverable

Redo log records what must be replayed after failure.

The DB can acknowledge a commit before data pages are fully flushed because the redo path is safer and cheaper than writing full pages immediately.

Read with:

- [Redo Log, Undo Log, Checkpoint, Crash Recovery](../contents/database/redo-log-undo-log-checkpoint-crash-recovery.md)

### 2. Undo preserves rollback and old snapshots

Undo is not just for explicit rollback.
It also underpins MVCC-style historical reads and recovery of incomplete transactions.

That means durability and consistency are coupled.

### 3. Checkpoints are the pressure valve

If checkpointing is delayed, recovery gets longer and write bursts become harsher.
If checkpointing is too aggressive, foreground latency grows.

That is why recovery tuning is also latency tuning.

### 4. Storage is part of the durability contract

Dirty pages, page cache, journal flushes, and doublewrite all affect what "safe" means in practice.

Read with:

- [Page Cache, Dirty Writeback, fsync](../contents/operating-system/page-cache-dirty-writeback-fsync.md)

## 실전 시나리오

### 시나리오 1: commits slow down after a bulk write

Likely cause:

- redo pressure
- checkpoint age growth
- dirty page flush burst

### 시나리오 2: restart takes much longer than expected

Likely cause:

- large redo window
- many dirty pages
- storage throughput bottleneck

### 시나리오 3: fsync changes the throughput curve

Likely cause:

- stronger durability settings
- flush on every commit
- journaling cost becoming visible

## 코드로 보기

### Recovery inspection

```sql
SHOW ENGINE INNODB STATUS\G
SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit';
SHOW VARIABLES LIKE 'sync_binlog';
```

### Storage observation

```bash
iostat -x 1
vmstat 1
cat /proc/meminfo | grep -E 'Dirty|Writeback'
```

### Durability-aware write path

```text
1. write intent to log
2. fsync log if policy requires
3. update in-memory page
4. flush dirty pages later
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Strong fsync policy | Maximum safety | Lower throughput | Money, ledger, core state |
| Relaxed flush policy | Better throughput | Data-loss window | Low-risk workloads |
| Small redo window | Faster recovery | More checkpoint pressure | Short-lived systems |
| Large redo window | Fewer flush stalls | Slower crash recovery | Stable, high-throughput systems |

## 꼬리질문

> Q: Why does durability affect latency?
> Intent: checks whether the candidate sees fsync and checkpoint cost as runtime cost.
> Core: making writes safe requires extra synchronization and flush work.

> Q: Why is crash recovery not just "read the table files"?
> Intent: checks WAL and replay understanding.
> Core: data files may be behind the committed logical state.

> Q: Why can checkpoint tuning hurt both writes and recovery?
> Intent: checks tradeoff awareness.
> Core: too slow increases replay work; too fast increases foreground flush cost.

## 한 줄 정리

Durability and recovery are the same guarantee split across normal writes and post-crash replay, so tuning one always changes the other.
