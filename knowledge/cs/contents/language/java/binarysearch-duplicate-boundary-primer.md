# BinarySearch Duplicate Boundary Primer

> 한 줄 요약: `Arrays.binarySearch()`는 중복값이 있을 때 "아무 일치 위치 하나"만 줄 수 있으므로, 초보자에게 가장 쉬운 follow-up은 "찾은 위치에서 왼쪽/오른쪽으로 같은 값 구간을 확장해 첫 위치와 마지막 위치를 읽는 것"이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: binarysearch duplicate boundary primer basics, binarysearch duplicate boundary primer beginner, binarysearch duplicate boundary primer intro, java basics, beginner java, 처음 배우는데 binarysearch duplicate boundary primer, binarysearch duplicate boundary primer 입문, binarysearch duplicate boundary primer 기초, what is binarysearch duplicate boundary primer, how to binarysearch duplicate boundary primer
> 관련 문서:
> - [Language README](../README.md)
> - [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
> - [BinarySearch With Nullable Wrapper Sort Keys](./binarysearch-nullable-wrapper-sort-keys.md)
> - [Priority-Only Range Search Follow-Up](./priority-only-range-search-follow-up.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Primitive Array Descending Search Primer](./primitive-array-descending-binarysearch-primer.md)
> - [Binary Search Patterns](../../algorithm/binary-search-patterns.md)

> retrieval-anchor-keywords: language-java-00097, binarySearch duplicate boundary primer, java binarySearch duplicates first last occurrence, java Arrays.binarySearch duplicate index beginner, java first occurrence after Arrays.binarySearch, java last occurrence after Arrays.binarySearch, java duplicate range after binary search java, java binarySearch left boundary right boundary beginner, java binarySearch scan left right duplicates, java binarySearch exact hit then expand duplicates, java binarySearch first last index primitive array, java binarySearch duplicate block beginner, java lower bound upper bound handoff java, java int array lowerBound upperBound helper, java long array lowerBound upperBound helper, java primitive array boundary helper beginner, java duplicate expansion to lowerBound upperBound java, java comparator duplicate boundary binarySearch, java Arrays.binarySearch duplicates no first guarantee, java first last occurrence sorted array java beginner, 자바 binarySearch 중복 첫 위치, 자바 binarySearch 중복 마지막 위치, 자바 Arrays.binarySearch 중복 인덱스, 자바 정렬 배열 중복 범위 찾기, 자바 binarySearch 찾은 뒤 좌우 확장, 자바 int 배열 lowerBound upperBound, 자바 long 배열 lowerBound upperBound

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 비교 표](#한-장-비교-표)
- [가장 쉬운 패턴: 찾은 위치에서 좌우 확장](#가장-쉬운-패턴-찾은-위치에서-좌우-확장)
- [재사용 helper로 묶기](#재사용-helper로-묶기)
- [좌우 확장에서 lower/upper bound helper로 넘어가기](#좌우-확장에서-lowerupper-bound-helper로-넘어가기)
- [comparator 배열에서도 같은 생각으로 읽기](#comparator-배열에서도-같은-생각으로-읽기)
- [언제 lower/upper bound로 넘어가면 좋을까](#언제-lowerupper-bound로-넘어가면-좋을까)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

`Arrays.binarySearch()`를 막 배운 초보자가 바로 부딪히는 follow-up 질문은 거의 같다.

- 값이 여러 개면 첫 번째 위치는 어떻게 찾지?
- 마지막 위치는 어떻게 찾지?
- `binarySearch()`가 `2`를 찾았는데 왜 인덱스 `1`이 아니라 `2`가 나오지?
- 이미 찾았는데 또 다른 이진 탐색을 해야 하나?

핵심은 간단하다.

- `Arrays.binarySearch()`는 **중복값 구간의 아무 위치 하나**를 돌려줄 수 있다
- 그래서 "존재 여부"는 바로 알 수 있어도, "첫 위치/마지막 위치"는 추가 해석이 필요하다
- beginner 단계에서는 **찾은 위치에서 같은 값이 끝날 때까지 좌우로 확장**하는 패턴이 가장 읽기 쉽다

이 문서는 그 가장 쉬운 패턴을 먼저 잡아 주고, 나중에 경계 탐색으로 넘어갈 연결점까지 짧게 남긴다.

## 먼저 잡을 mental model

중복값이 있는 정렬 배열을 이렇게 상상하면 쉽다.

```text
[1, 2, 2, 2, 4, 7]
    ^-----^
   같은 값 블록
```

`Arrays.binarySearch(numbers, 2)`는 이 블록 안의:

- 맨 왼쪽
- 가운데
- 맨 오른쪽

중 아무 곳이나 줄 수 있다.

그래서 질문을 두 단계로 나누면 된다.

1. `binarySearch()`로 "2가 있는 블록 안 아무 한 칸"을 찾는다
2. 그 칸에서 왼쪽/오른쪽으로 움직이며 블록의 시작과 끝을 읽는다

초보자에게는 이 mental model이 가장 안전하다.

## 한 장 비교 표

| 지금 알고 싶은 것 | 바로 쓸 도구 | 추가로 해야 할 일 | beginner 메모 |
|---|---|---|---|
| `2`가 있는지 | `Arrays.binarySearch(numbers, 2)` | 없음 | `0` 이상이면 존재 |
| 첫 번째 `2` 위치 | `Arrays.binarySearch(numbers, 2)` | 찾은 칸에서 왼쪽 확장 | 같은 값 블록의 왼쪽 끝 |
| 마지막 `2` 위치 | `Arrays.binarySearch(numbers, 2)` | 찾은 칸에서 오른쪽 확장 | 같은 값 블록의 오른쪽 끝 |
| `2`가 몇 개 있는지 | 첫 위치 + 마지막 위치 | `last - first + 1` | 연속 구간 길이 |
| 매번 빠르게 경계 찾기 | lower/upper bound | 별도 helper 작성 | 다음 단계용 패턴 |

## 가장 쉬운 패턴: 찾은 위치에서 좌우 확장

예제를 먼저 보자.

```java
import java.util.Arrays;

int[] numbers = {1, 2, 2, 2, 4, 7};

int hit = Arrays.binarySearch(numbers, 2);
System.out.println(hit); // 1, 2, 3 중 하나
```

여기서 `hit`는 첫 번째 `2`를 보장하지 않는다.
대신 `hit`가 `2` 블록 안에만 있으면 충분하다.

그다음 이렇게 읽는다.

```java
int first = hit;
while (first > 0 && numbers[first - 1] == 2) {
    first--;
}

int last = hit;
while (last < numbers.length - 1 && numbers[last + 1] == 2) {
    last++;
}

System.out.println(first); // 1
System.out.println(last);  // 3
```

동작 순서는 단순하다.

1. `hit`에서 시작한다
2. 왼쪽 칸도 같은 값이면 계속 왼쪽으로 간다
3. 더 이상 같은 값이 아니면 거기가 첫 위치다
4. 오른쪽도 같은 방식으로 읽으면 마지막 위치다

### 없는 값이면 먼저 멈춘다

```java
int hit = Arrays.binarySearch(numbers, 3); // 음수

if (hit < 0) {
    System.out.println("3 is absent");
}
```

찾지 못했는데 바로 좌우 확장을 시작하면 안 된다.
반드시 `hit >= 0`인지 먼저 확인한다.

### 한 번에 전체 흐름 보기

## 가장 쉬운 패턴: 찾은 위치에서 좌우 확장 (계속 2)

```java
import java.util.Arrays;

public class DuplicateBoundaryExample {
    public static void main(String[] args) {
        int[] numbers = {1, 2, 2, 2, 4, 7};

        int hit = Arrays.binarySearch(numbers, 2);
        if (hit < 0) {
            System.out.println("not found");
            return;
        }

        int first = hit;
        while (first > 0 && numbers[first - 1] == numbers[hit]) {
            first--;
        }

        int last = hit;
        while (last < numbers.length - 1 && numbers[last + 1] == numbers[hit]) {
            last++;
        }

        int count = last - first + 1;

        System.out.println(hit);   // 1, 2, 3 중 하나
        System.out.println(first); // 1
        System.out.println(last);  // 3
        System.out.println(count); // 3
    }
}
```

여기서는 비교 대상을 `2`로 다시 쓰는 대신 `numbers[hit]`로 읽었다.
그러면 "찾은 값 블록 전체"라는 의도가 더 잘 보인다.

## 재사용 helper로 묶기

같은 작업을 여러 번 한다면 helper로 빼 두는 편이 읽기 쉽다.

```java
import java.util.Arrays;

static int firstIndexOf(int[] numbers, int target) {
    int hit = Arrays.binarySearch(numbers, target);
    if (hit < 0) {
        return -1;
    }

    int first = hit;
    while (first > 0 && numbers[first - 1] == target) {
        first--;
    }
    return first;
}

static int lastIndexOf(int[] numbers, int target) {
    int hit = Arrays.binarySearch(numbers, target);
    if (hit < 0) {
        return -1;
    }

    int last = hit;
    while (last < numbers.length - 1 && numbers[last + 1] == target) {
        last++;
    }
    return last;
}
```

사용 예시는 다음과 같다.

```java
int[] numbers = {1, 2, 2, 2, 4, 7};

System.out.println(firstIndexOf(numbers, 2)); // 1
System.out.println(lastIndexOf(numbers, 2));  // 3
System.out.println(firstIndexOf(numbers, 3)); // -1
System.out.println(lastIndexOf(numbers, 3));  // -1
```

beginner 관점에서는 이 방식의 장점이 분명하다.

- 이미 아는 `Arrays.binarySearch()` 위에 얹어서 읽을 수 있다
- loop가 짧고 의도가 눈에 보인다
- 첫 위치, 마지막 위치, 개수 계산까지 자연스럽게 이어진다

## 좌우 확장에서 lower/upper bound helper로 넘어가기

여기서 다음 단계로 넘어갈 때는 이름만 어렵게 느끼지 않으면 된다.

- 좌우 확장은 "찾은 칸에서 블록 양끝까지 걸어간다"
- lower bound는 "처음으로 `target` 이상인 칸"을 바로 찾는다
- upper bound는 "처음으로 `target` 초과인 칸"을 바로 찾는다

같은 블록 그림으로 읽으면 둘은 이렇게 이어진다.

```text
[1, 2, 2, 2, 4, 7]
    ^        ^
 lower     upper
 bound      bound
```

- `lowerBound(numbers, 2)` -> `1`
- `upperBound(numbers, 2)` -> `4`
- 그래서 마지막 `2` 위치는 `upperBound(...) - 1`이다

즉 "좌우 확장으로 읽던 첫 위치/마지막 위치"를
이제는 "helper 두 개로 바로 읽는다"로 바꾸는 셈이다.

### `int[]`용 beginner helper

```java
static int lowerBound(int[] numbers, int target) {
    int left = 0;
    int right = numbers.length;

    while (left < right) {
        int mid = left + (right - left) / 2;
        if (numbers[mid] >= target) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}

static int upperBound(int[] numbers, int target) {
    int left = 0;
    int right = numbers.length;

    while (left < right) {
        int mid = left + (right - left) / 2;
        if (numbers[mid] <= target) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    return left;
}
```

사용할 때는 `upperBound(...)`가 "마지막 위치"가 아니라
"마지막 위치 다음 칸"이라는 점만 조심하면 된다.

## 좌우 확장에서 lower/upper bound helper로 넘어가기 (계속 2)

```java
int[] numbers = {1, 2, 2, 2, 4, 7};

int first = lowerBound(numbers, 2);     // 1
int afterLast = upperBound(numbers, 2); // 4

if (first == numbers.length || numbers[first] != 2) {
    System.out.println("not found");
} else {
    int last = afterLast - 1;           // 3
    int count = afterLast - first;      // 3
    System.out.println(first);
    System.out.println(last);
    System.out.println(count);
}
```

### `long[]`도 모양은 같다

primitive 타입이 바뀌어도 비교식만 같은 흐름으로 읽으면 된다.

```java
static int lowerBound(long[] numbers, long target) {
    int left = 0;
    int right = numbers.length;

    while (left < right) {
        int mid = left + (right - left) / 2;
        if (numbers[mid] >= target) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}

static int upperBound(long[] numbers, long target) {
    int left = 0;
    int right = numbers.length;

    while (left < right) {
        int mid = left + (right - left) / 2;
        if (numbers[mid] <= target) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    return left;
}
```

```java
long[] ids = {10L, 20L, 20L, 20L, 50L};

int first = lowerBound(ids, 20L);      // 1
int afterLast = upperBound(ids, 20L);  // 4
int last = afterLast - 1;              // 3
```

### 좌우 확장과 helper를 한 장으로 비교하면

## 좌우 확장에서 lower/upper bound helper로 넘어가기 (계속 3)

| 방식 | 먼저 떠올릴 질문 | 장점 | beginner 메모 |
|---|---|---|---|
| 좌우 확장 | "이미 찾은 칸에서 블록 끝까지 가자" | 직관적이다 | 첫 학습용으로 가장 쉽다 |
| lower/upper bound | "첫 `target 이상`, 첫 `target 초과`를 바로 찾자" | 재사용이 쉽다 | helper 이름만 익숙해지면 반복 작업에 강하다 |

그래서 입문자에게는 보통 이 순서가 가장 덜 헷갈린다.

1. 먼저 `binarySearch()` + 좌우 확장으로 같은 값 블록을 본다
2. 그다음 같은 의도를 `lowerBound()` / `upperBound()` helper로 옮긴다
3. 자주 쓰면 `int[]`, `long[]`용 helper를 따로 두고 재사용한다

## comparator 배열에서도 같은 생각으로 읽기

객체 배열이나 custom comparator 배열에서도 큰 생각은 같다.

- 먼저 **정렬에 쓴 것과 같은 comparator**로 `binarySearch(...)` 한다
- 일치 위치 하나를 얻는다
- 그 뒤 같은 comparator 기준으로 왼쪽/오른쪽 경계를 읽는다

예를 들어 문자열을 길이순으로 정렬했다고 해 보자.

```java
import java.util.Arrays;
import java.util.Comparator;

String[] words = {"a", "to", "be", "cat", "dog"};
Comparator<String> byLength = Comparator.comparingInt(String::length);

Arrays.sort(words, byLength);
int hit = Arrays.binarySearch(words, "hi", byLength);
```

여기서 `hit`는 길이가 `2`인 `"to"`나 `"be"` 위치 중 하나가 될 수 있다.
왜냐하면 이 comparator는 "문자열 내용"이 아니라 "길이"만 보기 때문이다.

즉 이 경우 "중복"은 값이 똑같다는 뜻이 아니라 **comparator 기준으로 같은 블록**이라는 뜻이다.

초보자 단계에서는 이 정도만 확실히 기억하면 충분하다.

- primitive 배열은 `==`로 같은 값 블록을 읽는다
- comparator 배열은 "comparator가 `0`을 주는 블록"을 읽는다고 생각한다

comparator tie-breaker나 nullable key까지 같이 들어오면,
[BinarySearch With Nullable Wrapper Sort Keys](./binarysearch-nullable-wrapper-sort-keys.md)에서 boundary 감각을 이어서 보는 편이 안전하다.

## 언제 lower/upper bound로 넘어가면 좋을까

좌우 확장 패턴은 beginner에게 가장 쉽지만, 중복 구간이 아주 길면 그 길이만큼 더 움직인다.

그래서 다음 상황에서는 lower/upper bound helper로 넘어가면 좋다.

- 첫 위치/마지막 위치를 자주 찾아야 한다
- 중복 구간이 길 수 있다
- comparator 배열에서 경계를 더 예측 가능하게 읽고 싶다

다만 입문 단계에서는 먼저 이 한 줄만 잡으면 된다.

- **지금은 `binarySearch()`로 한 칸을 찾고 좌우 확장하는 패턴을 익힌다**
- **다음 단계에서는 "처음 `target` 이상"과 "처음 `target` 초과"를 찾는 경계 탐색으로 넓힌다**

## 초보자가 자주 헷갈리는 지점

- `Arrays.binarySearch()`가 `2`를 찾았다고 해서 첫 번째 `2`를 보장하는 것은 아니다.
- 중복값 구간에서는 `hit`가 왼쪽 끝, 가운데, 오른쪽 끝 중 어디든 될 수 있다.
- 값을 못 찾았으면 음수가 나오므로, 좌우 확장 전에 `hit >= 0`부터 확인해야 한다.
- 이 패턴은 **정렬된 배열**에서만 의미가 있다. 정렬되지 않은 배열이면 `hit`부터 믿을 수 없다.
- 내림차순이나 custom ordering이면 정렬할 때 쓴 것과 같은 comparator로 검색해야 한다.
- comparator가 tie-breaker 없이 거칠면, "같은 값 블록"도 더 넓게 잡힐 수 있다.
- count가 필요하면 `last - first + 1`로 바로 읽을 수 있다.

## 어떤 문서를 다음에 읽으면 좋은가

- `sort`와 `binarySearch` 전체 규칙을 먼저 다시 묶어 보고 싶다면 [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
- comparator 정렬 배열에서 같은 comparator를 검색에도 재사용하는 감각을 다시 잡고 싶다면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- nullable wrapper sort key와 repeated `null` 경계까지 같이 보고 싶다면 [BinarySearch With Nullable Wrapper Sort Keys](./binarysearch-nullable-wrapper-sort-keys.md)
- primitive 배열에서 descending search 전제까지 같이 정리하고 싶다면 [Primitive Array Descending Search Primer](./primitive-array-descending-binarysearch-primer.md)
- `lower_bound`, `upper_bound` 같은 일반 경계 탐색 패턴으로 넓히고 싶다면 [Binary Search Patterns](../algorithm/binary-search-patterns.md)

## 한 줄 정리

중복값이 있는 정렬 배열에서 `Arrays.binarySearch()`는 일치 위치 하나만 보장하므로, beginner에게 가장 쉬운 다음 단계는 **찾은 위치에서 같은 값 블록을 왼쪽과 오른쪽으로 확장해 첫 위치와 마지막 위치를 읽는 것**이다.
