---
schema_version: 3
title: Java Arrays Method Choice 30 Second Card
concept_id: language/java-arrays-method-choice-30-second-card
canonical: true
category: language
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 95
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- arrays-utility
- method-choice
- beginner-routing
aliases:
- Java Arrays 메서드 선택 30초 카드
- java arrays method chooser beginner
- Arrays.toString equals copyOf sort binarySearch 선택
- 배열 출력 비교 복사 정렬 검색 선택표
- java array which Arrays method
- 배열 뭐 써야 하지
symptoms:
- Arrays 메서드를 이름으로만 외워 출력, 비교, 복사, 정렬, 검색 중 지금 문제에 맞는 도구를 고르지 못해
- binarySearch를 정렬 전 배열에 써도 결과가 의미 있다고 생각해 precondition을 놓쳐
- sort가 원본을 바꾸는 API라는 점을 모르고 원본 보존 없이 호출한다
intents:
- comparison
- troubleshooting
- definition
prerequisites:
- language/java-array-common-confusion-checklist
- language/java-array-debug-printing-basics
- language/java-array-equality-basics
next_docs:
- language/java-array-copy-clone-basics
- language/java-array-sorting-searching-basics
- language/java-2d-array-deeptostring-deepequals-shallow-copy-bridge
linked_paths:
- contents/language/java/java-array-common-confusion-checklist.md
- contents/language/java/java-array-debug-printing-basics.md
- contents/language/java/java-array-equality-basics.md
- contents/language/java/java-array-copy-clone-basics.md
- contents/language/java/java-array-sorting-searching-basics.md
- contents/language/java/java-2d-array-deeptostring-deepequals-shallow-copy-bridge.md
confusable_with:
- language/java-array-debug-printing-basics
- language/java-array-equality-basics
- language/java-array-copy-clone-basics
forbidden_neighbors: []
expected_queries:
- Java Arrays.toString equals deepEquals copyOf sort binarySearch를 증상별로 어떻게 고르면 돼?
- 배열 출력 비교 복사 정렬 검색 중 어떤 Arrays 메서드를 써야 하는지 표로 알려줘
- Arrays.binarySearch는 왜 정렬된 배열에서만 써야 해?
- Arrays.sort가 원본 배열을 바꾸는지와 원본 보존 방법을 설명해줘
- 2차원 배열 값 비교에는 Arrays.equals가 아니라 왜 deepEquals가 필요해?
contextual_chunk_prefix: |
  이 문서는 Java Arrays utility method를 출력, equality, copy, sort, binarySearch 증상별로 고르는 beginner chooser다.
  Arrays.toString, Arrays.equals, deepEquals, copyOf, sort, binarySearch, 배열 메서드 선택 질문이 본 문서에 매핑된다.
---
# Java `Arrays` 메서드 선택 30초 카드

> 한 줄 요약: 배열에서 막혔을 때는 "`[I@...`처럼 출력이 이상한가", "값은 같은데 `==`나 `array.equals(...)`가 `false`인가", "한쪽을 바꾸면 다른 쪽도 같이 바뀌는가", "정렬 뒤 원본이 바뀌었는가"를 먼저 나누면 `Arrays.toString()`, `Arrays.equals()`, `Arrays.copyOf()`, `Arrays.sort()`, `Arrays.binarySearch()`를 훨씬 빨리 고를 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)
- [Java 배열 입문 공통 confusion 체크리스트](./java-array-common-confusion-checklist.md)
- [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)
- [Java Array Equality Basics](./java-array-equality-basics.md)
- [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
- [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)

retrieval-anchor-keywords: java arrays method choice card, java arrays chooser beginner, java arrays tostring equals deepequals copyof sort binarysearch, java array which method to use, java arrays symptom first card, java array print compare copy sort search card, java arrays.tostring arrays.equals arrays.deepequals arrays.copyof arrays.sort arrays.binarysearch beginner, 배열 메서드 선택 카드, 배열 출력 비교 복사 정렬 검색 선택표, 배열 뭐 써야 하지, 배열 비교 뭐 써야 하지, 배열 값은 같은데 false, 배열 equals 왜 false, 2차원 배열 비교 뭐 써야 하지

## 먼저 잡는 멘탈 모델

초보자가 배열에서 메서드를 고를 때 가장 자주 하는 실수는 "배열 관련 메서드"를 한 덩어리로 외우는 것이다.
하지만 실제 질문은 다섯 갈래로 나뉜다.

- 눈에 보이게 출력하고 싶은가
- 같은 값인지 비교하고 싶은가
- 새 배열로 복사하고 싶은가
- 순서를 바꾸고 싶은가
- 이미 정렬된 배열에서 위치를 찾고 싶은가

특히 comparison 쪽은 질문을 한 번 더 잘라야 한다.

- 1차원 배열 값 비교인가
- 배열 안에 배열이 있는 중첩 비교인가
- 아니면 비교 문제가 아니라 같은 배열을 같이 보고 있는 alias 문제인가

즉 메서드 이름부터 떠올리기보다, **지금 증상이 무엇인지 먼저 말로 적는 편이 더 빠르다.**

## 30초 선택표

| 지금 드는 말 | 먼저 떠올릴 메서드 | 한 줄 판단 기준 |
|---|---|---|
| "`[I@...`처럼 이상하게 출력된다" | `Arrays.toString(array)` | 배열 내용을 사람이 읽을 문자열로 보고 싶을 때 |
| "두 배열 값이 같은지 확인하고 싶다" | `Arrays.equals(left, right)` | 1차원 배열에서 같은 배열이 아니라 같은 값 순서인지 보고 싶을 때 |
| "값은 같은데 `==`나 `array.equals(...)`가 `false`다" | `Arrays.equals(left, right)` | 비교 대상이 1차원 배열이면 값 비교 도구를 따로 써야 할 때 |
| "2차원 배열 비교가 이상하다" | `Arrays.deepEquals(left, right)` | 배열 안에 배열이 있어서 안쪽까지 내려가야 할 때 |
| "한쪽을 바꾸면 다른 쪽도 같이 바뀐다" | 메서드보다 alias 확인 먼저 | `copied == original`이면 복사가 아니라 공유일 수 있을 때 |
| "원본을 안 건드리고 복사본을 만들고 싶다" | `Arrays.copyOf(array, array.length)` | 새 배열이 필요할 때 |
| "배열을 오름차순으로 정리하고 싶다" | `Arrays.sort(array)` | 배열 순서를 실제로 바꿔도 될 때 |
| "정렬된 배열에서 값 위치를 찾고 싶다" | `Arrays.binarySearch(array, target)` | 이미 같은 규칙으로 정렬된 배열에서만 |

## 가장 흔한 한 줄 오해 바로잡기

- 출력 문제인데 `array.toString()`을 쓰면 안 된다. 보통 원하는 것은 `Arrays.toString(...)`이다.
- 값 비교 문제인데 `array.equals(other)`를 쓰면 안 된다. 보통 원하는 것은 `Arrays.equals(...)`이고, 2차원 배열이면 `Arrays.deepEquals(...)`다.
- "값은 같은데 왜 `false`지?"가 보이면 `==`와 `array.equals(...)`가 값 비교가 아니라는 신호다.
- "한쪽을 바꾸면 다른 쪽도 같이 바뀐다"가 보이면 비교보다 alias/copy 분기를 먼저 탄다.
- 복사 문제인데 `copied = original`은 복사가 아니라 같은 배열 공유다.
- 검색 문제인데 `Arrays.binarySearch(...)`를 정렬 전에 쓰면 결과를 믿으면 안 된다.
- `Arrays.sort(...)`를 호출하면 원본 배열 순서가 바로 바뀐다.

## 같은 예제로 한 번에 보기

```java
import java.util.Arrays;

int[] scores = {30, 10, 20};

System.out.println(Arrays.toString(scores));
// [30, 10, 20]

int[] copied = Arrays.copyOf(scores, scores.length);
System.out.println(Arrays.equals(scores, copied));
// true

Arrays.sort(copied);
System.out.println(Arrays.toString(copied));
// [10, 20, 30]

int idx = Arrays.binarySearch(copied, 20);
System.out.println(idx);
// 1
```

이 예제를 문장으로 읽으면 더 단순하다.

- 보여 주려면 `toString`
- 같은 값인지 보면 1차원은 `equals`, 중첩 배열은 `deepEquals`
- 분리된 새 배열이 필요하면 `copyOf`
- 순서를 정리하면 `sort`
- 정렬된 뒤 위치를 찾으면 `binarySearch`

## 자주 헷갈리는 분기

| 막힌 상황 | 왜 헷갈리나 | 먼저 갈 문서 |
|---|---|---|
| 출력은 했는데 2차원 배열이 또 이상하다 | 1차원과 중첩 배열 출력 도구가 다르다 | [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md) |
| `==`나 `array.equals(...)`가 `false`인데 눈으로 보면 같아 보인다 | 배열은 `==`와 `equals()`가 값 비교가 아니다 | [Java Array Equality Basics](./java-array-equality-basics.md) |
| 2차원 배열 comparison이 계속 어긋난다 | `Arrays.equals(...)`와 `Arrays.deepEquals(...)` 분기가 필요하다 | [Java Array Equality Basics](./java-array-equality-basics.md) |
| 한쪽을 바꾸면 다른 쪽도 같이 바뀐다 | 대입과 복사를 섞어 읽고 있다 | [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md) |
| `binarySearch` 결과가 이상하다 | 정렬 전제나 반환값 해석을 놓쳤다 | [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md) |

## 한 줄 정리

배열 메서드 선택은 "무엇을 하고 싶은가"보다 "지금 무슨 증상이 보이는가"로 시작하면 쉽다. 출력이면 `toString`, 값 비교면 1차원은 `equals`·중첩 배열은 `deepEquals`, 새 배열이면 `copyOf`, 순서 정리면 `sort`, 정렬된 뒤 위치 찾기면 `binarySearch`다.
