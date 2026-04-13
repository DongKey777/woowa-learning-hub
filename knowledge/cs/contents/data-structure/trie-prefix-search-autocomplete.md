# Trie (Prefix Search / Autocomplete)

> 한 줄 요약: Trie는 문자열의 공통 접두사를 공유해 prefix search와 autocomplete, top-k suggestion을 빠르게 만드는 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
> - [Skip List](./skip-list.md)
> - [Search 시스템 설계](../system-design/search-system-design.md)

> retrieval-anchor-keywords: trie, prefix tree, digital search tree, retrieval tree, autocomplete, prefix search, top-k autocomplete, suggestion ranking, search-as-you-type, prefix frequency, radix tree

## 핵심 개념

Trie는 문자열을 문자 단위로 쪼개서 저장하는 트리다.  
문자열 전체를 하나의 key로 다루는 `HashMap`과 달리, Trie는 **접두사(prefix)를 공유**한다.

이 구조가 중요한 이유는 검색 UI에서 자주 나오는 질문이 "정확히 이 단어가 있나?"보다 "이 접두사로 시작하는 단어가 뭐가 있나?"이기 때문이다.

- 사전 검색
- 자동완성
- 금칙어 필터
- URL path 라우팅
- 사전 기반 spell check

Trie의 기본 노드는 보통 다음 두 가지를 가진다.

- `children`: 다음 문자로 이어지는 자식 노드들
- `isWord`: 현재 노드가 단어의 끝인지 여부

여기에 실전에서는 다음 필드를 더 붙이기도 한다.

- `passCount`: 이 노드를 지나가는 단어 수
- `wordCount`: 정확히 이 단어로 끝나는 횟수
- `topSuggestions`: prefix별 상위 추천어 캐시

## 깊이 들어가기

### 1. 왜 Trie가 필요한가

`HashMap<String, ?>`으로도 정확한 문자열 조회는 빠르다.  
하지만 `"app"`으로 시작하는 단어를 찾으려면 매 문자열을 전부 비교해야 한다.

Trie는 접두사를 따라 내려가기만 하면 되므로 prefix search가 자연스럽다.

- exact lookup: `O(m)`
- prefix lookup: `O(m)`
- prefix 이후 후보 수집: 후보 개수에 따라 추가 비용 발생

여기서 `m`은 문자열 길이다.

### 2. 노드 설계

Trie 노드 설계는 성능보다 **문자 집합과 기능 요구사항**에 맞춰야 한다.

| 설계 방식 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| `TrieNode[] children = new TrieNode[26]` | 빠르고 단순하다 | 소문자 영어에만 잘 맞고 메모리를 많이 쓴다 | 알고리즘 문제, 제한된 문자 집합 |
| `Map<Character, TrieNode>` | 문자 집합이 넓어도 유연하다 | 해시 오버헤드가 있다 | 한글, URL, 다양한 토큰 |
| 압축 Trie(Radix Tree) | 공통 경로를 더 압축한다 | 구현이 어렵다 | 대규모 prefix index |

문자 집합이 작은데도 `Map`을 쓰면 유연성은 좋지만 오버헤드가 늘고,  
문자 집합이 큰데도 배열을 쓰면 공간이 급격히 낭비된다.

### 3. Prefix Search의 본질

prefix search는 두 단계다.

1. prefix 자체를 Trie에서 찾는다.
2. 그 노드 아래를 순회하며 후보를 모은다.

prefix 탐색만 보면 빠르지만, 실제 자동완성은 **후보 생성 + 랭킹**까지 봐야 한다.  
즉 Trie는 "찾기"를 빠르게 하고, "고르기"는 별도로 생각해야 한다.

### 4. Autocomplete와 top-k 확장

자동완성에서 가장 흔한 실전 요구는 다음과 같다.

- 접두사에 맞는 후보를 보여준다.
- 후보가 너무 많으면 상위 k개만 보여준다.
- 점수는 빈도, 최신성, 클릭률, 정확 일치 여부를 반영한다.

구현 방식은 크게 두 가지다.

| 방식 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| on-demand DFS + heap | 구현이 쉽고 저장 공간이 적다 | 질의 때마다 후보를 많이 훑을 수 있다 | 데이터가 작거나 prefix가 적을 때 |
| node별 top-k 캐시 | 질의가 빠르다 | insert/update 비용과 메모리가 늘어난다 | 검색 서비스, 실시간 autocomplete |

실서비스에서는 보통 빈도가 높은 prefix를 미리 캐시하고, 나머지는 on-demand로 보완한다.

### 5. 메모리 트레이드오프

Trie의 가장 큰 문제는 **문자 하나마다 노드가 늘어난다**는 점이다.  
단어 수가 많아질수록 노드 수가 급증하고, 자식 배열을 고정 길이로 잡으면 공간 낭비가 심해진다.

이럴 때 고려하는 대안은 다음과 같다.

- 자식 배열 대신 `Map` 사용
- 압축 Trie(Radix Tree) 사용
- 자주 쓰는 prefix만 hot cache로 따로 보관
- `passCount`가 0인 노드는 pruning

`HashMap` 문서를 같이 보면, 자식 노드를 `Map`으로 둘 때 왜 메모리와 탐색성 사이의 trade-off가 생기는지 이해하기 좋다.  
`Skip List` 문서는 "정렬된 순서 + 범위 조회" 관점에서 Trie의 대안 또는 보완재를 생각할 때 도움이 된다.

### 6. Search 시스템과의 연결

Trie는 검색 시스템 전체가 아니라, **검색 시스템의 일부**다.  
자동완성이나 prefix suggestion은 Trie가 잘 맞지만, 전체 검색 엔진은 더 많은 문제를 푼다.

- 문서 수집
- 정규화
- 토큰화
- 역인덱스
- 랭킹
- freshness
- hot query

즉 `Search 시스템 설계` 문서에서 말하는 전체 파이프라인 안에서, Trie는 보통 suggestion layer나 prefix index 역할을 맡는다.

## 실전 시나리오

### 시나리오 1: 검색창 자동완성

사용자가 `spr`를 입력했을 때 다음을 빠르게 보여줘야 한다.

- `spring`
- `spring boot`
- `spring security`

이때 full-text search는 과하고, HashMap exact lookup은 부족하다.  
Trie는 prefix를 바로 따라가서 후보를 뽑기에 적합하다.

### 시나리오 2: 금칙어 필터

금칙어가 수만 개일 때, 문장 전체를 하나씩 비교하는 방식은 비효율적이다.  
Trie는 문자열을 앞에서부터 따라가면서 빠르게 매칭할 수 있어 필터링에 자주 쓴다.

### 시나리오 3: 사전 기반 spell check

오타 허용 spell check에서는 Trie를 기반으로 근접 후보를 찾고,  
편집 거리(edit distance)와 랭킹을 조합한다.  
Trie 단독으로 끝나지 않고, 추천 점수 계산과 이어지는 경우가 많다.

### 시나리오 4: 서비스 내부 route prefix 매칭

`/api/orders`, `/api/order-items`, `/api/orders/history` 같은 path를 다루면 prefix 탐색이 유용하다.  
라우팅 테이블 자체를 Trie로 두면 공통 prefix를 쉽게 공유할 수 있다.

## 코드로 보기

### 기본 Trie

```java
import java.util.HashMap;
import java.util.Map;

class TrieNode {
    Map<Character, TrieNode> children = new HashMap<>();
    boolean isWord;
    int passCount;
    int wordCount;
}

public class Trie {
    private final TrieNode root = new TrieNode();

    public void insert(String word) {
        TrieNode current = root;
        current.passCount++;
        for (int i = 0; i < word.length(); i++) {
            char c = word.charAt(i);
            current = current.children.computeIfAbsent(c, key -> new TrieNode());
            current.passCount++;
        }
        current.isWord = true;
        current.wordCount++;
    }

    public boolean search(String word) {
        TrieNode node = findNode(word);
        return node != null && node.isWord;
    }

    public boolean startsWith(String prefix) {
        return findNode(prefix) != null;
    }

    public int countPrefix(String prefix) {
        TrieNode node = findNode(prefix);
        return node == null ? 0 : node.passCount;
    }

    private TrieNode findNode(String text) {
        TrieNode current = root;
        for (int i = 0; i < text.length(); i++) {
            current = current.children.get(text.charAt(i));
            if (current == null) {
                return null;
            }
        }
        return current;
    }
}
```

### Autocomplete top-k

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;

class Suggestion {
    final String word;
    final int score;

    Suggestion(String word, int score) {
        this.word = word;
        this.score = score;
    }
}

class AutoCompleteTrie {
    private final TrieNode root = new TrieNode();
    private final Map<String, Integer> frequency = new HashMap<>();

    public void insert(String word) {
        frequency.put(word, frequency.getOrDefault(word, 0) + 1);

        TrieNode current = root;
        for (int i = 0; i < word.length(); i++) {
            char c = word.charAt(i);
            current = current.children.computeIfAbsent(c, key -> new TrieNode());
        }
        current.isWord = true;
        current.wordCount++;
    }

    public List<String> autocomplete(String prefix, int k) {
        TrieNode node = findNode(prefix);
        if (node == null) {
            return List.of();
        }

        PriorityQueue<Suggestion> heap = new PriorityQueue<>(
            Comparator.comparingInt((Suggestion s) -> s.score)
                .thenComparing((a, b) -> b.word.compareTo(a.word))
        );

        dfs(node, new StringBuilder(prefix), heap, k);

        List<String> result = new ArrayList<>();
        while (!heap.isEmpty()) {
            result.add(0, heap.poll().word);
        }
        return result;
    }

    private void dfs(TrieNode node, StringBuilder path, PriorityQueue<Suggestion> heap, int k) {
        if (node.isWord) {
            String word = path.toString();
            int score = frequency.getOrDefault(word, 0);
            heap.offer(new Suggestion(word, score));
            if (heap.size() > k) {
                heap.poll();
            }
        }

        for (Map.Entry<Character, TrieNode> entry : node.children.entrySet()) {
            path.append(entry.getKey());
            dfs(entry.getValue(), path, heap, k);
            path.deleteCharAt(path.length() - 1);
        }
    }

    private TrieNode findNode(String text) {
        TrieNode current = root;
        for (int i = 0; i < text.length(); i++) {
            current = current.children.get(text.charAt(i));
            if (current == null) {
                return null;
            }
        }
        return current;
    }
}
```

### 실전 사용 예시

```java
AutoCompleteTrie trie = new AutoCompleteTrie();
trie.insert("spring");
trie.insert("spring boot");
trie.insert("spring security");
trie.insert("sql");
trie.insert("skip list");

System.out.println(trie.autocomplete("sp", 3));
// [spring, spring boot, spring security]
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `Trie` | prefix search와 autocomplete가 빠르다 | 메모리를 많이 쓴다 | 검색창, 사전, prefix routing |
| `HashMap<String, ?>` | exact lookup이 간단하고 빠르다 | prefix search는 비싸다 | 정확한 key 조회 |
| `TreeMap` | 정렬과 범위 조회가 편하다 | prefix 자체에는 특화되지 않는다 | lexicographic range가 중요할 때 |
| `Skip List` | 정렬 유지와 범위 조회가 쉽다 | prefix 공유는 못 한다 | ordered suggestion, range-based search |
| `Radix Tree` | Trie보다 메모리를 절약한다 | 구현이 복잡하다 | 대규모 prefix index |

핵심 판단 기준은 이렇다.

- prefix로 시작하는 후보를 자주 찾으면 Trie
- exact match만 필요하면 HashMap
- 정렬된 범위 조회가 중요하면 TreeMap 또는 Skip List
- 메모리가 더 중요하면 Radix Tree

## 꼬리질문

> Q: Trie가 HashMap보다 prefix search에서 유리한 이유는 무엇인가요?
> 의도: 문자열 exact lookup과 prefix 탐색의 차이를 이해하는지 확인
> 핵심: Trie는 접두사를 구조적으로 공유하므로 prefix를 따라 내려가면 후보 구간을 바로 찾을 수 있다.

> Q: Trie는 왜 메모리를 많이 쓰나요?
> 의도: 공간 복잡도와 구조적 중복을 설명할 수 있는지 확인
> 핵심: 문자마다 노드가 늘고 자식 배열이나 Map 오버헤드가 커지며, 공통 prefix가 적을수록 낭비가 커진다.

> Q: autocomplete에서 top-k를 Trie에 저장하는 것과 매번 DFS로 찾는 것의 차이는 무엇인가요?
> 의도: 조회 속도와 갱신 비용의 trade-off를 아는지 확인
> 핵심: 미리 저장하면 조회는 빠르지만 삽입/갱신과 메모리가 무거워지고, DFS는 반대로 조회 시 비용이 든다.

> Q: 검색 시스템 전체에서 Trie는 어떤 역할인가요?
> 의도: Trie를 단독 도구가 아니라 시스템 일부로 보는지 확인
> 핵심: 보통 prefix suggestion, autocomplete, hot query 보조 인덱스 역할을 하고, ranking/freshness는 별도 계층이 맡는다.

> Q: Trie 대신 Skip List를 고려할 수 있는 경우는 언제인가요?
> 의도: 자료구조 선택을 기능 요구사항으로 판단하는지 확인
> 핵심: prefix 공유보다 정렬된 순서와 범위 조회가 더 중요하면 Skip List나 TreeMap이 더 적합할 수 있다.

## 한 줄 정리

Trie는 접두사를 공유하는 구조 덕분에 prefix search와 autocomplete를 빠르게 만들지만, 메모리 비용이 커서 top-k 캐시나 radix tree 같은 확장 전략을 함께 고민해야 한다.
