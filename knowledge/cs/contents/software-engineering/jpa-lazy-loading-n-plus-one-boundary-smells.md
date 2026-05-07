---
schema_version: 3
title: JPA Lazy Loading and N+1 Boundary Smells
concept_id: software-engineering/jpa-lazy-loading-n-plus-one-boundary-smells
canonical: true
category: software-engineering
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- jpa
- lazy-loading
- n-plus-one
- entity-leakage
aliases:
- JPA Lazy Loading and N+1 Boundary Smells
- lazy loading N+1 boundary smells
- LazyInitializationException API boundary
- fetch join vs projection smell
- entity serialization N plus one
- JPA 지연 로딩 N+1 경계 냄새
symptoms:
- Controller가 Entity를 그대로 JSON 응답으로 반환해 serializer가 LAZY proxy를 건드리며 LazyInitializationException이나 N+1이 발생해
- 화면별 조회 요구를 domain entity와 fetch join everywhere로 해결하려다 persistence, API, domain boundary가 섞여
- OSIV가 켜져 있으면 직렬화 중 추가 쿼리가 조용히 나가고 꺼져 있으면 같은 API가 터져
intents:
- symptom
- troubleshooting
- definition
prerequisites:
- software-engineering/persistence-model-leakage
- software-engineering/repository-dao-entity
next_docs:
- software-engineering/query-model-separation-read-heavy
- software-engineering/persistence-adapter-mapping-checklist
- software-engineering/entity-leakage-review-checklist
linked_paths:
- contents/software-engineering/persistence-model-leakage-anti-patterns.md
- contents/software-engineering/persistence-adapter-mapping-checklist.md
- contents/software-engineering/query-model-separation-read-heavy-apis.md
- contents/software-engineering/repository-dao-entity.md
- contents/software-engineering/architecture-layering-fundamentals.md
- contents/software-engineering/api-design-error-handling.md
- contents/software-engineering/entity-leakage-review-checklist.md
confusable_with:
- software-engineering/persistence-model-leakage
- software-engineering/query-model-separation-read-heavy
- software-engineering/entity-leakage-review-checklist
forbidden_neighbors: []
expected_queries:
- JPA LAZY 자체가 문제가 아니라 Entity가 API boundary 밖으로 새서 N+1이 생기는 이유를 설명해줘
- Controller에서 Entity를 직접 반환하면 LazyInitializationException과 hidden N+1이 어떻게 발생해?
- fetch join을 everywhere로 넣는 것보다 response DTO와 query model을 분리해야 하는 이유가 뭐야?
- OSIV가 켜져 있을 때 직렬화 중 추가 쿼리가 조용히 나가는 문제를 어떻게 진단해?
- Domain, Persistence, API boundary 관점에서 LAZY loading과 N+1 문제를 나눠 설명해줘
contextual_chunk_prefix: |
  이 문서는 JPA LAZY loading, LazyInitializationException, hidden N+1, fetch join 남발을 persistence/API/domain boundary 냄새로 진단하는 beginner symptom router이다.
---
# JPA Lazy Loading and N+1 Boundary Smells

> 한 줄 요약: `LAZY` 자체가 문제라기보다, JPA 엔티티를 API와 애플리케이션 경계 밖으로 그대로 흘려보낼 때 직렬화와 화면 요구가 프록시를 건드리며 `LazyInitializationException`, 숨은 N+1, fetch join 남발이 함께 나타난다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: jpa lazy loading n plus one boundary smells basics, jpa lazy loading n plus one boundary smells beginner, jpa lazy loading n plus one boundary smells intro, software engineering basics, beginner software engineering, 처음 배우는데 jpa lazy loading n plus one boundary smells, jpa lazy loading n plus one boundary smells 입문, jpa lazy loading n plus one boundary smells 기초, what is jpa lazy loading n plus one boundary smells, how to jpa lazy loading n plus one boundary smells
<details>
<summary>Table of Contents</summary>

- [왜 같이 헷갈리는가](#왜-같이-헷갈리는가)
- [세 가지 경계로 나눠 보기](#세-가지-경계로-나눠-보기)
- [냄새 1. API가 엔티티를 직접 직렬화한다](#냄새-1-api가-엔티티를-직접-직렬화한다)
- [냄새 2. 서비스 흐름이 LAZY 조회 타이밍에 기대기 시작한다](#냄새-2-서비스-흐름이-lazy-조회-타이밍에-기대기-시작한다)
- [냄새 3. fetch join을 만능 해결책처럼 남발한다](#냄새-3-fetch-join을-만능-해결책처럼-남발한다)
- [초심자용 판단 순서](#초심자용-판단-순서)
- [기억할 기준](#기억할-기준)

</details>

> 관련 문서:
> - [Software Engineering README: JPA Lazy Loading and N+1 Boundary Smells](./README.md#jpa-lazy-loading-and-n1-boundary-smells)
> - [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)
> - [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
> - [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md)
> - [API 설계와 예외 처리](./api-design-error-handling.md)
>
> retrieval-anchor-keywords: jpa lazy loading, lazy initialization exception, n+1 query smell, fetch join boundary, fetch join vs projection, entity serialization smell, jpa entity api response, lazy loading api serialization, open session in view smell, osiv lazy loading, beginner jpa api boundary, persistence boundary smell, entity to dto separation, repository adapter fetch join, domain boundary persistence boundary, query repository separation, cqrs lite read model

## 왜 같이 헷갈리는가

처음 JPA를 배우면 보통 이런 흐름을 한 번에 만난다.

- `@ManyToOne(fetch = FetchType.LAZY)` 같은 연관관계 매핑
- 컨트롤러에서 엔티티를 그대로 JSON 응답으로 반환
- 화면 요구가 늘자 `fetch join`으로 조회 최적화 시도
- 어느 순간 `N+1`이나 `LazyInitializationException` 발생

그래서 초심자는 자주 이렇게 오해한다.

- "`LAZY`가 문제니까 전부 `EAGER`로 바꾸자"
- "JSON 순환 참조만 막으면 괜찮다"
- "느리면 일단 `fetch join`을 everywhere로 넣자"

하지만 이 셋은 보통 같은 근본 원인에서 나온다.

- 저장 모델인 JPA 엔티티가 API 경계까지 넘어간다
- 애플리케이션 서비스가 ORM 프록시가 언제 초기화되는지에 기대기 시작한다
- 화면별 조회 요구를 도메인 모델과 같은 객체로 해결하려 한다

즉 "쿼리 최적화 문제"처럼 보이지만 실제로는 **경계(boundary) 문제**인 경우가 많다.

## 세 가지 경계로 나눠 보기

| 경계 | 이 경계가 책임질 질문 | 여기서 다루면 좋은 것 | 여기서 다루면 안 좋은 것 |
|---|---|---|---|
| Domain boundary | "무슨 규칙을 지켜야 하지?" | 주문 상태 변경 규칙, 불변식, 계산 규칙 | 프록시 초기화 시점, fetch 전략, JSON 필드 노출 |
| Persistence boundary | "어떻게 저장하고 읽지?" | `LAZY`, `fetch join`, `entity graph`, 매핑, ORM 최적화 | 응답 JSON 모양, 화면 전용 필드 결정 |
| API boundary | "무엇을 외부에 보여주지?" | 응답 DTO, 직렬화 정책, 필드 이름, 에러 응답 | JPA 프록시 직접 노출, 영속성 컨텍스트에 의존한 직렬화 |

짧게 정리하면 이렇다.

- `LAZY`와 `fetch join`은 persistence boundary의 관심사다
- JSON 직렬화와 응답 필드 선택은 API boundary의 관심사다
- 주문 규칙, 계산 규칙은 domain boundary의 관심사다

이 셋이 섞이면 "컨트롤러가 엔티티를 반환했을 뿐인데 쿼리가 터지는" 일이 생긴다.

## 냄새 1. API가 엔티티를 직접 직렬화한다

가장 흔한 시작점이다.

### Before

```java
@Entity
public class OrderEntity {
    @Id
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    private MemberEntity member;

    @OneToMany(mappedBy = "order", fetch = FetchType.LAZY)
    private List<OrderLineEntity> lines = new ArrayList<>();

    public MemberEntity getMember() {
        return member;
    }

    public List<OrderLineEntity> getLines() {
        return lines;
    }
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

겉으로는 간단하지만 실제 흐름은 보통 이렇다.

1. 컨트롤러가 `OrderEntity`를 반환한다.
2. JSON 직렬화기가 getter를 따라 `member`, `lines`를 읽는다.
3. 이 시점이 트랜잭션 밖이면 `LazyInitializationException`이 난다.
4. 이 시점이 트랜잭션 안이거나 OSIV가 켜져 있으면, 직렬화 과정에서 추가 쿼리가 발생한다.

주문 1건이면 티가 덜 난다.
하지만 주문 목록 20건을 반환하면 다음처럼 변한다.

- 주문 목록 조회 1번
- 각 주문의 `member` 초기화 N번
- 각 주문의 `lines` 초기화 N번

즉 **API 직렬화가 N+1을 만들어 낼 수 있다.**

### 왜 경계 냄새인가

여기서 문제는 `LAZY` 자체가 아니다.
문제는 API 경계가 "JPA 프록시를 어떻게 직렬화할지"까지 떠안는다는 점이다.

- API 스펙이 엔티티 내부 구조에 묶인다
- 직렬화 시점이 쿼리 시점이 된다
- OSIV 설정이 바뀌면 API 동작도 같이 흔들린다

### After

## 냄새 1. API가 엔티티를 직접 직렬화한다 (계속 2)

```java
public interface OrderRepository {
    Order getDetail(OrderId id);
}

@Component
class JpaOrderRepositoryAdapter implements OrderRepository {
    @PersistenceContext
    private EntityManager em;

    private final OrderEntityMapper mapper;

    @Override
    public Order getDetail(OrderId id) {
        OrderEntity entity = em.createQuery(
                """
                select distinct o
                from OrderEntity o
                join fetch o.member
                left join fetch o.lines
                where o.id = :id
                """,
                OrderEntity.class
        ).setParameter("id", id.value())
                .getSingleResult();

        return mapper.toDomain(entity);
    }
}

public record OrderResponse(
        Long id,
        String memberName,
        int lineCount
) {
    static OrderResponse from(Order order) {
        return new OrderResponse(
                order.id().value(),
                order.memberName(),
                order.lines().size()
        );
    }
}

@RestController
class OrderController {
    private final GetOrderUseCase getOrderUseCase;

    @GetMapping("/orders/{id}")
    OrderResponse findById(@PathVariable Long id) {
        Order order = getOrderUseCase.get(new OrderId(id));
        return OrderResponse.from(order);
    }
}
```

여기서 핵심은 둘이다.

- `fetch join`은 repository adapter 안에 있다
- API는 `OrderResponse`만 반환한다

## 냄새 1. API가 엔티티를 직접 직렬화한다 (계속 3)

즉 "어떤 연관관계를 미리 읽어 와야 하는가"는 persistence boundary가 결정하고, "어떤 필드를 외부에 보여줄까"는 API boundary가 결정한다.

## 냄새 2. 서비스 흐름이 LAZY 조회 타이밍에 기대기 시작한다

두 번째 냄새는 컨트롤러 밖에서도 생긴다.
서비스가 엔티티 컬렉션을 순회하면서, 사실상 쿼리 타이밍까지 함께 제어하게 되는 경우다.

### Before

```java
@Service
@Transactional(readOnly = true)
public class OrderSummaryService {
    private final OrderJpaRepository orderJpaRepository;

    public MemberOrderSummary summarize(Long memberId) {
        List<OrderEntity> orders = orderJpaRepository.findByMemberId(memberId);

        int totalPrice = 0;
        for (OrderEntity order : orders) {
            totalPrice += order.getLines().stream()
                    .mapToInt(line -> line.getPrice() * line.getQuantity())
                    .sum();
        }

        return new MemberOrderSummary(orders.size(), totalPrice);
    }
}
```

이 코드는 비즈니스 로직처럼 보이지만 실제로는 이런 의미를 가진다.

- 주문 목록 1번 조회
- 각 주문의 `lines`를 순회할 때마다 추가 조회 N번

서비스는 "합계를 계산한다"는 규칙과 함께 "언제 DB에 다시 다녀올지"까지 사실상 떠안는다.

이 구조의 문제는 두 가지다.

- 루프를 돌 때마다 쿼리가 나가므로 성능이 코드 모양만 보고는 보이지 않는다
- 같은 로직을 트랜잭션 밖으로 옮기면 갑자기 예외가 날 수 있다

즉 서비스가 도메인 규칙을 말하는 척하지만, 실제로는 ORM의 지연 로딩 타이밍에 기대고 있다.

### 더 나은 방향

질문을 먼저 나눠야 한다.

- 정말 aggregate 규칙을 계산하려는가
- 아니면 API 목록 화면에 필요한 숫자만 만들려는가

목록 화면이라면 projection이 더 단순할 때가 많다.

## 냄새 2. 서비스 흐름이 LAZY 조회 타이밍에 기대기 시작한다 (계속 2)

```java
public record MemberOrderSummaryRow(
        Long orderId,
        String status,
        long itemCount,
        int totalPrice
) {
}

@Repository
class OrderQueryRepository {
    @PersistenceContext
    private EntityManager em;

    public List<MemberOrderSummaryRow> findSummaries(Long memberId) {
        return em.createQuery(
                """
                select new com.example.MemberOrderSummaryRow(
                    o.id,
                    o.status,
                    count(l.id),
                    coalesce(sum(l.price * l.quantity), 0)
                )
                from OrderEntity o
                left join o.lines l
                where o.member.id = :memberId
                group by o.id, o.status
                """,
                MemberOrderSummaryRow.class
        ).setParameter("memberId", memberId)
                .getResultList();
    }
}
```

이 경우에는 aggregate 전체를 복원할 이유가 없다.
화면에 필요한 읽기 모델을 바로 만든다.

반대로 주문 변경 규칙을 검증해야 한다면, 그때는 repository adapter가 필요한 연관관계를 포함해 aggregate를 읽어 오면 된다.

핵심은 이것이다.

- **규칙 검증**이면 aggregate 중심
- **목록/조회 화면**이면 projection이나 query model 중심

둘을 구분하지 않으면 "엔티티 순회 코드"가 어느새 성능 병목과 경계 누수의 출발점이 된다.

## 냄새 3. fetch join을 만능 해결책처럼 남발한다

`fetch join`은 매우 유용하다.
하지만 유용하다는 말과 "항상 정답"이라는 말은 다르다.

초심자가 자주 만드는 메서드는 이런 모양이다.

```java
List<OrderEntity> findAllForApi();
```

그리고 내부 쿼리는 점점 이렇게 커진다.

- `join fetch o.member`
- `join fetch o.lines`
- `join fetch l.product`
- `join fetch o.coupon`

그러다 보면 이런 문제가 따라온다.

- 어떤 화면은 필요 없는 연관관계까지 항상 읽는다
- 컬렉션 fetch join은 중복 row와 pagination 문제를 쉽게 만든다
- 새 API 필드가 생길 때마다 repository 조회 메서드가 계속 비대해진다
- 읽기 최적화 요구가 도메인/엔티티 설계를 끌고 다닌다

즉 `fetch join`은 "도메인 설계"가 아니라 **특정 읽기 경로를 위한 조회 전략**이다.

### 초심자용 기본 선택

| 상황 | 먼저 떠올릴 기본 선택 | 이유 |
|---|---|---|
| 주문 상태 변경, 주문 취소 같은 규칙 검증 | repository adapter에서 필요한 연관관계만 로딩 | 규칙을 지키는 aggregate가 필요하다 |
| 단건 상세 API | `fetch join` 또는 `entity graph` | 필요한 관계가 비교적 명확하다 |
| 목록 화면, 검색, 대시보드 | projection / query model | 화면 필드만 읽는 편이 단순하고 가볍다 |
| 엔티티를 그대로 JSON으로 내려보내고 싶음 | 하지 않는다 | 직렬화가 ORM 경계를 침범한다 |

`fetch join`을 넣는 질문은 "예외가 없어지나?"가 아니라, "이 읽기 경로가 어떤 데이터를 미리 필요로 하나?"여야 한다.

## 초심자용 판단 순서

1. 이 값이 API 응답 밖으로 나가나?
2. 그렇다면 엔티티가 아니라 응답 DTO나 view model로 끊었나?
3. 이 유스케이스가 도메인 규칙 검증인가, 단순 조회인가?
4. 단순 조회라면 aggregate 대신 projection으로 끝낼 수 없나?
5. `LAZY` 컬렉션을 루프나 직렬화가 건드리고 있다면 N+1을 먼저 의심했나?
6. `fetch join`을 추가하려는 이유가 화면 요구인지, 도메인 규칙인지 구분했나?

이 순서로 보면 보통 "EAGER로 바꾸자"보다 더 안정적인 답에 빨리 도달한다.

## 기억할 기준

- `LAZY`는 나쁜 옵션이 아니라 **조회 시점을 통제하는 persistence 도구**다
- N+1은 repository 메서드 안에서만 생기는 것이 아니라, **API 직렬화와 서비스 루프**에서도 생긴다
- `fetch join`은 유용하지만 **persistence boundary 안의 읽기 전략**이지 도메인 규칙이 아니다
- 엔티티를 API 응답으로 직접 반환하는 순간 직렬화, ORM 프록시, API 계약이 한 덩어리가 된다
- OSIV는 문제를 해결하기보다, 같은 경계 냄새를 **예외 대신 숨은 쿼리**로 보이게 만들 때가 많다
- "어떤 데이터를 지금 읽어 와야 하지?"는 adapter/query model이 결정하고, "무슨 규칙을 지켜야 하지?"는 domain이 결정하게 두는 편이 덜 아프다

## 한 줄 정리

`LAZY` 자체가 문제라기보다, JPA 엔티티를 API와 애플리케이션 경계 밖으로 그대로 흘려보낼 때 직렬화와 화면 요구가 프록시를 건드리며 `LazyInitializationException`, 숨은 N+1, fetch join 남발이 함께 나타난다.
