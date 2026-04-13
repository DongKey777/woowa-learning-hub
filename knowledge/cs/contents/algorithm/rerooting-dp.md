# Rerooting DP

> 한 줄 요약: Rerooting DP는 트리에서 한 번의 DFS 결과를 다시 뿌려 모든 정점을 루트로 보는 답을 효율적으로 계산하는 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Binary Lifting](./binary-lifting.md)
> - [그래프 관련 알고리즘](./graph.md)
> - [Topological DP](./topological-dp.md)

> retrieval-anchor-keywords: rerooting dp, tree dp, subtree dp, all roots, tree reroot, prefix suffix dp on tree, dp propagation, tree distances, centroid-like intuition

## 핵심 개념

Rerooting DP는 "트리의 한 루트에서 구한 값을 모든 루트로 확장"하는 기법이다.

트리 DP에서 흔한 질문은 다음과 같다.

- 각 노드를 루트로 했을 때 정답은 무엇인가
- 모든 정점까지의 거리 합은?
- 서브트리 외부 정보를 어떻게 포함할까?

## 깊이 들어가기

### 1. 왜 rerooting이 필요한가

한 루트에서만 계산하면 그 루트 기준 결과만 나온다.

하지만 문제는 "모든 정점이 루트일 때의 답"을 요구할 수 있다.

### 2. 두 단계

보통 두 번 DFS를 쓴다.

1. 아래에서 위로 서브트리 정보를 모은다.
2. 위에서 아래로 부모 쪽 정보를 다시 내려보낸다.

이 방식으로 각 노드가 루트일 때의 값을 계산한다.

### 3. prefix/suffix 감각

어떤 노드의 자식들 중 한 자식을 제외한 나머지 정보를 빠르게 합치려면 prefix/suffix 누적이 유용하다.

### 4. backend에서의 감각

트리형 조직, 트리형 카탈로그, 계층형 상태 분석에서 자주 등장한다.

## 실전 시나리오

### 시나리오 1: 모든 루트의 거리 합

어떤 노드를 루트로 잡아도 전체 거리 합을 구하고 싶을 때 쓸 수 있다.

### 시나리오 2: 서브트리 외부 정보

자식들만 보아서는 안 되는 문제에서 rerooting이 힘을 발휘한다.

### 시나리오 3: 오판

트리가 아니라 일반 그래프라면 rerooting DP가 바로 적용되지 않는다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.List;

public class RerootingDp {
    private final List<List<Integer>> tree;
    private final int[] down;
    private final int[] up;

    public RerootingDp(List<List<Integer>> tree) {
        this.tree = tree;
        int n = tree.size();
        this.down = new int[n];
        this.up = new int[n];
    }

    public void dfsDown(int v, int p) {
        for (int to : tree.get(v)) {
            if (to == p) continue;
            dfsDown(to, v);
            down[v] = Math.max(down[v], down[to] + 1);
        }
    }

    public void dfsUp(int v, int p) {
        for (int to : tree.get(v)) {
            if (to == p) continue;
            up[to] = Math.max(up[v] + 1, down[v] + 1);
            dfsUp(to, v);
        }
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Rerooting DP | 모든 루트의 답을 효율적으로 구한다 | 두 번의 DFS와 상태 설계가 필요하다 | tree DP all-roots |
| Naive re-run | 직관적이다 | 너무 느리다 | 작은 트리 |
| BFS/DFS 단일 루트 | 구현이 쉽다 | 모든 루트 답을 못 구한다 | 루트 고정 문제 |

## 꼬리질문

> Q: 왜 두 번 DFS가 필요한가?
> 의도: 위/아래 정보 분리를 이해하는지 확인
> 핵심: 서브트리 정보와 부모 방향 정보를 둘 다 써야 하기 때문이다.

> Q: prefix/suffix가 왜 나오나?
> 의도: 자식 하나를 제외한 합성 이해 확인
> 핵심: 각 자식의 기여를 빠르게 합치기 위해서다.

> Q: 어디에 자주 쓰이나?
> 의도: tree DP 패턴 인식 확인
> 핵심: 거리 합, 최장거리, 모든 루트 최적화다.

## 한 줄 정리

Rerooting DP는 트리에서 한 루트의 결과를 모든 루트로 효율적으로 확장하는 두 단계 DFS 기법이다.
