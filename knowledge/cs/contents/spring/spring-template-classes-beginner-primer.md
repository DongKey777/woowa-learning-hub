# Spring Template 클래스 입문: `JdbcTemplate`, `RestTemplate`, `TransactionTemplate` 큰 그림

> 한 줄 요약: Spring의 `...Template` 클래스는 "반복되는 준비/정리/예외 처리 흐름은 프레임워크가 맡고, 내가 바꾸고 싶은 핵심 한 조각만 콜백이나 API 호출로 넣는" 도구다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `JdbcTemplate`, `RestTemplate`, `TransactionTemplate`를 한 장 mental model로 먼저 묶어 보는 **beginner bridge primer**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring `JdbcTemplate` and `SQLException` Translation](./spring-jdbctemplate-sqlexception-translation.md)
> - [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
> - [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md)
> - [Spring `@Transactional` Basics](./spring-transactional-basics.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)

retrieval-anchor-keywords: spring template class beginner, spring template 클래스 입문, spring template 큰 그림, 스프링 템플릿 클래스 뭐예요, 스프링 template 언제 쓰는지, 처음 배우는데 jdbctemplate 뭐예요, 처음 배우는데 resttemplate 뭐예요, transactiontemplate 언제 쓰는지, template callback pattern, template method pattern spring, 반복 코드 감싸기, 준비 정리 예외처리 공통화, jdbc template beginner, resttemplate beginner, transactiontemplate beginner

## 처음 배우는데 헷갈릴 때: 큰 그림 30초

초보자 기준으로는 이름보다 "무엇을 대신 해 주는가"부터 보면 된다.

| 클래스 | 프레임워크가 대신 해 주는 것 | 내가 직접 신경 쓰는 것 | 언제 쓰는지 |
|---|---|---|---|
| `JdbcTemplate` | 커넥션/statement/result set 정리, JDBC 예외 번역 | SQL과 row mapping | SQL 중심 데이터 접근을 할 때 |
| `RestTemplate` | HTTP 요청 생성/전송, message converter, 응답 바인딩 | 어떤 URL을 어떻게 호출할지 | 단순한 동기 outbound HTTP 호출 |
| `TransactionTemplate` | 트랜잭션 시작/커밋/롤백 | 어느 코드 블록을 트랜잭션으로 감쌀지 | 메서드보다 더 잘게 경계를 자를 때 |

한 줄 감각으로 외우면 이렇다.

- `JdbcTemplate`: "JDBC boilerplate를 대신 감싸는 틀"
- `RestTemplate`: "HTTP 호출 boilerplate를 대신 감싸는 틀"
- `TransactionTemplate`: "트랜잭션 boilerplate를 대신 감싸는 틀"

즉 `Template`라는 이름은 "모든 걸 추상화한다"보다, **반복되는 바깥 흐름을 고정해 두고 안쪽 핵심 작업만 바꿔 끼운다**에 가깝다.

## 이 문서 다음에 보면 좋은 문서

- SQL 실행보다 예외 번역 경계가 왜 중요한지 보려면 [Spring `JdbcTemplate` and `SQLException` Translation](./spring-jdbctemplate-sqlexception-translation.md)로 이어진다.
- `RestTemplate`를 계속 써도 되는지, `WebClient`로 언제 넘어가는지 보려면 [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)로 이어진다.
- "`@Transactional` 말고 왜 `TransactionTemplate`가 필요한가?"를 경계 제어 관점으로 보려면 [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md)로 이어진다.
- 트랜잭션 기본기부터 먼저 잡고 싶다면 [Spring `@Transactional` Basics](./spring-transactional-basics.md)를 먼저 본다.

---

## 핵심 개념

처음 배우는데 `Template Method` 패턴, callback, 추상화 같은 말이 한꺼번에 나오면 오히려 더 헷갈린다.

먼저 이 한 문장만 잡으면 된다.

**"매번 비슷하게 반복되는 바깥 절차는 Spring이 맡고, 나는 안쪽 핵심 한 칸만 채운다."**

예를 들면:

- DB 작업에서는 연결 열기, 닫기, 예외 번역이 반복된다
- HTTP 호출에서는 요청 만들기, converter 적용, 응답 읽기가 반복된다
- 트랜잭션에서는 시작, 커밋, 롤백이 반복된다

`...Template` 클래스는 이런 반복 껍데기를 공통화한 도구다.

그래서 beginner 관점에서는 "패턴 이름"보다 아래 질문이 더 중요하다.

- 지금 내가 반복해서 쓰는 준비/정리 코드가 있는가?
- 그 바깥 절차는 거의 늘 같고, 안쪽 핵심 작업만 달라지는가?
- 그 공통 절차를 프레임워크가 대신 책임져 주면 코드가 더 읽기 쉬워지는가?

이 질문에 `예`가 많으면 template 계열이 잘 맞는다.

---

## 큰 그림 코드 감각

세 클래스는 겉모습은 달라도 읽는 감각이 비슷하다.

```text
공통 절차 시작
-> 내가 넣은 핵심 작업 실행
-> 실패하면 공통 정책 적용
-> 정리 후 결과 반환
```

### `JdbcTemplate`

```java
jdbcTemplate.query("select id, name from users", rowMapper);
```

이 한 줄 뒤에서 Spring은 대충 이런 바깥 일을 맡는다.

- JDBC 리소스 준비
- SQL 실행
- 예외가 나면 `DataAccessException` 계층으로 번역
- 리소스 정리

### `RestTemplate`

```java
restTemplate.getForObject("/profiles/{id}", Profile.class, id);
```

이 한 줄 뒤에서 Spring은 대충 이런 바깥 일을 맡는다.

- 요청 객체 구성
- HTTP 호출
- converter로 응답 바인딩
- 에러 응답 처리

### `TransactionTemplate`

```java
transactionTemplate.executeWithoutResult(status -> service.process(command));
```

이 한 줄 뒤에서 Spring은 대충 이런 바깥 일을 맡는다.

- 트랜잭션 시작
- 콜백 실행
- 성공 시 커밋
- 실패 시 롤백

핵심은 셋 다 "내 비즈니스 코드가 공통 인프라 흐름 한가운데 들어간다"는 점이다.

---

## 자주 섞이는 오해 3가지

### 1. `Template`면 다 구식인가?

아니다. 중요한 것은 이름이 아니라 **어떤 경계를 공통화하느냐**다.

- `RestTemplate`는 새 Spring 앱에서 기본 추천이 아니지만, 단순 동기 호출에서는 여전히 읽기 쉬운 선택일 수 있다.
- `JdbcTemplate`는 지금도 SQL 중심 코드에서 자주 쓴다.
- `TransactionTemplate`는 선언형 트랜잭션이 어색한 일부 경계에서 여전히 유용하다.

즉 "template라서 구식"이 아니라, **문제에 맞는 경계인가**로 봐야 한다.

### 2. `Template`면 모든 세부 제어를 잃는가?

그렇지 않다. 세부 제어를 완전히 포기하는 것이 아니라, **매번 직접 쓰지 않아도 되는 기본 절차를 맡기는 것**에 가깝다.

그래서 실무 질문은 보통 이렇게 바뀐다.

- `JdbcTemplate`에서 어떤 예외 계층으로 번역되는가?
- `RestTemplate` 대신 `WebClient`가 필요한 규모인가?
- `TransactionTemplate`가 정말 필요한 경계인가, 그냥 `@Transactional`이면 되는가?

### 3. 이름이 같으면 다 같은 수준의 도구인가?

아니다. 이름은 비슷해도 다루는 대상이 다르다.

| 클래스 | 다루는 대상 | 초보자용 질문 |
|---|---|---|
| `JdbcTemplate` | DB 접근 | "SQL 실행 주변 반복 코드를 줄이고 싶은가?" |
| `RestTemplate` | 외부 HTTP 호출 | "동기 HTTP 호출을 간단히 감싸고 싶은가?" |
| `TransactionTemplate` | 트랜잭션 경계 | "메서드보다 작은 코드 블록을 트랜잭션으로 묶고 싶은가?" |

---

## 언제 어떤 문서로 바로 가면 되는가

| 지금 궁금한 것 | 먼저 볼 문서 |
|---|---|
| `JdbcTemplate`가 왜 단순 편의 API가 아니라는지 | [Spring `JdbcTemplate` and `SQLException` Translation](./spring-jdbctemplate-sqlexception-translation.md) |
| `RestTemplate`를 계속 써도 되는지, `WebClient`와 차이가 뭔지 | [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md) |
| `@Transactional` 대신 코드 블록 단위 트랜잭션이 왜 필요한지 | [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md) |

## 한 줄 정리

Spring의 `...Template` 클래스는 "반복되는 인프라 절차는 Spring이 맡고, 내가 바꾸고 싶은 핵심 작업만 채우게 하는 틀"이라고 보면 초반 큰 그림을 잡기 쉽다.
