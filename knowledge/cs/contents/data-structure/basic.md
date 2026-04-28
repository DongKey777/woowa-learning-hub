# 기본 자료 구조

> 한 줄 요약: 배열, 연결 리스트, 스택, 큐, 해시 테이블, 힙, 트리, 그래프, 유니온-파인드는 "무슨 연산을 자주 빠르게 하고 싶은가"를 기준으로 고르는 기본 도구다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 정리](./README.md)
- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)

retrieval-anchor-keywords: data structure basics, beginner data structure, what data structure to choose, 자료구조 처음 배우는데, array linked list stack queue basics, hash table heap tree graph basics, union find basics, map set beginner choice, beginner cs primer, 자료구조 기초, 어떤 자료구조 써야 하나, basics intro

## 핵심 개념

자료구조는 "데이터를 어디에 놓을까"보다 "어떤 연산을 빠르게 만들까"에 더 가깝다.
초보자가 제일 많이 헷갈리는 이유는 이름을 외우려 하기 때문이다. 안전한 시작점은 이름이 아니라 질문이다.

- `index`로 바로 읽고 싶은가
- 맨 앞이나 맨 뒤에서 자주 넣고 빼는가
- `key -> value`를 빠르게 찾고 싶은가
- 최소값/최대값을 반복해서 꺼내는가
- 부모-자식 관계나 연결 관계를 표현하는가
- `같은 그룹인가?`만 빠르게 반복해서 묻는가

즉 자료구조 선택은 "정답 하나"를 찾는 일이 아니라 "내 연산 패턴에 맞는 기본값"을 고르는 일이다.

## 한눈에 보기

| 구조 | 먼저 떠올릴 질문 | 강한 연산 | 약한 연산 |
|---|---|---|---|
| 배열 | `n번째 값을 바로 읽어야 하나?` | 임의 접근 | 중간 삽입/삭제 |
| 연결 리스트 | `위치를 알고 있는 노드 주변을 자주 바꾸나?` | 삽입/삭제 | 임의 접근 |
| 스택 | `가장 최근 작업부터 꺼내나?` | `push/pop` | 중간 원소 탐색 |
| 큐 | `먼저 온 작업부터 처리하나?` | `enqueue/dequeue` | 우선순위 처리 |
| 해시 테이블 | `key로 바로 찾나?` | 평균 조회/삽입 | 정렬/범위 조회 |
| 힙 | `최소값/최대값 하나를 계속 꺼내나?` | `peek/poll` | 임의 탐색 |
| 트리 | `계층 구조를 표현하나?` | 부모-자식 탐색 | 일반 그래프 표현 |
| 그래프 | `경로/연결 관계가 복잡한가?` | BFS/DFS 기반 탐색 | 단순 구현성 |
| 유니온-파인드 | `같은 그룹인가를 반복해 묻나?` | 그룹 병합/대표 찾기 | 실제 경로 복원 |

처음에는 "무조건 빠른 구조"를 찾지 말고, "내 질문에 바로 답하는 구조"를 찾는 편이 맞다.

## Array (배열)

배열은 값이 **연속된 메모리**에 놓이는 구조다.
그래서 `index`가 있으면 곧바로 원하는 원소로 점프할 수 있다.

- 잘 맞는 상황:
  - 점수표, 좌표, 방문 배열처럼 위치가 의미인 데이터
  - 정렬 결과, DP 테이블, prefix sum 저장소
- 기억할 감각:
  - 읽기는 빠르다
  - 중간에 끼워 넣거나 빼는 일은 느리다

`ArrayList`도 이름은 리스트지만 내부는 동적 배열이다.
그래서 "인덱스로 자주 읽는다"가 핵심이면 배열 계열부터 생각하는 편이 안전하다.

더 자세한 비교는 [배열 vs 연결 리스트](./array-vs-linked-list.md)로 이어 가면 된다.

## Linked List (연결 리스트)

연결 리스트는 노드가 `next` 또는 `prev` 포인터로 이어지는 구조다.
배열처럼 붙어 있지 않으므로 `3번째 값`을 바로 읽는 데는 약하지만, 이미 잡고 있는 노드 주변을 바꾸는 데는 자연스럽다.

- 잘 맞는 상황:
  - 노드 삽입/삭제가 자주 일어나는 흐름
  - LRU처럼 순서를 자주 앞뒤로 옮기는 구조
- 주의할 점:
  - "삽입/삭제가 O(1)"은 위치를 이미 알고 있을 때 이야기다
  - 위치를 찾는 순회 비용까지 합치면 실제로는 O(n)일 수 있다

배열과의 차이는 "연속 메모리 vs 포인터 연결" 한 줄로 먼저 잡으면 된다.
실전 선택 감각은 [연결 리스트 기초](./linked-list-basics.md)와 [배열 vs 연결 리스트](./array-vs-linked-list.md)가 가장 빠르다.

## Stack (스택)

스택은 **LIFO**다. 마지막에 넣은 것이 먼저 나온다.
즉 "가장 최근 상태"가 중요하면 스택을 먼저 떠올리면 된다.

- 대표 장면:
  - 괄호 짝 맞추기
  - 되돌리기(undo)
  - 함수 호출 스택
  - DFS의 반복문 구현

초보자는 `peek`와 `pop`을 자주 섞는다.

- `peek`: 보기만 한다
- `pop`: 꺼내면서 제거한다

"최근 것부터 되돌린다"는 문장이 보이면 스택 신호다.
자세한 입문 설명은 [스택 기초](./stack-basics.md)를 보면 된다.

## Queue (큐)

큐는 **FIFO**다. 먼저 들어온 것이 먼저 나온다.
즉 순서를 지키는 대기열이 보이면 큐가 기본값이다.

- 대표 장면:
  - BFS
  - 작업 대기열
  - 메시지 처리 순서 보장
- 자주 헷갈리는 경계:
  - `Queue`: 먼저 온 순서
  - `Deque`: 앞뒤 양쪽에서 넣고 뺌
  - `Priority Queue`: 먼저 온 순서가 아니라 우선순위가 높은 것을 먼저 꺼냄

배열 기반 큐는 앞칸 낭비를 막으려고 원형 큐로 구현하는 경우가 많다.
즉 "FIFO 규칙"과 "배열로 어떻게 구현하나"는 다른 질문이다.

입문 단계에서는 [큐 기초](./queue-basics.md)로 FIFO를 먼저 잡고, 그다음 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)로 분기하면 덜 헷갈린다.

## Hash Table (해시 테이블)

해시 테이블은 `key`를 해시 함수로 버킷 위치에 바꿔 저장하는 구조다.
핵심은 "정렬"이 아니라 "빠른 조회"다.

- 대표 장면:
  - `id -> 객체` 조회
  - 중복 체크
  - 방문 여부 기록
- 꼭 기억할 오해 방지:
  - 평균적으로 빠르지, 항상 O(1)은 아니다
  - 충돌이 많아지면 성능이 떨어진다

초급자 관점에서는 `Map`과 `Set`도 같이 보면 좋다.

- `Map`: `key -> value`를 저장
- `Set`: 값의 존재 여부, 중복 제거가 핵심

빠른 membership이 먼저면 해시 계열이 출발점이다.
기본 감각은 [해시 테이블 기초](./hash-table-basics.md), set 선택은 [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md)로 이어서 보면 된다.

## Heap (힙)

힙은 "전체가 정렬된 구조"가 아니라 "루트 하나가 강한 구조"다.
최솟값 또는 최댓값을 반복해서 꺼내야 할 때 가장 자연스럽다.

- 대표 장면:
  - 우선순위 큐
  - Top-K
  - 다익스트라
- 꼭 구분할 것:
  - 힙은 정렬된 배열이 아니다
  - 루트만 최소/최대가 보장된다

즉 질문이 `가장 작은 값 하나`, `가장 큰 값 하나`를 계속 꺼내는 쪽이면 힙이 잘 맞고,
`범위`, `floor`, `ceiling`처럼 정렬된 전체 관계가 중요하면 트리 계열이 더 맞을 수 있다.

기본 동작은 [힙 기초](./heap-basics.md), 경계 비교는 [Heap vs Priority Queue vs Ordered Map Beginner Bridge](./heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)에서 정리할 수 있다.

## Tree (트리)

트리는 **계층 구조**를 표현하는 비선형 자료구조다.
루트에서 자식으로 내려가며 관계를 읽는 구조라고 생각하면 된다.

- 대표 장면:
  - 파일 시스템
  - HTML DOM
  - 조직도
- 먼저 잡을 용어:
  - 루트
  - 부모/자식
  - 리프
  - 깊이/높이

초보자는 트리, BST, 힙을 한 덩어리로 외우다가 섞이는 경우가 많다.

- 일반 트리: 계층 관계 자체가 핵심
- BST: 정렬 규칙으로 탐색을 빠르게 함
- 힙: 루트 최소/최대만 강하게 보장

큰 그림은 [트리 기초](./tree-basics.md), 세 구조의 분리는 [Binary Tree vs BST vs Heap Bridge](./binary-tree-vs-bst-vs-heap-bridge.md)가 잘 맞는다.

## Graph (그래프)

그래프는 정점과 간선으로 관계를 표현한다.
트리가 "부모-자식 계층"이라면 그래프는 "복잡한 연결망" 쪽에 더 가깝다.

- 대표 장면:
  - 친구 관계
  - 지도 경로
  - 네트워크 연결
- 먼저 갈라야 할 질문:
  - 연결만 확인하는가
  - 실제 경로 하나가 필요한가
  - 최단 경로가 필요한가

그래프에서는 BFS와 DFS가 기본 도구다.
특히 무가중치 최단 경로는 BFS, 연결 여부나 순회는 DFS/BFS 둘 다 가능하다는 감각을 먼저 잡으면 좋다.

입문 설명은 [그래프 기초](./graph-basics.md), 탐색 감각은 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)으로 이어 가면 된다.

## Union-Find (유니온-파인드)

유니온-파인드는 그래프 전체를 다 그리지 않고도 "`a`와 `b`가 같은 그룹인가?"를 빠르게 반복해서 답하는 구조다.
이름보다 역할을 먼저 기억하는 편이 쉽다.

- 잘 맞는 질문:
  - 같은 팀인가
  - 연결 요소가 몇 개인가
  - 두 그룹을 합치면 어떻게 되나
- 잘 안 맞는 질문:
  - 실제 경로를 보여 달라
  - 방문 순서를 알려 달라

즉 유니온-파인드는 **연결 여부/그룹 병합**에 강하고, **경로 복원**에는 약하다.
그래서 "연결만 확인"이면 유니온-파인드, "어떻게 가는지"가 중요하면 BFS/DFS로 가는 분기가 중요하다.

첫 진입은 [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md)로 `same component yes/no` 감각부터 잡고, 그다음 [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md)로 `size/count`를 익히면 된다. 전체 경계는 [Connectivity Question Router](./connectivity-question-router.md)에서 정리한다.

## Map / Set 선택 감각

초급자가 해시 테이블을 배운 뒤 가장 자주 묻는 질문은 "그래서 `Map`이랑 `Set`은 언제 쓰나요?"다.
안전한 첫 분기는 아래처럼 잡으면 된다.

| 지금 필요한 것 | 먼저 떠올릴 구조 |
|---|---|
| `key -> value` 저장 | `Map` |
| 중복 제거, 존재 여부 체크 | `Set` |
| 빠른 조회가 우선 | `HashMap`, `HashSet` |
| 정렬된 순서, 범위, 주변 값 | `TreeMap`, `TreeSet` |

한 줄로 줄이면 이렇다.

- `hash`: 빠른 조회
- `tree`: 정렬과 범위

그래서 "중복만 막아도 되나, 정렬된 상태로 다뤄야 하나"가 set 선택의 핵심이고,
"빠른 단건 조회인가, `floor/ceiling` 같은 ordered query인가"가 map 선택의 핵심이다.

여기서 더 내려가려면 [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md)와 [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)를 이어서 보면 된다.

## 흔한 오해와 첫 분기

- 배열이 항상 제일 빠른 구조는 아니다. 읽기에는 강하지만 중간 변경에는 약하다.
- 연결 리스트가 항상 삽입에 유리한 것도 아니다. 위치를 찾는 순회 비용을 같이 봐야 한다.
- 힙은 정렬 구조가 아니다. 최소/최대 하나를 빨리 꺼내는 구조다.
- 그래프 연결성 문제라고 해서 항상 유니온-파인드가 답은 아니다. 경로가 필요하면 BFS/DFS로 가야 한다.
- 해시 테이블이 빠르다고 해서 ordered query까지 잘하는 것은 아니다. 범위와 인접 값은 트리 계열이 더 자연스럽다.

입문 단계에서는 "이름 외우기"보다 아래 순서로 고르면 실수가 줄어든다.

1. 내가 자주 하는 연산을 한 줄로 쓴다.
2. 그 연산이 `읽기`, `삽입/삭제`, `조회`, `최소/최대`, `계층`, `연결성` 중 어디에 가까운지 본다.
3. 그 축에 맞는 기본 구조를 고른다.
4. 그다음 구현체와 언어 API 차이를 본다.

## 한 줄 정리

자료구조 입문은 이름을 많이 외우는 일이 아니라, "내 질문이 읽기인지, 조회인지, 최소값 추출인지, 연결성 판단인지"를 먼저 구분하고 그에 맞는 기본 구조를 고르는 일이다.
