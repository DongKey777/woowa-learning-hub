# Event Sourcing, CQRS Adoption Criteria

> 한 줄 요약: Event Sourcing과 CQRS는 "멋진 아키텍처"가 아니라, 감사 추적과 읽기/쓰기 모델 분리 요구가 명확할 때만 값어치가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)
> - [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)

## 핵심 개념

Event Sourcing은 상태를 직접 저장하는 대신, **상태를 바꾸는 이벤트 자체를 저장**하는 방식이다.
CQRS는 **쓰기 모델과 읽기 모델을 분리**하는 방식이다.

둘은 자주 같이 나오지만 같은 개념은 아니다.

- Event Sourcing은 저장 방식
- CQRS는 모델 분리 방식

같이 쓰면 강력하지만, 같이 써야 하는 것은 아니다.

## 왜 도입하는가

다음 문제가 동시에 있으면 도입을 검토할 가치가 있다.

- “누가 언제 왜 이 상태로 바꿨는가”를 반드시 추적해야 한다
- 읽기 화면이 다양해서 조회 모델이 계속 달라진다
- 쓰기 규칙이 복잡해서 상태 변경 이력을 남겨야 한다
- 나중에 과거 시점으로 재생하거나 복구해야 한다

즉, 단순 CRUD보다 **변화의 역사**가 비즈니스 가치가 될 때 유리하다.

## 깊이 들어가기

### 1. Event Sourcing의 장단점

장점:
- 상태 변경 이력을 그대로 남길 수 있다
- 특정 시점의 상태를 재생할 수 있다
- 감사, 분쟁 대응, 분석에 강하다

단점:
- 이벤트 버전 관리가 어렵다
- 상태 재구성 비용이 있다
- 디버깅이 이벤트 스트림 이해에 의존한다

### 2. CQRS가 필요한 이유

쓰기 모델은 보통 규칙 중심이다.
읽기 모델은 보통 화면 중심이다.

이 둘을 하나의 모델로 억지로 맞추면:
- 쓰기 규칙이 조회 요구에 끌려다닌다
- 조회를 위해 도메인 객체가 비대해진다
- 인덱스와 조인 전략이 도메인에 새어 나온다

CQRS는 이 충돌을 줄인다.

### 3. Projection과 Rebuild

읽기 모델은 보통 projection으로 만든다.

```text
Event Store -> Projection Handler -> Read Model
```

projection은 다시 만들 수 있어야 한다.
이게 안 되면 이벤트 기반 설계의 장점이 절반쯤 사라진다.

### 4. 언제 과해지는가

다음 상황이면 보수적으로 가는 게 낫다.

- 도메인 규칙이 단순하다
- 감사/복구 요구가 약하다
- 읽기 모델이 하나뿐이다
- 팀이 이벤트 버전 관리에 익숙하지 않다

이 경우 CRUD + Domain Event + Outbox 정도가 더 낫다.

## 실전 시나리오

### 시나리오 1: 결제/정산

결제는 단순히 `paid = true`가 아니라, 승인/취소/환불/부분환불/재시도 이력이 중요하다.

이런 도메인은 이벤트가 더 자연스럽다.

### 시나리오 2: 주문 히스토리

사용자는 “현재 상태”보다 “어떤 순서로 바뀌었는지”를 묻는다.
이력 기반 조회가 핵심이면 event sourcing이 맞을 수 있다.

### 시나리오 3: 대시보드

운영 화면은 쓰기 규칙보다 읽기 형태가 더 중요하다.
여기서는 CQRS로 읽기 모델을 따로 두는 편이 유리하다.

## 코드로 보기

### 이벤트 저장 예시

```java
public record OrderPlacedEvent(
    long orderId,
    long userId,
    long totalAmount,
    long occurredAt
) {}

public class OrderService {
    private final EventStore eventStore;

    public void placeOrder(OrderCommand command) {
        OrderPlacedEvent event = new OrderPlacedEvent(
            command.orderId(),
            command.userId(),
            command.totalAmount(),
            System.currentTimeMillis()
        );
        eventStore.append(event);
    }
}
```

### Projection 예시

```java
public class OrderSummaryProjection {
    public void handle(OrderPlacedEvent event) {
        orderSummaryRepository.upsert(
            event.orderId(),
            event.userId(),
            event.totalAmount()
        );
    }
}
```

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| CRUD | 단순하다 | 이력과 재생이 약하다 | 작은 도메인 |
| CRUD + Domain Event | 점진적 확장이 쉽다 | 완전한 재생은 어렵다 | 대부분의 서비스 |
| Event Sourcing | 이력/감사/재생이 강하다 | 복잡도가 높다 | 이력이 비즈니스 자산일 때 |
| CQRS | 읽기/쓰기 최적화 가능 | 모델이 둘이라 운영이 어렵다 | 조회 형태가 다양할 때 |

## 꼬리질문

- Event Sourcing을 썼을 때 이벤트 버전 업그레이드는 어떻게 할 것인가?
- CQRS에서 읽기 모델이 stale해졌을 때 사용자 경험은 어떻게 설계할 것인가?
- Outbox와 Event Sourcing은 왜 비슷해 보이지만 목적이 다른가?
- projection이 깨졌을 때 재빌드 전략은 어떻게 가져갈 것인가?

## 한 줄 정리

Event Sourcing과 CQRS는 "복잡한 도메인에서 변경 이력과 조회 최적화가 실제 가치가 될 때"만 선택해야 하는 도구다.

