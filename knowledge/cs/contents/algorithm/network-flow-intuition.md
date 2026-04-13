# Network Flow Intuition

> 한 줄 요약: 네트워크 플로우는 "간선의 용량"을 가진 그래프에서 얼마나 많이 흘려보낼 수 있는지 계산하는 문제다.

**난이도: 🔴 Advanced**

> 관련 문서: [그래프](./graph.md)

---

## 핵심 개념

네트워크 플로우는 출발점 `source`에서 도착점 `sink`로 보낼 수 있는 최대 유량을 찾는다.

이 문제는 다음 상황에서 자주 등장한다.

- 작업 배분
- 매칭
- 용량 제한
- 물류/네트워크 대역폭

핵심은 간선마다 `capacity`가 있고, 이미 흘린 만큼은 남은 용량으로 계산한다는 점이다.

---

## 깊이 들어가기

### 1. Residual Graph

어떤 경로로 유량을 흘리면, 남은 용량을 표현하는 잔여 그래프가 생긴다.
이 잔여 그래프에서 또 다른 경로를 찾으며 유량을 계속 늘린다.

즉, 플로우는 "한 번 흘리고 끝"이 아니라 "되돌리며 다시 최적화"하는 구조다.

### 2. Augmenting Path

source에서 sink까지 남은 용량이 있는 경로를 찾으면 그만큼 더 보낼 수 있다.
이 경로를 augmenting path라고 한다.

경로를 어떻게 찾느냐에 따라 알고리즘 성능이 달라진다.

- BFS 기반: Edmonds-Karp
- 레벨 그래프 기반: Dinic

### 3. Min Cut

최대 유량은 최소 컷과 같다.
즉 source와 sink를 나누는 어떤 절단에서 끊을 수 있는 최대 용량이 곧 전체 최대 유량의 상한이다.

이 감각이 있으면 "왜 이 문제를 flow로 풀 수 있는가"를 설명하기 쉬워진다.

---

## 실전 시나리오

### 시나리오 1: 작업-자원 매칭

사람과 일감이 여러 개 있고, 각 자원은 한 번만 사용할 수 있다면 이분 매칭 문제로 볼 수 있다.
이걸 플로우 그래프로 바꾸면 구현이 쉬워진다.

### 시나리오 2: 네트워크 대역폭

서버 간 연결 용량이 정해져 있을 때 최대 처리량을 구해야 하면 flow가 자연스럽다.

### 시나리오 3: 팀 배치/일정 배정

제약 조건이 "각 사람은 한 번만", "각 팀은 최대 몇 명" 같은 형태로 바뀌면
flow 모델로 정리할 수 있다.

### 시나리오 4: 오판

단순 최단 경로 문제를 flow로 풀면 과설계가 된다.
반대로 용량 제약이 있는데 greedy로만 풀면 정답이 깨질 수 있다.

---

## 코드로 보기

```java
// BFS로 augmenting path를 찾는 개념 코드
while (true) {
    int[] parent = new int[n];
    Arrays.fill(parent, -1);
    Queue<Integer> q = new LinkedList<>();
    q.offer(source);
    parent[source] = source;

    while (!q.isEmpty() && parent[sink] == -1) {
        int cur = q.poll();
        for (Edge e : graph[cur]) {
            if (parent[e.to] == -1 && e.remaining() > 0) {
                parent[e.to] = cur;
                q.offer(e.to);
            }
        }
    }

    if (parent[sink] == -1) break;

    int flow = INF;
    for (int v = sink; v != source; v = parent[v]) {
        flow = Math.min(flow, residual(parent[v], v));
    }
    for (int v = sink; v != source; v = parent[v]) {
        push(parent[v], v, flow);
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Greedy | 빠르고 단순 | 제약이 복잡하면 깨짐 | 제약이 거의 없을 때 |
| BFS augmenting | 구현이 쉽다 | 느릴 수 있다 | 작은 그래프 |
| Dinic | 빠르고 실전적 | 구현 난이도 높음 | 매칭/용량 문제 |
| Min-cost flow | 비용까지 고려 가능 | 더 복잡하다 | 최적 비용 배분 |

네트워크 플로우는 "문제가 복잡해서 쓰는" 게 아니라,
"용량과 제약을 그래프로 바꾸면 더 명확해지는" 문제에 쓴다.

---

## 꼬리질문

> Q: 최대 유량과 최소 컷이 왜 같나요?
> 의도: flow-cut duality 이해 확인
> 핵심: 더 못 보내는 병목이 곧 끊는 최소 절단이다

> Q: Edmonds-Karp와 Dinic의 차이는 무엇인가요?
> 의도: 알고리즘 선택 감각 확인
> 핵심: 경로 찾는 방식과 성능이 다르다

> Q: 이 문제를 flow로 모델링할지 어떻게 판단하나요?
> 의도: 문제 변환 능력 확인
> 핵심: 용량, 제약, 매칭, 배분 구조를 먼저 본다

---

## 한 줄 정리

네트워크 플로우는 용량과 제약을 가진 그래프에서 source에서 sink로 보낼 수 있는 최대치를 구하는 패턴이다.

