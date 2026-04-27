# `Arrays.sort`, `List.sort`, `stream.sorted` Comparator Reuse Bridge

> 한 줄 요약: 같은 `Comparator` chain은 다시 만들 필요 없이 `Arrays.sort(...)`, `List.sort(...)`, `stream.sorted(...)`에 그대로 연결할 수 있고, 초보자 기준 핵심 차이는 "무엇을 정렬하나"와 "원본을 바꾸나" 두 가지다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [`Arrays.sort(...)` vs `List.sort(...)` 브리지](./arrays-sort-vs-list-sort-bridge.md)
> - [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
> - [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
> - [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
> - [Primitive Descending Array Sort Bridge](./primitive-descending-array-sort-bridge.md)

> retrieval-anchor-keywords: language-java-00104, arrays sort comparator reuse bridge, java same comparator arrays sort list sort stream sorted, java comparator reuse across Arrays.sort List.sort stream.sorted, java comparator chain arrays list stream beginner, java Arrays.sort List.sort Stream.sorted side by side, java same sorting rule array list stream, java object array list stream comparator bridge, java sort api comparator reuse beginner, java array list stream sorting primer, java comparator variable reuse java sort apis, java sort mutates list sort mutates stream sorted new result, java object array sort list sort stream sorted, 자바 같은 comparator 배열 리스트 스트림 재사용, 자바 Arrays.sort List.sort stream.sorted 비교, 자바 정렬 규칙 재사용 브리지, 자바 배열 리스트 스트림 정렬 차이, 자바 comparator 체인 재사용, 자바 초급 정렬 API 비교

## 먼저 잡을 mental model

초보자에게 가장 안전한 기억법은 이것이다.

- `Comparator`는 줄 세우는 규칙이다
- `Arrays.sort(...)`, `List.sort(...)`, `stream.sorted(...)`는 그 규칙을 받는 서로 다른 입구다

즉 API를 세 개 따로 외우기보다 이렇게 보면 된다.

> "같은 정렬 규칙을 배열에 적용할지, 리스트 자체에 적용할지, 스트림 결과로 받을지 고른다"

## 한 장 비교 표

| 질문 | `Arrays.sort(array, comparator)` | `list.sort(comparator)` | `list.stream().sorted(comparator)` |
|---|---|---|---|
| 같은 comparator를 그대로 재사용할 수 있나? | 가능 | 가능 | 가능 |
| 원본 순서가 바뀌나? | 바뀐다 | 바뀐다 | 바뀌지 않는다 |
| 결과를 어디서 받나? | 같은 배열 | 같은 리스트 | 새 stream 결과 |
| 가장 자연스러운 상황 | object 배열이 손에 있음 | mutable `List`를 직접 정렬 | 원본 보존 + 새 결과 필요 |
| 초보자 메모 | `Arrays` 유틸리티 호출 | 리스트 인스턴스 메서드 | `toList()` 같은 최종 연산 필요 |

여기서 실전 판단 기준은 두 가지뿐이다.

- 지금 정렬 대상이 배열인가, 리스트인가
- 원본을 직접 바꿔도 되는가

## 같은 comparator를 먼저 이름 붙인다

세 API를 오갈 때 가장 흔한 실수는 정렬 규칙까지 매번 다시 쓰는 것이다.
먼저 규칙에 이름을 붙이면 세 군데가 한 번에 연결된다.

```java
import java.util.Comparator;

record Student(String name, int grade, int score) {}

Comparator<Student> byGradeThenScoreDescThenName =
        Comparator.comparingInt(Student::grade)
                .thenComparing(Comparator.comparingInt(Student::score).reversed())
                .thenComparing(Student::name);
```

이 comparator는 이렇게 읽는다.

1. `grade` 오름차순
2. 같은 `grade`면 `score` 내림차순
3. 그래도 같으면 `name` 오름차순

중요한 점은 이 규칙이 배열 전용도 아니고 리스트 전용도 아니라는 점이다.

## 세 API를 나란히 보면 차이가 더 작아진다

```java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

record Student(String name, int grade, int score) {}

Comparator<Student> byGradeThenScoreDescThenName =
        Comparator.comparingInt(Student::grade)
                .thenComparing(Comparator.comparingInt(Student::score).reversed())
                .thenComparing(Student::name);

Student[] studentArray = {
        new Student("Mina", 2, 90),
        new Student("Ari", 1, 95),
        new Student("Joon", 2, 95),
        new Student("Bora", 2, 95)
};

List<Student> originalList = new ArrayList<>(List.of(studentArray));
List<Student> listForSort = new ArrayList<>(originalList);

Arrays.sort(studentArray, byGradeThenScoreDescThenName);
listForSort.sort(byGradeThenScoreDescThenName);

List<Student> sortedView = originalList.stream()
        .sorted(byGradeThenScoreDescThenName)
        .toList();
```

### 옆으로 보면 바뀌는 부분

| 하고 싶은 일 | 코드 모양 | 읽는 법 |
|---|---|---|
| 배열을 직접 정렬 | `Arrays.sort(studentArray, by...)` | 배열 자체 순서가 바뀜 |
| 리스트를 직접 정렬 | `listForSort.sort(by...)` | 리스트 자체 순서가 바뀜 |
| 정렬된 새 결과 받기 | `originalList.stream().sorted(by...).toList()` | 원본은 두고 새 결과 생성 |

이 표를 보고 기억하면 된다.

- comparator는 그대로
- 호출 입구만 바뀜

## 가장 작은 side-by-side 예제

같은 데이터를 세 방식으로 보면 차이가 더 선명하다.

```java
Student[] studentArray = {
        new Student("Mina", 2, 90),
        new Student("Ari", 1, 95),
        new Student("Joon", 2, 95)
};

List<Student> originalList = new ArrayList<>(List.of(studentArray));
List<Student> listForSort = new ArrayList<>(originalList);

Arrays.sort(studentArray, byGradeThenScoreDescThenName);
listForSort.sort(byGradeThenScoreDescThenName);

List<Student> sortedCopy = originalList.stream()
        .sorted(byGradeThenScoreDescThenName)
        .toList();
```

```java
// Arrays.sort 후
studentArray
// [Student[name=Ari, grade=1, score=95],
//  Student[name=Joon, grade=2, score=95],
//  Student[name=Mina, grade=2, score=90]]

// List.sort 후
listForSort
// [Student[name=Ari, grade=1, score=95],
//  Student[name=Joon, grade=2, score=95],
//  Student[name=Mina, grade=2, score=90]]

// stream.sorted 후
sortedCopy
// [Student[name=Ari, grade=1, score=95],
//  Student[name=Joon, grade=2, score=95],
//  Student[name=Mina, grade=2, score=90]]
```

결과 순서는 같지만, 상태 변화는 다르다.

- `Arrays.sort(...)`는 배열을 바꾼다
- `List.sort(...)`는 `listForSort`를 바꾼다
- `stream.sorted(...)`는 새 결과를 만든다

## 초보자가 자주 헷갈리는 지점

- `stream.sorted(...)`도 같은 comparator를 쓰지만, 원본 리스트를 직접 정렬하는 것은 아니다.
- `originalList.stream().sorted(by...)`만 쓰고 끝내면 결과를 아직 사용하지 않은 것이다. `toList()` 같은 최종 연산이 필요하다.
- `Arrays.sort(array, comparator)`의 comparator overload는 object 배열용이다. `int[]` 같은 primitive 배열에는 그대로 못 쓴다.
- 정렬 규칙이 길어질수록 세 API마다 comparator chain을 다시 쓰지 말고 변수나 메서드로 뽑는 편이 안전하다.
- `.reversed()`를 체인 끝에 붙이면 전체 규칙이 뒤집힐 수 있다. 특정 필드만 내림차순이면 그 필드 comparator 범위 안에서 뒤집어 읽는다.

## 언제 무엇을 먼저 떠올리면 되나

| 지금 상황 | 먼저 떠올릴 것 | 이유 |
|---|---|---|
| `Student[]` 같은 object 배열을 이미 가지고 있다 | `Arrays.sort(array, comparator)` | 배열 정렬 입구 |
| 이후 코드가 같은 리스트를 계속 사용할 것이다 | `list.sort(comparator)` | 기존 리스트 자체를 정렬 |
| 원본 순서를 보존하고 정렬된 결과만 따로 쓰고 싶다 | `stream.sorted(comparator)` | 새 결과를 만들기 쉬움 |
| 세 군데에서 같은 규칙을 쓸 것 같다 | `Comparator<Student> by... = ...` | 중복과 방향 실수 감소 |

## 다음에 이어서 읽기 좋은 문서

- 배열과 리스트 두 입구 차이만 먼저 좁게 보고 싶다면 [`Arrays.sort(...)` vs `List.sort(...)` 브리지](./arrays-sort-vs-list-sort-bridge.md)
- 리스트와 스트림의 "원본 변경 vs 새 결과" 차이를 더 보고 싶다면 [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- comparator chain 조립법 자체가 아직 낯설다면 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- `.reversed()` 범위가 헷갈리면 [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
- primitive 배열에 comparator를 왜 바로 못 주는지 막히면 [Primitive Descending Array Sort Bridge](./primitive-descending-array-sort-bridge.md)

## 한 줄 정리

같은 `Comparator` chain은 `Arrays.sort(...)`, `List.sort(...)`, `stream.sorted(...)`에 그대로 재사용할 수 있으므로, 초보자에게 가장 안전한 패턴은 정렬 규칙에 먼저 이름을 붙인 뒤 "배열 직접 변경", "리스트 직접 변경", "정렬된 새 결과" 중 필요한 입구만 고르는 것이다.
