# Java Array Debug Printing Basics

> 한 줄 요약: 배열을 그대로 출력하면 내용이 아니라 reference-like 문자열이 보이기 쉽고, 1차원 배열은 `Arrays.toString()`, 중첩 배열은 `Arrays.deepToString()`으로 봐야 실제 값을 확인할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)
- [Java 배열 입문 공통 confusion 체크리스트](./java-array-common-confusion-checklist.md)
- [Java `Arrays` 메서드 선택 30초 카드](./java-arrays-method-choice-30-second-card.md)
- [Java Array Equality Basics](./java-array-equality-basics.md)
- [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)

retrieval-anchor-keywords: java array debug printing basics, java array print weird output, java array default tostring, java arrays.tostring when to use, java arrays.deeptostring when to use, java array [i@ output meaning, java array weird log output, java 2d array printing basics, 배열 출력 왜 이상해요, 배열 [i@ 뭐예요, 배열 출력 처음 헷갈릴 때, 배열 equals 왜 false, 배열 왜 같이 바뀌나요, what is java array debug printing, beginner java array debugging

## 핵심 개념

배열 디버깅에서 초보자가 제일 먼저 당황하는 순간은 출력이 기대와 다를 때다.

- `System.out.println(numbers)`를 했는데 `[I@...`가 나온다.
- `String[][]`를 찍었더니 `[[Ljava.lang.String;@...`처럼 보인다.
- 값은 같은데 `==`나 `array.equals(...)`가 `false`다.
- 한쪽을 바꾸면 다른 쪽도 같이 바뀐다.

여기서 먼저 잘라야 하는 질문은 하나다.

> 지금 문제는 "배열 내용을 어떻게 볼까"인가, "값은 같은데 `==`나 `array.equals(...)`가 `false`다"인가, 아니면 "한쪽을 바꾸면 다른 쪽도 같이 바뀐다"인가?

이 문서는 첫 번째 질문, 즉 **출력 경로**를 다룬다. 한 줄 규칙은 이것이면 충분하다.

- 1차원 배열 출력: `Arrays.toString(...)`
- 중첩 배열 출력: `Arrays.deepToString(...)`
- 배열을 그대로 `println`하거나 문자열과 바로 더하지 않기

## 증상으로 바로 고르기

배열에서 막히면 메서드 이름보다 증상으로 분기하는 편이 빠르다.

| 지금 보이는 증상 | 실제로 먼저 묻는 질문 | 먼저 쓸 도구 | 다음 연결 |
|---|---|---|---|
| `System.out.println(array)` 결과가 `[I@...`, `[Ljava.lang.String;@...`처럼 이상하다 | 배열 내용을 잘못 출력한 건가 | 1차원은 `Arrays.toString(...)` | 이 문서 |
| `String[][]`를 `Arrays.toString(...)`으로 찍었더니 안쪽 row가 또 이상하다 | 중첩 배열이라 안쪽까지 내려가야 하나 | `Arrays.deepToString(...)` | 이 문서 |
| 값은 같은데 `==`나 `array.equals(...)`가 `false`다 | 출력 문제가 아니라 비교 규칙 문제인가 | 1차원은 `Arrays.equals(...)`, 중첩 배열은 `Arrays.deepEquals(...)` | [Java Array Equality Basics](./java-array-equality-basics.md) |
| 한쪽을 바꾸면 다른 쪽도 같이 바뀐다 | 비교 문제가 아니라 같은 배열을 공유한 건가 | `copied == original` 확인 | [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md) |

짧게 외우면 이렇다.

- `[I@...`를 보면 출력 문제부터 의심한다.
- "값은 같은데 `==`나 `array.equals(...)`가 `false`다"가 보이면 equality 문서로 분기한다.
- "한쪽을 바꾸면 다른 쪽도 같이 바뀐다"가 보이면 copy/alias 문서로 분기한다.

## 한눈에 보기

| 하고 싶은 일 | 잘못 고르기 쉬운 코드 | 먼저 떠올릴 코드 | 결과 |
|---|---|---|---|
| 1차원 배열 내용 보기 | `System.out.println(numbers)` | `Arrays.toString(numbers)` | `[1, 2, 3]` |
| 문자열과 함께 로그 남기기 | `"numbers=" + numbers` | `"numbers=" + Arrays.toString(numbers)` | `numbers=[1, 2, 3]` |
| 2차원 배열 내용 보기 | `Arrays.toString(board)` | `Arrays.deepToString(board)` | `[[O, X], [X, O]]` |
| 값이 같은지 보기 | `numbers.equals(other)` | `Arrays.equals(numbers, other)` | `true` 또는 `false` |

즉 `toString` 계열은 **보여 주는 도구**고, `equals` 계열은 **비교 도구**다. 이 문서는 `[I@...`, `[[Ljava...`처럼 "출력이 이상하다"에 답하고, "값은 같은데 `==`나 `array.equals(...)`가 `false`다"와 "한쪽을 바꾸면 다른 쪽도 같이 바뀐다"는 각각 equality/copy 문서로 돌려보낸다.

## 왜 배열을 그대로 출력하면 이상한 문자열이 보일까

배열도 객체지만, 사람이 읽기 좋은 형태로 `toString()`을 따로 재정의하지 않는다. 그래서 배열 변수를 그대로 출력하면 `Object.toString()` 계열의 문자열이 보인다.

```java
int[] numbers = {1, 2, 3};
String[] names = {"A", "B"};

System.out.println(numbers); // [I@6d06d69c 같은 형태
System.out.println(names);   // [Ljava.lang.String;@7852e922 같은 형태
```

이 출력은 보통 이렇게 읽으면 된다.

- 앞의 `[`는 배열이라는 힌트다.
- `I`, `Ljava.lang.String;`는 원소 타입 힌트다.
- `@` 뒤 문자열은 배열 내용을 보여 주는 값이 아니다.

핵심은 단순하다. `[I@...`를 봤다고 해서 배열이 망가진 것이 아니라, **배열 내용 대신 기본 출력 경로를 본 것**이다.

## 1차원 배열과 중첩 배열 출력

### 1차원 배열

1차원 배열은 `Arrays.toString(...)`이 기본이다.

```java
import java.util.Arrays;

int[] numbers = {1, 2, 3};
String[] names = {"A", "B"};

System.out.println(Arrays.toString(numbers)); // [1, 2, 3]
System.out.println(Arrays.toString(names));   // [A, B]
System.out.println("numbers=" + Arrays.toString(numbers));
```

### 중첩 배열

2차원 이상 배열은 "배열 안에 배열"이다. 그래서 `Arrays.toString(...)`만 쓰면 바깥 배열 원소가 다시 배열 객체처럼 보일 수 있다.

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

초보자 기준에서는 다음처럼 나누면 충분하다.

- `int[]`, `String[]`: `Arrays.toString(...)`
- `int[][]`, `String[][]`, 배열을 담은 `Object[]`: `Arrays.deepToString(...)`

## 흔한 오해와 함정

### `Arrays.toString()`이면 모든 배열이 해결된다고 생각한다

1차원 배열에는 맞지만, 2차원 배열에서는 안쪽 row가 다시 이상하게 보일 수 있다. 이때는 `Arrays.deepToString(...)`으로 바꿔야 한다.

### `"prefix=" + array`도 괜찮다고 생각한다

문자열과 배열을 바로 더해도 결국 배열 기본 출력이 붙는다.

```java
int[] numbers = {1, 2, 3};

System.out.println("numbers=" + numbers);
// numbers=[I@... 같은 형태
```

로그를 남길 때도 항상 배열을 먼저 `Arrays.toString(...)` 또는 `Arrays.deepToString(...)`으로 바꿔야 한다.

### 출력이 같아 보이면 비교도 맞다고 생각한다

이건 다른 축이다.

| 보고 싶은 것 | 질문 | 대표 도구 |
|---|---|---|
| 현재 내용 확인 | 지금 배열 안에 뭐가 있지 | `Arrays.toString()`, `Arrays.deepToString()` |
| 값 비교 | 두 배열 값이 같은가 | `Arrays.equals()`, `Arrays.deepEquals()` |
| 참조 공유 확인 | 같은 배열을 같이 보고 있는가 | `==`, `clone()`, `Arrays.copyOf()` |

예를 들어 `Arrays.toString(a)`와 `Arrays.toString(b)`가 둘 다 `[1, 2, 3]`이어도 "값은 같은데 `==`나 `array.equals(...)`가 `false`다"가 나올 수 있다. 반대로 `b = a`였다면 출력이 같을 뿐 아니라 "한쪽을 바꾸면 다른 쪽도 같이 바뀐다"가 발생할 수 있다.

### `char[]` 출력이 예외처럼 보여 규칙을 일반화한다

```java
char[] letters = {'J', 'a', 'v', 'a'};

System.out.println(letters); // Java
```

이건 `char[]` 전용 출력 경로가 있어서 보이는 예외에 가깝다. `int[]`, `String[]`, `String[][]`까지 같은 방식으로 기대하면 다시 헷갈린다.

## 실무에서 쓰는 모습

배열 출력 문제는 보통 테스트 실패 로그나 디버그 로그에서 먼저 드러난다.

1. 로그에 `[I@...`가 보이면 배열 내용이 안 보이는 상태라고 판단한다.
2. 1차원이면 `Arrays.toString(...)`, 중첩 배열이면 `Arrays.deepToString(...)`으로 바꾼다.
3. 출력이 정상화된 뒤에도 "값은 같은데 `==`나 `array.equals(...)`가 `false`다"가 문제면 equality 쪽으로 분기한다.
4. 출력은 맞는데 "한쪽을 바꾸면 다른 쪽도 같이 바뀐다"가 핵심이면 copy/alias 쪽으로 분기한다.

이 순서가 중요한 이유는, 출력 문제가 해결되지 않은 상태에서는 비교 문제를 읽어도 원인이 섞여 보이기 때문이다. 먼저 눈으로 내용을 확인할 수 있어야 다음 단계 판단이 쉬워진다.

## 더 깊이 가려면

- "값은 같은데 `==`나 `array.equals(...)`가 `false`다"를 바로 이어서 정리하려면 [Java Array Equality Basics](./java-array-equality-basics.md)
- 출력/비교/복사/정렬을 한 번에 분기하고 싶으면 [Java 배열 입문 공통 confusion 체크리스트](./java-array-common-confusion-checklist.md)
- `Arrays` 계열 메서드를 증상 기준으로 다시 고르려면 [Java `Arrays` 메서드 선택 30초 카드](./java-arrays-method-choice-30-second-card.md)
- "한쪽을 바꾸면 다른 쪽도 같이 바뀐다"를 바로 이어 보려면 [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)

## 한 줄 정리

배열 디버깅에서 `[I@...` 같은 문자열이 보이면 값이 이상한 것이 아니라 출력 경로가 잘못된 것이고, 1차원은 `Arrays.toString(...)`, 중첩 배열은 `Arrays.deepToString(...)`으로 먼저 내용을 확인하면 된다.
