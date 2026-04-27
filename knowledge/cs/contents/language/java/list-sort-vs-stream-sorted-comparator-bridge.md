# `List.sort` vs `Stream.sorted` Comparator Bridge

> 한 줄 요약: `List.sort(...)`와 `stream.sorted(...)`는 서로 다른 정렬 API처럼 보이지만, 핵심은 같은 `Comparator` 정렬 규칙을 어디에 적용하느냐의 차이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: list sort vs stream sorted comparator bridge basics, list sort vs stream sorted comparator bridge beginner, list sort vs stream sorted comparator bridge intro, java basics, beginner java, 처음 배우는데 list sort vs stream sorted comparator bridge, list sort vs stream sorted comparator bridge 입문, list sort vs stream sorted comparator bridge 기초, what is list sort vs stream sorted comparator bridge, how to list sort vs stream sorted comparator bridge
> 관련 문서:
> - [Language README](../README.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
> - [`Arrays.sort`, `List.sort`, `stream.sorted` Comparator Reuse Bridge](./arrays-sort-comparator-reuse-bridge.md)
> - [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
> - [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
> - [`Stream.toList()` vs `Collectors.toList()` Result Mutability Bridge](./stream-tolist-vs-collectors-tolist-mutability-bridge.md)
> - [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
> - [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)

> retrieval-anchor-keywords: java list sort vs stream sorted, list sort stream sorted comparator bridge, java list sort comparator, java stream sorted comparator, same comparator list sort stream sorted, comparator chain list sort sorted stream, java sorted stream original list unchanged, list sort mutates list, stream sorted returns sorted stream, named comparator factory reuse java, comparator factory list sort stream sorted, mixed direction comparator factory java, comparator method extract reuse java, java sort comparator helper method, java comparator reuse across apis, stream toList vs collectors toList, stream result mutability bridge, sorted toList unmodifiable, collectors toList no guarantees, comparator readability boxing, comparingInt vs comparing readability, beginner java sorting bridge

<details>
<summary>Table of Contents</summary>

- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [같은 comparator를 먼저 변수로 뽑기](#같은-comparator를-먼저-변수로-뽑기)
- [mixed-direction comparator는 팩토리 이름으로 뽑아두기](#mixed-direction-comparator는-팩토리-이름으로-뽑아두기)
- [`List.sort(...)`: 기존 리스트를 직접 정렬](#listsort-기존-리스트를-직접-정렬)
- [`stream.sorted(...)`: 정렬된 흐름을 새 결과로 받기](#streamsorted-정렬된-흐름을-새-결과로-받기)
- [한 장 비교 표](#한-장-비교-표)
- [boxing보다 가독성이 먼저인 경우](#boxing보다-가독성이-먼저인-경우)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 먼저 잡을 mental model

정렬을 볼 때 API 이름부터 외우면 헷갈리기 쉽다.
먼저 이렇게 나누면 훨씬 단순하다.

- `Comparator`는 "어떤 순서로 줄 세울지"를 담은 규칙이다.
- `List.sort(comparator)`는 그 규칙으로 **기존 리스트 자체**를 바꾼다.
- `stream.sorted(comparator)`는 그 규칙으로 **정렬된 stream 흐름**을 만들고, 최종 연산에서 새 결과를 받는다.

즉 `List.sort`와 `Stream.sorted`의 차이는 "정렬 규칙이 다르다"가 아니다.

> 같은 정렬 규칙을 mutable list에 바로 적용할지, stream pipeline 안에서 새 결과로 받을지의 차이다.

## 같은 comparator를 먼저 변수로 뽑기

예를 들어 학생을 다음 순서로 보고 싶다고 해 보자.

1. 학년 오름차순
2. 같은 학년이면 점수 내림차순
3. 그래도 같으면 이름 오름차순

먼저 정렬 규칙을 `Comparator` 변수로 만든다.

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

record Student(String name, int grade, int score) {}

Comparator<Student> byGradeThenScoreDescThenName =
        Comparator.comparingInt(Student::grade)
                .thenComparing(Comparator.comparingInt(Student::score).reversed())
                .thenComparing(Student::name);

List<Student> students = new ArrayList<>(List.of(
        new Student("Mina", 2, 90),
        new Student("Ari", 1, 85),
        new Student("Joon", 2, 95),
        new Student("Bora", 2, 95)
));
```

여기서 중요한 건 `byGradeThenScoreDescThenName`이 **API 전용 규칙이 아니라 객체 정렬 규칙**이라는 점이다.
그래서 같은 comparator를 `List.sort(...)`에도 넘기고, `stream.sorted(...)`에도 넘길 수 있다.

## mixed-direction comparator는 팩토리 이름으로 뽑아두기

정렬 규칙이 한 번만 쓰이는 짧은 예제라면 변수 하나로도 충분하다.
하지만 초보자가 실무 코드에서 자주 만나는 상황은 이쪽이다.

- 화면 목록 정렬에도 같은 규칙이 필요하다
- `List.sort(...)`와 `stream.sorted(...)` 양쪽에서 같은 규칙을 쓴다
- "학년 오름차순 + 점수 내림차순 + 이름 오름차순"처럼 방향이 섞여 있다

이때는 체인을 사용하는 자리마다 다시 쓰기보다, **이름 있는 comparator 팩토리 메서드**로 뽑아두는 편이 읽기 쉽다.

```java
import java.util.Comparator;

record Student(String name, int grade, int score) {}

static Comparator<Student> byGradeAscScoreDescNameAsc() {
    return Comparator.comparingInt(Student::grade)
            .thenComparing(Comparator.comparingInt(Student::score).reversed())
            .thenComparing(Student::name);
}
```

이 메서드 이름은 규칙을 문장처럼 드러낸다.

- `grade`는 `Asc`
- `score`는 `Desc`
- `name`은 `Asc`

그래서 사용하는 쪽은 API보다 의도가 먼저 읽힌다.

```java
students.sort(byGradeAscScoreDescNameAsc());

List<Student> sortedStudents = students.stream()
        .sorted(byGradeAscScoreDescNameAsc())
        .toList();
```

초보자 기준에서 이 패턴의 장점은 세 가지다.

| 장점 | 왜 beginner-friendly 한가 |
|---|---|
| 규칙 이름이 남는다 | 긴 comparator 체인을 매번 해석하지 않아도 된다 |
| 중복이 줄어든다 | `List.sort`와 `stream.sorted`에서 실수로 다른 방향을 쓰기 어렵다 |
| 리뷰 포인트가 선명해진다 | "정렬 API 선택"과 "정렬 규칙 정의"를 분리해서 볼 수 있다 |

즉 mental model은 이렇게 잡으면 된다.

> `List.sort(...)`와 `stream.sorted(...)`는 같은 comparator 팩토리를 소비하는 두 입구일 뿐이고, mixed-direction 정렬 규칙 자체는 별도 이름으로 보관할 수 있다.

## `List.sort(...)`: 기존 리스트를 직접 정렬

기존 `students` 리스트 자체의 순서를 바꾸고 싶다면 `List.sort(...)`를 쓴다.

```java
students.sort(byGradeThenScoreDescThenName);
```

이 코드를 읽는 법은 다음과 같다.

- `students`라는 mutable list를 직접 재배열한다.
- 정렬이 끝나면 `students` 변수 안의 순서가 바뀌어 있다.
- 이후 코드가 같은 `students`를 쓰면 정렬된 순서를 보게 된다.

초보자용 판단 기준은 간단하다.

> 이 리스트를 이후에도 정렬된 상태로 계속 써도 괜찮으면 `List.sort(...)`가 자연스럽다.

## `stream.sorted(...)`: 정렬된 흐름을 새 결과로 받기

원본 리스트는 그대로 두고, 정렬된 결과만 따로 얻고 싶다면 `stream.sorted(...)`를 쓴다.

```java
List<Student> sortedStudents = students.stream()
        .sorted(byGradeThenScoreDescThenName)
        .toList();
```

이 코드를 읽는 법은 다음과 같다.

- `students` 원본 리스트의 순서는 바꾸지 않는다.
- stream pipeline 안에서 정렬된 흐름을 만든다.
- `toList()` 같은 최종 연산을 만나야 실제 결과 리스트가 만들어진다.
- 여기서 `sorted(...)`는 순서만 정하고, `toList()`가 결과 리스트 계약을 정한다.

초보자용 판단 기준은 이렇게 잡으면 된다.

> 원본을 건드리지 않고 "정렬된 결과"만 필요하면 `stream.sorted(...)`가 자연스럽다.

단, 정렬 결과를 나중에 `add`/`remove`할 생각이라면 `toList()`가 아니라 결과 컨테이너를 더 명시적으로 고르는 편이 안전하다.
이 차이는 [`Stream.toList()` vs `Collectors.toList()` Result Mutability Bridge](./stream-tolist-vs-collectors-tolist-mutability-bridge.md)에서 따로 정리했다.

## 한 장 비교 표

| 질문 | `List.sort(...)` | `stream.sorted(...)` |
|---|---|---|
| 같은 `Comparator`를 쓸 수 있나? | 가능 | 가능 |
| 원본 리스트가 바뀌나? | 바뀐다 | 바뀌지 않는다 |
| 결과를 어디서 얻나? | 정렬 후 같은 리스트 | `toList()`, `collect(...)` 같은 최종 연산 |
| 주로 어울리는 상황 | 이미 mutable list가 있고 그 순서 자체를 바꿔도 됨 | pipeline 중간에서 정렬하거나 원본 순서를 보존해야 함 |
| 초보자 기억법 | "이 리스트를 직접 줄 세운다" | "정렬된 흐름을 만들어 새 결과로 받는다" |

중요한 포인트는 하나다.

- comparator chain을 중복 작성하지 말고, 이름 있는 변수로 뽑으면 두 API에서 같은 의도를 공유할 수 있다

## boxing보다 가독성이 먼저인 경우

`Comparator.comparingInt(...)`와 `Comparator.comparing(...)`을 볼 때 boxing 이야기가 자주 나온다.
하지만 `List.sort`를 쓸지 `stream.sorted`를 쓸지는 boxing 문제가 아니다.

boxing 선택은 comparator 안에서 일어난다.

```java
Comparator<Student> byScorePrimitive =
        Comparator.comparingInt(Student::score);

Comparator<Student> byScoreBoxed =
        Comparator.comparing(Student::score);
```

`score`가 primitive `int`라면 `comparingInt`가 자연스럽다.
하지만 초급 단계에서 더 중요한 기준은 "정렬 의도가 바로 읽히는가"다.

| 상황 | 추천 감각 |
|---|---|
| `int`/`long`/`double` primitive 필드를 그대로 정렬 | `comparingInt`/`Long`/`Double`을 먼저 떠올린다 |
| `Integer`/`Long`/`Double` wrapper이고 `null` 가능성이 있음 | `comparing(...)` + `nullsFirst`/`nullsLast`가 더 안전하다 |
| 작은 화면용 리스트를 한두 번 정렬 | boxing 미세 차이보다 comparator 이름과 정렬 의도가 더 중요하다 |
| 큰 리스트를 자주 정렬하는 hot path | 성능 측정 뒤 primitive specialization을 적극적으로 본다 |

즉 초보자에게 안전한 결론은 이렇다.

- primitive면 `comparingInt`류를 기본 후보로 둔다.
- nullable wrapper면 `null` 정책을 먼저 드러낸다.
- 작은 코드에서 boxing을 피하려고 comparator를 읽기 어렵게 만들지는 않는다.
- 같은 comparator를 `List.sort`와 `stream.sorted` 양쪽에 재사용하면 성능보다 먼저 중복과 실수를 줄일 수 있다.

## 초보자가 자주 헷갈리는 지점

- `stream.sorted(comparator)`를 호출해도 원본 `List`가 정렬되는 것은 아니다. 최종 결과를 변수로 받아야 한다.
- `students.stream().sorted(...)`만 쓰고 끝내면 결과를 사용하지 않은 것이다. `toList()`, `forEach(...)`, `count()` 같은 최종 연산이 필요하다.
- 같은 정렬 기준을 두 번 손으로 쓰지 말고 `Comparator<Student> bySomething = ...`처럼 이름을 붙이면 리뷰에서 의도가 잘 보인다.
- mixed-direction 정렬이 길어지면 변수 하나보다 `byGradeAscScoreDescNameAsc()` 같은 팩토리 이름이 더 읽기 쉬울 수 있다.
- `.reversed()`를 체인 맨 끝에 붙이면 전체 comparator가 뒤집힐 수 있다. 특정 필드만 내림차순이면 `thenComparing(Comparator.comparingInt(...).reversed())`처럼 범위를 좁혀 읽는다.
- `List.sort(...)`와 `stream.sorted(...)` 중 무엇을 고를지는 "mutable 원본을 바꿀 것인가"가 먼저이고, boxing 미세 최적화는 그 다음 문제다.

## 어떤 문서를 다음에 읽으면 좋은가

- `Comparator` 자체가 아직 낯설다면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- `comparingInt`, `thenComparing`, `reversed`, `nullsLast` 조립법을 더 연습하려면 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- mixed-direction chain에서 어느 `reversed()`가 어디까지 영향을 주는지 더 정확히 보려면 [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
- stream pipeline의 `filter`, `map`, `sorted`, 최종 연산 흐름을 먼저 잡고 싶다면 [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
- `sorted(...)` 다음 `toList()`와 `Collectors.toList()`의 차이가 헷갈리면 [`Stream.toList()` vs `Collectors.toList()` Result Mutability Bridge](./stream-tolist-vs-collectors-tolist-mutability-bridge.md)
- `Integer`/`Long`/`Double` wrapper 필드의 `null` 정렬 정책이 헷갈리면 [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)

## 한 줄 정리

`List.sort(...)`와 `stream.sorted(...)`는 같은 `Comparator` chain이나 이름 있는 comparator 팩토리를 공유할 수 있으며, 선택 기준은 "원본 리스트를 직접 바꿀 것인가, 정렬된 새 결과를 받을 것인가"이고, 초보자에게는 mixed-direction 규칙을 재사용 가능한 이름으로 분리해 두는 것이 중복과 방향 실수를 줄이는 가장 안전한 출발점이다.
