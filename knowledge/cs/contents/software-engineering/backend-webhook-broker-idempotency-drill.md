---
schema_version: 3
title: Backend Webhook Broker Idempotency Drill
concept_id: software-engineering/backend-webhook-broker-idempotency-drill
canonical: false
category: software-engineering
difficulty: intermediate
doc_role: drill
level: intermediate
language: mixed
source_priority: 74
mission_ids:
- missions/backend
review_feedback_tags:
- backend
- webhook
- message-broker
- idempotency
aliases:
- backend webhook broker idempotency drill
- webhook broker ack idempotency exercise
- HTTP 2xx ack offset drill
- durable handoff idempotency drill
- webhook broker 중복 처리 드릴
symptoms:
- webhook 200 OK와 broker ack/offset commit을 같은 성공 신호로 취급한다
- durable handoff 전에 acknowledgment를 보내도 되는지 판단하지 못한다
- provider event id와 message id 중 무엇을 dedup key로 삼을지 헷갈린다
intents:
- drill
- troubleshooting
- design
prerequisites:
- software-engineering/webhook-broker-boundary-primer
- software-engineering/idempotency-retry-consistency-boundaries
next_docs:
- software-engineering/outbox-inbox-domain-events
- system-design/message-queue-basics
- system-design/idempotency-key-store-dedup-window-replay-safe-retry-design
linked_paths:
- contents/software-engineering/webhook-and-broker-boundary-primer.md
- contents/software-engineering/idempotency-retry-consistency-boundaries.md
- contents/software-engineering/outbox-inbox-domain-events.md
- contents/software-engineering/inbound-adapter-testing-matrix.md
- contents/system-design/message-queue-basics.md
- contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md
confusable_with:
- software-engineering/webhook-broker-boundary-primer
- software-engineering/idempotency-retry-consistency-boundaries
- software-engineering/outbox-inbox-domain-events
forbidden_neighbors:
- contents/software-engineering/api-design-error-handling.md
expected_queries:
- backend webhook 200 OK와 broker ack 차이를 idempotency 문제로 연습하고 싶어
- webhook durable handoff 전에 2xx를 보내면 왜 위험한지 드릴해줘
- broker consumer offset commit과 DB commit 순서를 어떻게 판단해?
- provider event id와 message id를 dedup key로 고르는 문제를 풀어줘
- backend inbound adapter 중복 처리 테스트를 어떻게 나눠?
contextual_chunk_prefix: |
  이 문서는 backend webhook broker idempotency drill이다. HTTP 2xx,
  broker ack, offset commit, durable handoff, provider event id, message id,
  inbox table, duplicate delivery, replay-safe response 같은 미션 질문을
  선택 문제로 매핑한다.
---
# Backend Webhook Broker Idempotency Drill

> 한 줄 요약: webhook과 broker consumer는 둘 다 중복 배달될 수 있는 inbound adapter이고, acknowledgment를 언제 보내느냐가 안정성의 핵심이다.

**난이도: Intermediate**

## 문제 1

상황:

```text
결제 webhook payload를 메모리에서 파싱한 뒤 바로 200 OK를 보낸다.
inbox row나 providerEventId 저장은 비동기 작업이 나중에 한다.
```

답:

위험하다. provider는 2xx를 재전송 중단 신호로 볼 수 있는데, durable handoff가 아직 없다.
최소한 provider event id와 raw payload를 저장하거나 같은 사실을 재처리할 수 있는 durable 기록이 먼저 필요하다.

## 문제 2

상황:

```text
Kafka consumer가 메시지를 받자마자 offset을 commit하고, 그 뒤 DB에 주문 상태를 반영한다.
DB commit 중 장애가 나면 메시지는 다시 오지 않는다.
```

답:

ack/offset commit이 너무 이르다. broker 관점 성공 신호는 DB commit과 dedup 기록 이후에 맞추는 편이 안전하다.
그렇지 않으면 broker는 처리 완료로 보지만 application state에는 반영되지 않는 구멍이 생긴다.

## 문제 3

상황:

```text
webhook에는 X-Provider-Event-Id가 있고, broker 메시지에는 messageId와 paymentId가 있다.
둘 다 결제 상태 변경을 전달한다.
```

답:

dedup key는 채널별 stable external identity를 기준으로 잡는다.
webhook은 provider event id가 1차 후보이고, broker는 source topic과 event id 또는 business event id를 조합한다.
단순히 internal paymentId만 쓰면 서로 다른 상태 변경을 하나로 뭉갤 수 있다.

## 빠른 체크

| 질문 | webhook | broker consumer |
|---|---|---|
| 성공 신호 | HTTP 2xx | ack/nack 또는 offset commit |
| retry owner | provider/sender | broker/listener policy |
| dedup 후보 | provider event id | event id + topic/source |
| 먼저 durable해야 할 것 | inbox/raw payload | state change + dedup record |

## 한 줄 정리

backend inbound adapter는 protocol 이름보다 acknowledgment와 durable idempotency 경계를 먼저 읽어야 한다.
