---
schema_version: 3
title: Topological Sort Patterns
concept_id: algorithm/topological-sort-patterns
canonical: true
category: algorithm
difficulty: intermediate
doc_role: bridge
level: intermediate
language: mixed
source_priority: 87
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- dependency-ordering
- dag-cycle-detection
- topological-sort-vs-path-optimization
aliases:
- topological sort patterns
- topological ordering
- DAG ordering
- dependency graph ordering
- Kahn algorithm
- indegree queue
- course schedule
- build order
- workflow dependency order
- 위상 정렬 패턴
- 의존성 순서
- 진입 차수
- 빌드 순서
symptoms:
- 선후 관계 순서만 필요한 문제와 비용이 붙은 경로 최적화 문제를 모두 위상 정렬 하나로 설명하려고 한다
- indegree가 0인 노드를 queue에 넣는 이유는 외웠지만 cycle 검출 근거를 설명하지 못한다
- 작업 의존성 그래프에서 순서, 병렬 가능성, 용량 제한 배분 문제를 섞어 라우팅한다
intents:
- comparison
- deep_dive
- troubleshooting
prerequisites:
- algorithm/graph
- algorithm/dfs-bfs-intro
next_docs:
- algorithm/topological-dp
- algorithm/dijkstra-bellman-ford-floyd-warshall
- algorithm/network-flow-intuition
- system-design/job-queue-design
linked_paths:
- contents/algorithm/graph.md
- contents/algorithm/topological-dp.md
- contents/algorithm/dijkstra-bellman-ford-floyd-warshall.md
- contents/algorithm/network-flow-intuition.md
- contents/system-design/job-queue-design.md
confusable_with:
- algorithm/topological-dp
- algorithm/dijkstra-bellman-ford-floyd-warshall
- algorithm/network-flow-intuition
forbidden_neighbors: []
expected_queries:
- 위상 정렬은 어떤 그래프 문제에서 쓰고 indegree 0 queue를 왜 사용하는지 설명해줘
- course schedule이나 build order 문제에서 cycle이 있으면 왜 topological ordering이 불가능한지 알려줘
- DAG에서 순서만 구하는 문제와 최소 비용 경로를 구하는 topological DP 문제를 어떻게 구분해?
- Kahn 알고리즘과 DFS 기반 위상 정렬의 차이를 사이클 검출 기준으로 비교해줘
- 워크플로우 의존성 순서와 네트워크 플로우 같은 용량 배분 문제를 왜 따로 봐야 해?
contextual_chunk_prefix: |
  이 문서는 DAG dependency ordering을 topological sort로 라우팅하는 bridge다.
  indegree, Kahn algorithm, DFS topological sort, cycle detection, course schedule, build order, workflow dependencies, topological DP, shortest path, network flow와의 문제 정의 차이를 다룬다.
---
# Topological Sort Patterns

> 한 줄 요약: 선후 관계가 있는 작업을 순서대로 배치하는 문제를 푸는 패턴이다.
>
> 문서 역할: 이 문서는 algorithm 카테고리 안에서 **DAG dependency ordering 패턴**을 설명하는 pattern deep dive다.
>
> retrieval-anchor-keywords: topological sort, DAG ordering, dependency graph ordering, dependency order only, pure topological ordering, indegree, Kahn algorithm, DFS topological sort, course schedule, build order, build order only, workflow dependency, cycle detection, order vs shortest path, order vs network flow

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: topological sort patterns basics, topological sort patterns beginner, topological sort patterns intro, algorithm basics, beginner algorithm, 처음 배우는데 topological sort patterns, topological sort patterns 입문, topological sort patterns 기초, what is topological sort patterns, how to topological sort patterns
> 관련 문서:
> - [그래프](./graph.md)
> - [Topological DP](./topological-dp.md)
> - [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)
> - [Network Flow Intuition](./network-flow-intuition.md)
> - [위상 정렬이 자주 쓰이는 시스템 설계](../system-design/chat-system-design.md)

## 이 문서 다음에 보면 좋은 문서

- dependency graph의 기본 표현이 낯설다면 [그래프](./graph.md)에서 adjacency list와 cycle 감각을 먼저 잡으면 좋다.
- DAG라도 비용 최소/최대 경로나 누적값 계산을 따지는 순간 문제는 [Topological DP](./topological-dp.md) 쪽으로 넘어가고, 일반 shortest-path 비교까지 필요하면 [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)을 같이 보면 좋다.
- 순서가 아니라 용량, 배분, 병목이 본질이면 [Network Flow Intuition](./network-flow-intuition.md)으로 이어서 보는 편이 정확하다.

## 핵심 개념

위상 정렬은 방향 그래프 DAG에서 정점들을 선후 관계를 지키는 순서로 나열하는 것이다.

다음 같은 문제에서 자주 나온다.

- 과목 선수 과목
- 빌드 순서
- 작업 의존성
- 패키지 설치 순서
- 워크플로우 단계

핵심은 "먼저 끝나야 다음이 가능한 것"을 찾는 것이다.

## 헷갈리기 쉬운 그래프 선택 경계

| 질문 | 실제로 먼저 볼 문서 | 구분 포인트 |
|---|---|---|
| 작업의 **실행 순서**만 정하면 되는가 | 이 문서 | indegree와 cycle 여부가 핵심이다 |
| DAG에서 **최소 비용/최대 점수 경로**를 구하는가 | [Topological DP](./topological-dp.md), [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md) | 위상 정렬은 계산 보조 수단이고, 정답은 path optimization이다 |
| 사람/자원/슬롯을 **용량 제한** 아래 배분하는가 | [Network Flow Intuition](./network-flow-intuition.md) | 순서보다 capacity와 throughput이 본질이다 |

## 깊이 들어가기

### 1. Kahn 알고리즘

진입 차수(indegree)가 0인 노드부터 꺼내면서 순서를 만든다.

```text
1. 모든 노드의 indegree 계산
2. indegree 0인 노드를 queue에 넣음
3. queue에서 꺼내며 결과에 추가
4. 간선을 제거하며 indegree 감소
5. 새로 indegree 0이 된 노드를 queue에 넣음
```

장점:

- 순서를 직관적으로 얻는다.
- 사이클이 있으면 결과 길이가 N보다 짧아진다.

### 2. DFS 기반 위상 정렬

DFS 종료 시점에 스택에 넣으면 역순으로 위상 정렬 결과를 얻는다.

장점:

- 구현이 간결할 수 있다.
- 사이클 탐지도 함께 할 수 있다.

단점:

- 재귀 깊이가 깊으면 스택 오버플로 위험이 있다.

### 3. 사이클이 왜 문제인가

위상 정렬은 DAG에서만 가능하다.
사이클이 있으면 "서로가 먼저 끝나야 하는" 모순이 발생한다.

---

## 실전 시나리오

### 시나리오 1: 빌드 파이프라인

소스 파일 A가 B를 import하고, B가 C를 참조한다면 순서는 C -> B -> A가 되어야 한다.

### 시나리오 2: 주문 후처리

결제 -> 재고 차감 -> 알림 발송 같은 단계가 있을 때, 일부 단계는 병렬 가능하지만 일부는 선행 조건이 필요하다.

위상 정렬은 "병렬화 가능한 선후 관계"를 찾는 출발점이 된다.

### 시나리오 3: DAG 최단 경로와의 혼동

그래프가 DAG라고 해서 문제가 곧 위상 정렬인 것은 아니다.
비용 최소화가 목표라면 위상 정렬 순서로 DP를 돌릴 수는 있지만, 여전히 핵심 문제는 shortest path다.

### 시나리오 4: 오판

용량 제한이 있는 배분 문제를 위상 정렬로 풀려고 하면 제약이 사라진다.
위상 정렬은 "무엇이 먼저인가"를 다루고, "얼마나 보낼 수 있는가"는 다루지 않는다.

---

## 코드로 보기

```java
import java.util.*;

public class TopologicalSort {
    public List<Integer> sort(int n, List<List<Integer>> edges) {
        List<List<Integer>> graph = new ArrayList<>();
        int[] indegree = new int[n];

        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
        for (List<Integer> edge : edges) {
            int from = edge.get(0);
            int to = edge.get(1);
            graph.get(from).add(to);
            indegree[to]++;
        }

        Queue<Integer> queue = new ArrayDeque<>();
        for (int i = 0; i < n; i++) {
            if (indegree[i] == 0) queue.offer(i);
        }

        List<Integer> order = new ArrayList<>();
        while (!queue.isEmpty()) {
            int now = queue.poll();
            order.add(now);

            for (int next : graph.get(now)) {
                if (--indegree[next] == 0) {
                    queue.offer(next);
                }
            }
        }

        if (order.size() != n) {
            throw new IllegalStateException("cycle detected");
        }
        return order;
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Kahn(BFS) | 진입 차수로 직관적, 사이클 감지가 쉽다 | queue와 indegree 관리가 필요 | 순서와 의존성을 명확히 보고 싶을 때 |
| DFS | 코드가 간단할 수 있다 | 재귀 깊이 문제, 디버깅 난이도 | DFS 기반 구조가 이미 있을 때 |
| 단순 정렬 | 구현이 쉬워 보인다 | 선후 관계를 반영하지 못한다 | 사실상 적합하지 않음 |

핵심 판단 기준은 "숫자 정렬"이 아니라 "의존성 정렬"인지다.

---

## 꼬리질문

> Q: 위상 정렬 결과는 항상 하나인가?
> 의도: 선후 관계와 순열 개념을 구분하는지 확인
> 핵심: indegree 0인 노드가 여러 개면 여러 정답이 가능하다.

> Q: 사이클이 있으면 어떻게 감지하는가?
> 의도: 구현상의 검증 포인트를 아는지 확인
> 핵심: Kahn에서는 결과 길이로, DFS에서는 방문 상태로 감지한다.

> Q: 언제 위상 정렬이 실무에 쓰이는가?
> 의도: 코딩테스트 패턴을 시스템 문제로 연결하는지 확인
> 핵심: 빌드, 배포, 워크플로우, 마이그레이션 순서다.

> Q: DAG 최단 경로도 위상 정렬 문제인가요?
> 의도: 계산 순서와 문제 정의를 구분하는지 확인
> 핵심: 아니다. 위상 정렬은 도구이고, 문제 자체는 path optimization이다.

## 한 줄 정리

위상 정렬은 DAG의 선후 관계를 만족하는 순서를 찾는 패턴이고, `indegree 0`부터 처리하는 Kahn 알고리즘이 가장 실용적이다.
