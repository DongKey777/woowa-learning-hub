---
schema_version: 3
title: Wavelet Tree Intuition
concept_id: data-structure/wavelet-tree
canonical: false
category: data-structure
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 83
mission_ids:
- missions/lotto
review_feedback_tags:
- wavelet-tree
- static-range-rank
- kth-range-query
aliases:
- Wavelet Tree
- wavelet tree intuition
- range kth query
- range frequency query
- static order statistics
- compressed sequence rank
- value partition tree
symptoms:
- range kth, range count, frequency query를 모두 segment tree 집계 문제로만 보고 값 기준 recursive partition을 떠올리지 못한다
- Wavelet Tree가 index position 기준이 아니라 value range 기준으로 나누며 bitvector rank를 써서 구간을 내려간다는 점을 놓친다
- 업데이트가 잦은 동적 ordered set 문제에 정적 Wavelet Tree를 적용하려 해 재구성 비용을 과소평가한다
intents:
- definition
- comparison
prerequisites:
- data-structure/coordinate-compression-patterns
- data-structure/succinct-bitvector-rank-select
next_docs:
- data-structure/order-statistic-tree
- data-structure/sparse-table
- data-structure/succinct-bitvector-rank-select
linked_paths:
- contents/data-structure/coordinate-compression-patterns.md
- contents/data-structure/order-statistic-tree.md
- contents/data-structure/sparse-table.md
- contents/data-structure/succinct-bitvector-rank-select.md
confusable_with:
- data-structure/order-statistic-tree
- data-structure/sparse-table
- data-structure/segment-tree-lazy-propagation
- data-structure/succinct-bitvector-rank-select
forbidden_neighbors: []
expected_queries:
- Wavelet Tree는 value range를 나눠서 range kth query를 어떻게 처리해?
- 구간 내 k번째 값과 특정 값 이하 개수를 빠르게 묻는 정적 구조는?
- Wavelet Tree와 Order Statistic Tree는 정적 데이터와 동적 삽입 삭제 관점에서 어떻게 달라?
- Wavelet Tree에서 bitvector rank가 각 레벨의 구간 이동에 왜 필요해?
- range frequency query를 segment tree가 아니라 wavelet tree로 보는 경우는 언제야?
contextual_chunk_prefix: |
  이 문서는 Wavelet Tree를 value range partition과 bitvector rank를 이용해
  static array의 range kth, range count, frequency query를 처리하는 compressed
  sequence structure로 설명한다. Order Statistic Tree, Sparse Table과 비교한다.
---
# Wavelet Tree Intuition

> 한 줄 요약: Wavelet Tree는 값의 범위를 기준으로 배열을 분할해 rank, kth, range count 같은 질의를 빠르게 하는 압축형 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Coordinate Compression Patterns](./coordinate-compression-patterns.md)
> - [Order Statistic Tree](./order-statistic-tree.md)
> - [Sparse Table](./sparse-table.md)

> retrieval-anchor-keywords: wavelet tree, rank query, kth query, range frequency, compressed sequence, value partition, range count, order statistics, static array, implicit tree

## 핵심 개념

Wavelet Tree는 배열을 값의 중간 기준으로 반씩 나누며,  
각 구간에서 왼쪽/오른쪽으로 몇 개가 갔는지 저장한다.

이 구조를 쓰면 다음 질의를 빠르게 할 수 있다.

- 구간 내 k번째 값
- 특정 값 이하의 개수
- 구간 빈도 수

## 깊이 들어가기

### 1. 왜 값 기준 분할인가

인덱스 기준이 아니라 값 기준으로 나누면,  
정렬된 순서와 rank 정보를 동시에 활용할 수 있다.

### 2. bitvector 감각

각 레벨에서 원소가 왼쪽으로 갔는지 오른쪽으로 갔는지를 bit처럼 기록한다.

이 누적 정보 덕분에 구간 질의가 빠르게 내려간다.

### 3. backend에서의 감각

값 분포 분석이나 순위 질의가 필요한 정적 데이터에 적합하다.

- 로그 점수 분포
- 통계 리포트
- 정적 순위 인덱스

### 4. 제약

데이터가 정적일 때 가장 빛난다.
업데이트가 많으면 다른 구조가 더 적합하다.

## 실전 시나리오

### 시나리오 1: 구간 k번째 수

정적 배열에서 k번째 값을 자주 물으면 wavelet tree가 강하다.

### 시나리오 2: 구간 frequency

특정 값 이하 또는 특정 구간 범위의 개수를 세기에 좋다.

### 시나리오 3: 오판

빈번한 업데이트가 필요하면 wavelet tree는 부담이 크다.

## 코드로 보기

```java
public class WaveletTreeNotes {
    // 설명용 노트: 실제 구현은 value range split과 prefix rank 구조가 필요하다.
    public int kth(int l, int r, int k) {
        return 0;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Wavelet Tree | rank/kth/range count가 강하다 | 구현이 복잡하다 | 정적 순위 질의 |
| Order Statistic Tree | 동적 삽입/삭제가 쉽다 | range frequency가 약할 수 있다 | 동적 ordered set |
| Segment Tree | 범용적이다 | 순위 질의는 직접적이지 않다 | 값 집계 |

## 꼬리질문

> Q: wavelet tree가 왜 값 기준으로 나누나?
> 의도: 값 분포와 순위 질의의 관계 확인
> 핵심: rank/kth 질의를 값 범위 분할로 푸는 구조이기 때문이다.

> Q: 어디에 특히 잘 맞나?
> 의도: 정적 데이터셋 인식 확인
> 핵심: 업데이트 없는 순위/빈도 질의다.

> Q: order statistic tree와 차이는?
> 의도: 동적 vs 정적 구조 차이 이해 확인
> 핵심: wavelet tree는 정적, OST는 동적에 강하다.

## 한 줄 정리

Wavelet Tree는 값 범위를 재귀적으로 분할해 구간 k번째와 빈도 질의를 빠르게 하는 정적 순위 구조다.
