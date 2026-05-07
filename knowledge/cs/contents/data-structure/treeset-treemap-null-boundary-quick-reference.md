---
schema_version: 3
title: TreeSet, TreeMap Null-Boundary Quick Reference
concept_id: data-structure/treeset-treemap-null-boundary-quick-reference
canonical: false
category: data-structure
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- navigable-null-boundary
- treeset-treemap-null
- first-vs-neighbor-failure
aliases:
- TreeSet TreeMap null boundary
- NavigableSet null return
- NavigableMap null return
- firstKey firstEntry null
- floor ceiling null
- ordered set map boundary
- TreeSet TreeMap NPE beginner
symptoms:
- TreeSet TreeMap에서 못 찾으면 모두 예외라고 생각해 lower floor ceiling higher의 null 반환을 놓친다
- firstKey와 firstEntry가 모두 first 계열이라 empty behavior도 같다고 오해한다
- floor ceiling null을 exact match 부재로만 해석하고 해당 방향 후보 자체가 없다는 의미를 구분하지 못한다
intents:
- definition
- troubleshooting
prerequisites:
- data-structure/treeset-exact-match-drill
- data-structure/treemap-key-entry-strictness-bridge
next_docs:
- data-structure/treemap-null-boundary-micro-drill
- data-structure/treemap-firstkey-firstentry-floorkey-floorentry-return-shape-card
- data-structure/treemap-key-entry-strictness-bridge
linked_paths:
- contents/data-structure/treemap-firstkey-firstentry-floorkey-floorentry-return-shape-card.md
- contents/data-structure/treemap-null-boundary-micro-drill.md
- contents/data-structure/treeset-exact-match-drill.md
- contents/data-structure/treemap-neighbor-query-micro-drill.md
- contents/data-structure/treemap-interval-entry-primer.md
- contents/language/java/navigablemap-navigableset-mental-model.md
- contents/language/java/ordered-map-null-safe-practice-drill.md
- contents/language/java/firstentry-lastentry-vs-firstkey-lastkey-bridge.md
confusable_with:
- data-structure/treemap-null-boundary-micro-drill
- data-structure/treemap-firstkey-firstentry-floorkey-floorentry-return-shape-card
- data-structure/treeset-exact-match-drill
- data-structure/treemap-key-entry-strictness-bridge
forbidden_neighbors: []
expected_queries:
- TreeSet TreeMap에서 first 계열과 lower floor ceiling higher 계열은 null과 예외가 어떻게 달라?
- TreeMap firstKey는 empty에서 예외인데 firstEntry는 null이라는 걸 정리해줘
- floor ceiling lower higher가 경계 밖에서 null을 줄 수 있는 이유는?
- NavigableSet NavigableMap null boundary를 NPE 안 나게 빠르게 확인하고 싶어
- ordered set map에서 못 찾으면 null인지 예외인지 구분하는 quick reference가 필요해
contextual_chunk_prefix: |
  이 문서는 TreeSet과 TreeMap의 null boundary를 quick reference로 정리한다.
  first/last key 계열의 empty exception, firstEntry/lastEntry의 null, lower/floor/
  ceiling/higher neighbor 계열의 boundary null을 beginner-safe하게 분리한다.
---
# TreeSet, TreeMap Null-Boundary Quick Reference

> 한 줄 요약: `TreeSet`/`TreeMap`에서 "`못 찾으면 예외인가, null인가?`"만 먼저 분리하면 `first` 계열과 `floor/ceiling/lower/higher` 계열 첫 사용 NPE 혼동을 크게 줄일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [TreeMap `firstKey` vs `firstEntry`, `floorKey` vs `floorEntry` Return-Shape Card](./treemap-firstkey-firstentry-floorkey-floorentry-return-shape-card.md)
- [TreeMap Null Boundary Micro Drill](./treemap-null-boundary-micro-drill.md)
- [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md)
- [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
- [Ordered Map Null-Safe Practice Drill](../language/java/ordered-map-null-safe-practice-drill.md)
- [`firstEntry()`/`lastEntry()` vs `firstKey()`/`lastKey()` Beginner Bridge](../language/java/firstentry-lastentry-vs-firstkey-lastkey-bridge.md)

retrieval-anchor-keywords: treeset treemap null boundary quick reference, navigableset null return beginner, navigablemap null return beginner, treeset first floor ceiling null, treemap firstkey firstentry null, ordered set map null boundary, tree set tree map npe 처음, floor ceiling null 왜 나와요, firstkey firstentry 헷갈려요, treeset treemap null safe basics, ordered map set boundary primer, what is navigableset null return

## 핵심 개념

처음엔 메서드 이름을 다 외우기보다 아래 한 줄만 먼저 고정하면 된다.

> `first`/`last`는 "맨 앞이나 맨 뒤가 반드시 있어야 한다" 쪽이고, `lower`/`floor`/`ceiling`/`higher`는 "그 방향 이웃이 없을 수도 있다" 쪽이다.

그래서 beginner가 가장 자주 헷갈리는 경계는 두 종류다.

- 컬렉션이 비어 있을 때
- 찾는 기준값이 맨 왼쪽이나 맨 오른쪽 경계를 벗어났을 때

이 문서는 `TreeSet`과 `TreeMap`에서 그 둘을 1장으로 자르는 카드다.

## 한눈에 보기

| 구조 | 호출 | 비어 있을 때 | 경계를 벗어났을 때 |
|---|---|---|---|
| `TreeSet` | `first()`, `last()` | `NoSuchElementException` | 기준값 없음 |
| `TreeSet` | `lower(x)`, `floor(x)`, `ceiling(x)`, `higher(x)` | `null` | 그 방향 이웃이 없으면 `null` |
| `TreeMap` | `firstKey()`, `lastKey()` | `NoSuchElementException` | 기준값 없음 |
| `TreeMap` | `firstEntry()`, `lastEntry()` | `null` | 기준값 없음 |
| `TreeMap` | `lowerKey(x)`, `floorKey(x)`, `ceilingKey(x)`, `higherKey(x)` | `null` | 그 방향 이웃이 없으면 `null` |
| `TreeMap` | `lowerEntry(x)`, `floorEntry(x)`, `ceilingEntry(x)`, `higherEntry(x)` | `null` | 그 방향 이웃이 없으면 `null` |

짧게 외우면 아래처럼 끝난다.

- `first()/last()/firstKey()/lastKey()` -> 비면 예외
- `firstEntry()/lastEntry()` -> 비면 `null`
- `lower/floor/ceiling/higher` 계열 -> 이웃이 없으면 `null`

## TreeSet에서 먼저 보는 경계

`TreeSet<Integer>`에 `[10, 20, 30]`이 있다고 하자.

| 질문 | 호출 | 결과 |
|---|---|---|
| 빈 set에서 첫 값 보기 | `empty.first()` | `NoSuchElementException` |
| `10`보다 왼쪽 이웃 찾기 | `set.lower(10)` | `null` |
| `5` 이하 가장 가까운 값 찾기 | `set.floor(5)` | `null` |
| `30`보다 오른쪽 이웃 찾기 | `set.higher(30)` | `null` |
| `35` 이상 가장 가까운 값 찾기 | `set.ceiling(35)` | `null` |

여기서 중요한 건 `null`이 "버그"가 아니라 "`그 방향에 값이 없음`"이라는 정상 신호라는 점이다.

```java
NavigableSet<Integer> scores = new TreeSet<>(List.of(10, 20, 30));

Integer next = scores.ceiling(35); // null
```

위 코드는 실패가 아니라 "35 이상 점수가 없음"이라는 뜻이다.

## TreeMap에서 먼저 보는 경계

`TreeMap<Integer, String>`에 `(10, "A"), (20, "B"), (30, "C")`가 있다고 하자.

| 질문 | 호출 | 결과 |
|---|---|---|
| 빈 map에서 첫 key 보기 | `empty.firstKey()` | `NoSuchElementException` |
| 빈 map에서 첫 entry 보기 | `empty.firstEntry()` | `null` |
| `10`보다 왼쪽 key 찾기 | `map.lowerKey(10)` | `null` |
| `5` 이하 entry 찾기 | `map.floorEntry(5)` | `null` |
| `30`보다 오른쪽 key 찾기 | `map.higherKey(30)` | `null` |
| `35` 이상 key 찾기 | `map.ceilingKey(35)` | `null` |

초보자에게 특히 헷갈리는 쌍은 이것이다.

- `firstKey()`는 비어 있으면 예외
- `firstEntry()`는 비어 있으면 `null`

즉 "`맨 앞`을 읽는다"는 공통점만 보고 둘을 같은 실패 방식으로 묶으면 안 된다.

## 흔한 오해와 함정

- "`TreeMap`에서 못 찾으면 다 예외 아닌가요?"
  아니다. `firstKey()`/`lastKey()`는 예외지만, `floorKey()`나 `ceilingEntry()`는 `null`로 실패를 표현한다.
- "`TreeSet.floor()`가 `null`이면 바로 산술 연산해도 되나요?"
  안 된다. `Integer prev = set.floor(x);` 다음에 바로 `prev + 1`을 하면 NPE가 날 수 있다.
- "`firstEntry()`도 `firstKey()`처럼 비면 터지나요?"
  아니다. `firstEntry()`/`lastEntry()`는 `null`을 준다.
- "`null`이면 exact match가 없다는 뜻인가요?"
  꼭 그렇진 않다. 더 넓게는 그 방향에 후보 자체가 없다는 뜻이다.

beginner 체크 문장 하나로 줄이면 이렇다.

> "이 메서드는 '반드시 있어야 하는 자리'를 읽나, 아니면 '없을 수도 있는 이웃'을 읽나?"

## 실무에서 쓰는 모습

예약 시각을 `TreeSet<LocalTime>`이나 `TreeMap<LocalTime, Reservation>`으로 다룰 때 가장 흔한 실수는 `ceiling`이나 `higher`가 항상 값을 줄 거라고 가정하는 것이다.

```java
LocalTime next = reservationStarts.ceiling(targetTime);
if (next == null) {
    return "다음 예약 없음";
}
return next.toString();
```

`TreeMap`도 감각은 같다.

```java
Map.Entry<LocalTime, Reservation> next = reservations.ceilingEntry(targetTime);
if (next == null) {
    return "다음 예약 없음";
}
return next.getValue().name();
```

즉 처음엔 "`경계를 벗어나면 null일 수 있다`"를 먼저 코드에 드러내는 편이 안전하다.

## 더 깊이 가려면

- 예약표에서 `lowerEntry`/`floorEntry`/`ceilingEntry`/`higherEntry`가 첫 슬롯과 마지막 슬롯 바깥에서 왜 `null`인지 짧게 손으로 맞히고 싶다면 [TreeMap Null Boundary Micro Drill](./treemap-null-boundary-micro-drill.md)
- `TreeSet` 쪽 exact match 감각을 먼저 손으로 맞히고 싶다면 [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md)
- `TreeMap` 쪽 strict/inclusive 차이를 예약표로 보고 싶다면 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- `entry` 반환이 왜 `null`인지 더 짧게 분리하고 싶다면 [Ordered Map Null-Safe Practice Drill](../language/java/ordered-map-null-safe-practice-drill.md)
- `firstKey()`/`firstEntry()`와 `floorKey()`/`floorEntry()`를 반환 shape 기준으로 한 장에서 같이 보고 싶다면 [TreeMap `firstKey` vs `firstEntry`, `floorKey` vs `floorEntry` Return-Shape Card](./treemap-firstkey-firstentry-floorkey-floorentry-return-shape-card.md)
- `firstKey()`와 `firstEntry()` empty behavior만 따로 고정하고 싶다면 [`firstEntry()`/`lastEntry()` vs `firstKey()`/`lastKey()` Beginner Bridge](../language/java/firstentry-lastentry-vs-firstkey-lastkey-bridge.md)

## 한 줄 정리

`TreeSet`/`TreeMap`에서 beginner가 먼저 외울 규칙은 "`first` 계열은 비면 예외일 수 있고, `lower/floor/ceiling/higher` 계열은 이웃이 없으면 `null`일 수 있다"는 한 줄이다.
