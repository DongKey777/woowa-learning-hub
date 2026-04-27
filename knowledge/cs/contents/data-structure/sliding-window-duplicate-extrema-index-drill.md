# Sliding Window Duplicate Extrema Index Drill

> 한 줄 요약: sliding-window max/min에서 duplicate가 나오면 값은 같아도 `대표 index`는 달라질 수 있으므로, 먼저 `왼쪽 tie-break`인지 `오른쪽 tie-break`인지부터 정한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)
> - [Monotonic Duplicate Rule Micro-Drill](./monotonic-duplicate-rule-micro-drill.md)
> - [Monotonic Operator Boundary Cheat Sheet](./monotonic-operator-boundary-cheat-sheet.md)
> - [Monotonic Deque vs Heap for Window Extrema](./monotonic-deque-vs-heap-for-window-extrema.md)
>
> retrieval-anchor-keywords: sliding window duplicate extrema index drill, sliding window duplicate tie break, sliding window max duplicate index, sliding window min duplicate index, monotonic deque duplicate index tie break, leftmost max index deque, rightmost max index deque, leftmost min index deque, rightmost min index deque, duplicate extrema representative index, sliding window max index tie break, sliding window min index tie break, recent k max duplicate index, recent k min duplicate index, window extrema duplicate primer, monotonic deque duplicate extrema drill, monotonic deque leftmost index, monotonic deque rightmost index, 슬라이딩 윈도우 중복 최대값 인덱스, 슬라이딩 윈도우 중복 최소값 인덱스, 단조 덱 중복 인덱스 tie break, 왼쪽 최대 인덱스, 오른쪽 최대 인덱스, 왼쪽 최소 인덱스, 오른쪽 최소 인덱스, 윈도우 극값 중복 인덱스

## 먼저 잡는 멘탈 모델

중복 최대값이나 최소값이 여러 개 있으면, deque는 그중 **누가 대표 index인지**만 정하면 된다.

- 왼쪽 대표를 원하면: 같은 값은 지우지 않는다.
- 오른쪽 대표를 원하면: 같은 값도 새 값이 들어올 때 지운다.

값 자체는 같아 보여도, `어느 index가 front에 남는가`는 다를 수 있다.

## 20초 결정표

| 목표 | max deque 뒤쪽 pop | min deque 뒤쪽 pop | 남는 대표 |
|---|---|---|---|
| 값만 맞으면 됨 | `<=` | `>=` | 오른쪽 새 값 |
| 가장 왼쪽 index 유지 | `<` | `>` | 왼쪽 옛 값 |

이 표를 먼저 고정하고 trace를 보면 헷갈림이 줄어든다.

## Drill 1. Window Max: 같은 최대값이면 누구 index가 답인가

문제: `nums = [5, 5, 4]`, `k = 2`

window는 두 개다.

- `[0..1]`의 최대값은 `5`
- `[1..2]`의 최대값도 `5`

초보자가 놓치기 쉬운 점은 "값은 둘 다 5인데, 첫 window 대표 index는 다를 수 있다"는 점이다.

| max deque pop 조건 | `i = 1`에서 처리 | 첫 window 대표 index |
|---|---|---|
| `while nums[dq.back] < nums[i]` | 기존 `5(index 0)` 유지 | `0` |
| `while nums[dq.back] <= nums[i]` | 기존 `5(index 0)` 제거 | `1` |

한 줄 해석:

- `<`는 같은 최대값을 둘 다 살려 두므로 왼쪽 index가 먼저 남는다.
- `<=`는 새 equal 값이 옛 equal 값을 대체하므로 오른쪽 index가 대표가 된다.

## Drill 2. Window Min: 같은 최소값이면 누구 index가 답인가

문제: `nums = [2, 2, 3]`, `k = 2`

window는 두 개다.

- `[0..1]`의 최소값은 `2`
- `[1..2]`의 최소값도 `2`

최소값도 원리는 똑같고 부호만 반대다.

| min deque pop 조건 | `i = 1`에서 처리 | 첫 window 대표 index |
|---|---|---|
| `while nums[dq.back] > nums[i]` | 기존 `2(index 0)` 유지 | `0` |
| `while nums[dq.back] >= nums[i]` | 기존 `2(index 0)` 제거 | `1` |

한 줄 해석:

- `>`는 같은 최소값을 남겨서 왼쪽 index가 대표다.
- `>=`는 새 equal 값이 대체해서 오른쪽 index가 대표다.

## 값은 같아도 index는 다르다

같은 입력이라도 질문이 다르면 정답 규칙도 달라진다.

| 질문 | max 예시 `nums=[5,5,4], k=2` | min 예시 `nums=[2,2,3], k=2` |
|---|---|---|
| 각 window의 값만 구하라 | 둘 다 값은 맞을 수 있다 | 둘 다 값은 맞을 수 있다 |
| 각 window extrema의 가장 왼쪽 index를 구하라 | strict 비교가 필요하다 | strict 비교가 필요하다 |
| 각 window extrema의 가장 오른쪽 index를 구하라 | equal까지 pop한다 | equal까지 pop한다 |

즉 `값만 맞는 구현`과 `index tie-break까지 맞는 구현`은 같은 것이 아니다.

## 자주 하는 착각

- `sliding-window maximum은 무조건 <= 인가요?`
  - 값만 반환하는 전형 문제에서는 자주 그렇다. 하지만 `가장 왼쪽 최대 index`를 요구하면 `<`가 더 자연스럽다.
- `minimum도 그냥 같은 규칙인가요?`
  - 방향만 반대다. `max`의 `< / <=`가 `min`에서는 `> / >=`로 바뀐다.
- `왜 value가 아니라 index를 저장하나요?`
  - window 만료와 tie-break를 동시에 추적하려면 index가 필요하다.

## 마지막 체크

문제를 읽고 시작하기 전에 이 두 줄만 먼저 적으면 된다.

1. 중복 extrema에서 `왼쪽 index`를 남길지 `오른쪽 index`를 남길지
2. 그래서 equal을 `남길지` `pop할지`

이 두 줄이 정해지면 sliding-window max/min의 duplicate tie-break는 거의 끝난다.
