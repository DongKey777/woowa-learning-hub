---
schema_version: 3
title: Binary Tree Traversal Routing Guide
concept_id: data-structure/binary-tree-traversal-routing-guide
canonical: true
category: data-structure
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- traversal-signal-routing
- inorder-bst-only
- level-order-uses-queue
aliases:
- binary tree traversal routing guide basics
- binary tree traversal routing guide beginner
- binary tree traversal routing guide intro
- data structure basics
- beginner data structure
- 처음 배우는데 binary tree traversal routing guide
- binary tree traversal routing guide 입문
- binary tree traversal routing guide 기초
- what is binary tree traversal routing guide
- how to binary tree traversal routing guide
symptoms:
- preorder inorder postorder level-order가 이름만 비슷하게 보여서 문제를 읽을 때 바로 안 갈라진다
- BST 문제에서만 inorder가 정렬 느낌을 준다는 점을 자꾸 놓친다
- 레벨 단위 문제인데도 재귀 DFS부터 떠올라 queue 신호를 놓친다
intents:
- definition
prerequisites:
- data-structure/tree-basics
- data-structure/basic
next_docs:
- data-structure/binary-tree-vs-bst-vs-heap-bridge
- algorithm/dfs-bfs-intro
- data-structure/queue-vs-deque-vs-priority-queue-primer
linked_paths:
- contents/data-structure/basic.md
- contents/data-structure/tree-basics.md
- contents/data-structure/binary-tree-vs-bst-vs-heap-bridge.md
- contents/data-structure/queue-vs-deque-vs-priority-queue-primer.md
- contents/algorithm/dfs-bfs-intro.md
- contents/algorithm/basic.md
confusable_with:
- data-structure/tree-basics
- data-structure/binary-tree-vs-bst-vs-heap-bridge
- algorithm/dfs-bfs-intro
forbidden_neighbors:
- contents/data-structure/tree-basics.md
- contents/algorithm/dfs-bfs-intro.md
expected_queries:
- 전위 중위 후위 레벨 순회를 문제 신호로 어떻게 빠르게 고르면 돼?
- 트리 순회 문제가 나오면 현재 노드를 언제 처리해야 하는지부터 어떻게 판단해?
- BST라서 중위 순회를 떠올려야 하는 장면을 초급자 기준으로 정리해줘
- 높이 균형 subtree 계산 문제를 보면 어떤 순회가 자연스러운지 감을 잡고 싶어
- 같은 깊이끼리 보라는 문장이 나오면 왜 queue 기반 순회로 넘어가는지 설명해줘
- preorder와 postorder를 둘 다 DFS라고만 외우지 않으려면 어떤 질문으로 갈라야 해?
contextual_chunk_prefix: |
  이 문서는 트리 순회를 처음 배우는 학습자가 preorder, inorder,
  postorder, level-order를 문제 신호에 맞춰 어떻게 고르는지 기초를
  잡는 primer다. 현재 노드를 언제 처리해, BST라서 정렬 순서가 보여,
  자식 계산 후 부모를 닫아, 같은 깊이끼리 보고 싶어, queue로 레벨을
  나눠 같은 자연어 paraphrase가 본 문서의 순회 라우팅 기준에
  매핑된다.
---
# Binary Tree Traversal Routing Guide

> 한 줄 요약: `preorder`, `inorder`, `postorder`, `level-order`는 "현재 노드를 언제 처리하느냐"만 다르고, 그 타이밍이 면접 문제의 signal이 된다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: binary tree traversal routing guide basics, binary tree traversal routing guide beginner, binary tree traversal routing guide intro, data structure basics, beginner data structure, 처음 배우는데 binary tree traversal routing guide, binary tree traversal routing guide 입문, binary tree traversal routing guide 기초, what is binary tree traversal routing guide, how to binary tree traversal routing guide
> 관련 문서:
> - [기본 자료 구조](./basic.md)
> - [자료구조 정리](./README.md)
> - [Binary Tree vs BST vs Heap Bridge](./binary-tree-vs-bst-vs-heap-bridge.md)
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
> - [알고리즘 기본](../algorithm/basic.md#dfs와-bfs)
>
> retrieval-anchor-keywords: binary tree traversal, tree traversal basics, tree traversal routing guide, preorder inorder postorder level order, preorder traversal basics, inorder traversal basics, postorder traversal basics, level order traversal basics, tree dfs bfs, preorder signal, inorder signal, postorder signal, level order signal, visit timing tree, recursive tree traversal, bfs tree traversal, queue level order tree, bst inorder sorted, validate bst inorder, kth smallest bst inorder, tree serialize preorder, root to leaf preorder, subtree height postorder, delete tree postorder, minimum depth level order, zigzag level order, binary tree interview patterns, 이진 트리 순회, 트리 순회 입문, 트리 순회 라우팅, 전위 순회, 중위 순회, 후위 순회, 레벨 순회, 너비 우선 순회, BFS 트리 순회, BST 중위 순회 정렬, 전위 순회 직렬화, 후위 순회 높이 계산, 레벨 순회 큐

## 먼저 한 그림으로 잡기

예시 트리를 하나 고정해 두면 네 순회가 훨씬 덜 섞인다.

```text
        1
      /   \
     2     3
    / \     \
   4   5     6
```

| 순회 | 방문 순서 |
|---|---|
| Preorder | `1 -> 2 -> 4 -> 5 -> 3 -> 6` |
| Inorder | `4 -> 2 -> 5 -> 1 -> 3 -> 6` |
| Postorder | `4 -> 5 -> 2 -> 6 -> 3 -> 1` |
| Level-order | `1 -> 2 -> 3 -> 4 -> 5 -> 6` |

핵심은 순회 이름보다 **현재 노드가 답에 들어가는 시점**이다.

- `preorder`: 현재 노드를 자식보다 먼저 처리한다
- `inorder`: 왼쪽과 오른쪽 사이에서 처리한다
- `postorder`: 자식 둘을 본 뒤 처리한다
- `level-order`: 깊이 순서대로 처리한다

## 가장 빠른 라우팅 표

| 문제에서 보이는 signal | 먼저 떠올릴 순회 | 이유 | 자주 만나는 인터뷰 패턴 |
|---|---|---|---|
| `루트부터 기록`, `부모 결정을 먼저 내려야 함`, `직렬화`, `경로 문자열` | Preorder | 부모를 먼저 처리해야 하위 탐색이 자연스럽다 | tree serialize/deserialize, root-to-leaf path, tree copy/flatten |
| `BST`, `정렬된 순서`, `k번째 작은 값`, `이전/다음 값` | Inorder | BST에서는 `left -> root -> right`가 정렬 순서가 된다 | validate BST, kth smallest in BST, range scan |
| `자식 답을 모아 부모 계산`, `높이`, `균형`, `삭제`, `subtree 합성` | Postorder | 부모 답이 자식 결과에 의존한다 | height/depth aggregation, balanced tree, diameter, delete/free tree |
| `레벨별`, `가장 얕은`, `같은 깊이끼리`, `오른쪽에서 보이는 노드` | Level-order | 깊이 단위로 끊어 보는 질문이다 | minimum depth, level averages, right side view, zigzag traversal |

이 표만 기억해도 면접에서 "어느 순회가 자연스러운가"를 꽤 빨리 고를 수 있다.

## 1. Preorder: 루트가 먼저 뜻을 만든다

Preorder는 `root -> left -> right`다.
즉 **부모의 정보가 먼저 나와야 할 때** 가장 자연스럽다.

```text
visit(node)
traverse(node.left)
traverse(node.right)
```

이 순회가 잘 맞는 대표 상황:

- 트리를 문자열이나 배열로 직렬화할 때
- `root-to-leaf` 경로를 내려가며 상태를 쌓을 때
- 새 노드를 만들면서 원본 트리를 복사할 때
- "부모를 보자마자 현재 결정을 기록"해야 할 때

면접 signal은 보통 이런 문장으로 나온다.

- `루트를 먼저 출력하라`
- `현재 노드를 결과에 바로 넣어라`
- `경로를 내려가며 문자열을 만든다`
- `prefix` 형태로 표현한다

초보자 포인트:

- preorder는 **부모 기준 설명**에 강하다
- 하지만 BST의 정렬 순서를 보여주지는 않는다

## 2. Inorder: BST에서 정렬 순서가 드러난다

Inorder는 `left -> root -> right`다.
이 순회의 핵심 가치는 **BST에서만** 정렬 순서가 나온다는 점이다.

```text
traverse(node.left)
visit(node)
traverse(node.right)
```

이 순회가 잘 맞는 대표 상황:

- BST가 올바른지 검증할 때
- BST에서 `kth smallest`를 찾을 때
- 정렬된 결과를 뽑고 싶을 때
- predecessor / successor 감각을 설명할 때

면접 signal은 대개 이렇다.

- `BST`
- `오름차순으로 방문`
- `이전 값보다 항상 커야 한다`
- `정렬된 리스트로 바꿔라`

초보자 포인트:

- inorder가 정렬을 보장하는 건 **일반 binary tree가 아니라 BST**일 때뿐이다
- "중위 순회 = 항상 sorted"로 외우면 바로 틀린다

## 3. Postorder: 자식 답을 다 모은 뒤 부모를 계산한다

Postorder는 `left -> right -> root`다.
즉 **부모의 답이 자식들의 답에 의존할 때** 가장 자주 나온다.

```text
traverse(node.left)
traverse(node.right)
visit(node)
```

이 순회가 잘 맞는 대표 상황:

- 트리의 높이, 크기, subtree 합을 계산할 때
- balanced tree 여부를 검사할 때
- diameter처럼 자식 정보 두 개를 합쳐 부모 답을 만들 때
- 노드를 안전하게 삭제하거나 해제할 때

면접 signal은 이런 식으로 읽힌다.

- `왼쪽과 오른쪽 결과를 이용해 현재 답을 계산`
- `subtree 정보 반환`
- `리프에서부터 올라오며 판단`
- `자식을 먼저 처리하고 부모를 지운다`

초보자 포인트:

- 후위 순회는 "나중에 방문"이라기보다 **계산이 끝난 뒤 부모를 닫는 순서**에 가깝다
- tree DP 감각의 출발점이 되는 경우가 많다

## 4. Level-order: 깊이별로 본다

Level-order는 깊이 `0`, 깊이 `1`, 깊이 `2` 순으로 방문한다.
보통 구현은 `queue`를 써서 **BFS**로 한다.

```text
queue <- root
while queue not empty:
  pop front
  push children
```

이 순회가 잘 맞는 대표 상황:

- 각 레벨의 노드를 묶어 출력할 때
- 가장 얕은 리프를 찾을 때
- 오른쪽에서 보이는 노드만 모을 때
- zigzag traversal처럼 레벨 단위 후처리가 필요할 때
- 완전 이진 트리 여부를 점검할 때

면접 signal은 이런 단어로 나온다.

- `level by level`
- `같은 깊이끼리`
- `minimum depth`
- `BFS`
- `queue`

`queue` 감각이 약하면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)에서 `FIFO`부터 다시 묶어 보는 편이 좋다.

## Pre/In/Post가 헷갈릴 때 보는 한 문장

세 DFS 순회는 사실 같은 틀이다.
다른 점은 **visit(node)를 어디에 놓느냐**뿐이다.

```text
preorder:
  visit(node)
  left
  right

inorder:
  left
  visit(node)
  right

postorder:
  left
  right
  visit(node)
```

그래서 면접에서 제일 중요한 질문은 이것이다.

> "현재 노드의 값을 지금 바로 써야 하나, 왼쪽과 오른쪽을 본 뒤 써야 하나, 아니면 깊이 단위로 봐야 하나?"

이 질문으로 대부분의 tree traversal 문제가 빠르게 갈린다.

## 자주 하는 실수

1. `inorder`가 모든 binary tree를 정렬한다고 생각한다.
2. `postorder`를 단순 출력 순서로만 외우고, subtree DP signal을 놓친다.
3. `level-order`도 DFS처럼 재귀로 먼저 떠올려 queue/BFS 감각을 놓친다.
4. `preorder`와 `postorder`를 둘 다 DFS라고만 보고 "부모를 먼저 쓰는지, 나중에 쓰는지" 차이를 무시한다.

## 한 줄 정리

`preorder`는 부모 먼저, `inorder`는 BST 정렬 확인, `postorder`는 자식 결과 합성, `level-order`는 깊이별 관찰이다.
트리 문제는 "현재 노드를 언제 처리해야 답이 자연스러운가"만 먼저 물어도 라우팅이 많이 쉬워진다.
