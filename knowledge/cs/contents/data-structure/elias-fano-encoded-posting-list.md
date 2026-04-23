# Elias-Fano Encoded Posting List

> 한 줄 요약: Elias-Fano는 정렬된 정수 ID 목록을 매우 작게 압축하면서도 select, skip, predecessor 같은 탐색을 유지해, posting list와 memory-efficient index에 자주 쓰이는 단조 수열 인코딩이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap](./roaring-bitmap.md)
> - [Succinct Bitvector Rank/Select](./succinct-bitvector-rank-select.md)
> - [Bit-Sliced Bitmap Index](./bit-sliced-bitmap-index.md)
> - [LSM-Friendly Index Structures](./lsm-friendly-index-structures.md)
> - [Adaptive Radix Tree](./adaptive-radix-tree.md)

> retrieval-anchor-keywords: elias fano, posting list compression, monotone integer sequence, succinct index, predecessor query, compressed posting list, sorted row ids, skip index, memory efficient indexing, doc id compression, rank select bitvector

## 핵심 개념

정렬된 ID 목록은 backend 곳곳에 등장한다.

- 검색엔진 posting list
- 사용자 세그먼트 row id
- time-series block offset
- columnar index row pointer

이런 목록은 보통 **오름차순 단조 증가**라는 강한 성질이 있다.  
Elias-Fano는 이 성질을 이용해, 값 전체를 그대로 저장하는 대신 상위 비트와 하위 비트를 분리해 압축한다.

핵심은 이렇다.

- 정렬되어 있을 것
- 값 범위 `U`와 원소 수 `n`을 기준으로 lower bits 수를 정함
- lower bits 배열 + unary 비슷한 upper bits bitvector로 표현

즉 일반 압축이 아니라 **단조 수열에 특화된 succinct encoding**이다.

## 깊이 들어가기

### 1. 왜 정렬된 ID는 특별한가

정렬되어 있으면 두 가지 정보가 이미 줄어든다.

- 값의 순서를 따로 저장할 필요가 없다
- 인접 값 차이가 작을 가능성이 높다

Elias-Fano는 이걸 delta encoding처럼 차이값만 저장하는 식으로 보지 않고,  
각 값의 상/하위 비트를 분리해 rank/select 가능한 형태로 저장한다.

### 2. lower bits와 upper bits 분리가 핵심이다

값 `x`를 이렇게 나눈다고 생각하면 쉽다.

- lower = `x & ((1 << l) - 1)`
- upper = `x >>> l`

모든 원소의 lower bits는 고정 길이 배열에 저장한다.  
upper bits는 단조 증가하므로 bitvector에서 1의 위치로 표현하기 좋다.

이 구조 덕분에:

- 공간이 매우 작다
- `select(i)`가 가능하다
- predecessor / skip search를 만들기 쉽다

즉 "압축은 했지만 순차 스캔밖에 못 한다"가 아니라,  
**압축 상태에서도 탐색 친화적**이라는 점이 중요하다.

### 3. posting list에서 왜 자주 나오나

검색/분석 인덱스는 posting list를 많이 가진다.

- term -> docID 목록
- segment -> userID 목록
- value bucket -> rowID 목록

이때 BitSet이나 Roaring Bitmap은 집합 연산에 강하고,  
Elias-Fano는 **정렬된 sparse ID 목록 자체를 아주 작게 들고 가는 것**에 강하다.

특히 posting list가 매우 sparse하고, 순차 merge나 skip이 중요할 때 잘 맞는다.

### 4. bitmap과 어디서 갈리나

Roaring Bitmap과 Elias-Fano는 경쟁 관계이기도 하고 보완 관계이기도 하다.

- dense set operation이 많으면 bitmap 쪽이 유리할 수 있다
- sparse sorted list와 skip scan이 중요하면 Elias-Fano가 유리할 수 있다

즉 질문이 다르다.

- "집합 연산이 핵심인가?"
- "정렬된 ID 목록을 작게 들고 predecessor/merge 해야 하는가?"

### 5. backend에서의 함정

Elias-Fano는 update-heavy OLTP 인덱스와는 잘 맞지 않는다.

- append-friendly하게 만들 수는 있어도
- 중간 삽입과 삭제가 잦으면 재인코딩 부담이 커진다

그래서 보통은 immutable segment나 block 단위 구조에서 빛난다.

- 검색 인덱스 세그먼트
- columnar block
- snapshot 기반 analytics

## 실전 시나리오

### 시나리오 1: sparse posting list 압축

문서 수는 큰데 특정 term의 docID 목록은 sparse하다면,  
bitmap보다 Elias-Fano가 더 작은 공간으로 skip-friendly list를 만들 수 있다.

### 시나리오 2: columnar row id list

필터 결과 row id를 정렬된 목록으로 보관하고 병합/교집합을 자주 한다면  
compressed sorted integer list가 좋은 선택이 된다.

### 시나리오 3: block offset index

대형 파일이나 segment 내부 오프셋이 증가 순서라면  
작은 메모리로 탐색 포인트를 유지하기 좋다.

### 시나리오 4: 부적합한 경우

업데이트가 매우 잦거나 dense bitmap set algebra가 중심이면  
Roaring Bitmap이나 다른 구조가 더 낫다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.BitSet;
import java.util.List;

public class EliasFanoSketch {
    private final int lowerBitCount;
    private final List<Integer> lowers = new ArrayList<>();
    private final BitSet uppers = new BitSet();

    public EliasFanoSketch(int universe, int itemCount) {
        this.lowerBitCount = Math.max(0, 31 - Integer.numberOfLeadingZeros(Math.max(1, universe / Math.max(1, itemCount))));
    }

    public void encode(List<Integer> sortedValues) {
        int mask = (1 << lowerBitCount) - 1;
        for (int i = 0; i < sortedValues.size(); i++) {
            int value = sortedValues.get(i);
            int lower = value & mask;
            int upper = value >>> lowerBitCount;

            lowers.add(lower);
            uppers.set(upper + i);
        }
    }
}
```

이 코드는 upper/lower 분리 감각만 보여준다.  
실전 Elias-Fano는 `select`, `rank`, predecessor, skip pointer 보조 구조까지 같이 구현해야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Elias-Fano Encoded Posting List | sparse한 정렬 ID 목록을 작게 저장하면서 skip-friendly 탐색이 가능하다 | update-heavy 구조에는 부적합하고 구현 이해가 필요하다 | posting list, immutable index, compressed offsets |
| Roaring Bitmap | exact set algebra가 빠르고 dense/sparse 적응이 좋다 | 매우 sparse sorted list에서는 더 클 수 있다 | 집합 연산과 bitmap combine이 중요할 때 |
| Delta / Varint List | 구현이 단순하고 순차 스캔이 빠르다 | random select / predecessor 지원이 약하다 | 압축된 순차 스캔이 중심일 때 |
| HashSet | membership은 단순하다 | 정렬 순서와 압축 효율이 약하다 | 작은 집합, 단순 exact lookup |

중요한 질문은 "정렬된 sparse ID 목록을 어떻게 가장 작게 들고 갈까"와 "압축 상태에서 어떤 탐색이 필요한가"다.

## 꼬리질문

> Q: Elias-Fano가 bitmap보다 유리한 경우는 언제인가요?
> 의도: sparse sorted list와 dense set algebra를 구분하는지 확인
> 핵심: posting list가 sparse하고, 순차 merge나 predecessor/skip 탐색이 중요할 때다.

> Q: 왜 immutable segment형 구조와 잘 맞나요?
> 의도: 인코딩 재구성 비용 감각 확인
> 핵심: 중간 삽입/삭제가 잦으면 재인코딩 비용이 커지기 때문이다.

> Q: Elias-Fano가 단순 delta encoding보다 좋은 점은 무엇인가요?
> 의도: 압축과 탐색의 균형 이해 확인
> 핵심: 공간 효율을 유지하면서도 rank/select 기반 탐색 친화적 구조를 만들기 쉽다는 점이다.

## 한 줄 정리

Elias-Fano는 정렬된 sparse ID 목록을 compact하게 압축하면서도 skip와 predecessor 탐색을 유지할 수 있어, posting list와 memory-efficient immutable index에 특히 잘 맞는 자료구조다.
