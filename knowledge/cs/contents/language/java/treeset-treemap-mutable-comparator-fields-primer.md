# Mutable Fields Inside Sorted Collections

> 한 줄 요약: `TreeSet`/`TreeMap` 안에 들어간 뒤 comparator나 `compareTo()`가 보는 필드를 바꾸면, 객체의 현재 값과 트리 내부 위치가 어긋나서 정렬, 조회, 삭제가 이상해질 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)
- [HashSet vs TreeSet Beginner Bridge](../../data-structure/hashset-vs-treeset-beginner-bridge.md)


retrieval-anchor-keywords: mutable fields inside sorted collections, treeset mutable field bug, treemap mutable key bug, treeset contains false after mutation, treemap get null after key mutation, treeset 값 바꿨더니 contains false, treemap key 바꿨더니 get null, treeset 정렬이 안 바뀌어요, treemap 키 수정 왜 안 돼요, compareto mutable field bug, comparator depends on mutable field, immutable key sorted collection beginner, 처음 treeset 헷갈림, 왜 정렬 컬렉션 값 바꾸면 안 되나요, 언제 remove 후 reinsert 하나요
> 관련 문서:
> - [Language README](../README.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Mutable Elements in HashSet and TreeSet Primer](./mutable-elements-hashset-treeset-primer.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
> - [Priority Update Patterns](./priority-update-patterns-treeset-treemap-priorityqueue-bridge.md)
> - [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [HashSet vs TreeSet Beginner Bridge](../../data-structure/hashset-vs-treeset-beginner-bridge.md)
> - [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)

> retrieval-anchor-keywords: language-java-00063, mutable fields inside sorted collections, treeset mutable field bug, treemap mutable key bug, comparator depends on mutable field, compareTo mutable field bug, mutate element after insert treeset, mutate key after insert treemap, treeset contains false after mutation, treemap get null after key mutation, sorted collection broken ordering, sorted set lookup broken after mutation, sorted map lookup broken after mutation, comparator field changed after insertion, mutable priority treeset bug, immutable key sorted collection beginner

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 요약 표](#한-장-요약-표)
- [예제에 쓸 mutable 객체](#예제에-쓸-mutable-객체)
- [`TreeSet`: 값은 바뀌었는데 자리는 그대로다](#treeset-값은-바뀌었는데-자리는-그대로다)
- [`TreeMap`: key를 바꾸면 `get`도 길을 잃을 수 있다](#treemap-key를-바꾸면-get도-길을-잃을-수-있다)
- [안전하게 바꾸는 기본 패턴](#안전하게-바꾸는-기본-패턴)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

`TreeSet`과 `TreeMap`을 처음 배우면 보통 "자동 정렬되는 컬렉션"이라고 이해한다.
그래서 객체의 값을 바꾸면 컬렉션도 알아서 다시 정렬될 것처럼 기대하기 쉽다.

하지만 실제로는 이런 질문이 자주 생긴다.

- `TreeSet.first()`가 현재 값 기준으로 가장 작은 원소를 돌려주지 않는다
- `TreeSet.contains(...)`가 분명 있어 보이는 원소를 못 찾는다
- `TreeMap.get(...)`이 방금 key의 필드를 바꿨을 뿐인데 `null`을 돌려준다
- `thenComparing(...)`까지 넣었는데도 정렬이 깨진 것처럼 보인다

이 문서는 특히 `"TreeSet 값 바꿨더니 contains가 false예요"`, `"TreeMap key 수정했더니 get이 null이에요"` 같은 첫 질문이 깊은 구현 문서보다 먼저 여기로 오도록 만든 primer다.

핵심은 하나다.

- `TreeSet`/`TreeMap`은 삽입할 때 comparator가 알려 준 길을 따라 트리 안의 자리를 정한다
- 나중에 객체의 비교 기준 필드가 바뀌어도 그 객체를 자동으로 빼서 새 자리에 다시 넣지 않는다
- 그래서 "현재 필드 값"과 "트리 안에 놓인 자리"가 서로 다른 이야기를 하게 된다

이 문서는 그 감각을 `TreeSet`, `TreeMap`, 안전한 수정 패턴으로만 좁혀서 설명한다.

## 먼저 잡을 mental model

초보자용 기억법은 이 한 줄이면 충분하다.

> `TreeSet`/`TreeMap`은 객체를 넣을 때의 비교 결과로 자리를 잡고, 객체 안의 필드 변화를 감시하지 않는다.

상자에 주소 라벨을 붙여 창고 선반에 넣는다고 생각해 보자.

- 넣을 때 라벨이 `priority=10`이면 앞쪽 선반에 둔다
- 나중에 라벨만 `priority=30`으로 바꿔도 상자는 스스로 뒤쪽 선반으로 이동하지 않는다
- 검색하는 사람은 새 라벨 `priority=30`을 보고 뒤쪽 선반으로 가는데, 실제 상자는 아직 앞쪽 선반에 있을 수 있다

`TreeSet`/`TreeMap`의 조회도 비슷하다.
`contains`, `get`, `remove`, `floor`, `ceiling` 같은 메서드는 comparator가 만든 길을 따라간다.
객체가 예전 길에 놓여 있는데 현재 값으로 새 길을 찾으면 결과가 어긋날 수 있다.

## 한 장 요약 표

| 바꾸는 대상 | 보통 안전한가 | 이유 |
|---|---|---|
| comparator가 보지 않는 필드 | 대체로 안전 | 트리 안의 순서 기준이 변하지 않는다 |
| comparator가 보는 필드, 삽입 전 | 안전 | 아직 트리 안의 자리가 정해지지 않았다 |
| comparator가 보는 필드, 삽입 후 | 위험 | 트리 안의 기존 위치와 현재 비교 결과가 어긋난다 |
| `TreeMap`의 value 객체 | key 조회 기준에는 보통 안전 | `TreeMap` 정렬과 조회는 value가 아니라 key를 본다 |
| `TreeMap`의 key 객체 필드 | 위험 | key의 comparator 결과가 바뀌면 `get`/`remove`가 깨질 수 있다 |

비슷한 규칙이 해시 컬렉션에도 있다.

| 컬렉션 | 안정적으로 유지해야 하는 필드 |
|---|---|
| `HashSet`, `HashMap` key | `equals()`/`hashCode()`가 보는 필드 |
| `TreeSet`, `TreeMap` key | `compareTo()`나 `Comparator`가 보는 필드 |

이 문서는 두 번째 경우, 즉 sorted collection의 비교 기준 필드가 변하는 상황만 다룬다.

## 예제에 쓸 mutable 객체

아래 예제에서는 `Task`를 `priority` 오름차순, 같은 priority면 `id` 오름차순으로 정렬한다.

```java
import java.util.Comparator;
import java.util.TreeMap;
import java.util.TreeSet;

final class Task {
    private final int id;
    private int priority;

    Task(int id, int priority) {
        this.id = id;
        this.priority = priority;
    }

    int id() {
        return id;
    }

    int priority() {
        return priority;
    }

    void setPriority(int priority) {
        this.priority = priority;
    }

    @Override
    public String toString() {
        return "Task{id=" + id + ", priority=" + priority + "}";
    }
}

Comparator<Task> byPriorityThenId =
        Comparator.comparingInt(Task::priority)
                .thenComparingInt(Task::id);
```

여기서 중요한 점은 `id` tie-breaker가 있다는 것이다.
tie-breaker는 "서로 다른 task가 `compare == 0`으로 뭉개지는 문제"를 줄여 준다.
하지만 `priority` 자체를 삽입 후 바꾸는 문제까지 해결해 주지는 않는다.

## `TreeSet`: 값은 바뀌었는데 자리는 그대로다

먼저 세 task를 `TreeSet`에 넣는다.

```java
TreeSet<Task> tasks = new TreeSet<>(byPriorityThenId);

Task first = new Task(1, 10);
Task second = new Task(2, 20);
Task third = new Task(3, 30);

tasks.add(first);
tasks.add(second);
tasks.add(third);

System.out.println(tasks);
System.out.println(tasks.first());
System.out.println(tasks.contains(new Task(1, 10)));
```

출력은 자연스럽다.

```text
[Task{id=1, priority=10}, Task{id=2, priority=20}, Task{id=3, priority=30}]
Task{id=1, priority=10}
true
```

이제 `TreeSet` 안에 들어간 `first`의 `priority`를 바꾼다.

```java
first.setPriority(30);

System.out.println(tasks);
System.out.println(tasks.first());
System.out.println(tasks.contains(new Task(1, 30)));
System.out.println(tasks.floor(new Task(1, 30)));
System.out.println(tasks.ceiling(new Task(1, 30)));
```

가능한 출력은 이렇게 보일 수 있다.

```text
[Task{id=1, priority=30}, Task{id=2, priority=20}, Task{id=3, priority=30}]
Task{id=1, priority=30}
false
Task{id=2, priority=20}
Task{id=3, priority=30}
```

초보자에게 이상하게 보이는 지점은 세 가지다.

- 현재 값 기준으로는 `priority=20`인 `second`가 먼저여야 할 것 같은데, `first()`가 `priority=30`인 `first`를 돌려준다
- `Task{id=1, priority=30}`이 출력에 보이는데도 `contains(new Task(1, 30))`가 `false`일 수 있다
- `floor`와 `ceiling`도 현재 값 기준으로 기대한 이웃을 찾지 못할 수 있다

이 결과는 `TreeSet`이 갑자기 고장 난 것이 아니다.
`TreeSet`이 요구하는 전제를 깨뜨린 것이다.

> sorted collection 안에 있는 동안에는 comparator가 보는 값이 안정적이어야 한다.

## `TreeMap`: key를 바꾸면 `get`도 길을 잃을 수 있다

`TreeMap`에서는 문제가 key 쪽에서 더 위험하게 보인다.

```java
TreeMap<Task, String> ownerByTask = new TreeMap<>(byPriorityThenId);

Task first = new Task(1, 10);
Task second = new Task(2, 20);
Task third = new Task(3, 30);

ownerByTask.put(first, "Mina");
ownerByTask.put(second, "Jin");
ownerByTask.put(third, "Taro");

System.out.println(ownerByTask.get(new Task(1, 10)));
```

처음에는 key를 찾는다.

```text
Mina
```

그런데 map 안에 들어간 key 객체의 비교 기준 필드를 바꾸면 문제가 생긴다.

```java
first.setPriority(30);

System.out.println(ownerByTask);
System.out.println(ownerByTask.get(new Task(1, 30)));
System.out.println(ownerByTask.containsKey(new Task(1, 30)));
System.out.println(ownerByTask.floorKey(new Task(1, 30)));
System.out.println(ownerByTask.ceilingKey(new Task(1, 30)));
```

가능한 출력은 이렇게 보일 수 있다.

```text
{Task{id=1, priority=30}=Mina, Task{id=2, priority=20}=Jin, Task{id=3, priority=30}=Taro}
null
false
Task{id=2, priority=20}
Task{id=3, priority=30}
```

map 출력에는 `Task{id=1, priority=30}`이 보인다.
하지만 `get(new Task(1, 30))`은 그 key를 못 찾을 수 있다.

이유는 같다.

- entry는 예전에 `priority=10`이던 위치에 들어갔다
- key 객체의 현재 값은 `priority=30`으로 바뀌었다
- 새 조회 key는 comparator 기준으로 `priority=30` 위치를 찾아간다
- 실제 entry는 아직 예전 위치에 있으므로 검색 경로가 어긋날 수 있다

`TreeMap`에서는 특히 "key 객체는 map에 들어간 동안 비교 기준이 바뀌면 안 된다"라고 기억하는 편이 안전하다.
value 객체의 내부 상태를 바꾸는 것은 key 정렬과 직접 관련이 없지만, key 객체를 바꾸는 것은 조회 자체를 깨뜨릴 수 있다.

## 안전하게 바꾸는 기본 패턴

가장 안전한 설계는 sorted collection에 들어가는 key나 원소를 불변으로 만드는 것이다.

```java
record TaskKey(int id, int priority) {}
```

그래도 mutable 객체를 써야 한다면 기본 패턴은 "빼고, 바꾸고, 다시 넣기"다.

```java
if (tasks.remove(first)) {      // 아직 old priority 위치에 있을 때 제거
    first.setPriority(30);
    tasks.add(first);           // new priority 기준으로 다시 삽입
}
```

`TreeMap` key도 같은 방향으로 생각한다.

```java
String owner = ownerByTask.remove(first);  // old key 위치에서 먼저 제거
if (owner != null) {
    first.setPriority(30);
    ownerByTask.put(first, owner);         // new key 위치로 다시 삽입
}
```

이미 key나 원소를 바꿔 버렸다면 `remove`가 항상 믿을 만하게 동작한다고 가정하지 않는 편이 좋다.
그때는 새 `TreeSet`/`TreeMap`을 만들고 현재 객체들을 다시 넣어 트리를 재구성하는 편이 더 안전하다.

업데이트가 자주 일어나는 도메인이라면 구조를 바꾸는 것도 고려한다.

| 상황 | 더 안전한 방향 |
|---|---|
| id로 조회가 중요하고 priority는 자주 바뀜 | `Map<id, Task>`를 두고 필요할 때 정렬 |
| priority 순위가 필요하지만 값도 자주 바뀜 | remove-before-mutate-add를 한 곳에 캡슐화 |
| key 자체가 값 객체에 가까움 | immutable key를 새로 만들어 교체 |

## 초보자 혼동 포인트

- "객체 reference는 같은데 왜 못 찾나?" `TreeSet`/`TreeMap` 조회는 reference identity가 아니라 comparator 경로를 따라간다.
- "`toString()`에는 바뀐 값이 보이는데?" 객체 필드는 바뀌었다. 다만 트리 안의 node 위치가 자동으로 바뀐 것은 아니다.
- "`thenComparing(id)`를 넣었는데 왜 깨지나?" tie-breaker는 `compare == 0` 충돌을 줄여 주지만, 앞쪽 비교 필드를 삽입 후 바꾸는 문제는 막지 못한다.
- "`TreeMap` value를 바꾸는 것도 위험한가?" key comparator가 value를 보지 않는 일반적인 `TreeMap`에서는 value 변경이 key lookup을 깨뜨리지는 않는다. 위험한 것은 key의 비교 기준 필드 변경이다.
- "항상 같은 방식으로 깨지나?" 아니다. 트리 모양, 삽입 순서, 변경한 값에 따라 `contains`나 `remove`가 어떤 때는 되는 것처럼 보일 수도 있다. 그래서 더 위험하다.

## 빠른 체크리스트

- `TreeSet` 원소의 comparator 대상 필드는 컬렉션 안에 있는 동안 바꾸지 않는다
- `TreeMap` key의 comparator 대상 필드는 map 안에 있는 동안 바꾸지 않는다
- natural ordering을 쓰는 경우에도 `compareTo()`가 보는 필드는 같은 규칙을 따른다
- 값 변경이 필요하면 remove-before-mutate-add 순서를 지킨다
- 이미 바꿔 버려서 조회가 이상하면 새 sorted collection을 만들어 다시 넣는 방식으로 복구한다
- 업데이트가 잦은 객체는 immutable key, stable id map, 정렬 snapshot 같은 구조를 먼저 고려한다

## 어떤 문서를 다음에 읽으면 좋은가

- comparator가 `TreeSet`/`TreeMap`에서 "같은 자리"까지 정한다는 감각이 약하면 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- `Comparator`를 넘기지 않은 natural ordering에서도 같은 문제가 생기는 이유를 보려면 [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- `first`/`floor`/`ceiling`이 comparator order 위의 이웃 찾기라는 점을 더 보려면 [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- hash collection에서 mutable key가 왜 위험한지도 비교하고 싶다면 [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- key/value object를 불변으로 설계하는 감각을 잡고 싶다면 [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

## 한 줄 정리

`TreeSet`/`TreeMap`은 comparator가 보는 값으로 트리 안의 자리를 정하지만 그 값을 나중에 감시해서 다시 배치하지 않으므로, 원소나 key가 컬렉션 안에 있는 동안 비교 기준 필드는 안정적으로 유지해야 한다.
