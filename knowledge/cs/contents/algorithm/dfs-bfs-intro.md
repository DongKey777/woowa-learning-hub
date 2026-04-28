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

retrieval-anchor-keywords: dfs bfs 입문, dfs bfs 차이, dfs 기초, bfs 기초, 깊이 우선 탐색 입문, 너비 우선 탐색 입문, bfs shortest path beginner, 최단 경로 bfs, 최소 이동 횟수, 최소 환승 횟수, bfs queue, bfs dfs 헷갈림, why bfs not dfs, connected component beginner

## README 복귀 가이드

- `BFS냐 queue냐`가 다시 섞이면 [Algorithm README - BFS, Queue, Map 먼저 분리하기](./README.md#bfs-queue-map-먼저-분리하기)로 돌아간다.
- `graph, bfs, queue` 층위가 다시 헷갈리면 [자료구조 README - graph, bfs, queue가 같이 보일 때](../data-structure/README.md#graph-bfs-queue가-같이-보일-때)를 같이 본다.

## 처음 읽을 때는 여기까지만

이 문서에서 먼저 고정할 것은 딱 두 가지다.

1. `끝까지 한 갈래를 파고들면 DFS`
2. `가까운 칸부터 최소 이동 횟수를 세면 BFS`

`0-1 BFS`, `가중치`, `MST`, `희소 그래프 shortest path`는 지금 바로 붙잡지 않아도 된다. 이 문서 끝의 관련 링크로 넘기면 충분하다.

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

## DFS, BFS, Queue를 한 번에 분리하기

처음에는 세 단어가 한 묶음처럼 보여도 층위가 다르다.

| 단어 | 역할 | 한 줄 기억 |
|---|---|---|
| 그래프 | 탐색 대상 구조 | 정점과 간선으로 관계를 그린다 |
| DFS / BFS | 방문 순서 규칙 | 깊게 갈지, 가까운 것부터 넓게 갈지 |
| queue / stack | 구현 도구 | BFS는 queue, DFS는 stack/재귀를 자주 쓴다 |

즉 `queue를 쓴다 = 무조건 BFS`는 아니고, `가까운 칸부터 한 겹씩 퍼진다`가 보여야 BFS다. 반대로 `graph가 나온다 = 무조건 BFS`도 아니다. 연결만 보거나 경로 하나만 찾으면 DFS도 충분할 수 있다.

처음 30초 판단표는 아래처럼 들고 가면 된다.

| 문제에서 보인 말 | beginner 번역 | 첫 선택 |
|---|---|---|
| `끝까지 가 보고 막히면 돌아오기` | 한 갈래를 깊게 본다 | DFS |
| `가까운 칸부터`, `최소 이동 횟수` | 거리 1, 2, 3 순서로 센다 | BFS |
| `갈 수 있나?` | 연결 여부만 확인하면 된다 | DFS 또는 BFS |
| `최소 비용`, `가중치` | BFS 범위를 벗어난다 | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) |

## 문제 문장 번역

처음에는 용어보다 질문을 이렇게 번역하면 빠르다.

| 문제 문장 | 먼저 떠올릴 탐색 | 이유 |
|---|---|---|
| `끝까지 가 보고 막히면 돌아오기` | DFS | 한 갈래를 깊게 따라간다 |
| `가까운 칸부터 최소 이동 횟수` | BFS | 거리 1, 2, 3 순서로 퍼진다 |
| `연결되어 있는지 전부 표시` | DFS 또는 BFS | 둘 다 방문 자체는 가능하다 |

입문자가 가장 많이 혼동하는 지점은 "최단 경로"다. **BFS는 간선 가중치가 모두 같을 때 최단 경로를 보장**하고, DFS는 경로를 하나씩 탐색하므로 최단을 보장하지 않는다.

처음 미로 문제를 읽을 때는 아래처럼 문장을 바로 다시 적어 보면 덜 헷갈린다.

```text
S . .
# # .
. . E
```

| 처음 본 문장 | 초보자 번역 | 첫 선택 |
|---|---|---|
| `S에서 E로 갈 수 있어?` | 연결 여부 yes/no | DFS 또는 BFS |
| `S에서 E까지 아무 경로나 하나만 보여줘` | 유효 경로 하나 | DFS 또는 BFS + `parent` |
| `S에서 E까지 최소 몇 칸이야?` | 간선 수 최소 | BFS |
| `S에서 E까지 비용 합이 최소야?` | 칸 수가 아니라 가중치 합 최소 | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) |

`왜 같은 미로인데 답이 달라져요?`라는 질문의 핵심은 지도가 아니라 **문제 문장**이 바뀌었다는 점이다.

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
- `비용`, `가중치`, `요금`이 보이면 BFS 고집을 멈추고 [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)로 넘긴다.

입문자는 아래 4문장을 그대로 체크리스트처럼 읽어도 된다.

| 문제에서 실제로 묻는 말 | 첫 판단 | 바로 다음 문서 |
|---|---|---|
| `갈 수 있나?` | 연결 여부라서 yes/no 문제다 | [Connectivity Question Router](../data-structure/connectivity-question-router.md) |
| `아무 경로 하나 보여줘` | 유효한 경로 하나면 된다 | [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md) |
| `최소 이동 횟수`, `최소 환승 횟수` | 무가중치 shortest path라서 BFS다 | 이 문서 |
| `최소 비용`, `가중치 합` | BFS가 아니라 weighted shortest path 분기다 | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) |

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

같은 `최소`라도 무엇을 최소화하는지 먼저 자르면 초반 오진이 줄어든다.

| 문제 문장 | 실제로 최소화하는 것 | 첫 출발점 |
|---|---|---|
| `최소 이동 횟수` | 간선 수 | BFS |
| `최소 환승 횟수` | 단계 수 | BFS |
| `최소 비용` | 가중치 합 | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) |

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
| 연결성 확인 | O | O |
| 사이클 감지 | O | O |

`visited`가 배열이든 `set/map`이든 이 문서에서는 `중복 방문을 막는다`까지만 이해하면 충분하다. 구현체 선택이 막히면 [Java BFS visited 배열 vs Set beginner card](./bfs-visited-array-vs-set-java-beginner-card.md)로 넘기면 된다.

왜 `최소 이동 횟수`면 BFS가 먼저냐는 질문은 레벨 그림 하나로 끝난다.

```text
시작
거리 0: S
거리 1: S에서 한 번에 닿는 칸들
거리 2: 그다음 한 번 더 가서 닿는 칸들
```

BFS는 큐로 `거리 0 -> 1 -> 2` 순서를 지키므로, 처음 도착한 순간의 거리가 곧 최소 이동 횟수다. 반대로 DFS는 한 갈래를 끝까지 파고들기 때문에 먼저 도착했다고 해서 최소라고 보장되지 않는다.

## 구현에서 딱 두 군데만 조심

- **DFS 흐름**: 방문한 노드를 visited 배열로 표시 → 현재 노드의 인접 노드 중 미방문 노드를 재귀 호출 → 더 갈 곳 없으면 리턴.
- **BFS 흐름**: 시작 노드를 큐에 삽입 + visited 표시 → 큐에서 노드 꺼냄 → 그 노드의 인접 노드 중 미방문을 큐에 삽입 + visited 표시 → 반복.
- **visited 배열의 위치**: BFS에서는 큐에 **넣을 때** visited를 표시해야 중복 삽입을 막는다. 꺼낼 때 표시하면 같은 노드가 여러 번 큐에 들어간다.
- `dist`, `parent`, 실제 경로 출력까지 한 번에 붙잡으려 하면 초반에 과부하가 온다. 이 문서에서는 `DFS냐 BFS냐`, `최소면 BFS냐`까지만 먼저 고정한다.

## 어디까지가 이 문서 범위인가

이 문서는 `DFS냐 BFS냐`를 자르는 primer다. 아래 주제는 여기서 깊게 들어가지 않고 다음 문서로 넘기는 편이 안전하다.

- `가중치가 있는 최단 경로`, `0/1 비용 shortest path` -> [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- `실제 경로 복원` -> [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- `0-1 BFS`, 희소 그래프 shortest path, MST 같은 확장 비교 -> [그래프 관련 알고리즘](./graph.md)
- `그래프 자체가 아직 추상적` -> [그래프 기초](../data-structure/graph-basics.md)

처음 읽는 단계라면 `0-1 BFS`, `가중치`, `MST`가 보여도 지금은 `왜 queue를 쓰는지`, `왜 최소 이동 횟수면 BFS인지`까지만 고정하고, 그다음 한 칸으로는 broad graph 문서보다 [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)를 먼저 여는 편이 더 안전하다.

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

- BFS shortest path와 가중치 shortest path를 자르고 싶으면 [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- 실제 경로 출력이 막히면 [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- `queue` 감각이 약하면 [큐 기초](../data-structure/queue-basics.md)
- primer를 다 읽었는데도 다음 문서가 막히면 [algorithm 카테고리 인덱스](./README.md)

## 다음 단계

- `경로 하나 찾기`와 `최소 경로 길이`를 자꾸 섞는다면 [Path vs Shortest Path Micro Drill](./path-vs-shortest-path-micro-drill.md)
- BFS와 Dijkstra 경계를 바로 자르고 싶다면 [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- 그래프 문제 전체 라우팅이 필요하면 [그래프 관련 알고리즘](./graph.md)

## 한 줄 정리

DFS는 재귀(스택)로 깊게, BFS는 큐로 넓게 탐색하며, 단위 가중치 최단 경로는 BFS로만 보장된다.
