# Java 2차원 배열 출력·비교·shallow copy 브리지

> 한 줄 요약: Java의 2차원 배열은 "배열 안에 row 배열이 들어 있는 구조"라서, 출력은 `Arrays.deepToString()`, 값 비교는 `Arrays.deepEquals()`, `clone()`/`Arrays.copyOf()`는 바깥만 복사하는 shallow copy라는 세 규칙을 같이 묶어 보는 편이 덜 헷갈린다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java 2d array deeptostring deepequals shallow copy bridge basics, java 2d array deeptostring deepequals shallow copy bridge beginner, java 2d array deeptostring deepequals shallow copy bridge intro, java basics, beginner java, 처음 배우는데 java 2d array deeptostring deepequals shallow copy bridge, java 2d array deeptostring deepequals shallow copy bridge 입문, java 2d array deeptostring deepequals shallow copy bridge 기초, what is java 2d array deeptostring deepequals shallow copy bridge, how to java 2d array deeptostring deepequals shallow copy bridge
> 관련 문서:
> - [Java 배열 입문 공통 confusion 체크리스트](./java-array-common-confusion-checklist.md)
> - [Java 2차원 배열 순회 입문](./java-2d-array-traversal-primer.md)
> - [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)
> - [Java Array Equality Basics](./java-array-equality-basics.md)
> - [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)

> retrieval-anchor-keywords: java 2d array confusion bridge, java 2d array deepToString deepEquals shallow copy, java multidimensional array debug compare copy together, java matrix deepToString deepEquals clone, java nested array output compare copy bridge, java 2d array same output but shared row, java clone shallow copy 2d array beginner, java Arrays.deepToString Arrays.deepEquals matrix, java 2d array row shared clone, java array of arrays beginner bridge, 자바 2차원 배열 confusion bridge, 자바 2차원 배열 출력 비교 복사 한 번에, 자바 deepToString deepEquals shallow copy, 자바 2차원 배열 clone 왜 같이 바뀜, 자바 배열 안의 배열 브리지, 자바 행 배열 공유 복사

## 먼저 잡는 mental model

2차원 배열을 "표 한 장"으로만 보면 출력, 비교, 복사가 자꾸 따로 놀아 보인다.

초보자에게는 이 한 줄이 더 안전하다.

> 2차원 배열 = 바깥 배열 안에 row 배열들이 들어 있는 구조

이 관점으로 보면 세 가지가 한 번에 정리된다.

- 출력: row 배열 안까지 내려가야 실제 값이 보인다
- 비교: row 배열 안까지 내려가야 값 비교가 된다
- 복사: 바깥 배열만 복사하면 row 배열은 여전히 공유될 수 있다

## 20초 비교표

| 지금 하고 싶은 일 | 2차원 배열에서 먼저 떠올릴 것 | 이유 |
|---|---|---|
| 내용 출력 | `Arrays.deepToString(board)` | row 배열 안까지 내려가서 보여 준다 |
| 값 비교 | `Arrays.deepEquals(left, right)` | row 배열 안까지 내려가서 비교한다 |
| 복사 | `clone()`/`Arrays.copyOf()`는 shallow copy부터 의심 | 바깥 배열만 새로 만들고 안쪽 row는 공유할 수 있다 |

## 한 예제로 같이 보기

```java
import java.util.Arrays;

public class TwoDimensionalArrayBridge {
    public static void main(String[] args) {
        int[][] original = {
                {1, 2},
                {3, 4}
        };

        int[][] sameValues = {
                {1, 2},
                {3, 4}
        };

        int[][] shallowCopy = original.clone();

        System.out.println(Arrays.toString(original));
        // [[I@..., [I@...]

        System.out.println(Arrays.deepToString(original));
        // [[1, 2], [3, 4]]

        System.out.println(Arrays.equals(original, sameValues));
        // false

        System.out.println(Arrays.deepEquals(original, sameValues));
        // true

        System.out.println(original == shallowCopy);
        // false

        System.out.println(original[0] == shallowCopy[0]);
        // true

        shallowCopy[0][0] = 99;

        System.out.println(Arrays.deepToString(original));
        // [[99, 2], [3, 4]]

        System.out.println(Arrays.deepToString(shallowCopy));
        // [[99, 2], [3, 4]]
    }
}
```

이 예제는 일부러 세 축을 한 번에 붙여 둔 것이다.

- `Arrays.toString(original)`은 바깥 배열만 보여서 row가 `[[I@...`처럼 보인다
- `Arrays.deepToString(original)`은 row 안까지 내려가 실제 값이 보인다
- `Arrays.equals(original, sameValues)`는 row 배열 reference를 비교해서 `false`가 된다
- `Arrays.deepEquals(original, sameValues)`는 row 안의 값까지 비교해서 `true`가 된다
- `original.clone()`은 바깥 배열은 새로 만들지만 `original[0]`과 `shallowCopy[0]`은 같은 row를 공유한다

## 한 예제로 같이 보기 (계속 2)

즉 마지막 변경이 원본에도 반영되는 이유는 "2차원 배열이라서 특별한 버그가 생긴 것"이 아니라, **row 배열이 공유된 shallow copy**이기 때문이다.

## 초보자가 가장 자주 섞는 질문

| 보이는 증상 | 실제 원인 | 먼저 고칠 생각 |
|---|---|---|
| `[[I@...`처럼 출력된다 | 출력 도구가 얕다 | `deepToString()`으로 바꾼다 |
| 값이 같아 보이는데 비교가 `false`다 | row 배열 안까지 비교하지 않았다 | `deepEquals()`로 바꾼다 |
| 복사본만 바꿨는데 원본도 바뀐다 | row 배열을 공유하는 shallow copy다 | row까지 따로 복사할지 결정한다 |

여기서 중요한 구분은 이것이다.

- `deepToString()`은 보기용이다
- `deepEquals()`는 비교용이다
- `clone()`/`copyOf()`는 복사용이지만 2차원에서는 깊지 않을 수 있다

이 셋은 이름이 비슷해 보여도 역할이 다르다.

## row까지 분리하려면

2차원 `int[][]`를 원본과 완전히 분리하고 싶다면 row도 직접 복사해야 한다.

```java
int[][] deepCopy = new int[original.length][];
for (int row = 0; row < original.length; row++) {
    deepCopy[row] = original[row].clone();
}
```

이제는 `deepCopy[0][0]`을 바꿔도 `original[0][0]`은 함께 바뀌지 않는다.

초보자 기준으로는 아래 순서로 생각하면 충분하다.

1. 바깥 배열만 새로 만들면 shallow copy일 수 있다.
2. 2차원 배열에서는 row 공유 여부를 `original[row] == copied[row]`로 확인할 수 있다.
3. row까지 따로 복사해야 "수정 전파"를 끊을 수 있다.

## 다음에 어디로 이어 읽으면 좋은가

| 지금 더 궁금한 것 | 다음 문서 |
|---|---|
| "`arr.length`와 `arr[row].length`를 어디에 써야 하는지" | [Java 2차원 배열 순회 입문](./java-2d-array-traversal-primer.md) |
| "`[I@...`와 `[[I@...` 출력이 왜 생기는지" | [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md) |
| "`Arrays.equals`와 `Arrays.deepEquals`를 더 정확히 구분하고 싶다" | [Java Array Equality Basics](./java-array-equality-basics.md) |
| "`clone()`과 `Arrays.copyOf()`의 shallow copy 범위를 더 보고 싶다" | [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md) |

## 한 줄 정리

2차원 배열에서는 "배열 안의 배열"이라는 mental model 하나로 보면 `deepToString()`은 출력, `deepEquals()`는 값 비교, `clone()`/`copyOf()`는 shallow copy 가능성 확인이라는 세 갈래가 한 번에 정리된다.
