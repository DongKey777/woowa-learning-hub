# Union-Find Amortized Proof Intuition

> 한 줄 요약: Union-Find가 거의 O(1)처럼 보이는 이유는 path compression과 union by size/rank가 트리 높이를 계속 눌러 주기 때문이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Union-Find Deep Dive](../data-structure/union-find-deep-dive.md)
> - [Amortized Analysis Pitfalls](./amortized-analysis-pitfalls.md)
> - [그래프 관련 알고리즘](./graph.md)

> retrieval-anchor-keywords: union-find amortized proof, path compression intuition, union by rank, inverse ackermann, disjoint set, potential method, almost constant time, DSU proof, tree flattening

## 핵심 개념

Union-Find의 성능 설명은 보통 `O(alpha(n))` 또는 "거의 상수"라고 말한다.  
이 문서는 그 표현이 왜 나오는지에 대한 직관을 다룬다.

핵심은 두 가지다.

- 작은 트리는 큰 트리에 붙인다.
- find를 할 때 경로를 직접 루트로 연결해 버린다.

이 두 최적화가 함께 작동하면, 한 번 비싼 일을 해도 다음부터는 훨씬 싸진다.

## 깊이 들어가기

### 1. 왜 path compression이 강한가

find는 루트를 찾는 과정에서 경로에 있는 노드들을 전부 루트에 붙여 버린다.

한 번 지나간 길을 평평하게 만들어 두기 때문에, 같은 경로를 다음에 다시 갈 때 비용이 크게 줄어든다.

직관적으로는 "길 안내를 받은 사람은 다음부터 바로 목적지를 기억한다"에 가깝다.

### 2. union by size/rank가 왜 중요한가

작은 트리를 큰 트리에 붙이면 높이가 급격히 자라지 않는다.

- size: 실제 원소 수를 본다
- rank: 높이 추정치를 본다

둘 다 쏠림을 막는 장치다.  
path compression만 있고 union 규칙이 없으면 긴 체인이 생길 수 있다.

### 3. 왜 상각 분석이 맞는가

어떤 find는 비쌀 수 있다.
하지만 그 비싼 find가 경로를 평탄화해 다음 호출들을 싸게 만든다.

즉 비용이 한 번에 몰리지 않고, 여러 연산에 분산된다.

이 때문에 개별 연산 기준 worst-case와 전체 연산 평균 감각이 달라진다.

### 4. backend에서의 감각

Union-Find는 반복적인 그룹 병합과 연결성 질의가 많을 때 강하다.

- 클러스터 병합
- 셋 합치기
- 연결성 추적
- 실시간 그룹 판별

## 실전 시나리오

### 시나리오 1: Kruskal

사이클이 생기는 간선을 빠르게 걸러내야 할 때 find가 반복된다.  
상각적으로 거의 상수처럼 동작하니 MST에서 잘 맞는다.

### 시나리오 2: 동적 연결성

서버 그룹이나 친구 집합을 반복적으로 합칠 때, path compression이 누적될수록 질의가 더 빨라진다.

### 시나리오 3: 오판

삭제가 자주 일어나는 동적 그래프에는 Union-Find가 잘 맞지 않는다.  
이 구조는 기본적으로 merge-friendly다.

### 시나리오 4: 비용 체감

초반에는 트리가 깊어서 find가 조금 느릴 수 있지만, 연산이 쌓일수록 구조가 납작해진다.

## 코드로 보기

```java
public class UnionFindAmortized {
    private final int[] parent;
    private final int[] size;

    public UnionFindAmortized(int n) {
        this.parent = new int[n];
        this.size = new int[n];
        for (int i = 0; i < n; i++) {
            parent[i] = i;
            size[i] = 1;
        }
    }

    public int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]); // path compression
        }
        return parent[x];
    }

    public boolean union(int a, int b) {
        int ra = find(a);
        int rb = find(b);
        if (ra == rb) return false;
        if (size[ra] < size[rb]) {
            int tmp = ra; ra = rb; rb = tmp;
        }
        parent[rb] = ra;
        size[ra] += size[rb];
        return true;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Union-Find | merge/find가 매우 빠르다 | 삭제와 순서 정보 표현이 어렵다 | 연결성, 병합, MST |
| BFS/DFS 재탐색 | 직관적이다 | 반복 질의에 비싸다 | 한두 번만 확인할 때 |
| 동적 그래프 구조 | 유연하다 | 구현과 유지비가 크다 | 삽입/삭제가 빈번할 때 |

핵심은 "상각적으로 거의 상수"가 실제 서비스에서도 "항상 즉시"라는 뜻은 아니라는 점이다.

## 꼬리질문

> Q: 왜 find가 한 번 비싸도 괜찮은가?
> 의도: 상각 비용 분산을 이해하는지 확인
> 핵심: 그 비싼 작업이 다음 호출들을 싸게 만들기 때문이다.

> Q: union by size와 rank는 왜 같이 언급되나?
> 의도: 트리 쏠림 방지 원리를 이해하는지 확인
> 핵심: 둘 다 트리를 얕게 유지하는 전략이다.

> Q: 삭제가 많은 문제에 왜 약한가?
> 의도: 적용 범위 확인
> 핵심: 병합은 쉽지만 분해는 어렵기 때문이다.

## 한 줄 정리

Union-Find의 거의 상수 성능은 path compression이 경로를 평탄화하고 union by size/rank가 트리 쏠림을 막기 때문에 나온다.
