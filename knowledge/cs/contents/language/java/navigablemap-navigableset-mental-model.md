# NavigableMap and NavigableSet Mental Model

> 한 줄 요약: `NavigableSet`/`NavigableMap`의 `first`/`last`/`floor`/`ceiling`/`lower`/`higher`는 정렬 결과를 예쁘게 보여 주는 API가 아니라, comparator가 만든 순서 위에서 가까운 이웃을 찾는 조회 API다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [TreeMap Interval Entry Primer](../../data-structure/treemap-interval-entry-primer.md)
- [Navigable Range API 미니 드릴](./navigable-range-api-mini-drill.md)
- [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)
- [`ceiling` vs `higher` Exact Match 미니 드릴](./ceiling-vs-higher-exact-match-mini-drill.md)
- [`firstEntry()`/`lastEntry()` vs `firstKey()`/`lastKey()` Beginner Bridge](./firstentry-lastentry-vs-firstkey-lastkey-bridge.md)
- [`pollFirst`/`pollLast` vs `first`/`last` Beginner Bridge](./pollfirst-polllast-vs-first-last-beginner-bridge.md)
- [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
- [`descendingKeySet()` vs `descendingMap()` Beginner Bridge](./descendingkeyset-vs-descendingmap-bridge.md)
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
- [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- [`Instant`, `LocalDateTime`, `OffsetDateTime`, `ZonedDateTime` Boundary Design](./java-time-instant-localdatetime-boundaries.md)

retrieval-anchor-keywords: navigablemap mental model, navigableset mental model, treemap floor ceiling lower higher basics, treemap floorkey ceilingkey 뭐예요, treemap floorentry higherentry 언제 쓰나요, floor ceiling lower higher 차이 헷갈려요, 처음 배우는데 navigablemap, treemap 정렬된 key 근처 찾기, 빈 treemap firstkey 왜 예외, 빈 treemap floorkey 왜 null, treemap ceilingkey null 왜 나와요, treemap higherkey null max key, boundary null vs null key treemap, comparator 순서 기준 조회, ordered map range lookup beginner

<details>
<summary>Table of Contents</summary>

- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [`NavigableSet`과 `NavigableMap`은 어디서 만나나](#navigableset과-navigablemap은-어디서-만나나)
- [메서드 이름을 한 장으로 보기](#메서드-이름을-한-장으로-보기)
- [자연 순서 예제: 숫자 줄에서 이웃 찾기](#자연-순서-예제-숫자-줄에서-이웃-찾기)
- [`TreeMap` 예제: 점수 구간 찾기](#treemap-예제-점수-구간-찾기)
- [작은 워크시트: timestamp와 score bucket에서 이웃 질의](#작은-워크시트-timestamp와-score-bucket에서-이웃-질의)
- [comparator를 뒤집으면 조회 결과도 뒤집힌다](#comparator를-뒤집으면-조회-결과도-뒤집힌다)
- [2행 미니 워크시트: reverse order에서 `floor`/`ceiling` 읽기](#2행-미니-워크시트-reverse-order에서-floorceiling-읽기)
- [custom comparator에서는 질문 객체도 comparator로 해석된다](#custom-comparator에서는-질문-객체도-comparator로-해석된다)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 먼저 잡을 mental model

`TreeSet`과 `TreeMap`을 처음 배울 때는 보통 "자동으로 정렬된다"에 집중한다.
하지만 `NavigableSet`/`NavigableMap`까지 쓰기 시작하면 더 중요한 감각이 필요하다.

> comparator는 단순히 출력 순서를 정하는 도구가 아니라, 컬렉션 안에 "한 줄짜리 좌표계"를 만든다.

그 좌표계 위에서 navigation 메서드는 이런 질문을 한다.

- `first`: 이 줄에서 가장 앞은 누구인가?
- `last`: 이 줄에서 가장 뒤는 누구인가?
- `floor(x)`: `x`와 같거나, `x` 바로 앞쪽에 있는 가장 가까운 값은 무엇인가?
- `ceiling(x)`: `x`와 같거나, `x` 바로 뒤쪽에 있는 가장 가까운 값은 무엇인가?
- `lower(x)`: `x`보다 strictly 앞쪽에 있는 가장 가까운 값은 무엇인가?
- `higher(x)`: `x`보다 strictly 뒤쪽에 있는 가장 가까운 값은 무엇인가?

여기서 "앞쪽", "뒤쪽", "같다"는 모두 **comparator가 정한 순서 기준**이다.
숫자의 크기, 삽입 순서, 화면에 보이는 느낌이 아니라 비교 규칙이 기준이다.

## `NavigableSet`과 `NavigableMap`은 어디서 만나나

입문자가 가장 자주 만나는 구현체는 다음 두 개다.

| 구현체 | 구현하는 인터페이스 | navigation 대상 |
|---|---|---|
| `TreeSet<E>` | `NavigableSet<E>` | 원소 자체 |
| `TreeMap<K, V>` | `NavigableMap<K, V>` | key |

`TreeSet`은 원소를 comparator 순서로 세운 뒤 가까운 원소를 찾는다.
`TreeMap`은 key를 comparator 순서로 세운 뒤 가까운 key나 entry를 찾는다.

즉 `TreeMap`에서 `floorEntry(87)`을 호출하면 value를 비교하는 것이 아니다.
먼저 key 중에서 `87`에 가장 가까운 위치를 찾고, 그 key에 붙은 value를 돌려준다.

## 메서드 이름을 한 장으로 보기

| 질문 | `NavigableSet` | `NavigableMap` key | `NavigableMap` entry | 포함 여부 |
|---|---|---|---|---|
| 가장 앞 | `first()` | `firstKey()` | `firstEntry()` | 기준값 없음 |
| 가장 뒤 | `last()` | `lastKey()` | `lastEntry()` | 기준값 없음 |
| 기준보다 앞 | `lower(x)` | `lowerKey(x)` | `lowerEntry(x)` | `x` 제외 |
| 기준 이하 | `floor(x)` | `floorKey(x)` | `floorEntry(x)` | `x` 포함 |
| 기준 이상 | `ceiling(x)` | `ceilingKey(x)` | `ceilingEntry(x)` | `x` 포함 |
| 기준보다 뒤 | `higher(x)` | `higherKey(x)` | `higherEntry(x)` | `x` 제외 |

초보자용으로는 이 두 쌍만 먼저 외우면 된다.

- `lower` / `higher`: 기준값과 같은 것은 제외한다
- `floor` / `ceiling`: 기준값과 같은 것도 포함한다

빈 컬렉션에서는 반환 방식도 다르다.

| 호출 | 비어 있을 때 |
|---|---|
| `set.first()`, `set.last()`, `map.firstKey()`, `map.lastKey()` | `NoSuchElementException` |
| `set.floor(x)`, `set.ceiling(x)`, `set.lower(x)`, `set.higher(x)`, `map.floorKey(x)`, `map.ceilingKey(x)`, `map.lowerKey(x)`, `map.higherKey(x)` | `null` |
| `map.firstEntry()`, `map.lastEntry()`, `map.floorEntry(x)`, `map.ceilingEntry(x)`, `map.lowerEntry(x)`, `map.higherEntry(x)` | `null` |

`firstEntry()`/`lastEntry()`와 `firstKey()`/`lastKey()`의 empty behavior만 따로 짧게 고정하고 싶다면 [`firstEntry()`/`lastEntry()` vs `firstKey()`/`lastKey()` Beginner Bridge](./firstentry-lastentry-vs-firstkey-lastkey-bridge.md)를 먼저 보고 돌아오면 된다.

`null` 경계만 3문항으로 짧게 손예측해 보고 싶다면 [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)을 먼저 보고 돌아오면 된다.

## 메서드 이름을 한 장으로 보기 (계속 2)

range view인 `headSet`/`tailSet`/`subSet`, `headMap`/`tailMap`/`subMap` 결과를 먼저 손으로 맞혀 보고 싶다면 [Navigable Range API 미니 드릴](./navigable-range-api-mini-drill.md)부터 보는 편이 빠르다.

## 빈 map warning: `firstKey`/`lastKey`와 `floorKey` 계열은 실패 방식이 다르다

초보자가 가장 자주 하는 착각은 "`TreeMap`에서 못 찾으면 다 `null`이겠지"라고 묶어 버리는 것이다.
하지만 양 끝 조회와 이웃 조회는 실패 방식이 다르다.

| 질문 | 빈 `TreeMap`에서의 결과 | 왜 다르게 동작하나 |
|---|---|---|
| `firstKey()`, `lastKey()` | `NoSuchElementException` | "양 끝 key가 반드시 있어야" 값을 돌려주는 API라서 |
| `lowerKey(x)`, `floorKey(x)`, `ceilingKey(x)`, `higherKey(x)` | `null` | "해당 방향 이웃이 없을 수 있다"를 반환값으로 표현해서 |

짧게 기억하면 이렇다.

- `first`/`last`: 양 끝 원소가 없으면 예외
- `lower`/`floor`/`ceiling`/`higher`: 이웃이 없으면 `null`

여기서의 `null`은 "그 방향 이웃이 없음"이라는 boundary result다.
즉 `ceilingKey(max보다 큰 값)`이나 `higherKey(마지막 key)`에서 나오는 `null`은 `TreeMap`의 `null` key 허용 정책이나 `get(key)`의 `null value` 의미와는 다른 축이다.

```java
TreeMap<Integer, String> map = new TreeMap<>();

map.firstKey();      // NoSuchElementException
map.floorKey(10);    // null
map.ceilingKey(10);  // null
```

그래서 빈 map 가능성이 있으면 아래처럼 읽는 편이 안전하다.

```java
if (map.isEmpty()) {
    return "예약 없음";
}

Integer first = map.firstKey();
Integer next = map.ceilingKey(target);
```

## 자연 순서 예제: 숫자 줄에서 이웃 찾기

가장 단순한 예시는 숫자를 자연 순서로 둔 `TreeSet`이다.

```java
import java.util.List;
import java.util.TreeSet;

TreeSet<Integer> scores = new TreeSet<>(List.of(10, 20, 30, 40));

System.out.println(scores.first());       // 10
System.out.println(scores.last());        // 40
System.out.println(scores.lower(30));     // 20
System.out.println(scores.floor(30));     // 30
System.out.println(scores.ceiling(30));   // 30
System.out.println(scores.higher(30));    // 40
System.out.println(scores.floor(25));     // 20
System.out.println(scores.ceiling(25));   // 30
```

이 줄은 이렇게 생겼다고 보면 된다.

```text
10   20   30   40
```

| 호출 | 결과 | 이유 |
|---|---:|---|
| `first()` | `10` | comparator 순서에서 가장 앞 |
| `last()` | `40` | comparator 순서에서 가장 뒤 |
| `lower(30)` | `20` | `30`은 제외하고 바로 앞 |
| `floor(30)` | `30` | `30`도 포함하므로 자기 자신 |
| `ceiling(30)` | `30` | `30`도 포함하므로 자기 자신 |
| `higher(30)` | `40` | `30`은 제외하고 바로 뒤 |
| `floor(25)` | `20` | `25` 이하 중 가장 가까운 값 |
| `ceiling(25)` | `30` | `25` 이상 중 가장 가까운 값 |

`25`는 set 안에 없어도 된다.
navigation 메서드는 "그 값이 들어 있나?"보다 "그 값이 들어간다면 어느 위치인가?"를 먼저 생각한다.

## `TreeMap` 예제: 점수 구간 찾기

`TreeMap`에서는 이 감각이 구간 조회에 자주 쓰인다.

```java
import java.util.Map;
import java.util.TreeMap;

TreeMap<Integer, String> gradeByMinimumScore = new TreeMap<>();
gradeByMinimumScore.put(0, "F");
gradeByMinimumScore.put(60, "D");
gradeByMinimumScore.put(70, "C");
gradeByMinimumScore.put(80, "B");
gradeByMinimumScore.put(90, "A");

Map.Entry<Integer, String> entry = gradeByMinimumScore.floorEntry(87);

System.out.println(entry.getKey());   // 80
System.out.println(entry.getValue()); // B
```

여기서 key는 "이 등급이 시작되는 최소 점수"다.
`87`점은 정확한 key로 들어 있지 않지만, `87` 이하인 key 중 가장 가까운 key는 `80`이다.

그래서 `floorEntry(87)`은 `80=B` entry를 돌려준다.

| 질문 | 호출 | 결과 |
|---|---|---|
| `87`점의 등급 시작점 | `floorEntry(87)` | `80=B` |
| `80`점의 등급 시작점 | `floorEntry(80)` | `80=B` |
| `59`점의 등급 시작점 | `floorEntry(59)` | `0=F` |
| 다음 등급 시작점 | `higherEntry(87)` | `90=A` |

이 예제에서 핵심은 `TreeMap`이 value인 `"A"`, `"B"`를 비교하지 않는다는 점이다.
navigation은 항상 key의 comparator 순서로 움직인다.

## 작은 워크시트: timestamp와 score bucket에서 이웃 질의

아래 표는 `lower`/`floor`/`ceiling`/`higher`를 문제집처럼 손으로 확인할 때 쓰는 가장 작은 워크시트다.

- timestamp key 줄: `09:00`, `09:30`, `10:00`
- score bucket key 줄: `0`, `60`, `70`, `80`, `90`

| 도메인 | query `x` | `lower(x)` | `floor(x)` | `ceiling(x)` | `higher(x)` | 읽는 법 |
|---|---|---|---|---|---|---|
| timestamp | `09:30` | `09:00` | `09:30` | `09:30` | `10:00` | 정확히 있는 key를 물으면 `floor`/`ceiling`은 자기 자신 |
| timestamp | `09:40` | `09:30` | `09:30` | `10:00` | `10:00` | key 사이 값이면 `floor`는 왼쪽, `ceiling`은 오른쪽 |
| timestamp | `10:10` | `10:00` | `10:00` | `null` | `null` | 마지막 key보다 더 오른쪽이면 `ceiling`/`higher`의 `null`은 오른쪽 이웃이 없다는 뜻 |
| score bucket | `80` | `70` | `80` | `80` | `90` | bucket 시작점을 직접 물으면 `lower`만 strict하게 한 칸 왼쪽 |
| score bucket | `87` | `80` | `80` | `90` | `90` | 현재 등급 시작점은 `floor`, 다음 경계는 `ceiling`/`higher` |

한 줄로 다시 보면 다음 규칙 하나다.

- `lower`/`higher`: strict (같은 key 제외)
- `floor`/`ceiling`: inclusive (같은 key 포함)

이 워크시트 감각을 예약 시간표 문제로 바로 옮겨 보고 싶으면 [TreeMap Interval Entry Primer](../../data-structure/treemap-interval-entry-primer.md)를 이어서 보면 된다. 여기서의 `timestamp` 줄이 그 문서에서는 `예약 시작 시각` 줄로 그대로 바뀐다.

exact match에서 `lower`와 `floor`만 따로 더 짧게 손예측하고 싶다면 [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)을 먼저 보고 돌아와도 된다.

## comparator를 뒤집으면 조회 결과도 뒤집힌다

`floor`라는 이름 때문에 수학의 "내림"을 떠올리기 쉽다.
하지만 `NavigableSet`의 `floor`는 수학 함수가 아니라 comparator 순서 위의 이웃 찾기다.

```java
import java.util.Comparator;
import java.util.List;
import java.util.TreeSet;

TreeSet<Integer> descendingScores =
        new TreeSet<>(Comparator.reverseOrder());
descendingScores.addAll(List.of(10, 20, 30, 40));

System.out.println(descendingScores);       // [40, 30, 20, 10]
System.out.println(descendingScores.first());     // 40
System.out.println(descendingScores.last());      // 10
System.out.println(descendingScores.lower(30));   // 40
System.out.println(descendingScores.floor(25));   // 30
System.out.println(descendingScores.ceiling(25)); // 20
System.out.println(descendingScores.higher(30));  // 20
```

reverse comparator가 만든 줄은 이렇게 읽는다.

```text
40   30   20   10
```

따라서 `floor(25)`가 숫자상 더 작은 `20`이 아니라 `30`을 돌려줄 수 있다.
`25`가 이 줄에 들어간다면 `30`과 `20` 사이에 들어가고, comparator가 만든 줄에서 `25`와 같거나 바로 앞쪽인 값 중 가장 가까운 값이 `30`이기 때문이다.

이 지점이 이 문서의 핵심이다.

> `floor`/`ceiling`/`lower`/`higher`는 숫자의 자연스러운 크기를 보는 것이 아니라, 현재 set/map의 comparator order를 따른다.

## 2행 미니 워크시트: reverse order에서 `floor`/`ceiling` 읽기

초보자가 가장 자주 멈추는 지점만 2행으로 다시 고르면 아래 표다.

- comparator 줄: `40 -> 30 -> 20 -> 10`
- 읽는 질문: "이 줄에서 `x`와 같거나 바로 앞은 `floor`, 같거나 바로 뒤는 `ceiling`"

| 줄 | query `x` | `floor(x)` | `ceiling(x)` | 왜 이렇게 나오나 |
|---|---:|---:|---:|---|
| reverse order | `30` | `30` | `30` | exact match라서 둘 다 자기 자신 |
| reverse order | `25` | `30` | `20` | 이 줄에서는 `30`이 앞쪽, `20`이 뒤쪽이라서 숫자 감각과 반대로 보일 수 있다 |

손으로 읽는 순서는 늘 같다.

1. 숫자 크기부터 보지 말고, comparator가 만든 줄을 먼저 적는다.
2. `floor`는 그 줄에서 왼쪽(앞쪽), `ceiling`은 오른쪽(뒤쪽)을 찾는다.

즉 reverse order에서 헷갈리면 "`floor`는 작은 수"라고 외우지 말고 "`floor`는 comparator 줄에서 앞쪽"이라고 다시 읽는 편이 안전하다.

## custom comparator에서는 질문 객체도 comparator로 해석된다

객체를 넣을 때도 마찬가지다.

```java
import java.util.Comparator;
import java.util.TreeSet;

record Student(long id, String name) {}

TreeSet<Student> students = new TreeSet<>(
        Comparator.comparing(Student::name)
                .thenComparingLong(Student::id)
);

students.add(new Student(10L, "Jin"));
students.add(new Student(20L, "Mina"));
students.add(new Student(30L, "Sora"));

Student query = new Student(25L, "Mina");

System.out.println(students.floor(query));   // Student[id=20, name=Mina]
System.out.println(students.higher(query));  // Student[id=30, name=Sora]
```

`query` 객체가 set 안에 실제로 들어 있을 필요는 없다.
`TreeSet`은 `query`도 같은 comparator로 해석해서 "이 객체가 들어간다면 어느 위치인가?"를 계산한다.

만약 comparator가 `name`만 비교한다면 `id`가 달라도 같은 자리로 볼 수 있다.
그 경우 navigation도 `name` 기준으로만 움직이며, 서로 다른 학생을 구분하지 못한다.

이 내용은 정렬보다 중복/동등성에 더 가까운 주제라서 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)에서 따로 이어서 보면 좋다.

## 초보자가 자주 헷갈리는 지점

- `first()`는 처음 넣은 값이 아니다. comparator 순서에서 가장 앞의 값이다.
- `last()`도 마지막에 넣은 값이 아니다. comparator 순서에서 가장 뒤의 값이다.
- `first()`/`last()`는 양 끝을 보기만 한다. 양 끝을 꺼내면서 제거하는 API는 `pollFirst()`/`pollLast()` 쪽이다.
- `floor(x)`는 숫자 전용 API가 아니다. comparator 순서에서 `x` 이하인 가장 가까운 원소/key를 찾는다.
- `lower(x)`와 `floor(x)`의 차이는 기준값 `x`를 포함하느냐다. `lower`는 제외, `floor`는 포함이다.
- `higher(x)`와 `ceiling(x)`도 같은 방식이다. `higher`는 제외, `ceiling`은 포함이다.
- `ceiling(x) == null`이나 `higher(x) == null`은 "오른쪽 이웃이 없음"이지, `null` key나 `null` value 정책 설명이 아니다.
- `TreeMap`의 navigation은 value가 아니라 key를 기준으로 한다.
- query 값이나 query key가 컬렉션에 실제로 들어 있지 않아도 navigation lookup은 가능하다.
- timestamp에서 `lower(09:30)` 결과는 `09:30`이 아니다. 같은 값을 포함하려면 `floor(09:30)`를 써야 한다.
- comparator가 `0`을 반환하는 두 값은 같은 자리로 취급된다. 이 경우 `TreeSet` 중복 무시나 `TreeMap` value 교체와 같은 surprise도 같이 생길 수 있다.
- `descendingSet()`이나 `descendingMap()` view에서는 navigation 기준도 뒤집힌 view의 comparator order를 따른다. 이 부분만 따로 짧게 다시 보고 싶다면 [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)을 보면 된다.

## 빠른 체크리스트

- `NavigableSet`/`NavigableMap`을 보면 먼저 "현재 comparator order가 무엇인가?"를 확인한다
- `first`/`last`는 삽입 순서가 아니라 comparator 순서의 양 끝이다
- `lower`/`higher`는 strict, `floor`/`ceiling`은 inclusive다
- `TreeMap`에서는 가까운 value가 아니라 가까운 key를 찾는다
- reverse comparator나 `descendingSet()`/`descendingMap()`에서는 `floor`/`ceiling` 결과가 숫자 감각과 반대로 보일 수 있다
- 객체 comparator가 일부 필드만 보면 navigation도 그 일부 필드 기준으로만 움직인다

## 어떤 문서를 다음에 읽으면 좋은가

- `Comparable`, `Comparator`, natural ordering의 큰 그림이 아직 헷갈리면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- `first`/`last`와 `pollFirst`/`pollLast`의 removal semantics, empty behavior를 한 장으로 고정하고 싶다면 [`pollFirst`/`pollLast` vs `first`/`last` Beginner Bridge](./pollfirst-polllast-vs-first-last-beginner-bridge.md)
- `floorEntry`/`ceilingEntry`와 오른쪽 경계 `ceiling`/`higher`의 `null`을 `null` key/value 정책과 분리해서 붙이고 싶다면 [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)
- `subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap`의 inclusive vs exclusive 경계를 먼저 고정하고 싶다면 [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- `descendingSet()`/`descendingMap()`이 왜 copy가 아니라 view이고, 왜 `floor`/`ceiling` 결과가 뒤집혀 보이는지 짧게 다시 잡고 싶다면 [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
- exact match에서 `lower`와 `floor`만 먼저 굳히고 싶다면 [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)
- `TreeSet`/`TreeMap`에서 comparator가 "같은 자리"까지 정한다는 감각을 이어서 보려면 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- comparator를 직접 넘기지 않은 `TreeSet`/`TreeMap`의 `compareTo()` 기준을 보려면 [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- 워크시트에서 본 이웃 질의를 예약 충돌 검사, gap check, 시간창 조회로 연결하고 싶다면 [TreeMap Interval Entry Primer](../../data-structure/treemap-interval-entry-primer.md)

## 어떤 문서를 다음에 읽으면 좋은가 (계속 2)

- 컬렉션 구현체 선택 감각을 넓히려면 [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)

## 한 줄 정리

`NavigableSet`/`NavigableMap`의 navigation 메서드는 "정렬된 결과에서 가까운 이웃 찾기"이며, 그 이웃의 기준은 항상 현재 컬렉션의 comparator order다.
