---
schema_version: 3
title: Priority Only Range Search Follow Up
concept_id: language/priority-only-range-search-follow-up
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- binary-search
- comparator
- range-search
aliases:
- Priority Only Range Search Follow Up
- priority only range search comparator prefix
- Java primary key block binary search
- comparator prefix range search beginner
- lower bound upper bound primary comparator key
- 자바 priority 범위 검색
symptoms:
- priority title id 전체 comparator로 정렬된 배열에서 priority만 같은 블록을 찾으려다 exact search와 range search를 섞어
- 정렬 prefix가 아닌 title만 comparator로 잘라 range search를 시도해 title 값들이 연속 블록이라는 보장이 없다는 점을 놓쳐
- tie-breaker까지 포함한 probe 하나로 priority 블록 전체를 찾을 수 있다고 생각해 lower/upper boundary 탐색을 빠뜨려
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- language/binarysearch-nullable-wrapper-sort-keys
- language/binarysearch-duplicate-boundary-primer
- language/java-comparator-utility-patterns
next_docs:
- language/record-comparator-60-second-mini-drill
- language/treeset-treemap-comparator-tie-breaker-basics
- language/java-array-sorting-searching-basics
linked_paths:
- contents/language/java/binarysearch-nullable-wrapper-sort-keys.md
- contents/language/java/binarysearch-duplicate-boundary-primer.md
- contents/language/java/java-array-sorting-searching-basics.md
- contents/language/java/java-comparator-utility-patterns.md
- contents/language/java/treeset-treemap-comparator-tie-breaker-basics.md
confusable_with:
- language/binarysearch-duplicate-boundary-primer
- language/java-comparator-utility-patterns
- language/treeset-treemap-comparator-tie-breaker-basics
forbidden_neighbors: []
expected_queries:
- priority title id로 정렬된 배열에서 priority만 같은 전체 range를 어떻게 찾을 수 있어?
- range search에서는 전체 comparator가 아니라 prefix comparator로 boundary를 찾는다는 뜻이 뭐야?
- exact search와 priority-only range search는 comparator 사용이 어떻게 달라?
- 정렬 key의 prefix가 아닌 title만으로 range search하면 왜 안전하지 않아?
- priority block의 lower bound upper bound를 beginner 기준으로 설명해줘
contextual_chunk_prefix: |
  이 문서는 priority -> title -> id comparator로 정렬된 배열에서 priority prefix만 같은 range block을 찾는 방법을 설명하는 beginner primer다.
  priority range search, comparator prefix, lower bound, upper bound, binary search block 질문이 본 문서에 매핑된다.
---
# Priority-Only Range Search Follow-Up

> 한 줄 요약: 배열이 `priority -> title -> id` 같은 전체 comparator로 정렬되어 있어도, `priority`만 묻는 range search는 **prefix comparator**로 시작 경계와 끝 경계를 읽으면 beginner 단계에서 가장 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [BinarySearch With Nullable Wrapper Sort Keys](./binarysearch-nullable-wrapper-sort-keys.md)
- [BinarySearch Duplicate Boundary Primer](./binarysearch-duplicate-boundary-primer.md)
- [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
- [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)

retrieval-anchor-keywords: language-java-00129, priority only range search follow up, java priority only range search comparator tie breaker, java primary key block binary search, java comparator prefix range search beginner, java lower bound upper bound primary comparator key, java priority title id comparator range, java binary search one key with tie breakers, java first last range by primary comparator, java object array primary key range search, java prefix comparator safe range search, java title only comparator unsafe range search, 자바 priority 범위 찾기 tie breaker, 자바 1차 key 범위 검색, priority only range search follow up basics

## 왜 이 follow-up이 필요한가

초보자가 여기서 자주 막힌다.

- 정렬은 `priority -> title -> id`로 했는데 `priority == 2` 전체 구간은 어떻게 찾지?
- probe object 하나를 만들면 `priority == 2`인 아무 원소나 찾을 수 있지 않나?
- `title`도 comparator에 들어가는데 왜 `priority`만 보는 boundary search가 가능하지?

핵심은 간단하다.

- exact search와 range search를 나눠서 생각한다
- exact search는 전체 comparator chain을 따라야 한다
- 하지만 "같은 `priority` 블록 전체"를 찾고 싶다면 `priority`만 보는 **더 거친 prefix comparator**로 경계를 읽을 수 있다

## 먼저 잡을 mental model

정렬 줄을 먼저 이렇게 본다.

```text
priority -> title -> id
```

이 뜻은:

1. 먼저 `priority`끼리 큰 덩어리로 나뉜다
2. 같은 `priority` 안에서 `title`이 다시 줄을 선다
3. 그래도 같으면 `id`가 마지막 tie-breaker가 된다

그래서 `priority == 2`인 원소들은 중간 순서가 어떻든 **한 덩어리 블록**으로 붙어 있다.

```text
[priority 1 block][priority 2 block][priority null block]
```

beginner 단계에서는 이 블록 감각만 먼저 잡으면 된다.

## 한 장 비교 표

| 지금 하고 싶은 일 | 어떤 comparator로 읽나 | 왜 그렇게 읽나 |
|---|---|---|
| 정확히 한 원소 찾기 | `priority -> title -> id` 전체 comparator | tie-breaker까지 같아야 exact match다 |
| `priority == 2` 시작 찾기 | `priority`만 보는 comparator | `priority` 블록의 왼쪽 끝을 찾는 질문이기 때문 |
| `priority == 2` 끝 찾기 | `priority`만 보는 comparator | `priority` 블록의 오른쪽 끝을 찾는 질문이기 때문 |
| `title == "Deploy"` 블록 찾기 | `title`만 보는 comparator는 보통 위험 | 정렬 줄에서 `title`이 연속 블록이라는 보장이 없다 |

짧게 외우면 이렇다.

> range search에서 줄 세우기 축을 줄일 수는 있지만, **앞에서부터 잘라 낸 prefix까지만** 안전하다.

## 예제로 바로 보기

```java
import java.util.Arrays;
import java.util.Comparator;

record Task(long id, String title, Integer priority) {}

Comparator<Task> byPriorityThenTitleThenId =
        Comparator.comparing(
                Task::priority,
                Comparator.nullsLast(Comparator.naturalOrder())
        ).thenComparing(Task::title)
         .thenComparingLong(Task::id);

Comparator<Task> byPriorityOnly =
        Comparator.comparing(
                Task::priority,
                Comparator.nullsLast(Comparator.naturalOrder())
        );

Task[] tasks = {
        new Task(30L, "DB connection", 2),
        new Task(10L, "API docs", null),
        new Task(20L, "Auth bug", 1),
        new Task(40L, "Cache cleanup", 2),
        new Task(50L, "Deploy", 2)
};

Arrays.sort(tasks, byPriorityThenTitleThenId);
```

정렬 뒤 순서는 이렇게 읽힌다.

| index | task |
|---|---|
| `0` | `new Task(20L, "Auth bug", 1)` |
| `1` | `new Task(40L, "Cache cleanup", 2)` |
| `2` | `new Task(30L, "DB connection", 2)` |
| `3` | `new Task(50L, "Deploy", 2)` |
| `4` | `new Task(10L, "API docs", null)` |

여기서 `priority == 2`는 인덱스 `1..3` 블록이다.

## 시작 경계와 끝 경계 읽기

probe object는 `priority`만 맞추면 된다.
이 boundary search에서는 `title`, `id`를 보지 않기 때문이다.

```java
int start = lowerBound(
        tasks,
        new Task(0L, "", 2),
        byPriorityOnly
); // 1

int endExclusive = upperBound(
        tasks,
        new Task(0L, "", 2),
        byPriorityOnly
); // 4

int endInclusive = endExclusive - 1; // 3
```

읽는 법은 단순하다.

- `start == 1` -> `priority == 2` 블록 시작
- `endExclusive == 4` -> 블록 바로 다음 칸
- 그래서 실제 구간은 `[1, 4)` 또는 `1..3`

## 왜 이게 안전할까

정렬 comparator가 `priority -> title -> id`라면:

- 같은 `priority`는 무조건 붙어 있다
- 같은 `priority` 안에서만 `title`, `id`가 순서를 가른다

즉 tie-breaker는 블록 **안쪽 순서**만 바꾸고, `priority` 블록 자체를 찢어 놓지는 않는다.

그래서 `priority`만 보는 comparator는 정렬 규칙의 앞부분(prefix)이라 안전하다.

## 무엇이 unsafe한가

아래처럼 `title`만 보는 comparator로는 보통 같은 title 블록이 연속이라고 보장할 수 없다.

| 정렬 comparator | boundary용 comparator | 안전한가 |
|---|---|---|
| `priority -> title -> id` | `priority` | 안전 |
| `priority -> title -> id` | `priority -> title` | 안전 |
| `priority -> title -> id` | `title` | 보통 unsafe |

예를 들어 정렬된 줄이 아래처럼 될 수 있다.

```text
(1, "Deploy"), (2, "Cache cleanup"), (2, "Deploy"), (null, "API docs")
```

이 줄에서는 `"Deploy"`가 한 덩어리로 붙어 있지 않다.
그래서 `title`만 보는 경계 탐색은 beginner가 기대한 "연속 구간" 질문과 맞지 않는다.

## helper를 같이 보면 더 쉽다

```java
static <T> int lowerBound(T[] array, T target, Comparator<? super T> comparator) {
    int left = 0;
    int right = array.length;

    while (left < right) {
        int mid = left + (right - left) / 2;
        if (comparator.compare(array[mid], target) >= 0) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}

static <T> int upperBound(T[] array, T target, Comparator<? super T> comparator) {
    int left = 0;
    int right = array.length;

    while (left < right) {
        int mid = left + (right - left) / 2;
        if (comparator.compare(array[mid], target) > 0) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}
```

이 helper를 beginner 관점에서 읽으면:

- `lowerBound`는 "`priority >= 2`가 처음 나오는 칸"
- `upperBound`는 "`priority > 2`가 처음 나오는 칸"

그래서 둘 사이가 곧 `priority == 2` 블록이다.

## 초보자가 자주 헷갈리는 지점

- exact search probe와 range search probe를 같은 질문이라고 생각하기 쉽다.
- tie-breaker가 있으면 `priority`만 보는 search는 전부 틀린다고 오해하기 쉽다.
- prefix comparator와 아무 축이나 뽑아 온 comparator를 같은 것으로 생각하기 쉽다.
- `endExclusive`는 마지막 원소 인덱스가 아니라 "바로 다음 칸"이라는 점을 자주 놓친다.

안전한 기억법:

- exact search는 전체 comparator
- range search는 필요한 prefix comparator
- 결과 구간은 보통 `[start, endExclusive)`로 읽는다

## 다음 읽기

- nullable wrapper와 tie-breaker가 같이 들어간 전체 그림부터 다시 보고 싶다면 [BinarySearch With Nullable Wrapper Sort Keys](./binarysearch-nullable-wrapper-sort-keys.md)
- 중복값에서 첫 위치/마지막 위치를 가장 쉬운 방식으로 먼저 잡고 싶다면 [BinarySearch Duplicate Boundary Primer](./binarysearch-duplicate-boundary-primer.md)
- comparator chain 자체를 더 익히고 싶다면 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)

## 한 줄 정리

정렬이 `priority -> title -> id`처럼 더 자세한 comparator로 되어 있어도, `priority` 전체 구간을 찾는 beginner range search는 **앞부분 prefix comparator로 lower/upper boundary를 읽는다**고 기억하면 가장 안전하다.
