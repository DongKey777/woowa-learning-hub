---
schema_version: 3
title: Active Predicate Alignment for Capacity Guards
concept_id: database/active-predicate-alignment-capacity-guards
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 85
mission_ids:
- missions/roomescape
review_feedback_tags:
- capacity-guard
- active-predicate
- guard-row-drift
- reservation-capacity
aliases:
- active predicate alignment
- capacity guard predicate
- expires_at released_at alignment
- soft delete guard row drift
- admission check guard row reconciliation
- reservation capacity drift
- active predicate reconciliation
- released_at vs deleted_at counter
- capacity guard active set
- 예약 capacity guard predicate
symptoms:
- admission check는 expires_at만 보고 빈 자리라고 판단하지만 guard row counter는 아직 reserved 수량을 잡고 있다
- reconciliation scan이 deleted_at 기준으로 계산해 runtime guard predicate와 다른 active set을 정상처럼 본다
- expired-but-unreleased row가 쌓여 false capacity blocker 또는 false vacancy가 반복된다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- database/guard-row-vs-serializable-vs-reconciliation-set-invariants
- database/hold-expiration-predicate-drift
- database/active-hold-table-split-pattern
next_docs:
- database/expired-unreleased-drift-runbook
- database/expiry-worker-race-patterns
- database/range-invariant-enforcement-write-skew-phantom
linked_paths:
- contents/database/reservation-reschedule-cancellation-transition-patterns.md
- contents/database/guard-row-vs-serializable-vs-reconciliation-set-invariants.md
- contents/database/hold-expiration-predicate-drift.md
- contents/database/expired-unreleased-drift-runbook.md
- contents/database/active-hold-table-split-pattern.md
- contents/database/guard-row-scope-design-multi-day-bookings.md
- contents/database/range-invariant-enforcement-write-skew-phantom.md
- contents/database/soft-delete-uniqueness-indexing-lifecycle.md
- contents/database/expiry-worker-race-patterns.md
confusable_with:
- database/active-hold-table-split-pattern
- database/active-predicate-drift-reservation-arbitration
- database/hold-expiration-predicate-drift
- database/guard-row-vs-serializable-vs-reconciliation-set-invariants
forbidden_neighbors: []
expected_queries:
- capacity guard에서 admission check, guard row mutation, reconciliation scan이 같은 active predicate를 봐야 하는 이유가 뭐야?
- expires_at은 release 후보이고 released_at은 capacity handoff truth라는 차이를 설명해줘
- deleted_at이나 archive worker가 guard row counter를 바꾸면 capacity drift가 생기는 이유가 뭐야?
- expired-but-unreleased claim 때문에 capacity가 남아 보이는데 guard update가 실패하는 문제를 어떻게 진단해?
- reservation capacity guard에서 active predicate alignment contract를 SQL과 worker 기준으로 어떻게 잡아?
contextual_chunk_prefix: |
  이 문서는 Active Predicate Alignment for Capacity Guards playbook으로, expirable reservation claim에서
  admission check, guard row counter mutation, reconciliation scan이 expires_at, released_at, deleted_at을
  같은 active set contract로 해석해야 false vacancy와 false blocker를 막을 수 있음을 설명한다.
---
# Active Predicate Alignment for Capacity Guards

> 한 줄 요약: capacity guard는 counter 하나만 맞추는 문제가 아니라, admission check·guard row 전이·reconciliation scan이 `expires_at`, `released_at`, soft-delete를 같은 active predicate로 해석하게 만드는 문제다.

**난이도: 🔴 Advanced**

관련 문서:

- [Reservation Reschedule and Cancellation Transition Patterns](./reservation-reschedule-cancellation-transition-patterns.md)
- [Guard Row vs Serializable Retry vs Reconciliation for Set Invariants](./guard-row-vs-serializable-vs-reconciliation-set-invariants.md)
- [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md)
- [Expired-Unreleased Drift Runbook](./expired-unreleased-drift-runbook.md)
- [Active Hold Table Split Pattern](./active-hold-table-split-pattern.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)
- [Soft Delete, Uniqueness, and Data Lifecycle Design](./soft-delete-uniqueness-indexing-lifecycle.md)
- [Expiry Worker Race Patterns](./expiry-worker-race-patterns.md)

retrieval-anchor-keywords: active predicate alignment, capacity guard predicate, expires_at released_at alignment, soft delete guard row drift, admission check guard row reconciliation, expired but still counted, false capacity blocker, false vacancy guard counter, release transition counter decrement, active predicate reconciliation, reservation capacity drift, bucket guard reconciliation, released_at vs deleted_at counter, expirable claim alignment, deadline passed still counted

## 핵심 개념

expirable hold가 capacity를 점유하는 시스템은 보통 세 시점을 동시에 가진다.

- `expires_at`: deadline이 지났는지
- `released_at`: 실제로 capacity를 비운 시점
- `deleted_at` / `archived_at`: retention 정리가 끝난 시점

문제는 이 세 컬럼이 각 surface에서 다른 뜻으로 소비되기 쉽다는 점이다.

- admission check는 `expires_at > now()`만 보고 "지금 새 요청을 받아도 된다"고 판단한다
- guard row는 `released_at IS NULL` row를 아직 reserved 수량으로 잡고 있다
- reconciliation scan은 `deleted_at IS NULL`만 보고 guard counter와 detail row를 대조한다

이렇게 되면 같은 claim이 세 경로에서 서로 다른 현재를 만든다.

- admission은 "빈 자리"라고 말한다
- guard row는 "이미 capacity가 찼다"고 막는다
- reconciliation은 "guard와 detail이 일치한다"고 잘못 결론 낸다

capacity invariant에서 핵심은 `expires_at`, `released_at`, soft-delete를 각각의 의미로 분리한 뒤, **capacity를 실제로 점유하는 active set이 무엇인지 하나의 계약으로 고정하는 것**이다.

## 먼저 고정할 세 가지 의미

| 컬럼 | 뜻 | capacity membership를 직접 바꾸는가 |
|---|---|---|
| `expires_at` | release 후보가 되는 deadline | 아니다. 그 자체로 active set에서 빠지지 않는다 |
| `released_at` | 더 이상 capacity를 점유하지 않게 된 시각 | 그렇다. active predicate handoff 시점이다 |
| `deleted_at` / `archived_at` | 감사/보관 lifecycle이 끝난 시각 | 아니다. cleanup truth일 뿐이다 |

이 구분이 흐려지면 흔히 두 가지 오류가 난다.

1. deadline이 지났다는 이유만으로 admission이 row를 무시한다
2. soft delete가 끝났다는 이유만으로 guard row를 감소시킨다

둘 다 잘못이다.

- `expires_at`은 "지금 release를 시도해야 하는가"를 알려 줄 뿐이다
- `released_at` 또는 active table row 제거가 실제 capacity handoff다
- `deleted_at`은 release가 끝난 후에야 따라와도 된다

따라서 최소 계약은 아래처럼 적는 편이 안전하다.

- `released_at IS NULL` 또는 `*_active` relation row 존재가 blocking truth다
- `expires_at <= now()`는 blocking row를 finalize해야 할 후보 조건이다
- `deleted_at IS NOT NULL`이면 반드시 이미 `released_at IS NOT NULL`이어야 한다
- soft-delete worker는 retention metadata만 채우고 guard row에는 손대지 않는다

## 세 surface가 같은 질문을 하게 만들어야 한다

### 1. admission check

admission check의 질문은 "새 claim을 받아도 되는가"다.  
이 질문은 deadline 자체가 아니라 **지금도 capacity를 점유하는 row가 무엇인가**를 기준으로 답해야 한다.

안전한 흐름:

1. 같은 bucket/resource를 점유 중인 row를 canonical active predicate로 찾는다
2. 그중 `expires_at <= now()`이면서 아직 `released_at IS NULL`인 row는 잠금 아래에서 inline finalize하거나 retry 대상으로 넘긴다
3. 그다음 guard row 또는 detail aggregate를 같은 predicate로 다시 본다

위 흐름 없이 `expires_at > now()`만 필터로 쓰면, admission은 expired-but-unreleased row를 건너뛰지만 guard row는 여전히 그 수량을 잡고 있어서 false vacancy가 생긴다.

### 2. guard row mutation

guard row의 질문은 "active capacity 총량이 얼마인가"다.  
따라서 counter를 바꾸는 이벤트도 active predicate 변화와 정확히 같아야 한다.

- claim 생성으로 blocking set에 들어올 때: 증가
- `released_at`이 처음 채워지거나 active table에서 빠질 때: 감소
- `deleted_at`만 채워질 때: 변화 없음
- deadline만 지났지만 아직 release를 commit하지 않았을 때: 변화 없음

즉 guard row는 wall clock이나 archive 배치에 반응하면 안 되고, **blocking truth가 바뀐 트랜잭션**에만 반응해야 한다.

### 3. reconciliation scan

reconciliation의 질문은 "guard row가 실제 active detail row와 같은 수량을 보고 있는가"다.  
그러므로 scan 조건도 admission/guard mutation과 동일해야 한다.

여기서 자주 틀리는 패턴:

- scan은 `deleted_at IS NULL`만 보고 더한다
- runtime guard는 `released_at IS NULL`에만 반응한다
- admission은 `expires_at > now()`를 본다

이 상태에서는 drift가 있어도 scan이 못 잡거나, drift가 없는데 scan이 계속 alert를 낸다.  
reconciliation은 "대충 비슷한 active scope"가 아니라 **런타임 counter를 만든 바로 그 predicate**를 재계산해야 한다.

## 대표 anti-pattern

아래 셋이 같이 있으면 capacity guard는 거의 반드시 drift 난다.

```sql
-- admission: deadline 기반으로만 남은 수량을 계산
SELECT COALESCE(SUM(qty), 0) AS active_qty
FROM reservation_claim
WHERE bucket_id = :bucket_id
  AND status IN ('HELD', 'CONFIRMED')
  AND expires_at > now();
```

```sql
-- guard row: expiry worker가 나중에 soft delete를 찍을 때까지 reserved_qty 유지
UPDATE reservation_guard
SET reserved_qty = reserved_qty - :qty
WHERE bucket_id = :bucket_id;
```

```sql
-- reconciliation: soft delete 기준으로 active scope를 계산
SELECT COALESCE(SUM(qty), 0) AS actual_qty
FROM reservation_claim
WHERE bucket_id = :bucket_id
  AND status IN ('HELD', 'CONFIRMED')
  AND deleted_at IS NULL;
```

세 쿼리 모두 그럴듯하지만, 사실은 서로 다른 row 집합을 보고 있다.

- admission은 deadline-past row를 이미 제외한다
- guard row는 release commit 전까지 계속 포함한다
- reconciliation은 archive backlog가 사라질 때까지 포함한다

이 상태에서 나타나는 증상:

- capacity가 남아 보이는데 guard update가 실패한다
- sweeper가 늦을수록 reserved counter가 과대 계상된다
- archive backlog가 길어지면 reconciliation이 계속 "정상"처럼 보인다

## 권장 contract: expirable claim과 cleanup을 분리한다

single-table 모델이라면 active predicate를 보통 이렇게 고정한다.

- expirable blocking claim: `status IN ('HELD', 'PENDING_PAYMENT') AND released_at IS NULL`
- durable blocking allocation: `status IN ('CONFIRMED', 'ALLOCATED') AND released_at IS NULL`
- cleanup/retention metadata: `deleted_at`, `archived_at`

여기서 중요한 규칙:

1. `expires_at`은 expirable claim을 release 후보로 고르는 데만 쓴다
2. actual capacity handoff는 `released_at`을 채우는 순간 또는 active table row를 제거하는 순간에만 일어난다
3. `deleted_at`은 이미 release된 row에 나중에 찍혀도 된다

active/history split 모델이면 더 단순하다.

- admission check는 `claim_active`만 본다
- guard row는 `claim_active` insert/delete에만 반응한다
- reconciliation은 `claim_active` 합계를 재계산한다
- `deleted_at`은 history table 안에서만 의미를 가진다

즉 split을 쓰든 single table을 쓰든, guard semantics의 핵심은 같다.  
**capacity를 막는 truth와 retention truth를 같은 컬럼에 매달지 않는 것**이다.

## 실전 프로토콜

### 1. create / claim path

1. bucket/resource에 해당하는 guard row를 잠그거나 conditionally update할 준비를 한다
2. 같은 bucket의 stale active row를 canonical predicate로 찾는다
3. `expires_at <= now()`이면서 아직 active면, 같은 트랜잭션에서 `released_at`을 채우고 guard 수량을 한 번만 감소시킨다
4. 그다음 guard capacity를 검사하고 새 claim을 삽입한다

핵심은 "deadline이 지난 row를 읽기에서 무시"가 아니라, **release를 commit한 뒤에 capacity를 다시 판정**하는 것이다.

### 2. expiry / cancel / confirm path

이 경로들의 책임은 status label을 바꾸는 것이 아니라 active predicate를 옮기는 것이다.

- expire: `released_at`을 채우고 guard row를 감소
- cancel: `released_at`을 채우고 guard row를 감소
- confirm:
  - confirm 자체가 계속 capacity를 점유하는 상태라면 `released_at`을 채우지 않는다
  - hold에서 booking으로 authority를 넘기는 구조라면 hold release와 booking acquire를 같은 트랜잭션에서 handoff한다

따라서 `status='EXPIRED'`만 먼저 찍고 guard row 감소를 다른 배치에 미루면 active predicate alignment가 깨진다.

### 3. archive / soft-delete worker

archive worker의 책임은 보관 정리다.

- `deleted_at` 채우기
- history table 이관
- 오래된 released row purge

이 worker가 guard row를 건드리기 시작하면 cleanup lag가 곧 capacity truth가 된다.  
그 순간부터 admission, runtime counter, reconciliation이 서로 엇갈리기 쉽다.

## 코드로 보기

```sql
CREATE TABLE reservation_claim (
  claim_id BIGINT PRIMARY KEY,
  bucket_id BIGINT NOT NULL,
  qty INT NOT NULL,
  status TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  released_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ,
  version BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE reservation_guard (
  bucket_id BIGINT PRIMARY KEY,
  reserved_qty INT NOT NULL,
  capacity INT NOT NULL,
  version BIGINT NOT NULL DEFAULT 0
);
```

```sql
-- canonical reconciliation: guard row와 detail row가 같은 active predicate를 보는지 확인
SELECT g.bucket_id,
       g.reserved_qty AS guard_qty,
       COALESCE(SUM(c.qty), 0) AS detail_qty
FROM reservation_guard g
LEFT JOIN reservation_claim c
  ON c.bucket_id = g.bucket_id
 AND c.released_at IS NULL
 AND c.status IN ('HELD', 'PENDING_PAYMENT', 'CONFIRMED')
GROUP BY g.bucket_id, g.reserved_qty, g.capacity
HAVING COALESCE(SUM(c.qty), 0) <> g.reserved_qty
    OR COALESCE(SUM(c.qty), 0) > g.capacity;
```

```sql
-- expired row를 release 후보로 고르되, deadline만으로 active set에서 빼지는 않는다
SELECT claim_id, qty
FROM reservation_claim
WHERE bucket_id = :bucket_id
  AND status IN ('HELD', 'PENDING_PAYMENT')
  AND released_at IS NULL
  AND expires_at <= now()
FOR UPDATE;
```

위 두 쿼리의 핵심은 같다.

- active membership는 `released_at IS NULL`이 정의한다
- `expires_at`은 release candidate 탐지에만 쓰인다
- `deleted_at`은 guard reconciliation predicate에 등장하지 않는다

## 시나리오 1. 쿠폰 claim capacity

규칙:

- campaign별 `qty` 합계는 `capacity` 이하
- `HELD`는 5분 뒤 자동 만료
- `CONFIRMED`는 계속 capacity를 점유

틀린 정렬:

- admission은 `expires_at > now()` 합계만 본다
- sweeper가 몇 분 뒤 `released_at`과 guard 감소를 처리한다
- reconciliation은 `deleted_at IS NULL` 조건으로 guard를 검증한다

결과:

- 사용자에게는 남은 수량이 있어 보인다
- guard row는 아직 만료분을 reserved로 잡고 있다
- archive가 늦으면 reconciliation도 drift를 못 본다

맞는 정렬:

- admission은 stale hold를 잠그고 `released_at`을 채운 뒤 guard를 재판정한다
- sweeper는 hot path가 놓친 stale row를 수렴시킨다
- reconciliation은 `released_at IS NULL` 합계를 guard와 비교한다

## 시나리오 2. multi-day room-type inventory

규칙:

- `(room_type_id, stay_day)`별 capacity가 있다
- hold는 day별 수량을 잡고 `expires_at` 후 release되어야 한다
- reschedule은 old/new day union을 한 번에 다룬다

여기서 alignment가 깨지는 흔한 지점:

- create path는 day guard row를 본다
- reschedule path는 old booking day를 `deleted_at` 기준으로 뺀다
- reconciliation job은 `expires_at > now()`만 보고 일별 active qty를 계산한다

이 경우 같은 stay_day라도 path마다 active row 집합이 달라진다.  
결국 day guard는 맞는데 reschedule만 실패하거나, guard는 비었는데 reconciliation이 초과를 못 잡는 식의 이상 증상이 나온다.

해결 기준은 단순하다.

- 모든 path가 같은 `resource/day + released_at` predicate를 쓴다
- old/new union lock 뒤에 deadline-past row를 먼저 finalize한다
- history/archive는 day guard와 분리된 lifecycle로 다룬다

## 운영 체크리스트

- admission check, guard decrement, reconciliation scan의 `WHERE` 절을 문서로 나란히 적어 보면 정말 같은 row 집합인가
- `expires_at <= now() AND released_at IS NULL` row가 guard qty에 포함되는 동안 admission이 이를 무시하지 않는가
- `deleted_at`을 채우는 경로가 guard row나 active counter를 만지지 않는가
- `status='EXPIRED'` 또는 `deleted_at IS NOT NULL`인데 `released_at IS NULL`인 anomaly를 별도 alert로 보나
- split 모델이라면 guard와 reconciliation이 history가 아니라 `*_active`만 읽는가

## 꼬리질문

> Q: `expires_at`이 지났으면 admission check에서 그냥 active set에서 빼면 되지 않나요?
> 의도: deadline과 release commit을 구분하는지 확인
> 핵심: deadline은 release 후보일 뿐이고, guard row와 detail truth가 아직 handoff되지 않았다면 그냥 빼면 false vacancy가 생긴다

> Q: soft delete가 끝났을 때 guard row를 줄이면 더 단순하지 않나요?
> 의도: cleanup semantics와 blocking semantics를 구분하는지 확인
> 핵심: 그러면 archive backlog가 곧 capacity backlog가 되어 runtime truth가 cleanup 속도에 종속된다

> Q: reconciliation은 대충 active 비슷한 조건이면 되지 않나요?
> 의도: repair scan이 runtime predicate와 완전히 같아야 한다는 점을 이해하는지 확인
> 핵심: scan predicate가 다르면 drift를 놓치거나 가짜 drift를 계속 보고하게 된다

## 한 줄 정리

capacity guard에서 `expires_at`은 release 후보, `released_at`은 실제 capacity handoff, soft delete는 retention cleanup이다. admission check·guard row·reconciliation이 이 세 의미를 똑같이 해석할 때만 false full과 false vacancy 없이 invariant가 유지된다.
