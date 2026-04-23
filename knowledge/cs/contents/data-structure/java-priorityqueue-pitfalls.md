# Java PriorityQueue Pitfalls

> 한 줄 요약: Java `PriorityQueue`는 "정렬된 리스트"가 아니라 "루트만 빠른 min-heap"이므로 comparator 방향, tie-breaker, stale entry 처리 방식을 따로 챙겨야 한다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
> - [Heap Variants](./heap-variants.md)
> - [Top-K Heap Direction Patterns](./top-k-heap-direction-patterns.md)
> - [Monotonic Deque vs Heap for Window Extrema](./monotonic-deque-vs-heap-for-window-extrema.md)
> - [희소 그래프 최단 경로](../algorithm/sparse-graph-shortest-paths.md)
> - [Minimum Spanning Tree: Prim vs Kruskal](../algorithm/minimum-spanning-tree-prim-vs-kruskal.md)
> - [Top-k Streaming / Heavy Hitters](../algorithm/top-k-streaming-heavy-hitters.md)
>
> retrieval-anchor-keywords: java priorityqueue pitfalls, java priority queue pitfalls, java priorityqueue, java priority queue, priorityqueue comparator direction, priorityqueue max heap java, priorityqueue min heap default, priorityqueue tie breaker, priorityqueue tiebreaker, priorityqueue stale entry, priorityqueue stale entries, priorityqueue decrease key, priorityqueue mutable key, priorityqueue not sorted, priorityqueue iteration order, priorityqueue iterator order, heap is not sorted list, dijkstra stale entry java, prim stale entry java, java heap comparator overflow, priorityqueue kth largest min heap java, priorityqueue median two heaps java, priorityqueue heap direction java, 우선순위 큐 비교자 방향, 자바 priorityqueue 함정, 자바 우선순위 큐 함정, priorityqueue 동점 처리, stale entry 다익스트라, priorityqueue 정렬 리스트 아님, priorityqueue 순회 순서, priorityqueue decrease-key 없음, 자바 kth largest 힙 방향, 자바 median 두 힙

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

`PriorityQueue`는 "더 우선인 원소를 먼저 꺼낸다"만 보장하지, **같은 priority끼리 삽입 순서를 보존한다**고 약속하지 않는다.

예를 들어 "priority가 높을수록 먼저 처리하되, 같으면 먼저 들어온 작업부터"라는 요구가 있으면 tie-breaker를 직접 넣어야 한다.

```java
Comparator<Job> byPriorityThenSequence =
    Comparator.<Job>comparingInt(job -> job.priority)
        .reversed()
        .thenComparingLong(job -> job.sequence);

PriorityQueue<Job> pq = new PriorityQueue<>(byPriorityThenSequence);
```

핵심은 이렇다.

- priority만 비교하면 같은 priority 내부 순서는 구현 세부에 기대게 된다.
- stable order가 문제 요구면 `timestamp`, `sequence`, `id` 같은 secondary key를 같이 비교해야 한다.
- tie-breaker가 없으면 테스트는 우연히 통과해도, 다른 입력에서 순서가 흔들릴 수 있다.

즉 `PriorityQueue`는 "동점까지 알아서 정리된 정렬 컨테이너"가 아니다.

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
