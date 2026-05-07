---
schema_version: 3
title: BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap
concept_id: language/bigdecimal-sorted-collection-bridge
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
- bigdecimal-equals-compareto
- sorted-collection-surprise
- collection-key-policy
aliases:
- BigDecimal compareTo equals
- BigDecimal HashSet TreeSet TreeMap
- BigDecimal sorted collection bridge
- BigDecimal 1.0 1.00 difference
- BigDecimal equals scale compareTo scale ignored
- 자바 BigDecimal 컬렉션 기준
symptoms:
- BigDecimal에는 숫자값 기준 compareTo와 표현 scale까지 보는 equals가 모두 있다는 점을 모르고 컬렉션 결과를 예측해
- TreeSet에서 원소가 사라지거나 TreeMap에서 value가 덮이는 현상을 compareTo 0 같은 자리 판정으로 설명하지 못해
- 도메인에서 1.0과 1.00을 같은 값으로 볼지 먼저 정하지 않고 HashSet TreeSet TreeMap을 선택해
intents:
- definition
- comparison
- troubleshooting
prerequisites:
- language/java-collections-basics
- language/java-comparable-comparator-basics
next_docs:
- language/bigdecimal-1-0-vs-1-00-collections-mini-drill
- language/bigdecimal-hashset-treeset-contains-mini-drill
- language/bigdecimal-hashmap-treemap-lookup-mini-drill
- language/bigdecimal-comparator-tie-breaker-mini-drill
linked_paths:
- contents/language/java/java-collections-basics.md
- contents/language/java/java-comparable-comparator-basics.md
- contents/language/java/hashset-vs-treeset-duplicate-semantics.md
- contents/language/java/treeset-treemap-natural-ordering-compareto-bridge.md
- contents/language/java/bigdecimal-hashset-treeset-contains-mini-drill.md
- contents/language/java/treeset-treemap-comparator-tie-breaker-basics.md
- contents/language/java/bigdecimal-comparator-tie-breaker-mini-drill.md
- contents/language/java/bigdecimal-key-policy-30-second-checklist.md
- contents/language/java/bigdecimal-striptrailingzeros-input-boundary-bridge.md
- contents/language/java/bigdecimal-hashmap-treemap-lookup-mini-drill.md
- contents/language/java/bigdecimal-money-equality-rounding-serialization-pitfalls.md
- contents/data-structure/treemap-vs-hashmap-vs-linkedhashmap.md
confusable_with:
- language/hashset-vs-treeset-duplicate-semantics
- language/treeset-treemap-natural-ordering-compareto-bridge
- language/bigdecimal-comparator-tie-breaker-mini-drill
forbidden_neighbors: []
expected_queries:
- BigDecimal equals와 compareTo 차이가 HashSet TreeSet TreeMap에서 어떻게 다르게 나타나?
- BigDecimal 1.0과 1.00이 HashSet에는 둘 다 남고 TreeSet에는 하나만 남을 수 있는 이유가 뭐야?
- TreeMap BigDecimal key가 compareTo 0이면 value를 덮어쓰는 이유를 설명해줘
- BigDecimal을 collection key로 쓰기 전에 도메인의 같음 기준을 어떻게 정해야 해?
- BigDecimal sorted collection surprise를 초보자에게 예제로 알려줘
contextual_chunk_prefix: |
  이 문서는 BigDecimal compareTo vs equals 차이를 HashSet, TreeSet, TreeMap collection behavior와 key policy로 설명하는 beginner primer다.
  BigDecimal 1.0 vs 1.00, equals scale, compareTo scale ignored, sorted set duplicate, TreeMap overwrite, HashMap lookup 질문이 본 문서에 매핑된다.
---
# BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap

> 한 줄 요약: `BigDecimal`은 "숫자로 같은가"와 "표현까지 같은가"를 다르게 다루므로, `1.0`과 `1.00`이 `HashSet`에서는 둘 다 남고 `TreeSet`/`TreeMap`에서는 같은 자리처럼 보일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- [BigDecimal 조회 전용 미니 드릴: `contains` in `HashSet` vs `TreeSet`](./bigdecimal-hashset-treeset-contains-mini-drill.md)
- [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- [BigDecimal Comparator Tie-Breaker 미니 드릴](./bigdecimal-comparator-tie-breaker-mini-drill.md)
- [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md)
- [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md)
- [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
- [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
- [TreeMap vs HashMap vs LinkedHashMap](../../data-structure/treemap-vs-hashmap-vs-linkedhashmap.md)

retrieval-anchor-keywords: bigdecimal compareto equals, bigdecimal hashset treeset treemap, java bigdecimal collection behavior, bigdecimal 1.0 1.00 difference, bigdecimal equals scale, bigdecimal compareto scale ignored, bigdecimal hashset duplicate, bigdecimal treeset duplicate, bigdecimal treemap overwrite, bigdecimal sorted collection surprise, bigdecimal sorted set duplicate, bigdecimal sorted map overwrite, bigdecimal compareto equals mismatch, why bigdecimal equals false, beginner bigdecimal collections

## 핵심 개념

초보자용으로 가장 안전한 기억법은 이것이다.

> `BigDecimal`에는 "같다"가 두 개 있고, 컬렉션은 그중 무엇을 쓰는지에 따라 결과가 달라진다.

- `compareTo()`는 숫자 크기를 본다
- `equals()`는 숫자와 scale을 함께 본다
- `HashSet`은 `equals()`/`hashCode()`를 따른다
- `TreeSet`/`TreeMap`은 natural ordering인 `compareTo()`를 따른다

그래서 `BigDecimal("1.0")`와 `BigDecimal("1.00")`는 사람 눈에는 같아 보여도 컬렉션마다 다르게 처리될 수 있다.

## 먼저 보는 sorted collection surprise

많이 놀라는 장면은 사실 정렬 자체보다 "같은 자리 판정"이다.

> `TreeSet`/`TreeMap`은 `equals()`가 아니라 `compareTo() == 0`이면 같은 자리라고 본다.

그래서 `BigDecimal`에서는 아래 두 가지 surprise가 한 번에 나온다.

| 컬렉션 | 초보자가 기대하기 쉬운 결과 | 실제로 자주 만나는 결과 |
|---|---|---|
| `TreeSet<BigDecimal>` | `1.0`, `1.00`이 둘 다 남는다 | 숫자로 같아서 하나만 남을 수 있다 |
| `TreeMap<BigDecimal, V>` | 두 key가 따로 저장된다 | 같은 key 자리로 보고 나중 값이 덮어쓸 수 있다 |

이 문서를 읽을 때는 "정렬 컬렉션은 중복 제거 컬렉션"보다 아래 문장을 먼저 기억하는 편이 덜 헷갈린다.

- `TreeSet` surprise: 원소가 사라진 것처럼 보일 수 있다
- `TreeMap` surprise: 값이 갑자기 덮어써진 것처럼 보일 수 있다
- 원인은 둘 다 `BigDecimal.compareTo() == 0`이다

## 한눈에 보기

| 위치 | 무엇을 같다고 보나 | `1.0` vs `1.00` 결과 |
|---|---|---|
| `a.compareTo(b) == 0` | 숫자 값이 같은가 | `true` |
| `a.equals(b)` | 숫자와 scale이 같은가 | `false` |
| `HashSet<BigDecimal>` | `equals()`/`hashCode()` | 둘 다 들어갈 수 있다 |
| `TreeSet<BigDecimal>` | `compareTo() == 0` | 하나만 남을 수 있다 |
| `TreeMap<BigDecimal, V>` | key의 `compareTo() == 0` | 같은 key 자리로 보고 나중 값이 덮어써질 수 있다 |

짧게 외우면 다음 한 줄이면 충분하다.

- hash 기반 컬렉션은 `equals()`
- sorted 컬렉션은 `compareTo()`

## 30초 mental movie: 왜 "중복"과 "덮어쓰기"가 같이 나오나

초보자에게는 아래 순서로 그리면 가장 이해가 빠르다.

1. `1.0`을 넣는다
2. `1.00`을 넣는다
3. sorted 컬렉션은 두 값을 `compareTo() == 0`으로 본다
4. 그래서 "새 칸 생성"이 아니라 "기존 칸 재사용"처럼 동작한다

그 결과가 컬렉션별로 다르게 보인다.

| 컬렉션 | 기존 칸 재사용이 눈에 보이는 방식 |
|---|---|
| `TreeSet` | 새 원소가 따로 늘지 않아 `size()`가 그대로다 |
| `TreeMap` | 같은 key 칸으로 보고 value가 바뀐다 |

즉 "`TreeSet`은 duplicate surprise", "`TreeMap`은 overwrite surprise"라고 나눠 외우면 된다.

## 15초 선택 흐름: 도메인의 "같음" 기준부터 고정하기

컬렉션 API를 고르기 전에 아래 두 질문을 먼저 결정하면 대부분의 혼동을 줄일 수 있다.

| 먼저 답할 질문 | `Yes`라면 | `No`라면 |
|---|---|---|
| `1.0`과 `1.00`을 같은 값으로 볼까? | 입력 경계에서 정규화 정책을 먼저 정한다 | scale 차이를 의미로 보존하는 정책을 명시한다 |
| 정렬/범위 조회가 핵심일까? | `TreeSet`/`TreeMap`을 쓰되 `compareTo() == 0` 충돌을 테스트한다 | `HashSet`/`HashMap`의 `equals()` 기준을 먼저 테스트한다 |

핵심은 "어떤 컬렉션을 쓸까?"보다 "우리 도메인의 같음이 무엇인가?"를 먼저 고정하는 것이다.

## 조회(`contains`/`get`)에서 특히 헷갈리는 이유

입문자가 실제로 많이 막히는 지점은 "중복"보다 "조회"다.

| 조회 연산 | hash 계열(`HashSet`/`HashMap`) | sorted 계열(`TreeSet`/`TreeMap`) |
|---|---|---|
| 기준 | `equals()`/`hashCode()` | `compareTo() == 0` |
| `new BigDecimal("1.0")` 저장 후 `new BigDecimal("1")`로 조회 | 못 찾을 수 있음 | 찾을 수 있음 |

```java
import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;
import java.util.TreeMap;

Map<BigDecimal, String> hash = new HashMap<>();
hash.put(new BigDecimal("1.0"), "saved-in-hash");

Map<BigDecimal, String> tree = new TreeMap<>();
tree.put(new BigDecimal("1.0"), "saved-in-tree");

System.out.println(hash.get(new BigDecimal("1"))); // null
System.out.println(tree.get(new BigDecimal("1"))); // saved-in-tree
```

이 예제를 기억해 두면 "`HashMap`에서는 못 찾는데 `TreeMap`에서는 찾아진다"는 상황을 바로 설명할 수 있다.

조회만 따로 짧게 손예측하고 싶으면 아래 두 문서로 나눠서 보면 된다.

- set 조회만 먼저: [BigDecimal 조회 전용 미니 드릴: `contains` in `HashSet` vs `TreeSet`](./bigdecimal-hashset-treeset-contains-mini-drill.md)
- map 조회까지 확장: [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)

## 1분 재현 예제: 왜 결과가 갈리는지 한 번에 보기

```java
import java.math.BigDecimal;
import java.util.HashSet;
import java.util.Set;
import java.util.TreeMap;

Set<BigDecimal> hash = new HashSet<>();
hash.add(new BigDecimal("1.0"));

TreeMap<BigDecimal, String> tree = new TreeMap<>();
tree.put(new BigDecimal("1.0"), "first");
tree.put(new BigDecimal("1.00"), "second");

System.out.println(hash.contains(new BigDecimal("1"))); // false
System.out.println(tree.size());                        // 1
System.out.println(tree.get(new BigDecimal("1")));      // second
```

초보자 관점에서 포인트는 두 줄이다.

- `HashSet.contains(new BigDecimal("1"))`가 `false`가 될 수 있다 (`equals()` 기준)
- `TreeMap`은 `1.0`과 `1.00`을 같은 key 자리로 보고 값이 합쳐질 수 있다 (`compareTo()` 기준)

같은 장면을 sorted collection surprise만 좁혀서 다시 말하면 아래처럼 요약된다.

| 장면 | 왜 이런가 |
|---|---|
| `TreeSet`에 두 번 넣었는데 `size() == 1` | `compareTo() == 0`이라 같은 원소 자리 |
| `TreeMap`에 두 번 `put`했는데 `size() == 1` | `compareTo() == 0`이라 같은 key 자리 |
| `TreeMap.get(new BigDecimal("1"))`가 `"second"` | 조회도 같은 비교 규칙을 쓴다 |

## 왜 `BigDecimal`은 두 규칙이 갈릴까

`BigDecimal`은 숫자 값만 들고 있는 것이 아니라 scale도 함께 가진다.

```java
import java.math.BigDecimal;

BigDecimal a = new BigDecimal("1.0");
BigDecimal b = new BigDecimal("1.00");

System.out.println(a.compareTo(b) == 0); // true
System.out.println(a.equals(b));         // false
```

왜 이런 결과가 나올까?

- `compareTo()`는 "수학적으로 같은 수인가"를 본다
- `equals()`는 "표현까지 같은 값 객체인가"를 본다

즉 `1.0`과 `1.00`은 숫자로는 같지만 표현은 다르다. 이 차이가 컬렉션 규칙까지 그대로 이어진다.

## `HashSet`에서는 왜 둘 다 남을까

`HashSet`은 해시 기반 컬렉션이라 최종 중복 판단을 `equals()`로 한다.

```java
import java.math.BigDecimal;
import java.util.HashSet;
import java.util.Set;

Set<BigDecimal> amounts = new HashSet<>();
amounts.add(new BigDecimal("1.0"));
amounts.add(new BigDecimal("1.00"));

System.out.println(amounts.size()); // 2
```

이 결과는 이상한 것이 아니다.

- 두 값은 `compareTo()`로는 같아도
- `equals()`는 `false`다
- 그래서 `HashSet`은 서로 다른 원소로 본다

`BigDecimal`을 `HashSet` 원소나 `HashMap` key처럼 쓸 때는 "scale 차이도 다른 값으로 볼 것인가"를 먼저 정해야 한다.

## `TreeSet`과 `TreeMap`에서는 왜 하나처럼 보일까

`TreeSet`과 `TreeMap`은 기본적으로 natural ordering을 쓰므로 `BigDecimal.compareTo()`를 기준으로 움직인다.

```java
import java.math.BigDecimal;
import java.util.TreeMap;
import java.util.TreeSet;

TreeSet<BigDecimal> sortedAmounts = new TreeSet<>();
sortedAmounts.add(new BigDecimal("1.0"));
sortedAmounts.add(new BigDecimal("1.00"));

TreeMap<BigDecimal, String> labels = new TreeMap<>();
labels.put(new BigDecimal("1.0"), "first");
labels.put(new BigDecimal("1.00"), "second");

System.out.println(sortedAmounts.size());                  // 1
System.out.println(labels.size());                         // 1
System.out.println(labels.get(new BigDecimal("1.000")));   // second
```

여기서 핵심은 `compareTo() == 0`이다.

- `TreeSet`은 같은 원소 자리라고 보고 하나만 유지할 수 있다
- `TreeMap`은 같은 key 자리라고 보고 나중 `put`의 값으로 바꾼다

즉 `TreeMap`에서 값이 덮어써지는 이유는 key reference가 같아서가 아니라, `BigDecimal.compareTo()`가 같은 key 자리라고 보기 때문이다.

초보자용으로 더 짧게 바꾸면 다음처럼 외우면 된다.

- `TreeSet`: "둘 다 저장"이 아니라 "이미 있던 칸이라 추가 안 함"
- `TreeMap`: "둘 다 저장"이 아니라 "이미 있던 key 칸이라 value 교체"

## 흔한 오해와 함정

- `compareTo() == 0`이면 `equals() == true`라고 착각하기 쉽지만, `BigDecimal`은 대표적인 반례다.
- `HashSet`과 `TreeSet` 결과가 다르면 컬렉션 버그가 아니라 "같음"의 기준이 다른 것이다.
- `TreeMap<BigDecimal, ...>`에 `1.0`과 `1.00`을 따로 넣어 두 값을 모두 보관할 수 있다고 기대하면 값 덮어쓰기를 만나기 쉽다.
- 반대로 scale 차이도 의미 있는 데이터인데 `TreeSet<BigDecimal>`로 dedupe하면 의도보다 많이 합쳐질 수 있다.
- "`sorted`니까 정렬만 다르고 중복 규칙은 `Set`/`Map`이 다 비슷하겠지"라고 생각하기 쉽지만, sorted 컬렉션의 surprise는 바로 그 중복/덮어쓰기 규칙에서 나온다.
- `HashSet`에 `1.0`만 넣어 두고 `contains(new BigDecimal("1"))`가 `true`일 거라고 기대하면 오해하기 쉽다.
- `stripTrailingZeros()` 같은 정규화 도구는 도움이 될 수 있지만, "항상 자동으로 맞는 답"은 아니다. 표현 의미까지 바꾸기 때문이다. 입력 경계 정책으로 짧게 정리한 문서는 [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md).
- `new BigDecimal(0.1)`처럼 `double` 생성자를 쓰면 값 표현 자체가 흔들릴 수 있다. 문자열 기반 생성/파싱 정책은 [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)에서 이어서 확인하는 편이 안전하다.

## 실무에서 쓰는 모습

| 의도 | 초보자용 첫 선택 | 이유 |
|---|---|---|
| 숫자로 같은 금액은 하나로 보고 싶다 | 입력 경계에서 scale 정책을 정해 정규화한다 | `HashSet`과 `TreeSet` 결과를 덜 놀랍게 만든다 |
| `1.0`과 `1.00`을 다른 표현으로 보존해야 한다 | `equals()` 기준 컬렉션과 명시적 표현 정책을 함께 쓴다 | scale 차이가 사라지지 않는다 |
| 범위 조회나 정렬이 필요하다 | `TreeMap`/`TreeSet`을 쓰되 `compareTo() == 0` 충돌을 의식한다 | 숫자로 같은 값은 같은 자리로 합쳐질 수 있다 |

실무에서 가장 먼저 할 질문은 이것이다.

- 우리 도메인은 `1.0`과 `1.00`을 같은 값으로 보나?
- 아니면 표시/직렬화/입력 의미까지 달라서 다른 값으로 보나?

이 답을 먼저 정하면 어떤 컬렉션을 써야 할지도 훨씬 분명해진다.

## 더 깊이 가려면

지금 막힌 질문별로 다음 문서를 고르면 탐색 속도가 빨라진다.

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| List/Set/Map 첫 선택 자체가 아직 낯설다 | [Java 컬렉션 프레임워크 입문](./java-collections-basics.md) |
| hash와 sorted 컬렉션의 중복 규칙 자체가 헷갈린다 | [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md) |
| `TreeSet`/`TreeMap`에서 `compareTo() == 0` 의미를 더 정확히 보고 싶다 | [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md) |
| PR 전에 `1.0` vs `1` key 정책과 테스트 항목을 빠르게 점검하고 싶다 | [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md) |
| comparator tie-breaker까지 확장하고 싶다 | [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md) |
| `stripTrailingZeros()`를 고급 함정 전에 입력 경계 정책으로 먼저 잡고 싶다 | [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md) |
| `BigDecimal` scale/rounding/직렬화까지 확장해서 보고 싶다 | [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md) |

값 객체 `equals()`/`hashCode()` 감각을 먼저 다지고 싶다면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)을 함께 보면 연결이 더 잘 된다.

## 한 줄 정리

`BigDecimal`에서 `1.0`과 `1.00`은 `compareTo()`로는 같고 `equals()`로는 다르기 때문에, `HashSet`은 둘을 따로 담을 수 있지만 `TreeSet`/`TreeMap`은 같은 자리처럼 처리할 수 있다.
