---
schema_version: 3
title: Dancing Links / DLX Basics
concept_id: algorithm/dancing-links-dlx
canonical: true
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- dancing-links
- exact-cover
- reversible-backtracking
aliases:
- dancing links
- DLX
- algorithm x
- exact cover
- cover uncover
- sudoku exact cover
- reversible linked list backtracking
- 포인터 복구 백트래킹
- 정확한 덮개
symptoms:
- 스도쿠나 exact cover 문제를 단순 백트래킹으로만 풀어 매번 후보 구조를 복사한다
- cover와 uncover 순서를 반대로 복구하지 않아 포인터 구조가 깨진다
- exact cover 모델링과 일반 constraint satisfaction 문제를 구분하지 못한다
intents:
- deep_dive
- troubleshooting
- design
prerequisites:
- algorithm/backtracking-intro
- data-structure/linked-list-basics
- algorithm/basic
next_docs:
- algorithm/meet-in-the-middle
- algorithm/dsu-rollback
- algorithm/branch-and-bound-primer
linked_paths:
- contents/algorithm/backtracking-intro.md
- contents/algorithm/meet-in-the-middle.md
- contents/data-structure/linked-list-basics.md
- contents/algorithm/basic.md
confusable_with:
- algorithm/backtracking-intro
- algorithm/meet-in-the-middle
- algorithm/dsu-rollback
- data-structure/linked-list-basics
forbidden_neighbors: []
expected_queries:
- Dancing Links는 exact cover 백트래킹에서 cover와 uncover를 어떻게 빠르게 해?
- DLX에서 포인터를 지웠다가 복구하는 순서가 왜 중요해?
- 스도쿠를 exact cover matrix로 바꾸면 Algorithm X가 어떻게 동작해?
- 일반 백트래킹과 DLX는 후보 제거와 복구 비용에서 어떻게 달라?
- exact cover 문제인지 아닌지 어떻게 판단해?
contextual_chunk_prefix: |
  이 문서는 Dancing Links / DLX deep dive로, exact cover 문제를 matrix로
  모델링하고 cover/uncover 포인터 조작을 통해 백트래킹 복구 비용을 줄이는
  Algorithm X 구현 감각을 설명한다.
---
# Dancing Links / DLX Basics

> 한 줄 요약: Dancing Links(DLX)는 정확한 덮개(Exact Cover) 문제를 빠르게 되돌리기 위해 연결 리스트 포인터를 지웠다가 복구하는 백트래킹 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Meet-in-the-Middle](./meet-in-the-middle.md)
> - [Backtracking](./basic.md)
> - [탐욕 / Greedy 알고리즘 개요](./greedy.md)

> retrieval-anchor-keywords: dancing links, DLX, exact cover, algorithm x, backtracking, cover uncover, linked structure, sudoku exact cover, constraint search, reversible removal

## 핵심 개념

DLX는 Donald Knuth의 Algorithm X를 구현하는 대표적 자료구조 기법이다.

- 문제를 exact cover matrix로 바꾼다.
- 선택한 행과 충돌하는 열/행을 빠르게 제거한다.
- 백트래킹 시 포인터를 복구한다.

핵심은 "지운 것을 다시 살리는" 복구 비용을 최소화하는 것이다.

## 깊이 들어가기

### 1. exact cover란

모든 제약을 정확히 한 번씩 만족해야 하는 문제다.

대표 예:

- 스도쿠
- 퍼즐 배치
- 조합 제약 충족

### 2. cover/uncover

DLX는 행과 열을 제거할 때 단순 배열 복사 대신 연결 리스트 포인터를 끊고 다시 연결한다.

이렇게 하면 백트래킹이 매우 빠르다.

### 3. backend에서의 감각

실무에서는 직접 exact cover를 쓰기보다,  
강한 제약 탐색이나 퍼즐형 스케줄링에서 이 아이디어를 떠올리는 경우가 많다.

### 4. 왜 어려운가

문제를 matrix로 바꾸는 modeling이 먼저고,  
그다음 포인터 기반 undo/redo 구조를 이해해야 한다.

## 실전 시나리오

### 시나리오 1: 스도쿠

숫자 배치를 exact cover로 바꾸면 DLX가 강력하다.

### 시나리오 2: 제약 조합 탐색

서로 충돌하는 선택지를 빠르게 제거해야 할 때 쓰인다.

### 시나리오 3: 오판

제약이 약한 일반 문제에는 과한 도구다.

## 코드로 보기

```java
public class DLXNotes {
    // 설명용 노트: 실제 DLX는 cover/uncover 포인터 조작이 핵심이다.
    public boolean search() {
        return false;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| DLX | exact cover 백트래킹이 빠르다 | 모델링과 구현이 어렵다 | 강한 제약 탐색 |
| 일반 백트래킹 | 이해가 쉽다 | 가지치기가 약하다 | 작은 문제 |
| DP | 상태가 명확하면 좋다 | exact cover에 바로 안 맞을 수 있다 | 상태 재사용 가능할 때 |

## 꼬리질문

> Q: DLX는 무엇을 빠르게 하려는가?
> 의도: 포인터 기반 복구의 의미 확인
> 핵심: cover/uncover 백트래킹이다.

> Q: exact cover는 어떤 문제인가?
> 의도: 문제 모델링 감각 확인
> 핵심: 제약을 정확히 한 번씩 만족해야 하는 문제다.

> Q: 왜 matrix로 바꾸나?
> 의도: 알고리즘 X의 전제 이해 확인
> 핵심: 행과 열 제약을 구조적으로 다루기 위해서다.

## 한 줄 정리

DLX는 exact cover를 풀기 위해 제약을 포인터로 지웠다가 빠르게 복구하는 백트래킹 자료구조 기법이다.
