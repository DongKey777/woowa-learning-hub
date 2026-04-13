# Binary Lifting

> 한 줄 요약: Binary Lifting은 부모를 2^k 단위로 미리 점프해, 조상 조회와 경로 계산을 O(log n)으로 줄이는 테크닉이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [그래프 관련 알고리즘](./graph.md)
> - [위상 정렬 패턴](./topological-sort-patterns.md)
> - [Union-Find Deep Dive](../data-structure/union-find-deep-dive.md)

> retrieval-anchor-keywords: binary lifting, ancestor query, LCA, jump table, tree ancestor, kth ancestor, sparse table style dp, tree query, path query, doubling

## 핵심 개념

Binary Lifting은 어떤 노드의 `2^k`번째 조상을 미리 저장해 두는 방식이다.  
이 테이블을 쓰면 다음을 빠르게 구할 수 있다.

- k번째 조상
- 두 노드의 LCA
- 경로 상 조건 검사
- 트리에서 여러 단계 위로 점프하는 질의

backend 관점에서는 계층형 데이터에서 "몇 단계 위의 상위 객체"를 자주 물을 때 유용하다.

- 조직도
- 카테고리 트리
- 권한 상속
- 버전/상태 계층 탐색

## 깊이 들어가기

### 1. 왜 2^k 점프가 가능한가

`1`, `2`, `4`, `8`...처럼 두 배씩 점프를 미리 저장하면, 임의의 거리도 이진수 분해로 표현할 수 있다.

예를 들어 13칸 점프는 `8 + 4 + 1`로 나눌 수 있다.  
즉 `13`을 한 번에 가지 않고 2의 거듭제곱 점프 세 번으로 나눠 갈 수 있다.

### 2. jump table의 구조

보통 `up[k][v]` 형태로 저장한다.

- `up[0][v]`: v의 바로 위 부모
- `up[1][v]`: 2칸 위 부모
- `up[2][v]`: 4칸 위 부모

이렇게 `up[k][v] = up[k-1][ up[k-1][v] ]`로 채운다.

### 3. LCA와의 연결

LCA(Least Common Ancestor)는 두 노드의 공통 조상 중 가장 깊은 노드다.

Binary lifting으로는 다음 식으로 처리한다.

1. 더 깊은 노드를 위로 올려 깊이를 맞춘다.
2. 큰 점프부터 내려가며 서로 다른 조상일 때 같이 올린다.
3. 마지막에 바로 위 부모가 LCA가 된다.

### 4. backend에서 중요한 이유

트리형 데이터는 의외로 많다.

- 댓글/답글 트리
- 조직 구조
- 폴더 구조
- 계층형 카탈로그

이런 곳에서 상위 계층 탐색이 자주 나오면 binary lifting이 매우 편하다.

## 실전 시나리오

### 시나리오 1: k번째 상위 조직 찾기

직원 → 팀장 → 본부장처럼 상위 계층을 여러 번 따라가야 할 때, 매번 부모를 한 칸씩 올라가는 건 비효율적이다.

### 시나리오 2: LCA 기반 경로 질의

두 노드 사이 경로의 공통 구간이나 거리 계산이 필요하면 LCA가 출발점이 된다.

### 시나리오 3: 권한 상속

어떤 리소스가 상위 폴더의 권한을 상속받는 구조라면, 특정 조상까지의 규칙을 빠르게 확인할 수 있다.

### 시나리오 4: 오판

트리가 아니라 일반 그래프에 binary lifting을 그대로 쓰면 안 된다.  
부모가 하나로 정해지는 구조가 전제다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.List;

public class BinaryLifting {
    private final int log;
    private final int[][] up;
    private final int[] depth;
    private final List<List<Integer>> tree;

    public BinaryLifting(List<List<Integer>> tree, int root) {
        this.tree = tree;
        int n = tree.size();
        this.log = 1 + Integer.toBinaryString(Math.max(1, n)).length();
        this.up = new int[log][n];
        this.depth = new int[n];
        dfs(root, root);
    }

    private void dfs(int v, int parent) {
        up[0][v] = parent;
        for (int k = 1; k < log; k++) {
            up[k][v] = up[k - 1][up[k - 1][v]];
        }

        for (int next : tree.get(v)) {
            if (next == parent) continue;
            depth[next] = depth[v] + 1;
            dfs(next, v);
        }
    }

    public int kthAncestor(int v, int k) {
        for (int i = 0; i < log; i++) {
            if (((k >> i) & 1) == 1) {
                v = up[i][v];
            }
        }
        return v;
    }

    public int lca(int a, int b) {
        if (depth[a] < depth[b]) {
            int tmp = a; a = b; b = tmp;
        }

        a = kthAncestor(a, depth[a] - depth[b]);
        if (a == b) return a;

        for (int i = log - 1; i >= 0; i--) {
            if (up[i][a] != up[i][b]) {
                a = up[i][a];
                b = up[i][b];
            }
        }
        return up[0][a];
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Binary Lifting | 질의가 빠르고 구현이 안정적이다 | 전처리와 메모리가 필요하다 | LCA, kth ancestor |
| 부모를 한 칸씩 따라가기 | 구현이 쉽다 | 질의가 느리다 | 데이터가 작을 때 |
| DFS 재탐색 | 직관적이다 | 반복 질의에 비효율적이다 | 한두 번만 조회할 때 |

Binary lifting은 질의가 많을수록 가치가 커진다.

## 꼬리질문

> Q: 왜 2^k 테이블이 필요한가?
> 의도: 이진 분해와 점프 최적화 이해 확인
> 핵심: 큰 이동을 작은 점프들의 조합으로 표현할 수 있기 때문이다.

> Q: LCA가 왜 binary lifting과 잘 맞나?
> 의도: 트리 질의 구조 이해 확인
> 핵심: 두 노드를 같은 높이로 맞추고 동시에 끌어올리기 쉽다.

> Q: 일반 그래프에도 쓸 수 있나?
> 의도: 적용 범위 이해 확인
> 핵심: 아니다. 부모가 하나로 정해지는 트리/루트 구조가 필요하다.

## 한 줄 정리

Binary Lifting은 트리에서 반복적인 조상 조회를 이진 점프로 압축해 빠르게 처리하는 기법이다.
