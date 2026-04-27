# Priority Update Patterns

> 한 줄 요약: `TreeSet`, `TreeMap`, `PriorityQueue` 계열은 "priority 필드를 바꾸면 자동 재정렬된다"라고 기대하면 안 되고, 각 구조에 맞는 안전한 update 패턴을 골라야 한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
> - [`PriorityBlockingQueue` Cancellation/Update Mini Bridge](./priorityblockingqueue-cancellation-stale-entry-mini-bridge.md)
> - [Java PriorityQueue Pitfalls](../data-structure/java-priorityqueue-pitfalls.md)
> - [Heap vs Priority Queue vs Ordered Map Beginner Bridge](../data-structure/heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)

> retrieval-anchor-keywords: language-java-00080, priority update patterns, treeset priority update, treemap key priority update, priorityqueue priority update, priorityblockingqueue priority update, priorityblockingqueue cancellation update, priorityblockingqueue duplicate entries, java reorder after priority change, remove and reinsert treeset, remove and reinsert treemap, stale entry priorityqueue, decrease key java priorityqueue, mutable priority sorted collection, mutable priority queue item beginner, tree set priority mutation safe pattern, tree map priority mutation safe pattern, priority queue lazy deletion pattern, versioned entry priority queue, ordered collection priority change, 자바 우선순위 변경 패턴, TreeSet priority 변경, TreeMap key priority 변경, PriorityQueue 우선순위 변경, PriorityBlockingQueue 취소 패턴, stale entry 패턴

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 비교 표](#한-장-비교-표)
- [`TreeSet`: remove -> change -> add](#treeset-remove---change---add)
- [`TreeMap`: key를 다시 만들거나, priority를 value 쪽으로 보낸다](#treemap-key를-다시-만들거나-priority를-value-쪽으로-보낸다)
- [`PriorityQueue` 계열: in-place update보다 새 entry 추가가 기본](#priorityqueue-계열-in-place-update보다-새-entry-추가가-기본)
- [언제 어떤 구조가 더 맞는가](#언제-어떤-구조가-더-맞는가)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [빠른 체크리스트](#빠른-체크리스트)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

초보자는 보통 이렇게 기대한다.

- `task.priority = 5`로 바꾸면 컬렉션 안에서도 자동으로 자리 이동할 것이다
- `TreeSet`, `TreeMap`, `PriorityQueue`는 다 "정렬"과 관련 있으니 update 방식도 비슷할 것이다

하지만 실제로는 구조마다 안전한 패턴이 다르다.

- `TreeSet`은 원소를 빼고 다시 넣는 쪽이 안전하다
- `TreeMap`은 key를 다시 넣거나, 아예 priority를 value 쪽 상태로 두는 설계가 더 안전할 수 있다
- `PriorityQueue` 계열은 보통 기존 entry를 고치기보다 새 entry를 넣고 오래된 entry를 stale로 버린다

이 문서는 "왜 mutation이 위험한가"를 길게 다시 설명하기보다, 이미 그 함정을 안다고 가정하고 **그래서 실제 update를 어떻게 해야 하는지**에만 집중한다.

## 먼저 잡을 mental model

초보자용 기억법은 이 한 줄이면 충분하다.

> ordered/priority collection은 "현재 객체 필드"가 아니라 "넣을 때 정한 내부 위치"를 먼저 믿는다.

그래서 priority를 바꾸고 싶을 때의 안전한 기본 질문은 이것이다.

1. 이 구조가 priority를 **어디에** 저장하고 있나?
2. priority가 바뀌면 **기존 entry를 다시 배치**해야 하나?
3. 그 재배치를 이 구조가 **자동으로** 해 주나?

이 질문에 대한 초급 답은 거의 항상 같다.

- 자동 재배치는 기대하지 않는다
- 필요하면 remove/reinsert 또는 새 entry 추가 패턴을 직접 쓴다

## 한 장 비교 표

| 구조 | priority가 순서에 참여하나 | 안전한 기본 update | beginner 메모 |
|---|---|---|---|
| `TreeSet<E>` | 예 | `remove(old)` -> change/new object -> `add(new)` | comparator가 보는 필드는 안에서 직접 바꾸지 않는다 |
| `TreeMap<K, V>`, priority가 `key`에 있음 | 예 | old key로 `remove` 후 새 key로 `put` | key priority를 바꾼 뒤 `get/remove`를 기대하면 안 된다 |
| `TreeMap<K, V>`, priority가 `value`에만 있음 | 보통 아니오 | value만 갱신 가능 | 다만 "priority 순 정렬" 용도라면 구조 선택이 다시 필요하다 |
| `PriorityQueue<E>` / `PriorityBlockingQueue<E>` | 예 | 새 entry `offer`, old entry는 stale로 무시 | Java에는 일반적인 `decrease-key`가 없다고 생각하면 편하다 |

## `TreeSet`: remove -> change -> add

`TreeSet`이 priority 순 정렬을 맡고 있다면, 가장 단순한 안전 패턴은 이것이다.

> 원소를 꺼내기 전에 먼저 `remove`, 그다음 priority를 바꾸고 다시 `add`한다.

```java
Comparator<Task> byPriorityThenId =
        Comparator.comparingInt(Task::priority)
                .thenComparingLong(Task::id);

TreeSet<Task> tasks = new TreeSet<>(byPriorityThenId);

Task task = new Task(10L, 3, "review");

tasks.add(task);

tasks.remove(task);      // old priority 기준으로 제거
task.setPriority(1);     // 그 다음 변경
tasks.add(task);         // 새 priority 기준으로 재삽입
```

여기서 순서가 중요하다.

- 먼저 바꾸고 나서 `remove(task)`를 시도하면, comparator 경로가 달라져 제거가 실패할 수 있다
- 그래서 beginner 기본값은 "remove 먼저, change 나중"이다

객체를 mutable로 들고 가기 싫다면 새 객체를 다시 넣는 쪽이 더 명확하다.

```java
tasks.remove(task);
Task updated = new Task(task.id(), 1, task.name());
tasks.add(updated);
```

이 패턴이 특히 잘 맞는 경우:

- entry 수가 아주 크지 않다
- 특정 task reference를 이미 들고 있다
- priority 변경 빈도가 많지 않다

## `TreeMap`: key를 다시 만들거나, priority를 value 쪽으로 보낸다

`TreeMap`은 두 경우를 구분해야 한다.

### 1. priority가 `key`에 들어 있는 경우

예를 들어 `(priority, id)`를 key로 두고 작업을 관리한다면, priority 변경은 사실상 **key 변경**이다.

```java
record TaskKey(int priority, long id) {}

TreeMap<TaskKey, Task> tasksByPriority = new TreeMap<>(
        Comparator.comparingInt(TaskKey::priority)
                .thenComparingLong(TaskKey::id)
);

TaskKey oldKey = new TaskKey(3, 10L);
Task task = tasksByPriority.remove(oldKey);

TaskKey newKey = new TaskKey(1, 10L);
tasksByPriority.put(newKey, task);
```

핵심은 간단하다.

- priority를 바꾸는 순간 old key는 더 이상 old 자리의 정렬 기준과 맞지 않는다
- 그래서 `key`를 제자리 수정하는 생각보다, **old key 삭제 + new key 삽입**으로 보는 편이 안전하다

### 2. priority가 `value` 상태일 뿐, lookup key는 따로 있는 경우

예를 들어 `Map<Long, Task>`에서 `Long`은 task id이고, `Task.priority`는 단지 상태 필드라면 상황이 다르다.

```java
Map<Long, Task> tasksById = new TreeMap<>();

Task task = tasksById.get(10L);
task.setPriority(1);
```

이 update 자체는 lookup key를 깨뜨리지 않는다.
다만 이런 설계는 "id 순 map"일 뿐이지 "priority 순 조회"를 빠르게 해 주는 구조는 아니다.

즉 `TreeMap`에서 초보자 판단은 이렇게 하면 된다.

- 내 `TreeMap`이 id나 name 같은 **stable key 조회**용인가? -> value update는 보통 가능
- 내 `TreeMap`이 priority 순 정렬 자체를 맡고 있나? -> key 재삽입 패턴이 필요

## `PriorityQueue` 계열: in-place update보다 새 entry 추가가 기본

`PriorityQueue`와 `PriorityBlockingQueue`는 beginner가 특히 많이 오해하는 지점이 있다.

> queue 안의 객체 priority를 직접 바꿔도 heap이 자동으로 다시 맞춰지지 않는다.

그래서 Java 쪽 기본 패턴은 대개 이것이다.

- 기존 entry를 찾아 고치려고 하지 않는다
- 새 priority를 가진 entry를 하나 더 `offer`한다
- 나중에 `poll()`할 때 오래된 entry면 stale로 버린다

```java
record QueueEntry(long taskId, int priority, long version) {}

Map<Long, Long> latestVersionByTaskId = new HashMap<>();

PriorityQueue<QueueEntry> pq = new PriorityQueue<>(
        Comparator.comparingInt(QueueEntry::priority)
                .thenComparingLong(QueueEntry::version)
);

void updatePriority(long taskId, int newPriority) {
    long newVersion = latestVersionByTaskId.getOrDefault(taskId, 0L) + 1;
    latestVersionByTaskId.put(taskId, newVersion);
    pq.offer(new QueueEntry(taskId, newPriority, newVersion));
}

QueueEntry pollLive() {
    while (!pq.isEmpty()) {
        QueueEntry entry = pq.poll();
        long latestVersion = latestVersionByTaskId.getOrDefault(entry.taskId(), -1L);
        if (entry.version() == latestVersion) {
            return entry;
        }
    }
    return null;
}
```

왜 이런 패턴을 쓰나?

- Java `PriorityQueue`는 "entry 우선순위 제자리 갱신" API를 기대하기 어렵다
- 임의 원소 제거 후 재삽입은 가능해도, 보통 "찾기" 비용과 코드 복잡도가 커진다
- 알고리즘과 스케줄링에서는 stale entry skip 패턴이 더 흔하고 설명도 쉽다

priority 변경이 드물고 entry reference를 직접 들고 있다면 `remove(entry)` 후 `offer(updated)`도 가능하다.
하지만 beginner 기본값으로는 "새 entry + stale skip"이 더 덜 헷갈린다.

`PriorityBlockingQueue`까지 같이 보는 초보자라면, cancel 때문에 생기는 duplicate entry와 stale skip 감각을 [`PriorityBlockingQueue` Cancellation/Update Mini Bridge](./priorityblockingqueue-cancellation-stale-entry-mini-bridge.md)에서 바로 이어 보면 된다.

## 언제 어떤 구조가 더 맞는가

| 지금 필요한 것 | 더 자연스러운 구조 | update 감각 |
|---|---|---|
| priority 순 전체 질서 + 이웃 탐색 | `TreeSet` / priority key `TreeMap` | remove/reinsert |
| stable key 조회가 본체이고 priority는 부가 상태 | id/name 기준 `Map` | value update 가능, 정렬은 별도 책임 |
| top 1 반복 추출 | `PriorityQueue` 계열 | 새 entry 추가 + stale skip |

초보자용으로는 이렇게 외우면 충분하다.

- "정렬된 자리"를 다시 잡아야 하면 `TreeSet`/priority-key `TreeMap`
- "맨 위 하나"만 계속 중요하면 `PriorityQueue`

## 초보자가 자주 헷갈리는 지점

- `TreeSet`과 `PriorityQueue` 모두 comparator를 써도 update 전략은 같지 않다.
- `TreeMap`에서 value를 바꾸는 것과 key를 바꾸는 것은 전혀 다른 일이다.
- `PriorityBlockingQueue`도 "blocking"만 추가된 것이지, priority update가 자동 안전해지는 것은 아니다.
- `remove`가 실패하는 구조에서는 대개 "이미 먼저 mutate했다"를 의심하면 된다.
- stale entry 패턴은 "중복 데이터 버그"가 아니라 Java heap 구조에서 흔한 의도적 패턴이다.

## 빠른 체크리스트

- priority가 comparator/key/heap order에 참여하는가?
- 참여한다면 in-place mutation 대신 재삽입이 필요한가?
- `TreeSet`/`TreeMap`이면 `remove`를 mutation 전에 하고 있는가?
- `PriorityQueue` 계열이면 stale entry를 구분할 version/sequence/state가 있는가?
- 사실은 priority 정렬보다 stable key lookup이 더 중요한 문제는 아닌가?

## 한 줄 정리

priority 변경에서 초보자용 안전 기본값은 간단하다.
`TreeSet`과 priority-key `TreeMap`은 `remove -> reinsert`, `PriorityQueue` 계열은 `new entry -> stale skip`으로 기억하면 된다.
