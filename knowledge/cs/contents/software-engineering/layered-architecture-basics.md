# 계층형 아키텍처 기초 (Layered Architecture Basics)

> 한 줄 요약: 계층형 아키텍처는 코드를 역할별로 쌓아 올려 각 계층이 바로 아래 계층에만 의존하도록 구조를 나누는 가장 흔한 설계 패턴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)
- [Service 계층 기초](./service-layer-basics.md)
- [Repository, DAO, Entity](./repository-dao-entity.md)
- [software-engineering 카테고리 인덱스](./README.md)
- [Spring Bean DI Basics](../spring/spring-bean-di-basics.md)

retrieval-anchor-keywords: layered architecture basics, 계층형 아키텍처 입문, 레이어드 아키텍처 기초, controller service repository 구조, presentation layer, business layer, persistence layer, 계층 분리 이유, 3 tier architecture beginner, 레이어 의존 방향, 계층 왜 나누나요, beginner layered architecture

## 핵심 개념

계층형 아키텍처(Layered Architecture)는 애플리케이션 코드를 역할별로 수평 계층으로 나눠 상위 계층이 하위 계층에만 의존하도록 강제한다.

스프링 기반 웹 서버에서 가장 흔히 보이는 3계층 구조:

```
[Presentation]  Controller (HTTP 요청/응답)
      ↓
[Application]   Service (비즈니스 로직)
      ↓
[Persistence]   Repository / DAO (DB 접근)
```

화살표 방향이 곧 의존 방향이다. Controller는 Service를 호출하고, Service는 Repository를 호출한다. Repository가 Controller를 직접 호출하는 역방향은 허용하지 않는다.

## 한눈에 보기

| 계층 | 주요 책임 | 예시 클래스 |
|---|---|---|
| Presentation | HTTP 요청 수신, 응답 직렬화 | `OrderController` |
| Application | 비즈니스 규칙, 트랜잭션 조율 | `OrderService` |
| Persistence | DB 쿼리, 엔티티 매핑 | `OrderRepository` |
| Domain | 핵심 도메인 객체, 비즈니스 규칙 표현 | `Order`, `OrderItem` |

Domain 계층은 선택적으로 추가하거나 Application 계층 안에 두기도 한다.

## 상세 분해

**왜 계층을 나누는가**

계층을 나누지 않으면 Controller 안에 SQL이 섞이고, 같은 비즈니스 로직이 여러 Controller에 복사된다. 계층을 분리하면 변경이 해당 계층에만 머문다. DB를 JPA에서 MyBatis로 바꿔도 Persistence 계층만 수정하면 된다.

**계층 간 데이터 전달**

계층 경계를 넘을 때는 DTO(Data Transfer Object)를 사용한다. Controller가 받은 JSON을 RequestDTO로 변환하고, Service는 그 DTO를 처리해 도메인 객체나 ResponseDTO를 반환한다. DB에서 꺼낸 JPA 엔티티를 Controller까지 그대로 노출하면 엔티티가 HTTP 응답 형태에 종속된다.

**상향 의존 금지**

Persistence 계층이 Service 계층의 클래스를 직접 import하면 하위 계층이 상위 계층을 알게 된다. 이 규칙이 깨지면 순환 의존이 생기고 계층 경계가 무너진다.

## 흔한 오해와 함정

- "Controller에서 Repository를 직접 호출해도 된다"는 생각이 있다. 규모가 작으면 동작하지만, 비즈니스 로직이 Controller에 쌓이면 분리 비용이 커진다.
- "Service는 무조건 얇아야 한다"고 오해하기도 한다. Service가 비즈니스 로직의 중심이므로 도메인 규칙은 Service나 도메인 객체에 있어야 한다. Controller가 로직을 가지면 안 된다.
- "3계층 구조가 유일한 정답"이라는 오해도 있다. 계층 수는 요구사항에 따라 달라진다. 중요한 건 의존 방향이 단방향이어야 한다는 원칙이다.

## 실무에서 쓰는 모습

`POST /orders` 요청이 들어오면 `OrderController`가 받아 `OrderRequest` DTO로 역직렬화하고 `OrderService.createOrder(request)`를 호출한다. Service는 비즈니스 규칙을 검증한 뒤 `orderRepository.save(order)`로 저장하고 `OrderResponse`를 반환한다. Controller는 그 응답을 HTTP 200으로 내보낸다.

이 흐름에서 각 계층은 자기 역할만 한다.

## 더 깊이 가려면

- [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md) — 계층형과 클린 아키텍처의 트레이드오프
- [Repository, DAO, Entity](./repository-dao-entity.md) — Persistence 계층 설계 세부 사항

## 면접/시니어 질문 미리보기

- "계층형 아키텍처의 단점은?" — 하위 계층을 거치지 않는 단순 조회도 모든 계층을 통과해야 하는 불필요한 우회가 생길 수 있다. 또한 계층이 많아지면 결합이 수직으로 전파된다.
- "JPA 엔티티를 Controller에서 직접 반환하면 어떤 문제가 생기나요?" — 엔티티의 필드 변경이 HTTP 응답 스펙에 직접 영향을 주고, 지연 로딩 예외가 직렬화 시점에 발생할 수 있다.
- "Service에 비즈니스 로직이 없고 Repository만 호출한다면?" — 이를 빈혈 도메인 모델(Anemic Domain Model)이라 한다. 로직이 분산돼 응집도가 낮아진다는 신호다.

## 한 줄 정리

계층형 아키텍처는 Controller → Service → Repository의 단방향 의존 방향을 지켜 변경을 해당 계층에 가두는 구조다.
