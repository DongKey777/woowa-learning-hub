# BigDecimal 조회 전용 미니 드릴: `contains` in `HashSet` vs `TreeSet`

> 한 줄 요약: `BigDecimal("1.0")`를 넣어 두고 `BigDecimal("1")`로 `contains`를 하면, `HashSet`은 못 찾을 수 있고 `TreeSet`은 찾을 수 있다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
> - [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md)
> - [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)

> retrieval-anchor-keywords: bigdecimal hashset treeset contains mini drill, bigdecimal hashset contains false treeset contains true, bigdecimal set lookup compareTo equals mismatch, bigdecimal contains worksheet beginner, java bigdecimal hashset treeset 조회 차이, 자바 bigdecimal contains 연습, 자바 hashset treeset contains 기준

## 먼저 잡을 mental model

처음엔 이 2줄만 기억하면 된다.

- `HashSet.contains(...)`는 `equals()`/`hashCode()` 기준이다
- `TreeSet.contains(...)`는 `compareTo() == 0` 기준이다

`BigDecimal`에서는 `1.0`과 `1`이 이 두 기준에서 갈린다.

- `new BigDecimal("1.0").equals(new BigDecimal("1")) == false`
- `new BigDecimal("1.0").compareTo(new BigDecimal("1")) == 0`

## 10초 비교표

| 조회 시나리오 | `HashSet<BigDecimal>` | `TreeSet<BigDecimal>` |
|---|---|---|
| `add("1.0")` 후 `contains("1")` | `false` 가능 | `true` 가능 |
| `add("1.0")` 후 `contains("1.00")` | `false` 가능 | `true` 가능 |

## 1페이지 조회 드릴

### 드릴 코드

```java
import java.math.BigDecimal;
import java.util.HashSet;
import java.util.Set;
import java.util.TreeSet;

Set<BigDecimal> hash = new HashSet<>();
hash.add(new BigDecimal("1.0"));

Set<BigDecimal> tree = new TreeSet<>();
tree.add(new BigDecimal("1.0"));

System.out.println(hash.contains(new BigDecimal("1")));
System.out.println(hash.contains(new BigDecimal("1.00")));
System.out.println(tree.contains(new BigDecimal("1")));
System.out.println(tree.contains(new BigDecimal("1.00")));
```

### 실행 전 워크시트

| 질문 | 내 답(실행 전) |
|---|---|
| `hash.contains(new BigDecimal("1"))` |  |
| `hash.contains(new BigDecimal("1.00"))` |  |
| `tree.contains(new BigDecimal("1"))` |  |
| `tree.contains(new BigDecimal("1.00"))` |  |

### 정답

- `hash.contains(new BigDecimal("1"))` -> `false`
- `hash.contains(new BigDecimal("1.00"))` -> `false`
- `tree.contains(new BigDecimal("1"))` -> `true`
- `tree.contains(new BigDecimal("1.00"))` -> `true`

## 초보자 혼동 포인트

- `Set`은 둘 다 "중복 제거 컬렉션"이니까 조회 기준도 같을 거라고 생각하기 쉽다
- `TreeSet.contains(...)` 성공을 "숫자니까 Java가 알아서 맞춰 줬다"로 오해하기 쉽다
- `HashSet.contains(...)` 실패를 reference 비교 문제로 착각하기 쉽다

안전한 습관:

- 조회 버그가 나면 먼저 `equals` 기준인지 `compareTo == 0` 기준인지 적는다
- `BigDecimal`을 `Set`에 넣으면 `1`, `1.0`, `1.00`으로 `contains`를 한 번씩 예측해 본다
- 팀 규칙으로 "`1`과 `1.0`을 같은 원소로 볼지"를 먼저 정한다

## 다음 읽기

- map 조회까지 확장: [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
- 중복/덮어쓰기까지 확장: [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md)
- 개념 정리: [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
