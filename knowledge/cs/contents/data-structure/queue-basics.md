# 큐 기초 (Queue Basics)

> 한 줄 요약: 큐는 먼저 들어온 것이 먼저 나오는 FIFO 구조로, 순서를 지키며 처리해야 하는 모든 대기열 문제의 기본 도구다.

**난이도: 🟢 Beginner**

관련 문서:

- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [ArrayDeque vs BlockingQueue 서비스 handoff 프라이머](./arraydeque-vs-blockingqueue-service-handoff-primer.md)
- [기본 자료 구조](./basic.md)
- [자료구조 정리](./README.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)

retrieval-anchor-keywords: queue basics, fifo, 큐 입문, 큐가 뭐예요, queue enqueue dequeue, bfs queue difference, queue는 도구 bfs는 문제 유형, queue vs bfs beginner, 큐와 스택 차이, beginner queue, queue vs stack, 대기열 자료구조, queue front rear, 처음 queue 헷갈림, arraydeque queue beginner

## 핵심 개념

큐는 데이터를 **한쪽 끝(rear)으로 넣고 반대쪽 끝(front)에서 꺼내는** 선형 자료구조다.
규칙은 딱 하나, **FIFO(First In, First Out)** — 가장 먼저 들어온 것이 가장 먼저 나간다.

입문자가 처음 잡아야 할 감각은 "`누가 먼저 처리되나`"다.

- 먼저 도착한 원소를 그대로 처리하면 큐다.
- 가장 작은 값이나 가장 급한 작업을 먼저 꺼내면 큐가 아니라 우선순위 큐다.
- 양쪽 끝을 번갈아 써야 하면 큐보다 덱을 먼저 의심한다.

입문자가 자주 헷갈리는 포인트는 이것이다.

- 스택(Stack)은 넣은 쪽에서 꺼내는 LIFO다.
- 큐는 반대쪽에서 꺼내기 때문에 순서가 보존된다.

아래 비유가 도움이 된다.

> 줄 서기: 가장 먼저 줄을 선 사람이 가장 먼저 처리된다. 새로 온 사람은 맨 뒤에 선다.

문제 문장을 이렇게 번역하면 초반 오분류가 크게 줄어든다.

| 문제 문장 | 실제로 묻는 것 | 첫 구조 |
|---|---|---|
| `들어온 순서대로 처리` | 먼저 온 것을 먼저 꺼내는가 | 큐 |
| `가까운 칸부터 한 겹씩 본다` | 거리 1, 2, 3 순서로 넓어지는가 | 큐 + BFS |
| `가장 급한 작업부터` | 도착 순서가 아니라 우선순위가 기준인가 | 우선순위 큐 |

처음엔 아래 비교만 정확히 자르면 queue 오분류가 크게 줄어든다.

| 문장 신호 | 실제 핵심 | 첫 출발점 |
|---|---|---|
| `먼저 받은 요청부터 처리` | FIFO 처리 순서 | 큐 |
| `가까운 칸부터 한 겹씩 확장` | 거리 순서 탐색 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `id로 한 건 바로 찾기` | key lookup | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) |
| `가장 급한 작업부터 처리` | 우선순위 기준 | [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md) |

queue인지 다시 자를 때는 아래 3문장만 보면 된다.

1. `먼저 들어온 것`이 먼저 나가야 하나?
2. 아니면 `더 가까운 칸`, `더 짧은 거리`처럼 탐색 레벨이 핵심인가?
3. 아니면 `더 급한 작업`, `더 작은 값`처럼 우선순위가 핵심인가?

1번이면 queue, 2번이면 BFS에서 queue를 도구로 쓰는 상황, 3번이면 우선순위 큐다.

Java 문법까지 붙이면 한 줄 습관은 이것이다.

```java
Queue<Integer> queue = new ArrayDeque<>();
```

이 한 줄은 "`덱 문제를 풀고 있다`"가 아니라
"구현체는 `ArrayDeque`를 쓰지만, 이번 코드는 FIFO queue 연산만 쓴다"는 뜻이다.

## 한눈에 보기

| 연산 | 의미 | 시간 복잡도 |
|---|---|---|
| `enqueue(x)` | rear에 원소 추가 | O(1) |
| `dequeue()` | front 원소 제거 후 반환 | O(1) |
| `peek()` | front 원소 조회 (제거 없음) | O(1) |
| `isEmpty()` | 큐가 비어 있는지 확인 | O(1) |

```text
enqueue(1) → [1]
enqueue(2) → [1, 2]
enqueue(3) → [1, 2, 3]
dequeue()  → 1 반환, [2, 3]
peek()     → 2 조회, [2, 3]
```

처음 문제를 읽을 때는 아래 한 줄 표로 먼저 자르면 덜 헷갈린다.

| 문제 문장 | 먼저 떠올릴 구조 | 이유 |
|---|---|---|
| `요청이 들어온 순서대로 처리` | 큐 | 도착 순서가 곧 처리 순서다 |
| `가장 작은 값부터 꺼내기` | 우선순위 큐 | FIFO가 아니라 우선순위가 기준이다 |
| `앞에서도 빼고 뒤에서도 뺀다` | 덱 | 꺼내는 쪽이 하나로 고정되지 않는다 |

| 구조 | 먼저 꺼내는 기준 | 대표 질문 |
|---|---|---|
| 큐 | 먼저 들어온 것 | `요청 순서대로 처리` |
| 스택 | 가장 나중에 넣은 것 | `되돌리기`, `최근 작업 취소` |
| 우선순위 큐 | 우선순위가 가장 큰 것 또는 작은 것 | `가장 급한 작업부터` |

## queue와 BFS를 먼저 분리하기

초보자 기준으로는 아래 한 줄이 핵심이다.

> `queue는 순서를 만드는 도구`, `BFS는 그 도구를 써서 가까운 것부터 탐색하는 문제 풀이 방식`

같은 문장에 `queue`와 `BFS`가 함께 나와도, 먼저 묻는 것이 다르다.

| 지금 보이는 신호 | 먼저 묻는 것 | 바로 떠올릴 첫 생각 |
|---|---|---|
| `먼저 온 요청부터 처리` | 처리 순서가 FIFO인가 | queue |
| `미로에서 가까운 칸부터` | 탐색이 레벨 순서인가 | BFS, 구현 도구는 queue |
| `갈 수 있나?`, `최소 몇 번인가?` | 연결/최단 경로 질문인가 | [그래프 기초](./graph-basics.md) 또는 [Connectivity Question Router](./connectivity-question-router.md) |

짧은 예시로 보면 더 분명하다.

| 상황 | queue가 답인가 | BFS가 답인가 | 이유 |
|---|---|---|---|
| 프린터 작업이 들어온 순서대로 출력 | 예 | 아니오 | 탐색이 아니라 FIFO 처리다 |
| 미로에서 출구까지 최소 이동 횟수 찾기 | 도구로는 예 | 예 | 문제 핵심이 `가까운 칸부터 한 겹씩`이다 |
| 주문 `orderId`로 바로 조회 | 아니오 | 아니오 | 이 경우 핵심은 queue가 아니라 map lookup이다 |

헷갈릴 때는 이렇게 자르면 된다.

1. `순서대로 처리`가 핵심이면 queue다.
2. `가까운 것부터 탐색`이 핵심이면 BFS다.
3. BFS를 고른 뒤에야 `그 BFS를 queue로 구현한다`고 붙인다.

## 상세 분해

큐를 쓸 때 도움이 되는 핵심 패턴은 세 가지다.

- **BFS (너비 우선 탐색)**: 그래프나 트리를 레벨 순서로 탐색할 때 큐를 쓴다. 현재 노드의 이웃을 enqueue하고, 차례로 dequeue해 처리한다.
- **작업 대기열 (Task Queue)**: 요청이 들어오는 순서대로 처리해야 할 때. 프린터 스풀러, 메시지 큐가 이 방식이다.
- **캐시 교체 (FIFO Cache)**: 오래된 항목을 먼저 제거하는 간단한 캐시 정책. 가장 먼저 들어온 항목을 dequeue해 공간을 확보한다.

짧은 BFS trace를 붙이면 queue 감각이 더 빨리 잡힌다.

```text
시작: q = [A]
poll A -> B, C enqueue -> q = [B, C]
poll B -> D enqueue    -> q = [C, D]
poll C -> E enqueue    -> q = [D, E]
```

큐가 먼저 들어온 `B`를 먼저 꺼내기 때문에 거리 1 레벨을 다 본 뒤 거리 2 레벨로 넘어간다.

## 흔한 오해와 함정

- **오해 1: 큐와 스택은 비슷하다.**
  둘 다 선형 구조지만 꺼내는 순서가 반대다. 스택은 LIFO(최근 것 먼저), 큐는 FIFO(오래된 것 먼저)다.
- **오해 1-0: queue와 BFS는 같은 말이다.**
  아니다. queue는 FIFO 도구이고, BFS는 그래프/미로를 레벨 순서로 탐색하는 방식이다. `가까운 칸부터`, `최소 이동 횟수`, `최소 환승 횟수` 같은 문장이 보이면 먼저 BFS 문제인지 판단하고, 그다음 구현 도구로 queue를 붙인다.
- **오해 1-1: BFS에 쓰는 큐와 우선순위 큐가 비슷하다.**
  아니다. BFS는 "먼저 발견한 정점"을 먼저 처리하므로 FIFO 큐다. 가중치가 있으면 우선순위 큐 기반 다익스트라로 넘어간다.

- **오해 2: Java의 `Queue`는 인터페이스다.**
  맞다. `LinkedList`, `ArrayDeque`가 `Queue` 인터페이스를 구현한다. `new Queue()`는 불가능하다.
- **오해 2-1: BFS나 서비스 코드의 기본 큐 구현은 `LinkedList`다.**
  꼭 그렇지 않다. Java에서는 보통 `Queue<T> q = new ArrayDeque<>();`를 기본값으로 두고, `LinkedList`를 꼭 써야 할 이유가 있는지 나중에 확인하는 편이 더 안전하다.
- **오해 2-2: `ArrayDeque`를 쓰면 BFS가 덱 문제로 바뀐다.**
  아니다. 구현체 이름이 `Deque`를 포함해도, BFS에서 실제로 쓰는 것은 `offer`/`poll` 기반 FIFO 규칙이다. `offerFirst`/`pollLast`처럼 양끝 제어가 등장할 때만 "덱 능력"이 핵심이다.
- **오해 3: BFS에서는 dequeue할 때 방문 표시해도 같다.**
  아니다. 보통은 enqueue하는 순간 방문 표시를 해야 같은 정점이 여러 번 들어가는 일을 막을 수 있다.
- **오해 4: `queue`라는 단어가 나오면 무조건 자료구조 문제다.**
  아니다. `최소 이동 횟수`, `가까운 칸부터`, `레벨 순서` 같은 문장은 알고리즘 쪽에서는 BFS 신호다. 큐는 그 BFS를 구현하는 도구다.
- **오해 5: 한 문제에는 queue나 map 중 하나만 나온다.**
  아니다. 예를 들어 주문 시스템에서 `대기열 처리`는 queue로, `orderId 조회`는 map으로 푼다. 한 기능 안에서도 "무엇을 먼저 묻는가"에 따라 구조가 갈린다.
- **오해 6: BFS에서 queue만 있으면 충분하다.**
  아니다. 보통은 `queue + visited set/map`이 같이 간다. queue는 처리 순서를 만들고, visited는 같은 칸이나 정점이 다시 들어오는 일을 막는다.

- **함정: 배열 기반 큐에서 앞쪽 공간이 낭비된다.**
  단순 배열로 큐를 구현하면 dequeue 후 앞 공간을 재사용하지 못한다. 원형 배열(circular array)로 해결한다.

## 실무에서 쓰는 모습

**BFS 그래프 탐색** — 미로 탐색, 최단 경로처럼 "레벨 단위"로 탐색해야 할 때 큐를 쓴다.
시작 노드를 enqueue하고, dequeue한 노드의 이웃을 큐에 추가하는 패턴을 반복한다. `회원 추천 1촌 -> 2촌 -> 3촌`처럼 가까운 관계부터 넓혀 가는 기능도 같은 감각이다.
Java에선 이때 `Queue<Node> q = new ArrayDeque<>();`를 많이 쓰는데, 포인트는 `ArrayDeque`라는 이름보다 "이번 BFS가 FIFO만 필요하다"는 사용 의도다.

**메시지 브로커** — Kafka, RabbitMQ 같은 메시지 큐 시스템도 FIFO 원칙을 따른다. 생산자(Producer)가 enqueue하고 소비자(Consumer)가 dequeue한다.

## 더 깊이 가려면

- 큐, 덱, 우선순위 큐의 선택 기준은 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- Java에서 BFS/서비스 코드 큐 구현 기본값을 짧게 정리한 카드는 [ArrayDeque vs LinkedList 큐 선택 카드](./arraydeque-vs-linkedlist-queue-choice-card.md)
- 로컬 FIFO와 멀티스레드 worker handoff 큐를 언제 갈라야 하는지는 [ArrayDeque vs BlockingQueue 서비스 handoff 프라이머](./arraydeque-vs-blockingqueue-service-handoff-primer.md)
- 원형 큐와 링 버퍼의 차이는 [Circular Queue vs Ring Buffer Primer](./circular-queue-vs-ring-buffer-primer.md)
- BFS에서 큐가 왜 레벨 순서를 보장하는지는 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- `갈 수 있나?`, `경로 하나`, `최소 이동 횟수`를 먼저 분기하고 싶다면 [Connectivity Question Router](./connectivity-question-router.md)

## 다음 단계

- 큐, 덱, 우선순위 큐를 문제 문장으로 먼저 자르고 싶다면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- BFS에서 큐가 왜 `거리 순서`를 만드는지 다시 붙이고 싶다면 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- `queue는 도구, BFS는 문제 유형` 감각을 그래프 질문으로 다시 확인하고 싶다면 [그래프 기초](./graph-basics.md)
- 원형 큐와 링 버퍼까지 이어 보고 싶다면 [Circular Queue vs Ring Buffer Primer](./circular-queue-vs-ring-buffer-primer.md)
- `queue`와 `map`을 자꾸 섞는다면 [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md)

## 한 줄 정리

큐는 "먼저 들어온 것이 먼저 나온다"는 FIFO 규칙 하나로, BFS·대기열·메시지 처리처럼 순서 보존이 중요한 문제를 깔끔하게 풀어준다.
