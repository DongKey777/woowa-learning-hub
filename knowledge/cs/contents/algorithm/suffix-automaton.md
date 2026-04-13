# Suffix Automaton

> 한 줄 요약: Suffix Automaton은 문자열의 모든 substring을 압축해 담는 자동자로, 반복 패턴과 substring 질의에 강하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Suffix Array and LCP](./suffix-array-lcp.md)
> - [Trie (Prefix Search / Autocomplete)](../data-structure/trie-prefix-search-autocomplete.md)
> - [Radix Tree (Compressed Trie)](../data-structure/radix-tree.md)

> retrieval-anchor-keywords: suffix automaton, sam, substring automaton, endpos, suffix link, clone state, distinct substring, repeated substring, string automaton, compressed substrings

## 핵심 개념

Suffix Automaton(SAM)은 어떤 문자열의 **모든 substring**을 압축된 상태 그래프로 표현한다.

Trie가 prefix를 잘 다루고, Suffix Array가 정렬된 suffix를 다룬다면, SAM은 substring 전체를 더 동적으로 다룬다.

실무적으로는 다음 질문에 잘 맞는다.

- 이 문자열이 다른 문자열 안에 포함되는가
- 가장 긴 반복 substring은 무엇인가
- 서로 다른 substring이 몇 개인가

## 깊이 들어가기

### 1. state가 무엇인가

각 state는 특정 substring들의 집합을 대표한다.

핵심 개념은 `endpos`다.

- 같은 end position 집합을 공유하는 substring들은 비슷한 상태로 묶인다.
- 이 묶음을 통해 substring 공간을 압축한다.

### 2. suffix link

각 state는 더 짧은 관련 상태로 향하는 suffix link를 가진다.

이 링크를 따라가면 substring을 점점 짧게 줄여 갈 수 있다.  
즉 suffix 관계를 빠르게 이동하는 통로가 된다.

### 3. clone state

새 문자를 넣을 때 기존 전이가 너무 많이 공유되면 상태를 복제해야 할 수 있다.

이 clone이 SAM 구현의 핵심 난이도 포인트다.

### 4. backend에서의 감각

SAM은 문자열을 단순 검색하는 수준을 넘어서, 반복/포함/구조 분석에 쓰기 좋다.

- 로그 조각 중복 탐지
- 반복 템플릿 분석
- 문자열 압축 전 중복 구조 파악

## 실전 시나리오

### 시나리오 1: 서로 다른 substring 개수

문자열 내부의 모든 substring 수를 빠르게 계산하거나 추정 구조를 만들 때 SAM이 강하다.

### 시나리오 2: longest repeated substring

반복되는 가장 긴 부분 문자열을 찾는 문제에 잘 맞는다.

### 시나리오 3: substring membership

특정 패턴이 문자열에 포함되는지 빠르게 확인할 수 있다.

### 시나리오 4: 오판

prefix 중심 문제라면 Trie가 더 자연스럽고, 정적 다량 검색이면 Suffix Array가 더 편할 수 있다.

## 코드로 보기

```java
import java.util.HashMap;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class SuffixAutomaton {
    private static final class State {
        Map<Character, Integer> next = new HashMap<>();
        int link = -1;
        int len = 0;
    }

    private final List<State> st = new ArrayList<>();
    private int last = 0;

    public SuffixAutomaton() {
        st.add(new State());
    }

    public void extend(char c) {
        int cur = st.size();
        st.add(new State());
        st.get(cur).len = st.get(last).len + 1;

        int p = last;
        while (p != -1 && !st.get(p).next.containsKey(c)) {
            st.get(p).next.put(c, cur);
            p = st.get(p).link;
        }

        if (p == -1) {
            st.get(cur).link = 0;
        } else {
            int q = st.get(p).next.get(c);
            if (st.get(p).len + 1 == st.get(q).len) {
                st.get(cur).link = q;
            } else {
                int clone = st.size();
                st.add(new State());
                st.get(clone).len = st.get(p).len + 1;
                st.get(clone).next.putAll(st.get(q).next);
                st.get(clone).link = st.get(q).link;

                while (p != -1 && st.get(p).next.get(c) == q) {
                    st.get(p).next.put(c, clone);
                    p = st.get(p).link;
                }

                st.get(q).link = st.get(cur).link = clone;
            }
        }
        last = cur;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Suffix Automaton | substring 관련 연산이 강하다 | 구현이 어렵다 | 반복/포함 분석 |
| Suffix Array | 정적 인덱싱과 검색에 좋다 | 빌드가 무겁다 | 대량 문자열 검색 |
| Trie | prefix에 강하다 | substring 전체에는 약하다 | autocomplete |

SAM은 구현 난도 대신 substring 문제를 아주 강하게 푼다.

## 꼬리질문

> Q: SAM이 prefix trie와 다른 점은?
> 의도: prefix와 substring의 차이를 이해하는지 확인
> 핵심: Trie는 prefix, SAM은 모든 substring을 압축한다.

> Q: clone state는 왜 필요한가?
> 의도: 상태 분기와 최소 자동자 구조를 이해하는지 확인
> 핵심: 전이 구조가 너무 많이 공유되면 상태를 분리해야 하기 때문이다.

> Q: 어떤 문제에 가장 잘 맞나?
> 의도: 실전 적용 감각 확인
> 핵심: 반복 substring, 포함 여부, distinct substring 수다.

## 한 줄 정리

Suffix Automaton은 문자열의 모든 substring을 압축 상태로 표현해 반복 패턴과 substring 질의를 빠르게 다루는 자동자다.
