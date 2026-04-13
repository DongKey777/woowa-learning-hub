# A* vs Dijkstra

> 한 줄 요약: Dijkstra는 시작점 기준의 최단 경로를 보장하고, A*는 목표점까지의 추정 비용을 더해 더 똑똑하게 탐색을 줄인다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)
> - [그래프 관련 알고리즘](./graph.md)
> - [Greedy 알고리즘](./greedy.md)

> retrieval-anchor-keywords: A*, A star, heuristic search, admissible heuristic, consistent heuristic, pathfinding, best-first search, shortest path, routing, map search

## 핵심 개념

둘 다 최단 경로를 찾는 알고리즘이지만, 접근 방식이 다르다.

- Dijkstra: 현재까지의 실제 거리 `g(n)`만 보고 확장한다.
- A*: 실제 거리 `g(n)`에 목표까지의 추정 비용 `h(n)`를 더해 `f(n)=g(n)+h(n)`가 작은 것부터 본다.

즉 A*는 "목표에 더 가까워 보이는 후보"를 우선시한다.

실무에서는 지도 경로 탐색, 게임 NPC 이동, 라우팅 후보 탐색처럼 목표가 명확할 때 유리하다.

## 깊이 들어가기

### 1. Dijkstra는 왜 안전한가

Dijkstra는 간선 가중치가 음수가 없을 때, 가장 짧아 보이는 정점을 확정해도 나중에 더 짧아지지 않는다는 성질을 쓴다.

그래서 시작점에서 모든 정점까지의 최단 거리를 안정적으로 구한다.

### 2. A*의 heuristic이 핵심이다

A*는 추정 함수 `h(n)`가 있어야 한다.

- admissible: 실제 남은 비용을 절대 과대평가하지 않는다
- consistent: 추정치가 경로를 따라 일관되게 줄어든다

이 조건이 깨지면 최단 경로 보장이 흔들릴 수 있다.

### 3. 언제 더 빠른가

A*는 "정답이 있는 방향"을 더 빨리 파고든다.  
목표가 명확하고 좋은 heuristic이 있으면 탐색 노드를 크게 줄일 수 있다.

하지만 heuristic이 나쁘면 Dijkstra보다 별로일 수 있다.  
즉 A*는 heuristic 품질에 크게 의존한다.

### 4. backend에서의 감각

경로 탐색이 단순 지도 앱만의 문제는 아니다.

- 유사 문서/상품 후보 탐색
- 제약을 가진 경로 계획
- 상태 공간이 있는 최적화 문제

좋은 추정치가 있으면 탐색 비용이 줄어든다.

## 실전 시나리오

### 시나리오 1: 지도 경로 탐색

출발지와 목적지가 명확한 내비게이션에서는 A*가 Dijkstra보다 적은 노드를 보는 경우가 많다.

### 시나리오 2: 게임 이동

장애물이 있는 맵에서 NPC가 목표 지점으로 갈 때, 휴리스틱이 좋은 경로 탐색이 중요하다.

### 시나리오 3: 단순 최단거리 테이블

한 시작점에서 모든 정점까지의 최단 거리가 필요하면 Dijkstra가 더 자연스럽다.

### 시나리오 4: 오판

heuristic이 없는데 A*를 쓰면 사실상 Dijkstra에 가까워진다.  
반대로 heuristic이 부정확하면 결과는 맞아도 탐색량이 많아질 수 있다.

## 코드로 보기

```java
import java.util.*;

public class AStarSearch {
    private static final class Node {
        final int id;
        final int g;
        final int f;

        Node(int id, int g, int f) {
            this.id = id;
            this.g = g;
            this.f = f;
        }
    }

    public int shortestPath(int start, int goal, List<List<int[]>> graph, int[] heuristic) {
        PriorityQueue<Node> pq = new PriorityQueue<>(Comparator.comparingInt(n -> n.f));
        int[] dist = new int[graph.size()];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[start] = 0;
        pq.offer(new Node(start, 0, heuristic[start]));

        while (!pq.isEmpty()) {
            Node cur = pq.poll();
            if (cur.g != dist[cur.id]) continue;
            if (cur.id == goal) return cur.g;

            for (int[] edge : graph.get(cur.id)) {
                int next = edge[0];
                int cost = edge[1];
                int ng = cur.g + cost;
                if (ng < dist[next]) {
                    dist[next] = ng;
                    pq.offer(new Node(next, ng, ng + heuristic[next]));
                }
            }
        }
        return -1;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Dijkstra | 구현이 안정적이고 최단 경로 보장이 쉽다 | 목표를 향한 유도력이 없다 | 단일 시작점 최단 경로 |
| A* | 좋은 heuristic이 있으면 탐색을 줄인다 | heuristic 품질에 의존한다 | 시작점과 목표가 둘 다 중요할 때 |
| BFS | 가중치가 같을 때 가장 단순하다 | 가중치가 있으면 부적합하다 | 무가중 그래프 |

핵심은 "더 똑똑해 보이는 탐색"이 아니라, **목표를 향한 좋은 추정치가 있는가**다.

## 꼬리질문

> Q: A*가 Dijkstra보다 항상 빠른가?
> 의도: 휴리스틱 의존성을 이해하는지 확인
> 핵심: 아니다. heuristic이 좋을 때만 탐색을 줄인다.

> Q: admissible heuristic이 왜 중요한가?
> 의도: 최단 경로 보장 조건 확인
> 핵심: 남은 비용을 과대평가하지 않아야 최적해를 놓치지 않는다.

> Q: 언제 Dijkstra를 그냥 쓰는가?
> 의도: 실전 선택 감각 확인
> 핵심: heuristic이 없거나 단일 출발 최단거리 전체가 필요할 때다.

## 한 줄 정리

Dijkstra는 실제 누적 비용으로 최단 경로를 보장하고, A*는 목표까지의 추정 비용을 더해 더 목적지 지향적으로 탐색한다.
