---
schema_version: 3
title: '`pollFirst`/`pollLast` vs `first`/`last` Beginner Bridge'
concept_id: language/pollfirst-polllast-vs-first-last-beginner-bridge
canonical: false
category: language
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- poll-vs-peek-semantics
- navigable-collection-removal-semantics
- empty-collection-null-vs-exception
aliases:
- pollfirst polllast first last beginner
- java pollfirst vs first
- java polllast vs last
- treeset pollfirst first difference
- empty treeset first exception
- empty treeset pollfirst null
- first last vs pollfirst polllast
- treemap pollfirstentry firstentry difference
- firstkey vs firstentry vs pollfirstentry
- 자바 pollfirst first 차이
- 자바 polllast last 차이
- treemap pollfirstentry firstentry 차이
- 언제 firstentry 말고 pollfirstentry
- firstentry pollfirstentry 헷갈려요
- remove 여부로 고르기
symptoms:
- first와 pollFirst가 둘 다 맨 앞을 보는 것처럼 보여서 제거 여부를 자꾸 놓쳐
- 빈 TreeSet에서 어떤 메서드는 null이고 어떤 메서드는 예외라서 외우기가 안 돼
- TreeMap에서 firstEntry와 pollFirstEntry 차이까지 한 번에 섞여서 헷갈려
intents:
- comparison
prerequisites:
- language/java-collections-basics
- language/navigablemap-navigableset-mental-model
- language/firstentry-lastentry-vs-firstkey-lastkey-bridge
next_docs:
- language/pollfirst-polllast-view-semantics-primer
- language/ordered-map-null-safe-practice-drill
- language/descendingkeyset-vs-descendingmap-bridge
linked_paths:
- contents/language/java/java-collections-basics.md
- contents/language/java/navigablemap-navigableset-mental-model.md
- contents/language/java/firstentry-lastentry-vs-firstkey-lastkey-bridge.md
- contents/language/java/pollfirst-polllast-view-semantics-primer.md
- contents/language/java/submap-boundaries-primer.md
- contents/language/java/treeset-treemap-natural-ordering-compareto-bridge.md
- contents/language/java/ordered-map-null-safe-practice-drill.md
- contents/language/java/descendingkeyset-vs-descendingmap-bridge.md
confusable_with:
- language/firstentry-lastentry-vs-firstkey-lastkey-bridge
- language/pollfirst-polllast-view-semantics-primer
- language/navigablemap-navigableset-mental-model
forbidden_neighbors: []
expected_queries:
- TreeSet에서 first와 pollFirst를 어떤 기준으로 고르는지 입문자용으로 알려줘
- pollLast가 last와 달리 컬렉션을 바꾼다는 점을 한 번에 이해하고 싶어
- 빈 정렬 컬렉션에서 null과 예외가 갈리는 이유를 pollFirst 기준으로 설명해줘
- firstEntry와 pollFirstEntry를 remove 여부 중심으로 비교한 자바 브리지가 필요해
- 양 끝을 보기만 할지 꺼내면서 제거할지 고르는 기준을 짧게 정리해줘
contextual_chunk_prefix: |
  이 문서는 Java 정렬 컬렉션을 처음 배우는 학습자가 양 끝 값을 보기만 할지 꺼내면서 없앨지, 빈 컬렉션에서 null과 예외가 왜 달라지는지 연결하는 bridge다. 맨 앞만 확인하고 싶음, 꺼낸 뒤 컬렉션에서도 사라져야 함, 끝값 소비와 단순 조회 구분, 빈 상태 안전 처리, remove 여부로 API 고르기 같은 자연어 표현이 본 문서의 판단 기준에 매핑된다.
---
# `pollFirst`/`pollLast` vs `first`/`last` Beginner Bridge

> 한 줄 요약: `first`/`last`는 양 끝값을 "보기만" 하는 조회이고, `pollFirst`/`pollLast`는 양 끝값을 "꺼내면서 제거"하는 소비다. 초보자는 먼저 **remove 여부**와 **빈 컬렉션일 때의 반응**을 같이 붙여 기억하면 된다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: pollfirst polllast vs first last beginner bridge basics, pollfirst polllast vs first last beginner bridge beginner, pollfirst polllast vs first last beginner bridge intro, java basics, beginner java, 처음 배우는데 pollfirst polllast vs first last beginner bridge, pollfirst polllast vs first last beginner bridge 입문, pollfirst polllast vs first last beginner bridge 기초, what is pollfirst polllast vs first last beginner bridge, how to pollfirst polllast vs first last beginner bridge
> 관련 문서:
> - [Language README](../README.md)
> - [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
> - [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
> - [`firstEntry()`/`lastEntry()` vs `firstKey()`/`lastKey()` Beginner Bridge](./firstentry-lastentry-vs-firstkey-lastkey-bridge.md)
> - [`pollFirst()` / `pollLast()` on Original vs Descending View Primer](./pollfirst-polllast-view-semantics-primer.md)
> - [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
> - [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)

> retrieval-anchor-keywords: language-java-00078, poll first last bridge, pollfirst polllast first last beginner, java pollFirst vs first, java pollLast vs last, treeset pollFirst first difference, treeset pollLast last difference, navigableset pollFirst removes, navigableset first no remove, empty treeset first exception, empty treeset pollFirst null, first last vs pollFirst pollLast, java sorted collection remove while reading, treemap pollFirstEntry firstEntry difference, treemap pollLastEntry lastEntry difference, firstKey vs firstEntry vs pollFirstEntry, firstEntry vs firstKey empty behavior, junior collections removal semantics, 자바 pollFirst first 차이, 자바 pollLast last 차이, 트리셋 first 는 제거 안 함, 트리셋 pollFirst 는 제거, 빈 TreeSet first 예외, 빈 TreeSet pollFirst null, TreeMap pollFirstEntry firstEntry 차이

## 먼저 잡을 멘탈 모델

정렬된 줄이 있다고 생각하자.

```text
10   20   30   40
```

이때 양 끝을 다루는 질문은 둘로 나뉜다.

- "`맨 앞 값을 보기만` 할까?"
- "`맨 앞 값을 꺼내고 줄에서도 없앨`까?"

초보자 기준으로는 이 한 줄이 핵심이다.

- `first()` / `last()` = 조회
- `pollFirst()` / `pollLast()` = 조회 + 제거

즉 `poll...`은 "peek 비슷한 이름"이 아니라, **꺼낸 뒤 컬렉션 크기까지 바꾸는 메서드**다.

## 한 화면 비교표

`TreeSet` 같은 `NavigableSet`에서 먼저 보면 가장 단순하다.

| 메서드 | 무슨 일을 하나 | 호출 뒤 컬렉션 변화 | 비어 있으면 |
|---|---|---|---|
| `first()` | 가장 앞 원소를 반환 | 변화 없음 | `NoSuchElementException` |
| `last()` | 가장 뒤 원소를 반환 | 변화 없음 | `NoSuchElementException` |
| `pollFirst()` | 가장 앞 원소를 반환하고 제거 | 맨 앞 원소가 사라짐 | `null` |
| `pollLast()` | 가장 뒤 원소를 반환하고 제거 | 맨 뒤 원소가 사라짐 | `null` |

입문자는 아래 두 쌍으로 묶어 기억하면 실수가 줄어든다.

- `first` vs `pollFirst`: 둘 다 맨 앞을 보지만, `pollFirst`만 제거한다
- `last` vs `pollLast`: 둘 다 맨 뒤를 보지만, `pollLast`만 제거한다

## `TreeSet` 예제로 바로 보기

```java
import java.util.List;
import java.util.TreeSet;

TreeSet<Integer> numbers = new TreeSet<>(List.of(10, 20, 30));

System.out.println(numbers.first());      // 10
System.out.println(numbers);              // [10, 20, 30]

System.out.println(numbers.pollFirst());  // 10
System.out.println(numbers);              // [20, 30]

System.out.println(numbers.last());       // 30
System.out.println(numbers);              // [20, 30]

System.out.println(numbers.pollLast());   // 30
System.out.println(numbers);              // [20]
```

읽는 순서를 붙여 쓰면 더 명확하다.

1. `first()`는 `10`을 보여 주지만 set은 그대로다.
2. `pollFirst()`도 `10`을 돌려주지만, 이번에는 set에서 `10`이 실제로 빠진다.
3. `last()`는 `30`을 보여 주지만 set은 그대로다.
4. `pollLast()`는 `30`을 돌려주고 set에서도 제거한다.

즉 `poll...`은 "가장자리 원소를 하나 소비한다"는 감각으로 읽는 편이 안전하다.

## 빈 컬렉션에서 왜 다르게 반응할까

초보자가 가장 많이 부딪히는 차이는 여기다.

```java
TreeSet<Integer> empty = new TreeSet<>();

System.out.println(empty.pollFirst()); // null
System.out.println(empty.pollLast());  // null

System.out.println(empty.first());     // NoSuchElementException
System.out.println(empty.last());      // NoSuchElementException
```

이 차이는 "비어 있는 것을 정상 흐름으로 볼지"에 가깝다.

- `first()` / `last()`는 "반드시 있어야 한다"는 쪽에 가깝다
- `pollFirst()` / `pollLast()`는 "없으면 그냥 `null`로 알려 줄게"에 가깝다

그래서 비어 있을 수도 있는 queue-like 소비 흐름에서는 `poll...`이 편하고,
"비어 있으면 버그에 가깝다"는 전제에서는 `first`/`last`가 더 빨리 문제를 드러낸다.

## `TreeMap`에서는 이름이 조금 달라진다

`TreeMap`은 원소 자체가 아니라 entry를 다루므로 이름이 조금 바뀐다.

| 질문 | 제거 안 함 | 제거함 | 비어 있으면 |
|---|---|---|---|
| 맨 앞 entry | `firstEntry()` | `pollFirstEntry()` | 둘 다 `null` |
| 맨 뒤 entry | `lastEntry()` | `pollLastEntry()` | 둘 다 `null` |
| 맨 앞 key | `firstKey()` | 없음 | 비면 `NoSuchElementException` |
| 맨 뒤 key | `lastKey()` | 없음 | 비면 `NoSuchElementException` |

여기서 초보자가 특히 헷갈리는 포인트는 이것이다.

- `firstKey()`는 key만 주고, 비어 있으면 예외다
- `firstEntry()`는 entry를 주고, 비어 있으면 `null`이다
- `pollFirstEntry()`는 entry를 주고, 그 entry를 map에서도 제거한다

이 empty behavior 차이만 따로 짧게 붙잡고 싶다면 [`firstEntry()`/`lastEntry()` vs `firstKey()`/`lastKey()` Beginner Bridge](./firstentry-lastentry-vs-firstkey-lastkey-bridge.md)를 보면 된다.

## `TreeMap` 예제

```java
import java.util.TreeMap;

TreeMap<Integer, String> gradeByScore = new TreeMap<>();
gradeByScore.put(60, "D");
gradeByScore.put(70, "C");
gradeByScore.put(80, "B");

System.out.println(gradeByScore.firstEntry());     // 60=D
System.out.println(gradeByScore);                  // {60=D, 70=C, 80=B}

System.out.println(gradeByScore.pollFirstEntry()); // 60=D
System.out.println(gradeByScore);                  // {70=C, 80=B}
```

이 예제에서도 핵심은 같다.

- `firstEntry()`는 맨 앞 entry를 본다
- `pollFirstEntry()`는 맨 앞 entry를 꺼내면서 map에서도 없앤다

즉 set에서는 `pollFirst`, map에서는 `pollFirstEntry`가 같은 역할 계열이라고 보면 된다.

## 초보자 혼동 포인트

- `first()`가 "첫 번째 원소를 꺼낸다"고 착각하기 쉽다. 실제로는 제거하지 않는다.
- `pollFirst()`를 여러 번 호출하면 컬렉션이 줄어든다. 디버깅 중 출력용으로 무심코 호출하면 상태를 바꿔 버릴 수 있다.
- `TreeSet.first()`와 `TreeMap.firstKey()`는 둘 다 비어 있으면 예외다.
- `TreeMap.firstEntry()`는 이름이 비슷하지만 `firstKey()`와 empty behavior가 다르다. 비어 있으면 `null`이다.
- `pollFirst()` / `pollLast()`의 "first/last"는 삽입 순서가 아니라 comparator 순서의 양 끝이다.

## 빠른 선택 가이드

| 내가 원하는 것 | 맞는 선택 |
|---|---|
| 맨 앞 값을 보기만 한다 | `first()` / `firstEntry()` |
| 맨 뒤 값을 보기만 한다 | `last()` / `lastEntry()` |
| 맨 앞 값을 꺼내면서 제거한다 | `pollFirst()` / `pollFirstEntry()` |
| 맨 뒤 값을 꺼내면서 제거한다 | `pollLast()` / `pollLastEntry()` |
| 비어 있으면 예외보다 `null`이 낫다 | `poll...` 또는 `firstEntry()` / `lastEntry()` 쪽을 먼저 검토 |

## 다음에 읽으면 좋은 문서

- `first`/`last`가 삽입 순서가 아니라 comparator 순서라는 감각을 먼저 굳히려면 [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- descending view에서 `pollFirst`/`pollLast`가 원본의 어느 끝을 지우는지 헷갈리면 [`pollFirst()` / `pollLast()` on Original vs Descending View Primer](./pollfirst-polllast-view-semantics-primer.md)
- `subSet`/`subMap` 경계까지 같이 헷갈리면 [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- `TreeSet`/`TreeMap`에서 comparator가 같은 자리를 어떻게 정하는지 보려면 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)

## 한 줄 정리

`first`/`last`는 양 끝값을 **조회만** 하고, `pollFirst`/`pollLast`는 양 끝값을 **반환하면서 제거**한다. 초보자는 이 차이에 빈 컬렉션에서의 `예외 vs null` 반응까지 붙여서 기억하면 된다.
