---
schema_version: 3
title: Spring Template Classes Beginner Primer
concept_id: spring/template-classes-beginner-primer
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 73
review_feedback_tags:
- template-classes
- jdbctemplate-resttemplate-transactiontemplate
- template-callback
- framework-handles-setup
aliases:
- Spring Template classes
- JdbcTemplate RestTemplate TransactionTemplate
- template callback pattern
- framework handles setup cleanup
- Spring template method mental model
intents:
- definition
- comparison
linked_paths:
- contents/spring/spring-jdbctemplate-sqlexception-translation.md
- contents/spring/spring-webclient-vs-resttemplate.md
- contents/spring/spring-transactional-basics.md
- contents/spring/spring-aop-basics.md
- contents/design-pattern/template-method-basics.md
- contents/design-pattern/template-method-framework-lifecycle-examples.md
expected_queries:
- Spring의 JdbcTemplate RestTemplate TransactionTemplate은 왜 Template이라는 이름이야?
- Template 클래스는 반복되는 준비 정리 예외 처리를 어떻게 감춰줘?
- Spring template과 template method pattern의 관계를 초급자에게 설명해줘
- JdbcTemplate과 TransactionTemplate을 같은 mental model로 묶을 수 있어?
contextual_chunk_prefix: |
  이 문서는 Spring ...Template 클래스가 반복되는 setup, cleanup, exception translation 같은
  흐름은 framework가 맡고 사용자는 핵심 callback이나 API 호출만 제공하는 도구라는 mental
  model을 초급자에게 제공한다.
---
# Spring Template 클래스 입문: `JdbcTemplate`, `RestTemplate`, `TransactionTemplate` 큰 그림

> 한 줄 요약: Spring의 `...Template` 클래스는 "반복되는 준비/정리/예외 처리 흐름은 프레임워크가 맡고, 내가 바꾸고 싶은 핵심 한 조각만 콜백이나 API 호출로 넣는" 도구다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `JdbcTemplate`, `RestTemplate`, `TransactionTemplate`를 한 장 mental model로 먼저 묶어 보는 **beginner bridge primer**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [Spring `JdbcTemplate` and `SQLException` Translation](./spring-jdbctemplate-sqlexception-translation.md)
- [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
- [Spring `RestClient` vs `WebClient`: lifecycle와 경계](./spring-restclient-vs-webclient-lifecycle-boundaries.md)
- [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md)
- [Spring `@Transactional` Basics](./spring-transactional-basics.md)
- [템플릿 메소드 패턴 기초](../design-pattern/template-method-basics.md)
- [트랜잭션 기초](../database/transaction-basics.md)
- [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
- [카테고리 README](./README.md)

retrieval-anchor-keywords: spring template class beginner, spring template 클래스 입문, spring template 큰 그림, 스프링 템플릿 클래스 뭐예요, 스프링 template 언제 쓰는지, 처음 배우는데 jdbctemplate 뭐예요, 처음 배우는데 resttemplate 뭐예요, restclient 랑 resttemplate 뭐가 달라요, transactiontemplate 언제 쓰는지, 왜 이름이 template예요, template method 패턴이랑 같은 거예요, 반복 코드 감싸기, jdbc template beginner, resttemplate beginner, transactiontemplate beginner

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

처음 질문이 아래처럼 나오면 이 문서가 맞다.

- "`JdbcTemplate`이 뭐예요? 왜 `Connection`을 직접 안 열어요?"
- "`RestTemplate`는 왜 아직 보이고, 언제 `WebClient`를 봐야 해요?"
- "요즘은 `RestClient`를 쓴다는데 왜 예제에는 아직 `RestTemplate`가 보여요?"
- "`@Transactional`이 있는데 `TransactionTemplate`는 언제 써요?"
- "`왜 이름이 다 `Template`예요?`"
- "`Template Method` 패턴이랑 같은 거예요?"

## 이 문서 다음에 보면 좋은 문서

- SQL 실행보다 예외 번역 경계가 왜 중요한지 보려면 [Spring `JdbcTemplate` and `SQLException` Translation](./spring-jdbctemplate-sqlexception-translation.md)로 이어진다.
- `RestTemplate`를 계속 써도 되는지, `WebClient`로 언제 넘어가는지 보려면 [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)로 이어진다.
- 새 동기 HTTP 클라이언트에서 `RestTemplate` 대신 무엇을 보는지 궁금하면 [Spring `RestClient` vs `WebClient`: lifecycle와 경계](./spring-restclient-vs-webclient-lifecycle-boundaries.md)로 이어진다.
- "`@Transactional` 말고 왜 `TransactionTemplate`가 필요한가?"를 경계 제어 관점으로 보려면 [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md)로 이어진다.
- 트랜잭션 기본기부터 먼저 잡고 싶다면 [Spring `@Transactional` Basics](./spring-transactional-basics.md)를 먼저 본다.

---

## 핵심 개념

처음 배우는데 `Template Method` 패턴, callback, 추상화 같은 말이 한꺼번에 나오면 오히려 더 헷갈린다.
이름 때문에 GoF `Template Method` 패턴과 완전히 같은 개념이라고 느끼기 쉽지만, beginner 기준에서는 "상속 구조를 외우는 일"보다 **반복 절차를 Spring이 고정하고 내가 핵심 한 칸만 채운다**는 감각을 먼저 잡는 편이 안전하다.

먼저 이 한 문장만 잡으면 된다.

**"매번 비슷하게 반복되는 바깥 절차는 Spring이 맡고, 나는 안쪽 핵심 한 칸만 채운다."**

예를 들면:

- DB 작업에서는 연결 열기, 닫기, 예외 번역이 반복된다
- HTTP 호출에서는 요청 만들기, converter 적용, 응답 읽기가 반복된다
- 트랜잭션에서는 시작, 커밋, 롤백이 반복된다

`...Template` 클래스는 이런 반복 껍데기를 공통화한 도구다.

처음엔 아래처럼 두 칸으로 나눠 읽으면 용어가 훨씬 덜 무섭다.

| 구분 | Spring이 고정하는 바깥 흐름 | 내가 채우는 안쪽 한 칸 |
|---|---|---|
| `JdbcTemplate` | 연결 열기, SQL 실행 준비, 예외 번역, 정리 | SQL 문장, row mapping |
| `RestTemplate` | 요청 만들기, HTTP 호출, 응답 변환, 에러 처리 | 어떤 URL을 어떤 방식으로 호출할지 |
| `TransactionTemplate` | 시작, 커밋, 롤백, 트랜잭션 상태 관리 | 어느 코드 블록을 실행할지 |

즉 초보자 기준 mental model은 "`Template` = 복잡한 엔진"보다 **"바깥 껍데기는 고정, 안쪽 한 칸만 내가 넣는 틀"**에 가깝다.

그래서 beginner 관점에서는 "패턴 이름"보다 아래 질문이 더 중요하다.

- 지금 내가 반복해서 쓰는 준비/정리 코드가 있는가?
- 그 바깥 절차는 거의 늘 같고, 안쪽 핵심 작업만 달라지는가?
- 그 공통 절차를 프레임워크가 대신 책임져 주면 코드가 더 읽기 쉬워지는가?

이 질문에 `예`가 많으면 template 계열이 잘 맞는다.

## 왜 초반에 자꾸 용어가 헷갈리는가

입문자 입장에서는 세 클래스가 서로 다른 문제를 푸는데도 이름이 너무 비슷하다. 그래서 "`JdbcTemplate`는 DB 도구", "`RestTemplate`는 HTTP 도구", "`TransactionTemplate`는 트랜잭션 경계 도구"처럼 **대상부터 먼저 분리**하는 편이 빠르다.

| 지금 보이는 코드 | 먼저 떠올릴 질문 | 붙여야 할 mental model |
|---|---|---|
| `jdbcTemplate.query(...)` | "DB 접근 반복 코드를 줄이려는가?" | SQL 실행 바깥 껍데기를 Spring이 대신 맡는다 |
| `restTemplate.getForObject(...)` | "외부 HTTP 호출을 한 줄로 감싸려는가?" | 요청/응답 변환 껍데기를 Spring이 맡는다 |
| `transactionTemplate.execute(...)` | "이 코드 블록만 트랜잭션으로 묶고 싶은가?" | 시작/커밋/롤백 껍데기를 Spring이 맡는다 |

초급자 질문을 한 줄로 더 줄이면 아래처럼 읽어도 된다.

- `JdbcTemplate`: "`Connection` 열고 닫는 코드가 왜 안 보이지?" -> Spring이 바깥 JDBC 절차를 맡는다.
- `RestTemplate`: "HTTP 호출인데 왜 요청 객체를 매번 안 만들지?" -> Spring이 호출 껍데기를 맡는다.
- `TransactionTemplate`: "`@Transactional` 없이도 왜 rollback이 되지?" -> Spring이 그 블록을 트랜잭션으로 감싼다.

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

용어 때문에 멈출 필요는 없다.

- `callback`은 "Spring이 정해 둔 타이밍에 내가 넣는 한 조각 코드" 정도로 읽으면 충분하다.
- `Template Method`라는 패턴 이름은 나중 문제다. 이 문서에서는 "반복 껍데기를 공통화했다"만 잡아도 다음 문서로 넘어가는 데 충분하다.

## 처음 보는 상황에 바로 대입해 보기

아래처럼 읽으면 glossary 대신 실제 장면으로 기억하기 쉽다.

| 상황 | 템플릿 감각 | 왜 이 템플릿이 맞는가 |
|---|---|---|
| "회원 목록 SQL을 실행할 때 `try-catch-finally`가 너무 길어요" | `JdbcTemplate` | SQL만 남기고 JDBC 준비/정리를 감춘다 |
| "결제 서비스에 동기 HTTP GET/POST를 보내야 해요" | `RestTemplate` | 요청 생성, 응답 바인딩, 기본 에러 처리를 감싼다 |
| "한 메서드 전체가 아니라 이 두 줄만 트랜잭션으로 묶고 싶어요" | `TransactionTemplate` | 코드 블록 단위로 트랜잭션 경계를 직접 잡는다 |

초반에는 "이 클래스의 모든 메서드 이름"보다 "`어떤 반복 껍데기를 대신 치워 주는가`"를 먼저 기억하면 된다.

## 자주 섞이는 오해 3가지

### 1. `Template`면 다 구식인가?

아니다. 중요한 것은 이름이 아니라 **어떤 경계를 공통화하느냐**다.

- `RestTemplate`는 새 Spring 앱에서 기본 추천이 아니지만, 단순 동기 호출에서는 여전히 읽기 쉬운 선택일 수 있다.
- Spring 6+ 계열 새 코드에서는 동기 클라이언트로 `RestClient`를 먼저 보는 경우가 많지만, 기존 자료와 레거시 코드에서는 `RestTemplate`가 여전히 자주 보인다.
- `JdbcTemplate`는 지금도 SQL 중심 코드에서 자주 쓴다.
- `TransactionTemplate`는 선언형 트랜잭션이 어색한 일부 경계에서 여전히 유용하다.

즉 "template라서 구식"이 아니라, **문제에 맞는 경계인가**, 그리고 "지금 보는 코드가 새 코드인지 기존 코드인지"를 함께 봐야 한다.

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

## 흔한 증상별 다음 문서

| 지금 막힌 문장 | 바로 갈 문서 | 이유 |
|---|---|---|
| "`JdbcTemplate` 예외가 왜 `SQLException`이 아니라 다른 예외로 와요?" | [Spring `JdbcTemplate` and `SQLException` Translation](./spring-jdbctemplate-sqlexception-translation.md) | 예외 번역이 이 템플릿의 핵심 가치다 |
| "`RestTemplate`가 구식이라는데 지금 코드에서 당장 바꿔야 해요?" | [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md) | 교체 기준과 안전한 판단선을 알려 준다 |
| "`RestTemplate` 말고 `RestClient`도 본다는데 둘을 어떻게 읽어요?" | [Spring `RestClient` vs `WebClient`: lifecycle와 경계](./spring-restclient-vs-webclient-lifecycle-boundaries.md) | 새 synchronous client 선택지를 현재 Spring 세대 기준으로 이어 준다 |
| "`@Transactional`로 안 풀리고 블록 단위 제어가 필요해요" | [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md) | 선언형과 프로그램적 경계 차이를 바로 이어 준다 |
| "트랜잭션 자체가 아직 뭐예요 단계예요" | [트랜잭션 기초](../database/transaction-basics.md) | spring 바깥 개념부터 먼저 잡아야 덜 헷갈린다 |

## 언제 어떤 문서로 바로 가면 되는가

| 지금 궁금한 것 | 먼저 볼 문서 |
|---|---|
| `JdbcTemplate`가 왜 단순 편의 API가 아니라는지 | [Spring `JdbcTemplate` and `SQLException` Translation](./spring-jdbctemplate-sqlexception-translation.md) |
| `RestTemplate`를 계속 써도 되는지, `WebClient`와 차이가 뭔지 | [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md) |
| 새 동기 HTTP 클라이언트에서 `RestClient`를 언제 먼저 보는지 | [Spring `RestClient` vs `WebClient`: lifecycle와 경계](./spring-restclient-vs-webclient-lifecycle-boundaries.md) |
| `@Transactional` 대신 코드 블록 단위 트랜잭션이 왜 필요한지 | [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md) |

## 한 줄 정리

Spring의 `...Template` 클래스는 "반복되는 인프라 절차는 Spring이 맡고, 내가 바꾸고 싶은 핵심 작업만 채우게 하는 틀"이라고 보면 초반 큰 그림을 잡기 쉽다.
