# Query Model Separation for Read-Heavy APIs

> 한 줄 요약: 목록/상세 화면이 많아질수록 write entity나 aggregate 하나로 모든 읽기 요구를 버티기보다, 같은 DB 위에서도 query repository와 response model을 따로 두는 CQRS-lite가 더 단순할 때가 많다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: query model basics, read model beginner, query repository basics, query model 뭐예요, read model 뭐예요, query repository 뭐예요, query model 큰 그림, 처음 query model 헷갈림, 조회 전용 모델 기초, 목록 api 엔티티 분리, 목록 api 때문에 repository가 비대해져요, write model read model 차이, query model과 response model 차이, 왜 query model을 나누나요, same database read model
<details>
<summary>Table of Contents</summary>

- [왜 헷갈리는가](#왜-헷갈리는가)
- [한 장으로 보는 세 모델](#한-장으로-보는-세-모델)
- [언제 query repository를 꺼낼까](#언제-query-repository를-꺼낼까)
- [언제 아직 과한가](#언제-아직-과한가)
- [Before: write entity 하나로 목록과 상세를 모두 버틴다](#before-write-entity-하나로-목록과-상세를-모두-버틴다)
- [After: CQRS-lite로 읽기 경로만 분리한다](#after-cqrs-lite로-읽기-경로만-분리한다)
- [초심자용 도입 순서](#초심자용-도입-순서)
- [기억할 기준](#기억할-기준)

</details>

> 관련 문서:
> - [Software Engineering README: Query Model Separation for Read-Heavy APIs](./README.md#query-model-separation-for-read-heavy-apis)
> - [DAO vs Query Model Entrypoint](./dao-vs-query-model-entrypoint-primer.md)
> - [Persistence Follow-up Question Guide](./persistence-follow-up-question-guide.md)
> - [Helper Snapshot Bloat Vs Response DTO Separation](./helper-snapshot-bloat-vs-response-dto-separation.md)
> - [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)
> - [JPA Lazy Loading and N+1 Boundary Smells](./jpa-lazy-loading-n-plus-one-boundary-smells.md)
> - [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [Event Sourcing, CQRS Adoption Criteria](./event-sourcing-cqrs-adoption-criteria.md)
> - [Record and Value Object Equality](../language/java/record-value-object-equality-basics.md)
>
> retrieval-anchor-keywords: query model separation, read-heavy api, cqrs lite, dedicated query repository, query repository, read model separation, response model separation, list detail api model, projection repository, aggregate vs projection, write entity stretching, list screen query model, detail screen query model, beginner cqrs lite, same database read model, helper snapshot bloat, helper snapshot vs response dto, command support data, dao vs query model, query repository 언제 쓰는지, read model 언제 필요해요, query model과 response model 차이, write model read model 차이, 목록 api에서 엔티티가 비대해져요, 조회 화면 때문에 repository 메서드가 많아져요, 처음 query model 헷갈림, query model 첫 질문, read model 큰 그림

## 왜 헷갈리는가

처음 CRUD를 만들 때는 `OrderEntity`나 `Order` 하나로도 충분해 보인다.

- 저장할 때도 쓴다
- 상세 조회에도 쓴다
- 목록 응답에도 재활용한다

문제는 목록 화면과 상세 화면이 커질수록 "읽기 요구"가 write model을 끌고 다니기 시작한다는 점이다.

- 목록 화면은 합계, 개수, 상태 라벨, 검색용 조인이 필요하다
- 상세 화면은 연관 엔티티와 설명 필드가 더 많이 필요하다
- 쓰기 모델은 취소 가능 여부, 주소 변경 규칙 같은 불변식을 지켜야 한다

즉 세 요구는 서로 바뀌는 이유가 다르다.

- write model은 규칙 때문에 바뀐다
- query model은 화면과 조회 성능 때문에 바뀐다
- response model은 외부 API 계약 때문에 바뀐다

이 셋을 한 클래스에 몰아넣으면 "조회 편의용 필드"와 "상태 변경 규칙"이 서로를 망가뜨리기 쉽다.

## 한 장으로 보는 세 모델

| 모델 | 답해야 하는 질문 | 잘 어울리는 예 | 여기 넣지 않는 편이 좋은 것 |
|---|---|---|---|
| Write model | "이 변경이 규칙을 지키나?" | `Order`, `OrderRepository`, `cancel()`, `changeAddress()` | 목록 컬럼, 검색 정렬 전용 값, 화면용 별칭 |
| Query model | "이 화면이 빨리 읽어야 하는 값이 뭔가?" | `OrderSummaryView`, `OrderDetailView`, `OrderQueryRepository` | 상태 변경 메서드, dirty checking 전제 |
| Response model | "외부에 어떤 계약으로 보여줄까?" | `OrderSummaryResponse`, `OrderDetailResponse` | ORM 어노테이션, SQL alias, 내부 조인 구조 |

핵심은 "클래스 수를 늘리는 것"이 아니라 "변경 이유를 섞지 않는 것"이다.

- query model은 조회를 빠르고 단순하게 만든다
- response model은 API 계약을 보호한다
- write model은 규칙을 지키는 데 집중한다

query model과 response model은 모양이 비슷할 수 있다.
그래도 둘을 개념적으로 구분해 두면, 나중에 API 필드 이름이나 외부 계약이 바뀌어도 SQL projection을 덜 흔들 수 있다.
Java에서 `query view`나 `response model`을 `record`로 둘 계획이라면, 값 의미와 동등성 감각은 [Record and Value Object Equality](../language/java/record-value-object-equality-basics.md)로 이어 보면 덜 섞인다.

## 언제 query repository를 꺼낼까

아래 신호가 2~3개 이상 겹치면 write model을 늘리는 대신 query 경로 분리를 검토할 시점이다.

| 신호 | 왜 분리 신호인가 |
|---|---|
| 목록 API와 상세 API가 같은 엔티티를 억지로 공유한다 | 화면마다 필요한 필드와 조인이 다르다 |
| 엔티티에 `itemCount`, `totalPrice`, `memberName` 같은 조회 전용 값이 계속 붙는다 | aggregate 규칙보다 화면 요구가 모델을 밀고 있다 |
| repository 메서드가 `findAllForList`, `findAllForAdmin`, `findDetailWithEverything`처럼 화면별로 비대해진다 | 읽기 전략이 write repository를 잠식한다 |
| 읽기 트래픽이 쓰기보다 훨씬 많다 | 읽기 전용 최적화 경로의 비용 대비 효과가 커진다 |
| `fetch join`과 projection 선택이 유스케이스 규칙보다 더 자주 논의된다 | 도메인보다 조회 구조가 더 큰 설계 압력이 됐다 |
| 목록에서는 필요 없는 상세 연관관계까지 항상 로딩한다 | aggregate 복원이 과한 읽기 비용을 만든다 |

짧게 외우면 이렇다.

- 규칙 검증이면 write model
- 목록/검색/대시보드면 query model
- 외부 JSON 계약이면 response model

## 언제 아직 과한가

반대로 아래 상황이면 아직은 별도 query repository가 과할 수 있다.

- 단건 상세 API 몇 개만 있고 목록/검색이 거의 없다
- 읽기 요구가 단순해서 aggregate를 읽어도 비용이 크지 않다
- 화면별 차이가 거의 없어 응답 DTO만 분리해도 충분하다
- 팀이 아직 repository/entity/DTO 경계도 정리하지 못했다

이 경우에는 보통 이 순서면 충분하다.

1. 엔티티를 API 응답으로 직접 내보내지 않는다.
2. 응답 DTO를 먼저 분리한다.
3. 그래도 조회 전용 요구가 계속 불어나면 query repository를 추가한다.

즉 full CQRS를 선포하는 것이 목적이 아니라, 읽기 경로가 write model을 망가뜨리기 시작했는지를 보는 게 먼저다.

## Before: write entity 하나로 목록과 상세를 모두 버틴다

```java
@Entity
public class OrderEntity {
    @Id
    private Long id;

    private String status;
    private String memberName;
    private int itemCount;
    private BigDecimal totalPrice;
    private String lastPaymentType;

    @OneToMany(mappedBy = "order")
    private List<OrderLineEntity> lines = new ArrayList<>();

    public void cancel() {
        if ("SHIPPED".equals(status)) {
            throw new IllegalStateException("already shipped");
        }
        this.status = "CANCELLED";
    }
}

public interface OrderJpaRepository extends JpaRepository<OrderEntity, Long> {
    @EntityGraph(attributePaths = {"lines", "member", "payment"})
    Optional<OrderEntity> findDetailById(Long id);

    @Query("""
            select o
            from OrderEntity o
            left join fetch o.member
            left join fetch o.payment
            """)
    List<OrderEntity> findAllForList();
}

public record OrderSummaryResponse(
        Long id,
        String status,
        String memberName,
        int itemCount,
        BigDecimal totalPrice
) {
    static OrderSummaryResponse from(OrderEntity entity) {
        return new OrderSummaryResponse(
                entity.getId(),
                entity.getStatus(),
                entity.getMemberName(),
                entity.getItemCount(),
                entity.getTotalPrice()
        );
    }
}
```

처음엔 빨라 보이지만 곧 이런 냄새가 붙는다.

## Before: write entity 하나로 목록과 상세를 모두 버틴다 (계속 2)

- 주문 규칙을 담는 객체가 목록 컬럼 요구까지 같이 떠안는다
- 목록과 상세가 서로 다른 조인 전략을 요구하면서 repository가 화면별 메서드 창고가 된다
- 응답 필드 하나를 바꿀 때 엔티티와 쿼리 메서드까지 같이 흔들린다
- `OrderEntity`가 "쓰기 모델"인지 "목록 projection"인지 애매해진다

## After: CQRS-lite로 읽기 경로만 분리한다

핵심은 거창한 이벤트 소싱이 아니다.
같은 DB, 같은 애플리케이션 안에서도 읽기 경로만 분리할 수 있다.

## After: CQRS-lite로 읽기 경로만 분리한다 (계속 2)

```java
public interface OrderRepository {
    Order get(OrderId id);
    void save(Order order);
}

public interface OrderQueryRepository {
    Page<OrderSummaryView> findSummaries(OrderSearchCondition condition, Pageable pageable);
    Optional<OrderDetailView> findDetail(OrderId id);
}

public record OrderSummaryView(
        Long id,
        String status,
        String memberName,
        int itemCount,
        BigDecimal totalPrice
) {
}

public record OrderDetailView(
        Long id,
        String status,
        String memberName,
        String shippingAddress,
        List<OrderLineView> lines,
        BigDecimal totalPrice
) {
}

public record OrderSummaryResponse(
        Long id,
        String status,
        String customer,
        int itemCount,
        BigDecimal totalPrice
) {
    static OrderSummaryResponse from(OrderSummaryView view) {
        return new OrderSummaryResponse(
                view.id(),
                view.status(),
                view.memberName(),
                view.itemCount(),
                view.totalPrice()
        );
    }
}

@Service
@Transactional(readOnly = true)
public class OrderQueryService {
    private final OrderQueryRepository orderQueryRepository;

    public Page<OrderSummaryResponse> findSummaries(
            OrderSearchCondition condition,
            Pageable pageable
    ) {
        return orderQueryRepository.findSummaries(condition, pageable)
                .map(OrderSummaryResponse::from);
    }
}
```

## After: CQRS-lite로 읽기 경로만 분리한다 (계속 3)

이 구조에서 각 책임은 이렇게 나뉜다.

- `OrderRepository`: aggregate를 읽고 저장하며 규칙 검증을 돕는다
- `OrderQueryRepository`: 목록/상세 화면에 맞는 projection을 읽는다
- `OrderSummaryView`, `OrderDetailView`: 읽기 최적화용 내부 모델이다
- `OrderSummaryResponse`: 외부 API 계약을 표현한다

여기서 중요한 점은 두 가지다.

1. query repository가 write repository를 대체하는 것이 아니다.
2. query model을 만든다고 해서 event sourcing이나 비동기 projection이 반드시 필요한 것도 아니다.

즉 이 문서의 분리는 "full CQRS"가 아니라 **CQRS-lite**다.

- write path는 aggregate 중심으로 유지한다
- read path는 projection 중심으로 분리한다
- 둘 다 같은 트랜잭션 DB를 써도 괜찮다

## 초심자용 도입 순서

복잡도를 한 번에 올리지 말고 아래 순서로 자르는 편이 안전하다.

1. 컨트롤러에서 엔티티를 직접 반환하지 않고 response model을 먼저 만든다.
2. 목록과 상세가 같은 응답 타입을 억지로 공유하고 있다면 두 response model을 나눈다.
3. write repository는 그대로 두고, 읽기 전용 `QueryRepository`를 별도로 만든다.
4. query repository는 aggregate 대신 projection/view를 반환하게 한다.
5. 읽기 모델이 캐시, 비동기 projection, 별도 저장소까지 필요해질 때만 그다음 CQRS 단계를 고민한다.

초심자에게는 3번까지만 해도 효과가 크다.
대부분의 문제는 "쓰기 모델을 화면별 조회 요구에서 해방하는 것"만으로 많이 줄어든다.

## 기억할 기준

- aggregate는 규칙을 지키기 위한 모델이지, 모든 목록/상세 화면을 먹여 살리는 만능 DTO가 아니다
- read-heavy API는 write model을 늘리는 대신 query repository와 projection을 먼저 의심한다
- response model은 query model과 비슷해 보여도 외부 계약이라는 별도 변경 이유를 가진다
- 같은 DB 위의 query 분리만으로도 충분한 경우가 많다
- CQRS-lite의 출발점은 유행어가 아니라 "읽기 요구가 write model을 망가뜨리고 있는가"라는 질문이다

## 다음 읽기

이 문서는 "query model을 왜 나누는가"까지 잡는 primer다. 여기서 더 내려갈 때도 아래처럼 한 칸씩만 붙이면 초심자 route가 무너지지 않는다.

| 지금 남은 질문 | 다음 문서 |
|---|---|
| "분리는 알겠는데 출발 판단이 아직 헷갈린다" | [DAO vs Query Model Entrypoint](./dao-vs-query-model-entrypoint-primer.md) |
| "같은 DB query repository로 끝낼지, read store를 따로 둘지 궁금하다" | [Same-DB Query Repository Vs Separate Read Store](./same-db-query-repository-vs-separate-read-store.md) |
| "query view와 response DTO가 비슷해 보여서 다시 섞인다" | [Helper Snapshot Bloat Vs Response DTO Separation](./helper-snapshot-bloat-vs-response-dto-separation.md) |
| "조회 경로 분리 때문에 entity 누수와 lazy loading 경계도 같이 보고 싶다" | [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md), [JPA Lazy Loading and N+1 Boundary Smells](./jpa-lazy-loading-n-plus-one-boundary-smells.md) |

README 기반 persistence route로 복귀하려면 여기서 다시 시작하면 된다: [Software Engineering README](./README.md#query-model-separation-for-read-heavy-apis)

## 한 줄 정리

목록/상세 화면이 많아질수록 write entity나 aggregate 하나로 모든 읽기 요구를 버티기보다, 같은 DB 위에서도 query repository와 response model을 따로 두는 CQRS-lite가 더 단순할 때가 많다.
