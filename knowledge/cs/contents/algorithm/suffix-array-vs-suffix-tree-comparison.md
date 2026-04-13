# Suffix Array vs Suffix Tree

> 한 줄 요약: Suffix Array는 정렬 기반 정적 인덱스이고, Suffix Tree는 압축 트리 기반의 더 직접적인 substring 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Suffix Array and LCP](./suffix-array-lcp.md)
> - [Suffix Tree Intuition](./suffix-tree-intuition.md)
> - [Suffix Automaton](./suffix-automaton.md)

> retrieval-anchor-keywords: suffix array vs suffix tree, substring index comparison, static vs online, compressed trie, suffix lcp, text indexing, memory tradeoff

## 핵심 개념

둘 다 substring 분석에 쓰이지만 구조가 다르다.

- Suffix Array: suffix를 정렬한 배열
- Suffix Tree: suffix를 압축한 트리

즉 하나는 정렬, 다른 하나는 구조화된 트리다.

## 깊이 들어가기

### 1. suffix array의 장점

- 구현이 상대적으로 단순하다
- 메모리 사용이 예측 가능하다
- LCP와 결합해 다양한 검색을 지원한다

### 2. suffix tree의 장점

- substring 구조를 직접적으로 다룬다
- 질의 관점에서 강력하다

### 3. backend에서의 선택

정적 로그나 텍스트 인덱스에는 suffix array가 더 실용적인 경우가 많다.  
이론적 직접성과 빠른 substring 탐색을 원하면 suffix tree를 본다.

### 4. 실전 감각

구현 난이도, 메모리, 업데이트 가능성까지 함께 본다.

## 실전 시나리오

### 시나리오 1: 텍스트 검색

정적 문서 집합이면 suffix array가 관리가 쉽다.

### 시나리오 2: 반복 패턴 분석

더 직접적인 substring 구조가 필요하면 suffix tree가 유리할 수 있다.

### 시나리오 3: 오판

업데이트가 많은 상황에서는 둘 다 부담이 될 수 있다.

## 코드로 보기

```java
public class SuffixIndexComparison {
    public static String choose(boolean staticIndex, boolean directSubstringStructure) {
        if (staticIndex) return "Suffix Array";
        if (directSubstringStructure) return "Suffix Tree";
        return "Need another tool";
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Suffix Array | 구현과 메모리가 비교적 낫다 | 질의 보조 구조가 필요할 수 있다 | 정적 텍스트 인덱싱 |
| Suffix Tree | substring 질의가 직관적이다 | 구현이 어렵다 | 고급 문자열 분석 |
| Suffix Automaton | substring 압축에 강하다 | 상태 해석이 어렵다 | 반복 패턴/포함 분석 |

## 꼬리질문

> Q: 둘의 핵심 차이는 무엇인가요?
> 의도: 정렬 vs 트리 구조를 구분하는지 확인
> 핵심: suffix array는 정렬 인덱스, suffix tree는 압축 트리다.

> Q: 왜 실무에서는 suffix array를 더 자주 보나?
> 의도: 구현 난이도와 메모리 감각 확인
> 핵심: 구현이 상대적으로 쉽고 안정적이기 때문이다.

> Q: suffix automaton은 어디에 서나?
> 의도: 관련 문자열 구조 분류 확인
> 핵심: substring 압축 구조로 볼 수 있다.

## 한 줄 정리

Suffix Array는 정적 정렬 인덱스, Suffix Tree는 직접적인 압축 substring 트리라는 점이 가장 큰 차이다.
