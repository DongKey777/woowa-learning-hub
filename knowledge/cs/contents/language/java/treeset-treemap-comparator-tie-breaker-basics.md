# Comparator in TreeSet and TreeMap

> 한 줄 요약: Java 입문자가 `TreeSet`/`TreeMap`에서는 comparator가 단순 정렬 규칙이 아니라 "무엇을 같은 원소/같은 key로 볼지"까지 정한다는 점을 `compare == 0`, tie-breaker, concrete example로 이해하도록 만든 beginner primer다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
> - [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
> - [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
> - [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)

> retrieval-anchor-keywords: comparator in treeset and treemap, treeset treemap comparator basics, java treeset comparator duplicate, java treemap comparator duplicate key, java treemap comparator replace value, compare == 0 same element, compare == 0 same key, tree set map tie breaker, comparator tie breaker beginner, thenComparing distinctness, sorted collection duplicate surprise, sorted map duplicate surprise, different objects treated as duplicate, comparator defines equality in treeset, comparator defines key identity in treemap, explicit comparator vs natural ordering, compareTo same surprise in treeset treemap, navigableset comparator lookup, navigablemap comparator lookup, floor ceiling lower higher comparator order, mutable comparator field treeset, mutable key treemap lookup broken

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 요약 표](#한-장-요약-표)
- [`TreeSet`: 왜 하나만 남을까](#treeset-왜-하나만-남을까)
- [`TreeMap`: 왜 값이 덮어써질까](#treemap-왜-값이-덮어써질까)
- [tie-breaker는 정렬 예쁘게 하기용만이 아니다](#tie-breaker는-정렬-예쁘게-하기용만이-아니다)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문자가 `Comparator`를 배운 뒤 `TreeSet`이나 `TreeMap`을 쓰면 자주 이런 질문에서 막힌다.

- 분명 다른 객체 두 개를 넣었는데 왜 `TreeSet` 크기가 `1`일까?
- `TreeMap`에 key를 두 번 넣었더니 왜 새 값이 이전 값을 덮어쓸까?
- `compare(...) == 0`은 그냥 "정렬상 동점" 아닌가?
- `thenComparing(...)`은 보기 좋은 정렬을 위해서만 필요한 것 아닐까?

핵심은 간단하다.

- `TreeSet`과 `TreeMap`은 **정렬된 컬렉션**이다
- 그래서 comparator는 "누가 앞에 오나"뿐 아니라 "**누가 같은 자리인가**"도 결정한다
- 이때 `compare(...) == 0`이면 sorted collection은 둘을 같은 원소 또는 같은 key처럼 다룰 수 있다

이 문서는 그 감각을 `TreeSet`, `TreeMap`, tie-breaker 세 가지로만 좁혀서 설명한다.

## 먼저 잡을 mental model

초보자에게 가장 안전한 기억법은 이 한 줄이다.

> `TreeSet`/`TreeMap`에서 comparator는 정렬 순서이면서 동시에 "같은 칸 판정기"다.

즉 `compare(...) == 0`은 여기서 단순한 동점 표시가 아니다.

- `List.sort(...)`에서는 "같은 그룹" 정도로 끝날 수 있다
- `TreeSet`에서는 "같은 원소 자리"로 본다
- `TreeMap`에서는 "같은 key 자리"로 본다

그래서 sorted collection에서는 tie-breaker가 없으면 서로 다른 객체도 합쳐진 것처럼 보일 수 있다.

## 한 장 요약 표

| 위치 | `compare(...) == 0`의 의미 | 초보자 메모 |
|---|---|---|
| `list.sort(comparator)` | 정렬상 같은 그룹 | 둘 다 리스트에 남는다 |
| `TreeSet` | 같은 원소 자리 | 나중 `add`가 무시될 수 있다 |
| `TreeMap` | 같은 key 자리 | 나중 `put`이 기존 값을 덮어쓸 수 있다 |

그리고 comparator를 직접 넘기지 않아도, 기본 `TreeSet`/`TreeMap`은 natural ordering인 `compareTo()`로 같은 규칙을 따른다.

## `TreeSet`: 왜 하나만 남을까

예를 들어 이름만 비교하는 comparator로 학생을 보관한다고 해 보자.

```java
import java.util.Comparator;
import java.util.Set;
import java.util.TreeSet;

record Student(long id, String name) {}

Comparator<Student> byNameOnly =
        Comparator.comparing(Student::name);

Set<Student> students = new TreeSet<>(byNameOnly);
students.add(new Student(1L, "Mina"));
students.add(new Student(2L, "Mina"));

System.out.println(students.size()); // 1
```

왜 `1`일까?

- 두 객체는 `id`가 다르므로 `equals()`는 `false`다
- 하지만 comparator는 `name`만 보므로 둘 다 `"Mina"`일 때 `compare(...) == 0`이다
- `TreeSet`은 둘을 "같은 위치에 오는 원소"로 보고 하나만 유지한다

즉 여기서 중요한 포인트는 이것이다.

- `TreeSet`은 "서로 다른 객체인가?"보다 "`compare == 0`인가?"를 더 직접적으로 본다

## `TreeMap`: 왜 값이 덮어써질까

`TreeMap`도 감각은 같다.  
차이는 `Set`처럼 원소를 하나만 보관하는 대신, 같은 key 자리라고 판단하면 **새 값으로 교체**된다는 점이다.

```java
import java.util.Comparator;
import java.util.Map;
import java.util.TreeMap;

record Student(long id, String name) {}

Comparator<Student> byNameOnly =
        Comparator.comparing(Student::name);

Map<Student, String> seats = new TreeMap<>(byNameOnly);
seats.put(new Student(1L, "Mina"), "front");
seats.put(new Student(2L, "Mina"), "back");

System.out.println(seats.size()); // 1
System.out.println(seats.get(new Student(99L, "Mina"))); // back
```

이 예시는 초보자에게 꽤 강하게 남는다.

- 두 key 객체는 서로 다르다
- 그래도 comparator는 둘 다 `"Mina"`라서 `compare(...) == 0`을 만든다
- `TreeMap`은 같은 key 자리라고 보고 두 번째 `put`으로 값을 바꾼다

즉 `TreeMap`에서는 comparator가 사실상 "**key distinctness 규칙**"처럼 동작한다.

## tie-breaker는 정렬 예쁘게 하기용만이 아니다

입문 단계에서 tie-breaker를 "동점자 보기 좋게 정렬하는 2차 기준"으로만 외우기 쉽다.  
하지만 `TreeSet`/`TreeMap`에서는 더 중요하다.

> tie-breaker는 서로 다른 객체가 `compare == 0`으로 뭉개지지 않게 해 주는 구분자다.

예를 들어 이름이 같아도 학생 번호가 다르면 다른 학생으로 유지하고 싶다면 이렇게 바꾼다.

```java
Comparator<Student> byNameThenId =
        Comparator.comparing(Student::name)
                .thenComparingLong(Student::id);
```

이 comparator를 `TreeSet`과 `TreeMap`에 쓰면 다음처럼 바뀐다.

| 의도 | comparator |
|---|---|
| 이름이 같으면 같은 사람으로 취급 | `Comparator.comparing(Student::name)` |
| 이름이 같아도 `id`가 다르면 다른 사람으로 취급 | `Comparator.comparing(Student::name).thenComparingLong(Student::id)` |

즉 `thenComparing(...)`은 "더 예쁜 정렬"이 아니라, sorted collection 안에서는 **distinctness를 끝까지 분리하는 마지막 규칙**이 되기도 한다.

## 초보자가 자주 헷갈리는 지점

- `compare(...) == 0`은 `equals(...) == true`와 같은 말이 아니다. sorted collection 안에서는 "같은 자리"라는 뜻에 더 가깝다.
- `TreeSet`에서 원소가 사라진 것처럼 보여도 실제로는 comparator가 둘을 구분하지 못한 것이다.
- `TreeMap`에서 값이 덮어써졌다면 key 객체가 같은 reference였기 때문이 아니라 comparator가 같은 key라고 봤을 가능성이 크다.
- tie-breaker는 optional decoration이 아니다. distinctness가 중요하면 꼭 필요한 규칙이다.
- 반대로 "이름만 같으면 같은 사람으로 보겠다"가 의도라면 name-only comparator도 틀린 것이 아니다. comparator가 그 정책을 표현한 것이다.
- comparator를 넘기지 않은 `TreeSet`/`TreeMap`도 안전지대가 아니다. natural ordering의 `compareTo()` 역시 `0`이면 같은 자리로 본다.

## 빠른 체크리스트

- `TreeSet`에서는 `compare == 0`이면 같은 원소처럼 취급될 수 있다
- `TreeMap`에서는 `compare == 0`이면 같은 key처럼 취급되어 값이 교체될 수 있다
- 서로 다른 객체를 모두 보관해야 한다면 comparator가 끝까지 구분되도록 tie-breaker를 넣는다
- `thenComparing(...)`은 정렬 품질뿐 아니라 distinctness 보존에도 영향을 준다
- comparator가 표현하는 "같은 것의 정의"가 도메인 의도와 맞는지 먼저 확인한다

## 어떤 문서를 다음에 읽으면 좋은가

- `Comparable`, `Comparator`, natural ordering의 큰 그림을 먼저 다시 묶고 싶다면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- `Comparator`를 넘기지 않은 `new TreeSet<>()`/`new TreeMap<>()`에서 `compareTo()`만으로 같은 surprise가 생기는 모습을 보려면 [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- `TreeSet`/`TreeMap` 안에 넣은 뒤 comparator가 보는 필드를 바꿔서 조회와 정렬이 깨지는 문제를 보려면 [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
- `thenComparing`, `reversed`, `nullsLast` 같은 API 조합을 더 손에 익히려면 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- `HashSet`과 `TreeSet`의 차이를 equality 기준까지 넓혀 보고 싶다면 [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- equality와 ordering 계약을 더 엄밀하게 보고 싶다면 [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)

## 한 줄 정리

`TreeSet`/`TreeMap`에서 comparator는 정렬 순서만 정하는 도구가 아니라 "`compare == 0`이면 같은 자리"라는 규칙까지 만들기 때문에, 서로 다른 객체를 모두 유지하고 싶다면 tie-breaker까지 포함해 comparator를 설계해야 한다.
