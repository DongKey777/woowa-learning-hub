---
schema_version: 3
title: Radix Tree Compressed Trie
concept_id: data-structure/radix-tree
canonical: false
category: data-structure
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- radix-tree
- compressed-trie
- prefix-routing-index
aliases:
- Radix Tree
- compressed trie
- path compression trie
- prefix routing
- edge label trie
- sparse trie
- IP prefix URL router
symptoms:
- Trie가 prefix search에는 좋지만 긴 단일 경로와 sparse branching에서 node overhead가 커지는 문제를 놓친다
- Radix Tree의 핵심이 문자 하나씩 node를 만드는 대신 edge label로 compressed path를 저장하는 것임을 이해하지 못한다
- prefix search가 필요한지 exact hash lookup이나 ordered range scan이 필요한지 구분하지 않고 HashMap/TreeMap과 비교한다
intents:
- definition
- comparison
prerequisites:
- data-structure/trie-prefix-search-autocomplete
next_docs:
- data-structure/adaptive-radix-tree
- data-structure/finite-state-transducer
- data-structure/hashmap-internals
- data-structure/treemap-vs-hashmap-vs-linkedhashmap
linked_paths:
- contents/data-structure/trie-prefix-search-autocomplete.md
- contents/data-structure/adaptive-radix-tree.md
- contents/data-structure/finite-state-transducer.md
- contents/data-structure/hashmap-internals.md
- contents/data-structure/treemap-vs-hashmap-vs-linkedhashmap.md
confusable_with:
- data-structure/trie-prefix-search-autocomplete
- data-structure/adaptive-radix-tree
- data-structure/finite-state-transducer
- data-structure/hashmap-internals
forbidden_neighbors: []
expected_queries:
- Radix Tree는 일반 Trie보다 공통 경로를 어떻게 압축해?
- compressed trie에서 edge label split과 merge가 필요한 이유는?
- URL router나 IP prefix matching에 Radix Tree가 맞는 이유는?
- Radix Tree와 Adaptive Radix Tree와 FST를 어떻게 비교해?
- prefix search가 필요할 때 HashMap이나 TreeMap 대신 Radix Tree를 보는 기준은?
contextual_chunk_prefix: |
  이 문서는 Radix Tree를 Trie의 single-child path를 edge label로 압축해 prefix
  search를 유지하면서 node overhead를 줄이는 compressed trie primer로
  설명한다. URL routing, IP prefix, autocomplete, edge split/merge를 다룬다.
---
# Radix Tree (Compressed Trie)

> 한 줄 요약: Radix Tree는 Trie의 공통 경로를 압축해서, prefix 검색은 유지하면서 메모리 낭비를 줄인 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Trie (Prefix Search / Autocomplete)](./trie-prefix-search-autocomplete.md)
> - [Adaptive Radix Tree](./adaptive-radix-tree.md)
> - [Finite State Transducer](./finite-state-transducer.md)
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)

> retrieval-anchor-keywords: radix tree, compressed trie, path compression, prefix routing, autocomplete, IP prefix, URL router, sparse trie, edge label, compressed edge

## 핵심 개념

Radix Tree는 Trie와 비슷하지만, **자식이 하나뿐인 긴 경로를 하나의 edge label로 합친 구조**다.  
즉 문자 하나씩 노드를 늘리지 않고, 공통 prefix를 문자열 조각 단위로 압축한다.

이 구조의 핵심은 두 가지다.

- prefix 탐색의 장점은 유지한다.
- 노드 수를 줄여 메모리와 순회 비용을 낮춘다.

실무에서는 문자열 키가 많지만 prefix가 매우 편중된 경우에 특히 유리하다.

- URL path 라우팅
- CIDR / IP prefix 매칭
- 검색 자동완성의 sparse index
- 설정 키 / feature flag prefix 관리

## 깊이 들어가기

### 1. 왜 Trie를 압축하나

Trie는 prefix 검색이 편하지만, 문자열이 길고 분기 수가 적으면 노드가 너무 많아진다.  
예를 들어 `spring`, `spring-boot`, `spring-security`처럼 앞부분이 긴 문자열이 많을수록 중복 경로가 비싸다.

Radix Tree는 이런 구간을 하나의 edge로 묶어버린다.

- `s -> p -> r -> i -> n -> g`
- `spring`

같은 prefix를 하나의 레이블로 보관하면, 공통 경로를 더 적은 객체로 표현할 수 있다.

### 2. 노드와 edge 설계

Radix Tree에서는 node보다 **edge label 관리**가 중요하다.

- 각 edge는 `"prefix"` 같은 문자열 조각을 가진다.
- 노드는 여러 edge를 자식으로 가진다.
- 삽입 시 기존 edge를 쪼개거나 합칠 수 있어야 한다.

이 때문에 구현 난이도는 일반 Trie보다 높다.

### 3. split과 merge가 핵심이다

삽입할 때 새 문자열이 기존 edge와 부분적으로만 일치하면 edge를 분할해야 한다.

예:

- 기존 edge: `"spring"`
- 새 문자열: `"sprout"`

공통 prefix `"spr"`를 기준으로 edge를 두 갈래로 나눠야 한다.

삭제 후에는 자식이 하나뿐인 노드를 다시 합쳐서 압축 상태를 유지할 수 있다.

### 4. backend에서 유용한 이유

Radix Tree는 "문자열을 빠르게 찾는다"보다 "많은 prefix 규칙을 깔끔하게 관리한다"는 쪽이 더 중요하다.

- 라우팅 테이블이 길고 비슷한 prefix를 공유할 때
- 디렉터리 구조처럼 계층형 문자열을 다룰 때
- IP prefix처럼 공통 앞부분이 많은 규칙을 다룰 때

이때 일반 Trie보다 메모리 점유가 작고, prefix 매칭도 자연스럽다.

## 실전 시나리오

### 시나리오 1: URL 라우터

`/api/orders`, `/api/orders/history`, `/api/order-items` 같은 경로가 많다면 Radix Tree가 잘 맞는다.  
공통 prefix를 압축해 두면 라우팅 테이블이 더 작아지고, prefix 기반 매칭도 간단해진다.

### 시나리오 2: CIDR / IP prefix

네트워크에서 `10.0.0.0/8`, `10.1.0.0/16` 같은 prefix 규칙을 찾을 때 압축 구조가 잘 맞는다.  
같은 prefix를 공유하는 경로가 많을수록 Radix Tree의 장점이 커진다.

### 시나리오 3: autocomplete의 sparse index

검색어가 너무 많아서 일반 Trie의 노드 수가 부담될 때, 자주 등장하는 prefix만 압축해서 관리할 수 있다.

### 시나리오 4: 구성 키 prefix 관리

`payment.timeout`, `payment.retry.count`, `payment.retry.backoff`처럼 점 구분 키가 많으면 계층형 prefix를 압축해서 저장하기 좋다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class RadixTree {
    private static final class Node {
        Map<String, Node> edges = new HashMap<>();
        boolean isWord;
    }

    private final Node root = new Node();

    public void insert(String word) {
        insert(root, word);
    }

    private void insert(Node current, String word) {
        for (String edge : new ArrayList<>(current.edges.keySet())) {
            Node child = current.edges.get(edge);
            int lcp = longestCommonPrefix(edge, word);
            if (lcp == 0) continue;

            if (lcp == edge.length() && lcp == word.length()) {
                child.isWord = true;
                return;
            }

            if (lcp == edge.length()) {
                insert(child, word.substring(lcp));
                return;
            }

            Node split = new Node();
            split.edges.put(edge.substring(lcp), child);
            split.isWord = lcp == word.length();

            current.edges.remove(edge);
            current.edges.put(edge.substring(0, lcp), split);

            if (lcp < word.length()) {
                split.edges.put(word.substring(lcp), new Node());
                split.edges.get(word.substring(lcp)).isWord = true;
            }
            return;
        }

        Node leaf = new Node();
        leaf.isWord = true;
        current.edges.put(word, leaf);
    }

    public boolean search(String word) {
        return search(root, word);
    }

    private boolean search(Node current, String word) {
        if (word.isEmpty()) {
            return current.isWord;
        }

        for (Map.Entry<String, Node> entry : current.edges.entrySet()) {
            String edge = entry.getKey();
            if (word.startsWith(edge)) {
                return search(entry.getValue(), word.substring(edge.length()));
            }
        }
        return false;
    }

    private int longestCommonPrefix(String a, String b) {
        int len = Math.min(a.length(), b.length());
        int i = 0;
        while (i < len && a.charAt(i) == b.charAt(i)) {
            i++;
        }
        return i;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Trie | 구현이 단순하고 prefix 검색이 직관적이다 | 노드 수가 많아 메모리를 많이 쓴다 | 문자 집합이 작고 규칙이 단순할 때 |
| Radix Tree | 중복 prefix를 압축해 메모리를 절약한다 | split/merge가 복잡하다 | prefix가 길고 sparse할 때 |
| HashMap 인덱스 | exact lookup이 매우 빠르다 | prefix 검색이 어렵다 | 정확한 키 조회만 필요할 때 |

Radix Tree는 "빠른 exact lookup"보다 "prefix를 다루는 구조적 효율"이 중요할 때 선택한다.

## 꼬리질문

> Q: Radix Tree가 Trie보다 항상 좋은가?
> 의도: 압축의 장단점을 구분하는지 확인
> 핵심: 아니다. 데이터가 촘촘하고 분기가 많으면 일반 Trie가 더 단순할 수 있다.

> Q: split 로직이 왜 어려운가?
> 의도: edge label 분해와 구조 유지 이해 확인
> 핵심: 기존 경로와 새 문자열의 공통 prefix를 기준으로 구조를 다시 짜야 하기 때문이다.

> Q: backend에서 가장 큰 이점은 무엇인가?
> 의도: 실무적 판단 감각 확인
> 핵심: prefix rule이 많은 테이블을 메모리 효율적으로 관리할 수 있다는 점이다.

## 한 줄 정리

Radix Tree는 Trie의 prefix 검색 능력을 유지하면서, 긴 공통 경로를 압축해 저장 효율을 높이는 자료구조다.
