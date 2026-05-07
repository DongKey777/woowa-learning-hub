---
schema_version: 3
title: Outbox Relay and Idempotent Publisher
concept_id: design-pattern/outbox-relay-idempotent-publisher
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- outbox-relay
- idempotent-publisher
- at-least-once-delivery
aliases:
- outbox relay
- idempotent publisher
- at least once publish
- duplicate event delivery
- relay lease
- publish mark sent
- outbox dead letter
- poison message
- outbox 멱등 발행
- 중복 이벤트 발행
symptoms:
- outbox를 쓰면 exactly-once delivery가 자동으로 보장된다고 생각해 at-least-once와 idempotency 설계를 빼먹는다
- 브로커 publish 성공 후 sent mark 전에 crash 나는 경우 같은 중복 발행 시나리오를 고려하지 않는다
- poison message를 무한 재시도해 relay backlog 전체를 막고 projection lag를 키운다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/domain-event-translation-pipeline
- design-pattern/event-envelope-pattern
- database/outbox-saga-eventual-consistency
next_docs:
- design-pattern/idempotent-consumer-projection-dedup-pattern
- design-pattern/projection-lag-budgeting-pattern
- spring/eventlistener-transaction-phase-outbox
linked_paths:
- contents/design-pattern/domain-event-translation-pipeline.md
- contents/design-pattern/domain-events-vs-integration-events.md
- contents/design-pattern/event-envelope-pattern.md
- contents/design-pattern/idempotent-consumer-projection-dedup-pattern.md
- contents/design-pattern/saga-coordinator-pattern-language.md
- contents/design-pattern/read-model-staleness-read-your-writes.md
- contents/database/outbox-saga-eventual-consistency.md
- contents/spring/spring-eventlistener-transaction-phase-outbox.md
- contents/system-design/change-data-capture-outbox-relay-design.md
confusable_with:
- design-pattern/idempotent-consumer-projection-dedup-pattern
- database/outbox-saga-eventual-consistency
- spring/eventlistener-transaction-phase-outbox
- design-pattern/projection-lag-budgeting-pattern
forbidden_neighbors: []
expected_queries:
- Outbox Relay는 DB commit 이후 pending outbox row를 어떻게 claim하고 broker로 publish해?
- outbox를 써도 exactly-once가 아니라 at-least-once와 idempotent publisher가 필요한 이유가 뭐야?
- broker publish 성공 후 markSent 전에 crash 나면 중복 발행을 eventId와 message key로 어떻게 버텨?
- relay lease, attempt count, dead-letter, poison message 처리는 sent flag만으로 왜 부족해?
- 소비자 dedup도 필요하지만 publisher 쪽 stable event id와 retry policy가 중요한 이유는 뭐야?
contextual_chunk_prefix: |
  이 문서는 Outbox Relay and Idempotent Publisher playbook으로, transaction commit과
  message publish 사이의 gap을 outbox relay가 처리하며, at-least-once delivery,
  stable eventId/message key, lease/status, retry, dead-letter 정책으로 중복 발행과
  poison message를 운영적으로 통제하는 방법을 설명한다.
---
# Outbox Relay and Idempotent Publisher

> 한 줄 요약: Outbox relay는 DB commit 이후 메시지를 안전하게 꺼내 보내는 운영 패턴이고, idempotent publisher는 중복 전송과 재시도를 전제로 외부 발행을 안정화한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Domain Event Translation Pipeline](./domain-event-translation-pipeline.md)
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
> - [Event Envelope Pattern](./event-envelope-pattern.md)
> - [Idempotent Consumer and Projection Dedup Pattern](./idempotent-consumer-projection-dedup-pattern.md)
> - [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](./saga-coordinator-pattern-language.md)
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Projection Lag Budgeting Pattern](./projection-lag-budgeting-pattern.md)
> - [Outbox, Saga, Eventual Consistency](../database/outbox-saga-eventual-consistency.md)
> - [Spring EventListener, TransactionalEventListener, and Outbox](../spring/spring-eventlistener-transaction-phase-outbox.md)
> - [Change Data Capture / Outbox Relay 설계](../system-design/change-data-capture-outbox-relay-design.md)

---

## 핵심 개념

Outbox를 도입했다고 해서 문제가 끝나지는 않는다.  
이제 남는 질문은 이거다.

- 누가 outbox를 읽어 발행하나
- relay가 죽었다 살아나면 중복 발행은 어떻게 되나
- 외부 브로커 응답 전에 crash 나면 어떤 상태가 남나

Outbox Relay는 저장된 outbox 레코드를 실제 브로커로 내보내는 실행 계층이다.  
Idempotent Publisher는 그 과정이 **at-least-once**가 되더라도 안전하게 버티도록 만드는 운영 원칙이다.

### Retrieval Anchors

- `outbox relay`
- `idempotent publisher`
- `at least once publish`
- `duplicate event delivery`
- `relay lease`
- `publish mark sent`
- `projection lag`
- `consumer backlog`
- `idempotent consumer`
- `lag degrade policy`

---

## 깊이 들어가기

### 1. relay는 translation과 별개 책임을 가진다

translation pipeline이 계약 shape를 결정한다면, relay는 발행 실행을 담당한다.

- 어떤 레코드를 가져올지
- 누가 지금 처리 중인지
- 성공/실패를 어떻게 기록할지
- poison message를 어떻게 격리할지

즉 translator가 "무엇을 보낼까"라면 relay는 "어떻게 안전하게 보낼까"다.

### 2. outbox relay는 보통 at-least-once를 전제로 해야 한다

다음 상황은 피하기 어렵다.

- 브로커 전송 성공 후 ack 기록 전에 crash
- relay 재시작 후 같은 outbox 재처리
- 네트워크 timeout으로 성공 여부 불명확

그래서 outbox relay의 현실적 기본값은 exactly-once 환상보다 **at-least-once + idempotency**다.

### 3. sent flag 하나만으로는 부족한 경우가 많다

단순한 `sent = true`는 작동할 수도 있지만 운영이 커질수록 부족해진다.

- 여러 relay worker가 경쟁함
- stuck row가 생김
- 재시도 횟수와 마지막 오류가 필요함
- poison message를 분리해야 함

그래서 보통 이런 필드가 붙는다.

- status: pending, processing, sent, failed, dead-letter
- lease owner / lease until
- attempt count
- last error
- published at

### 4. publisher idempotency는 소비자에게만 맡기지 않는 편이 낫다

중복 소비 방지는 결국 소비자 쪽도 필요하다.  
하지만 relay/publisher 쪽에서도 중복을 줄이는 설계가 유용하다.

- stable event id 사용
- broker message key 고정
- relay 재시도 시 같은 envelope 유지
- 발행 결과 기록을 멱등하게 갱신

즉 "소비자가 알아서 dedup하겠지"만으로 끝내지 않는 편이 좋다.

### 5. poison message는 재시도와 격리 정책을 분리해야 한다

계속 실패하는 레코드를 무한 재시도하면 backlog 전체가 막힐 수 있다.

- 일시 장애: backoff 후 재시도
- 스키마 불일치: dead-letter
- 코드 버그: pause + alert

relay는 단순 루프가 아니라 **운영 정책 실행기**에 가깝다.

---

## 실전 시나리오

### 시나리오 1: 브로커 ack 직전 crash

이벤트는 이미 브로커로 갔지만 DB에는 `sent`가 아직 기록되지 않았다.  
relay 재시작 후 같은 메시지를 다시 보낼 수 있으므로 event id 기반 멱등성이 필요하다.

### 시나리오 2: projection consumer 장애

relay는 정상 발행했지만 consumer가 backlog를 쌓아 read model lag가 커질 수 있다.  
따라서 relay 성공과 사용자 가시성은 다른 운영 신호다.

### 시나리오 3: 스키마 깨진 메시지

특정 이벤트만 계속 역직렬화 오류를 일으키면, 무한 재시도 대신 dead-letter 격리와 알람이 더 안전하다.

---

## 코드로 보기

### outbox row 감각

```java
public record OutboxMessage(
    String eventId,
    String eventType,
    String payload,
    OutboxStatus status,
    int attemptCount,
    Instant leaseUntil
) {}
```

### relay loop 감각

```java
public class OutboxRelay {
    public void publishPendingBatch() {
        List<OutboxMessage> batch = outboxRepository.claimPendingBatch(workerId, now());
        for (OutboxMessage message : batch) {
            try {
                broker.publish(message.eventId(), message.payload());
                outboxRepository.markSent(message.eventId(), now());
            } catch (TransientPublishException ex) {
                outboxRepository.releaseForRetry(message.eventId(), ex.getMessage());
            } catch (FatalPublishException ex) {
                outboxRepository.moveToDeadLetter(message.eventId(), ex.getMessage());
            }
        }
    }
}
```

### idempotent publish 키

```java
// 동일 outbox row는 재시도되어도 같은 eventId와 message key를 사용한다.
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단순 sent flag relay | 구현이 빠르다 | 중복/경합/poison 대응이 약하다 | 소규모 단일 워커 |
| lease + status 기반 relay | 운영 안정성이 높다 | 상태 관리가 늘어난다 | worker 여러 개, 재시도/장애 대응이 필요할 때 |
| exactly-once 환상 추구 | 개념적으로 매력적이다 | 비용이 크고 시스템 제약이 많다 | 매우 특수한 플랫폼 제어 하에서만 검토 |

판단 기준은 다음과 같다.

- relay는 at-least-once를 기본값으로 본다
- event id와 message key는 안정적으로 유지한다
- poison message와 transient failure를 분리 처리한다

---

## 꼬리질문

> Q: outbox를 쓰면 exactly-once가 되나요?
> 의도: outbox와 전달 보장 수준을 혼동하지 않는지 본다.
> 핵심: 아니다. 보통은 at-least-once이며, 멱등성이 같이 필요하다.

> Q: 소비자가 dedup하면 publisher는 단순해도 되지 않나요?
> 의도: 책임을 한쪽으로만 미루지 않는지 본다.
> 핵심: 소비자 dedup도 필요하지만, relay 쪽 안정적 event id와 재시도 정책이 있어야 운영이 덜 아프다.

> Q: poison message는 계속 재시도하면 언젠가 되지 않나요?
> 의도: 일시 장애와 영구 오류를 구분하는지 본다.
> 핵심: 아니다. 영구 오류는 dead-letter와 알람으로 격리해야 backlog를 보호할 수 있다.

## 한 줄 정리

Outbox relay는 commit 이후 메시지 발행을 운영적으로 책임지고, idempotent publisher는 중복 전송과 재시도를 전제로 안전한 외부 전달을 만들게 해준다.
