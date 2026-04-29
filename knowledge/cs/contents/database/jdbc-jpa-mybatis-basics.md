# JDBC · JPA · MyBatis 기초

> 한 줄 요약: JDBC · JPA · MyBatis의 첫 차이는 "SQL을 코드 어디서 만들고 찾느냐"로 보면 가장 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md)
- [Database First-Step Bridge](./database-first-step-bridge.md)
- [트랜잭션 기초](./transaction-basics.md)
- [Spring Persistence / Transaction Mental Model Primer](../spring/spring-persistence-transaction-web-service-repository-primer.md)
- [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)
- [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)
- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- [database 카테고리 인덱스](./README.md)
- [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md)

retrieval-anchor-keywords: jdbc jpa mybatis beginner, jdbc vs jpa, mybatis 처음, jparepository 처음, repository entity 헷갈려요, save 만 보이는데 sql 안 보여, save 가 insert 인지 update 인지 헷갈려요, controller 다음 save sql 어디서 봐요, spring 다음 database 뭐부터, 처음 jdbc jpa mybatis 뭐예요, mapper xml 어디서 봐요, preparedstatement 가 보이면 뭐지, repository 구현체가 안 보여요, entity 만 보이는데 repository 가 안 보여요, transactional 이면 jpa 인가요

## 먼저 큰 그림

처음에는 기술 이름보다 "SQL을 누가 준비하나?"만 보면 된다.

```text
Controller / Service
  -> Repository / Mapper / DAO 호출
  -> JPA 또는 MyBatis 또는 JDBC 코드가 SQL 준비
  -> 마지막 전송은 JDBC가 맡음
```

- JDBC는 SQL을 코드에서 직접 보내는 기본 통로다.
- JPA는 객체 저장 요청 뒤에서 ORM이 SQL을 만든다.
- MyBatis는 SQL은 직접 쓰되, 매핑 반복을 줄여 준다.

그래서 "`save()`는 보이는데 SQL이 안 보여요", "`Repository`면 전부 JPA예요?", "`findByEmail()`은 누가 만들어요?" 같은 질문은 같은 축이다. 전부 "SQL 위치와 생성 주체"를 찾는 질문이다.

처음 한 번은 이름보다 아래 3줄로 끊어 읽는 편이 안전하다.

| 코드에서 먼저 보인 것 | 초보자용 첫 뜻 | 바로 다음 행동 |
|---|---|---|
| `@Entity` | 저장 대상과 컬럼 매핑 단서다 | 필드명과 `@Id`를 본다 |
| `Repository` / `JpaRepository` | 저장/조회 시작점이다 | `save`, `findBy...` 같은 호출을 본다 |
| SQL 문자열 / `mapper.xml` | 실제 SQL이 이미 드러난 상태다 | 현재 메서드나 XML에서 조건과 파라미터를 본다 |

즉 `Entity`는 "무엇을 저장하나", `Repository`는 "어디서 저장을 시작하나", SQL 문자열은 "실행 문장이 지금 보이느냐"를 알려 주는 단서다.

같은 저장 기능을 세 기술로 아주 짧게 비교하면 아래처럼 읽으면 된다.

| 기술 | SQL이 처음 보이는 자리 | 초보자용 첫 파일 | 자주 하는 오해 |
|---|---|---|---|
| JDBC | 현재 메서드 본문 | DAO/repository 메서드 | "`jdbcTemplate.update(...)` 뒤에 다른 숨은 SQL이 더 있겠지?" |
| JPA | repository 호출 뒤, 실행 시점 | repository 인터페이스 + `@Entity` | "`save()`를 봤으니 insert SQL이 바로 코드에 있어야지" |
| MyBatis | `mapper.xml` 또는 어노테이션 | mapper 인터페이스 + XML | "`Mapper`도 repository처럼 구현체가 숨어 있겠지" |

첫 독해에서는 "누가 더 좋나?"보다 "SQL을 어느 파일에서 찾나?"만 먼저 확정하면 충분하다.

## beginner-safe 사다리

이 문서는 DB 접근 기술 primer다. "`브라우저 -> controller -> save()` 전체 흐름이 처음이에요", "`왜 controller 다음에 바로 SQL이 안 보여요?`", "`처음인데 뭘 먼저 읽죠?`"처럼 앞단 handoff까지 같이 헷갈리면 아래처럼 한 칸씩만 내려간다.

| 지금 막힌 말 | primer | safe next step | deeper는 이때만 |
|---|---|---|---|
| "`HTTP` 다음에 Spring 코드는 어디서 봐요?" | [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md) | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | filter ordering, async, timeout처럼 요청 입구 자체를 더 파야 할 때 |
| "`controller` 다음에 DB는 어디서 시작돼요?" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | [Database First-Step Bridge](./database-first-step-bridge.md) | `@Transactional`, 인덱스, 동시성 축을 따로 분리해야 할 때 |
| "`save()`만 보여서 SQL이 안 보여요" | [Database First-Step Bridge](./database-first-step-bridge.md) | 이 문서 | `flush`, OSIV, SQL 로그, 런타임 지연처럼 구현 안쪽 해석이 필요할 때 |

짧게는 아래 4칸만 기억하면 된다.

`HTTP 요청-응답 기본 흐름 -> Spring 요청 파이프라인과 Bean Container 기초 -> Database First-Step Bridge -> JDBC · JPA · MyBatis 기초`

## 여기서 미루는 질문

처음에는 `deadlock`, `retry`, `failover`, `cutover`, `OSIV`, `N+1`, `connection pool timeout`으로 바로 가지 않는다. 이 문서의 목표는 "SQL을 어디서 찾을지"와 "`Repository`/`Entity`가 어떤 역할인지"까지 고정하는 것이다.

입문 1회차에서는 아래처럼 끊어 두면 scope creep를 막기 쉽다.

| 먼저 튀는 단어 | 지금 왜 멈추나 | 다음 문서 |
|---|---|---|
| `deadlock`, `lock timeout`, `retry` | 접근 기술 구분이 아니라 동시성/증상 대응 질문이다 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md), [락 기초](./lock-basics.md) |
| `OSIV`, lazy loading, persistence context | JPA 내부 동작을 먼저 파면 SQL 위치 감각이 흐려진다 | [Spring Persistence / Transaction Mental Model Primer](../spring/spring-persistence-transaction-web-service-repository-primer.md), [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md) |
| pool timeout, connection leak | 운영 증상 단계라서 beginner entrypoint 중심이 바뀐다 | [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) |

## 30초 판별표

| 지금 먼저 보인 흔적 | 가장 안전한 첫 판단 | 바로 열 파일 |
|---|---|---|
| `save()`, `@Entity`, `JpaRepository` | JPA가 SQL 생성을 뒤로 숨겼을 가능성이 높다 | repository 인터페이스, 엔티티 |
| `findByEmail`, `findByStatus`, 구현체 없는 repository 인터페이스 | Spring Data JPA가 메서드 이름으로 쿼리를 만들 가능성이 높다 | repository 인터페이스, [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md) |
| `@Mapper`, `mapper.xml`, `<select>`, `<insert>` | MyBatis가 바깥 SQL 파일이나 어노테이션 SQL을 실행할 가능성이 높다 | mapper 인터페이스, XML/어노테이션 SQL |
| `JdbcTemplate`, `PreparedStatement`, SQL 문자열 | JDBC 축에서 SQL과 파라미터를 직접 다루는 중일 가능성이 높다 | DAO/repository 메서드 본문 |
| `@Transactional`만 먼저 보임 | 트랜잭션 경계 단서일 뿐 접근 기술 확정은 아니다 | service 메서드, 저장 호출 위치 |

처음 1분은 아래 순서면 충분하다.

1. `save`, `mapper`, `jdbcTemplate` 중 무엇이 먼저 보이는지 본다.
2. 그 호출이 가리키는 파일 1개만 연다.
3. SQL이 repository 뒤인지, mapper/XML인지, 메서드 본문인지 적어 둔다.

처음 미션 코드에서 `Repository`, `Entity`, `@Transactional`이 한 화면에 같이 보이면 아래처럼 역할을 끊으면 덜 흔들린다.

| 화면에 같이 보인 것 | 지금 확정할 최소 해석 | 다음 1걸음 |
|---|---|---|
| `@Entity` + 필드 | 어떤 테이블/컬럼 후보를 다루는지 본다 | 필드명과 `@Id` 확인 |
| `Repository` / `JpaRepository` | 저장/조회 시작점이 어디인지 본다 | `save`, `findBy...` 호출 위치 확인 |
| `@Transactional` | 이 호출들을 어디까지 같이 commit/rollback할지 본다 | [트랜잭션 기초](./transaction-basics.md)로 경계 분리 |

핵심은 "`Entity`가 보인다 = JPA를 다 이해했다"가 아니라 "`무엇을 저장하는지`, `어디서 저장을 시작하는지`, `어디까지 같이 실패하는지`를 따로 본다"는 점이다.

## `save()`가 insert인지 update인지 왜 바로 안 보일까

초보자가 JPA repository에서 자주 멈추는 이유는 `save()` 한 단어가 "저장 반영 요청"만 보여 주고, 실제 SQL 종류는 바로 드러내지 않기 때문이다. 이때는 메서드 이름보다 "지금 넘기는 객체가 새것인가, 이미 있던 것인가"를 먼저 본다.

| 지금 보인 장면 | 초보자용 첫 해석 | 바로 확인할 단서 |
|---|---|---|
| `new Member(...)`를 만든 뒤 `save()` | 새 저장 후보라서 insert 쪽으로 읽기 쉽다 | `@Id`를 직접 넣는지, 생성 전략이 있는지 |
| 조회한 엔티티 필드를 바꾼 뒤 `save()` 또는 commit | 기존 데이터 변경이라 update 가능성을 먼저 본다 | 같은 트랜잭션 안에서 먼저 조회했는지 |
| `save()`만 한 줄 덩그러니 보임 | 호출문만으로 insert/update를 단정하지 않는다 | service 앞뒤 코드, entity id 상태 |

아래 세 줄만 기억하면 첫 독해에는 충분하다.

- `save()`는 "DB에 반영 요청"이지, 항상 insert만 뜻하는 단어는 아니다.
- JPA는 SQL이 바로 안 보여도 entity 상태와 트랜잭션 문맥에 따라 insert/update를 나눌 수 있다.
- insert인지 update인지부터 막히면 SQL 튜닝 문서보다 service 코드와 entity `@Id`를 먼저 다시 본다.

## JPA repository를 처음 읽을 때 1분 예시

"`save()`는 보이는데 insert SQL이 안 보여요", "`Entity`만 있고 repository 구현체가 없어요", "`findByEmail()`은 누가 만들어요?"가 같이 나오면 아래처럼 한 번만 추적하면 된다.

```java
@Entity
class Member {
    @Id
    private Long id;
    private String email;
}

interface MemberRepository extends JpaRepository<Member, Long> {
    Optional<Member> findByEmail(String email);
}

memberRepository.save(new Member(...));
```

| 코드에서 보이는 것 | 초보자용 첫 해석 | 지금 확인할 파일/자리 |
|---|---|---|
| `@Entity` | 어떤 테이블/컬럼 후보인지 알려 주는 매핑 단서 | entity 필드와 어노테이션 |
| `JpaRepository<Member, Long>` | Spring Data JPA가 기본 CRUD 구현체를 만들어 줄 수 있다 | repository 인터페이스 선언 |
| `findByEmail(...)` | 메서드 이름으로 조회 쿼리를 만들 가능성이 높다 | 메서드 이름, 엔티티 필드명 |
| `memberRepository.save(...)` | SQL이 호출문에 직접 보이지 않아도 ORM 뒤에서 insert/update가 준비될 수 있다 | service 호출 위치, SQL 로그 필요 여부 |

## 구현체가 안 보일 때 읽는 순서

처음에는 "구현 클래스가 왜 안 보이지?"보다 아래 한 줄로 끊는 편이 쉽다.

- entity는 "무엇을 저장할지"를 설명한다.
- repository는 "어떻게 저장/조회 시작할지"를 설명한다.
- 실제 SQL 생성은 실행 시점에 프레임워크가 맡을 수 있다.

처음 코드 독해라면 아래 4단계만 따라가면 충분하다.

1. service에서 `memberRepository.save(...)`나 `findByEmail(...)` 호출을 찾는다.
2. repository 인터페이스가 `JpaRepository`를 상속하는지 본다.
3. 연결된 `@Entity`에서 필드 이름과 `@Id`를 확인한다.
4. SQL이 안 보여도 "지금은 JPA가 뒤에서 만든다"까지만 확정하고, 더 필요하면 SQL 로그나 심화 문서로 넘긴다.

같은 예시에서 `findByEmail()`과 `save()`를 초보자 눈으로 나누면 아래처럼 더 단순하다.

| 메서드 | 지금 초보자가 붙이면 되는 뜻 | 흔한 오해 |
|---|---|---|
| `findByEmail()` | 이름을 보고 조회 SQL을 만들 수도 있겠다 | 구현체가 안 보이니 코드가 빠졌다고 단정 |
| `save()` | 저장 반영을 요청하는 시작점이구나 | 항상 insert 한 종류만 한다고 단정 |

그래서 repository를 처음 읽을 때는 "`구현 클래스 찾기`"보다 "`이 메서드가 조회 시작점인지 저장 시작점인지`"를 먼저 적어 두는 편이 더 안전하다.

## JPA 입문 다음 1걸음

| 지금 막힌 장면 | 초보자용 다음 1걸음 | 바로 열 문서 |
|---|---|---|
| `JpaRepository`만 있고 구현체가 안 보임 | "런타임 구현 가능성"까지만 확정하고 메서드 이름과 엔티티 필드를 본다 | [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md) |
| `Entity`는 보이는데 repository 역할이 헷갈림 | 저장 창구와 매핑 정보를 분리해서 읽는다 | [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md) |
| `save()`가 insert인지 update인지 모르겠음 | service 앞뒤와 `@Id` 상태를 먼저 본다 | 이 문서의 [`save()`가 insert인지 update인지 왜 바로 안 보일까](#save가-insert인지-update인지-왜-바로-안-보일까) |
| 알고 보니 SQL 문자열이 이미 보임 | JPA 추적을 멈추고 raw JDBC/MyBatis 파일로 이동한다 | [JDBC 실전 코드 패턴](./jdbc-code-patterns.md) |

## 한 화면 pass cycle 예시

처음 미션 코드에서 `@Transactional`, `save()`, `@Entity`가 한 화면에 같이 보이면 아래 4칸만 순서대로 확인하면 된다. 핵심은 "모든 의미를 한 줄에서 다 읽지 않는다"는 점이다.

```java
@Transactional
public void register(String email) {
    Member member = new Member(email);
    memberRepository.save(member);
}
```

| 보는 순서 | 지금 확정할 것 | 초보자용 한 문장 |
|---|---|---|
| 1 | `@Transactional` | 같이 commit/rollback할 경계를 먼저 본다 |
| 2 | `memberRepository.save(...)` | 저장 요청 시작점을 본다 |
| 3 | `Member` / `@Entity` | 어떤 테이블 후보를 다루는지 본다 |
| 4 | SQL이 안 보이면 | "JPA가 뒤에서 만들 수 있다"까지만 확정한다 |

같은 저장 기능이더라도 첫 추적 파일은 기술마다 다르다.

| 지금 보이는 첫 줄 | 먼저 열 파일 | 바로 던질 질문 |
|---|---|---|
| `memberRepository.save(member)` | repository 인터페이스 + `@Entity` | SQL이 repository 뒤에서 만들어지나? |
| `memberMapper.insert(member)` | mapper 인터페이스 + `mapper.xml` | SQL이 XML/어노테이션에 있나? |
| `jdbcTemplate.update(...)` | 현재 메서드 본문 | SQL과 파라미터가 여기서 끝나나? |

한 줄로 줄이면 아래 pass cycle이다.

`트랜잭션 경계 확인 -> 저장 시작점 확인 -> 저장 대상 확인 -> SQL 위치 확정`

## service와 `@Transactional`이 같이 보일 때

```java
@Transactional
public void register(String email) {
    Member member = new Member(email);
    memberRepository.save(member);
}
```

| 지금 줄에서 확정할 것 | 초보자용 해석 |
|---|---|
| `new Member(email)` | 저장할 객체를 만드는 중이다 |
| `memberRepository.save(member)` | 저장 요청 시작점이다 |
| `@Transactional` | 이 저장을 어느 경계에서 commit/rollback할지 정하는 중이다 |

여기서 중요한 점은 `@Transactional`이 보여도 "JPA가 맞다"까지는 아직 확정이 아니라는 점이다. JPA 여부는 `JpaRepository`, `@Entity`, SQL 로그/mapper 흔적으로 따로 확인한다.

## Repository와 Entity를 이름으로 단정하지 않기

초보자가 가장 많이 헷갈리는 부분은 `Repository`, `Entity`, `@Transactional`을 같은 그룹으로 보는 것이다.

| 보인 단어 | 초보자용 첫 뜻 | 같은 뜻이 아닌 것 |
|---|---|---|
| `Repository` | 저장/조회 진입점 이름 | 자동으로 JPA라는 보장 |
| `Entity` | 테이블 매핑 단서 | 트랜잭션 경계 |
| `@Transactional` | 같이 commit/rollback할 범위 | 접근 기술 이름 |
| `JpaRepository` | Spring Data JPA 계약 | 도메인 repository라는 보장 |

특히 아래 오해를 먼저 끊어 두면 안전하다.

- "`Repository`라는 이름이니 무조건 JPA다" -> 이름 말고 `JpaRepository` 상속, `@Entity`, SQL 문자열 흔적을 본다.
- "`@Transactional`이 있으니 JPA다" -> 트랜잭션 경계와 접근 기술은 다른 질문이다.
- "`Entity`가 있으니 저장 로직도 자동이다" -> entity는 매핑 정보이고, 실제 SQL 경로는 repository/mapper/DAO 쪽에서 다시 본다.
- "`JpaRepository` 구현체가 안 보이니 코드가 빠진 것 같다" -> Spring Data JPA가 런타임 proxy/구현체를 만들 수 있으니 repository 선언과 entity 필드 이름부터 본다.
- "`save()`를 봤으니 무조건 insert다" -> 새 엔티티 저장인지, 기존 엔티티 변경 반영인지 문맥을 같이 봐야 한다.
- "`findBy...` 메서드면 아무 필드로나 자동 조회된다" -> 메서드 이름과 entity 필드명이 맞아야 하고, 복잡한 조건은 별도 쿼리 선언으로 내려갈 수 있다.

`Repository`와 `Entity` 역할 자체가 아직 헷갈리면 [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)로 바로 넘어가는 편이 좋다.

## 같은 주문 저장을 세 줄로 보기

같은 기능도 초보자가 열어야 할 첫 파일은 다르다.

```java
// JPA
orderRepository.save(order);
```

```java
// MyBatis
orderMapper.insert(order);
```

```java
// JDBC
jdbcTemplate.update("insert into orders(user_id, total_price) values (?, ?)", userId, totalPrice);
```

| 보이는 한 줄 | SQL을 찾을 자리 | 초보자용 첫 질문 |
|---|---|---|
| `orderRepository.save(order)` | repository 뒤의 엔티티 매핑, SQL 로그 | 어떤 테이블/컬럼으로 저장되나? |
| `orderMapper.insert(order)` | mapper 인터페이스, `mapper.xml`, 어노테이션 SQL | 실제 insert SQL이 어디 있나? |
| `jdbcTemplate.update(...)` | 현재 메서드 본문 | SQL과 파라미터가 여기서 끝나나? |

핵심은 기술 이름 맞히기가 아니다. "SQL 찾는 시작 위치"를 먼저 고정하는 것이다.

## 자주 나오는 증상 문장 끊기

| 지금 막힌 문장 | 먼저 답할 질문 | 다음 문서 |
|---|---|---|
| "`save()`만 보여서 SQL이 없는 줄 알겠어요" | SQL이 없는가, 뒤로 숨은 것인가 | 이 문서, [JDBC 실전 코드 패턴](./jdbc-code-patterns.md) |
| "`Repository` 인터페이스만 있고 구현체가 안 보여요" | 프레임워크가 구현을 만들었는가 | 이 문서, [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md) |
| "`Repository`랑 `Entity`가 각각 뭐 하는지 헷갈려요" | 저장 창구와 매핑 정보를 분리했는가 | 이 문서, [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md) |
| "`@Transactional`도 있는데 왜 마지막 재고가 또 팔려요?" | 실패 범위와 동시성 충돌을 분리했는가 | [트랜잭션 기초](./transaction-basics.md), [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |
| "service에서 조회했는데 controller/DTO에서 SQL이 또 나가요" | SQL 위치 질문이 아니라 persistence context와 lazy loading 경계 질문인가 | [Spring Persistence / Transaction Mental Model Primer](../spring/spring-persistence-transaction-web-service-repository-primer.md), [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md) |

## 여기서 멈추고 다음 문서로 넘길 때

처음 읽기에서는 "JDBC / JPA / MyBatis 중 지금 SQL을 어디서 찾는가"만 분리되면 충분하다.

| 먼저 보인 단어 | 지금은 왜 넘기나 | 다음 문서 |
|---|---|---|
| `flush`, 영속성 컨텍스트, OSIV | JPA 내부 동작은 기술 구분 뒤에 봐도 된다 | [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md) |
| N+1, fetch join | 이미 조회 최적화 질문이다 | [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md) |
| pool timeout, connection leak | 운영/성능 증상 단계다 | [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) |
| `deadlock`, `lock timeout`, `retry` | 접근 기술 구분이 아니라 동시성 대응 질문이다 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md), [락 기초](./lock-basics.md) |

위 단어가 먼저 보여도 이 문서가 부족한 게 아니라 질문 축이 이미 다음 단계로 넘어간 것이다. 입문 1회차에서는 "SQL 위치"와 "`Repository`·`Entity`·`@Transactional` 역할 구분"까지만 잡으면 된다.

처음 읽기에서 follow-up을 하나만 붙인다면 아래처럼 고르면 안전하다.

| 지금 질문 | 먼저 읽을 primer | 다음 한 걸음 |
|---|---|---|
| "`save()` 뒤 SQL이 구체적으로 어디서 만들어져요?" | 이 문서 | [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md) |
| "`Repository`와 `Entity` 역할이 왜 달라요?" | 이 문서 | [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md) |
| "`@Transactional`도 보이는데 마지막 재고가 왜 또 팔려요?" | [트랜잭션 기초](./transaction-basics.md) | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |
| "`mapper.xml`, `JdbcTemplate`, `JpaRepository` 중 뭐부터 읽죠?" | 이 문서 | 위 `30초 판별표`에서 첫 흔적 하나만 다시 고른다 |

## 길을 잃었을 때

문서가 빨라지면 뒤로 한 칸만 물러난다.

- "`처음`이라 request 흐름부터 다시 보고 싶다" -> [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- "`controller`, `service`, `repository` 연결부터 다시 보고 싶다" -> [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md)
- "`트랜잭션인지 SQL 위치인지` 질문 축부터 다시 고르고 싶다" -> [Database First-Step Bridge](./database-first-step-bridge.md)
- category 단위에서 next step을 다시 고르고 싶다 -> [database 카테고리 인덱스](./README.md)

## 한 줄 정리

JDBC · JPA · MyBatis 입문에서는 "SQL이 코드 어디에 있나"만 먼저 분리하고, `Repository`·`Entity`·`@Transactional`은 서로 다른 역할이라는 점까지 구분되면 첫 독해는 충분하다.
