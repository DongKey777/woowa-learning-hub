# Persistence Model Leakage Anti-Patterns

> 한 줄 요약: JPA `@Entity`를 API 응답, 애플리케이션 흐름, 도메인 규칙까지 한 번에 끌고 가면 처음엔 편해 보여도 변경 이유가 섞여 경계가 빠르게 무너진다.

**난이도: 🟢 Beginner**

<details>
<summary>Table of Contents</summary>

- [왜 초심자에게 자주 생기나](#왜-초심자에게-자주-생기나)
- [문제를 한 장으로 보기](#문제를-한-장으로-보기)
- [안티패턴 1. JPA Entity를 API 응답으로 직접 반환](#안티패턴-1-jpa-entity를-api-응답으로-직접-반환)
- [안티패턴 2. 서비스와 도메인이 ORM 세부를 직접 안다](#안티패턴-2-서비스와-도메인이-orm-세부를-직접-안다)
- [안티패턴 3. 조회 최적화 요구가 도메인 모델을 망가뜨린다](#안티패턴-3-조회-최적화-요구가-도메인-모델을-망가뜨린다)
- [리팩토링을 시작하는 신호](#리팩토링을-시작하는-신호)
- [초심자용 분리 순서](#초심자용-분리-순서)
- [기억할 기준](#기억할-기준)

</details>

> 관련 문서:
> - [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
> - [Aggregate Persistence Mapping Pitfalls](./aggregate-persistence-mapping-pitfalls.md)
> - [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
> - [JPA Lazy Loading and N+1 Boundary Smells](./jpa-lazy-loading-n-plus-one-boundary-smells.md)
> - [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
> - [API 설계와 예외 처리](./api-design-error-handling.md)
> - [Domain Invariants as Contracts](./domain-invariants-as-contracts.md)
>
> retrieval-anchor-keywords: persistence model leakage, JPA entity leakage, entity leakage anti-pattern, domain model vs persistence model, entity to dto separation, orm leakage, lazy loading api response, repository adapter mapping, beginner jpa boundary, persistence boundary smell, persistence adapter mapping checklist, aggregate persistence mapping pitfalls, bidirectional association domain leak, cascade type all smell, orphanRemoval smell, domain object to jpa entity, jpa entity mapper checklist, lazy initialization exception, n+1 query smell, fetch join boundary, entity serialization smell, query repository separation, read-heavy api query model, list detail response model

## 왜 초심자에게 자주 생기나

처음 JPA를 배우면 `@Entity` 하나로 많은 문제가 동시에 풀리는 것처럼 보인다.

- DB 테이블과 바로 연결된다
- 서비스에서 그대로 조회할 수 있다
- 컨트롤러에서 JSON 응답으로도 바로 내보낼 수 있다
- 엔티티 메서드에 규칙을 넣으면 도메인 객체처럼도 보인다

그래서 `@Entity`를

- 저장 모델
- 도메인 모델
- API 응답 모델

로 동시에 쓰기 쉽다.

문제는 이 세 가지가 **서로 다른 이유로 바뀐다**는 점이다.

- 저장 모델은 테이블 구조, fetch 전략, 연관관계 매핑 때문에 바뀐다
- 도메인 모델은 규칙, 불변식, 용어 변화 때문에 바뀐다
- API 모델은 화면 요구사항, 응답 필드, 직렬화 정책 때문에 바뀐다

한 객체가 이 세 변경 이유를 모두 떠안으면 작은 수정도 여러 층에 퍼진다.

## 문제를 한 장으로 보기

| 구분 | 좋은 질문 | 주로 바뀌는 이유 | 추천 모델 |
|---|---|---|---|
| Domain model | "무슨 규칙을 지켜야 하지?" | 정책, 용어, 불변식 | `Order`, `OrderLine`, `Money` |
| Persistence model | "어떻게 저장하지?" | 테이블 구조, FK, fetch, cascade | `OrderEntity`, `OrderLineEntity` |
| API model | "무엇을 보여주지?" | 응답 스펙, 화면 요구, 직렬화 | `OrderResponse`, `OrderSummaryResponse` |

핵심은 이름이 아니라 책임이다.

- 도메인 모델은 비즈니스 규칙을 지킨다
- persistence model은 저장을 쉽게 만든다
- API model은 외부 계약을 맞춘다

세 역할이 다르면 객체도 분리하는 편이 안전하다.

## 안티패턴 1. JPA Entity를 API 응답으로 직접 반환

가장 흔한 누수는 컨트롤러가 `@Entity`를 그대로 반환하는 경우다.

### Before

```java
@Entity
public class OrderEntity {
    @Id
    private Long id;

    @Enumerated(EnumType.STRING)
    private OrderStatus status;

    @ManyToOne(fetch = FetchType.LAZY)
    private MemberEntity member;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<OrderLineEntity> lines = new ArrayList<>();
}

@RestController
class OrderController {
    private final OrderJpaRepository orderJpaRepository;

    @GetMapping("/orders/{id}")
    OrderEntity findById(@PathVariable Long id) {
        return orderJpaRepository.findById(id)
                .orElseThrow();
    }
}
```

처음에는 코드가 짧아 보이지만 바로 이런 문제가 붙는다.

- LAZY 연관관계 때문에 직렬화 시점에 예외가 난다
- 양방향 연관관계 때문에 순환 참조 대응이 필요해진다
- 내부 컬럼 구조가 API 스펙으로 굳어 버린다
- 응답 최적화 때문에 엔티티 필드가 늘어나기 시작한다

### After

```java
public record OrderResponse(
        Long id,
        String status,
        String memberName,
        List<OrderLineResponse> lines
) {
    static OrderResponse from(Order order) {
        return new OrderResponse(
                order.id().value(),
                order.status().name(),
                order.memberName(),
                order.lines().stream()
                        .map(line -> new OrderLineResponse(
                                line.productName(),
                                line.quantity(),
                                line.price().amount()
                        ))
                        .toList()
        );
    }
}

@RestController
class OrderController {
    private final GetOrderUseCase getOrderUseCase;

    @GetMapping("/orders/{id}")
    OrderResponse findById(@PathVariable Long id) {
        Order order = getOrderUseCase.findById(id);
        return OrderResponse.from(order);
    }
}
```

이렇게 바꾸면 컨트롤러는 응답 계약만 다루고, 저장 전략은 바깥으로 밀려난다.

### 리팩토링 cue

- 컨트롤러 반환 타입에서 `Entity`를 먼저 제거한다
- 응답 전용 DTO를 만들고 필요한 필드만 고른다
- 직렬화 대응용 어노테이션을 엔티티에 계속 붙이고 있다면 분리 시점이다

## 안티패턴 2. 서비스와 도메인이 ORM 세부를 직접 안다

두 번째 누수는 애플리케이션 서비스나 도메인 코드가 ORM 세부를 직접 기준으로 움직이는 경우다.

### Before

```java
@Service
@Transactional
public class OrderService {
    private final OrderJpaRepository orderJpaRepository;

    public void changeAddress(Long orderId, String address) {
        OrderEntity entity = orderJpaRepository.findById(orderId)
                .orElseThrow();

        if (entity.getStatus() == OrderStatus.SHIPPED) {
            throw new IllegalStateException("already shipped");
        }

        entity.setAddress(address);
    }
}
```

겉으로는 단순하지만 서비스가 다음을 한꺼번에 떠안는다.

- 조회 방식
- ORM 영속성 컨텍스트 동작
- 도메인 규칙
- 상태 변경

이 상태가 길어지면 "서비스 메서드가 도메인 규칙 창고"가 된다.

### After

```java
public interface OrderRepository {
    Order get(OrderId id);
    void save(Order order);
}

public final class Order {
    private final OrderId id;
    private OrderStatus status;
    private Address address;

    public void changeAddress(Address newAddress) {
        if (status == OrderStatus.SHIPPED) {
            throw new IllegalStateException("already shipped");
        }
        this.address = newAddress;
    }
}

@Service
public class ChangeOrderAddressService {
    private final OrderRepository orderRepository;

    @Transactional
    public void changeAddress(Long orderId, String address) {
        Order order = orderRepository.get(new OrderId(orderId));
        order.changeAddress(new Address(address));
        orderRepository.save(order);
    }
}
```

서비스는 흐름만 조합하고, 규칙은 도메인 객체가 책임진다.
JPA 구현은 repository adapter 안으로 숨길 수 있다.

### 리팩토링 cue

- 서비스 메서드에서 `entity.setXxx()`가 계속 보이면 규칙 위치를 의심한다
- 서비스 테스트가 JPA 동작을 알아야만 통과한다면 경계가 섞인 것이다
- `OrderJpaRepository`를 바로 주입하는 대신 `OrderRepository` 인터페이스를 도입한다

## 안티패턴 3. 조회 최적화 요구가 도메인 모델을 망가뜨린다

세 번째 누수는 "화면에서 빨리 보여줘야 하니까 엔티티를 그대로 재사용하자"에서 시작한다.

### Before

```java
@Entity
public class OrderEntity {
    @Id
    private Long id;

    private String status;

    private String memberName;

    private int itemCount;

    private int totalPrice;

    // 주문 규칙보다 목록 화면 컬럼에 맞춘 필드가 계속 늘어난다.
}
```

이 패턴이 계속되면 엔티티가

- 쓰기 모델
- 목록 조회 모델
- 상세 조회 모델

을 동시에 담당하게 된다.

그 결과:

- 조회 화면 하나 바뀔 때마다 엔티티 컬럼 설계가 흔들린다
- 집계성 필드가 늘어나며 값의 진실 원천이 흐려진다
- "도메인 규칙을 담은 모델"이 아니라 "화면 대응용 덩치 큰 레코드"가 된다

### After

```java
public record OrderSummaryResponse(
        Long id,
        String status,
        String memberName,
        int itemCount,
        int totalPrice
) {
}

public interface OrderQueryRepository {
    List<OrderSummaryResponse> findSummaries();
}
```

복잡한 조회는 별도 query model로 두고, 규칙을 담는 도메인 모델과 분리하는 편이 낫다.
CRUD 초반에는 과한 분리가 필요 없지만, 화면 요구가 엔티티 구조를 끌고 다니기 시작하면 읽기 모델을 분리할 가치가 생긴다.

### 리팩토링 cue

- 엔티티 필드 이름이 화면 컬럼 이름을 따라가기 시작하면 분리 신호다
- 목록 API와 상세 API가 같은 엔티티를 억지로 공유하면 query model을 검토한다
- `fetch join` 최적화 요구가 도메인 객체 설계를 밀어내기 시작하면 읽기 경로를 따로 둔다

## 리팩토링을 시작하는 신호

아래 신호가 두세 개 이상 보이면 persistence model leakage를 의심해 볼 만하다.

- 컨트롤러 응답 타입에 `Entity`가 직접 등장한다
- 엔티티 클래스에 JSON 직렬화 어노테이션이 늘어난다
- 서비스가 `entity.getStatus()`를 읽고 `entity.setStatus()`로 규칙을 직접 구현한다
- 도메인 설명보다 `fetch = LAZY`, `cascade`, `orphanRemoval` 논의가 더 자주 나온다
- API 변경 때문에 테이블 매핑 클래스가 자주 수정된다
- 양방향 연관관계와 직렬화 문제를 우회하는 코드가 많아진다

## 초심자용 분리 순서

처음부터 모든 모델을 완전히 나눌 필요는 없다.
대신 아래 순서로 잘라 나가면 부담이 덜하다.

1. API 응답 DTO를 먼저 분리한다.
2. 도메인 규칙이 많은 엔티티부터 별도 도메인 객체나 메서드로 옮긴다.
3. 애플리케이션 서비스가 직접 `JpaRepository`를 모르게 만든다.
4. repository adapter에서 domain <-> entity 매핑을 맡긴다.
5. 조회 최적화 요구가 커지면 query model을 별도 경로로 분리한다.

4번 단계에서 무엇을 adapter 안에 남기고 무엇을 안쪽에서 지워야 하는지 빠르게 점검하려면 [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)를 함께 보면 된다.

초심자에게 중요한 건 "한 번에 완벽한 구조"보다 **변경 이유가 다른 것부터 분리하는 감각**이다.

## 기억할 기준

- `@Entity`는 저장에 최적화된 객체이지, 시스템 전체 대표 모델이 아니다
- API contract와 persistence mapping은 바뀌는 이유가 다르다
- 도메인 규칙은 ORM 세부보다 비즈니스 언어로 읽혀야 한다
- 분리의 출발점은 거창한 패턴 이름보다 "무엇이 무엇 때문에 자주 바뀌는가"다
