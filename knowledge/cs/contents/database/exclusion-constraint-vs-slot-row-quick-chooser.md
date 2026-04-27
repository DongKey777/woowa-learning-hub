# Exclusion Constraint vs Slot Row 빠른 선택 가이드

> 한 줄 요약: interval overlap 문제는 exact-key 중복 방지와 다르고, PostgreSQL exclusion constraint는 "겹치는 구간 자체"를 막고 slot row는 "겹침을 여러 exact slot 충돌"로 바꿔 막는다.

**난이도: 🟢 Beginner**

관련 문서:

- [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- [Slot Row 도입 전 주니어 체크리스트: Rounding, Half-Open Interval, DST](./slot-row-rounding-half-open-dst-junior-checklist.md)
- [MySQL Overlap Fallback Beginner Bridge](./mysql-overlap-fallback-beginner-bridge.md)
- [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)
- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md)
- [Inventory Reservation System Design](../system-design/inventory-reservation-system-design.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: exclusion constraint vs slot row, exact key vs interval overlap, booking overlap beginner, postgresql overlap chooser, slot row chooser, continuous interval vs discrete slot, overlap not duplicate key, booking overlap exact key 아님, continuous time truth, discrete time truth, exclusion constraint intro, slotization basics, reservation overlap what to use, double booking prevention beginner, stay day slot row, arbitrary duration overlap

MySQL에서 `SELECT ... FOR UPDATE`가 PostgreSQL exclusion constraint의 direct substitute인지부터 헷갈리면 [MySQL Overlap Fallback Beginner Bridge](./mysql-overlap-fallback-beginner-bridge.md)를 먼저 보고 오는 편이 좋다.

## 핵심 개념

interval overlap 문제는 exact key 중복 방지와 질문이 다르다.

- exact key 중복 방지: "같은 키가 두 번 들어오나?"
- interval overlap 방지: "같은 자원에서 시간 구간이 겹치나?"

예를 들어 아래 둘은 완전히 다른 문제다.

- `UNIQUE(order_id)`는 같은 주문 번호 재삽입을 막는다
- `UNIQUE(room_id, start_at, end_at)`는 exact same interval만 막고 `10:00~11:00`와 `10:30~11:30`의 겹침은 못 막는다

그래서 초보자가 먼저 고를 것은 락 문법이 아니라 **점유 truth를 어디에 둘지**다.

- exclusion constraint: booking row 자체가 truth다
- slot row: slot claim row 집합이 truth다

기억법은 더 단순하게 가져가면 된다.

- 시간이 "선"처럼 연속 구간이면 exclusion constraint
- 시간이 "칸"처럼 이미 잘린 규칙이면 slot row

## 30초 선택 플로우

1. 지금 문제가 exact-key dedup인지, interval overlap인지 먼저 가른다.
2. overlap이라면 시간 truth가 continuous인지 discrete인지 고른다.
3. continuous면 exclusion constraint, discrete면 slot row를 1차 후보로 둔다.

| 질문 | 예 | 1차 후보 |
|---|---|---|
| 시간이 임의 길이인가? | `10:07~11:43` | exclusion constraint |
| 시간이 이미 고정 칸인가? | 30분 단위, 1박 단위 | slot row |
| 엔진을 PostgreSQL+MySQL 둘 다 맞춰야 하나? | 공통 모델 필요 | slot row 우선 검토 |

## 한눈에 보기

먼저 exact-key dedup과 interval overlap을 분리한다.

| 먼저 구분할 문제 | 질문 | 기본 후보 |
|---|---|---|
| exact-key dedup | "같은 키가 두 번 들어오나?" | `UNIQUE`, idempotency key |
| interval overlap | "다른 시작/종료라도 시간이 겹치나?" | exclusion constraint 또는 slot row |

| 질문 | exclusion constraint | slot row |
|---|---|---|
| 충돌 surface | 같은 booking table의 equality + range overlap | `(resource_id, slot_start)` 같은 exact slot key들 |
| 시간 모델 | continuous interval에 자연스럽다 | discrete bucket에 자연스럽다 |
| 엔진 적합성 | PostgreSQL 쪽이 가장 직접적이다 | PostgreSQL/MySQL 모두 설명하기 쉽다 |
| 패배 요청이 겪는 것 | `23P01` 같은 overlap conflict | slot insert 중 `duplicate key` |
| 잘 맞는 상황 | arbitrary duration, single-table active booking | 30분 회의실, 1박 숙박, day-slot inventory |
| exact-key chooser와 다른 점 | 구간 자체가 blocker다 | slot 여러 개 중 하나만 부딪혀도 blocker다 |
| 먼저 조심할 것 | active predicate, `[start, end)`, legacy overlap 정리 | rounding, DST, reschedule delta, slot fan-out |

핵심 차이는 "무엇이 더 강한가"가 아니다.
continuous truth를 그대로 둘지, discrete truth로 바꿀지의 차이다.

## 같은 요청을 두 모델로 보면

요청: "회의실 A, 10:30~11:30 예약"

- exclusion constraint 모델: booking row 1개를 넣고, 겹치는 구간이면 DB가 `23P01`로 거부
- slot row 모델: `10:30`, `11:00` slot claim 2개를 넣고, 한 칸이라도 `duplicate key`면 거부

둘 다 "겹침 거부"는 같지만, 충돌이 표현되는 단위가 다르다.

- exclusion constraint: 구간 자체 충돌
- slot row: slot key 충돌의 합

## exact-key와 다른 이유

먼저 "`UNIQUE(start, end)`면 되지 않나?"를 버린다.

exact-key dedup은 "같으면 충돌"이고, overlap은 "겹치면 충돌"이다.

- `09:00~10:00` 와 `09:00~10:00`는 exact key도 겹침도 둘 다 충돌한다
- `09:00~10:00` 와 `09:30~10:30`는 exact key는 다르지만 겹침은 충돌한다

즉 interval overlap에서는 같은 key를 찾는 게 아니라,
**겹치는 시간대를 어떻게 DB가 중재하게 만들지**를 정해야 한다.

## 상세 분해

### 1. exclusion constraint를 먼저 볼 때

다음 조건이 맞으면 exclusion constraint가 가장 직선적이다.

- PostgreSQL을 쓴다
- 예약 길이가 제각각이라 slot으로 자르는 편이 더 부자연스럽다
- conflict truth가 한 table 안에서 닫힌다

예를 들어 회의실 예약 시간이 `10:07~11:43`처럼 임의 길이라면, 구간 자체를 `tstzrange(start_at, end_at, '[)')`로 두는 편이 자연스럽다.

초보자 기준 핵심은 이거다.

- booking row 하나가 곧 점유 truth다
- DB가 "겹치는 구간 자체"를 바로 거부한다
- 패배 요청은 overlap conflict로 끝난다

### 2. slot row를 먼저 볼 때

다음 조건이 맞으면 slot row가 더 단순하다.

- business time resolution이 이미 15분, 30분, 1일처럼 고정돼 있다
- PostgreSQL 말고도 같은 모델을 쓰고 싶다
- 어떤 slot에서 졌는지를 운영에서 바로 설명하고 싶다

예를 들어 30분 회의실 예약은 `10:00`, `10:30` slot claim으로 펼칠 수 있고, 충돌은 각 slot key의 `UNIQUE`가 맡는다.

초보자 기준 핵심은 이거다.

- overlap을 "여러 exact key 충돌"로 번역한다
- slot claim row가 실제 blocker truth가 된다
- 패배 요청은 특정 slot의 duplicate key로 끝난다

slot row를 처음 도입하는 팀이라면, DDL보다 먼저 `[start, end)`, rounding, timezone/DST 체크를 짧게 맞춰 두는 편이 안전하다.
이 준비를 빠르게 훑고 싶으면 [Slot Row 도입 전 주니어 체크리스트: Rounding, Half-Open Interval, DST](./slot-row-rounding-half-open-dst-junior-checklist.md)를 먼저 보면 된다.

### 3. 같은 예약 도메인이라도 truth가 다르면 답이 달라진다

같은 "예약"이어도 항상 같은 답이 나오지 않는다.

- 스튜디오 예약이 `10:07~11:43`처럼 임의 길이면 exclusion constraint가 더 직접적이다
- 숙박 판매 truth가 `stay_day`면 slot row가 더 직접적이다
- 회의실이 30분 단위 정책이면 slot row가 운영 설명이 쉽다
- 객실 청소 buffer까지 room-level continuous block으로 관리하면 exclusion constraint가 더 자연스럽다

즉 exclusion constraint가 slot row보다 더 강한 것도, slot row가 더 실용적이라서 항상 이기는 것도 아니다.

- continuous interval이 truth면 exclusion constraint가 더 직접적이다
- discrete slot이 truth면 slot row가 더 직접적이다

capacity가 2 이상이거나 later assignment, pooled inventory까지 함께 다뤄야 하면 둘만으로는 설명이 부족할 수 있다. 그런 경우는 guard row나 ledger 쪽으로 넘어간다.

## 흔한 오해와 함정

- "`UNIQUE(resource_id, start_at, end_at)`면 overlap도 막힌다"
  - 아니다. exact same interval만 막고, 일부만 겹치는 구간은 못 막는다.
- "`UNIQUE`처럼 exact key가 아니니 exclusion constraint가 무조건 맞다"
  - 아니다. 이미 discrete slot policy가 있으면 slot row가 더 단순하다.
- "PostgreSQL이면 항상 exclusion constraint가 정답이다"
  - 아니다. 판매 truth가 `stay_day`나 30분 slot이면 slot row가 더 설명 가능하다.
- "slot row는 exclusion constraint를 못 써서 만드는 우회다"
  - 아니다. slot row는 conflict truth를 discrete key로 바꾸는 독립 모델이다.
- "exclusion constraint면 capacity 초과도 같이 해결된다"
  - 아니다. exclusion constraint는 보통 pairwise overlap에 강하다.
- "slot row로 바꾸면 경계 문제가 사라진다"
  - 아니다. rounding, timezone, DST, reschedule 규칙이 오히려 더 중요해진다.

## 실무에서 쓰는 모습

시나리오 1. **PostgreSQL에서 임의 길이 스튜디오 예약**

```sql
EXCLUDE USING gist (
  studio_id WITH =,
  tstzrange(start_at, end_at, '[)') WITH &&
)
```

예약 시간이 계속 달라지고 continuous interval 자체가 truth라면 이 방식이 가장 짧다.

시나리오 2. **30분 단위 회의실 예약**

```sql
CREATE TABLE room_slot_claim (
  room_id BIGINT NOT NULL,
  slot_start TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (room_id, slot_start)
);
```

시간이 이미 slot으로 굳어 있으면, overlap을 slot claim의 exact key 충돌로 설명하는 편이 더 쉽다.

시나리오 3. **1박 단위 숙박 재고**

숙박은 겉으로는 interval이지만 실제 판매 truth가 `stay_day`면 slot row가 자연스럽다. 반대로 체크인/체크아웃 시간이 자주 바뀌고 청소 buffer까지 continuous하게 관리해야 하면 exclusion constraint가 더 잘 맞을 수 있다.

즉 도메인 이름이 아니라 "무엇을 blocker로 삼는가"가 선택 기준이다.

## 다음 단계 라우팅

- exact-key duplicate와 overlap을 먼저 분리하고 싶으면 -> [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- exclusion constraint의 active predicate/경계값/에러 대응을 깊게 보려면 -> [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- 엔진별 fallback까지 같이 판단하려면 -> [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- slot row 이후 reschedule/cancel 전이를 설계하려면 -> [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md)

## 더 깊이 가려면

- overlap 전체 패턴 지형도를 먼저 보려면 -> [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)
- capacity/hold/release를 시스템 설계 관점으로 넓히려면 -> [Inventory Reservation System Design](../system-design/inventory-reservation-system-design.md)

## 면접/시니어 질문 미리보기

> Q: overlap 문제에서 exclusion constraint와 slot row 중 먼저 무엇을 고르나요?
> 의도: 시간 truth를 continuous/discrete로 먼저 나누는지 확인
> 핵심: continuous interval이 truth면 exclusion constraint, discrete bucket이 truth면 slot row를 먼저 본다.

> Q: slot row는 exclusion constraint보다 약한가요?
> 의도: 도구를 서열이 아니라 모델 차이로 설명하는지 확인
> 핵심: 약하고 강함의 문제가 아니라, interval을 그대로 둘지 slot 집합으로 바꿀지의 차이다.

> Q: exclusion constraint를 쓰면 어떤 준비가 먼저 필요하나요?
> 의도: 문법보다 active predicate와 레거시 데이터 정리를 먼저 떠올리는지 확인
> 핵심: `[start, end)` 경계, active status, 기존 overlap pair 정리가 먼저다.

## 한 줄 정리

interval overlap에서는 "PostgreSQL 기능이 있나"보다 먼저 시간 truth가 continuous인지 discrete인지부터 고른다. continuous면 exclusion constraint, discrete면 slot row가 보통 더 자연스럽다.
