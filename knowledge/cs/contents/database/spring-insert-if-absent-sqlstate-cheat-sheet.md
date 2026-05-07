---
schema_version: 3
title: Spring Insert-if-Absent SQLSTATE Cheat Sheet
concept_id: database/spring-insert-if-absent-sqlstate-cheat-sheet
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- spring
- insert-if-absent
- sqlstate
- exception-mapping
- retry
aliases:
- Spring insert-if-absent SQLSTATE cheat sheet
- insert-if-absent exception bucket
- MySQL 1062 1205 1213 Spring
- PostgreSQL 23505 55P03 40P01 40001 Spring
- DuplicateKeyException
- CannotAcquireLockException
- DeadlockLoserDataAccessException
- CannotSerializeTransactionException
- Spring DB code to exception bucket
- SQLSTATE cheat sheet beginner
symptoms:
- insert-if-absent에서 Spring 예외 클래스 이름보다 DB code, Spring bucket, service outcome 순서로 읽어야 해
- duplicate, timeout, deadlock, serialization failure를 already exists, busy, retryable로 빠르게 매핑해야 해
- CannotAcquireLockException 안에 timeout과 deadlock이 같이 숨어 있어 root SQLSTATE/errno가 필요해
intents:
- definition
- drill
- troubleshooting
prerequisites:
- database/insert-if-absent-log-reading-examples-primer
- database/three-bucket-decision-tree
next_docs:
- database/insert-if-absent-retry-outcome-guide
- database/spring-cannotacquirelockexception-root-sql-code
- database/spring-jpa-lock-timeout-deadlock-exception-mapping
linked_paths:
- contents/database/insert-if-absent-log-reading-examples-primer.md
- contents/database/insert-if-absent-retry-outcome-guide.md
- contents/database/mysql-duplicate-key-retry-handling-cheat-sheet.md
- contents/database/timeout-errorcode-mapping-mini-card.md
- contents/database/spring-cannotacquirelockexception-root-sql-code-card.md
- contents/database/spring-jpa-lock-timeout-deadlock-exception-mapping.md
- contents/database/postgresql-serializable-retry-playbook.md
confusable_with:
- database/spring-cannotacquirelockexception-root-sql-code
- database/three-bucket-decision-tree
- database/insert-if-absent-retry-outcome-guide
forbidden_neighbors: []
expected_queries:
- Spring insert-if-absent에서 MySQL 1062 1205 1213과 PostgreSQL 23505 55P03 40P01 40001을 어떻게 매핑해?
- DuplicateKeyException은 already exists, lock timeout은 busy, deadlock serialization failure는 retryable로 보는 치트시트를 보여줘
- CannotAcquireLockException 하나만 보고 retry하지 말고 root SQLSTATE errno를 봐야 하는 이유가 뭐야?
- PostgreSQL 40001은 serialization failure로 retryable이지만 deadlock telemetry와 분리해야 하는 이유를 설명해줘
- insert-if-absent에서 duplicate key는 같은 INSERT blind retry보다 winner fresh read가 먼저인 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Spring insert-if-absent 예외를 DB code -> Spring exception bucket -> service outcome 순서로 매핑하는 beginner cheat sheet다.
  MySQL 1062/1205/1213, PostgreSQL 23505/55P03/40P01/40001, DuplicateKeyException, CannotAcquireLockException 질문이 본 문서에 매핑된다.
---
# Spring Insert-if-Absent SQLSTATE Cheat Sheet

> 한 줄 요약: `insert-if-absent`에서 초보자가 먼저 외울 것은 예외 클래스 이름이 아니라 **DB 코드 -> Spring bucket -> 서비스 결과** 순서다.

**난이도: 🟢 Beginner**

관련 문서:

- [Insert-if-Absent 로그 읽기 예시 프라이머](./insert-if-absent-log-reading-examples-primer.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)
- [Timeout 에러코드 매핑 미니카드](./timeout-errorcode-mapping-mini-card.md)
- [Spring `CannotAcquireLockException`에서 root SQL 코드 먼저 읽는 초간단 카드](./spring-cannotacquirelockexception-root-sql-code-card.md)
- [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: spring insert-if-absent sqlstate cheat sheet, spring sqlstate mysql postgresql duplicate timeout deadlock serialization, insert-if-absent exception bucket card, mysql 1062 1205 1213 spring, postgres 23505 55p03 40p01 40001 spring, duplicatekeyexception cannotacquirelockexception deadlockloser cannotserializetransactionexception, spring jdbc jpa sqlstate quick map, junior sqlstate primer, insert-if-absent retry bucket map, spring db code to exception bucket, sqlstate cheat sheet beginner, spring 예외 버킷 치트시트, insert-if-absent sqlstate 정리, mysql postgres sqlstate spring 매핑, spring insert if absent sqlstate cheat sheet basics

## 먼저 멘탈모델

`insert-if-absent`에서는 실패를 4개 이름으로 보기보다 아래 3단계로 읽으면 덜 헷갈린다.

1. DB 코드가 무엇인가
2. Spring에서 어느 예외 bucket으로 보이는가
3. 서비스에서는 `already exists` / `busy` / `retryable` 중 무엇으로 닫는가

짧게 외우면:

- duplicate -> `already exists`
- timeout -> `busy`
- deadlock / serialization -> `retryable`

## 한 장 치트시트

| 장면 | MySQL 코드 | PostgreSQL 코드 | Spring에서 흔한 bucket | 서비스 결과 | 기본 대응 |
|---|---|---|---|---|---|
| 중복 insert, winner가 이미 있음 | errno `1062`, SQLSTATE `23000` | SQLSTATE `23505` | `DuplicateKeyException` 또는 `DataIntegrityViolationException` | `already exists` | 같은 `INSERT` 재시도보다 winner fresh read |
| lock wait timeout, lock-not-available | errno `1205`, SQLSTATE `HY000` | SQLSTATE `55P03` | 보통 `CannotAcquireLockException` | `busy` | blocker, hot key, 긴 트랜잭션 확인 |
| deadlock victim | errno `1213`, SQLSTATE `40001` | SQLSTATE `40P01` | JDBC면 `DeadlockLoserDataAccessException`, JPA/Hibernate면 `CannotAcquireLockException` 또는 `PessimisticLockingFailureException` | `retryable` | 새 트랜잭션으로 bounded retry |
| serialization failure | 드물고 별도 beginner 기본축에서는 보통 다루지 않음 | SQLSTATE `40001` | `CannotSerializeTransactionException` 또는 `PessimisticLockingFailureException` | `retryable` | 새 트랜잭션으로 bounded retry |

초보자용 핵심 메모:

- PostgreSQL `40001`은 deadlock이 아니라 serialization failure다.
- MySQL `40001`은 insert-if-absent 문맥에서 보통 deadlock(`1213`) 쪽과 같이 읽는다.
- `CannotAcquireLockException` 하나만 보고 timeout인지 deadlock인지 정하지 않는다.

## 예외 이름을 읽는 가장 안전한 순서

| 먼저 보이는 것 | 바로 결론 내리면 안 되는 이유 | 다음 확인 |
|---|---|---|
| `DuplicateKeyException` | 같은 key 재전송인지, 다른 payload 충돌인지는 아직 모른다 | winner row fresh read |
| `CannotAcquireLockException` | timeout과 deadlock이 같이 숨어 있을 수 있다 | root `SQLSTATE/errno` |
| `PessimisticLockingFailureException` | JPA/Hibernate 번역 경로에 따라 deadlock/lock conflict가 섞일 수 있다 | root `SQLSTATE/errno` |
| `CannotSerializeTransactionException` | retryable인 것은 맞지만 deadlock으로 집계하면 안 된다 | `40001`인지 확인 후 별도 집계 |

## insert-if-absent에서 자주 쓰는 최소 대응표

| root code | 먼저 붙일 라벨 | retry 기준 |
|---|---|---|
| MySQL `1062`, PostgreSQL `23505` | `already exists` | 같은 `INSERT` blind retry는 보통 하지 않음 |
| MySQL `1205`, PostgreSQL `55P03` | `busy` | 기본은 원인 확인 우선, intentional short-timeout path만 제한적 retry |
| MySQL `1213`, PostgreSQL `40P01` | `retryable` | transaction 전체 2~3회 bounded retry |
| PostgreSQL `40001` | `retryable` | transaction 전체 2~3회 bounded retry, deadlock과 분리 집계 |

## 10초 판별 예시

| 로그 조각 | 초보자 해석 |
|---|---|
| `DuplicateKeyException` + `1062` | 이미 승자가 있다. `already exists` 쪽이다 |
| `CannotAcquireLockException` + `1205` | 아직 줄이 안 풀린 `busy`다 |
| `CannotAcquireLockException` + `40P01` | 이름은 같아도 실제로는 deadlock이라 `retryable`이다 |
| `CannotSerializeTransactionException` + `40001` | serialization failure라 `retryable`이지만 deadlock은 아니다 |

## 자주 하는 오해

- `CannotAcquireLockException` = 무조건 retry -> 아니다. `1205`/`55P03`면 보통 `busy`다.
- `DuplicateKeyException` = 바로 `409 conflict` -> 아니다. 같은 payload 재전송이면 replay일 수도 있다.
- PostgreSQL `40001` = deadlock -> 아니다. `40P01`이 deadlock이다.
- deadlock과 serialization failure는 다른 이름이니 retry 정책도 달라야 한다 -> 보통 둘 다 whole-transaction bounded retry지만 telemetry는 분리하는 편이 낫다.

## 한 줄 정리

초보자는 Spring 예외 이름을 외우기보다 `1062/23505 -> already exists`, `1205/55P03 -> busy`, `1213/40P01/40001 -> retryable` 순서로 먼저 고정하면 `insert-if-absent` 분류가 빨라진다.
