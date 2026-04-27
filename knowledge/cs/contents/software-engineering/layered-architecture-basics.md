# 계층형 아키텍처 기초 (Layered Architecture Basics)

> 한 줄 요약: 계층형 아키텍처는 코드를 역할별로 쌓아 올려 각 계층이 바로 아래 계층에만 의존하도록 구조를 나누는 가장 흔한 설계 패턴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Controller / Service / Repository before 예시 - 주문 생성 로직이 Controller에 몰린 상태](#before-주문-생성-로직이-controller에-몰린-상태)
- [Controller / Service / Repository after 예시 - 주문 생성 흐름을 Controller Service Repository로 나눈 상태](#after-주문-생성-흐름을-controller-service-repository로-나눈-상태)
- [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)
- [Service 계층 기초](./service-layer-basics.md)
- [Repository, DAO, Entity](./repository-dao-entity.md)
- [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md)
- [software-engineering 카테고리 인덱스](./README.md)
- [Spring Bean DI Basics](../spring/spring-bean-di-basics.md)

retrieval-anchor-keywords: layered architecture basics, 계층형 아키텍처 입문, 레이어드 아키텍처 기초, controller service repository 구조, presentation layer, business layer, persistence layer, 계층 분리 이유, 3 tier architecture beginner, 레이어 의존 방향, 계층 왜 나누나요, beginner layered architecture, responsibility leakage example, controller fat anti pattern, clean layering before after, controller validation boundary, controller transaction boundary, service transaction orchestration, validation in controller vs service, order create inventory check example, 주문 생성 재고 확인 예시, controller service repository 주문 생성, 형식 검증 업무 규칙 트랜잭션 한 줄 요약, controller service validation transaction self check, self-check 상단 요약

## 먼저 보는 10초 기준

먼저 이 한 줄만 잡고 시작하면 된다: **형식 검증은 Controller, 업무 규칙은 Service/Domain, 여러 저장을 함께 묶는 트랜잭션은 Service**.

- self-check로 바로 확인: [Controller 검증/트랜잭션 경계 self-check](#controller-검증트랜잭션-경계-self-check-3문항)
- 같은 기준을 Service 문맥에서 다시 보기: [Service 계층 기초 - 검증/트랜잭션 경계 quick sync](./service-layer-basics.md#검증트랜잭션-경계-quick-sync)

## 먼저 잡는 멘탈 모델

계층형 아키텍처를 처음 볼 때는 용어보다 **"창구-업무-창고" 3칸 분리**로 기억하면 쉽다.

- Controller: 주문 창구(요청/응답)
- Service: 업무 처리(규칙/정책)
- Repository: 창고 출납(DB 저장/조회)

핵심은 "한 칸이 옆 칸 일까지 가져가지 않기"다.

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

### 작은 before/after 코드 스케치

처음에는 "어떤 코드를 어디에 둬야 하는지"만 잡아도 충분하다. 아래 예시는 **주문 생성 시나리오**를 기준으로, **책임이 섞인 상태(before)**와 **역할을 나눈 상태(after)**를 비교한다.

| 비교 포인트 | Before (책임 누수) | After (계층 분리) |
|---|---|---|
| 시나리오 | 주문 생성 시 Controller가 수량 검증, 재고 확인, 주문 저장까지 다 처리 | 주문 생성 시 Controller는 요청만 받고, Service가 재고 확인 + 주문 저장을 조립 |
| Controller 역할 | 요청 처리 + 비즈니스 규칙 + DB 접근을 모두 수행 | 요청/응답 변환만 담당 |
| Service 역할 | 없음(비즈니스 규칙이 흩어짐) | "수량은 1 이상", "재고가 충분해야 함", "주문 저장과 재고 차감은 함께 성공/실패"를 한곳에 모음 |
| Repository 역할 | 없음(쿼리가 Controller에 박힘) | 주문/재고 저장 전담 |

#### Before: 주문 생성 로직이 Controller에 몰린 상태

```java
// BEFORE: 주문 생성 유스케이스가 Controller에 몰려 있음
@PostMapping("/orders")
public OrderResponse create(@RequestBody OrderRequest req) {
    if (req.quantity() <= 0) {
        throw new IllegalArgumentException("수량은 1 이상");
    }

    int stock = inventoryRepository.findStockByProductId(req.productId());
    if (stock < req.quantity()) {
        throw new IllegalStateException("재고 부족");
    }

    inventoryRepository.decrease(req.productId(), req.quantity());
    orderRepository.save(req.productId(), req.quantity());

    return new OrderResponse("CREATED");
}
```

#### After: 주문 생성 흐름을 Controller Service Repository로 나눈 상태

```java
// AFTER: 같은 주문 생성 시나리오를 Controller -> Service -> Repository로 분리
@PostMapping("/orders")
public OrderResponse create(@RequestBody OrderRequest req) {
    orderService.createOrder(req.productId(), req.quantity());
    return new OrderResponse("CREATED");
}

@Service
class OrderService {
    private final OrderRepository orderRepository;
    private final InventoryRepository inventoryRepository;

    @Transactional
    void createOrder(Long productId, int quantity) {
        if (quantity <= 0) {
            throw new IllegalArgumentException("수량은 1 이상");
        }

        int stock = inventoryRepository.findStockByProductId(productId);
        if (stock < quantity) {
            throw new IllegalStateException("재고 부족");
        }

        inventoryRepository.decrease(productId, quantity);
        orderRepository.save(productId, quantity);
    }
}

@Repository
class OrderRepository {
    void save(Long productId, int quantity) {
        // SQL/JPA는 여기에서만 다룬다.
    }
}
```

이 before/after는 [Service 계층 기초](./service-layer-basics.md)의 표와 같은 **"주문 생성 + 재고 확인/차감"** 시나리오를 쓴다. 두 문서를 왕복할 때 예시가 바뀌지 않게 맞춘 것이다.

핵심은 "Controller를 얇게 만들자"가 아니라 **규칙(검증/정책)과 저장(쿼리)을 분리해 변경 지점을 줄이는 것**이다.

before/after를 본 뒤에도 "그럼 after에서 Service가 어디까지 맡아야 하지?"가 바로 헷갈리면 [Service 계층 기초의 흔한 오해와 함정](./service-layer-basics.md#흔한-오해와-함정)으로 넘어가 자주 섞이는 책임 경계를 다시 맞추면 된다.

### 짧은 안티패턴 비교: Controller가 Repository 조회로 검증까지 하는 경우

초심자가 특히 많이 하는 실수는 "중복 이메일 검사 정도는 간단하니까 Controller에서 Repository를 직접 조회해도 되지 않나?"라고 생각하는 것이다. 하지만 이 순간부터 검증 규칙이 HTTP 진입점에 묶인다.

| 상태 | 코드 모양 | 왜 문제인가 |
|---|---|---|
| before: Controller가 Repository 조회까지 수행 | `userRepository.existsByEmail(...)`를 Controller에서 호출하고 중복이면 바로 예외 반환 | 같은 회원가입 규칙을 배치/관리자 등록/API 재사용 시 다시 써야 한다 |
| after: Controller는 형식만 확인, Service가 조회 규칙 조립 | Controller는 `@Email`, 빈 값 여부만 보고 `userService.register(...)` 호출 | "이미 가입된 이메일은 불가" 규칙을 다른 진입점에서도 같은 Service로 재사용할 수 있다 |

```java
// BEFORE: 컨트롤러가 저장소 조회로 업무 규칙까지 검증
@PostMapping("/users")
public UserResponse register(@RequestBody RegisterUserRequest request) {
    if (userRepository.existsByEmail(request.email())) {
        throw new IllegalArgumentException("이미 가입된 이메일입니다.");
    }

    userRepository.save(new User(request.email(), request.name()));
    return new UserResponse("CREATED");
}

// AFTER: 컨트롤러는 형식만, 중복 조회 규칙은 서비스가 담당
@PostMapping("/users")
public UserResponse register(@Valid @RequestBody RegisterUserRequest request) {
    userService.register(request.email(), request.name());
    return new UserResponse("CREATED");
}

@Service
class UserService {
    private final UserRepository userRepository;

    void register(String email, String name) {
        if (userRepository.existsByEmail(email)) {
            throw new IllegalArgumentException("이미 가입된 이메일입니다.");
        }

        userRepository.save(new User(email, name));
    }
}
```

짧게 외우면:

- `@Email`, 빈 문자열, JSON 형식 오류는 Controller
- `이미 가입된 이메일인가?`처럼 조회가 필요한 업무 규칙은 Service/Domain
- 저장 전 조회가 들어간다고 해서 모두 Controller 검증이 되는 것은 아니다

**계층 간 데이터 전달**

계층 경계를 넘을 때는 DTO(Data Transfer Object)를 사용한다. Controller가 받은 JSON을 RequestDTO로 변환하고, Service는 그 DTO를 처리해 도메인 객체나 ResponseDTO를 반환한다. DB에서 꺼낸 JPA 엔티티를 Controller까지 그대로 노출하면 엔티티가 HTTP 응답 형태에 종속된다.

**상향 의존 금지**

Persistence 계층이 Service 계층의 클래스를 직접 import하면 하위 계층이 상위 계층을 알게 된다. 이 규칙이 깨지면 순환 의존이 생기고 계층 경계가 무너진다.

## 흔한 오해와 함정

- "Controller에서 Repository를 직접 호출해도 된다"는 생각이 있다. 규모가 작으면 동작하지만, 비즈니스 로직이 Controller에 쌓이면 분리 비용이 커진다.
- "Service는 무조건 얇아야 한다"고 오해하기도 한다. Service가 비즈니스 로직의 중심이므로 도메인 규칙은 Service나 도메인 객체에 있어야 한다. Controller가 로직을 가지면 안 된다.
- "3계층 구조가 유일한 정답"이라는 오해도 있다. 계층 수는 요구사항에 따라 달라진다. 중요한 건 의존 방향이 단방향이어야 한다는 원칙이다.

## Controller 검증/트랜잭션 경계 self-check (3문항)

초심자는 보통 "간단한 검증은 Controller에서 해도 되나?", "트랜잭션을 어디에 걸지?"에서 가장 많이 헷갈린다. 아래 3문항으로 먼저 자가진단하면 경계를 빠르게 잡을 수 있다.

먼저 한 줄로 기억하면: **형식 검증은 Controller, 업무 규칙은 Service/Domain, 여러 저장을 함께 묶는 트랜잭션은 Service**다.

문서 상단의 [먼저 보는 10초 기준](#먼저-보는-10초-기준)과 같은 문장이다. 이 한 줄을 기준점으로 두고 아래 표를 보면, [Service 계층 기초](./service-layer-basics.md#검증트랜잭션-경계-quick-sync)와 왕복할 때도 같은 기준으로 읽을 수 있다.

| self-check 질문 | YES면 | NO면 |
|---|---|---|
| 1) 이 검증 규칙이 HTTP 바깥(배치/메시지 소비자)에서도 동일하게 필요하다? | Service(또는 Domain)로 올린다. | Controller에서 입력 형식 검증(`null`, 빈 문자열, 포맷)까지만 처리한다. |
| 2) 이 로직이 여러 Repository 저장/조회의 원자성(같이 성공/실패)을 보장해야 한다? | 트랜잭션은 Service에 둔다. | 단건 단순 조회/위임이면 Service에서 트랜잭션 없이 시작해도 된다. |
| 3) 같은 유스케이스를 다른 진입점이 재사용할 가능성이 있다? | Controller를 얇게 두고 Service 유스케이스로 모은다. | 진입점 전용 변환/직렬화 로직은 Controller에 남긴다. |

작은 예시:

- "수량은 1 이상", "재고가 부족하면 주문할 수 없다"는 웹/배치/이벤트 모두에 적용되는 업무 규칙이므로 Service 쪽이 기본 위치다.
- `@Valid` 같은 요청 스키마 검증은 HTTP 요청 해석 단계라 Controller 쪽이 자연스럽다.
- 주문 생성 시 `orders` 저장 + `inventory` 차감이 함께 성공/실패해야 하면 트랜잭션 경계는 Service에 둔다.
- 회원가입에서 `existsByEmail(...)`처럼 Repository 조회가 필요한 중복 검사도 업무 규칙이므로 기본 위치는 Service다.

빠르게 다시 맞춰 보고 싶다면:

- Service 쪽 한눈 요약으로 돌아가기: [Service 계층 기초 - 검증/트랜잭션 경계 quick sync](./service-layer-basics.md#검증트랜잭션-경계-quick-sync)

## 실무에서 쓰는 모습

`POST /orders` 요청이 들어오면 `OrderController`가 받아 `OrderRequest` DTO로 역직렬화하고 `OrderService.createOrder(request)`를 호출한다. Service는 "수량은 1 이상"과 "재고가 충분해야 함"을 확인한 뒤, 재고 차감과 주문 저장을 같은 트랜잭션 안에서 처리한다. Controller는 그 결과를 `OrderResponse`로 감싸 HTTP 응답으로 내보낸다.

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
