# Nullable Enum Comparator Bridge

> 한 줄 요약: nullable `enum` 정렬은 "`null`을 어디에 둘까?"를 먼저 정하고, 그 다음 "enum 선언 순서로 볼까, 이름 문자열 순서로 볼까?"를 구분해서 읽으면 초보자가 `String` 사전순과 enum 순서를 섞지 않게 된다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
> - [Comparator Null Reversal Primer](./comparator-null-reversal-primer.md)
> - [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)
> - [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
> - [Java enum 기초](./java-enum-basics.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Enum Persistence, JSON, and Unknown Value Evolution](./enum-persistence-json-unknown-value-evolution.md)

> retrieval-anchor-keywords: nullable enum comparator bridge, java nullable enum sorting, java enum comparator nullsLast, java enum comparator nullsFirst, java enum natural order declaration order, java enum compareTo ordinal order beginner, java nullable enum field comparator, java Comparator.comparing enum nullsLast, java enum sort by declaration order, java enum sort by name string, java enum custom rank comparator, java enum business priority order comparator, java enum explicit rank map comparator, java EnumMap custom order comparator, java nullable enum custom priority nullsLast, java nullable enum custom priority nullsFirst, java nullable enum vs nullable string comparator, java lexicographic vs enum declaration order, java status comparator null last, java enum TreeSet duplicate comparator, java enum TreeMap overwrite comparator, java enum null placement comparator, 자바 nullable enum 정렬, 자바 enum comparator nullsLast, 자바 enum 선언 순서 정렬, 자바 enum 업무 우선순위 정렬, 자바 enum custom rank comparator, 자바 enum null 위치 명시

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [`String`과 `enum`을 한 장으로 비교하기](#string과-enum을-한-장으로-비교하기)
- [가장 자주 쓰는 기본 형태](#가장-자주-쓰는-기본-형태)
- [선언 순서 정렬 예제](#선언-순서-정렬-예제)
- [이름 문자열 순서로 보고 싶을 때](#이름-문자열-순서로-보고-싶을-때)
- [업무 우선순위가 선언 순서와 다를 때](#업무-우선순위가-선언-순서와-다를-때)
- [`TreeSet`/`TreeMap`에서는 같은 enum 값이 같은 자리다](#treesettreemap에서는-같은-enum-값이-같은-자리다)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

nullable 필드 comparator를 막 배우면 보통 두 감각이 섞인다.

- 문자열이면 사전순으로 비교한다
- `null`이 올 수 있으면 `nullsFirst(...)`나 `nullsLast(...)`를 붙인다

그런데 필드 타입이 `String`이 아니라 `enum`이면 질문 하나가 더 생긴다.

- 이 enum은 선언 순서로 정렬할까?
- 아니면 이름 문자열을 알파벳순으로 정렬할까?

즉 nullable `enum` 정렬은 "`null` 위치 + enum 값 순서"를 같이 적는 문제다.
여기서 enum 값 순서는 초보자가 문자열 사전순으로 착각하기 쉽다.

## 먼저 잡을 mental model

초보자용으로 가장 안전한 한 줄은 이것이다.

> nullable `enum`은 `null` 위치를 먼저 정하고, non-null 값끼리는 "enum 자체의 순서"로 볼지 "문자열 이름 순서"로 볼지 따로 고른다.

가장 흔한 기본형은 이쪽이다.

- `Comparator.comparing(Task::status, Comparator.nullsLast(Comparator.naturalOrder()))`

이 코드를 읽는 순서는 다음과 같다.

1. `status`를 꺼낸다.
2. `null`이면 뒤로 보낸다.
3. 값이 있으면 enum natural ordering으로 비교한다.

여기서 중요한 점은 이것이다.

> enum natural ordering은 보통 "선언 순서"이지, `String`처럼 사전순 문자열 비교가 아니다.

## `String`과 `enum`을 한 장으로 비교하기

| 필드 | 초보자 기본 선택지 | 값이 있을 때 비교 기준 | 읽는 법 |
|---|---|---|---|
| nullable `String nickname` | `Comparator.comparing(User::nickname, Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER))` | 문자열 사전순, 대소문자 무시 | "`null`은 뒤, 값은 문자열 비교" |
| nullable `ReviewStatus status` | `Comparator.comparing(Task::status, Comparator.nullsLast(Comparator.naturalOrder()))` | enum 선언 순서 | "`null`은 뒤, 값은 enum 순서" |
| nullable `ReviewStatus status`, 이름 알파벳순 | `Comparator.comparing(task -> task.status() == null ? null : task.status().name(), Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER))` | `name()` 문자열 비교 | "`null`은 뒤, 값은 이름 문자열 비교" |

핵심은 간단하다.

- `nullsLast(...)`는 `null` 위치 정책이다
- `String.CASE_INSENSITIVE_ORDER`는 문자열 비교 정책이다
- `Comparator.naturalOrder()`는 enum 자체의 기본 순서다
- 그래서 "`null` 뒤"라는 같은 정책을 써도, `String`과 `enum`은 non-null 값 비교 기준이 다를 수 있다

## 가장 자주 쓰는 기본 형태

업무 코드에서 nullable 상태 필드를 정렬할 때 초보자 기본형은 이 한 줄로 시작하면 된다.

```java
Comparator<Task> byStatus =
        Comparator.comparing(
                Task::status,
                Comparator.nullsLast(Comparator.naturalOrder())
        );
```

이 코드는 다음 뜻이다.

- `status == null`이면 맨 뒤로 간다
- `status`가 있으면 enum 선언 순서대로 비교한다

enum이 선언된 순서가 곧 업무 흐름 순서라면 이 형태가 가장 읽기 쉽다.

## 선언 순서 정렬 예제

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

enum ReviewStatus {
    TODO,
    IN_PROGRESS,
    DONE
}

record Task(long id, ReviewStatus status) {}

Comparator<Task> byStatusNullLast =
        Comparator.comparing(
                Task::status,
                Comparator.nullsLast(Comparator.naturalOrder())
        ).thenComparingLong(Task::id);

List<Task> tasks = new ArrayList<>(List.of(
        new Task(1L, ReviewStatus.DONE),
        new Task(2L, null),
        new Task(3L, ReviewStatus.TODO),
        new Task(4L, ReviewStatus.IN_PROGRESS)
));

tasks.sort(byStatusNullLast);
```

정렬 결과를 초보자 감각으로 읽으면 다음 순서다.

1. `TODO`
2. `IN_PROGRESS`
3. `DONE`
4. `null`

왜 이렇게 될까?

- enum natural ordering은 선언된 순서를 따른다
- 그래서 `TODO`, `IN_PROGRESS`, `DONE` 순서가 비교 기준이 된다
- `nullsLast(...)`가 `null`만 맨 뒤로 보낸다

중요한 포인트는 `DONE`이 문자열로는 `IN_PROGRESS`보다 앞처럼 보여도, 여기서는 문자열 알파벳순이 아니라는 점이다.

## 이름 문자열 순서로 보고 싶을 때

화면 정렬이나 간단한 관리자 목록에서는 enum 선언 순서보다 이름 문자열 순서가 필요할 수 있다.

그럴 때는 enum 자체를 비교하지 말고, 비교 기준을 문자열로 바꿔 읽는다.

```java
Comparator<Task> byStatusNameNullLast =
        Comparator.comparing(
                task -> task.status() == null ? null : task.status().name(),
                Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER)
        ).thenComparingLong(Task::id);
```

이제 읽는 법이 달라진다.

1. `status`가 `null`이면 뒤로 간다.
2. 값이 있으면 `name()` 문자열을 꺼낸다.
3. 문자열 대소문자를 무시하고 알파벳순으로 비교한다.

즉 같은 enum 필드라도 comparator를 무엇에 거느냐에 따라 뜻이 달라진다.

- enum 자체를 비교하면 선언 순서
- `name()` 문자열을 비교하면 문자열 순서

초보자에게는 이 분리가 제일 중요하다.

## 업무 우선순위가 선언 순서와 다를 때

실무에서는 enum 선언 순서와 화면/업무 우선순위가 딱 맞지 않을 때가 있다.

예를 들어 enum은 상태 흐름대로 선언되어 있어도,

```java
enum ReviewStatus {
    TODO,
    IN_PROGRESS,
    BLOCKED,
    DONE
}
```

목록에서는 `BLOCKED`를 가장 먼저 보여 주고 싶을 수 있다.

이때 초보자용 mental model은 이것이다.

> `null` 위치 정책과 business rank 정책을 따로 적는다.

즉 "업무 우선순위 정렬"은 보통 두 단계다.

1. `null`을 앞에 둘지 뒤에 둘지 먼저 정한다.
2. non-null enum 값에는 명시적인 rank를 붙인다.

짧게 쓰면 이런 형태다.

```java
import java.util.Comparator;
import java.util.EnumMap;
import java.util.Map;

enum ReviewStatus {
    TODO,
    IN_PROGRESS,
    BLOCKED,
    DONE
}

record Task(long id, ReviewStatus status) {}

Map<ReviewStatus, Integer> priorityRank = new EnumMap<>(ReviewStatus.class);
priorityRank.put(ReviewStatus.BLOCKED, 0);
priorityRank.put(ReviewStatus.IN_PROGRESS, 1);
priorityRank.put(ReviewStatus.TODO, 2);
priorityRank.put(ReviewStatus.DONE, 3);

Comparator<Task> byBusinessPriorityNullLast =
        Comparator.comparing(
                Task::status,
                Comparator.nullsLast(
                        Comparator.comparingInt(priorityRank::get)
                )
        ).thenComparingLong(Task::id);
```

이 comparator는 이렇게 읽으면 된다.

- `status == null`이면 맨 뒤로 간다.
- 값이 있으면 enum 선언 순서가 아니라 `priorityRank` 숫자로 비교한다.
- rank가 같을 때는 `id`로 tie-breaker를 준다.

정렬 결과를 감각적으로 쓰면 다음과 같다.

1. `BLOCKED`
2. `IN_PROGRESS`
3. `TODO`
4. `DONE`
5. `null`

여기서 중요한 점은 둘이다.

- `nullsLast(...)`가 있으므로 `null` 위치가 코드에 드러난다.
- `priorityRank`가 있으므로 "왜 이 순서인가?"가 선언 순서와 분리되어 읽힌다.

### 왜 `ordinal()`보다 명시적 rank가 더 낫나

초보자는 가끔 `BLOCKED`를 먼저 보내려고 `ordinal()` 계산을 비틀고 싶어질 수 있다.
하지만 business priority는 선언 순서와 다른 별도 규칙이므로, rank를 따로 적는 편이 더 안전하다.

| 방법 | 읽기 쉬운가 | 선언 순서 변경에 대한 의도 표현 |
|---|---|---|
| enum natural order | 쉽다 | "선언 순서가 곧 우선순위"일 때만 잘 맞음 |
| `name()` 문자열 비교 | 쉽다 | 알파벳순이 필요할 때만 맞음 |
| 명시적 rank (`EnumMap`, `switch`) | 가장 분명하다 | "업무 우선순위가 따로 있다"는 의도가 바로 보임 |

초보자 기준에서는 이렇게 고르면 된다.

- 선언 순서가 곧 우선순위면 `Comparator.naturalOrder()`
- 이름 문자열 순서가 필요하면 `name()` 비교
- 업무 우선순위가 따로 있으면 명시적 rank

### `switch`로 rank를 적어도 된다

작은 예제에서는 `EnumMap` 대신 `switch`로 바로 적어도 충분하다.

```java
Comparator<Task> byBusinessPriorityNullFirst =
        Comparator.comparing(
                Task::status,
                Comparator.nullsFirst(
                        Comparator.comparingInt(status -> switch (status) {
                            case BLOCKED -> 0;
                            case IN_PROGRESS -> 1;
                            case TODO -> 2;
                            case DONE -> 3;
                        })
                )
        );
```

읽는 법은 같다.

- 이번에는 `null`이 앞이다.
- non-null 값은 `businessRank(...)` 숫자로 비교한다.

즉 custom rank가 들어와도 여전히 먼저 볼 축은 "`null` 위치", 그 다음 축은 "non-null rank"다.

## `TreeSet`/`TreeMap`에서는 같은 enum 값이 같은 자리다

sorted collection에서는 `compare == 0`이 곧 같은 자리다.

```java
import java.util.Comparator;
import java.util.Set;
import java.util.TreeSet;

enum ReviewStatus {
    TODO,
    IN_PROGRESS,
    DONE
}

record Task(long id, ReviewStatus status) {}

Comparator<Task> byStatusOnly =
        Comparator.comparing(
                Task::status,
                Comparator.nullsLast(Comparator.naturalOrder())
        );

Set<Task> tasks = new TreeSet<>(byStatusOnly);
tasks.add(new Task(1L, ReviewStatus.TODO));
tasks.add(new Task(2L, ReviewStatus.TODO));

System.out.println(tasks.size()); // 1
```

왜 그럴까?

- comparator는 `id`를 안 보고 `status`만 본다
- 두 값 모두 `ReviewStatus.TODO`라서 `compare == 0`이다
- `TreeSet`은 같은 원소 자리라고 본다

그래서 `List.sort(...)`만이 아니라 `TreeSet`/`TreeMap`까지 재사용할 comparator라면 tie-breaker를 붙이는 편이 안전하다.

```java
Comparator<Task> byStatusThenId =
        Comparator.comparing(
                Task::status,
                Comparator.nullsLast(Comparator.naturalOrder())
        ).thenComparingLong(Task::id);
```

## 초보자가 자주 헷갈리는 지점

- `Comparator.comparing(Task::status)`만 쓰면 `status`가 `null`일 때 정렬 중 `NullPointerException`이 날 수 있다.
- `Comparator.nullsLast(Comparator.naturalOrder())`는 enum을 문자열 사전순으로 정렬하는 코드가 아니다. enum 선언 순서를 사용한다.
- `null`을 뒤로 보낸다고 해서 non-null 값 비교 기준까지 바뀌지는 않는다. `null` 위치와 값 순서는 별도 축이다.
- `enum.name()`을 기준으로 정렬하는 것과 enum 자체를 정렬하는 것은 다르다.
- `ordinal()`을 직접 꺼내서 정렬 기준으로 박아 넣기보다, 초보자 단계에서는 enum natural ordering이나 명시적인 rank comparator로 의도를 드러내는 편이 읽기 쉽다.
- `.reversed()`를 comparator 체인 끝에 붙이면 `null` 위치까지 같이 뒤집힐 수 있다. 이 부분은 [Comparator Null Reversal Primer](./comparator-null-reversal-primer.md)에서 따로 보는 편이 빠르다.
- 선언 순서가 업무 우선순위를 제대로 표현하지 못하면 comparator 쪽에서 명시적인 순서를 따로 적어야 한다. 그때도 먼저 "`null`은 어디에 둘까?"를 분리해서 생각하는 편이 안전하다.

## 어떤 문서를 다음에 읽으면 좋은가

- `Comparator`와 natural ordering의 큰 그림을 먼저 묶고 싶다면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- nullable `String`과 enum의 차이를 바로 비교하고 싶다면 [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)
- nullable 숫자 필드에서 같은 패턴이 어떻게 반복되는지 보고 싶다면 [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
- `nullsLast`, `reversed`, `reverseOrder` 범위를 같이 보고 싶다면 [Comparator Null Reversal Primer](./comparator-null-reversal-primer.md)
- enum 자체의 선언 순서, `name()`, `ordinal()` 감각을 먼저 다지고 싶다면 [Java enum 기초](./java-enum-basics.md)
- enum 저장/진화 관점에서 `ordinal()`을 왜 계약으로 쓰기 위험한지 이어서 보고 싶다면 [Enum Persistence, JSON, and Unknown Value Evolution](./enum-persistence-json-unknown-value-evolution.md)
- sorted collection에서 comparator가 중복 판단까지 바꾼다는 점을 더 보고 싶다면 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)

## 한 줄 정리

nullable `enum` comparator의 초보자 기본 질문은 "`null`을 어디에 둘까?"와 "non-null 값은 enum 선언 순서로 볼까, 이름 문자열 순서로 볼까?"이며, 이 둘을 분리해서 읽어야 문자열 사전순과 enum 순서를 헷갈리지 않게 된다.
