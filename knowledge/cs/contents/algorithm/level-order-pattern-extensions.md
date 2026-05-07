---
schema_version: 3
title: Level-Order Pattern Extensions
concept_id: algorithm/level-order-pattern-extensions
canonical: true
category: algorithm
difficulty: beginner
doc_role: playbook
level: beginner
language: ko
source_priority: 86
mission_ids: []
review_feedback_tags:
- tree-bfs-level-order
- queue-frontier-invariant
- binary-tree-traversal
aliases:
- level order pattern extensions
- tree bfs patterns
- level order traversal variants
- zigzag traversal
- right side view
- minimum depth bfs
- complete binary tree check
- queue frontier invariant
- 레벨 순회 응용
- 트리 bfs 패턴
symptoms:
- tree BFS 문제에서 큐를 쓰는 것은 알지만 levelSize가 현재 레벨 경계라는 불변식을 놓친다
- zigzag traversal에서 방문 순서와 레벨 결과 후처리를 섞어 enqueue 순서를 망가뜨린다
- minimum depth와 completeness check에서 조기 종료 조건을 리프나 null gap이 아닌 다른 신호로 판단한다
intents:
- troubleshooting
- comparison
- drill
prerequisites:
- algorithm/dfs-bfs-intro
- data-structure/tree-basics
- data-structure/queue-vs-deque-vs-priority-queue-primer
next_docs:
- data-structure/binary-tree-traversal-routing-guide
- algorithm/topological-dp
- algorithm/graph
linked_paths:
- contents/algorithm/dfs-bfs-intro.md
- contents/data-structure/tree-basics.md
- contents/data-structure/binary-tree-traversal-routing-guide.md
- contents/data-structure/queue-vs-deque-vs-priority-queue-primer.md
confusable_with:
- algorithm/dfs-bfs-intro
- data-structure/binary-tree-traversal-routing-guide
- data-structure/tree-basics
- data-structure/queue-vs-deque-vs-priority-queue-primer
forbidden_neighbors: []
expected_queries:
- level order traversal에서 levelSize를 먼저 읽는 이유가 뭐야?
- zigzag traversal은 큐 순서를 바꾸는 문제야 아니면 레벨 결과를 뒤집는 문제야?
- binary tree right side view는 레벨마다 마지막 노드를 기록하면 되는 이유가 뭐야?
- minimum depth는 왜 BFS에서 처음 만난 리프를 바로 반환해도 돼?
- complete binary tree check에서 null 뒤에 실노드가 나오면 왜 실패야?
contextual_chunk_prefix: |
  이 문서는 Level-Order Pattern Extensions playbook으로, tree BFS에서
  queue frontier와 levelSize 경계를 유지해 zigzag traversal, right side view,
  minimum depth, complete binary tree check를 같은 불변식으로 푸는 방법을 설명한다.
---
# Level-Order Pattern Extensions

> 한 줄 요약: `level-order` 문제는 새 알고리즘을 계속 외우는 게 아니라, "큐에는 지금 레벨의 경계가 들어 있다"는 불변식을 어떻게 활용하느냐로 갈린다.
>
> 문서 역할: 이 문서는 tree BFS 안에서 `zigzag traversal`, `right-side view`, `minimum depth`, `completeness check`를 하나의 레벨 경계 관점으로 묶어 주는 beginner-first pattern guide다.

**난이도: 🟢 Beginner**

관련 문서:

- [DFS와 BFS 입문](./dfs-bfs-intro.md)
- [트리 기초](../data-structure/tree-basics.md)
- [Binary Tree Traversal Routing Guide](../data-structure/binary-tree-traversal-routing-guide.md)
- [Queue vs Deque vs Priority Queue Primer](../data-structure/queue-vs-deque-vs-priority-queue-primer.md)

retrieval-anchor-keywords: level order pattern extensions, tree bfs patterns, level order invariants, queue frontier invariant, zigzag traversal, zigzag level order, right side view, binary tree right side view, minimum depth bfs, complete binary tree check bfs, completeness check queue, level size boundary, tree level batching, level order pattern extensions basics, level order pattern extensions beginner

---

## 먼저 잡아야 할 불변식

레벨 순회 문제는 대부분 아래 네 줄로 시작한다.

```text
queue <- root
while queue not empty:
  levelSize = queue.size()
  repeat levelSize times:
```

이때 중요한 불변식은 두 가지다.

1. `levelSize`를 읽는 순간, 그 개수만큼이 **현재 레벨 노드 전체**다.
2. 그 노드들을 처리하는 동안 새로 넣는 자식들은 **다음 레벨**이다.

초보자가 BFS 응용을 어려워하는 이유는 보통 "큐를 쓴다"까지만 기억하고,
"이번 반복이 정확히 어느 레벨을 닫는가"를 놓치기 때문이다.

이 경계만 고정되면 아래 문제들이 거의 한 가족처럼 보인다.

| 문제 | 레벨 경계에서 보는 핵심 |
|---|---|
| Zigzag traversal | 레벨 결과를 왼쪽→오른쪽으로 둘지, 뒤집을지 |
| Right-side view | 각 레벨의 마지막 노드만 뽑기 |
| Minimum depth | 처음 만난 리프가 가장 얕은 리프인지 확인 |
| Completeness check | `null` 자리가 나온 뒤 다시 실노드가 오면 깨짐 |

---

## 공통 템플릿

```text
if root == null:
  return ...

queue <- [root]

while queue not empty:
  levelSize = queue.size()

  repeat levelSize times:
    node = queue.pop_front()

    // 현재 레벨 기준 처리

    if node.left != null:
      queue.push_back(node.left)
    if node.right != null:
      queue.push_back(node.right)
```

차이는 `// 현재 레벨 기준 처리` 부분에만 생긴다.

---

## 1. Zigzag Traversal

### 문제 signal

- `홀수 레벨은 반대로`
- `left to right, then right to left`
- `지그재그`

### 핵심 생각

노드를 방문하는 순서는 그대로 `level-order`다.
바꾸는 것은 **레벨 결과를 담는 방식**이지, 큐에서 꺼내는 순서가 아니다.

그래서 보통 두 방식이 나온다.

1. 레벨 배열에 그냥 넣고, 레벨이 끝난 뒤 뒤집기
2. `deque`처럼 앞/뒤 삽입으로 바로 원하는 순서를 만들기

입문 단계에서는 1번이 더 안전하다.

```text
leftToRight = true

while queue not empty:
  levelSize = queue.size()
  level = []

  repeat levelSize times:
    node = queue.pop_front()
    level.append(node.value)
    push children

  if not leftToRight:
    reverse(level)

  answer.append(level)
  leftToRight = not leftToRight
```

### 왜 이렇게 읽어야 하나

`zigzag`는 탐색 방향 문제가 아니라 **출력 후처리 문제**에 가깝다.
큐 자체를 거꾸로 돌리려 하면 자식 enqueue 순서까지 꼬이기 쉽다.

---

## 2. Right-Side View

### 문제 signal

- `오른쪽에서 보이는 노드`
- `each depth visible node`
- `레벨마다 하나만`

### 핵심 생각

레벨 순회에서 같은 깊이 노드가 한 번에 묶이므로,
**그 레벨에서 마지막으로 꺼낸 노드**가 오른쪽 끝 노드다.

```text
while queue not empty:
  levelSize = queue.size()

  repeat i from 0 to levelSize - 1:
    node = queue.pop_front()

    if i == levelSize - 1:
      answer.append(node.value)

    push children
```

### 자주 하는 실수

- "오른쪽이 보이니까 `right`를 먼저 넣어야 하나?"라고 생각한다.
- 하지만 보통은 **기본 left/right enqueue를 유지하고 마지막 노드를 기록**하는 쪽이 덜 헷갈린다.

`right`를 먼저 넣는 방식도 가능하지만, 템플릿을 문제마다 바꾸면 실수가 늘어난다.

---

## 3. Minimum Depth

### 문제 signal

- `가장 가까운 리프`
- `minimum depth`
- `최소 이동 횟수처럼 가장 먼저 도달`

### 핵심 생각

BFS는 깊이 1, 깊이 2, 깊이 3 순서로 간다.
그래서 **처음 만난 리프가 최소 깊이 리프**다.

```text
queue <- [(root, 1)]

while queue not empty:
  node, depth = queue.pop_front()

  if node.left == null and node.right == null:
    return depth

  if node.left != null:
    queue.push_back((node.left, depth + 1))
  if node.right != null:
    queue.push_back((node.right, depth + 1))
```

### 왜 DFS보다 BFS가 자연스러운가

DFS로도 최소 깊이를 구할 수는 있지만, 모든 경로를 다 비교해야 한다.
BFS는 레벨 단위라 **처음 리프를 만나는 순간 종료**할 수 있다.

### 초보자 함정

- `node.left == null || node.right == null`을 리프로 착각한다.
- 리프는 **둘 다 null**이어야 한다.

---

## 4. Completeness Check

### 문제 signal

- `complete binary tree`
- `완전 이진 트리인지`
- `중간에 빈 칸이 있으면 안 됨`

### 핵심 생각

완전 이진 트리는 레벨 순서로 볼 때,
어느 순간 `null` 자리를 한 번 만난 뒤에는 **뒤에 실노드가 나오면 안 된다**.

즉 배열로 펼쳤다고 생각하면 `값 값 값 null null ...`은 가능하지만
`값 null 값`은 불가능하다.

```text
queue <- [root]
seenGap = false

while queue not empty:
  node = queue.pop_front()

  if node == null:
    seenGap = true
    continue

  if seenGap:
    return false

  queue.push_back(node.left)
  queue.push_back(node.right)

return true
```

### 왜 이 불변식이 먹히나

레벨 순회는 트리를 **배열 인덱스 순서에 가깝게** 읽는다.
그래서 중간 빈칸 뒤에 실제 노드가 다시 나오면 "왼쪽부터 차곡차곡 채운다"는 완전 이진 트리 정의를 깨뜨린다.

### 초보자 포인트

- 이 문제는 "높이가 비슷한가?"를 보는 게 아니다.
- 핵심은 **레벨 순서에서 빈칸 이후 실노드 재등장 여부**다.

---

## 네 문제를 한 번에 묶는 비교표

| 패턴 | 공통 BFS 골격 | 레벨 경계에서 바뀌는 점 | 조기 종료 가능? |
|---|---|---|---|
| Zigzag traversal | `levelSize`만큼 pop | 레벨 결과를 뒤집거나 반대로 담기 | X |
| Right-side view | `levelSize`만큼 pop | 각 레벨 마지막 노드 기록 | X |
| Minimum depth | 일반 BFS | 첫 리프를 만나면 반환 | O |
| Completeness check | 일반 BFS + `null`도 큐에 넣음 | `seenGap` 뒤 실노드 나오면 실패 | O |

이 표를 보면 "새 문제"라기보다
"같은 level-order 뼈대에 레벨 규칙 하나를 붙이는 문제"라는 점이 보인다.

---

## 패턴 라우팅 질문

트리 BFS 문제가 나오면 먼저 이 네 질문을 던지면 된다.

1. 답이 `깊이별 묶음`인가?
2. 레벨마다 `첫 번째`나 `마지막` 노드만 필요하나?
3. `처음 도달한 목표`가 정답인가?
4. 레벨 순서에서 `빈칸 이후 재등장 금지` 같은 구조 규칙이 있나?

이 질문에 각각 대응하면:

- 1번이면 `zigzag`나 level grouping
- 2번이면 `right-side view`
- 3번이면 `minimum depth`
- 4번이면 `completeness check`

---

## 자주 섞이는 오해

1. `zigzag`라서 큐에서 꺼내는 순서도 바꿔야 한다고 생각한다.
2. `right-side view`에서 오른쪽 자식을 먼저 넣는 방식만 정답이라고 생각한다.
3. `minimum depth`에서 첫 번째 `null`이나 첫 번째 자식을 보고 너무 일찍 종료한다.
4. `complete tree`를 "균형 잡힌 트리"와 비슷한 말로 착각한다.

---

## 한 줄 정리

레벨 순회 확장 문제는 "현재 큐가 정확히 한 레벨의 경계를 들고 있다"는 불변식만 유지하면, `zigzag`, `right-side view`, `minimum depth`, `completeness check`를 거의 같은 템플릿으로 풀 수 있다.
