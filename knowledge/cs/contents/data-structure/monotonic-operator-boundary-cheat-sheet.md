# Monotonic Operator Boundary Cheat Sheet

> 한 줄 요약: monotonic deque/stack에서 `중복 값`이 있을 때 `<`/`<=`, `>`/`>=`는 "누가 남는가(오래된 값 vs 새 값)"를 정하는 경계다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
> - [Monotonic Duplicate Rule Micro-Drill](./monotonic-duplicate-rule-micro-drill.md)
> - [Monotonic Strict-vs-Equal Translation Card](./monotonic-strict-vs-equal-translation-card.md)
> - [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)
> - [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)
> - [Monotonic Deque vs Monotonic Stack Shared-Input Drill](./monotonic-deque-vs-stack-shared-input-drill.md)
>
> retrieval-anchor-keywords: monotonic operator boundary, monotonic deque operator, monotonic stack operator, monotonic duplicates, less than vs less than equal monotonic, greater than vs greater than equal monotonic, monotonic deque duplicate tie break, monotonic stack duplicate tie break, monotonic duplicate rule drill, monotonic duplicate micro drill, deque leftmost max index, deque rightmost max index, deque rightmost min index, first greater monotonic, first greater or equal monotonic, value only monotonic deque, value only vs index tie break deque, monotonic deque value only, monotonic deque leftmost tie break, previous smaller strict duplicate bug, operator boundary cheat sheet, monotonic operator decision table, monotonic deque stack decision table, monotonic operator mapping table, problem sentence to operator monotonic, strict vs or equal monotonic mapping, 단조 연산자 경계, 단조 덱 중복 연산자, 단조 스택 중복 연산자, 단조 덱 < <= 차이, 단조 스택 > >= 차이, 값만 구할 때 단조 덱, 인덱스 tie break 단조 덱, 중복값 tie break, 단조 연산자 결정표, 문제 문장 연산자 매핑

## 먼저 잡는 감각

연산자는 "정답이 최대/최소인가?"보다 한 단계 더 구체적으로,
"같은 값이 둘이면 옛 값을 남길지 새 값을 남길지"를 결정한다.

- `<` / `>`: 같은 값은 둘 다 남기기 쉽다.
- `<=` / `>=`: 같은 값은 새 값이 옛 값을 밀어내기 쉽다.

## one-screen 결정표: 문제 문장을 연산자로 바로 옮기기

먼저 구조를 고르고, 그다음 `strict`인지 `같은 값 포함`인지 읽으면 된다.

| 문제 문장에서 먼저 잡을 말 | 구조 | 보통 보는 답 | pop/비교 기준 | 한 줄 해석 |
|---|---|---|---|---|
| `최근 k개`, `window`, `구간 최대/최소` | deque | 현재 window의 대표값 | max면 뒤에서 `<=`, min이면 뒤에서 `>=` | 값만 맞으면 새 동점이 옛 동점을 밀어내도 된다 |
| `최근 k개`인데 `가장 왼쪽 index`까지 중요 | deque | window 대표 index | max면 뒤에서 `<`, min이면 뒤에서 `>` | 동점이면 먼저 나온 값을 남긴다 |
| `next greater`, `next smaller` | stack | 현재 원소의 다음 답 | greater면 `top < cur`, smaller면 `top > cur`일 때 답 확정 | strict라서 같은 값은 답이 아니다 |
| `previous strictly smaller`, `previous strictly greater` | stack | 현재 원소의 이전 답 | smaller면 push 전 `top >= cur` pop, greater면 push 전 `top <= cur` pop | equal을 지워야 strict 이전 답이 남는다 |
| `greater or equal`, `smaller or equal` | stack | 현재 원소의 다음/이전 답 | equal도 답으로 인정되게 반대편 strict만 pop | 문장에 `or equal`, `이상`, `이하`가 보이면 equal을 남겨야 한다 |

### 3단계 번역 습관

1. `window / recent k`가 보이면 deque, `next / previous`가 보이면 stack부터 의심한다.
2. `strictly`, `초과`, `미만`이면 같은 값을 제거하는 쪽으로 읽는다.
3. `가장 왼쪽 index`, `먼저 나온 값`이 보이면 deque 동점 pop을 strict(`<`, `>`)로 둔다.

## 가장 흔한 헷갈림 먼저 끊기

| 헷갈리는 문장 | 바로 번역 |
|---|---|
| `최대값`만 구하라 | deque에서 보통 `<=` |
| `최대값의 가장 왼쪽 index`를 구하라 | deque에서 `<` |
| `previous strictly smaller` | stack에서 `>=`를 pop |
| `next greater or equal` | stack에서 `top < cur`만 pop하고 같은 값은 남김 |

## deque 먼저 보는 10초 미니 표

초보자가 가장 자주 묻는 것은 사실 이 한 줄이다.
"**값만 구하나, 아니면 같은 값일 때 대표 index도 중요하나?**"

| 목표 | max deque 뒤쪽 pop | min deque 뒤쪽 pop | 동점에서 남는 쪽 |
|---|---|---|---|
| 값만 구함 | `<=` | `>=` | 새 값(오른쪽) |
| 가장 왼쪽 index tie-break | `<` | `>` | 옛 값(왼쪽) |

먼저 이 표로 분기한 뒤, stack의 strict/or-equal 규칙은 아래 표로 내려가면 된다.

## 같은 입력으로 바로 보는 deque 중복 예시

입력: `nums = [4, 4, 2]`, `k = 2`

첫 window `[0..1]`에서 최대값은 둘 다 `4`다.
그래서 `strict`와 `or-equal` 차이는 "값"보다 "**어느 index를 대표로 남기느냐**"에서 드러난다.

| 질문 | pop 조건 | 첫 window 결과 |
|---|---|---|
| 최대값의 값만 구하라 | `while backValue <= cur` 또는 `while backValue < cur` | 둘 다 `4` |
| 최대값의 가장 왼쪽 index를 구하라 | `while backValue < cur` | `0` |
| 최대값의 가장 오른쪽 index를 구하라 | `while backValue <= cur` | `1` |

한 줄 해석:

- `<`는 같은 값이 와도 예전 값을 남겨서 `strict` 쪽처럼 보인다.
- `<=`는 같은 값도 밀어내서 새 값을 남기므로 `or-equal` 감각에 더 가깝다.
- deque에서 `strict/or-equal`을 헷갈리면, 먼저 "왼쪽 대표 vs 오른쪽 대표"로 번역해 보면 빨라진다.

## 초간단 선택표 (중복 기준)

| 상황 | 보통 쓰는 pop 조건 | 중복에서 남는 쪽 | 기억할 말 |
|---|---|---|---|
| max deque (window 최대값) | `while backValue <= cur` | 새 값(오른쪽) | "새 동점이 옛 동점을 대체" |
| max deque + 왼쪽 index tie-break 필요 | `while backValue < cur` | 옛 값(왼쪽) | "동점이면 먼저 나온 값 유지" |
| min deque (window 최소값) | `while backValue >= cur` | 새 값(오른쪽) | "새 동점이 옛 동점을 대체" |
| min deque + 왼쪽 index tie-break 필요 | `while backValue > cur` | 옛 값(왼쪽) | "동점이면 먼저 나온 값 유지" |
| Next Greater (strict) stack | `while topValue < cur` | 같은 값은 미해결로 남음 | "strictly greater만 답" |
| Previous Smaller (strict) stack | `while topValue >= cur` | 같은 값 제거 | "equal은 smaller가 아님" |

## 실패 케이스 1: `<` vs `<=` (deque, 동점 index 정책)

문제 요구가 "window 최대값의 **가장 왼쪽 index**를 반환"인데,
max deque를 `<=`로 구현하면 틀릴 수 있다.

- 입력: `nums = [5, 5, 4]`, `k = 2`
- 첫 window `[0..1]`의 최대값 index 정답: `0` (왼쪽 tie-break)

`<=`를 쓰면 `i=1`에서 기존 `5(index 0)`이 pop되고 `5(index 1)`만 남는다.
그래서 index `1`을 내보내 오답이 된다.

정리:
- 왼쪽 tie-break가 필요하면 `max deque`에서 동점 pop을 `<`로 둔다.
- 값만 필요하면 `<=`/`<` 둘 다 가능하지만, tie-break 요구가 생기면 연산자가 정답을 바꾼다.

### 같은 규칙의 최소값 버전도 바로 보기

- 입력: `nums = [2, 2, 3]`, `k = 2`
- 첫 window `[0..1]`의 최소값 index 정답:
  - 값만 구하면 `2`만 맞으면 된다.
  - 가장 왼쪽 index까지 묻는다면 `0`이어야 한다.

| pop 조건 | `i = 1`에서 무슨 일이 생기나 | 첫 window 대표 index |
|---|---|---|
| `while backValue > cur` | 기존 `2(index 0)` 유지 | `0` |
| `while backValue >= cur` | 기존 `2(index 0)` pop, 새 `2(index 1)`만 남음 | `1` |

즉 `min deque`도 똑같다.

- 값만 필요하면 보통 `>=`
- 왼쪽 index tie-break가 중요하면 `>`

## 실패 케이스 2: `>` vs `>=` (stack, strict 경계)

문제 요구가 "previous **strictly smaller**"인데,
stack pop을 `>`로만 두면 중복에서 틀린다.

- 입력: `[2, 2]`
- strict previous smaller 정답: `[-1, -1]`

`while top > cur`만 쓰면 첫 번째 `2`가 stack에 남아,
두 번째 `2`의 이전 원소를 `2`로 잘못 기록하기 쉽다(같은 값은 smaller가 아님).

정리:
- strict smaller/greater 경계 문제에서 equal을 배제해야 하면 `>=`/`<=` pop이 필요하다.
- "strict인지, or-equal인지"를 먼저 문장으로 확정하고 연산자를 고른다.

## 한 줄 체크리스트

- 중복이 있을 때 "왼쪽 우선 vs 오른쪽 우선" tie-break를 먼저 적는다.
- deque는 먼저 "값만 구함 vs 대표 index도 의미 있음"으로 분기하면 빠르다.
- strict 조건이면 equal을 stack/deque에 남길지 제거할지 먼저 결정한다.
- 연산자 선택은 성능이 아니라 정답 정의(경계, tie-break)와 1:1로 연결된다.

## 자주 생기는 오해 한 줄 정리

- `deque에서도 strict/or-equal이라고 말해도 되나요?`
  - 가능하다. 다만 초급자에게는 `왼쪽 대표 유지` vs `새 대표로 교체`로 번역하는 편이 더 바로 읽힌다.
- `값만 맞으면 < 와 <= 는 같은 구현인가요?`
  - 출력 값만 보면 같을 수 있다. 하지만 walkthrough를 지나 index tie-break 문제로 가는 순간 바로 갈린다.
