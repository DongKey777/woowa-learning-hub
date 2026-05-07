---
schema_version: 3
title: Mo's Algorithm Basics
concept_id: algorithm/mo-algorithm-basics
canonical: true
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- mo-algorithm
- offline-range-query
- sqrt-decomposition-ordering
aliases:
- mo's algorithm
- Mo algorithm basics
- offline range query
- sqrt decomposition query ordering
- range query reordering
- add remove window maintenance
- 구간 질의 오프라인
- 모 알고리즘
symptoms:
- 모든 구간 질의를 입력 순서대로 처음부터 다시 계산해 반복 비용을 줄이지 못한다
- online으로 즉시 답해야 하는 질의와 offline으로 순서를 바꿀 수 있는 질의를 구분하지 못한다
- Mo's algorithm에서 query ordering보다 add remove 상태 유지 함수 비용이 핵심이라는 점을 놓친다
intents:
- deep_dive
- comparison
- design
prerequisites:
- algorithm/sliding-window-patterns
- algorithm/basic
next_docs:
- algorithm/bitset-optimization-patterns
- data-structure/fenwick-tree
- data-structure/segment-tree-lazy-propagation
linked_paths:
- contents/algorithm/sliding-window-patterns.md
- contents/algorithm/binary-search-patterns.md
- contents/algorithm/bitset-optimization-patterns.md
confusable_with:
- algorithm/sliding-window-patterns
- data-structure/fenwick-tree
- data-structure/segment-tree-lazy-propagation
- algorithm/bitset-optimization-patterns
forbidden_neighbors: []
expected_queries:
- Mo's algorithm은 offline range query를 왜 재정렬해서 포인터 이동 비용을 줄여?
- query 순서를 바꿀 수 없는 online 질의에는 Mo's algorithm이 왜 맞지 않아?
- sqrt decomposition으로 left block과 right order를 정하는 직관을 알려줘
- 구간 내 distinct count나 frequency query에서 add/remove 함수가 왜 중요해?
- prefix sum, segment tree, Mo's algorithm은 range query 조건에서 어떻게 나눠?
contextual_chunk_prefix: |
  이 문서는 Mo's Algorithm advanced deep dive로, offline range query를 block
  ordering으로 재정렬해 현재 구간에서 다음 구간으로 이동할 때 add/remove만
  수행하여 frequency, distinct count 같은 구간 통계를 유지하는 기법을 설명한다.
---
# Mo's Algorithm Basics

> 한 줄 요약: Mo's algorithm은 오프라인 구간 질의를 재정렬해 포인터 이동 비용을 줄이는 sqrt decomposition 기반 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Sliding Window Patterns](./sliding-window-patterns.md)
> - [Binary Search Patterns](./binary-search-patterns.md)
> - [Bitset Optimization Patterns](./bitset-optimization-patterns.md)

> retrieval-anchor-keywords: mo's algorithm, offline query, sqrt decomposition, range query ordering, add remove, sliding window queries, query reordering, frequency maintenance, interval query optimization

## 핵심 개념

Mo's algorithm은 여러 구간 질의를 오프라인으로 받아서,  
질의 순서를 잘 정렬해 포인터 이동을 최소화하는 기법이다.

핵심 아이디어:

- 질의를 블록 단위로 정렬한다.
- 현재 구간에서 다음 구간으로 이동할 때 add/remove를 조금만 한다.

즉 "각 질의마다 처음부터 다시 계산하지 않는다"가 핵심이다.

## 깊이 들어가기

### 1. 왜 offline이어야 하나

질의 순서를 바꿔야 최적화가 된다.

그래서 모든 질의를 먼저 받은 뒤 재정렬할 수 있어야 한다.

### 2. sqrt decomposition 감각

left를 블록으로 묶고 right를 정렬하면, 포인터 이동 총량이 줄어든다.

대략 `O((N + Q) sqrt(N))` 감각으로 설명된다.

### 3. add/remove가 핵심

현재 구간에 원소가 들어오면 add, 나가면 remove를 호출해 상태를 유지한다.

이 상태 유지 함수가 빠를수록 Mo's algorithm이 강해진다.

### 4. backend에서의 감각

대량 구간 질의가 반복되는 분석 작업에 잘 맞는다.

- 로그 구간 통계
- 이벤트 구간 빈도
- 부분 배열 분석

## 실전 시나리오

### 시나리오 1: 구간 빈도

각 질의에 대해 구간 내 고유값 수나 빈도 통계를 구할 때 유용하다.

### 시나리오 2: 오판

질의가 online이어야 하면 Mo의 재정렬을 쓸 수 없다.

### 시나리오 3: 상태 업데이트 비용

add/remove가 비싸면 Mo의 이점이 줄어든다.

## 코드로 보기

```java
public class MoAlgorithmNotes {
    // 설명용 스케치: 실제 핵심은 query ordering과 add/remove 유지다.
    static final class Query {
        int l, r, idx;
        Query(int l, int r, int idx) { this.l = l; this.r = r; this.idx = idx; }
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Mo's Algorithm | 오프라인 구간 질의를 효율화한다 | 온라인 질의에 못 쓴다 | 구간 통계 반복 |
| Prefix Sum | 매우 단순하다 | 조건이 제한적이다 | 합 위주 질의 |
| Segment Tree | 온라인에 강하다 | 구현이 복잡하다 | 동적 질의 |

## 꼬리질문

> Q: 왜 질의 순서를 바꾸나?
> 의도: 포인터 이동 최소화 아이디어 이해 확인
> 핵심: 구간 이동 비용을 줄이기 위해서다.

> Q: 온라인 질의에는 왜 안 맞나?
> 의도: 오프라인 전제 이해 확인
> 핵심: 질의 순서를 미리 정해야 하기 때문이다.

> Q: 어떤 상태가 잘 맞나?
> 의도: add/remove 기반 상태 관리 이해 확인
> 핵심: 빈도, 카운트, distinct tracking이다.

## 한 줄 정리

Mo's algorithm은 오프라인 구간 질의를 재정렬해 포인터 이동을 줄이는 sqrt decomposition 기반 최적화다.
