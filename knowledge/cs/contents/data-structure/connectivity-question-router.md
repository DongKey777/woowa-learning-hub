# Connectivity Question Router

> 한 줄 요약: `연결돼 있나?` 질문은 먼저 `yes/no만 필요`, `경로 하나 필요`, `가장 짧아야 함`으로 자르면 union-find와 BFS 계열을 초반에 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:
- [자료구조 정리](./README.md)
- [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md)
- [Union-Find Deep Dive](./union-find-deep-dive.md)
- [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- [BFS vs Dijkstra shortest path mini card](../algorithm/bfs-vs-dijkstra-shortest-path-mini-card.md)
- [Dijkstra, Bellman-Ford, Floyd-Warshall](../algorithm/dijkstra-bellman-ford-floyd-warshall.md)

retrieval-anchor-keywords: connectivity question router, union find vs bfs, 연결돼 있나, 갈 수 있나, 같은 그룹인가, 같은 묶음인지, 몇 덩어리인지, connected yes no, actual path reconstruction, shortest path router, bfs parent reconstruction, path reconstruction 뭐예요, union find bfs 차이, what is connectivity, 처음 그래프 헷갈림

## 핵심 개념

초보자가 가장 먼저 섞는 문장은 보통 이 세 개다.

- `연결돼 있나?`, `갈 수 있나?`
- `갈 수 있으면 실제 경로 하나 보여줘`
- `가장 짧게 가는 길을 보여줘`

겉으로는 비슷하지만, 필요한 답의 모양이 다르다.

| 질문 신호 | 필요한 답 | 첫 분기 |
|---|---|---|
| `연결돼 있나?`, `같은 그룹이야?`, `몇 덩어리야?` | yes/no 또는 그룹 메타데이터 | union-find |
| `경로 하나 보여줘`, `중간 정점도 써 줘` | 유효한 경로 하나 | BFS/DFS + `parent` |
| `가장 짧게`, `최소 이동`, `최소 비용` | shortest path | BFS / Dijkstra 계열 |

짧게 기억하면 된다.

- `연결만 확인`이면 union-find bucket
- `경로를 복원`하면 BFS/DFS bucket
- `최소`가 붙으면 shortest-path bucket

## beginner 안전 사다리

처음 읽는 사람은 `yes/no -> 경로 하나 -> 최단 경로` 순서로 한 칸씩만 올라가는 편이 덜 흔들린다.

| 지금 보이는 문장 | primer | follow-up | deep dive는 그다음 |
|---|---|---|---|
| `같은 그룹이야?`, `몇 덩어리야?` | [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md) | [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md) | [Union-Find Deep Dive](./union-find-deep-dive.md) |
| `갈 수 있으면 아무 경로나 하나 보여줘` | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md) | 경로 복원 구현 세부만 더 필요할 때 관련 deep dive |
| `최소 몇 번`, `최소 환승`, `최소 비용` | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | [BFS vs Dijkstra shortest path mini card](../algorithm/bfs-vs-dijkstra-shortest-path-mini-card.md) | [Dijkstra, Bellman-Ford, Floyd-Warshall](../algorithm/dijkstra-bellman-ford-floyd-warshall.md) |

- `처음`, `헷갈`, `왜 BFS가 아니지`, `왜 union-find지` 같은 beginner query는 위 표의 primer에서 멈춘 뒤 다음 한 칸만 붙인다.
- `최소 비용` 문장이 보여도 바로 고급 shortest-path 비교 문서로 점프하지 말고, 먼저 `최소 이동 횟수`와 `최소 비용`을 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)에서 분리하는 편이 안전하다.

## 한눈에 보기

처음에는 알고리즘 이름보다 아래 번역표를 먼저 보는 편이 빠르다.

| learner question | 실제 의도 | 첫 문서 |
|---|---|---|
| `A에서 B로 연결돼 있나?` | connected yes/no | [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md) |
| `A와 B가 같은 팀이야?` | same-component yes/no | [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md) |
| `지금 몇 개 그룹으로 나뉘어?` | component count | [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md) |
| `연결되면 아무 경로나 하나만 보여줘` | actual path reconstruction | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `최소 몇 번 만에 가?` | unweighted shortest path | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `비용이 가장 적은 길은?` | weighted shortest path | [Dijkstra, Bellman-Ford, Floyd-Warshall](../algorithm/dijkstra-bellman-ford-floyd-warshall.md) |

핵심은 `연결된다`는 말만 보고 BFS부터 들어가지 않는 것이다.
문장이 yes/no에서 끝나면, 아직은 shortest-path가 아니다.

## shortest-path에서 제일 많이 틀리는 한 번 분리

먼저 이렇게 생각하면 된다.

- `갈 수 있나?`만 묻는 순간은 아직 shortest-path가 아니라 connectivity 질문이다.
- **BFS**: "한 칸 이동" 비용이 모두 같아서 `몇 번 움직였는가`만 세면 된다.
- **Dijkstra**: 간선마다 요금/시간이 달라서 `총비용 합`이 가장 작은 경로를 골라야 한다.

| 묻는 것 | 먼저 떠올릴 알고리즘 | 왜 |
|---|---|---|
| 무가중치 최소 간선 수 | BFS | 레벨 순서가 곧 `간선 수 1개, 2개, 3개...` 순서다 |
| 가중치 최소 비용 | Dijkstra | 간선마다 비용이 달라 레벨 순서만으로는 최소 비용이 보장되지 않는다 |

같은 `최단 경로`라는 말이어도 `최소 이동 횟수`인지 `최소 비용`인지 먼저 잘라야 오답 분기가 크게 줄어든다.

특히 [그래프 기초](./graph-basics.md)에서 `BFS가 최단 경로를 찾는다`는 문장을 먼저 본 초보자는 아래 한 줄을 같이 붙여서 기억하면 안전하다.

- `갈 수 있나?` -> Connectivity Router
- `가장 짧게 가나?` + 간선 비용이 전부 같음 -> BFS
- `가장 싸게 가나?` + 간선 비용이 다름 -> Dijkstra

## Union-Find와 BFS를 가장 먼저 분리하는 기준

둘 다 `연결` 얘기처럼 보여서 많이 섞이지만, 저장하는 정보가 다르다.

| 비교 축 | Union-Find | BFS |
|---|---|---|
| 가장 잘 답하는 질문 | `같은 그룹인가?` | `어떻게 가나?`, `최소 몇 번 가나?` |
| 답의 모양 | yes/no, 그룹 수, 그룹 크기 | 방문 순서, 거리, `parent` 경로 |
| 실제 경로 복원 | 못 함 | 가능 |
| `연결돼 있나?`를 여러 번 묻는 반복 질의 | 강함 | 매번 다시 탐색 |

한 줄로 자르면 이렇다.

- `연결 여부를 빨리 많이 묻는다` -> union-find
- `이번 한 번 실제로 따라가 본다` -> BFS/DFS
- `최소`까지 요구한다 -> BFS 또는 Dijkstra

## 초보 별칭 빠른 매핑

| 문제에 자주 쓰는 표현 | 실제로 묻는 것 | 첫 문서 |
|---|---|---|
| `union-find`, `dsu`, `유니온파인드`, `서로소 집합` | 같은 그룹인지 yes/no | [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md) |
| `connected components 개수`, `연결 요소 수`, `컴포넌트 수`, `친구 네트워크 그룹 수`, `몇 덩어리로 나뉘어?` | 그룹 수/크기 메타데이터 | [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md) |
| `연결은 되는데 경로를 보여줘` | 실제 경로 하나 복원 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `환승 횟수 최소`, `몇 번 갈아타나`, `최소 환승 경로` | 무가중치 최소 간선 수 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |

## Beginner Query Phrase Pack

생활 표현을 `답의 모양`으로만 번역하면 된다.

| 실사용 질문 문장 | 숨은 의도 | 첫 문서 |
|---|---|---|
| `A랑 B 같은 팀이야?` | same-component yes/no | [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md) |
| `둘이 한 묶음이야, 따로야?` | same-component yes/no | [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md) |
| `3번이랑 17번 유저 지금 이어져 있어?` | connected yes/no | [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md) |
| `지금 연결요소가 몇 개인지 알려줘.` | component count | [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md) |
| `7번 유저가 속한 묶음 크기도 같이 보고 싶어.` | component size metadata | [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md) |
| `1번에서 9번까지 갈 수 있으면 아무 경로나 하나만 보여줘.` | actual path reconstruction | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `A역에서 B역까지 최소 몇 번 갈아타?` | unweighted shortest path | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `창고 S에서 고객 T까지 비용 제일 적게 가는 길은?` | weighted shortest path | [Dijkstra, Bellman-Ford, Floyd-Warshall](../algorithm/dijkstra-bellman-ford-floyd-warshall.md) |

짧게 기억하면 된다. `같은 팀`, `같은 묶음`, `몇 덩어리야?`는 union-find 쪽이고, `하나만 보여줘`는 actual path, `최소`는 shortest-path 쪽이다. `연결돼 있나?`가 yes/no에서 끝나면 BFS를 아직 꺼낼 필요가 없다.

## 먼저 질문을 번역하기

| 질문이 요구하는 답 | 먼저 갈 문서 | 왜 거기로 가는가 |
|---|---|---|
| `같은 컴포넌트인가?`, `same set`, `connected yes/no` | [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md) | 답의 모양이 `같다/아니다`면 컴포넌트 대표만 빠르게 비교하면 된다 |
| `이 그룹 크기는?`, `전체 컴포넌트 수는?`까지 같이 묻나 | [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md) | 같은 컴포넌트 질의에 `size`, `count` 메타데이터가 추가된 경우다 |
| `실제 경로 하나를 출력`, `방문 순서`, `도달 가능한 정점 목록` | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | 간선을 실제로 따라가며 `parent`나 방문 순서를 남겨야 한다 |
| `최단 거리`, `최소 이동 횟수`, `최소 비용`, `최단 경로` | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md), [Dijkstra, Bellman-Ford, Floyd-Warshall](../algorithm/dijkstra-bellman-ford-floyd-warshall.md) | shortest-path라도 `무가중치 최소 간선 수`면 BFS, `가중치 최소 비용`이면 Dijkstra 계열로 갈린다 |

## 초보자 자주 하는 오해

- `환승 횟수`를 묻는데 간선 비용이 모두 같다면, 보통은 `최소 비용`이 아니라 `최소 간선 수` 문제라서 BFS 쪽이 먼저다.
- `친구 네트워크 그룹 수`를 묻는 질문은 경로를 출력하는 문제가 아니라 `componentCount`를 관리하는 union-find 메타데이터 문제다.
- `갈 수 있나요?`와 `어떻게 가나요?`는 다른 질문이다. 앞은 yes/no, 뒤는 actual path 복원이다.
- `같은 팀인지`를 물었다고 해서 실제 팀원 목록이나 경로를 바로 요구하는 것은 아니다. 문장 끝이 yes/no면 우선 union-find로 읽는다.

자주 나오는 오답 문장을 짧게 끊어 보면 더 분명하다.

- `1번에서 9번으로 갈 수 있나요?`를 보고 경로를 바로 출력하면 과한 답이다. 이 문장은 yes/no만 요구한다.
- `1번과 9번이 연결되어 있으면 중간 정점도 같이 써 주세요.`를 union-find로 풀면 부족하다. 연결 여부가 아니라 `실제 경로 하나`가 필요하다.
- `A와 B가 같은 네트워크인지 확인하고, 맞다면 한 경로도 보여줘.`는 yes/no로 끝나는 문제가 아니다. 앞 문장에 속지 말고 DFS/BFS parent 복원까지 포함해야 한다.

## 경로 존재 vs 경로 복원 미니 드릴

같은 그래프를 두고도 질문이 바뀌면 필요한 답이 달라진다.

```text
1 - 2 - 4
 \  |
   3
```

| 문제 문장 | 필요한 출력 | 첫 도구 | 초보자 체크포인트 |
|---|---|---|---|
| `1에서 4로 갈 수 있나?` | `yes/no` | Union-Find 또는 BFS/DFS | 경로 문자열까지 출력할 필요는 없다 |
| `1에서 4로 갈 수 있으면 실제 경로 하나를 출력하라` | `1 -> 2 -> 4` 같은 유효 경로 | BFS/DFS + `parent` | 연결 확인만 하고 끝내면 답이 모자란다 |
| `1에서 4까지 가장 짧은 경로를 출력하라` | 최소 간선 수 경로 | BFS + `parent` | `경로 하나`와 `최단 경로`를 다시 구분해야 한다 |

짧게 자르면 이렇게 기억하면 된다.

- `갈 수 있나?`는 답의 모양이 yes/no다.
- `실제 경로를 출력하라`는 중간 정점 정보가 필요하므로 `parent`를 남겨야 한다.
- `가장 짧게`가 붙는 순간에는 경로 복원 전에 shortest-path 문제인지부터 판단한다.

## 30초 빠른 예시 분기

같은 입력 그래프라도 문제 문장에 따라 첫 도구가 달라진다.

| 같은 상황에서 문장만 바꾼 질문 | 답 모양 | 첫 문서 |
|---|---|---|
| `1과 6이 같은 그룹인지 true/false만 말해줘` | yes/no | [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md) |
| `1이 속한 그룹 크기와 전체 그룹 개수도 같이 알려줘` | yes/no + size/count 메타데이터 | [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md) |
| `1에서 6까지 실제 경로 하나를 출력해줘` | actual path | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `1에서 6까지 최소 이동 횟수 경로를 출력해줘` | minimum path (unweighted) | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `1에서 6까지 최소 비용 경로를 출력해줘` | minimum path (weighted) | [Dijkstra, Bellman-Ford, Floyd-Warshall](../algorithm/dijkstra-bellman-ford-floyd-warshall.md) |

가장 중요한 경계는 이것이다.

> `경로를 복원하라`와 `최단 경로를 복원하라`는 같은 말이 아니다.

- 앞 문장은 **유효한 경로 하나**면 된다. DFS/BFS로 parent를 남기면 충분하다.
- 뒤 문장은 먼저 **shortest-path 알고리즘**을 고르고, 그다음 predecessor를 저장해 경로를 복원해야 한다.
- 이때 `무가중치 최소 간선 수`는 BFS, `가중치 최소 비용`은 Dijkstra로 다시 한 번 나뉜다.

## Union-Find vs BFS decision micro-drill

아래 6문장은 일부러 비슷하게 섞어 놓은 것이다.
먼저 `yes/no`, `path reconstruction`, `shortest-path` 중 어디에 속하는지만 고르면 된다.

| 한 줄 문제 문장 | 먼저 고를 bucket | 첫 도구 | 왜 |
|---|---|---|---|
| `사용자 2와 9가 지금 같은 네트워크인지 true/false만 필요해요.` | yes/no | Union-Find | 답이 연결 여부 하나면 대표 비교로 충분하다 |
| `2에서 9까지 갈 수 있으면 중간 번호를 포함한 경로 예시 하나를 보여줘.` | path reconstruction | DFS/BFS + `parent` | 연결 여부가 아니라 실제 경로 정보가 필요하다 |
| `2에서 9까지 가장 적은 클릭 수로 가는 경로를 출력해줘.` | shortest-path | BFS + `parent` | `가장 적은`이 붙어 무가중치 최단 경로다 |
| `친구 관계가 계속 추가될 때 지금 그룹이 몇 덩어리인지 세 줘.` | yes/no 계열 메타데이터 | Union-Find + component count | 경로보다 그룹 수 관리가 핵심이다 |
| `미로에서 S에서 T까지 갈 수만 있는지 확인하고, 된다면 아무 경로나 하나 써 줘.` | path reconstruction | DFS/BFS + `parent` | yes/no 뒤에 `아무 경로` 요구가 붙어서 답이 커졌다 |
| `배송 그래프에서 창고 S부터 고객 T까지 비용이 가장 적은 경로를 구해줘.` | shortest-path | Dijkstra + predecessor | 비용 최적화가 핵심이라 Union-Find/BFS 둘 다 아니다 |

빠르게 채점하면 이렇게 보면 된다.

- `true/false만`, `같은 그룹`, `몇 덩어리` -> Union-Find bucket
- `아무 경로`, `예시 하나`, `중간 정점도 써 줘` -> path reconstruction bucket
- `가장 적은`, `최소 이동`, `최소 비용` -> shortest-path bucket

특히 초급자가 많이 틀리는 문장은 이것이다.

- `갈 수만 있으면`으로 시작해도 뒤에 `경로를 보여줘`가 붙으면 yes/no가 아니라 path reconstruction이다.
- `경로를 출력해줘`라고 써 있어도 앞에 `가장 적은`, `최소 비용`이 붙으면 shortest-path다.

## 마이크로 self-check (5문항)

아래 문장을 보고 `첫 문서`만 5초 안에 고르면 라우터 감각이 빨리 붙는다.

| 한 줄 문제 문장 | expected first-doc route |
|---|---|
| `사용자 3과 17이 지금 같은 네트워크 그룹인지 true/false만 필요해요.` | [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md) |
| `친구 추천 묶음에서 3이 속한 그룹 인원수와 전체 그룹 개수를 알려줘.` | [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md) |
| `미로에서 2번 칸에서 9번 칸까지 갈 수 있으면 실제 이동 경로 하나만 출력해줘.` | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `지하철 노선(모든 간선 비용 동일)에서 A부터 B까지 최소 환승 횟수 경로를 구해줘.` | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `택배 그래프(간선마다 비용 다름)에서 창고 S부터 고객 T까지 최소 비용 경로를 구해줘.` | [Dijkstra, Bellman-Ford, Floyd-Warshall](../algorithm/dijkstra-bellman-ford-floyd-warshall.md) |

## 헷갈리는 문장을 바로 분해하면

| 문제 문장 | 실제로 묻는 것 | 먼저 떠올릴 도구 |
|---|---|---|
| `1과 9가 같은 컴포넌트인가?` | same-component yes/no | Union-Find |
| `1에서 9까지 갈 수 있으면 경로 하나를 출력하라` | actual path reconstruction | DFS/BFS + `parent` |
| `1에서 9까지 최소 간선 수와 그 경로를 구하라` | unweighted shortest path + reconstruction | BFS + `parent` |
| `1에서 9까지 최소 비용 경로를 구하라` | weighted shortest path + reconstruction | Dijkstra / Bellman-Ford + predecessor |
| `0/1 비용으로 1에서 9까지 가장 싸게 가라` | special weighted shortest path | [Sparse Graph Shortest Paths](../algorithm/sparse-graph-shortest-paths.md) |

## 꼭 기억할 경계

- Union-Find는 `같은 그룹인가?`를 빨리 답하지만 `1 -> 4 -> 7` 같은 실제 경로는 주지 않는다.
- Union-Find에 `size`, `componentCount`를 붙여도 여전히 답 모양은 `그룹 메타데이터`까지다. 실제 경로가 필요하면 DFS/BFS 계열로 넘어가야 한다.
- DFS는 경로 하나를 빨리 찾을 수 있지만 그 경로가 shortest라는 보장은 없다.
- BFS는 **무가중치 그래프**에서는 shortest-path와 path reconstruction을 동시에 처리할 수 있다.
- weighted shortest path에서 경로까지 출력하려면 거리 배열만으로는 부족하고 predecessor 배열을 같이 저장해야 한다.

## 한 줄 정리

연결성 질문은 `yes/no`, `actual path`, `minimum path` 중 무엇을 요구하는지 먼저 고르면 된다.
그 구분만 잡히면 union-find, BFS/DFS, shortest-path 문서가 거의 자동으로 갈린다.
