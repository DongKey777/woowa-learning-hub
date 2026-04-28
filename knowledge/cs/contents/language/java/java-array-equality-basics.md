# Java Array Equality Basics

> 한 줄 요약: 배열은 객체라서 `==`와 `array.equals(...)`가 같은 배열인지부터 보고, 값 비교는 1차원이면 `Arrays.equals()`, 중첩 배열이면 `Arrays.deepEquals()`로 나눠야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)
- [Java 배열 입문 공통 confusion 체크리스트](./java-array-common-confusion-checklist.md)
- [Java `Arrays` 메서드 선택 30초 카드](./java-arrays-method-choice-30-second-card.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [`HashMap`/`HashSet` 조회 흐름 브리지: `hashCode()` 다음에 왜 `equals()`를 볼까](./hashmap-hashset-hashcode-equals-lookup-bridge.md)

retrieval-anchor-keywords: java array equality basics, java array == vs arrays.equals, java array equals false why, java array same value but false, java array identity vs equality, java arrays.equals when to use, java arrays.deepequals when to use, java 2d array comparison basics, 자바 배열 비교 기초, 배열 == 값 비교 차이, 배열 equals 왜 false, 배열 비교 처음 배우는데, arrays.equals 뭐예요, arrays.deepequals 언제 써요

## 핵심 개념

배열 비교에서 초보자가 가장 자주 섞는 질문은 두 가지다.

- "같은 배열 객체인가?"
- "배열 안의 값이 같은가?"

배열은 참조형 객체라서 `==`는 기본적으로 첫 번째 질문을 본다.
그래서 값이 같아 보여도 서로 다른 배열 두 개면 `==`는 `false`다.

이 문서를 한 줄로 줄이면 이렇게 읽으면 된다.

- 같은 배열인지 확인: `==`
- 1차원 배열 값 비교: `Arrays.equals(...)`
- 중첩 배열 값 비교: `Arrays.deepEquals(...)`

큰 equality 감각 자체가 아직 흔들리면 먼저 [Java Equality and Identity Basics](./java-equality-identity-basics.md)에서 "같은 객체"와 "같은 값"을 분리하고, 다시 이 문서로 돌아오면 배열 규칙이 훨씬 덜 헷갈린다.

## 증상으로 바로 고르기

배열 비교도 "문법"보다 "지금 무슨 증상이 보이느냐"로 고르면 빠르다.

| 지금 보이는 증상 | 실제로 묻는 질문 | 먼저 쓸 도구 | 다음 연결 |
|---|---|---|---|
| `first == second`가 `false`인데 눈으로는 값이 같다 | 같은 배열인지, 같은 값인지 | 값 비교면 `Arrays.equals(...)` | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |
| `array.equals(other)`도 `false`다 | 배열이 `equals()`를 값 비교로 바꿨는가 | 보통 아니다. `Arrays.equals(...)` 또는 `Arrays.deepEquals(...)` | [Java `Arrays` 메서드 선택 30초 카드](./java-arrays-method-choice-30-second-card.md) |
| `String[][]` 비교에 `Arrays.equals(...)`를 썼는데 `false`다 | 바깥 배열 원소가 다시 배열인가 | `Arrays.deepEquals(...)` | [Java 배열 입문 공통 confusion 체크리스트](./java-array-common-confusion-checklist.md) |
| 한쪽을 바꾸면 다른 쪽도 같이 바뀐다 | 비교 문제가 아니라 alias인가 | `left == right`로 같은 배열인지 확인 | [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md) |

배열 comparison bug를 만났을 때 첫 질문은 항상 이 두 개면 충분하다.

1. 지금 내가 보고 싶은 건 같은 배열인가, 같은 값인가?
2. 이 배열이 1차원인가, 배열 안에 배열이 또 있는가?

## 한눈에 보기

| 비교 방법 | 실제 의미 | 잘 맞는 경우 | 초보자 주의점 |
|---|---|---|---|
| `==` | 같은 배열 객체를 가리키는가 | alias 확인 | 값이 같아도 새로 만든 배열 둘이면 `false` |
| `array.equals(other)` | 배열에서는 사실상 identity 비교 | 거의 쓰지 않는 편이 안전 | 값 비교라고 기대하면 틀리기 쉽다 |
| `Arrays.equals(a, b)` | 1차원 배열 원소가 같은 순서로 같은가 | `int[]`, `String[]`, `Member[]` | 원소가 다시 배열이면 안쪽까지는 내려가지 않는다 |
| `Arrays.deepEquals(a, b)` | 중첩 배열 내부까지 내려가서 같은가 | `int[][]`, `String[][]`, 배열을 담은 `Object[]` | 1차원 primitive 배열 만능 도구가 아니다 |

짧게 외우면 이렇다.

- 배열 `==`는 reference identity
- 배열 값 비교의 기본값은 `Arrays.equals(...)`
- 2차원 이상이거나 배열 안에 배열이 있으면 `Arrays.deepEquals(...)`

## 왜 `==`와 `array.equals(...)`가 계속 헷갈릴까

배열도 객체이기 때문이다.

```java
int[] first = {1, 2, 3};
int[] second = {1, 2, 3};
int[] alias = first;

System.out.println(first == second); // false
System.out.println(first == alias);  // true
System.out.println(first.equals(second)); // false
```

이 예제를 문장으로 읽으면 단순하다.

- `first`와 `second`는 값은 같지만 다른 배열이다
- `alias`는 `first`와 같은 배열을 같이 본다
- 배열의 `equals()`는 초보자가 기대하는 "값 비교용 equals"가 아니다

즉 배열에서 `==`와 `array.equals(...)`가 둘 다 `false`라면, 대개 버그는 "`equals`를 썼는데 왜 값 비교가 안 되지?" 쪽이다.
그때는 바로 core equality 문서의 한 줄 규칙으로 돌아가면 된다.

> 참조형에서 `==`는 보통 같은 객체 질문이고, 값 질문이면 타입이 제공하는 값 비교 도구로 간다.

배열에서 그 "값 비교 도구"가 바로 `Arrays.equals(...)`와 `Arrays.deepEquals(...)`다.

## 1차원 배열과 중첩 배열을 나눠 보기

### 1차원 배열: `Arrays.equals(...)`

```java
import java.util.Arrays;

int[] left = {1, 2, 3};
int[] right = {1, 2, 3};

System.out.println(Arrays.equals(left, right)); // true
```

이때 `Arrays.equals(...)`는 길이와 순서와 각 칸의 값을 본다.
그래서 `int[]`, `long[]`, `String[]` 같은 평범한 1차원 배열 비교의 기본값으로 생각하면 된다.

### 중첩 배열: `Arrays.deepEquals(...)`

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

System.out.println(Arrays.equals(board1, board2));     // false
System.out.println(Arrays.deepEquals(board1, board2)); // true
```

`board1`과 `board2`의 바깥 배열 원소는 `String[]`다.
그래서 `Arrays.equals(...)`는 row 배열들을 다시 객체로 보고 비교해 `false`가 될 수 있다.
이럴 때는 안쪽 배열까지 내려가는 `Arrays.deepEquals(...)`가 맞다.

배열 구조를 이렇게 읽으면 된다.

- `int[]`, `String[]`: 1차원 비교
- `int[][]`, `String[][]`: 중첩 비교
- `Object[]` 안에 배열이 들어 있다: 중첩 비교

## 흔한 오해와 함정

### `array.equals(...)`면 값 비교라고 생각한다

배열은 그 기대를 만족하지 않는다.
배열 값 비교 의도를 드러내려면 `Arrays.equals(...)` 또는 `Arrays.deepEquals(...)`를 써야 한다.

### 2차원 배열도 `Arrays.equals(...)`면 충분하다고 생각한다

2차원 배열은 "배열 안에 배열"이다.
겉만 보면 안쪽 row는 여전히 다른 배열 객체라서 `Arrays.equals(...)`가 기대와 다르게 보일 수 있다.

### `Arrays.deepEquals(...)`를 모든 배열의 만능 해답으로 생각한다

초보자 기본 규칙은 더 단순하게 두는 편이 좋다.

- 평범한 1차원 배열: `Arrays.equals(...)`
- 중첩 배열: `Arrays.deepEquals(...)`

이렇게 나누면 불필요하게 복잡한 오버로드 규칙까지 한 번에 들고 가지 않아도 된다.

### 순서가 달라도 원소만 같으면 같다고 생각한다

배열 비교는 둘 다 순서 민감하다.
집합처럼 "들어 있는 원소만 같으면 된다"가 아니다.

## 실무에서 쓰는 모습

배열 equality bug는 보통 테스트 코드나 디버깅에서 처음 보인다.

- 예상 결과 배열과 실제 결과 배열을 비교해야 할 때
- 2차원 보드, 좌표표, 좌석 상태처럼 중첩 배열을 검증할 때
- copy 문제인지 comparison 문제인지 먼저 잘라야 할 때

예를 들어 "출력은 같은데 assertion이 실패한다"면 아래 순서가 안전하다.

1. 비교 대상이 1차원인지 중첩 배열인지 먼저 본다.
2. 1차원이면 `Arrays.equals(...)`, 중첩이면 `Arrays.deepEquals(...)`로 바꾼다.
3. 그래도 이상하면 값 비교 문제가 아니라 alias나 복사 문제인지 확인한다.

이 흐름은 [Java Equality and Identity Basics](./java-equality-identity-basics.md)의 symptom route와 같다.
먼저 "같은 객체 질문인가, 같은 값 질문인가"를 자르고, 그다음 배열 타입에 맞는 비교 도구를 고른다.

## 더 깊이 가려면

- 배열 비교 전에 equality 기본 축을 다시 잡고 싶으면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- 출력이 `[I@...`처럼 보여서 비교 전에 눈으로 확인하는 법이 먼저 필요하면 [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)
- 한쪽 변경이 다른 쪽에도 퍼져서 comparison보다 alias가 의심되면 [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
- 배열 equality 다음 단계로 `HashSet`/`HashMap`의 `equals()`/`hashCode()` 흐름을 잇고 싶으면 [`HashMap`/`HashSet` 조회 흐름 브리지: `hashCode()` 다음에 왜 `equals()`를 볼까](./hashmap-hashset-hashcode-equals-lookup-bridge.md)

## 한 줄 정리

배열 비교에서 먼저 자를 것은 "같은 배열인가, 같은 값인가"이고, 값 비교라면 1차원은 `Arrays.equals(...)`, 중첩 배열은 `Arrays.deepEquals(...)`로 가면 된다.
