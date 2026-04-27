# Comparator Consistency With `equals()` Bridge

> 한 줄 요약: `HashSet`은 `equals()`/`hashCode()`를, `TreeSet`/`TreeMap`은 `compare(...) == 0`을 더 직접적으로 보기 때문에, comparator가 `equals()`와 일관되지 않으면 같은 `record` 예제도 컬렉션마다 다르게 보일 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: comparator consistency with equals bridge basics, comparator consistency with equals bridge beginner, comparator consistency with equals bridge intro, java basics, beginner java, 처음 배우는데 comparator consistency with equals bridge, comparator consistency with equals bridge 입문, comparator consistency with equals bridge 기초, what is comparator consistency with equals bridge, how to comparator consistency with equals bridge
> 관련 문서:
> - [Language README](../README.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
> - [Record and Value Object Equality](./record-value-object-equality-basics.md)
> - [Beginner Drill Sheet: Equality vs Ordering](./equality-vs-ordering-beginner-drill-sheet.md)
> - [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)

> retrieval-anchor-keywords: language-java-00086, comparator consistency with equals bridge, compare zero equals consistency java, compare == 0 equals mismatch beginner, comparator consistent with equals treeset treemap, record comparator equals hashset treeset treemap, java record compare zero hashset treeset treemap, java comparator same element same key slot, java tree set tree map equals consistency, hashset treeset treemap same example beginner, compare zero vs equals record primer, comparator consistent with equals why it matters, sorted collection equality mismatch beginner, record value object comparator mismatch, compare zero same key tree map record, hashset equals treeset compare zero bridge

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [예제 `record`: `equals()`와 comparator가 서로 다른 기준을 본다](#예제-record-equals와-comparator가-서로-다른-기준을-본다)
- [한 화면 비교표](#한-화면-비교표)
- [`HashSet`: 왜 2개가 남을까](#hashset-왜-2개가-남을까)
- [`TreeSet`: 왜 1개만 남을까](#treeset-왜-1개만-남을까)
- [`TreeMap`: 왜 값이 덮어써질까](#treemap-왜-값이-덮어써질까)
- [`Comparator`가 `equals()`와 일관적이라는 말의 뜻](#comparator가-equals와-일관적이라는-말의-뜻)
- [초보자 공통 혼동](#초보자-공통-혼동)
- [빠른 체크리스트](#빠른-체크리스트)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

초보자가 `Comparator`를 배울 때 가장 많이 놓치는 지점은 이것이다.

- `equals()`는 "같은 객체인가?"를 말해 주는 것 같다
- `compare(...) == 0`은 그냥 "정렬상 동점"처럼 보인다
- 그래서 둘이 조금 달라도 괜찮다고 느끼기 쉽다

하지만 `TreeSet`과 `TreeMap` 안에서는 `compare(...) == 0`이 단순한 동점이 아니다.

- `TreeSet`에서는 같은 원소 자리다
- `TreeMap`에서는 같은 key 자리다

그래서 comparator가 `equals()`와 다른 기준을 보면, 같은 객체 집합을 넣어도 `HashSet`, `TreeSet`, `TreeMap` 결과가 달라질 수 있다.

## 먼저 잡을 mental model

가장 안전한 beginner 기억법은 이 한 줄이다.

> `HashSet`은 `equals()`를, `TreeSet`/`TreeMap`은 `compare(...) == 0`을 먼저 본다.

그리고 "comparator가 `equals()`와 일관적이다"라는 말은 보통 이렇게 읽으면 된다.

> `compare(a, b) == 0`이면 `a.equals(b)`도 `true`가 되도록 비교 기준을 맞춘다.

완전히 같은 문장으로 외울 필요는 없다. 초보자 기준으로는 "sorted collection에서 같은 자리라고 본다면, `equals()`로도 거의 같은 객체라고 느껴지게 맞추는 편이 덜 놀랍다" 정도로 이해해도 충분하다.

## 예제 `record`: `equals()`와 comparator가 서로 다른 기준을 본다

한 가지 예제로만 끝까지 보자.

```java
record Student(long id, String name) {}
```

이 `record`의 기본 `equals()`와 `hashCode()`는 `id`, `name` 둘 다 본다.

하지만 comparator를 이렇게 만들면 기준이 달라진다.

```java
import java.util.Comparator;

Comparator<Student> byNameOnly =
        Comparator.comparing(Student::name);
```

이제 다음 두 객체를 보자.

```java
Student first = new Student(1L, "Mina");
Student second = new Student(2L, "Mina");
```

- `first.equals(second)`는 `false`다
- `byNameOnly.compare(first, second)`는 `0`이다

즉 같은 `record`를 놓고도 equality 기준과 ordering 기준이 갈라진 상태다.

## 한 화면 비교표

| 컬렉션 | 더 직접적으로 보는 기준 | `first`, `second` 결과 |
|---|---|---|
| `HashSet<Student>` | `equals()`/`hashCode()` | 2개 다 들어간다 |
| `TreeSet<Student>` with `byNameOnly` | `compare(...) == 0` | 1개만 남는다 |
| `TreeMap<Student, String>` with `byNameOnly` | `compare(...) == 0` | 같은 key 자리로 보고 값이 덮어써진다 |

핵심은 컬렉션이 이상한 것이 아니라, 각 컬렉션이 자기 규칙대로 일하고 있다는 점이다.

## `HashSet`: 왜 2개가 남을까

```java
import java.util.HashSet;
import java.util.Set;

Set<Student> hashSet = new HashSet<>();
hashSet.add(first);
hashSet.add(second);

System.out.println(hashSet.size()); // 2
```

이유는 단순하다.

- `HashSet`은 최종적으로 `equals()`를 본다
- `record Student(long id, String name)`에서 `id`가 다르면 `equals()`는 `false`다
- 그래서 두 객체를 다른 원소로 보관한다

## `TreeSet`: 왜 1개만 남을까

```java
import java.util.Set;
import java.util.TreeSet;

Set<Student> treeSet = new TreeSet<>(byNameOnly);
treeSet.add(first);
treeSet.add(second);

System.out.println(treeSet.size()); // 1
```

여기서는 기준이 달라진다.

- `TreeSet`은 comparator 결과를 본다
- 이름만 비교하므로 `"Mina"`와 `"Mina"`는 `compare(...) == 0`이다
- `TreeSet`은 둘을 같은 원소 자리로 본다

즉 `equals()`가 `false`여도 `TreeSet`은 하나만 남길 수 있다.

## `TreeMap`: 왜 값이 덮어써질까

```java
import java.util.Map;
import java.util.TreeMap;

Map<Student, String> treeMap = new TreeMap<>(byNameOnly);
treeMap.put(first, "front");
treeMap.put(second, "back");

System.out.println(treeMap.size()); // 1
System.out.println(treeMap.get(new Student(99L, "Mina"))); // back
```

여기서도 comparator가 key 자리를 결정한다.

- 첫 번째 `put`은 `"Mina"` 자리를 만든다
- 두 번째 `put`은 같은 `"Mina"` 자리라고 보고 값을 `"back"`으로 바꾼다
- `new Student(99L, "Mina")`로 조회해도 comparator 기준으로는 같은 key 자리다

초보자는 여기서 "key 객체가 완전히 교체되었다"보다 "같은 key 칸의 value가 바뀌었다"라고 이해하는 편이 더 정확하다.

## `Comparator`가 `equals()`와 일관적이라는 말의 뜻

이번 예제에서 comparator는 `equals()`와 일관적이지 않다.

이유:

- `compare(first, second) == 0`
- 그런데 `first.equals(second)`는 `false`

그래서 sorted collection에서 surprise가 생긴다.

반대로 이름이 같아도 `id`가 다르면 끝까지 구분하고 싶다면 tie-breaker를 붙인다.

```java
Comparator<Student> byNameThenId =
        Comparator.comparing(Student::name)
                .thenComparingLong(Student::id);
```

이제는 `first`와 `second`가 다음처럼 맞춰진다.

- `compare(first, second) != 0`
- `equals()`도 `false`

즉 "다른 객체면 sorted collection에서도 다른 자리로 보이게" 기준이 맞춰진다.

## 초보자 공통 혼동

- `compare(...) == 0`은 sorted collection 안에서 단순 동점이 아니라 같은 자리 판정에 가깝다.
- `record`가 자동으로 `equals()`를 만들어 줘도, comparator가 다른 필드만 보면 `TreeSet`/`TreeMap` 기준은 달라질 수 있다.
- `HashSet`에서 잘 되었다고 `TreeSet`도 같을 것이라고 기대하면 안 된다.
- `TreeMap`에서 `size()`가 `1`이면 key reference가 같아서가 아니라 comparator가 같은 key 자리라고 본 경우가 많다.
- comparator consistency with equals는 "무조건 항상 지켜야 하는 문장"으로 외우기보다, "안 맞추면 sorted collection에서 놀랄 수 있다"로 먼저 이해하면 된다.

## 빠른 체크리스트

- 지금 보는 컬렉션이 `HashSet`인가, `TreeSet`/`TreeMap`인가?
- `equals()`가 보는 필드와 comparator가 보는 필드가 같은가?
- `compare(...) == 0`이면 정말 같은 원소나 같은 key로 합쳐도 되는가?
- 아니라면 `thenComparing(...)` 같은 tie-breaker가 필요한가?

## 한 줄 정리

`HashSet`은 `equals()` 기준으로, `TreeSet`/`TreeMap`은 `compare(...) == 0` 기준으로 같은 자리를 판단하므로, comparator가 `equals()`와 어긋나면 같은 `record` 예제도 컬렉션마다 전혀 다르게 보일 수 있다.
