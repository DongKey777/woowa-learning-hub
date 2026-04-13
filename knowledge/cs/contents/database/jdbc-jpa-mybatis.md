# JDBC, JPA, MyBatis

> 신입 백엔드 개발자가 데이터베이스 접근 기술을 구분해서 이해하기 위한 정리

<details>
<summary>Table of Contents</summary>

- [왜 이 주제를 알아야 하나](#왜-이-주제를-알아야-하나)
- [JDBC](#jdbc)
- [JPA와 Hibernate](#jpa와-hibernate)
- [MyBatis](#mybatis)
- [SQLite, H2, MySQL은 무엇이 다른가](#sqlite-h2-mysql은-무엇이-다른가)
- [언제 무엇을 선택할까](#언제-무엇을-선택할까)
- [추천 공식 자료](#추천-공식-자료)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 이 주제를 알아야 하나

백엔드 개발자는 결국 **애플리케이션의 객체 상태를 데이터베이스에 저장하고 다시 복원**해야 한다.  
이때 자바에서 자주 마주치는 선택지가 JDBC, JPA(Hibernate), MyBatis다.

이 셋은 모두 DB에 접근하기 위한 기술이지만,

- SQL을 얼마나 직접 다루는지
- 객체 중심인지 SQL 중심인지
- 반복 코드를 얼마나 감춰주는지

가 다르다.

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
