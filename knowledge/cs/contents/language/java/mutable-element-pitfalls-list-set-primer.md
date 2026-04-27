# Mutable Element Pitfalls in List and Set

> 한 줄 요약: `List`는 원소를 넣은 뒤 값을 바꿔도 구조 자체는 보통 유지되지만, `Set`은 `equals()`/`hashCode()`나 정렬 기준 필드를 바꾸면 `contains()`/`remove()`/디버깅 감각이 쉽게 깨진다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: mutable element pitfalls list set primer basics, mutable element pitfalls list set primer beginner, mutable element pitfalls list set primer intro, java basics, beginner java, 처음 배우는데 mutable element pitfalls list set primer, mutable element pitfalls list set primer 입문, mutable element pitfalls list set primer 기초, what is mutable element pitfalls list set primer, how to mutable element pitfalls list set primer
> 관련 문서:
> - [Language README](../README.md)
> - [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
> - [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Mutable Elements in HashSet and TreeSet Primer](./mutable-elements-hashset-treeset-primer.md)
> - [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md)
> - [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md)
> - [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
> - [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

> retrieval-anchor-keywords: language-java-00114, mutable element pitfalls in list and set, java mutable list element pitfall, java mutable set element pitfall, mutate element after add list set, list contains false after mutation java, list remove object false after mutation java, hashset contains false after mutation beginner, hashset remove false after mutation beginner, treeset contains false after mutation beginner, treeset remove false after mutation beginner, same object still not found set after mutation, collection prints element but remove fails java, debug mutable set element, equals hashCode compareTo mutation primer, list vs hashset vs treeset mutable state, 자바 list set 원소 변경 함정, 자바 list contains remove equals 변경, 자바 hashset treeset 원소 변경 디버깅, 자바 set contains remove 실패 디버깅, 컬렉션에 넣고 값 바꾸면 왜 안 찾지

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 화면 비교표](#한-화면-비교표)
- [`List`: 구조는 덜 깨지지만 비교 메서드는 흔들릴 수 있다](#list-구조는-덜-깨지지만-비교-메서드는-흔들릴-수-있다)
- [`HashSet`: 같은 객체인데도 못 찾는 대표 함정](#hashset-같은-객체인데도-못-찾는-대표-함정)
- [`TreeSet`: 값은 바뀌었는데 자리는 그대로다](#treeset-값은-바뀌었는데-자리는-그대로다)
- [디버깅할 때 바로 보는 순서](#디버깅할-때-바로-보는-순서)
- [안전한 기본 패턴](#안전한-기본-패턴)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

초보자는 보통 이렇게 기대한다.

- 컬렉션 안에 같은 객체가 들어 있으니 나중에도 당연히 찾을 수 있을 것이다
- `List`와 `Set` 모두 "원소를 저장하는 통"이므로 값을 조금 바꿔도 비슷하게 동작할 것이다
- 출력에 원소가 보이면 `contains()`와 `remove()`도 될 것이다

하지만 실제로는 컬렉션마다 함정이 다르다.

- `List`는 순서만 저장하므로 구조는 대체로 유지된다
- 대신 `contains`, `indexOf`, `remove(Object)`는 현재 `equals()` 기준으로 다시 비교한다
- `HashSet`은 hash 경로가 어긋나면 같은 객체인데도 못 찾을 수 있다
- `TreeSet`은 정렬 경로가 어긋나면 현재 값과 내부 위치가 서로 다른 이야기를 할 수 있다

즉 "원소를 바꿨다"보다 먼저 봐야 할 질문은 이것이다.

> 이 컬렉션은 원소를 찾을 때 무엇을 기준으로 길을 찾는가?

## 먼저 잡을 mental model

초보자용 기억법은 아래 세 줄이면 충분하다.

- `List`: 넣은 순서대로 줄 세운다
- `HashSet`: `hashCode()`와 `equals()`로 원소를 찾는다
- `TreeSet`: `compareTo()`나 `Comparator`로 원소를 찾는다

여기서 핵심 차이는 이것이다.

- `List`는 원소가 바뀌어도 "자리 재배치" 문제가 크지 않다
- `HashSet`과 `TreeSet`은 넣을 때 정한 lookup 경로를 자동 복구하지 않는다

그래서 beginner 관점에서는 이렇게 외우는 편이 안전하다.

> mutable 원소는 `List`보다 `Set`에서 더 위험하다.
> 특히 `Set`이 보는 기준 필드를 바꾸면 "보이는데 못 찾는" 버그가 나온다.

## 한 화면 비교표

| 컬렉션 | 원소 저장의 핵심 | 바뀌면 특히 위험한 것 | 흔한 증상 |
|---|---|---|---|
| `List` | 순서 | `equals()`가 보는 필드 | `contains`, `indexOf`, `remove(Object)` 결과 변화 |
| `HashSet` | hash bucket | `equals()`/`hashCode()`가 보는 필드 | `contains`, `remove` 실패 |
| `TreeSet` | 정렬 경로 | `compareTo()`/`Comparator`가 보는 필드 | `contains`, `remove`, `first`, `floor` 기대 어긋남 |

같은 "원소 변경"이라도 결과가 다른 이유를 한 줄로 말하면 아래와 같다.

- `List`는 "비교 결과"만 흔들리기 쉽다
- `Set`은 "비교 결과 + 내부에서 찾아가는 길"이 함께 흔들릴 수 있다

## `List`: 구조는 덜 깨지지만 비교 메서드는 흔들릴 수 있다

`List`는 보통 beginner가 생각하는 것과 가장 가깝다.
원소 값을 바꿔도 그 객체가 들어 있는 칸 자체가 자동으로 사라지지는 않는다.

```java
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

final class User {
    private String login;

    User(String login) {
        this.login = login;
    }

    void rename(String login) {
        this.login = login;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof User other)) return false;
        return Objects.equals(login, other.login);
    }

    @Override
    public int hashCode() {
        return Objects.hash(login);
    }

    @Override
    public String toString() {
        return "User{login=" + login + "}";
    }
}

List<User> users = new ArrayList<>();
User user = new User("mina");
users.add(user);

user.rename("momo");

System.out.println(users); // [User{login=momo}]
System.out.println(users.contains(user)); // true
System.out.println(users.contains(new User("mina"))); // false
System.out.println(users.remove(new User("mina"))); // false
```

핵심은 두 가지다.

- `List`는 같은 reference를 들고 있으면 그 객체는 그대로 들어 있다
- 하지만 `contains(new User("mina"))`처럼 새 객체로 찾을 때는 현재 `equals()` 기준이 달라졌으니 실패할 수 있다

즉 `List`의 mutation 문제는 주로 "비교 결과가 달라진다" 쪽이다.
반면 `HashSet`과 `TreeSet`은 한 단계 더 나가서 "길찾기 자체가 틀어진다".

## `HashSet`: 같은 객체인데도 못 찾는 대표 함정

```java
import java.util.HashSet;
import java.util.Set;

Set<User> users = new HashSet<>();
User user = new User("mina");
users.add(user);

user.rename("momo");

System.out.println(users); // [User{login=momo}]
System.out.println(users.contains(user)); // false 가능
System.out.println(users.remove(user)); // false 가능
System.out.println(users.contains(new User("momo"))); // false 가능
```

왜 `List`보다 더 이상하게 보일까?

1. `add(...)`할 때는 `"mina"` 기준 hash로 bucket을 정했다
2. 원소는 그 bucket에 그대로 남아 있다
3. 지금 `contains(...)`와 `remove(...)`는 `"momo"` 기준 hash로 다른 bucket을 찾을 수 있다
4. 그래서 같은 객체 reference를 넘겨도 못 찾을 수 있다

초보자용 포인트는 이것이다.

> `HashSet`은 "객체를 기억"하는 것이 아니라, 현재 hash/equality 규칙으로 다시 찾아간다.

그래서 디버깅할 때 아래 장면이 나오면 mutable element를 의심하면 된다.

- `System.out.println(set)`에는 원소가 보인다
- 그런데 `contains(element)`가 `false`다
- `remove(element)`도 실패한다

## `TreeSet`: 값은 바뀌었는데 자리는 그대로다

```java
import java.util.Comparator;
import java.util.TreeSet;

final class Task {
    private final long id;
    private int priority;

    Task(long id, int priority) {
        this.id = id;
        this.priority = priority;
    }

    long id() {
        return id;
    }

    int priority() {
        return priority;
    }

    void changePriority(int priority) {
        this.priority = priority;
    }

    @Override
    public String toString() {
        return "Task{id=" + id + ", priority=" + priority + "}";
    }
}

Comparator<Task> byPriorityThenId =
        Comparator.comparingInt(Task::priority)
                .thenComparingLong(Task::id);

TreeSet<Task> tasks = new TreeSet<>(byPriorityThenId);
Task task = new Task(1L, 10);
tasks.add(task);

task.changePriority(30);

System.out.println(tasks); // [Task{id=1, priority=30}]
System.out.println(tasks.contains(task)); // false 가능
System.out.println(tasks.remove(task)); // false 가능
System.out.println(tasks.contains(new Task(1L, 30))); // false 가능
```

`TreeSet`은 hash bucket 대신 comparator가 만든 경로를 따라간다.

1. 넣을 때는 `priority=10` 기준으로 자리를 잡았다
2. 원소는 그 node 위치에 그대로 남아 있다
3. 지금은 `priority=30` 기준 경로로 탐색한다
4. 그래서 현재 값으로는 맞아 보여도 못 찾을 수 있다

여기서 beginner가 특히 당황하는 장면은 두 가지다.

- 출력에는 `priority=30`이 보이는데 `contains()`가 `false`다
- 자동 정렬 컬렉션인데도 값 변경 후 순서가 기대와 다르게 보인다

`TreeSet`의 핵심 오해를 한 줄로 정리하면 이렇다.

> 자동 정렬은 "삽입과 탐색 규칙"이지, 삽입 후 필드 변화까지 자동 재정렬한다는 뜻이 아니다.

## 디버깅할 때 바로 보는 순서

컬렉션에 원소가 보이는데 `contains()`나 `remove()`가 실패하면 아래 순서로 보면 된다.

1. 컬렉션이 `List`, `HashSet`, `TreeSet` 중 무엇인지 먼저 확인한다
2. `equals()`/`hashCode()`/`compareTo()`/`Comparator` 중 무엇이 lookup 기준인지 확인한다
3. 그 기준에 들어가는 필드가 `add(...)` 뒤에 바뀌었는지 확인한다
4. "같은 reference로 찾는지"와 "새 객체로 찾는지"를 구분해서 본다
5. 출력에 보이는데 못 찾는다면 lookup 경로 어긋남을 먼저 의심한다

짧은 판단표로 보면 아래와 같다.

| 증상 | 먼저 의심할 것 |
|---|---|
| `List`에서 `contains(new X(...))`가 갑자기 `false` | `equals()` 기준 필드 변경 |
| `HashSet`에서 같은 객체인데도 `contains(element)`가 `false` | `hashCode()`/`equals()` 기준 필드 변경 |
| `TreeSet`에서 출력 순서나 `first()`가 이상함 | comparator 기준 필드 변경 |
| 출력에는 있는데 `remove()`가 안 됨 | 삽입 후 기준 필드 변경 + 재삽입 누락 |

## 안전한 기본 패턴

가장 안전한 기본값은 아래 둘이다.

1. `Set` 원소는 가능하면 불변으로 만든다
2. 기준 필드를 꼭 바꿔야 하면 제거 후 수정 후 재삽입한다

```java
if (users.remove(user)) {
    user.rename("momo");
    users.add(user);
}
```

```java
if (tasks.remove(task)) {
    task.changePriority(30);
    tasks.add(task);
}
```

`List`에서는 같은 패턴이 항상 필요한 것은 아니다.
하지만 `contains`/`remove(Object)`를 equality 기준으로 자주 쓴다면, `List` 원소도 불변 쪽이 디버깅 비용이 적다.

## 초보자가 자주 헷갈리는 지점

- 같은 객체 reference면 컬렉션 종류와 무관하게 항상 찾을 수 있다고 생각한다
- `List`와 `Set` 모두 그냥 "객체 보관함"이라서 mutation 영향도 비슷하다고 생각한다
- 출력에 원소가 보이면 `contains()`와 `remove()`도 반드시 된다고 생각한다
- `TreeSet`의 자동 정렬을 "값이 바뀌면 내부 위치도 자동 갱신"으로 이해한다
- `HashSet` 문제와 `TreeSet` 문제를 둘 다 단순한 `equals()` 버그로만 본다

## 한 줄 정리

mutable 원소는 `List`에서는 주로 비교 결과를 흔들고, `HashSet`/`TreeSet`에서는 lookup 경로까지 깨뜨릴 수 있으므로, `Set` 안에 있는 동안에는 equality나 ordering 기준 필드를 바꾸지 않는 편이 가장 안전하다.
