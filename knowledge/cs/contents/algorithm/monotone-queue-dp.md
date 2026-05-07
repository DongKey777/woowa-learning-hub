---
schema_version: 3
title: Monotone Queue DP
concept_id: algorithm/monotone-queue-dp
canonical: true
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- monotone-queue-dp
- sliding-window-dp
- constrained-transition-optimization
aliases:
- monotone queue dp
- monotonic queue dp
- deque optimization DP
- sliding window DP
- constrained transition
- window minimum DP
- optimized DP transition
- 단조 큐 DP
symptoms:
- DP 전이에서 최근 k개 상태의 최소 최대만 필요하다는 구조를 보고도 매번 k개를 전부 순회한다
- prefix min으로 충분한 전이와 window가 이동하며 오래된 후보를 제거해야 하는 전이를 구분하지 못한다
- monotone deque의 dominated candidate 증명을 DP 전이 최적화와 연결하지 못한다
intents:
- deep_dive
- comparison
- design
prerequisites:
- algorithm/monotone-deque-proof-intuition
- algorithm/sliding-window-patterns
- algorithm/dp-intro
next_docs:
- algorithm/bitset-optimization-patterns
- data-structure/segment-tree-lazy-propagation
- algorithm/amortized-analysis-pitfalls
linked_paths:
- contents/algorithm/monotone-deque-proof-intuition.md
- contents/algorithm/sliding-window-patterns.md
- contents/algorithm/bitset-optimization-patterns.md
confusable_with:
- algorithm/monotone-deque-proof-intuition
- algorithm/sliding-window-patterns
- algorithm/bitset-optimization-patterns
- data-structure/segment-tree-lazy-propagation
forbidden_neighbors: []
expected_queries:
- Monotone Queue DP는 dp 전이 범위의 최솟값이나 최댓값을 deque로 어떻게 유지해?
- dp[i]가 최근 k개 dp[j]의 min/max에 의존하면 왜 sliding window DP가 돼?
- prefix min으로 충분한 경우와 오래된 후보를 제거해야 하는 window DP는 어떻게 달라?
- Segment Tree DP와 Monotone Queue DP는 range query 일반성 기준으로 어떻게 나눠?
- monotone deque proof의 dominated candidate가 DP 전이 최적화에서 어떻게 쓰여?
contextual_chunk_prefix: |
  이 문서는 Monotone Queue DP advanced deep dive로, DP transition이 최근 k개
  상태의 minimum/maximum 같은 sliding window optimum에 의존할 때 monotone
  deque로 후보를 유지해 O(nk)를 O(n) 근처로 줄이는 패턴을 설명한다.
---
# Monotone Queue DP

> 한 줄 요약: Monotone Queue DP는 DP 전이식이 슬라이딩 윈도우 최적값으로 바뀔 때 단조 덱으로 상태를 최적화하는 패턴이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Monotone Deque Proof Intuition](./monotone-deque-proof-intuition.md)
> - [Sliding Window Patterns](./sliding-window-patterns.md)
> - [Bitset Optimization Patterns](./bitset-optimization-patterns.md)

> retrieval-anchor-keywords: monotone queue dp, deque optimization, sliding window dp, constrained transition, window minimum, window maximum, optimized dp transition, queue dp, state transition optimization

## 핵심 개념

일부 DP는 이전 상태들 중 특정 범위의 최솟값/최댓값만 필요하다.

이때 monotone queue를 쓰면 전이를 빠르게 할 수 있다.

전형적인 형태:

- `dp[i] = min(dp[j]) + cost`
- `j`는 특정 범위 안에 있어야 함

## 깊이 들어가기

### 1. 왜 덱이 나오나

범위 내 후보 중 최적만 유지하면 나머지는 버려도 된다.

그래서 monotone deque가 자연스럽다.

### 2. DP와 sliding window의 연결

구간 최솟값 유지와 동일한 구조가 DP 전이에 붙는다.

즉 "윈도우 내 최적값"을 유지하는 문제다.

### 3. backend에서의 감각

연속 시간 또는 연속 배치의 최적값을 구하는 상황에 맞는다.

- 제한된 작업 스케줄
- 최근 구간 최저 비용
- 윈도우 기반 최적화

### 4. 언제 안 맞나

전이 범위가 단조롭지 않거나 add/remove가 복잡하면 쓰기 어렵다.

## 실전 시나리오

### 시나리오 1: 구간 제한 최적화

최근 k개 상태만 볼 수 있는 DP에서 잘 맞는다.

### 시나리오 2: 오판

단순 prefix min으로 해결되지 않는다면 덱이 필요할 수 있다.

## 코드로 보기

```java
public class MonotoneQueueDp {
    public int solve(int[] cost, int k) {
        // 설명용 스케치: 실제 구현은 window min/max를 덱으로 유지한다.
        return 0;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Monotone Queue DP | 윈도우 전이를 빠르게 한다 | 조건이 맞아야 한다 | windowed transition |
| Brute Force DP | 단순하다 | 느리다 | 작은 입력 |
| Segment Tree DP | 범위 질의가 일반적이다 | 더 무겁다 | 복잡한 범위 전이 |

## 꼬리질문

> Q: 왜 monotone queue가 DP에 도움이 되나?
> 의도: 윈도우 최적값 전이 이해 확인
> 핵심: 전이 범위의 최솟값/최댓값만 유지하면 되기 때문이다.

> Q: 어떤 전이가 맞나?
> 의도: 적용 조건 이해 확인
> 핵심: 범위 내 최적 상태만 필요할 때다.

> Q: monotone deque proof와 관계는?
> 의도: 정당성 기반 이해 확인
> 핵심: 버려도 되는 후보를 버리는 불변식이 같다.

## 한 줄 정리

Monotone Queue DP는 슬라이딩 윈도우 최적값을 DP 전이에 붙여 상태 전이를 빠르게 하는 패턴이다.
