---
schema_version: 3
title: Monotonic Deque vs Monotonic Stack Shared-Input Drill
concept_id: data-structure/monotonic-deque-vs-stack-shared-input-drill
canonical: false
category: data-structure
difficulty: beginner
doc_role: drill
level: beginner
language: ko
source_priority: 88
mission_ids:
- missions/lotto
review_feedback_tags:
- monotonic-structure-drill
- deque-vs-stack-practice
- window-vs-index-answer
aliases:
- monotonic deque vs stack drill
- shared input monotonic structures
- window answer read drill
- index answer finalize drill
- sliding window max vs next greater
- monotonic beginner practice
- 단조 덱 스택 공통 입력
symptoms:
- 같은 배열을 보고 sliding window maximum이면 deque, next greater element이면 stack이라는 질문 차이를 손으로 구분하지 못한다
- window expiration과 answer finalization을 같은 pop 동작으로만 보고 output timing이 달라지는 이유를 놓친다
- strict/or-equal 연산자 번역과 duplicate 처리 기준을 실제 dry run 전에 정하지 않아 한 글자 오답을 만든다
intents:
- drill
- troubleshooting
prerequisites:
- data-structure/deque-vs-stack-signal-card
- data-structure/monotonic-structure-router-quiz
next_docs:
- data-structure/monotonic-duplicate-rule-micro-drill
- data-structure/monotonic-deque-walkthrough
- data-structure/monotonic-stack-walkthrough
- data-structure/monotonic-operator-boundary-cheat-sheet
linked_paths:
- contents/data-structure/monotonic-structure-router-quiz.md
- contents/data-structure/deque-vs-stack-signal-card.md
- contents/data-structure/monotonic-duplicate-rule-micro-drill.md
- contents/data-structure/monotonic-deque-walkthrough.md
- contents/data-structure/monotonic-stack-walkthrough.md
- contents/data-structure/monotonic-queue-and-stack.md
- contents/data-structure/monotonic-operator-boundary-cheat-sheet.md
- contents/algorithm/sliding-window-patterns.md
- contents/algorithm/monotone-deque-proof-intuition.md
confusable_with:
- data-structure/deque-vs-stack-signal-card
- data-structure/monotonic-structure-router-quiz
- data-structure/monotonic-deque-walkthrough
- data-structure/monotonic-stack-walkthrough
forbidden_neighbors: []
expected_queries:
- 같은 입력으로 monotonic deque와 monotonic stack을 비교하는 연습을 하고 싶어
- sliding window maximum과 next greater element는 왜 각각 deque와 stack이야?
- window 만료와 index 답 확정의 차이를 dry run으로 보여줘
- strict greater와 greater or equal 연산자 선택을 단조 구조에서 어떻게 점검해?
- 단조 덱 스택 공통 입력 드릴로 처음부터 손체크하는 방법을 알려줘
contextual_chunk_prefix: |
  이 문서는 같은 input을 sliding window extrema와 next greater element로 풀어
  monotonic deque와 monotonic stack의 차이를 연습하는 drill이다. window
  expiration, answer finalization, strict/or-equal operator, duplicate handling
  dry run을 다룬다.
---
# Monotonic Deque vs Monotonic Stack Shared-Input Drill

> 한 줄 요약: 같은 입력을 두 번 풀어 보면, deque는 `window 극값`, stack은 `미해결 index 답 확정` 문제라는 차이가 바로 보인다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: monotonic deque vs stack shared input drill basics, monotonic deque vs stack shared input drill beginner, monotonic deque vs stack shared input drill intro, data structure basics, beginner data structure, 처음 배우는데 monotonic deque vs stack shared input drill, monotonic deque vs stack shared input drill 입문, monotonic deque vs stack shared input drill 기초, what is monotonic deque vs stack shared input drill, how to monotonic deque vs stack shared input drill
> 관련 문서:
> - [Monotonic Structure Router Quiz](./monotonic-structure-router-quiz.md) - 먼저 `deque / stack / neither`를 10초 분기하고 내려오고 싶을 때
> - [Deque vs Stack Signal Card](./deque-vs-stack-signal-card.md)
> - [Monotonic Duplicate Rule Micro-Drill](./monotonic-duplicate-rule-micro-drill.md)
> - [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)
> - [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
> - [Monotonic Operator Boundary Cheat Sheet](./monotonic-operator-boundary-cheat-sheet.md)
> - [Sliding Window Patterns](../algorithm/sliding-window-patterns.md)
> - [Monotone Deque Proof Intuition](../algorithm/monotone-deque-proof-intuition.md) (증명 companion)
>
> retrieval-anchor-keywords: monotonic deque vs stack drill, shared input monotonic structures, monotonic deque stack decision, monotonic deque or stack, deque vs stack signal card, window answer read, index answer finalize, sliding window max vs next greater, sliding window minimum vs previous smaller element, window expiration vs answer finalization, deque decision drill, stack decision drill, monotonic beginner practice, monotonic primer, previous smaller element stack trace, monotonic deque minimum drill, monotonic strict vs or-equal checklist, monotonic operator translation, strictly greater or equal monotonic, monotonic operator boundary beginner, monotonic duplicate rule drill, monotonic duplicate micro drill, monotonic dry run checklist, shared input dry run, monotonic hand trace checklist, monotonic 4 step checklist, monotonic beginner dry run, duplicate shared input monotonic, monotonic duplicate add-on, monotonic less than vs less than equal, monotonic greater than vs greater than equal, monotonic duplicate shared example, router quiz aftercare, monotonic reading order, monotonic router to drill bridge, 단조 덱 단조 스택 비교, 단조 덱 스택 공통 입력, 단조 구조 입문 드릴, 덱 스택 선택 기준, 윈도우 만료와 답 확정 차이, 슬라이딩 윈도우 최대값 오큰수 비교, 슬라이딩 윈도우 최소값 이전 작은 값 비교, strict or equal 번역, 단조 연산자 체크리스트, 단조 구조 드라이런 체크리스트, 공통 입력 손체크, 4단계 드라이런, 단조 중복값 공통 예제, 단조 < <= 차이, 단조 > >= 차이, 라우터 퀴즈 다음 드릴, 단조 독서 순서 브리지, window 답 읽기, index 답 확정

## 이 문서를 여는 가장 자연스러운 순간

먼저 [Monotonic Structure Router Quiz](./monotonic-structure-router-quiz.md)에서 `deque / stack / neither`를 고른다.
그다음 이 문서로 내려와 같은 입력 하나로 `deque는 window를 읽는 문제`, `stack은 index 답을 확정하는 문제`를 손으로 비교한다.

## 먼저 잡는 mental model

같은 배열을 보더라도 질문이 다르면 구조가 달라진다.

- `monotonic deque`: 최근 `k`칸 window에서 지금 당장 최대/최소를 읽고 싶을 때
- `monotonic stack`: 각 index의 답이 "언제 확정되는지"를 추적하고 싶을 때

한 줄로 외우면:

- `window 만료가 있으면 deque`, `만료 없이 pop 순간 답이 정해지면 stack`

## 연산자 실수 방지: strict/or-equal 3줄 점검표

문제를 읽자마자 아래 3줄을 먼저 적고 시작하면, `>`/`>=` 한 글자 실수가 많이 줄어든다.

| 점검 3줄 | 지금 바로 확인할 것 |
|---|---|
| 1. 문제 문장 번역 | `strictly`면 strict, `or equal / 이상·이하 / 크거나 같은`이면 or-equal로 먼저 한국어 한 줄로 적는다. |
| 2. equal 처리 정책 | 중복값에서 `같은 값은 답 후보가 아니다`인지, `같은 값도 후보`인지 먼저 정한다. |
| 3. while 조건 확정 | 위 1~2를 반영해 pop 연산자를 고른다. (`>=` vs `>`, `<=` vs `<`) |

### 문제 문장을 연산자로 바로 번역하는 초간단 표

| 문제 문장 | 먼저 적을 번역 | 흔한 pop 조건 |
|---|---|---|
| next **greater** | "같은 값은 greater가 아니다" | `while top < cur` |
| next **greater or equal** | "같은 값도 이번에 해결 가능" | `while top <= cur` |
| previous **smaller** | "같은 값은 smaller가 아니다" | `while top >= cur` |
| previous **smaller or equal** | "같은 값도 왼쪽 답이 될 수 있다" | `while top > cur` |

짧은 예시 하나:

- `Previous Smaller (strict)`에서 `nums = [2, 2]`면 두 번째 값의 답은 `-1`이다.
- 그래서 stack pop은 `while top >= cur`가 맞고, `while top > cur`면 첫 번째 `2`가 남아 오답이 된다.
- 반대로 `Previous Smaller or Equal`이면 두 번째 값의 답이 `2`가 될 수 있으니 `while top > cur` 쪽이 맞다.

## 공통 입력

배열은 둘 다 `nums = [4, 2, 1, 3, 5]`를 쓴다.

- Drill A (deque): `k = 3`일 때 각 window의 최대값
- Drill B (stack): 각 index의 Next Greater Element

## 같은 입력 바로 아래에 두는 4단계 dry-run 체크리스트

표를 길게 따라가기 전에, 종이에 아래 4줄만 먼저 적고 시작하면 된다.

| 단계 | 손으로 체크할 한 줄 |
|---|---|
| 1. 질문 종류 | `window를 매번 읽는가?` 그러면 deque. `각 index 답을 언젠가 확정하는가?` 그러면 stack. |
| 2. 제거 이유 | deque면 `front 만료`, `back 후보 정리` 두 종류를 나눠 적는다. stack이면 `현재 값이 top 답을 확정할 때만 pop`이라고 적는다. |
| 3. 답 쓰는 시점 | deque는 `i >= k-1`부터 front를 읽는다. stack은 `pop 순간` 또는 `정리 후 top 확인`에 답을 쓴다. |
| 4. 이번 칸 한 줄 메모 | 각 칸마다 `만료?`, `뒤/위 제거?`, `push`, `답 기록?` 네 칸만 체크한다. |

초급자용으로 더 짧게 줄이면 아래 한 줄이다.

| 구조 | 매 칸에서 손으로 볼 것 |
|---|---|
| deque | `만료 -> 뒤 정리 -> push -> front 읽기` |
| stack | `top 답 확정 pop? -> 필요하면 답 기록 -> push` |

이 4단계를 적어 두면 표를 끝까지 외우지 않아도 된다.
지금 칸에서 보는 것은 항상 `왜 제거했는지`와 `언제 답을 쓰는지` 두 가지뿐이다.

## Drill A. Monotonic Deque (window max)

질문: 길이 `3` window를 한 칸씩 밀 때 최대값은?

| `i` | 값 | 결정(왜 pop?) | deque 상태 (`index:value`) | 출력 |
|---|---|---|---|---|
| `0` | `4` | push | `[(0:4)]` | `-` |
| `1` | `2` | push (`4`가 더 큼) | `[(0:4), (1:2)]` | `-` |
| `2` | `1` | push | `[(0:4), (1:2), (2:1)]` | `4` |
| `3` | `3` | front 만료 `(0:4)` 제거, back에서 `(2:1)`, `(1:2)` 제거 | `[(3:3)]` | `3` |
| `4` | `5` | back에서 `(3:3)` 제거 | `[(4:5)]` | `5` |

결과: `window max = [4, 3, 5]`

핵심 결정 포인트는 두 개다.

- front pop: window 밖 index 만료
- back pop: 새 값에게 지는 후보 제거

### 구현 전이용 최소 의사코드: deque max vs min

같은 뼈대에서 `뒤 정리 비교`만 뒤집으면 `window max`와 `window min`이 같이 풀린다.

| window max | window min |
|---|---|
| ```text
| dq = empty deque of index
|
| for i in 0..n-1:
|     while dq not empty and dq.front < i-k+1:
|         dq.pop_front()      // 만료 제거
|
|     while dq not empty and nums[dq.back] <= nums[i]:
|         dq.pop_back()       // 더 작은 후보 제거
|
|     dq.push_back(i)
|
|     if i >= k-1:
|         answer.add(nums[dq.front])
| ``` | ```text
| dq = empty deque of index
|
| for i in 0..n-1:
|     while dq not empty and dq.front < i-k+1:
|         dq.pop_front()      // 만료 제거
|
|     while dq not empty and nums[dq.back] >= nums[i]:
|         dq.pop_back()       // 더 큰 후보 제거
|
|     dq.push_back(i)
|
|     if i >= k-1:
|         answer.add(nums[dq.front])
| ``` |

처음 구현할 때는 이렇게 외우면 충분하다.

- deque는 항상 `front 만료 제거 -> back 후보 정리 -> push -> front 읽기`
- `max`면 뒤에서 작은 값을 버리고, `min`이면 뒤에서 큰 값을 버린다

## Drill B. Monotonic Stack (next greater)

질문: 각 index 오른쪽에서 처음 만나는 더 큰 값은?

| `i` | 값 | 결정(왜 pop?) | stack 상태 (`index:value`) | 확정된 답 |
|---|---|---|---|---|
| `0` | `4` | push | `[(0:4)]` | 없음 |
| `1` | `2` | push (`4`가 더 큼) | `[(0:4), (1:2)]` | 없음 |
| `2` | `1` | push | `[(0:4), (1:2), (2:1)]` | 없음 |
| `3` | `3` | `(2:1)`, `(1:2)` pop -> 답 `3` 확정 | `[(0:4), (3:3)]` | `ans[2]=3`, `ans[1]=3` |
| `4` | `5` | `(3:3)`, `(0:4)` pop -> 답 `5` 확정 | `[(4:5)]` | `ans[3]=5`, `ans[0]=5` |
| 종료 | `-` | 남은 `(4:5)`는 더 큰 값 없음 | `[]` | `ans[4]=-1` |

결과: `NGE = [5, 3, 3, 5, -1]`

핵심 결정 포인트는 하나다.

- top pop: "현재 값이 이전 index의 답을 확정"할 때만 pop

## Duplicate Add-On. 중복값 한 번 더 고정하기

이번에는 공통 입력을 아주 짧게 바꿔서 연산자 차이만 본다.

- 보조 입력: `dup = [2, 2, 1]`
- 보는 포인트: `같은 값이 나오면 이전 값을 남길지`, `equal도 답으로 인정할지`

### 1. Deque 쪽: `<` vs `<=`

질문: `k = 2`일 때 window max를 구한다.

- `값만` 보면 결과는 둘 다 `[2, 2]`다.
- 하지만 `대표 index`는 달라진다.

| 뒤 정리 조건 | `i = 1`에서 어떤 `2`가 남나 | 첫 window 대표 |
|---|---|---|
| `while backValue < cur` | 이전 `2(index 0)` 유지 | `index 0` |
| `while backValue <= cur` | 이전 `2(index 0)` pop, 새 `2(index 1)` 유지 | `index 1` |

한 줄로 요약하면:

- `<`는 `같은 값이면 이전 후보 유지`
- `<=`는 `같은 값이면 새 후보로 교체`

### 2. Stack 쪽: `next greater` vs `next greater or equal`

질문: 같은 `dup = [2, 2, 1]`에서 오른쪽 답을 비교한다.

| 질문 | pop 조건 | 결과 |
|---|---|---|
| `Next Greater` | `while topValue < cur` | `[-1, -1, -1]` |
| `Next Greater or Equal` | `while topValue <= cur` | `[2, -1, -1]` |

손으로 보면 차이는 `i = 1`의 두 번째 `2`에서 바로 난다.

| 현재 값 | `Next Greater` | `Next Greater or Equal` |
|---|---|---|
| 두 번째 `2` | 첫 번째 `2`를 pop하지 않음. 같은 값은 `greater`가 아님 | 첫 번째 `2`를 pop하고 `ans[0] = 2` 확정. 같은 값도 `equal`로 인정 |

여기서 초급자가 가장 자주 놓치는 부분은 이것이다.

- `strict greater`면 같은 값 `2`는 답이 아니므로 `<`까지만 pop한다.
- `greater or equal`이면 같은 값 `2`도 답이 되므로 `<=`까지 pop한다.

### 중복값 보조 예제에서 딱 기억할 두 줄

| 상황 | 먼저 적을 문장 |
|---|---|
| deque duplicate tie-break | `이전 대표를 남길까, 새 대표로 바꿀까?` |
| stack strict/or-equal | `같은 값도 답인가, 아직 답이 아닌가?` |

이 두 줄만 먼저 적으면 `<`/`<=`, `>`/`>=`를 외우기보다 문제 문장에서 다시 고를 수 있다.

### 구현 전이용 최소 의사코드: stack NGE vs NGE-or-equal

stack은 `같은 값도 이번에 답을 확정할지`만 먼저 정하면 된다.
둘 다 오른쪽 답을 pop 순간에 쓴다는 뼈대는 같다.

## Duplicate Add-On. 중복값 한 번 더 고정하기 (계속 2)

| next greater element (NGE) | next greater or equal element (NGEE) |
|---|---|
| ```text
| ans = [-1] * n
| st = empty stack of index
|
| for i in 0..n-1:
|     while st not empty and nums[st.top] < nums[i]:
|         ans[st.pop()] = nums[i]
|
|     st.push(i)
| ``` | ```text
| ans = [-1] * n
| st = empty stack of index
|
| for i in 0..n-1:
|     while st not empty and nums[st.top] <= nums[i]:
|         ans[st.pop()] = nums[i]
|
|     st.push(i)
| ``` |

입문자 기준으로는 아래 두 문장이 가장 중요하다.

- NGE: `현재 값이 예전 index의 답을 써 준다`
- NGEE: `현재 값이 같아도 예전 index의 답을 써 줄 수 있다`

## 빠른 비교표

| 구분 | monotonic deque | monotonic stack |
|---|---|---|
| 답의 형태 | 각 window마다 1개 | 각 index마다 1개 |
| pop 트리거 | `만료` + `뒤 후보 정리` | `현재 값이 top 답을 확정` |
| 답 읽는 시점 | `i >= k-1`마다 front 읽기 | pop 순간 answer 배열 채우기 |
| 상태 의미 | 현재 window 생존 후보 | 아직 답이 미정인 index |

## 자주 헷갈리는 포인트

- `둘 다 while-pop이라 같은 구조 아닌가요?`
  - 비슷해 보여도 pop 이유가 다르다. deque는 `만료/지배`, stack은 `답 확정`.
- `stack에서도 만료 제거를 해야 하나요?`
  - 아니다. stack 문제는 보통 고정 window가 아니라 "오른쪽 첫 큰 값" 같은 전역 비교다.
- `deque도 pop할 때 답을 채우나요?`
  - 보통 아니다. deque는 매 window에서 front를 읽어 답을 만든다.
- `strict/or-equal은 deque보다 stack에서만 중요한가요?`
  - 아니다. deque도 중복 tie-break에 영향이 있다. 값만 필요하면 둘 다 가능해 보여도, index tie-break가 붙으면 `<`와 `<=`가 정답을 바꾼다. 정리는 [Monotonic Operator Boundary Cheat Sheet](./monotonic-operator-boundary-cheat-sheet.md)에서 바로 확인하면 된다.

<a id="min-pse-mini-drill"></a>

## Mini Drill 2. 같은 입력으로 minimum + previous smaller

같은 배열 `nums = [4, 2, 1, 3, 5]`를 다시 쓰되, 이번에는 질문을 이렇게 바꾼다.

- Drill C (deque): `k = 3`일 때 각 window의 **최소값**
- Drill D (stack): 각 index의 **Previous Smaller Element (PSE)**
  (왼쪽에서 가장 가까운 더 작은 값, 없으면 `-1`)

### Drill C. Monotonic Deque (window min)

| `i` | 값 | 결정(왜 pop?) | deque 상태 (`index:value`) | 출력 |
|---|---|---|---|---|
| `0` | `4` | push | `[(0:4)]` | `-` |
| `1` | `2` | back에서 `(0:4)` 제거 (`4`가 더 큼) | `[(1:2)]` | `-` |
| `2` | `1` | back에서 `(1:2)` 제거 (`2`가 더 큼) | `[(2:1)]` | `1` |
| `3` | `3` | push (`1`이 더 작아 유지) | `[(2:1), (3:3)]` | `1` |
| `4` | `5` | push (`3`이 더 작아 유지) | `[(2:1), (3:3), (4:5)]` | `1` |

결과: `window min = [1, 1, 1]`

### Drill D. Monotonic Stack (previous smaller element)

| `i` | 값 | 결정(왜 pop?) | stack 상태 (`index:value`) | 확정된 답 |
|---|---|---|---|---|
| `0` | `4` | push | `[(0:4)]` | `ans[0] = -1` |
| `1` | `2` | `(0:4)` pop (`4 >= 2`) 후 push | `[(1:2)]` | `ans[1] = -1` |
| `2` | `1` | `(1:2)` pop (`2 >= 1`) 후 push | `[(2:1)]` | `ans[2] = -1` |
| `3` | `3` | pop 없음 (`1 < 3`), push | `[(2:1), (3:3)]` | `ans[3] = 1` |
| `4` | `5` | pop 없음 (`3 < 5`), push | `[(2:1), (3:3), (4:5)]` | `ans[4] = 3` |

결과: `PSE = [-1, -1, -1, 1, 3]`

### Mini Drill 2에서 가져갈 한 문장

- minimum deque도 본질은 같다: `만료 + 뒤 후보 정리`
- previous smaller stack도 본질은 같다: `top이 답 후보가 되도록 불필요 후보 pop`
- 그래서 같은 입력을 다시 풀 때도 `뼈대는 유지`, `비교와 답 쓰는 시점만 변경`으로 옮기면 된다

### 이 섹션을 다시 보면 좋은 경우

## Mini Drill 2. 같은 입력으로 minimum + previous smaller (계속 2)

- router quiz에서 `최근 k개 최소값`을 stack으로 골랐다면 여기서 `minimum deque` 트랙만 다시 읽는다.
- router quiz에서 `이전 더 작은 값`을 deque로 골랐다면 여기서 `PSE stack` 트랙만 다시 읽는다.
- 둘 다 헷갈리면 먼저 아래 한 줄만 다시 외운다: `window 답을 매번 읽으면 deque`, `각 index의 왼쪽/오른쪽 답을 확정하면 stack`

## 다음 단계

- 덱 쪽을 더 자세히: [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)
- 스택 쪽을 더 자세히: [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)
- 왜 O(n)인지 증명: [Monotone Deque Proof Intuition](../algorithm/monotone-deque-proof-intuition.md)

## 한 줄 정리

같은 입력을 두 번 풀어 보면, deque는 `window 극값`, stack은 `미해결 index 답 확정` 문제라는 차이가 바로 보인다.
