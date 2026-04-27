# Natural Ordering in TreeSet and TreeMap

> 한 줄 요약: `Comparator`를 직접 넘기지 않은 `TreeSet`/`TreeMap`도 안전지대가 아니며, natural ordering의 `compareTo() == 0`이면 같은 원소나 같은 key 자리로 판단되어 중복 무시와 값 덮어쓰기가 생길 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: treeset treemap natural ordering compareto bridge basics, treeset treemap natural ordering compareto bridge beginner, treeset treemap natural ordering compareto bridge intro, java basics, beginner java, 처음 배우는데 treeset treemap natural ordering compareto bridge, treeset treemap natural ordering compareto bridge 입문, treeset treemap natural ordering compareto bridge 기초, what is treeset treemap natural ordering compareto bridge, how to treeset treemap natural ordering compareto bridge
> 관련 문서:
> - [Language README](../README.md)
> - [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
> - [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
> - [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)

> retrieval-anchor-keywords: natural ordering in treeset and treemap, java treeset natural ordering duplicate, java treemap natural ordering replace value, java treemap compareTo same key, java compareTo tree set map surprise, comparable compareTo duplicate surprise, no comparator treeset treemap, new TreeSet natural ordering, new TreeMap natural ordering, compareTo 0 same element, compareTo 0 same key slot, sorted collection natural ordering duplicate, sorted map natural ordering value replacement, beginner comparable sorted collections, navigableset natural ordering lookup, navigablemap natural ordering lookup, first last floor ceiling compareTo order, mutable compareTo field treeset treemap, bigdecimal sorted collection surprise, bigdecimal compareTo equals mismatch

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 요약 표](#한-장-요약-표)
- [예제에 쓸 natural ordering](#예제에-쓸-natural-ordering)
- [`TreeSet`: `compareTo() == 0`이면 왜 하나만 남을까](#treeset-compareto--0이면-왜-하나만-남을까)
- [`TreeMap`: `compareTo() == 0`이면 왜 값이 덮어써질까](#treemap-compareto--0이면-왜-값이-덮어써질까)
- [`compareTo()`에 tie-breaker를 넣으면 어떻게 달라질까](#compareto에-tie-breaker를-넣으면-어떻게-달라질까)
- [explicit `Comparator` 예제와 같은 surprise다](#explicit-comparator-예제와-같은-surprise다)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

`TreeSet`과 `TreeMap` 예제를 처음 볼 때는 보통 이런 형태를 먼저 만난다.

```java
Set<Student> students = new TreeSet<>(Comparator.comparing(Student::name));
```

이때는 "아, comparator가 이름만 보니까 이름이 같으면 하나로 합쳐질 수 있구나"라고 이해하기 쉽다.

그런데 아래처럼 comparator를 직접 넘기지 않으면 안전하다고 착각하기 쉽다.

```java
Set<Student> students = new TreeSet<>();
Map<Student, String> seats = new TreeMap<>();
```

핵심은 이것이다.

- `TreeSet`/`TreeMap`은 항상 비교 규칙이 필요하다
- 생성자에 `Comparator`를 넘기지 않으면 key나 원소의 natural ordering을 사용한다
- natural ordering은 보통 클래스 안의 `compareTo()`다
- 따라서 `compareTo() == 0`도 explicit `Comparator.compare(...) == 0`과 같은 surprise를 만들 수 있다

이 문서는 `Comparator`를 직접 넘기지 않은 상황만 좁혀서 본다.

## 먼저 잡을 mental model

초보자용 기억법은 이 한 줄이면 충분하다.

> `new TreeSet<>()`와 `new TreeMap<>()`은 "비교 규칙이 없다"가 아니라 "객체의 `compareTo()`를 비교 규칙으로 쓴다"는 뜻이다.

`TreeSet`/`TreeMap` 안에서 `compareTo()`는 단순히 "누가 앞에 오나"만 정하지 않는다.

- `compareTo()`가 음수면 왼쪽, 양수면 오른쪽으로 간다
- `compareTo()`가 `0`이면 같은 자리라고 본다
- 같은 자리라면 `TreeSet`은 새 원소를 따로 보관하지 않을 수 있다
- 같은 자리라면 `TreeMap`은 같은 key로 보고 값을 바꿀 수 있다

즉 natural ordering에서도 `0`은 단순한 동점 표시가 아니라 "같은 칸" 판정이다.

## 한 장 요약 표

| 생성 코드 | 비교 규칙 출처 | `0`이면 어떻게 보나 |
|---|---|---|
| `new TreeSet<>()` | 원소의 `compareTo()` | 같은 원소 자리 |
| `new TreeMap<>()` | key의 `compareTo()` | 같은 key 자리 |
| `new TreeSet<>(comparator)` | 넘긴 `Comparator` | 같은 원소 자리 |
| `new TreeMap<>(comparator)` | 넘긴 `Comparator` | 같은 key 자리 |

차이는 규칙이 어디서 오느냐뿐이다.

- 클래스 안에서 오면 `Comparable.compareTo()`
- 생성자 밖에서 주면 `Comparator.compare(...)`

sorted collection 안에서는 둘 다 `0`의 의미가 강하다.

## 예제에 쓸 natural ordering

예제로 학생을 이름순으로 정렬하고 싶다고 해 보자.

```java
record Student(long id, String name) implements Comparable<Student> {
    @Override
    public int compareTo(Student other) {
        return this.name.compareTo(other.name);
    }
}
```

이 코드는 "학생의 natural ordering은 이름순"이라고 말한다.

하지만 주의할 점이 있다.

- record의 `equals()`는 `id`와 `name`을 모두 본다
- 위 `compareTo()`는 `name`만 본다
- 그래서 `id`가 달라도 `name`이 같으면 `compareTo()`는 `0`을 반환한다

이제 이 클래스를 `TreeSet`과 `TreeMap`에 넣어 보자.

## `TreeSet`: `compareTo() == 0`이면 왜 하나만 남을까

아래 코드에는 explicit `Comparator`가 없다.

```java
import java.util.TreeSet;

record Student(long id, String name) implements Comparable<Student> {
    @Override
    public int compareTo(Student other) {
        return this.name.compareTo(other.name);
    }
}

TreeSet<Student> students = new TreeSet<>();

boolean firstAdded = students.add(new Student(1L, "Mina"));
boolean secondAdded = students.add(new Student(2L, "Mina"));

System.out.println(firstAdded);  // true
System.out.println(secondAdded); // false
System.out.println(students.size()); // 1
```

왜 두 번째 `add`가 `false`일까?

- 두 `Student`는 `id`가 다르므로 record 기준 `equals()`는 `false`다
- 하지만 `compareTo()`는 이름만 비교한다
- 둘 다 `"Mina"`라서 `compareTo()` 결과가 `0`이다
- `TreeSet`은 둘을 같은 원소 자리로 보고 두 번째 원소를 따로 넣지 않는다

즉 `TreeSet`에서는 explicit `Comparator`가 없어도 `compareTo() == 0`이면 중복처럼 보일 수 있다.

## `TreeMap`: `compareTo() == 0`이면 왜 값이 덮어써질까

`TreeMap`에서도 같은 일이 key 쪽에서 일어난다.

```java
import java.util.TreeMap;

record Student(long id, String name) implements Comparable<Student> {
    @Override
    public int compareTo(Student other) {
        return this.name.compareTo(other.name);
    }
}

TreeMap<Student, String> seats = new TreeMap<>();

String firstPrevious = seats.put(new Student(1L, "Mina"), "front");
String secondPrevious = seats.put(new Student(2L, "Mina"), "back");

System.out.println(firstPrevious);  // null
System.out.println(secondPrevious); // front
System.out.println(seats.size());   // 1
System.out.println(seats.get(new Student(99L, "Mina"))); // back
System.out.println(seats.firstKey()); // Student[id=1, name=Mina]
```

여기서도 explicit `Comparator`는 없다.

하지만 `TreeMap`은 key를 비교해야 하므로 `Student.compareTo()`를 사용한다.

- 첫 번째 key: `Student(1, "Mina")`
- 두 번째 key: `Student(2, "Mina")`
- 조회 key: `Student(99, "Mina")`

셋은 `equals()`로 보면 서로 다르다.
하지만 `compareTo()`는 `name`만 보므로 셋 모두 같은 key 자리로 간다.

그래서 결과가 이렇게 보인다.

- 첫 번째 `put`은 새 key 자리라서 이전 값이 `null`이다
- 두 번째 `put`은 같은 key 자리라서 이전 값 `"front"`를 `"back"`으로 바꾼다
- `size()`는 `1`이다
- `new Student(99, "Mina")`로 조회해도 같은 key 자리라서 `"back"`을 찾는다

중요한 세부 사항도 하나 있다.

> `TreeMap`은 보통 두 번째 key 객체를 따로 저장하지 않고, 기존 key 자리의 value를 바꾼다.

그래서 위 예제에서 `firstKey()`는 여전히 첫 번째로 넣은 `Student[id=1, name=Mina]`로 보일 수 있다.
초보자 관점에서는 "key 객체가 완전히 교체되었다"보다 "같은 key 자리의 value가 교체되었다"라고 이해하는 편이 정확하다.

## `compareTo()`에 tie-breaker를 넣으면 어떻게 달라질까

이름이 같아도 `id`가 다르면 다른 학생으로 보관하고 싶다면 `compareTo()`가 둘을 끝까지 구분해야 한다.

```java
record Student(long id, String name) implements Comparable<Student> {
    @Override
    public int compareTo(Student other) {
        int nameResult = this.name.compareTo(other.name);
        if (nameResult != 0) {
            return nameResult;
        }
        return Long.compare(this.id, other.id);
    }
}
```

이제 natural ordering은 "이름순, 이름이 같으면 id순"이다.

| 데이터 | name-only `compareTo()` | name-then-id `compareTo()` |
|---|---|---|
| `Student(1, "Mina")`, `Student(2, "Mina")` | `0` | `0`이 아님 |
| `TreeSet` 결과 | 하나만 남을 수 있음 | 둘 다 남음 |
| `TreeMap` 결과 | 같은 key 자리라 value 교체 | 서로 다른 key 자리 |

tie-breaker는 정렬을 보기 좋게 만드는 장식만이 아니다.
`TreeSet`/`TreeMap`에서는 서로 다른 원소나 key를 구분하는 마지막 규칙이 된다.

## explicit `Comparator` 예제와 같은 surprise다

두 코드는 모양만 다르고 sorted collection 입장에서는 같은 종류의 규칙이다.

| 방식 | 코드 모양 | 비교 규칙 |
|---|---|---|
| natural ordering | `new TreeSet<>()` | `Student.compareTo(...)` |
| explicit comparator | `new TreeSet<>(Comparator.comparing(Student::name))` | 넘긴 comparator |

따라서 아래 두 문장은 같은 의미로 읽어야 한다.

- `compareTo() == 0`이면 같은 자리
- `Comparator.compare(...) == 0`이면 같은 자리

`List.sort(...)`에서는 둘이 "정렬상 동점" 정도로 끝날 수 있다.
하지만 `TreeSet`/`TreeMap`에서는 그 동점이 저장 여부와 값 교체에 직접 영향을 준다.

## 초보자가 자주 헷갈리는 지점

- `Comparator`를 안 넘겼다고 `equals()`로 중복 판단하는 것이 아니다. natural ordering의 `compareTo()`를 쓴다.
- `compareTo() == 0`은 `equals() == true`와 같은 말이 아니다. 다만 `TreeSet`/`TreeMap` 안에서는 같은 자리로 취급된다.
- `TreeSet`에서 두 번째 `add`가 `false`면 객체가 이상하게 사라진 것이 아니라 `compareTo()`가 구분하지 못한 것이다.
- `TreeMap`에서 두 번째 `put`이 값을 덮어쓰면 key reference가 같아서가 아니라 `compareTo()`가 같은 key 자리라고 판단했을 수 있다.
- `TreeMap`에서 value는 바뀌어도 저장된 key 객체는 처음 넣은 객체로 남을 수 있다.
- `Comparator`도 없고 원소/key가 `Comparable`도 아니면, 삽입 시점에 비교할 방법이 없어 예외가 날 수 있다.

## 빠른 체크리스트

- `new TreeSet<>()`는 원소의 `compareTo()`로 정렬하고 중복 자리를 판단한다
- `new TreeMap<>()`는 key의 `compareTo()`로 정렬하고 같은 key 자리를 판단한다
- `compareTo() == 0`이면 `TreeSet`에서는 같은 원소처럼 보일 수 있다
- `compareTo() == 0`이면 `TreeMap`에서는 같은 key처럼 보여 value가 교체될 수 있다
- `equals()`와 `compareTo()`가 보는 필드가 다르면 sorted collection surprise가 생길 수 있다
- natural ordering을 직접 만들 때는 정말 같은 객체로 볼 때만 `0`이 나오게 설계한다
- 다른 객체를 모두 유지해야 하면 `compareTo()` 끝에 tie-breaker를 넣는다

## 어떤 문서를 다음에 읽으면 좋은가

- `Comparable`, `Comparator`, natural ordering의 큰 그림을 먼저 잡으려면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- explicit `Comparator`를 넘긴 `TreeSet`/`TreeMap`에서도 같은 surprise가 생기는 모습을 보려면 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- `compareTo()`가 보는 mutable 필드를 삽입 후 바꿨을 때 조회와 정렬이 왜 깨지는지 보려면 [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
- `HashSet`과 `TreeSet`의 중복 기준 차이를 equality까지 같이 보고 싶다면 [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- `equals()`와 identity 기초가 헷갈리면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- 계약을 더 엄밀하게 보려면 [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)

## 한 줄 정리

`Comparator`를 직접 넘기지 않은 `TreeSet`/`TreeMap`도 원소나 key의 `compareTo()`를 사용하므로, `compareTo() == 0`이 정말 같은 것일 때만 나오게 설계하지 않으면 중복 무시와 value 덮어쓰기 surprise가 생긴다.
