# Trie vs Radix vs Suffix Automaton

> 한 줄 요약: Trie, Radix Tree, Suffix Automaton은 모두 문자열 구조를 압축하지만, prefix, compressed prefix, substring이라는 서로 다른 질문에 맞춘다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Trie (Prefix Search / Autocomplete)](../data-structure/trie-prefix-search-autocomplete.md)
> - [Radix Tree (Compressed Trie)](../data-structure/radix-tree.md)
> - [Suffix Automaton](./suffix-automaton.md)

> retrieval-anchor-keywords: trie vs radix vs suffix automaton, prefix vs substring, compressed string index, autocomplete, substring automaton, edge compression, string data structure comparison

## 핵심 개념

이 세 구조는 서로 비슷해 보이지만, 최적화 대상이 다르다.

- Trie: prefix를 빠르게 찾는다
- Radix Tree: prefix를 압축해서 더 적은 메모리로 저장한다
- Suffix Automaton: 모든 substring을 압축해서 다룬다

문제 유형을 먼저 분류하면 구조 선택이 쉬워진다.

## 깊이 들어가기

### 1. Trie가 적합한 질문

문자열의 앞부분이 중요할 때 쓴다.

- autocomplete
- prefix routing
- 금칙어 prefix 검사

### 2. Radix Tree가 적합한 질문

prefix는 맞지만 경로가 길고 sparse할 때 쓴다.

- 긴 URL path
- IP prefix
- 계층형 키

### 3. Suffix Automaton이 적합한 질문

substring 전체를 보거나 반복 패턴을 보고 싶을 때 쓴다.

- 반복 substring
- 포함 여부
- distinct substring 개수

### 4. backend에서의 선택 감각

문자열 계층이 어디에 있느냐가 중요하다.

- 입력 접두사 -> Trie
- 압축된 접두사 -> Radix Tree
- 전체 문자열 내부 패턴 -> Suffix Automaton

## 실전 시나리오

### 시나리오 1: 검색창 자동완성

Trie가 가장 직관적이다.

### 시나리오 2: 긴 경로 라우팅

Radix Tree가 메모리와 구조 둘 다 균형이 좋다.

### 시나리오 3: 반복 문자열 분석

Suffix Automaton이 더 강하다.

### 시나리오 4: 오판

prefix 문제에 suffix automaton을 쓰면 과하다.  
substring 문제에 Trie를 쓰면 표현력이 부족할 수 있다.

## 코드로 보기

```java
public class StringStructureSelector {
    public static String choose(boolean prefix, boolean compressedPrefix, boolean substring) {
        if (substring) return "Suffix Automaton";
        if (compressedPrefix) return "Radix Tree";
        if (prefix) return "Trie";
        return "Need another tool";
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Trie | prefix 검색이 직관적이다 | 메모리를 많이 쓸 수 있다 | autocomplete |
| Radix Tree | prefix를 압축해 효율적이다 | 구현이 더 복잡하다 | sparse prefix |
| Suffix Automaton | substring 질문에 강하다 | 구현 난도가 높다 | 반복 패턴/substring |

## 꼬리질문

> Q: 세 구조의 핵심 차이는 무엇인가?
> 의도: 질문 유형과 자료구조를 연결하는지 확인
> 핵심: prefix, compressed prefix, substring이다.

> Q: prefix 문제에 SAM을 쓰면 안 되나?
> 의도: 과한 도구 선택을 피하는지 확인
> 핵심: 가능은 하지만 보통 과하다.

> Q: Radix Tree는 왜 Trie보다 압축되나?
> 의도: path compression 감각 확인
> 핵심: 단일 경로를 edge label로 합치기 때문이다.

## 한 줄 정리

Trie, Radix Tree, Suffix Automaton은 각각 prefix, compressed prefix, substring이라는 서로 다른 문자열 질문에 맞춘다.
