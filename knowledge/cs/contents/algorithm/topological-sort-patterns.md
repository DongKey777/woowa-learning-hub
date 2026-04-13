# Topological Sort Patterns

> 한 줄 요약: 선후 관계가 있는 작업을 순서대로 배치하는 문제를 푸는 패턴이다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [그래프](./graph.md)
> - [분할 정복법](./basic.md#분할-정복법-divide-and-conquer)
> - [위상 정렬이 자주 쓰이는 시스템 설계](../system-design/chat-system-design.md)

## 핵심 개념

위상 정렬은 방향 그래프 DAG에서 정점들을 선후 관계를 지키는 순서로 나열하는 것이다.

다음 같은 문제에서 자주 나온다.

- 과목 선수 과목
- 빌드 순서
- 작업 의존성
- 패키지 설치 순서
- 워크플로우 단계

핵심은 "먼저 끝나야 다음이 가능한 것"을 찾는 것이다.

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

## 한 줄 정리

위상 정렬은 DAG의 선후 관계를 만족하는 순서를 찾는 패턴이고, `indegree 0`부터 처리하는 Kahn 알고리즘이 가장 실용적이다.
