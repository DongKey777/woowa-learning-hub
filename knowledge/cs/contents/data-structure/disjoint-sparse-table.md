---
schema_version: 3
title: Disjoint Sparse Table
concept_id: data-structure/disjoint-sparse-table
canonical: false
category: data-structure
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 82
mission_ids: []
review_feedback_tags:
- static-range-query
- sparse-table-variant
- associative-operation-query
aliases:
- disjoint sparse table
- static range query
- associative operation range query
- prefix suffix preprocess
- immutable range query
- static monoid query
- O1 range combine
symptoms:
- 배열이 immutable이고 구간 질의가 많지만 업데이트가 필요한 Fenwick/Segment Tree와 정적 전처리 구조를 구분하지 못한다
- 일반 Sparse Table이 idempotent operation에 강한 이유와 Disjoint Sparse Table이 associative operation까지 다루는 차이를 놓친다
- prefix/suffix disjoint preprocess로 range를 겹치지 않는 두 조각으로 결합한다는 핵심을 이해하지 못한다
intents:
- comparison
- deep_dive
prerequisites:
- data-structure/sparse-table
next_docs:
- data-structure/sparse-table
- data-structure/fenwick-tree
- data-structure/fenwick-vs-segment-tree
- algorithm/binary-search-patterns
linked_paths:
- contents/data-structure/sparse-table.md
- contents/data-structure/fenwick-tree.md
- contents/algorithm/binary-search-patterns.md
confusable_with:
- data-structure/sparse-table
- data-structure/fenwick-tree
- data-structure/fenwick-vs-segment-tree
forbidden_neighbors: []
expected_queries:
- Disjoint Sparse Table은 일반 Sparse Table과 어떤 연산 성질에서 달라?
- static range query에서 associative operation을 O(1)에 가깝게 처리하는 방법은?
- 배열 업데이트가 없을 때 Fenwick Segment Tree보다 Sparse Table 계열을 보는 기준은?
- prefix suffix preprocess로 구간을 disjoint하게 합친다는 뜻을 설명해줘
- Disjoint Sparse Table을 backend read-only metric snapshot에 쓰는 감각은?
contextual_chunk_prefix: |
  이 문서는 immutable array의 static range query를 위한 Disjoint Sparse
  Table chooser다. 일반 sparse table의 idempotent operation 감각에서
  associative operation과 prefix/suffix disjoint preprocessing으로 확장하는
  차이를 설명한다.
---
# Disjoint Sparse Table

> 한 줄 요약: Disjoint Sparse Table은 정적 구간 질의를 O(1)에 가깝게 처리하되, 일반 sparse table보다 더 넓은 연산을 다루려는 전처리 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Sparse Table](./sparse-table.md)
> - [Fenwick Tree (Binary Indexed Tree)](./fenwick-tree.md)
> - [Binary Search Patterns](../algorithm/binary-search-patterns.md)

> retrieval-anchor-keywords: disjoint sparse table, static range query, associative operation, prefix suffix preprocess, O1 query, range combine, immutable query, binary lifting style, static monoid query

## 핵심 개념

Disjoint Sparse Table은 정적 배열에서 구간 질의를 빠르게 하기 위한 전처리 구조다.

Sparse Table과 비슷하지만,  
구간을 겹치지 않는 방식으로 나눠 더 일반적인 결합 연산을 다룰 수 있다.

주로 다음과 같은 조건에서 쓴다.

- 배열이 바뀌지 않는다
- 연산이 associative하다
- 빠른 구간 질의가 필요하다

## 깊이 들어가기

### 1. 왜 disjoint인가

기존 sparse table은 겹치는 블록을 활용해 idempotent 연산에 강하다.

Disjoint Sparse Table은 왼쪽 prefix와 오른쪽 suffix를 분리해,  
겹치지 않는 두 조각으로 질의를 결합한다.

### 2. 어떤 연산에 맞나

`min`, `max`, `gcd`처럼 associative한 연산에 맞는다.  
문제 구조에 따라 일반 sparse table보다 더 유연하게 생각할 수 있다.

### 3. backend에서의 감각

정적 리포트, 읽기 전용 메트릭, 기준 데이터셋의 구간 조회에 적합하다.

### 4. 왜 업데이트에 약한가

전처리가 무거워서 값이 바뀌면 다시 계산해야 한다.

## 실전 시나리오

### 시나리오 1: 정적 구간 질의

변경 없는 로그 snapshot에서 range query를 빠르게 보고 싶을 때 좋다.

### 시나리오 2: 오판

업데이트가 많으면 segment tree나 Fenwick tree가 더 낫다.

### 시나리오 3: 일반 sparse table과 선택

연산 성질에 따라 둘 중 맞는 쪽을 고르면 된다.

## 코드로 보기

```java
public class DisjointSparseTable {
    // 설명용 스케치: 실제 구현은 level별 prefix/suffix 전처리가 핵심이다.
    public int rangeMin(int l, int r) {
        return 0;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Disjoint Sparse Table | 정적 질의가 빠르다 | 구현과 전처리가 복잡하다 | immutable range query |
| Sparse Table | 매우 직관적이다 | idempotent 연산에 더 맞는다 | 정적 RMQ |
| Segment Tree | 업데이트를 지원한다 | 질의가 조금 느릴 수 있다 | 동적 배열 |

## 꼬리질문

> Q: 왜 일반 sparse table과 구분하나?
> 의도: 겹치는 구간과 disjoint 구조 차이를 이해하는지 확인
> 핵심: 전처리 방식과 연산 조건이 다르기 때문이다.

> Q: 어떤 상황에 적합한가?
> 의도: static query 패턴을 아는지 확인
> 핵심: 값이 바뀌지 않는 정적 배열이다.

> Q: 업데이트가 있으면 왜 안 되나?
> 의도: 전처리 비용 감각 확인
> 핵심: 다시 쌓아야 해서 이점이 사라진다.

## 한 줄 정리

Disjoint Sparse Table은 정적 배열에서 빠른 구간 질의를 위해 prefix/suffix 전처리를 쓰는 고급 범위 조회 구조다.
