# Data Migration Consistency Master Note

> 한 줄 요약: data migration consistency is the problem of moving truth from one place to another without creating an unexplainable gap in between.

**Difficulty: Advanced**

> retrieval-anchor-keywords: backfill, dual write, shadow read, CDC, binlog, parity check, cutover, rollback, schema drift, data drift, reconciliation, online schema change, outbox, idempotent migration

> related docs:
> - [Strangler Fig Migration, Contract, Cutover](../contents/software-engineering/strangler-fig-migration-contract-cutover.md)
> - [Deployment Rollout / Rollback / Canary / Blue-Green](../contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md)
> - [CDC / Debezium / Outbox / Binlog](../contents/database/cdc-debezium-outbox-binlog.md)
> - [Online Schema Change Strategies](../contents/database/online-schema-change-strategies.md)
> - [Schema Migration / Partitioning / CDC / CQRS](../contents/database/schema-migration-partitioning-cdc-cqrs.md)
> - [API Versioning / Contract Testing / Anti-Corruption Layer](../contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md)
> - [Domain Events, Outbox, Inbox](../contents/software-engineering/outbox-inbox-domain-events.md)
> - [Payment System Ledger / Idempotency / Reconciliation](../contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

Data migration consistency is not a single migration step.

It is a chain of guarantees:

- source data is complete
- copied data is correct
- writes stay in sync during transition
- readers see a valid version
- rollback stays possible until parity is proven

When migration is wrong, the system usually looks "mostly fine" until a rare edge case exposes the gap.

## 깊이 들어가기

### 1. Backfill is not enough

Backfill copies historical data.
It does not solve live write drift.

That is why migration plans often need:

- backfill
- dual write
- shadow read
- parity verification
- cutover

### 2. The hard part is keeping two truths aligned

If old and new stores both accept writes, they can diverge.

You need a clear answer for:

- which system is source of truth
- how conflicts are detected
- how reconciliation works

Read with:

- [CDC / Debezium / Outbox / Binlog](../contents/database/cdc-debezium-outbox-binlog.md)
- [Schema Migration / Partitioning / CDC / CQRS](../contents/database/schema-migration-partitioning-cdc-cqrs.md)

### 3. Contracts must move with the data

If the schema changes but the API or event contract does not, consumers can still break.

That is why migration and contract testing belong together:

- [API Versioning / Contract Testing / Anti-Corruption Layer](../contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md)

### 4. Reconciliation is the safety net

Even with careful migration, some drift is inevitable.

The safe approach is to:

- detect drift
- measure its size
- repair it
- confirm parity

Read with:

- [Payment System Ledger / Idempotency / Reconciliation](../contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md)

## 실전 시나리오

### 시나리오 1: backfill completes but live traffic still diverges

Likely cause:

- dual write not symmetric
- event lag
- write path still points to old store somewhere

### 시나리오 2: cutover succeeds, then hidden drift appears later

Likely cause:

- parity check was too shallow
- rare data shape was missed
- consumers had stale assumptions

### 시나리오 3: rollback is impossible after release

Likely cause:

- incompatible schema change
- no backward compatibility
- irreversible data deletion

### 시나리오 4: migrated data is technically present but semantically wrong

Likely cause:

- transformation bug
- lost default value
- ordering or timezone mismatch

## 코드로 보기

### Migration checkpoint sketch

```yaml
migration:
  backfill_done: true
  dual_write_enabled: true
  shadow_read_parity: 99.99%
  rollback_window_open: true
  owner: platform-team
```

### Parity probe sketch

```sql
SELECT COUNT(*) FROM old_orders;
SELECT COUNT(*) FROM new_orders;
```

### Reconciliation marker sketch

```java
public record MigrationCheckpoint(String name, Instant checkedAt, boolean passed) {}
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Backfill only | Simple | Live drift remains | Historical import |
| Dual write | Faster transition | Divergence risk | Cutover period |
| CDC sync | Better continuity | More moving parts | Large migrations |
| Shadow read | Safe validation | Extra load | Pre-cutover verification |
| Hard cutover | Fast switch | High risk | Small, reversible systems |

## 꼬리질문

> Q: Why is backfill not enough for migration consistency?
> Intent: checks live-write awareness.
> Core: backfill handles history, not concurrent updates.

> Q: Why is dual write risky?
> Intent: checks divergence understanding.
> Core: one write path can fail or lag behind the other.

> Q: Why is reconciliation necessary?
> Intent: checks operational realism.
> Core: even careful migrations can drift and need repair.

> Q: Why must rollback remain open during cutover?
> Intent: checks safe deployment thinking.
> Core: if rollback is impossible, you cannot safely validate the move.

## 한 줄 정리

Data migration consistency is the discipline of moving truth with parity checks, controlled overlap, and a real rollback window until the new path is proven.
