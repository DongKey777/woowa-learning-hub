---
schema_version: 3
title: Constraint-First Booking Primer
concept_id: database/constraint-first-booking-primer
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- constraint-before-locking
- read-then-insert-booking-race
- empty-row-for-update-misconception
aliases:
- constraint first booking
- unique before for update
- booking constraint primer
- reservation duplicate beginner
- for update empty row booking
symptoms:
- 예약 중복 방지를 처음 잡는데 unique와 for update 중 어디서 시작할지 헷갈려
- 빈 시간대를 먼저 조회하고 insert하는 코드가 왜 위험한지 감이 안 와
- exclusion constraint, slot row, guard row 중 어느 갈래로 이어질지 먼저 정하고 싶어
intents:
- definition
- design
prerequisites:
- database/transaction-basics
linked_paths:
- contents/database/unique-vs-slot-row-vs-guard-row-quick-chooser.md
- contents/database/exclusion-constraint-vs-slot-row-quick-chooser.md
- contents/database/phantom-safe-booking-patterns-primer.md
- contents/database/mysql-overlap-fallback-beginner-bridge.md
- contents/system-design/inventory-reservation-system-design.md
next_docs:
- database/phantom-safe-booking-patterns-primer
- database/unique-vs-slot-row-vs-guard-row-quick-chooser
- database/exclusion-constraint-vs-slot-row-quick-chooser
confusable_with:
- database/unique-vs-slot-row-vs-guard-row-quick-chooser
- database/exclusion-constraint-vs-slot-row-quick-chooser
- database/phantom-safe-booking-patterns-primer
forbidden_neighbors:
- contents/database/empty-result-locking-cheat-sheet-postgresql-mysql.md
expected_queries:
- 예약 중복 방지는 왜 for update보다 constraint를 먼저 봐?
- booking에서 unique 먼저 보라는 말이 무슨 뜻이야?
- 빈 row 조회 뒤 insert가 왜 위험해?
- 예약 문제를 처음 보면 unique, slot, exclusion 중 뭐부터 골라?
contextual_chunk_prefix: |
  이 문서는 예약 중복 방지를 처음 잡는 학습자에게 빈 시간대를 먼저 읽고 잠그는
  흐름보다 저장 시점 규칙으로 한 명만 통과시키는 방법을 먼저 잡아 주는 primer다.
  예약이 왜 동시에 둘 다 들어가, 빈 자리 조회를 믿어도 되나, 잠금보다 제약이
  먼저야, 겹침 방지를 어디서 막아야 해 같은 자연어 표현이 이 문서의 기초 개념에
  매핑된다.
---

# Constraint-First Booking Primer

> 한 줄 요약: 예약 중복 방지를 처음 설계할 때는 `FOR UPDATE`로 빈 자리를 잠그려 하기보다, 먼저 `UNIQUE`나 exclusion constraint처럼 "DB가 저장 시점에 거부할 수 있는 규칙"으로 바꿀 수 있는지 보는 편이 더 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- [Exclusion Constraint vs Slot Row 빠른 선택 가이드](./exclusion-constraint-vs-slot-row-quick-chooser.md)
- [MySQL Overlap Fallback Beginner Bridge](./mysql-overlap-fallback-beginner-bridge.md)
- [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)
- [database 카테고리 인덱스](./README.md)
- [Inventory Reservation System Design](../system-design/inventory-reservation-system-design.md)

retrieval-anchor-keywords: constraint first booking, unique before for update, booking constraint primer, reservation duplicate beginner, for update empty row booking, double booking why unique, unique slot booking basics, exclusion constraint booking intro, 언제 for update 말고 constraint, 예약 중복 처음, 왜 for update 말고 unique, booking overlap what is safe, beginner booking locking, constraint vs locking read basics

## 핵심 개념

초급자 기준으로는 예약 동시성 문제를 두 문장으로 먼저 나누면 된다.

- `constraint-first`: "겹치면 안 되는 규칙"을 DB가 저장 시점에 바로 거부하게 만든다.
- `FOR UPDATE first`: 먼저 조회해서 비어 있으면 안전하다고 믿고, 그 조회 결과를 락으로 지키려 한다.

왜 첫 번째가 더 안전하냐면, 예약 경쟁의 진짜 문제는 "이미 있는 row를 누가 수정하나"보다 **아직 없는 자리를 두 요청이 동시에 비어 있다고 보는 상황**이 더 자주 나오기 때문이다.

`FOR UPDATE`는 이미 읽은 row를 잠그는 데 강하다. 하지만 `0 row`면 잠근 것도 `0 row`라서, "빈 자리 자체"를 portable하게 보장한다고 생각하면 과대평가가 된다.

그래서 beginner 기본 규칙은 이렇다.

> 예약 문제를 처음 보면 `FOR UPDATE` 문법부터 고르지 말고, 먼저 이 규칙을 `UNIQUE`, slot claim의 `UNIQUE`, exclusion constraint 같은 저장 시점 제약으로 바꿀 수 있는지 본다.

## 한눈에 보기

| 지금 막힌 질문 | 먼저 보는 선택 | 이유 |
|---|---|---|
| "같은 예약 요청이 두 번 들어오면 안 돼요" | `UNIQUE` | exact key 중복은 write 시점에 한 명만 통과시키는 게 가장 단순하다 |
| "30분/1일 slot이 겹치면 안 돼요" | slot row + `UNIQUE` | overlap을 여러 exact key 충돌로 바꿀 수 있다 |
| "임의 시간 구간이 겹치면 안 돼요" + PostgreSQL | exclusion constraint | 겹치는 구간 자체를 DB 규칙으로 적을 수 있다 |
| "취소, 연장, 만료, 재고까지 같은 queue로 묶어야 해요" | guard row + `FOR UPDATE` | 이때는 기존 booking row보다 대표 guard key를 먼저 잠그는 편이 낫다 |

핵심 기억법:

- `FOR UPDATE`는 **이미 있는 row ownership**에 강하다
- constraint는 **새 row admission rule**에 강하다
- 예약에서 먼저 흔들리는 쪽은 보통 admission rule이다

## 왜 `FOR UPDATE`부터 잡으면 헷갈리나

팀이 처음 자주 쓰는 흐름은 대개 이렇다.

1. 겹치는 예약이 있는지 조회한다
2. 없으면 `INSERT`한다
3. 조회에 `FOR UPDATE`를 붙였으니 안전하다고 느낀다

문제는 2개의 요청이 같은 빈 시간대를 동시에 볼 수 있다는 점이다.

```text
T1: overlap 조회 -> 0 row
T2: overlap 조회 -> 0 row
T1: insert
T2: insert
```

이때 `FOR UPDATE`가 항상 막아 주려면 "빈 시간대" 자체가 같은 잠금 surface로 표현돼야 한다. 그런데 booking overlap은 보통 시간 구간 predicate라서, 엔진, 인덱스 경로, 격리 수준에 따라 lock footprint가 흔들리기 쉽다.

초급자에게 더 안전한 해석은 이것이다.

- `FOR UPDATE`를 봤다 -> "읽힌 row를 잠그는구나"
- `0 row FOR UPDATE`를 봤다 -> "빈 자리 전체가 잠겼다"라고 단정하지 말자

즉 `FOR UPDATE`는 "없는 예약을 한 명만 만들게 하는 규칙" 그 자체라기보다, **이미 읽힌 대상이 있을 때 후속 수정 순서를 맞추는 도구**에 가깝다.

## 예약에서 constraint-first가 잘 맞는 경우

### 1. exact duplicate 예약 요청

예: 같은 `idempotency_key`, 같은 `external_booking_id`, 같은 `(user_id, event_id)`

이 경우는 overlap이 아니라 exact key 중복이다. `UNIQUE`가 바로 정답에 가깝다.

```sql
ALTER TABLE booking_request
ADD CONSTRAINT uq_booking_request_idempotency
UNIQUE (idempotency_key);
```

패배 요청은 `duplicate key`로 끝나고, 서비스는 "이미 처리된 요청"으로 번역하면 된다.

### 2. 시간이 이미 slot/day 단위로 굳은 예약

예: 30분 회의실, 1박 숙박, 좌석-회차 예약

이 경우는 overlap을 바로 잠그려 하기보다 slot claim row로 내려서 `UNIQUE`를 거는 편이 더 설명 가능하다.

```sql
CREATE TABLE room_slot_claim (
  room_id BIGINT NOT NULL,
  slot_start TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (room_id, slot_start)
);
```

즉 "겹침"을 "같은 slot key 중복"으로 바꾼다.

### 3. PostgreSQL에서 continuous interval 자체가 진짜 규칙

예: `10:07~11:43`처럼 임의 길이 예약

이 경우는 exclusion constraint가 더 직접적이다.

```sql
ALTER TABLE room_booking
ADD CONSTRAINT room_booking_no_overlap
EXCLUDE USING gist (
  room_id WITH =,
  tstzrange(start_at, end_at, '[)') WITH &&
);
```

애플리케이션이 먼저 "비었는지"를 믿지 않아도, DB가 저장 시점에 겹침을 거부한다.

## 언제 `FOR UPDATE`가 다시 주인공이 되나

constraint-first가 기본이라고 해서 `FOR UPDATE`가 필요 없다는 뜻은 아니다. 다만 **등장 순서**가 바뀐다.

| 장면 | `FOR UPDATE` 역할 |
|---|---|
| 이미 있는 booking row를 취소/확정/상태 전이 | 같은 row를 동시에 바꾸지 않게 잠근다 |
| 이미 만든 idempotency row를 읽고 재사용 | existing row를 안전하게 확인한다 |
| guard row를 먼저 잡고 연장/취소/만료를 같은 protocol로 묶음 | detail booking row가 아니라 대표 queue row를 잠근다 |

즉 `FOR UPDATE`는 "constraint 대신 쓰는 첫 무기"보다, **constraint로 winner를 가른 뒤 existing row나 guard row를 다루는 두 번째 무기**로 보는 편이 더 맞다.

예약에서 guard row가 필요한 경우는 보통 이런 장면이다.

- booking, hold, blackout, expiry cleanup이 모두 같은 자원을 흔든다
- capacity나 later assignment까지 같이 관리해야 한다
- 패배 요청을 duplicate error보다 queueing으로 다루는 편이 낫다

이때도 보통 base booking table의 overlap query를 바로 잠그기보다, `(room_id, day)` 같은 **항상 존재하게 만들 수 있는 대표 key**를 먼저 잠근다.

## 흔한 오해와 함정

- "`FOR UPDATE`가 더 강한 락이니까 `UNIQUE`보다 안전하다"
  - 강한 건 락 모드이지, 부재 규칙 표현력은 아니다. exact duplicate는 `UNIQUE`가 더 직접적이다.
- "`UNIQUE`는 exact key만 막으니 예약에는 쓸 데가 없다"
  - slot row로 내려가면 예약도 exact key 여러 개로 바꿀 수 있다.
- "`0 row FOR UPDATE`면 그 시간대가 예약된 거나 마찬가지다"
  - 아니다. 그 해석은 엔진과 인덱스 경로에 과도하게 기대기 쉽다.
- "constraint를 쓰면 `FOR UPDATE`는 전혀 필요 없다"
  - 아니다. existing row 상태 전이, guard row queue, 후속 재사용 단계에서는 여전히 중요하다.

## 실무에서 쓰는 모습

시나리오 1. **중복 결제/예약 요청 재전송**
먼저 `idempotency_key`에 `UNIQUE`를 둔다. 이 단계에서는 `FOR UPDATE`보다 constraint가 winner를 더 명확하게 정한다.

시나리오 2. **30분 회의실 예약**
기본 보호는 `room_id + slot_start`의 `UNIQUE`다. 나중에 예약 변경이나 취소를 안전하게 처리할 때만 existing slot row 또는 별도 guard row 락이 등장한다.

시나리오 3. **숙박 재고 + 연장/취소/만료**
처음부터 booking detail row에 `FOR UPDATE`를 거는 것보다, day guard나 inventory guard를 먼저 잠그고 그 아래에서 상태 전이를 처리하는 편이 프로토콜이 분명하다.

## 더 깊이 가려면

- exact duplicate와 slot/guard 선택을 한 번에 보고 싶으면 -> [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- PostgreSQL overlap을 constraint로 닫는 그림이 더 필요하면 -> [Exclusion Constraint vs Slot Row 빠른 선택 가이드](./exclusion-constraint-vs-slot-row-quick-chooser.md)
- MySQL에서 왜 base booking `FOR UPDATE`를 과신하면 안 되는지 보려면 -> [MySQL Overlap Fallback Beginner Bridge](./mysql-overlap-fallback-beginner-bridge.md)
- booking 전체 패턴을 한 단계 더 넓게 보고 싶으면 -> [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)

## 면접/시니어 질문 미리보기

> Q: 왜 예약에서 `FOR UPDATE`보다 constraint를 먼저 보나요?
> 의도: existing row lock과 new-row admission rule을 분리하는지 확인
> 핵심: 예약 경쟁은 "없던 자리를 누가 먼저 차지하나"가 핵심인 경우가 많아서, 저장 시점 제약이 더 직접적이다.

> Q: `UNIQUE`로 못 닫히는 예약은 바로 `FOR UPDATE`로 가나요?
> 의도: slot row, exclusion constraint, guard row를 순서 있게 설명하는지 확인
> 핵심: 아니오. 먼저 slot row나 exclusion constraint처럼 constraint-first 번역이 가능한지 보고, 그래도 안 되면 guard row queue를 본다.

## 한 줄 정리

예약 동시성 문제를 처음 잡을 때는 "`FOR UPDATE`로 빈 자리를 잠글 수 있나?"보다 "이 규칙을 `UNIQUE`나 constraint로 저장 시점에 거부하게 바꿀 수 있나?"를 먼저 묻는 편이 더 안전하다.
