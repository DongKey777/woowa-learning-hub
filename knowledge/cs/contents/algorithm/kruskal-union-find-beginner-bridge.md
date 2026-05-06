---
schema_version: 3
title: Kruskal에서 Union-Find가 끼는 순간
concept_id: algorithm/kruskal-union-find-beginner-bridge
canonical: false
category: algorithm
difficulty: beginner
doc_role: bridge
level: beginner
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- mst-cycle-check
- union-find-role-separation
aliases:
- kruskal union find beginner
- kruskal dsu intro
- mst cycle check basics
- why union find in kruskal
- kruskal 처음 배우기
- union find가 왜 필요한가
- mst 뭐예요 kruskal
- edge list mst intro
- same group cycle check
- beginner graph mst
symptoms:
- 크루스칼에서 왜 union-find가 필요한지 역할이 분리돼서 안 보여
- MST 문제인데 탐색 말고 분리 집합이 왜 나오는지 감이 안 와
- 간선 정렬과 사이클 판별 중 무엇이 크루스칼이고 무엇이 union-find인지 헷갈려
intents:
- comparison
prerequisites:
- algorithm/minimum-spanning-tree-prim-vs-kruskal
- data-structure/union-find-standalone-beginner-primer
next_docs:
- data-structure/union-find-deep-dive
- algorithm/graph
linked_paths:
- contents/algorithm/minimum-spanning-tree-prim-vs-kruskal.md
- contents/algorithm/graph.md
- contents/data-structure/union-find-standalone-beginner-primer.md
- contents/data-structure/union-find-deep-dive.md
confusable_with:
- algorithm/minimum-spanning-tree-prim-vs-kruskal
- data-structure/union-find-standalone-beginner-primer
forbidden_neighbors:
expected_queries:
- 크루스칼에서 union find가 정확히 어느 순간에 쓰이는지 연결해서 설명해줘
- MST에서 사이클 검사를 왜 union-find로 하는지 초보자 기준으로 알고 싶어
- 크루스칼 알고리즘과 union-find 역할 차이를 한 번에 이해하고 싶어
- 간선을 비용순으로 보면서 같은 그룹인지 확인하는 흐름이 왜 필요한 거야
- 최소 스패닝 트리 문제에서 union find가 끼는 이유를 예시로 설명해줘
- Prim이 아니라 Kruskal을 볼 때 union-find가 왜 함께 따라오는지 첫 연결이 필요해
- MST 문제 풀이에서 간선 정렬 단계와 서로소 집합 단계가 어떻게 이어지는지 헷갈려
contextual_chunk_prefix: |
  이 문서는 알고리즘 초급자가 Kruskal과 Union-Find의 역할을 함께 처음 엮어 보는 bridge다. 가장 싼 간선을 순서대로 볼 때 정확히 어느 순간 묶음 검사가 끼는지, 트리를 늘리는 주체와 사이클 여부만 빠르게 확인하는 보조 도구를 어떻게 분리해 읽는지, 간선 고르기와 그룹 합치기 흐름 연결 같은 자연어 paraphrase가 본 문서의 핵심 연결에 매핑된다.
---
# Kruskal에서 Union-Find가 끼는 순간

> 한 줄 요약: Kruskal은 `가장 싼 간선을 하나씩 넣어도 되나?`를 반복해서 묻는 MST 알고리즘이고, union-find는 그때 `지금 넣으면 사이클이 생기나?`를 빠르게 판별하는 보조 도구다.

**난이도: 🟢 Beginner**

관련 문서:

- [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md)
- [그래프](./graph.md)
- [Union-Find Standalone Beginner Primer](../data-structure/union-find-standalone-beginner-primer.md)
- [Union-Find Deep Dive](../data-structure/union-find-deep-dive.md)

retrieval-anchor-keywords: kruskal union find beginner, kruskal dsu intro, mst cycle check basics, why union find in kruskal, kruskal 처음 배우기, union find가 왜 필요한가, mst 뭐예요 kruskal, edge list mst intro, same group cycle check, beginner graph mst

## 핵심 개념

Kruskal을 처음 볼 때는 증명보다 질문 문장을 먼저 잡는 편이 쉽다.

- Kruskal의 목표: `모든 정점을 최소 비용으로 연결`한다
- Kruskal의 진행 방식: `가장 싼 간선부터` 본다
- 매 단계의 확인 질문: `이 간선을 넣어도 사이클이 안 생기나?`

여기서 union-find가 등장한다. union-find는 실제 MST를 계산하는 주인공이라기보다, `두 정점이 이미 같은 묶음인가?`를 빨리 확인해서 사이클 여부를 알려 주는 검사기다.

## 한눈에 보기

`간선을 넣는다`는 장면을 이렇게 보면 된다.

| Kruskal 단계 | 실제로 하는 일 | union-find가 하는 일 |
|---|---|---|
| 1 | 간선을 비용 오름차순으로 정렬 | 아직 안 쓴다 |
| 2 | 가장 싼 간선 하나를 집어 든다 | 양 끝 정점이 같은 그룹인지 확인 |
| 3 | 같은 그룹이 아니면 간선을 채택 | `union(a, b)`로 그룹을 합친다 |
| 4 | 같은 그룹이면 간선을 버린다 | 이미 연결되어 있으니 사이클 경고 역할 |

짧게 외우면 이렇다.

- Kruskal은 `어떤 간선을 고를까`를 결정한다
- union-find는 `그 간선을 넣어도 되나`를 검사한다

## 작은 예시로 연결하기

정점이 `1, 2, 3, 4`이고 간선이 아래처럼 있다고 하자.

| 간선 | 비용 |
|---|---|
| `1-2` | 1 |
| `2-3` | 2 |
| `1-3` | 3 |
| `3-4` | 4 |

Kruskal은 비용 순서대로 본다.

1. `1-2` 채택: 아직 서로 다른 그룹이므로 OK
2. `2-3` 채택: `1,2` 그룹과 `3` 그룹이 다르므로 OK
3. `1-3` 검사: 이미 `1`과 `3`은 같은 그룹이다. 넣으면 사이클이 생기므로 버림
4. `3-4` 채택: `4`가 다른 그룹이므로 OK

여기서 초보자가 봐야 할 핵심은 하나다.  
union-find는 `1-3`이 몇 칸짜리 경로인지 계산하지 않는다. 그냥 `이미 같은 묶음이라 다시 연결하면 원이 생긴다`만 알려 준다.

## 왜 BFS/DFS가 아니라 union-find인가

이 지점에서 많이 헷갈린다. BFS/DFS도 연결 여부를 볼 수 있는데 왜 굳이 union-find를 쓰는가?

| 질문 | 더 자연스러운 도구 | 이유 |
|---|---|---|
| `지금 이 간선을 넣으면 사이클이 생기나?`를 간선마다 반복 | union-find | same-group yes/no를 여러 번 물어서 대표 비교가 싸다 |
| `1에서 7까지 실제 경로를 보여줘` | BFS/DFS | 중간 정점을 따라가야 한다 |
| `1에서 7까지 가장 짧은 비용은?` | shortest path | 거리와 비용 계산이 목적이다 |

Kruskal에서는 간선을 많게는 `E`개까지 보면서 같은 질문을 반복한다. 그래서 매번 그래프 전체를 다시 훑는 탐색보다, 그룹 대표만 비교하는 union-find가 잘 맞는다.

## 흔한 오해와 함정

- union-find가 MST의 전체 비용을 계산해 주는 것은 아니다. 비용 합산과 간선 선택 순서는 Kruskal이 맡는다.
- `find(a) == find(b)`면 `a`와 `b` 사이의 실제 경로를 복원할 수 있다고 오해하면 안 된다.
- `간선을 정렬하지 않고 union-find만 쓰면 Kruskal`이 되는 것도 아니다. 정렬이 빠지면 `최소 비용` 보장이 사라진다.
- Prim에도 같은 방식으로 union-find가 꼭 필요한 것은 아니다. Prim은 보통 `visited + priority queue` 쪽이 중심이다.

## 실무에서 쓰는 모습

코딩 테스트나 학습 문제에서는 이런 문장일 때 이 브리지가 가장 유용하다.

- `모든 도시를 가장 싼 비용으로 연결하라`
- `간선 목록이 이미 주어지고, 사이클 없이 최소 비용 네트워크를 만들어라`
- `도로 후보를 비용순으로 보면서 선택해도 되는지 판단하라`

이때 읽는 순서는 보통 이렇다.

1. union-find primer로 `same-group yes/no` 감각을 먼저 잡는다
2. 이 문서에서 `그 감각이 Kruskal에서 어디에 끼는지` 연결한다
3. 그다음 Prim과의 비교나 cut property는 MST 비교 문서로 넘어간다

## 더 깊이 가려면

- MST 전체 선택 기준과 Prim 비교까지 보려면 [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md)
- union-find의 `parent`, `path compression`, `union by rank`까지 구조적으로 보려면 [Union-Find Deep Dive](../data-structure/union-find-deep-dive.md)
- 그래프 문제 전체에서 `MST vs shortest path vs connectivity`를 먼저 자르고 싶으면 [그래프](./graph.md)

## 한 줄 정리

Kruskal은 `싼 간선을 고르는 알고리즘`, union-find는 그 간선을 넣을 때 `이미 같은 그룹인가`를 검사해 사이클을 막는 연결 고리다.
