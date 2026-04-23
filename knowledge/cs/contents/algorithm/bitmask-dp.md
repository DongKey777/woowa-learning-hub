# Bitmask DP

> 한 줄 요약: Bitmask DP는 선택한 원소 집합을 비트로 표현해, 부분집합 상태를 메모이제이션하는 DP 패턴이다.
>
> 문서 역할: 이 문서는 algorithm 카테고리 안에서 **subset-state optimization / small-n exact assignment / TSP-style ordering** 감각을 잡는 intuition deep dive다.
>
> retrieval-anchor-keywords: bitmask dp, bitmask assignment, subset dp, subset state optimization, subset-state optimization, state compression, state compressed dp, small n dp, small-n assignment, small-n exact assignment, exact assignment small n, assignment dp, assignment bitmask, assignment exact search, one worker one job small n, one task per worker small n, worker job assignment dp, worker-task assignment dp, minimum assignment small n, minimum cost assignment small n, cost matrix dp, cost matrix small n, square cost matrix small n, weighted assignment dp, popcount assignment, n <= 15 assignment, n <= 20 assignment, traveling salesman, tsp dp, tsp style routing, visit all nodes once, hamiltonian path dp, hamiltonian cycle dp, held-karp, set cover, mask transition, subset transition, profile dp, memoization, mask memoization, hungarian vs bitmask dp, assignment dp vs flow, flow vs bitmask assignment, subset permutation optimization, 순회 dp, 상태 압축 dp, 비트마스크 dp, 부분집합 상태 최적화, 작은 n 배정, 작은 n 최소 비용 배정, 비용 행렬 dp, 정사각 비용 행렬 작은 n, 배정 dp, 작업 배정 dp, 순서 의존 최적화

**난이도: 🔴 Advanced**

> 관련 문서:
> - [알고리즘 기본](./basic.md)
> - [동적 계획법](./basic.md#동적-계획법-dynamic-programming)
> - [순열, 조합, 부분집합](./basic.md#순열-조합-부분집합)
> - [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md)
> - [Network Flow Intuition](./network-flow-intuition.md)
> - [Min-Cost Max-Flow Intuition](./min-cost-max-flow-intuition.md)

## 이 문서 다음에 보면 좋은 문서

- `정사각 cost matrix의 exact 1:1 최소 비용 배정`인데 `dp[mask]`, `N <= 20` 같은 small-`n` 신호가 약하면 [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md)이 더 직접적이다.
- `최대 몇 쌍을 만들 수 있는가`, `capacity가 있는 배정인가`가 핵심이면 [Network Flow Intuition](./network-flow-intuition.md)이 더 직접적이다.
- `공급/수요`, `부분 배정`, `capacity > 1`, `transportation`까지 열리면 [Min-Cost Max-Flow Intuition](./min-cost-max-flow-intuition.md) 쪽이 먼저다.
- DP 기본 감각부터 다시 잡고 싶다면 [동적 계획법](./basic.md#동적-계획법-dynamic-programming)으로 돌아가면 된다.

---

## 이런 표현으로 들어와도 이 문서 후보다

| 질문 표현 / 검색 alias | 먼저 볼 문서 | 왜 여기로 오면 되는가 |
|---|---|---|
| `small-n assignment`, `assignment dp`, `작은 n 배정`, `n <= 20 assignment` | 이 문서 | 사람/일감 집합이 작고 `dp[mask]` 형태의 exact search가 자연스럽다 |
| `cost matrix small n`, `one worker one job n <= 20`, `popcount assignment` | 이 문서 | 현재 몇 번째 사람을 배정 중인지 `popcount(mask)`로 읽는 전형적인 small-`n` assignment 신호다 |
| `visit all nodes once`, `traveling salesman`, `held-karp`, `순회 순서 최적화` | 이 문서 | pair matching이 아니라 방문 집합과 마지막 위치가 상태다 |
| `subset-state optimization`, `state compression`, `부분집합 상태 최적화` | 이 문서 | residual capacity보다 부분집합 전이 자체가 문제의 본문이다 |
| `optimal assignment`, `linear assignment`, `one worker one job` | [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md) | exact 1:1 cost matrix 구조가 중심이지만 small-`n` 상태 힌트는 약한 경우다 |
| `maximum matching`, `최대 몇 쌍 배정`, `capacity assignment` | [Network Flow Intuition](./network-flow-intuition.md) | subset enumeration보다 cardinality/capacity model이 본질이다 |
| `weighted matching`, `transportation`, `capacity > 1 assignment`, `supply-demand allocation` | [Min-Cost Max-Flow Intuition](./min-cost-max-flow-intuition.md) | exact 1:1 subset-state보다 비용과 용량 일반화가 본질이다 |

---

## 작은 n 배정 라우터

| 문제 신호 | 먼저 볼 문서 | 구분 포인트 |
|---|---|---|
| `dp[mask]`, `popcount(mask)`, `이미 고른 집합`이 자연스럽게 상태가 되나 | 이 문서 | 문제 핵심이 subset-state memory다 |
| `worker -> job` 1:1 배정인데 `N <= 20`, `cost matrix small n`, `one worker one job small n` 힌트가 있나 | 이 문서 | 현재 worker를 `popcount(mask)`로 복원할 수 있어 `dp[mask]`가 직접적인 모델이 된다 |
| `배정`처럼 보이지만 사실은 `이전 선택 -> 다음 비용`으로 이어지는 순서 최적화인가 | 이 문서 | `dp[mask][last]`가 필요한 TSP/Held-Karp류다 |
| 정사각 `cost matrix`, `optimal assignment`, `linear assignment` 자체가 본문인데 small-`n` 상태 힌트는 약한가 | [Hungarian Algorithm Intuition](./hungarian-algorithm-intuition.md) | subset-state보다 matrix 1:1 구조가 먼저 읽힌다 |
| `최대 몇 명 배정`, `최대 몇 쌍`, `가능한 배정 수`가 목적이고 용량 제약이 있나 | [Network Flow Intuition](./network-flow-intuition.md) | pair relation과 capacity가 본질이다 |
| `최소 비용 배정`, `weighted matching`, `cost matrix`인데 공급/수요/부분 배정/용량 일반화가 있나 | [Min-Cost Max-Flow Intuition](./min-cost-max-flow-intuition.md) | pair cost와 capacity를 함께 다루는 flow model이 더 일반적이다 |

질문에 `assignment`가 들어가도 바로 flow로 가면 안 된다. 먼저 `mask`, `popcount`, `N <= 20`, exact 1:1 cost matrix 같은 신호를 보고 bitmask DP 또는 Hungarian으로 먼저 분기한 뒤, 그다음에 flow 일반화를 확인한다.

## 핵심 개념

Bitmask DP는 각 원소를 bit 하나로 나타내서, "어떤 원소를 이미 선택했는가"를 상태로 저장하는 방식이다.

예:

- `mask = 0101`이면 0번과 2번 원소를 선택
- 상태가 `2^n`개라서 작은 `n`에 적합

이 패턴은 조합 폭발을 막는 대신, 상태 공간을 정교하게 제한하는 전략이다.

실무 감각으로는 "선택 가능한 대상 수가 적지만 경우의 수가 많을 때" 쓰는 압축형 탐색이다.

## 깊이 들어가기

### 1. 왜 비트가 좋은가

비트는 집합을 표현하기 편하다.

- 포함 여부 체크가 빠르다
- 추가/삭제가 비트 연산으로 간단하다
- 부분집합 순회가 자연스럽다

`mask & (1 << i)`로 i번째 원소 포함 여부를 확인할 수 있다.

### 2. 상태와 전이

Bitmask DP의 핵심은 보통 `dp[mask][last]` 같은 형태다.

- `mask`: 어떤 원소들을 이미 썼는가
- `last`: 마지막으로 선택한 원소는 무엇인가

전이는 "다음에 어떤 원소를 붙일 수 있는가"를 본다.

작은 `assignment problem`에서는 `dp[mask]`만으로도 자주 푼다.
이때 `popcount(mask)`를 "지금 몇 번째 worker를 배정 중인가"로 해석하면
현재까지 선택한 job 집합만으로 최소 비용을 누적할 수 있다.

### 3. 작은 n exact assignment 상태식

전형적인 small-`n` assignment 상태식은 다음처럼 읽는다.

- `worker = popcount(mask)`
- `dp[mask]`: 앞의 `worker`명에게 `mask`에 들어 있는 job들을 배정했을 때의 최소 비용
- 아직 선택하지 않은 `job` 하나를 붙이며 전이

`dp[mask | (1 << job)] = min(dp[mask | (1 << job)], dp[mask] + cost[worker][job])`

즉 핵심은 "관계 그래프에 유량을 보낸다"가 아니라 "이미 고른 집합을 상태로 기억한다"는 데 있다.
복잡도는 구현에 따라 보통 `O(N * 2^N)` 또는 `O(N^2 * 2^N)` 정도로 읽는다.

### 4. 대표 문제 유형

- TSP(외판원 순회)
- 작은 `n`의 최소 비용 배정
- 부분집합 합
- 최소/최대 커버
- 상태별 순열 생성

### 5. backend에서 보는 관점

Bitmask DP는 대부분의 실무 서비스에서 직접 쓰기보다, 제한된 개수의 옵션을 조합하는 최적화 문제에 가깝다.

- 소규모 feature flag 조합
- 제한된 리소스 배치
- 적은 수의 작업 순서 최적화

## 실전 시나리오

### 시나리오 1: 작업 배정

작업자 수가 적고 각 작업의 비용이 명확할 때, 누가 어떤 작업을 맡을지 전부 탐색하는 대신 상태를 압축해서 최적 배정을 찾을 수 있다.
특히 `cost[i][j]`가 있고 `N`이 작다면 `dp[mask]`로 "이미 선택한 job 집합"만 저장하는 패턴이 자주 나온다.

### 시나리오 2: TSP류 순회

배송 경로, 검사 순서, 라운드 트립 최소화처럼 "모든 지점을 한 번씩 방문"해야 하는 문제에 잘 맞는다.
이 경우 핵심은 "누구와 누구를 짝지을까"가 아니라 "어떤 집합을 방문했고 마지막 위치가 어디인가"다.

### 시나리오 3: 부분집합 제약

허용 가능한 옵션 조합을 체크해야 하는 문제에서, 비트마스크로 빠르게 집합 조건을 검사한다.

### 시나리오 4: 오판

원소 수가 20~25개를 넘어가면 상태 수가 폭증한다.  
이때는 bitmask DP가 아니라 다른 근사나 분기 한정, greedy, ILP를 봐야 할 수 있다.
또 목표가 `최대 배정 수`나 `capacity가 있는 matching`이라면 bitmask보다 flow가 더 자연스럽다.

## 코드로 보기

### 작은 n 1:1 배정

```java
import java.util.Arrays;

public class SmallAssignmentBitmask {
    private static final int INF = 1_000_000_000;

    public int solve(int[][] cost) {
        int n = cost.length;
        int[] dp = new int[1 << n];
        Arrays.fill(dp, INF);
        dp[0] = 0;

        for (int mask = 0; mask < (1 << n); mask++) {
            int worker = Integer.bitCount(mask);
            if (worker == n) continue;

            for (int job = 0; job < n; job++) {
                if ((mask & (1 << job)) != 0) continue;
                int next = mask | (1 << job);
                dp[next] = Math.min(dp[next], dp[mask] + cost[worker][job]);
            }
        }

        return dp[(1 << n) - 1];
    }
}
```

여기서는 "다음 worker가 누구인가"를 별도 차원으로 들고 가지 않고 `Integer.bitCount(mask)`로 복원한다.
이 패턴이 바로 `small-n assignment`, `assignment dp`, `cost matrix small n` 질의를 bitmask DP로 연결하는 핵심 신호다.

### TSP / ordering

```java
import java.util.Arrays;

public class TravelingSalesmanBitmask {
    private static final int INF = 1_000_000_000;
    private int[][] dist;
    private int[][] memo;
    private int n;

    public int solve(int[][] dist) {
        this.dist = dist;
        this.n = dist.length;
        this.memo = new int[1 << n][n];
        for (int[] row : memo) Arrays.fill(row, -1);
        return tsp(1, 0);
    }

    private int tsp(int mask, int last) {
        if (mask == (1 << n) - 1) {
            return dist[last][0] == 0 ? INF : dist[last][0];
        }
        if (memo[mask][last] != -1) {
            return memo[mask][last];
        }

        int best = INF;
        for (int next = 0; next < n; next++) {
            if ((mask & (1 << next)) != 0) continue;
            if (dist[last][next] == 0) continue;
            best = Math.min(best, dist[last][next] + tsp(mask | (1 << next), next));
        }
        return memo[mask][last] = best;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Bitmask DP | 상태 표현이 깔끔하고 강력하다 | 상태 수가 `2^n`으로 급격히 늘어난다 | n이 작고 조합 최적화가 필요할 때 |
| Hungarian | 정사각 cost matrix의 exact 1:1 배정에 특화돼 있다 | `dp[mask]` 같은 subset-state 설명력은 약하다 | optimal assignment, linear assignment |
| Network Flow | 최대 배정 수와 capacity 제약을 모델링하기 쉽다 | 순서 의존 상태나 `dp[mask][last]`는 직접 표현하기 어렵다 | maximum matching, max throughput |
| Min-Cost Max-Flow | 배정 비용과 capacity 일반화를 함께 다룬다 | 구현이 복잡하고 작은 순열형 문제에는 과할 수 있다 | weighted matching, general assignment |
| 완전탐색 | 구현이 단순하다 | 경우의 수가 너무 많다 | 데이터가 매우 작을 때 |
| Greedy | 빠르고 직관적이다 | 최적해 보장이 없다 | 근사로 충분할 때 |

Bitmask DP는 "작은 n에 대한 정교한 최적화"를 맡는다. 특히 `mask/popcount`가 자연스럽게 들리면 flow보다 먼저 확인하는 편이 정확하다.

## 꼬리질문

> Q: 왜 상태 수가 `2^n`이 되나?
> 의도: 부분집합 표현의 본질 이해 확인
> 핵심: 각 원소가 선택/비선택 두 가지 상태를 가지기 때문이다.

> Q: `last`까지 상태에 넣는 이유는?
> 의도: 경로 의존성 이해 확인
> 핵심: 다음 전이가 마지막 선택 원소에 따라 달라질 수 있기 때문이다.

> Q: 언제 쓰면 안 되나?
> 의도: 적용 범위 인지 확인
> 핵심: 원소 수가 조금만 커져도 상태 폭발이 생긴다.

> Q: 작업 배정은 언제 flow가 더 낫나?
> 의도: assignment DP와 flow의 경계 이해 확인
> 핵심: 최대 배정 수나 일반 capacity/cost 제약이 본질이면 flow, 작은 `n` subset-state exact search면 bitmask DP가 더 직접적이다.

> Q: 같은 최소 비용 배정인데 언제 Hungarian이 더 낫나?
> 의도: bitmask DP와 Hungarian의 경계 이해 확인
> 핵심: 정사각 cost matrix의 exact 1:1 구조가 중심이고 `N <= 20`, `mask`, `popcount` 같은 subset-state 힌트가 약하면 Hungarian이 더 직접적이다.

## 한 줄 정리

Bitmask DP는 부분집합을 비트로 압축해 작은 상태 공간에서 최적 조합을 찾는 동적 계획법이다.
