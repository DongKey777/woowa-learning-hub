# Nullable Wrapper Comparator Bridge

> 한 줄 요약: `Integer`/`Long`/`Double` wrapper 필드는 primitive tie-breaker 습관을 그대로 가져가기보다, "숫자 비교"보다 먼저 "`null`이 올 수 있는가, 오면 앞에 둘까 뒤에 둘까"를 정하게 만든다. 그래서 초보자 기본 선택지는 `comparingInt`/`Long`/`Double`보다 `Comparator.comparing(..., Comparator.nullsFirst(...))` 또는 `Comparator.comparing(..., Comparator.nullsLast(...))` 쪽이 된다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
> - [Comparator Null Reversal Primer](./comparator-null-reversal-primer.md)
> - [TreeMap Null Key vs Nullable Field Primer](./treemap-null-key-vs-nullable-field-primer.md)
> - [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
> - [BinarySearch With Nullable Wrapper Sort Keys](./binarysearch-nullable-wrapper-sort-keys.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./autoboxing-integercache-null-unboxing-pitfalls.md)
> - [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
> - [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./floating-point-precision-nan-infinity-serialization-pitfalls.md)

> retrieval-anchor-keywords: nullable wrapper comparator bridge, java nullable wrapper sorting, java Integer comparator nullsFirst, java Integer comparator nullsLast, java Long comparator nullsFirst, java Long comparator nullsLast, java Double comparator nullsFirst, java Double comparator nullsLast, java wrapper field comparator, java nullable numeric field sorting, java comparing vs comparingInt wrapper, nullable Integer sorting java, nullable Long sorting java, nullable Double sorting java, wrapper null handling comparator, beginner comparator null policy, java nullsLast reversed descending, java descending nullsLast comparator, java wrapper number descending null last, Comparator.nullsLast reverseOrder, reversed changes null placement, nullsLast TreeSet duplicate, nullable comparator TreeSet duplicate, nullable rank TreeSet compare zero, nullable comparator TreeMap overwrite, TreeMap null rank replace value, TreeSet TreeMap null tie breaker, nullable comparator list sort treeset treemap bridge, same comparator list sort treeset difference, null rank tree map overwrite beginner, nullsLast sorted collection duplicate surprise, java primitive tie breaker vs nullable wrapper, java thenComparingInt vs nullsLast, java nullable wrapper tie breaker, java Integer Long Double nullable follow up comparator

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [primitive tie-breaker에서 nullable wrapper follow-up로 넘어가기](#primitive-tie-breaker에서-nullable-wrapper-follow-up로-넘어가기)
- [한 장 비교 표](#한-장-비교-표)
- [`Integer`, `Long`, `Double` 예제](#integer-long-double-예제)
- [내림차순인데 `null`은 뒤에 두고 싶을 때](#내림차순인데-null은-뒤에-두고-싶을-때)
- [`TreeSet`/`TreeMap`에서는 `null`끼리도 같은 자리일 수 있다](#treesettreemap에서는-null끼리도-같은-자리일-수-있다)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Comparator를 막 배우면 보통 이런 식으로 기억한다.

- 숫자면 `comparingInt`, `comparingLong`, `comparingDouble`
- 문자열이면 `comparing`

그런데 필드가 `Integer`, `Long`, `Double` wrapper면 이야기가 조금 달라진다.

- 값이 비어 있을 수 있다
- 비교 중 unboxing이 숨어 들어갈 수 있다
- "빈 값은 앞/뒤 어디로 보낼지"를 먼저 정해야 한다

즉 wrapper 숫자 필드는 "무슨 숫자 타입인가"보다 "`null` 가능성이 있나"가 comparator 선택을 먼저 바꾼다.

## 먼저 잡을 mental model

초보자용으로 가장 안전한 한 줄은 이것이다.

> primitive 필드는 숫자를 바로 비교하고, nullable wrapper 필드는 `null` 위치를 먼저 정한 뒤 숫자 순서를 붙인다.

예를 들어:

- `int grade` -> `Comparator.comparingInt(Student::grade)`
- `Integer rank` with possible `null` -> `Comparator.comparing(Student::rank, Comparator.nullsLast(Comparator.naturalOrder()))`

여기서 중요한 건 "wrapper 타입이냐" 자체보다 "`null`이 실제로 올 수 있느냐"다.

- wrapper지만 생성자/검증에서 항상 non-null이면 일반 `comparing(...)`로 읽어도 된다
- wrapper고 `null`이 올 수 있으면 `nullsFirst`/`nullsLast`를 먼저 떠올리는 편이 안전하다

## primitive tie-breaker에서 nullable wrapper follow-up로 넘어가기

`Comparator Utility Patterns`를 막 읽고 오면 보통 이렇게 손이 먼저 간다.

- primitive follow-up이면 `thenComparingInt`/`thenComparingLong`/`thenComparingDouble`
- 내림차순이면 `reversed()`나 `reverseOrder()`

그 감각 자체는 맞다. 다만 같은 "숫자 필드 follow-up"이라도 필드가 nullable wrapper로 바뀌는 순간 질문 순서가 달라진다.

> primitive tie-breaker는 "어떤 shortcut을 쓸까?"가 먼저고, nullable wrapper follow-up은 "`null`을 앞/뒤 어디에 둘까?"가 먼저다.

| follow-up 필드 | 초보자 기본 선택지 | 읽는 법 |
|---|---|---|
| `int retryCount` | `.thenComparingInt(Job::retryCount)` | "앞 기준이 같으면 int를 바로 비교" |
| `Integer manualRank` | `.thenComparing(Job::manualRank, Comparator.nullsLast(Comparator.naturalOrder()))` | "앞 기준이 같으면 rank 오름차순, 빈 값은 뒤" |
| `Long approvedAtEpoch` | `.thenComparing(Job::approvedAtEpoch, Comparator.nullsFirst(Comparator.naturalOrder()))` | "승인 시각이 없으면 먼저, 값이 있으면 숫자 오름차순" |
| `Double reviewScore` | `.thenComparing(Job::reviewScore, Comparator.nullsLast(Comparator.reverseOrder()))` | "점수 높은 순, 빈 값은 뒤" |

짧게 코드로 같이 보면 차이가 더 또렷하다.

```java
import java.util.Comparator;

record Job(String title, int queue, int retryCount, Integer manualRank, Long approvedAtEpoch, Double reviewScore) {}

Comparator<Job> byQueueThenRetryCount =
        Comparator.comparingInt(Job::queue)
                .thenComparingInt(Job::retryCount);

Comparator<Job> byQueueThenManualRank =
        Comparator.comparingInt(Job::queue)
                .thenComparing(
                        Job::manualRank,
                        Comparator.nullsLast(Comparator.naturalOrder())
                );

Comparator<Job> byQueueThenApprovedAt =
        Comparator.comparingInt(Job::queue)
                .thenComparing(
                        Job::approvedAtEpoch,
                        Comparator.nullsFirst(Comparator.naturalOrder())
                );

Comparator<Job> byQueueThenReviewScore =
        Comparator.comparingInt(Job::queue)
                .thenComparing(
                        Job::reviewScore,
                        Comparator.nullsLast(Comparator.reverseOrder())
                );
```

이 네 줄을 초보자 감각으로 묶으면 다음처럼 기억하면 된다.

- primitive tie-breaker는 `thenComparingInt`/`Long`/`Double` shortcut으로 바로 이어 간다
- `Integer`/`Long`/`Double`이지만 `null`이 올 수 있으면 method 이름보다 `nullsFirst`/`nullsLast`가 먼저 눈에 들어와야 한다
- 내림차순 nullable wrapper는 `.reversed()`를 체인 끝에 붙이는 대신 `Comparator.reverseOrder()`를 `nullsLast(...)` 안에 넣는 편이 의도가 덜 흔들린다
- 왜 그런지 scope까지 분리해서 보고 싶다면 [Comparator Null Reversal Primer](./comparator-null-reversal-primer.md)를 바로 이어서 읽는 편이 가장 빠르다

## 한 장 비교 표

| 필드 선언 | 먼저 생각할 질문 | 초보자 기본 선택지 | 읽는 법 |
|---|---|---|---|
| `int grade` | `null`이 올 수 없나? | `Comparator.comparingInt(Student::grade)` | "숫자를 바로 비교" |
| `Integer rank` | 미정 rank가 `null`인가? | `Comparator.comparing(Student::rank, Comparator.nullsLast(Comparator.naturalOrder()))` | "rank 오름차순, 빈 값은 뒤" |
| `Long lastLoginEpoch` | 로그인 이력 없음이 `null`인가? | `Comparator.comparing(Student::lastLoginEpoch, Comparator.nullsFirst(Comparator.naturalOrder()))` | "빈 값 먼저, 값이 있으면 숫자 오름차순" |
| `Double score` | 점수 미계산을 `null`로 두나? | `Comparator.comparing(Student::score, Comparator.nullsLast(Comparator.reverseOrder()))` | "점수 높은 순, 빈 값은 뒤" |

핵심은 간단하다.

- primitive면 `comparingInt`/`Long`/`Double`이 자연스럽다
- nullable wrapper면 `comparing(...)` 안에서 `null` 정책을 같이 적는 편이 자연스럽다

## `Integer`, `Long`, `Double` 예제

```java
import java.util.Comparator;

record Candidate(String name, Integer rank, Long lastLoginEpoch, Double score) {}

Comparator<Candidate> byRank =
        Comparator.comparing(
                Candidate::rank,
                Comparator.nullsLast(Comparator.naturalOrder())
        ).thenComparing(Candidate::name);

Comparator<Candidate> byLastLogin =
        Comparator.comparing(
                Candidate::lastLoginEpoch,
                Comparator.nullsFirst(Comparator.naturalOrder())
        ).thenComparing(Candidate::name);

Comparator<Candidate> byScoreHighFirst =
        Comparator.comparing(
                Candidate::score,
                Comparator.nullsLast(Comparator.reverseOrder())
        ).thenComparing(Candidate::name);
```

초보자용으로 읽으면 각각 이런 뜻이다.

- `byRank`: rank 작은 값이 먼저 오고, rank가 없으면 맨 뒤로 간다
- `byLastLogin`: 로그인 기록이 없는 사람(`null`)을 먼저 보고, 값이 있으면 숫자 순으로 정렬한다
- `byScoreHighFirst`: 점수는 높은 순으로 보고, 아직 점수가 없는 사람은 맨 뒤로 보낸다

이 문서의 핵심은 세 comparator가 모두 `Integer`/`Long`/`Double`이라는 wrapper 숫자를 다루지만, 실제 선택 기준은 "숫자 종류"보다 "`null` 정책"이라는 점이다.

## 내림차순인데 `null`은 뒤에 두고 싶을 때

먼저 이렇게 생각하면 쉽다.

> `.reversed()`는 "숫자 값만 뒤집기"가 아니라 지금 만든 comparator 전체를 뒤집는다.

그래서 `nullsLast(naturalOrder())`까지 만든 뒤 맨 끝에 `.reversed()`를 붙이면 `null` 위치도 같이 뒤집힌다.

```java
Comparator<Candidate> surprising =
        Comparator.comparing(
                Candidate::score,
                Comparator.nullsLast(Comparator.naturalOrder())
        ).reversed();
```

읽는 순서는 다음처럼 바뀐다.

| comparator | 값의 순서 | `null` 위치 | 초보자용 해석 |
|---|---|---|---|
| `nullsLast(naturalOrder())` | 낮은 점수 -> 높은 점수 | 뒤 | "오름차순, 빈 값 뒤" |
| `nullsLast(naturalOrder()).reversed()` | 높은 점수 -> 낮은 점수 | 앞 | "전체를 뒤집어서 빈 값도 앞으로 옴" |
| `nullsLast(reverseOrder())` | 높은 점수 -> 낮은 점수 | 뒤 | "값만 내림차순, 빈 값은 계속 뒤" |

내림차순 wrapper 숫자 정렬에서 `null`을 계속 뒤에 두고 싶다면, `nullsLast`는 그대로 두고 그 안의 값 비교만 `reverseOrder()`로 바꾼다.

```java
Comparator<Candidate> byScoreHighFirstNullLast =
        Comparator.comparing(
                Candidate::score,
                Comparator.nullsLast(Comparator.reverseOrder())
        ).thenComparing(Candidate::name);
```

이 코드는 다음 의도를 그대로 말한다.

1. `score`가 있으면 높은 점수가 먼저 온다.
2. `score`가 `null`이면 맨 뒤로 간다.
3. 점수가 같으면 이름순으로 한 번 더 정렬한다.

실전에서 헷갈릴 때는 "`null` 위치 정책은 바깥에 두고, 값의 오름/내림만 안쪽 comparator에서 고른다"로 기억하면 된다.

## `TreeSet`/`TreeMap`에서는 `null`끼리도 같은 자리일 수 있다

`nullsLast`는 처음에는 "`null`을 어디에 둘까?"처럼 보인다.
하지만 같은 comparator를 `TreeSet`이나 `TreeMap`에 넣으면 한 가지 의미가 더 생긴다.

> `TreeSet`/`TreeMap`에서는 comparator가 `0`을 돌려주는 두 값이 같은 자리로 취급될 수 있다.

먼저 같은 nullable comparator를 세 군데에 그대로 붙여 보면 감각이 빠르게 잡힌다.

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;

record Candidate(long id, String name, Integer rank) {}

Comparator<Candidate> byRankOnly =
        Comparator.comparing(
                Candidate::rank,
                Comparator.nullsLast(Comparator.naturalOrder())
        );

List<Candidate> queue = new ArrayList<>(List.of(
        new Candidate(1L, "Mina", null),
        new Candidate(2L, "Joon", null)
));
queue.sort(byRankOnly);

System.out.println(queue.size()); // 2

Set<Candidate> waiting = new TreeSet<>(byRankOnly);
waiting.addAll(queue);

System.out.println(waiting.size()); // 1

Map<Candidate, String> memoByCandidate = new TreeMap<>(byRankOnly);
memoByCandidate.put(queue.get(0), "first memo");
memoByCandidate.put(queue.get(1), "second memo");

System.out.println(memoByCandidate.size()); // 1
System.out.println(memoByCandidate.get(new Candidate(99L, "Ghost", null))); // second memo
```

같은 comparator인데 결과가 이렇게 갈린다.

| 위치 | 결과 | 초보자용 해석 |
|---|---|---|
| `List.sort(byRankOnly)` | 두 후보가 둘 다 남는다 | 정렬만 했지, 중복 제거는 하지 않는다 |
| `new TreeSet<>(byRankOnly)` | 크기가 `1`이 될 수 있다 | `compare == 0`이면 같은 원소 자리로 본다 |
| `new TreeMap<>(byRankOnly)` | 크기가 `1`이고 값이 `"second memo"`로 바뀐다 | `compare == 0`이면 같은 key 자리로 보고 나중 `put`이 덮어쓴다 |

왜 이런 일이 생길까?

| 상황 | `byRankOnly`가 보는 값 | comparator 결과 | `TreeSet`/`TreeMap` 해석 |
|---|---|---|---|
| Mina와 Joon 비교 | `null` vs `null` | `compare == 0` | 같은 자리 |

두 후보는 `id`와 `name`이 다르다.
하지만 comparator는 `rank`만 꺼내 보고, 둘 다 `null`이면 `nullsLast(...)` 안에서 같은 값처럼 비교된다.

- `TreeSet`은 둘을 같은 원소 자리로 보고 하나만 남길 수 있다
- `TreeMap`은 둘을 같은 key 자리로 보고 나중 `put`의 값으로 덮어쓸 수 있다
- `List.sort(...)`라면 둘 다 리스트에 남지만, sorted collection에서는 `compare == 0`의 의미가 더 강해진다
- `memoByCandidate.get(new Candidate(99L, "Ghost", null))`가 `"second memo"`를 돌려주는 것도 같은 이유다. `TreeMap`은 이름이나 `id`보다 comparator가 보는 `rank`의 `null` 여부를 먼저 본다.

서로 다른 후보를 모두 보관해야 한다면 `null` 정책 뒤에 tie-breaker를 붙인다.

```java
Comparator<Candidate> byRankThenId =
        Comparator.comparing(
                Candidate::rank,
                Comparator.nullsLast(Comparator.naturalOrder())
        ).thenComparingLong(Candidate::id);
```

이제 `rank`가 둘 다 `null`이어도 `id`가 다르면 `compare == 0`으로 끝나지 않는다.
초보자용 결론은 간단하다.

> nullable field comparator를 `TreeSet`/`TreeMap`에 넣을 때는 "`null`을 앞/뒤 어디에 둘까?" 다음에 "같은 `null`끼리는 정말 같은 원소/key인가?"까지 물어본다.

## 초보자가 자주 헷갈리는 지점

- `Integer rank`가 nullable인데 `Comparator.comparingInt(Candidate::rank)`를 쓰면 비교 중 unboxing 때문에 `NullPointerException`이 날 수 있다.
- `nullsFirst`와 `nullsLast`는 "객체 전체"가 아니라 꺼낸 필드 값의 `null` 위치를 정하는 도구라고 보면 읽기 쉽다.
- `thenComparingInt(...)`를 쓰던 자리에 필드가 `Integer`/`Long`/`Double` nullable wrapper로 바뀌면, shortcut 이름만 바꾸는 게 아니라 `nullsFirst`/`nullsLast` 정책까지 같이 적어야 한다.
- 내림차순이면서 `null`을 뒤에 두고 싶다면 `.reversed()`를 맨 끝에 붙이기보다 `Comparator.nullsLast(Comparator.reverseOrder())`를 field comparator 안에 넣는 편이 의도가 잘 보인다.
- `.reversed()`를 comparator chain 맨 끝에 붙이면 tie-breaker까지 같이 뒤집힐 수 있다. 특정 필드만 내림차순이어야 하면 그 필드 comparator 안에서 방향을 정한다.
- `TreeSet`/`TreeMap`에서는 같은 `null`끼리 `compare == 0`이 되면 서로 다른 객체도 같은 원소/key 자리처럼 보일 수 있다.
- wrapper라고 해서 무조건 `null`을 허용해야 하는 것은 아니다. 하지만 초보자 첫 질문은 "`null`이 진짜 올 수 있나?"여야 한다.
- `Double`에서 `null` 처리와 부동소수점 정밀도/`NaN` 문제는 다른 축이다. `nullsLast`가 그 문제까지 해결해 주지는 않는다.

## 어떤 문서를 다음에 읽으면 좋은가

- `Comparable`과 `Comparator`의 큰 그림을 먼저 다시 묶고 싶다면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- `comparingInt`/`Long`/`Double`, `thenComparing`, `reversed`, `nullsLast`를 더 넓게 손에 익히려면 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- 같은 comparator를 `List.sort(...)`와 stream 정렬에 재사용하는 감각부터 따로 분리해 보고 싶다면 [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- 같은 nullable wrapper comparator를 `Arrays.sort(...)`와 `Arrays.binarySearch(...)`에 함께 재사용하는 감각을 붙이고 싶다면 [BinarySearch With Nullable Wrapper Sort Keys](./binarysearch-nullable-wrapper-sort-keys.md)
- 같은 comparator가 `TreeSet`/`TreeMap`에서 중복 제거와 값 덮어쓰기로 이어지는 감각을 더 보려면 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- `HashSet`과 `TreeSet`의 중복 판단 기준 차이를 먼저 분리해서 보고 싶다면 [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- wrapper unboxing이 왜 comparator에서도 조용히 문제를 만들 수 있는지 보려면 [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./autoboxing-integercache-null-unboxing-pitfalls.md)
- wrapper 선택 자체가 payload 의미와 어떻게 연결되는지 보려면 [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
- `Double` 값 정렬에서 `NaN`, `Infinity`, 반올림 오해까지 같이 보고 싶다면 [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./floating-point-precision-nan-infinity-serialization-pitfalls.md)

## 한 줄 정리

`Integer`/`Long`/`Double` wrapper 필드를 정렬할 때 초보자 핵심 질문은 "어떤 숫자 helper를 쓸까?"가 아니라 "`null`이 올 수 있나, 오면 앞에 둘까 뒤에 둘까?"이며, 같은 comparator를 `TreeSet`/`TreeMap`에 넣는다면 같은 `null`끼리 정말 같은 원소/key인지까지 tie-breaker로 확인해야 한다.
