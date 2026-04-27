# BFS vs 0-1 BFS vs Dijkstra shortest path mini card

> 한 줄 요약: `모든 이동이 같으면 BFS`, `비용이 0 또는 1만 섞이면 0-1 BFS`, `그보다 일반 가중치면 Dijkstra`로 먼저 자르면 초보자 분기가 쉬워진다.

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

## 먼저 한 줄로 자르기

- 모든 간선 비용이 같으면: BFS
- 간선 비용이 `0` 또는 `1`만 나오면: 0-1 BFS
- `2`, `5`, `10` 같은 일반 가중치가 나오면: Dijkstra

초보자 기준으로는 `무엇을 최소화하나`와 `간선 비용이 몇 종류인가`를 먼저 분리하면 된다.

## 한 표로 바로 구분하기

| 알고리즘 | 간선 비용 | 보통 최소화하는 것 | 핵심 자료구조 | 첫 질문 |
|---|---|---|---|---|
| BFS | 전부 동일, 보통 `1` | 이동 횟수, 간선 수 | 큐 | "모든 이동이 같은 한 걸음인가?" |
| 0-1 BFS | `0` 또는 `1`만 존재 | 0/1 비용 합 | deque | "공짜 이동과 유료 이동만 섞였나?" |
| Dijkstra | 0 이상 일반 가중치 | 일반 비용 합 | 우선순위 큐 | "`2`, `5` 같은 비용도 나오나?" |

문제를 읽고 위 표의 첫 질문에 답하면 대부분 첫 선택이 정리된다.

## 같은 그래프를 세 번 읽어 보기

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

이 예제는 `0-1 BFS`와 Dijkstra가 답을 공유할 수 있어도, `0-1 BFS`는 "가중치가 0/1뿐"이라는 특수 조건을 이용해 더 단순하게 푸는 선택지라는 점을 보여 준다.

## 왜 세 알고리즘이 갈리나

- BFS는 큐로 레벨을 넓혀 가므로 "먼저 도착한 레벨"이 최소 간선 수다.
- 0-1 BFS는 deque에서 비용 `0` 간선을 앞에, 비용 `1` 간선을 뒤에 넣어 `0/1 비용 합` 순서를 유지한다.
- Dijkstra는 우선순위 큐에서 "현재까지 비용이 가장 작은 후보"를 먼저 꺼내 일반 가중치까지 처리한다.

짧게 외우면 이렇다.

| 알고리즘 | 무엇을 최소화하나 | 대표 질문 |
|---|---|---|
| BFS | 간선 수 | 최소 칸 수, 최소 이동 횟수 |
| 0-1 BFS | 0/1 비용 합 | 순간이동 0초, 벽 부수기 1회, 무료/유료 이동 |
| Dijkstra | 일반 가중치 합 | 최소 비용, 최소 시간, 최소 요금 |

## 자주 하는 착각

- "BFS는 최단 경로 알고리즘이니까 가중치 그래프에도 된다" -> 아니다. BFS는 간선 비용이 모두 같을 때만 안전하다.
- "`0`과 `1`만 있으니 Dijkstra만 쓰면 된다" -> 맞게 풀 수는 있지만, 문제 조건을 더 직접 쓰는 쪽은 0-1 BFS다.
- "간선이 1개면 항상 더 짧다" -> 비용 문제에서는 틀릴 수 있다. `1개짜리 비싼 길`보다 `2개짜리 싼 길`이 더 좋을 수 있다.
- "가중치가 전부 1이면 Dijkstra만 써야 한다" -> 아니다. 이때는 BFS가 더 단순하다.

## 이렇게 고르면 덜 헷갈린다

1. 답이 `최소 이동 횟수`인가? 그러면 BFS부터 본다.
2. 답이 `최소 비용 합`인데 비용이 `0/1`뿐인가? 그러면 0-1 BFS부터 본다.
3. 비용이 `0/1`을 넘어서 더 다양하게 나오나? 그러면 Dijkstra로 간다.
4. 가중치가 모두 `1`인가? 그러면 비용 문제처럼 보여도 BFS로 줄일 수 있다.

## 한 줄 정리

BFS는 `간선 수 최소`, 0-1 BFS는 `0/1 비용 합 최소`, Dijkstra는 `일반 가중치 합 최소`를 찾는다고 기억하면 초보자도 shortest-path 분기를 한 표로 설명할 수 있다.
