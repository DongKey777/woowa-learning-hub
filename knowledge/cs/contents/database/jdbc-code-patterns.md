---
schema_version: 3
title: JDBC 실전 코드 패턴
concept_id: database/jdbc-code-patterns
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- jdbc-code-patterns
- connection-lifecycle
- manual-commit-rollback
aliases:
- jdbc preparedstatement resultset
- try-with-resources
- auto commit
- setAutoCommit false
- manual commit rollback
- connection lifecycle
- connection borrow return
- getConnection close pattern
- jdbc repository example
- 순수 JDBC 예제
symptoms:
- raw JDBC 코드에서 Connection, PreparedStatement, ResultSet, commit, rollback, close 순서를 읽지 못하고 있어
- setAutoCommit(false)와 manual transaction 경계가 connection pool 점유 시간과 어떻게 연결되는지 헷갈려
- batch insert나 generated keys 코드를 문법보다 transaction chunk와 resource cleanup 관점으로 봐야 해
intents:
- troubleshooting
- design
prerequisites:
- database/jdbc-jpa-mybatis-basics
- database/transaction-basics
next_docs:
- database/jdbc-jpa-mybatis
- database/connection-pool-transaction-propagation-bulk-write
- database/hikari-connection-pool-tuning
- database/transaction-isolation-locking
linked_paths:
- contents/database/jdbc-jpa-mybatis-basics.md
- contents/database/jdbc-jpa-mybatis.md
- contents/database/transaction-basics.md
- contents/database/transaction-isolation-locking.md
- contents/database/connection-pool-transaction-propagation-bulk-write.md
- contents/database/hikari-connection-pool-tuning.md
confusable_with:
- database/jdbc-jpa-mybatis-basics
- database/jdbc-jpa-mybatis
- database/connection-pool-transaction-propagation-bulk-write
forbidden_neighbors: []
expected_queries:
- raw JDBC 코드를 Connection, PreparedStatement, ResultSet, commit, rollback, close 순서로 어떻게 읽어?
- setAutoCommit(false)를 쓰면 transaction 경계와 connection pool 반환이 어떻게 달라져?
- try-with-resources가 JDBC에서 statement와 resultset 누수를 줄이는 이유는 뭐야?
- JDBC batch insert는 chunk 크기와 commit 주기를 왜 같이 봐야 해?
- close가 물리 connection 종료가 아니라 pool 반환일 수 있다는 점을 초보자에게 설명해줘
contextual_chunk_prefix: |
  이 문서는 raw JDBC 코드를 Connection, PreparedStatement, ResultSet, execute, commit/rollback, close 순서로 읽고 connection lifecycle을 이해하는 advanced playbook이다.
  JDBC PreparedStatement, autoCommit, manual commit rollback, connection lifecycle 같은 자연어 질문이 본 문서에 매핑된다.
---
# JDBC 실전 코드 패턴

> 한 줄 요약: 이 문서는 raw JDBC 코드를 실제로 만났을 때 `Connection -> PreparedStatement -> ResultSet -> commit/rollback -> close` 순서로 읽게 만드는 follow-up entry다.

**난이도: 🔴 Advanced**

관련 문서:

- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md)
- [트랜잭션 기초](./transaction-basics.md)
- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
- [HikariCP 튜닝](./hikari-connection-pool-tuning.md)

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [기본 조회 패턴](#기본-조회-패턴)
- [기본 저장 패턴](#기본-저장-패턴)
- [생성된 키 반환 패턴](#생성된-키-반환-패턴)
- [batch insert 패턴](#batch-insert-패턴)
- [트랜잭션 패턴](#트랜잭션-패턴)
- [예외와 자원 정리](#예외와-자원-정리)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

> retrieval-anchor-keywords: jdbc preparedstatement resultset, try-with-resources, auto commit, setautocommit false, manual commit rollback, connection lifecycle, connection borrow return, getconnection close pattern, jdbc repository example, jdbc generated keys, jdbc row mapping, connection close leak, 순수 jdbc 예제, jdbc 코드 예시

## 먼저 큰 그림

처음 JDBC 코드를 읽을 때는 문법보다 **커넥션을 빌리고 반납하는 순서**를 먼저 보면 덜 헷갈린다.

```text
Connection 획득
  -> PreparedStatement 준비
  -> 파라미터 바인딩
  -> executeQuery / executeUpdate
  -> 필요하면 commit / 실패하면 rollback
  -> close 로 자원 반납
```

이 문서는 database 입문 전체의 첫 문서가 아니라, `PreparedStatement`나 `JdbcTemplate`가 실제로 보일 때 여는 follow-up이다. 초보자 기준 첫 질문은 "이 SQL이 맞나?"보다 아래 셋이다.

| 지금 먼저 볼 것 | 왜 먼저 보나 |
|---|---|
| `getConnection()` 위치 | connection을 언제 빌리는지 알아야 transaction 길이가 보인다 |
| `setAutoCommit(false)` 유무 | 여러 SQL을 한 묶음으로 보는지 바로 알 수 있다 |
| `close()` 위치 | 누수가 있는지, pool 반환이 늦는지 감이 잡힌다 |

증상 문장으로 바꾸면 아래처럼 라우팅하면 된다.

| 지금 막힌 문장 | 먼저 읽을 포인트 |
|---|---|
| "`PreparedStatement`는 보이는데 전체 흐름이 안 잡혀요" | 이 문서의 기본 조회/저장 패턴 |
| "`setAutoCommit(false)`가 왜 필요한지 모르겠어요" | 이 문서의 트랜잭션 패턴, [트랜잭션 기초](./transaction-basics.md) |
| "`close()` 했는데 왜 connection pool 이야기가 또 나오죠?" | 이 문서의 트랜잭션 패턴까지만 보고, 운영 설명은 [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) |

## 이 문서 다음에 보면 좋은 문서

- "JDBC가 JPA/MyBatis와 뭐가 다른가?"부터 헷갈리면 [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)로 먼저 돌아간다.
- `autoCommit`, `commit/rollback`, 락 범위가 왜 중요한지 이어서 보려면 [트랜잭션 기초](./transaction-basics.md), [트랜잭션 격리수준과 락](./transaction-isolation-locking.md) 순서가 바로 연결된다.
- `connection lifecycle`, `getConnection()` 시점, `close()`가 실제로 pool 반환인지가 궁금하면 [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)와 [HikariCP 튜닝](./hikari-connection-pool-tuning.md)으로 넘어가면 된다.
- `batch insert`를 단순 문법이 아니라 chunk 크기, 커밋 주기, pool 점유 시간까지 같이 보려면 [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)를 바로 이어서 읽는다.

## 왜 이 문서가 필요한가

JDBC는 이론 설명만으로 끝나기 쉽다.

하지만 실제로는

- connection을 어디서 열지
- `autoCommit`을 언제 끌지
- statement를 어떻게 만들지
- 트랜잭션을 어디서 시작하고 끝낼지
- 예외는 어디서 감쌀지

가 중요하다.

검색어로 들어오면 다음처럼 바로 이어 보면 된다.

- `autoCommit`, `commit`, `rollback`, `manual transaction` -> [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- `connection lifecycle`, `connection borrow/return`, `close returns to pool` -> [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
- `batch insert`, `bulk insert`, `chunk commit` -> [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)

---

## 기본 조회 패턴

```java
try (Connection connection = connectionProvider.getConnection();
     PreparedStatement statement = connection.prepareStatement(
             "SELECT x, y, name, team FROM pieces WHERE game_id = ?")) {

    statement.setLong(1, gameId);

    try (ResultSet resultSet = statement.executeQuery()) {
        while (resultSet.next()) {
            int x = resultSet.getInt("x");
            int y = resultSet.getInt("y");
            String name = resultSet.getString("name");
            String team = resultSet.getString("team");
        }
    }
}
```

핵심:

- `try-with-resources`로 닫기
- SQL과 파라미터 분리
- row를 읽어서 도메인으로 복원

---

## 기본 저장 패턴

```java
try (Connection connection = connectionProvider.getConnection();
     PreparedStatement statement = connection.prepareStatement(
             "INSERT INTO games(turn, status) VALUES (?, ?)")) {

    statement.setString(1, turn);
    statement.setString(2, status);
    statement.executeUpdate();
}
```

조회와 다른 점은

- `executeQuery()` 대신 `executeUpdate()`

를 쓴다는 점이다.

---

## 생성된 키 반환 패턴

자동 증가 PK나 surrogate key를 바로 받아와야 하면 `RETURN_GENERATED_KEYS`를 함께 쓴다.

```java
try (Connection connection = connectionProvider.getConnection();
     PreparedStatement statement = connection.prepareStatement(
             "INSERT INTO games(turn, status) VALUES (?, ?)",
             Statement.RETURN_GENERATED_KEYS)) {

    statement.setString(1, turn);
    statement.setString(2, status);
    statement.executeUpdate();

    try (ResultSet generatedKeys = statement.getGeneratedKeys()) {
        if (generatedKeys.next()) {
            long gameId = generatedKeys.getLong(1);
        }
    }
}
```

핵심:

- insert와 키 조회를 같은 statement lifecycle 안에서 끝낸다
- generated key를 못 받는 드라이버/DB 조합인지 확인한다
- 저장 직후 다른 조회를 날리기 전에, 반환값만으로도 다음 로직을 진행할 수 있으면 그 편이 더 단순하다

---

## batch insert 패턴

네트워크 왕복과 statement 실행 오버헤드를 줄이려면 `addBatch()` / `executeBatch()`를 묶어 쓴다.

```java
try (Connection connection = connectionProvider.getConnection();
     PreparedStatement statement = connection.prepareStatement(
             "INSERT INTO pieces(game_id, x, y, name, team) VALUES (?, ?, ?, ?, ?)")) {

    connection.setAutoCommit(false);

    for (Piece piece : pieces) {
        statement.setLong(1, piece.gameId());
        statement.setInt(2, piece.x());
        statement.setInt(3, piece.y());
        statement.setString(4, piece.name());
        statement.setString(5, piece.team());
        statement.addBatch();
    }

    statement.executeBatch();
    connection.commit();
}
```

핵심:

- batch는 왕복을 줄이지만, 너무 크게 잡으면 rollback 비용과 락 유지 시간이 커진다
- chunk 크기와 commit 주기를 같이 정해야 한다
- batch insert가 빨라도 커넥션을 오래 점유하면 pool starvation으로 번질 수 있다

---

## 트랜잭션 패턴

```java
Connection connection = connectionProvider.getConnection();
try {
    connection.setAutoCommit(false);

    updateGame(connection, ...);
    deleteCapturedPiece(connection, ...);
    updateMovedPiece(connection, ...);

    connection.commit();
} catch (SQLException e) {
    connection.rollback();
    throw new RuntimeException(e);
} finally {
    connection.close();
}
```

핵심:

- 기본 `autoCommit=true` 흐름에서 명시적으로 빠져나와야 여러 SQL을 하나의 transaction으로 묶을 수 있다
- 같은 connection으로 여러 SQL 실행
- 성공하면 commit
- 실패하면 rollback
- 마지막 `close()`는 물리 연결 종료가 아니라 pool 환경에서는 "반환"일 수 있으므로 connection lifecycle 전체를 같이 봐야 한다

이 패턴을 읽을 때는 질문을 두 갈래로 나누면 좋다.

- `왜 rollback이 필요한가`, `격리수준이나 락은 여기서 어떻게 이어지나` -> [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- `close()`가 pool에 어떤 영향을 주나, 긴 transaction이 왜 starvation으로 번지나 -> [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)

---

## 예외와 자원 정리

JDBC 코드는 예외와 자원 정리를 소홀히 하면 금방 망가진다.

중요한 기준:

- `Connection`, `PreparedStatement`, `ResultSet`는 닫혀야 한다
- `SQLException`을 그대로 퍼뜨릴지 감쌀지 기준이 필요하다
- 도메인 예외와 인프라 예외를 구분해야 한다
- `rollback()` 자체도 실패할 수 있어서, 실패 경로 로깅을 따로 남길지 정해야 한다
- `finally`에서 `close()`만 호출하는 패턴보다 `try-with-resources`를 우선한다

---

## 시니어 관점 질문

- 트랜잭션 경계는 service에서 가져야 하나 repository에서 가져야 하나?
- `Connection`을 매번 열고 닫는 구조가 문제가 되는 시점은 언제인가?
- `SQLException`을 모두 `RuntimeException`으로 감싸면 얻는 것과 잃는 것은 무엇인가?
- row 매핑 로직이 길어질 때 `RowMapper`를 도입할 기준은 무엇인가?
