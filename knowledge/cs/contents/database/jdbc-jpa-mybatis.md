# JDBC, JPA, MyBatis

> 한 줄 요약: 이 문서는 beginner primer 다음 단계에서 "SQL 위치 구분" 위에 `flush`, 영속성 컨텍스트, OSIV, pool 점유 시간 같은 심화 개념을 얹는 follow-up이다.

**난이도: 🔴 Advanced**

관련 문서:

- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)
- [트랜잭션 기초](./transaction-basics.md)
- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
- [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)

<details>
<summary>Table of Contents</summary>

- [왜 이 주제를 알아야 하나](#왜-이-주제를-알아야-하나)
- [빠르게 구분하는 기준](#빠르게-구분하는-기준)
- [JDBC](#jdbc)
- [JPA와 Hibernate](#jpa와-hibernate)
- [MyBatis](#mybatis)
- [SQLite, H2, MySQL은 무엇이 다른가](#sqlite-h2-mysql은-무엇이-다른가)
- [언제 무엇을 선택할까](#언제-무엇을-선택할까)
- [추천 공식 자료](#추천-공식-자료)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

> retrieval-anchor-keywords: jdbc vs jpa vs mybatis, orm vs sql mapper, hibernate vs jpa, entity manager, persistence context, dirty checking, flush timing, osiv, self invocation, transaction propagation, long transaction, connection pool exhaustion, lazy loading controller, external call in transaction

## 먼저 볼 mental model

이 문서는 "처음 기술 이름을 구분하는 primer"가 아니라, **이미 JPA/JDBC/MyBatis 이름은 구분했는데 왜 실제 런타임 동작이 예상과 다르게 보이는지** 설명하는 follow-up이다.

따라서 beginner 첫 읽기에서는 아래 셋을 이 문서 안에서 한꺼번에 해결하려 하지 않는다.

- `save()` 뒤 SQL 위치 구분이 아직 안 됐다
- `Repository`/`Entity`/`Mapper` 역할 이름이 아직 헷갈린다
- `deadlock`, `retry`, `pool exhausted`처럼 이미 incident 성격의 단어가 먼저 튄다

| 지금 들리는 증상 | 먼저 볼 문서 | 이 문서를 여는 시점 |
|---|---|---|
| "`save()`만 보이고 SQL이 안 보여요" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | 아직 이 문서 전 단계다 |
| "`save()`는 했는데 왜 여기서 `UPDATE` SQL이 나가죠?" | 이 문서 | `flush`, dirty checking 감각이 필요하다 |
| "`@Transactional` 붙였는데 왜 적용이 안 되죠?" | 이 문서, [트랜잭션 기초](./transaction-basics.md) | 기술 구분보다 Spring 경계와 proxy를 같이 봐야 한다 |
| "외부 API 한 번 불렀는데 pool timeout이 나요" | 이 문서, [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) | 긴 트랜잭션과 connection 점유 시간을 같이 봐야 한다 |

짧게 말하면 아래처럼 나눈다.

- 기초 문서의 질문: "SQL이 어디서 만들어지지?"
- 이 문서의 질문: "그 기술이 런타임에서 왜 이런 식으로 움직이지?"

증상이 이미 운영/incident 언어라면 이 문서도 끝 문서가 아니다.

| 먼저 튀는 단어 | 이 문서에서 잡는 최소선 | 바로 이어질 문서 |
|---|---|---|
| `pool exhausted`, long transaction | "접근 기술보다 connection 점유 시간이 핵심" | [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) |
| `deadlock`, `lock timeout`, `retry` | "JPA/JDBC 비교표만으로 안 끝난다" | [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md) |
| OSIV, lazy loading controller | "JPA 런타임 경계 질문" | [Spring Open Session In View Trade-offs](../spring/spring-open-session-in-view-tradeoffs.md) |

## 이 문서 다음에 보면 좋은 문서

- 선택 기준만 잡혔는데 raw JDBC 코드 감각이 부족하면 [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)으로 바로 내려가면 된다.
- JPA에서 `@Version`, `PESSIMISTIC_WRITE`, retry 경계를 서비스 레이어 코드로 보고 싶다면 [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md)로 이어 가면 된다.
- 어떤 접근 기술을 써도 결국 트랜잭션과 락을 이해해야 하므로 [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)을 같이 보는 편이 안전하다.
- 운영 병목이 ORM 자체보다 connection 점유 시간과 bulk write 경계에서 생길 때는 [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)와 [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)로 이어진다.

## 헷갈리면 바로 가는 라우트

- `@Transactional`, rollback, `REQUIRES_NEW`, self-invocation이 먼저 떠오르면 프레임워크 선택보다 Spring 트랜잭션 경계 문제일 가능성이 크다. [@Transactional 깊이 파기](../spring/transactional-deep-dive.md) -> [Spring Service-Layer Transaction Boundary Patterns](../spring/spring-service-layer-transaction-boundary-patterns.md) 순으로 보면 빠르다.
- `EntityManager`, persistence context, `flush`, `clear`, `detach`, "왜 여기서 update SQL이 나가지?"가 궁금하면 [Spring Persistence Context Flush / Clear / Detach Boundaries](../spring/spring-persistence-context-flush-clear-detach-boundaries.md)로 바로 간다.
- `OSIV`, Open Session In View, 컨트롤러/JSON 직렬화 단계 lazy loading, 응답 직전에 N+1이 튀는 증상은 [Spring Open Session In View Trade-offs](../spring/spring-open-session-in-view-tradeoffs.md)에서 바로 설명한다.
- `pool exhausted`, connection timeout, long transaction, "외부 API를 트랜잭션 안에서 호출했다", `JPA가 커넥션을 오래 잡는다`처럼 운영 경계가 먼저 보이면 [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)로 바로 내려간다.

## 왜 이 주제를 알아야 하나

백엔드 개발자는 결국 **애플리케이션의 객체 상태를 데이터베이스에 저장하고 다시 복원**해야 한다.  
이때 자바에서 자주 마주치는 선택지가 JDBC, JPA(Hibernate), MyBatis다.

이 셋은 모두 DB에 접근하기 위한 기술이지만,

- SQL을 얼마나 직접 다루는지
- 객체 중심인지 SQL 중심인지
- 반복 코드를 얼마나 감춰주는지

가 다르다.

입문자가 한 번 더 헷갈리는 지점은 "접근 기술 선택"과 "트랜잭션/성능 문제"를 같은 질문으로 섞는다는 점이다. 이 문서는 기술 비교표만 보여 주는 glossary가 아니라, 아래처럼 **같은 주문 저장 흐름을 다른 축으로 다시 읽는 용도**에 가깝다.

| 같은 주문 저장 흐름에서 보이는 장면 | 기술 구분 질문 | 심화 동작 질문 |
|---|---|---|
| `orderRepository.save(order)` | JPA 축인가? | 왜 지금 SQL이 바로 안 나가고 commit 직전에 몰리나? |
| `orderMapper.insert(order)` | MyBatis 축인가? | SQL은 명확한데 트랜잭션 경계는 어디서 잡히나? |
| `jdbcTemplate.update(...)` | JDBC 축인가? | connection을 언제 빌리고 언제 반환하나? |

---

## 빠르게 구분하는 기준

| 기술 | SQL 통제력 | 추상화 수준 | 자주 붙는 고민 | 잘 맞는 상황 |
|------|------|------|------|------|
| JDBC | 가장 높음 | 가장 낮음 | 자원 정리, 매핑 반복, 트랜잭션 경계 | 원리 학습, 작은 서비스, SQL 완전 제어 |
| JPA/Hibernate | 가장 낮음 | 가장 높음 | flush 시점, dirty checking, N+1, 영속성 컨텍스트 | CRUD 중심, 객체 모델 중심 서비스 |
| MyBatis | 높음 | 중간 | mapper 관리, 동적 SQL, SQL 중복 | 복잡한 조회, SQL 튜닝 중심, 레거시 DB |

핵심은 “무엇이 더 좋으냐”보다 “팀이 어디에서 복잡도를 감당할 것이냐”다.

---

## JDBC

JDBC는 **자바에서 데이터베이스와 통신하기 위한 가장 기본적인 표준 API**다.

### 핵심 객체

- `Connection`
  - DB 연결 자체
- `PreparedStatement`
  - 실행할 SQL과 파라미터
- `ResultSet`
  - 조회 결과를 읽는 객체

### 동작 흐름

1. `Connection`을 얻는다.
2. `PreparedStatement`로 SQL을 준비한다.
3. 파라미터를 바인딩한다.
4. `executeQuery()` 또는 `executeUpdate()`를 실행한다.
5. `ResultSet`을 읽어 자바 객체로 복원한다.

```java
Connection connection = DriverManager.getConnection(url);
PreparedStatement statement =
        connection.prepareStatement("SELECT name, team FROM pieces WHERE game_id = ?");
statement.setLong(1, gameId);
ResultSet resultSet = statement.executeQuery();
```

### `PreparedStatement`를 쓰는 이유

- SQL Injection 방지
- 타입에 맞는 값 바인딩 가능
- 문자열 이어붙이기보다 안전함

#### 문자열 이어붙이기의 문제

```java
String sql = "SELECT * FROM game WHERE id = " + input;
```

사용자 입력이 SQL 문장 안으로 그대로 들어가면, 입력값이 **데이터**가 아니라 **SQL 문법 일부**로 해석될 수 있다.

#### `PreparedStatement`는 왜 안전한가

```java
PreparedStatement statement =
        connection.prepareStatement("SELECT * FROM game WHERE id = ?");
statement.setString(1, input);
```

이 방식에서는 SQL 구조가 먼저 고정되고, 입력값은 나중에 별도 데이터로 전달된다.  
즉 입력값이 SQL 문법을 깨뜨리지 못한다.

### JDBC의 장점

- 동작 원리가 가장 명확하다.
- SQL을 완전히 직접 통제할 수 있다.
- 작은 프로젝트나 학습용으로 적합하다.

### JDBC의 단점

- 반복 코드가 많다.
- 예외 처리, 자원 정리, 매핑 코드가 길어진다.

---

## JPA와 Hibernate

### JPA

JPA는 **자바 객체와 데이터베이스 테이블을 매핑하기 위한 표준 명세**다.

즉 JPA는 인터페이스/규약에 가깝고, 실제 구현은 Hibernate 같은 구현체가 담당한다.

### Hibernate

Hibernate는 **JPA를 구현한 대표적인 ORM 프레임워크**다.

### ORM이란

ORM(Object Relational Mapping)은 **객체와 관계형 데이터베이스를 연결해주는 방식**이다.

즉 이런 식으로 생각할 수 있다.

- 자바 객체 = 도메인 모델
- 테이블 row = DB 저장 형태
- ORM = 둘을 연결하는 도구

### JPA/Hibernate의 장점

- 객체 중심으로 개발할 수 있다.
- 기본 CRUD 생산성이 좋다.
- 스프링과 함께 쓸 때 편하다.

### JPA/Hibernate의 단점

- 내부 동작을 모르고 쓰면 왜 쿼리가 나가는지 이해하기 어렵다.
- 성능 문제를 만나면 결국 SQL과 DB 원리를 알아야 한다.
- 작은 프로젝트에서는 과할 수 있다.

### JPA/Hibernate에서 같이 알아야 할 용어

- `EntityManager`
  - 영속성 컨텍스트를 다루는 핵심 인터페이스다
- 1차 캐시(`first level cache`, `persistence context`)
  - 같은 트랜잭션 안에서는 같은 엔티티 조회가 메모리에서 재사용될 수 있다
- `dirty checking`
  - 엔티티 변경을 감지해 flush 시점에 update SQL을 만든다
- `flush`
  - commit 직전뿐 아니라 쿼리 실행 전에도 일어날 수 있어서 “왜 여기서 SQL이 나가지?”를 만든다
- `N+1`
  - 연관 엔티티를 지연 로딩할 때 반복 조회가 폭증하는 대표적인 ORM 문제다

---

## MyBatis

MyBatis는 **SQL은 직접 쓰되, JDBC 반복 작업과 매핑을 줄여주는 프레임워크**다.

### 특징

- SQL을 직접 작성한다.
- 조회 결과를 객체로 매핑한다.
- JDBC보다 보일러플레이트가 적다.
- JPA보다 SQL 통제가 쉽다.

### MyBatis가 어울리는 경우

- 복잡한 SQL이 많을 때
- SQL 튜닝이 중요할 때
- 레거시 DB와 강하게 맞물릴 때

### MyBatis를 볼 때 같이 떠올릴 점

- mapper interface / XML / annotation 중 어디에 SQL을 둘지 팀 규칙이 필요하다
- 동적 SQL이 강력하지만, 너무 복잡해지면 SQL 가독성이 급격히 나빠질 수 있다
- 결과 매핑을 자동화해도 결국 SQL 설계와 인덱스 감각은 직접 가져가야 한다

---

## SQLite, H2, MySQL은 무엇이 다른가

이 셋은 모두 **DB 제품**이다.  
JDBC, JPA, MyBatis는 **접근 기술**이고, SQLite/H2/MySQL은 **실제 DB**다.

### SQLite

- 파일 기반 DB
- 설정이 가볍다
- 로컬 앱, 작은 프로젝트, 저장/복원 기능에 잘 맞는다

### H2

- 자바에서 많이 쓰는 경량 DB
- 메모리 모드 / 파일 모드 둘 다 가능
- 테스트용으로 자주 쓰인다

### MySQL

- 서버 기반 RDBMS
- 실제 서비스 환경에서 많이 쓰인다
- 계정, 포트, DB 생성 등 설정이 더 많다

### 선택 감각

- 학습용 콘솔 앱, 로컬 저장: `SQLite`
- 테스트 자동화, 가벼운 임시 DB: `H2`
- 실제 운영 서버 느낌: `MySQL`

---

## 언제 무엇을 선택할까

### JDBC

- DB 작동 원리를 배우고 싶을 때
- 작은 프로젝트
- SQL을 직접 통제하고 싶을 때

### MyBatis

- SQL은 내가 직접 쓰고 싶고
- JDBC 반복 코드는 줄이고 싶을 때

### JPA/Hibernate

- 객체 중심으로 개발하고 싶을 때
- CRUD가 많고 스프링과 함께 갈 때

### 신입 백엔드 기준 추천 감각

처음엔 **JDBC 원리 이해**가 제일 중요하다.  
그 다음에

- SQL 중심이면 `MyBatis`
- 객체 중심이면 `JPA/Hibernate`

이렇게 구분해가면 된다.

---

## 추천 공식 자료

- Oracle JDBC Tutorial: https://docs.oracle.com/javase/tutorial/jdbc/basics/index.html
- SQLite CREATE TABLE: https://www.sqlite.org/lang_createtable.html
- MyBatis 공식 문서: https://mybatis.org/mybatis-3/
- Hibernate ORM 문서: https://hibernate.org/orm/documentation/6.5/

## 면접에서 자주 나오는 질문

### Q. JDBC와 JPA의 차이는 무엇인가요?

- JDBC는 자바가 DB와 통신하기 위한 기본 API다.
- JPA는 객체와 테이블을 매핑해주는 표준 명세다.
- JDBC는 SQL과 자원 관리를 직접 다루고, JPA는 이를 더 추상화한다.

### Q. JPA와 Hibernate의 차이는 무엇인가요?

- JPA는 표준 명세다.
- Hibernate는 JPA를 구현한 구현체다.

### Q. MyBatis와 JPA 중 어떤 걸 선택하겠습니까?

- 복잡한 SQL과 튜닝이 중요하면 MyBatis가 유리하다.
- 객체 중심 모델과 CRUD 생산성이 중요하면 JPA가 유리하다.

### Q. SQLite와 H2의 차이는 무엇인가요?

- 둘 다 경량 DB지만, SQLite는 파일 기반 로컬 저장에 더 자주 쓰이고, H2는 자바/스프링 테스트 환경에서 메모리 DB로 많이 쓰인다.
