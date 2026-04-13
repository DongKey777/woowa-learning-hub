# Sparse Graph Shortest Paths

> 한 줄 요약: Sparse Graph에서는 adjacency list와 우선순위 큐를 쓰는 Dijkstra 계열이 가장 자연스럽고, 가중치 분포에 따라 0-1 BFS나 Dial도 검토할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)
> - [A* vs Dijkstra](./a-star-vs-dijkstra.md)
> - [그래프 관련 알고리즘](./graph.md)

> retrieval-anchor-keywords: sparse graph shortest paths, adjacency list, priority queue dijkstra, 0-1 bfs, dial algorithm, shortest path optimization, sparse routing, weighted graph, graph representation

## 핵심 개념

Sparse graph는 간선 수 `E`가 정점 수 `V`에 비해 상대적으로 적은 그래프다.  
이런 그래프에서는 adjacency matrix보다 adjacency list가 훨씬 유리하다.

최단 경로도 마찬가지다.

- dense graph: `O(V^2)` 접근이 덜 나쁘다
- sparse graph: `O(E log V)` 계열이 더 자연스럽다

즉 그래프의 밀도에 맞는 표현과 알고리즘을 골라야 한다.

## 깊이 들어가기

### 1. 왜 adjacency list가 기본인가

희소 그래프는 실제로 존재하는 간선만 순회하는 편이 낫다.

- 메모리 절약
- 탐색 비용 절약
- 이웃 순회가 자연스러움

간선이 적을수록 adjacency list의 장점이 커진다.

### 2. Dijkstra가 sparse graph에서 빛나는 이유

우선순위 큐를 쓰는 Dijkstra는 실제 간선만 relax한다.

정점 수보다 간선 수가 훨씬 적으면 `O(V^2)`보다 훨씬 좋다.

### 3. 0-1 BFS와 Dial

가중치가 0 또는 1이면 deque를 쓰는 0-1 BFS가 더 빠르고 단순할 수 있다.

가중치가 작은 정수 범위면 Dial algorithm도 후보가 된다.

즉 sparse graph라고 해서 항상 한 가지 알고리즘만 쓰는 건 아니다.

### 4. backend에서의 감각

희소 그래프는 의존성이나 라우팅에서 흔하다.

- 서비스 호출 그래프
- 배치 의존성
- 네트워크 라우팅
- 권한/정책 전파

## 실전 시나리오

### 시나리오 1: 라우팅 비용 계산

노드 수가 많고 연결이 성기면 adjacency list 기반 Dijkstra가 자연스럽다.

### 시나리오 2: 0/1 비용 전이

체크 여부, 무료/유료 전환처럼 간선 비용이 두 종류뿐이면 0-1 BFS를 먼저 의심한다.

### 시나리오 3: 오판

간선이 적은데도 adjacency matrix로 전부 훑으면 불필요한 비용이 크다.

### 시나리오 4: 선택 기준

가중치가 일반적이면 Dijkstra, 0/1이면 0-1 BFS, 작은 정수면 Dial을 본다.

## 코드로 보기

```java
import java.util.*;

public class SparseGraphShortestPaths {
    public int[] dijkstra(List<List<int[]>> graph, int start) {
        int n = graph.size();
        int[] dist = new int[n];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[start] = 0;
        PriorityQueue<int[]> pq = new PriorityQueue<>(Comparator.comparingInt(a -> a[1]));
        pq.offer(new int[]{start, 0});

        while (!pq.isEmpty()) {
            int[] cur = pq.poll();
            int v = cur[0];
            int d = cur[1];
            if (d != dist[v]) continue;

            for (int[] edge : graph.get(v)) {
                int to = edge[0];
                int w = edge[1];
                if (dist[to] > dist[v] + w) {
                    dist[to] = dist[v] + w;
                    pq.offer(new int[]{to, dist[to]});
                }
            }
        }
        return dist;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Dijkstra + PQ | sparse graph에 잘 맞는다 | 음수 간선 불가 | 일반적인 양수 가중치 |
| 0-1 BFS | 0/1 가중치에 매우 강하다 | 적용 범위가 좁다 | 이진 비용 그래프 |
| Dial | 작은 정수 가중치에 좋다 | 버킷 관리가 필요하다 | 제한된 가중치 범위 |
| Floyd-Warshall | 구현이 단순하다 | sparse graph에서 비효율적이다 | 정점 수가 작을 때 |

핵심은 "희소하니까 무조건 Dijkstra"가 아니라, 가중치 특성까지 함께 보는 것이다.

## 꼬리질문

> Q: 왜 sparse graph에서 adjacency list가 유리한가?
> 의도: 그래프 표현 선택 기준을 이해하는지 확인
> 핵심: 실제 간선만 저장하고 순회할 수 있기 때문이다.

> Q: 0-1 BFS는 언제 쓰나?
> 의도: 가중치 특수 케이스를 아는지 확인
> 핵심: 간선 비용이 0 또는 1뿐일 때다.

> Q: Dijkstra와 A*는 어떻게 다르나?
> 의도: 최단 경로 탐색과 휴리스틱 탐색을 구분하는지 확인
> 핵심: A*는 목적지까지의 추정치를 더해 탐색을 유도한다.

## 한 줄 정리

Sparse graph의 최단 경로는 adjacency list 기반 Dijkstra 계열이 기본이고, 0/1이나 작은 정수 가중치면 더 특화된 변형을 검토한다.
