# Engine Fallbacks for Overlap Enforcement

> 한 줄 요약: PostgreSQL은 exclusion constraint로 continuous overlap을 직접 중재하기 쉽지만, MySQL은 같은 규칙을 slot row, next-key locking 보조, guard row/ledger 같은 다른 arbitration surface로 내려야 phantom-safe하게 유지된다.

**난이도: 🔴 Advanced**

관련 문서:

- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)
- [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md)
- [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
- [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md)
- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)

retrieval-anchor-keywords: overlap enforcement across engines, PostgreSQL vs MySQL overlap, exclusion constraint fallback, phantom-safe overlap rule, slotization booking, slot row unique index, next-key locking overlap, guard row booking, reservation ledger overlap, active predicate arbitration, temporal overlap MySQL, continuous interval fallback, range invariant engine support, overlap probe composite index, booking lock footprint, interval predicate btree mismatch, guard row scope, room day guard, multi-day booking guard, canonical lock ordering, ordered guard row upsert, pre-seeded guard row

## 핵심 개념

겹침 규칙은 "조회 결과가 비어 있으면 insert"가 아니라,  
**어느 저장 surface가 충돌을 중재할지**를 정하는 문제다.

같은 규칙이라도 엔진마다 첫 선택지가 다르다.

| 상황 | PostgreSQL 우선 선택 | MySQL 우선 선택 | 이유 |
|---|---|---|---|
| 같은 테이블 안의 continuous interval 겹침 금지 | exclusion constraint + range type | slotization 또는 guard row | PostgreSQL은 range overlap을 제약으로 직접 표현할 수 있지만, MySQL은 같은 의미의 exclusion 제약이 없다 |
| discrete bucket 겹침 금지 | slot row + unique도 가능 | slot row + unique | 엔진 공통으로 가장 설명 가능하고 예측 가능하다 |
| capacity/합계 규칙 | guard row / ledger | guard row / ledger | pairwise overlap 제약만으로 합계 규칙은 닫히지 않는다 |
| 여러 테이블/외부 시스템을 합친 점유 규칙 | materialized arbitration table 또는 ledger | materialized arbitration table 또는 ledger | 어느 쪽도 "임의의 다중 테이블 predicate"를 제약 하나로 닫지는 못한다 |

핵심 차이는 기능 이름이 아니라 이거다.

- PostgreSQL: "겹침" 자체를 제약으로 표현하기 좋다
- MySQL: "겹침"을 바로 표현하기보다, 충돌 surface를 slot/key/guard row로 재모델링해야 안전하다

## 깊이 들어가기

### 1. PostgreSQL에서는 exclusion constraint가 기준선이다

같은 자원에 대해 `[start_at, end_at)` 구간이 겹치면 안 되는 문제라면 PostgreSQL은 가장 직접적인 수단을 준다.

- equality dimension: `room_id`, `device_id`, `(tenant_id, product_id)` 같은 자원 키
- range expression: `tstzrange(start_at, end_at, '[)')`
- active predicate: `status IN ('HELD', 'CONFIRMED', 'BLACKOUT')`

이 조합이 한 테이블 안에서 닫히면 exclusion constraint가 기본값이다.  
애플리케이션의 absence check를 DB arbitration으로 옮기기 가장 쉽기 때문이다.

하지만 PostgreSQL에서도 아래 경우는 fallback이 필요하다.

- 시간이 5분, 15분 단위로 이미 discrete한 경우
- capacity가 1이 아니라 N인 경우
- 점유 규칙이 여러 테이블이나 외부 시스템을 합쳐야 하는 경우

즉 PostgreSQL도 만능은 아니고, "pairwise continuous overlap"에 특히 강하다.

### 2. MySQL은 exclusion constraint를 그대로 옮길 수 없다

MySQL InnoDB는 next-key/gap lock으로 phantom을 줄일 수 있지만,  
그건 **스캔한 인덱스 범위를 잠그는 것**이지 "구간 overlap 연산자"를 제약으로 거는 것이 아니다.

즉 `(room_id, start_at)`와 `(room_id, end_at)`는 같은 overlap SQL에도 다른 락 표면을 만든다.  
어떤 composite index 모양이 어떤 false-positive scan과 lock footprint를 만드는지는 [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md)에서 따로 비교한다.

그래서 아래 두 문장은 같은 뜻이 아니다.

- PostgreSQL: `EXCLUDE USING gist (... WITH &&)`
- MySQL: `SELECT ... FOR UPDATE WHERE start_at < :end AND end_at > :start`

MySQL 쪽의 함정:

- overlap predicate는 보통 두 경계(`start_at`, `end_at`)와 상태 predicate를 함께 본다
- InnoDB는 추상적인 overlap 규칙이 아니라 실제 스캔한 인덱스 range만 잠근다
- 인덱스가 어긋나거나 optimizer가 다른 경로를 타면 잠금 범위가 달라진다
- `READ COMMITTED`에서는 gap/next-key 보호를 기대하기 어려워진다

즉 MySQL에서 continuous overlap을 base booking table의 locking read 하나로 끝내려 하면  
"너무 넓게 잠그거나", "예상보다 약하게 잠그거나", "경로별로 다른 락 범위를 갖는" 문제가 생기기 쉽다.

### 3. slotization은 가장 portable한 fallback이다

시간이 business resolution으로 잘릴 수 있으면 overlap을 continuous interval로 다루지 말고 slot row로 환원하는 편이 낫다.

예:

- 15분 단위 회의실 예약
- 1일 단위 숙박 재고
- 30분 단위 장비 대여

패턴:

1. 예약 구간을 slot 목록으로 펼친다
2. `resource_id + slot_start`를 unique key로 잡는다
3. 각 slot row insert를 같은 트랜잭션으로 묶는다
4. duplicate key가 나면 "이미 점유됨"으로 번역한다

장점:

- PostgreSQL/MySQL 공통 패턴이라 운영 설명이 쉽다
- next-key locking 세부 차이에 덜 의존한다
- active 상태를 "slot row가 존재하는가"로 단순화할 수 있다

단점:

- row 수가 늘어난다
- bucket보다 더 세밀한 실제 시간 의미는 버린다
- bucket 경계 규칙을 먼저 합의해야 한다

### 4. next-key locking은 주력 설계보다 보조 전술에 가깝다

MySQL에서 next-key locking은 쓸 수 있지만, 다음 조건을 만족할 때만 "phantom-safe 보조"로 본다.

- 트랜잭션이 `REPEATABLE READ` 또는 `SERIALIZABLE`에 있다
- locking read가 실제 conflict surface와 같은 인덱스 prefix를 탄다
- 모든 쓰기 경로가 같은 probe SQL과 같은 인덱스를 사용한다
- insert 전에 반드시 그 locking read가 먼저 수행된다

예를 들어 discrete slot table에서는 다음이 비교적 자연스럽다.

- `SELECT ... FOR UPDATE`로 해당 slot range를 잠근다
- 또는 곧바로 unique slot insert로 충돌을 중재한다

반면 continuous interval의 base booking table은 애매하다.

- `start_at < :end`는 잠금 범위를 넓게 잡기 쉽다
- `end_at > :start`는 같은 B-tree 상에서 바로 잠금 범위가 되지 않는다
- 상태 predicate(`ACTIVE`, `HELD`)까지 섞이면 scan surface와 business predicate가 벌어진다

그래서 next-key locking은 "MySQL도 exclusion constraint 대체가 가능하다"는 뜻이 아니라,  
**fallback 모델이 충분히 단순할 때만 쓸 수 있는 락 도구**로 보는 편이 안전하다.

### 5. guard row는 continuous interval과 capacity 규칙을 한 키로 직렬화한다

slotization이 너무 비싸거나 bucket이 어색하면, 충돌 가능성이 있는 쓰기를 guard row에 모은다.

대표 패턴:

- `room_guard(room_id)` 한 row를 `SELECT ... FOR UPDATE`
- 또는 `(room_id, booking_day)` 단위 guard row를 잠가서 contention 범위를 줄임
- guard row를 잡은 뒤 overlap recheck + insert를 같은 트랜잭션에서 수행

이 패턴이 phantom-safe한 이유는 단순하다.  
같은 자원을 건드리는 모든 쓰기가 먼저 같은 guard row를 잠그면, overlap 판정이 사실상 직렬화되기 때문이다.

주의할 점:

- 모든 경로가 guard row를 반드시 거쳐야 한다
- 여러 day/resource를 잠가야 하면 canonical order를 강제해야 한다
- guard row는 binary overlap뿐 아니라 capacity/count 규칙에도 확장하기 쉽다

여기서 guard row의 granularity를 `(room_id)`로 둘지 `(room_id, booking_day)`로 둘지, 그리고 multi-day reschedule에서 old/new scope union을 어떻게 잠글지는 [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)에서 따로 본다.

즉 MySQL에서 guard row는 "복잡한 predicate lock 흉내"보다 현실적인 기본기다.

### 6. ledger/materialized arbitration table은 엔진 차이를 더 줄여 준다

점유 규칙이 여러 테이블, 여러 상태, 외부 시스템까지 엮이면 base table에 직접 걸기보다  
별도 arbitration table을 두는 편이 두 엔진 모두에서 명확하다.

예:

- `resource_reservation_ledger`
- `active_booking_slot`
- `campaign_capacity_guard`

원칙:

- 읽기용 booking/history table과 쓰기 arbitration table을 분리한다
- overlap/capacity 판단은 arbitration table만 본다
- cleanup/backfill/reconciliation도 이 테이블을 기준으로 설계한다

이렇게 하면 "엔진마다 base table locking semantics가 다르다"는 문제를 줄일 수 있다.

## 엔진별 선택 가이드

### PostgreSQL을 쓸 때

1. continuous pairwise overlap이면 exclusion constraint를 먼저 검토한다
2. discrete bucket이면 slotization이 더 단순한지 비교한다
3. capacity/합계 규칙이면 guard row나 ledger로 내려간다
4. 여러 테이블 predicate를 읽어야 하면 serializable + retry 또는 materialized arbitration table을 검토한다

### MySQL을 쓸 때

1. discrete bucket으로 환원 가능하면 slotization을 기본값으로 둔다
2. continuous interval이면 base table next-key locking부터 시작하지 말고 guard row 범위를 먼저 설계한다
3. 정말 locking read를 쓴다면 `REPEATABLE READ`와 인덱스 prefix를 고정하고, 실행 계획 드리프트를 운영 지표로 본다
4. capacity/합계 규칙은 처음부터 guard row/ledger를 사용한다

## 실전 시나리오

### 시나리오 1. 회의실 예약

- PostgreSQL: `room_id + tstzrange(start_at, end_at, '[)')` exclusion constraint
- MySQL: 15분 단위로 자를 수 있으면 `room_slot_claim(room_id, slot_start)` unique
- MySQL에서 bucket이 불가능하면 `room_guard(room_id, booking_day)`를 먼저 잠그고 overlap recheck

핵심:

- PostgreSQL은 overlap을 직접 표현
- MySQL은 overlap을 slot 또는 guard key로 번역

### 시나리오 2. 장비 대여 + 점검 buffer

- PostgreSQL: blocked range를 `tstzrange(start_at, end_at + buffer, '[)')`로 직접 모델링
- MySQL: 실제 점유 구간을 slot row로 펼치거나, `(device_id, calendar_day)` guard row를 잠근 뒤 `buffer`를 포함한 recheck

핵심:

- 사용자에게 보이는 `rent_end`와 실제 blocked range를 분리해야 한다
- MySQL locking read는 "buffer까지 포함한 구간"을 안정적으로 잠그는 surface를 따로 만들어야 한다

### 시나리오 3. capacity가 1보다 큰 재고/좌석

- PostgreSQL: exclusion constraint만으로는 부족하고 `inventory_guard`나 ledger가 필요
- MySQL: 처음부터 같은 guard/ledger 패턴 사용

핵심:

- pairwise overlap 도구와 sum/count 도구를 섞어 쓰지 말아야 한다

## 코드로 보기

```sql
-- PostgreSQL: continuous overlap을 직접 제약으로 건다
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE room_booking
ADD CONSTRAINT room_booking_no_overlap
EXCLUDE USING gist (
  room_id WITH =,
  tstzrange(start_at, end_at, '[)') WITH &&
)
WHERE (status IN ('HELD', 'CONFIRMED', 'BLACKOUT'));
```

```sql
-- PostgreSQL/MySQL 공통: slotization
CREATE TABLE room_slot_claim (
  room_id BIGINT NOT NULL,
  slot_start TIMESTAMP NOT NULL,
  booking_id BIGINT NOT NULL,
  PRIMARY KEY (room_id, slot_start)
);
```

```sql
-- MySQL fallback: guard row를 먼저 잠그고 overlap 판정을 직렬화
CREATE TABLE room_booking_guard (
  room_id BIGINT NOT NULL,
  guard_day DATE NOT NULL,
  PRIMARY KEY (room_id, guard_day)
);
```

```text
MySQL guard-row protocol
1. 예약이 닿는 guard_day 목록 계산
2. (room_id, guard_day)를 정렬된 순서로 SELECT ... FOR UPDATE
3. 같은 active predicate로 overlap recheck
4. 충돌 없으면 booking insert
5. commit
```

## 운영 guardrail 체크리스트

- `[start, end)` 반개구간과 timezone 기준을 먼저 고정한다
- active predicate를 앱 조회, arbitration table, cleanup job에서 동일하게 해석한다
- MySQL에서 next-key locking을 주장한다면 격리수준이 `REPEATABLE READ` 이상인지 확인한다
- MySQL locking read는 intended index를 강제하거나 최소한 실행 계획 drift를 모니터링한다
- `INSERT` 자체가 phantom-safe check를 대신해 주지 않는다고 가정한다
- slotization이면 bucket 폭, row explosion, cleanup 정책을 같이 문서화한다
- guard row면 lock ordering, deadlock retry, reconciliation query를 같이 설계한다
- conflict를 예외가 아니라 예상 가능한 중재 결과로 번역한다

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| PostgreSQL exclusion constraint | continuous overlap을 가장 직접적으로 표현한다 | 엔진 종속적이고 pairwise 규칙 중심이다 | PostgreSQL 단일 테이블 overlap |
| slotization | 엔진 공통, 테스트 용이, duplicate key로 중재 가능 | row 수 증가, bucket 해상도 제약 | 시간이 discrete bucket으로 자연스럽게 나뉠 때 |
| MySQL next-key locking probe | 추가 테이블 없이 잠금 전술을 쓸 수 있다 | 인덱스/격리수준/계획에 민감하고 설명이 어렵다 | 이미 단순한 indexed range로 환원된 경우만 |
| guard row / ledger | overlap과 capacity 모두에 적용 가능하다 | 모든 경로 강제가 필요하고 contention이 생길 수 있다 | continuous interval, capacity, cross-table 규칙 |

## 꼬리질문

> Q: MySQL에서도 `SELECT ... FOR UPDATE`로 overlap query를 잠그면 exclusion constraint랑 같은가요?
> 의도: 락 범위와 제약 의미를 구분하는지 확인
> 핵심: 아니다. MySQL은 스캔한 인덱스 range를 잠그는 것이고, overlap 연산자 자체를 제약으로 거는 것이 아니다.

> Q: 왜 MySQL에서는 slotization을 더 자주 권하나요?
> 의도: portable arbitration surface를 이해하는지 확인
> 핵심: unique key 충돌은 엔진 간 의미가 안정적이고, next-key locking보다 운영 설명과 테스트가 쉽다.

> Q: PostgreSQL인데도 guard row를 쓰는 경우가 있나요?
> 의도: exclusion constraint의 적용 범위를 과대평가하지 않는지 확인
> 핵심: capacity/count 규칙이나 다중 테이블 arbitration처럼 pairwise overlap을 넘어가는 문제에서는 guard row/ledger가 더 직접적이다.

## 한 줄 정리

겹침 규칙이 phantom-safe해야 할 때 PostgreSQL은 overlap 자체를 제약으로 표현하고, MySQL은 같은 규칙을 slot key나 guard row 같은 별도 arbitration surface로 번역하는 쪽이 더 안전하다.
