# 그래프 기초 (Graph Basics)

> 한 줄 요약: 그래프는 `점`과 `점 사이 연결선`으로 관계를 그리는 자료구조이며, 초보자는 먼저 `무엇이 점이고 무엇이 연결인가`만 잡아도 BFS/DFS와 최단 경로 문서를 훨씬 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- [Connectivity Question Router](./connectivity-question-router.md)
- [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md)
- [자료구조 정리](./README.md)
- [그래프 관련 알고리즘](../algorithm/graph.md)

retrieval-anchor-keywords: graph basics, 그래프 입문, 그래프가 뭐예요, vertex edge, directed undirected graph, adjacency list matrix, graph vs tree, 방향 무방향 그래프, 인접 리스트 행렬, 처음 그래프, 그래프 헷갈림, 최소 이동 횟수, path reconstruction graph, parent array path, graph basics beginner

## 핵심 개념

그래프는 **정점(Vertex, 노드)과 간선(Edge)의 집합**이다.
두 정점을 간선 하나로 연결하면, 그것이 곧 그래프다.

처음에는 어려운 용어보다 아래 두 문장으로 잡아도 충분하다.

- `점`은 사람, 역, 페이지, 칸처럼 **상태 하나**다.
- `선`은 친구 관계, 이동 가능, 링크처럼 **상태 사이 연결 규칙**이다.

즉 그래프는 "무언가가 여러 개 있고, 그 사이를 오갈 수 있는 규칙이 있다"를 그리는 그림이라고 보면 된다.

처음 읽을 때는 아래 세 문장만 먼저 고정하면 된다.

- `그래프가 뭐예요?` -> 점과 선으로 관계를 그린다.
- `왜 미로도 그래프예요?` -> 칸을 점으로, 이동 가능을 선으로 보면 된다.
- `왜 queue가 나오죠?` -> 그래프 자체가 아니라 탐색 순서를 고르는 단계다.

## 처음 보는 분류

입문자가 자주 헷갈리는 포인트는 이것이다.

- 트리도 그래프의 일종이다. 단, 트리는 사이클이 없고 루트가 하나인 **특수한 그래프**다.
- 그래프는 사이클이 있을 수 있고, 간선에 방향과 가중치가 붙을 수 있다.

핵심 분류를 정리하면 이렇다.

- **방향 그래프(Directed)**: 간선에 방향이 있다. A → B는 있지만 B → A는 없을 수 있다.
- **무방향 그래프(Undirected)**: 간선에 방향이 없다. A — B이면 양쪽에서 이동 가능하다.
- **가중치 그래프(Weighted)**: 간선에 비용이 붙는다. 최단 경로 문제에서 쓴다.

처음 읽는 사람이 자주 묻는 질문을 한 줄로 자르면 아래처럼 정리된다.

| 지금 막힌 문장 | 먼저 잡을 생각 | 다음 문서 |
|---|---|---|
| `그래프가 뭐예요?` | 점과 연결 규칙을 그림으로 이해 | 이 문서 |
| `가까운 칸부터 왜 queue로 보나요?` | 탐색 순서 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `연결만 확인하면 되나요, 경로도 필요하나요?` | 답의 모양 분기 | [Connectivity Question Router](./connectivity-question-router.md) |

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

짧은 예시를 하나 붙이면 그래프 감각이 빨리 붙는다.

| 실제 장면 | 정점 | 간선 |
|---|---|---|
| 지하철 | 역 | 역 사이 이동 가능 |
| 친구 추천 | 사람 | 친구 관계 |
| 미로 | 칸 | 상하좌우 한 칸 이동 |

처음 헷갈리는 구조를 한 번에 자르면 아래 표가 가장 빠르다.

| 지금 떠오른 그림 | 먼저 보는 구조 | 초보자용 한 줄 메모 |
|---|---|---|
| `루트에서 자식으로 내려간다` | 트리 | 부모-자식 방향이 먼저 보인다 |
| `칸과 칸이 이어져 있다` | 그래프 | 격자도 칸을 정점으로 보면 그래프다 |
| `순서대로 줄 세운 값` | 배열/리스트 | 연결보다 인덱스 순서가 먼저다 |

## 처음 고를 두 가지

그래프를 코드로 다룰 때 초보자는 두 가지만 먼저 고르면 된다.

- **표현 방법 선택**: 정점이 많고 간선이 적은 희소 그래프라면 인접 리스트, 정점이 적고 간선이 많은 밀집 그래프라면 인접 행렬이 유리하다.
- **질문 모양 선택**: 연결만 보는지, 경로 하나가 필요한지, 최소 이동 횟수를 묻는지 먼저 자른다.

입문자는 이 세 가지를 한 번에 외우기보다 아래처럼 순서를 고정하면 덜 무겁다.

1. `무엇이 정점이고 무엇이 간선인가?`
2. `연결만 보나, 실제 경로를 보나, 최단을 보나?`
3. 그다음에야 BFS/DFS나 표현 방법을 고른다.

## 경로 질문이 나오면 여기서 갈라진다

> 빠른 분기: `연결만 확인`인지, `아무 경로 하나`인지, `최단 경로`인지 먼저 자르면 다음 문서가 바로 정해진다.

| 질문 형태 | 지금 필요한 답 | 다음 문서 |
|---|---|---|
| `A에서 B로 연결돼?`, `갈 수 있어?` | yes/no 연결 여부 | [Connectivity Question Router](./connectivity-question-router.md) |
| `연결 요소가 몇 개야?`, `이 묶음은 몇 명이야?` | 그룹 수, 그룹 크기 메타데이터 | [Connectivity Question Router](./connectivity-question-router.md) |
| `실제 경로 하나 보여줘` | 도달 가능한 경로 하나와 `parent` 복원 | [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md) |
| `가장 짧게 가는 길은?`, `최소 이동 횟수는?`, `최소 환승 횟수는?` | 무가중치면 BFS, 가중치가 있으면 Dijkstra 분기 | [BFS vs Dijkstra shortest path mini card](../algorithm/bfs-vs-dijkstra-shortest-path-mini-card.md) |

## 자주 섞는 표현

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

## 탐색은 다음 문서로 넘기기

이 문서는 그래프 그림을 붙이는 입구다. 아래부터는 질문이 더 구체적일 때 내려가면 된다.

- `가까운 칸부터`나 `최소 이동 횟수`가 핵심이면 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- `가중치가 있는 최단 경로`까지 가면 [그래프 관련 알고리즘](../algorithm/graph.md)
- `실제 경로 복원`이 막히면 [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md)

## 흔한 오해와 함정

- **오해 1: 그래프와 트리는 다른 개념이다.**
  트리는 사이클 없는 연결 무방향 그래프다. 트리는 그래프의 특수 케이스다.

- **오해 2: BFS는 항상 최단 경로를 찾는다.**
  간선 가중치가 모두 같을 때만 BFS가 최단 경로를 보장한다. 질문이 `갈 수 있나?` 수준이면 shortest-path가 아니라 연결성 분기이고, `가장 짧게`가 붙었을 때만 BFS vs Dijkstra를 고르면 된다. 먼저 [Connectivity Question Router](./connectivity-question-router.md)에서 질문 형태를 자르는 습관이 안전하다.

- **오해 3: 미로나 2차원 배열은 그래프가 아니다.**
  격자의 각 칸을 정점, 상하좌우 이동 가능 조건을 간선으로 보면 그대로 그래프다. 그래서 `최소 이동 횟수` 문제는 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)으로 자연스럽게 이어진다.

- **함정: 방문 배열 없이 그래프를 순회하면 무한 루프다.**
  사이클이 있는 그래프에서 `visited[]` 없이 BFS/DFS를 돌리면 같은 노드를 무한히 방문한다. 항상 방문 체크를 먼저 작성한다.

## 더 깊이 가려면

- 트리와의 구조 차이가 헷갈리면 [트리 기초](./tree-basics.md)
- 연결과 경로 질문이 섞이면 [Connectivity Question Router](./connectivity-question-router.md)
- 최단 경로, MST, 위상 정렬까지 한 번에 라우팅하려면 [그래프 관련 알고리즘](../algorithm/graph.md)

## 한 줄 정리

그래프는 정점과 간선으로 현실의 연결 관계를 표현하며, 인접 리스트로 저장하고 BFS/DFS로 탐색하는 세 가지 조합이 코딩 테스트의 기본이다.
