---
schema_version: 3
title: DSU Rollback
concept_id: algorithm/dsu-rollback
canonical: true
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- dsu-rollback
- offline-dynamic-connectivity
- union-find-undo
aliases:
- dsu rollback
- rollback union find
- union find undo
- offline dynamic connectivity
- connected components with deletions
- edge deletion connectivity
- reversible dsu
- 유니온 파인드 롤백
- 되돌리기 유니온 파인드
symptoms:
- 간선 삭제가 섞인 동적 연결성 문제를 일반 Union-Find로만 풀려고 한다
- rollback을 쉽게 하려면 path compression을 제한하고 parent/size 변경을 기록해야 한다는 점을 놓친다
- 완전 online dynamic graph와 offline interval 처리 가능한 dynamic connectivity를 구분하지 못한다
intents:
- deep_dive
- comparison
- design
prerequisites:
- data-structure/union-find-deep-dive
- algorithm/union-find-amortized-proof-intuition
next_docs:
- data-structure/deletion-aware-connectivity-bridge
- algorithm/mo-algorithm-basics
- algorithm/segment-tree-offline-dynamic-connectivity
linked_paths:
- contents/algorithm/union-find-amortized-proof-intuition.md
- contents/data-structure/union-find-deep-dive.md
- contents/data-structure/deletion-aware-connectivity-bridge.md
- contents/algorithm/mo-algorithm-basics.md
confusable_with:
- data-structure/union-find-deep-dive
- data-structure/deletion-aware-connectivity-bridge
- algorithm/mo-algorithm-basics
- algorithm/union-find-amortized-proof-intuition
forbidden_neighbors: []
expected_queries:
- DSU Rollback은 union-find 변경을 기록했다가 어떻게 되돌려?
- 간선 삭제가 있는 dynamic connectivity를 offline으로 풀 때 rollback DSU가 왜 필요해?
- path compression을 쓰면 rollback이 어려워지는 이유가 뭐야?
- parent와 size 변경 로그를 stack에 저장해 snapshot으로 돌아가는 흐름을 설명해줘
- 일반 Union-Find와 DSU rollback은 edge deletion 처리에서 어떻게 달라?
contextual_chunk_prefix: |
  이 문서는 DSU Rollback advanced deep dive로, Union-Find의 parent/size 변경을
  stack에 기록해 rollback 가능한 DSU를 만들고 offline dynamic connectivity,
  edge deletion, temporal query를 처리하는 기법을 설명한다.
---
# DSU Rollback

> 한 줄 요약: DSU Rollback은 Union-Find의 변경을 기록해 되돌릴 수 있게 만들어 오프라인 동적 연결성 문제에 쓰는 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Union-Find Amortized Proof Intuition](./union-find-amortized-proof-intuition.md)
> - [Union-Find Deep Dive](../data-structure/union-find-deep-dive.md)
> - [Deletion-Aware Connectivity Bridge](../data-structure/deletion-aware-connectivity-bridge.md)
> - [Mo's Algorithm Basics](./mo-algorithm-basics.md)

> retrieval-anchor-keywords: dsu rollback, rollback union find, rollback union-find, union-find undo, unionfind rollback, dsu with rollback, offline dynamic connectivity, undo union, stack changes, temporal queries, graph connectivity, connected components with deletions, connectivity after edge deletion, backtracking union, reversible dsu, 유니온 파인드 롤백, 유니온파인드 롤백, 되돌리기 유니온 파인드, 간선 삭제 연결성 dsu

## 핵심 개념

DSU Rollback은 union 연산의 변경을 스택에 저장해 두고,
필요할 때 이전 상태로 되돌린다.

이 방식은 삭제가 섞인 연결성 문제를 오프라인으로 풀 때 유용하다.

## 깊이 들어가기

### 1. 왜 일반 DSU로 안 되나

일반 Union-Find는 union은 잘하지만 rollback이 없다.

동적 그래프에서 간선 추가/삭제가 섞이면 과거 상태로 돌아가야 할 때가 있다.

### 2. 무엇을 기록하나

보통 부모 변경과 size 변경을 기록한다.

되돌릴 때는 이 로그를 역순으로 복구한다.

### 3. path compression과의 관계

rollback을 쉽게 하려면 path compression을 제한하는 경우가 많다.

즉 약간의 find 비용을 감수하고 undo 가능성을 얻는다.

### 4. backend에서의 감각

시간 축에 따라 그래프 상태가 바뀌는 분석 문제에 유용하다.

- 임시 연결성
- 온라인 변경의 오프라인 처리
- 시간 구간별 네트워크 상태

## 실전 시나리오

### 시나리오 1: 간선 삭제가 섞인 연결성

오프라인으로 구간을 나눠 처리할 때 DSU rollback을 쓸 수 있다.

### 시나리오 2: 오판

완전 온라인 동적 그래프에는 적합하지 않다.

## 코드로 보기

```java
import java.util.ArrayDeque;
import java.util.Deque;

public class DsuRollback {
    private final int[] parent;
    private final int[] size;
    private final Deque<int[]> history = new ArrayDeque<>();

    public DsuRollback(int n) {
        parent = new int[n];
        size = new int[n];
        for (int i = 0; i < n; i++) {
            parent[i] = i;
            size[i] = 1;
        }
    }

    public int find(int x) {
        while (parent[x] != x) x = parent[x];
        return x;
    }

    public boolean union(int a, int b) {
        a = find(a);
        b = find(b);
        if (a == b) {
            history.push(new int[]{-1, -1, -1});
            return false;
        }
        if (size[a] < size[b]) {
            int t = a; a = b; b = t;
        }
        history.push(new int[]{b, parent[b], size[a]});
        parent[b] = a;
        size[a] += size[b];
        return true;
    }

    public void rollback() {
        int[] log = history.pop();
        if (log[0] == -1) return;
        int b = log[0];
        int prevParent = log[1];
        int prevSize = log[2];
        int a = parent[b];
        parent[b] = prevParent;
        size[a] = prevSize;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| DSU Rollback | undo 가능한 union-find다 | path compression이 제한된다 | 오프라인 동적 연결성 |
| 일반 DSU | 매우 빠르다 | 되돌릴 수 없다 | static connectivity |
| DFS 재탐색 | 직관적이다 | 반복 질의에 비싸다 | 작은 그래프 |

## 꼬리질문

> Q: 왜 rollback이 필요한가?
> 의도: 시간 축 상태 복구 이해 확인
> 핵심: 삭제나 구간 처리에서 과거 상태가 필요하기 때문이다.

> Q: path compression을 제한하는 이유는?
> 의도: 복구 비용과 구조 변경의 관계 이해 확인
> 핵심: 되돌리기 어렵기 때문이다.

> Q: 어디에 자주 쓰이나?
> 의도: 오프라인 동적 연결성 감각 확인
> 핵심: 간선 추가/삭제가 섞인 연결성 문제다.

## 한 줄 정리

DSU Rollback은 union 변경 로그를 저장해 과거 상태로 되돌릴 수 있게 하는 오프라인 동적 연결성 기법이다.
