# Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL

> 한 줄 요약: `SELECT ... FOR UPDATE`는 이미 찾은 row를 잠그는 데는 강하지만, `0 row`가 나온 absence check는 PostgreSQL에서는 보통 보호하지 못하고, MySQL도 `REPEATABLE READ`의 일부 indexed range에서만 좁게 보조한다.

**난이도: 🟢 Beginner**

관련 문서:

- [PostgreSQL vs MySQL Isolation Cheat Sheet](./postgresql-vs-mysql-isolation-cheat-sheet.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [MySQL Empty-Result Locking Reads](./mysql-empty-result-locking-reads.md)
- [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md)
- [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)
- [Spring 트랜잭션 기초](../spring/spring-transactional-basics.md)
- [Inventory Reservation System Design](../system-design/inventory-reservation-system-design.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: empty result locking cheat sheet, 0 row for update, select for update zero rows, select for update basics, for update 처음 배우는데, 0 row for update 뭐예요, absence check for update, missing row lock myth, postgresql select for update empty result, mysql select for update empty result, postgres absence check race, mysql gap lock zero rows, for update race timeline, 없으면 insert race, 빈 결과 for update

## 핵심 개념

먼저 머릿속에 세 칸만 만든다.

- 이미 있는 row를 선점하는 문제
- "지금은 없다"는 부재를 믿고 insert 하는 문제
- 시간대나 조건 집합 같은 범위를 비워 둔 채 insert 하는 문제

`FOR UPDATE`가 가장 잘 맞는 것은 첫 번째다.
두 번째와 세 번째는 `0 row`가 나오는 순간 엔진별 차이가 커진다.

- PostgreSQL: `0 row`면 보통 잠근 row가 없다
- MySQL `REPEATABLE READ`: 스캔한 인덱스 gap이 잠길 수는 있다
- 두 엔진 공통: `WHERE` 조건 전체가 잠겼다고 읽으면 위험하다

초보자용 기억법은 이 한 문장이다.

> `FOR UPDATE`는 "없는 것"을 잠그는 기능이 아니라, 기본적으로 "읽어 낸 것"을 잠그는 기능이다.

## 30초 문제 분류 카드

| 지금 하려는 일 | `0 row FOR UPDATE`에 기대도 되나 | 기본 해법 |
|---|---|---|
| 기존 주문 row 1개를 한 명만 수정 | 예 (row가 있으면) | `FOR UPDATE` |
| "없으면 insert" exact duplicate 방지 | 아니오 | `UNIQUE`/PK/upsert |
| "겹치는 예약 없음" overlap 방지 | 아니오 | exclusion constraint / slot row / guard row |

이 표에서 두 번째, 세 번째에 해당하면 lock 문법보다 먼저 "충돌 truth를 어디에 저장할지"를 정한다.

## 한눈에 보기

| 엔진 / 격리수준 | `0 row FOR UPDATE`가 absence check를 보호하나 | 입문자 기억법 |
|---|---|---|
| PostgreSQL `READ COMMITTED` | 보통 아니오 | 결과가 없으면 잠근 row도 없다 |
| PostgreSQL `REPEATABLE READ` | 보통 아니오 | snapshot은 유지돼도 missing row lock은 아니다 |
| PostgreSQL `SERIALIZABLE` | 조건부 예 | empty result를 잠가서가 아니라, 충돌 시 한쪽을 abort하기 때문이다 |
| MySQL `READ COMMITTED` | 보통 아니오 | search gap lock을 기대하면 안 된다 |
| MySQL `REPEATABLE READ` | 때때로 좁게 예 | 같은 indexed range를 같은 경로로 스캔했을 때만 일부 insert를 막을 수 있다 |

안전한 기본 해석은 늘 보수적으로 잡는다.

- PostgreSQL: `0 row FOR UPDATE`는 absence lock이 아니다
- MySQL: `REPEATABLE READ`의 성공 경험은 보너스일 뿐, 설계 계약으로 쓰면 안 된다

## 언제 보호되고 언제 안 되나

| 상황 | `FOR UPDATE`를 1차 도구로 써도 되나 | 더 안전한 기본 선택 |
|---|---|---|
| 이미 존재하는 주문 row 하나를 한 명만 수정해야 함 | 예 | `FOR UPDATE` |
| "이 이메일이 아직 없다"를 믿고 insert | 아니오 | `UNIQUE`, PK, upsert |
| "이 시간대에 예약이 없다"를 믿고 insert | 아니오 | exclusion constraint, slot row, guard row |
| PostgreSQL에서 absence check를 직렬화해야 함 | `SERIALIZABLE`이면 가능 | 단, whole-transaction retry가 필수 |
| MySQL RR에서 동일 indexed probe를 잠깐 직렬화하고 싶음 | 제한적으로만 예 | 핵심 invariant는 여전히 constraint나 guard surface로 닫는다 |

판단 질문은 하나면 충분하다.

> 지금 풀려는 문제가 "기존 row 하나의 소유권"인가, 아니면 "`없음`이나 범위"를 믿는 문제인가?

앞쪽이면 `FOR UPDATE`가 맞고, 뒤쪽이면 다른 저장 surface가 필요할 가능성이 크다.

## 30초 타임라인: 왜 race가 생기나

`SELECT ... FOR UPDATE`가 `0 row`를 반환한 두 트랜잭션은 둘 다 "잠근 대상 없음" 상태로 다음 단계로 갈 수 있다.

| 시점 | 트랜잭션 T1 | 트랜잭션 T2 |
|---|---|---|
| t1 | `SELECT ... FOR UPDATE -> 0 rows` |  |
| t2 |  | `SELECT ... FOR UPDATE -> 0 rows` |
| t3 | `INSERT` 시도 | `INSERT` 시도 |
| t4 | (제약 없으면 둘 다 성공 가능) | (제약 없으면 둘 다 성공 가능) |

그래서 exact duplicate 경로의 핵심은 lock이 아니라 write 시점 충돌(`UNIQUE`)이다.

## 예제 1. "없으면 insert" exact duplicate 체크

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

두 트랜잭션이 동시에 실행되면 둘 다 `0 row`를 볼 수 있다.

- PostgreSQL `READ COMMITTED` / `REPEATABLE READ`: absence 자체를 잠그지 못하므로 둘 다 `INSERT`까지 갈 수 있다
- MySQL `READ COMMITTED`: 마찬가지로 새 insert를 막는다고 기대하면 안 된다
- MySQL `REPEATABLE READ`: 같은 indexed key probe에서는 막히는 것처럼 보일 수 있지만, 설계 핵심으로 삼기엔 엔진 의존성이 크다

이 경우 beginner-safe 정답은 row lock이 아니라 제약조건이다.

```sql
ALTER TABLE coupon_issue
ADD CONSTRAINT uq_coupon_issue_coupon_member
UNIQUE (coupon_id, member_id);
```

핵심은 "`없음`을 잠그기"가 아니라, 같은 key가 write 시점에 반드시 충돌하게 만드는 것이다.

## 예제 2. "겹치는 예약이 없으면 insert" overlap 체크

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

이 결과를 보고 "겹치는 예약이 없다는 사실을 잠갔다"고 이해하면 대부분 틀린다.

- PostgreSQL: empty result는 overlap predicate 자체를 잠그지 않는다
- MySQL `READ COMMITTED`: 새 overlap insert가 그대로 통과할 수 있다
- MySQL `REPEATABLE READ`: 스캔한 인덱스 구간 일부는 막을 수 있어도, overlap 규칙 전체를 잠근 것은 아니다

이 문제는 single-row lock 문제가 아니라 predicate/range 문제다. 그래서 보통은 아래 쪽이 더 안전하다.

- PostgreSQL single-table overlap: exclusion constraint
- PostgreSQL absence serialization: `SERIALIZABLE` + whole-transaction retry
- MySQL 또는 cross-engine: slot row + `UNIQUE`, guard row

초보자 기억법:

- exact duplicate는 key 문제
- overlap booking은 predicate 문제

## 흔한 오해와 함정

- `0 row`였으니 아무 일도 안 잠겼다
  - PostgreSQL에서는 대체로 맞다
  - MySQL `REPEATABLE READ`에서는 scanned gap lock이 남을 수 있다
- `WHERE`를 썼으니 그 조건 전체가 잠겼다
  - 실제 잠금 단위는 보통 읽힌 row나 스캔한 인덱스 범위다
- MySQL에서 테스트가 통과했으니 PostgreSQL도 같을 것이다
  - 특히 틀리기 쉽다. MySQL RR의 next-key 체감을 PostgreSQL row lock에 옮기면 안 된다
- PostgreSQL `SERIALIZABLE`이면 retry 코드가 필요 없다
  - 아니다. 안전성은 abort + retry 계약으로 나온다

## 다음 단계 라우팅

- exact duplicate(`없으면 insert`)를 먼저 닫아야 하면 -> [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- overlap/예약 충돌 모델을 고르려면 -> [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)
- PostgreSQL에서 absence를 직렬화하고 싶으면 -> [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- MySQL에서 empty-result gap footprint를 더 자세히 보려면 -> [MySQL Empty-Result Locking Reads](./mysql-empty-result-locking-reads.md)

## 더 깊이 가려면

- [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md): 왜 RC 전환 후 같은 코드가 갑자기 새는지 이어서 본다
- [Spring 트랜잭션 기초](../spring/spring-transactional-basics.md): 이 차이가 애플리케이션 transaction boundary와 어떻게 이어지는지 연결한다
- [Inventory Reservation System Design](../system-design/inventory-reservation-system-design.md): 예약/재고 시스템에서 absence check를 어떤 arbitration surface로 바꾸는지 큰 그림을 본다

## 면접/시니어 질문 미리보기

- PostgreSQL에서 `0 row FOR UPDATE`가 왜 unsafe한가
  - 잠글 row가 없고, absence 자체를 row lock으로 표현하지 않기 때문이다
- MySQL `REPEATABLE READ`에서 왜 가끔 되는 것처럼 보이나
  - 같은 indexed range에 next-key/gap lock이 잡히면 일부 insert가 막히기 때문이다
- exact duplicate와 overlap booking의 기본 해법이 왜 다른가
  - 전자는 concrete key 충돌로 닫히고, 후자는 predicate/range 충돌을 별도 surface로 내려야 하기 때문이다

## 한 줄 정리

`SELECT ... FOR UPDATE`는 existing row lock에는 강하지만, `0 row` absence check는 PostgreSQL에서는 보통 보호하지 못하고 MySQL도 일부 indexed range에서만 좁게 보조하므로, 핵심 안전성은 제약조건이나 별도 arbitration surface로 표현하는 편이 낫다.
