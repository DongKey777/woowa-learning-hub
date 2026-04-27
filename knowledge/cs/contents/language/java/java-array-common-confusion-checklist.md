# Java 배열 입문 공통 confusion 체크리스트

> 한 줄 요약: 배열에서 막힐 때는 먼저 "지금 헷갈리는 게 출력인지, 값 비교인지, 같은 배열 공유인지, 제자리 정렬인지"를 나누면 `==`, alias, `Arrays.sort()` 함정을 훨씬 빨리 피할 수 있다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [Java 반복문과 스코프 follow-up 입문](./java-loop-control-scope-follow-up-primer.md)
> - [Java `Arrays` 메서드 선택 30초 카드](./java-arrays-method-choice-30-second-card.md)
> - [Java 2차원 배열 순회 입문](./java-2d-array-traversal-primer.md)
> - [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)
> - [Java Array Equality Basics](./java-array-equality-basics.md)
> - [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
> - [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
> - [Primitive Descending Array Sort Bridge](./primitive-descending-array-sort-bridge.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

> retrieval-anchor-keywords: java array common confusion checklist, java array beginner checklist, java array confusion bridge, java array re-entry checklist, java array first routing, java array same array vs same value, java array compare copy sort checklist, java array == vs value compare, java array equals confusion, java array alias confusion, java array assignment alias, java array sort mutates original, java array in place sort, java array beginner routing, java array same value but false, java array changed together, java array sort changed original, java 2d array confusion route, java row column confusion route, jagged array confusion route, 자바 배열 혼동 체크리스트, 자바 배열 입문 체크리스트, 배열 공통 confusion, 배열 재진입 체크리스트, 배열 같은 값 같은 배열 차이, 배열 == 값 비교 차이, 배열 equals 혼동, 배열 alias 혼동, 배열 대입 참조 공유, 배열 sort 원본 변경, 배열 제자리 정렬, 배열 비교 복사 정렬 분기, 배열 인덱스 순회 실수, 2차원 배열 행 열 혼동, jagged array 순회 실수, i less than length, i less or equal length, array loop route, 배열 length까지 돌면 왜 에러, 배열 길이만큼 돌면 왜 터짐, i <= arr.length 왜 에러, 배열 마지막 인덱스 length minus one, 배열 오프바이원 입문

## 먼저 잡는 mental model

배열에서 자주 막히는 질문은 사실 서로 다른 네 문제다.

- 출력: "지금 배열 안에 뭐가 들어 있지?"
- 비교: "두 배열의 값이 같은가?"
- 공유: "두 변수가 같은 배열을 같이 보고 있나?"
- 정렬: "정렬 결과가 원본을 바꿨나, 복사본을 만들었나?"

초보자 기준으로는 아래 한 줄이 제일 중요하다.

> 배열 문제를 만나면 먼저 "값이 같은가"와 "같은 배열인가"를 분리해서 생각한다.

이 한 줄만 놓치지 않으면 `==`, alias, 제자리 정렬이 한 덩어리로 섞이는 일을 많이 줄일 수 있다.

## 이 문서를 먼저 열면 좋은 순간

- "값은 같은데 왜 false지?"와 "왜 같이 바뀌지?"가 머릿속에서 섞이기 시작할 때
- `==`, `clone()`, `Arrays.sort()`를 각각 봤는데도 어디로 다시 돌아가야 할지 감이 안 잡힐 때
- 배열 primer를 여러 장 읽고 나서도 "지금 질문이 비교인지 공유인지 정렬인지" 구분이 안 될 때

반대로 아직 "`i <= arr.length`가 왜 안 되지?"처럼 반복문과 인덱스 범위 자체가 먼저 흔들리면, 이 문서보다 [Java 반복문과 스코프 follow-up 입문](./java-loop-control-scope-follow-up-primer.md)의 배열 인덱스 순회 bridge를 먼저 보는 편이 빠르다.

이 한 문장도 같이 붙여 두면 헷갈림이 줄어든다.

> 배열의 `length`는 마지막 칸 번호가 아니라 전체 칸 수다. 그래서 마지막 유효 인덱스는 항상 `length - 1`이다.

## 10초 선택표

| 지금 보이는 증상 | 실제로 먼저 묻는 질문 | 첫 도구/첫 확인 | 다음 문서 |
|---|---|---|---|
| `System.out.println(array)` 결과가 `[I@...`처럼 이상하다 | "출력 경로가 잘못된 건가?" | 1차원은 `Arrays.toString()`, 중첩 배열은 `Arrays.deepToString()` | [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md) |
| 값은 같아 보이는데 `==` 또는 `array.equals(...)`가 `false`다 | "같은 배열을 비교한 건가, 값 비교를 한 건가?" | 1차원은 `Arrays.equals()`, 중첩 배열은 `Arrays.deepEquals()` | [Java Array Equality Basics](./java-array-equality-basics.md) |
| `copied = original` 뒤 한쪽을 바꾸니 다른 쪽도 바뀐다 | "복사본이 아니라 같은 배열 alias인가?" | `copied == original` 확인 | [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md) |
| `Arrays.sort()` 뒤 원본 순서가 사라졌다 | "정렬이 새 배열을 만든다고 착각했나?" | `sort()`는 반환값 없이 원본을 직접 바꿈 | [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md) |
| `int[]`에 `Comparator.reverseOrder()`를 넘기려다 막혔다 | "primitive 배열인데 object 배열 overload를 기대했나?" | `int[]`는 오름차순 정렬 후 뒤집기/역방향 읽기부터 검토 | [Primitive Descending Array Sort Bridge](./primitive-descending-array-sort-bridge.md) |
| 2차원 배열에서 `row`/`col`이 자꾸 바뀌거나 jagged array에서 터진다 | "바깥 길이와 현재 row 길이를 섞고 있나?" | 바깥은 `arr.length`, 안쪽은 `arr[row].length` 확인 | [Java 2차원 배열 순회 입문](./java-2d-array-traversal-primer.md) |

배열 순회에서 자주 나오는 오프바이원만 따로 보면 다음 비교가 가장 빠르다.

| 코드 | 길이 3 배열에서 마지막 접근 | 결과 |
|---|---|---|
| `for (int i = 0; i < arr.length; i++)` | `arr[2]` | 안전한 기본형 |
| `for (int i = 0; i <= arr.length; i++)` | `arr[3]` | `ArrayIndexOutOfBoundsException` 위험 |

## 가장 많이 반복되는 세 가지 혼동

### 1. `==`는 값 비교가 아니라 "같은 배열인가"를 본다

```java
int[] first = {1, 2, 3};
int[] second = {1, 2, 3};

System.out.println(first == second); // false
```

`first`와 `second`는 내용은 같아도 서로 다른 배열이다.

- 같은 배열 객체인지 확인: `==`
- 1차원 배열 값 비교: `Arrays.equals(...)`
- 2차원 이상 배열 값 비교: `Arrays.deepEquals(...)`

즉 "`==`가 false"라는 사실만으로 "값이 다르다"라고 결론 내리면 안 된다.

### 2. `copied = original`은 복사가 아니라 alias다

```java
int[] original = {1, 2, 3};
int[] copied = original;

copied[0] = 99;

System.out.println(original[0]); // 99
```

이 코드는 새 배열을 만들지 않는다.
두 변수가 같은 배열을 함께 가리킨다.

- 원본과 분리된 배열이 필요하면 `clone()` 또는 `Arrays.copyOf()`
- 중첩 배열이면 바깥 배열만 복사해서는 부족할 수 있음

즉 "한쪽 수정이 같이 퍼진다"는 증상은 비교 문제가 아니라 공유 문제다.

### 3. `Arrays.sort()`는 정렬된 복사본을 반환하지 않는다

```java
int[] numbers = {3, 1, 2};

Arrays.sort(numbers);

System.out.println(Arrays.toString(numbers)); // [1, 2, 3]
```

`Arrays.sort()`는 기존 배열을 **제자리에서** 정렬한다.

- 원본을 유지하고 싶으면 먼저 복사
- 그다음 복사본을 정렬

```java
int[] original = {3, 1, 2};
int[] sortedCopy = original.clone();

Arrays.sort(sortedCopy);
```

즉 "정렬 후 원본이 바뀌었다"는 증상은 alias와 비슷하게 보이지만, 실제 원인은 `sort()` 자체가 원본 변경 API라는 점이다.

## 한 번에 같이 보면 덜 헷갈리는 예제

```java
import java.util.Arrays;

int[] original = {3, 1, 2};
int[] alias = original;
int[] copy = original.clone();

System.out.println(original == alias);            // true
System.out.println(original == copy);             // false
System.out.println(Arrays.equals(original, copy)); // true

Arrays.sort(alias);

System.out.println(Arrays.toString(original)); // [1, 2, 3]
System.out.println(Arrays.toString(copy));     // [3, 1, 2]
```

여기서 읽는 순서는 이렇다.

- `alias`는 `original`과 같은 배열이다
- `copy`는 다른 배열이지만 초기 값은 같다
- `Arrays.sort(alias)`는 결국 `original`을 정렬한 것과 같다
- `copy`는 독립된 배열이므로 그대로 남는다

이 예제 하나에 `==`, alias, 값 비교, 제자리 정렬이 같이 들어 있다.

## 초보자 체크리스트

- 지금 묻는 게 "같은 값인가"인지 "같은 배열인가"인지 먼저 적어 본다
- 배열 값 비교에 `array.equals(...)`를 습관처럼 쓰지 않는다
- `copied = original`을 보면 먼저 "복사"가 아니라 "공유"라고 읽는다
- `Arrays.sort(...)`를 호출하기 전에 원본 보존이 필요한지 먼저 확인한다
- 원본 보존이 필요하면 `clone()` 또는 `Arrays.copyOf()` 뒤에 정렬한다
- 2차원 이상 배열이면 출력은 `deepToString()`, 비교는 `deepEquals()`를 먼저 떠올린다

## 30초 재진입 순서

1. 메서드 자체가 헷갈리면 [Java `Arrays` 메서드 선택 30초 카드](./java-arrays-method-choice-30-second-card.md)부터 본다.
2. 출력이 이상하면 [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)로 간다.
3. `false`가 문제면 [Java Array Equality Basics](./java-array-equality-basics.md)로 간다.
4. 같이 바뀌면 [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)로 간다.
5. 정렬 뒤 원본이 달라졌거나 검색 결과가 이상하면 [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)로 간다.

## 다음에 어디로 이어 읽으면 좋은가

| 지금 가장 헷갈리는 질문 | 다음 문서 |
|---|---|
| "`[I@...`처럼 출력이 이상한 이유가 먼저 궁금하다" | [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md) |
| "`==`, `equals`, `Arrays.equals`, `Arrays.deepEquals`를 정확히 구분하고 싶다" | [Java Array Equality Basics](./java-array-equality-basics.md) |
| "`clone()`과 `Arrays.copyOf()`까지 포함해 복사/공유를 더 자세히 보고 싶다" | [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md) |
| "`sort`와 `binarySearch`를 같이 쓸 때 전제가 무엇인지 알고 싶다" | [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md) |

## 한 줄 정리

배열 입문에서 가장 흔한 실수는 `==`, alias, `Arrays.sort()`를 모두 "값이 왜 이상하지?" 한 문제로 섞어 읽는 것이다. 먼저 출력/비교/공유/정렬 네 축을 나누면 다음 문서 선택도 훨씬 쉬워진다.
