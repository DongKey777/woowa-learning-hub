---
schema_version: 3
title: Bridges and Articulation Points
concept_id: algorithm/bridges-and-articulation-points
canonical: false
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- low-link-modeling
- cut-edge-vs-cut-vertex
- undirected-graph-assumption
aliases:
- bridge
- articulation point
- cut edge
- cut vertex
- low-link
- dfs tree critical node
- graph connectivity cut
- network reliability critical edge
- critical node graph
- 단절선
- 단절점
symptoms:
- DFS low-link 값이 왜 끊기는 간선과 정점을 찾아 주는지 직관이 잘 안 와
- bridge와 articulation point를 SCC나 단순 연결 여부와 자꾸 섞어 생각해
- 무향 그래프 기준인지 방향 그래프에서도 바로 쓸 수 있는지 헷갈려
intents:
- deep_dive
- comparison
prerequisites:
- algorithm/dfs-bfs-intro
- algorithm/graph
next_docs:
- algorithm/scc-tarjan-kosaraju
- algorithm/union-find-amortized-proof-intuition
linked_paths:
- contents/algorithm/graph.md
- contents/algorithm/dfs-bfs-intro.md
- contents/algorithm/scc-tarjan-kosaraju.md
- contents/algorithm/union-find-amortized-proof-intuition.md
- contents/data-structure/graph-basics.md
confusable_with:
- algorithm/scc-tarjan-kosaraju
- algorithm/union-find-amortized-proof-intuition
forbidden_neighbors: []
expected_queries:
- 그래프에서 간선 하나 끊으면 연결이 깨지는지 찾는 알고리즘을 low-link 관점으로 설명해줘
- articulation point와 bridge를 DFS 트리에서 어떻게 판정하는지 정리해줘
- cut edge와 cut vertex를 SCC랑 헷갈리지 않게 비교해서 알려줘
- 무향 그래프 단절점 문제에서 disc와 low가 각각 무슨 뜻인지 이해하고 싶어
- 네트워크 취약 링크를 찾는 문제를 알고리즘으로 번역하면 왜 bridge 탐색이 되는지 궁금해
contextual_chunk_prefix: |
  이 문서는 무향 그래프에서 간선 하나나 정점 하나가 빠졌을 때 연결성이 왜 깨지는지 DFS low-link로 깊이 잡는 deep_dive다. 끊으면 그래프가 갈라지는 링크 찾기, 특정 정점 하나가 빠지면 왜 분리되는지 보기, disc와 low를 우회 경로 신호로 읽기, DFS 트리에서 부모 쪽으로 돌아갈 길이 남는지 판단, SCC와 다른 기준 정리 같은 자연어 paraphrase가 본 문서의 핵심 판정에 매핑된다.
---
# Bridges and Articulation Points

> 한 줄 요약: Bridges와 articulation points는 그래프에서 하나 끊기면 연결성이 깨지는 간선과 정점을 찾는 DFS 기반 구조 분석이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [그래프 관련 알고리즘](./graph.md)
> - [Strongly Connected Components: Tarjan vs Kosaraju](./scc-tarjan-kosaraju.md)
> - [Union-Find Amortized Proof Intuition](./union-find-amortized-proof-intuition.md)

> retrieval-anchor-keywords: bridge, articulation point, cut edge, cut vertex, low-link, dfs tree, graph connectivity, network reliability, critical edge, critical node

## 핵심 개념

그래프에서 특정 간선이나 정점이 제거되면 연결 성분이 늘어나는 경우가 있다.

- bridge: 제거하면 그래프가 더 분리되는 간선
- articulation point: 제거하면 그래프가 더 분리되는 정점

실무적으로는 네트워크 신뢰성, 의존성 취약점, 병목 지점을 찾는 질문과 닿아 있다.

## 깊이 들어가기

### 1. 왜 중요하나

한 개의 연결 고리만 끊겨도 전체 서비스가 분리되는 구조는 위험하다.

- 단일 장애점
- 의존성 병목
- 취약한 네트워크 링크

이런 곳에서 bridge와 articulation point를 찾는 건 매우 유용하다.

### 2. low-link 감각

Tarjan 스타일 DFS에서 `disc`와 `low`를 이용하면 된다.

- `disc[v]`: v 방문 순서
- `low[v]`: v에서 역방향 간선까지 고려했을 때 도달 가능한 가장 이른 방문 번호

이 값이 부모와의 관계를 통해 bridge/articulation 여부를 드러낸다.

### 3. bridge 판정

자식 `to`의 `low[to] > disc[v]`이면, `v-to` 간선은 bridge다.

왜냐하면 자식 서브트리가 부모 쪽으로 우회해서 돌아올 방법이 없기 때문이다.

### 4. articulation 판정

루트와 비루트의 기준이 조금 다르다.

- 루트는 DFS 자식이 두 개 이상이면 articulation일 수 있다.
- 비루트는 어떤 자식의 low가 부모를 못 올라가면 articulation이다.

## 실전 시나리오

### 시나리오 1: 네트워크 취약 링크

한 링크가 끊겼을 때 통신망이 분리된다면, 그 링크는 bridge일 수 있다.

### 시나리오 2: 서비스 단절점

의존 그래프에서 특정 모듈 하나가 제거되면 전체 체인이 끊기는지 확인할 때 유용하다.

### 시나리오 3: 오판

방향 그래프의 SCC와 혼동하면 안 된다.  
bridge/articulation은 기본적으로 무향 그래프에서 더 자연스럽다.

### 시나리오 4: 병목 제거

운영 관점에서는 bridge를 줄이는 방향으로 시스템을 설계하면 안정성이 높아진다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.List;

public class BridgesAndArticulation {
    private final List<List<Integer>> graph;
    private final int[] disc;
    private final int[] low;
    private final boolean[] visited;
    private int time = 0;

    public BridgesAndArticulation(List<List<Integer>> graph) {
        this.graph = graph;
        int n = graph.size();
        this.disc = new int[n];
        this.low = new int[n];
        this.visited = new boolean[n];
    }

    public void dfs(int v, int parent) {
        visited[v] = true;
        disc[v] = low[v] = ++time;
        for (int to : graph.get(v)) {
            if (to == parent) continue;
            if (!visited[to]) {
                dfs(to, v);
                low[v] = Math.min(low[v], low[to]);
                // bridge: if (low[to] > disc[v])
            } else {
                low[v] = Math.min(low[v], disc[to]);
            }
        }
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| DFS low-link | bridge/articulation을 정확히 찾는다 | 구현이 섬세하다 | 그래프 취약점 분석 |
| Union-Find | 연결성 병합이 쉽다 | critical edge를 직접 못 찾는다 | 연결 여부만 볼 때 |
| BFS/DFS 단순 탐색 | 직관적이다 | 병목 판정이 안 된다 | 소규모 분석 |

## 꼬리질문

> Q: bridge와 articulation point의 차이는?
> 의도: 간선과 정점의 criticality를 구분하는지 확인
> 핵심: 하나는 간선, 다른 하나는 정점이다.

> Q: low-link가 왜 필요한가?
> 의도: DFS back edge의 의미를 이해하는지 확인
> 핵심: 우회 경로의 존재 여부를 알아내기 때문이다.

> Q: 왜 무향 그래프에서 자주 설명하나?
> 의도: 적용 맥락 이해 확인
> 핵심: 연결성 단절의 의미가 가장 자연스럽기 때문이다.

## 한 줄 정리

Bridges와 articulation points는 그래프의 연결성을 깨는 critical edge와 critical node를 DFS low-link로 찾는 기법이다.
