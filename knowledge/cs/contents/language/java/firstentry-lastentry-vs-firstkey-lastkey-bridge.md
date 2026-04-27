# `firstEntry()`/`lastEntry()` vs `firstKey()`/`lastKey()` Beginner Bridge

> 한 줄 요약: 빈 `TreeMap`에서 `firstEntry()`/`lastEntry()`는 `null`로 "entry가 없음"을 알려 주지만, `firstKey()`/`lastKey()`는 "반드시 key가 있어야 한다"는 전제로 `NoSuchElementException`을 던진다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`pollFirst`/`pollLast` vs `first`/`last` Beginner Bridge](./pollfirst-polllast-vs-first-last-beginner-bridge.md)
- [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)
- [TreeMap Interval Entry Primer](../data-structure/treemap-interval-entry-primer.md)
- [Navigable Range API 미니 드릴](./navigable-range-api-mini-drill.md)

retrieval-anchor-keywords: language-java-00122, firstEntry lastEntry vs firstKey lastKey, treemap empty firstEntry null, treemap empty firstKey exception, lastEntry lastKey empty treemap, java treemap entry null vs key exception, firstEntry null firstKey NoSuchElementException, TreeMap beginner empty bridge, firstKey lastKey firstEntry lastEntry difference, 자바 treemap firstEntry firstKey 차이, 빈 TreeMap firstEntry null, 빈 TreeMap firstKey 예외

## 먼저 잡을 mental model

`TreeMap`의 맨 앞이나 맨 뒤를 보고 싶을 때, 사실 질문이 두 종류다.

- "맨 앞 `key`만 있으면 된다"
- "맨 앞 `entry(key=value)` 전체가 필요하다"

초보자는 여기에 empty behavior까지 같이 묶어 기억하면 된다.

- `firstKey()` / `lastKey()` = key만 준다, 비어 있으면 예외
- `firstEntry()` / `lastEntry()` = entry를 준다, 비어 있으면 `null`

즉 이름이 비슷해 보여도 "반환 shape"와 "빈 map 반응"이 같이 다르다.

## 한 화면 비교표

| 질문 | 메서드 | 반환값 모양 | 빈 `TreeMap`이면 |
|---|---|---|---|
| 맨 앞 key는? | `firstKey()` | `K` | `NoSuchElementException` |
| 맨 뒤 key는? | `lastKey()` | `K` | `NoSuchElementException` |
| 맨 앞 entry는? | `firstEntry()` | `Map.Entry<K, V>` | `null` |
| 맨 뒤 entry는? | `lastEntry()` | `Map.Entry<K, V>` | `null` |

짧게 번역하면:

- `...Key()`는 "key가 있다고 보고 바로 꺼내는" 쪽
- `...Entry()`는 "entry가 없을 수도 있다고 보고 nullable하게 받는" 쪽

## 비어 있지 않을 때는 이렇게 보인다

```java
import java.util.Map;
import java.util.TreeMap;

TreeMap<Integer, String> gradeByScore = new TreeMap<>();
gradeByScore.put(60, "D");
gradeByScore.put(70, "C");
gradeByScore.put(80, "B");

System.out.println(gradeByScore.firstKey());    // 60
System.out.println(gradeByScore.lastKey());     // 80

Map.Entry<Integer, String> first = gradeByScore.firstEntry();
Map.Entry<Integer, String> last = gradeByScore.lastEntry();

System.out.println(first);                      // 60=D
System.out.println(last);                       // 80=B
System.out.println(first.getValue());           // D
```

이 장면에서는 둘 다 정상 동작한다.
차이는 "key만 바로 받는가"와 "entry 전체를 받아서 value까지 같이 볼 수 있는가"다.

## 빈 `TreeMap`에서 차이가 바로 드러난다

```java
import java.util.Map;
import java.util.TreeMap;

TreeMap<Integer, String> empty = new TreeMap<>();

Map.Entry<Integer, String> firstEntry = empty.firstEntry();
Map.Entry<Integer, String> lastEntry = empty.lastEntry();

System.out.println(firstEntry);                 // null
System.out.println(lastEntry);                  // null

System.out.println(empty.firstKey());           // NoSuchElementException
System.out.println(empty.lastKey());            // NoSuchElementException
```

왜 이렇게 다를까?

- `firstEntry()` / `lastEntry()`는 "맨 앞 entry가 없을 수도 있음"을 반환값 `null`로 표현한다
- `firstKey()` / `lastKey()`는 "맨 앞 key를 달라"는 요청이라, 줄이 비어 있으면 예외로 실패를 드러낸다

그래서 empty 가능성이 있으면 `firstEntry()` 쪽이 초보자에게 더 읽기 쉬운 경우가 많다.

## 언제 `...Entry()` 쪽이 더 편한가

`TreeMap`을 쓰는 코드는 key만 필요한 경우도 있지만, value까지 바로 써야 하는 경우가 많다.

```java
TreeMap<Integer, String> schedule = new TreeMap<>();

Map.Entry<Integer, String> first = schedule.firstEntry();
if (first == null) {
    System.out.println("예약 없음");
} else {
    System.out.println(first.getKey());
    System.out.println(first.getValue());
}
```

이 패턴이 편한 이유:

- 빈 map이면 `null` 체크 한 번으로 끝난다
- non-empty면 key와 value를 둘 다 바로 쓸 수 있다

반대로 `firstKey()`를 쓰면 비어 있지 않다는 전제를 코드가 이미 알고 있을 때 더 자연스럽다.

```java
if (schedule.isEmpty()) {
    System.out.println("예약 없음");
} else {
    Integer firstStart = schedule.firstKey();
    System.out.println(firstStart);
}
```

## 초보자 혼동 포인트

- `firstEntry()`가 `firstKey()`보다 "맨 앞" 의미가 약한 것이 아니다. 둘 다 같은 위치를 가리키지만 반환 shape가 다르다.
- `firstEntry()`가 `null`을 준다고 해서 `firstKey()`도 `null`을 줄 것이라고 묶어 생각하면 안 된다.
- `Map.Entry`가 필요 없으면 `firstKey()`가 더 단순하지만, 비어 있을 수 있는 흐름에서는 예외 처리를 먼저 의식해야 한다.
- `firstEntry()` / `lastEntry()`는 제거하지 않는다. 제거까지 원하면 `pollFirstEntry()` / `pollLastEntry()` 계열을 봐야 한다.

## 빠른 선택 가이드

| 내가 필요한 것 | 먼저 떠올릴 선택 |
|---|---|
| 맨 앞 key만 간단히 읽는다 | `firstKey()` |
| 맨 뒤 key만 간단히 읽는다 | `lastKey()` |
| key와 value를 같이 읽는다 | `firstEntry()` / `lastEntry()` |
| 빈 map 가능성이 커서 null-safe하게 읽고 싶다 | `firstEntry()` / `lastEntry()` |
| 빈 map이면 바로 버그로 보고 싶다 | `firstKey()` / `lastKey()` |

## 다음에 읽으면 좋은 문서

- `TreeMap`의 `floorEntry`/`ceilingEntry`까지 한 장으로 연결하려면 [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- `null` 반환 감각을 더 짧게 연습하려면 [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)
- 예약/시간표 예제로 entry 조회를 붙여 보고 싶다면 [TreeMap Interval Entry Primer](../data-structure/treemap-interval-entry-primer.md)
- 제거 여부까지 같이 정리하려면 [`pollFirst`/`pollLast` vs `first`/`last` Beginner Bridge](./pollfirst-polllast-vs-first-last-beginner-bridge.md)

## 한 줄 정리

빈 `TreeMap`에서 `firstEntry()`/`lastEntry()`는 "없음"을 `null`로 돌려주고, `firstKey()`/`lastKey()`는 "있어야 한다"는 전제로 예외를 던진다. 초보자는 이 차이를 `entry vs key`와 함께 묶어 기억하면 된다.
