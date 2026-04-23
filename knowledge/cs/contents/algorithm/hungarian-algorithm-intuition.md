# Hungarian Algorithm Intuition

> 한 줄 요약: Hungarian 알고리즘은 정사각 cost matrix에서 모든 행과 열을 정확히 한 번씩 쓰는 1:1 최소 비용 배정을 푸는 특화 알고리즘이다.
>
> 문서 역할: 이 문서는 algorithm 카테고리 안에서 **optimal assignment / linear assignment / 1:1 weighted matching**을 Hungarian 관점으로 읽는 intuition deep dive다.
>
> retrieval-anchor-keywords: hungarian algorithm, hungarian, kuhn munkres, kuhn-munkres, linear assignment, linear sum assignment, assignment problem, optimal assignment, optimal task assignment, optimal worker assignment, assignment matrix, cost matrix assignment, square cost matrix, balanced assignment, minimum assignment, minimum cost assignment, minimum weight perfect matching, minimum cost perfect matching, weighted bipartite matching, one-to-one weighted matching, one to one weighted matching, 1:1 weighted matching, exact assignment, one worker one job, one task per worker, optimal job assignment, assignment matrix optimization, hungarian vs min-cost max-flow, hungarian vs bitmask dp, 헝가리안 알고리즘, 최적 배정, 최소 비용 배정, 비용 행렬 배정, 1대1 가중치 매칭, 할당 문제

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Min-Cost Max-Flow Intuition](./min-cost-max-flow-intuition.md)
> - [Bitmask DP](./bitmask-dp.md)
> - [Network Flow Intuition](./network-flow-intuition.md)

## 이 문서 다음에 보면 좋은 문서

- `공급량/수요량`, `edge capacity`, `부분 배정`, `transportation`처럼 일반 네트워크 제약까지 열리면 [Min-Cost Max-Flow Intuition](./min-cost-max-flow-intuition.md)이 더 맞다.
- `N`이 작고 `dp[mask]` 기반 exact search가 더 자연스럽다면 [Bitmask DP](./bitmask-dp.md)가 구현상 더 직접적일 수 있다.
- 비용 없이 `최대 몇 쌍`만 묻는다면 [Network Flow Intuition](./network-flow-intuition.md)으로 가는 편이 정확하다.

---

## 이런 표현으로 들어와도 이 문서 후보다

| 질문 표현 / 검색 alias | 먼저 볼 문서 | 왜 여기로 오면 되는가 |
|---|---|---|
| `hungarian algorithm`, `kuhn-munkres`, `linear assignment` | 이 문서 | cost matrix 기반 1:1 minimum assignment를 직접 가리키는 표현이다 |
| `optimal assignment`, `optimal worker-task assignment`, `최적 배정` | 이 문서 | 모든 사람/작업을 정확히 한 번씩 배정하며 총 비용 최소화가 목적이다 |
| `minimum weight perfect matching`, `1:1 weighted matching`, `one worker one job` | 이 문서 | bipartite graph 관점으로는 exact weighted matching이고, matrix 관점으로는 Hungarian 후보다 |
| `weighted matching`인데 공급/수요/부분 배정/edge capacity까지 풀어야 하나 | [Min-Cost Max-Flow Intuition](./min-cost-max-flow-intuition.md) | Hungarian보다 일반화된 flow 모델이 필요하다 |
| `small-n assignment`, `assignment dp`, `dp[mask]` | [Bitmask DP](./bitmask-dp.md) | 상태 압축 exact search가 문제의 본문이면 DP가 더 직접적이다 |
| `maximum matching`, `최대 몇 쌍`, `배정 수 최대화` | [Network Flow Intuition](./network-flow-intuition.md) | 비용이 없고 cardinality만 중요하면 일반 flow/matching으로 충분하다 |

---

## 핵심 개념

Hungarian 알고리즘은 "누가 어떤 일을 맡을지"가 cost matrix로 주어질 때,
각 행과 각 열을 정확히 한 번씩 고르면서 총합 비용을 최소화하는 데 특화돼 있다.

즉 문제 모양이 다음과 같을 때 강하다.

- worker 수와 job 수가 같거나 dummy를 넣어 같은 크기로 맞출 수 있다
- 각 worker는 정확히 하나의 job만 맡는다
- 각 job도 정확히 하나의 worker만 받는다
- 목표는 총 비용 최소화다

이 모양은 `assignment problem`, `linear assignment`, `optimal assignment`,
`minimum weight perfect matching` 같은 이름으로도 자주 들어온다.

## Hungarian이 잘 맞는 문제 신호

| 문제 신호 | 먼저 볼 문서 | 구분 포인트 |
|---|---|---|
| 정사각 `cost[i][j]` matrix가 있고 exact 1:1 배정이 핵심인가 | 이 문서 | Hungarian이 matrix 구조를 직접 사용한다 |
| worker/job 수는 비슷하지만 `capacity > 1`, `공급량`, `수요량`, `부분 배정`이 있나 | [Min-Cost Max-Flow Intuition](./min-cost-max-flow-intuition.md) | 1:1 matrix보다 일반화된 flow 제약이다 |
| `dp[mask]`, `popcount(mask)`, `N <= 20` 같은 small-`n` 힌트가 먼저 보이나 | [Bitmask DP](./bitmask-dp.md) | subset-state exact search가 더 짧고 구현도 단순할 수 있다 |
| 비용이 없고 `최대 몇 쌍`을 만들 수 있는지만 중요하나 | [Network Flow Intuition](./network-flow-intuition.md) | matching cardinality 문제다 |

## weighted matching과 Hungarian의 브리지

질문에 `weighted matching`이 보여도 바로 min-cost max-flow로 점프할 필요는 없다.
먼저 "이게 정확히 1:1 cost matrix assignment인가?"를 확인하면 된다.

- **예**: worker 4명, task 4개, `cost[i][j]` 표가 주어짐
- **아니오**: 한 worker가 여러 task를 맡을 수 있음, 공급량/수요량이 다름, 부분 배정 허용

앞의 경우는 Hungarian이 자연스럽고,
뒤의 경우는 [Min-Cost Max-Flow Intuition](./min-cost-max-flow-intuition.md)이 더 일반적이다.

즉 `1:1 weighted matching`은 Hungarian과 min-cost max-flow 사이의 브리지 표현이다.

## 깊이 들어가기

### 1. 왜 generic graph보다 Hungarian이 먼저인가

generic graph 문서에서는 shortest path / MST / flow처럼 큰 갈래만 보이기 쉽다.
하지만 `optimal assignment`, `cost matrix`, `one worker one job`이 보이면
문제 핵심은 path나 cut이 아니라 exact 1:1 assignment다.

이때 Hungarian은 그래프 전체를 일반화해서 보기보다
행/열 제약이 분명한 matrix 구조를 바로 활용한다.

### 2. 직관적으로 무엇을 하는가

Hungarian은 각 행과 열에서 공통으로 빼도 되는 값을 정리해
"비용이 0이 되는 선택 후보"를 드러내고,
그 0들만으로 완전한 1:1 배정이 가능한지 점점 다듬는다.

직관은 다음과 같다.

- 각 행/열에서 공통으로 줄일 수 있는 비용은 미리 정리한다
- "상대적으로 싼 후보"를 0으로 드러낸다
- 그 0들만으로 모든 행/열을 덮는 완전 배정이 되는지 본다
- 부족하면 matrix를 다시 조정해 더 나은 0 후보를 만든다

즉 Hungarian은 모든 조합을 다 뒤지는 대신
"최적 배정이 숨어 있는 cost matrix 구조"를 계속 정돈한다.

### 3. min-cost max-flow와의 경계

Hungarian은 매우 강력하지만 적용 범위가 분명하다.

- `1:1`, `balanced`, `cost matrix`이면 Hungarian이 특화돼 있다
- `capacity > 1`, `공급/수요`, `부분 배정`, `transportation network`면 min-cost max-flow가 더 유연하다

그래서 `optimal assignment`라는 표현 하나만으로 끝내지 말고,
문제에 network 제약이 있는지 확인해야 한다.

### 4. bitmask DP와의 경계

문제가 같은 1:1 배정이어도 `N`이 매우 작다면 `dp[mask]`가 더 구현하기 쉬울 수 있다.
즉 "어떤 알고리즘이 더 일반적인가"와 "어떤 구현이 지금 더 적합한가"는 다른 질문이다.

## 실전 시나리오

### 시나리오 1: 면접관-면접 슬롯 배정

면접관 5명과 슬롯 5개가 있고 선호도/비용 표가 주어졌다면
이건 전형적인 `optimal assignment`다.
한 사람당 하나, 슬롯당 하나라는 1:1 구조가 명확하다.

### 시나리오 2: 서버-작업 배정

서버마다 작업 처리 비용이 다르고,
각 서버가 정확히 하나의 작업만 맡는다면 Hungarian 후보다.
하지만 서버 하나가 여러 작업을 처리할 수 있다면 Hungarian보다 min-cost max-flow 쪽으로 넘어간다.

### 시나리오 3: 오판

`assignment problem`이라는 말만 보고 generic graph나 max flow부터 시작하면
비용 최적화와 1:1 구조가 흐려진다.
반대로 모든 weighted assignment를 Hungarian으로 몰면
capacity와 supply/demand가 있는 문제를 과도하게 단순화하게 된다.

## 코드로 보기

```java
public class HungarianAssignment {
    public int solve(int[][] cost) {
        int n = cost.length;
        // 설명용 스케치:
        // 1. 행/열 기준으로 비용을 정규화해 0 후보를 만든다.
        // 2. 0들로 완전한 1:1 배정이 가능한지 본다.
        // 3. 부족하면 matrix를 다시 조정해 새 0 후보를 만든다.
        // 4. 모든 행/열이 정확히 한 번씩 선택되면 총 비용을 복원한다.
        return 0;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Hungarian | 정사각 cost matrix의 exact 1:1 minimum assignment에 특화돼 있다 | 일반 네트워크/다중 수요/capacity로는 바로 확장되지 않는다 | optimal assignment, linear assignment |
| Min-Cost Max-Flow | 비용과 capacity, 공급/수요를 함께 다룰 수 있다 | 구현과 모델이 더 무겁다 | generalized weighted assignment, transportation |
| Bitmask DP | 작은 `N`에서 구현이 짧고 직관적일 수 있다 | `N`이 커지면 상태 수가 폭발한다 | small-`n` assignment |
| Max Flow | 비용이 없을 때 단순하고 강하다 | weighted / minimum-cost objective를 다루지 못한다 | maximum matching, assignment count maximization |

## 꼬리질문

> Q: Hungarian 알고리즘은 어떤 문제 모양에서 가장 잘 맞나요?
> 의도: 문제 형태 인식 확인
> 핵심: 정사각 cost matrix에서 행/열을 정확히 한 번씩 쓰는 1:1 minimum assignment다.

> Q: `optimal assignment`와 `weighted matching`은 어떻게 연결되나요?
> 의도: 용어 브리지 이해 확인
> 핵심: bipartite graph로 보면 minimum weight perfect matching이고, matrix로 보면 Hungarian assignment다.

> Q: Hungarian 대신 min-cost max-flow를 써야 하는 신호는 무엇인가요?
> 의도: 경계 판단 확인
> 핵심: capacity, supply/demand, 부분 배정, transportation 제약이 보이면 flow 쪽이 더 일반적이다.

## 한 줄 정리

Hungarian 알고리즘은 `optimal assignment`, `linear assignment`, `1:1 weighted matching`처럼 exact cost matrix 배정을 푸는 특화 알고리즘이다.
