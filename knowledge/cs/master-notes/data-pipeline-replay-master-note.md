# Data Pipeline Replay Master Note

> 한 줄 요약: replayable pipelines are built so that lost, duplicated, or delayed events can be reprocessed into the same final state.

**Difficulty: Advanced**

> retrieval-anchor-keywords: replay, reprocessing, CDC, outbox, inbox, idempotent consumer, offset, checkpoint, watermark, dead letter queue, exactly-once, at-least-once, deduplication

> related docs:
> - [Domain Events, Outbox, Inbox](../contents/software-engineering/outbox-inbox-domain-events.md)
> - [CDC / Debezium / Outbox / Binlog](../contents/database/cdc-debezium-outbox-binlog.md)
> - [Outbox, Saga, Eventual Consistency](../contents/database/outbox-saga-eventual-consistency.md)
> - [Spring EventListener, TransactionalEventListener, and Outbox](../contents/spring/spring-eventlistener-transaction-phase-outbox.md)
> - [Idempotency Key and Deduplication](../contents/database/idempotency-key-and-deduplication.md)
> - [Workflow Orchestration / Saga Design](../contents/system-design/workflow-orchestration-saga-design.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

Replay is not "run it again."
It is "run it again without creating a different business result."

That means pipeline design must handle:

- duplicates
- partial failures
- out-of-order arrival
- delayed visibility
- manual backfill

## 깊이 들어가기

### 1. Source of truth and derived state must be separated

Replay works when the pipeline can rebuild derived state from stable inputs.

Typical stable inputs:

- source DB change log
- outbox table
- event stream

Read with:

- [CDC / Debezium / Outbox / Binlog](../contents/database/cdc-debezium-outbox-binlog.md)

### 2. Checkpoints and offsets are operational state

Pipelines need to remember where they are.
If checkpoints are wrong, replay can skip data or duplicate it.

### 3. Consumers must be idempotent

Replay is safe only if repeated inputs do not create different outputs.

Read with:

- [Idempotency Key and Deduplication](../contents/database/idempotency-key-and-deduplication.md)

### 4. DLQ and manual repair are part of the design

Some events are not safe to auto-replay forever.
Those need quarantine, inspection, and sometimes schema transformation before they can be reprocessed.

## 실전 시나리오

### 시나리오 1: pipeline lost events during deploy

Likely cause:

- offsets committed before downstream success
- restart did not resume from the right checkpoint

### 시나리오 2: replay doubles a side effect

Likely cause:

- consumer not idempotent
- dedupe key missing

### 시나리오 3: backfill finishes but new events drift

Likely cause:

- live writes were not mirrored
- replay path and live path diverged

## 코드로 보기

### Offset checkpoint sketch

```java
public record Checkpoint(String stream, long offset, Instant updatedAt) {}
```

### Idempotent consumer sketch

```java
if (processedEventRepository.existsByEventId(event.id())) {
    return;
}
apply(event);
processedEventRepository.save(new ProcessedEvent(event.id()));
```

### Replay mode switch

```text
if (mode == REPLAY) {
    readFromCheckpoint();
} else {
    consumeLiveStream();
}
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| At-least-once | Simple reliability | Duplicates | Most pipelines |
| Exactly-once illusion | Easier reasoning | Complex machinery | Narrow managed systems |
| Replayable design | Recovery-friendly | More state tracking | Business-critical data flows |
| Fire-and-forget | Low overhead | Hard recovery | Non-critical telemetry |

## 꼬리질문

> Q: Why is replay different from retry?
> Intent: checks pipeline semantics.
> Core: retry is immediate execution recovery; replay is reprocessing past data into a stable state.

> Q: Why are offsets dangerous if mismanaged?
> Intent: checks operational state understanding.
> Core: an incorrect offset can silently skip or duplicate data.

> Q: Why must consumers be idempotent?
> Intent: checks duplicate-tolerance design.
> Core: replay and at-least-once delivery both create duplicates.

## 한 줄 정리

Data pipeline replay is safe only when checkpoints, offsets, and consumer idempotency are designed together as one recovery model.
