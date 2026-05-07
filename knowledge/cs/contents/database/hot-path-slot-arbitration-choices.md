---
schema_version: 3
title: Hot-Path Slot Arbitration Choices
concept_id: database/hot-path-slot-arbitration-choices
canonical: true
category: database
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- hot-path-slot-arbitration
- slot-unique-vs-guard-row
- hybrid-fencing-booking
aliases:
- hot path slot arbitration
- booking arbitration choice
- slot unique key
- unique slot claim
- resource-day guard row
- room day guard
- duplicate slot insert storm
- hybrid fencing booking
- slot unique vs guard row
- booking flash crowd locking
symptoms:
- high-contention booking hot path에서 slot unique key, resource-day guard row, hybrid fencing 중 어떤 queue shape를 골라야 할지 모르겠어
- duplicate key로 빨리 탈락시키는 비용과 guard row lock wait 비용을 비교해야 해
- 같은 booking retry, reschedule, expiry cleanup 경합까지 slot truth 하나로 닫으려 하고 있어
intents:
- comparison
- design
- troubleshooting
prerequisites:
- database/guard-row-scope-design-multi-day-bookings
- database/unique-vs-slot-row-vs-guard-row-quick-chooser
next_docs:
- database/slot-delta-reschedule-semantics
- database/hot-row-contention-counter-sharding
- database/shared-pool-guard-design-room-type-inventory
- database/upsert-contention-unique-index-locking
linked_paths:
- contents/database/slot-delta-reschedule-semantics.md
- contents/database/guard-row-scope-design-multi-day-bookings.md
- contents/database/reservation-reschedule-cancellation-transition-patterns.md
- contents/database/ordered-guard-row-upsert-patterns-postgresql-mysql.md
- contents/database/hot-row-contention-counter-sharding.md
- contents/database/shared-pool-guard-design-room-type-inventory.md
- contents/database/engine-fallbacks-overlap-enforcement.md
- contents/database/upsert-contention-unique-index-locking.md
- contents/database/guard-row-hot-row-symptoms-primer.md
confusable_with:
- database/guard-row-scope-design-multi-day-bookings
- database/hot-row-contention-counter-sharding
- database/upsert-contention-unique-index-locking
forbidden_neighbors: []
expected_queries:
- booking hot path에서 slot unique key와 resource-day guard row는 대기열 위치가 어떻게 달라?
- duplicate slot insert storm을 긴 lock wait보다 낫다고 볼 수 있는 상황은 언제야?
- hybrid fencing booking은 slot claim truth와 fence gate 역할을 어떻게 나눠?
- reschedule, expiry cleanup, admin override가 섞이는 예약 경합에서 slot unique key만으로 부족한 이유는 뭐야?
- high contention booking에서 패배 요청 비용을 duplicate key, lock wait, short fence retry로 비교해줘
contextual_chunk_prefix: |
  이 문서는 high-contention booking hot path에서 slot unique key, resource-day guard row, hybrid fencing 중 어디에 대기열과 패배 비용을 둘지 고르는 advanced chooser다.
  hot path slot arbitration, slot unique key, resource-day guard row, hybrid fencing booking 같은 자연어 설계 질문이 본 문서에 매핑된다.
---
# Hot-Path Slot Arbitration Choices

> 한 줄 요약: high-contention booking hot path에서는 `slot unique key`, `resource-day guard row`, `hybrid fencing`이 모두 정합성은 지킬 수 있지만, 실제 차이는 어디에 대기열을 만들고 패배 요청이 어떤 비용을 치르게 할지를 어떻게 고르느냐에 있다.

**난이도: 🔴 Advanced**

관련 문서:

- [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Reservation Reschedule and Cancellation Transition Patterns](./reservation-reschedule-cancellation-transition-patterns.md)
- [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md)
- [Guard-Row Hot-Row Contention Mitigation](./hot-row-contention-counter-sharding.md)
- [Shared-Pool Guard Design for Room-Type Inventory](./shared-pool-guard-design-room-type-inventory.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)

retrieval-anchor-keywords: hot path slot arbitration, booking arbitration choice, slot unique key, unique slot claim, resource-day guard row, room day guard, booking hot key contention, slotization contention, duplicate slot insert storm, booking flash crowd locking, hybrid fencing booking, reservation-local fence, mutation fence booking, ingress fence slot claim, coarse guard fine slot truth, slot claim duplicate retry, room-day mutex, booking contention topology, slot unique vs guard row, hot path booking locking

## 핵심 개념

예약 경합에서 중요한 것은 "무엇이 더 안전한가"가 아니다.  
셋 다 제대로 구현하면 정합성은 지킬 수 있다.

진짜 차이는 세 가지다.

1. 어디에서 경쟁 요청을 줄 세울 것인가
2. 패배한 요청이 `lock wait`를 겪을지, `duplicate key`로 빨리 탈락할지, 짧은 fence 뒤에서 재시도할지
3. reschedule, expiry cleanup, admin override 같은 **전이 경로**를 같은 계약으로 묶기 쉬운가

같은 "double booking 방지"라도 queue shape는 완전히 다르다.

| 선택지 | occupancy의 최종 truth | 주된 대기 surface | 패배 요청의 전형적 비용 | 가장 강한 점 | 가장 큰 함정 |
|---|---|---|---|---|---|
| slot unique key | `resource_id + slot_start` active claim | slot PK/UNIQUE index | duplicate key, insert rollback, index latch 경쟁 | discrete slot truth가 가장 직접적이다 | row 수와 duplicate storm가 빠르게 커진다 |
| resource-day guard row | `(resource_id, stay_day)` guard + 후속 recheck | guard row lock queue | row lock wait, multi-day deadlock retry | write path를 한 곳으로 모으기 쉽다 | day 전체가 전역 mutex처럼 뜨거워질 수 있다 |
| hybrid fencing | slot claim이 최종 truth, fence는 ingress/transition gate | booking-local fence + day/stripe fence + 최종 slot unique | 짧은 fence wait + duplicate key 또는 business reject | hot storm와 stale retry를 같이 줄일 수 있다 | 두 surface의 역할을 섞으면 설명력이 무너진다 |

## 먼저 분리할 세 종류의 경쟁

세 선택지를 비교하기 전에, 어떤 경쟁을 푸는지 먼저 나눠야 한다.

### 1. 서로 다른 booking끼리 같은 inventory를 두고 싸우는 경쟁

- 인기 오픈 시간에 여러 사용자가 같은 회의실/객실/좌석을 노린다
- 핵심은 누가 먼저 점유 truth를 commit하느냐다

### 2. 같은 booking에 대한 retry / reschedule / cancel / expiry가 엇갈리는 경쟁

- 결제 callback 재시도
- 모바일 재요청
- expiry worker와 confirm path의 교차
- admin override와 일반 사용자 reschedule의 교차

이 문제는 slot unique key만으로는 다 안 닫힌다.  
같은 `booking_id`가 old/new slot 집합을 두 번 흔들 수 있기 때문이다.

### 3. admission hot path와 cleanup / replay / backfill이 섞이는 경쟁

- active truth를 누가 보나
- tombstone이나 history를 blocker로 잘못 읽지 않나
- migration catch-up이 release evidence를 놓치지 않나

이 구분 없이 "slot table이면 끝" 또는 "guard row 하나면 끝"으로 가면, 실제 병목은 다른 곳에서 다시 생긴다.

## 선택지 1. Slot Unique Key

slot unique key의 핵심은 간단하다.

- 시간 구간을 canonical slot으로 펼친다
- active slot claim row를 만든다
- `resource_id + slot_start` unique key가 최종 arbitration을 맡는다

```sql
CREATE TABLE booking_slot_claim_active (
  tenant_id BIGINT NOT NULL,
  resource_id BIGINT NOT NULL,
  slot_start TIMESTAMPTZ NOT NULL,
  booking_id BIGINT NOT NULL,
  claim_version BIGINT NOT NULL,
  source_mutation_key VARCHAR(100) NOT NULL,
  PRIMARY KEY (tenant_id, resource_id, slot_start),
  UNIQUE (booking_id, slot_start)
);
```

이 패턴이 high contention에서 강한 이유:

- conflict surface가 slot boundary와 정확히 일치한다
- winner는 실제 점유 row를 바로 남긴다
- loser는 긴 lock wait보다 `duplicate key`로 빠르게 탈락하기 쉽다
- PostgreSQL/MySQL 모두에서 설명이 비교적 portable하다

하지만 hot path 비용도 분명하다.

### 언제 잘 맞나

- 15분, 30분처럼 discrete slot이 이미 business truth다
- 요청 하나가 만지는 slot 수가 작고 bounded 되어 있다
- same-slot conflict를 fail-fast로 떨어뜨리는 편이 낫다
- audit/replay가 slot claim relation 중심으로 설계되어 있다

### high contention에서 보이는 증상

- lock wait보다 duplicate key / unique violation이 많이 보인다
- 실패 요청도 index insert 시도와 rollback 비용을 낸다
- 같은 slot page/index prefix에 latch 경쟁이 생긴다
- 긴 예약이나 multi-slot move는 한 요청의 write amplification이 커진다

즉 slot unique key는 "대기를 없애는" 방식이 아니라,  
**대기를 짧은 duplicate arbitration으로 바꾸는 방식**에 가깝다.

### 가장 자주 터지는 함정

#### 1. multi-slot booking을 단일 slot과 같은 비용으로 오해한다

30분 예약 1건과 4시간 예약 1건은 같은 booking 수라도 write cost가 다르다.

- 1 slot booking: unique insert 1번
- 8 slot booking: unique insert 8번 + reschedule 시 old/new union handling

경합이 심한데 요청당 slot fan-out까지 크면 slot unique path는 금방 CPU/redo/index write 압박을 받는다.

#### 2. reschedule을 delete 후 insert로 쪼갠다

slot unique key를 쓴다고 해서 reschedule이 자동으로 안전해지지 않는다.

- old slot delete 후 new slot insert를 두 단계로 나누면 gap이 생긴다
- `keep` slot을 안 잠그면 concurrent cancel/retry와 교차한다
- 같은 booking retry가 old/new delta를 두 번 적용할 수 있다

그래서 slot unique key를 택해도 [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md)의 `old_slots ∪ new_slots` union lock과 mutation fence는 여전히 필요하다.

#### 3. duplicate storm를 "정상 실패니까 싸다"고 착각한다

duplicate key는 business conflict일 수 있지만 공짜는 아니다.

- index probe
- insert intent
- rollback / exception mapping
- 애플리케이션 retry

인기 slot 하나에 수천 요청이 몰리면, 패배 요청이 빨리 끝나더라도 시스템은 꽤 많은 write-path 일을 한다.

## 선택지 2. Resource-Day Guard Row

resource-day guard row는 occupancy truth를 day-level arbitration surface로 먼저 압축한다.

- `(resource_id, stay_day)` 같은 대표 row를 잠근다
- 그 잠금 아래에서 interval/slot overlap을 재검사한다
- booking row, counter, ledger, active row를 한 트랜잭션에서 바꾼다

```sql
CREATE TABLE resource_day_guard (
  tenant_id BIGINT NOT NULL,
  resource_id BIGINT NOT NULL,
  stay_day DATE NOT NULL,
  version BIGINT NOT NULL,
  PRIMARY KEY (tenant_id, resource_id, stay_day)
);
```

```sql
SELECT tenant_id, resource_id, stay_day
FROM resource_day_guard
WHERE tenant_id = :tenant_id
  AND resource_id = :resource_id
  AND stay_day IN (:days)
FOR UPDATE;
```

이 패턴이 high contention에서 강한 이유:

- conflicting writer들이 같은 row queue로 모여 설명이 쉽다
- 슬롯 여러 개를 만지는 booking도 guard lock은 day 수만큼만 잡으면 된다
- 중간 단계에서 duplicate insert 폭풍을 덜 만든다
- reschedule/cancel/expiry/admin override를 같은 transition engine으로 모으기 쉽다

### 언제 잘 맞나

- 숙박처럼 `day`가 자연스러운 business resolution이다
- 예약 길이가 2~7일 정도로 bounded 되어 있다
- sub-day slot row 수를 hot path에 직접 늘리고 싶지 않다
- conflict loser를 fail-fast보다 queued serialization로 다루는 편이 낫다

### high contention에서 보이는 증상

- duplicate key보다 row lock wait이 먼저 튄다
- 같은 `resource_id + stay_day`가 전역 mutex처럼 보인다
- day-level hot key 하나가 p99를 끌어올린다
- multi-day booking은 lock fan-out이 날짜 수만큼 늘어난다

즉 resource-day guard row는  
**패배 요청의 비용을 duplicate work 대신 기다림으로 바꾸는 방식**에 가깝다.

### 가장 자주 터지는 함정

#### 1. day guard를 occupancy truth 자체로 오해한다

day guard는 보통 arbitration surface이지, 실제 점유 detail 전체가 아니다.

- sub-day overlap이 있으면 후속 recheck가 필요하다
- later unit assignment가 있으면 `room_id + day` 2차 invariant가 또 필요하다
- active predicate drift가 있으면 guard counter와 detail row가 쉽게 벌어진다

그래서 guard row만 있고 active detail / ledger가 약하면 운영 복구가 힘들어진다.

#### 2. hot row 완화 없이 day granularity만 믿는다

인기 resource 하나에 하루 요청이 집중되면:

- 같은 day guard row에 모든 writer가 몰리고
- queue는 단순해지지만 throughput이 flat해지고
- retry보다 lock timeout이 먼저 운영 문제로 올라온다

이 경우는 [Guard-Row Hot-Row Contention Mitigation](./hot-row-contention-counter-sharding.md)의 stripe/budget/ledger 판단이 필요할 수 있다.

#### 3. multi-day reschedule에서 canonical order를 느슨하게 둔다

- 기존 숙박일과 새 숙박일의 합집합을 잠가야 한다
- `old_scope` 먼저, `new_scope` 나중 같은 경로 분리는 위험하다
- `pool -> unit -> slot` 같은 계층 guard가 있으면 방향을 고정해야 한다

즉 resource-day guard row는 coarse해 보여도 deadlock 설계가 사라지지 않는다.

## 선택지 3. Hybrid Fencing

hybrid fencing은 "guard냐 slot이냐"의 중간이 아니라,  
**coarse ingress/transition gate와 fine-grained slot truth를 분리하는 패턴**이다.

권장 해석은 이렇다.

- 최종 occupancy truth: active slot claim
- hot-path ingress gate: resource-day 또는 stripe fence
- same-booking stale retry 방지: reservation-local mutation fence

즉 fence row는 "지금 누가 이 영역의 전이를 시도할 수 있나"를 정하고,  
slot unique key는 "무엇이 실제로 점유 중인가"를 정한다.

```sql
CREATE TABLE booking_mutation_fence (
  booking_id BIGINT NOT NULL,
  mutation_key VARCHAR(100) NOT NULL,
  applied_version BIGINT NOT NULL,
  PRIMARY KEY (booking_id, mutation_key)
);

CREATE TABLE resource_day_fence (
  tenant_id BIGINT NOT NULL,
  resource_id BIGINT NOT NULL,
  stay_day DATE NOT NULL,
  fence_version BIGINT NOT NULL,
  PRIMARY KEY (tenant_id, resource_id, stay_day)
);
```

권장 프로토콜:

1. `booking_id + mutation_key`를 먼저 선점한다
2. booking row 또는 aggregate를 fenced lock으로 잡는다
3. 필요한 `resource_day_fence`를 canonical order로 잠근다
4. 그 잠금 아래에서 `old_slots/new_slots`를 계산한다
5. active slot claim unique insert/delete/tombstone을 한 번만 적용한다
6. duplicate key면 business reject, stale mutation이면 prior result 재사용 또는 reject 한다

### 왜 high contention에서 유리할 수 있나

slot unique key 단독 경로는 모든 contender가 곧바로 fine-grained index에 몰린다.  
resource-day guard 단독 경로는 day 전체가 긴 row-lock queue가 된다.

hybrid fencing은 그 사이를 노린다.

- booking-local retry/cancel/expiry를 먼저 잘라 stale write를 줄인다
- resource-day ingress를 짧게 serialize해 thundering herd를 누그러뜨린다
- 최종 occupancy는 slot unique key가 결정해 exactness를 잃지 않는다

즉 hot day에 1000명이 몰려도 "1000명이 동시에 slot insert 폭풍"으로 가지 않고,  
짧은 fence 통과 후 실제 claim 시도로 들어가게 만들 수 있다.

### 언제 잘 맞나

- slot truth는 필요하지만, hot day/slot에 retry 폭풍도 같이 있다
- 결제, hold, expiry cleanup, admin override가 같은 예약을 자주 건드린다
- same-booking stale mutation이 duplicate storm만큼 위험하다
- 팀이 `fence != occupancy truth`라는 역할 분리를 운영할 수 있다

### 가장 자주 터지는 함정

#### 1. fence row를 availability truth로 읽기 시작한다

이 순간 hybrid는 망가진다.

- fence row는 "누가 지금 시도 중인가" 또는 "같은 전이를 두 번 적용하지 말자"를 위한 장치다
- 실제 빈자리 여부는 slot claim active relation이 말해야 한다
- fence backlog나 stale fence를 blocker truth로 읽으면 false full이 생긴다

즉 hybrid에서는 **truth와 authority를 다른 table에 둔 이유**를 끝까지 지켜야 한다.

#### 2. fence만 두고 final unique truth를 느슨하게 둔다

fence가 있다고 해서 exactness가 생기지는 않는다.

- worker crash 후 재진입
- partial retry
- cross-day move
- multi-resource booking

이 상황에서 최종 active claim surface가 없다면 fence는 단지 "시도 순서"만 정할 뿐이다.  
그래서 hybrid는 fence-only 패턴이 아니라 **fence + exact claim truth** 패턴이어야 한다.

#### 3. fence 획득 시간을 길게 만든다

외부 결제 호출, 네트워크 RPC, 긴 policy 계산을 fence 구간 안에 넣으면:

- 결국 resource-day guard row와 비슷한 긴 queue가 된다
- hybrid의 장점인 짧은 ingress serialization이 사라진다

따라서 hybrid는 fence를 잡은 뒤 **짧게 판단하고 짧게 claim**하는 경로일 때만 이득이 크다.

## 세 선택지를 어떻게 빨리 고를까

| 질문 | slot unique key | resource-day guard row | hybrid fencing |
|---|---|---|---|
| business truth가 discrete slot인가 | 가장 잘 맞는다 | 재모델링이 필요할 수 있다 | slot truth 유지 가능 |
| 패배 요청을 빠르게 탈락시키고 싶은가 | 강하다 | 약하다 | 중간 |
| hot key 하나에 긴 queue를 허용할 수 있는가 | 상대적으로 덜 필요하다 | 필요하다 | 짧은 queue만 허용 |
| booking retry / expiry / admin 교차가 잦은가 | 추가 mutation fence가 필수다 | transition engine으로 다루기 쉽다 | 가장 잘 맞는다 |
| 요청당 slot fan-out이 큰가 | 불리하다 | 유리하다 | 중간 |
| 운영 복잡도를 낮추고 싶은가 | 중간 | 가장 단순하다 | 가장 복잡하다 |

빠른 기준으로 요약하면:

- slot이 곧 truth이고 요청이 짧다: `slot unique key`
- day가 자연 단위이고 serialize cost를 감수할 수 있다: `resource-day guard row`
- slot truth는 유지해야 하지만 retry storm와 stale mutation까지 같이 다뤄야 한다: `hybrid fencing`

## 이런 증상이 보이면 선택을 다시 본다

### duplicate key 비율이 높고 lock wait은 낮다

가능한 해석:

- slot unique key path가 hot slot에 몰려 있다
- loser가 fail-fast 하긴 하지만 시스템은 duplicate work를 많이 한다

다음 선택지:

- slot bucket을 더 coarse하게 재설계
- hot day/stripe ingress fence를 얹는 hybrid 검토
- retry budget과 backoff를 강화

### lock wait p99가 높고 duplicate conflict는 거의 없다

가능한 해석:

- resource-day guard row가 너무 coarse하다
- day row 하나가 사실상 global mutex처럼 쓰이고 있다

다음 선택지:

- finer slot truth로 내려가기
- day guard stripe/budget 재구성
- multi-day fan-out 상한 재검토

### stale retry, expiry cleanup, admin override가 occupancy를 흔든다

가능한 해석:

- 문제의 핵심은 inventory 경쟁보다 mutation ordering이다
- slot unique vs guard row 이전에 reservation-local fence가 빠져 있다

다음 선택지:

- mutation key dedupe
- booking-local fence
- 필요하면 hybrid fencing으로 ingress gate까지 추가

## 실전 시나리오

### 시나리오 1. 30분 회의실 예약 오픈

특징:

- discrete slot이 business truth다
- 한 번 예약이 보통 1~2 slot이다
- 패배 요청을 빨리 탈락시키는 편이 낫다

권장:

- `slot unique key`

이 경우 day guard를 앞에 두면 같은 날 다른 시간대 예약까지 같이 줄 세울 수 있다.

### 시나리오 2. 2박~5박 숙박 예약

특징:

- nightly inventory가 핵심이다
- 한 예약이 여러 day를 만진다
- sub-day slot row fan-out은 불필요하게 크다

권장:

- `resource-day guard row`

이 경우 slot unique key로 nightly inventory를 직접 표현하면 row 수와 write amplification이 과해질 수 있다.

### 시나리오 3. 인기 예약 오픈 + 결제 retry + expiry cleanup 동시 폭주

특징:

- exact slot truth는 필요하다
- 같은 `booking_id`에 대한 retry와 finalize 경쟁도 심하다
- hot day/slot에 contender가 매우 많다

권장:

- `hybrid fencing`

이 경우 pure slot unique path만 두면 duplicate storm가 커지고, pure day guard path만 두면 queue가 지나치게 길어진다.

## 결정 체크리스트

- slot이 실제 business truth인지, 아니면 admission을 위한 구현 디테일인지 먼저 구분했는가
- 패배 요청의 비용을 `duplicate work`로 낼지 `lock wait`로 낼지 선택했는가
- same-booking retry/cancel/expiry/admin override에 대한 mutation fence가 있는가
- reschedule에서 `old_scope/new_scope` union lock 또는 union fence를 일관되게 쓰는가
- cleanup/history/tombstone을 blocker truth로 읽지 않게 active relation을 분리했는가
- 인기 key 하나가 뜨거워질 때 어떤 metric이 먼저 튀어야 정상인지 합의했는가

## 꼬리질문

> Q: slot unique key를 쓰면 guard row는 전혀 필요 없나요?
> 의도: fine-grained exact truth와 transition fencing을 구분하는지 확인
> 핵심: exact slot truth는 얻지만, same-booking mutation ordering이나 hot ingress control은 별도 fence가 여전히 필요할 수 있다

> Q: resource-day guard row가 더 안전한가요?
> 의도: 정합성과 queue shape를 분리해서 생각하는지 확인
> 핵심: 안전성보다 arbitration surface가 더 coarse할 뿐이다. high contention에서 대기열과 p99가 더 커질 수 있다

> Q: hybrid fencing은 guard와 slot을 둘 다 쓰니 항상 더 좋은가요?
> 의도: 복합 패턴의 운영 비용을 이해하는지 확인
> 핵심: 아니다. `fence != occupancy truth` 역할 분리를 못 지키면 complexity만 늘고 false blocker까지 생긴다

## 한 줄 정리

high-contention booking에서 `slot unique key`, `resource-day guard row`, `hybrid fencing`의 차이는 정합성 자체보다도, **어디에 줄을 세우고 누가 어떤 비용으로 탈락하며 stale mutation을 어떤 층에서 자를지**를 어떻게 설계하느냐에 있다.
