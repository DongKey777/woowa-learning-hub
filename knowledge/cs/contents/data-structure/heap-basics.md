# 힙 기초 (Heap Basics)

> 한 줄 요약: 힙은 최솟값 또는 최댓값을 O(1)에 꺼낼 수 있는 완전 이진 트리로, 우선순위 큐를 구현하는 가장 자연스러운 방법이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Binary Tree vs BST vs Heap Bridge](./binary-tree-vs-bst-vs-heap-bridge.md)
- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [자료구조 정리](./README.md)
- [그리디 알고리즘 입문](../algorithm/greedy-intro.md)

retrieval-anchor-keywords: heap basics, min heap max heap, 힙 입문, 힙이 뭐예요, priority queue heap, heap insert delete, heapify, 우선순위 큐 힙, 최솟값 최댓값 구조, beginner heap, heap vs bst, java priorityqueue heap

## 핵심 개념

힙은 **완전 이진 트리(Complete Binary Tree)** 형태를 가지며, 모든 노드가 **자식보다 크거나 같다(Max-Heap)** 또는 **자식보다 작거나 같다(Min-Heap)** 규칙을 만족한다.

입문자가 자주 헷갈리는 포인트는 이것이다.

- 힙은 BST(이진 탐색 트리)가 아니다. BST는 왼쪽 < 부모 < 오른쪽이지만, 힙은 부모-자식 관계만 따진다.
- 힙에서 루트는 항상 최솟값(Min-Heap) 또는 최댓값(Max-Heap)이다. 나머지 노드는 정렬되지 않는다.

핵심 강점은 **최솟값/최댓값을 O(1)에 확인**할 수 있다는 것이다.

## 한눈에 보기

```text
Min-Heap 예시:
        1
       / \
      3   2
     / \
    7   5
```

| 연산 | 시간 복잡도 |
|---|---|
| 루트(최솟값/최댓값) 조회 | O(1) |
| 삽입 | O(log n) |
| 루트 삭제 | O(log n) |
| 임의 원소 탐색 | O(n) |

## 상세 분해

힙의 두 핵심 연산을 순서대로 이해한다.

- **삽입(Insert)**: 새 원소를 트리의 가장 마지막 위치에 추가한 뒤, 부모와 비교해 규칙을 어기면 교환한다. 이 과정을 위로 올라가며 반복한다(Bubble Up / Sift Up).
- **루트 삭제(Extract)**: 루트를 꺼내고 마지막 원소를 루트 자리에 가져온다. 그 다음 두 자식 중 더 작은(또는 큰) 자식과 비교해 교환한다. 이 과정을 아래로 내려가며 반복한다(Sink Down / Sift Down).

힙은 배열로 구현하면 인덱스 계산이 간단하다.

- 부모: `(i - 1) / 2`
- 왼쪽 자식: `2 * i + 1`
- 오른쪽 자식: `2 * i + 2`

## 흔한 오해와 함정

- **오해 1: 힙은 정렬된 자료구조다.**
  힙의 루트만 최솟값/최댓값이 보장된다. 전체 원소는 정렬되지 않는다. 전체 정렬이 필요하면 Heap Sort를 써야 한다.

- **오해 2: Java의 `PriorityQueue`는 Max-Heap이다.**
  Java `PriorityQueue`는 기본적으로 **Min-Heap**이다. 최댓값을 먼저 꺼내려면 `Collections.reverseOrder()` 비교자를 사용해야 한다.

- **함정: 중간 원소를 O(log n)에 삭제할 수 없다.**
  힙은 루트 삭제만 O(log n)이다. 임의 위치의 원소를 삭제하려면 O(n) 탐색이 필요하다.

## 실무에서 쓰는 모습

**다익스트라 알고리즘** — 미방문 노드 중 최단 거리 노드를 빠르게 꺼낼 때 Min-Heap(우선순위 큐)을 사용한다. 힙이 없다면 O(V²)이지만, 힙을 쓰면 O((V + E) log V)로 줄어든다.

**Top-K 문제** — K번째로 큰 원소를 찾는 문제에서 크기 K의 Min-Heap을 유지하면 O(n log K)로 처리할 수 있다. 매번 배열을 정렬하면 O(n log n)이 된다.

## 더 깊이 가려면

- 이진 트리 / BST / 힙의 구조적 차이는 [Binary Tree vs BST vs Heap Bridge](./binary-tree-vs-bst-vs-heap-bridge.md)
- 우선순위 큐 선택 기준과 Java 함정은 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)

## 면접/시니어 질문 미리보기

1. **힙과 BST의 차이는 무엇인가요?**
   BST는 "왼쪽 < 부모 < 오른쪽" 규칙으로 전체 탐색이 O(log n)이다. 힙은 "부모가 자식보다 크거나 작다"는 규칙으로 최솟값/최댓값 접근이 O(1)이지만 임의 탐색은 O(n)이다.

2. **Java의 PriorityQueue 기본 정렬 방향은?**
   Min-Heap이다. 작은 값이 먼저 나온다. Max-Heap이 필요하면 `new PriorityQueue<>(Collections.reverseOrder())`로 선언한다.

3. **n개 원소에서 K번째로 큰 값을 효율적으로 찾으려면?**
   크기 K의 Min-Heap을 만들고 나머지 원소를 순회하며 힙 루트보다 크면 루트를 빼고 새 원소를 삽입한다. 최종 힙의 루트가 K번째로 큰 값이다. O(n log K).

## 한 줄 정리

힙은 "루트가 항상 최솟값/최댓값"이라는 규칙 하나로, 우선순위 큐·다익스트라·Top-K 문제에서 O(log n) 삽입·삭제를 제공하는 핵심 구조다.
