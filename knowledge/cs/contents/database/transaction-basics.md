# 트랜잭션 기초 (Transaction Basics)

> 한 줄 요약: 트랜잭션은 commit/rollback으로 묶인 작업 단위이고, ACID 4글자는 그 단위가 어떤 사고에서 살아남아야 하는지를 네 가지 다른 각도에서 약속한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Database First-Step Bridge](./database-first-step-bridge.md)
- [Database README: 빠른 탐색](./README.md#빠른-탐색)
- [Junior Backend Roadmap: 3단계 데이터베이스 기본기](../../JUNIOR-BACKEND-ROADMAP.md#3단계-데이터베이스-기본기)
- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Isolation Anomaly Cheat Sheet](./isolation-anomaly-cheat-sheet.md)
- [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)
- [Spring @Transactional 기초](../spring/spring-transactional-basics.md)

retrieval-anchor-keywords: transaction basics, acid intro, commit rollback intro, atomicity for beginners, durability beginner, isolation beginner, transaction unit of work, what is transaction, savepoint basics, beginner db transaction, transaction to isolation bridge, atomicity vs isolation beginner, commit not enough concurrency, beginner isolation faq, 트랜잭션이 뭐예요, commit이 뭔가요, 격리수준 왜 배우나요

## 핵심 개념

트랜잭션(transaction)은 **여러 SQL 문장을 하나의 사건처럼 묶어 주는 단위**다. 학습자가 처음 만나는 가장 흔한 비유는 송금이다.

```
계좌 A에서 1만 원 차감
계좌 B에 1만 원 입금
```

이 두 줄 사이에 데이터베이스가 죽거나 네트워크가 끊기면 "차감은 되었는데 입금은 안 된" 상태가 남는다. 트랜잭션은 둘 다 성공하거나(`commit`), 아예 둘 다 일어나지 않은 것처럼 되돌리거나(`rollback`) 둘 중 하나만 허용한다.

입문자가 자주 헷갈리는 지점:

- 트랜잭션은 SQL 한 줄짜리도 만들 수 있다 — 단지 보통은 2줄 이상에 의미가 있다
- 트랜잭션은 "느린 동기화" 같은 것이 아니라 **사고 후 복구를 위한 약속**이다
- `commit`을 하지 않으면 다른 세션은 그 변경을 보지 못한다 (격리 수준에 따라 다르지만 보통 그렇다)

## 한눈에 보기 — ACID 4글자

| 글자 | 영문 | 한 줄 의미 | 입문 단계에서 외울 그림 |
|---|---|---|---|
| A | Atomicity (원자성) | 트랜잭션 안의 모든 변경은 전부 일어나거나 전부 없던 일이 된다 | 송금이 절반만 성공하지 않는다 |
| C | Consistency (일관성) | 트랜잭션 끝났을 때 DB가 정의한 규칙(제약, 외래키 등)을 모두 만족한다 | 잔액이 음수가 될 수 없는 규칙이 깨지지 않는다 |
| I | Isolation (격리성) | 동시에 도는 다른 트랜잭션이 내 중간 결과를 보지 않는다 | 옆 사람이 내가 쓰던 메모장을 훔쳐보지 않는다 |
| D | Durability (지속성) | `commit`이 끝났으면 그 결과는 정전/재시작 후에도 사라지지 않는다 | 영수증이 출력되면 손에 남는다 |

ACID는 "트랜잭션 = 안전"이라는 추상적 결론이 아니라 **네 가지 다른 종류의 사고**(중간 실패, 규칙 위반, 동시성 간섭, 정전)에 대한 각각의 답이다.

## 상세 분해 — commit과 rollback의 라이프사이클

가장 단순한 흐름은 세 줄이다:

1. **begin** — 새 트랜잭션을 시작한다 (대부분의 ORM/JDBC는 첫 SQL 직전에 자동으로 시작한다)
2. **여러 SQL 실행** — `INSERT`, `UPDATE`, `DELETE`, `SELECT`가 임의로 섞일 수 있다
3. **commit 또는 rollback** — 끝낸다

```
BEGIN;
UPDATE accounts SET balance = balance - 10000 WHERE id = 1;
UPDATE accounts SET balance = balance + 10000 WHERE id = 2;
COMMIT;
```

중간 줄 하나가 실패하면 보통 애플리케이션이 `ROLLBACK`을 호출하거나, DB가 자동으로 트랜잭션을 abort한다. 그 결과 1번 계좌의 잔액도 원래대로 돌아간다.

`savepoint`는 트랜잭션 안에 부분 되돌림 지점을 찍는 것이다. 입문 단계에서는 "rollback의 작은 버전이 가능하구나" 정도만 기억해도 충분하다 — 실무에서 의미가 커지는 시점은 한 트랜잭션 안에서 여러 step을 나눠서 처리할 때다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "INSERT 한 줄짜리는 트랜잭션이 아니다" | 모든 SQL은 사실 implicit transaction 안에서 돈다 — autocommit이 매번 commit을 끼워 줄 뿐 | 한 줄이라도 commit/rollback 경계가 있다는 사실을 먼저 인식 |
| "rollback하면 성능이 나쁘다" | rollback은 abort 처리이며 보통 commit보다 더 무거울 이유가 없다 | rollback이 자주 일어나는 것이 문제(=충돌이 잦다)이지, rollback 자체가 문제는 아니다 |
| "트랜잭션을 길게 잡으면 더 안전하다" | 긴 트랜잭션은 락을 오래 잡아 다른 사용자를 기다리게 만들고 deadlock 가능성을 키운다 | 트랜잭션은 "필요한 SQL만" 짧게 묶는 것이 안전 |
| "ACID는 모두 같은 종류의 보장이다" | A/C/I/D는 각각 다른 사고에 대한 답이다 — isolation 한 글자만 올린다고 atomicity가 함께 강해지지 않는다 | 어떤 사고를 막고 싶은지 먼저 정하고, 그 글자에 해당하는 도구(트랜잭션 경계, 제약, 격리 수준, fsync)부터 본다 |

## 실무에서 쓰는 모습

가장 흔한 시나리오 둘:

**(1) 송금/잔액 변경** — 입금과 출금처럼 두 row를 함께 바꿔야 하는 경우. 한 트랜잭션으로 묶지 않으면 시스템 장애 시 절반만 성공한 상태가 남는다. 이때 atomicity가 살아 있어야 한다.

**(2) 주문 생성 + 재고 차감** — 하나가 실패하면 다른 것도 무효여야 한다. 여기서 학습자가 새로 배워야 하는 것은 트랜잭션만으로는 다른 사용자가 동시에 같은 재고를 차감하는 문제를 막지 못한다는 점이다. 그 문제는 격리 수준(I)과 락의 영역으로 넘어간다 — 그래서 `## 더 깊이 가려면` 절에서 다음 문서로 넘긴다.

스프링/JPA 환경에서는 `@Transactional` 어노테이션이 begin/commit/rollback을 자동으로 끼워 준다. 처음에는 "이 메서드가 시작될 때 트랜잭션이 열리고 끝날 때 닫힌다" 정도로 단순화해서 본다.

## 트랜잭션에서 격리 수준으로 넘어갈 때 FAQ

먼저 그림 하나만 고정하면 덜 헷갈린다. 트랜잭션은 "내 작업을 한 덩어리로 끝내는 규칙"이고, 격리 수준은 "동시에 일하는 다른 사람과 서로 어디까지 보이게 할지 정하는 규칙"이다.

| 질문이 겨누는 것 | 먼저 떠올릴 단어 |
|---|---|
| 실패 시 되돌릴 수 있나? | `commit` / `rollback` |
| 동시에 실행될 때 서로 꼬이나? | 격리 수준 / 락 |

### Q1. `commit`만 하면 동시성 문제도 해결되나요?

아니다. `commit`은 **내 작업을 확정하는 시점**이지, 다른 트랜잭션이 중간에 같은 row를 읽거나 바꾸는 문제까지 자동으로 막아 주지는 않는다.

예를 들어 두 사용자가 재고 1개를 거의 동시에 읽고 둘 다 "아직 1개 남았네"라고 판단할 수 있다. 둘 다 각자 트랜잭션을 잘 `commit`했더라도, 읽는 순간과 쓰는 순간이 겹치면 oversell 문제가 생긴다. 이 지점부터는 atomicity보다 **isolation과 락**을 같이 봐야 한다.

### Q2. 격리 수준은 "`rollback`을 더 강하게 해 주는 옵션"인가요?

아니다. `rollback`은 실패했을 때 **내 변경을 없던 일로 돌리는 기능**이고, 격리 수준은 동시에 실행될 때 **서로의 변경을 언제 볼 수 있는지**를 정한다. 둘은 다른 문제를 다룬다.

입문자는 "`SERIALIZABLE`이면 더 안전하니까 rollback도 더 잘 되겠지"라고 섞어 생각하기 쉽다. 하지만 rollback은 모든 격리 수준에서 가능하고, 격리 수준은 주로 dirty read, non-repeatable read, phantom read 같은 **동시성 간섭**을 줄이는 데 쓰인다.

### Q3. 트랜잭션을 길게 잡으면 격리 수준 문제를 덜 신경 써도 되나요?

오히려 반대인 경우가 많다. 트랜잭션이 길수록 락을 오래 잡거나, 오래된 스냅샷을 붙들고 있게 되어 다른 요청과 더 자주 충돌한다.

즉 "오래 잡으면 안전"이 아니라 **짧고 필요한 SQL만 묶고**, 정말 동시에 꼬이는 구간에서만 격리 수준이나 락 전략을 올바르게 고르는 쪽이 안전하다.

### Q4. 지금 `READ COMMITTED`, `REPEATABLE READ`, `SERIALIZABLE`을 전부 외워야 하나요?

처음부터 표 전체를 암기할 필요는 없다. 먼저 아래 두 줄만 이해하면 된다.

- `READ COMMITTED`: 매번 읽을 때 이미 `commit`된 최신 결과를 본다
- `REPEATABLE READ`: 같은 트랜잭션 안에서 내가 처음 본 값을 다시 읽을 때 덜 흔들리게 잡아 준다

이 두 단계 차이만 잡아도 "왜 트랜잭션 다음에 격리 수준을 배우는지"가 보인다. 그다음에 dirty read, non-repeatable read, phantom read를 [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)에서 연결하면 된다.

## 더 깊이 가려면

- 학습 흐름으로 돌아가려면 [Database README: 빠른 탐색](./README.md#빠른-탐색), [Junior Backend Roadmap: 3단계 데이터베이스 기본기](../../JUNIOR-BACKEND-ROADMAP.md#3단계-데이터베이스-기본기)를 먼저 본다.
- 가장 안전한 다음 한 걸음은 [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)다.
같은 카테고리 다음 단계 문서:

- 동시에 도는 두 트랜잭션이 서로의 변경을 어떻게 보는지 가장 먼저 잡으려면 → [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- 격리 수준과 락을 한 문서에서 더 길게 묶어 보려면 → [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- 격리 수준만으로 막지 못하는 5가지 이상 현상 → [Isolation Anomaly Cheat Sheet](./isolation-anomaly-cheat-sheet.md)
- 실무에서 트랜잭션 경계/락 전략을 어떻게 고르는가 → [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)

cross-category bridge:

- Spring 환경에서 `@Transactional`이 실제로 무엇을 해 주는지는 spring 카테고리 문서를 다음 단계로 볼 것

## 면접/시니어 질문 미리보기

> Q: 트랜잭션이 없으면 어떤 일이 생기나요?
> 의도: atomicity의 필요성을 자기 말로 설명할 수 있는지 확인
> 핵심: 여러 SQL 중 하나만 성공한 "절반 상태"가 남고, 그 상태는 자동으로 복구되지 않는다. 송금/주문/재고 같은 다중 row 작업이 기본적으로 깨진다.

> Q: ACID 중에서 가장 먼저 신경 써야 하는 글자는 무엇인가요?
> 의도: 추상적 정답("다 중요해요")이 아니라 상황별 우선순위를 생각하는지 확인
> 핵심: 정해진 답은 없다. OLTP 입문 단계에서는 atomicity와 durability가 가장 직관적이고, 동시에 도는 사용자가 늘어날수록 isolation이 새로운 문제로 등장한다.

## 한 줄 정리

트랜잭션은 commit/rollback으로 묶인 사건의 단위이고, ACID 4글자는 그 단위가 사고를 만났을 때 어떤 보장을 약속하는지를 atomicity·consistency·isolation·durability 네 각도에서 따로따로 설명한다.
