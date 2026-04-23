# 그래프 관련 알고리즘

> 작성자 : [서그림](https://github.com/Seogeurim), [정희재](https://github.com/Hee-Jae)

<details>
<summary>Table of Contents</summary>

- [그래프 문제 Decision Router](#그래프-문제-decision-router)
- [Shortest Path Router: Unweighted vs DAG vs Weighted](#shortest-path-router-unweighted-vs-dag-vs-weighted)
- [Weighted Shortest Path Density Router: Sparse vs Dense](#weighted-shortest-path-density-router-sparse-vs-dense)
- [다익스트라 알고리즘 (Dijkstra Algorithm)](#다익스트라-알고리즘-dijkstra-algorithm)
- [벨만-포드 알고리즘 (Bellman-Ford-Moore Algorithm)](#벨만-포드-알고리즘-bellman-ford-moore-algorithm)
- [플로이드-워셜 알고리즘 (Floyd-Warshall Algorithm)](#플로이드-워셜-알고리즘-floyd-warshall-algorithm)
- [분리 집합(Union Find)과 크루스칼(Kruskal) 알고리즘](#분리-집합Union-Find과-크루스칼Kruskal-알고리즘)
- [위상 정렬 패턴](#위상-정렬-패턴)

</details>

> 한 줄 요약: 이 문서는 legacy graph primer에서 들어오는 질문을 shortest path / MST / topological sort / flow로 먼저 분기시키는 entrypoint다.

**난이도: 🟡 Intermediate**
>
> 문서 역할: 이 문서는 algorithm 카테고리 안에서 **graph basics primer + routing entrypoint** 역할을 한다.
>
> retrieval-anchor-keywords: graph basics, graph primer, legacy graph primer, graph algorithm primer, graph algorithm guide, graph algorithm choice, graph problem router, graph decision tree, which graph algorithm to use, shortest path, shortest path primer, shortest path cluster, shortest path decision tree, unweighted vs dag vs weighted shortest path, shortest path router, weighted shortest path, positive weighted shortest path, sparse graph shortest path, dense graph shortest path, sparse vs dense shortest path, graph density shortest path, edge density shortest path, adjacency list shortest path, adjacency matrix shortest path, sparse weighted shortest path, dense weighted shortest path, sparse graph routing, dense graph routing, matrix dijkstra, O(V^2) dijkstra, priority queue dijkstra, 0-1 bfs, zero one bfs, 0/1 cost shortest path, binary edge weight shortest path, deque shortest path, shortest path with deque, teleport shortest path, portal shortest path, warp shortest path, teleport cost 0 walk cost 1, dag shortest path, shortest path on dag, topological shortest path, pathfinding router, graph pathfinding, route finding, point-to-point shortest path, point to point shortest path, source-to-target routing, goal-directed pathfinding, heuristic pathfinding, A*, A star, astar, single-source shortest path, single source shortest path, single-source routing, start-to-all routing, routing table shortest path, single pair shortest path, all-pairs shortest path, all pairs shortest path, pairwise shortest path, distance matrix shortest path, bfs shortest path, unweighted shortest path, unit weight shortest path, maze shortest path, dijkstra, bellman ford, floyd warshall, negative-edge shortest path, negative edge, negative weight shortest path, negative cycle, shortest path vs MST, minimum spanning tree, MST, minimum spanning forest, connect all nodes minimum cost, kruskal, prim, prim vs kruskal, union find, disjoint set, dense graph mst, sparse graph mst, topological sort, topological ordering, DAG ordering, dependency graph, build order, course schedule, prerequisite graph, path vs tree vs order vs flow, network flow, max flow, maximum throughput, throughput maximization, throughput optimization, bottleneck, bottleneck edge, bottleneck link, bottleneck capacity, capacity bottleneck, bandwidth bottleneck, min cut, minimum cut, cut capacity, flow cut theorem, flow vs shortest path, bipartite matching, job assignment, matching reduction, 그래프 기본, 그래프 프라이머, 그래프 알고리즘 선택, 최단 경로, 경로 탐색, 길찾기, 점대점 최단 경로, 목표 지향 탐색, 가중치 최단 경로, 양수 가중치 최단 경로, 그래프 밀도 최단 경로, 희소 그래프 최단 경로, 밀집 그래프 최단 경로, 인접 리스트 최단 경로, 인접 행렬 최단 경로, 순간이동 최단 경로, 텔레포트 최단 경로, 포털 최단 경로, 워프 최단 경로, DAG 최단 경로, 무가중치 최단 경로, 단일 시작점 최단 경로, 모든 쌍 최단 경로, 음수 간선 최단 경로, 최소 신장 트리, 프림 알고리즘, 크루스칼 알고리즘, 위상 정렬, 선후 관계, 의존성 그래프, 빌드 순서, 선수 과목, 최대 처리량, 병목, 병목 간선, 병목 링크, 네트워크 병목, 최소 컷, 최소 절단, 절단 용량
>
> 관련 문서:
> - [알고리즘 기본](./basic.md#dfs와-bfs)
> - [Connectivity Question Router](../data-structure/connectivity-question-router.md)
> - [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)
> - [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md)
> - [A* vs Dijkstra](./a-star-vs-dijkstra.md)
> - [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)
> - [Topological DP](./topological-dp.md)
> - [위상 정렬 패턴](./topological-sort-patterns.md)
> - [Union-Find Amortized Proof Intuition](./union-find-amortized-proof-intuition.md)
> - [Network Flow Intuition](./network-flow-intuition.md)
> - [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md)

---

## 이 문서 다음에 보면 좋은 문서

- `same-component`, `connected yes/no`, `경로 하나 복원`, `최단 경로` phrasing가 한데 섞이면 [Connectivity Question Router](../data-structure/connectivity-question-router.md)에서 먼저 답의 모양을 `yes/no vs actual path vs minimum`으로 가르는 편이 빠르다.
- `unweighted shortest path`, `bfs shortest path`, `최소 칸 수`, `미로 최단 경로`처럼 무가중치 shortest path가 먼저면 [알고리즘 기본](./basic.md#dfs와-bfs)에서 BFS 레벨 탐색을 먼저 보는 편이 빠르다.
- `dag shortest path`, `topological shortest path`, `의존성 그래프 최소 비용`처럼 DAG 위 path optimization이 핵심이면 [Topological DP](./topological-dp.md)와 [위상 정렬 패턴](./topological-sort-patterns.md)을 같이 보면 좋다.
- `weighted shortest path`, `single-source shortest path`, `single-source routing`, `all-pairs shortest path`, `negative-edge shortest path`처럼 가중치 shortest path 선택 기준이 핵심이면 [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)로 이어지면 좋다.
- `sparse graph shortest path`, `dense graph shortest path`, `adjacency list shortest path`, `adjacency matrix shortest path`, `graph density shortest path`처럼 그래프 밀도/표현이 먼저 보이면 아래의 [Weighted Shortest Path Density Router: Sparse vs Dense](#weighted-shortest-path-density-router-sparse-vs-dense)를 한 번 거친 뒤, 희소 그래프 쪽은 [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md), 밀집 그래프 쪽은 [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)로 가면 된다.
- `0-1 BFS`, `0/1 cost shortest path`, `deque shortest path`, `teleport shortest path`, `portal shortest path`, `warp shortest path`, `순간이동 최단 경로`처럼 특수 weighted shortest-path phrasing이면 [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)로 바로 보내는 편이 빠르다. 대개 `0 edge + 1 edge` 모델인지 먼저 확인하면 된다.
- `pathfinding`, `point-to-point shortest path`, `goal-directed routing`, `A*`처럼 목표 정점이 또렷한 질문이면 [A* vs Dijkstra](./a-star-vs-dijkstra.md)로 이어지면 좋다.
- `build order`, `course schedule`, `dependency ordering`처럼 DAG 순서 문제를 따로 분리해서 보고 싶다면 [위상 정렬 패턴](./topological-sort-patterns.md)이 가장 직접적이다.
- `MST`, `minimum spanning tree`, `Prim vs Kruskal`, `모든 정점을 최소 비용으로 연결` 같은 질문이면 [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md)로 먼저 가는 편이 더 직접적이다.
- `optimal assignment`, `linear assignment`, `1:1 weighted matching`, `cost matrix assignment`처럼 exact 배정이 핵심이면 [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md)부터 확인하는 편이 정확하다.
- `bottleneck`, `min cut`, `minimum cut`, `cut capacity`, `maximum throughput`, `네트워크 병목`, `최소 절단`처럼 전체 처리량을 막는 절단/병목을 묻는 phrasing이면 [Network Flow Intuition](./network-flow-intuition.md)으로 바로 넘어가야 한다. 한 경로의 최단 거리보다 cut과 capacity가 핵심이다.
- 경로 하나가 아니라 여러 경로를 통한 총 처리량, 배정, 매칭 문제라면 [Network Flow Intuition](./network-flow-intuition.md)으로 넘어가는 편이 정확하다.

## 그래프 문제 Decision Router

그래프 문제는 먼저 답의 모양을 구분하면 길을 잃지 않는다.
`path 하나`, `tree 하나`, `order 하나`, `flow 양` 중 무엇을 묻는지 먼저 보면 된다.

| 문제에서 먼저 확인할 질문 | 먼저 갈 문서 | 왜 그 문서가 맞는가 |
|---|---|---|
| 한 정점에서 다른 정점까지 **최소 비용 / 최단 거리**를 구하나 | [Shortest Path Router: Unweighted vs DAG vs Weighted](#shortest-path-router-unweighted-vs-dag-vs-weighted), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 핵심이 path cost 최소화다. 그 안에서 `unweighted shortest path` / `DAG shortest path` / `weighted shortest path`를 먼저 가르고, weighted shortest path면 `sparse vs dense`를 한 번 더 나눈다. 목표 정점이 또렷하면 A*까지 다시 갈라진다 |
| 그래프의 모든 정점을 **사이클 없이 최소 비용으로 연결**해야 하나 | [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md) | shortest path가 아니라 minimum spanning tree다 |
| DAG에서 **선후 관계를 만족하는 순서**만 구하면 되나 | [위상 정렬 패턴](./topological-sort-patterns.md) | dependency ordering 문제다 |
| 정사각 `cost matrix`의 **1:1 최소 비용 배정 / optimal assignment**인가 | [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md), [Min-Cost Max-Flow Intuition](./min-cost-max-flow-intuition.md) | 순수 assignment matrix면 Hungarian이 먼저고, capacity/supply 제약까지 붙으면 min-cost max-flow로 확장된다 |
| 간선에 `capacity`가 있거나 `max throughput` / `bottleneck` / `min cut` / bipartite matching / job assignment처럼 **총 얼마나 많이 보낼 수 있나, 어디가 전체 처리량을 막나**를 묻나 | [Network Flow Intuition](./network-flow-intuition.md) | shortest path가 아니라 throughput, bottleneck, min cut, residual graph, unit-capacity reduction이 핵심이다 |

### Shortest Path Router: Unweighted vs DAG vs Weighted

| 질문 phrasing | 먼저 갈 문서 | 왜 그 문서가 맞는가 |
|---|---|---|
| `unweighted shortest path`, `bfs shortest path`, `최소 칸 수`, `최소 이동 횟수`, `미로 최단 경로` | [알고리즘 기본](./basic.md#dfs와-bfs), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 가중치가 없거나 모두 같으면 BFS 레벨 탐색이 곧 최단 거리다 |
| `DAG shortest path`, `shortest path on DAG`, `topological shortest path`, `acyclic shortest path`, `의존성 그래프 최소 비용` | [Topological DP](./topological-dp.md), [위상 정렬 패턴](./topological-sort-patterns.md), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 위상 정렬은 계산 순서이고, 문제 자체는 shortest path다. DAG라면 음수 간선이 있어도 위상 순서 완화가 가능하다 |
| `weighted shortest path`, `positive weighted shortest path`, `양수 가중치 shortest path`, `single-source shortest path`, `routing cost`, `graph density shortest path`, `sparse graph shortest path`, `dense graph shortest path` | [Weighted Shortest Path Density Router: Sparse vs Dense](#weighted-shortest-path-density-router-sparse-vs-dense), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md), [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md) | weighted shortest path cluster의 기본 진입점이다. 음수 간선이 없으면 Dijkstra 계열이 기본이고, 밀도/표현 phrasing이 보이면 sparse vs dense를 한 번 더 나눠 deep dive로 보낸다 |
| `0-1 BFS`, `0/1 cost shortest path`, `binary edge weight shortest path`, `deque shortest path`, `teleport shortest path`, `portal shortest path`, `warp shortest path`, `순간이동 최단 경로` | [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | weighted shortest path 안에서도 가중치 분포가 바로 드러난 케이스다. teleport-style query라도 본질이 `0 edge + 1 edge`면 0-1 BFS bridge가 가장 직접적이다 |
| `negative-edge shortest path`, `negative edge`, `negative cycle`, `arbitrage` | [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | weighted shortest path 안에서도 음수 간선과 음수 사이클 검출 여부가 핵심이다 |
| `all-pairs shortest path`, `all pairs shortest path`, `distance matrix shortest path`, `모든 정점 쌍 최단 거리` | [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 시작점 하나가 아니라 전체 쌍을 한 번에 다뤄야 한다 |
| `pathfinding`, `point-to-point shortest path`, `source-to-target routing`, `goal-directed route`, `A*`, `heuristic search` | [A* vs Dijkstra](./a-star-vs-dijkstra.md), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 목표 정점이 분명한 shortest path cluster 안에서는 A*와 Dijkstra를 다시 비교해야 한다 |

#### Shortest Path Alias Normalization

| canonical phrase | 같이 걸리기 쉬운 alias | 먼저 연결되는 선택 |
|---|---|---|
| `single-source shortest path` | `single source shortest path`, `single-source routing`, `start-to-all routing`, `routing table shortest path`, `한 시작점에서 모든 정점까지`, `출발점 하나 전체 거리표` | Dijkstra / Bellman-Ford / DAG shortest path |
| `all-pairs shortest path` | `all pairs shortest path`, `pairwise shortest path`, `distance matrix shortest path`, `모든 정점 쌍 최단 거리`, `모든 노드 쌍 거리표` | Floyd-Warshall |
| `negative-edge shortest path` | `negative edge`, `negative weight shortest path`, `negative cycle`, `arbitrage`, `음수 간선 최단 경로` | Bellman-Ford 또는 DAG shortest path |
| `route planning` | `pathfinding`, `point-to-point shortest path`, `source-to-target routing`, `goal-directed route`, `heuristic search` | 목표 정점이 고정된 길찾기면 [A* vs Dijkstra](./a-star-vs-dijkstra.md), 아니면 `single-source` / `all-pairs` 축을 다시 본다 |

#### Weighted Shortest Path Density Router: Sparse vs Dense

`weighted shortest path`라고 해도 질문이 `희소/밀집`, `adjacency list/matrix`, `O(E log V) vs O(V^2)`처럼 그래프 밀도와 표현 vocabulary로 들어오면 deep dive에 바로 떨어지기 전에 한 번 더 갈라두는 편이 빠르다.

| 질문 phrasing | 먼저 갈 문서 | 왜 그 문서가 맞는가 |
|---|---|---|
| `sparse graph shortest path`, `graph density shortest path`, `sparse vs dense shortest path`, `adjacency list shortest path`, `priority queue dijkstra`, `routing cost on sparse network` | [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 양수 가중치 shortest path 안에서도 희소 그래프, PQ Dijkstra, 0-1 BFS, Dial 같은 density/weight-distribution 선택이 먼저 드러난다 |
| `dense graph shortest path`, `adjacency matrix shortest path`, `complete graph shortest path`, `dense weighted shortest path`, `matrix dijkstra`, `O(V^2) dijkstra` | [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md), [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md) | 밀집 그래프에서는 희소 그래프 최적화보다 `single-source vs all-pairs`, `negative-edge`, `O(V^2)` 행렬 감각이 더 큰 분기다. 필요하면 그다음 sparse-vs-dense 세부 선택으로 내려간다 |
| `0-1 BFS`, `zero one bfs`, `0/1 cost shortest path`, `deque shortest path`, `teleport shortest path`, `portal shortest path`, `warp shortest path`, `Dial`, `bucket shortest path`, `small integer shortest path` | [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md) | 희소 weighted shortest path의 특수 가중치 분포 질문이라 전용 변형을 먼저 잡는 편이 빠르다. teleport-style query라도 `0 cost edge / 1 cost edge`면 여기로 보낸다 |

### 빠른 판별 체크

- 간선 값이 비용(cost)이면 shortest path / MST 쪽이고, 용량(capacity)이면 flow 쪽이다.
- `bottleneck`, `min cut`, `minimum cut`, `cut capacity`, `어디가 병목인가`가 나오고 대상이 **전체 네트워크 처리량**이면 shortest path가 아니라 flow / min-cut 쪽이다.
- "모든 정점을 연결"이면 MST, "한 점에서 다른 점까지 간다"면 shortest path를 먼저 의심한다.
- shortest path라고 다 같은 bucket이 아니다. 먼저 `unweighted shortest path` / `DAG shortest path` / `weighted shortest path`로 가른다.
- 가중치가 없거나 모두 같으면 shortest path는 BFS부터 본다.
- DAG에서 비용 최소 / 최대 경로를 묻는 순간 위상 정렬은 계산 순서일 뿐이고, 문제 자체는 path optimization이다.
- `0-1 BFS`, `0/1 cost`, `deque shortest path`, `teleport shortest path`가 보이면 weighted shortest path 안에서도 [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)로 바로 브리지한다.
- `weighted shortest path` cluster 안에서는 `single-source shortest path` / `negative-edge shortest path` / `all-pairs shortest path`를 다시 나눠 Dijkstra, Bellman-Ford, Floyd-Warshall 쪽으로 보낸다.
- `sparse graph shortest path` / `dense graph shortest path` / `adjacency list shortest path` / `adjacency matrix shortest path`처럼 그래프 밀도와 표현이 먼저 보이면 weighted shortest path 안에서도 [Weighted Shortest Path Density Router: Sparse vs Dense](#weighted-shortest-path-density-router-sparse-vs-dense)를 한 번 더 거친다.
- `dense`라는 말이 보여도 `negative-edge shortest path`나 `all-pairs shortest path`가 같이 나오면 그래프 밀도보다 [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)의 큰 축이 우선이다.
- `pathfinding`, `point-to-point`, `goal-directed`, `navigation route` 같은 phrasing은 shortest path cluster 안에서 [A* vs Dijkstra](./a-star-vs-dijkstra.md)로 다시 갈라진다.
- 음수 간선 또는 음수 사이클 검출이 나오면 `negative-edge shortest path`로 normalize해서 Bellman-Ford를 먼저 확인한다.
- 모든 쌍의 최단 거리가 필요하면 `all-pairs shortest path`, 시작점 하나 기준이면 `single-source shortest path`로 normalize해 Dijkstra / Bellman-Ford를 우선 비교한다.
- `optimal assignment`, `linear assignment`, `cost matrix`, `1:1 weighted matching`이 먼저 보이면 generic graph보다 [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md)을 먼저 본다.
- `왼쪽 집합-오른쪽 집합`, `한 사람당 하나`, `최대 몇 쌍` 같은 문구가 보이면 bipartite matching을 flow reduction으로 바꾸는 쪽을 먼저 본다.

# 최단 경로 알고리즘

- 작성자 서그림 | [최단 경로 알고리즘](./materials/최단경로알고리즘.pdf)

## 최단 경로 문제

최단 경로 문제란, 가중 그래프에서 간선의 가중치의 합이 최소가 되는 경로를 찾는 문제이다. 최단 경로 문제는 다음과 같은 유형들이 있다.

- 단일 출발 (single-source) 최단 경로 : 어떤 하나의 정점에서 출발하여 나머지 모든 정점까지의 최단 경로를 찾는다.
- 단일 도착 (single-destination) 최단 경로 : 모든 정점에서 출발하여 어떤 하나의 정점까지의 최단 경로를 찾는다.  
  _(그래프 내의 간선들을 뒤집으면 단일 출발 최단 경로 문제로 바뀔 수 있다.)_
- 단일 쌍 (single-pair) 최단 경로 : 어떤 정점 v에서 v'로 가는 최단 경로를 찾는다.
- 전체 쌍 (all-pair) 최단 경로 : 모든 정점 쌍들 사이의 최단 경로를 찾는다.

최단 경로 문제를 해결하는 알고리즘으로는 대표적으로 **다익스트라, 벨만-포드, 플로이드-워셜 알고리즘**이 있다. 각 알고리즘을 적용하기 적합한 유형은 다음과 같다.

- 다익스트라 알고리즘 : **음이 아닌** 가중 그래프에서의 **단일 출발, 단일 도착, 단일 쌍** 최단 경로 문제
- 벨만-포드 알고리즘 : 가중 그래프에서의 **단일 출발, 단일 도착, 단일 쌍** 최단 경로 문제
- 플로이드-워셜 알고리즘 : **전체 쌍** 최단 경로 문제
- _BFS : 가중치가 없거나 가중치가 동일한 그래프에서 최단 경로를 찾는 경우 가장 빠르다._

## 다익스트라 알고리즘 (Dijkstra Algorithm)

그래프 G = (V, E) 에서 특정 출발 정점(S)에서 다른 모든 정점까지의 최단 경로를 구하는 알고리즘이다. 음의 가중치를 가지는 간선이 없을 때 정상적으로 동작한다.

### 알고리즘 설계 및 구현

1. 출발 노드 S를 설정한다.
2. 출발 노드 S에서 모든 노드들까지의 최단 거리를 저장하는 배열 D를 초기화한다.
3. 방문하지 않은 노드 중에서 최단 거리가 가장 짧은 노드를 선택한다. (D 배열 검사)
4. 해당 노드를 거쳐 다른 노드로 가는 비용을 계산하여 최단 거리 배열 D를 갱신한다.
5. 모든 노드를 방문할 때까지 3, 4 과정을 반복한다.

![다익스트라](https://user-images.githubusercontent.com/22045163/106482569-eca38480-64f0-11eb-9c52-28a886a9f947.gif)

다익스트라 알고리즘 구현 ▶️ [DijkstraTest.java](./code/DijkstraTest.java)

### 특징

- 각 정점을 최대 한 번씩만 방문하여 최단 거리를 확정한다.
- 아직 방문하지 않은 정점들 중 최단 거리인 정점을 찾아 방문하는 식으로 진행된다.
    - 이 때, 최단 거리가 최소인 정점을 찾는 과정에서 PriorityQueue 또는 Heap 자료구조를 이용하면 더욱 개선된 알고리즘이 가능하다.
- 매 순간마다 최단 거리의 정점을 선택하는 과정을 반복하므로 그리디 알고리즘으로 분류된다.
- 총 V x V 번 연산이 필요하므로 **O(V^2)** 의 시간복잡도를 가진다.

## 개선된 다익스트라 알고리즘

다익스트라 알고리즘에는 **방문하지 않은 노드 중에서 최단 거리가 가장 짧은 노드를 선택**하는 과정이 있다. 이 과정에서 다음과 같은 비용이 발생한다.

- 방문했는지 여부에 대한 정보를 저장하는 배열을 노드의 크기(V) 만큼 생성하고 접근해야 한다.
- D 배열을 모두 순회하여 최단 거리가 짧은 노드를 선택해야 한다.

이 과정을 PriorityQueue 또는 Heap 자료구조를 이용하면 노드를 선택하는 비용을 O(V)에서 O(log{`힙에 저장한 정점의 개수`})로 줄일 수 있다.
최단 거리가 가장 짧은 노드를 선택해야 하므로 **최소 힙**을 사용하면 되며, 힙을 통해 구현된 **Priority Queue**를 사용해도 좋다.
동작 과정은 다음과 같다.

1. 출발점에 대하여 D 배열을 초기화할 때 `D[S] = 0`을 해준다. 이와 동시에 힙에 노드 정보(번호, 거리 : `[S, 0]`)를 넣어준다.
2. 힙에서 맨 위에 있는 노드 I를 꺼낸다.
3. 만일 꺼낸 노드 I의 거리 정보가 현재 D[I]보다 크다면 이미 방문한 노드일 것이므로 무시한다.
4. I를 대상으로 다익스트라 알고리즘을 수행하는데, D 배열이 갱신될 경우 그 노드 정보를 힙에 넣는다.  
   (D[J] = D[I] + W 로 갱신될 경우 힙에 노드 J(`[J, D[J]]`)를 삽입한다.)
5. 힙에 노드가 없을 때까지 반복한다.

개선된 다익스트라 알고리즘의 시간 복잡도는 **O(ElogV)** 이다. (O(ElogE) → O(ElogV²) → O(2ElogV) → O(ElogV))

![개선다익스트라](https://user-images.githubusercontent.com/22045163/106778119-f9f37700-6688-11eb-8e6d-6e824596e184.jpg)

개선된 다익스트라 알고리즘 구현 ▶️ [DijkstraTest.java > class ImprovedDijkstra](./code/DijkstraTest.java)

## 벨만-포드 알고리즘 (Bellman-Ford-Moore Algorithm)

그래프 G = (V, E) 에서 특정 출발 정점(S)에서 다른 모든 정점까지의 최단 경로를 구하는 알고리즘이다. 다익스트라 알고리즘과 달리, 음의 가중치를 가지는 간선도 가능하다.

### 아이디어

- 가중 그래프 (V, E)에서 **어떤 정점 A에서 정점 B까지의 최단 거리는 최대 V - 1개의 간선을 사용**한다. (= 시작 정점 A를 포함하여 최대 V개의 정점을 지난다.)

### 알고리즘 설계 및 구현

1. 출발 노드 S를 설정한다.
2. 출발 노드 S에서 모든 노드들까지의 최단 거리를 저장하는 배열 D를 초기화한다.
3. 그래프의 모든 간선을 돌면서 각 노드로 가는 비용을 계산하여 최단 거리 배열 D를 갱신한다.
4. 3 과정을 (노드의 개수 - 1)번, 즉 V-1번 반복한다.
5. 3 과정을 한 번 더 반복하였을 때, 배열 D가 갱신되면 음의 사이클이 있는 것으로 판단한다.

![벨만포드](https://user-images.githubusercontent.com/22045163/106553083-f6160680-655b-11eb-8da9-cda67af0493e.gif)

벨만-포드 알고리즘 구현 ▶️ [BellmanFordTest.java](./code/BellmanFordTest.java)

### 특징

- 음의 가중치를 가지는 간선도 가능하므로, 음의 사이클의 존재 여부를 따져야 한다.
- 최단 거리를 구하기 위해서 V - 1번 E개의 모든 간선을 확인한다.
- 음의 사이클 존재 여부를 확인하기 위해서 한 번 더 (V번째) E개의 간선을 확인한다. 이 때 거리 배열이 갱신되었다면, 그래프 G는 음의 사이클을 가진다.
- 따라서 총 V x E 번 연산하므로 **O(VE)** 의 시간복잡도를 가진다.

## 플로이드-워셜 알고리즘 (Floyd-Warshall Algorithm)

그래프 G = (V, E) 에서 모든 정점 사이의 최단 경로를 구하는 알고리즘이다.

### 아이디어

- 어떤 두 정점 사이의 최단 경로는 **어떤 경유지(K)를 거치거나, 거치지 않는 경로 중 하나**이다. 즉 정점 A와 정점 B 사이의 최단 경로는 A-B 이거나 A-K-B 이다.
- 만약 경유지(K)를 거친다면 최단 경로를 이루는 부분 경로 역시 최단 경로이다. 즉 A-B의 최단 경로가 A-K-B라면 A-K와 K-B도 각각 최단 경로이다.

### 알고리즘 설계 및 구현

1. 각 노드들 사이의 최단 거리를 저장하는 2차원 배열 D를 초기화한다.
2. 각 노드가 경유지 K를 지날 때마다 최단 경로를 계산하여 배열 D를 갱신한다.
3. 동적 계획법으로 해결하며, 점화식은 `D[A][B] = min(D[A][B], D[A][K] + D[K][B]` 이다.

![플로이드워셜](https://user-images.githubusercontent.com/22045163/106489876-95091700-64f8-11eb-91fa-bd903685f284.gif)

플로이드-워셜 알고리즘 구현 ▶️ [FloydWarshallTest.java](./code/FloydWarshallTest.java)

### 특징

- 사이클이 없다면 음수 가중치를 가져도 적용 가능하다.
- 동적 계획법(Dynamic Programming)으로 접근한다.
- 모든 가능한 경유지에 대해서 모든 정점 -> 모든 정점으로 가는 최단 거리를 확인하므로 연산 횟수는 V^3이고, 따라서 시간복잡도는 **O(V^3)** 이다.

---

# 분리 집합(Union Find)과 크루스칼(Kruskal) 알고리즘

> 스터디 자료 - 작성자 정희재 | [Union Find & Kruskal Algorithm](./materials/유니온파인드.pdf)

## 서로소 집합(Disjoint Set)과 Union-Find

서로소 집합(Disjoint Set)은 교집합이 없는, 즉 공통되는 원소가 없는 집합을 말한다. Union-Find는 서로소 집합을 표현할 때 사용되는 알고리즘으로, 서로소 집합의 정보를 확인(Find)하고 조작(Union)한다. Union Find 알고리즘을 이용하면 **서로 다른 두 노드가 같은 집합 내에 속해 있는지 확인**할 수 있다.

### Union Find 구현

#### 초기화 (initialize)

root 배열에 i 원소의 부모 노드 번호를 저장한다. i 원소가 루트 노드라면, 자기 자신의 번호를 저장한다.

```java
void initialize() {
    for (int i = 1; i <= N; i++) {
        root[i] = i;
    }
}
```

#### n번 노드의 root 노드 번호 찾기 (find)

```java
int find(int n) {
    if (root[n] == n) return n;
    return root[n] = find(root[n]);
}
```

#### a 노드와 b 노드를 같은 집합으로 묶기 (merge, union)

```java
void merge(int a, int b) {
    root[find(b)] = find(a);
}
```

## Union Find를 활용한 MST 찾기 - Kruskal Algorithm

무향 그래프 G가 순환이 없는 연결 그래프이면 그래프 G는 트리(Tree)이다.

신장 트리 (Spanning Tree)란 무향 연결 그래프 G의 부분 그래프이며, G의 모든 정점을 포함하는 트리(Tree)인 그래프이다.

여기서 최소 신장 트리 (Minimum Spanning Tree, MST)란 무향 연결 그래프 G에서 간선의 가중치의 합이 최소인 신장 트리이다. 이 최소 신장 트리 MST를 구할 수 있는 알고리즘으로는 크루스칼 알고리즘, 프림 알고리즘이 있다. 간선 리스트를 정렬해 사이클만 막으면 되는 문제는 크루스칼이 설명하기 쉽고, 인접 정점을 확장하는 모델이 더 자연스러운 상황에서는 프림도 자주 쓰인다. 여기서는 Union-Find와 연결되는 크루스칼 알고리즘을 중심으로 본다.

> Prim vs Kruskal 선택 기준, MST와 shortest path 경계, minimum spanning forest 예외는 [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md)에서 따로 정리한다.

### Kruskal Algorithm 구현

1. (Cost, A, B) 리스트를 만들어서 모든 간선들의 정보를 Priority Queue에 저장한다. (최소 힙)
2. Priority Queue에서 하나씩 pop하면서 **만약 A와 B가 연결되어 있지 않다면 A와 B를 연결**하고 전체 비용에 Cost를 더한다.
3. **만일 A와 B가 연결되어 있다면** 무시한다.

굵은 글씨 부분을 Union-Find로 구현한다.

> 시간 복잡도 (E: 간선의 개수) : ![formula](https://render.githubusercontent.com/render/math?math=O(Elog_2E))

Kruskal 알고리즘 구현 ▶️ [KruskalTest.java](./code/KruskalTest.java)

---

# 위상 정렬 패턴

- [위상 정렬 패턴](./topological-sort-patterns.md)

위상 정렬은 선후 관계를 만족하는 순서를 찾는 그래프 패턴이다.
선수 과목, 빌드 순서, 작업 의존성, 배포 순서를 볼 때 가장 먼저 떠올려야 한다.
