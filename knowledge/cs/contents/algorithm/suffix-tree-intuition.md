# Suffix Tree Intuition

> 한 줄 요약: Suffix Tree는 문자열의 모든 suffix를 압축된 트리로 담아 substring 질의를 빠르게 하려는 고급 문자열 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Suffix Array and LCP](./suffix-array-lcp.md)
> - [Suffix Automaton](./suffix-automaton.md)
> - [Trie (Prefix Search / Autocomplete)](../data-structure/trie-prefix-search-autocomplete.md)

> retrieval-anchor-keywords: suffix tree, compressed suffix trie, substring search, Ukkonen intuition, suffix link, edge compression, repeated substring, string index, path compression, online string structure

## 핵심 개념

Suffix Tree는 문자열의 모든 suffix를 트리 형태로 저장하되,  
단일 경로를 edge label로 압축해 substring 검색을 빠르게 만든 구조다.

Trie가 prefix를 다루고, Suffix Automaton이 substring을 압축 상태로 표현한다면,  
Suffix Tree는 suffix 전체를 구조적으로 압축한 형태라고 보면 된다.

## 깊이 들어가기

### 1. 왜 suffix를 모두 넣나

어떤 substring도 어떤 suffix의 prefix로 볼 수 있다.
그래서 suffix를 전부 넣어 두면 substring 문제를 자연스럽게 다룰 수 있다.

### 2. edge compression

긴 단일 경로를 문자 하나씩 늘리지 않고 문자열 조각으로 저장한다.

이 덕분에 노드 수를 줄이고, substring 매칭 시 비교도 단축할 수 있다.

### 3. suffix link 감각

일부 구현에서는 suffix link를 통해 현재 경로의 한 단계 짧은 suffix로 빠르게 이동한다.  
온라인 구성에서 중요한 최적화 포인트다.

### 4. backend에서의 의미

Suffix Tree는 실무에서 직접 구현하기보다 문자열 분석용 개념으로 많이 본다.

- 반복 로그 패턴 분석
- 장문 텍스트 검색
- 압축 전 중복 구간 파악

## 실전 시나리오

### 시나리오 1: substring 검색

패턴이 문자열 어딘가에 있는지 빠르게 확인할 수 있다.

### 시나리오 2: 반복 문자열 탐지

가장 긴 반복 구간 같은 문제를 다루기 쉽다.

### 시나리오 3: 오판

구현 복잡도가 높아서, 실제로는 Suffix Array나 Suffix Automaton이 더 실용적인 경우가 많다.

## 코드로 보기

```java
public class SuffixTreeNotes {
    // 설명용 노트: 실제 온라인 suffix tree는 Ukkonen 방식과 suffix link가 핵심이다.
    public boolean containsSubstring(String text, String pattern) {
        return text.contains(pattern);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Suffix Tree | substring 질의가 강력하다 | 구현이 매우 어렵다 | 이론/고급 문자열 분석 |
| Suffix Array | 구현과 검색이 비교적 단순하다 | 동적 업데이트가 약하다 | 정적 인덱싱 |
| Suffix Automaton | substring 관련 연산이 압축적이다 | 상태 해석이 어렵다 | 반복/포함 분석 |

## 꼬리질문

> Q: 왜 suffix를 전부 넣어야 하나요?
> 의도: substring과 suffix의 관계 이해 확인
> 핵심: 모든 substring은 어떤 suffix의 prefix이기 때문이다.

> Q: Suffix Array와 가장 큰 차이는 무엇인가요?
> 의도: 정렬 인덱스와 트리 구조 차이 이해 확인
> 핵심: 하나는 정렬, 다른 하나는 압축 트리다.

> Q: 실무에서 직접 구현하나요?
> 의도: 구현 복잡도 감각 확인
> 핵심: 보통은 개념 이해와 라이브러리/대안 선택에 더 가깝다.

## 한 줄 정리

Suffix Tree는 모든 suffix를 압축된 트리로 저장해 substring 질문을 빠르게 처리하려는 고급 문자열 구조다.
