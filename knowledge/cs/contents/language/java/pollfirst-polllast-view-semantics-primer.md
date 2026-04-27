# `pollFirst()` / `pollLast()` on Original vs Descending View Primer

> 한 줄 요약: `pollFirst()` / `pollLast()`는 **현재 보고 있는 순서의 양 끝**에서 값을 꺼내며, `descendingSet()` / `descendingMap()` view에서 호출하면 원본의 반대쪽 끝이 제거된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [`pollFirst`/`pollLast` vs `first`/`last` Beginner Bridge](./pollfirst-polllast-vs-first-last-beginner-bridge.md)
- [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`subMap()` / `headMap()` / `tailMap()` Live View Primer](./treemap-range-view-live-window-primer.md)

retrieval-anchor-keywords: language-java-00120, pollfirst polllast descending view semantics, descendingset pollfirst polllast beginner, original vs descending pollfirst java, descendingset pollfirst removes largest, descendingset polllast removes smallest, java pollfirst current view order, java polllast current view order, treeset descending view mutation reflected, descending view is live pollfirst, treemap descendingmap pollfirstentry semantics, java navigableset pollfirst descending beginner, 자바 descendingset pollfirst polllast, 자바 원본 descending view pollfirst 차이, 자바 pollfirst 는 현재 view 기준

## 먼저 잡을 멘탈 모델

초보자는 이 두 줄만 먼저 기억하면 된다.

- `pollFirst()` = **현재 view의 맨 앞**을 꺼내고 제거
- `pollLast()` = **현재 view의 맨 뒤**를 꺼내고 제거

그래서 원본 `TreeSet`과 `descendingSet()` view는 같은 데이터를 보더라도, "앞"과 "뒤"의 뜻이 다르다.

```text
원본 numbers:   10 -> 20 -> 30 -> 40
descending view: 40 -> 30 -> 20 -> 10
```

즉 `descendingSet().pollFirst()`는 descending view에서 맨 앞인 `40`을 꺼내고, 그 결과 원본에서도 `40`이 사라진다.

## 한 화면 비교표

`TreeSet<Integer> numbers = [10, 20, 30, 40]`라고 하자.

| 어디서 호출하나 | `pollFirst()` | `pollLast()` |
|---|---|---|
| 원본 `numbers` | `10` 반환, `10` 제거 | `40` 반환, `40` 제거 |
| `numbers.descendingSet()` | `40` 반환, 원본의 `40` 제거 | `10` 반환, 원본의 `10` 제거 |

핵심은 이것이다.

- 원본에서는 `first = 작은 쪽`, `last = 큰 쪽`
- descending view에서는 `first = 큰 쪽`, `last = 작은 쪽`

즉 `poll...`이 "숫자상 작은 값/큰 값을 고정적으로 제거한다"고 외우면 안 되고, **현재 줄의 앞/뒤를 제거한다**고 읽어야 한다.

## 작은 mutation 예제

```java
import java.util.List;
import java.util.NavigableSet;
import java.util.TreeSet;

TreeSet<Integer> numbers = new TreeSet<>(List.of(10, 20, 30, 40));
NavigableSet<Integer> desc = numbers.descendingSet();

System.out.println(desc.pollFirst()); // 40
System.out.println(numbers);          // [10, 20, 30]

System.out.println(numbers.pollFirst()); // 10
System.out.println(desc);                // [30, 20]
```

이 코드는 두 가지를 한 번에 보여 준다.

1. `desc.pollFirst()`는 descending view의 맨 앞인 `40`을 꺼낸다.
2. 그 제거가 view 안에서만 끝나지 않고 원본 `numbers`에도 바로 반영된다.

즉 `descendingSet()`은 복사본이 아니라 **같은 데이터를 반대 방향으로 보는 live view**다.

## 왜 이런 결과가 나오나

`descendingSet()`은 새 `TreeSet`을 하나 더 만드는 API가 아니다.

| 질문 | 답 |
|---|---|
| 새 복사본인가? | 아니다 |
| backing data가 같은가? | 예 |
| 한쪽에서 제거하면 다른 쪽에서도 보이나? | 예 |
| `pollFirst` 기준은 무엇인가? | 현재 보고 있는 view의 앞쪽 |

그래서 아래 둘은 다른 뜻이다.

- `numbers.pollFirst()` = 원본 줄의 맨 앞 제거
- `numbers.descendingSet().pollFirst()` = reversed view 줄의 맨 앞 제거

결과적으로 제거되는 실제 원소도 반대쪽이 된다.

## `TreeMap`도 같은 규칙이다

`TreeMap`에서는 이름만 `pollFirstEntry()` / `pollLastEntry()`로 바뀌고 원리는 같다.

| 어디서 호출하나 | 앞쪽에서 제거되는 entry |
|---|---|
| 원본 `map.pollFirstEntry()` | 가장 작은 key entry |
| `map.descendingMap().pollFirstEntry()` | 가장 큰 key entry |

즉 set에서는 원소 자체를 꺼내고, map에서는 key 순서의 entry를 꺼내지만, 둘 다 **현재 view의 앞/뒤**를 기준으로 동작한다.

## 자주 헷갈리는 포인트

- `descendingSet().pollFirst()`가 "원본의 첫 번째"를 제거하는 것은 아니다.
- descending view에서의 `first`는 원본의 `last` 쪽에 가깝다.
- `poll...` 호출은 조회만 하는 것이 아니라 실제로 데이터를 제거한다.
- descending view에서 제거해도 원본에는 남아 있지 않다. 같은 backing data를 보기 때문이다.

## 빠른 기억 카드

| 표현 | 실제 의미 |
|---|---|
| 원본 `pollFirst()` | 가장 작은 쪽 제거 |
| 원본 `pollLast()` | 가장 큰 쪽 제거 |
| descending view `pollFirst()` | 원본의 가장 큰 쪽 제거 |
| descending view `pollLast()` | 원본의 가장 작은 쪽 제거 |

## 다음 읽기

- `first`/`last`와 `pollFirst`/`pollLast`의 remove 차이를 먼저 따로 묶고 싶다면 [`pollFirst`/`pollLast` vs `first`/`last` Beginner Bridge](./pollfirst-polllast-vs-first-last-beginner-bridge.md)
- descending view 자체가 왜 live view인지 다시 보고 싶다면 [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
- `floor`/`ceiling`까지 포함한 전체 navigation 감각을 묶고 싶다면 [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)

## 한 줄 정리

`pollFirst()` / `pollLast()`는 "숫자상 작은 값/큰 값"이 아니라 **현재 view의 앞/뒤**를 제거하므로, descending view에서는 원본의 반대쪽 끝이 제거된다고 기억하면 된다.
