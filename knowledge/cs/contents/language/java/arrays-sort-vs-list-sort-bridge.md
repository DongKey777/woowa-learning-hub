# `Arrays.sort(...)` vs `List.sort(...)` 브리지

> 한 줄 요약: object 배열과 `List`는 모양만 다를 뿐, 같은 `Comparator` chain을 `Arrays.sort(array, comparator)`와 `list.sort(comparator)`에 그대로 옮겨 쓸 수 있다.

**난이도: 🟢 Beginner**

관련 문서:
- [Language README](../README.md)
- [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- [`Arrays.sort`, `List.sort`, `stream.sorted` Comparator Reuse Bridge](./arrays-sort-comparator-reuse-bridge.md)
- [`List.sort` vs `Collections.sort` 미니 브리지](./list-sort-vs-collections-sort-mini-bridge.md)
- [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- [Primitive Descending Array Sort Bridge](./primitive-descending-array-sort-bridge.md)

retrieval-anchor-keywords: arrays sort vs list sort, java array sort list sort, java arrays sort list sort comparator, java object array sorting beginner, java list sorting beginner, java comparator reuse array list, java in place sort array list, 자바 arrays sort list sort 차이, 자바 배열 정렬 리스트 정렬, 자바 comparator 재사용 배열 리스트, arrays sort vs list sort bridge basics, arrays sort vs list sort bridge beginner, arrays sort vs list sort bridge intro, java basics, beginner java

## 먼저 잡을 mental model

초보자에게 가장 중요한 결론은 이것이다.

- 정렬 규칙은 `Comparator`가 들고 있다
- `Arrays.sort(...)`와 `List.sort(...)`는 그 규칙을 적용하는 **입구**만 다르다
- 둘 다 **기존 대상 자체를 바로 다시 줄 세우는 제자리 정렬**이다

즉 API 이름을 따로 외우기보다 이렇게 보면 된다.

> "같은 줄 세우기 규칙을 배열에 적용하느냐, 리스트에 적용하느냐"

## 한 장 비교 표

| 질문 | `Arrays.sort(array, comparator)` | `list.sort(comparator)` |
|---|---|---|
| 정렬 규칙을 `Comparator`로 줄 수 있나? | 가능 | 가능 |
| 같은 comparator 변수를 재사용할 수 있나? | 가능 | 가능 |
| 원본 컨테이너가 바뀌나? | 바뀐다 | 바뀐다 |
| 주로 언제 보나? | object 배열을 직접 다룰 때 | `List` 컬렉션을 직접 다룰 때 |
| 초보자 주의점 | comparator overload는 object 배열에서만 쓴다 | natural ordering도 `list.sort(...)`로 가능 |

핵심은 차이보다 공통점이다.

- 둘 다 제자리 정렬이다
- 둘 다 같은 comparator chain을 받을 수 있다

리스트 쪽 호출이 `Collections.sort(list, comparator)`로 보이더라도 감각은 같다.

- 배열이면 `Arrays.sort(...)`
- 리스트면 `list.sort(...)` 또는 `Collections.sort(...)`
- 셋 다 새 컨테이너를 만드는 것이 아니라, 지금 들고 있는 대상을 바로 정렬한다

## 같은 comparator를 먼저 만든다

배열과 리스트를 오갈 때 헷갈리는 이유는 보통 정렬 규칙과 정렬 대상을 같이 보기 때문이다.

먼저 규칙을 분리하면 훨씬 단순해진다.

```java
import java.util.Comparator;

record Student(String name, int grade, int score) {}

Comparator<Student> byGradeThenScoreDescThenName =
        Comparator.comparingInt(Student::grade)
                .thenComparing(Comparator.comparingInt(Student::score).reversed())
                .thenComparing(Student::name);
```

이 comparator를 읽는 법은 같다.

1. `grade` 오름차순
2. 같은 `grade`면 `score` 내림차순
3. 그래도 같으면 `name` 오름차순

이 규칙은 배열용 규칙도 아니고 리스트용 규칙도 아니다.
그냥 `Student`를 어떤 순서로 줄 세울지 적은 규칙이다.

## 배열에서 쓰면 이렇게 된다

```java
import java.util.Arrays;
import java.util.Comparator;

record Student(String name, int grade, int score) {}

Student[] studentArray = {
        new Student("Mina", 2, 90),
        new Student("Ari", 1, 95),
        new Student("Joon", 2, 95),
        new Student("Bora", 2, 95)
};

Comparator<Student> byGradeThenScoreDescThenName =
        Comparator.comparingInt(Student::grade)
                .thenComparing(Comparator.comparingInt(Student::score).reversed())
                .thenComparing(Student::name);

Arrays.sort(studentArray, byGradeThenScoreDescThenName);
```

여기서 읽어야 할 포인트는 두 개다.

- 정렬 대상은 `studentArray`
- 정렬 규칙은 `byGradeThenScoreDescThenName`

## 리스트에서 쓰면 이렇게 된다

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

record Student(String name, int grade, int score) {}

List<Student> studentList = new ArrayList<>(List.of(
        new Student("Mina", 2, 90),
        new Student("Ari", 1, 95),
        new Student("Joon", 2, 95),
        new Student("Bora", 2, 95)
));

Comparator<Student> byGradeThenScoreDescThenName =
        Comparator.comparingInt(Student::grade)
                .thenComparing(Comparator.comparingInt(Student::score).reversed())
                .thenComparing(Student::name);

studentList.sort(byGradeThenScoreDescThenName);
```

바뀐 것은 거의 한 줄뿐이다.

- 배열이면 `Arrays.sort(studentArray, comparator)`
- 리스트면 `studentList.sort(comparator)`

즉 **정렬 규칙을 새로 배우는 것이 아니라, 정렬 대상에 맞는 호출 모양만 바꾸는 것**이다.

## 한 번에 이어서 보면 더 잘 보인다

같은 데이터를 배열과 리스트로 각각 들고 있어도 comparator는 그대로 옮긴다.

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

List<Student> studentList = new ArrayList<>(List.of(studentArray));

Arrays.sort(studentArray, byGradeThenScoreDescThenName);
studentList.sort(byGradeThenScoreDescThenName);
```

초보자 관점 기억법:

- "정렬 규칙"은 comparator 변수
- "배열용 입구"는 `Arrays.sort(...)`
- "리스트용 입구"는 `List.sort(...)`

## 그래서 무엇을 먼저 떠올리면 되나

| 지금 손에 있는 것 | 먼저 떠올릴 호출 | 이유 |
|---|---|---|
| `Student[]` 같은 object 배열 | `Arrays.sort(array, comparator)` | 배열은 static 유틸리티로 정렬 |
| `List<Student>` 같은 리스트 | `list.sort(comparator)` | 리스트 자신이 정렬 메서드를 가진다 |
| 정렬 규칙을 여러 군데에서 써야 함 | `Comparator<Student> by... = ...` | API마다 체인을 다시 쓰지 않아도 된다 |

여기서 중요한 건 "배열이냐 리스트냐"보다, **정렬 규칙을 이름 있는 comparator로 먼저 분리하느냐**다.

## 초보자가 자주 헷갈리는 지점

- `Arrays.sort(array, comparator)`와 `list.sort(comparator)`는 둘 다 기존 순서를 직접 바꾼다.
- 같은 comparator chain을 배열과 리스트에 모두 재사용할 수 있다.
- `Arrays.sort(int[], comparator)` 같은 형태는 없다. comparator overload는 object 배열용이다.
- `Collections.sort(list, comparator)`를 봐도 "리스트를 제자리 정렬하는 다른 호출 모양"으로 읽으면 된다. 배열에 쓰는 API가 아니다.
- 리스트에서 새 결과가 필요한 게 아니라 기존 리스트 순서를 바꾸고 싶다면 `List.sort(...)`가 자연스럽다.
- 배열에서 natural ordering만 필요하면 `Arrays.sort(array)`를 쓴다. 리스트에서 natural ordering만 필요하면 `list.sort(null)`도 가능하지만 초보자 문맥에서는 [`List.sort` vs `Collections.sort` 미니 브리지](./list-sort-vs-collections-sort-mini-bridge.md)처럼 더 읽기 쉬운 호출을 같이 비교하는 편이 낫다.

## 빠른 체크

- "같은 정렬 규칙을 배열과 리스트에 옮기고 싶다" -> comparator를 변수로 뽑는다
- "지금 손에 있는 것이 object 배열이다" -> `Arrays.sort(array, comparator)`
- "지금 손에 있는 것이 `List`다" -> `list.sort(comparator)`
- "`Collections.sort(list, comparator)`가 보인다" -> 이것도 리스트를 직접 바꾸는 호출이라고 읽는다
- "primitive 배열을 comparator로 정렬하려 한다" -> 그대로는 안 된다. [Primitive Descending Array Sort Bridge](./primitive-descending-array-sort-bridge.md)로 간다

## 한 줄 정리

`Arrays.sort(array, comparator)`와 `List.sort(comparator)`의 핵심 차이는 정렬 규칙이 아니라 정렬 대상의 모양이므로, 초보자에게 가장 안전한 패턴은 comparator chain을 먼저 이름 있는 변수로 만들고 그다음 배열에는 `Arrays.sort(...)`, 리스트에는 `List.sort(...)`로 같은 규칙을 그대로 연결하는 것이다.
