# Spring Retry Envelope 위치 Primer

> 한 줄 요약: Spring에서 retry는 실패한 `@Transactional` 안을 되살리는 장치가 아니라, **트랜잭션 한 번의 시도 바깥에서 새 시도를 다시 시작하는 경계**다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Retry Proxy Boundary Pitfalls](./spring-retry-proxy-boundary-pitfalls.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
- [Idempotent Transaction Retry Envelopes](./idempotent-transaction-retry-envelopes.md)
- [Version Column Retry Walkthrough](./version-column-retry-walkthrough.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [트랜잭션 경계 체크리스트 카드](./transaction-boundary-external-io-checklist-card.md)

retrieval-anchor-keywords: spring retry envelope placement, spring retry facade primer, spring retry outside transaction, retry outside @transactional, retry facade vs transactional inside retry, @transactional retry beginner, rollback only retry same transaction, unexpectedrollbackexception retry beginner, fresh transaction per attempt spring, retry facade transaction service split, spring retry before after example, spring retry envelope 위치, spring retry 트랜잭션 바깥, spring 재시도 위치 primer

## 먼저 그림부터

beginner는 아래 두 줄만 먼저 고정하면 된다.

- `@Transactional` 메서드 하나는 "한 번의 시도"다
- retry는 그 한 번의 시도가 실패했을 때 **새 트랜잭션으로 다시 시작**하게 감싸는 바깥 경계다

즉 "트랜잭션 안에서 한 번 더"가 아니라 "트랜잭션 바깥에서 처음부터 한 번 더"가 핵심이다.

## 한 장 비교

| 질문 | `@Transactional` 안쪽 재시도 | 바깥 retry facade |
|---|---|---|
| 다시 시작되는 범위 | 실패한 같은 transaction 안 | 새 transaction 한 번 전체 |
| 첫 실패 뒤 상태 | rollback-only로 오염되기 쉽다 | 이전 시도를 버리고 새로 시작한다 |
| 흔한 결과 | `UnexpectedRollbackException`, 같은 오염 상태 반복 | fresh read + fresh write attempt |
| beginner 기본값 | 피하는 쪽이 안전 | 기본 추천 |

## Before: `@Transactional` 안에서 재시도

아래 코드는 처음 보면 "3번 다시 시도하니까 괜찮다"처럼 보이지만, beginner가 가장 자주 헷갈리는 모양이다.

```java
@Service
public class SeatService {

    @Transactional
    public void reserve(Long seatId, Long memberId) {
        for (int attempt = 1; attempt <= 3; attempt++) {
            try {
                Seat seat = seatRepository.findByIdForUpdate(seatId)
                        .orElseThrow();

                seat.reserve(memberId);
                reservationRepository.save(new Reservation(seatId, memberId));
                return;
            } catch (ObjectOptimisticLockingFailureException ex) {
                if (attempt == 3) {
                    throw ex;
                }
            }
        }
    }
}
```

왜 위험한가:

1. `reserve()`가 transaction을 한 번 연다
2. 중간에 optimistic lock 충돌이나 lock 예외가 나면 그 시도는 이미 실패한 시도다
3. transaction이 rollback-only가 되면, 같은 메서드 안에서 loop를 더 돌아도 깨끗한 새 시도가 아니다
4. 마지막에는 `UnexpectedRollbackException`이나 최종 rollback으로 끝나기 쉽다

핵심 오해는 이것이다.
"예외만 잡으면 같은 transaction 안에서도 다시 해볼 수 있겠지"라고 생각하기 쉽지만, Spring transaction은 그런 식으로 되살리지 않는다.

## After: retry facade는 바깥, transaction은 안쪽

아래 구조가 beginner 기준 기본형이다.

```java
@Service
@RequiredArgsConstructor
public class ReservationRetryFacade {

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
        Seat seat = seatRepository.findByIdForUpdate(seatId)
                .orElseThrow();

        seat.reserve(memberId);
        reservationRepository.save(new Reservation(seatId, memberId));
    }
}
```

이 구조에서 읽어야 할 포인트는 단순하다.

- `ReservationTxService.reserveOnce()`는 딱 한 번의 business attempt만 책임진다
- 실패하면 그 attempt는 버린다
- retry facade가 `reserveOnce()`를 다시 호출할 때는 **새 transaction**이 열린다

필요하면 `@Retryable` 대신 facade에서 수동 loop를 써도 핵심은 같다.
retry 위치가 바깥이면 되고, transaction은 "한 번의 시도"로 남겨 두면 된다.

## 언제 차이가 크게 드러나나

| 상황 | 안쪽 재시도에서 생기기 쉬운 문제 | 바깥 retry facade가 주는 이점 |
|---|---|---|
| optimistic locking 충돌 | stale/rollback-only 상태를 다시 물고 간다 | 최신 상태를 다시 읽는 새 시도가 된다 |
| deadlock / lock timeout | 같은 transaction 안에서 의미 없는 반복이 되기 쉽다 | lock을 풀고 backoff 후 다시 시작할 수 있다 |
| 서비스 코드 리뷰 | loop는 보이지만 경계가 안 보인다 | "retry 담당"과 "한 번의 시도"가 분리돼 읽기 쉽다 |

## 자주 하는 오해

- `@Retryable`을 `@Transactional`과 같은 메서드에 붙이면 항상 틀리다: 항상 그런 것은 아니다. 다만 beginner는 먼저 facade/tx service 분리 구조를 기본값으로 잡는 편이 안전하다.
- `REQUIRES_NEW`를 붙이면 해결된다: 새 transaction은 열 수 있어도, main domain write를 여러 조각 commit으로 만들 수 있다. retry 복구와 같은 뜻이 아니다.
- repository에서 조용히 retry하면 더 깔끔하다: retry budget과 사용자 의미는 repository보다 facade/application service에서 결정하는 편이 낫다.

## 한 줄 규칙

`@Transactional`은 "한 번의 시도", retry facade는 "실패한 시도를 새로 시작하는 바깥 경계"라고 기억하면 첫 설계와 코드리뷰에서 덜 틀린다.
