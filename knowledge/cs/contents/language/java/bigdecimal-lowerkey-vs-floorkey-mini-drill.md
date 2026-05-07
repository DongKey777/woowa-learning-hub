---
schema_version: 3
title: BigDecimal lowerKey vs floorKey Mini Drill
concept_id: language/bigdecimal-lowerkey-vs-floorkey-mini-drill
canonical: true
category: language
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 87
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- bigdecimal-navigablemap
- floor-lower-boundary
- ordered-map
aliases:
- BigDecimal lowerKey floorKey drill
- BigDecimal floorKey lowerKey exact match
- BigDecimal NavigableMap strict inclusive lookup
- TreeMap BigDecimal lowerKey null floorKey same slot
- 자바 BigDecimal lowerKey floorKey 차이
- NavigableMap boundary null
symptoms:
- floorKey는 exact match 자리를 포함하고 lowerKey는 제외한다는 inclusive vs strict 차이를 BigDecimal scale 차이와 같이 놓쳐
- lowerKey가 null을 반환할 때 null key 저장으로 오해하고 boundary result로 읽지 못해
- query key의 문자열 모양이 아니라 map 안의 저장된 key 표현이 반환된다는 점이 헷갈려
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- language/lower-vs-floor-exact-match-mini-drill
- language/bigdecimal-navigablemap-lookup-bridge
next_docs:
- language/bigdecimal-navigablemap-lookup-bridge
- language/ordered-map-null-safe-practice-drill
- language/ceiling-vs-higher-exact-match-mini-drill
linked_paths:
- contents/language/java/lower-vs-floor-exact-match-mini-drill.md
- contents/language/java/bigdecimal-navigablemap-lookup-bridge.md
- contents/language/java/bigdecimal-hashmap-treemap-lookup-mini-drill.md
- contents/language/java/bigdecimal-sorted-collection-bridge.md
- contents/language/java/bigdecimal-key-policy-30-second-checklist.md
confusable_with:
- language/lower-vs-floor-exact-match-mini-drill
- language/bigdecimal-navigablemap-lookup-bridge
- language/ceiling-vs-higher-exact-match-mini-drill
forbidden_neighbors: []
expected_queries:
- BigDecimal TreeMap에서 floorKey와 lowerKey가 1.0 1.00 exact match에서 왜 다르게 나와?
- lowerKey(new BigDecimal(\"1\"))가 null이면 null key가 저장된 뜻인지 boundary result인지 알려줘
- BigDecimal lowerKey floorKey 차이를 strict inclusive lookup으로 설명해줘
- TreeMap에 1.0을 넣고 1이나 1.00으로 floorKey lowerKey를 호출하면 뭐가 나와?
- NavigableMap에서 반환되는 key가 query key 모양이 아니라 저장된 key인 이유를 알려줘
contextual_chunk_prefix: |
  이 문서는 BigDecimal TreeMap lowerKey vs floorKey를 exact match, compareTo == 0, strict vs inclusive boundary result 관점으로 손예측하는 beginner drill이다.
  BigDecimal lowerKey floorKey, NavigableMap, boundary null, 1.0 vs 1.00, ordered map lookup 질문이 본 문서에 매핑된다.
---
# BigDecimal `lowerKey` vs `floorKey` Mini Drill

> 한 줄 요약: `TreeMap<BigDecimal, V>`에서 `BigDecimal("1.0")`를 넣어 둔 뒤 `BigDecimal("1")`나 `BigDecimal("1.00")`로 물으면, `floorKey`는 같은 숫자 자리에 멈추지만 `lowerKey`는 그 자리를 포함하지 않는다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README: Java primer](../README.md#java-primer)
- [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)
- [BigDecimal NavigableMap Lookup Bridge: `floorKey`, `ceilingKey`, and Range Lookups](./bigdecimal-navigablemap-lookup-bridge.md)
- [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
- [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md)

retrieval-anchor-keywords: bigdecimal lowerkey floorkey mini drill, bigdecimal lowerkey floorkey exact match, bigdecimal 1.0 1.00 lower floor treemap, bigdecimal numerically equal different scale lowerkey, bigdecimal strict vs inclusive lookup drill, treemap bigdecimal lowerkey null floorkey same slot, bigdecimal boundary null vs null key treemap, navigablemap bigdecimal beginner prediction, 자바 bigdecimal lowerkey floorkey 차이, 자바 bigdecimal scale 다른 key 조회, 자바 strict inclusive lookup 연습, bigdecimal lowerkey vs floorkey mini drill basics, bigdecimal lowerkey vs floorkey mini drill beginner, 처음 bigdecimal lowerkey null 헷갈림, java basics

## 먼저 잡을 mental model

이번 드릴은 이 두 줄만 고정하면 된다.

- `floorKey(x)`: `x`와 같은 숫자 자리가 있으면 그 자리에 멈춘다
- `lowerKey(x)`: `x`와 같은 숫자 자리가 있어도 그 자리는 제외하고 더 작은 자리로 간다

`BigDecimal`에서는 query key의 scale이 달라도 comparator 줄에서는 같은 자리일 수 있다.

```java
new BigDecimal("1.0").compareTo(new BigDecimal("1")) == 0
new BigDecimal("1.0").compareTo(new BigDecimal("1.00")) == 0
```

그래서 `1.0`, `1`, `1.00`은 `TreeMap` navigation에서 같은 숫자 자리처럼 읽어야 한다.

같이 붙여 둘 해석도 있다.

> `lowerKey(...) == null`은 "strict하게 더 작은 key가 없다"는 boundary result이지, `TreeMap`이 `null` key를 받아들였다는 뜻이 아니다.

## 10초 비교표

map 안에 이 key만 있다고 하자.

```java
map.put(new BigDecimal("1.0"), "one");
```

| 호출 | 결과 | 이유 |
|---|---|---|
| `floorKey(new BigDecimal("1"))` | `1.0` | 같은 숫자 자리 포함 |
| `lowerKey(new BigDecimal("1"))` | `null` | 같은 숫자 자리는 strict하게 제외 |
| `floorKey(new BigDecimal("1.00"))` | `1.0` | scale이 달라도 같은 자리 |
| `lowerKey(new BigDecimal("1.00"))` | `null` | 같은 자리 제외 후 더 작은 key가 없음 |

초보자 포인트는 한 줄이다.

- `BigDecimal`에서 exact match는 "문자열 모양이 같은가"가 아니라 `compareTo() == 0`인가로 읽는다

## 1페이지 예측 드릴

```java
import java.math.BigDecimal;
import java.util.TreeMap;

TreeMap<BigDecimal, String> priceBand = new TreeMap<>();
priceBand.put(new BigDecimal("1.0"), "one");
priceBand.put(new BigDecimal("2.00"), "two");

System.out.println(priceBand.floorKey(new BigDecimal("1")));
System.out.println(priceBand.lowerKey(new BigDecimal("1")));
System.out.println(priceBand.floorKey(new BigDecimal("1.00")));
System.out.println(priceBand.lowerKey(new BigDecimal("1.00")));
System.out.println(priceBand.floorKey(new BigDecimal("1.50")));
System.out.println(priceBand.lowerKey(new BigDecimal("1.50")));
```

실행 전에 먼저 적어 보자.

| 호출 | 내 답 |
|---|---|
| `floorKey(new BigDecimal("1"))` |  |
| `lowerKey(new BigDecimal("1"))` |  |
| `floorKey(new BigDecimal("1.00"))` |  |
| `lowerKey(new BigDecimal("1.00"))` |  |
| `floorKey(new BigDecimal("1.50"))` |  |
| `lowerKey(new BigDecimal("1.50"))` |  |

정답:

- `floorKey(new BigDecimal("1")) -> 1.0`
- `lowerKey(new BigDecimal("1")) -> null`
- `floorKey(new BigDecimal("1.00")) -> 1.0`
- `lowerKey(new BigDecimal("1.00")) -> null`
- `floorKey(new BigDecimal("1.50")) -> 1.0`
- `lowerKey(new BigDecimal("1.50")) -> 1.0`

여기서 `null`은 "`1`과 같은 숫자 자리는 strict하게 제외했고, 그보다 더 작은 key가 map 안에 없음"이라는 뜻이다.
삽입 시 `null` key를 허용하느냐와는 다른 문제라서, boundary-result `null`과 key 정책 `null`을 분리해 읽어야 덜 헷갈린다.

## 왜 `1`에서는 갈리고 `1.50`에서는 같을까

정렬 줄을 이렇게 그리면 쉽다.

```text
1.0   2.00
```

- `1`과 `1.00`은 `1.0`과 같은 숫자 자리에 선다
- exact match 자리에서는 `floorKey`만 포함되고 `lowerKey`는 한 칸 왼쪽을 찾는다
- `1.50`은 exact match가 아니므로 둘 다 `1.0`을 가리킨다

짧게 외우면:

> `BigDecimal` scale이 달라도 comparator상 exact match면 `floorKey`만 멈추고 `lowerKey`는 지나간다.

## 자주 헷갈리는 순간

- `lowerKey(new BigDecimal("1"))`도 `1.0`일 거라고 생각하기 쉽다
- `1`과 `1.0`이 `equals()`로 다르니 `floorKey(new BigDecimal("1"))`도 못 찾을 거라고 생각하기 쉽다
- 반환되는 key가 query key 모양인 `1`이나 `1.00`일 거라고 생각하기 쉽다
- `lowerKey(new BigDecimal("1")) == null`을 보고 "`TreeMap`이 `null`을 저장했나?"로 오해하기 쉽다

안전한 읽기 순서:

1. comparator 줄에서 같은 숫자 자리인지 먼저 본다
2. exact match면 `floorKey`는 포함, `lowerKey`는 제외로 읽는다
3. 반환되는 key는 query key가 아니라 map 안에 저장된 key 표현이라고 본다
4. strict하게 한 칸 왼쪽이 없으면 `null`은 boundary result라고 읽는다

## 다음 읽기

- `ceilingKey`와 range API까지 이어서 보려면: [BigDecimal NavigableMap Lookup Bridge: `floorKey`, `ceilingKey`, and Range Lookups](./bigdecimal-navigablemap-lookup-bridge.md)
- 조회 기준 자체를 먼저 굳히려면: [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
- `lower`/`floor`를 `TreeSet` 감각으로 먼저 익히려면: [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)
- boundary-result `null`과 `null` key 규칙을 분리하고 싶다면: [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)

## 한 줄 정리

`TreeMap<BigDecimal, V>`에서 `1.0`, `1`, `1.00`이 comparator상 같은 숫자 자리라면, `floorKey`는 그 자리를 포함하지만 `lowerKey`는 strict하게 제외하고, 더 작은 key가 없을 때의 `null`은 boundary result로 읽어야 한다.
