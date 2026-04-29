# Java Array Copy and Clone Basics

> 한 줄 요약: 배열 변수 대입은 copy가 아니라 alias를 만들고, `clone()`과 `Arrays.copyOf()`는 새 바깥 배열을 만들지만 중첩 배열에서는 둘 다 shallow copy라서 안쪽 배열은 공유한다.

**난이도: 🟢 Beginner**


관련 문서:

- [Language README](../README.md)
- [자바 언어의 구조와 기본 문법](./java-language-basics.md)
- [Java parameter 전달, pass-by-value, side effect 입문](./java-parameter-passing-pass-by-value-side-effects-primer.md)
- [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)
- [Java `Arrays` 메서드 선택 30초 카드](./java-arrays-method-choice-30-second-card.md)
- [Java 배열 입문 공통 confusion 체크리스트](./java-array-common-confusion-checklist.md)
- [Java Array Equality Basics](./java-array-equality-basics.md)
- [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
- [배열 vs `List` 변환 엔트리 프라이머](./array-to-list-conversion-entrypoint-primer.md)

retrieval-anchor-keywords: java array copy basics, java array clone basics, java arrays.copyof vs clone, java array assignment alias, java shallow copy deep copy, java array alias vs equality symptom, same value but false vs changed together array, 배열 대입 복사 차이, 배열 복사 처음 배우는데, clone 과 copyof 차이 기초, 왜 clone해도 같이 바뀌나요, 배열 한쪽 바꾸면 다른 쪽도 같이 바뀜, 배열 값은 같은데 false, 배열 == equals false 인데 복사 문제인가, java nested array shallow copy

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 자를 것: "값은 같은데 false"와 "같이 바뀐다"를 같은 문제로 읽지 않는다](#먼저-자를-것-값은-같은데-false와-같이-바뀐다를-같은-문제로-읽지-않는다)
- [먼저 결론: 대입 vs `clone()` vs `Arrays.copyOf()`](#먼저-결론-대입-vs-clone-vs-arrayscopyof)
- [배열 변수 대입은 복사가 아니다](#배열-변수-대입은-복사가-아니다)
- [`clone()`은 같은 길이의 새 배열을 만든다](#clone은-같은-길이의-새-배열을-만든다)
- [`Arrays.copyOf()`는 복사와 길이 조절을 함께 한다](#arrayscopyof는-복사와-길이-조절을-함께-한다)
- [중첩 배열에서는 왜 shallow copy가 될까](#중첩-배열에서는-왜-shallow-copy가-될까)
- [중첩 배열 deep copy는 단계별로 직접 만든다](#중첩-배열-deep-copy는-단계별로-직접-만든다)
- [초보자가 자주 하는 실수](#초보자가-자주-하는-실수)
- [코드로 한 번에 보기](#코드로-한-번에-보기)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문자가 배열을 다루다가 자주 헷갈리는 질문은 대체로 비슷하다.

- `copied = original`을 했는데 왜 원본까지 같이 바뀔까?
- `clone()`과 `Arrays.copyOf()`는 무엇이 다를까?
- `int[][]`를 복사했는데 왜 안쪽 row가 같이 바뀔까?
- shallow copy와 deep copy는 배열에서 어디까지를 뜻할까?
- 값은 같은데 `==`나 `array.equals(...)`가 `false`다와, 한쪽을 바꾸면 다른 쪽도 같이 바뀐다는 증상을 같은 문제로 읽고 있지는 않을까?

핵심은 간단하다.

- 배열 변수 대입은 새 배열을 만들지 않는다
- `clone()`과 `Arrays.copyOf()`는 새 바깥 배열을 만든다
- 하지만 2차원 이상 배열은 "배열 안에 배열"이기 때문에, 바깥 배열만 복사하면 안쪽 배열은 여전히 공유된다

배열 초보자가 자주 빠지는 함정도 하나 더 있다.

- "`Arrays.equals()`가 이상한가?"라고 생각했는데, 실제 첫 증상은 "값은 같은데 `==`나 `array.equals(...)`가 `false`다"가 아니라 "한쪽을 바꾸면 다른 쪽도 같이 바뀐다"였을 수 있다

이 문서는 그 차이를 초보자 관점에서 한 번에 정리한다.

## 먼저 자를 것: "값은 같은데 false"와 "같이 바뀐다"를 같은 문제로 읽지 않는다

"값은 같은데 `==`나 `array.equals(...)`가 `false`다"와 "한쪽을 바꾸면 다른 쪽도 같이 바뀐다"는 비슷해 보여도 출발 축이 다르다.
앞은 비교 축이고, 뒤는 alias/copy 축이다.

특히 아래처럼 읽으면 덜 헷갈린다.

| 지금 보이는 증상 | 실제로 먼저 의심할 것 | 첫 확인 | 다음 문서 |
|---|---|---|---|
| `[I@...`처럼 출력이 이상하거나, 2차원 배열 로그가 `[[Ljava...`처럼 보인다 | 복사 문제가 아니라 출력 경로 문제 | 1차원은 `Arrays.toString(...)`, 중첩 배열은 `Arrays.deepToString(...)` | [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md) |
| 값은 같은데 `==`나 `array.equals(...)`가 `false`다 | 같은 배열인지, 같은 값인지 | 1차원은 `Arrays.equals()`, 중첩 배열은 `Arrays.deepEquals()` | [Java Array Equality Basics](./java-array-equality-basics.md) |
| `left == right`가 `true`고 한쪽 수정이 다른 쪽에도 바로 보인다 | 비교 실패가 아니라 같은 배열 alias | `left == right`와 수정 전후 출력 함께 보기 | 이 문서 |
| 값이 달라진 이유를 `equals()` 탓으로 돌리고 싶은데, 변경이 양쪽에 동시에 퍼진다 | shared reference가 먼저 생겼는지 | `copied = original` 같은 대입이 있었는지 찾기 | 이 문서 |

짧게 외우면 이렇다.

- 값은 같은데 `==`나 `array.equals(...)`가 `false`다면 equality 도구를 먼저 본다
- 한쪽을 바꾸면 다른 쪽도 같이 바뀌면 alias/shared reference를 먼저 본다
- 출력이 이상하면 copy보다 출력 경로를 먼저 자른다

즉 "값은 같은데 `==`나 `array.equals(...)`가 `false`다"와 "한쪽을 바꾸면 다른 쪽도 같이 바뀐다"는 비슷해 보여도 출발 문서가 다르다.
앞은 [Java Array Equality Basics](./java-array-equality-basics.md), 뒤는 이 문서다.

먼저 축을 나누면 더 빠르다.

- 아직 "공유 문제인지 비교 문제인지"부터 헷갈리면 [Java 배열 입문 공통 confusion 체크리스트](./java-array-common-confusion-checklist.md)를 먼저 본다.
- `[I@...`처럼 출력이 이상하면 복사보다 [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)를 먼저 본다.
- 값은 비슷해 보이는데 `==`나 `equals()` 결과가 기대와 다르면 복사보다 [Java Array Equality Basics](./java-array-equality-basics.md) 쪽이 더 가깝다.
- "한쪽 수정이 다른 쪽에도 전파된다"가 핵심 증상이면 이 문서가 맞다.

## 먼저 결론: 대입 vs `clone()` vs `Arrays.copyOf()`

| 표현 | 새 바깥 배열을 만드나 | 길이를 바꿀 수 있나 | 중첩 배열의 안쪽 row는 공유하나 | 언제 가장 먼저 떠올리면 좋은가 |
|---|---|---|---|---|
| `copied = original` | 아니오 | 아니오 | 예 | alias만 만들고 싶을 때 |
| `original.clone()` | 예 | 아니오 | 예 | 같은 길이로 바로 복사할 때 |
| `Arrays.copyOf(original, n)` | 예 | 예 | 예 | 복사하면서 길이도 줄이거나 늘릴 때 |

초보자용 규칙으로는 다음처럼 외우면 된다.

- `=`는 copy가 아니라 "같은 배열을 함께 가리키기"다
- 같은 길이의 새 배열이 필요하면 `clone()` 또는 `Arrays.copyOf(array, array.length)`
- 길이를 조절하면서 복사하려면 `Arrays.copyOf()`
- 중첩 배열에서는 `clone()`과 `Arrays.copyOf()` 둘 다 shallow copy다

## 배열 변수 대입은 복사가 아니다

배열은 참조형이므로, 변수에 다른 배열 변수를 대입하면 새 배열이 생기지 않는다.

```java
int[] original = {1, 2, 3};
int[] assigned = original;

assigned[0] = 99;

System.out.println(original[0]); // 99
System.out.println(assigned[0]); // 99
System.out.println(original == assigned); // true
```

여기서 `assigned`는 복사본이 아니라 `original`의 alias다.
즉 두 변수가 같은 배열 객체를 가리킨다.

이 규칙은 1차원, 2차원, 객체 배열 모두 똑같다.
복사본이 필요하다면 `clone()`이나 `Arrays.copyOf()` 같은 명시적 복사 도구를 써야 한다.

## `clone()`은 같은 길이의 새 배열을 만든다

배열의 `clone()`은 같은 길이의 새 배열을 만들고, 바깥 배열의 각 칸을 그대로 복사한다.

```java
int[] original = {1, 2, 3};
int[] cloned = original.clone();

cloned[0] = 99;

System.out.println(original[0]); // 1
System.out.println(cloned[0]);   // 99
System.out.println(original == cloned); // false
```

이 경우 `original`과 `cloned`는 서로 다른 배열이다.
그래서 `int[]` 같은 1차원 primitive 배열에서는 흔히 기대하는 "독립된 복사본"처럼 보인다.

하지만 `clone()`이 복사하는 것은 바깥 배열의 칸이다.
칸 안에 들어 있는 값이 다시 참조형이면, 그 참조 자체를 복사할 뿐이다.

즉 `String[]`, `Member[]`, `int[][]` 같은 경우에는 "배열 칸"은 새로 생겨도, 안쪽 객체나 안쪽 배열은 공유될 수 있다.

## `Arrays.copyOf()`는 복사와 길이 조절을 함께 한다

`Arrays.copyOf()`는 새 배열을 만들면서 길이도 바꿀 수 있다는 점이 `clone()`과 가장 큰 차이다.

```java
import java.util.Arrays;

int[] original = {10, 20, 30};

int[] sameSize = Arrays.copyOf(original, original.length);
int[] shorter = Arrays.copyOf(original, 2);
int[] longer = Arrays.copyOf(original, 5);

System.out.println(Arrays.toString(sameSize)); // [10, 20, 30]
System.out.println(Arrays.toString(shorter));  // [10, 20]
System.out.println(Arrays.toString(longer));   // [10, 20, 30, 0, 0]
```

길이를 늘리면 남는 칸은 기본값으로 채워진다.

- `int[]`는 `0`
- `boolean[]`는 `false`
- 참조형 배열은 `null`

즉 `Arrays.copyOf()`는 다음 상황에서 특히 편하다.

- 같은 길이로 복사하고 싶다
- 앞부분만 잘라서 복사하고 싶다
- 더 큰 배열을 만들고 기존 값을 옮기고 싶다

다만 중요한 점은 `Arrays.copyOf()`도 중첩 배열에서는 shallow copy라는 것이다.
바깥 배열은 새로 생기지만 안쪽 배열까지 자동으로 복제되지는 않는다.

## 중첩 배열에서는 왜 shallow copy가 될까

2차원 배열은 "표"처럼 보이지만, Java 관점에서는 사실 "배열 안에 배열"이다.

```java
int[][] original = {
        {1, 2},
        {3, 4}
};

int[][] shallow = original.clone();

System.out.println(original == shallow);     // false
System.out.println(original[0] == shallow[0]); // true
```

여기서 바깥 배열은 달라졌지만, 첫 번째 row는 같은 배열을 함께 가리킨다.
그래서 안쪽 row를 수정하면 원본도 영향을 받는다.

```java
shallow[0][0] = 99;

System.out.println(original[0][0]); // 99
```

반대로 row 자체를 다른 배열로 바꿔 끼우면 그때는 바깥 배열이 이미 분리되어 있으므로 원본 row 참조는 유지된다.

```java
shallow[0] = new int[]{7, 7};

System.out.println(original[0][0]); // 99
System.out.println(shallow[0][0]);  // 7
```

이 감각을 한 줄로 요약하면 다음과 같다.

- 바깥 배열은 복사되었다
- 안쪽 배열은 아직 공유 중이다

이것이 중첩 배열에서 말하는 shallow copy다.

## 중첩 배열 deep copy는 단계별로 직접 만든다

중첩 배열을 truly independent하게 만들려면 안쪽 배열도 하나씩 복사해야 한다.

```java
int[][] original = {
        {1, 2},
        {3, 4}
};

int[][] deep = new int[original.length][];
for (int i = 0; i < original.length; i++) {
    deep[i] = original[i].clone();
}

deep[0][0] = 99;

System.out.println(original[0][0]); // 1
System.out.println(deep[0][0]);     // 99
```

이 경우에는 바깥 배열과 안쪽 row 배열까지 각각 새로 만들어서 `int[][]` 기준으로는 deep copy가 된다.

하지만 여기에도 한 단계 더 생각할 점이 있다.
만약 `Member[][]`처럼 안쪽 row 안에 가변 객체가 들어 있다면, row만 복사해도 `Member` 객체 참조는 여전히 공유된다.

즉 deep copy는 "무조건 한 번에 되는 마법 API"가 아니라, **어디까지 독립시킬지 구조를 보고 직접 정하는 작업**이다.

- `int[][]`처럼 row 안이 primitive라면 row 복사까지로 충분할 수 있다
- `Member[][]`처럼 가변 객체가 들어 있으면 요소 객체까지 새로 만들어야 완전한 deep copy가 된다

## 초보자가 자주 하는 실수

### 1. `copied = original`을 복사라고 생각한다

```java
int[] copied = original;
```

이 코드는 새 배열을 만들지 않는다.
복사본이 아니라 alias다.

### 2. `clone()`을 중첩 배열 deep copy라고 생각한다

```java
int[][] cloned = original.clone();
```

이 코드는 바깥 배열만 새로 만든다.
안쪽 row는 그대로 공유한다.

### 3. `Arrays.copyOf()`면 안쪽 배열까지 자동으로 복사된다고 생각한다

`Arrays.copyOf(matrix, matrix.length)`도 `clone()`과 같은 수준의 shallow copy다.
중첩 구조를 완전히 분리하려면 row를 따로 복사해야 한다.

### 4. 길이를 늘린 `Arrays.copyOf()`의 빈 칸이 쓰레기 값일 거라고 생각한다

Java 배열은 기본값으로 채워진다.

- `int[]`는 `0`
- `double[]`는 `0.0`
- `boolean[]`는 `false`
- `String[]` 같은 참조형은 `null`

## 코드로 한 번에 보기

```java
import java.util.Arrays;

public class ArrayCopyExample {
    public static void main(String[] args) {
        int[] original = {1, 2, 3};
        int[] assigned = original;
        int[] cloned = original.clone();
        int[] copied = Arrays.copyOf(original, original.length);

        assigned[0] = 10;
        cloned[1] = 20;
        copied[2] = 30;

        System.out.println(Arrays.toString(original)); // [10, 2, 3]
        System.out.println(Arrays.toString(assigned)); // [10, 2, 3]
        System.out.println(Arrays.toString(cloned));   // [1, 20, 3]
        System.out.println(Arrays.toString(copied));   // [1, 2, 30]

        int[] longer = Arrays.copyOf(original, 5);
        System.out.println(Arrays.toString(longer));   // [10, 2, 3, 0, 0]

        int[][] matrix = {
                {1, 2},
                {3, 4}
        };

        int[][] shallow = matrix.clone();
        shallow[0][0] = 99;

        System.out.println(Arrays.deepToString(matrix));  // [[99, 2], [3, 4]]
        System.out.println(Arrays.deepToString(shallow)); // [[99, 2], [3, 4]]

        int[][] deep = new int[matrix.length][];
        for (int i = 0; i < matrix.length; i++) {
            deep[i] = matrix[i].clone();
        }

        deep[0][1] = 77;

        System.out.println(Arrays.deepToString(matrix)); // [[99, 2], [3, 4]]
        System.out.println(Arrays.deepToString(deep));   // [[99, 77], [3, 4]]
    }
}
```

## 이 예제에서 바로 볼 것

위 코드를 읽을 때 확인할 포인트는 다섯 가지다.

- 변수 대입은 copy가 아니라 alias다
- `clone()`은 같은 길이의 새 바깥 배열을 만든다
- `Arrays.copyOf()`는 길이를 조절하면서 새 바깥 배열을 만든다
- 중첩 배열에서 `clone()`은 shallow copy다
- nested deep copy는 row를 하나씩 복사해야 한다

## 빠른 체크리스트

- `copied = original`은 복사본이 아니라 alias다
- 같은 길이 복사면 `clone()` 또는 `Arrays.copyOf(array, array.length)`
- 길이를 줄이거나 늘리려면 `Arrays.copyOf()`
- `int[][]`, `String[][]` 같은 중첩 배열에서 `clone()`과 `Arrays.copyOf()`는 둘 다 shallow copy다
- `int[][]`를 truly independent하게 만들려면 row를 하나씩 복사한다
- 안쪽 요소가 가변 객체라면 row 복사만으로는 full deep copy가 아니다

## 어떤 문서를 다음에 읽으면 좋은가

- aliasing과 side effect 감각을 먼저 넓히려면 [Java parameter 전달, pass-by-value, side effect 입문](./java-parameter-passing-pass-by-value-side-effects-primer.md)
- 배열 비교까지 함께 정리하려면 [Java Array Equality Basics](./java-array-equality-basics.md)
- 배열을 로그로 확인하는 법까지 묶어 보려면 [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)
- 방어적 복사와 불변 설계로 확장하려면 [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

## 한 줄 정리

Java에서 `assigned = original`은 복사가 아니라 alias이고, `clone()`과 `Arrays.copyOf()`는 새 바깥 배열을 만들지만 중첩 배열에서는 안쪽 배열이나 가변 요소까지 직접 복사해야 deep copy가 된다.
