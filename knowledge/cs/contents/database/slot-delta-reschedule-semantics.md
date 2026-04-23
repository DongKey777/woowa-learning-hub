# Slot Delta Reschedule Semantics

> 한 줄 요약: slot claim table에서는 create/cancel/reschedule을 서로 다른 SQL로 흩뜨리지 말고, `old_slots/new_slots`에서 계산한 delta를 같은 union lock과 같은 tombstone contract 아래에서 한 번만 적용해야 backfill, catch-up, cleanup이 같은 occupancy truth를 본다.

**난이도: 🔴 Advanced**

관련 문서:

- [Hot-Path Slot Arbitration Choices](./hot-path-slot-arbitration-choices.md)
- [Slotization Migration and Backfill Playbook](./slotization-migration-backfill-playbook.md)
- [Reservation Reschedule and Cancellation Transition Patterns](./reservation-reschedule-cancellation-transition-patterns.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Active Hold Table Split Pattern](./active-hold-table-split-pattern.md)
- [Soft Delete, Uniqueness, and Data Lifecycle Design](./soft-delete-uniqueness-indexing-lifecycle.md)
- [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md)
- [Expiry Worker Race Patterns](./expiry-worker-race-patterns.md)

retrieval-anchor-keywords: slot delta reschedule semantics, slot claim delta apply, create cancel reschedule slot claim, booking slot claim tombstone cleanup, slot union lock, old slots new slots union, slot release tombstone watermark, slot backfill reschedule delta, slot claim active history split, slot cleanup lag, release tombstone compaction, slot occupancy parity, slotization reschedule backfill, interval to slot delta semantics, slot claim mutation idempotency

## 핵심 개념

slot claim table로 옮긴 뒤에도 문제의 본질은 같다.

- 어떤 booking이 지금 어떤 slot 집합을 점유하는가
- 그 집합의 변화가 create/cancel/reschedule/retry에서 한 번만 적용되는가
- release 흔적을 CDC/backfill/replay가 끝까지 따라갈 수 있는가

즉 slotization 뒤의 write path는 "row를 넣거나 지운다"가 아니라, 아래 네 단계를 같은 계약으로 묶는 일이다.

1. `old_slots`를 현재 commit된 active truth에서 읽는다
2. `new_slots`를 canonical slot policy로 다시 펼친다
3. `slot_delta = claim/release/keep`를 계산한다
4. tombstone cleanup까지 같은 version/watermark 언어로 닫는다

여기서 핵심은 tombstone이 **release evidence**이지 **blocking truth**가 아니라는 점이다.

- admission / overlap / capacity 판단은 active claim만 본다
- tombstone은 catch-up, replay, audit, rollback window를 위해 남긴다
- cleanup lag가 admission 규칙을 바꾸지 못하게 active path와 tombstone path를 분리한다

## 먼저 고정할 slot delta contract

slot claim table에서는 최소한 아래 용어를 고정해 두는 편이 안전하다.

| 이름 | 뜻 | create / cancel / reschedule 예시 |
|---|---|---|
| `old_slots` | 지금 active slot claim이 점유 중인 slot 집합 | create는 `∅`, cancel은 기존 active claims, reschedule은 현재 claims |
| `new_slots` | 전이 후 점유해야 할 canonical slot 집합 | create는 target slots, cancel은 `∅`, reschedule은 새 target slots |
| `touched_slots` | `old_slots ∪ new_slots` | create는 `new_slots`, cancel은 `old_slots`, reschedule은 old/new 합집합 |
| `slot_delta` | `claim = new - old`, `release = old - new`, `keep = old ∩ new` | extend/move/shorten/cancel을 하나의 delta vocabulary로 표현 |
| `claim_version` | 같은 booking의 slot set 버전 | retry, catch-up, tombstone cleanup 기준점 |

중요한 규칙은 두 가지다.

- `old_slots`는 클라이언트 payload나 캐시가 아니라 **현재 active claim table**에서 계산한다
- `new_slots`는 create path와 같은 slot expander, 같은 timezone/DST 규칙, 같은 active predicate를 써야 한다

즉 cancel은 `new_slots = ∅`인 delta이고, reschedule은 old/new가 모두 있는 delta일 뿐이다.

## 권장 relation 분리

slot claim table에 tombstone을 같은 hot relation에 남겨 두면 active truth와 cleanup truth가 다시 섞인다. 보통은 아래처럼 분리하는 편이 설명력이 높다.

```sql
CREATE TABLE booking_slot_guard (
  tenant_id BIGINT NOT NULL,
  resource_id BIGINT NOT NULL,
  slot_start TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (tenant_id, resource_id, slot_start)
);

CREATE TABLE booking_slot_claim_active (
  tenant_id BIGINT NOT NULL,
  resource_id BIGINT NOT NULL,
  slot_start TIMESTAMPTZ NOT NULL,
  booking_id BIGINT NOT NULL,
  claim_version BIGINT NOT NULL,
  source_mutation_key VARCHAR(100) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, resource_id, slot_start),
  UNIQUE (booking_id, slot_start)
);

CREATE TABLE booking_slot_claim_tombstone (
  booking_id BIGINT NOT NULL,
  tenant_id BIGINT NOT NULL,
  resource_id BIGINT NOT NULL,
  slot_start TIMESTAMPTZ NOT NULL,
  released_version BIGINT NOT NULL,
  release_reason VARCHAR(32) NOT NULL,
  source_mutation_key VARCHAR(100) NOT NULL,
  cleanup_after_watermark BIGINT NOT NULL,
  released_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (booking_id, slot_start, released_version)
);
```

이 구조의 의도는 단순하다.

- `booking_slot_guard`: 아직 claim row가 없는 빈 slot도 잠글 수 있게 한다
- `booking_slot_claim_active`: admission truth와 uniqueness를 여기만 기준으로 삼는다
- `booking_slot_claim_tombstone`: release 흔적과 cleanup watermark를 보존한다

만약 tombstone을 같은 테이블에 soft delete로 눌러 넣는다면:

- active uniqueness가 partial index / generated column에 매달리고
- hot path가 tombstone bloat와 통계를 같이 떠안고
- cleanup lag가 곧 availability 오류로 번지기 쉬워진다

그래서 slot claim path는 [Active Hold Table Split Pattern](./active-hold-table-split-pattern.md)의 active/history 분리 원칙을 그대로 가져오는 편이 낫다.

## mutation별 delta application

### 1. create

create는 `old_slots = ∅`인 가장 단순한 delta다.

- `claim = new_slots`
- `release = ∅`
- `touched_slots = new_slots`

하지만 단순하다고 해서 그냥 insert만 하면 안 된다.

- 빈 slot은 row lock 대상이 없으므로 `booking_slot_guard` 같은 guard surface를 먼저 잠가야 한다
- 같은 booking retry와 다른 booking 충돌을 구분해야 한다
- catch-up/backfill consumer가 이해할 수 있게 `claim_version`과 mutation key를 남겨야 한다

즉 create의 본질은 "row 추가"가 아니라 **새 active slot set을 최초로 소유하게 하는 delta commit**이다.

### 2. cancel / expire

cancel은 `new_slots = ∅`인 release delta다.

- `claim = ∅`
- `release = old_slots`
- `touched_slots = old_slots`

여기서 빠지기 쉬운 함정이 있다.

- active claim delete와 tombstone insert를 다른 트랜잭션으로 나누면 crash 사이에 release 흔적이 사라진다
- tombstone 없이 hard delete만 하면 lagging catch-up이 release를 모른 채 stale claim을 다시 만들 수 있다
- tombstone을 blocker로 해석하면 cleanup backlog가 false conflict가 된다

따라서 cancel/expire는 **active claim 제거 + tombstone 기록**이 같은 transaction에서 끝나야 한다.

### 3. reschedule

reschedule은 slot claim path에서 가장 위험한 delta다.

- `claim = new_slots - old_slots`
- `release = old_slots - new_slots`
- `keep = old_slots ∩ new_slots`
- `touched_slots = old_slots ∪ new_slots`

핵심은 세 가지다.

1. `release`를 먼저 commit하고 `claim`을 나중에 하지 않는다
2. `keep` slot도 함께 잠가서 concurrent cancel/create와 엇갈리지 않게 한다
3. reschedule을 create/cancel 두 API나 두 outbox event로 쪼개지 않는다

특히 partial overlap이 있는 move/shorten/extend에서 `keep`을 잠그지 않으면:

- 다른 요청이 middle slot을 끼어먹고
- 같은 booking에 대한 retry/cancel이 double release를 만들고
- backfill diff가 "release 누락"인지 "실제 move"인지 구분을 잃는다

### 4. backfill / catch-up consumer

migration이나 replay 경로도 결국 같은 delta vocabulary를 소비해야 한다.

- snapshot backfill은 active slot snapshot만 채우고 tombstone을 blocker로 보지 않는다
- live catch-up은 create/cancel/reschedule을 explicit delta event로 재생한다
- consumer는 "row가 사라졌으니 cancel이겠지"처럼 snapshot diff로 전이를 추론하지 않는다

즉 backfill과 live write가 같은 `claim_version`, 같은 mutation key, 같은 release reason을 이해해야 cleanup watermark도 닫을 수 있다.

## union-lock handling

slot claim table에서 가장 흔한 실수는 **existing active rows만 잠그는 것**이다.  
reschedule의 새 target slot은 아직 row가 없을 수 있으므로 row lock만으로는 union을 잠갔다고 말할 수 없다.

안전한 패턴은 아래와 같다.

1. booking row 또는 booking aggregate를 먼저 fenced lock으로 잡는다
2. `old_slots/new_slots/touched_slots`를 계산한다
3. `touched_slots`에 해당하는 `booking_slot_guard` row를 canonical order로 잠근다
4. 같은 잠금 아래에서 `claim` subset에 대한 conflict를 active claim table로 재검사한다
5. 그 뒤에만 active claim delete/insert와 tombstone write를 적용한다

canonical order 예:

```text
lock order
1. pool/day guard if present
2. unit/day guard if present
3. slot guard rows sorted by (tenant_id, resource_id, slot_start)
4. active claim rows owned by the current booking
```

여기서 중요한 포인트:

- create는 `new_slots`만 잠그지만, reschedule은 반드시 `old ∪ new`를 잠근다
- cancel도 release-only fast path로 빼지 않고 `old_slots`를 같은 order로 잠근다
- multi-day / multi-resource move는 [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)의 day-level canonical ordering 위에 slot lock을 얹는 편이 안전하다

`DELETE old -> COMMIT -> INSERT new` 두 단계로 나누는 순간, slot claim table은 다시 "틈새를 노출하는 interval path"로 돌아간다.

## tombstone cleanup semantics

tombstone cleanup은 storage housekeeping이 아니라 replay contract의 마지막 단계다.

### 1. tombstone을 왜 남기나

- catch-up consumer가 release를 보지 못하면 stale active projection을 다시 세울 수 있다
- rollback/probation window에서는 "이 slot이 왜 비었는가"를 재현할 증거가 필요하다
- booking 단위 diff 검증에서 release 누락과 단순 absence를 구분해야 한다

즉 tombstone은 "지웠다"가 아니라 **"이 version에서 이 slot을 의도적으로 release했다"**는 증거다.

### 2. cleanup은 age만 보고 하지 않는다

cleanup 기준은 보통 둘을 같이 본다.

- 모든 catch-up / CDC / replay consumer의 최소 watermark가 tombstone의 `cleanup_after_watermark`를 지났는가
- probation / rollback window가 끝났는가

둘 중 하나라도 안 닫혔는데 age만 보고 purge하면 lagging consumer가 release event를 영영 놓친다.

### 3. cleanup 전 검증해야 할 것

- tombstone 대상 slot에 active claim이 다시 살아 있는가
- active parity compare에서 mismatch가 남아 있지 않은가
- 같은 mutation key의 delta가 downstream artifact에 반영됐는가

즉 cleanup worker는 "오래됐으니 지운다"가 아니라, **watermark와 parity를 확인한 뒤 physical delete 또는 archive move를 한다**고 생각하는 편이 맞다.

### 4. tombstone을 blocker로 해석하지 않는다

tombstone이 active predicate에 섞이면 다음이 곧바로 깨진다.

- availability probe가 false conflict를 낸다
- unique slot claim이 cleanup backlog에 발목 잡힌다
- active claim count와 release history count가 서로 다른 의미를 잃는다

그래서 admission query, overlap check, capacity reconciliation은 오직 active claim relation만 봐야 한다.

## 실전 시나리오

### 시나리오 1. 겹치는 일부 slot이 있는 reschedule

기존 예약:

- `old_slots = {10:00, 10:30, 11:00}`

변경 요청:

- `new_slots = {10:30, 11:00, 11:30}`

그러면 delta는 이렇게 읽는다.

- `keep = {10:30, 11:00}`
- `release = {10:00}`
- `claim = {11:30}`

이때 `10:30`, `11:00`를 잠그지 않으면:

- concurrent cancel이 전체 old set을 release하고
- 다른 create가 `11:00` 이후 일부 slot을 차지하고
- reschedule retry가 release/claim을 중복 적용할 수 있다

겹치는 slot이 있어도 union 전체를 잠그는 이유가 여기 있다.

### 시나리오 2. cancel 직후 catch-up lag가 남아 있는 migration

slot authoritative 전환 직전:

- active claim delete는 성공했다
- tombstone도 기록됐다
- 하지만 CDC consumer 하나가 fence watermark 뒤처져 있다

이때 tombstone cleanup을 먼저 해 버리면 lagging consumer는 release 사실을 모른 채 stale interval snapshot을 다시 반영할 수 있다.  
그래서 cleanup은 "cancel이 오래됐다"가 아니라 **모든 consumer가 그 release version을 넘겼다**는 증거 뒤에 와야 한다.

### 시나리오 3. expire worker와 API cancel이 동시에 온다

둘 다 `new_slots = ∅`라는 점은 같지만, mutation key는 달라질 수 있다.

- `cancel:{request_id}`
- `expiry:{booking_id}:{claim_version}`

이 경우 booking-local fence와 mutation log가 먼저 같은 final outcome을 결정해야 한다.  
그 뒤 tombstone은 한 번만 써야 하며, retry는 prior result를 재사용해야 한다.

## 코드로 보기

```text
slot delta protocol
1. claim mutation key
2. fence booking row / aggregate
3. old_slots = load current active claims for booking
4. new_slots = expand requested target with canonical slot policy
5. touched_slots = union(old_slots, new_slots)
6. lock slot guards for touched_slots in canonical order
7. recheck conflicts for claim slots against active claims
8. delete release slots from active claims
9. insert tombstones for deleted slots in the same transaction
10. insert claim slots into active claims
11. persist booking state + claim_version + mutation result
```

```sql
WITH released AS (
  DELETE FROM booking_slot_claim_active
  WHERE booking_id = :booking_id
    AND (tenant_id, resource_id, slot_start) IN (:release_slots)
  RETURNING booking_id, tenant_id, resource_id, slot_start
)
INSERT INTO booking_slot_claim_tombstone (
  booking_id,
  tenant_id,
  resource_id,
  slot_start,
  released_version,
  release_reason,
  source_mutation_key,
  cleanup_after_watermark,
  released_at
)
SELECT booking_id,
       tenant_id,
       resource_id,
       slot_start,
       :next_claim_version,
       :release_reason,
       :mutation_key,
       :cleanup_after_watermark,
       now()
FROM released;
```

```sql
INSERT INTO booking_slot_claim_active (
  tenant_id,
  resource_id,
  slot_start,
  booking_id,
  claim_version,
  source_mutation_key
)
VALUES (:tenant_id, :resource_id, :slot_start, :booking_id, :next_claim_version, :mutation_key);
```

핵심은 쿼리 문법보다, **release가 tombstone으로 남는 시점과 claim이 active truth로 보이는 시점이 같은 mutation transaction 안에 묶여 있는가**다.

## 체크리스트

- create/cancel/reschedule이 모두 `old_slots/new_slots/slot_delta` vocabulary로 표현되는가
- reschedule에서 `old ∪ new` 전체를 guard surface로 잠그는가
- 빈 slot도 잠글 수 있게 pre-seeded slot guard 또는 동등한 guard surface가 있는가
- active claim delete와 tombstone insert가 같은 트랜잭션에서 일어나는가
- tombstone cleanup이 age가 아니라 watermark + probation window 기준으로 닫히는가
- admission / overlap / capacity query가 tombstone relation을 절대 보지 않는가
- backfill / catch-up consumer가 explicit delta event와 mutation key를 이해하는가

## 꼬리질문

> Q: reschedule에서 old slot을 먼저 지우고 new slot을 나중에 넣으면 왜 안 되나요?
> 의도: union lock과 중간 빈 구간 노출 위험을 이해하는지 확인
> 핵심: 중간 순간에 다른 요청이 끼어들고, retry/cancel과 교차하면 release/claim이 두 번 적용될 수 있다

> Q: tombstone이 있는데 왜 active query에서 같이 보면 안 되나요?
> 의도: release evidence와 blocking truth를 구분하는지 확인
> 핵심: tombstone은 replay/audit용이지 현재 점유를 뜻하지 않아서 active predicate에 섞는 순간 false conflict와 bloat가 생긴다

> Q: cleanup을 왜 retention 시간만 보고 하지 않나요?
> 의도: backfill/catch-up watermark 의존성을 아는지 확인
> 핵심: lagging consumer가 release version을 아직 못 봤으면 tombstone purge가 곧 replay 손실이 되기 때문이다

## 한 줄 정리

slot claim table의 create/cancel/reschedule은 각각 다른 CRUD가 아니라, **같은 `slot_delta`를 union lock 아래서 한 번 적용하고 release는 tombstone watermark까지 보존한 뒤 cleanup하는 하나의 transition protocol**로 봐야 안전하다.
