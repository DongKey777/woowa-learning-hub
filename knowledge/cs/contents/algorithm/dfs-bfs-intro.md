# DFS와 BFS 입문 (DFS and BFS Basics)

> 한 줄 요약: DFS는 스택(재귀)으로 한 방향을 끝까지 파고드는 탐색이고, BFS는 큐로 가까운 노드부터 넓게 퍼지는 탐색이며, 두 방식은 "연결성 확인"은 같이 되지만 "최단 경로"는 BFS만 보장한다.

**난이도: 🟢 Beginner**

관련 문서:

- [그래프 관련 알고리즘](./graph.md)
- [알고리즘 기본](./basic.md)
- [Connectivity Question Router](../data-structure/connectivity-question-router.md)
- [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- [Java BFS visited 배열 vs Set beginner card](./bfs-visited-array-vs-set-java-beginner-card.md)
- [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- [algorithm 카테고리 인덱스](./README.md)
- [그래프 기초](../data-structure/graph-basics.md)

retrieval-anchor-keywords: dfs bfs 입문, dfs bfs 차이, dfs 기초, bfs 기초, 깊이 우선 탐색 입문, 너비 우선 탐색 입문, graph traversal beginner, bfs shortest path beginner, 최단 경로 bfs, 미로 bfs, 최소 이동 횟수, 최소 환승 횟수, bfs queue, bfs dfs 헷갈림, connected component beginner

## 핵심 개념

그래프(또는 트리)에서 모든 노드를 방문하는 방법은 크게 두 가지다.

- **DFS (Depth-First Search)**: 현재 노드에서 갈 수 있는 방향을 하나 골라 끝까지 파고든다. 재귀 호출 스택 또는 명시적 스택으로 구현한다.
- **BFS (Breadth-First Search)**: 현재 노드에서 인접한 모든 노드를 먼저 방문한 뒤 그 다음 거리로 나아간다. 큐로 구현한다.

처음에는 용어보다 그림을 이렇게 잡으면 된다.

- DFS는 `막다른 길이 나올 때까지 한 줄로 걷는 방식`이다.
- BFS는 `같은 거리의 칸을 한 겹씩 넓히는 방식`이다.
- 그래서 `최소 이동 횟수`라는 표현이 보이면 BFS부터 의심하고, `가능한 경우를 끝까지 파 본다`가 보이면 DFS를 먼저 떠올린다.

처음 1회독이면 아래 세 문장만 먼저 잡아도 된다.

- `왜 queue가 나오죠?` -> BFS는 넓게 퍼지는 순서를 만들기 위해 queue를 쓴다.
- `왜 dfs bfs가 헷갈리죠?` -> 둘 다 방문은 가능하지만 질문이 `최소`인지가 다르다.
- `언제 bfs예요?` -> `최소 이동 횟수`, `최소 환승 횟수`, `가까운 칸부터`가 보일 때다.

## 문제 문장 번역

처음에는 용어보다 질문을 이렇게 번역하면 빠르다.

| 문제 문장 | 먼저 떠올릴 탐색 | 이유 |
|---|---|---|
| `끝까지 가 보고 막히면 돌아오기` | DFS | 한 갈래를 깊게 따라간다 |
| `가까운 칸부터 최소 이동 횟수` | BFS | 거리 1, 2, 3 순서로 퍼진다 |
| `연결되어 있는지 전부 표시` | DFS 또는 BFS | 둘 다 방문 자체는 가능하다 |

입문자가 가장 많이 혼동하는 지점은 "최단 경로"다. **BFS는 간선 가중치가 모두 같을 때 최단 경로를 보장**하고, DFS는 경로를 하나씩 탐색하므로 최단을 보장하지 않는다.

## 먼저 질문부터 자르기

그래프 문제에서 `DFS냐 BFS냐`를 고르기 전에, 질문이 무엇을 요구하는지부터 자르면 초반 오답이 크게 줄어든다.

| 문제 문장 | 먼저 필요한 답 | 첫 출발점 |
|---|---|---|
| `A에서 B로 갈 수 있어?` | yes/no 연결 여부 | [Connectivity Question Router](../data-structure/connectivity-question-router.md) |
| `갈 수 있으면 아무 경로나 하나 보여줘` | 실제 경로 하나 | DFS 또는 BFS + `parent` |
| `가장 적게 움직여서 가는 길은?` | 최소 간선 수 경로 | BFS |

짧게 외우면 이렇게 보면 된다.

- `연결만 확인`이면 DFS/BFS 구현 전에 질문 bucket부터 자른다.
- `경로 하나`면 DFS도 가능하다.
- `최소`가 붙으면 BFS부터 의심한다.

## 같은 그래프, 질문이 바뀌면

처음 읽을 때는 `최소 이동 횟수`와 `최소 환승 횟수`를 같은 패턴으로 묶으면 쉽다.

| 문제 문장 | 실제로 세는 것 | 첫 선택 |
|---|---|---|
| `미로에서 출구까지 최소 이동 횟수` | 칸을 몇 번 건너는가 = 간선 수 | BFS |
| `A역에서 B역까지 최소 환승 횟수` | 역/노선을 몇 번 넘어가는가 = 간선 수 | BFS |

둘 다 핵심은 "`한 번 이동`의 비용이 모두 1로 같다"는 점이다. 그래서 초보자에게는 `이동`이든 `환승`이든 먼저 **간선 수를 세는 문제인가**로 읽는 습관이 중요하다.

같은 작은 그래프도 질문이 바뀌면 첫 선택이 달라진다.

```text
1 - 2 - 4
 \  |
   3
```

| 같은 그래프에서 바뀐 질문 | 필요한 답 | 첫 선택 |
|---|---|---|
| `1에서 4로 갈 수 있나?` | yes/no | DFS 또는 BFS |
| `1에서 4까지 아무 경로나 하나 보여줘` | `1 -> 2 -> 4` 같은 유효 경로 | DFS 또는 BFS + `parent` |
| `1에서 4까지 최소 몇 번 만에 가나?` | 최소 간선 수 | BFS |

같은 `queue`가 보여도 아래처럼 질문이 다르면 출발점이 달라진다.

| 문장 신호 | 실제 핵심 | 첫 출발점 |
|---|---|---|
| `먼저 받은 요청부터 처리` | FIFO 규칙 | [큐 기초](../data-structure/queue-basics.md) |
| `가까운 칸부터 한 겹씩 확장` | 거리 순서 탐색 | BFS |
| `가장 급한 작업부터 처리` | 우선순위 기준 | [Queue vs Deque vs Priority Queue Primer](../data-structure/queue-vs-deque-vs-priority-queue-primer.md) |

## 한눈에 보기

```
그래프 예시:
1 - 2 - 4
|       |
3 - - - 5

DFS (1 시작): 1 → 2 → 4 → 5 → 3 (한 방향 끝까지)
BFS (1 시작): 1 → 2 → 3 → 4 → 5 (거리 1, 거리 2 순서)
```

| 특성 | DFS | BFS |
|---|---|---|
| 자료구조 | 스택 (재귀) | 큐 |
| 최단 경로 보장 | X | O (단위 가중치) |
| 메모리 | 경로 깊이 O(h) | 최대 너비 O(w) |
| 연결성 확인 | O | O |
| 사이클 감지 | O | O |

`visited set/map`이 같이 보여도 탐색을 버리는 신호는 아니다.

| 코드/문장 신호 | 실제 역할 | 먼저 볼 문서 |
|---|---|---|
| `visited.add(next)` | 중복 방문 방지 | 이 문서의 BFS/DFS 흐름 |
| `dist.put(next, dist.get(cur) + 1)` | 거리 기록 | 이 문서의 BFS |
| `parent.put(next, cur)` | 실제 경로 복원 | [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md) |

`visited[]`와 `visited set` 중 무엇을 고를지 자꾸 막히면,
정점 번호가 `0..n-1`처럼 촘촘한지부터 보는 편이 빠르다.
이 분기는 [Java BFS visited 배열 vs Set beginner card](./bfs-visited-array-vs-set-java-beginner-card.md)에 따로 정리돼 있다.

## 구현에서 딱 두 군데만 조심

- **DFS 흐름**: 방문한 노드를 visited 배열로 표시 → 현재 노드의 인접 노드 중 미방문 노드를 재귀 호출 → 더 갈 곳 없으면 리턴.
- **BFS 흐름**: 시작 노드를 큐에 삽입 + visited 표시 → 큐에서 노드 꺼냄 → 그 노드의 인접 노드 중 미방문을 큐에 삽입 + visited 표시 → 반복.
- **visited 배열의 위치**: BFS에서는 큐에 **넣을 때** visited를 표시해야 중복 삽입을 막는다. 꺼낼 때 표시하면 같은 노드가 여러 번 큐에 들어간다.
- **DFS 재귀 깊이**: 이 문서에서는 `깊게 파고든다`는 감각만 잡으면 충분하다. 큰 입력에서 스택 한계가 걱정되면 명시적 스택 구현은 후속 문서에서 본다.

## 어디까지가 이 문서 범위인가

이 문서는 `DFS냐 BFS냐`를 자르는 primer다. 아래 주제는 여기서 깊게 들어가지 않고 다음 문서로 넘기는 편이 안전하다.

- `가중치가 있는 최단 경로` -> [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- `실제 경로 복원` -> [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- `그래프 자체가 아직 추상적` -> [그래프 기초](../data-structure/graph-basics.md)

## 흔한 오해와 함정

- "DFS는 느리고 BFS는 빠르다" → 틀리다. 두 방식 모두 시간복잡도는 O(V+E)로 같다.
- "BFS를 쓰면 항상 최단 경로를 찾는다" → 간선 비용이 모두 같을 때만. 가중치가 다르면 다익스트라를 써야 한다.
- "DFS는 트리에서만 쓴다" → 그래프(사이클 있음)에서도 visited 배열만 있으면 쓸 수 있다.
- "`queue`를 쓴다고 다 BFS다" → 아니다. 작업 대기열도 queue를 쓴다. 핵심은 `거리 순서로 퍼지느냐`다.
- "`visited`를 map/set으로 두면 BFS/DFS가 아닌가요?" → 아니다. 방문 기록을 배열로 두든 `set/map`으로 두든 핵심은 탐색 순서다. 노드 번호가 듬성듬성하거나 문자열 key면 `visited set/map`이 더 자연스럽다.
- visited 배열 없이 DFS 호출하면 사이클이 있는 그래프에서 무한 루프가 된다.
- "BFS는 큐만 쓰면 된다" → 반만 맞다. **큐에 넣을 때 visited 표시**를 해야 같은 노드가 여러 번 들어가지 않는다.
- "`map`이 보이면 자료구조 문제 아닌가요?" → 아니다. BFS에서 `dist map`, `parent map`, `visited set/map`은 흔한 보조 저장소다. 핵심 질문이 `최소 이동 횟수`면 여전히 BFS부터 읽는 편이 맞다.

## 작은 예시로 다시 묶기

- `미로에서 출구까지 최소 이동 횟수` -> BFS
- `지하철에서 최소 환승 횟수` -> BFS
- `섬 개수 세기` -> DFS 또는 BFS
- `가능한 경우를 끝까지 따라가 보기` -> DFS

## 더 깊이 가려면

- 최단 경로 알고리즘 비교(가중치 그래프 포함)는 [그래프 관련 알고리즘](./graph.md)
- BFS shortest path와 Dijkstra shortest path를 같은 예제로 바로 분리하려면 [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- BFS와 Dijkstra가 `parent`/`predecessor` 배열로 실제 경로를 어떻게 복원하는지는 [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- BFS 응용 패턴과 복잡도 증명은 [algorithm 카테고리 인덱스](./README.md)
- BFS에서 쓰는 FIFO 큐 감각이 약하면 [큐 기초](../data-structure/queue-basics.md)
- Java에서 `visited[]`와 `Set`을 언제 고르는지 따로 보고 싶으면 [Java BFS visited 배열 vs Set beginner card](./bfs-visited-array-vs-set-java-beginner-card.md)

## 다음 단계

- `경로 하나 찾기`와 `최소 경로 길이`를 자꾸 섞는다면 [Path vs Shortest Path Micro Drill](./path-vs-shortest-path-micro-drill.md)
- BFS와 Dijkstra 경계를 바로 자르고 싶다면 [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- 그래프 문제 전체 라우팅이 필요하면 [그래프 관련 알고리즘](./graph.md)

## 한 줄 정리

DFS는 재귀(스택)로 깊게, BFS는 큐로 넓게 탐색하며, 단위 가중치 최단 경로는 BFS로만 보장된다.
