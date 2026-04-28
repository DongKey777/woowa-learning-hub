# 트랜잭션 기초 (Transaction Basics)

> 한 줄 요약: 트랜잭션은 "여기까지 같이 성공하거나 같이 실패한다"를 정하는 묶음이고, 동시성 충돌 제어와는 먼저 분리해서 봐야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Database First-Step Bridge](./database-first-step-bridge.md)
- [Database README: 빠른 탐색](./README.md#빠른-탐색)
- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- [락 기초](./lock-basics.md)
- [Spring @Transactional 기초](../spring/spring-transactional-basics.md)
- [미션 코드 독해용 DB 체크리스트](./mission-code-reading-db-checklist.md)
- [Isolation Anomaly Cheat Sheet](./isolation-anomaly-cheat-sheet.md)

retrieval-anchor-keywords: transaction basics, acid basics, transaction beginner, commit rollback intro, transaction unit of work, transaction vs isolation, transaction vs jpa, what is transaction, 트랜잭션이 뭐예요, 주문 저장 재고 차감 같이 취소, commit 했는데 두 번 팔렸어요, transactional 이면 jpa 인가요, save 만 보이는데 rollback, rollback only beginner, transaction boundary service

## 먼저 잡을 그림

트랜잭션은 여러 DB 변경을 **하나의 사건처럼 묶는 단위**다. 초보자는 "같이 성공하거나 같이 실패할 범위"로 먼저 이해하면 된다.

```text
주문 저장
  -> 재고 차감
  -> 둘 다 끝나면 commit
  -> 하나라도 실패하면 rollback
```

이 문서의 질문은 하나다. "무엇을 같이 `commit`/`rollback`할까?"  
"두 사용자가 동시에 마지막 재고를 잡으면?"은 다음 단계인 격리 수준과 락 질문이다.

입문 1회차에서는 여기서 멈추는 편이 안전하다. `deadlock`, `savepoint`, `retry` 같은 단어가 먼저 보여도 이 문서에서는 "같이 되돌릴 범위"만 분리하고, 나머지는 관련 문서로 넘긴다.

| 지금 보이는 문제 | 이 문서가 먼저 답하는가? | 왜 그런가 |
|---|---|---|
| 주문 저장과 재고 차감이 같이 취소되어야 한다 | 예 | 실패 단위를 묶는 문제다 |
| `commit`은 했는데 마지막 재고가 두 번 팔렸다 | 아니오 | 동시성 충돌은 격리 수준/락 문제다 |
| `save()`는 보이는데 SQL이 안 보인다 | 아니오 | 접근 기술(JDBC/JPA/MyBatis) 문제다 |

## 10초 구분표

| 지금 들리는 말 | 먼저 볼 축 | 바로 열 문서 |
|---|---|---|
| "주문 저장은 됐는데 결제 기록은 실패했어요" | 트랜잭션 | 이 문서 |
| "`commit`은 했는데 마지막 재고가 두 번 팔렸어요" | 격리 수준 / 락 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |
| "`save()`는 보이는데 SQL은 안 보여요" | 접근 기술 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |

입문 목표는 여기서 끝이다. 실패 범위만 분리되면 1차 이해는 충분하다.

## 30초 구분 카드

처음 트랜잭션 문서를 펴는 이유가 "`@Transactional`은 있는데 왜 아직도 꼬이죠?`"라면, 아래 두 축을 먼저 분리하면 된다.

| 지금 들리는 말 | 먼저 답할 질문 | 바로 볼 문서 |
|---|---|---|
| "주문 저장과 결제 기록이 같이 실패해야 하나?" | 어디까지 같이 rollback할까? | 이 문서 |
| "마지막 재고를 두 요청이 동시에 잡았어요" | 누가 먼저 이기게 설계할까? | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md), [락 기초](./lock-basics.md) |
| "`save()`는 보이는데 SQL은 안 보여요" | 어떤 접근 기술이 SQL을 만들까? | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |

핵심은 "`트랜잭션이 있다`"와 "`동시성 문제가 없다`"를 같은 뜻으로 읽지 않는 것이다.

## ACID를 입문자 기준으로 읽기

트랜잭션을 배우면 ACID가 바로 붙는데, 처음에는 "트랜잭션이 지키려는 약속 4개" 정도로 읽으면 충분하다.

| 글자 | 초보자용 첫 해석 | 주문/예약 예시 |
|---|---|---|
| Atomicity | 전부 성공하거나 전부 실패한다 | 주문 저장은 됐는데 재고 차감이 실패하면 둘 다 취소 |
| Consistency | 정해 둔 규칙을 깨지 않은 상태로 끝나야 한다 | 재고가 음수가 되면 안 됨, 같은 좌석이 두 번 예약되면 안 됨 |
| Isolation | 동시에 실행될 때 서로 이상하게 간섭하지 않게 한다 | 같은 row를 다시 읽었는데 값이 바뀌거나, 마지막 재고를 둘 다 성공시키지 않게 설계 |
| Durability | `commit`된 결과는 살아남아야 한다 | 결제 완료 후 서버가 잠깐 죽어도 결과는 남아야 함 |

여기서 특히 많이 헷갈리는 지점은 `Consistency`와 `Isolation`이다.

- `Consistency`는 "끝났을 때 규칙이 깨지지 않아야 한다"는 뜻으로 먼저 읽는다.
- `Isolation`은 "동시에 실행될 때 서로 무엇을 보게 할까"에 가깝다.

입문자는 아래 한 줄로 끊어 두면 안전하다.

- ACID는 트랜잭션의 약속을 설명한다.
- 마지막 재고 경쟁을 실제로 막는 방법은 다음 단계 문서에서 따로 본다.

## 코드에서 경계 찾기

처음 코드를 읽을 때는 아래 세 군데만 보면 된다.

| 먼저 볼 곳 | 왜 여기서 시작하나 | 초보자용 첫 해석 |
|---|---|---|
| service 메서드의 `@Transactional` | 바깥 경계를 여기서 선언하는 경우가 많다 | 이 메서드 안 DB 작업이 같이 `commit`/`rollback`될 가능성이 높다 |
| 그 메서드가 호출하는 repository/mapper | 실제 DB 변경 위치가 보인다 | SQL 위치와 상관없이 한 묶음으로 처리될 수 있다 |
| 트랜잭션 안의 외부 API/오래 걸리는 로직 | 경계가 너무 길어지는 원인이다 | DB와 무관한 대기는 트랜잭션을 불필요하게 길게 만든다 |

같은 주문 생성 흐름도 질문 축이 다르면 보는 문서가 달라진다.

| 같은 장면 | 트랜잭션이 먼저 답하나? | 지금 더 맞는 문서 |
|---|---|---|
| 주문 row 저장 뒤 결제 row 저장이 실패했다 | 예 | 이 문서 |
| 주문은 `commit`됐는데 마지막 재고가 중복 판매됐다 | 아니오 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |
| `orderRepository.save()`는 보이는데 insert SQL이 안 보인다 | 아니오 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |

짧은 주문 예시로 보면 더 분리하기 쉽다.

```text
@Transactional
createOrder()
  -> 주문 저장
  -> 재고 차감
  -> 결제 이력 저장
```

이 장면에서 "결제 이력 저장에서 예외가 나면 앞의 두 작업도 같이 취소할까?"가 트랜잭션 질문이다.  
"두 사람이 동시에 마지막 재고를 잡으면 누가 이기나?"는 트랜잭션만으로 끝나지 않고, 격리 수준과 락 문서로 넘어가는 질문이다.

주문 생성 코드라면 아래 3줄로 끝낸다.

1. `@Transactional`이 붙은 service 메서드를 찾는다.
2. 그 안에서 같이 실패해야 하는 호출을 적어 본다.
3. 외부 API 호출이 끼어 있으면 꼭 같은 트랜잭션 안에 있어야 하는지 따로 묻는다.

초보자가 특히 자주 섞는 오해도 여기서 한 번 끊어 두면 좋다.

- `@Transactional`이 붙었다고 JPA라는 뜻은 아니다. JDBC나 MyBatis도 같은 트랜잭션 경계 안에 들어갈 수 있다.
- repository 호출이 2개여도 같은 service 메서드 경계라면 "한 트랜잭션"일 수 있다.
- 반대로 repository가 1개여도 마지막 재고 경쟁처럼 동시성 문제가 보이면 이 문서만으로는 끝나지 않는다.
- "트랜잭션이 있으니 중복 판매도 막히겠지"라고 생각하면 흔히 틀린다. 트랜잭션은 실패 범위를 묶고, 동시성 충돌 방지는 별도 설계가 필요하다.

짧게 기억하면 아래 두 줄이면 충분하다.

- 트랜잭션은 "같이 되돌릴 범위"를 정한다.
- "누가 먼저 이기나"는 격리 수준, 락, 제약 조건 문서로 넘긴다.

## 언제 락 이야기까지 가야 하나

초보자가 가장 많이 하는 질문은 "`@Transactional`도 있는데 왜 락이 또 필요해요?"다. 이때는 "실패 범위를 묶는 문제"와 "동시에 같은 자원을 건드리는 문제"를 분리하면 된다.

| 보인 장면 | 트랜잭션만으로 충분한가 | 왜 그런가 |
|---|---|---|
| 주문 row 저장 후 결제 row 저장 중 예외가 났다 | 대체로 예 | 같이 취소할 범위가 핵심이다 |
| 마지막 재고 1개를 두 요청이 동시에 본다 | 아니오 | 둘 다 읽은 뒤 차감하면 중복 성공이 날 수 있다 |
| "이 시간대 예약이 비어 있으면 insert"를 동시에 실행한다 | 아니오 | 특정 row 1개가 아니라 부재/범위 판단이 경쟁한다 |

실무 첫 대응은 아래 순서로 단순화하면 된다.

1. 먼저 "같이 취소할 작업 묶음"이 맞는지 본다.
2. 그다음 "같은 row나 범위를 동시에 읽고 판단하는가"를 본다.
3. 그렇다면 [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)와 [락 기초](./lock-basics.md)로 넘어가 locking read, 제약, 재시도를 같이 검토한다.

## 여기서 멈추는 기준

아래 세 줄이 분리되면 이 문서는 충분히 읽은 것이다.

- 트랜잭션은 "무엇을 같이 `commit`/`rollback`할까"를 정한다.
- 격리 수준과 락은 "동시에 실행될 때 왜 꼬이나"를 다룬다.
- `deadlock`, `savepoint`, `40001 retry`는 입문 본문이 아니라 follow-up 링크로 넘긴다.

| 먼저 보인 단어 | 지금은 왜 넘기나 | 다음 문서 |
|---|---|---|
| `deadlock`, `lock wait` | 이미 충돌 대응 단계다 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md), [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md) |
| `savepoint` | 부분 롤백은 입문 핵심보다 한 단계 뒤다 | [Savepoint Rollback, Lock Retention, and Escalation Edge Cases](./savepoint-lock-retention-edge-cases.md) |
| `40001`, `retry` | 재시도는 격리 수준과 충돌 해석을 같이 봐야 한다 | [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md) |

## 한 줄 정리

트랜잭션은 "실패했을 때 어디까지 같이 되돌릴까"를 정하는 도구이고, 동시성 충돌이나 엔진별 incident 대응은 다음 문서로 넘기는 것이 초보자에게 가장 안전하다.
