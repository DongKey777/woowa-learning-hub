# Phantom-Safe Booking Patterns Primer

> 한 줄 요약: booking overlap check를 phantom-safe하게 만들려면 "빈 시간대인지 조회"를 버리고, `unique-slot`, exclusion constraint, guard row 중 하나를 write-time arbitration surface로 선택해야 한다.

**난이도: 🟡 Intermediate**

관련 문서:

- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)
- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- [Hot-Path Slot Arbitration Choices](./hot-path-slot-arbitration-choices.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md)
- [Slotization Precheck Queries for Overlaps, Rounding Collisions, and DST Boundaries](./slotization-precheck-overlap-rounding-dst.md)

retrieval-anchor-keywords: phantom-safe booking patterns, phantom-safe booking primer, booking overlap primer, unique-slot, unique slot, slot unique key, booking slot claim, exclusion-constraint, exclusion constraint, guard-row, guard row, double booking prevention, booking overlap design, overlap check pattern matrix, unique slot vs exclusion constraint vs guard row, discrete slot booking, continuous interval booking, PostgreSQL overlap constraint, MySQL booking guard

## 핵심 개념

겹침 금지 예약은 보통 이렇게 잘못 시작한다.

1. 겹치는 예약이 있는지 조회한다
2. 없으면 insert 한다

이 방식은 동시에 두 요청이 같은 "없음"을 관찰하면 phantom이나 write skew로 쉽게 샌다.

phantom-safe 설계의 핵심은 조회 결과를 믿지 않는 것이다.  
대신 "충돌 가능한 요청이 어디서 반드시 부딪히는가"를 저장 시점에 고정한다.

- `unique-slot`: slot claim row의 PK/UNIQUE가 부딪히게 만든다
- exclusion constraint: range overlap 자체를 제약으로 표현한다
- guard row: 대표 key를 먼저 잠가 충돌 요청을 같은 queue로 보낸다

셋 다 phantom-safe해질 수 있지만, **충돌을 중재하는 surface와 패배 요청이 치르는 비용이 다르다.**

## 먼저 보는 비교표

| 패턴 | 충돌을 중재하는 surface | phantom-safe 이유 | 잘 맞는 상황 | 주된 비용 |
|---|---|---|---|---|
| `unique-slot` | `(resource_id, slot_start)` 같은 active slot claim PK/UNIQUE | 충돌 요청이 같은 concrete slot key에 insert 하다 직접 부딪힌다 | 시간이 이미 15분, 30분, 1일처럼 discrete bucket으로 자연스럽게 잘리는 booking | slot row fan-out, rounding/DST policy, reschedule union handling |
| exclusion constraint | booking table의 equality dimension + range overlap 제약 | DB가 overlapping active interval을 insert/update 시점에 거부한다 | PostgreSQL, single-table active booking, continuous interval 자체가 business truth인 경우 | 엔진 의존성, active predicate 모델링, legacy overlap 정리 |
| guard row | `(resource)` 또는 `(resource, day)` guard row lock queue + 후속 exact overlap recheck | 충돌 가능한 writer가 같은 guard key를 먼저 잠가 absence check를 직렬화한다 | MySQL, multi-table workflow, later unit assignment, lifecycle가 복잡한 booking | hot row, canonical ordering, 모든 경로의 protocol 일치 필요 |

질문을 바꿔서 보면 더 명확하다.

- 패배 요청을 `duplicate key`나 constraint error로 빨리 떨어뜨리고 싶은가
- 패배 요청을 row-lock queue에 세워 transition path까지 한 protocol로 통일하고 싶은가
- 시간 모델이 discrete한가, continuous한가
- PostgreSQL 기능을 직접 쓸 수 있는가

## 패턴 1. `unique-slot`

`unique-slot`은 예약 구간을 canonical slot 집합으로 펼친 뒤, slot row 존재 여부를 occupancy truth로 삼는 방식이다.

```sql
CREATE TABLE room_slot_claim_active (
  room_id BIGINT NOT NULL,
  slot_start TIMESTAMPTZ NOT NULL,
  booking_id BIGINT NOT NULL,
  PRIMARY KEY (room_id, slot_start)
);
```

흐름은 단순하다.

1. `[start_at, end_at)`를 slot policy에 따라 정규화한다
2. 필요한 slot claim row를 insert 한다
3. duplicate key가 나면 이미 점유된 slot로 해석한다

### 언제 첫 선택이 되나

- 회의실 15분 슬롯, 숙박 1박 단위처럼 business time resolution이 이미 discrete하다
- PostgreSQL/MySQL 양쪽에서 같은 설명력을 원한다
- 패배 요청을 긴 lock wait보다 빠른 reject로 보내는 편이 낫다

### 왜 phantom-safe한가

부재 기반 판단을 "겹치는 slot row가 아직 없다"는 exact key 충돌로 바꿔 버리기 때문이다.  
즉 phantom을 abstract interval이 아니라 **실제 존재해야 하는 slot row**로 내린다.

### 놓치기 쉬운 함정

- slot rounding 규칙이 경로마다 다르면 conflict truth가 바로 갈라진다
- DST fold/gap, local time rounding, 청소 buffer를 slot policy에 먼저 반영해야 한다
- multi-slot reschedule은 `old_slots ∪ new_slots` 기준의 mutation protocol이 필요하다
- 긴 예약은 slot 수만큼 row와 index write가 늘어난다

`unique-slot`은 가장 portable한 기본값이지만, continuous interval을 억지로 slot으로 쪼개면 데이터 양과 경계 정책이 빠르게 복잡해진다.

## 패턴 2. exclusion constraint

exclusion constraint는 PostgreSQL에서 continuous interval overlap 자체를 저장 규칙으로 표현하는 방법이다.

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE room_booking
ADD CONSTRAINT room_booking_no_overlap
EXCLUDE USING gist (
  room_id WITH =,
  tstzrange(start_at, end_at, '[)') WITH &&
)
WHERE (status IN ('HELD', 'CONFIRMED', 'BLACKOUT'));
```

### 언제 첫 선택이 되나

- PostgreSQL을 사용한다
- conflict surface가 같은 테이블 안에서 닫힌다
- interval 자체가 continuous하고, discrete slot으로 자르는 편이 더 부자연스럽다

### 왜 phantom-safe한가

애플리케이션이 "겹치는 row가 없는지"를 먼저 판단하지 않아도,  
DB가 overlapping active interval을 insert/update 시점에 직접 거부하기 때문이다.

### 놓치기 쉬운 함정

- `room_id`, `[start, end)`, active status 정의가 먼저 고정되지 않으면 false conflict와 missed conflict가 같이 난다
- `23P01`은 business conflict이지 retry 후보가 아니다
- capacity가 1보다 큰 문제나 multi-table arbitration까지 제약 하나로 닫히지는 않는다
- 운영 테이블에 바로 추가하기 전에 overlap preflight scan과 lifecycle 정리가 필요하다

즉 exclusion constraint는 continuous overlap에는 매우 직접적이지만,  
"예약끼리 2개 이상 허용", "room type pool에서 팔고 나중에 room_id를 붙임" 같은 문제로 가면 다른 surface가 필요하다.

## 패턴 3. guard row

guard row는 overlap truth를 row 하나에 저장하는 패턴이 아니라, **충돌 가능한 writer를 같은 lock queue로 보내는 protocol**이다.

```text
1. booking이 건드릴 guard key 집합을 계산한다
2. key를 canonical order로 정렬한다
3. guard row를 같은 순서로 잠근다
4. 잠근 상태에서 exact overlap를 재검사한다
5. booking / hold / blackout row를 갱신한다
```

guard key는 workload에 따라 달라진다.

- `(room_id)`: 구현은 단순하지만 hot row가 되기 쉽다
- `(room_id, booking_day)`: multi-day booking에서 contention 범위를 줄이기 쉽다
- `(room_type_id, stay_day)`: pooled inventory나 later assignment에 맞다

### 언제 첫 선택이 되나

- MySQL에서 continuous overlap을 base table locking read 하나로 설명하기 어렵다
- booking, blackout, maintenance, hold cleanup 같은 여러 write path를 한 protocol로 묶어야 한다
- later assignment, capacity, multi-resource reservation처럼 overlap 바깥 invariant도 함께 다뤄야 한다

### 왜 phantom-safe한가

충돌 가능한 요청이 모두 같은 guard key를 먼저 잠그면,  
absence check와 insert/update가 사실상 직렬화되기 때문이다.

단, 이 조건이 빠지면 바로 샌다.

- 실제로 충돌하는 두 요청이 같은 guard key를 공유해야 한다
- 모든 write path가 guard row를 반드시 거쳐야 한다
- guard lock 아래에서 exact overlap 또는 capacity를 다시 확인해야 한다

### 놓치기 쉬운 함정

- guard row는 queue surface이지 occupancy truth 자체가 아니다
- multi-day move/reschedule은 `old_scope ∪ new_scope` 합집합을 잠가야 한다
- canonical ordering이 없으면 deadlock이 booking volume보다 먼저 문제를 만든다
- hot resource는 duplicate storm 대신 lock wait hotspot으로 바뀐다

guard row는 "MySQL이라서 어쩔 수 없이 쓰는 우회"라기보다,  
multi-path booking workflow를 한 admission protocol로 묶기 위한 적극적인 선택지에 가깝다.

## 어떤 질문으로 고르면 되나

### 1. 시간이 이미 discrete한가

그렇다면 `unique-slot`이 1차 후보다.  
slot row가 곧 truth가 되므로 엔진 차이를 가장 덜 탄다.

### 2. continuous interval이 business truth이고 PostgreSQL을 쓰는가

그렇다면 exclusion constraint가 가장 직접적이다.  
단일 active table 안에서 닫히는 overlap은 이 방식이 설명과 복구가 가장 짧다.

### 3. write path가 여러 개고 transition도 함께 통일해야 하는가

그렇다면 guard row를 먼저 본다.  
신규 예약, 연장, 취소, expiry cleanup, admin override를 같은 queue surface로 묶기 쉽다.

### 4. 패배 요청을 어떻게 다루고 싶은가

- 빠른 reject가 좋으면: `unique-slot`, exclusion constraint
- queued serialization이 좋으면: guard row

즉 세 패턴의 차이는 "무엇이 더 안전한가"가 아니라  
**어디에서 경쟁을 줄 세우고, 어디에서 conflict를 설명할 것인가**에 더 가깝다.

## 실전 판단 예시

### 시나리오 1. 15분 단위 회의실 예약

- 1차 선택: `unique-slot`
- 이유: 시간 해상도가 이미 discrete하고, duplicate key가 곧 double booking rejection이 된다
- 보완: slot rounding, cleanup buffer, reschedule union handling을 같은 slot policy로 맞춘다

### 시나리오 2. arbitrary time 장비 대여 on PostgreSQL

- 1차 선택: exclusion constraint
- 이유: continuous blocked range를 그대로 표현할 수 있고, buffer 시간도 derived range에 포함시키기 쉽다
- 보완: `HELD`/`CONFIRMED`/`MAINTENANCE`를 같은 active predicate로 묶는다

### 시나리오 3. MySQL 기반 숙박 예약 + later room assignment

- 1차 선택: `(room_type_id, stay_day)` 또는 `(room_id, stay_day)` guard row
- 이유: sell-time inventory와 later assignment, cleanup, admin override까지 같은 protocol로 묶기 쉽다
- 보완: guard lock 아래에서 exact overlap 또는 pooled capacity를 재검사하고, canonical ordering을 고정한다

## 자주 하는 오해

### "`SELECT ... FOR UPDATE` overlap probe면 충분한가?"

보통 아니다.  
base booking table의 overlap predicate는 B-tree scan axis와 business overlap이 어긋나기 쉽고, MySQL에서는 isolation/plan/index shape에 따라 lock footprint가 흔들린다.

### "guard row를 잠갔으면 exact overlap recheck는 필요 없나?"

아니다.  
guard row는 동시성 queue를 만드는 도구이지, 실제 점유 구간을 자동으로 계산해 주는 도구는 아니다.

### "exclusion constraint면 모든 예약 문제를 끝낼 수 있나?"

아니다.  
capacity > 1, multi-table arbitration, later assignment, external inventory는 guard row나 ledger까지 같이 봐야 한다.

## 한 줄 정리

booking overlap check에서 phantom-safe를 얻는 방법은 하나가 아니다.  
시간이 discrete하면 `unique-slot`, PostgreSQL continuous interval이면 exclusion constraint, multi-path booking workflow나 MySQL 중심 설계면 guard row를 먼저 검토하면 된다.
