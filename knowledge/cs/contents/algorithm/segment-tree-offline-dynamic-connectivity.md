---
schema_version: 3
title: Segment Tree over Time for Offline Dynamic Connectivity
concept_id: algorithm/segment-tree-offline-dynamic-connectivity
canonical: true
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 76
mission_ids: []
review_feedback_tags:
- offline-dynamic-connectivity
- segment-tree-over-time
- dsu-rollback
- graph-updates
aliases:
- segment tree over time
- offline dynamic connectivity
- dynamic connectivity with rollback DSU
- 시간 세그먼트 트리
- 오프라인 동적 연결성
- rollback DSU segment tree
symptoms:
- 간선 추가와 삭제가 섞인 그래프 연결성 질의를 온라인 DSU로 처리하려고 한다
- rollback DSU가 왜 segment tree over time과 같이 쓰이는지 모르겠다
- 각 간선이 살아 있는 시간 구간을 어디에 저장해야 하는지 헷갈린다
intents:
- design
- deep_dive
- comparison
prerequisites:
- algorithm/dsu-rollback
- algorithm/union-find-amortized-proof-intuition
next_docs:
- algorithm/offline-query-ordering-patterns
- algorithm/mo-algorithm-basics
- algorithm/topological-dp
linked_paths:
- contents/algorithm/dsu-rollback.md
- contents/algorithm/union-find-amortized-proof-intuition.md
- contents/algorithm/offline-query-ordering-patterns.md
- contents/algorithm/mo-algorithm-basics.md
- contents/algorithm/graph.md
- contents/algorithm/time-complexity-intro.md
confusable_with:
- algorithm/dsu-rollback
- algorithm/offline-query-ordering-patterns
- algorithm/mo-algorithm-basics
forbidden_neighbors: []
expected_queries:
- offline dynamic connectivity에서 segment tree over time을 왜 써?
- edge add remove query를 rollback DSU로 처리하는 흐름을 설명해줘
- 간선이 살아 있는 시간 구간을 세그먼트 트리에 넣는다는 뜻이 뭐야?
- online DSU로는 삭제가 어려운데 offline으로 어떻게 바꿔?
contextual_chunk_prefix: |
  이 문서는 offline dynamic connectivity를 segment tree over time과 rollback
  DSU로 푸는 advanced deep_dive다. edge add/remove, connectivity query,
  alive interval, rollback union find, segment tree over time 같은 표현을
  시간 구간에 간선을 배치하고 DFS 중 union/rollback하는 흐름으로 매핑한다.
---
# Segment Tree over Time for Offline Dynamic Connectivity

> 한 줄 요약: 간선 삭제가 있는 연결성 질의는 "각 간선이 살아 있는 시간 구간"을 세그먼트 트리에 올리고, DFS로 시간 구간을 내려가며 rollback DSU를 적용하면 오프라인으로 처리할 수 있다.

**난이도: Advanced**

## 왜 그냥 DSU로 어렵나

DSU는 union은 빠르지만 delete가 어렵다.
간선을 지웠을 때 두 component가 다시 나뉘는지 알려면 내부 구조를 되돌려야 하기 때문이다.

offline dynamic connectivity는 질의를 모두 알고 있다는 조건을 쓴다.
각 간선이 언제 추가되고 언제 삭제되는지 모아 "살아 있는 시간 구간"으로 바꾼다.

## 핵심 흐름

1. query index를 시간축으로 둔다.
2. 각 edge의 alive interval `[l, r]`을 계산한다.
3. 그 interval을 덮는 segment tree node들에 edge를 저장한다.
4. tree DFS 중 node에 들어갈 때 edge들을 union한다.
5. leaf에서 connectivity query에 답한다.
6. node를 나올 때 union 기록을 rollback한다.

## 왜 rollback DSU가 맞물리나

segment tree DFS는 한 node 구간에만 필요한 edge를 잠시 적용한다.
자식 탐색이 끝나면 부모 상태로 돌아가야 하므로 path compression 대신 size/rank와 stack 기록을 쓰는 rollback DSU가 필요하다.

| 도구 | 역할 |
|---|---|
| segment tree over time | edge가 유효한 시간 구간을 나눠 담는다 |
| rollback DSU | DFS 진입/탈출마다 connectivity 상태를 되돌린다 |
| offline preprocessing | add/remove를 interval로 바꾼다 |

## 흔한 실수

- path compression을 켜서 rollback할 변경량이 복잡해진다.
- 삭제되지 않은 edge의 끝 시간을 마지막 query까지 열어 두지 않는다.
- 같은 edge가 여러 번 add/remove될 때 interval을 하나로 합쳐 버린다.
- leaf query 전에 node edge를 union하지 않는다.
