# 큐 기초 (Queue Basics)

> 한 줄 요약: 큐는 먼저 들어온 것이 먼저 나오는 FIFO 구조로, 순서를 지키며 처리해야 하는 모든 대기열 문제의 기본 도구다.

**난이도: 🟢 Beginner**

관련 문서:

- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [기본 자료 구조](./basic.md)
- [자료구조 정리](./README.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)

retrieval-anchor-keywords: queue basics, fifo, 큐 입문, 큐가 뭐예요, queue enqueue dequeue, bfs queue, 큐와 스택 차이, beginner queue, queue vs stack, 대기열 자료구조, queue front rear, 선입선출 설명, queue basics basics, queue basics beginner, queue basics intro

## 핵심 개념

큐는 데이터를 **한쪽 끝(rear)으로 넣고 반대쪽 끝(front)에서 꺼내는** 선형 자료구조다.
규칙은 딱 하나, **FIFO(First In, First Out)** — 가장 먼저 들어온 것이 가장 먼저 나간다.

입문자가 자주 헷갈리는 포인트는 이것이다.

- 스택(Stack)은 넣은 쪽에서 꺼내는 LIFO다.
- 큐는 반대쪽에서 꺼내기 때문에 순서가 보존된다.

아래 비유가 도움이 된다.

> 줄 서기: 가장 먼저 줄을 선 사람이 가장 먼저 처리된다. 새로 온 사람은 맨 뒤에 선다.

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

## 상세 분해

큐를 쓸 때 도움이 되는 핵심 패턴은 세 가지다.

- **BFS (너비 우선 탐색)**: 그래프나 트리를 레벨 순서로 탐색할 때 큐를 쓴다. 현재 노드의 이웃을 enqueue하고, 차례로 dequeue해 처리한다.
- **작업 대기열 (Task Queue)**: 요청이 들어오는 순서대로 처리해야 할 때. 프린터 스풀러, 메시지 큐가 이 방식이다.
- **캐시 교체 (FIFO Cache)**: 오래된 항목을 먼저 제거하는 간단한 캐시 정책. 가장 먼저 들어온 항목을 dequeue해 공간을 확보한다.

## 흔한 오해와 함정

- **오해 1: 큐와 스택은 비슷하다.**
  둘 다 선형 구조지만 꺼내는 순서가 반대다. 스택은 LIFO(최근 것 먼저), 큐는 FIFO(오래된 것 먼저)다.

- **오해 2: Java의 `Queue`는 인터페이스다.**
  맞다. `LinkedList`, `ArrayDeque`가 `Queue` 인터페이스를 구현한다. `new Queue()`는 불가능하다.

- **함정: 배열 기반 큐에서 앞쪽 공간이 낭비된다.**
  단순 배열로 큐를 구현하면 dequeue 후 앞 공간을 재사용하지 못한다. 원형 배열(circular array)로 해결한다.

## 실무에서 쓰는 모습

**BFS 그래프 탐색** — 미로 탐색, 최단 경로처럼 "레벨 단위"로 탐색해야 할 때 큐를 쓴다.
시작 노드를 enqueue하고, dequeue한 노드의 이웃을 큐에 추가하는 패턴을 반복한다.

**메시지 브로커** — Kafka, RabbitMQ 같은 메시지 큐 시스템도 FIFO 원칙을 따른다. 생산자(Producer)가 enqueue하고 소비자(Consumer)가 dequeue한다.

## 더 깊이 가려면

- 큐, 덱, 우선순위 큐의 선택 기준은 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- 원형 큐와 링 버퍼의 차이는 [Circular Queue vs Ring Buffer Primer](./circular-queue-vs-ring-buffer-primer.md)

## 면접/시니어 질문 미리보기

1. **큐와 스택의 차이가 무엇인가요?**
   큐는 FIFO(먼저 넣은 것이 먼저 나옴), 스택은 LIFO(마지막에 넣은 것이 먼저 나옴)다. BFS나 대기열 처리는 큐, 되돌리기나 재귀 호출 추적은 스택이 적합하다.

2. **BFS에서 큐가 왜 필요한가요?**
   BFS는 현재 레벨의 노드를 모두 처리한 뒤 다음 레벨로 넘어간다. 큐의 FIFO 성질이 이 레벨 순서를 자연스럽게 보장한다.

3. **Java에서 큐를 어떻게 사용하나요?**
   `Queue<Integer> q = new LinkedList<>();` 또는 `new ArrayDeque<>();`로 선언한다. `ArrayDeque`가 `LinkedList`보다 일반적으로 빠르다. `offer/poll/peek` API를 사용한다.

## 한 줄 정리

큐는 "먼저 들어온 것이 먼저 나온다"는 FIFO 규칙 하나로, BFS·대기열·메시지 처리처럼 순서 보존이 중요한 문제를 깔끔하게 풀어준다.
