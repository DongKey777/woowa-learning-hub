# Monotonic Duplicate Rule Micro-Drill

> 한 줄 요약: monotonic deque/stack에서 `<` vs `<=`, `>` vs `>=`는 "같은 값이 나오면 이전 값을 남길지, 새 값을 남길지"를 정하는 규칙이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: monotonic duplicate rule micro drill basics, monotonic duplicate rule micro drill beginner, monotonic duplicate rule micro drill intro, data structure basics, beginner data structure, 처음 배우는데 monotonic duplicate rule micro drill, monotonic duplicate rule micro drill 입문, monotonic duplicate rule micro drill 기초, what is monotonic duplicate rule micro drill, how to monotonic duplicate rule micro drill
> 관련 문서:
> - [Monotonic Operator Boundary Cheat Sheet](./monotonic-operator-boundary-cheat-sheet.md)
> - [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)
> - [Sliding Window Duplicate Extrema Index Drill](./sliding-window-duplicate-extrema-index-drill.md)
> - [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)
> - [Monotonic Deque vs Monotonic Stack Shared-Input Drill](./monotonic-deque-vs-stack-shared-input-drill.md)
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
>
> retrieval-anchor-keywords: monotonic duplicate rule drill, monotonic duplicate micro drill, monotonic duplicate tie handling, monotonic deque duplicate values, monotonic stack duplicate values, less than vs less than equal monotonic drill, greater than vs greater than equal monotonic drill, monotonic duplicate operator boundary, monotonic equal handling, leftmost max duplicate deque, rightmost max duplicate deque, next greater duplicate rule, previous smaller duplicate rule, strict or equal duplicate monotonic, monotonic beginners duplicate values, 단조 중복 규칙 드릴, 단조 중복값 연산자, 단조 덱 중복값 처리, 단조 스택 중복값 처리, 단조 < <= 차이, 단조 > >= 차이, 중복값 tie handling, 왼쪽 최대 index, 오른쪽 최대 index

## 먼저 잡는 한 문장

같은 값이 나오면 둘 중 하나만 먼저 정하면 된다.

- 이전 값을 남기고 싶다 -> strict 비교를 더 자주 쓴다. (`<`, `>`)
- 새 값을 남기고 싶다 -> equal까지 같이 pop하는 비교를 더 자주 쓴다. (`<=`, `>=`)

deque와 stack의 모양은 달라도, `equal을 남길지 지울지`를 먼저 정한다는 점은 같다.

## 30초 규칙표

| 구조 | 질문 | 보통 고르는 pop 조건 | 중복에서 남는 쪽 |
|---|---|---|---|
| max deque | "같은 최대값이면 가장 오른쪽 index를 대표로 써도 됨" | `backValue <= cur` | 새 값 = 오른쪽 대표 |
| max deque | "같은 최대값이면 가장 왼쪽 index를 대표로 유지" | `backValue < cur` | 이전 값 = 왼쪽 대표 |
| next greater stack | "greater만 허용" | `topValue < cur` | 같은 값은 남겨 둠 |
| next greater or equal stack | "greater or equal 허용" | `topValue <= cur` | 같은 값도 이번에 해결 |
| previous smaller stack | "smaller만 허용" | `topValue >= cur` | 같은 값 제거 |
| previous smaller or equal stack | "smaller or equal 허용" | `topValue > cur` | 같은 값 유지 |

## Drill 1. Deque: `<`와 `<=`가 바꾸는 것

문제: `nums = [5, 5, 4]`, `k = 2`

질문 A. 각 window 최대값의 `값`만 구하라.

- 답은 둘 다 `[5, 5]`다.
- 그래서 초보자는 `<`와 `<=`가 같아 보이기 쉽다.

질문 B. 각 window 최대값의 `가장 왼쪽 index`를 구하라.

이제는 연산자가 정답을 바꾼다.

| pop 조건 | `i = 1`에서 무슨 일이 생기나 | 첫 window 대표 index |
|---|---|---|
| `while backValue < cur` | 기존 `5(index 0)` 유지 | `0` |
| `while backValue <= cur` | 기존 `5(index 0)` pop, 새 `5(index 1)`만 남음 | `1` |

기억할 말:

- `값만` 물으면 두 구현이 모두 통과할 수 있다.
- `어느 index를 대표로 볼지`가 붙는 순간 `<`와 `<=`는 다른 규칙이다.
- `새 값 유지`라고 적어도 되고, beginner 관점에서는 `오른쪽 대표 유지`라고 적어도 같은 말이다.

## Drill 2. Stack: `>`와 `>=`가 바꾸는 것

문제: `nums = [2, 2]`

질문 A. `Previous Smaller (strict)`를 구하라.

- 정답: `[-1, -1]`
- 같은 값 `2`는 smaller가 아니다.

| pop 조건 | 두 번째 `2`를 볼 때 stack top | 결과 |
|---|---|---|
| `while topValue > cur` | 첫 번째 `2`가 남아 있음 | 오답 가능 (`2`를 smaller처럼 사용) |
| `while topValue >= cur` | 첫 번째 `2` 제거 | 정답 유지 (`-1`) |

질문 B. `Previous Smaller or Equal`을 구하라.

- 이제는 반대로 같은 값도 답 후보다.
- 그래서 `while topValue > cur`처럼 equal을 남기는 쪽이 자연스럽다.

## 두 문제를 한 규칙으로 묶기

| 먼저 적을 문장 | 연산자 선택 감각 |
|---|---|
| "같은 값은 답 후보로 남겨 둔다" | strict 비교 쪽 (`<`, `>`)을 먼저 의심 |
| "같은 값은 새 값이 대체한다" | equal까지 pop하는 쪽 (`<=`, `>=`)을 먼저 의심 |
| "strictly greater / strictly smaller" | equal은 답이 아니므로 제거가 필요한지 확인 |
| "or equal / 이상 / 이하" | equal도 답이므로 남겨야 하는지 확인 |

## 자주 헷갈리는 포인트

- `deque는 <=, stack은 >=처럼 외우면 되나요?`
  - 아니다. 구조보다 문제 문장이 먼저다. `strict인지`, `leftmost tie-break인지`를 먼저 본다.
- `왜 deque 예시는 < / <=이고 stack 예시는 > / >=인가요?`
  - deque 예시는 최대값을 유지하는 방향, stack 예시는 smaller를 찾는 방향이라 비교 부호가 반대로 보일 뿐이다.
- `중복값이 없으면 아무거나 써도 되나요?`
  - 그 입력에서는 결과가 같을 수 있다. 하지만 실전 문제는 중복이 자주 섞이므로 규칙을 문장으로 먼저 고정하는 편이 안전하다.

## 마지막 체크

문제를 읽고 시작하기 전에 딱 두 줄만 적으면 된다.

1. 같은 값이 나오면 `이전 값 유지`인지 `새 값 대체`인지
2. 답이 `strict`인지 `or equal`인지

이 두 줄이 정해지면 `<`/`<=`, `>`/`>=`는 거의 자동으로 따라온다.

## 한 줄 정리

monotonic deque/stack에서 `<` vs `<=`, `>` vs `>=`는 "같은 값이 나오면 이전 값을 남길지, 새 값을 남길지"를 정하는 규칙이다.
