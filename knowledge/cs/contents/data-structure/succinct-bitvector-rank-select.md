---
schema_version: 3
title: Succinct Bitvector Rank/Select
concept_id: data-structure/succinct-bitvector-rank-select
canonical: false
category: data-structure
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- succinct-bitvector
- rank-select
- compressed-index-primitive
aliases:
- succinct bitvector rank select
- rank select bitvector
- RRR bitvector
- compressed bitvector index
- bitvector rank query
- bitvector select query
- succinct index primitive
symptoms:
- compressed bitmap과 plain BitSet을 membership 관점으로만 보고 rank(i), select(k)가 필요한 압축 인덱스 primitive를 놓친다
- Elias-Fano와 Wavelet Tree가 빠른 rank/select bitvector에 의존한다는 연결을 이해하지 못한다
- update가 잦은 mutable workload에 succinct bitvector를 적용하려 해 build와 재구성 비용을 과소평가한다
intents:
- deep_dive
- comparison
prerequisites:
- data-structure/roaring-bitmap
- data-structure/elias-fano-encoded-posting-list
next_docs:
- data-structure/wavelet-tree
- data-structure/roaring-bitmap-selection-playbook
- data-structure/bit-sliced-bitmap-index
linked_paths:
- contents/data-structure/roaring-bitmap.md
- contents/data-structure/elias-fano-encoded-posting-list.md
- contents/data-structure/wavelet-tree.md
- contents/data-structure/roaring-bitmap-selection-playbook.md
- contents/data-structure/bit-sliced-bitmap-index.md
confusable_with:
- data-structure/roaring-bitmap
- data-structure/elias-fano-encoded-posting-list
- data-structure/wavelet-tree
- data-structure/plain-bitset-vs-compressed-bitmap-decision-card
forbidden_neighbors: []
expected_queries:
- succinct bitvector의 rank와 select는 compressed index에서 왜 중요한 primitive야?
- rank(i)와 select(k)를 빠르게 지원하면 Elias-Fano와 Wavelet Tree가 어떻게 가능해져?
- plain BitSet과 Roaring Bitmap과 succinct bitvector는 목적이 어떻게 달라?
- 압축 상태에서 k번째 1 위치를 찾는 select query는 왜 보조 인덱스가 필요해?
- immutable compressed index에서 rank/select bitvector를 쓰고 mutable update에는 조심해야 하는 이유는?
contextual_chunk_prefix: |
  이 문서는 succinct bitvector를 거의 압축된 크기로 저장하면서 rank(i)와
  select(k)를 빠르게 지원하는 compressed index primitive로 설명한다. Elias-Fano,
  Wavelet Tree, posting list, Roaring Bitmap과의 역할 차이를 다룬다.
---
# Succinct Bitvector Rank/Select

> 한 줄 요약: Succinct Bitvector with rank/select는 비트열을 거의 정보이론적 크기로 저장하면서 `rank`와 `select` 질의를 빠르게 지원해, 압축 인덱스의 기본 부품이 되는 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap](./roaring-bitmap.md)
> - [Elias-Fano Encoded Posting List](./elias-fano-encoded-posting-list.md)
> - [Wavelet Tree](./wavelet-tree.md)

> retrieval-anchor-keywords: succinct bitvector, rank select, bitvector index, compressed bitmap, rrr bitvector, rank query, select query, succinct index, wavelet tree primitive, elias fano primitive

## 핵심 개념

압축 인덱스를 읽다 보면 자주 등장하는 연산이 있다.

- `rank(i)`: i 위치까지 1이 몇 개인가
- `select(k)`: k번째 1은 어디 있는가

비트열 자체는 단순해 보이지만,  
이 두 연산을 빠르게 지원하면 놀라울 정도로 많은 압축 구조를 만들 수 있다.

- Elias-Fano
- Wavelet Tree
- compressed posting list
- succinct trie / automaton 보조 구조

즉 succinct bitvector는 그 자체보다  
**다른 compressed index를 가능하게 하는 기반 부품**에 가깝다.

## 깊이 들어가기

### 1. 왜 plain BitSet만으로는 부족한가

일반 BitSet은 membership이나 bitwise AND/OR에는 강하다.  
하지만 `k번째 1이 어디냐` 같은 질의를 자주 하면 순차 스캔이 필요해질 수 있다.

succinct bitvector는 여기에 보조 인덱스를 붙인다.

- 큰 블록의 prefix popcount
- 작은 블록의 보정값
- 경우에 따라 block 압축

그래서 공간은 크게 늘리지 않으면서도  
rank/select를 매우 빠르게 처리하려 한다.

### 2. rank와 select가 왜 중요한가

압축 구조는 종종 "값을 직접 저장"하지 않고  
"1의 위치"나 "누적 개수"만 가지고 탐색한다.

예:

- Elias-Fano upper bits에서 i번째 원소 위치 찾기
- Wavelet Tree에서 구간 내 rank 갱신
- compressed posting index에서 block boundary 이동

즉 rank/select가 빠르면  
압축 상태에서도 탐색과 점프가 가능해진다.

### 3. succinct는 "작다"가 아니라 "작고 탐색 가능하다"다

단순 압축만 하면 디코딩 후 다시 써야 한다.  
succinct 구조는 압축 상태에서 직접 질의하려는 게 포인트다.

그래서 trade-off는 보통 이렇게 잡힌다.

- raw BitSet보다 조금 더 계산한다
- 대신 공간은 매우 작게 유지한다
- 그래도 rank/select는 빠르게 제공한다

즉 저장과 질의의 균형을 맞춘다.

### 4. backend에서 어디에 맞나

read-heavy compressed index가 필요한 곳에서 가치가 크다.

- search engine posting index
- columnar analytic dictionary
- immutable segment metadata
- bitmap-based secondary index

특히 메모리 예산이 빡빡하고,  
index 구조를 가능한 한 많이 memory-resident로 두고 싶을 때 유용하다.

### 5. 함정과 운영 포인트

succinct bitvector는 update-friendly한 구조가 아니다.

- 중간 삽입/삭제가 잦으면 재구성이 부담된다
- build 단계가 필요하다
- 구현이 plain bitmap보다 훨씬 복잡하다

그래서 immutable segment / snapshot형 데이터에 잘 맞는다.

## 실전 시나리오

### 시나리오 1: Elias-Fano upper bits 지원

Elias-Fano는 upper bitvector에서 `select`가 빨라야  
i번째 원소를 효율적으로 복원할 수 있다.

### 시나리오 2: Wavelet Tree 질의 가속

Wavelet Tree의 rank 기반 하향 탐색은  
bitvector rank 연산이 빠를수록 전체 질의가 빨라진다.

### 시나리오 3: compressed posting skip

block boundary나 sparse marker를 bitvector로 들고 있다면  
rank/select로 빠르게 점프할 수 있다.

### 시나리오 4: 부적합한 경우

동적 업데이트가 많고 메모리 압축이 덜 중요하면  
plain bitmap이나 다른 mutable 구조가 더 낫다.

## 코드로 보기

```java
public class RankSelectBitvector {
    private final long[] words;
    private final int[] superblockRank;

    public RankSelectBitvector(long[] words) {
        this.words = words;
        this.superblockRank = new int[words.length + 1];
        for (int i = 0; i < words.length; i++) {
            superblockRank[i + 1] = superblockRank[i] + Long.bitCount(words[i]);
        }
    }

    public int rank1(int bitIndex) {
        int wordIndex = bitIndex >>> 6;
        int offset = bitIndex & 63;
        long mask = offset == 63 ? -1L : ((1L << (offset + 1)) - 1);
        return superblockRank[wordIndex] + Long.bitCount(words[wordIndex] & mask);
    }

    public int select1(int target) {
        int low = 0;
        int high = words.length;
        while (low < high) {
            int mid = (low + high) >>> 1;
            if (superblockRank[mid] < target) {
                low = mid + 1;
            } else {
                high = mid;
            }
        }
        int wordIndex = low - 1;
        int remaining = target - superblockRank[wordIndex];
        long word = words[wordIndex];
        for (int bit = 0; bit < 64; bit++) {
            if (((word >>> bit) & 1L) == 1L && --remaining == 0) {
                return (wordIndex << 6) + bit;
            }
        }
        return -1;
    }
}
```

이 코드는 rank/select 감각만 보여준다.  
실제 succinct bitvector는 block hierarchy, compressed block encoding, faster select 지원이 더 중요하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Succinct Bitvector with rank/select | 압축 상태에서도 rank/select 질의를 빠르게 지원한다 | build와 구현이 복잡하고 update에 약하다 | immutable compressed index |
| Plain BitSet | 구현이 단순하고 bitwise 연산이 빠르다 | rank/select 질의엔 보조 스캔이 필요할 수 있다 | 단순 membership / bitwise set algebra |
| Roaring Bitmap | exact set algebra와 적응형 압축이 좋다 | 순수 rank/select 기반 succinct primitive와는 목적이 다르다 | exact bitmap set operations |
| Elias-Fano | 정렬된 sparse 수열 자체를 잘 압축한다 | 일반 bitvector primitive와는 역할이 다르다 | monotone integer sequence compression |

중요한 질문은 "비트열을 저장하는가"보다  
"압축 상태에서 rank/select 질의를 직접 해야 하는가"다.

## 꼬리질문

> Q: rank와 select가 왜 그렇게 중요한가요?
> 의도: compressed index의 탐색이 누적 개수/위치 질의에 의존한다는 점 이해 확인
> 핵심: 압축 상태에서도 위치 점프와 구간 매핑을 하려면 rank/select가 핵심 primitive가 되기 때문이다.

> Q: Elias-Fano와 succinct bitvector의 관계는 무엇인가요?
> 의도: 상위 구조와 기반 primitive를 구분하는지 확인
> 핵심: Elias-Fano는 상위 인코딩이고, 그 내부 upper bitvector 탐색에 rank/select가 자주 필요하다.

> Q: 왜 immutable index에 잘 맞나요?
> 의도: build-heavy / query-light 감각 확인
> 핵심: compact 보조 인덱스를 미리 만들어두고 읽기 질의를 빠르게 하는 구조이기 때문이다.

## 한 줄 정리

Succinct Bitvector with rank/select는 압축된 비트열에서 개수와 위치 질의를 빠르게 제공하는 기반 primitive로, Elias-Fano와 wavelet 계열 같은 memory-efficient index를 가능하게 하는 핵심 부품이다.
