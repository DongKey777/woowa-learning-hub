# TreeMap Key/Entry Strictness Bridge

> 한 줄 요약: `왜 lower랑 floor가 달라요?`라는 감각은 `Entry`로 바꿔도 그대로이며, `exact match 포함 여부`는 `lower/higher` vs `floor/ceiling`이 결정하고 `Key/Entry` 차이가 결정하지 않는다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
- [Ordered Map Null-Safe Practice Drill](../language/java/ordered-map-null-safe-practice-drill.md)

retrieval-anchor-keywords: treemap key entry bridge, lowerkey lowerentry beginner, floorkey floorentry beginner, ceilingkey ceilingentry beginner, higherkey higherentry beginner, treemap strict inclusive entry, 왜 lower랑 floor가 달라요 entry, exact match 포함 여부 entry, lower floor ceiling higher 헷갈림, ordered map key entry difference, ordered map exact match entry, entry로 바꾸면 포함 여부 바뀌나요, treemap key에서 entry로, treemap entry 뭐예요, what is lowerentry

## 핵심 개념

이 문서의 목표는 새 개념을 많이 추가하는 것이 아니다.
초보자 기준으로는 아래 한 줄만 붙이면 된다.

> `Key`는 "어느 예약 줄인가"를 찾고, `Entry`는 "그 예약 줄의 시작과 끝을 같이" 준다.

여기서 beginner가 놓치기 쉬운 연결은 하나 더 있다.

> `TreeSet.floor(x)`를 이해했다면 `TreeMap.floorKey(x)`도 같은 exact-match 규칙이고, `TreeMap.floorEntry(x)`는 그 자리에 value만 붙여 읽는 다음 칸이다.

strictness도 바뀌지 않는다.

- `lower` / `higher`는 exact match를 제외한다.
- `floor` / `ceiling`은 exact match를 포함한다.
- `Key`를 `Entry`로 바꿔도 이 포함 규칙은 그대로다.

즉 `lowerKey(t)`를 이해했다면, `lowerEntry(t)`는 "같은 줄을 찾되 value까지 함께 받는 버전"이라고 읽으면 된다.

입문자 질문을 바로 번역하면 아래 두 줄이다.

- `왜 lower랑 floor가 달라요?` -> strict vs inclusive 차이다.
- `entry로 바꾸면 exact match 포함 여부도 바뀌나요?` -> 아니다. `Key/Entry`가 아니라 메서드 이름이 결정한다.

ordered map query로 다시 쓰면 아래처럼 읽으면 된다.

| 학습자 질문 | 바로 번역한 답 |
|---|---|
| `ordered map에서 key랑 entry 차이가 뭐예요?` | key는 위치만, entry는 위치와 값까지 준다 |
| `entry로 바꾸면 exact match 포함 여부도 바뀌나요?` | 아니다. `lower/floor/ceiling/higher` 이름이 포함 여부를 정한다 |
| `왜 lowerEntry랑 floorEntry가 달라요?` | `entry` 차이가 아니라 strict/inclusive 차이다 |

특히 `floorKey -> floorEntry`에서 멈칫하는 초보자는 아래처럼 세 칸을 이어 읽으면 된다.

| 이미 익힌 칸 | 다음 칸 | 그대로 유지되는 규칙 |
|---|---|---|
| `TreeSet.floor(10:30)` -> `10:30` | `TreeMap.floorKey(10:30)` -> `10:30` | exact match 포함 |
| `TreeMap.floorKey(10:30)` -> `10:30` | `TreeMap.floorEntry(10:30)` -> `10:30 -> 11:00` | exact match 포함 |

## 한눈에 보기

`TreeMap<start, end>` 예약표가 아래처럼 있다고 하자.

```text
09:00 -> 10:00
10:30 -> 11:00
13:00 -> 14:00
15:30 -> 16:00
```

기준 시각이 `10:30`일 때, key와 entry를 한 장으로 붙이면 이렇다.

| 질문 | key 버전 | entry 버전 | exact match 포함 여부 |
|---|---|---|---|
| 바로 이전 예약 | `lowerKey(10:30)` -> `09:00` | `lowerEntry(10:30)` -> `09:00 -> 10:00` | 제외 |
| 같거나 바로 이전 예약 | `floorKey(10:30)` -> `10:30` | `floorEntry(10:30)` -> `10:30 -> 11:00` | 포함 |
| 같거나 바로 다음 예약 | `ceilingKey(10:30)` -> `10:30` | `ceilingEntry(10:30)` -> `10:30 -> 11:00` | 포함 |
| 바로 다음 예약 | `higherKey(10:30)` -> `13:00` | `higherEntry(10:30)` -> `13:00 -> 14:00` | 제외 |

`floorKey(10:30)`와 `floorEntry(10:30)`가 둘 다 같은 줄에서 멈춘다는 점을 먼저 고정하면 value-read 단계에서 덜 흔들린다.
차이는 "`exact match를 포함하나`"가 아니라 "`그 줄의 끝 시각까지 같이 받나`"뿐이다.

초보자용으로 줄이면 이렇게 외우면 된다.

- `key`는 시작 시각만
- `entry`는 시작 시각 + 종료 시각
- strict/inclusive는 메서드 이름이 결정하고, key/entry 차이가 결정하지는 않는다

## exact match 포함 여부를 다시 고정하기

이 문서에서 가장 중요한 오해 방지는 이것이다.

| 헷갈리는 포인트 | 실제 기준 |
|---|---|
| `lowerEntry`가 `lowerKey`보다 더 많이 포함하나 | 아니다. 둘 다 exact match를 제외한다 |
| `floorEntry`는 `Entry`라서 포함하나 | 아니다. `floor`라서 포함한다 |
| `ceilingEntry`와 `higherEntry` 차이가 value 때문인가 | 아니다. `ceiling`은 포함, `higher`는 제외다 |
| `ordered map에서 entry가 더 똑똑한 검색인가` | 아니다. 검색 기준은 여전히 key이고 entry는 찾은 줄의 value를 같이 보여 줄 뿐이다 |

즉 `왜 lower랑 floor가 달라요`의 답은 `Key` 단계에서도 같고 `Entry` 단계에서도 같다.

## 네 쌍을 한 번에 연결하는 표

예약 충돌 검사 직전 단계에서는 아래 변환표가 가장 실용적이다.

| 이미 읽던 질문 | key로 끝내면 | entry로 확장하면 | 왜 entry가 필요한가 |
|---|---|---|---|
| `t`보다 strict하게 바로 이전 예약은? | `lowerKey(t)` | `lowerEntry(t)` | 그 예약이 몇 시에 끝나는지 읽기 위해 |
| `t`와 같거나 바로 이전 예약은? | `floorKey(t)` | `floorEntry(t)` | exact match 예약의 종료 시각까지 읽기 위해 |
| `t`와 같거나 바로 다음 예약은? | `ceilingKey(t)` | `ceilingEntry(t)` | 다음 예약의 시작/끝을 함께 보기 위해 |
| `t`보다 strict하게 바로 다음 예약은? | `higherKey(t)` | `higherEntry(t)` | exact match는 건너뛴 다음 예약 정보를 보기 위해 |

핵심은 "`어느 줄인가`를 찾던 질문이 `그 줄 내용을 읽는 질문`으로 커진다"는 점이다.

## 예약 충돌 검사로 넘어갈 때 왜 이 브리지가 필요하나

`Key`만으로는 "양옆 예약이 있다"까지만 알 수 있다.
하지만 예약 충돌 검사는 보통 아래 두 질문까지 필요하다.

1. 왼쪽 예약은 몇 시에 끝나나?
2. 오른쪽 예약은 몇 시에 시작하나?

예를 들어 새 예약이 `[11:00, 11:30)`이라면:

- `floorKey(11:00)` -> `10:30`
- `floorEntry(11:00)` -> `10:30 -> 11:00`
- `ceilingKey(11:00)` -> `13:00`
- `ceilingEntry(11:00)` -> `13:00 -> 14:00`

이제야 충돌 판단 문장으로 번역할 수 있다.

- 왼쪽 예약 끝 `11:00`은 새 시작 `11:00`을 넘지 않는다.
- 오른쪽 예약 시작 `13:00`은 새 끝 `11:30`보다 늦다.

그래서 입문자에게는 `Key -> Entry` 브리지가 사실상 "`이웃 찾기`에서 `충돌 검사 읽기`로 넘어가는 문턱"이다.

## 짧은 코드 감각

아래 6줄이 이 문서의 실전 감각이다.

```java
Map.Entry<LocalTime, LocalTime> prev = reservations.floorEntry(start);
Map.Entry<LocalTime, LocalTime> next = reservations.ceilingEntry(start);

boolean noLeftOverlap = prev == null || !prev.getValue().isAfter(start);
boolean noRightOverlap = next == null || !end.isAfter(next.getKey());
```

여기서 읽는 순서는 고정이다.

1. 어떤 이웃을 찾을지 `floor` / `ceiling` / `lower` / `higher`로 정한다.
2. 시작 시각만 필요하면 `Key`, 시작+끝이 필요하면 `Entry`를 고른다.
3. `Entry`라면 `getKey()`와 `getValue()`를 분리해서 읽는다.

## 흔한 오해와 함정

- `Entry`가 더 똑똑한 검색이라고 느끼기 쉽지만, 실제 검색 기준은 여전히 key다. `value`를 비교해서 찾는 것이 아니다.
- `lowerEntry`와 `floorEntry` 차이가 `Entry`라서 생긴다고 오해하기 쉽다. 차이는 여전히 strict vs inclusive다.
- `floorKey`에서 `floorEntry`로 바꾸는 순간 exact-match 규칙을 새로 외워야 한다고 느끼기 쉽다. 실제로는 같은 줄에서 멈춘 뒤 value를 같이 읽기만 하면 된다.
- `higherEntry(t)`를 "무조건 다음 줄"로 외우면 exact match에서 틀린다. 같은 key는 strict하게 건너뛴다.
- `Entry`를 받았으면 바로 `getValue()`부터 읽고 싶어지지만, 경계 시각에서는 `null` 먼저 확인해야 한다.
- 충돌 검사 전체를 한 번에 외우려 하면 더 막힌다. 먼저 `Key/Entry` 대응표를 붙이고, 그다음 `prev.end <= start`, `end <= next.start`로 넘어가는 편이 낫다.

## 더 깊이 가려면

- 아직 `lower/floor/ceiling/higher` 이름 자체가 헷갈리면 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- `floorEntry`/`ceilingEntry` 위주로 종료 시각 읽기만 먼저 손에 붙이고 싶다면 [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- 실제 예약 충돌 검사 한 줄 규칙으로 이어 가려면 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- `NavigableMap` 전체 이름표를 key/entry/set 관점에서 한 장으로 다시 보고 싶다면 [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

## 한 줄 정리

`lowerKey`/`floorKey`/`ceilingKey`/`higherKey`에서 이미 익힌 strictness는 그대로 두고, 예약 충돌 검사 직전에는 같은 네 쌍을 `lowerEntry`/`floorEntry`/`ceilingEntry`/`higherEntry`로 바꿔 "그 줄의 종료 시각까지 읽는 단계"로 넘어가면 된다.
