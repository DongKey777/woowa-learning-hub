---
schema_version: 3
title: Java PriorityQueue Pitfalls
concept_id: data-structure/java-priorityqueue-pitfalls
canonical: true
category: data-structure
difficulty: intermediate
doc_role: playbook
level: intermediate
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- java-priorityqueue-comparator-direction
- priorityqueue-stale-entry
- heap-not-sorted-list
aliases:
- Java PriorityQueue pitfalls
- PriorityQueue not sorted
- PriorityQueue stale entry
- PriorityQueue tie breaker
- Java min heap max heap
- decrease key 없음
- duplicate priority order
- PriorityQueue 삽입 순서 보장
symptoms:
- Java PriorityQueue 기본이 min-heap이라는 점을 놓쳐 comparator 방향을 반대로 잡고 있어
- 같은 priority에서 삽입 순서가 자동 보장된다고 기대하고 있어
- Dijkstra나 Prim에서 decrease-key 대신 stale entry를 버리는 패턴을 이해하지 못하고 있어
intents:
- troubleshooting
- comparison
prerequisites:
- data-structure/heap-vs-priority-queue-vs-ordered-map-beginner-bridge
- data-structure/heap-basics
next_docs:
- data-structure/top-k-heap-direction-patterns
- data-structure/mutable-priority-stale-ticket-pattern
- algorithm/sparse-graph-shortest-paths
- language/treeset-treemap-comparator-tie-breaker-basics
linked_paths:
- contents/data-structure/queue-vs-deque-vs-priority-queue-primer.md
- contents/data-structure/heap-variants.md
- contents/data-structure/top-k-heap-direction-patterns.md
- contents/data-structure/mutable-priority-stale-ticket-pattern.md
- contents/language/java/treeset-treemap-comparator-tie-breaker-basics.md
- contents/algorithm/sparse-graph-shortest-paths.md
confusable_with:
- data-structure/heap-vs-priority-queue-vs-ordered-map-beginner-bridge
- data-structure/top-k-heap-direction-patterns
- data-structure/treemap-vs-hashmap-vs-linkedhashmap
forbidden_neighbors: []
expected_queries:
- Java PriorityQueue에서 min-heap과 max-heap comparator 방향을 어떻게 잡아?
- PriorityQueue는 같은 priority에서 삽입 순서를 보장하지 않는 이유가 뭐야?
- PriorityQueue iterator나 toString 결과가 정렬되어 있지 않은 이유는 뭐야?
- Dijkstra에서 decrease-key가 없을 때 stale entry를 어떻게 버려?
- heap에 넣은 객체의 priority 필드를 바꾸면 왜 자동으로 재정렬되지 않아?
contextual_chunk_prefix: |
  이 문서는 Java PriorityQueue pitfalls playbook으로, min-heap default, comparator direction, tie-breaker sequence, heap is not sorted iteration, no decrease-key, stale entry skip을 다룬다.
  PriorityQueue 동점 처리, 삽입 순서 보장, stale entry, max heap comparator, Dijkstra duplicate push 같은 자연어 질문이 본 문서에 매핑된다.
---
# Java PriorityQueue Pitfalls

> 한 줄 요약: Java `PriorityQueue`는 "정렬된 리스트"가 아니라 "루트만 빠른 min-heap"이므로 comparator 방향, tie-breaker, stale entry 처리 방식을 따로 챙겨야 한다.

**난이도: 🟡 Intermediate**

관련 문서:
- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [Heap Variants](./heap-variants.md)
- [Top-K Heap Direction Patterns](./top-k-heap-direction-patterns.md)
- [Mutable Priority Stale Ticket Pattern](./mutable-priority-stale-ticket-pattern.md)
- [Comparator in TreeSet and TreeMap](../language/java/treeset-treemap-comparator-tie-breaker-basics.md)
- [희소 그래프 최단 경로](../algorithm/sparse-graph-shortest-paths.md)

retrieval-anchor-keywords: java priorityqueue pitfalls, priorityqueue tie breaker, priorityqueue stale entry, priorityqueue not sorted, priorityqueue duplicate priority order, priorityqueue insertion order misconception, priority queue stable order misconception, priority sequence tie breaker java, priorityqueue 동점 처리, priorityqueue 중복 우선순위, priorityqueue 삽입 순서 보장, priorityqueue 정렬 리스트 아님, priorityqueue basics, priorityqueue 뭐예요, java priorityqueue pitfalls basics

## 빠른 진단 표

| 증상 | 실제 원인 | 바로 잡는 기준 |
|---|---|---|
| max heap을 만들었다고 생각했는데 작은 값이 먼저 나온다 | Java `PriorityQueue` 기본은 min-heap이다 | comparator 방향을 먼저 확인한다 |
| 같은 priority끼리 순서가 들쭉날쭉하다 | stable order를 자동 보장하지 않는다 | secondary key나 sequence를 넣는다 |
| `for-each`, `iterator()`, `toString()` 결과가 정렬돼 있지 않다 | heap은 루트만 보장한다 | 전체 정렬이 필요하면 `poll()` 반복이나 별도 sort가 필요하다 |
| Dijkstra / Prim에서 같은 정점이 여러 번 들어간다 | `decrease-key`가 없다 | duplicate push 후 `poll()` 시 stale entry를 버린다 |
| heap에 넣은 객체의 priority 필드를 바꿨는데 순서가 안 바뀐다 | 삽입 후 내부 재정렬이 자동으로 일어나지 않는다 | key를 바꿔치기하지 말고 새 항목을 넣고 이전 항목은 stale로 처리한다 |

## 1. 기본값은 min-heap이다

Java `PriorityQueue`의 기본 정렬 방향은 natural order다.
즉 숫자는 **작은 값이 먼저**, 문자열은 **사전순으로 앞선 값이 먼저** 나온다.

```java
PriorityQueue<Integer> minHeap = new PriorityQueue<>();
PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Comparator.reverseOrder());
```

custom object일 때도 comparator 방향을 먼저 확인해야 한다.

```java
PriorityQueue<Task> bySmallestDeadline =
    new PriorityQueue<>(Comparator.comparingInt(task -> task.deadline));

PriorityQueue<Task> byLargestScore =
    new PriorityQueue<>((a, b) -> Integer.compare(b.score, a.score));
```

여기서 초보자가 자주 하는 실수는 두 가지다.

- `max heap` 문제인데 min-heap comparator를 그대로 둔다.
- `(a, b) -> a.score - b.score`처럼 뺄셈으로 comparator를 써서 overflow 위험을 만든다.

그래서 Java에서는 `Integer.compare`, `Long.compare`, `Comparator.comparingInt`처럼 방향이 드러나는 비교식을 쓰는 편이 안전하다.

추가로 `top k largest` 류 문제는 이름만 보고 max-heap을 고르기 쉽지만, 실제로는 **크기 `k`짜리 min-heap**을 유지하는 쪽이 더 흔하다.
루트에 "`현재 top-k 중 가장 약한 후보`"를 두어 새 값과 빠르게 비교하기 위해서다.
`kth-largest`, `streaming top-k`, `median`에서 이 방향 감각이 자꾸 헷갈리면 [Top-K Heap Direction Patterns](./top-k-heap-direction-patterns.md)로 바로 이어 보면 흐름이 정리된다.

## 2. 동점은 stable하지 않다

`PriorityQueue`는 "줄 전체를 정렬해 두는 구조"가 아니라 "**머리 1개만 가장 우선**"인 구조다.
그래서 **중복 priority**가 있으면, 같은 priority 안쪽 순서는 자동으로 stable하지 않다.

짧게 손으로 따라가 보면 오해가 빨리 풀린다.

여기서는 **숫자가 작을수록 더 높은 우선순위**라고 가정하자.
즉 `3`이 `5`보다 먼저 나오는 min-heap 예시다.

| 넣은 순서 | 작업 | priority |
|---|---|---|
| 1 | A | 5 |
| 2 | B | 5 |
| 3 | C | 3 |

`priority`만 비교하면 `poll()` 첫 번째는 C로 고정이지만, 그다음 A/B 순서는 보장되지 않는다.

| comparator | 가능한 `poll()` 결과 예시 |
|---|---|
| `priority` only | `C -> A -> B` 또는 `C -> B -> A` |
| `(priority ASC, sequence ASC)` | `C -> A -> B` (동점이면 먼저 들어온 순서 고정) |

즉 요구사항이 "priority가 같으면 먼저 들어온 작업부터"라면 `(priority, sequence)`를 **한 쌍의 정렬 키**로 만들어야 한다.

> 바로 붙여 넣는 시작 스니펫:
> ```java
> record Job(int priority, long sequence) {}
> PriorityQueue<Job> pq = new PriorityQueue<>(
>     Comparator.<Job>comparingInt(Job::priority)
>         .thenComparingLong(Job::sequence)
> );
> ```
> `priority`가 작으면 먼저 나오고, 같으면 `sequence`가 작은 작업이 먼저 나온다.

```java
record Job(int priority, long sequence, String name) {}

Comparator<Job> byPriorityThenSequence =
    Comparator.<Job>comparingInt(Job::priority)
        .thenComparingLong(Job::sequence);

PriorityQueue<Job> pq = new PriorityQueue<>(byPriorityThenSequence);
```

초급자 common confusion:

- "같은 priority면 삽입 순서가 자동 유지된다" -> 보장되지 않는다.
- "내 로컬 JDK에서 우연히 그렇게 나왔으니 항상 맞다" -> 입력/heap shape가 바뀌면 깨질 수 있다.
- "stable order가 필요하면 queue 종류를 바꿔야 한다" -> 대개는 comparator에 `sequence` tie-breaker를 추가하면 충분하다.

## 3. `PriorityQueue`는 sorted list가 아니다

heap이 보장하는 것은 **루트가 최우선 원소**라는 사실뿐이다.
나머지 원소는 부분 순서만 맞고, 전체가 정렬된 배열처럼 나열되지는 않는다.

그래서 아래 기대는 틀리다.

- `for (int x : pq)`를 돌리면 오름차순으로 나올 것이다
- `System.out.println(pq)` 결과가 항상 정렬돼 있을 것이다
- `toArray()`만 하면 정렬 결과를 얻을 수 있다

정렬된 순서가 정말 필요하면 `poll()`을 반복해야 한다.

```java
PriorityQueue<Integer> copy = new PriorityQueue<>(pq);
while (!copy.isEmpty()) {
    System.out.println(copy.poll());
}
```

원본을 보존하면서 순서만 보고 싶으면 **복사본에서 `poll()`** 하는 쪽이 안전하다.

이 차이를 이해하면 "heap은 왜 정렬 배열보다 빠를 수 있는가"도 같이 보인다.

- `peek()`는 루트만 보면 되니 빠르다
- 대신 전체 순서를 항상 맞춰 두지는 않는다

즉 질문이 "`가장 작은 것 하나를 반복적으로 꺼내기`"인지, "`전체를 정렬된 상태로 순회하기`"인지 먼저 구분해야 한다.

## 4. `decrease-key`가 없어서 stale entry 패턴이 흔하다

Java `PriorityQueue`는 이미 들어간 항목의 우선순위를 **제자리에서 낮추거나 높이는 연산**을 직접 지원하지 않는다.

이 때문에 Dijkstra, Prim, A* 같은 알고리즘에서는 같은 정점이나 상태가 queue에 여러 번 들어가는 것이 자연스럽다.

```java
record State(int vertex, int dist) {}

PriorityQueue<State> pq =
    new PriorityQueue<>(Comparator.comparingInt(State::dist));

int[] dist = new int[n];
Arrays.fill(dist, Integer.MAX_VALUE);
dist[start] = 0;
pq.offer(new State(start, 0));

while (!pq.isEmpty()) {
    State cur = pq.poll();
    if (cur.dist() != dist[cur.vertex()]) {
        continue; // stale entry
    }

    for (Edge edge : graph.get(cur.vertex())) {
        int nextDist = cur.dist() + edge.weight;
        if (nextDist < dist[edge.to]) {
            dist[edge.to] = nextDist;
            pq.offer(new State(edge.to, nextDist));
        }
    }
}
```

이 패턴의 핵심은 두 가지다.

- 더 좋은 값이 나오면 기존 항목을 직접 수정하지 않고 **새 항목을 다시 넣는다**
- 나중에 `poll()`했을 때 최신 정답과 다르면 **stale entry로 버린다**

이 방식이 흔한 이유도 분명하다.

- `remove(Object)`는 힙 루트 제거처럼 `O(log n)`이 아니라, 보통 대상 탐색 때문에 `O(n)`이 든다
- heap 안에 들어간 객체의 priority 필드를 바꿔도 자동으로 reheapify되지 않는다

즉 "기존 항목을 찾아서 고쳐 쓰기"보다 "새 항목을 넣고 오래된 항목은 나중에 버리기"가 Java `PriorityQueue`에서는 더 자연스럽다.

알고리즘별 stale check도 보통 다르다.

- Dijkstra: `if (cur.dist() != dist[cur.vertex()]) continue;`
- lazy Prim: `if (visited[cur.vertex()]) continue;`

같은 "stale skip" 패턴이지만, 최신성 기준이 무엇인지가 문제마다 달라진다.

## 5. 면접에서 바로 확인할 체크리스트

1. 이 문제가 min-heap인지 max-heap인지 comparator 방향부터 확정했는가?
2. 같은 priority에서 순서 요구가 있으면 tie-breaker를 넣었는가?
3. `PriorityQueue`를 정렬 배열처럼 순회하려고 하지는 않는가?
4. heap에 넣은 뒤 priority 필드를 직접 수정하지 않는가?
5. Dijkstra / Prim / A*라면 stale entry skip 조건을 명시했는가?

## 한 줄 정리

Java `PriorityQueue`에서 가장 자주 틀리는 지점은 "기본은 min-heap", "동점은 stable하지 않음", "전체 정렬 구조가 아님", "`decrease-key` 대신 stale entry를 버려야 함" 이 네 가지다.
