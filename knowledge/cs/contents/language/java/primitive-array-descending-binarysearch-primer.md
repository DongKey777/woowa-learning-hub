---
schema_version: 3
title: Primitive Array Descending BinarySearch Primer
concept_id: language/primitive-array-descending-binarysearch-primer
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 91
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- arrays
- binary-search
- primitive
aliases:
- Primitive Array Descending Search Primer
- primitive array descending binarySearch primer
- Java int array descending binarySearch
- Arrays.binarySearch primitive no comparator
- keep primitive array ascending search
- 자바 primitive 배열 내림차순 binarySearch
symptoms:
- int 배열을 내림차순으로 뒤집어 둔 뒤 Arrays.binarySearch를 그대로 호출해 오름차순 전제를 깨뜨려 잘못된 결과를 얻어
- primitive 배열에는 sort와 binarySearch comparator overload가 없다는 점을 모르고 Comparator.reverseOrder를 넘기려 해
- 화면은 내림차순이어야 하지만 검색은 오름차순 저장 배열에서 처리하고 인덱스만 변환하는 안전 패턴을 떠올리지 못해
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- language/java-array-sorting-searching-basics
- language/primitive-descending-array-sort-bridge
- language/primitive-reverse-copy-vs-view-bridge
next_docs:
- language/binarysearch-nullable-wrapper-sort-keys
- language/java-comparator-utility-patterns
- language/descending-view-mental-model
linked_paths:
- contents/language/java/java-array-sorting-searching-basics.md
- contents/language/java/binarysearch-nullable-wrapper-sort-keys.md
- contents/language/java/descending-view-mental-model.md
- contents/language/java/java-comparator-utility-patterns.md
confusable_with:
- language/primitive-descending-array-sort-bridge
- language/primitive-reverse-copy-vs-view-bridge
- language/binarysearch-nullable-wrapper-sort-keys
forbidden_neighbors: []
expected_queries:
- int 배열을 내림차순으로 뒤집은 뒤 Arrays.binarySearch를 쓰면 왜 위험해?
- primitive 배열 binarySearch는 comparator를 못 받으니 오름차순 저장을 유지하는 게 왜 안전해?
- 내림차순 화면 인덱스가 필요할 때 오름차순 검색 결과를 어떻게 변환해?
- Arrays.sort int[]와 Arrays.binarySearch int[]에 Comparator.reverseOrder를 넘길 수 없는 이유가 뭐야?
- primitive 배열 descending search를 wrapper 배열이나 custom search로 바꿔야 하는 경우를 설명해줘
contextual_chunk_prefix: |
  이 문서는 primitive 배열에서 Arrays.binarySearch가 ascending order를 전제하고 comparator overload가 없기 때문에 descending view는 읽기 방향으로 처리하는 beginner primer다.
  primitive array, descending binarySearch, Arrays.binarySearch, int array comparator, ascending search 질문이 본 문서에 매핑된다.
---
# Primitive Array Descending Search Primer

> 한 줄 요약: primitive 배열에서는 `Arrays.sort(array, comparator)`와 `Arrays.binarySearch(array, key, comparator)` overload가 없으므로, **배열 자체는 오름차순으로 유지하고 필요할 때만 내림차순으로 읽는 패턴**이 초보자에게 가장 안전하다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: primitive array descending binarysearch primer basics, primitive array descending binarysearch primer beginner, primitive array descending binarysearch primer intro, java basics, beginner java, 처음 배우는데 primitive array descending binarysearch primer, primitive array descending binarysearch primer 입문, primitive array descending binarysearch primer 기초, what is primitive array descending binarysearch primer, how to primitive array descending binarysearch primer
> 관련 문서:
> - [Language README](../README.md)
> - [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
> - [BinarySearch With Nullable Wrapper Sort Keys](./binarysearch-nullable-wrapper-sort-keys.md)
> - [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
> - [Comparator Utility Patterns](./java-comparator-utility-patterns.md)

> retrieval-anchor-keywords: language-java-00090, primitive array descending binarySearch primer, java primitive descending binary search, java int array descending binarySearch, java long array descending binarySearch, java double array descending binarySearch, java primitive array comparator unavailable, java Arrays.sort primitive no comparator, java Arrays.binarySearch primitive no comparator, java descending view primitive array beginner, java keep primitive array ascending search descending display, java primitive array reverse display search ascending, java descending insertion point primitive array, java int array descending search safe pattern, 자바 primitive 배열 내림차순 binarySearch, 자바 int 배열 comparator 없는 내림차순 검색, 자바 primitive 배열 오름차순 유지 내림차순 보기

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 비교 표](#한-장-비교-표)
- [가장 안전한 기본 패턴: 오름차순 저장, 내림차순 보기](#가장-안전한-기본-패턴-오름차순-저장-내림차순-보기)
- [검색 결과를 내림차순 위치로 바꾸는 법](#검색-결과를-내림차순-위치로-바꾸는-법)
- [정말 내림차순 실배열이 필요할 때](#정말-내림차순-실배열이-필요할-때)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [다음 읽기](#다음-읽기)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

초보자가 primitive 배열을 다루다가 자주 만나는 막힘은 보통 이 흐름이다.

- `int[]`를 내림차순으로 보고 싶다
- 그래서 배열을 뒤집어 놓고 `Arrays.binarySearch(numbers, key)`를 그대로 호출한다
- 그런데 결과가 이상하거나, "왜 comparator를 못 넘기지?"에서 막힌다

핵심 이유는 단순하다.

- primitive 배열은 `Arrays.sort(array, comparator)`가 없다
- primitive 배열은 `Arrays.binarySearch(array, key, comparator)`도 없다
- 즉 primitive 배열 검색은 **natural ascending order** 전제를 기본으로 읽는 편이 가장 안전하다

그래서 beginner-safe 기본 해법은 "내림차순으로 저장하고 검색"이 아니라,
"**오름차순으로 저장하고 검색한 뒤, 필요하면 내림차순 view처럼 읽기**"다.

## 먼저 잡을 mental model

초보자 기준으로는 아래 두 줄이면 충분하다.

- primitive 배열의 `binarySearch`는 **오름차순 정렬된 줄**을 전제로 읽는다
- 내림차순이 화면 요구사항이라면 **배열을 바꾸기보다 읽는 방향을 바꾸는 쪽**이 안전하다

예를 들어 값이 이렇게 있다고 하자.

```text
오름차순 저장: 10   20   30   40
내림차순 보기: 40   30   20   10
```

값 집합은 같지만, 검색을 안전하게 맡길 수 있는 쪽은 첫 번째 줄이다.

즉 이 문서의 기본 태도는 `descendingSet()` 문서와 비슷하다.

- 데이터를 굳이 뒤집어 저장하지 않는다
- 필요할 때 반대 방향으로 읽는다
- 검색은 원래 기준 줄에서 처리한다

## 한 장 비교 표

| 하고 싶은 일 | beginner-safe 패턴 | 피할 패턴 | 이유 |
|---|---|---|---|
| `int[]`를 내림차순으로 보여 주기 | 오름차순 정렬 후 뒤에서부터 읽기 | 뒤집은 배열에 `binarySearch` 그대로 호출 | primitive 검색 overload는 comparator를 못 받는다 |
| 값 존재 여부 찾기 | 오름차순 배열에 `Arrays.binarySearch(numbers, key)` | 내림차순 실배열에 같은 호출 | 검색 전제가 깨진다 |
| 내림차순 화면 인덱스 구하기 | 오름차순 검색 후 인덱스 변환 | 배열 자체를 내림차순으로 유지 | 정렬/검색 일관성이 약해진다 |
| 진짜 custom descending 검색이 필요 | wrapper 배열로 전환하거나 직접 전용 검색 구현 | "reverse 했으니 괜찮겠지" 식 재사용 | 규칙을 코드로 분명히 가져가야 한다 |

짧게 외우면 다음 한 줄이다.

> primitive 배열은 "내림차순 검색 API"가 없으니, 검색은 오름차순 기준으로 고정하고 표현만 뒤집는 쪽이 안전하다.

## 가장 안전한 기본 패턴: 오름차순 저장, 내림차순 보기

가장 단순한 예제부터 보자.

```java
import java.util.Arrays;

int[] scores = {30, 10, 40, 20};
Arrays.sort(scores); // [10, 20, 30, 40]

for (int i = scores.length - 1; i >= 0; i--) {
    System.out.print(scores[i] + " ");
}
// 40 30 20 10

int index = Arrays.binarySearch(scores, 30); // 2
boolean exists = index >= 0;
```

이 패턴의 장점은 명확하다.

- 정렬은 표준 API 전제를 그대로 따른다
- 검색도 표준 API 전제를 그대로 따른다
- 내림차순 출력은 반복 방향만 바꾸면 된다

즉 "데이터 저장 순서"와 "화면에서 읽는 순서"를 분리하면 실수가 크게 줄어든다.

## 검색 결과를 내림차순 위치로 바꾸는 법

검색은 오름차순 배열에서 했지만,
화면은 내림차순 인덱스로 보여 주고 싶을 수 있다.

이때는 인덱스만 바꾸면 된다.

### 찾은 경우

```java
int[] scores = {10, 20, 30, 40}; // ascending
int ascIndex = Arrays.binarySearch(scores, 30); // 2
int descIndex = scores.length - 1 - ascIndex;   // 1
```

내림차순 view `[40, 30, 20, 10]`에서 `30`의 위치는 실제로 `1`이다.

### 못 찾은 경우: 삽입 위치 바꾸기

```java
int[] scores = {10, 20, 30, 40};
int result = Arrays.binarySearch(scores, 25); // -3
int ascInsertionPoint = -result - 1;          // 2
int descInsertionPoint = scores.length - ascInsertionPoint; // 2
```

읽는 법은 이렇다.

- 오름차순 기준으로 `25`는 `20` 뒤, `30` 앞에 들어간다
- 내림차순 view `[40, 30, 20, 10]`에서는 `30` 뒤, `20` 앞에 들어간다
- 그래서 내림차순 삽입 위치도 `2`가 된다

간단 공식만 기억하면 된다.

- 찾은 인덱스: `descIndex = length - 1 - ascIndex`
- 못 찾은 삽입 위치: `descInsertionPoint = length - ascInsertionPoint`

## 정말 내림차순 실배열이 필요할 때

초보자 기준의 기본 답은 여전히 "오름차순 저장"이다.
그래도 아래처럼 진짜 내림차순 실배열이 필요할 수는 있다.

- 외부 API 계약이 내림차순 배열 자체를 요구한다
- primitive 배열을 그대로 넘겨야 해서 wrapper로 바꾸기 싫다
- 검색 규칙을 직접 제어해야 한다

이때 선택지는 두 가지다.

| 선택지 | 언제 쓰나 | 초보자 관점 메모 |
|---|---|---|
| `Integer[]`/`Long[]` 같은 wrapper 배열로 바꾸고 comparator overload 사용 | comparator 기반 정렬/검색 규칙이 중요할 때 | 코드 설명은 쉬워지지만 boxing이 들어간다 |
| primitive 배열용 "내림차순 전용 binary search"를 직접 구현 | 성능/자료형 제약 때문에 primitive를 유지해야 할 때 | beginner 기본 패턴은 아니다 |

중요한 점은 이것이다.

- primitive 배열을 물리적으로 뒤집었다고 해서 `Arrays.binarySearch(array, key)`가 갑자기 "내림차순 검색"을 이해해 주는 것은 아니다
- 내림차순 실배열을 유지한다면 검색 규칙도 그에 맞게 **직접** 가져가야 한다

즉 "배열만 뒤집고 검색 API는 그대로"가 가장 위험한 중간 상태다.

## 초보자 혼동 포인트

- `int[]`, `long[]`, `double[]`에는 comparator overload가 없다.
- primitive 배열을 내림차순으로 뒤집어 둔 뒤 `Arrays.binarySearch(array, key)`를 호출하면 결과를 믿으면 안 된다.
- "내림차순으로 보고 싶다"와 "내림차순으로 저장/검색해야 한다"는 같은 요구가 아니다.
- 검색이 목적이면 오름차순 저장을 유지하고, 출력이나 순위 계산에서만 뒤집어 읽는 편이 안전하다.
- 못 찾은 결과가 음수일 때도 insertion point는 오름차순 기준으로 먼저 읽어야 한다.
- 내림차순 화면 인덱스가 필요하면 검색 결과를 변환하면 되지, 검색 전제 자체를 깨면 안 된다.

## 다음 읽기

- 배열 정렬과 `binarySearch` 전체 기초를 먼저 넓게 다시 보고 싶다면 [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
- object array에서는 왜 comparator를 정렬과 검색에 같이 넘길 수 있는지 이어서 보려면 [BinarySearch With Nullable Wrapper Sort Keys](./binarysearch-nullable-wrapper-sort-keys.md)
- "내림차순으로 본다"는 감각 자체를 view 관점으로 익히고 싶다면 [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
- comparator 조합과 `reversed()` 범위를 따로 연습하고 싶다면 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)

## 한 줄 정리

primitive 배열에서 descending search가 필요해 보여도 초보자에게 가장 안전한 기본 패턴은 **배열 자체는 오름차순으로 유지하고 `binarySearch`도 그 기준으로 수행한 뒤, 결과만 내림차순 view 기준으로 해석하는 것**이다.
