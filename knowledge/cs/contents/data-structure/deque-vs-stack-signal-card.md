# Deque vs Stack Signal Card

> 한 줄 요약: `window 답을 매번 읽는 문제`면 보통 deque이고, `각 index의 답이 나중에 확정되는 문제`면 보통 stack이다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Deque Basics](./deque-basics.md)
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
> - [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)
> - [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)
> - [Monotonic Deque vs Monotonic Stack Shared-Input Drill](./monotonic-deque-vs-stack-shared-input-drill.md)
> - [Monotonic Structure Router Quiz](./monotonic-structure-router-quiz.md)
>
> retrieval-anchor-keywords: deque vs stack signal card, monotonic deque vs stack signal, window answer read, index answer finalize, deque or stack quick signal, monotonic beginner signal card, sliding window read answer, next greater finalize answer, monotonic deque stack mental model, monotonic structure signal card, window max deque signal, next greater stack signal, deque stack comparison card, monotonic deque vs stack primer, monotonic routing beginner, 단조 덱 스택 신호 카드, window 답 읽기, index 답 확정, 덱 스택 빠른 구분, 단조 구조 입문 카드

## 먼저 잡는 2줄 멘탈 모델

- `window가 한 칸씩 움직일 때 매번 지금 답을 읽는다`면 deque 쪽이다.
- `어느 index의 답이 나중에 나타나는 값 때문에 확정된다`면 stack 쪽이다.

짧게 외우면 이렇다.

| 신호 | 먼저 떠올릴 구조 | 왜 그런가 |
|---|---|---|
| `window answer read` | deque | 매 window마다 front에서 현재 대표값을 읽는다 |
| `index answer finalize` | stack | 현재 값이 예전 index의 답을 확정하면서 pop이 난다 |

## Card A. `window answer read` -> deque

질문: `nums = [7, 1, 4, 2]`, `k = 2`일 때 각 window 최대값은?

window를 만들 때마다 그 순간의 답을 읽는다.

| window | deque가 하는 일 | 읽는 답 |
|---|---|---|
| `[7, 1]` | `7`이 front에 남음 | `7` |
| `[1, 4]` | `4`가 `1`을 밀어내고 front 대표가 됨 | `4` |
| `[4, 2]` | `4`가 아직 window 안이므로 front 유지 | `4` |

결과: `[7, 4, 4]`

핵심 문장:

- deque는 `만료된 index를 front에서 버리고`
- `약한 후보를 back에서 지운 뒤`
- `front를 읽어서 이번 window 답을 낸다`

## Card B. `index answer finalize` -> stack

질문: `nums = [2, 5, 1, 4]`의 Next Greater Element는?

여기서는 window를 읽지 않는다.
대신 나중 값이 나타날 때마다 예전 index의 답이 확정된다.

| 현재 값 | stack에서 확정되는 일 | 새로 확정된 답 |
|---|---|---|
| `2` | 아직 모름, push | 없음 |
| `5` | `2`보다 크므로 `2`의 답 확정 | `ans[0] = 5` |
| `1` | 아직 모름, push | 없음 |
| `4` | `1`보다 크므로 `1`의 답 확정 | `ans[2] = 4` |

마지막에 `5`, `4`는 더 큰 값을 못 만나므로 `-1`이다.
결과: `[5, -1, 4, -1]`

핵심 문장:

- stack은 `미해결 index`를 쌓아 둔다
- `현재 값이 더 크면 pop하면서 그 index의 답을 확정한다`
- 그래서 답을 쓰는 순간이 `window 종료`가 아니라 `pop 순간`이다

## 가장 흔한 혼동

- `둘 다 ArrayDeque로 구현할 수 있는데 왜 다르죠?`
  - 구현 도구는 같아도 읽는 타이밍이 다르다. deque는 `front에서 지금 답을 읽고`, stack은 `pop 순간 예전 답을 쓴다`.
- `sliding window 문제면 무조건 deque인가요?`
  - 합, 빈도, 중복 없는 구간처럼 `extrema`가 아니면 map/two pointers가 더 직접적일 수 있다. [Sliding Window Patterns](../algorithm/sliding-window-patterns.md)로 먼저 분기한다.
- `next/previous가 보이면 무조건 stack인가요?`
  - 초급 분기에서는 거의 맞다. 특히 `각 index 답이 언제 정해지나`가 중심이면 stack부터 의심하면 된다.

## 마지막 한 줄

`매 window마다 읽는 답`이면 deque, `각 index가 나중에 답을 받는 구조`면 stack부터 본다.
