# Database (데이터베이스)

> 한 줄 요약: 이 README는 database를 처음 읽는 사람을 위한 `category navigator`다. 처음에는 `트랜잭션 기초 -> JDBC · JPA · MyBatis 기초 -> 인덱스 기초`까지만 잡고, `deadlock`·`failover`·`cdc`는 증상이 생겼을 때만 관련 문서로 내려간다.

**난이도: 🟢 Beginner**

관련 문서:

- [Database First-Step Bridge](./database-first-step-bridge.md)
- [트랜잭션 기초](./transaction-basics.md)
- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- [인덱스 기초](./index-basics.md)
- [SQL 읽기와 관계형 모델링 기초](./sql-reading-relational-modeling-primer.md)
- [MVCC Read View and Consistent Read Internals](./mvcc-read-view-consistent-read-internals.md)
- [Language README의 beginner 복귀 사다리](../language/README.md#language-java-return-ladder)
- [루트 README](../../README.md)

retrieval-anchor-keywords: database readme, database navigator, database beginner route, database basics, database 처음 뭐부터, db 처음 어디부터, transactional save entity 헷갈려요, save 보이는데 sql 안 보여요, explain 처음인데 뭐부터 봐요, where 조건 하나인데 왜 느리죠, key = null 이 보여요, rows가 너무 커 보여요, using temporary 왜 보여요, group by 처음 헷갈려요, distinct 처음 헷갈려요, deadlock 은 나중에, what is database basics

<a id="database-entry-handoff"></a>
## Spring -> Database handoff

`controller -> service -> repository -> save()` 흐름이 한 화면에 같이 보여도 처음에는 DB 질문을 한 칸만 고르는 편이 안전하다.

| 지금 보이는 beginner 증상 | 먼저 갈 문서 | 왜 이 문서가 첫 칸인가 |
|---|---|---|
| "`왜 저장은 되는데 rollback 범위가 헷갈리죠?`" | [트랜잭션 기초](./transaction-basics.md) | 같이 성공/실패할 경계를 먼저 자르면 `@Transactional`과 `save()`를 분리해 읽을 수 있다 |
| "`save()`는 보이는데 SQL 위치가 안 보여요" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | `Repository`, mapper, SQL 위치를 한 화면에서 구분해 준다 |
| "`Entity`, `Repository`, `table`이 같이 보여서 뭐가 저장 단위인지 모르겠어요" | [Database First-Step Bridge](./database-first-step-bridge.md) | DB 진입용 큰 그림을 먼저 잡은 뒤 `트랜잭션`이나 `SQL 위치` 한 축으로 다시 줄일 수 있다 |

한 장 읽고도 질문이 다시 Java 문법 축으로 줄어들면 [Language README의 beginner 복귀 사다리](../language/README.md#language-java-return-ladder)로 돌아가고, DB 질문이 남아 있으면 이 README의 [빠른 탐색](#빠른-탐색)으로 돌아와 다음 한 칸만 고른다.

<a id="빠른-탐색"></a>
## 빠른 시작

처음 10분은 아래 3문서만 보면 된다.

`트랜잭션 기초 -> JDBC · JPA · MyBatis 기초 -> 인덱스 기초`

위 표는 이 README의 beginner용 `빠른 탐색` 자리다. 다른 primer에서 [Database README: 빠른 탐색](./README.md#빠른-탐색)으로 돌아오라는 링크를 따라오면, 여기서 다시 `트랜잭션`, `SQL 위치`, `인덱스`, `모델링` 중 한 칸만 고르면 된다.

| 지금 막힌 말 | 먼저 열 문서 | 왜 여기서 시작하나 |
|---|---|---|
| "`@Transactional`이 뭐예요?" | [트랜잭션 기초](./transaction-basics.md) | 같이 성공하거나 같이 실패할 범위를 먼저 잡는다 |
| "`save()`는 보이는데 SQL이 안 보여요" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | SQL 위치와 `Repository`/`Entity` 역할을 먼저 분리한다 |
| "`Entity`와 `Repository` 중 누가 DB에 저장해요?" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | 저장 대상과 저장 시작점을 다른 질문으로 나눠 준다 |
| "`WHERE` 조건 하나인데 왜 느리죠?" | [인덱스 기초](./index-basics.md) | 조회 경로 문제인지 먼저 본다 |
| "`GROUP BY` 했는데 `ORDER BY`까지 붙이면 왜 더 느리죠?" | [GROUP BY 결과를 왜 다시 ORDER BY 하면 느려지나요?](./group-by-order-by-different-axis-mysql-postgresql-bridge.md) | 집계 축과 정렬 축이 같은지 다른지 먼저 분리한다 |
| "`table`, `column`, `FK`부터 낯설어요" | [SQL 읽기와 관계형 모델링 기초](./sql-reading-relational-modeling-primer.md) | 저장 모양을 먼저 읽어야 다른 문서가 덜 헷갈린다 |

## 한 화면 읽는 법

초보자는 같은 화면에 `@Transactional`, `save()`, `@Entity`가 같이 보여도 질문을 하나씩 자르는 편이 안전하다.

| 코드 단서 | 지금 붙일 첫 질문 | 먼저 갈 문서 |
|---|---|---|
| `@Transactional` | 어디까지 같이 `commit`/`rollback`하지? | [트랜잭션 기초](./transaction-basics.md) |
| `save()`, `findBy...`, `mapper`, `JdbcTemplate` | SQL은 어디서 찾지? | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| `@Entity`, `table`, `column` | 무엇을 저장하려는 거지? | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md), [SQL 읽기와 관계형 모델링 기초](./sql-reading-relational-modeling-primer.md) |
| "`WHERE` 조건 하나인데 왜 느리죠?" | 조회 경로가 느린 건가? | [인덱스 기초](./index-basics.md) |
| "`EXPLAIN` 처음인데 뭐부터 봐요?", "`key = NULL`이 보여요", "`rows가 너무 커 보여요`" | 조회 경로 단서를 어디서 읽지? | [인덱스 기초](./index-basics.md), [인덱스와 실행 계획](./index-and-explain.md) |
| "`Using temporary`가 보여요", "`GROUP BY`/`DISTINCT`가 왜 여기로 이어져요?" | 집계/중복 제거 때문에 중간 정리가 붙었는지 먼저 본다 | [MySQL `EXPLAIN`에서 `Using temporary`가 보여요](./mysql-explain-using-temporary-beginner-card.md), [SQL 집계 함수와 GROUP BY 기초](./sql-aggregate-groupby-basics.md), [DISTINCT vs GROUP BY 초보자 비교 카드](./distinct-vs-group-by-beginner-card.md) |
| "`Using temporary; Using filesort`가 같이 보여요" | 집계 뒤 재정렬이 붙었나? | [MySQL `EXPLAIN`에서 `Using temporary`가 보여요](./mysql-explain-using-temporary-beginner-card.md), [GROUP BY 결과를 왜 다시 ORDER BY 하면 느려지나요?](./group-by-order-by-different-axis-mysql-postgresql-bridge.md) |

짧게는 "`경계`인지, `SQL 위치`인지, `저장 모양`인지, `조회 경로`인지 먼저 고른다"로 기억하면 된다.

특히 처음에는 `@Transactional`, `Repository`, `Entity`를 한 덩어리로 읽지 않는 편이 안전하다.

- `@Transactional` = 같이 성공/실패할 경계
- `Repository` = 저장/조회 호출을 시작하는 자리
- `Entity` = 저장할 데이터 모양

## 여기서 멈추는 기준

beginner route에서는 아래 단어가 보여도 본문을 길게 파지 않는다.

| 먼저 보인 단어 | 지금 이 README에서 할 일 | 관련 문서 |
|---|---|---|
| `deadlock`, `lock wait`, `retry`, `55P03`, `NOWAIT` | 동시성 follow-up이라는 것만 확인한다 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md), [락 기초](./lock-basics.md), [PostgreSQL `55P03`에서 `NOWAIT`와 `lock_timeout`을 어떻게 나눠 읽을까?](./postgresql-55p03-nowait-vs-lock-timeout-beginner-card.md) |
| `MVCC`, `read view`, `consistent read`, `undo chain` | 격리 수준 내부 동작 follow-up이라는 것만 확인한다 | [MVCC Read View and Consistent Read Internals](./mvcc-read-view-consistent-read-internals.md), [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |
| `flush`, OSIV, lazy loading | JPA 런타임 follow-up이라는 것만 확인한다 | [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md), [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md) |
| `pool timeout`, `replica lag`, `failover` | 운영/배포 질문이라는 것만 확인한다 | [connection-pool-transaction-propagation-bulk-write](./connection-pool-transaction-propagation-bulk-write.md), [Replica Lag와 Read-after-Write](./replica-lag-read-after-write-strategies.md) |
| `cdc`, `backfill`, `cutover` | 데이터 이동 질문이라는 것만 확인한다 | [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md) |

핵심은 "이 README가 부족해서"가 아니라 "질문 축이 이미 다음 단계로 이동했다"는 해석이다.

<a id="database-vs-language-return"></a>
## 다른 카테고리로 돌아갈 때

DB 문서를 읽다가도 실제로는 Java나 Spring 기초가 먼저 필요한 경우가 있다.

| 지금 더 먼저 막히는 말 | 먼저 갈 문서 | 왜 이쪽이 먼저인가 |
|---|---|---|
| "`controller` 전에 `400`/`415`가 나요" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | 아직 DB에 내려오기 전 단계일 수 있다 |
| "`save()`보다 `HashMap#get(...)`이나 `new`가 더 헷갈려요" | [Language README의 beginner 복귀 사다리](../language/README.md#language-java-return-ladder) | Java 실행 모델이 흔들리면 DB 흐름도 같이 흐려진다 |
| "`Repository`는 보이는데 Bean, DI, proxy가 더 낯설어요" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | Spring 역할 구분이 먼저 잡혀야 DB 접근 기술이 덜 섞인다 |

`HashMap#get(...) == null`, `new 했는데 왜 같이 바뀌지?`, `같은 객체와 같은 값이 뭐가 다르지?`처럼 질문이 Java 증상으로 줄어들면 DB deep dive로 더 내려가지 말고 [Language README의 beginner 복귀 사다리](../language/README.md#language-java-return-ladder)로 바로 되돌아간다. 반대로 `save()`, `rollback`, SQL 위치가 다시 남으면 이 README의 [Spring -> Database handoff](#database-entry-handoff)나 [빠른 시작](#빠른-시작)으로 돌아오면 된다.

## 한 줄 정리

database 입문은 `트랜잭션 기초 -> JDBC · JPA · MyBatis 기초 -> 인덱스 기초`까지만 먼저 잡고, 충돌 대응이나 운영 문서는 증상이 붙을 때 관련 문서로 넘기는 것이 가장 안전하다.
