---
schema_version: 3
title: Java 2D Array Traversal Primer
concept_id: language/java-2d-array-traversal-primer
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 93
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- array-traversal
- off-by-one
- row-column
aliases:
- Java 2차원 배열 순회 입문
- java 2d array traversal primer
- arr.length vs arr row length
- jagged array traversal Java
- row column index confusion
- 자바 2차원 배열 row col for문
symptoms:
- arr.length를 column 개수로 착각해 안쪽 loop 조건에도 그대로 쓰다가 rectangular가 아닌 배열에서 터져
- board[row][col]에서 row와 col 순서를 좌표계처럼만 외워 Java의 배열 안의 배열 구조를 놓쳐
- jagged array도 항상 모든 row 길이가 같다고 가정해 ArrayIndexOutOfBoundsException을 만든다
intents:
- definition
- troubleshooting
- drill
prerequisites:
- language/java-language-basics
- language/java-loop-control-scope-follow-up-primer
- language/java-array-common-confusion-checklist
next_docs:
- language/java-2d-array-deeptostring-deepequals-shallow-copy-bridge
- language/java-array-debug-printing-basics
- language/java-array-copy-clone-basics
linked_paths:
- contents/language/java/java-language-basics.md
- contents/language/java/java-loop-control-scope-follow-up-primer.md
- contents/language/java/java-array-common-confusion-checklist.md
- contents/language/java/java-array-debug-printing-basics.md
- contents/language/java/java-array-copy-clone-basics.md
- contents/language/java/java-2d-array-deeptostring-deepequals-shallow-copy-bridge.md
- contents/data-structure/array-vs-linked-list.md
confusable_with:
- language/java-array-common-confusion-checklist
- language/java-2d-array-deeptostring-deepequals-shallow-copy-bridge
- language/java-loop-control-scope-follow-up-primer
forbidden_neighbors: []
expected_queries:
- Java 2차원 배열에서 arr.length와 arr[row].length 차이를 설명해줘
- jagged array를 안전하게 순회하는 중첩 for문을 보여줘
- board[row][col]에서 row와 col을 어떻게 읽어야 덜 헷갈려?
- 2차원 배열 순회에서 ArrayIndexOutOfBoundsException이 나는 흔한 이유가 뭐야?
- Java 2차원 배열은 왜 표 하나보다 배열 안의 배열로 이해해야 해?
contextual_chunk_prefix: |
  이 문서는 Java 2D array traversal을 arr.length, arr[row].length, row/column index, jagged array 관점으로 설명하는 beginner primer다.
  2차원 배열 순회, row col, arr.length vs arr[i].length, jagged array, ArrayIndexOutOfBoundsException 질문이 본 문서에 매핑된다.
---
# Java 2차원 배열 순회 입문

> 한 줄 요약: Java의 2차원 배열은 "표 하나"라기보다 "row 배열 안에 row 배열이 들어 있는 구조"라서, 바깥 길이는 `arr.length`, 안쪽 길이는 매 row마다 `arr[row].length`로 읽어야 jagged array 혼동을 줄일 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java 2d array traversal primer, java two dimensional array beginner, java row column index confusion, java arr.length vs arr[i].length, java jagged array traversal, java board traversal java, 자바 2차원 배열 입문, 자바 2차원 배열 처음 배우는데, 자바 행 열 인덱스 헷갈림, 자바 arr.length arr[i].length 차이, 자바 2차원 배열 for문 기초, 배열 안의 배열 뭐예요, 처음 배우는데 2차원 배열, 2차원 배열 뭐예요, 2차원 배열 왜 헷갈려요
> 관련 문서:
> - [자바 언어의 구조와 기본 문법](./java-language-basics.md)
> - [Java 반복문과 스코프 follow-up 입문](./java-loop-control-scope-follow-up-primer.md)
> - [Java 배열 입문 공통 confusion 체크리스트](./java-array-common-confusion-checklist.md)
> - [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)
> - [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
> - [배열 vs 연결 리스트](../../data-structure/array-vs-linked-list.md)

> retrieval-anchor-keywords: java 2d array traversal primer, java two dimensional array beginner, java multidimensional array beginner, java row column index confusion, java arr.length vs arr[i].length, java jagged array primer, java jagged array traversal, java 2d array nested loop, java matrix loop beginner, java board traversal java, java grid traversal java beginner, java row first column second, java 2차원 배열 순회, 자바 2차원 배열 입문, 자바 행 열 인덱스 헷갈림, 자바 arr.length arr[i].length 차이, 자바 가변 길이 2차원 배열, jagged array 순회, 배열 안의 배열, 행 먼저 열 나중, 2차원 배열 for문 기초, 2차원 배열 row column 차이

## 왜 이 문서가 필요한가

2차원 배열을 처음 볼 때 초보자가 가장 자주 멈추는 지점은 보통 세 가지다.

- `board[row][col]`에서 왜 row가 먼저인지
- `arr.length`와 `arr[row].length` 중 무엇을 어디에 써야 하는지
- 모든 row 길이가 같다고 생각하고 순회했다가 jagged array에서 왜 터지는지

이 문서는 문법보다 먼저 "Java의 2차원 배열을 어떤 모양으로 생각해야 하는가"를 짧게 고정한다.

## 먼저 잡는 mental model

Java의 2차원 배열은 "큰 표 한 장"으로만 생각하면 자주 헷갈린다.
초보자에게는 아래 그림처럼 읽는 편이 더 안전하다.

> 2차원 배열 = "row 배열" 안에 "각 row 배열"이 들어 있는 구조

즉:

- 첫 번째 인덱스 `arr[row]`는 "몇 번째 row를 고를까?"
- 두 번째 인덱스 `arr[row][col]`는 "그 row 안에서 몇 번째 칸을 고를까?"

짧게 외우면 다음 한 줄이 기본형이다.

> `arr.length`는 row 개수, `arr[row].length`는 그 row의 column 개수다.

## 20초 비교표

`int[][] board = {{1, 2, 3}, {4, 5, 6}};` 를 기준으로 보면:

| 표현 | 뜻 | 값 |
|---|---|---|
| `board.length` | row 개수 | `2` |
| `board[0].length` | 0번 row의 column 개수 | `3` |
| `board[1].length` | 1번 row의 column 개수 | `3` |
| `board[1][2]` | 1번 row, 2번 column 값 | `6` |

여기서 중요한 점은 하나다.

- 바깥 `length`는 전체 row 수를 말한다.
- 안쪽 `length`는 "현재 보고 있는 row"의 칸 수를 말한다.

## 가장 안전한 기본 순회

```java
int[][] board = {
    {1, 2, 3},
    {4, 5, 6}
};

for (int row = 0; row < board.length; row++) {
    for (int col = 0; col < board[row].length; col++) {
        System.out.println("board[" + row + "][" + col + "]=" + board[row][col]);
    }
}
```

이 코드를 읽는 순서는 이렇다.

1. 바깥 루프가 row를 고른다.
2. 안쪽 루프가 그 row 안의 column을 돈다.
3. 그래서 접근 순서는 항상 `board[row][col]`이다.

초보자 기준으로는 변수 이름을 `i`, `j`보다 `row`, `col`로 두는 편이 실수를 줄여 준다.

## row/column이 왜 자꾸 바뀌어 보일까

헷갈릴 때는 "첫 인덱스가 세로냐 가로냐"를 외우려 하기보다, 아래 질문으로 다시 보면 쉽다.

| 지금 보는 코드 | 먼저 읽는 질문 | 의미 |
|---|---|---|
| `board[row]` | "몇 번째 row를 꺼냈지?" | row 하나를 고른다 |
| `board[row][col]` | "그 row 안에서 몇 번째 칸이지?" | 실제 값 하나를 고른다 |

즉 `board[1]`은 값 하나가 아니라 row 하나다.
그래서 `board[1].length`가 가능하고, `board[1][2]`처럼 한 칸 더 들어갈 수 있다.

## jagged array에서는 왜 `board[row].length`를 써야 할까

Java의 2차원 배열은 각 row 길이가 꼭 같을 필요가 없다.

```java
int[][] scores = {
    {90, 85, 100},
    {70},
    {88, 92}
};
```

이런 구조를 보통 jagged array라고 부른다.
초보자에게는 "row마다 칸 수가 다른 2차원 배열"이라고 이해하면 충분하다.

이때 안전한 순회는 아래처럼 해야 한다.

```java
for (int row = 0; row < scores.length; row++) {
    for (int col = 0; col < scores[row].length; col++) {
        System.out.println(scores[row][col]);
    }
}
```

왜냐하면:

- `scores.length`는 row 개수라서 바깥 루프 조건에 맞다
- `scores[row].length`는 현재 row 길이라서 안쪽 루프 조건에 맞다

반대로 아래 코드는 jagged array에서 위험하다.

```java
for (int row = 0; row < scores.length; row++) {
    for (int col = 0; col < scores[0].length; col++) {
        System.out.println(scores[row][col]);
    }
}
```

`row = 1`일 때 `scores[1].length`는 `1`인데, `scores[0].length`는 `3`이다.
그래서 존재하지 않는 `scores[1][1]`, `scores[1][2]`를 읽으려 하며 `ArrayIndexOutOfBoundsException`이 날 수 있다.

## 초보자가 자주 섞는 혼동

### 1. `arr.length`를 column 개수로 착각한다

- `arr.length`는 바깥 배열 길이다
- 2차원 배열에서는 보통 row 개수다

즉 안쪽 루프까지 `col < arr.length`로 두면, 우연히 정사각형 배열일 때만 맞고 다른 모양에서는 틀릴 수 있다.

### 2. 모든 row 길이가 같다고 가정한다

- 표처럼 보여도 Java에서는 row마다 길이가 다를 수 있다
- 그래서 안쪽 조건은 `arr[row].length`가 기본형이다

### 3. `arr[row]`도 이미 배열이라는 점을 놓친다

`arr[row]`는 값 하나가 아니라 row 배열 하나다.
그래서:

- 출력은 `Arrays.toString(arr[row])`
- 길이는 `arr[row].length`
- 값 하나는 `arr[row][col]`

이 순서로 읽으면 덜 헷갈린다.

## 디버깅할 때 바로 보는 예제

```java
import java.util.Arrays;

int[][] board = {
    {1, 2, 3},
    {4, 5},
    {6}
};

System.out.println("rows=" + board.length);

for (int row = 0; row < board.length; row++) {
    System.out.println("row " + row + " -> " + Arrays.toString(board[row]));

    for (int col = 0; col < board[row].length; col++) {
        System.out.println("value=" + board[row][col]);
    }
}
```

이 예제에서 먼저 볼 포인트는 두 가지다.

- `board.length`는 `3`이다
- 각 row 출력 길이는 `3`, `2`, `1`로 다르다

즉 "2차원 배열은 큰 직사각형 한 장"이라는 생각보다 "row 배열 묶음"이라는 생각이 실제 Java 구조에 더 가깝다.

## 빠른 체크리스트

- 바깥 루프는 보통 `row < arr.length`
- 안쪽 루프는 보통 `col < arr[row].length`
- 값 접근은 `arr[row][col]`
- `arr[row]`는 값 하나가 아니라 row 배열
- row 길이가 모두 같다고 가정하지 않기

## 다음에 어디로 이어 읽으면 좋은가

| 지금 가장 막히는 질문 | 다음 문서 |
|---|---|
| "`for`/`break`/`continue` 자체가 아직 흔들린다" | [Java 반복문과 스코프 follow-up 입문](./java-loop-control-scope-follow-up-primer.md) |
| "출력해 보니 `[[I@...`처럼 보여서 구조를 확인하기 어렵다" | [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md) |
| "2차원 배열 복사했는데 안쪽 row가 같이 바뀐다" | [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md) |
| "배열 비교/공유/정렬 문제까지 같이 섞여 있다" | [Java 배열 입문 공통 confusion 체크리스트](./java-array-common-confusion-checklist.md) |

## 한 줄 정리

Java의 2차원 배열은 "배열 안의 배열"이므로, 순회 기본형은 `row < arr.length`, `col < arr[row].length`, 값 접근은 `arr[row][col]`으로 읽는 것이 가장 안전하다.
