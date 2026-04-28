# Deque vs Stack: 언제 덱이고 언제 스택인가

> 한 줄 요약: `매 window마다 지금 답을 읽는 문제`면 보통 deque이고, `각 index의 답이 나중 값 때문에 확정되는 문제`면 보통 stack이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [Deque Basics](./deque-basics.md)
- [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
- [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)
- [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)
- [Sliding Window Patterns](../algorithm/sliding-window-patterns.md)

retrieval-anchor-keywords: deque vs stack, monotonic deque vs stack, 언제 deque 쓰나요, 언제 stack 쓰나요, sliding window maximum deque, next greater element stack, window 답 읽기, index 답 확정, 처음 deque stack 헷갈림, why deque not stack, what is monotonic deque, beginner monotonic structure

## 왜 처음에 헷갈리나요?

deque와 stack은 둘 다 `값을 넣고 빼는 보조 구조`처럼 보여서 처음엔 같은 문제에 써도 될 것처럼 느껴진다.
하지만 초급자 기준으로는 `답을 언제 읽는가`만 먼저 구분하면 대부분 갈린다.

- `지금 이 window의 답`을 바로 읽어야 하면 deque 쪽이다.
- `예전 index의 답`이 현재 값 때문에 뒤늦게 정해지면 stack 쪽이다.

## 먼저 잡는 2줄 멘탈 모델

- `window가 한 칸씩 움직일 때 매번 지금 답을 읽는다`면 deque 쪽이다.
- `어느 index의 답이 나중에 나타나는 값 때문에 확정된다`면 stack 쪽이다.

짧게 외우면 이렇다.

| 신호 | 먼저 떠올릴 구조 | 왜 그런가 |
|---|---|---|
| `window answer read` | deque | 매 window마다 front에서 현재 대표값을 읽는다 |
| `index answer finalize` | stack | 현재 값이 예전 index의 답을 확정하면서 pop이 난다 |

## 10초 결정표

| 문제에서 보이는 표현 | 먼저 의심할 구조 | 이유 |
|---|---|---|
| `최근 k개 중 최대/최소` | deque | 창이 밀릴 때마다 대표값을 바로 읽어야 한다 |
| `sliding window maximum` | deque | 만료된 후보 제거와 현재 대표 유지가 핵심이다 |
| `next greater element` | stack | 현재 값이 이전 원소의 답을 확정한다 |
| `오른쪽에서 처음 만나는 더 큰 값` | stack | 아직 답이 없는 index를 쌓아 두고 해결한다 |

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

이 문제에서 중요한 건 `2가 들어왔을 때 4가 아직 살아 있는가`이지, `2가 누구의 답을 확정했는가`가 아니다.
그래서 사고방식이 stack보다 deque에 가깝다.

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

이 문제에서 중요한 건 `지금 window의 대표값`이 아니라 `예전 원소 하나하나의 운명`이다.
그래서 deque보다 stack이 더 자연스럽다.

## 가장 흔한 혼동

- `둘 다 ArrayDeque로 구현할 수 있는데 왜 다르죠?`
  - 구현 도구는 같아도 읽는 타이밍이 다르다. deque는 `front에서 지금 답을 읽고`, stack은 `pop 순간 예전 답을 쓴다`.
- `sliding window 문제면 무조건 deque인가요?`
  - 합, 빈도, 중복 없는 구간처럼 `extrema`가 아니면 map/two pointers가 더 직접적일 수 있다. [Sliding Window Patterns](../algorithm/sliding-window-patterns.md)로 먼저 분기한다.
- `next/previous가 보이면 무조건 stack인가요?`
  - 초급 분기에서는 거의 맞다. 특히 `각 index 답이 언제 정해지나`가 중심이면 stack부터 의심하면 된다.

## 다음에 어디로 가면 되나요?

- deque 자체가 아직 낯설면 [Deque Basics](./deque-basics.md)부터 읽는 편이 안전하다.
- `window maximum` 구현 순서를 코드로 보고 싶으면 [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)로 이어 가면 된다.
- `next greater` 류를 더 연습하고 싶으면 [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)로 가면 된다.
- `이게 덱 문제인지 아예 슬라이딩 윈도우가 아닌지`부터 헷갈리면 [Sliding Window Patterns](../algorithm/sliding-window-patterns.md)로 한 단계 뒤로 가서 분기하는 편이 낫다.

## 마지막 한 줄

`매 window마다 읽는 답`이면 deque, `각 index가 나중에 답을 받는 구조`면 stack부터 본다.

## 한 줄 정리

`window 답을 매번 읽는 문제`면 보통 deque이고, `각 index의 답이 나중에 확정되는 문제`면 보통 stack이다.
