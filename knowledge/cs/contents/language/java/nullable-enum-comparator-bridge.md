# `null` 가능한 enum, 어떻게 정렬할까 beginner bridge

> 한 줄 요약: nullable `enum` 정렬은 먼저 `null`을 앞/뒤 어디에 둘지 정하고, 그다음 값끼리는 "enum 선언 순서"로 볼지 "`name()` 문자열 순서"로 볼지 나누면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java enum 기초](./java-enum-basics.md)
- [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- [Comparator Null Reversal Primer](./comparator-null-reversal-primer.md)
- [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)
- [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)

retrieval-anchor-keywords: nullable enum comparator, java enum nullslast, java enum nullsfirst, enum declaration order, enum name sort, nullable enum sort beginner, enum comparator 헷갈림, null enum 정렬 왜, comparator enum null, enum natural order, enum name comparator, beginner enum sorting

## 먼저 잡는 멘탈 모델

초보자 기준으로는 nullable `enum` 정렬을 두 질문으로 끊으면 된다.

1. `null`을 앞에 둘까, 뒤에 둘까?
2. 값이 있으면 enum 선언 순서로 볼까, `name()` 문자열 순서로 볼까?

여기서 `Comparator.nullsFirst(...)`와 `Comparator.nullsLast(...)`는 1번 질문에 답한다.
`Comparator.naturalOrder()`는 보통 2번 질문에서 "enum 선언 순서"를 뜻한다.

즉 `DONE`이라는 이름이 알파벳상 앞에 보여도, enum이 `TODO, IN_PROGRESS, DONE` 순서로 선언됐다면 natural order 결과는 선언 순서를 따른다.

## 20초 비교표

| 지금 원하는 정렬 | 첫 코드 형태 | 읽는 법 |
|---|---|---|
| `null`은 뒤, enum 선언 순서 | `Comparator.comparing(Task::status, Comparator.nullsLast(Comparator.naturalOrder()))` | "`null`은 뒤, 값은 enum 선언 순서" |
| `null`은 앞, enum 선언 순서 | `Comparator.comparing(Task::status, Comparator.nullsFirst(Comparator.naturalOrder()))` | "`null`은 앞, 값은 enum 선언 순서" |
| `null`은 뒤, 이름 문자열 순서 | `Comparator.comparing(task -> task.status() == null ? null : task.status().name(), Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER))` | "`null`은 뒤, 값은 `name()` 문자열 순서" |

핵심은 "`null` 정책"과 "값 비교 기준"이 다른 층이라는 점이다.

## 가장 작은 예제

```java
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
        );

List<Task> tasks = List.of(
        new Task(1L, ReviewStatus.DONE),
        new Task(2L, null),
        new Task(3L, ReviewStatus.TODO)
);
```

이 comparator 결과는 `TODO -> DONE -> null`이다. 이유는 간단하다.

- `nullsLast(...)`: `null`을 뒤로 보낸다
- `naturalOrder()`: enum 선언 순서를 따른다
- 그래서 문자열 알파벳순이 아니라 `TODO, IN_PROGRESS, DONE` 순서로 읽는다

## 초보자가 자주 헷갈리는 지점

- "`enum`도 문자열처럼 알파벳순 아닌가요?"
  아니다. `Comparator.naturalOrder()`는 보통 enum 선언 순서다. 알파벳순이 필요하면 `status.name()`을 꺼내서 문자열 comparator로 비교한다.
- "`nullsLast(...).reversed()`면 `null`은 계속 뒤 아닌가요?"
  아니다. comparator 전체를 뒤집으면 `null` 위치도 같이 바뀐다. `null`을 계속 뒤에 두고 값만 내림차순으로 바꾸고 싶으면 안쪽 값 comparator만 `reverseOrder()`로 바꿔야 한다.
- "`TreeSet`이나 `TreeMap`에서도 그냥 보기용 정렬이죠?"
  아니다. sorted collection에서는 `compare(...) == 0`이면 같은 자리로 본다. enum 비교 기준을 너무 거칠게 잡으면 중복 판단까지 영향을 받는다.

## 다음 한 칸

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`nullsLast(...).reversed()`가 왜 이상하게 보여요?" | [Comparator Null Reversal Primer](./comparator-null-reversal-primer.md) |
| "문자열 정렬과 nullable 정렬을 같이 보고 싶어요" | [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md) |
| "sorted set/map에서 comparator가 중복 판단까지 바꾸나요?" | [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md) |
| "enum 자체를 먼저 다시 잡고 싶어요" | [Java enum 기초](./java-enum-basics.md) |

## 한 줄 정리

nullable `enum` 정렬은 `null` 위치 정책과 enum 값 비교 기준을 분리해서 읽고, 기본은 선언 순서인지 문자열 순서인지부터 먼저 확인하면 헷갈림이 크게 줄어든다.
