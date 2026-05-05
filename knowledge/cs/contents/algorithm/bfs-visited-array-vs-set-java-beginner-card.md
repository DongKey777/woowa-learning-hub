---
schema_version: 3
title: Java BFS visited 배열 vs Set beginner card
concept_id: algorithm/bfs-visited-array-vs-set-java-beginner-card
canonical: false
category: algorithm
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- visited-representation-choice
- sparse-id-modeling
- boolean-array-vs-hashset
aliases:
- java bfs visited array vs set
- bfs boolean array or hashset
- visited boolean array java
- visited set java bfs
- sparse id bfs visited
- string key bfs visited
- bfs visited 뭐 써요
- bfs set 말고 배열 써도 되나
- bfs visited 처음 배우는데
- java graph traversal visited choice
- unweighted graph visited tracking
- java bfs beginner visited
- boolean array vs hashset bfs
symptoms:
- Java BFS에서 방문 체크를 배열로 둘지 Set으로 둘지 기준이 안 서
- 정점 번호가 듬성듬성할 때도 boolean 배열을 써도 되는지 헷갈려
- 문자열 key 그래프를 BFS로 돌릴 때 visited 표현을 어떻게 바꿔야 할지 모르겠어
intents:
- comparison
- design
prerequisites:
- algorithm/dfs-bfs-intro
- data-structure/map-vs-set-requirement-bridge
next_docs:
- algorithm/bfs-vs-dijkstra-shortest-path-mini-card
- algorithm/shortest-path-reconstruction-bridge
linked_paths:
- contents/algorithm/dfs-bfs-intro.md
- contents/algorithm/bfs-vs-dijkstra-shortest-path-mini-card.md
- contents/data-structure/graph-basics.md
- contents/data-structure/map-vs-set-requirement-bridge.md
- contents/data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md
confusable_with:
- data-structure/map-vs-set-requirement-bridge
- data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer
forbidden_neighbors:
- contents/data-structure/map-vs-set-requirement-bridge.md
- contents/data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md
expected_queries:
- Java BFS에서 정점 번호가 0부터 촘촘할 때 visited를 왜 boolean 배열로 두는 게 편해?
- 노드 id가 sparse하면 BFS 방문 체크를 배열 대신 Set으로 바꿔야 하는 이유를 알려줘
- 문자열 key 그래프를 BFS로 돌릴 때 visited 자료구조를 어떻게 선택해?
- boolean[] visited와 HashSet visited를 고르는 기준을 BFS 초보자 관점으로 비교해줘
- 방문 여부 말고 거리나 parent도 같이 저장해야 할 때는 언제 Map 쪽으로 넘어가야 해?
contextual_chunk_prefix: |
  이 문서는 Java BFS를 처음 구현할 때 visited를 boolean 배열로 둘지 Set으로 고르는 chooser다. 번호를 바로 칸 위치로 써도 되는지, 노드 이름이 듬성듬성하거나 문자열인지, 본 적 있나만 기억하면 되는지, 거리와 parent까지 함께 들고 가야 하는지, 배열 접근과 key 기반 저장 중 무엇이 자연스러운지 같은 자연어 paraphrase가 본 문서의 선택 기준에 매핑된다.
---
# Java BFS visited 배열 vs Set beginner card

> 한 줄 요약: Java BFS에서 노드 번호가 `0..n-1`처럼 촘촘하고 크기를 알면 `boolean[]`이 가장 단순하고, id가 듬성듬성하거나 문자열 key면 `Set`이 더 자연스럽다.

**난이도: 🟢 Beginner**

관련 문서:

- [DFS와 BFS 입문](./dfs-bfs-intro.md)
- [BFS vs 0-1 BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- [algorithm 카테고리 인덱스](./README.md)
- [그래프 기초](../data-structure/graph-basics.md)
- [Map vs Set Requirement Bridge](../data-structure/map-vs-set-requirement-bridge.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](../data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md)

retrieval-anchor-keywords: java bfs visited array vs set, bfs boolean array or hashset, visited boolean array java, visited set java bfs, sparse id bfs visited, string key bfs visited, bfs visited 뭐 써요, bfs set 말고 배열 써도 되나, bfs visited 처음 배우는데, java graph traversal visited choice, unweighted graph visited tracking, java bfs beginner visited, boolean array vs hashset bfs

## 핵심 개념

처음엔 이렇게만 자르면 된다.

- 노드 번호가 `0, 1, 2, ... n-1`처럼 촘촘하다 -> `boolean[] visited`
- 노드 id가 `100, 2050, 999999`처럼 듬성듬성하다 -> `Set<Integer>` 또는 `Set<Long>`
- 노드가 `"SEOUL"`, `"A-17"`, `"user:42"` 같은 문자열 key다 -> `Set<String>`

핵심은 BFS 자체가 아니라 **노드를 어떻게 식별하느냐**다.
방문 체크는 "이 노드를 이미 큐에 넣었나?"만 답하면 되므로,
id를 배열 index로 바로 바꿀 수 있으면 배열이 가장 단순하고,
그럴 수 없으면 `Set`이 더 자연스럽다.

## 한눈에 보기

| 상황 | 추천 기본값 | 왜 이쪽이 쉬운가 |
|---|---|---|
| 정점 수 `n`이 있고 번호가 `0..n-1` | `boolean[]` | index로 바로 접근한다 |
| 정점 번호가 크고 비어 있는 구간이 많다 | `Set<Integer>` | 본 정점만 저장하면 된다 |
| 노드 key가 문자열이다 | `Set<String>` | 배열 index로 바꾸기 어렵다 |
| 나중에 `거리`, `parent`, `timestamp`도 같이 저장해야 한다 | `Map` 계열 검토 | 방문 여부만으로 안 끝난다 |

짧게 외우면:

> **배열은 "자리"가 있을 때**, `Set`은 **"이름표"만 있을 때** 쓴다.

## 왜 둘이 갈리나

`boolean[]`은 "방 번호가 이미 정해진 아파트"에 가깝다.
`visited[7]`처럼 바로 7번 칸을 찍으면 된다.

반면 `Set`은 "방 번호 체계가 없고 이름표만 있는 명단"에 가깝다.
`visited.contains("SEOUL")`처럼 key 자체를 저장한다.

그래서 초보자 판단 기준은 아래 두 가지면 충분하다.

1. 이 노드를 배열 index 하나로 바로 바꿀 수 있는가?
2. 전체 범위를 미리 다 만들어도 낭비가 크지 않은가?

둘 다 `yes`면 배열이 편하고, 하나라도 `no`면 `Set`이 안전하다.

## 자바 BFS에서 쓰는 모습

### 1. 번호가 촘촘한 그래프면 `boolean[]`

```java
boolean[] visited = new boolean[n];
Queue<Integer> queue = new ArrayDeque<>();

visited[start] = true;
queue.offer(start);

while (!queue.isEmpty()) {
    int cur = queue.poll();
    for (int next : graph[cur]) {
        if (visited[next]) {
            continue;
        }
        visited[next] = true;
        queue.offer(next);
    }
}
```

이 패턴은 `1번부터 n번까지`, `0번부터 n-1번까지`처럼 범위가 분명할 때 가장 읽기 쉽다.

### 2. id가 sparse하면 `Set<Integer>`

```java
Set<Integer> visited = new HashSet<>();
Queue<Integer> queue = new ArrayDeque<>();

visited.add(start);
queue.offer(start);

while (!queue.isEmpty()) {
    int cur = queue.poll();
    for (int next : graph.getOrDefault(cur, List.of())) {
        if (!visited.add(next)) {
            continue;
        }
        queue.offer(next);
    }
}
```

`visited.add(next)`가 `true`면 처음 본 노드, `false`면 이미 본 노드다.
즉 membership 확인과 삽입을 한 줄로 같이 처리할 수 있다.

### 3. 문자열 key면 `Set<String>`

```java
Set<String> visited = new HashSet<>();
Queue<String> queue = new ArrayDeque<>();
```

역 이름, 파일 이름, 사용자 key처럼 문자열을 그대로 다루는 BFS라면 보통 이쪽이 더 자연스럽다.

## 흔한 오해와 함정

- "`Set`이 더 고급이라서 BFS에서도 항상 더 좋은가요?"  
  아니다. 정점 번호가 촘촘하면 `boolean[]`이 더 단순하다.
- "`boolean[]`만 써야 진짜 BFS인가요?"  
  아니다. 탐색 순서를 큐가 만들면 BFS다. 방문 기록 도구는 배열이어도, `Set`이어도 된다.
- "`visited`는 큐에서 꺼낼 때 표시하면 되나요?"  
  아니다. **큐에 넣을 때** 표시해야 중복 삽입을 막는다.
- "정점 번호가 `1`과 `1_000_000` 두 개뿐이어도 배열이 낫나요?"  
  아니다. 이런 sparse id는 `boolean[1_000_001]`가 낭비가 크니 `Set`이 더 자연스럽다.
- "문자열 key BFS도 배열로 바꾸면 더 빠르지 않나요?"  
  가능은 하지만 초급 단계에서는 먼저 `Set<String>`으로 맞게 푸는 편이 좋다. 성능이 정말 아쉬울 때만 `문자열 -> 압축된 int id`로 내려가면 된다.

## 실무에서 읽는 기준

| 문제 문장 | 보통 더 자연스러운 선택 | 이유 |
|---|---|---|
| `1번 학생부터 n번 학생까지 친구 관계` | `boolean[]` | 번호 범위가 고정돼 있다 |
| `도시 코드가 100, 3500, 98000처럼 띄엄띄엄 등장` | `Set<Integer>` | 전체 범위를 배열로 잡기 애매하다 |
| `역 이름`, `파일 경로`, `문자열 상태`를 노드로 탐색 | `Set<String>` | 숫자 index가 없다 |
| `문자열이지만 반복이 많고 성능이 부족하다` | 먼저 `Set<String>`, 필요시 id 압축 | correctness를 먼저 맞춘 뒤 최적화한다 |

입문자에게는 "배열이 더 빠르다"보다 **"무리 없이 index를 만들 수 있나"**가 먼저다.
index가 자연스럽지 않으면 `Set`으로 시작하는 편이 실수가 적다.

## 더 깊이 가려면

- BFS의 기본 흐름과 `큐에 넣을 때 visited 표시` 원칙은 [DFS와 BFS 입문](./dfs-bfs-intro.md)
- shortest-path 분기가 함께 헷갈리면 [BFS vs 0-1 BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- `Set`으로 끝나는지 `Map`으로 커지는지 헷갈리면 [Map vs Set Requirement Bridge](../data-structure/map-vs-set-requirement-bridge.md)
- `HashMap`/`LinkedHashMap`/`TreeMap` 선택까지 넓히려면 [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](../data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md)

## 면접/시니어 질문 미리보기

1. `boolean[]` 대신 `Set<Integer>`를 쓰는 기준은 무엇인가요?  
   정점 번호가 촘촘한지, sparse한지, 그리고 배열 index로 자연스럽게 바꿀 수 있는지가 기준이다.
2. 문자열 그래프 BFS는 왜 `Set<String>`으로 시작하나요?  
   문자열을 배열 index로 바로 쓰기 어렵고, 초반에는 correctness가 더 중요하기 때문이다.
3. `Set<String>`이 느리면 어떻게 하나요?  
   문자열을 `int id`로 압축한 뒤 `boolean[]`나 `BitSet` 쪽으로 내려갈 수 있다. 하지만 그건 최적화 단계다.

## 한 줄 정리

Java BFS의 방문 체크는 `번호가 촘촘하면 boolean[]`, `id가 sparse하거나 문자열 key면 Set`으로 자르면 초급자의 `visited` 선택 실수가 크게 줄어든다.
