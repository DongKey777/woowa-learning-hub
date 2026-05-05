# Migration Cutover Master Note

> 한 줄 요약: migration success is not just moving code, but moving traffic, data, and contracts while keeping rollback open until parity is proven.

**난이도: 🔴 Advanced**

> retrieval-anchor-keywords: cutover, shadow traffic, dual write, feature flag, canary, blue-green, strangler fig, contract testing, rollback, archive, shadow read, parity, schema migration, CDC

> related docs:
> - [Strangler Fig Migration, Contract, Cutover](../contents/software-engineering/strangler-fig-migration-contract-cutover.md)
> - [Branch by Abstraction vs Feature Flag vs Strangler](../contents/software-engineering/branch-by-abstraction-vs-feature-flag-vs-strangler.md)
> - [Deployment Rollout / Rollback / Canary / Blue-Green](../contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md)
> - [Feature Flags, Rollout, Dependency Management](../contents/software-engineering/feature-flags-rollout-dependency-management.md)
> - [Feature Flag Cleanup / Expiration](../contents/software-engineering/feature-flag-cleanup-expiration.md)
> - [API Versioning / Contract Testing / Anti-Corruption Layer](../contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md)
> - [CDC / Debezium / Outbox / Binlog](../contents/database/cdc-debezium-outbox-binlog.md)
> - [Online Schema Change Strategies](../contents/database/online-schema-change-strategies.md)
> - [Schema Migration / Partitioning / CDC / CQRS](../contents/database/schema-migration-partitioning-cdc-cqrs.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Cutover is a controlled change of truth.

You are not only replacing code.
You are also shifting:

- request path
- data source of truth
- contract surface
- observability path
- rollback path

The safest migrations separate the problem into four layers:

- traffic migration
- data migration
- contract migration
- operational migration

## Which migration doc first?

When "migration" questions start to blur together, split them by the first decision you need to make.

| First question | Read first | Why |
|---|---|---|
| Who can advance or pause the next wave? | [Migration Wave Governance and Decision Rights](../contents/software-engineering/migration-wave-governance-decision-rights.md) | decision rights and pause authority |
| Which numbers say the migration is healthy enough? | [Migration Scorecards](../contents/software-engineering/migration-scorecards.md) | readiness/risk metrics and exit criteria |
| Which consumers move first and how do we dual-run them? | [Consumer Migration Playbook and Contract Adoption](../contents/software-engineering/consumer-migration-playbook-contract-adoption.md) | rollout order, registry, fallback |
| Should we shrink scope or stop the migration? | [Migration Stop-Loss and Scope Reduction Governance](../contents/software-engineering/migration-stop-loss-scope-reduction-governance.md) | stop-loss and pivot criteria |

This keeps "migration governance" from collapsing into one vague bucket during retrieval.

## 깊이 들어가기

### 1. Strangler is about path replacement, not big-bang rewrite

The old and new systems coexist.
Traffic is peeled away gradually.

That is why these docs fit together:

- [Strangler Fig Migration, Contract, Cutover](../contents/software-engineering/strangler-fig-migration-contract-cutover.md)
- [Branch by Abstraction vs Feature Flag vs Strangler](../contents/software-engineering/branch-by-abstraction-vs-feature-flag-vs-strangler.md)

### 2. Data cutover is the hard part

Code can be switched quickly.
Data cannot.

Typical techniques:

- backfill
- shadow write
- dual write
- CDC replication
- read switch after parity

Read with:

- [CDC / Debezium / Outbox / Binlog](../contents/database/cdc-debezium-outbox-binlog.md)
- [Online Schema Change Strategies](../contents/database/online-schema-change-strategies.md)

### 3. Rollback must remain real

If rollback is not actually possible, the "cutover" is just a point of no return.

Rollback requires:

- reversible schema changes
- backward-compatible contracts
- feature flags that can be removed later
- clear ownership of data replays

### 4. Observability before and after cutover matters

The migration should be measurable:

- error rate
- latency
- data drift
- duplicate writes
- missing rows
- contract mismatches

Useful companion:

- [cache message observability](../contents/software-engineering/cache-message-observability.md)

## 실전 시나리오

### 시나리오 1: old API and new API run in parallel

Use:

- contract tests
- shadow traffic
- a feature flag for traffic split

### 시나리오 2: dual write creates divergence

The failure is not just technical.
The failure is in the missing reconciliation strategy.

### 시나리오 3: schema migration blocks the rollout

This is where online schema change strategies matter.
The deployment and the migration cannot be planned separately.

### 시나리오 4: feature flag never gets removed

Then the cutover is not complete.
Technical debt and migration debt overlap here.

## 코드로 보기

### Safe rollout checklist sketch

```yaml
cutover:
  shadow_traffic: true
  contract_tests: true
  data_parity_check: true
  rollback_path: ready
  feature_flag_owner: platform-team
  cleanup_due_date: 2026-04-30
```

### Dual write with parity check sketch

```java
public void save(Order order) {
    legacyStore.save(order);
    newStore.save(order);
    parityVerifier.record(order.getId());
}
```

This is only safe when reconciliation and failure handling are explicit.

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Shadow traffic | Low risk validation | Extra cost | Early verification |
| Canary | Real traffic signal | Partial exposure | Production rollout |
| Blue-green | Fast switch / rollback | Double infra | Big releases |
| Dual write | Stronger consistency path | Divergence risk | Transitional periods |
| CDC | Decouples writers/readers | More moving parts | Data-heavy migration |

## 꼬리질문

> Q: Why is cutover risky even when code compiles and tests pass?
> Intent: checks production migration realism.
> Core: data, traffic, and contracts still need to line up.

> Q: Why is dual write dangerous?
> Intent: checks consistency and reconciliation thinking.
> Core: one side can fail independently and create drift.

> Q: Why do feature flags need cleanup?
> Intent: checks operational discipline.
> Core: stale flags keep hidden paths alive and increase complexity.

> Q: What makes rollback real instead of theoretical?
> Intent: checks reversibility.
> Core: backward compatibility and state reversion must still exist after release.

## 한 줄 정리

Migration cutover is the art of changing systems without losing the ability to explain, verify, or undo what happened.
