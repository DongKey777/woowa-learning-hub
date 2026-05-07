---
schema_version: 3
title: Data Structure 자료구조 라우팅 인덱스
concept_id: data-structure/data-structure-routing-index
canonical: true
category: data-structure
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 93
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- data-structure-first-router
- map-set-queue-tree-split
- beginner-navigation
aliases:
- data structure readme
- 자료구조 처음 라우터
- map set queue tree 뭐부터
- beginner data structure routing
- 자료구조 입구 문서
- queue bfs map set 차이
- TreeMap TreeSet PriorityQueue 선택
symptoms:
- 처음 자료구조를 볼 때 map, set, queue, tree 중 어디서 시작할지 모르겠다
- queue와 BFS, TreeSet과 PriorityQueue, HashMap과 TreeMap이 같은 층위처럼 보여 분기가 섞인다
- 정렬, 범위 조회, 이웃 값, FIFO 순서, 중복 제거 중 어떤 요구가 먼저인지 문제 문장에서 못 자른다
intents:
- troubleshooting
- comparison
- definition
prerequisites:
- language/java-collections-basics
next_docs:
- data-structure/backend-data-structure-starter-pack
- data-structure/map-set-queue-priorityqueue-trie-bitmap-selection-primer
- data-structure/map-vs-set-requirement-bridge
- data-structure/queue-vs-deque-vs-priority-queue-primer
- data-structure/connectivity-question-router
- algorithm/dfs-bfs-intro
linked_paths:
- contents/language/java/java-collections-basics.md
- contents/data-structure/backend-data-structure-starter-pack.md
- contents/data-structure/map-set-queue-priorityqueue-trie-bitmap-selection-primer.md
- contents/data-structure/map-vs-set-requirement-bridge.md
- contents/data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md
- contents/data-structure/hashset-vs-treeset-beginner-bridge.md
- contents/data-structure/treeset-vs-priorityqueue-neighbor-choice-card.md
- contents/data-structure/queue-vs-deque-vs-priority-queue-primer.md
- contents/data-structure/queue-bfs-priorityqueue-map-lookup-micro-drill.md
- contents/data-structure/connectivity-question-router.md
- contents/algorithm/dfs-bfs-intro.md
confusable_with:
- data-structure/backend-data-structure-starter-pack
- language/java-collections-basics
- algorithm/dfs-bfs-intro
- data-structure/queue-basics
- data-structure/map-vs-set-requirement-bridge
forbidden_neighbors: []
expected_queries:
- 자료구조 처음인데 Map Set Queue Tree 중 무엇부터 봐야 해?
- queue랑 BFS가 왜 같이 나오고 어떻게 분리해야 하는지 알려줘
- HashMap TreeMap TreeSet PriorityQueue를 문제 문장으로 구분하고 싶어
- 정렬 범위 조회 이웃 값이 보이면 어떤 자료구조로 가야 해?
- 중복 제거와 key 조회와 FIFO 순서를 처음에 어떻게 나눠야 해?
contextual_chunk_prefix: |
  이 문서는 자료구조 카테고리의 beginner 라우팅 인덱스다. 학습자가
  Map, Set, Queue, Deque, PriorityQueue, TreeMap, TreeSet, Trie, Bitmap,
  Graph, BFS를 한꺼번에 같은 층위로 읽지 않도록 문제 문장을 요구 신호로
  번역한다. 중복 제거, key 조회, FIFO 순서, 정렬/범위 조회, 이웃 값,
  연결성 질문을 첫 분기로 삼는다.
---
# Data Structure (자료구조)

> 한 줄 요약: 자료구조 README는 백엔드 주니어가 `map`, `queue`, `tree` 계열을 헷갈릴 때 문제 문장을 먼저 번역해 출발점을 고르게 돕는 입구 문서다.

**난이도: 🟢 Beginner**

관련 문서:

- [큐 기초](./queue-basics.md)
- [덱 기초](./deque-basics.md)
- [Map vs Set vs Queue vs Priority Queue vs Trie vs Bitmap 선택 프라이머](./map-set-queue-priorityqueue-trie-bitmap-selection-primer.md)
- [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md)
- [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md)
- [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md)
- [TreeSet vs PriorityQueue Neighbor-Choice Card](./treeset-vs-priorityqueue-neighbor-choice-card.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [Map order symptom router card](./map-order-symptom-router-card.md)
- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [Queue vs BFS vs Priority Queue vs Map Lookup Micro Drill](./queue-bfs-priorityqueue-map-lookup-micro-drill.md)
- [Connectivity Question Router](./connectivity-question-router.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- [Backend Data-Structure Starter Pack](./backend-data-structure-starter-pack.md)

retrieval-anchor-keywords: data structure readme, beginner data structure routing, hashmap treemap linkedhashmap primer, queue deque priority queue, connectivity router, queue는 fifo 순서를 만드는 도구, bfs는 level-order 레벨 순서 탐색, 자료구조 처음인데 뭐부터, map set queue tree 뭐부터, set map 차이 처음, queue deque 차이 처음, deque가 뭐예요, treemap 왜 써요, 범위 조회 자료구조 뭐부터, bfs랑 queue 차이 뭐예요

## 길 잃었을 때 복귀 경로

길을 잃으면 아래 표에서 고르면 된다.

| 지금 헷갈리는 문장 | 여기로 되돌아오기 | 바로 다음 안전한 한 걸음 |
|---|---|---|
| `처음 자료구조라 map/set/queue 중 어디서 시작할지 모르겠어요` | [처음 15분 읽기 루트](#처음-15분-읽기-루트) | [Backend Data-Structure Starter Pack](./backend-data-structure-starter-pack.md) |
| `set인지 map인지 아직도 모르겠어요` | [먼저 자를 질문](#먼저-자를-질문) | [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md) |
| `중복 제거는 되는데 왜 TreeSet/TreeMap이 또 필요하죠?` | [증상별 빠른 길](#증상별-빠른-길) | [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md) -> [HashMap, TreeMap, LinkedHashMap Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) |
| `next smallest가 x 다음 값인지, 그냥 최소값 하나씩 꺼내는 건지 헷갈려요` | [증상별 빠른 길](#증상별-빠른-길) | [TreeSet vs PriorityQueue Neighbor-Choice Card](./treeset-vs-priorityqueue-neighbor-choice-card.md) |
| `queue를 쓰는데 FIFO 문제인지 BFS 문제인지 모르겠어요` | [초급 10초 라우터](#초급-10초-라우터) | [큐 기초](./queue-basics.md) -> [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `덱이 queue의 다른 이름인지, 양쪽에서 빼는지 헷갈려요` | [증상별 빠른 길](#증상별-빠른-길) | [덱 기초](./deque-basics.md) |
| `정렬/범위 조회가 필요한데 HashMap으로도 될지 헷갈려요`, `다음 예약, 이전 예약, 범위 조회를 같이 다뤄요` | [처음 15분 읽기 루트](#처음-15분-읽기-루트) | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) |
| `왜 lower랑 floor가 달라요?`, `exact match 포함이 헷갈려요`, `entry로 바꾸면 exact match 포함도 바뀌나요?` | [증상별 빠른 길](#증상별-빠른-길) | [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md) -> [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md) -> [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md) |

## cross-category beginner bridge

자료구조 문서를 읽다가 바로 advanced 구현체나 운영 문서로 점프하기보다, 아래처럼 `language -> data-structure -> algorithm/software-engineering` 사다리로만 움직이면 초심자 오진이 줄어든다.

| 지금 막힌 문장 | primer 사다리 | 여기서 멈춰도 되는 기준 |
|---|---|---|
| `List/Set/Map 이름은 봤는데 문제 문장을 구조로 못 옮기겠어요` | [Java 컬렉션 프레임워크 입문](../language/java/java-collections-basics.md) -> [Backend Data-Structure Starter Pack](./backend-data-structure-starter-pack.md) -> [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md) | `순서 / 중복 / key 조회` 중 무엇이 먼저인지 말할 수 있다 |
| `queue가 왜 BFS에도 나오고 worker handoff에도 나와요` | [Backend Data-Structure Starter Pack](./backend-data-structure-starter-pack.md) -> `최소 이동`이면 [Backend Algorithm Starter Pack](../algorithm/backend-algorithm-starter-pack.md), `worker 순서`면 [Service 계층 기초](../software-engineering/service-layer-basics.md) | `queue`가 FIFO 도구인지 탐색 도구인지 한 줄로 말할 수 있다 |
| `HashMap이면 됐는데 왜 TreeMap/TreeSet까지 가죠` | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) -> [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md) | `정렬/범위/이웃 값`이 실제 요구인지 분리됐다 |

- retrieval note: `queue가 왜 둘 다 나와요`, `처음 자료구조인데 service 전에 뭐부터`, `bfs랑 queue 차이 뭐예요` 같은 query는 이 사다리를 먼저 타게 만든다.
- stop rule: 아직 `최소 이동`, `worker 순서`, `정렬/범위 조회` 중 무엇이 먼저인지 못 말하면 deep dive 문서보다 위 primer 표로 돌아간다.

## 프라이머에서 다시 돌아오는 자리

primer를 읽고 분기가 다시 섞이면 아래 표에서 가장 가까운 한 줄만 고르면 된다.

| 방금 읽은 primer | 이 README에서 다시 붙일 자리 | 바로 다음 한 걸음 |
|---|---|---|
| [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md) | [증상별 빠른 길](#증상별-빠른-길) | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) |
| [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md) | [처음 15분 읽기 루트](#처음-15분-읽기-루트) | `정렬/범위`가 붙으면 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md) |
| [TreeSet vs PriorityQueue Neighbor-Choice Card](./treeset-vs-priorityqueue-neighbor-choice-card.md) | [증상별 빠른 길](#증상별-빠른-길) | `이웃`이면 [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md), `최소 추출`이면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md) |
| [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) | [초급 10초 라우터](#초급-10초-라우터) | `순서`가 흔들리면 [Map order symptom router card](./map-order-symptom-router-card.md), `범위/이웃`이 붙으면 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md) |

## 탐색/순서 프라이머에서 다시 돌아오는 자리

| 방금 읽은 primer | 이 README에서 다시 붙일 자리 | 바로 다음 한 걸음 |
|---|---|---|
| [큐 기초](./queue-basics.md) | [초급 10초 라우터](#초급-10초-라우터) | `작업 순서`면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md), `최소 이동`이면 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| [그래프 기초](./graph-basics.md) | [graph, bfs, queue가 같이 보일 때](#graph-bfs-queue가-같이-보일-때) | [Connectivity Question Router](./connectivity-question-router.md) 또는 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | [graph, bfs, queue가 같이 보일 때](#graph-bfs-queue가-같이-보일-때) | `최소 이동`이면 그대로 BFS, `작업 순서`가 먼저면 [큐 기초](./queue-basics.md), `같은 그룹/갈 수 있나`면 [Connectivity Question Router](./connectivity-question-router.md)로 다시 자른다 |
| [Queue vs BFS vs Priority Queue vs Map Lookup Micro Drill](./queue-bfs-priorityqueue-map-lookup-micro-drill.md) | [초급 10초 라우터](#초급-10초-라우터) | `FIFO handoff`면 [큐 기초](./queue-basics.md), `가까운 칸부터`면 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)으로 다시 한 줄만 고른다 |

## 탐색/순서 프라이머에서 다시 돌아오는 자리 (계속 2)

| 방금 읽은 primer | 이 README에서 다시 붙일 자리 | 바로 다음 한 걸음 |
|---|---|---|
| [Backend Data-Structure Starter Pack](./backend-data-structure-starter-pack.md) | [처음 15분 읽기 루트](#처음-15분-읽기-루트) | `lookup`이면 [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md), `FIFO`면 [큐 기초](./queue-basics.md) |
| [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md) | [초급 10초 라우터](#초급-10초-라우터) | `양쪽 끝`이면 [덱 기초](./deque-basics.md), `우선순위`면 [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md) |

## 탐색/순서 프라이머에서 다시 돌아오는 자리 (계속 3)

| 방금 읽은 primer | 이 README에서 다시 붙일 자리 | 바로 다음 한 걸음 |
|---|---|---|
| [알고리즘 README - BFS, Queue, Map 먼저 분리하기](../algorithm/README.md#bfs-queue-map-먼저-분리하기) | [graph, bfs, queue가 같이 보일 때](#graph-bfs-queue가-같이-보일-때) | `작업 순서`면 [큐 기초](./queue-basics.md), `같은 그룹/갈 수 있나`면 [Connectivity Question Router](./connectivity-question-router.md)로 다시 한 번 좁힌다 |
| [Software Engineering README - 연결해서 보면 좋은 문서](../software-engineering/README.md#연결해서-보면-좋은-문서-cross-category-bridge) | [같은 장면 번역](#같은-장면-번역) | `Service 책임`을 정리했다면 `구조 선택`, `순서 규칙`, `탐색 계산` 중 어디가 먼저인지 다시 잘라 [초급 10초 라우터](#초급-10초-라우터)나 [graph, bfs, queue가 같이 보일 때](#graph-bfs-queue가-같이-보일-때)로 복귀한다 |

## 프라이머 복귀 신호

`처음 자료구조`, `헷갈려요`, `왜 queue인데 bfs예요` 같은 query는 이 표를 먼저 탄다.
문장이 `최소 이동 횟수`, `가까운 칸부터`로 바뀌면 [알고리즘 README - BFS, Queue, Map 먼저 분리하기](../algorithm/README.md#bfs-queue-map-먼저-분리하기)로 복귀한다.
복귀 자리가 다시 흐려지면 [길 잃었을 때 복귀 경로](#길-잃었을-때-복귀-경로)에서 증상 문장을 다시 고르면 된다.

## graph, bfs, queue가 같이 보일 때

세 단어를 같은 층위로 보면 헷갈린다.

| 단어 | 먼저 이렇게 읽기 | 막힐 때 다음 문서 |
|---|---|---|
| `graph` | 점과 선으로 연결 관계를 그린 구조 | [그래프 기초](./graph-basics.md) |
| `tree` | 루트에서 내려가는 계층 구조 | [트리 기초](./tree-basics.md) |
| `bfs` / `dfs` | 그래프를 방문하는 순서 규칙 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `queue` | FIFO 순서를 만드는 도구 | [큐 기초](./queue-basics.md) |

짧게 외우면 `그래프는 일반 연결 구조`, `트리는 계층 구조`, `BFS/DFS는 탐색`, `queue는 FIFO 도구`다.
- beginner stop line: 여기서는 `graph -> bfs -> queue` 순서만 잡으면 된다. `MST`, `위상 정렬`, `가중치 최단 경로` 같은 심화 이름은 아직 붙잡지 말고, 먼저 아래 분기에서 한 장만 고른다.

처음이면 아래 한 줄 번역을 먼저 고정하면 된다.

| 지금 떠오른 말 | 실제로 먼저 묻는 것 | 첫 문서 |
|---|---|---|
| `graph가 뭐예요?` | 장면을 `정점-간선`으로 번역할 수 있는가 | [그래프 기초](./graph-basics.md) |
| `갈 수 있나?`, `같은 그룹인가?` | yes/no 연결 여부인가 | [Connectivity Question Router](./connectivity-question-router.md) |
| `아무 경로 하나만 보여줘` | shortest path가 아니라 path 1개가 필요한가 | [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md) |
| `최소 몇 번 만에 가요?` | 거리 1, 2, 3 순서 확장이 필요한가 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `왜 queue가 보여요?` | 탐색 규칙이 아니라 FIFO 도구를 묻는가 | [큐 기초](./queue-basics.md) |

## graph/bfs/queue 3줄 분기

아래 세 문장만 자르면 충분하다.

- `어떻게 연결돼 있지?` -> [그래프 기초](./graph-basics.md)
- `아무 경로 하나만 보여줄까?` -> [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md)
- `가까운 칸부터 몇 번 만에 가지?` -> [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- `먼저 들어온 작업부터 처리하지?` -> [큐 기초](./queue-basics.md)

`창고-도로-배송` 장면도 질문이 바뀌면 출발점이 달라진다.

| 같은 장면에서 나온 문장 | 실제로 먼저 답할 것 | 첫 출발점 |
|---|---|---|
| `창고 A에서 B로 갈 수 있나?` | yes/no 연결 여부 | [Connectivity Question Router](./connectivity-question-router.md) |
| `창고 A에서 B까지 아무 경로 하나만 보여줘` | 경로 하나 복원 | [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md) |
| `창고 A에서 B까지 최소 몇 번 이동하나?` | 최소 간선 수 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `배송 작업을 받은 순서대로 worker에 넘겨라` | FIFO 처리 규칙 | [큐 기초](./queue-basics.md) |

`왜 queue인데 bfs예요`, `왜 graph인데 queue 문서가 먼저예요` 같은 symptom은 표에서 `연결`, `경로 하나`, `최소 이동`, `작업 순서`를 안 자를 때 생긴다. `queue 문제`, `BFS 문제`, `priority queue 문제`, `map lookup 문제`가 한꺼번에 흔들리면 [Queue vs BFS vs Priority Queue vs Map Lookup Micro Drill](./queue-bfs-priorityqueue-map-lookup-micro-drill.md) 한 장만 보고 돌아오면 된다.

여기서 멈춰도 되는 기준은 `연결 여부`, `경로 하나`, `최소 이동 횟수`, `FIFO 작업 처리`를 말로 구분할 수 있는지다. 그 뒤에만 [그래프 관련 알고리즘](../algorithm/graph.md)의 상단 라우터로 넘어간다.

## graph/bfs 오진 바로 교정하기

처음 읽는 사람이 바로 걸러야 하는 오진도 짧게 붙여 두면 좋다.

| 헷갈린 문장 | 바로 고칠 생각 | 첫 문서 |
|---|---|---|
| `queue가 나오니까 자료구조 문제죠?` | queue는 도구일 수 있고, 질문이 `최소 이동 횟수`면 알고리즘 출발이다 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `graph가 보이면 무조건 BFS죠?` | graph는 구조 이름이고, 연결만 보면 DFS도 충분할 수 있다 | [그래프 기초](./graph-basics.md) |
| `경로를 보여 달라는데 BFS로 거리부터 구해야 하죠?` | 아니다. `아무 경로 하나`면 path reconstruction부터 본다 | [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md) |
| `왜 미로가 graph예요?` | 칸을 정점으로 바꾸면 된다 | [그래프 기초](./graph-basics.md) |

같은 장면이라도 `연결`, `경로 하나`, `최소 몇 번`, `FIFO 처리` 중 무엇을 묻는지 먼저 자르면 된다. 이 한 줄이 정리되지 않았으면 심화 그래프 문서보다 [그래프 기초](./graph-basics.md), [Shortest Path Reconstruction Bridge](../algorithm/shortest-path-reconstruction-bridge.md), [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md), [큐 기초](./queue-basics.md) 중 한 장만 다시 보는 편이 안전하다.

## 증상별 빠른 길

처음엔 이름을 다 외우기보다, 지금 막힌 문장을 beginner bridge에 바로 붙이는 편이 더 빠르다.

| 지금 보이는 증상 질문 | 먼저 볼 beginner bridge | 여기서 먼저 해결되는 혼동 |
|---|---|---|
| `중복만 막으면 되나요, 값도 같이 저장해야 하나요?`, `set이랑 map이 뭐가 달라요?` | [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md) | `membership only`와 `key -> value`를 먼저 분리한다 |
| `정수 id 집합인데 set이면 되나요, bitmap은 언제 worth it이죠?`, `dense integer id membership도 그냥 set이면 되나요?`, `id는 정수인데 sparse range라 bitset이 아깝지 않나요?` | [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md) | `membership only` 기본값, `dense integer id`, `sparse range` follow-up, compressed bitmap handoff를 함께 분리한다 |
| `대상자 선택 문제에서 set이랑 bitmap 중 뭐예요?`, `audience segment 계산은 어떤 쪽으로 먼저 자르죠?`, `sparse id면 set bitset roaring 중 뭐예요?` | [Set vs Bitmap Audience Selection Mini Drill](./set-vs-bitmap-audience-selection-mini-drill.md) | audience-selection 문장에 decision table을 바로 적용하고, sparse range follow-up도 다시 자르게 돕는다 |
| `bitset이면 충분한가요, roaring bitmap은 언제부터 봐야 해요?`, `bitset vs roaring 차이 뭐예요?` | [BitSet vs Roaring Bitmap Beginner Handoff](./bitset-vs-roaring-bitmap-beginner-handoff.md) | plain `BitSet` mental model에서 멈출 지점과 sparse range용 compressed bitmap handoff 신호를 분리한다 |
## bitmap/treeset에서 다음 한 걸음

위 표에서 bitmap 계열이나 정렬된 set 계열까지 왔다면, 다음 한 걸음은 아래처럼 다시 자르면 된다.

| 지금 보이는 후속 질문 | 먼저 볼 beginner bridge | 여기서 먼저 해결되는 혼동 |
|---|---|---|
| `plain bitset이랑 compressed bitmap은 어디서 갈리죠?`, `dense vs sparse bitmap follow-up이 필요해요`, `bitset 다음 카드로 뭘 봐야 해요?` | [Plain BitSet vs Compressed Bitmap Decision Card](./plain-bitset-vs-compressed-bitmap-decision-card.md) | dense/sparse만이 아니라 `빈 칸 비용`과 repeated exact set algebra를 함께 보게 하는 intermediate bridge다 |
| `정렬된 set이 왜 필요하죠?`, `HashSet이면 끝 아닌가요?` | [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md) | `중복 제거만`과 `정렬/이웃/범위` 요구를 분리한다 |
| `next smallest after x`, `왜 ceiling이랑 poll이 다른가요?` | [TreeSet vs PriorityQueue Neighbor-Choice Card](./treeset-vs-priorityqueue-neighbor-choice-card.md) | `ordered neighbor query`와 `repeated min extraction`을 분리한다 |

## 문자열/순서/정렬 라우터

질문 문장을 바로 붙이면 아래처럼 다시 자를 수 있다.

| 지금 보이는 증상 질문 | 먼저 볼 beginner bridge | 여기서 먼저 해결되는 혼동 |
|---|---|---|
| `문자열 key인데 Trie를 써야 하나요?`, `자동완성이 아니면 map이면 되나요?` | [Trie vs HashMap: exact lookup이냐 prefix search냐](./trie-vs-hashmap-exact-lookup-beginner-card.md) | exact string lookup과 prefix search를 먼저 분리한다 |
| `문자열 key인데 prefix search와 사전순 다음 key가 헷갈려요`, `Trie랑 TreeMap이 둘 다 문자열 검색 같아요` | [Trie Prefix Search vs TreeMap Ordered Map Beginner Card](./trie-prefix-search-vs-treemap-ordered-map-beginner-card.md) | prefix 후보 묶음과 ordered neighbor/range를 먼저 분리한다 |
| `queue가 뭐예요?`, `왜 BFS랑 queue가 같이 나오죠?` | [큐 기초](./queue-basics.md) | FIFO 도구와 BFS 탐색을 먼저 분리한다 |
| `queue인지 BFS인지 priority queue인지 map lookup인지 한 줄 문제에서 헷갈려요` | [Queue vs BFS vs Priority Queue vs Map Lookup Micro Drill](./queue-bfs-priorityqueue-map-lookup-micro-drill.md) | 초급 분류 문장을 4가지로 빠르게 자른다 |
| `최단 경로에서 BFS, 0-1 BFS, Dijkstra를 어떻게 나누죠?` | [BFS vs 0-1 BFS vs Dijkstra 한 줄 분류 카드](./bfs-zero-one-bfs-dijkstra-one-line-classification-card.md) | `최소 이동 횟수`, `0/1 비용`, `일반 비용 합`을 shortest-path 문장에서 바로 자른다 |
| `deque가 뭐예요?`, `queue랑 뭐가 달라요?`, `양쪽에서 빼는 게 왜 필요하죠?` | [덱 기초](./deque-basics.md) | plain deque와 queue/stack의 차이를 먼저 잡는다 |
| `TreeMap은 언제 써요?`, `범위 조회면 왜 HashMap이 아니죠?` | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) | `lookup only`와 `정렬/범위/ceiling/floor` 요구를 분리한다 |
| `왜 lower랑 floor가 달라요?`, `같은 key 포함 여부가 뭐예요?` | [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md) | strict/inclusive와 exact match 포함 여부를 먼저 고정한다 |

## 섞인 질문을 자르는 순서

질문이 둘 이상 섞여 보이면 이 순서로 자르면 된다.

1. `있나/없나`에서 끝나면 `set`
2. `key의 값`이 필요하면 `map`
3. `먼저 온 순서`면 `queue`
4. `앞뒤 양쪽 끝 제어`면 `deque`
5. `정렬된 이웃/범위`면 `TreeSet/TreeMap`

## 먼저 자를 질문

이름보다 "지금 무엇을 해야 하나"를 먼저 묻는 편이 빠르다.

| 지금 먼저 묻는 것 | 첫 구조/문서 | 이유 |
|---|---|---|
| `응용 자료구조가 뭔지`, `online/offline부터 헷갈린다` | [응용 자료 구조 개요](./applied-data-structures-overview.md) | 반복 질의를 연산 문장으로 먼저 번역한다 |
| `중복만 막나`, `있는지만 보나`, `값도 붙여야 하나` | [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md) | `set`과 `map` 경계를 먼저 자른다 |
| `dense integer id 집합을 계속 겹쳐 보나`, `bitmap이 괜히 과한가`, `정수 id인데 범위가 희소해서 plain bitset이 wasteful한가` | [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md) | `Set` 기본값에서 `bitmap/bitset`, `sparse range`, compressed bitmap handoff 신호를 자른다 |
| `audience selection에서 set인지 bitmap인지 감이 안 와요`, `세그먼트 대상자 계산은 어떤 구조로 시작하죠?`, `sparse range 정수 id면 set bitset roaring 중 뭘 고르죠?` | [Set vs Bitmap Audience Selection Mini Drill](./set-vs-bitmap-audience-selection-mini-drill.md) | 세그먼트 대상 계산 문장을 `membership only`와 `set algebra`로 다시 자르고, sparse range follow-up에서 `Set`/plain `BitSet`/`Roaring Bitmap` 분기를 짧게 연습시킨다 |
| `bitset만 알면 되나`, `roaring bitmap은 언제부터 필요한가`, `compressed bitmap 첫 설명이 필요하다` | [BitSet vs Roaring Bitmap Beginner Handoff](./bitset-vs-roaring-bitmap-beginner-handoff.md) | plain `BitSet` mental model의 학습 종료선과 `Roaring`으로 넘어갈 시작 신호를 짧게 분리한다 |

## 먼저 자를 질문: follow-up 분기

위 표에서 bitmap 계열이나 ordered set 계열까지 왔다면, follow-up 질문을 한 번 더 줄여서 본다.

| `plain bitset과 compressed bitmap 차이를 한 번 더 정리하고 싶다`, `dense bitmap과 sparse bitmap follow-up 카드가 필요하다`, `exact set algebra 때문에 왜 compressed bitmap이 나오죠?` | [Plain BitSet vs Compressed Bitmap Decision Card](./plain-bitset-vs-compressed-bitmap-decision-card.md) | plain `BitSet`과 compressed bitmap을 dense/sparse + repeated set algebra 기준으로 다시 자르는 intermediate follow-up이다 |
| `중복 제거는 맞는데 정렬/범위도 같이 필요하다` | [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md) | `hash set`과 `tree set` 경계를 자른다 |
| `TreeSet/TreeMap에서 왜 null이 나오죠?`, `first랑 floor가 실패 방식이 왜 달라요?` | [TreeSet, TreeMap Null-Boundary Quick Reference](./treeset-treemap-null-boundary-quick-reference.md) | `예외 vs null` 경계와 첫 NPE 실수를 먼저 자른다 |

## 조회/문자열/순서 출발점

아래는 `lookup`, `prefix`, `FIFO`, `graph`처럼 문제 문장이 좀 더 직접적일 때 바로 붙일 수 있는 출발점이다.

| 지금 먼저 묻는 것 | 첫 구조/문서 | 이유 |
|---|---|---|
| `map/set/queue/priority queue/trie/bitmap 중 뭐부터 고르지` | [Map vs Set vs Queue vs Priority Queue vs Trie vs Bitmap 선택 프라이머](./map-set-queue-priorityqueue-trie-bitmap-selection-primer.md) | lookup, dedupe, fifo, prefix를 정리한다 |
| `id로 바로 찾기`, `key -> value` | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) | 조회가 핵심이면 `map` 계열부터 정해야 한다 |
| `문자열 exact lookup인데 trie까지 필요한가`, `prefix search가 아니라면 뭐가 기본값인가` | [Trie vs HashMap: exact lookup이냐 prefix search냐](./trie-vs-hashmap-exact-lookup-beginner-card.md) | exact lookup과 startsWith 질의를 분리해야 한다 |
| `문자열 key인데 prefix search와 사전순 다음 key가 헷갈려요`, `다음 문자열 key를 찾는 건 trie예요 treemap예요` | [Trie Prefix Search vs TreeMap Ordered Map Beginner Card](./trie-prefix-search-vs-treemap-ordered-map-beginner-card.md) | `Trie`와 ordered map의 질문 축을 분리한다 |
| `먼저 들어온 순서대로 처리` | [큐 기초](./queue-basics.md) | FIFO 규칙이 먼저다 |
| `앞/뒤 양쪽 끝을 번갈아 써야 한다` | [덱 기초](./deque-basics.md) | plain deque가 필요한지부터 분리할 수 있다 |
| `가장 작은 값`, `가장 급한 작업` | [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md) | queue와 priority queue를 분리해야 한다 |
| `같은 그룹인가`, `연결되어 있나` | [Connectivity Question Router](./connectivity-question-router.md) | 자료구조 선택인지 탐색 문제인지부터 가른다 |
| `그래프가 뭐고 정점/간선이 뭔지부터 낯설다` | [그래프 기초](./graph-basics.md) | BFS나 union-find 전에 그래프 그림을 먼저 붙인다 |

## 초급 10초 라우터

문장을 이렇게 번역하면 출발점이 잡힌다.

### 조회/순서 라우터

| 지금 문제에서 가장 먼저 보이는 문장 | 먼저 볼 문서 | 왜 여기서 시작하나 |
|---|---|---|
| `회원 id로 주문 조회` | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) | exact lookup |
| `문자열 key를 찾는데 trie가 필요한가요?` | [Trie vs HashMap: exact lookup이냐 prefix search냐](./trie-vs-hashmap-exact-lookup-beginner-card.md) | 문자열이라고 다 prefix search는 아니다 |
| `문자열 key인데 prefix search와 사전순 다음 key가 헷갈려요`, `문자열 key의 다음 값`, `사전순 범위`, `prefix 후보`가 한 문제에 같이 보여요 | [Trie Prefix Search vs TreeMap Ordered Map Beginner Card](./trie-prefix-search-vs-treemap-ordered-map-beginner-card.md) | 문자열 key 위에서 prefix와 ordered range를 먼저 나눈다 |
| `이미 처리한 요청인가`, `중복만 막으면 되나` | [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md) | `set`인지 `map`인지 먼저 자른다 |
| `입력한 순서 그대로 응답` | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) | 삽입 순서 요구 |
| `왜 출력 순서가 바뀌지?` | [Map order symptom router card](./map-order-symptom-router-card.md) | 순서 규칙부터 자른다 |
| `조회/갱신 뒤 map 순서가 바뀐다` | [LinkedHashMap access-order 미니 프라이머](./linkedhashmap-access-order-mini-primer.md) | 삽입 순서와 접근 순서를 분리한다 |

`처음 자료구조`, `set map 차이 처음`, `왜 순서가 바뀌지` 같은 query는 여기서 먼저 끊는 편이 안전하다. 핵심은 `lookup`, `dedupe`, `삽입 순서` 중 무엇이 먼저 필요한지 고르는 것이다.

## 예약/범위 10초 라우터

예약표나 정렬된 key 이웃을 읽기 시작하면 아래 표만 보면 된다.

| 지금 문제에서 가장 먼저 보이는 문장 | 먼저 볼 문서 | 왜 여기서 시작하나 |
|---|---|---|
| `다음 예약 시간`, `범위 조회` | [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md) | 이웃/범위 탐색 |
| `왜 lower랑 floor가 달라요?`, `entry로 바꾸면 exact match 포함도 바뀌나요?` | [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md) -> [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md) | strict/inclusive와 key/entry를 함께 자른다 |
| ``ceiling/floor`는 보이는데 왜 자꾸 `PriorityQueue.poll()`이 떠오르죠?`, `예약표에서 다음 예약 찾는데 poll을 써도 되나요?` | [PriorityQueue.poll() vs TreeMap `ceiling`/`floor` Schedule Bridge](./priorityqueue-poll-vs-treemap-ceiling-floor-schedule-bridge.md) | key-value schedule exact-neighbor query와 global min extraction을 분리한다 |

## 예약/범위 10초 라우터: 경계와 gap

예약표 follow-up은 경계 해석과 빈 슬롯 계산을 분리해서 보면 더 덜 헷갈린다.

| `"[start, end)"가 뭐예요?`, `끝과 다음 시작이 같으면 겹치나요?` | [Reservation Interval Half-Open Boundary Card](./reservation-interval-half-open-boundary-card.md) | 예약 경계 해석 |
| `30분 빈 시간 있나?`, `가장 가까운 1시간 슬롯은 어디죠?` | [TreeMap Gap Detection Mini Drill](./treemap-gap-detection-mini-drill.md) | gap 계산과 nearest-slot 분기 |
| `왜 다음 후보를 next.end로 점프해도 되죠?`, `nearest slot이 disjoint interval set이랑 무슨 관계예요?` | [TreeMap Nearest-Slot Jump to Disjoint Interval Set Bridge](./treemap-nearest-slot-disjoint-interval-bridge.md) | gap jump를 비겹침 interval state와 연결한다 |
| `왜 ceilingKey가 null이죠?`, `firstEntry는 null인데 firstKey는 왜 예외죠?` | [TreeSet, TreeMap Null-Boundary Quick Reference](./treeset-treemap-null-boundary-quick-reference.md) | null boundary와 empty behavior |
| `firstKey/firstEntry`, `floorKey/floorEntry`, `ceilingKey/ceilingEntry`가 헷갈려요 | [TreeMap `firstKey` vs `firstEntry`, `floorKey` vs `floorEntry` Return-Shape Card](./treemap-firstkey-firstentry-floorkey-floorentry-return-shape-card.md), [TreeMap `ceilingKey` vs `ceilingEntry` Return-Shape Twin Card](./treemap-ceilingkey-ceilingentry-return-shape-twin-card.md) | key-only와 entry 반환 shape를 한 번에 정리한다 |

## 그래프/탐색 10초 라우터

| 지금 문제에서 가장 먼저 보이는 문장 | 먼저 볼 문서 | 왜 여기서 시작하나 |
|---|---|---|
| `작업을 받은 순서대로 처리` | [큐 기초](./queue-basics.md) | FIFO handoff가 핵심이다 |
| `가까운 칸부터`, `최소 이동 횟수` | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | queue는 도구이고 질문은 BFS다 |
| `미로가 왜 그래프예요?`, `격자도 그래프인가요?` | [그래프 기초](./graph-basics.md) -> [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | 칸을 정점, 이동 가능을 간선으로 번역하면 BFS/DFS가 바로 붙는다 |
| `정점`, `간선`, `방향 그래프`가 낯설다 | [그래프 기초](./graph-basics.md) | 그래프 그림부터 이해해야 뒤 문서가 덜 추상적이다 |
| `최단 경로, MST, 위상 정렬이 한꺼번에 섞인다` | [그래프 기초](./graph-basics.md) -> [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) -> [그래프 관련 알고리즘](../algorithm/graph.md) | 그래프 그림과 탐색 질문을 먼저 자른 뒤, `graph.md`는 상단 라우터로만 보고 세부 구현은 전용 follow-up 문서 한 장으로 넘기는 편이 beginner-safe 하다 |

짧게 외우면 `graph는 구조`, `bfs는 거리 순서 탐색`, `queue는 FIFO 도구`다. `왜 queue인데 bfs예요?`, `왜 graph예요?`, `왜 최소 이동 횟수예요?` 같은 beginner symptom은 아래 한 줄 비교로 다시 자르면 된다.

| learner symptom | 먼저 답해야 하는 것 | 첫 문서 |
|---|---|---|
| `왜 queue가 나와요?` | FIFO 도구가 필요한지 | [큐 기초](./queue-basics.md) |
| `왜 bfs예요?` | `최소 이동 횟수`처럼 거리 순서가 핵심인지 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `왜 graph예요?` | 칸/역/페이지를 정점으로 번역할 수 있는지 | [그래프 기초](./graph-basics.md) |
| `visited를 boolean[]로 두나요, Set으로 두나요?` | 탐색 자체보다 방문 기록 방식이 막힌 것인지 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) -> [Java BFS visited 배열 vs Set beginner card](../algorithm/bfs-visited-array-vs-set-java-beginner-card.md) |

## graph/bfs/queue 한 장면 예시

같은 물류 장면을 봐도 질문을 이렇게 자르면 출발점이 바로 달라진다.

| 같은 `주문/창고` 장면에서 들린 말 | 먼저 고를 것 | 첫 문서 |
|---|---|---|
| `주문을 받은 순서대로 worker에 넘겨` | FIFO 순서 규칙 | [큐 기초](./queue-basics.md) |
| `가까운 창고부터 넓혀서 찾자` | 거리 순서 탐색 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `orderId로 상태를 바로 찾아` | key -> value lookup | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) |
| `이미 처리한 주문인지 확인해` | membership only | [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md) |

자주 섞는 오해도 여기서 끊어 두면 좋다.

- `queue를 쓴다`와 `BFS다`는 같은 말이 아니다. 전자는 도구, 후자는 탐색 규칙이다.
- `graph가 보인다`와 `BFS를 써야 한다`도 같은 말이 아니다. 그래프는 구조이고, 질문은 연결/경로/최소 이동으로 다시 자른다.
- `visited`가 `Set`이나 `Map`이라도 문제의 중심은 여전히 탐색일 수 있다.

## 같은 장면 번역

같은 서비스 장면도 질문이 어디에 있느냐에 따라 구조가 달라진다.

| 같은 주문 서비스 장면 | 첫 출발점 | 이유 |
|---|---|---|
| `orderId로 한 건 찾기` | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) | 조회 구조 선택 문제다 |
| `요청을 받은 순서대로 worker에 넘기기` | [큐 기초](./queue-basics.md) | 순서 보존이 핵심이다 |
| `가장 가까운 창고부터 확장` | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) -> [큐 기초](./queue-basics.md) | 자료구조보다 탐색 순서가 핵심이다 |

짧은 예시 하나만 더 붙이면 초반 분기가 더 빨라진다.

| `주문 처리`라는 같은 말이라도 | 실제로 먼저 필요한 답 | 첫 구조 |
|---|---|---|
| `이 주문번호 이미 봤나?` | membership only | `Set` |
| `orderId로 상태를 바로 찾나?` | `key -> value` lookup | `Map` |
| `먼저 들어온 주문부터 보내나?` | FIFO 순서 | [큐 기초](./queue-basics.md) |
| `가까운 물류센터부터 넓히나?` | 거리 순서 확장 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) -> [큐 기초](./queue-basics.md) |

이 한 장면 예시는 `map`, `queue`, `bfs`를 이름이 아니라 질문 모양으로 나누는 용도다.

그래프 계열은 여기서 한 번 더 짧게 자르면 더 안전하다.

| 지금 헷갈리는 말 | 먼저 볼 문서 | 이유 |
|---|---|---|
| `정점`, `간선`, `방향 그래프` | [그래프 기초](./graph-basics.md) | 자료구조 그림 자체가 먼저다 |
| `갈 수 있나`, `같은 그룹인가` | [Connectivity Question Router](./connectivity-question-router.md) | 답의 모양이 yes/no인지 먼저 자른다 |
| `가까운 칸부터`, `최소 이동 횟수` | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | 그래프 위에서 탐색 순서를 고르는 단계다 |

헷갈리면 아래 3문장만 순서대로 다시 묻는 편이 가장 빠르다.

1. `key로 바로 찾는가?` -> `map`
2. `먼저 온 것을 먼저 처리하는가?` -> `queue`
3. `거리 1, 2, 3 순서로 넓히는가?` -> `BFS + queue`

특히 2번과 3번은 둘 다 queue를 쓰지만 질문이 다르다.
`작업 순서`면 자료구조 문서로, `최소 이동 횟수`면 알고리즘 문서로 가면 된다.

## 처음 15분 읽기 루트

처음엔 구현체보다 요구를 먼저 고정한다.

| 지금 막힌 문장 | 15분 첫 루트 | 왜 이 순서가 쉬운가 |
|---|---|---|
| `중복만 막나, 값도 붙이나` | [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md) -> [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) | `set`과 `map`을 먼저 자른다 |
| `HashSet이면 되나, TreeSet/TreeMap도 봐야 하나` | [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md) -> [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) | `정렬된 집합`과 `정렬된 key-value` 요구를 나눠 본다 |
| `먼저 들어온 순서대로 처리` | [큐 기초](./queue-basics.md) -> [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md) | FIFO 감각부터 잡고 queue/deque/priority queue를 나눈다 |
| `덱이 왜 필요한지 모르겠다`, `queue로 안 되나` | [덱 기초](./deque-basics.md) -> [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md) | 양쪽 끝 제어가 필요한지 먼저 본다 |
| `다음 예약`, `이전 값`, `범위 조회`, `다음 예약, 이전 예약, 범위 조회를 같이 다뤄요` | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) -> [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md) | `정렬`보다 `이웃/범위` 요구를 먼저 본다 |
| `가까운 칸부터`, `최소 이동 횟수` | [큐 기초](./queue-basics.md) -> [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | queue를 써도 핵심 질문이 BFS인지 본다 |
| `그래프 정점/간선부터 안 잡힌다` | [그래프 기초](./graph-basics.md) -> [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | 그래프 그림이 먼저다 |
| `10:00 이후 첫 예약 찾기` | [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md) | 이웃 탐색이 필요하다 |

## 옆 카테고리로 잠깐 갔다가 돌아오기

자료구조 primer를 읽다가 탐색 규칙이나 서비스 책임 문장이 더 먼저 막히면, 옆 카테고리 문서 한 장만 보고 다시 이 README로 복귀하는 동선이 가장 안전하다.

| 지금 먼저 막힌 문장 | 잠깐 다녀올 문서 | 돌아올 자리 |
|---|---|---|
| `queue를 쓰긴 하는데 왜 BFS라고 하죠?`, `가까운 칸부터가 뭐예요?` | [알고리즘 README - BFS, Queue, Map 먼저 분리하기](../algorithm/README.md#bfs-queue-map-먼저-분리하기) | [초급 10초 라우터](#초급-10초-라우터) |
| `queue`, `priority queue`, `map lookup`까지 한 줄에서 같이 보여요 | [Queue vs BFS vs Priority Queue vs Map Lookup Micro Drill](./queue-bfs-priorityqueue-map-lookup-micro-drill.md) | [graph, bfs, queue가 같이 보일 때](#graph-bfs-queue가-같이-보일-때) |
| `Service 규칙보다 List/Set/Map 선택이 먼저 막혀요`, `처음이라 어디까지가 구조 선택이죠?` | [Software Engineering README - 연결해서 보면 좋은 문서](../software-engineering/README.md#연결해서-보면-좋은-문서-cross-category-bridge) | [같은 장면 번역](#같은-장면-번역) |
| `왜 출력 순서가 바뀌지?`, `Java 컬렉션 basics부터 다시 볼래요` | [Java 컬렉션 프레임워크 입문](../language/java/java-collections-basics.md) | [처음 15분 읽기 루트](#처음-15분-읽기-루트) |

옆 카테고리 문서를 보고 돌아오면 `이 문제에서 먼저 고를 것은 구조인가, 순서 규칙인가, 책임 위치인가`만 다시 묻고 다음 칸으로 이동하면 된다.
`왜 queue인데 bfs예요`, `왜 service 얘기인데 map이 먼저 보여요` 같은 symptom이 남아 있으면 여기서 더 깊이 내려가기보다 [초급 10초 라우터](#초급-10초-라우터)나 [같은 장면 번역](#같은-장면-번역)으로 먼저 복귀해 질문 층위를 다시 맞춘다.
복귀 위치가 헷갈리면 [길 잃었을 때 복귀 경로](#길-잃었을-때-복귀-경로)에서 증상 문장을 다시 고르면 안전하다.

## 자주 섞는 오해

- `queue`가 보인다고 항상 자료구조 문제가 아니다. `최소 이동 횟수`면 핵심은 BFS다.
- `map`이 보인다고 항상 탐색이 사라지는 것도 아니다. BFS/DFS 안에서도 `visited set/map`을 쓴다.
- `그래프`, `union-find`, `BFS`를 같은 층위로 외우면 더 헷갈린다. `그래프는 구조`, `union-find는 연결성 질의`, `BFS는 탐색 순서`로 끊어 읽는 편이 안전하다.
- `그래프 기초`에서 바로 다익스트라나 MST로 들어가면 초보자 범위를 넘기 쉽다. `그래프 기초 -> DFS와 BFS 입문`까지 본 뒤에도 안 잘릴 때만 [그래프 관련 알고리즘](../algorithm/graph.md)의 상단 라우터로 넘기고, 갈래가 정해지면 그 문서 안에 머물지 말고 전용 follow-up 문서로 바로 내려가는 편이 낫다.
- `정렬된 출력 한 번`과 `계속 range/floor/ceiling을 묻는 상황`은 다르다. 전자는 `HashMap + 마지막 정렬`로 끝날 수 있고, 후자는 `TreeMap` 쪽이다.
- `priority queue`는 queue라는 이름이 있어도 FIFO가 아니다. 먼저 꺼내는 기준이 도착 순서가 아니라 우선순위다.
- `queue`와 `map`이 같이 보여도 둘 중 하나만 고르는 문제가 아닐 수 있다. 예를 들어 BFS는 queue로 확장하고 `visited set/map`으로 중복 방문을 막는다.

처음엔 아래 세 문장으로 다시 번역해도 된다.

- `순서대로 처리`면 queue
- `key로 바로 찾기`면 map
- `거리 순서로 퍼지기`면 알고리즘 문서의 BFS

## 처음 읽는 순서

처음이면 아래 5개만 먼저 보면 충분하다.

1. [기본 자료 구조](./basic.md)
2. [큐 기초](./queue-basics.md)
3. [Map vs Set vs Queue vs Priority Queue vs Trie vs Bitmap 선택 프라이머](./map-set-queue-priorityqueue-trie-bitmap-selection-primer.md)
4. [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md)
5. [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md)
6. [Set vs Bitmap Audience Selection Mini Drill](./set-vs-bitmap-audience-selection-mini-drill.md)

## 심화로 내려가는 기준

아래부터는 "기본 선택은 끝났는데 다음 경계가 막힐 때" 보는 문서들이다.

- queue에서 `deque`나 `priority queue` 경계가 헷갈리면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- `LinkedHashMap`의 삽입 순서와 access-order, 같은 key 갱신 시 순서 변화까지 짧게 분리하고 싶으면 [LinkedHashMap access-order 미니 프라이머](./linkedhashmap-access-order-mini-primer.md)
- `HashMap`/`LinkedHashMap`/`TreeMap` 중 무엇 때문에 순서가 달라졌는지 먼저 빨리 자르고 싶으면 [Map order symptom router card](./map-order-symptom-router-card.md)
- `TreeMap`의 `floor/ceiling/subMap`이 필요하면 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- `circular queue`와 `ring buffer`를 구분하고 싶으면 [Circular Queue vs Ring Buffer Primer](./circular-queue-vs-ring-buffer-primer.md)
- `sliding window`에서 deque가 왜 필요한지 보고 싶으면 [Monotonic Queue / Stack](./monotonic-queue-and-stack.md)
- timer queue, lock-free queue, roaring bitmap 같은 운영/심화 주제는 아래 `응용 catalog`에서 필요한 것만 고르면 된다

처음 읽는 단계라면 여기서 더 넓히기보다 `Queue vs Deque vs Priority Queue Primer`나 `HashMap, TreeMap, LinkedHashMap Beginner Selection Primer`처럼 지금 막힌 경계 문서 한 장만 더 읽고 멈추는 편이 beginner-safe 하다.

## 기본 primer

### 기본 자료 구조 [▶︎ 🗒](basic.md)

- [Array](basic.md#array-배열)
- [Linked List](basic.md#linked-list-연결-리스트)
- [Backend Data-Structure Starter Pack](backend-data-structure-starter-pack.md)
- [Map vs Set vs Queue vs Priority Queue vs Trie vs Bitmap 선택 프라이머](map-set-queue-priorityqueue-trie-bitmap-selection-primer.md)
- [Bitmap vs Set Dense Integer ID Beginner Bridge](bitmap-vs-set-dense-integer-id-beginner-bridge.md)
- [복잡도와 알고리즘 패턴 기초](complexity-and-algorithm-pattern-foundations-backend-juniors.md)
- [Stack](basic.md#stack-스택)
- [Queue](basic.md#queue-큐) (`enqueue/dequeue` vs `front/rear/head/tail` 브리지 포함)
- [Queue vs Deque vs Priority Queue Primer](queue-vs-deque-vs-priority-queue-primer.md)
- [ArrayDeque vs LinkedList 큐 선택 카드](arraydeque-vs-linkedlist-queue-choice-card.md) (`java queue 구현 기본값`, BFS/service FIFO에서 왜 `ArrayDeque`를 먼저 두는지)
- [ArrayDeque vs BlockingQueue 서비스 handoff 프라이머](arraydeque-vs-blockingqueue-service-handoff-primer.md) (`로컬 FIFO`와 `멀티스레드 worker handoff`를 어디서 갈라야 하는지)
- [Java PriorityQueue Pitfalls](java-priorityqueue-pitfalls.md) (중복 priority trace, stable-order 오해, `(priority, sequence)` tie-breaker)

## queue/timer 심화 follow-up

이 구간은 `queue 기본`, `priority queue 기본`, `service handoff 기본`을 이미 구분한 뒤에만 내려가면 된다. `처음`, `뭐부터`, `queue가 왜 두 군데 나오죠?` 단계라면 위 primer 구간으로 돌아가는 편이 더 안전하다.

- [TreeMap Interval Entry Primer](treemap-interval-entry-primer.md)
- [PriorityBlockingQueue Timer Misuse Primer](priorityblockingqueue-timer-misuse-primer.md)
- [ScheduledExecutorService vs DelayQueue Bridge](scheduledexecutorservice-vs-delayqueue-bridge.md)
- [DelayQueue Repeating Task Primer](delayqueue-repeating-task-primer.md)
- [Java Timer Clock Choice Primer](java-timer-clock-choice-primer.md)
- [ScheduledFuture Cancellation Bridge](scheduledfuture-cancel-stale-entries.md)
- [DelayQueue Remove Cost Primer](delayqueue-remove-cost-primer.md)
- [DelayQueue Delayed Contract Primer](delayqueue-delayed-contract-primer.md)
- [Timer Cancellation and Reschedule Stale Entry Primer](timer-cancellation-reschedule-stale-entry-primer.md)
- [Top-K Heap Direction Patterns](top-k-heap-direction-patterns.md)
- [Circular Queue vs Ring Buffer Primer](circular-queue-vs-ring-buffer-primer.md)
- [Bounded Queue Policy Primer](bounded-queue-policy-primer.md)

## tree와 graph primer

- [Hash Table](basic.md#hash-table-해시-테이블)
- [Heap](basic.md#heap-힙)
- [Tree](basic.md#tree-트리)
- [Binary Tree](binary-tree-vs-bst-vs-heap-bridge.md)
- [Binary Tree vs BST vs Heap Bridge](binary-tree-vs-bst-vs-heap-bridge.md)
- [Binary Tree Traversal Routing Guide](binary-tree-traversal-routing-guide.md)
- [Segment Tree Is Not BST or Heap](segment-tree-not-bst-or-heap-bridge.md)
- [Balanced BST vs Unbalanced BST Primer](balanced-bst-vs-unbalanced-bst-primer.md)
- [Graph](basic.md#graph-그래프)
- [Union-Find](basic.md#union-find-유니온-파인드)
- [Union-Find Standalone Beginner Primer](union-find-standalone-beginner-primer.md) (`same component yes/no` first stop)
- [Union-Find Component Metadata Walkthrough](union-find-component-metadata-walkthrough.md) (`same?` 질문이 `size/count`까지 확장될 때)
- [Deletion-Aware Connectivity Bridge](deletion-aware-connectivity-bridge.md)

## 응용 catalog

## 응용 자료 구조 [▶︎ 🗒](applied-data-structures-overview.md)

개별 deep dive 전에, [응용 자료 구조 개요](applied-data-structures-overview.md)에서 `문제 문장 -> 필요한 연산 -> 자료 구조` 흐름과 30초 선택 플로우만 먼저 잡아두면 첫 진입이 훨씬 빨라진다.
아래 mixed catalog에서는 `[playbook]` 라벨로 step-oriented selection / operation 문서를 따로 튀게 했다.
이 아래부터는 beginner entrypoint라기보다 필요할 때 찾아가는 follow-up catalog다. timer, 동시성 queue, roaring bitmap 운영 문서는 `기본 선택이 끝난 뒤`에만 붙여도 늦지 않다.

## 큐와 작업 흐름

`FIFO queue`, `deque`, `priority queue` 구분이 먼저 헷갈리면 [Queue vs Deque vs Priority Queue Primer](queue-vs-deque-vs-priority-queue-primer.md)에서 `도착 순서`, `양쪽 끝 제어`, `우선순위` 축을 먼저 나누고, `A(2) -> B(1) -> C(1)` 한 입력으로 `FIFO poll`과 `duplicate-priority poll`을 바로 비교한 초급 trace, 그리고 `먼저 도착한 요청`, `비용 0은 앞`, `상위 3개만 유지` 같은 자연어 문장을 핵심 연산으로 번역하는 짧은 bridge 예시까지 보고 아래 deep dive로 내려가면 된다.
Java에서 "BFS나 메서드 안의 로컬 FIFO"와 "여러 스레드가 worker에게 작업을 넘기는 큐"를 자꾸 같은 질문으로 보면 [ArrayDeque vs BlockingQueue 서비스 handoff 프라이머](arraydeque-vs-blockingqueue-service-handoff-primer.md)로 이어서 `로컬 순서 보존`과 `동시성 handoff 계약`을 먼저 분리하는 편이 좋다.
같은 `deque`라도 `양끝 시뮬레이션`, `sliding window extrema`, `0-1 shortest path`가 서로 다른 패턴이라는 감각을 빨리 잡고 싶다면 [Deque Router Example Pack](deque-router-example-pack.md)으로 바로 가는 편이 빠르다.
`enqueue/dequeue/peek` 같은 FIFO API와 `front/rear/head/tail` 같은 구현 용어를 가장 얕게 이어 주는 입문 정리는 [Queue](basic.md#queue-큐) 섹션이다.
Java `PriorityQueue`를 쓰다가 comparator 방향, tie-breaker, stale entry, sorted iteration 오해가 자주 섞이면 [Java PriorityQueue Pitfalls](java-priorityqueue-pitfalls.md)에서 중복 priority trace와 `(priority, sequence)` 패턴까지 함께 정리하는 편이 빠르다.

## timer queue와 delay queue

Java timer executor를 떠올리며 `PriorityBlockingQueue`면 thread safety와 timer 대기가 한 번에 해결된다고 느껴지면 [PriorityBlockingQueue Timer Misuse Primer](priorityblockingqueue-timer-misuse-primer.md)에서 `empty blocking`과 `deadline blocking` 차이를 먼저 분리해두는 편이 좋다.
`ScheduledExecutorService`를 쓰면서 내부에서 작업이 어떻게 기다리는지 자료구조 그림이 안 잡히거나, `scheduleAtFixedRate()`와 `scheduleWithFixedDelay()`가 왜 다른 박자로 다시 queue에 들어가는지 헷갈리면 [ScheduledExecutorService vs DelayQueue Bridge](scheduledexecutorservice-vs-delayqueue-bridge.md)에서 `deadline ticket -> delayed work queue -> worker -> periodic re-enqueue` 흐름을 먼저 잡아두면 좋다.
직접 `DelayQueue`로 반복 작업을 만들면서 fixed-rate와 fixed-delay를 어떤 수식으로 다시 넣는지, 그리고 self-rescheduling 코드에서 stale ticket이 어디서 생기는지 같이 보고 싶다면 [DelayQueue Repeating Task Primer](delayqueue-repeating-task-primer.md)가 가장 바로 맞는 진입점이다.
상대 지연을 queue 내부 deadline으로 저장할 때 `currentTimeMillis()`와 `nanoTime()` 중 무엇이 더 자연스러운지 막히면 [Java Timer Clock Choice Primer](java-timer-clock-choice-primer.md)에서 `벽시계 vs 스톱워치` 감각을 먼저 잡고 가면 이후 `DelayQueue` 문서가 훨씬 덜 헷갈린다.

## cancellation과 stale entry

`ScheduledFuture.cancel()`을 호출했는데 `true`가 나와도 왜 queue size가 안 줄 수 있는지, 취소된 작업이 왜 내부에서 stale ticket처럼 남는지, 이 API를 `DelayQueue` 쪽 invalidation으로 어떻게 번역해 읽어야 하는지, `removeOnCancelPolicy`를 언제 켜야 하는지 헷갈리면 [ScheduledFuture Cancellation Bridge](scheduledfuture-cancel-stale-entries.md)에서 future 상태 전환과 DelayQueue-style stale-entry mental model을 한 그림으로 먼저 붙여두면 좋다.
heap-backed timer queue에서 `remove(ticket)`가 왜 `poll()`처럼 바로 끝나지 않는지, exact handle과 `equals()` 기반 제거가 왜 다른 함정으로 이어지는지 헷갈리면 [DelayQueue Remove Cost Primer](delayqueue-remove-cost-primer.md)에서 `head pop vs middle search`, `handle vs equality`, `latest generation` 함정을 먼저 분리해두면 좋다.

## delay queue contract

`DelayQueue`를 직접 구현해 보며 `Delayed.compareTo()`와 `getDelay()`가 왜 같은 deadline을 봐야 하는지 헷갈리면 [DelayQueue Delayed Contract Primer](delayqueue-delayed-contract-primer.md)에서 `head ordering`과 `expired head` 계약을 먼저 확인하는 편이 안전하다.
`Delayed.compareTo()`에 business priority까지 넣고 싶어질 때는 [Timer Priority Policy Split](timer-priority-policy-split.md)에서 `due-time gate`와 `ready priority ordering`을 먼저 분리하는 편이 안전하다.
`DelayQueue`를 이미 골랐는데 취소나 재예약 때문에 오래된 timer ticket이 왜 남는지 막히면 [Timer Cancellation and Reschedule Stale Entry Primer](timer-cancellation-reschedule-stale-entry-primer.md)에서 `즉시 제거`, `lazy stale skip`, `generation` 플래그, latest-wins 검사를 먼저 분리해두는 편이 좋다.
Java timer executor나 delayed task queue를 만들 때 `PriorityQueue`로 끝내도 되는지, `DelayQueue`가 필요한지 헷갈리면 [DelayQueue vs PriorityQueue Timer Pitfalls](delayqueue-vs-priorityqueue-timer-pitfalls.md)에서 `정렬`과 `delay-aware blocking`, cancellation stale-entry trade-off를 먼저 분리해두는 편이 안전하다. 같은 문서의 non-timer 분기에서 stable-order 요구를 `(priority, sequence)` comparator 패턴으로 바로 라우팅해 준다.

## heap 방향과 bounded queue

`kth-largest`, `streaming top-k`, `median`에서 min-heap / max-heap 방향 선택이 이름과 다르게 느껴질 때는 [Top-K Heap Direction Patterns](top-k-heap-direction-patterns.md)로 바로 이어 보면 "루트가 어떤 경계값을 대표해야 하는가" 기준이 정리된다.
원형 배열 queue 구현과 시스템 문맥 `ring buffer` 용어가 자꾸 섞이면 [Circular Queue vs Ring Buffer Primer](circular-queue-vs-ring-buffer-primer.md)에서 `면접형 queue 설계`와 `시스템형 bounded buffer`를 먼저 분리해두는 편이 좋다.
고정 크기 queue가 꽉 찼을 때 `reject`, `overwrite`, `blocking`, `backpressure` 중 무엇이 맞는지 먼저 잡고 싶다면 [Bounded Queue Policy Primer](bounded-queue-policy-primer.md)로 내려가면 `누가 양보하나` 축이 빨리 정리된다.
`logging`, `telemetry`, `audio`, `producer-consumer pipeline`처럼 같은 ring buffer 계열이어도 `유실 허용`, `callback 실시간성`, `fan-in/out`, `stage dependency` 축이 다르면 다음 문서 라우팅이 달라지므로 [Ring Buffer](ring-buffer.md)의 use-case matrix까지 같이 보면 빠르다.

## concurrent queue와 ring buffer

timer 구조를 고를 때는 [Timing Wheel vs Delay Queue](timing-wheel-vs-delay-queue.md)에서 `earliest deadline`과 `timer churn` 축을 먼저 잡고, 이어서 [Concurrent Skip List Internals](concurrent-skiplist-internals.md)에서 `ordered range scan`이 왜 별도 요구인지 보면 읽기 흐름이 자연스럽다.

동시성 큐 internals를 한 축으로 읽고 싶다면 `Ring Buffer -> Lock-Free SPSC Ring Buffer -> Bounded MPMC Queue -> Sequencer-Based Ring Buffer Coordination -> ABA Problem and Tagged Pointers -> Hazard Pointers vs Epoch-Based Reclamation -> Reclamation Cost Trade-offs` 순서가 좋다.
앞쪽은 bounded ring의 slot/state machine과 backpressure를, 뒤쪽은 pointer reuse와 safe reclamation을 이어서 설명한다.

## monotonic deque와 stack

`sliding window maximum/minimum`처럼 연속 구간의 `최대/최소`를 바로 답해야 하면 deque 쪽으로 먼저 간다.
반대로 `next greater element`, `오큰수`, `histogram largest rectangle`처럼 "현재 원소의 답이 스택 top 비교로 정해지나"를 묻는 문제면 stack 쪽으로 먼저 간다.
중복값에서 `<`와 `<=`가 갈리는 규칙만 자꾸 흔들리면 drill 문서 하나만 먼저 보고, 나머지 심화 문서는 아래 링크에서 필요한 것만 고르면 된다.

## monotonic 관련 문서

- [Deque](applied-data-structures-overview.md#deque-덱) (monotonic deque routing for sliding window maximum/minimum, recent `k` extrema)
- [Deque Router Example Pack](deque-router-example-pack.md) (plain deque vs monotonic deque vs 0-1 BFS quick split)
- [Monotonic Deque Walkthrough](monotonic-deque-walkthrough.md) (plain deque -> monotonic deque trace, sliding window maximum/minimum step-by-step, 값만 출력 vs index 출력에서 `<`/`<=`, `>`/`>=`가 갈리는 duplicate tie-break 미니 박스와 4문항 strict/or-equal 퀴즈 + 4문항 duplicate 대표자 퀴즈)
- [Sliding Window Duplicate Extrema Index Drill](sliding-window-duplicate-extrema-index-drill.md) (sliding-window max/min에서 duplicate extrema index tie-break만 따로 분리해 `왼쪽 index`와 `오른쪽 index` 규칙을 작은 표와 예제로 먼저 고정하는 초급 드릴)
- [Monotonic Deque vs Heap for Window Extrema](monotonic-deque-vs-heap-for-window-extrema.md) (6-line beginner router box for `deque vs heap vs other`, duplicate vs stale-entry comparison table, worst-case heap growth)

## monotonic stack 관련 문서

- [Monotonic Stack Walkthrough](monotonic-stack-walkthrough.md) (첫머리 `strictly` 번역 체크 1줄, next greater element, histogram largest rectangle, index vs value, `previous/next smaller/greater` while 조건 템플릿 표, `previous vs next`와 `strict/or-equal`을 한 번에 자르는 compact 미니 퀴즈, 연산자/flush 기준)
- [Monotonic Duplicate Rule Micro-Drill](monotonic-duplicate-rule-micro-drill.md) (`<` vs `<=`, `>` vs `>=`를 `이전 값 유지 vs 새 값 대체` 규칙과 작은 duplicate 예제로 바로 고정하는 초급 드릴)
- [Monotonic Deque vs Monotonic Stack Shared-Input Drill](monotonic-deque-vs-stack-shared-input-drill.md) (먼저 [Monotonic Structure Router Quiz](monotonic-structure-router-quiz.md)로 `deque vs stack vs neither`를 고른 뒤, 같은 입력에서 `window max/min`과 `NGE/PSE`를 함께 비교하고 duplicate add-on으로 `<` vs `<=`, `>` vs `>=` 차이까지 짧게 고정하는 초급 손추적 드릴)
- [Monotonic Structure Router Quiz](monotonic-structure-router-quiz.md) (`signal -> 선택 구조` 1페이지 표와 6문항으로 `deque vs stack vs neither` 첫 분기를 빠르게 잡고, `neither` 안의 `map/freq sliding window` vs `interval overlap`도 짧은 handoff 예제로 나눠 주는 첫 독서용 라우팅 퀴즈)
- [Monotonic Queue / Stack](monotonic-queue-and-stack.md) (상단 초급 5줄 멘탈 모델 박스로 `좋은 후보만 남긴다` 감각부터 잡고, sliding window maximum/minimum과 recent `k` extrema로 내려가는 브리지)

## 순서 유지와 캐시

트리 문제에서 "루트를 먼저 기록하나, 자식 결과를 모아 부모를 계산하나, 아니면 레벨별로 보나"가 먼저 막히면 [Binary Tree Traversal Routing Guide](binary-tree-traversal-routing-guide.md)에서 `preorder/inorder/postorder/level-order` signal을 먼저 분리한 뒤 BST/heap/segment tree 문서로 내려가면 된다.

plain `BST`가 왜 입력 순서에 따라 `O(n)`까지 무너지는지부터 헷갈리면 [Balanced BST vs Unbalanced BST Primer](balanced-bst-vs-unbalanced-bst-primer.md)에서 `높이` 관점을 먼저 잡고, 이어서 [TreeMap, HashMap, LinkedHashMap 비교](treemap-vs-hashmap-vs-linkedhashmap.md)와 [Skip List](skip-list.md)로 내려가면 ordered set/map 선택 이유가 훨씬 또렷해진다. 이번 정리에는 `lower/floor/ceiling/higher`가 범위를 벗어날 때 `null`을 돌려주는 한 줄 경계표도 추가되어, `TreeMap` 첫 사용에서 나오는 NPE 실수를 바로 잡기 쉽다.

`LinkedHashMap`을 쓰는데 조회만 했더니 순서가 바뀌는 현상이 먼저 보이면 [LinkedHashMap access-order 미니 프라이머](linkedhashmap-access-order-mini-primer.md)에서 `삽입 순서 vs 접근 순서`를 1페이지로 분리한 뒤, 필요할 때만 [LRU 캐시 설계 입문 (LRU Cache Basics)](lru-cache-basics.md)으로 내려가면 된다. 핵심은 "최근에 넣은 것"이 아니라 "최근에 만진 것" 기준이라는 점이다.

`HashMap`인지 `LinkedHashMap`인지 `TreeMap`인지부터 헷갈려 "왜 출력 순서가 바뀌지?"가 첫 증상이라면 [Map order symptom router card](map-order-symptom-router-card.md)에서 `순서 계약 없음 / 삽입 순서 / key 정렬 / access-order` 4갈래로 먼저 자르는 편이 더 빠르다.

## 범위 질의와 예약 탐색

예약/캘린더/gap-check 문제에서 `lower/floor/ceiling/higher`가 아직 손에 안 붙으면 먼저 [TreeSet Exact-Match Drill](treeset-exact-match-drill.md)에서 값만 있는 정렬 줄로 `strict/inclusive`를 떼어 연습한다. exact match 다음으로 `subSet/headSet/tailSet` 같은 단순 range slicing을 붙이고 싶다면 [TreeSet Range View Mini Drill](treeset-range-view-mini-drill.md)로 넘어간다. 그다음 [TreeMap Neighbor-Query Micro Drill](treemap-neighbor-query-micro-drill.md)에서 `왼쪽/오른쪽` 감각을 예약표로 옮겨 보고, `끝 시각과 다음 시작 시각이 같으면 겹치나요?`, `[start, end)`가 뭐예요?`가 먼저 막히면 [Reservation Interval Half-Open Boundary Card](reservation-interval-half-open-boundary-card.md)로 경계 규칙을 먼저 고정하는 편이 덜 막힌다.

## 예약 탐색 다음 한 걸음

그다음에는 `lowerKey/floorKey/ceilingKey/higherKey`를 `lowerEntry/floorEntry/ceilingEntry/higherEntry`로 연결하는 [TreeMap Key/Entry Strictness Bridge](treemap-key-entry-strictness-bridge.md)를 끼워 넣고, 오전/오후 시간창만 먼저 잘라 보고 싶다면 [TreeMap `subMap` Schedule-Window Mini Drill](treemap-submap-schedule-window-mini-drill.md)에서 `오전 창`, `점심 포함 오후 창`, `점심 이후 창`을 손으로 예측해 본다. 이후 [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](treemap-floorentry-ceilingentry-value-read-micro-drill.md)에서 `entry.getValue()`로 종료 시각 읽기를 붙이고, 질문이 바로 `30분 빈 시간 있나?`라면 [TreeMap Gap Detection Mini Drill](treemap-gap-detection-mini-drill.md)에서 free-slot 길이 판단을 한 번 더 손으로 맞힌다. `왜 next.end로 점프해도 안전한가`, `이 규칙이 왜 disjoint interval state와 이어지나`가 궁금해지면 [TreeMap Nearest-Slot Jump to Disjoint Interval Set Bridge](treemap-nearest-slot-disjoint-interval-bridge.md)로 intermediate 한 칸을 밟고, 마지막으로 [TreeMap Interval Entry Primer](treemap-interval-entry-primer.md)와 [Disjoint Interval Set](disjoint-interval-set.md)로 들어가 충돌 검사와 canonical state 유지를 함께 묶으면 된다.

`ceiling/floor` 이름까지는 익혔는데도 `다음 예약`을 찾을 때 자꾸 `PriorityQueue.poll()`로 손이 가면, [PriorityQueue.poll() vs TreeMap `ceiling`/`floor` Schedule Bridge](priorityqueue-poll-vs-treemap-ceiling-floor-schedule-bridge.md)에서 `global min extraction`과 `x 기준 이웃 조회`를 한 번 더 분리한 뒤 돌아오는 편이 안전하다. 특히 `TreeMap<start, reservation>`처럼 value까지 읽어야 하는 schedule에서는 `ceilingEntry`/`floorEntry` 쪽이 follow-up query에 더 직접적이다.

## ordered search와 layout

정적 ordered search locality를 비교하려면 `Cache-Aware Data Structure Layouts -> Ordered Search Workload Matrix -> Eytzinger Layout and Cache-Friendly Search -> van Emde Boas Layout vs Eytzinger vs Blocked Arrays -> Cache-Oblivious B-Tree / Leaf-Packed Variants vs Plain vEB Layout -> Hybrid Top-Index / Leaf Layouts -> Cache-Oblivious vs Cache-Aware Layouts` 순서로 읽으면 workload triage, point lookup, `lower_bound` 뒤 scan 연결, pure vEB binary와 scan-friendly leaf layout의 차이, top guide와 contiguous leaf의 역할 분리, 재귀 배치의 선택축이 함께 잡힌다.

interval이 처음부터 전부 주어져 한 번 계산하면 끝나는 문제가 아니라, 새 interval이 계속 들어오며 `insert -> overlap query`가 섞이면 `segment tree`보다 [Interval Tree](interval-tree.md)나 [Disjoint Interval Set](disjoint-interval-set.md)을 먼저 보는 편이 맞다.
`segment tree`라는 이름 때문에 ordered tree나 priority tree처럼 읽히면 먼저 [Segment Tree Is Not BST or Heap](segment-tree-not-bst-or-heap-bridge.md)에서 역할을 분리하고, 그다음 [Fenwick Tree vs Segment Tree](fenwick-vs-segment-tree.md)와 [Segment Tree Lazy Propagation](segment-tree-lazy-propagation.md)으로 내려가면 혼선이 적다.

## connectivity와 union-find

연결성에서 매번 헷갈리면 아래 3줄만 먼저 잡아도 된다.
1. `같은 그룹인가?`, `갈 수 있나?`처럼 yes/no만 필요하면 union-find 쪽으로 먼저 간다.
2. `실제 경로 하나`를 보여 달라는 말이면 DFS/BFS로 `parent`를 남겨 복원한다. 이 경로가 shortest일 필요는 없다.
3. `가장 짧은/가장 싼 경로`를 묻는 순간 shortest-path 문제다. 알고리즘을 먼저 고르고 predecessor로 경로를 복원한다.
`같은 컴포넌트인가`, `connected components(연결 요소)가 몇 개인가`, `경로 하나를 복원하라`, `최단 경로를 구하라`가 한데 섞이면 [Connectivity Question Router](connectivity-question-router.md)에서 먼저 답의 모양을 `yes/no vs actual path vs minimum path`로 분리한 뒤 union-find / BFS / shortest-path 문서로 내려가면 된다. 이번 버전에는 `같은 팀이야?`, `이어져 있어?`, `연결요소가 몇 개야?`처럼 초급자가 실제로 던지는 질문 문장 pack도 함께 들어 있어 첫 분기 정확도를 바로 잡기 쉽다. yes/no만 먼저 익힐 때는 [Union-Find Standalone Beginner Primer](union-find-standalone-beginner-primer.md)로 들어가고, 여기에 `그룹 크기`, `전체 그룹 수`, `connected components(연결 요소) 수`가 붙으면 [Union-Find Component Metadata Walkthrough](union-find-component-metadata-walkthrough.md)로 넘기면 된다.
간선 추가만 있는 연결성의 첫 관문은 [Union-Find Standalone Beginner Primer](union-find-standalone-beginner-primer.md)이고, path compression과 union by size/rank까지 구조적으로 정리하려면 [Union-Find Deep Dive](union-find-deep-dive.md)로 내려가면 된다. 삭제가 섞이는 순간은 [Deletion-Aware Connectivity Bridge](deletion-aware-connectivity-bridge.md)에서 `왜 plain DSU가 안 되고 DSU rollback / dynamic connectivity로 넘어가는지`를 먼저 분리한 뒤 [DSU Rollback](../algorithm/dsu-rollback.md)로 이어 가면 된다.

## connectivity 관련 문서

- [Connectivity Question Router](connectivity-question-router.md) (same-component yes/no, `같은 팀인지`/`연결요소 몇 개인지` 같은 beginner query phrase pack, `yes/no vs path reconstruction vs shortest-path` micro-drill, `무가중치 BFS vs 가중치 Dijkstra` shortest-path handoff)
- [Union-Find Standalone Beginner Primer](union-find-standalone-beginner-primer.md) (same-component yes/no first stop, union-find vs BFS/DFS boundary, smallest hand trace)
- [Union-Find Deep Dive](union-find-deep-dive.md) (same-component yes/no, BFS/DFS traversal boundary, edge-addition-only connectivity)
- [Deletion-Aware Connectivity Bridge](deletion-aware-connectivity-bridge.md) (edge deletion handoff, DSU rollback/dynamic connectivity threshold)
- [Union-Find Component Metadata Walkthrough](union-find-component-metadata-walkthrough.md) (component size, component count, redundant union guard, `size[find(x)]` 기준)

## 근사 집계와 압축 표현

이 구간은 초보자용 첫 선택보다 "정확도와 메모리를 어떻게 바꿔 먹는가"를 따지는 심화 라우트다.
처음이면 sketch/filter와 roaring bitmap을 같은 층위로 외우기보다, 아래에서 필요한 축만 골라 내려가는 편이 빠르다.

## sketch와 filter

- [Bloom Filter](bloom-filter.md) (`exact membership` 정답 경로와 `approximate prefilter` 선필터를 초반 decision box로 분리)
- [Cuckoo Filter](cuckoo-filter.md) (`exact membership` 정답 경로와 `deletion 가능한 approximate prefilter` 선필터를 초반 decision box로 분리)
- [Quotient Filter](quotient-filter.md)
- [Xor Filter](xor-filter.md)
- [Bloom Filter vs Cuckoo Filter](bloom-filter-vs-cuckoo-filter.md)
- [Count-Min Sketch](count-min-sketch.md)
- [Space-Saving Heavy Hitters](space-saving-heavy-hitters.md)
- [HyperLogLog](hyperloglog.md)
- [HDR Histogram](hdr-histogram.md)
- [DDSketch](ddsketch.md)
- [KLL Sketch](kll-sketch.md)
- [t-Digest](t-digest.md)
- `[playbook]` [Sketch and Filter Selection Playbook](sketch-filter-selection-playbook.md)
- [Count-Min Sketch vs HyperLogLog](count-min-vs-hyperloglog.md)
- [Approximate Counting for Rate Limiting and Observability](approximate-counting-rate-limiting-observability.md)

## roaring bitmap 계열

- [BitSet vs boolean[] Beginner Card](bitset-vs-boolean-array-beginner-card.md)
- [BitSet vs Roaring Bitmap Beginner Handoff](bitset-vs-roaring-bitmap-beginner-handoff.md)
- [Plain BitSet vs Compressed Bitmap Decision Card](plain-bitset-vs-compressed-bitmap-decision-card.md)
- [Roaring Bitmap](roaring-bitmap.md)
- [Roaring Container Transition Heuristics](roaring-container-transition-heuristics.md)
- [Chunk-Boundary Pathologies In Roaring](chunk-boundary-pathologies-in-roaring.md)
- [Roaring Set-Op Result Heuristics](roaring-set-op-result-heuristics.md)
- [Roaring Bitmap-Wide Lazy Union Pipeline](roaring-bitmap-wide-lazy-union-pipeline.md)
- [Roaring Lazy Union And Repair Costs](roaring-lazy-union-and-repair-costs.md)
- [Roaring Intermediate Repair Path Guide](roaring-intermediate-repair-path-guide.md)
- [Roaring Query Result Ordering Guide](roaring-query-result-ordering-guide.md)
- [Roaring ANDNOT Result Heuristics](roaring-andnot-result-heuristics.md)
- [Roaring runOptimize Timing Guide](roaring-run-optimize-timing-guide.md)
- [Roaring Production Profiling Checklist](roaring-production-profiling-checklist.md)
- [Roaring Run-Churn Observability Guide](roaring-run-churn-observability-guide.md)

## bitmap 운영 playbook

- `[playbook]` [Bitmap Locality Remediation Playbook](bitmap-locality-remediation-playbook.md)
- [Roaring Instrumentation Schema Examples](roaring-instrumentation-schema-examples.md) (Prometheus/OpenTelemetry naming, adaptive sampling, bridge patterns)
- `[playbook]` [Roaring Bitmap Selection Playbook](roaring-bitmap-selection-playbook.md)
- [Compressed Bitmap Families: WAH, EWAH, CONCISE](compressed-bitmap-families-wah-ewah-concise.md)
- `[playbook]` [Row-Ordering and Bitmap Compression Playbook](row-ordering-and-bitmap-compression-playbook.md)
- [Warehouse Sort-Key Co-Design for Bitmap Indexes](warehouse-sort-key-co-design-for-bitmap-indexes.md)
- [Late-Arriving Rows and Bitmap Maintenance](late-arriving-rows-and-bitmap-maintenance.md)
- [Roaring Run Formation and Row Ordering](roaring-run-formation-and-row-ordering.md)

## succinct bitmap index

- [Succinct Bitvector Rank/Select](succinct-bitvector-rank-select.md)
- [Bit-Sliced Bitmap Index](bit-sliced-bitmap-index.md)
- [Bit-Sliced Bitmap Sort-Key Sensitivity](bit-sliced-bitmap-sort-key-sensitivity.md)
- [Elias-Fano Encoded Posting List](elias-fano-encoded-posting-list.md)
- [LSM-Friendly Index Structures](lsm-friendly-index-structures.md)

## 문자열 / Prefix 검색

- [Trie](applied-data-structures-overview.md#trie-트라이)
- [Trie vs HashMap: exact lookup이냐 prefix search냐](trie-vs-hashmap-exact-lookup-beginner-card.md)
- [Trie Prefix Search vs TreeMap Ordered Map Beginner Card](trie-prefix-search-vs-treemap-ordered-map-beginner-card.md)
- [TreeMap 문자열 Prefix vs 사전순 Range Mini Drill](treemap-string-prefix-range-mini-drill.md)
- [Trie Prefix Search / Autocomplete](trie-prefix-search-autocomplete.md)
- [Adaptive Radix Tree](adaptive-radix-tree.md)
- [Radix Tree](radix-tree.md)
- [Finite State Transducer](finite-state-transducer.md)

---

## 면접형 question bank

아래 구간은 설명 본문이 아니라 self-check용 질문 묶음이다. 막히는 항목은 다시 위의 `primer`, `catalog`, 개별 `deep dive` 문서로 돌아가서 보강한다.

## 질의응답

<details>
<summary>자료구조가 무엇인지 말씀해주세요.</summary>
<p>

자료구조는 컴퓨터 과학에서 `효율적인 접근 및 수정`을 가능케 하는 자료의 조직, 관리, 저장을 의미한다.
더 정확히 말해, 자료 구조는 데이터 값의 모임, 또 데이터 간의 관계, 그리고 데이터에 적용할 수 있는 함수나 명령을 의미한다.

</p>
</details>

<details>
<summary>선형 구조와 비선형 구조의 차이가 무엇인가요?</summary>
<p>

자료구조는 저장되는 데이터의 형태에 따라 구분된다. 선형 구조는 데이터가 일렬로 나열되어있고, 비선형 구조는 데이터가 특정한 형태를 띄고 있다.

</p>
</details>

<details>
<summary>배열과 연결 리스트의 차이점에 대해 설명해주세요.</summary>
<p>

배열은 동일한 자료형의 데이터를 일렬로 나열한 자료구조로서, 데이터 접근이 용이하나 데이터의 삽입과 삭제가 비효율적이다.

연결리스트는 각 노드가 데이터와 포인터를 가지고 일렬로 연결된 자료구조로서, 데이터의 접근이 O(n)으로 느리지만 데이터의 삽입과 삭제가 O(1)로 용이하다. 단, 데이터 삽입/삭제 연산 이전에 데이터에 접근하는 것이 선행되므로 배열보다 비효율적일 수 있다.

</p>
</details>

<details>
<summary>A-B-C-D 순서로 연결된 연결 리스트가 있습니다. C 노드 다음에 F 노드를 삽입할 때의 과정을 설명해주세요.</summary>
<p>

1. F의 next node를 C의 next node인 D로 설정한다.
   `A-B-C-D`
   `F-D`

2. C의 next node를 F로 설정한다.
   `A-B-C-F-D`

</p>
</details>

<details>
<summary>스택으로 큐를 구현할 수 있을까요?</summary>
<p>

네. 2개의 스택을 이용하여 구현할 수 있습니다. Enqueue 연산은 첫번째 스택에 원소를 추가하면 됩니다. Dequeue 연산은 두번째 스택을 이용합니다. 우선 두번째 스택이 비어있다면 첫번째 스택이 빌 때까지 첫번째 스택의 원소를 pop하고 두번째 스택에 push하는 것을 반복합니다. 그리고 두번째 스택이 비어있지 않다면 두번째 스택의 원소를 pop하면 됩니다.

</p>
</details>

<details>
<summary>큐로 스택을 구현할 수 있을까요?</summary>
<p>

네. 2개의 큐를 이용하여 구현할 수 있습니다. `push` 연산은 첫번째 큐에 원소를 추가하기 전에 첫번째 큐가 빌때까지 두번째 큐로 값을 옮겨줍니다. 그 후 첫번째 큐에 원소를 추가하고 두번째 큐에서 다시 첫번째 큐로 빌때까지 원소들을 전부 다시 옮겨줍니다. 쉽게 말하자면 원소를 추가할 때마다 원소들의 위치를 스택에 맞게 변경시키는 것입니다. `pop` 연산은 첫번째 큐에서 dequeue만 하면 됩니다.

</p>
</details>

## 질의응답: queue

<details>
<summary>큐와 덱의 차이점은 무엇일까요?</summary>
<p>

`큐` 는 front에서만 output이 발생하고 rear에서만 input이 발생하는 입출력의 방향이 제한되어 있는 자료구조이다. 반면 `덱` 은 양방향에서 입출력이 가능하다.

</p>
</details>

<details>
<summary>큐보다 덱을 사용했을 때 더 효율적인 경우가 있을까요?</summary>
<p>

스케줄링 알고리즘을 수행할 때 스케줄링이 복잡해질수록 덱이 더 효율적으로 동작한다. 즉, 우선순위를 관리하는 데 있어 스택과 큐에 비해 이점을 갖는다.
예를 들어 오래된 프로세스에 우선순위를 주고 싶다면 앞에 있는 프로세스를 빼내야하는데 이는 스택에서 불가능하고 최근에 들어온 프로세스에 우선순위를 두고 싶다면 큐에서 불가능하다. 반면 덱은 두 경우 모두에서 사용 가능하다.

</p>
</details>

## 질의응답: tree

<details>
<summary>트리라는 자료구조가 무엇인지 간략하게 한 줄로 설명해보세요.</summary>
<p>

자료들 사이의 계층적 관계를 나타내는데 사용하는 자료구조로 부모-자식관계로 표현합니다.

</p>
</details>

<details>
<summary>트리의 용어중 '깊이' 라는 용어의 정의는 무엇인가요?</summary>
<p>

루트 노드에서 해당노드까지 도달하는데 사용하는 간선의 개수며, 루트노드의 깊이는 0입니다.

</p>
</details>

<details>
<summary>포화 이진트리와 완전 이진트리의 차이점은 무엇인가요?</summary>
<p>

1. 포화 이진 트리(Perfect Binary Tree) : 정 이진트리(Full Binary Tree)에서 모든 단말 노드의 깊이가 같은 이진트리
2. 완전 이진 트리(Complete Binary Tree) : 마지막 레벨은 노드가 왼쪽에 몰려있고, 마지막 레벨을 제외하면 포화이진트리(Perfect Binary Tree) 구조를 띄고 있음

</p>
</details>

<details>
<summary>트리의 순회에 대해 알고있는 것 한 가지 말해주세요.</summary>
<p>

1. 전위 순회(Pre-order)  : __현재 노드 방문__ -> 왼쪽 자식 탐색 -> 오른쪽 자식 탐색
2. 중위 순회(In-order)   : 왼쪽 자식 탐색 -> __현재 노드 방문__ -> 오른쪽 자식 탐색
3. 후위 순회(Post-order) : 왼쪽 자식 탐색 -> 오른쪽 자식 탐색 -> __현재노드 방문__
4. 레벨 순회(Level-order): 같은 깊이의 노드를 왼쪽부터 차례대로 방문하며 보통 `queue/BFS`로 구현한다.
자세한 라우팅 기준은 [Binary Tree Traversal Routing Guide](binary-tree-traversal-routing-guide.md)를 참고한다.

</p>
</details>

## 질의응답: tree와 heap

<details>
<summary>구간합 문제를 누적합으로 풀이한다면, 단점은 무엇이며 그에 비해 인덱스 트리가 갖는 장점은 무엇인지 시간복잡도를 들어 설명해주세요.</summary>
<p>

누적합으로 풀 경우 누적합을 구하는데 O(N), 이를 M번 수행하면 O(MN)이 걸린다. 하지만 인덱스 트리를 사용할 경우 누적합을 구하는데 O(logN)이 걸리므로, 이를 M번 수행하면 O(MlogN)이 걸리기에 구간합을 여러차례 구하는 중간에 배열의 값이 바뀌는 경우 인덱스 트리가 적합하다.

</p>
</details>

<details>
<summary>인덱스 트리에서 삽입이 일어날때의 시간복잡도는 몇인가요?</summary>
<p>

수행시간은 O(logN)이다.

</p>
</details>

<details>
<summary>힙이란 무엇일까요?</summary>
<p>

힙은 최댓값 및 최솟값을 찾아내는 연산을 빠르게 하기 위해 고안된 완전이진트리를 기본으로 한 자료구조로서 다음과 같은 힙 속성을 만족한다.
A가 B의 부모노드 이면, A의 키값과 B의 키값 사이에는 대소관계가 성립한다.
최대 힙의 경우 `A > B`를 만족하고,
최소 힙의 경우 `A < B`를 만족한다.

이렇게 힙은 부모와 자식노드 간의 대소관계를 만족하는 `느슨한 정렬 상태`를 가진 자료구조이다.

</p>
</details>

<details>
<summary>그림의 힙 구조에서 삭제연산이 일어났을 때 힙의 변화를 서술하세요.</summary>
<p>

<img width="491" alt="스크린샷 2021-06-01 오전 11 47 16" src="https://user-images.githubusercontent.com/22493971/120898116-7b253f80-c664-11eb-9f84-39d795b36bff.png">

1. 루트 노드 값을 삭제한다. (44 삭제)
2. 가장 마지막 리프노드를 루트 노드로 이동한다. (14가 루트 노드로 이동)
3. Heapify 진행
> Heapify란 루트노드부터 시작하여 힙의 구조를 만족할 때까지 부모/자식 노드 간 Swap연산을 하며 밑으로 내려가는 연산을 의미한다.

     a. 현재 노드의 자식노드가 현재 노드보다 클 경우 SWAP한다. (14<->42) (14<->33)

<img width="491" alt="ㅋㅋ" src="https://user-images.githubusercontent.com/22493971/120898448-defc3800-c665-11eb-95f1-76d75ad804fd.png">

</p>
</details>

## 한 줄 정리

Data Structure (자료구조)는 백엔드 주니어가 `조회`, `순서`, `범위`, `탐색` 질문을 먼저 나눠 `map`, `queue`, `tree` 출발점을 고르게 돕는 문서다.
