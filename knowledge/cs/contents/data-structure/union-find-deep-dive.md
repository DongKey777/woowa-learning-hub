# Union-Find Deep Dive

> 한 줄 요약: 유니온 파인드는 집합을 병합하고 대표 원소를 찾는 문제를 거의 상수 시간에 처리하는 자료구조다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [자료구조 정리](./README.md)
> - [그래프 알고리즘](../algorithm/graph.md)
> - [위상 정렬 패턴](../algorithm/topological-sort-patterns.md)

## 핵심 개념

Union-Find는 Disjoint Set Union(DSU)이라고도 부른다.  
서로 겹치지 않는 집합들을 관리하면서 다음 두 연산을 빠르게 한다.

- `find(x)`: x가 속한 집합의 대표 원소를 찾는다.
- `union(a, b)`: 두 집합을 합친다.

핵심 최적화는 두 가지다.

- path compression
- union by rank/size

이 두 가지를 같이 쓰면 거의 O(1)에 가까운 암묵적 성능을 낸다.

## 깊이 들어가기

### 1. 왜 필요한가

그래프에서 "서로 연결되어 있는가"를 반복적으로 묻는 문제가 많다.

- 사이클 탐지
- 최소 신장 트리(Kruskal)
- 동적 연결성 관리
- 친구 그룹, 조직 병합, 네트워크 분리 판단

### 2. path compression

find를 수행할 때 루트를 찾는 경로상의 노드들을 모두 루트로 직접 연결한다.  
이렇게 하면 다음 find가 훨씬 빨라진다.

### 3. union by rank/size

항상 작은 트리를 큰 트리에 붙여서 높이가 비정상적으로 커지는 것을 막는다.

이 둘을 같이 쓰면 amortized time complexity가 매우 좋아진다.

## 실전 시나리오

### 시나리오 1: Kruskal의 MST

간선을 비용 순으로 보면서, 양 끝 정점이 이미 같은 집합이면 사이클이므로 버린다.  
union-find는 이 "같은 집합인지" 판단을 빠르게 해준다.

### 시나리오 2: 네트워크 연결 여부

서버 간 링크를 추가/차단하면서 그룹이 분리되었는지 확인할 때 유용하다.

## 코드로 보기

```java
public class UnionFind {
    private final int[] parent;
    private final int[] size;

    public UnionFind(int n) {
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
        int rootA = find(a);
        int rootB = find(b);
        if (rootA == rootB) return false;

        if (size[rootA] < size[rootB]) {
            int tmp = rootA;
            rootA = rootB;
            rootB = tmp;
        }

        parent[rootB] = rootA;
        size[rootA] += size[rootB];
        return true;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Union-Find | 구현이 간단하고 find/union이 매우 빠르다 | 집합 내부 순서나 경로 정보는 표현하기 어렵다 | 연결 여부, MST, 그룹 병합 |
| BFS/DFS 매번 재탐색 | 직관적이다 | 반복 질의에 비싸다 | 한 번만 확인할 때 |
| 동적 그래프 구조 | 표현력이 높다 | 구현과 유지비가 크다 | 삽입/삭제가 복잡한 그래프 |

## 꼬리질문

> Q: path compression이 왜 그렇게 중요한가?
> 의도: 암묵적 트리 평탄화의 효과를 이해하는지 확인
> 핵심: 반복 find에서 경로를 압축해야 거의 상수 시간처럼 동작한다.

> Q: union by rank와 size는 무엇이 다른가?
> 의도: 트리 높이 관리와 집합 크기 관리 차이 확인
> 핵심: 둘 다 트리 쏠림을 줄이지만, rank는 높이 추정, size는 실제 노드 수를 본다.

## 한 줄 정리

유니온 파인드는 path compression과 union by size/rank로 집합 병합과 대표 조회를 매우 빠르게 만드는 자료구조다.
