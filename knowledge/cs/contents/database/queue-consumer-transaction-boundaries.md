---
schema_version: 3
title: Queue Consumer Transaction Boundaries
concept_id: database/queue-consumer-transaction-boundaries
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- queue-consumer
- ack-boundary
- transactional-inbox
- outbox
aliases:
- queue consumer transaction
- ack boundary
- commit boundary
- message processing
- consumer retry
- poison message
- commit then ack
- ack then commit 위험
- consumer transaction boundary
- 메시지 ack DB commit 순서
symptoms:
- queue consumer에서 DB commit 전에 ack를 보내 메시지 유실 위험을 만들고 있어
- ack 전에 죽은 중복 재전달을 transactional inbox나 dedup 없이 처리해 같은 side effect를 반복할 수 있어
- 외부 API 호출까지 긴 DB transaction 안에 넣어 lock, ack delay, retry 폭주가 커지고 있어
intents:
- troubleshooting
- design
prerequisites:
- database/transaction-boundary-isolation-locking-framework
- database/exactly-once-myths-db-queue
next_docs:
- database/transactional-inbox-dedup-design
- database/outbox-saga-eventual-consistency
- database/queue-claim-skip-locked-fairness
linked_paths:
- contents/database/transaction-boundary-isolation-locking-decision-framework.md
- contents/database/exactly-once-myths-db-queue.md
- contents/database/transactional-inbox-dedup-design.md
- contents/database/outbox-saga-eventual-consistency.md
- contents/database/queue-claim-skip-locked-fairness.md
confusable_with:
- database/exactly-once-myths-db-queue
- database/transactional-inbox-dedup-design
- database/outbox-saga-eventual-consistency
forbidden_neighbors: []
expected_queries:
- queue consumer에서 DB commit과 message ack 순서를 왜 commit then ack로 잡아야 해?
- ack before commit이 메시지 유실을 만들고 ack after commit이 중복을 만들 수 있는 흐름을 설명해줘
- consumer transaction 안에 외부 API 호출을 오래 넣으면 어떤 lock과 retry 비용이 생겨?
- poison message를 무한 retry하지 않고 DLQ와 수동 재처리로 넘기는 기준을 알려줘
- transactional inbox와 dedup으로 consumer 중복 처리를 어떻게 방어해?
contextual_chunk_prefix: |
  이 문서는 queue consumer에서 DB commit과 broker ack boundary를 맞추고 duplicate delivery, message loss, poison message, transactional inbox를 다루는 advanced playbook이다.
  메시지 ack DB commit 순서, commit then ack, ack then commit 위험 질문이 본 문서에 매핑된다.
---
# Queue Consumer Transaction Boundaries

> 한 줄 요약: 소비자 트랜잭션은 메시지 ack와 DB commit의 경계를 잘못 잡는 순간 중복과 유실을 동시에 만든다.

**난이도: 🔴 Advanced**

관련 문서: [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md), [Exactly-Once 신화와 DB + Queue 경계](./exactly-once-myths-db-queue.md), [Transactional Inbox와 Dedup Design](./transactional-inbox-dedup-design.md), [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md), [Queue Claim with `SKIP LOCKED`, Fairness, and Starvation Trade-offs](./queue-claim-skip-locked-fairness.md)
retrieval-anchor-keywords: queue consumer transaction, ack boundary, commit boundary, message processing, consumer retry, skip locked, queue claim

## 핵심 개념

Queue consumer는 메시지를 받고, 비즈니스 처리를 수행한 뒤, ack를 보내는 흐름을 가진다.  
이때 트랜잭션 경계를 어디에 두느냐가 정합성을 좌우한다.

왜 중요한가:

- ack 전에 죽으면 메시지가 다시 올 수 있다
- commit 전에 ack하면 메시지를 잃을 수 있다
- 처리 범위를 너무 넓히면 락과 시간 비용이 커진다

소비자 트랜잭션은 단순히 DB를 감싸는 것이 아니라, **메시지 전달과 상태 저장의 경계를 조정하는 일**이다.

## 깊이 들어가기

### 1. ack와 commit의 순서

가장 흔한 원칙은 `commit -> ack`다.

- DB 변경이 먼저 확정된다
- 그 다음 메시지를 처리 완료로 알린다

이 순서를 바꾸면 메시지 유실이 생길 수 있다.
다만 claim 단계에서 `SKIP LOCKED`를 쓰는 경우, 처리 순서와 fairness는 별도 문제로 분리해서 봐야 한다.

### 2. 트랜잭션을 너무 크게 잡으면

- 메시지 하나 처리 중 lock이 오래 유지된다
- DB가 느려지면 브로커 ack도 늦어진다
- 실패 시 재시도가 무거워진다

즉 소비자 트랜잭션은 가능한 짧아야 한다.

### 3. 중간 처리와 외부 호출

소비자가 외부 API를 호출해야 한다면 더 조심해야 한다.

- 외부 호출 전 DB commit이 끝났는지
- 외부 호출 실패 시 재시도 전략이 있는지
- 중복 호출이 허용되는지

외부 side effect는 트랜잭션 경계 밖으로 빼거나 outbox/consumer idempotency와 같이 설계해야 한다.

### 4. poison message

반복 실패하는 메시지는 무한 retry하면 안 된다.

- DLQ로 보낸다
- 실패 사유를 저장한다
- 수동 재처리 경로를 둔다

## 실전 시나리오

### 시나리오 1: DB commit 전에 ack를 보내버림

브로커는 처리 완료로 생각하지만 DB는 반영되지 않는다.  
이건 메시지 유실이다.

### 시나리오 2: ack 전에 죽어서 같은 메시지가 다시 옴

처리 완료가 이미 저장돼 있으면 inbox dedup으로 방어해야 한다.

### 시나리오 3: 외부 호출이 긴 소비자

트랜잭션이 길어지면 ack도 늦고 재시도도 폭주한다.  
이런 경우 경계를 더 잘게 나누어야 한다.

## 코드로 보기

```java
try {
    tx.begin();
    handleMessage(event);
    tx.commit();
    broker.ack(message);
} catch (Exception e) {
    tx.rollback();
    broker.nack(message);
}
```

```text
bad:
  ack first -> commit later

good:
  commit first -> ack later
```

queue consumer의 핵심은 메시지 처리와 ack의 경계를 정확히 잡아 **유실과 중복을 동시에 피하는 것**이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| commit then ack | 안전하다 | 약간 늦을 수 있다 | 일반적 해법 |
| ack then commit | 빠르다 | 유실 위험이 있다 | 거의 없음 |
| large transaction | 단순하다 | 락과 재시도 비용이 크다 | 드문 경우 |
| inbox + short tx | 강하다 | 구현이 복잡하다 | 중요한 소비자 |

## 꼬리질문

> Q: consumer에서 왜 commit과 ack 순서가 중요한가요?
> 의도: 유실과 중복을 동시에 이해하는지 확인
> 핵심: 순서가 뒤집히면 메시지 유실 또는 중복이 생긴다

> Q: 소비자 트랜잭션을 크게 잡으면 왜 안 좋은가요?
> 의도: 락과 재시도 비용을 아는지 확인
> 핵심: 처리 시간이 길어지고 ack가 늦어진다

> Q: poison message는 어떻게 다뤄야 하나요?
> 의도: 무한 retry의 위험을 아는지 확인
> 핵심: DLQ와 수동 재처리 경로가 필요하다

## 한 줄 정리

Queue consumer의 트랜잭션 경계는 commit과 ack의 순서를 안전하게 맞추는 일이며, 보통 `commit -> ack`가 기본이다.
