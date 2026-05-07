---
schema_version: 3
title: Spring/JPA SQLSTATE 23P01 Bridge
concept_id: database/spring-jpa-sqlstate-23p01-bridge
canonical: true
category: database
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- spring
- jpa
- postgresql
- sqlstate
- exclusion-constraint
aliases:
- Spring JPA SQLSTATE 23P01 bridge
- DataIntegrityViolationException 23P01
- Spring exception wrapper SQLSTATE extract
- JPA ConstraintViolationException PSQLException
- PostgreSQL overlap conflict Spring mapping
- SQLSTATE 23P01
- booking overlap 409 problem detail
- raw DB message leak prevention
- SQLSTATE extractor
- exclusion constraint conflict
symptoms:
- DataIntegrityViolationException 같은 wrapper 예외 안에 감긴 SQLSTATE 23P01을 꺼내야 해
- PostgreSQL exclusion constraint conflict를 raw DB 메시지가 아니라 BOOKING_OVERLAP 제품 문장으로 번역해야 해
- 23P01과 23505를 둘 다 409로 낼 수 있지만 제품 의미가 다르다는 점을 설명해야 해
intents:
- definition
- troubleshooting
- design
prerequisites:
- database/postgresql-23p01-handling-note
- database/db-signal-service-result-http-bridge
next_docs:
- database/postgresql-23p01-vs-23505-product-language-card
- spring/problemdetail-error-response-design
- spring/jdbctemplate-sqlexception-translation
linked_paths:
- contents/database/postgresql-23p01-handling-note.md
- contents/database/postgresql-23p01-vs-23505-product-language-card.md
- contents/database/db-signal-service-result-http-bridge.md
- contents/spring/spring-jdbctemplate-sqlexception-translation.md
- contents/spring/spring-problemdetail-error-response-design.md
confusable_with:
- database/postgresql-23p01-vs-23505-product-language-card
- database/db-signal-service-result-http-bridge
- database/spring-cannotacquirelockexception-root-sql-code
forbidden_neighbors: []
expected_queries:
- Spring/JPA DataIntegrityViolationException 안에서 PostgreSQL SQLSTATE 23P01을 어떻게 꺼내?
- exclusion constraint conflict 23P01을 raw DB message 대신 BOOKING_OVERLAP 409 ProblemDetail로 번역하는 흐름을 알려줘
- SQLSTATE 23P01과 23505는 둘 다 conflict처럼 보이지만 제품 언어가 어떻게 달라?
- JPA ConstraintViolationException, PersistenceException, PSQLException wrapper를 cause chain으로 따라가야 하는 이유는?
- SQLSTATE extractor helper로 root SQLException getSQLState를 읽는 beginner 패턴을 보여줘
contextual_chunk_prefix: |
  이 문서는 Spring/JPA wrapper exception 안의 PostgreSQL SQLSTATE 23P01을 추출해 booking overlap 409 product language로 번역하는 beginner bridge다.
  DataIntegrityViolationException 23P01, exclusion constraint conflict, SQLSTATE extractor, raw DB message leak prevention 질문이 본 문서에 매핑된다.
---
# Spring/JPA 예외 래퍼에서 `SQLSTATE 23P01` 꺼내는 브리지

> 한 줄 요약: Spring/JPA에서는 `23P01`이 `DataIntegrityViolationException` 같은 바깥 예외 안에 감겨 올라오기 쉬우므로, 초보자는 **wrapper 예외 이름에서 멈추지 말고 안쪽 `SQLException`의 `SQLSTATE`를 읽은 뒤 제품용 conflict 문장으로 번역**하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [PostgreSQL `23P01` Handling Note](./postgresql-23p01-handling-note.md)
- [PostgreSQL `23P01` vs `23505` Product Language Card](./postgresql-23p01-vs-23505-product-language-card.md)
- [DB 신호 -> 서비스 결과 enum -> HTTP 응답 브리지](./db-signal-service-result-http-bridge.md)
- [Spring `JdbcTemplate` and `SQLException` Translation](../spring/spring-jdbctemplate-sqlexception-translation.md)
- [Spring `ProblemDetail` Error Response Design](../spring/spring-problemdetail-error-response-design.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring jpa sqlstate 23p01 bridge, dataintegrityviolationexception 23p01, spring exception wrapper sqlstate extract, jpa constraintviolationexception psql exception, sqlstate 23p01 어디서 읽지, spring 예약 겹침 예외 처리, postgres overlap conflict spring mapping, psql exception getsqlstate beginner, spring jpa exclusion constraint conflict, raw db message leak prevention, booking overlap 409 problem detail, sqlstate extractor basics

## 핵심 개념

멘탈모델은 한 줄이면 된다.

> Spring/JPA 예외는 봉투이고, `23P01`은 안쪽 `SQLException`에 적힌 사고 코드다.

그래서 바깥에서 `DataIntegrityViolationException`만 보고 "입력값 오류인가?", "DB 장애인가?"를 바로 결정하면 흔들리기 쉽다.

`23P01`을 정확히 다루려면 보통 아래 두 단계를 분리한다.

1. cause chain 안쪽에서 `SQLException#getSQLState()`를 읽는다.
2. 읽은 값이 `23P01`이면 raw DB 문장 대신 `예약 시간이 겹칩니다` 같은 제품 문장으로 번역한다.

핵심은 **DB 메시지를 밖으로 노출하지 않고도 내부 분류는 정확하게 유지**하는 것이다.

## 한눈에 보기

| 층 | 흔히 보이는 예외 이름 | 여기서 바로 판단하면 생기는 오해 | 실제로 봐야 할 것 |
|---|---|---|---|
| Spring DAO | `DataIntegrityViolationException` | 단순 validation 실패처럼 읽기 쉽다 | 안쪽 `SQLException`의 `SQLSTATE` |
| JPA/Hibernate | `ConstraintViolationException`, `PersistenceException`, `JpaSystemException` | Hibernate 이름만 보고 DB 종류를 잊기 쉽다 | 안쪽 `SQLException` 또는 `PSQLException` |
| PostgreSQL driver | `PSQLException` | 여기까지 내려오면 거의 끝났다고 생각하기 쉽다 | `getSQLState()` 결과가 `23P01`인지 |

초급자용 흐름:

`Spring/JPA wrapper`
-> `SQLException 찾기`
-> `sqlState == 23P01`
-> `BOOKING_OVERLAP / 409 Conflict`
-> 사용자에게는 짧은 제품 문장만 노출

## 왜 wrapper 예외가 생기나

Spring JDBC, JPA, Hibernate는 DB 예외를 애플리케이션이 다루기 쉬운 예외 계층으로 감싸서 올린다.

그래서 같은 `23P01`도 경로에 따라 아래처럼 보일 수 있다.

- Spring JDBC면 `DataIntegrityViolationException`
- Hibernate면 `ConstraintViolationException`
- JPA 경계에서는 `PersistenceException`, `JpaSystemException`

즉 바깥 이름은 달라도, 안쪽 root `SQLException`이 같으면 분류 기준도 같게 가져가야 한다.

## `23P01`은 어디서 읽나

가장 안전한 beginner 기본형은 cause chain을 끝까지 내려가면서 첫 `SQLException`을 찾는 것이다.

```java
import java.sql.SQLException;

public final class SqlStateExtractor {

    private SqlStateExtractor() {
    }

    public static String find(Throwable throwable) {
        SQLException sql = findSqlException(throwable);
        return sql == null ? null : sql.getSQLState();
    }

    private static SQLException findSqlException(Throwable throwable) {
        Throwable current = throwable;
        while (current != null) {
            if (current instanceof SQLException sqlException) {
                return sqlException;
            }
            current = current.getCause();
        }
        return null;
    }
}
```

이 helper의 목적은 단순하다.

- Spring 예외 이름을 business 분기 기준으로 직접 쓰지 않는다
- DB root code를 읽는 공통 지점을 만든다

## 서비스 계층에서는 어떻게 번역하나

`23P01`은 보통 retryable보다 conflict에 가깝다.

그래서 서비스 계층에서는 아래처럼 제품 의미로 닫는 편이 안정적이다.

```java
String sqlState = SqlStateExtractor.find(exception);

if ("23P01".equals(sqlState)) {
    throw new BookingConflictException(
        "BOOKING_OVERLAP",
        "이미 같은 시간대에 예약이 있습니다."
    );
}
```

여기서 중요한 점:

- 분기 키는 `23P01`
- 밖으로 나가는 문장은 `이미 같은 시간대에 예약이 있습니다.`
- `ERROR: conflicting key value violates exclusion constraint ...` 같은 raw DB 메시지는 응답에 싣지 않는다

## HTTP 응답은 raw DB 메시지 대신 계약으로 낸다

API 계층에서는 보통 아래 정도면 충분하다.

| 내부 분류 | HTTP 상태 | 외부 코드 | 외부 메시지 |
|---|---|---|---|
| `23P01` | `409 Conflict` | `BOOKING_OVERLAP` | `이미 같은 시간대에 예약이 있습니다.` |
| `23505` | `409 Conflict` 또는 replay 성공 | `ALREADY_EXISTS` | `이미 같은 요청이 있습니다.` |
| `40001`, `40P01` | `503` 또는 내부 retry | `RETRYABLE` | 보통 사용자 메시지보다 내부 retry 정책이 중심 |

핵심은 SQLSTATE를 숨기는 게 아니라, **사용자 계약에 맞는 언어로 다시 표현하는 것**이다.

## 흔한 오해와 함정

- `DataIntegrityViolationException`이면 다 같은 입력 오류다
  - 아니다. 안쪽이 `23505`인지 `23P01`인지에 따라 제품 의미가 달라진다.
- `ConstraintViolationException`이면 Bean Validation 예외다
  - Hibernate 쪽 `ConstraintViolationException`은 DB constraint 위반일 수도 있다.
- raw DB 메시지를 그대로 보여 줘야 디버깅이 쉽다
  - 응답에는 숨기고, 내부 로그/관측에는 SQLSTATE와 도메인 코드를 남기는 편이 안전하다.
- `23P01`도 경쟁 상황이니 일단 retry한다
  - overlap 입력이 그대로면 같은 충돌이 반복되기 쉽다.

## 실무에서 쓰는 모습

룸예약 저장 흐름을 짧게 그리면 아래와 같다.

1. repository가 insert 또는 flush를 수행한다.
2. PostgreSQL exclusion constraint가 겹침을 감지하면 driver 안쪽에서 `23P01`이 생긴다.
3. Spring/JPA가 이를 `DataIntegrityViolationException` 같은 wrapper로 감싸 올린다.
4. 서비스 계층 helper가 안쪽 `SQLSTATE`를 읽는다.
5. `23P01`이면 `BookingConflictException`으로 바꾼다.
6. controller advice가 `409 Conflict` + `BOOKING_OVERLAP`를 내려 준다.

이 흐름이면 학습자가 흔히 겪는 두 가지 문제를 동시에 줄일 수 있다.

- wrapper 예외 이름만 보고 잘못 분류하는 문제
- PostgreSQL raw 메시지를 그대로 응답에 흘리는 문제

## 더 깊이 가려면

- `23P01` 자체를 왜 retryable보다 conflict로 닫는지 더 보려면 [PostgreSQL `23P01` Handling Note](./postgresql-23p01-handling-note.md)
- `23P01`과 `23505`를 제품 문장 기준으로 같이 비교하려면 [PostgreSQL `23P01` vs `23505` Product Language Card](./postgresql-23p01-vs-23505-product-language-card.md)
- Spring이 `SQLException`을 왜 wrapper 예외로 번역하는지부터 다시 보려면 [Spring `JdbcTemplate` and `SQLException` Translation](../spring/spring-jdbctemplate-sqlexception-translation.md)
- API 오류 계약을 `ProblemDetail`로 다듬고 싶으면 [Spring `ProblemDetail` Error Response Design](../spring/spring-problemdetail-error-response-design.md)

## 면접/시니어 질문 미리보기

> Q. `23P01`을 왜 `DataIntegrityViolationException` 이름만으로 분기하지 않나요?
> 의도: wrapper와 root cause를 분리해서 읽는지 확인
> 핵심: 같은 바깥 예외 안에 `23505`, `23P01` 등 다른 DB 신호가 숨어 있을 수 있기 때문이다.

> Q. raw DB 메시지를 응답에 그대로 주지 않는 이유는 무엇인가요?
> 의도: 외부 계약과 내부 진단 정보를 분리하는지 확인
> 핵심: 사용자 경험과 보안 측면에서 제품 문장으로 번역하고, 내부에서는 SQLSTATE를 관측하면 된다.

> Q. `23P01`과 `40001`을 서비스 정책에서 어떻게 다르게 다루나요?
> 의도: conflict와 retryable을 분리하는지 확인
> 핵심: `23P01`은 보통 overlap conflict, `40001`은 whole-transaction retry 후보다.

## 한 줄 정리

Spring/JPA에서는 `23P01`이 wrapper 예외 안에 감겨 올라오기 쉬우므로, 초보자는 바깥 예외 이름보다 안쪽 `SQLException#getSQLState()`를 읽고 `409 Conflict`용 제품 문장으로 번역하는 흐름을 먼저 고정하면 된다.
