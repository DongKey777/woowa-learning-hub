# BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`

> 한 줄 요약: `BigDecimal("1.0")`를 넣어 두고 `BigDecimal("1")`로 조회하면, `HashMap`은 못 찾을 수 있고 `TreeMap`은 찾을 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: bigdecimal hashmap treemap lookup mini drill basics, bigdecimal hashmap treemap lookup mini drill beginner, bigdecimal hashmap treemap lookup mini drill intro, java basics, beginner java, 처음 배우는데 bigdecimal hashmap treemap lookup mini drill, bigdecimal hashmap treemap lookup mini drill 입문, bigdecimal hashmap treemap lookup mini drill 기초, what is bigdecimal hashmap treemap lookup mini drill, how to bigdecimal hashmap treemap lookup mini drill
> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
> - [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md)
> - [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md)
> - [BigDecimal NavigableMap Lookup Bridge: `floorKey`, `ceilingKey`, and Range Lookups](./bigdecimal-navigablemap-lookup-bridge.md)
> - [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)

> retrieval-anchor-keywords: bigdecimal hashmap treemap lookup mini drill, bigdecimal containsKey get 차이, bigdecimal hashmap get null treemap get success, bigdecimal 1.0 1 조회, equals compareTo lookup mismatch, bigdecimal lookup confusion beginner, bigdecimal key policy checklist, bigdecimal floorkey ceilingkey range lookup, 자바 bigdecimal hashmap treemap 조회 차이, 자바 containsKey get 혼동

## 먼저 잡을 mental model

처음엔 이 2줄만 기억하면 된다.

- `HashMap` 조회는 key의 `equals()`/`hashCode()` 기준이다
- `TreeMap` 조회는 key의 `compareTo() == 0` 기준이다

`BigDecimal`에서는 `1.0`과 `1`이 이 두 기준에서 갈린다.

- `new BigDecimal("1.0").equals(new BigDecimal("1")) == false`
- `new BigDecimal("1.0").compareTo(new BigDecimal("1")) == 0`

## 10초 비교표

| 조회 시나리오 | `HashMap<BigDecimal, V>` | `TreeMap<BigDecimal, V>` |
|---|---|---|
| `put("1.0")` 후 `get("1")` | `null` 가능 | 값 조회 가능 |
| `put("1.0")` 후 `containsKey("1")` | `false` 가능 | `true` 가능 |

## 1페이지 조회 드릴

### 드릴 코드

```java
import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;
import java.util.TreeMap;

Map<BigDecimal, String> hash = new HashMap<>();
hash.put(new BigDecimal("1.0"), "saved");

Map<BigDecimal, String> tree = new TreeMap<>();
tree.put(new BigDecimal("1.0"), "saved");

System.out.println(hash.containsKey(new BigDecimal("1")));
System.out.println(hash.get(new BigDecimal("1")));
System.out.println(tree.containsKey(new BigDecimal("1")));
System.out.println(tree.get(new BigDecimal("1")));
```

### 실행 전 워크시트

| 질문 | 내 답(실행 전) |
|---|---|
| `hash.containsKey(new BigDecimal("1"))` |  |
| `hash.get(new BigDecimal("1"))` |  |
| `tree.containsKey(new BigDecimal("1"))` |  |
| `tree.get(new BigDecimal("1"))` |  |

### 정답

- `hash.containsKey(new BigDecimal("1"))` -> `false`
- `hash.get(new BigDecimal("1"))` -> `null`
- `tree.containsKey(new BigDecimal("1"))` -> `true`
- `tree.get(new BigDecimal("1"))` -> `"saved"`

## 초보자 혼동 포인트

- 숫자로 같아 보이니 두 맵 조회도 같을 거라고 생각하기 쉽다
- `TreeMap` 조회 성공을 "운 좋게 hash가 맞았다"로 오해하기 쉽다
- `HashMap` 조회 실패를 key reference 비교 문제로 착각하기 쉽다

안전한 습관:

- 조회 버그가 나면 먼저 key 비교 기준을 적는다: `equals`인지 `compareTo == 0`인지
- `BigDecimal` key를 쓸 때 `containsKey`/`get`을 `1.0`과 `1` 둘 다로 테스트한다
- 팀 규칙으로 "`1.0`과 `1`을 같은 key로 볼지"를 먼저 정한다

## 다음 읽기

- PR 점검용: [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md)
- 확장 드릴: [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md)
- 개념 정리: [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- 범위 조회까지 연결: [BigDecimal NavigableMap Lookup Bridge: `floorKey`, `ceilingKey`, and Range Lookups](./bigdecimal-navigablemap-lookup-bridge.md)

## 한 줄 정리

`BigDecimal("1.0")`를 넣어 두고 `BigDecimal("1")`로 조회하면, `HashMap`은 못 찾을 수 있고 `TreeMap`은 찾을 수 있다.
