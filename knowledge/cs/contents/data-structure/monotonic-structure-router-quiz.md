# Monotonic Structure Router Quiz

> 한 줄 요약: 문제 문장을 보고 `deque / stack / neither`를 10초 안에 고르고, `greater`와 `greater or equal`도 함께 구분하는 초급 6문항 퀴즈.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Monotonic Deque vs Monotonic Stack Shared-Input Drill](./monotonic-deque-vs-stack-shared-input-drill.md) - 이 퀴즈에서 `deque / stack` 분기를 헷갈렸을 때 바로 이어 보는 같은 입력 비교 복습
> - [Min/PSE Mini Drill Path](./monotonic-deque-vs-stack-shared-input-drill.md#min-pse-mini-drill)
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
> - [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)
> - [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)
> - [Monotonic Operator Boundary Cheat Sheet](./monotonic-operator-boundary-cheat-sheet.md)
> - [Deque Router Example Pack](./deque-router-example-pack.md)
> - [Sliding Window Patterns](../algorithm/sliding-window-patterns.md)
>
> retrieval-anchor-keywords: monotonic structure router quiz, monotonic answer key table, signal to structure table, deque stack neither quiz, monotonic beginner quiz, deque vs stack classification, monotonic prompt classification, sliding window deque quiz, next greater stack quiz, histogram stack quiz, meeting rooms neither quiz, monotonic structure primer quiz, monotonic min pse mini drill, minimum deque previous smaller stack, deque vs stack recovery path, next greater vs next greater or equal, greater vs greater or equal quiz, monotonic operator translation quiz, strict or equal monotonic question, same input deque stack neither example, single input monotonic comparison, one input deque stack neither, router first then shared input drill, monotonic first reading route, monotonic beginner reading order, monotonic wrong answer self check, deque mistake self check, stack mistake self check, neither mistake self check, signal 선택 구조 표, 단조 구조 라우터 퀴즈, 덱 스택 분류 퀴즈, 덱 스택 neither 문제 분기, 초급 단조 구조 연습, 최소값 덱 이전 작은 값 스택, min pse 미니 드릴, 다음 큰 수 다음 크거나 같은 수, greater greater or equal 구분, strict or equal 연산자 번역, 같은 입력 덱 스택 neither 비교, 입력 하나로 단조 구조 비교, 라우터 다음 공통 입력 드릴, 단조 첫 독서 경로, 오답 셀프 체크, 덱 오답 점검, 스택 오답 점검, neither 오답 점검

## 처음 읽는 순서

먼저 이 문서에서 `deque / stack / neither`를 고른다.
분기는 맞췄는데 손으로 따라가는 감각이 약하면 바로 [Monotonic Deque vs Monotonic Stack Shared-Input Drill](./monotonic-deque-vs-stack-shared-input-drill.md)로 내려가 같은 입력에서 `window 만료`와 `답 확정`을 나란히 본다.

## 먼저 잡는 10초 규칙

- `연속 window + 만료`면 `deque`
- `pop 순간 index 답 확정`이면 `stack`
- 둘 다 아니면 `neither` (대개 heap, sweep line, map/freq 등)

## 한 페이지 미니 답안표

먼저 문제에서 **답의 모양**을 본다.
`최근 k개 범위를 유지해야 하나?`, `지금 원소가 예전 원소의 답을 확정하나?`, `아예 다른 종류의 문제인가?`를 3갈래로 자르면 첫 분기가 빨라진다.

| 문제에서 먼저 보이는 signal | 선택 구조 | 왜 이쪽인가 |
|---|---|---|
| `길이 k`, `최근 k개`, `연속 구간`, `window가 한 칸씩 이동` | `Deque` | 윈도우 밖 index 만료와 극값 후보 정리가 동시에 필요하다 |
| `매 시점 최근 5초 최소/최대`, `현재 구간 extrema` | `Deque` | front가 현재 답이고, 뒤에서는 쓸모없는 후보를 버린다 |
| `오른쪽에서 처음 더 큰 수`, `이전 더 작은 수` | `Stack` | 현재 값이 stack top 후보들의 답을 pop 시점에 확정한다 |
| `히스토그램 최대 직사각형`, `span`, `막대가 꺾이는 순간 너비 계산` | `Stack` | 깨지는 순간 높이의 유효 범위가 정해진다 |
| `window`라는 말은 있지만 `합`, `빈도`, `중복 없는 최장 구간`이 핵심 | `Neither` | 보통 monotonic이 아니라 sliding window + map/freq 패턴이다 |
| `회의실 수`, `예약 겹침`, `interval overlap` | `Neither` | 연속 index window가 아니라 interval 집합이라 heap/sweep line이 더 자연스럽다 |
| `항상 최대값 하나만 빨리 꺼내기`, 만료보다 `우선순위`가 핵심 | `Neither` | heap route가 더 직접적이다 |

### `Neither`인데 왜 서로 다른가: `map/freq window` vs `interval overlap`

먼저 `둘 다 monotonic이 아니다`까지만 맞추고 끝내면 절반만 맞춘 것이다.
초급 단계에서는 **입력이 한 줄 배열/문자열인지, 아니면 각 원소가 이미 `start/end`를 가진 일정 레코드인지**를 먼저 보면 다음 문서가 바로 갈린다.

| 프롬프트 | 선택 구조 | 왜 이쪽인가 | 바로 갈 문서 |
|---|---|---|---|
| `문자열에서 중복 없는 가장 긴 부분 문자열` | `Neither` | 배열/문자열의 **연속 구간**을 밀면서 `freq/map`으로 상태를 갱신한다 | [Sliding Window Patterns](../algorithm/sliding-window-patterns.md) |
| `회의 시작/종료 시간이 주어질 때 동시에 몇 개가 겹치는가` | `Neither` | 각 원소가 이미 `start/end`를 가진 **interval 레코드**라서 overlap counting이 핵심이다 | [Sweep Line Overlap Counting](../algorithm/sweep-line-overlap-counting.md) |

짧게 외우면 이렇다.

- `문자/숫자 배열을 한 칸씩 밀며 중복/빈도/합을 관리`하면 `sliding window + map/freq`
- `회의/예약처럼 시작과 끝이 따로 있는 일정 묶음`이면 `interval overlap`
- 둘 다 `Neither`지만, 전자는 `연속 인덱스 구간`, 후자는 `독립 interval 집합`을 다룬다

### 3초 체크 질문

- `범위 밖으로 밀려난 원소를 지워야 하나?` 그러면 먼저 `deque`를 의심한다.
- `현재 원소가 이전 원소들의 답을 한꺼번에 끝내나?` 그러면 먼저 `stack`을 의심한다.
- 둘 다 아니면 `monotonic`이 아닐 가능성이 높다.

## 연산자 문장도 같이 번역하기

문제 문장에서 `greater`와 `greater or equal`은 거의 비슷해 보여도, **같은 값을 만나면 멈추는지 아니면 넘겨 버리는지**가 달라진다.

| 문장 표현 | 머릿속 번역 | duplicate를 만났을 때 |
|---|---|---|
| `first greater` | `나보다 엄격하게 큰 값` | 같은 값은 답이 아니다. 더 큰 값을 계속 찾는다 |
| `first greater or equal` | `나와 같아도 답 인정` | 같은 값을 만나면 거기서 답이 확정될 수 있다 |

- 초급 단계에서는 먼저 `구조 선택`을 맞춘 뒤, 바로 다음으로 `strict냐 or-equal이냐`를 확인하면 실수가 많이 줄어든다.
- 더 자세한 연산자 규칙은 [Monotonic Operator Boundary Cheat Sheet](./monotonic-operator-boundary-cheat-sheet.md)로 바로 이어서 보면 된다.

## 입력 1개로 `deque / stack / neither` 나란히 보기

먼저 입력은 하나만 고정한다.

- 배열: `nums = [4, 2, 1, 3, 5]`
- 보조 조건: `k = 3`

핵심은 **입력이 아니라 질문이 구조를 결정한다**는 점이다.

| 같은 입력에서 바꾼 질문 | 선택 구조 | 왜 이렇게 갈리나 |
|---|---|---|
| `길이 3인 모든 연속 구간의 최대값을 구하라` | `Deque` | `최근 k개` 범위가 움직이고, window 밖 index 만료가 필요하다 |
| `각 원소의 오른쪽에서 처음 만나는 더 큰 값을 구하라` | `Stack` | 현재 값이 이전 index들의 답을 pop 시점에 확정한다 |
| `값이 큰 순서대로 상위 2개만 빠르게 뽑아라` | `Neither` | 연속 window도 아니고 NGE류 답 확정도 아니라 보통 heap/partial sort 쪽이다 |

### 눈으로 바로 붙이는 미니 답안

| 질문 | 답 예시 | 초급용 한 줄 해석 |
|---|---|---|
| `길이 3 window 최대값` | `[4, 3, 5]` | 매 window마다 front를 읽는 문제라 `deque` |
| `다음 더 큰 값` | `[5, 3, 3, 5, -1]` | 현재 값이 예전 답을 써 주는 문제라 `stack` |
| `상위 2개 큰 값` | `[5, 4]` | "최근 k개"도 아니고 "각 index 답"도 아니라 `neither` |

- 같은 `nums`라도 `window 답을 매번 읽는가?`가 보이면 `deque`
- 같은 `nums`라도 `각 index의 미해결 답을 지금 확정하는가?`가 보이면 `stack`
- 둘 다 아니면 `monotonic`이 아니라 다른 도구를 먼저 본다

헷갈렸다면: 방금 고른 구조를 같은 입력으로 다시 붙여 보는 [Monotonic Deque vs Monotonic Stack Shared-Input Drill](./monotonic-deque-vs-stack-shared-input-drill.md)로 바로 이어 가면 `왜 deque였는지`, `왜 stack이었는지`가 손 추적으로 고정된다.

## 6문항 라우터 퀴즈

1. 프롬프트: `길이 k인 모든 연속 구간의 최대값을 구하라.`
답: `Deque` - 윈도우가 한 칸씩 이동하고 만료 index를 지워야 하므로 monotonic deque가 맞다.
오답 셀프 체크 질문:
- `최근 k개`에서 범위 밖 index를 앞에서 바로 버려야 하는가?
- 답이 `각 index의 다음 값`이 아니라 `매 window의 최대값`인가?
- 핵심이 합/빈도/정렬이 아니라 `연속 구간 extrema` 유지인가?
헷갈렸다면: `window 답을 매번 읽는가?`를 다시 보고, 반대 부호 버전인 [Min/PSE Mini Drill Path](./monotonic-deque-vs-stack-shared-input-drill.md#min-pse-mini-drill)의 `minimum deque`를 같이 보면 `max/min`이 아니라 `window냐 아니냐`가 기준이라는 점이 더 잘 고정된다.

2. 프롬프트: `각 원소의 오른쪽에서 처음 만나는 더 큰 수를 구하라.`
답: `Stack` - 현재 값이 이전 index들의 답을 pop 시점에 확정하는 전형적인 monotonic stack 문제다.
오답 셀프 체크 질문:
- `최근 k개` 같은 만료 문장 없이도 답이 정의되는가?
- 현재 값 하나가 여러 미해결 index의 답을 pop 시점에 끝내는가?
- 답이 전체 최대 하나가 아니라 `각 index별 다음 값` 형태인가?
헷갈렸다면: 오른쪽 답을 쓰는 NGE와 왼쪽 답을 읽는 PSE를 같이 보면 더 선명하다. [Min/PSE Mini Drill Path](./monotonic-deque-vs-stack-shared-input-drill.md#min-pse-mini-drill)의 `PSE stack`을 같이 보면 `답 확정/답 읽기`가 둘 다 stack 축이라는 점이 보인다.

3. 프롬프트: `회의 시작/종료 시간이 주어질 때 필요한 최소 회의실 수를 구하라.`
답: `Neither` - 연속 window extrema나 NGE가 아니라 interval overlap이므로 보통 min-heap 또는 sweep line을 쓴다.
오답 셀프 체크 질문:
- 회의들은 `최근 k개 window`가 아니라 시작/종료가 따로 있는 interval 집합인가?
- 현재 회의 하나가 과거 회의들의 `다음 값` 답을 확정하는 구조인가?
- 문제의 답이 `각 원소별 관계`가 아니라 `동시에 몇 개 겹치나`인가?
헷갈렸다면: `Neither`라고만 묶지 말고 바로 옆의 `문자열에서 중복 없는 가장 긴 부분 문자열`과 비교해 본다. `left/right`로 배열 한 줄을 미는 문제면 [Sliding Window Patterns](../algorithm/sliding-window-patterns.md), `start/end` 일정이 겹치는지 세는 문제면 [Sweep Line Overlap Counting](../algorithm/sweep-line-overlap-counting.md)으로 갈라진다.

4. 프롬프트: `매 초마다 최근 5초 이벤트의 최솟값을 출력하라.`
답: `Deque` - 최근 k개 범위 유지와 만료 제거가 핵심이라 monotonic deque 라우트가 맞다.
오답 셀프 체크 질문:
- `최근 5초`라는 문장이 곧 움직이는 window 만료 조건인가?
- 현재 이벤트가 과거 이벤트의 답을 쓰는 게 아니라 `지금 시점 최소`를 읽는가?
- `최솟값`이라는 단어보다 `최근 범위 유지`가 더 큰 신호인가?
헷갈렸다면: 이 문항이 바로 `min/PSE` 갈림길이다. `최근 5초` 때문에 답을 매번 읽어야 하므로 stack이 아니라 deque다. 바로 아래 [Min/PSE Mini Drill Path](./monotonic-deque-vs-stack-shared-input-drill.md#min-pse-mini-drill)로 가서 `minimum deque` 표를 한 번 더 따라가면 된다.

5. 프롬프트: `히스토그램에서 만들 수 있는 최대 직사각형 넓이를 구하라.`
답: `Stack` - 막대가 pop될 때 너비와 높이가 확정되는 monotonic stack 패턴이다.
오답 셀프 체크 질문:
- `최근 k개` 같은 window 만료 없이 막대 경계가 깨질 때 답이 정해지는가?
- 낮은 막대를 만났을 때 이전 높은 막대들의 넓이가 연쇄적으로 확정되는가?
- 출력은 최대 넓이 하나여도 계산 방식은 `각 막대의 유효 범위`를 정하는가?

6. 프롬프트: `각 원소의 오른쪽에서 처음 만나는 greater or equal 값을 구하라. 즉, 다음 크거나 같은 수를 찾는다.`
답: `Stack` - 여전히 `현재 값이 이전 index들의 답을 pop 시점에 확정`하는 문제라 구조는 stack이다. 다만 이번에는 `greater`가 아니라 `greater or equal`이므로 같은 값도 답으로 인정된다는 점을 한 번 더 읽어야 한다.
오답 셀프 체크 질문:
- `window`가 아니라 `각 index의 오른쪽 첫 답`을 찾는 문제인가?
- 구조 선택과 별개로 `같은 값도 답으로 인정`하는 문장이 들어 있는가?
- 바뀐 것이 `stack vs deque`가 아니라 `strict vs or-equal` 번역뿐인가?
헷갈렸다면: 여기서 바뀌는 것은 `deque vs stack`이 아니라 `연산자 번역`이다. `다음 큰 수`면 같은 값을 넘기고, `다음 크거나 같은 수`면 같은 값을 만나는 순간 답이 될 수 있다. 이 감각은 [Monotonic Operator Boundary Cheat Sheet](./monotonic-operator-boundary-cheat-sheet.md)와 [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)를 붙여 보면 더 빨리 고정된다.

## 틀렸을 때 바로 가는 복구 경로

먼저 용어보다 `답의 모양`을 다시 본다.

| 내가 틀린 이유 | 바로 볼 문서 | 왜 여기로 가는가 |
|---|---|---|
| `최대/최소`라는 단어만 보고 deque/stack을 섞었다 | [Min/PSE Mini Drill Path](./monotonic-deque-vs-stack-shared-input-drill.md#min-pse-mini-drill) | `max/min`보다 `window 답을 읽는가`가 먼저라는 점을 같은 입력으로 다시 보여 준다 |
| `최근 k개 최소값`을 stack으로 골랐다 | [Min/PSE Mini Drill Path](./monotonic-deque-vs-stack-shared-input-drill.md#min-pse-mini-drill) | `minimum deque` 표에서 `만료 + 뒤 후보 정리`를 바로 복습할 수 있다 |
| `이전 더 작은 값`을 deque로 골랐다 | [Min/PSE Mini Drill Path](./monotonic-deque-vs-stack-shared-input-drill.md#min-pse-mini-drill) | `PSE stack` 표에서 `현재 값보다 작은 왼쪽 후보만 남긴다`는 stack 감각을 다시 잡을 수 있다 |
| `greater`와 `greater or equal`을 같은 뜻으로 읽었다 | [Monotonic Operator Boundary Cheat Sheet](./monotonic-operator-boundary-cheat-sheet.md) | `같은 값을 답으로 인정하는지`를 짧은 tie-break 규칙으로 다시 고정할 수 있다 |
| `window`라는 단어만 보고 무조건 monotonic으로 갔다 | [Sliding Window Patterns](../algorithm/sliding-window-patterns.md) | 합/빈도 문제는 deque가 아니라 map/freq 라우트일 수 있다 |
| `deque냐 stack이냐` 자체가 아직 흐리다 | [Monotonic Deque vs Monotonic Stack Shared-Input Drill](./monotonic-deque-vs-stack-shared-input-drill.md) | 이 퀴즈의 분기 결과를 같은 입력 손추적으로 바로 확인할 수 있다 |

## 자주 틀리는 한 줄 오해

- `window`라는 단어만 보이면 deque가 아니다: 합/빈도 문제면 map/freq 슬라이딩 윈도우일 수 있다.
- `deque를 쓴다`와 `monotonic deque`는 다르다: 양끝 시뮬레이션은 plain deque일 수 있다.
- `최대/최소`라는 단어만 보고 deque로 가지 않는다: `최근 k개 범위`가 없으면 heap이나 정렬 기준 문제일 수 있다.
- `stack`은 LIFO라서 쓰는 게 아니라 `pop 순간 답 확정`이라서 쓰는 경우가 많다.
- `greater`와 `greater or equal`은 같은 말이 아니다: duplicate를 답으로 인정하는지가 달라진다.
