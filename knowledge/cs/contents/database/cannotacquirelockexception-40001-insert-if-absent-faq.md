# `CannotAcquireLockException` / `40001` 혼동 FAQ

> 한 줄 요약: `CannotAcquireLockException`은 "락 문제처럼 보인다"는 Spring 표면 이름일 뿐이고, PostgreSQL `40001`은 deadlock이 아니라 serialization failure라서 `insert-if-absent`에서는 **예외 이름보다 DB 신호를 먼저 `busy` / `retryable`로 번역**해야 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `CannotAcquireLockException`에서 root SQL 코드 먼저 읽는 초간단 카드](./spring-cannotacquirelockexception-root-sql-code-card.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [Spring Service Layer Transaction Boundary Patterns](../spring/spring-service-layer-transaction-boundary-patterns.md)
- [Lock 예외와 Unique 예외 통합 미니 브리지](./lock-duplicate-three-bucket-mini-bridge.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: cannotacquirelockexception 40001 faq, cannotacquirelockexception postgres 40001 difference, insert-if-absent faq, cannotacquirelockexception retryable or busy, 40001 deadlock or serialization failure, beginner lock exception faq, spring exception sqlstate faq, insert-if-absent cannotacquirelockexception guide, sqlstate 40001 beginner, postgresql 40001 retryable faq, cannotacquirelockexception timeout deadlock difference, busy vs retryable faq, 왜 40001이 deadlock 아니에요, 처음 sqlstate 뭐예요

## 먼저 멘탈모델

초보자는 예외 이름을 길게 외우기 전에 아래 두 줄만 먼저 잡으면 된다.

- `CannotAcquireLockException` = "Spring이 락 계열 충돌로 번역한 바깥 이름"
- `40001` = "PostgreSQL에서 이번 판단을 직렬화할 수 없어서 새 트랜잭션으로 다시 시작하라는 신호"

즉 둘은 같은 레벨의 이름이 아니다.

- `CannotAcquireLockException`은 **Spring 예외 이름**
- `40001`은 **DB SQLSTATE**

그래서 `CannotAcquireLockException == 40001`처럼 1:1로 외우면 자주 틀린다.

## 이런 검색어로 들어오면 먼저 이름보다 코드를 본다

아래처럼 검색하고 있다면 이 문서의 출발점은 항상 같다.

- "`CannotAcquireLockException`인데 deadlock인가요?"
- "`40001`이면 이미 누가 이긴 건가요?"
- "Spring 예외 이름만 보고 retry 걸어도 되나요?"

세 질문 모두 첫 답은 "`예외 이름`이 아니라 root `SQLSTATE/errno`부터 본다"다.

처음 이 오류를 보면 이름이 길어서 겁먹기 쉬운데, 초보자 메모는 "`바깥 이름`과 `안쪽 DB 코드`를 분리해서 본다" 한 줄이면 충분하다.

## 30초 비교표

| 지금 보이는 것 | 실제로 먼저 확인할 것 | beginner 번역 | 기본 동작 |
|---|---|---|---|
| `CannotAcquireLockException` | root `SQLSTATE/errno` | 아직 timeout인지 deadlock인지 모른다 | 바로 무한 retry하지 말고 원인 분류 |
| PostgreSQL `40001` | serialization failure | 이번 시도를 버리고 새 트랜잭션으로 다시 | whole-transaction bounded retry |
| PostgreSQL `40P01` | deadlock detected | 이번 시도가 희생됐다 | whole-transaction bounded retry |
| PostgreSQL `55P03` / MySQL `1205` | lock timeout / lock not available | 아직 결론을 못 본 busy 상태 | 기본은 busy, 필요 시 짧은 제한 retry |

핵심은 이것이다.

- `40001`은 deadlock 이름이 아니다
- `CannotAcquireLockException`은 안에 timeout/deadlock이 섞일 수 있다
- `insert-if-absent`에서는 둘 다 바로 "재시도"로 뭉개지 말고 `busy` vs `retryable`을 나눠야 한다

## FAQ

### Q1. `CannotAcquireLockException`이 떴으면 무조건 retryable인가요?

아니다. `CannotAcquireLockException`은 표면 이름이라서 안쪽에 무엇이 들어 있는지 다시 봐야 한다.

- root code가 PostgreSQL `55P03` 또는 MySQL `1205`면 보통 `busy`
- root code가 PostgreSQL `40P01` 또는 MySQL `1213`면 `retryable`
- JPA/Hibernate 경로에서는 deadlock도 `CannotAcquireLockException`으로 보일 수 있다

한 줄로 줄이면 `CannotAcquireLockException`은 **답이 아니라 질문**이다.
"안쪽 SQLSTATE가 무엇이냐"를 다시 물어야 한다.

### Q2. PostgreSQL `40001`은 deadlock 아닌가요?

아니다. PostgreSQL에서 deadlock은 `40P01`이고, `40001`은 serialization failure다.

초보자 해석으로는 이렇게 나누면 충분하다.

| 코드 | 뜻 | 왜 다시 하나 |
|---|---|---|
| `40P01` | deadlock | 잠금 순환 대기에서 희생자가 뽑혔다 |
| `40001` | serialization failure | 읽고 판단한 결과를 현재 동시 실행 집합과 함께 직렬화할 수 없다 |

둘 다 `retryable`일 수는 있지만, **왜 실패했는지**는 다르다.
그래서 telemetry나 FAQ에서도 deadlock과 `40001`을 같은 문장으로 설명하면 검색 진입이 흔들린다.

### Q3. `insert-if-absent`에서 `40001`도 그냥 "이미 있음"으로 보면 안 되나요?

안 된다. `duplicate key`와 `40001`은 말하는 문장이 다르다.

| 신호 | 서비스 결과 | 초급자 해석 |
|---|---|---|
| `duplicate key` | `already exists` | 이미 승자가 확정됐다 |
| `40001` | `retryable` | 이번 판단을 새 snapshot에서 다시 해야 한다 |
| lock timeout | `busy` | 아직 승패를 확정하지 못했다 |

`insert-if-absent`에서는 이 3문장을 분리해야 한다.

- `already exists`: 기존 결과 재조회
- `busy`: 지금은 혼잡하다고 응답하거나 짧게 제한 retry
- `retryable`: 새 트랜잭션으로 전체 시도 다시 시작

## 재시도 단위

초보자는 먼저 "DB가 방금 문제 삼은 범위가 어디인가?"만 잡으면 된다.

- `duplicate key`: 보통 `INSERT` 한 줄 결과만 다시 해석하면 된다
- `40001`: 그 `INSERT` 앞에서 했던 읽기와 판단까지 포함한 **한 번의 시도 전체**가 무효다
- `deadlock`: 내가 잡은 락 순서가 이번 시도에서 꼬였으니, 역시 **이번 트랜잭션 전체**를 버려야 한다

가장 작은 예시를 보자.

1. 트랜잭션이 "`오늘 남은 좌석이 있나?`"를 읽는다.
2. 있으면 `INSERT reservation ...`를 하기로 판단한다.
3. 동시에 다른 트랜잭션도 같은 판단을 한다.
4. DB는 둘을 함께 놓고 보니 이 판단 조합을 직렬화할 수 없어서 `40001`을 돌려준다.

여기서 `INSERT` 한 줄만 다시 던지면 문제가 두 가지다.

| 무엇을 재시도하나 | 왜 초보자 기준으로 위험한가 |
|---|---|
| 실패한 SQL 1줄만 다시 실행 | "좌석이 남아 있다"는 이전 판단을 그대로 들고 간다 |
| 트랜잭션 전체를 새로 시작 | 다시 읽고, 다시 판단하고, 다시 쓰므로 새 snapshot 기준으로 맞는 결론을 낸다 |

즉 `40001`은 "이 SQL 문법이 틀렸다"가 아니라, **이 읽기-판단-쓰기 묶음이 이번 snapshot에서는 성립하지 않는다**는 신호다.

그래서 "`실패한 INSERT 한 줄만 다시 치면 되나요?`"라는 질문이 나오면, 초보자 기본 답은 "아니오, 판단에 쓰인 읽기부터 새로 시작"이다.

deadlock도 초보자 해석은 비슷하다.

- deadlock victim이 되면 현재 트랜잭션은 이미 중단됐다
- 일부 SQL만 이어서 실행하는 게 아니라, 새 트랜잭션에서 락을 다시 잡아야 한다
- 그래서 `40P01`/`1213`도 보통 SQL 한 줄 retry가 아니라 whole-transaction retry로 묶는다

짧게 외우면:

- `duplicate key` -> winner read
- `40001` / deadlock -> transaction retry
- timeout -> busy 분리

## FAQ (계속)

### Q5. 검색할 때 어떤 문서로 바로 들어가면 좋나요?

- "`createIfAbsent()`에서 이 예외를 서비스 결과로 어떻게 번역하지?" -> [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- "`CannotAcquireLockException` 안에 timeout/deadlock이 왜 섞이지?" -> [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- "PostgreSQL `40001` whole-transaction retry를 더 자세히 보고 싶다" -> [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)

## 가장 짧은 실무 규칙

1. `CannotAcquireLockException`을 보면 예외 이름에서 멈추지 말고 root `SQLSTATE/errno`를 본다.
2. PostgreSQL `40001`은 deadlock이 아니라 serialization failure로 분리한다.
3. `insert-if-absent`에서는 `duplicate key`=`already exists`, timeout=`busy`, `40001`/deadlock=`retryable`로 먼저 번역한다.
4. `retryable`은 SQL 한 줄이 아니라 새 트랜잭션 attempt로 다시 시작한다.

Spring 트랜잭션 경계에서 retry를 어디에 걸어야 하는지 바로 이어서 보고 싶다면 [Spring Service Layer Transaction Boundary Patterns](../spring/spring-service-layer-transaction-boundary-patterns.md)로 넘어가면 된다.

## 바로 이어서 읽기

- service-layer 코드 스니펫까지 바로 보려면 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- Spring/JPA 예외 surface 차이를 더 자세히 보려면 [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- PostgreSQL SSI와 `40001` 배경을 보려면 [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)

## 한 줄 정리

`CannotAcquireLockException`은 "락 문제처럼 보인다"는 Spring 표면 이름일 뿐이고, PostgreSQL `40001`은 deadlock이 아니라 serialization failure라서 `insert-if-absent`에서는 **예외 이름보다 DB 신호를 먼저 `busy` / `retryable`로 번역**해야 덜 헷갈린다.
