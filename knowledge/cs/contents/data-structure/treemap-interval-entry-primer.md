# TreeMap Interval Entry Primer

> 한 줄 요약: 예약표가 이미 겹치지 않게 정리돼 있다면, `floorEntry(start)`와 `ceilingEntry(start)`로 찾은 왼쪽/오른쪽 이웃만 확인해서 새 예약의 overlap 여부를 한 번에 판단할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [Reservation Interval Half-Open Boundary Card](./reservation-interval-half-open-boundary-card.md)
- [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)
- [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- [TreeMap Gap Detection Mini Drill](./treemap-gap-detection-mini-drill.md)
- [Disjoint Interval Set](./disjoint-interval-set.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
- [Interval Greedy Patterns](../algorithm/interval-greedy-patterns.md)

retrieval-anchor-keywords: treemap interval primer, reservation overlap check, calendar booking treemap, floorentry ceilingentry booking, floorentry ceilingentry exact match, exact match floorentry ceilingentry stop, left right neighbor overlap rule, online interval insert beginner, booking conflict decision rule, room reservation gap check, treemap booking 뭐예요, interval insert 처음 배우기, my calendar beginner, non overlapping reservation map

## 핵심 개념

이 문서는 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)에서 "`왼쪽 이웃`, `오른쪽 이웃`을 찾는다"까지 이해한 다음 단계다.

초보자 기준으로는 `TreeMap<start, end>`를 이렇게 보면 된다.

- key: 예약 시작 시각
- value: 예약 종료 시각
- map 상태: 이미 저장된 예약들은 서로 겹치지 않는다

그러면 새 예약 `[start, end)`를 넣을 때 질문은 길지 않다.

> 왼쪽 예약의 끝이 `start`보다 늦지 않고, 오른쪽 예약의 시작이 `end`보다 빠르지 않으면 넣을 수 있다.

즉 이웃 조회를 overlap 판단으로 번역하는 것이 이 문서의 목표다.
질문이 "`겹치나?`"보다 "`30분 빈 시간 있나?`"에 더 가깝다면 [TreeMap Gap Detection Mini Drill](./treemap-gap-detection-mini-drill.md)부터 읽는 편이 빠르다.

## 한눈에 보기

기존 예약표가 아래처럼 있다고 하자.

```text
09:00 -> 10:00
10:30 -> 11:00
13:00 -> 14:00
15:30 -> 16:00
```

새 예약 `[start, end)`를 넣을 때 먼저 읽는 값은 두 개다.

| 읽는 값 | 뜻 | 체크 조건 |
|---|---|---|
| `prev = floorEntry(start)` | 시작 시각 기준 왼쪽 이웃 예약 | `prev == null || prev.end <= start` |
| `next = ceilingEntry(start)` | 시작 시각 기준 오른쪽 이웃 예약 | `next == null || end <= next.start` |

두 조건을 한 줄로 합치면 아래가 된다.

```java
boolean canBook =
        (prev == null || !prev.getValue().isAfter(start))
        && (next == null || !end.isAfter(next.getKey()));
```

초보자용 한국어로 바꾸면 이렇다.

- 왼쪽 예약은 새 예약 시작 전에 끝나야 한다.
- 오른쪽 예약은 새 예약 끝난 뒤에 시작해야 한다.

exact match에서 두 메서드가 어디에 멈추는지도 같이 고정해 두면 retrieval이 더 안정적이다.

| 기준 시각 `t`에 이미 예약 시작 key가 있다면 | 어디에 멈추나 | interval check에서 읽는 포인트 |
|---|---|---|
| `floorEntry(t)` | exact match인 `t` 엔트리 | `prev`가 `t`보다 왼쪽 줄이 아닐 수 있다. 그래서 `prev.end <= start`를 그대로 읽어야 한다 |
| `ceilingEntry(t)` | exact match인 `t` 엔트리 | `next`도 같은 줄에서 멈출 수 있다. 그래서 `end <= next.start`를 그대로 읽어야 한다 |

즉 exact match라고 해서 `floorEntry`가 자동으로 한 칸 더 왼쪽으로, `ceilingEntry`가 한 칸 더 오른쪽으로 밀리지 않는다.

## 왜 왼쪽과 오른쪽만 보면 되나

전제는 하나다.

> 저장된 예약들이 이미 서로 겹치지 않게 유지되고 있다.

이 전제에서는 `start`보다 더 왼쪽에 있는 예약들 중에서 실제로 새 예약과 가장 가까운 후보는 `floorEntry(start)`뿐이다.
그 예약도 안 겹치면 더 왼쪽 예약들은 더 일찍 끝나므로 같이 안전하다.

오른쪽도 같은 논리다.
`ceilingEntry(start)`가 새 예약 끝보다 늦게 시작하면, 그보다 더 오른쪽 예약들은 시작 시각이 더 뒤에 있으므로 역시 안전하다.

그래서 beginner 단계에서는 "모든 예약을 다 훑는다"보다 "양옆 이웃 두 개만 본다"가 더 정확한 mental model이다.

## overlap 판단 규칙을 손으로 번역해 보기

같은 예약표를 계속 쓴다.

```text
09:00 -> 10:00
10:30 -> 11:00
13:00 -> 14:00
15:30 -> 16:00
```

| 새 예약 | `prev = floorEntry(start)` | `next = ceilingEntry(start)` | 판단 |
|---|---|---|---|
| `[10:00, 10:30)` | `09:00 -> 10:00` | `10:30 -> 11:00` | 가능 |
| `[09:30, 10:15)` | `09:00 -> 10:00` | `10:30 -> 11:00` | 왼쪽과 충돌 |
| `[11:00, 12:30)` | `10:30 -> 11:00` | `13:00 -> 14:00` | 가능 |
| `[12:30, 13:30)` | `10:30 -> 11:00` | `13:00 -> 14:00` | 오른쪽과 충돌 |

읽는 순서는 항상 같다.

1. `prev.end <= start`인지 본다.
2. `end <= next.start`인지 본다.
3. 둘 다 참이면 overlap이 없다.

이 표 하나가 "neighbor query -> interval insert" 브리지다.

경계 규칙 자체가 아직 손에 안 붙는다면 여기서 바로 멈추고 [Reservation Interval Half-Open Boundary Card](./reservation-interval-half-open-boundary-card.md)로 가는 편이 낫다.
이 문서의 `가능` 판정은 모두 반열린 구간 `[start, end)`를 전제로 해서, `10:00`에 끝난 예약 뒤 `10:00`에 시작하는 예약은 맞닿지만 겹치지 않는다고 읽는다.

## 흔한 오해와 함정

- `ceilingEntry(end)`를 찾아야 한다고 느끼기 쉽지만, beginner용 booking check는 보통 `ceilingEntry(start)`면 충분하다.
  이유는 "새 예약이 시작하는 자리 기준으로 바로 오른쪽 예약"만 보면 되기 때문이다.
- `floorEntry(start)`가 안 겹친다고 모든 경우가 끝나는 것은 아니다.
  오른쪽 예약이 새 예약 끝보다 빨리 시작할 수 있으므로 `ceilingEntry(start)`도 같이 봐야 한다.
- `[start, end)`와 `[start, end]`를 섞으면 경계 조건이 바로 틀어진다.
  이 문서의 규칙은 반열린 구간 `[start, end)` 기준이다.
- 기존 예약들이 이미 서로 겹친 상태라면 이 규칙 하나만으로는 부족하다.
  이 문서는 "비겹침 상태를 유지하는 예약표"를 전제로 한다.

## 실무에서 쓰는 모습

`My Calendar`, 회의실 예약, 룸 예약 같은 문제에서 자주 나오는 코드는 사실 복잡하지 않다.

```java
Map.Entry<LocalTime, LocalTime> prev = bookings.floorEntry(start);
Map.Entry<LocalTime, LocalTime> next = bookings.ceilingEntry(start);

boolean noLeftOverlap = prev == null || !prev.getValue().isAfter(start);
boolean noRightOverlap = next == null || !end.isAfter(next.getKey());

if (noLeftOverlap && noRightOverlap) {
    bookings.put(start, end);
}
```

여기서 중요한 것은 문법보다 읽는 순서다.

- `floorEntry(start)`로 왼쪽 예약의 종료 시각을 읽는다.
- `ceilingEntry(start)`로 오른쪽 예약의 시작 시각을 읽는다.
- 둘 다 안전하면 insert한다.

처음에는 "트리"보다 "양옆 예약 확인 후 넣기"로 기억하는 편이 훨씬 덜 막힌다.

## 더 깊이 가려면

- `[start, end)`와 inclusive endpoint `[start, end]`가 자꾸 섞이면 [Reservation Interval Half-Open Boundary Card](./reservation-interval-half-open-boundary-card.md)
- 아직 `floorKey`와 `ceilingKey` 자체가 헷갈리면 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- `lowerKey/floorKey/ceilingKey/higherKey`를 `Entry` 네 쌍으로 바꾸는 중간 브리지가 필요하면 [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)
- 시작 시각을 찾은 뒤 종료 시각을 읽는 감각이 약하면 [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- `floorEntry(start)`와 `ceilingEntry(start)`를 바로 free-slot 길이 판단으로 바꾸는 짧은 드릴이 필요하면 [TreeMap Gap Detection Mini Drill](./treemap-gap-detection-mini-drill.md)
- insert할 때 merge와 gap tracking까지 같이 유지하려면 [Disjoint Interval Set](./disjoint-interval-set.md)
- 한 번 정렬해서 끝나는 offline 구간 문제와 구분하려면 [Interval Greedy Patterns](../algorithm/interval-greedy-patterns.md)

## 면접/시니어 질문 미리보기

- 왜 `ceilingEntry(start)`만 보고도 오른쪽 overlap을 판단할 수 있나?
  저장된 예약들이 시작 시각 기준으로 정렬돼 있고 서로 비겹침이기 때문이다.
- 왜 `subMap`이 아니라 neighbor query부터 보나?
  새 예약 1건의 가능 여부는 전체 시간창보다 가장 가까운 양옆 예약이 먼저 결정하기 때문이다.
- 언제 `TreeMap` 패턴보다 더 강한 구조가 필요한가?
  "겹치는 예약 전체 찾기", "겹침 개수 세기", "이미 겹친 상태도 저장" 같은 요구가 커질 때다.

## 한 줄 정리

`TreeMap` 예약 insert 입문은 "`왼쪽 예약 끝 <= 새 시작` 그리고 `새 끝 <= 오른쪽 예약 시작`이면 겹치지 않는다"라는 한 줄 규칙으로 정리된다.
