---
schema_version: 3
title: Persistent Segment Tree Basics
concept_id: data-structure/persistent-segment-tree
canonical: false
category: data-structure
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 83
mission_ids: []
review_feedback_tags:
- persistent-segment-tree
- versioned-range-query
- path-copying
aliases:
- Persistent Segment Tree
- versioned segment tree
- path copying segment tree
- historical query
- time travel query
- k-th number persistent tree
- functional segment tree
symptoms:
- 업데이트 후에도 과거 버전 range query를 해야 하는데 일반 segment tree로 덮어써 이전 상태를 잃는다
- path copying으로 변경 경로만 새 node를 만들고 나머지는 공유한다는 persistence 핵심을 놓친다
- version 수와 update 수에 따라 메모리 비용이 늘어나는 trade-off를 보지 않는다
intents:
- definition
- deep_dive
prerequisites:
- data-structure/segment-tree-lazy-propagation
- data-structure/coordinate-compression-patterns
next_docs:
- data-structure/disjoint-sparse-table
- data-structure/fenwick-vs-segment-tree
- data-structure/order-statistic-tree
linked_paths:
- contents/data-structure/segment-tree-lazy-propagation.md
- contents/data-structure/disjoint-sparse-table.md
- contents/data-structure/coordinate-compression-patterns.md
confusable_with:
- data-structure/segment-tree-lazy-propagation
- data-structure/disjoint-sparse-table
- data-structure/order-statistic-tree
- data-structure/fenwick-tree
forbidden_neighbors: []
expected_queries:
- Persistent Segment Tree는 이전 버전을 보존하면서 range query를 어떻게 해?
- path copying으로 segment tree update 경로만 복사한다는 뜻은?
- 과거 시점 k번째 수나 versioned range query를 처리할 때 왜 persistent tree를 써?
- version 수가 많아지면 Persistent Segment Tree memory cost가 어떻게 늘어?
- 일반 Segment Tree와 Persistent Segment Tree를 역사 조회 기준으로 비교해줘
contextual_chunk_prefix: |
  이 문서는 Persistent Segment Tree를 update 때 기존 node를 덮어쓰지 않고
  path copying으로 새 version root를 만드는 versioned range query primer로
  설명한다. historical query, k-th number, immutable structure, memory cost를
  다룬다.
---
# Persistent Segment Tree Basics

> 한 줄 요약: Persistent Segment Tree는 구간 트리의 이전 버전을 보존하면서 시간 축 버전 조회를 가능하게 하는 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Segment Tree Lazy Propagation](./segment-tree-lazy-propagation.md)
> - [Disjoint Sparse Table](./disjoint-sparse-table.md)
> - [Coordinate Compression Patterns](./coordinate-compression-patterns.md)

> retrieval-anchor-keywords: persistent segment tree, versioned segment tree, immutable structure, path copying, historical query, time travel query, k-th number, offline versioning, functional tree, versioned range query

## 핵심 개념

Persistent Segment Tree는 업데이트를 할 때 기존 트리를 덮어쓰지 않고,  
바뀐 경로만 복사해 새 버전을 만드는 세그먼트 트리다.

이렇게 하면 과거 버전도 그대로 조회할 수 있다.

## 깊이 들어가기

### 1. path copying

갱신 경로의 노드만 새로 만들고 나머지는 공유한다.

이 덕분에 버전 수가 늘어도 전체 복사 비용이 들지 않는다.

### 2. 왜 persistence가 필요한가

시간에 따라 바뀌는 배열을 다루면서, 과거 상태도 질문해야 하는 문제가 있다.

- 시간별 통계
- 이전 시점 비교
- 버전별 range query

### 3. backend에서의 감각

이력 조회가 필요할 때 유용하다.

- 감사 로그
- 버전별 설정값
- 과거 지표 스냅샷

### 4. 주의점

메모리는 버전 수만큼 늘어난다.
그래서 불변성의 편의성과 메모리 비용을 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 과거 버전 k번째 수

버전별 배열에서 k번째 값을 찾는 유형에 잘 맞는다.

### 시나리오 2: 시점별 집계

과거 상태를 손대지 않고 조회해야 할 때 유용하다.

### 시나리오 3: 오판

버전이 너무 많고 업데이트가 잦으면 메모리 부담이 크다.

## 코드로 보기

```java
public class PersistentSegmentTreeNotes {
    static final class Node {
        Node left, right;
        int sum;
    }

    public Node update(Node prev, int l, int r, int idx, int delta) {
        Node cur = new Node();
        cur.sum = (prev == null ? 0 : prev.sum) + delta;
        return cur;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Persistent Segment Tree | 과거 버전 조회가 가능하다 | 메모리를 더 쓴다 | historical query |
| 일반 Segment Tree | 단순하고 빠르다 | 이전 버전을 못 본다 | 현재 상태만 필요 |
| Sparse Table | 정적 질의에 강하다 | 업데이트가 불가능하다 | immutable data |

## 꼬리질문

> Q: persistence의 핵심은 무엇인가?
> 의도: 불변성과 버전 분리 이해 확인
> 핵심: 바뀐 경로만 복사해 이전 버전을 보존하는 것이다.

> Q: 왜 path copying이 효율적인가?
> 의도: 부분 공유 구조 이해 확인
> 핵심: 전체가 아니라 경로만 새로 만들기 때문이다.

> Q: 어떤 문제에 맞나?
> 의도: versioned query 감각 확인
> 핵심: 과거 시점 조회와 버전별 집계다.

## 한 줄 정리

Persistent Segment Tree는 업데이트 경로만 복사해 버전을 보존하며 과거 상태 질의를 가능하게 하는 구조다.
