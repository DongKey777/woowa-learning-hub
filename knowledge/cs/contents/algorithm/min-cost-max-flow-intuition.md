# Min-Cost Max-Flow Intuition

> 한 줄 요약: Min-Cost Max-Flow는 최대 유량을 보내면서 총 비용까지 최소화하는 흐름 최적화 문제다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Network Flow Intuition](./network-flow-intuition.md)
> - [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)
> - [Topological DP](./topological-dp.md)

> retrieval-anchor-keywords: min-cost max-flow, mcmf, flow cost optimization, residual graph, shortest augmenting path, assignment, transportation, optimal routing, costed flow

## 핵심 개념

Min-Cost Max-Flow는 flow의 양만 최대화하는 것이 아니라,  
그 flow를 보내는 비용까지 함께 최소화하는 문제다.

즉 두 목표가 있다.

- 가능한 많은 유량을 보낸다
- 그 유량을 가장 싼 비용으로 보낸다

이 구조는 배분, 매칭, 운송, 스케줄링에서 자주 등장한다.

## 깊이 들어가기

### 1. 왜 일반 flow만으로는 부족한가

최대 유량만 찾으면 "얼마나 많이"는 알 수 있지만,  
그 흐름이 가장 싸게 구성되었는지는 보장하지 않는다.

비용까지 관리해야 하면 min-cost layer가 필요하다.

### 2. residual graph와 cost

유량을 보낸 뒤 남은 잔여 그래프에서 더 좋은 경로를 찾아 재조정한다.  
이때 간선 비용도 함께 고려한다.

### 3. shortest augmenting path

많은 구현은 매번 비용이 가장 낮은 augmenting path를 찾는다.

이때 가중치가 있을 수 있으므로 Dijkstra나 Bellman-Ford 변형이 필요하다.

### 4. backend에서의 감각

min-cost max-flow는 자원 배분 문제를 깔끔하게 모델링할 수 있다.

- 작업-서버 배정
- 물류 비용 최소화
- 광고 슬롯 배치
- 요청을 여러 경로로 분산할 때의 비용 최적화

## 실전 시나리오

### 시나리오 1: 작업 배정

각 작업을 처리할 서버가 다르고 비용이 다를 때, 최대 작업 수와 최소 비용을 동시에 고려한다.

### 시나리오 2: 운송 최적화

물류 네트워크에서 최대 처리량을 보내면서 비용을 낮추고 싶을 때 맞다.

### 시나리오 3: 오판

비용이 없는 매칭 문제면 일반 max flow나 bipartite matching이 더 단순하다.

### 시나리오 4: 안정성

경로마다 비용이 다르면 greedy만으로는 전체 최적을 보장하기 어렵다.

## 코드로 보기

```java
import java.util.*;

public class MinCostMaxFlow {
    static final class Edge {
        int to, rev, cap, cost;
        Edge(int to, int rev, int cap, int cost) {
            this.to = to; this.rev = rev; this.cap = cap; this.cost = cost;
        }
    }

    private final List<List<Edge>> graph;

    public MinCostMaxFlow(int n) {
        graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
    }

    public void addEdge(int u, int v, int cap, int cost) {
        Edge a = new Edge(v, graph.get(v).size(), cap, cost);
        Edge b = new Edge(u, graph.get(u).size(), 0, -cost);
        graph.get(u).add(a);
        graph.get(v).add(b);
    }

    public int[] solve(int s, int t) {
        int flow = 0, cost = 0;
        // 설명용 스케치: 실제 구현은 shortest augmenting path 반복이 필요하다.
        return new int[]{flow, cost};
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Min-Cost Max-Flow | 유량과 비용을 동시에 최적화한다 | 구현이 복잡하다 | 배분/운송/최적 매칭 |
| Max Flow | 더 단순하다 | 비용을 고려하지 않는다 | 최대량만 중요할 때 |
| Hungarian | 특정 매칭에 강하다 | 적용 범위가 좁다 | 1:1 할당 |

## 꼬리질문

> Q: 왜 max flow만으로 충분하지 않나?
> 의도: 비용 최적화 필요성을 이해하는지 확인
> 핵심: 동일한 양의 흐름이라도 비용이 다를 수 있기 때문이다.

> Q: 비용 간선이 있으면 어떤 경로 탐색이 필요한가?
> 의도: shortest path와 flow 결합 감각 확인
> 핵심: 최소 비용 augmenting path를 찾아야 한다.

> Q: 어디에 실무적으로 쓰이나?
> 의도: 배분/운송 모델링 이해 확인
> 핵심: 자원 배정, 물류, 비용 최소화 매칭이다.

## 한 줄 정리

Min-Cost Max-Flow는 최대 유량을 보내면서 총 비용도 최소화하는 흐름 최적화 기법이다.
