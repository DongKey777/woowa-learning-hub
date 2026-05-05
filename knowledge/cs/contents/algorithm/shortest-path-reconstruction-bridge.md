---
schema_version: 3
title: Shortest Path Reconstruction Bridge
concept_id: algorithm/shortest-path-reconstruction-bridge
canonical: false
category: algorithm
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- parent-array-update
- shortest-path-reconstruction
aliases:
- shortest path reconstruction
- path reconstruction beginner
- bfs path reconstruction
- dijkstra path reconstruction
- 0-1 bfs path reconstruction
- zero one bfs reconstruction
- predecessor array
- parent array shortest path
- prev array
- restore shortest path
- reconstruct route after shortest path
- bfs vs 0-1 bfs parent update
- bfs first visit vs relax
- 0-1 bfs relax update
- bfs 처음 방문 고정
symptoms:
- 최단 거리는 구했는데 실제 경로를 어떻게 복원하는지 모르겠어
- parent를 언제 갱신해야 하는지 BFS랑 다익스트라에서 헷갈려
- 거리표와 경로표를 같이 관리하는 그림이 안 잡혀
intents:
- comparison
prerequisites:
- algorithm/dfs-bfs-intro
- algorithm/dijkstra-bellman-ford-floyd-warshall
next_docs:
- algorithm/zero-one-bfs-implementation-mistake-check-template
- algorithm/sparse-graph-shortest-paths
linked_paths:
- contents/algorithm/dfs-bfs-intro.md
- contents/algorithm/zero-one-bfs-implementation-mistake-check-template.md
- contents/algorithm/zero-one-bfs-dist-vs-visited-counterexamples.md
- contents/algorithm/dijkstra-bellman-ford-floyd-warshall.md
- contents/algorithm/sparse-graph-shortest-paths.md
- contents/algorithm/graph.md
confusable_with:
- algorithm/dijkstra-bellman-ford-floyd-warshall
- algorithm/zero-one-bfs-state-visited-vs-dist-starter-card
forbidden_neighbors:
- contents/algorithm/bfs-vs-dijkstra-shortest-path-mini-card.md
expected_queries:
- BFS로 최단 거리만 구한 뒤 실제 경로를 출력하려면 무엇을 저장해야 해
- 다익스트라에서 predecessor 배열은 언제 바꾸는지 예시로 보고 싶어
- 0-1 BFS에서 parent 갱신 규칙이 BFS와 어떻게 다른지 설명해줘
- 최단 경로 복원할 때 target에서 start로 거꾸로 따라가는 흐름을 알고 싶어
- 거리 배열과 parent 배열을 같이 쓰는 shortest path 기본 패턴을 정리해줘
- 경로 출력 문제에서 first visit과 relax 성공을 어떻게 구분해야 해
contextual_chunk_prefix: |
  이 문서는 BFS, 0-1 BFS, Dijkstra에서 거리 계산과 실제 경로 복원을 어떻게 이어서 읽어야 하는지 연결하는 bridge다. 최단 거리만 구하고 끝내지 않고 어디서 왔는지 함께 적기, parent 배열을 거꾸로 따라 출발점까지 되짚기, 처음 방문 고정과 relax 갱신 차이, 거리표와 경로표를 한 장면으로 묶어 보기 같은 자연어 paraphrase가 본 문서의 핵심 연결에 매핑된다.
---
# Shortest Path Reconstruction Bridge

> 한 줄 요약: BFS, 0-1 BFS, Dijkstra는 "거리를 구하는 방법"은 다르지만, 실제 경로를 복원할 때는 결국 `parent` 또는 `predecessor` 배열을 거꾸로 따라가면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [DFS와 BFS 입문](./dfs-bfs-intro.md)
- [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)
- [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)
- [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)
- [그래프 관련 알고리즘](./graph.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: shortest path reconstruction, path reconstruction beginner, bfs path reconstruction, dijkstra path reconstruction, 0-1 bfs path reconstruction, zero one bfs reconstruction, predecessor array, parent array shortest path, prev array, restore shortest path, reconstruct route after shortest path, bfs vs 0-1 bfs parent update, bfs first visit vs relax, 0-1 bfs relax update, bfs 처음 방문 고정

## 먼저 잡을 그림

최단 거리 문제는 보통 두 단계로 본다.

1. `dist[]`에 시작점부터의 최소 거리를 채운다.
2. `parent[]`에 "이 정점에 오기 직전 정점"을 저장하고, 도착점에서 시작점까지 거꾸로 따라간다.

즉 BFS, 0-1 BFS, Dijkstra의 차이는 **거리표를 채우는 규칙**이고, 경로 복원 규칙은 거의 같다.

## 한눈에 비교

| 항목 | BFS | 0-1 BFS | Dijkstra |
|---|---|---|---|
| 쓰는 상황 | 무가중치, 모든 간선 비용이 같음 | 간선 비용이 0 또는 1 | 양수 가중치 |
| 거리 갱신 계기 | 처음 방문했을 때 | 더 짧은 경로를 찾았을 때 | 더 짧은 경로를 찾았을 때 |
| `parent[next]` 갱신 시점 | 큐에 처음 넣을 때 | relax 성공 시 | relax 성공 시 |
| 경로 복원 방법 | `target -> parent[target] -> ... -> start` | `target -> parent[target] -> ... -> start` | `target -> predecessor[target] -> ... -> start` |

## BFS에서 parent 저장

무가중치 그래프에서는 어떤 정점을 **처음 방문한 순간** 그 경로가 최단 경로다.
그래서 그때 부모를 기록하면 된다.

```text
dist[start] = 0
parent[start] = -1
queue <- start

while queue not empty
    cur = pop front
    for next in adj[cur]
        if next is not visited
            visited[next] = true
            dist[next] = dist[cur] + 1
            parent[next] = cur
            push next
```

예를 들어 `1 -> 2 -> 4`, `1 -> 3 -> 4` 그래프에서 BFS가 `2`를 먼저 통해 `4`를 처음 방문했다면 `parent[4] = 2`가 된다.
그러면 `4 -> 2 -> 1`을 뒤집어서 `1 -> 2 -> 4`를 얻는다.

## Dijkstra에서 predecessor 저장

다익스트라는 "처음 방문"이 아니라 **더 짧은 거리로 갱신될 때** 직전 정점을 바꾼다.
그래서 `predecessor[next] = cur`는 relax 성공과 같이 움직인다.

```text
dist[start] = 0
predecessor[start] = -1
pq <- (0, start)

while pq not empty
    cur = smallest-distance node
    for (next, weight) in adj[cur]
        newDist = dist[cur] + weight
        if newDist < dist[next]
            dist[next] = newDist
            predecessor[next] = cur
            push (newDist, next)
```

핵심은 "현재 더 좋은 경로를 찾았으니, 그 경로의 직전 정점도 함께 갈아끼운다"는 감각이다.

## 0-1 BFS도 복원 규칙은 같다

0-1 BFS는 deque를 쓰지만, 경로 복원 관점에서는 Dijkstra 쪽 감각에 더 가깝다.
즉 `next`를 **처음 넣었는지**보다, `dist[next]`가 **정말 더 좋아졌는지**를 보고 부모를 바꾼다.

```text
dist[start] = 0
parent[start] = -1
deque <- front(start)

while deque not empty
    cur = pop front
    for (next, cost) in adj[cur]   // cost is 0 or 1
        newDist = dist[cur] + cost
        if newDist < dist[next]
            dist[next] = newDist
            parent[next] = cur
            if cost == 0
                push front(next)
            else
                push back(next)
```

초보자용으로 아주 짧게만 기억하면 이렇다.

| 알고리즘 | `parent[next]`를 언제 바꾸나 |
|---|---|
| BFS | `next`를 처음 방문했을 때 |
| 0-1 BFS | relax 성공으로 `dist[next]`가 줄었을 때 |
| Dijkstra | relax 성공으로 `dist[next]`가 줄었을 때 |

예를 들어 `1 -> 2 (1)`, `1 -> 3 (0)`, `3 -> 2 (0)`이면,
처음에는 `parent[2] = 1`, `dist[2] = 1`일 수 있다.
하지만 `3`을 거쳐 `2`로 가면 `newDist = 0`이 되므로 `parent[2]`를 `3`으로 바꿔야 한다.
deque를 쓴다고 해서 "처음 본 부모를 고정"하는 게 아니라, **더 싼 경로가 나오면 부모도 같이 갱신**한다고 보면 된다.

### 왜 `visited`를 BFS처럼 영구 고정하면 틀리나

`0-1 BFS`는 이름에 BFS가 들어가도, 판단 기준은 `처음 넣었는가`가 아니라 `더 짧아졌는가`다.
그래서 아래처럼 `visited[next] = true`를 첫 삽입에 고정하는 코드는 반례를 놓친다.

| 비교 포인트 | 잘못된 BFS식 습관 | 맞는 0-1 BFS식 relax |
|---|---|---|
| 갱신 기준 | `visited[next]`가 false면 1회만 처리 | `newDist < dist[next]`면 다시 갱신 |
| 실수 결과 | 첫 삽입이 영구 고정된다 | 더 싼 경로가 늦게 와도 반영된다 |

```text
// 잘못된 예시
for (next, cost) in adj[cur]
    if visited[next]
        continue
    visited[next] = true
    dist[next] = dist[cur] + cost
    parent[next] = cur
```

## 0-1 BFS도 복원 규칙은 같다 (계속 2)

```text
// 맞는 예시
for (next, cost) in adj[cur]
    newDist = dist[cur] + cost
    if newDist < dist[next]
        dist[next] = newDist
        parent[next] = cur
        if cost == 0
            push front(next)
        else
            push back(next)
```

왼쪽 코드는 `1 -> 2 (1)`을 먼저 보면 `visited[2] = true`가 되어, 나중에 `1 -> 3 (0) -> 2 (0)`의 더 싼 경로를 만나도 `2`를 다시 갱신하지 못한다.
초보자 기준으로는 "`visited`가 정답을 지키는 배열"이 아니라, `dist`가 줄어들었는지를 보는 문제가 0-1 BFS라고 기억하면 안전하다.

## 오해 방지 반례 한 장 표

초보자가 가장 자주 헷갈리는 문장은 이것이다.

- BFS: "처음 큐에 들어간 경로가 최단이니 그대로 고정해도 된다."
- 0-1 BFS: "deque를 쓰니까 BFS처럼 처음 본 경로를 고정하면 되겠지?"

두 번째 문장이 틀리는 반례를 한 번에 보면 감각이 빨라진다.

| 단계 | BFS에서 가능한 사고방식 | 0-1 BFS에서 실제로 해야 할 일 |
|---|---|---|
| 예시 그래프 | `1 -> 2`, `1 -> 3`, `3 -> 2`처럼 모든 간선 비용이 같다고 본다 | `1 -> 2 (1)`, `1 -> 3 (0)`, `3 -> 2 (0)`처럼 비용이 다르다 |
| `1`에서 첫 확장 | `2`, `3` 모두 거리 1이므로 먼저 들어간 쪽을 써도 안전하다 | `2`는 거리 1, `3`은 거리 0이다. 같은 "한 번 이동"처럼 보여도 비용은 다르다 |
| `2`를 처음 만난 순간 | `dist[2] = 1`, `parent[2] = 1`로 고정 가능 | 일단 `dist[2] = 1`, `parent[2] = 1`로 들어갈 수는 있지만 아직 확정이 아니다 |
| 나중에 `3 -> 2` 확인 | `1 -> 3 -> 2`도 거리 2라서 더 나쁘다. 갱신할 이유가 없다 | `1 -> 3 -> 2`의 비용은 `0 + 0 = 0`이라 더 좋다. `dist[2] = 0`, `parent[2] = 3`으로 바꿔야 한다 |
| 결론 | **처음 방문 고정**이 맞다 | **relax 성공 시 재갱신**이 맞다 |

같은 내용을 배열 변화만 떼어 놓고 보면 더 선명하다.

| 순간 | BFS | 0-1 BFS |
|---|---|---|
| `1 -> 2`를 먼저 봤을 때 | `dist[2] = 1`, `parent[2] = 1` | `dist[2] = 1`, `parent[2] = 1` |
| `1 -> 3 -> 2`를 나중에 봤을 때 | 유지 | `dist[2] = 0`, `parent[2] = 3`으로 갱신 |

즉 "queue냐 deque냐"가 본질이 아니라, **처음 방문이 최단이라고 말할 수 있는 문제인지**, 아니면 **더 싼 경로가 뒤늦게 나올 수 있는 문제인지**가 본질이다.
이 기준으로 보면 BFS는 방문 고정, 0-1 BFS와 Dijkstra는 relax 갱신 쪽으로 묶인다.

## 복원 함수는 거의 같다

둘 다 아래처럼 도착점에서 시작점으로 거꾸로 걷고, 마지막에 뒤집으면 된다.

```text
path = []
cur = target

while cur != -1
    path.add(cur)
    cur = parent[cur]

reverse(path)
```

`parent[target] == -1`인데 `target != start`라면, 보통은 시작점에서 도달하지 못한 상태다.

## 입문자가 자주 헷갈리는 부분

- `dist[]`만 있으면 길이를 알 수 있지만, 실제 경로는 모른다. 경로 자체가 필요하면 `parent[]`도 같이 저장해야 한다.
- BFS에서는 보통 부모를 한 번만 정한다. 처음 방문이 최단이기 때문이다.
- 0-1 BFS에서는 부모가 바뀔 수 있다. `0 edge`를 통해 더 싼 경로가 뒤늦게 발견될 수 있기 때문이다.
- Dijkstra에서는 더 짧은 경로가 나오면 부모가 바뀔 수 있다.
- 0-1 BFS에서 `visited[next] = true`를 BFS처럼 "첫 삽입 시 영구 고정"해 버리면 반례를 놓친다. 이 문서의 반례 표처럼 `dist` 비교와 relax가 먼저다.
- 같은 최단 경로가 여러 개면, 어떤 경로가 복원되는지는 인접 리스트 순서나 PQ 처리 순서에 따라 달라질 수 있다.

## 이렇게 연결해서 기억하면 쉽다

- BFS: "처음 도착한 길이 최단이므로 그때 부모를 적는다."
- 0-1 BFS: "0/1 비용이지만 본질은 relax이므로, 더 짧아질 때 부모를 고친다."
- Dijkstra: "더 싼 길을 찾을 때마다 부모를 새로 적는다."

셋 다 결국은 **거리표 + 직전 정점표**로 생각하면 된다.

## 다음에 읽으면 좋은 문서

- BFS가 왜 무가중치 최단 경로가 되는지부터 다시 잡으려면 [DFS와 BFS 입문](./dfs-bfs-intro.md)
- Java/Python 기준으로 `dist`, `deque`, `parent` 갱신 위치를 한 번에 보려면 [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- `0-1 BFS`의 `dist vs visited` 반례만 아주 짧게 복습하려면 [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)
- 어떤 최단 경로 알고리즘을 골라야 하는지 비교하려면 [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)
- `0-1 BFS`, `Dial`, 희소 그래프 변형까지 이어 보려면 [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)
- `deque`라는 단어 때문에 sliding window 쪽으로 새는지부터 먼저 막으려면 [Deque Router Example Pack](../data-structure/deque-router-example-pack.md)

## 한 줄 정리

BFS, 0-1 BFS, Dijkstra는 "거리를 구하는 방법"은 다르지만, 실제 경로를 복원할 때는 결국 `parent` 또는 `predecessor` 배열을 거꾸로 따라가면 된다.
