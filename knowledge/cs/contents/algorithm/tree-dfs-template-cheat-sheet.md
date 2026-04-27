# Tree DFS Template Cheat Sheet

> 한 줄 요약: 트리 DFS 템플릿은 "현재 노드를 언제 기록하느냐"와 "스택에 무엇을 다시 넣느냐"만 정확히 고정하면 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Binary Tree Traversal Routing Guide](../data-structure/binary-tree-traversal-routing-guide.md)
- [트리 기초](../data-structure/tree-basics.md)
- [재귀 입문](./recursion-intro.md)
- [DFS와 BFS 입문](./dfs-bfs-intro.md)

retrieval-anchor-keywords: tree dfs template cheat sheet, tree traversal template, preorder iterative recursive, inorder iterative recursive, postorder iterative recursive, binary tree dfs template, preorder inorder postorder code template, tree stack simulation, recursive vs iterative traversal, 트리 dfs 템플릿, 트리 순회 템플릿, 전위 순회 구현, 중위 순회 구현, tree dfs template cheat sheet basics, tree dfs template cheat sheet beginner

## 먼저 한 문장으로 구분

- `preorder`: `root -> left -> right`
- `inorder`: `left -> root -> right`
- `postorder`: `left -> right -> root`

재귀에서는 `visit(node)` 위치만 바꾸면 된다.
반복에서는 **스택이 재귀 호출 순서를 어떻게 흉내 내는지**를 봐야 한다.

## 공통 재귀 틀

```text
dfs(node):
  if node == null:
    return

  // preorder면 여기서 visit
  dfs(node.left)
  // inorder면 여기서 visit
  dfs(node.right)
  // postorder면 여기서 visit
```

초보자가 재귀를 덜 섞으려면 "왼쪽 호출 전 / 두 호출 사이 / 오른쪽 호출 후" 세 칸만 기억하면 된다.

## 1. Preorder

### 재귀

```text
preorder(node):
  if node == null:
    return

  visit(node)
  preorder(node.left)
  preorder(node.right)
```

### 반복

```text
preorder(root):
  if root == null:
    return

  stack = [root]

  while stack not empty:
    node = stack.pop()
    visit(node)

    if node.right != null:
      stack.push(node.right)
    if node.left != null:
      stack.push(node.left)
```

### 왜 이렇게 넣나

스택은 `LIFO`라서 **오른쪽을 먼저 넣고 왼쪽을 나중에 넣어야** 왼쪽이 먼저 나온다.

### 기억 포인트

- preorder 반복은 `pop 하자마자 visit`
- `right 먼저 push, left 나중 push`

## 2. Inorder

### 재귀

```text
inorder(node):
  if node == null:
    return

  inorder(node.left)
  visit(node)
  inorder(node.right)
```

### 반복

```text
inorder(root):
  stack = []
  current = root

  while current != null or stack not empty:
    while current != null:
      stack.push(current)
      current = current.left

    current = stack.pop()
    visit(current)
    current = current.right
```

### 왜 이렇게 도나

inorder 반복은 "왼쪽 끝까지 내려간 뒤, 돌아오면서 visit"을 직접 흉내 낸다.
즉 스택에는 **아직 방문하지 않았지만 왼쪽은 더 내려가 보는 중인 조상들**이 쌓인다.

### 기억 포인트

- inorder 반복은 `left spine`을 먼저 다 넣는다
- `pop 한 뒤 visit`
- 그다음 `current = current.right`

## 3. Postorder

### 재귀

```text
postorder(node):
  if node == null:
    return

  postorder(node.left)
  postorder(node.right)
  visit(node)
```

### 반복: 방문 표시 플래그 버전

```text
postorder(root):
  if root == null:
    return

  stack = [(root, false)]

  while stack not empty:
    node, visited = stack.pop()

    if node == null:
      continue

    if visited:
      visit(node)
      continue

    stack.push((node, true))
    stack.push((node.right, false))
    stack.push((node.left, false))
```

### 왜 이 버전이 안전한가

postorder 반복은 "자식을 다 처리한 뒤 부모를 다시 꺼내야" 해서 가장 자주 헷갈린다.
`(node, visited)` 패턴은 "첫 번째로 꺼냈을 때는 자식 예약, 두 번째로 꺼냈을 때 visit"이라서 재귀 흐름과 가장 비슷하다.

### 기억 포인트

- postorder 반복은 `node`를 한 번 더 스택에 넣는다
- `visited=true`일 때만 visit
- push 순서는 `self(true) -> right -> left`여야 실제 처리 순서가 `left -> right -> self`가 된다

## 한눈에 비교

| 순회 | 재귀에서 visit 위치 | 반복에서 바로 visit 하나 | 반복 핵심 패턴 |
|---|---|---|---|
| Preorder | 왼쪽 호출 전 | O | pop 직후 visit, `right -> left` push |
| Inorder | 왼쪽/오른쪽 사이 | X | 왼쪽 끝까지 push 후 pop visit |
| Postorder | 오른쪽 호출 후 | X | 방문 표시 또는 두 스택으로 "다시 꺼내기" |

## 자주 섞이는 지점

1. preorder 반복에서 `left`를 먼저 push해서 순서가 뒤집힌다.
2. inorder 반복에서 `current = current.right`를 빼먹어 오른쪽 서브트리를 못 돈다.
3. postorder 반복을 preorder처럼 한 번만 꺼내고 visit해서 틀린다.
4. 재귀 템플릿에서 `null` 종료 조건을 빼먹는다.

## 선택 기준

- 면접에서 빨리 쓰기 쉬운 건 `preorder/inorder 재귀`
- 스택 오버플로우가 걱정되면 `iterative`
- postorder 반복은 외워서 쓰기보다 **visited 플래그 템플릿** 하나를 고정하는 편이 실수가 적다

## 한 줄 정리

트리 DFS 구현이 섞일 때는 "재귀는 visit 위치, 반복은 스택 재방문 규칙"만 분리해서 기억하면 된다.
