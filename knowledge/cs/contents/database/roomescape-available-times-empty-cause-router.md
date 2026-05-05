---
schema_version: 3
title: roomescape 예약 가능 시간이 안 보여요 원인 라우터
concept_id: database/roomescape-available-times-empty-cause-router
canonical: false
category: database
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/roomescape
review_feedback_tags:
- available-times-empty
- left-join-filter-placement
- availability-vs-admission-drift
aliases:
- roomescape 예약 가능 시간 안 보임
- roomescape available times empty
- 룸이스케이프 가능한 시간 조회가 비어요
- 예약 가능 시간 조회 결과가 없음
- 취소된 예약인데도 시간이 계속 막혀요
symptoms:
- roomescape에서 예약 가능한 시간 목록을 조회했는데 하루가 통째로 비어 보여요
- 취소된 예약은 무시해야 하는데 가능한 시간이 하나도 안 남아요
- 관리자 화면에서는 예약 가능하다고 봤는데 생성 API에서는 다시 충돌이 나요
- 리뷰어가 LEFT JOIN 조건 위치와 active predicate를 같이 보라고 했는데 왜인지 모르겠어요
intents:
- symptom
- troubleshooting
- mission_bridge
prerequisites:
- database/sql-reading-relational-modeling-primer
- database/transaction-basics
next_docs:
- database/roomescape-available-times-active-predicate-antijoin-bridge
- database/roomescape-reservation-cancel-reschedule-active-predicate-bridge
- database/active-predicate-drift-reservation-arbitration
- database/roomescape-reservation-concurrency-bridge
linked_paths:
- contents/database/roomescape-availability-vs-stale-read-vs-concurrency-decision-guide.md
- contents/database/roomescape-available-times-active-predicate-antijoin-bridge.md
- contents/database/roomescape-reservation-cancel-reschedule-active-predicate-bridge.md
- contents/database/active-predicate-drift-reservation-arbitration.md
- contents/database/roomescape-reservation-concurrency-bridge.md
- contents/database/left-join-filter-placement-primer.md
confusable_with:
- database/roomescape-availability-vs-stale-read-vs-concurrency-decision-guide
- database/roomescape-available-times-active-predicate-antijoin-bridge
- database/roomescape-reservation-cancel-reschedule-active-predicate-bridge
- database/roomescape-reservation-concurrency-bridge
forbidden_neighbors:
- contents/database/roomescape-reservation-concurrency-bridge.md
expected_queries:
- roomescape 예약 가능 시간 API가 갑자기 빈 배열만 주면 어디부터 의심해야 해?
- 취소된 예약을 빼고 조회한다는데도 가능한 시간이 다 사라지는 이유가 뭐야?
- 가능한 시간 조회에서는 열려 보이는데 실제 예약 생성은 막히는 상황을 어떻게 나눠 봐야 해?
- reviewer가 LEFT JOIN 필터를 WHERE에 두지 말라고 한 뜻을 roomescape 예시로 설명해줘
- 예약 가능 시간 목록이 없을 때 active predicate랑 cancellation 상태를 왜 같이 확인해야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 예약 가능 시간이 통째로 사라지거나 취소한
  예약이 계속 자리를 막고, 조회 화면은 열려 있는데 저장 단계에서만 다시 충돌하는
  상황을 증상에서 원인으로 가르는 symptom_router다. 빈 슬롯이 하나도 안 남음,
  LEFT JOIN 필터 위치가 이상함, 막는 예약 기준이 안 풀림, 읽기 판단과 쓰기 판정이
  따로 논다, 가능한 줄 알았는데 생성이 실패함 같은 자연어 paraphrase가 active
  predicate와 arbitration drift 원인에 매핑된다.
---

# roomescape 예약 가능 시간이 안 보여요 원인 라우터

## 한 줄 요약

> roomescape 예약 가능 시간이 비어 보일 때는 "데이터가 없다"보다, 조회 쿼리가 blocker를 너무 넓게 잡았거나 `LEFT JOIN` 의미를 깨뜨렸거나, 읽기용 가능 시간 판단과 실제 저장 시점 판단이 서로 다른 truth를 보고 있을 가능성이 더 크다.

## 가능한 원인

1. **`LEFT JOIN` 오른쪽 조건이 `WHERE`로 내려가 시간 슬롯 자체가 지워졌다.** 취소된 예약을 제외하려고 `WHERE reservation.status <> 'CANCELED'`를 붙이면 `NULL` 행까지 탈락해 가능한 시간이 전부 사라질 수 있다. 이 갈래는 [roomescape 예약 가능 시간 조회 ↔ anti-join과 active predicate 브릿지](./roomescape-available-times-active-predicate-antijoin-bridge.md)와 [LEFT JOIN 필터 위치 입문서](./left-join-filter-placement-primer.md)로 바로 이어진다.
2. **조회용 active predicate와 상태 전이 규칙이 어긋났다.** `CANCELED`나 만료된 예약을 이미 풀린 것으로 봐야 하는데 조회는 여전히 blocker로 읽으면, 실제로는 비어 있어야 할 슬롯이 계속 막혀 보인다. 이 경우는 [roomescape 예약 변경/취소 ↔ active predicate와 상태 전이 브릿지](./roomescape-reservation-cancel-reschedule-active-predicate-bridge.md)로 가서 어떤 상태가 지금 시간을 막는지부터 다시 고정한다.
3. **가능 시간 조회와 실제 예약 생성이 다른 arbitration surface를 본다.** 목록 API는 `NOT EXISTS`로 보는데 생성 API는 유니크 제약이나 다른 조건으로 막으면, 화면에서는 열려 보여도 저장 순간 다시 충돌이 날 수 있다. 이때는 [같은 시간대 예약 동시 요청 — 락 vs 유니크 제약 vs 낙관적 락 결정](./roomescape-reservation-concurrency-bridge.md)을 함께 봐야 한다.
4. **취소/변경 cleanup이 늦어 blocker truth가 남아 있다.** 상태 라벨은 바뀌었는데 실제 blocker 해제 기준이 같이 내려가지 않으면 가능한 시간이 늦게 풀리거나 하루 전체가 막힌 것처럼 보인다. 이 갈래는 [Active Predicate Drift in Reservation Arbitration](./active-predicate-drift-reservation-arbitration.md)로 이어서 본다.

## 빠른 자기 진단

1. 가능한 시간 조회 SQL이 `LEFT JOIN` 뒤 `WHERE reservation...` 조건을 쓰는지 먼저 본다. 그렇다면 join 의미가 깨진 분기를 먼저 의심한다.
2. 취소, 만료, 변경된 예약이 어떤 상태값일 때 blocker에서 빠지는지 적어 본다. 팀의 조회 쿼리와 생성 로직이 같은 기준을 쓰지 않으면 active predicate drift 가능성이 높다.
3. 화면 목록 API와 실제 저장 API가 같은 날짜/시간 truth를 보는지 확인한다. 하나는 조회용 anti-join, 다른 하나는 제약/락으로만 막고 있다면 조회와 생성이 다르게 보일 수 있다.
4. 취소 직후나 변경 직후에만 시간이 안 풀린다면 cleanup 지연이나 상태 전이 handoff를 본다. 이 경우 단순 조회 버그보다 blocker 해제 타이밍이 핵심이다.

## 다음 학습

- `LEFT JOIN`, `NOT EXISTS`, active blocker 정의를 roomescape 예시로 다시 묶고 싶다면 [roomescape 예약 가능 시간 조회 ↔ anti-join과 active predicate 브릿지](./roomescape-available-times-active-predicate-antijoin-bridge.md)를 본다.
- 취소와 변경 이후 왜 blocker가 늦게 풀리는지 보려면 [roomescape 예약 변경/취소 ↔ active predicate와 상태 전이 브릿지](./roomescape-reservation-cancel-reschedule-active-predicate-bridge.md)로 이어간다.
- 조회는 열려 보이는데 저장에서는 충돌하는 이유를 write-time 관점에서 보려면 [같은 시간대 예약 동시 요청 — 락 vs 유니크 제약 vs 낙관적 락 결정](./roomescape-reservation-concurrency-bridge.md)을 함께 읽는다.
- 상태 라벨과 실제 blocker truth가 왜 어긋나는지 더 깊게 보고 싶다면 [Active Predicate Drift in Reservation Arbitration](./active-predicate-drift-reservation-arbitration.md)을 본다.
