---
schema_version: 3
title: Digit DP Patterns
concept_id: algorithm/digit-dp-patterns
canonical: true
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- digit-dp
- tight-state
- range-counting
aliases:
- digit dp
- digit dynamic programming
- tight state
- number counting dp
- bounded number counting
- prefix constraint dp
- leading zero digit dp
- digit mask dp
- 자릿수 dp
- 숫자 범위 카운팅
symptoms:
- 숫자 범위가 커서 완전탐색이 불가능한데도 모든 수를 순회하려고 한다
- tight 상태가 상한과 같은 접두사인지 이미 작아진 접두사인지 구분하지 못한다
- leading zero 처리와 실제 숫자 시작 여부를 같은 상태로 뭉개서 중복 카운트한다
intents:
- deep_dive
- troubleshooting
- design
prerequisites:
- algorithm/dp-intro
- algorithm/bitmask-dp
- algorithm/backtracking-intro
next_docs:
- algorithm/meet-in-the-middle
- algorithm/knuth-optimization-intuition
- algorithm/topological-dp
linked_paths:
- contents/algorithm/dp-intro.md
- contents/algorithm/bitmask-dp.md
- contents/algorithm/backtracking-intro.md
- contents/algorithm/meet-in-the-middle.md
confusable_with:
- algorithm/backtracking-intro
- algorithm/bitmask-dp
- algorithm/meet-in-the-middle
- algorithm/binary-search-patterns
forbidden_neighbors: []
expected_queries:
- Digit DP에서 tight 상태는 상한과 같은 접두사인지 어떻게 표현해?
- 큰 숫자 범위에서 조건을 만족하는 수의 개수를 완전탐색 없이 세려면 어떻게 해?
- leading zero와 started 상태를 분리하지 않으면 digit DP에서 왜 중복 카운트가 생겨?
- 숫자 합이나 특정 digit 포함 여부를 digit DP 상태에 어떻게 넣어?
- count(upper) - count(lower - 1)로 구간 카운트를 만드는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 algorithm 카테고리에서 Digit DP Patterns를 다루는 deep_dive 문서다. digit dp, digit dynamic programming, tight state, number counting dp, bounded number counting 같은 lexical 표현과 Digit DP에서 tight 상태는 상한과 같은 접두사인지 어떻게 표현해?, 큰 숫자 범위에서 조건을 만족하는 수의 개수를 완전탐색 없이 세려면 어떻게 해? 같은 자연어 질문을 같은 개념으로 묶어, 학습자가 증상, 비교, 설계 판단, 코드리뷰 맥락 중 어디에서 들어오더라도 본문의 핵심 분기와 다음 문서로 안정적으로 이어지게 한다.
---
# Digit DP Patterns

> 한 줄 요약: Digit DP는 자릿수 제약을 상태로 들고 가며, 특정 숫자 조건을 만족하는 개수를 세는 패턴이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [알고리즘 기본](./basic.md)
> - [Binary Search Patterns](./binary-search-patterns.md)
> - [Meet-in-the-Middle](./meet-in-the-middle.md)

> retrieval-anchor-keywords: digit dp, digit dynamic programming, tight state, number counting, bounded numbers, prefix constraint, combinatorial count, numeric DP, digit mask, leading zero

## 핵심 개념

Digit DP는 숫자를 자릿수 단위로 쪼개서 조건을 만족하는 경우의 수를 센다.

핵심 상태는 보통 다음을 포함한다.

- 현재 자리
- tight 여부
- 누적 상태

`tight`는 지금까지 만든 접두사가 상한과 정확히 같은지 나타낸다.

## 깊이 들어가기

### 1. 왜 자릿수로 나누나

숫자 범위가 너무 커서 일일이 세기 어렵다.

자릿수별로 보면 앞자리 제약을 하나씩 풀어갈 수 있다.

### 2. tight 상태

상한보다 아직 접두사가 같다면 다음 자리 선택에 제약이 있다.

상한보다 이미 작아졌다면 남은 자리는 자유롭다.

이 두 상태가 digit DP의 핵심이다.

### 3. backend에서의 감각

숫자 규칙 검증이나 범위 내 조건 개수 계산에 유용하다.

- 번호 정책
- 제한 조건 카운트
- 범위 내 패턴 수

### 4. 흔한 확장

- 숫자 합
- 특정 digit 포함 여부
- 연속 digit 제약
- 자리별 mask

## 실전 시나리오

### 시나리오 1: 제한 조건 카운트

어떤 범위 내에서 특정 규칙을 만족하는 숫자 개수를 세는 문제.

### 시나리오 2: 오판

범위가 크다고 무조건 완전탐색하면 안 된다.

### 시나리오 3: 상한/하한

두 개의 숫자 범위 사이를 세려면 상한용 함수를 만들어 차이를 구할 수 있다.

## 코드로 보기

```java
public class DigitDpPatterns {
    public long count(long n) {
        // 설명용 스케치: 실제 구현은 자리/ tight / 누적 상태를 가진다.
        return 0;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Digit DP | 큰 범위를 효율적으로 센다 | 상태 설계가 까다롭다 | 숫자 범위 카운트 |
| Brute Force | 직관적이다 | 범위가 크면 불가능하다 | 작은 입력 |
| Math Formula | 빠를 수 있다 | 조건이 맞아야 한다 | 규칙이 단순할 때 |

## 꼬리질문

> Q: tight는 왜 중요한가?
> 의도: 상한 제약 상태를 이해하는지 확인
> 핵심: 상한과 같은 접두사인지 여부를 나타내기 때문이다.

> Q: 왜 숫자를 자리별로 보나?
> 의도: 범위 제약 분해 이해 확인
> 핵심: 큰 숫자 범위를 작은 선택으로 나누기 위해서다.

> Q: 어디에 자주 쓰이나?
> 의도: 규칙 기반 카운팅 감각 확인
> 핵심: 제한 조건 숫자 세기다.

## 한 줄 정리

Digit DP는 자릿수와 tight 상태를 이용해 큰 숫자 범위에서 조건 만족 개수를 세는 패턴이다.
