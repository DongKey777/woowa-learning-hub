# Min-Cost Max-Flow Intuition

> 한 줄 요약: Min-Cost Max-Flow는 "얼마나 많이 보낼 수 있는가"와 "그중 가장 싸게 보내는 조합은 무엇인가"를 함께 푸는 흐름 최적화다.
>
> 문서 역할: 이 문서는 algorithm 카테고리 안에서 **costed assignment / weighted matching / transportation routing**을 flow 관점으로 읽는 intuition deep dive다.
>
> retrieval-anchor-keywords: min-cost max-flow, mcmf, minimum cost flow, minimum cost maximum flow, flow cost optimization, residual graph, shortest augmenting path, assignment, assignment problem, weighted matching, weighted bipartite matching, minimum cost bipartite matching, cost-aware matching, cost aware matching, cost-aware bipartite matching, minimum assignment, minimum cost assignment, cost matrix assignment, cost matrix, cheapest assignment, cheapest matching, costed assignment, costed matching, optimal assignment flow, worker job cost, worker task cost, job assignment cost, assignment with costs, linear assignment flow boundary, 1:1 weighted matching flow boundary, minimum weight perfect matching flow boundary, transportation, transportation problem, transport problem, minimum cost transportation, transportation cost minimization, shipping cost minimization, supply demand allocation, supply demand matching, supply demand transportation, warehouse store routing, logistics allocation, optimal routing, costed flow, hungarian algorithm boundary, hungarian, kuhn munkres boundary, assignment flow vs dp, weighted assignment flow, 배정 비용 최소화, 최소 비용 할당, 비용 행렬 할당, 가중치 매칭, 비용 있는 매칭, 최소 비용 매칭, 운송 문제, 수요 공급 배분, 물류 비용 최소화

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md)
> - [Network Flow Intuition](./network-flow-intuition.md)
> - [Bitmask DP](./bitmask-dp.md)
> - [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)

## 이 문서 다음에 보면 좋은 문서

- 문제가 정확히 `optimal assignment`, `linear assignment`, `정사각 cost matrix의 1:1 최소 비용 배정`이라면 [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md)이 더 직접적이다.
- 비용 없는 `maximum matching`, `최대 몇 쌍 배정` 문제라면 [Network Flow Intuition](./network-flow-intuition.md)이 먼저다.
- `N`이 작고 1:1 배정을 완전탐색형으로 최적화하거나 `dp[mask]`가 바로 떠오르면 [Bitmask DP](./bitmask-dp.md)가 더 직접적일 수 있다.
- 한 경로의 최단 비용만 묻는다면 [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) 쪽이 맞다.

---

## 이런 표현으로 들어와도 이 문서 후보다

| 질문 표현 / 검색 alias | 먼저 볼 문서 | 왜 여기로 오면 되는가 |
|---|---|---|
| `weighted matching`, `weighted bipartite matching`, `가중치 매칭` | 이 문서 | 매칭 수가 아니라 선택한 pair들의 총 비용이 objective다 |
| `hungarian algorithm`, `kuhn-munkres`, `optimal assignment`, `linear assignment` | [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md) | 순수한 1:1 cost matrix assignment면 Hungarian이 더 특화돼 있다 |
| `cost matrix assignment`, `worker-job cost matrix`, `비용 행렬 할당` | 이 문서 | `cost[i][j]` 형태의 배정 비용 표는 assignment reduction 신호다 |
| `minimum assignment`, `minimum cost assignment`, `최소 비용 할당` | 이 문서 | 모든 사람/작업을 1:1로 연결하면서 총합 비용을 최소화하는 문제다 |
| `cheapest assignment`, `costed assignment`, `배정 비용 최소화` | 이 문서 | capacity만 보는 max flow가 아니라 edge cost가 추가된 경우다 |
| `cost-aware matching`, `minimum cost bipartite matching`, `cheapest matching` | 이 문서 | cardinality matching이 아니라 pair cost 총합을 줄이는 matching 질의다 |
| `transportation problem`, `transport problem`, `minimum cost transportation`, `운송 문제` | 이 문서 | 공급/수요와 route cost를 같이 다루는 전형적인 min-cost flow 표현이다 |
| `small-n assignment`, `assignment dp`, `subset-state assignment`, `dp[mask]` | [Bitmask DP](./bitmask-dp.md) | 비용 배정이라도 subset-state exact search가 핵심이면 bitmask DP가 더 직접적이다 |
| `maximum matching`, `최대 배정 수`, `최대 몇 쌍` | [Network Flow Intuition](./network-flow-intuition.md) | 비용이 없고 cardinality만 중요하면 일반 flow/matching으로 충분하다 |

---

## 핵심 개념

Min-Cost Max-Flow는 flow의 양만 최대화하는 것이 아니라 그 flow를 보내는 총 비용까지 최소화한다.

즉 두 질문을 같이 푼다.

- 가능한 많은 유량을 보낼 수 있는가
- 그 유량을 어떤 간선 조합으로 보내야 가장 싼가

이 구조는 배분, 운송, 스케줄링, costed matching에서 자주 등장한다.

## 매칭/배정을 flow로 읽는 브리지

질문에 `assignment`, `weighted matching`, `cost matrix`, `최소 비용 할당` 같은 표현이 보이면
generic flow 용어가 없어도 먼저 "1:1 배정을 cost가 있는 flow로 바꿀 수 있는가"를 보면 된다.

### cost matrix를 그래프로 바꾸는 기본 패턴

작업자 `i`가 작업 `j`를 맡을 때 비용이 `cost[i][j]`라면 보통 이렇게 놓는다.

- `source -> worker_i`: 용량 `1`, 비용 `0`
- `worker_i -> job_j`: 용량 `1`, 비용 `cost[i][j]`
- `job_j -> sink`: 용량 `1`, 비용 `0`

여기서 `N`개의 유량을 보내면 "각 worker와 job을 한 번씩만 쓰는 minimum assignment"가 된다.

즉 `cost matrix assignment`나 `weighted bipartite matching`은
"간선 존재 여부"만 보는 max matching보다 한 단계 더 들어간 모델이다.

### weighted matching과 max matching의 차이

- **max matching / max flow**: 몇 쌍을 만들 수 있는지가 목표다.
- **weighted matching / minimum assignment**: 어떤 쌍을 선택해야 총 비용이 최소인지가 목표다.

같은 3쌍 배정이라도 pair 선택에 따라 총 비용이 완전히 달라질 수 있으므로
capacity만 보는 일반 flow로는 답이 부족하다.

## transportation을 flow로 읽는 브리지

`transportation problem`, `supply-demand allocation`, `shipping cost minimization`, `운송 문제`처럼 들어오면
"여러 공급지에서 여러 수요지로 물량을 가장 싸게 보내는 흐름"인지 먼저 보면 된다.

### transportation graph의 기본 패턴

공급지 `i`의 물량이 `supply[i]`, 수요지 `j`의 필요량이 `demand[j]`,
운송 비용이 `shippingCost[i][j]`라면 보통 이렇게 놓는다.

- `source -> supply_i`: 용량 `supply[i]`, 비용 `0`
- `supply_i -> demand_j`: 용량 `routeCapacity` 또는 충분히 큰 값, 비용 `shippingCost[i][j]`
- `demand_j -> sink`: 용량 `demand[j]`, 비용 `0`

이 구조는 "어느 한 경로가 가장 짧은가"보다
"전체 물량을 어떤 조합으로 보내야 총 운송비가 최소인가"를 묻는 모델이다.

즉 `transportation problem`은 shortest path보다 min-cost flow 쪽 vocabulary가 더 잘 맞는다.

## 작은 n assignment와의 경계

| 문제 신호 | 먼저 볼 문서 | 구분 포인트 |
|---|---|---|
| 정사각 `cost matrix`의 exact 1:1 배정 자체가 본문인가 | [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md) | Hungarian이 matrix 구조를 직접 활용한다 |
| 정사각 `cost matrix`이고 `N`이 작아서 `dp[mask]` exact search가 자연스러운가 | [Bitmask DP](./bitmask-dp.md) | subset-state DP가 더 짧고 직접적일 수 있다 |
| `weighted matching`, `minimum assignment`인데 공급/수요/부분 배정/edge capacity가 열려 있나 | 이 문서 | cost와 capacity를 함께 다루는 일반화 모델이 필요하다 |
| `transportation problem`, `supply-demand allocation`, `shipping cost minimization`처럼 multi-unit 운송인가 | 이 문서 | exact 1:1 pair 선택보다 공급량/수요량과 route cost가 본문이다 |
| 비용이 없고 `최대 몇 쌍`만 중요하나 | [Network Flow Intuition](./network-flow-intuition.md) | cardinality matching이면 일반 flow로 충분하다 |

즉 이 문서는 "cost가 있는 배정" 전반을 다루지만, `small-n subset-state optimization`이면 bitmask DP가 더 알맞을 수 있다.

## 깊이 들어가기

### 1. 왜 일반 flow만으로는 부족한가

최대 유량만 찾으면 "얼마나 많이"는 알 수 있지만 그 흐름이 가장 싸게 구성되었는지는 보장하지 않는다.

비용까지 관리해야 하면 min-cost layer가 필요하다.

### 2. residual graph와 cost

유량을 보낸 뒤 남은 잔여 그래프에서 더 좋은 경로를 찾아 재조정한다.
이때 forward edge의 cost뿐 아니라 reverse edge의 `-cost`도 함께 보며 기존 선택을 되돌릴 수 있다.

즉 한 번 싸 보이는 배정을 했더라도 이후 더 싼 전체 조합이 보이면 갈아탈 수 있다.

### 3. shortest augmenting path

많은 구현은 매번 총 추가 비용이 가장 낮은 augmenting path를 찾는다.

이때 cost가 있으므로 BFS만으로는 부족하고 Bellman-Ford나 potential을 곁들인 Dijkstra를 쓴다.

핵심 감각은 "남은 capacity가 있는 경로 중 가장 싸게 한 단위 유량을 더 보낼 경로"를 반복해서 찾는다는 점이다.

### 4. assignment problem 관점

`minimum assignment`는 보통 "모든 행/열을 정확히 한 번씩 쓰는 최소 총비용 배정"을 뜻한다.
같은 문제를 `optimal assignment`, `linear assignment`, `linear sum assignment`라고도 부른다.
이 문제는 square cost matrix라면 Hungarian으로도 풀 수 있지만,
capacity가 `1`이 아니거나 source/sink 양쪽 수요가 다르면 min-cost max-flow가 더 일반적이다.

## 실전 시나리오

### 시나리오 1: 작업 배정

각 작업을 처리할 서버가 다르고 비용이 다를 때 "최대 작업 수"와 "총 비용"을 함께 봐야 한다.
`worker-job cost matrix`, `job assignment cost`, `cheapest assignment`가 모두 같은 방향 신호다.

### 시나리오 2: 운송 최적화

공장-창고-매장처럼 여러 공급/수요 노드가 있고 경로별 운송비가 다르면
단순 max flow보다 min-cost max-flow가 자연스럽다.

### 시나리오 3: 오판

비용이 없는 매칭 문제면 일반 max flow나 bipartite matching이 더 단순하다.
반대로 1:1 배정인데 비용 행렬이 붙어 있으면 "matching"이라는 단어만 보고 max flow로 끝내면 반쪽 답이 된다.

### 시나리오 4: Hungarian과의 경계

문제가 정확히 "정사각 cost matrix의 1:1 최소 비용 할당"이라면 Hungarian이 더 특화돼 있다.
하지만 공급량/수요량, edge capacity, 부분 배정, 운송 네트워크까지 열리면 min-cost max-flow가 더 유연하다.

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
        // 설명용 스케치:
        // 가장 싼 augmenting path를 반복해서 찾고,
        // 그 경로에 흘린 유량만큼 총 cost를 누적한다.
        return new int[]{flow, cost};
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Min-Cost Max-Flow | 유량과 비용을 함께 최적화하고 capacity 변형에도 유연하다 | 구현이 복잡하다 | 배분/운송/weighted matching |
| Max Flow | 더 단순하다 | 비용을 고려하지 않는다 | 최대량이나 최대 배정 수만 중요할 때 |
| Hungarian | 1:1 cost matrix assignment에 매우 강하다 | 일반 네트워크/다중 수요로 확장하기 어렵다 | 정사각 minimum assignment |
| Bitmask DP | 작은 `N`에서 구현이 직관적일 수 있다 | `N`이 커지면 바로 폭발한다 | 작은 규모 완전탐색형 assignment |

## 꼬리질문

> Q: 왜 max flow만으로 충분하지 않나?
> 의도: 비용 최적화 필요성을 이해하는지 확인
> 핵심: 동일한 양의 배정이라도 어떤 pair를 고르느냐에 따라 총 비용이 달라진다.

> Q: `cost matrix assignment`를 min-cost max-flow로 어떻게 바꾸나?
> 의도: assignment reduction 감각 확인
> 핵심: `source -> left -> right -> sink`로 두고 가운데 간선 cost를 행렬 값으로 둔다.

> Q: `transportation problem`은 왜 shortest path보다 min-cost max-flow로 읽나?
> 의도: 운송 질의 라우팅 확인
> 핵심: 한 경로를 고르는 문제가 아니라 공급/수요를 만족하도록 여러 경로의 총 운송비를 함께 줄이는 문제다.

> Q: Hungarian과 min-cost max-flow는 어떻게 구분하나?
> 의도: 알고리즘 선택 경계 이해 확인
> 핵심: 순수 1:1 cost matrix면 Hungarian, 용량/수요/운송 제약까지 있으면 min-cost max-flow가 더 일반적이다.

## 한 줄 정리

Min-Cost Max-Flow는 weighted matching, cost matrix assignment, transportation처럼 "보내는 양"과 "총 비용"을 함께 최적화해야 할 때 쓰는 흐름 모델이다.
