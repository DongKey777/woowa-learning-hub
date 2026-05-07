---
schema_version: 3
title: 알고리즘 문제 신호에서 첫 패턴 고르기
concept_id: algorithm/problem-signal-to-pattern-router-beginner
canonical: true
category: algorithm
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 91
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- algorithm-pattern-first-router
- problem-signal-to-technique
- beginner-before-implementation
aliases:
- algorithm pattern router beginner
- 알고리즘 문제 패턴 라우터
- 문제 보고 무슨 알고리즘인지 고르기
- 알고리즘 처음 패턴 고르기
- 정렬 이분탐색 투포인터 BFS DP 그리디 구분
- 코딩테스트 문제 분류
- 문제 신호에서 패턴 고르기
- 알고리즘 뭐부터 떠올려야 해요
- beginner algorithm chooser
- pattern first before code
symptoms:
- 문제를 보자마자 코드부터 쓰기 시작해서 정렬, 탐색, DP, 그리디 중 어떤 패턴인지 나중에야 흔들려
- 최소, 최댓값, 가능한가, 연결돼 있나 같은 단어만 보고 BFS나 DP를 과하게 붙여 오진해
- 정렬 후 이분 탐색, 정렬 후 투 포인터, 그리디 정렬 기준처럼 정렬이 목적이 아니라 전처리일 수 있다는 점을 놓쳐
intents:
- troubleshooting
- comparison
prerequisites:
- algorithm/time-complexity-intro
next_docs:
- algorithm/sort-intro
- algorithm/binary-search-intro
- algorithm/two-pointer-intro
- algorithm/dfs-bfs-intro
- algorithm/greedy-intro
- algorithm/dp-intro
linked_paths:
- contents/algorithm/time-complexity-intro.md
- contents/algorithm/sort-intro.md
- contents/algorithm/sort-to-binary-search-bridge.md
- contents/algorithm/binary-search-intro.md
- contents/algorithm/two-pointer-intro.md
- contents/algorithm/sliding-window-patterns.md
- contents/algorithm/dfs-bfs-intro.md
- contents/algorithm/bfs-vs-dijkstra-shortest-path-mini-card.md
- contents/algorithm/greedy-intro.md
- contents/algorithm/greedy-vs-dp-decision-card.md
- contents/algorithm/dp-intro.md
- contents/algorithm/brute-force-intro.md
- contents/algorithm/backtracking-intro.md
- contents/data-structure/hash-table-basics.md
- contents/data-structure/queue-basics.md
confusable_with:
- algorithm/backend-algorithm-starter-pack
- algorithm/greedy-vs-dp-decision-card
- algorithm/sort-to-binary-search-bridge
- algorithm/bfs-vs-dijkstra-shortest-path-mini-card
- data-structure/backend-data-structure-starter-pack
forbidden_neighbors: []
expected_queries:
- 알고리즘 문제를 처음 봤을 때 정렬, 이분 탐색, 투 포인터, BFS, DP, 그리디 중 무엇을 먼저 떠올려야 해?
- 최소라는 단어가 보이면 항상 BFS나 DP로 가면 안 되는 이유를 문제 신호 기준으로 설명해줘
- 정렬이 최종 목적이 아니라 이분 탐색이나 투 포인터 전처리일 수 있다는 뜻을 알려줘
- 그리디와 DP를 문제 문장만 보고 처음 어떻게 의심해야 해?
- 연결돼 있나, 최소 몇 번, 비용 합 최소를 그래프 문제에서 어떻게 나눠야 해?
contextual_chunk_prefix: |
  이 문서는 초급 학습자가 알고리즘 문제 문장을 보고 구현 전에 첫 패턴을 고르는 chooser다.
  정렬, 이분 탐색, 투 포인터, 슬라이딩 윈도우, DFS/BFS, 다익스트라, 그리디, DP, 완전탐색, 백트래킹, 해시 조회를 문제 신호와 답의 모양으로 분기한다.
---
# 알고리즘 문제 신호에서 첫 패턴 고르기

> 한 줄 요약: 알고리즘 문제는 코드보다 먼저 `답의 모양`, `입력의 성질`, `선택을 되돌릴 수 있는지`를 보고 첫 패턴을 고르는 편이 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [시간복잡도 입문](./time-complexity-intro.md)
- [정렬 알고리즘 입문](./sort-intro.md)
- [정렬에서 이분 탐색으로 넘어가는 브리지](./sort-to-binary-search-bridge.md)
- [이분 탐색 입문](./binary-search-intro.md)
- [두 포인터 입문](./two-pointer-intro.md)
- [DFS와 BFS 입문](./dfs-bfs-intro.md)
- [BFS vs Dijkstra shortest path beginner split card](./bfs-vs-dijkstra-shortest-path-mini-card.md)
- [그리디 알고리즘 입문](./greedy-intro.md)
- [그리디 vs DP 결정 카드](./greedy-vs-dp-decision-card.md)
- [동적 계획법 입문](./dp-intro.md)

retrieval-anchor-keywords: 알고리즘 문제 패턴 라우터, 문제 보고 알고리즘 고르기, 정렬 이분탐색 투포인터 BFS DP 그리디 구분, 코딩테스트 문제 분류, pattern first before code, algorithm chooser beginner

## 먼저 3개만 묻기

처음에는 알고리즘 이름보다 아래 세 질문을 먼저 던진다.

| 먼저 물을 질문 | 왜 중요한가 |
|---|---|
| 답이 `존재 여부`, `개수`, `최소/최대`, `순서` 중 무엇인가 | 같은 입력이어도 답의 모양에 따라 도구가 달라진다 |
| 입력이 이미 정렬됐거나, 정렬해도 의미가 유지되는가 | 이분 탐색, 투 포인터, 그리디의 출발점이 자주 된다 |
| 지금 선택을 나중에 되돌리거나 비교해야 하는가 | 그리디, DP, 백트래킹을 가르는 핵심 신호다 |

이 세 질문이 끝나기 전에는 `BFS`, `DP`, `그리디` 같은 이름을 바로 붙이지 않는 편이 좋다.

## 30초 첫 패턴 표

| 문제에서 먼저 보이는 신호 | 먼저 의심할 패턴 | 바로 확인할 조건 | 다음 문서 |
|---|---|---|---|
| 순서대로 나열, 정렬 기준, stable, 중복 묶기 | 정렬 | 정렬 자체가 답인지, 다른 알고리즘 전처리인지 | [정렬 알고리즘 입문](./sort-intro.md) |
| 정렬된 배열, `처음 만족하는 위치`, `가능한 최소 X` | 이분 탐색 | 버릴 절반이 단조적으로 결정되는지 | [이분 탐색 입문](./binary-search-intro.md) |
| 정렬된 배열에서 두 수 합, 양끝에서 좁히기 | 투 포인터 | 포인터 이동 방향이 보장되는지 | [두 포인터 입문](./two-pointer-intro.md) |
| 연속 부분 배열, 부분 문자열, 길이 k, 중복 없는 구간 | 슬라이딩 윈도우 | 상태가 연속 구간에서만 유지되는지 | [Sliding Window 패턴](./sliding-window-patterns.md) |
| 갈 수 있나, 같은 그룹인가, 연결돼 있나 | DFS/BFS 또는 DSU | yes/no 연결성인지, 실제 경로/거리인지 | [DFS와 BFS 입문](./dfs-bfs-intro.md) |
| 최소 몇 번 만에 도착, 모든 이동 비용이 같음 | BFS | 간선 비용이 모두 1인지 | [DFS와 BFS 입문](./dfs-bfs-intro.md) |
| 비용 합 최소, 가중치가 다름 | Dijkstra 계열 | 음수 비용이 없는지 | [BFS vs Dijkstra shortest path beginner split card](./bfs-vs-dijkstra-shortest-path-mini-card.md) |
| 지금 가장 좋은 선택을 반복, 정렬 기준이 핵심 | 그리디 | 반례가 없는지, 탐욕 선택을 증명할 수 있는지 | [그리디 알고리즘 입문](./greedy-intro.md) |
| 같은 부분 문제를 여러 번 계산, `dp[i]` 상태가 보임 | DP | 중복 부분 문제와 점화식이 있는지 | [동적 계획법 입문](./dp-intro.md) |
| 입력 크기가 작고 모든 경우를 세도 됨 | 완전 탐색 | 시간복잡도가 제한 안에 들어오는지 | [완전 탐색 입문](./brute-force-intro.md) |
| 선택하고 되돌리며 조건을 만족하는 조합을 찾음 | 백트래킹 | 가지치기 조건이 있는지 | [백트래킹 입문](./backtracking-intro.md) |
| 빠른 존재 확인, 중복 제거, key로 바로 찾기 | Hash / Map / Set | 순서보다 조회가 핵심인지 | [해시 테이블 기초](../data-structure/hash-table-basics.md) |

## 단어 하나만 보고 고르면 자주 틀린다

`최소`라는 말이 보인다고 항상 BFS나 DP는 아니다.

| 문장 | 더 안전한 첫 분기 |
|---|---|
| 최소 이동 횟수, 모든 이동 비용 1 | BFS |
| 최소 비용, 간선마다 비용이 다름 | Dijkstra 또는 최단 경로 문서 |
| 가능한 최소 용량 X | 답의 범위에 이분 탐색 |
| 동전 개수 최소, 단위가 임의 | DP 의심 |
| 회의 수 최대, 종료 시간 기준 정렬 | 그리디 의심 |

`정렬`도 마찬가지다. 정렬은 최종 목적이 아니라 전처리일 때가 많다.

| 정렬 뒤에 하는 일 | 더 가까운 패턴 |
|---|---|
| 특정 값이나 첫 위치를 찾는다 | 이분 탐색 |
| 두 원소의 합을 맞춘다 | 투 포인터 |
| 끝나는 시간이 빠른 것부터 고른다 | 그리디 |
| 같은 값끼리 묶어 센다 | 정렬 + 카운팅 또는 해시 |

## 그래프 문장 3갈래

그래프 문제는 `graph`, `BFS`, `queue`가 한꺼번에 보여서 초급자가 자주 섞는다.

| 질문 | 먼저 붙일 이름 | 흔한 도구 |
|---|---|---|
| 점과 선으로 표현할 수 있나 | 그래프 구조화 | adjacency list |
| 갈 수 있나, 연결돼 있나 | 연결성 | DFS/BFS, DSU |
| 최소 몇 번 만에 가나 | unweighted shortest path | BFS + queue |
| 비용 합이 최소인가 | weighted shortest path | Dijkstra 등 |

`queue`는 BFS 자체가 아니라, BFS가 가까운 노드부터 처리하기 위해 쓰는 FIFO 도구다.

## 그리디와 DP를 처음 가르는 기준

그리디와 DP는 둘 다 최적값 문제에서 자주 나오지만, 질문이 다르다.

| 질문 | 그리디 쪽 신호 | DP 쪽 신호 |
|---|---|---|
| 선택을 되돌리나 | 되돌리지 않는다 | 여러 선택 결과를 저장해 비교한다 |
| 증명 방식 | 지금 선택이 안전하다는 교환 논증 | 점화식과 base case |
| 반례가 있나 | 작은 반례가 나오면 실패 | 반례 대신 상태 정의가 핵심 |
| 대표 문장 | 종료 시간이 빠른 회의부터 선택 | i번째까지의 최적값 |

감으로 그리디를 고른 뒤 작은 반례를 못 막으면 [그리디 vs DP 결정 카드](./greedy-vs-dp-decision-card.md)로 바로 내려가면 된다.

## 한 줄 정리

문제를 보자마자 알고리즘 이름을 붙이기보다, `답의 모양`, `입력 성질`, `선택을 되돌릴 필요`를 먼저 보면 정렬, 이분 탐색, 투 포인터, BFS, 그리디, DP 중 첫 패턴을 훨씬 덜 흔들리게 고를 수 있다.
