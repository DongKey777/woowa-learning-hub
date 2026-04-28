# TreeMap `subMap` Schedule-Window Mini Drill

> 한 줄 요약: `subMap()`은 "정렬된 일정표에서 오전 창, 오후 창만 잘라 보는 도구"라고 생각하면 되고, 먼저 `어떤 key가 창에 들어오는지` 손으로 맞혀 보면 live view 문서로 넘어가기 훨씬 쉽다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- [Navigable Range API 미니 드릴](../language/java/navigable-range-api-mini-drill.md)
- [`subMap()` / `headMap()` / `tailMap()` Live View Primer](../language/java/treemap-range-view-live-window-primer.md)
- [MySQL Overlap Fallback Beginner Bridge](../database/mysql-overlap-fallback-beginner-bridge.md)

retrieval-anchor-keywords: treemap submap mini drill, treemap submap beginner, schedule window treemap, morning afternoon schedule slice, treemap range query practice, submap 뭐예요, 오전 오후 일정 treemap, treemap submap 처음 배우기, range view before live view, calendar window query basics, treemap schedule window intro, booking conflict window, overlap gap check beginner, submap empty but conflict, reservation gap 뭐예요

## 핵심 개념

`TreeMap<startTime, title>`을 처음 볼 때 `subMap()`은 복잡한 range API보다 먼저 이렇게 읽는 편이 쉽다.

> "정렬된 일정표에서 이 시간창 안에 **시작한 일정들만** 보자."

즉 `subMap(09:00, true, 12:00, false)`는 보통 "오전 일정 창"처럼 읽으면 된다.

초급자 기준 첫 목표는 딱 하나다.

- value가 아니라 key 범위를 본다
- 왼쪽 경계와 오른쪽 경계의 포함/제외를 읽는다
- 결과를 실행 전에 손으로 먼저 맞혀 본다

live view 성질은 다음 문서에서 다루고, 이 드릴에서는 "어떤 일정이 오전 창에 들어오나"만 먼저 고정한다.

## 한눈에 보기

오늘 일정표가 아래처럼 있다고 하자.

```text
08:30 출근 준비
09:00 데일리 스탠드업
10:30 API 리뷰
12:00 점심
13:30 페어 프로그래밍
15:00 배포 점검
```

이때 `TreeMap`의 key 줄만 보면 이렇게 된다.

```text
08:30   09:00   10:30   12:00   13:30   15:00
```

| 질문 | 먼저 읽는 호출 | 손으로 읽는 답 |
|---|---|---|
| 오전 일정만 보려면 | `subMap(09:00, true, 12:00, false)` | `09:00`, `10:30` |
| 점심 이후 일정만 보려면 | `tailMap(12:00, false)` | `13:30`, `15:00` |
| 오전 시작 전 준비 시간까지 보려면 | `headMap(12:00, false)` | `08:30`, `09:00`, `10:30` |

짧게 줄이면 이렇다.

- `headMap`은 앞쪽 창
- `tailMap`은 뒤쪽 창
- `subMap`은 가운데 창

## 창 조회에서 충돌 검사로 넘어가는 브리지

여기서 초급자가 다음으로 자주 묻는 질문이 있다.

> "`subMap`으로 시간창을 잘랐는데, 이 창이 비어 있으면 예약 충돌이 없는 건가요?"

답은 "아직 반만 맞다"에 가깝다.

`subMap(start, true, end, false)`는 **그 창 안에서 시작한 예약**을 보여 준다.
그래서 "오전 창에 어떤 예약들이 보이나?"를 읽을 때는 좋지만, "새 예약이 겹치나?"를 단독으로 판정하기에는 부족할 수 있다.

같은 예약표를 다시 보자.

```text
09:00 -> 10:00
10:30 -> 11:00
13:00 -> 14:00
```

| 새 예약 질문 | `subMap(start, true, end, false)` 결과 | 실제 판단 |
|---|---|---|
| `[10:00, 10:30)` 넣어도 되나 | 비어 있음 | 가능. 앞 예약이 `10:00`에 끝나고 뒤 예약이 `10:30`에 시작한다 |
| `[09:30, 10:15)` 넣어도 되나 | 비어 있을 수 있음 | 불가. `09:00 -> 10:00`이 이미 왼쪽에서 걸쳐 들어온다 |

두 번째 줄이 핵심이다.

- `subMap(09:30, true, 10:15, false)`에는 "`09:30` 이후에 시작한 예약"이 없을 수 있다
- 하지만 `09:00 -> 10:00` 예약은 창 바깥에서 시작해서 창 안으로 이어진다
- 그래서 `subMap`이 비었다고 바로 "안전한 빈 시간"이라고 결론 내리면 틀린다

초급자용 연결 문장은 이렇게 잡으면 된다.

- `subMap` = "이 창 안에 **시작한 예약 목록** 보기"
- `floorEntry(start)` = "왼쪽에서 이미 시작해 들어오는 예약 있는지 보기"
- `ceilingEntry(start)` = "오른쪽에서 바로 붙는 다음 예약 보기"

즉 창 조회는 "누가 보이느냐"에 강하고, 충돌 검사와 gap 검사는 "양옆 이웃이 안전하냐"까지 붙어야 끝난다.

## 오전/오후 일정 4문항 미니 드릴

같은 일정표를 계속 쓴다.

```text
08:30 출근 준비
09:00 데일리 스탠드업
10:30 API 리뷰
12:00 점심
13:30 페어 프로그래밍
15:00 배포 점검
```

### 1. 오전 회의 창

호출:

```java
schedule.subMap("09:00", true, "12:00", false)
```

답:

- `09:00 데일리 스탠드업`
- `10:30 API 리뷰`

해석: 시작 경계 `09:00`은 포함, 끝 경계 `12:00`은 제외라서 `12:00 점심`은 안 들어온다.

### 2. 점심 포함 오후 창

호출:

```java
schedule.subMap("12:00", true, "18:00", false)
```

답:

- `12:00 점심`
- `13:30 페어 프로그래밍`
- `15:00 배포 점검`

해석: 이번에는 시작 경계가 `12:00`이고 포함이므로 점심 일정도 창 안에 들어온다.

### 3. 점심 이후만 보고 싶을 때

호출:

```java
schedule.tailMap("12:00", false)
```

답:

- `13:30 페어 프로그래밍`
- `15:00 배포 점검`

해석: "`12:00` 이후"라고 말했으니 exact match인 `12:00`은 뺀다.

### 4. 오전 전체를 넉넉하게 보고 싶을 때

호출:

```java
schedule.headMap("12:00", true)
```

답:

- `08:30 출근 준비`
- `09:00 데일리 스탠드업`
- `10:30 API 리뷰`
- `12:00 점심`

해석: `headMap`도 결국 경계 포함 여부만 읽으면 된다.

## 상세 분해

`subMap(from, fromInclusive, to, toInclusive)`가 길어 보여도 초급자는 아래 두 질문만 나눠 읽으면 된다.

1. 시작 경계 `from`을 포함하나
2. 끝 경계 `to`를 포함하나

오전/오후 일정 문제에 붙이면 이렇게 번역된다.

| 원래 호출 | 초급자용 번역 |
|---|---|
| `subMap(09:00, true, 12:00, false)` | `09:00`부터 시작하는 일정은 포함, `12:00` 시작 일정은 제외 |
| `subMap(12:00, true, 18:00, false)` | 점심 시각부터 시작하는 일정은 포함, 저녁 전까지만 보기 |
| `tailMap(12:00, false)` | `12:00`보다 뒤에서 시작한 일정만 보기 |

핵심은 "일정이 그 시간까지 이어지는가"보다 먼저 "그 일정의 **시작 key**가 범위 안인가"를 본다는 점이다.

## 흔한 오해와 함정

- `subMap(09:00, true, 12:00, false)`를 "오전 동안 진행 중인 모든 일정"으로 읽으면 안 된다. 이 호출은 오전에 **시작한 일정**을 본다.
- `12:00`이 끝 경계라서 오전 창에 포함될 것 같아도, `false`면 빠진다.
- value가 `"점심"`인지 `"리뷰"`인지로 자르는 게 아니다. `TreeMap`은 key인 `09:00`, `10:30`, `12:00` 같은 시작 시각을 기준으로 자른다.
- `subMap(...)` 결과가 비었다고 곧바로 "그 시간대는 예약 가능"이라고 읽으면 안 된다. 창 바깥에서 시작해 안으로 이어지는 왼쪽 예약이 있을 수 있다.
- 이 드릴만 보고 `subMap` 결과가 독립 복사본이라고 생각하면 다음 단계에서 헷갈린다. 복사본인지 live view인지는 [live view primer](../language/java/treemap-range-view-live-window-primer.md)에서 이어서 분리하면 된다.

## 실무에서 쓰는 모습

백엔드에서 예약표나 배치 시간표를 볼 때 "`오전 예약만 보여 줘`", "`점심 이후 건만 다시 확인하자`" 같은 요구는 자주 나온다.

이때 초급자는 먼저 아래처럼 번역하면 된다.

- 오전/오후처럼 시간창을 자른다 -> `subMap`
- 특정 시각 이전만 본다 -> `headMap`
- 특정 시각 이후만 본다 -> `tailMap`
- 새 예약이 정말 비어 있는 틈에 들어가는지 본다 -> `floorEntry(start)`와 `ceilingEntry(start)`

그다음에야 "`이 창이 live view라서 원본 수정이 같이 보이는가`", "`범위 밖 key를 넣으면 어떻게 되나`" 같은 Java 컬렉션 성질로 내려가면 읽기 순서가 자연스럽다.

예약 예제로 붙이면 보통 순서가 이렇게 간다.

1. `subMap(09:00, true, 12:00, false)`로 오전 창에 어떤 예약이 잡혀 있는지 본다.
2. 새 예약 `[09:30, 10:15)`처럼 실제 booking check가 나오면 `floorEntry(09:30)`와 `ceilingEntry(09:30)`로 양옆 이웃을 읽는다.
3. 비어 보이는 창과 실제 gap을 구분한다.

## 더 깊이 가려면

- 오전 창 다음으로 충돌 검사와 gap check까지 붙이고 싶다면 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- `headMap`/`tailMap`/`subMap` 기본 경계 패턴을 숫자 예제로 더 풀고 싶다면 [Navigable Range API 미니 드릴](../language/java/navigable-range-api-mini-drill.md)
- 왜 결과가 복사본이 아니라 원본 위 창인지 이어서 보고 싶다면 [`subMap()` / `headMap()` / `tailMap()` Live View Primer](../language/java/treemap-range-view-live-window-primer.md)
- 메모리 안 `TreeMap` 검사와 DB 저장 시점 overlap 보장을 구분하고 싶다면 [MySQL Overlap Fallback Beginner Bridge](../database/mysql-overlap-fallback-beginner-bridge.md)

## 면접/시니어 질문 미리보기

- "`subMap`은 범위 안에서 시작한 일정만 주는데, 오전에 걸쳐 있는 일정 전체를 보려면 무엇을 더 확인해야 하나?"
  보통 `floorEntry(rangeStart)`를 같이 봐서 더 일찍 시작했지만 아직 끝나지 않은 일정을 보완한다.
- "`subMap`이 비었는데도 왜 충돌일 수 있나?"
  기존 예약이 창 바깥에서 시작해서 창 안으로 이어질 수 있기 때문이다. 그래서 overlap 판단은 창 내부 목록만으로 끝나지 않는다.
- "`TreeMap`으로 충분한가, interval tree가 필요한가?"
  양옆 이웃과 간단한 시간창 조회면 `TreeMap`이 충분하지만, 겹치는 interval 전부를 자주 찾으면 별도 구조가 필요하다.

## 한 줄 정리

`TreeMap subMap` 초급 드릴의 핵심은 "오전/오후 창에서 어떤 **시작 시각 key**가 들어오는지"를 먼저 손으로 맞히고, 그다음에만 live view와 interval 심화로 내려가는 것이다.
