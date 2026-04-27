# Dijkstra, Bellman-Ford, Floyd-Warshall

> 한 줄 요약: 최단 경로 문제는 먼저 **unweighted shortest path vs DAG shortest path vs weighted shortest path**로 갈라야 선택이 빨라진다.
>
> 문서 역할: 이 문서는 algorithm 카테고리 안에서 **최단 경로 알고리즘 선택 기준**을 정리하는 comparison deep dive다.
>
> retrieval-anchor-keywords: shortest path algorithms comparison, shortest path decision tree, shortest path router, which shortest path algorithm, bfs shortest path, unweighted shortest path, unit weight shortest path, dag shortest path, shortest path on dag, topological shortest path, weighted shortest path, positive weighted shortest path, weighted shortest path router, 0-1 bfs, zero one bfs, zero-one bfs, dial, dial algorithm, dial's algorithm, bucket shortest path, bucket-shortest-path, bucket dijkstra, binary weight shortest path, small integer shortest path, when to use dijkstra, when to use bellman ford, when to use floyd warshall, graph algorithm choice, single-source shortest path, single source shortest path, start-to-all shortest path, single-source routing, one source to all nodes shortest path, source to every vertex shortest path, all-pairs shortest path, all pairs shortest path, pairwise shortest path, every pair shortest path, distance matrix shortest path, shortest path for every pair of nodes, negative-edge shortest path, negative edge, negative weight shortest path, shortest path with negative edges, which algorithm for negative edges, negative cycle detection, route planning shortest path, route-planning shortest path, navigation route planning, routing table shortest path, path vs order vs capacity, 무가중치 최단 경로, DAG 최단 경로, 가중치 최단 경로, 양수 가중치 최단 경로, 단일 시작점 최단 경로, 한 시작점에서 모든 정점까지 최단 거리, 시작점 하나 전체 최단거리, 출발점 하나 전체 거리표, 모든 쌍 최단 경로, 모든 정점 쌍 최단 거리, 모든 노드 쌍 거리표, 음수 간선 최단 경로, 음수 가중치 그래프 최단 경로, 음수 간선 있는데 뭐 써야 하나, 음수 간선에서 다익스트라 되나, 벨만포드 언제 써야 하나, 다익스트라 언제 써야 하나, 플로이드 워셜 언제 써야 하나, 경로 계획 알고리즘, 다익스트라 벨만포드 플로이드워셜 차이

**난이도: 🔴 Advanced**

> 관련 문서:
> - [그래프](./graph.md)
> - [알고리즘 기본](./basic.md#dfs와-bfs)
> - [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
> - [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)
> - [A* vs Dijkstra](./a-star-vs-dijkstra.md)
> - [Topological DP](./topological-dp.md)
> - [Topological Sort Patterns](./topological-sort-patterns.md)
> - [Network Flow Intuition](./network-flow-intuition.md)

## 이 문서 다음에 보면 좋은 문서

- 가중치가 없거나 모두 같아서 BFS shortest path가 먼저라면 [알고리즘 기본](./basic.md#dfs와-bfs)에서 BFS 레벨 탐색을 먼저 확인하면 좋다.
- 실제 경로를 `parent` / `predecessor` 배열로 복원하는 감각을 짧게 잡으려면 [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)를 먼저 보면 좋다.
- 그래프 기본기와 표현은 [그래프](./graph.md)에서 먼저 확인하면 좋다.
- DAG shortest path나 위상 정렬 기반 완화가 핵심이면 [Topological DP](./topological-dp.md)를 먼저 보고, "순서 문제"와의 경계는 [Topological Sort Patterns](./topological-sort-patterns.md)로 같이 확인하면 좋다.
- 희소 그래프에서 `0-1 BFS`, `zero-one BFS`, `Dial`, `bucket-shortest-path`, `PQ Dijkstra`까지 같이 보고 싶다면 [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)로 이어지면 좋다.
- 목표 정점이 분명하고 heuristic이 있으면 [A* vs Dijkstra](./a-star-vs-dijkstra.md)까지 같이 보면 선택 기준이 더 선명해진다.
- 병목 용량, 매칭, 처리량 문제가 섞이면 [Network Flow Intuition](./network-flow-intuition.md)로 넘어가서 "경로"와 "용량"을 구분하면 된다.

---

## Shortest Path Entry Router

| 질문 phrasing | 먼저 의심할 선택 | 왜 그렇게 가는가 |
|---|---|---|
| `가중치 없음`, `unweighted shortest path`, `최소 칸 수`, `edge count minimum` | [BFS](./basic.md#dfs와-bfs) | 레벨 순서가 곧 최단 거리다 |
| `DAG shortest path`, `acyclic shortest path`, `위상 정렬로 최단 경로`, `의존성 그래프 최소 비용` | [Topological DP](./topological-dp.md) + [Topological Sort Patterns](./topological-sort-patterns.md) | 위상 정렬은 계산 순서이고, 문제 자체는 shortest path다 |
| `weighted shortest path`, `positive weighted shortest path`, `양수 가중치`, `single-source shortest path`, `single-source routing`, `start-to-all routing`, `routing cost`, `한 시작점에서 모든 정점`, `출발점 하나 전체 거리표` | Dijkstra | weighted shortest path cluster에서 음수 간선이 없으면 greedy 확정 조건이 유지된다 |
| `0-1 BFS`, `zero-one BFS`, `Dial`, `bucket-shortest-path`, `bucket shortest path`, `small integer shortest path` | [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md) | 희소 그래프의 양수 가중치 shortest path라도 가중치 분포가 특수하면 PQ Dijkstra보다 전용 변형이 더 직접적이다 |
| `negative-edge shortest path`, `negative edge`, `negative weight`, `음수 간선`, `음수 간선 있는데 뭐 써`, `negative weights but single source`, `negative cycle`, `arbitrage` | Bellman-Ford | 음수 간선 처리와 음수 사이클 검출이 필요하다 |
| `all-pairs shortest path`, `all pairs shortest path`, `pairwise shortest path`, `모든 정점 쌍`, `모든 노드 쌍 거리표`, `every pair shortest path`, `distance matrix` | Floyd-Warshall | 모든 쌍을 한 번에 갱신하는 DP가 자연스럽다 |

- `route planning`, `navigation routing`, `road network shortest path` 같은 표현은 범위가 넓다.
  목표 정점이 고정된 `point-to-point shortest path` / `single-pair shortest path` / `source-to-target routing`이면 [A* vs Dijkstra](./a-star-vs-dijkstra.md)로 넘기고, 시작점 하나에서 전체 거리표를 만드는 `single-source routing`이면 이 문서의 Dijkstra/Bellman-Ford 축으로 본다.

---

## 핵심 개념

최단 경로 문제에서 먼저 확인할 것은 네 가지다.

1. 가중치가 없거나 모두 같은가
2. 그래프가 DAG인가
3. 음수 가중치가 있는가
4. `single-source`로 구하는가, `all-pairs`로 구하는가

이 네 질문으로 대부분의 선택이 결정된다.

| 접근 | 전제 | 대상 | 핵심 감각 |
|---|---|---|---|
| BFS | 무가중치 또는 동일 가중치 | 단일 시작점 / 단일 쌍 | 레벨 순서가 곧 최단 거리 |
| DAG shortest path | DAG, 사이클이 없으면 음수 간선도 가능 | 단일 시작점 | 위상 정렬 순서로 한 번씩 relax |
| Dijkstra | 음수 간선 불가 | 단일 시작점 | 가장 짧아 보이는 정점을 확정 |
| Bellman-Ford | 음수 간선 가능 | 단일 시작점 | 모든 간선을 여러 번 완화 |
| Floyd-Warshall | 음수 간선 가능, 정점 수가 작을 때 유리 | 모든 쌍 | 경유지를 하나씩 늘리며 갱신 |

DAG shortest path는 위상 정렬이 계산 도구인 특수 케이스다.
즉 "DAG라서 위상 정렬"이 아니라, "DAG인데 path optimization인가"를 같이 봐야 한다.

## Alias Normalization

이 shortest-path cluster에서는 아래 네 축으로 vocabulary를 맞춘다.

| canonical phrase | 같이 걸리기 쉬운 alias | 우선 연결되는 선택 |
|---|---|---|
| `single-source shortest path` | `single source shortest path`, `start-to-all routing`, `routing table`, `한 시작점에서 전체 거리`, `한 시작점에서 모든 정점까지`, `출발점 하나 전체 거리표` | Dijkstra / Bellman-Ford / DAG shortest path |
| `all-pairs shortest path` | `all pairs shortest path`, `pairwise shortest path`, `distance matrix`, `모든 정점 쌍 거리`, `모든 노드 쌍 거리표`, `every pair shortest path` | Floyd-Warshall |
| `0-1 BFS` | `zero one bfs`, `zero-one bfs`, `binary weight shortest path`, `deque shortest path` | [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)를 먼저 보고, 큰 축에서는 양수 가중치 shortest path의 sparse 특수 케이스로 본다 |
| `Dial` | `dial algorithm`, `dial's algorithm`, `bucket shortest path`, `bucket-shortest-path`, `bucket dijkstra` | [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)를 먼저 보고, 큰 축에서는 bounded positive weight shortest path 변형으로 본다 |
| `negative-edge shortest path` | `negative edge`, `negative weight`, `discount edge`, `rebate edge`, `arbitrage`, `음수 간선 있는데 뭐 써`, `음수 간선 그래프 최단 경로` | Bellman-Ford 또는 DAG shortest path |
| `route planning` | `navigation routing`, `road network shortest path`, `pathfinding`, `route optimization` | `point-to-point` / `single-pair` / `goal-directed`면 [A* vs Dijkstra](./a-star-vs-dijkstra.md), 아니면 `single-source`/`all-pairs`를 다시 본다 |

## Query-Shaped Retrieval Anchors

| query-shaped phrasing | normalize to | 먼저 읽을 축 |
|---|---|---|
| `음수 간선이 있으면 뭐 써야 하나?`, `negative edges shortest path which algorithm`, `음수 가중치 그래프 최단 경로` | `negative-edge shortest path` | Bellman-Ford, 단 DAG면 위상 정렬 기반 shortest path도 다시 확인 |
| `한 시작점에서 모든 정점까지 최단 거리`, `source one to every node shortest path`, `출발점 하나 전체 거리표` | `single-source shortest path` | Dijkstra, 단 음수 간선이면 Bellman-Ford / DAG shortest path로 분기 |
| `모든 정점 쌍 최단 거리`, `every pair shortest path`, `모든 노드 쌍 거리표`, `distance matrix shortest path` | `all-pairs shortest path` | Floyd-Warshall |
| `0-1 BFS가 뭐지`, `zero-one bfs`, `Dial algorithm`, `bucket-shortest-path`, `bucket shortest path` | `0-1 BFS` 또는 `Dial` | [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)에서 가중치 분포별 특수 케이스를 먼저 보고, 큰 선택표는 이 문서에서 다시 맞춘다 |

- `한 점에서 한 점까지`를 묻는 `point-to-point shortest path` / `single-pair shortest path` / `source-to-target routing`은 이 문서의 `single-source` 축과 비슷해 보여도 우선 [A* vs Dijkstra](./a-star-vs-dijkstra.md)와 함께 본다.

## 헷갈리기 쉬운 그래프 선택 경계

| 질문 | 실제로 먼저 볼 문서 | 구분 포인트 |
|---|---|---|
| 가중치가 없거나 모두 같은 그래프에서 **최소 이동 횟수 / 최소 칸 수**를 묻나 | [알고리즘 기본](./basic.md#dfs와-bfs) | shortest path는 BFS부터 본다 |
| 한 점에서 다른 점까지 **최소 비용 경로**가 필요한가 | 이 문서 | path cost를 최소화하는 문제다 |
| DAG에서 **선후 관계를 만족하는 순서**만 필요할 뿐인가 | [Topological Sort Patterns](./topological-sort-patterns.md) | 비용 최소화보다 dependency ordering이 본질이다 |
| DAG인데 비용 합 최소/최대 경로를 구하나 | 이 문서 + [Topological Sort Patterns](./topological-sort-patterns.md) | 위상 정렬은 계산 순서일 뿐, 문제 자체는 shortest/longest path다 |
| 간선별 **용량(capacity)**, 매칭, 병목 처리량을 다루나 | [Network Flow Intuition](./network-flow-intuition.md) | 한 경로가 아니라 총 흘려보낼 양과 cut이 핵심이다 |

---

## 깊이 들어가기

### 0. 먼저 빠지는 두 갈래: BFS와 DAG shortest path

가중치가 없거나 모두 같으면 BFS가 가장 먼저 빠지는 정답이다.
레벨 단위 탐색이 곧 간선 수 기준 최단 거리이기 때문이다.

DAG에서 비용 최소화를 묻는다면 위상 정렬 순서로 relax하는 shortest path가 자연스럽다.
사이클만 없으면 음수 간선이 있어도 처리할 수 있다는 점이 Dijkstra와 다르다.

이 두 경우가 아니면 그다음부터 Dijkstra / Bellman-Ford / Floyd-Warshall를 비교하면 된다.

### 1. Dijkstra

다익스트라는 현재까지 가장 짧은 정점을 하나씩 확정한다.
음수 간선이 있으면 "이미 확정한 정점이 나중에 더 짧아질 수 있다"는 전제가 깨지므로 사용하면 안 된다.

```java
// 개념용 의사 코드
dist[start] = 0
pq.add(start)

while (!pq.isEmpty()) {
    cur = pq.poll()
    if (visited[cur]) continue
    visited[cur] = true

    for (next : adj[cur]) {
        if (dist[next] > dist[cur] + w) {
            dist[next] = dist[cur] + w
            pq.add(next)
        }
    }
}
```

### 2. Bellman-Ford

벨만-포드는 모든 간선을 `V-1`번 완화한다.
그래서 느리지만 음수 간선을 처리할 수 있다.

음의 사이클 검출도 가능하다.
한 번 더 완화했을 때 거리가 줄어들면, 그 그래프는 더 이상 정상적인 최단 경로 문제가 아니다.

### 3. Floyd-Warshall

플로이드-워셜은 `K`라는 경유지를 하나씩 허용해 가며 `i -> j` 최단 거리를 갱신한다.
모든 쌍을 한 번에 구할 때 가장 이해하기 쉽다.

```text
dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
```

이 점화식만 정확히 이해하면 된다.

---

## 실전 시나리오

### 시나리오 1: 지도/라우팅

도로 비용이 항상 양수면 다익스트라가 적합하다.
가중치가 할인/보조금처럼 음수 효과를 가질 수 있으면 벨만-포드를 의심해야 한다.

### 시나리오 2: 환율/거래 차익

음의 사이클이 존재하는지 확인해야 하는 문제는 벨만-포드가 자연스럽다.

### 시나리오 3: 작은 정점 수, 자주 조회

정점 수가 적고 모든 쌍 최단 경로가 필요하면 플로이드-워셜이 단순하고 실수도 적다.

### 시나리오 4: 실무에서의 오판

정점 수가 큰데 "모든 쌍이 필요할 것 같아"라는 이유로 플로이드-워셜을 쓰면 바로 터진다.
반대로 음수 간선이 있는데 다익스트라를 쓰면 결과가 틀리지만 그게 바로 드러나지 않을 수 있다.

---

## 코드로 보기

```java
// Bellman-Ford 개념 코드
for (int i = 1; i <= V - 1; i++) {
    for (Edge e : edges) {
        if (dist[e.from] != INF && dist[e.to] > dist[e.from] + e.weight) {
            dist[e.to] = dist[e.from] + e.weight;
        }
    }
}

boolean hasNegativeCycle = false;
for (Edge e : edges) {
    if (dist[e.from] != INF && dist[e.to] > dist[e.from] + e.weight) {
        hasNegativeCycle = true;
        break;
    }
}
```

다익스트라와 벨만-포드는 "더 빠른가"보다 "조건이 맞는가"가 먼저다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| BFS | 구현이 단순하고 무가중치 shortest path에 강하다 | 가중치가 있으면 부적합하다 | 가중치가 없거나 모두 같을 때 |
| DAG shortest path | DAG에서 선형적으로 relax 가능하고 음수 간선도 처리 가능하다 | DAG가 아니면 못 쓴다 | DAG path optimization |
| Dijkstra | 빠르다 | 음수 간선 불가 | 일반적인 양수 가중치 |
| Bellman-Ford | 음수 간선 가능 | 느리다 | 음수/음수 사이클 검출 |
| Floyd-Warshall | 모든 쌍에 단순 | `O(V^3)` | 정점 수가 작을 때 |

핵심은 "최단 경로"라는 이름이 같아도,
입력 조건이 다르면 전혀 다른 문제라는 점이다.

---

## 꼬리질문

> Q: 다익스트라가 왜 음수 간선에 취약한가요?
> 의도: greedy 확정 조건 이해 확인
> 핵심: 한 번 확정한 정점의 값이 더 줄어들 수 있기 때문이다

> Q: 벨만-포드는 왜 느린가요?
> 의도: 완화 횟수와 간선 순회 비용 이해 확인
> 핵심: 모든 간선을 V-1번 본다

> Q: 플로이드-워셜은 언제 쓰면 안 되나요?
> 의도: 복잡도 감각 확인
> 핵심: 정점 수가 큰 문제에서는 `O(V^3)`가 너무 크다

---

## 한 줄 정리

최단 경로는 먼저 무가중치면 BFS, DAG면 위상 정렬 기반 shortest path로 빼고, 그다음 가중치 조건과 범위로 Dijkstra / Bellman-Ford / Floyd-Warshall를 고르면 된다.
