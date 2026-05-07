---
schema_version: 3
title: Payment After Commit Outbox Mission Bridge
concept_id: spring/payment-after-commit-outbox-mission-bridge
canonical: false
category: spring
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: mixed
source_priority: 78
mission_ids:
- missions/payment
- missions/shopping-cart
review_feedback_tags:
- payment
- after-commit
- outbox
- transaction-boundary
aliases:
- payment after commit outbox bridge
- 결제 after commit outbox 브리지
- payment transaction outbox mission bridge
- order paid event after commit
- payment side effect handoff bridge
symptoms:
- 결제 확정 트랜잭션 안에서 알림, 정산 이벤트, 외부 API 호출까지 모두 처리한다
- AFTER_COMMIT과 outbox를 둘 다 "커밋 후 실행" 정도로만 이해한다
- 주문은 commit됐는데 이벤트 발행 실패 시 재처리 근거가 없다
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/service-layer-external-io-after-commit-outbox-primer
- spring/payment-approval-db-failure-compensation-idempotency-primer
next_docs:
- software-engineering/outbox-inbox-domain-events
- system-design/payment-system-ledger-idempotency-reconciliation-design
- system-design/webhook-consumer-platform-design
linked_paths:
- contents/spring/spring-service-layer-external-io-after-commit-outbox-primer.md
- contents/spring/spring-payment-approval-db-failure-compensation-idempotency-primer.md
- contents/spring/shopping-cart-order-complete-after-commit-outbox-bridge.md
- contents/software-engineering/outbox-inbox-domain-events.md
- contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md
- contents/system-design/webhook-consumer-platform-design.md
confusable_with:
- spring/service-layer-external-io-after-commit-outbox-primer
- spring/payment-approval-db-failure-compensation-idempotency-primer
- software-engineering/outbox-inbox-domain-events
forbidden_neighbors:
- contents/spring/spring-transaction-propagation-required-requires-new-rollbackonly-primer.md
expected_queries:
- payment 미션에서 AFTER_COMMIT과 outbox를 어떻게 구분해야 해?
- 결제 확정 후 알림이나 정산 이벤트를 트랜잭션 안에서 처리하면 왜 위험해?
- 주문 commit은 됐는데 이벤트 발행이 실패하면 outbox가 왜 필요해?
- payment side effect를 after commit listener로 충분히 처리해도 되는 경우를 알려줘
- 결제 완료 이벤트 발행을 Spring transaction boundary로 설명해줘
contextual_chunk_prefix: |
  이 문서는 payment after commit outbox mission_bridge다. payment confirmed,
  order paid event, AFTER_COMMIT listener, outbox, transaction boundary,
  side effect handoff, publish failure, retry evidence 같은 결제 미션 리뷰
  문장을 Spring transaction boundary와 outbox pattern으로 매핑한다.
---
# Payment After Commit Outbox Mission Bridge

> 한 줄 요약: 결제 확정 뒤의 부작용은 "커밋 뒤 실행"이면 모두 같은 게 아니라, 잃어도 되는 후속 작업인지 반드시 재처리해야 하는 이벤트인지에 따라 `AFTER_COMMIT`과 outbox가 갈린다.

**난이도: Intermediate**

## 미션 진입 증상

| payment 장면 | 먼저 볼 경계 |
|---|---|
| 주문 확정 뒤 알림을 보낸다 | 실패해도 재시도 근거가 필요한가 |
| 정산/배송 이벤트를 발행한다 | 반드시 전달해야 하는 business event인가 |
| transaction 안에서 외부 API가 오래 돈다 | DB connection/lock을 붙잡는가 |
| commit 뒤 publish 실패 | outbox row가 남아 있는가 |

## CS concept 매핑

`AFTER_COMMIT`과 outbox는 둘 다 "DB commit 이후"라는 말로 묶이지만 운영 의미가 다르다.

| 선택 | 맞는 장면 | 약한 점 |
|---|---|---|
| `AFTER_COMMIT` listener | 같은 프로세스 안 후속 작업, 실패해도 별도 보상 가능 | process crash나 publish 실패 재처리 근거가 약하다 |
| outbox | 주문/결제 확정 사실을 반드시 다른 worker/system에 전달 | relay, 중복 발행, 소비자 멱등성까지 운영해야 한다 |

payment 미션에서 알림처럼 사용자 편의 작업은 `AFTER_COMMIT`으로 시작할 수 있다.
하지만 정산, 배송, 포인트 적립처럼 "결제 완료 사실"을 다른 경계가 반드시 받아야 하면 outbox row가 더 안전하다.

## 리뷰 신호

- "트랜잭션 안에서 외부 호출이 길어요"는 DB commit 경계를 짧게 만들라는 신호다.
- "커밋 뒤 이벤트 발행 실패는 어떻게 복구하나요?"는 outbox 없이 설명하기 어렵다는 뜻이다.
- "`AFTER_COMMIT`이면 안전한가요?"는 process crash와 retry 근거를 같이 보라는 말이다.
- "같은 이벤트가 두 번 발행되면요?"는 consumer idempotency까지 포함해야 한다는 신호다.

## 판단 순서

1. payment/order 상태 변경은 짧은 DB transaction으로 commit한다.
2. commit 후 작업이 best-effort인지 durable delivery인지 나눈다.
3. durable delivery가 필요하면 outbox row를 같은 transaction에 저장한다.
4. outbox relay와 consumer는 event id 기준으로 중복 처리 가능해야 한다.

이 구분이 잡히면 payment 미션의 후속 부작용 리뷰가 `@Transactional` 옵션 논쟁이 아니라 재처리 가능한 handoff 설계로 정리된다.
