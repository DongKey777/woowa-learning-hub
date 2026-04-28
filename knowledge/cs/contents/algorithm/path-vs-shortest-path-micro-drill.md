# Path vs Shortest Path Micro Drill

> 한 줄 요약: `경로 하나만 찾기`와 `최단 경로 구하기`는 답의 모양이 다르므로, 문제 문장에서 `아무 경로나`인지 `최소`인지 먼저 자르면 초급자 실수가 줄어든다.

**난이도: 🟢 Beginner**

관련 문서:

- [DFS와 BFS 입문](./dfs-bfs-intro.md)
- [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- [그래프 관련 알고리즘](./graph.md)
- [Connectivity Question Router](../data-structure/connectivity-question-router.md)
- [그래프 기초](../data-structure/graph-basics.md)
- [Queue Basics](../data-structure/queue-basics.md)

retrieval-anchor-keywords: path vs shortest path, actual path vs minimum path, any path drill, bfs shortest path beginner, dfs path reconstruction, minimum move count, 처음 path shortest path 헷갈림, 왜 dfs shortest 아니지, 언제 bfs path, 뭐예요 actual path, graph beginner drill, basics

처음 읽는다면 이렇게 보면 된다.

- `갈 수 있나`
- `아무 경로나 하나면 되나`
- `최단이어야 하나`

이 세 줄만 먼저 자르면 `dfs`, `bfs`, `shortest path`가 왜 갈리는지 덜 헷갈린다.

## 먼저 떠올릴 그림

문제를 보면 먼저 "`길이 있나`", "`하나만 보여 주면 되나`", "`가장 짧아야 하나`" 셋 중 무엇인지 자른다.

| 질문 | 답의 모양 | 먼저 떠올릴 도구 |
|---|---|---|
| 갈 수 있나 | yes/no | DFS/BFS |
| 경로 하나만 보여 줘 | actual path 1개 | DFS/BFS + parent 또는 재귀 |
| 가장 짧은 경로를 구해 | minimum path | BFS 또는 shortest-path 알고리즘 |

`경로를 출력하라`는 겉모양이고, 실제 분기는 `아무 경로나`인지 `최소`인지가 만든다.

## 먼저 자르는 기준

초보자가 가장 많이 섞는 두 문장은 아래 둘이다.

| 문제 문장 | 답의 모양 | 첫 선택 |
|---|---|---|
| `s에서 t까지 갈 수 있는 경로 하나를 보여라` | 아무 경로나 1개 | DFS/BFS 둘 다 가능 |
| `s에서 t까지 가는 최단 경로를 구하라` | 최소 간선 수 또는 최소 비용 경로 | 보통 BFS 또는 shortest-path 알고리즘 |

핵심은 `path`가 아니라 앞의 수식어다.

- `아무`, `하나`, `예시`, `가능한 경로`가 보이면 actual path 쪽이다.
- `최소`, `최단`, `가장 적게`, `최소 비용`이 보이면 shortest path 쪽이다.
- BFS는 `큐`로 가까운 레벨부터 퍼지므로 무가중치에서는 shortest path까지 보장한다.
- DFS는 경로 하나를 찾는 데는 충분하지만, 먼저 찾았다고 shortest는 아니다.

문장을 한 줄로 줄이면 이렇다.

- `보여 줘`는 출력 요구다.
- `최단으로 보여 줘`는 최적화 요구다.

## 증상 문구로 빠르게 분기

문제를 읽다 아래 표현이 보이면 거의 바로 갈라진다.

| 보이는 표현 | 읽는 법 | 흔한 초보 실수 |
|---|---|---|
| `아무 경로나`, `하나만`, `예시를 보여라` | actual path | shortest까지 구해야 한다고 과하게 풂 |
| `최단`, `최소 이동`, `가장 적은`, `최소 비용` | shortest path | path 출력 문제처럼 보고 DFS부터 잡음 |
| `도달 가능한가`, `연결되어 있나` | yes/no | path 복원까지 같이 해야 한다고 생각 |

이 표를 먼저 보면 `경로`라는 단어 하나에 덜 끌려간다.

## 4문항 Micro Drill

1. `미로에서 출구까지 갈 수 있는 경로 하나만 출력하라. 길이 최소일 필요는 없다.`
정답: actual path.
이유: `하나만`, `최소일 필요는 없다`가 직접 신호다. DFS로 한 길을 끝까지 가도 된다.

2. `미로에서 출구까지 최소 이동 횟수를 구하라.`
정답: shortest path.
이유: `최소 이동 횟수`는 무가중치 그래프의 최소 간선 수라서 BFS가 자연스럽다.

3. `지하철 A역에서 B역까지 환승이 가장 적은 경로를 출력하라.`
정답: shortest path.
이유: 경로를 출력하더라도 핵심은 `가장 적은`이다. 출력 형식이 path여도 문제의 목적 함수는 shortest다.

4. `친구 추천 그래프에서 민수에서 지훈까지 연결 예시를 하나 보여라.`
정답: actual path.
이유: 연결되어 있다는 예시만 있으면 된다. 가장 짧은 소개 사슬을 요구하지 않았다.

## 자주 하는 착각

- `경로를 출력하라`만 보고 무조건 DFS로 가면 틀릴 수 있다. 앞에 `최단`이 붙으면 path 출력 문제이면서도 shortest-path 문제다.
- BFS를 쓴다고 항상 shortest가 되는 것은 아니다. `가중치`가 붙으면 BFS가 아니라 Dijkstra 같은 다른 분기가 필요하다.
- `경로가 있나`와 `최단 거리가 몇이냐`를 한 번에 풀어야 한다고 생각하기 쉽지만, 문제는 보통 둘 중 하나만 먼저 묻는다.
- `도달 가능 여부`, `경로 하나`, `최단 경로`는 서로 다른 질문이다. `yes/no vs actual path vs minimum path`를 먼저 자르는 습관이 안전하다.

## 다음에 어디로 가나

- `yes/no`, `경로 하나`, `최단 경로` 세 bucket 자체를 자꾸 섞는다면 [Connectivity Question Router](../data-structure/connectivity-question-router.md)
- `경로를 어떻게 복원하지?`에서 막히면 [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- `BFS가 왜 무가중치 최단 거리인가?`를 다시 잡고 싶으면 [DFS와 BFS 입문](./dfs-bfs-intro.md)
- `가중치 0/1이면 BFS와 뭐가 달라지지?`가 궁금하면 [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)

## 한 줄 정리

`path를 보여라`는 출력 형식이고, `shortest를 구하라`는 최적화 조건이므로 문제를 읽을 때는 `아무 경로나`인지 `최소`인지부터 먼저 확인한다.
