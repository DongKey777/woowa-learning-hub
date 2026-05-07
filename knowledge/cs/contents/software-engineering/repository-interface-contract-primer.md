---
schema_version: 3
title: Repository Interface Contract Primer
concept_id: software-engineering/repository-interface-contract-primer
canonical: true
category: software-engineering
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- repository-interface-contract
- repository-interface
- repository-contract
- repository-port
aliases:
- repository interface
- repository contract
- 영속성 인터페이스 추상화
- 도메인 객체 영속성
- repository port
- jparepository 인터페이스 차이
- 왜 repository를 인터페이스로
intents:
- definition
- design
linked_paths:
- contents/software-engineering/repository-dao-entity.md
- contents/software-engineering/persistence-follow-up-question-guide.md
- contents/software-engineering/persistence-adapter-mapping-checklist.md
- contents/software-engineering/ports-and-adapters-beginner-primer.md
- contents/spring/spring-data-jpa-basics.md
expected_queries:
- repository 인터페이스가 왜 필요해?
- repository는 왜 interface로 만들어?
- DAO랑 Repository는 뭐가 달라?
- JpaRepository를 왜 그대로 노출하지 않아야 해?
contextual_chunk_prefix: |
  이 문서는 학습자가 도메인 객체의 영속성 처리를 인터페이스로 추상화하는
  패턴이 무엇인지, 왜 application/domain이 직접 DB API를 쓰는 대신 저장소
  계약을 두고 구현체를 갈아끼우는지 처음 이해하는 primer다. 도메인 객체
  영속성 처리, 인터페이스로 추상화하는 패턴, 왜 repository를 interface로,
  JPA/MyBatis 구현체 교체, ports & adapters 같은 자연어 paraphrase가 본
  문서의 핵심 약속에 매핑된다.
---
# Repository Interface Contract Primer

> 한 줄 요약: Repository 인터페이스는 "DB 코드를 감추는 장식"이 아니라 application/domain이 기대하는 저장 약속이고, JPA/MyBatis/JDBC 구현체는 그 약속을 맞춰 끼우는 교체 부품이다.

**난이도: 🟢 Beginner**

## 미션 진입 증상

| persistence 장면 | 먼저 볼 contract |
|---|---|
| Service가 `JpaRepository` 세부 메서드에 직접 의존한다 | domain/application 저장 약속이 있는가 |
| DAO와 Repository를 같은 이름으로 쓰며 역할이 섞인다 | SQL access와 domain persistence 계약을 나눴는가 |
| 테스트에서 DB 없이 저장소 규칙을 바꾸고 싶다 | interface/fake 경계가 필요한가 |
| Entity mapping 변경에 use case 코드가 같이 흔들린다 | persistence adapter가 내부 세부를 숨기는가 |

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡는 한 줄 멘탈 모델](#먼저-잡는-한-줄-멘탈-모델)
- [before / after 한눈 비교](#before--after-한눈-비교)
- [Repository 인터페이스, 구현체, DAO를 한 표로 보기](#repository-인터페이스-구현체-dao를-한-표로-보기)
- [코드로 보면 어디가 계약이고 어디가 구현인가](#코드로-보면-어디가-계약이고-어디가-구현인가)
- [언제 인터페이스를 두고 언제 클래스로 충분한가](#언제-인터페이스를-두고-언제-클래스로-충분한가)
- [contract 질문 vs persistence 질문 30초 분기](#contract-질문-vs-persistence-질문-30초-분기)
- [흔한 오해와 함정](#흔한-오해와-함정)
- [다음에 읽을 문서](#다음에-읽을-문서)
- [한 줄 정리](#한-줄-정리)

</details>

관련 문서:

- [Software Engineering README: Repository Interface Contract Primer](./README.md#repository-interface-contract-primer)
- [Repository, DAO, Entity](./repository-dao-entity.md)
- [Persistence Follow-up Question Guide](./persistence-follow-up-question-guide.md)
- [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
- [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
- [Java 타입, 클래스, 객체, OOP 입문](../language/java/java-types-class-object-oop-basics.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

retrieval-anchor-keywords: repository interface beginner, repository interface contract, repository interface vs implementation, repository port beginner, dao vs repository interface, spring data jpa repository interface, domain repository contract, repository adapter beginner, 왜 repository를 인터페이스로 만들어요, repository가 interface인 이유, 처음 배우는데 repository interface 뭐예요, 처음 배우는데 왜 구현체가 또 있죠, repository interface 언제 쓰는지, jparepository랑 repository interface 차이, 인터페이스 왜 쓰는지 저장소 예시

처음 배우는데 "왜 `Repository`를 인터페이스로 두고 구현체를 갈아끼운다고 말하지?"가 제일 막힌다면, 이 문서를 `왜 repository를 interface로 만들어요?` 같은 첫 질문을 받았을 때 가장 먼저 닿아야 하는 큰 그림 entrypoint로 잡고 나서 [Repository, DAO, Entity](./repository-dao-entity.md)와 [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)로 내려가면 된다.
`interface`라는 단어 자체가 아직 낯설면 [Java 타입, 클래스, 객체, OOP 입문](../language/java/java-types-class-object-oop-basics.md)에서 계약과 구현을 나누는 감각을 먼저 잡고 돌아오면 덜 헷갈린다.

## 왜 이 문서가 필요한가

초심자는 보통 이런 장면에서 한 번에 헷갈린다.

- `OrderRepository`는 인터페이스인데 왜 구현 클래스가 또 있지?
- Spring Data `JpaRepository`도 인터페이스인데, 이게 domain repository랑 같은 말인가?
- DAO도 인터페이스로 만들어야 하나?
- 테스트용 fake repository 때문에 인터페이스를 두는 건가?

이 질문들을 한 줄로 묶으면 이렇다.

- **Repository 인터페이스는 "바꿔 끼울 구현 목록"이 아니라, 안쪽 코드가 믿는 저장 계약이다.**

즉 핵심은 "인터페이스를 썼다"가 아니라 "어느 경계에서 어떤 약속을 고정했느냐"다.

## 먼저 잡는 한 줄 멘탈 모델

처음에는 콘센트와 플러그 비유로 보는 편이 빠르다.

- `Repository 인터페이스`는 콘센트 모양이다.
- `JPA/MyBatis/JDBC 구현체`는 그 콘센트에 맞춰 꽂는 플러그다.
- `Service`나 `UseCase`는 전기를 쓰는 가전제품처럼 콘센트 모양만 안다.

그래서 안쪽 코드는 이렇게 생각한다.

- "주문을 저장할 수 있어야 한다"
- "주문을 ID로 찾을 수 있어야 한다"

반면 구현체는 이렇게 생각한다.

- "JPA로 저장할까"
- "MyBatis SQL로 읽을까"
- "테스트에서는 메모리 fake로 대신할까"

정리하면:

- **인터페이스는 무엇을 약속하는가**
- **구현체는 그 약속을 어떤 기술로 지키는가**

를 나눈 것이다.

## before / after 한눈 비교

| 상태 | 코드 신호 | 결과 |
|---|---|---|
| before: 저장 기술과 유스케이스 계약이 한 덩어리 | service가 `JpaRepository`, SQL 컬럼 이름, 매퍼 세부를 직접 안다 | 구현 교체와 테스트 대체가 service 수정으로 번진다 |
| after: repository 인터페이스가 안쪽 계약을 고정 | service는 `OrderRepository`만 보고 adapter가 JPA/MyBatis/JDBC를 맞춘다 | 저장 기술 변경과 fake 대체가 adapter 경계 안에서 끝난다 |

## Repository 인터페이스, 구현체, DAO를 한 표로 보기

| 이름 | 초심자용 한 문장 | 보통 위치 | 언제 바뀌기 쉬운가 |
|---|---|---|---|
| `OrderRepository` 인터페이스 | 유스케이스가 기대하는 저장 계약 | domain/application 경계 | 비즈니스가 요구하는 조회/저장 의미가 바뀔 때 |
| `JpaOrderRepositoryAdapter` 구현체 | JPA로 그 계약을 지키는 어댑터 | infrastructure/adapter | ORM, DB, 매핑 전략이 바뀔 때 |
| `OrderDao` | 테이블/SQL 중심의 더 낮은 수준 도구 | adapter 내부 | 쿼리 최적화나 테이블 구조가 바뀔 때 |
| `SpringDataOrderJpaRepository` | 프레임워크가 제공하는 repository interface | framework adapter 내부 | Spring Data 사용 방식이 바뀔 때 |

여기서 초심자가 가장 많이 놓치는 포인트는 이것이다.

- `Repository 인터페이스`는 **도메인/유스케이스 언어**로 말한다.
- `DAO`는 **테이블/SQL 언어**로 말한다.
- `Spring Data repository interface`는 **프레임워크 언어**로 말한다.

셋 다 "인터페이스"일 수는 있지만, **같은 경계의 인터페이스는 아니다.**

## 코드로 보면 어디가 계약이고 어디가 구현인가

```java
// application/domain boundary
public interface OrderRepository {
    Optional<Order> findById(OrderId id);
    void save(Order order);
}

// infrastructure adapter
@Component
class JpaOrderRepositoryAdapter implements OrderRepository {
    private final SpringDataOrderJpaRepository jpaRepository;
    private final OrderEntityMapper mapper;

    @Override
    public Optional<Order> findById(OrderId id) {
        return jpaRepository.findById(id.value())
                .map(mapper::toDomain);
    }

    @Override
    public void save(Order order) {
        jpaRepository.save(mapper.toEntity(order));
    }
}

// adapter-internal helper
interface SpringDataOrderJpaRepository
        extends JpaRepository<OrderEntity, Long> {
}
```

이 코드를 beginner 눈높이로 읽으면 된다.

- `OrderRepository`는 서비스가 믿는 약속이다.
- `JpaOrderRepositoryAdapter`는 "그 약속을 JPA로 구현한 클래스"다.
- `SpringDataOrderJpaRepository`는 adapter가 프레임워크와 대화할 때 쓰는 도구다.

즉 service는 `JpaRepository`를 직접 알 필요가 없다.
service는 "주문을 저장/조회할 수 있다"는 계약만 알면 된다.

## 언제 인터페이스를 두고 언제 클래스로 충분한가

모든 곳에 인터페이스를 만들 필요는 없다.
중요한 것은 **교체 가능성이 아니라 경계의 계약이 필요한가**다.

### 인터페이스를 두는 편이 좋은 경우

- application/domain이 바깥 저장 기술을 직접 모르도록 막고 싶을 때
- 같은 유스케이스 계약에 대해 JPA 구현, JDBC 구현, fake 구현이 자연스럽게 생길 수 있을 때
- 테스트에서 "DB 흉내"가 아니라 "저장 계약"만 재현하고 싶을 때
- 팀이 `OrderRepository`라는 이름으로 비즈니스 의미를 먼저 합의해야 할 때

### 클래스로 충분한 경우

- DAO가 adapter 내부 helper일 뿐이고 바깥에서 그 이름의 계약을 직접 쓰지 않을 때
- SQL 한두 개를 감싼 작은 구현 클래스라 굳이 별도 계약을 노출할 필요가 없을 때
- 아직 저장 경계 자체가 작고, 유스케이스가 직접 의존할 장기 계약이 보이지 않을 때

초심자용 기준으로 더 짧게 말하면:

- `Repository interface`는 **안쪽이 의존하는 계약**
- `DAO class`는 **바깥 구현을 돕는 부품**

인 경우가 많다.

## contract 질문 vs persistence 질문 30초 분기

`Repository Interface Contract Primer`를 읽고 나면 초심자는 종종 "`그래서 다음에 fake를 보나요, JPA를 더 보나요?`"에서 다시 멈춘다.
이때는 후속 문서를 3갈래로만 보면 된다.

- **fake 문서로 간다**: "`이 저장 계약을 test에서 어떻게 재현하지?`"가 막힐 때
- **mapping 문서로 간다**: "`domain`과 `Entity`를 어디서 나누지?`"가 막힐 때
- **leakage 문서로 간다**: "`서비스/API에 `Entity`가 보이는데 이게 왜 문제지?`"가 막힐 때

즉 초심자 기준 후속 선택표는 "`계약 재현` vs `매핑 경계` vs `ORM 누수`" 3갈래로 읽으면 된다.

| 지금 막힌 질문 | 먼저 볼 문서 | 이유 |
|---|---|---|
| "`Service`가 repository에 정확히 무엇을 기대해야 하지?", "`fake`도 이 계약만 재현하면 되나?" | [Repository Fake Design Guide](./repository-fake-design-guide.md) | fake는 "`DB 없이도 저장 계약을 어떻게 재현할까`"라는 contract 질문의 다음 단계다 |
| "`flush`, dirty checking, `cascade`, `Entity` 매핑은 어디서 다뤄야 하지?" | [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md) | 이쪽은 fake보다 persistence adapter와 ORM 번역 규칙 질문에 가깝다 |
| "`Service`에 `Entity`가 보이는데 이게 괜찮나?" | [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md) | 계약 자체보다 ORM 세부가 바깥으로 샌 상태를 먼저 보는 편이 빠르다 |

짧게 정리하면:

- `Repository Fake Design Guide`는 **계약을 test에서 어떻게 재현하나**를 이어서 보는 문서다.
- JPA 동작 설명이 더 필요하다면 fake보다 **매핑/누수 문서**로 가는 편이 덜 헷갈린다.

## 흔한 오해와 함정

- "`Repository는 무조건 인터페이스다`"라고 외우기 쉽다.
  - 더 정확히는 "안쪽이 의존할 저장 계약이면 인터페이스가 유용하다"다.
- "`DAO도 인터페이스로 만들어야 하나요?`"라고 묻는다.
  - DAO가 adapter 내부 SQL 도구라면 concrete class여도 충분한 경우가 많다.
- "`테스트 때문에 인터페이스를 만든다`"고 생각한다.
  - 테스트는 부가 이점이고, 먼저는 domain/application이 기술 세부 대신 계약에 의존하게 하려는 것이다.
- "`Spring Data repository interface = domain repository interface`"라고 합쳐서 본다.
  - Spring Data interface는 프레임워크 seam이고, domain repository는 유스케이스 seam이다.
- "`메서드 이름이 테이블과 컬럼 중심인데도 repository라고 부르면 되겠지`"라고 생각한다.
  - `insertGame`, `selectPieceRows`, `updateBoardTable`처럼 SQL/테이블 어휘가 앞서면 DAO 쪽에 더 가깝다.

## 다음에 읽을 문서

- `Repository Interface Contract Primer`를 막 끝냈다면 test 계약 재현은 [Repository Fake Design Guide](./repository-fake-design-guide.md), JPA 번역 경계는 [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md), 서비스/API의 `Entity` 노출은 [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)로 가면 된다.
- 큰 분류부터 다시 잡고 싶다면 [Repository, DAO, Entity](./repository-dao-entity.md)
- repository port와 adapter mapping 경계를 바로 점검하고 싶다면 [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
- repository를 outbound port로 읽는 감각을 넓히고 싶다면 [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
- test fake가 왜 "구현 교체"가 아니라 "계약 재현"인지 보고 싶다면 [Repository Fake Design Guide](./repository-fake-design-guide.md)
- service에 `Entity`가 보이거나 JPA 세부가 밖으로 샌 것 같다면 [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)

## 한 줄 정리

Repository 인터페이스는 "테스트용 인터페이스"가 아니라, application/domain이 저장소에 기대하는 의미를 먼저 고정하는 계약이다.
