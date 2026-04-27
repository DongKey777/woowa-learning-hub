# 0-1 BFS 구현 실수 체크 템플릿

> 한 줄 요약: `0-1 BFS` 구현에서 초보자가 가장 많이 틀리는 위치는 `dist`, `deque`, `parent` 갱신 순서다.

**난이도: 🟢 Beginner**

관련 문서:

- [0-1 BFS 손계산 워크시트](./zero-one-bfs-hand-calculation-worksheet.md)
- [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)
- [0-1 BFS stale-entry mini card](./zero-one-bfs-stale-entry-mini-card.md)
- [0-1 BFS equal-distance reinsert mini note](./zero-one-bfs-equal-distance-reinsert-mini-note.md)
- [0-1 BFS parent tie mini note](./zero-one-bfs-parent-tie-mini-note.md)
- [0-1 BFS lexicographic tie mini note](./zero-one-bfs-lexicographic-tie-mini-note.md)
- [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)
- [DFS와 BFS 입문](./dfs-bfs-intro.md)

retrieval-anchor-keywords: 0-1 bfs implementation template, zero one bfs template, 0-1 bfs java template, 0-1 bfs python template, 0-1 bfs dist deque parent, zero one bfs dist deque parent, 0-1 bfs beginner template, 0-1 bfs relax template, 0-1 bfs parent update template, 0-1 bfs deque push front back, 0-1 bfs code skeleton, 0-1 bfs checklist, 0-1 bfs equal distance, 0-1 bfs newDist == dist, 0-1 bfs same distance no reinsertion, 0-1 bfs 구현 템플릿, 0-1 bfs 자바 템플릿, 0-1 bfs 파이썬 템플릿, 0-1 bfs dist 갱신, 0-1 bfs deque 갱신, 0-1 bfs parent 갱신, 0-1 bfs relax 위치, 0-1 bfs 초보 템플릿, 0-1 bfs 실수 체크, 0-1 bfs 같은 거리 다시 넣기, 0-1 bfs parent tie, 0-1 bfs 같은 거리 parent, 0-1 bfs lexicographic tie, 0-1 bfs 사전순 경로

## 먼저 외울 규칙 3개

- `dist[next]`는 "처음 봤는가"가 아니라 "더 짧아졌는가"로 갱신한다.
- `cost == 0`이면 덱 앞, `cost == 1`이면 덱 뒤에 넣는다.
- `dist[next]`가 줄어드는 순간 `parent[next]`도 같은 줄에서 같이 바꾼다.
- beginner 기본형은 보통 `newDist == dist[next]`일 때 다시 넣지 않고, `newDist < dist[next]`만 처리한다.

초보자 기준으로는 이 네 줄만 안 섞이면 큰 실수 대부분이 사라진다.

## 한눈에 보는 체크 표

| 확인할 것 | 맞는 위치 | 자주 하는 실수 |
|---|---|---|
| `dist[next]` | `newDist < dist[next]`일 때만 갱신 | `visited[next]`를 먼저 고정 |
| `parent[next]` | `dist[next]`를 갱신한 바로 아래 | 첫 방문 때 한 번만 기록 |
| `deque` | `cost == 0`이면 `front`, `cost == 1`이면 `back` | 둘 다 뒤에 넣음 |

## Java 템플릿

```java
import java.util.*;

class Edge {
    int to;
    int cost; // 0 or 1

    Edge(int to, int cost) {
        this.to = to;
        this.cost = cost;
    }
}

int[] zeroOneBfs(List<Edge>[] graph, int start, int[] parent) {
    int n = graph.length;
    int INF = Integer.MAX_VALUE;
    int[] dist = new int[n];
    Arrays.fill(dist, INF);
    Arrays.fill(parent, -1);

    Deque<Integer> deque = new ArrayDeque<>();
    dist[start] = 0;
    deque.addFirst(start);

    while (!deque.isEmpty()) {
        int cur = deque.pollFirst();

        for (Edge edge : graph[cur]) {
            int next = edge.to;
            int newDist = dist[cur] + edge.cost;

            if (newDist < dist[next]) {
                dist[next] = newDist;   // 1. 거리 갱신
                parent[next] = cur;     // 2. 부모 갱신

                if (edge.cost == 0) {
                    deque.addFirst(next); // 3. 0이면 앞
                } else {
                    deque.addLast(next);  // 4. 1이면 뒤
                }
            }
        }
    }

    return dist;
}
```

## Python 템플릿

```python
from collections import deque


def zero_one_bfs(graph, start):
    n = len(graph)
    INF = 10**18
    dist = [INF] * n
    parent = [-1] * n

    dq = deque()
    dist[start] = 0
    dq.appendleft(start)

    while dq:
        cur = dq.popleft()

        for nxt, cost in graph[cur]:  # cost is 0 or 1
            new_dist = dist[cur] + cost

            if new_dist < dist[nxt]:
                dist[nxt] = new_dist   # 1. 거리 갱신
                parent[nxt] = cur      # 2. 부모 갱신

                if cost == 0:
                    dq.appendleft(nxt)  # 3. 0이면 앞
                else:
                    dq.append(nxt)      # 4. 1이면 뒤

    return dist, parent
```

## 어디를 보면 되나

초보자가 코드를 점검할 때는 `for` 루프 안을 아래 순서로만 보면 된다.

```text
newDist 계산
-> 더 짧은가 비교
-> dist 갱신
-> parent 갱신
-> 0이면 앞 / 1이면 뒤
```

즉 `parent`를 따로 갱신하는 알고리즘이 아니라, **relax 성공 블록 안에서 세트로 움직이는 알고리즘**이라고 보면 된다.

손으로 먼저 추적해 보고 싶다면 [0-1 BFS 손계산 워크시트](./zero-one-bfs-hand-calculation-worksheet.md)의 deque / `dist` 표를 바로 옆에 두고 같이 보면 된다.
특히 `push_front`와 `push_back`이 `dist` 변화와 어떻게 짝을 이루는지만 먼저 보고 싶다면, 같은 문서의 초미니 deque 업데이트 카드부터 보면 빠르다.

## 가장 흔한 오답 패턴

### 1. `visited`를 BFS처럼 먼저 고정

```text
if visited[next]:
    continue
visited[next] = true
```

이 패턴은 `0-1 BFS`에서 위험하다.
핵심 조건은 `visited`가 아니라 `newDist < dist[next]`다.

### 2. `parent`를 갱신하지 않음

`dist[next]`만 줄이고 `parent[next]`를 안 바꾸면, 최단 거리는 맞아도 복원 경로가 틀릴 수 있다.

### 3. `0 edge`도 뒤에 넣음

이러면 "더 싼 후보를 먼저 처리"하는 흐름이 깨진다.

### 4. deque에 같은 정점이 두 번 들어가면 무조건 버그라고 생각

`A@1` 뒤에 `A@0`이 다시 들어오는 장면은 `0-1 BFS`에서 자연스럽다.
중요한 것은 중복 자체가 아니라, 최신 `dist`가 더 작은 값을 유지하느냐다.

### 5. 같은 거리 후보도 꼭 다시 넣어야 한다고 생각

초보자용 최단 거리 기본형에서는 보통 아니다.
`newDist == dist[next]`는 개선이 아니라 동점이라서, 대개 `newDist < dist[next]`만으로 충분하다.
이 감각만 따로 짧게 보려면 [0-1 BFS equal-distance reinsert mini note](./zero-one-bfs-equal-distance-reinsert-mini-note.md)를 이어서 보면 된다.

### 6. 같은 거리 후보가 나오면 `parent[next]`도 꼭 갈아껴야 한다고 생각

이것도 beginner 기본형에서는 보통 아니다.
최단 거리 하나와 그 경로 하나만 복원하면 된다면, 이미 기록된 최단 부모 하나로 충분하다.
즉 보통은 `newDist < dist[next]`일 때만 `parent[next] = cur`를 같이 수행한다.

동점 parent 규칙만 분리해서 다시 보고 싶다면 [0-1 BFS parent tie mini note](./zero-one-bfs-parent-tie-mini-note.md)로 이어가면 된다.
다만 문제에서 "사전순으로 가장 작은 경로"를 강제하면 예외가 생길 수 있으니, 그 경우는 [0-1 BFS lexicographic tie mini note](./zero-one-bfs-lexicographic-tie-mini-note.md)를 같이 보는 편이 안전하다.

## 복원까지 같이 볼 때 기억할 한 줄

- BFS: 첫 방문 때 `parent` 고정
- 0-1 BFS: relax 성공 때 `parent` 갱신
- Dijkstra: relax 성공 때 `parent` 갱신

0-1 BFS는 이름보다 동작을 기준으로 보면, `parent` 갱신 감각이 BFS보다 Dijkstra 쪽에 더 가깝다.

## 같이 보면 좋은 문서

- 반례를 먼저 보고 싶으면 [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)
- 오래된 deque 항목이 왜 harmless한지 한 장만 더 보려면 [0-1 BFS stale-entry mini card](./zero-one-bfs-stale-entry-mini-card.md)
- `newDist == dist[next]`일 때 왜 보통 재삽입이 필요 없는지 보려면 [0-1 BFS equal-distance reinsert mini note](./zero-one-bfs-equal-distance-reinsert-mini-note.md)
- 같은 거리 후보에서 `parent[next]`를 왜 보통 그대로 두는지 보려면 [0-1 BFS parent tie mini note](./zero-one-bfs-parent-tie-mini-note.md)
- 줄 단위 deque 변화와 오래된 항목 처리까지 보고 싶으면 [0-1 BFS 손계산 워크시트](./zero-one-bfs-hand-calculation-worksheet.md)
- `parent[]`로 경로를 실제 복원하는 흐름은 [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- `0-1 BFS`와 Dijkstra를 언제 고르는지는 [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)
