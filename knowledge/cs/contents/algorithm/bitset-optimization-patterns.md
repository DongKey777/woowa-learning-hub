---
schema_version: 3
title: Bitset Optimization Patterns
concept_id: algorithm/bitset-optimization-patterns
canonical: true
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- bitset-optimization
- word-level-parallelism
- dense-boolean-state
aliases:
- bitset optimization patterns
- bitwise dp
- vectorized set operations
- shift and or
- word level parallelism
- boolean dp bitset
- dense set operations
- subset sum bitset
- 비트셋 최적화
symptoms:
- boolean[] 상태를 그대로 순회하며 dense한 상태 공간에서 word-level parallelism 이점을 놓친다
- bitset shift-or 전이를 단순 비트 트릭으로만 보고 subset sum 같은 DP 전이 최적화를 연결하지 못한다
- sparse 상태에도 무조건 bitset을 펼쳐 메모리 낭비와 scan 비용을 만든다
intents:
- deep_dive
- comparison
- design
prerequisites:
- algorithm/bitmask-dp
- algorithm/basic
next_docs:
- data-structure/count-min-sketch
- algorithm/monotone-queue-dp
- algorithm/amortized-analysis-pitfalls
linked_paths:
- contents/algorithm/bitmask-dp.md
- contents/data-structure/count-min-sketch.md
- contents/algorithm/basic.md
confusable_with:
- algorithm/bitmask-dp
- data-structure/count-min-sketch
- algorithm/amortized-analysis-pitfalls
- data-structure/bitset-vs-roaring-bitmap-handoff
forbidden_neighbors: []
expected_queries:
- Bitset optimization은 boolean DP 상태를 word 단위 병렬 연산으로 어떻게 빠르게 해?
- subset sum에서 bitset shift와 OR로 가능한 합을 갱신하는 직관을 알려줘
- dense 상태와 sparse 상태에서 bitset 선택 기준은 어떻게 달라?
- bitmask DP와 bitset optimization은 상태 표현과 전이 최적화 관점에서 무엇이 달라?
- 권한 flag나 feature flag 집합처럼 dense boolean 상태를 bitset으로 다루는 장단점은 뭐야?
contextual_chunk_prefix: |
  이 문서는 Bitset Optimization advanced deep dive로, dense boolean state를
  bitset으로 압축해 word-level parallelism, shift/or transition, set
  intersection/union, subset sum DP를 빠르게 처리하는 패턴을 설명한다.
---
# Bitset Optimization Patterns

> 한 줄 요약: Bitset optimization은 비트 연산과 벡터화 감각을 이용해 집합 DP, 전이, 포함 검사를 빠르게 만드는 패턴이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Bitmask DP](./bitmask-dp.md)
> - [Approximate / Streaming Sketches](../data-structure/count-min-sketch.md)
> - [알고리즘 기본](./basic.md)

> retrieval-anchor-keywords: bitset optimization, bitwise dp, vectorized set operations, subset convolution intuition, shift and or, fast intersection, boolean dp, word-level parallelism, dense set operations

## 핵심 개념

Bitset optimization은 `boolean[]`처럼 보이는 상태를 비트 단위로 압축해,  
한 번의 CPU word 연산으로 많은 상태를 같이 처리하는 패턴이다.

주로 다음에서 유용하다.

- 부분집합 전이
- 도달 가능 상태
- 문자열 포함 검사
- 집합 교집합/합집합

## 깊이 들어가기

### 1. 왜 빠른가

비트 연산은 한 번에 64개 정도의 상태를 같이 다룰 수 있다.

즉 같은 논리를 더 작은 메모리와 더 적은 연산으로 수행한다.

### 2. shift와 or

집합 전이에서 `bitset << k`는 특정 차이만큼 이동하는 효과가 있다.

예:

- subset sum
- 도달 가능한 합 계산
- 문자열 위치 이동

### 3. backend에서의 감각

bitset은 dense한 true/false 상태를 관리할 때 강하다.

- 권한 플래그
- feature flag 집합
- 작은 상태 공간의 전이

### 4. 주의점

상태가 너무 크거나 sparse하면 bitset이 오히려 비효율적일 수 있다.

## 실전 시나리오

### 시나리오 1: subset sum 빠르게 갱신

가능한 합의 집합을 비트로 표현해 전이를 빠르게 할 수 있다.

### 시나리오 2: 문자열 후보 필터

여러 위치의 가능성을 비트로 다뤄서 빠르게 포함 여부를 계산할 수 있다.

### 시나리오 3: 오판

비트셋이 항상 빠른 건 아니다.  
희소한 상태를 억지로 비트로 펼치면 메모리가 낭비된다.

## 코드로 보기

```java
import java.util.BitSet;

public class BitsetOptimization {
    public BitSet shiftLeft(BitSet bits, int shift, int size) {
        BitSet result = new BitSet(size);
        for (int i = bits.nextSetBit(0); i >= 0; i = bits.nextSetBit(i + 1)) {
            if (i + shift < size) result.set(i + shift);
        }
        return result;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Bitset | word-level parallelism이 좋다 | sparse 상태에 비효율적이다 | dense boolean state |
| Array DP | 명확하고 직관적이다 | 느릴 수 있다 | 작은 입력 |
| Hash-based state | 희소 상태에 유리하다 | 비트셋보다 느릴 수 있다 | sparse DP |

## 꼬리질문

> Q: bitset이 왜 빠른가?
> 의도: CPU word parallelism을 이해하는지 확인
> 핵심: 한 번의 연산으로 여러 상태를 같이 처리하기 때문이다.

> Q: 언제 비효율적인가?
> 의도: dense/sparse 구분을 아는지 확인
> 핵심: 상태가 희소하고 범위가 크면 낭비가 크다.

> Q: bitmask DP와 차이는?
> 의도: 상태 압축과 연산 가속을 구분하는지 확인
> 핵심: bitmask DP는 상태 표현, bitset optimization은 연산 가속이다.

## 한 줄 정리

Bitset optimization은 비트 단위 병렬성을 이용해 dense한 boolean 상태 전이와 포함 검사를 빠르게 만드는 패턴이다.
