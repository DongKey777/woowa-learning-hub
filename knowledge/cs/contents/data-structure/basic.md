# 기본 자료 구조

> 작성자 : [서그림](https://github.com/Seogeurim)

> 한 줄 요약: 배열, 연결 리스트, 스택, 큐, 해시 테이블, 힙, 트리, 그래프, 유니온-파인드는 "어떤 연산을 빠르게 만들고 싶은가"를 기준으로 고르는 기본 도구다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: basic basics, basic beginner, basic intro, data structure basics, beginner data structure, 처음 배우는데 basic, basic 입문, basic 기초, what is basic, how to basic
> retrieval-anchor-keywords: data structure basics, beginner data structure, array basics, dynamic array, linked list basics, singly linked list, doubly linked list, array vs linked list, stack basics, lifo, queue basics, fifo, queue terminology, queue api terms, enqueue dequeue peek, front rear head tail, circular queue basics, ring buffer basics, circular queue vs ring buffer, deque basics, queue vs deque, priority queue vs queue, hash table basics, hash map basics, collision basics, heap basics, priority queue basics, min heap, max heap, tree basics, binary tree basics, binary search tree basics, bst basics, binary tree vs bst vs heap, binary tree traversal basics, preorder inorder postorder, level order traversal, tree traversal routing, graph basics, graph representation, adjacency list, adjacency matrix, edge list, union find basics, union-find basics, disjoint set union basics, DSU basics, connected components, cycle detection, backend data structure, tradeoff
>
> 관련 문서:
> - [자료구조 정리](./README.md)
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
> - [Circular Queue vs Ring Buffer Primer](./circular-queue-vs-ring-buffer-primer.md)
> - [Ring Buffer](./ring-buffer.md)
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [Heap Variants](./heap-variants.md)
> - [Binary Tree vs BST vs Heap Bridge](./binary-tree-vs-bst-vs-heap-bridge.md)
> - [Binary Tree Traversal Routing Guide](./binary-tree-traversal-routing-guide.md)
> - [Union-Find Deep Dive](./union-find-deep-dive.md)
> - [그래프 관련 알고리즘](../algorithm/graph.md)
> - [알고리즘 기본](../algorithm/basic.md)

<details>
<summary>Table of Contents</summary>

- [빠른 비교표](#빠른-비교표)
- [Array (배열)](#array-배열)
- [Linked List (연결 리스트)](#linked-list-연결-리스트)
- [Stack (스택)](#stack-스택)
- [Queue (큐)](#queue-큐)
- [Hash Table (해시 테이블)](#hash-table-해시-테이블)
- [Heap (힙)](#heap-힙)
- [Tree (트리)](#tree-트리)
- [Binary Tree (이진 트리)](#binary-tree-이진-트리)
- [Graph (그래프)](#graph-그래프)
- [Union-Find (유니온-파인드)](#union-find-유니온-파인드)

</details>

---

자료구조는 **데이터를 어떤 모양으로 저장하고 어떤 연산을 빠르게 만들지 결정하는 설계**다.
같은 데이터를 다뤄도, 무엇을 자주 하느냐에 따라 최적의 구조가 달라진다.

- `index`로 바로 읽고 싶으면 `Array`
- 맨 앞/뒤 삽입과 삭제 흐름이 중요하면 `Linked List`, `Queue`, `Deque`
- 가장 최근 작업을 먼저 되돌리면 `Stack`
- `key -> value` 조회가 핵심이면 `Hash Table`
- 가장 작은 값/큰 값을 반복해서 꺼내면 `Heap`
- 부모-자식 관계가 핵심이면 `Tree`
- 관계가 복잡하고 경로/연결성/순서가 중요하면 `Graph`
- "같은 그룹인가?"를 반복해 묻고 합치면 `Union-Find`

이 문서는 각 구조의 **입문 감각**을 먼저 잡아두고, 더 깊은 내부 구현이나 응용 문서로 자연스럽게 이어지도록 구성했다.

## 빠른 비교표

| 구조 | 빠르게 만들고 싶은 연산 | 대표 강점 | 대표 약점 |
|---|---|---|---|
| Array | 임의 위치 조회 | `index` 접근이 빠르다 | 중간 삽입/삭제가 비싸다 |
| Linked List | 위치를 알고 있는 노드 주변 변경 | 삽입/삭제가 유연하다 | 임의 접근이 느리다 |
| Stack | 마지막 작업 push/pop | 구현이 단순하고 LIFO에 강하다 | 중간 원소 접근이 부자연스럽다 |
| Queue | 먼저 온 작업 처리 | 순서 보장에 강하다 | 우선순위가 섞이면 다른 구조가 필요하다 |
| Hash Table | key로 값 찾기 | 평균 `O(1)` 조회 | 순서/범위 질의가 약하다 |
| Heap | 최소/최대값 반복 추출 | `peek`와 `poll`이 빠르다 | 전체 정렬 상태는 보장하지 않는다 |
| Tree | 계층 구조 표현 | 부모-자식 관계가 자연스럽다 | 균형이 무너지면 성능이 나빠질 수 있다 |
| Graph | 관계/경로/연결성 표현 | 현실 문제를 풍부하게 모델링한다 | 표현과 알고리즘 선택이 더 어렵다 |
| Union-Find | 그룹 병합과 같은 집합 여부 | 연결성 질의가 매우 빠르다 | 실제 경로나 순서는 알려주지 않는다 |

---

## Array (배열)

배열은 같은 타입의 데이터를 **연속된 메모리 공간**에 저장하는 가장 기본적인 구조다.
핵심 감각은 `index` 하나로 원하는 위치를 바로 찾을 수 있다는 점이다.

- 잘 맞는 문제:
  - 점수표, 좌표, ID 매핑처럼 위치가 곧 의미인 데이터
  - 최근 N개 값을 담는 고정 길이 버퍼
  - 정렬 결과, prefix sum, DP 테이블 같은 전처리 저장소
- 주요 복잡도:
  - 조회: `O(1)`
  - 맨 끝 삽입: 동적 배열이면 amortized `O(1)`
  - 중간 삽입/삭제: `O(n)`
- 초보자 주의:
  - `ArrayList` 같은 동적 배열도 **중간 삽입/삭제는 여전히 비싸다**
  - "배열은 무조건 빠르다"가 아니라 **읽기와 cache locality에 강하다**가 더 정확하다

```java
int[] values = new int[5];
values[0] = 10;
values[1] = 20;
values[2] = 30;
```

배열은 다른 구조의 기준점이기도 하다.
힙은 배열 인덱스로 구현할 수 있고, 인접 행렬도 결국 2차원 배열이며, 많은 알고리즘의 보조 메모리가 배열이다.

---

## Linked List (연결 리스트)

연결 리스트는 각 노드가 다음 노드(또는 이전 노드)의 참조를 들고 이어지는 구조다.
배열처럼 연속 메모리에 있지 않아 random access는 느리지만, **이미 위치를 알고 있는 노드 주변을 수정하는 작업**에는 자연스럽다.

- 잘 맞는 문제:
  - 노드 삽입/삭제가 자주 일어나는 흐름
  - LRU처럼 순서를 자주 앞뒤로 옮기는 구조
  - 큐/스택의 연결 기반 구현
- 주요 복잡도:
  - 조회: `O(n)`
  - 맨 앞 삽입/삭제: `O(1)`
  - 중간 삽입/삭제: 노드를 이미 찾았으면 `O(1)`, 찾는 비용까지 합치면 보통 `O(n)`
- 초보자 주의:
  - "삽입/삭제가 O(1)"은 **삽입 위치를 이미 알고 있을 때** 이야기다
  - 실제 서비스에서는 메모리 locality가 약해 배열보다 느린 경우가 많다

### Linked List 구현

- [Singly Linked List](./code/LinkedList/SinglyLinkedList.java)
- [Doubly Linked List](./code/LinkedList/DoublyLinkedList.java)
- 위 코드 실행 : [LinkedListExample.java](./code/LinkedList/LinkedListExample.java)

### Singly vs Doubly

| 구조 | 장점 | 단점 | 언제 자연스러운가 |
|---|---|---|---|
| Singly Linked List | 구현이 단순하다 | 이전 노드로 못 간다 | 한 방향 순회만 있으면 충분할 때 |
| Doubly Linked List | 앞뒤 이동이 쉽다 | 포인터 메모리가 더 든다 | 순서 변경, 삭제, 캐시 관리 |

더 깊게 가면 [LRU Cache Design](./lru-cache-design.md)에서 `HashMap + Doubly Linked List` 조합이 왜 자주 등장하는지 연결해 볼 수 있다.

---

## Stack (스택)

스택은 마지막에 넣은 것이 먼저 나오는 **LIFO(Last In, First Out)** 구조다.
"가장 최근 작업부터 되돌리기"가 핵심인 흐름이면 스택을 먼저 떠올리면 된다.

- 대표 연산:
  - `push`: 넣기
  - `pop`: 꺼내기
  - `peek`: 맨 위 값 보기
- 주요 복잡도:
  - `push/pop/peek`: `O(1)`
- 잘 맞는 문제:
  - 함수 호출 스택
  - 괄호 검사
  - DFS
  - undo/redo
  - 수식 변환과 파싱
- 초보자 주의:
  - 스택은 "최근 것 하나"만 빠르게 다루는 구조다
  - 중간 원소를 자주 읽어야 하면 다른 구조가 더 낫다

### Stack 구현

- [Array를 통해 구현한 Stack](./code/Stack/ArrayStack.java)
- [Singly Linked List를 통해 구현한 Stack](./code/Stack/LinkedStack.java)
- 위 코드 실행 : [StackExample.java](./code/Stack/StackExample.java)

스택은 자료구조 자체보다도 **문제의 시간 흐름**을 읽는 힌트로 중요하다.
예외 처리, 롤백, parser backtracking을 볼 때 "마지막 상태부터 되돌린다"면 스택 관점이 숨어 있는 경우가 많다.

---

## Queue (큐)

큐는 먼저 들어온 것이 먼저 나오는 **FIFO(First In, First Out)** 구조다.
순서가 중요한 대기열이라면 가장 먼저 떠올릴 기본 구조다.

- 대표 연산:
  - `enqueue`: 뒤에 넣기
  - `dequeue`: 앞에서 꺼내기
  - `peek`: 맨 앞 값 보기
- 주요 복잡도:
  - `enqueue/dequeue/peek`: `O(1)`
- 잘 맞는 문제:
  - 작업 큐
  - 이벤트 루프
  - 네트워크 패킷 버퍼
  - BFS
- 초보자 주의:
  - `Queue`와 `PriorityQueue`는 다르다
  - "먼저 들어온 순서"가 중요하면 큐, "우선순위가 높은 것"이 중요하면 힙 계열을 쓴다

### Queue 용어 브리지

초보자가 가장 많이 헷갈리는 지점은 "**queue의 규칙**"과 "**queue를 구현하는 용어**"를 한 덩어리로 외우는 것이다.

| 구분 | 먼저 기억할 말 | 지금 묻는 핵심 |
|---|---|---|
| FIFO queue API | `enqueue`, `dequeue`, `peek`, `front` | "무엇을 할 수 있는가?" |
| Circular queue 구현 | `front`, `rear`, `isFull`, `wraparound` | "배열로 FIFO queue를 어떻게 구현하는가?" |
| Ring buffer 구현/운영 | `head`, `tail`, `capacity`, `overwrite`, `backpressure` | "고정 크기 버퍼를 어떤 정책으로 굴리는가?" |

- `enqueue/dequeue`는 **FIFO 규칙을 설명하는 API 용어**다.
- `front/rear`는 원형 큐 구현 문제에서 자주 나오는 **큐의 앞/뒤 포인터 이름**이다.
- `head/tail`은 ring buffer에서 자주 보이는 **읽기/쓰기 위치 이름**이지만, 문서마다 "현재 원소"인지 "다음 슬롯"인지 정의가 조금 다를 수 있다.
- 즉 `queue`, `circular queue`, `ring buffer`는 완전히 분리된 세계가 아니라, **같은 FIFO 계열을 어떤 관점에서 설명하느냐**가 다르다.

같은 패킷 대기열도 설명 초점에 따라 이름이 달라질 수 있다.

- "먼저 들어온 패킷을 먼저 처리한다"를 말하면 `queue`
- "배열 끝에서 처음으로 돌아오게 구현한다"를 말하면 `circular queue`
- "고정 용량에서 overwrite/backpressure 정책을 고른다"를 말하면 `ring buffer`

### Queue 구현

- [Array를 통해 구현한 Queue](./code/Queue/ArrayQueue.java)
- [Singly Linked List를 통해 구현한 Queue](./code/Queue/LinkedQueue.java)
- 위 코드 실행 : [QueueExample.java](./code/Queue/QueueExample.java)

## Queue (큐) (계속 2)

> Java에서 `Queue` 인터페이스는 `LinkedList`, `ArrayDeque`, `PriorityQueue` 같은 구현체와 함께 쓸 수 있다.
> `FIFO queue`인지 `priority queue`인지 먼저 구분하는 습관이 중요하다.

`queue`, `deque`, `priority queue`가 한꺼번에 나와 헷갈리면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)에서 `도착 순서`, `양쪽 끝 제어`, `우선순위` 기준으로 먼저 분리해 두면 이후 BFS, sliding window, heap 문제 라우팅이 훨씬 쉬워진다.

`enqueue/dequeue`와 `front/rear/head/tail`이 한꺼번에 섞이면 [Circular Queue vs Ring Buffer Primer](./circular-queue-vs-ring-buffer-primer.md)에서 `queue API`, `원형 배열 구현`, `bounded buffer 운영`을 따로 분리해 보는 편이 빠르다. 시스템 쪽 정책과 예측 가능한 지연시간까지 보려면 [Ring Buffer](./ring-buffer.md)로 이어서 읽으면 된다.

큐는 요청과 처리 사이의 완충재 역할도 한다.
백그라운드 작업 분배, 메시지 소비, rate limiter 앞단의 대기열에서 자주 보인다.

---

## Hash Table (해시 테이블)

해시 테이블은 키를 해시값으로 바꿔 **버킷(bucket)** 을 빠르게 찾는 `key -> value` 구조다.
Java의 `HashMap`이 가장 익숙한 예시다.

- 잘 맞는 문제:
  - 회원 ID, 이메일, 토큰처럼 정확한 키 조회
  - 중복 체크
  - 카운팅
  - 캐시
- 주요 복잡도:
  - 조회/삽입/삭제: 평균 `O(1)`
  - 최악: 충돌이 심하면 더 느려질 수 있다
- 초보자 주의:
  - 해시 테이블은 **정렬 순서**를 보장하지 않는다
  - 범위 질의(`floor`, `ceiling`, `subMap`)는 약하다
  - 충돌 처리, resize, `equals/hashCode` 계약을 모르고 쓰면 성능과 정확도가 흔들린다

### Hash Table을 먼저 떠올릴 질문

- "이 키가 있는가?"
- "이 키의 값을 바로 찾고 싶은가?"
- "순서는 필요 없고 exact lookup만 빠르면 되는가?"

이 질문에 `yes`가 많으면 해시 테이블이 자연스럽다.
정렬된 순서나 최근 사용 순서가 필요하면 [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)로 이어서 보면 된다.

Hash Table 입문 뒤에는 다음 흐름이 자연스럽다.

- 내부 동작과 충돌 처리: [HashMap 내부 구조](./hashmap-internals.md)
- Map 선택 비교: [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)

---

## Heap (힙)

힙은 **가장 작은 값** 또는 **가장 큰 값**을 빠르게 꺼내기 위한 우선순위 구조다.
보통 완전 이진 트리를 배열로 구현하며, 루트 하나만 확실하게 우선순위를 보장한다.

- 잘 맞는 문제:
  - 우선순위 큐
  - 작업 스케줄링
  - top-k 유지
  - Dijkstra/Prim의 frontier
  - 실시간 최소값/최대값 추출
- 주요 복잡도:
  - `peek`: `O(1)`
  - 삽입/삭제(`offer/poll`): `O(log n)`
  - 전체 build: `O(n)`
- 초보자 주의:
  - 힙은 **전체가 정렬된 구조가 아니다**
  - 루트만 가장 작거나 크다는 보장이 있고, 나머지는 부분 정렬 상태다
  - 임의 원소 검색은 보통 빠르지 않다

### Min Heap vs Max Heap

| 구조 | 루트 의미 | 자주 쓰는 상황 |
|---|---|---|
| Min Heap | 가장 작은 값 | 가장 이른 작업, 최단 거리 후보, top-k 유지 |
| Max Heap | 가장 큰 값 | 최대값 유지, lower half 관리, 우선순위 역방향 문제 |

힙 입문 뒤에는 "왜 binary heap이 기본인가", "priority queue가 왜 전체 정렬과 다른가"를 [Heap Variants](./heap-variants.md)에서 이어서 보면 좋다.

---

## Tree (트리)

트리는 부모-자식 관계를 가지는 계층 구조다.
핵심은 **한 노드가 여러 자식을 가질 수 있지만, 부모는 보통 하나**라는 점이다.

- 잘 맞는 문제:
  - 파일 시스템
  - DOM
  - 카테고리 구조
  - 조직도
  - 권한 상속
- 주요 감각:
  - 루트(root)에서 시작한다
  - 리프(leaf)는 자식이 없는 노드다
  - 깊이(depth)와 높이(height)로 위치를 설명한다
- 초보자 주의:
  - 트리는 그래프의 특수한 경우다
  - 사이클이 없고 연결 구조가 계층적일 때 트리로 보는 편이 단순하다

### Tree 구현

- [List를 사용해 구현한 Tree (Typescript로 작성됨)](./code/Tree/Tree.ts)

### Tree가 자연스러운 이유

트리는 "누가 누구 아래에 있는가"를 표현할 때 가장 읽기 쉽다.
그래서 문제 설명에 `하위`, `자식`, `폴더`, `상속`, `카테고리`, `부모 메뉴`가 나오면 트리를 먼저 의심하면 된다.

더 나아가면 [Trie](./trie-prefix-search-autocomplete.md), [Fenwick Tree](./fenwick-tree.md), [Heavy-Light Decomposition](./heavy-light-decomposition.md)처럼 응용 구조로 확장된다.

---

## Binary Tree (이진 트리)

이진 트리는 각 노드가 최대 두 개의 자식을 갖는 트리다.
왼쪽/오른쪽 자식을 구분하므로, 여러 기본 자료구조와 알고리즘의 기반이 된다.

- 핵심 유형:
  - 정 이진 트리
  - 포화 이진 트리
  - 완전 이진 트리
- 잘 맞는 문제:
  - BST
  - Heap
  - Segment Tree
  - Expression Tree
- 초보자 주의:
  - "이진 트리"와 "이진 탐색 트리(BST)"는 다르다
  - 모든 이진 트리가 정렬 성질을 가지는 것은 아니다

이진 트리는 직접 포인터로 연결해도 되고, 완전 이진 트리 성질을 활용해 배열 인덱스로 관리할 수도 있다.
힙이 대표적인 배열 기반 이진 트리 예시다.

`binary tree`, `BST`, `heap`가 자꾸 섞이면 [Binary Tree vs BST vs Heap Bridge](./binary-tree-vs-bst-vs-heap-bridge.md)에서 `모양`, `정렬`, `우선순위` 축으로 먼저 분리한 뒤, heap이나 ordered tree 심화 문서로 넘어가는 편이 덜 헷갈린다.

전위/중위/후위/레벨 순회가 막히면 [Binary Tree Traversal Routing Guide](./binary-tree-traversal-routing-guide.md)에서 "현재 노드를 언제 답에 넣는가" 기준으로 다시 묶어 보는 편이 빠르다. BST의 중위 정렬, subtree 계산의 후위, BFS의 레벨 순회가 한 번에 연결된다.

---

## Graph (그래프)

그래프는 정점(vertex)과 간선(edge)으로 관계를 표현하는 구조다.
트리보다 일반적이어서 **사이클, 다대다 관계, 네트워크, 경로**를 자연스럽게 모델링한다.

- 잘 맞는 문제:
  - 길찾기와 최단 경로
  - 연결성
  - 의존성
  - 추천 관계
  - 네트워크 라우팅
- 기본 용어:
  - 정점, 간선, 차수, 경로, 사이클, 연결 성분, 가중치
- 기본 종류:
  - 방향 그래프
  - 무방향 그래프
  - 가중 그래프
  - DAG

### 그래프 표현

| 방식 | 장점 | 단점 | 언제 자연스러운가 |
|---|---|---|---|
| Edge List | 구현이 단순하다 | 이웃 정점 조회가 느리다 | 간선 정렬, Kruskal, offline 처리 |
| Adjacency Matrix | 간선 존재 확인이 빠르다 | 메모리를 많이 쓴다 | 정점 수가 작고 dense한 그래프 |
| Adjacency List | 희소 그래프에 효율적이다 | 구현이 조금 더 필요하다 | 일반적인 실전 그래프 문제 |

### 초보자 주의

- 트리는 그래프의 일부지만, 그래프는 훨씬 일반적이다
- 그래프를 선택했다면 다음 질문이 바로 따라온다
  - 경로를 구하나?
  - 연결 여부를 구하나?
  - 순서를 구하나?
  - 최소 비용으로 모두 잇나?

이 분기부터는 자료구조를 넘어 알고리즘 선택이 시작된다.
[알고리즘 기본](../algorithm/basic.md#dfs와-bfs)에서 DFS/BFS를 보고, 이어서 [그래프 관련 알고리즘](../algorithm/graph.md)에서 shortest path, MST, topological sort, flow로 이어 가면 좋다.

---

## Union-Find (유니온-파인드)

Union-Find는 서로소 집합(Disjoint Set Union, DSU)을 관리하는 구조다.
핵심은 "**두 원소가 지금 같은 그룹인가?**"와 "**이 두 그룹을 합쳐도 되는가?**"를 빠르게 처리하는 것이다.

- 대표 연산:
  - `find(x)`: x가 속한 집합의 대표를 찾기
  - `union(a, b)`: 두 집합 합치기
- 잘 맞는 문제:
  - 연결 요소 관리
  - 사이클 판별
  - Kruskal MST
  - 친구 네트워크, 그룹 병합
- 주요 복잡도:
  - path compression + union by rank/size를 쓰면 거의 `O(1)`처럼 동작한다
- 초보자 주의:
  - Union-Find는 **같은 집합인지**는 잘 알려주지만, 실제 경로나 순서는 알려주지 않는다
  - 간선 삭제가 많은 동적 그래프 문제에는 바로 맞지 않을 수 있다

### 언제 Graph가 아니라 Union-Find를 떠올리나

- "경로 자체"보다 "같은 컴포넌트인가"만 중요할 때
- 간선을 하나씩 추가하면서 사이클 여부를 즉시 판정해야 할 때
- MST에서 간선을 싼 순서로 보며 사이클만 빠르게 막고 싶을 때

즉, 그래프 전체를 풍부하게 탐색하는 구조가 아니라 **연결성 질의에 특화된 보조 자료구조**라고 보면 된다.

더 깊게는 다음 문서로 이어진다.

- 입문 이후 설명: [Union-Find Deep Dive](./union-find-deep-dive.md)
- MST 문맥 연결: [Minimum Spanning Tree: Prim vs Kruskal](../algorithm/minimum-spanning-tree-prim-vs-kruskal.md)

---

## 한 줄 정리

기본 자료 구조를 고를 때는 "데이터 모양"보다 **무엇을 가장 자주 읽고, 넣고, 빼고, 비교하는가**를 먼저 물어보는 습관이 중요하다.
