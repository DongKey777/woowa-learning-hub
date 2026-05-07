---
schema_version: 3
title: Bit-Sliced Bitmap Index
concept_id: data-structure/bit-sliced-bitmap-index
canonical: false
category: data-structure
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 83
mission_ids: []
review_feedback_tags:
- bitmap-index-bsi
- range-filter-bit-slice
- warehouse-index-compression
aliases:
- bit sliced bitmap index
- BSI bitmap index
- bit slice index
- bitmap range filter
- bitwise aggregation
- columnar bitmap index
- numeric bitmap slice
symptoms:
- 숫자 컬럼의 range predicate를 값별 bitmap이나 HashMap exact lookup처럼만 보고 bit slice 방식의 장점을 놓친다
- high-cardinality numeric value마다 bitmap을 만들려 해 bitmap 수가 폭증한다
- BSI를 OLTP point lookup 인덱스로 오해하고 row ordering과 compression 조건을 같이 보지 않는다
intents:
- deep_dive
- design
prerequisites:
- data-structure/roaring-bitmap
- data-structure/plain-bitset-vs-compressed-bitmap-decision-card
next_docs:
- data-structure/bit-sliced-bitmap-sort-key-sensitivity
- data-structure/row-ordering-and-bitmap-compression-playbook
- data-structure/warehouse-sort-key-co-design-for-bitmap-indexes
- data-structure/elias-fano-encoded-posting-list
linked_paths:
- contents/data-structure/roaring-bitmap.md
- contents/data-structure/row-ordering-and-bitmap-compression-playbook.md
- contents/data-structure/bit-sliced-bitmap-sort-key-sensitivity.md
- contents/data-structure/warehouse-sort-key-co-design-for-bitmap-indexes.md
- contents/data-structure/roaring-run-formation-and-row-ordering.md
- contents/data-structure/elias-fano-encoded-posting-list.md
- contents/data-structure/hashmap-internals.md
- contents/data-structure/adaptive-radix-tree.md
confusable_with:
- data-structure/roaring-bitmap
- data-structure/plain-bitset-vs-compressed-bitmap-decision-card
- data-structure/elias-fano-encoded-posting-list
- data-structure/hashmap-internals
forbidden_neighbors: []
expected_queries:
- Bit-Sliced Bitmap Index는 숫자 range filter를 어떻게 bitmap으로 처리해?
- 값별 bitmap과 bit slice bitmap index는 무엇이 달라?
- high-cardinality numeric column에서 bitmap index를 어떻게 설계해야 해?
- BSI가 range query와 aggregation에 유리한 이유를 설명해줘
- BSI를 HashMap이나 posting list와 비교하면 어떤 요구에 맞아?
contextual_chunk_prefix: |
  이 문서는 numeric column을 bit position별 bitmap slice로 나누어 range
  filter와 aggregation을 비트 연산으로 처리하는 Bit-Sliced Bitmap Index
  playbook이다. 값별 bitmap 폭증, high-cardinality numeric value, row
  ordering, compressed bitmap, warehouse analytic query 맥락을 다룬다.
---
# Bit-Sliced Bitmap Index

> 한 줄 요약: Bit-Sliced Bitmap Index는 숫자 값을 비트 단위 bitmap slice로 분해해 저장함으로써, exact value lookup뿐 아니라 range filter와 집계를 비트 연산으로 빠르게 처리하려는 인덱스 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap](./roaring-bitmap.md)
> - [Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)
> - [Bit-Sliced Bitmap Sort-Key Sensitivity](./bit-sliced-bitmap-sort-key-sensitivity.md)
> - [Warehouse Sort-Key Co-Design for Bitmap Indexes](./warehouse-sort-key-co-design-for-bitmap-indexes.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Elias-Fano Encoded Posting List](./elias-fano-encoded-posting-list.md)
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [Adaptive Radix Tree](./adaptive-radix-tree.md)

> retrieval-anchor-keywords: bit sliced bitmap index, bitmap index, bit slice, bitwise aggregation, posting list, columnar index, range filter, compressed bitmap, analytic query, segment filtering, bitmap sort order, row group compression, warehouse bitmap slice, bsi sort key sensitivity, bit slice prefix locality, upper slice run length, segment boundary bit slice, roaring locality bit slice

## 핵심 개념

숫자 컬럼을 exact key-value map으로만 보면 `price = 1000` 조회는 쉽다.  
하지만 `price >= 1000 AND price < 5000` 같은 조건을 대량 row에 반복 적용하면 이야기가 달라진다.

Bit-Sliced Bitmap Index(BSI)는 값을 비트 단위로 쪼개 bitmap으로 저장한다.

- row 하나당 값 하나를 그대로 두지 않는다
- 값의 각 bit position마다 "이 비트가 1인 row 집합"을 저장한다
- 질의는 bitmap AND/OR/XOR 조합으로 계산한다

즉 레코드 단위 접근보다 **컬럼 단위 비트 연산**을 우선하는 인덱스 구조다.

## 깊이 들어가기

### 1. 일반 bitmap index와 무엇이 다른가

기본 bitmap index는 보통 "값별 bitmap"을 둔다.

- `status = ACTIVE` bitmap
- `status = BLOCKED` bitmap

카디널리티가 낮은 enum에는 아주 잘 맞는다.  
하지만 숫자 범위가 넓으면 값별 bitmap 수가 급격히 늘어난다.

Bit-sliced index는 값 하나마다 bitmap을 만드는 대신  
값을 이진수 자리수로 분해해 slice 수를 고정한다.

예:

- 8비트 값이면 slice 8개
- 각 slice는 해당 bit가 1인 row id 집합

### 2. 왜 range query가 가능한가

값 비교를 bit-level 연산으로 바꿀 수 있기 때문이다.

예를 들어 `value >= threshold`는 상위 비트부터 비교하며:

- 이미 큰 것이 확정된 row 집합
- 아직 동일 prefix인 후보 집합

을 bitmap으로 유지하면서 내려갈 수 있다.

즉 row마다 값을 하나씩 다시 읽지 않고,  
slice bitmap만 조합해 후보군을 줄인다.

### 3. 집계에도 쓸 수 있다

BSI는 필터만이 아니라 일부 집계에도 유용하다.

- 조건을 만족하는 row count
- 가중치 합산
- score thresholding

왜냐하면 각 bit slice가 "이 자릿값이 있는 row들"을 뜻하므로,  
bitmap cardinality와 bit weight를 이용해 합계를 계산할 수 있기 때문이다.

### 4. compression과 container 선택이 실전 성능을 좌우한다

bit-sliced index 자체는 개념이고, 실제 성능은 bitmap 표현에 달려 있다.

- dense하면 raw bitmap이나 SIMD 친화 구조
- sparse하면 Roaring Bitmap 같은 compressed bitmap
- run이 많으면 run-length 계열

즉 BSI는 단독 구조라기보다, **bitmap container 위에서 작동하는 인덱스 레이아웃**에 가깝다.

특히 slice 압축률은 값 분포만이 아니라 row ordering과 row group 경계에도 크게 좌우된다.  
숫자 값의 prefix가 segment 안에서 얼마나 오래 유지되는지는 [Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)에서 함께 보는 편이 정확하다.

그리고 "정렬이 BSI 전체에 똑같이 먹히지 않고, 상위/하위 slice가 다르게 반응한다"는 점과 그 locality가 Roaring의 chunk-local 이득인지 global run 이득인지 구분하는 기준은 [Bit-Sliced Bitmap Sort-Key Sensitivity](./bit-sliced-bitmap-sort-key-sensitivity.md)에서 이어서 정리했다.

### 5. backend에서 어디에 맞나

OLTP 한 건 조회보다 analytics/segment evaluation 쪽에서 가치가 크다.

- 사용자 세그먼트 조건 평가
- 광고 타게팅
- feature rollout 대상 필터
- columnar execution engine의 predicate pushdown

질문이 "이 row 하나를 빨리 찾기"보다  
"많은 row를 조건으로 빨리 걸러내기"일수록 강해진다.

## 실전 시나리오

### 시나리오 1: 사용자 점수 기반 세그먼트

`loyaltyScore >= 700` 같은 조건을 자주 평가하면,  
row를 순회하기보다 score bit slice bitmap을 조합하는 편이 빠를 수 있다.

### 시나리오 2: 컬럼형 분석 엔진

columnar store에서 특정 숫자 컬럼 필터를 반복 적용할 때  
bit-sliced index는 predicate evaluation 비용을 크게 낮출 수 있다.

### 시나리오 3: bitmap 기반 권한/대상 선정

사용자 속성을 정수 코드로 정규화해 둔 시스템에서는  
여러 조건을 bitmap 연산으로 결합하는 방식이 매우 효율적이다.

### 시나리오 4: 부적합한 경우

row 수가 작거나 값 업데이트가 매우 잦으면  
bitmap 재구성 비용이 이득보다 커질 수 있다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.BitSet;
import java.util.List;

public class BitSlicedBitmapIndex {
    private final List<BitSet> slices;
    private int rowCount = 0;

    public BitSlicedBitmapIndex(int bitWidth) {
        this.slices = new ArrayList<>(bitWidth);
        for (int i = 0; i < bitWidth; i++) {
            slices.add(new BitSet());
        }
    }

    public void put(int rowId, int value) {
        rowCount = Math.max(rowCount, rowId + 1);
        for (int bit = 0; bit < slices.size(); bit++) {
            if (((value >>> bit) & 1) == 1) {
                slices.get(bit).set(rowId);
            } else {
                slices.get(bit).clear(rowId);
            }
        }
    }

    public BitSet equalsTo(int value) {
        BitSet result = new BitSet(rowCount);
        result.set(0, rowCount);

        for (int bit = 0; bit < slices.size(); bit++) {
            BitSet current = matchingSlice(bit, ((value >>> bit) & 1) == 1);
            result.and(current);
        }
        return result;
    }

    private BitSet matchingSlice(int bit, boolean oneBit) {
        BitSet current = (BitSet) slices.get(bit).clone();
        if (!oneBit) {
            current.flip(0, rowCount);
        }
        return current;
    }
}
```

이 코드는 equality 감각만 보여준다.  
실전 range query와 aggregation은 candidate/equal-set bitmap을 단계적으로 갱신하는 추가 로직이 필요하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Bit-Sliced Bitmap Index | 숫자 조건 필터와 일부 집계를 비트 연산으로 빠르게 처리할 수 있다 | 업데이트와 구현이 복잡하고 row-wise OLTP에는 과할 수 있다 | columnar filtering, segmentation, analytics |
| 값별 Bitmap Index | low-cardinality enum에는 매우 단순하고 빠르다 | 숫자 범위가 넓으면 bitmap 수가 너무 많아진다 | status/category 같은 속성 |
| B-Tree / Ordered Index | point/range lookup이 범용적이다 | 대규모 bitmap set algebra에는 약하다 | OLTP, mixed read/write |
| HashMap | exact key lookup이 단순하다 | range filter와 집합 결합이 비효율적이다 | exact match 중심 |

중요한 질문은 "값 하나를 찾는가"보다 "많은 row를 조건으로 잘라내는가"다.

## 꼬리질문

> Q: 값별 bitmap index 대신 bit-sliced index를 쓰는 이유는?
> 의도: high-cardinality 숫자 컬럼 인덱싱 감각 확인
> 핵심: 값 범위가 넓을 때 bitmap 개수를 통제하면서 조건 필터를 빠르게 처리할 수 있기 때문이다.

> Q: 왜 Roaring Bitmap 같은 압축 bitmap과 잘 어울리나요?
> 의도: 개념 레이어와 container 레이어를 구분하는지 확인
> 핵심: BSI는 bitmap 레이아웃이고, 실제 메모리 효율과 연산 성능은 각 slice의 container 표현에 크게 좌우되기 때문이다.

> Q: 어떤 시스템에서 특히 빛나나요?
> 의도: OLTP와 analytics 구분 이해 확인
> 핵심: columnar filtering, 세그먼트 평가, bitmap set algebra가 많은 시스템이다.

## 한 줄 정리

Bit-Sliced Bitmap Index는 숫자 값을 bit slice bitmap으로 분해해, 대량 row 조건 필터와 집계를 비트 연산 중심으로 처리하는 analytics 친화적 인덱스 구조다.
