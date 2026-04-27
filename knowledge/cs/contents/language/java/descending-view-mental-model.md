# `descendingSet()` / `descendingMap()` View Mental Model

> 한 줄 요약: `descendingSet()`과 `descendingMap()`은 데이터를 거꾸로 복사한 새 컬렉션이 아니라, **같은 데이터를 반대 순서로 읽는 view**이고, 그래서 `floor`/`ceiling` 같은 navigation 결과도 그 반대 순서를 기준으로 다시 해석된다.

**난이도: 🟢 Beginner**

관련 문서:
- [Language README](../README.md)
- [Heap vs PriorityQueue vs Ordered Map Beginner Bridge](../../data-structure/heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`pollFirst()` / `pollLast()` on Original vs Descending View Primer](./pollfirst-polllast-view-semantics-primer.md)
- [`descendingKeySet()` vs `descendingMap()` Beginner Bridge](./descendingkeyset-vs-descendingmap-bridge.md)
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
- [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)

retrieval-anchor-keywords: language-java-00077, descendingset descendingmap mental model, java descendingset beginner, java descendingmap beginner, descending view not copy, descendingmap floor ceiling confusion, descendingset floor ceiling confusion, reverse order view lookup, comparator reverseorder treeset same lookup, comparator reverseorder treemap same lookup, descendingmap vs reverseorder beginner, java reversed navigation result beginner, descendingset common confusion, descendingmap common confusion, why is descendingmap floor bigger

## 먼저 잡을 mental model

초보자 기준으로는 이 두 줄만 먼저 잡으면 된다.

- `descendingSet()` / `descendingMap()`은 **새로 정렬한 복사본**이 아니라 **원본 위에 열린 반대 방향 view**다.
- 그래서 `first`, `last`, `lower`, `floor`, `ceiling`, `higher`도 **원본 기준이 아니라 그 view가 보는 순서 기준**으로 읽어야 한다.

정렬된 줄이 원본에서 이렇게 보인다고 하자.

```text
10   20   30   40
```

`descendingSet()` view에서는 같은 데이터를 이렇게 읽는다.

```text
40   30   20   10
```

값이 바뀐 것이 아니라, **줄을 읽는 방향이 바뀐 것**이다.

## 왜 "view"라는 말이 중요한가

`descending...` API를 처음 보면 "내림차순 새 컬렉션을 하나 더 만들었나?"라고 오해하기 쉽다. 하지만 핵심은 복사가 아니라 연결이다.

| 질문 | 답 |
|---|---|
| 새 복사본인가? | 아니다. 원본을 다른 방향으로 보는 view다 |
| 데이터 저장소가 따로 있나? | 없다. backing data는 원본과 같다 |
| 한쪽에서 수정하면 다른 쪽에도 보이나? | 보인다. 같은 데이터를 보고 있기 때문이다 |
| navigation 기준은 무엇인가? | 현재 보고 있는 view의 순서 |

짧게 기억하면 다음 한 줄이다.

> `descendingSet()` / `descendingMap()`은 "같은 책을 뒤에서부터 넘겨 보는 것"에 가깝다.

## `TreeSet` 예제로 바로 보기

```java
import java.util.List;
import java.util.NavigableSet;
import java.util.TreeSet;

TreeSet<Integer> numbers = new TreeSet<>(List.of(10, 20, 30, 40));
NavigableSet<Integer> desc = numbers.descendingSet();

System.out.println(numbers); // [10, 20, 30, 40]
System.out.println(desc);    // [40, 30, 20, 10]

System.out.println(numbers.first()); // 10
System.out.println(desc.first());    // 40

System.out.println(numbers.floor(25)); // 20
System.out.println(desc.floor(25));    // 30
```

여기서 가장 중요한 포인트는 마지막 두 줄이다.

- 원본 줄에서 `25`의 `floor`는 `20`이다
- descending view 줄에서 `25`의 `floor`는 `30`이다

왜냐하면 `floor`는 "숫자상 더 작은 값"을 찾는 버튼이 아니라, **현재 줄에서 같거나 바로 앞쪽**을 찾는 버튼이기 때문이다.

## navigation 결과가 왜 뒤집혀 보이나

같은 질문을 원본 줄과 descending view 줄에 나란히 적어 보면 헷갈림이 크게 줄어든다.

- 원본 줄: `10 -> 20 -> 30 -> 40`
- descending view 줄: `40 -> 30 -> 20 -> 10`

| query `25` | 원본 `numbers` | descending view `desc` |
|---|---|---|
| `floor(25)` | `20` | `30` |
| `ceiling(25)` | `30` | `20` |
| `lower(30)` | `20` | `40` |
| `higher(30)` | `40` | `20` |

읽는 법은 늘 같다.

- `floor`: 현재 줄에서 같거나 바로 앞
- `ceiling`: 현재 줄에서 같거나 바로 뒤
- `lower`: 현재 줄에서 바로 앞, 단 exact match 제외
- `higher`: 현재 줄에서 바로 뒤, 단 exact match 제외

즉 descending view에서 결과가 "뒤집힌다"기보다, **앞/뒤의 기준선 자체가 바뀐다**고 보는 편이 정확하다.

## `TreeMap`에서도 key 줄을 반대로 읽는다

`descendingMap()`도 value를 뒤집는 것이 아니다. key 줄을 반대로 읽는 view다.

```java
import java.util.Map;
import java.util.NavigableMap;
import java.util.TreeMap;

TreeMap<Integer, String> grades = new TreeMap<>();
grades.put(0, "F");
grades.put(60, "D");
grades.put(70, "C");
grades.put(80, "B");
grades.put(90, "A");

NavigableMap<Integer, String> desc = grades.descendingMap();

System.out.println(grades.floorEntry(87)); // 80=B
System.out.println(desc.floorEntry(87));   // 90=A
```

원본 key 줄과 descending key 줄은 이렇게 읽으면 된다.

- 원본: `0 -> 60 -> 70 -> 80 -> 90`
- descending view: `90 -> 80 -> 70 -> 60 -> 0`

그래서 `descendingMap().floorEntry(87)`은 숫자상 더 작은 `80`이 아니라, descending 줄에서 `87`과 같거나 바로 앞쪽인 `90`을 돌려준다.

`TreeMap`에서도 원리는 동일하다.

- navigation은 value가 아니라 key 기준이다
- descending view에서는 그 key 줄의 방향이 반대다
- 그래서 `floorEntry`, `ceilingEntry`, `lowerEntry`, `higherEntry`도 반대 방향 감각으로 읽힌다

## `reverseOrder()` 컬렉션과 읽는 법은 같다

여기서 초보자가 한 번 더 헷갈리는 지점이 있다.

- `descendingSet()` / `descendingMap()` view
- `new TreeSet<>(Comparator.reverseOrder())`
- `new TreeMap<>(Comparator.reverseOrder())`

이 셋은 "만들어진 방식"은 다르지만, **지금 보고 있는 comparator 줄이 같으면 조회 규칙도 같다.**

| 비교 대상 | 보이는 줄 | `floor(25)` / `floorEntry(87)` 읽는 법 |
|---|---|---|
| `numbers.descendingSet()` | `40 -> 30 -> 20 -> 10` | 그 줄에서 같거나 바로 앞 |
| `new TreeSet<>(Comparator.reverseOrder())` | `40 -> 30 -> 20 -> 10` | 그 줄에서 같거나 바로 앞 |
| `grades.descendingMap()` | `90 -> 80 -> 70 -> 60 -> 0` | 그 key 줄에서 같거나 바로 앞 |
| `new TreeMap<>(Comparator.reverseOrder())` | `90 -> 80 -> 70 -> 60 -> 0` | 그 key 줄에서 같거나 바로 앞 |

즉 `descendingSet().floor(25)`가 `30`이고, 같은 값을 담은 reverse comparator `TreeSet`의 `floor(25)`도 `30`이다.
`descendingMap().floorEntry(87)`가 `90=A`라면, 같은 key를 reverse comparator로 만든 `TreeMap`도 `90=A`를 돌려준다.

차이는 조회 규칙이 아니라 **컬렉션의 정체**다.

- `descending...`은 기존 컬렉션 위에 열린 view다
- `Comparator.reverseOrder()` 컬렉션은 그 comparator를 기본 규칙으로 가진 별도 컬렉션이다

그래서 "왜 둘 다 `floor`가 더 큰 값을 주지?"라는 질문에는 같은 답을 쓰면 된다.

> 둘 다 현재 읽는 comparator 줄에서 `floor`를 계산하기 때문이다.

## 원본과 descending view는 함께 움직인다

view semantics를 가장 짧게 확인하는 코드는 이것이다.

```java
TreeSet<Integer> numbers = new TreeSet<>(List.of(10, 20, 30));
NavigableSet<Integer> desc = numbers.descendingSet();

numbers.add(40);
System.out.println(desc); // [40, 30, 20, 10]

desc.remove(20);
System.out.println(numbers); // [10, 30, 40]
```

한쪽 수정이 다른 쪽에 바로 보이는 이유는 둘이 같은 backing data를 보기 때문이다.

초보자 입장에서는 이 정도만 기억하면 충분하다.

- `descending...`은 snapshot이 아니다
- 원본과 분리된 사본이 아니다
- 한쪽 변화가 다른 쪽에도 반영된다

## 초보자가 자주 헷갈리는 지점

- `descendingSet()` / `descendingMap()`은 새 컬렉션 복사본이 아니다.
- "내림차순이니까 무조건 작은 값 쪽으로 간다"라고 읽으면 `floor`/`ceiling`을 자주 반대로 해석하게 된다.
- `first()`와 `last()`도 원본 기준이 아니라 descending view 기준으로 바뀐다.
- `TreeMap`에서는 여전히 value가 아니라 key를 기준으로 navigation한다.
- `descendingMap().floorEntry(x)`와 `map.floorEntry(x)`는 같은 뜻이 아니다.
- reverse comparator를 준 `TreeSet`/`TreeMap`과 `descending...` view는 조회 규칙은 같아 보일 수 있지만, 하나는 별도 컬렉션이고 다른 하나는 기존 컬렉션 위의 reversed view다.

## 빠른 비교 카드

| 보고 있는 것 | `first()` | `floor(25)` on `10,20,30,40` |
|---|---:|---:|
| 원본 `TreeSet` | `10` | `20` |
| `descendingSet()` view | `40` | `30` |

이 표만 기억해도 핵심 오해 하나는 줄어든다.

- 값 집합은 같다
- 읽는 방향이 다르다
- navigation 결과도 그 방향을 따른다

## 다음 읽기

- `lower`/`floor`/`ceiling`/`higher` 전체 mental model을 먼저 묶고 싶다면 [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- `pollFirst`/`pollLast`가 원본과 descending view에서 정확히 어느 쪽 끝을 제거하는지 따로 보고 싶다면 [`pollFirst()` / `pollLast()` on Original vs Descending View Primer](./pollfirst-polllast-view-semantics-primer.md)
- range view까지 포함해 "view" 감각을 넓히고 싶다면 [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- reverse comparator와 descending view를 구분해서 보고 싶다면 [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
- `descendingKeySet()`과 `descendingMap()`을 왜 같은 descending 계열이어도 다르게 골라야 하는지 짧게 정리하려면 [`descendingKeySet()` vs `descendingMap()` Beginner Bridge](./descendingkeyset-vs-descendingmap-bridge.md)
- natural ordering과 comparator가 sorted collection 동작을 어떻게 정하는지 다시 묶고 싶다면 [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)

## 한 줄 정리

`descendingSet()`과 `descendingMap()`은 데이터를 뒤집어 복사한 컬렉션이 아니라 같은 데이터를 반대 순서로 읽는 view이므로, navigation 결과도 "숫자 감각"이 아니라 **그 reversed view의 앞/뒤 기준**으로 해석해야 한다.
