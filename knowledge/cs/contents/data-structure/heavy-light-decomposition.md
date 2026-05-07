---
schema_version: 3
title: Heavy-Light Decomposition
concept_id: data-structure/heavy-light-decomposition
canonical: false
category: data-structure
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 82
mission_ids: []
review_feedback_tags:
- heavy-light-decomposition
- tree-path-query
- segment-tree-on-tree
aliases:
- Heavy-Light Decomposition
- HLD
- tree path query
- chain decomposition
- segment tree on tree
- LCA path query
- tree flattening
symptoms:
- 트리에서 두 노드 사이 path sum max update 질의를 매번 DFS로 처리하려고 해 쿼리 수가 많을 때 비용이 커진다
- 트리 경로를 heavy chain 몇 개의 배열 구간 질의로 바꾸는 핵심 변환을 이해하지 못한다
- LCA, binary lifting, segment tree를 각각 따로 보고 HLD의 path query 흐름으로 연결하지 못한다
intents:
- deep_dive
- design
prerequisites:
- algorithm/binary-lifting
- data-structure/segment-tree-lazy-propagation
next_docs:
- algorithm/binary-lifting
- algorithm/rerooting-dp
- data-structure/segment-tree-lazy-propagation
linked_paths:
- contents/algorithm/binary-lifting.md
- contents/algorithm/rerooting-dp.md
- contents/data-structure/segment-tree-lazy-propagation.md
confusable_with:
- algorithm/binary-lifting
- algorithm/rerooting-dp
- data-structure/segment-tree-lazy-propagation
- data-structure/fenwick-tree
forbidden_neighbors: []
expected_queries:
- Heavy-Light Decomposition은 트리 경로 질의를 어떻게 배열 구간 질의로 바꿔?
- HLD에서 heavy edge와 chain head는 무엇을 의미해?
- LCA와 Segment Tree를 HLD path query에서 어떻게 같이 써?
- tree path sum max update가 많을 때 HLD가 필요한 이유는?
- 경로 질의가 거의 없으면 HLD가 과한 구조인 이유를 알려줘
contextual_chunk_prefix: |
  이 문서는 Heavy-Light Decomposition을 트리 path query를 heavy chain의
  연속 배열 구간 질의로 바꾸는 deep dive로 설명한다. heavy edge, chain
  head, LCA, binary lifting, segment tree on tree, path update/query를 다룬다.
---
# Heavy-Light Decomposition

> 한 줄 요약: Heavy-Light Decomposition은 트리 경로를 몇 개의 체인으로 나눠 경로 질의를 배열 질의처럼 바꾸는 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Binary Lifting](../algorithm/binary-lifting.md)
> - [Rerooting DP](../algorithm/rerooting-dp.md)
> - [Segment Tree Lazy Propagation](./segment-tree-lazy-propagation.md)

> retrieval-anchor-keywords: heavy light decomposition, HLD, tree path query, chain decomposition, segment tree on tree, subtree query, lca path query, path sum, tree flattening

## 핵심 개념

HLD는 트리의 경로를 heavy edge와 light edge로 나눠서,  
경로 질의를 적은 수의 체인 구간 질의로 바꾸는 기법이다.

자주 나오는 질문:

- 경로 합
- 경로 최댓값
- 경로 업데이트
- 서브트리와 경로를 함께 다루는 문제

## 깊이 들어가기

### 1. heavy edge는 무엇인가

자식 서브트리가 가장 큰 간선 하나를 heavy로 둔다.

이렇게 하면 루트에서 잎까지 내려갈 때 heavy chain을 길게 유지할 수 있다.

### 2. 왜 체인으로 나누나

트리 경로를 몇 개의 연속 구간으로 바꾸면, 그 구간을 segment tree나 Fenwick으로 처리할 수 있다.

즉 트리 문제를 배열 문제로 변환하는 것이다.

### 3. LCA와의 연결

경로 질의는 보통 LCA를 기준으로 두 노드에서 위로 올라가며 체인을 건너뛴다.

binary lifting과 결합하면 경로 쿼리를 더 효율적으로 만들 수 있다.

### 4. backend에서의 감각

트리 구조의 경로 계산이 필요한 경우 유용하다.

- 조직 경로 비용
- 계층형 권한 전파
- 폴더 경로 기반 통계

## 실전 시나리오

### 시나리오 1: 경로 합

두 노드 사이 경로의 값을 합치고 싶을 때 적합하다.

### 시나리오 2: 서브트리 업데이트 + 경로 조회

트리형 구조에서 두 종류의 질의를 섞어 처리할 수 있다.

### 시나리오 3: 오판

경로 질의가 거의 없으면 HLD는 과한 구조일 수 있다.

## 코드로 보기

```java
public class HeavyLightNotes {
    // 설명용 스케치: 실제 구현은 size 계산, heavy child 선택, chain head 관리가 필요하다.
    public int queryPath(int u, int v) {
        return 0;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Heavy-Light Decomposition | 경로 질의를 배열 질의로 바꾼다 | 구현이 복잡하다 | tree path queries |
| Binary Lifting | 조상 조회가 빠르다 | 경로 집계는 약하다 | kth ancestor, LCA |
| Naive DFS | 직관적이다 | 너무 느리다 | 작은 트리 |

## 꼬리질문

> Q: heavy edge를 왜 고르나?
> 의도: 체인 길이 최적화 이해 확인
> 핵심: 경로가 적은 체인으로 분해되도록 하기 위해서다.

> Q: HLD가 왜 배열 질의로 바뀌나?
> 의도: 트리 flattening 감각 확인
> 핵심: 체인마다 연속 구간을 만들기 때문이다.

> Q: binary lifting과 차이는?
> 의도: 경로 집계와 조상 점프의 차이 이해 확인
> 핵심: HLD는 경로 질의, binary lifting은 점프/조상이다.

## 한 줄 정리

Heavy-Light Decomposition은 트리 경로를 체인 구간으로 분해해 segment tree 같은 배열 구조로 질의를 처리하는 기법이다.
