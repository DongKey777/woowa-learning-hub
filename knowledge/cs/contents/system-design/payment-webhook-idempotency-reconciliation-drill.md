---
schema_version: 3
title: Payment Webhook Idempotency Reconciliation Drill
concept_id: system-design/payment-webhook-idempotency-reconciliation-drill
canonical: false
category: system-design
difficulty: intermediate
doc_role: drill
level: intermediate
language: mixed
source_priority: 74
mission_ids:
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- payment-webhook
- idempotency
- reconciliation
- durable-acceptance
aliases:
- payment webhook idempotency drill
- 결제 webhook reconciliation drill
- PG callback duplicate event drill
- provider event dedup reconciliation
- payment webhook 200 OK timing exercise
symptoms:
- 같은 결제 webhook이 두 번 오면 주문 상태가 두 번 바뀔까 봐 불안하다
- 200 OK를 언제 보내야 결제사가 재전송을 멈춰도 안전한지 모르겠다
- 내부 주문 상태와 PG 상태가 어긋났을 때 reconciliation이 왜 필요한지 헷갈린다
intents:
- drill
- troubleshooting
- design
prerequisites:
- system-design/payment-system-ledger-idempotency-reconciliation-design
- software-engineering/shopping-cart-payment-webhook-idempotency-bridge
next_docs:
- system-design/webhook-consumer-platform-design
- system-design/reconciliation-window-cutoff-control-design
- database/idempotency-key-and-deduplication
linked_paths:
- contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md
- contents/system-design/webhook-consumer-platform-design.md
- contents/system-design/reconciliation-window-cutoff-control-design.md
- contents/software-engineering/shopping-cart-payment-webhook-idempotency-bridge.md
- contents/database/idempotency-key-and-deduplication.md
- contents/spring/spring-payment-approval-db-failure-compensation-idempotency-primer.md
confusable_with:
- system-design/payment-system-ledger-idempotency-reconciliation-design
- software-engineering/shopping-cart-payment-webhook-idempotency-bridge
- system-design/webhook-consumer-platform-design
forbidden_neighbors:
- contents/database/shopping-cart-payment-idempotency-stock-bridge.md
expected_queries:
- payment webhook idempotency와 reconciliation을 문제로 연습하고 싶어
- 결제사 callback을 두 번 받았을 때 200 OK를 언제 보내야 해?
- PG 상태와 내부 주문 상태가 다를 때 reconciliation drill을 줘
- shopping-cart 결제 webhook 중복 이벤트를 system design으로 판단해줘
contextual_chunk_prefix: |
  이 문서는 payment webhook idempotency reconciliation drill이다.
  provider event id, duplicate callback, durable acceptance, 200 OK timing,
  ledger, PG/internal state mismatch, reconciliation window 같은 질문을
  system design 판별 문제로 매핑한다.
---
# Payment Webhook Idempotency Reconciliation Drill

> 한 줄 요약: webhook은 "한 번 온 HTTP 요청"이 아니라 "같은 사실이 다시 배달될 수 있는 외부 이벤트"다.

**난이도: Intermediate**

## 문제 1

상황:

```text
PG webhook을 받자마자 order.confirm()을 호출하고 200 OK를 보낸다. providerEventId는 저장하지 않는다.
```

답:

중복 반영 위험이 있다. provider가 같은 event를 재전송하면 새 사실인지 replay인지 구분할 key가 없기 때문이다.

## 문제 2

상황:

```text
raw webhook payload와 providerEventId를 inbox table에 commit한 뒤 200 OK를 보낸다.
```

답:

durable acceptance 경계가 생긴다. 후속 주문 반영이 늦어져도 이벤트를 잃지 않고 재처리할 수 있다.

## 문제 3

상황:

```text
PG dashboard는 CAPTURED인데 내부 주문은 PENDING이다.
```

답:

reconciliation 대상이다. 내부 ledger/inbox와 PG 상태를 비교해 누락된 상태 전이를 보정해야 한다.

## 빠른 체크

| 질문 | 필요한 장치 |
|---|---|
| 같은 event인지 어떻게 아는가 | provider event id / idempotency key |
| 200 OK 전에 무엇이 durable해야 하나 | inbox row / raw payload |
| 내부와 PG가 어긋나면 어떻게 찾나 | reconciliation job |
| 이미 처리된 event가 다시 오면 | replay-safe response |
