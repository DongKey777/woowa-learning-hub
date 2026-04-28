# 트랜잭션 격리수준과 락

> 한 줄 요약: 이 문서는 [트랜잭션 기초](./transaction-basics.md)와 [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) 다음 단계에서, "무엇을 같이 되돌릴까"와 "동시에 실행될 때 무엇이 보일까"가 실제 락/incident 대응으로 어떻게 이어지는지 묶어 주는 심화 bridge다.

**난이도: 🔴 Advanced**

transaction, ACID, isolation level, locking을 한 흐름으로 설명해야 할 때 보는 심화 primer다. 처음 DB를 배우는 단계라면 [트랜잭션 기초](./transaction-basics.md)에서 `commit`/`rollback` 경계를 먼저 잡고, [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)에서 row 재조회와 범위 재조회 차이를 먼저 분리한 뒤 이 문서로 올라오는 편이 안전하다.

관련 문서:

- [트랜잭션 기초](./transaction-basics.md)
- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- [락 기초](./lock-basics.md)
- [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md)
- [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
- [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)
- [Read Committed vs Repeatable Read Anomalies](./read-committed-vs-repeatable-read-anomalies.md)
- [Compare-and-Swap과 Pessimistic Locks](./compare-and-swap-vs-pessimistic-locks.md)
- [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
- [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)
- [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md)

retrieval-anchor-keywords: transaction basics next step, transaction isolation basics next, transaction acid, acid, atomicity consistency isolation durability, transaction isolation, isolation level, dirty read, non-repeatable read, phantom read, read committed, repeatable read, serializable, locking read, select for update, optimistic lock, pessimistic lock, when to lock, lost update, deadlock, lock timeout, serialization failure, incident handling, transaction primer 다음 뭐 읽어요, 격리 수준 기초 다음 뭐 봐요, 처음 트랜잭션 다음 단계, isolation basics after beginner, what is select for update, commit 했는데 왜 두 번 팔려요, select 두 번 했는데 값이 달라요, 언제 for update 써요, deadlock 나면 다음 뭐 봐요, transaction lock isolation difference

<details>
<summary>Table of Contents</summary>

- [기초에서 incident로 올라가는 읽기 순서](#기초에서-incident로-올라가는-읽기-순서)
- [이 문서 다음에 보면 좋은 문서](#이-문서-다음에-보면-좋은-문서)
- [왜 중요한가](#왜-중요한가)
- [트랜잭션이란](#트랜잭션이란)
- [ACID를 어떻게 이해해야 하나](#acid를-어떻게-이해해야-하나)
- [격리수준과 대표 이상 현상](#격리수준과-대표-이상-현상)
- [격리수준별로 무엇이 달라지나](#격리수준별로-무엇이-달라지나)
- [락은 언제 필요한가](#락은-언제-필요한가)
- [낙관적 락과 비관적 락](#낙관적-락과-비관적-락)
- [백엔드에서 자주 만나는 예시](#백엔드에서-자주-만나는-예시)
- [한 번에 정리하는 선택 기준](#한-번에-정리하는-선택-기준)
- [추천 공식 자료](#추천-공식-자료)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 기초에서 incident로 올라가는 읽기 순서

이 문서는 beginner primer를 건너뛰고 바로 여는 문서라기보다, 두 primer를 읽고도 "`FOR UPDATE`를 언제 붙이지?", "`deadlock`이 보이면 어디까지가 개념이고 어디부터가 incident 대응이지?"가 남았을 때 여는 bridge다.

| 학습 단계 | 지금 막힌 질문 | 먼저 볼 문서 | 이 문서를 읽은 뒤 다음 단계 |
|---|---|---|---|
| 1단계. 경계 이해 | "무엇을 같이 `commit`/`rollback`하지?" | [트랜잭션 기초](./transaction-basics.md) | 같은 row/범위를 다시 읽을 때 왜 달라지는지 궁금해지면 [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |
| 2단계. 가시성 이해 | "`select`를 두 번 했는데 왜 값이나 행 수가 달라지지?" | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) | plain `SELECT`와 locking read를 같이 봐야 하면 이 문서 |
| 3단계. bridge | "`@Transactional`도 있는데 언제 `FOR UPDATE`, version, constraint까지 붙이지?" | 이 문서 | 엔진 차이, retry, deadlock처럼 증상이 구체화되면 아래 follow-up |
| 4단계. incident handling | "`lock timeout`, `deadlock`, `40001`이 실제로 떴다" | [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md), [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md) | 엔진별 재현/정책까지 내려간다 |

짧게 기억하면 progression은 아래 네 줄이다.

1. [트랜잭션 기초](./transaction-basics.md): 같이 성공/실패할 경계를 먼저 잡는다.
2. [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md): 같은 row 재조회와 범위 재조회 차이를 먼저 분리한다.
3. 이 문서: 격리 수준, locking read, optimistic/pessimistic lock, constraint를 한 프레임으로 묶는다.
4. incident 문서: `deadlock`, `lock timeout`, `40001 retry`처럼 실제 증상이 붙었을 때만 내려간다.

## 먼저 분리할 세 질문

이 문서는 용어를 한꺼번에 외우기보다, 아래 세 질문을 분리해 주는 역할로 읽는 편이 훨씬 쉽다.

| 지금 막힌 질문 | 먼저 붙일 축 | 첫 문장 |
|---|---|---|
| "왜 주문 저장과 재고 차감이 같이 취소되지?" | 트랜잭션 경계 | 무엇을 같이 `commit`/`rollback`할지 정하는 문제다 |
| "`commit`은 했는데 같은 값을 다시 읽으니 달라졌어" | 격리 수준 | 동시에 실행될 때 무엇이 보이느냐의 문제다 |
| "마지막 재고를 누가 먼저 잡게 해야 하지?" | 락 전략 | 경쟁 자원을 기다리게 할지, 실패시키고 재시도할지 정하는 문제다 |

같은 주문 생성 요청을 한 줄씩 자르면 더 덜 추상적이다.

| 코드/증상에서 보이는 장면 | 이 문서가 답하는 부분 | 먼저 다른 문서가 답하는 부분 |
|---|---|---|
| `@Transactional`이 붙어 있다 | 트랜잭션과 격리 수준이 어디에 걸리는지 | JPA인지 JDBC인지 자체는 [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| `commit`은 됐는데 마지막 재고가 두 번 팔렸다 | 격리 수준만으로 안 끝나고 락/제약이 왜 필요한지 | 입문 설명은 [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |
| `SELECT ... FOR UPDATE`가 처음 보인다 | plain `SELECT`와 locking read 차이 | lock 용어 첫 감은 [락 기초](./lock-basics.md) |

## 이 문서 다음에 보면 좋은 문서

- `@Transactional`, `Connection`, `EntityManager`, `flush`처럼 JDBC/JPA/Spring 위에서 보이는 이름과 DB 트랜잭션 개념을 연결하려면 [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md)를 먼저 같이 본다.
- 질문이 "어떤 이상 현상을 막아야 하나"보다 "`REQUIRED` / `REQUIRES_NEW` 때문에 왜 커넥션이 오래 잡히나", "왜 pool이 마르나"에 가까우면 [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)로 이어진다.
- raw JDBC에서 `autoCommit`, `commit/rollback`, batch와 transaction boundary를 코드로 확인하려면 [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)을 붙여 읽는 편이 좋다.
- 실제 증상이 `deadlock`, `lock timeout`, `waiting for lock`에 가까우면 [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)으로 바로 내려가서 incident 순서대로 확인한다.
- 실제 증상이 `40001`, serialization failure, "retry를 어디에 둘까"라면 [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)과 [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)를 이어 본다.

## 왜 중요한가

백엔드 서버는 요청을 순서대로 하나씩만 처리하지 않는다.  
여러 요청이 동시에 같은 데이터를 읽고 바꾸면 다음 같은 문제가 생긴다.

- 두 요청이 같은 잔액을 보고 동시에 차감해서 음수 잔액이 생김
- 재고가 `1`개인데 두 사용자가 동시에 구매 성공
- 같은 회의실 시간대를 서로 비어 있다고 보고 둘 다 예약

JDBC에서 `setAutoCommit(false)`와 `commit/rollback`으로 보이든, Spring/JPA에서 `@Transactional`, `flush`, `EntityManager`로 보이든 결국 같은 DB 동시성 문제를 다른 층위에서 보고 있는 것이다.

이 문제를 설명할 때는 보통 네 단계를 같이 봐야 한다.

1. 어떤 SQL들을 하나의 작업으로 묶을지: transaction boundary
2. 그 작업이 지켜야 할 성질이 무엇인지: ACID
3. 동시 실행에서 어떤 이상 현상을 막아야 하는지: isolation level
4. 충돌을 기다릴지, 실패시키고 재시도할지: locking strategy

즉 트랜잭션만 안다고 끝나지 않고, 격리수준과 락까지 같이 이해해야 실제 동시성 문제를 설명할 수 있다.

## 트랜잭션이란

트랜잭션은 **하나의 논리적 작업 단위**다.
여러 SQL이 있어도 비즈니스적으로 하나의 작업이라면 같이 성공하거나 같이 실패해야 한다.

예:

- 계좌 이체: 출금과 입금은 같이 성공하거나 같이 실패해야 한다
- 주문 생성: 주문 row 저장과 재고 차감은 따로 성공하면 안 된다
- 상태 전이: 결제 성공 후 주문 상태를 `PAID`로 바꾸는 작업은 중간 상태가 남으면 안 된다

보통 트랜잭션은 다음 흐름으로 이해하면 된다.

- `BEGIN` 또는 `START TRANSACTION`
- 여러 SQL 실행
- 성공이면 `COMMIT`
- 중간에 실패하면 `ROLLBACK`

JDBC에서는 이 흐름이 보통 `setAutoCommit(false)` -> 여러 SQL -> `commit()` / `rollback()`으로 드러난다.
코드 감각이 필요하면 [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)을 같이 보면 검색어가 바로 이어진다.

중요한 점은 트랜잭션이 있다고 해서 동시성 충돌이 자동으로 해결되지는 않는다는 것이다.
같은 데이터를 여러 요청이 함께 만지면 어떤 격리수준과 락 전략을 쓸지 별도로 정해야 한다.

## ACID를 어떻게 이해해야 하나

ACID는 트랜잭션을 설명할 때 가장 먼저 나오는 네 가지 성질이다.
면접에서는 정의만 외우기보다 "무엇을 보장하고, 무엇은 별도 설계가 필요한가"까지 같이 말하는 편이 좋다.

### Atomicity (원자성)

- 전부 성공하거나 전부 실패해야 한다
- 중간 상태가 남으면 안 된다
- 실패하면 rollback으로 이전 상태로 되돌린다

예를 들어 송금에서 출금만 되고 입금이 안 되면 원자성이 깨진 것이다.

### Consistency (일관성)

- 트랜잭션 전후로 데이터가 규칙을 지켜야 한다
- 예: 재고는 음수가 되면 안 된다, 중복 예약이 생기면 안 된다

주의할 점은 consistency가 "DB가 알아서 모든 비즈니스 규칙을 지켜준다"는 뜻은 아니라는 것이다.
규칙은 `UNIQUE`, `CHECK`, 외래키, 조건부 `UPDATE`, 애플리케이션 검증처럼 **실제로 표현된 제약**이 있어야 보호된다.

### Isolation (격리성)

- 동시에 실행되는 트랜잭션이 서로에게 부적절하게 간섭하지 않아야 한다
- 다만 "완전히 안 보이게 막는다"가 아니라, **어느 정도까지 허용할지**를 격리수준으로 정한다

즉 isolation은 "동시성을 없애는 기능"이 아니라, 동시성 때문에 생길 수 있는 이상 현상을 어디까지 허용할지 정하는 기능이다.

### Durability (지속성)

- commit된 결과는 장애가 나더라도 보존되어야 한다
- 보통 WAL, redo log, fsync 정책 같은 저장 엔진 메커니즘이 이를 뒷받침한다

핵심은 **commit 전에는 아직 확정된 상태가 아니고, commit 후에는 살아남아야 한다**는 점이다.

## 격리수준과 대표 이상 현상

격리수준(isolation level)은 동시에 실행되는 트랜잭션을 어느 정도까지 분리할지 정하는 기준이다.
신입 단계에서는 아래 세 가지 이상 현상을 구분할 수 있으면 설명이 훨씬 명확해진다.

| 이상 현상 | 무엇이 문제인가 | 짧은 예시 |
|---|---|---|
| Dirty Read | 다른 트랜잭션이 아직 commit하지 않은 값을 읽음 | A가 잔액을 `0`으로 바꿨다가 rollback했는데, B가 그 `0`을 읽음 |
| Non-repeatable Read | 같은 row를 두 번 읽었는데 값이 달라짐 | A가 주문 상태를 읽은 뒤, B가 `WAITING -> PAID`로 바꾸고 commit해서 A의 재조회 결과가 달라짐 |
| Phantom Read | 같은 조건의 범위 조회를 두 번 했는데 row 집합이 달라짐 | A가 `status='WAITING'` 주문 수를 셌는데, B가 새 주문을 insert해서 A의 재조회 count가 늘어남 |

구분 포인트는 다음처럼 기억하면 편하다.

- dirty read: **commit되지 않은 값**을 봤는가
- non-repeatable read: **같은 row 값**이 달라졌는가
- phantom read: **같은 조건의 결과 집합**이 달라졌는가

실무에서 많이 헷갈리는 점은 phantom read가 단순히 "다시 조회하니 숫자가 달라졌다"로 끝나지 않는다는 것이다.
실제로는 "비어 있다고 믿고 insert했다", "이 범위는 안전하다고 믿고 승인했다"처럼 **범위나 부재를 믿고 판단하는 로직**에서 문제를 만든다.

## 격리수준별로 무엇이 달라지나

아래 표는 입문용으로 이해하기 좋은 기본 비교다.
정확한 세부 동작은 DB 엔진 구현에 따라 달라질 수 있다.

| 격리수준 | Dirty Read | Non-repeatable Read | Phantom Read | 보통 어떻게 이해하면 좋은가 |
|---|---|---|---|---|
| `READ UNCOMMITTED` | 가능 | 가능 | 가능 | 거의 쓰지 않는 가장 약한 수준 |
| `READ COMMITTED` | 막음 | 남을 수 있음 | 남을 수 있음 | 각 쿼리 시점의 최신 commit 데이터 기준 |
| `REPEATABLE READ` | 막음 | 보통 막음 | 엔진에 따라 다름 | 한 transaction 안에서 같은 row 재조회 일관성을 더 챙김 |
| `SERIALIZABLE` | 막음 | 막음 | 막음 | 순차 실행한 것처럼 보이게 하는 가장 강한 수준 |

여기서 많이 나오는 꼬리 포인트는 다음이다.

- `READ COMMITTED`는 dirty read는 막지만, 재조회 결과가 바뀌는 것은 허용할 수 있다
- `REPEATABLE READ`는 같은 row 재조회에는 강하지만, 범위/집합 규칙까지 자동으로 안전해지는 것은 아니다
- `SERIALIZABLE`은 가장 강하지만, 대기나 retry 비용이 커질 수 있다

엔진별로 보면 더 정확하다.

- MySQL InnoDB는 `REPEATABLE READ`에서 locking read와 next-key lock으로 일부 phantom을 막을 수 있다
- PostgreSQL의 `REPEATABLE READ`는 snapshot isolation에 가깝고, 범위/집합 불변식 보호는 `SERIALIZABLE`이나 constraint가 더 직접적이다

그래서 격리수준은 "무조건 높게"가 아니라, **막아야 하는 이상 현상에 맞춰** 고르는 것이 핵심이다.

## 락은 언제 필요한가

입문 단계에서 가장 실용적인 질문은 "그래서 언제 락을 써야 하냐"다.
답은 "충돌을 DB가 자동으로 정리해주지 않는 읽기-판단-쓰기 경로가 있을 때"다.

### 1. 같은 row를 읽고 계산한 뒤 다시 쓸 때

예:

- 현재 잔액을 읽고 `balance - 1000`으로 갱신
- 현재 재고를 읽고 `stock - 1`로 갱신

이 경우에는 두 요청이 같은 값을 읽고 각각 저장해 버리는 lost update가 생길 수 있다.
해법은 보통 셋 중 하나다.

- 원자적 SQL: `UPDATE ... SET stock = stock - 1 WHERE stock > 0`
- 낙관적 락: `version` column 비교
- 비관적 락: `SELECT ... FOR UPDATE`

### 2. 충돌이 잦아서 "실패 후 재시도"보다 "잠깐 대기"가 나을 때

예:

- 핫한 재고 row 하나를 두고 요청이 몰리는 경우
- 좌석 1개를 선점하는 경우

이때는 pessimistic lock이 실무적으로 더 단순할 수 있다.
충돌이 많으면 optimistic lock은 계속 실패와 재시도를 만들고, 오히려 사용자 경험이 나빠질 수 있다.

### 3. "없음"이나 범위를 믿고 insert/update할 때

예:

- "이 시간대 예약이 없으면 insert"
- "활성 쿠폰 claim 합계가 capacity 이하이면 승인"

이 경우는 row 하나만 잠그는 것으로 끝나지 않을 수 있다.
문제의 핵심이 특정 row가 아니라 **범위, 부재, 집합 규칙**이기 때문이다.

그래서 다음 같은 장치가 필요할 수 있다.

- `UNIQUE`, exclusion constraint 같은 제약
- MySQL의 gap lock / next-key lock 같은 범위 보호
- guard row나 counter row
- `SERIALIZABLE` + retry

### 4. 락을 오래 잡으면 안 되는 상황

다음은 lock을 잡기보다 경계를 다시 잘라야 하는 경우다.

- 트랜잭션 안에서 외부 API 호출을 기다림
- 사용자 입력 대기
- 메시지 브로커, 파일 I/O, 네트워크 왕복이 길게 들어감

이런 작업은 lock을 잡은 채 오래 기다리게 만들어 lock wait과 deadlock을 키운다.
DB 상태 변화만 짧게 transaction 안에 넣고, 오래 걸리는 작업은 밖으로 빼는 편이 안전하다.

## 낙관적 락과 비관적 락

낙관적 락과 비관적 락은 둘 다 동시성 제어 방법이지만, 성격이 다르다.

| 구분 | 낙관적 락 | 비관적 락 |
|---|---|---|
| 기본 가정 | 충돌이 자주 나지 않을 것 | 충돌이 충분히 날 수 있음 |
| 대표 구현 | `version` column, CAS | `SELECT ... FOR UPDATE` |
| 장점 | lock 점유 시간이 짧고 확장성이 좋다 | 충돌 상황을 더 직접적으로 막는다 |
| 단점 | 실패 시 retry 필요 | 대기와 deadlock 가능성이 있다 |
| 잘 맞는 경우 | 충돌이 드물고 retry가 싼 작업 | 충돌이 잦고 중복 성공이 치명적인 작업 |

짧게 말하면:

- optimistic lock은 **나중에 충돌을 감지**한다
- pessimistic lock은 **미리 충돌을 막는다**

둘 중 어느 쪽이 "더 안전한 정답"인지는 없다.
충돌 빈도와 retry 비용이 결정 기준이다.

## 백엔드에서 자주 만나는 예시

### 예시 1. 잔액 차감

두 요청이 동시에 `balance = 10000`을 읽고 각각 `1000`을 차감하면, 둘 다 성공해도 최종 결과가 잘못될 수 있다.

가장 먼저 고려할 수 있는 해법은 원자적 SQL이다.

```sql
UPDATE account
SET balance = balance - 1000
WHERE id = 1
  AND balance >= 1000;
```

영향받은 row 수가 `1`이면 성공이고, `0`이면 잔액 부족으로 처리할 수 있다.
이 패턴으로 끝난다면 굳이 긴 lock을 잡지 않는 편이 낫다.

### 예시 2. 주문 상태 전이

현재 상태를 읽고 "아직 `WAITING`이면 `PAID`로 바꾼다"는 로직은 동시에 실행되면 충돌할 수 있다.

이럴 때는 다음을 고려한다.

- 충돌이 적으면 optimistic lock
- 같은 주문 row에 충돌이 잦으면 `FOR UPDATE`
- 상태 전이 조건을 SQL에 직접 넣을 수 있으면 조건부 `UPDATE`

즉 핵심은 "읽고 판단하고 다시 쓰는 사이"에 다른 요청이 끼어들 수 있느냐이다.

### 예시 3. 회의실 예약

`10:00 ~ 11:00` 예약이 없는지 조회한 뒤 insert하는 방식은 phantom 문제를 만들기 쉽다.
둘 다 빈 범위를 보고 동시에 insert할 수 있기 때문이다.

이 경우는 단순 row lock보다 다음이 더 중요하다.

- 겹침 규칙을 제약으로 옮길 수 있는가
- 범위를 안전하게 보호하는 locking read가 있는가
- 엔진이 지원하지 않으면 guard row나 slot model로 바꿔야 하는가

즉 "예약이 없다"는 사실 자체를 어떻게 보호할지 설계해야 한다.

## 한 번에 정리하는 선택 기준

| 상황 | 먼저 떠올릴 것 |
|---|---|
| 여러 SQL이 같이 성공/실패해야 함 | transaction |
| commit되지 않은 값은 절대 보면 안 됨 | 최소 `READ COMMITTED` |
| 같은 transaction 안에서 같은 row를 다시 읽어도 같아야 함 | `REPEATABLE READ` 이상 검토 |
| 범위 결과나 "없음"을 믿고 결정함 | constraint, range-safe locking, guard row, `SERIALIZABLE` 검토 |
| 충돌이 적고 retry가 쉬움 | optimistic lock |
| 충돌이 많고 중복 성공이 치명적임 | pessimistic lock 또는 atomic SQL |
| 외부 호출이 길게 섞임 | lock을 늘리기보다 transaction boundary를 줄이기 |

실무에서는 보통 이 순서로 생각하면 된다.

1. transaction으로 같이 성공/실패해야 하는 범위를 정한다
2. 막아야 할 anomaly를 보고 isolation level을 고른다
3. 가능하면 constraint나 atomic SQL로 끝낸다
4. 그래도 남는 충돌에 optimistic/pessimistic lock을 고른다

## 추천 공식 자료

- PostgreSQL Transaction Isolation
  - https://www.postgresql.org/docs/current/transaction-iso.html
- MySQL 8.0 InnoDB Transaction Isolation Levels
  - https://dev.mysql.com/doc/refman/8.0/en/innodb-transaction-isolation-levels.html
- MySQL 8.0 InnoDB Locking
  - https://dev.mysql.com/doc/refman/8.0/en/innodb-locking.html
- SQLite Transactions
  - https://www.sqlite.org/lang_transaction.html

## 면접에서 자주 나오는 질문

### Q. 트랜잭션이 왜 필요한가요?

- 여러 SQL을 하나의 작업 단위로 묶어 전부 성공하거나 전부 실패하게 만들기 위해 필요하다.

### Q. ACID의 Consistency는 DB가 비즈니스 규칙을 자동으로 지켜준다는 뜻인가요?

- 아니다. 규칙은 제약조건, 조건부 update, 애플리케이션 로직처럼 실제 장치로 표현되어야 한다.

### Q. Dirty Read, Non-repeatable Read, Phantom Read의 차이는 무엇인가요?

- dirty read는 commit 전 값을 읽는 문제다.
- non-repeatable read는 같은 row를 다시 읽었더니 값이 달라지는 문제다.
- phantom read는 같은 조건의 범위 조회 결과 집합이 달라지는 문제다.

### Q. 락은 언제 필요한가요?

- 읽고 판단한 뒤 다시 쓰는 경로에서 충돌이 날 수 있을 때 필요하다.
- 다만 먼저 constraint나 atomic SQL로 끝낼 수 있는지 보는 것이 좋다.

### Q. Serializable이 항상 정답인가요?

- 가장 강한 격리수준이지만 비용이 크다.
- 막아야 하는 이상 현상에 맞춰 필요한 수준만 선택하는 편이 실무적으로 낫다.
