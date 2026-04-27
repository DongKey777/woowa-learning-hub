# BigDecimal Comparator Tie-Breaker 미니 드릴

> 한 줄 요약: `BigDecimal`의 natural ordering은 scale을 무시하므로, `TreeSet`/`TreeMap`에서 `1.0`과 `1.00`을 둘 다 남기고 싶다면 "값 비교 후 scale tie-breaker"를 붙여야 한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
> - [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [Comparator Consistency With `equals()` Bridge](./comparator-consistency-with-equals-bridge.md)
> - [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md)
> - [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)

> retrieval-anchor-keywords: language-java-00126, bigdecimal comparator tie breaker, bigdecimal treeset comparator scale, bigdecimal treemap comparator scale, bigdecimal value then scale comparator, bigdecimal custom comparator distinct scale, bigdecimal 1.0 1.00 treeset both kept, bigdecimal 1.0 1.00 treemap separate keys, comparator naturalOrder thenComparingInt scale, java bigdecimal scale sensitive sorted collection, java bigdecimal custom comparator beginner, 자바 bigdecimal comparator tie breaker, 자바 bigdecimal treeset scale 유지, 자바 bigdecimal treemap scale 유지, 자바 bigdecimal compareTo scale 무시, 자바 bigdecimal custom comparator 연습

## 먼저 잡을 mental model

초보자 기준으로는 아래 두 줄이면 충분하다.

- 기본 `TreeSet<BigDecimal>`/`TreeMap<BigDecimal, V>`는 `compareTo()`를 쓴다
- `BigDecimal.compareTo()`는 scale을 무시하므로 `1.0`과 `1.00`을 같은 자리로 볼 수 있다

그래서 scale 차이도 보존하고 싶다면 comparator에 마지막 구분자를 직접 붙여야 한다.

> 값 순서는 `compareTo()`로 유지하고, 같은 숫자 안에서는 `scale()`로 다시 나눈다.

## 문제 장면 한 장 요약

| 비교 규칙 | `1.0` vs `1.00` 결과 | `TreeSet`/`TreeMap`에서 보이는 현상 |
|---|---|---|
| natural ordering (`compareTo`) | 같은 값 | 하나로 합쳐지거나 value가 덮어써질 수 있음 |
| `value -> scale` comparator | 다른 값으로 끝까지 구분 | 둘 다 남길 수 있음 |

이 문서의 목표는 "정렬을 바꾸자"가 아니라 "숫자 순서는 유지하면서 scale-sensitive entry도 살려 보자"다.

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
labels.put(new BigDecimal("2.0"), "scale-1-two");

System.out.println(amounts);
System.out.println(amounts.size());
System.out.println(labels.size());
System.out.println(labels.get(new BigDecimal("1.0")));
System.out.println(labels.get(new BigDecimal("1.00")));
```

## 실행 전 30초 손예측

| 질문 | 내 답 |
|---|---|
| `amounts` 출력 순서 |  |
| `amounts.size()` |  |
| `labels.size()` |  |
| `labels.get(new BigDecimal("1.0"))` |  |
| `labels.get(new BigDecimal("1.00"))` |  |

## 정답

- `amounts` -> `[1.0, 1.00, 2.0]`
- `amounts.size()` -> `3`
- `labels.size()` -> `3`
- `labels.get(new BigDecimal("1.0"))` -> `"scale-1"`
- `labels.get(new BigDecimal("1.00"))` -> `"scale-2"`

핵심은 `1.0`과 `1.00`이 숫자로는 같아도 comparator가 마지막에 `scale()`까지 보므로 `compare(...) == 0`으로 끝나지 않는다는 점이다.

## 왜 이 comparator가 두 요구를 같이 만족하나

```java
Comparator<BigDecimal> byValueThenScale =
        Comparator.<BigDecimal>naturalOrder()
                .thenComparingInt(BigDecimal::scale);
```

위 한 줄을 초보자 눈으로 풀면 이렇게 읽으면 된다.

1. 먼저 숫자 크기대로 정렬한다
2. 숫자가 같으면 scale이 작은 쪽을 앞에 둔다
3. 그래서 `1.0`과 `1.00`은 같은 숫자 그룹 안에서 다른 자리로 갈라진다

짧은 비교표로 보면 더 쉽다.

| 비교 단계 | `1.0` vs `1.00` |
|---|---|
| `compareTo()` | `0` |
| `scale()` 비교 | `1` vs `2` |
| 최종 comparator 결과 | `0`이 아님 |

즉 tie-breaker는 보기 좋은 정렬용이 아니라, 여기서는 "같은 숫자라도 scale-sensitive entry를 따로 남길지"를 결정하는 distinctness 규칙이다.

## `TreeMap`에서 특히 기억할 점

이 comparator를 쓰면 `TreeMap`도 scale별로 다른 key 칸을 가진다.

| key | value |
|---|---|
| `1.0` | `"scale-1"` |
| `1.00` | `"scale-2"` |
| `2.0` | `"scale-1-two"` |

그래서 아래처럼 읽으면 된다.

- natural ordering `TreeMap`이면 `1.0`과 `1.00`이 같은 key 칸으로 합쳐질 수 있다
- `byValueThenScale` `TreeMap`이면 scale까지 key identity에 포함된다

이건 장점이지만, 동시에 조회 기준도 바뀐다는 뜻이다.

- `labels.get(new BigDecimal("1.0"))`는 `"scale-1"`
- `labels.get(new BigDecimal("1.00"))`는 `"scale-2"`
- `labels.get(new BigDecimal("1"))`는 `null`일 수 있다

즉 "scale을 보존하고 싶다"는 요구가 있을 때만 이 comparator가 맞다.

## 초보자 공통 혼동

- `thenComparingInt(BigDecimal::scale)`를 붙이면 정렬만 달라지고 distinctness는 그대로라고 생각하기 쉽다.
- `TreeMap`에서 custom comparator를 쓰면 조회는 여전히 `compareTo()` 기준일 거라고 생각하기 쉽다.
- `1.0`과 `1.00`을 둘 다 남기고 싶으면서도 `get(new BigDecimal("1"))`도 둘 다 찾길 기대하기 쉽다.

안전한 기억법:

- 같은 숫자를 한 칸으로 모으고 싶다 -> natural ordering 쪽
- 같은 숫자라도 scale 차이를 살리고 싶다 -> tie-breaker 추가

## 한 줄 정리

`TreeSet`/`TreeMap`에서 `BigDecimal`의 숫자 순서는 유지하되 `1.0`과 `1.00` 같은 scale-sensitive entry를 둘 다 남기고 싶다면, `Comparator.naturalOrder().thenComparingInt(BigDecimal::scale)`처럼 tie-breaker를 직접 넣어야 한다.
