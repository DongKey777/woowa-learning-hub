# Comparator Consistency With `equals()` Bridge

> 한 줄 요약: `HashSet`은 `equals()`/`hashCode()`를, `TreeSet`/`TreeMap`은 `compare(...) == 0`을 더 직접적으로 보므로, comparator가 `equals()`와 어긋나면 같은 `record` 예제도 컬렉션마다 다르게 보일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- [Record and Value Object Equality](./record-value-object-equality-basics.md)
- [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)

retrieval-anchor-keywords: comparator consistency with equals, compare zero equals mismatch, treeset treemap comparator zero, hashset vs treeset equality, java record comparator mismatch, 자바 comparator equals 일관성, 처음 배우는데 comparator consistency, why treeset removes duplicate, how compare zero works, sorted collection equality mismatch, comparator tie breaker beginner, compare zero same key

## 먼저 잡을 mental model

가장 안전한 beginner 기억법은 이 두 줄이다.

- `HashSet`은 `equals()`/`hashCode()` 기준으로 같은 원소를 판단한다.
- `TreeSet`/`TreeMap`은 `compare(...) == 0`이면 같은 자리로 본다.

즉 comparator에서 `0`이 나온다는 말은 sorted collection 안에서는 단순 동점이 아니라 "같은 원소 칸" 또는 "같은 key 칸"에 더 가깝다.

## 한 화면 비교 예제

```java
record Student(long id, String name) {}

Comparator<Student> byNameOnly =
        Comparator.comparing(Student::name);

Student first = new Student(1L, "Mina");
Student second = new Student(2L, "Mina");
```

이 예제에서 기준은 갈라진다.

- `first.equals(second)`는 `false`
- `byNameOnly.compare(first, second)`는 `0`

즉 equality 기준과 ordering 기준이 서로 다른 상태다.

## 컬렉션별로 왜 결과가 갈리나

| 컬렉션 | 먼저 보는 기준 | 결과 |
|---|---|---|
| `HashSet<Student>` | `equals()`/`hashCode()` | 2개 다 들어간다 |
| `TreeSet<Student>` + `byNameOnly` | `compare(...) == 0` | 1개만 남는다 |
| `TreeMap<Student, String>` + `byNameOnly` | `compare(...) == 0` | 같은 key 자리라 값이 덮어써진다 |

핵심은 컬렉션이 이상한 것이 아니라 각 컬렉션이 자기 규칙대로 움직인다는 점이다.

## `TreeMap`이 특히 헷갈리는 이유

```java
Map<Student, String> map = new TreeMap<>(byNameOnly);
map.put(first, "front");
map.put(second, "back");

System.out.println(map.size()); // 1
System.out.println(map.get(new Student(99L, "Mina"))); // back
```

초보자는 `new Student(99L, "Mina")`가 전혀 다른 객체인데도 조회가 되는 장면에서 많이 막힌다.

이유는 단순하다.

1. `TreeMap`은 key reference보다 comparator 기준을 먼저 본다.
2. 이름만 비교하면 `"Mina"`는 모두 같은 key 자리다.
3. 그래서 두 번째 `put`이 value를 덮어쓰고, 조회도 같은 이름이면 같은 자리로 찾는다.

## 언제 tie-breaker가 필요한가

이름이 같아도 `id`가 다르면 다른 학생으로 남겨야 한다면 comparator를 끝까지 나눠야 한다.

```java
Comparator<Student> byNameThenId =
        Comparator.comparing(Student::name)
                .thenComparingLong(Student::id);
```

이제는 다음이 같이 맞춰진다.

- `compare(first, second) != 0`
- `equals()`도 `false`

즉 "다른 객체면 sorted collection에서도 다른 자리"라는 기대와 더 잘 맞는다.

## 초보자 공통 혼동

- `compare(...) == 0`을 단순 정렬 동점으로만 이해하기 쉽다.
- `record`가 `equals()`를 자동 생성하니 `TreeSet`도 같은 기준일 거라고 기대하기 쉽다.
- `HashSet`에서 잘 되면 `TreeSet`/`TreeMap`도 같을 거라고 생각하기 쉽다.

빠른 점검 질문은 세 가지면 충분하다.

1. 지금 컬렉션이 `HashSet`인가, `TreeSet`/`TreeMap`인가?
2. comparator가 보는 필드와 `equals()`가 보는 필드가 같은가?
3. `compare(...) == 0`이어도 정말 같은 원소나 같은 key로 합쳐도 되는가?

## 다음에 어디로 이어서 읽을까

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| `TreeSet` comparator를 어떻게 설계하지? | [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md) |
| hash 계열과 sorted 계열 차이를 더 짧게 보고 싶다 | [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md) |
| value object equality 기준부터 다시 잡고 싶다 | [Record and Value Object Equality](./record-value-object-equality-basics.md) |

## 한 줄 정리

`HashSet`은 `equals()` 기준으로, `TreeSet`/`TreeMap`은 `compare(...) == 0` 기준으로 같은 자리를 판단하므로, comparator가 `equals()`와 어긋나면 같은 `record` 예제도 컬렉션마다 전혀 다르게 보일 수 있다.
