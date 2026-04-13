# Schema Evolution Master Note

> 한 줄 요약: schema evolution is the art of changing contracts across services, storage, and events without breaking old readers or new writers.

**Difficulty: Advanced**

> retrieval-anchor-keywords: schema evolution, backward compatible, forward compatible, expand and contract, contract testing, nullable field, default value, replay compatibility, event schema, API versioning, anti-corruption layer, cutover

> related docs:
> - [Schema Contract Evolution Across Services](../contents/software-engineering/schema-contract-evolution-cross-service.md)
> - [Event Schema Versioning and Compatibility](../contents/software-engineering/event-schema-versioning-compatibility.md)
> - [API Versioning / Contract Testing / Anti-Corruption Layer](../contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md)
> - [Strangler Fig Migration, Contract, Cutover](../contents/software-engineering/strangler-fig-migration-contract-cutover.md)
> - [Domain Events, Outbox, Inbox](../contents/software-engineering/outbox-inbox-domain-events.md)
> - [Monolith to MSA Failure Patterns](../contents/software-engineering/monolith-to-msa-failure-patterns.md)

## 핵심 개념

Schema evolution is not just adding fields.
It is managing a shared contract across producers, consumers, replay jobs, and migrations.

The safe answer must preserve:

- old readers
- new writers
- reprocessing
- rollback

## 깊이 들어가기

### 1. Direction matters

Backward compatibility protects old consumers.
Forward compatibility protects new consumers reading old data.

Read with:

- [Schema Contract Evolution Across Services](../contents/software-engineering/schema-contract-evolution-cross-service.md)

### 2. Meaning changes are more dangerous than type changes

Changing `status` semantics is usually riskier than adding `promotionId`.

### 3. Expand and contract is the default migration pattern

Add first, dual-read or dual-write, then remove later.

### 4. Event schemas need replay compatibility

Events can be replayed months later, so old payloads must still parse.

Read with:

- [Event Schema Versioning and Compatibility](../contents/software-engineering/event-schema-versioning-compatibility.md)

### 5. Cutover depends on contract testing

Schema changes and route changes should be verified before full rollout.

Read with:

- [API Versioning / Contract Testing / Anti-Corruption Layer](../contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md)
- [Strangler Fig Migration, Contract, Cutover](../contents/software-engineering/strangler-fig-migration-contract-cutover.md)

## 실전 시나리오

### 시나리오 1: add field breaks older consumer

Likely cause:

- required field added
- parser too strict

### 시나리오 2: rename causes hidden outage

Likely cause:

- meaning changed but field name stayed similar
- consumer assumptions not updated

### 시나리오 3: replay job fails on old payloads

Likely cause:

- replay compatibility not tested

## 코드로 보기

### Versioned event sketch

```java
public record OrderPlacedV2(
    String eventId,
    String orderId,
    int schemaVersion,
    String promotionId
) {}
```

### Expand and contract sketch

```text
1. add nullable field
2. write both old and new paths
3. switch readers
4. remove old field
```

### Consumer tolerance

```java
String promotionId = payload.getOrDefault("promotionId", null);
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Immediate rename | Simple | High break risk | Tiny internal systems |
| Expand and contract | Safe | Slow rollout | Production services |
| Versioned schema | Explicit | More versions to manage | Many consumers |
| Strict parsing | Early failure | Fragile replay | Internal tooling only |

## 꼬리질문

> Q: Why is schema evolution harder than schema creation?
> Intent: checks contract lifecycle awareness.
> Core: existing consumers and replays constrain what can change.

> Q: Why is meaning change more dangerous than field addition?
> Intent: checks semantic compatibility.
> Core: the name stays the same while the contract silently shifts.

> Q: Why does replay matter for schema evolution?
> Intent: checks historical compatibility.
> Core: old payloads will be read again during recovery or backfill.

## 한 줄 정리

Schema evolution is contract management over time, and the safest strategy preserves compatibility for old readers, new writers, and replay jobs simultaneously.
