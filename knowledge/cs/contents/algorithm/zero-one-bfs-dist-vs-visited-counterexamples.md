---
schema_version: 3
title: 0-1 BFS dist vs visited 미니 반례 카드
concept_id: algorithm/zero-one-bfs-dist-vs-visited-counterexamples
canonical: false
category: algorithm
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- visited-vs-dist-choice
- zero-cost-revisit
aliases:
- 0-1 bfs dist vs visited
- zero one bfs dist visited
- 0-1 bfs counterexample
- 0-1 bfs beginner mistake
- 0-1 bfs visited bug
- 0-1 bfs relax first visit
- 0-1 bfs parent update
- deque shortest path visited
- binary weight shortest path visited
- 0-1 bfs first-visit trap
- 0-1 bfs dist relax rule
- 0-1 bfs appendleft rule
- 0-1 bfs beginner primer
- 0/1 cost shortest path relax
- dist visited choice basics
symptoms:
- visited로 막았더니 더 짧은 경로를 놓쳐
- 0-1 BFS인데 BFS처럼 처음 방문에서 끝내고 있어
- 왜 dist를 보고 다시 넣는지 반례로 확인하고 싶어
intents:
- comparison
- design
prerequisites:
- algorithm/dfs-bfs-intro
- algorithm/zero-one-bfs-grid-conversion-primer
next_docs:
- algorithm/zero-one-bfs-state-visited-vs-dist-starter-card
- algorithm/zero-one-bfs-hand-calculation-worksheet
- algorithm/zero-one-bfs-implementation-mistake-check-template
linked_paths:
- contents/algorithm/dfs-bfs-intro.md
- contents/algorithm/zero-one-bfs-grid-conversion-primer.md
- contents/algorithm/zero-one-bfs-state-visited-vs-dist-starter-card.md
- contents/algorithm/zero-one-bfs-stale-entry-mini-card.md
- contents/algorithm/zero-one-bfs-equal-distance-reinsert-mini-note.md
- contents/algorithm/zero-one-bfs-hand-calculation-worksheet.md
- contents/algorithm/zero-one-bfs-implementation-mistake-check-template.md
- contents/algorithm/shortest-path-reconstruction-bridge.md
- contents/algorithm/sparse-graph-shortest-paths.md
- contents/algorithm/dijkstra-bellman-ford-floyd-warshall.md
- contents/data-structure/deque-basics.md
confusable_with:
- algorithm/zero-one-bfs-state-visited-vs-dist-starter-card
- algorithm/dfs-bfs-intro
- algorithm/zero-one-bfs-grid-conversion-primer
forbidden_neighbors:
expected_queries:
- 0-1 BFS에서 visited만 쓰면 왜 오답이 되는지 작은 반례로 보고 싶어
- 처음 도착한 값보다 더 싼 경로가 나오는 0-1 BFS 예시를 설명해줘
- 3차원 상태 문제에서도 첫 방문 고정이 왜 위험한지 반례 느낌으로 이해하고 싶어
- appendleft와 dist 갱신을 같이 봐야 하는 이유를 beginner 관점에서 알고 싶어
- BFS 습관대로 첫 방문 고정을 넣었더니 틀릴 때 어디를 의심해야 해
- 0비용 간선 때문에 재방문이 필요한 상황을 한 번에 이해하고 싶어
contextual_chunk_prefix: |
  이 문서는 0-1 BFS를 처음 배우는 학습자가 visited처럼 한 번 보고
  끝낼지, dist를 계속 비교하며 갱신할지 판단 기준을 골라주는 chooser다.
  처음 본 정점인데 왜 또 바뀌지, 방문 체크로 막으면 왜 틀리지, 비용
  0은 왜 앞쪽 처리지, 더 싼 경로가 나오면 다시 바꾸기, deque 순서와
  거리 갱신 관계 같은 자연어 paraphrase가 본 문서의 핵심 대비에
  매핑된다.
---
# 0-1 BFS dist vs visited 미니 반례 카드

> 한 줄 요약: `0-1 BFS`는 이름에 BFS가 들어가도 "처음 봤으니 visited로 고정"이 아니라 "`dist`가 더 줄어드나?"를 계속 보는 문제다.

**난이도: 🟢 Beginner**

관련 문서:

- [DFS와 BFS 입문](./dfs-bfs-intro.md)
- [State-space visited vs dist starter card](./zero-one-bfs-state-visited-vs-dist-starter-card.md)
- [0-1 BFS stale-entry mini card](./zero-one-bfs-stale-entry-mini-card.md)
- [0-1 BFS equal-distance reinsert mini note](./zero-one-bfs-equal-distance-reinsert-mini-note.md)
- [0-1 BFS 손계산 워크시트](./zero-one-bfs-hand-calculation-worksheet.md)
- [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)
- [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)
- [Deque Basics](../data-structure/deque-basics.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: 0-1 bfs dist vs visited, zero one bfs dist visited, 0-1 bfs counterexample, 0-1 bfs beginner mistake, 0-1 bfs visited bug, 0-1 bfs relax first visit, 0-1 bfs parent update, deque shortest path visited, binary weight shortest path visited, 처음 0-1 bfs 왜 visited 아니지, 왜 dist 로 보나요, 언제 appendleft 하죠, 뭐예요 0-1 bfs basics, 0/1 cost shortest path relax, 처음 dist visited 차이

이 문서는 이런 증상에서 바로 펼치면 된다.

- `처음 방문했는데 왜 또 갱신돼?`
- `왜 visited로 막으면 틀리지?`
- `왜 0 비용은 앞에 넣어야 하지?`

## 먼저 떠올릴 그림

`visited`는 "들어가 봤다" 표시이고, `dist`는 "얼마나 싸게 왔나" 기록이다.
0-1 BFS는 출석 체크보다 영수증 비교에 가깝다.

| 배열 | 보는 질문 | 0-1 BFS에서 더 중요한 쪽 |
|---|---|---|
| `visited[]` | 본 적 있나 | 덜 중요 |
| `dist[]` | 더 싸게 올 수 있나 | 더 중요 |

한 줄 비유로 외우면 더 쉽다.

- BFS는 `출석 체크`
- 0-1 BFS는 `더 싼 영수증이 있으면 갈아끼우기`

## 먼저 한 문장으로 잡기

초보자 기준으로는 이렇게 구분하면 된다.

- BFS: **처음 방문한 순간 최단 거리 확정**
- 0-1 BFS: **처음 방문은 임시값일 뿐, 더 싼 경로가 나오면 갱신**

즉 `visited`보다 먼저 보는 배열은 `dist[]`다.

상태 공간 문제라면 이 문장을 `dist[r][c][state]`까지 그대로 확장해서 보면 된다.
"언제 3차원 `visited`만으로 충분한가?"를 먼저 분리해 보고 싶으면 [State-space visited vs dist starter card](./zero-one-bfs-state-visited-vs-dist-starter-card.md)를 같이 보면 연결이 빠르다.

## 증상 문구로 먼저 잡기

코드를 보거나 문제를 풀 때 아래 말이 머리에 떠오르면 `dist`를 다시 확인하면 된다.

| 떠오르는 말 | 위험 신호 | 바로 바꿀 말 |
|---|---|---|
| `한 번 넣었으니 끝 아닌가?` | BFS 습관을 그대로 씀 | `더 싼 경로가 나오면 다시 갱신` |
| `0 간선도 그냥 뒤에 넣자` | 덱 순서가 흐트러짐 | `0은 앞, 1은 뒤` |
| `거리만 맞으면 parent는 그대로 둬도 되지` | 복원 경로가 틀릴 수 있음 | `dist가 줄면 parent도 같이` |

## 3개 반례만 빠르게 보기

| 자주 틀리는 습관 | 작은 반례 | 왜 틀리나 | 바로 고칠 한 문장 |
|---|---|---|---|
| `next`를 처음 큐/덱에 넣었으니 `visited[next] = true`로 영구 고정 | `1 -> 2 (1)`, `1 -> 3 (0)`, `3 -> 2 (0)` | `2`를 먼저 비용 `1`로 봐도, 나중에 `1 -> 3 -> 2` 비용 `0`이 나온다 | `visited` 고정보다 `if (newDist < dist[next])`가 먼저다 |
| `0 edge`도 그냥 뒤에 넣어도 되겠지 | `1 -> 2 (1)`, `1 -> 3 (0)` | 비용 `0` 후보를 뒤에 넣으면 "더 싼 상태를 먼저 처리"하는 흐름이 깨진다 | `0 edge`는 앞, `1 edge`는 뒤 |
| 부모 `parent[next]`도 BFS처럼 첫 기록만 유지 | `1 -> 2 (1)`, `1 -> 3 (0)`, `3 -> 2 (0)` | 거리표가 줄었는데 부모를 안 바꾸면 경로 복원이 틀린다 | `dist[next]`가 줄면 `parent[next]`도 같이 바꾼다 |

## 반례 1: 첫 방문 고정이 왜 깨지나

그래프:

```text
1 --(1)--> 2
 \
  --(0)--> 3 --(0)--> 2
```

배열 변화만 보면 더 쉽다.

| 순간 | `dist[2]` | 설명 |
|---|---|---|
| 시작 | `INF` | 아직 모름 |
| `1 -> 2 (1)` 확인 | `1` | 일단 비용 1로 도달 |
| `1 -> 3 (0) -> 2 (0)` 확인 | `0`으로 갱신 | 더 싼 경로가 뒤늦게 나옴 |

여기서 핵심은 "`2`를 본 적 있나?"가 아니라 "`2`를 더 싸게 갈 수 있나?"다.

deque 안에 예전 후보가 남아 있어도 괜찮은지까지 바로 이어서 보고 싶다면, 이 반례를 `A@1` / `A@0` 표로 다시 쪼갠 [0-1 BFS stale-entry mini card](./zero-one-bfs-stale-entry-mini-card.md)가 가장 짧다.

## 반례 2: 왜 `0 edge`는 앞에 넣나

그래프:

```text
1 --(1)--> A
 \
  --(0)--> B
```

`B`는 현재 거리 그대로 가는 후보고, `A`는 거리 `+1` 후보다.
둘을 같은 방식으로 뒤에 넣으면 `0-1 BFS`가 유지해야 하는 "더 싼 후보가 먼저 나온다"는 감각이 흐려진다.

짧게 외우면 충분하다.

| 간선 비용 | 덱 처리 |
|---|---|
| `0` | `push front` |
| `1` | `push back` |

## 반례 3: 거리만 고치고 부모를 안 고치면 왜 틀리나

같은 반례에서 거리 복원까지 보면 실수가 더 잘 보인다.

| 순간 | `dist[2]` | `parent[2]` |
|---|---|---|
| `1 -> 2 (1)` 먼저 봄 | `1` | `1` |
| `1 -> 3 -> 2` 나중에 봄 | `0` | `3`으로 갱신 |

`dist[2]`는 `0`인데 `parent[2]`가 여전히 `1`이면, 복원 경로는 잘못된 값이 된다.

## 초보자용 체크리스트

- `if (newDist < dist[next])`가 핵심 조건인가
- `0 edge`를 덱 앞에 넣고 있는가
- `1 edge`를 덱 뒤에 넣고 있는가
- 거리 갱신과 부모 갱신이 같이 움직이는가
- BFS 습관처럼 "첫 삽입 = 영구 방문 고정"을 쓰고 있지 않은가
- `visited`를 쓰더라도 "재방문 금지"가 아니라 보조 표시인지 구분했는가

## 다음에 어디로 가나

- 실제 코드에서 `dist`, `deque`, `parent`를 어디서 같이 갱신하는지 바로 보려면 [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- deque와 `dist`가 실제로 어떻게 한 줄씩 변하는지 손으로 먼저 따라가려면 [0-1 BFS 손계산 워크시트](./zero-one-bfs-hand-calculation-worksheet.md)
- BFS의 "처음 방문 고정"이 왜 맞는지 다시 잡으려면 [DFS와 BFS 입문](./dfs-bfs-intro.md)
- `parent[]`까지 포함한 경로 복원 감각은 [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- `newDist == dist[next]`일 때 왜 보통 덱에 다시 넣지 않는지 보려면 [0-1 BFS equal-distance reinsert mini note](./zero-one-bfs-equal-distance-reinsert-mini-note.md)
- `0-1 BFS`, `Dial`, `PQ Dijkstra`를 어떤 질문에서 고르는지는 [Sparse Graph Shortest Paths](./sparse-graph-shortest-paths.md)
- 덱 자체가 아직 낯설면 [Deque Basics](../data-structure/deque-basics.md)
- 아직도 "`왜 같은 정점이 두 번 들어가요?`"에서 막히면 [0-1 BFS stale-entry mini card](./zero-one-bfs-stale-entry-mini-card.md)부터 다시 보면 된다.

## 한 줄 정리

`0-1 BFS`는 이름에 BFS가 들어가도 "처음 봤으니 visited로 고정"이 아니라 "`dist`가 더 줄어드나?"를 계속 보는 문제다.
