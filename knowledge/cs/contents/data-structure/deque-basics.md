---
schema_version: 3
title: 덱 기초
concept_id: data-structure/deque-basics
canonical: true
category: data-structure
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- deque-stack-queue-basics
- arraydeque-java
- sliding-window-router
aliases:
- deque basics
- double ended queue
- arraydeque java
- deque vs queue vs stack
- addFirst addLast pollFirst pollLast
- plain deque simulation
- monotonic deque entrypoint
- 덱 입문
- 양방향 큐
symptoms:
- Deque를 Queue나 Stack과 같은 단방향 구조로 이해해 양끝 삽입 삭제를 놓친다
- Java에서 Stack이나 LinkedList를 기본 선택하고 ArrayDeque의 장단점을 비교하지 않는다
- plain deque, monotonic deque, 0-1 BFS를 모두 같은 deque 사용법으로 섞는다
intents:
- definition
- comparison
- drill
prerequisites:
- data-structure/stack-basics
- data-structure/queue-basics
next_docs:
- data-structure/queue-vs-deque-vs-priority-queue-primer
- data-structure/deque-router-example-pack
- data-structure/monotonic-deque-walkthrough
- algorithm/two-pointer-intro
linked_paths:
- contents/data-structure/queue-vs-deque-vs-priority-queue-primer.md
- contents/data-structure/deque-router-example-pack.md
- contents/data-structure/stack-basics.md
- contents/data-structure/queue-basics.md
- contents/algorithm/two-pointer-intro.md
- contents/data-structure/monotonic-deque-walkthrough.md
confusable_with:
- data-structure/queue-basics
- data-structure/stack-basics
- data-structure/queue-vs-deque-vs-priority-queue-primer
- data-structure/monotonic-deque-walkthrough
- algorithm/zero-one-bfs-state-space-bridge
forbidden_neighbors: []
expected_queries:
- Deque는 Queue와 Stack과 무엇이 달라?
- Java에서 Stack 대신 ArrayDeque를 쓰는 이유가 뭐야?
- addFirst addLast pollFirst pollLast는 각각 어느 쪽 끝을 다뤄?
- plain deque와 monotonic deque와 0-1 BFS는 어떻게 구분해?
- sliding window 최솟값 문제에서 Deque를 왜 쓰는지 입문자용으로 설명해줘
contextual_chunk_prefix: |
  이 문서는 Deque beginner primer로, 양쪽 끝 삽입 삭제, Java ArrayDeque,
  queue와 stack 대체, plain deque, monotonic deque, 0-1 BFS 라우팅을
  구분한다. 덱과 큐, 덱과 스택 차이를 묻는 질문이 본 문서에 매핑된다.
---
# 덱 기초 (Deque Basics)

> 한 줄 요약: 덱(Deque)은 앞과 뒤 양쪽에서 삽입·삭제가 가능한 구조로, 스택과 큐를 모두 대체할 수 있는 더 유연한 선형 자료구조다.

**난이도: 🟢 Beginner**

관련 문서:

- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [Deque Router Example Pack](./deque-router-example-pack.md)
- [스택 기초](./stack-basics.md)
- [자료구조 정리](./README.md)
- [두 포인터 입문](../algorithm/two-pointer-intro.md)

retrieval-anchor-keywords: deque basics, double ended queue, 덱 입문, 덱이 뭐예요, deque vs queue vs stack, arraydeque java, addfirst addlast, 양방향 큐 설명, 덱과 스택 차이, 덱과 큐 차이, beginner deque, deque sliding window, plain deque, plain deque simulation, deque router

## 핵심 개념

덱(Deque, Double-Ended Queue)은 **앞(front)과 뒤(rear) 양쪽**에서 삽입과 삭제가 모두 가능한 선형 자료구조다.

입문자가 자주 헷갈리는 포인트는 이것이다.

- 큐는 rear에만 넣고 front에서만 꺼낸다(FIFO).
- 스택은 한쪽 끝에서만 넣고 꺼낸다(LIFO).
- 덱은 **양쪽 끝 모두에서** 삽입과 삭제가 가능해서 스택과 큐를 모두 흉내 낼 수 있다.

Java에서는 `ArrayDeque`가 가장 많이 쓰이고, 일반적으로 `Stack`이나 `LinkedList`보다 성능이 좋다.

## 한눈에 보기

```text
          front              rear
[addFirst] [1, 2, 3, 4, 5] [addLast]
[pollFirst]                [pollLast]
```

| 연산 | 의미 | 시간 복잡도 |
|---|---|---|
| `addFirst(x)` | front에 추가 | O(1) |
| `addLast(x)` | rear에 추가 | O(1) |
| `pollFirst()` | front 제거 후 반환 | O(1) |
| `pollLast()` | rear 제거 후 반환 | O(1) |
| `peekFirst()` | front 조회 (제거 없음) | O(1) |
| `peekLast()` | rear 조회 (제거 없음) | O(1) |

## 상세 분해

덱이 스택·큐보다 유용한 세 가지 상황을 살펴본다.

- **스택 대용**: `addFirst` + `pollFirst`만 사용하면 LIFO 동작이다. Java에서 `Stack` 클래스 대신 `ArrayDeque`를 쓰는 것이 공식 권장이다.
- **큐 대용**: `addLast` + `pollFirst`만 사용하면 FIFO 동작이다. `LinkedList` 대신 `ArrayDeque`가 메모리 효율이 좋다.
- **슬라이딩 윈도우 최솟값/최댓값**: 덱의 양쪽에서 제거가 가능해서, 윈도우 범위를 벗어난 오래된 인덱스를 앞에서 제거하고 새 원소와 비교해 뒤에서 제거하는 단조 덱 패턴을 구현할 수 있다.

같은 `Deque`라도 세부 패턴은 갈린다.

- 양끝 명령을 그대로 시뮬레이션하면 **plain deque**
- 연속 구간의 max/min 후보를 압축하면 **monotonic deque**
- 그래프에서 `0 edge`는 앞, `1 edge`는 뒤로 보내면 **0-1 BFS**

빠른 분기 예시는 [Deque Router Example Pack](./deque-router-example-pack.md)에 묶어 두었다.

## 흔한 오해와 함정

- **오해 1: Deque는 "deck"이라고 읽는다.**
  공식 발음은 "deck"이다. 알고리즘 설명에서 "double-ended queue"의 약자임을 명시하면 혼동이 줄어든다.

- **오해 2: Java `ArrayDeque`는 null을 허용한다.**
  `ArrayDeque`는 null을 허용하지 않는다. null을 저장해야 한다면 `LinkedList`를 써야 한다.

- **함정: `peek()`는 `peekFirst()`와 같다.**
  `ArrayDeque.peek()`은 front를 반환한다. rear를 보려면 반드시 `peekLast()`를 명시해야 한다. 혼용하면 버그가 생긴다.

## 실무에서 쓰는 모습

**브라우저 앞/뒤 이동** — "뒤로 가기" 스택과 "앞으로 가기" 스택 대신, 덱 하나로 현재 위치를 가운데로 두고 앞뒤 이동을 표현할 수 있다.

**슬라이딩 윈도우 최솟값** — 크기 K의 윈도우를 오른쪽으로 이동하면서 최솟값을 유지할 때, 덱에 인덱스를 저장하고 front에서 범위를 벗어난 것을 제거, rear에서 현재 값보다 큰 것을 제거한다. O(n) 처리가 된다.

## 더 깊이 가려면

- 덱·큐·우선순위 큐 중 선택 기준은 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- plain deque / monotonic deque / 0-1 BFS를 한 번에 구분하는 예시는 [Deque Router Example Pack](./deque-router-example-pack.md)
- 단조 덱을 이용한 슬라이딩 윈도우 패턴은 [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)

## 면접/시니어 질문 미리보기

1. **덱, 스택, 큐의 차이는 무엇인가요?**
   스택은 LIFO(한쪽 끝만), 큐는 FIFO(앞에서 꺼내고 뒤에 넣음), 덱은 양쪽 끝에서 모두 삽입·삭제 가능하다. 덱은 스택과 큐를 둘 다 흉내 낼 수 있다.

2. **Java에서 스택을 쓸 때 `Stack` 클래스보다 `ArrayDeque`를 권장하는 이유는?**
   `Stack`은 `Vector`를 상속해 모든 연산에 동기화 오버헤드가 있다. `ArrayDeque`는 동기화가 없어 단일 스레드에서 빠르고, Java 공식 문서도 `ArrayDeque`를 권장한다.

3. **덱으로 슬라이딩 윈도우 최솟값을 O(n)에 구하는 방법은?**
   덱에 인덱스를 저장한다. 새 원소를 추가할 때 rear에서 현재 원소보다 큰 값을 모두 제거한다(단조 증가 유지). front가 윈도우 범위를 벗어나면 제거한다. 매 위치에서 front가 윈도우의 최솟값이다.

## 한 줄 정리

덱은 양쪽 끝에서 O(1) 삽입·삭제를 제공해 스택과 큐를 모두 대체할 수 있으며, Java에서는 `ArrayDeque`가 `Stack`과 `LinkedList`보다 성능이 좋아 범용으로 권장된다.
