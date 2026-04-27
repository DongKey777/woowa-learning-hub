# Spring/JPA 락킹 예제 가이드

> 한 줄 요약: Spring 서비스 계층에서는 `@Version`, `SELECT ... FOR UPDATE`, retry loop를 각각 "충돌 감지", "선점 보호", "재실행 경계"로 분리해야 코드와 운영 해석이 단순해진다.

**난이도: 🔴 Advanced**

관련 문서: [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md), [Compare-and-Set와 Version Columns](./compare-and-set-version-columns.md), [Version Column Retry Walkthrough](./version-column-retry-walkthrough.md), [Compare-and-Swap과 Pessimistic Locks](./compare-and-swap-vs-pessimistic-locks.md), [Spring/JPA Exact-Key Lock Mapping Guide](./spring-jpa-exact-key-lock-mapping-guide.md), [JPA `PESSIMISTIC_WRITE`의 범위 잠금 한계와 전환 기준](./range-locking-limits-jpa.md), [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md), [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md), [Spring Service Layer Transaction Boundary Patterns](../spring/spring-service-layer-transaction-boundary-patterns.md)
retrieval-anchor-keywords: spring jpa locking example, spring optimistic locking example, spring pessimistic locking example, jpa version column service flow, select for update spring data jpa, retry boundary transactional spring, optimistic lock retry facade, spring transaction retry boundary, jpa for update example, spring lock timeout retry, version column flush sql, objectoptimisticlockingfailureexception, optimistic lock failure propagation, rollback only optimistic lock, jpa pessimistic write limitation, jpa absence invariant, jpa range invariant, jpa empty result for update

## 핵심 개념

Spring/JPA에서 락킹을 설명할 때는 DB 이론만으로는 부족하고, **서비스 계층에서 어디를 한 번의 시도로 보고 어디를 다시 실행할지**까지 같이 말해야 한다.

핵심 구분은 세 가지다.

- `@Version`: commit 직전 `UPDATE ... WHERE version = ?`로 마지막 경합을 감지한다
- `SELECT ... FOR UPDATE`: transaction 초반에 row를 선점해서 충돌을 대기로 바꾼다
- retry boundary: 실패한 transaction 전체를 새로 시작할 경계를 `@Transactional` 바깥에 둔다

즉 "락을 어떤 SQL로 거는가"보다 **"서비스 흐름을 몇 겹으로 자르는가"**가 더 중요하다.

## 먼저 고르는 기준

| 상황 | 보통의 선택 | 이유 | retry 경계 |
|---|---|---|---|
| 같은 row 수정인데 충돌이 가끔만 난다 | `@Version` | lock 점유 시간을 늘리지 않는다 | facade/application service 바깥 루프 |
| 같은 row에 요청이 몰리고 중복 성공이 치명적이다 | `FOR UPDATE` / `PESSIMISTIC_WRITE` | DB가 순서를 직접 세운다 | lock timeout, deadlock만 bounded retry |
| "없음"이나 범위를 믿고 insert한다 | row lock만으로 부족할 수 있다 | set invariant 문제다 | guard row / unique / serializable 문서로 이동 |

세 번째 축은 이 문서의 범위를 넘는다. 그 경우는 [JPA `PESSIMISTIC_WRITE`의 범위 잠금 한계와 전환 기준](./range-locking-limits-jpa.md), [Guard Row vs Serializable Retry vs Reconciliation for Set Invariants](./guard-row-vs-serializable-vs-reconciliation-set-invariants.md), [MySQL Empty-Result Locking Reads](./mysql-empty-result-locking-reads.md)로 내려가는 편이 맞다.

## 서비스 계층을 두 겹으로 자르기

실무에서는 보통 아래 구조가 가장 설명하기 쉽다.

1. `Facade` 또는 application service
2. `@Transactional`이 붙은 per-attempt service
3. JPA repository

의도는 명확하다.

- facade는 retry, backoff, idempotency 판단을 가진다
- transactional service는 "한 번 시도"의 원자성만 책임진다
- repository는 lock mode와 조회 shape를 노출한다

이 구분이 무너지면 `rollback-only` transaction 안에서 같은 로직을 다시 돌리거나, lock을 잡은 채 외부 API를 기다리는 문제가 나온다.

## 예제 1: `@Version`으로 마지막 저장 경합 잡기

충돌은 드물지만 같은 coupon row를 동시에 수정할 수 있는 경로라고 가정하자. 이 경우 `@Version`이 가장 자연스럽다.

### 엔티티

```java
@Entity
public class CouponStock {

    @Id
    private Long couponId;

    private int remainingCount;

    @Version
    private long version;

    public void decrease(int quantity) {
        if (remainingCount < quantity) {
            throw new SoldOutException();
        }
        remainingCount -= quantity;
    }
}
```

### 서비스 흐름

```java
@Service
@RequiredArgsConstructor
public class CouponIssueFacade {

    private final CouponIssueTxService txService;

    public void issue(Long couponId, Long memberId, int quantity) {
        for (int attempt = 1; attempt <= 3; attempt++) {
            try {
                txService.issueOnce(couponId, memberId, quantity);
                return;
            } catch (ObjectOptimisticLockingFailureException ex) {
                if (attempt == 3) {
                    throw ex;
                }
                sleepBriefly(attempt);
            }
        }
    }

    private void sleepBriefly(int attempt) {
        try {
            Thread.sleep(20L * attempt);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(interrupted);
        }
    }
}

@Service
@RequiredArgsConstructor
class CouponIssueTxService {

    private final CouponStockRepository couponStockRepository;
    private final CouponIssuanceRepository couponIssuanceRepository;

    @Transactional
    public void issueOnce(Long couponId, Long memberId, int quantity) {
        CouponStock stock = couponStockRepository.findById(couponId)
                .orElseThrow(() -> new IllegalArgumentException("coupon not found"));

        stock.decrease(quantity);
        couponIssuanceRepository.save(new CouponIssuance(couponId, memberId, quantity));
    }
}
```

### flush 시 실제로 일어나는 일

Hibernate는 dirty checking 후 대략 아래 형태의 SQL을 보낸다.

```sql
update coupon_stock
   set remaining_count = ?,
       version = ?
 where coupon_id = ?
   and version = ?;
```

여기서 중요한 해석은 다음이다.

- update count가 `1`이면 내가 읽은 version이 아직 유효했다
- update count가 `0`이면 누군가 먼저 커밋했고, Spring은 `ObjectOptimisticLockingFailureException`으로 번역할 수 있다
- 이 시점의 transaction은 이미 rollback-only이므로 **같은 `@Transactional` 메서드 안에서 다시 시도하면 안 된다**

즉 optimistic locking의 retry는 "쿼리 한 줄 재실행"이 아니라 **transaction 전체 재실행**이다.

### 언제 이 패턴이 맞나

- 같은 row 충돌은 있지만 lock wait로 줄 세우고 싶지는 않을 때
- 재계산 비용이 작고 2~3회 재시도가 UX를 망치지 않을 때
- 외부 API 호출 없이 DB 상태만 짧게 바꿀 때

반대로 사용자가 직접 merge 여부를 결정해야 하는 편집 화면이라면 자동 retry보다 conflict 응답이 더 맞을 수 있다.

## 예제 2: `SELECT ... FOR UPDATE`로 hot row 먼저 잠그기

재고 1개, 좌석 1개처럼 **중복 성공이 치명적이고 충돌도 자주 나는 row**는 pessimistic lock이 더 단순하다.

### Repository에서 lock mode 드러내기

```java
public interface InventoryRepository extends JpaRepository<Inventory, Long> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select i from Inventory i where i.id = :inventoryId")
    @QueryHints(
            @QueryHint(name = "jakarta.persistence.lock.timeout", value = "2000")
    )
    Optional<Inventory> findByIdForUpdate(@Param("inventoryId") Long inventoryId);
}
```

dialect가 지원하면 대략 아래 SQL이 나간다.

```sql
select id, available_quantity, version
  from inventory
 where id = ?
 for update;
```

### 서비스 흐름

```java
@Service
@RequiredArgsConstructor
public class InventoryReservationTxService {

    private final InventoryRepository inventoryRepository;
    private final ReservationRepository reservationRepository;

    @Transactional
    public Reservation reserve(Long inventoryId, Long orderId, int quantity) {
        Inventory inventory = inventoryRepository.findByIdForUpdate(inventoryId)
                .orElseThrow(() -> new IllegalArgumentException("inventory not found"));

        inventory.decrease(quantity);

        return reservationRepository.save(
                Reservation.pending(orderId, inventoryId, quantity)
        );
    }
}
```

이 패턴에서 중요한 것은 transaction을 짧게 유지하는 것이다.

- lock을 잡은 뒤 외부 결제 API를 호출하지 않는다
- 같은 transaction 안에서 여러 row를 잠글 때는 순서를 고정한다
- hot row가 너무 뜨거워지면 lock 전략보다 데이터 모델을 바꿀 시점인지 먼저 본다

### JPA로 부족할 때

다음 경우는 repository 메서드를 native query나 JDBC/MyBatis로 내리는 편이 낫다.

- `SKIP LOCKED`, `NOWAIT` 같은 vendor 문법이 필요한 queue claim
- range probe와 `FOR UPDATE` footprint를 정확히 통제해야 하는 경우
- 실행 계획과 index 선택을 SQL 레벨에서 직접 보고 싶은 경우

즉 `@Lock(PESSIMISTIC_WRITE)`는 출발점이고, lock footprint를 정밀 제어해야 하면 ORM 추상을 일부 벗겨야 한다.

## 예제 3: retry boundary는 `@Transactional` 바깥에 둔다

locking 예제가 실제 서비스에서 헷갈리는 이유는 DB 충돌보다 **재시도와 외부 부작용의 경계**가 더 어렵기 때문이다.

아래처럼 주문 배치 흐름을 두 단계로 쪼개면 설명이 쉬워진다.

```java
@Service
@RequiredArgsConstructor
public class PlaceOrderFacade {

    private final OrderReservationTxService orderReservationTxService;
    private final PaymentClient paymentClient;
    private final OrderFinalizeTxService orderFinalizeTxService;

    public OrderReceipt place(PlaceOrderCommand command) {
        OrderDraft draft = retryReservation(command);

        PaymentResult payment = paymentClient.charge(
                command.idempotencyKey(),
                draft.totalAmount()
        );

        return orderFinalizeTxService.confirm(draft.orderId(), payment.approvalNo());
    }

    private OrderDraft retryReservation(PlaceOrderCommand command) {
        for (int attempt = 1; attempt <= 3; attempt++) {
            try {
                return orderReservationTxService.reserve(command);
            } catch (ObjectOptimisticLockingFailureException
                     | PessimisticLockingFailureException ex) {
                if (attempt == 3) {
                    throw ex;
                }
                sleepBriefly(attempt);
            }
        }
        throw new IllegalStateException("unreachable");
    }

    private void sleepBriefly(int attempt) {
        try {
            Thread.sleep(30L * attempt);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(interrupted);
        }
    }
}
```

이 구조가 주는 이점은 세 가지다.

- reservation 단계의 DB contention만 retry한다
- 결제 API는 DB lock이 없는 상태에서 호출한다
- confirm 단계는 결제 결과만 반영하므로 실패 원인이 훨씬 단순해진다

### 재시도 여부를 나누는 표

| 예외/상황 | 보통 retry? | 이유 |
|---|---|---|
| `ObjectOptimisticLockingFailureException` | 예 | 같은 row 경합이므로 전체 transaction 재시도 후보다 |
| `CannotAcquireLockException`, `PessimisticLockingFailureException` | 제한적으로 예 | lock timeout, deadlock은 transient일 수 있다 |
| `SoldOutException`, `InsufficientBalanceException` | 아니오 | 비즈니스 규칙 실패는 다시 해도 그대로다 |
| 외부 결제 timeout after charge | 무작정 아니오 | 상태 불명확이므로 idempotency key와 결과 조회형 복구가 필요하다 |

retry는 "실패했으니 다시"가 아니라, **같은 입력을 새 transaction으로 안전하게 다시 흘릴 수 있는가**를 묻는 정책이다.

## 자주 하는 실수

- 같은 클래스 안에서 `this.issueOnce()`를 다시 호출한다.
  - self-invocation이면 Spring proxy를 타지 않아 새 transaction이 열리지 않을 수 있다.
- `@Transactional` 메서드 안에서 `OptimisticLockException`을 catch하고 계속 진행한다.
  - 이미 rollback-only일 가능성이 높아서 결국 commit 시점에 다시 실패한다.
- `FOR UPDATE`로 잠근 뒤 HTTP 호출이나 Kafka publish를 기다린다.
  - lock wait, deadlock, connection pool 고갈로 번지기 쉽다.
- JPA `PESSIMISTIC_WRITE`면 범위 부재까지 자동 보호된다고 생각한다.
  - empty-result/range invariant는 엔진과 쿼리 shape에 따라 별도 설계가 필요하다.

## 면접이나 리뷰에서 짧게 답하는 문장

- "`@Version`은 마지막 `UPDATE ... WHERE version = ?`에서 충돌을 감지하므로 retry는 transaction 바깥에서 다시 시작해야 합니다."
- "`SELECT ... FOR UPDATE`는 충돌을 대기로 바꾸는 대신 lock 점유 시간이 길어지면 운영 리스크가 커집니다."
- "Spring에서는 facade가 retry를 책임지고, `@Transactional` service는 한 번의 시도만 책임지게 나누면 설명과 장애 해석이 단순해집니다."

## 한 줄 정리

Spring/JPA 락킹의 핵심은 lock 문법보다 경계 설계다. `@Version`은 저장 시 충돌 감지, `FOR UPDATE`는 transaction 초반 선점, retry는 반드시 그 transaction 바깥에서 다시 시작해야 한다.
