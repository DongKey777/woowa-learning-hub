# Union-Find Component Metadata Walkthrough

> 한 줄 요약: union-find에 `component size`와 `component count` 메타데이터를 함께 두면, repeated union 중에도 "지금 이 그룹이 몇 명인지"와 "전체 그룹이 몇 개 남았는지"를 바로 답할 수 있다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Union-Find Deep Dive](./union-find-deep-dive.md)
> - [기본 자료 구조](./basic.md#union-find-유니온-파인드)
> - [그래프 알고리즘](../algorithm/graph.md)
> - [Minimum Spanning Tree: Prim vs Kruskal](../algorithm/minimum-spanning-tree-prim-vs-kruskal.md)
> - [Union-Find Amortized Proof Intuition](../algorithm/union-find-amortized-proof-intuition.md)
>
> retrieval-anchor-keywords: union find component size, union find component count, DSU metadata, disjoint set metadata, union find size array, union find connected components count, redundant union count unchanged, repeated union walkthrough, connectivity union trace, component size query, number of components union find, union by size metadata, group size after union, friend network component size, network cluster count, same set metadata, union find beginner walkthrough, union-find size example, union-find count example, componentCount dsu, size[find(x)] dsu, union find metadata tutorial, 유니온 파인드 컴포넌트 크기, 유니온 파인드 그룹 크기, 유니온 파인드 컴포넌트 개수, 서로소 집합 메타데이터, union 중 컴포넌트 수, 중복 union count 유지

## 빠른 라우팅

- `같은 그룹인가?`만 아니라 `이 그룹 크기가 몇인가?`, `전체 그룹이 몇 개 남았나?`까지 같이 추적하고 싶다면 이 문서가 바로 맞다.
- union-find 자체의 역할과 BFS/DFS 경계를 먼저 정리하고 싶다면 [Union-Find Deep Dive](./union-find-deep-dive.md)를 먼저 본다.
- `왜 거의 O(1)처럼 보이는가`가 궁금하면 [Union-Find Amortized Proof Intuition](../algorithm/union-find-amortized-proof-intuition.md)로 이어 가면 된다.
- Kruskal 문맥에서 `merged 되었는가`만 필요한 경우는 [Minimum Spanning Tree: Prim vs Kruskal](../algorithm/minimum-spanning-tree-prim-vs-kruskal.md)이 더 직접적이다.

## 문제 설정

서버 `1..6`이 처음에는 모두 따로 떨어져 있다고 하자.

- 초기 그룹 수 `componentCount = 6`
- 각 정점의 초기 그룹 크기 `size[root] = 1`
- 우리가 반복해서 알고 싶은 값:
  - `same(a, b)`: 같은 컴포넌트인가?
  - `componentSize(x)`: `x`가 속한 그룹 크기는 몇인가?
  - `componentCount()`: 현재 전체 컴포넌트는 몇 개인가?

핵심은 union-find가 원래 하던 `find`, `union`에 **메타데이터 두 개만 얹는 것**이다.

- `size[root]`: 루트가 대표하는 컴포넌트 크기
- `components`: 현재 전체 컴포넌트 개수

## 1. 어떤 값이 언제 바뀌나

초보자 기준으로는 아래 규칙만 기억하면 된다.

1. `union(a, b)` 전에 항상 `rootA = find(a)`, `rootB = find(b)`를 구한다.
2. 두 루트가 다를 때만 실제 병합이 일어난다.
3. 실제 병합이 일어나면 새 루트의 `size`를 합치고, `components`를 `1` 줄인다.
4. 이미 같은 루트였다면 `size`도 `components`도 바뀌지 않는다.

특히 `redundant union`에서 `components--`를 해버리는 실수가 아주 흔하다.

## 2. repeated union trace

아래 표는 `union by size`를 쓴다고 가정한 간단한 추적이다.
표기 `1:{1,2,3}`은 "루트 `1`이 `{1,2,3}` 컴포넌트를 대표한다"는 뜻이다.

| 단계 | 연산 | 루트 기준 결과 | merged? | 대표 size 변화 | component count |
|---|---|---|---|---|---|
| 시작 | - | `1:{1}`, `2:{2}`, `3:{3}`, `4:{4}`, `5:{5}`, `6:{6}` | - | 모두 `1` | `6` |
| 1 | `union(1, 2)` | `1:{1,2}`, `3:{3}`, `4:{4}`, `5:{5}`, `6:{6}` | yes | `size[1] = 2` | `5` |
| 2 | `union(2, 3)` | `1:{1,2,3}`, `4:{4}`, `5:{5}`, `6:{6}` | yes | `size[1] = 3` | `4` |
| 3 | `union(4, 5)` | `1:{1,2,3}`, `4:{4,5}`, `6:{6}` | yes | `size[4] = 2` | `3` |
| 4 | `union(3, 5)` | `1:{1,2,3,4,5}`, `6:{6}` | yes | `size[1] = 5` | `2` |
| 5 | `union(5, 1)` | `1:{1,2,3,4,5}`, `6:{6}` | no | 변화 없음 | `2` |
| 6 | `union(6, 1)` | `1:{1,2,3,4,5,6}` | yes | `size[1] = 6` | `1` |

여기서 가장 중요한 관찰은 두 가지다.

- `union(5, 1)`은 이미 같은 컴포넌트라서 `merged = no`다.
- 그래서 `component count`도 그대로 `2`이고, 대표 `size`도 그대로 `5`다.

즉 "union을 호출했다"와 "컴포넌트가 실제로 줄었다"는 같은 말이 아니다.

## 3. 질의는 어떻게 읽나

위 4단계 직후 상태를 기준으로 질의를 읽어 보자.

- `same(2, 4)`:
  - `find(2) = 1`
  - `find(4) = 1`
  - 따라서 `true`
- `componentSize(4)`:
  - `find(4) = 1`
  - 답은 `size[1] = 5`
- `componentCount()`:
  - 전체 그룹은 `{1,2,3,4,5}`, `{6}` 두 개
  - 답은 `2`

이때 `size[4]`를 직접 읽으면 안 된다.
`4`는 더 이상 루트가 아닐 수 있으므로, 크기는 항상 `size[find(4)]`처럼 읽는 편이 안전하다.

## 4. 코드로 옮기면

```java
public class UnionFindWithMetadata {
    private final int[] parent;
    private final int[] size;
    private int components;

    public UnionFindWithMetadata(int n) {
        this.parent = new int[n + 1];
        this.size = new int[n + 1];
        this.components = n;
        for (int i = 1; i <= n; i++) {
            parent[i] = i;
            size[i] = 1;
        }
    }

    public int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);
        }
        return parent[x];
    }

    public boolean union(int a, int b) {
        int rootA = find(a);
        int rootB = find(b);
        if (rootA == rootB) {
            return false;
        }

        if (size[rootA] < size[rootB]) {
            int tmp = rootA;
            rootA = rootB;
            rootB = tmp;
        }

        parent[rootB] = rootA;
        size[rootA] += size[rootB];
        components--;
        return true;
    }

    public boolean same(int a, int b) {
        return find(a) == find(b);
    }

    public int componentSize(int x) {
        return size[find(x)];
    }

    public int componentCount() {
        return components;
    }
}
```

## 5. 초보자 함정

- `components--`는 **실제 merge가 일어났을 때만** 해야 한다.
- `size`는 보통 **루트에만 의미 있는 값**이라고 생각하는 편이 안전하다.
- `componentSize(x)`를 구현할 때 `size[x]`를 바로 읽지 말고 `size[find(x)]`를 읽는다.
- path compression이 일어나도 `size`는 루트 기준으로만 관리하면 된다.

## 한 줄 정리

union-find에 `size[root]`와 `components`를 같이 두면, repeated union 중에도 연결 여부와 그룹 메타데이터를 한 번에 관리할 수 있다.
