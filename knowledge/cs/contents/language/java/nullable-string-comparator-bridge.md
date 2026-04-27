# Nullable String Comparator Bridge

> 한 줄 요약: nullable `String` 정렬은 "문자열 비교"보다 먼저 "`null`을 어디에 둘까?"를 정하고, 그 다음 "대소문자를 구분할까?"를 붙여 읽으면 초보자가 가장 덜 헷갈린다. 그래서 기본 출발점은 `Comparator.comparing(..., Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER))` 같은 형태다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: nullable string comparator bridge basics, nullable string comparator bridge beginner, nullable string comparator bridge intro, java basics, beginner java, 처음 배우는데 nullable string comparator bridge, nullable string comparator bridge 입문, nullable string comparator bridge 기초, what is nullable string comparator bridge, how to nullable string comparator bridge
> 관련 문서:
> - [Language README](../README.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
> - [`equalsIgnoreCase()` vs `CASE_INSENSITIVE_ORDER` Bridge](./equalsignorecase-vs-case-insensitive-order-bridge.md)
> - [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
> - [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
> - [Java String 기초](./java-string-basics.md)
> - [Empty String, Blank, `null`, and Missing Payload Semantics](./empty-string-blank-null-missing-payload-semantics.md)
> - [`Locale.ROOT`, Case Mapping, and Unicode Normalization Pitfalls](./locale-root-case-mapping-unicode-normalization.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)

> retrieval-anchor-keywords: nullable string comparator bridge, java nullable string sorting, java string comparator nullsLast, java string comparator nullsFirst, java case insensitive string comparator java, java String.CASE_INSENSITIVE_ORDER nullsLast, java Comparator.comparing nullable String, java nullable String sort key beginner, java nullable name sort, java nullsLast case insensitive comparator, java null last string sort java, java string reversed nullsLast comparator, java TreeSet case insensitive duplicate, java TreeMap case insensitive overwrite, java nullable string tie breaker comparator, java empty string null string sorting, 자바 nullable string 정렬, 자바 문자열 comparator nullsLast, 자바 대소문자 무시 정렬 comparator

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 비교 표](#한-장-비교-표)
- [가장 자주 쓰는 기본 형태](#가장-자주-쓰는-기본-형태)
- [case-insensitive + `nullsLast` 예제](#case-insensitive--nullslast-예제)
- [내림차순이어도 `null`은 뒤에 두고 싶을 때](#내림차순이어도-null은-뒤에-두고-싶을-때)
- [`TreeSet`/`TreeMap`에서는 `"Mina"`와 `"MINA"`도 같은 자리일 수 있다](#treesettreemap에서는-mina와-mina도-같은-자리일-수-있다)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

문자열 정렬을 막 배우면 보통 이렇게 시작한다.

- 이름순이면 `Comparator.comparing(User::name)`
- 대소문자 무시 정렬이면 `String.CASE_INSENSITIVE_ORDER`

그런데 실제 필드가 `String`이고 값이 비어 있을 수 있으면 질문이 하나 더 생긴다.

- `null`은 맨 앞에 둘까, 맨 뒤에 둘까?
- `"Mina"`와 `"MINA"`는 같은 이름처럼 볼까?
- sorted collection에서는 그 둘을 정말 같은 key처럼 취급해도 될까?

즉 nullable `String` 정렬은 "문자열 비교 API"만 고르는 문제가 아니라,
"`null` 정책 + 대소문자 정책 + 필요하면 tie-breaker"를 같이 적는 문제다.

## 먼저 잡을 mental model

초보자용으로 가장 안전한 한 줄은 이것이다.

> nullable `String`은 `null` 위치를 먼저 정하고, 그 안에서 문자열 비교 방식을 고른다.

예를 들어:

- `String nickname`이 항상 값이 있다 -> `Comparator.comparing(User::nickname)`
- `String nickname`이 `null`일 수 있고 대소문자 무시가 필요하다 -> `Comparator.comparing(User::nickname, Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER))`

읽는 순서도 이렇게 잡으면 쉽다.

1. `nickname`을 꺼낸다.
2. `null`이면 뒤로 보낸다.
3. 값이 있으면 대소문자 무시 순서로 비교한다.

## 한 장 비교 표

| 상황 | 초보자 기본 선택지 | 읽는 법 |
|---|---|---|
| non-null `String name` | `Comparator.comparing(User::name)` | "이름 사전순" |
| nullable `String nickname` | `Comparator.comparing(User::nickname, Comparator.nullsLast(Comparator.naturalOrder()))` | "`null`은 뒤, 값이 있으면 사전순" |
| nullable `String nickname`, 대소문자 무시 | `Comparator.comparing(User::nickname, Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER))` | "`null`은 뒤, 값이 있으면 대소문자 무시 순서" |
| nullable `String nickname`, Z -> A, `null`은 뒤 | `Comparator.comparing(User::nickname, Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER.reversed()))` | "`null`은 뒤, 값이 있으면 대소문자 무시 내림차순" |

핵심은 간단하다.

- `nullsLast(...)`는 `null` 위치 정책이다
- `String.CASE_INSENSITIVE_ORDER`는 값이 있을 때의 비교 정책이다
- 둘을 같이 써야 "nullable + case-insensitive" 의도가 한 번에 보인다

## 가장 자주 쓰는 기본 형태

초보자 기본형은 이 한 줄로 거의 충분하다.

```java
Comparator<User> byNickname =
        Comparator.comparing(
                User::nickname,
                Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER)
        );
```

이 코드는 다음 뜻이다.

- `nickname`이 `null`이면 맨 뒤로 간다
- `nickname`이 있으면 대소문자를 무시하고 비교한다

## case-insensitive + `nullsLast` 예제

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

record User(long id, String nickname) {}

Comparator<User> byNicknameIgnoreCaseNullLast =
        Comparator.comparing(
                User::nickname,
                Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER)
        ).thenComparingLong(User::id);

List<User> users = new ArrayList<>(List.of(
        new User(1L, "Mina"),
        new User(2L, null),
        new User(3L, "ari"),
        new User(4L, "Bora"),
        new User(5L, "mina")
));

users.sort(byNicknameIgnoreCaseNullLast);
```

이 comparator를 초보자용으로 읽으면 다음 순서다.

1. `nickname`이 있는 사람끼리 먼저 비교한다.
2. `"ari"`와 `"Ari"`는 같은 방향으로 본다.
3. `nickname`이 `null`인 사람은 맨 뒤로 보낸다.
4. 대소문자를 무시한 결과가 같으면 `id`로 한 번 더 비교한다.

왜 `thenComparingLong(User::id)`를 붙였을까?

- `"Mina"`와 `"mina"`는 case-insensitive 비교에서는 `0`이 될 수 있다
- `List.sort(...)`만 할 때는 그냥 같은 순위처럼 보여도 괜찮을 수 있다
- 하지만 `TreeSet`/`TreeMap`까지 같은 comparator를 재사용할 생각이면 tie-breaker가 있어야 안전하다

## 내림차순이어도 `null`은 뒤에 두고 싶을 때

여기서 초보자가 많이 헷갈린다.

> `.reversed()`를 맨 끝에 붙이면 지금 만든 comparator 전체가 뒤집힌다.

그래서 이런 코드는 `null`도 앞으로 올 수 있다.

```java
Comparator<User> surprising =
        Comparator.comparing(
                User::nickname,
                Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER)
        ).reversed();
```

`null`은 계속 뒤에 두고, 값만 Z -> A로 바꾸고 싶다면 안쪽 비교만 뒤집는다.

```java
Comparator<User> byNicknameDescNullLast =
        Comparator.comparing(
                User::nickname,
                Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER.reversed())
        ).thenComparingLong(User::id);
```

기억법은 짧다.

- 바깥 `nullsLast(...)`는 `null` 자리
- 안쪽 `CASE_INSENSITIVE_ORDER.reversed()`는 문자열 값 방향

## `TreeSet`/`TreeMap`에서는 `"Mina"`와 `"MINA"`도 같은 자리일 수 있다

`String.CASE_INSENSITIVE_ORDER`는 대소문자를 무시하고 비교한다.
그래서 `"Mina"`와 `"MINA"`는 compare 결과가 `0`이 될 수 있다.

```java
import java.util.Comparator;
import java.util.Set;
import java.util.TreeSet;

record User(long id, String nickname) {}

Comparator<User> byNicknameOnly =
        Comparator.comparing(
                User::nickname,
                Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER)
        );

Set<User> users = new TreeSet<>(byNicknameOnly);
users.add(new User(1L, "Mina"));
users.add(new User(2L, "MINA"));

System.out.println(users.size()); // 1
```

왜 그럴까?

- comparator는 `id`를 안 보고 `nickname`만 본다
- case-insensitive 비교에서는 `"Mina"`와 `"MINA"`가 같은 자리다
- `TreeSet`은 `compare == 0`이면 같은 원소 자리로 볼 수 있다

그래서 sorted collection까지 염두에 두면 tie-breaker를 붙이는 편이 안전하다.

```java
Comparator<User> byNicknameThenId =
        Comparator.comparing(
                User::nickname,
                Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER)
        ).thenComparingLong(User::id);
```

이제 닉네임이 같아 보여도 `id`가 다르면 `compare == 0`으로 바로 끝나지 않는다.

## 초보자가 자주 헷갈리는 지점

- `Comparator.comparing(User::nickname)`만 쓰면 `nickname`이 `null`일 때 정렬 중 `NullPointerException`이 날 수 있다.
- `nullsLast(...)`는 문자열 사전순을 바꾸는 도구가 아니라 `null` 위치를 정하는 도구다.
- `String.CASE_INSENSITIVE_ORDER`는 `null`을 처리하지 않는다. `null` 가능성이 있으면 `nullsFirst(...)`나 `nullsLast(...)`로 감싸야 한다.
- `"Mina"`와 `"MINA"`를 같은 값처럼 보고 싶지 않다면 case-insensitive comparator를 sorted collection key comparator로 그대로 쓰면 안 된다.
- `.reversed()`를 체인 맨 끝에 붙이면 `null` 위치까지 같이 뒤집힐 수 있다.
- `""`와 `null`은 같은 값이 아니다. 빈 문자열 처리 정책이 따로 필요하면 [Empty String, Blank, `null`, and Missing Payload Semantics](./empty-string-blank-null-missing-payload-semantics.md) 쪽이 더 정확한 다음 문서다.
- 영어권 identifier나 간단한 화면 정렬에서는 `String.CASE_INSENSITIVE_ORDER`가 충분할 수 있지만, locale/Unicode 정책까지 필요한 정렬은 더 큰 문제다. 그 부분은 [`Locale.ROOT`, Case Mapping, and Unicode Normalization Pitfalls](./locale-root-case-mapping-unicode-normalization.md)에서 따로 본다.

## 어떤 문서를 다음에 읽으면 좋은가

- `Comparable`과 `Comparator`의 큰 그림을 먼저 묶고 싶다면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- `nullsFirst`, `nullsLast`, `reversed`, `thenComparing` 조립 감각을 넓히고 싶다면 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- nullable 숫자 필드와 nullable 문자열 필드의 차이를 같이 보고 싶다면 [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
- 같은 comparator를 `List.sort(...)`와 stream 정렬에 같이 쓰는 감각을 붙이고 싶다면 [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- `String` 자체의 `equals`, 불변성, 기본 비교 감각을 먼저 다지고 싶다면 [Java String 기초](./java-string-basics.md)
- `TreeSet`/`TreeMap`에서 comparator가 중복 판단과 key overwrite까지 바꾸는 감각을 더 보고 싶다면 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)

## 한 줄 정리

nullable `String` 정렬의 초보자 기본 질문은 "문자열을 어떻게 비교할까?" 하나가 아니라 "`null`을 어디에 둘까, 대소문자를 무시할까, 같은 자리면 tie-breaker가 필요한가?"이며, 그 의도를 `Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER)` 같은 형태로 한 줄에 드러내면 읽기 쉬워진다.
