# BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`

> 한 줄 요약: `BigDecimal("1.0")`와 `BigDecimal("1.00")`는 hash 기준(`equals`)에서는 다르고 sorted 기준(`compareTo == 0`)에서는 같은 자리처럼 보일 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: bigdecimal 1 0 vs 1 00 collections mini drill basics, bigdecimal 1 0 vs 1 00 collections mini drill beginner, bigdecimal 1 0 vs 1 00 collections mini drill intro, java basics, beginner java, 처음 배우는데 bigdecimal 1 0 vs 1 00 collections mini drill, bigdecimal 1 0 vs 1 00 collections mini drill 입문, bigdecimal 1 0 vs 1 00 collections mini drill 기초, what is bigdecimal 1 0 vs 1 00 collections mini drill, how to bigdecimal 1 0 vs 1 00 collections mini drill
> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [Beginner Drill Sheet: Equality vs Ordering](./equality-vs-ordering-beginner-drill-sheet.md)
> - [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
> - [BigDecimal Comparator Tie-Breaker 미니 드릴](./bigdecimal-comparator-tie-breaker-mini-drill.md)
> - [BigDecimal 조회 전용 미니 드릴: `contains` in `HashSet` vs `TreeSet`](./bigdecimal-hashset-treeset-contains-mini-drill.md)
> - [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)

> retrieval-anchor-keywords: bigdecimal mini drill, bigdecimal 1.0 1.00 worksheet, hashset treeset treemap bigdecimal result, bigdecimal equals compareTo beginner practice, java collection prediction exercise, compareTo 0 same slot, treeset duplicate bigdecimal, treemap overwrite bigdecimal, hashset size bigdecimal surprise, 자바 bigdecimal 1.0 1.00 연습, 자바 hashset treeset treemap 결과 예측

## 먼저 잡을 mental model

처음엔 아래 2줄만 기억하면 된다.

- `HashSet`은 `equals()/hashCode()` 기준으로 중복을 판단한다
- `TreeSet`/`TreeMap`은 `compareTo() == 0` 기준으로 같은 자리를 판단한다

`BigDecimal`에서는 이 두 기준이 갈릴 수 있다.

- `new BigDecimal("1.0").equals(new BigDecimal("1.00")) == false`
- `new BigDecimal("1.0").compareTo(new BigDecimal("1.00")) == 0`

## 한 장 결과표

| 컬렉션 | 판단 기준 | `1.0`, `1.00` 넣었을 때 |
|---|---|---|
| `HashSet<BigDecimal>` | `equals()/hashCode()` | 둘 다 남을 수 있음 (`size == 2`) |
| `TreeSet<BigDecimal>` | `compareTo() == 0` | 하나로 합쳐질 수 있음 (`size == 1`) |
| `TreeMap<BigDecimal, V>` | key `compareTo() == 0` | 같은 key 자리로 보고 나중 값이 덮어씀 |

## 1페이지 미니 드릴

### 드릴 코드

```java
import java.math.BigDecimal;
import java.util.HashSet;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;

Set<BigDecimal> hash = new HashSet<>();
hash.add(new BigDecimal("1.0"));
hash.add(new BigDecimal("1.00"));

Set<BigDecimal> tree = new TreeSet<>();
tree.add(new BigDecimal("1.0"));
tree.add(new BigDecimal("1.00"));

TreeMap<BigDecimal, String> map = new TreeMap<>();
String prev1 = map.put(new BigDecimal("1.0"), "A");
String prev2 = map.put(new BigDecimal("1.00"), "B");

System.out.println(hash.size());
System.out.println(tree.size());
System.out.println(prev1);
System.out.println(prev2);
System.out.println(map.size());
System.out.println(map.get(new BigDecimal("1")));
```

### 실행 전 워크시트

| 질문 | 내 답(실행 전) |
|---|---|
| `hash.size()` |  |
| `tree.size()` |  |
| `prev1` |  |
| `prev2` |  |
| `map.size()` |  |
| `map.get(new BigDecimal("1"))` |  |

### 정답

- `hash.size()` -> `2`
- `tree.size()` -> `1`
- `prev1` -> `null`
- `prev2` -> `"A"`
- `map.size()` -> `1`
- `map.get(new BigDecimal("1"))` -> `"B"`

## 초보자 혼동 포인트

- "숫자가 같아 보이니 `HashSet`도 1개겠지"라고 생각하기 쉽다
- "record/값 객체면 어디서나 같은 기준으로 중복이 제거되겠지"라고 생각하기 쉽다
- `TreeMap`에서 값이 바뀌는 이유를 key reference 동일성으로 오해하기 쉽다

안전한 습관:

- `BigDecimal`을 컬렉션에 넣기 전에 "우리 도메인은 `1.0`과 `1.00`을 같은 값으로 볼지"를 먼저 정한다
- sorted 컬렉션을 쓰면 `compareTo() == 0` 조건을 한 줄로 적고 시작한다
- `size()`와 `put` 반환값을 실행 전에 먼저 예측한다

## 다음 읽기

- 확장 드릴: [Beginner Drill Sheet: Equality vs Ordering](./equality-vs-ordering-beginner-drill-sheet.md)
- set 조회 전용: [BigDecimal 조회 전용 미니 드릴: `contains` in `HashSet` vs `TreeSet`](./bigdecimal-hashset-treeset-contains-mini-drill.md)
- 조회 전용: [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
- 개념 정리: [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- 정렬 컬렉션 감각: [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)

## 한 줄 정리

`BigDecimal("1.0")`와 `BigDecimal("1.00")`는 hash 기준(`equals`)에서는 다르고 sorted 기준(`compareTo == 0`)에서는 같은 자리처럼 보일 수 있다.
