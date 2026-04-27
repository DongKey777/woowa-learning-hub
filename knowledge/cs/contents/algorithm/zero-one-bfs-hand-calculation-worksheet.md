# 0-1 BFS 손계산 워크시트

> 한 줄 요약: `0-1 BFS`는 "비용이 그대로면 앞, 비용이 1 늘면 뒤"만 지키면서 `dist`와 deque를 같이 추적하면 손으로도 충분히 따라갈 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [DFS와 BFS 입문](./dfs-bfs-intro.md)
- [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)
- [0-1 BFS stale-entry mini card](./zero-one-bfs-stale-entry-mini-card.md)
- [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)
- [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)

retrieval-anchor-keywords: 0-1 bfs worksheet, zero one bfs worksheet, 0-1 bfs hand calculation, zero one bfs hand trace, 0-1 bfs deque trace, 0-1 bfs dist trace, 0-1 bfs beginner walkthrough, 0-1 bfs worked example, 0-1 bfs step by step, 0-1 bfs manual simulation, 0-1 bfs deque state, 0-1 bfs dist update, 0-1 bfs stale entry, deque shortest path worksheet, deque shortest path trace, binary weight shortest path worksheet, teleport shortest path worksheet, 0/1 shortest path worksheet, 0-1 bfs 손계산, 0-1 bfs 추적, 0-1 bfs 덱 상태, 0-1 bfs 거리표 변화, 0-1 bfs 줄 단위 예제, 0-1 bfs 입문 예제, 덱 최단 경로 워크시트, 순간이동 최단 경로 손계산

## 먼저 잡을 그림

`0-1 BFS`를 손으로 계산할 때는 deque를 "두 칸짜리 대기열"처럼 보면 쉽다.

- 앞쪽: **현재 거리 그대로** 처리할 후보
- 뒤쪽: **현재 거리 + 1**이 된 후보

그래서 규칙은 세 줄이면 충분하다.

- `newDist < dist[next]`일 때만 갱신한다.
- 간선 비용이 `0`이면 deque 앞에 넣는다.
- 간선 비용이 `1`이면 deque 뒤에 넣는다.

이 문서에서는 deque 안의 상태를 `정점@그때의거리`로 적는다.
실제 코드에서는 정점만 넣는 구현도 많지만, 손계산에서는 오래된 항목과 최신 항목을 구분하기 쉬워진다.

## 초미니 deque 업데이트 카드

한 번만 눈에 익히면 되는 핵심 장면만 먼저 보면 이렇다.

```text
시작: deque = [S@0], dist[A] = INF, dist[B] = INF

1) S -> A 비용 1
   newDist = 1
   dist[A] = 1로 갱신
   push_back(A@1)
   deque = [A@1]

2) S -> B 비용 0
   newDist = 0
   dist[B] = 0으로 갱신
   push_front(B@0)
   deque = [B@0, A@1]
```

| 방금 본 행동 | 거리 변화 | deque 동작 | 한 줄 기억 |
|---|---|---|---|
| `S -> A (1)` | `dist[A]: INF -> 1` | `push_back(A@1)` | 비용 `1`은 다음 거리층이라 뒤 |
| `S -> B (0)` | `dist[B]: INF -> 0` | `push_front(B@0)` | 비용 `0`은 현재 거리층이라 앞 |

즉 `push_front`와 `push_back`은 "자료구조 테크닉"이 아니라,
`dist`가 그대로인지 `+1`인지에 맞춰 처리 순서를 보존하는 장치다.

## 예제 그래프

```text
S --(1)--> A --(1)--> C --(0)--> T
|          \                      ^
|           --(1)----------------|
|
--(0)--> B --(0)--> A
           \
            --(1)--> C
```

시작점은 `S`다.

간선 표로 다시 쓰면 아래와 같다.

| 출발 | 도착 | 비용 |
|---|---|---|
| `S` | `A` | `1` |
| `S` | `B` | `0` |
| `B` | `A` | `0` |
| `B` | `C` | `1` |
| `A` | `C` | `1` |
| `A` | `T` | `1` |
| `C` | `T` | `0` |

초기 상태:

- `dist[S] = 0`
- 나머지는 `INF`
- deque = `[S@0]`

## 줄 단위 워크시트

| step | 꺼낸 상태 | 이번 줄에서 일어난 일 | deque 상태 (front -> back) | `dist[A]` | `dist[B]` | `dist[C]` | `dist[T]` |
|---|---|---|---|---:|---:|---:|---:|
| 0 | 시작 전 | `S@0`만 넣고 시작 | `[S@0]` | `INF` | `INF` | `INF` | `INF` |
| 1 | `S@0` | `A`는 비용 `1`이라 뒤에 `A@1`, `B`는 비용 `0`이라 앞에 `B@0` | `[B@0, A@1]` | `1` | `0` | `INF` | `INF` |
| 2 | `B@0` | `A`를 비용 `0`으로 더 싸게 가서 `A@0`을 앞에 넣음, `C@1`은 뒤에 넣음 | `[A@0, A@1, C@1]` | `0` | `0` | `1` | `INF` |
| 3 | `A@0` | `C`는 새 거리도 `1`이라 그대로, `T@1`을 뒤에 넣음 | `[A@1, C@1, T@1]` | `0` | `0` | `1` | `1` |
| 4 | `A@1` | 오래된 항목이다. 현재 `dist[A] = 0`이라 더 볼 이득이 없다 | `[C@1, T@1]` | `0` | `0` | `1` | `1` |
| 5 | `C@1` | `C -> T (0)`을 봐도 새 거리는 `1`이라 변화 없음 | `[T@1]` | `0` | `0` | `1` | `1` |
| 6 | `T@1` | 도착 정점 처리 완료 | `[]` | `0` | `0` | `1` | `1` |

## 왜 이 예제가 좋은가

초보자가 자주 헷갈리는 장면이 한 번에 다 나온다.

| 장면 | 이 예제에서 보이는 위치 | 핵심 해석 |
|---|---|---|
| `0 edge`는 왜 앞에 넣나 | step 1의 `S -> B`, step 2의 `B -> A` | 같은 거리층 후보를 먼저 처리해야 더 싼 경로가 밀리지 않는다 |
| 첫 방문이 최단이 아닐 수 있나 | step 1에서 `A=1`, step 2에서 `A=0` | `visited` 고정보다 `dist` 비교가 먼저다 |
| deque에 같은 정점이 두 번 들어가도 되나 | step 2 이후 `[A@0, A@1, C@1]` | 예전 값이 남아 있어도 최신 `dist`가 더 작으면 오래된 항목은 무해하다 |

## 손으로 풀 때 체크 순서

매 줄마다 아래 순서만 반복하면 된다.

1. deque 맨 앞을 꺼낸다.
2. 그 정점에서 나가는 간선을 한 줄씩 본다.
3. `newDist < dist[next]`인지 확인한다.
4. 더 짧아졌으면 `dist[next]`를 고친다.
5. 비용이 `0`이면 앞, `1`이면 뒤에 넣는다.

초보자는 `visited`를 먼저 적지 말고, `dist` 표를 먼저 적는 편이 덜 헷갈린다.

## 직접 다시 적어보는 빈 템플릿

아래 표를 복사해서 위 풀이를 가리고 한 번 더 채워 보면 감각이 빨리 붙는다.

| step | 꺼낸 상태 | 이번 줄에서 일어난 일 | deque 상태 (front -> back) | `dist[A]` | `dist[B]` | `dist[C]` | `dist[T]` |
|---|---|---|---|---:|---:|---:|---:|
| 0 |  |  |  |  |  |  |  |
| 1 |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |
| 4 |  |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |  |
| 6 |  |  |  |  |  |  |  |

## 자주 헷갈리는 포인트

- `A@1`처럼 오래된 항목이 나와도 panic할 필요는 없다. 최신 `dist[A]`만 보면 된다.
- `newDist == dist[next]`면 보통 다시 넣지 않는다. 이 워크시트도 그 규칙을 따른다.
- `0-1 BFS`는 이름에 BFS가 들어가도 "처음 봤으니 끝"이 아니라 "더 짧아졌나"를 계속 본다.

`A@1`이 왜 무해한지 그 장면만 더 작게 떼어서 보고 싶다면 [0-1 BFS stale-entry mini card](./zero-one-bfs-stale-entry-mini-card.md)를 바로 이어서 보면 된다.

## 다음 연결

- `visited`를 먼저 쓰면 왜 틀리는지 반례부터 보고 싶으면 [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)
- 실제 코드 뼈대에서 `dist`, `parent`, deque가 어디서 같이 움직이는지 보려면 [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- `0-1 BFS`를 Dijkstra, Dial과 언제 구분해서 쓰는지 보려면 [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)
