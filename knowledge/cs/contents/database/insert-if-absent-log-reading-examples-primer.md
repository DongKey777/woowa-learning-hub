# Insert-if-Absent 로그 읽기 예시 프라이머

> 한 줄 요약: `insert-if-absent` 장애 로그를 보면 초보자는 "원인 분석"보다 먼저 **첫 액션**을 고정하면 덜 흔들린다. `duplicate`는 winner 확인, `timeout`은 blocker 확인, `deadlock`과 `40001`은 새 트랜잭션 재시도부터 시작한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [Spring Insert-if-Absent SQLSTATE Cheat Sheet](./spring-insert-if-absent-sqlstate-cheat-sheet.md)
- [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)
- [Timeout 에러코드 매핑 미니카드](./timeout-errorcode-mapping-mini-card.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [DB 입문 오류 신호 미니카드](./db-error-signal-beginner-result-language-mini-card.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: insert-if-absent log reading examples, duplicate timeout deadlock 40001 log primer, sqlstate log reading beginner, insert if absent first action, duplicate key timeout deadlock serialization logs, mysql 1062 1205 1213 log example, postgres 23505 55P03 40P01 40001 log example, beginner database log snippets, spring log sqlstate primer, junior log first action duplicate timeout deadlock, insert-if-absent 로그 읽기 예시, 중복 타임아웃 데드락 40001 로그, sqlstate 초급자 로그 해석, first action duplicate timeout deadlock 40001

## 먼저 잡을 멘탈모델

로그를 읽을 때 초보자가 가장 많이 하는 실수는 "`에러 이름을 이해해야만 다음 행동을 고를 수 있다`"라고 생각하는 것이다.
`insert-if-absent`에서는 반대로 가는 편이 안전하다.

| 로그에서 먼저 보인 것 | 초급자 첫 액션 | 서비스 결과 언어 |
|---|---|---|
| `duplicate key` / `23505` / `1062` | winner row를 fresh read로 확인 | `already exists` |
| `lock wait timeout` / `55P03` / `1205` | blocker, hot key, 긴 트랜잭션부터 확인 | `busy` |
| `deadlock` / `40P01` / `1213` | 트랜잭션 전체를 새로 재시도 | `retryable` |
| PostgreSQL `40001` | 새 snapshot에서 트랜잭션 전체 재시도 | `retryable` |

짧게 외우면 이렇다.

- `duplicate` -> 이미 winner가 있다
- `timeout` -> 아직 결론을 못 봤다
- `deadlock`, `40001` -> 이번 시도만 버리고 다시 간다

## 30초 로그 읽기 순서

1. 예외 클래스보다 `SQLSTATE`나 vendor code를 먼저 찾는다.
2. 같은 key winner가 이미 있는지, 아직 모르는지, 이번 attempt만 실패한 것인지 고른다.
3. 첫 액션을 바로 정한다.

아래 예시는 "로그를 보자마자 무엇을 할까?"에만 집중한다.

## 예시 1. Duplicate Key

```text
2026-04-27 10:14:03.412 WARN  --- [http-nio-8080-exec-7]
o.h.engine.jdbc.spi.SqlExceptionHelper :
SQL Error: 1062, SQLState: 23000

2026-04-27 10:14:03.413 ERROR --- [http-nio-8080-exec-7]
o.h.engine.jdbc.spi.SqlExceptionHelper :
Duplicate entry 'coupon-77:user-18' for key 'uk_coupon_issue_coupon_user'

org.springframework.dao.DuplicateKeyException:
could not execute statement
```

이 로그를 한 문장으로 번역하면:

> "같은 key의 winner가 이미 있다."

초급자 첫 액션:

- 같은 `INSERT`를 다시 던지지 말고 winner row를 fresh read한다.
- 같은 payload 재전송인지, 이미 발급된 기존 결과인지 확인한다.

바로 하면 안 되는 것:

- `DuplicateKeyException`이니까 무조건 `409`라고 단정
- blind retry로 같은 `INSERT`를 반복

## 예시 2. Lock Timeout

```text
2026-04-27 10:16:41.990 WARN  --- [http-nio-8080-exec-3]
o.h.engine.jdbc.spi.SqlExceptionHelper :
SQL Error: 1205, SQLState: HY000

2026-04-27 10:16:41.991 ERROR --- [http-nio-8080-exec-3]
o.h.engine.jdbc.spi.SqlExceptionHelper :
Lock wait timeout exceeded; try restarting transaction

org.springframework.dao.CannotAcquireLockException:
could not execute statement
```

이 로그를 한 문장으로 번역하면:

> "누가 winner인지 아직 못 본 채 기다림 예산이 끝났다."

초급자 첫 액션:

- blocker 트랜잭션, 같은 business key 반복 경합, 긴 트랜잭션부터 확인한다.
- `busy`로 번역하고, 필요하면 매우 짧은 제한 retry만 검토한다.

바로 하면 안 되는 것:

- 로그 문구에 `try restarting transaction`이 있다고 무조건 자동 retry
- `이미 누가 넣었나 보다`라고 `already exists`로 단정

메모:

- PostgreSQL에서는 비슷한 장면이 `55P03`으로 보일 수 있다.
- `CannotAcquireLockException`만 보고 deadlock인지 timeout인지 정하지 않는다.

## 예시 3. Deadlock

```text
2026-04-27 10:18:22.504 WARN  --- [http-nio-8080-exec-5]
o.h.engine.jdbc.spi.SqlExceptionHelper :
SQL Error: 1213, SQLState: 40001

2026-04-27 10:18:22.505 ERROR --- [http-nio-8080-exec-5]
o.h.engine.jdbc.spi.SqlExceptionHelper :
Deadlock found when trying to get lock; try restarting transaction

org.springframework.dao.CannotAcquireLockException:
could not execute statement
```

이 로그를 한 문장으로 번역하면:

> "이번 attempt가 deadlock 희생자가 됐다."

초급자 첫 액션:

- SQL 한 줄이 아니라 **트랜잭션 전체**를 새로 재시도한다.
- retry 횟수는 2~3회처럼 bounded하게 둔다.

바로 하면 안 되는 것:

- timeout 늘리기만 해서 해결하려고 함
- 실패한 SQL 한 줄만 다시 실행

메모:

- MySQL deadlock은 `1213`이고 `SQLSTATE 40001`로 같이 보일 수 있다.
- PostgreSQL deadlock은 보통 `40P01`이다.

## 예시 4. PostgreSQL `40001`

```text
2026-04-27 10:20:11.223 ERROR --- [http-nio-8080-exec-9]
org.postgresql.util.PSQLException:
ERROR: could not serialize access due to read/write dependencies among transactions
SQLState: 40001

org.springframework.dao.CannotSerializeTransactionException:
could not execute statement
```

이 로그를 한 문장으로 번역하면:

> "deadlock이 아니라, 방금 읽고 판단한 snapshot이 더 이상 유효하지 않다."

초급자 첫 액션:

- 새 트랜잭션, 새 snapshot에서 처음부터 다시 계산한다.
- `retryable`로 집계하되 deadlock과는 분리해서 본다.

바로 하면 안 되는 것:

- `40001`을 무조건 deadlock이라고 부름
- 읽기 결과만 재사용한 채 중간부터 이어서 실행

## 한 장 비교표

| 로그 조각 | 뜻 | 첫 액션 | 자주 하는 오해 |
|---|---|---|---|
| `1062` / `23505` / `DuplicateKeyException` | winner가 이미 있다 | winner fresh read | "같은 INSERT를 다시 넣자" |
| `1205` / `55P03` / `CannotAcquireLockException` | 아직 결론을 못 봤다 | blocker와 hot key 확인 | "이미 있나 보다" |
| `1213` / `40P01` / `deadlock` | 이번 attempt만 실패 | 트랜잭션 전체 bounded retry | "timeout만 늘리면 된다" |
| PostgreSQL `40001` / `CannotSerializeTransactionException` | snapshot 충돌 | 새 snapshot에서 전체 재시도 | "deadlock이랑 완전히 같다" |

## 초급자용 마지막 규칙

- `duplicate`를 보면 먼저 read
- `timeout`을 보면 먼저 blocker
- `deadlock`과 `40001`을 보면 먼저 whole-transaction retry

이 세 줄만 고정해도 `insert-if-absent` 로그를 읽을 때 "중복인데 왜 retry하지?", "`40001`이 왜 deadlock이 아니지?" 같은 흔한 혼동을 크게 줄일 수 있다.
