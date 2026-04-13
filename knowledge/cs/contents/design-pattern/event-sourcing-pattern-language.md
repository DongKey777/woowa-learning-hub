# Event Sourcing: 변경 이력을 진실의 원천으로 쓰는 패턴 언어

> 한 줄 요약: Event Sourcing은 현재 상태를 직접 저장하기보다, 발생한 사건의 흐름을 저장하고 상태는 그 결과로 재구성하는 방식이다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)
> - [Saga / Coordinator](./saga-coordinator-pattern-language.md)
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [Unit of Work Pattern](./unit-of-work-pattern.md)

---

## 핵심 개념

Event Sourcing은 **상태를 덮어쓰는 대신 사건을 순서대로 저장**하는 패턴 언어다.  
현재의 값은 이벤트의 결과이며, 필요하면 재생(replay)해서 다시 계산할 수 있다.

이 방식은 강력하지만, 다루는 복잡도도 높다.

- 변경 이력이 남는다
- 감사와 재현이 쉽다
- 읽기 모델을 따로 두는 경우가 많다
- 이벤트 버전 관리가 필요하다

### Retrieval Anchors

- `event sourcing`
- `event log as source of truth`
- `state reconstruction`
- `replay events`
- `event versioning`

---

## 깊이 들어가기

### 1. 상태 대신 사건을 저장한다

예를 들어 주문이 다음 이벤트를 가질 수 있다.

- OrderPlaced
- PaymentAuthorized
- PaymentCaptured
- OrderShipped

이벤트를 저장하면 현재 상태는 언제든 다시 계산할 수 있다.

### 2. 장점은 감사성, 단점은 복잡성이다

장점:

- 과거를 추적할 수 있다
- 버그 재현이 쉽다
- 실패 상황 분석에 강하다

단점:

- 이벤트 스키마 진화가 어렵다
- 조회 모델이 별도로 필요하다
- 단순 CRUD보다 훨씬 복잡하다

### 3. CQRS와 자주 묶인다

쓰기 모델은 이벤트를 append하고, 읽기 모델은 projection으로 갱신한다.
그래서 Event Sourcing은 CQRS와 함께 등장하는 경우가 많다.

---

## 실전 시나리오

### 시나리오 1: 결제/정산 로그

결제 과정이 복잡하고 감사가 중요하면 이벤트를 남기는 방식이 강하다.

### 시나리오 2: 주문 이력 추적

누가 언제 무엇을 바꿨는지 추적해야 하는 경우 적합하다.

### 시나리오 3: 상태 재현이 중요한 시스템

장애 시점의 상태를 다시 만들어야 하면 replay가 큰 힘을 발휘한다.

---

## 코드로 보기

### 이벤트 저장

```java
public interface DomainEvent {}

public record OrderPlaced(Long orderId, Long userId) implements DomainEvent {}
public record PaymentCaptured(Long orderId, int amount) implements DomainEvent {}
```

### Aggregate

```java
public class OrderAggregate {
    private final List<DomainEvent> changes = new ArrayList<>();

    public void place(Long orderId, Long userId) {
        apply(new OrderPlaced(orderId, userId));
    }

    private void apply(DomainEvent event) {
        changes.add(event);
        // 상태 갱신
    }

    public List<DomainEvent> changes() {
        return List.copyOf(changes);
    }
}
```

### Replay

```java
public OrderAggregate rehydrate(List<DomainEvent> history) {
    OrderAggregate aggregate = new OrderAggregate();
    for (DomainEvent event : history) {
        aggregate.apply(event);
    }
    return aggregate;
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| CRUD | 단순하다 | 이력 재현이 약하다 | 단순 도메인 |
| Event Sourcing | 이력이 진실의 원천이 된다 | 복잡도가 크다 | 감사와 재현이 중요할 때 |
| Event Sourcing + CQRS | 읽기 최적화가 좋다 | 운영 난이도가 높다 | 조회 트래픽도 클 때 |

판단 기준은 다음과 같다.

- "왜 이 상태가 되었는가"가 중요하면 Event Sourcing
- 최신 상태만 중요하면 CRUD가 더 낫다
- 읽기와 쓰기 요구가 다르면 CQRS와 함께 본다

---

## 꼬리질문

> Q: Event Sourcing과 로그는 같은가요?
> 의도: 단순 로그와 도메인 이벤트를 구분하는지 확인한다.
> 핵심: 이벤트는 도메인 상태를 재구성하는 근거여야 한다.

> Q: 이벤트 버전 관리가 왜 어렵나요?
> 의도: 시간이 지나도 재생 가능한 설계가 필요한지 아는지 확인한다.
> 핵심: 과거 이벤트 형식이 바뀌어도 replay가 가능해야 하기 때문이다.

> Q: Event Sourcing을 언제 피해야 하나요?
> 의도: 복잡도 대비 효익을 판단하는지 확인한다.
> 핵심: 감사와 재현이 중요하지 않으면 과한 경우가 많다.

## 한 줄 정리

Event Sourcing은 상태를 직접 저장하지 않고 사건의 흐름을 저장해, 재현과 감사에 강한 패턴 언어다.

