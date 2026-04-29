# Algorithm (알고리즘)

> 한 줄 요약: 알고리즘 README는 백엔드 주니어가 문제를 읽었을 때 `무엇을 세는가`, `어떤 순서로 확장하는가`, `어떤 규칙으로 범위를 줄이는가`를 먼저 분리하게 돕는 입구 문서다.

**난이도: 🟢 Beginner**

관련 문서:

- [그래프 기초](../data-structure/graph-basics.md)
- [시간복잡도 입문](./time-complexity-intro.md)
- [DFS와 BFS 입문](./dfs-bfs-intro.md)
- [이분 탐색 입문](./binary-search-intro.md)
- [두 포인터 입문](./two-pointer-intro.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](../data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [큐 기초](../data-structure/queue-basics.md)

retrieval-anchor-keywords: algorithm readme, beginner algorithm routing, time complexity starter, dfs bfs starter, binary search intro, two pointer intro, dp intro, shortest path router, queue map bfs split, graph problem router, 처음 알고리즘 뭐부터, 알고리즘 입구, bfs queue map 왜 같이 나와요, bfs랑 queue 차이 뭐예요, queue vs bfs basics

## 길 잃었을 때 복귀 경로

이 README는 알고리즘 카테고리 navigator다. primer를 읽다가 헷갈리면 아래 두 단계만 다시 잡으면 된다.

| 지금 헷갈리는 문장 | 여기로 되돌아오기 | 바로 다음 안전한 한 걸음 |
|---|---|---|
| `BFS인지 queue인지 아직도 헷갈려요`, `왜 자꾸 map까지 섞이죠?` | [BFS, Queue, Map 먼저 분리하기](#bfs-queue-map-먼저-분리하기) | [큐 기초](../data-structure/queue-basics.md) -> [DFS와 BFS 입문](./dfs-bfs-intro.md) |
| `반으로 줄이는 건지, 양끝에서 좁히는 건지 모르겠어요` | [초보자 첫 분기](#초보자-첫-분기) | [이분 탐색 입문](./binary-search-intro.md) 또는 [두 포인터 입문](./two-pointer-intro.md) |
| `문제보다 자료구조 선택이 먼저 막혀요` | [먼저 자를 질문](#먼저-자를-질문) | [자료구조 README - 초급 10초 라우터](../data-structure/README.md#초급-10초-라우터) |
| `queue/map는 정리됐는데 이게 계산 규칙인지 Service 책임인지 모르겠어요` | [옆 카테고리로 잠깐 갔다가 돌아오기](#옆-카테고리로-잠깐-갔다가-돌아오기) | [Software Engineering README - 연결해서 보면 좋은 문서](../software-engineering/README.md#연결해서-보면-좋은-문서-cross-category-bridge) |

## 프라이머에서 다시 돌아오는 자리

입문 문서를 읽고 다시 길이 흐려질 때 보는 복귀 표다.

| 방금 읽은 primer | 이 README에서 다시 붙일 자리 | 바로 다음 한 걸음 |
|---|---|---|
| [Backend Algorithm Starter Pack](./backend-algorithm-starter-pack.md) | [초보자 첫 분기](#초보자-첫-분기) | `최소 이동`이면 [DFS와 BFS 입문](./dfs-bfs-intro.md), `경계값`이면 [이분 탐색 입문](./binary-search-intro.md)으로 한 장만 고른다 |
| [Backend Data-Structure Starter Pack](../data-structure/backend-data-structure-starter-pack.md) | [먼저 자를 질문](#먼저-자를-질문) | `queue/map`를 먼저 골랐다면 `최소 이동`, `반으로 줄이기`, `양끝 좁히기` 중 질문 모양을 다시 잘라 [DFS와 BFS 입문](./dfs-bfs-intro.md) 또는 [이분 탐색 입문](./binary-search-intro.md) 한 장만 고른다 |
| [그래프 기초](../data-structure/graph-basics.md) | [그래프 입문 10분 루트](#그래프-입문-10분-루트) | [DFS와 BFS 입문](./dfs-bfs-intro.md) |
| [큐 기초](../data-structure/queue-basics.md) | [BFS, Queue, Map 먼저 분리하기](#bfs-queue-map-먼저-분리하기) | [DFS와 BFS 입문](./dfs-bfs-intro.md) |

## 프라이머에서 다시 돌아오는 자리 (계속 2)

| 방금 읽은 primer | 이 README에서 다시 붙일 자리 | 바로 다음 한 걸음 |
|---|---|---|
| [DFS와 BFS 입문](./dfs-bfs-intro.md) | [초보자 첫 분기](#초보자-첫-분기) | [Connectivity Question Router](../data-structure/connectivity-question-router.md) 또는 [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) |
| [이분 탐색 입문](./binary-search-intro.md) | [먼저 자를 질문](#먼저-자를-질문) | [두 포인터 입문](./two-pointer-intro.md)과 헷갈리는지 한 번 더 확인한다 |
| [자료구조 README - 초급 10초 라우터](../data-structure/README.md#초급-10초-라우터) | [먼저 자를 질문](#먼저-자를-질문) | `queue/map`이 먼저였는지, `최소 이동/반으로 줄이기`가 먼저였는지 다시 잘라 [DFS와 BFS 입문](./dfs-bfs-intro.md) 또는 [이분 탐색 입문](./binary-search-intro.md) 한 장만 고른다 |
| [Software Engineering README - 연결해서 보면 좋은 문서](../software-engineering/README.md#연결해서-보면-좋은-문서-cross-category-bridge) | [옆 카테고리로 잠깐 갔다가 돌아오기](#옆-카테고리로-잠깐-갔다가-돌아오기) | `Service 책임` 문장을 걷어내고 [BFS, Queue, Map 먼저 분리하기](#bfs-queue-map-먼저-분리하기) 또는 [먼저 자를 질문](#먼저-자를-질문)으로 다시 한 칸만 고른다 |

## 복귀 후 한 줄 규칙

`왜 bfs랑 queue가 같이 나와요`가 다시 나오면 이 표에서 한 칸만 고르면 된다.

## 그래프 입문 10분 루트

백엔드 주니어가 `graph`, `bfs`, `queue`, `최소 이동 횟수`를 한 번에 만나면 보통 여기서 막힌다. 이때는 알고리즘을 더 넓게 보지 말고 아래 순서로 좁히는 편이 가장 안전하다.

| 지금 보이는 증상 | 먼저 볼 문서 | 여기서 얻는 mental model |
|---|---|---|
| `그래프가 뭐예요?`, `정점/간선이 아직 추상적이에요` | [그래프 기초](../data-structure/graph-basics.md) | 그래프는 구조라는 감각 |
| `트리 DFS랑 그래프 DFS가 같은 말 같아요` | [트리 기초](../data-structure/tree-basics.md) -> [Tree DFS Template Cheat Sheet](./tree-dfs-template-cheat-sheet.md) | 계층 순회와 일반 그래프 탐색을 분리 |
| `왜 queue가 나오죠?`, `bfs랑 queue가 같은 말인가요?` | [큐 기초](../data-structure/queue-basics.md) -> [DFS와 BFS 입문](./dfs-bfs-intro.md) | queue는 도구, BFS는 탐색 규칙이라는 분리 |
| `갈 수 있나`와 `최소 이동 횟수`를 자꾸 섞어요 | [DFS와 BFS 입문](./dfs-bfs-intro.md) -> [Connectivity Question Router](../data-structure/connectivity-question-router.md) | 연결 여부와 shortest path를 다른 질문으로 자르기 |
| `가중치`, `비용 합 최소`까지 같이 보여요 | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) | `간선 수 최소`와 `비용 합 최소`를 먼저 자르기 |

이 루트의 종료선은 `그래프는 구조`, `BFS는 최소 이동 횟수`, `queue는 구현 도구`를 분리하는 데까지다. `MST`, `위상 정렬`, `flow`, `weighted shortest path` 비교는 primer 두 장([그래프 기초](../data-structure/graph-basics.md), [DFS와 BFS 입문](./dfs-bfs-intro.md))을 지난 뒤에만 [그래프 관련 알고리즘](./graph.md)으로 넘긴다.

같은 문장을 어디에서 잘라야 하는지 헷갈리면 아래 한 줄 번역부터 다시 보면 된다.

| 원래 문장 | 자료구조로 읽으면 | 알고리즘으로 읽으면 |
|---|---|---|
| `queue를 써야 하나요?` | FIFO 도구가 필요한가 | 거리 순서 탐색에서 queue를 도구로 쓰는가 |
| `graph가 뭐예요?` | 정점과 간선으로 관계를 그리는 구조 | 그 구조 위에서 어떤 탐색을 할지 고르는 단계 |
| `최소 이동 횟수예요` | queue 이름보다 먼저 알고리즘 냄새가 난다 | BFS 시작 신호다 |

즉 `queue`, `graph`, `BFS`가 한 문제에 같이 보여도 셋이 같은 층위는 아니다. beginner가 자주 하는 오진은 `도구 이름`과 `질문 종류`를 섞는 데서 시작한다.

## graph 문장을 10초 안에 다시 읽는 법

헷갈리면 `구조 -> 질문 -> 도구` 순서로 한 번만 다시 자르면 된다.

| 지금 먼저 보이는 것 | 먼저 붙일 mental model | 바로 다음 문서 |
|---|---|---|
| `graph`, `정점`, `간선`, `격자` | 연결 그림 자체가 구조다 | [그래프 기초](../data-structure/graph-basics.md) |
| `root`, `parent`, `left/right`, `전위/중위/후위` | 트리 순회 vocabulary가 먼저다 | [트리 기초](../data-structure/tree-basics.md), [Tree DFS Template Cheat Sheet](./tree-dfs-template-cheat-sheet.md) |
| `갈 수 있나`, `최소 이동 횟수`, `경로 하나` | 답의 모양을 먼저 자른다 | [DFS와 BFS 입문](./dfs-bfs-intro.md) |
| `queue`, `set/map`, `visited` | 구현 도구는 질문을 고른 뒤 붙인다 | [BFS, Queue, Map 먼저 분리하기](#bfs-queue-map-먼저-분리하기) |

- 초보자 기준 기본 순서는 `그래프 그림 이해 -> 질문 종류 분리 -> 구현 도구 선택`이다.
- `왜 queue부터 보면 안 돼요?`라는 질문에는 `도구보다 먼저 문제 문장을 잘라야 BFS/queue 오진이 줄기 때문`이라고 답하면 된다.

## 그래프 입문 오진 교정
바로 아래 오진 교정표까지 같이 보면 entrypoint가 더 선명해진다.

| 헷갈린 첫 문장 | 먼저 고칠 생각 | 첫 문서 |
|---|---|---|
| `queue가 보이니까 BFS죠?` | queue는 BFS 구현 도구일 수 있지만, 작업 FIFO일 수도 있다 | [큐 기초](../data-structure/queue-basics.md) |
| `전위/중위/후위도 DFS니까 graph DFS랑 완전히 같죠?` | 트리는 순회 패턴, 일반 그래프는 visited를 둔 탐색이라는 차이를 먼저 본다 | [Tree DFS Template Cheat Sheet](./tree-dfs-template-cheat-sheet.md), [DFS와 BFS 입문](./dfs-bfs-intro.md) |
| `graph가 보이니까 최단 경로죠?` | graph 문제도 연결 여부, 경로 하나, 최단 경로로 갈라진다 | [그래프 기초](../data-structure/graph-basics.md) -> [DFS와 BFS 입문](./dfs-bfs-intro.md) |
| `최소면 다 BFS죠?` | `최소 이동 횟수`와 `최소 비용`은 다르다 | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) |

같은 물류 장면이라도 질문이 달라지면 출발점도 바로 달라진다.

| 같은 장면에서 나온 문장 | 실제로 먼저 답할 것 | 첫 출발점 |
|---|---|---|
| `창고 A에서 B로 갈 수 있나?` | yes/no 연결 여부 | [Connectivity Question Router](../data-structure/connectivity-question-router.md) |
| `창고 A에서 B까지 아무 경로 하나만 보여줘` | 경로 하나 복원 | [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md) |
| `창고 A에서 B까지 최소 몇 번 이동하나?` | 최소 간선 수 | [DFS와 BFS 입문](./dfs-bfs-intro.md) |
| `창고 A에서 B까지 비용 합이 최소인가?` | 최소 비용 | [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md) |

`창고-도로` 비유는 entry ramp일 뿐이다. 실제 graph는 화면 칸, 사용자 상태 전이, 서비스 간 연결처럼 눈에 안 보이는 관계도 포함하므로, 비유를 그대로 구현 규칙으로 오해하면 다시 헷갈린다.

## 먼저 자를 질문

알고리즘 이름보다 문제 문장을 먼저 번역하면 길을 빨리 잡을 수 있다.

| 먼저 자를 질문 | 초보자용 첫 번역 | 먼저 볼 문서 |
|---|---|---|
| `무엇을 세는가?` | 횟수, 거리, 비용, 경우의 수 중 하나를 먼저 고른다 | [시간복잡도 입문](./time-complexity-intro.md), [동적 계획법 입문](./dp-intro.md) |
| `그래프 자체가 아직 낯선가?` | 정점/간선부터 먼저 잡는다 | [그래프 기초](../data-structure/graph-basics.md) |
| `어떤 순서로 확장하나?` | 가까운 것부터 퍼지는지, 끝까지 파고드는지 본다 | [DFS와 BFS 입문](./dfs-bfs-intro.md) |
| `어떤 규칙으로 범위를 줄이나?` | 정렬된 절반을 버리는지, 양끝을 좁히는지 본다 | [이분 탐색 입문](./binary-search-intro.md), [두 포인터 입문](./two-pointer-intro.md) |
| `자료구조 선택이 먼저인가?` | 탐색보다 queue/map 선택이 먼저인지 확인한다 | [큐 기초](../data-structure/queue-basics.md), [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](../data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md) |

## 초보자 첫 분기

| 문제 문장 | 먼저 볼 문서 | 왜 여기서 시작하나 |
|---|---|---|
| `최소 이동 횟수`, `가까운 칸부터`, `환승 최소` | [DFS와 BFS 입문](./dfs-bfs-intro.md) | queue는 도구이고 핵심은 unweighted shortest path다 |
| `그래프가 뭐고 정점/간선이 뭔지부터 헷갈린다` | [그래프 기초](../data-structure/graph-basics.md) | 문제 풀이 전에 자료구조 그림부터 붙여야 BFS/DFS가 덜 추상적이다 |
| `같은 그룹인가`, `연결요소가 몇 개인가` | [Connectivity Question Router](../data-structure/connectivity-question-router.md) | 연결성 질문과 최단 경로 질문을 먼저 가른다 |
| `MST`, `위상 정렬`, `가중치 최단 경로`까지 한 번에 섞여 보인다 | [그래프 기초](../data-structure/graph-basics.md) -> [DFS와 BFS 입문](./dfs-bfs-intro.md) -> [그래프](./graph.md) | primer 두 장으로 질문 종류를 먼저 자른 뒤에만 심화 그래프 라우터로 내려간다 |
| `반으로 줄여 찾기` | [이분 탐색 입문](./binary-search-intro.md) | 정렬 구간을 줄이는 규칙이 핵심이다 |
| `정렬은 했는데 왜 \`binarySearch\` 결과가 이상하지?` | [Sorting and Searching Arrays Basics](../language/java/java-array-sorting-searching-basics.md) -> [`Arrays.sort(...)` 뒤 `binarySearch(...)` 전제 브리지](../language/java/arrays-sort-binarysearch-precondition-bridge.md) | Java 라이브러리 전제를 먼저 정리한 뒤 알고리즘 패턴으로 넘어가야 덜 헷갈린다 |
| `양끝에서 좁히기`, `두 수의 합`, `연속 구간` | [두 포인터 입문](./two-pointer-intro.md) | 포인터 이동 규칙이 핵심이다 |

## 처음 15분 읽기 루트

알고리즘을 오래 붙잡기 전에 "문제에서 무엇을 먼저 세는가"만 고정해도 첫 분기 실수가 크게 줄어든다.

| 지금 막힌 문장 | 15분 첫 루트 | 왜 이 순서가 쉬운가 |
|---|---|---|
| `최소 이동 횟수`, `가까운 칸부터` | [큐 기초](../data-structure/queue-basics.md) -> [DFS와 BFS 입문](./dfs-bfs-intro.md) | queue 도구 감각을 먼저 잡고 BFS 거리 감각으로 넘어간다 |
| `그래프 정점/간선부터 안 잡힌다` | [그래프 기초](../data-structure/graph-basics.md) -> [DFS와 BFS 입문](./dfs-bfs-intro.md) | 자료구조 그림을 먼저 잡아야 탐색 순서 설명이 덜 추상적이다 |
| `MST`, `가중치 최단 경로`, `위상 정렬`이 바로 눈에 들어온다 | [그래프 기초](../data-structure/graph-basics.md) -> [DFS와 BFS 입문](./dfs-bfs-intro.md) -> [그래프](./graph.md) | primer 두 장으로 질문 종류를 먼저 자른 뒤 심화 비교로 가는 편이 beginner-safe 하다 |
| `id로 바로 찾기`, `중복 체크` | [Backend Data-Structure Primer](../data-structure/backend-data-structure-starter-pack.md) -> [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](../data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md) | 알고리즘 전에 자료구조 첫 선택 실수를 줄인다 |
| `반으로 줄여 찾기` | [시간복잡도 입문](./time-complexity-intro.md) -> [이분 탐색 입문](./binary-search-intro.md) | 왜 `O(log n)`이 되는지 먼저 붙인다 |
| `Java에서 정렬 후 검색 결과가 이상하다` | [Sorting and Searching Arrays Basics](../language/java/java-array-sorting-searching-basics.md) -> [`Arrays.sort(...)` 뒤 `binarySearch(...)` 전제 브리지](../language/java/arrays-sort-binarysearch-precondition-bridge.md) -> [이분 탐색 입문](./binary-search-intro.md) | `정렬 여부`와 `검색 기준 일치`를 먼저 분리하면 알고리즘 경계 설명이 덜 과부하다 |
| `경우를 다 해 봐야 하나` | [재귀 입문](./recursion-intro.md) -> [완전 탐색 입문](./brute-force-intro.md) | 호출 흐름을 먼저 이해하면 brute force가 덜 무겁다 |

## 옆 카테고리로 잠깐 갔다가 돌아오기

알고리즘 primer를 읽다가 자료구조나 Java 전제가 먼저 막히면, 옆 카테고리 문서를 짧게 보고 다시 이 README로 돌아오는 편이 초심자에게 더 안전하다.

| 지금 먼저 막힌 문장 | 잠깐 다녀올 문서 | 돌아올 자리 |
|---|---|---|
| `BFS인지 queue인지 아직도 헷갈려요`, `왜 queue가 나오지?` | [자료구조 README - 초급 10초 라우터](../data-structure/README.md#초급-10초-라우터) | [BFS, Queue, Map 먼저 분리하기](#bfs-queue-map-먼저-분리하기) |
| `정렬은 했는데 왜 \`binarySearch\`가 이상해요?`, `처음이라 전제가 뭐예요?` | [Sorting and Searching Arrays Basics](../language/java/java-array-sorting-searching-basics.md), [`Arrays.sort(...)` 뒤 `binarySearch(...)` 전제 브리지](../language/java/arrays-sort-binarysearch-precondition-bridge.md) | [초보자 첫 분기](#초보자-첫-분기) |
| `서비스 규칙 설명보다 collection 선택이 먼저 막혀요` | [자료구조 README - 먼저 자를 질문](../data-structure/README.md#먼저-자를-질문) | [먼저 자를 질문](#먼저-자를-질문) |
| `이건 BFS가 아니라 Service 책임 얘기인가요?`, `queue/map가 보여도 어디서 끊어 읽죠?` | [Software Engineering README - 연결해서 보면 좋은 문서](../software-engineering/README.md#연결해서-보면-좋은-문서-cross-category-bridge) | [BFS, Queue, Map 먼저 분리하기](#bfs-queue-map-먼저-분리하기) |

옆 카테고리 문서를 보고 나면, 용어를 더 늘리기보다 이 README의 `초보자 첫 분기`나 `BFS, Queue, Map 먼저 분리하기`로 돌아와 문제 문장을 다시 번역하는 편이 beginner-safe 하다.
특히 `queue가 보여서 자료구조로 갔다가`, `Service 얘기 같아서 software-engineering으로 갔다가` 다시 돌아왔다면, 다음 한 걸음은 항상 [BFS, Queue, Map 먼저 분리하기](#bfs-queue-map-먼저-분리하기) 또는 [먼저 자를 질문](#먼저-자를-질문) 둘 중 하나로만 잡는다.
복귀 위치가 다시 흐려지면 [길 잃었을 때 복귀 경로](#길-잃었을-때-복귀-경로)에서 증상 문장을 다시 고르면 된다.

## BFS, Queue, Map 먼저 분리하기

입문자가 가장 자주 섞는 세 갈래는 `bfs`, `queue`, `map`이다.

| 문장 신호 | 실제로 묻는 것 | 첫 출발점 |
|---|---|---|
| `미로에서 출구까지 몇 칸?` | 간선 수가 최소인 경로 | [DFS와 BFS 입문](./dfs-bfs-intro.md) |
| `A에서 B로 갈 수 있어?`, `같은 그룹인가?` | 연결 여부 yes/no 또는 component 질문 | [Connectivity Question Router](../data-structure/connectivity-question-router.md) |
| `A에서 B까지 아무 경로나 하나 보여줘` | 실제 경로 하나 복원 | [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md) |
| `주문을 받은 순서대로 worker에 넘기기` | FIFO handoff 정책 | [큐 기초](../data-structure/queue-basics.md) |
| `회원 id로 주문을 바로 조회` | exact lookup | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](../data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md) |
| `visited를 boolean[]로 둘지 Set으로 둘지부터 막혀요` | 탐색 질문은 이미 정했고, 방문 기록 도구만 남은 상태 | [DFS와 BFS 입문](./dfs-bfs-intro.md) -> [Java BFS visited 배열 vs Set beginner card](./bfs-visited-array-vs-set-java-beginner-card.md) |

처음에는 아래 세 줄만 먼저 고정하면 충분하다.

- `먼저 온 요청을 차례대로 처리`면 queue
- `갈 수 있나`, `같은 그룹인가`면 connectivity
- `아무 경로 하나 보여줘`면 path reconstruction
- `key로 한 건 바로 찾기`면 map
- `거리 1, 2, 3 순서로 넓히기`면 BFS

헷갈리면 아래 순서로 다시 자르면 된다.

1. `무엇을 먼저 꺼내나?`가 핵심이면 자료구조 후보를 본다.
2. `갈 수 있나`, `같은 그룹인가?`가 핵심이면 connectivity부터 본다.
3. `몇 번 만에 닿나?`가 핵심이면 BFS부터 본다.
4. `방문 체크를 무엇으로 저장하나?`는 보조 도구 질문이다. `set/map`이 보여도 탐색 자체는 여전히 BFS/DFS일 수 있다.

## 초급자가 자주 섞는 오해

- `queue`가 보인다고 항상 자료구조 문제가 아니다. `최소 이동 횟수`면 핵심은 BFS다.
- `갈 수 있나?`와 `최소 이동 횟수인가?`를 안 자르면 BFS와 DSU, path reconstruction이 한데 섞인다.
- `map`이 보인다고 항상 알고리즘이 사라지는 것도 아니다. BFS/DFS 안의 `visited set/map`은 탐색 보조 도구다.
- `그래프`, `BFS`, `최단 경로`를 한 단어로 뭉개면 초반에 거의 반드시 섞인다. `그래프는 구조`, `BFS/DFS는 탐색`, `최단 경로는 질문 종류`로 따로 떼면 읽기 난도가 크게 내려간다.
- `visited`를 `boolean[]`로 둘지 `Set`으로 둘지 막히면 [Java BFS visited 배열 vs Set beginner card](./bfs-visited-array-vs-set-java-beginner-card.md)에서 sparse id / 문자열 key 분기를 먼저 자르면 된다.
- `연결되어 있나?`와 `최단 경로인가?`는 같은 그래프 문장처럼 보여도 질문이 다르다.
- `queue`와 `map`이 같이 나와도 보통은 충돌이 아니다. 예를 들어 BFS는 queue로 레벨을 관리하고 map/set으로 방문 여부나 거리를 기록한다.

짧은 번역 한 줄만 더 붙이면 초보자 오진이 줄어든다. `왜 queue인데 bfs예요?`는 탐색 규칙과 구현 도구를 섞은 질문이고, `왜 visited가 set/map예요?`는 탐색을 정한 뒤 저장 방식을 묻는 질문이다.

## 여기서 멈추고 다음으로 넘길 것

이 섹션의 목표는 `bfs`, `queue`, `map`을 분리하는 데까지다. 아래 주제는 초반 primer 범위를 넘기므로, 지금 막힌 질문이 명확할 때만 내려가면 된다.

- `최소 이동 횟수`와 `최소 비용`이 섞이면 [BFS vs Dijkstra shortest path mini card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- 그래프 질문 전체를 다시 자르고 싶으면 [그래프 관련 알고리즘](./graph.md)
- `visited[]`와 `Set` 구현 선택이 막히면 [Java BFS visited 배열 vs Set beginner card](./bfs-visited-array-vs-set-java-beginner-card.md)

처음 읽는 단계라면 여기서 더 넓히기보다 `DFS와 BFS 입문`, `이분 탐색 입문`, `두 포인터 입문` 중 지금 막힌 문서 한 장만 더 읽고 멈추는 편이 안전하다.

## 🟢 Beginner 입문 문서

처음 알고리즘을 공부하는 경우 아래 목록에서 **앞 5편 정도만 먼저** 읽는 것을 권장한다.

- [Backend Algorithm Starter Pack](backend-algorithm-starter-pack.md) — `정렬/이분 탐색/BFS/DFS/그리디/DP/shortest path` 중 어디서 시작할지 먼저 자르는 입구 문서
- [시간복잡도 입문](time-complexity-intro.md) — Big-O 감각 잡기, 루프 분석, `이중 for문` 시간복잡도 첫 판단
- [DFS와 BFS 입문](dfs-bfs-intro.md) — 그래프/트리 탐색 기초, 최단 경로 차이
- [Java BFS visited 배열 vs Set beginner card](bfs-visited-array-vs-set-java-beginner-card.md) — `boolean[]`와 `Set`을 sparse id / 문자열 key 기준으로 자르는 초급 카드
- [정렬 알고리즘 입문](sort-intro.md) — 버블/삽입/병합/퀵, 안정 정렬 의미
- [이분 탐색 입문](binary-search-intro.md) — O(log n) 탐색, Lower/Upper Bound 패턴
- [동적 계획법 입문](dp-intro.md) — 메모이제이션, Bottom-up DP, 점화식
- [그리디 vs DP 결정 카드](greedy-vs-dp-decision-card.md) — 반례 신호와 상태 정의 신호를 한 표로 묶어 첫 분기를 빠르게 잡는 beginner 카드
- [재귀 입문](recursion-intro.md) — base case, 콜 스택, 재귀 vs 반복문
- [그리디 알고리즘 입문](greedy-intro.md) — 탐욕 선택 속성, 거스름돈 예시, DP와 비교
- [두 포인터 입문](two-pointer-intro.md) — 양 끝 좁히기, O(n) 쌍 탐색, 슬라이딩 윈도우 차이
- [완전 탐색 입문](brute-force-intro.md) — 순열/조합/부분집합, 경우의 수 계산
- [백트래킹 입문](backtracking-intro.md) — 가지치기, N-Queen, visited 해제 패턴

자료구조 이름부터 헷갈린다면 알고리즘 문서로 더 내려가기 전에 [Backend Data-Structure Primer](../data-structure/backend-data-structure-starter-pack.md)에서 `map/set/queue/priority queue` 첫 분기를 먼저 잡는 편이 빠르다.
특히 BFS를 읽는데 큐 자체가 낯설다면 [큐 기초](../data-structure/queue-basics.md)를 먼저 1회독하고 돌아오면 `왜 queue가 레벨 순서를 보장하나`가 훨씬 빨리 붙는다.

## 기본 프라이머

아래 broad survey는 `입문 문서를 읽고 난 뒤 한 번에 훑는` 용도에 가깝다. 처음이라면 바로 아래 catalog보다 위의 beginner primer부터 타는 편이 안전하다.

## 알고리즘 기본 [▶︎ 🗒](basic.md)

- [시간복잡도와 공간복잡도](basic.md#시간복잡도와-공간복잡도)
- [상각 분석과 복잡도 함정](amortized-analysis-pitfalls.md)
- [이분 탐색 패턴](binary-search-patterns.md)
- 완전 탐색 알고리즘 (Brute Force)
- [DFS와 BFS](basic.md#dfs와-bfs) (BFS shortest-path 입문 프라이머, unweighted shortest-path handoff)
  - [순열, 조합, 부분집합](basic.md#순열-조합-부분집합)
- [백트래킹 (Backtracking)](basic.md#백트래킹-backtracking)
- [분할 정복법 (Divide and Conquer)](basic.md#분할-정복법-divide-and-conquer)
- [탐욕 알고리즘 (Greedy)](basic.md#탐욕-알고리즘-greedy)
- [탐욕 / Greedy 알고리즘 개요](greedy.md) (generic greedy landing page, proof vocabulary, interval/sweep/DP handoff)
- [동적 계획법 (Dynamic Programming)](basic.md#동적-계획법-dynamic-programming)

## 패턴 / 비교 카탈로그

이 아래 카탈로그는 `입문 분기`를 끝낸 뒤 필요한 주제만 집어 내려가는 follow-up 구간이다. `MST`, `flow`, `0-1 BFS`, `A*`처럼 이름이 먼저 보인다고 해서 첫 회독부터 모두 따라갈 필요는 없다.

## 알고리즘 응용

- [정렬 알고리즘](sort.md) (stable / unstable, comparison / non-comparison, preprocessing, interval merge vs scheduling sort key)
- [그래프](graph.md)
  - [그래프 문제 Decision Router](graph.md#그래프-문제-decision-router) (입문 프라이머 다음 단계의 그래프 분기 라우터)
  - [Shortest Path Router: Unweighted vs DAG vs Weighted](graph.md#shortest-path-router-unweighted-vs-dag-vs-weighted) (무가중치/BFS, DAG, weighted shortest-path 분기)
  - [Weighted Shortest Path Density Router: Sparse vs Dense](graph.md#weighted-shortest-path-density-router-sparse-vs-dense) (sparse-vs-dense shortest-path handoff)
  - [BFS vs Dijkstra shortest path mini card](bfs-vs-dijkstra-shortest-path-mini-card.md) (beginner shortest-path 1차 분기)
  - [Dijkstra, Bellman-Ford, Floyd-Warshall](dijkstra-bellman-ford-floyd-warshall.md) (weighted shortest path 전용 follow-up)
  - [Minimum Spanning Tree: Prim vs Kruskal](minimum-spanning-tree-prim-vs-kruskal.md) (MST follow-up)
  - [Kruskal에서 Union-Find가 끼는 순간](kruskal-union-find-beginner-bridge.md) (beginner MST cycle-check bridge)
  - [위상 정렬 패턴](topological-sort-patterns.md) (DAG ordering / dependency routing)
  - [Topological DP](topological-dp.md) (DAG shortest/longest path, dependency accumulation, critical path scheduling)

## 알고리즘 응용 (계속 1b)

- [Longest Increasing Subsequence Patterns](longest-increasing-subsequence-patterns.md) (subsequence optimization, tails + lower_bound, subsequence vs subarray)
- [두 포인터 (two-pointer)](two-pointer.md) (pair relation scan, same-direction / opposite-direction, contiguous index scan, schedule interval boundary)

## 알고리즘 응용 (계속 2)

- [슬라이딩 윈도우 패턴](sliding-window-patterns.md) (substring/subarray, fixed or variable window, `sum/count` window vs `max/min` deque branch, contiguous index interval, not schedule overlap)
- [Monotonic Queue / Stack](../data-structure/monotonic-queue-and-stack.md) (sliding window maximum/minimum, deque-based window state, contiguous index extrema)
- [Deque Router Example Pack](../data-structure/deque-router-example-pack.md) (plain deque vs monotonic deque vs 0-1 BFS quick split)
- [Monotone Deque Proof Intuition](monotone-deque-proof-intuition.md) (monotonic queue correctness, dominated candidate proof, amortized O(n), contiguous window proof, why back-pop is safe)
- `queue/deque/heap`라는 단어가 먼저 보여도 여기서는 구현 암기보다 패턴 분기가 우선이다. `앞에서 꺼내고 뒤에 넣는 순서`면 [큐 기초](../data-structure/queue-basics.md), `양끝에서 넣고 빼는 상태 관리`면 [덱 기초](../data-structure/deque-basics.md), `가장 작은 값/큰 값을 먼저 뽑기`면 [힙 기초](../data-structure/heap-basics.md)로 30초만 먼저 정리하고 돌아오면 초심자 오분류가 줄어든다.
- [구간 / Interval Greedy 패턴](interval-greedy-patterns.md) (activity selection, erase overlap intervals, minimum arrows, end-time sort, meeting rooms I boundary)
- [Sweep Line Overlap Counting](sweep-line-overlap-counting.md) (meeting rooms II, minimum meeting rooms, railway platform, hotel booking possible, event sweep, heap boundary)
- [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md) (unweighted vs DAG vs weighted router, negative-edge/single-source/all-pairs query anchors, A* handoff)

## 알고리즘 응용 (계속 3)

- [Topological DP](topological-dp.md) (DAG path optimization, topological relaxation, earliest finish time, critical path)
- [A* vs Dijkstra](a-star-vs-dijkstra.md) (goal-directed shortest path, A-star/astar alias, route-planning, maze-navigation, weighted point-to-point routing, target-fixed/source-to-target routing)
- [Sparse Graph Shortest Paths](sparse-graph-shortest-paths.md) (graph density phrasing, single-source weighted shortest path, route-planning to A* handoff, PQ Dijkstra, 0-1 BFS, 0/1 cost, deque/teleport-style shortest path, Dial)
- [Bitmask DP](bitmask-dp.md) (subset-state optimization, popcount-based small-n assignment, cost-matrix/TSP boundary)
- [Hungarian Algorithm Intuition](hungarian-algorithm-intuition.md) (optimal assignment, linear assignment, Kuhn-Munkres, 1:1 weighted matching)
- [네트워크 플로우 직관](network-flow-intuition.md) (bipartite matching, assignment reduction, max throughput, bottleneck/min-cut/cut-capacity reading)
- [Min-Cost Max-Flow Intuition](min-cost-max-flow-intuition.md) (costed assignment, cheapest matching, transportation problem, supply-demand allocation)
- [문자열 처리 알고리즘](string.md)
  - [KMP 알고리즘](string.md#문자열-패턴-매칭)

---

## 질의응답

<!-- 탐색 알고리즘 -->

<details>
<summary>DFS와 BFS의 장단점에 대해 각각 설명해 주세요.</summary>
<p>

1. BFS 장점
   1. 너비를 우선으로 탐색하기 때문에 답이 되는 경로가 여러개인 경우에도 최단경로임을 보장합니다.
   2. 최단 경로가 존재한다면, 어느 한 경로가 무한히 깊어진다 해도 최단경로를 반드시 찾을 수 있습니다.
   3. 노드의 수가 적고 깊이가 얕은 해가 존재할 때 유리합니다.
2. BFS 단점
   1. 재귀 호출을 사용하는 DFS와는 달리 큐를 이용해 다음에 탐색할 노드들을 저장합니다. 이 때, 노드의 수가 많을 수록 필요없는 노드들까지 저장해야하기 때문에 더 큰 저장공간이 필요합니다.
   2. 노드의 수가 늘어나면 탐색해야하는 노드 또한 많아지기 때문에 비현실적입니다.
3. DFS 장점
   1. BFS에 비해 저장공간의 필요성이 적고 백트래킹을 해야하는 노드들만 저장해주면 됩니다.
   2. 찾아야하는 노드가 깊은 단계에 있을 수록, 그 노드가 좌측에 있을 수록 BFS보다 유리합니다.
4. DFS 단점
   1. 답이 아닌 경로가 매우 깊다면, 그 경로에 깊이 빠질 우려가 있습니다.
   2. 내가 지금까지 찾은 최단경로가 끝까지 탐색 했을 때의 최단경로가 된다는 보장이 없습니다.

</p>
</details>

---

<!-- 정렬 알고리즘 -->

<details>
<summary>라이브러리 없이 정렬을 구현하려고 할 때 어떤 정렬 방식을 사용해 구현할 것이고 왜 그렇게 생각하는지 성능 측면에서 얘기를 해주세요.</summary>
<p>

(예시 답안)
퀵소트로 구현할 것입니다. 퀵소트는 average case에서 nlgn의 시간복잡도를 가지며 공간복잡도 측면에서도 제자리 정렬이기 때문에 좋은 성능을 가집니다. worst case의 경우 n^2의 시간복잡도를 가지지만 worst case가 나타날 경우는 확률적으로 매우 낮습니다. (자료가 n개일 때 오름차순 또는 내림차순 -> 2/n!)

</p>
</details>

<details>
<summary>퀵소트에서 최악의 경우 시간복잡도를 개선시킬 수 있는 방법이 있을까요?</summary>
<p>

피벗의 위치를 다르게 설정함으로써 시간복잡도를 개선시킬 수 있습니다. 일정한 위치에 대해서만(ex. 첫번째 element) 피벗을 설정하는 것보다 첫번째, 마지막 element 중 무작위로 선택한다거나 첫번째, 가운데, 마지막 element 중 중간값을 계산하여 피벗을 설정했을 때 시간복잡도를 더 개선시킬 수 있습니다.

</p>
</details>

<details>
<summary>머지소트의 분할 정복 과정에 대해 단계별로 설명해주세요.</summary>
<p>

- Divide : 초기 배열을 2개의 배열로 분할
- Conquer : 각 부분 배열을 정렬
- Combine : 부분 배열을 하나의 배열로 결합

</p>
</details>

---

<!-- MST -->

## 질의응답 (계속 2)

<details>
<summary>MST(Minimum Spanning Tree)를 구하는 알고리즘에 대해 설명하고, 각각 어떤 상황에서 사용하는 것이 적절한지 설명해 주세요.</summary>
<p>

> 정점의 개수 : V, 간선의 개수 : E

먼저 MST는 "모든 정점을 사이클 없이 연결할 때 전체 간선 가중치 합을 최소화하는 트리"를 구하는 문제입니다. 그래서 `한 시작점에서 각 정점까지의 최단 거리`를 구하는 shortest path 문제와는 목적 함수가 다릅니다. 그래프가 disconnected라면 MST 하나는 존재하지 않고, 각 연결 성분별 최소 트리를 구한 **minimum spanning forest**로 해석해야 합니다.

대표 알고리즘은 Prim과 Kruskal입니다.

- Prim: 현재까지 만든 트리에서 바깥으로 나가는 간선 중 가장 싼 간선을 계속 붙이는 frontier 확장 방식입니다. 인접 리스트/행렬처럼 adjacency 중심 표현과 잘 맞고, 우선순위 큐를 쓰면 보통 `O(E log V)`로 설명합니다. dense graph에서는 `O(V^2)` 형태 구현도 자주 씁니다.
- Kruskal: 간선을 가중치 오름차순으로 정렬해 사이클이 생기지 않는 간선만 채택하는 방식입니다. flat edge list 입력, sparse graph, Union-Find 조합과 잘 맞고 정렬 때문에 보통 `O(E log E)`입니다. disconnected 그래프에서는 끝까지 돌리면 minimum spanning forest가 남습니다.

정리하면 `모든 도시를 가장 싸게 모두 잇기`면 MST이고, `1번 도시에서 나머지 도시까지 가장 싸게 가기`면 shortest path입니다. 입력 표현이 adjacency 중심이면 Prim, 간선 목록 정렬과 cycle check가 중심이면 Kruskal이 더 자연스럽습니다.

더 자세한 비교는 [Minimum Spanning Tree: Prim vs Kruskal](minimum-spanning-tree-prim-vs-kruskal.md), shortest-path와의 구분은 [최단 경로 알고리즘 비교](dijkstra-bellman-ford-floyd-warshall.md)를 같이 보면 됩니다.

</p>
</details>

<details>
<summary>Minimum Spanning Tree를 찾기 위한 프림 알고리즘의 동작원리 또는 특징에 대해 설명해주세요</summary>
<p>

## 질의응답 (계속 3)

1. 시작 정점 하나를 현재 트리 집합으로 잡고, 그 집합에서 바깥으로 나가는 간선 중 최소 비용 간선을 선택해 트리를 확장합니다.
2. 즉 Prim은 "현재 트리의 frontier를 넓혀 가는 방식"이지, 시작점에서 다른 정점까지의 거리를 갱신하는 shortest path 알고리즘이 아닙니다.
3. 보통 `visited + priority queue`로 구현하며, 인접 리스트 기준으로는 `O(E log V)`로 설명합니다. dense graph에서는 인접 행렬 기반 `O(V^2)` 구현도 자주 씁니다.
4. 연결 그래프라면 간선을 `N-1`개 채우면 MST가 완성됩니다. 그래프가 disconnected라면 한 번의 실행으로 전체 MST 하나를 만들 수 없고, 각 컴포넌트마다 다시 시작해 minimum spanning forest를 만들어야 합니다.

</p>
</details>

<details>
<summary>Minimum Spanning Tree를 찾기 위한 크루스칼 알고리즘의 동작원리 또는 특징에 대해 설명해주세요</summary>
<p>

1. 그래프의 모든 간선을 가중치 오름차순으로 정렬한 뒤, 가장 싼 간선부터 순서대로 검토합니다.
2. 각 간선을 추가했을 때 사이클이 생기지 않으면 채택하고, 생기면 버립니다. 이 cycle check를 빠르게 하려고 보통 Union-Find를 씁니다.
3. Kruskal은 특정 시작 정점에서 거리를 줄이는 알고리즘이 아니라, 전역적으로 가장 싼 간선을 골라 전체 연결 비용을 최소화하는 MST 알고리즘입니다.
4. 간선을 `N-1`개 선택하면 연결 그래프의 MST가 완성됩니다. 그래프가 disconnected라면 끝까지 훑은 결과는 실패가 아니라 각 연결 성분의 최소 트리를 모아 둔 minimum spanning forest입니다.
5. 간선 목록이 이미 edge list로 주어지거나 sparse graph에서 cycle 여부 판단이 핵심일 때 특히 자연스럽고, 정렬 때문에 시간 복잡도는 보통 `O(E log E)`로 설명합니다.

</p>
</details>

---

<!-- 최단 경로 -->

<details>
<summary>최단경로를 구하기 위한 알고리즘을 두 가지 이상 말하고 어떤 차이점이 있는지 설명해주세요.</summary>
<p>

- 다익스트라 : 하나의 시작 정점 ~ 모든 다른 정점까지의 최단 경로를 구한다.
- 벨만포드 : 하나의 시작 정점 ~ 모든 다른 정점까지의 최단 경로를 구한다. + 가중치가 음수일 때도 사용이 가능하다. (음의 사이클 검사 가능)
- 플로이드 와샬 : 모든 정점 ~ 모든 정점까지의 최단 경로를 구한다.

</p>
</details>

<details>
<summary>다익스트라 알고리즘 동작원리 또는 특징을 시간복잡도와 연관지어 설명해주세요.</summary>
<p>

(방법 1)

## 질의응답 (계속 4)

1. 출발 노드 S에서 모든 노드들까지의 최단 거리를 저장하는 배열 D를 초기화한다.
2. 방문하지 않은 노드 중에서 최단 거리가 가장 짧은 노드를 선택한다. (D 배열 검사)
3. 선택한 노드를 거쳐 다른 노드로 가는 비용을 계산하여 최단 거리 배열 D를 갱신한다.
4. 모든 노드를 방문할 때까지 3, 4 과정을 반복한다.
5. 노드의 개수를 V라고 할 때, 총 V\*V번 연산이 필요하므로 `O(V^2)`의 시간복잡도를 가진다.

(방법 2 - 힙/우선순위큐 사용)

1. 출발 노드 S에 대하여 D 배열을 초기화할 때 D[S] = 0을 해준다. 이와 동시에 힙에 노드 정보(번호, 거리 : [S, 0])를 넣어준다.
2. 힙에서 맨 위에 있는 노드 I를 꺼낸다.
3. 만일 꺼낸 노드 I의 거리 정보가 현재 D[I]보다 크다면 이미 방문한 노드일 것이므로 무시한다.
4. I를 대상으로 다익스트라 알고리즘을 수행하는데, D 배열이 갱신될 경우 그 노드 정보를 힙에 넣는다.
5. 힙에 노드가 없을 때까지 2-4 과정을 반복한다.
6. 노드의 개수를 V, 간선의 개수를 E라고 할 때 시간 복잡도는 `O(ElogV)` 이다.

</p>
</details>

<details>
<summary>다익스트라 알고리즘에서 힙(우선순위큐)을 사용할 경우 어떤 점에서 시간복잡도가 개선이 되나요?</summary>
<p>

다익스트라 알고리즘에서 방문하지 않은 노드 중 최단 거리가 가장 짧은 노드를 선택하는 과정이 있는데, 이 과정에서 O(`노드의 개수`)만큼의 비용이 발생하게 됩니다. 힙(우선순위큐)을 사용할 경우 그 비용을 O(`log{힙에 저장한 노드의 개수}`)로 줄일 수 있습니다.

</p>
</details>

<details>
<summary>벨만포드 알고리즘 동작원리 또는 특징을 시간복잡도와 연관지어 설명해주세요.</summary>
<p>

1. 음의 가중치를 가지는 간선도 가능하므로, 음의 사이클의 존재 여부를 따져야 한다.
2. 최단 거리를 구하기 위해서 V - 1번 E개의 모든 간선을 확인한다.
3. 음의 사이클 존재 여부를 확인하기 위해서 한 번 더 (V번째) E개의 간선을 확인한다.
4. 이 때 거리 배열이 갱신되었다면, 그래프 G는 음의 사이클을 가진다.
5. 따라서 총 V x E 번 연산하므로 O(VE)의 시간복잡도를 가진다.

</p>
</details>

<details>
<summary>플로이드 와샬 알고리즘 동작원리 또는 특징을 시간복잡도와 연관지어 설명해주세요.</summary>
<p>

1. 사이클이 없다면 음수 가중치를 가져도 적용 가능하다.
2. 동적 계획법(Dynamic Programming)으로 접근한다.
3. 모든 가능한 경유지에 대해서 모든 정점 -> 모든 정점으로 가는 최단 거리를 확인하므로 연산 횟수는 V^3이고, 따라서 시간복잡도는 O(V^3)

</p>
</details>

---

<!-- 문자열 -->

<details>
<summary> KMP 알고리즘에 대해 설명해주세요. </summary>
<p>

## 질의응답 (계속 5)

Kunth, Morris, Prett이 만든 알고리즘이라서 각 이름의 앞자리를 따서 KMP라고 지어졌습니다. 문자열이 불일치할 때 그 다음 문자부터 다시 탐색을 시작하는 것이 아니라 지금까지 일치했던 정보들을 버리지 말고 재사용 함으로써 몇칸 정도는 건너 뛰어서 탐색하자는 아이디어에서 알고리즘이 탄생했습니다. 접두사와 접미사 정보를 가지고 문자열을 점프해가며 탐색하는데, Naive한 문자열 탐색 알고리즘이 O(NM)의 시간복잡도를 갖는 반면에 KMP알고리즘은 O(N+M)의 시간복잡도를 갖습니다.

</p>
</details>

<details>
<summary>라빈 카프 알고리즘에 대해 설명해주세요.</summary>
<p>

문자열의 해시함수값을 이용합니다. 탐색 대상 문자열의 길이를 M이라고 했을 때 글을 M칸씩, 한칸 한칸 옮겨가며 부분 문자열을 떼어내고 해시함수값을 구하여 탐색 문자열의 해시함수값과 비교합니다. 해시함수값 충돌이 없다는 가정하에 글의 길이를 N이라고 하면 O(N-M)의 시간복잡도를 갖습니다.

</p>
</details>

<details>
<summary>라빈 카프 알고리즘이 KMP보다 빠른가?</summary>
<p>

사실상 그렇지 않습니다. 탐색 문자열의 길이가 길어질 수록 해시함수값에 충돌이 생길 확률이 높습니다. 따라서 해시함수값이 일치한다고 무조건 문자가 일치한다고 보장할 수 없기 때문에 해시함수값이 일치했을 때 문자열을 직접 비교하는 2차적인 검증이 필요합니다. 따라서 평균적으로 라빈 카프 또한 O(N+M)의 시간복잡도가 요구됩니다.

</p>
</details>

<details>
<summary>자료구조의 한 종류인 트라이를 설명해주세요.</summary>
<p>

트라이는 문자열을 저장하고 효율적으로 탐색하기 위한 트리 형태의 자료구조이다. 기본적으로 k진트리 구조를 띠고 어떤 문자열 집합 S와 문자열 A가 있다고 할 때 A가 S안에 존재하는지 찾는데에 사용되는 자료구조이다.

</p>
</details>

<details>
<summary>트라이의 장점과 단점을 설명해주세요.</summary>
<p>

이분탐색은 탐색하는데에 있어 검색어의 최대 길이 M * 전체 데이터 N 중 O(M log N)을 사용하게 되는데 이에 반해 트라이는 문자열 탐색에서의 전체 데이터의 길이인 시간복잡도 O(N)을 가지게 되어 매우 효율적이다. 하지만 트라이의 단점은 공간 복잡도가 높다. 알파벳을 저장하는 형태라면 1 depth당 26개의 공간이 사용될 수 있다.

</p>
</details>

<details>
<summary>트라이 자료구조를 사용한 적이 있나요? 경험을 이야기해주세요.</summary>
<p>

모범 답안) 알고리즘을 공부하는 과정에서 트라이 자료구조를 이용하여 아호코라식 알고리즘을 작성하여 문제를 해결했던 경험이 있습니다. 아호코라식 알고리즘은 KMP에서 사용하는 Failure Function을 트라이로 확장시킨 알고리즘으로 문자열 탐색에 사용하였습니다.

</p>
</details>

---

## 질의응답 (계속 6)

<!-- 투포인터 -->
<details>
<summary> <strong>투포인터</strong>라는 알고리즘 문제 해결 전략이 있습니다. 어떤 알고리즘이고 주로 어떤 문제를 해결하는데 사용되나요?</summary>
<p>

배열을 가리키는 포인터 2개를 이용해서 포인터를 한칸 씩 움직이며 특정 구간 내에서 원하는 값을 얻을 때 사용합니다. 예를 들면 연속되는 배열의 구간 중 특정 조건을 만족하는 가장 짧은 구간을 구하는 문제에서 사용될 수 있습니다.

</p>
</details>

## 한 줄 정리

Algorithm (알고리즘)는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
