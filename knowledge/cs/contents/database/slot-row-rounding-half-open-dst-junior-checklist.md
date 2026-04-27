# Slot Row 도입 전 주니어 체크리스트: Rounding, Half-Open Interval, DST

> 한 줄 요약: slot row는 `UNIQUE`만 만들면 끝나는 모델이 아니라, `[start, end)` 경계, slot rounding, timezone/DST 계약을 먼저 하나로 고정해야 충돌 truth가 흔들리지 않는다.

**난이도: 🟢 Beginner**

관련 문서:

- [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- [Exclusion Constraint vs Slot Row 빠른 선택 가이드](./exclusion-constraint-vs-slot-row-quick-chooser.md)
- [Slotization Precheck Queries for Overlaps, Rounding Collisions, and DST Boundaries](./slotization-precheck-overlap-rounding-dst.md)
- [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)

retrieval-anchor-keywords: slot row junior checklist, slot row rounding checklist, half-open interval beginner, slot row dst pitfall, slotization beginner primer, slot row before adoption, slot rounding floor ceil, local time fold gap, slot row timezone checklist, rounded slot collision beginner, slot row adjacent booking, [start end) booking, beginner slotization guardrails

## 핵심 개념

slot row를 처음 도입할 때는 "예약 row를 여러 slot row로 펼친다" 정도로만 이해하기 쉽다.
하지만 실제로 먼저 고정해야 하는 것은 row 수가 아니라 **시간을 자르는 규칙**이다.

초보자 기준 mental model은 이 정도면 충분하다.

- interval 계약: 예약 시간은 보통 `[start, end)`로 읽는다
- rounding 계약: `start`는 어느 칸으로 내리고, `end`는 어느 칸으로 올릴지 정한다
- timezone 계약: 어떤 시간대를 canonical source로 쓸지 정한다

이 셋이 경로마다 다르면 같은 예약도 서로 다른 slot 집합으로 펼쳐진다.
그 순간 slot row의 `UNIQUE`는 안전장치가 아니라 **뒤늦게 드러난 정책 불일치 탐지기**가 된다.

## 먼저 머릿속에 넣을 그림

| 질문 | junior가 먼저 고를 답 |
|---|---|
| "겹침"은 어떤 경계로 판단하나? | 보통 `[start, end)` |
| `10:05` 같은 애매한 시작은 어디로 가나? | 미리 정한 `floor(start)` 또는 다른 단일 규칙 |
| `10:25` 같은 애매한 종료는 어디로 가나? | 미리 정한 `ceil(end)` 또는 다른 단일 규칙 |
| slot key는 local time인가 UTC인가? | 가능하면 UTC slot key + local display 분리 |
| DST 날의 `02:30`처럼 애매한 시간은? | 로컬 wall-clock만 믿지 말고 zone + calendar로 판정 |

핵심은 "어느 SQL이 더 영리한가"가 아니다.
create, reschedule, cleanup, backfill이 **같은 시간 계산기**를 쓰는지가 먼저다.

## 1. half-open interval부터 고정한다

slot row로 가기 전 가장 먼저 통일할 것은 boundary다.
beginner 문서에서는 거의 항상 `[start, end)`를 기본값으로 두는 편이 설명이 쉽다.

`[start, end)` 뜻:

- `start`는 포함
- `end`는 제외

예를 들어 30분 slot이면 아래 둘은 겹치지 않는다.

| 예약 | 의미 | 겹침 여부 |
|---|---|---|
| `[10:00, 10:30)` | `10:00` slot만 점유 | - |
| `[10:30, 11:00)` | `10:30` slot만 점유 | 겹치지 않음 |

초보자가 자주 헷갈리는 포인트:

- `[10:00, 10:30]`처럼 end를 포함한다고 생각하면 인접 예약도 겹치는 것처럼 보인다
- create는 `[start, end)`인데 cleanup은 `[start, end]`처럼 다르게 해석하면 slot release가 늦거나 빨라진다
- reschedule에서 old/new interval 경계를 다르게 쓰면 같은 booking이 자기 자신과 충돌하는 것처럼 보일 수 있다

한 줄 기억법:

- 인접 예약을 허용하고 싶으면 `[start, end)`부터 고정한다

## 2. rounding은 "예쁘게 보정"이 아니라 occupancy truth다

slot row에서 rounding은 UI 보정이 아니다.
어떤 slot을 점유했다고 간주할지 결정하는 핵심 계약이다.

예를 들어 slot width가 30분이고 규칙이 `floor(start)`, `ceil(end)`라고 하자.

| 원래 interval | 펼쳐진 slot 예시 | 메모 |
|---|---|---|
| `[10:00, 10:30)` | `10:00` | 경계가 딱 맞아 단순하다 |
| `[10:05, 10:25)` | `10:00` | partial slot 하나를 점유한다고 본다 |
| `[10:25, 10:45)` | `10:00`, `10:30` | 같은 20분이라도 경계 위치에 따라 slot 수가 달라진다 |

이 표가 보여 주는 핵심은 이것이다.

- 같은 길이의 예약도 경계 위치에 따라 점유 slot 수가 달라질 수 있다
- 그래서 product 정책이 "partial slot을 어떻게 팔 것인가"를 먼저 정하지 않으면 DB 모델이 먼저 흔들린다

### 자주 하는 오해

| 오해 | 왜 위험한가 | 더 나은 기준 |
|---|---|---|
| "대충 floor/ceil 하면 되겠지" | create/backfill/replay 경로가 다르면 같은 예약이 다른 slot으로 퍼진다 | 모든 경로에서 같은 rounding 함수 사용 |
| "읽을 때만 반올림하면 된다" | write path와 read path가 다른 truth를 보게 된다 | 저장 시점과 검증 시점의 rounding 계약 일치 |
| "slot row는 결국 `UNIQUE`니까 경계는 덜 중요하다" | 경계가 곧 어떤 `UNIQUE` key에 부딪히는지 결정한다 | slot key 생성기를 계약으로 취급 |

## 3. DST는 "특정 나라만의 예외"가 아니라 local-time 모델의 구조적 함정이다

UTC slot key만 쓰고 display만 local time으로 바꾸면 DST 위험이 크게 줄어든다.
반대로 local wall-clock slot을 business truth로 삼으면 DST를 명시적으로 모델링해야 한다.

대표 함정은 두 가지다.

| 현상 | 실제 예시 | 무슨 일이 생기나 |
|---|---|---|
| gap | 미국 동부 시간은 `2026-03-08 02:30`이 존재하지 않는다 | local slot 생성기가 없는 시간을 만들 수 있다 |
| fold | 미국 동부 시간은 `2026-11-01 01:30`이 두 번 온다 | 같은 라벨이 다른 UTC 두 시각을 가리킬 수 있다 |

초보자 기준 결론:

- "local 시각 문자열"만 slot key로 쓰지 않는다
- `zone_name` 없이 local timestamp만 저장하지 않는다
- DST를 쓰는 지역이면 slot calendar 또는 검증 fixture가 필요하다

한국처럼 DST를 쓰지 않는 환경에서도 이 체크를 빼면 안 되는 이유는 간단하다.
글로벌 서비스, 해외 지점, 외부 파트너 데이터가 들어오는 순간 같은 문제가 다시 생긴다.

## 도입 전에 이 6가지는 체크한다

1. interval 계약이 모든 경로에서 `[start, end)`로 고정돼 있는가
2. slot width가 한 문서와 한 코드 경로로 정의돼 있는가
3. `start`/`end` rounding 규칙이 create, reschedule, cleanup, backfill에서 같은가
4. slot key가 UTC 기준인지, local 기준이면 `zone_name`과 DST 정책이 함께 정의돼 있는가
5. adjacent booking, partial-slot booking, DST gap/fold fixture로 테스트가 있는가
6. "원래 interval은 안 겹치지만 rounding 후 충돌" 케이스를 precheck로 분리할 수 있는가

이 중 하나라도 비어 있으면, slot row 도입 전에 먼저 계약 문서를 채우는 편이 낫다.

## 바로 써먹는 최소 예시

시나리오: 30분 단위 회의실 예약을 slot row로 옮기려 한다.

- 권장 interval 계약: `[start_at, end_at)`
- 권장 slot key: `(room_id, slot_start_utc)`
- 권장 rounding 예시: `floor(start_at_utc, 30m)`, `ceil(end_at_utc, 30m)`
- 검증 fixture:
  - `[10:00, 10:30)`와 `[10:30, 11:00)`는 공존해야 한다
  - `[10:05, 10:25)`와 `[10:25, 10:45)`는 policy상 몇 slot을 점유하는지 합의돼 있어야 한다
  - DST 지역이면 `2026-03-08`, `2026-11-01` 같은 transition 날짜 fixture가 있어야 한다

이 정도가 없으면 slot table DDL보다 먼저 시간 계약 문서를 채우는 편이 안전하다.

## 어디로 이어서 읽으면 좋은가

- slot row 자체가 맞는 모델인지 먼저 고르고 싶으면 -> [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- continuous interval과 discrete slot 중 무엇이 더 자연스러운지 고르고 싶으면 -> [Exclusion Constraint vs Slot Row 빠른 선택 가이드](./exclusion-constraint-vs-slot-row-quick-chooser.md)
- cutover 전에 rounding-only collision과 DST row를 어떻게 찾는지 보고 싶으면 -> [Slotization Precheck Queries for Overlaps, Rounding Collisions, and DST Boundaries](./slotization-precheck-overlap-rounding-dst.md)
- reschedule에서 `old_slots ∪ new_slots`를 왜 같이 봐야 하는지 이어서 보려면 -> [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md)

## 한 줄 정리

slot row 도입 전 주니어 체크리스트의 핵심은 간단하다. `UNIQUE`보다 먼저 `[start, end)`, rounding, timezone/DST 계약을 하나로 고정해야 같은 예약이 항상 같은 slot 집합으로 펼쳐진다.
