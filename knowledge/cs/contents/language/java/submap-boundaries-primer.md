# `subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer

> 한 줄 요약: `TreeSet`/`TreeMap`의 range API는 "정렬된 줄에서 어디부터 어디까지 볼지"를 고르는 창이고, 초급자는 inclusive vs exclusive 경계만 먼저 고정하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Navigable Range API 미니 드릴](./navigable-range-api-mini-drill.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
- [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- [BigDecimal NavigableMap Lookup Bridge: `floorKey`, `ceilingKey`, and Range Lookups](./bigdecimal-navigablemap-lookup-bridge.md)
- [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)

retrieval-anchor-keywords: subset headset tailset beginner, submap headmap tailmap beginner, treeset subset inclusive exclusive, treemap submap inclusive exclusive, submap 경계 뭐예요, submap inclusive exclusive 헷갈려요, headset는 왜 끝값 제외, tailmap은 왜 시작값 포함, 처음 배우는데 submap, 처음 배우는데 range view, treemap 범위 조회 기초, linkedhashmap은 왜 submap 이 없어요, ordered map 범위 자르기 basics, floor ceiling 다음 submap, collections to ordered map bridge

## 먼저 잡을 멘탈 모델

`TreeSet`과 `TreeMap`을 정렬된 숫자 줄이라고 생각하면 쉽다.

> range API는 "전체 줄"을 복사하는 게 아니라, 그중에서 "이 구간만 보는 창"을 여는 것이다.

초급자 기준으로는 이 규칙 하나가 핵심이다.

- `[` 또는 `]` 느낌: 경계를 포함한다
- `(` 또는 `)` 느낌: 경계를 제외한다

즉 `10`부터 `40` 전까지 보면 `[10, 40)`처럼 읽으면 된다.

## 먼저 갈라야 하는 질문: 삽입 순서인가, 정렬 범위인가

range API를 읽기 전에 이것부터 분리하면 beginner 혼동이 크게 줄어든다.

| 지금 필요한 것 | 첫 선택 | 이유 |
|---|---|---|
| "넣은 순서대로 다시 보여 줘" | `LinkedHashMap` | 삽입 순서를 보장한다 |
| "`30` 이하에서 가장 가까운 key를 찾아 줘" | `TreeMap` | `floorKey(30)` 같은 이웃 조회가 된다 |
| "`20` 이상 `40` 미만만 잘라 줘" | `TreeMap` | `subMap(20, 40)` 같은 range view를 만든다 |

짧게 말하면 `LinkedHashMap`의 강점은 **삽입 순서 보장**이고, 이 문서의 `headMap`/`tailMap`/`subMap`은 **정렬된 key 경계 자르기** 쪽이다.

그래서 "`LinkedHashMap`도 순서가 있으니 `subMap` 비슷하게 생각해도 되지 않나?"라고 묻는다면 답은 아니다. 삽입 순서는 비교 가능한 정렬 축이 아니어서, `20`과 `40` 사이를 자르거나 `30` 근처 이웃을 찾는 기준이 되지 못한다.

## 이름부터 10초로 읽기

| 메서드 | 초급자용 질문 | 기본 경계 감각 |
|---|---|---|
| `headSet(x)` / `headMap(x)` | `x` 앞쪽만 볼까? | `x`는 기본 제외 |
| `tailSet(x)` / `tailMap(x)` | `x`부터 뒤쪽만 볼까? | `x`는 기본 포함 |
| `subSet(a, b)` / `subMap(a, b)` | `a`부터 `b` 전까지만 볼까? | 시작 포함, 끝 제외 |

이 세 줄만 먼저 기억해도 절반은 끝난다.

실행 전에 바로 손예측으로 붙이고 싶다면 [Navigable Range API 미니 드릴](./navigable-range-api-mini-drill.md)을 먼저 풀고 돌아와도 된다.

## 기본 규칙 한 장

`SortedSet`/`SortedMap` 쪽 기본 메서드는 다음처럼 읽으면 된다.

| API | 기본 범위 읽기 |
|---|---|
| `headSet(to)` | `(-inf, to)` |
| `tailSet(from)` | `[from, +inf)` |
| `subSet(from, to)` | `[from, to)` |
| `headMap(to)` | `(-inf, to)` |
| `tailMap(from)` | `[from, +inf)` |
| `subMap(from, to)` | `[from, to)` |

초급자용 핵심 문장:

- `head...`는 끝 경계를 기본으로 제외한다
- `tail...`는 시작 경계를 기본으로 포함한다
- `sub...`는 시작 포함, 끝 제외가 기본이다

## `TreeSet` 예제로 바로 보기

정렬된 줄이 이렇게 있다고 하자.

```text
10   20   30   40   50
```

```java
import java.util.List;
import java.util.TreeSet;

TreeSet<Integer> numbers = new TreeSet<>(List.of(10, 20, 30, 40, 50));

System.out.println(numbers.headSet(30));   // [10, 20]
System.out.println(numbers.tailSet(30));   // [30, 40, 50]
System.out.println(numbers.subSet(20, 50)); // [20, 30, 40]
```

| 호출 | 결과 | 경계 읽기 |
|---|---|---|
| `headSet(30)` | `[10, 20]` | `30`보다 앞만, `30`은 제외 |
| `tailSet(30)` | `[30, 40, 50]` | `30`부터 뒤, `30` 포함 |
| `subSet(20, 50)` | `[20, 30, 40]` | `20` 이상, `50` 미만 |

여기서 `subSet(20, 50)`이 `50`을 포함하지 않는다는 점이 가장 흔한 첫 실수다.

## `TreeMap`은 key 범위를 자른다

`TreeMap`에서는 value가 아니라 key 범위를 자른다.

```java
import java.util.TreeMap;

TreeMap<Integer, String> gradeByScore = new TreeMap<>();
gradeByScore.put(10, "D");
gradeByScore.put(20, "C");
gradeByScore.put(30, "B");
gradeByScore.put(40, "A");

System.out.println(gradeByScore.headMap(30));   // {10=D, 20=C}
System.out.println(gradeByScore.tailMap(30));   // {30=B, 40=A}
System.out.println(gradeByScore.subMap(20, 40)); // {20=C, 30=B}
```

읽는 포인트는 하나다.

- `headMap(30)`은 `30`점 value를 보는 게 아니라 `30` **key 이전 구간**을 본다
- `subMap(20, 40)`은 `20 <= key < 40`인 entry만 본다

## inclusive/exclusive를 직접 고르고 싶을 때

`NavigableSet`/`NavigableMap` overload를 쓰면 경계 포함 여부를 직접 적을 수 있다.

| API | 예시 | 읽는 법 |
|---|---|---|
| `subSet(from, fromInclusive, to, toInclusive)` | `subSet(20, true, 40, true)` | `[20, 40]` |
| `headSet(to, inclusive)` | `headSet(30, true)` | `(-inf, 30]` |
| `tailSet(from, inclusive)` | `tailSet(30, false)` | `(30, +inf)` |
| `subMap(from, fromInclusive, to, toInclusive)` | `subMap(20, false, 40, true)` | `(20, 40]` |
| `headMap(to, inclusive)` | `headMap(30, true)` | `(-inf, 30]` |
| `tailMap(from, inclusive)` | `tailMap(30, false)` | `(30, +inf)` |

예제를 한 번만 보면 기억이 빨라진다.

```java
System.out.println(numbers.subSet(20, true, 40, true));  // [20, 30, 40]
System.out.println(numbers.subSet(20, false, 40, false)); // [30]
System.out.println(numbers.headSet(30, true));            // [10, 20, 30]
System.out.println(numbers.tailSet(30, false));           // [40, 50]
```

## inclusive 플래그를 `floor`/`ceiling`으로 연결해 읽기

초급자가 boolean overload에서 가장 많이 멈추는 지점은 "`true`면 포함"을 알아도 왜 그게 range 문제에서 바로 안 읽히는가다.

이때는 inclusive를 따로 외우기보다, 이미 익숙한 `floor`/`ceiling` 감각으로 번역하면 빠르다.

> 경계를 포함한다는 말은 "그 경계값에 exact match가 있을 때 잘라 내지 않고 잡아둔다"는 뜻이다.

즉:

- 오른쪽 끝을 포함한다 = 그 끝값을 `floor`처럼 잡는다
- 오른쪽 끝을 제외한다 = 그 끝값보다 strictly 앞만 남긴다
- 왼쪽 시작을 포함한다 = 그 시작값을 `ceiling`처럼 잡는다
- 왼쪽 시작을 제외한다 = 그 시작값보다 strictly 뒤만 남긴다

짧게 대응시키면 아래 표처럼 읽을 수 있다.

| range API 질문 | inclusive 플래그 | 이웃 질의 감각으로 읽기 |
|---|---|---|
| `headMap(to, ?)` / `headSet(to, ?)` | `true` | "`to`가 있으면 `floor(to)` 자리까지 본다" |
| `headMap(to, ?)` / `headSet(to, ?)` | `false` | "`to`가 있으면 그 바로 앞까지만 본다" |
| `tailMap(from, ?)` / `tailSet(from, ?)` | `true` | "`from`이 있으면 `ceiling(from)` 자리부터 본다" |
| `tailMap(from, ?)` / `tailSet(from, ?)` | `false` | "`from`이 있으면 그 바로 뒤부터 본다" |
| `subMap(from, fromInc, to, toInc)` | `true, false` | 시작은 `ceiling`, 끝은 `lower/floor` 감각으로 읽는 기본형 `[from, to)` |

엄밀히 말해 range API가 실제로 `floor()`/`ceiling()`을 호출하는 것은 아니다.
하지만 초급자에게는 "경계값 exact match를 포함할지 말지"를 같은 감각으로 읽는 브리지로 충분히 유용하다.

## 같은 숫자 줄에서 바로 연결해 보기

정렬된 줄이 다시 이렇게 있다고 하자.

```text
10   20   30   40   50
```

이제 "`30`이 실제로 들어 있는 경우"만 떠올리면 inclusive 플래그가 더 빨리 읽힌다.

| 호출 | 결과 | `floor`/`ceiling` 감각 |
|---|---|---|
| `headSet(30, true)` | `[10, 20, 30]` | `30`이 있으면 `floor(30)` 자리까지 포함 |
| `headSet(30, false)` | `[10, 20]` | `30` exact match는 잘라 내고 바로 앞까지만 |
| `tailSet(30, true)` | `[30, 40, 50]` | `30`이 있으면 `ceiling(30)` 자리부터 포함 |
| `tailSet(30, false)` | `[40, 50]` | `30` exact match는 건너뛰고 바로 뒤부터 |
| `subSet(20, true, 40, false)` | `[20, 30]` | 시작 `20`은 잡고, 끝 `40`은 제외하는 `[20, 40)` |
| `subSet(20, false, 40, true)` | `[30, 40]` | 시작 `20`은 넘기고, 끝 `40`은 잡는 `(20, 40]` |

초급자 기준으로는 이 두 문장만 붙이면 거의 다 풀린다.

- 왼쪽 경계 boolean은 "`from` exact match를 포함할까?"를 정한다
- 오른쪽 경계 boolean은 "`to` exact match를 포함할까?"를 정한다

## follow-up: `descendingSet()` / `descendingMap()`에서는 range를 어떻게 읽나

여기서 한 번 더 자주 막히는 질문이 있다.

> "내림차순 view로 보면 `subSet(40, 20)`처럼 거꾸로 써야 하나?"

초급자 기준으로는 이렇게 기억하면 된다.

- `descendingSet()` / `descendingMap()`도 여전히 **현재 view의 정렬 순서**로 range를 읽는다
- 그래서 descending view에서는 `40 -> 30 -> 20 -> 10`이 "앞에서 뒤" 순서다
- 따라서 descending view에서는 `subSet(40, 20)`이 자연스럽고, 원본 기준 감각으로 `subSet(20, 40)`를 쓰면 보통 거꾸로 읽은 셈이 된다

같은 데이터를 원본과 descending view로 나란히 놓고 보면 빠르다.

| 보고 있는 줄 | `subSet(40, 20)` 읽기 |
|---|---|
| 원본 `10 -> 20 -> 30 -> 40` | 거꾸로 읽은 범위라서 맞지 않는다 |
| descending view `40 -> 30 -> 20 -> 10` | 시작 포함, 끝 제외인 `[40, 20)`처럼 읽는다 |

예제를 보면 더 분명하다.

```java
import java.util.List;
import java.util.NavigableSet;
import java.util.TreeSet;

TreeSet<Integer> numbers = new TreeSet<>(List.of(10, 20, 30, 40, 50));
NavigableSet<Integer> desc = numbers.descendingSet();

System.out.println(desc);                 // [50, 40, 30, 20, 10]
System.out.println(desc.subSet(40, 20)); // [40, 30]
```

`desc.subSet(40, 20)`은 "숫자가 큰 쪽에서 작은 쪽으로 간다"가 아니라, **descending view에서 앞의 경계가 `40`, 뒤의 경계가 `20`**인 범위를 읽는 것이다.

`TreeMap`도 똑같이 key 줄 기준으로 읽는다.

```java
import java.util.NavigableMap;
import java.util.TreeMap;

TreeMap<Integer, String> gradeByScore = new TreeMap<>();
gradeByScore.put(10, "D");
gradeByScore.put(20, "C");
gradeByScore.put(30, "B");
gradeByScore.put(40, "A");

NavigableMap<Integer, String> desc = gradeByScore.descendingMap();

System.out.println(desc.subMap(40, 20)); // {40=A, 30=B}
```

초급자용 핵심은 이 한 줄이다.

## follow-up: `descendingSet()` / `descendingMap()`에서는 range를 어떻게 읽나 (계속 2)

> range API의 `from`/`to`는 "숫자상 작은 값에서 큰 값으로"가 아니라, **지금 보고 있는 정렬 줄에서 앞 경계와 뒤 경계**다.

그래서 descending view follow-up에서는 이렇게 연결하면 안전하다.

- 원본 view: `subSet(20, 40)`은 `[20, 40)`
- descending view: `subSet(40, 20)`이 같은 자리 범위를 반대 방향 줄에서 읽는 감각이다

더 자세한 "왜 `floor`/`ceiling`까지 같이 뒤집혀 보이는가"는 [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)에서 이어서 보면 된다.

## 가장 많이 헷갈리는 조합만 짧게 비교

| 내가 묻는 것 | 맞는 API | 이유 |
|---|---|---|
| `30`보다 작은 것만 | `headSet(30)` / `headMap(30)` | 끝 경계 기본 제외 |
| `30` 이상만 | `tailSet(30)` / `tailMap(30)` | 시작 경계 기본 포함 |
| `20`부터 `40` 전까지만 | `subSet(20, 40)` / `subMap(20, 40)` | 기본이 `[20, 40)` |
| `20`부터 `40`까지 둘 다 포함 | `subSet(20, true, 40, true)` / `subMap(20, true, 40, true)` | boolean overload로 직접 지정 |

## 초보자 혼동 포인트

- `subSet(20, 40)`를 `20`과 `40` 둘 다 포함으로 읽기 쉽다. 기본은 `[20, 40)`다.
- `headSet(30)`을 "`30`까지"라고 읽기 쉽다. 기본은 `30` 제외다.
- `tailSet(30)`을 "`30` 뒤부터"라고 읽고 `30`을 빼기 쉽다. 기본은 `30` 포함이다.
- `LinkedHashMap`도 순서가 있으니 비슷한 range query가 가능하다고 생각하기 쉽다. 하지만 삽입 순서는 정렬 줄이 아니라서 `floorKey`/`subMap` 계열 질문은 `TreeMap` 쪽이다.
- `subMap(20, false, 40, true)` 같은 boolean overload를 보면 순서를 놓치기 쉽다. `fromInclusive`, `toInclusive` 순서라서 "왼쪽부터 하나씩" 읽는 편이 안전하다.
- `headMap(30, true)`를 "오른쪽까지 넓힌다"로 읽기 쉽다. 실제로는 "`30` exact match를 포함하느냐"만 바뀐다.
- `subMap(...)`이 value 범위를 자른다고 생각하기 쉽다. 실제로는 key 범위를 자른다.
- 결과를 새 컬렉션 복사본으로 착각하기 쉽다. 이 API들은 보통 원본 위의 range view로 읽는 편이 안전하다.

## 초급자용 기억 카드

| 이름 | 가장 짧은 기억 문장 |
|---|---|
| `head...` | "앞쪽만, 끝은 기본 제외" |
| `tail...` | "뒤쪽만, 시작은 기본 포함" |
| `sub...` | "시작 포함, 끝 제외" |
| boolean overload | "포함 여부를 내가 직접 적는다" |

## 다음 읽기

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| `floor`/`ceiling`/`lower`/`higher`까지 같이 헷갈린다 | [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md) |
| `BigDecimal` key에서 scale이 다른데 range 결과가 왜 같은지 궁금하다 | [BigDecimal NavigableMap Lookup Bridge: `floorKey`, `ceilingKey`, and Range Lookups](./bigdecimal-navigablemap-lookup-bridge.md) |
| `subMap`을 예약 시간창 조회와 연결해서 보고 싶다 | [TreeMap Interval Entry Primer](../../data-structure/treemap-interval-entry-primer.md) |
| `TreeSet`/`TreeMap`에서 무엇이 같은 자리인지 헷갈린다 | [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md) |
| comparator 없이도 왜 자동 정렬되는지 다시 잡고 싶다 | [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md) |
| 컬렉션 큰 그림부터 다시 보고 싶다 | [Java 컬렉션 프레임워크 입문](./java-collections-basics.md) |

## 한 줄 정리

`subSet`/`subMap` 계열은 "정렬된 줄에서 어느 구간을 볼지" 정하는 API이고, 초급자는 먼저 `head = 끝 제외`, `tail = 시작 포함`, `sub = [from, to)`만 정확히 기억하면 된다.
