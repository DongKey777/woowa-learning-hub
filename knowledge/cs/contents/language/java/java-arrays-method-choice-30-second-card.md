# Java `Arrays` 메서드 선택 30초 카드

> 한 줄 요약: 배열에서 막혔을 때는 "출력", "값 비교", "복사", "정렬", "정렬된 상태에서 찾기" 중 무엇이 문제인지 먼저 나누면 `Arrays.toString()`, `Arrays.equals()`, `Arrays.copyOf()`, `Arrays.sort()`, `Arrays.binarySearch()`를 훨씬 빨리 고를 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 배열 입문 공통 confusion 체크리스트](./java-array-common-confusion-checklist.md)
- [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)
- [Java Array Equality Basics](./java-array-equality-basics.md)
- [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
- [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)

retrieval-anchor-keywords: java arrays method choice card, java arrays chooser beginner, java arrays tostring equals copyof sort binarysearch, java array which method to use, java arrays symptom first card, java array print compare copy sort search card, java arrays.tostring arrays.equals arrays.copyof arrays.sort arrays.binarysearch beginner, 배열 메서드 선택 카드, 배열 출력 비교 복사 정렬 검색 선택표, 배열 뭐 써야 하지, arrays.tostring equals copyof sort binarysearch 차이, beginner java arrays cheatsheet, java arrays method choice 30 second card basics, java arrays method choice 30 second card beginner, java arrays method choice 30 second card intro

## 먼저 잡는 멘탈 모델

초보자가 배열에서 메서드를 고를 때 가장 자주 하는 실수는 "배열 관련 메서드"를 한 덩어리로 외우는 것이다.
하지만 실제 질문은 다섯 갈래로 나뉜다.

- 눈에 보이게 출력하고 싶은가
- 같은 값인지 비교하고 싶은가
- 새 배열로 복사하고 싶은가
- 순서를 바꾸고 싶은가
- 이미 정렬된 배열에서 위치를 찾고 싶은가

즉 메서드 이름부터 떠올리기보다, **지금 증상이 무엇인지 먼저 말로 적는 편이 더 빠르다.**

## 30초 선택표

| 지금 드는 말 | 먼저 떠올릴 메서드 | 한 줄 판단 기준 |
|---|---|---|
| "`[I@...`처럼 이상하게 출력된다" | `Arrays.toString(array)` | 배열 내용을 사람이 읽을 문자열로 보고 싶을 때 |
| "두 배열 값이 같은지 확인하고 싶다" | `Arrays.equals(left, right)` | 같은 배열인지가 아니라 같은 값 순서인지 보고 싶을 때 |
| "원본을 안 건드리고 복사본을 만들고 싶다" | `Arrays.copyOf(array, array.length)` | 새 배열이 필요할 때 |
| "배열을 오름차순으로 정리하고 싶다" | `Arrays.sort(array)` | 배열 순서를 실제로 바꿔도 될 때 |
| "정렬된 배열에서 값 위치를 찾고 싶다" | `Arrays.binarySearch(array, target)` | 이미 같은 규칙으로 정렬된 배열에서만 |

## 가장 흔한 한 줄 오해 바로잡기

- 출력 문제인데 `array.toString()`을 쓰면 안 된다. 보통 원하는 것은 `Arrays.toString(...)`이다.
- 값 비교 문제인데 `array.equals(other)`를 쓰면 안 된다. 보통 원하는 것은 `Arrays.equals(...)`이다.
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
- 같은 값인지 보면 `equals`
- 분리된 새 배열이 필요하면 `copyOf`
- 순서를 정리하면 `sort`
- 정렬된 뒤 위치를 찾으면 `binarySearch`

## 자주 헷갈리는 분기

| 막힌 상황 | 왜 헷갈리나 | 먼저 갈 문서 |
|---|---|---|
| 출력은 했는데 2차원 배열이 또 이상하다 | 1차원과 중첩 배열 출력 도구가 다르다 | [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md) |
| `equals`가 `false`인데 눈으로 보면 같아 보인다 | 배열은 `==`와 `equals()`가 값 비교가 아니다 | [Java Array Equality Basics](./java-array-equality-basics.md) |
| 복사했다고 생각했는데 같이 바뀐다 | 대입과 복사를 섞어 읽고 있다 | [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md) |
| `binarySearch` 결과가 이상하다 | 정렬 전제나 반환값 해석을 놓쳤다 | [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md) |

## 한 줄 정리

배열 메서드 선택은 "무엇을 하고 싶은가"보다 "지금 무슨 증상이 보이는가"로 시작하면 쉽다. 출력이면 `toString`, 값 비교면 `equals`, 새 배열이면 `copyOf`, 순서 정리면 `sort`, 정렬된 뒤 위치 찾기면 `binarySearch`다.
