# 락 기초 (Database Lock Basics)

> 한 줄 요약: 데이터베이스 락은 동시에 실행되는 트랜잭션이 같은 데이터를 충돌 없이 변경할 수 있도록 순서를 강제하는 메커니즘이다.

**난이도: 🟢 Beginner**

관련 문서:

- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Deadlock Case Study](./deadlock-case-study.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [database 카테고리 인덱스](./README.md)
- [Spring @Transactional 심화](../spring/transactional-deep-dive.md)

retrieval-anchor-keywords: database lock basics, 락 기초, shared lock exclusive lock 처음 배우는데, 낙관적 락 비관적 락 차이, optimistic pessimistic lock 입문, 락이 뭐예요, 데드락 기초, deadlock what is, deadlock 처음, deadlock이 뭐예요, lock wait 왜 생겨요, lock timeout 처음, row lock table lock 입문, 잠금 기초, lock basics beginner

## 핵심 개념

**락(lock)** 은 트랜잭션이 데이터를 읽거나 쓸 때 다른 트랜잭션이 동시에 간섭하지 못하도록 잠그는 장치다. 아무도 락을 걸지 않으면 두 트랜잭션이 같은 계좌 잔액을 동시에 읽어 각자 10원을 차감하고 commit하는 "갱신 손실(lost update)" 문제가 생긴다.

입문자가 자주 혼동하는 지점:

- 락은 DB 서버가 내부적으로 관리하는 것이지만, 개발자가 `SELECT ... FOR UPDATE`처럼 명시적으로 요청할 수도 있다
- 락이 길어지면 다른 트랜잭션이 대기하고, 두 트랜잭션이 서로 상대의 락을 기다리면 **데드락(deadlock)** 이 발생한다
- 격리 수준이 높아질수록 DB가 내부적으로 더 많은 락을 자동으로 건다

## 한눈에 보기 — 락 종류

| 종류 | 설명 | 언제 걸리나 |
|---|---|---|
| 공유 락 (S Lock, Shared) | 읽기용. 여러 트랜잭션이 동시에 가질 수 있다 | `SELECT ... LOCK IN SHARE MODE` 또는 SERIALIZABLE 읽기 |
| 배타 락 (X Lock, Exclusive) | 쓰기용. 하나의 트랜잭션만 가질 수 있다 | `UPDATE`, `DELETE`, `SELECT ... FOR UPDATE` |
| 행 락 (Row Lock) | 특정 행 하나를 잠금 | InnoDB 기본값 — 인덱스 기반 |
| 테이블 락 (Table Lock) | 테이블 전체를 잠금 | DDL, MyISAM 등 |

## 상세 분해

**비관적 락 vs 낙관적 락** — 입문에서 가장 많이 혼동하는 개념이다.

- **비관적 락(pessimistic lock)**: "충돌이 자주 난다"고 가정하고 데이터를 읽는 순간부터 락을 건다. `SELECT ... FOR UPDATE`가 대표적이다. 락을 잡고 있는 동안 다른 트랜잭션은 대기해야 한다.
- **낙관적 락(optimistic lock)**: "충돌이 드물다"고 가정하고 락 없이 읽은 뒤, 쓸 때 버전 번호(`version` 컬럼)를 비교한다. 버전이 다르면 충돌로 판단해 예외를 던지고 재시도한다. JPA `@Version`이 이 방식이다.

비관적 락은 대기가 발생하지만 충돌을 즉시 막는다. 낙관적 락은 대기가 없지만 충돌 시 재시도 비용이 든다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "락은 자동으로 걸리니 신경 안 써도 된다" | DB가 자동 락을 걸더라도 범위와 시간을 개발자가 제어하지 않으면 데드락·타임아웃이 발생한다 | 락이 어느 범위에 어떤 기간 동안 걸리는지 의식적으로 설계한다 |
| "낙관적 락이 항상 더 빠르다" | 충돌이 잦은 상황에서는 재시도 비용이 쌓여 오히려 더 느리다 | 충돌 빈도를 먼저 예측하고 방식을 고른다 |
| "테이블 락을 걸면 행 락보다 안전하다" | 테이블 전체가 잠기면 해당 테이블에 접근하는 모든 트랜잭션이 대기해 처리량이 급감한다 | InnoDB 행 락으로 최소 범위를 잡고, 테이블 락은 DDL 등 부득이한 경우로 제한한다 |

## incident로 넘어가는 3단계 라우트

초보자는 `deadlock`, `lock wait timeout`, `FOR UPDATE` 같은 단어가 먼저 보여도 바로 운영 playbook으로 내려가기보다, 아래 3단계로 문서를 밟으면 "락 기초"와 "실제 incident 대응"이 덜 끊긴다.

| 단계 | 여기서 답할 질문 | 먼저 잡을 한 줄 | 다음 이동 |
|---|---|---|---|
| 1. primer | "락이 뭐예요? 왜 기다려요?" | 락은 같은 데이터를 동시에 바꾸지 못하게 순서를 세우는 장치다 | 이 문서에서 shared/exclusive, pessimistic/optimistic 차이를 먼저 정리한다 |
| 2. symptom bridge | "`deadlock`인지 `lock wait timeout`인지 어떻게 읽어요?" | `deadlock`은 순환 대기이고 `lock wait timeout`은 오래 기다렸다는 신호다 | deadlock이면 [Deadlock Case Study](./deadlock-case-study.md), timeout이면 3단계로 바로 간다 |
| 3. incident playbook | "지금 운영에서 무엇부터 확인하죠?" | 이제는 개념보다 blocker, wait graph, metadata lock 분류가 우선이다 | [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md) |

증상 단어별 빠른 갈림길도 같이 기억하면 좋다.

| 먼저 보인 단어 | 1문장 번역 | 바로 열 문서 |
|---|---|---|
| `deadlock` | 서로가 가진 락을 반대 순서로 기다리는 순환 대기다 | [Deadlock Case Study](./deadlock-case-study.md) |
| `lock wait timeout` | 락 줄에서 너무 오래 기다렸다는 뜻이지, 이미 중복 성공했다는 뜻은 아니다 | [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md) |
| `FOR UPDATE` | 그냥 읽기와 달리 읽으면서 경쟁 자원을 잡는 locking read다 | [트랜잭션 격리수준과 락](./transaction-isolation-locking.md) |

## 실무에서 쓰는 모습

**(1) 재고 차감** — 동시에 여러 사용자가 재고를 차감하는 경우 `SELECT ... FOR UPDATE`로 해당 row에 배타 락을 건 뒤 재고 값을 확인하고 차감한다. 락을 잡기 때문에 하나씩 직렬 처리된다.

**(2) 낙관적 락 + JPA** — 수정이 드문 프로필 정보 수정 등에서 `@Version` 컬럼을 두고 충돌 시 `OptimisticLockingFailureException`을 catch해 재시도하거나 사용자에게 재시도를 안내한다.

## 여기서 멈추는 기준

입문 1회차에서는 아래만 분리되면 충분하다.

- plain `SELECT`와 locking read는 역할이 다르다.
- 비관적 락은 기다리게 하고, 낙관적 락은 충돌 시 실패시키고 다시 판단한다.
- deadlock, timeout, gap lock은 "락이 있다" 다음 단계의 심화 주제지만, `deadlock = 서로 반대 순서로 기다리는 순환 대기` 정도는 먼저 잡고 넘어가면 follow-up이 훨씬 덜 헷갈린다.

## 더 깊이 가려면

- 격리 수준과 락의 관계, 갭 락·넥스트 키 락 → [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- 실제 데드락 발생 패턴과 해결책은 2단계 follow-up으로 → [Deadlock Case Study](./deadlock-case-study.md)
- deadlock/lock timeout incident에서 blocker 분류가 바로 필요하면 3단계 playbook으로 → [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)

cross-category bridge:

- JPA `@Version`과 `@Transactional`에서 낙관적 락이 어떻게 동작하는지 → [Spring @Transactional 심화](../spring/transactional-deep-dive.md)

## 한 줄 정리

락은 동시 트랜잭션의 충돌을 막는 순서 강제 메커니즘이며, 공유/배타 락과 비관적/낙관적 접근 중 충돌 빈도와 비용에 맞는 방식을 골라야 한다.
