# Repository Fake Design Guide

> 한 줄 요약: repository fake는 DB 없는 JPA 흉내가 아니라 outbound port 계약을 메모리에서 재현하는 test adapter여야 하고, 유스케이스 test는 그 계약만 의존해야 persistence 세부가 새지 않는다.

**난이도: 🟡 Intermediate**

관련 문서:

- [Fake vs Mock 첫 테스트 프라이머](./fake-vs-mock-first-test-primer.md)
- [Outbound Notifier Mock Boundary Primer](./outbound-notifier-mock-boundary-primer.md)
- [Repository Interface Contract Primer](./repository-interface-contract-primer.md)
- [Repository, DAO, Entity](./repository-dao-entity.md)
- [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)
- [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)


retrieval-anchor-keywords: repository fake design guide, repository fake intermediate, fake repository example, memory repository example, repository port contract, outbound port fake, mock vs fake repository, 처음 repository fake 다음, repository interface 다음 문서, mock 대신 fake 왜, what is repository fake, fake repository contract, service repository contract test, jpa 흉내 말고 계약 재현

이 문서는 Beginner 입문서 다음 칸에 놓인 Intermediate 가이드다.
`Repository Interface Contract Primer`에서 "`service가 기대하는 저장 계약을 test에서는 어떻게 재현하지?`"까지 왔다면 여기로 올라오면 된다.
아직 질문이 "`첫 failing test에서 fake와 mock 중 뭐부터 집어야 하지?`"라면 [Fake vs Mock 첫 테스트 프라이머](./fake-vs-mock-first-test-primer.md)로 먼저 내려가 결과 중심 선택 기준부터 짧게 잡는 편이 더 안전하다.
질문이 `flush`, dirty checking, `cascade`, `Entity` 매핑 자체로 기울어 있으면 fake 설계보다 [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)나 [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)를 먼저 보는 편이 맞다.
<details>
<summary>Table of Contents</summary>

- [왜 별도 가이드가 필요한가](#왜-별도-가이드가-필요한가)
- [먼저 repository port semantics를 고정한다](#먼저-repository-port-semantics를-고정한다)
- [fake가 재현해야 할 것](#fake가-재현해야-할-것)
- [fake가 재현하지 말아야 할 것](#fake가-재현하지-말아야-할-것)
- [코드로 보기](#코드로-보기)
- [integration test로 넘겨야 할 것](#integration-test로-넘겨야-할-것)
- [냄새 신호](#냄새-신호)
- [기억할 기준](#기억할-기준)

</details>

## 처음 3분 요약

처음에는 어렵게 잡지 말고 이렇게 보면 된다.

- repository fake는 "`DB 없이도 저장 계약을 읽을 수 있게 만든 메모리 저장소`"다.
- mock repository는 "`이 메서드를 불렀는지`"를 확인할 때 더 잘 맞는다.
- 초심자 starter에서는 보통 호출 횟수보다 "`저장 후 다시 읽으면 어떤 결과가 나와야 하나`"가 더 중요해서 fake가 먼저 등장한다.

짧게 비교하면 아래 표로 충분하다.

| 지금 확인하려는 질문 | 더 먼저 고를 것 | 이유 |
|---|---|---|
| "`중복 주문번호면 실패하나?`" | fake repository | 저장/조회/중복 같은 계약 결과를 한 흐름으로 읽을 수 있다 |
| "`알림을 정확히 1번 보냈나?`" | mock/spy | 호출 자체가 비즈니스 결과일 수 있다 |
| "`JPA dirty checking 없이도 save 의미가 분명한가?`" | fake repository | `save()` 전후 상태를 메모리에서 드러내기 쉽다 |

## 왜 별도 가이드가 필요한가

Hexagonal Architecture를 배우고 나면 유스케이스 test에서 outbound port를 fake로 바꾸는 감각은 빨리 잡힌다.
문제는 repository fake가 들어오는 순간 자주 이런 실수가 같이 따라온다는 점이다.

- fake가 `OrderEntity`를 저장한다
- fake가 `JpaRepository`, `Pageable`, `Specification`을 그대로 노출한다
- fake가 `findById()`로 꺼낸 객체를 같은 참조로 다시 돌려줘서 `save()` 없이도 변경이 반영된다
- test가 `flush`, `clear`, lazy loading 같은 JPA 동작을 알아야만 통과한다

이 상태가 되면 유스케이스 test는 "비즈니스 규칙을 빠르게 검증하는 test"가 아니라 "메모리 안에 옮겨 놓은 JPA 설명서"가 된다.

핵심 기준은 하나다.

- **유스케이스가 관찰할 수 있는 port 계약은 fake가 재현한다**
- **JPA나 DB만 관찰할 수 있는 구현 세부는 adapter integration test로 보낸다**

repository fake 설계가 어렵다면, 종종 fake가 아니라 **repository port 자체가 persistence 세부를 끌고 들어온 것**이 원인이다.

## 먼저 repository port semantics를 고정한다

fake 설계는 port 설계의 거울이다.
port가 도메인 언어로 선명하면 fake도 단순해지고, port가 JPA 언어를 끌고 오면 fake도 금방 이상해진다.

### 좋은 port의 기본 질문

| 질문 | port에 드러나야 하는 것 | port에 드러나지 말아야 하는 것 |
|---|---|---|
| 무엇을 저장/조회하나 | `Order`, `OrderId`, `OrderNumber` 같은 도메인 타입 | `OrderEntity`, `JpaRepository`, `EntityManager` |
| 실패를 어떻게 표현하나 | 없음, 중복, 버전 충돌 같은 유스케이스가 관찰하는 결과 | `DataIntegrityViolationException`, flush 타이밍 |
| 쓰기 lifecycle이 무엇인가 | `save(order)`처럼 명시적 저장 의도 | dirty checking이 알아서 반영된다는 전제 |
| 조회 의미가 무엇인가 | aggregate 조회, 존재 여부, 도메인 기준 정렬 | `Pageable`, `Sort`, `Specification` 같은 프레임워크 API |

예를 들면 이런 형태가 더 안전하다.

```java
public interface OrderRepository {
    Optional<Order> findById(OrderId id);
    boolean existsByOrderNumber(OrderNumber orderNumber);
    void save(Order order);
}
```

이 계약은 유스케이스가 실제로 아는 사실만 남긴다.

- 주문이 없을 수 있다
- 주문 번호 중복 여부를 볼 수 있다
- 저장 의도를 명시적으로 표현한다

반대로 아래 신호가 나오면 port부터 다시 보는 편이 낫다.

- `save()`가 아니라 transaction commit과 dirty checking을 fake가 대신 흉내 내야 한다
- `Page<OrderEntity>`가 없으면 use case를 테스트할 수 없다
- port가 `fetch join`, `entity graph`, `flush`를 직접 안다

특히 ID 생성이 DB auto increment에 묶여 있다면 repository fake가 불필요하게 DB 흉내를 내기 시작한다.
이 경우는 `OrderIdGenerator` 같은 별도 outbound port로 분리하거나, 애플리케이션 레벨에서 ID를 미리 만드는 편이 use case test를 훨씬 단순하게 만든다.

## fake가 재현해야 할 것

좋은 repository fake는 "실제 adapter와 완전히 같아야" 하는 것이 아니라, **port가 약속한 의미**를 지켜야 한다.

| 재현할 semantics | 이유 |
|---|---|
| 존재/부재 (`findById`, `exists...`) | 유스케이스의 분기 조건이기 때문이다 |
| 중복/충돌 규칙 | port가 uniqueness나 version 충돌을 약속했다면 fake도 같은 결과를 내야 한다 |
| 명시적 저장 결과 | `save()` 전후에 무엇이 영속 상태인지 구분해야 한다 |
| 계약된 조회 순서 | port가 정렬된 결과를 약속하면 fake도 같은 순서를 돌려줘야 한다 |
| 도메인 타입 round-trip | `Order`를 넣으면 다시 `Order`가 나와야 한다 |

여기서 특히 중요한 구현 습관이 **copy on write / copy on read**다.

- `save(order)` 할 때 내부 저장소에는 snapshot을 넣는다
- `findById(id)` 할 때는 새 도메인 객체를 만들어 돌려준다

이렇게 해야 test가 다음 착각을 하지 않는다.

- 저장 후 객체를 그냥 들고 있다가 바꾸면 저절로 반영될 것이다
- 한 번 조회한 객체는 영속성 컨텍스트가 계속 관리할 것이다

즉 fake는 **managed entity identity map**이 아니라, **repository 계약을 검증하는 메모리 저장소**에 가깝다.

## fake가 재현하지 말아야 할 것

아래 항목은 fake로 옮기기 시작할수록 use case test가 persistence 설명에 오염된다.

| fake가 재현하지 말아야 할 것 | 이유 |
|---|---|
| `@Entity`, `JpaRepository`, `EntityManager` | port 안쪽으로 JPA 타입이 새는 순간 경계가 무너진다 |
| dirty checking, flush, persistence context identity | 이것은 JPA 런타임 동작이지 use case 계약이 아니다 |
| lazy loading 프록시와 초기화 예외 | adapter mapping / transaction 경계 검증 주제다 |
| `cascade`, `orphanRemoval`, `mappedBy` | aggregate 규칙이 아니라 persistence 구현 결정이다 |
| `Pageable`, `Sort`, `Specification` 같은 Spring Data API | use case보다 query/persistence 프레임워크 의미가 앞선다 |
| fetch join, entity graph, SQL 힌트 | 성능/매핑 최적화는 integration test에서 검증해야 한다 |

짧게 말하면 이 기준이다.

- **유스케이스가 알아야 하는 의미는 fake로**
- **ORM이 알아서 처리하는 메커니즘은 adapter test로**

만약 fake가 dirty checking까지 흉내 내야만 현재 서비스 test가 통과한다면, 그건 fake를 똑똑하게 만들 문제가 아니라 application/service가 JPA 관리 상태에 의존하고 있다는 신호다.

## 메모리 repository 예시: 같은 질문을 fake로 읽기

초심자가 제일 헷갈리는 장면은 "`mock으로도 되는데 왜 fake를 만들죠?`"다.
같은 주문 생성 질문을 두 방식으로 놓고 보면 차이가 빨리 보인다.

질문은 하나로 고정한다.

- "`같은 주문번호가 이미 있으면 주문 생성이 실패해야 한다.`"

fake는 메모리에서 계약을 재현한다.
그래서 테스트가 결과 문장에 더 가깝게 읽힌다.

```java
@Test
void duplicate_order_number_is_rejected() {
    FakeOrderRepository repository = new FakeOrderRepository();
    repository.save(existingOrder("ORDER-001"));

    PlaceOrderService service = new PlaceOrderService(repository, fixedIdGenerator("order-2"));

    assertThatThrownBy(() -> service.place(command("ORDER-001")))
            .isInstanceOf(DuplicateOrderNumberException.class);
}
```

이 테스트는 초심자 눈에도 비교적 직접 읽힌다.

- 먼저 기존 주문을 저장했다
- 같은 주문번호로 다시 생성했다
- 중복이라 실패했다

즉 중심 질문이 `호출 순서`가 아니라 `계약 결과`다.

## 같은 질문을 mock으로 읽으면 무엇이 달라지나

mock은 호출 확인이 질문일 때 더 잘 맞는다.
같은 규칙을 mock 중심으로 쓰면 테스트의 초점이 조금 달라진다.

```java
@Test
void duplicate_order_number_is_rejected() {
    OrderRepository repository = mock(OrderRepository.class);
    given(repository.existsByOrderNumber(new OrderNumber("ORDER-001"))).willReturn(true);

    PlaceOrderService service = new PlaceOrderService(repository, fixedIdGenerator("order-2"));

    assertThatThrownBy(() -> service.place(command("ORDER-001")))
            .isInstanceOf(DuplicateOrderNumberException.class);

    then(repository).should(never()).save(any(Order.class));
}
```

이 테스트도 틀린 것은 아니다.
다만 초심자 starter에서는 아래처럼 읽힐 가능성이 높다.

- `existsByOrderNumber()`를 먼저 불렀는가
- `save()`를 안 불렀는가

즉 결과보다 상호작용이 먼저 눈에 들어온다.

## fake와 mock을 여기서 어떻게 고를까

| 같은 repository 경계 테스트에서 | fake가 더 잘 맞는 경우 | mock이 더 잘 맞는 경우 |
|---|---|---|
| 질문의 중심 | 저장 계약의 결과 | 호출 자체 |
| 테스트가 설명하는 문장 | "`중복이면 실패한다`" | "`이 메서드를 부르거나 안 부른다`" |
| beginner starter 적합도 | 높음 | 보조 수단 |

- repository처럼 `상태를 저장하고 다시 읽는 경계`는 fake가 결과 중심 읽기에 유리하다.
- notifier, event publisher처럼 `호출이 일 자체인 경계`는 mock/spy가 더 자연스럽다. 이쪽은 저장 계약이 아니라 상호작용 계약을 읽는 문제라서 [Outbound Notifier Mock Boundary Primer](./outbound-notifier-mock-boundary-primer.md)로 따로 분리해 보는 편이 덜 헷갈린다.
- 그래서 repository fake는 "mock보다 더 진짜 같아서"가 아니라, **현재 질문이 저장 계약 중심이라서** 선택하는 경우가 많다.

## 코드로 보기

아래 fake는 port semantics만 메모리에서 재현하는 쪽에 가깝다.

## 코드로 보기 (계속 2)

```java
public interface OrderRepository {
    Optional<Order> findById(OrderId id);
    boolean existsByOrderNumber(OrderNumber orderNumber);
    void save(Order order);
}

final class FakeOrderRepository implements OrderRepository {
    private final Map<OrderId, StoredOrder> storage = new LinkedHashMap<>();

    @Override
    public Optional<Order> findById(OrderId id) {
        StoredOrder stored = storage.get(id);
        if (stored == null) {
            return Optional.empty();
        }
        return Optional.of(stored.toDomain());
    }

    @Override
    public boolean existsByOrderNumber(OrderNumber orderNumber) {
        return storage.values().stream()
                .anyMatch(stored -> stored.orderNumber().equals(orderNumber));
    }

    @Override
    public void save(Order order) {
        if (hasDuplicateOrderNumber(order)) {
            throw new DuplicateOrderNumberException(order.orderNumber());
        }
        storage.put(order.id(), StoredOrder.from(order));
    }

    private boolean hasDuplicateOrderNumber(Order order) {
        return storage.values().stream()
                .anyMatch(stored -> stored.sameOrderNumber(order) && !stored.id().equals(order.id()));
    }

    private record StoredOrder(
            OrderId id,
            OrderNumber orderNumber,
            Address shippingAddress,
            List<StoredLine> lines
    ) {
        static StoredOrder from(Order order) {
            return new StoredOrder(

## 코드로 보기 (계속 3)

order.id(),
                    order.orderNumber(),
                    order.shippingAddress(),
                    order.lines().stream()
                            .map(line -> new StoredLine(line.productId(), line.quantity()))
                            .toList()
            );
        }

        Order toDomain() {
            return Order.rehydrate(
                    id,
                    orderNumber,
                    shippingAddress,
                    lines.stream()
                            .map(line -> new OrderLine(line.productId(), line.quantity()))
                            .toList()
            );
        }

        boolean sameOrderNumber(Order order) {
            return orderNumber.equals(order.orderNumber());
        }
    }

    private record StoredLine(ProductId productId, int quantity) {
    }
}
```

이 fake의 포인트는 세 가지다.

1. 내부 저장소가 `OrderEntity`가 아니라 domain snapshot을 저장한다.
2. `findById()`가 매번 새 domain 객체를 돌려줘서 managed entity 착각을 막는다.
3. 중복 주문번호처럼 port가 약속한 실패 semantics만 재현한다.

그래서 use case test도 결과 중심으로 읽을 수 있다.

## 코드로 보기 (계속 4)

```java
@Test
void duplicate_order_number_is_rejected() {
    FakeOrderRepository repository = new FakeOrderRepository();
    repository.save(existingOrder("ORDER-001"));

    PlaceOrderService service = new PlaceOrderService(repository, fixedIdGenerator("order-2"));

    assertThatThrownBy(() -> service.place(command("ORDER-001")))
            .isInstanceOf(DuplicateOrderNumberException.class);
}

@Test
void aggregate_changes_are_persisted_only_after_explicit_save() {
    FakeOrderRepository repository = new FakeOrderRepository();
    OrderId orderId = new OrderId("order-1");
    repository.save(existingOrder(orderId, "ORDER-001", "Seoul"));

    Order loaded = repository.findById(orderId).orElseThrow();
    loaded.changeShippingAddress(new Address("Busan"));

    assertThat(repository.findById(orderId).orElseThrow().shippingAddress())
            .isEqualTo(new Address("Seoul"));

    repository.save(loaded);

    assertThat(repository.findById(orderId).orElseThrow().shippingAddress())
            .isEqualTo(new Address("Busan"));
}
```

두 번째 test는 일부러 중요하다.
이 test가 깨진다면 현재 fake는 `save()` 없이도 변경이 반영되는, 즉 JPA dirty checking을 흉내 내는 쪽일 가능성이 높다.
그 경우 use case가 repository port보다 persistence context에 더 가깝게 설계된 것은 아닌지 먼저 의심해야 한다.

## integration test로 넘겨야 할 것

repository fake가 아무리 좋아도 아래 항목은 별도 adapter integration test가 필요하다.

- `Order <-> OrderEntity` 매핑이 맞는가
- `@Version` 기반 낙관적 락 충돌이 실제로 기대대로 터지는가
- `cascade`, `orphanRemoval`, FK 제약이 실제 schema와 맞는가
- fetch join, entity graph, projection이 성능/정합성 요구를 만족하는가
- transaction 경계 안팎에서 lazy loading 예외가 어떻게 드러나는가

즉 fake는 "유스케이스가 port를 어떻게 쓰는가"를 검증하고, integration test는 "adapter가 기술과 어떻게 붙는가"를 검증한다.
둘을 한 테스트에 섞을수록 속도도 느려지고 실패 원인도 흐려진다.

## 냄새 신호

아래 신호가 반복되면 repository fake나 port 경계가 persistence 쪽으로 기울고 있는 편이다.

- use case test import에 `OrderEntity`, `JpaRepository`, `EntityManager`, `Pageable`이 등장한다
- fake 클래스에 `flush()`, `clear()`, `deleteAllInBatch()` 같은 메서드가 필요해진다
- fake가 조회한 객체를 같은 참조로 다시 돌려줘서 `save()` 없이도 상태가 바뀐다
- fake 구현보다 JPA adapter 구현이 더 기준이 되고, domain 계약 설명은 뒤로 밀린다
- uniqueness, version conflict 같은 port 의미 대신 Spring 예외 타입이 test assertion의 중심이 된다
- fake를 만들려면 `mappedBy`, fetch 전략, cascade 설정을 먼저 떠올려야 한다

이때의 처방은 보통 둘 중 하나다.

1. repository port를 더 작고 명시적인 도메인 계약으로 줄인다.
2. query/persistence 최적화 요구를 별도 adapter integration test나 query port로 분리한다.

## 기억할 기준

- repository fake는 in-memory JPA clone이 아니라 **outbound port용 test adapter**다
- fake는 port가 약속한 의미만 재현하고, ORM 메커니즘은 흉내 내지 않는다
- `save()` 이후/이전 상태를 분명히 하려면 snapshot 저장과 새 객체 재구성이 유용하다
- fake 설계가 지나치게 복잡하면 "테스트 더블이 약해서"가 아니라 "port가 persistence 세부를 담고 있어서"일 가능성이 크다

## 한 줄 정리

repository fake는 DB 없는 JPA 흉내가 아니라 outbound port 계약을 메모리에서 재현하는 test adapter여야 하고, 유스케이스 test는 그 계약만 의존해야 persistence 세부가 새지 않는다.
