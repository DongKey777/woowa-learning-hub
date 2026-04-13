# Topological DP

> 한 줄 요약: Topological DP는 DAG를 위상 순서로 훑으면서, 각 정점의 최적값을 선행 정점에서 전달받아 갱신하는 패턴이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Topological Sort Patterns](./topological-sort-patterns.md)
> - [Strongly Connected Components: Tarjan vs Kosaraju](./scc-tarjan-kosaraju.md)
> - [그래프 관련 알고리즘](./graph.md)

> retrieval-anchor-keywords: topological dp, dag dp, dependency dp, longest path dag, earliest finish time, build pipeline dp, indegree order, acyclic graph, task scheduling

## 핵심 개념

Topological DP는 방향 비순환 그래프(DAG)에서만 자연스럽게 쓸 수 있다.  
위상 정렬 순서대로 노드를 처리하면, 선행 조건이 먼저 계산되기 때문이다.

대표적으로 다음 문제에 잘 맞는다.

- DAG 최장 경로
- 작업 완료 시점
- 의존성 기반 누적 비용
- 빌드/배포 단계별 최소 시간

## 깊이 들어가기

### 1. 왜 위상 정렬이 필요하나

DP는 보통 "앞선 상태가 먼저 계산돼 있어야" 편하다.

DAG에서는 위상 정렬이 바로 그런 순서를 제공한다.

- 먼저 끝나는 작업
- 그다음 의존 작업
- 최종 결과

### 2. state transition

정점 `u`에서 `v`로 가는 간선이 있으면, `dp[v]`는 `dp[u]`를 보고 갱신된다.

즉 각 노드는 predecessor들로부터 값을 받아서 자신의 최적값을 결정한다.

### 3. longest path in DAG

가중치가 있는 DAG에서 최장 경로는 위상 순서로 DP를 하면 된다.

사이클이 없기 때문에 "계속 더 좋아질 수도 있음" 같은 문제가 없다.

### 4. backend에서의 감각

워크플로우, 빌드, 배포, 데이터 파이프라인은 모두 DAG-like한 경우가 많다.

- 마이그레이션 순서
- batch pipeline 단계
- 컴파일 의존성
- 작업 선행 관계

## 실전 시나리오

### 시나리오 1: 빌드 시간 계산

각 모듈의 빌드 시간이 있고 의존성이 있다면, 위상 순서로 누적해서 가장 늦게 끝나는 시점을 구할 수 있다.

### 시나리오 2: 작업 스케줄링

작업이 끝나야 다음 작업이 시작되는 구조에서 earliest finish time을 계산할 수 있다.

### 시나리오 3: 오판

사이클이 있으면 topological DP가 성립하지 않는다.  
이 경우 SCC로 압축하거나 아예 문제 조건을 다시 봐야 한다.

### 시나리오 4: 최단/최장

가중치와 목적에 따라 max/min 갱신만 바뀔 뿐, 위상 순서 DP라는 틀은 같다.

## 코드로 보기

```java
import java.util.*;

public class TopologicalDp {
    public int[] longestPath(int n, List<List<int[]>> graph) {
        int[] indegree = new int[n];
        for (int u = 0; u < n; u++) {
            for (int[] edge : graph.get(u)) {
                indegree[edge[0]]++;
            }
        }

        Queue<Integer> q = new ArrayDeque<>();
        for (int i = 0; i < n; i++) {
            if (indegree[i] == 0) q.offer(i);
        }

        int[] dp = new int[n];
        Arrays.fill(dp, Integer.MIN_VALUE / 4);
        for (int i = 0; i < n; i++) {
            if (indegree[i] == 0) dp[i] = 0;
        }

        while (!q.isEmpty()) {
            int u = q.poll();
            for (int[] edge : graph.get(u)) {
                int v = edge[0];
                int w = edge[1];
                dp[v] = Math.max(dp[v], dp[u] + w);
                if (--indegree[v] == 0) q.offer(v);
            }
        }
        return dp;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Topological DP | 선후 관계를 자연스럽게 반영한다 | DAG여야 한다 | 의존성 그래프 |
| 일반 DFS DP | 코드가 단순할 수 있다 | 재방문 처리와 사이클 문제가 있다 | 작은 그래프 |
| Bellman-Ford 스타일 | 사이클/음수까지 다룰 수 있다 | 느리다 | 제약이 복잡할 때 |

Topological DP는 "정렬된 순서로 DP를 흘려보낸다"는 감각이 핵심이다.

## 꼬리질문

> Q: 왜 DAG에서만 잘 맞나?
> 의도: 위상 순서의 전제 이해 확인
> 핵심: 사이클이 있으면 선행 상태가 끝없이 서로를 기다린다.

> Q: 최장 경로를 왜 DP로 구할 수 있나?
> 의도: 선행 결과 누적 구조 이해 확인
> 핵심: 위상 순서가 predecessor를 먼저 보장해 주기 때문이다.

> Q: SCC와 어떤 관계가 있나?
> 의도: 사이클 압축 후 DAG로 바꾸는 감각 확인
> 핵심: SCC를 압축하면 DAG가 되어 topological DP를 적용할 수 있다.

## 한 줄 정리

Topological DP는 DAG를 위상 순서로 처리해 각 정점의 값을 선행 정점에서 누적하는 동적 계획법 패턴이다.
