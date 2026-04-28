# Union-Find Component Metadata Walkthrough

> 한 줄 요약: union-find에 `component size`와 `component count` 메타데이터를 함께 두면, repeated union 중에도 "지금 이 그룹이 몇 명인지"와 "전체 그룹이 몇 개 남았는지"를 바로 답할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md)
- [Connectivity Question Router](./connectivity-question-router.md)
- [Union-Find Deep Dive](./union-find-deep-dive.md)
- [기본 자료 구조](./basic.md#union-find-유니온-파인드)
- [그래프 알고리즘](../algorithm/graph.md)
- [Minimum Spanning Tree: Prim vs Kruskal](../algorithm/minimum-spanning-tree-prim-vs-kruskal.md)
- [Union-Find Amortized Proof Intuition](../algorithm/union-find-amortized-proof-intuition.md)

retrieval-anchor-keywords: union find component size, union find component count, dsu metadata, connected components count dsu, component size query, size[find(x)] dsu, repeated union walkthrough, union 했는데 count 왜 안 줄어, union 했는데 size 왜 그대로, friend relation group count, network group count, 연결 요소 수, 친구 관계 그룹 수, 네트워크 그룹 수, union find metadata 뭐예요

## 빠른 라우팅

- 질문이 `연결되어 있나요?`에서 끝나는지, `그 그룹 크기는요? 전체 그룹은요?`까지 가는지 먼저 헷갈리면 [Connectivity Question Router](./connectivity-question-router.md)에서 답 모양을 먼저 고른 뒤 이 문서로 오면 된다.
- union-find를 처음 보는 단계라면 먼저 [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md)에서 `same component yes/no` 감각을 고정하고 오는 편이 빠르다.
- `같은 그룹인가?`만 아니라 `이 그룹 크기가 몇인가?`, `전체 그룹이 몇 개 남았나?`까지 같이 추적하고 싶다면 이 문서가 바로 맞다.
- union-find 자체의 역할과 BFS/DFS 경계를 먼저 정리하고 싶다면 [Union-Find Deep Dive](./union-find-deep-dive.md)를 먼저 본다.
- `왜 거의 O(1)처럼 보이는가`가 궁금하면 [Union-Find Amortized Proof Intuition](../algorithm/union-find-amortized-proof-intuition.md)로 이어 가면 된다.
- Kruskal 문맥에서 `merged 되었는가`만 필요한 경우는 [Minimum Spanning Tree: Prim vs Kruskal](../algorithm/minimum-spanning-tree-prim-vs-kruskal.md)이 더 직접적이다.

## 15초 진입 체크

| 질문 문장 | 이 문서가 맞나 | 이유 |
|---|---|---|
| `1과 9가 같은 그룹인가요?` | 경우에 따라 | yes/no만 필요하면 일반 union-find 문서만으로 충분하다 |
| `1이 속한 그룹 크기는 몇인가요?` | 예 | `size[find(x)]` 메타데이터가 핵심이다 |
| `지금 전체 그룹이 몇 개인가요?` | 예 | `componentCount`를 추적해야 한다 |
| `1에서 9까지 실제 경로를 출력해 주세요` | 아니오 | DSU 메타데이터가 아니라 BFS/DFS 경로 복원 문제다 |

## 초보 별칭 한 번에 번역

문제 문장이 용어 대신 생활 표현으로 와도, 아래처럼 `무엇을 세는가`만 번역하면 같은 문서로 모인다.

| 이렇게 말해도 | 실제로 보는 값 | 이 문서에서 잡는 포인트 |
|---|---|---|
| `친구 관계가 몇 그룹으로 나뉘어 있나요?` | `componentCount()` | 전체 그룹 수를 줄여 가는 문제다 |
| `지금 네트워크 그룹이 몇 개 남았나요?` | `componentCount()` | 연결될 때마다 그룹 수가 `1`씩 줄 수 있다 |
| `연결 요소 수를 계속 물어봐요` | `componentCount()` | `connected components count`를 메타데이터로 들고 간다 |
| `3번이 속한 친구 묶음은 몇 명인가요?` | `componentSize(3)` | `size[find(3)]`를 읽어야 한다 |

짧게 말하면 `친구 관계`, `네트워크 그룹`, `연결 요소 수`는 표현만 다르고, 이 문서에서는 결국 `그룹 크기`와 `전체 그룹 수` 메타데이터를 관리하는 같은 종류의 질문이다.

## 먼저 잡는 mental model

union-find를 "그룹 대표 연락처"라고 생각하면 메타데이터가 훨씬 덜 헷갈린다.

- `parent[x]`: `x`가 따라가야 할 대표 경로
- `size[root]`: 대표가 들고 있는 그룹 인원수
- `components`: 현재 전체 그룹 개수

핵심은 `union(a, b)` 호출 자체가 아니라 **실제로 합쳐졌는지(`merged`)**다.
합쳐지지 않았다면 `size`, `components`는 그대로여야 한다.

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

입문자가 처음 구현할 때는 아래 매핑을 옆에 두고 시작하는 편이 안전하다.

| 문제에서 묻는 값 | 실제로 읽는 값 | 흔한 실수 |
|---|---|---|
| `same(a, b)` | `find(a) == find(b)` | parent를 한 칸만 보고 끝내기 |
| `componentSize(x)` | `size[find(x)]` | `size[x]`를 바로 읽기 |
| `componentCount()` | `components` 필드 | union 호출 횟수로 세기 |

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

## 2-1. 1페이지 미니 trace

router 다음에 바로 읽는 입문자라면, 아래 한 장만 보면 된다.
핵심은 `union 호출`이 아니라 `실제로 합쳐졌는가`를 `before -> after`로 보는 것이다.

| 연산 | `find` 결과 | before | after | `componentSize(3)` | `componentCount()` |
|---|---|---|---|---|---|
| 시작 | - | `{1}` `{2}` `{3}` `{4}` `{5}` `{6}` | 그대로 | `1` | `6` |
| `union(1, 2)` | `1`, `2` | `size[1]=1`, `size[2]=1`, `count=6` | `{1,2}`, `size[1]=2`, `count=5` | `1` | `5` |
| `union(2, 3)` | `1`, `3` | `size[1]=2`, `size[3]=1`, `count=5` | `{1,2,3}`, `size[1]=3`, `count=4` | `3` | `4` |
| `union(4, 5)` | `4`, `5` | `size[4]=1`, `size[5]=1`, `count=4` | `{4,5}`, `size[4]=2`, `count=3` | `3` | `3` |
| `union(3, 5)` | `1`, `4` | `size[1]=3`, `size[4]=2`, `count=3` | `{1,2,3,4,5}`, `size[1]=5`, `count=2` | `5` | `2` |
| `union(5, 1)` | `1`, `1` | 이미 같은 루트, `count=2` | 변화 없음 | `5` | `2` |

이 표에서 초보자가 바로 잡아야 하는 오해는 세 가지다.

- `union(2, 3)`에서 `2`의 루트는 `2`가 아니라 `1`이다. 그래서 더하는 값은 `size[2]`가 아니라 `size[1] + size[3]`이다.
- `componentSize(3)`은 `3`번 칸의 숫자가 아니라 `find(3)`이 가리키는 대표 묶음 크기다.
- `union(5, 1)`처럼 `find` 결과가 같으면 union을 호출해도 `count`가 줄지 않는다.

증상 문장으로 바꾸면 이렇게 읽으면 된다.

| 헷갈리는 말 | 바로 고칠 해석 |
|---|---|
| `union 했는데 count가 왜 안 줄어요?` | 이미 같은 루트끼리 붙였기 때문이다 |
| `3번 그룹 크기를 보는데 왜 5가 돼요?` | `3`이 아니라 `find(3)`의 대표 묶음이 5명이기 때문이다 |
| `size[5]를 보면 안 되나요?` | `5`가 루트가 아닐 수 있으니 `size[find(5)]`를 봐야 한다 |

짧게 외우면 `componentSize(x)`는 "`x` 칸의 값"이 아니라 "`find(x)` 대표 묶음의 값"이다.

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

## 6. 다음 단계 라우팅

- 연결성 질문 자체의 분기(`yes/no` vs 경로 복원 vs 최단 경로)가 헷갈리면: [Connectivity Question Router](./connectivity-question-router.md)
- 간선 삭제까지 들어오는 동적 연결성으로 확장하려면: [Deletion-Aware Connectivity Bridge](./deletion-aware-connectivity-bridge.md), [DSU Rollback](../algorithm/dsu-rollback.md)
- `왜 거의 O(1)`인지 증명 관점으로 이어 가려면: [Union-Find Amortized Proof Intuition](../algorithm/union-find-amortized-proof-intuition.md)

## 한 줄 정리

union-find에 `size[root]`와 `components`를 같이 두면, repeated union 중에도 연결 여부와 그룹 메타데이터를 한 번에 관리할 수 있다.
