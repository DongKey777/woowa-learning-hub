# Repository Interface Contract Primer

> 한 줄 요약: Repository 인터페이스는 "DB 코드를 감추는 장식"이 아니라 application/domain이 기대하는 저장 약속이고, JPA/MyBatis/JDBC 구현체는 그 약속을 맞춰 끼우는 교체 부품이다.

**난이도: 🟢 Beginner**

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡는 한 줄 멘탈 모델](#먼저-잡는-한-줄-멘탈-모델)
- [before / after 한눈 비교](#before--after-한눈-비교)
- [Repository 인터페이스, 구현체, DAO를 한 표로 보기](#repository-인터페이스-구현체-dao를-한-표로-보기)
- [코드로 보면 어디가 계약이고 어디가 구현인가](#코드로-보면-어디가-계약이고-어디가-구현인가)
- [언제 인터페이스를 두고 언제 클래스로 충분한가](#언제-인터페이스를-두고-언제-클래스로-충분한가)
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
- [Spring Data JPA 기초](../database/spring-data-jpa-basics.md)

retrieval-anchor-keywords: repository interface beginner, repository interface contract, repository interface vs implementation, repository implementation swap, repository port beginner, dao vs repository interface, spring data jpa repository interface, domain repository contract, repository adapter beginner, repository naming smell, persistence follow-up question guide, repository method naming beginner

처음 배우는데 "왜 `Repository`를 인터페이스로 두고 구현체를 갈아끼운다고 말하지?"가 제일 막힌다면, 이 문서를 큰 그림 entrypoint로 잡고 나서 [Repository, DAO, Entity](./repository-dao-entity.md)와 [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)로 내려가면 된다.

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

- 큰 분류부터 다시 잡고 싶다면 [Repository, DAO, Entity](./repository-dao-entity.md)
- repository port와 adapter mapping 경계를 바로 점검하고 싶다면 [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
- repository를 outbound port로 읽는 감각을 넓히고 싶다면 [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
- test fake가 왜 "구현 교체"가 아니라 "계약 재현"인지 보고 싶다면 [Repository Fake Design Guide](./repository-fake-design-guide.md)

## 한 줄 정리

Repository 인터페이스는 "테스트용 인터페이스"가 아니라, application/domain이 저장소에 기대하는 의미를 먼저 고정하는 계약이다.
