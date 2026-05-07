---
schema_version: 3
title: Divide and Conquer DP Optimization
concept_id: algorithm/divide-and-conquer-dp-optimization
canonical: false
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- partition-dp-monotonicity
- opt-range-pruning
aliases:
- divide and conquer dp optimization
- monotone opt
- knuth-like partition
- dp speedup
- interval dp
- opt monotonicity
- partition point
- dynamic programming optimization
symptoms:
- 분할 DP 식은 보이는데 왜 탐색 구간을 줄여도 되는지 근거가 안 보여
- Knuth optimization이랑 divide and conquer DP를 같은 것으로 읽고 있어
- 최적 분할점이 단조적이라는 말이 코드에서 어떤 의미인지 모르겠어
intents:
- deep_dive
prerequisites:
- algorithm/dp-intro
- algorithm/knuth-optimization-intuition
next_docs:
- algorithm/convex-hull-trick-basics
- algorithm/topological-dp
- algorithm/monotone-queue-dp
linked_paths:
- contents/algorithm/knuth-optimization-intuition.md
- contents/algorithm/convex-hull-trick-basics.md
- contents/algorithm/binary-search-patterns.md
- contents/algorithm/topological-dp.md
- contents/algorithm/monotone-queue-dp.md
confusable_with:
- algorithm/knuth-optimization-intuition
- algorithm/convex-hull-trick-basics
forbidden_neighbors:
- contents/algorithm/convex-hull-trick-basics.md
- contents/algorithm/knuth-optimization-intuition.md
expected_queries:
- 분할 정복 DP 최적화는 어떤 단조성 조건이 있어야 적용할 수 있어?
- opt 배열이 오른쪽으로만 움직인다는 말이 divide and conquer DP에서 왜 중요한지 설명해줘
- 구간 분할 DP를 O(n^2)에서 줄일 때 Knuth 말고 다른 최적화로 보는 기준이 뭐야
- partition DP에서 최적 k 탐색 범위를 재귀적으로 줄이는 아이디어를 알고 싶어
- monotone opt가 성립할 때 divide and conquer DP 코드가 왜 mid 기준으로 퍼지는지 이해하고 싶어
contextual_chunk_prefix: |
  이 문서는 알고리즘 학습자가 분할 DP에서 최적 분할점이 오른쪽으로만 밀리는 조건이
  왜 탐색 범위 축소 근거가 되는지, mid를 기준으로 후보 구간을 줄이는 흐름을 깊이
  잡는 deep_dive다. 분할점 단조 이동, k 후보 범위 줄이기, 구간 분할 DP 가속,
  모든 k 다 보지 않기, 재귀로 탐색 줄이기 같은 자연어 paraphrase가 본 문서의
  divide and conquer DP 최적화에 매핑된다.
---
# Divide and Conquer DP Optimization

> 한 줄 요약: Divide and Conquer DP Optimization은 DP의 최적 분할점이 단조적일 때 탐색 범위를 줄여 계산을 가속하는 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Convex Hull Trick Basics](./convex-hull-trick-basics.md)
> - [Binary Search Patterns](./binary-search-patterns.md)
> - [Topological DP](./topological-dp.md)

> retrieval-anchor-keywords: divide and conquer dp optimization, monotone opt, knuth-like partition, dp speedup, interval dp, opt monotonicity, partition point, dynamic programming optimization

## 핵심 개념

일부 DP는 다음과 같은 형태를 가진다.

- `dp[i] = min(dp[k] + cost(k, i))`

이때 최적 `k`가 i에 따라 단조적으로 이동하면,  
모든 k를 다 보지 않고 탐색 범위를 줄일 수 있다.

## 깊이 들어가기

### 1. 왜 나누어 정복하나

구간의 중간을 먼저 계산하고,  
왼쪽/오른쪽에서 가능한 최적 분할점을 제한한다.

이렇게 하면 전체 계산량이 크게 줄어든다.

### 2. monotone opt

최적 분할점이 `opt[i] <= opt[i+1]` 같은 성질을 가지면 핵심 조건이 맞는 것이다.

이 단조성이 이 최적화의 핵심 전제다.

### 3. backend에서의 감각

구간 비용 최적화, 배치 분할, 클러스터링 비용 최소화 같은 문제에서 활용될 수 있다.

### 4. 언제 유효한가

DP 구조와 cost 함수가 해당 성질을 만족해야 한다.

조건이 없으면 억지로 쓰면 안 된다.

## 실전 시나리오

### 시나리오 1: 구간 분할 비용

연속 구간을 여러 개로 나눠 비용을 최소화할 때 강력하다.

### 시나리오 2: 오판

최적점 단조성이 없는데 쓰면 잘못된 결과가 나올 수 있다.

## 코드로 보기

```java
public class DivideAndConquerDpOptimization {
    public void compute(int l, int r, int optL, int optR) {
        // 설명용 스케치: 실제 구현은 divide and conquer로 opt 범위를 줄인다.
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Divide and Conquer DP | 계산량을 줄일 수 있다 | 단조성 전제가 필요하다 | monotone opt DP |
| Brute Force DP | 단순하다 | 느리다 | 작은 입력 |
| Knuth Optimization | 더 강한 조건에서 더 빠르다 | 조건이 더 엄격하다 | 특정 interval DP |

## 꼬리질문

> Q: 왜 최적점이 단조적이어야 하나?
> 의도: 탐색 범위 축소 근거 이해 확인
> 핵심: 그래야 재귀적으로 후보 범위를 줄일 수 있다.

> Q: 언제 쓰면 안 되나?
> 의도: 전제 조건 검증 습관 확인
> 핵심: 단조성이 보장되지 않을 때다.

> Q: Knuth optimization과 차이는?
> 의도: DP 최적화 계열 구분 확인
> 핵심: Knuth는 더 특정한 조건에 맞는 별도 최적화다.

## 한 줄 정리

Divide and Conquer DP Optimization은 DP의 최적 분할점 단조성을 이용해 후보 범위를 줄이는 가속 기법이다.
