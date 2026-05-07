---
schema_version: 3
title: Binary Lifting vs Heavy-Light Decomposition
concept_id: algorithm/binary-lifting-vs-hld
canonical: true
category: algorithm
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- binary-lifting-vs-hld
- tree-query-selection
- ancestor-vs-path-query
aliases:
- binary lifting vs hld
- binary lifting vs heavy light decomposition
- tree query comparison
- LCA vs path query
- ancestor query vs path query
- segment tree on tree
- heavy light decomposition
- 트리 질의 비교
symptoms:
- kth ancestor나 LCA처럼 위로 점프하는 질의에 HLD를 먼저 써서 구현을 과하게 만든다
- path sum, path max, path update처럼 경로 집계가 필요한데 binary lifting만으로 해결하려 한다
- rerooting DP처럼 모든 루트의 값을 구하는 문제와 tree path query 문제를 섞는다
intents:
- comparison
- design
- deep_dive
prerequisites:
- algorithm/binary-lifting
- data-structure/tree-basics
next_docs:
- data-structure/heavy-light-decomposition
- algorithm/rerooting-dp
- algorithm/tree-dfs-template-cheat-sheet
linked_paths:
- contents/algorithm/binary-lifting.md
- contents/data-structure/heavy-light-decomposition.md
- contents/algorithm/rerooting-dp.md
confusable_with:
- algorithm/binary-lifting
- data-structure/heavy-light-decomposition
- algorithm/rerooting-dp
- data-structure/tree-basics
forbidden_neighbors: []
expected_queries:
- Binary Lifting과 Heavy-Light Decomposition은 조상 점프와 경로 질의 관점에서 어떻게 달라?
- kth ancestor나 LCA만 필요하면 HLD보다 binary lifting이 충분한 이유가 뭐야?
- path sum이나 path max처럼 경로 집계가 필요하면 HLD가 더 자연스러운 이유가 뭐야?
- LCA는 binary lifting으로 구하고 경로 집계는 HLD로 같이 쓸 수 있어?
- rerooting DP와 tree path query는 all roots와 path aggregation 관점에서 어떻게 달라?
contextual_chunk_prefix: |
  이 문서는 Binary Lifting vs Heavy-Light Decomposition bridge로, binary lifting은
  kth ancestor와 LCA 같은 ancestor jump에 강하고, HLD는 tree path sum/max/update를
  segment tree on tree로 처리하는 경로 질의에 강하다는 선택 기준을 설명한다.
---
# Binary Lifting vs Heavy-Light Decomposition

> 한 줄 요약: Binary Lifting은 조상 점프에 강하고, Heavy-Light Decomposition은 경로 질의에 강하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Binary Lifting](./binary-lifting.md)
> - [Heavy-Light Decomposition](../data-structure/heavy-light-decomposition.md)
> - [Rerooting DP](./rerooting-dp.md)

> retrieval-anchor-keywords: binary lifting vs heavy light decomposition, tree query comparison, lca, path query, ancestor query, tree decomposition, segment tree on tree

## 핵심 개념

둘 다 트리 질의를 빠르게 하지만, 질문이 다르다.

- Binary Lifting: k번째 조상, LCA, 점프
- HLD: 경로 합, 경로 최댓값, 경로 업데이트

즉 하나는 "위로 뛰기", 다른 하나는 "경로를 잘라 배열로 보기"다.

## 깊이 들어가기

### 1. Binary Lifting이 잘 맞는 경우

- 조상 질의가 많다
- LCA가 핵심이다
- 경로 전체보다 점프가 중요하다

### 2. HLD가 잘 맞는 경우

- 경로 위의 값을 합치거나 갱신한다
- 트리 경로를 segment tree로 처리하고 싶다
- 서브트리와 경로 질의를 같이 다룬다

### 3. backend에서의 감각

조직도, 권한 전파, 계층형 비용 계산에서는 두 구조가 서로 다른 질문을 해결한다.

### 4. 같이 쓰는 경우

실전에서는 binary lifting으로 LCA를 구하고, HLD로 경로 집계를 한다.

## 실전 시나리오

### 시나리오 1: kth ancestor

Binary lifting이 자연스럽다.

### 시나리오 2: path sum

HLD가 더 강하다.

### 시나리오 3: 오판

경로 질의에 binary lifting만 쓰면 집계가 부족할 수 있다.

## 코드로 보기

```java
public class TreeQuerySelector {
    public static String choose(boolean ancestorQuery, boolean pathQuery) {
        if (ancestorQuery) return "Binary Lifting";
        if (pathQuery) return "Heavy-Light Decomposition";
        return "Need a different tool";
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Binary Lifting | 구현이 안정적이고 점프가 빠르다 | 경로 집계는 약하다 | LCA, kth ancestor |
| Heavy-Light Decomposition | 경로 질의에 강하다 | 구현이 복잡하다 | path query |
| Rerooting DP | 모든 루트 결과를 다룬다 | 목적이 다르다 | all-roots tree DP |

## 꼬리질문

> Q: 둘의 가장 큰 차이는 무엇인가요?
> 의도: 문제 유형 구분 확인
> 핵심: binary lifting은 조상 점프, HLD는 경로 집계다.

> Q: 같이 쓸 수도 있나요?
> 의도: 조합 전략 이해 확인
> 핵심: LCA는 binary lifting, 경로 질의는 HLD로 나눠 쓸 수 있다.

> Q: 어떤 상황에서 HLD가 과한가요?
> 의도: 구조 선택 감각 확인
> 핵심: 조상 질의만 필요한 경우다.

## 한 줄 정리

Binary Lifting은 조상 점프와 LCA에, HLD는 경로 집계와 업데이트에 더 잘 맞는다.
