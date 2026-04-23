# MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑

> 한 줄 요약: lock timeout과 deadlock은 DB에서는 서로 다른 신호이고, Spring에서는 `CannotAcquireLockException` 하나로 뭉개져 보일 수도 있어서 **top-level 예외 이름만 보지 말고 `SQLSTATE/errno + 번역 경로(JDBC vs Hibernate/JPA)`까지 같이 봐야** bounded retry를 안전하게 설계할 수 있다.

**난이도: 🔴 Advanced**

관련 문서:

- [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md)
- [Spring Retry Proxy Boundary Pitfalls](./spring-retry-proxy-boundary-pitfalls.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
- [Transaction Timeout과 Lock Timeout](./transaction-timeout-vs-lock-timeout.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)

retrieval-anchor-keywords: mysql 1205 spring, mysql 1213 spring, postgres 55P03 spring, postgres 40P01 spring, lock timeout exception mapping, deadlock exception mapping, cannotacquirelockexception, deadlockloserdataaccessexception, pessimisticlockexception, locktimeoutexception, hibernate lockacquisitionexception, spring jpa deadlock retry, spring lock timeout retry classification, sqlstate 55P03, sqlstate 40P01, sqlstate 40001 mysql deadlock, sqlstate 40001 postgres serialization, bounded retry lock timeout, bounded retry deadlock

## 핵심 개념

이 주제에서 가장 많이 틀리는 지점은 예외 클래스 이름만 보고 retry 정책까지 바로 정하는 것이다.

- 같은 DB 실패도 `JdbcTemplate`/MyBatis 경로와 Hibernate/JPA 경로에서 **다른 예외 이름**으로 surface된다
- 같은 Spring 예외(`CannotAcquireLockException`) 안에도 **deadlock / lock timeout / serialization failure**가 섞일 수 있다
- deadlock은 대체로 `whole transaction retry` 후보다
- lock timeout은 대체로 **blocking/saturation 신호**라서 blind retry 대상이 아니다

그래서 분류 순서는 보통 아래가 가장 덜 흔들린다.

1. `SQLException`의 `SQLSTATE`와 vendor `errorCode(errno)`를 본다
2. 예외가 JDBC translator에서 왔는지, Hibernate/JPA translator에서 왔는지 본다
3. retry가 필요하면 SQL 한 줄이 아니라 **transaction attempt 전체**를 다시 시작한다

## 먼저 DB 신호를 분리한다

| 엔진 | 현상 | DB 코드 | DB 쪽 rollback 의미 | 1차 해석 |
|---|---|---|---|---|
| MySQL | lock wait timeout | errno `1205`, SQLSTATE `HY000` | 기본값에서는 현재 statement만 rollback, `innodb_rollback_on_timeout`이면 transaction 전체 rollback | 경합이 오래 풀리지 않았다는 뜻이다. 건강한 경쟁이라기보다 blocking/saturation 신호에 가깝다 |
| MySQL | deadlock victim | errno `1213`, SQLSTATE `40001` | deadlock victim transaction 전체 rollback | retry 가능한 충돌이다. lock ordering 문제를 같이 의심한다 |
| PostgreSQL | lock timeout / `NOWAIT` lock-not-available | SQLSTATE `55P03` | statement는 실패하고, transaction block은 rollback 또는 savepoint 복구 전까지 계속 쓸 수 없다 | non-blocking probe 또는 짧은 lock budget이 실패한 것이다. timeout policy/saturation 신호로 본다 |
| PostgreSQL | deadlock detected | SQLSTATE `40P01` | current transaction aborted | retry 가능한 충돌이다. `40001`과 분리해서 본다 |

헷갈리기 쉬운 옆 케이스도 하나 있다.

- PostgreSQL `40001`은 deadlock이 아니라 **serialization failure**다
- MySQL `40001`은 흔히 `1213 deadlock`과 같이 온다

즉 `SQLSTATE = 40001`만 보고 deadlock이라고 단정하면 PostgreSQL에서는 틀린다.

## Spring JDBC / MyBatis 경로에서는 이렇게 번역된다

`JdbcTemplate`, MyBatis, plain JDBC처럼 Spring의 `SQLErrorCodeSQLExceptionTranslator`를 타는 경로는 DB 코드 기준 매핑이 비교적 직접적이다.

| DB 신호 | Spring 예외 surface | 해석 포인트 |
|---|---|---|
| MySQL `1205` | `CannotAcquireLockException` | Spring error-code map의 `cannotAcquireLockCodes`에 들어간다 |
| MySQL `1213` | `DeadlockLoserDataAccessException` | 여전히 많이 보이지만 Spring 6.0.3부터 deprecated다. 실전 분류는 `PessimisticLockingFailureException` 계열로 보는 편이 낫다 |
| PostgreSQL `55P03` | `CannotAcquireLockException` | `lock_timeout`, `NOWAIT`, lock-not-available가 이 bucket으로 들어온다 |
| PostgreSQL `40P01` | `DeadlockLoserDataAccessException` | deadlock 전용 bucket으로 들어온다 |
| PostgreSQL `40001` | `CannotSerializeTransactionException` | retry 가능하지만 deadlock이 아니라 serialization conflict다 |

이 경로의 중요한 함정은 두 가지다.

- `DeadlockLoserDataAccessException`는 deadlock을 비교적 잘 드러내지만, **Hibernate/JPA 경로로 가면 같은 deadlock이 이 이름으로 안 보일 수 있다**
- `CannotAcquireLockException` 하나만 잡으면 MySQL `1205`, PostgreSQL `55P03`, 일부 Hibernate deadlock 변환이 한 bucket에 섞인다

## Hibernate/JPA 경로에서는 surface가 한 번 더 바뀐다

Spring Data JPA / `EntityManager` 경로에서는 DB 예외가 Hibernate 예외를 거쳐 JPA 예외 또는 Spring `DataAccessException`으로 한 번 더 번역된다.

### 1. lock timeout 계열

Hibernate dialect는 보통 다음처럼 나눈다.

- MySQL `1205`, PostgreSQL `55P03` -> Hibernate `org.hibernate.PessimisticLockException`
- 명시적 timeout / `NOWAIT` signal이 더 직접 잡히면 Hibernate `org.hibernate.exception.LockTimeoutException`

그다음 JPA/Spring으로 올라오면 아래처럼 갈라진다.

| 층 | 대표 surface | 의미 |
|---|---|---|
| JPA | `jakarta.persistence.LockTimeoutException` | JPA spec 기준으로는 "pessimistic lock conflict지만 transaction rollback까지는 아니다"라는 뜻이다 |
| JPA | `jakarta.persistence.PessimisticLockException` | pessimistic locking conflict이며 현재 transaction은 rollback 대상으로 본다 |
| Spring generic JPA translation | `LockTimeoutException` -> `CannotAcquireLockException` | top-level만 보면 deadlock과 헷갈릴 수 있다 |
| Spring generic JPA translation | `PessimisticLockException` -> `PessimisticLockingFailureException` | timeout보다 더 넓은 pessimistic locking 실패 bucket이다 |
| Spring `HibernateJpaDialect` | Hibernate `PessimisticLockException` -> `PessimisticLockingFailureException` | Hibernate raw 예외를 Spring DAO 예외로 바꾼다 |

즉 **JPA에서는 `LockTimeoutException` vs `PessimisticLockException`이 중요한 구분**이고, **Spring에서는 다시 `CannotAcquireLockException` vs `PessimisticLockingFailureException`으로 보일 수 있다**.

다만 이 JPA 구분을 그대로 "같은 transaction을 계속 써도 된다"로 받아들이면 위험하다.  
특히 PostgreSQL `55P03` 계열은 JPA top-level이 `LockTimeoutException`으로 보여도 실제 DB transaction block은 이미 에러 상태일 수 있어서, Spring service code에서는 **현재 attempt를 버리고 바깥 retry envelope로 나가는 편**이 안전하다.

### 2. deadlock 계열

Hibernate dialect는 보통 deadlock을 `org.hibernate.exception.LockAcquisitionException`으로 만든다.

- MySQL deadlock: SQLSTATE `40001`, errno `1213`
- PostgreSQL deadlock: SQLSTATE `40P01`

Spring `HibernateJpaDialect`는 이 Hibernate `LockAcquisitionException`을 `CannotAcquireLockException`으로 번역한다.

그래서 JPA/Hibernate 경로에서는 아래 같은 현상이 생긴다.

- MySQL `1213 deadlock`이 JDBC 경로에서는 `DeadlockLoserDataAccessException`
- 같은 deadlock이 Hibernate/JPA 경로에서는 `CannotAcquireLockException`

즉 deadlock 여부를 top-level Spring 예외 이름만으로 판정하면 오분류가 난다.

## bounded retry는 이렇게 나누는 편이 안전하다

| bucket | 대표 코드 / 예외 | 기본 처리 | retry 단위 | 왜 이렇게 보나 |
|---|---|---|---|---|
| deadlock | MySQL `1213` / SQLSTATE `40001`, PostgreSQL `40P01`, `DeadlockLoserDataAccessException`, `CannotAcquireLockException` + root cause `1213`/`40P01` | bounded retry `예` | transaction 전체 | victim이 이미 죽었거나 transaction이 abort되었기 때문이다. 보통 2~3회 + 짧은 backoff면 충분하다 |
| lock timeout | MySQL `1205`, PostgreSQL `55P03`, `CannotAcquireLockException`, `PessimisticLockingFailureException` + root cause `1205`/`55P03` | blind retry `아니오`, conditional retry만 | retry한다면 transaction 전체 | 기다려도 lock을 못 얻었다는 뜻이라 blocker, 긴 transaction, pool starvation, timeout policy를 먼저 봐야 한다 |
| serialization failure | PostgreSQL `40001`, `CannotSerializeTransactionException` | bounded retry `예` but separate bucket | transaction 전체 | deadlock이 아니라 serializable/SSI conflict다. metrics를 deadlock과 합치지 않는다 |

실전 규칙을 더 짧게 줄이면 이렇다.

- deadlock: **retryable**
- lock timeout: **원인 분석 우선**, intentional short timeout일 때만 제한적 retry
- serialization failure: **retryable지만 deadlock과 별도 집계**

## lock timeout을 무조건 retry하면 안 되는 이유

lock timeout은 "지금 줄이 너무 길다"는 신호일 때가 많다.

대표적인 오분류:

- 긴 business transaction이 row를 오래 쥐고 있다
- 외부 API 호출이 transaction 안에 있다
- hot row / hot key에 요청이 몰린다
- pool starvation 때문에 commit이 늦어져 lock hold time이 커진다

이 상황에서 즉시 retry를 걸면:

- 같은 blocker를 다시 만난다
- 경쟁을 더 키운다
- tail latency와 pool pressure만 늘어난다

그래서 lock timeout retry는 아래 조건을 만족할 때만 제한적으로 건다.

- path가 애초에 `NOWAIT` 또는 짧은 local lock timeout으로 "대기 대신 빨리 실패"를 의도했다
- command가 idempotent하거나 중복 부작용이 없다
- retry budget이 작다: 보통 1~2회, 짧은 jitter

반대로 일반적인 OLTP request에서 우연히 `1205`/`55P03`가 보인다면 먼저 [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)으로 가는 편이 맞다.

## classifier는 top-level 예외가 아니라 root SQL 코드를 본다

아래처럼 `DataAccessException`만 보고 분기하면 deadlock과 timeout이 섞인다.

```java
catch (CannotAcquireLockException ex) {
    // 너무 거칠다. 1205, 40P01, 1213, 40001 일부가 같이 섞일 수 있다.
}
```

더 안전한 기준은 root `SQLException`을 다시 보는 것이다.

```java
public enum ConcurrencyKind {
    DEADLOCK,
    LOCK_TIMEOUT,
    SERIALIZATION_FAILURE,
    OTHER
}

public final class ConcurrencyClassifier {

    public static ConcurrencyKind classify(Throwable ex) {
        SQLException sqlException = findSqlException(ex);
        if (sqlException == null) {
            return ConcurrencyKind.OTHER;
        }

        String sqlState = sqlException.getSQLState();
        int vendorCode = sqlException.getErrorCode();

        if (vendorCode == 1213 || "40P01".equals(sqlState)) {
            return ConcurrencyKind.DEADLOCK;
        }

        if (vendorCode == 1205 || "55P03".equals(sqlState)) {
            return ConcurrencyKind.LOCK_TIMEOUT;
        }

        if ("40001".equals(sqlState) && vendorCode != 1213) {
            return ConcurrencyKind.SERIALIZATION_FAILURE;
        }

        return ConcurrencyKind.OTHER;
    }

    private static SQLException findSqlException(Throwable ex) {
        Throwable current = ex;
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

이 분류를 쓰면 다음처럼 retry envelope를 더 명시적으로 만들 수 있다.

- `DEADLOCK` -> `maxAttempts = 3`
- `SERIALIZATION_FAILURE` -> `maxAttempts = 3`
- `LOCK_TIMEOUT` -> 기본 `0`, intentional short-timeout path만 `1~2`

## retry 경계는 항상 `@Transactional` 바깥이다

이 문서의 모든 retry 분류는 같은 전제를 가진다.

- deadlock 뒤에는 같은 transaction을 이어서 쓸 수 없다
- PostgreSQL `55P03`도 transaction block이 실패 상태가 되기 쉬워서 같은 attempt를 이어서 쓰기 어렵다
- MySQL `1205`가 statement rollback만 한다고 해도, Spring/JPA persistence context까지 안전하게 복구됐다고 가정하면 안 된다

그래서 retry loop는 repository 안쪽도 아니고, 실패한 `@Transactional` 메서드 안쪽도 아니라 **facade/application service 바깥**에 둔다.

## 헷갈리지 않게 마지막으로 정리

- MySQL `1213`와 PostgreSQL `40P01`은 deadlock bucket이다
- MySQL `1205`와 PostgreSQL `55P03`은 lock-timeout bucket이다
- PostgreSQL `40001`은 deadlock이 아니라 serialization failure bucket이다
- JDBC 경로의 deadlock은 `DeadlockLoserDataAccessException`로 보일 수 있지만, Hibernate/JPA 경로에서는 같은 현상이 `CannotAcquireLockException`로 보일 수 있다
- 그래서 retry 분류는 `DataAccessException` 이름보다 `SQLSTATE/errno`를 기준으로 하는 편이 안전하다

## 꼬리질문

> Q: `CannotAcquireLockException`이면 항상 retry하면 되나요?
> 의도: top-level Spring 예외 하나로 retry 여부를 단정하지 않는지 확인
> 핵심: 아니다. `1205`, `55P03`, deadlock 변환이 함께 들어올 수 있어서 root SQL 코드를 다시 봐야 한다

> Q: 왜 deadlock은 retry하고 lock timeout은 보수적으로 보나요?
> 의도: 경쟁 충돌과 saturation 신호를 구분하는지 확인
> 핵심: deadlock은 victim을 골라 transaction을 끊는 충돌이고, lock timeout은 blocker가 오래 안 풀린다는 운영 신호인 경우가 많다

> Q: PostgreSQL `40001`과 MySQL `40001`은 같은 의미인가요?
> 의도: SQLSTATE 문자열만으로 오해하지 않는지 확인
> 핵심: 아니다. PostgreSQL에서는 serialization failure이고, MySQL에서는 deadlock(`1213`)과 같이 보이는 경우가 흔하다

## 한 줄 정리

lock timeout/deadlock retry 정책은 `CannotAcquireLockException` 같은 top-level 이름 하나로 정하지 말고, **DB 코드(`SQLSTATE/errno`)와 번역 경로를 같이 본 뒤 deadlock만 기본 retry, lock timeout은 조건부 retry**로 두는 편이 안전하다.
