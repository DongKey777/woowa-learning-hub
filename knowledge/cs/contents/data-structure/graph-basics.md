# 그래프 기초 (Graph Basics)

> 한 줄 요약: 그래프는 노드(정점)와 간선(엣지)으로 이루어진 자료구조로, 트리와 달리 사이클과 방향성 개념이 추가되어 현실의 네트워크 관계를 표현하기에 가장 적합하다.

**난이도: 🟢 Beginner**

관련 문서:

- [기본 자료 구조](./basic.md)
- [트리 기초](./tree-basics.md)
- [자료구조 정리](./README.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- [그래프 관련 알고리즘](../algorithm/graph.md)
- [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md)
- [Connectivity Question Router](./connectivity-question-router.md)

retrieval-anchor-keywords: graph basics, 그래프 입문, 그래프가 뭐예요, vertex edge, directed undirected graph, adjacency list matrix, graph vs tree, 방향 무방향 그래프, 인접 리스트 행렬, 최소 이동 횟수, 최소 환승 횟수, path reconstruction graph, parent array path

## 핵심 개념

그래프는 **정점(Vertex, 노드)과 간선(Edge)의 집합**이다.
두 정점을 간선 하나로 연결하면, 그것이 곧 그래프다.

입문자가 자주 헷갈리는 포인트는 이것이다.

- 트리도 그래프의 일종이다. 단, 트리는 사이클이 없고 루트가 하나인 **특수한 그래프**다.
- 그래프는 사이클이 있을 수 있고, 간선에 방향과 가중치가 붙을 수 있다.

핵심 분류를 정리하면 이렇다.

- **방향 그래프(Directed)**: 간선에 방향이 있다. A → B는 있지만 B → A는 없을 수 있다.
- **무방향 그래프(Undirected)**: 간선에 방향이 없다. A — B이면 양쪽에서 이동 가능하다.
- **가중치 그래프(Weighted)**: 간선에 비용이 붙는다. 최단 경로 문제에서 쓴다.

## 한눈에 보기

```text
무방향 그래프:         방향 그래프:
  A — B              A → B
  |   |              ↑   ↓
  C — D              D ← C
```

| 표현 방식 | 장점 | 단점 |
|---|---|---|
| 인접 행렬 | 간선 존재 여부 O(1) | 공간 O(V²) |
| 인접 리스트 | 공간 O(V+E) | 간선 존재 여부 O(degree) |

코딩 테스트에서는 대부분 **인접 리스트**를 쓴다.

## 상세 분해

그래프를 코드로 다룰 때 세 가지를 먼저 결정한다.

- **표현 방법 선택**: 정점이 많고 간선이 적은 희소 그래프라면 인접 리스트, 정점이 적고 간선이 많은 밀집 그래프라면 인접 행렬이 유리하다.
- **탐색 방법 선택**: BFS(너비 우선)는 최단 경로(가중치 없는 그래프)를 찾을 때, DFS(깊이 우선)는 연결 여부·사이클 탐지에 쓴다.
- **사이클 탐지**: 방문 체크 배열(`visited[]`)만으로 기본 탐지가 가능하다. DFS 중 이미 방문한 노드를 다시 만나면 사이클이다.

## 경로 질문이 나오면 여기서 갈라진다

> 빠른 분기: `연결만 확인`인지, `아무 경로 하나`인지, `최단 경로`인지 먼저 자르면 다음 문서가 바로 정해진다.

| 질문 형태 | 지금 필요한 답 | 다음 문서 |
|---|---|---|
| `A에서 B로 연결돼?`, `갈 수 있어?` | yes/no 연결 여부 | [Connectivity Question Router](./connectivity-question-router.md) |
| `연결 요소가 몇 개야?`, `이 묶음은 몇 명이야?` | 그룹 수, 그룹 크기 메타데이터 | [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md) |
| `실제 경로 하나 보여줘` | 도달 가능한 경로 하나와 `parent` 복원 | [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md) |
| `가장 짧게 가는 길은?`, `최소 이동 횟수는?`, `최소 환승 횟수는?` | 무가중치면 BFS, 가중치가 있으면 Dijkstra 분기 | [BFS vs Dijkstra shortest path mini card](../algorithm/bfs-vs-dijkstra-shortest-path-mini-card.md) |

초보자 기준으로 제일 많이 섞이는 두 문장은 이것이다.

- `갈 수 있나?`는 연결 여부 질문이라 경로를 꼭 출력할 필요가 없다.
- `어떻게 가나?`와 `가장 짧게 어떻게 가나?`는 다른 질문이다. 앞은 경로 하나, 뒤는 shortest-path 문제다.
- `최소 이동 횟수`와 `최소 환승 횟수`는 표현만 다르고, 처음 읽을 때는 둘 다 `간선 수를 최소로 세는가?`로 번역하면 BFS 출발점이 같다.
- `BFS`라는 단어가 보여도 바로 shortest-path로 들어가지 말고, 먼저 [Connectivity Question Router](./connectivity-question-router.md)에서 `yes/no vs 경로 하나 vs minimum path`를 자르면 헷갈림이 크게 줄어든다.

## 실제 경로 복원 미니 예시

경로를 "찾기만" 하는 것과 "실제로 어떻게 갔는지 출력"하는 것은 다르다.
이때는 `parent[next] = now`를 같이 저장하면 된다.

```text
1 - 2 - 4
 \  |
   3

start = 1, target = 4
```

| 탐색 | parent에 남는 것 | 복원 결과 |
|---|---|---|
| BFS | `parent[2]=1`, `parent[3]=1`, `parent[4]=2` | `4 -> 2 -> 1`로 거꾸로 올라간 뒤 뒤집어서 `1 -> 2 -> 4` |
| DFS | 방문 순서에 따라 parent가 달라질 수 있음 | `경로 하나`는 복원되지만 보통 최단 경로는 아님 |

```text
cur = 4
path = []

4를 넣고 parent[4]=2로 이동
2를 넣고 parent[2]=1로 이동
1을 넣고 종료

뒤집으면 1 -> 2 -> 4
```

- 시작점은 `parent[start] = -1`처럼 비워 두면 역추적 종료가 쉽다.
- 무가중치 그래프에서 BFS parent 경로는 실제 경로이면서 최단 경로다.
- `parent[target]`가 끝까지 비어 있으면 도달하지 못한 것이다.

## 흔한 오해와 함정

- **오해 1: 그래프와 트리는 다른 개념이다.**
  트리는 사이클 없는 연결 무방향 그래프다. 트리는 그래프의 특수 케이스다.

- **오해 2: BFS는 항상 최단 경로를 찾는다.**
  간선 가중치가 모두 같을 때만 BFS가 최단 경로를 보장한다. 질문이 `갈 수 있나?` 수준이면 shortest-path가 아니라 연결성 분기이고, `가장 짧게`가 붙었을 때만 BFS vs Dijkstra를 고르면 된다. 먼저 [Connectivity Question Router](./connectivity-question-router.md)에서 질문 형태를 자르는 습관이 안전하다.

- **함정: 방문 배열 없이 그래프를 순회하면 무한 루프다.**
  사이클이 있는 그래프에서 `visited[]` 없이 BFS/DFS를 돌리면 같은 노드를 무한히 방문한다. 항상 방문 체크를 먼저 작성한다.

## 실무에서 쓰는 모습

**소셜 네트워크** — 사람을 정점, 친구 관계를 간선으로 표현한다. 친구 추천, 연결 거리 계산이 그래프 탐색이다.

**경로 탐색** — 지도 앱에서 도로를 간선, 교차점을 정점으로 표현한다. 최단 경로 알고리즘(다익스트라 등)이 가중치 그래프 위에서 동작한다.

## 더 깊이 가려면

- 연결 컴포넌트, 경로 재구성 질문은 [Connectivity Question Router](./connectivity-question-router.md)
- 트리와의 구조 차이를 더 보려면 [트리 기초](./tree-basics.md)

## 면접/시니어 질문 미리보기

1. **그래프를 표현하는 두 가지 방법의 차이는?**
   인접 행렬은 `O(V²)` 공간을 쓰지만 간선 조회가 O(1)이다. 인접 리스트는 `O(V+E)` 공간을 쓰며 희소 그래프에 유리하다. 코딩 테스트에서는 인접 리스트가 일반적이다.

2. **BFS와 DFS의 차이와 선택 기준은?**
   BFS는 큐를 쓰며 레벨 단위로 탐색해 최단 경로(균등 가중치)에 적합하다. DFS는 스택(또는 재귀)을 쓰며 연결 여부, 사이클 탐지, 위상 정렬에 적합하다.

3. **사이클 탐지를 어떻게 하나요?**
   무방향 그래프는 DFS 중 방문한 노드를 다시 만나면 사이클이다. 방향 그래프는 현재 DFS 경로에 있는 노드를 다시 만날 때만 사이클이므로 "현재 스택"을 별도로 관리한다.

## 한 줄 정리

그래프는 정점과 간선으로 현실의 연결 관계를 표현하며, 인접 리스트로 저장하고 BFS/DFS로 탐색하는 세 가지 조합이 코딩 테스트의 기본이다.
