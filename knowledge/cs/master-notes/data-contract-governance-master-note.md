# Data Contract Governance Master Note

> 한 줄 요약: data contract governance is the discipline of defining, versioning, testing, and retiring data shapes so producers and consumers can evolve safely.

**Difficulty: Advanced**

> retrieval-anchor-keywords: data contract, schema ownership, contract testing, versioning, compatibility, schema evolution, consumer-driven, deprecation, replay compatibility, data contract governance, ownership, lifecycle

> related docs:
> - [Schema Contract Evolution Across Services](../contents/software-engineering/schema-contract-evolution-cross-service.md)
> - [Event Schema Versioning and Compatibility](../contents/software-engineering/event-schema-versioning-compatibility.md)
> - [API Versioning / Contract Testing / Anti-Corruption Layer](../contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md)
> - [Consumer-Driven Contract Testing](../contents/software-engineering/api-contract-testing-consumer-driven.md)
> - [Data Contract Ownership Lifecycle](../contents/software-engineering/data-contract-ownership-lifecycle.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

Data contracts exist in APIs, events, tables, files, and streams.
Governance is what keeps those contracts from drifting until nobody trusts the shape anymore.

The governance job is to make sure:

- owners are known
- versions are explicit
- compatibility rules are documented
- deprecation has a date
- consumers can be tested against change

## 깊이 들어가기

### 1. Contract ownership matters

If no one owns the schema, no one owns compatibility.

Read with:

- [Data Contract Ownership Lifecycle](../contents/software-engineering/data-contract-ownership-lifecycle.md)

### 2. Versioning must have a policy

Version numbers without a change policy become cargo cult.

Read with:

- [Schema Contract Evolution Across Services](../contents/software-engineering/schema-contract-evolution-cross-service.md)
- [Event Schema Versioning and Compatibility](../contents/software-engineering/event-schema-versioning-compatibility.md)

### 3. Consumer-driven testing is the enforcement layer

Consumers define what they need, and producers verify they still provide it.

Read with:

- [Consumer-Driven Contract Testing](../contents/software-engineering/api-contract-testing-consumer-driven.md)

### 4. Anti-corruption layers prevent raw drift

Internal models should not directly mirror unstable external schemas.

Read with:

- [API Versioning / Contract Testing / Anti-Corruption Layer](../contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md)

### 5. Governance includes deprecation and retirement

If an old field or event stays forever, the contract is not governed; it is just accumulated.

## 실전 시나리오

### 시나리오 1: producer removes field too early

Likely cause:

- ownership unclear
- deprecation window not defined

### 시나리오 2: consumer breaks after schema change

Likely cause:

- compatibility policy missing
- contract tests absent

### 시나리오 3: event replay fails months later

Likely cause:

- old schema not governed
- replay compatibility not tested

## 코드로 보기

### Contract metadata sketch

```yaml
contract:
  owner: payments-team
  version: v3
  compatibility: backward-compatible
  deprecate_after: 2026-06-30
```

### Consumer contract sketch

```json
{
  "consumer": "delivery-service",
  "provider": "order-service",
  "expectedFields": ["id", "status", "totalAmount"]
}
```

### Governance gate

```text
if contract breaking change:
  require version bump + migration plan + consumer sign-off
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| No governance | Fast initially | Drift accumulates | Tiny prototypes |
| Light governance | Low overhead | Some risk remains | Small teams |
| Strong governance | Safer evolution | More process | Shared data platforms |

## 꼬리질문

> Q: Why are data contracts different from code contracts?
> Intent: checks cross-system lifecycle understanding.
> Core: data outlives deployments and gets replayed, cached, and shared.

> Q: Why do consumers need to own the contract too?
> Intent: checks ownership distribution.
> Core: the consumer is the first place a break will show up.

> Q: Why does deprecation need a date?
> Intent: checks lifecycle discipline.
> Core: without an end date, old shapes never leave.

## 한 줄 정리

Data contract governance is the ownership and policy system that keeps shared data shapes compatible as producers, consumers, and replayers evolve.
