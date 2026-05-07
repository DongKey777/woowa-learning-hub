---
schema_version: 3
title: Mediator vs Observer vs Pub/Sub
concept_id: design-pattern/mediator-vs-observer-vs-pubsub
canonical: true
category: design-pattern
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 86
mission_ids: []
review_feedback_tags:
- mediator-observer-pubsub
- event-boundary-choice
- collaboration-routing
aliases:
- mediator vs observer vs pubsub
- mediator vs observer
- observer vs pubsub
- event bus vs mediator
- component communication pattern
- same process fan out
- broker pubsub boundary
- central coordinator object
- ui mediator pattern
- collaboration routing
symptoms:
- 객체들이 서로 너무 많이 직접 호출하자 모든 통신을 event로 바꾸려 하지만 실제로는 중앙 조율 객체가 필요한 상황이다
- 같은 프로세스 listener fan-out과 broker 기반 pubsub를 모두 이벤트라고 부르며 실패 경계와 재시도 의미를 섞는다
- Mediator를 쓰면서도 participant끼리 몰래 직접 호출해 조율 책임이 분산되고 순서 정책이 흐려진다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- design-pattern/observer
- design-pattern/observer-vs-pubsub-quick-bridge
- design-pattern/pattern-selection
next_docs:
- design-pattern/observer-pubsub-application-events
- design-pattern/observer-lifecycle-hygiene
- design-pattern/domain-events-vs-integration-events
linked_paths:
- contents/design-pattern/observer.md
- contents/design-pattern/observer-vs-pubsub-quick-bridge.md
- contents/design-pattern/observer-pubsub-application-events.md
- contents/design-pattern/observer-lifecycle-hygiene.md
- contents/design-pattern/pattern-selection.md
- contents/design-pattern/domain-events-vs-integration-events.md
- contents/design-pattern/outbox-relay-idempotent-publisher.md
- contents/software-engineering/oop-design-basics.md
confusable_with:
- design-pattern/observer
- design-pattern/observer-pubsub-application-events
- design-pattern/domain-events-vs-integration-events
- design-pattern/facade-vs-adapter-vs-proxy
forbidden_neighbors: []
expected_queries:
- Mediator, Observer, Pub/Sub는 객체 간 통신을 줄인다는 점은 비슷한데 무엇이 달라?
- component들이 서로 직접 호출해 순서 정책이 엉키면 mediator가 observer보다 나은 이유가 뭐야?
- 같은 프로세스 fan out이면 observer이고 broker topic을 거치면 pubsub로 보는 기준을 설명해줘
- Mediator를 쓰는데 participant들이 서로 직접 호출하면 조율 책임이 왜 깨져?
- 이벤트로 분리하기 전에 중앙 조율 객체가 필요한지 listener fan out이 필요한지 어떻게 판단해?
contextual_chunk_prefix: |
  이 문서는 Mediator vs Observer vs Pub/Sub chooser로, 여러 participant의 상호작용을
  중앙 조율 객체로 모으는 Mediator, 같은 프로세스 안에서 상태 변화 반응을 fan-out하는
  Observer, broker나 bus를 통해 발행과 소비를 분리하는 Pub/Sub의 선택 기준을 설명한다.
---
# Mediator vs Observer vs Pub/Sub

> 한 줄 요약: Mediator는 참여자 사이의 상호작용을 중앙 조율 객체로 모으고, Observer는 상태 변화를 같은 프로세스 안 리스너에게 알리며, Pub/Sub는 발행과 소비를 bus나 broker로 분리한다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Observer(옵저버) 디자인 패턴](./observer.md)
> - [옵저버 vs Pub-Sub: 처음 읽을 때 바로 잡는 짧은 다리](./observer-vs-pubsub-quick-bridge.md)
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [Observer Lifecycle Hygiene](./observer-lifecycle-hygiene.md)
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)

---

## 핵심 개념

세 패턴은 모두 직접 결합을 줄이는 데 쓰이지만, 줄이는 결합의 종류가 다르다.

- Mediator: 여러 객체가 서로를 직접 호출하지 않고 중앙 조율 객체를 통해 협력한다.
- Observer: 한 subject의 상태 변화에 여러 listener가 반응한다.
- Pub/Sub: publisher와 subscriber가 topic, bus, broker를 사이에 두고 분리된다.

짧게 말하면, **Mediator는 대화 흐름 조율**, **Observer는 상태 변화 fan-out**, **Pub/Sub는 전달 경계 분리**에 더 가깝다.

### Retrieval Anchors

- `mediator vs observer vs pubsub`
- `event bus vs mediator`
- `component communication pattern`
- `same process fan out`
- `broker pubsub boundary`
- `central coordinator object`
- `observer vs pubsub`

---

## 한눈에 구분

| 질문 | Mediator | Observer | Pub/Sub |
|---|---|---|---|
| 중심 문제 | 참여자 사이 상호작용 조율 | 상태 변화 후속 반응 추가 | 발행자와 소비자 실행 경계 분리 |
| 누가 흐름을 안다 | mediator | subject와 listener 계약 | broker/topic 계약 |
| 실행 감각 | 보통 같은 프로세스의 명시적 조율 | 보통 같은 프로세스 fan-out | 비동기/분산 전달이 흔함 |
| 순서 정책 | mediator에 명시하기 쉽다 | 등록 순서나 framework 규칙에 흐르기 쉽다 | broker, partition, consumer 정책에 따름 |
| 대표 예시 | UI dialog coordinator, checkout flow coordinator | button listener, domain listener, Spring ApplicationEvent | Kafka topic, RabbitMQ exchange, durable event bus |

빠른 기준은 이렇다.

- 여러 participant가 서로 호출해 mesh가 생기면 Mediator를 본다.
- 하나의 상태 변화 뒤에 반응을 붙이는 문제면 Observer를 본다.
- 발행과 소비를 시간/프로세스/운영 경계로 분리해야 하면 Pub/Sub를 본다.

---

## 깊이 들어가기

### 1. Mediator는 "누가 누구를 부를지"를 중앙에서 정한다

Mediator는 참여자들이 서로를 직접 알지 않게 만든다.

예를 들어 검색 화면에서 filter, sort, pagination, result view가 서로 직접 호출하면 조합이 빠르게 복잡해진다. 이때 `SearchPageMediator`가 변경 신호를 받아 어떤 component를 갱신할지 정하면 관계가 단순해진다.

```java
public class CheckoutMediator {
    public void couponChanged(Coupon coupon) {
        pricePanel.recalculate(coupon);
        paymentPanel.refreshAvailableMethods();
        summaryPanel.update();
    }
}
```

핵심은 "변경 사실을 모두에게 뿌린다"가 아니라 "이 변경에 대해 어떤 협력을 어떤 순서로 수행할지 mediator가 안다"는 점이다.

### 2. Observer는 subject의 변화에 관심 있는 listener를 붙인다

Observer는 subject가 구체 listener를 몰라도 후속 반응을 붙일 수 있게 한다.

```java
public interface OrderListener {
    void orderCompleted(OrderCompleted event);
}
```

알림, 메트릭, 감사 로그처럼 같은 상태 변화에 여러 부가 반응이 붙는다면 observer가 자연스럽다.
다만 같은 프로세스 observer는 기본적으로 직접 메서드 호출 fan-out에 가까우므로, listener 예외와 순서 의미를 의식해야 한다.

### 3. Pub/Sub는 전달 경계를 바꾼다

Pub/Sub는 publisher가 subscriber를 모르는 정도를 넘어, 전달 책임을 topic, bus, broker에 맡긴다.

- 발행 성공과 소비 성공이 분리될 수 있다.
- consumer lag, retry, ack, dedup, dead letter 같은 운영 단어가 생긴다.
- 메시지 계약과 versioning이 중요해진다.

즉 Pub/Sub는 "Observer의 더 느슨한 버전"이라기보다, 운영 경계가 달라지는 선택이다.

---

## 흔한 오판

### 1. Mediator가 필요한데 Observer로만 풀면 순서 정책이 숨는다

participant 사이 조율 순서가 요구사항이라면, observer listener 등록 순서에 기대기보다 mediator에 명시하는 편이 안전하다.

### 2. Observer가 필요한데 Mediator가 모든 반응을 떠안으면 커진다

단순 감사 로그, 메트릭, 알림까지 mediator가 전부 알면 mediator가 god object로 커질 수 있다. 주 흐름과 독립적인 후속 반응은 observer가 더 낫다.

### 3. Pub/Sub가 필요한데 같은 프로세스 event로 끝내면 실패 경계가 부족하다

consumer 재시도, 중복 처리, 발행 후 소비 지연이 요구사항이면 같은 프로세스 observer로는 부족하다. outbox, broker, idempotent consumer까지 같이 봐야 한다.

---

## 꼬리질문

> Q: Mediator와 Observer는 둘 다 참여자를 직접 모르게 하니까 같은 건가요?
> 의도: 중앙 조율과 상태 변화 fan-out을 구분하는지 본다.
> 핵심: 아니다. Mediator는 협력 흐름을 알고 조율하고, Observer는 subject 변화에 대한 반응을 분리한다.

> Q: Event bus를 쓰면 무조건 Pub/Sub인가요?
> 의도: 이름보다 실행 경계를 보는지 확인한다.
> 핵심: 같은 프로세스 동기 dispatch라면 observer나 mediator infrastructure에 가까울 수 있다.

> Q: 순서가 중요한 흐름도 observer로 처리해도 되나요?
> 의도: 등록 순서와 명시적 orchestration의 차이를 보는 질문이다.
> 핵심: 순서가 비즈니스 규칙이면 mediator나 직접 호출처럼 순서가 드러나는 구조가 더 안전하다.

## 한 줄 정리

Mediator는 상호작용 조율, Observer는 상태 변화 fan-out, Pub/Sub는 전달 경계 분리다. 이름보다 실행 시점, 실패 경계, 순서 정책을 먼저 보면 선택이 덜 흔들린다.
