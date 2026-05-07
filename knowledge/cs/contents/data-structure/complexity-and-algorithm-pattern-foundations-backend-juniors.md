---
schema_version: 3
title: 백엔드 주니어를 위한 복잡도와 알고리즘 패턴 기초
concept_id: data-structure/complexity-algorithm-pattern-foundations-backend-juniors
canonical: false
category: data-structure
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 88
mission_ids:
- missions/baseball
- missions/lotto
- missions/roomescape
review_feedback_tags:
- backend-algorithm-foundation
- complexity-first-routing
- data-structure-to-algorithm-bridge
aliases:
- backend complexity algorithm foundations
- 백엔드 알고리즘 패턴 기초
- 우테코 백엔드 알고리즘 입문
- 정렬 이분탐색 BFS DFS 뭐부터
- 자료구조에서 알고리즘으로 넘어가기
- beginner Big-O router backend
- backend junior algorithm foundation
symptoms:
- 백엔드 미션이나 알고리즘 문제에서 입력 크기와 답의 모양을 먼저 보지 않고 유명한 기법 이름부터 붙인다
- 정렬, 이분 탐색, BFS/DFS, 구현/시뮬레이션, priority queue가 어떤 문제 신호에서 나오는지 섞인다
- 자료구조 선택과 알고리즘 패턴 선택을 분리된 챕터로만 보고 실제 문제 문장에 함께 적용하지 못한다
intents:
- mission_bridge
- troubleshooting
prerequisites:
- data-structure/backend-data-structure-starter-pack
- algorithm/time-complexity-intro
next_docs:
- algorithm/backend-algorithm-starter-pack
- algorithm/time-complexity-intro
- algorithm/binary-search-intro
- algorithm/dfs-bfs-intro
- algorithm/sort-intro
linked_paths:
- contents/data-structure/backend-data-structure-starter-pack.md
- contents/algorithm/backend-algorithm-starter-pack.md
- contents/algorithm/time-complexity-intro.md
- contents/algorithm/binary-search-intro.md
- contents/algorithm/dfs-bfs-intro.md
- contents/algorithm/sort-intro.md
- contents/data-structure/queue-vs-deque-vs-priority-queue-primer.md
- contents/data-structure/graph-basics.md
confusable_with:
- algorithm/backend-algorithm-starter-pack
- data-structure/backend-data-structure-starter-pack
- algorithm/time-complexity-intro
- algorithm/dfs-bfs-intro
- algorithm/binary-search-intro
forbidden_neighbors: []
expected_queries:
- 백엔드 주니어가 알고리즘 문제를 볼 때 입력 크기와 답의 모양을 어떻게 먼저 봐야 해?
- 정렬 이분 탐색 BFS DFS 구현 중 첫 패턴을 문제 문장에서 고르는 방법은?
- 자료구조 선택과 알고리즘 패턴 선택을 미션 문제에서 같이 보는 법을 알려줘
- Big-O가 불안할 때 어떤 풀이를 먼저 버려야 하는지 beginner 기준으로 설명해줘
- priority queue queue graph sort binary search가 나오는 신호를 한 번에 정리해줘
contextual_chunk_prefix: |
  이 문서는 Woowacourse 백엔드 주니어가 자료구조와 알고리즘을 별개
  암기 과목으로 보지 않고, 입력 크기와 답의 모양으로 정렬, 이분 탐색,
  BFS/DFS, priority queue, 구현/시뮬레이션을 고르는 mission bridge다.
---
# 백엔드 주니어를 위한 복잡도와 알고리즘 패턴 기초

> 한 줄 요약: 백엔드 미션에서 알고리즘은 "유명한 기법 이름"보다 먼저 입력 크기와 답의 모양을 읽어 `정렬`, `이분 탐색`, `BFS/DFS`, `구현/그리디` 중 어디로 갈지를 고르는 감각이 핵심이다.

**난이도: 🟢 Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "입력 크기와 답의 모양을 보지 않고 유명한 기법 이름부터 붙이고 있어요" | 알고리즘 문제나 미션 요구사항 첫 triage | Big-O로 불가능한 풀이를 먼저 지우고 답의 형태를 본다 |
| "정렬, 이분 탐색, BFS/DFS, priority queue 신호가 섞여요" | backend junior 알고리즘 패턴 선택 | 순서/경계/연결/최소값/반복 질의 신호를 분리한다 |
| "자료구조 선택과 알고리즘 패턴 선택을 실제 문제에 같이 적용하지 못해요" | queue/map/graph가 미션 코드와 문제 풀이에 같이 등장 | 구조 선택과 계산 패턴 선택을 한 장면에서 번역한다 |

관련 문서:

- [Backend Data-Structure Starter Pack](./backend-data-structure-starter-pack.md)
- [algorithm 카테고리 인덱스](../algorithm/README.md)
- [Backend Algorithm Starter Pack](../algorithm/backend-algorithm-starter-pack.md)
- [시간복잡도 입문](../algorithm/time-complexity-intro.md)
- [이분 탐색 입문](../algorithm/binary-search-intro.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- [정렬 알고리즘 입문](../algorithm/sort-intro.md)
- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [Graph Basics](./graph-basics.md)
- [data-structure 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: backend complexity algorithm foundations, backend junior algorithm foundation, big o starter pack backend, woowacourse backend algorithm basics, binary search bfs dfs beginner backend, 정렬 이분탐색 bfs dfs 뭐부터, 백엔드 알고리즘 패턴 기초, 우테코 백엔드 알고리즘 입문, 자료구조에서 알고리즘으로 넘어가기, complexity and algorithm pattern foundations backend juniors basics, complexity and algorithm pattern foundations backend juniors beginner, complexity and algorithm pattern foundations backend juniors intro, data structure basics, beginner data structure, 처음 배우는데 complexity and algorithm pattern foundations backend juniors

## 먼저 잡을 mental model

백엔드 초보자가 알고리즘 문제를 볼 때 제일 많이 흔들리는 지점은 "이거 정렬인가, BFS인가, 그냥 구현인가"를 처음 30초 안에 못 가르는 순간이다.

이때는 기법 이름을 더 외우기보다 아래 순서로 잘라 보면 된다.

1. 입력 크기가 어느 정도인가
2. 답이 `하나의 값`, `경계`, `최단 이동`, `정렬 후 순회` 중 무엇인가
3. 상태를 그대로 시뮬레이션해야 하는가

짧게 외우면 이렇다.

- 입력 크기로 안 되는 풀이를 먼저 자른다
- 정렬이 비교 대상을 붙여 주는지 본다
- 경계 하나를 찾는 문제면 이분 탐색을 의심한다
- 그래프/격자/최소 이동이면 BFS/DFS를 먼저 본다

## 한눈에 보는 분기표

| 문제 신호 | 먼저 떠올릴 것 | 왜 이쪽이 먼저인가 |
|---|---|---|
| `n`이 크고 단순 이중 루프가 불안하다 | Big-O 점검 | 애초에 안 되는 풀이를 빨리 버려야 한다 |
| 순서, 겹침, 랭킹, 인접 비교가 중요하다 | 정렬 후 스캔 | 비교 대상을 붙여 두면 규칙이 단순해진다 |
| `최소 x`, `최대 x`, `처음 만족`이 보인다 | 이분 탐색 | 답이 바뀌는 경계를 찾는 문제일 수 있다 |
| 연결 여부, 최소 이동 횟수, 격자 탐색 | BFS/DFS | 상태 전이 그래프로 읽는 편이 자연스럽다 |
| 규칙이 많고 상태가 계속 바뀐다 | 구현 / 시뮬레이션 | 자료구조와 예외 순서가 핵심이다 |

## Woowacourse 백엔드 기준으로 자주 나오는 첫 묶음

| 장면 | 먼저 보는 것 | 바로 이어 볼 문서 |
|---|---|---|
| 입력 크기와 시간 제한이 먼저 불안하다 | Big-O 감각 | [시간복잡도 입문](../algorithm/time-complexity-intro.md) |
| 정렬 후 한 번 훑으면 될 것 같다 | 정렬 + scan | [Backend Algorithm Starter Pack](../algorithm/backend-algorithm-starter-pack.md), [정렬 알고리즘 입문](../algorithm/sort-intro.md) |
| "처음 만족하는 위치", "최소 허용값"처럼 들린다 | 이분 탐색 | [이분 탐색 입문](../algorithm/binary-search-intro.md) |
| 미로, 연결 요소, 최소 이동 횟수처럼 들린다 | BFS/DFS | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md), [그래프 기초](./graph-basics.md) |
| 우선순위가 높은 작업, top-k, 가장 이른 마감 | heap / priority queue | [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md), [Backend Data-Structure Starter Pack](./backend-data-structure-starter-pack.md) |

핵심은 자료구조와 알고리즘을 따로 보지 않는 것이다.

- `priority queue`를 떠올리면 동시에 `top-k`, `earliest-first`, `정렬 매번 하지 않기`가 같이 떠올라야 하고
- `queue`를 떠올리면 `BFS`, `FIFO handoff`, `레벨 순 탐색`이 같이 떠올라야 한다

## 자주 하는 오해

- "`O(log n)`이 보이면 무조건 빠르다"라고 생각한다.
  실제로는 정렬 + 이분 탐색이면 전체는 `O(n log n)`이다.
- BFS와 DFS를 둘 다 "탐색"으로만 외워 최단 이동과 연결성 질문을 섞는다.
- 구현 문제를 억지로 그리디나 DP로 보려고 한다.
- 자료구조 선택과 알고리즘 선택을 완전히 다른 챕터로 본다.

## 안전한 다음 단계

- 알고리즘 전체 입구가 필요하면: [Backend Algorithm Starter Pack](../algorithm/backend-algorithm-starter-pack.md)
- 자료구조 쪽 선택 기준이 먼저면: [Backend Data-Structure Starter Pack](./backend-data-structure-starter-pack.md)
- BFS/DFS로 바로 내려가야 하면: [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- 이분 탐색 경계 감각이 약하면: [이분 탐색 입문](../algorithm/binary-search-intro.md)

## 한 줄 정리

백엔드 주니어의 알고리즘 첫 판단은 "어떤 유명 기법인가"보다 `입력 크기 -> 정렬 필요 여부 -> 경계 탐색 여부 -> BFS/DFS 여부 -> 구현/그리디 여부` 순으로 좁혀 가는 데서 시작한다.
