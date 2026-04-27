# Idempotent Transaction Retry Envelopes

> 한 줄 요약: retry는 반복 실행이 아니라, 같은 작업을 안전하게 다시 시도할 수 있게 감싸는 envelope 설계다.

**난이도: 🔴 Advanced**

관련 문서: [Spring Retry Envelope 위치 Primer](./spring-retry-envelope-placement-primer.md), [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md), [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md), [Exactly-Once 신화와 DB + Queue 경계](./exactly-once-myths-db-queue.md)
retrieval-anchor-keywords: retry envelope, idempotent retry, exception classifier, backoff policy, attempt budget, spring retry envelope placement, retry outside transaction

## 핵심 개념

Idempotent transaction retry envelope는 트랜잭션 실행을 한 겹 더 감싸서, 재시도 가능한 실패와 불가능한 실패를 구분하고, 같은 작업이 여러 번 실행돼도 최종 결과가 한 번만 반영되게 만드는 구조다.

왜 중요한가:

- serialization failure와 deadlock은 정상적인 경쟁 결과일 수 있다
- 하지만 무차별 retry는 중복 결제, 중복 예약, 중복 메시지를 만든다
- retry는 DB 문제가 아니라 애플리케이션 계약 문제이기도 하다

envelope의 핵심은 “다시 해도 되는가”를 판단하고, 다시 해도 안전하도록 side effect 경계를 조정하는 것이다.

## 깊이 들어가기

### 1. retry envelope가 필요한 이유

단순히 `catch -> retry`를 넣으면 끝날 것 같지만 실제로는 그렇지 않다.

- 일부 예외는 재시도하면 안 된다
- 일부 작업은 재시도 전에 멱등성을 확보해야 한다
- 일부 실패는 한 번 더 해도 같은 결과를 보장하지 않는다

그래서 envelope는 트랜잭션 실행 자체보다 **실패 분류와 재진입 안전성**에 집중한다.

### 2. envelope에 들어가야 하는 것

- 최대 시도 횟수
- 예외 분류기
- exponential backoff + jitter
- idempotency key 또는 business key
- success 이후 결과 저장 방식
- retry 로그와 관측 메타데이터

즉 envelope는 단순 루프가 아니라, **재시도 정책과 중복 방지 정책을 함께 묶는 실행 단위**다.

### 3. side effect 분리

retry 가능한 트랜잭션 안에 외부 호출이 들어가면 위험하다.

- DB는 롤백됐는데 외부 결제는 이미 성공할 수 있다
- 메시지는 나갔는데 트랜잭션은 실패할 수 있다
- retry가 외부 side effect를 두 번 일으킬 수 있다

그래서 envelope 바깥 또는 outbox 같은 구조로 side effect를 분리해야 한다.

### 4. 실패를 상태로 남겨야 한다

retry가 끝까지 실패하면 그냥 throw만 하면 안 된다.

- 최종 실패 원인
- 시도 횟수
- 마지막 예외
- idempotency key

이 정보가 남아야 운영자가 원인을 재현할 수 있다.

## 실전 시나리오

### 시나리오 1: 좌석 예약이 간헐적으로 실패

충돌로 인한 serialization failure는 envelope 안에서 재시도할 수 있다.
하지만 같은 요청이 두 번 예약되지 않도록 idempotency key가 같이 있어야 한다.

### 시나리오 2: 배치가 밤마다 deadlock에 걸림

같은 작업을 재시도할 수 있어도, row 접근 순서가 잘못되면 retry가 폭주한다.
이때 envelope는 backoff와 제한 횟수를 반드시 둬야 한다.

### 시나리오 3: 외부 호출 후 commit 실패

외부는 성공, DB는 실패인 경우 그냥 재시도하면 중복이 된다.
envelope는 결과 조회나 멱등성 회복 로직을 포함해야 한다.

## 코드로 보기

```java
public <T> T runWithRetry(Callable<T> txWork, String idemKey) {
    int attempt = 0;
    while (true) {
        try {
            return txWork.call();
        } catch (RetryableTransactionException e) {
            if (++attempt >= 5) throw e;
            sleepWithJitter(attempt);
        } catch (NonRetryableBusinessException e) {
            throw e;
        }
    }
}
```

```sql
-- retry 전에 결과를 선점해 두면 중복 반영을 줄일 수 있다
INSERT INTO idempotency_keys (idem_key, status, created_at)
VALUES ('req-123', 'PROCESSING', NOW())
ON DUPLICATE KEY UPDATE idem_key = idem_key;
```

retry envelope는 “다시 실행”이 아니라, **다시 실행해도 안전한 형태로 작업을 감싸는 것**이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 무조건 retry | 구현이 쉽다 | 중복과 폭주가 생긴다 | 거의 없음 |
| 제한적 retry envelope | 운영 가능성이 높다 | 분류 로직이 필요하다 | 대부분의 서비스 |
| outbox 결합 | side effect가 안전하다 | 구조가 복잡하다 | 메시지/결제 연동 |
| no retry | 단순하다 | 일시 실패에 취약하다 | 아주 작은 작업 |

## 꼬리질문

> Q: retry envelope와 그냥 retry loop의 차이는 무엇인가요?
> 의도: 재시도 정책과 중복 방지 정책을 분리하는지 확인
> 핵심: envelope는 예외 분류, backoff, idempotency까지 포함한다

> Q: 모든 실패를 retry하면 안 되는 이유는 무엇인가요?
> 의도: 재시도 불가능 실패를 구분하는지 확인
> 핵심: 비즈니스 검증 실패나 유니크 위반은 다시 해도 안 된다

> Q: retry envelope에서 가장 먼저 챙길 것은 무엇인가요?
> 의도: side effect 분리와 idempotency 우선순위를 아는지 확인
> 핵심: 멱등성과 외부 호출 분리다

## 한 줄 정리

Idempotent transaction retry envelope는 재시도 가능한 실패만 다시 시도하고, 같은 작업이 여러 번 실행돼도 결과가 한 번만 반영되게 만드는 실행 경계다.
