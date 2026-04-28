# JDBC · JPA · MyBatis 기초

> 한 줄 요약: JDBC · JPA · MyBatis의 입문 차이는 "SQL을 코드 어디서 만들고 찾느냐"로 먼저 보면 가장 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Database First-Step Bridge](./database-first-step-bridge.md)
- [트랜잭션 기초](./transaction-basics.md)
- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- [인덱스 기초](./index-basics.md)
- [미션 코드 독해용 DB 체크리스트](./mission-code-reading-db-checklist.md)
- [database 카테고리 인덱스](./README.md)
- [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)
- [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md)
- [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)

retrieval-anchor-keywords: jdbc jpa mybatis beginner, jdbc vs jpa, jpa 입문, mybatis 처음, repository mapper entity 차이, repository entity 처음, save 만 보이는데 sql 안 보여, mapper xml 어디서 봐요, preparedstatement 가 보이면 뭐지, transactional 이면 jpa 인가요, repository 면 전부 jpa 인가요, entity 는 뭐예요, sql log 어디서 보지, jdbc jpa mybatis first read

## 먼저 큰 그림

초보자에게는 기술 이름보다 **SQL을 어디서 만들고 찾는가**가 먼저다.

```text
Controller/Service
  -> Repository / Mapper / DAO 호출
  -> JDBC / JPA / MyBatis 중 하나가 SQL 준비
  -> JDBC가 DB에 SQL 전송
```

짧게 비유하면 이렇다.

- JDBC는 "DB로 가는 기본 도로"다.
- JPA는 "객체를 넘기면 ORM이 SQL을 만들어 주는 주행 방식"에 가깝다.
- MyBatis는 "SQL은 내가 쓰되, 매핑 반복을 줄이는 방식"에 가깝다.
- 그래서 셋은 경쟁 관계이기도 하지만, 결국 마지막 전송층은 JDBC다.

셋은 완전히 다른 세계가 아니다.

- JDBC는 가장 아래에서 직접 SQL을 보내는 기본 통로다.
- JPA와 MyBatis는 그 위에서 반복 작업을 줄여 주는 방식이다.
- 그래서 JPA/MyBatis를 써도 SQL 로그와 트랜잭션 경계는 계속 봐야 한다.
- 이 문서는 여기까지만 다룬다. `flush`, N+1, 영속성 컨텍스트, connection pool 점유 시간처럼 "기술을 구분한 뒤" 봐야 하는 런타임 증상은 심화 문서로 넘긴다.

입문 목표도 단순하다. "이 코드의 SQL은 어디에서 만들어지고 실행되는가?"만 분리되면 1차 독해는 충분하다.

같은 "주문 저장"이라도 초보자가 실제로 보는 표면은 아래처럼 다르다.

| 보이는 첫 줄 | 먼저 떠올릴 해석 | 지금 당장 열 파일 |
|---|---|---|
| `orderRepository.save(order)` | JPA가 엔티티 정보를 바탕으로 SQL을 만들 가능성이 높다 | repository 인터페이스, `Order` 엔티티 |
| `orderMapper.insert(order)` | MyBatis가 mapper/XML에 적힌 SQL을 실행할 가능성이 높다 | mapper 인터페이스, `mapper.xml` |
| `jdbcTemplate.update(\"insert into orders ...\")` | JDBC 축에서 SQL과 파라미터를 직접 다루는 경우가 많다 | DAO/repository 메서드 본문 |

처음에는 "무슨 기술이 더 좋지?"보다 아래 2가지만 분리하면 충분하다.

| 먼저 확인할 것 | 왜 먼저 보나 |
|---|---|
| SQL이 메서드 안에 직접 보이나 | 보이면 JDBC/MyBatis 쪽일 가능성이 높다 |
| `@Entity`, `JpaRepository`, `mapper.xml` 같은 흔적이 보이나 | SQL이 숨겨진 위치를 빠르게 좁힐 수 있다 |

처음 읽기에서 자주 나오는 말도 여기서 바로 자를 수 있다.

| 지금 드는 말 | 이 문서가 먼저 답하나 | 바로 할 일 |
|---|---|---|
| "`save()`만 보여서 왜 SQL이 안 보이죠?" | 예 | repository와 `@Entity`를 같이 연다 |
| "`Repository`라는데 JPA 맞나요, 헷갈려요" | 예 | 이름 말고 `JpaRepository` 상속 여부를 본다 |
| "`flush`나 timeout까지 지금 같이 봐야 하나요?" | 아니오 | 기술 구분이 끝난 뒤 심화 문서로 넘긴다 |

## 30초 판별 카드

처음 화면에서 "`왜 SQL이 안 보여요?`", "`Repository면 전부 JPA예요?`"가 동시에 떠오르면 아래 카드만 먼저 쓴다.

| 첫 화면에서 보인 것 | 가장 안전한 첫 판단 | 바로 이어서 볼 것 |
|---|---|---|
| `save()`, `@Entity`, `JpaRepository` | JPA가 엔티티를 보고 SQL을 만들 가능성이 높다 | repository 인터페이스, 엔티티 매핑 |
| `@Mapper`, `mapper.xml`, `<insert>` | MyBatis가 바깥 SQL 파일이나 어노테이션 SQL을 실행할 가능성이 높다 | mapper 인터페이스, XML/어노테이션 SQL |
| `PreparedStatement`, `JdbcTemplate`, SQL 문자열 | JDBC 계열에서 SQL과 바인딩을 코드에서 직접 다루는 중일 가능성이 높다 | DAO/repository 메서드 본문 |
| `@Transactional`만 먼저 보임 | 트랜잭션 경계가 보인 것이지 접근 기술이 확정된 것은 아니다 | [트랜잭션 기초](./transaction-basics.md), 이 문서 본문 |

핵심은 이름보다 흔적이다.

- `Repository`라는 이름만으로 JPA라고 단정하지 않는다.
- `@Transactional`은 접근 기술 이름이 아니라 commit/rollback 경계 단서다.
- SQL이 안 보인다고 SQL이 없는 것은 아니다. JPA/MyBatis 뒤로 숨었을 수 있다.

## 한 번에 보는 저장 pass cycle

처음에는 "주문 저장 1번"이 화면을 어떻게 지나가는지만 보면 된다. 아래 예시는 `Controller -> Service -> Repository/Mapper/DAO -> JDBC -> DB` 순서를 같은 기능으로 나눈 것이다.

| 보이는 호출 | 초보자용 해석 | SQL을 찾을 자리 |
|---|---|---|
| `orderRepository.save(order)` | JPA가 entity 매핑을 보고 insert/update SQL을 만들 수 있다 | repository 인터페이스, `Order` 엔티티, SQL 로그 |
| `orderMapper.insert(order)` | MyBatis가 미리 적어 둔 SQL을 실행할 수 있다 | mapper 인터페이스, `mapper.xml`, 어노테이션 SQL |
| `orderDao.save(order)` + `jdbcTemplate.update(...)` | JDBC 축에서 SQL과 파라미터를 직접 넘기는 중일 수 있다 | DAO 메서드 본문 |

짧게 붙이면 아래처럼 읽으면 된다.

1. controller/service는 "언제 저장할지"를 결정한다.
2. repository/mapper/dao는 "어느 방식으로 SQL에 닿을지"를 결정한다.
3. 마지막 전송은 결국 JDBC가 맡는다.

그래서 `save()`만 보여도 "DB 호출이 없다"가 아니라 "SQL 생성 위치가 뒤로 숨었다"로 읽는 편이 안전하다.

## 같은 기능을 세 방식으로 보면

같은 "주문 1건 저장"도 어디를 열어야 하는지가 다르다. 초보자는 문법보다 **첫 파일 위치**만 먼저 고정하면 된다.

| 기술 | 코드에서 먼저 보이는 한 줄 | 바로 열 파일 | 초보자용 첫 질문 |
|---|---|---|---|
| JDBC | `jdbcTemplate.update("insert into orders ...")` | DAO/repository 메서드 본문 | SQL과 파라미터가 여기서 끝나나? |
| JPA | `orderRepository.save(order)` | repository 인터페이스, `Order` 엔티티 | 이 저장 요청이 어떤 테이블/컬럼으로 매핑되나? |
| MyBatis | `orderMapper.insert(order)` | mapper 인터페이스, `mapper.xml` | 실제 insert SQL이 XML/어노테이션 어디에 있나? |

예를 들어 리뷰 중 "`save()`만 보여서 아무 SQL도 안 쓰는 줄 알았어요"라는 말이 나오면, "SQL이 없다"가 아니라 "JPA가 뒤에서 SQL을 만든다"로 먼저 고치면 된다.

`entity`라는 단어가 같이 보이면 아래처럼 해석하면 안전하다.

| 지금 보인 단어 | 초보자용 첫 뜻 | 바로 붙일 질문 |
|---|---|---|
| `@Entity` | JPA가 테이블 매핑 대상으로 보는 클래스일 가능성이 높다 | 이 필드가 어느 컬럼으로 매핑되지? |
| `Repository` | 저장/조회 진입점 이름일 뿐이다 | 진짜 JPA repository인가, JDBC 구현체인가? |
| `Mapper` | SQL 진입점일 가능성이 높다 | SQL이 어노테이션에 있나, XML에 있나? |
| `DAO` | JDBC처럼 SQL을 직접 다루는 진입점일 가능성이 높다 | `JdbcTemplate`이나 SQL 문자열이 보이나? |

처음 JPA 코드를 보면 아래처럼 보이는 경우가 많다.

```java
@Transactional
public void create(OrderCreateRequest request) {
    Order order = new Order(request.userId(), request.totalPrice());
    orderRepository.save(order);
}
```

이때 초보자가 바로 붙이면 좋은 해석은 아래 3줄이다.

| 지금 보이는 것 | 바로 해석할 것 | 다음 확인 지점 |
|---|---|---|
| `new Order(...)` | `Entity` 객체를 만들고 있다 | `Order` 클래스에 `@Entity`가 붙어 있나 |
| `orderRepository.save(order)` | JPA repository가 저장 요청을 받을 수 있다 | `orderRepository`가 `JpaRepository`를 상속하나 |
| SQL이 안 보임 | SQL이 없는 게 아니라 뒤에서 생성될 수 있다 | SQL 로그 또는 엔티티-테이블 매핑 |

즉 `Entity`는 "테이블과 연결된 객체", `Repository`는 "저장/조회 진입점"으로 먼저 나눠 읽으면 된다. 둘은 자주 같이 보이지만 같은 역할이 아니다.

## 첫 파일을 어디서 열까

처음 미션 코드를 열었을 때는 기술 이름을 맞히는 것보다 첫 파일 1개를 바로 여는 편이 중요하다.

| 먼저 보인 단서 | 가장 먼저 열 위치 | 왜 여기서 시작하나 |
|---|---|---|
| `save()`, `findById()`, `JpaRepository` | repository 인터페이스와 `@Entity` | JPA라면 메서드 뒤 SQL과 매핑 규칙이 숨어 있다 |
| `@Mapper`, `mapper.xml`, `<select>` | mapper 인터페이스와 XML SQL | MyBatis라면 SQL이 바깥 파일에 있다 |
| `PreparedStatement`, `JdbcTemplate`, SQL 문자열 | DAO/repository 메서드 본문 | JDBC라면 SQL과 바인딩이 코드에 직접 있다 |

처음 1분은 아래 순서로만 확인해도 된다.

1. service에서 `save()`, `mapper`, `jdbcTemplate` 중 무엇이 먼저 보이는지 본다.
2. 그 호출이 가리키는 첫 파일 1개만 연다.
3. SQL이 숨겨진 곳이 repository 뒤인지, mapper/XML인지, 메서드 본문인지 메모한다.

이 3단계가 되면 아직 `flush`나 영속성 컨텍스트를 몰라도 "무슨 기술을 읽고 있는가"는 분리된다.

같은 "주문 저장"을 세 기술로 바꾸면 차이가 더 빨리 보인다.

| 기술 | 초보자에게 먼저 보이는 코드 | 한 문장 기억법 |
|---|---|---|
| JDBC | `jdbcTemplate.update("insert into orders ...")` | SQL을 내가 직접 쓴다 |
| JPA | `orderRepository.save(order)` | 객체 저장 요청 뒤에서 ORM이 SQL을 만든다 |
| MyBatis | `orderMapper.insert(order)` + `mapper.xml` | SQL은 내가 쓰고, 매핑 반복을 줄인다 |

이름보다 흔적을 먼저 보면 더 안전하다.

| 이름만 보고 단정하면 안 되는 것 | 실제로 확인할 흔적 |
|---|---|
| `Repository`라는 클래스명 | `JpaRepository` 상속 여부, `@Entity` 존재, SQL 로그 |
| `DAO`라는 클래스명 | `JdbcTemplate`, `PreparedStatement`, SQL 문자열 |
| `Mapper`라는 이름 | `@Mapper`, `mapper.xml`, `<select>/<insert>` SQL |

## 자주 섞이는 말

| 자주 하는 말 | 실제 질문 | 먼저 볼 문서 |
|---|---|---|
| "`@Transactional`이 붙어 있으니 JPA겠죠?" | 실패 범위와 접근 기술을 같은 것으로 본다 | 이 문서, [트랜잭션 기초](./transaction-basics.md) |
| "`Repository`라는 이름이니 무조건 JPA 아닌가요?" | 클래스 이름과 구현 기술을 같은 것으로 본다 | 이 문서 |
| "`save()`만 보이니 SQL이 없는 것 아닌가요?" | SQL 위치가 숨겨진 것과 SQL이 없는 것을 같은 것으로 본다 | 이 문서, [JDBC 실전 코드 패턴](./jdbc-code-patterns.md) |
| "`entity`가 있으면 repository가 전부 자동으로 되는 건가요?" | 엔티티 매핑과 repository 구현 책임을 같은 것으로 본다 | 이 문서, [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md) |
| "`DAO`면 무조건 옛날 방식 아닌가요?" | 이름이 아니라 SQL을 어디서 직접 쓰는지가 핵심이다 | 이 문서, [JDBC 실전 코드 패턴](./jdbc-code-patterns.md) |

같이 많이 헷갈리는 짝도 아래처럼 바로 끊어 두면 첫 독해가 빨라진다.

| 같이 보이면 헷갈리는 것 | 먼저 이렇게 자른다 |
|---|---|
| `Entity`와 `Repository` | entity는 테이블 매핑 정보, repository는 저장/조회 진입점이다 |
| `@Transactional`과 `save()` | `@Transactional`은 경계, `save()`는 저장 요청 진입점이다 |
| `Repository`와 `DAO` | 이름보다 실제로 SQL 문자열/JDBC 호출이 메서드 안에 보이는지 확인한다 |

## 한 번 더 끊어 읽기

짧게 묶으면 아래 세 줄이면 충분하다.

- `@Transactional`은 "무엇을 같이 `commit`/`rollback`할까?"의 답이다.
- JDBC/JPA/MyBatis는 "SQL을 어디서 만들고 찾을까?"의 답이다.
- `Repository`라는 이름만으로 구현 기술을 단정하지 않는다.

특히 아래 오해를 먼저 끊어 두면 첫 독해가 훨씬 쉬워진다.

| 흔한 오해 | 더 정확한 첫 문장 |
|---|---|
| "`@Transactional`이 있으니 JPA 코드겠지?" | 트랜잭션 경계와 접근 기술은 다른 질문이다 |
| "`Repository`라는 이름이니 SQL이 안 보이는 게 정상이지?" | 이름 말고 `JpaRepository` 상속, `@Mapper`, SQL 문자열 흔적을 직접 확인해야 한다 |
| "`Entity`만 있으면 저장 로직도 자동 완성되겠지?" | 엔티티는 매핑 정보이고, SQL 실행 경로는 repository/mapper/DAO 쪽에서 다시 확인해야 한다 |
| "`DAO`면 전부 레거시라서 건너뛰어도 되겠지?" | 이름보다 JDBC 호출과 SQL 문자열이 실제로 보이는지부터 확인해야 한다 |
| "JPA면 SQL을 몰라도 된다" | SQL 위치가 숨겨졌을 뿐, 성능과 정합성 문제를 읽으려면 결국 SQL 축으로 돌아온다 |

같은 서비스 메서드 안에서 아래처럼 섞여 있어도 이상한 구조는 아니다.

```text
createOrderService()
  -> orderRepository.save(order)      // JPA
  -> orderMapper.insertAudit(log)     // MyBatis
  -> jdbcTemplate.update(...)         // JDBC
```

핵심은 "한 프로젝트는 한 기술만 쓴다"가 아니라, **각 호출이 SQL을 어디서 만드는지 따로 찾는 것**이다.

## 여기서 멈추는 기준

처음 읽기에서는 아래만 분리되면 충분하다.

- SQL 문자열이 메서드 안에 보이면 JDBC 축일 가능성이 높다.
- `save()`와 `@Entity`가 먼저 보이면 JPA 축일 가능성이 높다.
- `mapper.xml`이나 `@Mapper`가 보이면 MyBatis 축일 가능성이 높다.

| 먼저 보인 단어 | 지금은 왜 넘기나 | 나중에 갈 문서 |
|---|---|---|
| `flush`, 영속성 컨텍스트 | JPA 내부 동작은 기술 구분 뒤에 봐도 된다 | [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md) |
| N+1, fetch join | 이미 조회 최적화 질문이다 | [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md), [인덱스와 실행 계획](./index-and-explain.md) |
| pool timeout, connection leak | 운영/성능 증상 단계다 | [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) |

초보자 기준 종료 조건은 단순하다.

- `save()`가 보이면 JPA 흔적인지부터 확인한다.
- `mapper.xml`이 보이면 MyBatis 경로부터 확인한다.
- SQL 문자열이 직접 보이면 JDBC 경로부터 확인한다.
- 그다음에만 `flush`, N+1, pool, timeout 같은 심화 주제로 넘어간다.

cross-category bridge:

- JPA repository와 Spring Data 메서드 이름 규칙이 같이 헷갈리면 [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)로 이어서 본다.

## 한 줄 정리

JDBC · JPA · MyBatis 입문에서는 "SQL이 코드 어디에 보이느냐"만 먼저 분리하고, `flush`, N+1, pool 이슈 같은 심화 주제는 관련 문서로 넘기는 편이 초보자에게 가장 안전하다.
