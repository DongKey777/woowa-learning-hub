---
schema_version: 3
title: PostgreSQL SERIALIZABLE Retry Playbook for Beginners
concept_id: database/postgresql-serializable-retry-playbook
canonical: true
category: database
difficulty: beginner
doc_role: playbook
level: beginner
language: mixed
source_priority: 92
mission_ids: []
review_feedback_tags:
- postgresql
- serializable
- retry-envelope
- sqlstate-40001
aliases:
- postgresql serializable retry playbook
- postgres serializable beginner
- SQLSTATE 40001 handling
- serialization failure retry whole transaction
- could not serialize access retry
- serializable retry envelope
- no retry inside same transaction
- postgresql 40001 뭐예요
- transaction retry beginner
- SSI retry
symptoms:
- PostgreSQL SERIALIZABLE을 모든 row를 먼저 lock하는 모드로 오해하고 SQL 한 줄만 retry하려 해
- SQLSTATE 40001이 나면 failed transaction attempt 전체를 버리고 새 transaction으로 다시 시작해야 하는데 같은 transaction 안에서 재시도하고 있어
- duplicate key, exclusion violation, deadlock, lock timeout을 모두 40001과 같은 blanket retry bucket에 넣으려 해
intents:
- troubleshooting
- definition
prerequisites:
- database/duplicate-key-vs-serialization-failure-mini-card
- database/postgresql-vs-mysql-isolation-cheat-sheet
next_docs:
- database/idempotent-transaction-retry-envelopes
- database/serializable-retry-telemetry-set-invariants
- database/guard-row-vs-serializable-vs-reconciliation-set-invariants
linked_paths:
- contents/database/duplicate-key-vs-serialization-failure-mini-card.md
- contents/database/postgresql-vs-mysql-isolation-cheat-sheet.md
- contents/database/cannotacquirelockexception-40001-insert-if-absent-faq.md
- contents/database/transaction-retry-serialization-failure-patterns.md
- contents/database/idempotent-transaction-retry-envelopes.md
- contents/database/spring-jpa-locking-example-guide.md
- contents/database/transaction-boundary-isolation-locking-decision-framework.md
- contents/database/guard-row-vs-serializable-vs-reconciliation-set-invariants.md
- contents/database/serializable-retry-telemetry-set-invariants.md
- contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md
- contents/database/transaction-boundary-external-io-checklist-card.md
- contents/database/insert-if-absent-retry-outcome-guide.md
- contents/database/mysql-duplicate-key-retry-handling-cheat-sheet.md
confusable_with:
- database/duplicate-key-vs-serialization-failure-mini-card
- database/cannotacquirelockexception-40001-insert-if-absent-faq
- database/postgresql-23p01-handling-note
forbidden_neighbors: []
expected_queries:
- PostgreSQL SERIALIZABLE에서 SQLSTATE 40001이 나면 왜 SQL 한 줄이 아니라 transaction attempt 전체를 retry해야 해?
- Serializable Snapshot Isolation은 모든 row를 먼저 lock하는 방식인지 SSI abort 방식인지 설명해줘
- duplicate key 23505와 serialization failure 40001을 retry 정책에서 어떻게 다르게 처리해?
- Spring @Transactional 바깥 facade에 serializable retry envelope를 둬야 하는 이유가 뭐야?
- 외부 API 호출이나 outbox publish를 serializable retry loop 안에 두면 왜 위험해?
contextual_chunk_prefix: |
  이 문서는 PostgreSQL SERIALIZABLE, SSI, SQLSTATE 40001 serialization failure를 whole-transaction retry envelope로 처리하는 beginner playbook이다.
  PostgreSQL 40001 뭐예요, serializable retry envelope, no retry inside same transaction 질문이 본 문서에 매핑된다.
---
# PostgreSQL SERIALIZABLE Retry Playbook for Beginners

> 한 줄 요약: PostgreSQL `SERIALIZABLE`은 "모든 걸 먼저 잠그는 모드"가 아니라 SSI로 위험한 동시성 패턴을 `SQLSTATE 40001`로 끊어 내는 모드라서, 서비스 계층은 실패한 SQL 한 줄이 아니라 **트랜잭션 시도 전체**를 새로 시작하는 retry envelope를 가져야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Duplicate Key vs Serialization Failure 미니 카드](./duplicate-key-vs-serialization-failure-mini-card.md)
- [PostgreSQL vs MySQL Isolation Cheat Sheet](./postgresql-vs-mysql-isolation-cheat-sheet.md)
- [`CannotAcquireLockException` / `40001` 혼동 FAQ](./cannotacquirelockexception-40001-insert-if-absent-faq.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
- [Idempotent Transaction Retry Envelopes](./idempotent-transaction-retry-envelopes.md)
- [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md)
- [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)
- [Guard Row vs Serializable Retry vs Reconciliation for Set Invariants](./guard-row-vs-serializable-vs-reconciliation-set-invariants.md)
- [Serializable Retry Telemetry for Set Invariants](./serializable-retry-telemetry-set-invariants.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)

retrieval-anchor-keywords: postgresql serializable retry playbook, postgres serializable beginner, sqlstate 40001 handling, serialization failure retry whole transaction, duplicate key vs serialization failure, already exists vs serialization failure, same insert retried, could not serialize access retry, no retry inside same transaction, serializable retry envelope, postgres 40p01 vs 40001, 23505 vs 40001 beginner comparison, postgresql 40001 뭐예요, serializable retry basics, transaction retry beginner

## Beginner 연결표 (경계 -> 재시도 -> 중복 방지)

트랜잭션 경계를 점검한 뒤 `SERIALIZABLE` retry를 보고 있다면, 아래 표로 옆 카드까지 바로 이어서 보면 된다.

| 지금 질문 | 바로 볼 카드 | 연결 이유 |
|---|---|---|
| "트랜잭션 안 외부 I/O부터 먼저 점검하고 싶다" | [트랜잭션 경계 체크리스트 카드](./transaction-boundary-external-io-checklist-card.md) | retry 설계 전에 경계 길이를 먼저 줄여 lock/pool 전파를 낮춘다 |
| "insert-if-absent에서 예외를 어떤 결과로 번역하지?" | [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md) | `duplicate/timeout/deadlock/40001`을 서비스 결과 3버킷으로 맞춘다 |
| "MySQL `1062`도 같은 retry 규칙으로 보면 되나?" | [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md) | `duplicate key`는 보통 재삽입 retry보다 winner read 분류가 먼저라는 점을 분리해 준다 |

## 핵심 개념

PostgreSQL `SERIALIZABLE`은 "read마다 강한 lock을 걸어서 모두 줄 세우는 모드"라고 이해하면 초반부터 헷갈린다.
실제로는 snapshot 위에 **SSI(Serializable Snapshot Isolation)** 검사를 추가해서, 동시에 실행된 트랜잭션 집합이 어떤 순서로도 직렬 실행처럼 설명되지 않으면 한쪽을 abort한다.

beginner는 아래 네 줄만 먼저 기억하면 된다.

1. `40001`은 "지금 시도는 버리고 처음부터 다시 하라"는 신호다.
2. 다시 실행할 단위는 SQL 한 줄이 아니라 **트랜잭션 전체 시도**다.
3. retry loop는 `@Transactional` 바깥, 즉 facade/application service 쪽에 둔다.
4. 외부 API 호출, 메일, 메시지 발행은 retry loop 안쪽에 두지 말고 outbox나 멱등성으로 분리한다.

즉 PostgreSQL `SERIALIZABLE`의 핵심은 "언제 락을 더 거느냐"보다 **실패한 시도를 어디서 버리고 어떻게 다시 시작하느냐**다.

## 이 문서가 필요한 상황

아래처럼 **읽고 판단한 뒤 쓰는** 경로에서 PostgreSQL `SERIALIZABLE`을 검토하거나 이미 쓰고 있다면 이 문서가 맞다.

- "겹치는 예약이 없으면 insert" 같은 absence-check + insert
- "활성 claim 합계가 100 이하면 승인" 같은 count/sum invariant
- "당직 의사가 최소 1명 남으면 해제" 같은 cross-row write skew
- 조회 결과를 믿고 update했는데 commit 순간 `40001`이 나는 경로

반대로 단일 row 조건부 update나 `UNIQUE`/`EXCLUDE`/원자적 `UPDATE ... WHERE ...`로 끝나는 문제라면, 그쪽이 `SERIALIZABLE`보다 더 단순한 경우가 많다.

## `40001`이 나는 전형 패턴

### 1. absence-check 후 insert

예: "이 시간대에 기존 예약이 없으면 새 예약을 넣자"

- 두 요청이 동시에 같은 범위를 읽는다
- 둘 다 "없다"고 판단한다
- 둘 다 insert를 시도한다
- PostgreSQL은 둘 다 성공시키면 serial order로 설명되지 않는다고 보고 한쪽을 `40001`로 종료할 수 있다

이 패턴에서 초보자가 틀리는 지점은 "조회는 성공했으니 결정도 유효하다"고 믿는 것이다.
`SERIALIZABLE`에서는 **commit 전까지 결정이 확정되지 않는다.**

### 2. count/sum invariant

예: "현재 사용량 합계가 100 이하면 이번 요청을 받자"

- 트랜잭션 A와 B가 같은 집합 합계를 읽는다
- 둘 다 아직 여유가 있다고 계산한다
- 각자 다른 row를 추가하거나 수정한다
- 결과적으로 합계 초과가 날 수 있으므로 PostgreSQL이 한쪽을 abort한다

이건 row 한 개 충돌이 아니라 **집합 규칙 충돌**이라서, 단순 row lock 직관만으로는 설명이 잘 안 된다.

### 3. cross-row write skew

예: "당직 의사는 최소 1명 남아야 한다"

- 의사 A를 해제하는 트랜잭션과 의사 B를 해제하는 트랜잭션이 동시에 시작한다
- 둘 다 "아직 다른 한 명이 남아 있다"고 읽는다
- 각자 서로 다른 row를 update한다
- 둘 다 성공하면 최소 1명 규칙이 깨진다

PostgreSQL은 이런 위험한 read-write dependency cycle을 SSI로 잡아 한쪽을 실패시킨다.

### 4. 읽은 row가 commit 전에 바뀜

예: 같은 row를 읽고 검증한 뒤 수정하는 경로

- 트랜잭션이 snapshot 기준으로 row를 읽는다
- 다른 트랜잭션이 그 row를 먼저 바꾸고 commit한다
- 내 트랜잭션이 그 row를 수정하거나 lock하려고 하면 `40001`로 밀릴 수 있다

이 경우 beginner는 "동시 update니까 optimistic lock 비슷한 것"으로 받아들이면 된다.
중요한 점은 역시 **새 transaction으로 처음부터 다시**라는 것이다.

## 서비스 계층에서 SQLSTATE를 어떻게 나눌까

`SERIALIZABLE` 경로라고 해서 모든 DB 예외를 retry하면 안 된다.
최소한 아래 정도로는 나눠야 서비스 코드를 망치지 않는다.

| SQLSTATE | 기본 처리 | 왜 이렇게 보나 |
|---|---|---|
| `40001` | whole-transaction retry | PostgreSQL이 직렬화 불가능한 시도를 안전하게 중단한 것이다 |
| `40P01` | retry 가능하지만 `40001`과 별도 집계 | deadlock이다. 재시도는 가능해도 lock ordering 문제일 수 있다 |
| `23505`, `23P01` | 보통 business/domain reject 또는 duplicate 처리 | unique/exclusion 위반은 "경쟁을 막아 준 정상 거절"일 수 있다. blanket retry 대상이 아니다 |
| class `08` | blind retry 금지, idempotent recovery 필요 | 연결 끊김/commit 결과 불명확일 수 있다 |
| `55P03`, `57014` | 보통 timeout/lock policy 문제로 분리 | `SERIALIZABLE`의 정상 경쟁이라기보다 blocking, cancel, budget 초과에 가깝다 |

핵심은 이것이다.

- `40001`이면 같은 request/command를 **새 시도**로 다시 돌린다
- `23505`를 `40001`처럼 취급하면 중복 요청과 정상 거절이 섞인다
- `40P01`은 재시도 가능해도 별도 telemetry bucket으로 본다

## 가장 작은 retry envelope

가장 흔한 기본형은 "facade가 retry loop를 들고, attempt service가 매번 새 `SERIALIZABLE` transaction을 여는 구조"다. 아래 세 장면을 따로 보면 초급자가 덜 헷갈린다.

## 동기 api retry envelope

가장 흔한 기본형이다.

구조:

1. facade가 retry loop를 가진다
2. per-attempt service가 `SERIALIZABLE` transaction 하나를 연다
3. 그 안에서 read -> validate -> write -> commit만 한다

beginner 규칙:

- 한 번의 attempt는 "새 transaction + 새 조회 + 새 계산"이다
- 이전 attempt에서 읽은 entity, 합계, boolean 판단을 재사용하지 않는다
- 동기 요청은 보통 `3회` 정도면 충분하다
- backoff는 짧게 두고, 무한 retry는 하지 않는다

## 동기 api 코드 스케치

```java
@Component
public class SerializableRetryExecutor {

    public <T> T run(Supplier<T> attemptWork) {
        for (int attempt = 1; attempt <= 3; attempt++) {
            try {
                return attemptWork.get();
            } catch (DataAccessException ex) {
                String sqlState = SqlStateExtractor.find(ex);
                boolean retryable = "40001".equals(sqlState) || "40P01".equals(sqlState);

                if (!retryable || attempt == 3) {
                    throw ex;
                }

                sleepWithJitter(attempt);
            }
        }

        throw new IllegalStateException("unreachable");
    }

    private void sleepWithJitter(int attempt) {
        try {
            Thread.sleep((long) (10L * Math.pow(2, attempt - 1)));
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(interrupted);
        }
    }
}
```

여기서 `SqlStateExtractor.find(ex)`는 프레임워크 예외 안쪽 `SQLException` cause chain을 따라가 `SQLSTATE`를 꺼내는 작은 helper라고 생각하면 된다.

## transaction service 코드 스케치

```java
@Service
@RequiredArgsConstructor
public class BookingFacade {

    private final SerializableRetryExecutor retryExecutor;
    private final BookingTxService bookingTxService;

    public BookingResult reserve(ReserveCommand command) {
        return retryExecutor.run(() -> bookingTxService.reserveOnce(command));
    }
}

@Service
public class BookingTxService {

    @Transactional(isolation = Isolation.SERIALIZABLE, propagation = Propagation.REQUIRES_NEW)
    public BookingResult reserveOnce(ReserveCommand command) {
        // read current state
        // validate business rule
        // write rows
        // commit
        return BookingResult.success();
    }
}
```

## outbox를 곁들인 retry envelope

예: 결제 승인, 메일 발송, Kafka publish가 같이 붙는 경우

이 경우에도 retry loop 바깥 구조는 같지만, 트랜잭션 안에는 다음만 둔다.

- 비즈니스 row 변경
- outbox insert 또는 "처리 예정" 상태 저장

밖으로 빼야 하는 것:

- 결제 API 호출
- 메일/푸시 발송
- 메시지 브로커 publish

이유는 간단하다.
`40001`은 **커밋 직전에도** 날 수 있으므로, 외부 부작용을 안쪽에 넣으면 retry가 중복 결제나 중복 발송으로 바뀐다.

가장 작은 안전한 모양은 아래다.

1. retry loop 안쪽 transaction에서 business row + outbox row를 함께 commit
2. commit 성공 후 relay가 outbox를 publish
3. publish 재시도는 outbox/idempotency 규칙으로 별도 처리

## queue worker retry envelope

비동기 worker는 동기 API보다 retry budget을 조금 더 길게 줄 수 있다.
대신 **메시지 중복 소비 안전성**을 먼저 챙겨야 한다.

최소 규칙:

- inbox 또는 idempotency key를 transaction 안에서 같이 기록한다
- `40001`/`40P01`만 bounded retry한다
- commit 성공 뒤에 ack 또는 offset commit을 보낸다
- retry budget을 넘기면 requeue/DLQ로 넘긴다

권장 시작점:

| 흐름 | 권장 attempt | backoff 시작점 | 꼭 같이 둘 것 |
|---|---|---|---|
| 동기 API, pure DB command | 3 | `10ms` | 짧은 transaction |
| 동기 API + outbox | 3 | `10ms` | outbox, command id |
| queue worker | 5 | `25ms` | inbox/idempotency, commit 후 ack |

## retry loop에서 다시 계산해야 하는 것

초보자가 가장 많이 놓치는 부분이다.
retry는 "같은 SQL을 한 번 더"가 아니라, **같은 비즈니스 의사결정을 새 snapshot에서 다시 수행**하는 일이다.

다시 계산해야 하는 것:

- 조회 결과 전체
- count/sum 같은 파생값
- "예약 가능", "아직 한 명 남음" 같은 boolean 판단
- transaction 안에서 생성한 임시 객체/엔티티 상태

그대로 들고 가도 되는 것:

- command id
- idempotency key
- 사용자 입력 자체
- 최종 응답을 위한 correlation id

즉 "판단의 재료"는 다시 읽고, "같은 요청임을 증명하는 키"만 유지한다.

## 하면 안 되는 패턴

### 1. 같은 `@Transactional` 메서드 안에서 catch 후 다시 쿼리

잘못된 이유:

- 현재 transaction attempt는 이미 실패한 시도다
- persistence context, snapshot, rollback-only 상태가 섞인다
- 설명도 어렵고 테스트도 불안정해진다

retry는 항상 **새 transaction**으로 해야 한다.

### 2. controller부터 외부 API까지 전부 retry

잘못된 이유:

- 같은 HTTP 요청 안에서 결제/메일/브로커 publish가 중복된다
- sleep 동안 request thread와 connection을 오래 잡고 있게 된다
- 실패 원인 분리가 어려워진다

retry envelope는 command 처리 핵심만 감싸고, side effect는 분리한다.

### 3. `40001`과 `23505`를 한 bucket에 넣기

잘못된 이유:

- serialization retry pressure와 business reject가 섞인다
- "capacity가 다 찬 정상 거절"과 "경합으로 재시도 필요"를 구분 못 한다
- 운영 알람이 무의미해진다

### 4. 무한 즉시 retry

잘못된 이유:

- hot key에서 경합만 더 키운다
- application thread와 connection pool을 태운다
- 결국 tail latency만 늘고 성공률은 크게 안 오른다

bounded retry + 짧은 backoff가 기본이다.

## 바로 써먹는 판단표

| 질문 | 기본 답 |
|---|---|
| `40001`을 받으면 무엇을 다시 실행하나 | SQL 한 줄이 아니라 transaction attempt 전체 |
| retry loop는 어디에 두나 | `@Transactional` 바깥 facade/application service |
| 외부 API 호출은 어디에 두나 | retry transaction 바깥, 보통 outbox 뒤 |
| 자동 retry 횟수는 몇 번부터 시작하나 | 동기 3회, worker 5회 정도 |
| `40P01`도 같은 bucket인가 | 아니다. 재시도 가능하지만 deadlock bucket으로 따로 본다 |
| `23505`도 무조건 retry하나 | 아니다. 보통 duplicate/domain reject로 본다 |

## 꼬리질문

> Q: 왜 `40001`이면 SQL 한 줄만 다시 실행하면 안 되나요?
> 의도: retry 단위가 query가 아니라 transaction attempt 전체라는 점을 이해하는지 확인
> 핵심: 이전 snapshot과 판단이 이미 무효가 되었기 때문이다

> Q: PostgreSQL `SERIALIZABLE`에서 외부 API 호출을 transaction 안에 두면 왜 위험한가요?
> 의도: commit 직전 abort와 중복 부작용을 연결할 수 있는지 확인
> 핵심: DB는 rollback됐는데 외부 부작용은 이미 실행될 수 있기 때문이다

> Q: `40001`과 `23505`를 같은 재시도 정책으로 다루면 왜 운영이 꼬이나요?
> 의도: retryable conflict와 business reject를 구분하는지 확인
> 핵심: serialization pressure와 정상 거절이 같은 지표에 섞여 원인 해석이 무너진다

## 한 줄 정리

PostgreSQL `SERIALIZABLE`의 retry는 "실패한 SQL 재실행"이 아니라, `40001`이 난 **트랜잭션 시도 전체를 새 snapshot에서 다시 시작하는 서비스 계층 계약**이다.
