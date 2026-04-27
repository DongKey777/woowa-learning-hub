# Lock 예외와 Unique 예외 통합 미니 브리지

> 한 줄 요약: beginner는 lock 경로와 duplicate-key 경로를 따로 외우기보다, 먼저 `already exists` / `busy` / `retryable` 3버킷으로 번역한 뒤 "승자가 이미 있나, 아직 막혀 있나, 이번 시도만 버리면 되나"를 한 장에서 비교하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)
- [Duplicate Key vs Busy Response Mapping](./duplicate-key-vs-busy-response-mapping.md)
- [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md)
- [3버킷 결정 트리 미니카드](./three-bucket-decision-tree-mini-card.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)
- [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: lock unique exception bridge, duplicate key lock timeout deadlock one page, busy retryable already exists lock duplicate, lock path duplicate path comparison, beginner exception mapping bridge, spring exception 3 bucket bridge, unique violation vs lock timeout vs deadlock, duplicate key already exists busy retryable one sheet, 락 예외 중복키 예외 비교, 락 경로 unique 경로 한 장 비교, already exists busy retryable 연결 문서, 초급자 예외 버킷 브리지, lock duplicate mini bridge, unique lock exception mental model

## 먼저 멘탈모델

용어 뜻부터 헷갈리면 [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)를 먼저 보고 오는 편이 빠르다.

이 문서에서는 그 공통 용어를 기준으로 **duplicate 경로와 lock 경로를 나란히 비교**한다.

핵심은 이거다.

> duplicate-key 경로는 보통 "이미 승자가 있다" 쪽이고, lock 경로는 "지금 막혀 있거나 이번 시도만 깨졌다" 쪽이다.

처음에는 아래 `입문` 표만 보고, "duplicate 경로와 lock 경로가 왜 다른가"가 궁금할 때 `확장` 표로 내려가면 된다.

## 입문: 3버킷 한 장 비교표

| 경로 | 대표 신호 | 먼저 넣을 버킷 | 초급자 해석 | 기본 동작 |
|---|---|---|---|---|
| unique/duplicate 경로 | `duplicate key`, unique violation | `already exists` | 같은 key 승자가 이미 있다 | 기존 row/기존 결과 재조회 |
| lock 경로 | `lock timeout` | `busy` | 지금 막혀 있어 결과를 단정 못 한다 | 즉시 무한 재시도 말고 혼잡 원인 확인 |
| lock 경로 | `deadlock` | `retryable` | 이번 시도만 희생됐다 | 전체 트랜잭션 bounded retry |
| lock/격리 경로 | `serialization failure` | `retryable` | 새 snapshot에서 다시 계산해야 한다 | 전체 트랜잭션 bounded retry |

짧은 기억법:

- `duplicate key` = 이미 자리 있음
- `lock timeout` = 아직 줄이 안 빠짐
- `deadlock` / `serialization failure` = 이번 판만 다시

## 확장: duplicate 경로와 lock 경로를 나란히 보기

| 질문 | duplicate-key 경로 | lock 경로 |
|---|---|---|
| DB가 말하는 핵심 | "승자는 이미 있다" | "아직 못 들어갔거나, 이번 시도만 깨졌다" |
| 대표 예외 | `DuplicateKeyException`, unique violation | `CannotAcquireLockException`, deadlock, `CannotSerializeTransactionException` |
| 흔한 첫 반응 | 기존 결과를 읽는다 | timeout인지 deadlock인지 먼저 가른다 |
| 초보자 실수 | 같은 `INSERT`를 계속 다시 던진다 | timeout을 무조건 retry해서 혼잡을 키운다 |
| 기본 처리 단위 | winner read / result replay | 새 트랜잭션 재시도 또는 busy 응답 |

## 작은 예시

쿠폰 발급 API에서 `(coupon_id, member_id)`가 유일하다고 하자.

| 장면 | 어느 경로인가 | 3버킷 | 기본 응답 |
|---|---|---|---|
| A가 먼저 insert commit, B는 같은 key insert에서 실패 | duplicate-key 경로 | `already exists` | "이미 발급됨" 또는 기존 결과 반환 |
| A가 row를 오래 잡아서 B가 lock timeout | lock 경로 | `busy` | "지금 혼잡" 응답 또는 짧은 제한 retry |
| A와 B가 잠금 순서를 엇갈리게 잡아 deadlock | lock 경로 | `retryable` | 전체 발급 트랜잭션 다시 시도 |

같은 "발급 실패"라도, duplicate 경로와 lock 경로는 뜻이 다르다.

- duplicate는 보통 **이미 결론이 난 실패**
- lock timeout은 **아직 결론을 못 본 실패**
- deadlock/serialization failure는 **이번 attempt만 무효인 실패**

## 자주 헷갈리는 지점

- `DuplicateKeyException`을 `retryable`로 두면 같은 key에 다시 부딪힐 가능성이 크다.
- `lock timeout`을 `already exists`처럼 읽는 공통 오해는 [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md) 5줄로 먼저 고정해 두면 덜 흔들린다.
- `CannotAcquireLockException` 하나만 보고 retry 여부를 결정하면 deadlock과 timeout이 섞여 오분류될 수 있다.
- `already exists`는 DB 상태 버킷이고, HTTP `409 conflict`는 그다음 서비스 응답 선택이다.
- HTTP까지 한 장으로 이어서 보고 싶으면 [Duplicate Key vs Busy Response Mapping](./duplicate-key-vs-busy-response-mapping.md)을 바로 붙여 읽으면 된다.

## 초보자용 실무 규칙

1. 먼저 모든 예외를 `already exists` / `busy` / `retryable` 중 하나로 번역한다.
2. duplicate-key 경로는 같은 `INSERT` 재시도보다 winner read가 먼저다.
3. lock 경로는 timeout과 deadlock을 분리한다.
4. `retryable`은 SQL 한 줄이 아니라 트랜잭션 전체를 다시 시작한다.

## 다음에 이어서 볼 문서

- 한 장 결정표를 더 짧게 보고 싶으면 [3버킷 결정 트리 미니카드](./three-bucket-decision-tree-mini-card.md)
- duplicate-key 쪽을 더 자세히 보면 [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)
- lock 예외가 Spring/JPA에서 어떻게 보이는지 보면 [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- service-layer `createIfAbsent()`에 바로 붙이려면 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
