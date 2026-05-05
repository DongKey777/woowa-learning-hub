---
schema_version: 3
title: Union-Find Standalone Beginner Primer
concept_id: data-structure/union-find-standalone-beginner-primer
canonical: true
category: data-structure
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- union-find-vs-bfs-routing
- same-component-question
- parent-array-misread
aliases:
- union find beginner
- union find primer
- dsu intro
- disjoint set intro
- what is union find
- union find 뭐예요
- 같은 그룹인가 자료구조
- connected yes no basics
- union find vs bfs intro
- union find 처음 배우기
- group merge basics
- kruskal union find beginner
- 연결돼 있나 union find
- 갈 수 있나 bfs 차이
- why not bfs
symptoms:
- 같은 그룹인지 확인하면 된다는데 왜 BFS랑 자꾸 헷갈리는지 모르겠어
- union-find의 parent 배열이 실제 이동 경로처럼 보여서 감이 안 와
- 연결 여부만 묻는 문제를 그래프 탐색으로 풀어야 할지 대표 비교로 풀어야 할지 헷갈려
intents:
- definition
prerequisites:
- data-structure/basic
- data-structure/graph-basics
next_docs:
- data-structure/connectivity-question-router
- data-structure/union-find-component-metadata-walkthrough
- data-structure/union-find-deep-dive
- algorithm/kruskal-union-find-beginner-bridge
linked_paths:
- contents/data-structure/connectivity-question-router.md
- contents/data-structure/union-find-component-metadata-walkthrough.md
- contents/data-structure/union-find-deep-dive.md
- contents/algorithm/dfs-bfs-intro.md
- contents/algorithm/kruskal-union-find-beginner-bridge.md
- contents/algorithm/minimum-spanning-tree-prim-vs-kruskal.md
confusable_with:
- data-structure/connectivity-question-router
- algorithm/dfs-bfs-intro
- algorithm/kruskal-union-find-beginner-bridge
forbidden_neighbors:
- contents/algorithm/dfs-bfs-intro.md
expected_queries:
- union find가 뭐예요? 처음 배우는 사람 기준으로 설명해줘
- 같은 그룹인지 빠르게 확인하는 자료구조가 왜 bfs랑 다른가요?
- 연결 여부만 여러 번 물을 때 union find를 왜 쓰는지 알고 싶어
- union find는 경로를 찾는 게 아니라 대표만 비교한다는 말이 무슨 뜻이야?
- kruskal 전에 union find 큰 그림을 먼저 잡고 싶어
contextual_chunk_prefix: |
  이 문서는 연결 질문을 처음 만난 학습자가 union-find를 그래프 전체 탐색이
  아니라 같은 그룹인지 빠르게 확인하는 도구로 기초를 잡는 primer다. 같은
  편인지 반복 확인, 대표만 비교해 답하기, 경로 말고 묶음 판별, 그룹 합치기,
  BFS보다 뭐가 다른지 같은 자연어 paraphrase가 본 문서의 핵심 개념에
  매핑된다.
---
# Union-Find Standalone Beginner Primer

> 한 줄 요약: union-find는 `둘이 같은 그룹인가?`를 반복해서 물을 때, 매번 그래프 전체를 다시 훑지 않고 대표만 비교해서 빠르게 답하는 자료구조다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 정리](./README.md)
- [Connectivity Question Router](./connectivity-question-router.md)
- [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md)
- [Union-Find Deep Dive](./union-find-deep-dive.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- [Kruskal에서 Union-Find가 끼는 순간](../algorithm/kruskal-union-find-beginner-bridge.md)
- [Minimum Spanning Tree: Prim vs Kruskal](../algorithm/minimum-spanning-tree-prim-vs-kruskal.md)

retrieval-anchor-keywords: union find beginner, union find primer, dsu intro, disjoint set intro, what is union find, union find 뭐예요, 같은 그룹인가 자료구조, connected yes no basics, union find vs bfs intro, union find 처음 배우기, group merge basics, kruskal union find beginner, 연결돼 있나 union find, 갈 수 있나 bfs 차이, why not bfs

## 핵심 개념

union-find를 처음 볼 때는 `트리`, `랭크`, `상각` 같은 용어보다 먼저 역할부터 잡는 편이 쉽다.

- `find(x)`: `x`가 속한 그룹의 대표를 찾는다
- `union(a, b)`: `a`가 속한 그룹과 `b`가 속한 그룹을 합친다

짧게 말하면 union-find는 "`지금 이 둘이 같은 편이야?`"를 자주 물을 때 쓰는 **그룹 관리 도구**다.
그래프 전체 경로를 저장하는 구조가 아니라, "누가 같은 묶음인가"만 빠르게 확인하는 데 집중한다.

## 한눈에 보기

먼저 질문 문장을 이렇게 자르면 된다.

| 문제 문장 | 먼저 떠올릴 것 | 이유 |
|---|---|---|
| `1번과 9번이 같은 그룹인가?` | union-find | 답이 yes/no라서 대표 비교면 충분하다 |
| `지금 몇 개 그룹으로 나뉘어 있지?` | union-find + 메타데이터 | 그룹 수까지 세야 하므로 다음 단계로 확장하면 된다 |
| `1번에서 9번까지 실제 경로를 보여줘` | BFS/DFS | 중간 정점을 따라가야 한다 |
| `1번에서 9번까지 가장 짧게 가는 길은?` | shortest path 계열 | yes/no를 넘어 최단 경로 문제다 |

한 문장으로 외우면 이렇다.

- `같은 그룹인가?`면 union-find
- `어떻게 가는가?`면 BFS/DFS
- `가장 짧게 가는가?`면 shortest path

## beginner 다음 한 칸

이 문서는 `같은 그룹인가?`에만 답하는 primer다. 처음에는 여기서 멈추고, 질문이 커질 때만 한 칸씩 넘어가면 된다.

| 지금 질문이 커진 방식 | 다음 문서 | 왜 바로 그 문서로 가나 |
|---|---|---|
| `그룹 크기`, `전체 그룹 수`도 같이 알고 싶다 | [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md) | yes/no 질문은 유지한 채 메타데이터만 추가된다 |
| `연결되면 실제 경로 하나도 보여줘` | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | 이제는 그룹 대표 비교가 아니라 간선을 따라간 경로 정보가 필요하다 |
| `최소 몇 번`, `최소 비용`까지 구하고 싶다 | [Connectivity Question Router](./connectivity-question-router.md) | 무가중치 BFS와 가중치 shortest-path를 먼저 다시 분기해야 안전하다 |
| path compression, union by rank가 왜 빠른지 궁금하다 | [Union-Find Deep Dive](./union-find-deep-dive.md) | 여기서부터가 구현 최적화 deep dive다 |

- `처음 union-find`, `why not bfs`, `갈 수 있나 bfs 차이`, `헷갈려요` 같은 query는 이 primer -> router 순서가 가장 안전하다.
- `실제 경로`, `최단 경로`, `최소 비용` 문장이 보이면 union-find 문서에 오래 머무르지 않는 편이 좋다.

특히 `연결돼 있나?`와 `갈 수 있나?`를 보면 초보자는 BFS를 먼저 떠올리기 쉽다.
하지만 질문이 yes/no에서 끝나면, 이 문서의 출발점은 `탐색`보다 `그룹 대표 비교`다.

## Union-Find vs BFS 한 번에 분리

둘 다 그래프 위에서 `연결`을 다루지만, 답의 모양이 다르다.

| 질문 | union-find | BFS |
|---|---|---|
| `A와 B가 같은 묶음이야?` | 적합 | 가능은 하지만 과하다 |
| `A에서 B까지 실제 경로 하나를 보여줘` | 부족 | 적합 |
| `A에서 B까지 최소 몇 번 만에 가?` | 불가 | 무가중치면 적합 |
| `연결 여부를 여러 번 반복해서 물어봐` | 강함 | 매번 다시 탐색 |

짧게 자르면 아래처럼 기억하면 된다.

- union-find는 `연결 여부를 빨리 확인하는 메모장`
- BFS는 `직접 따라가며 경로와 거리를 보는 탐색`

## 대표자 메모장으로 생각하기

초보자에게는 union-find를 "그룹 대표자 메모장"으로 비유하면 덜 헷갈린다.

- 처음에는 모든 원소가 자기 자신을 대표한다
- 둘을 합치면 한쪽 대표를 다른 대표 밑으로 붙인다
- 나중에 `같은 그룹인가?`를 물으면 각자 대표를 찾아 비교한다

예를 들어 `1, 2, 3, 4`가 모두 따로 시작한다고 하자.

1. `union(1, 2)`를 하면 `1`과 `2`는 같은 그룹이 된다
2. `union(2, 3)`을 하면 `1, 2, 3`이 한 그룹이 된다
3. 이때 `find(1)`과 `find(3)` 결과가 같으면 `same(1, 3) = true`다

여기서 중요한 점은 union-find가 `1 -> 2 -> 3` 같은 **이동 경로**를 알려 주는 것이 아니라, `1`과 `3`이 **같은 묶음인지**만 알려 준다는 것이다.

## 손으로 보는 가장 작은 예시

아래처럼 친구 관계가 추가된다고 생각해 보자.

| 단계 | 연산 | 그룹 상태 | `same(1, 3)` | `same(1, 4)` |
|---|---|---|---|---|
| 시작 | - | `{1}` `{2}` `{3}` `{4}` | false | false |
| 1 | `union(1, 2)` | `{1,2}` `{3}` `{4}` | false | false |
| 2 | `union(2, 3)` | `{1,2,3}` `{4}` | true | false |
| 3 | `union(3, 4)` | `{1,2,3,4}` | true | true |

이 표에서 union-find가 잘하는 일은 분명하다.

- `1`과 `3`이 같은 친구 묶음인지 빠르게 확인
- 그룹을 합칠 때마다 다시 전체 그래프를 순회하지 않기

즉 **간선이 추가되기만 하고**, 질문도 **같은 그룹인지 반복해서 확인**하는 상황에 잘 맞는다.

## 흔한 오해와 함정

- `연결되어 있나?`와 `어떻게 연결되어 있나?`는 다른 질문이다. 앞은 union-find, 뒤는 BFS/DFS다.
- union-find의 `parent` 배열을 경로 정보로 오해하면 안 된다. 그 값은 탐색용 지도라기보다 대표를 찾기 위한 내부 연결이다.
- `union`을 한 번 불렀다고 항상 새로운 그룹 병합이 일어나는 것은 아니다. 이미 같은 그룹이면 상태가 안 바뀔 수도 있다.
- `가장 짧은 경로`를 물을 때 union-find로 가면 오답이다. union-find는 거리와 비용을 계산하지 않는다.

초보자가 많이 하는 질문을 한 줄로 번역하면 이렇다.

| 헷갈리는 질문 | 바로 고칠 해석 |
|---|---|
| `둘이 이어져 있으면 경로도 바로 나오나요?` | 아니다. union-find는 yes/no가 중심이다 |
| `find 결과가 같으면 몇 칸 만에 가는지도 알 수 있나요?` | 아니다. 거리 정보는 없다 |
| `이미 같은 그룹인데 또 union 하면요?` | 보통 변화 없이 끝난다 |

## 실무에서 쓰는 모습

백엔드나 코딩 테스트에서 union-find가 자주 보이는 장면은 비슷하다.

1. 친구/조직/네트워크처럼 그룹이 계속 합쳐진다
2. 매번 전체를 다시 탐색하기보다 `같은 묶음인지`를 빨리 확인하고 싶다
3. 대표 비교만으로 답할 수 있는 질문이 반복된다

대표적인 예시는 두 가지다.

- `친구 관계 추가 후 A와 B가 같은 네트워크인지 확인`
- `Kruskal`에서 간선을 하나 넣었을 때 사이클이 생기는지 확인

반대로 아래 질문은 union-find만으로는 부족하다.

- `A에서 B까지 실제 이동 경로를 출력`
- `A에서 B까지 최소 비용 경로를 계산`
- `간선을 삭제한 뒤에도 아직 연결인지 즉시 반영`

## 더 깊이 가려면

- yes/no와 경로 복원, 최단 경로를 먼저 분리하고 싶으면 [Connectivity Question Router](./connectivity-question-router.md)
- `그룹 크기`, `전체 그룹 수`까지 같이 추적하려면 [Union-Find Component Metadata Walkthrough](./union-find-component-metadata-walkthrough.md)
- path compression, union by size/rank까지 포함한 구조 설명은 [Union-Find Deep Dive](./union-find-deep-dive.md)
- `간선을 지웠는데 아직 연결인가?`처럼 삭제가 끼는 순간 왜 plain union-find가 멈추는지 먼저 보려면 [Deletion-Aware Connectivity Bridge](./deletion-aware-connectivity-bridge.md)
- Kruskal 문맥에서 union-find가 어디에 끼는지 초급자용 연결만 먼저 보려면 [Kruskal에서 Union-Find가 끼는 순간](../algorithm/kruskal-union-find-beginner-bridge.md)
- Prim과 Kruskal 전체 비교까지 바로 가려면 [Minimum Spanning Tree: Prim vs Kruskal](../algorithm/minimum-spanning-tree-prim-vs-kruskal.md)

## 면접/시니어 질문 미리보기

| 질문 | 의도 | 짧은 답 방향 |
|---|---|---|
| `왜 BFS 대신 union-find를 쓰나요?` | 문제 분기 이해 확인 | 실제 경로가 아니라 same-component yes/no를 반복해서 묻기 때문이다 |
| `union-find가 실제 경로를 못 주는 이유는?` | 저장 정보의 한계 이해 확인 | 그룹 대표만 관리하고 그래프 경로 자체는 보존하지 않기 때문이다 |
| `그룹 크기까지 물으면 무엇을 더 저장하나요?` | 다음 단계 연결 | 루트 기준 `size` 같은 메타데이터를 추가한다 |

## 한 줄 정리

union-find는 `같은 그룹인가?`를 빠르게 반복해서 답하는 첫 관문 자료구조이고, 경로/최단거리 문제와는 초반에 분리해서 읽는 것이 핵심이다.
