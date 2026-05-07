---
schema_version: 3
title: Rerooting DP
concept_id: algorithm/rerooting-dp
canonical: true
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 83
mission_ids: []
review_feedback_tags:
- rerooting-dp
- tree-dp-all-roots
- prefix-suffix-child-merge
aliases:
- rerooting dp
- tree rerooting
- tree dp all roots
- subtree dp
- prefix suffix dp on tree
- dp propagation on tree
- sum of distances tree
- all roots tree dp
- 트리 루트 바꾸기 DP
symptoms:
- 트리 DP를 한 루트 기준 서브트리 값으로만 끝내고 모든 노드를 루트로 보는 답을 다시 계산해야 하는 상황을 놓친다
- 자식 하나를 제외한 나머지 정보를 합치는 prefix suffix 누적 필요성을 이해하지 못한다
- 일반 그래프에 rerooting DP를 바로 적용하려 하고 tree 전제를 확인하지 않는다
intents:
- deep_dive
- design
- comparison
prerequisites:
- data-structure/tree-basics
- algorithm/dp-intro
next_docs:
- algorithm/binary-lifting
- algorithm/topological-dp
- algorithm/tree-dfs-template-cheat-sheet
linked_paths:
- contents/algorithm/binary-lifting.md
- contents/algorithm/graph.md
- contents/algorithm/topological-dp.md
- contents/data-structure/tree-basics.md
confusable_with:
- algorithm/binary-lifting
- algorithm/topological-dp
- algorithm/tree-dfs-template-cheat-sheet
- data-structure/tree-basics
forbidden_neighbors: []
expected_queries:
- Rerooting DP는 한 루트에서 구한 트리 DP를 모든 루트 답으로 어떻게 확장해?
- down pass와 up pass 두 번 DFS로 subtree 정보와 parent side 정보를 어떻게 합쳐?
- 자식 하나를 제외한 나머지 정보를 빠르게 합치려면 prefix suffix 누적이 왜 필요해?
- 모든 노드까지 거리 합을 각 루트 기준으로 구할 때 rerooting DP를 어떻게 써?
- rerooting DP는 왜 tree 전제가 필요하고 일반 graph에는 바로 적용하기 어려워?
contextual_chunk_prefix: |
  이 문서는 Rerooting DP deep dive로, tree DP에서 한 루트 기준 down 값을 구한 뒤
  parent side 정보를 다시 내려 보내 모든 노드를 루트로 보는 답을 계산한다.
  prefix/suffix child merge, all roots, sum of distances, subtree outside info를
  다룬다.
---
# Rerooting DP

> 한 줄 요약: Rerooting DP는 트리에서 한 번의 DFS 결과를 다시 뿌려 모든 정점을 루트로 보는 답을 효율적으로 계산하는 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Binary Lifting](./binary-lifting.md)
> - [그래프 관련 알고리즘](./graph.md)
> - [Topological DP](./topological-dp.md)

> retrieval-anchor-keywords: rerooting dp, tree dp, subtree dp, all roots, tree reroot, prefix suffix dp on tree, dp propagation, tree distances, centroid-like intuition

## 핵심 개념

Rerooting DP는 "트리의 한 루트에서 구한 값을 모든 루트로 확장"하는 기법이다.

트리 DP에서 흔한 질문은 다음과 같다.

- 각 노드를 루트로 했을 때 정답은 무엇인가
- 모든 정점까지의 거리 합은?
- 서브트리 외부 정보를 어떻게 포함할까?

## 깊이 들어가기

### 1. 왜 rerooting이 필요한가

한 루트에서만 계산하면 그 루트 기준 결과만 나온다.

하지만 문제는 "모든 정점이 루트일 때의 답"을 요구할 수 있다.

### 2. 두 단계

보통 두 번 DFS를 쓴다.

1. 아래에서 위로 서브트리 정보를 모은다.
2. 위에서 아래로 부모 쪽 정보를 다시 내려보낸다.

이 방식으로 각 노드가 루트일 때의 값을 계산한다.

### 3. prefix/suffix 감각

어떤 노드의 자식들 중 한 자식을 제외한 나머지 정보를 빠르게 합치려면 prefix/suffix 누적이 유용하다.

### 4. backend에서의 감각

트리형 조직, 트리형 카탈로그, 계층형 상태 분석에서 자주 등장한다.

## 실전 시나리오

### 시나리오 1: 모든 루트의 거리 합

어떤 노드를 루트로 잡아도 전체 거리 합을 구하고 싶을 때 쓸 수 있다.

### 시나리오 2: 서브트리 외부 정보

자식들만 보아서는 안 되는 문제에서 rerooting이 힘을 발휘한다.

### 시나리오 3: 오판

트리가 아니라 일반 그래프라면 rerooting DP가 바로 적용되지 않는다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.List;

public class RerootingDp {
    private final List<List<Integer>> tree;
    private final int[] down;
    private final int[] up;

    public RerootingDp(List<List<Integer>> tree) {
        this.tree = tree;
        int n = tree.size();
        this.down = new int[n];
        this.up = new int[n];
    }

    public void dfsDown(int v, int p) {
        for (int to : tree.get(v)) {
            if (to == p) continue;
            dfsDown(to, v);
            down[v] = Math.max(down[v], down[to] + 1);
        }
    }

    public void dfsUp(int v, int p) {
        for (int to : tree.get(v)) {
            if (to == p) continue;
            up[to] = Math.max(up[v] + 1, down[v] + 1);
            dfsUp(to, v);
        }
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Rerooting DP | 모든 루트의 답을 효율적으로 구한다 | 두 번의 DFS와 상태 설계가 필요하다 | tree DP all-roots |
| Naive re-run | 직관적이다 | 너무 느리다 | 작은 트리 |
| BFS/DFS 단일 루트 | 구현이 쉽다 | 모든 루트 답을 못 구한다 | 루트 고정 문제 |

## 꼬리질문

> Q: 왜 두 번 DFS가 필요한가?
> 의도: 위/아래 정보 분리를 이해하는지 확인
> 핵심: 서브트리 정보와 부모 방향 정보를 둘 다 써야 하기 때문이다.

> Q: prefix/suffix가 왜 나오나?
> 의도: 자식 하나를 제외한 합성 이해 확인
> 핵심: 각 자식의 기여를 빠르게 합치기 위해서다.

> Q: 어디에 자주 쓰이나?
> 의도: tree DP 패턴 인식 확인
> 핵심: 거리 합, 최장거리, 모든 루트 최적화다.

## 한 줄 정리

Rerooting DP는 트리에서 한 루트의 결과를 모든 루트로 효율적으로 확장하는 두 단계 DFS 기법이다.
