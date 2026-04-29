# DFS와 BFS 입문 (DFS and BFS Basics)

> 한 줄 요약: DFS는 한 갈래를 끝까지 파고드는 탐색이고, BFS는 가까운 노드부터 넓게 퍼지는 탐색이며, beginner는 `연결 확인`과 `최소 이동 횟수`를 먼저 구분하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [그래프 기초](../data-structure/graph-basics.md)
- [Connectivity Question Router](../data-structure/connectivity-question-router.md)
- [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- [큐 기초](../data-structure/queue-basics.md)
- [알고리즘 정리](./README.md)

retrieval-anchor-keywords: dfs bfs 입문, dfs bfs 차이, bfs shortest path beginner, 최소 이동 횟수, bfs queue, dfs bfs 헷갈림, why bfs not dfs, connected component beginner, 언제 bfs 써요, 처음 bfs 뭐예요

## 먼저 한 줄로 나누기

처음에는 복잡하게 외우기보다 아래 두 줄만 고정하면 된다.

- DFS: 한 방향을 `끝까지` 파고든다
- BFS: `가까운 것부터` 한 겹씩 넓힌다

그래서 `갈 수 있나?`처럼 방문 자체가 중요하면 둘 다 후보가 될 수 있고, `최소 몇 번 만에 가나?`처럼 간선 수 최소가 중요하면 BFS가 먼저 나온다. `queue`는 BFS를 구현할 때 쓰는 도구일 뿐, BFS와 같은 말은 아니다.

## 왜 queue가 같이 나오나요

beginner가 많이 묻는 `왜 queue인데 bfs예요?`, `visited는 map인가요 set인가요?`는 질문 층위가 달라서 생긴다.

| 지금 보이는 단어 | 실제 역할 | 먼저 답할 질문 | 다음 문서 |
|---|---|---|---|
| `BFS` | 가까운 것부터 넓히는 탐색 규칙 | `최소 이동 횟수`를 묻는가 | 이 문서 |
| `queue` | BFS를 구현할 때 자주 쓰는 FIFO 도구 | `거리 0, 1, 2` 순서로 퍼져야 하는가 | [큐 기초](../data-structure/queue-basics.md) |
| `visited set/map` | 중복 방문 방지 보조 도구 | 정점 id가 배열형인지 sparse key인지 | [Java BFS visited 배열 vs Set beginner card](./bfs-visited-array-vs-set-java-beginner-card.md) |

짧게 외우면 `BFS는 질문`, `queue는 도구`, `visited는 보조 저장소`다. 이 순서로 읽으면 `bfs랑 queue 차이 뭐예요` 같은 첫 혼동이 많이 줄어든다.

## 언제 DFS고 언제 BFS인가요

| 문제 문장 | 첫 선택 | 이유 |
|---|---|---|
| `갈 수 있나?`, `연결돼 있나?` | DFS 또는 BFS | 방문 여부만 알면 된다 |
| `아무 경로 하나만 보여줘` | DFS 또는 BFS | 유효한 경로 하나면 된다 |
| `최소 이동 횟수`, `최소 환승 횟수` | BFS | 가까운 거리부터 보므로 최소 간선 수를 보장한다 |
| `최소 비용` | BFS 아님을 먼저 의심 | 가중치 합 질문이므로 follow-up 문서로 넘긴다 |

beginner에게 중요한 기준은 구현 취향보다 `무엇을 최소화하나`다. `횟수`를 세면 BFS, `비용`을 세면 weighted shortest path 분기로 넘긴다.

## 같은 장면도 세 질문으로 갈립니다

같은 미로나 지도 그림도 보통 아래 셋 중 하나를 묻는다.

| 같은 장면에서 들린 말 | 실제 질문 | 다음 문서 |
|---|---|---|
| `갈 수 있나?` | yes/no 연결 여부 | [Connectivity Question Router](../data-structure/connectivity-question-router.md) |
| `어떻게 가나?` | 경로 하나 복원 | [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md) |
| `최소 몇 번 만에 가나?` | 최소 간선 수 | 이 문서 |

`왜 같은 미로인데 답이 달라요?`라는 질문은 장면이 아니라 문제 문장이 달라졌기 때문이다. 초반 오답은 대부분 이 분기를 건너뛰었을 때 생긴다.

## 작은 예시로 붙이기

```text
S . .
# # .
. . E
```

| 질문 | 첫 선택 | 한 줄 이유 |
|---|---|---|
| `S에서 E로 갈 수 있나?` | DFS 또는 BFS | 도달 여부만 보면 된다 |
| `S에서 E까지 아무 경로 하나 보여줘` | DFS 또는 BFS | 유효한 경로 하나면 된다 |
| `S에서 E까지 최소 몇 칸이야?` | BFS | 거리 0, 1, 2 순서로 넓혀 간다 |

이 예시에서 BFS가 중요한 이유는 `먼저 도착한 순간의 거리`가 최소라는 점이다. DFS는 먼저 도착해도 더 짧은 길이라는 보장이 없다. 반대로 `갈 수 있나?`만 확인하는 상황이면 DFS도 충분하다.

## 자주 헷갈리는 말

| 헷갈린 표현 | 바로 고칠 한 줄 |
|---|---|
| `queue가 나오니까 자료구조 문제죠?` | queue는 BFS 구현 도구일 수 있다 |
| `최소면 다 bfs죠?` | `최소 이동 횟수`와 `최소 비용`은 다르다 |
| `graph가 보이면 bfs부터죠?` | graph는 구조이고, 질문은 연결인지 최단인지 다시 나눠야 한다 |

처음 읽는 단계라면 `0-1 BFS`, `다익스트라`, `MST`까지 한 번에 붙잡지 않는 편이 안전하다. 이 문서의 역할은 `연결 vs 최소 이동 횟수`를 분리하는 데까지다.

## 다음 문서 고르기

| 지금 막힌 문장 | 다음 문서 |
|---|---|
| `그래프 자체가 아직 추상적이에요` | [그래프 기초](../data-structure/graph-basics.md) |
| `같은 그룹인지 보고 싶어요` | [Connectivity Question Router](../data-structure/connectivity-question-router.md) |
| `경로를 실제로 출력해야 해요` | [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md) |
| `비용 합 최소가 보여요` | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) |
| `왜 queue가 같이 나와요?` | [큐 기초](../data-structure/queue-basics.md) |

target query는 `dfs bfs 차이`, `처음 bfs 뭐예요`, `최소 이동 횟수면 왜 bfs예요` 같은 beginner 질문이다. 그래서 심화 분기보다 첫 판단 기준을 짧게 남기는 쪽이 이 문서 목적에 맞다.

## 한 줄 정리

DFS는 `끝까지 파고드는 탐색`, BFS는 `가까운 것부터 넓히는 탐색`이고, beginner는 먼저 `연결 확인`과 `최소 이동 횟수`를 분리하면 된다.
