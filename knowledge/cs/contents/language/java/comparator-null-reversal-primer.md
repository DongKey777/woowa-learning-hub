---
schema_version: 3
title: Comparator Null Reversal Primer
concept_id: language/comparator-null-reversal-primer
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- comparator-null
- reversed-scope
- nullable-sort
aliases:
- Comparator null reversal primer
- nullsLast reversed 차이
- nullsFirst reversed 차이
- reverseOrder vs reversed null
- comparator null position
- nullable comparator descending null last
- 자바 comparator null 위치 뒤집힘
symptoms:
- Comparator.nullsLast(naturalOrder()).reversed()가 null 자리까지 앞으로 뒤집는다는 점을 예상하지 못해
- 값만 내림차순으로 만들고 null 위치는 유지하려면 nullsLast(reverseOrder())처럼 안쪽 value comparator를 뒤집어야 한다는 경계를 놓쳐
- null policy와 non-null value order를 하나의 comparator 방향으로 섞어 읽어 정렬 결과가 반대로 나온다
intents:
- troubleshooting
- definition
- comparison
prerequisites:
- language/java-comparable-comparator-basics
- language/comparator-reversed-scope-primer
next_docs:
- language/nullable-wrapper-comparator-bridge
- language/nullable-string-comparator-bridge
- language/binarysearch-nullable-wrapper-sort-keys
linked_paths:
- contents/language/java/java-comparable-comparator-basics.md
- contents/language/java/java-comparator-utility-patterns.md
- contents/language/java/comparator-reversed-scope-primer.md
- contents/language/java/nullable-wrapper-comparator-bridge.md
- contents/language/java/nullable-string-comparator-bridge.md
- contents/language/java/binarysearch-nullable-wrapper-sort-keys.md
confusable_with:
- language/comparator-reversed-scope-primer
- language/nullable-wrapper-comparator-bridge
- language/binarysearch-nullable-wrapper-sort-keys
forbidden_neighbors: []
expected_queries:
- Comparator.nullsLast(naturalOrder()).reversed()와 nullsLast(reverseOrder()) 차이를 설명해줘
- Java comparator에서 null 위치는 뒤로 유지하고 값만 내림차순으로 정렬하려면 어떻게 해?
- reversed가 comparator 전체를 뒤집으면 nullsFirst nullsLast 정책도 바뀌는 이유가 뭐야?
- null policy와 value order를 comparator에서 어떻게 분리해서 읽어야 해?
- nullable comparator에서 null이 왜 앞으로 오는지 초보자 예제로 알려줘
contextual_chunk_prefix: |
  이 문서는 Java Comparator nullsFirst/nullsLast와 reversed/reverseOrder 차이를 outer null policy와 inner value order로 설명하는 beginner primer다.
  nullsLast reversed, null position, reverseOrder, nullable comparator, descending null last 질문이 본 문서에 매핑된다.
---
# Comparator Null Reversal Primer

> 한 줄 요약: `nullsFirst(...)`와 `nullsLast(...)`는 "값 비교기" 바깥에 있는 `null` 자리 규칙이다. 그래서 comparator 전체를 `reversed()` 하면 `null` 자리도 같이 바뀌고, 안쪽 값 비교기만 `reverseOrder()`나 `.reversed()`로 바꾸면 `null` 자리는 그대로 남는다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: comparator null reversal primer, nullslast reversed 차이, nullsfirst reversed 차이, reverseorder vs reversed null 차이, comparator null 위치 왜 바뀌어요, null 값은 뒤인데 내림차순 하고 싶어요, null 먼저 뒤로 comparator, nullable comparator 큰 그림, comparator outer null policy inner value order, 자바 nullslast reversed 차이, 자바 reverseorder nullslast 차이, 자바 comparator null 위치 뒤집힘, 처음 배우는데 comparator null 처리, nullable 정렬 기초, java comparator null beginner
> 관련 문서:
> - [Language README](../README.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
> - [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
> - [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
> - [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)
> - [BinarySearch With Nullable Wrapper Sort Keys](./binarysearch-nullable-wrapper-sort-keys.md)

> retrieval-anchor-keywords: comparator null reversal primer, java nullsfirst reversed, java nullslast reversed, java reverse comparator null placement, java reverse whole comparator nullslast, java reverse only value comparator nullslast, java comparator.nullslast reversed beginner, java comparator.nullsfirst reversed beginner, java nullslast reverseorder difference, java nullsfirst reverseorder difference, java nullable comparator descending null last, java nullable comparator descending null first, java reversed changes null position, java reverseorder keeps null position, java comparator outer null policy inner value order, java null handling comparator primer, java beginner comparator null reversal, null이 왜 앞으로 와요, null 위치는 유지하고 값만 내림차순, null policy와 value order 차이, 자바 nullslast reversed 차이, 자바 reverseorder nullslast 차이, 자바 comparator null 위치 뒤집힘

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 비교 표](#한-장-비교-표)
- [가장 작은 예제로 보기](#가장-작은-예제로-보기)
- [`nullsLast`에서 왜 결과가 달라질까](#nullslast에서-왜-결과가-달라질까)
- [`nullsFirst`도 같은 방식으로 읽는다](#nullsfirst도-같은-방식으로-읽는다)
- [필드 comparator에 끼워 넣어 읽기](#필드-comparator에-끼워-넣어-읽기)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

초보자가 `nullsFirst`, `nullsLast`, `reversed`, `reverseOrder`를 한 번에 만나면 보통 여기서 헷갈린다.

- `nullsLast(naturalOrder()).reversed()`와 `nullsLast(reverseOrder())`는 둘 다 내림차순 아닌가?
- 왜 하나는 `null`이 앞으로 오고, 다른 하나는 계속 뒤에 남을까?
- `.reversed()`는 값 방향만 바꾸는 게 아닌가?

핵심은 comparator가 두 층으로 되어 있다는 점이다.

1. 바깥 층: `null`을 앞에 둘지 뒤에 둘지
2. 안쪽 층: non-null 값끼리를 오름차순/내림차순으로 비교할지

이 두 층을 따로 읽으면 차이가 단순해진다.

## 먼저 잡을 mental model

초보자용으로 가장 안전한 한 줄은 이것이다.

> `nullsFirst`/`nullsLast`는 바깥 `null` 정책이고, `naturalOrder`/`reverseOrder`는 안쪽 값 순서다.

그래서:

- comparator 전체에 `.reversed()`를 붙이면 바깥 정책과 안쪽 순서가 같이 뒤집힌다
- `nullsLast(...)` 안의 값 comparator만 `reverseOrder()`로 바꾸면, 안쪽 값 순서만 바뀌고 바깥 `null` 정책은 그대로다

짧게 외우면 이렇게 된다.

- 전체 뒤집기: `null` 자리도 바뀜
- 값 비교만 뒤집기: `null` 자리는 유지됨

## 한 장 비교 표

| 코드 | non-null 값 순서 | `null` 위치 | 초보자용 해석 |
|---|---|---|---|
| `Comparator.nullsLast(Comparator.naturalOrder())` | 작은 값 -> 큰 값 | 뒤 | "오름차순, `null`은 뒤" |
| `Comparator.nullsLast(Comparator.naturalOrder()).reversed()` | 큰 값 -> 작은 값 | 앞 | "전체를 뒤집어서 `null`도 앞으로 옴" |
| `Comparator.nullsLast(Comparator.reverseOrder())` | 큰 값 -> 작은 값 | 뒤 | "값만 내림차순, `null`은 계속 뒤" |
| `Comparator.nullsFirst(Comparator.naturalOrder())` | 작은 값 -> 큰 값 | 앞 | "오름차순, `null`은 앞" |
| `Comparator.nullsFirst(Comparator.naturalOrder()).reversed()` | 큰 값 -> 작은 값 | 뒤 | "전체를 뒤집어서 `null`도 뒤로 감" |
| `Comparator.nullsFirst(Comparator.reverseOrder())` | 큰 값 -> 작은 값 | 앞 | "값만 내림차순, `null`은 계속 앞" |

## 가장 작은 예제로 보기

```java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

List<Integer> values = new ArrayList<>(Arrays.asList(3, null, 1, 2, null));

Comparator<Integer> ascNullLast =
        Comparator.nullsLast(Comparator.<Integer>naturalOrder());

Comparator<Integer> wholeReversed =
        Comparator.<Integer>nullsLast(Comparator.<Integer>naturalOrder())
                .reversed();

Comparator<Integer> valueOnlyReversed =
        Comparator.nullsLast(Comparator.<Integer>reverseOrder());

List<Integer> a = new ArrayList<>(values);
a.sort(ascNullLast);
System.out.println(a); // [1, 2, 3, null, null]

List<Integer> b = new ArrayList<>(values);
b.sort(wholeReversed);
System.out.println(b); // [null, null, 3, 2, 1]

List<Integer> c = new ArrayList<>(values);
c.sort(valueOnlyReversed);
System.out.println(c); // [3, 2, 1, null, null]
```

초보자 기준에서는 결과 세 줄만 정확히 읽어도 충분하다.

- `ascNullLast`: 오름차순, `null` 뒤
- `wholeReversed`: 전체 뒤집기라서 내림차순이 되면서 `null`도 앞으로 옴
- `valueOnlyReversed`: 값만 내림차순으로 바뀌고 `null`은 계속 뒤

## `nullsLast`에서 왜 결과가 달라질까

`nullsLast(...)`를 껍질이라고 생각하면 쉽다.

```java
Comparator<Integer> base =
        Comparator.nullsLast(Comparator.<Integer>naturalOrder());
```

이 코드는 다음 두 규칙을 이미 함께 가진다.

1. `null`은 뒤로 보낸다.
2. 값이 있으면 오름차순으로 비교한다.

여기서 맨 끝에 `.reversed()`를 붙이면:

```java
Comparator<Integer> wholeReversed =
        Comparator.<Integer>nullsLast(Comparator.<Integer>naturalOrder())
                .reversed();
```

뒤집히는 대상은 `naturalOrder()` 하나가 아니라, 이미 조립된 **전체 comparator**다.
그래서 다음 둘이 같이 뒤집힌다.

- 값 오름차순 -> 값 내림차순
- `null` 뒤 -> `null` 앞

반대로 안쪽 값 비교기만 바꾸면:

```java
Comparator<Integer> valueOnlyReversed =
        Comparator.nullsLast(Comparator.<Integer>reverseOrder());
```

바깥 `nullsLast(...)`는 그대로고, 안쪽 값 comparator만 `reverseOrder()`로 바뀐다.
그래서 결과는 이렇게 읽는다.

- 값 오름차순 -> 값 내림차순
- `null` 뒤 -> 그대로 뒤

## `nullsFirst`도 같은 방식으로 읽는다

`nullsFirst(...)`도 원리는 완전히 같다.

| 코드 | 결과 |
|---|---|
| `Comparator.nullsFirst(Comparator.naturalOrder())` | `[null, null, 1, 2, 3]` |
| `Comparator.nullsFirst(Comparator.naturalOrder()).reversed()` | `[3, 2, 1, null, null]` |
| `Comparator.nullsFirst(Comparator.reverseOrder())` | `[null, null, 3, 2, 1]` |

여기서도 읽는 법은 같다.

- 전체를 뒤집으면 `null` 위치도 같이 바뀐다
- 안쪽 값 comparator만 바꾸면 `null` 위치는 유지된다

즉 `nullsFirst`와 `nullsLast`의 차이는 "처음 위치"일 뿐이고, reversal 규칙 자체는 동일하다.

## 필드 comparator에 끼워 넣어 읽기

실전에서는 `Integer`나 `String` 필드 comparator 안에서 이 차이를 만난다.

```java
import java.util.Comparator;

record Candidate(String name, Integer score) {}

Comparator<Candidate> surprising =
        Comparator.comparing(
                Candidate::score,
                Comparator.nullsLast(Comparator.naturalOrder())
        ).reversed();

Comparator<Candidate> intended =
        Comparator.comparing(
                Candidate::score,
                Comparator.nullsLast(Comparator.reverseOrder())
        );
```

두 comparator는 비슷해 보이지만 뜻이 다르다.

| 코드 | `score` 값 순서 | `score == null` 위치 |
|---|---|---|
| `comparing(..., nullsLast(naturalOrder())).reversed()` | 높은 점수 먼저 | 앞 |
| `comparing(..., nullsLast(reverseOrder()))` | 높은 점수 먼저 | 뒤 |

초보자용으로 문장으로 바꾸면:

- 첫 번째는 "점수 내림차순 + `null`도 앞으로"
- 두 번째는 "점수 내림차순 + `null`은 계속 뒤"

내림차순인데 `null`은 계속 뒤에 두고 싶다면, 보통 원하는 것은 두 번째다.

## 초보자 혼동 포인트

- `.reversed()`는 "값 방향만 바꾸는 버튼"이 아니다. 호출 시점까지 만든 comparator 전체를 뒤집는다.
- `nullsLast(...).reversed()`와 `nullsLast(reverseOrder())`는 같은 뜻이 아니다.
- `nullsFirst(...).reversed()`도 마찬가지로 `null`을 뒤로 보낼 수 있다.
- `Comparator.comparing(...).reversed()`는 key comparator뿐 아니라 그 `comparing(...)`이 만든 전체 규칙을 뒤집는다.
- "내림차순 + `null` 뒤"를 원하면 바깥 `nullsLast(...)`는 유지하고 안쪽 값 comparator만 `reverseOrder()`나 `.reversed()`로 바꿔야 한다.
- tie-breaker까지 붙은 긴 comparator chain에서는 [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md) 쪽이 더 직접적인 다음 문서다.

## 어떤 문서를 다음에 읽으면 좋은가

- `Comparator` 전체 조립 감각을 먼저 넓히고 싶다면 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- `reversed()`가 whole-chain에 어떻게 적용되는지 더 직접적으로 보고 싶다면 [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
- nullable 숫자 필드 예제를 더 보고 싶다면 [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
- nullable 문자열에서도 같은 구조가 어떻게 반복되는지 보고 싶다면 [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)
- 정렬에 쓴 같은 comparator를 검색에도 그대로 써야 하는 이유까지 연결하고 싶다면 [BinarySearch With Nullable Wrapper Sort Keys](./binarysearch-nullable-wrapper-sort-keys.md)

## 한 줄 정리

`nullsFirst`/`nullsLast`는 바깥 `null` 정책이고 `naturalOrder`/`reverseOrder`는 안쪽 값 정책이라서, **comparator 전체를 뒤집으면 `null` 자리도 뒤집히고 안쪽 값 comparator만 뒤집으면 `null` 자리는 유지된다.**
