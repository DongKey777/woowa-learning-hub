# Connection Pool, Transaction Propagation, Bulk Write

**난이도: 🔴 Advanced**

> 실무에서 DB가 느려졌을 때, 쿼리보다 먼저 봐야 하는 운영 경계와 쓰기 전략 정리

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md), [JDBC 실전 코드 패턴](./jdbc-code-patterns.md), [HikariCP 튜닝](./hikari-connection-pool-tuning.md), [Spring Retry Proxy Boundary Pitfalls](./spring-retry-proxy-boundary-pitfalls.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)

<details>
<summary>Table of Contents</summary>

- [이 문서 다음에 보면 좋은 문서](#이-문서-다음에-보면-좋은-문서)
- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [Connection Pool](#connection-pool)
- [트랜잭션 경계와 전파](#트랜잭션-경계와-전파)
- [Bulk Write/Update 전략](#bulk-writeupdate-전략)
- [운영에서 자주 터지는 조합](#운영에서-자주-터지는-조합)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

retrieval-anchor-keywords: connection pool starvation, transaction propagation, transaction boundary, bulk write strategy, external call in transaction, long transaction, connection pool exhaustion, required propagation, bulk update batching, transaction scope too wide, spring transaction propagation, @transactional propagation, required vs requires_new, jdbc transaction boundary, jdbc connection leak, jpa long transaction, entitymanager transaction, hibernate flush timing, open session in view, hikaricp pool exhausted, hikaricp connection timeout, bulk insert jpa, batch insert jdbc, connection lifecycle, jdbc connection lifecycle, connection borrow return, connection checkout checkin, getConnection close pattern, close returns to pool, auto commit false, autoCommit false, setAutoCommit false, manual commit rollback, commit timing, rollback timing, batch chunk commit, connection held too long, requires_new pool starvation, retry plus requires_new, self invocation requires_new ignored, unexpectedrollbackexception propagation

## 이 문서 다음에 보면 좋은 문서

- dirty read, phantom read, `SELECT ... FOR UPDATE`, optimistic/pessimistic lock 판단이 먼저면 [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)으로 먼저 올라간다.
- `JDBC`, `JPA`, `Hibernate`, `MyBatis`, `EntityManager`, `dirty checking`, `flush` 같은 접근 기술 용어가 먼저 헷갈리면 [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md)로 기본 축을 맞춘다.
- raw JDBC에서 `setAutoCommit(false)`, `commit()`, `rollback()`, `executeBatch()` 코드 모양부터 확인하려면 [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)을 같이 열어 두는 편이 빠르다.
- `maximumPoolSize`, timeout, leak detection, pool sizing 같은 Hikari 설정값 질문이면 [HikariCP 튜닝](./hikari-connection-pool-tuning.md)으로 바로 이어진다.
- `@Retryable`, self-invocation, outer transaction, `REQUIRES_NEW`가 서로 엮이면서 경계가 헷갈리면 [Spring Retry Proxy Boundary Pitfalls](./spring-retry-proxy-boundary-pitfalls.md)로 바로 내려간다.

## 왜 이 문서가 필요한가

DB 성능 문제는 종종 느린 쿼리 하나가 아니라,

- 커넥션을 오래 점유하는 코드
- 트랜잭션 범위가 넓은 설계
- 대량 쓰기를 한 번에 처리하려는 시도

에서 시작된다.

즉 병목은 SQL 문장보다 **요청의 생명주기 전체**에 있을 수 있다. 이 문서는 그 경계를 보는 문서다.
JDBC에서 `Connection`을 언제 얻고 언제 `commit/rollback`하는지로 보이든, Spring/JPA에서 `@Transactional`, propagation, `EntityManager flush`로 보이든 핵심은 같다. 언제 커넥션을 점유하고 얼마나 오래 잡는지가 운영 병목을 만든다.

---

## Connection Pool

Connection Pool은 **DB 연결을 매번 새로 만들지 않고 재사용하기 위한 연결 보관소**다.

DB 연결 생성은 비싸다.

- TCP 연결
- 인증
- 세션 초기화

가 들어가기 때문이다.

### 핵심 감각

- 풀 크기가 커지면 동시 처리량이 늘어날 것 같지만, 항상 그렇지 않다
- 커넥션은 유한한 자원이라서, 잡고 있는 시간이 길어지면 대기열이 생긴다
- DB가 느린 게 아니라, 커넥션을 오래 물고 있는 코드가 느린 경우가 많다

### 흔한 실수

- 요청 전체를 하나의 트랜잭션으로 묶는다
- 외부 API 호출을 트랜잭션 안에서 수행한다
- 배치 작업이 커넥션을 점유한 채 오래 돈다
- 로그 출력이나 파일 처리까지 커넥션을 잡고 있다

### 체크 포인트

- 커넥션 획득 시점이 너무 빠르지 않은가
- 커밋/롤백이 너무 늦지 않은가
- 커넥션 풀 고갈 시 대기 시간이 폭증하지 않는가
- CPU가 아니라 대기 상태가 병목인지 확인했는가

핵심은 단순하다. **짧게 잡고, 빨리 반환해야 한다.**

### JDBC connection lifecycle로 보면 더 명확하다

pool 환경에서 흔히 보는 lifecycle은 아래 한 줄로 요약된다.

1. `getConnection()`으로 pool에서 빌린다
2. 필요하면 `setAutoCommit(false)`로 transaction 경계를 수동으로 연다
3. SQL을 실행한다
4. 성공이면 `commit()`, 실패면 `rollback()`
5. `close()`로 물리 종료가 아니라 pool에 반환한다

즉 `close()`를 늦게 부르는 문제는 곧 pool 반환을 늦게 하는 문제다.
이 흐름의 코드 예시는 [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)에 있고, lock/isolation 판단은 [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)으로 이어진다.

---

## 트랜잭션 경계와 전파

트랜잭션 경계는 **어디부터 어디까지를 하나의 원자적 작업으로 볼 것인가**의 문제다.

전파(propagation)는 주로 스프링 같은 프레임워크에서,

- 이미 트랜잭션이 있으면 합류할지
- 새로 만들지
- 아예 참여하지 않을지

를 정하는 규칙이다.
JDBC에서는 `Connection` 획득 시점과 `autoCommit=false`, `commit/rollback`이 경계를 드러내고, Spring/JPA에서는 `@Transactional`, `REQUIRED`, `REQUIRES_NEW`, `EntityManager`가 그 경계를 감싸서 보여준다.

### 실무에서 중요한 이유

전파 설정을 잘못 이해하면,

- 생각보다 큰 트랜잭션이 생기거나
- 반대로 꼭 같이 커밋돼야 할 작업이 분리될 수 있다

### 대표적인 판단

- 같은 정합성 단위면 한 트랜잭션으로 묶는다
- 외부 I/O는 가능하면 트랜잭션 밖으로 뺀다
- 읽기 전용 쿼리는 별도 범위로 분리한다
- 재시도 가능한 작업과 불가능한 작업을 섞지 않는다

### 흔한 함정

- `REQUIRED`가 너무 넓은 범위를 덮는다
- 내부 메서드가 새 트랜잭션인 줄 알았는데 기존 트랜잭션에 합류한다
- 롤백되면 안 되는 외부 호출이 이미 실행됐다
- 예외를 잡아먹어서 롤백이 안 된다
- `autoCommit=false`로 열어 둔 connection을 오래 쥔 채 외부 호출이나 대량 loop를 태운다

### 면접에서 자주 받는 질문 포인트

- “왜 트랜잭션을 짧게 가져가야 하나요?”
- “전파 옵션을 잘못 쓰면 어떤 버그가 나나요?”
- “읽기와 쓰기를 같은 트랜잭션에 둘 이유가 있나요?”

---

## Bulk Write/Update 전략

대량 쓰기는 보통 느린 작업이 아니라, **한 번에 너무 많이 하려는 작업**에서 망가진다.

### 기본 전략

- 단건 반복보다 batch 처리로 왕복 비용을 줄인다
- 너무 큰 배치는 적당한 크기로 쪼갠다
- 실패 복구를 위해 chunk 단위를 정한다
- update는 가능하면 set-based 방식으로 처리한다

### Batch insert

여러 row를 한 번에 넣는 방식이다.

장점:

- 네트워크 왕복이 줄어든다
- statement 실행 오버헤드가 줄어든다

단점:

- 실패 시 범위가 커진다
- 한 트랜잭션이 길어질 수 있다
- 락과 undo/redo 부담이 커질 수 있다
- 한 번의 `executeBatch()` 뒤에 `commit()`이 늦어지면 connection lifecycle 전체가 길어진다

### Batch update

update는 row를 하나씩 반복하는 것보다, 조건이 맞으면 한 번에 갱신하는 편이 낫다.

예:

- 상태값 일괄 변경
- 기간 기준 비활성화
- 누적 값 정산

주의할 점:

- 조건이 너무 넓으면 대량 락이 걸린다
- 인덱스를 못 타면 오히려 더 느려질 수 있다
- row별 검증이 필요한 로직은 단일 SQL로 끝나지 않을 수 있다

### 판단 기준

- 같은 SQL을 반복하는가
- 실패 시 어느 단위까지 되돌릴 것인가
- 재시도해도 안전한가
- 운영 중 락 경합을 감당할 수 있는가

대량 처리는 보통 “최대 성능”보다 “복구 가능성”이 더 중요하다.
문법 자체가 필요하면 [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)의 `batch insert` 예제를 보고, batch가 pool과 transaction boundary에 미치는 영향은 여기 문서에서 이어 본다.

---

## 운영에서 자주 터지는 조합

### 1. 긴 트랜잭션 + connection pool 고갈

가장 흔한 문제다.

증상:

- 응답 시간이 전반적으로 느려짐
- DB CPU는 낮은데 요청이 밀림
- 새 요청이 커넥션을 못 얻음

원인:

- 트랜잭션 안에서 오래 기다림
- 외부 시스템 호출을 끼워 넣음

### 2. 큰 배치 + 하나의 커밋

증상:

- 롤백 비용이 커짐
- 장애 시 재처리가 어려움
- 락과 로그가 과하게 쌓임

### 3. 전파 오해 + 정합성 버그

증상:

- 일부 데이터만 커밋됨
- 내부 호출이 새 트랜잭션이라고 착각함
- 예외 처리 후에도 커밋이 진행됨

### 4. 읽기 분리와 쓰기 분리의 혼동

읽기와 쓰기를 분리하면 부하 분산은 쉬워지지만, 정합성은 자동으로 따라오지 않는다.

이 부분은 별도 문서에서 더 자세히 다룰 가치가 있다.

---

## 시니어 관점 질문

- 이 병목은 쿼리 문제인가, 커넥션 점유 문제인가?
- 트랜잭션을 줄였을 때 정합성이 깨지지 않는가?
- bulk 작업을 chunk로 나눌 때 실패 복구는 어떻게 하는가?
- 전파 설정을 바꾸면 커밋 경계가 어떻게 바뀌는가?
- 단건 API를 배치로 바꿨을 때 운영 난이도는 얼마나 올라가는가?
