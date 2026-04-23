# Domain Events vs Integration Events

> 한 줄 요약: Domain Event는 bounded context 내부 의미를 표현하고, Integration Event는 외부 계약을 위한 번역된 메시지다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](./saga-coordinator-pattern-language.md)
> - [Process Manager vs Saga Coordinator](./process-manager-vs-saga-coordinator.md)
> - [Domain Event Translation Pipeline](./domain-event-translation-pipeline.md)
> - [Event Upcaster Compatibility Patterns](./event-upcaster-compatibility-patterns.md)
> - [Tolerant Reader for Event Contracts](./tolerant-reader-event-contract-pattern.md)
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
> - [Event Envelope Pattern](./event-envelope-pattern.md)
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [Bounded Context Relationship Patterns](./bounded-context-relationship-patterns.md)
> - [Anti-Corruption Translation Map Pattern](./anti-corruption-translation-map-pattern.md)

---

## 핵심 개념

둘 다 "이벤트"라고 부르기 때문에 많은 팀이 섞어 쓴다.  
하지만 설계 목적은 꽤 다르다.

- Domain Event: 우리 도메인 안에서 의미 있는 상태 변화
- Integration Event: 다른 bounded context나 외부 시스템에 공개할 계약 메시지

둘을 구분하지 않으면 내부 모델이 외부 계약으로 굳어 버리거나, 반대로 외부 호환성 때문에 내부 모델 진화가 막힌다.

### Retrieval Anchors

- `domain event`
- `integration event`
- `event contract`
- `after commit publication`
- `outbox translation`
- `bounded context event boundary`
- `published language versioning`
- `event contract evolution`
- `event upcaster`
- `outbox relay`
- `tolerant reader`

---

## 깊이 들어가기

### 1. Domain Event는 도메인 언어를 기록한다

Domain Event는 aggregate나 domain model 입장에서 의미 있는 사실이다.

- `OrderPlaced`
- `PaymentCaptured`
- `CouponRedeemed`

핵심은 "내부 도메인 의미"다.

- 필드는 내부 모델에 맞춰질 수 있다
- 이벤트 이름이 팀의 유비쿼터스 언어를 반영한다
- 아직 외부 호환성을 고려하지 않아도 된다

즉 domain event는 모델 내부의 의미를 풍부하게 담을 수 있다.

### 2. Integration Event는 외부 계약이다

Integration Event는 다른 팀, 다른 서비스, 다른 저장 모델이 소비한다.

- 필드 이름은 더 안정적이어야 한다
- 버전 호환성을 고려해야 한다
- 내부 엔티티 구조를 그대로 노출하면 안 된다

예를 들어 내부 aggregate가 `OrderPlaced`를 발생시켜도, 외부로는 다음 같은 계약으로 내보낼 수 있다.

- `OrderSubmittedV1`
- `CheckoutCompleted`
- `OrderReadyForFulfillment`

즉 integration event는 내부 사실의 단순 복사가 아니라 **경계 밖으로 내보낼 공개 언어**다.

### 3. 보통은 after-commit translation이 안전하다

가장 흔한 실수는 aggregate에서 만든 domain event를 그 자리에서 외부 브로커로 바로 발행하는 것이다.

그러면 다음 문제가 생긴다.

- DB transaction은 실패했는데 이벤트는 이미 나감
- 내부 필드 구조가 외부 계약이 됨
- 재시도와 중복 처리 정책이 모호해짐

더 안전한 기본값은 다음이다.

- aggregate가 domain event를 기록한다
- application layer가 commit 안에서 outbox를 함께 저장한다
- 별도 publisher가 이를 integration event로 번역해 발행한다

즉 publish 시점과 message shape를 한 번 더 분리한다.

### 4. 모든 domain event가 integration event가 되는 것은 아니다

내부에서만 가치가 있는 이벤트가 많다.

- read model 갱신
- audit trail 축적
- 후속 정책 평가
- aggregate 내부 파생 계산 트리거

반대로 외부로 공개할 이벤트는 더 드물고 더 엄격해야 한다.

### 5. 버전 전략은 integration event 쪽의 문제다

Domain Event는 내부 리팩터링과 함께 바뀔 수 있다.  
Integration Event는 소비자와의 약속이므로 그렇게 쉽게 바꾸면 안 된다.

그래서 보통 다음 규칙이 붙는다.

- 필드 추가는 호환 가능하게
- 의미 변경은 새 버전으로
- 삭제는 deprecated 기간을 둔다

---

## 실전 시나리오

### 시나리오 1: 주문 생성

`Order` aggregate는 `OrderPlaced`를 기록할 수 있다.  
하지만 외부 물류 시스템에는 주문 내부 컬렉션 구조를 그대로 노출하지 말고, 필요한 계약 필드만 담은 `OrderSubmittedV1`를 내보내는 편이 안전하다.

### 시나리오 2: 내부 검색 인덱스 갱신

검색 인덱스 갱신은 같은 bounded context 내부 read model 작업일 수 있다.  
이 경우 domain event만으로 충분하고 integration event까지 만들 필요는 없다.

### 시나리오 3: 결제 완료 알림

결제 완료를 알림 서비스, 정산 서비스, CRM이 함께 쓴다면 integration event로 공개할 가치가 있다.  
이때는 재처리와 스키마 버전까지 같이 설계해야 한다.

---

## 코드로 보기

### Aggregate가 domain event를 기록

```java
public class Order {
    private final List<DomainEvent> domainEvents = new ArrayList<>();

    public static Order place(MemberId memberId, List<OrderLine> lines) {
        Order order = new Order(memberId, lines);
        order.domainEvents.add(new OrderPlaced(order.id, memberId, order.totalAmount));
        return order;
    }

    public List<DomainEvent> pullDomainEvents() {
        List<DomainEvent> copied = List.copyOf(domainEvents);
        domainEvents.clear();
        return copied;
    }
}
```

### Application layer가 outbox에 번역해서 저장

```java
@Transactional
public void placeOrder(PlaceOrderCommand command) {
    Order order = Order.place(command.memberId(), command.lines());
    orderRepository.save(order);

    for (DomainEvent event : order.pullDomainEvents()) {
        if (event instanceof OrderPlaced placed) {
            outboxRepository.save(IntegrationMessage.of(
                "OrderSubmittedV1",
                placed.orderId(),
                Map.of(
                    "orderId", placed.orderId(),
                    "memberId", placed.memberId(),
                    "totalAmount", placed.totalAmount()
                )
            ));
        }
    }
}
```

### 구분 원칙

```java
// Domain Event: 내부 의미
// Integration Event: 외부 계약
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Domain Event만 사용 | 내부 모델링이 빠르다 | 외부 계약이 필요하면 부족하다 | 같은 bounded context 내부 반응 |
| Domain Event -> Integration Event 번역 | 경계가 선명하고 진화가 쉽다 | outbox/publisher 설계가 필요하다 | 외부 팀/서비스와 연결될 때 |
| Domain Event를 바로 외부 발행 | 구현이 빠르다 | 내부 모델 누수와 일관성 문제가 생긴다 | 아주 짧은 실험 외에는 피하는 편이 좋다 |

판단 기준은 다음과 같다.

- 소비자가 경계 밖이면 integration event를 의식한다
- commit 일관성이 중요하면 outbox 번역을 기본값으로 둔다
- 내부 모델 필드를 외부 계약으로 고정하지 않는다

---

## 꼬리질문

> Q: Domain Event를 Kafka로 보내면 그게 바로 Integration Event 아닌가요?
> 의도: 운반 수단과 설계 역할을 구분하는지 본다.
> 핵심: 아니다. Kafka에 실려도 내부 의미를 그대로 내보내면 domain event의 외부 노출일 뿐이다.

> Q: 모든 이벤트를 이중으로 만들어야 하나요?
> 의도: 과설계를 피하는 감각을 보는 질문이다.
> 핵심: 아니다. 경계 밖 소비자가 생길 때 번역 계층이 필요하다.

> Q: 왜 after-commit이 중요하나요?
> 의도: 저장 성공과 메시지 발행의 일관성을 이해하는지 본다.
> 핵심: DB는 실패했는데 이벤트만 나가는 상황을 막기 위해서다.

## 한 줄 정리

Domain Event는 내부 의미를, Integration Event는 외부 계약을 표현하므로 같은 이름의 "이벤트"라도 경계와 책임을 분리해서 다뤄야 한다.
