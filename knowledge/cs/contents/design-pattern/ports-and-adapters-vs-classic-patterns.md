# Ports and Adapters vs GoF 패턴: 경계에서 책임을 자르는 법

> 한 줄 요약: Ports and Adapters는 아키텍처 경계의 규칙이고, GoF 어댑터는 클래스 수준 변환이다. 둘을 구분해야 코드 경계가 흐려지지 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Adapter (어댑터) 패턴](./adapter.md)
> - [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md)
> - [Hexagonal Ports: 유스케이스를 둘러싼 입출력 경계](./hexagonal-ports-pattern-language.md)
> - [Anti-Corruption Adapter Layering](./anti-corruption-adapter-layering.md)
> - [Adapter Chaining Smells](./adapter-chaining-smells.md)
> - [Composition over Inheritance](./composition-over-inheritance-practical.md)
> - [안티 패턴](./anti-pattern.md)

> retrieval-anchor-keywords: ports and adapters, hexagonal architecture, hexagonal vs adapter pattern, boundary architecture, clean architecture boundary, inbound port, outbound port, driving adapter, driven adapter, application service port, interface translation vs boundary architecture, anti-corruption boundary

---

## 핵심 개념

Ports and Adapters, 흔히 Hexagonal Architecture라고 부르는 스타일은 **도메인 코드를 외부 기술로부터 분리**하려는 아키텍처다.  
여기서 포트는 "도메인이 원하는 입력/출력 계약"이고, 어댑터는 그 계약을 구현하는 기술 구체체다.

GoF Adapter와 이름은 비슷하지만 역할은 다르다.

- GoF Adapter: 인터페이스가 맞지 않는 객체를 연결한다
- Port: 애플리케이션이 외부에 기대는 계약이다
- Adapter: 그 계약을 구현하는 인프라 코드다

### 질문 분기

- 메서드 시그니처 하나를 맞추거나 SDK wrapper가 필요하면 [Adapter (어댑터) 패턴](./adapter.md)이나 [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md) 범주다.
- inbound/outbound port, controller adapter, repository adapter처럼 경계와 의존성 방향이 핵심이면 이 문서와 [Hexagonal Ports](./hexagonal-ports-pattern-language.md)를 본다.
- port는 맞지만 adapter, translator, facade가 너무 많아 책임이 흐리면 [Adapter Chaining Smells](./adapter-chaining-smells.md)나 [Anti-Corruption Adapter Layering](./anti-corruption-adapter-layering.md)로 내려간다.

---

## 깊이 들어가기

### 1. 포트는 인터페이스, 어댑터는 구현이다

포트는 도메인 또는 애플리케이션 계층이 외부와 소통할 때 사용하는 계약이다.

- Inbound Port: 컨트롤러, 메시지 컨슈머, 스케줄러가 호출한다
- Outbound Port: 결제, 메일, 저장소 같은 외부 의존성을 호출한다

이 구분을 넣으면 프레임워크가 바뀌어도 핵심 유스케이스는 덜 흔들린다.

### 2. GoF Adapter와 헷갈리면 안 되는 이유

GoF Adapter는 단순히 "메서드 시그니처를 맞추는 변환기"에 가깝다.  
Ports and Adapters는 그보다 큰 범위에서 **의존성 방향을 뒤집는 규칙**이다.

| 구분 | GoF Adapter | Ports and Adapters |
|---|---|---|
| 범위 | 클래스/객체 수준 | 아키텍처 수준 |
| 목적 | 호환성 확보 | 경계 분리 |
| 중심 | 변환 | 의존성 역전 |

둘은 배타적이지 않다. Ports and Adapters 구조 안쪽의 boundary마다 GoF Adapter 하나가 놓일 수 있다. 혼동 포인트는 "adapter"라는 이름이 같다는 것뿐이고, 역할 층위는 다르다.

### 3. 패키지 경계가 설계의 절반이다

실전에서는 다음처럼 나뉜다.

- `application`: 유스케이스
- `domain`: 핵심 모델과 규칙
- `adapter.in`: 웹, 메시지, 배치 진입점
- `adapter.out`: DB, 외부 API, 메시징 구현

이렇게 나누면 "무엇이 정책이고 무엇이 기술인가"가 보인다.

---

## 실전 시나리오

### 시나리오 1: 주문 유스케이스

컨트롤러는 주문 생성 요청을 받고, 애플리케이션 서비스는 유스케이스를 실행하고, 결제 API와 저장소는 outbound adapter가 처리한다.

### 시나리오 2: 외부 결제 게이트웨이 교체

PG를 바꿔도 포트는 유지하고 어댑터만 바꾸면 된다.  
핵심 유스케이스가 PG SDK에 직접 의존하지 않기 때문이다.

### 시나리오 3: 메시지 컨슈머 추가

REST로 받든 Kafka로 받든, 같은 inbound port를 호출하면 된다.

---

## 코드로 보기

### Port

```java
public interface PlaceOrderUseCase {
    OrderId placeOrder(PlaceOrderCommand command);
}

public interface PaymentPort {
    PaymentResult pay(PaymentRequest request);
}
```

### Application Service

```java
@Service
public class PlaceOrderService implements PlaceOrderUseCase {
    private final PaymentPort paymentPort;
    private final OrderRepository orderRepository;

    public PlaceOrderService(PaymentPort paymentPort, OrderRepository orderRepository) {
        this.paymentPort = paymentPort;
        this.orderRepository = orderRepository;
    }

    @Override
    public OrderId placeOrder(PlaceOrderCommand command) {
        PaymentResult result = paymentPort.pay(new PaymentRequest(command.amount()));
        Order order = Order.place(command, result);
        return orderRepository.save(order).getId();
    }
}
```

### Driving Adapter

```java
@RestController
public class OrderController {
    private final PlaceOrderUseCase placeOrderUseCase;

    public OrderController(PlaceOrderUseCase placeOrderUseCase) {
        this.placeOrderUseCase = placeOrderUseCase;
    }

    @PostMapping("/orders")
    public OrderId place(@RequestBody PlaceOrderRequest request) {
        return placeOrderUseCase.placeOrder(request.toCommand());
    }
}
```

### Driven Adapter

```java
@Component
public class PgPaymentAdapter implements PaymentPort {
    private final ExternalPgClient client;

    public PgPaymentAdapter(ExternalPgClient client) {
        this.client = client;
    }

    @Override
    public PaymentResult pay(PaymentRequest request) {
        return client.requestPayment(request.amount(), request.orderId());
    }
}
```

어댑터는 기술 세부사항을 숨기고, 포트는 도메인 언어를 지킨다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 프레임워크 직결 | 빠르다 | 경계가 흐려진다 | 작은 실험 프로젝트 |
| Ports and Adapters | 교체가 쉽다 | 초기 구조가 무겁다 | 도메인 핵심이 오래 가야 할 때 |
| GoF Adapter만 사용 | 부분 통합에 좋다 | 아키텍처 경계는 못 잡는다 | 레거시 연결이 목적일 때 |

판단 기준은 다음과 같다.

- 기술 교체 가능성이 높으면 포트로 분리한다
- 단순한 API 호환 문제면 GoF Adapter면 충분하다
- 경계가 중요하면 도메인 객체가 프레임워크를 몰라야 한다

---

## 꼬리질문

> Q: Ports and Adapters를 쓰면 GoF Adapter가 필요 없나요?
> 의도: 아키텍처와 클래스 패턴을 같은 층위로 보지 않는지 확인한다.
> 핵심: 아니다. 포트는 경계 규칙이고, GoF Adapter는 그 경계 안에서의 변환 도구다.

> Q: 왜 컨트롤러가 도메인 로직을 직접 알면 안 되나요?
> 의도: 의존성 방향을 이해하는지 확인한다.
> 핵심: 프레임워크 변화가 도메인까지 번지기 때문이다.

> Q: 퍼사드와 포트는 어떻게 다른가요?
> 의도: 단순화와 경계의 차이를 구분하는지 확인한다.
> 핵심: 퍼사드는 사용성을 줄이고, 포트는 의존성 경계를 정의한다.

## 한 줄 정리

Ports and Adapters는 도메인과 기술의 경계를 고정하는 아키텍처이고, GoF Adapter는 그 경계 안팎의 인터페이스를 맞추는 도구다.
