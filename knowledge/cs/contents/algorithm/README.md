# Algorithm (알고리즘)

**난이도: 🟡 Intermediate**

> retrieval-anchor-keywords: algorithm readme, algorithm navigator, algorithm primer, time complexity, amortized analysis, binary search pattern, sliding window, contiguous index interval, interval greedy, interval scheduling, merge intervals, insert interval, interval merge, batch interval merge, start time sort, end time sort, sweep line, sweep-line, line sweep, meeting room, meeting rooms i, meeting rooms ii, meeting rooms 2, minimum meeting rooms, max concurrency, peak concurrency, overlap counting, room allocation, minimum number of platforms, hotel booking possible, car pooling, calendar overlap, overlap removal, reservation scheduling, dynamic interval query boundary, online interval insert boundary, calendar booking routing, my calendar routing, interval tree handoff, disjoint interval set handoff, window vs interval scheduling, calendar overlap not sliding window, greedy algorithm overview, greedy overview, greedy primer, greedy choice, greedy choice property, optimal substructure, exchange argument, when greedy works, when greedy fails, 탐욕 알고리즘 개요, 그리디 알고리즘 개요, 탐욕 선택 속성, 최적 부분 구조, two-pointer, lis, longest increasing subsequence, subsequence vs subarray, contiguous subarray, monotonic predicate, answer space search, graph algorithm, graph problem router, path vs tree vs order vs flow, shortest path, shortest path router, shortest path cluster, unweighted vs dag vs weighted shortest path, weighted shortest path, positive weighted shortest path, weighted shortest path router, graph density shortest path, sparse graph shortest path, dense graph shortest path, sparse vs dense shortest path, adjacency list shortest path, adjacency matrix shortest path, sparse weighted shortest path, dense weighted shortest path, edge density shortest path, bfs shortest path, unweighted shortest path, maze shortest path, maze navigation, maze-navigation, maze pathfinding, minimum move count, dag shortest path, shortest path on dag, point-to-point shortest path, point to point shortest path, weighted point-to-point routing, route planning, route-planning, weighted route planning, minimum cost route between two nodes, 가중치 길찾기, 두 정점 사이 최소 비용 경로, single-pair shortest path, single pair shortest path, source-to-target routing, goal-directed shortest path, goal-directed pathfinding, target-fixed shortest path, target fixed shortest path, fixed-target shortest path, fixed destination shortest path, start-to-goal shortest path, origin-destination shortest path, graph pathfinding, pathfinding router, heuristic search, negative edge, all pairs shortest path, 0-1 bfs, zero one bfs, binary weight shortest path, binary edge weight shortest path, 0/1 cost shortest path, deque shortest path, shortest path with deque, free paid edge shortest path, teleport shortest path, portal shortest path, warp shortest path, teleport cost 0 walk cost 1, 순간이동 최단 경로, minimum spanning tree, MST, mst entry, mst router, mst interview question, prim vs kruskal interview, shortest path tree vs mst, shortest path vs mst interview, disconnected graph mst, minimum spanning forest edge case, connect all nodes minimum cost, connect all cities minimum cost, connect all points minimum cost, minimum cost to connect all nodes, minimum cost to connect all points, network wiring minimum cost, cycle-free minimum cost, prim vs kruskal, mst algorithm choice, which mst algorithm, dense graph mst, sparse graph mst, prim adjacency list heap, prim heap implementation, lazy prim, eager prim, decrease key prim, prim adjacency matrix dense graph, prim o(v^2), complete graph prim, cost matrix mst, minimum spanning forest, shortest path vs mst, union find mst, union find, 최소 신장 트리 면접 질문, 최소 신장 포레스트, MST와 최단 경로 차이, 끊어진 그래프 MST, 프림 인접 리스트 힙, 프림 우선순위 큐 구현, 프림 인접 행렬, 프림 O(V^2), 완전 그래프 MST, topological sort, network flow, max flow, max throughput, throughput maximization, throughput optimization, bottleneck capacity, bottleneck edge, bottleneck link, bandwidth bottleneck, min cut, minimum cut, cut capacity, flow cut theorem, bipartite matching, maximum matching, assignment problem, job assignment, worker task assignment, matching to flow reduction, weighted matching, weighted bipartite matching, minimum cost bipartite matching, cost-aware matching, cost aware matching, minimum assignment, minimum cost assignment, cost matrix assignment, cheapest assignment, cheapest matching, optimal assignment, min-cost max-flow, mcmf, minimum cost flow, transportation problem, transport problem, minimum cost transportation, shipping cost minimization, supply demand allocation, hungarian algorithm, hungarian, kuhn munkres, linear assignment, linear sum assignment, minimum weight perfect matching, 1:1 weighted matching, bitmask dp, assignment dp, small-n assignment, small-n exact assignment, one worker one job small n, cost matrix small n, n <= 20 assignment, popcount assignment, subset-state optimization, held-karp, tsp dp, A*, A star, A-star, a-star, astar, graph decision tree, dependency ordering, string algorithm, 병목, 네트워크 병목, 최소 컷, 최소 절단, 절단 용량, 최대 처리량

## 빠른 탐색

이 `README`는 알고리즘 기본 primer와 pattern / comparison deep dive가 함께 있는 **navigator 문서**다.

- 복잡도와 탐색 기본기를 먼저 잡고 싶다면:
  - [시간복잡도와 공간복잡도](basic.md#시간복잡도와-공간복잡도)
  - [상각 분석과 복잡도 함정](amortized-analysis-pitfalls.md)
  - [이분 탐색 패턴](binary-search-patterns.md)
  - [DFS와 BFS](basic.md#dfs와-bfs) (BFS shortest-path primer, unweighted shortest-path handoff)
  - [백트래킹](basic.md#백트래킹-backtracking)
  - [동적 계획법](basic.md#동적-계획법-dynamic-programming)
- 그래프 문제에서 "무슨 알고리즘을 골라야 하지?"가 먼저라면:
  - [그래프 문제 Decision Router](graph.md#그래프-문제-decision-router) (path vs tree vs order vs flow, bottleneck/min-cut handoff)
  - [그래프](graph.md)
  - [Shortest Path Router: Unweighted vs DAG vs Weighted](graph.md#shortest-path-router-unweighted-vs-dag-vs-weighted) (legacy graph primer router, same canonical single-source/all-pairs/negative-edge vocabulary as the comparison deep dive)
  - [Minimum Spanning Tree: Prim vs Kruskal](minimum-spanning-tree-prim-vs-kruskal.md)
  - [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md) (unweighted vs DAG vs weighted router, negative-edge/single-source/all-pairs query anchors, A* handoff)
  - [A* vs Dijkstra](a-star-vs-dijkstra.md) (goal-directed shortest path, A-star/astar alias, route-planning, maze-navigation, point-to-point shortest path, target-fixed routing)
  - [Sparse Graph Shortest Paths](sparse-graph-shortest-paths.md) (graph density phrasing, single-source weighted shortest path, route-planning to A* handoff, PQ Dijkstra, 0-1 BFS, 0/1 cost shortest path, Dial)
  - [위상 정렬 패턴](topological-sort-patterns.md)
  - [네트워크 플로우 직관](network-flow-intuition.md)
  - [분리 집합(Union Find)과 크루스칼(Kruskal) 알고리즘](graph.md#분리-집합Union-Find과-크루스칼Kruskal-알고리즘) (legacy primer section)
- `MST`, `minimum spanning tree`, `connect all nodes minimum cost`, `connect all points minimum cost`, `모든 정점을 최소 비용으로 연결`, `prim vs kruskal`, `shortest path vs mst`, `minimum spanning forest`처럼 전체 연결 비용, shortest-path와의 경계, disconnected graph 예외가 먼저 보이면:
  - [Minimum Spanning Tree: Prim vs Kruskal](minimum-spanning-tree-prim-vs-kruskal.md)
  - [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md)
  - [그래프 문제 Decision Router](graph.md#그래프-문제-decision-router)
  - [분리 집합(Union Find)과 크루스칼(Kruskal) 알고리즘](graph.md#분리-집합Union-Find과-크루스칼Kruskal-알고리즘)
- `prim adjacency list heap`, `lazy prim`, `decrease-key 없는 prim`, `priority queue duplicate edge`, `prim adjacency matrix`, `dense graph prim`, `prim O(V^2)`, `complete graph mst`처럼 Prim 구현 디테일이 먼저 보이면:
  - [Minimum Spanning Tree: Prim vs Kruskal](minimum-spanning-tree-prim-vs-kruskal.md) (Prim heap vs matrix follow-up note 포함)
  - [Heap Variants](../data-structure/heap-variants.md)
- `unweighted shortest path`, `bfs shortest path`, `최소 이동 횟수`, `미로 최단 경로`처럼 BFS alias가 먼저 보이면:
  - [DFS와 BFS](basic.md#dfs와-bfs) (BFS shortest-path primer, unweighted shortest-path handoff)
  - [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md)
- `0-1 BFS`, `zero one bfs`, `binary edge weight shortest path`, `0/1 cost shortest path`, `deque shortest path`, `shortest path with deque`, `teleport shortest path`, `portal shortest path`, `warp shortest path`, `무료/유료 간선 최단 경로`처럼 0/1 가중치 shortest-path phrasing이면:
  - [Sparse Graph Shortest Paths](sparse-graph-shortest-paths.md)
  - [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md)
  - [Deque Router Example Pack](../data-structure/deque-router-example-pack.md)
- `pathfinding`, `point-to-point shortest path`, `single-pair shortest path`, `route planning`, `route-planning`, `weighted route planning`, `minimum cost route between two nodes`, `maze navigation`, `maze-navigation`, `maze pathfinding`, `가중치 길찾기`, `두 정점 사이 최소 비용 경로`, `target-fixed shortest path`, `start-to-goal shortest path`, `source-to-target routing`, `A*`, `A-star`, `astar`처럼 목표 정점이 또렷하면:
  - [A* vs Dijkstra](a-star-vs-dijkstra.md)
  - [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md)
  - [Sparse Graph Shortest Paths](sparse-graph-shortest-paths.md)
- `sparse graph shortest path`, `dense graph shortest path`, `adjacency list shortest path`, `adjacency matrix shortest path`, `graph density shortest path`, `single-source shortest path on sparse graph`처럼 그래프 밀도/표현이 먼저 보이면:
  - [Weighted Shortest Path Density Router: Sparse vs Dense](graph.md#weighted-shortest-path-density-router-sparse-vs-dense)
  - [Sparse Graph Shortest Paths](sparse-graph-shortest-paths.md)
  - [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md)
- `음수 간선 있는데 뭐 써야 하지`, `single-source shortest path`, `start-to-all routing`, `한 시작점에서 모든 정점 최단 거리`, `모든 정점 쌍 최단 거리`처럼 shortest-path 질문 자체가 query 형태로 들어오면:
  - [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md)
  - [A* vs Dijkstra](a-star-vs-dijkstra.md)
  - [Sparse Graph Shortest Paths](sparse-graph-shortest-paths.md)
- `dag dp`, `dag shortest path`, `critical path`, `earliest finish time`, `의존성 그래프 최소 비용`처럼 DAG 위에서 값을 누적하거나 최적화해야 한다면:
  - [Topological DP](topological-dp.md)
  - [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md)
  - [위상 정렬 패턴](topological-sort-patterns.md)
- `bipartite matching`, `job assignment`, `최대 몇 쌍 배정`처럼 matching 질문을 flow로 옮겨야 한다면:
  - [네트워크 플로우 직관](network-flow-intuition.md)
  - [Min-Cost Max-Flow Intuition](min-cost-max-flow-intuition.md)
  - [Bitmask DP](bitmask-dp.md)
- `small-n assignment`, `assignment dp`, `cost matrix small n`, `one worker one job n <= 20`, `dp[mask][last]`, `visit all nodes once`처럼 상태 압축/순서 의존성이 먼저 보이면:
  - [Bitmask DP](bitmask-dp.md)
  - [Hungarian Algorithm Intuition](hungarian-algorithm-intuition.md)
  - [Min-Cost Max-Flow Intuition](min-cost-max-flow-intuition.md)
- `optimal assignment`, `hungarian algorithm`, `linear assignment`, `minimum weight perfect matching`, `1:1 weighted matching`처럼 exact cost matrix 배정이라면:
  - [Hungarian Algorithm Intuition](hungarian-algorithm-intuition.md)
  - [Bitmask DP](bitmask-dp.md)
  - [Min-Cost Max-Flow Intuition](min-cost-max-flow-intuition.md)
- `weighted matching`, `cost matrix assignment`, `minimum assignment`, `cheapest matching`, `cost-aware matching`, `배정 비용 최소화`처럼 cost objective가 붙은 배정인데 공급/수요/capacity까지 열려 있다면:
  - [Min-Cost Max-Flow Intuition](min-cost-max-flow-intuition.md)
  - [Hungarian Algorithm Intuition](hungarian-algorithm-intuition.md)
  - [Bitmask DP](bitmask-dp.md)
- `transportation problem`, `transport problem`, `minimum cost transportation`, `shipping cost minimization`, `supply-demand allocation`, `운송 문제`처럼 여러 공급지와 수요지를 가장 싸게 연결해야 한다면:
  - [Min-Cost Max-Flow Intuition](min-cost-max-flow-intuition.md)
  - [네트워크 플로우 직관](network-flow-intuition.md)
  - [Hungarian Algorithm Intuition](hungarian-algorithm-intuition.md)
- `maximum throughput`, `bandwidth bottleneck`, `min cut`, `minimum cut`, `cut capacity`, `최소 절단`, `어디가 병목인가`처럼 처리량/절단 관점이 먼저라면:
  - [그래프 문제 Decision Router](graph.md#그래프-문제-decision-router)
  - [네트워크 플로우 직관](network-flow-intuition.md)
  - [Min-Cost Max-Flow Intuition](min-cost-max-flow-intuition.md)
- 그래프에서 "경로 vs 트리 vs 순서 vs 용량"을 구분하고 싶다면:
  - [그래프 문제 Decision Router](graph.md#그래프-문제-decision-router)
  - [Minimum Spanning Tree: Prim vs Kruskal](minimum-spanning-tree-prim-vs-kruskal.md)
  - [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md)
  - [위상 정렬 패턴](topological-sort-patterns.md)
  - [네트워크 플로우 직관](network-flow-intuition.md)
- `greedy choice property`, `optimal substructure`, `탐욕 선택 속성`, `최적 부분 구조`, `exchange argument`, `언제 greedy가 맞나`, `탐욕이 왜 실패하나`처럼 generic greedy 판단이 먼저라면:
  - [탐욕 / Greedy 알고리즘 개요](greedy.md)
  - [구간 / Interval Greedy 패턴](interval-greedy-patterns.md)
  - [동적 계획법](basic.md#동적-계획법-dynamic-programming)
- 패턴형 deep dive로 바로 들어가려면:
  - [상각 분석과 복잡도 함정](amortized-analysis-pitfalls.md)
  - [이분 탐색 패턴](binary-search-patterns.md)
  - [Longest Increasing Subsequence Patterns](longest-increasing-subsequence-patterns.md)
  - [슬라이딩 윈도우 패턴](sliding-window-patterns.md)
  - [두 포인터 (two-pointer)](two-pointer.md)
  - [구간 / Interval Greedy 패턴](interval-greedy-patterns.md)
  - [Sweep Line Overlap Counting](sweep-line-overlap-counting.md)
- `activity selection`, `erase overlap intervals`, `minimum arrows`, `겹치지 않게 최대 몇 개`, `예약 충돌 제거`처럼 어떤 interval을 고르거나 제거해야 한다면:
  - [구간 / Interval Greedy 패턴](interval-greedy-patterns.md)
- `merge intervals`, `insert interval`, `구간 병합`, `겹치는 구간 합치기`처럼 정렬 후 한 번 훑어 merge하면 되는 batch 문제라면:
  - [정렬 알고리즘](sort.md#정렬-전처리로-구간-문제-읽기)
  - [구간 / Interval Greedy 패턴](interval-greedy-patterns.md)
  - [Disjoint Interval Set](../data-structure/disjoint-interval-set.md)
- `meeting rooms II`, `minimum meeting rooms`, `강의실 배정`, `max concurrency`, `calendar overlap count`, `peak concurrent users`처럼 동시 몇 개가 겹치는지가 핵심이라면:
  - [Sweep Line Overlap Counting](sweep-line-overlap-counting.md)
  - [Heap Variants](../data-structure/heap-variants.md)
- `meeting rooms I`, `meeting rooms II`, `my calendar`, `hotel booking possible`가 한 덩어리로 헷갈린다면:
  - [Sweep Line Overlap Counting](sweep-line-overlap-counting.md)
  - [구간 / Interval Greedy 패턴](interval-greedy-patterns.md)
  - [Interval Tree](../data-structure/interval-tree.md)
- `meeting`, `schedule`, `reservation`, `calendar overlap`이 보이는데 연속 인덱스 스캔인지 일정 레코드 겹침인지 헷갈린다면:
  - [구간 / Interval Greedy 패턴](interval-greedy-patterns.md)
  - [Sweep Line Overlap Counting](sweep-line-overlap-counting.md)
  - [슬라이딩 윈도우 패턴](sliding-window-patterns.md)
- `calendar booking`, `online reservation insert`, `insert interval then query overlap`, `실시간 예약 충돌 검사`처럼 새 interval이 계속 들어오고 매번 질의해야 한다면:
  - [Interval Tree](../data-structure/interval-tree.md)
  - [Disjoint Interval Set](../data-structure/disjoint-interval-set.md)
- `substring`, `subarray`, `최근 k개`, `minimum window`처럼 연속 구간 스캔 문제라면:
  - [슬라이딩 윈도우 패턴](sliding-window-patterns.md)
- `pair sum`, `two sum sorted`, `difference`, `palindrome`, `left/right`, `container with most water`처럼 두 위치 관계를 줄이는 scan이라면:
  - [두 포인터 (two-pointer)](two-pointer.md)
  - [슬라이딩 윈도우 패턴](sliding-window-patterns.md)
  - [Longest Increasing Subsequence Patterns](longest-increasing-subsequence-patterns.md)
- `monotonic predicate`와 `contiguous window`를 먼저 구분하고 싶다면:
  - [이분 탐색 패턴](binary-search-patterns.md)
  - [슬라이딩 윈도우 패턴](sliding-window-patterns.md)
  - [두 포인터 (two-pointer)](two-pointer.md)
- `sliding window maximum`, `window minimum`, `최근 k개 최대값`처럼 deque 상태가 필요하다면:
  - [슬라이딩 윈도우 패턴](sliding-window-patterns.md)
  - [Monotonic Queue / Stack](../data-structure/monotonic-queue-and-stack.md)
  - [Deque Router Example Pack](../data-structure/deque-router-example-pack.md)
- `monotonic queue proof`, `sliding window maximum proof`, `왜 뒤에서 pop`, `단조 덱 O(n)`처럼 증명/불변식이 먼저라면:
  - [Monotone Deque Proof Intuition](monotone-deque-proof-intuition.md)
  - [Monotonic Queue / Stack](../data-structure/monotonic-queue-and-stack.md)
  - [슬라이딩 윈도우 패턴](sliding-window-patterns.md)
- `subsequence`와 `contiguous subarray/substring`가 자꾸 헷갈린다면:
  - [Longest Increasing Subsequence Patterns](longest-increasing-subsequence-patterns.md)
  - [슬라이딩 윈도우 패턴](sliding-window-patterns.md)
  - [이분 탐색 패턴](binary-search-patterns.md)
- 비교 / 선택형 문서로 바로 들어가려면:
  - [Minimum Spanning Tree: Prim vs Kruskal](minimum-spanning-tree-prim-vs-kruskal.md)
  - [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md)
  - [A* vs Dijkstra](a-star-vs-dijkstra.md)
  - [Sparse Graph Shortest Paths](sparse-graph-shortest-paths.md)
  - [네트워크 플로우 직관](network-flow-intuition.md)
  - [정렬 알고리즘](sort.md)

## 🟢 Beginner 입문 문서

처음 알고리즘을 공부하는 경우 아래 5편을 순서대로 읽는 것을 권장한다.

- [시간복잡도 입문](time-complexity-intro.md) — Big-O 감각 잡기, 루프 분석
- [DFS와 BFS 입문](dfs-bfs-intro.md) — 그래프/트리 탐색 기초, 최단 경로 차이
- [정렬 알고리즘 입문](sort-intro.md) — 버블/삽입/병합/퀵, 안정 정렬 의미
- [이분 탐색 입문](binary-search-intro.md) — O(log n) 탐색, Lower/Upper Bound 패턴
- [동적 계획법 입문](dp-intro.md) — 메모이제이션, Bottom-up DP, 점화식
- [재귀 입문](recursion-intro.md) — base case, 콜 스택, 재귀 vs 반복문
- [그리디 알고리즘 입문](greedy-intro.md) — 탐욕 선택 속성, 거스름돈 예시, DP와 비교
- [두 포인터 입문](two-pointer-intro.md) — 양 끝 좁히기, O(n) 쌍 탐색, 슬라이딩 윈도우 차이
- [완전 탐색 입문](brute-force-intro.md) — 순열/조합/부분집합, 경우의 수 계산
- [백트래킹 입문](backtracking-intro.md) — 가지치기, N-Queen, visited 해제 패턴

## 기본 primer

## 알고리즘 기본 [▶︎ 🗒](basic.md)

- [시간복잡도와 공간복잡도](basic.md#시간복잡도와-공간복잡도)
- [상각 분석과 복잡도 함정](amortized-analysis-pitfalls.md)
- [이분 탐색 패턴](binary-search-patterns.md)
- 완전 탐색 알고리즘 (Brute Force)
- [DFS와 BFS](basic.md#dfs와-bfs) (BFS shortest-path primer, unweighted shortest-path handoff)
  - [순열, 조합, 부분집합](basic.md#순열-조합-부분집합)
- [백트래킹 (Backtracking)](basic.md#백트래킹-backtracking)
- [분할 정복법 (Divide and Conquer)](basic.md#분할-정복법-divide-and-conquer)
- [탐욕 알고리즘 (Greedy)](basic.md#탐욕-알고리즘-greedy)
- [탐욕 / Greedy 알고리즘 개요](greedy.md) (generic greedy landing page, proof vocabulary, interval/sweep/DP handoff)
- [동적 계획법 (Dynamic Programming)](basic.md#동적-계획법-dynamic-programming)

## 패턴 / 비교 catalog

## 알고리즘 응용

- [정렬 알고리즘](sort.md) (stable / unstable, comparison / non-comparison, preprocessing, interval merge vs scheduling sort key)
- [그래프](graph.md)
  - [그래프 문제 Decision Router](graph.md#그래프-문제-decision-router)
  - [Shortest Path Router: Unweighted vs DAG vs Weighted](graph.md#shortest-path-router-unweighted-vs-dag-vs-weighted) (legacy graph primer router, BFS/DAG/weighted split plus canonical single-source/all-pairs/negative-edge phrasing)
  - [Weighted Shortest Path Density Router: Sparse vs Dense](graph.md#weighted-shortest-path-density-router-sparse-vs-dense) (graph density phrasing, adjacency list vs matrix, sparse-vs-dense shortest-path handoff)
  - [Minimum Spanning Tree: Prim vs Kruskal](minimum-spanning-tree-prim-vs-kruskal.md) (generic MST landing page, Prim/Kruskal selection, Prim heap vs matrix implementation follow-up)
  - [최단 경로 알고리즘](graph.md#최단-경로-알고리즘) (다익스트라, 벨만-포드, 플로이드-워셜 legacy notes)
  - [분리 집합(Union Find)과 크루스칼(Kruskal) 알고리즘](graph.md#분리-집합Union-Find과-크루스칼Kruskal-알고리즘)
  - [위상 정렬 패턴](topological-sort-patterns.md)
  - [Topological DP](topological-dp.md) (DAG shortest/longest path, dependency accumulation, critical path scheduling)
- [Longest Increasing Subsequence Patterns](longest-increasing-subsequence-patterns.md) (subsequence optimization, tails + lower_bound, subsequence vs subarray)
- [두 포인터 (two-pointer)](two-pointer.md) (pair relation scan, same-direction / opposite-direction, contiguous index scan, schedule interval boundary)
- [슬라이딩 윈도우 패턴](sliding-window-patterns.md) (substring/subarray, fixed or variable window, contiguous index interval, not schedule overlap)
- [Monotonic Queue / Stack](../data-structure/monotonic-queue-and-stack.md) (sliding window maximum/minimum, deque-based window state, contiguous index extrema)
- [Deque Router Example Pack](../data-structure/deque-router-example-pack.md) (plain deque vs monotonic deque vs 0-1 BFS quick split)
- [Monotone Deque Proof Intuition](monotone-deque-proof-intuition.md) (monotonic queue correctness, dominated candidate proof, amortized O(n), contiguous window proof, why back-pop is safe)
- [구간 / Interval Greedy 패턴](interval-greedy-patterns.md) (activity selection, erase overlap intervals, minimum arrows, end-time sort, meeting rooms I boundary)
- [Sweep Line Overlap Counting](sweep-line-overlap-counting.md) (meeting rooms II, minimum meeting rooms, railway platform, hotel booking possible, event sweep, heap boundary)
- [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md) (unweighted vs DAG vs weighted router, negative-edge/single-source/all-pairs query anchors, A* handoff)
- [Topological DP](topological-dp.md) (DAG path optimization, topological relaxation, earliest finish time, critical path)
- [A* vs Dijkstra](a-star-vs-dijkstra.md) (goal-directed shortest path, A-star/astar alias, route-planning, maze-navigation, weighted point-to-point routing, target-fixed/source-to-target routing)
- [Sparse Graph Shortest Paths](sparse-graph-shortest-paths.md) (graph density phrasing, single-source weighted shortest path, route-planning to A* handoff, PQ Dijkstra, 0-1 BFS, 0/1 cost, deque/teleport-style shortest path, Dial)
- [Bitmask DP](bitmask-dp.md) (subset-state optimization, popcount-based small-n assignment, cost-matrix/TSP boundary)
- [Hungarian Algorithm Intuition](hungarian-algorithm-intuition.md) (optimal assignment, linear assignment, Kuhn-Munkres, 1:1 weighted matching)
- [네트워크 플로우 직관](network-flow-intuition.md) (bipartite matching, assignment reduction, max throughput, bottleneck/min-cut/cut-capacity reading)
- [Min-Cost Max-Flow Intuition](min-cost-max-flow-intuition.md) (costed assignment, cheapest matching, transportation problem, supply-demand allocation)
- [문자열 처리 알고리즘](string.md)
  - [KMP 알고리즘](string.md#문자열-패턴-매칭)

---

## 질의응답

<!-- 탐색 알고리즘 -->

<details>
<summary>DFS와 BFS의 장단점에 대해 각각 설명해 주세요.</summary>
<p>

1. BFS 장점
   1. 너비를 우선으로 탐색하기 때문에 답이 되는 경로가 여러개인 경우에도 최단경로임을 보장합니다.
   2. 최단 경로가 존재한다면, 어느 한 경로가 무한히 깊어진다 해도 최단경로를 반드시 찾을 수 있습니다.
   3. 노드의 수가 적고 깊이가 얕은 해가 존재할 때 유리합니다.
2. BFS 단점
   1. 재귀 호출을 사용하는 DFS와는 달리 큐를 이용해 다음에 탐색할 노드들을 저장합니다. 이 때, 노드의 수가 많을 수록 필요없는 노드들까지 저장해야하기 때문에 더 큰 저장공간이 필요합니다.
   2. 노드의 수가 늘어나면 탐색해야하는 노드 또한 많아지기 때문에 비현실적입니다.
3. DFS 장점
   1. BFS에 비해 저장공간의 필요성이 적고 백트래킹을 해야하는 노드들만 저장해주면 됩니다.
   2. 찾아야하는 노드가 깊은 단계에 있을 수록, 그 노드가 좌측에 있을 수록 BFS보다 유리합니다.
4. DFS 단점
   1. 답이 아닌 경로가 매우 깊다면, 그 경로에 깊이 빠질 우려가 있습니다.
   2. 내가 지금까지 찾은 최단경로가 끝까지 탐색 했을 때의 최단경로가 된다는 보장이 없습니다.

</p>
</details>

---

<!-- 정렬 알고리즘 -->

<details>
<summary>라이브러리 없이 정렬을 구현하려고 할 때 어떤 정렬 방식을 사용해 구현할 것이고 왜 그렇게 생각하는지 성능 측면에서 얘기를 해주세요.</summary>
<p>

(예시 답안)
퀵소트로 구현할 것입니다. 퀵소트는 average case에서 nlgn의 시간복잡도를 가지며 공간복잡도 측면에서도 제자리 정렬이기 때문에 좋은 성능을 가집니다. worst case의 경우 n^2의 시간복잡도를 가지지만 worst case가 나타날 경우는 확률적으로 매우 낮습니다. (자료가 n개일 때 오름차순 또는 내림차순 -> 2/n!)

</p>
</details>

<details>
<summary>퀵소트에서 최악의 경우 시간복잡도를 개선시킬 수 있는 방법이 있을까요?</summary>
<p>

피벗의 위치를 다르게 설정함으로써 시간복잡도를 개선시킬 수 있습니다. 일정한 위치에 대해서만(ex. 첫번째 element) 피벗을 설정하는 것보다 첫번째, 마지막 element 중 무작위로 선택한다거나 첫번째, 가운데, 마지막 element 중 중간값을 계산하여 피벗을 설정했을 때 시간복잡도를 더 개선시킬 수 있습니다.

</p>
</details>

<details>
<summary>머지소트의 분할 정복 과정에 대해 단계별로 설명해주세요.</summary>
<p>

- Divide : 초기 배열을 2개의 배열로 분할
- Conquer : 각 부분 배열을 정렬
- Combine : 부분 배열을 하나의 배열로 결합

</p>
</details>

---

<!-- MST -->

<details>
<summary>MST(Minimum Spanning Tree)를 구하는 알고리즘에 대해 설명하고, 각각 어떤 상황에서 사용하는 것이 적절한지 설명해 주세요.</summary>
<p>

> 정점의 개수 : V, 간선의 개수 : E

먼저 MST는 "모든 정점을 사이클 없이 연결할 때 전체 간선 가중치 합을 최소화하는 트리"를 구하는 문제입니다. 그래서 `한 시작점에서 각 정점까지의 최단 거리`를 구하는 shortest path 문제와는 목적 함수가 다릅니다. 그래프가 disconnected라면 MST 하나는 존재하지 않고, 각 연결 성분별 최소 트리를 구한 **minimum spanning forest**로 해석해야 합니다.

대표 알고리즘은 Prim과 Kruskal입니다.

- Prim: 현재까지 만든 트리에서 바깥으로 나가는 간선 중 가장 싼 간선을 계속 붙이는 frontier 확장 방식입니다. 인접 리스트/행렬처럼 adjacency 중심 표현과 잘 맞고, 우선순위 큐를 쓰면 보통 `O(E log V)`로 설명합니다. dense graph에서는 `O(V^2)` 형태 구현도 자주 씁니다.
- Kruskal: 간선을 가중치 오름차순으로 정렬해 사이클이 생기지 않는 간선만 채택하는 방식입니다. flat edge list 입력, sparse graph, Union-Find 조합과 잘 맞고 정렬 때문에 보통 `O(E log E)`입니다. disconnected 그래프에서는 끝까지 돌리면 minimum spanning forest가 남습니다.

정리하면 `모든 도시를 가장 싸게 모두 잇기`면 MST이고, `1번 도시에서 나머지 도시까지 가장 싸게 가기`면 shortest path입니다. 입력 표현이 adjacency 중심이면 Prim, 간선 목록 정렬과 cycle check가 중심이면 Kruskal이 더 자연스럽습니다.

더 자세한 비교는 [Minimum Spanning Tree: Prim vs Kruskal](minimum-spanning-tree-prim-vs-kruskal.md), shortest-path와의 구분은 [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md)를 같이 보면 됩니다.

</p>
</details>

<details>
<summary>Minimum Spanning Tree를 찾기 위한 프림 알고리즘의 동작원리 또는 특징에 대해 설명해주세요</summary>
<p>

1. 시작 정점 하나를 현재 트리 집합으로 잡고, 그 집합에서 바깥으로 나가는 간선 중 최소 비용 간선을 선택해 트리를 확장합니다.
2. 즉 Prim은 "현재 트리의 frontier를 넓혀 가는 방식"이지, 시작점에서 다른 정점까지의 거리를 갱신하는 shortest path 알고리즘이 아닙니다.
3. 보통 `visited + priority queue`로 구현하며, 인접 리스트 기준으로는 `O(E log V)`로 설명합니다. dense graph에서는 인접 행렬 기반 `O(V^2)` 구현도 자주 씁니다.
4. 연결 그래프라면 간선을 `N-1`개 채우면 MST가 완성됩니다. 그래프가 disconnected라면 한 번의 실행으로 전체 MST 하나를 만들 수 없고, 각 컴포넌트마다 다시 시작해 minimum spanning forest를 만들어야 합니다.

</p>
</details>

<details>
<summary>Minimum Spanning Tree를 찾기 위한 크루스칼 알고리즘의 동작원리 또는 특징에 대해 설명해주세요</summary>
<p>

1. 그래프의 모든 간선을 가중치 오름차순으로 정렬한 뒤, 가장 싼 간선부터 순서대로 검토합니다.
2. 각 간선을 추가했을 때 사이클이 생기지 않으면 채택하고, 생기면 버립니다. 이 cycle check를 빠르게 하려고 보통 Union-Find를 씁니다.
3. Kruskal은 특정 시작 정점에서 거리를 줄이는 알고리즘이 아니라, 전역적으로 가장 싼 간선을 골라 전체 연결 비용을 최소화하는 MST 알고리즘입니다.
4. 간선을 `N-1`개 선택하면 연결 그래프의 MST가 완성됩니다. 그래프가 disconnected라면 끝까지 훑은 결과는 실패가 아니라 각 연결 성분의 최소 트리를 모아 둔 minimum spanning forest입니다.
5. 간선 목록이 이미 edge list로 주어지거나 sparse graph에서 cycle 여부 판단이 핵심일 때 특히 자연스럽고, 정렬 때문에 시간 복잡도는 보통 `O(E log E)`로 설명합니다.

</p>
</details>

---

<!-- 최단 경로 -->

<details>
<summary>최단경로를 구하기 위한 알고리즘을 두 가지 이상 말하고 어떤 차이점이 있는지 설명해주세요.</summary>
<p>

- 다익스트라 : 하나의 시작 정점 ~ 모든 다른 정점까지의 최단 경로를 구한다.
- 벨만포드 : 하나의 시작 정점 ~ 모든 다른 정점까지의 최단 경로를 구한다. + 가중치가 음수일 때도 사용이 가능하다. (음의 사이클 검사 가능)
- 플로이드 와샬 : 모든 정점 ~ 모든 정점까지의 최단 경로를 구한다.

</p>
</details>

<details>
<summary>다익스트라 알고리즘 동작원리 또는 특징을 시간복잡도와 연관지어 설명해주세요.</summary>
<p>

(방법 1)

1. 출발 노드 S에서 모든 노드들까지의 최단 거리를 저장하는 배열 D를 초기화한다.
2. 방문하지 않은 노드 중에서 최단 거리가 가장 짧은 노드를 선택한다. (D 배열 검사)
3. 선택한 노드를 거쳐 다른 노드로 가는 비용을 계산하여 최단 거리 배열 D를 갱신한다.
4. 모든 노드를 방문할 때까지 3, 4 과정을 반복한다.
5. 노드의 개수를 V라고 할 때, 총 V\*V번 연산이 필요하므로 `O(V^2)`의 시간복잡도를 가진다.

(방법 2 - 힙/우선순위큐 사용)

1. 출발 노드 S에 대하여 D 배열을 초기화할 때 D[S] = 0을 해준다. 이와 동시에 힙에 노드 정보(번호, 거리 : [S, 0])를 넣어준다.
2. 힙에서 맨 위에 있는 노드 I를 꺼낸다.
3. 만일 꺼낸 노드 I의 거리 정보가 현재 D[I]보다 크다면 이미 방문한 노드일 것이므로 무시한다.
4. I를 대상으로 다익스트라 알고리즘을 수행하는데, D 배열이 갱신될 경우 그 노드 정보를 힙에 넣는다.
5. 힙에 노드가 없을 때까지 2-4 과정을 반복한다.
6. 노드의 개수를 V, 간선의 개수를 E라고 할 때 시간 복잡도는 `O(ElogV)` 이다.

</p>
</details>

<details>
<summary>다익스트라 알고리즘에서 힙(우선순위큐)을 사용할 경우 어떤 점에서 시간복잡도가 개선이 되나요?</summary>
<p>

다익스트라 알고리즘에서 방문하지 않은 노드 중 최단 거리가 가장 짧은 노드를 선택하는 과정이 있는데, 이 과정에서 O(`노드의 개수`)만큼의 비용이 발생하게 됩니다. 힙(우선순위큐)을 사용할 경우 그 비용을 O(`log{힙에 저장한 노드의 개수}`)로 줄일 수 있습니다.

</p>
</details>

<details>
<summary>벨만포드 알고리즘 동작원리 또는 특징을 시간복잡도와 연관지어 설명해주세요.</summary>
<p>

1. 음의 가중치를 가지는 간선도 가능하므로, 음의 사이클의 존재 여부를 따져야 한다.
2. 최단 거리를 구하기 위해서 V - 1번 E개의 모든 간선을 확인한다.
3. 음의 사이클 존재 여부를 확인하기 위해서 한 번 더 (V번째) E개의 간선을 확인한다.
4. 이 때 거리 배열이 갱신되었다면, 그래프 G는 음의 사이클을 가진다.
5. 따라서 총 V x E 번 연산하므로 O(VE)의 시간복잡도를 가진다.

</p>
</details>

<details>
<summary>플로이드 와샬 알고리즘 동작원리 또는 특징을 시간복잡도와 연관지어 설명해주세요.</summary>
<p>

1. 사이클이 없다면 음수 가중치를 가져도 적용 가능하다.
2. 동적 계획법(Dynamic Programming)으로 접근한다.
3. 모든 가능한 경유지에 대해서 모든 정점 -> 모든 정점으로 가는 최단 거리를 확인하므로 연산 횟수는 V^3이고, 따라서 시간복잡도는 O(V^3)

</p>
</details>

---

<!-- 문자열 -->

<details>
<summary> KMP 알고리즘에 대해 설명해주세요. </summary>
<p>
  
Kunth, Morris, Prett이 만든 알고리즘이라서 각 이름의 앞자리를 따서 KMP라고 지어졌습니다. 문자열이 불일치할 때 그 다음 문자부터 다시 탐색을 시작하는 것이 아니라 지금까지 일치했던 정보들을 버리지 말고 재사용 함으로써 몇칸 정도는 건너 뛰어서 탐색하자는 아이디어에서 알고리즘이 탄생했습니다. 접두사와 접미사 정보를 가지고 문자열을 점프해가며 탐색하는데, Naive한 문자열 탐색 알고리즘이 O(NM)의 시간복잡도를 갖는 반면에 KMP알고리즘은 O(N+M)의 시간복잡도를 갖습니다.

</p>
</details>

<details>
<summary>라빈 카프 알고리즘에 대해 설명해주세요.</summary>
<p>
  
문자열의 해시함수값을 이용합니다. 탐색 대상 문자열의 길이를 M이라고 했을 때 글을 M칸씩, 한칸 한칸 옮겨가며 부분 문자열을 떼어내고 해시함수값을 구하여 탐색 문자열의 해시함수값과 비교합니다. 해시함수값 충돌이 없다는 가정하에 글의 길이를 N이라고 하면 O(N-M)의 시간복잡도를 갖습니다.

</p>
</details>

<details>
<summary>라빈 카프 알고리즘이 KMP보다 빠른가?</summary>
<p>
  
사실상 그렇지 않습니다. 탐색 문자열의 길이가 길어질 수록 해시함수값에 충돌이 생길 확률이 높습니다. 따라서 해시함수값이 일치한다고 무조건 문자가 일치한다고 보장할 수 없기 때문에 해시함수값이 일치했을 때 문자열을 직접 비교하는 2차적인 검증이 필요합니다. 따라서 평균적으로 라빈 카프 또한 O(N+M)의 시간복잡도가 요구됩니다.

</p>
</details>

<details>
<summary>자료구조의 한 종류인 트라이를 설명해주세요.</summary>
<p>
  
트라이는 문자열을 저장하고 효율적으로 탐색하기 위한 트리 형태의 자료구조이다. 기본적으로 k진트리 구조를 띠고 어떤 문자열 집합 S와 문자열 A가 있다고 할 때 A가 S안에 존재하는지 찾는데에 사용되는 자료구조이다.

</p>
</details>

<details>
<summary>트라이의 장점과 단점을 설명해주세요.</summary>
<p>
  
이분탐색은 탐색하는데에 있어 검색어의 최대 길이 M * 전체 데이터 N 중 O(M log N)을 사용하게 되는데 이에 반해 트라이는 문자열 탐색에서의 전체 데이터의 길이인 시간복잡도 O(N)을 가지게 되어 매우 효율적이다. 하지만 트라이의 단점은 공간 복잡도가 높다. 알파벳을 저장하는 형태라면 1 depth당 26개의 공간이 사용될 수 있다.

</p>
</details>

<details>
<summary>트라이 자료구조를 사용한 적이 있나요? 경험을 이야기해주세요.</summary>
<p>
  
모범 답안) 알고리즘을 공부하는 과정에서 트라이 자료구조를 이용하여 아호코라식 알고리즘을 작성하여 문제를 해결했던 경험이 있습니다. 아호코라식 알고리즘은 KMP에서 사용하는 Failure Function을 트라이로 확장시킨 알고리즘으로 문자열 탐색에 사용하였습니다.

</p>
</details>

---

<!-- 투포인터 -->
<details>
<summary> <strong>투포인터</strong>라는 알고리즘 문제 해결 전략이 있습니다. 어떤 알고리즘이고 주로 어떤 문제를 해결하는데 사용되나요?</summary>
<p>

배열을 가리키는 포인터 2개를 이용해서 포인터를 한칸 씩 움직이며 특정 구간 내에서 원하는 값을 얻을 때 사용합니다. 예를 들면 연속되는 배열의 구간 중 특정 조건을 만족하는 가장 짧은 구간을 구하는 문제에서 사용될 수 있습니다.

</p>
</details>
