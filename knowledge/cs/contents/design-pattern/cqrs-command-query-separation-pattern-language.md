# CQRS: Command와 Query를 분리하는 패턴 언어

> 한 줄 요약: CQRS는 쓰기와 읽기의 관심사를 분리해, 명령은 상태 변경에 집중하고 조회는 읽기 최적화 모델에 집중하게 만든다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Command Pattern, Undo, Queue](./command-pattern-undo-queue.md)
> - [Specification Pattern](./specification-pattern.md)
> - [Repository Boundary: Aggregate Persistence vs Read Model](./repository-boundary-aggregate-vs-read-model.md)
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [Saga / Coordinator](./saga-coordinator-pattern-language.md)

---

## 핵심 개념

CQRS(Command Query Responsibility Segregation)는 **상태를 바꾸는 책임과 상태를 읽는 책임을 분리**하는 아키텍처/패턴 언어다.  
많이 오해하지만, CQRS는 반드시 두 개의 DB를 뜻하지 않는다.

핵심은 다음이다.

- Command: 상태를 변경한다
- Query: 상태를 조회한다
- 둘의 모델과 최적화 기준은 달라도 된다

### Retrieval Anchors

- `command query separation`
- `read model`
- `write model`
- `projection`
- `materialized view`
- `query service boundary`
- `aggregate persistence boundary`
- `read your writes`
- `projection lag`
- `projection rebuild`
- `projection cutover`

---

## 깊이 들어가기

### 1. 명령과 조회는 요구사항이 다르다

쓰기 모델은 정합성과 규칙이 중요하다.  
읽기 모델은 조회 속도와 표현이 중요하다.

둘을 하나의 모델로 억지로 맞추면 다음 문제가 생긴다.

- 조회를 위해 엔티티가 비대해진다
- 정합성을 위해 화면 편의가 희생된다
- 복잡한 join과 계산이 쓰기 경로에 들어온다

### 2. CQRS는 분리의 정도를 조절할 수 있다

가벼운 형태는 같은 DB를 공유하면서 코드 구조만 분리할 수 있다.  
강한 형태는 이벤트 기반으로 읽기 모델을 따로 유지한다.

| 구분 | 가벼운 분리 | 강한 분리 |
|---|---|---|
| 저장소 | 동일 DB 가능 | 별도 read model 가능 |
| 동기성 | 높다 | 결국 eventual consistency |
| 복잡도 | 낮다 | 높다 |

### 3. CQRS는 이벤트와 자주 연결된다

쓰기 모델이 변경되면 이벤트를 발행하고, 읽기 모델은 그 이벤트를 소비해 projection을 갱신한다.
이 구조는 응답성과 확장성에 좋지만, 운영 관점에서 추적 지점이 늘어난다.

---

## 실전 시나리오

### 시나리오 1: 주문 등록과 주문 조회

주문 등록은 검증과 정합성이 중요하고, 주문 조회는 검색 성능과 화면 조합이 중요하다.

### 시나리오 2: 관리자 대시보드

관리자 화면은 여러 테이블을 조합한 읽기 전용 모델이 더 적합하다.

### 시나리오 3: 대용량 상태 집계

주문 수, 결제 완료 건수, 취소율 같은 집계는 읽기 모델로 따로 두면 빠르다.

---

## 코드로 보기

### Command

```java
public record PlaceOrderCommand(Long userId, List<Long> itemIds) {}

@Service
public class PlaceOrderCommandHandler {
    private final OrderRepository repository;

    public OrderId handle(PlaceOrderCommand command) {
        Order order = Order.place(command.userId(), command.itemIds());
        repository.save(order);
        return order.getId();
    }
}
```

### Query

```java
public record OrderSummary(Long orderId, String status, int totalAmount) {}

@Service
public class OrderQueryService {
    private final OrderReadRepository readRepository;

    public List<OrderSummary> findRecentOrders(Long userId) {
        return readRepository.findRecentOrders(userId);
    }
}
```

### Projection

```java
@Component
public class OrderProjection {
    @EventListener
    public void on(OrderPlacedEvent event) {
        // read model 갱신
    }
}
```

Command은 상태를 바꾸고, Query는 읽기 최적화 모델을 조회한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 모델 | 단순하다 | 읽기/쓰기 요구가 충돌한다 | 작은 시스템 |
| 코드 분리만 CQRS | 도입 비용이 낮다 | 성능 최적화는 제한적이다 | 분리가 필요하지만 복잡도는 낮출 때 |
| 읽기 모델 분리 | 조회가 빠르다 | eventual consistency가 생긴다 | 조회 트래픽이 큰 시스템 |

판단 기준은 다음과 같다.

- 조회와 쓰기 요구가 크게 다르면 CQRS를 검토한다
- 읽기 모델이 복잡해지면 projection을 분리한다
- 정합성이 강하게 요구되면 단순 분리를 먼저 시도한다

---

## 꼬리질문

> Q: CQRS는 무조건 데이터베이스를 둘로 나누나요?
> 의도: CQRS의 본질이 저장소 분리가 아니라 책임 분리라는 점을 아는지 확인한다.
> 핵심: 아니다. 핵심은 command와 query의 관심사 분리다.

> Q: CQRS와 Command 패턴은 같은 건가요?
> 의도: 이름이 비슷한 패턴을 같은 레벨로 보지 않는지 확인한다.
> 핵심: Command 패턴은 요청 캡슐화이고, CQRS는 쓰기/읽기 분리다.

> Q: CQRS를 쓰면 항상 더 좋아지나요?
> 의도: 구조를 늘리는 대가를 이해하는지 확인한다.
> 핵심: 아니다. 운영 복잡도와 eventual consistency 비용이 따라온다.

## 한 줄 정리

CQRS는 명령과 조회를 분리해 쓰기 정합성과 읽기 최적화를 각각 다루게 하는 패턴 언어다.
