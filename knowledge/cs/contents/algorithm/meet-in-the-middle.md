---
schema_version: 3
title: Meet-in-the-Middle
concept_id: algorithm/meet-in-the-middle
canonical: true
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- meet-in-the-middle
- subset-split-search
- exponential-state-reduction
aliases:
- meet in the middle
- MITM algorithm
- subset split
- half enumeration
- subset sum meet in the middle
- exponential optimization
- split search
- state space reduction
- 중간에서 만나기
symptoms:
- n이 30에서 40 정도인 subset search를 2^n 완전 탐색으로 바로 처리하려 한다
- 상태 공간을 반으로 나눈 뒤 정렬 이진 탐색이나 해시로 결합하는 전략을 떠올리지 못한다
- DP 상태를 만들기 어렵다는 이유만으로 조합 폭발을 그대로 감수한다
intents:
- deep_dive
- comparison
- design
prerequisites:
- algorithm/brute-force-intro
- algorithm/bitmask-dp
next_docs:
- algorithm/binary-search-patterns
- algorithm/bitmask-dp
- algorithm/dp-intro
linked_paths:
- contents/algorithm/bitmask-dp.md
- contents/algorithm/binary-search-patterns.md
- contents/algorithm/basic.md
confusable_with:
- algorithm/bitmask-dp
- algorithm/brute-force-intro
- algorithm/binary-search-patterns
- algorithm/dp-intro
forbidden_neighbors: []
expected_queries:
- Meet-in-the-Middle은 2^n 탐색을 왜 2^(n/2) 두 묶음으로 줄여?
- subset sum에서 왼쪽 절반 합과 오른쪽 절반 합을 어떻게 결합해?
- n이 30에서 40인 조합 탐색에서 brute force와 DP 사이에 MITM을 보는 기준이 뭐야?
- 반으로 나눈 결과를 정렬해서 binary search로 목표를 찾는 패턴을 설명해줘
- Meet-in-the-Middle도 여전히 메모리와 정렬 비용이 있다는 tradeoff는 뭐야?
contextual_chunk_prefix: |
  이 문서는 Meet-in-the-Middle advanced deep dive로, subset sum과 조합 탐색에서
  상태 공간을 왼쪽/오른쪽 절반으로 나눠 각각 가능한 값을 만들고 hash 또는
  binary search로 결합해 exponential search를 줄이는 기법을 설명한다.
---
# Meet-in-the-Middle

> 한 줄 요약: Meet-in-the-Middle은 상태 공간을 반으로 나눠 각 절반을 계산한 뒤, 결과를 합쳐 조합 폭발을 줄이는 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Bitmask DP](./bitmask-dp.md)
> - [Binary Search Patterns](./binary-search-patterns.md)
> - [알고리즘 기본](./basic.md)

> retrieval-anchor-keywords: meet in the middle, subset split, exponential optimization, half enumeration, hash combine, subset sum, combinatorial search, split search, state space reduction

## 핵심 개념

Meet-in-the-Middle(MITM)은 원래 `2^n`짜리 탐색을 `2^(n/2)` 두 번으로 쪼개는 방식이다.

대표적으로:

- subset sum
- 조합 최적화
- 작은 n에서의 brute force 개선

## 깊이 들어가기

### 1. 왜 반으로 나누나

조합 수는 지수적으로 늘어난다.

하지만 절반씩 나누면 각 절반은 훨씬 작아지고,  
합치는 단계에서 이진 탐색이나 해시를 쓸 수 있다.

### 2. 대표 패턴

왼쪽 절반의 가능한 합을 모두 구하고, 오른쪽 절반의 가능한 합을 구한 뒤,  
두 결과를 결합해 목표를 찾는다.

### 3. backend에서의 감각

MITM은 보안/스케줄링/옵션 조합처럼 상태 수가 작지만 조합 폭발이 있는 문제에 맞는다.

### 4. 왜 강력한가

완전탐색보다 훨씬 작고, DP가 어려운 경우에도 잘 먹힌다.

## 실전 시나리오

### 시나리오 1: subset sum

숫자 수가 30~40 정도일 때 완전탐색 대신 MITM이 강하다.

### 시나리오 2: 조합 검색

특정 조건을 만족하는 두 그룹 조합을 찾는 데 유용하다.

### 시나리오 3: 오판

문제가 크다고 무조건 MITM이 되는 건 아니다.  
반으로 나눴을 때도 여전히 너무 크면 다른 방법이 필요하다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class MeetInTheMiddle {
    public List<Long> subsetSums(long[] arr, int l, int r) {
        List<Long> sums = new ArrayList<>();
        int n = r - l;
        for (int mask = 0; mask < (1 << n); mask++) {
            long sum = 0;
            for (int i = 0; i < n; i++) {
                if ((mask & (1 << i)) != 0) sum += arr[l + i];
            }
            sums.add(sum);
        }
        return sums;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Meet-in-the-Middle | 지수 폭발을 줄인다 | 여전히 메모리/정렬 비용이 있다 | n이 중간 크기일 때 |
| DP | 안정적이다 | 상태가 커질 수 있다 | 제약이 단순할 때 |
| Brute Force | 단순하다 | 너무 느리다 | 데이터가 매우 작을 때 |

## 꼬리질문

> Q: 왜 절반으로 나누나?
> 의도: 지수 복잡도 완화 개념 이해 확인
> 핵심: 각 절반의 탐색 공간을 줄이기 위해서다.

> Q: 어디서 결합하나?
> 의도: 합치기 단계의 존재를 아는지 확인
> 핵심: 한쪽 결과를 정렬/해시해 다른 쪽과 맞춘다.

> Q: DP와 무엇이 다른가?
> 의도: 상태 공간 축소 방식 이해 확인
> 핵심: DP는 상태 저장, MITM은 분할 탐색이다.

## 한 줄 정리

Meet-in-the-Middle은 지수 탐색을 반으로 나눠 계산하고 결합해 조합 폭발을 줄이는 기법이다.
