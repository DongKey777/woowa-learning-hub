# Comparator Utility Patterns

> 한 줄 요약: Java 입문자가 `Comparator.comparing`, `thenComparing`, primitive tie-breaker shortcut, `reversed`, `nullsFirst`, `nullsLast`를 "정렬 규칙을 조립하는 도구"로 이해하고 바로 손으로 연습할 수 있게 만든 practice-oriented companion doc이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java comparator utility patterns basics, java comparator utility patterns beginner, java comparator utility patterns intro, java basics, beginner java, 처음 배우는데 java comparator utility patterns, java comparator utility patterns 입문, java comparator utility patterns 기초, what is java comparator utility patterns, how to java comparator utility patterns
> 관련 문서:
> - [Language README](../README.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [`Arrays.sort`, `List.sort`, `stream.sorted` Comparator Reuse Bridge](./arrays-sort-comparator-reuse-bridge.md)
> - [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
> - [Comparator Null Reversal Primer](./comparator-null-reversal-primer.md)
> - [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
> - [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)
> - [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
> - [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
> - [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
> - [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./autoboxing-integercache-null-unboxing-pitfalls.md)
> - [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./floating-point-precision-nan-infinity-serialization-pitfalls.md)

> retrieval-anchor-keywords: comparator utility patterns, java comparator comparing, java comparator comparingint, java comparator comparinglong, java comparator comparingdouble, java comparingInt vs comparing, java comparingLong vs comparing, java comparingDouble vs comparing, java comparator primitive specialization, java comparator primitive shortcut, java comparator boxing overhead, java comparator boxing matters, java comparator boxing ignore, java comparator thenComparing, java comparator thenComparingInt, java comparator thenComparingLong, java comparator thenComparingDouble, java primitive tie breaker comparator, java comparator primitive tie breaker, java comparator tie breaker lambda, java comparator reversed, java comparator reversed placement, java thenComparingInt reversed placement, java thenComparingLong reversed placement, java thenComparingDouble reversed placement, java mixed direction comparator chain, java primitive descending tie breaker, java grade desc id asc comparator, java nullsFirst, java comparator nullsLast, java comparator null reversal, java nullsLast reversed vs reverseOrder, java comparator chaining beginner, java arrays sort comparator chain, java Arrays.sort thenComparing, java object array multi key sort comparator, java beginner multi key sort comparator, java list sort comparator practice, java stream sorted comparator, java list sort vs stream sorted, java primitive field sort comparator, java nullable field sorting java, java wrapper field comparator, java Integer wrapper comparator, java Long wrapper comparator, java Double wrapper comparator, java nullable String comparator, java String.CASE_INSENSITIVE_ORDER nullsLast, beginner comparator examples

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 요약 표](#한-장-요약-표)
- [`comparing`: 첫 정렬 기준 고르기](#comparing-첫-정렬-기준-고르기)
- [`comparingInt`, `comparingLong`, `comparingDouble`: primitive 필드 follow-up](#comparingint-comparinglong-comparingdouble-primitive-필드-follow-up)
- [`thenComparing`: 동점일 때 다음 기준 붙이기](#thencomparing-동점일-때-다음-기준-붙이기)
- [`thenComparingInt`, `thenComparingLong`, `thenComparingDouble`: primitive tie-breaker shortcut](#thencomparingint-thencomparinglong-thencomparingdouble-primitive-tie-breaker-shortcut)
- [`reversed`: 정렬 방향 뒤집기](#reversed-정렬-방향-뒤집기)
- [primitive tie-breaker와 mixed-direction chain](#primitive-tie-breaker와-mixed-direction-chain)
- [`nullsFirst`, `nullsLast`: `null` 위치 먼저 정하기](#nullsfirst-nullslast-null-위치-먼저-정하기)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [코드로 한 번에 보기](#코드로-한-번에-보기)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

`Comparator` 입문 뒤에 바로 나오는 막힘은 대체로 비슷하다.

- `Comparator.comparing(Student::name)`는 알겠는데, 2차 기준은 어떻게 붙일까?
- 1차 기준은 `comparingInt`로 시작했는데, 동점자 기준도 primitive면 다시 custom lambda를 써야 할까?
- 내림차순은 어디에 `reversed()`를 붙여야 할까?
- `null`이 섞이면 왜 바로 `NullPointerException`이 나거나 정렬이 깨질까?
- 이름은 오름차순인데 학년만 내림차순으로 하고 싶으면 어떻게 해야 할까?

핵심은 간단하다.

- `comparing`은 첫 기준을 만든다
- `thenComparing`은 동점자용 추가 기준을 만든다
- primitive tie-breaker면 `thenComparingInt`/`Long`/`Double`도 바로 붙일 수 있다
- `reversed`는 현재 comparator의 방향을 뒤집는다
- `nullsFirst`와 `nullsLast`는 `null`을 어디에 둘지 먼저 정한다

즉 `Comparator` 유틸리티는 "정렬 규칙을 한 번에 다 쓰는 API"가 아니라 **작은 규칙을 조립하는 빌더**라고 보면 이해가 훨씬 쉽다.

## 먼저 잡을 mental model

초보자에게 가장 안전한 기억법은 다음 한 줄이다.

> `comparing`으로 1차 규칙을 만들고, `thenComparing`으로 tie-breaker를 붙이고, 필요하면 `reversed`나 `nullsLast` 같은 옵션으로 모양을 다듬는다.

예를 들어 학생 목록을 정렬한다고 해 보자.

- 이름순으로만 정렬하고 싶다 -> `comparing`
- 학년이 같으면 이름순으로 정렬하고 싶다 -> `thenComparing`
- 학년이 같으면 반 번호나 학생 번호 같은 primitive 필드로 정렬하고 싶다 -> `thenComparingInt`/`thenComparingLong`
- 학년 높은 순으로 보고 싶다 -> `reversed`
- 담당 멘토가 없는 학생(`null`)은 맨 뒤로 보내고 싶다 -> `nullsLast`

이렇게 보면 각 메서드는 새로운 개념이 아니라 "정렬 규칙 조립 부품"이다.

이 감각은 `List.sort(...)`에서만 쓰는 것이 아니다.

- `Arrays.sort(objectArray, comparator)`에도 같은 comparator chain을 그대로 넣을 수 있다
- 배열 primer에서 "점수순, 같으면 이름순" 같은 multi-key sort가 막혔다면 이 문서를 바로 다음 단계로 읽으면 된다

## 한 장 요약 표

| 유틸리티 | 하는 일 | 가장 자주 보는 형태 | 초보자 기억법 |
|---|---|---|---|
| `Comparator.comparing(...)` | 1차 정렬 기준 만들기 | `Comparator.comparing(Student::name)` | "무엇으로 먼저 줄 세울까?" |
| `thenComparing(...)` | 동점일 때 다음 기준 추가 | `.thenComparing(Student::name)` | "같으면 한 번 더 비교" |
| `reversed()` | 현재 comparator 방향 뒤집기 | `.reversed()` | "오름차순을 내림차순으로 뒤집기" |
| `nullsFirst(...)` | `null`을 앞에 두기 | `Comparator.nullsFirst(Comparator.naturalOrder())` | "빈 값 먼저" |
| `nullsLast(...)` | `null`을 뒤에 두기 | `Comparator.nullsLast(Comparator.naturalOrder())` | "빈 값 나중" |

## `comparing`: 첫 정렬 기준 고르기

`comparing`은 "이 필드를 기준으로 먼저 줄 세워라"라는 뜻이다.

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

record Student(String name, int grade, String mentorName) {}

List<Student> students = new ArrayList<>(List.of(
        new Student("Mina", 2, "Nora"),
        new Student("Ari", 1, null),
        new Student("Joon", 2, "Ari")
));

students.sort(Comparator.comparing(Student::name));
System.out.println(students);
```

정렬 결과는 이름 오름차순이다.

```java
[Student[name=Ari, grade=1, mentorName=null],
 Student[name=Joon, grade=2, mentorName=Ari],
 Student[name=Mina, grade=2, mentorName=Nora]]
```

여기서 중요한 감각은 하나다.

- `Comparator.comparing(Student::name)`은 "`Student` 전체"를 비교하는 게 아니라, 먼저 `name`을 꺼내서 그 값을 기준으로 비교한다

즉 `String`, `Integer`, `LocalDate`처럼 natural ordering이 있는 필드를 기준으로 정렬할 때 가장 많이 쓰는 출발점이 `comparing`이다.

## `comparingInt`, `comparingLong`, `comparingDouble`: primitive 필드 follow-up

처음 보면 이름이 많아서 복잡해 보이지만 기억법은 단순하다.

> `comparing(...)`의 primitive 전용 shortcut이 `comparingInt`, `comparingLong`, `comparingDouble`이다.

즉 "정렬 규칙"은 같고, 차이는 **getter가 primitive를 바로 꺼내는지**에 있다.

| 메서드 | 이런 필드에 자주 쓴다 | 초보자 기억법 |
|---|---|---|
| `Comparator.comparingInt(...)` | `int grade`, `int score`, `int age` | "int를 바로 비교" |
| `Comparator.comparingLong(...)` | `long id`, `long createdAtEpoch` | "long을 바로 비교" |
| `Comparator.comparingDouble(...)` | `double average`, `double distance` | "double을 바로 비교" |

예를 들어 학년이 `int` 필드라면 이렇게 쓴다.

```java
Comparator<Student> byGrade =
        Comparator.comparingInt(Student::grade);
```

같은 정렬 규칙을 일반 `comparing(...)`로 쓰면 이런 느낌이다.

```java
Comparator<Student> byGradeBoxed =
        Comparator.comparing(Student::grade);

Comparator<Student> byGradePrimitive =
        Comparator.comparingInt(Student::grade);
```

둘 다 "학년 오름차순"이라는 뜻으로 읽어도 된다.
초보자 기준에서 먼저 볼 차이는 "primitive를 바로 비교하느냐, 잠깐 `Integer` boxing을 거치느냐"다.

### 먼저 외울 한 줄 판단

> primitive `int`/`long`/`double`이고 `null`이 없으면 `comparingInt`/`Long`/`Double`을 기본값처럼 쓰고, 그 외에는 `comparing(...)`부터 생각해도 충분하다.

### boxing이 언제 의미 있고, 언제 무시해도 되나

## `comparingInt`, `comparingLong`, `comparingDouble`: primitive 필드 follow-up (계속 2)

| 상황 | 초보자용 추천 | 왜 이렇게 보면 되나 |
|---|---|---|
| `int`/`long`/`double` 필드를 큰 컬렉션에서 자주 정렬한다 | `comparingInt`/`Long`/`Double` 우선 | boxing을 줄이는 방향이라 성능 감각상 자연스럽다 |
| stream `sorted`, `max`, `min`처럼 값을 계속 꺼내 비교한다 | primitive specialization 우선 | 같은 값 추출과 비교가 많이 반복된다 |
| 화면용 작은 리스트를 한두 번 정렬한다 | boxing은 일단 무시 가능 | 병목보다 "정렬 규칙이 바로 읽히는가"가 더 중요하다 |
| 필드가 `Integer`/`Long`/`Double`이거나 `null`이 올 수 있다 | `comparing(...)` + `nullsFirst`/`nullsLast` 우선 | primitive specialization은 `null` 다루기가 불편하거나 위험하다 |

즉 `comparingInt`류는 "무조건 미세 최적화"가 아니라, **primitive 필드를 정렬할 때 자연스러운 기본 선택지** 정도로 이해하면 충분하다.

### boxing이 신경 쓰일 때

- 큰 리스트를 자주 정렬하는 hot path일 때
- stream, sort, aggregation처럼 같은 값을 아주 많이 꺼내 비교할 때
- 이미 성능 측정을 해 봤고 allocation/GC가 보일 때

이럴 때는 primitive specialization이 "쓸 수 있으면 쓰는 편이 자연스럽다" 정도로 이해하면 충분하다.

### boxing을 무시해도 되는 때

- 리스트가 작고 한두 번 정렬하는 화면/관리자 코드일 때
- 아직 병목을 측정하지 않았고 가독성이 더 중요한 초급 단계일 때
- 어차피 비교 대상이 `Integer`, `Long`, `Double` 같은 wrapper거나 `null` 가능성이 있을 때

즉 초보자용 실전 규칙은 이렇다.

- 필드가 primitive이고 `null`이 될 수 없으면 `comparingInt`/`Long`/`Double`을 먼저 떠올린다
- 필드가 wrapper거나 `null` 가능성이 있으면 `comparing(...)` + `nullsFirst`/`nullsLast` 쪽이 더 안전하다
- 작은 코드에서는 boxing보다 "정렬 기준이 읽히는가"가 더 중요할 수 있다
- `comparingDouble`을 쓴다고 해서 부동소수점 반올림/`NaN` 문제가 사라지는 것은 아니다. 그 부분은 [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./floating-point-precision-nan-infinity-serialization-pitfalls.md)에서 따로 보면 된다.

같은 감각으로 tie-breaker도 `thenComparingInt`, `thenComparingLong`, `thenComparingDouble`을 붙일 수 있다.

## `thenComparing`: 동점일 때 다음 기준 붙이기

배열 정렬 primer에서 본 "`score` 오름차순, 같으면 `name` 오름차순" 예시를 `Student[]`나 `List<Student>`에 옮기면, 그 "같으면 한 번 더 비교"를 코드로 적는 자리가 바로 `thenComparing`이다.

정렬하다 보면 1차 기준만으로는 부족한 경우가 많다.

예를 들어 학년순으로 정렬하면 같은 학년 학생이 여러 명 생긴다.
이럴 때 `thenComparing`으로 2차 기준을 붙인다.

```java
List<Student> students = new ArrayList<>(List.of(
        new Student("Mina", 2, "Nora"),
        new Student("Ari", 1, null),
        new Student("Joon", 2, "Ari"),
        new Student("Bora", 2, null)
));

students.sort(
        Comparator.comparing(Student::grade)
                .thenComparing(Student::name)
);

System.out.println(students);
```

결과는 다음 순서다.

```java
[Student[name=Ari, grade=1, mentorName=null],
 Student[name=Bora, grade=2, mentorName=null],
 Student[name=Joon, grade=2, mentorName=Ari],
 Student[name=Mina, grade=2, mentorName=Nora]]
```

읽는 법은 단순하다.

1. 먼저 `grade`로 비교한다.
2. `grade`가 같으면 그때 `name`으로 다시 비교한다.

초보자 관점에서는 `thenComparing`을 "**동점자 처리 규칙**"이라고 기억하면 가장 쉽다.

## `thenComparingInt`, `thenComparingLong`, `thenComparingDouble`: primitive tie-breaker shortcut

동점자 기준도 primitive 필드라면 `thenComparing(...)` 대신 더 짧고 읽기 쉬운 primitive shortcut을 그대로 이어 붙이면 된다.

> 이미 만든 comparator 체인 뒤에 primitive tie-breaker를 하나 더 붙이는 도구가 `thenComparingInt`/`thenComparingLong`/`thenComparingDouble`이다.

| 메서드 | 이런 tie-breaker에 자주 쓴다 | 읽는 법 |
|---|---|---|
| `thenComparingInt(...)` | `int classNumber`, `int age`, `int round` | "앞 기준이 같으면 int로 한 번 더 비교" |
| `thenComparingLong(...)` | `long studentId`, `long createdAtEpoch` | "앞 기준이 같으면 long으로 한 번 더 비교" |
| `thenComparingDouble(...)` | `double average`, `double distance` | "앞 기준이 같으면 double로 한 번 더 비교" |

예를 들어 학생 랭킹을 다음처럼 갖고 있다고 해 보자.

```java
record StudentRank(
        String name,
        int grade,
        int classNumber,
        long studentId,
        double averageScore
) {}
```

각 shortcut은 이렇게 읽으면 된다.

```java
Comparator<StudentRank> byGradeThenClassNumber =
        Comparator.comparingInt(StudentRank::grade)
                .thenComparingInt(StudentRank::classNumber);

Comparator<StudentRank> byGradeThenStudentId =
        Comparator.comparingInt(StudentRank::grade)
                .thenComparingLong(StudentRank::studentId);

Comparator<StudentRank> byGradeThenAverageScore =
        Comparator.comparingInt(StudentRank::grade)
                .thenComparingDouble(StudentRank::averageScore)
                .thenComparing(StudentRank::name);
```

- 첫 번째는 "학년순, 같은 학년이면 반 번호순"이다.
- 두 번째는 "학년순, 같은 학년이면 학생 번호순"이다.
- 세 번째는 "학년순, 같은 학년이면 평균 점수순, 그래도 같으면 이름순"이다.

여기서 중요한 감각은 하나다.

## `thenComparingInt`, `thenComparingLong`, `thenComparingDouble`: primitive tie-breaker shortcut (계속 2)

- 1차 기준이 primitive shortcut이었으면 2차 기준도 같은 방식으로 계속 붙일 수 있다
- 첫 기준이 `comparing(...)`였더라도 2차 기준은 `thenComparingInt`/`Long`/`Double`로 붙일 수 있다
- 즉 "primitive tie-breaker니까 다시 verbose lambda로 풀어써야 하나?"라고 생각할 필요가 없다

### custom lambda로 돌아가지 않아도 된다

초보자가 자주 쓰는 우회는 이런 형태다.

```java
Comparator<StudentRank> verbose =
        (left, right) -> {
            int result = Integer.compare(left.grade(), right.grade());
            if (result != 0) {
                return result;
            }
            return Long.compare(left.studentId(), right.studentId());
        };
```

같은 규칙을 comparator utility로 쓰면 더 짧고 의도가 바로 보인다.

```java
Comparator<StudentRank> fluent =
        Comparator.comparingInt(StudentRank::grade)
                .thenComparingLong(StudentRank::studentId);
```

입문 단계에서는 이 차이를 "고급 최적화"보다 **정렬 기준이 문장처럼 읽히는가**로 보면 충분하다.

## `reversed`: 정렬 방향 뒤집기

`comparing` 기본 방향은 오름차순이다.
내림차순이 필요하면 `reversed()`를 붙인다.

```java
List<Student> students = new ArrayList<>(List.of(
        new Student("Mina", 2, "Nora"),
        new Student("Ari", 1, null),
        new Student("Joon", 2, "Ari"),
        new Student("Bora", 2, null)
));

students.sort(
        Comparator.comparing(Student::grade)
                .reversed()
                .thenComparing(Student::name)
);

System.out.println(students);
```

이 코드는 "학년은 높은 순, 같은 학년 안에서는 이름 오름차순"이다.

```java
[Student[name=Bora, grade=2, mentorName=null],
 Student[name=Joon, grade=2, mentorName=Ari],
 Student[name=Mina, grade=2, mentorName=Nora],
 Student[name=Ari, grade=1, mentorName=null]]
```

### `reversed()`는 붙이는 위치가 중요하다

다음 두 코드는 비슷해 보이지만 의미가 다르다.

```java
Comparator<Student> gradeDescNameAsc =
        Comparator.comparing(Student::grade)
                .reversed()
                .thenComparing(Student::name);

Comparator<Student> wholeChainReversed =
        Comparator.comparing(Student::grade)
                .thenComparing(Student::name)
                .reversed();
```

- 첫 번째는 학년만 내림차순이고, 이름 tie-breaker는 오름차순이다
- 두 번째는 연결된 전체 규칙이 뒤집혀서 이름도 내림차순 쪽으로 바뀐다

초보자용 안전 규칙은 이렇다.

- "첫 기준만 뒤집고 싶다"면 그 기준 직후에 `reversed()`
- "전체 순서를 통째로 뒤집고 싶다"면 맨 끝에 `reversed()`

### primitive tie-breaker와 mixed-direction chain

`reversed()`는 "지금까지 만든 comparator"를 뒤집는다.
그래서 `thenComparingInt`/`Long`/`Double`과 섞을 때는 "어느 시점까지 만든 규칙을 뒤집었는가"를 같이 읽어야 한다.

## `reversed`: 정렬 방향 뒤집기 (계속 2)

| 코드 | 읽는 결과 |
|---|---|
| `Comparator.comparingInt(StudentRank::grade).reversed().thenComparingInt(StudentRank::classNumber)` | 학년 내림차순, 같은 학년이면 반 번호 오름차순 |
| `Comparator.comparingInt(StudentRank::grade).reversed().thenComparingLong(StudentRank::studentId)` | 학년 내림차순, 같은 학년이면 학생 번호 오름차순 |
| `Comparator.comparingInt(StudentRank::grade).reversed().thenComparingDouble(StudentRank::averageScore)` | 학년 내림차순, 같은 학년이면 평균 점수 오름차순 |
| `Comparator.comparingInt(StudentRank::grade).thenComparingLong(StudentRank::studentId).reversed()` | 학년도 학생 번호도 함께 뒤집힌 전체 내림차순 |

짧게 기억하면 이렇다.

- 앞에서 한 번 `reversed()`를 했더라도, 그 뒤에 붙는 `thenComparingInt`/`Long`/`Double`은 기본이 오름차순이다.
- 즉 `grade`만 내림차순이고 primitive tie-breaker는 오름차순인 mixed-direction chain은 `reversed()` 뒤에 shortcut을 그대로 붙이면 된다.
- primitive tie-breaker 자체도 내림차순으로 만들고 싶다면 shortcut 끝에 `reversed()`를 붙이는 것이 아니라 `thenComparing(Comparator.comparingInt(...).reversed())`처럼 범위를 좁혀야 한다.
- 같은 패턴으로 `int`는 `comparingInt`, `long`은 `comparingLong`, `double`은 `comparingDouble`을 `thenComparing(...)` 안에 넣어 뒤집으면 된다.

예를 들어 "학년은 높은 순, 같은 학년이면 평균 점수도 높은 순"이라면 이렇게 쓴다.

```java
Comparator<StudentRank> gradeDescAverageDesc =
        Comparator.comparingInt(StudentRank::grade)
                .reversed()
                .thenComparing(
                        Comparator.comparingDouble(StudentRank::averageScore)
                                .reversed()
                );
```

반대로 아래 코드는 전체 체인을 뒤집기 때문에 읽는 결과가 다르다.

## `reversed`: 정렬 방향 뒤집기 (계속 3)

```java
Comparator<StudentRank> wholeChainDesc =
        Comparator.comparingInt(StudentRank::grade)
                .thenComparingDouble(StudentRank::averageScore)
                .reversed();
```

## `nullsFirst`, `nullsLast`: `null` 위치 먼저 정하기

정렬 대상에 `null`이 섞이면 규칙을 먼저 정해야 한다.
안 그러면 비교 도중 예외가 나거나 의도가 불분명해진다.

가장 단순한 예시는 `String` 리스트다.

```java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

List<String> mentors = new ArrayList<>(Arrays.asList(
        "Nora", null, "Ari", null, "Mina"
));

mentors.sort(Comparator.nullsFirst(Comparator.naturalOrder()));
System.out.println(mentors); // [null, null, Ari, Mina, Nora]
```

`null`을 맨 뒤로 보내고 싶다면 `nullsLast`를 쓴다.

```java
List<String> mentors = new ArrayList<>(Arrays.asList(
        "Nora", null, "Ari", null, "Mina"
));

mentors.sort(Comparator.nullsLast(Comparator.naturalOrder()));
System.out.println(mentors); // [Ari, Mina, Nora, null, null]
```

### nullable 필드를 정렬할 때

실무에서는 "객체 자체가 `null`"인 경우보다 "필드 하나가 `null`"인 경우가 더 자주 나온다.

```java
List<Student> students = new ArrayList<>(List.of(
        new Student("Mina", 2, "Nora"),
        new Student("Ari", 1, null),
        new Student("Joon", 2, "Ari"),
        new Student("Bora", 2, null)
));

students.sort(
        Comparator.comparing(
                Student::mentorName,
                Comparator.nullsLast(Comparator.naturalOrder())
        ).thenComparing(Student::name)
);

System.out.println(students);
```

이 코드는 다음처럼 읽으면 된다.

- 먼저 `mentorName`으로 정렬한다
- `mentorName`이 `null`이면 맨 뒤로 보낸다
- `mentorName`까지 같으면 `name`으로 정렬한다

결과적으로 멘토 이름이 있는 학생이 먼저 오고, 멘토 정보가 없는 학생은 뒤로 밀린다.

## 초보자가 자주 헷갈리는 지점

- `comparing`은 기본이 오름차순이다. 내림차순이 필요하면 `reversed()`를 별도로 붙여야 한다.
- `comparing(Student::grade)`와 `comparingInt(Student::grade)`는 보통 같은 순서를 만든다. 차이는 주로 boxing 여부다.
- `comparingInt`/`Long`/`Double`은 "primitive 필드에서 기본으로 떠올리면 좋은 shortcut"이지, 모든 작은 코드에서 성능 집착을 해야 한다는 뜻은 아니다.
- `comparingInt`, `comparingLong`, `comparingDouble`은 primitive 전용이라 `null`을 직접 다루지 못한다. nullable 필드는 `comparing(...)` 쪽이 더 안전하다.
- `comparingDouble`은 comparator 선택 문제이고, 부동소수점 정밀도 문제 자체를 해결하는 도구는 아니다.
- `thenComparing`은 2차 기준이 아니라 "1차 기준이 같을 때만 쓰는 기준"이다.
- `thenComparingInt`/`Long`/`Double`도 똑같이 "앞 기준이 같을 때만" 동작한다. 첫 비교를 건너뛰는 별도 정렬이 아니다.
- 첫 기준이 `comparing(Student::name)`처럼 object comparator여도, 다음 기준은 `thenComparingInt(Student::grade)`처럼 primitive shortcut으로 섞어 쓸 수 있다.
- `Comparator.comparingInt(...).reversed().thenComparingInt(...)`는 "첫 기준만 내림차순, tie-breaker는 오름차순"이다. 뒤의 primitive tie-breaker까지 내림차순으로 만들고 싶다면 `thenComparing(Comparator.comparingInt(...).reversed())`처럼 따로 감싸야 한다.
- `a.thenComparing(b).reversed()`는 전체 체인을 뒤집는다. `a.reversed().thenComparing(b)`와 다르다.
- `nullsFirst`와 `nullsLast`는 "`null`을 어디에 둘지"를 정하는 도구다. 문자열 사전순 자체를 바꾸는 도구는 아니다.
- `List.of(...)`는 `null`을 허용하지 않는다. `null` 예제는 `Arrays.asList(...)`나 별도 `ArrayList`로 만들어야 한다.

## 초보자가 자주 헷갈리는 지점 (계속 2)

- `TreeSet`이나 `TreeMap`에 comparator를 넣을 때는 `thenComparing`으로 tie-breaker를 충분히 넣지 않으면 서로 다른 객체가 같은 원소나 같은 key처럼 보일 수 있다. 이 부분은 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md), [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md), [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)에서 이어서 보면 된다.

## 코드로 한 번에 보기

```java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

public class ComparatorUtilityPatternsExample {
    private record Student(String name, int grade, String mentorName) {}

    public static void main(String[] args) {
        List<Student> students = new ArrayList<>(List.of(
                new Student("Mina", 2, "Nora"),
                new Student("Ari", 1, null),
                new Student("Joon", 2, "Ari"),
                new Student("Bora", 2, null)
        ));

        students.sort(Comparator.comparing(Student::name));
        System.out.println(students);

        students = new ArrayList<>(List.of(
                new Student("Mina", 2, "Nora"),
                new Student("Ari", 1, null),
                new Student("Joon", 2, "Ari"),
                new Student("Bora", 2, null)
        ));
        students.sort(
                Comparator.comparing(Student::grade)
                        .thenComparing(Student::name)
        );
        System.out.println(students);

        students = new ArrayList<>(List.of(
                new Student("Mina", 2, "Nora"),
                new Student("Ari", 1, null),
                new Student("Joon", 2, "Ari"),
                new Student("Bora", 2, null)
        ));
        students.sort(
                Comparator.comparing(Student::grade)
                        .reversed()
                        .thenComparing(Student::name)
        );

## 코드로 한 번에 보기 (계속 2)

System.out.println(students);

        students = new ArrayList<>(List.of(
                new Student("Mina", 2, "Nora"),
                new Student("Ari", 1, null),
                new Student("Joon", 2, "Ari"),
                new Student("Bora", 2, null)
        ));
        students.sort(
                Comparator.comparing(
                        Student::mentorName,
                        Comparator.nullsLast(Comparator.naturalOrder())
                ).thenComparing(Student::name)
        );
        System.out.println(students);

        List<String> mentors = new ArrayList<>(Arrays.asList(
                "Nora", null, "Ari", null, "Mina"
        ));
        mentors.sort(Comparator.nullsFirst(Comparator.naturalOrder()));
        System.out.println(mentors);
    }
}
```

연습할 때는 한 줄씩 바꿔 보는 게 좋다.

- `Student::grade`를 `Student::name`으로 바꾸기
- `nullsLast`를 `nullsFirst`로 바꾸기
- `reversed()` 위치를 바꿔서 결과 차이 확인하기

## 빠른 체크리스트

- 한 필드 기준 정렬이면 `Comparator.comparing(...)`
- primitive `int`/`long`/`double` 필드면 `Comparator.comparingInt(...)`, `comparingLong(...)`, `comparingDouble(...)`도 먼저 후보에 둔다
- 동점 처리까지 필요하면 `.thenComparing(...)`, primitive tie-breaker면 `.thenComparingInt(...)`/`Long(...)`/`Double(...)`
- 내림차순이면 `.reversed()`
- `null`이 섞이면 `Comparator.nullsFirst(...)` 또는 `Comparator.nullsLast(...)`
- `reversed()` 위치가 전체 체인을 뒤집는지, 일부 기준만 뒤집는지 항상 확인
- `TreeSet`/`TreeMap`에 넣을 comparator는 tie-breaker 부족으로 `compare == 0`이 너무 쉽게 나오지 않는지 점검

## 어떤 문서를 다음에 읽으면 좋은가

- `Comparable`과 `Comparator`의 큰 그림을 먼저 다시 묶고 싶다면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- `a.reversed().thenComparing(b)`와 `a.thenComparing(b).reversed()` 차이만 작게 집중해서 보고 싶다면 [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
- nullable `String` sort key에서 `String.CASE_INSENSITIVE_ORDER`, `nullsLast`, tie-breaker를 함께 읽고 싶다면 [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)
- `Integer`/`Long`/`Double` wrapper 필드가 있을 때 `nullsFirst`/`nullsLast`를 어떤 감각으로 붙여야 하는지 좁혀 보고 싶다면 [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
- 배열 정렬과 comparator precondition을 같이 보고 싶다면 [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
- 정렬된 컬렉션에서 comparator가 중복 판단에 어떻게 연결되는지 보려면 [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- `TreeSet`/`TreeMap`에서 tie-breaker 부족이 왜 값 손실처럼 보이는지 보려면 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- 같은 comparator chain을 `List.sort(...)`와 `stream.sorted(...)` 양쪽에 어떻게 재사용하는지 보고 싶다면 [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- stream pipeline의 `sorted(comparator)` 위치까지 넓게 연결하고 싶다면 [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
- boxing/unboxing 자체를 더 정확히 보고 싶다면 [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./autoboxing-integercache-null-unboxing-pitfalls.md)

## 어떤 문서를 다음에 읽으면 좋은가 (계속 2)

- `double` 정렬에서 정밀도나 `NaN`까지 같이 떠오른다면 [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./floating-point-precision-nan-infinity-serialization-pitfalls.md)

## 한 줄 정리

`Comparator` 유틸리티는 외워야 할 독립 기능 묶음이 아니라 "`comparing`으로 시작해서 `thenComparing`, `reversed`, `nullsLast` 같은 부품을 이어 붙여 원하는 정렬 규칙을 조립하는 방식"으로 이해하면 가장 빠르게 손에 익는다.
