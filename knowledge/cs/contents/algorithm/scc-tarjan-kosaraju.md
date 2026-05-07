---
schema_version: 3
title: Strongly Connected Components Tarjan vs Kosaraju
concept_id: algorithm/scc-tarjan-kosaraju
canonical: true
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- strongly-connected-components
- tarjan-kosaraju-comparison
- condensation-graph-dag
aliases:
- strongly connected components
- SCC Tarjan Kosaraju
- Tarjan algorithm
- Kosaraju algorithm
- low-link
- condensation graph
- component DAG
- directed graph cycle
- 강한 연결 요소
symptoms:
- 방향 그래프에서 단순 연결성과 서로 왕복 도달 가능성을 구분하지 못한다
- SCC를 찾은 뒤 component DAG로 압축해 topological sort나 DP를 적용하는 후속 단계를 놓친다
- Tarjan의 low-link와 Kosaraju의 reversed graph two-pass 흐름을 같은 구현으로 섞어 설명한다
intents:
- deep_dive
- comparison
- troubleshooting
prerequisites:
- algorithm/graph
- algorithm/topological-sort-patterns
next_docs:
- algorithm/topological-dp
- algorithm/network-flow-intuition
- software-engineering/modular-monolith-boundary-enforcement
linked_paths:
- contents/algorithm/graph.md
- contents/algorithm/topological-sort-patterns.md
- contents/algorithm/network-flow-intuition.md
- contents/algorithm/topological-dp.md
confusable_with:
- algorithm/topological-sort-patterns
- algorithm/topological-dp
- algorithm/network-flow-intuition
- data-structure/union-find-deep-dive
forbidden_neighbors: []
expected_queries:
- SCC는 방향 그래프에서 서로 왕복 도달 가능한 정점 묶음이라는 뜻이야?
- Tarjan의 low-link와 Kosaraju의 reverse graph 두 번 DFS는 어떤 차이가 있어?
- SCC를 component DAG로 압축하면 왜 위상 정렬이나 DP가 쉬워져?
- 서비스나 모듈 의존성 사이클을 SCC로 찾는 감각을 설명해줘
- 단순 DFS 연결성과 strongly connected component는 방향 그래프에서 어떻게 달라?
contextual_chunk_prefix: |
  이 문서는 Strongly Connected Components deep dive로, directed graph에서
  서로 왕복 도달 가능한 정점 묶음을 Tarjan low-link 또는 Kosaraju two-pass로
  찾고 condensation graph를 DAG로 만들어 topological sort/DP로 넘기는 흐름을
  설명한다.
---
# Strongly Connected Components: Tarjan vs Kosaraju

> 한 줄 요약: SCC는 서로 도달 가능한 정점들을 한 덩어리로 묶는 개념이고, Tarjan과 Kosaraju는 그 덩어리를 찾는 대표 방법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [그래프 관련 알고리즘](./graph.md)
> - [위상 정렬 패턴](./topological-sort-patterns.md)
> - [네트워크 플로우 직관](./network-flow-intuition.md)

> retrieval-anchor-keywords: strongly connected components, SCC, Tarjan, Kosaraju, low-link, condensation graph, cycle detection, dependency graph, directed graph, component DAG

## 핵심 개념

SCC(Strongly Connected Component)는 **방향 그래프에서 서로 왕복 도달이 가능한 정점들의 최대 집합**이다.

SCC를 구하면 많은 문제가 단순해진다.

- 방향 그래프의 순환 구조를 압축할 수 있다.
- SCC를 하나의 정점처럼 보면 DAG가 된다.
- 그 다음에는 위상 정렬 같은 알고리즘을 적용하기 쉬워진다.

실무 감각으로는 "서로 강하게 얽힌 의존성 덩어리"를 찾는 문제라고 보면 좋다.

## 깊이 들어가기

### 1. 왜 SCC를 찾나

방향 그래프에서 중요한 건 단순 연결성이 아니라 **상호 도달 가능성**이다.

예를 들어:

- 서비스 A가 B를 호출하고 B가 다시 A를 호출하면 사이클이다.
- 패키지 의존성이 서로 물려 있으면 배포 순서가 꼬인다.
- 작업 그래프에서 순환이 있으면 선후 관계가 깨진다.

SCC는 이런 "묶여 있는 사이클 덩어리"를 찾아낸다.

### 2. Tarjan은 low-link가 핵심이다

Tarjan 알고리즘은 DFS 한 번으로 SCC를 찾는다.

핵심 개념:

- `disc[v]`: 방문 순서
- `low[v]`: v에서 DFS 트리와 back edge를 통해 도달 가능한 가장 작은 방문 번호
- 스택: 현재 SCC 후보를 유지

어떤 정점의 `low[v] == disc[v]`가 되면, 그 정점은 SCC의 루트가 된다.

### 3. Kosaraju는 두 번 DFS한다

Kosaraju 알고리즘은 더 직관적이다.

1. 원래 그래프에서 DFS를 돌려 종료 순서를 저장한다.
2. 간선을 뒤집은 그래프에서 종료 순서 역순으로 DFS를 돌린다.

첫 번째 패스가 "나가는 순서"를 저장하고, 두 번째 패스가 SCC를 분리한다.

### 4. condensation graph가 왜 중요한가

SCC를 하나의 정점으로 압축하면, 압축 그래프는 DAG가 된다.  
이 DAG 위에서는 위상 정렬이나 DP를 적용하기가 쉬워진다.

즉 SCC는 끝이 아니라, 더 다루기 쉬운 그래프로 바꾸는 전처리다.

## 실전 시나리오

### 시나리오 1: 서비스 의존성 사이클 탐지

마이크로서비스가 서로를 물고 늘어지는 호출 구조를 SCC로 보면, 실제로 어떤 서비스 집합이 한 덩어리인지 드러난다.

### 시나리오 2: 패키지/모듈 의존성 정리

빌드 시스템에서 모듈 사이에 순환 의존성이 있으면 배포가 어려워진다.  
SCC는 그 순환 묶음을 찾아 리팩토링 우선순위를 정하는 데 도움이 된다.

### 시나리오 3: 작업 그래프 압축

작업 간 순환이 섞인 상태에서 위상 정렬이 안 되면, 먼저 SCC로 압축해 component DAG를 만들어야 한다.

### 시나리오 4: 오판

단순 BFS/DFS로는 "연결되어 있다"만 보이고, "서로 왕복 가능한가"는 놓치기 쉽다.  
방향 그래프에서는 SCC가 더 정확한 질문이다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.List;
import java.util.Stack;

public class TarjanScc {
    private final List<List<Integer>> graph;
    private final int[] disc;
    private final int[] low;
    private final boolean[] onStack;
    private final Stack<Integer> stack = new Stack<>();
    private final List<List<Integer>> components = new ArrayList<>();
    private int time = 0;

    public TarjanScc(List<List<Integer>> graph) {
        this.graph = graph;
        int n = graph.size();
        this.disc = new int[n];
        this.low = new int[n];
        this.onStack = new boolean[n];
    }

    public List<List<Integer>> run() {
        for (int v = 0; v < graph.size(); v++) {
            if (disc[v] == 0) {
                dfs(v);
            }
        }
        return components;
    }

    private void dfs(int v) {
        disc[v] = low[v] = ++time;
        stack.push(v);
        onStack[v] = true;

        for (int next : graph.get(v)) {
            if (disc[next] == 0) {
                dfs(next);
                low[v] = Math.min(low[v], low[next]);
            } else if (onStack[next]) {
                low[v] = Math.min(low[v], disc[next]);
            }
        }

        if (low[v] == disc[v]) {
            List<Integer> component = new ArrayList<>();
            while (true) {
                int node = stack.pop();
                onStack[node] = false;
                component.add(node);
                if (node == v) {
                    break;
                }
            }
            components.add(component);
        }
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Tarjan | 한 번의 DFS로 SCC를 구한다 | low-link와 스택 이해가 필요하다 | 성능과 메모리 둘 다 중요할 때 |
| Kosaraju | 개념이 직관적이다 | 그래프를 뒤집고 DFS를 두 번 돈다 | 구현 실수를 줄이고 싶을 때 |
| 단순 DFS/BFS | 쉽다 | SCC를 정확히 구하지 못한다 | 연결 여부만 볼 때 |

Tarjan은 빠르고, Kosaraju는 이해가 쉽다.  
둘 다 결과는 SCC지만, 실수 포인트가 다르다.

## 꼬리질문

> Q: SCC를 찾으면 무엇이 좋아지나?
> 의도: 압축 후 구조를 이해하는지 확인
> 핵심: component DAG가 되어 위상 정렬과 DP가 쉬워진다.

> Q: Tarjan의 low-link는 무엇을 뜻하나?
> 의도: DFS 트리와 back edge 관계 이해 확인
> 핵심: 현재 정점에서 도달 가능한 가장 이른 방문 시점을 나타낸다.

> Q: Kosaraju는 왜 그래프를 뒤집나?
> 의도: 종료 순서와 역방향 탐색의 의미 확인
> 핵심: SCC 경계가 뒤집힌 그래프에서 더 잘 분리되기 때문이다.

## 한 줄 정리

SCC는 방향 그래프의 순환 덩어리를 압축하는 도구이고, Tarjan과 Kosaraju는 그 덩어리를 찾는 대표적인 두 방식이다.
