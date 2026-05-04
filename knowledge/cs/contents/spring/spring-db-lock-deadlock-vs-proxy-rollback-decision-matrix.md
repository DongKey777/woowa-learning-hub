---
schema_version: 3
title: DB Lock Wait / Deadlock vs Spring Proxy / Rollback 빠른 분기표
concept_id: spring/spring-db-lock-deadlock-vs-proxy-rollback-decision-matrix
canonical: false
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
aliases:
- db lock vs spring proxy
- deadlock vs self invocation
- lock timeout vs transactional not applied
- rollback not working vs lock wait
- spring db lock decision matrix
intents:
- comparison
- design
linked_paths:
- contents/database/deadlock-vs-lock-wait-timeout-primer.md
- contents/database/spring-jpa-lock-timeout-deadlock-exception-mapping.md
- contents/spring/spring-transactional-basics.md
- contents/spring/spring-self-invocation-transactional-only-misconception-primer.md
- contents/spring/spring-transaction-propagation-required-requires-new-rollbackonly-primer.md
confusable_with:
- database/lock-wait-deadlock-latch-triage-playbook
- spring/self-invocation-proxy-misconception
expected_queries:
- lock wait랑 @Transactional proxy 문제를 어떻게 먼저 구분해?
- deadlock인지 self-invocation인지 헷갈릴 때 어떤 분기표를 봐?
- rollback이 안 된 것처럼 보이는데 DB lock 문제인지 Spring 문제인지 모르겠어
- CannotAcquireLockException과 rollback-only가 같이 보이면 어디서 시작해?
contextual_chunk_prefix: |
  이 문서는 트랜잭션이 안 풀리거나 lock timeout이 떨어졌을 때 학습자가
  "DB가 진짜 락을 걸어 막힌 건지, Spring proxy/AOP가 트랜잭션을 안 열어줬는지,
  또는 @Transactional 표시가 잘못 붙어 안 풀린 건지" 헷갈리는 상황을
  먼저 가르는 분기표 chooser다. DB lock vs Spring proxy, deadlock vs
  self-invocation, lock wait vs transactional not applied, rollback이 안 됨
  vs lock 잡힘 같은 자연어 표현이 본 문서의 분기 갈래에 매핑된다.
---

# DB Lock Wait / Deadlock vs Spring Proxy / Rollback 빠른 분기표

> 한 줄 요약: `lock wait`, `deadlock`, `왜 @Transactional이 안 먹지`, `왜 안 롤백되지`가 한 문장에 섞여도 먼저 "DB가 실제로 기다리고 있나"와 "Spring 프록시/롤백 규칙이 깨졌나"를 분리하면 잘못된 branch로 깊게 들어가는 일을 줄일 수 있다.
>
> 문서 역할: 이 문서는 database와 spring 경계에서 자주 섞이는 transaction 증상을 **beginner troubleshooting note**로 먼저 가르는 compact bridge다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Database to Spring Transaction Master Note](../../master-notes/database-to-spring-transaction-master-note.md)
> - [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)
> - [Lock Wait, Deadlock, and Latch Contention Triage Playbook](../database/lock-wait-deadlock-latch-triage-playbook.md)
> - [Deadlock Case Study](../database/deadlock-case-study.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
> - [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
> - [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)

retrieval-anchor-keywords: lock wait vs rollback, deadlock vs self invocation, db lock wait vs spring proxy, deadlock vs rollback-only, lock timeout vs transactional not applied, deadlock vs unexpectedrollbackexception, why transactional not applied vs deadlock, rollback not working vs lock wait, transaction marked rollback-only vs lock wait, self invocation vs deadlock, checked exception commit vs deadlock, lock wait timeout exceeded, deadlock found when trying to get lock, blocker waiter victim evidence, spring db lock deadlock vs proxy rollback decision matrix basics

## 핵심 개념

초보자가 가장 먼저 버려야 할 착각은 이것이다.

- `@Transactional`이 보이니까 문제도 Spring annotation일 것이다
- rollback이 이상하니까 DB deadlock도 그 연장선일 것이다

둘은 자주 같은 transaction 문맥에서 나타나지만, **실패가 surface되는 층이 다르다**.

- DB lock/deadlock branch: DB가 실제로 row/range/schema lock을 기다리거나 순환 대기를 감지했다
- Spring proxy/rollback branch: 프록시 경계, 전파, rollback 규칙, rollback-only marker 해석이 어긋났다

즉 첫 질문은 "`@Transactional`이 있나?"가 아니라 아래 둘이다.

1. **DB가 실제 blocker / waiter / victim을 보여 주나**
2. **Spring이 transaction 시작/전파/rollback 의미를 기대와 다르게 처리했나**

---

## 2분 triage 체크리스트

장애 초반엔 아래 4줄만 확인해도 branch 오판을 많이 줄일 수 있다.

1. 에러 로그에 `deadlock`/`lock wait timeout`/wait graph 출력이 있는가
2. 반대로 `UnexpectedRollbackException`/`transaction marked rollback-only`가 먼저 뜨는가
3. 같은 클래스 내부 호출(`self-invocation`)이나 `private` `@Transactional` 경로가 있는가
4. 트랜잭션 안에서 외부 API/원격 호출을 오래 잡고 있지는 않은가

| 체크 결과 | 첫 분기 |
|---|---|
| 1번이 명확히 예 | DB lock/deadlock branch |
| 2~3번이 먼저 예 | Spring proxy/rollback branch |
| 1번과 4번이 함께 예 | DB 현상 + Spring boundary 동시 점검 |

---

## 먼저 이 표로 갈라 본다

| 먼저 보이는 신호 | 우선 branch | 왜 이쪽에서 시작하나 | 지금 시작하지 말 것 |
|---|---|---|---|
| `Lock wait timeout exceeded`, `deadlock found`, `could not serialize`, DB 세션 wait graph, blocker pid/tx id가 보인다 | DB lock/deadlock | 실제 wait나 victim이 DB에서 관측된다 | self-invocation부터 파고들기 |
| 특정 요청이 오래 멈추고, DB CPU는 높지 않은데 waiter가 늘어난다 | DB lock/deadlock | 느린 계산보다 lock 대기일 가능성이 크다 | `rollbackFor` 설명부터 읽기 |
| `UnexpectedRollbackException`, `transaction marked rollback-only`, `checked exception인데 커밋`, `왜 안 롤백되지`가 먼저 보인다 | Spring proxy/rollback | commit 직전 rollback 의미가 어긋난 문제다 | deadlock case study부터 읽기 |
| `private method`, `same class call`, `self invocation`, `new`로 만든 객체에서 `@Transactional`이 안 먹는다 | Spring proxy/rollback | DB wait가 아니라 proxy boundary 누락 문제다 | lock wait timeout 문서부터 읽기 |
| `audit는 남고 본 작업은 롤백`, `REQUIRES_NEW` 때문에 일부만 커밋 | Spring proxy/rollback | commit boundary 분리 문제다 | deadlock graph 해석부터 읽기 |
| 외부 API를 transaction 안에서 호출한 뒤 concurrency에서 lock wait가 같이 늘어난다 | 혼합: Spring boundary -> DB lock | Spring이 transaction을 길게 열어 DB lock 시간을 키웠을 수 있다 | 한쪽만 원인이라고 단정하기 |

표를 한 줄로 줄이면 이렇다.

```text
실제 DB wait 증거가 있으면 DB branch, commit 의미/프록시 경계 착시가 먼저면 Spring branch
```

---

## 로그 한 줄로 branch 잡는 예시

| 증상 문장 | 1차 분기 |
|---|---|
| `Deadlock found when trying to get lock; try restarting transaction` | DB lock/deadlock부터 시작 |
| `org.springframework.transaction.UnexpectedRollbackException: Transaction silently rolled back because it has been marked as rollback-only` | Spring proxy/rollback부터 시작 |

초반에는 "누가 맞는지 토론"보다, 로그 한 줄로 첫 branch를 정해 시간을 아끼는 게 낫다.

---

## 1. DB lock / deadlock branch로 가야 하는 신호

아래 표현이 보이면 우선 DB 쪽으로 간다.

- `lock wait timeout`
- `deadlock`
- blocker / waiter / victim
- `SELECT ... FOR UPDATE` 이후 대기
- 같은 row를 잡는 요청이 몰릴 때만 p99 급증
- `SHOW ENGINE INNODB STATUS`, `pg_locks`, wait graph에서 실제 충돌이 보임

이 branch의 핵심 질문은 아래다.

1. 누가 누구를 막고 있나
2. 단순 대기인가, 순환 대기인가
3. row lock인가, range/gap lock인가, metadata lock인가
4. 긴 transaction이 lock hold time을 키우고 있나

여기서 중요한 점은 `@Transactional`이 붙어 있어도, **deadlock 자체는 DB concurrency contract의 현상**이라는 것이다.
annotation이 있다고 해서 문제를 Spring proxy로 읽으면 분기가 늦어진다.

먼저 볼 문서:

- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](../database/lock-wait-deadlock-latch-triage-playbook.md)
- [Deadlock Case Study](../database/deadlock-case-study.md)
- [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)

---

## 2. Spring proxy / rollback branch로 가야 하는 신호

아래 표현이 먼저 보이면 Spring 쪽으로 간다.

- `@Transactional`이 안 먹는다
- same-class call / self-invocation
- `private method`에서는 안 된다
- `UnexpectedRollbackException`
- `transaction marked rollback-only`
- `checked exception`인데 커밋된다
- 안쪽에서 예외를 catch했는데 마지막 commit에서 갑자기 실패한다

이 branch의 핵심 질문은 아래다.

1. 호출이 실제 프록시를 통과했나
2. 안쪽 메서드가 같은 transaction에 참여했나
3. rollback 규칙이 runtime exception 중심이라 기대와 어긋난 것은 아닌가
4. rollback-only가 찍힌 뒤 바깥에서 성공처럼 계속 진행한 것은 아닌가

여기서 중요한 점은 `rollback이 이상하다`가 곧 `DB lock 문제`를 뜻하지 않는다는 것이다.
대부분은 wait graph가 아니라 **호출 경로와 rollback 규칙**을 먼저 봐야 한다.

먼저 볼 문서:

- [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
- [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
- [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)

---

## 3. 둘이 진짜로 만나는 회색 지대

둘 중 하나만 보는 것도 틀릴 수 있다.
실무에서는 아래처럼 이어진다.

### 경우 1: Spring boundary가 DB lock 문제를 키운다

예:

- service method 안에서 외부 API 호출
- transaction이 필요 이상으로 길다
- 그동안 row lock을 오래 잡는다
- 결국 다른 요청들이 lock wait나 deadlock으로 터진다

이 경우 시작은 DB incident처럼 보이지만, 재발 방지는 [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)까지 올라가야 한다.

### 경우 2: lock wait는 없는데 개발자가 계속 DB를 의심한다

예:

- 실제 에러는 `UnexpectedRollbackException`
- 내부 catch 이후 rollback-only가 찍혀 있었다
- 또는 self-invocation이라 transaction 자체가 안 열렸다

이 경우 DB branch를 오래 보면 시간이 낭비된다.
wait graph가 없다면 Spring branch를 먼저 끝내는 편이 빠르다.

### 경우 3: 둘 다 보이면 이 질문 하나로 먼저 가른다

```text
DB가 blocker / waiter / victim을 실제로 보여 주는가?
```

- 예: DB branch부터
- 아니오: Spring proxy/rollback branch부터

---

## 자주 섞이는 오해 3가지

- `deadlock`이 한 번 떴다고 모든 rollback 이슈를 DB로 몰아가면 안 된다. 이후 증상은 rollback-only chain일 수 있다.
- `@Transactional`이 붙어 있어도 DB wait 증거가 없으면 프록시 경계 문제가 먼저일 가능성이 크다.
- DB wait 증거가 있어도 원인이 항상 SQL 튜닝만은 아니다. 긴 트랜잭션 경계가 lock hold time을 키웠을 수 있다.

---

## 빠른 읽기 순서

### A. `lock wait`, `deadlock`가 먼저다

1. [Lock Wait, Deadlock, and Latch Contention Triage Playbook](../database/lock-wait-deadlock-latch-triage-playbook.md)
2. [Deadlock Case Study](../database/deadlock-case-study.md)
3. [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)
4. 필요하면 [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)

### B. `왜 안 롤백되지`, `왜 @Transactional이 안 먹지`가 먼저다

1. [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
2. [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
3. [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
4. 필요하면 [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)

### C. `lock wait`와 `rollback-only`가 같이 나온다

1. [Database to Spring Transaction Master Note](../../master-notes/database-to-spring-transaction-master-note.md)
2. 이 문서의 표로 branch 선택
3. 선택한 branch의 playbook/deep dive로 이동

---

## 꼬리질문

> Q: `@Transactional`이 붙어 있는데 deadlock이 나면 Spring 문제인가요?
> 의도: DB concurrency 현상과 framework boundary를 분리하는지 확인
> 핵심: deadlock 자체는 DB wait/lock ordering 문제로 먼저 읽고, Spring은 hold time을 키웠는지 보조로 본다.

> Q: `UnexpectedRollbackException`이 나면 deadlock부터 봐야 하나요?
> 의도: rollback-only surface와 DB wait를 구분하는지 확인
> 핵심: 보통은 rollback-only marker와 commit 의미를 먼저 본다.

> Q: 둘 다 섞여 보이면 가장 먼저 무엇을 확인하나요?
> 의도: 초반 분기 기준 확인
> 핵심: 실제 blocker/waiter/victim 같은 DB wait 증거가 있는지 본다.

> Q: 외부 API를 transaction 안에 둔 뒤 lock wait가 늘어나면 어느 쪽 문제인가요?
> 의도: 회색 지대 처리 확인
> 핵심: 시작은 DB lock symptom이지만, 근본 원인은 Spring/service boundary 설계일 수 있다.

---

## 한 줄 정리

`deadlock`과 `rollback`은 같은 transaction 문맥에 있어도, **실제 DB wait 증거가 있으면 DB branch부터, 프록시/rollback 의미 착시가 먼저면 Spring branch부터** 보는 편이 빠르다.
