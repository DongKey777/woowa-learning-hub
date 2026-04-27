# MySQL Overlap Fallback Beginner Bridge

> 한 줄 요약: MySQL의 `SELECT ... FOR UPDATE`는 PostgreSQL exclusion constraint처럼 "겹치는 시간 구간 자체"를 직접 막아 주는 도구가 아니라, 잘해야 특정 인덱스 scan 경로를 잠그는 보조 수단이다. 그래서 junior 단계에서는 "locking read로 버틸까?"보다 "slot row로 내릴까, guard row로 줄 세울까?"를 먼저 고르는 편이 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [Exclusion Constraint vs Slot Row 빠른 선택 가이드](./exclusion-constraint-vs-slot-row-quick-chooser.md)
- [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [MySQL Empty-Result Locking Reads](./mysql-empty-result-locking-reads.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: mysql overlap fallback beginner, mysql locking read overlap beginner, mysql select for update overlap not exclusion constraint, mysql overlap not direct substitute, postgresql exclusion constraint vs mysql locking read, when to use slot row, when to use guard row, mysql booking overlap primer, beginner booking overlap mysql, slot row vs guard row mysql, select for update overlap pitfall, mysql overlap fallback bridge, mysql double booking beginner, overlap query for update beginner, room_id start_at index beginner

## 핵심 개념

먼저 이 그림으로 잡으면 된다.

- PostgreSQL exclusion constraint: "겹치는 구간이면 저장 자체를 거부"
- MySQL locking read: "내가 이번에 훑은 인덱스 길목을 잠글 수도 있음"

즉 둘은 이름만 다른 같은 도구가 아니다.

- exclusion constraint는 **겹침 규칙 자체**에 가깝다
- MySQL locking read는 **스캔 경로 기반 락 도구**에 가깝다

초보자에게 중요한 결론은 단순하다.

- PostgreSQL에서는 continuous overlap을 제약으로 직접 닫기 쉽다
- MySQL에서는 같은 문제를 slot row나 guard row 같은 **다른 충돌 surface**로 바꾸는 편이 더 예측 가능하다

## 왜 direct substitute가 아닌가

흔히 이렇게 생각한다.

```sql
SELECT id
FROM booking
WHERE room_id = :room_id
  AND start_at < :requested_end
  AND end_at > :requested_start
FOR UPDATE;
```

결과가 `0 row`면 "이제 이 시간대는 잠겼다"라고 느끼기 쉽다.
하지만 MySQL은 보통 **겹침 조건 자체**를 잠그지 않는다.

MySQL이 실제로 보는 것은 대개 이런 쪽이다.

- 어떤 인덱스를 탔는가
- 어느 range를 스캔했는가
- 현재 격리가 `REPEATABLE READ`인가 `READ COMMITTED`인가
- 다른 writer도 같은 probe 경로를 꼭 타는가

그래서 같은 business rule이라도 다음에 따라 잠금 결과가 달라질 수 있다.

- `(room_id, start_at)` 인덱스를 탄 경우
- `(room_id, end_at)` 인덱스를 탄 경우
- optimizer가 다른 경로를 고른 경우
- `READ COMMITTED`에서 gap 보호가 약해진 경우

핵심은 이것이다.

- PostgreSQL exclusion constraint: "겹침이면 안 됨"을 DB에 바로 적는다
- MySQL locking read: "이번 scan 경로에 새 row가 끼어들지 못하게 할 수도 있음"에 가깝다

즉 MySQL locking read는 overlap 규칙을 직접 표현한 것이 아니라,
**어떤 storage path를 먼저 밟았는지에 기대는 방식**이다.

## 왜 `(room_id, start_at)`와 `(room_id, end_at)`가 다르게 느껴지나

초보자는 "둘 다 room_id가 같고 시간 컬럼도 들어가니 비슷하겠지"라고 생각하기 쉽다.
하지만 B-tree는 한 번에 한 축을 먼저 훑는다.

- `(room_id, start_at)`: "이 방에서 시작 시간이 요청 종료보다 이른 row" 쪽을 먼저 훑는다
- `(room_id, end_at)`: "이 방에서 종료 시간이 요청 시작보다 늦은 row" 쪽을 먼저 훑는다

예를 들어 요청이 `10:00~11:00`이면 mental model은 이렇게 잡으면 된다.

| 인덱스 | 먼저 넓게 보는 쪽 | 초보자 기억법 | 보호하려는 lock surface |
|---|---|---|---|
| `(room_id, start_at)` | `11:00`보다 먼저 시작한 row들 | "왼쪽 경계보다 과거를 많이 훑는다" | 과거에서 현재로 끼어드는 시작 시각 쪽 길목 |
| `(room_id, end_at)` | `10:00`보다 늦게 끝나는 row들 | "오른쪽 경계보다 미래를 많이 훑는다" | 현재에서 미래로 이어지는 종료 시각 쪽 길목 |

즉 둘 다 "겹치는 구간 전체"를 잠그는 것이 아니라,
각자 **다른 문 앞에서 대기열을 세우는 것**에 가깝다.

- `(room_id, start_at)`는 이미 오래전에 시작한 row까지 같이 보기 쉽다
- `(room_id, end_at)`는 아직 한참 뒤에 끝나는 row까지 같이 보기 쉽다
- 그래서 같은 overlap SQL이어도 무엇을 많이 건드리는지가 달라진다

한 줄로 줄이면 이렇다.

- `(room_id, start_at)`는 start 쪽 길목을 지키는 느낌
- `(room_id, end_at)`는 end 쪽 길목을 지키는 느낌
- 둘을 같이 만들어도 MySQL이 한 번에 둘 다 합쳐 "겹침 구간 전체"를 잠그는 것은 아니다

이 차이를 더 기술적으로 보고 싶다면
[Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md)를 이어서 보면 된다.

## 한눈에 비교

| 질문 | PostgreSQL exclusion constraint | MySQL locking read |
|---|---|---|
| DB가 직접 아는 것 | 겹치는 구간 자체 | 스캔한 인덱스 경로와 잠금 범위 |
| 초보자 mental model | "겹치면 저장 실패" | "이 길목으로 들어오는 경쟁을 줄일 수 있음" |
| plan/index 변화에 민감한가 | 상대적으로 덜 민감 | 더 민감하다 |
| `0 row`의 의미 | 충돌 row 없음 | 부재 전체가 잠겼다는 뜻이 아님 |
| beginner 기본 판단 | overlap 제약 도구 | 보조 락 도구 |

## 그래서 언제 locking read에서 내려와야 하나

다음 신호가 보이면 "base booking table에서 overlap query + `FOR UPDATE`"를 기본 해법으로 두지 않는 편이 좋다.

### 1. 시간이 discrete bucket으로 이미 잘린다

예:

- 15분 단위 회의실
- 30분 단위 장비 대여
- 1박 단위 숙박

이때는 slot row가 더 단순하다.

- `room_id + slot_start`
- `device_id + slot_start`
- `room_id + stay_day`

처럼 exact key로 바꿀 수 있기 때문이다.

기억법:

- "칸으로 이미 운영하는 시간"이면 slot row
- "선처럼 연속 시간"이면 다른 후보를 본다

### 2. 연속 구간인데 MySQL에서도 예측 가능한 동작이 필요하다

예:

- `10:07~11:43` 같은 임의 길이 예약
- 청소 buffer까지 포함한 blocked range
- 상태 predicate가 `HELD`, `CONFIRMED`, `BLACKOUT`처럼 섞이는 경우

이때는 guard row를 먼저 검토한다.

이유:

- overlap 판단을 하기 전에 같은 자원 요청을 한 queue로 모을 수 있다
- locking read의 scan-path 우연성보다 protocol이 더 분명하다
- 취소, 연장, admin override 같은 여러 write path를 같은 순서로 묶기 쉽다

### 3. capacity나 later assignment까지 같이 다뤄야 한다

예:

- 같은 room type 재고를 여러 객실이 공유
- 판매 시점에는 room_id가 아직 없음
- 좌석/재고가 1개가 아니라 여러 개

이 경우는 처음부터 guard row 쪽이 더 자연스럽다.

이유:

- pairwise overlap만 막는다고 capacity 규칙이 자동으로 닫히지 않는다
- "누가 먼저 들어오나"보다 "같은 재고를 건드리는 요청을 어디서 줄 세우나"가 더 중요하다

## slot row로 가는 기준

slot row는 overlap을 "여러 exact key 충돌"로 바꾸는 방식이다.

이럴 때 1차 후보로 둔다.

| 상황 | 왜 slot row가 잘 맞는가 |
|---|---|
| 시간이 이미 15분/30분/1일 단위다 | business truth가 slot 집합이기 때문이다 |
| PostgreSQL/MySQL 공통 모델이 필요하다 | 엔진별 락 차이보다 `UNIQUE` 충돌로 설명 가능하다 |
| 패배 요청을 빠르게 끝내고 싶다 | slot insert 중 `duplicate key`로 바로 떨어질 수 있다 |

짧은 예:

- 예약 `10:00~11:00`
- 30분 slot 정책
- 실제 충돌 surface: `10:00`, `10:30` 두 slot key

즉 junior 기준으로는 "overlap 쿼리를 잘 잠그는 법"보다
**겹침을 exact key 여러 개로 바꿀 수 있나**를 먼저 보면 된다.

## guard row로 가는 기준

guard row는 overlap truth를 직접 저장하기보다,
**충돌 가능한 writer를 같은 잠금 queue로 보내는 방식**이다.

이럴 때 1차 후보로 둔다.

| 상황 | 왜 guard row가 잘 맞는가 |
|---|---|
| continuous interval이라 slot fan-out이 어색하다 | 대표 key 하나를 먼저 잠그고 재검사할 수 있다 |
| booking, hold, blackout, cleanup 경로가 많다 | 모든 write path를 같은 protocol로 맞추기 쉽다 |
| capacity, later assignment, multi-day reschedule이 있다 | overlap 밖의 전이 규칙까지 함께 묶기 쉽다 |

짧은 예:

- `room_guard(room_id, booking_day)`를 먼저 `FOR UPDATE`
- lock 아래에서 exact overlap를 다시 검사
- 검사 후 booking insert/update

이 패턴의 핵심은 "겹침 SQL이 특별해서 안전하다"가 아니라,
"같은 자원 요청이 먼저 같은 문을 통과한다"는 점이다.

## 초보자가 자주 헷갈리는 포인트

- "`FOR UPDATE`면 exclusion constraint 비슷한 거 아닌가요?"
  - 아니다. exclusion constraint는 겹침 규칙을 직접 적는 것이고, MySQL locking read는 scan path에 의존한다.
- "`0 row`면 그 시간대가 잠긴 거 아닌가요?"
  - 아니다. 부재 전체를 잠갔다고 읽으면 과대평가다.
- "MySQL도 인덱스만 잘 만들면 같은 효과 아닌가요?"
  - 일부 narrow case는 버틸 수 있어도, overlap 전체를 direct substitute처럼 설명하면 위험하다.
- "slot row는 exclusion constraint가 없어서 만드는 우회인가요?"
  - 아니다. discrete time truth를 exact key로 바꾸는 독립 모델이다.
- "guard row는 성능이 느리니까 마지막 수단인가요?"
  - 아니다. 여러 write path를 같은 protocol로 묶어야 하면 오히려 가장 설명 가능한 기본기일 수 있다.

## 30초 선택표

| 질문 | 먼저 볼 선택지 |
|---|---|
| 시간이 이미 slot/day 단위로 굳어 있나 | slot row |
| 시간이 임의 길이이고 MySQL에서 운영해야 하나 | guard row |
| capacity, later assignment, admin override까지 같이 있나 | guard row |
| PostgreSQL 단일 active booking table에서 continuous overlap인가 | exclusion constraint |

## 추천 학습 순서

1. "겹침 쿼리를 잠글 수 있나"보다 "충돌 surface가 뭔가"를 먼저 잡는다.
2. discrete time이면 slot row를 먼저 검토한다.
3. continuous time + 복잡한 write path면 guard row를 먼저 검토한다.
4. MySQL locking read는 주력 모델이 아니라 보조 락 도구로 이해한다.

## 다음 단계 라우팅

- PostgreSQL exclusion constraint와 slot row를 먼저 비교하고 싶다면 -> [Exclusion Constraint vs Slot Row 빠른 선택 가이드](./exclusion-constraint-vs-slot-row-quick-chooser.md)
- `UNIQUE`, slot row, guard row 전체 선택지를 beginner 기준으로 보고 싶다면 -> [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- MySQL locking read의 empty-result/gap lock 디테일을 더 보고 싶다면 -> [MySQL Empty-Result Locking Reads](./mysql-empty-result-locking-reads.md)
- continuous interval fallback을 더 깊게 보고 싶다면 -> [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- guard row scope를 day/resource 기준으로 더 구체화하려면 -> [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)

## 한 줄 정리

MySQL locking read는 PostgreSQL exclusion constraint의 직역판이 아니다. junior 기준으로는 "겹침 조회를 어떻게 잠글까"보다 "slot row로 exact key 충돌로 내릴까, guard row로 같은 자원 요청을 줄 세울까"를 먼저 고르는 편이 더 안전하다.
