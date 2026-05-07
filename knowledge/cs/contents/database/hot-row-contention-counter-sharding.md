---
schema_version: 3
title: Guard-Row Hot-Row Contention Mitigation
concept_id: database/hot-row-contention-counter-sharding
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- guard-row-hot-row-mitigation
- striped-guard-row-counter-sharding
- hot-aggregate-admission-surface
aliases:
- hot row contention
- guard row hotspot
- striped guard rows
- guard row sharding
- counter sharding
- capacity hotspot mitigation
- quota hotspot
- reservation ledger fallback
- sharded guard counter
- hot aggregate row
symptoms:
- capacity guard row 하나가 전역 admission mutex가 되어 lock timeout과 p99가 치솟고 있어
- hard invariant를 유지하면서 single guard row 경합을 striped guard row나 counter shard로 분산해야 해
- 쓰기 경합을 줄이면 읽기 fan-in, shard rebalance, summary drift repair 비용이 생기는 tradeoff를 판단해야 해
intents:
- troubleshooting
- design
prerequisites:
- database/guard-row-hot-row-symptoms-primer
- database/guard-row-vs-serializable-vs-reconciliation-set-invariants
next_docs:
- database/striped-guard-row-budgeting
- database/hot-path-slot-arbitration-choices
- database/shared-pool-guard-design-room-type-inventory
- database/summary-drift-detection-bounded-rebuild
linked_paths:
- contents/database/striped-guard-row-budgeting-primer.md
- contents/database/hot-path-slot-arbitration-choices.md
- contents/database/guard-row-vs-serializable-vs-reconciliation-set-invariants.md
- contents/database/guard-row-scope-design-multi-day-bookings.md
- contents/database/shared-pool-guard-design-room-type-inventory.md
- contents/database/range-invariant-enforcement-write-skew-phantom.md
- contents/database/upsert-contention-unique-index-locking.md
- contents/database/summary-drift-detection-bounded-rebuild.md
- contents/database/lock-wait-deadlock-latch-triage-playbook.md
- contents/database/guard-row-hot-row-symptoms-primer.md
confusable_with:
- database/guard-row-hot-row-symptoms-primer
- database/striped-guard-row-budgeting
- database/summary-drift-detection-bounded-rebuild
forbidden_neighbors: []
expected_queries:
- guard row hotspot을 striped guard row, counter sharding, ledger projection 중 무엇으로 완화해야 해?
- capacity guard row가 hot aggregate row가 되면 hard invariant를 유지하면서 경합을 어떻게 분산해?
- counter sharding은 write contention을 줄이지만 read fan-in과 shard rebalance 비용이 왜 생겨?
- guard row sharding을 하기 전에 같은 key wait metrics로 hotspot을 어떻게 확인해?
- ledger projection은 admission control과 audit/replay/repair에서 어떤 장단점이 있어?
contextual_chunk_prefix: |
  이 문서는 capacity/quota guard row가 hot aggregate mutex가 될 때 striped guard row, counter sharding, ledger projection으로 arbitration surface를 재구성하는 advanced playbook이다.
  hot row contention, guard row hotspot, striped guard rows, counter sharding 같은 자연어 증상 질문이 본 문서에 매핑된다.
---
# Guard-Row Hot-Row Contention Mitigation

> 한 줄 요약: capacity나 quota를 지키는 guard row가 너무 뜨거워지면 락을 없애는 게 아니라 arbitration surface를 striped guard row, counter shard, ledger projection으로 재구성해야 한다.

**난이도: 🔴 Advanced**

관련 문서:

- [Striped Guard Row Budgeting Primer](./striped-guard-row-budgeting-primer.md)
- [Hot-Path Slot Arbitration Choices](./hot-path-slot-arbitration-choices.md)
- [Guard Row vs Serializable Retry vs Reconciliation for Set Invariants](./guard-row-vs-serializable-vs-reconciliation-set-invariants.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Shared-Pool Guard Design for Room-Type Inventory](./shared-pool-guard-design-room-type-inventory.md)
- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)
- [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)
- [Summary Drift Detection, Invalidation, and Bounded Rebuild](./summary-drift-detection-bounded-rebuild.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [Database + System Design 브리지 맵](../../rag/cross-domain-bridge-map.md#database--system-design)

retrieval-anchor-keywords: hot row contention, guard row hotspot, striped guard rows, guard row sharding, counter sharding, capacity hotspot mitigation, quota hotspot, reservation ledger fallback, append-only ledger, sharded guard counter, hot aggregate row, striped admission control, bucket rebalance, hot row 뭐예요, 처음 배우는데 같은 key만 기다려요

## 핵심 개념

count/sum invariant를 guard row 하나로 내리면 모델은 단순하다.

- `campaign_guard(campaign_id, reserved_qty, capacity)`
- `room_type_day_guard(room_type_id, stay_day, held_qty, limit_qty)`
- `tenant_quota_guard(tenant_id, active_sessions, max_sessions)`

하지만 트래픽이 커지면 이 row는 source of truth이기 전에 **전역 admission mutex**가 된다.

- 모든 요청이 같은 row lock 대기열에 선다
- `SELECT ... FOR UPDATE`든 조건부 `UPDATE`든 결국 같은 row를 직렬화한다
- 락 timeout, deadlock retry, p99 급등이 정합성 오류보다 먼저 보인다

핵심은 "guard row를 버릴까"가 아니라 **정확한 규칙은 유지한 채 어느 물리 surface에 경쟁을 분산할까**를 정하는 일이다.

## 먼저 판단할 질문

### 1. 이 경로는 즉시 승인/거절이 꼭 필요한가

즉시 oversell 방지가 필요하면 hot path에 여전히 동기식 arbitration surface가 있어야 한다.

- 공연 좌석, 쿠폰 수량, 동시 세션 제한처럼 초과 허용이 안 된다
- 그러면 striped guard row나 tokenized unit claim처럼 **동기식 승인 gate**가 필요하다
- pure async 집계나 pure ledger 합산만으로는 부족하다

반대로 잠깐의 drift를 사후 정산할 수 있으면 counter shard나 ledger 중심 설계로 더 쉽게 넘어갈 수 있다.

### 2. capacity를 안전하게 나눌 차원이 있는가

guard row hotspot을 분산하려면 논리 aggregate를 물리 bucket으로 쪼갤 근거가 필요하다.

- `campaign_id + bucket_id`
- `room_type_id + stay_day + bucket_id`
- `tenant_id + quota_bucket`

여기서 중요한 것은 "샤드를 많이 만든다"가 아니라 **요청이 적은 수의 bucket만 만지도록** 만드는 것이다.

### 3. 읽기 경로가 fan-in 비용을 감당할 수 있는가

카운터를 분산하면 쓰기 경합은 줄지만 읽기는 합산이 필요하다.

- 읽기가 적고 쓰기가 훨씬 많으면 counter sharding이 유리하다
- 읽기도 매우 뜨겁다면 materialized summary나 cache가 필요하다
- write path마다 모든 shard를 다시 합산하면 이득이 거의 사라진다

### 4. audit, replay, repair가 중요한가

수동 수정, 만료 cleanup, 재처리, 운영 복구가 잦다면 append-only ledger가 source of truth로 더 적합할 수 있다.

- 누가 언제 용량을 점유/반납했는지 남는다
- summary drift를 재계산할 수 있다
- shard 수 변경이나 rebalancing 시 근거 데이터가 남는다

## 패턴을 계층적으로 보면

| 패턴 | write path에서 주로 만지는 것 | 장점 | 비용 / 함정 | 잘 맞는 경우 |
|---|---|---|---|---|
| 단일 guard row | 대표 row 1개 | 구현과 설명이 가장 단순하다 | hot aggregate가 곧 전역 mutex가 된다 | 낮은 TPS, 작은 aggregate |
| striped guard row | 대표 row N개 중 1개 또는 적은 수 | 동기식 거절을 유지한 채 경합을 분산한다 | bucket budget, rebalance, stripe 선택이 필요하다 | exact admission이 필요한 hot capacity path |
| counter sharding | counter shard 1개 + 읽기 합산 | increment/update fan-out을 크게 줄인다 | read fan-in, skew, shard resize가 어렵다 | 쓰기 폭주, 읽기 fan-in 허용 |
| ledger + projection | append-only ledger + summary/materialization | audit/replay/repair가 강하고 write path가 append 중심이 된다 | pure ledger만으로는 hard invariant admission을 바로 못 닫는다 | 복구성, 추적성, 재계산이 중요한 경로 |

## 1. 단일 guard row가 핫스팟이 되는 순간

아래 패턴은 가장 흔한 시작점이다.

```sql
UPDATE campaign_guard
SET reserved_qty = reserved_qty + :qty,
    version = version + 1
WHERE campaign_id = :campaign_id
  AND reserved_qty + :qty <= capacity
  AND version = :version;
```

정합성은 좋다. 문제는 경합이다.

- 같은 `campaign_id`에 몰린 요청이 모두 같은 row를 두드린다
- 실패해도 규칙 위반이 아니라 lock wait로 오래 붙잡힌다
- reschedule, cancel, expiry cleanup까지 같은 row를 만지면 더 뜨거워진다

즉 이 단계에서는 "row 하나로 set invariant를 잘 모델링했다"가 곧 "서비스 전체가 row 하나를 기다린다"로 뒤집힐 수 있다.

## 2. striped guard row: admission surface를 쪼개기

아직 "정말 같은 guard key가 반복해서 줄을 세우는 상황인가?"가 먼저 헷갈린다면 striping 설계로 내려가기 전에 [Guard Row Hot-Row Symptoms Primer](./guard-row-hot-row-symptoms-primer.md)에서 증상부터 확인하는 편이 안전하다.

striped guard row의 핵심은 **storage를 나누는 것보다 승인 대기열을 나누는 것**이다.

```sql
CREATE TABLE campaign_guard_bucket (
  campaign_id BIGINT NOT NULL,
  bucket_id INT NOT NULL,
  budget_qty INT NOT NULL,
  reserved_qty INT NOT NULL,
  version BIGINT NOT NULL,
  PRIMARY KEY (campaign_id, bucket_id)
);
```

```sql
UPDATE campaign_guard_bucket
SET reserved_qty = reserved_qty + :qty,
    version = version + 1
WHERE campaign_id = :campaign_id
  AND bucket_id = :bucket_id
  AND reserved_qty + :qty <= budget_qty
  AND version = :version;
```

이 패턴에서 중요한 것은 세 가지다.

### 1. bucket 선택은 stable해야 한다

같은 reservation/claim의 acquire와 release가 같은 bucket으로 돌아와야 한다.

- `bucket_id = crc32(user_id) % 16`
- `bucket_id = crc32(reservation_id) % 16`
- `bucket_id = stay_day_slot % 16`

release나 cancel이 다른 bucket으로 가면 summary drift가 아니라 즉시 corruption이 된다.
그래서 detail row나 ledger에 `bucket_id`를 함께 저장하는 편이 안전하다.

이 세 규칙을 beginner 관점에서 짧게 먼저 잡고 싶다면 [Striped Guard Row Budgeting Primer](./striped-guard-row-budgeting-primer.md)를 먼저 읽는 편이 좋다.

## 2-1. bucket-local budget으로 exact admission 유지

`SUM(reserved_qty)`를 매번 다시 세면서 bucket 하나만 update하면 bucket 수만 늘어난 단일 guard row일 뿐이다.

exact invariant를 유지하려면:

- 정적 분배: 총 capacity 100을 bucket 10개에 `10`씩 나눈다
- 동적 top-up: 중앙에서 낮은 빈도로 budget을 재배분한다
- 자연 분할: tenant, slot, room block처럼 애초에 business capacity가 쪼개져 있다

즉 striped guard row는 "global total을 매 요청 계산"이 아니라 **bucket-local headroom**으로 승인한다.

### hot path fan-out은 작게 유지한다

요청 하나가 16개 bucket을 전부 훑으면 기다림만 여러 row로 번진다.

권장 방식:

1. home bucket 1개를 먼저 시도한다
2. 필요하면 spill bucket 1~2개만 정해진 순서로 시도한다
3. 그래도 부족하면 business rejection 또는 별도 refill path로 넘긴다

모든 bucket을 매번 합산/잠금하는 것은 striped guard row의 이점을 거의 없앤다.

## 2-2. budget rebalance는 hot path 밖으로 분리한다

bucket 간 capacity가 치우치면 budget 이동이 필요할 수 있다.

```sql
-- 항상 (src_bucket_id, dst_bucket_id) 오름차순으로 잠근다
SELECT campaign_id, bucket_id, budget_qty, reserved_qty
FROM campaign_guard_bucket
WHERE campaign_id = :campaign_id
  AND bucket_id IN (:src_bucket_id, :dst_bucket_id)
FOR UPDATE;

UPDATE campaign_guard_bucket
SET budget_qty = CASE
  WHEN bucket_id = :src_bucket_id THEN budget_qty - :qty
  WHEN bucket_id = :dst_bucket_id THEN budget_qty + :qty
END
WHERE campaign_id = :campaign_id
  AND bucket_id IN (:src_bucket_id, :dst_bucket_id);
```

rebalancing을 hot write path에 붙이면 다시 중앙 조정이 병목이 된다.
가능하면 낮은 빈도의 refill worker나 운영 루틴으로 분리한다.

## 3. counter sharding: 쓰기 fan-out을 읽기 fan-in으로 바꾸기

counter sharding은 같은 논리 총량을 여러 shard counter에 나눠 적는다.

```sql
CREATE TABLE campaign_counter_shard (
  campaign_id BIGINT NOT NULL,
  shard_id INT NOT NULL,
  reserved_qty BIGINT NOT NULL,
  PRIMARY KEY (campaign_id, shard_id)
);
```

```sql
INSERT INTO campaign_counter_shard (campaign_id, shard_id, reserved_qty)
VALUES (:campaign_id, :shard_id, :qty)
ON DUPLICATE KEY UPDATE reserved_qty = reserved_qty + VALUES(reserved_qty);
```

```sql
SELECT COALESCE(SUM(reserved_qty), 0) AS reserved_qty
FROM campaign_counter_shard
WHERE campaign_id = :campaign_id;
```

이 패턴은 다음에서 강하다.

- like count, usage metering, soft quota telemetry
- write 폭주가 심하고 total read는 상대적으로 덜 뜨겁다
- 요약값을 materialized view/cache로 다뤄도 된다

하지만 hard capacity admission에서는 한계가 분명하다.

- 매 write마다 shard 합산을 다시 하면 병목이 읽기로 옮겨갈 뿐이다
- 승인 여부가 즉시 정확해야 하면 counter shard만으로는 부족하다
- 결국 striped guard budget, unit token claim, ledger projection 중 하나와 결합해야 한다

즉 counter sharding은 **admission gate 자체**라기보다 hot aggregate의 write burden을 분산하는 도구다.

## 4. ledger fallback: row update 대신 append-only source of truth로 가기

aggregate row를 계속 덮어쓰는 대신, 점유/반납을 ledger에 append하는 방식도 있다.

```sql
CREATE TABLE campaign_capacity_ledger (
  campaign_id BIGINT NOT NULL,
  reservation_id BIGINT NOT NULL,
  bucket_id INT NOT NULL,
  event_seq BIGINT NOT NULL,
  event_type VARCHAR(16) NOT NULL,
  qty INT NOT NULL,
  occurred_at TIMESTAMP NOT NULL,
  PRIMARY KEY (campaign_id, reservation_id, event_seq)
);
```

```sql
INSERT INTO campaign_capacity_ledger (
  campaign_id, reservation_id, bucket_id, event_seq, event_type, qty, occurred_at
) VALUES (
  :campaign_id, :reservation_id, :bucket_id, :event_seq, 'HOLD', :qty, NOW()
);
```

ledger fallback이 주는 장점:

- append-only라 overwrite hot row보다 write path가 안정적이다
- repair, replay, 감사 추적의 기반이 된다
- striped guard row budget과 실제 detail/hold 상태를 대조하기 쉽다

대신 pure ledger에는 한계가 있다.

- active predicate를 계산하거나 projection을 유지해야 한다
- 중복 append를 막을 idempotency key가 필요하다
- 즉시 hard reject가 필요하면 ledger alone으로는 부족하다

그래서 실전에서는 보통 아래 조합으로 쓴다.

1. `striped guard row + ledger`
2. `counter shard + ledger projection`
3. `ledger + tokenized unit/slot claim`

첫 번째 조합이 가장 흔하다.
guard bucket이 실시간 admission을 맡고, ledger가 repair와 audit source가 된다.

## 무엇을 고를지 빠르게 정리하면

### striped guard row가 맞는 경우

- oversell을 즉시 막아야 한다
- 요청이 자연스럽게 분산될 stable key가 있다
- 약간의 stranded headroom과 budget rebalance 복잡도를 감당할 수 있다

대표 예:

- flash sale coupon quota
- `room_type_id + stay_day` shared pool
- tenant별 동시 세션 제한

### counter sharding이 맞는 경우

- write는 매우 뜨겁지만 total read는 상대적으로 적다
- hard reject보다 usage 집계나 soft limit가 더 중요하다
- materialized total이나 cache를 둘 수 있다

대표 예:

- 좋아요 수, 조회 수, metering
- soft quota 관측
- 배치성 summary counter

### ledger fallback이 맞는 경우

- 수동 수정과 재처리가 잦다
- summary drift를 재계산할 근거가 필요하다
- bucket 수 조정, backfill, audit trace가 중요하다

대표 예:

- hold/confirm/release가 복잡한 예약 시스템
- 회계성 차감/복구 이력
- 운영 복구가 자주 필요한 shared inventory

## 자주 하는 실수

- bucket을 32개로 늘려 놓고 매 요청마다 전 bucket 합산/잠금한다
- acquire는 hash bucket을 쓰는데 release는 그냥 첫 bucket에 반납한다
- guard bucket은 두고 detail row/expiry worker/manual SQL이 우회 경로를 가진다
- ledger를 append-only로 만들고 active predicate, idempotency, reconciliation query는 정의하지 않는다
- bucket rebalance를 임의 순서 update로 처리해 deadlock을 새로 만든다

## 실전 시나리오

### 시나리오 1. flash sale coupon quota

`campaign_guard` 하나에 모든 요청이 몰려 p99가 급등한다.

권장:

- `campaign_guard_bucket(campaign_id, bucket_id)`로 분산
- 주문/사용자 기준 stable bucket을 저장
- bucket budget으로 즉시 승인/거절
- 실제 claim/expire/release는 ledger에 append
- ledger와 bucket summary를 대조하는 reconciliation job 유지

### 시나리오 2. room_type-day shared inventory

`(room_type_id, stay_day)` guard row 하나가 특정 성수일에 너무 뜨거워진다.

권장:

- `(room_type_id, stay_day, bucket_id)` striped guard 도입
- reschedule은 old/new bucket과 day union을 같은 order로 잠금
- bucket 쏠림이 심하면 refill worker 또는 더 근본적으로 slot/unit claim으로 재설계

### 시나리오 3. 운영 복구가 잦은 reservation hold path

만료 cleanup 지연, 수동 복구, 재처리 때문에 aggregate row가 자주 어긋난다.

권장:

- row overwrite 중심 설계에서 ledger source of truth로 이동
- summary projection은 bounded rebuild 가능하게 유지
- hard reject가 남아 있다면 guard bucket은 얇게 두고, truth/repair는 ledger가 맡는다

## 결정 체크리스트

- 이 경로는 oversell을 즉시 막아야 하는가
- request마다 만지는 bucket 수를 1개 또는 작은 상수로 제한했는가
- acquire와 release가 같은 bucket id를 공유하도록 detail/ledger에 저장하는가
- bucket-local budget 없이 global sum을 write path에서 다시 계산하고 있지 않은가
- counter shard read fan-in을 cache/materialized summary 없이 hot path에 올리지 않았는가
- ledger의 active predicate, idempotency key, reconciliation query를 정의했는가
- rebalancing이나 multi-bucket lock이 있다면 canonical lock order가 있는가

## 꼬리질문

> Q: guard row hotspot을 만나면 그냥 counter shard로 바꾸면 되나요?
> 의도: admission gate와 summary counter를 구분하는지 확인
> 핵심: hard capacity path라면 shard counter alone은 부족하고 striped guard budget이나 token/unit claim이 함께 필요하다

> Q: striped guard row가 exact invariant를 어떻게 유지하나요?
> 의도: bucket 개수만 늘린 설계와 local budget 설계를 구분하는지 확인
> 핵심: 각 bucket이 자신만의 headroom을 갖고 승인해야 hot path가 global total 재계산으로 돌아가지 않는다

> Q: ledger fallback이 좋아 보여도 왜 guard가 남을 수 있나요?
> 의도: append-only truth와 synchronous admission을 분리해서 이해하는지 확인
> 핵심: ledger는 repair/audit에는 강하지만 즉시 hard reject는 별도 arbitration surface가 필요한 경우가 많다

## 한 줄 정리

guard row hotspot의 해법은 락을 없애는 것이 아니라, 단일 aggregate row가 맡던 admission과 summary 책임을 striped guard row, counter shard, ledger projection으로 분리해 동시성을 분산하는 것이다.
