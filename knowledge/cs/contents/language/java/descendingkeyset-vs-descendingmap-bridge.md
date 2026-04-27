# `descendingKeySet()` vs `descendingMap()` Beginner Bridge

> 한 줄 요약: `descendingKeySet()`은 **key만 보는 `NavigableSet<K>` view**이고, `descendingMap()`은 **key와 value를 함께 다루는 `NavigableMap<K, V>` view**다. 초보자는 "`key 줄만 필요하면 set view`, `entry 작업까지 필요하면 map view`"로 나누면 덜 헷갈린다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
> - [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
> - [`subMap()` / `headMap()` / `tailMap()` Live View Primer](./treemap-range-view-live-window-primer.md)
> - [`pollFirst`/`pollLast` vs `first`/`last` Beginner Bridge](./pollfirst-polllast-vs-first-last-beginner-bridge.md)

> retrieval-anchor-keywords: language-java-00119, descendingkeyset vs descendingmap, java descendingKeySet descendingMap difference, treemap descending key view vs entry view, navigablemap descendingkeyset beginner, navigablemap descendingmap beginner, java key view entry view bridge, descendingKeySet returns NavigableSet, descendingMap returns NavigableMap, TreeMap descendingKeySet example, TreeMap descendingMap example, key only view vs map view java, descending keyset common confusion, descending map entry api beginner, 자바 descendingKeySet descendingMap 차이, 자바 treemap key view entry view, 자바 descendingKeySet 는 뭐를 반환하나, 자바 descendingMap entry 조회

## 먼저 잡을 멘탈 모델

`TreeMap`을 뒤집어 보고 싶을 때 이름이 비슷한 API가 두 개 나온다.

- `descendingKeySet()`
- `descendingMap()`

초보자는 둘 다 "내림차순으로 보는 거"라는 공통점만 기억해서 자주 섞어 쓴다.
하지만 실전 구분은 단순하다.

> `descendingKeySet()`은 **key 줄만 보여 주는 set view**, `descendingMap()`은 **entry까지 다룰 수 있는 map view**다.

즉 질문을 먼저 나누면 된다.

- "내가 key만 돌면서 읽을 건가?"
- "아니면 key와 value를 같이 조회/수정할 건가?"

## 한 장 비교표

| API | 반환 타입 | 보이는 것 | 바로 쓸 수 있는 대표 API |
|---|---|---|---|
| `descendingKeySet()` | `NavigableSet<K>` | key만 | `first()`, `higher()`, `pollFirst()` |
| `descendingMap()` | `NavigableMap<K, V>` | key + value(entry) | `firstEntry()`, `higherEntry()`, `pollFirstEntry()`, `get(key)` |

짧게 붙이면 이렇다.

- `descendingKeySet()` = "내림차순 key 목록 view"
- `descendingMap()` = "내림차순 map view"

## 같은 데이터로 나란히 보기

```java
import java.util.Map;
import java.util.NavigableMap;
import java.util.NavigableSet;
import java.util.TreeMap;

TreeMap<Integer, String> scores = new TreeMap<>();
scores.put(70, "C");
scores.put(80, "B");
scores.put(90, "A");

NavigableSet<Integer> keys = scores.descendingKeySet();
NavigableMap<Integer, String> entries = scores.descendingMap();

System.out.println(keys);    // [90, 80, 70]
System.out.println(entries); // {90=A, 80=B, 70=C}
```

둘 다 같은 backing data를 뒤에서부터 읽는다.
차이는 "무엇을 꺼내 쓸 수 있느냐"다.

- `keys`는 `90`, `80`, `70` 같은 key만 준다
- `entries`는 `90=A`, `80=B`, `70=C` 같은 entry 맥락을 유지한다

## 언제 `descendingKeySet()`이 맞나

key 자체만 필요하면 set view가 더 직접적이다.

```java
Integer highest = scores.descendingKeySet().first();
System.out.println(highest); // 90
```

이 코드는 "가장 큰 key가 무엇인가?"만 묻는다.
value는 관심사가 아니다.

이런 상황에 잘 맞는다.

- 우선순위 숫자나 점수 key만 역순으로 훑고 싶을 때
- 가장 큰 key, 그다음 key 같은 key navigation만 필요할 때
- `for (Integer key : map.descendingKeySet())`처럼 key 순회가 목적일 때

## 언제 `descendingMap()`이 맞나

key만이 아니라 value까지 같이 써야 하면 map view가 맞다.

```java
Map.Entry<Integer, String> topEntry = scores.descendingMap().firstEntry();

System.out.println(topEntry.getKey());   // 90
System.out.println(topEntry.getValue()); // A
```

이 코드는 "가장 큰 key가 무엇인가?"에서 끝나지 않고,
"그 key에 연결된 value까지 같이 보고 싶다"로 이어진다.

이런 상황에 잘 맞는다.

- 가장 큰 entry 전체를 바로 꺼내고 싶을 때
- `floorEntry`, `higherEntry`, `pollFirstEntry`처럼 entry API가 필요할 때
- reversed view에서 `put`, `get`, `remove` 같은 map 연산도 계속 쓰고 싶을 때

## 초보자가 자주 섞는 포인트

### 1. `descendingKeySet()`에서 value를 바로 꺼내려는 경우

이건 안 된다.

```java
Integer key = scores.descendingKeySet().first();
String grade = scores.get(key);
```

이 코드는 가능하지만, value는 set view가 아니라 **원본 map에 다시 물어본 것**이다.

즉:

- `descendingKeySet()`이 value를 준 것이 아니다
- key를 하나 얻은 뒤 `scores.get(key)`를 따로 한 것이다

value까지 자주 필요하면 처음부터 `descendingMap()` 쪽이 읽기 쉽다.

### 2. `descendingMap()`을 "entry list"처럼 오해하는 경우

`descendingMap()`은 entry를 보여 주지만 여전히 `NavigableMap`이다.
즉 단순 결과 목록이 아니라 live view다.

```java
scores.descendingMap().put(85, "B+");
System.out.println(scores); // {70=C, 80=B, 85=B+, 90=A}
```

reversed 방향으로 보고 있어도, 수정은 원본 `scores`에 바로 반영된다.

### 3. `pollFirst()`와 `pollFirstEntry()`를 같은 것으로 읽는 경우

이 둘은 반환 모양이 다르다.

| 호출 위치 | 반환값 | 제거 대상 |
|---|---|---|
| `scores.descendingKeySet().pollFirst()` | key 하나 | 가장 큰 key entry |
| `scores.descendingMap().pollFirstEntry()` | entry 하나 | 가장 큰 key entry |

둘 다 가장 큰 key 쪽 데이터를 소비하지만:

- set view는 key만 돌려준다
- map view는 key와 value를 함께 돌려준다

## 빠른 선택 카드

| 내가 원하는 것 | 더 잘 맞는 선택 |
|---|---|
| 큰 key부터 key만 순회 | `descendingKeySet()` |
| 가장 큰 key 값만 확인 | `descendingKeySet().first()` |
| 가장 큰 entry 전체 확인 | `descendingMap().firstEntry()` |
| reversed view에서 value까지 읽기 | `descendingMap()` |
| reversed view에서 `floorEntry`/`higherEntry` 쓰기 | `descendingMap()` |

## 자주 나오는 한 줄 오해 바로잡기

- "`descendingKeySet()`도 map이니까 `get()` 되겠지" → 아니다. set view라서 `get(key)` 같은 map API는 없다.
- "`descendingMap()`은 key 순서만 바꾼 복사본이다" → 아니다. 원본과 연결된 live view다.
- "`descendingKeySet()`과 `descendingMap()`은 결과 모양만 다르고 아무거나 써도 된다" → 아니다. key-only 작업인지, entry/map 작업인지에 따라 고르는 API가 다르다.

## 다음에 읽으면 좋은 문서

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| descending view 자체가 왜 live view인지 헷갈린다 | [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md) |
| `floor`/`ceiling`/`higher`를 reversed 순서에서 어떻게 읽는지 헷갈린다 | [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md) |
| range view도 copy가 아니라 view라는 점이 헷갈린다 | [`subMap()` / `headMap()` / `tailMap()` Live View Primer](./treemap-range-view-live-window-primer.md) |
| key 소비와 조회 차이까지 같이 헷갈린다 | [`pollFirst`/`pollLast` vs `first`/`last` Beginner Bridge](./pollfirst-polllast-vs-first-last-beginner-bridge.md) |

## 한 줄 정리

`descendingKeySet()`은 **내림차순 key-only view**, `descendingMap()`은 **내림차순 entry/map view**다. key만 필요하면 전자, key와 value를 함께 다뤄야 하면 후자를 고르면 된다.
