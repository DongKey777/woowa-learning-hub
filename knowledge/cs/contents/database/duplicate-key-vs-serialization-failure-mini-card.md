# Duplicate Key vs Serialization Failure 미니 카드

> 한 줄 요약: `duplicate key` loser는 보통 "이미 winner가 있다" 쪽이고, `serialization failure` loser는 "이번 시도 전체를 버리고 처음부터 다시 하라" 쪽이다.

**난이도: 🟢 Beginner**

관련 문서:

- [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [Spring Insert-if-Absent SQLSTATE Cheat Sheet](./spring-insert-if-absent-sqlstate-cheat-sheet.md)
- [Duplicate Key vs Busy Response Mapping](./duplicate-key-vs-busy-response-mapping.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: duplicate key vs serialization failure mini card, duplicate key already exists vs serialization failure retry, mysql 1062 vs postgres 40001 beginner, duplicate loser means winner exists, serialization loser means retry whole transaction, duplicate key fresh read vs serializable retry, postgresql serializable whole transaction retry, exact key duplicate not blind retry, duplicate key conflict replay processing, sqlstate 23505 vs 40001 beginner, insert if absent duplicate vs serialization failure, 중복키 직렬화 실패 차이, duplicate key 재조회 serialization failure 전체 재시도, 1062 40001 비교 카드, loser signal already exists vs retry

## 먼저 멘탈모델

초보자는 두 신호를 아래처럼 완전히 다른 질문으로 읽으면 된다.

- `duplicate key`: "누가 먼저 자리를 차지했나?"는 이미 끝났다.
- `serialization failure`: "이번 경쟁 결과를 이 snapshot으로는 확정할 수 있나?"가 깨졌다.

짧게 외우면:

- `duplicate key` = **winner row를 읽어 의미를 분류**
- `serialization failure` = **트랜잭션 시도 전체를 새로 시작**

## 30초 비교표

| 항목 | `duplicate key` | `serialization failure` |
|---|---|---|
| 대표 코드 | MySQL `1062`, PostgreSQL `23505` | PostgreSQL `40001` |
| loser가 뜻하는 것 | 이미 같은 key winner가 있다 | 이번 시도는 직렬화할 수 없어 abort됐다 |
| 먼저 할 질문 | "그 winner는 내 요청과 같은가?" | "새 트랜잭션으로 처음부터 다시 해도 안전한가?" |
| 기본 동작 | fresh read로 winner 확인 | whole-transaction bounded retry |
| retry 단위 | 보통 `INSERT` 재시도 아님 | SQL 한 줄이 아니라 트랜잭션 전체 |
| 초보자 기억법 | 이미 자리가 찼다 | 이번 판만 다시 시작 |

## 가장 작은 예시

### 1. `duplicate key`

결제 API가 `idempotency_key=pay-7`로 row를 만들려고 한다.

- 요청 A가 먼저 `INSERT` 성공
- 요청 B가 같은 key로 들어와 `1062` 또는 `23505`

이때 loser B가 먼저 할 일은 "`INSERT`를 한 번 더"가 아니다.

1. primary/fresh read로 winner row를 읽는다.
2. same payload면 이전 성공 replay
3. same key + different payload면 `409 conflict`
4. 아직 `PROCESSING`이면 `in-progress`로 응답

즉 `duplicate key`는 보통 **already-exists 계열 해석**에서 끝난다.

### 2. `serialization failure`

PostgreSQL `SERIALIZABLE`에서 두 요청이 같은 집합 규칙을 읽고 동시에 수정한다고 하자.

- 요청 A와 B가 둘 다 "지금 예약 가능"이라고 읽음
- 둘 다 write 시도
- commit 근처에서 PostgreSQL이 한쪽에 `40001` 반환

이때 loser가 먼저 할 일은 "winner row 하나 읽고 끝"이 아니다.

1. 현재 트랜잭션 시도를 버린다.
2. 새 트랜잭션을 연다.
3. read -> validate -> write 전체를 다시 수행한다.

즉 `40001`은 보통 **retryable 계열 해석**이다.

## 왜 둘을 같은 retry로 보면 안 되나

| 잘못 섞은 해석 | 왜 문제인가 | 올바른 기본값 |
|---|---|---|
| `duplicate key`도 그냥 3회 retry | 이미 있는 winner만 반복해서 만날 수 있다 | winner read 후 replay/conflict/in-progress 분류 |
| `40001`도 기존 row 한 번 읽고 끝 | 집합 판단 전체가 이미 깨졌을 수 있다 | 새 transaction에서 처음부터 재계산 |
| 둘 다 `409`로 바로 응답 | same-payload replay와 transient retry가 섞인다 | 서비스 라벨을 먼저 나눈다 |

## 서비스에서 이렇게 기억

| 신호 | 먼저 붙일 서비스 라벨 | 보통의 후속 동작 |
|---|---|---|
| MySQL `1062`, PostgreSQL `23505` | `already exists` | winner fresh read 후 replay / conflict / processing 분기 |
| PostgreSQL `40001` | `retryable` | 서버 내부 whole-transaction retry 2~3회 |

핵심은 "`loser`가 졌다는 사실"보다 **왜 졌는지**다.

- `duplicate key` loser: 이미 선점된 key에 늦게 도착했다.
- `40001` loser: 지금 읽고 계산한 전체 시나리오가 직렬 실행처럼 설명되지 않았다.

## 자주 하는 오해

- "`duplicate key`도 동시성 실패니까 whole-transaction retry"
  - 보통 아니다. 같은 key winner가 이미 있으니 먼저 existing state를 읽는다.
- "`40001`도 결국 누가 먼저 넣었는지 보면 된다"
  - 아니다. row 한 개가 아니라 read-set / write-set 전체 관계가 깨진 것일 수 있다.
- "`23505`와 `40001`은 둘 다 PostgreSQL에서 나올 수 있으니 같은 정책"
  - 아니다. `23505`는 duplicate/constraint 축, `40001`은 serializable retry 축이다.

## 한 줄 규칙

1. `duplicate key`를 보면 "이미 있는 결과를 어떻게 해석할까?"를 먼저 묻는다.
2. `serialization failure`를 보면 "이 시도를 통째로 다시 시작할 수 있게 감쌌나?"를 먼저 묻는다.
3. 초보자 기본값은 `duplicate key -> fresh read`, `40001 -> whole transaction retry`다.

## 한 줄 정리

`duplicate key` loser는 보통 "이미 winner가 있다" 쪽이고, `serialization failure` loser는 "이번 시도 전체를 버리고 처음부터 다시 하라" 쪽이다.
