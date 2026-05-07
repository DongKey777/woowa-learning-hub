---
schema_version: 3
title: Spring Retry Proxy Boundary Pitfalls
concept_id: database/spring-retry-proxy-boundary-pitfalls
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- spring
- retry
- proxy
- transactional
- requires-new
aliases:
- Spring retry proxy boundary
- @Retryable @Transactional same method
- self-invocation retry ignored
- self invocation transactional ignored
- same bean call no proxy
- AOP proxy retry boundary
- REQUIRES_NEW retry pitfall
- UnexpectedRollbackException retry
- rollback-only retry Spring
- retry advice transaction advice order
symptoms:
- '@Retryable'이 붙어 있는데 같은 bean 내부 호출이라 proxy를 타지 않아 retry가 동작하지 않아
- retry 로그는 찍히지만 바깥 transaction이 rollback-only가 되어 UnexpectedRollbackException이 나
- REQUIRES_NEW를 잘못 써서 inner commit이 outer rollback과 분리되거나 connection pool이 고갈돼
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- database/transaction-boundary-external-io-checklist
- database/spring-retry-envelope-placement-primer
next_docs:
- database/transaction-retry-serialization-failure-patterns
- database/idempotent-transaction-retry-envelopes
- spring/service-layer-transaction-boundary-patterns
linked_paths:
- contents/database/transaction-boundary-external-io-checklist-card.md
- contents/database/postgresql-serializable-retry-playbook.md
- contents/database/insert-if-absent-retry-outcome-guide.md
- contents/database/cannotacquirelockexception-40001-insert-if-absent-faq.md
- contents/database/spring-retry-envelope-placement-primer.md
- contents/database/transaction-retry-serialization-failure-patterns.md
- contents/database/version-column-retry-walkthrough.md
- contents/database/connection-pool-transaction-propagation-bulk-write.md
- contents/database/spring-jpa-locking-example-guide.md
- contents/database/idempotent-transaction-retry-envelopes.md
- contents/spring/spring-service-layer-transaction-boundary-patterns.md
confusable_with:
- database/spring-retry-envelope-placement-primer
- database/transaction-retry-serialization-failure-patterns
- database/connection-pool-transaction-propagation-bulk-write
forbidden_neighbors: []
expected_queries:
- Spring에서 @Retryable이 안 먹는 이유가 self-invocation과 proxy boundary 때문인지 어떻게 확인해?
- @Retryable과 @Transactional이 같은 method에 있을 때 언제 괜찮고 언제 self-invocation이나 outer transaction 때문에 깨져?
- REQUIRES_NEW를 retry에 쓰면 왜 atomic unit이 분리되고 connection pool exhaustion이 생길 수 있어?
- retry 로그는 3번 찍히는데 UnexpectedRollbackException이 나는 rollback-only retry Spring 문제를 설명해줘
- retry facade와 transactional service를 별도 bean으로 나눠 proxy를 통과하게 만드는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Spring retry proxy boundary pitfalls를 @Retryable, @Transactional, self-invocation, REQUIRES_NEW, rollback-only transaction 관점으로 다루는 advanced playbook이다.
  self-invocation retry ignored, same bean call no proxy, UnexpectedRollbackException retry, REQUIRES_NEW retry pitfall 질문이 본 문서에 매핑된다.
---
# Spring Retry Proxy Boundary Pitfalls

> 한 줄 요약: Spring에서 transaction retry는 예외 이름보다 `@Retryable`, `@Transactional`, `REQUIRES_NEW`가 어느 proxy 경계를 통과하느냐가 더 중요하다.

**난이도: 🔴 Advanced**

관련 문서: [트랜잭션 경계 체크리스트 카드](./transaction-boundary-external-io-checklist-card.md), [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md), [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md), [`CannotAcquireLockException` / `40001` 혼동 FAQ](./cannotacquirelockexception-40001-insert-if-absent-faq.md), [Spring Retry Envelope 위치 Primer](./spring-retry-envelope-placement-primer.md), [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md), [Version Column Retry Walkthrough](./version-column-retry-walkthrough.md), [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md), [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md), [Idempotent Transaction Retry Envelopes](./idempotent-transaction-retry-envelopes.md), [Spring Service Layer Transaction Boundary Patterns](../spring/spring-service-layer-transaction-boundary-patterns.md)
retrieval-anchor-keywords: spring retry proxy boundary, spring retryable transactional, spring retry transaction boundary, @retryable @transactional same method, self-invocation retry ignored, self invocation transactional ignored, same bean call no proxy, aop proxy retry boundary, requires_new retry pitfall, requires_new connection pool exhaustion, unexpectedrollbackexception retry, rollback-only retry spring, outer transaction inner retry spring, retry advice transaction advice order, fresh transaction per retry attempt, spring retry facade split, retry envelope placement spring

## Beginner 먼저 보기

이 문서는 "`@Retryable`이 왜 안 먹지?", "retry는 3번 찍히는데 왜 `UnexpectedRollbackException`이 나지?", "`40001`이면 같은 transaction 안에서 SQL만 다시 치면 되나?" 같은 증상을 proxy/transaction 경계 관점에서 해부하는 advanced 문서다.

처음 보는 독자라면 아래 순서로 짧게 우회한 뒤 돌아오는 편이 훨씬 안전하다.

| 지금 막힌 첫 질문 | 먼저 볼 카드 | 여기서 먼저 잡는 감각 |
|---|---|---|
| "트랜잭션 안에서 뭘 밖으로 빼야 하는지부터 헷갈린다" | [트랜잭션 경계 체크리스트 카드](./transaction-boundary-external-io-checklist-card.md) | retry 전에 **트랜잭션 길이와 외부 I/O 경계**를 먼저 줄인다 |
| "`40001`/deadlock은 SQL 한 줄 재시도인가, 전체 재시도인가" | [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md) | retry 단위가 **SQL 한 줄이 아니라 트랜잭션 시도 전체**라는 감각을 맞춘다 |
| "`duplicate`/`busy`/`retryable` 결과 문장이 자꾸 섞인다" | [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md) | 예외 이름보다 **서비스 결과 라벨**을 먼저 고정한다 |

짧게 말해, **경계 길이 -> whole-transaction retry -> 결과 라벨** 순서로 첫 그림을 잡고 이 문서를 읽으면 `proxy` 함정이 glossary처럼 보이지 않는다.

## 핵심 개념

이 주제는 "retry를 몇 번 할까"보다 "retry가 **어디를 다시 실행하나**"가 먼저다.

- `@Retryable`은 proxy를 통과한 메서드 호출에만 붙는다
- `@Transactional`도 proxy를 통과한 메서드 호출에만 transaction 경계를 만든다
- `REQUIRES_NEW`는 "새 transaction"이지 "원래 atomic unit을 자동 복구"가 아니다

즉 Spring retry 문제는 거의 항상 예외 분류보다 **proxy boundary + transaction boundary** 문제다.

한 가지 중요한 nuance도 있다.

- `@Retryable`과 `@Transactional`을 같은 top-level 메서드에 같이 두는 것 자체는 자동으로 오답이 아니다
- 일반적인 default order에서는 retry advice가 transaction advice 바깥에 걸려서 attempt마다 새 transaction이 열리기 쉽다
- 하지만 self-invocation, 바깥 `@Transactional`, 잘못된 `REQUIRES_NEW` 사용이 끼어들면 기대한 경계가 바로 무너진다

## 이름 혼동을 먼저 끊고 싶다면

예외 클래스 이름 때문에 자꾸 길을 잃는다면 아래 두 장을 먼저 붙이면 된다.

- `insert-if-absent`에서 `duplicate` / `busy` / `retryable` 3버킷을 먼저 익히려면 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- `CannotAcquireLockException`과 PostgreSQL `40001`을 같은 이름으로 외우지 않으려면 [`CannotAcquireLockException` / `40001` 혼동 FAQ](./cannotacquirelockexception-40001-insert-if-absent-faq.md)

## 먼저 실패 지도를 잡기

| 보이는 증상 | 실제로 벌어진 일 | 먼저 고칠 것 |
|---|---|---|
| `@Retryable`이 아예 안 먹는 것 같다 | 같은 bean 내부 호출이라 proxy를 안 탔다 | retry facade를 별도 bean으로 분리 |
| retry 로그는 3번 찍히는데 결국 `UnexpectedRollbackException`이 난다 | 바깥 transaction 하나가 이미 rollback-only가 됐다 | retry loop를 outer transaction 바깥으로 이동 |
| `REQUIRES_NEW`를 붙였더니 일단 돌아가지만 데이터가 어긋난다 | inner commit이 outer rollback과 분리됐다 | main domain write에 `REQUIRES_NEW`를 쓰지 않기 |
| retry를 켠 뒤 pool timeout이 늘었다 | outer transaction이 resource를 쥔 채 inner `REQUIRES_NEW`가 추가 connection을 더 요구할 수 있다 | retry loop와 outer transaction을 겹치지 않기 |

## 함정 1: self-invocation이 proxy를 우회한다

가장 흔한 오해는 annotation이 붙어 있으면 같은 bean 안에서도 항상 동작한다고 생각하는 것이다.

```java
@Service
public class CouponService {

    public void issue(Long couponId) {
        issueWithRetry(couponId); // same bean call
    }

    @Retryable(
            retryFor = ObjectOptimisticLockingFailureException.class,
            maxAttempts = 3
    )
    public void issueWithRetry(Long couponId) {
        issueOnce(couponId); // same bean call
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void issueOnce(Long couponId) {
        // coupon row update
    }
}
```

이 코드에서 annotation은 보여도 경계는 기대와 다르다.

- `issue()` -> `issueWithRetry()`는 같은 bean 내부 호출이라 `@Retryable`이 적용되지 않는다
- `issueWithRetry()` -> `issueOnce()`도 같은 bean 내부 호출이라 `REQUIRES_NEW`가 적용되지 않는다
- 결과적으로 "retry + fresh transaction per attempt"가 아니라 그냥 같은 객체 메서드 호출 두 번일 뿐이다

self-invocation은 retry와 transaction 둘 다 동시에 깨뜨릴 수 있다.

### 더 안전한 모양

```java
@Service
@RequiredArgsConstructor
public class CouponRetryFacade {

    private final CouponTxService couponTxService;

    @Retryable(
            retryFor = ObjectOptimisticLockingFailureException.class,
            maxAttempts = 3
    )
    public void issue(Long couponId) {
        couponTxService.issueOnce(couponId);
    }
}

@Service
public class CouponTxService {

    @Transactional
    public void issueOnce(Long couponId) {
        // one atomic attempt
    }
}
```

이 구조에서는 bean 경계가 분리되어 proxy를 실제로 통과한다.

## 함정 2: outer `@Transactional`이 retry boundary를 먹어버린다

retry가 fresh transaction을 열어 줄 것이라고 기대했는데, 실제로는 바깥 transaction 하나 안에서 재시도만 반복되는 경우가 많다.

```java
@Service
@RequiredArgsConstructor
public class OrderFacade {

    private final PaymentService paymentService;

    @Transactional
    public void placeOrder(Long orderId) {
        paymentService.captureWithRetry(orderId);
    }
}

@Service
public class PaymentService {

    @Retryable(
            retryFor = CannotAcquireLockException.class,
            maxAttempts = 3
    )
    @Transactional
    public void captureWithRetry(Long orderId) {
        // payment row update
    }
}
```

겉보기에는 `captureWithRetry()`가 3번 새로 시도될 것 같지만, 실제 경계는 다르다.

1. `placeOrder()`가 outer transaction을 한 번 연다
2. inner `@Transactional`은 기본값 `REQUIRED`라서 그 transaction에 합류한다
3. 첫 실패가 outer transaction을 rollback-only로 만든다
4. retry interceptor가 다시 호출해도 각 attempt는 같은 doomed transaction에 다시 들어간다
5. 마지막에는 `UnexpectedRollbackException` 또는 최종 rollback으로 끝난다

핵심은 "retry 횟수"가 아니라 "fresh transaction per attempt가 있었는가"다.

### 판단 규칙

- orchestration과 retry를 담당하는 메서드는 가능하면 non-transactional로 둔다
- per-attempt atomic unit만 별도 bean의 `@Transactional` 메서드로 둔다
- outer transaction이 꼭 필요하다면, inner retry가 정말 같은 logical unit 안에서 의미가 있는지 먼저 의심한다

## 함정 3: `REQUIRES_NEW`는 응급처치가 아니라 별도 commit이다

rollback-only 오염을 피하려고 `REQUIRES_NEW`를 붙이면 당장 예외 모양은 바뀔 수 있다. 하지만 그것이 곧 올바른 retry boundary는 아니다.

```java
@Service
@RequiredArgsConstructor
public class ReservationFacade {

    private final ReservationTxService reservationTxService;

    @Transactional
    public void reserve(Long seatId, Long memberId) {
        for (int attempt = 1; attempt <= 3; attempt++) {
            try {
                reservationTxService.reserveOnce(seatId, memberId);
                return;
            } catch (CannotAcquireLockException ex) {
                if (attempt == 3) {
                    throw ex;
                }
            }
        }
    }
}

@Service
public class ReservationTxService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void reserveOnce(Long seatId, Long memberId) {
        // seat claim + reservation insert
    }
}
```

이 구조는 두 가지 함정을 만든다.

- outer transaction이 resource를 쥔 상태에서 inner `REQUIRES_NEW`가 추가 connection을 더 요구할 수 있다
- inner attempt가 성공해 commit되면, 나중에 outer 코드가 실패해도 그 inner commit은 되돌아가지 않는다

즉 `REQUIRES_NEW`는 "fresh retry attempt"가 아니라 **독립 커밋 단위**다.

이 패턴이 위험한 이유는 다음과 같다.

- concurrency가 높으면 pool starvation을 더 빨리 만든다
- retry loop가 길수록 inner commit 조각이 늘어난다
- audit, outbox, idempotency row를 무심코 섞으면 partial success를 만들기 쉽다

### 언제 `REQUIRES_NEW`가 맞는가

`REQUIRES_NEW`는 아래처럼 "정말로 따로 남겨야 하는 기록"에만 제한적으로 맞다.

- 실패 attempt audit row
- best-effort metric/event log
- outer 성공 여부와 분리해도 되는 운영 흔적

반대로 main domain write를 살리기 위한 응급처치로 붙이면 경계가 더 헷갈려진다.

## 권장 구조: retry envelope는 바깥, transaction은 per-attempt

가장 덜 흔들리는 기본 모양은 아래다.

```java
@Service
@RequiredArgsConstructor
public class ReservationCommandFacade {

    private final ReservationTxService reservationTxService;

    @Retryable(
            retryFor = {
                    CannotAcquireLockException.class,
                    ObjectOptimisticLockingFailureException.class
            },
            maxAttempts = 3,
            backoff = @Backoff(delay = 50, multiplier = 2.0)
    )
    public void reserve(Long seatId, Long memberId) {
        reservationTxService.reserveOnce(seatId, memberId);
    }
}

@Service
public class ReservationTxService {

    @Transactional
    public void reserveOnce(Long seatId, Long memberId) {
        // one business attempt
    }
}
```

이 구조의 장점은 명확하다.

- retry envelope가 transaction attempt 바깥에 있다
- bean이 분리되어 self-invocation을 피한다
- 매 attempt가 새 transaction으로 해석되기 쉽다
- `REQUIRES_NEW`를 "주 write path 복구 도구"로 남용하지 않는다

추가로 같이 기억하면 좋은 규칙은 다음이다.

- retry 대상 예외만 좁게 분류한다
- 외부 API 호출은 가능하면 transaction 안에 두지 않는다
- idempotency가 없으면 retry는 중복 부작용 증폭기가 된다

## 꼬리질문

> Q: `@Retryable`이 안 먹는지 어떻게 가장 먼저 의심하나요?
> 의도: proxy를 실제로 통과했는지부터 보는지 확인
> 핵심: 같은 bean 내부 호출이면 annotation이 보여도 advice는 적용되지 않을 수 있다

> Q: outer `@Transactional` + inner retry에서 왜 `UnexpectedRollbackException`이 나오나요?
> 의도: 실패한 attempt와 rollback-only transaction 오염을 구분하는지 확인
> 핵심: 첫 실패가 outer transaction 전체를 망가뜨리면 이후 retry도 fresh attempt가 아니다

> Q: `REQUIRES_NEW`를 붙이면 retry 문제가 해결되나요?
> 의도: fresh attempt와 separate commit을 구분하는지 확인
> 핵심: `REQUIRES_NEW`는 새 transaction이지만 기존 atomic unit을 보존해 주지는 않는다

## 한 줄 정리

Spring retry 경계는 `@Retryable` annotation 자체보다 proxy를 실제로 통과했는지, outer transaction이 이미 경계를 먹고 있지 않은지, `REQUIRES_NEW`가 복구가 아니라 별도 commit이라는 점을 구분할 때 비로소 안정해진다.
