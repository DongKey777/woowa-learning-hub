# JDBC · JPA · MyBatis 기초

> 한 줄 요약: JDBC · JPA · MyBatis의 첫 차이는 "SQL을 코드 어디서 만들고 찾느냐"로 보면 가장 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Database First-Step Bridge](./database-first-step-bridge.md)
- [트랜잭션 기초](./transaction-basics.md)
- [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)
- [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)
- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- [database 카테고리 인덱스](./README.md)
- [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md)

retrieval-anchor-keywords: jdbc jpa mybatis beginner, jdbc vs jpa, mybatis 처음, jparepository 처음, repository entity 헷갈려요, save 만 보이는데 sql 안 보여, mapper xml 어디서 봐요, preparedstatement 가 보이면 뭐지, repository 구현체가 안 보여요, entity 는 뭐예요, findbyemail 은 누가 만들어요, transactional 이면 jpa 인가요, repository 면 전부 jpa 인가요, sql log 어디서 보지, jdbc jpa mybatis first read

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

## 여기서 멈추고 다음 문서로 넘길 때

처음 읽기에서는 아래만 분리되면 충분하다.

- SQL 문자열이 메서드 안에 보이면 JDBC 축부터 본다.
- `save()`와 `JpaRepository`가 먼저 보이면 JPA 축부터 본다.
- `mapper.xml`이나 `@Mapper`가 보이면 MyBatis 축부터 본다.

| 먼저 보인 단어 | 지금은 왜 넘기나 | 다음 문서 |
|---|---|---|
| `flush`, 영속성 컨텍스트, OSIV | JPA 내부 동작은 기술 구분 뒤에 봐도 된다 | [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md) |
| N+1, fetch join | 이미 조회 최적화 질문이다 | [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md) |
| pool timeout, connection leak | 운영/성능 증상 단계다 | [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) |
| `deadlock`, `lock timeout`, `retry` | 접근 기술 구분이 아니라 동시성 대응 질문이다 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md), [락 기초](./lock-basics.md) |

## 한 줄 정리

JDBC · JPA · MyBatis 입문에서는 "SQL이 코드 어디에 있나"만 먼저 분리하고, `Repository`·`Entity`·`@Transactional`은 서로 다른 역할이라는 점까지 구분되면 첫 독해는 충분하다.
