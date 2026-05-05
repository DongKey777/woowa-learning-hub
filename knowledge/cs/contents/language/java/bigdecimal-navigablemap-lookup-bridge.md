---
schema_version: 3
title: 'BigDecimal NavigableMap Lookup Bridge: `floorKey`, `ceilingKey`, and Range Lookups'
concept_id: language/bigdecimal-navigablemap-lookup-bridge
canonical: false
category: language
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- treemap-bigdecimal-key-semantics
- compareto-vs-equals
aliases:
- bigdecimal navigablemap lookup bridge
- bigdecimal floorkey ceilingkey treemap
- bigdecimal range lookup scale difference
- bigdecimal 1.0 1 treemap floor ceiling
- bigdecimal submap headmap tailmap compareto equals
- bigdecimal numerically equal different scale treemap
- bigdecimal tree map same slot range query
- 자바 bigdecimal floorkey ceilingkey
- 자바 bigdecimal submap 범위 조회
- 자바 bigdecimal scale 다른데 treemap 조회됨
- 자바 bigdecimal navigablemap beginner
- bigdecimal navigablemap lookup bridge basics
- bigdecimal navigablemap lookup bridge beginner
- bigdecimal navigablemap lookup bridge intro
- java basics
symptoms:
- TreeMap에 1.0을 넣었는데 1이나 1.00으로도 조회돼서 이상해
- floorKey와 ceilingKey가 scale이 다른 값에도 같은 자리처럼 동작해
- headMap 경계에서 exact match를 빼야 하는지 포함해야 하는지 헷갈려
intents:
- comparison
prerequisites:
- language/navigablemap-navigableset-mental-model
- language/bigdecimal-sorted-collection-bridge
next_docs:
- language/bigdecimal-lowerkey-vs-floorkey-mini-drill
- language/bigdecimal-hashmap-treemap-lookup-mini-drill
linked_paths:
- contents/language/java/navigablemap-navigableset-mental-model.md
- contents/language/java/submap-boundaries-primer.md
- contents/language/java/lower-vs-floor-exact-match-mini-drill.md
- contents/language/java/bigdecimal-lowerkey-vs-floorkey-mini-drill.md
- contents/language/java/bigdecimal-sorted-collection-bridge.md
- contents/language/java/bigdecimal-hashmap-treemap-lookup-mini-drill.md
- contents/language/java/bigdecimal-key-policy-30-second-checklist.md
confusable_with:
- language/bigdecimal-hashmap-treemap-lookup-mini-drill
- language/lower-vs-floor-exact-match-mini-drill
forbidden_neighbors: []
expected_queries:
- TreeMap<BigDecimal>에서 1과 1.0이 왜 같은 자리로 조회돼?
- floorKey와 ceilingKey가 scale 다른 숫자에도 붙는 이유가 뭐야?
- BigDecimal key로 headMap 경계를 읽는 법을 초보자 기준으로 설명해줘
- 1.00으로 찾았는데 1.0 key가 돌아오는 이유를 알고 싶어
- subMap inclusive false가 exact match에서 어떻게 동작하는지 예제로 보고 싶어
contextual_chunk_prefix: |
  이 문서는 Java 학습자가 BigDecimal key를 TreeMap에서 조회할 때 숫자
  비교와 표현 비교가 어떻게 이어지는지 연결하는 bridge다. 1과 1.0이
  같은 자리로 잡힘, floorKey가 어디에 멈추는지, scale 다른 값으로 범위
  조회, exact match 제외 headMap, 저장된 대표 key가 반환됨 같은 자연어
  paraphrase가 본 문서의 조회 규칙에 매핑된다.
---
# BigDecimal NavigableMap Lookup Bridge: `floorKey`, `ceilingKey`, and Range Lookups

> 한 줄 요약: `TreeMap<BigDecimal, V>`에서 `1.0`과 `1`은 `equals()`로는 다르지만 `compareTo() == 0`이면 같은 key 자리로 취급되므로, `floorKey`/`ceilingKey`/`subMap` 같은 조회도 숫자 기준으로 붙어서 동작한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README: Java primer](../README.md#java-primer)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)
- [BigDecimal `lowerKey` vs `floorKey` Mini Drill](./bigdecimal-lowerkey-vs-floorkey-mini-drill.md)
- [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
- [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md)

retrieval-anchor-keywords: bigdecimal navigablemap lookup bridge, bigdecimal floorkey ceilingkey treemap, bigdecimal range lookup scale difference, bigdecimal 1.0 1 treemap floor ceiling, bigdecimal submap headmap tailmap compareto equals, bigdecimal numerically equal different scale treemap, bigdecimal tree map same slot range query, 자바 bigdecimal floorkey ceilingkey, 자바 bigdecimal submap 범위 조회, 자바 bigdecimal scale 다른데 treemap 조회됨, 자바 bigdecimal navigablemap beginner, bigdecimal navigablemap lookup bridge basics, bigdecimal navigablemap lookup bridge beginner, bigdecimal navigablemap lookup bridge intro, java basics

## 먼저 잡을 mental model

처음에는 이 한 줄로 잡으면 된다.

> `TreeMap<BigDecimal, V>`의 navigation 조회는 "문자열 모양"이 아니라 `compareTo()`가 만든 숫자 줄 위에서 움직인다.

그래서 `BigDecimal("1.0")`을 저장해 두면:

- `get(new BigDecimal("1"))`도 찾을 수 있다
- `floorKey(new BigDecimal("1"))`도 그 자리를 찾을 수 있다
- `ceilingKey(new BigDecimal("1.00"))`도 그 자리를 찾을 수 있다

이유는 셋 다 `BigDecimal.compareTo() == 0`인 같은 자리로 보기 때문이다.

## 제일 먼저 구분할 2줄

`BigDecimal`에서는 "같다"가 둘로 갈린다.

```java
new BigDecimal("1.0").equals(new BigDecimal("1"));     // false
new BigDecimal("1.0").compareTo(new BigDecimal("1"));  // 0
```

`NavigableMap` 계열에서 중요한 쪽은 `equals()`가 아니라 `compareTo()` 쪽이다.

| 질문 | `TreeMap<BigDecimal, V>`의 기준 |
|---|---|
| 같은 key 자리인가? | `compareTo() == 0` |
| `floorKey`/`ceilingKey`가 어디에 멈추나? | comparator가 만든 정렬 줄 |
| `subMap`/`headMap`/`tailMap` 경계가 포함되나? | 경계값과 `compareTo()`로 비교 |

## 10초 결과표

map에 이 key 하나만 있다고 하자.

```java
map.put(new BigDecimal("1.0"), "saved");
```

그때 결과는 이렇게 읽으면 된다.

| 호출 | 결과 | 읽는 법 |
|---|---|---|
| `map.get(new BigDecimal("1"))` | `"saved"` | 숫자로 같은 자리 |
| `map.floorKey(new BigDecimal("1"))` | `1.0` | exact match처럼 멈춤 |
| `map.ceilingKey(new BigDecimal("1.00"))` | `1.0` | exact match처럼 멈춤 |
| `map.headMap(new BigDecimal("1"), true)` | `{1.0=saved}` | `1`과 같은 자리 포함 |
| `map.headMap(new BigDecimal("1"), false)` | `{}` | exact match 자리 제외 |
| `map.tailMap(new BigDecimal("1.00"), true)` | `{1.0=saved}` | 같은 자리부터 시작 |

초보자 포인트:

- 조회 기준은 숫자 비교다
- 반환되는 key object는 "질문에 사용한 key"가 아니라 "map 안에 저장돼 있던 대표 key"다

## 1분 예제: `floorKey`와 `ceilingKey`

```java
import java.math.BigDecimal;
import java.util.TreeMap;

TreeMap<BigDecimal, String> priceBand = new TreeMap<>();
priceBand.put(new BigDecimal("1.0"), "one");
priceBand.put(new BigDecimal("2.00"), "two");

System.out.println(priceBand.floorKey(new BigDecimal("1")));
System.out.println(priceBand.ceilingKey(new BigDecimal("1.00")));
System.out.println(priceBand.floorKey(new BigDecimal("1.50")));
System.out.println(priceBand.ceilingKey(new BigDecimal("1.50")));
```

| 호출 | 결과 | 이유 |
|---|---|---|
| `floorKey(new BigDecimal("1"))` | `1.0` | `1`과 `1.0`은 같은 자리 |
| `ceilingKey(new BigDecimal("1.00"))` | `1.0` | `1.00`도 같은 자리 |
| `floorKey(new BigDecimal("1.50"))` | `1.0` | `1.50` 이하 중 가장 가까운 key |
| `ceilingKey(new BigDecimal("1.50"))` | `2.00` | `1.50` 이상 중 가장 가까운 key |

여기서 첫 두 줄이 핵심이다.

- query key의 scale이 달라도
- comparator상 같은 숫자 위치면 exact match처럼 읽힌다

## 초보자가 많이 놓치는 지점: 저장된 key 모양은 첫 key가 남을 수 있다

아래 코드를 보자.

```java
TreeMap<BigDecimal, String> map = new TreeMap<>();
map.put(new BigDecimal("1.0"), "first");
map.put(new BigDecimal("1.00"), "second");

System.out.println(map.size());
System.out.println(map.firstKey());
System.out.println(map.get(new BigDecimal("1")));
```

결과는 보통 이렇게 읽힌다.

- `map.size()` -> `1`
- `map.firstKey()` -> `1.0`
- `map.get(new BigDecimal("1"))` -> `"second"`

왜 이런가?

- 두 번째 `put`은 새 key 칸을 만들지 못한다
- `compareTo() == 0`이라 기존 자리의 value만 바꾼다
- 그래서 value는 `"second"`로 바뀌어도 저장된 key 표현은 첫 key인 `1.0`이 남을 수 있다

즉 "숫자 기준 조회"와 "보여지는 key 문자열"은 따로 볼 필요가 있다.

## range-style lookup은 어떻게 읽나

range API도 똑같이 comparator 줄을 따른다.

```java
import java.math.BigDecimal;
import java.util.NavigableMap;
import java.util.TreeMap;

TreeMap<BigDecimal, String> map = new TreeMap<>();
map.put(new BigDecimal("1.0"), "one");
map.put(new BigDecimal("2.0"), "two");
map.put(new BigDecimal("3.0"), "three");

NavigableMap<BigDecimal, String> a = map.headMap(new BigDecimal("2"), true);
NavigableMap<BigDecimal, String> b = map.headMap(new BigDecimal("2.00"), false);
NavigableMap<BigDecimal, String> c = map.tailMap(new BigDecimal("2"), true);
NavigableMap<BigDecimal, String> d = map.subMap(new BigDecimal("1"), false, new BigDecimal("3.00"), true);
```

| view | 결과 | 읽는 법 |
|---|---|---|
| `headMap(new BigDecimal("2"), true)` | `{1.0=one, 2.0=two}` | `2`와 같은 자리 포함 |
| `headMap(new BigDecimal("2.00"), false)` | `{1.0=one}` | `2.00`과 같은 자리 제외 |
| `tailMap(new BigDecimal("2"), true)` | `{2.0=two, 3.0=three}` | `2`와 같은 자리부터 시작 |
| `subMap(new BigDecimal("1"), false, new BigDecimal("3.00"), true)` | `{2.0=two, 3.0=three}` | `1` 자리는 제외, `3.00` 자리는 포함 |

짧게 번역하면:

- inclusive `true`는 "그 숫자 자리를 잡아둔다"
- inclusive `false`는 "그 숫자 자리 exact match를 잘라 낸다"

## `floorKey`/`ceilingKey`와 range API를 한 장으로 연결하기

같은 숫자 줄에서 보면 더 덜 헷갈린다.

```text
1.0   2.0   3.0
```

| 질문 | 같은 감각 |
|---|---|
| `floorKey(2)` | `2`와 같은 자리에 멈춘다 |
| `ceilingKey(2.00)` | `2.00`과 같은 자리에 멈춘다 |
| `headMap(2, true)` | 그 멈춘 자리까지 포함한다 |
| `headMap(2, false)` | 그 멈춘 자리는 뺀다 |
| `tailMap(2.00, true)` | 그 멈춘 자리부터 시작한다 |
| `subMap(1, false, 3, true)` | 왼쪽 exact match는 빼고, 오른쪽 exact match는 포함한다 |

즉 navigation 조회와 range 조회는 따로 놀지 않는다.
둘 다 같은 comparator 줄을 공유한다.

## 자주 하는 오해

- "`BigDecimal("1.0")`와 `BigDecimal("1")`은 `equals()`가 false니까 `floorKey(1)`도 못 찾겠지"라고 생각하기 쉽다.
- `headMap(2, false)`를 "문자열 `2.00`만 제외"처럼 읽기 쉽다. 실제로는 숫자 기준 같은 자리 전체를 제외하는 감각으로 읽어야 한다.
- `ceilingKey(1)`가 `1`을 새로 만들어 돌려준다고 생각하기 쉽다. 실제로는 map 안에 있던 key object를 돌려준다.

## 안전한 실무 습관

- `BigDecimal`을 sorted key로 쓰면 `1`, `1.0`, `1.00`을 섞은 조회 테스트를 꼭 넣는다.
- range 경계 테스트는 inclusive `true`와 `false`를 exact match 숫자로 각각 한 번씩 적는다.
- "scale도 의미다"가 도메인 규칙이면 입력 경계에서 canonicalization 정책을 먼저 정한다.

## 다음 읽기

- 조회 기준 자체를 먼저 굳히려면: [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
- `BigDecimal`의 `equals()`/`compareTo()` 큰 그림은: [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- `lowerKey`와 `floorKey` strict/inclusive 차이만 따로 손예측하려면: [BigDecimal `lowerKey` vs `floorKey` Mini Drill](./bigdecimal-lowerkey-vs-floorkey-mini-drill.md)
- inclusive/exclusive 경계만 따로 연습하려면: [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- `floor`와 `lower` exact match 차이만 따로 보면: [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)

## 한 줄 정리

`TreeMap<BigDecimal, V>`의 `floorKey`, `ceilingKey`, `headMap`, `tailMap`, `subMap`은 모두 `compareTo()`가 만든 숫자 줄 위에서 동작하므로, scale이 달라도 숫자로 같은 `BigDecimal`은 같은 key 자리처럼 취급된다.
