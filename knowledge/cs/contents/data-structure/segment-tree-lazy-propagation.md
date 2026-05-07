---
schema_version: 3
title: Segment Tree Lazy Propagation
concept_id: data-structure/segment-tree-lazy-propagation
canonical: false
category: data-structure
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 84
mission_ids:
- missions/lotto
review_feedback_tags:
- segment-tree-lazy-propagation
- range-update-range-query
- lazy-tag-pushdown
aliases:
- segment tree lazy propagation
- lazy segment tree
- range update range query
- lazy tag pushdown
- 구간 갱신 세그먼트 트리
- range add range sum
- interval assignment segment tree
symptoms:
- range update를 leaf 전체에 즉시 반영하려 해 O(n log n)에 가까운 비용으로 구현한다
- lazy tag가 부모 집계값과 자식 미반영 값을 동시에 의미한다는 점을 놓쳐 query 전에 pushdown을 빠뜨린다
- range add와 range assignment를 함께 지원할 때 lazy tag 합성 순서를 정의하지 않아 덮어쓰기 버그를 만든다
intents:
- deep_dive
- design
prerequisites:
- data-structure/fenwick-vs-segment-tree
- data-structure/segment-tree-not-bst-or-heap-bridge
next_docs:
- data-structure/fenwick-segment-tree-operations-playbook
- algorithm/amortized-analysis-pitfalls
- data-structure/persistent-segment-tree
linked_paths:
- contents/data-structure/applied-data-structures-overview.md
- contents/data-structure/segment-tree-not-bst-or-heap-bridge.md
- contents/data-structure/fenwick-tree.md
- contents/data-structure/fenwick-vs-segment-tree.md
- contents/data-structure/fenwick-segment-tree-operations-playbook.md
- contents/algorithm/amortized-analysis-pitfalls.md
confusable_with:
- data-structure/fenwick-tree
- data-structure/fenwick-vs-segment-tree
- data-structure/persistent-segment-tree
- data-structure/interval-tree
forbidden_neighbors: []
expected_queries:
- segment tree lazy propagation은 range update를 어떻게 O(log n)으로 미뤄?
- lazy tag를 query 전에 pushdown하지 않으면 어떤 버그가 생겨?
- 구간 덧셈과 구간 합을 지원하는 lazy segment tree 구현 원리를 설명해줘
- range assignment와 range add를 같이 쓰면 lazy tag 합성이 왜 어려워?
- Fenwick tree로 안 되고 segment tree lazy propagation이 필요한 문제는?
contextual_chunk_prefix: |
  이 문서는 segment tree lazy propagation을 range update와 range query를 함께
  처리하기 위한 deferred pushdown 기법으로 설명한다. lazy tag, range add,
  range assignment, Fenwick tree와의 경계를 다룬다.
---
# Segment Tree Lazy Propagation

> 한 줄 요약: lazy propagation은 구간 갱신이 많은 세그먼트 트리에서 "지금 당장 다 갱신하지 말고 나중에 밀어두는" 최적화다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [자료구조 정리](./README.md)
> - [세그먼트 트리](./applied-data-structures-overview.md#세그먼트-트리-indexed-tree--segment-tree)
> - [Segment Tree Is Not BST or Heap](./segment-tree-not-bst-or-heap-bridge.md)
> - [Fenwick Tree](./fenwick-tree.md)
> - [Fenwick Tree vs Segment Tree](./fenwick-vs-segment-tree.md)
> - [Fenwick and Segment Tree Operations Playbook](./fenwick-segment-tree-operations-playbook.md)
> - [상각 분석과 복잡도 함정](../algorithm/amortized-analysis-pitfalls.md)

> retrieval-anchor-keywords: segment tree lazy propagation, range update, range query, lazy propagation, interval assignment, quota adjustment, backend range aggregation, operational segment tree, bulk range update, tree pushdown, segment tree not bst or heap, range aggregation tree, segment tree vs bst, segment tree vs heap

## 핵심 개념

세그먼트 트리는 구간 합/최솟값/최댓값 같은 질의를 빠르게 처리하는 자료구조다.  
즉 `key`를 정렬해서 찾는 `BST`도 아니고, 가장 높은 우선순위 원소를 꺼내는 `heap`도 아니라, **구간 집계값을 저장하는 binary tree**다.
lazy propagation은 여기에 **구간 갱신(update)** 을 효율적으로 추가하는 기법이다.

- 질의(query): O(log n)
- 점 갱신(point update): O(log n)
- 구간 갱신(range update): lazy 없이는 O(n log n)에 가까워질 수 있다

lazy propagation은 "아직 자식에게 반영되지 않은 변경값"을 노드에 저장해 두고, 필요할 때만 아래로 전파한다.

## 깊이 들어가기

### 1. 왜 필요한가

예를 들어 배열의 [l, r] 구간 전체에 +x를 여러 번 적용해야 한다고 하자.

매번 모든 원소를 직접 갱신하면 너무 비싸다.  
세그먼트 트리는 이 구간 갱신을 노드 단위로 묶어 처리할 수 있고, lazy는 그 갱신을 더 미룬다.

### 2. 핵심 아이디어

각 노드는 다음 두 값을 가진다.

- 현재 구간 값
- 아직 자식에게 반영하지 않은 lazy 값

질의나 추가 갱신이 자식 쪽으로 내려갈 때만 lazy를 밀어준다.

### 3. 실전 감각

lazy propagation은 구간 덧셈, 구간 할당, 구간 최솟값/최댓값 질의, 차분형 문제에 자주 나온다.

실무에서는 광고 노출 카운터, 기간별 통계, 일정 구간의 상태 플래그 갱신처럼 "전체 구간 업데이트 후 부분 조회"가 많을 때 유용한 사고방식으로 이어진다.

## 실전 시나리오

### 시나리오 1: 구간 덧셈 + 구간 합

모든 `[l, r]`에 x를 더하고, 중간중간 구간 합을 구해야 한다면 lazy propagation이 적합하다.

### 시나리오 2: 대량의 상태 플래그 반영

사용자 구간 전체에 이벤트 상태를 적용해야 하지만, 실제 하위 요소 조회는 일부만 일어날 수 있다.

이럴 때 "지금 전체를 바꾸지 말고 나중에 반영"하는 것이 훨씬 싸다.

## 코드로 보기

```java
public class LazySegmentTree {
    private final long[] tree;
    private final long[] lazy;
    private final int n;

    public LazySegmentTree(long[] arr) {
        this.n = arr.length;
        this.tree = new long[n * 4];
        this.lazy = new long[n * 4];
        build(arr, 1, 0, n - 1);
    }

    private void build(long[] arr, int node, int start, int end) {
        if (start == end) {
            tree[node] = arr[start];
            return;
        }
        int mid = (start + end) / 2;
        build(arr, node * 2, start, mid);
        build(arr, node * 2 + 1, mid + 1, end);
        tree[node] = tree[node * 2] + tree[node * 2 + 1];
    }

    private void push(int node, int start, int end) {
        if (lazy[node] == 0) return;
        tree[node] += (end - start + 1) * lazy[node];
        if (start != end) {
            lazy[node * 2] += lazy[node];
            lazy[node * 2 + 1] += lazy[node];
        }
        lazy[node] = 0;
    }

    public void rangeAdd(int left, int right, long val) {
        rangeAdd(1, 0, n - 1, left, right, val);
    }

    private void rangeAdd(int node, int start, int end, int left, int right, long val) {
        push(node, start, end);
        if (right < start || end < left) return;
        if (left <= start && end <= right) {
            lazy[node] += val;
            push(node, start, end);
            return;
        }
        int mid = (start + end) / 2;
        rangeAdd(node * 2, start, mid, left, right, val);
        rangeAdd(node * 2 + 1, mid + 1, end, left, right, val);
        tree[node] = tree[node * 2] + tree[node * 2 + 1];
    }

    public long rangeSum(int left, int right) {
        return rangeSum(1, 0, n - 1, left, right);
    }

    private long rangeSum(int node, int start, int end, int left, int right) {
        push(node, start, end);
        if (right < start || end < left) return 0;
        if (left <= start && end <= right) return tree[node];
        int mid = (start + end) / 2;
        return rangeSum(node * 2, start, mid, left, right)
             + rangeSum(node * 2 + 1, mid + 1, end, left, right);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 세그먼트 트리 + lazy | 구간 갱신과 질의를 함께 처리할 수 있다 | 구현이 복잡하다 | 구간 update/query가 모두 많을 때 |
| 펜윅 트리 | 구현이 단순하고 빠르다 | 표현 가능한 연산이 제한적이다 | 점 갱신/구간 합 중심 |
| 단순 배열 | 직관적이다 | 대량 구간 갱신에 너무 느리다 | 데이터가 작을 때 |

## 꼬리질문

> Q: lazy propagation이 왜 상각적으로 유리한가?
> 의도: "미뤄둔 작업"의 비용 분배를 이해하는지 확인
> 핵심: 모든 갱신을 즉시 하지 않고 필요한 시점에만 전파하기 때문이다.

> Q: 구간 할당과 구간 덧셈을 동시에 지원하면 왜 더 어려워지나?
> 의도: lazy tag의 우선순위와 합성 규칙 이해 여부 확인
> 핵심: 연산 간 덮어쓰기 관계를 명확히 정의해야 하기 때문이다.

## 한 줄 정리

lazy propagation은 세그먼트 트리에서 구간 갱신 비용을 미뤄서, 질의와 갱신을 모두 O(log n) 수준으로 유지하는 기법이다.
