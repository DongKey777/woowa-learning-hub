# Java Array Debug Printing Basics

> 한 줄 요약: 배열을 그냥 출력하면 `Object.toString()` 계열의 reference-like 문자열이 보이기 쉽고, 1차원 배열은 `Arrays.toString()`, 중첩 배열은 `Arrays.deepToString()`으로 봐야 실제 내용이 드러난다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java array debug printing basics basics, java array debug printing basics beginner, java array debug printing basics intro, java basics, beginner java, 처음 배우는데 java array debug printing basics, java array debug printing basics 입문, java array debug printing basics 기초, what is java array debug printing basics, how to java array debug printing basics
> 관련 문서:
> - [Language README](../README.md)
> - [자바 언어의 구조와 기본 문법](./java-language-basics.md)
> - [Java `Arrays` 메서드 선택 30초 카드](./java-arrays-method-choice-30-second-card.md)
> - [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [Java Array Equality Basics](./java-array-equality-basics.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

> retrieval-anchor-keywords: java array debug printing basics, java array printing basics, java array print weird output, java array reference-like output, java array default toString, java array `Arrays.toString`, java array `Arrays.deepToString`, java nested array printing, java 2d array printing, java multidimensional array printing, java array debug output, java array log output, java array string concatenation weird output, java `[I@` output meaning, java `[Ljava.lang.String;@` output meaning, java array memory address confusion, java `Arrays.toString` vs `Arrays.deepToString`, java beginner array debugging, java array weird output next step, java array debug vs equality vs copy, java array print compare copy branch, 배열 출력 이상함 다음 문서, 배열 출력 비교 복사 구분

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 결론](#먼저-결론)
- [30초 선택표: 출력 문제인지, 비교 문제인지, 복사 문제인지](#30초-선택표-출력-문제인지-비교-문제인지-복사-문제인지)
- [왜 배열을 그냥 출력하면 이상한 문자열이 보일까](#왜-배열을-그냥-출력하면-이상한-문자열이-보일까)
- [1차원 배열 출력](#1차원-배열-출력)
- [중첩 배열 출력](#중첩-배열-출력)
- [초보자가 자주 헷갈리는 출력 함정](#초보자가-자주-헷갈리는-출력-함정)
- [코드로 한 번에 보기](#코드로-한-번에-보기)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문자가 배열을 디버깅할 때 가장 자주 만나는 당황 포인트는 출력 결과가 기대와 다르다는 점이다.

- `System.out.println(numbers)`를 했는데 왜 `[I@6d06d69c` 같은 문자열이 보일까?
- `String[][]`를 찍었더니 왜 `[[Ljava.lang.String;@...` 같은 값이 나올까?
- `Arrays.toString()`을 썼는데 2차원 배열은 왜 여전히 이상하게 보일까?
- `Arrays.deepToString()`은 언제 써야 할까?

핵심은 간단하다.

- 배열 변수 자체를 그냥 출력하면 배열 객체의 기본 `toString()` 모양이 나온다
- 1차원 배열 내용은 `Arrays.toString()`으로 본다
- 배열 안에 배열이 들어 있으면 `Arrays.deepToString()`으로 본다

이 문서는 위 규칙을 디버깅 관점에서 바로 쓸 수 있게 정리한다.

## 먼저 결론

| 상황 | 가장 먼저 떠올릴 도구 | 예시 | 기대 결과 |
|---|---|---|---|
| 배열 자체를 그냥 출력하고 있다 | 피하기 | `System.out.println(numbers)` | reference-like 문자열이 보일 수 있음 |
| 1차원 배열 내용을 보고 싶다 | `Arrays.toString()` | `Arrays.toString(numbers)` | `[1, 2, 3]` |
| 2차원 이상 배열이나 배열 안의 배열을 보고 싶다 | `Arrays.deepToString()` | `Arrays.deepToString(board)` | `[[O, X], [X, O]]` |
| 문자열과 함께 디버그 로그를 찍고 싶다 | 변환 후 붙이기 | `"numbers=" + Arrays.toString(numbers)` | `numbers=[1, 2, 3]` |

초보자용 규칙으로 외우면 다음이 가장 안전하다.

- 배열을 그대로 `println`하지 않기
- 1차원 배열이면 `Arrays.toString()`
- 중첩 배열이면 `Arrays.deepToString()`

## 30초 선택표: 출력 문제인지, 비교 문제인지, 복사 문제인지

배열에서 막혔을 때는 "지금 내가 헷갈리는 축이 무엇인가?"를 먼저 나누는 편이 빠르다.

| 지금 보이는 증상 | 먼저 확인할 질문 | 지금 읽을 문서 |
|---|---|---|
| `System.out.println(array)` 결과가 `[I@...`, `[[Ljava.lang.String;@...`처럼 이상하다 | "배열 내용을 잘못 출력한 건가?" | 이 문서 |
| 출력해 보면 값은 같아 보이는데 `==`, `array.equals(...)`가 `false`다 | "출력 문제가 아니라 비교 규칙 문제인가?" | [Java Array Equality Basics](./java-array-equality-basics.md) |
| `copied = original` 뒤에 한쪽을 바꾸니 다른 쪽도 같이 바뀐다 | "비교 문제가 아니라 같은 배열을 공유한 건가?" | [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md) |
| 2차원 배열을 `Arrays.toString()`으로 찍었더니 안쪽 row가 또 이상하다 | "중첩 배열이라 `deepToString()`이 필요한가?" | 이 문서 |

짧게 구분하면 이렇다.

- 출력이 이상하다: debug printing 문제다.
- 값 비교가 기대와 다르다: equality 문제다.
- 수정이 같이 전파된다: copy/alias 문제다.

즉 `[I@...`를 본 순간 바로 `==`나 `clone()`으로 가지 말고, 먼저 "출력 경로가 잘못됐나?"를 확인하면 된다.

## 왜 배열을 그냥 출력하면 이상한 문자열이 보일까

배열도 객체다. 그런데 배열은 사람이 읽기 좋은 형태로 `toString()`을 오버라이드하지 않는다.
그래서 배열 변수를 그대로 출력하면 `Object.toString()` 계열의 문자열이 보인다.

```java
int[] numbers = {1, 2, 3};
String[] names = {"A", "B"};

System.out.println(numbers); // [I@6d06d69c 같은 형태
System.out.println(names);   // [Ljava.lang.String;@7852e922 같은 형태
```

이 출력은 보통 세 부분으로 읽으면 된다.

- 앞의 `[`는 "배열"이라는 뜻이다
- 그 뒤의 `I`, `Ljava.lang.String;` 같은 부분은 원소 타입 힌트다
- `@` 뒤의 16진수 모양은 identity-style 문자열 일부다

여기서 중요한 점은 두 가지다.

- 이 값은 배열 내용이 아니다
- `@` 뒤 문자열은 실제 메모리 주소라고 보장되지 않는다

즉 `[I@...`나 `[Ljava.lang.String;@...`가 보이면 "배열 내용을 잘못 찍고 있구나"라고 바로 떠올리면 된다.

## 1차원 배열 출력

1차원 배열은 `Arrays.toString()`이 기본 도구다.

```java
import java.util.Arrays;

int[] numbers = {1, 2, 3};
String[] names = {"A", "B"};

System.out.println(Arrays.toString(numbers)); // [1, 2, 3]
System.out.println(Arrays.toString(names));   // [A, B]
```

디버깅에서는 문자열과 붙일 때도 같은 규칙을 쓴다.

```java
System.out.println("numbers=" + Arrays.toString(numbers));
// numbers=[1, 2, 3]
```

반대로 배열을 그대로 더하면 다시 기본 `toString()`이 나온다.

```java
System.out.println("numbers=" + numbers);
// numbers=[I@6d06d69c 같은 형태
```

즉 디버깅에서 배열을 로그에 실을 때는 "배열을 먼저 문자열로 바꾼다"가 기본 습관이다.

## 중첩 배열 출력

2차원 이상 배열은 사실 "배열 안에 배열"이다.
그래서 `Arrays.toString()`만 쓰면 바깥 배열만 적당히 보이고, 안쪽 row는 다시 배열 객체처럼 찍힌다.

```java
import java.util.Arrays;

String[][] board = {
        {"O", "X"},
        {"X", "O"}
};

System.out.println(Arrays.toString(board));
// [[Ljava.lang.String;@..., [Ljava.lang.String;@...]

System.out.println(Arrays.deepToString(board));
// [[O, X], [X, O]]
```

왜 이런 차이가 날까?

- `Arrays.toString(board)`는 바깥 배열의 각 원소를 한 번만 문자열로 바꾼다
- 그런데 바깥 배열의 각 원소는 `String[]` row다
- row를 다시 문자열로 바꾸는 순간 row의 기본 `toString()`이 보인다

반면 `Arrays.deepToString()`은 원소가 다시 배열이면 안쪽까지 내려가서 출력한다.
그래서 중첩 구조를 사람이 읽기 쉬운 형태로 확인할 수 있다.

중첩된 primitive 배열도 같은 감각으로 보면 된다.

```java
int[][] matrix = {
        {1, 2},
        {3, 4}
};

System.out.println(Arrays.deepToString(matrix)); // [[1, 2], [3, 4]]
```

## 초보자가 자주 헷갈리는 출력 함정

### 1. `Arrays.toString()`이면 모든 배열이 해결된다고 생각한다

`Arrays.toString()`은 1차원 배열에는 맞지만, 2차원 배열에서는 row가 여전히 이상한 문자열로 보일 수 있다.

- `int[]`, `String[]` 같은 1차원 배열: `Arrays.toString()`
- `int[][]`, `String[][]` 같은 중첩 배열: `Arrays.deepToString()`

### 2. `Arrays.deepToString()`을 1차원 primitive 배열에도 직접 쓰려 한다

```java
int[] numbers = {1, 2, 3};

// Arrays.deepToString(numbers); // 컴파일되지 않음
System.out.println(Arrays.toString(numbers));   // [1, 2, 3]
```

`Arrays.deepToString()`은 `Object[]` 계열에 맞는 도구다.
평범한 `int[]`, `long[]`, `double[]` 같은 1차원 primitive 배열은 계속 `Arrays.toString()`을 써야 한다.

### 3. `@` 뒤 숫자를 메모리 주소라고 단정한다

배열 기본 출력은 "identity-style 문자열"로 이해하는 편이 안전하다.
실제 메모리 주소를 믿고 해석하는 습관은 버리는 편이 낫다.

### 4. `char[]`가 예외처럼 보여 규칙을 잘못 일반화한다

```java
char[] letters = {'J', 'a', 'v', 'a'};

System.out.println(letters); // Java
```

이건 `PrintStream`에 `char[]` 전용 출력 경로가 있어서 생기는 예외처럼 보면 된다.
`int[]`, `String[]`, `String[][]`에도 같은 기대를 하면 다시 혼란이 생긴다.

### 5. 출력이 같아 보이면 비교나 복사도 문제없다고 생각한다

이건 서로 다른 축이다.

| 보고 싶은 것 | 질문 | 대표 도구 |
|---|---|---|
| 현재 내용이 무엇인가 | "지금 배열 안에 뭐가 들어 있지?" | `Arrays.toString()`, `Arrays.deepToString()` |
| 값이 같은가 | "두 배열 내용이 같은가?" | `Arrays.equals()`, `Arrays.deepEquals()` |
| 서로 독립적인가 | "한쪽을 바꿔도 다른 쪽이 안 바뀌는가?" | `clone()`, `Arrays.copyOf()`, 필요하면 row별 복사 |

예를 들어 `Arrays.toString(a)`와 `Arrays.toString(b)`가 둘 다 `[1, 2, 3]`으로 보이더라도:

- `a == b`는 `false`일 수 있다
- `Arrays.equals(a, b)`는 `true`일 수 있다
- `b = a`였다면 한쪽 수정이 다른 쪽에 같이 반영될 수 있다

그래서 "출력", "비교", "복사"를 한 문제로 섞지 않는 습관이 중요하다.

## 코드로 한 번에 보기

```java
import java.util.Arrays;

public class ArrayDebugPrintingExample {
    public static void main(String[] args) {
        int[] numbers = {1, 2, 3};
        String[][] board = {
                {"O", "X"},
                {"X", "O"}
        };
        Object[] mixed = {
                new int[]{1, 2},
                new String[]{"A", "B"}
        };

        System.out.println(numbers); // [I@... 같은 형태
        System.out.println("numbers=" + numbers); // numbers=[I@... 같은 형태
        System.out.println(Arrays.toString(numbers)); // [1, 2, 3]

        System.out.println(board); // [[Ljava.lang.String;@... 같은 형태
        System.out.println(Arrays.toString(board)); // [[Ljava.lang.String;@..., [Ljava.lang.String;@...]
        System.out.println(Arrays.deepToString(board)); // [[O, X], [X, O]]

        System.out.println(Arrays.deepToString(mixed)); // [[1, 2], [A, B]]
    }
}
```

이 예제에서 확인할 포인트는 네 가지다.

- 배열 자체를 그냥 출력하면 내용이 아니라 reference-like 문자열이 보일 수 있다
- 1차원 배열 디버깅은 `Arrays.toString()`이 기본이다
- 중첩 배열 디버깅은 `Arrays.deepToString()`이 기본이다
- `"prefix=" + array`도 결국 배열 기본 출력과 같은 함정에 걸린다

## 빠른 체크리스트

- `System.out.println(array)`가 보이면 먼저 의심하기
- 배열을 문자열과 바로 더하지 않기
- 1차원 배열은 `Arrays.toString()`
- 2차원 이상 배열은 `Arrays.deepToString()`
- `[I@...`, `[Ljava.lang.String;@...`는 배열 내용이 아니라 기본 출력 형태라고 기억하기
- nested array 출력이 이상하면 `Arrays.toString()` 대신 `Arrays.deepToString()`인지 확인하기

## 어떤 문서를 다음에 읽으면 좋은가

- "`출력은 확인했는데 값 비교가 왜 다르지?`"로 넘어가면 [Java Array Equality Basics](./java-array-equality-basics.md)
- "`한쪽만 바꿨는데 왜 둘 다 바뀌지?`"로 넘어가면 [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
- 배열 비교까지 함께 정리하려면 [Java Array Equality Basics](./java-array-equality-basics.md)
- 참조형과 객체 identity 감각을 먼저 넓히려면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- 배열과 참조형의 기본 구조를 다시 다지고 싶다면 [자바 언어의 구조와 기본 문법](./java-language-basics.md)
- aliasing, 얕은 복사, 깊은 복사 감각으로 이어 가려면 [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

## 한 줄 정리

Java에서 배열을 디버깅할 때 배열 자체를 그냥 출력하면 reference-like 문자열이 보일 수 있으니, 1차원 배열은 `Arrays.toString()`, 중첩 배열은 `Arrays.deepToString()`으로 내용을 확인해야 한다.
