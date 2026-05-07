---
schema_version: 3
title: Payment Ledger State Reconciliation Mission Bridge
concept_id: database/payment-ledger-state-reconciliation-mission-bridge
canonical: false
category: database
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: mixed
source_priority: 78
mission_ids:
- missions/payment
- missions/shopping-cart
review_feedback_tags:
- payment-ledger
- reconciliation
- idempotency-key
- state-transition
aliases:
- payment ledger reconciliation bridge
- 결제 원장 상태 재조정 브리지
- payment state ledger mission bridge
- PG internal state mismatch bridge
- payment idempotency ledger bridge
symptoms:
- PG dashboard는 성공인데 내부 payment row는 PENDING으로 남아 있다
- 결제 상태를 단일 status 컬럼만으로 처리해 환불, 취소, 재시도 이력을 설명하지 못한다
- 같은 paymentKey 재시도가 새 승인인지 기존 결과 재생인지 구분하지 못한다
intents:
- mission_bridge
- troubleshooting
- design
prerequisites:
- system-design/payment-system-ledger-idempotency-reconciliation-design
- database/idempotency-key-and-deduplication
next_docs:
- system-design/webhook-consumer-platform-design
- software-engineering/outbox-inbox-domain-events
- database/compare-and-set-version-columns
linked_paths:
- contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md
- contents/database/idempotency-key-and-deduplication.md
- contents/database/compare-and-set-version-columns.md
- contents/database/transaction-basics.md
- contents/software-engineering/outbox-inbox-domain-events.md
- contents/system-design/webhook-consumer-platform-design.md
confusable_with:
- system-design/payment-system-ledger-idempotency-reconciliation-design
- database/idempotency-key-and-deduplication
- database/compare-and-set-version-columns
forbidden_neighbors:
- contents/database/index-basics.md
expected_queries:
- payment 미션에서 PG는 성공인데 내부 상태가 PENDING이면 어떤 reconciliation을 해야 해?
- 결제 상태를 단일 status보다 ledger event로 남겨야 하는 이유를 미션 장면으로 설명해줘
- 같은 paymentKey 재시도가 들어오면 새 결제인지 replay인지 DB에서 어떻게 판단해?
- payment ledger와 idempotency key를 주문 확정 흐름에 어떻게 연결해?
- PG 내부 상태 mismatch를 database 관점 mission bridge로 풀어줘
contextual_chunk_prefix: |
  이 문서는 payment ledger state reconciliation mission_bridge다. PG success
  but internal pending, paymentKey replay, ledger event, idempotency key,
  state transition, reconciliation job, internal/external mismatch 같은
  결제 미션 질문을 database consistency와 state recording 문제로 매핑한다.
---
# Payment Ledger State Reconciliation Mission Bridge

> 한 줄 요약: 결제 상태는 마지막 `status` 하나보다, 어떤 외부 사실을 어떤 키로 받아 어떤 상태 전이를 남겼는지가 나중에 재시도와 정산을 살린다.

**난이도: Intermediate**

## 미션 진입 증상

| payment 장면 | 먼저 볼 DB 질문 |
|---|---|
| PG는 `CAPTURED`, 내부는 `PENDING` | reconciliation 대상인가 |
| 같은 `paymentKey`로 재시도 | 기존 결과 replay인가 새 attempt인가 |
| 환불/취소가 status overwrite로만 남음 | ledger event가 필요한가 |
| webhook과 approve 응답이 둘 다 들어옴 | 같은 external fact로 dedup되는가 |

## CS concept 매핑

payment 미션에서 DB는 단순 저장소가 아니라 "나중에 같은 사실이 다시 와도 같은 답을 줄 수 있는 근거"를 보관한다.
그래서 최소한 아래 셋은 분리해서 생각한다.

- idempotency record: 같은 요청 시도인지 판정한다.
- payment state: 현재 결제의 business 상태를 보여 준다.
- ledger/event row: 어떤 승인, 취소, 환불 사실이 언제 들어왔는지 설명한다.

단일 `payment.status = PAID`만 있으면 지금 화면은 그릴 수 있지만, `PG는 성공인데 우리는 pending`, `취소 callback이 늦게 도착`, `같은 승인 event가 재전송` 같은 질문에 답하기 어렵다.

## 리뷰 신호

- "PG 상태와 내부 상태가 어긋나면 어떻게 맞추나요?"는 reconciliation job과 비교 기준을 묻는 말이다.
- "결제 재시도면 그냥 다시 approve 하면 되나요?"는 idempotency key/status 조회가 먼저라는 신호다.
- "취소/환불 이력을 어디서 보나요?"는 overwrite status보다 ledger event를 검토하라는 뜻이다.
- "webhook이 늦게 오면 상태를 덮어써도 되나요?"는 version/state transition guard가 필요한지 보라는 말이다.

## 판단 순서

1. payment attempt key와 provider transaction id를 DB에 남긴다.
2. 같은 키가 다시 오면 새 외부 호출보다 기존 payment state와 ledger를 조회한다.
3. 외부 PG 상태와 내부 상태가 다르면 reconciliation 후보로 표시한다.
4. 상태 전이는 현재 상태에서 허용되는 전이인지 확인하고, 필요하면 version/CAS로 보호한다.

이 흐름을 잡으면 payment 미션 리뷰가 "예외 처리"가 아니라 "재시도 가능한 기록 설계"로 설명된다.
