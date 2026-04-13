# Bitmask DP

> 한 줄 요약: Bitmask DP는 선택한 원소 집합을 비트로 표현해, 부분집합 상태를 메모이제이션하는 DP 패턴이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [알고리즘 기본](./basic.md)
> - [동적 계획법](./basic.md#동적-계획법-dynamic-programming)
> - [순열, 조합, 부분집합](./basic.md#순열-조합-부분집합)

> retrieval-anchor-keywords: bitmask dp, subset dp, state compression, traveling salesman, assignment problem, set cover, mask transition, profile dp, memoization, held-karp

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

### 3. 대표 문제 유형

- TSP(외판원 순회)
- 작업 배정
- 부분집합 합
- 최소/최대 커버
- 상태별 순열 생성

### 4. backend에서 보는 관점

Bitmask DP는 대부분의 실무 서비스에서 직접 쓰기보다, 제한된 개수의 옵션을 조합하는 최적화 문제에 가깝다.

- 소규모 feature flag 조합
- 제한된 리소스 배치
- 적은 수의 작업 순서 최적화

## 실전 시나리오

### 시나리오 1: 작업 배정

작업자 수가 적고 각 작업의 비용이 명확할 때, 누가 어떤 작업을 맡을지 전부 탐색하는 대신 상태를 압축해서 최적 배정을 찾을 수 있다.

### 시나리오 2: TSP류 순회

배송 경로, 검사 순서, 라운드 트립 최소화처럼 "모든 지점을 한 번씩 방문"해야 하는 문제에 잘 맞는다.

### 시나리오 3: 부분집합 제약

허용 가능한 옵션 조합을 체크해야 하는 문제에서, 비트마스크로 빠르게 집합 조건을 검사한다.

### 시나리오 4: 오판

원소 수가 20~25개를 넘어가면 상태 수가 폭증한다.  
이때는 bitmask DP가 아니라 다른 근사나 분기 한정, greedy, ILP를 봐야 할 수 있다.

## 코드로 보기

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
| 완전탐색 | 구현이 단순하다 | 경우의 수가 너무 많다 | 데이터가 매우 작을 때 |
| Greedy | 빠르고 직관적이다 | 최적해 보장이 없다 | 근사로 충분할 때 |

Bitmask DP는 "작은 n에 대한 정교한 최적화"를 맡는다.

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

## 한 줄 정리

Bitmask DP는 부분집합을 비트로 압축해 작은 상태 공간에서 최적 조합을 찾는 동적 계획법이다.
