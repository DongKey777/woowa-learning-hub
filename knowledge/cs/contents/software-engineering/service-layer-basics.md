# Service 계층 기초 (Service Layer Basics)

> 한 줄 요약: Service 계층은 여러 도메인 객체와 저장소를 조합해 하나의 유스케이스를 완성하는 곳이며, 비즈니스 규칙이 Controller나 Repository로 새지 않도록 막는 경계선이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md)
- [API 설계와 예외 처리](./api-design-error-handling.md)
- [Spring IoC 컨테이너와 DI](../spring/ioc-di-container.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: service layer basics, 서비스 계층 입문, service class 역할, 서비스 레이어 뭐하는 곳, controller vs service 차이, service 비즈니스 로직, service god class, 서비스 클래스 너무 커져요, application service, domain service 차이, 서비스 레이어 입문, beginner service layer

## 핵심 개념

Service 계층은 Layered Architecture에서 Controller(입력층)와 Repository(저장층) 사이에 위치한다.

역할을 한 줄로 정리하면: **"무엇을 해야 하는가(유스케이스)"를 결정하는 곳**이다.

- Controller는 HTTP 요청을 받아 Service를 호출하고, 응답을 반환하는 역할이다.
- Repository는 데이터를 읽고 쓰는 역할이다.
- Service는 그 사이에서 어떤 순서로, 어떤 규칙을 지키며 도메인 객체와 저장소를 조합할지 결정한다.

입문자가 헷갈리는 지점은 "어떤 코드가 Service에 있어야 하고, 어떤 코드가 Domain에 있어야 하는가"다.

## 한눈에 보기

Service 계층은 Controller(입력)와 Repository(저장) 사이에서 유스케이스 흐름을 조율한다. 의존 방향은 위에서 아래로만 흐른다.

```
HTTP 요청
    │
    ▼
Controller  ← 입력 변환, 유효성 검사, 응답 형식 결정
    │
    ▼
Service     ← 유스케이스 흐름 제어, 트랜잭션 경계, 도메인 조합
    │
    ▼
Domain      ← 핵심 비즈니스 규칙, 불변식
    │
    ▼
Repository  ← 저장, 조회
```

각 계층의 책임 범위를 명확히 나누는 것이 핵심이다. 아래 표는 계층별로 해야 할 일과 하면 안 되는 일을 정리한 것이다.

| 계층 | 해야 할 일 | 하면 안 되는 일 |
|---|---|---|
| Controller | 요청 매핑, DTO 변환 | 비즈니스 규칙 결정 |
| Service | 유스케이스 조합, 트랜잭션 | HTTP, 저장 기술 세부 |
| Repository | 저장/조회 | 비즈니스 조건 판단 |

경계를 지키지 않으면 비즈니스 로직이 Controller로 새거나, 저장 기술이 Service에 노출된다.

## 상세 분해

**Service가 담당하는 것**

- 여러 도메인 객체를 조합해 하나의 기능 흐름을 완성한다
- 트랜잭션 경계를 정한다 (`@Transactional`)
- 인프라 예외를 비즈니스 예외로 변환하거나 적절히 처리한다
- 여러 Repository, 외부 서비스 호출 순서를 결정한다

**Service가 담당하지 않는 것**

- HTTP 상태 코드, 헤더, 쿠키 — 이건 Controller가 결정
- SQL 문 작성, ORM 세부 — 이건 Repository가 담당
- 도메인 불변식 검증 — 이건 Domain 객체 안에 두는 것이 좋다

**Application Service vs Domain Service**

- Application Service: 유스케이스 흐름 조합. `OrderApplicationService`.
- Domain Service: 여러 도메인 객체가 협력해야 하는 도메인 규칙. `DiscountCalculator`.

입문 단계에서는 구분이 불명확해도 괜찮다. "비즈니스 규칙이 도메인 객체 하나에 들어가지 않을 때"를 도메인 서비스로 분리한다는 감각을 잡으면 충분하다.

## 흔한 오해와 함정

- Service에 모든 로직을 넣다 보면 God Class가 된다. 도메인 객체가 스스로 처리할 수 있는 규칙은 도메인 안에 두는 편이 좋다.
- Controller에서 `if` 분기로 비즈니스 로직을 처리하면, 같은 로직을 CLI나 배치에서 쓸 때 중복이 생긴다. Service가 중심이 되어야 재사용이 가능하다.
- Repository를 Service 없이 Controller에서 직접 호출하면, 트랜잭션 경계가 흐릿해지고 비즈니스 규칙이 Controller에 흩어진다.

## 실무에서 쓰는 모습

주문 생성 유스케이스를 예로 들면:

1. Controller가 `CreateOrderRequest`를 받아 `CreateOrderCommand`로 변환해 Service를 호출한다.
2. Service는 재고 확인(`InventoryService`), 주문 생성(`Order.create()`), 저장(`OrderRepository.save()`)을 순서대로 수행하고 트랜잭션을 관리한다.
3. 성공 시 `OrderId`를 반환하면 Controller가 `201 Created` 응답을 만든다.

이 흐름에서 Controller는 HTTP 세부를, Service는 유스케이스 순서를, Domain은 규칙을 각자 책임진다.

## 더 깊이 가려면

- [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md) — 계층 전체 구조와 의존 방향
- [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md) — Service가 UseCase Port가 되는 구조

## 면접/시니어 질문 미리보기

- "비즈니스 로직을 Service에 두는 것과 Domain 객체에 두는 것, 어떻게 구분하나요?" — 하나의 도메인 객체가 스스로 처리할 수 있는 규칙은 Domain 안에, 여러 객체나 외부 자원을 조합해야 하는 규칙은 Service에 둔다.
- "Service를 `interface + impl`로 나누는 이유가 뭔가요?" — 테스트에서 Mock 교체를 위해, 또는 DIP를 적용해 구현을 숨기기 위해서다. 구현이 하나밖에 없을 때는 interface가 없어도 무방하다는 견해도 있다.
- "트랜잭션은 어느 계층에 두나요?" — 일반적으로 Service 계층에 `@Transactional`을 두어 유스케이스 단위로 트랜잭션을 관리한다. Repository에 두면 트랜잭션 범위가 너무 좁아진다.

## 한 줄 정리

Service 계층은 유스케이스 흐름을 조합하고 트랜잭션 경계를 잡는 곳이며, 비즈니스 규칙이 Controller나 Repository로 새지 않게 막는 역할이다.
