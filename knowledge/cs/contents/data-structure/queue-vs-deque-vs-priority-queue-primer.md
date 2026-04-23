# Queue vs Deque vs Priority Queue Primer

> 한 줄 요약: 세 구조를 고르는 가장 빠른 기준은 "다음으로 꺼낼 원소를 무엇이 결정하는가"다. 도착 순서면 `queue`, 양쪽 끝 제어면 `deque`, 값/우선순위면 `priority queue`다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [기본 자료 구조](./basic.md)
> - [자료구조 정리](./README.md)
> - [응용 자료 구조 개요](./applied-data-structures-overview.md#deque-덱)
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
> - [Heap Variants](./heap-variants.md)
> - [희소 그래프 최단 경로](../algorithm/sparse-graph-shortest-paths.md)
>
> retrieval-anchor-keywords: queue vs deque vs priority queue, fifo queue, deque basics, double ended queue, deque vs queue, priority queue basics, priority queue vs queue, heap vs queue, queue interview, deque interview, priority queue interview, bfs queue, topological sort queue, sliding window deque, monotonic deque, zero one bfs deque, 0-1 bfs deque, dijkstra priority queue, meeting rooms heap, top k heap, 큐 덱 우선순위 큐 차이, fifo 큐, 덱 입문, 양방향 큐, 큐와 덱 차이, 우선순위 큐 입문, 큐와 힙 차이, bfs 큐, 위상정렬 큐, 슬라이딩 윈도우 덱, 단조 덱, 0-1 bfs 덱, 다익스트라 우선순위 큐, 회의실 최소 힙, top k 힙

## 핵심 질문

문제를 읽을 때 제일 먼저 묻는다.

> "다음 원소를 꺼내는 기준이 무엇인가?"

- 도착한 순서 그대로면 `queue`
- 앞/뒤 양쪽 끝을 상황에 따라 써야 하면 `deque`
- 값이 작거나 큰 순서, 혹은 deadline/priority 순서면 `priority queue`

같은 값 `5, 1, 3`을 넣어도 꺼내는 순서는 달라질 수 있다.

| 구조 | 꺼내는 기준 | 같은 입력 `5, 1, 3` 예시 |
|---|---|---|
| Queue | 먼저 들어온 것부터 | `5 -> 1 -> 3` |
| Deque | front/back 중 어디서 꺼내는지에 따라 다름 | `popFront`면 `5`, `popBack`이면 `3` |
| Priority Queue (min) | 가장 작은 값부터 | `1 -> 3 -> 5` |

## 빠른 비교표

| 구조 | 핵심 규칙 | 대표 연산 | 보통 복잡도 | 대표 면접 예시 |
|---|---|---|---|---|
| Queue | FIFO, 먼저 들어온 것이 먼저 나간다 | `offer`, `poll`, `peek` | `O(1)` | BFS, level-order traversal, Kahn 위상정렬 |
| Deque | 양쪽 끝에서 넣고 뺄 수 있다 | `offerFirst`, `offerLast`, `pollFirst`, `pollLast` | 양끝 연산 `O(1)` | sliding window maximum, 0-1 BFS, circular deque design |
| Priority Queue | 우선순위가 가장 높은 원소가 먼저 나온다 | `offer`, `poll`, `peek` | `peek O(1)`, `offer/poll O(log n)` | Dijkstra, meeting rooms, top-k / kth largest |

## 1. Queue: "도착 순서"가 답을 정한다

Queue는 **들어온 순서 자체가 의미**일 때 쓴다.
즉 "누가 먼저 왔는가"가 다음 처리 대상을 결정한다.

- 잘 맞는 질문
  - `BFS`
  - `level order traversal`
  - `indegree 0인 노드부터 처리`
  - `요청을 받은 순서대로 소비`
- 잘 안 맞는 질문
  - `가장 작은 비용부터`
  - `가장 빨리 끝나는 회의실부터`
  - `앞/뒤 둘 다 조작`

대표 감각은 이렇다.

- BFS는 먼저 발견한 정점을 먼저 확장해야 하므로 queue다.
- 프린터 대기열, 단순 작업 버퍼, 네트워크 수신 버퍼도 arrival order가 중요하면 queue다.
- "priority"라는 단어가 없고 순서가 바뀌면 안 되면 queue를 먼저 의심한다.

## 2. Deque: "양쪽 끝"을 써야 할 때 고른다

Deque는 **double-ended queue**의 줄임말이다.
앞과 뒤 양쪽에서 넣고 뺄 수 있으므로 queue보다 제어 폭이 넓다.

초보자에게 가장 중요한 구분은 이것이다.

- queue는 보통 `뒤에 넣고 앞에서 뺀다`
- deque는 `앞/뒤 둘 다` 필요할 수 있다

Deque가 자연스러운 대표 상황은 다음과 같다.

### 슬라이딩 윈도우 최대/최소

`sliding window maximum/minimum`은 단순 queue가 아니라 **monotonic deque**가 핵심이다.
윈도우 밖 원소는 front에서 빼고, 의미 없는 후보는 back에서 뺀다.

즉 이 문제의 signal은 "최근 순서"만이 아니라 **front 만료 + back 후보 정리**가 동시에 있다는 점이다.

### 0-1 BFS

간선 가중치가 `0` 또는 `1`뿐이면 deque로 순서를 관리할 수 있다.

- `0` 비용 간선은 front에 넣고
- `1` 비용 간선은 back에 넣는다

이때는 priority queue 대신 deque가 더 직접적이다.

### 양쪽 끝 조작이 문제에 드러나는 경우

`circular deque design`, `앞에서 제거하고 뒤에 추가`, `뒤에서 최근 항목 제거`처럼
문제 설명이 아예 양쪽 끝 조작을 요구하면 deque가 맞다.

주의할 점도 있다.

- `deque`라고 해서 자동으로 monotonic deque는 아니다.
- 단조성은 sliding window maximum 같은 문제에서 **추가 invariant**를 붙인 것이다.

## 3. Priority Queue: "가장 작은 값/큰 값"이 먼저다

Priority Queue는 도착 순서가 아니라 **우선순위 키**가 다음 원소를 정한다.
보통 내부적으로 heap을 쓴다.

- 잘 맞는 질문
  - `현재 후보 중 가장 작은 거리`
  - `가장 빨리 끝나는 회의`
  - `상위 k개 유지`
  - `deadline이 가장 이른 작업`
- 잘 안 맞는 질문
  - 단순 `FIFO` 처리
  - front/back 양쪽 조작
  - 전체 정렬 결과를 한 번에 순회해야 하는 경우

대표 예시는 아래와 같다.

### Dijkstra / Prim

항상 현재 비용이 가장 작은 후보를 꺼내야 한다.
이 기준은 arrival order가 아니라 `min distance`이므로 queue가 아니라 priority queue다.

### Meeting Rooms / Interval 스케줄링 보조 구조

현재 사용 중인 회의실 중 **가장 빨리 끝나는 종료 시각**을 빠르게 알고 싶으면 min heap이 잘 맞는다.

### Top-k / Kth Largest in Stream

전체를 매번 정렬하지 않고도, 필요한 상위 후보만 유지할 수 있다.

자주 헷갈리는 점:

- `PriorityQueue`라는 이름 때문에 queue처럼 느껴지지만, FIFO queue와 동작이 다르다.
- 같은 priority끼리 stable order가 필요하면 `(priority, sequence)`처럼 tie-breaker를 직접 넣어야 한다.
- heap은 전체 정렬 구조가 아니라 루트만 빠른 구조다.

## 면접형 라우팅 문장

| 문제에서 보이는 표현 | 먼저 떠올릴 구조 | 이유 |
|---|---|---|
| `먼저 들어온 요청`, `레벨 순회`, `진입 차수 0부터 처리` | Queue | arrival order가 정답 순서를 만든다 |
| `앞에서도 빼고 뒤에서도 넣는다`, `sliding window maximum`, `0 edge는 앞, 1 edge는 뒤` | Deque | 양끝 제어 또는 front/back 분기가 필요하다 |
| `항상 가장 작은 비용`, `가장 빨리 끝나는 시각`, `상위 k개만 유지` | Priority Queue | 다음 원소가 priority key로 결정된다 |

## 자주 하는 실수

1. `PriorityQueue`를 일반 queue처럼 생각한다.
2. deque를 "양쪽에서 되는 queue" 정도로만 외우고, sliding window / 0-1 BFS signal을 놓친다.
3. priority queue를 정렬 배열처럼 생각해서 전체 순서를 기대한다.
4. 같은 priority의 안정적인 순서를 기대하면서 tie-breaker를 넣지 않는다.

## 한 줄 정리

`Queue`는 도착 순서, `Deque`는 양쪽 끝 제어, `Priority Queue`는 우선순위가 핵심이다.  
면접에서는 "다음 원소를 무엇이 결정하는가"만 먼저 물어도 세 구조가 꽤 잘 분리된다.
