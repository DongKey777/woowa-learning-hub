# Spring `CannotAcquireLockException`에서 root SQL 코드 먼저 읽는 초간단 카드

> 한 줄 요약: `CannotAcquireLockException`은 "락 계열로 번역됐다"는 바깥 이름일 뿐이라서, deadlock인지 timeout인지 판단하려면 **예외 이름에서 멈추지 말고 root `SQLSTATE/errno`를 먼저 확인**해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [3버킷 결정 트리 미니카드](./three-bucket-decision-tree-mini-card.md)
- [Timeout 에러코드 매핑 미니카드](./timeout-errorcode-mapping-mini-card.md)
- [`CannotAcquireLockException` / `40001` 혼동 FAQ](./cannotacquirelockexception-40001-insert-if-absent-faq.md)
- [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- [Spring Service Layer Transaction Boundary Patterns](../spring/spring-service-layer-transaction-boundary-patterns.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring cannotacquirelockexception root sql code card, cannotacquirelockexception sqlstate errno quick card, spring lock exception root cause order, cannotacquirelockexception deadlock timeout difference, root sqlstate before retry, spring exception root sql code beginner, cannotacquirelockexception 40p01 55p03 40001 1205 1213, spring 락 예외 root sql 코드, cannotacquirelockexception 먼저 볼 것, sqlstate errno 확인 순서, deadlock timeout 오해 방지 카드, spring 예외명 sqlstate errno 카드, findsql throwable helper, cannotacquirelockexception basics, 처음 배우는데 cannotacquirelockexception 뭐예요

## 먼저 멘탈모델

초보자는 아래 한 줄만 먼저 고정하면 된다.

> `CannotAcquireLockException`은 봉투 이름이고, root `SQLSTATE/errno`가 실제 사고 코드다.

즉 바깥 봉투에 `CannotAcquireLockException`이라고 적혀 있어도 안쪽 사고 코드는 다를 수 있다.

- `55P03` / `1205`면 보통 lock timeout 쪽이다
- `40P01` / `1213`면 deadlock 쪽이다
- PostgreSQL `40001`이면 deadlock이 아니라 serialization failure다

## 엔진별 deadlock 코드 10초 비교

프레임워크 예외 이름으로 내려가기 전에, 먼저 "어느 DB에서 나온 deadlock 코드인가"만 분리해도 절반은 끝난다.

| 엔진 | deadlock 코드 | 같이 헷갈리는 코드 | beginner 기억법 |
|---|---|---|---|
| MySQL | errno `1213`, SQLSTATE `40001` | errno `1205` | MySQL에서 `1213`이면 deadlock victim이다 |
| PostgreSQL | SQLSTATE `40P01` | SQLSTATE `40001`, `55P03` | PostgreSQL에서 deadlock은 `40P01` 하나로 먼저 기억한다 |

공통 오해 한 줄:

- PostgreSQL `40001`은 deadlock이 아니라 serialization failure다.
- MySQL `1213`과 PostgreSQL `40P01`은 둘 다 deadlock이지만 코드 모양이 다르다.

## 10초 확인 순서

1. Spring 예외 이름이 `CannotAcquireLockException`인지 본다.
2. 바로 retry 여부를 결정하지 말고 root `SQLException`의 `SQLSTATE/errno`를 본다.
3. 아래 3칸 중 어디인지 넣는다.

| root code | 먼저 읽을 뜻 | beginner 분류 | 첫 대응 |
|---|---|---|---|
| PostgreSQL `55P03`, MySQL `1205` | lock timeout / lock not available | `busy` | blocker, 긴 트랜잭션, hot key를 먼저 본다 |
| PostgreSQL `40P01`, MySQL `1213` | deadlock victim | `retryable` | 새 트랜잭션으로 전체 bounded retry |
| PostgreSQL `40001` | serialization failure | `retryable` | deadlock과 분리 집계하고 전체 bounded retry |

핵심은 `CannotAcquireLockException` 하나만으로는 첫 줄과 둘째 줄을 구분할 수 없다는 점이다.

## root code는 여기서 읽는다

실무에서는 `CannotAcquireLockException`에서 바로 판단하지 말고, cause chain 안의 첫 `SQLException`을 찾아 `SQLSTATE`와 vendor `errorCode`를 읽으면 된다.

```java
import java.sql.SQLException;
import org.springframework.dao.CannotAcquireLockException;

void logRootCode(CannotAcquireLockException ex) {
    SQLException sql = findSql(ex);
    if (sql == null) {
        return;
    }

    String sqlState = sql.getSQLState();
    int errorCode = sql.getErrorCode();

    System.out.printf("sqlState=%s, errorCode=%d%n", sqlState, errorCode);
}

private SQLException findSql(Throwable t) {
    while (t != null) {
        if (t instanceof SQLException sql) {
            return sql;
        }
        t = t.getCause();
    }
    return null;
}
```

짧게 읽는 법:

- `sqlState = 40P01` -> PostgreSQL deadlock, `retryable`
- `sqlState = 55P03` -> PostgreSQL lock timeout/lock not available, `busy`
- `errorCode = 1213` -> MySQL deadlock, `retryable`
- `errorCode = 1205` -> MySQL lock wait timeout, `busy`

즉 "root code를 어디서 읽지?"라는 질문의 답은 `CannotAcquireLockException` 객체 자체가 아니라 **내부 `SQLException`의 `getSQLState()` / `getErrorCode()`**다.

## 가장 짧은 예시

| 로그 조각 | 실제 해석 | 바로 하면 안 되는 것 |
|---|---|---|
| `CannotAcquireLockException` + root `55P03` | 지금 lock을 못 얻은 `busy` | deadlock이라고 단정하고 무한 retry |
| `CannotAcquireLockException` + root `40P01` | deadlock victim | lock timeout이라고 보고 blocker만 찾기 |
| `CannotAcquireLockException` + root `40001` | serialization failure | deadlock 코드로 묶어 telemetry를 섞기 |

코드로 붙여 보면 아래처럼 읽는다.

| 코드에서 읽은 값 | 해석 | 서비스 쪽 첫 문장 |
|---|---|---|
| `findSql(ex).getSQLState()` -> `40P01` | PostgreSQL deadlock | "이번 트랜잭션은 다시 시도 가능" |
| `findSql(ex).getSQLState()` -> `55P03` | PostgreSQL lock 대기 실패 | "지금은 막혀 있음" |
| `findSql(ex).getErrorCode()` -> `1213` | MySQL deadlock | "이번 트랜잭션은 다시 시도 가능" |
| `findSql(ex).getErrorCode()` -> `1205` | MySQL lock wait timeout | "지금은 막혀 있음" |

## 자주 하는 오해

- `CannotAcquireLockException` = deadlock -> 아니다. timeout도 이 이름으로 보일 수 있다.
- `CannotAcquireLockException` = 무조건 retry -> 아니다. `55P03`/`1205`면 보통 `busy`다.
- MySQL `1213`과 PostgreSQL `40P01`을 같은 숫자 코드로 찾으려 함 -> 엔진마다 deadlock 코드를 따로 기억해야 한다.
- PostgreSQL `40001` = deadlock -> 아니다. deadlock은 `40P01`이다.

## 한 줄 정리

`CannotAcquireLockException`을 보면 "retry할까?"보다 먼저 "root `SQLSTATE/errno`가 무엇인가?"를 확인한다.
