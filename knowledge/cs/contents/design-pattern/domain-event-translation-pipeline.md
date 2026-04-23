# Domain Event Translation Pipeline

> 한 줄 요약: Domain Event Translation Pipeline은 내부 도메인 이벤트를 그대로 외부에 내보내지 않고, outbox와 translator를 거쳐 published language로 변환하면서 계약 진화를 관리하는 패턴이다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
> - [Event Upcaster Compatibility Patterns](./event-upcaster-compatibility-patterns.md)
> - [Tolerant Reader for Event Contracts](./tolerant-reader-event-contract-pattern.md)
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
> - [Event Envelope Pattern](./event-envelope-pattern.md)
> - [Bounded Context Relationship Patterns](./bounded-context-relationship-patterns.md)
> - [Anti-Corruption Translation Map Pattern](./anti-corruption-translation-map-pattern.md)
> - [Event Sourcing: 변경 이력을 진실의 원천으로 쓰는 패턴 언어](./event-sourcing-pattern-language.md)

---

## 핵심 개념

Domain event와 integration event를 구분하자고 해도, 실제 시스템에는 한 단계가 더 필요하다.  
바로 **어떻게 번역하고, 어디서 계약을 안정화하고, 모델 진화를 어떻게 흡수할 것인가**다.

Domain Event Translation Pipeline은 보통 이런 흐름을 가진다.

1. aggregate가 domain event를 기록한다
2. application layer가 outbox에 발행 후보를 저장한다
3. translator가 published language 계약으로 변환한다
4. envelope가 버전/추적 메타데이터를 감싼다
5. publisher가 외부 브로커로 전달한다

핵심은 "이벤트를 발행한다"가 아니라 **내부 의미를 외부 계약으로 안전하게 번역한다**는 데 있다.

### Retrieval Anchors

- `domain event translation pipeline`
- `integration event mapper`
- `published language versioning`
- `event contract evolution`
- `outbox translator`
- `event upcasting strategy`
- `outbox relay`
- `idempotent publisher`
- `tolerant reader`

---

## 깊이 들어가기

### 1. 번역 파이프라인이 필요한 이유는 내부 모델 진화 속도와 외부 계약 안정성이 다르기 때문이다

내부 aggregate는 리팩터링과 함께 바뀔 수 있다.

- 필드 구조 변경
- 값 객체 도입
- 상태 이름 변경
- aggregate 경계 재조정

하지만 외부 계약은 소비자가 이미 붙어 있다.

- 물류 시스템
- 정산 시스템
- CRM
- 데이터 파이프라인

그래서 translator는 단순 매핑이 아니라 **진화 속도가 다른 두 세계 사이의 완충지대**가 된다.

### 2. outbox 저장 시점과 translation 시점은 분리할 수 있다

팀마다 두 가지 방식을 택한다.

- commit 안에서 integration payload까지 완성해 outbox 저장
- commit 안에서는 domain event snapshot만 저장하고, publisher가 translation 수행

첫 방식은 발행 payload가 일찍 고정된다.  
둘째 방식은 번역 규칙을 나중에 바꾸기 쉽지만 publisher 책임이 커진다.

중요한 건 어느 쪽이든 **translation rule이 명시적이어야 한다**는 점이다.

### 3. Published Language는 내부 엔티티 dump가 아니다

나쁜 번역은 내부 모델을 거의 그대로 내보낸다.

- 엔티티 필드명을 그대로 사용
- 내부 enum 이름을 그대로 공개
- 소비자가 내부 aggregate 구조를 알아야 파싱 가능

좋은 번역은 외부 소비자 관점의 의미를 우선한다.

- 안정적인 필드명
- 계약 버전
- 선택적 필드 추가 전략
- 과거와 미래 소비자를 모두 고려한 shape

### 4. 모델 진화는 새 버전과 upcasting을 함께 생각해야 한다

모델 진화 시 자주 나오는 선택지는 다음과 같다.

- 같은 이벤트 타입에 optional field 추가
- 새 의미면 새 버전 이벤트 타입 도입
- 저장된 과거 이벤트는 upcaster로 현재 소비 모델에 맞춤

여기서 중요한 건 "무조건 새 버전"이 아니라 의미 변화의 크기다.

- 단순 필드 추가: 하위 호환 가능
- 필드 의미 변경: 새 버전이 안전
- 의미 분해/통합: translation rule과 upcasting을 함께 검토

### 5. translator는 비즈니스 규칙의 본체가 아니라 공개 계약 변환기다

가끔 translator가 도메인 규칙까지 떠안으면서 또 다른 god mapper가 된다.

- 할인 계산
- 상태 전이 판단
- 권한 체크
- 외부 호출

이건 translation layer가 아니라 application/domain 책임 침범이다.  
Translator는 가능한 한 **계약 shape와 의미 이름 변환**에 집중하는 편이 좋다.

---

## 실전 시나리오

### 시나리오 1: 주문 도메인 리팩터링

내부에서 `OrderPlaced`가 `CheckoutAccepted`와 `OrderCreated`로 분리되더라도, 외부 fulfillment 팀은 당장 `OrderSubmittedV1`만 필요할 수 있다.  
Translation pipeline이 있으면 내부 분해와 외부 계약 안정성을 동시에 가져갈 수 있다.

### 시나리오 2: 필드 의미 변경

기존 `totalAmount`가 할인 전 금액이었다가 할인 후 청구 금액으로 바뀌면, 같은 필드명 재사용은 위험하다.  
`chargedAmount`를 포함한 `OrderSubmittedV2`로 가는 편이 더 안전하다.

### 시나리오 3: 과거 이벤트 재처리

데이터 재적재나 replay가 필요할 때, 오래된 outbox/event store 기록을 최신 소비자 계약으로 맞춰야 할 수 있다.  
이때 upcaster나 translation compatibility layer가 유용하다.

---

## 코드로 보기

### domain event

```java
public record OrderPlaced(
    OrderId orderId,
    MemberId memberId,
    Money totalAmount
) implements DomainEvent {}
```

### translator

```java
public class OrderEventTranslator {
    public EventEnvelope<OrderSubmittedV1> translate(OrderPlaced event) {
        return new EventEnvelope<>(
            UUID.randomUUID().toString(),
            "OrderSubmittedV1",
            Instant.now(),
            correlationIdFor(event),
            causationIdFor(event),
            1,
            new OrderSubmittedV1(
                event.orderId().value(),
                event.memberId().value(),
                event.totalAmount().amount()
            )
        );
    }
}
```

### version split

```java
public sealed interface OrderSubmittedContract permits OrderSubmittedV1, OrderSubmittedV2 {}
```

### upcasting 감각

```java
public class OrderSubmittedUpcaster {
    public OrderSubmittedV2 upcast(OrderSubmittedV1 legacy) {
        return new OrderSubmittedV2(
            legacy.orderId(),
            legacy.memberId(),
            legacy.totalAmount(),
            "UNKNOWN_CHANNEL"
        );
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 내부 이벤트 그대로 외부 발행 | 구현이 빠르다 | 계약 진화와 모델 누수에 취약하다 | 짧은 실험 단계 정도 |
| 명시적 translation pipeline | 경계와 진화 전략이 선명하다 | mapper/outbox/publisher 설계가 필요하다 | 외부 소비자가 늘거나 계약 수명이 길 때 |
| 버전 없는 단일 계약 유지 | 운영이 단순해 보인다 | 의미 변화가 쌓이면 파손 위험이 크다 | 변화가 거의 없는 내부 전용 계약 |

판단 기준은 다음과 같다.

- 내부 모델 진화 속도와 외부 계약 안정성을 분리한다
- translation layer는 공개 언어를 소유한다
- replay와 재처리가 필요하면 upcasting 전략까지 미리 본다

---

## 꼬리질문

> Q: translation pipeline이 있으면 이벤트를 항상 두 번 저장하나요?
> 의도: 개념적 단계와 물리 저장 방식을 구분하는지 본다.
> 핵심: 꼭 그렇진 않다. 중요한 건 번역 경계가 명시되는 것이다.

> Q: 새 필드가 추가되면 무조건 V2를 만들어야 하나요?
> 의도: 버전 전략을 기계적으로 적용하지 않는지 본다.
> 핵심: 아니다. 의미가 유지되고 optional하게 추가 가능하면 호환 확장이 더 낫다.

> Q: upcaster는 event sourcing에서만 필요한가요?
> 의도: 저장된 과거 메시지 재해석 문제를 폭넓게 보는지 확인한다.
> 핵심: 아니다. 오래된 outbox 레코드 재처리나 계약 호환 계층에도 유용하다.

## 한 줄 정리

Domain Event Translation Pipeline은 내부 도메인 사실을 published language 계약으로 번역하면서, 외부 계약 안정성과 내부 모델 진화를 동시에 관리하게 해준다.
