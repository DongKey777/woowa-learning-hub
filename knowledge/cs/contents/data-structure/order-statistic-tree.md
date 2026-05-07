---
schema_version: 3
title: Order Statistic Tree
concept_id: data-structure/order-statistic-tree
canonical: false
category: data-structure
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 83
mission_ids: []
review_feedback_tags:
- order-statistic-tree
- rank-query
- kth-element-balanced-tree
aliases:
- Order Statistic Tree
- rank query
- kth element tree
- subtree size balanced BST
- select by rank
- indexed tree
- median maintenance
symptoms:
- 정렬된 set은 유지하지만 k번째 원소나 특정 key의 rank를 빠르게 물어야 하는 요구를 일반 BST로만 처리하려 한다
- subtree size를 유지하면 왼쪽 subtree count로 select/rank를 계산할 수 있다는 핵심을 놓친다
- rank가 필요 없고 floor/ceiling만 필요한 ordered map 문제에도 order statistic tree를 과하게 적용한다
intents:
- definition
- deep_dive
prerequisites:
- data-structure/balanced-bst-vs-unbalanced-bst
next_docs:
- data-structure/treap-vs-skip-list
- data-structure/skip-list
- algorithm/binary-search-patterns
linked_paths:
- contents/data-structure/treap-vs-skip-list.md
- contents/data-structure/skip-list.md
- contents/algorithm/binary-search-patterns.md
confusable_with:
- data-structure/treap-vs-skip-list
- data-structure/skip-list
- data-structure/fenwick-tree
- data-structure/treemap-vs-hashmap-vs-linkedhashmap
forbidden_neighbors: []
expected_queries:
- Order Statistic Tree는 k번째 원소와 rank query를 어떻게 빠르게 처리해?
- balanced BST에 subtree size를 붙이면 select by rank가 가능한 이유는?
- 실시간 ranking이나 median maintenance에서 Order Statistic Tree가 맞는 경우는?
- rank가 필요 없으면 TreeMap이나 Skip List로 충분한 이유는?
- kth element query와 range count를 ordered set에서 처리하는 구조를 알려줘
contextual_chunk_prefix: |
  이 문서는 balanced BST에 subtree size를 유지해 kth element, rank query,
  range count, median maintenance를 처리하는 Order Statistic Tree primer다.
  Treap, Red-Black Tree, AVL, Skip List와 기능적 차이를 설명한다.
---
# Order Statistic Tree

> 한 줄 요약: Order Statistic Tree는 정렬된 집합에서 k번째 원소와 rank를 빠르게 찾도록 subtree size를 유지하는 균형 트리다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Treap vs Skip List](./treap-vs-skip-list.md)
> - [Skip List](./skip-list.md)
> - [Binary Search Patterns](../algorithm/binary-search-patterns.md)

> retrieval-anchor-keywords: order statistic tree, rank query, kth element, subtree size, balanced BST, indexed tree, select by rank, ordered set, median maintenance, rank-based query

## 핵심 개념

Order Statistic Tree는 BST에 subtree size를 붙여서 다음 질의를 빠르게 한다.

- k번째로 작은 원소 찾기
- 어떤 원소의 순위(rank) 찾기
- 범위 내 몇 개가 있는지 세기

핵심은 각 노드에 "내 서브트리에는 원소가 몇 개나 있는가"를 저장하는 것이다.

## 깊이 들어가기

### 1. 왜 size가 필요한가

단순 BST는 정렬은 되지만 rank 정보가 없다.

size를 유지하면 왼쪽 서브트리 개수를 보고 바로 순위를 계산할 수 있다.

### 2. 어떤 균형 구조와도 결합 가능

Order statistic은 구조가 아니라 기능이다.

- Treap
- Red-black tree
- AVL tree

균형 BST에 size를 붙이면 된다.

### 3. backend에서 유용한 이유

정렬된 값 집합에서 순위 질의가 자주 나오는 시스템에 잘 맞는다.

- leader board
- percentile 근사
- median 유지
- 실시간 랭킹

### 4. 트레이드오프

size를 유지하려면 insert/delete 때마다 갱신해야 한다.
그래서 단순 set보다 구현이 복잡해진다.

## 실전 시나리오

### 시나리오 1: k번째 점수

실시간 랭킹에서 k번째 사용자를 찾는 데 유용하다.

### 시나리오 2: rank query

특정 사용자가 전체 중 몇 등인지 빠르게 보고 싶을 때 좋다.

### 시나리오 3: 오판

정렬만 필요하고 rank가 필요 없다면 과한 구조일 수 있다.

## 코드로 보기

```java
public class OrderStatisticNotes {
    static final class Node {
        int key;
        int size = 1;
        Node left, right;
        Node(int key) { this.key = key; }
    }

    public int kth(Node root, int k) {
        int leftSize = root.left == null ? 0 : root.left.size;
        if (k == leftSize + 1) return root.key;
        if (k <= leftSize) return kth(root.left, k);
        return kth(root.right, k - leftSize - 1);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Order Statistic Tree | rank/kth 질의가 빠르다 | size 유지가 필요하다 | 순위 기반 질의 |
| Sorted Array | 탐색이 쉽다 | 삽입/삭제가 비싸다 | 읽기 위주 |
| Heap | top/min/max에 강하다 | rank가 약하다 | 극값 유지 |

## 꼬리질문

> Q: 왜 subtree size가 핵심인가?
> 의도: rank 계산 원리를 아는지 확인
> 핵심: 왼쪽 서브트리 크기로 현재 노드의 순위를 알 수 있다.

> Q: 어떤 균형 트리와 결합 가능한가?
> 의도: 기능과 구조를 구분하는지 확인
> 핵심: 균형 BST라면 대부분 가능하다.

> Q: kth와 rank는 어떻게 다른가?
> 의도: 양방향 질의 이해 확인
> 핵심: 하나는 순위로 값 찾기, 다른 하나는 값으로 순위 찾기다.

## 한 줄 정리

Order Statistic Tree는 균형 BST에 subtree size를 붙여 k번째 원소와 rank를 빠르게 구하는 구조다.
