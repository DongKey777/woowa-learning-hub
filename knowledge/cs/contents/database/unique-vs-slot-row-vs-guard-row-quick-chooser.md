# UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드

> 한 줄 요약: `없으면 insert` 문제는 "어디에서 한 명만 이기게 만들 것인가"를 고르는 일이고, exact key면 `UNIQUE`, 작은 bucket 집합이면 slot row, overlap·capacity·전이 경로까지 함께 다뤄야 하면 guard row가 기본 후보가 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Constraint-First Booking Primer](./constraint-first-booking-primer.md)
- [Guard Row Scope Quick Examples](./guard-row-scope-quick-examples.md)
- [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)
- [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)
- [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md)
- [Hot-Path Slot Arbitration Choices](./hot-path-slot-arbitration-choices.md)
- [database 카테고리 인덱스](./README.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)

retrieval-anchor-keywords: unique vs guard row, slot row primer, insert if absent, insert-if-absent pattern, duplicate insert race, unique constraint chooser, guard row chooser, slot row vs unique, exact key conflict, absence check beginner, 중복 insert 막기, 없으면 insert 어떻게, beginner insert race, unique vs slot row vs guard row quick chooser basics, unique vs slot row vs guard row quick chooser beginner

## 핵심 개념

`SELECT`로 먼저 조회해서 "없네"를 확인한 뒤 `INSERT`하는 흐름은, 동시에 두 요청이 같은 "없음"을 보면 쉽게 중복 생성으로 샌다.

초보자가 먼저 바꿔야 할 질문은 이것이다.

- 같은 요청 둘이 **어디에서 반드시 부딪혀야 하는가**
- 패배한 요청을 `duplicate key`로 빨리 끝낼지, 잠깐 기다렸다가 재검사하게 만들지
- 한 row만 보면 되는지, 여러 slot이나 범위·수량 규칙까지 같이 봐야 하는지

이 기준으로 보면 세 선택지는 이렇게 갈린다.

- `UNIQUE`: 충돌 단위가 이미 **하나의 exact key**다
- slot row: 충돌 단위를 **작은 exact key 집합**으로 펼칠 수 있다
- guard row: 아직 exact key 하나로 못 내리므로 **대표 row lock queue**를 먼저 만든다

## 한눈에 보기

| 선택지 | 충돌 단위 | 패배 요청이 보통 겪는 것 | 잘 맞는 예시 |
|---|---|---|---|
| `UNIQUE` constraint | 하나의 exact key | `duplicate key` 후 기존 row 재조회 | `user_id + coupon_id`, `idempotency_key` |
| slot row | 2~N개의 exact bucket key | slot insert 중 하나에서 `duplicate key` | `room_id + 10:00`, `seat_id + day` |
| guard row | 대표 key 하나 또는 소수의 대표 key | row lock wait 후 overlap/capacity 재검사 | `room_type_id + stay_day`, interval overlap, reschedule/cancel |

핵심 기억법:

- "정확히 같은 것 하나"를 막는 문제면 `UNIQUE`
- "애매한 범위"를 먼저 작은 칸으로 바꿀 수 있으면 slot row
- "칸으로 잘 안 쪼개지거나, 같은 전이 경로를 묶어야" 하면 guard row

## 먼저 이렇게 고른다

1. **같음을 한 key로 바로 쓸 수 있나?**
   예: `idempotency_key`, `email`, `user_id + coupon_id`
   이 질문에 yes면 `UNIQUE`가 1순위다.

2. **범위를 작은 bucket 집합으로 안정적으로 펼칠 수 있나?**
   예: 30분 회의실, 1박 숙박, 좌석-일자 예약
   이 질문에 yes면 slot row가 보통 guard row보다 단순하다.

3. **overlap, capacity, reschedule, expiry 같은 전이 경로를 같이 묶어야 하나?**
   이 질문에 yes면 guard row를 먼저 본다.

여전히 설계가 `SELECT` 후 `INSERT`에 기대고 있다면, 아직 충돌 surface를 제대로 정하지 않은 상태일 가능성이 크다.

## `UNIQUE` constraint가 맞는 경우

`UNIQUE`는 가장 단순한 선택지다.
"같은 의미의 row는 하나만 존재해야 한다"를 exact key로 바로 표현할 수 있을 때 쓴다.

예약 도메인에서 처음 헷갈리면 [Constraint-First Booking Primer](./constraint-first-booking-primer.md)를 먼저 보고 "`FOR UPDATE`보다 먼저 exact key나 slot key로 바꿀 수 있는가"를 확인하는 편이 빠르다.

예:

- 결제 API의 `idempotency_key`
- 사용자별 쿠폰 1회 발급의 `(user_id, coupon_id)`
- 외부 주문 번호의 `external_order_id`

장점:

- DB가 가장 직접적으로 한 명만 winner가 되게 만든다
- 패배 요청을 `duplicate key`로 빠르게 처리할 수 있다
- 설계 설명이 짧고 운영 복구도 쉽다

한계:

- count/sum/capacity 같은 집합 규칙은 보통 혼자 표현하지 못한다
- 시간 구간 overlap처럼 "같음"이 한 key가 아닌 문제에는 바로 쓰기 어렵다
- `없음`을 잠그는 portable range lock 대체재는 아니다

즉 `UNIQUE`는 "한 개의 exact truth key"가 있을 때 가장 좋고, 없는데 억지로 쓰면 설명력이 급격히 떨어진다.

## slot row가 맞는 경우

slot row는 fuzzy한 부재 체크를 "여러 개의 exact key 충돌"로 바꾸는 방법이다.
한 문장으로 줄이면 **한 번의 애매한 insert-if-absent를 여러 번의 정확한 insert-if-absent로 펼치는 방식**이다.

예:

- 회의실 예약을 30분 slot으로 펼친 `room_id + slot_start`
- 1박 숙박을 `room_id + stay_day`로 펼친 active slot claim
- 좌석 예약을 `seat_id + show_slot`으로 고정한 경우

장점:

- `UNIQUE`의 장점을 여러 bucket에 그대로 가져온다
- winner/loser가 어느 slot에서 갈렸는지 설명하기 쉽다
- PostgreSQL/MySQL 모두에서 비교적 portable하다

주의점:

- slot rounding 규칙이 경로마다 다르면 conflict truth가 갈라진다
- 요청 하나가 slot을 많이 만질수록 write 수가 늘어난다
- reschedule은 `old slots + new slots`를 함께 다뤄야 안전하다

즉 slot row는 guard row의 하위 버전이 아니라, **충돌을 작은 exact key들로 내릴 수 있을 때 쓰는 별도 모델**이다.

## guard row가 맞는 경우

guard row는 "진짜 점유 row" 자체라기보다 **충돌 가능한 writer를 먼저 줄 세우는 대표 row**다.

예:

- `room_type_id + stay_day` 재고 guard
- `(resource_id, booking_day)` guard 아래에서 exact overlap 재검사
- cancel, reschedule, expiry cleanup이 같은 inventory를 흔드는 경로

장점:

- overlap, capacity, 전이 경로를 한 protocol로 묶기 쉽다
- slot을 너무 많이 펼치지 않고도 admission surface를 만들 수 있다
- 패배 요청이 같은 queue를 공유하므로 운영 설명이 명확하다

주의점:

- guard row만 있다고 실제 점유 truth가 자동으로 생기지는 않는다
- 모든 write path가 같은 guard protocol을 따라야 한다
- 대표 row 하나에 요청이 몰리면 hot row와 lock wait가 먼저 보인다

즉 guard row는 "`UNIQUE`보다 더 강하다"가 아니라, **exact key 하나로는 문제를 못 닫을 때 queue surface를 따로 만드는 선택지**다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "`SELECT`로 없다고 확인했으니 안전하다" | 동시에 두 요청이 같은 "없음"을 볼 수 있다 | absence check를 write-time 충돌 surface로 바꾼다 |
| "`UNIQUE` 하나면 capacity도 해결된다" | `UNIQUE`는 보통 exact key 중복만 막는다 | count/sum이면 guard row나 별도 counter 모델을 본다 |
| "slot row는 결국 row 수만 많은 `UNIQUE`일 뿐이다" | 맞는 말이 일부 있지만, 시간/bucket 정규화와 delta 전이가 핵심 난점이다 | slot policy와 reschedule contract를 먼저 고정한다 |
| "guard row를 잡았으니 overlap 재검사는 필요 없다" | guard row는 queue surface일 뿐 실제 blocker 계산은 따로 필요할 수 있다 | lock 아래에서 exact overlap 또는 capacity를 다시 확인한다 |

## 실무에서 쓰는 모습

시나리오 1. **중복 결제 요청 방지**
같은 `idempotency_key`는 딱 한 번만 성공해야 한다. 이 경우는 `UNIQUE`가 가장 직선적이다. 중복 요청은 기존 결과를 재사용하면 된다.

시나리오 2. **30분 단위 회의실 예약**
`10:00~11:00` 예약은 `10:00`, `10:30` 두 slot claim으로 펼친다. 경쟁은 각 slot의 `UNIQUE` 충돌에서 난다. 이 경우 slot row가 자연스럽다.

시나리오 3. **숙박 재고 + 연장/취소/만료 처리**
판매 시점에는 `room_type_id + stay_day` 재고를 보고, 나중에는 연장·취소·expiry가 같은 날짜 범위를 흔든다. 이 경우는 guard row로 먼저 줄 세운 뒤 실제 active row를 갱신하는 편이 설명 가능하다.

## 더 깊이 가려면

- interval overlap에서 PostgreSQL exclusion constraint와 slot row만 따로 고르고 싶다면 → [Exclusion Constraint vs Slot Row 빠른 선택 가이드](./exclusion-constraint-vs-slot-row-quick-chooser.md)
- `UNIQUE`와 `upsert` 충돌 비용을 더 보고 싶다면 → [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)
- booking overlap에서 slot row와 guard row를 더 넓게 비교하려면 → [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)
- guard row key를 `resource`, `resource + day`, pooled inventory로 빠르게 구분하려면 → [Guard Row Scope Quick Examples](./guard-row-scope-quick-examples.md)
- guard row 생성 순서와 엔진 차이를 보려면 → [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md)
- high-contention 환경에서 slot row와 guard row의 queue shape 차이를 보려면 → [Hot-Path Slot Arbitration Choices](./hot-path-slot-arbitration-choices.md)
- API replay-safe 설계까지 넓히려면 → [Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)

## 면접/시니어 질문 미리보기

> Q: 왜 `SELECT` 후 `INSERT`가 위험한가요?
> 의도: 부재 기반 판단이 왜 race에 취약한지 설명할 수 있는지 확인
> 핵심: 두 트랜잭션이 같은 "없음"을 동시에 볼 수 있기 때문이다. 그래서 read result가 아니라 write-time 충돌 surface가 필요하다.

> Q: `UNIQUE`와 guard row 중 무엇이 더 강한가요?
> 의도: 도구를 서열로 보지 않고 문제 모양에 맞춰 설명하는지 확인
> 핵심: 더 강한 쪽이 따로 있는 게 아니다. exact key면 `UNIQUE`가 가장 단순하고, exact key로 못 내리는 규칙이면 guard row가 더 맞다.

> Q: slot row는 언제 guard row보다 좋은가요?
> 의도: discrete bucket 모델의 장단점을 아는지 확인
> 핵심: 시간/재고를 작은 exact key 집합으로 안정적으로 펼칠 수 있을 때다. 이 경우 duplicate key 기반 설명이 lock queue보다 더 단순해진다.

## 한 줄 정리

`없으면 insert` 경로에서 먼저 고를 것은 락 문법이 아니라 충돌 surface다. exact key면 `UNIQUE`, 작은 bucket 집합이면 slot row, overlap·capacity·전이 경로까지 함께 묶어야 하면 guard row가 기본 선택지다.
