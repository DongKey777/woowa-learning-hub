---
schema_version: 3
title: Map 구현체별 반복 순서 치트시트
concept_id: language/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- map-implementation
- iteration-order
- linkedhashmap-access-order
aliases:
- HashMap LinkedHashMap TreeMap iteration order
- Java Map order cheat sheet
- HashMap iteration order not guaranteed
- LinkedHashMap insertion order access order
- TreeMap sorted order
- 자바 Map 구현체별 순서
symptoms:
- HashMap 출력 순서가 우연히 일정해 보인 것을 iteration order contract로 믿어
- LinkedHashMap access-order=true에서 get만 해도 순서가 바뀌고 eviction 대상이 달라지는 이유를 놓쳐
- 삽입/접근 순서가 필요한 요구와 floorKey/subMap 같은 정렬 기반 이웃·범위 조회 요구를 구분하지 못해
intents:
- definition
- comparison
- troubleshooting
prerequisites:
- language/java-collections-basics
next_docs:
- language/hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge
- language/linkedhashmap-access-order-cache-behavior-bridge
- language/navigablemap-navigableset-mental-model
linked_paths:
- contents/language/java/java-collections-basics.md
- contents/language/java/map-implementation-selection-mini-drill.md
- contents/language/java/linkedhashmap-access-order-cache-behavior-bridge.md
- contents/language/java/hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md
- contents/language/java/map-iteration-patterns-cheat-sheet.md
- contents/language/java/navigablemap-navigableset-mental-model.md
- contents/language/java/submap-boundaries-primer.md
- contents/language/java/treeset-treemap-natural-ordering-compareto-bridge.md
confusable_with:
- language/hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge
- language/linkedhashmap-access-order-cache-behavior-bridge
- language/hashmap-vs-treemap-beginner-selection-bridge
forbidden_neighbors: []
expected_queries:
- HashMap LinkedHashMap TreeMap 반복 순서 차이를 초보자용 치트시트로 알려줘
- HashMap은 지금 순서가 맞아 보여도 iteration order를 믿으면 안 되는 이유가 뭐야?
- LinkedHashMap 기본 삽입 순서와 access-order=true 접근 순서 차이를 설명해줘
- TreeMap은 key 정렬 순서와 floorKey subMap 같은 range lookup을 제공한다는 뜻이야?
- 처음 넣은 순서를 유지해야 할 때 LinkedHashMap과 TreeMap 중 무엇을 골라야 해?
contextual_chunk_prefix: |
  이 문서는 HashMap, LinkedHashMap, TreeMap iteration order를 no-order, insertion/access order, sorted key order와 floorKey/subMap capabilities로 비교하는 beginner cheat sheet다.
  HashMap order, LinkedHashMap insertion order, access-order, TreeMap sorted order, Map implementation choice 질문이 본 문서에 매핑된다.
---
# Map 구현체별 반복 순서 치트시트

> 한 줄 요약: `HashMap`은 반복 순서를 믿으면 안 되고, `LinkedHashMap`은 기본이 삽입 순서지만 `access-order=true`면 조회만 해도 최근 접근 순서로 바뀌며, `TreeMap`은 key 정렬 순서와 `floorKey`/`subMap` 같은 이웃·범위 조회를 함께 제공한다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md)
- [LinkedHashMap access-order와 캐시 동작 브리지](./linkedhashmap-access-order-cache-behavior-bridge.md)
- [HashMap vs LinkedHashMap vs TreeMap Key Contract Bridge](./hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md)
- [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)

retrieval-anchor-keywords: hashmap linkedhashmap treemap iteration order, java map order cheat sheet, hashmap iteration order not guaranteed, linkedhashmap insertion order, linkedhashmap access order, treemap sorted order, treemap floorkey ceilingkey submap beginner, 삽입 순서 보장 map, 정렬 기반 이웃 조회 map, map 구현체별 순서 차이, 자바 hashmap 순서 왜 바뀌지, 조회만 했는데 순서가 바뀐다, 최근에 조회한 key가 뒤로 간다, 처음 넣은 순서가 왜 안 나오지, linkedhashmap treemap 순서 차이 뭐예요

## 먼저 잡는 멘탈 모델

`Map`에서 "반복 순서"는 `Map` 공통 규칙이 아니라 **구현체별 규칙**이다.

- `HashMap`: 순서 없음
- `LinkedHashMap`: 기본은 넣은 순서, 옵션을 바꾸면 최근 접근 순서
- `TreeMap`: 정렬 순서 있음

그래서 "출력 순서가 중요하다"는 요구가 생기면 `Map`만 고르면 안 되고, 어떤 구현체인지까지 같이 골라야 한다.

## 10초 비교표

| 구현체 | 반복 순서 | 이웃/범위 조회 | 이런 때 고른다 |
|---|---|---|---|
| `HashMap` | 예측하지 않는다 | 없음 | 순서보다 일반 조회/갱신이 중요할 때 |
| `LinkedHashMap` | 기본은 삽입 순서 | 없음 | 화면/로그에서 넣은 순서대로 보여 주고 싶을 때 |
| `TreeMap` | key 정렬 순서 | `floorKey`, `ceilingKey`, `subMap` 가능 | key를 오름차순으로 보거나 가까운 key, 범위를 찾아야 할 때 |

초보자용 기억 문장은 이것만으로 충분하다.

- "순서 기대 안 함" -> `HashMap`
- "넣은 순서 유지" -> 기본 `LinkedHashMap`
- "최근에 본 것이 뒤로 가야 함" -> `LinkedHashMap(access-order=true)`
- "정렬해서 봄" -> `TreeMap`
- "`x` 이하에서 가장 가까운 key"나 "`20` 이상 `40` 미만"을 바로 찾음 -> `TreeMap`

## 순서 혼동을 15초 만에 자르는 증상 -> 원인 블록

반복 순서 질문은 구현체 이름보다 **처음 보인 증상**으로 자르면 retrieval이 더 잘 걸린다.

| 보인 증상 | 먼저 의심할 원인 | 첫 선택 |
|---|---|---|
| "처음 넣은 순서가 왜 안 나오지?" | `HashMap`에 순서 계약이 있다고 기대했다 | 기본 `LinkedHashMap` |
| "조회만 했는데 key가 뒤로 갔다" | `LinkedHashMap(access-order=true)`라서 접근이 순서를 바꿨다 | `LinkedHashMap(access-order=true)` |
| "왜 최근에 읽은 key 때문에 eviction 대상이 바뀌지?" | access-order와 `removeEldestEntry()`가 같이 동작했다 | `LinkedHashMap(access-order=true)` |
| "`87` 이하에서 가장 가까운 key`", "`20` 이상 `40` 미만`"이 필요하다 | 삽입 순서가 아니라 정렬된 key 줄이 필요하다 | `TreeMap` |
| "지금은 `HashMap`도 순서가 맞아 보이는데요?" | 우연한 출력 패턴을 계약처럼 읽고 있다 | 순서가 중요하면 `LinkedHashMap` 또는 `TreeMap`으로 의도를 명시 |

짧게 번역하면 이렇다.

- "처음 넣은 순서를 보여 줘" -> `LinkedHashMap`
- "조회 후 순서가 밀린다" -> `LinkedHashMap(access-order=true)`
- "가까운 key`/`범위" -> `TreeMap`
- "`HashMap`인데도 지금은 일정해 보인다" -> 보장으로 읽지 말고 구현체 선택부터 다시 본다

## 같은 데이터로 바로 비교

```java
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.TreeMap;

Map<String, Integer> hashMap = new HashMap<>();
Map<String, Integer> linkedHashMap = new LinkedHashMap<>();
Map<String, Integer> treeMap = new TreeMap<>();

hashMap.put("banana", 2);
hashMap.put("apple", 1);
hashMap.put("carrot", 3);

linkedHashMap.put("banana", 2);
linkedHashMap.put("apple", 1);
linkedHashMap.put("carrot", 3);

treeMap.put("banana", 2);
treeMap.put("apple", 1);
treeMap.put("carrot", 3);

System.out.println(linkedHashMap.keySet()); // [banana, apple, carrot]
System.out.println(treeMap.keySet());       // [apple, banana, carrot]
System.out.println(hashMap.keySet());       // 순서를 기대하면 안 됨
```

읽는 포인트는 두 가지다.

- `LinkedHashMap`은 넣은 순서를 그대로 보여 준다.
- `TreeMap`은 `key` 기준으로 정렬해서 보여 준다.

`HashMap`은 어떤 실행에서 우연히 일정해 보일 수 있어도, 그 결과를 로직 규칙처럼 믿으면 안 된다.

## `LinkedHashMap`과 `TreeMap`을 beginner 질문으로 나누기

입문자 기준으로는 두 구현체를 "둘 다 순서가 있는 map"으로 묶지 말고, **어떤 질문에 답하는 map인지**로 나누는 편이 더 안전하다.

| 내가 실제로 묻는 것 | 첫 선택 | 이유 |
|---|---|---|
| "넣은 순서대로 다시 보여 줘" | `LinkedHashMap` | 삽입 순서를 보장한다 |
| "방금 읽은 것을 뒤로 보내고 싶어" | `LinkedHashMap(access-order=true)` | 접근 순서를 기록한다 |
| "`87` 이하에서 가장 가까운 key가 뭐야?" | `TreeMap` | 정렬된 key 줄에서 `floorKey`로 찾는다 |
| "`20` 이상 `40` 미만 구간만 보고 싶어" | `TreeMap` | `subMap`으로 range view를 만든다 |

짧게 말하면:

- `LinkedHashMap`은 **삽입/접근 순서를 보여 주는 map**
- `TreeMap`은 **정렬된 key 줄에서 이웃과 범위를 찾는 map**

즉 "`LinkedHashMap`도 순서가 있으니 범위 조회에 쓰면 되지 않나?"가 흔한 첫 오해다. 삽입 순서는 "먼저 들어온 순서"일 뿐이고, `10 -> 20 -> 30`처럼 비교 가능한 정렬 축을 뜻하지 않는다.

## `TreeMap`은 순서 표시보다 이웃 조회가 더 중요한 경우가 많다

`TreeMap`을 처음 보면 "오름차순으로 예쁘게 보인다"가 먼저 보이지만, 초급자에게 더 중요한 차이는 **정렬된 key 위에서 가까운 위치를 찾을 수 있다는 점**이다.

```java
import java.util.LinkedHashMap;
import java.util.TreeMap;

LinkedHashMap<Integer, String> linked = new LinkedHashMap<>();
linked.put(30, "B");
linked.put(10, "D");
linked.put(20, "C");

TreeMap<Integer, String> tree = new TreeMap<>(linked);

System.out.println(linked.keySet());     // [30, 10, 20]
System.out.println(tree.keySet());       // [10, 20, 30]
System.out.println(tree.floorKey(25));   // 20
System.out.println(tree.subMap(10, 30)); // {10=D, 20=C}
```

이 예제에서 읽는 포인트는 세 가지다.

- `LinkedHashMap`의 `[30, 10, 20]`은 넣은 순서일 뿐, 크기순 줄이 아니다.
- 그래서 `25`의 왼쪽 이웃이 누구인지 바로 물을 기준이 없다.
- `TreeMap`은 key를 정렬해 두므로 `floorKey(25)`, `subMap(10, 30)` 같은 질문을 바로 받는다.

## `LinkedHashMap`의 삽입 순서 vs 접근 순서

`LinkedHashMap`은 여기서 한 번 더 갈린다.

| 모드 | 순서가 바뀌는 순간 | 이런 때 쓴다 |
|---|---|---|
| 기본값 (`access-order=false`) | 새 key를 `put`할 때 | 입력한 순서를 유지하고 싶을 때 |
| 접근 순서 (`access-order=true`) | `get`, `put`, `putIfAbsent`처럼 entry를 다시 만질 때 | "최근에 사용한 것" 기준으로 보고 싶을 때 |

즉 `LinkedHashMap`은 항상 "삽입 순서 map"이 아니다. 생성자 옵션 하나로 "최근 접근 순서 map"으로도 쓸 수 있다.

여기서 캐시 예제가 갑자기 어렵게 느껴지는 이유는 `access-order=true`가 단순 출력 순서 옵션이 아니라, **조회한 항목을 뒤로 보내서 다음 eviction 후보를 바꾸는 규칙**이기 때문이다.

### 증상으로 바로 연결하기

아래 두 문장은 사실 거의 같은 질문이다.

- "조회만 했는데 순서가 바뀐다"
- "왜 캐시에서 `B`가 지워지지"

첫 문장은 순서 증상처럼 보이지만, `LinkedHashMap(access-order=true)`에서는 곧바로 캐시 제거 후보 질문으로 이어진다.

1. `get("A")`를 하면 `A`가 뒤로 간다.
2. 그러면 맨 앞에 남는 eldest가 `B`로 바뀐다.
3. 다음 `put("C")`에서 제거되는 것도 `A`가 아니라 `B`가 된다.

즉 순서가 바뀌었다는 관찰과 eviction 결과가 달라졌다는 관찰은 따로가 아니라 같은 원인으로 묶어 읽어야 한다.

## 작은 LRU 느낌 예제

```java
import java.util.LinkedHashMap;
import java.util.Map;

Map<String, String> cache = new LinkedHashMap<>(16, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry<String, String> eldest) {
        return size() > 2;
    }
};

cache.put("A", "apple");
cache.put("B", "banana");   // [A, B]
cache.get("A");             // [B, A]  최근 접근한 A가 뒤로 감
cache.put("C", "carrot");   // [A, C]  가장 오래된 B 제거
```

이 예제의 읽는 포인트는 두 가지다.

- 세 번째 인자 `true`가 `access-order`를 켠다.
- `removeEldestEntry()`를 같이 쓰면 "가장 오래 안 쓴 것부터 밀어내기" 같은 아주 작은 LRU 스타일 캐시를 만들 수 있다.

질문을 symptom-first로 바꾸면 더 빨리 읽힌다.

| 보인 증상 | 실제로 확인할 것 | 왜 그런가 |
|---|---|---|
| `get(A)`만 했는데 `A`가 뒤로 갔다 | `access-order=true` 여부 | 조회가 최신 접근으로 기록된다 |
| 다음 `put(C)`에서 `B`가 지워졌다 | `removeEldestEntry()`와 현재 맨 앞 entry | `A`를 방금 읽어서 eldest가 `B`가 됐다 |
| "나는 삽입 순서를 원했는데 캐시처럼 움직인다" | `LinkedHashMap` 생성자 세 번째 인자 | 삽입 순서 map이 아니라 접근 순서 map으로 만든 상태다 |

## 역방향 확인 1문항

이번에는 반대로, 증상을 보고 구현체를 고르는 연습을 해 보자.

> 테스트 로그에서 `A -> B -> C`로 넣어 둔 map이 있었는데, `get(B)`를 한 뒤 다시 출력하니 `A -> C -> B`가 됐다.  
> "최근에 조회한 key가 뒤로 간다"는 증상만 보고 가장 먼저 떠올릴 구현체는 무엇일까?

1. `HashMap`
2. 기본 `LinkedHashMap`
3. `LinkedHashMap(access-order=true)`
4. `TreeMap`

정답은 `3`이다.

- 핵심 단서는 "`get(B)`만 했는데 순서가 바뀌었다"는 부분이다.
- 기본 `LinkedHashMap`은 조회만으로 순서를 바꾸지 않으므로 `2`번이 아니다.
- `TreeMap`은 key 정렬 순서를 유지할 뿐 "방금 조회한 key를 뒤로 민다" 같은 최근 접근 증상을 만들지 않는다.

이 한 문장을 바로 번역하면 된다.

- "조회 후 뒤로 밀림" -> `LinkedHashMap(access-order=true)`

## 자주 하는 오해

- "`HashMap`도 지금은 항상 같은 순서로 찍히는데요?"
  지금 그 환경에서 우연히 그렇게 보이는 것뿐이다. 반복 순서 계약이 아니므로 코드 의미로 기대하면 안 된다.
- "`LinkedHashMap`은 key를 정렬해 주나요?"
  아니다. 정렬이 아니라 **삽입 순서 유지**다.
- "`LinkedHashMap`은 항상 넣은 순서 아닌가요?"
  기본은 그렇지만, `new LinkedHashMap<>(..., true)`로 만들면 최근 접근 순서로 바뀐다.
- "`LinkedHashMap`에도 `30` 근처 key를 찾는 API가 있나요?"
  없다. 삽입 순서는 정렬 기준이 아니라서 `floorKey`/`ceilingKey`/`subMap` 같은 질문은 `TreeMap` 쪽이다.
- "`TreeMap`은 value 기준 정렬인가요?"
  아니다. 기본은 **key 기준 정렬**이다. `Comparator`를 주지 않으면 key의 자연 순서를 쓴다.
- "출력만 예쁘게 하고 싶은데 `HashMap` 써도 되나요?"
  출력 순서가 중요한 순간부터 `HashMap`은 의도가 약하다. `LinkedHashMap`이나 `TreeMap`으로 의도를 드러내는 편이 안전하다.

## 어떤 구현체를 고를지 빠르게 정하기

| 요구사항 한 줄 | 첫 선택 |
|---|---|
| "순서는 상관없고 key로 빨리 찾고 싶다" | `HashMap` |
| "사용자가 입력한 순서대로 보여 주고 싶다" | `LinkedHashMap` |
| "최근에 본 항목이 뒤로 가야 하고 오래된 것을 밀어내고 싶다" | `LinkedHashMap(access-order=true)` |
| "이름순, 날짜순처럼 정렬된 key 순서가 필요하다" | `TreeMap` |
| "`x` 이하/이상에서 가장 가까운 key를 찾아야 한다" | `TreeMap` |
| "`from` 이상 `to` 미만 범위를 잘라 봐야 한다" | `TreeMap` |

## 다음 읽기

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "짧은 요구 문장에서 셋 중 하나를 바로 골라야 한다" | [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md) |
| "`LinkedHashMap` access-order 자체가 아직 헷갈린다" | [LinkedHashMap access-order 미니 프라이머](../../data-structure/linkedhashmap-access-order-mini-primer.md) |
| "조회만 했는데 순서가 바뀐다" | [LinkedHashMap access-order와 캐시 동작 브리지](./linkedhashmap-access-order-cache-behavior-bridge.md) |
| "왜 캐시에서 `B`가 지워지지" | [LinkedHashMap access-order와 캐시 동작 브리지](./linkedhashmap-access-order-cache-behavior-bridge.md) |
| "조회 규칙과 immutable key까지 같이 비교하고 싶다" | [HashMap vs LinkedHashMap vs TreeMap Key Contract Bridge](./hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md) |
| "`Map`을 돌 때 `entrySet()`/`keySet()`/`values()` 중 뭘 써야 하지?" | [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md) |
| "`TreeMap`에서 왜 두 번째 `put`이 덮어써지지?" | [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md) |
| "`firstKey`, `floorKey` 같은 탐색은 언제 쓰지?" | [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md) |
| "`subMap(20, 40)`이 왜 `40`을 빼는지 헷갈린다" | [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md) |

## 한 줄 정리

반복 순서를 보여 주는 목적이면 `LinkedHashMap`, 정렬된 key에서 이웃과 범위를 찾는 목적이면 `TreeMap`으로 나눠 읽으면 beginner가 "삽입 순서"와 "range query"를 섞는 실수를 크게 줄일 수 있다.
