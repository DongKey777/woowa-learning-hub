# Monotonic Deque Walkthrough

> 한 줄 요약: monotonic deque는 plain deque에 `만료 제거`와 `뒤쪽 후보 정리` 규칙을 더해, sliding window의 최대/최소를 즉시 읽게 만든다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
> - [Monotonic Deque vs Heap for Window Extrema](./monotonic-deque-vs-heap-for-window-extrema.md)
> - [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)
> - [Sliding Window Patterns](../algorithm/sliding-window-patterns.md)
> - [Monotone Deque Proof Intuition](../algorithm/monotone-deque-proof-intuition.md)
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
>
> retrieval-anchor-keywords: monotonic deque walkthrough, monotonic deque trace, monotonic queue walkthrough, sliding window maximum walkthrough, sliding window minimum walkthrough, sliding window maximum trace, sliding window minimum trace, monotonic deque beginner, plain deque to monotonic deque, deque candidate pruning, deque dominance, deque expiration, deque back pop, recent k maximum trace, recent k minimum trace, max in every window walkthrough, min in every window walkthrough, deque index trace, sliding window extrema tutorial, monotonic deque step by step, monotonic deque vs monotonic stack, monotonic stack contrast, 단조 덱 풀이 순서, 단조 덱 추적, 슬라이딩 윈도우 최대값 추적, 슬라이딩 윈도우 최소값 추적, 일반 덱에서 단조 덱으로, 덱 만료 처리, 덱 뒤에서 pop, 윈도우 극값 입문

## 빠른 라우팅

- `sliding window maximum`, `window minimum`, `최근 k개 중 최대/최소`를 손으로 따라가며 이해하고 싶다면 이 문서가 직접 라우트다.
- `deque와 heap 중 무엇을 골라야 하나`, `lazy deletion heap도 되나`처럼 선택 기준이 먼저 필요하면 [Monotonic Deque vs Heap for Window Extrema](./monotonic-deque-vs-heap-for-window-extrema.md)를 같이 보면 된다.
- `next greater element`, `오큰수`, `histogram largest rectangle`처럼 front 만료 없이 stack top만으로 답을 확정하는 문제라면 [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)로 가야 한다.
- 구현 규칙만 빠르게 정리하고 싶다면 [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)으로 바로 가면 된다.
- `왜 뒤에서 pop해도 되는가`, `왜 O(n)인가`가 궁금하면 [Monotone Deque Proof Intuition](../algorithm/monotone-deque-proof-intuition.md)이 proof companion이다.
- `window sum`, `minimum window substring`, `중복 없는 가장 긴 구간`처럼 deque가 필요한지부터 헷갈리면 [Sliding Window Patterns](../algorithm/sliding-window-patterns.md)에서 먼저 분기한다.

## 문제 설정

예제 배열은 `nums = [1, 3, -1, -3, 5, 3, 6, 7]`, 윈도우 크기는 `k = 3`이다.

- 각 window의 최대값 목표: `[3, 3, 5, 5, 6, 7]`
- 각 window의 최소값 목표: `[-1, -3, -3, -3, 3, 3]`
- 표기법: `[(index:value), ...]`

## 1. plain deque는 왜 부족한가

가장 먼저 떠올리기 쉬운 방법은 "현재 window 원소를 deque에 도착 순서대로 넣자"다.

| step | 들어온 값 | plain deque | 현재 window | front가 뜻하는 것 | 문제 |
|---|---|---|---|---|---|
| `i = 0` | `1` | `[1]` | `[1]` | 가장 오래된 값 | 아직 답을 모른다 |
| `i = 1` | `3` | `[1, 3]` | `[1, 3]` | 가장 오래된 값 `1` | 최대값은 `3`이다 |
| `i = 2` | `-1` | `[1, 3, -1]` | `[1, 3, -1]` | 가장 오래된 값 `1` | 최대값은 여전히 `3`이다 |

plain deque의 front는 `현재 최댓값`이 아니라 `가장 먼저 들어온 값`이다.
즉 deque를 쓴다고 자동으로 sliding window maximum/minimum이 풀리지는 않는다.

## 2. 첫 업그레이드: 값 대신 index를 저장한다

윈도우가 한 칸씩 밀리면 "누가 window 밖으로 나갔는가"를 알아야 한다.
값만 저장하면 중복 값에서 어느 원소가 만료됐는지 헷갈리므로 보통 `index`를 저장한다.

예를 들어 `i = 3`, 새 값 `-3`이 들어오면 window는 `[1..3]`이 된다.

- 직전 deque: `[(0:1), (1:3), (2:-1)]`
- 새 window 시작 index: `i - k + 1 = 1`
- index `0`은 window 밖이므로 front에서 제거
- 새 원소를 back에 추가하면 `[(1:3), (2:-1), (3:-3)]`

이제 `만료된 원소 제거`는 가능해졌다.
하지만 deque는 아직 입력 순서를 거의 그대로 들고 있어서, front가 항상 최대/최소를 보장하지는 못한다.

## 3. 두 번째 업그레이드: 뒤에서 지는 후보를 버린다

최대값용 deque를 예로 들면, 새 값 `x`가 들어올 때 뒤쪽 값 `y`가 `y <= x`라면 `y`는 앞으로 이길 수 없다.

- `x`는 `y`보다 늦게 들어왔는데 값은 더 크다.
- `y`가 살아 있는 동안 같은 window에 `x`도 함께 있다.
- 따라서 이후 어떤 window에서도 `y`가 `x`보다 먼저 최대값이 될 수 없다.

이 논리로 뒤쪽의 약한 후보를 버리면 deque는 plain deque에서 **monotonic deque**로 바뀐다.

- 최대값용 deque: front에서 back으로 갈수록 값이 감소하도록 유지
- 최소값용 deque: front에서 back으로 갈수록 값이 증가하도록 유지

결국 규칙은 네 줄로 정리된다.

1. window 밖 index를 front에서 제거한다.
2. 새 값보다 더 나쁜 뒤쪽 후보를 back에서 제거한다.
3. 새 index를 back에 넣는다.
4. front가 현재 window의 답이다.

## 4. 최대값 trace

최대값을 구할 때는 `nums[dq.back] <= nums[i]`인 동안 back을 제거한다.
아래 표에서 `i = 1` 순간 plain deque의 `[1, 3]`이 monotonic deque의 `[(1:3)]`으로 압축되는 것이 핵심 변화다.

| `i` | 새 값 | 만료 제거 | 뒤쪽 정리 (`<= 현재 값`) | deque 상태 | 출력 |
|---|---|---|---|---|---|
| `0` | `1` | 없음 | 없음 | `[(0:1)]` | `-` |
| `1` | `3` | 없음 | `(0:1)` 제거 | `[(1:3)]` | `-` |
| `2` | `-1` | 없음 | 없음 | `[(1:3), (2:-1)]` | `3` |
| `3` | `-3` | 없음 | 없음 | `[(1:3), (2:-1), (3:-3)]` | `3` |
| `4` | `5` | `(1:3)` 만료 | `(3:-3)`, `(2:-1)` 제거 | `[(4:5)]` | `5` |
| `5` | `3` | 없음 | 없음 | `[(4:5), (5:3)]` | `5` |
| `6` | `6` | 없음 | `(5:3)`, `(4:5)` 제거 | `[(6:6)]` | `6` |
| `7` | `7` | 없음 | `(6:6)` 제거 | `[(7:7)]` | `7` |

관찰 포인트는 두 개다.

- front는 언제나 현재 window의 최대값 후보만 남는다.
- 한 번 뒤에서 제거된 원소는 다시 deque로 돌아오지 않는다.

그래서 출력은 `[3, 3, 5, 5, 6, 7]`이 된다.

## 5. 최소값 trace

최소값은 비교 부호만 뒤집으면 된다.
이번에는 `nums[dq.back] >= nums[i]`인 동안 back을 제거해서, 앞에서 뒤로 값이 증가하도록 유지한다.

| `i` | 새 값 | 만료 제거 | 뒤쪽 정리 (`>= 현재 값`) | deque 상태 | 출력 |
|---|---|---|---|---|---|
| `0` | `1` | 없음 | 없음 | `[(0:1)]` | `-` |
| `1` | `3` | 없음 | 없음 | `[(0:1), (1:3)]` | `-` |
| `2` | `-1` | 없음 | `(1:3)`, `(0:1)` 제거 | `[(2:-1)]` | `-1` |
| `3` | `-3` | 없음 | `(2:-1)` 제거 | `[(3:-3)]` | `-3` |
| `4` | `5` | 없음 | 없음 | `[(3:-3), (4:5)]` | `-3` |
| `5` | `3` | 없음 | `(4:5)` 제거 | `[(3:-3), (5:3)]` | `-3` |
| `6` | `6` | `(3:-3)` 만료 | 없음 | `[(5:3), (6:6)]` | `3` |
| `7` | `7` | 없음 | 없음 | `[(5:3), (6:6), (7:7)]` | `3` |

같은 코드에서 바뀌는 것은 사실상 비교 연산 하나뿐이다.
그래서 최대값 문제를 이해했다면 최소값 문제는 거의 복사해서 생각할 수 있다.

## 6. 코드로 옮기면

```java
while (!dq.isEmpty() && dq.peekFirst() < i - k + 1) {
    dq.pollFirst(); // window 밖 index 제거
}

while (!dq.isEmpty() && nums[dq.peekLast()] <= nums[i]) {
    dq.pollLast(); // 최대값용: 뒤쪽의 약한 후보 제거
}

dq.offerLast(i);

if (i >= k - 1) {
    answer.add(nums[dq.peekFirst()]);
}
```

최소값이면 두 번째 `while`의 비교를 `>=`로 바꾸면 된다.

## 7. 입문 체크리스트

- deque에는 값보다 `index`를 넣는 편이 안전하다.
- front에서 빼는 이유는 `만료`다.
- back에서 빼는 이유는 `지배당한 후보 제거`다.
- 최대값은 `<=`, 최소값은 `>=` 비교를 쓴다.
- front가 답이 되는 이유는 deque가 이미 monotonic invariant를 유지하고 있기 때문이다.

## 한 줄 정리

plain deque가 "들어온 순서"를 기억한다면, monotonic deque는 "앞으로도 답이 될 후보만" 기억한다.
