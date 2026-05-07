---
schema_version: 3
title: HashMap vs TreeMap 초급 선택 브리지
concept_id: language/hashmap-vs-treemap-beginner-selection-bridge
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 89
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- map-selection
- hashmap-treemap
- ordered-lookup
aliases:
- HashMap vs TreeMap beginner selection bridge
- HashMap TreeMap 차이 초급
- sorted map basics
- hash based lookup vs sorted map ordering
- TreeMap floorKey ceilingKey subMap
- HashMap 정렬 안 됨
symptoms:
- HashMap과 TreeMap을 둘 다 key로 찾는 Map이라고만 보고 hash/equality lookup과 ordering lookup 차이를 놓쳐
- TreeMap이 단순히 출력 정렬만 해 주는 것이 아니라 compare == 0 overwrite와 range lookup 기준도 제공한다는 점을 모른다
- 순서가 중요하지 않은 id lookup과 가까운 key/range 조회가 필요한 정렬 map 요구를 구분하지 못해
intents:
- definition
- comparison
- troubleshooting
prerequisites:
- language/java-collections-basics
next_docs:
- language/hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge
- language/treeset-treemap-natural-ordering-compareto-bridge
- language/treemap-put-return-value-overwrite-bridge
linked_paths:
- contents/language/java/map-implementation-selection-mini-drill.md
- contents/language/java/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md
- contents/language/java/hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md
- contents/language/java/treemap-put-return-value-overwrite-bridge.md
- contents/language/java/treeset-treemap-natural-ordering-compareto-bridge.md
- contents/language/java/treemap-null-key-vs-nullable-field-primer.md
confusable_with:
- language/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet
- language/hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge
- language/treeset-treemap-natural-ordering-compareto-bridge
forbidden_neighbors: []
expected_queries:
- HashMap과 TreeMap을 언제 선택해야 하는지 hash lookup과 sorted lookup으로 설명해줘
- TreeMap은 정렬 출력뿐 아니라 floorKey ceilingKey subMap 같은 range lookup이 핵심이라는 뜻이야?
- HashMap은 equals hashCode 기준이고 TreeMap은 compareTo Comparator 기준으로 key를 찾는 차이를 알려줘
- TreeMap에서 id가 다른 객체가 comparator 때문에 value overwrite 되는 예제를 보여줘
- HashMap은 순서가 없고 TreeMap은 key 정렬 순서라는 점을 초보자용으로 정리해줘
contextual_chunk_prefix: |
  이 문서는 HashMap vs TreeMap 선택을 hash/equality lookup과 sorted key ordering/range lookup, compare == 0 overwrite semantics로 설명하는 beginner bridge다.
  HashMap vs TreeMap, sorted map, floorKey, ceilingKey, subMap, hash lookup, TreeMap overwrite 질문이 본 문서에 매핑된다.
---
# HashMap vs TreeMap 초급 선택 브리지

> 한 줄 요약: `HashMap`은 "정렬 없이 key를 빨리 찾는 서랍", `TreeMap`은 "정렬된 key 줄에서 찾는 사전"으로 읽으면 초보자가 가장 헷갈리는 조회 규칙, 순서, 덮어쓰기 차이를 한 번에 묶을 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md)
- [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- [HashMap vs LinkedHashMap vs TreeMap Key Contract Bridge](./hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md)
- [TreeMap `put` 반환값 브리지: `null` vs 이전 값](./treemap-put-return-value-overwrite-bridge.md)
- [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)

retrieval-anchor-keywords: hashmap vs treemap beginner selection bridge, hashmap treemap 차이 초급, hashmap treemap 언제 써요, hashmap treemap 뭐가 달라, sorted map basics, hash based lookup vs sorted map ordering, hashmap treemap overwrite semantics, treemap compareto 0 overwrite beginner, hashmap put same key overwrite, treemap floorkey ceilingkey submap beginner, range query treemap vs hashmap, 자바 map 아는데 hashmap treemap 헷갈려, 처음 hashmap treemap 선택, 왜 treemap 덮어쓰기 되나요, 왜 hashmap 정렬 안 되나요

## 먼저 잡는 멘탈 모델

`Map`을 이미 안다면 이제 질문은 두 개로 줄이면 된다.

1. key를 **어떻게 찾을까**
2. key를 **어떤 순서로 보고 싶을까**

초보자용 기억 문장은 이렇다.

- `HashMap`: 정렬은 포기하고 key를 찾는 기본 map
- `TreeMap`: key를 정렬된 줄에 세워 두고 그 순서로 찾는 map

비유로 붙이면 더 쉽다.

- `HashMap`은 "라벨 붙은 서랍"
- `TreeMap`은 "가나다순으로 정리된 사전"

그래서 "`Map`이면 다 key로 찾는 것 아닌가?"는 맞지만, **찾는 규칙과 보여 주는 순서가 다르다**는 점이 핵심이다.

## 15초 결정표

| 지금 질문 | `HashMap` 먼저 고를 때 | `TreeMap` 먼저 고를 때 |
|---|---|---|
| key를 어떻게 찾나 | `equals()`/`hashCode()` 기준 | `compareTo()`/`Comparator` 기준 |
| 반복 순서를 믿어도 되나 | 아니오 | 예, key 정렬 순서 |
| `floorKey`/`ceilingKey`/`subMap` 같은 range lookup이 필요한가 | 보통 직접 다른 구조를 더 붙여야 한다 | 예, 정렬된 key 줄 위에서 바로 읽는다 |
| 요구 문장 신호 | "순서는 상관없다", "id로 찾기만 한다" | "이름순", "점수순", "범위 조회" |
| 같은 key를 다시 `put`하면 | 같은 key면 value 덮어쓰기 | 같은 key 자리면 value 덮어쓰기 |

여기서 마지막 줄이 자주 헷갈린다.

- `HashMap`: `equals()`가 같은 key면 덮어쓴다
- `TreeMap`: `compare(...) == 0`인 같은 key 자리면 덮어쓴다

즉 둘 다 overwrite는 있지만, **"같은 key"를 판정하는 기준이 다르다**.

## 같은 예제로 한 번에 보기

```java
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.TreeMap;

record Student(long id, String name) {}

Map<Long, String> nicknameById = new HashMap<>();
nicknameById.put(1L, "Mina");
nicknameById.put(1L, "Momo");

Map<Student, Integer> scoreByStudent =
        new TreeMap<>(Comparator.comparing(Student::name));
scoreByStudent.put(new Student(1L, "Mina"), 90);
scoreByStudent.put(new Student(2L, "Mina"), 95);
```

이 코드는 이렇게 읽으면 된다.

- `HashMap` 쪽: key `1L`이 같으니 `"Mina"`가 `"Momo"`로 덮어써진다
- `TreeMap` 쪽: comparator가 `name`만 보니 두 `Student`가 같은 key 자리로 판단되어 `90`이 `95`로 덮어써진다

겉으로는 둘 다 "두 번째 `put`이 앞의 값을 바꿨다"로 보이지만, 내부 기준은 다르다.

| 장면 | `HashMap`에서 본 기준 | `TreeMap`에서 본 기준 |
|---|---|---|
| 같은 key인지 | `equals()`/`hashCode()` | `compare(...) == 0` |
| 출력 순서 | 믿지 않음 | `name` 정렬 순서 |
| 초보자 오해 | "왜 순서가 일정하지 않지?" | "왜 id가 다른데 덮어써지지?" |

## 자주 헷갈리는 문장 바로 번역하기

| 학습자 머릿속 문장 | 바로 번역 |
|---|---|
| "`HashMap`도 key로 찾고 `TreeMap`도 key로 찾는데 뭐가 달라?" | `HashMap`은 hash/equality, `TreeMap`은 ordering으로 key 자리를 찾는다 |
| "`TreeMap`은 정렬만 해 주는 거 아닌가?" | 정렬뿐 아니라 같은 key 자리 판단과 range lookup 기준도 comparator가 한다 |
| "`TreeMap`에서 id가 다른 객체를 넣었는데 왜 값이 덮어써져?" | comparator가 id를 안 보고 `compare == 0`을 만들었을 수 있다 |
| "`HashMap`도 지금은 순서대로 보이는데 그냥 써도 되지 않나?" | 우연히 그렇게 보인 것일 수 있고 순서 계약은 아니다 |

## `TreeMap`이 필요한 순간은 "예쁜 출력"보다 "정렬된 lookup"일 때가 많다

초보자는 `TreeMap`을 보면 보통 "출력이 오름차순으로 보이네"부터 떠올린다.
하지만 더 중요한 이유는 **정렬된 key 줄을 이용한 lookup** 이다.

예를 들어 점수 구간표를 생각해 보자.

```java
import java.util.TreeMap;

TreeMap<Integer, String> gradeByMinimumScore = new TreeMap<>();
gradeByMinimumScore.put(0, "F");
gradeByMinimumScore.put(60, "D");
gradeByMinimumScore.put(70, "C");
gradeByMinimumScore.put(80, "B");
gradeByMinimumScore.put(90, "A");

System.out.println(gradeByMinimumScore.floorKey(87));   // 80
System.out.println(gradeByMinimumScore.ceilingKey(87)); // 90
System.out.println(gradeByMinimumScore.subMap(70, true, 90, false));
// {70=C, 80=B}
```

이 예제에서 중요한 질문은 "출력이 정렬돼 보여서 좋다"가 아니다.

- `87`점이 어느 구간에 들어가나 -> `floorKey(87)`
- `87`점 다음 경계는 어디인가 -> `ceilingKey(87)`
- `70` 이상 `90` 미만 구간표만 잠깐 보고 싶다 -> `subMap(...)`

즉 `TreeMap`은 "정렬된 결과를 보여 주는 map"을 넘어서,
**정렬된 key를 기준으로 가장 가까운 key와 범위를 찾는 map** 으로 읽는 편이 더 정확하다.

## 왜 `HashMap`으로는 같은 질문을 바로 못 푸나

`HashMap`은 key가 정렬된 줄을 만들지 않는다.
그래서 아래 질문은 기본 조회만으로 바로 답하기 어렵다.

- "`87` 이하에서 가장 가까운 key가 뭐지?"
- "`87` 이상에서 가장 가까운 key가 뭐지?"
- "`70` 이상 `90` 미만 key만 잘라 보고 싶다"

`HashMap`은 "이 exact key가 있나?"에는 잘 맞는다.
하지만 "가장 가까운 key", "이 구간의 key들" 같은 질문은 **정렬 기준 자체가 필요**하다.

| 질문 종류 | `HashMap` | `TreeMap` |
|---|---|---|
| exact key 조회 | 잘 맞음 | 잘 맞음 |
| key 오름차순 순회 | 계약 없음 | 바로 가능 |
| `floorKey`/`ceilingKey` 같은 이웃 조회 | 직접 제공하지 않음 | 바로 가능 |
| `subMap` 같은 range view | 직접 제공하지 않음 | 바로 가능 |

## 초보자용 선택 순서

1. "정렬된 key 순서나 범위 조회가 필요한가?"를 먼저 본다.
2. 아니면 기본값은 `HashMap`으로 둔다.
3. `TreeMap`을 고를 때는 comparator가 "같은 key 자리"까지 결정한다는 점을 같이 확인한다.

짧게 줄이면:

- 정렬 요구 없음 -> `HashMap`
- key 정렬/범위 조회 필요 -> `TreeMap`
- `floorKey`/`ceilingKey`/`subMap`이 보이면 "출력 순서"보다 "정렬된 lookup" 요구로 읽기
- `TreeMap` comparator가 너무 거칠면 overwrite surprise가 생길 수 있음

ordered map 학습이 여기서 끊기지 않게, beginner follow-up은 아래 사다리로 붙이면 된다.

- 이 문서에서 구현체 선택 감각을 잡는다
- 다음 한 칸은 [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)로 가서 `floor`/`ceiling`의 boundary-`null`을 먼저 손으로 예측한다
- 그다음 [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)에서 `lower`/`floor`/`ceiling`/`higher` 전체 좌표계를 묶는다

## 다음 읽기

- 구현체 선택을 짧은 문제로 더 굳히려면 [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md)
- 순서 차이만 다시 보고 싶다면 [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- `TreeMap`에서 두 번째 `put`이 왜 덮어쓰기로 읽히는지 더 짧게 보려면 [TreeMap `put` 반환값 브리지: `null` vs 이전 값](./treemap-put-return-value-overwrite-bridge.md)
- ordered map route를 beginner-safe하게 이어 가려면 [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md) -> [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- `floorKey`, `ceilingKey`, `lowerKey`, `higherKey`를 한 장으로 묶어 보고 싶다면 [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- `TreeMap` comparator와 natural ordering이 같은 key 자리를 어떻게 만드는지 보려면 [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)

## 한 줄 정리

`HashMap`은 hash/equality로 찾는 기본 map, `TreeMap`은 ordering으로 찾고 정렬 순서로 보여 주는 map이라고 분리해서 읽으면 "순서"와 "덮어쓰기"를 같은 질문으로 섞는 실수를 줄일 수 있다.
