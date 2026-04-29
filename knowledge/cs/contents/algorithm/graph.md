# 그래프 관련 알고리즘

> 한 줄 요약: 그래프 문제를 보면 먼저 `연결`, `경로`, `최소 이동 횟수`, `최소 비용`, `전체 연결`, `흐름` 중 무엇을 묻는지부터 자르는 follow-up 라우터 문서다.

**난이도: 🟡 Intermediate**

retrieval-anchor-keywords: graph router, graph follow-up router, shortest path router, weighted shortest path, unweighted shortest path, mst router, topological sort, dsu vs bfs, same group vs actual path, graph basics next step, 왜 bfs예요, graph 뭐예요 다음, 그래프 라우터, 최단 경로, 연결성 질문

관련 문서:
- [그래프 기초](../data-structure/graph-basics.md)
- [DFS와 BFS 입문](./dfs-bfs-intro.md)
- [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- [Connectivity Question Router](../data-structure/connectivity-question-router.md)
- [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)
- [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md)
- [Network Flow Intuition](./network-flow-intuition.md)

> 작성자 : [서그림](https://github.com/Seogeurim), [정희재](https://github.com/Hee-Jae)

<details>
<summary>Table of Contents</summary>

- [beginner stop line](#beginner-stop-line)
- [그래프 문제 Decision Router](#그래프-문제-decision-router)
- [Shortest Path Router: Unweighted vs DAG vs Weighted](#shortest-path-router-unweighted-vs-dag-vs-weighted)
- [Weighted Shortest Path Density Router: Sparse vs Dense](#weighted-shortest-path-density-router-sparse-vs-dense)

</details>

> 문서 역할: 이 문서는 algorithm 카테고리 안에서 **graph basics/dfs-bfs primer 다음 단계의 그래프 라우터** 역할을 한다.

---

## beginner 먼저 자를 질문

이 문서는 `그래프 문제를 더 넓게 분기하는 라우터`다. 아직 `그래프가 뭐예요`, `왜 queue가 같이 나와요`, `갈 수 있나`와 `최소 이동 횟수`가 섞인다면 이 문서를 깊게 읽기보다 아래처럼 한 칸 뒤로 물러나는 편이 더 안전하다.

| 지금 막힌 문장 | 먼저 볼 문서 | 왜 여기서 끊는가 |
|---|---|---|
| `그래프가 뭐예요?`, `격자도 그래프인가요?` | [그래프 기초](../data-structure/graph-basics.md) | 정점/간선 그림이 먼저다 |
| `갈 수 있나?`, `같은 그룹인가?` | [Connectivity Question Router](../data-structure/connectivity-question-router.md) | 답의 모양이 `yes/no`인지 먼저 자른다 |
| `아무 경로 하나 보여줘` | [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md) | shortest path가 아니라 경로 복원 질문이다 |
| `최소 이동 횟수`, `최소 칸 수` | [DFS와 BFS 입문](./dfs-bfs-intro.md) | 무가중치 shortest path는 BFS가 먼저다 |
| `최소 비용`, `가중치 합` | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) | BFS와 weighted shortest path를 분리해야 한다 |
| `모든 정점을 싸게 연결` | [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md) | path가 아니라 spanning tree 질문이다 |

짧게 외우면 `구조가 낯설면 graph basics`, `yes/no면 connectivity`, `최소 이동 횟수면 BFS`, `최소 비용이면 Dijkstra 계열`이다.

## beginner stop line

백엔드 주니어가 첫 회독에서 이 문서를 끝까지 읽어야 하는 경우는 드물다. 아래 중 하나가 정리되면 여기서 멈추고 관련 문서 한 장만 내려가는 편이 beginner-safe 하다.

| 지금 정리된 것 | 여기서 멈추고 갈 문서 | 왜 더 내려가지 않나 |
|---|---|---|
| `갈 수 있나`와 `최소 몇 번`을 구분했다 | [DFS와 BFS 입문](./dfs-bfs-intro.md) | BFS/DFS 판단까지면 첫 분기로 충분하다 |
| `최소 이동 횟수`와 `최소 비용`을 구분했다 | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) | weighted shortest path 전체 비교는 다음 단계다 |
| `모든 정점을 연결`이 shortest path가 아니라는 걸 알았다 | [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md) | MST 세부 구현은 별도 문서가 더 직접적이다 |
| `한 번에 얼마나 많이 보내나`가 path가 아니라 flow라는 걸 알았다 | [Network Flow Intuition](./network-flow-intuition.md) | flow는 용량과 절단 vocabulary가 먼저다 |

이 아래의 legacy 설명은 `심화 비교나 옛 정리까지 이어 읽고 싶을 때만` 참고하면 된다. beginner primer로는 `그래프 기초 -> DFS와 BFS 입문 -> 이 문서 상단 라우터`까지만 잡아도 충분하다.

## 같은 장면 30초 예시

백엔드 주니어가 `창고 네트워크`, `미로`, `지하철` 문장을 읽을 때는 장면보다 **무엇을 답해야 하는지**를 먼저 자르는 편이 안전하다.

| 같은 장면에서 들린 말 | 실제로 답할 것 | 첫 문서 |
|---|---|---|
| `A 창고에서 B 창고로 갈 수 있나?` | yes/no 연결 여부 | [Connectivity Question Router](../data-structure/connectivity-question-router.md) |
| `A에서 B까지 아무 경로 하나만 보여줘` | actual path 하나 | [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md) |
| `A에서 B까지 최소 몇 번 만에 가나?` | unweighted shortest path | [DFS와 BFS 입문](./dfs-bfs-intro.md) |
| `모든 창고를 가장 싸게 연결해 줘` | spanning tree 비용 최소 | [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md) |
| `한 번에 얼마나 많이 흘려보낼 수 있나?` | total throughput / bottleneck | [Network Flow Intuition](./network-flow-intuition.md) |

- `왜 bfs예요?`, `왜 mst가 아니죠?`, `왜 shortest path가 아니고 flow예요?` 같은 symptom은 장면이 아니라 **답의 모양**을 잘못 잡았을 때 생긴다.

## 자주 섞는 오해

| 헷갈린 첫 판단 | 바로 고칠 한 줄 | 돌아갈 문서 |
|---|---|---|
| `graph가 보이니까 bfs겠지` | graph는 구조 이름일 뿐이라 연결, 경로, 비용, 흐름으로 다시 잘라야 한다 | [그래프 기초](../data-structure/graph-basics.md) |
| `최소면 다 bfs겠지` | `최소 이동 횟수`와 `최소 비용`은 다른 질문이다 | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) |
| `같은 그룹인가`도 shortest path겠지 | yes/no connectivity는 path 자체를 묻지 않을 수 있다 | [Connectivity Question Router](../data-structure/connectivity-question-router.md) |
| `모든 정점을 연결`도 shortest path겠지 | 한 쌍 경로가 아니라 전체 연결 비용이면 MST 질문이다 | [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md) |

- beginner 기준 1차 분기는 `갈 수 있나`, `어떻게 가나`, `최소 몇 번/얼마`, `전부 연결하나`, `얼마나 많이 보내나` 다섯 줄이면 충분하다.

## 이 문서 다음에 보면 좋은 문서

- `same-component`, `connected yes/no`, `경로 하나 복원`, `최단 경로` phrasing가 한데 섞이면 [Connectivity Question Router](../data-structure/connectivity-question-router.md)에서 먼저 답의 모양을 `yes/no vs actual path vs minimum`으로 가르는 편이 빠르다.
- `same component query`, `same set query`, `connected yes/no`, `connected components`, `connected component count`, `union-find`, `dsu`, `유니온파인드`, `서로소 집합`, `같은 그룹인가`, `컴포넌트 크기`, `컴포넌트 개수`처럼 DSU 초보 phrasing가 먼저 보이면 [Connectivity Question Router](../data-structure/connectivity-question-router.md)로 바로 가서 `yes/no vs size/count vs actual path vs minimum path`를 먼저 고르는 편이 빠르다.
- `unweighted shortest path`, `bfs shortest path`, `최소 칸 수`, `미로 최단 경로`처럼 무가중치 shortest path가 먼저면 [DFS와 BFS 입문](./dfs-bfs-intro.md)에서 BFS 레벨 탐색을 먼저 보는 편이 빠르다.
- `dag shortest path`, `topological shortest path`, `의존성 그래프 최소 비용`처럼 DAG 위 path optimization이 핵심이면 [Topological DP](./topological-dp.md)와 [위상 정렬 패턴](./topological-sort-patterns.md)을 같이 보면 좋다.
- `weighted shortest path`, `single-source shortest path`, `single-source routing`, `all-pairs shortest path`, `negative-edge shortest path`처럼 가중치 shortest path 선택 기준이 핵심이면 [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)로 이어지면 좋다.

## shortest path 브리지 문서

- `sparse graph shortest path`, `dense graph shortest path`, `adjacency list shortest path`, `adjacency matrix shortest path`, `graph density shortest path`처럼 그래프 밀도/표현이 먼저 보이면 아래의 [Weighted Shortest Path Density Router: Sparse vs Dense](#weighted-shortest-path-density-router-sparse-vs-dense)를 한 번 거친 뒤, 희소 그래프 쪽은 [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md), 밀집 그래프 쪽은 [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)로 가면 된다.
- `0-1 BFS`, `0/1 cost shortest path`, `deque shortest path`, `teleport shortest path`, `portal shortest path`, `warp shortest path`, `순간이동 최단 경로`처럼 특수 weighted shortest-path phrasing이면 [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)로 바로 보내는 편이 빠르다. 대개 `0 edge + 1 edge` 모델인지 먼저 확인하면 된다.
- `pathfinding`, `point-to-point shortest path`, `goal-directed routing`, `A*`처럼 목표 정점이 또렷한 질문이면 [A* vs Dijkstra](./a-star-vs-dijkstra.md)로 이어지면 좋다.

## shortest path 밖의 그래프 문서

- `build order`, `course schedule`, `dependency ordering`처럼 DAG 순서 문제를 따로 분리해서 보고 싶다면 [위상 정렬 패턴](./topological-sort-patterns.md)이 가장 직접적이다.
- `MST`, `minimum spanning tree`, `Prim vs Kruskal`, `모든 정점을 최소 비용으로 연결` 같은 질문이면 [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md)로 먼저 가는 편이 더 직접적이다.
- `optimal assignment`, `linear assignment`, `1:1 weighted matching`, `cost matrix assignment`처럼 exact 배정이 핵심이면 [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md)부터 확인하는 편이 정확하다.
- `bottleneck`, `min cut`, `minimum cut`, `cut capacity`, `maximum throughput`, `네트워크 병목`, `최소 절단`처럼 전체 처리량을 막는 절단/병목을 묻는 phrasing이면 [Network Flow Intuition](./network-flow-intuition.md)으로 바로 넘어가야 한다. 한 경로의 최단 거리보다 cut과 capacity가 핵심이다.
- 경로 하나가 아니라 여러 경로를 통한 총 처리량, 배정, 매칭 문제라면 [Network Flow Intuition](./network-flow-intuition.md)으로 넘어가는 편이 정확하다.

## 그래프 문제 Decision Router

그래프 문제는 먼저 답의 모양을 구분하면 길을 잃지 않는다.
`same-group yes/no`, `path 하나`, `tree 하나`, `order 하나`, `flow 양` 중 무엇을 묻는지 먼저 보면 된다.

> 초보자 빠른 비교:
> - `같은 그룹인가?`만 묻는다 -> DSU(Union-Find)
> - `1에서 7까지 실제로 어떻게 가나?`를 묻는다 -> BFS/DFS + `parent`
> - DSU는 연결 여부를 빠르게 확인하지만 `1 -> 3 -> 7` 같은 실제 경로는 주지 못한다.

| 문제에서 먼저 확인할 질문 | 먼저 갈 문서 | 왜 그 문서가 맞는가 |
|---|---|---|
| `같은 컴포넌트인가?`, `same set`, `connected yes/no`, `component size/count`처럼 연결성 확인이 먼저인가 | [Connectivity Question Router](../data-structure/connectivity-question-router.md), [분리 집합(Union Find)과 크루스칼(Kruskal) 알고리즘](#분리-집합Union-Find과-크루스칼Kruskal-알고리즘) | 답의 모양이 `yes/no` 또는 `size/count`면 shortest path보다 DSU 계열 분기가 먼저다 |
| 한 정점에서 다른 정점까지 **최소 비용 / 최단 거리**를 구하나 | [Shortest Path Router: Unweighted vs DAG vs Weighted](#shortest-path-router-unweighted-vs-dag-vs-weighted), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 핵심이 path cost 최소화다. 그 안에서 `unweighted shortest path` / `DAG shortest path` / `weighted shortest path`를 먼저 가르고, weighted shortest path면 `sparse vs dense`를 한 번 더 나눈다. 목표 정점이 또렷하면 A*까지 다시 갈라진다 |
| 그래프의 모든 정점을 **사이클 없이 최소 비용으로 연결**해야 하나 | [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md) | shortest path가 아니라 minimum spanning tree다 |
| DAG에서 **선후 관계를 만족하는 순서**만 구하면 되나 | [위상 정렬 패턴](./topological-sort-patterns.md) | dependency ordering 문제다 |

## 그래프 문제 Decision Router: 배정과 flow

| 문제에서 먼저 확인할 질문 | 먼저 갈 문서 | 왜 그 문서가 맞는가 |
|---|---|---|
| 정사각 `cost matrix`의 **1:1 최소 비용 배정 / optimal assignment**인가 | [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md), [Min-Cost Max-Flow Intuition](./min-cost-max-flow-intuition.md) | 순수 assignment matrix면 Hungarian이 먼저고, capacity/supply 제약까지 붙으면 min-cost max-flow로 확장된다 |
| 간선에 `capacity`가 있거나 `max throughput` / `bottleneck` / `min cut` / bipartite matching / job assignment처럼 **총 얼마나 많이 보낼 수 있나, 어디가 전체 처리량을 막나**를 묻나 | [Network Flow Intuition](./network-flow-intuition.md) | shortest path가 아니라 throughput, bottleneck, min cut, residual graph, unit-capacity reduction이 핵심이다 |

## Shortest Path Router: Unweighted vs DAG vs Weighted

| 질문 phrasing | 자연어 질문 예시 | 먼저 갈 문서 | 왜 그 문서가 맞는가 |
|---|---|---|---|
| `unweighted shortest path`, `bfs shortest path`, `최소 칸 수`, `최소 이동 횟수`, `미로 최단 경로` | `이 미로에서 목표 지점까지 최소 이동 횟수는 몇 번이야?` | [알고리즘 기본](./basic.md#dfs와-bfs), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 가중치가 없거나 모두 같으면 BFS 레벨 탐색이 곧 최단 거리다 |
| `DAG shortest path`, `shortest path on DAG`, `topological shortest path`, `acyclic shortest path`, `의존성 그래프 최소 비용` | `선행 작업 순서를 지키면서 목표 지점까지 가는 최소 비용은 얼마야?` | [Topological DP](./topological-dp.md), [위상 정렬 패턴](./topological-sort-patterns.md), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 위상 정렬은 계산 순서이고, 문제 자체는 shortest path다. DAG라면 음수 간선이 있어도 위상 순서 완화가 가능하다 |

## Shortest Path Router: weighted와 0-1 BFS

| 질문 phrasing | 자연어 질문 예시 | 먼저 갈 문서 | 왜 그 문서가 맞는가 |
|---|---|---|---|
| `weighted shortest path`, `positive weighted shortest path`, `양수 가중치 shortest path`, `single-source shortest path`, `routing cost`, `graph density shortest path`, `sparse graph shortest path`, `dense graph shortest path` | `출발점에서 목표 지점까지 가는 최소 비용 경로를 찾고 싶어.` | [Weighted Shortest Path Density Router: Sparse vs Dense](#weighted-shortest-path-density-router-sparse-vs-dense), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md), [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md) | weighted shortest path cluster의 기본 진입점이다. 음수 간선이 없으면 Dijkstra 계열이 기본이고, 밀도/표현 phrasing이 보이면 sparse vs dense를 한 번 더 나눠 deep dive로 보낸다 |
| `0-1 BFS`, `0/1 cost shortest path`, `binary edge weight shortest path`, `deque shortest path`, `teleport shortest path`, `portal shortest path`, `warp shortest path`, `순간이동 최단 경로` | `걷기는 1초, 순간이동은 0초일 때 목표 지점까지 가장 빨리 가려면?` | [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | weighted shortest path 안에서도 가중치 분포가 바로 드러난 케이스다. teleport-style query라도 본질이 `0 edge + 1 edge`면 0-1 BFS bridge가 가장 직접적이다 |

## Shortest Path Router: 음수 간선, 전체 쌍, 길찾기

| 질문 phrasing | 자연어 질문 예시 | 먼저 갈 문서 | 왜 그 문서가 맞는가 |
|---|---|---|---|
| `negative-edge shortest path`, `negative edge`, `negative cycle`, `arbitrage` | `보상 간선까지 있을 때 목표 지점까지 최소 비용이 음수로 계속 줄어드는지 알고 싶어.` | [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | weighted shortest path 안에서도 음수 간선과 음수 사이클 검출 여부가 핵심이다 |
| `all-pairs shortest path`, `all pairs shortest path`, `distance matrix shortest path`, `모든 정점 쌍 최단 거리` | `모든 지점끼리의 최소 비용을 한 번에 표로 만들고 싶어.` | [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 시작점 하나가 아니라 전체 쌍을 한 번에 다뤄야 한다 |
| `pathfinding`, `point-to-point shortest path`, `source-to-target routing`, `goal-directed route`, `A*`, `heuristic search` | `현재 위치에서 목표 지점까지 빨리 가는 길을 바로 찾고 싶어.` | [A* vs Dijkstra](./a-star-vs-dijkstra.md), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 목표 정점이 분명한 shortest path cluster 안에서는 A*와 Dijkstra를 다시 비교해야 한다 |

## Shortest Path Alias Normalization

| canonical phrase | 같이 걸리기 쉬운 alias | 먼저 연결되는 선택 |
|---|---|---|
| `single-source shortest path` | `single source shortest path`, `single-source routing`, `start-to-all routing`, `routing table shortest path`, `한 시작점에서 모든 정점까지`, `출발점 하나 전체 거리표` | Dijkstra / Bellman-Ford / DAG shortest path |
| `all-pairs shortest path` | `all pairs shortest path`, `pairwise shortest path`, `distance matrix shortest path`, `모든 정점 쌍 최단 거리`, `모든 노드 쌍 거리표` | Floyd-Warshall |
| `negative-edge shortest path` | `negative edge`, `negative weight shortest path`, `negative cycle`, `arbitrage`, `음수 간선 최단 경로` | Bellman-Ford 또는 DAG shortest path |
| `route planning` | `pathfinding`, `point-to-point shortest path`, `source-to-target routing`, `goal-directed route`, `heuristic search` | 목표 정점이 고정된 길찾기면 [A* vs Dijkstra](./a-star-vs-dijkstra.md), 아니면 `single-source` / `all-pairs` 축을 다시 본다 |

## Weighted Shortest Path Density Router: Sparse vs Dense

`weighted shortest path`라고 해도 질문이 `희소/밀집`, `adjacency list/matrix`, `O(E log V) vs O(V^2)`처럼 그래프 밀도와 표현 vocabulary로 들어오면 deep dive에 바로 떨어지기 전에 한 번 더 갈라두는 편이 빠르다.

## Weighted Shortest Path Density Router: Sparse vs Dense (계속 2)

| 질문 phrasing | 먼저 갈 문서 | 왜 그 문서가 맞는가 |
|---|---|---|
| `sparse graph shortest path`, `graph density shortest path`, `sparse vs dense shortest path`, `adjacency list shortest path`, `priority queue dijkstra`, `routing cost on sparse network` | [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 양수 가중치 shortest path 안에서도 희소 그래프, PQ Dijkstra, 0-1 BFS, Dial 같은 density/weight-distribution 선택이 먼저 드러난다 |
| `dense graph shortest path`, `adjacency matrix shortest path`, `complete graph shortest path`, `dense weighted shortest path`, `matrix dijkstra`, `O(V^2) dijkstra` | [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md), [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md) | 밀집 그래프에서는 희소 그래프 최적화보다 `single-source vs all-pairs`, `negative-edge`, `O(V^2)` 행렬 감각이 더 큰 분기다. 필요하면 그다음 sparse-vs-dense 세부 선택으로 내려간다 |
| `0-1 BFS`, `zero one bfs`, `0/1 cost shortest path`, `deque shortest path`, `teleport shortest path`, `portal shortest path`, `warp shortest path`, `Dial`, `bucket shortest path`, `small integer shortest path` | [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md) | 희소 weighted shortest path의 특수 가중치 분포 질문이라 전용 변형을 먼저 잡는 편이 빠르다. teleport-style query라도 `0 cost edge / 1 cost edge`면 여기로 보낸다 |

## 빠른 판별 체크

- `같은 그룹인지 yes/no만` 묻거나 `컴포넌트 크기/개수`가 같이 나오면 shortest path 전에 [Connectivity Question Router](../data-structure/connectivity-question-router.md)로 먼저 보낸다.
- 간선 값이 비용(cost)이면 shortest path / MST 쪽이고, 용량(capacity)이면 flow 쪽이다.
- `bottleneck`, `min cut`, `minimum cut`, `cut capacity`, `어디가 병목인가`가 나오고 대상이 **전체 네트워크 처리량**이면 shortest path가 아니라 flow / min-cut 쪽이다.
- "모든 정점을 연결"이면 MST, "한 점에서 다른 점까지 간다"면 shortest path를 먼저 의심한다.
- shortest path라고 다 같은 bucket이 아니다. 먼저 `unweighted shortest path` / `DAG shortest path` / `weighted shortest path`로 가른다.
- 가중치가 없거나 모두 같으면 shortest path는 BFS부터 본다.
- DAG에서 비용 최소 / 최대 경로를 묻는 순간 위상 정렬은 계산 순서일 뿐이고, 문제 자체는 path optimization이다.
- `0-1 BFS`, `0/1 cost`, `deque shortest path`, `teleport shortest path`가 보이면 weighted shortest path 안에서도 [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)로 바로 브리지한다.
- `weighted shortest path` cluster 안에서는 `single-source shortest path` / `negative-edge shortest path` / `all-pairs shortest path`를 다시 나눠 Dijkstra, Bellman-Ford, Floyd-Warshall 쪽으로 보낸다.
- `sparse graph shortest path` / `dense graph shortest path` / `adjacency list shortest path` / `adjacency matrix shortest path`처럼 그래프 밀도와 표현이 먼저 보이면 weighted shortest path 안에서도 [Weighted Shortest Path Density Router: Sparse vs Dense](#weighted-shortest-path-density-router-sparse-vs-dense)를 한 번 더 거친다.

## 빠른 판별 체크 (계속 2)

- `dense`라는 말이 보여도 `negative-edge shortest path`나 `all-pairs shortest path`가 같이 나오면 그래프 밀도보다 [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)의 큰 축이 우선이다.

## 빠른 판별 체크 2

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

## 한 줄 정리

그래프 문제는 "연결만 확인하는가, 최단 경로를 구하는가, 모두를 최소 비용으로 잇는가, 순서를 정하는가, 총 처리량을 따지는가"를 먼저 가르면 다음 문서와 알고리즘이 훨씬 빨리 보인다.
