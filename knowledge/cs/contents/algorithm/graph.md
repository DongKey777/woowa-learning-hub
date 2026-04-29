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

한 번 더 5초로 자르면 아래 네 줄이면 충분하다.

| 들린 문장 | beginner 첫 판정 | 먼저 갈 문서 |
|---|---|---|
| `갈 수 있나?`, `같은 그룹인가?` | yes/no 연결성 | [Connectivity Question Router](../data-structure/connectivity-question-router.md) |
| `아무 경로 하나만 보여줘` | shortest path가 아니라 path reconstruction | [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md) |
| `최소 몇 번 만에 가나?` | unweighted shortest path | [DFS와 BFS 입문](./dfs-bfs-intro.md) |
| `비용 합이 최소인가?` | weighted shortest path | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) |

## beginner stop line

백엔드 주니어가 첫 회독에서 이 문서를 끝까지 읽어야 하는 경우는 드물다. 아래 중 하나가 정리되면 여기서 멈추고 관련 문서 한 장만 내려가는 편이 beginner-safe 하다.

| 지금 정리된 것 | 여기서 멈추고 갈 문서 | 왜 더 내려가지 않나 |
|---|---|---|
| `갈 수 있나`와 `최소 몇 번`을 구분했다 | [DFS와 BFS 입문](./dfs-bfs-intro.md) | BFS/DFS 판단까지면 첫 분기로 충분하다 |
| `최소 이동 횟수`와 `최소 비용`을 구분했다 | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) | weighted shortest path 전체 비교는 다음 단계다 |
| `모든 정점을 연결`이 shortest path가 아니라는 걸 알았다 | [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md) | MST 세부 구현은 별도 문서가 더 직접적이다 |
| `한 번에 얼마나 많이 보내나`가 path가 아니라 flow라는 걸 알았다 | [Network Flow Intuition](./network-flow-intuition.md) | flow는 용량과 절단 vocabulary가 먼저다 |

이 아래는 `한 단계 더 내려갈 follow-up 링크를 고르는 구간`으로만 써도 충분하다. beginner primer로는 `그래프 기초 -> DFS와 BFS 입문 -> 이 문서 상단 라우터`까지만 잡아도 된다.

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

## 다음 한 장만 고르기

이 문서에서 더 중요한 것은 `심화 내용을 다 읽는 것`이 아니라 `다음 문서 한 장만 정확히 고르는 것`이다.

| 지금 보이는 질문 | 바로 갈 문서 | 왜 여기서 멈추나 |
|---|---|---|
| `같은 그룹인가`, `연결돼 있나`, `컴포넌트 개수/크기` | [Connectivity Question Router](../data-structure/connectivity-question-router.md) | yes/no와 component 질문을 shortest path와 섞지 않기 위해 |
| `최소 몇 번`, `최소 칸 수`, `미로 최단 경로` | [DFS와 BFS 입문](./dfs-bfs-intro.md) | 무가중치 shortest path 첫 분기는 BFS가 더 직접적이어서 |
| `최소 비용`, `가중치 합`, `음수 간선`, `전체 쌍 최단 경로` | [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | weighted shortest path 큰 축을 먼저 잡아야 해서 |
| `0-1 BFS`, `순간이동`, `0/1 cost` | [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md) | 특수 가중치 분포는 전용 bridge가 더 짧아서 |
| `의존성 순서`, `build order`, `course schedule` | [위상 정렬 패턴](./topological-sort-patterns.md) | path보다 순서 제약이 핵심이어서 |
| `모든 정점을 최소 비용으로 연결` | [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md) | shortest path가 아니라 spanning tree 문제여서 |
| `최대 유량`, `병목`, `min cut`, `배정` | [Network Flow Intuition](./network-flow-intuition.md), [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md) | 여러 경로의 총 처리량이나 exact matching이 중심이라서 |

첫 회독이라면 여기서 멈추면 된다. 아래 legacy 라우터와 알고리즘 정리는 `추가 비교가 정말 필요할 때만` 참고한다.

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

## 여기서 바로 넘길 심화 분기

이 문서는 `그래프 문제를 무슨 갈래로 읽을지` 정리하는 데서 멈추면 된다. 다익스트라 구현 세부, union-find 최적화, 위상 정렬 패턴, flow 절차를 한 문서에서 다 읽기 시작하면 beginner용 라우터 역할이 흐려진다.

| 지금 분명히 보이는 질문 | 바로 갈 문서 | 왜 여기서 끊는가 |
|---|---|---|
| `양수 가중치 최단 경로를 구현해야 해요` | [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 이 문서 역할은 shortest path 분류까지다 |
| `희소 그래프`, `0-1 BFS`, `deque shortest path`가 보여요 | [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md) | 밀도와 가중치 분포는 별도 deep dive가 더 직접적이다 |
| `모든 정점을 최소 비용으로 연결`이 핵심이에요 | [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md) | shortest path와 MST를 섞지 않도록 전용 문서로 보낸다 |
| `반복 yes/no 연결성 질의`가 핵심이에요 | [Connectivity Question Router](../data-structure/connectivity-question-router.md) | union-find 구현보다 질문 종류를 먼저 확정해야 한다 |
| `한 번에 얼마나 많이 보내나`, `min cut`이 보여요 | [Network Flow Intuition](./network-flow-intuition.md) | flow는 path보다 throughput vocabulary가 먼저다 |
| `선행 작업 순서`, `DAG 계산 순서`가 먼저예요 | [위상 정렬 패턴](./topological-sort-patterns.md) | 위상 정렬은 순서 생성 전용 mental model이 필요하다 |

## 한 줄 정리

그래프 문제는 `무엇을 답해야 하는가`부터 자른 뒤, beginner는 여기서 멈추고 shortest path / MST / connectivity / flow / DAG 순서 제약 중 맞는 follow-up 한 장으로만 내려가면 된다.
