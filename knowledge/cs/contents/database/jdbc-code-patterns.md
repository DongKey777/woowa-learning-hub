# JDBC 실전 코드 패턴

> JDBC를 설명할 때 “원리”를 넘어 “실제로 어떻게 짜는가”를 보기 위한 문서

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [기본 조회 패턴](#기본-조회-패턴)
- [기본 저장 패턴](#기본-저장-패턴)
- [트랜잭션 패턴](#트랜잭션-패턴)
- [예외와 자원 정리](#예외와-자원-정리)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

## 왜 이 문서가 필요한가

JDBC는 이론 설명만으로 끝나기 쉽다.

하지만 실제로는

- connection을 어디서 열지
- statement를 어떻게 만들지
- 트랜잭션을 어디서 시작하고 끝낼지
- 예외는 어디서 감쌀지

가 중요하다.

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

- auto-commit 끄기
- 같은 connection으로 여러 SQL 실행
- 성공하면 commit
- 실패하면 rollback

---

## 예외와 자원 정리

JDBC 코드는 예외와 자원 정리를 소홀히 하면 금방 망가진다.

중요한 기준:

- `Connection`, `PreparedStatement`, `ResultSet`는 닫혀야 한다
- `SQLException`을 그대로 퍼뜨릴지 감쌀지 기준이 필요하다
- 도메인 예외와 인프라 예외를 구분해야 한다

---

## 시니어 관점 질문

- 트랜잭션 경계는 service에서 가져야 하나 repository에서 가져야 하나?
- `Connection`을 매번 열고 닫는 구조가 문제가 되는 시점은 언제인가?
- `SQLException`을 모두 `RuntimeException`으로 감싸면 얻는 것과 잃는 것은 무엇인가?
- row 매핑 로직이 길어질 때 `RowMapper`를 도입할 기준은 무엇인가?
