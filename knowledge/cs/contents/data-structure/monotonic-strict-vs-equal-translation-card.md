# Monotonic Strict-vs-Equal Translation Card

> 한 줄 요약: monotonic 문제에서 문장 속 `first greater`, `greater or equal`, `leftmost max`, `rightmost min`은 거의 바로 pop 조건으로 번역된다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Monotonic Operator Boundary Cheat Sheet](./monotonic-operator-boundary-cheat-sheet.md)
> - [Monotonic Duplicate Rule Micro-Drill](./monotonic-duplicate-rule-micro-drill.md)
> - [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)
> - [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
>
> retrieval-anchor-keywords: monotonic strict vs equal translation card, monotonic phrase to pop condition, first greater monotonic, first greater or equal monotonic, first smaller monotonic, first smaller or equal monotonic, leftmost max monotonic deque, rightmost max monotonic deque, leftmost min monotonic deque, rightmost min monotonic deque, monotonic pop condition card, monotonic operator translation, problem phrase to operator monotonic, monotonic beginner card, next greater strict vs equal, deque tie break pop condition, stack strict or equal pop condition, 단조 strict equal 카드, 단조 문장 연산자 번역, first greater pop 조건, greater or equal pop 조건, 왼쪽 최대 index, 오른쪽 최소 index, 단조 덱 tie break, 단조 스택 연산자 카드

## 먼저 잡는 2줄

- `first/next/previous ...`처럼 **누군가의 답을 찾는 문장**이면 보통 `stack`이다.
- `leftmost/rightmost max/min`처럼 **window 대표를 고르는 문장**이면 보통 `deque`다.

그다음에는 `strict인가`, `equal도 포함하나`, `동점이면 왼쪽을 남기나 오른쪽을 남기나`만 읽으면 된다.

## 문장 -> pop 조건 바로 번역

| 문제 문장 | 구조 | 보통 쓰는 pop 조건 | 짧은 해석 |
|---|---|---|---|
| `first greater` | stack | `while topValue < cur` | strict greater를 만났을 때만 해결 |
| `first greater or equal` | stack | `while topValue <= cur` | 같은 값도 이번에 해결 |
| `first smaller` | stack | `while topValue > cur` | strict smaller를 만났을 때만 해결 |
| `first smaller or equal` | stack | `while topValue >= cur` | 같은 값도 smaller 쪽으로 인정 |
| `leftmost max` | deque | `while backValue < cur` | 같은 최대값이면 예전 값 유지 |
| `rightmost max` | deque | `while backValue <= cur` | 같은 최대값이면 새 값으로 교체 |
| `leftmost min` | deque | `while backValue > cur` | 같은 최소값이면 예전 값 유지 |
| `rightmost min` | deque | `while backValue >= cur` | 같은 최소값이면 새 값으로 교체 |

## 한 번에 외우는 미니 규칙

| 읽은 표현 | 바로 떠올릴 말 |
|---|---|
| `strict`, `first greater`, `first smaller` | equal은 아직 답이 아니다 |
| `or equal`, `이상`, `이하` | equal도 이번에 답이 될 수 있다 |
| `leftmost` | 동점이면 예전 값을 남긴다 |
| `rightmost` | 동점이면 새 값을 남긴다 |

## 10초 예시

같은 값 두 개만 있어도 차이가 바로 보인다.

| 입력/질문 | pop 조건 | 결과 |
|---|---|---|
| `nums = [4, 4]`, `leftmost max` | `while backValue < cur` | 대표 index `0` |
| `nums = [2, 2]`, `rightmost min` | `while backValue >= cur` | 대표 index `1` |
| `nums = [5, 5]`, `first greater` | `while topValue < cur` | 첫 `5`는 아직 미해결 |
| `nums = [5, 5]`, `first greater or equal` | `while topValue <= cur` | 첫 `5`는 두 번째 `5`에서 해결 |

## 가장 흔한 오해

- `max면 항상 <= 인가요?`
  - 아니다. `rightmost max`일 때는 `<=`가 자연스럽지만, `leftmost max`면 `<`가 맞다.
- `greater면 무조건 < 를 pop하나요?`
  - `greater or equal`이면 `<=`로 바뀐다. 핵심은 `equal도 답인지`다.
- `값만 구할 때도 tie-break를 신경 써야 하나요?`
  - 지금 출력값만 보면 차이가 안 날 수 있다. 하지만 index 요구나 duplicate 테스트가 붙으면 바로 갈린다.

## 마지막 체크

문제를 읽고 아래 한 줄만 먼저 적으면 된다.

`equal을 답으로 인정하나?`, `동점이면 왼쪽을 남기나 오른쪽을 남기나?`

이 한 줄이 정해지면 pop 조건은 거의 표에서 바로 나온다.
