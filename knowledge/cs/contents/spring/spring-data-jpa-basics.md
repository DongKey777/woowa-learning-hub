# Spring Data JPA 기초: Repository로 DB를 다루는 방법

> 한 줄 요약: Spring Data JPA는 `JpaRepository` 인터페이스를 상속하는 것만으로 기본 CRUD와 쿼리 메서드를 자동 생성해, 반복적인 데이터 접근 코드를 거의 없애준다.

**난이도: 🟢 Beginner**

관련 문서:

- [JPA Dirty Checking / Version Strategy](./jpa-dirty-checking-version-strategy.md)
- [JDBC, JPA, MyBatis](../database/jdbc-jpa-mybatis.md)
- [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring data jpa basics, 스프링 jpa 처음, jparepository 입문, spring data jpa 왜 써요, repository 인터페이스 입문, 쿼리 메서드 뭐예요, findby 메서드 입문, @entity 입문, spring jpa beginner primer, crud repository 입문, jpql 처음, spring jpa 설정 없이 쿼리 만드는법

## 핵심 개념

JDBC로 조회하려면 SQL 작성, `PreparedStatement` 생성, `ResultSet` 파싱까지 반복 코드가 많다. JPA는 객체를 DB 테이블에 매핑하고, Spring Data JPA는 그 위에 Repository 패턴을 더해 **인터페이스만 선언하면 기본 CRUD 구현체를 자동 생성**한다.

`extends JpaRepository<Member, Long>` 한 줄이면 `save`, `findById`, `findAll`, `delete` 등이 즉시 사용 가능하다. 추가 쿼리는 메서드 이름 규칙만 따르면 SQL 없이 만들 수 있다.

## 한눈에 보기

```text
MemberRepository extends JpaRepository<Member, Long>
    ↓ Spring Data JPA가 구현체 자동 생성
    ↓
findById(1L)   → SELECT * FROM member WHERE id = 1
save(member)   → INSERT / UPDATE (id 유무에 따라)
delete(member) → DELETE FROM member WHERE id = ?
findByEmail(email) → SELECT * FROM member WHERE email = ?
```

| 계층 | 역할 |
|---|---|
| `JpaRepository` | CRUD + 페이징/정렬 메서드 제공 |
| `PagingAndSortingRepository` | 페이징·정렬 추가 |
| `CrudRepository` | 기본 CRUD |

## 상세 분해

- **`@Entity`**: 클래스를 JPA 엔티티로 표시. DB 테이블과 매핑된다.
- **`@Id`와 `@GeneratedValue`**: 기본 키 필드와 자동 증가 전략 지정.
- **쿼리 메서드**: `findByUsername`, `findByEmailAndStatus` 처럼 메서드 이름에서 쿼리를 자동 생성한다. `And`, `Or`, `Like`, `Between` 등 키워드를 지원한다.
- **`@Query`**: 복잡한 JPQL이나 네이티브 SQL을 직접 작성하고 싶을 때 메서드에 붙인다.
- **페이징**: `findAll(Pageable pageable)`을 사용하면 `LIMIT / OFFSET` 처리를 자동으로 해준다.

## 흔한 오해와 함정

**오해 1: `save()`를 호출해야 DB에 저장된다**
트랜잭션 안에서 조회한 엔티티의 필드를 변경하면 트랜잭션 커밋 시점에 Dirty Checking으로 자동 UPDATE된다. `save()`를 다시 호출하지 않아도 된다.

**오해 2: `findById()`가 항상 DB를 조회한다**
동일 트랜잭션 안에서 같은 id로 조회하면 1차 캐시(영속성 컨텍스트)에서 반환한다. DB 조회가 일어나지 않을 수 있다.

**오해 3: `JpaRepository`를 구현 클래스로 만들어야 한다**
인터페이스로 선언만 하면 Spring Data JPA가 런타임에 프록시 구현체를 만들어준다. 구현 클래스를 직접 작성할 필요가 없다.

## 실무에서 쓰는 모습

```java
@Entity
public class Member {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String email;
    private String username;
    // getter/setter 생략
}

public interface MemberRepository extends JpaRepository<Member, Long> {
    Optional<Member> findByEmail(String email);
    List<Member> findByUsernameContaining(String keyword);
}
```

`MemberRepository`는 인터페이스만 선언했지만, `save`, `findById`, `findByEmail`이 모두 동작한다.

## 더 깊이 가려면

- Dirty Checking이 실제로 어떻게 동작하는지는 [JPA Dirty Checking / Version Strategy](./jpa-dirty-checking-version-strategy.md)에서 이어서 본다.
- JPA가 JDBC, MyBatis와 어떤 계층에 있는지는 [JDBC, JPA, MyBatis](../database/jdbc-jpa-mybatis.md)를 참고한다.

## 면접/시니어 질문 미리보기

> Q: Spring Data JPA의 `save()` 메서드는 항상 INSERT를 실행하나?
> 의도: 영속성 컨텍스트와 save 동작 원리 이해
> 핵심: id가 없으면 `persist(INSERT)`, id가 있으면 `merge(SELECT 후 UPDATE 또는 INSERT)`를 실행한다.

> Q: 쿼리 메서드와 `@Query`를 언제 구분해 쓰나?
> 의도: 적절한 도구 선택 이해
> 핵심: 단순 조건 조합은 쿼리 메서드로, JOIN이나 복잡한 조건은 `@Query`로 JPQL을 직접 작성하는 편이 가독성이 높다.

> Q: Dirty Checking이 동작하려면 어떤 조건이 필요한가?
> 의도: 영속 상태 개념 확인
> 핵심: 트랜잭션이 열려 있고 엔티티가 영속(managed) 상태여야 한다. `detach` 상태나 트랜잭션 밖에서는 Dirty Checking이 동작하지 않는다.

## 한 줄 정리

Spring Data JPA는 `JpaRepository` 인터페이스 선언만으로 CRUD와 쿼리 메서드를 자동 생성해 반복 코드를 줄이고, Dirty Checking 덕분에 변경된 엔티티는 `save()` 없이도 트랜잭션 커밋 시 자동 반영된다.
