# BFS vs Dijkstra shortest path beginner split card

> 한 줄 요약: `간선 수 최소`를 묻는지 `비용 합 최소`를 묻는지 먼저 자르면, 초보자가 BFS와 Dijkstra를 헷갈리는 빈도가 크게 줄어든다.

**난이도: 🟢 Beginner**

관련 문서:

- [DFS와 BFS 입문](./dfs-bfs-intro.md)
- [0-1 BFS grid-conversion primer](./zero-one-bfs-grid-conversion-primer.md)
- [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)
- [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)
- [그래프 기초](../data-structure/graph-basics.md)
- [algorithm 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: bfs vs 0-1 bfs vs dijkstra, unweighted vs binary weighted vs weighted shortest path, bfs shortest path, zero one bfs shortest path, dijkstra shortest path, edge count vs cost sum, deque shortest path beginner, beginner shortest path graph, 최단 경로 뭐예요, 무가중치 최단 경로, 0/1 가중치 최단 경로, 가중치 최단 경로, bfs 0-1 bfs 다익스트라 차이, 간선 수 최소, 비용 합 최소

## 핵심 개념

이 문서의 목표는 shortest path 전체를 다 외우는 게 아니라, 초보자 오분류 하나를 줄이는 것이다.

- `간선 수 최소`면 BFS
- `비용 합 최소`면 Dijkstra 계열

문제를 읽을 때 `최단`이라는 단어만 보면 안 된다. `무엇이 짧은가`를 먼저 확인해야 한다.

- `최소 이동 횟수`, `최소 칸 수`, `최소 환승 횟수` -> 보통 간선 수 최소
- `최소 비용`, `최소 시간`, `최소 요금` -> 보통 비용 합 최소

처음 1분 판단 규칙은 이것만 들고 가면 된다.

- 한 번 이동할 때 드는 값이 전부 같으면: BFS
- 이동마다 드는 값이 다를 수 있으면: Dijkstra
- 예외로 비용이 `0` 또는 `1`만 나오면: 0-1 BFS도 후보

## 한 표로 바로 구분하기

| 알고리즘 | 간선 비용 | 보통 최소화하는 것 | 핵심 자료구조 | 첫 질문 |
|---|---|---|---|---|
| BFS | 전부 동일, 보통 `1` | 이동 횟수, 간선 수 | 큐 | "모든 이동이 같은 한 걸음인가?" |
| 0-1 BFS | `0` 또는 `1`만 존재 | 0/1 비용 합 | deque | "공짜 이동과 유료 이동만 섞였나?" |
| Dijkstra | 0 이상 일반 가중치 | 일반 비용 합 | 우선순위 큐 | "`2`, `5` 같은 비용도 나오나?" |

위 표에서 beginner가 먼저 붙잡아야 하는 축은 두 개뿐이다.

| 먼저 볼 축 | BFS 쪽 신호 | Dijkstra 쪽 신호 |
|---|---|---|
| 무엇을 최소화하나 | 칸 수, 이동 횟수, 환승 횟수 | 시간, 요금, 위험도, 연료 |
| 한 번 이동 비용이 같은가 | 예 | 아니오 |

`최단 경로 = BFS`가 아니라, `간선 수 shortest = BFS`라고 기억하면 덜 틀린다.

## 1분 컷 예시

```text
S --2--> T
 \\
  0
   \\
    > A --1--> T
```

- `S -> T`: 간선 1개, 총 비용 2
- `S -> A -> T`: 간선 2개, 총 비용 1

같은 그래프여도 무엇을 "짧다"라고 부르는지에 따라 답이 달라진다.

| 질문 | 답 | 이유 |
|---|---|---|
| 간선 수가 가장 적은 경로는? | `S -> T` | 1번 이동이라서 BFS 기준 shortest |
| 비용이 `0/1`만일 때 최소 비용 경로는? | `S -> A -> T` | `0 + 1 = 1`이라서 0-1 BFS 기준 shortest |
| 일반 비용 최솟값 경로는? | `S -> A -> T` | 총 비용 1이 2보다 작아서 Dijkstra 기준 shortest |

이 예시에서 초보자가 가장 자주 놓치는 점은 이것이다.

- `간선 1개`라고 해서 비용까지 가장 작은 건 아니다.
- `최단`이라는 한 단어 안에 `간선 수 shortest`와 `비용 shortest`가 같이 들어올 수 있다.
- 그래서 문제 문장을 읽을 때는 경로 길이보다 목적 함수부터 본다.

## 흔한 문제 문장 번역

| 문제 문장 | 실제로 묻는 것 | 첫 선택 |
|---|---|---|
| `미로에서 출구까지 최소 몇 칸인가?` | 간선 수 최소 | BFS |
| `지하철에서 최소 환승 횟수는?` | 간선 수 최소 | BFS |
| `마을 A에서 B까지 최소 요금은?` | 비용 합 최소 | Dijkstra |
| `도로마다 시간이 다를 때 가장 빠른 길은?` | 비용 합 최소 | Dijkstra |
| `순간이동은 0초, 걷기는 1초다` | 0/1 비용 합 최소 | 0-1 BFS |

짧게 번역하면 아래처럼 된다.

- `몇 번 움직였나`를 세면 BFS
- `움직일 때마다 드는 값의 합`을 세면 Dijkstra
- `드는 값`이 `0` 또는 `1`만 섞이면 0-1 BFS

## 자주 하는 착각

- "BFS는 최단 경로 알고리즘이니까 가중치 그래프에도 된다" -> 아니다. BFS는 간선 비용이 모두 같을 때만 안전하다.
- "`최단`이라고만 써 있으니 BFS겠지" -> 아니다. `최단` 앞뒤에 `비용`, `시간`, `요금`이 붙으면 Dijkstra 쪽이다.
- "`0`과 `1`만 있으니 Dijkstra만 쓰면 된다" -> 맞게 풀 수는 있지만, 문제 조건을 더 직접 쓰는 쪽은 0-1 BFS다.
- "간선이 1개면 항상 더 짧다" -> 비용 문제에서는 틀릴 수 있다. `1개짜리 비싼 길`보다 `2개짜리 싼 길`이 더 좋을 수 있다.
- "가중치가 전부 1이면 Dijkstra만 써야 한다" -> 아니다. 이때는 BFS가 더 단순하다.

## 이렇게 고르면 덜 헷갈린다

1. 문제 문장에서 `무엇을 최소화하는지` 먼저 동그라미 친다.
2. `횟수`를 세면 BFS, `합`을 세면 Dijkstra로 먼저 가른다.
3. `합`을 세는데 비용이 `0/1`뿐이면 0-1 BFS로 더 줄인다.
4. 구현 전에 "`이동마다 비용이 같은가?`"를 한 번 더 확인한다.

이 카드만으로도 초보자 기준 첫 오진 대부분은 막을 수 있다.

## 더 깊이 가려면

- `경로 하나 찾기`와 `최단 경로`를 자꾸 섞는다면 [Path vs Shortest Path Micro Drill](./path-vs-shortest-path-micro-drill.md)
- `BFS가 왜 최소 이동 횟수인가`를 다시 붙이고 싶다면 [DFS와 BFS 입문](./dfs-bfs-intro.md)
- `0/1 비용`이 왜 별도 분기인지 궁금하면 [0-1 BFS grid-conversion primer](./zero-one-bfs-grid-conversion-primer.md)
- 일반 weighted shortest-path 전체 비교는 [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)

## 한 줄 정리

BFS는 `간선 수 최소`, Dijkstra는 `비용 합 최소`를 찾는다고 먼저 자르고, 그다음에만 0-1 BFS 같은 예외 분기를 붙이면 초보자 shortest-path 오분류가 크게 줄어든다.
