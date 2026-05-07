---
schema_version: 3
title: Coordinate Compression Patterns
concept_id: data-structure/coordinate-compression-patterns
canonical: false
category: data-structure
difficulty: intermediate
doc_role: playbook
level: intermediate
language: ko
source_priority: 83
mission_ids:
- missions/lotto
review_feedback_tags:
- coordinate-compression
- sparse-value-indexing
- range-query-prep
aliases:
- coordinate compression
- value compression
- rank compression
- discrete coordinates
- compressed indexing
- sparse values to array index
- 좌표 압축
symptoms:
- 값 범위가 너무 커서 배열 기반 Fenwick Tree나 Segment Tree를 못 쓰는 상황을 보고도 순서만 보존하면 되는지 판단하지 못한다
- coordinate compression이 값의 실제 거리까지 보존한다고 착각해 gap 크기가 의미 있는 문제에 잘못 적용한다
- sort unique rank 매핑 후에도 range query에서 inclusive boundary와 원래 값 복원이 섞여 off-by-one을 만든다
intents:
- troubleshooting
- design
prerequisites:
- algorithm/time-complexity-intro
next_docs:
- data-structure/fenwick-tree
- data-structure/sparse-table
- algorithm/meet-in-the-middle
linked_paths:
- contents/data-structure/fenwick-tree.md
- contents/data-structure/sparse-table.md
- contents/algorithm/meet-in-the-middle.md
confusable_with:
- data-structure/fenwick-tree
- data-structure/sparse-table
- algorithm/meet-in-the-middle
forbidden_neighbors: []
expected_queries:
- Coordinate compression은 큰 좌표를 어떻게 작은 배열 index로 바꿔?
- 좌표 압축이 순서는 보존하지만 실제 거리 차이는 보존하지 않는다는 뜻은?
- sparse value range에서 Fenwick Tree나 Segment Tree를 쓰려면 어떻게 압축해?
- sort unique rank mapping을 구현할 때 off-by-one을 어떻게 피해야 해?
- 구간 통계 문제에서 coordinate compression을 적용해도 되는 기준은?
contextual_chunk_prefix: |
  이 문서는 큰 정수 좌표나 sparse value space를 sort unique rank로 작은
  index에 매핑해 Fenwick Tree, Segment Tree, sweep line 같은 배열 기반
  구조를 쓰게 하는 coordinate compression playbook이다. 순서 보존과 거리
  비보존, boundary mapping, 복원 오해를 다룬다.
---
# Coordinate Compression Patterns

> 한 줄 요약: Coordinate compression은 큰 값의 상대적 순서만 남겨 인덱스를 줄이고, 배열 기반 자료구조를 적용 가능하게 만든다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: coordinate compression patterns basics, coordinate compression patterns beginner, coordinate compression patterns intro, data structure basics, beginner data structure, 처음 배우는데 coordinate compression patterns, coordinate compression patterns 입문, coordinate compression patterns 기초, what is coordinate compression patterns, how to coordinate compression patterns
> 관련 문서:
> - [Fenwick Tree (Binary Indexed Tree)](./fenwick-tree.md)
> - [Sparse Table](./sparse-table.md)
> - [Meet-in-the-Middle](../algorithm/meet-in-the-middle.md)

> retrieval-anchor-keywords: coordinate compression, value compression, rank compression, discrete coordinates, compressed indexing, sparse values, segment tree indexing, fenwick indexing, range mapping

## 핵심 개념

Coordinate compression은 값의 절대 크기는 버리고 순서만 보존해 작은 정수로 바꾸는 기법이다.

예:

- `100, 1000, 500000` -> `1, 2, 3`

이렇게 바꾸면 큰 좌표도 작은 배열 인덱스로 다룰 수 있다.

## 깊이 들어가기

### 1. 왜 필요한가

좌표가 너무 크면 배열을 바로 못 쓴다.

- 위치 기반 이벤트
- 시간 축 데이터
- 희소한 키 공간

이럴 때 compression으로 인덱스를 줄인다.

### 2. 순서가 중요한 이유

압축 후에도 대소 관계가 유지되어야 한다.

그래서 sort 후 unique를 취해 rank를 부여한다.

### 3. backend에서의 감각

좌표 압축은 로그/이벤트/트래픽에서 자주 나온다.

- 시간순 이벤트 인덱싱
- 희소한 ID를 배열로 옮기기
- range query 준비

### 4. 어떤 구조와 자주 결합하나

압축된 인덱스는 segment tree, Fenwick tree, sweep line과 잘 맞는다.

## 실전 시나리오

### 시나리오 1: 큰 범위의 점 갱신

실제 값이 매우 커도 압축 후 배열로 관리할 수 있다.

### 시나리오 2: 구간 통계

희소 좌표에서 빈도 집계할 때 유용하다.

### 시나리오 3: 오판

정확한 원래 값이 필요한 경우에는 압축만으로는 부족하다.
매핑 테이블을 같이 유지해야 한다.

## 코드로 보기

```java
import java.util.*;

public class CoordinateCompression {
    public int[] compress(int[] values) {
        int[] sorted = Arrays.stream(values).distinct().sorted().toArray();
        Map<Integer, Integer> rank = new HashMap<>();
        for (int i = 0; i < sorted.length; i++) {
            rank.put(sorted[i], i);
        }
        int[] result = new int[values.length];
        for (int i = 0; i < values.length; i++) {
            result[i] = rank.get(values[i]);
        }
        return result;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Coordinate Compression | 큰 값 공간을 작은 인덱스로 바꾼다 | 원래 값 복원이 필요하다 | sparse coordinates |
| HashMap 인덱스 | 바로 매핑할 수 있다 | 순서 정보가 약하다 | key lookup |
| 직접 배열 | 단순하다 | 값 범위가 크면 불가능 | 작은 범위 |

## 꼬리질문

> Q: 왜 sort + unique가 필요한가?
> 의도: rank 부여 원리를 아는지 확인
> 핵심: 순서를 보존하며 중복을 제거하기 위해서다.

> Q: 무엇과 자주 결합하나?
> 의도: 실전 자료구조 결합 이해 확인
> 핵심: Fenwick, segment tree, sweep line이다.

> Q: 원래 값이 꼭 필요한가?
> 의도: 매핑 보존 개념 확인
> 핵심: 역매핑이 필요하면 배열로 저장해야 한다.

## 한 줄 정리

Coordinate compression은 희소하고 큰 값을 순위 인덱스로 바꿔 배열 기반 자료구조를 적용 가능하게 만드는 패턴이다.
