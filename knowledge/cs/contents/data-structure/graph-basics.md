# 그래프 기초 (Graph Basics)

> 한 줄 요약: 그래프는 `점`과 `점 사이 연결선`으로 관계를 그리는 자료구조이며, 초보자는 먼저 `무엇이 점이고 무엇이 연결인가`만 잡아도 BFS/DFS와 최단 경로 문서를 훨씬 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- [BFS vs Dijkstra shortest path mini card](../algorithm/bfs-vs-dijkstra-shortest-path-mini-card.md)
- [Connectivity Question Router](./connectivity-question-router.md)
- [큐 기초](./queue-basics.md)
- [자료구조 정리](./README.md)
- [그래프 관련 알고리즘](../algorithm/graph.md)

retrieval-anchor-keywords: graph basics, graph basics beginner, what is graph, 그래프 입문, 그래프가 뭐예요, 왜 미로도 그래프, vertex edge, graph vs tree, directed undirected graph, adjacency list basics, 처음 그래프, 그래프 헷갈림

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

입문자는 아래 세 가지만 먼저 구분하면 충분하다.

| 분류 | 처음엔 이렇게 이해 | 지금 단계 메모 |
|---|---|---|
| 트리 | 사이클 없는 특별한 그래프 | 부모-자식 그림이 먼저 보일 때 |
| 방향 그래프 | A -> B와 B -> A가 다를 수 있음 | 팔로우, 링크, 일방통행 |
| 무방향 그래프 | 한 번 연결되면 양쪽 이동 가능 | 친구 관계, 양방향 길 |

`가중치 그래프`, `최단 비용`, `다익스트라`는 이 문서의 중심이 아니다. 처음 읽는 단계라면 `점과 선으로 읽기`까지만 잡고, 비용 이야기는 뒤 문서로 넘기는 편이 안전하다.

처음 읽는 사람이 자주 묻는 질문을 한 줄로 자르면 아래처럼 정리된다.

| 지금 막힌 문장 | 먼저 잡을 생각 | 다음 문서 |
|---|---|---|
| `그래프가 뭐예요?` | 점과 연결 규칙을 그림으로 이해 | 이 문서 |
| `가까운 칸부터 왜 queue로 보나요?` | 탐색 순서 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `연결만 확인하면 되나요, 경로도 필요하나요?` | 답의 모양 분기 | [Connectivity Question Router](./connectivity-question-router.md) |

## 10초 mental model

처음 그래프를 보면 용어가 많아서 막히기 쉽다. 초보자 기준으로는 아래 세 줄만 먼저 분리하면 된다.

| 지금 헷갈리는 단어 | 먼저 이렇게 번역 | 다음 문서 |
|---|---|---|
| `graph` | 점과 선으로 상태 관계를 그린 그림 | 이 문서 |
| `bfs` / `dfs` | 그 그림을 어떤 순서로 방문할지 정하는 탐색 규칙 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `queue` | BFS를 구현할 때 쓰는 도구 | [큐 기초](./queue-basics.md) |

즉 `그래프 = 구조`, `BFS/DFS = 탐색 방식`, `queue = 구현 도구`다. 이 세 층위를 분리하면 `왜 그래프 문서에도 BFS가 나오고 queue 문서도 따로 있지?`라는 혼동이 크게 줄어든다.

## 처음 30초 분기
처음 30초 안에 문장을 고르는 표도 같이 보면 더 덜 헷갈린다.

| learner symptom | 지금 바로 답할 한 문장 | 첫 이동 |
|---|---|---|
| `그래프가 뭐예요?` | 점과 선으로 관계를 그리는 구조다 | 이 문서 |
| `왜 미로도 그래프예요?` | 칸을 점으로, 이동 가능을 선으로 바꾸면 된다 | 이 문서 -> [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `왜 queue가 같이 나와요?` | queue는 BFS를 구현할 때 쓰는 도구일 뿐이다 | [큐 기초](./queue-basics.md) |
| `언제 BFS예요?` | `최소 이동 횟수`, `가까운 칸부터`가 보일 때다 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |

같은 그래프 그림도 질문 문장이 달라지면 다음 문서가 달라진다.

| 같은 장면에서 바뀐 질문 | 먼저 필요한 답 | 다음 문서 |
|---|---|---|
| `갈 수 있나?`, `같은 그룹인가?` | yes/no 연결 여부 | [Connectivity Question Router](./connectivity-question-router.md) |
| `어떻게 가나?` | 경로 하나 복원 | [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md) |
| `가장 짧게 가나?`, `최소 이동 횟수인가?` | 무가중치 shortest path | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |

처음에는 한 장면만 붙잡아도 충분하다.

| 같은 장면 | 그래프 문장으로 읽으면 | BFS 문장으로 읽으면 | queue 문장으로 읽으면 |
|---|---|---|---|
| 지하철 길찾기 | 역은 정점, 이동 가능은 간선 | 가까운 역부터 몇 번 만에 도착하나 | 탐색 중 다음에 볼 역을 FIFO로 보관 |
| 미로 탈출 | 칸은 정점, 상하좌우 이동은 간선 | 거리 1, 2, 3 순서로 퍼져서 최소 칸 수를 센다 | 이번 레벨에서 발견한 칸을 순서대로 꺼낸다 |
| 추천 그래프 | 사용자/상품은 정점, 클릭/연결 관계는 간선 | 몇 단계 안에 닿는 추천인지 본다 | 다음에 확장할 후보를 순서대로 보관한다 |

`그래프가 뭐예요`, `왜 미로가 그래프예요`, `왜 queue가 같이 나와요`는 결국 같은 장면을 어느 층위에서 읽는지의 차이다.

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

처음 미로를 그래프로 바꾸는 감각이 안 오면 2 x 2 칸만 그려도 충분하다.

```text
[S][.]
[.][E]
```

| 미로에서 보는 것 | 그래프로 번역하면 |
|---|---|
| 각 칸 | 정점 하나 |
| 상하좌우로 이동 가능 | 정점 사이 간선 |
| `S`에서 `E`까지 최소 몇 칸? | 무가중치 shortest-path 질문 |

즉 `왜 갑자기 그래프예요?`라는 질문에는 `칸을 정점으로 바꿔 읽기 때문`이라고 답하면 된다. 여기까지 번역되면 다음 단계는 자연스럽게 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)으로 이어진다.

## beginner 다음 한 걸음 사다리

그래프 primer를 읽은 직후 초급자가 가장 많이 하는 점프는 `정점/간선은 알겠는데 바로 다익스트라나 MST를 봐야 하나요?`다.
안전한 순서는 아래처럼 `primer -> follow-up -> deep dive` 3칸만 유지하는 것이다.

| 지금 막힌 문장 | primer | 바로 다음 follow-up | 그다음 deep dive |
|---|---|---|---|
| `가까운 칸부터`, `최소 이동 횟수`가 보여요 | 이 문서 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | [그래프 관련 알고리즘](../algorithm/graph.md)으로 가기 전에 [BFS vs Dijkstra shortest path mini card](../algorithm/bfs-vs-dijkstra-shortest-path-mini-card.md)에서 `무가중치 vs 가중치`를 먼저 자른다 |
| `갈 수 있나?`, `같은 그룹인가요?`가 먼저예요 | 이 문서 | [Connectivity Question Router](./connectivity-question-router.md) | 연결성 분기가 끝난 뒤에만 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)으로 간다 |
| `실제 경로 하나만 보여주면 돼요` | 이 문서 | [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md) | 경로 복원이 익숙해진 뒤에만 shortest-path 비교로 넓힌다 |

- `처음`, `헷갈려요`, `왜 queue가 같이 나와요`, `최단 경로 뭐예요` 같은 query는 이 사다리에서 한 칸씩만 내려가는 편이 beginner-safe 하다.
- 핵심은 `그래프 그림 이해 -> 질문 모양 분리 -> shortest-path 종류 구분` 순서를 지키는 것이다.

처음 헷갈리는 구조를 한 번에 자르면 아래 표가 가장 빠르다.

| 지금 떠오른 그림 | 먼저 보는 구조 | 초보자용 한 줄 메모 |
|---|---|---|
| `루트에서 자식으로 내려간다` | 트리 | 부모-자식 방향이 먼저 보인다 |
| `칸과 칸이 이어져 있다` | 그래프 | 격자도 칸을 정점으로 보면 그래프다 |
| `순서대로 줄 세운 값` | 배열/리스트 | 연결보다 인덱스 순서가 먼저다 |

## 처음 고를 두 가지

그래프를 처음 코드로 옮길 때는 두 가지만 먼저 고르면 된다.

- **무엇이 정점이고 무엇이 간선인가**
- **질문이 연결인지, 경로 하나인지, 최소 이동 횟수인지**

표현 방법은 대부분 인접 리스트부터 시작하면 충분하다. 인접 행렬은 "정점 수가 작고 연결 여부를 자주 바로 확인해야 할 때"만 후속 비교로 넘겨도 된다.

입문자는 세부 구현을 한 번에 외우기보다 아래 순서를 고정하면 덜 무겁다.

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

처음 읽는 사람은 문장을 이렇게 바로 번역해도 충분하다.

- `갈 수 있어?` -> 연결성 질문
- `어떻게 가?` -> 경로 하나 복원 질문
- `가장 짧게 가?` -> shortest-path 질문

처음이라면 여기서 바로 다익스트라나 MST로 넓히지 말고, `그래프 그림 이해 -> 질문 모양 분리 -> BFS/DFS 입문` 순서만 지키는 편이 가장 안전하다.

## 자주 섞는 표현

초보자 기준으로 제일 많이 섞이는 두 문장은 이것이다.

- `갈 수 있나?`는 연결 여부 질문이라 경로를 꼭 출력할 필요가 없다.
- `어떻게 가나?`와 `가장 짧게 어떻게 가나?`는 다른 질문이다. 앞은 경로 하나, 뒤는 shortest-path 문제다.
- `최소 이동 횟수`와 `최소 환승 횟수`는 표현만 다르고, 처음 읽을 때는 둘 다 `간선 수를 최소로 세는가?`로 번역하면 BFS 출발점이 같다.
- `BFS`라는 단어가 보여도 바로 shortest-path로 들어가지 말고, 먼저 [Connectivity Question Router](./connectivity-question-router.md)에서 `yes/no vs 경로 하나 vs minimum path`를 자르면 헷갈림이 크게 줄어든다.

## 경로 질문은 여기서 멈추기

이 문서에서 중요한 것은 `그래프를 어떤 그림으로 읽는가`까지다.
경로 질문이 나오면 아래처럼 **답의 모양만 분리**하고, 자세한 구현은 다음 문서로 넘기면 된다.

| 질문 형태 | 지금 기억할 것 | 다음 문서 |
|---|---|---|
| `갈 수 있나?` | yes/no 연결 여부 질문이다 | [Connectivity Question Router](./connectivity-question-router.md) |
| `어떻게 가나?` | 경로 하나를 복원해야 한다 | [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md) |
| `가장 짧게 어떻게 가나?` | shortest-path 질문이다 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |

- `parent` 배열, 역추적, 실제 출력 형식은 복원 브리지 문서에서 따로 보는 편이 초보자에게 덜 무겁다.
- 이 문서에서는 `정점/간선 그림`과 `질문 종류 분리`까지만 잡아도 충분하다.

## 탐색은 다음 문서로 넘기기

이 문서는 그래프 그림을 붙이는 입구다. 아래부터는 질문이 더 구체적일 때 내려가면 된다.

- `가까운 칸부터`나 `최소 이동 횟수`가 핵심이면 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- `가중치`, `비용 합`, `0/1 비용`이 같이 보이면 [BFS vs Dijkstra shortest path mini card](../algorithm/bfs-vs-dijkstra-shortest-path-mini-card.md)에서 `BFS vs 0-1 BFS vs Dijkstra`를 먼저 자른다
- shortest-path 종류를 구분한 뒤 더 넓은 비교가 필요할 때만 [그래프 관련 알고리즘](../algorithm/graph.md)
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
- `최소 이동 횟수`가 왜 BFS로 가는지 막히면 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- 최단 경로, MST, 위상 정렬처럼 더 넓은 비교가 필요할 때만 [그래프 관련 알고리즘](../algorithm/graph.md)

## 한 줄 정리

그래프는 정점과 간선으로 현실의 연결 관계를 표현하며, 인접 리스트로 저장하고 BFS/DFS로 탐색하는 세 가지 조합이 코딩 테스트의 기본이다.
