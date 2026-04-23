# Monotonic Stack Walkthrough

> 한 줄 요약: monotonic stack은 "아직 답이 확정되지 않은 index"를 쌓아 두었다가, 더 큰 값이나 더 낮은 막대가 나타나는 순간 pop하며 답을 확정하는 구조다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
> - [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)
> - [Stack](./basic.md#stack-스택)
> - [Monotone Deque Proof Intuition](../algorithm/monotone-deque-proof-intuition.md)
> - [상각 분석과 복잡도 함정](../algorithm/amortized-analysis-pitfalls.md)
>
> retrieval-anchor-keywords: monotonic stack walkthrough, monotonic stack trace, monotonic stack beginner, next greater element walkthrough, next greater element trace, next greater element step by step, next greater element monotonic stack, histogram largest rectangle walkthrough, histogram largest rectangle trace, largest rectangle in histogram monotonic stack, histogram stack tutorial, stock span monotonic stack, daily temperatures monotonic stack, previous smaller element, next smaller element, monotonic stack vs monotonic deque, stack candidate pruning, stack unresolved index, stack boundary finding, histogram width formula, histogram sentinel zero, 오큰수 추적, 단조 스택 추적, 단조 스택 입문, 다음 큰 수 추적, 히스토그램 최대 직사각형 추적, 히스토그램 스택 풀이, 단조 덱과 단조 스택 차이, 스택으로 경계 찾기

## 빠른 라우팅

- `next greater element`, `daily temperatures`, `stock span`, `오큰수`, `히스토그램 최대 직사각형`처럼 **나중에 온 값이 이전 index의 답을 확정**하는 문제라면 이 문서가 직접 라우트다.
- `sliding window maximum/minimum`, `최근 k개 최대/최소`처럼 **window 만료 처리**가 필요하면 [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)부터 보는 편이 맞다.
- 구현보다 `왜 while pop이 O(n)인가`, `왜 지배당한 후보를 버려도 되나`가 궁금하면 [Monotone Deque Proof Intuition](../algorithm/monotone-deque-proof-intuition.md)과 [상각 분석과 복잡도 함정](../algorithm/amortized-analysis-pitfalls.md)을 같이 보면 된다.

## 먼저 대비: deque와 stack

같은 monotonic 계열이어도 질문의 모양이 다르다.

| 구조 | 제거가 일어나는 이유 | 대표 문제 | 현재 구조가 뜻하는 것 |
|---|---|---|---|
| monotonic deque | window 밖 원소 만료 + 뒤쪽 약한 후보 제거 | sliding window max/min | 현재 window에서 살아남은 후보 |
| monotonic stack | 현재 값이 이전 후보의 답을 확정 | next greater element, histogram | 아직 답이 미정인 index |

즉 deque walkthrough가 `front 만료`를 배우는 문서라면, stack walkthrough는 `pop되는 순간 답이 확정되는 시점`을 배우는 문서다.

## 문제 설정

이 문서에서는 두 문제를 같이 본다.

- Next Greater Element 예제: `nums = [2, 1, 2, 4, 3]`
  - 목표 답: `[4, 2, 4, -1, -1]`
- Largest Rectangle in Histogram 예제: `heights = [2, 1, 5, 6, 2, 3]`
  - 목표 답: `10`
- 표기법: `[(index:value), ...]`
- 표 안에서는 **오른쪽이 stack top**이다.

## 1. Next Greater Element trace

이 문제에서는 **값이 큰 순서로 미해결 index를 쌓아 둔다**.
현재 값이 stack top보다 크면, top index는 지금 처음으로 더 큰 값을 만난 것이므로 답이 확정된다.

| `i` | 새 값 | pop하며 확정한 답 | stack 상태 | answer snapshot |
|---|---|---|---|---|
| `0` | `2` | 없음 | `[(0:2)]` | `[-, -, -, -, -]` |
| `1` | `1` | 없음 | `[(0:2), (1:1)]` | `[-, -, -, -, -]` |
| `2` | `2` | `(1:1) -> 2` | `[(0:2), (2:2)]` | `[-, 2, -, -, -]` |
| `3` | `4` | `(2:2) -> 4`, `(0:2) -> 4` | `[(3:4)]` | `[4, 2, 4, -, -]` |
| `4` | `3` | 없음 | `[(3:4), (4:3)]` | `[4, 2, 4, -, -]` |
| 종료 | - | 남은 `(4:3)`, `(3:4)`는 더 큰 값을 못 만나서 `-1` | `[]` | `[4, 2, 4, -1, -1]` |

초보자가 특히 봐야 할 순간은 `i = 3`, 값 `4`가 들어오는 지점이다.

- `4`는 `2`보다 크므로 index `2`의 답을 `4`로 확정한다.
- 이어서 그 아래 있던 index `0`의 값 `2`보다도 크므로 그것도 같이 확정한다.
- 한 번 pop된 index는 다시 stack에 돌아오지 않는다.

여기서 비교가 `<`인 이유는 문제가 **next greater**이기 때문이다.
만약 `next greater or equal` 문제라면 비교 연산이 달라진다.

## 2. Histogram trace

히스토그램에서는 반대로 **높이가 증가하는 stack**을 유지한다.
현재 막대가 더 낮아지는 순간, stack top 막대는 "오른쪽에서 처음 만난 더 낮은 막대"를 만난 것이므로 최대 폭이 확정된다.

핵심 공식은 하나다.

- `width = rightSmaller - leftSmaller - 1`

여기서

- `rightSmaller`는 지금 보고 있는 index `i`
- `leftSmaller`는 pop 후 새 stack top의 index, 없으면 `-1`

마지막 정리를 위해 `i = 6`, 높이 `0`인 가상 막대를 한 번 더 넣어 flush한다고 생각하자.

| `i` | 높이 | pop하며 계산한 직사각형 | stack 상태 | 현재 max area |
|---|---|---|---|---|
| `0` | `2` | 없음 | `[(0:2)]` | `0` |
| `1` | `1` | `(0:2): width = 1, area = 2` | `[(1:1)]` | `2` |
| `2` | `5` | 없음 | `[(1:1), (2:5)]` | `2` |
| `3` | `6` | 없음 | `[(1:1), (2:5), (3:6)]` | `2` |
| `4` | `2` | `(3:6): width = 1, area = 6`, `(2:5): width = 2, area = 10` | `[(1:1), (4:2)]` | `10` |
| `5` | `3` | 없음 | `[(1:1), (4:2), (5:3)]` | `10` |
| `6` (`flush`) | `0` | `(5:3): width = 1, area = 3`, `(4:2): width = 4, area = 8`, `(1:1): width = 6, area = 6` | `[]` | `10` |

가장 중요한 장면은 `i = 4`, 높이 `2`가 들어오는 순간이다.

- 높이 `6` 막대는 오른쪽에서 처음 더 낮은 막대 `2`를 만났으므로 폭이 `1`로 확정된다.
- 이어서 높이 `5` 막대도 오른쪽 경계가 같은 `i = 4`로 확정된다.
- pop 후 남은 top이 index `1`이므로, 높이 `5` 막대의 왼쪽 경계는 `1`, 오른쪽 경계는 `4`가 되어 폭이 `2`가 된다.

즉 histogram에서는 **pop된 막대가 높이**, 현재 index와 새 top이 **폭**을 제공한다.

## 3. 코드로 옮기면

### Next Greater Element

```java
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;

int[] answer = new int[nums.length];
Arrays.fill(answer, -1);
Deque<Integer> stack = new ArrayDeque<>();

for (int i = 0; i < nums.length; i++) {
    while (!stack.isEmpty() && nums[stack.peek()] < nums[i]) {
        answer[stack.pop()] = nums[i];
    }
    stack.push(i);
}
```

### Largest Rectangle in Histogram

```java
import java.util.ArrayDeque;
import java.util.Deque;

Deque<Integer> stack = new ArrayDeque<>();
int best = 0;

for (int i = 0; i <= heights.length; i++) {
    int current = (i == heights.length) ? 0 : heights[i]; // flush용 sentinel

    while (!stack.isEmpty() && heights[stack.peek()] > current) {
        int mid = stack.pop();
        int leftSmaller = stack.isEmpty() ? -1 : stack.peek();
        int width = i - leftSmaller - 1;
        best = Math.max(best, heights[mid] * width);
    }

    if (i < heights.length) {
        stack.push(i);
    }
}
```

## 4. 입문 체크리스트

- monotonic stack도 값보다 `index`를 저장하는 편이 안전하다.
- Next Greater Element에서는 stack이 `아직 더 큰 값을 못 만난 index`를 뜻한다.
- Histogram에서는 pop된 index가 직사각형의 `높이`를 제공한다.
- Histogram 폭은 `현재 index - pop 후 top - 1`로 읽는다.
- deque와 달리 front 만료는 없다. `window`가 움직이면 stack보다 deque를 먼저 의심해야 한다.
- 비교 연산 `<`, `<=`, `>`, `>=`는 문제 정의와 중복 처리 규칙에 맞춰 정해야 한다.

## 한 줄 정리

monotonic stack의 핵심은 "답이 미정인 index를 쌓아 두고, pop되는 순간 그 index의 답을 확정한다"는 흐름이다.
