# Pricing Billing Master Note

> 한 줄 요약: pricing and billing are about turning usage into money without losing auditability, proration correctness, or customer trust.

**Difficulty: Advanced**

> retrieval-anchor-keywords: billing, pricing, usage metering, invoice, ledger, proration, rating, quota, revenue recognition, reconciliation, credits, refunds, overage, metered events

> related docs:
> - [Billing / Usage Metering System 설계](../contents/system-design/billing-usage-metering-system-design.md)
> - [Payment System Ledger, Idempotency, Reconciliation](../contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md)
> - [멱등성 키와 중복 방지](../contents/database/idempotency-key-and-deduplication.md)
> - [Multi-tenant SaaS 격리 설계](../contents/system-design/multi-tenant-saas-isolation-design.md)
> - [Rate Limiter 설계](../contents/system-design/rate-limiter-design.md)
> - [Workflow Orchestration / Saga 설계](../contents/system-design/workflow-orchestration-saga-design.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Pricing decides what the service is worth.
Billing decides what was actually used and what must be charged.

The system must connect:

- usage events
- rating and pricing tables
- invoice generation
- credits/refunds
- reconciliation and disputes

## 깊이 들어가기

### 1. Usage is noisy, ledger is clean

Raw usage events can be duplicate, delayed, or partial.
Billing ledger entries must be deterministic and auditable.

Read with:

- [Billing / Usage Metering System 설계](../contents/system-design/billing-usage-metering-system-design.md)

### 2. Proration is a contract problem

When plans change mid-cycle, the system needs a consistent effective date model.

### 3. Quota and overage tie pricing to control

Usage limits are not only a guardrail; they often precede billing or overage charges.

Read with:

- [Rate Limiter 설계](../contents/system-design/rate-limiter-design.md)

### 4. Reconciliation is mandatory

If invoice totals and ledger totals diverge, the system needs a repeatable correction path.

Read with:

- [Payment System Ledger, Idempotency, Reconciliation](../contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md)

## 실전 시나리오

### 시나리오 1: monthly invoice is wrong after plan upgrade

Likely cause:

- proration boundary incorrect
- effective date mismatch

### 시나리오 2: usage is double-counted

Likely cause:

- metering dedupe missing
- replayed event not idempotent

### 시나리오 3: customer dispute requires audit trail

Likely cause:

- ledger insufficiently descriptive
- missing reconciliation record

## 코드로 보기

### Billing pipeline sketch

```text
usage event -> normalize -> dedupe -> aggregate -> rate -> ledger -> invoice
```

### Idempotent metering write

```sql
INSERT INTO usage_ledger(event_id, tenant_id, units, occurred_at)
VALUES (?, ?, ?, ?)
ON CONFLICT (event_id) DO NOTHING;
```

### Proration idea

```java
Money prorated = pricingService.prorate(oldPlan, newPlan, effectiveDate);
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Real-time billing | Immediate visibility | Complex and expensive | High-value overage |
| Batch billing | Stable and simple | Delayed invoices | Most SaaS products |
| Usage-ledger separation | Auditable | More moving parts | Regulated or enterprise billing |
| Soft quota + overage | Better UX | More accounting work | Growth products |

## 꼬리질문

> Q: Why separate usage events from invoice lines?
> Intent: checks metering vs billing distinction.
> Core: raw usage is noisy; invoices need normalized, auditable entries.

> Q: Why is proration hard?
> Intent: checks mid-cycle policy reasoning.
> Core: plan changes and effective dates overlap with billing periods.

> Q: Why is reconciliation mandatory in billing?
> Intent: checks trust and auditability.
> Core: external systems and internal ledgers can diverge.

## 한 줄 정리

Pricing and billing are a financial data pipeline, not just a charge API, and they must be auditable, idempotent, and reconciliation-friendly.
