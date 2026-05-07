---
schema_version: 3
title: Nullable Number Mixed Direction Bridge
concept_id: language/nullable-number-mixed-direction-bridge
canonical: true
category: language
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 91
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- comparator
- null-handling
- numeric-sort
aliases:
- Nullable Number Mixed Direction Bridge
- nullable Integer descending nullsLast
- nullable Long reverseOrder nullsFirst
- nullable Double comparator chain
- Comparator nullsLast reverseOrder number
- 자바 nullable 숫자 내림차순 정렬
symptoms:
- nullable 숫자 정렬에서 null 위치와 숫자 오름내림 방향을 한 번에 뒤집어 null이 예상과 반대쪽으로 이동해
- Comparator.reversed를 chain 전체에 적용해 값 방향뿐 아니라 null placement까지 함께 뒤집히는 문제를 놓쳐
- Integer Long Double wrapper 필드를 primitive comparator 습관으로 처리하다가 null unboxing이나 NPE 위험을 만든다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- language/java-comparable-comparator-basics
- language/java-comparator-utility-patterns
- language/nullable-wrapper-comparator-bridge
next_docs:
- language/comparator-reversed-scope-primer
- language/binarysearch-nullable-wrapper-sort-keys
- language/nullable-enum-comparator-bridge
linked_paths:
- contents/language/java/java-comparable-comparator-basics.md
- contents/language/java/java-comparator-utility-patterns.md
- contents/language/java/nullable-wrapper-comparator-bridge.md
- contents/language/java/comparator-reversed-scope-primer.md
- contents/language/java/binarysearch-nullable-wrapper-sort-keys.md
confusable_with:
- language/nullable-wrapper-comparator-bridge
- language/comparator-reversed-scope-primer
- language/nullable-enum-comparator-bridge
forbidden_neighbors: []
expected_queries:
- nullable Integer를 내림차순으로 정렬하되 null은 뒤에 두려면 Comparator를 어떻게 써?
- Comparator.nullsLast(reverseOrder())와 reversed()를 전체에 거는 것의 차이를 설명해줘
- nullable Long이나 Double comparator chain에서 null 위치와 값 방향을 따로 읽는 방법이 뭐야?
- wrapper 숫자 필드를 comparingInt처럼 처리하면 null에서 어떤 문제가 생길 수 있어?
- 숫자는 큰 값 먼저인데 null은 앞으로 보내는 comparator를 beginner 기준으로 보여줘
contextual_chunk_prefix: |
  이 문서는 nullable Integer, Long, Double 정렬에서 null placement와 numeric direction을 분리해 Comparator를 고르는 beginner chooser다.
  nullable number comparator, nullsLast reverseOrder, mixed direction, wrapper numeric sorting 질문이 본 문서에 매핑된다.
---
# Nullable Number Mixed-Direction Bridge

> 한 줄 요약: nullable `Integer`/`Long`/`Double` 정렬에서 가장 쉬운 읽는 법은 "`null` 위치는 바깥 `nullsFirst`/`nullsLast`가 정하고, 오름/내림 방향은 안쪽 숫자 comparator가 정한다"이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: nullable number mixed direction bridge basics, nullable number mixed direction bridge beginner, nullable number mixed direction bridge intro, java basics, beginner java, 처음 배우는데 nullable number mixed direction bridge, nullable number mixed direction bridge 입문, nullable number mixed direction bridge 기초, what is nullable number mixed direction bridge, how to nullable number mixed direction bridge
> 관련 문서:
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
> - [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
> - [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
> - [BinarySearch With Nullable Wrapper Sort Keys](./binarysearch-nullable-wrapper-sort-keys.md)

> retrieval-anchor-keywords: language-java-00091, nullable number mixed direction bridge, java nullable integer descending nullslast, java nullable integer descending nullsfirst, java nullable long descending comparator chain, java nullable double descending comparator chain, java nullsFirst nullsLast reverseOrder wrapper, java mixed direction comparator nullable number, java Integer Long Double comparator chain beginner, java nullsLast reverseOrder thenComparing, java reversed changes null placement, java descending wrapper key null last, java descending wrapper key null first, 자바 nullable 숫자 정렬, 자바 Integer Long Double nullsLast reverseOrder, 자바 comparator 체인 nullsFirst nullsLast 내림차순

## 먼저 잡을 mental model

초보자용으로 가장 안전한 기억법은 두 줄이다.

- `nullsFirst(...)` / `nullsLast(...)`는 "`null`을 앞에 둘까 뒤에 둘까?"를 정한다.
- `naturalOrder()` / `reverseOrder()`는 값이 있을 때 숫자를 오름차순으로 볼까 내림차순으로 볼까를 정한다.

그래서 nullable 숫자 필드에서 "내림차순인데 `null`은 뒤"를 만들고 싶다면 보통 이렇게 읽는다.

```java
Comparator.nullsLast(Comparator.reverseOrder())
```

뜻은 단순하다.

1. 값이 있으면 큰 숫자가 먼저 온다.
2. `null`은 계속 맨 뒤에 둔다.

## 한 장 비교 표

| 원하는 규칙 | comparator 조각 | 초보자용 읽는 법 |
|---|---|---|
| nullable `Integer` 오름차순, `null` 뒤 | `Comparator.nullsLast(Comparator.naturalOrder())` | "작은 수 먼저, 빈 값 뒤" |
| nullable `Integer` 내림차순, `null` 뒤 | `Comparator.nullsLast(Comparator.reverseOrder())` | "큰 수 먼저, 빈 값 뒤" |
| nullable `Long` 내림차순, `null` 앞 | `Comparator.nullsFirst(Comparator.reverseOrder())` | "빈 값 먼저, 값은 큰 수부터" |
| nullable `Double` 오름차순, `null` 앞 | `Comparator.nullsFirst(Comparator.naturalOrder())` | "빈 값 먼저, 값은 작은 수부터" |

핵심은 "`null` 정책"과 "값 방향"을 분리해서 읽는 것이다.

## comparator chain에서 같이 보기

```java
import java.util.Comparator;

record Candidate(String name, Integer rank, Long submittedAtEpoch, Double score) {}

Comparator<Candidate> order =
        Comparator.comparing(
                        Candidate::rank,
                        Comparator.nullsLast(Comparator.reverseOrder())
                )
                .thenComparing(
                        Candidate::submittedAtEpoch,
                        Comparator.nullsFirst(Comparator.naturalOrder())
                )
                .thenComparing(
                        Candidate::score,
                        Comparator.nullsLast(Comparator.reverseOrder())
                )
                .thenComparing(Candidate::name);
```

이 체인은 아래 순서로 읽으면 된다.

1. `rank`가 있으면 높은 rank가 먼저 오고, `rank == null`이면 뒤로 간다.
2. `rank`가 같으면 `submittedAtEpoch == null`인 항목을 먼저 본다.
3. 그것도 같으면 `score`가 높은 항목을 먼저 보고, `score == null`은 뒤로 보낸다.
4. 마지막으로 `name`으로 tie-breaker를 건다.

즉 comparator chain이 길어져도 각 줄마다 "바깥은 `null` 자리, 안쪽은 숫자 방향"으로 읽으면 덜 헷갈린다.

## 가장 많이 헷갈리는 지점

이 코드는 초보자가 자주 예상과 다르게 읽는다.

```java
Comparator<Candidate> surprising =
        Comparator.comparing(
                Candidate::rank,
                Comparator.nullsLast(Comparator.naturalOrder())
        ).reversed();
```

많이 하는 오해는 이것이다.

- "값만 내림차순이 되겠지"

실제 동작은 더 넓다.

- comparator 전체를 뒤집기 때문에 `null` 위치도 함께 뒤집힐 수 있다
- 결과적으로 `rank == null`이 앞으로 올 수 있다

`null`은 계속 뒤에 두고 값만 내림차순으로 바꾸고 싶다면, 전체 체인을 뒤집지 말고 안쪽 값 comparator만 바꾼다.

```java
Comparator<Candidate> rankDescNullLast =
        Comparator.comparing(
                Candidate::rank,
                Comparator.nullsLast(Comparator.reverseOrder())
        );
```

## 초보자 체크 카드

- nullable `Integer`/`Long`/`Double`이면 `comparingInt`/`Long`/`Double`보다 `Comparator.comparing(..., ...)` 쪽이 먼저 떠오르는지 확인한다.
- "내림차순 + `null` 뒤"는 `nullsLast(reverseOrder())`처럼 안쪽 값 comparator만 뒤집는다.
- `.reversed()`를 체인 맨 끝에 붙이면 tie-breaker와 `null` 위치까지 같이 뒤집힐 수 있다.
- `TreeSet`/`TreeMap`까지 같은 comparator를 재사용할 생각이면 마지막에 안정적인 tie-breaker를 붙인다.

## 한 줄 정리

nullable 숫자 comparator chain은 "바깥 `nullsFirst`/`nullsLast`가 자리, 안쪽 `naturalOrder`/`reverseOrder`가 방향"이라고 읽으면 `Integer`/`Long`/`Double`이 섞여도 초보자가 훨씬 덜 헷갈린다.
