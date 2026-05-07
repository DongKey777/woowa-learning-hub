---
schema_version: 3
title: Deque Router Example Pack
concept_id: data-structure/deque-router-example-pack
canonical: false
category: data-structure
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 87
mission_ids:
- missions/lotto
review_feedback_tags:
- deque-pattern-router
- monotonic-deque-vs-zero-one-bfs
- plain-deque-simulation
aliases:
- deque router example pack
- plain deque vs monotonic deque
- monotonic deque vs 0-1 BFS
- deque problem patterns
- sliding window maximum deque
- zero one BFS deque
- 덱 문제 패턴 라우터
symptoms:
- Deque라는 자료구조 이름만 보고 양끝 시뮬레이션, monotonic deque, 0-1 BFS를 같은 패턴으로 처리한다
- sliding window extrema는 index 후보를 유지하고 0-1 BFS는 distance layer를 유지한다는 불변식 차이를 놓친다
- push_front push_back 같은 명령 시뮬레이션과 binary-weight shortest path를 같은 front/back 의미로 해석한다
intents:
- comparison
- troubleshooting
prerequisites:
- data-structure/deque-basics
- data-structure/queue-vs-deque-vs-priority-queue-primer
next_docs:
- data-structure/monotonic-deque-walkthrough
- data-structure/monotonic-queue-and-stack
- algorithm/sliding-window-patterns
- algorithm/sparse-graph-shortest-paths
linked_paths:
- contents/data-structure/deque-basics.md
- contents/data-structure/queue-vs-deque-vs-priority-queue-primer.md
- contents/data-structure/monotonic-deque-walkthrough.md
- contents/data-structure/monotonic-queue-and-stack.md
- contents/algorithm/sliding-window-patterns.md
- contents/algorithm/sparse-graph-shortest-paths.md
confusable_with:
- data-structure/deque-basics
- data-structure/monotonic-deque-walkthrough
- data-structure/monotonic-queue-and-stack
- algorithm/sparse-graph-shortest-paths
forbidden_neighbors: []
expected_queries:
- Deque를 쓰는 문제에서 plain deque, monotonic deque, 0-1 BFS를 어떻게 구분해?
- sliding window maximum은 왜 monotonic deque이고 양끝 명령 시뮬레이션과 달라?
- 0-1 BFS에서 deque front back은 비용 0과 1 layer를 어떻게 표현해?
- 덱 문제를 보면 답이 최단 거리인지 window extrema인지 명령 시뮬레이션인지 어떻게 먼저 자르지?
- monotonic deque와 일반 deque의 불변식 차이를 예제로 알려줘
contextual_chunk_prefix: |
  이 문서는 Deque가 보일 때 plain deque simulation, monotonic deque for
  sliding window extrema, 0-1 BFS for binary-weight shortest path를 분리하는
  chooser다. front/back가 실제 양끝인지, candidate dominance인지, distance
  layer인지 먼저 해석한다.
---
# Deque Router Example Pack

> 한 줄 요약: 같은 `Deque`를 써도 plain deque는 양끝 시뮬레이션, monotonic deque는 contiguous window extrema, 0-1 BFS는 binary-weight shortest path를 푸는 서로 다른 패턴이다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: deque router example pack basics, deque router example pack beginner, deque router example pack intro, data structure basics, beginner data structure, 처음 배우는데 deque router example pack, deque router example pack 입문, deque router example pack 기초, what is deque router example pack, how to deque router example pack
> 관련 문서:
> - [덱 기초](./deque-basics.md)
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
> - [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
> - [Sliding Window Patterns](../algorithm/sliding-window-patterns.md)
> - [Sparse Graph Shortest Paths](../algorithm/sparse-graph-shortest-paths.md)
>
> retrieval-anchor-keywords: deque router example pack, deque router, deque routing examples, plain deque vs monotonic deque, monotonic deque vs 0-1 bfs, plain deque vs 0-1 bfs, deque problem patterns, deque use case separation, deque simulation pattern, reverse command deque, plain deque simulation, sliding window maximum deque, sliding window minimum deque, monotonic deque routing, window extrema deque, 0-1 bfs deque, zero one bfs deque, deque shortest path, teleport shortest path deque, binary edge weight shortest path deque, arraydeque routing, deque offerfirst offerlast pollfirst polllast, 덱 라우팅 예제, 덱 문제 패턴, 일반 덱 단조 덱 차이, 단조 덱 0-1 BFS 차이, 덱 시뮬레이션, 양끝 명령 시뮬레이션, 슬라이딩 윈도우 최대값 덱, 0-1 BFS 덱, 순간이동 최단 경로 덱

## 먼저 세 갈래로 자르기

| 질문 signal | deque에 저장하는 것 | front/back가 뜻하는 것 | 정답의 모양 | 먼저 볼 문서 |
|---|---|---|---|---|
| `push_front`, `push_back`, `reverse`, `양쪽 끝 삭제`처럼 **명령 자체가 양끝 조작**이다 | 값 자체, 혹은 문자열/카드/명령 처리 대상 | 실제 자료구조의 앞과 뒤 | 최종 순서, 시뮬레이션 결과 | [덱 기초](./deque-basics.md), [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md) |
| `sliding window maximum/minimum`, `최근 k개 최대/최소`처럼 **연속 window의 extrema**가 필요하다 | 보통 `index` | front는 현재 extrema 후보, back은 지배당한 후보 정리 지점 | 각 window의 max/min | [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md), [Monotonic Queue and Stack](./monotonic-queue-and-stack.md) |
| `0/1 cost shortest path`, `teleport cost 0`, `walk cost 1`처럼 **그래프 최단 경로**다 | 정점/상태 | front는 현재 거리 층, back은 `+1` 비용 층 | 최단 거리표 또는 목표까지 최소 비용 | [Sparse Graph Shortest Paths](../algorithm/sparse-graph-shortest-paths.md) |

가장 빠른 분기 질문은 세 개다.

1. 답이 `최단 거리`인가? 그러면 plain/monotonic이 아니라 0-1 BFS를 먼저 의심한다.
2. 답이 `각 연속 구간의 최대/최소`인가? 그러면 plain deque가 아니라 monotonic deque다.
3. 답이 `명령을 순서대로 시뮬레이션한 결과`인가? 그러면 보통 plain deque다.

## 예제 1: plain deque는 "양끝 명령 시뮬레이션"이다

문제 예시:

> 정수 스트림에 대해 `push_front x`, `push_back x`, `pop_front`, `pop_back`, `reverse` 명령이 주어진다. 모든 명령 후 남아 있는 수열을 출력하라.

이 문제의 핵심은 **양끝 조작 자체가 요구사항**이라는 점이다.

- front/back는 그냥 자료구조의 실제 끝이다.
- 최대값/최솟값 후보를 유지하지 않는다.
- 거리 relax 순서도 없다.

즉 `Deque`를 쓰더라도 어떤 전역 불변식을 붙이지 않는다.
필요하면 `reverse` 플래그만 따로 두고, 실제 삭제 방향만 바꿔서 처리하면 된다.

```java
Deque<Integer> dq = new ArrayDeque<>();
boolean reversed = false;

for (Command cmd : commands) {
    switch (cmd.type()) {
        case PUSH_FRONT -> {
            if (!reversed) dq.offerFirst(cmd.value());
            else dq.offerLast(cmd.value());
        }
        case PUSH_BACK -> {
            if (!reversed) dq.offerLast(cmd.value());
            else dq.offerFirst(cmd.value());
        }
        case POP_FRONT -> {
            if (!reversed) dq.pollFirst();
            else dq.pollLast();
        }
        case POP_BACK -> {
            if (!reversed) dq.pollLast();
            else dq.pollFirst();
        }
        case REVERSE -> reversed = !reversed;
    }
}
```

이 패턴의 signal:

- `자료구조를 설계하라`
- `양쪽 끝에서 넣고 빼라`
- `reverse 상태를 유지하라`
- `카드/문자열/작업열을 그대로 시뮬레이션하라`

이 패턴이 아닌 signal:

- `최근 k개 중 최대`
- `최단 거리`
- `비용 0 또는 1`

## 예제 2: monotonic deque는 "window extrema 후보 압축"이다

문제 예시:

> 배열 `nums`와 `k`가 주어질 때, 길이 `k`인 모든 연속 구간의 최대값을 구하라.

여기서 plain deque가 바로 안 되는 이유는 front가 "가장 먼저 들어온 값"일 뿐, 최대값이 아니기 때문이다.
그래서 deque에 **index를 저장하고**, 두 규칙을 추가한다.

1. window 밖으로 나간 index는 front에서 제거한다.
2. 새 값보다 약한 후보는 back에서 제거한다.

이때 front는 현재 window의 답이 된다.

```java
Deque<Integer> dq = new ArrayDeque<>();

for (int i = 0; i < nums.length; i++) {
    int start = i - k + 1;

    while (!dq.isEmpty() && dq.peekFirst() < start) {
        dq.pollFirst();
    }

    while (!dq.isEmpty() && nums[dq.peekLast()] <= nums[i]) {
        dq.pollLast();
    }

    dq.offerLast(i);

    if (i >= k - 1) {
        answer.add(nums[dq.peekFirst()]);
    }
}
```

이 패턴의 signal:

- `sliding window maximum/minimum`
- `최근 k개 중 최대/최소`
- `모든 길이 k 구간의 extrema`
- `window 밖 원소 만료`

이 패턴이 아닌 signal:

- 합/빈도/중복 개수라서 `Map`이나 `freq[]`가 필요한 경우
- `meeting rooms`, `calendar overlap`처럼 독립 interval 집합인 경우
- 그래프에서 `0 edge`, `1 edge`를 따라 최단 거리를 구하는 경우

핵심 기억법은 단순하다.

- plain deque는 **수열을 보관**한다.
- monotonic deque는 **답이 될 후보만 압축**한다.

## 예제 3: 0-1 BFS는 "distance bucket을 덱으로 흉내 낸다"

문제 예시:

> 정점 `x`에서 `x * 2`로 가는 비용은 `0`, `x - 1`과 `x + 1`로 가는 비용은 `1`일 때 목표 정점까지의 최소 비용을 구하라.

이 문제는 deque를 쓰지만, sliding window와는 완전히 다르다.

- deque에 저장하는 것은 `index`가 아니라 **정점/상태**다.
- front/back는 `window 만료`와 `후보 지배`가 아니라 **거리 층**을 뜻한다.
- `0` 비용 전이는 front, `1` 비용 전이는 back에 넣는다.

즉 monotonic deque처럼 값의 단조성을 유지하는 것이 아니라,
`현재 거리`와 `현재 거리 + 1` 후보를 빠르게 번갈아 처리하는 shortest-path 도구다.

```java
Deque<Integer> dq = new ArrayDeque<>();
Arrays.fill(dist, INF);
dist[start] = 0;
dq.offerFirst(start);

while (!dq.isEmpty()) {
    int cur = dq.pollFirst();

    for (Edge edge : graph[cur]) {
        int next = edge.to();
        int nd = dist[cur] + edge.cost();
        if (nd >= dist[next]) continue;

        dist[next] = nd;
        if (edge.cost() == 0) dq.offerFirst(next);
        else dq.offerLast(next);
    }
}
```

이 패턴의 signal:

- `0-1 BFS`
- `binary edge weight shortest path`
- `teleport shortest path`
- `free/paid edge`
- `deque shortest path`

이 패턴이 아닌 signal:

- `가장 큰 값`, `가장 작은 값`
- `최근 k개`
- `front에서 만료, back에서 약한 후보 제거`

추가 분기:

- 가중치가 일반 양수면 `priority queue` 기반 Dijkstra로 돌아간다.
- 가중치가 음수면 Bellman-Ford/SPFA 계열 판단으로 넘어간다.

## 같은 `offerFirst/offerLast`라도 의미가 다르다

| 연산 | plain deque | monotonic deque | 0-1 BFS |
|---|---|---|---|
| `offerFirst` | 실제 앞쪽 삽입 | 잘 안 쓴다. 보통 만료 제거는 `pollFirst`만 한다 | `0` 비용 전이를 현재 거리 층 앞으로 당긴다 |
| `offerLast` | 실제 뒤쪽 삽입 | 새 index를 후보열 뒤에 붙인다 | `1` 비용 전이를 다음 거리 층 뒤로 미룬다 |
| `pollFirst` | 실제 앞쪽 제거 | window 만료 또는 현재 extrema 읽기 | 현재 가장 가까운 정점을 꺼낸다 |
| `pollLast` | 실제 뒤쪽 제거 | 지배당한 후보 제거 | 거의 쓰지 않는다 |

같은 API를 쓰더라도 "왜 front/back를 만지는가"를 묻는 순간 패턴이 갈린다.

## 빠른 오진 방지 체크리스트

- `graph`, `shortest path`, `cost`, `teleport`, `0/1`가 보이면 0-1 BFS부터 본다.
- `contiguous`, `window`, `recent k`, `max/min`이 보이면 monotonic deque부터 본다.
- `push/pop/reverse`, `양끝`, `시뮬레이션`, `circular deque design`이 보이면 plain deque부터 본다.
- `window`라는 단어만 보고 monotonic deque로 가지 않는다. `sum/count/frequency`면 sliding window + map/freq가 더 직접적이다.
- `deque`라는 단어만 보고 0-1 BFS로 가지 않는다. 최단 거리 문맥이 없으면 대개 다른 패턴이다.

## 한 줄 정리

Deque 문제를 빨리 자르는 기준은 `양끝 시뮬레이션인가`, `window extrema인가`, `0/1 최단 경로인가`다. 같은 컨테이너를 써도 저장 대상과 front/back의 의미가 완전히 다르다.
