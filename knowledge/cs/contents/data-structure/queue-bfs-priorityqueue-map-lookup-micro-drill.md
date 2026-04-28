# Queue vs BFS vs Priority Queue vs Map Lookup Micro Drill

> 한 줄 요약: 한 줄 문제를 읽을 때 `순서대로 처리`면 `queue`, `가까운 칸부터`면 `BFS`, `가장 급한 것부터`면 `priority queue`, `key로 바로 찾기`면 `map lookup`으로 먼저 자르면 초급 오분류가 크게 줄어든다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [큐 기초](./queue-basics.md)
- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [Map vs Set vs Queue vs Priority Queue vs Trie vs Bitmap 선택 프라이머](./map-set-queue-priorityqueue-trie-bitmap-selection-primer.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- [알고리즘 카테고리 인덱스](../algorithm/README.md)

retrieval-anchor-keywords: queue vs bfs vs priority queue vs map lookup, queue bfs difference beginner, bfs queue 헷갈림, priority queue 언제 써요, map lookup 뭐예요, one line problem classification, 자료구조 처음 분류, queue bfs priority queue map drill, what is map lookup, why is this bfs not queue, closest first bfs, earliest first priority queue, key lookup basics, beginner self check card, 처음 queue bfs 헷갈림

## 핵심 개념

처음에는 이름보다 문장 신호를 먼저 읽으면 된다.

- `먼저 들어온 순서대로 처리` -> `queue`
- `가까운 칸부터`, `최소 이동 횟수` -> `BFS`
- `가장 작은 값`, `가장 급한 작업`, `가장 이른 시각` -> `priority queue`
- `orderId로 상태 찾기`, `key로 값 꺼내기` -> `map lookup`

짧게 외우면 이렇다.

> `queue`는 FIFO 도구, `BFS`는 거리 순서 탐색, `priority queue`는 우선순위 순서, `map`은 key lookup이다.

## 한눈에 보기

| 문제 문장 신호 | 첫 선택 | 왜 이렇게 자르나 |
|---|---|---|
| `받은 순서대로 처리` | `queue` | arrival order가 규칙이다 |
| `미로에서 가까운 칸부터` | `BFS` | 거리 1, 2, 3 순서로 퍼진다 |
| `다음 재시도 시각이 가장 이른 작업` | `priority queue` | 가장 작은 key 하나를 계속 꺼낸다 |
| `orderId 42의 상태를 바로 조회` | `map lookup` | key 하나로 value를 찾는다 |

헷갈릴 때는 질문을 이렇게 다시 적는다.

- `누가 먼저 나가나?` -> `queue`
- `어떤 칸을 먼저 탐색하나?` -> `BFS`
- `지금 제일 급한 것 하나가 뭔가?` -> `priority queue`
- `이 key의 값이 뭐지?` -> `map lookup`

## 4문장 셀프 체크

아래 네 문장을 보고 5초 안에 첫 선택을 말해 본다.

| 한 줄 문제 | 정답 |
|---|---|
| `프린터 작업을 들어온 순서대로 처리한다.` | `queue` |
| `미로에서 출구까지 최소 몇 칸인지 구한다.` | `BFS` |
| `재시도 시간이 가장 이른 작업부터 다시 실행한다.` | `priority queue` |
| `회원 id로 회원 정보를 바로 찾는다.` | `map lookup` |

정답을 고른 뒤 한 줄 이유까지 붙이면 더 단단해진다.

| 정답 | 한 줄 이유 |
|---|---|
| `queue` | FIFO가 핵심이다 |
| `BFS` | 최소 이동 횟수라서 거리 순서 탐색이 핵심이다 |
| `priority queue` | 도착 순서보다 우선순위 key가 먼저다 |
| `map lookup` | 순서보다 `key -> value` 조회가 핵심이다 |

## 흔한 오해와 함정

- `BFS도 queue를 쓰니까 queue가 정답이다` -> 반만 맞다. 구현 도구는 queue지만, 문제 분류는 `BFS`가 먼저다.
- `priority queue도 queue니까 FIFO와 비슷하다` -> 아니다. 먼저 꺼내는 기준이 도착 순서가 아니라 우선순위다.
- `map`은 그냥 저장소라서 분류 대상이 아니다` -> 아니다. `key로 바로 찾기`가 핵심이면 map lookup 문제가 맞다.
- `queue`와 `map`은 둘 중 하나만 나온다` -> 아니다. 예를 들어 BFS는 `queue + visited map/set`으로 함께 간다.

## 다음 한 걸음

- `queue`와 `priority queue`를 더 또렷하게 나누고 싶다면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- `queue`와 `BFS`가 계속 섞이면 [큐 기초](./queue-basics.md) 다음 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- `map lookup`과 ordered map 선택까지 이어 보고 싶다면 [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)

## 한 줄 정리

한 줄 문제를 볼 때 `FIFO면 queue`, `최소 이동이면 BFS`, `가장 급한 것 하나면 priority queue`, `key로 값 찾기면 map lookup`으로 먼저 자르면 beginner 분류 실수가 크게 줄어든다.
