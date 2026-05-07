---
schema_version: 3
title: Idempotent Consumer and Projection Dedup Pattern
concept_id: design-pattern/idempotent-consumer-projection-dedup-pattern
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- idempotent-consumer
- projection-dedup
- at-least-once-consumer
aliases:
- idempotent consumer
- projection dedup
- consumer dedup store
- at least once consumer
- replay safe projector
- duplicate event handling
- processed event ledger
- event id dedup
- projector idempotency
- 중복 이벤트 처리
symptoms:
- producer outbox를 만들었으니 consumer는 중복 이벤트를 보지 않을 거라고 가정한다
- projection rebuild나 broker redelivery 때 같은 이벤트가 두 번 적용되어 포인트, 수량, read model 값이 중복 증가한다
- broker message id, envelope event id, aggregate version, business action id 중 어떤 dedup key가 안정적인지 정하지 않는다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/outbox-relay-idempotent-publisher
- design-pattern/event-envelope-pattern
- design-pattern/projection-rebuild-backfill-cutover-pattern
next_docs:
- design-pattern/projection-rebuild-poison-event-replay-failure-handling
- design-pattern/projection-lag-budgeting-pattern
- design-pattern/tolerant-reader-event-contract-pattern
linked_paths:
- contents/design-pattern/outbox-relay-idempotent-publisher.md
- contents/design-pattern/read-model-staleness-read-your-writes.md
- contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md
- contents/design-pattern/event-envelope-pattern.md
- contents/design-pattern/tolerant-reader-event-contract-pattern.md
- contents/design-pattern/projection-rebuild-poison-event-replay-failure-handling.md
- contents/design-pattern/projection-lag-budgeting-pattern.md
- contents/design-pattern/event-sourcing-pattern-language.md
confusable_with:
- design-pattern/outbox-relay-idempotent-publisher
- design-pattern/event-envelope-pattern
- design-pattern/projection-rebuild-backfill-cutover-pattern
- design-pattern/projection-lag-budgeting-pattern
forbidden_neighbors: []
expected_queries:
- Idempotent Consumer는 at least once delivery에서 같은 이벤트를 여러 번 받아도 안전하게 처리하는 패턴이야?
- Producer가 outbox와 idempotent publisher를 써도 consumer dedup과 projector idempotency가 필요한 이유가 뭐야?
- projection rebuild나 replay 중 이미 처리한 이벤트를 다시 볼 때 upsert, sequence check, processed event ledger를 어떻게 써?
- broker message id와 envelope event id, aggregate version, business action id는 dedup key로 어떤 차이가 있어?
- 이메일, 포인트, webhook 같은 side effect consumer는 projection보다 dedup ledger를 더 강하게 봐야 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Idempotent Consumer and Projection Dedup Pattern playbook으로, at-least-once
  delivery, relay retry, offset rollback, replay/backfill 환경에서 consumer와 projector가
  duplicate event를 안전하게 처리하도록 processed event ledger, stable dedup key, upsert,
  sequence check, replay-safe projector를 설계하는 방법을 설명한다.
---
# Idempotent Consumer and Projection Dedup Pattern

> 한 줄 요약: at-least-once delivery 환경에서는 consumer와 projector가 같은 이벤트를 여러 번 받아도 같은 결과를 내도록 설계해야 하며, dedup store와 projector idempotency는 별개이면서 함께 필요할 수 있다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Event Envelope Pattern](./event-envelope-pattern.md)
> - [Tolerant Reader for Event Contracts](./tolerant-reader-event-contract-pattern.md)

---

## 핵심 개념

Producer가 outbox와 relay를 잘 만들더라도, consumer 쪽 문제가 남는다.

- 같은 이벤트가 두 번 올 수 있다
- replay/backfill 중 이미 처리한 이벤트를 다시 볼 수 있다
- consumer가 처리 직후 crash 나서 offset만 뒤로 갈 수 있다

이때 consumer가 중복 입력에 안전하지 않으면 다음 문제가 생긴다.

- 포인트 두 번 적립
- projection 수량 두 번 증가
- 알림 중복 발송

Idempotent consumer 패턴은 같은 메시지를 여러 번 처리해도 결과가 같도록 만든다.  
Projection dedup은 그중에서도 read model projector가 중복 이벤트를 안전하게 흡수하도록 하는 운영 패턴이다.

중요한 점은 중복 전달이 예외가 아니라 정상 운영 조건이라는 것이다. relay retry, consumer crash, offset rollback, rebuild replay가 모두 같은 이벤트를 다시 보게 만들 수 있다.

### Retrieval Anchors

- `idempotent consumer`
- `projection dedup`
- `consumer dedup store`
- `at least once consumer`
- `replay safe projector`
- `duplicate event handling`

---

## 깊이 들어가기

### 1. 멱등성과 dedup은 같은 말이 아니다

둘은 비슷하지만 다르다.

- 멱등성: 같은 입력을 여러 번 처리해도 결과가 같다
- dedup: 같은 입력을 여러 번 처리하지 않도록 식별/차단한다

가장 안전한 시스템은 두 가지를 함께 가진다.

- consumer logic 자체가 가급적 멱등적
- 추가로 processed event id나 sequence로 dedup

### 2. projector는 replay-safe해야 한다

read model은 언젠가 rebuild/replay/backfill을 겪는다.  
그래서 projector는 평상시 중복뿐 아니라 **역사 재생**에도 안전해야 한다.

- append가 아니라 upsert
- 누적 합이면 version/sequence check
- 이미 본 event id면 skip

즉 projector는 online consumer이면서 offline rebuild 도구이기도 하다.

### 3. dedup key는 business identity와 transport identity를 구분해야 한다

좋은 dedup key를 정하지 않으면 모호해진다.

- broker message id
- envelope event id
- aggregate id + version
- business action id

무엇이 안정적이고 재전송 시 유지되는지 먼저 확인해야 한다.

### 4. side effect consumer는 projector보다 더 조심해야 한다

projection은 덮어쓰기나 upsert로 흡수하기 쉬운 편이다.  
반면 side effect consumer는 중복 비용이 더 크다.

- 이메일 발송
- SMS 발송
- 외부 webhook 호출
- 정산 요청

이 경우 processed message ledger나 outbox-like effect log가 따로 필요할 수 있다.

### 5. 정확성보다 처리량을 우선하다 보면 중복 창이 생긴다

batch ack, async commit, parallel consumer를 쓰면 처리량은 좋아질 수 있다.  
대신 crash window와 중복 가능성이 커진다.

그래서 idempotent consumer는 성능 최적화의 부작용을 흡수하는 안전장치이기도 하다.

---

## 실전 시나리오

### 시나리오 1: 주문 projection

`OrderPlaced`가 두 번 와도 read model row는 한 번만 생성되거나 같은 값으로 upsert되어야 한다.

### 시나리오 2: 포인트 적립 consumer

결제 완료 이벤트 중복 시 포인트가 두 번 적립되면 안 된다.  
business action id나 event id 기준 processed ledger가 필요할 수 있다.

### 시나리오 3: projection rebuild

예전 이벤트를 다시 읽을 때 중복이나 순서 뒤틀림이 있어도 projector가 안전하게 재계산될 수 있어야 한다.

---

## 코드로 보기

### processed event ledger

```java
public interface ProcessedEventStore {
    boolean alreadyProcessed(String consumerName, String eventId);
    void markProcessed(String consumerName, String eventId);
}
```

### idempotent projector

```java
public class OrderProjector {
    public void on(EventEnvelope<OrderSubmittedV1> event) {
        if (processedEventStore.alreadyProcessed("order-projector", event.eventId())) {
            return;
        }

        orderReadRepository.upsert(event.payload().orderId(), event.payload());
        processedEventStore.markProcessed("order-projector", event.eventId());
    }
}
```

### sequence-aware update

```java
public void apply(OrderStateChanged event) {
    OrderReadRow row = repository.findById(event.orderId()).orElse(new OrderReadRow());
    if (row.version() >= event.aggregateVersion()) {
        return;
    }
    repository.save(row.apply(event));
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 멱등성 없이 단순 처리 | 구현이 빠르다 | 중복 전달에 취약하다 | 운영 중요도가 낮은 실험 |
| logic idempotency만 사용 | 구조가 단순하다 | side effect 중복은 막기 어렵다 | upsert 중심 read model |
| dedup store + idempotent logic | 가장 안전하다 | 저장/조회 비용이 늘어난다 | 중요한 projection, 포인트, 외부 호출 |

판단 기준은 다음과 같다.

- replay/backfill이 있으면 projector 멱등성은 거의 필수다
- side effect consumer는 dedup ledger를 더 강하게 본다
- dedup key가 재전송 시 안정적인지 먼저 확인한다

---

## 꼬리질문

> Q: producer가 멱등하면 consumer도 멱등할 필요 없지 않나요?
> 의도: 전달 보장과 처리 보장을 구분하는지 본다.
> 핵심: 아니다. relay 재시도, offset rollback, replay는 consumer 쪽에서도 중복을 만든다.

> Q: dedup store만 있으면 projector logic은 멱등하지 않아도 되나요?
> 의도: dedup 실패 창을 생각하는지 본다.
> 핵심: 가능한 한 logic도 멱등적인 편이 안전하다. 두 층이 같이 있어야 한다.

> Q: aggregate version으로 dedup하면 충분한가요?
> 의도: transport id와 business/version id의 차이를 보는 질문이다.
> 핵심: 경우에 따라 충분할 수 있지만, event 종류와 재전송 semantics를 같이 봐야 한다.

## 한 줄 정리

Idempotent consumer와 projection dedup은 at-least-once 시스템에서 중복 전달을 정상 상태로 받아들이고, consumer와 projector가 같은 이벤트를 여러 번 봐도 안전하게 버티게 해주는 패턴이다.
