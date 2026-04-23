# Slotization Precheck Queries for Overlaps, Rounding Collisions, and DST Boundaries

> 한 줄 요약: interval -> slot cutover 전 precheck는 "겹치는 row가 있나"만 보는 게 아니라, legacy overlap, slot-rounding collapse, DST fold/gap을 같은 canonical policy로 먼저 드러내는 것이다.

**난이도: 🔴 Advanced**

관련 문서:

- [Slotization Migration and Backfill Playbook](./slotization-migration-backfill-playbook.md)
- [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md)
- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md)
- [Active Predicate Drift in Reservation Arbitration](./active-predicate-drift-reservation-arbitration.md)
- [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md)

retrieval-anchor-keywords: slotization precheck, slotization preflight query, interval-to-slot cutover precheck, legacy interval overlap query, slot rounding collision query, rounded slot collapse, DST boundary precheck, daylight saving slotization, ambiguous local time fold, nonexistent local time gap, slot calendar dimension, overlap repair queue, pre-cutover conflict scan

## 핵심 개념

slotization cutover 직전 precheck가 답해야 하는 질문은 세 가지다.

1. source interval 자체가 이미 continuous overlap 규칙을 깨고 있는가
2. source는 합법인데 target slot policy가 floor/ceil 때문에 서로 다른 예약을 같은 slot claim으로 collapse시키는가
3. timezone / DST 경계 때문에 같은 local wall-clock label이 두 번 나타나거나 아예 사라져 slot expansion이 비결정적으로 되는가

이 셋을 한 카운트로 섞으면 conflict 수치는 나와도 복구 순서가 안 보인다.  
legacy corruption, policy mismatch, timezone calendar 문제는 repair path가 서로 다르기 때문이다.

## 먼저 고정할 계약

precheck 질의를 돌리기 전에 아래 값이 문서와 코드에서 같아야 한다.

- active predicate: 예를 들어 `HELD`, `CONFIRMED`, `BLACKOUT`만 blocker인지
- interval boundary: 보통 half-open interval `[start_at, end_at)`
- slot width: 5분, 15분, 30분, 1일
- start/end rounding 규칙: `floor(start)`, `ceil(end)`인지, 다른 정규화가 있는지
- canonical timezone source: row별 `zone_name`인지, resource/tenant default인지
- slot key 기준: UTC `slot_start`인지, local wall-clock slot인지
- quarantine 기준: precheck 실패 row를 cutover 대상에서 어떻게 제외할지

특히 `zone_name IS NULL`, `start_at >= end_at`, UTC와 local timestamp가 혼재된 row는 DST precheck 이전에 먼저 막아야 한다.  
이 상태로는 slot expansion 자체가 deterministic하지 않다.

## 공통 CTE부터 고정한다

아래 예시는 PostgreSQL 기준이다.  
MySQL에서는 `AT TIME ZONE` 대신 `CONVERT_TZ()`, `generate_series()` 대신 영구 `slot_sequence(n)` 또는 `slot_calendar` 테이블을 쓰면 된다.  
`CONVERT_TZ()`가 `NULL`을 반환하면 timezone table이 비어 있는 상태이므로 DST precheck를 `blocked`로 취급하는 편이 안전하다.

```sql
WITH slot_policy AS (
  SELECT 30::bigint AS slot_minutes,
         1800::bigint AS slot_seconds,
         'UTC'::text AS fallback_zone
),
active_booking AS (
  SELECT
    b.id,
    b.tenant_id,
    b.resource_id,
    COALESCE(b.zone_name, p.fallback_zone) AS zone_name,
    b.start_at_utc AS start_utc,
    b.end_at_utc AS end_utc
  FROM booking_interval b
  CROSS JOIN slot_policy p
  WHERE b.status IN ('HELD', 'CONFIRMED', 'BLACKOUT')
    AND b.cancelled_at IS NULL
    AND b.released_at IS NULL
    AND (b.expired_at IS NULL OR b.expired_at > CURRENT_TIMESTAMP)
    AND b.start_at_utc < b.end_at_utc
)
```

source가 local timestamp + zone 이름으로 저장돼 있다면 `start_utc`, `end_utc`를 먼저 UTC로 정규화해서 같은 CTE를 만든다.

```sql
-- PostgreSQL 예시
b.local_start_at AT TIME ZONE b.zone_name AS start_utc,
b.local_end_at   AT TIME ZONE b.zone_name AS end_utc
```

## 1. legacy continuous overlap pair를 먼저 분리한다

이 질의는 source가 이미 잘못된 경우를 잡는다.  
slotization 이전에도 충돌이 존재했다는 뜻이므로 rounding 문제와 같은 큐에 섞으면 안 된다.

```sql
WITH slot_policy AS (...),
active_booking AS (...)
SELECT
  a.tenant_id,
  a.resource_id,
  a.id AS left_booking_id,
  b.id AS right_booking_id,
  a.start_utc AS left_start_utc,
  a.end_utc AS left_end_utc,
  b.start_utc AS right_start_utc,
  b.end_utc AS right_end_utc
FROM active_booking a
JOIN active_booking b
  ON a.tenant_id = b.tenant_id
 AND a.resource_id = b.resource_id
 AND a.id < b.id
 AND a.start_utc < b.end_utc
 AND b.start_utc < a.end_utc
ORDER BY a.tenant_id, a.resource_id, a.start_utc, b.start_utc;
```

운영 팁:

- 결과 row는 `legacy-overlap`으로 따로 분류한다
- `resource_id`, `date_trunc('day', start_utc)` 기준 summary를 같이 남기면 repair batch를 나누기 쉽다
- cutover gate에서는 이 카운트가 `0`이거나, quarantine queue로 완전히 분리된 상태여야 한다

## 2. slot-rounding collision은 별도 질의로 잡는다

여기서 찾는 것은 "원래는 안 겹치지만 slot policy 때문에 같은 slot claim으로 붕괴되는 예약"이다.  
대표 예시는 `[10:05, 10:25)`와 `[10:25, 10:45)`를 30분 slot에 `floor(start) + ceil(end)`로 매핑할 때 둘 다 `10:00` slot을 점유해 버리는 경우다.

아래 예시는 slot key가 UTC `slot_start`인 모델을 가정한다.

```sql
WITH slot_policy AS (
  SELECT 1800::bigint AS slot_seconds
),
active_booking AS (...),
rounded AS (
  SELECT
    a.*,
    TIMESTAMPTZ 'epoch'
      + floor(extract(epoch FROM a.start_utc) / p.slot_seconds)
      * p.slot_seconds * INTERVAL '1 second' AS rounded_start_utc,
    TIMESTAMPTZ 'epoch'
      + ceil(extract(epoch FROM a.end_utc) / p.slot_seconds)
      * p.slot_seconds * INTERVAL '1 second' AS rounded_end_utc,
    p.slot_seconds
  FROM active_booking a
  CROSS JOIN slot_policy p
),
expanded AS (
  SELECT
    r.id,
    r.tenant_id,
    r.resource_id,
    r.start_utc,
    r.end_utc,
    gs.slot_start
  FROM rounded r
  CROSS JOIN LATERAL generate_series(
    r.rounded_start_utc,
    r.rounded_end_utc - r.slot_seconds * INTERVAL '1 second',
    r.slot_seconds * INTERVAL '1 second'
  ) AS gs(slot_start)
)
SELECT
  e1.tenant_id,
  e1.resource_id,
  e1.slot_start,
  e1.id AS left_booking_id,
  e2.id AS right_booking_id,
  e1.start_utc AS left_start_utc,
  e1.end_utc AS left_end_utc,
  e2.start_utc AS right_start_utc,
  e2.end_utc AS right_end_utc
FROM expanded e1
JOIN expanded e2
  ON e1.tenant_id = e2.tenant_id
 AND e1.resource_id = e2.resource_id
 AND e1.slot_start = e2.slot_start
 AND e1.id < e2.id
WHERE NOT (
  e1.start_utc < e2.end_utc
  AND e2.start_utc < e1.end_utc
)
ORDER BY e1.tenant_id, e1.resource_id, e1.slot_start;
```

이 결과는 `rounding-only-collision`이다.  
즉 source corruption이 아니라 slot policy mismatch이므로 보통 다음 셋 중 하나로 처리한다.

- legacy row를 slot 경계로 미리 정규화한다
- partial-slot row를 quarantine해서 old path에 남긴다
- slot width나 rounding rule을 다시 합의한다

slot별 hot spot summary가 필요하면 다음처럼 묶는다.

```sql
WITH ... expanded AS (...)
SELECT
  tenant_id,
  resource_id,
  slot_start,
  COUNT(DISTINCT id) AS booking_count
FROM expanded
GROUP BY tenant_id, resource_id, slot_start
HAVING COUNT(DISTINCT id) > 1
ORDER BY booking_count DESC, tenant_id, resource_id, slot_start;
```

## 3. DST boundary는 slot calendar로 검사하는 편이 안전하다

slot key가 local wall-clock 의미를 가지면 DST는 단순 timestamp arithmetic로 닫히지 않는다.

- spring forward: local time이 통째로 사라지는 gap
- fall back: 같은 local label이 두 번 나오는 fold
- zone별 offset change: 같은 30분 slot이라도 UTC 길이가 달라질 수 있음

이 경우 precheck helper로 `slot_calendar`를 두는 편이 가장 안전하다.

```sql
CREATE TABLE slot_calendar (
  zone_name TEXT NOT NULL,
  slot_width_minutes INTEGER NOT NULL,
  slot_start_utc TIMESTAMPTZ NOT NULL,
  slot_start_local TIMESTAMP NOT NULL,
  utc_offset_minutes INTEGER NOT NULL,
  PRIMARY KEY (zone_name, slot_width_minutes, slot_start_utc)
);
```

### 3-1. DST transition을 가로지르는 booking 찾기

```sql
WITH slot_policy AS (
  SELECT 30::int AS slot_minutes
),
active_booking AS (...),
calendar_hits AS (
  SELECT
    a.id,
    a.tenant_id,
    a.resource_id,
    a.zone_name,
    c.slot_start_utc,
    c.slot_start_local,
    c.utc_offset_minutes
  FROM active_booking a
  CROSS JOIN slot_policy p
  JOIN slot_calendar c
    ON c.zone_name = a.zone_name
   AND c.slot_width_minutes = p.slot_minutes
   AND c.slot_start_utc < a.end_utc
   AND c.slot_start_utc + p.slot_minutes * INTERVAL '1 minute' > a.start_utc
)
SELECT
  id,
  tenant_id,
  resource_id,
  zone_name,
  MIN(slot_start_local) AS first_local_slot,
  MAX(slot_start_local) AS last_local_slot,
  MIN(utc_offset_minutes) AS min_offset_minutes,
  MAX(utc_offset_minutes) AS max_offset_minutes,
  COUNT(*) AS covered_slot_count
FROM calendar_hits
GROUP BY id, tenant_id, resource_id, zone_name
HAVING MIN(utc_offset_minutes) <> MAX(utc_offset_minutes)
ORDER BY tenant_id, resource_id, id;
```

이 결과는 `dst-transition-crossing`으로 보관한다.  
cutover 전에 별도 샘플 검증을 하거나, 해당 구간만 old path로 남기는 기준점이 된다.

### 3-2. ambiguous local slot(fold) 자체를 찾기

```sql
SELECT
  zone_name,
  slot_width_minutes,
  slot_start_local,
  COUNT(*) AS utc_candidate_count,
  MIN(slot_start_utc) AS first_slot_start_utc,
  MAX(slot_start_utc) AS last_slot_start_utc
FROM slot_calendar
GROUP BY zone_name, slot_width_minutes, slot_start_local
HAVING COUNT(*) > 1
ORDER BY zone_name, slot_start_local;
```

같은 `slot_start_local`에 UTC 후보가 둘 이상 나오면 local label만으로는 slot key를 만들 수 없다.  
local slot을 식별자로 쓰는 설계라면 cutover 전에 UTC key 또는 offset 포함 key로 바꿔야 한다.

### 3-3. nonexistent local slot(gap) / local step discontinuity 찾기

```sql
WITH ordered AS (
  SELECT
    zone_name,
    slot_width_minutes,
    slot_start_utc,
    slot_start_local,
    LAG(slot_start_local) OVER (
      PARTITION BY zone_name, slot_width_minutes
      ORDER BY slot_start_utc
    ) AS prev_local
  FROM slot_calendar
)
SELECT
  zone_name,
  slot_width_minutes,
  prev_local,
  slot_start_local,
  EXTRACT(EPOCH FROM (slot_start_local - prev_local)) / 60 AS local_step_minutes
FROM ordered
WHERE prev_local IS NOT NULL
  AND slot_start_local - prev_local
      <> slot_width_minutes * INTERVAL '1 minute'
ORDER BY zone_name, slot_start_utc;
```

`local_step_minutes`가 slot width보다 크면 gap, 작거나 음수면 fold 주변 discontinuity다.  
이 창(window)과 겹치는 booking을 따로 조인하면 `dst-gap-window`, `dst-fold-window` 큐를 만들 수 있다.

## cutover gate는 분류별로 닫는다

precheck 결과는 합쳐서 한 줄로 보지 말고 최소 아래처럼 나눈다.

- `legacy-overlap`: source 자체가 continuous invariant를 위반
- `rounding-only-collision`: source는 합법이나 slot policy가 collapse 유발
- `dst-transition-crossing`: offset change를 가로지르는 row
- `dst-ambiguous-local-slot`: 같은 local label이 둘 이상의 UTC slot에 대응
- `dst-gap-window`: local calendar가 불연속인 구간과 겹치는 row

cutover 승인 기준 예시:

1. `legacy-overlap = 0`
2. `rounding-only-collision = 0` 또는 quarantine 완료
3. `dst-ambiguous-local-slot = 0` 또는 slot key가 UTC / offset 포함 key로 고정됨
4. `dst-transition-crossing`, `dst-gap-window`는 샘플 replay 또는 수동 검토 정책이 명시됨
5. precheck 결과가 backfill acceptance artifact에 남아 있음

즉 precheck는 단순 진단이 아니라 cutover gate의 첫 번째 evidence bundle이다.

## 꼬리질문

> Q: legacy overlap과 rounding collision을 왜 따로 세나요?
> 의도: source corruption과 target policy mismatch를 구분하는지 확인
> 핵심: 복구 책임이 다르다. 전자는 데이터 정리, 후자는 slot 정책 또는 quarantine 결정 문제다.

> Q: DST crossing booking은 무조건 잘못된 데이터인가요?
> 의도: DST 자체와 비결정적 slot key 문제를 구분하는지 확인
> 핵심: 아니다. 다만 local slot key가 ambiguous해질 수 있으므로 UTC key, offset 포함 key, 수동 검토 중 하나가 필요하다.

> Q: MySQL에서 timezone table이 없으면 그냥 UTC로만 보면 안 되나요?
> 의도: timezone 정보 손실을 "편의상 무시"하면 안 된다는 점을 이해하는지 확인
> 핵심: local wall-clock 기준 정책이면 안 된다. DST fold/gap을 잃어버리므로 precheck를 `blocked`로 두는 편이 더 안전하다.

## 한 줄 정리

slotization cutover 전 precheck는 overlap pair, rounding-only collision, DST calendar ambiguity를 같은 canonical policy 아래서 각각 분리해 잡아야 repair 순서와 cutover gate가 선명해진다.
