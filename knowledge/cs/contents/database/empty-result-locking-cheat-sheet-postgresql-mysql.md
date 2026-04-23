# Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL

> 한 줄 요약: `SELECT ... FOR UPDATE`는 **이미 있는 row**를 잠그는 데는 강하지만, `0 row`가 나온 absence check는 PostgreSQL에서는 보통 보호하지 못하고, MySQL도 `REPEATABLE READ`의 일부 indexed range에서만 좁게 보호할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [PostgreSQL vs MySQL Isolation Cheat Sheet](./postgresql-vs-mysql-isolation-cheat-sheet.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [MySQL Empty-Result Locking Reads](./mysql-empty-result-locking-reads.md)
- [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md)
- [JPA `PESSIMISTIC_WRITE`의 범위 잠금 한계와 전환 기준](./range-locking-limits-jpa.md)
- [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)
- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)

retrieval-anchor-keywords: empty result locking cheat sheet, 0 row for update, select for update zero rows, select for update empty result postgres mysql, absence check for update, missing row lock myth, postgresql select for update empty result, mysql select for update empty result, postgres absence check race, mysql gap lock zero rows, beginner empty-result locking, 없으면 insert race, 빈 결과 for update, 없으면 insert 동시성

## 핵심 개념

가장 먼저 잡아야 할 그림은 단순하다.

- `FOR UPDATE`는 기본적으로 **찾아낸 row**를 잠근다
- 결과가 `0 row`면 PostgreSQL은 보통 잠글 row가 없다
- MySQL InnoDB는 `REPEATABLE READ`에서 가끔 **스캔한 인덱스 gap**을 잠가 insert를 막을 수 있다

즉 `0 row`를 봤을 때 안전한 기본 해석은 이것이다.

> "없는 것을 잠갔다"가 아니라, 엔진에 따라 **아무것도 못 잠갔거나**, **스캔한 인덱스 구간만 좁게 막았을 수 있다.**

초보자 기준으로는 이 문장만 기억해도 큰 실수를 많이 줄일 수 있다.

## 먼저 보는 한 장 표

| 엔진 / 격리수준 | empty-result `FOR UPDATE`가 absence check를 보호하나 | 초보자 기억법 |
|---|---|---|
| PostgreSQL `READ COMMITTED` | 보통 아니오 | 결과로 나온 row만 잠근다. `0 row`면 "없음" 자체는 잠기지 않는다. |
| PostgreSQL `REPEATABLE READ` | 보통 아니오 | snapshot은 더 안정적이지만, missing row를 row lock으로 보호해 주지는 않는다. |
| PostgreSQL `SERIALIZABLE` | 경우에 따라 예, 하지만 **retry가 전제** | 안전성은 `FOR UPDATE`가 empty result를 잠가서가 아니라, 직렬화 불가능한 패턴을 DB가 abort하기 때문이다. |
| MySQL `READ COMMITTED` | 보통 아니오 | search gap lock을 기대하면 안 된다. `0 row`면 새 insert를 못 막는다고 보는 편이 안전하다. |
| MySQL `REPEATABLE READ` | 때때로 예, 하지만 **좁고 엔진 의존적** | indexed range를 스캔했다면 next-key/gap lock이 insert를 막을 수 있다. 그래도 "논리적 부재 전체"를 잠근다고 읽으면 안 된다. |

한 줄로 줄이면 이렇다.

- PostgreSQL: `0 row FOR UPDATE`를 absence lock으로 읽지 않는다
- MySQL: `REPEATABLE READ`에서만 일부 range가 막힐 수 있지만, portable rule로 쓰지 않는다

## 예제 1. "발급 이력이 없으면 insert"

가장 흔한 패턴은 이렇다.

```sql
BEGIN;

SELECT 1
FROM coupon_issue
WHERE coupon_id = :coupon_id
  AND member_id = :member_id
FOR UPDATE;
-- 0 rows

INSERT INTO coupon_issue(coupon_id, member_id)
VALUES (:coupon_id, :member_id);

COMMIT;
```

의도는 단순하다.

1. 이미 발급한 이력이 있는지 본다
2. 없으면 insert 한다

하지만 엔진별로 안전성은 다르다.

| 경우 | 해석 |
|---|---|
| PostgreSQL `READ COMMITTED` / `REPEATABLE READ` | 둘 다 `0 row`면 잠근 row가 없다. 다른 트랜잭션도 같은 값을 insert할 수 있다. |
| PostgreSQL `SERIALIZABLE` | 둘 다 진행했다가 나중에 한쪽이 abort될 수 있다. 애플리케이션이 whole-transaction retry를 해야 안전하다. |
| MySQL `READ COMMITTED` | 보통 안전하지 않다. 새 row insert를 막는 range protection을 기대하면 안 된다. |
| MySQL `REPEATABLE READ` | 같은 indexed key probe에서는 막히는 것처럼 보일 수 있다. 그래도 최종 보장은 `UNIQUE`가 맡아야 한다. |

이 경우의 beginner-safe 정답은 거의 항상 같다.

```sql
ALTER TABLE coupon_issue
ADD CONSTRAINT uq_coupon_issue_coupon_member
UNIQUE (coupon_id, member_id);
```

핵심은 "없음을 잠그는 것"이 아니라 **같은 key가 write 시점에 반드시 충돌하게 만드는 것**이다.

## 예제 2. "겹치는 예약이 없으면 insert"

이 패턴은 더 위험하다.

```sql
SELECT id
FROM room_booking
WHERE room_id = :room_id
  AND status IN ('HELD', 'CONFIRMED')
  AND start_at < :requested_end
  AND end_at > :requested_start
FOR UPDATE;
-- 0 rows
```

많은 팀이 이 결과를 보고 이렇게 생각한다.

> "겹치는 예약이 없다는 사실을 잠갔으니 이제 insert해도 되겠네."

이 해석은 PostgreSQL에서는 틀리고, MySQL에서도 자주 과장된다.

| 엔진 | 왜 위험한가 |
|---|---|
| PostgreSQL | `FOR UPDATE`가 잠그는 것은 읽힌 row다. empty result는 overlap predicate 자체를 잠그지 않는다. |
| MySQL `READ COMMITTED` | gap protection이 일반적으로 없어서 새 overlap insert를 막지 못할 수 있다. |
| MySQL `REPEATABLE READ` | 어떤 인덱스를 타느냐에 따라 scanned range insert는 막을 수 있다. 하지만 overlap predicate 전체를 잠근 것은 아니다. |

초보자 기억법:

- exact duplicate는 **key 문제**
- overlap은 **predicate/range 문제**

그래서 overlap은 `0 row FOR UPDATE` 하나로 닫기보다 아래 쪽으로 내려가는 편이 안전하다.

- PostgreSQL: exclusion constraint, `SERIALIZABLE` + retry, guard row
- MySQL / cross-engine: slot row + `UNIQUE`, guard row

## 언제는 괜찮고, 언제는 안 괜찮나

| 상황 | `FOR UPDATE`로 시작해도 되나 | 더 좋은 기본 선택 |
|---|---|---|
| 이미 존재하는 주문 row를 한 명만 수정해야 함 | 예 | `FOR UPDATE` |
| "이 이메일이 아직 없다"를 믿고 insert | 아니오 | `UNIQUE`, PK, upsert |
| "이 시간대에 예약이 없다"를 믿고 insert | 아니오 | exclusion constraint, slot row, guard row |
| PostgreSQL에서 absence check 자체를 직렬화해야 함 | `SERIALIZABLE`이면 가능 | 단, retry를 whole transaction 경계에서 반드시 구현 |
| MySQL `REPEATABLE READ`에서 indexed range insert를 잠깐 막고 싶음 | 제한적으로 예 | 그래도 핵심 invariant는 constraint/guard surface로 표현 |

핵심 판단 기준은 이것이다.

> 내 규칙이 "기존 row 하나의 소유권" 문제인가, 아니면 "`없음`/범위/집합" 문제인가?

첫 번째면 `FOR UPDATE`가 잘 맞는다.  
두 번째면 보통 다른 저장 surface가 필요하다.

## 자주 하는 오해

- `0 row`였으니 아무 일도 안 일어났다
  - PostgreSQL에서는 이 해석이 대체로 맞다.
  - MySQL `REPEATABLE READ`에서는 scanned gap lock이 남을 수도 있다.
- `0 row`였으니 없다는 사실이 잠겼다
  - 두 엔진 모두에서 일반 규칙으로는 틀리다.
- `WHERE` 절을 썼으니 그 조건 전체가 잠겼다
  - 잠금 단위는 보통 `WHERE` 절이 아니라 **실제로 읽힌 row** 또는 **스캔한 인덱스 범위**다.
- MySQL에서 테스트가 통과했으니 PostgreSQL로 옮겨도 된다
  - 특히 틀리기 쉽다. MySQL RR의 next-key 체감을 PostgreSQL `FOR UPDATE`에 그대로 기대하면 안 된다.

## 빠른 결정 가이드

- exact duplicate 방지면: `UNIQUE` / PK를 먼저 본다
- continuous interval overlap이면: PostgreSQL은 exclusion constraint를 먼저 본다
- 엔진 공통으로 설명 가능한 booking/capacity path가 필요하면: slot row나 guard row를 먼저 본다
- 이미 존재하는 row를 선점해야 하면: `FOR UPDATE`가 잘 맞는다
- PostgreSQL `SERIALIZABLE`을 쓰면: "막아 준다"보다 "충돌 시 한쪽을 abort하고 retry를 요구한다"로 이해한다

## 한 줄 정리

`SELECT ... FOR UPDATE`는 existing row lock에는 강하지만 empty-result absence check의 만능 해법은 아니다. PostgreSQL에서는 보통 안 되고, MySQL도 `REPEATABLE READ`의 좁은 index-range 상황에서만 일부 통할 뿐이므로, 정확한 안전성은 제약조건이나 별도 arbitration surface로 표현하는 편이 낫다.
