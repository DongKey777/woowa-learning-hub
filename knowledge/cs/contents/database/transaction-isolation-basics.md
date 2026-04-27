# 트랜잭션 격리 수준 기초 (Transaction Isolation Level Basics)

> 한 줄 요약: 격리 수준은 동시에 실행되는 트랜잭션끼리 서로의 중간 결과를 얼마나 볼 수 있는지를 결정하는 4단계 설정이다.

**난이도: 🟢 Beginner**

관련 문서:

- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Isolation Anomaly Cheat Sheet](./isolation-anomaly-cheat-sheet.md)
- [database 카테고리 인덱스](./README.md)
- [Spring @Transactional 심화](../spring/transactional-deep-dive.md)

retrieval-anchor-keywords: transaction isolation level basics, isolation level beginner, read committed beginner, repeatable read beginner, serializable beginner, dirty read beginner, 트랜잭션 격리 수준 처음 배우는데, 격리 수준이 뭐예요, read uncommitted 설명, isolation 4단계 입문, transaction isolation basics basics, transaction isolation basics beginner, transaction isolation basics intro, database basics, beginner database

## 핵심 개념

트랜잭션 격리 수준(isolation level)은 **두 트랜잭션이 동시에 실행될 때 서로의 변경 내용이 얼마나 보이는지를 제어하는 설정**이다.

"격리가 강할수록 안전하다"는 말은 맞지만, 격리가 강해질수록 동시 처리량(throughput)은 줄고 락 경합이 늘어난다. 따라서 비즈니스 요구사항에 맞는 수준을 골라야 한다.

입문자가 헷갈리는 지점:

- 격리 수준은 트랜잭션 크기나 길이와 무관하다 — 동시 실행 시 가시성(visibility) 설정이다
- MySQL InnoDB 기본값은 `REPEATABLE READ`, PostgreSQL 기본값은 `READ COMMITTED`다
- 격리 수준이 높다고 해서 데이터가 자동으로 '정확해지는' 것은 아니다

## 한눈에 보기 — 4단계 비교

| 격리 수준 | Dirty Read | Non-Repeatable Read | Phantom Read |
|---|---|---|---|
| READ UNCOMMITTED | 가능 | 가능 | 가능 |
| READ COMMITTED | 불가 | 가능 | 가능 |
| REPEATABLE READ | 불가 | 불가 | 가능(DB에 따라 다름) |
| SERIALIZABLE | 불가 | 불가 | 불가 |

숫자가 올라갈수록 보장은 강해지고 동시성은 낮아진다.

## 상세 분해 — 이상 현상 3가지

각 단계가 막는 이상 현상을 입문 단계에서 이해해야 한다.

- **Dirty Read**: 아직 commit되지 않은 다른 트랜잭션의 변경을 읽는다. 그 트랜잭션이 rollback되면 읽은 데이터가 사라진 데이터가 된다.
- **Non-Repeatable Read**: 같은 트랜잭션 안에서 같은 row를 두 번 읽었을 때 중간에 다른 트랜잭션이 그 row를 `UPDATE`하고 commit하면 두 번째 읽기 결과가 달라진다.
- **Phantom Read**: 같은 트랜잭션 안에서 같은 범위 조건으로 두 번 조회했을 때 중간에 다른 트랜잭션이 `INSERT`/`DELETE`를 하면 결과 행 수가 달라진다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "SERIALIZABLE이면 다 해결된다" | 동시성이 거의 직렬로 떨어져 처리량이 급감한다 | 실제 발생하는 이상 현상만 막는 수준을 고른다 |
| "READ UNCOMMITTED는 쓰면 안 된다" | 통계성 쿼리처럼 다소 부정확해도 빠른 읽기가 필요할 때 의도적으로 사용한다 | 용도를 먼저 정하고 수준을 선택한다 |
| "격리 수준 올리면 데드락이 없어진다" | 격리가 높아지면 락 범위가 넓어져 오히려 데드락 가능성이 커질 수 있다 | 데드락은 격리 수준이 아닌 락 획득 순서 설계로 다룬다 |

## 실무에서 쓰는 모습

가장 흔한 시나리오 둘:

**(1) 일반 웹 서비스 CRUD** — 대부분 `READ COMMITTED` 또는 MySQL 기본값인 `REPEATABLE READ`를 그대로 사용한다. 사용자의 한 번 요청은 하나의 짧은 트랜잭션으로 처리되기 때문에 Non-Repeatable Read가 문제가 되지 않는 경우가 많다.

**(2) 재고 차감·예약 시스템** — 같은 자원을 동시에 여러 사용자가 변경하는 경우 `REPEATABLE READ` + 명시적 락 또는 낙관적 락을 조합한다. 격리 수준만 올리는 것보다 락 전략을 함께 설계하는 것이 더 중요하다.

## 더 깊이 가려면

- 이상 현상 5가지를 더 자세히 보려면 → [Isolation Anomaly Cheat Sheet](./isolation-anomaly-cheat-sheet.md)
- MySQL vs PostgreSQL 격리 수준 구현 차이 → [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)

cross-category bridge:

- Spring `@Transactional(isolation = ...)` 설정 방법과 주의사항 → [Spring @Transactional 심화](../spring/transactional-deep-dive.md)

## 면접/시니어 질문 미리보기

> Q: READ COMMITTED와 REPEATABLE READ의 차이를 설명해 주세요.
> 의도: 이상 현상과 격리 수준의 대응 관계를 말로 표현할 수 있는지 확인
> 핵심: REPEATABLE READ는 같은 트랜잭션 안에서 같은 row를 다시 읽어도 결과가 바뀌지 않음을 보장한다. READ COMMITTED는 매 읽기마다 최신 commit 결과를 반영한다.

> Q: MySQL InnoDB의 기본 격리 수준이 REPEATABLE READ인데 왜 Phantom Read가 잘 발생하지 않나요?
> 의도: MVCC 개념을 아는지 간접 확인
> 핵심: InnoDB는 MVCC 스냅샷 읽기를 사용하므로 일반 `SELECT`에서는 phantom이 보이지 않는다. 단 `SELECT ... FOR UPDATE` 같은 현재 읽기에서는 발생할 수 있다.

## 한 줄 정리

격리 수준은 동시 트랜잭션 간 가시성을 4단계로 제어하며, 높을수록 안전하지만 처리량과 락 경합이 트레이드오프로 따라온다.
