---
schema_version: 3
title: lower vs floor Exact Match Mini Drill
concept_id: language/lower-vs-floor-exact-match-mini-drill
canonical: true
category: language
difficulty: beginner
doc_role: drill
level: beginner
language: ko
source_priority: 92
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- navigable-map
- boundary-api
- exact-match
aliases:
- lower vs floor exact match drill
- TreeMap lower floor exact key
- TreeSet lower floor same value
- NavigableMap exact match worksheet
- lower는 자기 자신이 아닌가
- 자바 lower floor 차이
symptoms:
- floor와 lower를 모두 아래쪽 key로만 외워 exact match에서 floor는 포함, lower는 제외라는 차이를 놓쳐
- lower(10)이 null인 것을 boundary result가 아니라 TreeMap null key 허용 정책 문제로 오해해
- exact match가 아닐 때 둘이 같은 결과를 낼 수 있다는 점 때문에 exact match 순간의 차이를 예측하지 못해
intents:
- drill
- definition
- troubleshooting
prerequisites:
- language/navigablemap-navigableset-mental-model
- language/submap-boundaries-primer
- language/descending-view-mental-model
next_docs:
- language/ceiling-vs-higher-exact-match-mini-drill
- language/ordered-map-null-safe-practice-drill
- language/treemap-null-key-vs-nullable-field-primer
linked_paths:
- contents/data-structure/heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md
- contents/language/java/navigablemap-navigableset-mental-model.md
- contents/language/java/descending-view-mental-model.md
- contents/language/java/submap-boundaries-primer.md
- contents/language/java/ordered-map-null-safe-practice-drill.md
- contents/language/java/ceiling-vs-higher-exact-match-mini-drill.md
- contents/language/java/treemap-null-key-vs-nullable-field-primer.md
confusable_with:
- language/ceiling-vs-higher-exact-match-mini-drill
- language/ordered-map-null-safe-practice-drill
- language/navigablemap-navigableset-mental-model
forbidden_neighbors: []
expected_queries:
- TreeMap TreeSet에서 lower와 floor는 exact match일 때 어떻게 달라?
- floor(30)는 30을 돌려주고 lower(30)는 20을 돌려주는 이유를 설명해줘
- lower(10)이 null이면 null key 문제가 아니라 boundary result라는 뜻인지 알려줘
- NavigableMap에서 lower floor ceiling higher 네 쌍을 exact match 기준으로 구분해줘
- lower vs floor 차이를 10 20 30 40 예제로 드릴해줘
contextual_chunk_prefix: |
  이 문서는 TreeSet/TreeMap Navigable API에서 lower와 floor의 exact match 포함/제외 차이를 손예측하는 beginner drill이다.
  lower vs floor, exact match, boundary null result, NavigableMap, TreeMap floorEntry 질문이 본 문서에 매핑된다.
---
# `lower` vs `floor` Exact Match 미니 드릴

> 한 줄 요약: `TreeSet`/`TreeMap`에서 exact match를 물었을 때 `lower`는 한 칸 왼쪽으로 가고 `floor`는 현재 자리에 멈춘다는 차이만 따로 떼어 짧게 손예측해 보는 1페이지 드릴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README: Java primer](../README.md#java-primer)
- [Heap vs PriorityQueue vs Ordered Map Beginner Bridge](../../data-structure/heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)

retrieval-anchor-keywords: lower vs floor exact match drill, treemap lower floor exact key, treeset lower floor same value, navigablemap exact match worksheet, java lower floor beginner, java floor lower confusion, exact match lower floor difference, ordered map exact match drill, boundary null vs null key treemap, floor lower null meaning beginner, 자바 lower floor 차이, 자바 exact match 워크시트, 처음 배우는데 lower floor, 왜 lower는 자기 자신이 아닌가, lower vs floor exact match mini drill basics

## 먼저 잡을 mental model

이번 드릴은 이것 하나만 고정하면 된다.

- `floor(x)`: `x`와 같으면 그 자리에 멈춘다
- `lower(x)`: `x`와 같아도 그 자리는 건너뛰고 바로 앞 칸으로 간다

짧게 외우면:

> exact match에서는 `floor`는 포함, `lower`는 제외다.

여기서 같이 붙여 둘 한 줄도 있다.

> `lower(x)`가 `null`이 되는 것은 "더 왼쪽 이웃이 없다"는 조회 결과이지, `TreeMap`의 `null` key 허용 정책 이야기와는 다르다.

## 10초 비교표

정렬된 줄이 `10   20   30   40`일 때:

| 질문 | 결과 | 한 줄 이유 |
|---|---|---|
| `floor(30)` | `30` | exact match 포함 |
| `lower(30)` | `20` | exact match 제외 |
| `floor(10)` | `10` | 첫 값 exact match 포함 |
| `lower(10)` | `null` | exact match는 제외했고 더 왼쪽 이웃이 없음 |
| `floor(25)` | `20` | `25` 이하 중 가장 가까움 |
| `lower(25)` | `20` | `25`보다 작은 값 중 가장 가까움 |

초보자 포인트는 한 줄이다.

- exact match가 아닐 때는 `floor`와 `lower`가 같을 수 있다
- exact match일 때만 둘이 갈라진다

## 드릴 1: `TreeSet`

```java
import java.util.List;
import java.util.TreeSet;

TreeSet<Integer> numbers = new TreeSet<>(List.of(10, 20, 30, 40));

System.out.println(numbers.floor(30));
System.out.println(numbers.lower(30));
System.out.println(numbers.floor(10));
System.out.println(numbers.lower(10));
System.out.println(numbers.floor(25));
System.out.println(numbers.lower(25));
```

실행 전에 먼저 적어 보자.

| 호출 | 내 답 |
|---|---|
| `floor(30)` |  |
| `lower(30)` |  |
| `floor(10)` |  |
| `lower(10)` |  |
| `floor(25)` |  |
| `lower(25)` |  |

정답:

- `floor(30) -> 30`
- `lower(30) -> 20`
- `floor(10) -> 10`
- `lower(10) -> null`
- `floor(25) -> 20`
- `lower(25) -> 20`

여기서 `lower(10) -> null`은 "맨 왼쪽 원소보다 더 앞에 갈 곳이 없다"는 뜻이다.
`TreeSet`/`TreeMap`에 `null`을 넣을 수 있느냐와는 다른 축이므로, 조회 결과 `null`과 입력 정책 `null`을 섞지 않는 편이 안전하다.

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

System.out.println(gradeByMinimumScore.floorEntry(80));
System.out.println(gradeByMinimumScore.lowerEntry(80));
System.out.println(gradeByMinimumScore.floorEntry(0));
System.out.println(gradeByMinimumScore.lowerEntry(0));
System.out.println(gradeByMinimumScore.floorEntry(87));
System.out.println(gradeByMinimumScore.lowerEntry(87));
```

| 호출 | 결과 | 읽는 법 |
|---|---|---|
| `floorEntry(80)` | `80=B` | exact match 포함 |
| `lowerEntry(80)` | `70=C` | exact match 제외 |
| `floorEntry(0)` | `0=F` | 첫 key exact match 포함 |
| `lowerEntry(0)` | `null` | 첫 key의 strict한 왼쪽 이웃이 없음 |
| `floorEntry(87)` | `80=B` | `87` 이하 중 가장 가까운 key |
| `lowerEntry(87)` | `80=B` | `87`보다 작은 key 중 가장 가까운 key |

여기서도 exact match가 아닌 `87`에서는 둘이 같아진다.
반대로 exact match가 맨 왼쪽 경계인 `0`에서는 `floorEntry`만 멈추고 `lowerEntry`는 `null`이 된다.

## 자주 헷갈리는 순간

- "`lower`도 아래쪽이니까 exact match면 자기 자신이겠지"라고 읽기 쉽다.
- "`floor`는 무조건 더 작은 값"이라고 외우면 `floor(30)`에서 틀리기 쉽다.
- `lowerEntry(0) == null`을 보고 "`TreeMap`이 `null` key를 다루는 규칙인가?"로 점프하기 쉽다.
- `TreeMap`에서 value를 비교한다고 생각하면 `80=B`와 `70=C` 차이를 잘못 읽기 쉽다.

안전한 읽기 순서:

1. key 또는 원소를 comparator 줄에 놓는다.
2. exact match인지 먼저 본다.
3. exact match면 `floor`는 멈추고 `lower`는 한 칸 더 왼쪽으로 간다.
4. 그 왼쪽 칸이 실제로 없으면 반환값은 `null`이고, 이 `null`은 boundary result라고 읽는다.

## 다음 읽기

- 전체 네 쌍을 같이 묶고 싶으면: [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- boundary-result `null`과 `null` key 규칙을 분리해서 보고 싶다면: [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)
- 오른쪽 exact match 대응편을 같이 보고 싶다면: [`ceiling` vs `higher` Exact Match 미니 드릴](./ceiling-vs-higher-exact-match-mini-drill.md)
- `TreeMap`의 `null` key와 nullable field 차이를 따로 정리한 입문 카드가 필요하면: [TreeMap Null Key vs Nullable Field Primer](./treemap-null-key-vs-nullable-field-primer.md)
- reverse order에서 왜 더 헷갈리는지 보려면: [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
- range API와 같이 섞일 때 경계 감각을 고정하려면: [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)

## 한 줄 정리

`lower`와 `floor`는 exact match가 아닌 값에서는 같게 보일 수 있지만, exact match 순간에는 `floor`만 현재 자리를 포함하고 `lower`는 바로 앞 칸으로 이동하며, 그 앞 칸이 없으면 `null`은 "경계 결과"로 읽어야 한다.
