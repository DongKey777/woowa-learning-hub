# Comparator Reversed Scope Primer

> 한 줄 요약: `reversed()`는 "다음 필드만" 뒤집는 버튼이 아니라, **그 시점까지 만든 comparator 전체**를 뒤집는다. 그래서 `a.reversed().thenComparing(b)`와 `a.thenComparing(b).reversed()`는 비슷해 보여도 다른 규칙이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: comparator reversed scope primer, java comparator reversed scope, comparator reversed 어디 붙여요, comparator reversed 왜 전체가 뒤집혀요, thencomparing 뒤 reversed 차이, a.reversed thencomparing b, a.thencomparing b reversed, 정렬 기준 하나만 내림차순, 학년 내림차순 이름 오름차순 comparator, 학년도 이름도 내림차순 comparator, comparator chain whole vs single field, comparator 큰 그림 reversed scope, 처음 배우는데 comparator reversed, comparator 체인 뒤집기 기초, java comparator reversed beginner
> 관련 문서:
> - [Language README](../README.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
> - [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
> - [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)

> retrieval-anchor-keywords: comparator reversed scope primer, java comparator reversed scope, java reversed whole chain comparator, java whole chain reversed comparator, java single field reversed comparator, java comparator reversed placement beginner, java reversed thenComparing scope, java a reversed thenComparing b, java a thenComparing b reversed, whole chain vs single field reversed, java grade desc name asc comparator, java grade desc name desc comparator, java tie breaker descending comparator, java comparator mixed direction beginner, java reversed comparator chain beginner, java comparator reversed small example, java beginner comparator reversed confusion, reversed가 왜 tie-breaker까지 뒤집혀요, 정렬 기준 하나만 뒤집고 싶어요, compare chain 전체 reversed 차이, java treeset reversed comparator distinctness, java treeset reversed comparator compare zero

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 비교 표](#한-장-비교-표)
- [작은 예제로 whole-chain vs single-field 보기](#작은-예제로-whole-chain-vs-single-field-보기)
- [`TreeSet`에서는 distinctness도 바뀔까](#treeset에서는-distinctness도-바뀔까)
- [tie-breaker도 내림차순으로 만들고 싶을 때](#tie-breaker도-내림차순으로-만들고-싶을-때)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

`Comparator`를 막 배우면 `reversed()`에서 자주 막힌다.

- `reversed()`를 어디에 붙여야 첫 기준만 내림차순이 될까?
- `thenComparing(...)`까지 쓴 뒤 맨 끝에 `reversed()`를 붙이면 무엇이 뒤집힐까?
- "학년은 높은 순, 이름은 오름차순"과 "학년도 이름도 모두 내림차순"을 어떻게 구분할까?

핵심은 메서드 이름이 아니라 **적용 범위(scope)** 다.

> `reversed()`는 그 줄의 "다음 필드"를 뒤집는 것이 아니라, 호출 시점까지 만들어진 comparator를 뒤집는다.

이 한 줄만 잡히면 whole-chain vs single-field 차이가 훨씬 단순해진다.

## 먼저 잡을 mental model

초보자에게 가장 안전한 기억법은 다음 두 줄이다.

- `a.reversed().thenComparing(b)`는 "`a`만 뒤집고, 그 다음 `b`를 새로 붙인다"
- `a.thenComparing(b).reversed()`는 "`a`와 `b`를 묶은 전체 체인"을 뒤집는다

즉 `reversed()`는 **필드에 붙는 장식**이 아니라 **지금까지 만든 comparator 객체에 적용되는 연산**이다.

## 한 장 비교 표

| 코드 | 실제 의미 | 같은 학년 안 이름 방향 |
|---|---|---|
| `Comparator.comparingInt(Student::grade).reversed().thenComparing(Student::name)` | 학년 내림차순, 같은 학년이면 이름 오름차순 | 오름차순 |
| `Comparator.comparingInt(Student::grade).thenComparing(Student::name).reversed()` | 학년 내림차순, 같은 학년이면 이름도 내림차순 | 내림차순 |
| `Comparator.comparingInt(Student::grade).reversed().thenComparing(Comparator.comparingInt(Student::score).reversed())` | 학년 내림차순, 같은 학년이면 점수도 내림차순 | tie-breaker도 따로 내림차순 |

짧게 읽으면 이렇다.

- `reversed()`를 일찍 붙이면 앞에서 만든 일부 규칙만 뒤집힌다
- `reversed()`를 맨 끝에 붙이면 지금까지 만든 전체 규칙이 뒤집힌다

## 작은 예제로 whole-chain vs single-field 보기

```java
import java.util.Comparator;
import java.util.List;

record Student(String name, int grade, int score) {}

List<Student> students = List.of(
        new Student("Mina", 2, 90),
        new Student("Bora", 2, 95),
        new Student("Joon", 2, 85),
        new Student("Ari", 1, 99)
);
```

먼저 "학년은 높은 순, 같은 학년이면 이름 오름차순"을 만들고 싶다면 `reversed()`를 첫 comparator 뒤에 둔다.

```java
Comparator<Student> gradeDescNameAsc =
        Comparator.comparingInt(Student::grade)
                .reversed()
                .thenComparing(Student::name);
```

결과를 짧게 쓰면 다음 순서다.

```java
[Bora(2), Joon(2), Mina(2), Ari(1)]
```

왜 이렇게 될까?

- `Comparator.comparingInt(Student::grade).reversed()` 시점에는 "학년 비교"만 존재한다
- 그래서 뒤집히는 것도 학년 기준뿐이다
- 그 뒤에 붙인 `thenComparing(Student::name)`은 새로 추가된 tie-breaker라서 기본 오름차순으로 읽힌다

이번에는 비슷해 보이지만 `reversed()`를 맨 끝에 붙여 보자.

```java
Comparator<Student> wholeChainReversed =
        Comparator.comparingInt(Student::grade)
                .thenComparing(Student::name)
                .reversed();
```

결과는 이렇게 달라진다.

```java
[Mina(2), Joon(2), Bora(2), Ari(1)]
```

이번에는 이름 방향까지 바뀌었다.

- 맨 끝에 도달했을 때는 이미 `grade -> name` 체인이 완성돼 있다
- 그래서 `reversed()`가 그 체인 전체를 뒤집는다
- 즉 "학년 내림차순, 같은 학년이면 이름 내림차순"이 된다

## `TreeSet`에서는 distinctness도 바뀔까

여기서 초보자가 한 번 더 헷갈리는 지점이 있다.

> `a.reversed().thenComparing(b)`와 `a.thenComparing(b).reversed()`는 순서는 바꾸지만, `TreeSet`의 중복 판정 자체는 보통 바꾸지 않는다.

```java
import java.util.Comparator;
import java.util.Set;
import java.util.TreeSet;

record Student(long id, String name, int grade) {}

Comparator<Student> gradeDescNameAsc =
        Comparator.comparingInt(Student::grade)
                .reversed()
                .thenComparing(Student::name);

Comparator<Student> wholeChainReversed =
        Comparator.comparingInt(Student::grade)
                .thenComparing(Student::name)
                .reversed();

Student mina = new Student(1L, "Mina", 2);
Student bora = new Student(2L, "Bora", 2);
Student ari = new Student(3L, "Ari", 1);

Set<Student> left = new TreeSet<>(gradeDescNameAsc);
Set<Student> right = new TreeSet<>(wholeChainReversed);

left.add(mina);
left.add(bora);
left.add(ari);

right.add(mina);
right.add(bora);
right.add(ari);

System.out.println(left.size());  // 3
System.out.println(right.size()); // 3
```

왜 둘 다 `3`일까?

- 두 comparator 모두 "학년이 같고 이름도 같을 때만" `compare(...) == 0`이 된다.
- `reversed()`는 비교 방향만 뒤집지, `0`을 다른 값으로 바꾸지 않는다.
- 그래서 `TreeSet` 기준 distinctness는 그대로고, 화면에 보이는 순서만 달라진다.

즉 `TreeSet` 크기까지 바꾸고 싶다면 `reversed()` 위치를 바꾸는 것이 아니라, `thenComparing(...)`으로 어떤 필드까지 구분할지를 바꿔야 한다.

## tie-breaker도 내림차순으로 만들고 싶을 때

여기서 초보자가 가장 자주 하는 실수는 이 패턴이다.

```java
Comparator<Student> gradeDescScoreAsc =
        Comparator.comparingInt(Student::grade)
                .reversed()
                .thenComparingInt(Student::score);
```

이 코드는 "학년 내림차순, 같은 학년이면 점수 오름차순"이다.
`reversed()`를 한 번 썼다고 해서 나중 tie-breaker까지 자동으로 내림차순이 되지 않는다.

점수 tie-breaker도 따로 내림차순으로 만들고 싶다면 범위를 좁혀서 뒤집어야 한다.

```java
Comparator<Student> gradeDescScoreDesc =
        Comparator.comparingInt(Student::grade)
                .reversed()
                .thenComparing(
                        Comparator.comparingInt(Student::score)
                                .reversed()
                );
```

| 코드 | 같은 학년 안 점수 방향 |
|---|---|
| `...reversed().thenComparingInt(Student::score)` | 오름차순 |
| `...reversed().thenComparing(Comparator.comparingInt(Student::score).reversed())` | 내림차순 |

핵심은 다음 한 줄이다.

> "첫 기준만 뒤집기"와 "tie-breaker도 따로 뒤집기"는 다른 작업이다.

## 초보자 혼동 포인트

- `reversed()`는 필드 이름에 붙는 것이 아니라, 그 시점까지 만든 comparator에 붙는다.
- `a.reversed().thenComparing(b)`와 `a.thenComparing(b).reversed()`는 같은 뜻이 아니다.
- 앞에서 한 번 `reversed()`를 써도, 뒤에 붙는 `thenComparing(...)`과 `thenComparingInt(...)`는 기본이 다시 오름차순이다.
- tie-breaker만 내림차순으로 만들고 싶다면 `thenComparing(Comparator.comparingInt(...).reversed())`처럼 그 비교기만 따로 감싸야 한다.
- `null`까지 섞인 정렬에서는 `nullsLast(...).reversed()`가 `null` 위치도 함께 뒤집을 수 있다. 이 경우는 [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)에서 따로 보는 편이 안전하다.

## 어떤 문서를 다음에 읽으면 좋은가

- `Comparable`, natural ordering, `Comparator` 큰 그림을 먼저 다시 묶고 싶다면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- `comparingInt`, `thenComparingInt`, `nullsLast`까지 포함해 comparator 조립 전체를 연습하고 싶다면 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- 같은 comparator chain을 `List.sort(...)`와 `stream.sorted(...)`에 어떻게 재사용하는지 보려면 [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- `null` 가능한 wrapper 필드까지 포함해 내림차순 범위를 더 정확히 보려면 [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
- `TreeSet`/`TreeMap`에서 comparator chain이 distinctness까지 바꾸는 모습을 보려면 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)

## 한 줄 정리

`reversed()`는 "다음 필드"가 아니라 "지금까지 만든 comparator"를 뒤집기 때문에, single-field 내림차순과 whole-chain 내림차순을 구분하려면 **어느 지점에서 `reversed()`를 호출했는지**를 먼저 읽어야 한다.
