# Active Predicate Drift in Reservation Arbitration

> 한 줄 요약: 예약 overlap arbitration은 interval 조건만 맞추면 끝나는 문제가 아니다. `HELD`/`CONFIRMED`/`BLACKOUT`/`EXPIRED`를 booking, blackout, cleanup path가 서로 다른 active predicate로 해석하면, `EXPIRED` 전이 지연이 곧 false blocker와 overlap 누락으로 번진다.

**난이도: 🔴 Advanced**

관련 문서:

- [Reservation Reschedule and Cancellation Transition Patterns](./reservation-reschedule-cancellation-transition-patterns.md)
- [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md)
- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md)
- [Expiry Worker Race Patterns](./expiry-worker-race-patterns.md)
- [Expired-Unreleased Drift Runbook](./expired-unreleased-drift-runbook.md)
- [Active Hold Table Split Pattern](./active-hold-table-split-pattern.md)
- [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md)

retrieval-anchor-keywords: active predicate drift reservation arbitration, held confirmed expired lifecycle drift, booking blackout cleanup predicate alignment, overlap blocker normalization, mysql reservation overlap predicate, expired still blocking reservation, blackout predicate drift, reservation blocker active set, released_at overlap truth, booking blackout cleanup contract, active overlap flag, hold confirm expire overlap, lifecycle drift overlap enforcement, arbitration table active predicate

## 핵심 개념

예약/blackout 시스템의 overlap rule은 보통 두 축으로 결정된다.

1. requested interval이 기존 row와 겹치는가
2. 그 row가 **지금 conflict set에 포함되는 active blocker인가**

많은 팀이 첫 번째 축에는 공을 들이지만, 두 번째 축은 path마다 다르게 해석한다.

- booking create는 `status IN ('CONFIRMED', 'BLACKOUT')`만 본다
- hold create는 `status IN ('HELD', 'CONFIRMED')`를 본다
- blackout 등록은 `status IN ('HELD', 'CONFIRMED', 'BLACKOUT') AND expires_at > NOW()`를 본다
- cleanup worker는 `status='HELD' AND expires_at <= NOW()`만 보고 나중에 `EXPIRED`로 바꾼다

이렇게 되면 interval predicate는 같아도 conflict set이 path마다 달라진다.  
결과는 둘 중 하나다.

- 아직 막아야 할 `HELD`를 어떤 path가 빼먹어 overlap을 허용한다
- 이미 풀렸어야 할 `EXPIRED` hold를 어떤 path가 계속 blocker로 본다

핵심은 `HELD`/`CONFIRMED`/`BLACKOUT`/`EXPIRED`를 상태 라벨로만 보지 않고,  
**어떤 전이가 overlap arbitration membership를 바꾸는가**를 하나의 계약으로 고정하는 것이다.

## 먼저 고정할 lifecycle 의미

| 라벨/컬럼 | 뜻 | overlap conflict set을 직접 바꾸는가 |
|---|---|---|
| `HELD` | 임시 보류지만 아직 자원을 막는 상태 | 그렇다. active blocker다 |
| `CONFIRMED` | 확정 예약으로 계속 자원을 막는 상태 | 그렇다. active blocker다 |
| `BLACKOUT` | 운영자/정책이 만든 차단 구간 | 그렇다. active blocker다 |
| `EXPIRED`, `CANCELED` | 더 이상 overlap arbitration에 포함되면 안 되는 종료 상태 | 그렇다. active set에서 빠져야 한다 |
| `expires_at` | `HELD`가 release 후보가 되는 deadline | 아니다. 그 자체로 active set에서 자동 이탈하지 않는다 |
| `released_at` | overlap conflict set에서 빠진 시각 | 그렇다. materialized release truth다 |

여기서 중요한 점은 `EXPIRED`와 `expires_at`을 구분하는 것이다.

- `expires_at`은 "이제 release를 시도해야 한다"는 wall-clock 신호다
- `EXPIRED`는 "이미 active blocker가 아니다"라는 materialized 결과여야 한다

즉 `expires_at <= NOW()`인데 `released_at IS NULL`이면, deadline은 지났지만 arbitration truth는 아직 active set 안에 남아 있는 것이다.

## overlap arbitration이 lifecycle drift에 약한 이유

### 1. `HELD`를 빼먹으면 booking과 blackout이 서로 다른 현재를 본다

실무에서 흔한 실수는 "확정 예약만 진짜 blocker"라고 생각하는 것이다.

- booking confirm path는 `CONFIRMED`만 본다
- blackout path는 `HELD`, `CONFIRMED`, `BLACKOUT`을 모두 본다

이 경우:

- booking path는 아직 살아 있는 hold를 못 보고 같은 구간을 중복 승인할 수 있다
- blackout path는 그 hold를 보고 차단을 거절한다

둘 다 자기 기준으로는 맞아 보이지만, conflict set이 다르므로 overlap rule은 이미 분열된 상태다.

### 2. `EXPIRED` 전이를 늦추면 false blocker가 생긴다

또 다른 흔한 실수:

- read/booking path는 `expires_at > NOW()`만 보고 expired hold를 무시한다
- blackout path나 constraint path는 `status IN ('HELD', 'CONFIRMED', 'BLACKOUT')`만 본다
- cleanup worker가 몇 분 뒤 `status='EXPIRED'`를 찍는다

이 상태에서는 deadline-past hold가 path마다 다르게 해석된다.

- 어떤 path는 "이미 끝났다"고 보고
- 어떤 path는 "아직 blocker"라고 본다

즉 `EXPIRED`가 늦게 materialize될수록 overlap arbitration의 일관성이 약해진다.

### 3. hold에서 booking으로 authority를 넘길 때 canonical blocker surface가 갈라지기 쉽다

`HELD -> CONFIRMED` 전이가 같은 row 안에서 끝나지 않고:

- `reservation_hold`에서 `reservation_booking`으로 row를 옮기거나
- `hold_active`와 `booking_active`를 따로 두는 구조

를 쓰는 경우가 많다.

이때 위험한 패턴:

- booking API는 `booking_active`만 본다
- blackout API는 `hold_active + blackout`만 본다
- cleanup worker는 `hold_active`만 정리한다

이 구조에서는 confirm 직후 동일한 authority가:

- 두 relation에 동시에 남거나
- 둘 다에서 잠깐 빠지거나
- 어느 한 path만 새 relation을 읽는

상태가 생긴다.

해결 기준은 단순하다.  
booking/hold/blackout이 어디에 저장되든 **overlap arbitration은 canonical blocker surface 하나만 읽어야 한다.**

## drift가 생기는 세 경로

| 경로 | 흔한 local predicate | 왜 drift가 생기는가 |
|---|---|---|
| booking create / reschedule | `status IN ('CONFIRMED', 'BLACKOUT')` | pending hold를 blocker에서 빼 overlap race를 만든다 |
| blackout create / edit | `status IN ('HELD', 'CONFIRMED', 'BLACKOUT') AND (status <> 'HELD' OR expires_at > NOW())` | expired-but-unreleased hold를 어떤 path는 무시하고 어떤 path는 계속 blocker로 본다 |
| cleanup / expiry | `status='HELD' AND expires_at <= NOW()`만 보고 label만 바꾼다 | `EXPIRED` 라벨과 actual release truth가 분리된다 |

여기서 중요한 건 SQL 문장 자체보다 **세 경로가 같은 active set을 읽고 쓰는가**다.  
질문은 "겹치느냐"보다 "누가 겹침 판정 대상인가"다.

## 권장 contract: lifecycle label과 arbitration membership를 분리한다

가장 안전한 계약은 아래 둘을 분리하는 것이다.

- lifecycle label: `HELD`, `CONFIRMED`, `BLACKOUT`, `EXPIRED`, `CANCELED`
- active overlap membership: `active_overlap = 1` 또는 `released_at IS NULL`

single-table 모델이라면 보통 이렇게 고정한다.

- active expirable blocker: `status = 'HELD' AND released_at IS NULL`
- active durable blocker: `status IN ('CONFIRMED', 'BLACKOUT') AND released_at IS NULL`
- inactive terminal row: `status IN ('EXPIRED', 'CANCELED') AND released_at IS NOT NULL`

핵심 규칙:

1. booking path와 blackout path는 같은 overlap probe를 쓴다
2. `HELD -> CONFIRMED`는 active membership를 유지한 채 label만 바꾸거나, canonical blocker row를 같은 트랜잭션에서 handoff한다
3. `HELD -> EXPIRED`는 `status='EXPIRED'`와 `released_at` 또는 `active_overlap=0` 전이를 같은 트랜잭션에서 commit한다
4. cleanup/archive는 release 이후에만 `deleted_at`이나 history move를 수행한다

중요한 금지사항:

- `expires_at > NOW()`를 overlap blocker truth로 직접 쓰지 않는다
- `deleted_at IS NULL`을 overlap active predicate로 재사용하지 않는다
- booking, blackout, cleanup이 서로 다른 source table 조합을 읽게 두지 않는다

## MySQL-friendly normalization

MySQL에서는 wall-clock 조건이 시간이 흐른다고 인덱스 membership를 자동으로 바꿔 주지 않는다.  
그래서 `expires_at > NOW()`를 active key의 진실로 쓰기보다, release를 명시적 write로 materialize하는 편이 안전하다.

```sql
CREATE TABLE reservation_blocker (
  blocker_id BIGINT PRIMARY KEY,
  resource_id BIGINT NOT NULL,
  blocker_kind VARCHAR(16) NOT NULL,   -- HOLD / BOOKING / BLACKOUT
  status VARCHAR(16) NOT NULL,         -- HELD / CONFIRMED / BLACKOUT / EXPIRED / CANCELED
  starts_at DATETIME(6) NOT NULL,
  ends_at DATETIME(6) NOT NULL,
  expires_at DATETIME(6) NULL,
  released_at DATETIME(6) NULL,
  active_overlap TINYINT(1) NOT NULL,
  version BIGINT NOT NULL DEFAULT 0,
  KEY ix_blocker_active_overlap (resource_id, active_overlap, starts_at, ends_at)
);
```

여기서 `active_overlap`은 time-derived truth가 아니라 transition-derived truth다.

- `HELD`, `CONFIRMED`, `BLACKOUT`이 overlap conflict set에 있으면 `1`
- `EXPIRED`, `CANCELED`, archive 완료 후 row면 `0`
- `expires_at`은 `HELD`를 언제 `0`으로 내려야 하는지 알려 주는 후보 조건일 뿐이다

그다음 booking과 blackout은 같은 probe를 쓴다.

```sql
SELECT blocker_id, blocker_kind, status
FROM reservation_blocker
WHERE resource_id = :resource_id
  AND active_overlap = 1
  AND starts_at < :requested_end
  AND ends_at > :requested_start
FOR UPDATE;
```

expire path는 label과 active membership를 함께 바꾼다.

```sql
UPDATE reservation_blocker
SET status = 'EXPIRED',
    released_at = NOW(6),
    active_overlap = 0,
    version = version + 1
WHERE blocker_id = :blocker_id
  AND blocker_kind = 'HOLD'
  AND status = 'HELD'
  AND active_overlap = 1
  AND released_at IS NULL
  AND expires_at <= NOW(6);
```

`HELD -> CONFIRMED`는 overlap membership를 유지해야 한다.

```sql
UPDATE reservation_blocker
SET status = 'CONFIRMED',
    version = version + 1
WHERE blocker_id = :blocker_id
  AND blocker_kind = 'HOLD'
  AND status = 'HELD'
  AND active_overlap = 1
  AND released_at IS NULL;
```

중요한 점은 confirm이 "blocking truth를 풀었다가 다시 잡는" 전이가 아니라는 것이다.  
같은 자원을 계속 막아야 한다면 active membership는 유지되고, label만 `HELD`에서 `CONFIRMED`로 바뀐다.

## canonical blocker surface를 별도 relation으로 둘 수도 있다

single table이 복잡해지면 더 명확한 방법은 `reservation_blocker_active`를 별도로 두는 것이다.

- booking create / reschedule는 `reservation_blocker_active`만 본다
- blackout create / edit도 같은 table만 본다
- expire / cancel / release는 active row를 삭제하거나 history로 이동한다
- `HELD -> CONFIRMED` handoff가 다른 relation으로 이동해야 하면, old row 제거와 new row 삽입을 같은 트랜잭션에서 처리한다

이 패턴의 장점:

- active predicate가 row presence로 고정된다
- `deleted_at`, archive lag, retention batch가 overlap truth를 오염시키지 못한다
- booking/blackout/cleanup이 서로 다른 source table을 읽는 drift를 줄인다

## 실전 시나리오

### 시나리오 1. hold는 booking path에서 빠지고 blackout path에만 남는다

규칙:

- 같은 `room_id`의 `HELD`, `CONFIRMED`, `BLACKOUT` interval은 겹치면 안 된다

틀린 정렬:

- 사용자 booking confirm은 `CONFIRMED`, `BLACKOUT`만 본다
- 운영자 blackout 등록은 `HELD`, `CONFIRMED`, `BLACKOUT`을 모두 본다

결과:

- booking path는 live hold를 무시하고 중복 승인할 수 있다
- blackout path는 같은 hold 때문에 등록을 거절한다

맞는 정렬:

- 두 path가 같은 blocker relation과 같은 active predicate를 본다
- `HELD`는 confirm 전까지 overlap conflict set에 남는다

### 시나리오 2. `EXPIRED` 라벨은 찍혔지만 still blocking 상태가 남는다

틀린 정렬:

- cleanup worker가 먼저 `status='EXPIRED'`만 기록한다
- active key나 canonical blocker row 제거는 나중 배치가 처리한다
- booking path는 `expires_at > NOW()` 기준으로 이미 무시한다
- blackout path는 아직 active row를 계속 읽는다

결과:

- 사용자에게는 빈 구간처럼 보이는데 blackout/booking 중 일부는 계속 충돌한다
- 운영자는 "예약은 없는데 blackout도 안 들어간다"는 증상을 본다

맞는 정렬:

- `EXPIRED` 전이와 active membership 제거를 같은 트랜잭션에서 수행한다
- repair/reconciliation은 `expires_at <= NOW() AND released_at IS NULL` anomaly를 직접 잡는다

### 시나리오 3. confirm handoff 때 canonical blocker surface가 잠깐 비거나 중복된다

틀린 정렬:

- `hold_active` row를 지운 뒤 별도 트랜잭션에서 `booking_active` row를 넣는다
- blackout 등록은 두 트랜잭션 사이에서 probe를 수행한다

결과:

- 잠깐 빈 window를 보고 blackout이 들어가거나
- 양쪽 row가 동시에 남아 false conflict가 난다

맞는 정렬:

- hold release와 booking acquire를 같은 트랜잭션에서 handoff한다
- 가능하면 blackout도 `booking_active`, `hold_active`를 따로 읽지 말고 canonical blocker surface만 읽는다

## 운영 guardrail 체크리스트

- booking, blackout, cleanup path의 `WHERE` 절을 나란히 적었을 때 정말 같은 active blocker 집합을 가리키는가
- `HELD -> CONFIRMED`가 active membership 유지인지, authority handoff인지 문서로 고정돼 있는가
- `EXPIRED`, `CANCELED` terminal label은 항상 `released_at IS NOT NULL` 또는 active row 부재와 같이 commit되는가
- `expires_at <= NOW()`인데 still active인 row 수와 `post-expiry conflict`를 함께 모니터링하는가
- MySQL overlap probe가 `(resource_id, active_overlap, starts_at|ends_at)` 같은 stable prefix를 가지는가
- archive/history move가 overlap arbitration table 또는 active relation을 직접 흔들지 않는가

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| status 라벨만으로 active set 추론 | 구현이 단순해 보인다 | path별 drift가 가장 쉽게 생긴다 | 중요도가 낮은 임시 도구 외에는 피한다 |
| `released_at` + `active_overlap` materialization | booking/blackout/cleanup을 같은 predicate로 맞추기 쉽다 | 전이 write discipline이 필요하다 | MySQL reservation overlap path의 기본값 |
| canonical blocker active table 분리 | active predicate가 가장 명확하다 | handoff/move transaction 설계가 필요하다 | hold, booking, blackout source가 여러 relation으로 갈라질 때 |
| `expires_at > NOW()` read-time 판단 | countdown UX 설명은 쉽다 | overlap arbitration truth로는 약하다 | 화면 힌트에는 가능하지만 write arbitration에는 부적합 |

## 꼬리질문

> Q: `EXPIRED` 상태만 찍으면 overlap blocker에서 빠졌다고 봐도 되나요?
> 의도: lifecycle label과 materialized release를 구분하는지 확인
> 핵심: 아니다. terminal label과 active membership 제거가 같은 트랜잭션에서 일어나지 않으면 path마다 다른 현재를 보게 된다

> Q: 왜 blackout 등록도 booking과 같은 active predicate를 읽어야 하나요?
> 의도: booking과 blackout이 같은 conflict set을 공유한다는 점을 이해하는지 확인
> 핵심: 둘 다 같은 resource-time interval에 blocker를 추가하는 writer라서, 하나라도 다른 predicate를 쓰면 overlap rule이 두 개가 된다

> Q: `expires_at > NOW()`를 active blocker truth로 쓰면 안 되는 이유는 무엇인가요?
> 의도: wall-clock 조건과 arbitration truth를 구분하는지 확인
> 핵심: 시간 경과만으로 row의 인덱스 membership나 canonical blocker relation이 자동으로 바뀌지 않으므로, release를 명시적 write로 materialize해야 한다

## 한 줄 정리

예약 overlap arbitration의 진짜 실패 원인은 interval SQL보다, `HELD`/`CONFIRMED`/`BLACKOUT`/`EXPIRED`가 booking·blackout·cleanup path에서 같은 active blocker 집합으로 해석되지 않는 데 있다. lifecycle label과 overlap membership를 분리하고, release를 같은 canonical surface에 materialize할 때만 drift 없는 arbitration이 가능하다.
