---
schema_version: 3
title: Checkout Sync vs Async Workflow Bridge
concept_id: system-design/checkout-sync-vs-async-workflow-bridge
canonical: false
category: system-design
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: mixed
source_priority: 76
mission_ids:
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- checkout-workflow
- sync-vs-async
- outbox
- job-queue
aliases:
- checkout sync vs async workflow bridge
- checkout 동기 비동기 workflow bridge
- 결제 후속 작업 outbox queue
- 주문 완료 알림 재고 쿠폰 비동기
- direct api vs job queue checkout
symptoms:
- checkout 요청 안에서 결제, 재고, 쿠폰, 알림, 이메일을 모두 끝내려다 timeout이 난다
- 주문은 commit됐는데 후속 작업 실패를 어떻게 복구할지 모르겠다
- outbox, job queue, direct API 중 어디서 시작해야 할지 헷갈린다
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- system-design/consistency-idempotency-async-workflow-foundations
- system-design/per-key-queue-vs-direct-api-primer
next_docs:
- spring/shopping-cart-order-complete-after-commit-outbox-bridge
- system-design/job-queue-design
- software-engineering/outbox-inbox-domain-events
linked_paths:
- contents/system-design/consistency-idempotency-async-workflow-foundations.md
- contents/system-design/per-key-queue-vs-direct-api-primer.md
- contents/system-design/job-queue-design.md
- contents/spring/shopping-cart-order-complete-after-commit-outbox-bridge.md
- contents/software-engineering/outbox-inbox-domain-events.md
- contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md
confusable_with:
- system-design/per-key-queue-vs-direct-api-primer
- spring/shopping-cart-order-complete-after-commit-outbox-bridge
- software-engineering/outbox-inbox-domain-events
forbidden_neighbors:
- contents/system-design/read-after-write-consistency-basics.md
expected_queries:
- checkout에서 동기로 끝낼 일과 비동기로 넘길 일을 어떻게 나눠?
- 주문 완료 후 알림 재고 쿠폰 처리를 outbox queue로 빼야 하는 기준은?
- shopping-cart checkout timeout을 direct API vs job queue 관점으로 설명해줘
- 결제 후속 작업 실패를 system design bridge로 연결해줘
contextual_chunk_prefix: |
  이 문서는 checkout sync vs async workflow mission_bridge다. checkout
  timeout, payment succeeded, order committed, inventory/coupon/notification
  follow-up, outbox, job queue, direct API, per-key ordering 같은 질문을
  shopping-cart/payment workflow design으로 매핑한다.
---
# Checkout Sync vs Async Workflow Bridge

> 한 줄 요약: checkout 요청 안에서 반드시 끝나야 하는 일과, commit 이후 안전하게 이어도 되는 일을 분리해야 timeout과 복구 문제가 줄어든다.

**난이도: Intermediate**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "checkout 요청 안에서 결제, 재고, 쿠폰, 알림을 모두 끝내려다 timeout이 나요" | 장바구니 주문 완료 API critical path가 길어진 장면 | 사용자 응답 전에 반드시 끝낼 일과 commit 이후 이어도 되는 일을 나눈다 |
| "주문은 저장됐는데 알림 실패를 전체 rollback해야 하나요?" | 주문 commit 이후 후속 작업 실패 | transaction outcome과 retryable async follow-up을 분리한다 |
| "outbox, job queue, direct API 중 무엇부터 써야 할지 모르겠어요" | 결제 후 부작용 전달 설계 | durable handoff, retry, per-key ordering 필요 여부를 먼저 본다 |

## CS concept 매핑

| checkout 장면 | 더 가까운 설계 질문 |
|---|---|
| 주문 row와 결제 승인 결과를 같은 성공 응답에 반영 | synchronous critical path |
| 이메일, 알림, 추천 이벤트 발행 | async follow-up |
| 주문 commit 뒤 알림 실패 | outbox / retryable job |
| 같은 주문의 후속 작업 순서 보장 | per-key queue |
| 외부 API timeout이 checkout 전체를 잡아먹음 | timeout budget / bulkhead |

## 리뷰 신호

- "checkout이 너무 오래 걸립니다"는 critical path가 과하게 길다는 신호다.
- "주문은 됐는데 알림 실패 때문에 전체 rollback되나요?"는 transaction outcome을 나누라는 말이다.
- "outbox를 쓰면 결국 eventual consistency 아닌가요?"는 사용자 응답 계약과 후속 작업 보장을 분리하라는 질문이다.
- "같은 주문 이벤트 순서가 뒤집히면 어떡하죠?"는 per-key ordering이 필요한지 확인하라는 뜻이다.

## 판단 순서

1. 사용자에게 성공/실패로 즉시 알려야 하는 최소 상태를 정한다.
2. 그 상태를 commit하는 transaction boundary를 닫는다.
3. commit 이후 필요한 부작용은 outbox나 durable job으로 넘긴다.
4. 같은 order/payment key의 순서가 중요하면 per-key queue나 idempotent consumer를 둔다.

이렇게 나누면 checkout 요청이 외부 연동을 전부 붙잡고 늘어지는 구조에서 벗어나고, 실패한 후속 작업도 재처리 가능한 단위가 된다.
