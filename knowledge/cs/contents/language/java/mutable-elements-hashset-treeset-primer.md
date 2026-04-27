# Mutable Elements in HashSet and TreeSet Primer

> 한 줄 요약: `HashSet`과 `TreeSet`에 넣은 뒤 원소의 "같다고 판단하는 값"이나 "정렬에 쓰는 값"을 바꾸면, 컬렉션이 원소를 새 자리로 옮겨 주지 않아서 `contains()`와 `remove()` 기대가 깨질 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: mutable elements hashset treeset primer basics, mutable elements hashset treeset primer beginner, mutable elements hashset treeset primer intro, java basics, beginner java, 처음 배우는데 mutable elements hashset treeset primer, mutable elements hashset treeset primer 입문, mutable elements hashset treeset primer 기초, what is mutable elements hashset treeset primer, how to mutable elements hashset treeset primer
> 관련 문서:
> - [Language README](../README.md)
> - [Mutable Element Pitfalls in List and Set](./mutable-element-pitfalls-list-set-primer.md)
> - [Java Collections 성능 감각](./collections-performance.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md)
> - [HashSet Mutable Element Removal Drill](./hashset-mutable-element-removal-drill.md)
> - [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

> retrieval-anchor-keywords: language-java-00112, mutable elements in hashset and treeset primer, hashset treeset mutable element beginner, mutate set element after insertion java, hashset contains false after mutation beginner, hashset remove false after mutation beginner, treeset contains false after mutation beginner, treeset remove false after mutation beginner, mutating equality field after add set, mutating ordering field after add set, set element moved expectation bug, equals hashCode compareTo mutation set primer, java set mutation trap beginner, hashset treeset mutation comparison, mutable element pitfalls list set, debug mutable set element, collection prints element but remove fails java, 자바 set 원소 변경 함정, 자바 hashset treeset contains remove 실패, equals 필드 변경 set 버그, compareTo 필드 변경 set 버그, 정렬 set 원소 변경 주의

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 화면 비교표](#한-화면-비교표)
- [`HashSet`: equality 기준이 바뀌면 찾는 서랍이 달라진다](#hashset-equality-기준이-바뀌면-찾는-서랍이-달라진다)
- [`TreeSet`: ordering 기준이 바뀌면 찾는 길이 달라진다](#treeset-ordering-기준이-바뀌면-찾는-길이-달라진다)
- [왜 `contains()`와 `remove()`가 같이 흔들리나](#왜-contains와-remove가-같이-흔들리나)
- [안전한 기본 패턴](#안전한-기본-패턴)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [빠른 체크리스트](#빠른-체크리스트)
- [다음에 읽으면 좋은 문서](#다음에-읽으면-좋은-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

초보자는 보통 이렇게 기대한다.

- `Set`에 넣은 객체는 조금 바꿔도 계속 잘 찾을 수 있을 것이다
- 같은 객체 reference를 들고 있으면 `contains()`와 `remove()`는 당연히 될 것이다
- `TreeSet`은 자동 정렬이니 값이 바뀌면 내부 자리도 알아서 맞춰질 것이다

하지만 실제로는 이런 장면이 나온다.

- `HashSet.contains(element)`가 `false`다
- `HashSet.remove(element)`가 실패한다
- `TreeSet.contains(element)`가 `false`다
- `TreeSet.remove(element)`가 실패하거나 이상하게 보인다

핵심은 하나다.

> `Set`은 원소를 넣을 때의 규칙으로 자리를 잡고, 원소 필드 변화를 감시해서 자동 재배치하지 않는다.

이 문서는 그 함정을 `HashSet`과 `TreeSet` 비교 한 장으로 묶어 설명한다.

## 먼저 잡을 mental model

초보자용 기억법은 아래 두 줄이면 충분하다.

- `HashSet`은 "이 원소가 어느 서랍에 있나?"를 `hashCode()`와 `equals()`로 찾는다
- `TreeSet`은 "이 원소가 어느 길로 가야 하나?"를 `compareTo()`나 `Comparator`로 찾는다

둘 다 공통점이 있다.

- 넣을 때 규칙으로 자리를 정한다
- 넣은 뒤 기준 필드가 바뀌어도 자동으로 다시 넣지 않는다

즉 "객체 값이 바뀌었다"와 "컬렉션 안 자리도 바뀌었다"는 같은 말이 아니다.

## 한 화면 비교표

| 질문 | `HashSet` | `TreeSet` |
|---|---|---|
| 원소 위치를 정할 때 보는 것 | `hashCode()`와 같은 bucket 안의 `equals()` | `compareTo()` 또는 `Comparator` |
| 삽입 후 바꾸면 위험한 필드 | `equals()`/`hashCode()` 참여 필드 | ordering 비교에 참여하는 필드 |
| mutation 뒤 흔한 증상 | `contains`, `remove` 실패 | `contains`, `remove`, 탐색 순서 기대 어긋남 |
| 초보자용 안전 규칙 | equality 기준 필드를 바꾸지 않는다 | ordering 기준 필드를 바꾸지 않는다 |

짧게 외우면 이렇다.

- `HashSet`: "같다고 판단하는 값"을 넣은 뒤 바꾸지 않는다
- `TreeSet`: "정렬에 쓰는 값"을 넣은 뒤 바꾸지 않는다

## `HashSet`: equality 기준이 바뀌면 찾는 서랍이 달라진다

```java
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

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
}

Set<User> users = new HashSet<>();
User user = new User("mina");
users.add(user);

System.out.println(users.contains(user)); // true

user.rename("momo");

System.out.println(users.contains(user)); // false 가능
System.out.println(users.remove(user));   // false 가능
```

왜 이럴까?

1. 넣을 때는 `"mina"` 기준 `hashCode()`로 bucket을 정했다
2. 원소는 그 bucket에 그대로 남아 있다
3. 지금은 `"momo"` 기준 `hashCode()`로 다른 bucket을 찾을 수 있다
4. 그래서 같은 객체 reference를 넘겨도 못 찾을 수 있다

핵심은 `HashSet`이 객체 reference 자체를 바로 찾는 것이 아니라, 먼저 현재 hash 경로를 계산한다는 점이다.

## `TreeSet`: ordering 기준이 바뀌면 찾는 길이 달라진다

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
}

Comparator<Task> byPriorityThenId =
        Comparator.comparingInt(Task::priority)
                .thenComparingLong(Task::id);

TreeSet<Task> tasks = new TreeSet<>(byPriorityThenId);
Task task = new Task(1L, 10);
tasks.add(task);

System.out.println(tasks.contains(new Task(1L, 10))); // true

task.changePriority(30);

System.out.println(tasks.contains(task));             // false 가능
System.out.println(tasks.remove(task));               // false 가능
System.out.println(tasks.contains(new Task(1L, 30))); // false 가능
```

`TreeSet`에서는 bucket 대신 비교 경로가 중요하다.

1. 넣을 때는 `priority=10` 기준으로 트리 경로를 따라 자리를 잡았다
2. 원소는 그 node 위치에 그대로 남아 있다
3. 지금 `contains`와 `remove`는 `priority=30` 기준 새 경로를 따라간다
4. 그래서 현재 값으로는 맞는 것 같은데도 못 찾을 수 있다

초보자 기준으로는 이렇게 기억하면 충분하다.

> `TreeSet`은 "값이 바뀌면 자동 재정렬"이 아니라 "다음 삽입/조회 때 현재 비교값으로 길을 찾는 컬렉션"이다.

## 왜 `contains()`와 `remove()`가 같이 흔들리나

두 메서드는 보통 같은 길찾기 규칙을 공유한다.

| 컬렉션 | `contains()`와 `remove()`가 의존하는 것 |
|---|---|
| `HashSet` | 현재 `hashCode()`와 `equals()` |
| `TreeSet` | 현재 comparator 결과 또는 `compareTo()` |

그래서 삽입 후 기준 필드를 바꾸면 둘 다 같이 흔들리기 쉽다.

- `contains()`가 못 찾으면 `remove()`도 같은 이유로 실패하기 쉽다
- 출력에 원소가 보여도 lookup 경로가 어긋나 있으면 실패할 수 있다

즉 "보인다"와 "찾을 수 있다"는 같은 보장이 아니다.

## 안전한 기본 패턴

가장 안전한 기본값은 두 가지다.

1. `Set` 원소를 불변으로 만든다
2. 꼭 바꿔야 하면 제거 후 수정 후 재삽입한다

예시는 이렇게 생각하면 된다.

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

더 안전한 설계는 아예 새 객체를 만드는 것이다.

```java
record UserKey(String login) {}
record TaskKey(long id, int priority) {}
```

## 초보자가 자주 헷갈리는 지점

- 같은 객체 reference면 항상 찾을 수 있다고 생각한다
- `HashSet`과 `TreeSet`이 둘 다 그냥 "중복 없는 집합"이므로 같은 방식으로 찾는다고 생각한다
- 출력에 원소가 보이면 `contains()`와 `remove()`도 반드시 될 거라고 생각한다
- `TreeSet`이 자동 정렬이니 값이 바뀌면 내부 위치도 자동 갱신된다고 생각한다
- `equals()`와 `hashCode()` 문제와 comparator 문제를 같은 말로 섞어 버린다

## 빠른 체크리스트

- 이 원소가 `HashSet` 안에 있는가
- 그렇다면 바꾸려는 필드가 `equals()`/`hashCode()`에 들어가는가
- 이 원소가 `TreeSet` 안에 있는가
- 그렇다면 바꾸려는 필드가 `compareTo()`나 `Comparator`에 들어가는가
- 기준 필드를 바꿔야 한다면 제거 후 수정 후 재삽입 순서를 지키는가
- 가능하면 원소를 불변 값 객체로 설계했는가

## 다음에 읽으면 좋은 문서

| 지금 궁금한 것 | 다음 문서 |
|---|---|
| `List`와 `Set`에서 mutation 영향 차이를 먼저 한 장으로 보고 싶다 | [Mutable Element Pitfalls in List and Set](./mutable-element-pitfalls-list-set-primer.md) |
| "`HashSet`에서 `contains()`와 `remove()`가 왜 같이 깨지는지 먼저 짧게 예측하고 싶다" | [HashSet Mutable Element Removal Drill](./hashset-mutable-element-removal-drill.md) |
| `HashSet` 쪽 함정을 더 자세히 보고 싶다 | [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md) |
| `TreeSet`과 `TreeMap`의 comparator 함정을 더 자세히 보고 싶다 | [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md) |
| 왜 `HashSet`과 `TreeSet`의 중복 기준이 다른지 먼저 다시 잡고 싶다 | [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md) |
| equality와 ordering 계약을 처음부터 다시 보고 싶다 | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |
| 불변 객체 설계 감각을 먼저 잡고 싶다 | [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md) |

## 한 줄 정리

`HashSet`은 equality 기준, `TreeSet`은 ordering 기준으로 원소 자리를 잡는데 둘 다 삽입 후 기준 필드 변화까지 자동 복구하지 않으므로, 기준 필드를 바꾸면 `contains()`와 `remove()` 기대가 깨질 수 있다.
