# HashSet vs TreeSet Duplicate Semantics

> 한 줄 요약: Java 입문자가 `HashSet`의 중복 판단은 `equals()`/`hashCode()`를, `TreeSet`의 중복 판단은 `compareTo()` 또는 `Comparator.compare(...) == 0`을 따른다는 점을 한 번에 이해하도록 정리한 beginner doc이다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Record and Value Object Equality](./record-value-object-equality-basics.md)
> - [Java Collections 성능 감각](./collections-performance.md)
> - [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)

> retrieval-anchor-keywords: hashset vs treeset duplicate semantics, java hashset duplicate rule, java treeset duplicate rule, java set duplicate semantics, hashset equals hashCode, treeset compareTo duplicate, treeset comparator compare zero duplicate, equals hashCode vs compare == 0, sorted set duplicate surprise, treeset compareTo 0 same element, comparator returning 0 same element, hash collision not duplicate, hashset vs treeset beginner, java set equality ordering mismatch

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 결론: `HashSet`과 `TreeSet`의 중복 규칙](#먼저-결론-hashset과-treeset의-중복-규칙)
- [`HashSet`은 어떻게 중복을 판단할까](#hashset은-어떻게-중복을-판단할까)
- [`TreeSet`은 어떻게 중복을 판단할까](#treeset은-어떻게-중복을-판단할까)
- [같은 데이터를 넣어도 결과가 달라지는 이유](#같은-데이터를-넣어도-결과가-달라지는-이유)
- [더 안전하게 설계하는 방법](#더-안전하게-설계하는-방법)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문자가 `Set`을 배우면서 자주 헷갈리는 질문은 대체로 비슷하다.

- `HashSet`에는 두 개가 다 들어가는데 왜 `TreeSet`에는 하나만 남을까?
- `hashCode()`가 같으면 중복이라고 봐야 할까?
- `compareTo()`가 `0`이면 `equals()`도 `true`여야 할까?
- `TreeSet`에 넣었더니 원소가 "사라진 것처럼" 보이는 이유는 뭘까?

핵심은 간단하다.

- `HashSet`은 **해시 기반**이라서 최종 중복 판단을 `equals()`로 한다
- `TreeSet`은 **정렬 기반**이라서 최종 중복 판단을 `compare == 0`으로 한다
- 그래서 equality 규칙과 ordering 규칙이 어긋나면 두 `Set`이 같은 데이터를 다르게 본다

이 문서는 그 차이를 초보자 관점에서 분리해서 설명한다.

## 먼저 결론: `HashSet`과 `TreeSet`의 중복 규칙

| 컬렉션 | 내부 기준 | 최종 중복 판단 | 초보자 메모 |
|---|---|---|---|
| `HashSet` | 해시 버킷 | `equals()`가 `true`면 같은 원소 | `hashCode()`는 위치를 찾는 힌트다 |
| `TreeSet` | 정렬 순서 | `compareTo()` 또는 `Comparator.compare(...)`가 `0`이면 같은 원소 | `0`이면 같은 자리라고 본다 |

짧게 외우면 다음이 가장 안전하다.

- `HashSet`: "`equals()`로 같으면 중복"
- `TreeSet`: "`compare == 0`이면 중복"

그리고 `HashSet`의 `hashCode()`는 중요하지만, **`hashCode()`만으로 중복이 결정되지는 않는다**.

## `HashSet`은 어떻게 중복을 판단할까

`HashSet`은 대략 다음 순서로 동작한다.

1. `hashCode()`로 원소가 들어갈 후보 버킷을 찾는다
2. 같은 버킷 안에서 `equals()`로 정말 같은 원소인지 확인한다

즉 초보자가 특히 기억해야 할 점은 이 두 가지다.

- 같은 `hashCode()`라고 해서 자동으로 중복은 아니다
- 정말 같은 원소인지의 마지막 판단은 `equals()`가 한다

```java
import java.util.HashSet;
import java.util.Set;

record User(long id, String name) {}

Set<User> users = new HashSet<>();
users.add(new User(1L, "Mina"));
users.add(new User(1L, "Mina"));

System.out.println(users.size()); // 1
```

위 예시에서 record는 `id`, `name` 전체를 기준으로 `equals()`/`hashCode()`를 만든다.  
두 객체는 값이 같으므로 `HashSet`은 중복으로 본다.

반대로 값이 다르면 `hashCode()`가 우연히 같아도 둘 다 들어갈 수 있다.  
즉 `hashCode()`는 중복의 최종 판정자가 아니라, 빠르게 찾기 위한 도구다.

## `TreeSet`은 어떻게 중복을 판단할까

`TreeSet`은 원소를 정렬된 상태로 유지한다.  
그래서 "같은 원소인가?"도 equality보다 **정렬 기준**에 더 가깝게 판단한다.

- 기본 `TreeSet`은 원소의 `compareTo()`를 사용한다
- `new TreeSet<>(comparator)` 형태면 넘긴 `Comparator`를 사용한다
- 이 비교 결과가 `0`이면 `TreeSet`은 같은 자리에 오는 원소라고 본다

```java
import java.util.Comparator;
import java.util.Set;
import java.util.TreeSet;

record Student(long id, String name) {}

Set<Student> students = new TreeSet<>(Comparator.comparing(Student::name));
students.add(new Student(1L, "Mina"));
students.add(new Student(2L, "Mina"));

System.out.println(students.size()); // 1
```

왜 `1`일까?

- 두 record는 `id`가 다르므로 `equals()`는 `false`다
- 하지만 comparator는 이름만 비교하므로 둘 다 `"Mina"`일 때 `compare(...) == 0`이다
- `TreeSet`은 둘을 "정렬 기준상 같은 원소"로 보고 하나만 남긴다

즉 `TreeSet`에서는 `equals()`보다 **`compare == 0`이 직접적인 중복 기준**이다.

## 같은 데이터를 넣어도 결과가 달라지는 이유

같은 두 객체를 넣어도 `HashSet`과 `TreeSet`은 서로 다른 규칙으로 판단할 수 있다.

```java
import java.util.Comparator;
import java.util.HashSet;
import java.util.Set;
import java.util.TreeSet;

record Student(long id, String name) {}

Student first = new Student(1L, "Mina");
Student second = new Student(2L, "Mina");

Set<Student> hashSet = new HashSet<>();
hashSet.add(first);
hashSet.add(second);

Set<Student> treeSet = new TreeSet<>(Comparator.comparing(Student::name));
treeSet.add(first);
treeSet.add(second);

System.out.println(hashSet.size()); // 2
System.out.println(treeSet.size()); // 1
```

이 결과는 이상한 것이 아니라, 각 컬렉션이 자기 규칙대로 일한 것이다.

- `HashSet`: `equals()`가 `false`이므로 둘 다 유지
- `TreeSet`: `compare == 0`이므로 하나로 취급

이 어긋남을 한 장으로 요약하면 다음과 같다.

| 상황 | `HashSet` | `TreeSet` |
|---|---|---|
| `equals()`는 `false`, `compare == 0` | 둘 다 들어갈 수 있다 | 하나만 남을 수 있다 |
| `equals()`는 `true`, `compare != 0` | 하나만 남을 수 있다 | 둘 다 들어갈 수 있다 |

그래서 sorted set을 설계할 때는 "무엇을 같은 원소로 볼 것인가"를 comparator와 함께 생각해야 한다.

## 더 안전하게 설계하는 방법

### 1. `HashSet`에서는 `equals()`와 `hashCode()`를 같이 본다

- `equals()`를 오버라이드하면 `hashCode()`도 같이 오버라이드한다
- 둘 다 같은 필드를 기준으로 만든다
- key나 set 원소에 mutable 필드를 넣는 것은 피한다

### 2. `TreeSet`에서는 `compare == 0`이 정말 같은 원소일 때만 나오게 한다

이름이 같아도 다른 학생을 따로 보관하고 싶다면 tie-breaker를 넣어야 한다.

```java
Comparator<Student> byNameThenId =
        Comparator.comparing(Student::name)
                .thenComparingLong(Student::id);

Set<Student> students = new TreeSet<>(byNameThenId);
students.add(new Student(1L, "Mina"));
students.add(new Student(2L, "Mina"));

System.out.println(students.size()); // 2
```

이제 이름이 같아도 `id`가 다르면 `compare == 0`이 아니므로 둘 다 남는다.

### 3. natural ordering을 직접 만들 때는 가능한 한 `equals()`와 맞춘다

초보자용 안전 규칙은 다음이다.

- 가능하면 `compareTo(other) == 0`이면 `equals(other)`도 `true`가 되게 한다
- custom `Comparator`도 정말 같은 원소로 묶고 싶을 때만 `0`을 반환하게 만든다

이 규칙을 지키면 `HashSet`, `TreeSet`, 정렬 API를 함께 쓸 때 surprise가 줄어든다.

## 빠른 체크리스트

- `HashSet` 중복 판단의 마지막 기준은 `equals()`다
- `HashSet`에서 `hashCode()`는 버킷 탐색용이지 단독 중복 기준이 아니다
- `TreeSet` 중복 판단의 마지막 기준은 `compare == 0`이다
- `TreeSet`에 custom `Comparator`를 넣으면 그 comparator가 사실상 "같은 원소"의 정의가 된다
- 이름만 비교하는 comparator를 `TreeSet`에 넣으면 이름이 같은 서로 다른 객체가 하나로 합쳐질 수 있다
- 둘 다 남겨야 하면 `thenComparing(...)` 같은 tie-breaker를 넣는다

## 어떤 문서를 다음에 읽으면 좋은가

- equality와 `hashCode()` 기초를 먼저 더 단단히 하려면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- `compareTo()`, `Comparator`, tie-breaker를 더 배우려면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- value object를 `HashSet` key로 안전하게 쓰는 감각을 익히려면 [Record and Value Object Equality](./record-value-object-equality-basics.md)
- `BigDecimal`처럼 `equals()`와 `compareTo()`가 어긋나는 표준 라이브러리 사례를 보려면 [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)

## 한 줄 정리

`HashSet`은 `equals()`/`hashCode()`를 기준으로, `TreeSet`은 `compare == 0`을 기준으로 중복을 판단하므로, equality 규칙과 ordering 규칙이 어긋나면 두 `Set`의 결과가 다르게 보일 수 있다.
