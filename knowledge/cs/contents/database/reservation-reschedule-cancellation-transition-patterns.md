---
schema_version: 3
title: Reservation Reschedule and Cancellation Transition Patterns
concept_id: database/reservation-reschedule-cancellation-transition-patterns
canonical: true
category: database
difficulty: advanced
doc_role: primer
level: advanced
language: mixed
source_priority: 90
mission_ids:
- missions/roomescape
review_feedback_tags:
- reservation-transition
- reschedule-union-lock
- cancellation-drift
aliases:
- reservation reschedule cancellation transition
- booking transition union lock
- old scope new scope union
- extend shorten move cancel expiry cleanup admin override
- reservation mutation idempotency
- booking scope delta
- active predicate transition
- reservation release acquire handoff
- reschedule deadlock control
- cancellation drift prevention
- force cancel override booking
- transition fence booking
- mutation log reservation
- old new scope union lock
- booking move cancellation flow
- slot delta apply
- slot claim union lock
- slot tombstone cleanup
- roomescape 예약 변경 락 경계
- roomescape 예약 취소 경쟁
symptoms:
- roomescape 예약 변경에서 기존 슬롯을 먼저 풀고 새 슬롯을 다시 잡아도 되나요
- 예약 취소와 변경 요청이 동시에 오면 drift 없이 어떻게 직렬화하나요
- 예약 reschedule에서 old scope와 new scope를 같이 잠가야 하는 이유가 궁금해요
intents:
- definition
prerequisites:
- database/phantom-safe-booking-patterns-primer
- database/roomescape-reservation-cancel-reschedule-active-predicate-bridge
next_docs:
- database/active-predicate-drift-reservation-arbitration
- database/slot-delta-reschedule-semantics
- database/hold-expiration-predicate-drift
linked_paths:
- contents/database/guard-row-scope-design-multi-day-bookings.md
- contents/database/active-predicate-alignment-capacity-guards.md
- contents/database/active-predicate-drift-reservation-arbitration.md
- contents/database/expiry-worker-race-patterns.md
- contents/database/active-hold-table-split-pattern.md
- contents/database/shared-pool-guard-design-room-type-inventory.md
- contents/database/slotization-migration-backfill-playbook.md
- contents/database/slot-delta-reschedule-semantics.md
- contents/database/idempotency-key-and-deduplication.md
confusable_with:
- database/roomescape-reservation-concurrency-bridge
- database/roomescape-reservation-cancel-reschedule-active-predicate-bridge
forbidden_neighbors:
- contents/database/roomescape-reservation-concurrency-bridge.md
expected_queries:
- roomescape 예약 변경에서 old scope와 new scope를 같이 잠가야 하나요?
- 예약 reschedule을 release 후 acquire 두 단계로 처리하면 왜 위험해요?
- 예약 취소와 연장 요청이 동시에 오면 어떤 transition contract로 묶어야 해요?
contextual_chunk_prefix: |
  이 문서는 roomescape 같은 예약 미션에서 예약 변경과 취소를 release 후
  acquire 두 번의 write가 아니라 old/new scope handoff로 잡는 advanced
  primer다. 예약 이동과 취소를 한 계약으로 봐야 해, old scope new
  scope union lock, reschedule에서 drift가 왜 나, expiry cleanup도 같은
  전이야, slot delta를 어떻게 넘겨 같은 자연어 paraphrase가 본 문서의
  전이 패턴에 매핑된다.
---
# Reservation Reschedule and Cancellation Transition Patterns

> 한 줄 요약: 예약 변경은 `old scope release -> new scope acquire` 두 번의 write가 아니라, 기존/목표 scope의 합집합을 잠근 뒤 active predicate, counter, ledger, history를 한 번에 넘기는 transition contract로 다뤄야 deadlock과 drift를 같이 줄일 수 있다.

**난이도: 🔴 Advanced**

관련 문서:

- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Active Predicate Alignment for Capacity Guards](./active-predicate-alignment-capacity-guards.md)
- [Active Predicate Drift in Reservation Arbitration](./active-predicate-drift-reservation-arbitration.md)
- [Expiry Worker Race Patterns](./expiry-worker-race-patterns.md)
- [Active Hold Table Split Pattern](./active-hold-table-split-pattern.md)
- [Shared-Pool Guard Design for Room-Type Inventory](./shared-pool-guard-design-room-type-inventory.md)
- [Slotization Migration and Backfill Playbook](./slotization-migration-backfill-playbook.md)
- [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md)
- [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)

retrieval-anchor-keywords: reservation reschedule cancellation transition, booking transition union lock, old scope new scope union, extend shorten move cancel expiry cleanup admin override, reservation mutation idempotency, booking scope delta, active predicate transition, reservation release acquire handoff, reschedule deadlock control, cancellation drift prevention, force cancel override booking, transition fence booking, mutation log reservation, old new scope union lock, booking move cancellation flow, slot delta apply, slot claim union lock, slot tombstone cleanup

## 핵심 개념

예약 상태 전이에는 사실 두 종류의 경쟁이 동시에 있다.

- 같은 `reservation_id`를 누가 마지막으로 바꾸는가
- 그 예약이 점유하던 `resource/day/slot` 집합을 다른 예약과 어떻게 직렬화하는가

둘 중 하나만 설계하면 금방 새 구멍이 생긴다.

- reservation-local fence만 있고 scope union lock이 없으면: 같은 자원으로 move/extend가 교차하면서 deadlock이나 oversell이 난다
- union lock만 있고 mutation idempotency가 없으면: cancel/expiry/admin retry가 guard counter를 두 번 줄이거나 history를 두 번 남긴다

그래서 안전한 전이 contract는 항상 두 층으로 본다.

1. **reservation-local transition fence**
   - 같은 예약의 reschedule, cancel, expiry cleanup, admin override가 동시에 들어와도 하나의 committed 결과만 남기게 한다
   - 구현은 보통 `SELECT ... FOR UPDATE` 또는 `version` 기반 CAS, 그리고 mutation log의 unique key 조합으로 만든다
2. **scope-level union lock**
   - 전이 전후 예약이 점유하는 모든 guard key를 canonical order로 잠가, 다른 예약과의 경쟁을 같은 순서로 직렬화한다

핵심은 "전이"를 상태 라벨 변경으로 보지 말고, **blocking truth handoff**로 보는 것이다.

## 먼저 고정할 transition contract

아래 네 가지를 용어로 먼저 고정해 두면 경로별 special-case가 줄어든다.

| 이름 | 뜻 | 예시 |
|---|---|---|
| `old_scope` | 현재 active truth가 점유 중인 key 집합 | 기존 `room_id + stay_day` nights |
| `new_scope` | 전이 후 active truth가 점유해야 할 key 집합 | 연장 후 nights, 이동 후 새 room/day set |
| `touched_scope` | `old_scope ∪ new_scope` | reschedule union, cancel이면 `old_scope`, create면 `new_scope` |
| `scope_delta` | `acquire = new - old`, `release = old - new`, `keep = old ∩ new` | tail 연장, tail 단축, room move delta |

여기서 중요한 점은 두 가지다.

- `old_scope`는 "API 요청이 기억하는 예전 값"이 아니라 **지금 commit된 active truth**에서 계산해야 한다
- `new_scope`는 create path가 쓰는 것과 같은 key generator, 같은 half-open interval 규칙, 같은 active predicate를 써야 한다

즉 cancel도 `new_scope = ∅`인 reschedule이고, expiry cleanup도 `cancel(reason='expiry')`인 전이로 보는 편이 안전하다.

이 계약이 slot claim table까지 내려가면 `scope_delta`는 곧 `old_slots/new_slots` delta와 tombstone cleanup watermark로 구체화된다. 구현 세부는 [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md)에서 이어 본다.

## 왜 special-case가 deadlock과 drift를 다시 만든다

### 1. shorten이나 cancel을 "release-only fast path"로 빼면 안 된다

겉으로는 단순해 보인다.

- shorten: 줄어든 tail만 풀면 되지 않나
- cancel: old scope만 해제하면 되지 않나

하지만 이 fast path가 기존 `keep` 구간을 잠그지 않으면 아래 경로와 교차한다.

- 동시에 다른 reschedule이 같은 예약을 extend/move 하려는 경우
- 같은 resource/day에 새 booking이 들어와 release 직후 빈 자리를 선점하는 경우
- pool guard와 unit guard가 같이 있는 모델에서 한 surface만 먼저 풀리는 경우

결과는 둘 중 하나다.

- 중간 상태가 노출되어 drift가 난다
- 서로 다른 경로가 다른 순서로 day/slot을 잡아 deadlock이 난다

shorten, cancel, expiry cleanup은 "덜 하는 write"가 아니라 **`release` delta가 있는 전이**일 뿐이다.

### 2. expiry cleanup을 별도 SQL로 두면 label과 blocking truth가 갈라진다

`status='EXPIRED'`만 먼저 찍고:

- `released_at`
- guard counter decrement
- active row delete/history move
- ledger append

를 다른 worker로 미루면, `expired` 라벨은 있는데 실제로는 아직 blocker인 row가 남는다.

이 상태가 길어질수록:

- admission은 빈자리처럼 보는데 guard row는 안 비어 있고
- reschedule은 old scope를 release했다고 생각하는데 reconciliation은 active row로 계산하고
- admin override는 "이미 만료된 건"이라고 보고 직접 수정해 drift를 키운다

expiry cleanup은 별도 lifecycle이 아니라 **empty target으로 가는 canonical transition**이어야 한다.

### 3. admin override가 canonical generator를 우회하면 repair가 불가능해진다

운영 툴에서 자주 하는 실수:

- `UPDATE reservation SET room_id = ...`만 직접 친다
- guard row는 뒤늦게 수동 보정한다
- ledger/history는 이유 없이 비어 있다

이렇게 되면 나중에 drift가 났을 때 "이게 의도된 override인지, 버그인지" 구분이 안 된다.

override가 진짜 blocking truth를 바꾼다면:

- 같은 `old_scope/new_scope` 계산
- 같은 canonical lock order
- 같은 active predicate recheck
- 같은 mutation log / audit reason

을 반드시 타야 한다.

## canonical mutation protocol

아래 순서를 모든 extend, shorten, move, cancel, expiry cleanup, admin override에 공통으로 쓰는 편이 안전하다.

1. **mutation key를 먼저 선점한다**
   - `reservation_id + mutation_key`를 unique하게 잡는다
   - 같은 key에 다른 payload가 오면 reject하고, 같은 payload면 이전 결과를 재사용한다
2. **reservation-local fence를 잡는다**
   - `reservation` row `FOR UPDATE` 또는 `version` 기반 CAS
   - 같은 예약에 대한 동시 전이를 한 경로만 commit하게 만든다
3. **현재 committed state에서 `old_scope`를 계산한다**
   - stale client payload나 UI cache를 믿지 않는다
   - `released_at IS NULL` 또는 active relation row 존재 여부 같은 canonical truth에서 계산한다
4. **요청된 target에서 `new_scope`를 계산한다**
   - cancel / expiry cleanup이면 빈 집합
   - shorten이면 old의 strict subset
   - move면 old와 다른 resource/day/slot set
5. **`touched_scope = old ∪ new`를 canonical order로 잠근다**
   - 예: `(tenant_id, resource_kind, resource_id, stay_day, slot_start)`
   - 계층 guard가 있으면 항상 `pool -> unit` 순서
6. **잠금 아래에서 overlap / capacity / lifecycle을 재검사한다**
   - 같은 active predicate, 같은 blocker surface를 쓴다
   - `expires_at`은 후보 조건이지 blocker truth가 아니다
7. **`scope_delta`를 한 번만 반영한다**
   - `acquire = new - old`
   - `release = old - new`
   - `keep = old ∩ new`
   - booking row, guard counter, active blocker row, ledger/history를 같은 트랜잭션에서 갱신한다
8. **mutation 결과를 commit 후 저장한다**
   - 이후 retry는 guard counter를 다시 흔들지 않고 prior result를 돌려준다

핵심은 "무엇을 잠그느냐"보다 **모든 경로가 같은 함수로 `old_scope/new_scope/touched_scope`를 만든다**는 점이다.

## 경로별 안전한 flow

| 경로 | `new_scope` | `touched_scope` | 절대 빼먹으면 안 되는 것 |
|---|---|---|---|
| extend | 기존 예약 + 추가 구간 | 보통 `new_scope` 전체 | 새 tail만 더하는 것처럼 보여도 기존 active row와 같은 mutation fence 아래서 처리해야 한다 |
| shorten | 줄어든 예약 구간 | `old_scope` 전체 | release-only fast path로 빼지 말고, retain 구간을 포함한 전체 old scope를 잠가야 drift가 줄어든다 |
| move | 새 resource/day/slot 집합 | `old ∪ new` | old release 후 new acquire로 쪼개지 말고 union lock 후 한 번에 handoff해야 한다 |
| cancel | 빈 집합 | `old_scope` | `released_at`, counter decrement, active row 제거/history move를 같은 트랜잭션에 묶어야 한다 |
| expiry cleanup | 빈 집합 | `old_scope` | worker 전용 SQL을 두지 말고 cancel과 같은 transition engine을 reason만 바꿔 호출한다 |
| admin override | override target에 따라 다름 | override가 바꾸는 old/new 합집합 | direct SQL 금지, `override_ticket_id` 같은 audit key와 같은 delta 계산을 강제한다 |

### extend

extend는 가장 덜 위험해 보여도, 실제로는 "기존 scope를 이미 내가 갖고 있다"는 착각이 가장 많이 들어가는 경로다.

- 같은 예약에 대해 cancel/expiry가 동시에 올 수 있다
- 기존 scope와 새 tail 사이에 다른 booking이 끼어들 수 있다
- pool inventory와 unit assignment가 분리된 모델에서는 두 surface를 함께 봐야 한다

따라서 extend도 create와 같은 capacity recheck를 하고, `acquire`는 새 tail에만 적용하되 **잠금은 whole touched scope** 기준으로 잡는 편이 안전하다.

### shorten

shorten은 `new_scope ⊂ old_scope`라서 union이 `old_scope`와 같아 보인다.  
그래도 이 경로를 별도 release-only SQL로 분기하면 아래 문제가 생긴다.

- tail release 중간에 다른 move가 같은 예약의 retained scope를 잡아 버림
- old scope 일부만 본 cancel/expiry가 먼저 성공해 double release가 발생
- reconciliation은 old active row를 보고 있는데 counter만 먼저 줄어듦

shorten의 핵심은 "덜 점유한다"가 아니라 **release delta가 있는 full transition**이라는 점이다.

### move

move는 deadlock과 oversell이 가장 잘 드러나는 경로다.

- 날짜만 바꾸는 move
- 같은 날짜에 room만 바꾸는 move
- room type과 concrete room이 둘 다 바뀌는 move

세 경우 모두 안전한 원칙은 같다.

1. old/new를 같은 key generator로 펼친다
2. pool/day와 unit/day가 둘 다 있으면 항상 `pool -> unit`으로 잠근다
3. union lock 뒤에만 release/acquire를 계산한다
4. `keep` 구간은 다시 차감하지 않는다

특히 move를 `cancel + create` 두 API로 쪼개면 재고는 맞더라도 deadlock control과 idempotency가 경로마다 갈라진다.

### cancel

cancel을 진짜로 안전하게 만들려면 "한 번만 release된다"를 보장해야 한다.

필수 조건:

- cancel retry는 이전 결과를 재사용해야 한다
- `released_at` 또는 active row delete가 실제 blocking truth handoff가 되어야 한다
- counter decrement와 history/ledger append가 같은 트랜잭션에 묶여야 한다

즉 `status='CANCELED'`만 찍고 나중에 background worker가 guard를 줄이게 하면 cancel 자체가 drift의 출발점이 된다.

### expiry cleanup

expiry cleanup은 API cancel과 actor만 다르고, write semantics는 같아야 한다.

- worker batch
- claim-path finalization
- timeout callback

세 경로가 서로 다른 SQL을 쓰지 말고, **same transition engine + different reason**을 써야 한다.

권장 mutation key 예:

- `expiry:{reservation_id}:{scope_version}`
- `claim_finalize:{reservation_id}:{scope_version}`

이렇게 해야 worker retry나 `SKIP LOCKED` 재시도가 counter/ledger를 두 번 흔들지 않는다.

### admin override

admin override는 "운영자가 보니 지금 바로 고쳐야 한다"는 상황이지만, 그래서 더더욱 canonical contract를 타야 한다.

안전한 기준:

- metadata note만 바꾸면 guard를 건드리지 않는다
- blocking truth를 바꾸면 reschedule/cancel과 같은 transition engine을 탄다
- capacity를 의도적으로 깨는 override라면 `override_ticket_id`, `override_reason`, compensating task를 함께 남긴다

즉 override는 "규칙 바깥"이 아니라 **예외 사유가 붙은 같은 규칙 안의 전이**여야 한다.

## idempotency와 audit를 transition 단위로 묶어야 한다

예약 전이에서 멱등성은 request replay만 막는 용도가 아니다.  
`release` delta가 있는 경로의 double-apply를 막는 safety 장치다.

권장 원칙:

- mutation key는 예약 단위로 unique해야 한다
- 같은 key에는 request hash를 같이 저장해 payload mismatch를 reject한다
- 적용 결과를 `applied`, `conflict`, `already_finalized` 같이 기록한다
- ledger/history에는 `source_transition`과 `mutation_key`를 같이 남긴다

대표 키 공간 예시:

| producer | 권장 key |
|---|---|
| reschedule API | `client_request_id` 또는 서버 발급 mutation id |
| cancel API | `cancel_request_id` |
| expiry worker | `expiry:{reservation_id}:{scope_version}` |
| claim-path finalization | `claim_finalize:{reservation_id}:{scope_version}` |
| admin override | `override:{ticket_id}` |

이때 중요한 점은 **retry를 허용할지와 delta를 다시 적용할지는 별개**라는 것이다.  
retry는 allowed일 수 있지만, 적용 결과는 mutation log가 이미 소유하고 있어야 한다.

## 코드로 보기

```sql
CREATE TABLE reservation_transition (
  reservation_id BIGINT NOT NULL,
  mutation_key VARCHAR(100) NOT NULL,
  mutation_kind VARCHAR(32) NOT NULL,
  request_hash CHAR(64) NOT NULL,
  result_state VARCHAR(32) NOT NULL,
  applied_at TIMESTAMP NULL,
  PRIMARY KEY (reservation_id, mutation_key)
);
```

```text
canonical reservation transition
1. claim (reservation_id, mutation_key)
2. fence current reservation row (row lock or version CAS)
3. derive old_scope from committed active truth
4. derive new_scope from requested target
5. touched_scope = union(old_scope, new_scope)
6. lock touched_scope in canonical order
7. recheck overlap/capacity/lifecycle under the same active predicate
8. apply acquire/release/keep delta once
9. write booking state + blocker truth + guard delta + ledger/history + transition result in one transaction
```

```text
scope delta example
old_scope = { (room-101, 04-14), (room-101, 04-15), (room-101, 04-16) }
new_scope = { (room-203, 04-15), (room-203, 04-16), (room-203, 04-17) }

keep    = ∅
release = { (room-101, 04-14), (room-101, 04-15), (room-101, 04-16) }
acquire = { (room-203, 04-15), (room-203, 04-16), (room-203, 04-17) }

lock order:
  pool/day keys first if present
  then unit/day keys
  each surface sorted by canonical key
```

핵심은 SQL 문장보다, **모든 actor가 같은 `scope_delta`를 계산하고 같은 mutation log에 귀속되는가**다.

## 자주 하는 anti-pattern

- reschedule을 `cancel -> create` 두 요청으로 분리한다
- shorten/cancel은 "어차피 release만 하니까" guard ordering을 생략한다
- expiry worker가 `status='EXPIRED'`만 먼저 찍고 release는 나중에 한다
- admin override가 다른 day bucketing이나 다른 active predicate를 쓴다
- retry가 성공/실패만 보고 이전 delta 적용 여부를 모른 채 다시 decrement한다

이 다섯 가지 중 하나만 있어도, create path가 아무리 정교해도 transition path에서 deadlock과 drift가 다시 들어온다.

## 체크리스트

- 같은 예약의 extend/shorten/move/cancel/expiry/admin override가 reservation-local fence를 공유하는가
- 모든 전이가 같은 key generator로 `old_scope/new_scope/touched_scope`를 계산하는가
- cancel과 expiry cleanup이 별도 fast path가 아니라 empty target transition으로 구현돼 있는가
- `released_at` 또는 active row delete가 실제 blocking truth handoff와 같은 트랜잭션에서 일어나는가
- guard counter, blocker row, ledger/history, mutation log가 같은 delta를 보게 되는가
- admin override도 `override_ticket_id`와 같은 audit key 아래에서 같은 contract를 타는가

## 한 줄 정리

extend, shorten, move, cancel, expiry cleanup, admin override를 각각 따로 구현하지 말고, **`old_scope/new_scope` union lock + reservation-local idempotent fence + one-shot scope delta apply**라는 하나의 transition protocol로 묶어야 deadlock과 drift를 동시에 줄일 수 있다.
