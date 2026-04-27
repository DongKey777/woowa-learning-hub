# Spring Data Repository vs Domain Repository Bridge

> 한 줄 요약: `JpaRepository`는 Spring Data가 DB 접근을 쉽게 하려고 주는 프레임워크 인터페이스이고, 도메인 repository는 우리 애플리케이션이 "무엇을 저장하고 찾는지"를 말하는 계약이다.
>
> 문서 역할: 이 문서는 처음 배우는데 "`Repository`가 왜 두 번 나오지?"가 헷갈릴 때, Spring Data 검색어가 들어와도 초급자가 **큰 그림**부터 잡도록 연결하는 beginner bridge primer다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Data JPA 기초](./spring-data-jpa-basics.md)
- [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)
- [Repository Interface Contract Primer](../software-engineering/repository-interface-contract-primer.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring data repository vs domain repository, spring data vs domain repository bridge, jparepository vs domain repository, jparepository vs repository interface, domain repository contract, spring data repository interface beginner, repository가 두 개, repository interface 두 개, 처음 배우는데 repository가 두개, spring repository 큰 그림, spring repository 언제 쓰는지, framework repository vs domain contract, persistence adapter repository, hexagonal repository spring, clean architecture repository spring, spring data adapter repository, infrastructure repository spring, application repository contract, jpa repository 구현체 아님, jpa repository를 바로 서비스에 붙여도 되나요, domain repository bridge primer

## 처음 배우는데 30초 큰 그림

`Repository`라는 단어가 두 번 나와도, 사실 질문이 다르다.

| 이름 | 답하는 질문 | 누가 소유하나 | 언제 쓰는지 |
|---|---|---|---|
| 도메인 repository | "우리 서비스는 무엇을 저장/조회해야 하지?" | 애플리케이션 | 유스케이스 언어를 고정할 때 |
| Spring Data repository (`JpaRepository`) | "JPA로 그 작업을 어떻게 쉽게 구현하지?" | 프레임워크 | CRUD, 쿼리 메서드, paging을 빠르게 붙일 때 |

초급 감각으로는 이렇게 보면 된다.

- 도메인 repository: 서비스 코드가 의존하는 **업무 계약**
- Spring Data repository: 그 계약을 구현할 때 쓰는 **기술 도구**

즉 둘은 경쟁 관계가 아니라, 자주 **위아래로 연결**된다.

## 왜 둘을 분리하나

`JpaRepository<OrderEntity, Long>`를 서비스가 바로 써도 작은 프로젝트에서는 돌아간다. 다만 그 순간 서비스가 이런 프레임워크 규칙까지 같이 알게 된다.

- `OrderEntity`라는 JPA 저장 모양
- `Pageable`, `Slice`, query method naming 같은 Spring Data 문법
- 저장 기술이 JPA라는 사실

반대로 도메인 repository를 하나 두면 서비스는 더 업무 말투로 읽힌다.

```java
public interface OrderRepository {
    Order save(Order order);
    Optional<Order> findByOrderNumber(String orderNumber);
}
```

그러면 서비스는 "주문을 저장한다, 주문번호로 찾는다"만 알고, 그 아래에서 JPA를 쓰든 JDBC를 쓰든 덜 흔들린다.

## 연결 모습 한 장으로 보기

```text
OrderService
  -> OrderRepository   // 도메인 계약
       -> OrderRepositoryBridge
            -> SpringDataOrderJpaRepository extends JpaRepository<OrderEntity, Long>
```

핵심은 가운데 bridge/adaptor다.

- 위로는 도메인 계약을 맞춘다
- 아래로는 Spring Data JPA 인터페이스를 호출한다

## 짧은 예제

```java
public interface OrderRepository {
    Optional<Order> findByOrderNumber(String orderNumber);
    Order save(Order order);
}

public interface SpringDataOrderJpaRepository
        extends JpaRepository<OrderEntity, Long> {
    Optional<OrderEntity> findByOrderNumber(String orderNumber);
}

@Repository
public class OrderRepositoryBridge implements OrderRepository {
    private final SpringDataOrderJpaRepository jpaRepository;

    public OrderRepositoryBridge(SpringDataOrderJpaRepository jpaRepository) {
        this.jpaRepository = jpaRepository;
    }

    @Override
    public Optional<Order> findByOrderNumber(String orderNumber) {
        return jpaRepository.findByOrderNumber(orderNumber)
                .map(OrderEntity::toDomain);
    }

    @Override
    public Order save(Order order) {
        OrderEntity saved = jpaRepository.save(OrderEntity.from(order));
        return saved.toDomain();
    }
}
```

여기서 이름은 팀마다 달라도 괜찮다.

- `OrderJpaRepository`
- `OrderJpaDataRepository`
- `OrderRepositoryAdapter`

중요한 것은 이름보다 **역할 분리**다.

## 자주 헷갈리는 포인트

### 1. `JpaRepository`가 곧 도메인 repository인가?

아니다. `JpaRepository`는 도메인 repository를 **구현하는 데 자주 쓰는 선택지**다.

### 2. 항상 두 인터페이스로 나눠야 하나?

아니다. 처음 배우는데 CRUD가 아주 단순한 작은 앱이면 바로 `JpaRepository`를 써도 된다.

다만 아래 조건이 보이면 분리가 이득이다.

- 서비스 코드에서 JPA 타입이 자꾸 새어 나온다
- 도메인 모델과 `@Entity`를 분리하고 싶다
- 저장 기술을 바꾸진 않더라도, 업무 계약을 먼저 읽히게 하고 싶다

### 3. 그럼 서비스는 무엇에 의존해야 하나?

기본적으로는 **도메인 repository 계약**에 의존하는 쪽이 큰 그림이 더 선명하다.

## 언제 이렇게 설명하면 좋나

- "Spring Data JPA는 알겠는데 repository 인터페이스를 왜 또 만들지?"라는 질문이 나올 때
- 포트/어댑터, 클린 아키텍처, 계층 분리를 처음 접할 때
- `Entity`와 domain object를 바로 섞어도 되는지 고민할 때

## 다음 문서

- Spring Data JPA 자체 문법부터 잡으려면 [Spring Data JPA 기초](./spring-data-jpa-basics.md)
- repository/DAO/entity 용어를 더 넓게 정리하려면 [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)
- "왜 인터페이스 계약을 따로 두는가"를 설계 관점으로 보려면 [Repository Interface Contract Primer](../software-engineering/repository-interface-contract-primer.md)

## 한 줄 정리

처음 배우는데 `Repository`가 두 번 보여도 겁먹을 필요는 없다. 도메인 repository는 **업무 계약**, Spring Data repository는 그 계약을 구현하는 **프레임워크 도구**다.
