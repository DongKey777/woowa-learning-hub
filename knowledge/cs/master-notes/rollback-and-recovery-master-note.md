# Rollback and Recovery Master Note

> 한 줄 요약: rollback is the planned way out, and recovery is the unplanned way back; good systems make both paths possible.

**Difficulty: Advanced**

> retrieval-anchor-keywords: rollback, recovery, blue-green, canary, feature flag, revert, restore, replay, compensation, checkpoint, failover, rollback window, parity check, archive

> related docs:
> - [Deployment Rollout / Rollback / Canary / Blue-Green](../contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md)
> - [Strangler Fig Migration, Contract, Cutover](../contents/software-engineering/strangler-fig-migration-contract-cutover.md)
> - [Feature Flag Cleanup / Expiration](../contents/software-engineering/feature-flag-cleanup-expiration.md)
> - [Redo Log, Undo Log, Checkpoint, Crash Recovery](../contents/database/redo-log-undo-log-checkpoint-crash-recovery.md)
> - [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md)
> - [Failure Recovery Lifecycle](../contents/operating-system/oom-killer-cgroup-memory-pressure.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Rollback is a deliberate reversal of a recent change.
Recovery is a response to an unexpected failure.

They share the same question:

- how do we get back to a known good state?

The answer needs:

- a stable baseline
- a way to verify parity
- a way to replay or restore data
- a way to stop the bleeding quickly

## 깊이 들어가기

### 1. Rollback only works if the old path still exists

This is why deployment strategy and migration strategy matter.

Read with:

- [Deployment Rollout / Rollback / Canary / Blue-Green](../contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md)
- [Strangler Fig Migration, Contract, Cutover](../contents/software-engineering/strangler-fig-migration-contract-cutover.md)

### 2. Database recovery is a specialized rollback model

DB crash recovery uses logs, checkpoints, and replay to reconstruct state.

Read with:

- [Redo Log, Undo Log, Checkpoint, Crash Recovery](../contents/database/redo-log-undo-log-checkpoint-crash-recovery.md)

### 3. Recovery needs observability and blast-radius control

If you cannot tell what changed, you cannot safely roll it back or recover it.

Rollback windows, feature flags, and parity checks are operational safety rails.

Read with:

- [Feature Flag Cleanup / Expiration](../contents/software-engineering/feature-flag-cleanup-expiration.md)

### 4. Application rollback and data recovery are not always the same

Code can be reverted quickly.
Data may need replay, restore, or compensation.

## 실전 시나리오

### 시나리오 1: deployment must be rolled back after metrics spike

Likely cause:

- no safe rollback path
- hidden schema or contract dependency

### 시나리오 2: data corruption discovered after release

Likely cause:

- rollback reverted code but not already mutated data

### 시나리오 3: recovery after crash takes too long

Likely cause:

- large recovery window
- replay backlog
- insufficient checkpointing

## 코드로 보기

### Rollback checklist sketch

```yaml
rollback:
  baseline_tag: v1.24.3
  feature_flag: off
  db_migration_reversible: true
  parity_check_passed: false
```

### Recovery probe sketch

```bash
kubectl rollout undo deploy/orders-api
SHOW ENGINE INNODB STATUS\G
```

### Compensation sketch

```java
public void compensate(String correlationId) {
    workflowService.revert(correlationId);
}
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Fast rollback | Shortens incident | Requires reversible design | Releases with clear baseline |
| Slow recovery | Safer reconstruction | Longer downtime | Data corruption or crash recovery |
| Blue-green | Easy switchback | Double infra | High-risk releases |
| Canary | Smaller blast radius | More monitoring needs | Gradual production rollout |

## 꼬리질문

> Q: Why is rollback not the same as recovery?
> Intent: checks incident-model separation.
> Core: rollback undoes a recent change; recovery reconstructs a stable state after failure.

> Q: Why must rollback be planned ahead of time?
> Intent: checks deployment discipline.
> Core: if the old path is gone, rollback is no longer possible.

> Q: Why do databases use logs for recovery?
> Intent: checks write-ahead logging understanding.
> Core: logs preserve the committed intent even when pages are not yet flushed.

## 한 줄 정리

Rollback and recovery are both about returning to safety, but one is a controlled escape hatch and the other is a reconstruction path after things already went wrong.
