# Persistence Adapter Mapping Checklist

> 한 줄 요약: domain object와 JPA entity를 같은 모델로 밀어붙이지 말고, repository port는 도메인 언어를 유지한 채 persistence adapter가 매핑과 ORM 세부를 바깥에서 감싸는지 점검하는 짧은 체크리스트다.

**난이도: 🟢 Beginner**

[30분 후속 분기표로 돌아가기](./common-confusion-wayfinding-notes.md#자주-헷갈리는-3개-케이스)

<details>
<summary>Table of Contents</summary>

- [언제 꺼내보면 좋은가](#언제-꺼내보면-좋은가)
- [먼저 떠올릴 1분 모델](#먼저-떠올릴-1분-모델)
- [짧은 체크리스트](#짧은-체크리스트)
- [30초 before/after 비교](#30초-beforeafter-비교)
- [코드에 꽂아 보면](#코드에-꽂아-보면)
- [누수 경보 신호](#누수-경보-신호)
- [자주 헷갈리는 지점](#자주-헷갈리는-지점)
- [기억할 기준](#기억할-기준)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)

</details>

> 관련 문서:
> - [Software Engineering README: Persistence Adapter Mapping Checklist](./README.md#persistence-adapter-mapping-checklist)
> - [Persistence Follow-up Question Guide](./persistence-follow-up-question-guide.md)
> - [Repository Interface Contract Primer](./repository-interface-contract-primer.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [Aggregate Persistence Mapping Pitfalls](./aggregate-persistence-mapping-pitfalls.md)
> - [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)
> - [JPA Lazy Loading and N+1 Boundary Smells](./jpa-lazy-loading-n-plus-one-boundary-smells.md)
> - [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)
> - [Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md)
> - [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
> - [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)
> - [Repository Fake Design Guide](./repository-fake-design-guide.md)
> - [Design Pattern: Repository Boundary: Aggregate Persistence vs Read Model](../design-pattern/repository-boundary-aggregate-vs-read-model.md)
> - [Design Pattern: Anti-Corruption Adapter Layering](../design-pattern/anti-corruption-adapter-layering.md)
> - [System Design: Change Data Capture / Outbox Relay 설계](../system-design/change-data-capture-outbox-relay-design.md)
> - [System Design: Zero-Downtime Schema Migration Platform 설계](../system-design/zero-downtime-schema-migration-platform-design.md)
>
> retrieval-anchor-keywords: persistence adapter mapping checklist, domain object to jpa entity, jpa entity mapper checklist, repository adapter mapping, repository interface contract, repository implementation contract, orm concern leakage, aggregate mapping checklist, aggregate persistence mapping pitfalls, bidirectional association mapping, cascade type all boundary, orphanRemoval boundary, hexagonal persistence adapter, domain repository port, fetch cascade dirty checking boundary, domain model vs jpa entity, fetch join boundary, lazy loading boundary, n+1 query boundary, projection vs aggregate read, managed entity collection diff, adapter bulk optimization without port leakage, JPA batch inside adapter, hibernate batch settings boundary, jpa batch config pitfalls, identity generation persistence concern, flush timing boundary, JDBC batch adapter, saveAll as adapter detail, repository boundary read model, anti corruption adapter layering, cdc outbox relay handoff, schema migration mapping bridge, persistence cross-category bridge, beginner repository mapping mental model, entity mapper responsibility split, domain to entity translation checklist, persistence follow-up question guide, entity leakage 다음 문서

Repository 경계를 아직 "구현 교체 계약"으로 못 읽겠다면 [Repository Interface Contract Primer](./repository-interface-contract-primer.md)로 먼저 큰 그림을 잡고, 이 문서는 그다음 체크리스트로 쓰는 편이 자연스럽다.

repository 경계가 조회 모델, 외부 모델 번역, relay/cutover 운영까지 넓어지기 시작하면 [Design Pattern: Repository Boundary: Aggregate Persistence vs Read Model](../design-pattern/repository-boundary-aggregate-vs-read-model.md), [Design Pattern: Anti-Corruption Adapter Layering](../design-pattern/anti-corruption-adapter-layering.md)로 경계 언어를 먼저 고정하는 편이 좋다.
그다음 실제 데이터 이동과 호환성 창은 [System Design: Change Data Capture / Outbox Relay 설계](../system-design/change-data-capture-outbox-relay-design.md), [System Design: Zero-Downtime Schema Migration Platform 설계](../system-design/zero-downtime-schema-migration-platform-design.md)로 이어서 보면 된다.

## 언제 꺼내보면 좋은가

아래처럼 저장 계층을 손볼 때 이 체크리스트를 같이 보면 경계가 덜 무너진다.

- `OrderRepository` 같은 outbound port를 새로 만들 때
- 기존 서비스가 `OrderJpaRepository`를 직접 주입받고 있을 때
- `@Entity`에 비즈니스 규칙과 API 요구가 같이 몰리기 시작했을 때
- aggregate 저장 로직이 커져서 mapper, fetch 전략, cascade 판단이 섞일 때

핵심 질문은 하나다.

- "이 결정이 도메인 규칙인가, 아니면 ORM이 편해지기 위한 결정인가?"

ORM 편의 때문에 생긴 결정이라면 adapter 쪽으로 밀어내는 편이 안전하다.

## 먼저 떠올릴 1분 모델

초심자에게는 repository 경계를 "통역"으로 떠올리면 쉽다.

- 안쪽(application/domain): 비즈니스 언어로 말한다 (`Order`, `OrderId`, `Money`)
- 바깥(adapter): DB 언어로 번역한다 (`OrderEntity`, FK, fetch 전략)

즉 repository port는 "무슨 뜻인지"를 약속하고, persistence adapter는 "어떻게 저장할지"를 숨긴다.

경계가 흔들릴 때는 아래 한 줄로 점검하면 된다.

- "지금 내가 고민하는 건 규칙인가, 아니면 ORM 사용법인가?"

ORM 사용법이면 대개 adapter concern이다.

## 짧은 체크리스트

| 체크 질문 | 괜찮은 상태 | 누수 신호 |
|---|---|---|
| repository port가 어떤 타입으로 말하나 | `Order`, `OrderId`, `Money` 같은 도메인 타입을 주고받는다 | `OrderEntity`, `Page<OrderEntity>`, `JpaRepository` 타입이 application 안쪽으로 들어온다 |
| domain model이 JPA를 알고 있나 | 도메인 객체에 규칙과 불변식만 있다 | `@Entity`, `@OneToMany`, `FetchType.LAZY`, 기본 생성자 요구가 도메인에 스며든다 |
| 매핑 책임이 어디 있나 | `OrderEntityMapper`나 adapter 내부 변환 메서드가 `Order <-> OrderEntity`를 담당한다 | 서비스, 컨트롤러, 엔티티 메서드에 변환 코드가 흩어진다 |
| 저장 최적화 규칙이 어디 있나 | FK, nullable, version, orphan 처리 같은 결정이 entity/adapter에 머문다 | 도메인 메서드가 cascade, dirty checking, lazy loading 전제를 직접 가진다 |
| 조회 최적화 요구를 어떻게 다루나 | fetch join, entity graph, projection은 adapter나 query model에서 처리한다 | 목록 화면 요구 때문에 aggregate나 entity 필드가 계속 부풀어 오른다 |
| 테스트가 무엇을 검증하나 | mapper unit test와 repository integration test가 round-trip과 불변식 복원을 본다 | 유스케이스 테스트가 JPA flush 타이밍이나 프록시 초기화를 알아야만 통과한다 |

짧게 외우면 이 순서다.

1. 안쪽은 도메인 언어로 말한다.
2. 바깥 adapter가 JPA entity로 번역한다.
3. fetch, cascade, dirty checking 같은 ORM 최적화는 번역 바깥으로 새지 않게 막는다.

## 30초 before/after 비교

| 상황 | before (누수) | after (경계 유지) |
|---|---|---|
| 서비스 의존 | `OrderJpaRepository` 직접 주입 | `OrderRepository` port 의존 |
| 유스케이스 입력/출력 타입 | `OrderEntity`, `Page<OrderEntity>` | `Order`, `OrderId`, 필요 시 읽기 DTO |
| 변경 코드 위치 | 서비스/컨트롤러에서 `entity.setXxx()` | adapter mapper에서 `domain <-> entity` 변환 |
| 성능 튜닝 반영 | use case가 `flush`, `LAZY`를 안다 | adapter가 fetch/join/batch를 선택 |

before에서 after로 가는 첫 단추는 "서비스에서 JPA 타입 이름을 지우는 것"이다.

## 코드에 꽂아 보면

```java
public interface OrderRepository {
    Order get(OrderId id);
    void save(Order order);
}

@Entity
class OrderJpaEntity {
    @Id
    private Long id;

    @Version
    private Long version;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderLineJpaEntity> lines = new ArrayList<>();
}

@Component
class JpaOrderRepositoryAdapter implements OrderRepository {
    private final SpringDataOrderJpaRepository jpaRepository;
    private final OrderEntityMapper mapper;

    @Override
    public Order get(OrderId id) {
        OrderJpaEntity entity = jpaRepository.findById(id.value())
                .orElseThrow();
        return mapper.toDomain(entity);
    }

    @Override
    public void save(Order order) {
        OrderJpaEntity entity = jpaRepository.findById(order.id().value())
                .orElseGet(() -> mapper.newEntity(order));

        mapper.copyIntoManagedEntity(order, entity);
        jpaRepository.save(entity);
    }
}
```

이 구조에서 안쪽이 지키는 것은 `OrderRepository`뿐이다.
반대로 아래 판단은 adapter가 가진다.

- 어떤 연관관계를 fetch join으로 읽을지
- 기존 managed entity에 덮어쓸지, 새 entity를 만들지
- `@Version`, `orphanRemoval`, FK 구조를 어떻게 맞출지

특히 aggregate 수정 시 `copyIntoManagedEntity(...)` 같은 방식이 필요한 이유는, 자식 컬렉션 identity와 orphan 처리 규칙이 JPA 세부이기 때문이다.
그 복잡도를 도메인 객체가 알기 시작하면 "규칙 모델"이 아니라 "영속성 컨텍스트 사용 설명서"가 된다.

## 누수 경보 신호

아래 항목이 반복되면 mapping 경계가 흔들리는 쪽이다.

- application service가 `springDataRepository.findById()` 후 `entity.setXxx()`를 직접 호출한다
- 도메인 규칙 설명보다 `LAZY 초기화`, `cascade`, `flush` 타이밍 설명이 더 자주 나온다
- 컨트롤러 응답이나 use case 반환 타입에 `@Entity`가 그대로 등장한다
- mapping 코드가 한 파일에 있지 않고 service, controller, entity helper로 흩어진다
- 읽기 화면 요구 때문에 aggregate가 "규칙 모델"보다 "목록 컬럼 묶음"에 가까워진다

## 자주 헷갈리는 지점

- "JPA를 쓰는데 도메인 객체에 어노테이션이 조금 있어도 괜찮지 않나?"
  - 한두 개로 시작해도 결국 fetch/cascade 결정이 규칙 코드에 스며든다. 도메인은 ORM 용어를 모르게 두는 편이 장기적으로 안전하다.
- "성능 때문에 `Page<OrderEntity>`를 바로 반환해야 빠른 것 아닌가?"
  - 빠른 것과 경계가 안전한 것은 별개다. adapter/query model에서 projection으로 해결하고 port는 도메인 언어를 유지할 수 있다.
- "매핑 코드가 번거로워서 서비스에서 바로 변환하면 안 되나?"
  - 변환 위치가 흩어지면 누락/불일치가 생긴다. mapper를 adapter에 모아 테스트 가능한 한 곳으로 유지하는 편이 낫다.
- "테스트에서 JPA 세부를 아는 게 왜 문제인가?"
  - 유스케이스 테스트가 ORM 동작에 잠기면 구현 교체 비용이 급증한다. 유스케이스는 의미를, adapter 테스트는 ORM 세부를 검증하도록 분리한다.

## 기억할 기준

- repository port는 도메인 언어를 보존하는 창구다
- JPA entity는 저장 전략을 표현하는 객체이지, 안쪽 전체가 공유할 대표 모델이 아니다
- domain object를 JPA에 맞추기보다 adapter가 두 모델 사이를 번역하게 두는 편이 장기적으로 덜 아프다
- ORM 세부를 안쪽으로 밀어 넣는 순간 테스트와 규칙 설명이 함께 무거워진다

## 다음에 이어서 볼 문서

- 누수 신호를 anti-pattern 중심으로 더 보려면: [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)
- 연관관계/cascade 함정을 더 자세히 보려면: [Aggregate Persistence Mapping Pitfalls](./aggregate-persistence-mapping-pitfalls.md)
- batch 최적화를 경계 밖으로 유지하려면: [Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md)
- 읽기 요구 때문에 모델이 부풀 때는: [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
