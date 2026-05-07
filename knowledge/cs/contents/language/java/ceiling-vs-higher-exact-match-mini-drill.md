---
schema_version: 3
title: ceiling vs higher Exact Match Mini Drill
concept_id: language/ceiling-vs-higher-exact-match-mini-drill
canonical: true
category: language
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- navigablemap
- ordered-map
- boundary-drill
aliases:
- ceiling vs higher exact match drill
- TreeMap ceiling higher exact key
- TreeSet ceiling higher same value
- NavigableMap exact match right side
- 자바 ceiling higher 차이
- ordered map exact match drill
symptoms:
- ceiling은 exact match를 포함하고 higher는 제외한다는 inclusive vs strict 차이를 구분하지 못해
- higher가 null을 반환하면 null key와 boundary result를 섞어 해석해
- exact match가 아닐 때 ceiling과 higher가 같을 수 있고 exact match일 때만 갈라진다는 감각이 부족해
intents:
- drill
- definition
- troubleshooting
prerequisites:
- language/navigablemap-navigableset-mental-model
next_docs:
- language/lower-vs-floor-exact-match-mini-drill
- language/submap-boundaries-primer
- language/ordered-map-null-safe-practice-drill
linked_paths:
- contents/language/java/ordered-map-null-safe-practice-drill.md
- contents/language/java/navigablemap-navigableset-mental-model.md
- contents/language/java/lower-vs-floor-exact-match-mini-drill.md
- contents/language/java/submap-boundaries-primer.md
- contents/data-structure/heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md
confusable_with:
- language/lower-vs-floor-exact-match-mini-drill
- language/navigablemap-navigableset-mental-model
- language/submap-boundaries-primer
forbidden_neighbors: []
expected_queries:
- TreeMap에서 ceiling과 higher가 exact match일 때 왜 다르게 나와?
- ceiling은 현재 key를 포함하고 higher는 제외한다는 차이를 예제로 보여줘
- higher(40)이 null이면 TreeMap null key와 관련 있는 건지 boundary result인지 알려줘
- NavigableMap ceiling higher exact match 미니 드릴을 풀고 싶어
- ordered map에서 exact match가 아닐 때 ceiling과 higher가 같을 수 있는 이유를 알려줘
contextual_chunk_prefix: |
  이 문서는 TreeSet/TreeMap Navigable API의 ceiling vs higher exact match 차이를 inclusive vs strict boundary, null boundary result로 손예측하는 beginner drill이다.
  ceiling higher, exact match, ordered map, NavigableMap, boundary null, TreeSet TreeMap 질문이 본 문서에 매핑된다.
---
# `ceiling` vs `higher` Exact Match 미니 드릴

> 한 줄 요약: `TreeSet`/`TreeMap`에서 exact match를 물었을 때 `ceiling`은 현재 자리에 멈추고 `higher`는 한 칸 오른쪽으로 가는 차이만 따로 떼어 짧게 손예측해 보는 1페이지 드릴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README: Java primer](../README.md#java-primer)
- [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- [Heap vs PriorityQueue vs Ordered Map Beginner Bridge](../../data-structure/heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)

retrieval-anchor-keywords: ceiling vs higher exact match drill, treemap ceiling higher exact key, treeset ceiling higher same value, navigablemap exact match worksheet right side, java ceiling higher beginner, java higher ceiling confusion, exact match ceiling higher difference, ordered map exact match drill, boundary null vs null key treemap, ceiling higher null meaning beginner, 자바 ceiling higher 차이, 자바 exact match 워크시트, 처음 배우는데 ceiling higher, 왜 higher는 자기 자신이 아닌가, why ceiling returns same key

## 먼저 잡을 mental model

이번 드릴은 이것 하나만 고정하면 된다.

- `ceiling(x)`: `x`와 같으면 그 자리에 멈춘다
- `higher(x)`: `x`와 같아도 그 자리는 건너뛰고 바로 다음 칸으로 간다

짧게 외우면:

> exact match에서는 `ceiling`은 포함, `higher`는 제외다.

여기서 같이 붙여 둘 한 줄도 있다.

> `higher(x)`가 `null`이 되는 것은 "더 오른쪽 이웃이 없다"는 조회 결과이지, `TreeMap`이 `null` key를 허용하는지와는 다른 이야기다.

## 10초 비교표

정렬된 줄이 `10   20   30   40`일 때:

| 질문 | 결과 | 한 줄 이유 |
|---|---|---|
| `ceiling(30)` | `30` | exact match 포함 |
| `higher(30)` | `40` | exact match 제외 |
| `ceiling(40)` | `40` | 마지막 값 exact match 포함 |
| `higher(40)` | `null` | exact match는 제외했고 더 오른쪽 이웃이 없음 |
| `ceiling(25)` | `30` | `25` 이상 중 가장 가까움 |
| `higher(25)` | `30` | `25`보다 큰 값 중 가장 가까움 |

초보자 포인트는 한 줄이다.

- exact match가 아닐 때는 `ceiling`과 `higher`가 같을 수 있다
- exact match일 때만 둘이 갈라진다

## 드릴 1: `TreeSet`

```java
import java.util.List;
import java.util.TreeSet;

TreeSet<Integer> numbers = new TreeSet<>(List.of(10, 20, 30, 40));

System.out.println(numbers.ceiling(30));
System.out.println(numbers.higher(30));
System.out.println(numbers.ceiling(40));
System.out.println(numbers.higher(40));
System.out.println(numbers.ceiling(25));
System.out.println(numbers.higher(25));
```

실행 전에 먼저 적어 보자.

| 호출 | 내 답 |
|---|---|
| `ceiling(30)` |  |
| `higher(30)` |  |
| `ceiling(40)` |  |
| `higher(40)` |  |
| `ceiling(25)` |  |
| `higher(25)` |  |

정답:

- `ceiling(30) -> 30`
- `higher(30) -> 40`
- `ceiling(40) -> 40`
- `higher(40) -> null`
- `ceiling(25) -> 30`
- `higher(25) -> 30`

여기서 `higher(40) -> null`은 "맨 오른쪽 원소보다 더 뒤에 갈 곳이 없다"는 뜻이다.
조회 결과 `null`을 "`TreeSet`/`TreeMap`이 `null`을 저장하나?"로 읽으면 다른 문제와 섞이기 쉽다.

## 드릴 2: `TreeMap`

이번에는 key 줄만 본다.

```java
import java.util.TreeMap;

TreeMap<Integer, String> gradeByMinimumScore = new TreeMap<>();
gradeByMinimumScore.put(0, "F");
gradeByMinimumScore.put(60, "D");
gradeByMinimumScore.put(70, "C");
gradeByMinimumScore.put(80, "B");
gradeByMinimumScore.put(90, "A");

System.out.println(gradeByMinimumScore.ceilingEntry(80));
System.out.println(gradeByMinimumScore.higherEntry(80));
System.out.println(gradeByMinimumScore.ceilingEntry(90));
System.out.println(gradeByMinimumScore.higherEntry(90));
System.out.println(gradeByMinimumScore.ceilingEntry(87));
System.out.println(gradeByMinimumScore.higherEntry(87));
```

| 호출 | 결과 | 읽는 법 |
|---|---|---|
| `ceilingEntry(80)` | `80=B` | exact match 포함 |
| `higherEntry(80)` | `90=A` | exact match 제외 |
| `ceilingEntry(90)` | `90=A` | 마지막 key exact match 포함 |
| `higherEntry(90)` | `null` | 마지막 key의 strict한 오른쪽 이웃이 없음 |
| `ceilingEntry(87)` | `90=A` | `87` 이상 중 가장 가까운 key |
| `higherEntry(87)` | `90=A` | `87`보다 큰 key 중 가장 가까운 key |

여기서도 exact match가 아닌 `87`에서는 둘이 같아진다.
반대로 exact match가 맨 오른쪽 경계인 `90`에서는 `ceilingEntry`만 멈추고 `higherEntry`는 `null`이 된다.

## 자주 헷갈리는 순간

- "`higher`도 위쪽이니까 exact match면 자기 자신이겠지"라고 읽기 쉽다.
- "`ceiling`은 무조건 더 큰 값"이라고 외우면 `ceiling(30)`에서 틀리기 쉽다.
- `higherEntry(90) == null`을 보고 "`TreeMap`이 `null` key를 허용하나?"로 점프하기 쉽다.
- `TreeMap`에서 value를 비교한다고 생각하면 `90=A`와 `80=B` 차이를 잘못 읽기 쉽다.

안전한 읽기 순서:

1. key 또는 원소를 comparator 줄에 놓는다.
2. exact match인지 먼저 본다.
3. exact match면 `ceiling`은 멈추고 `higher`는 한 칸 더 오른쪽으로 간다.
4. 그 오른쪽 칸이 실제로 없으면 반환값은 `null`이고, 이 `null`은 boundary result라고 읽는다.

## 다음 읽기

- 전체 네 쌍을 같이 묶고 싶으면: [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- boundary-result `null`과 `null` key 규칙을 분리해서 보고 싶다면: [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)
- 왼쪽 exact match 대응편을 같이 보고 싶다면: [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)
- `TreeMap`의 `null` key와 nullable field 차이를 따로 정리한 입문 카드가 필요하면: [TreeMap Null Key vs Nullable Field Primer](./treemap-null-key-vs-nullable-field-primer.md)
- range API와 같이 섞일 때 경계 감각을 고정하려면: [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)

## 한 줄 정리

`ceiling`과 `higher`는 exact match가 아닌 값에서는 같게 보일 수 있지만, exact match 순간에는 `ceiling`만 현재 자리를 포함하고 `higher`는 바로 다음 칸으로 이동하며, 그 다음 칸이 없으면 `null`은 "오른쪽 경계 결과"로 읽어야 한다.
