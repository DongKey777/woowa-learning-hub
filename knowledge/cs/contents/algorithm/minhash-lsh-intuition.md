# MinHash and LSH Intuition

> 한 줄 요약: MinHash는 집합의 Jaccard 유사도를 압축해 근사하고, LSH는 비슷한 항목끼리 같은 버킷에 들어가도록 설계하는 검색 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Rolling Hash / Rabin-Karp](./rolling-hash-rabin-karp.md)
> - [HyperLogLog](../data-structure/hyperloglog.md)
> - [Trie vs Radix vs Suffix Automaton](./trie-vs-radix-vs-suffix-automaton-comparison.md)

> retrieval-anchor-keywords: minhash, lsh, locality sensitive hashing, jaccard similarity, near duplicate, approximate similarity, shingles, banding, candidate generation, similarity search

## 핵심 개념

MinHash와 LSH는 "비슷한 것끼리 빨리 찾자"는 문제를 푸는 대표적 근사 기법이다.

- MinHash: 집합 유사도를 짧은 signature로 압축
- LSH: 비슷한 signature가 같은 bucket에 들어갈 확률을 높임

실무적으로는 near-duplicate 탐지, 문서 유사도, 아이템 후보 추천에 자주 연결된다.

## 깊이 들어가기

### 1. Jaccard 유사도

두 집합의 유사도를 `교집합 / 합집합`으로 보는 것이 Jaccard다.

문서의 shingle 집합이나 이벤트 집합을 비교할 때 자주 쓴다.

### 2. MinHash가 하는 일

집합을 해시 순서로 훑을 때 가장 먼저 만나는 원소를 기록하면,  
그 signature가 Jaccard 유사도를 근사하는 성질을 가진다.

즉 "set의 전체를 보지 않고도 비슷한 정도를 추정"할 수 있다.

### 3. LSH가 하는 일

비슷한 signature를 같은 후보 버킷에 넣는다.

banding 전략을 쓰면 비슷한 항목은 같은 bucket에 들어갈 가능성이 높아지고,  
다른 항목은 후보에서 빠지기 쉬워진다.

### 4. backend에서의 감각

문서/상품/이벤트의 near-duplicate 탐지는 정제 전 단계에서 중요하다.

- 검색 결과 중복 제거
- 유사 상품 그룹화
- 스팸/복제 콘텐츠 탐지

## 실전 시나리오

### 시나리오 1: near-duplicate 문서 찾기

긴 텍스트를 정확히 비교하기 전에 MinHash로 후보를 줄일 수 있다.

### 시나리오 2: 추천 후보 생성

유사한 아이템을 빠르게 모으는 후보 생성 단계에서 LSH가 잘 맞는다.

### 시나리오 3: 오판

정확한 문자열 equality를 원하는 경우에는 MinHash/LSH가 적합하지 않다.

### 시나리오 4: 대규모 검색 전처리

전체 공간을 다 비교하지 않고도 "비슷할 가능성이 높은 것"만 먼저 찾는다.

## 코드로 보기

```java
import java.util.Arrays;

public class MinHashNotes {
    public int[] signature(int[] shingles, int[] seeds) {
        int[] sig = new int[seeds.length];
        Arrays.fill(sig, Integer.MAX_VALUE);
        for (int shingle : shingles) {
            for (int i = 0; i < seeds.length; i++) {
                sig[i] = Math.min(sig[i], hash(shingle, seeds[i]));
            }
        }
        return sig;
    }

    private int hash(int x, int seed) {
        int h = x ^ (seed * 0x9e3779b9);
        h ^= (h >>> 16);
        return h;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| MinHash | 유사도 근사가 가능하다 | 정확하지 않다 | Jaccard 근사 |
| LSH | 비슷한 항목 후보를 줄인다 | 파라미터 튜닝이 필요하다 | 후보 생성 |
| Full Compare | 정확하다 | 너무 비싸다 | 소규모 데이터 |

## 꼬리질문

> Q: MinHash는 무엇을 근사하나?
> 의도: 유사도 유형을 아는지 확인
> 핵심: Jaccard similarity다.

> Q: LSH는 왜 필요한가?
> 의도: 후보 생성과 정확 비교 분리를 아는지 확인
> 핵심: 전체 비교를 줄이기 위해서다.

> Q: 어디에 자주 쓰이나?
> 의도: 실무 적용 감각 확인
> 핵심: near-duplicate, 추천, 유사 문서 검색이다.

## 한 줄 정리

MinHash와 LSH는 집합 유사도와 near-duplicate 탐색을 대규모에서 근사적으로 빠르게 처리하는 기법이다.
