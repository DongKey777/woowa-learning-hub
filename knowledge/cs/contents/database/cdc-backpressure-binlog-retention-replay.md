---
schema_version: 3
title: CDC Backpressure, Binlog/WAL Retention, and Replay Safety
concept_id: database/cdc-backpressure-binlog-retention-replay
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- cdc-backpressure
- binlog-retention
- wal-retention
- replay-safety
aliases:
- cdc backpressure
- binlog retention
- wal retention
- replication slot lag
- debezium lag
- replay window
- log retention pressure
- cdc recovery
- gap repair
- CDC lag retention
symptoms:
- CDC consumer가 느려져 downstream 반영만 늦는다고 봤지만 source DB binlog/WAL retention pressure가 커진다
- replication slot lag나 binlog purge window 때문에 replay 가능한 시간이 줄어들고 snapshot fallback 위험이 커진다
- connector lag만 보고 sink idempotency, heartbeat, replay-safe consumer, estimated time-to-log-loss를 같이 보지 않는다
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- database/cdc-debezium-outbox-binlog
- database/idempotent-transaction-retry-envelopes
next_docs:
- database/cdc-gap-repair-reconciliation-playbook
- database/cdc-replay-verification-idempotency-runbook
- system-design/historical-backfill-replay-platform-design
linked_paths:
- contents/database/cdc-debezium-outbox-binlog.md
- contents/database/cdc-gap-repair-reconciliation-playbook.md
- contents/database/replica-lag-observability-routing-slo.md
- contents/database/group-commit-binlog-fsync-durability.md
- contents/database/online-backfill-consistency.md
- contents/database/idempotent-transaction-retry-envelopes.md
- contents/system-design/historical-backfill-replay-platform-design.md
confusable_with:
- database/cdc-gap-repair-reconciliation-playbook
- database/cdc-replay-verification-idempotency-runbook
- database/replica-lag-observability-routing-slo
- system-design/change-data-capture-outbox-relay-design
forbidden_neighbors: []
expected_queries:
- CDC lag가 커지면 downstream 지연뿐 아니라 binlog WAL retention pressure와 replay window 축소가 생기는 이유가 뭐야?
- Debezium consumer가 늦을 때 estimated time-to-log-loss와 log retention window를 어떻게 봐야 해?
- PostgreSQL replication slot lag가 WAL 삭제를 막아 source DB storage pressure로 번지는 현상을 설명해줘
- CDC backpressure 상황에서 heartbeat, connector offset, sink idempotency를 같이 봐야 하는 이유가 뭐야?
- binlog retention을 놓치면 snapshot fallback이나 rebuild가 필요한 이유와 replay-safe consumer 조건을 알려줘
contextual_chunk_prefix: |
  이 문서는 CDC Backpressure, Binlog/WAL Retention, and Replay Safety playbook으로,
  Debezium/binlog/WAL consumer lag가 downstream staleness를 넘어 source log retention, replay window,
  replication slot storage pressure, snapshot fallback risk로 번지는 운영 대응 기준을 설명한다.
---
# CDC Backpressure, Binlog/WAL Retention, and Replay Safety

> 한 줄 요약: CDC 소비가 느려지면 문제는 단순 지연이 아니라, binlog/WAL 보존 기간과 replay 가능 시간이 같이 줄어드는 운영 사고로 번진다.

**난이도: 🔴 Advanced**

관련 문서:

- [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md)
- [CDC Gap Repair, Reconciliation, and Rebuild Boundaries](./cdc-gap-repair-reconciliation-playbook.md)
- [Replica Lag Observability와 Routing SLO](./replica-lag-observability-routing-slo.md)
- [Group Commit, Binlog, fsync, Durability](./group-commit-binlog-fsync-durability.md)
- [Online Backfill Consistency와 워터마크 전략](./online-backfill-consistency.md)
- [Idempotent Transaction Retry Envelope](./idempotent-transaction-retry-envelopes.md)
- [Historical Backfill / Replay Platform 설계](../system-design/historical-backfill-replay-platform-design.md)

retrieval-anchor-keywords: cdc backpressure, binlog retention, wal retention, replication slot lag, debezium lag, replay window, log retention pressure, cdc recovery, gap repair, projection reconciliation

## 핵심 개념

CDC 파이프라인을 운영할 때 가장 흔한 오해는 "consumer가 느리면 downstream 반영만 늦어진다"는 생각이다.

실제로는 더 큰 문제가 따라온다.

- DB 로그 보존량이 늘어난다
- 디스크 압박이 커진다
- retention window를 넘기면 재시작 시 snapshot 재구축이 필요해진다
- 복구 가능한 시간 범위(replay window)가 줄어든다

즉 CDC backpressure는 단순한 지연이 아니라, **원본 DB의 로그 lifecycle을 잠식하는 문제**다.

## 깊이 들어가기

### 1. CDC는 로그를 읽는 시스템이므로 "얼마나 늦었는가"보다 "얼마나 남겨둬야 하는가"가 중요하다

Debezium, logical replication, binlog reader 모두 결국 DB 변경 로그를 순서대로 소비한다.

이때 consumer가 느려지면:

- MySQL은 binlog purge를 늦출 수 있다
- PostgreSQL은 replication slot이 오래된 WAL 제거를 막을 수 있다
- downstream은 stale하지만, upstream은 storage pressure를 받는다

그래서 CDC lag metric은 메시지 지연이 아니라 **log retention 압력**과 같이 봐야 한다.

### 2. retention window를 숫자로 관리해야 한다

중요한 질문:

- 지금 consumer가 마지막으로 처리한 offset은 어디인가
- 현재 로그 생성 속도로 몇 시간 뒤면 retention을 넘는가
- snapshot 없이 재시작 가능한 replay window가 얼마나 남았는가

이 답이 없으면 "조금 느리다"와 "곧 복구 불가능해진다"를 구분할 수 없다.

운영에서는 보통 다음을 같이 본다.

- current source position
- connector committed offset
- lag bytes / lag seconds
- retained log bytes
- estimated hours to log loss

### 3. heartbeat와 low-traffic partition이 중요하다

CDC 지연은 write가 많을 때만 보이는 문제가 아니다.  
오히려 low traffic 테이블이나 파티션은 offset 진전이 드물어서 상태 판단이 어려울 수 있다.

이때 heartbeat record가 유용하다.

- connector가 여전히 살아 있는지 확인
- 실제 지연과 "조용해서 안 움직이는 것"을 구분
- recovery checkpoint를 더 자주 남김

heartbeat가 없으면 "정말 멈췄는지, 그냥 변경이 없는지" 판단하기 어렵다.

### 4. snapshot fallback은 쉽지 않다

log retention을 놓쳐 replay가 끊기면 "그냥 다시 snapshot 뜨면 되지"라고 생각하기 쉽다.  
하지만 운영에서는 snapshot이 더 큰 작업일 수 있다.

- 원본 DB에 큰 read 부하
- 대형 테이블 초기 적재 시간 증가
- snapshot 이후 catch-up 정합성 설계 필요
- downstream dedup/reconciliation 비용 증가

즉 snapshot fallback은 복구 수단이지만, 공짜 안전망은 아니다.

### 5. backpressure 완화는 connector만이 아니라 downstream 병목을 같이 봐야 한다

CDC lag가 커지는 이유는 다양하다.

- connector fetch/commit 설정 문제
- Kafka/브로커 지연
- sink database backpressure
- schema registry 또는 serialization 병목
- 소비자 측 idempotency table 경합

원인은 downstream인데 증상은 source log retention 압박으로 나타날 수 있다.  
그래서 source position만 보는 모니터링은 반쪽짜리다.

### 6. replay-safe consumer가 있어야 공격적으로 복구할 수 있다

connector 재시작, offset rewind, 부분 재처리를 하려면 sink 쪽이 replay-safe 해야 한다.

필요한 장치:

- event id dedup
- upsert 또는 merge semantics
- checkpoint와 watermark 관리
- dead letter와 replay tool

consumer가 replay-safe 하지 않으면, retention 압박 상황에서 "빨리 따라잡기" 자체가 더 위험해진다.

## 실전 시나리오

### 시나리오 1. Debezium lag가 2시간으로 증가

검색 인덱스 반영이 늦어지는 것만 문제가 아니다.  
binlog 생성량이 높은 시간대라면 몇 시간 안에 purge window를 따라잡지 못할 수 있다.

필요 대응:

- estimated time-to-log-loss 계산
- 불필요한 sink 부하 제거
- 중요하지 않은 connector 일시 중지
- replay-safe 범위 안에서 offset catch-up 가속

### 시나리오 2. PostgreSQL replication slot이 WAL 삭제를 막음

logical slot consumer가 오래 멈추면 WAL이 쌓여 디스크 압박이 커진다.

핵심 판단:

- slot을 살리기 위해 storage를 늘릴지
- slot을 버리고 snapshot 재구축할지
- 어떤 downstream을 우선 복구할지

### 시나리오 3. 장애 후 offset rewind 재처리

consumer 버그 수정 뒤 최근 30분 데이터를 다시 흘리고 싶다.

이때 sink가 event id dedup을 갖고 있으면 replay가 가능하지만, 그렇지 않으면 중복 side effect가 생긴다.

## 코드로 보기

```sql
CREATE TABLE cdc_consumer_checkpoint (
  consumer_name VARCHAR(100) PRIMARY KEY,
  source_position VARCHAR(255) NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

```sql
CREATE TABLE processed_cdc_event (
  event_id VARCHAR(100) PRIMARY KEY,
  processed_at TIMESTAMP NOT NULL
);
```

```java
if (processedEventRepository.exists(eventId)) {
    return;
}

applyChange(event);
processedEventRepository.insert(eventId, now());
checkpointRepository.update(consumerName, sourcePosition, now());
```

이 구조의 핵심은 "offset만 저장"이 아니라, **재처리 가능성을 dedup과 함께 확보**하는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 짧은 retention + 빠른 복구 기대 | 저장 비용이 적다 | 장애 시 snapshot 가능성이 커진다 | 작은 데이터, 낮은 중요도 |
| 넉넉한 retention | 복구 여유가 크다 | 로그 저장 비용이 든다 | 중요한 CDC 파이프라인 |
| heartbeat + lag 예측 | 상태 판단이 쉬워진다 | 운영 metric 설계가 필요하다 | 장기 운영 파이프라인 |
| replay-safe sink | 공격적 복구가 가능하다 | dedup/storage 비용이 든다 | 검색, 분석, read model 반영 |

## 꼬리질문

> Q: CDC lag가 왜 source DB 문제로 번지나요?
> 의도: 로그 기반 추출의 비용 전가를 이해하는지 확인
> 핵심: binlog/WAL 보존이 길어져 storage 압박과 replay window 축소가 생기기 때문이다

> Q: retention window를 넘기면 무엇이 문제인가요?
> 의도: 단순 지연과 복구 불능의 차이를 아는지 확인
> 핵심: 필요한 로그가 사라져 snapshot 재구축 없이는 따라잡을 수 없게 된다

> Q: heartbeat가 왜 필요한가요?
> 의도: low traffic 구간의 관측 문제를 아는지 확인
> 핵심: 변경이 없어서 조용한 것과 실제 멈춘 것을 구분하고 checkpoint를 전진시키기 위해 필요하다

## 한 줄 정리

CDC 운영의 핵심은 이벤트를 얼마나 빨리 보내느냐보다, backpressure가 생겨도 binlog/WAL retention과 replay window를 잃지 않도록 관측·복구·dedup 경로를 갖추는 것이다.
