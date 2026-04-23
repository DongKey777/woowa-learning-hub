# Ports and Adapters Beginner Primer

> 한 줄 요약: Ports and Adapters는 도메인과 유스케이스를 중심에 두고, 웹/DB/외부 API 같은 입출력 세부를 바깥 어댑터로 분리하는 초급용 구조 규칙이다.

**난이도: 🟢 Beginner**

<details>
<summary>Table of Contents</summary>

- [왜 이름이 어렵게 느껴지는가](#왜-이름이-어렵게-느껴지는가)
- [먼저 한 문장으로 이해하기](#먼저-한-문장으로-이해하기)
- [Port는 무엇인가](#port는-무엇인가)
- [Adapter는 무엇인가](#adapter는-무엇인가)
- [Inbound와 Outbound를 어떻게 구분하나](#inbound와-outbound를-어떻게-구분하나)
- [가장 작은 폴더 구조 예시](#가장-작은-폴더-구조-예시)
- [모듈별로 배치하면 어떻게 보이나](#모듈별로-배치하면-어떻게-보이나)
- [Clean Architecture와는 어떤 관계인가](#clean-architecture와는-어떤-관계인가)
- [처음 적용할 때 최소 규칙](#처음-적용할-때-최소-규칙)
- [자주 하는 오해](#자주-하는-오해)

</details>

> 관련 문서:
> - [Software Engineering README: Ports and Adapters Beginner Primer](./README.md#ports-and-adapters-beginner-primer)
> - [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md)
> - [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
> - [Message-Driven Adapter Example](./message-driven-adapter-example.md)
> - [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [Design Pattern: Ports and Adapters vs GoF 패턴](../design-pattern/ports-and-adapters-vs-classic-patterns.md)
> - [Design Pattern: Hexagonal Ports: 유스케이스를 둘러싼 입출력 경계](../design-pattern/hexagonal-ports-pattern-language.md)
> - [System Design: Job Queue 설계](../system-design/job-queue-design.md)
> - [System Design: Event Bus Control Plane 설계](../system-design/event-bus-control-plane-design.md)
>
> retrieval-anchor-keywords: ports and adapters beginner, hexagonal architecture beginner, hexagonal primer, ports and adapters primer, hexagonal folder layout, inbound port, outbound port, primary adapter, secondary adapter, use case port, controller adapter, message consumer adapter, scheduled job adapter, repository adapter, clean architecture relation, hexagonal vs clean architecture, hexagonal testing seam, fake outbound port, ports and adapters vs gof pattern, hexagonal ports pattern language, job queue handoff, event bus control plane handoff, runtime topology bridge

입문 설명이 끝난 뒤 "adapter"라는 이름이 GoF 어댑터와 어떻게 다른지 헷갈리면 [Design Pattern: Ports and Adapters vs GoF 패턴](../design-pattern/ports-and-adapters-vs-classic-patterns.md), [Design Pattern: Hexagonal Ports: 유스케이스를 둘러싼 입출력 경계](../design-pattern/hexagonal-ports-pattern-language.md)로 이어서 보면 된다.
같은 port/adaptor 구분이 queue, topic, consumer 운영 경계까지 커지는 순간은 [System Design: Job Queue 설계](../system-design/job-queue-design.md), [System Design: Event Bus Control Plane 설계](../system-design/event-bus-control-plane-design.md)가 다음 handoff다.

## 왜 이름이 어렵게 느껴지는가

처음 들으면 이름이 세 겹으로 겹친다.

- Hexagonal Architecture
- Ports and Adapters
- Primary/Secondary Adapter 혹은 Inbound/Outbound Adapter

하지만 초심자 기준으로는 이렇게 단순화해도 충분하다.

- `Hexagonal Architecture`는 그림 이름에 가깝다
- `Ports and Adapters`는 코드에 적용하는 설명 이름에 가깝다

즉 입문 단계에서는 둘을 거의 같은 문맥으로 이해해도 된다.

## 먼저 한 문장으로 이해하기

핵심은 하나다.

- 안쪽 코드는 "무엇이 필요하다"만 말한다
- 바깥 코드는 "그걸 HTTP, DB, 외부 API로 어떻게 연결할지"를 맡는다

그래서 도메인과 유스케이스는 웹 프레임워크나 DB 라이브러리 이름을 덜 알게 된다.

## Port는 무엇인가

Port는 **안쪽 코드가 대화하는 창구**다.

초심자에게는 두 종류만 먼저 잡으면 된다.

- Inbound port: 바깥에서 안쪽 유스케이스를 호출할 때 쓰는 인터페이스
- Outbound port: 안쪽에서 바깥 자원이 필요할 때 쓰는 인터페이스

예를 들어 주문 생성 기능이면:

```java
public interface PlaceOrderUseCase {
    OrderId place(PlaceOrderCommand command);
}

public interface PaymentGateway {
    PaymentResult authorize(PaymentRequest request);
}
```

- `PlaceOrderUseCase`는 안으로 들어오는 입구라서 inbound port다
- `PaymentGateway`는 안쪽이 바깥 결제 시스템을 필요로 하므로 outbound port다

## Adapter는 무엇인가

Adapter는 **Port에 맞춰 실제 입출력을 연결하는 바깥 코드**다.

- HTTP 요청을 받아 `PlaceOrderUseCase`를 호출하면 inbound adapter다
- PG SDK를 사용해 `PaymentGateway`를 구현하면 outbound adapter다

```java
@RestController
class OrderController {
    private final PlaceOrderUseCase useCase;

    @PostMapping("/orders")
    OrderResponse place(@RequestBody PlaceOrderRequest request) {
        return OrderResponse.from(useCase.place(request.toCommand()));
    }
}

class PgPaymentGatewayAdapter implements PaymentGateway {
    @Override
    public PaymentResult authorize(PaymentRequest request) {
        // 외부 PG SDK 호출
        return PaymentResult.success();
    }
}
```

중요한 점은 컨트롤러와 PG 연동 코드가 모두 바깥에 있다는 것이다.
안쪽 유스케이스는 HTTP나 SDK를 직접 모르고 Port만 본다.

## Inbound와 Outbound를 어떻게 구분하나

이 구분은 "누가 누구를 먼저 호출하느냐"로 보면 쉽다.

| 구분 | 역할 | 예시 |
|---|---|---|
| Inbound port | 시스템이 제공하는 기능의 입구 | `PlaceOrderUseCase`, `CancelOrderUseCase` |
| Inbound adapter | 바깥 요청을 포트 호출로 번역 | Controller, CLI handler, Message consumer |
| Outbound port | 시스템이 바깥에 요청해야 하는 기능 | `PaymentGateway`, `OrderRepository`, `ClockHolder` |
| Outbound adapter | 포트 구현을 실제 기술로 연결 | JPA repository adapter, Redis adapter, PG adapter |

초심자는 `Repository`도 outbound port라는 점에서 많이 정리된다.
도메인이나 애플리케이션이 저장이 필요하다고 말하고, 실제 DB 연동은 바깥 구현이 맡는다고 보면 된다.
HTTP controller, message consumer, scheduled job를 같은 inbound adapter 축에서 비교하고 싶다면 [Message-Driven Adapter Example](./message-driven-adapter-example.md)을 이어서 보면 된다.

## 가장 작은 폴더 구조 예시

가장 단순한 형태는 아래처럼 볼 수 있다.

```text
src/main/java/com/example/order/
  application/
    PlaceOrderUseCase.java
    PlaceOrderService.java
    port/
      out/
        PaymentGateway.java
        OrderRepository.java
  domain/
    Order.java
    OrderId.java
  adapters/
    in/
      web/
        OrderController.java
    out/
      persistence/
        JpaOrderRepositoryAdapter.java
      payment/
        PgPaymentGatewayAdapter.java
```

이 구조를 읽는 법:

- `application/PlaceOrderUseCase.java`: inbound port
- `application/PlaceOrderService.java`: 유스케이스 구현
- `application/port/out/*`: outbound port
- `adapters/in/*`: 웹, CLI, 메시지 소비 같은 입력 어댑터
- `adapters/out/*`: DB, 외부 API, 캐시 같은 출력 어댑터

폴더 이름은 팀마다 다를 수 있다.
중요한 것은 이름보다 **의존 방향**이다.

## 모듈별로 배치하면 어떻게 보이나

모듈러 모놀리스나 기능 중심 구조에서는 이렇게 배치할 수도 있다.

```text
src/main/java/com/example/
  order/
    domain/
      Order.java
    application/
      PlaceOrderUseCase.java
      PlaceOrderService.java
      port/
        out/
          OrderRepository.java
    adapters/
      in/
        web/
          OrderController.java
      out/
        persistence/
          JpaOrderRepositoryAdapter.java
  payment/
    domain/
    application/
    adapters/
```

이렇게 두면:

- 기능 경계는 `order`, `payment` 모듈이 잡고
- 각 모듈 안에서는 ports/adapters 구조를 유지할 수 있다

즉 ports and adapters는 "프로젝트 전체를 무조건 한 모양으로 배치하는 규칙"이라기보다, **각 기능 경계 안에서 바깥 의존을 다루는 방법**에 가깝다.

## Clean Architecture와는 어떤 관계인가

둘은 적대 관계가 아니라 거의 같은 방향을 본다.

| 질문 | Clean Architecture | Ports and Adapters |
|---|---|---|
| 무엇을 보호하나 | 도메인과 유스케이스 | 도메인과 유스케이스 |
| 핵심 규칙은 무엇인가 | 의존성은 안쪽으로 향해야 한다 | 바깥 기술은 포트를 통해서만 안쪽과 연결된다 |
| 바깥 기술은 어디에 두나 | 외곽 레이어 | 어댑터 |
| 초심자에게 보이는 실체는 무엇인가 | 레이어/원형 다이어그램 | 폴더 구조와 인터페이스 |

실무 감각으로 정리하면:

- Clean Architecture는 **의존성 규칙을 설명하는 말**에 가깝다
- Ports and Adapters는 그 규칙을 **입출력 경계에서 코드로 보이게 만드는 방법**에 가깝다

그래서 레이어드 구조를 쓰는 팀도 일부 경계에서는 ports/adapters를 함께 사용한다.
테스트 경계까지 이어서 보고 싶다면 [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)를 다음 문서로 보면 좋다.
이 문서가 초급용이고, consistency boundary나 DDD 고급 주제까지 같이 보고 싶다면 [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)를 이어서 보면 된다.

## 처음 적용할 때 최소 규칙

처음부터 모든 것을 추상화할 필요는 없다.
대신 아래 다섯 가지는 지키는 편이 좋다.

1. 유스케이스 진입점은 `UseCase` 인터페이스나 명확한 애플리케이션 서비스로 둔다.
2. 컨트롤러, CLI, 메시지 소비자는 도메인 객체를 직접 조립하지 말고 유스케이스를 호출한다.
3. DB, 외부 API, 시간, 파일 같은 바깥 의존은 outbound port 뒤로 숨긴다.
4. 어댑터 안에서 DTO, Entity, SDK 모델 변환을 끝내고 안쪽으로 새지 않게 한다.
5. 작은 CRUD에서는 모든 저장소를 무리하게 분리하지 말고, 변경 압력이 큰 지점부터 port를 도입한다.

핵심은 "모든 곳에 패턴을 칠하는 것"이 아니라 **바뀔 가능성이 높은 경계부터 보호하는 것**이다.

## 자주 하는 오해

- `ports and adapters = 폴더 이름을 adapters로 쓰는 것`이라고 오해한다. 실제 핵심은 포트와 의존 방향이다.
- 모든 클래스에 인터페이스를 만들어야 한다고 생각한다. 보통은 유스케이스 입구와 바깥 의존 지점만 먼저 분리해도 충분하다.
- 컨트롤러가 곧 application이라고 생각한다. 컨트롤러는 보통 inbound adapter다.
- JPA repository 구현체를 domain 안에 두기도 한다. 저장 구현은 대체로 outbound adapter 쪽이 맞다.
- Hexagonal Architecture를 배우자마자 bounded context, saga, eventual consistency까지 한 번에 넣으려 한다. 그건 다음 단계다.

한 문장으로 다시 정리하면, ports and adapters는 **안쪽 코드를 바깥 기술로부터 보호하기 위해 입구와 출구를 명확히 나누는 구조**다.
