---
schema_version: 3
title: Slotization Migration and Backfill Playbook
concept_id: database/slotization-migration-backfill-playbook
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 91
mission_ids: []
review_feedback_tags:
- slotization
- migration
- backfill
- cutover
- double-booking
aliases:
- slotization migration
- interval to slot migration
- continuous interval to slot table
- slot table backfill
- reservation slot claim
- no double booking cutover
- dual write fence
- watermark drain
- slot shadow table
- slot cutover playbook
symptoms:
- continuous interval booking table을 slot claim table로 옮기면서 double-booking 없이 cutover해야 해
- historical backfill이 끝나기 전 target slot table을 admission에 써서 recent write를 놓칠 위험이 있어
- old interval writer와 new slot writer가 동시에 승인하는 split-brain arbitration을 막아야 해
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- database/range-invariant-enforcement-write-skew-phantom
- database/slot-row-rounding-half-open-dst-junior-checklist
next_docs:
- database/slotization-precheck-overlap-rounding-dst
- database/slot-delta-reschedule-semantics
- database/online-backfill-verification-cutover-gates
linked_paths:
- contents/database/range-invariant-enforcement-write-skew-phantom.md
- contents/database/engine-fallbacks-overlap-enforcement.md
- contents/database/slotization-precheck-overlap-rounding-dst.md
- contents/database/guard-row-scope-design-multi-day-bookings.md
- contents/database/slot-delta-reschedule-semantics.md
- contents/database/online-backfill-consistency.md
- contents/database/online-backfill-verification-cutover-gates.md
- contents/database/online-schema-change-strategies.md
- contents/database/idempotency-key-and-deduplication.md
confusable_with:
- database/slotization-precheck-overlap-rounding-dst
- database/slot-delta-reschedule-semantics
- database/online-backfill-consistency
forbidden_neighbors: []
expected_queries:
- interval table을 slot table로 migration할 때 backfill, catch-up, fenced cutover 순서를 어떻게 잡아?
- slotization cutover에서 한 시점에 admission authority가 하나만 있어야 double booking을 막는 이유가 뭐야?
- old interval writer와 new slot writer가 동시에 승인하면 split-brain arbitration이 되는 예시를 설명해줘
- target slot table을 backfill 중 projection으로만 쓰고 admission에는 쓰면 안 되는 phase는 언제야?
- slot expansion, active predicate, watermark drain, conflict quarantine을 migration playbook으로 정리해줘
contextual_chunk_prefix: |
  이 문서는 continuous interval to slot table migration을 backfill, catch-up, fenced cutover, single admission authority, no double booking 원칙으로 다루는 advanced playbook이다.
  slotization migration, slot table backfill, dual write fence, watermark drain 질문이 본 문서에 매핑된다.
---
# Slotization Migration and Backfill Playbook

> 한 줄 요약: continuous interval 테이블을 slot 테이블로 옮길 때 핵심은 "복사 완료"가 아니라, 한 시점에 오직 하나의 admission authority만 유지하면서 backfill, catch-up, cutover를 거쳐도 double-booking이 생기지 않게 하는 것이다.

**난이도: 🔴 Advanced**

관련 문서:

- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [Slotization Precheck Queries for Overlaps, Rounding Collisions, and DST Boundaries](./slotization-precheck-overlap-rounding-dst.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md)
- [Online Backfill Consistency와 워터마크 전략](./online-backfill-consistency.md)
- [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md)
- [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
- [Idempotency Key and Deduplication](./idempotency-key-and-deduplication.md)

retrieval-anchor-keywords: slotization migration, interval to slot migration, continuous interval to slot table, slot table backfill, reservation slot claim, no double booking cutover, overlap migration, dual write fence, watermark drain, slot shadow table, booking slotization, unique slot claim, slot cutover playbook, slotization precheck, slot rounding collision, DST boundary cutover, interval overlap preflight, slot delta reschedule semantics, slot claim tombstone cleanup, slot release watermark, reschedule union lock slot claim

## 핵심 개념

continuous interval 모델에서 slot 모델로 옮긴다는 말은 단순히 row 포맷을 바꾸는 일이 아니다.  
실제로는 overlap 판단의 **중재 surface**를 interval predicate에서 `UNIQUE(resource_id, slot_start)` 같은 slot claim surface로 옮기는 작업이다.

이때 double-booking이 생기는 가장 흔한 이유는 다음 둘 중 하나다.

- historical backfill이 끝나기 전에 target slot table을 admission에 써서, recent write가 빠진 채로 "비어 있다"고 오판한다
- old interval writer와 new slot writer가 같은 시간대를 **각자 따로 승인**해서 split-brain arbitration이 된다

따라서 migration의 핵심 원칙은 이것이다.

1. slot expansion 규칙은 deterministic해야 한다
2. active predicate는 source와 target에서 같아야 한다
3. 각 phase마다 admission authority는 정확히 하나여야 한다

## 먼저 고정할 계약

### 1. slotization은 표현 변경이 아니라 정책 변경일 수 있다

연속 interval이 임의 분 단위를 허용했다면 slot table은 아래 규칙을 미리 고정해야 한다.

- interval boundary: 보통 half-open interval `[start_at, end_at)`
- slot 크기: 5분, 15분, 30분, 1일
- timezone / DST 규칙
- setup/buffer/cleanup 시간 포함 여부
- `HELD`, `CONFIRMED`, `CANCELLED`, `EXPIRED` 같은 active predicate
- legacy interval이 slot 경계에 안 맞을 때의 정규화 규칙

예를 들어 `10:05 ~ 10:55`를 30분 slot으로 바꿀 때:

- floor/ceil로 `10:00`, `10:30` 두 slot을 점유로 볼지
- legacy 데이터 자체를 먼저 정규화할지
- slot 경계에 맞지 않는 예약은 cutover 전에 quarantine할지

이 계약이 먼저 없으면 backfill mismatch가 기술 문제가 아니라 business semantics 충돌이 된다.

### 2. target slot table은 analytics copy가 아니라 새 arbitration table이다

slot table은 조회 최적화 테이블이 아니라, cutover 후 overlap을 막을 **승인 surface**다. 그래서 최소한 다음 성질이 필요하다.

- `tenant_id, resource_id, slot_start` 기준 unique/primary key
- 어떤 phase에서 들어온 row인지 추적 가능한 메타데이터
- booking 단위 idempotent 재처리를 위한 `booking_id` 또는 version
- 충돌이 나면 조용히 무시하지 않고 hard failure로 승격하는 절차

`INSERT IGNORE`, `ON CONFLICT DO NOTHING`를 무심코 쓰면 같은 booking 재처리와 다른 booking 충돌을 구분하지 못해 source corruption을 숨기게 된다.

### 3. migration phase별 authority를 명시해야 한다

| phase | admission authority | slot table 역할 | 안전 규칙 |
|---|---|---|---|
| A. shadow backfill | old interval path | projection only | 요청 승인에 slot table을 절대 직접 쓰지 않는다 |
| B. catch-up / dual-write | old interval path + shared fence | warm standby | 승인된 interval 변화만 slot delta로 반영한다 |
| C. fenced cutover | 일시 정지 또는 단일 fenced writer | drain only | old/new writer가 동시에 승인하지 않게 막는다 |
| D. slot authoritative | slot unique key / guard set | source of truth | old interval table은 history/projection으로 강등한다 |

중요한 점은 B와 D 사이에 "둘 다 승인 가능"인 애매한 구간을 만들지 않는 것이다.

## double-booking이 생기는 실패 패턴

### 1. historical backfill과 live write가 다른 truth를 본다

- backfill은 `booking_interval`을 읽어 slot row를 채우는 중이다
- 동시에 새 예약은 여전히 old interval path로만 승인된다
- catch-up이 늦어서 target slot table에 최신 예약 slot이 아직 없다
- cutover 직후 slot writer는 그 slot이 비었다고 보고 또 승인한다

즉 backfill이 끝났다는 사실만으로 target이 최신 truth라는 뜻은 아니다.

### 2. conflict를 "idempotent retry"로 착각한다

slot row insert가 충돌했을 때 가능한 경우는 둘이다.

- 같은 booking이 같은 slot을 다시 넣는 정상 재시도
- 다른 booking이 이미 그 slot을 점유한 진짜 충돌

둘을 구분하지 않으면 source overlap, rounding bug, stale cancellation이 전부 묻힌다.

### 3. reschedule을 old release -> new acquire로 처리한다

기존 interval 예약을 이동할 때 old slot을 먼저 지우고 new slot을 나중에 잡으면, 중간 순간에 다른 요청이 틈새를 먹을 수 있다.  
reschedule은 항상 **old slot 집합과 new slot 집합의 합집합**을 같은 fence와 같은 canonical ordering 아래에서 처리해야 한다.

### 4. rollback 경로가 없는데 old writer를 다시 연다

cutover 뒤 old interval table을 더 이상 sync하지 않았는데 rollback이 필요하다고 해서 old writer를 다시 열면, stale projection을 기준으로 또 별도 승인이 시작된다.  
rollback window 동안은 old projection을 계속 따라가게 하거나, slot table에서 interval projection을 재생성할 수 있어야 한다.

## 권장 playbook

### 1. precheck: source를 target semantics로 먼저 검사한다

backfill 전에 최소한 아래를 잡아야 한다.

- source active booking끼리 실제 continuous overlap이 없는가
- slot rounding 후에는 서로 다른 두 booking이 같은 slot으로 collapse되지 않는가
- `cancelled_at`, `released_at`, `expired_at` 규칙이 active predicate와 일치하는가
- long booking, partial slot, DST crossing 같은 edge case가 확정되어 있는가

구체 질의 패턴은 [Slotization Precheck Queries for Overlaps, Rounding Collisions, and DST Boundaries](./slotization-precheck-overlap-rounding-dst.md)에 따로 정리한다.  
핵심은 `legacy-overlap`, `rounding-only-collision`, `dst-transition-crossing`을 한 conflict 수치로 섞지 않는 것이다.

이 단계에서 나온 충돌은 migration runtime에서 숨기지 말고 별도 conflict queue로 격리하는 편이 낫다.

### 2. shadow slot table과 migration fence를 만든다

```sql
CREATE TABLE booking_slot_claim (
  tenant_id BIGINT NOT NULL,
  resource_id BIGINT NOT NULL,
  slot_start TIMESTAMP NOT NULL,
  booking_id BIGINT NOT NULL,
  source_phase VARCHAR(16) NOT NULL,
  source_version BIGINT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  PRIMARY KEY (tenant_id, resource_id, slot_start),
  UNIQUE (booking_id, slot_start)
);

CREATE TABLE slotization_migration_control (
  migration_name VARCHAR(100) PRIMARY KEY,
  writer_mode VARCHAR(32) NOT NULL,
  fence_epoch BIGINT NOT NULL,
  snapshot_watermark TIMESTAMP NOT NULL,
  catchup_watermark TIMESTAMP NULL,
  updated_at TIMESTAMP NOT NULL
);
```

여기서 `writer_mode`와 `fence_epoch`는 "지금 누가 승인권을 갖는가"를 운영자가 말로 합의하는 대신 DB 상태로 고정하기 위한 장치다.

### 3. historical backfill은 idempotent하되 conflict에는 시끄러워야 한다

backfill은 booking 단위 또는 PK chunk 단위로 interval을 slot 집합으로 펼친다.

```text
for each active booking_interval chunk:
  expanded_slots = expand_interval_to_slots(booking, slot_policy)
  for each slot in expanded_slots:
    if slot empty:
      insert slot claim
    else if existing.booking_id == booking.id:
      no-op  // retry
    else:
      record conflict and fail chunk
```

핵심:

- 재실행 시 같은 booking이면 no-op여야 한다
- 다른 booking과 부딪히면 chunk를 실패시켜야 한다
- chunk 성공/실패, conflict count, last processed PK를 artifact로 남겨야 한다

이 단계에서는 old interval path만 admission authority다.  
slot table은 아직 projection일 뿐이며, write admission에서 조회해 "이미 찼다"고 판단하면 안 된다.

### 4. live catch-up을 붙여 target을 warm 상태로 만든다

historical backfill이 돌고 있는 동안 source는 계속 바뀐다. 그래서 아래 셋 중 하나가 필요하다.

- interval table 기반 CDC
- old writer가 내보내는 outbox/event stream
- 임시 dual-write path

중요한 점은 어떤 방식을 쓰든 **승인 결과를 복제**해야지, 두 군데에서 따로 승인하면 안 된다는 것이다.

특히 create/cancel/reschedule은 모두 slot delta로 번역돼야 한다.

- create: 새 slot claim insert
- cancel/expire: 기존 slot claim release
- reschedule: old/new slot union 계산 후 한 번에 이동

slot claim table 안에서 delta를 어떻게 apply하고 tombstone cleanup watermark를 어떻게 닫을지는 [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md)에 따로 정리한다.

여기서 multi-day booking이면 [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)의 canonical ordering 규칙을 그대로 재사용하는 편이 안전하다.

### 5. cutover는 freeze -> drain -> verify -> switch 순서로 한다

권장 순서:

1. `writer_mode`를 fenced 상태로 올리거나 아주 짧은 write freeze를 건다
2. old epoch에서 시작된 interval write들이 모두 끝날 때까지 기다린다
3. CDC/outbox/catch-up을 `fence_epoch` 직전 watermark까지 완전히 drain한다
4. 아래 gate를 통과했는지 확인한다
5. `writer_mode = SLOT_AUTHORITATIVE`로 바꾸고 새 writer만 연다

여기서 중요한 것은 "flag 켜기"가 아니라 **old writer 종료 시점과 catch-up 완료 시점이 같은 cutover 증거에 묶여야 한다**는 점이다.

### 6. cutover gate는 slot parity와 recent write를 같이 봐야 한다

최소 gate 예시:

- precheck overlap conflict = 0
- historical backfill chunk failure = 0
- catch-up lag at fence watermark = 0
- resource/day bucket별 expected slot count = actual slot count
- shadow read mismatch = 0 또는 허용 한도 이하
- cancel/reschedule edge-case 샘플 diff 통과
- rollback/projection rebuild 절차 리허설 완료

row count만 맞는다고 cutover하면 안 된다.  
slotization migration은 count보다 **slot occupancy parity**가 더 중요하다.

### 7. cutover 후 probation window를 둔다

cutover 직후 곧바로 old projection을 버리면 rollback 선택지가 사라진다. 그래서 보통은 잠시 동안:

- slot table을 admission source로 사용하고
- interval/history table도 계속 projection으로 갱신하고
- shadow read 또는 bucket compare를 일정 시간 더 돌리고
- mismatch가 없을 때 old-only path를 제거한다

즉 cleanup은 cutover 직후가 아니라 probation 종료 뒤에 하는 편이 안전하다.

## 코드로 보기

```java
MigrationMode mode = migrationControl.loadForUpdate("booking-slotization");

if (mode.isIntervalAuthoritative()) {
    Booking booking = intervalWriter.accept(request);
    slotProjector.applyDelta(booking); // projection only
} else if (mode.isSlotAuthoritative()) {
    guardLocker.lockCanonicalSet(request);
    SlotSet slots = slotPolicy.expand(request);
    slotWriter.claim(slots);           // unique slot claim is the new arbitration
    intervalProjector.upsertHistory(request);
} else {
    throw new CutoverInProgressException();
}
```

```text
cutover invariant
1. no request is admitted by both writers
2. no request is admitted by neither writer without explicit failure
3. catch-up watermark must pass the fence before SLOT_AUTHORITATIVE opens
4. rollback path must not rely on stale interval projection
```

핵심은 dual-write 자체가 아니라, **writer mode와 fence epoch가 승인 경로를 하나로 직렬화**한다는 데 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| shadow backfill + CDC catch-up | 기존 앱 write path 변경이 적다 | cutover drain과 lag 관리가 까다롭다 | 이미 CDC/outbox가 있는 시스템 |
| fenced dual-write | 최신 slot parity를 맞추기 쉽다 | 앱 write path가 복잡해진다 | booking write path를 직접 제어할 수 있을 때 |
| 짧은 write freeze cutover | 모델이 단순하고 검증이 명확하다 | 아주 짧아도 쓰기 중단이 생긴다 | 강한 정합성이 더 중요할 때 |
| probation 동안 reverse projection 유지 | rollback이 쉬워진다 | 추가 저장/운영 비용이 든다 | 새 slot writer 안정성을 아직 관찰해야 할 때 |

## 꼬리질문

> Q: backfill만 끝나면 바로 slot writer로 전환해도 되나요?
> 의도: historical copy와 recent write parity를 구분하는지 확인
> 핵심: 안 된다. catch-up이 fence watermark까지 drain됐다는 증거가 있어야 한다

> Q: old interval path와 new slot path를 잠깐 같이 열어 두면 왜 안 되나요?
> 의도: split-brain arbitration 위험을 이해하는지 확인
> 핵심: 둘이 같은 active predicate와 같은 최신 상태를 보장하지 못하면 같은 시간대를 각자 승인할 수 있다

> Q: slot 경계에 맞지 않는 legacy 예약은 어떻게 해야 하나요?
> 의도: slotization이 business semantics를 바꿀 수 있음을 아는지 확인
> 핵심: floor/ceil 규칙을 먼저 고정하고, 애매한 예약은 precheck 단계에서 정규화하거나 격리해야 한다

## 한 줄 정리

slotization migration에서 double-booking을 막는 비결은 slot table을 빨리 채우는 것이 아니라, deterministic slot policy와 single admission authority를 유지한 채 backfill, catch-up, fenced cutover를 차례로 통과시키는 것이다.
