# Comparable and Comparator Basics

> 한 줄 요약: Java 입문자가 `Comparable`/`Comparator`를 정렬 도구로만 보지 않고, `TreeSet`/`TreeMap`에서 `equals()`/`hashCode()`와 다른 규칙으로 "같은 자리"를 만들 수 있다는 점까지 한 흐름으로 이해하도록 정리한 beginner companion doc이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java comparable comparator basics basics, java comparable comparator basics beginner, java comparable comparator basics intro, java basics, beginner java, 처음 배우는데 java comparable comparator basics, java comparable comparator basics 입문, java comparable comparator basics 기초, what is java comparable comparator basics, how to java comparable comparator basics
> 관련 문서:
> - [Language README](../README.md)
> - [자바 언어의 구조와 기본 문법](./java-language-basics.md)
> - [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
> - [`List.sort` vs `Collections.sort` 미니 브리지](./list-sort-vs-collections-sort-mini-bridge.md)
> - [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
> - [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
> - [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
> - [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)
> - [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
> - [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Beginner Drill Sheet: Equality vs Ordering](./equality-vs-ordering-beginner-drill-sheet.md)
> - [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
> - [Priority Update Patterns](./priority-update-patterns-treeset-treemap-priorityqueue-bridge.md)
> - [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md)
> - [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
> - [Java Collections 성능 감각](./collections-performance.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
> - [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)

> retrieval-anchor-keywords: java comparable basics, java comparator basics, natural ordering, custom comparator, java compareto basics, java compare method basics, java sorting beginner, java list sort comparator, java stream sorted comparator, java treeset comparator equals consistency, java treemap comparator equals consistency, java compareto equals consistency, java compareto returning 0, java sorted collection duplicate surprise, java treeset natural ordering duplicate, java treemap natural ordering replace value, compareto treeset treemap bridge, what is comparable java, why treeset size is 1, 처음 배우는데 comparable comparator, compareto comparator 언제 쓰는지, compare 0 equals 불일치, treeset compareto 0 중복 이유, treemap compareto 0 덮어쓰기

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [`Comparable`과 `Comparator`를 먼저 한 장으로 보기](#comparable과-comparator를-먼저-한-장으로-보기)
- [natural ordering과 `Comparable`](#natural-ordering과-comparable)
- [custom ordering과 `Comparator`](#custom-ordering과-comparator)
- [`equals()`와 일관성은 왜 중요할까](#equals와-일관성은-왜-중요할까)
- [Comparator 일관성 체크 카드](#comparator-일관성-체크-카드)
- [코드로 한 번에 보기](#코드로-한-번에-보기)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문자가 정렬을 배우면서 자주 막히는 질문은 대체로 비슷하다.

- 어떤 클래스는 왜 그냥 `Collections.sort(list)`가 되는데, 어떤 클래스는 안 될까?
- 기본 정렬 말고 이름순, 점수순처럼 다른 기준으로 정렬하려면 어떻게 해야 할까?
- `compareTo()`가 `0`이면 `equals()`도 `true`여야 할까?
- `TreeSet`에 두 개를 넣었는데 하나가 사라진 것처럼 보이는 이유는 뭘까?

핵심은 간단하다.

- 클래스 자체의 기본 정렬 기준이 필요하면 `Comparable`
- 상황마다 다른 정렬 기준이 필요하면 `Comparator`
- 그리고 sorted collection에서는 "`compare` 결과가 `0`인가"가 `equals()`만큼 중요하다

초보자에게 특히 중요한 연결은 하나 더 있다.

- `HashSet`/`HashMap`은 `equals()`/`hashCode()`를 본다
- `TreeSet`/`TreeMap`은 `compareTo()`/`Comparator`의 `0` 여부를 직접 본다

그래서 "중복 제거"라는 같은 말도 컬렉션마다 실제 판정 규칙이 다르다.

이 문서는 그 세 가지를 초급 관점에서 한 번에 연결한다.

## `Comparable`과 `Comparator`를 먼저 한 장으로 보기

| 도구 | 기준은 어디에 있나 | 몇 개의 정렬 기준을 두기 쉬운가 | 주로 쓰는 곳 | 초보자 기억법 |
|---|---|---|---|---|
| `equals()` | 클래스 내부 | 정렬 기준이 아니라 동등성 판단 | 값 비교, `HashSet`, `HashMap` | "같은 값인가?" |
| `Comparable<T>` | 클래스 내부 | 보통 하나의 기본 순서 | `Collections.sort(list)`, `list.sort(null)`, 기본 `TreeSet` | "이 객체의 대표 정렬 기준" |
| `Comparator<T>` | 클래스 바깥 | 여러 개 가능 | `list.sort(comparator)`, `stream.sorted(comparator)`, `new TreeSet<>(comparator)` | "상황별 외부 정렬 규칙" |

초보자용으로 가장 안전한 구분은 다음이다.

- 클래스에 "가장 자연스러운 기본 순서"가 있으면 `Comparable`
- 같은 클래스를 여러 방식으로 정렬해야 하면 `Comparator`
- 정렬과 동등성은 다른 개념이지만, sorted collection에서는 서로 맞물려 동작한다

## natural ordering과 `Comparable`

natural ordering은 "이 클래스의 기본 정렬 순서"다.
Java에서는 보통 클래스가 `Comparable<T>`를 구현해서 이 순서를 직접 가진다.

```java
public record Version(int major, int minor) implements Comparable<Version> {
    @Override
    public int compareTo(Version other) {
        int majorResult = Integer.compare(this.major, other.major);
        if (majorResult != 0) {
            return majorResult;
        }
        return Integer.compare(this.minor, other.minor);
    }
}
```

이제 `Version`은 기본 정렬 기준을 알게 된다.
record를 쓰면 `equals()`도 같은 필드를 기준으로 만들어지므로, 이 예시에서는 natural ordering과 동등성도 비교적 자연스럽게 맞는다.

```java
List<Version> versions = new ArrayList<>(List.of(
        new Version(2, 0),
        new Version(1, 9),
        new Version(1, 5)
));

Collections.sort(versions);
```

### `compareTo()`는 무엇을 반환하나

- 음수: 내가 더 앞이다
- `0`: 정렬 기준상 같은 위치다
- 양수: 내가 더 뒤다

중요한 점은 "정확히 `-1`, `0`, `1`만 반환해야 한다"가 아니라 **부호가 중요하다**는 것이다.

그래서 이런 구현은 피하는 편이 좋다.

```java
return this.major - other.major;
```

정수 범위가 커지면 overflow 위험이 있기 때문이다.
초보자용 기본 규칙은 `Integer.compare`, `Long.compare`, `Comparator.comparing` 같은 도구를 쓰는 것이다.

### 언제 `Comparable`이 잘 맞나

- 버전 번호
- 학생 번호
- ISBN
- 날짜/시간처럼 기본 순서가 비교적 분명한 값

즉 "이 클래스라면 보통 이 순서로 정렬한다"라고 말할 수 있을 때 `Comparable`이 자연스럽다.

## custom ordering과 `Comparator`

같은 객체라도 상황에 따라 정렬 기준이 달라질 수 있다.
이럴 때는 클래스 바깥에서 `Comparator`를 만든다.

예를 들어 학생을 정렬한다고 해 보자.

- 이름순
- 학년순
- 점수 내림차순
- 이름순, 이름이 같으면 학생 번호순

이 모든 기준을 클래스 하나의 `compareTo()` 안에 넣을 수는 없다.
그래서 `Comparator`를 사용한다.

```java
Comparator<Student> byNameThenGrade =
        Comparator.comparing(Student::name)
                .thenComparingInt(Student::grade);

Comparator<Student> byScoreDesc =
        Comparator.comparingInt(Student::score)
                .reversed();
```

사용도 간단하다.

```java
students.sort(byNameThenGrade);
students.sort(byScoreDesc);
```

### `Comparator`가 잘 맞는 경우

- 화면마다 정렬 기준이 다를 때
- 도메인 객체를 수정하지 않고 정렬 규칙만 바꾸고 싶을 때
- 하나의 클래스에 "기본 순서"가 명확하지 않을 때

초보자 관점에서는 이렇게 기억하면 된다.

- `Comparable`: 객체가 자기 기본 순서를 안다
- `Comparator`: 정렬 기준을 밖에서 주입한다

## `equals()`와 일관성은 왜 중요할까

여기가 초보자가 가장 많이 헷갈리는 지점이다.

`equals()`는 "논리적으로 같은 값인가"를 묻고,
`compareTo()`나 `Comparator`는 "정렬 기준상 같은 위치인가"를 묻는다.

둘은 같은 개념이 아니다.
하지만 `TreeSet`, `TreeMap` 같은 sorted collection에서는 이 차이가 바로 동작 차이로 드러난다.

### `compare` 결과가 `0`이면 같은 자리로 본다

```java
record Student(long id, String name, int grade, int score) {}

Comparator<Student> byNameOnly = Comparator.comparing(Student::name);

Set<Student> students = new TreeSet<>(byNameOnly);
students.add(new Student(1L, "Mina", 2, 80));
students.add(new Student(2L, "Mina", 3, 95));

System.out.println(students.size()); // 1
```

왜 그럴까?

- 두 `Student` record는 `id`, `grade`, `score`가 달라서 `equals()`는 `false`다
- 하지만 `byNameOnly`는 둘 다 `"Mina"`라서 `compare` 결과가 `0`이다
- `TreeSet`은 "정렬상 같은 자리"라고 판단해서 둘을 따로 보관하지 않는다

즉 sorted collection에서는 **`equals()`보다 compare 결과가 직접적인 중복 판단 기준**이 된다.

### 초보자용 안전 규칙

직접 만든 natural ordering에서는 가능하면 다음을 목표로 잡는 편이 가장 안전하다.

- `compareTo(other) == 0` 이면 `equals(other)`도 `true`

custom `Comparator`를 `TreeSet`/`TreeMap`에 넣을 때도 같은 감각이 필요하다.

- 정말 같은 원소로 취급하고 싶은 경우에만 `compare`가 `0`이 되게 한다
- 그렇지 않다면 tie-breaker를 더 넣는다

위 예제는 이렇게 고치면 surprise가 줄어든다.

```java
Comparator<Student> byNameThenId =
        Comparator.comparing(Student::name)
                .thenComparingLong(Student::id);
```

이제 이름이 같아도 `id`가 다르면 `compare` 결과가 `0`이 아니어서 둘 다 `TreeSet`에 들어간다.

## Comparator 일관성 체크 카드

처음엔 복잡하게 말하지 말고 아래 카드부터 보면 된다.

> mental model:
> `equals()`는 "같은 사람인가?"
> `compare(...) == 0`은 "정렬 기준상 같은 칸인가?"

| 체크 질문 | `yes`면 뜻 | 바로 할 일 |
|---|---|---|
| `equals()`는 다른데 `compare(...) == 0`이 나올 수 있나? | sorted collection에서 하나처럼 합쳐질 수 있다 | `TreeSet`/`TreeMap`용 comparator라면 tie-breaker 후보를 본다 |
| `compare(...) == 0`이면 정말 같은 원소 취급해도 되나? | 의도된 dedupe일 수도 있다 | 의도라면 유지, 아니면 `thenComparing(...)`을 더한다 |
| `HashSet`과 `TreeSet` 결과가 달라도 이상하지 않나? | 두 컬렉션의 중복 규칙이 다르다 | `equals/hashCode`와 `compare == 0`을 따로 적어 본다 |
| 비교 기준 필드가 mutable인가? | 넣은 뒤 조회와 정렬이 더 헷갈릴 수 있다 | 불변 값으로 두거나 삽입 후 수정하지 않는다 |

### 30초 예시

```java
record Student(long id, String name) {}

Student a = new Student(1L, "Mina");
Student b = new Student(2L, "Mina");

System.out.println(a.equals(b)); // false
System.out.println(Comparator.comparing(Student::name).compare(a, b)); // 0
```

이 상태를 초급 관점에서 읽으면 이렇다.

- `equals()` 기준으로는 다른 학생이다
- name-only comparator 기준으로는 같은 칸이다
- 그래서 `HashSet`은 둘 다 담을 수 있지만 `TreeSet`은 하나처럼 보일 수 있다

### 초보자용 빨간 신호

- comparator가 `name`만 보는데, 도메인에서는 `id`가 다르면 다른 사람이다
- `TreeMap.put` 두 번째 호출이 새 key 추가가 아니라 이전 값 덮어쓰기가 된다
- record라서 `equals()`가 자동 생성됐으니 sorted collection도 안전하다고 생각한다

이 중 하나라도 걸리면 먼저 이 한 줄을 적어 보면 된다.

`compare(...) == 0`이 되는 조건: ____________________

여기에 "name이 같으면 0"처럼 적었을 때 의도보다 넓다면 comparator를 더 좁혀야 한다.

### 실무에서 자주 보는 예외: `BigDecimal`

`BigDecimal`은 대표적인 예외 사례다.

## Comparator 일관성 체크 카드 (계속 2)

```java
System.out.println(new BigDecimal("1.0").compareTo(new BigDecimal("1.00")) == 0); // true
System.out.println(new BigDecimal("1.0").equals(new BigDecimal("1.00"))); // false
```

즉 수학적 크기는 같지만 표현(scale)은 다르다고 본다.
그래서 `HashSet`과 `TreeSet`에서 다르게 느껴질 수 있다.

초보자에게 가장 중요한 메시지는 하나다.

- `compare == 0`과 `equals == true`가 항상 같은 뜻은 아니다
- 하지만 직접 정렬 기준을 만들 때는 둘이 최대한 어긋나지 않게 설계하는 편이 안전하다

## 코드로 한 번에 보기

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;

public class ComparableComparatorExample {
    public static void main(String[] args) {
        List<Version> versions = new ArrayList<>(List.of(
                new Version(2, 0),
                new Version(1, 9),
                new Version(1, 5)
        ));

        versions.sort(null); // Comparable 기반 natural ordering
        System.out.println(versions);

        List<Student> students = new ArrayList<>(List.of(
                new Student(3L, "Mina", 2, 80),
                new Student(1L, "Ari", 1, 95),
                new Student(2L, "Mina", 3, 88)
        ));

        students.sort(
                Comparator.comparing(Student::name)
                        .thenComparingInt(Student::grade)
        );
        System.out.println(students);

        Set<Student> broken = new TreeSet<>(Comparator.comparing(Student::name));
        broken.add(new Student(1L, "Mina", 2, 80));
        broken.add(new Student(2L, "Mina", 3, 88));
        System.out.println(broken.size()); // 1

        Set<Student> fixed = new TreeSet<>(
                Comparator.comparing(Student::name)
                        .thenComparingLong(Student::id)
        );
        fixed.add(new Student(1L, "Mina", 2, 80));
        fixed.add(new Student(2L, "Mina", 3, 88));
        System.out.println(fixed.size()); // 2
    }

## 코드로 한 번에 보기 (계속 2)

private record Student(long id, String name, int grade, int score) {}

    private record Version(int major, int minor) implements Comparable<Version> {
        @Override
        public int compareTo(Version other) {
            int majorResult = Integer.compare(this.major, other.major);
            if (majorResult != 0) {
                return majorResult;
            }
            return Integer.compare(this.minor, other.minor);
        }
    }
}
```

이 예제에서 확인할 포인트는 네 가지다.

- 기본 정렬 기준은 `Comparable`
- 상황별 정렬 기준은 `Comparator`
- `compare`가 `0`이면 sorted collection이 같은 자리로 볼 수 있다
- tie-breaker를 넣어야 의도한 distinctness가 유지된다

## 빠른 체크리스트

- 클래스의 대표 정렬 기준이 하나면 `Comparable`
- 상황마다 다른 정렬 기준이 필요하면 `Comparator`
- `compareTo()`/`compare()`는 부호가 중요하지, 꼭 `-1`, `0`, `1`만 반환할 필요는 없다
- 숫자 비교는 뺄셈보다 `Integer.compare`, `Long.compare`를 우선 사용
- `TreeSet`/`TreeMap`에서는 `compare == 0`이 중복 판단에 직접 영향을 준다
- natural ordering은 가능하면 `equals()`와 일관되게 설계
- custom comparator에서 distinctness가 중요하면 `thenComparing`으로 tie-breaker 추가

## 어떤 문서를 다음에 읽으면 좋은가

- "`equals()`와 정렬 비교가 왜 다른 말인지 아직 헷갈린다"면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- "`Comparator.comparing`, `thenComparing`, `nullsLast`를 손으로 써 보며 익히고 싶다"면 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- "`reversed()`를 붙였더니 어디까지 뒤집히는지 감이 안 온다"면 [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
- "`List.sort(...)`와 `stream.sorted(...)` 중 어디에 같은 comparator를 써야 하는지 헷갈린다"면 [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- "`String` 정렬에서 대소문자와 `null`을 같이 다루려니 기준이 흔들린다"면 [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)
- "wrapper 숫자 필드에 `null`이 섞이자 comparator를 어떻게 골라야 할지 막힌다"면 [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
- "`TreeSet`/`TreeMap`에 comparator를 안 넘겼는데도 중복처럼 합쳐진다"면 [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- "`TreeSet`/`TreeMap`에서 이름만 같은데 하나가 사라진 것처럼 보인다"면 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- "정렬된 컬렉션에 넣은 뒤 필드를 바꿨더니 조회와 순서가 이상해졌다"면 [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
- "`HashSet`과 `TreeSet` 결과 차이를 성능 감각까지 같이 묶어 보고 싶다"면 [Java Collections 성능 감각](./collections-performance.md)

## 어떤 문서를 다음에 읽으면 좋은가 (계속 2)

- "`BigDecimal`은 숫자가 같은데 왜 `equals()`와 `compareTo()`가 다르게 나오지?" 싶다면 [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
- "`equals`, `hashCode`, `Comparable` 계약을 좀 더 엄밀하게 확인하고 싶다"면 [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)

## 한 줄 정리

Java에서 `Comparable`은 객체의 기본 정렬 기준, `Comparator`는 상황별 외부 정렬 기준이며, 특히 `TreeSet`/`TreeMap`에서는 `compare == 0`이 `equals()`만큼 중요한 의미를 가지므로 정렬 기준과 동등성의 관계를 함께 설계해야 한다.
