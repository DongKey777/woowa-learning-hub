---
schema_version: 3
title: BigDecimal Comparator Tie-Breaker Mini Drill
concept_id: language/bigdecimal-comparator-tie-breaker-mini-drill
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
- bigdecimal-comparator
- treeset-treemap
- comparator-tie-breaker
aliases:
- BigDecimal comparator tie breaker
- BigDecimal value then scale comparator
- BigDecimal TreeSet scale
- BigDecimal TreeMap scale
- thenComparingInt BigDecimal scale
- 자바 BigDecimal scale tie breaker
symptoms:
- BigDecimal TreeSet에서 1.0과 1.00을 둘 다 남기고 싶은데 natural ordering이 compareTo 0으로 합치는 이유를 놓쳐
- tie-breaker가 단순 정렬 장식이 아니라 sorted collection의 같은 key 여부까지 바꾼다는 점이 헷갈려
- scale을 살린 comparator를 쓰면 get 조회도 같은 표현 scale로 해야 한다는 점을 예상하지 못해
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- language/bigdecimal-sorted-collection-bridge
next_docs:
- language/comparator-consistency-with-equals-bridge
- language/treeset-treemap-comparator-tie-breaker-basics
- language/bigdecimal-hashmap-treemap-lookup-mini-drill
linked_paths:
- contents/language/java/bigdecimal-sorted-collection-bridge.md
- contents/language/java/bigdecimal-1-0-vs-1-00-collections-mini-drill.md
- contents/language/java/comparator-consistency-with-equals-bridge.md
- contents/language/java/treeset-treemap-comparator-tie-breaker-basics.md
- contents/language/java/bigdecimal-hashmap-treemap-lookup-mini-drill.md
confusable_with:
- language/bigdecimal-sorted-collection-bridge
- language/comparator-consistency-with-equals-bridge
- language/treeset-treemap-comparator-tie-breaker-basics
forbidden_neighbors: []
expected_queries:
- BigDecimal TreeSet에서 1.0과 1.00을 둘 다 남기려면 comparator를 어떻게 만들어야 해?
- Comparator.naturalOrder 다음 thenComparingInt BigDecimal scale을 붙이면 조회 기준도 바뀌나?
- BigDecimal TreeMap에서 scale tie breaker를 쓰면 get(new BigDecimal(\"1\"))가 왜 null이야?
- comparator tie breaker가 sorted collection distinctness를 바꾸는 이유를 알려줘
- BigDecimal value then scale comparator 미니 드릴을 풀고 싶어
contextual_chunk_prefix: |
  이 문서는 BigDecimal TreeSet/TreeMap에서 natural ordering 뒤 scale tie-breaker를 붙여 1.0과 1.00을 따로 남기는 beginner drill이다.
  BigDecimal comparator, thenComparingInt scale, TreeSet distinctness, TreeMap lookup, compareTo vs tie-breaker 질문이 본 문서에 매핑된다.
---
# BigDecimal Comparator Tie-Breaker 미니 드릴

> 한 줄 요약: `TreeSet`/`TreeMap`에서 `BigDecimal`의 숫자값은 같지만 scale은 다른 `1.0`과 `1.00`을 둘 다 남기고 싶다면, `compareTo()` 뒤에 `scale()` tie-breaker를 직접 붙여야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README: Java primer](../README.md#java-primer)
- [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md)
- [Comparator Consistency With `equals()` Bridge](./comparator-consistency-with-equals-bridge.md)
- [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)

retrieval-anchor-keywords: bigdecimal comparator tie breaker, bigdecimal treeset scale, bigdecimal treemap scale, bigdecimal 1.0 1.00 treeset, bigdecimal value then scale comparator, java bigdecimal compareto scale 무시, 자바 bigdecimal treeset 구분, 처음 배우는데 bigdecimal comparator, why bigdecimal treeset merges, how to keep 1.0 1.00, bigdecimal custom comparator beginner, sorted collection bigdecimal distinctness

## 먼저 잡을 mental model

- 기본 `TreeSet<BigDecimal>`/`TreeMap<BigDecimal, V>`는 `compareTo()` 결과로 같은 자리인지 판단한다.
- `BigDecimal.compareTo()`는 scale을 무시하므로 `1.0`과 `1.00`을 같은 숫자로 본다.
- 그래서 scale 차이도 남기고 싶다면 "숫자 비교 후 scale 비교"를 한 번 더 붙여야 한다.

짧게 외우면 이 문장이다.

> natural ordering은 "숫자값"만 보고, tie-breaker는 "같은 숫자 안에서 다시 나누는 규칙"이다.

## 한눈에 보는 비교

| 규칙 | `1.0` vs `1.00` | `TreeSet`/`TreeMap` 결과 |
|---|---|---|
| `compareTo()`만 사용 | 같은 값 | 같은 자리로 합쳐질 수 있다 |
| `compareTo()` 후 `scale()` 비교 | 다른 값 | 둘 다 따로 남길 수 있다 |

여기서 tie-breaker는 보기 좋은 정렬 장식이 아니다.
sorted collection 안에서 "같은 원소인가, 다른 원소인가"를 끝까지 나누는 기준이다.

## 드릴 코드

```java
import java.math.BigDecimal;
import java.util.Comparator;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;

Comparator<BigDecimal> byValueThenScale =
        Comparator.<BigDecimal>naturalOrder()
                .thenComparingInt(BigDecimal::scale);

Set<BigDecimal> amounts = new TreeSet<>(byValueThenScale);
amounts.add(new BigDecimal("1.0"));
amounts.add(new BigDecimal("1.00"));
amounts.add(new BigDecimal("2.0"));

TreeMap<BigDecimal, String> labels = new TreeMap<>(byValueThenScale);
labels.put(new BigDecimal("1.0"), "scale-1");
labels.put(new BigDecimal("1.00"), "scale-2");

System.out.println(amounts);
System.out.println(amounts.size());
System.out.println(labels.get(new BigDecimal("1.0")));
System.out.println(labels.get(new BigDecimal("1.00")));
System.out.println(labels.get(new BigDecimal("1")));
```

## 실행 전 손예측

| 질문 | 예상 |
|---|---|
| `amounts` |  |
| `amounts.size()` |  |
| `labels.get(new BigDecimal("1.0"))` |  |
| `labels.get(new BigDecimal("1.00"))` |  |
| `labels.get(new BigDecimal("1"))` |  |

정답은 이렇게 읽으면 된다.

- `amounts` -> `[1.0, 1.00, 2.0]`
- `amounts.size()` -> `3`
- `labels.get(new BigDecimal("1.0"))` -> `"scale-1"`
- `labels.get(new BigDecimal("1.00"))` -> `"scale-2"`
- `labels.get(new BigDecimal("1"))` -> `null`

## 왜 `get(new BigDecimal("1"))`는 `null`일까

`byValueThenScale`은 두 단계를 본다.

1. 먼저 `compareTo()`로 숫자값을 비교한다.
2. 숫자값이 같으면 `scale()`로 다시 비교한다.

그래서 `1`, `1.0`, `1.00`은 숫자값은 같아도 scale이 각각 `0`, `1`, `2`라서 모두 다른 key 자리다.

| key | scale | 같은 자리인가 |
|---|---|---|
| `1` | `0` | 아니오 |
| `1.0` | `1` | 아니오 |
| `1.00` | `2` | 아니오 |

즉 "scale을 살린다"는 말은 조회 기준도 같이 바뀐다는 뜻이다.

## 초보자 공통 혼동

- `thenComparingInt(BigDecimal::scale)`를 붙여도 정렬만 달라지고 distinctness는 그대로라고 생각하기 쉽다.
- `TreeMap`에서 custom comparator를 써도 `get()`은 여전히 `compareTo()`만 볼 거라고 생각하기 쉽다.
- `1.0`과 `1.00`을 둘 다 남기고 싶으면서 `1`로도 둘 다 찾히길 기대하기 쉽다.

안전한 선택 순서는 이렇다.

- 같은 숫자는 한 칸으로 합쳐도 된다 -> natural ordering 유지
- 같은 숫자라도 표현 차이를 남겨야 한다 -> tie-breaker 추가
- 표현 차이를 남겼다면 조회도 같은 표현으로 해야 한다

## 다음에 어디로 이어서 읽을까

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| `HashSet`과 `TreeSet` 결과가 왜 갈리지? | [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md) |
| comparator와 `equals()` 관계가 헷갈린다 | [Comparator Consistency With `equals()` Bridge](./comparator-consistency-with-equals-bridge.md) |
| tie-breaker를 언제 붙여야 할지 더 보고 싶다 | [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md) |

## 한 줄 정리

`TreeSet`/`TreeMap`에서 `BigDecimal`의 숫자 순서는 유지하되 `1.0`과 `1.00`을 따로 남기고 싶다면, `Comparator.naturalOrder().thenComparingInt(BigDecimal::scale)`처럼 scale tie-breaker를 직접 넣어야 한다.
