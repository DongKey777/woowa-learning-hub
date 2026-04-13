# Service Ownership Master Note

> 한 줄 요약: service ownership is the operational contract that says who owns the code, the on-call path, the data boundary, and the incident response for a service.

**Difficulty: Advanced**

> retrieval-anchor-keywords: service ownership, on-call, ownership boundary, service catalog, handoff, pager, incident response, domain boundary, operational responsibility, team contract, runbook, escalation

> related docs:
> - [Service Ownership Catalog Boundaries](../contents/software-engineering/service-ownership-catalog-boundaries.md)
> - [On-call Ownership Boundaries](../contents/software-engineering/on-call-ownership-boundaries.md)
> - [Change Ownership Handoff Boundaries](../contents/software-engineering/change-ownership-handoff-boundaries.md)
> - [Modular Monolith Boundary Enforcement](../contents/software-engineering/modular-monolith-boundary-enforcement.md)
> - [DDD Bounded Context Failure Patterns](../contents/software-engineering/ddd-bounded-context-failure-patterns.md)
> - [Query Playbook](../rag/query-playbook.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

Ownership is what turns a service from "some code" into "a system someone can operate."

A service owner should be clear about:

- code responsibility
- data responsibility
- deploy/rollback responsibility
- on-call and incident response
- contract change responsibility

If ownership is fuzzy, the service becomes a shared liability.

## 깊이 들어가기

### 1. Service ownership is not just team assignment

Ownership must include production readiness and incident response, not just feature work.

Read with:

- [Service Ownership Catalog Boundaries](../contents/software-engineering/service-ownership-catalog-boundaries.md)

### 2. On-call and ownership boundaries must align

If one team owns the code but another team gets paged, the service is mis-owned.

Read with:

- [On-call Ownership Boundaries](../contents/software-engineering/on-call-ownership-boundaries.md)

### 3. Handoffs need explicit contracts

During team changes or service transfers, runbooks, alerts, and dependencies must be transferred too.

Read with:

- [Change Ownership Handoff Boundaries](../contents/software-engineering/change-ownership-handoff-boundaries.md)

### 4. Domain boundaries should match service ownership

Services that cut across unrelated domains often have fuzzy ownership and weak accountability.

Read with:

- [Modular Monolith Boundary Enforcement](../contents/software-engineering/modular-monolith-boundary-enforcement.md)
- [DDD Bounded Context Failure Patterns](../contents/software-engineering/ddd-bounded-context-failure-patterns.md)

## 실전 시나리오

### 시나리오 1: service is deployed but nobody can debug it

Likely cause:

- no clear owner
- missing runbook

### 시나리오 2: incident ping-pongs between teams

Likely cause:

- code ownership and on-call ownership differ

### 시나리오 3: ownership changes but alerts do not

Likely cause:

- handoff incomplete

## 코드로 보기

### Ownership metadata sketch

```yaml
service:
  name: order-service
  owner: payments-team
  oncall: payments-oncall
  runbook: linked
```

### Handoff checklist sketch

```text
owner -> runbook -> alerts -> dashboards -> dependencies -> rollback
```

### Service catalog idea

```text
service -> team -> domain -> on-call -> dependencies
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Single owner | Clear accountability | More load on team | Mature services |
| Shared ownership | Coverage | Ambiguity risk | Temporary migration |
| Split code/on-call | Flexibility | Incident confusion | Avoid if possible |

## 꼬리질문

> Q: Why does service ownership matter operationally?
> Intent: checks responsibility awareness.
> Core: someone must own incidents, changes, and rollback.

> Q: Why should on-call and code ownership align?
> Intent: checks incident path clarity.
> Core: the person paged needs enough context to act.

> Q: Why are handoff boundaries important?
> Intent: checks transferability and continuity.
> Core: ownership changes without alerts and runbooks create gaps.

## 한 줄 정리

Service ownership is the explicit operational contract that makes a service maintainable, pageable, and safely transferable.
