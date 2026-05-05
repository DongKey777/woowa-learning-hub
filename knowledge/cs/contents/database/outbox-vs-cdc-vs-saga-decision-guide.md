---
schema_version: 3
title: Outbox vs CDC vs Saga 결정 가이드
concept_id: database/outbox-vs-cdc-vs-saga-decision-guide
canonical: false
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- dual-write-vs-workflow-boundary
- outbox-vs-cdc-delivery-scope
- saga-does-not-replace-outbox
aliases:
- outbox vs cdc vs saga
- debezium outbox saga 차이
- 이벤트 발행 패턴 선택 가이드
- 트랜잭션 후 메시지 발행 방식 선택
- dual write 피하려면 뭐 써야 해
- outbox cdc saga chooser
- binlog cdc or outbox or saga
symptoms:
- DB 저장과 이벤트 발행을 같이 맞추려는데 outbox, CDC, saga를 같은 계층 선택지로 보고 있다
- 주문 저장 후 메시지 누락이 걱정되는데 어느 패턴이 발행 보장이고 어느 패턴이 보상 흐름인지 섞인다
- Debezium을 붙이면 saga까지 해결된다고 생각해서 설계 축이 뒤엉킨다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- database/transaction-basics
- database/outbox-saga-eventual-consistency
next_docs:
- database/cdc-debezium-outbox-binlog
- database/outbox-saga-eventual-consistency
- database/saga-pivot-transaction-design
linked_paths:
- contents/database/cdc-debezium-outbox-binlog.md
- contents/database/outbox-saga-eventual-consistency.md
- contents/database/saga-pivot-transaction-design.md
- contents/database/transactional-inbox-dedup-design.md
- contents/database/idempotency-key-and-deduplication.md
confusable_with:
- database/cdc-debezium-outbox-binlog
- database/outbox-saga-eventual-consistency
- database/saga-pivot-transaction-design
forbidden_neighbors:
- contents/database/cdc-debezium-outbox-binlog.md
- contents/database/outbox-saga-eventual-consistency.md
- contents/software-engineering/outbox-vs-inbox-order-example-primer.md
expected_queries:
- 주문 저장 후 이벤트도 같이 내보내야 할 때 outbox, CDC, saga 중 무엇부터 골라야 해?
- dual write가 무서운데 Debezium만 붙이면 끝나는 문제야 아니면 outbox가 따로 필요해?
- outbox는 발행 보장이고 saga는 보상 흐름이라는 말을 한 번에 어떻게 구분해?
- binlog CDC와 application outbox를 같은 선택지로 비교할 때 먼저 보는 기준이 뭐야?
- 여러 서비스 결제 흐름이라 rollback이 어려운데 outbox와 saga를 어디서 나눠서 생각해야 해?
- outbox랑 inbox를 같은 비교축으로 보고 있었는데 CDC, saga랑은 어디서 분리해서 이해해야 해?
contextual_chunk_prefix: |
  이 문서는 학습자가 outbox, CDC, saga를 모두 "이벤트 비동기 처리 패턴"
  하나로 외울 때 같은 트랜잭션 안에서 발행 누락을 막는 문제, DB 변경을
  밖으로 흘려보내는 수집 방식, 여러 서비스에 걸친 보상 흐름을 분리해 주는
  beginner chooser다. dual write 회피, Debezium만 붙이면 끝나나, outbox가
  CDC를 대체하나, saga가 발행 보장도 해 주나, 결제 후 재고/포인트 보상은
  어느 층의 문제인가 같은 자연어 질문이 이 문서의 결정 매트릭스와 오선택
  패턴에 연결되도록 작성됐다.
---

# Outbox vs CDC vs Saga 결정 가이드

## 한 줄 요약

> 같은 로컬 트랜잭션의 이벤트 누락을 막는 1차 선택은 `outbox`, DB 변경을 외부로 안정적으로 흘려보내는 수집 방식은 `CDC`, 여러 서비스의 실패를 되감는 업무 흐름은 `saga`로 나눠 본다.

## 결정 매트릭스

| 지금 먼저 풀려는 문제 | 1차 선택 | 왜 이렇게 보나 |
|---|---|---|
| `order` 저장과 `order-created` 발행이 한 번에 맞물려야 함 | `outbox` | 같은 DB commit에 이벤트 기록을 묶어 dual write 누락을 줄인다 |
| 애플리케이션이 직접 publish하지 않고 DB 변경분을 밖으로 흘려보내고 싶음 | `CDC` | binlog/WAL을 읽어 변경 사실을 수집하는 경로라 발행 채널과 분리된다 |
| 결제, 재고, 포인트처럼 여러 서비스 단계 실패 시 보상 순서를 설계해야 함 | `saga` | 발행 기술이 아니라 분산 업무 흐름과 compensating action의 문제다 |
| 이벤트 누락도 막고 운영상 중앙 수집도 필요함 | `outbox` + `CDC` 조합 | outbox가 의미를 만들고 CDC가 전달 파이프를 담당할 수 있다 |
| "메시지는 갔는데 후속 단계가 일부만 성공"이 걱정됨 | `saga` + idempotency | 발행 자체보다 단계별 재시도와 보상 규칙이 핵심이다 |

짧게 고정하면 outbox는 "무엇을 남길지", CDC는 "어떻게 가져갈지", saga는 "실패를 어떻게 되감을지"에 가깝다.

## 흔한 오선택

가장 흔한 오선택은 Debezium 같은 CDC를 붙이면 dual write 문제가 자동으로 끝난다고 믿는 것이다. 학습자 표현으로는 "어차피 binlog를 읽어 가니까 이벤트 유실도 없지 않나?"에 가깝다. 하지만 CDC는 이미 기록된 변경을 밖으로 전달하는 수집 경로이고, 어떤 비즈니스 이벤트를 어떤 시점에 남길지는 outbox나 명시적 모델링이 정한다.

반대로 outbox를 saga 대체재로 보는 것도 자주 틀린다. outbox는 "주문 저장과 이벤트 기록"을 같은 로컬 트랜잭션에 묶는 데 강하지만, 결제는 성공했고 재고는 실패한 뒤 무엇을 보상할지까지 결정해 주지는 않는다. 그 장면은 메시지 전달 기술이 아니라 업무 단계 orchestration 문제다.

또 하나 흔한 오선택은 saga를 도입하면 발행 보장도 같이 해결된다고 생각하는 것이다. "보상 로직만 있으면 중간 이벤트 누락은 나중에 맞출 수 있지 않나?"처럼 들리지만, 시작 이벤트가 빠지면 saga 자체가 출발하지 못할 수 있다. 그래서 로컬 commit 이후의 발행 보장과 다중 서비스 보상 흐름을 같은 박스로 다루면 설계 축이 섞인다.

## 다음 학습

DB commit과 이벤트 발행을 같은 로컬 트랜잭션에 어떻게 묶는지 먼저 잡고 싶으면 [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md)와 [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md)를 이어서 보면 된다.

여러 서비스 단계의 보상 흐름과 pivot 지점을 더 분명히 보고 싶으면 [Saga Pivot Transaction Design](./saga-pivot-transaction-design.md)으로 내려가면 된다.

중복 소비와 재처리 방어까지 같이 보려면 [Transactional Inbox와 Dedup 설계](./transactional-inbox-dedup-design.md)와 [Idempotency Key와 Deduplication](./idempotency-key-and-deduplication.md)을 다음 문서로 잡으면 된다.
