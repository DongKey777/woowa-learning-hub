# Hexagonal Testing Seams Primer

> 한 줄 요약: Hexagonal Architecture에서 테스트 seam은 유스케이스를 빠르게 검증할 경계와, 어댑터를 실제 기술과 함께 검증할 경계를 분리해 주는 실전 규칙이다.

**난이도: 🟡 Intermediate**

입문 설명과 폴더 구조가 먼저 필요하다면 [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)부터 읽고, 이 문서는 그다음에 "그 경계를 테스트에서 어떻게 써먹는가"에 집중해서 보면 된다.
특히 controller/message handler 같은 inbound adapter에서 slice test와 full integration test를 어떻게 가를지 헷갈리면 [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)로 이어서 보면 된다.
controller, consumer, scheduled job를 서로 다른 테스트 포트폴리오로 비교하고 싶다면 [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)가 바로 다음 follow-up이다.

<details>
<summary>Table of Contents</summary>

- [왜 testing seam이 중요한가](#왜-testing-seam이-중요한가)
- [Hexagonal에서 seam은 어디에 생기나](#hexagonal에서-seam은-어디에-생기나)
- [유스케이스 unit test는 무엇을 검증하나](#유스케이스-unit-test는-무엇을-검증하나)
- [Fake outbound port로 unit test하기](#fake-outbound-port로-unit-test하기)
- [Fake와 Mock을 어떻게 나누나](#fake와-mock을-어떻게-나누나)
- [Adapter integration test는 언제 필요한가](#adapter-integration-test는-언제-필요한가)
- [최소 테스트 포트폴리오는 어떻게 잡나](#최소-테스트-포트폴리오는-어떻게-잡나)
- [자주 하는 오해](#자주-하는-오해)

</details>

> 관련 문서:
> - [Software Engineering README: Hexagonal Testing Seams Primer](./README.md#hexagonal-testing-seams-primer)
> - [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
> - [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)
> - [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)
> - [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md)
> - [Repository Fake Design Guide](./repository-fake-design-guide.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)

> retrieval-anchor-keywords:
> - hexagonal testing seam
> - hexagonal testing seams primer
> - ports and adapters testing
> - use case unit test
> - fake outbound port
> - repository fake
> - payment gateway fake
> - adapter integration test
> - repository adapter integration test
> - external api adapter test
> - hexagonal fake vs mock
> - inbound adapter slice test
> - controller slice vs integration
> - message handler slice test
> - inbound adapter testing matrix

## 왜 testing seam이 중요한가

Hexagonal Architecture를 배우면 보통 "의존성이 안쪽으로 향한다"까지는 이해한다.
실무에서 더 체감되는 장점은 그다음이다.

- 유스케이스는 바깥 기술 없이도 검증할 수 있다
- 바깥 어댑터는 기술 연결 책임만 따로 검증할 수 있다

즉 seam은 "테스트를 어디서 끊을지"를 알려 주는 경계다.
이 경계가 흐리면 유스케이스 테스트가 DB, HTTP, 메시지 브로커까지 끌고 들어와 느려지고, 반대로 어댑터 테스트가 없어 매핑 오류를 늦게 발견하게 된다.

## Hexagonal에서 seam은 어디에 생기나

핵심 seam은 보통 outbound port에 생긴다.

| 대상 | 주된 seam | 주로 쓰는 테스트 |
|---|---|---|
| 유스케이스 | outbound port를 fake/stub으로 대체 | unit test |
| outbound adapter | 실제 DB/HTTP SDK/브로커와 연결 | integration test |
| inbound adapter | 요청 바인딩, 검증, 직렬화 | slice test 또는 integration test |

이 표에서 중요한 점은 하나다.
유스케이스의 책임과 어댑터의 책임을 같은 테스트에서 한 번에 증명하려고 하지 않는 것이다.

- 유스케이스 test는 비즈니스 규칙을 빠르게 검증한다
- adapter test는 기술 연결과 매핑을 실제에 가깝게 검증한다

## 유스케이스 unit test는 무엇을 검증하나

유스케이스 unit test의 질문은 보통 아래에 가깝다.

- 주문 가능 조건을 맞게 검사하는가
- 할인/한도/상태 전이를 맞게 적용하는가
- 실패 조건에서 어떤 예외나 결과를 내보내는가
- outbound port를 어떤 입력으로 호출하는가

여기서 핵심은 **규칙과 흐름**이다.
JPA 매핑, HTTP status 해석, JSON 직렬화 같은 것은 유스케이스 unit test의 중심이 아니다.

예를 들어 주문 생성 유스케이스가 있다고 하자.

```java
public interface OrderRepository {
    void save(Order order);
}

public interface PaymentGateway {
    PaymentResult authorize(Money amount);
}

public class PlaceOrderService implements PlaceOrderUseCase {
    private final OrderRepository orderRepository;
    private final PaymentGateway paymentGateway;

    public PlaceOrderService(OrderRepository orderRepository, PaymentGateway paymentGateway) {
        this.orderRepository = orderRepository;
        this.paymentGateway = paymentGateway;
    }

    @Override
    public OrderId place(PlaceOrderCommand command) {
        PaymentResult payment = paymentGateway.authorize(command.totalAmount());
        if (!payment.isSuccess()) {
            throw new PaymentFailedException();
        }

        Order order = Order.create(command.customerId(), command.items());
        orderRepository.save(order);
        return order.id();
    }
}
```

이 서비스의 unit test는 "결제가 실패하면 저장하지 않는가", "성공하면 주문을 저장하는가"를 빠르게 보는 쪽이 맞다.

## Fake outbound port로 unit test하기

Hexagonal 유스케이스 test에서 fake가 자주 잘 맞는 이유는 상태를 직접 확인하기 쉽기 때문이다.

```java
class FakeOrderRepository implements OrderRepository {
    private final List<Order> saved = new ArrayList<>();

    @Override
    public void save(Order order) {
        saved.add(order);
    }

    List<Order> savedOrders() {
        return saved;
    }
}

class FakePaymentGateway implements PaymentGateway {
    private PaymentResult nextResult = PaymentResult.success();

    void willFail() {
        this.nextResult = PaymentResult.failure("DECLINED");
    }

    @Override
    public PaymentResult authorize(Money amount) {
        return nextResult;
    }
}
```

```java
@Test
void saves_order_when_payment_succeeds() {
    FakeOrderRepository orderRepository = new FakeOrderRepository();
    FakePaymentGateway paymentGateway = new FakePaymentGateway();
    PlaceOrderService service = new PlaceOrderService(orderRepository, paymentGateway);

    OrderId orderId = service.place(new PlaceOrderCommand(customerId, items));

    assertThat(orderId).isNotNull();
    assertThat(orderRepository.savedOrders()).hasSize(1);
}

@Test
void does_not_save_order_when_payment_fails() {
    FakeOrderRepository orderRepository = new FakeOrderRepository();
    FakePaymentGateway paymentGateway = new FakePaymentGateway();
    paymentGateway.willFail();
    PlaceOrderService service = new PlaceOrderService(orderRepository, paymentGateway);

    assertThatThrownBy(() -> service.place(new PlaceOrderCommand(customerId, items)))
        .isInstanceOf(PaymentFailedException.class);
    assertThat(orderRepository.savedOrders()).isEmpty();
}
```

이 테스트가 주는 장점:

- DB 없이도 빠르다
- 네트워크 없이도 안정적이다
- 저장 여부나 상태 전이를 결과 중심으로 읽을 수 있다

즉 fake는 "바깥 기술을 흉내 내는 작은 대역"이 아니라, **유스케이스가 기대하는 port 계약을 메모리 안에서 재현하는 도구**다.

## Fake와 Mock을 어떻게 나누나

Hexagonal 문맥에서는 outbound port에 fake를 먼저 검토하는 편이 보통 낫다.

| 선택 | 잘 맞는 상황 | 주의점 |
|---|---|---|
| Fake | 저장 결과, 누적 상태, 간단한 조회 조건을 보고 싶을 때 | 실제 기술 특성까지 증명하지는 못한다 |
| Mock | "정확히 이 호출이 일어나야 한다"가 핵심일 때 | 호출 순서에 테스트가 과도하게 묶일 수 있다 |
| Stub | 단순히 고정 응답만 있으면 될 때 | 상호작용이나 상태 변화는 약하다 |

실무 규칙으로는 이렇게 잡으면 충분하다.

- 유스케이스의 성공/실패 분기와 상태 검증이 목적이면 fake를 우선한다
- 정말로 상호작용 자체가 요구사항일 때만 mock/spy를 쓴다

예를 들어 "결제 실패 시 저장하지 않는다"는 fake로 읽기 쉽다.
반면 "정상 커밋 이후에만 이벤트를 publish해야 한다" 같은 것은 상호작용 타이밍 자체가 중요해 mock이나 더 상위 통합 검증이 필요할 수 있다.

## Adapter integration test는 언제 필요한가

유스케이스 unit test가 모두 초록이어도, 어댑터는 여전히 별도 위험을 가진다.
아래 책임이 어댑터 안에 있으면 integration test가 필요하다.

### 1. 매핑이 복잡할 때

- JPA entity ↔ domain 변환
- 외부 API DTO ↔ 내부 command/result 변환
- 메시지 payload ↔ 도메인 이벤트 변환

이 영역은 fake로는 "진짜 매핑이 맞는지"를 보장할 수 없다.

### 2. 기술 규칙을 타야 할 때

- 실제 query가 조건을 맞게 타는가
- unique constraint, transaction, lazy loading이 기대대로 동작하는가
- HTTP status, timeout, retry 규칙을 어댑터가 맞게 해석하는가
- 메시지 header, ack, serializer 설정이 실제 런타임과 맞는가

이건 port 인터페이스만 봐서는 증명되지 않는다.

### 3. 프레임워크 어노테이션/설정에 의존할 때

- `@Transactional`
- `@RestController`
- `@RequestBody` 바인딩
- `@Entity` 매핑

프레임워크가 실제로 개입하는 순간, unit test만으로는 핵심 리스크를 놓칠 수 있다.

### 4. 외부 계약이 바뀔 가능성이 클 때

특히 HTTP adapter, 메시지 adapter는 상대 시스템과의 계약이 중요하다.
이 경우에는 integration test나 contract test가 어댑터를 직접 덮어야 한다.

한 문장으로 정리하면:
**어댑터에 "기술과의 실제 접점"이 있으면 integration test로 덮고, 유스케이스에 "비즈니스 결정"이 있으면 unit test로 덮는다.**

## 최소 테스트 포트폴리오는 어떻게 잡나

처음부터 모든 어댑터를 무겁게 붙일 필요는 없다.
대신 아래 조합이 작고 강하다.

1. 유스케이스 unit test
   - outbound port를 fake로 대체
   - 규칙 분기와 상태 전이를 빠르게 검증
2. 핵심 outbound adapter integration test
   - repository query/매핑
   - external API 변환/에러 해석
   - message serialization/consumer binding
3. 최소 핵심 시나리오 E2E
   - 정말 끊기면 안 되는 사용자 흐름만 남긴다

예를 들어 주문 도메인이라면:

- `PlaceOrderService`는 fake `OrderRepository`, fake `PaymentGateway`로 unit test
- `JpaOrderRepositoryAdapter`는 실제 DB와 함께 integration test
- `PgPaymentGatewayAdapter`는 stub server나 sandbox로 contract/integration test

중요한 것은 같은 사실을 세 층에서 반복해 쓰는 것이 아니라, **각 층의 실패 모드를 다르게 덮는 것**이다.

## 자주 하는 오해

- 유스케이스 test도 실제 DB를 붙여야 안심된다고 생각한다. 그러면 피드백이 느려지고 실패 원인이 흐려진다.
- fake를 쓰면 현실성이 없다고 본다. fake는 현실 전체를 재현하는 도구가 아니라 port 계약을 빠르게 검증하는 도구다.
- unit test가 있으니 adapter test는 필요 없다고 본다. 매핑, 직렬화, 프레임워크 설정 오류는 여기서 빠진다.
- adapter integration test에서 비즈니스 규칙까지 다시 전부 검증한다. 그러면 중복이 커지고 실패 분석이 어려워진다.

## 한 줄 정리

Hexagonal testing seam의 핵심은 유스케이스는 fake outbound port로 빠르게 검증하고, 실제 기술 접점이 있는 adapter는 integration test로 따로 덮어 각 층의 실패 모드를 분리하는 것이다.
