# Expired-Unreleased Drift Runbook

> 한 줄 요약: deadline은 지났는데 blocking truth가 아직 살아 있는 row는 단순 cleanup backlog가 아니라 availability와 constraint arbitration을 동시에 흔드는 incident이므로, backlog count·release lag·post-expiry conflict를 같은 runbook으로 다뤄야 한다.

**난이도: 🔴 Advanced**

관련 문서:

- [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md)
- [Expiry Worker Race Patterns](./expiry-worker-race-patterns.md)
- [Active Hold Table Split Pattern](./active-hold-table-split-pattern.md)
- [Soft Delete, Uniqueness, and Data Lifecycle Design](./soft-delete-uniqueness-indexing-lifecycle.md)
- [Queue Claim with `SKIP LOCKED`, Fairness, and Starvation Trade-offs](./queue-claim-skip-locked-fairness.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [Slotization Migration and Backfill Playbook](./slotization-migration-backfill-playbook.md)

retrieval-anchor-keywords: expired-unreleased drift runbook, expired but unreleased, deadline passed still blocking, release lag slo, post-expiry conflict, stale hold repair, blocking truth repair, cleanup lag repair, active predicate incident, reservation hold remediation, expired hold runbook, operability runbook, confirm vs expire race, opportunistic release

## 핵심 개념

`expired-unreleased`는 wall-clock deadline은 지났지만, blocking truth는 아직 active set 안에 남아 있는 상태다.

대표 형태:

- `expires_at <= now()`인데 `released_at IS NULL`
- active/history split을 쓴다면 `*_active` table에 deadline-past row가 그대로 남음
- generated active key 또는 `deleted_at IS NULL` scope가 아직 살아 있어서 uniqueness/exclusion이 계속 충돌함

이 incident는 두 가지로 드러난다.

- coherent lag: reads와 constraints가 모두 "아직 막힘"으로 본다. predicate는 일치하지만 release lag SLO를 위반한다.
- predicate drift: reads는 이미 비었다고 보는데 constraints만 계속 막는다. lifecycle contract 자체가 어긋났다.

이 runbook의 목적은 세 가지다.

1. expirable blocking row의 backlog와 lag를 숫자로 고정한다.
2. idempotent batch repair로 blocking truth를 안전하게 해제한다.
3. backlog가 다시 쌓이지 않게 worker/lock/schema 원인을 분리한다.

## 0. 먼저 expirable blocking predicate를 적어 둔다

아래 예시는 이런 구조를 가정한다.

- table: `reservation_hold(id, resource_id, status, expires_at, released_at, deleted_at, version, updated_at)`
- expirable blocking state: deadline이 지나면 release되어야 하는 상태 (`HELD`, `PENDING_PAYMENT` 등)
- non-expirable blocking state: deadline이 지나도 계속 자원을 막는 상태 (`CONFIRMED`, `ALLOCATED` 등)

핵심은 **deadline이 지나면 해제되어야 하는 row만** repair 대상으로 삼는 것이다.  
원래 계속 blocking해야 하는 allocation row까지 같이 풀어 버리면 oversell incident로 바뀐다.

blocking truth별로 detection predicate를 먼저 고정한다.

| 모델 | expired-unreleased condition |
|---|---|
| single table + `released_at` | `expires_at <= now() AND released_at IS NULL AND status IN (...)` |
| active/history split | `expires_at <= now()` row가 `*_active` relation에 남아 있음 |
| generated active key / soft delete 기반 | `expires_at <= now()`인데 active key가 살아 있거나 `deleted_at` 기준 active scope에 남아 있음 |

## 1. detection queries

### 1. backlog 크기와 oldest lag를 먼저 본다

```sql
SELECT
  COUNT(*) AS expired_unreleased_count,
  MIN(expires_at) AS oldest_expired_at,
  MAX(now() - expires_at) AS max_release_lag
FROM reservation_hold
WHERE status IN ('HELD', 'PENDING_PAYMENT')
  AND released_at IS NULL
  AND expires_at <= now();
```

이 숫자는 현재 blast radius의 최솟값이다.

- `expired_unreleased_count > 0`
- `oldest_expired_at`이 계속 과거로 밀림
- `max_release_lag`가 alert budget을 넘김

이면 cleanup이 아니라 blocking truth incident로 취급한다.

### 2. lag bucket을 보면 "막혔는지" vs "못 따라가는지"를 나누기 쉽다

```sql
SELECT
  CASE
    WHEN expires_at > now() - INTERVAL '30 seconds' THEN '00-30s'
    WHEN expires_at > now() - INTERVAL '2 minutes' THEN '30s-2m'
    WHEN expires_at > now() - INTERVAL '10 minutes' THEN '2m-10m'
    ELSE '10m+'
  END AS lag_bucket,
  COUNT(*) AS row_count
FROM reservation_hold
WHERE status IN ('HELD', 'PENDING_PAYMENT')
  AND released_at IS NULL
  AND expires_at <= now()
GROUP BY 1
ORDER BY 1;
```

- 짧은 bucket만 많다: worker는 돌지만 tail이 길어지는 중일 수 있다
- 긴 bucket이 쌓인다: worker stall, lock contention, transition bug 가능성이 높다

### 3. 실제로 "지금은 비어 있어야 하는" false blocker scope를 본다

```sql
WITH expired_blocker AS (
  SELECT resource_id,
         COUNT(*) AS blocker_rows,
         MIN(expires_at) AS oldest_expired_at
  FROM reservation_hold
  WHERE status IN ('HELD', 'PENDING_PAYMENT')
    AND released_at IS NULL
    AND expires_at <= now()
  GROUP BY resource_id
),
live_blocker AS (
  SELECT DISTINCT resource_id
  FROM reservation_hold
  WHERE released_at IS NULL
    AND (
      (status IN ('HELD', 'PENDING_PAYMENT') AND expires_at > now())
      OR status IN ('CONFIRMED', 'ALLOCATED')
    )
)
SELECT e.resource_id,
       e.blocker_rows,
       e.oldest_expired_at
FROM expired_blocker e
LEFT JOIN live_blocker l
  ON l.resource_id = e.resource_id
WHERE l.resource_id IS NULL
ORDER BY e.oldest_expired_at ASC
LIMIT 50;
```

이 결과는 "지금 남아 있는 blocker가 사실상 모두 deadline-past expirable row"인 scope다.  
availability read가 `expires_at > now()`만 본다면, 사용자에게 가장 먼저 불만으로 드러나는 집합이기도 하다.

여기서 `CONFIRMED`, `ALLOCATED` 같은 non-expirable blocking state 집합은 도메인에 맞게 반드시 바꿔 넣어야 한다.

### 4. terminal state인데 still blocking인 anomaly를 분리한다

```sql
SELECT id,
       resource_id,
       status,
       expires_at,
       released_at,
       deleted_at,
       updated_at
FROM reservation_hold
WHERE expires_at <= now()
  AND released_at IS NULL
  AND (
    status IN ('EXPIRED', 'CANCELED')
    OR deleted_at IS NOT NULL
  )
ORDER BY expires_at ASC
LIMIT 100;
```

이 쿼리에 row가 보이면 단순 worker backlog가 아니라 **transition contract bug** 가능성이 크다.

- status는 terminal인데 blocking truth는 살아 있음
- archive metadata는 찍혔는데 active membership가 안 빠짐

이 경우에는 repair 전에 상태 전이 코드를 먼저 점검해야 한다.

### 5. active/history split 모델이면 active relation만 보면 된다

```sql
SELECT hold_id,
       resource_id,
       expires_at
FROM reservation_hold_active
WHERE expires_at <= now()
ORDER BY expires_at ASC
LIMIT 100;
```

split 모델에서 핵심 신호는 단순하다.  
deadline-past row가 active table에 남아 있다는 사실 자체가 expired-unreleased drift다.

## 2. 권장 SLI / SLO

아래 숫자는 countdown-driven reservation/lease 경로에서 시작점으로 쓰기 좋은 기본값이다.  
UX가 "타이머가 0초가 되면 즉시 다시 잡을 수 있다"를 약속한다면 더 엄격하게 잡아야 한다.

| SLI | 정의 | 시작 SLO | 의미 |
|---|---|---|---|
| `release_lag_p95` | expirable row가 deadline을 넘긴 뒤 release될 때까지 걸린 시간 p95 | 30초 이하 | 대부분의 만료는 worker 1~2 cycle 안에 정리되어야 함 |
| `release_lag_p99` | 같은 분포의 p99 | 2분 이하 | tail이 길어지기 시작하면 drift incident로 본다 |
| `expired_unreleased_rows_older_than_5m` | 5분 이상 지난 expired-unreleased row 수 | 0 | 숨은 backlog를 허용하지 않음 |
| `post_expiry_conflict_rate` | deadline-past blocker 때문에 claim/insert가 실패한 비율 | 0.1% 이하, 즉시 재예약 UX면 0 budget | 사용자 체감 오류를 직접 측정 |
| `repair_drain_time` | alert 발화 후 backlog가 SLO 안으로 복귀하는 시간 | 15분 이하 | 수동/자동 복구 절차의 operability 기준 |

권장 alert 규칙:

- `expired_unreleased_rows_older_than_5m > 0`가 두 윈도우 연속이면 page
- `release_lag_p99`가 평소 대비 3배 이상 치솟으면 page
- `post_expiry_conflict_rate`가 baseline 대비 급증하면 DB 지표와 함께 묶어 incident 생성

중요한 점은 archive/purge SLO와 섞지 않는 것이다.

- `released_at` 또는 active table row 삭제는 **blocking truth SLO**
- `deleted_at`, `archived_at`, purge 완료는 **retention / cleanup SLO**

둘을 섞으면 archive가 늦은 문제와 booking 불가 문제를 같은 숫자로 보게 된다.

## 3. triage 순서

| 관측 | 의미 | 다음 액션 |
|---|---|---|
| backlog count와 oldest lag가 같이 증가 | worker가 멈췄거나 lock에 막혔을 가능성 | repair 전에 worker health, lock wait, batch saturation 확인 |
| `status='EXPIRED'` 또는 `deleted_at IS NOT NULL` row가 still blocking | transition bug 또는 non-atomic move | write path / worker code 수정 없이 repair만 하면 재발 |
| expired-unreleased row는 거의 없는데 사용자 conflict만 증가 | read cache / projection / app routing 이슈일 수 있음 | 이 runbook보다 read-model 또는 cache 쪽으로 라우팅 |
| active/history split인데 active row가 줄지 않음 | move transaction 실패 또는 history insert 오류 | move path journal과 dead letter 확인 |

여기서 중요한 금지사항:

- unique/exclusion 제약을 임시로 끄지 않는다
- expirable row를 확인하지 않고 무작정 hard delete 하지 않는다
- `CONFIRMED` 같은 non-expirable allocation row를 deadline 기준으로 release하지 않는다

제약을 끄는 순간 incident는 사라져 보이지만, 실제로는 double booking이나 duplicate allocation으로 바뀐다.

## 4. repair steps

### 1. bounded batch로 repair 대상을 잠근다

한 번에 전체를 밀지 말고, oldest-first + `SKIP LOCKED` + small batch로 진행한다.

```sql
WITH candidates AS (
  SELECT id
  FROM reservation_hold
  WHERE status IN ('HELD', 'PENDING_PAYMENT')
    AND released_at IS NULL
    AND expires_at <= now()
  ORDER BY expires_at ASC
  FOR UPDATE SKIP LOCKED
  LIMIT 200
)
UPDATE reservation_hold h
SET status = 'EXPIRED',
    released_at = now(),
    updated_at = now(),
    version = h.version + 1
FROM candidates c
WHERE h.id = c.id
  AND h.released_at IS NULL
RETURNING h.id, h.resource_id, h.expires_at, h.released_at;
```

원칙:

- repair predicate는 detection predicate와 같아야 한다
- `released_at IS NULL` 같은 idempotent 조건을 마지막 `UPDATE`에도 다시 넣는다
- terminal status 라벨은 도메인에 맞게 바꾸되, release truth는 같은 트랜잭션에서 materialize한다

MySQL 8.0 계열이면 같은 트랜잭션에서 candidate id를 `SELECT ... FOR UPDATE SKIP LOCKED`로 먼저 뽑고, 그 id 집합만 `UPDATE ... WHERE id IN (...)`로 갱신하면 된다.

### 2. active/history split 모델이면 mutate가 아니라 move로 끝낸다

```sql
WITH moved AS (
  DELETE FROM reservation_hold_active
  WHERE hold_id IN (
    SELECT hold_id
    FROM reservation_hold_active
    WHERE expires_at <= now()
    ORDER BY expires_at ASC
    FOR UPDATE SKIP LOCKED
    LIMIT 200
  )
  RETURNING hold_id,
            resource_id,
            expires_at,
            now() AS released_at
)
INSERT INTO reservation_hold_history (
  hold_id,
  resource_id,
  expires_at,
  final_state,
  released_at,
  release_reason,
  source_transition
)
SELECT hold_id,
       resource_id,
       expires_at,
       'EXPIRED',
       released_at,
       'expired_unreleased_repair',
       'manual_or_automated_repair'
FROM moved;
```

split 모델에서는 "active relation에서 제거되는 순간"이 release truth다.  
active row를 terminal status로 남겨 두면 다시 single-table drift가 돌아온다.

### 3. 배치 사이사이 acceptance query를 반복한다

매 batch 뒤에는 최소한 이 셋을 다시 본다.

1. `expired_unreleased_count`
2. `oldest_expired_at`
3. terminal-state-but-blocking anomaly count

count가 줄어도 `oldest_expired_at`이 계속 오래된 채면 일부 hot scope가 잠겨 있거나 transition bug가 남아 있을 수 있다.

### 4. backlog가 바로 다시 쌓이면 repair를 멈추고 원인을 바꾼다

반복 repair만으로 버티지 말고, 아래 원인을 분리한다.

- expiry worker consumer lag / scheduler stop
- confirm path와 expiry path 사이의 row lock/version contract 부재
- `deleted_at` 또는 active generated key가 blocking truth를 대신하는 설계
- giant batch나 lock contention 때문에 expiry worker가 계속 starvation

즉 repair는 종료 조건이 아니라 **원인 분리용 time-buying step**일 수 있다.

## 5. 복구 완료 기준

다음 네 조건을 같이 만족해야 incident를 닫는다.

1. `expired_unreleased_rows_older_than_5m = 0`
2. terminal-state-but-blocking anomaly count = 0
3. `post_expiry_conflict_rate`가 baseline으로 회복
4. 두 개 이상의 연속 관측 윈도우에서 backlog가 다시 증가하지 않음

여기서 `count = 0` 하나만 보고 닫지 않는 이유는, worker가 잠깐 따라잡은 뒤 다시 밀릴 수 있기 때문이다.

## 6. 재발 방지 구조 개선

incident가 두 번 이상 반복되면 보통 운영 튜닝보다 구조 교정이 필요하다.

- claim path에서 stale row를 잠그고 opportunistic release 후 재판단한다
- blocking truth를 `deleted_at`이 아니라 `released_at` 또는 active relation row presence로 옮긴다
- expiry worker는 `FOR UPDATE SKIP LOCKED` 또는 version check로 confirm path와 합의한다
- release lag SLO와 archive/purge SLO를 분리 계측한다
- active/history split이 맞는 도메인이면 cleanup lag가 arbitration truth를 못 건드리게 relation을 나눈다

구조적 방향은 [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md)와 [Active Hold Table Split Pattern](./active-hold-table-split-pattern.md)에서 더 자세히 이어 볼 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| worker throughput만 올린다 | 즉시 시도하기 쉽다 | predicate bug면 재발한다 | backlog 원인이 순수 capacity 부족일 때 |
| bounded repair batch | blast radius를 줄이며 빠르게 unblock할 수 있다 | 근본 원인은 그대로 남을 수 있다 | active truth를 당장 복구해야 할 때 |
| claim path opportunistic release | 사용자 체감 lag를 크게 줄인다 | write path와 locking contract가 복잡해진다 | 즉시 재예약 UX가 중요한 시스템 |
| active/history split | cleanup lag가 blocking truth를 오염시키지 못한다 | move transaction과 history 설계가 필요하다 | 긴 보관 + 엄격한 live arbitration이 함께 필요한 경우 |

## 꼬리질문

> Q: expired-unreleased incident에서 제약을 잠시 꺼서 backlog를 먼저 비우면 안 되나요?
> 의도: availability 복구와 invariant 파괴를 구분하는지 확인
> 핵심: 안 된다. false blocker를 없애는 대신 double booking이나 duplicate allocation을 만들 수 있다

> Q: `status='EXPIRED'`인데도 still blocking이면 worker가 늦은 것뿐인가요?
> 의도: backlog와 transition bug를 분리하는지 확인
> 핵심: 아니다. status는 terminal인데 blocking truth가 살아 있으므로 write contract가 어긋난 것이다

> Q: archive lag SLO만 지키면 release lag도 자연히 해결되나요?
> 의도: cleanup SLO와 blocking SLO를 분리하는지 확인
> 핵심: 아니다. archive는 retention 문제이고, release는 live arbitration 문제라서 별도 budget이 필요하다

## 한 줄 정리

expired-unreleased drift runbook의 본질은 "만료된 row를 얼마나 빨리 지우느냐"가 아니라, **deadline이 지난 expirable blocker를 얼마나 빨리 active truth 밖으로 이동시키고 그 lag를 별도 SLO로 운영하느냐**에 있다.
