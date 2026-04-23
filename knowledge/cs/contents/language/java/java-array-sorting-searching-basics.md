# Sorting and Searching Arrays Basics

> 한 줄 요약: Java 입문자가 `Arrays.sort()`와 `Arrays.binarySearch()`를 함께 배울 때 꼭 알아야 하는 "제자리 정렬", "같은 comparator로 정렬/검색", "음수 반환값 해석", "중복값과 comparator 계약"을 한 번에 묶어 정리한 beginner doc이다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [자바 언어의 구조와 기본 문법](./java-language-basics.md)
> - [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
> - [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

> retrieval-anchor-keywords: java Arrays.sort basics, java Arrays.binarySearch basics, java array sorting basics, java array searching basics, java sort array beginner, java binary search beginner, java sort mutates original array, java array sort in place, java primitive array sort ascending, java object array sort comparator, java binarySearch insertion point, java binarySearch negative result, java binarySearch unsorted array, java binarySearch same comparator, java reverse order binarySearch, java comparator precondition sort search, java comparator contract beginner, java duplicate binarySearch index, java beginner sort search mistakes

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 결론: `sort`와 `binarySearch` 규칙 한 장 요약](#먼저-결론-sort와-binarysearch-규칙-한-장-요약)
- [`Arrays.sort()` 기초](#arrayssort-기초)
- [`Arrays.binarySearch()` 기초](#arraysbinarysearch-기초)
- [comparator precondition은 왜 중요할까](#comparator-precondition은-왜-중요할까)
- [초보자가 자주 하는 실수](#초보자가-자주-하는-실수)
- [코드로 한 번에 보기](#코드로-한-번에-보기)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문자가 배열 정렬과 검색을 배우다가 자주 막히는 질문은 대체로 비슷하다.

- `Arrays.sort()`를 했더니 왜 원본 배열 순서가 바뀔까?
- `Arrays.binarySearch()`는 왜 정렬되지 않은 배열에서 이상한 값을 줄까?
- 내림차순으로 정렬했는데 왜 검색 결과가 틀릴까?
- 검색 결과가 `-3`처럼 나오면 이게 무슨 뜻일까?
- 중복값이 있을 때 왜 첫 번째 인덱스를 보장하지 않을까?

핵심은 간단하다.

- `Arrays.sort()`는 **새 배열을 반환하지 않고 기존 배열을 제자리에서 정렬**한다
- `Arrays.binarySearch()`는 **이미 정렬된 배열**에서만 의미가 있다
- custom ordering이나 내림차순을 쓰면 **정렬할 때 쓴 것과 같은 comparator**로 검색해야 한다
- 검색 결과가 음수면 "실패 코드"가 아니라 **삽입 위치 정보**가 들어 있다

이 문서는 위 규칙을 초보자 관점에서 한 흐름으로 정리한다.

## 먼저 결론: `sort`와 `binarySearch` 규칙 한 장 요약

| 하고 싶은 일 | 가장 먼저 떠올릴 도구 | 꼭 지켜야 하는 전제 | 초보자 메모 |
|---|---|---|---|
| `int[]`, `double[]` 같은 primitive 배열 오름차순 정렬 | `Arrays.sort(array)` | 배열이 직접 바뀐다 | 반환값이 없다 |
| `String[]` 같은 객체 배열 natural ordering 정렬 | `Arrays.sort(array)` | 원소가 `Comparable`이어야 한다 | 문자열은 사전순 |
| 내림차순/사용자 기준 정렬 | `Arrays.sort(array, comparator)` | comparator가 일관된 순서를 만들어야 한다 | 검색도 같은 comparator 사용 |
| 정렬된 배열에서 값 찾기 | `Arrays.binarySearch(array, key)` | natural ordering 기준으로 이미 정렬되어 있어야 한다 | 못 찾으면 음수 |
| comparator 기준 배열에서 값 찾기 | `Arrays.binarySearch(array, key, comparator)` | 같은 comparator로 정렬되어 있어야 한다 | 다른 comparator면 결과를 믿으면 안 된다 |

짧게 외우면 다음이 가장 안전하다.

- 정렬은 `sort`
- 정렬된 배열 빠른 검색은 `binarySearch`
- 검색 전에 "무슨 규칙으로 정렬되어 있는가?"를 먼저 확인한다

## `Arrays.sort()` 기초

`Arrays.sort()`는 배열을 **제자리(in place)** 에서 정렬한다.

```java
import java.util.Arrays;

int[] numbers = {7, 2, 9, 2};
Arrays.sort(numbers);

System.out.println(Arrays.toString(numbers)); // [2, 2, 7, 9]
```

중요한 점은 두 가지다.

- 반환값이 없다
- 원래 배열 자체의 순서가 바뀐다

그래서 "정렬된 복사본"이 필요하면 먼저 복사해야 한다.

```java
int[] original = {7, 2, 9, 2};
int[] sortedCopy = original.clone();

Arrays.sort(sortedCopy);

System.out.println(Arrays.toString(original));   // [7, 2, 9, 2]
System.out.println(Arrays.toString(sortedCopy)); // [2, 2, 7, 9]
```

### primitive 배열과 object 배열의 차이

primitive 배열은 기본 오름차순 정렬을 쓴다.

```java
int[] scores = {90, 70, 100};
Arrays.sort(scores); // [70, 90, 100]
```

객체 배열은 두 경우로 나뉜다.

- 원소 자체가 natural ordering을 가지면 `Arrays.sort(array)`
- 다른 기준이 필요하면 `Arrays.sort(array, comparator)`

```java
String[] names = {"Mina", "Ari", "Jin"};
Arrays.sort(names);

System.out.println(Arrays.toString(names)); // [Ari, Jin, Mina]
```

내림차순처럼 natural ordering이 아닌 정렬은 comparator를 넘긴다.

```java
import java.util.Arrays;
import java.util.Comparator;

String[] names = {"Mina", "Ari", "Jin"};
Arrays.sort(names, Comparator.reverseOrder());

System.out.println(Arrays.toString(names)); // [Mina, Jin, Ari]
```

여기서 초보자가 자주 놓치는 점이 하나 더 있다.

- primitive 배열에는 `Arrays.sort(int[], comparator)` 같은 overload가 없다

즉 `int[]`를 comparator로 바로 내림차순 정렬할 수는 없다.  
primitive 배열은 기본 오름차순으로 정렬한 뒤 직접 뒤집거나, `Integer[]` 같은 wrapper 배열을 써야 한다.

## `Arrays.binarySearch()` 기초

`Arrays.binarySearch()`는 정렬된 배열에서 빠르게 위치를 찾는 도구다.  
하지만 "아무 배열에서나 찾아 주는 메서드"가 아니다.

가장 중요한 전제는 하나다.

- **검색 전에 배열이 그 검색 규칙대로 이미 정렬되어 있어야 한다**

예를 들어 오름차순 `int[]`에서는 다음처럼 쓴다.

```java
int[] numbers = {7, 2, 9, 2};
Arrays.sort(numbers); // [2, 2, 7, 9]

int foundIndex = Arrays.binarySearch(numbers, 7);
int missingIndex = Arrays.binarySearch(numbers, 5);

System.out.println(foundIndex);   // 2
System.out.println(missingIndex); // -3
```

### 반환값 읽는 법

- `0` 이상이면: 찾은 인덱스다
- 음수면: 못 찾았지만 "어디에 끼워 넣어야 하는지" 정보가 들어 있다

음수 결과는 다음 공식으로 읽는다.

```java
int result = Arrays.binarySearch(numbers, 5); // -3
int insertionPoint = -result - 1;             // 2
```

즉 `5`는 인덱스 `2` 자리에 들어가면 정렬 순서가 유지된다는 뜻이다.

### 중복값이 있으면 어떤 인덱스가 나올까

이 점도 초보자가 자주 오해한다.

```java
int[] numbers = {2, 2, 2, 7, 9};
int index = Arrays.binarySearch(numbers, 2);
```

여기서 `index`는 `0`, `1`, `2` 중 하나일 수 있다.  
`Arrays.binarySearch()`는 **같은 값이 여러 개일 때 첫 번째나 마지막 인덱스를 보장하지 않는다**.

즉 "존재 여부"나 "아무 한 위치"를 찾는 데는 맞지만,  
"첫 번째 2의 위치"나 "마지막 2의 위치"가 필요하면 다른 로직이 더 필요하다.

## comparator precondition은 왜 중요할까

배열이 natural ordering이 아니라 custom ordering으로 정렬되었다면, 검색도 그 규칙을 그대로 따라야 한다.

예를 들어 이름을 내림차순으로 정렬했다고 해 보자.

```java
String[] names = {"Mina", "Ari", "Jin"};
Comparator<String> descending = Comparator.reverseOrder();

Arrays.sort(names, descending);
```

이제 `names`는 natural ordering 배열이 아니다.  
그래서 검색도 같은 comparator를 써야 한다.

```java
int correct = Arrays.binarySearch(names, "Jin", descending);
```

반대로 이렇게 검색하면 안 된다.

```java
int wrong = Arrays.binarySearch(names, "Jin");
```

이 호출은 배열이 natural ordering으로 정렬되어 있다고 가정하기 때문이다.  
즉 **정렬 규칙과 검색 규칙이 다르면 결과를 믿을 수 없다**.

### comparator는 "일관된 순서"를 만들어야 한다

초보자 버전으로 가장 안전한 기준은 다음이다.

- `a`가 `b`보다 앞이라고 했다가 뒤라고 하면 안 된다
- 같은 기준이면 항상 같은 비교 결과가 나와야 한다
- 동점으로 볼 원소에만 `0`을 반환해야 한다

이 계약이 깨지면 `Arrays.sort()`가 이상하게 동작하거나, 경우에 따라 예외를 던질 수도 있다.

```java
Comparator<String> broken =
        (left, right) -> left.length() >= right.length() ? 1 : -1;
```

위 comparator는 길이가 같은 문자열도 `0`이 아니라 `1`을 돌려준다.  
즉 "같다"는 경우를 표현하지 못하고, 비교 방향도 뒤집혀서 정렬/검색 전제를 깨뜨린다.

### tie-breaker가 없으면 검색 결과가 거칠어질 수 있다

예를 들어 학생을 점수만으로 비교하면, 같은 점수의 학생은 comparator 기준으로 같은 자리다.

```java
Comparator<Student> byScoreOnly =
        Comparator.comparingInt(Student::score).reversed();
```

이 상태에서 `binarySearch()`를 하면 "그 점수대의 학생들 중 하나"는 찾을 수 있지만,  
어느 학생의 인덱스가 나올지는 더 거칠어진다.

정확히 구분되는 순서가 필요하면 tie-breaker를 추가한다.

```java
Comparator<Student> byScoreThenId =
        Comparator.comparingInt(Student::score)
                .reversed()
                .thenComparingLong(Student::id);
```

즉 comparator precondition은 단순히 "컴파일만 되면 된다"가 아니라,  
**정렬과 검색이 같은 질서(order)를 공유하도록 설계해야 한다**는 뜻이다.

## 초보자가 자주 하는 실수

### 1. `Arrays.sort()`가 새 배열을 돌려준다고 생각한다

`Arrays.sort()`는 `void`이고 원본 배열을 직접 바꾼다.  
원래 순서를 남겨야 하면 먼저 `clone()`이나 `Arrays.copyOf()`로 복사한다.

### 2. 정렬하지 않은 배열에 바로 `Arrays.binarySearch()`를 쓴다

이 경우 결과는 의미가 없다.  
배열이 우연히 맞아 보이는 값을 줄 수 있어 더 위험하다.

### 3. 정렬할 때와 검색할 때 다른 comparator를 쓴다

내림차순 정렬 후 natural ordering 검색, 혹은 다른 필드 조합 comparator 검색은 모두 잘못된 전제다.

### 4. 음수 결과를 단순히 "없다"로만 읽는다

음수에는 삽입 위치가 들어 있다.  
새 값을 정렬 순서를 깨지 않고 넣어야 할 때 유용하다.

### 5. 중복값이면 첫 번째 인덱스를 줄 거라고 기대한다

`binarySearch()`는 같은 값이 여러 개면 임의의 일치 위치 하나를 돌려줄 수 있다.

### 6. primitive 배열에도 comparator 정렬이 바로 된다고 생각한다

`int[]`, `long[]` 같은 primitive 배열은 comparator overload가 없다.  
이 점을 모르고 `Arrays.sort(numbers, comparator)`를 시도하다가 막히는 경우가 많다.

## 코드로 한 번에 보기

```java
import java.util.Arrays;
import java.util.Comparator;

public class ArraySortSearchExample {
    private record Student(long id, String name, int score) {}

    public static void main(String[] args) {
        int[] original = {7, 2, 9, 2};
        int[] sortedCopy = original.clone();

        Arrays.sort(sortedCopy);
        System.out.println(Arrays.toString(original));   // [7, 2, 9, 2]
        System.out.println(Arrays.toString(sortedCopy)); // [2, 2, 7, 9]

        int found = Arrays.binarySearch(sortedCopy, 7);
        int missing = Arrays.binarySearch(sortedCopy, 5);
        int insertionPoint = -missing - 1;

        System.out.println(found);          // 2
        System.out.println(missing);        // -3
        System.out.println(insertionPoint); // 2

        String[] names = {"Mina", "Ari", "Jin"};
        Comparator<String> descending = Comparator.reverseOrder();

        Arrays.sort(names, descending);
        System.out.println(Arrays.toString(names)); // [Mina, Jin, Ari]
        System.out.println(Arrays.binarySearch(names, "Jin", descending)); // 1

        Student[] students = {
                new Student(2L, "Mina", 90),
                new Student(1L, "Ari", 95),
                new Student(3L, "Jin", 90)
        };

        Comparator<Student> byScoreThenId =
                Comparator.comparingInt(Student::score)
                        .reversed()
                        .thenComparingLong(Student::id);

        Arrays.sort(students, byScoreThenId);
        System.out.println(Arrays.toString(students));

        int studentIndex = Arrays.binarySearch(
                students,
                new Student(3L, "Jin", 90),
                byScoreThenId
        );
        System.out.println(studentIndex); // 2
    }
}
```

이 예제에서 확인할 포인트는 다섯 가지다.

- `sort()`는 제자리 정렬이다
- 원래 순서를 보존하려면 먼저 복사한다
- `binarySearch()`는 정렬된 배열에서만 의미가 있다
- 음수 결과는 insertion point로 다시 해석할 수 있다
- comparator 정렬과 comparator 검색은 같은 규칙을 공유해야 한다

## 빠른 체크리스트

- `Arrays.sort()`는 새 배열을 반환하지 않는다
- 원본 순서가 필요하면 먼저 복사한다
- `Arrays.binarySearch()` 전에 배열이 이미 정렬되어 있는지 확인한다
- natural ordering으로 정렬했으면 natural ordering으로 검색한다
- custom comparator로 정렬했으면 같은 comparator로 검색한다
- 음수 결과는 `-result - 1`로 insertion point를 읽는다
- 중복값에서는 첫 번째/마지막 인덱스를 기대하지 않는다
- primitive 배열에는 comparator 정렬 overload가 없다는 점을 기억한다

## 어떤 문서를 다음에 읽으면 좋은가

- comparator와 natural ordering 감각을 먼저 더 단단히 잡으려면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- 배열 복사와 원본 보존을 함께 이해하려면 [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
- 배열 출력 디버깅까지 같이 익히려면 [Java Array Debug Printing Basics](./java-array-debug-printing-basics.md)
- 방어적 복사와 "원본을 바꾸지 않기" 관점까지 확장하려면 [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

## 한 줄 정리

Java에서 배열 정렬과 검색의 핵심은 "`Arrays.sort()`는 배열을 제자리에서 정렬하고, `Arrays.binarySearch()`는 그와 같은 정렬 규칙을 공유하는 배열에서만 올바르게 동작한다"는 점이다.
