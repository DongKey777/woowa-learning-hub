# 기본 자료 구조

> 작성자 : [서그림](https://github.com/Seogeurim)

> 한 줄 요약: 기본 자료 구조는 배열, 리스트, 스택, 큐, 트리, 그래프 같은 핵심 형태를 이해해 더 큰 알고리즘과 시스템 설계를 읽는 출발점이다.

**난이도: 🟡 Intermediate**

> retrieval-anchor-keywords: array, linked list, stack, queue, tree, binary tree, graph, random access, sequential access, adjacency list, traversal, backend data structure, tradeoff

<details>
<summary>Table of Contents</summary>

- [Array (배열)](#array-배열)
- [Linked List (연결 리스트)](#linked-list-연결-리스트)
- [Stack (스택)](#stack-스택)
- [Queue (큐)](#queue-큐)
- [Tree (트리)](#tree-트리)
- [Binary Tree (이진 트리)](#binary-tree-이진-트리)
- [Graph (그래프)](#graph-그래프)

</details>

---

자료구조(Data Structure)는 **데이터를 어떻게 저장하고, 어떻게 찾고, 어떻게 바꿀 것인가**를 다루는 방법이다.  
실무에서는 "저장 형식"보다 "어떤 연산을 빠르게 만들고 싶은가"가 더 중요하다.

- 조회가 많으면 `Array`, `HashMap`, `TreeMap` 계열이 유리하다.
- 삽입/삭제가 잦으면 `Linked List`, `Deque`, `Queue` 계열이 유리하다.
- 계층/의존성이 있으면 `Tree`, `Graph` 계열이 필요하다.

이 문서는 각 구조의 기본 감각을 잡아두고, 이후의 고급 문서들 - 예를 들면 [Fenwick Tree](./fenwick-tree.md), [Skip List](./skip-list.md), [Trie](./trie-prefix-search-autocomplete.md), [Heap Variants](./heap-variants.md) - 로 자연스럽게 이어지도록 만든다.

---

## Array (배열)

배열은 같은 타입의 데이터를 연속된 메모리 공간에 저장한다.  
가장 단순하지만, 많은 구조의 기준점이 된다.

- 장점: 인덱스로 즉시 접근할 수 있다.
- 단점: 중간 삽입/삭제가 비싸다.
- 실무 감각: 읽기 중심 캐시, 고정 길이 버퍼, 정적 테이블에 좋다.

### Array 구현

```java
int[] values = new int[5];
values[0] = 10;
values[1] = 20;
values[2] = 30;
```

### Array 시간 복잡도 & 공간 복잡도

- 조회: O(1)
- 마지막 삽입: 동적 배열이면 amortized O(1)
- 중간 삽입/삭제: O(n)

### 실전 시나리오

- 최근 N개 로그를 담는 고정 버퍼
- 점수 테이블, 좌표, ID 매핑
- 정적 구간 질의를 위한 전처리 결과 저장

### 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Array | 빠른 random access | 중간 변경이 느리다 | 읽기 위주, 고정 길이 |
| Linked List | 삽입/삭제가 편하다 | 탐색이 느리다 | 빈번한 구조 변경 |

---

## Linked List (연결 리스트)

연결 리스트는 각 노드가 다음 노드의 주소를 가진다.  
배열보다 메모리 접근은 느릴 수 있지만, 위치만 알면 끼워 넣고 빼기가 쉽다.

- 장점: 삽입/삭제가 유연하다.
- 단점: 임의 접근이 느리다.
- backend 감각: 큐/스택의 내부 구현, 이중 연결 구조, LRU 같은 정책 자료구조에 자주 등장한다.

### Linked List 구현

- [Singly Linked List](./code/LinkedList/SinglyLinkedList.java)
- [Doubly Linked List](./code/LinkedList/DoublyLinkedList.java)
- 위 코드 실행 : [LinkedListExample.java](./code/LinkedList/LinkedListExample.java)

### Linked List 시간 복잡도

- 조회: O(n)
- 맨 앞/뒤 삽입/삭제: O(1)
- 중간 삽입/삭제: 찾는 비용 포함 O(n)

### 실전 시나리오

- LRU 캐시의 연결 순서 유지
- 이벤트 노드 연결
- undo/redo 히스토리 관리

### 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Singly Linked List | 구현이 단순하다 | 역방향 이동이 어렵다 | forward-only 흐름 |
| Doubly Linked List | 양방향 이동이 쉽다 | 포인터가 더 필요하다 | 캐시/순서 관리 |
| Array | 메모리 연속성이 좋다 | 중간 삽입이 비싸다 | 조회 중심 |

---

## Stack (스택)

스택은 마지막에 들어간 것이 먼저 나오는 LIFO 구조다.  
함수 호출 스택, DFS, 괄호 검사처럼 "되돌아가기"가 있는 흐름에 잘 맞는다.

### Stack 용어

- `Top`: 현재 마지막 요소

### Stack 주요 연산

- `push`
- `pop`
- `peek`

### Stack 구현

- [Array를 통해 구현한 Stack](./code/Stack/ArrayStack.java)
- [Singly Linked List를 통해 구현한 Stack](./code/Stack/LinkedStack.java)
- 위 코드 실행 : [StackExample.java](./code/Stack/StackExample.java)

### Stack 시간 복잡도 & 공간 복잡도

- 삽입/삭제: O(1)
- top 조회: O(1)
- 임의 조회: O(n)

### Stack 활용

- 함수 호출/복귀
- 실행 취소
- 괄호 검사
- DFS
- 수식 변환

### backend angle

스택은 단순하지만, 예외 처리나 롤백 로직을 읽을 때 자주 숨어 있다.  
예를 들어 parser, middleware chain, 트랜잭션 추적에서 "마지막 작업을 먼저 되돌린다"는 흐름이 여기에 가깝다.

---

## Queue (큐)

큐는 먼저 들어간 것이 먼저 나오는 FIFO 구조다.  
순서 보장과 작업 대기열에 강하다.

### Queue 용어

- `Front` / `Head`
- `Rear` / `Tail`

### Queue 주요 연산

- `enQueue`
- `deQueue`

### Queue 구현

- [Array를 통해 구현한 Queue](./code/Queue/ArrayQueue.java)
- [Singly Linked List를 통해 구현한 Queue](./code/Queue/LinkedQueue.java)
- 위 코드 실행 : [QueueExample.java](./code/Queue/QueueExample.java)

> Java에서 `Queue` 인터페이스는 `LinkedList`, `ArrayDeque`, `PriorityQueue` 같은 구현체와 함께 쓸 수 있다.  
> 순서가 중요한지, 우선순위가 중요한지 먼저 분리해서 보자.

### Queue 시간 복잡도 & 공간 복잡도

- 삽입/삭제: O(1)
- front 조회: O(1)
- 임의 조회: O(n)

### Queue 활용

- 작업 큐
- 이벤트 루프
- 네트워크 패킷 버퍼
- BFS

### backend angle

큐는 요청 수신과 처리 사이의 완충재다.  
스파이크를 흡수하거나, rate limiter와 결합하거나, 백그라운드 작업 분배에 쓰인다.

---

## Tree (트리)

트리는 부모-자식 관계를 표현하는 비선형 자료구조다.  
계층 구조를 표현하고 싶을 때 가장 먼저 떠올려야 한다.

- 장점: 계층 표현이 자연스럽다.
- 단점: 경로/균형/회전 같은 관리가 필요할 수 있다.

### Tree 용어

- 루트, 부모, 자식, 형제, 조상, 후손, 리프, 깊이, 높이

### Tree 구현

- [List를 사용해 구현한 Tree (Typescript로 작성됨)](./code/Tree/Tree.ts)

### Tree 시간 복잡도 & 공간 복잡도

- 삽입: 구조에 따라 다름
- 삭제: 구조에 따라 다름
- 검색: 보통 O(N)

### Tree 활용

- 파일 시스템
- DOM
- 조직도
- 카테고리 트리
- [Trie](./trie-prefix-search-autocomplete.md), [Binary Tree](#binary-tree-이진-트리), [Heavy-Light Decomposition](./heavy-light-decomposition.md)

### backend angle

트리는 읽기보다 "구조화된 관계"를 표현하는 데 강하다.  
권한 상속, 메뉴 구조, 카탈로그, 폴더 경로 같은 문제를 보면 자연스럽게 트리를 떠올리자.

---

## Binary Tree (이진 트리)

이진 트리는 자식이 최대 두 개인 트리다.  
BST, heap, expression tree, decision tree 같은 핵심 구조의 바탕이 된다.

- 왼쪽/오른쪽 자식을 구분한다.
- 균형 여부가 성능에 큰 영향을 준다.

### Binary Tree의 종류

- 정 이진 트리
- 포화 이진 트리
- 완전 이진 트리

### Binary Tree 구현

이진 트리는 직접 노드를 만들어도 되고, 배열 기반 heap처럼 인덱스로 관리해도 된다.

### Binary Tree 시간 복잡도 & 공간 복잡도

- 조회: 구조에 따라 다름
- 삽입/삭제: 구조에 따라 다름

### Binary Tree 활용

- BST
- Heap
- Segment Tree
- Trie의 일부 응용

### backend angle

균형 이진 트리는 순서 유지와 빠른 조회 사이의 절충안이다.  
`TreeMap`, `Order Statistic Tree`, `Treap` 같은 구조를 이해하려면 이진 트리 감각이 필요하다.

---

## Graph (그래프)

그래프는 정점과 간선으로 관계를 표현한다.  
의존성, 네트워크, 추천, 최단 경로, 연결성 문제의 기반이다.

## 그래프 정의

정점(vertex)과 간선(edge)으로 구성된 구조이며, 방향 유무와 가중치 유무에 따라 다양한 문제를 표현한다.

## 그래프 용어

- 정점, 간선, 차수, 경로, 사이클, 연결 성분, 인접, 가중치

## 그래프 종류

- 방향 그래프
- 무방향 그래프
- 가중 그래프
- DAG

## 그래프 표현

### 간선 리스트 (Edge List)

간선을 그대로 저장한다.  
크루스칼, offline 처리에 잘 맞는다.

### 인접 행렬 (Adjacency Matrix)

정점 수가 작고 밀도가 높을 때 단순하다.  
정점 수가 크면 메모리 낭비가 심하다.

### 인접 리스트 (Adjacent List)

희소 그래프에서 가장 흔하다.  
실전에서는 이 표현이 기본이다.

### 그래프 표현 방식 비교

| 방식 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Edge List | 구현이 단순하다 | 이웃 조회가 느리다 | 정렬/간선 중심 |
| Matrix | 접근이 빠르다 | 메모리가 많이 든다 | 작은 dense graph |
| List | 희소 그래프에 좋다 | 추가 구조가 필요할 수 있다 | 일반적인 실전 |

### backend angle

서비스 의존성, 네트워크 라우팅, 작업 스케줄링, 권한 전파를 그래프로 보면 뒤의 고급 알고리즘들 - [Dijkstra](../algorithm/dijkstra-bellman-ford-floyd-warshall.md), [SCC](../algorithm/scc-tarjan-kosaraju.md), [Topological DP](../algorithm/topological-dp.md), [Bridges and Articulation Points](../algorithm/bridges-and-articulation-points.md) - 가 자연스럽게 연결된다.

---

## 한 줄 정리

기본 자료 구조는 "어떤 연산을 빠르게 만들고 싶은가"를 결정하는 가장 중요한 출발점이다.
