# Hexagonal Ports: 유스케이스를 둘러싼 입출력 경계

> 한 줄 요약: Hexagonal ports는 애플리케이션이 외부 기술에 의존하지 않도록 입력과 출력 계약을 분리하는 패턴 언어다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [Adapter (어댑터) 패턴](./adapter.md)
> - [Anti-Corruption Adapter Layering](./anti-corruption-adapter-layering.md)
> - [Facade as Anti-Corruption Seam](./facade-anti-corruption-seam.md)
> - [Bridge Pattern: 저장소와 제공자를 분리하는 추상화](./bridge-storage-provider-abstractions.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)

> retrieval-anchor-keywords: hexagonal architecture, ports and adapters, ports-and-adapters architecture, hexagonal ports, hexagonal boundary, inbound port, outbound port, inbound adapter, outbound adapter, driving adapter, driven adapter, use case contract, dependency inversion boundary, application core boundary, boundary architecture, anti corruption layer boundary, classic adapter vs ports and adapters

---

## 핵심 개념

Hexagonal architecture의 port는 **애플리케이션이 외부와 소통하는 계약**이다.  
이 문서는 그중에서도 port 자체를 패턴 언어처럼 읽는 데 집중한다.

- inbound port: 외부가 유스케이스를 호출하는 계약
- outbound port: 애플리케이션이 외부에 요구하는 계약

핵심은 프레임워크가 아니라 **행위 경계**다.

여기서 `adapter`는 `classic GoF adapter pattern`의 번역기 역할과 같은 말이 아니다. 이 문서의 관심사는 `port`, `inbound/outbound adapter`, `use case boundary`처럼 **아키텍처 경계**를 어떻게 자르는가다.

### 질문 분기

- `hexagonal architecture`, `ports and adapters`, `ports-and-adapters architecture`, `inbound/outbound adapter`, `application core boundary`, `boundary architecture`처럼 아키텍처 경계를 먼저 구분하고 싶으면 이 문서에서 시작한다.
- `adapter pattern`, `classic adapter`, `GoF adapter`, `메서드 시그니처 번역`, `SDK wrapper`, `target/adaptee`처럼 객체 간 인터페이스 번역이 핵심이면 [Adapter (어댑터) 패턴](./adapter.md), [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md)로 먼저 간다.
- `ACL`, `anti corruption layer`, `boundary translation`, `translator layering`처럼 외부 모델 번역층이 핵심이면 [Anti-Corruption Adapter Layering](./anti-corruption-adapter-layering.md)으로 바로 이어진다.
- `facade vs adapter vs proxy`처럼 classic wrapper 비교가 목적이면 [Adapter (어댑터) 패턴](./adapter.md), [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md)를 그다음에 본다.

## 깊이 들어가기

### 1. Port는 기술이 아니라 의도다

Port는 "어떤 프레임워크를 쓰는가"가 아니라 "무슨 일을 해야 하는가"를 선언한다.

- 주문을 접수한다
- 결제를 요청한다
- 메일을 보낸다
- 배송을 생성한다

이름이 기술적이면 금방 흐려진다.

### 2. inbound와 outbound는 방향이 다르다

Inbound Port는 컨트롤러, 메시지 소비자, 스케줄러가 호출한다.  
Outbound Port는 애플리케이션이 DB, PG, 메일 서버 같은 외부를 호출할 때 쓴다.

### 3. port가 많아지면 boundary가 드러난다

유스케이스가 잘 분리되어 있으면 port 이름만 봐도 시스템 경계가 보인다.

- `PlaceOrderUseCase`
- `CancelOrderUseCase`
- `PaymentPort`
- `InventoryPort`

---

## 실전 시나리오

### 시나리오 1: 웹과 메시지 공용 유스케이스

HTTP와 Kafka가 같은 inbound port를 호출할 수 있다.

### 시나리오 2: 외부 시스템 교체

PG나 메일 공급자를 바꿔도 outbound port 구현만 바꾸면 된다.

### 시나리오 3: 테스트

port를 mock으로 바꾸면 유스케이스를 프레임워크 없이 테스트할 수 있다.

---

## 코드로 보기

### Inbound Port

```java
public interface PlaceOrderUseCase {
    OrderId placeOrder(PlaceOrderCommand command);
}
```

### Outbound Port

```java
public interface PaymentPort {
    PaymentResult pay(PaymentRequest request);
}
```

### Use Case Service

```java
@Service
public class PlaceOrderService implements PlaceOrderUseCase {
    private final PaymentPort paymentPort;

    @Override
    public OrderId placeOrder(PlaceOrderCommand command) {
        paymentPort.pay(new PaymentRequest(command.amount()));
        return OrderId.newId();
    }
}
```

### Adapter가 port를 구현

```java
@Component
public class PgPaymentAdapter implements PaymentPort {
    @Override
    public PaymentResult pay(PaymentRequest request) {
        return PaymentResult.success();
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Framework controller 직접 호출 | 빨리 만든다 | 경계가 흐려진다 | 작은 프로토타입 |
| Hexagonal ports | 경계가 선명하다 | 초기 구조가 늘어난다 | 유스케이스가 오래 갈 때 |
| 단순 service interface | 가볍다 | inbound/outbound 구분이 약하다 | 경계가 작을 때 |

판단 기준은 다음과 같다.

- 외부 기술이 자주 바뀌면 port를 둔다
- 유스케이스가 프레임워크와 분리돼야 하면 port를 둔다
- port 이름은 기술이 아니라 의도를 드러내야 한다

---

## 꼬리질문

> Q: hexagonal ports와 GoF Adapter의 차이는 무엇인가요?
> 의도: 아키텍처 경계와 객체 호환을 구분하는지 확인한다.
> 핵심: port는 경계 계약이고 adapter는 그 구현이다.

> Q: inbound와 outbound를 왜 나누나요?
> 의도: 의존성 방향을 이해하는지 확인한다.
> 핵심: 호출 방향과 책임이 다르기 때문이다.

> Q: port 이름은 왜 중요한가요?
> 의도: 기술보다 의도를 먼저 보는지 확인한다.
> 핵심: 시스템 경계와 유스케이스 의도가 드러난다.

## 한 줄 정리

Hexagonal ports는 유스케이스를 둘러싼 입출력 계약을 분리해, 프레임워크 변화가 도메인에 번지지 않게 한다.
