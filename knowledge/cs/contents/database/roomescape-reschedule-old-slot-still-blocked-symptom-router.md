---
schema_version: 3
title: roomescape 예약 변경 뒤 이전 시간이 안 풀려요 원인 라우터
concept_id: database/roomescape-reschedule-old-slot-still-blocked-symptom-router
canonical: false
category: database
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
mission_ids:
- missions/roomescape
review_feedback_tags:
- reschedule-old-slot-stuck
- union-lock-handoff
- slot-rounding-self-conflict
aliases:
- roomescape 예약 변경 뒤 이전 시간 안 풀림
- reschedule 후 이전 슬롯이 계속 막힘
- 예약 옮겼는데 예전 시간이 비지 않음
- self conflict after reschedule
- old slot still blocked router
symptoms:
- roomescape에서 예약 시간을 옮겼는데 예전 시간대가 계속 막혀 있어요
- 예약 변경은 성공했는데 available times에는 이전 슬롯도 새 슬롯도 둘 다 막힌 것처럼 보여요
- 같은 예약을 수정하는데 자기 자신과 충돌했다고 나와요
- 취소나 변경 직후에만 이전 시간이 늦게 풀리거나 다시 막혀 보여서 어디부터 봐야 할지 모르겠어요
intents:
- symptom
- troubleshooting
- mission_bridge
prerequisites:
- database/transaction-basics
- database/roomescape-reservation-concurrency-bridge
next_docs:
- database/roomescape-reservation-cancel-reschedule-active-predicate-bridge
- database/reservation-reschedule-cancellation-transition-patterns
- database/slot-delta-reschedule-semantics
- database/guard-row-scope-design-multi-day-bookings
linked_paths:
- contents/database/roomescape-reservation-cancel-reschedule-active-predicate-bridge.md
- contents/database/reservation-reschedule-cancellation-transition-patterns.md
- contents/database/slot-delta-reschedule-semantics.md
- contents/database/guard-row-scope-design-multi-day-bookings.md
- contents/database/slot-row-rounding-half-open-dst-junior-checklist.md
- contents/database/active-predicate-drift-reservation-arbitration.md
confusable_with:
- database/roomescape-available-times-empty-cause-router
- database/overlapping-bookings-both-succeed-symptom-router
- database/reservation-reschedule-cancellation-transition-patterns
forbidden_neighbors:
- contents/database/roomescape-reservation-concurrency-bridge.md
expected_queries:
- roomescape에서 예약 시간을 옮긴 뒤 예전 슬롯이 안 풀리면 어디부터 확인해야 해?
- 예약 변경은 성공했는데 이전 시간도 계속 막혀 보일 때 원인을 어떻게 나눠?
- 같은 예약 수정인데 자기 자신과 충돌했다고 나오면 reschedule 쪽에서 뭘 의심해야 해?
- cancel 뒤 새 슬롯은 잡혔는데 old slot이 늦게 풀리는 상황은 어떤 문서로 가야 해?
- roomescape reschedule 이후 available times가 이상할 때 active predicate랑 slot 계산 중 뭐가 더 먼저야?
contextual_chunk_prefix: |
  이 문서는 roomescape 같은 예약 시스템에서 reschedule 뒤 old slot이 계속
  막혀 보이거나, 같은 예약 수정인데 자기 자신과 충돌하는 학습자 증상을
  release-before-acquire handoff, old/new scope union lock 누락, active predicate
  drift, slot rounding 불일치로 나눠 주는 symptom_router다. 예약 변경 성공 후
  이전 시간 안 풀림, old slot still blocked, self conflict after reschedule,
  취소 직후만 늦게 풀림 같은 자연어 표현이 이 문서의 분기에 매핑된다.
---

# roomescape 예약 변경 뒤 이전 시간이 안 풀려요 원인 라우터

## 한 줄 요약

> 예약 변경 뒤 이전 시간이 안 풀리는 증상은 보통 `변경 SQL 한 줄` 문제가 아니라, old slot을 언제 release로 간주하는지와 new slot을 언제 acquire로 간주하는지가 서로 다른 truth를 보고 있다는 신호다.

## 가능한 원인

1. **reschedule을 `old release -> new acquire` 두 단계로 쪼갰다.** 기존 시간을 먼저 비우고 새 시간을 다시 잡는 흐름이면, 중간 상태를 다른 요청이나 조회가 보면서 이전 슬롯이 다시 막힌 것처럼 남을 수 있다. 이 갈래는 [roomescape 예약 변경/취소 ↔ active predicate와 상태 전이 브릿지](./roomescape-reservation-cancel-reschedule-active-predicate-bridge.md)와 [Reservation Reschedule and Cancellation Transition Patterns](./reservation-reschedule-cancellation-transition-patterns.md)로 바로 이어진다.
2. **old scope와 new scope를 함께 잠그지 않았다.** 변경 전후 범위를 합집합으로 직렬화하지 않으면 같은 예약의 연장, 취소, 만료 cleanup이 서로 엇갈리면서 old slot 해제와 new slot 점유가 다른 순서로 보일 수 있다. 이 경우는 [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)를 먼저 본다.
3. **조회용 active predicate와 변경용 release truth가 다르다.** `status='CANCELED'`나 `expires_at < now()`만 보고 풀렸다고 생각했는데 available times 쿼리는 아직 active blocker로 읽으면, 변경은 성공했어도 이전 시간이 안 풀린 것처럼 보인다. 이 분기는 [Active Predicate Drift in Reservation Arbitration](./active-predicate-drift-reservation-arbitration.md)와 [roomescape 예약 변경/취소 ↔ active predicate와 상태 전이 브릿지](./roomescape-reservation-cancel-reschedule-active-predicate-bridge.md)로 이어진다.
4. **slot 계산 규칙이 create와 reschedule에서 다르다.** `[start, end)` 경계나 rounding 규칙이 다르면 같은 예약을 옮길 때 old slot은 남아 있고 new slot은 추가된 것처럼 보여 자기 자신과 충돌할 수 있다. 이 갈래는 [Slot Row 도입 전 주니어 체크리스트: Rounding, Half-Open Interval, DST](./slot-row-rounding-half-open-dst-junior-checklist.md)와 [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md)로 간다.

## 빠른 자기 진단

1. 변경 경로가 `취소 후 생성`처럼 두 요청으로 쪼개졌는지, 아니면 한 트랜잭션에서 old/new를 같이 다루는지 먼저 본다.
2. reschedule에서 실제로 잠그는 범위가 old slot과 new slot의 합집합인지 확인한다. old만 잠그거나 new만 잠그면 handoff drift가 남는다.
3. available times 조회가 보는 active 조건과 reschedule commit이 바꾸는 release 조건이 같은지 비교한다. 상태 라벨만 바뀌고 blocker truth가 안 바뀌면 이전 시간이 계속 막혀 보인다.
4. 같은 예약 수정인데 자기 자신과 충돌하면 slot expander를 의심한다. create, reschedule, cleanup이 같은 `[start, end)`와 rounding 규칙을 쓰는지 확인한다.

## 다음 학습

- 예약 변경과 취소를 상태 전이로 묶어 보는 기본 그림은 [roomescape 예약 변경/취소 ↔ active predicate와 상태 전이 브릿지](./roomescape-reservation-cancel-reschedule-active-predicate-bridge.md)에서 잡는다.
- old/new scope union lock과 mutation contract를 더 일반화해서 보려면 [Reservation Reschedule and Cancellation Transition Patterns](./reservation-reschedule-cancellation-transition-patterns.md)로 간다.
- slot row 모델에서 old slot release와 new slot claim을 어떻게 한 번만 적용할지 보려면 [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md)를 읽는다.
- 멀티데이나 guard row 설계 때문에 변경 경로가 꼬인다면 [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)을 이어서 본다.
