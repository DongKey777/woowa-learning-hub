---
schema_version: 3
title: CDC, Debezium, Outbox, Binlog
concept_id: database/cdc-debezium-outbox-binlog
canonical: true
category: database
difficulty: advanced
doc_role: bridge
level: advanced
language: ko
source_priority: 83
mission_ids: []
review_feedback_tags:
- cdc
- debezium
- outbox
- binlog-wal
aliases:
- cdc debezium outbox binlog
- cdc
- debezium
- outbox
- binlog
- wal connector
- outbox cdc
- replay safe consumer
- event dedup
- change data capture
symptoms:
- DB commit과 broker publish를 따로 처리해 주문은 저장됐지만 이벤트는 발행되지 않는 gap을 만든다
- CDC를 쓰면 중복이나 재처리 문제가 사라진다고 보고 idempotent consumer와 dedup table을 설계하지 않는다
- outbox polling, outbox+CDC, direct publish의 정합성/운영 trade-off를 구분하지 못한다
intents:
- definition
- design
- comparison
prerequisites:
- database/outbox-saga-eventual-consistency
- database/mvcc-replication-sharding
next_docs:
- database/cdc-backpressure-binlog-retention-replay
- database/cdc-gap-repair-reconciliation-playbook
- database/cdc-schema-evolution-compatibility-playbook
- database/cdc-replay-verification-idempotency-runbook
linked_paths:
- contents/database/outbox-saga-eventual-consistency.md
- contents/database/schema-migration-partitioning-cdc-cqrs.md
- contents/database/mvcc-replication-sharding.md
- contents/database/cdc-backpressure-binlog-retention-replay.md
- contents/database/cdc-gap-repair-reconciliation-playbook.md
- contents/database/cdc-schema-evolution-compatibility-playbook.md
- contents/database/cdc-replay-verification-idempotency-runbook.md
- contents/database/incremental-summary-table-refresh-watermark.md
- contents/system-design/change-data-capture-outbox-relay-design.md
- contents/system-design/historical-backfill-replay-platform-design.md
confusable_with:
- database/outbox-saga-eventual-consistency
- database/cdc-backpressure-binlog-retention-replay
- database/cdc-gap-repair-reconciliation-playbook
- system-design/change-data-capture-outbox-relay-design
forbidden_neighbors: []
expected_queries:
- CDC, Debezium, Outbox, Binlog는 DB 변경 이벤트를 안전하게 전달하기 위해 각각 어떤 역할을 해?
- 주문 DB commit과 메시지 publish 사이 gap을 outbox와 CDC로 어떻게 줄이는지 설명해줘
- Outbox polling, Outbox plus CDC, direct publish는 정합성과 운영 복잡도 관점에서 어떻게 달라?
- Debezium은 binlog나 WAL을 읽지만 idempotent consumer와 event dedup이 여전히 필요한 이유가 뭐야?
- CDC를 쓰면 schema evolution, replay, lag, backpressure를 같이 설계해야 하는 이유를 알려줘
contextual_chunk_prefix: |
  이 문서는 CDC, Debezium, Outbox, Binlog bridge로, DB local transaction 안의 outbox event와
  binlog/WAL 기반 Change Data Capture가 business data commit과 event delivery gap을 줄이는 방법,
  duplicate/replay/schema/lag 운영 trade-off를 설명한다.
---
# CDC, Debezium, Outbox, Binlog

> 한 줄 요약: DB 변경을 이벤트로 안전하게 흘려보내려면 outbox와 CDC를 같은 정합성 문제로 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md)
> - [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md)
> - [MVCC, Replication, Sharding](./mvcc-replication-sharding.md)
> - [CDC Backpressure, Binlog/WAL Retention, and Replay Safety](./cdc-backpressure-binlog-retention-replay.md)
> - [CDC Gap Repair, Reconciliation, and Rebuild Boundaries](./cdc-gap-repair-reconciliation-playbook.md)
> - [CDC Schema Evolution, Event Compatibility, and Expand-Contract Playbook](./cdc-schema-evolution-compatibility-playbook.md)
> - [CDC Replay Verification, Idempotency, and Acceptance Runbook](./cdc-replay-verification-idempotency-runbook.md)
> - [Incremental Summary Table Refresh and Watermark Discipline](./incremental-summary-table-refresh-watermark.md)
> - [API 설계와 예외 처리](../software-engineering/api-design-error-handling.md)
> - [Change Data Capture / Outbox Relay 설계](../system-design/change-data-capture-outbox-relay-design.md)
> - [Historical Backfill / Replay Platform 설계](../system-design/historical-backfill-replay-platform-design.md)

retrieval-anchor-keywords: cdc, debezium, outbox, binlog, wal, connector offset, replay safe consumer, cdc backpressure, event dedup, cdc gap repair, projection rebuild, schema evolution, expand contract

## 핵심 개념

CDC(Change Data Capture)는 DB의 변경을 외부 시스템으로 전달하는 방식이다.
Debezium은 binlog/WAL 같은 DB 로그를 읽어 변경 이벤트를 만드는 대표 도구다.

핵심은 **비즈니스 데이터와 이벤트가 서로 어긋나지 않게 만드는 것**이다.

## 깊이 들어가기

### 1. 왜 outbox가 필요한가

가장 흔한 실패는 이것이다.

1. 주문 DB는 커밋됨
2. 메시지 브로커 발행 실패
3. 외부 시스템은 주문을 모름

반대로 메시지만 나가고 DB가 롤백되면 더 큰 문제가 생긴다.

Outbox는 같은 로컬 트랜잭션에 넣어서 이 문제를 줄인다.

```sql
INSERT INTO orders(id, status) VALUES (1001, 'CREATED');
INSERT INTO outbox(id, aggregate_id, event_type, payload, created_at)
VALUES (9001, 1001, 'ORDER_CREATED', '{...}', NOW());
```

### 2. CDC가 하는 일

CDC는 DB 변경 로그를 보고 이벤트를 재구성한다.

- MySQL: binlog
- PostgreSQL: WAL

Debezium은 이 로그를 읽어 Kafka 같은 스트림으로 보낸다.

장점:

- 애플리케이션 코드가 단순해진다
- DB 커밋과 이벤트 발행 사이의 gap이 줄어든다

단점:

- 로그 포맷과 DB 운영을 이해해야 한다
- 스키마 변경과 재처리 전략이 필요하다
- 순서/중복/딜레이를 고려해야 한다

### 3. Outbox와 CDC의 차이

| 방식 | 장점 | 단점 | 적합한 상황 |
|---|---|---|---|
| Outbox polling | 구현이 쉽다 | polling 비용이 든다 | 단순 이벤트 발행 |
| Outbox + CDC | 정합성이 좋다 | 인프라가 복잡하다 | 대규모 이벤트 파이프라인 |
| Direct publish | 가장 단순해 보인다 | 실패에 취약하다 | 장난감 서비스 수준 |

### 4. Debezium 운용 포인트

- snapshot과 streaming을 구분해야 한다
- connector offset을 관리해야 한다
- 재처리 시 idempotent consumer가 필요하다
- schema evolution을 고려해야 한다
- lag seconds뿐 아니라 binlog/WAL retention 압박도 같이 봐야 한다
- heartbeat가 없으면 low-traffic 구간의 정지 여부를 오판하기 쉽다
- 실제 gap이 생기면 replay, backfill, recompute 중 어떤 repair 경계를 택할지 미리 정해 두어야 한다
- old/new consumer가 함께 살아 있는 동안 forward/backward compatibility를 유지하는 rollout 순서를 준비해야 한다

## 실전 시나리오

### 시나리오 1: outbox 중복 발행

consumer가 같은 이벤트를 두 번 받아도 안전해야 한다.

```sql
CREATE TABLE processed_event (
  event_id BIGINT PRIMARY KEY,
  processed_at TIMESTAMP NOT NULL
);
```

처리 전에 event_id를 저장하거나, unique key로 중복을 막는다.

### 시나리오 2: binlog 지연

DB write는 끝났는데 downstream 검색/캐시 반영이 늦을 수 있다.

이때는:

- lag 모니터링
- DLQ
- replay tool

이 필요하다.

### 시나리오 3: schema change

outbox payload를 바꾸면 consumer가 깨질 수 있다.

따라서 versioned payload가 필요하다.

## 코드로 보기

```java
@Transactional
public void createOrder(CreateOrderCommand command) {
    Order order = orderRepository.save(command.toOrder());
    outboxRepository.save(new OutboxEvent(
        order.getId(),
        "ORDER_CREATED",
        jsonSerializer.serialize(order)
    ));
}
```

CDC worker는 outbox 테이블을 읽거나, binlog를 읽어 Kafka로 보낸다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 판단 기준 |
|---|---|---|---|
| 직접 브로커 publish | 단순 | 실패 취약 | 낮은 정합성 요구 |
| outbox polling | 안정적 | 지연/부하 | 중간 규모 |
| CDC + Debezium | 확장성 좋음 | 운영 복잡 | 이벤트 파이프라인 중심 |

## 꼬리질문

> Q: outbox와 CDC를 같이 쓰면 중복이 많아지지 않나요?
> 의도: 중복을 설계로 다루는지 확인
> 핵심: 중복을 없애기보다 idempotent consumer와 deduplication으로 흡수한다.

> Q: binlog만 읽으면 이벤트 소싱과 같은 건가요?
> 의도: 로그 기반 추출과 이벤트 소싱 구분
> 핵심: binlog는 저장 변경 추적이고, 이벤트 소싱은 도메인 상태 자체를 이벤트로 모델링한다.

## 한 줄 정리

CDC는 변경을 전달하는 기술이고, outbox는 그 전달이 DB 커밋과 어긋나지 않게 하는 안전장치다.
