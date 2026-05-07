---
schema_version: 3
title: Guard Row Scope Quick Examples
concept_id: database/guard-row-scope-quick-examples
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- guard-row-scope-examples
- resource-vs-resource-day-guard
- pooled-inventory-guard
aliases:
- guard row scope quick examples
- resource guard row
- resource day guard row
- pooled inventory guard row
- room booking guard key
- room_type_day guard beginner
- guard key scope primer
- resource vs resource day
- pooled inventory booking example
- guard row scope intro
symptoms:
- guard row를 어느 table에 저장하느냐보다 서로 부딪혀야 할 요청이 어떤 key에서 만나야 하는지 헷갈려
- resource guard, resource+day guard, pooled inventory guard의 차이를 예시로 보고 싶어
- 예약 domain에서 guard key scope를 너무 넓거나 좁게 잡을까 걱정돼
intents:
- definition
- design
prerequisites:
- database/unique-vs-slot-row-vs-guard-row-quick-chooser
- database/guard-row-booking-timeline-card
next_docs:
- database/guard-row-scope-design-multi-day-bookings
- database/shared-pool-guard-design-room-type-inventory
- database/phantom-safe-booking-patterns-primer
linked_paths:
- contents/database/unique-vs-slot-row-vs-guard-row-quick-chooser.md
- contents/database/phantom-safe-booking-patterns-primer.md
- contents/database/guard-row-scope-design-multi-day-bookings.md
- contents/database/shared-pool-guard-design-room-type-inventory.md
- contents/database/guard-row-booking-timeline-card.md
confusable_with:
- database/guard-row-scope-design-multi-day-bookings
- database/unique-vs-slot-row-vs-guard-row-quick-chooser
- database/shared-pool-guard-design-room-type-inventory
forbidden_neighbors: []
expected_queries:
- guard row scope를 resource, resource+day, pooled inventory로 예시 들어 설명해줘
- 같은 room이라도 날짜가 안 겹치면 resource-day guard row가 왜 더 낫나?
- pooled inventory guard row는 개별 room assignment가 나중에 붙는 예약에서 언제 써?
- guard key는 실제 예약 row가 아니라 경쟁 요청이 만나는 대표 key라는 뜻이야?
- guard row scope를 초보자에게 숙박 예약 예시로 설명해줘
contextual_chunk_prefix: |
  이 문서는 guard row scope를 resource, resource+day, pooled inventory 세 예시로 설명해 서로 충돌해야 하는 요청이 어떤 대표 key에서 만나는지 잡아 주는 beginner primer다.
  guard row scope quick examples, resource day guard row, pooled inventory guard row 같은 자연어 질문이 본 문서에 매핑된다.
---
# Guard Row Scope Quick Examples

> 한 줄 요약: guard row의 핵심은 "예약 row를 어디에 저장하느냐"보다 "서로 부딪혀야 할 요청이 어떤 대표 key에서 만나게 하느냐"이며, 초보자 기준으로는 `resource`, `resource + day`, pooled inventory 세 가지를 먼저 구분하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Shared-Pool Guard Design for Room-Type Inventory](./shared-pool-guard-design-room-type-inventory.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: guard row scope quick examples, resource guard row, resource day guard row, pooled inventory guard row, room booking guard key, room_type_day guard beginner, guard row booking examples, guard key scope primer, resource vs resource day, pooled inventory booking example, beginner booking guard row, primary key guard examples, guard row scope quick examples basics, guard row scope quick examples beginner, guard row scope quick examples intro

## 먼저 잡을 그림

guard row는 "실제 예약 데이터"라기보다 **경쟁하는 요청을 먼저 줄 세우는 대표 key**다.

초보자는 먼저 이 질문 하나로 시작하면 된다.

- "내 시스템에서 서로 부딪혀야 하는 예약 둘이 어떤 key를 반드시 공유해야 하는가?"

이 질문에 대한 흔한 답 세 가지가 아래다.

| guard key | 뜻 | 주로 쓰는 상황 |
|---|---|---|
| `resource` | 리소스 하나에 예약 시도를 모두 모은다 | 개별 장비, 개별 회의실처럼 리소스 수는 적고 예약량도 많지 않을 때 |
| `resource + day` | 같은 리소스라도 같은 날짜일 때만 먼저 부딪히게 한다 | 숙박 1박 단위, 일 단위 재고, multi-day booking |
| pooled inventory | 개별 리소스가 아니라 같은 풀의 수량을 본다 | `room_type`, 좌석 등급, 공용 재고처럼 나중에 실제 개체를 붙이는 경우 |

## 1. `resource` guard

가장 단순한 형태다.

```text
guard key = (room_id)
예: room_id = 101
```

### 어떤 느낌인가

- 101호와 관련된 예약 요청은 모두 같은 guard row에서 줄을 선다
- 날짜가 달라도 일단 같은 `room_id`면 한 줄로 모인다

### 예약 예시

- 기존 예약: `101호`, `5월 1일~5월 2일`
- 새 요청 A: `101호`, `5월 10일~5월 11일`
- 새 요청 B: `101호`, `5월 1일~5월 3일`

이 모델에서는 A와 B가 둘 다 `(101)` guard를 먼저 잡으려 한다.

- B는 실제 날짜가 겹치므로 당연히 같은 줄에 서야 한다
- A는 날짜가 안 겹치지만, 그래도 같은 줄에 선다

즉 `resource` guard는 **안전하지만 범위가 넓다**.

### 잘 맞는 경우

- 예약량이 높지 않다
- "일단 같은 리소스면 한 번씩만 처리하자"가 운영상 충분하다
- 구현을 가장 단순하게 시작하고 싶다

### 초보자 메모

- 장점: 설계 설명이 쉽다
- 단점: 안 겹치는 예약도 같이 기다릴 수 있다

## 2. `resource + day` guard

숙박처럼 "하루"가 중요한 도메인에서 많이 쓴다.

```text
guard key = (room_id, stay_day)
예: (101, 2026-05-01), (101, 2026-05-02)
```

### 어떤 느낌인가

예약 하나가 guard row 하나를 잡는 게 아니라, **머무는 날짜 수만큼 여러 key를 잡는다**.

- `5월 1일~5월 3일` 예약
- half-open으로 보면 `5월 1일 밤`, `5월 2일 밤`
- guard key는 `(101, 5월 1일)`, `(101, 5월 2일)`

### 예약 예시

기존 예약:

- `101호`, `5월 1일 체크인 ~ 5월 3일 체크아웃`

새 요청 A:

- `101호`, `5월 3일 체크인 ~ 5월 4일 체크아웃`

새 요청 B:

- `101호`, `5월 2일 체크인 ~ 5월 4일 체크아웃`

guard key를 펼치면:

| 예약 | guard key |
|---|---|
| 기존 예약 | `(101, 5월 1일)`, `(101, 5월 2일)` |
| 새 요청 A | `(101, 5월 3일)` |
| 새 요청 B | `(101, 5월 2일)`, `(101, 5월 3일)` |

해석:

- A는 기존 예약과 guard key를 공유하지 않는다
- B는 `(101, 5월 2일)`를 공유하므로 같은 줄에서 경쟁한다

즉 `resource + day`는 **겹치는 날짜만 경쟁하게 좁혀 준다**.

### 잘 맞는 경우

- 1박 단위 숙박처럼 날짜가 자연 단위다
- 날짜가 안 겹치면 동시에 처리하고 싶다
- 예약 길이가 아주 길지는 않다

### 초보자 메모

- 장점: `resource`보다 덜 막는다
- 단점: 예약 하나가 여러 key를 잡으므로 순서 규칙이 중요하다

자주 헷갈리는 점:

- `5월 1일~5월 3일`은 보통 `5월 1일`, `5월 2일` 두 밤이다
- 그래서 체크아웃 날인 `5월 3일`은 점유 day에 포함하지 않는 half-open 규칙을 먼저 고정해야 한다

## 3. pooled inventory guard

여기서는 개별 방 번호보다 **같은 풀의 남은 수량**이 먼저 중요하다.

```text
guard key = (property_id, room_type_id, stay_day)
예: (hotel-A, deluxe, 2026-05-01)
```

### 어떤 느낌인가

- 아직 `101호`를 줄지 `102호`를 줄지 정하지 않는다
- 대신 "디럭스룸이 그날 몇 개 남았는가"를 먼저 본다

### 예약 예시

상황:

- 디럭스룸 총 3개
- `5월 1일` 현재 이미 2개 판매됨

새 요청 A:

- 디럭스룸 1개, `5월 1일~5월 2일`

새 요청 B:

- 디럭스룸 1개, `5월 1일~5월 2일`

두 요청은 둘 다 `(hotel-A, deluxe, 5월 1일)` guard에서 만난다.

- A가 먼저 들어와 3개 중 마지막 1개를 잡으면
- B는 같은 day guard를 본 뒤 "그날은 full"로 실패한다

여기서는 `101호`, `102호` 같은 개별 방 key를 바로 쓰지 않아도 된다.
핵심은 **같은 room type의 그날 총량**을 먼저 맞추는 것이다.

### 잘 맞는 경우

- 같은 타입 방들이 서로 대체 가능하다
- 판매 시점에는 개별 방 배정보다 총량 관리가 더 중요하다
- 실제 방 배정은 나중 단계에서 한다

### 초보자 메모

- 장점: 공용 재고 판매 모델과 잘 맞는다
- 단점: 나중에 실제 `room_id` 배정을 별도로 풀어야 할 수 있다

즉 pooled inventory guard는 "개별 리소스 중복"보다 **공용 수량 초과 판매 방지**가 중심인 모델이다.

## 세 가지를 한 번에 비교

| 질문 | `resource` | `resource + day` | pooled inventory |
|---|---|---|---|
| 대표 key 예시 | `(room_id)` | `(room_id, stay_day)` | `(property_id, room_type_id, stay_day)` |
| 먼저 막는 것 | 같은 리소스 전체 경쟁 | 같은 리소스의 같은 날짜 경쟁 | 같은 풀의 같은 날짜 총량 경쟁 |
| 예약 하나가 잡는 key 수 | 보통 1개 | 날짜 수만큼 여러 개 | 날짜 수만큼 여러 개 |
| 초보자에게 보이는 장점 | 가장 단순함 | 덜 과하게 직렬화함 | room-type/day 재고 설명이 쉬움 |
| 가장 흔한 함정 | 안 겹치는 예약도 같이 막음 | day 계산, 정렬 순서 | 개별 방 배정 문제를 따로 풀어야 함 |

## 어떤 걸 먼저 고를까

아주 간단히 고르면 이 순서다.

1. 같은 개별 리소스만 안전하게 막으면 되면 `resource`
2. 날짜가 핵심이고 날짜 안 겹치면 동시에 처리하고 싶으면 `resource + day`
3. 개별 리소스보다 공용 재고 수량이 먼저 중요하면 pooled inventory

초보자 기준에서는 "더 고급 패턴"을 찾기보다,
**실제로 충돌해야 하는 두 예약이 같은 guard key를 공유하는지**를 먼저 확인하는 편이 훨씬 중요하다.

## 자주 하는 오해

- "`resource + day`면 실제 예약 row도 날짜별로 쪼개야 하나요?"
  - 꼭 그렇지는 않다. guard row는 경쟁을 줄 세우는 key이고, 실제 booking row 저장 방식은 별개일 수 있다.
- "pooled inventory면 개별 방 중복 배정 문제는 끝났나요?"
  - 아니다. pooled inventory guard는 총량을 맞추는 1차 장치이고, 실제 `room_id` 배정은 나중에 별도 invariant가 될 수 있다.
- "`resource` guard가 제일 안전하니 항상 그게 낫나요?"
  - 안전할 수는 있지만 너무 넓게 직렬화해 throughput을 잃기 쉽다.

## 한 줄 정리

`resource`는 "같은 리소스면 모두 한 줄", `resource + day`는 "같은 리소스의 같은 날만 한 줄", pooled inventory는 "같은 풀의 같은 날 총량만 한 줄"이라고 기억하면 guard scope 첫 선택이 훨씬 쉬워진다.
