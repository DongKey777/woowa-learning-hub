# TreeMap Null Boundary Micro Drill

> 한 줄 요약: 예약표를 `TreeMap<start, end>`로 볼 때 `lowerEntry`/`floorEntry`는 첫 예약보다 더 왼쪽이면 `null`, `higherEntry`/`ceilingEntry`는 마지막 예약보다 더 오른쪽이면 `null`이라는 경계 감각만 먼저 붙이면 첫 NPE를 크게 줄일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [TreeSet, TreeMap Null-Boundary Quick Reference](./treeset-treemap-null-boundary-quick-reference.md)
- [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)
- [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
- [Ordered Map Null-Safe Practice Drill](../language/java/ordered-map-null-safe-practice-drill.md)

retrieval-anchor-keywords: treemap null boundary micro drill, lowerentry null beginner, higherentry null beginner, floorentry null first reservation, ceilingentry null last reservation, treemap reservation boundary null, 처음 예약 lowerentry 왜 null, 마지막 예약 higherentry 왜 null, floorentry ceilingentry null safety, treemap entry null check basics, reservation treemap npe 헷갈려요, what is lowerentry null, ordered map boundary beginner

## 핵심 개념

처음에는 메서드 네 개를 길게 외우기보다 아래 두 줄만 먼저 고정하면 된다.

- `lowerEntry`와 `floorEntry`는 왼쪽을 본다.
- `higherEntry`와 `ceilingEntry`는 오른쪽을 본다.

예약표에서 `null`은 보통 "오류"가 아니라 "`그 방향에 예약이 없음`"이라는 정상 신호다.

- 첫 예약보다 더 이른 시각을 물으면 왼쪽 이웃이 없어서 `lowerEntry`/`floorEntry`가 `null`
- 마지막 예약보다 더 늦은 시각을 물으면 오른쪽 이웃이 없어서 `higherEntry`/`ceilingEntry`가 `null`

이 문서는 그 두 경계만 예약 예제로 짧게 고정하는 카드다.

## 한눈에 보기

예약표가 아래처럼 있다고 하자.

```text
09:00 -> 10:00
10:30 -> 11:00
13:00 -> 14:00
15:30 -> 16:00
```

| 질문 | 호출 | 결과 | 왜 그런가 |
|---|---|---|---|
| 첫 예약보다 더 이른 `08:00` 왼쪽 예약은? | `lowerEntry(08:00)` | `null` | strict하게 왼쪽이 없다 |
| 첫 예약보다 더 이른 `08:00` 같거나 왼쪽 예약은? | `floorEntry(08:00)` | `null` | 포함해도 왼쪽 후보가 없다 |
| 마지막 예약보다 더 늦은 `17:00` 오른쪽 예약은? | `higherEntry(17:00)` | `null` | strict하게 오른쪽이 없다 |
| 마지막 예약보다 더 늦은 `17:00` 같거나 오른쪽 예약은? | `ceilingEntry(17:00)` | `null` | 포함해도 오른쪽 후보가 없다 |

짧게 외우면 이렇다.

- 첫 슬롯 바깥에서는 왼쪽 계열이 `null`
- 마지막 슬롯 바깥에서는 오른쪽 계열이 `null`

## 첫 슬롯 경계 2문제

### 문제 1. `lowerEntry(08:00)`은 왜 `null`인가

정답: `08:00`보다 strict하게 더 이른 예약이 없기 때문이다.

`09:00`은 첫 예약이지만 `08:00`의 오른쪽에 있다.
그래서 `lowerEntry(08:00)`의 후보가 아니다.

### 문제 2. `floorEntry(08:00)`도 왜 `null`인가

정답: `floor`는 exact match를 포함해도 `08:00` 이하 예약이 하나도 없기 때문이다.

입문자가 자주 하는 착각은 "`첫 예약 09:00이라도 하나 주겠지`"인데, `floorEntry`는 오른쪽 첫 예약을 주는 메서드가 아니다.
왼쪽 후보가 없으면 `null`이다.

## 마지막 슬롯 경계 2문제

### 문제 3. `higherEntry(17:00)`은 왜 `null`인가

정답: `17:00`보다 strict하게 더 늦은 예약이 없기 때문이다.

마지막 예약 `15:30 -> 16:00`은 `17:00`의 왼쪽에 있으므로 `higherEntry` 후보가 아니다.

### 문제 4. `ceilingEntry(17:00)`도 왜 `null`인가

정답: `ceiling`은 exact match를 포함해도 `17:00` 이상 예약이 하나도 없기 때문이다.

입문자가 자주 하는 착각은 "`마지막 예약이라도 주겠지`"인데, `ceilingEntry`는 왼쪽 마지막 예약을 주는 메서드가 아니다.
오른쪽 후보가 없으면 `null`이다.

## 흔한 오해와 함정

- `floorEntry`를 "무조건 이전 예약 하나는 주는 메서드"로 외우면 첫 슬롯 바깥에서 틀린다.
- `ceilingEntry`를 "무조건 다음 예약 하나는 주는 메서드"로 외우면 마지막 슬롯 바깥에서 틀린다.
- `lowerEntry`와 `higherEntry`만 `null`이 나온다고 생각하기 쉽지만, `floorEntry`와 `ceilingEntry`도 경계를 벗어나면 `null`이다.
- `entry.getValue()`를 바로 읽으면 첫 슬롯/마지막 슬롯 경계에서 NPE가 난다.

안전한 첫 습관은 아래 두 줄이다.

```java
Map.Entry<LocalTime, LocalTime> prev = reservations.floorEntry(requestStart);
Map.Entry<LocalTime, LocalTime> next = reservations.ceilingEntry(requestStart);
```

그리고 `prev != null`, `next != null`을 먼저 확인한 뒤 `getValue()`나 `getKey()`를 읽는다.

## 실무에서 쓰는 모습

새 예약 `[08:00, 08:30)`을 넣는다고 하자.

- `floorEntry(08:00)` -> `null`
- `ceilingEntry(08:00)` -> `09:00 -> 10:00`

이 뜻은 "`왼쪽 예약은 없음, 오른쪽 첫 예약은 09:00`"이다.

반대로 새 예약 `[17:00, 17:30)`을 넣는다고 하자.

- `floorEntry(17:00)` -> `15:30 -> 16:00`
- `ceilingEntry(17:00)` -> `null`

이 뜻은 "`왼쪽 마지막 예약은 있음, 오른쪽 예약은 없음`"이다.

즉 예약 경계 문제는 "`양옆 둘 다 항상 있다`"가 아니라 "`한쪽만 있을 수도 있고 둘 다 없을 수도 있다`"로 읽는 편이 beginner-safe 하다.

## 더 깊이 가려면

- strict/inclusive 차이 자체가 헷갈리면 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- `Key`와 `Entry`를 같은 표로 붙이고 싶으면 [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)
- `floorEntry`/`ceilingEntry`에서 종료 시각 `value`까지 읽는 연습을 더 하려면 [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- broader한 `null vs 예외` 경계표가 먼저 필요하면 [TreeSet, TreeMap Null-Boundary Quick Reference](./treeset-treemap-null-boundary-quick-reference.md)

## 한 줄 정리

예약 `TreeMap`에서 첫 슬롯 바깥이면 `lowerEntry`/`floorEntry`가 `null`, 마지막 슬롯 바깥이면 `higherEntry`/`ceilingEntry`가 `null`이라고 먼저 읽으면 경계 NPE를 크게 줄일 수 있다.
