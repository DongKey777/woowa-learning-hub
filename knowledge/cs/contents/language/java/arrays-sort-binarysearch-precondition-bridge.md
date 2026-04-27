# `Arrays.sort(...)` 뒤 `binarySearch(...)` 전제 브리지

> 한 줄 요약: `Arrays.binarySearch(...)`는 "정렬되어 있기만 하면 된다"가 아니라 **검색할 때 쓰는 기준과 같은 기준으로 정렬되어 있어야 한다**는 점이 초보자 함정이며, 가장 안전한 습관은 "정렬 규칙 확인 → 같은 규칙으로 검색" 체크리스트를 먼저 거치는 것이다.

**난이도: 🟢 Beginner**

관련 문서:
- [Language README](../README.md)
- [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
- [`Arrays.sort`, `List.sort`, `stream.sorted` Comparator Reuse Bridge](./arrays-sort-comparator-reuse-bridge.md)
- [Primitive Array Descending Search Primer](./primitive-array-descending-binarysearch-primer.md)
- [Binary Search Patterns](../algorithm/binary-search-patterns.md)

retrieval-anchor-keywords: language-java-00105, arrays sort binarysearch precondition bridge, java arrays sort then binarysearch checklist, java binarysearch same comparator precondition, java sort order must match search order, java binarysearch 왜 결과가 이상해요, java binarysearch 처음 배우는데 체크리스트, java descending sort binarysearch mismatch, java object array same comparator search, java arrays binarysearch unsorted comparator mismatch, 자바 binarysearch 전제 브리지, 자바 정렬 기준 검색 기준 같아야 함, 자바 배열 정렬 후 검색 체크리스트

## 왜 이 브리지가 필요한가

초보자는 보통 여기서 한 번 걸린다.

- "`Arrays.sort(...)` 했는데 왜 `binarySearch(...)` 결과가 이상하지?"
- "내림차순으로 정렬했는데 검색은 왜 안 맞지?"
- "정렬만 했으면 검색 준비가 끝난 것 아닌가?"

핵심은 "정렬 여부" 하나만 보는 것이 아니라는 점이다.

- `binarySearch(...)`는 정렬된 배열을 전제로 한다
- 그런데 그 정렬이 **검색이 기대하는 같은 기준**이어야 한다

즉 초보자에게 더 안전한 문장은 이것이다.

> "`sort`를 했는지"보다 "`무슨 규칙으로 sort 했고, search도 그 규칙을 쓰는지`"를 먼저 확인한다.

## 먼저 잡을 mental model

`binarySearch(...)`는 "줄이 이미 그 규칙대로 서 있다"고 믿고 가운데를 찍는다.

그래서 줄 세우는 규칙이 바뀌면 검색도 같이 바뀌어야 한다.

| 상황 | 줄 세우는 규칙 | 검색 호출 |
|---|---|---|
| primitive 배열 오름차순 | natural ascending | `Arrays.binarySearch(numbers, key)` |
| object 배열 이름 오름차순 | `Comparator.comparing(Student::name)` | `Arrays.binarySearch(array, key, sameComparator)` |
| object 배열 점수 내림차순 | `Comparator.comparingInt(Student::score).reversed()` | `Arrays.binarySearch(array, key, sameComparator)` |

한 줄로 줄이면 이렇다.

- 정렬 기준과 검색 기준이 같으면 `binarySearch(...)`가 믿을 수 있다
- 둘이 다르면 "정렬은 되어 보이는데 결과가 이상한" beginner 함정이 생긴다

## 바로 쓰는 4칸 체크리스트

`Arrays.sort(...)` 뒤에 `binarySearch(...)`를 붙일 때는 아래 네 줄만 먼저 확인하면 된다.

| 체크 | 예 | 왜 필요한가 |
|---|---|---|
| 1. 배열이 실제로 정렬됐나 | `Arrays.sort(numbers)` | 정렬 전 검색 방지 |
| 2. 어떤 기준으로 정렬했나 | 오름차순, 이름순, 점수 내림차순 | 검색 규칙 결정 |
| 3. 검색도 같은 기준을 쓰나 | 같은 comparator 전달 | 기준 불일치 방지 |
| 4. primitive인지 object 배열인지 구분했나 | `int[]` vs `Student[]` | primitive는 comparator overload가 없다 |

초보자용 빠른 기억법:

- 그냥 오름차순 primitive 배열이면 `sort(array)` 후 `binarySearch(array, key)`
- comparator로 정렬한 object 배열이면 `sort(array, by...)` 후 `binarySearch(array, key, by...)`
- 내림차순 primitive 배열처럼 보이면 먼저 "이 검색을 정말 표준 `binarySearch`로 처리해도 되나?"를 멈춰서 본다

## 코드로 바로 보기

같은 값 집합이어도 기준이 다르면 검색 호출도 달라진다.

```java
import java.util.Arrays;
import java.util.Comparator;

record Student(String name, int score) {}

Student[] students = {
        new Student("Mina", 90),
        new Student("Ari", 95),
        new Student("Joon", 80)
};

Comparator<Student> byScoreDesc =
        Comparator.comparingInt(Student::score).reversed();

Arrays.sort(students, byScoreDesc);

int ok = Arrays.binarySearch(students, new Student("", 90), byScoreDesc);
```

여기서 beginner 포인트는 하나다.

- 정렬할 때 `byScoreDesc`
- 검색할 때도 `byScoreDesc`

반대로 아래처럼 읽으면 위험하다.

```java
Arrays.sort(students, byScoreDesc);
Arrays.binarySearch(students, new Student("", 90));
```

이 코드는 "점수 내림차순으로 선 줄"에 대해 natural ordering 검색을 시도하므로 전제가 맞지 않는다.

## 초보자가 자주 헷갈리는 지점

- "`정렬만 했으면 됐다`"가 아니다. 어떤 규칙으로 정렬했는지가 같이 중요하다.
- object 배열을 comparator로 정렬했다면 검색도 같은 comparator overload를 써야 한다.
- primitive 배열은 comparator overload가 없으므로 내림차순 실배열에 표준 `binarySearch`를 그대로 붙이면 안 된다.
- `binarySearch(...)`가 틀린 것이 아니라, 검색이 기대한 줄과 실제 줄이 달라서 전제가 깨진 경우가 많다.
- 중복값 문제는 "같은 기준으로 찾았다" 이후의 다음 단계다. 먼저 기준 일치를 확인한 뒤 boundary 문제로 넘어간다.

## 다음 읽기

- 배열 정렬과 검색 규칙 전체를 한 번에 다시 보고 싶다면 [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
- 같은 comparator를 `Arrays.sort(...)`, `List.sort(...)`, `stream.sorted(...)`에 어떻게 재사용하는지 보고 싶다면 [`Arrays.sort`, `List.sort`, `stream.sorted` Comparator Reuse Bridge](./arrays-sort-comparator-reuse-bridge.md)
- primitive 배열 내림차순 검색 함정을 따로 좁혀 보고 싶다면 [Primitive Array Descending Search Primer](./primitive-array-descending-binarysearch-primer.md)
- 중복값에서 첫 위치/마지막 위치가 왜 바로 안 나오는지 이어서 보고 싶다면 [BinarySearch Duplicate Boundary Primer](./binarysearch-duplicate-boundary-primer.md)

## 한 줄 정리

`Arrays.binarySearch(...)`를 안전하게 쓰는 beginner 습관은 "정렬했는가?"에서 멈추지 않고 **"정렬 기준과 검색 기준이 같은가?"를 체크리스트로 먼저 확인하는 것**이다.
