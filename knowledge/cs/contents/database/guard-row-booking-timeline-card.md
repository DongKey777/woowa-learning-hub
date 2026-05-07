---
schema_version: 3
title: Guard Row Booking Timeline Card
concept_id: database/guard-row-booking-timeline-card
canonical: true
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- guard-row-booking-timeline
- constraint-first-booking-order
- existing-row-queue-surface
aliases:
- guard row booking timeline
- when to use guard row
- guard row for update booking
- constraint first booking
- booking locking timeline
- slot row vs guard row
- exclusion constraint vs guard row
- guard row 처음
- 언제 guard row
- 예약 guard row
symptoms:
- 예약 동시성 문제를 보자마자 base booking table에 FOR UPDATE를 붙이려 하고 있어
- UNIQUE, slot row, exclusion constraint, guard row 순서를 구분하지 못하고 있어
- 0 row FOR UPDATE와 existing guard row queue를 같은 방식으로 이해하고 있어
intents:
- comparison
- definition
- design
prerequisites:
- database/constraint-first-booking-primer
- database/unique-vs-slot-row-vs-guard-row-quick-chooser
next_docs:
- database/booking-guard-row-retry-card
- database/guard-row-scope-quick-examples
- database/phantom-safe-booking-patterns-primer
- database/guard-row-contention-observability-cheatsheet
linked_paths:
- contents/database/constraint-first-booking-primer.md
- contents/database/unique-vs-slot-row-vs-guard-row-quick-chooser.md
- contents/database/booking-guard-row-retry-card.md
- contents/database/empty-result-locking-cheat-sheet-postgresql-mysql.md
- contents/database/guard-row-scope-quick-examples.md
- contents/database/phantom-safe-booking-patterns-primer.md
- contents/system-design/inventory-reservation-system-design.md
confusable_with:
- database/unique-vs-slot-row-vs-guard-row-quick-chooser
- database/empty-result-locking-cheat-sheet-postgresql-mysql
- database/phantom-safe-booking-patterns-primer
forbidden_neighbors: []
expected_queries:
- 예약 동시성 문제에서 UNIQUE, slot row, exclusion constraint, guard row는 어떤 순서로 고려해야 해?
- guard row FOR UPDATE는 언제 쓰고 0 row FOR UPDATE와 무엇이 달라?
- constraint-first booking이 먼저이고 guard row가 나중인 이유를 초보자 기준으로 설명해줘
- room_type day 재고처럼 여러 write path를 같은 대표 key로 직렬화해야 할 때 guard row를 쓰는 이유는 뭐야?
- slot row와 guard row 중 예약 재고 모델에 무엇이 더 맞는지 timeline으로 비교해줘
contextual_chunk_prefix: |
  이 문서는 예약 동시성에서 UNIQUE, slot row, PostgreSQL exclusion constraint, guard row FOR UPDATE를 어떤 순서로 선택할지 설명하는 beginner chooser다.
  guard row booking timeline, constraint first booking, slot row vs guard row, 0 row FOR UPDATE 같은 자연어 질문이 본 문서에 매핑된다.
---
# Guard Row Booking Timeline Card

> 한 줄 요약: 예약 동시성 문제를 처음 보면 `FOR UPDATE`부터 붙이기 쉽지만, beginner 기준 더 안전한 순서는 `UNIQUE` -> slot row -> exclusion constraint -> guard row이고, guard row는 이 앞선 선택지들로 충돌 truth를 더 이상 깔끔하게 표현하기 어려울 때 등장한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Constraint-First Booking Primer](./constraint-first-booking-primer.md)
- [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- [Booking Guard Row Retry Card](./booking-guard-row-retry-card.md)
- [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)
- [Guard Row Scope Quick Examples](./guard-row-scope-quick-examples.md)
- [Inventory Reservation System Design](../system-design/inventory-reservation-system-design.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: guard row booking timeline, when to use guard row, guard row for update booking, constraint first booking, booking locking timeline, guard row 처음, 언제 guard row, 왜 unique 말고 guard row, slot row vs guard row, exclusion constraint vs guard row, booking for update basics, what is guard row booking

## 핵심 개념

처음엔 "`SELECT ... FOR UPDATE`로 비어 있는 시간대를 잠그면 되지 않나?"라고 생각하기 쉽다.

하지만 예약 문제의 첫 질문은 락 문법이 아니라 이것이다.

- 이 규칙을 exact key 충돌로 바꿀 수 있는가
- 시간 구간을 작은 slot/day key 집합으로 바꿀 수 있는가
- PostgreSQL이라면 overlap 자체를 constraint로 적을 수 있는가

이 셋이 모두 잘 안 맞을 때, 그다음 선택지가 **guard row를 `FOR UPDATE`로 잡아 writer를 한 줄로 세우는 방식**이다.

즉 guard row는 "제일 강한 락"이 아니라, **constraint-first 선택지가 더 이상 자연스럽지 않을 때 쓰는 대표 queue row**다.

## 한눈에 보기

| 단계 | 먼저 시도할 것 | 잘 맞는 질문 | 여기서 멈춰도 되나 |
|---|---|---|---|
| 1 | `UNIQUE` / PK | "같은 요청 둘이 동시에 성공하면 안 돼요" | exact key 하나면 예 |
| 2 | slot row + `UNIQUE` | "30분/1박/day 단위로 겹치면 안 돼요" | slot/day key로 truth가 닫히면 예 |
| 3 | exclusion constraint | "임의 시간 구간 overlap 자체가 규칙이에요" + PostgreSQL | single-table overlap이면 예 |
| 4 | guard row + `FOR UPDATE` | "취소/연장/만료/재고까지 같은 queue로 묶어야 해요" | 앞 단계가 설명력을 잃을 때 선택 |

짧은 기억법:

- exact key면 `UNIQUE`
- discrete bucket이면 slot row
- PostgreSQL continuous interval이면 exclusion constraint
- 여러 write path를 같은 대표 key에서 직렬화해야 하면 guard row

## 언제 constraint-first가 멈추나

아래 질문에 yes가 늘어나면 guard row 쪽으로 기운다.

| 보이는 장면 | 왜 constraint-first가 답답해지나 | guard row가 좋아지는 이유 |
|---|---|---|
| slot/day로 자르면 row 수가 너무 많아진다 | 예약 하나가 너무 많은 key를 만진다 | 더 작은 key fan-out 대신 대표 key queue를 만든다 |
| booking create 외에 cancel, extend, expire도 같은 재고를 흔든다 | insert 한 번만 막아서는 설명이 끝나지 않는다 | 모든 write path를 같은 protocol로 묶기 쉽다 |
| 개별 `room_id`보다 `room_type` 총량이 먼저 중요하다 | exact booking row보다 pooled inventory가 핵심이다 | `(room_type_id, stay_day)` 같은 guard가 더 직접적이다 |
| MySQL에서 continuous overlap을 single-table constraint로 닫기 어렵다 | exclusion constraint 같은 직접 표현이 없다 | guard row 아래에서 overlap/capacity를 재검사한다 |

핵심은 "constraint가 약해서"가 아니다.
**충돌 truth가 한 row insert나 한 constraint로 더 이상 짧게 설명되지 않아서** guard row가 등장하는 것이다.

## guard row `FOR UPDATE`가 맞는 순간

guard row를 잡는 목적은 booking detail row를 잠그는 것이 아니다.
먼저 **항상 존재하게 만들 수 있는 대표 key**를 잠가, 충돌 가능한 요청이 같은 순서로 지나가게 만드는 것이다.

예시 timeline:

| 시점 | 요청 A | 요청 B |
|---|---|---|
| t1 | `(room_type_id=7, stay_day=2026-05-01)` guard row `FOR UPDATE` |  |
| t2 | overlap/capacity 재검사 | 같은 guard row lock을 기다림 |
| t3 | hold/booking row insert 또는 수량 차감 | 계속 대기 |
| t4 | commit | lock 획득 후 다시 재검사 |
| t5 |  | 남은 수량/겹침 상태에 따라 성공 또는 실패 |

여기서 중요한 점은 두 가지다.

- `FOR UPDATE`를 booking table의 "빈 결과"에 거는 게 아니라, **guard row라는 existing row**에 건다
- lock 아래에서 overlap/capacity를 **다시 확인**해야 한다

그래서 guard row는 "`0 row FOR UPDATE`의 대체 문법"이 아니라, **absence check를 existing-row queue로 번역한 설계**에 가깝다.

## 흔한 오해와 함정

- "`FOR UPDATE`가 나오면 처음부터 guard row로 가야 한다"
  - 아니다. beginner 기본 순서는 constraint-first다.
- "guard row가 생기면 overlap 재검사는 없어도 된다"
  - 아니다. guard row는 queue surface이고, 실제 blocker 계산은 lock 아래에서 다시 본다.
- "base booking overlap query에 `FOR UPDATE`를 붙인 것과 guard row는 거의 같다"
  - 아니다. 전자는 `0 row`면 보호가 비어 버릴 수 있고, 후자는 existing guard row를 잠근다.
- "guard row는 무조건 더 안전한 상위 패턴이다"
  - 아니다. exact key나 slot key로 닫히는 문제라면 constraint-first가 더 짧고 운영도 쉽다.

## 실무에서 쓰는 모습

가장 쉬운 예시는 숙박 재고다.

- `idempotency_key` 중복은 `UNIQUE`로 막는다
- 1박 단위 개별 객실 점유만 보면 slot/day row도 가능하다
- 그런데 실제 서비스는 hold 생성, 결제 완료, 취소, 만료 worker, 운영자 재고 보정이 모두 같은 `room_type` 재고를 흔든다

이때는 `(room_type_id, stay_day)` guard row를 먼저 잠그고, 그 아래에서 "남은 수량이 있는가", "이미 만료된 hold는 제외했는가"를 다시 보는 편이 더 설명 가능하다.

즉 guard row는 **constraint-first가 실패했다**기보다, **문제가 booking insert 하나보다 넓어졌다**는 신호에 가깝다.

## 더 깊이 가려면

- constraint-first 출발점을 먼저 잡고 싶다면 -> [Constraint-First Booking Primer](./constraint-first-booking-primer.md)
- guard row에서 `lock timeout` / `deadlock` 뒤에 언제 기다리고, 언제 fail fast/retry할지 바로 이어서 보려면 -> [Booking Guard Row Retry Card](./booking-guard-row-retry-card.md)
- guard key를 `(resource)` / `(resource, day)` / pooled inventory로 고르고 싶다면 -> [Guard Row Scope Quick Examples](./guard-row-scope-quick-examples.md)
- `0 row FOR UPDATE`가 왜 같은 뜻이 아닌지 보려면 -> [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)
- booking overlap 패턴을 한 단계 넓게 비교하려면 -> [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)

## 한 줄 정리

예약에서 guard row `FOR UPDATE`는 첫 선택지가 아니라, `UNIQUE`·slot row·exclusion constraint로 충돌 truth를 충분히 설명하기 어려울 때 existing 대표 row에 queue를 세우는 다음 단계다.
