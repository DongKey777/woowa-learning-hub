# Java Array Equality Basics

> 한 줄 요약: 배열은 객체라서 `==`와 `array.equals()`가 reference identity를 보고, 값 비교는 1차원이면 `Arrays.equals()`, 중첩 배열이면 `Arrays.deepEquals()`를 써야 한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [자바 언어의 구조와 기본 문법](./java-language-basics.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)
> - [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)

> retrieval-anchor-keywords: java array equality basics, java array comparison, java array `==` vs `equals`, java array identity vs equality, java array `Arrays.equals`, java array `Arrays.deepEquals`, java 2d array comparison, java multidimensional array equality, java nested array comparison, java matrix equality, java `int[]` compare, java `String[][]` compare, java beginner array equality, java nested array equals mistake, java array alias equality confusion, java array copy clone equality confusion

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [배열 비교 규칙을 먼저 한 장으로 보기](#배열-비교-규칙을-먼저-한-장으로-보기)
- [배열에서 `==`와 `equals()`가 값 비교가 아닌 이유](#배열에서-와-equals가-값-비교가-아닌-이유)
- [1차원 배열은 `Arrays.equals()`로 비교하기](#1차원-배열은-arraysequals로-비교하기)
- [중첩 배열은 `Arrays.deepEquals()`로 비교하기](#중첩-배열은-arraysdeepequals로-비교하기)
- [중첩 배열에서 초보자가 자주 하는 실수](#중첩-배열에서-초보자가-자주-하는-실수)
- [코드로 한 번에 보기](#코드로-한-번에-보기)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

배열 비교는 Java 입문자가 자주 헷갈리는 주제다.

- `int[]` 두 개의 값이 같은데 왜 `==`는 `false`일까?
- `array.equals(other)`를 썼는데 왜 내용 비교가 안 될까?
- `String[][]` 비교에 `Arrays.equals()`를 썼는데 왜 `false`일까?
- `Arrays.deepEquals()`는 언제 쓰고, 언제 쓰면 안 될까?

핵심은 간단하다. 배열도 참조형 객체이고, 2차원 배열도 사실은 "배열 안에 배열"이다.  
그래서 기본형 비교 규칙을 그대로 가져오면 틀리고, 중첩 구조에서는 `Arrays.equals()`와 `Arrays.deepEquals()`의 역할도 나뉜다.

## 배열 비교 규칙을 먼저 한 장으로 보기

| 도구 | 실제로 묻는 질문 | 잘 맞는 경우 | 주의할 점 |
|---|---|---|---|
| `==` | 같은 배열 객체를 가리키는가 | alias인지 확인할 때 | 내용이 같아도 다른 배열이면 `false` |
| `array.equals(other)` | 배열에서는 사실상 `==`와 같다 | 거의 쓰지 않는 편이 낫다 | 배열은 `equals()`를 값 비교로 오버라이드하지 않는다 |
| `Arrays.equals(a, b)` | 1차원 배열의 각 원소가 순서대로 같은가 | `int[]`, `String[]`, `Member[]` 비교 | 원소가 다시 배열이면 그 안까지는 내려가지 않는다 |
| `Arrays.deepEquals(a, b)` | 중첩 배열 내부까지 내려가서 같은가 | `String[][]`, `int[][]`, 배열을 원소로 가진 `Object[]` 비교 | 평범한 `int[]` 같은 1차원 primitive 배열에는 직접 쓸 수 없다 |

초보자용 규칙으로는 다음처럼 외우면 된다.

- "같은 배열 객체냐?"를 묻는 경우만 `==`
- 1차원 배열 내용 비교는 `Arrays.equals()`
- 2차원 이상이거나 배열 안에 배열이 들어 있으면 `Arrays.deepEquals()`

## 배열에서 `==`와 `equals()`가 값 비교가 아닌 이유

배열은 참조형이다. 그래서 `==`는 "같은 메모리의 같은 배열 객체를 보고 있는가"를 비교한다.

```java
int[] first = {1, 2, 3};
int[] second = {1, 2, 3};
int[] alias = first;

System.out.println(first == second); // false
System.out.println(first == alias);  // true
```

`first`와 `second`는 값은 같지만 서로 다른 배열 객체다.  
반면 `alias`는 `first`와 같은 배열을 가리키므로 `true`다.

배열의 `equals()`도 함정이다.

```java
System.out.println(first.equals(second)); // false
```

배열은 `Object.equals()`를 값 비교용으로 오버라이드하지 않는다.  
그래서 `array.equals(other)`는 초보자 관점에서 사실상 `==`와 같은 함정이라고 봐도 된다.

## 1차원 배열은 `Arrays.equals()`로 비교하기

`Arrays.equals()`는 1차원 배열의 값을 비교할 때 가장 먼저 떠올리면 되는 기본 도구다.

```java
import java.util.Arrays;

int[] numbers1 = {1, 2, 3};
int[] numbers2 = {1, 2, 3};

System.out.println(Arrays.equals(numbers1, numbers2)); // true
```

이 메서드는 다음을 순서대로 본다.

1. 둘 다 `null`인지
2. 길이가 같은지
3. 같은 인덱스의 원소가 순서대로 같은지

따라서 이런 경우에 잘 맞는다.

- `int[]`, `long[]`, `double[]` 같은 1차원 primitive 배열
- `String[]`, `Integer[]`, 사용자 정의 객체 배열 같은 1차원 참조형 배열

예를 들어 `String[]`는 각 원소가 `String`이므로, 원소 비교 단계에서 `String.equals()`가 동작해 내용 비교가 된다.

```java
String[] left = {"A", "B"};
String[] right = {"A", "B"};

System.out.println(Arrays.equals(left, right)); // true
```

하지만 여기서 중요한 제한이 하나 있다.  
원소가 다시 배열이면, `Arrays.equals()`는 그 안으로 재귀적으로 들어가지 않는다.

## 중첩 배열은 `Arrays.deepEquals()`로 비교하기

`Arrays.deepEquals()`는 "배열 안에 배열"이 있는 중첩 구조를 비교할 때 쓴다.

```java
import java.util.Arrays;

String[][] board1 = {
        {"O", "X"},
        {"X", "O"}
};
String[][] board2 = {
        {"O", "X"},
        {"X", "O"}
};

System.out.println(Arrays.deepEquals(board1, board2)); // true
```

이 메서드는 바깥 배열의 원소를 보다가 그 원소도 배열이면 안쪽으로 더 내려가서 비교한다.  
그래서 다음 같은 구조에 잘 맞는다.

- `String[][]`, `String[][][]`
- `int[][]`, `long[][]`
- 배열을 원소로 담고 있는 `Object[]`

예를 들어 primitive 배열이 안쪽에 중첩된 경우도 처리할 수 있다.

```java
Object[] mixed1 = {new int[]{1, 2}, new String[]{"A", "B"}};
Object[] mixed2 = {new int[]{1, 2}, new String[]{"A", "B"}};

System.out.println(Arrays.deepEquals(mixed1, mixed2)); // true
```

다만 plain `int[]`처럼 1차원 primitive 배열은 `Arrays.deepEquals()`에 직접 넘길 수 없다.  
이 경우는 계속 `Arrays.equals(int[], int[])` 같은 1차원 전용 오버로드를 써야 한다.

## 중첩 배열에서 초보자가 자주 하는 실수

### 1. 2차원 배열도 `Arrays.equals()`면 충분하다고 생각한다

```java
String[][] left = {
        {"A", "B"},
        {"C"}
};
String[][] right = {
        {"A", "B"},
        {"C"}
};

System.out.println(Arrays.equals(left, right)); // false
```

이유는 바깥 배열의 각 원소가 `String[]`이기 때문이다.  
`Arrays.equals()`는 각 row를 다시 `String[]` 배열 객체로 보고 비교하므로, row reference가 다르면 `false`가 된다.

### 2. `array.equals(other)`가 값 비교라고 착각한다

```java
int[] left = {1, 2};
int[] right = {1, 2};

System.out.println(left.equals(right)); // false
```

배열의 `equals()`는 초보자가 기대하는 값 비교가 아니다.  
배열 내용 비교는 `Arrays.equals()` 또는 `Arrays.deepEquals()`로 의도를 분명히 드러내는 편이 안전하다.

### 3. `Arrays.deepEquals()`를 모든 배열 비교의 만능 도구로 생각한다

```java
int[] left = {1, 2};
int[] right = {1, 2};

// Arrays.deepEquals(left, right); // 컴파일되지 않음
System.out.println(Arrays.equals(left, right)); // true
```

1차원 primitive 배열은 `Object[]`가 아니므로 `deepEquals()` 대상이 아니다.  
깊게 내려갈 구조가 없는 평범한 `int[]`, `long[]`, `double[]`는 `Arrays.equals()`가 맞다.

### 4. 중첩 배열에서는 "원소만 같으면 순서는 상관없다"고 생각한다

배열 비교는 둘 다 순서 민감하다.

- 길이가 다르면 다르다.
- 같은 원소라도 순서가 다르면 다르다.
- jagged array라면 row 길이 차이도 그대로 비교 결과에 반영된다.

즉 `Arrays.deepEquals()`는 "중첩 구조를 재귀적으로 비교"할 뿐이고, 집합처럼 순서를 무시하지는 않는다.

## 코드로 한 번에 보기

```java
import java.util.Arrays;

public class ArrayEqualityExample {
    public static void main(String[] args) {
        int[] numbers1 = {1, 2, 3};
        int[] numbers2 = {1, 2, 3};
        int[] alias = numbers1;

        System.out.println(numbers1 == numbers2);      // false
        System.out.println(numbers1 == alias);         // true
        System.out.println(numbers1.equals(numbers2)); // false
        System.out.println(Arrays.equals(numbers1, numbers2)); // true

        String[][] board1 = {
                {"O", "X"},
                {"X", "O"}
        };
        String[][] board2 = {
                {"O", "X"},
                {"X", "O"}
        };

        System.out.println(Arrays.equals(board1, board2));     // false
        System.out.println(Arrays.deepEquals(board1, board2)); // true

        Object[] mixed1 = {new int[]{1, 2}, new String[]{"A", "B"}};
        Object[] mixed2 = {new int[]{1, 2}, new String[]{"A", "B"}};

        System.out.println(Arrays.deepEquals(mixed1, mixed2)); // true
    }
}
```

이 예제에서 확인할 포인트는 네 가지다.

- 배열의 `==`는 reference identity 비교다.
- 배열의 `equals()`는 값 비교가 아니다.
- 1차원 배열 내용 비교는 `Arrays.equals()`다.
- 중첩 배열 내용 비교는 `Arrays.deepEquals()`다.

## 빠른 체크리스트

- 같은 배열 객체인지 확인할 때만 `==`
- 배열 내용 비교에 `array.equals(other)`는 쓰지 않기
- `int[]`, `String[]`, `Member[]` 같은 1차원 배열은 `Arrays.equals()`
- `int[][]`, `String[][]`, 배열을 원소로 가진 `Object[]`는 `Arrays.deepEquals()`
- `Arrays.equals()`와 `Arrays.deepEquals()`는 둘 다 순서와 길이에 민감하다는 점 기억하기
- 1차원 primitive 배열에 `Arrays.deepEquals()`를 억지로 적용하지 않기

## 어떤 문서를 다음에 읽으면 좋은가

- 배열 출력이 왜 `[I@...`처럼 보이는지부터 정리하려면 [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)
- 배열 대입과 `clone()`, `Arrays.copyOf()` 차이까지 함께 보려면 [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
- equality 기본 축부터 넓게 정리하려면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- 배열과 참조형 기초를 먼저 다시 다지고 싶다면 [자바 언어의 구조와 기본 문법](./java-language-basics.md)
- 얕은 복사와 깊은 복사 감각까지 함께 묶어 보려면 [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
- 객체 `equals()`/`hashCode()` 계약으로 확장하려면 [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)

## 한 줄 정리

Java 배열 비교에서 `==`와 `array.equals()`는 객체 동일성을 보고, 실제 값 비교는 1차원 배열이면 `Arrays.equals()`, 중첩 배열이면 `Arrays.deepEquals()`를 써야 한다.
