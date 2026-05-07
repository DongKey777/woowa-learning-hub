---
schema_version: 3
title: Fenwick Tree Binary Indexed Tree
concept_id: data-structure/fenwick-tree
canonical: false
category: data-structure
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 84
mission_ids:
- missions/lotto
review_feedback_tags:
- fenwick-tree
- prefix-sum-point-update
- lowbit-indexing
aliases:
- Fenwick Tree
- Binary Indexed Tree
- BIT prefix sum
- lowbit
- point update range sum
- cumulative frequency tree
- inversion count BIT
symptoms:
- prefix sum과 point update를 모두 빠르게 해야 하는데 매번 전체 prefix를 다시 계산하거나 Segment Tree부터 과하게 떠올린다
- Fenwick Tree의 1-indexing과 lowbit가 각 index의 담당 구간을 결정한다는 핵심을 이해하지 못한다
- range sum은 prefix(r) - prefix(l-1)로 계산된다는 기본형과 range update 같은 변형을 섞어 시작한다
intents:
- definition
- deep_dive
prerequisites:
- algorithm/time-complexity-intro
next_docs:
- data-structure/fenwick-vs-segment-tree
- data-structure/fenwick-segment-tree-operations-playbook
- data-structure/segment-tree-lazy-propagation
- algorithm/amortized-analysis-pitfalls
linked_paths:
- contents/data-structure/segment-tree-lazy-propagation.md
- contents/data-structure/fenwick-vs-segment-tree.md
- contents/data-structure/fenwick-segment-tree-operations-playbook.md
- contents/data-structure/basic.md
- contents/algorithm/amortized-analysis-pitfalls.md
confusable_with:
- data-structure/fenwick-vs-segment-tree
- data-structure/segment-tree-lazy-propagation
- data-structure/sparse-table
- data-structure/coordinate-compression-patterns
forbidden_neighbors: []
expected_queries:
- Fenwick Tree는 prefix sum과 point update를 어떻게 O(log n)에 처리해?
- Binary Indexed Tree에서 lowbit와 1-indexing이 왜 중요한지 설명해줘
- range sum을 prefix(r) - prefix(l-1)로 계산하는 Fenwick 기본형을 알려줘
- 누적 빈도나 inversion count 문제에서 Fenwick Tree를 쓰는 이유는?
- Fenwick Tree와 Segment Tree 중 단순 prefix/range sum에는 무엇이 더 깔끔해?
contextual_chunk_prefix: |
  이 문서는 Fenwick Tree 또는 Binary Indexed Tree를 prefix sum과 point update를
  O(log n)에 처리하는 누적 자료구조로 설명하는 primer다. lowbit, 1-indexing,
  range sum, cumulative frequency, inversion count, Segment Tree와의 경계를
  다룬다.
---
# Fenwick Tree (Binary Indexed Tree)

> 한 줄 요약: Fenwick Tree는 prefix sum과 point update를 모두 O(log n)으로 처리하는 가벼운 누적 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Segment Tree Lazy Propagation](./segment-tree-lazy-propagation.md)
> - [Fenwick Tree vs Segment Tree](./fenwick-vs-segment-tree.md)
> - [Fenwick and Segment Tree Operations Playbook](./fenwick-segment-tree-operations-playbook.md)
> - [자료구조 정리](./basic.md)
> - [상각 분석과 복잡도 함정](../algorithm/amortized-analysis-pitfalls.md)

> retrieval-anchor-keywords: fenwick tree, binary indexed tree, BIT, prefix sum, point update, range sum, lowbit, inversion count, frequency table, cumulative frequency, operational counter tree, bucket aggregation

## 핵심 개념

Fenwick Tree는 배열의 prefix 정보를 부분적으로 저장해서,  
`sum(1..i)`와 `add(i, delta)`를 모두 빠르게 처리한다.

세그먼트 트리보다 메모리가 적고 구현이 단순해서, 다음 같은 문제에 자주 쓴다.

- 누적 카운트
- 순위 통계
- 빈도 배열
- inversion count
- 실시간 구간 합 모니터링

## 깊이 들어가기

### 1. lowbit가 왜 핵심인가

Fenwick Tree는 `i & -i`로 현재 인덱스가 담당하는 구간 크기를 찾는다.

- `lowbit(6) = 2`
- `lowbit(12) = 4`

이 값 덕분에 각 인덱스가 어떤 prefix 구간을 대표하는지 계산할 수 있다.

### 2. 1-indexing이 자주 쓰이는 이유

Fenwick Tree는 보통 1-indexed로 구현한다.

- `0`은 lowbit가 의미 없어진다.
- 부모/다음 노드 이동이 깔끔해진다.

즉 배열 인덱스 편의성보다 수식의 단순함이 중요하다.

### 3. range sum과 point update

기본형은 두 연산이다.

- `add(i, delta)`: i 위치 값을 delta만큼 더한다
- `sum(i)`: 1..i prefix 합을 구한다

구간 합 `[l, r]`은 `sum(r) - sum(l - 1)`로 계산한다.

### 4. backend에서의 활용

Fenwick Tree는 "정렬된 값의 누적 분포"를 다루기 좋다.

- 시간대별 트래픽 누적
- 점수 분포 집계
- 주문량 순위 계산
- 특정 임계값 이하의 카운트 조회

## 실전 시나리오

### 시나리오 1: 실시간 누적 카운터

분 단위 요청 수를 쌓아 두고, 특정 시점까지의 누적 요청 수를 자주 보고 싶을 때 잘 맞는다.

### 시나리오 2: 순위 또는 분위수 근사

값을 구간으로 bucketize한 뒤 빈도 Fenwick Tree를 쓰면, 누적 분포를 빠르게 읽을 수 있다.

### 시나리오 3: inversion count

배열의 상대적 역전 개수를 구할 때, 앞에서 본 값들의 빈도를 prefix sum으로 세면 효율적이다.

### 시나리오 4: 세그먼트 트리보다 가벼운 경우

점 갱신 + prefix 중심 질의만 필요하면 Fenwick Tree가 더 간단하고 빠를 수 있다.

## 코드로 보기

```java
public class FenwickTree {
    private final long[] tree;

    public FenwickTree(int n) {
        this.tree = new long[n + 1];
    }

    public void add(int index, long delta) {
        for (int i = index; i < tree.length; i += i & -i) {
            tree[i] += delta;
        }
    }

    public long sum(int index) {
        long result = 0;
        for (int i = index; i > 0; i -= i & -i) {
            result += tree[i];
        }
        return result;
    }

    public long rangeSum(int left, int right) {
        if (left > right) {
            return 0;
        }
        return sum(right) - sum(left - 1);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Fenwick Tree | 구현이 간단하고 메모리가 작다 | 복잡한 구간 연산은 약하다 | 점 갱신 + 누적 질의 중심일 때 |
| Segment Tree | 표현력이 높다 | 구현과 메모리 부담이 크다 | range update/query가 복잡할 때 |
| Prefix Array | 조회가 매우 빠르다 | 갱신 비용이 비싸다 | 데이터가 거의 바뀌지 않을 때 |

Fenwick Tree는 "적당히 강력하고 적당히 단순한" 중간 지점이다.

## 꼬리질문

> Q: lowbit가 왜 그렇게 동작하나?
> 의도: 이진수 구조와 구간 분할 이해 확인
> 핵심: 가장 낮은 1비트가 담당하는 구간 크기를 나타낸다.

> Q: 세그먼트 트리보다 언제 더 낫나?
> 의도: 자료구조 선택 기준 확인
> 핵심: 점 갱신과 prefix/query 정도면 Fenwick Tree가 더 가볍다.

> Q: 왜 0-indexed 구현이 덜 흔한가?
> 의도: 수식 단순화 감각 확인
> 핵심: lowbit 이동과 부모 추적이 1-indexed에서 훨씬 깔끔하다.

## 한 줄 정리

Fenwick Tree는 prefix 합과 점 갱신을 빠르게 처리하는, 작고 실용적인 누적 자료구조다.
