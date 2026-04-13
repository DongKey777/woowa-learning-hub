# Batch Processing Master Note

> 한 줄 요약: batch processing is reliable only when chunking, retry, skip, restart, and idempotency are designed together.

**Difficulty: Advanced**

> retrieval-anchor-keywords: chunk, restartability, retry, skip, checkpoint, execution context, idempotency, deadlock, backoff, scheduler, replay, poison record, DLQ

> related docs:
> - [Spring Batch Chunk Retry Skip](../contents/spring/spring-batch-chunk-retry-skip.md)
> - [Spring Scheduler / Async Boundaries](../contents/spring/spring-scheduler-async-boundaries.md)
> - [Domain Events, Outbox, Inbox](../contents/software-engineering/outbox-inbox-domain-events.md)
> - [CDC / Debezium / Outbox / Binlog](../contents/database/cdc-debezium-outbox-binlog.md)
> - [멱등성 키와 중복 방지](../contents/database/idempotency-key-and-deduplication.md)
> - [Timeout, Retry, Backoff 실전](../contents/network/timeout-retry-backoff-practical.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Batch is not just "process many rows."

It is:

- bounded commit size
- restartable execution
- controlled retries
- safe skips
- audit-friendly progress tracking

If the batch is not restartable, it is just a big request with a worse failure mode.

## 깊이 들어가기

### 1. Chunk is the transaction boundary

The chunk is where commit happens.
Too large means expensive rollback, too small means too much overhead.

Read with:

- [Spring Batch Chunk Retry Skip](../contents/spring/spring-batch-chunk-retry-skip.md)

### 2. Retry vs skip

Retry transient infrastructure problems.
Skip irrecoverable data problems.

If you retry poison records forever, batch throughput collapses.

### 3. Restartability needs saved state

ExecutionContext, job repository, checkpoints, and idempotent writes are what make batch resumable.

### 4. Batch often touches other reliability patterns

Batch jobs frequently rely on:

- outbox/inbox
- CDC replay
- idempotent upserts

Read with:

- [Domain Events, Outbox, Inbox](../contents/software-engineering/outbox-inbox-domain-events.md)
- [멱등성 키와 중복 방지](../contents/database/idempotency-key-and-deduplication.md)

## 실전 시나리오

### 시나리오 1: monthly close job fails halfway

Likely cause:

- chunk too large
- restart point not saved

### 시나리오 2: one row always fails parsing

Likely cause:

- poison record
- missing skip routing

### 시나리오 3: rerun creates duplicates

Likely cause:

- writer not idempotent
- unique key missing

## 코드로 보기

### Fault-tolerant step

```java
stepBuilder
  .<InputRow, OutputRow>chunk(100, txManager)
  .reader(reader)
  .processor(processor)
  .writer(writer)
  .faultTolerant()
  .retry(DeadlockLoserDataAccessException.class)
  .skip(FlatFileParseException.class);
```

### Idempotent write

```sql
INSERT INTO target(id, value)
VALUES (?, ?)
ON DUPLICATE KEY UPDATE value = VALUES(value);
```

### Restart note

```text
checkpoint -> resume from last successful chunk
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Large chunk | High throughput | Expensive rollback | Stable data and low failure rate |
| Small chunk | Easier recovery | More overhead | Risky or variable input |
| Retry-first | Transient recovery | Longer runtime | Deadlock/timeouts |
| Skip-first | Keeps progress moving | Data quality work needed | Poison records |

## 꼬리질문

> Q: Why must batch jobs be restartable?
> Intent: checks operational resilience.
> Core: large jobs fail, and progress must survive process death.

> Q: Why is writer idempotency important?
> Intent: checks duplicate-processing awareness.
> Core: retries and restarts can replay the same item.

> Q: When do you retry and when do you skip?
> Intent: checks failure classification.
> Core: transient infrastructure issues retry, corrupt data skips.

## 한 줄 정리

Batch processing is a controlled failure model for large work, and its safety comes from restartability, idempotency, and explicit retry/skip boundaries.
