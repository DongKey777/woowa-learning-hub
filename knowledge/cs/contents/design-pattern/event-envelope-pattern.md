# Event Envelope Pattern: 이벤트 본문과 메타데이터를 분리하기

> 한 줄 요약: Event Envelope는 이벤트 payload를 둘러싸는 메타데이터 계층을 두어 추적, 버전 관리, 라우팅을 쉽게 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Event Sourcing: 변경 이력을 진실의 원천으로 쓰는 패턴 언어](./event-sourcing-pattern-language.md)
> - [Domain Event Translation Pipeline](./domain-event-translation-pipeline.md)
> - [Event Upcaster Compatibility Patterns](./event-upcaster-compatibility-patterns.md)
> - [Tolerant Reader for Event Contracts](./tolerant-reader-event-contract-pattern.md)
> - [Idempotent Consumer and Projection Dedup Pattern](./idempotent-consumer-projection-dedup-pattern.md)
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [Saga / Coordinator](./saga-coordinator-pattern-language.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)

---

## 핵심 개념

이벤트를 다룰 때 payload만 저장하면 운영 정보가 빠진다.  
Envelope는 이벤트의 **본문(payload)** 과 **메타데이터(metadata)** 를 분리한다.

- payload: 도메인 사실
- metadata: id, type, occurredAt, correlationId, causationId, version

### Retrieval Anchors

- `event envelope`
- `event metadata`
- `correlation id`
- `causation id`
- `schema version`
- `event contract evolution`
- `published language versioning`
- `event dedup key`
- `legacy replay compatibility`
- `forward compatible consumer`

---

## 깊이 들어가기

### 1. payload만으로는 부족하다

이벤트 소비자가 알아야 하는 건 도메인 데이터만이 아니다.

- 어디서 왔는가
- 어떤 요청과 연결되는가
- 몇 번째 버전인가
- 재처리 대상인가

### 2. 추적성과 재처리에 중요하다

Envelope는 로그, 트레이싱, 재시도, 중복 제거에 도움이 된다.

### 3. event sourcing과 잘 맞는다

이벤트가 곧 진실의 원천이라면, Envelope는 그 이벤트를 안전하게 운반하는 포장지다.

---

## 실전 시나리오

### 시나리오 1: 주문 완료 이벤트

주문 상태와 함께 correlation id를 담아 후속 서비스가 추적할 수 있게 한다.

### 시나리오 2: 재처리

같은 payload라도 envelope metadata로 중복 제거할 수 있다.

### 시나리오 3: 버전 관리

구독자가 version에 따라 다른 파싱 로직을 선택할 수 있다.

---

## 코드로 보기

### Envelope

```java
public record EventEnvelope<T>(
    String eventId,
    String eventType,
    Instant occurredAt,
    String correlationId,
    String causationId,
    int schemaVersion,
    T payload
) {}
```

### Payload

```java
public record OrderCompleted(Long orderId, Long userId) {}
```

### Usage

```java
EventEnvelope<OrderCompleted> envelope = new EventEnvelope<>(
    UUID.randomUUID().toString(),
    "OrderCompleted",
    Instant.now(),
    correlationId,
    causationId,
    1,
    new OrderCompleted(orderId, userId)
);
```

Envelope는 이벤트를 운영 가능한 형태로 만든다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| payload only | 단순하다 | 추적 정보가 부족하다 | 작은 내부 이벤트 |
| Event Envelope | 운영과 추적이 쉽다 | 필드가 늘어난다 | 메시징/이벤트 기반 시스템 |
| 외부 broker schema | 관리가 체계적이다 | broker 의존이 커진다 | 대규모 이벤트 스트림 |

판단 기준은 다음과 같다.

- 재처리와 추적이 중요하면 envelope를 둔다
- payload만 보면 운영 맥락이 사라진다
- version과 correlation은 초기에 넣는 편이 낫다

---

## 꼬리질문

> Q: correlation id와 causation id는 왜 다른가요?
> 의도: 추적 체인의 시작과 원인을 구분하는지 확인한다.
> 핵심: correlation은 같은 흐름, causation은 직접 원인이다.

> Q: envelope가 너무 무거워지면 어떤가요?
> 의도: 메타데이터 과잉을 경계하는지 확인한다.
> 핵심: 필수 운영 메타만 남겨야 한다.

> Q: event sourcing에서 envelope가 꼭 필요한가요?
> 의도: 패턴을 절대 규칙으로 보지 않는지 확인한다.
> 핵심: 필수는 아니지만 실무에서 매우 유용하다.

## 한 줄 정리

Event Envelope는 이벤트 payload와 운영 메타데이터를 분리해 추적과 버전 관리를 쉽게 만든다.
