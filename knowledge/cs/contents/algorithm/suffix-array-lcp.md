---
schema_version: 3
title: Suffix Array and LCP
concept_id: algorithm/suffix-array-lcp
canonical: true
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
  - substring-index-choice
  - repeated-substring-analysis
aliases:
  - suffix array
  - lcp array
  - suffix array lcp
  - longest common prefix array
  - substring index
  - suffix sorting
  - repeated substring index
  - lexicographic suffix ordering
symptoms:
  - 반복 substring 문제라는데 suffix array와 LCP를 왜 같이 봐야 하는지 연결이 안 돼
  - suffix를 정렬하면 뭐가 쉬워지는지 모르겠고 LCP 배열은 더 낯설어
  - trie 말고 suffix array를 써야 하는 정적 문자열 검색 상황이 감이 안 와
intents:
  - definition
  - deep_dive
  - comparison
prerequisites:
  - algorithm/string
next_docs:
  - algorithm/suffix-tree-intuition
  - algorithm/suffix-automaton
  - algorithm/suffix-array-vs-suffix-tree-comparison
linked_paths:
  - contents/algorithm/string.md
  - contents/algorithm/suffix-tree-intuition.md
  - contents/algorithm/suffix-automaton.md
  - contents/algorithm/suffix-array-vs-suffix-tree-comparison.md
  - contents/data-structure/trie-prefix-search-autocomplete.md
  - contents/data-structure/radix-tree.md
confusable_with:
  - algorithm/suffix-tree-intuition
  - algorithm/suffix-automaton
forbidden_neighbors:
  - contents/data-structure/trie-prefix-search-autocomplete.md
expected_queries:
  - suffix array와 lcp를 같이 배우는 이유를 문자열 검색 관점에서 설명해줘
  - 반복 substring을 찾을 때 suffix array가 어떤 식으로 후보를 줄이는지 알고 싶어
  - suffix 정렬과 인접 공통 prefix 배열이 왜 같이 등장하는지 감이 안 와
  - trie 대신 suffix array를 떠올려야 하는 문자열 인덱스 상황을 비교해줘
  - 정적 텍스트 인덱싱에서 suffix array와 lcp가 어떤 역할을 나눠 가지는지 설명해줘
contextual_chunk_prefix: |
  이 문서는 문자열 학습자가 suffix를 사전순으로 세워 두면 왜 부분 문자열
  검색 후보가 줄고, 이웃한 suffix의 겹치는 길이를 함께 봐야 반복 패턴이
  보이는지 깊이 잡는 deep_dive다. 접미사 정렬로 찾기 범위 좁히기, 비슷한
  꼬리끼리 붙여 보기, 반복되는 조각 길이 재기, 인접 비교를 덜 하기, 정적
  텍스트 인덱스 감각 같은 자연어 paraphrase가 본 문서의 suffix array와
  LCP 연결에 매핑된다.
---
# Suffix Array and LCP

> 한 줄 요약: Suffix Array는 문자열의 모든 suffix를 정렬해 검색 기반을 만들고, LCP는 인접 suffix의 공통 접두사를 이용해 반복 비교를 줄인다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [문자열 패턴 매칭](./string.md)
> - [Trie (Prefix Search / Autocomplete)](../data-structure/trie-prefix-search-autocomplete.md)
> - [Radix Tree (Compressed Trie)](../data-structure/radix-tree.md)

> retrieval-anchor-keywords: suffix array, lcp array, longest common prefix, substring search, repeated patterns, suffix sorting, suffix ranking, string index, lexicographic order, longest repeated substring

## 핵심 개념

Suffix Array는 문자열 `S`의 모든 suffix를 사전순으로 정렬한 배열이다.  
LCP(Longest Common Prefix) 배열은 정렬된 인접 suffix끼리의 공통 접두사 길이를 저장한다.

이 조합의 장점은 문자열 전체를 매번 훑지 않고도 다음을 빠르게 할 수 있다는 점이다.

- 부분 문자열 존재 여부 확인
- 반복 패턴 탐지
- 가장 긴 반복 부분 문자열 찾기
- 여러 문자열이 공유하는 prefix 구조 분석

실무에서 이건 "검색 인덱스" 감각으로 이해하면 좋다.  
문자열을 정렬해 두고, 비슷한 suffix끼리 붙여 놓으면 비교 비용을 줄일 수 있다.

## 깊이 들어가기

### 1. suffix를 왜 정렬하나

문자열의 부분 문자열은 어떤 suffix의 prefix로 나타난다.  
즉 suffix들을 정렬해 놓으면, 원하는 패턴과 비슷한 suffix를 이진 탐색으로 찾을 수 있다.

예를 들어 `banana`의 suffix는 다음과 같다.

- `banana`
- `anana`
- `nana`
- `ana`
- `na`
- `a`

정렬하면 비슷한 문자열끼리 붙기 때문에, 검색과 중복 패턴 분석이 쉬워진다.

### 2. LCP 배열이 왜 중요한가

정렬된 suffix는 인접한 것끼리 비슷한 경우가 많다.  
LCP는 "이 두 suffix가 어디까지 같은가"를 저장해서 중복 비교를 줄인다.

이 값이 있으면 다음이 쉬워진다.

- 가장 긴 반복 substring 탐색
- 서로 다른 suffix 구간의 공통 패턴 파악
- 패턴 탐색 중 불필요한 비교 절약

### 3. backend에서 쓸 만한 곳

Suffix Array는 검색 엔진의 전체 인덱스라기보다, 문자열 분석 도구에 가깝다.

- 로그 메시지에서 반복되는 문구 찾기
- DNA/시퀀스처럼 반복 구조가 많은 데이터
- 대량 텍스트에서 흔한 접두사/접미사 패턴 분석
- 문자열 압축 전 반복 구간 탐지

### 4. Trie와의 관계

Trie는 prefix 관점에 강하고, Suffix Array는 substring 관점에 강하다.

- Trie: "이 prefix로 시작하는가"
- Suffix Array: "이 패턴이 문자열 어딘가에 있는가"

둘은 서로 다른 문제를 푸는 도구다.

## 실전 시나리오

### 시나리오 1: 부분 문자열 검색

로그 메시지, 장문 텍스트, 코드 스니펫에서 특정 패턴이 포함되는지 확인할 때 suffix array를 쓰면 후보 범위를 줄일 수 있다.

### 시나리오 2: 가장 긴 반복 구간 찾기

비슷한 문자열 조각이 반복되는 문서를 압축하거나 중복 콘텐츠를 분석할 때 유용하다.

### 시나리오 3: 여러 후보 중 가장 비슷한 접미사 찾기

정렬된 suffix 사이에서 인접 LCP를 비교하면 가장 가까운 문자열 군집을 찾기 쉽다.

### 시나리오 4: 오판

문자열 길이가 매우 짧거나 질의가 거의 없는 경우에는 suffix array를 만드는 비용이 과할 수 있다.  
이럴 땐 KMP나 단순 탐색이 더 적합할 수 있다.

## 코드로 보기

```java
import java.util.Arrays;

public class SuffixArray {
    public int[] build(String s) {
        int n = s.length();
        Integer[] order = new Integer[n];
        int[] rank = new int[n];
        int[] temp = new int[n];

        for (int i = 0; i < n; i++) {
            order[i] = i;
            rank[i] = s.charAt(i);
        }

        for (int k = 1; k < n; k <<= 1) {
            final int step = k;
            Arrays.sort(order, (a, b) -> {
                if (rank[a] != rank[b]) return Integer.compare(rank[a], rank[b]);
                int ra = a + step < n ? rank[a + step] : -1;
                int rb = b + step < n ? rank[b + step] : -1;
                return Integer.compare(ra, rb);
            });

            temp[order[0]] = 0;
            for (int i = 1; i < n; i++) {
                int prev = order[i - 1];
                int cur = order[i];
                boolean same = rank[prev] == rank[cur]
                    && (prev + step < n ? rank[prev + step] : -1) == (cur + step < n ? rank[cur + step] : -1);
                temp[cur] = temp[prev] + (same ? 0 : 1);
            }

            System.arraycopy(temp, 0, rank, 0, n);
            if (rank[order[n - 1]] == n - 1) break;
        }

        int[] suffixArray = new int[n];
        for (int i = 0; i < n; i++) {
            suffixArray[i] = order[i];
        }
        return suffixArray;
    }

    public int[] buildLcp(String s, int[] sa) {
        int n = s.length();
        int[] rank = new int[n];
        for (int i = 0; i < n; i++) rank[sa[i]] = i;

        int[] lcp = new int[n - 1];
        int h = 0;
        for (int i = 0; i < n; i++) {
            int r = rank[i];
            if (r == n - 1) {
                h = 0;
                continue;
            }
            int j = sa[r + 1];
            while (i + h < n && j + h < n && s.charAt(i + h) == s.charAt(j + h)) {
                h++;
            }
            lcp[r] = h;
            if (h > 0) h--;
        }
        return lcp;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Suffix Array + LCP | substring 검색과 반복 구조 분석이 강하다 | 빌드가 복잡하고 메모리 부담이 있다 | 대량 문자열 분석, 정적 인덱스 |
| Trie | prefix 검색이 직관적이다 | substring 검색에는 약하다 | autocomplete, prefix routing |
| KMP | 구현이 단순하고 빠르다 | 하나의 패턴만 본다 | 단일 패턴 검색 |

Suffix Array는 "문자열을 정렬해 검색을 빠르게 만드는 정적 인덱스"라고 보면 된다.

## 꼬리질문

> Q: suffix array는 왜 substring 검색에 도움이 되나?
> 의도: suffix와 substring의 관계 이해 확인
> 핵심: 모든 substring은 어떤 suffix의 prefix이기 때문이다.

> Q: LCP가 왜 필요한가?
> 의도: 정렬만으로 충분하지 않은 이유 확인
> 핵심: 인접 suffix의 공통 길이를 알면 반복 비교를 줄일 수 있다.

> Q: Trie와 어떤 기준으로 고르면 되나?
> 의도: prefix/substr 문제 구분 확인
> 핵심: prefix 질의는 Trie, substring 질의는 suffix array가 더 자연스럽다.

## 한 줄 정리

Suffix Array와 LCP는 문자열을 정렬된 인덱스로 바꿔 substring 검색과 반복 패턴 분석을 빠르게 하는 조합이다.
