# Connectivity Question Router

> 한 줄 요약: 그래프 질문은 먼저 `같은 컴포넌트인가`, `실제 경로 하나를 복원하나`, `최단 거리/최단 경로를 구하나`로 나누면 union-find, BFS/DFS, shortest-path 문서가 바로 갈린다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [자료구조 정리](./README.md)
> - [Union-Find Deep Dive](./union-find-deep-dive.md)
> - [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md)
> - [알고리즘 기본: DFS와 BFS](../algorithm/basic.md#dfs와-bfs)
> - [그래프 알고리즘](../algorithm/graph.md)
> - [Dijkstra, Bellman-Ford, Floyd-Warshall](../algorithm/dijkstra-bellman-ford-floyd-warshall.md)
> - [Sparse Graph Shortest Paths](../algorithm/sparse-graph-shortest-paths.md)
>
> retrieval-anchor-keywords: connectivity question router, graph connectivity router, same component vs path reconstruction vs shortest path, same-component question, same component query, connected yes no, component membership query, path reconstruction graph, actual path query, one valid path, bfs parent reconstruction, dfs parent reconstruction, shortest path query, minimum path cost, minimum number of edges, union find vs bfs vs dijkstra, path existence vs actual path vs minimum path, dijkstra predecessor reconstruction, predecessor array shortest path, 그래프 연결성 라우터, 같은 컴포넌트 질문, 연결 여부 질문, 경로 복원 질문, 실제 경로 하나, 최단 경로 질문, 연결 여부 vs 경로 복원 vs 최단 경로, 유니온 파인드 BFS 다익스트라 구분

## 먼저 질문을 번역하기

| 질문이 요구하는 답 | 먼저 갈 문서 | 왜 거기로 가는가 |
|---|---|---|
| `같은 컴포넌트인가?`, `same set`, `connected yes/no` | [Union-Find Deep Dive](./union-find-deep-dive.md) | 답의 모양이 `같다/아니다`면 컴포넌트 대표만 빠르게 비교하면 된다 |
| `이 그룹 크기는?`, `전체 컴포넌트 수는?`까지 같이 묻나 | [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md) | 같은 컴포넌트 질의에 `size`, `count` 메타데이터가 추가된 경우다 |
| `실제 경로 하나를 출력`, `방문 순서`, `도달 가능한 정점 목록` | [알고리즘 기본: DFS와 BFS](../algorithm/basic.md#dfs와-bfs) | 간선을 실제로 따라가며 `parent`나 방문 순서를 남겨야 한다 |
| `최단 거리`, `최소 이동 횟수`, `최소 비용`, `최단 경로` | [그래프 알고리즘](../algorithm/graph.md), [Dijkstra, Bellman-Ford, Floyd-Warshall](../algorithm/dijkstra-bellman-ford-floyd-warshall.md) | 연결만 확인하는 문제가 아니라 `minimum`을 최적화하는 shortest-path 문제다 |

가장 중요한 경계는 이것이다.

> `경로를 복원하라`와 `최단 경로를 복원하라`는 같은 말이 아니다.

- 앞 문장은 **유효한 경로 하나**면 된다. DFS/BFS로 parent를 남기면 충분하다.
- 뒤 문장은 먼저 **shortest-path 알고리즘**을 고르고, 그다음 predecessor를 저장해 경로를 복원해야 한다.

## 헷갈리는 문장을 바로 분해하면

| 문제 문장 | 실제로 묻는 것 | 먼저 떠올릴 도구 |
|---|---|---|
| `1과 9가 같은 컴포넌트인가?` | same-component yes/no | Union-Find |
| `1에서 9까지 갈 수 있으면 경로 하나를 출력하라` | actual path reconstruction | DFS/BFS + `parent` |
| `1에서 9까지 최소 간선 수와 그 경로를 구하라` | unweighted shortest path + reconstruction | BFS + `parent` |
| `1에서 9까지 최소 비용 경로를 구하라` | weighted shortest path + reconstruction | Dijkstra / Bellman-Ford + predecessor |
| `0/1 비용으로 1에서 9까지 가장 싸게 가라` | special weighted shortest path | [Sparse Graph Shortest Paths](../algorithm/sparse-graph-shortest-paths.md) |

## 꼭 기억할 경계

- Union-Find는 `같은 그룹인가?`를 빨리 답하지만 `1 -> 4 -> 7` 같은 실제 경로는 주지 않는다.
- DFS는 경로 하나를 빨리 찾을 수 있지만 그 경로가 shortest라는 보장은 없다.
- BFS는 **무가중치 그래프**에서는 shortest-path와 path reconstruction을 동시에 처리할 수 있다.
- weighted shortest path에서 경로까지 출력하려면 거리 배열만으로는 부족하고 predecessor 배열을 같이 저장해야 한다.

## 한 줄 정리

연결성 질문은 `yes/no`, `actual path`, `minimum path` 중 무엇을 요구하는지 먼저 고르면 된다.  
그 구분만 잡히면 union-find, BFS/DFS, shortest-path 문서가 거의 자동으로 갈린다.
