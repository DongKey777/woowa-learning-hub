# JPA `PESSIMISTIC_WRITE`의 범위 잠금 한계와 전환 기준

> 한 줄 요약: JPA `PESSIMISTIC_WRITE`는 조회된 엔티티 row를 잠그는 도구이지 `없음`, overlap, count/sum 같은 predicate invariant를 직접 잠그는 도구가 아니다. exact duplicate는 제약조건으로, range/set invariant는 guard row나 constraint로, lock footprint 제어는 native SQL로 옮겨야 한다.

**난이도: 🔴 Advanced**

관련 문서:

- [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md)
- [Spring/JPA Exact-Key Lock Mapping Guide](./spring-jpa-exact-key-lock-mapping-guide.md)
- [MySQL Empty-Result Locking Reads](./mysql-empty-result-locking-reads.md)
- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)
- [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)
- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- [Guard Row vs Serializable Retry vs Reconciliation for Set Invariants](./guard-row-vs-serializable-vs-reconciliation-set-invariants.md)
- [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md)
- [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md)

retrieval-anchor-keywords: jpa pessimistic write limitation, jpa range lock limitation, jpa absence invariant, spring data jpa for update zero rows, jpa overlap check race, jpa pessimistic lock phantom, jpa no rows locked insert race, lockmodetype pessimisticwrite range invariant, jpa booking overlap double booking, jpa guard row, jpa exclusion constraint, jpa unique constraint duplicate insert, native query for update skip locked, jpa select for update missing row, jpa count sum invariant lock, jpa range locking limits

## 핵심 개념

`LockModeType.PESSIMISTIC_WRITE`를 쓰면 팀이 흔히 이렇게 해석한다.

> "이제 이 조건을 만족하는 대상은 다른 트랜잭션이 못 건드리겠지."

하지만 JPA가 실제로 표현하는 것은 더 좁다.

- query가 반환한 **엔티티 row**를 잠근다
- 결과가 `0 row`면 JPA 입장에서는 잠근 엔티티도 `0 row`다
- range/absence 보호가 남는지 여부는 엔진, isolation level, index path에 달린다
- 그래서 `PESSIMISTIC_WRITE`는 **existing row ownership transfer**에는 좋지만, `없음`이나 `범위`를 믿고 새 row를 만드는 규칙에는 기본 해법이 아니다

핵심 질문은 "JPA가 `FOR UPDATE`를 만들 수 있는가"가 아니라, **내 business invariant가 실제로 어떤 저장 surface에서 충돌해야 하는가**다.

## 먼저 고르는 기준

| 지키려는 규칙 | detail row에 대한 `PESSIMISTIC_WRITE`로 충분한가 | 더 맞는 전환 |
|---|---|---|
| 같은 entity row 하나를 먼저 선점해야 함 | 대체로 예 | JPA `PESSIMISTIC_WRITE` |
| "이 key가 아직 없다"를 믿고 insert | 보통 아니오 | `UNIQUE`, PK, upsert arbitration |
| 시간 구간 overlap 금지 | 보통 아니오 | exclusion constraint, slot + unique, guard row |
| count/sum/capacity/minimum staffing | 아니오 | guard row, ledger, atomic conditional update |
| `SKIP LOCKED`, `NOWAIT`, ordered multi-lock, exact plan 통제 | 아니오 | native SQL, JDBC, MyBatis |

즉 `PESSIMISTIC_WRITE`를 버려야 한다는 뜻이 아니라, **detail row를 잠그는 위치가 invariant와 맞지 않으면 arbitration surface를 옮겨야 한다**는 뜻이다.

## 예제 1. absence invariant: 발급 이력이 없으면 insert

문제 코드의 의도는 단순하다.

1. 이미 발급한 `(coupon_id, member_id)`가 있는지 본다
2. 없으면 새 발급 row를 저장한다

```java
public interface CouponIssueRepository extends JpaRepository<CouponIssue, Long> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("""
        select ci
        from CouponIssue ci
        where ci.couponId = :couponId
          and ci.memberId = :memberId
        """)
    Optional<CouponIssue> findIssuedForUpdate(Long couponId, Long memberId);
}
```

```java
@Transactional
public void issue(Long couponId, Long memberId) {
    if (couponIssueRepository.findIssuedForUpdate(couponId, memberId).isPresent()) {
        throw new DuplicateIssueException();
    }

    couponIssueRepository.save(new CouponIssue(couponId, memberId));
}
```

왜 새는가:

- T1, T2가 동시에 `findIssuedForUpdate()`를 호출한다
- 둘 다 `Optional.empty()`를 본다
- 잠근 entity row가 없으니 JPA가 직렬화한 것도 없다
- 둘 다 `save()`에 성공하면 중복 발급이다

즉 `PESSIMISTIC_WRITE`가 막는 것은 **이미 존재하는 발급 row의 동시 수정**이지, "아직 없다"는 사실이 아니다.

### 전환: exact duplicate는 제약조건으로 닫는다

```sql
ALTER TABLE coupon_issue
ADD CONSTRAINT uq_coupon_issue_coupon_member
UNIQUE (coupon_id, member_id);
```

이제 arbitration surface는 조회가 아니라 **유일 제약**이 된다.

- 둘이 동시에 insert하면 하나만 성공한다
- 실패한 쪽은 duplicate-key/constraint violation을 business conflict로 번역하면 된다
- 쿠폰 수량 차감 같은 다른 규칙이 있으면 그건 `coupon_stock` 같은 **부모 row lock**으로 별도 중재한다

absence invariant에서 첫 선택은 `PESSIMISTIC_WRITE`가 아니라 보통 `UNIQUE`다.

## 예제 2. range invariant: 겹치는 예약이 없으면 저장

다음 JPA 코드는 흔히 "overlap을 잠그는" 코드로 오해된다.

```java
public interface RoomBookingRepository extends JpaRepository<RoomBooking, Long> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("""
        select b
        from RoomBooking b
        where b.roomId = :roomId
          and b.status in ('HELD', 'CONFIRMED')
          and b.startAt < :requestedEnd
          and b.endAt > :requestedStart
        """)
    List<RoomBooking> findActiveOverlapsForUpdate(
            Long roomId,
            Instant requestedStart,
            Instant requestedEnd
    );
}
```

```java
@Transactional
public RoomBooking book(Long roomId, Instant requestedStart, Instant requestedEnd) {
    List<RoomBooking> overlaps = roomBookingRepository.findActiveOverlapsForUpdate(
            roomId, requestedStart, requestedEnd
    );

    if (!overlaps.isEmpty()) {
        throw new OverlapBookingException();
    }

    return roomBookingRepository.save(
            RoomBooking.held(roomId, requestedStart, requestedEnd)
    );
}
```

왜 부족한가:

- `0 row`면 잠근 booking entity도 `0 row`다
- 기존 blocker row를 잠갔다 해도, 그건 **지금 읽힌 row**에 대한 락이지 overlap predicate 자체에 대한 락이 아니다
- 다른 write path가 probe 없이 insert/update 하거나, 엔진/plan/index가 바뀌면 보호 surface가 흔들린다

즉 이 코드는 "겹치는 row가 있으면 그 row를 잠근다"에 가깝지, "겹치는 booking이 생기지 못하게 한다"와는 다르다.

### 전환 A: PostgreSQL + continuous interval이면 constraint로 내린다

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE room_booking
ADD CONSTRAINT room_booking_no_overlap
EXCLUDE USING gist (
  room_id WITH =,
  tstzrange(start_at, end_at, '[)') WITH &&
)
WHERE (status IN ('HELD', 'CONFIRMED'));
```

이 경우 conflict surface는 JPA query가 아니라 **DB constraint**다.

- overlap 판단이 write-time rejection으로 바뀐다
- 애플리케이션은 `23P01`을 business conflict로 번역하면 된다
- "empty result를 잠갔다"는 불안정한 해석이 사라진다

### 전환 B: MySQL이거나 write path가 여러 개면 guard row로 queue를 만든다

continuous interval overlap, later assignment, blackout, cleanup path가 섞이면 detail booking row보다 **guard key**를 먼저 잠그는 편이 낫다.

```sql
INSERT INTO room_day_guard(room_id, stay_day)
VALUES (:room_id, :stay_day)
ON DUPLICATE KEY UPDATE room_id = room_id;

SELECT room_id, stay_day
FROM room_day_guard
WHERE room_id = :room_id
  AND stay_day BETWEEN :from_day AND :to_day
FOR UPDATE;
```

그 다음 lock 아래에서 exact overlap를 다시 확인하고 booking row를 쓴다.

guard row로 전환하면 달라지는 점은 이것이다.

- detail booking row 대신 `(room_id, stay_day)` 같은 **canonical arbitration key**에서 경쟁한다
- 신규 예약, 연장, 취소, expiry cleanup이 같은 protocol을 타게 만들 수 있다
- `0 row overlap query`라는 취약한 시작점 대신, 항상 존재하게 만들 수 있는 guard row를 잠근다

여기서 native SQL/JDBC를 자주 쓰는 이유는 JPA가 약해서가 아니라, **upsert 후 lock**, ordered multi-key lock, vendor-specific `NOWAIT`/`SKIP LOCKED`를 정확히 표현하기 어렵기 때문이다.

## 예제 3. set invariant: 현재 활성 예약 합계가 capacity 이하

capacity 문제도 detail row lock으로는 자주 잘못 시작한다.

```java
public interface RoomTypeReservationRepository extends JpaRepository<RoomTypeReservation, Long> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("""
        select r
        from RoomTypeReservation r
        where r.roomTypeId = :roomTypeId
          and r.stayDay = :stayDay
          and r.status in ('HELD', 'CONFIRMED')
        """)
    List<RoomTypeReservation> findActiveReservationsForUpdate(
            Long roomTypeId,
            LocalDate stayDay
    );
}
```

```java
@Transactional
public void reserve(Long roomTypeId, LocalDate stayDay, int qty) {
    List<RoomTypeReservation> active = roomTypeReservationRepository
            .findActiveReservationsForUpdate(roomTypeId, stayDay);

    int reserved = active.stream().mapToInt(RoomTypeReservation::getQty).sum();
    if (reserved + qty > capacity(roomTypeId, stayDay)) {
        throw new SoldOutException();
    }

    roomTypeReservationRepository.save(
            RoomTypeReservation.held(roomTypeId, stayDay, qty)
    );
}
```

왜 부족한가:

- active row가 `0 row`면 역시 lock도 `0 row`다
- 여러 트랜잭션이 각자 다른 신규 row를 insert해도 capacity는 동시에 깨질 수 있다
- 보호해야 하는 것은 각 reservation row가 아니라 **집계 결과**다

### 전환: guard row 또는 atomic conditional update

```sql
UPDATE room_type_day_guard
SET reserved_qty = reserved_qty + :qty
WHERE room_type_id = :room_type_id
  AND stay_day = :stay_day
  AND reserved_qty + :qty <= capacity;
```

영향받은 row 수가 `1`이면 승인, `0`이면 sold out이다.

이 패턴의 핵심은:

- capacity invariant를 `(room_type_id, stay_day)` guard row 하나로 내린다
- detail reservation insert는 guard update 성공 뒤에만 허용한다
- 필요하면 reconciliation으로 guard row와 detail row를 주기적으로 대조한다

여기서 중요한 전환은 JPA를 버리는 것이 아니라, **detail row lock에서 aggregate guard lock으로 사고방식을 바꾸는 것**이다.

## 언제 native SQL이나 JDBC로 내려야 하나

다음 조건이면 `@Lock(PESSIMISTIC_WRITE)` 추상화만으로는 부족한 경우가 많다.

- `SKIP LOCKED`, `NOWAIT`, `FOR UPDATE OF`, optimizer hint 같은 vendor 문법이 필요하다
- guard row를 `upsert -> exact PK/range lock` 순서로 확보해야 한다
- `old scope ∪ new scope` ordered lock처럼 lock 순서를 SQL로 명시해야 한다
- overlap probe가 실제로 어떤 index path를 탔는지 `EXPLAIN`과 함께 검증해야 한다
- update count, SQLSTATE, errno를 그대로 business branch에 연결해야 한다

이럴 때 native SQL/JDBC로 내려가면 얻는 것은 "더 강한 락"이 아니라, **정확한 arbitration surface와 관측 가능한 lock footprint**다.

## 짧은 의사결정표

| 증상 | detail row `PESSIMISTIC_WRITE`에서 보이는 착시 | 보통의 전환 |
|---|---|---|
| `find...ForUpdate()`가 비어 있으면 안전하다고 생각함 | empty result는 잠근 entity가 없다는 뜻이다 | `UNIQUE`, exclusion constraint, pre-seeded guard row |
| overlap query를 잠갔으니 double booking이 안 난다고 생각함 | 잠근 것은 현재 읽힌 booking row일 뿐이다 | exclusion constraint, slot + unique, guard row |
| 활성 row를 다 잠그고 합산했으니 capacity가 안전하다고 생각함 | 집계 규칙은 detail row 집합 바깥에 있다 | guard row, ledger, atomic conditional update |
| JPA `@Lock`만 쓰면 queue claim도 portable하다고 생각함 | vendor lock clauses와 plan 통제는 JPA가 가린다 | native SQL, JDBC, MyBatis |

## 한 줄 정리

JPA `PESSIMISTIC_WRITE`는 existing row serialization에는 좋지만, `없음`이나 range/set invariant를 그대로 잠가 주지는 않는다. 그 규칙이 exact key면 제약조건으로, aggregate/range면 guard row나 constraint로, lock surface가 vendor 문법에 달리면 native SQL로 옮겨야 한다.
