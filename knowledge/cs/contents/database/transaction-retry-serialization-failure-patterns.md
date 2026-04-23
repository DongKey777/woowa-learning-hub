# Transaction Retry와 Serialization Failure 패턴

> 한 줄 요약: 재시도는 실패를 지우는 장치가 아니라, 같은 실패를 안전하게 다시 만나는 방법을 설계하는 일이다.

**난이도: 🔴 Advanced**

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Deadlock Case Study](./deadlock-case-study.md), [Version Column Retry Walkthrough](./version-column-retry-walkthrough.md), [Spring Retry Proxy Boundary Pitfalls](./spring-retry-proxy-boundary-pitfalls.md), [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md), [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md), [Serializable Retry Telemetry for Set Invariants](./serializable-retry-telemetry-set-invariants.md), [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md)
retrieval-anchor-keywords: serialization failure, transaction retry, deadlock retry, backoff, idempotent retry, sqlstate 40001, sqlstate 40P01, postgresql serializable retry, ssi retry, retry whole transaction, retry budget, serializable observability, optimistic locking retry, retry boundary optimistic lock, spring retry transaction boundary, @retryable @transactional, self invocation retry, requires_new retry pitfall

## 핵심 개념

동시성이 높은 시스템에서는 트랜잭션이 항상 한 번에 성공하지 않는다.  
특히 Serializable 계열이나 강한 제약이 있는 환경에서는 serialization failure, deadlock, lock timeout이 반복된다.

왜 중요한가:

- “한 번만 성공” 가정으로 짠 코드는 실제 운영에서 깨진다
- retry는 넣었는데 중복 부작용 때문에 오히려 더 큰 사고가 난다
- 재시도 정책이 없으면 정상적인 경쟁 상황도 장애처럼 보인다

트랜잭션 retry는 단순 `while(true)`가 아니라, **무엇을 재시도하고 무엇을 재시도하지 않을지**를 나누는 설계다.

## 깊이 들어가기

### 1. 어떤 실패를 재시도해야 하나

대표적으로 재시도 후보는 다음이다.

- serialization failure
- deadlock victim
- transient lock timeout
- connection reset 후 커밋 결과 불명확 상황

반대로 재시도하면 안 되는 경우도 많다.

- 비즈니스 검증 실패
- 유니크 제약 위반
- 이미 처리된 멱등성 요청
- 외부 시스템이 확정적으로 거절한 경우

핵심은 “실패했다”와 “다시 하면 될 것 같다”를 구분하는 것이다.

### 2. retry loop가 위험해지는 지점

retry는 보통 안전해 보이지만, 아래 함정이 있다.

- 같은 입력을 다시 넣어도 부작용이 누적된다
- backoff 없이 즉시 재시도하면 경합이 더 심해진다
- 무한 재시도가 커넥션 풀과 스레드를 잡아먹는다
- 롤백 후에도 애플리케이션 상태가 남아 있으면 다음 시도가 오염된다

즉 retry는 DB 문제가 아니라 **애플리케이션 상태 관리 문제**이기도 하다.

### 3. serialization failure가 자주 생기는 패턴

- 범위 검사 후 업데이트하는 로직
- 여러 row를 읽고 합쳐서 새 값을 쓰는 로직
- 높은 격리수준에서 경쟁이 많은 테이블
- 순서를 보장하려는 배치/정산 job

이런 패턴은 retry가 가능해야 하며, 동시에 side effect를 외부로 밀어내야 한다.

### 4. 재시도 전에 필요한 것

- 트랜잭션 범위를 작게 만든다
- 외부 호출은 트랜잭션 밖으로 뺀다
- 멱등성 키 또는 상태 전이를 준비한다
- jittered exponential backoff를 적용한다

retry는 “더 많이 시도”가 아니라 “덜 깨지게 다시 시도”다.

## 실전 시나리오

### 시나리오 1: 좌석 예약이 간헐적으로 실패

같은 좌석을 여러 요청이 잡으면 하나는 serialization failure나 deadlock victim이 된다.  
이 경우 사용자는 재시도가 필요하고, 서버는 같은 요청을 안전하게 다시 받아야 한다.

### 시나리오 2: 정산 배치가 밤마다 흔들림

다른 job과 row 순서가 뒤엉키면 데드락이 반복된다.  
retry는 필요하지만, row 접근 순서를 통일하지 않으면 재시도만 늘어난다.

### 시나리오 3: 외부 호출 후 DB 커밋이 실패

외부 시스템은 이미 성공했는데 DB가 commit 실패를 반환하면, 무조건 다시 처리하면 중복이 생긴다.  
이때는 멱등성 키와 결과 조회형 retry가 필요하다.

## 코드로 보기

```java
public void withRetry(Runnable txWork) {
    int attempt = 0;
    while (true) {
        try {
            txWork.run();
            return;
        } catch (SerializationFailureException | DeadlockLoserDataAccessException e) {
            if (++attempt >= 5) throw e;
            sleepWithJitter(attempt);
        }
    }
}
```

```sql
-- 재시도 대상이 되는 전형적인 경쟁 상황
START TRANSACTION;
SELECT balance FROM accounts WHERE id = 1 FOR UPDATE;
UPDATE accounts SET balance = balance - 1000 WHERE id = 1;
COMMIT;
```

retry가 안전하려면, 같은 작업을 다시 해도 결과가 한 번만 반영되도록 만들어야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 무제한 즉시 retry | 구현이 쉽다 | 폭주와 중복을 만든다 | 거의 없음 |
| 제한 횟수 retry | 현실적이다 | 최종 실패를 처리해야 한다 | 대부분의 서비스 |
| backoff + jitter | 경합을 줄인다 | 응답 시간이 늘어난다 | 경쟁이 많은 경로 |
| 비재시도 실패 분리 | 장애 해석이 쉽다 | 분류 로직이 필요하다 | 운영 민감 서비스 |

## 꼬리질문

> Q: 모든 트랜잭션 실패를 retry하면 되나요?
> 의도: 재시도 가능한 실패와 불가능한 실패를 구분하는지 확인
> 핵심: 유니크 위반이나 비즈니스 검증 실패는 다시 해도 안 된다

> Q: 왜 backoff와 jitter가 필요한가요?
> 의도: 동시에 재시도하는 폭주를 이해하는지 확인
> 핵심: 즉시 재시도는 경합을 더 키운다

> Q: retry와 멱등성은 왜 같이 다뤄야 하나요?
> 의도: 재시도 시 중복 부작용 문제를 아는지 확인
> 핵심: 다시 시도해도 결과가 한 번만 반영돼야 한다

## 한 줄 정리

Transaction retry는 실패를 무조건 반복하는 게 아니라, 재시도 가능한 오류만 제한적으로 다시 시도하고 멱등성까지 보장하는 패턴이다.
