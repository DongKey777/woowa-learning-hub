---
schema_version: 3
title: Monotonic Deque Walkthrough
concept_id: data-structure/monotonic-deque-walkthrough
canonical: true
category: data-structure
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- sliding-window-extrema-choice
- deque-expiration-rule
- monotonic-duplicate-tie-break
aliases:
- monotonic deque walkthrough
- monotonic deque trace
- monotonic queue walkthrough
- sliding window maximum trace
- sliding window minimum trace
- plain deque to monotonic deque
- deque candidate pruning
- deque expiration
- recent k maximum
- recent k minimum
- monotonic deque duplicates
- deque index trace
symptoms:
- sliding window maximum을 손으로 추적해도 deque가 왜 답을 주는지 감이 안 와
- 최근 k개 최대값 문제에서 plain deque로는 왜 안 되는지 헷갈려
- monotonic deque에서 만료 제거와 뒤쪽 pop 순서를 자꾸 섞어 써
intents:
- definition
prerequisites:
- data-structure/deque-basics
- algorithm/sliding-window-patterns
next_docs:
- data-structure/monotonic-deque-vs-heap-for-window-extrema
- data-structure/sliding-window-duplicate-extrema-index-drill
- data-structure/monotonic-deque-vs-stack-shared-input-drill
linked_paths:
- contents/data-structure/monotonic-queue-and-stack.md
- contents/data-structure/monotonic-deque-vs-heap-for-window-extrema.md
- contents/data-structure/sliding-window-duplicate-extrema-index-drill.md
- contents/data-structure/monotonic-deque-vs-stack-shared-input-drill.md
- contents/data-structure/monotonic-operator-boundary-cheat-sheet.md
- contents/algorithm/sliding-window-patterns.md
- contents/algorithm/monotone-deque-proof-intuition.md
confusable_with:
- data-structure/monotonic-stack-walkthrough
- data-structure/monotonic-queue-and-stack
- data-structure/queue-vs-deque-vs-priority-queue-primer
forbidden_neighbors:
- contents/data-structure/monotonic-stack-walkthrough.md
expected_queries:
- sliding window maximum을 처음부터 표로 따라가며 설명해줘
- monotonic deque가 plain deque와 뭐가 달라지는지 입문자 기준으로 보고 싶어
- 최근 k개 최댓값 문제에서 만료 제거와 뒤쪽 pop 순서를 같이 정리해줘
- monotonic deque에서 index를 저장해야 하는 이유를 walkthrough로 알고 싶어
- sliding window minimum도 같은 규칙으로 추적하는 예제를 보고 싶어
- 단조 덱 중복값 처리에서 < 와 <= 중 무엇을 쓰는지 초보자용으로 설명해줘
- deque front가 현재 답이 되려면 어떤 후보 정리가 필요한지 단계별로 보여줘
- window max 문제에서 heap 대신 monotonic deque를 먼저 배우는 이유가 궁금해
contextual_chunk_prefix: |
  이 문서는 sliding window 최대값과 최소값 문제를 배우는 학습자가
  monotonic deque가 plain deque에 만료 제거와 뒤쪽 후보 정리 규칙을
  더해 답을 읽게 만드는 흐름을 처음 잡는 primer다. 최근 k개 최댓값,
  index를 왜 저장하는지, 뒤에서 약한 후보 버리기, 중복값에서 < 와 <=
  선택, front가 현재 답이 되는 이유 같은 자연어 paraphrase가 본
  문서의 핵심 개념에 매핑된다.
---
# Monotonic Deque Walkthrough

> 한 줄 요약: monotonic deque는 plain deque에 `만료 제거`와 `뒤쪽 후보 정리` 규칙을 더해, sliding window의 최대/최소를 즉시 읽게 만든다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: monotonic deque walkthrough basics, monotonic deque walkthrough beginner, monotonic deque walkthrough intro, data structure basics, beginner data structure, 처음 배우는데 monotonic deque walkthrough, monotonic deque walkthrough 입문, monotonic deque walkthrough 기초, what is monotonic deque walkthrough, how to monotonic deque walkthrough
> 관련 문서:
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
> - [Monotonic Deque vs Heap for Window Extrema](./monotonic-deque-vs-heap-for-window-extrema.md)
> - [Monotonic Stack Walkthrough](./monotonic-stack-walkthrough.md)
> - [Monotonic Operator Boundary Cheat Sheet](./monotonic-operator-boundary-cheat-sheet.md)
> - [Sliding Window Duplicate Extrema Index Drill](./sliding-window-duplicate-extrema-index-drill.md)
> - [Monotonic Deque vs Monotonic Stack Shared-Input Drill](./monotonic-deque-vs-stack-shared-input-drill.md)
> - [Sliding Window Patterns](../algorithm/sliding-window-patterns.md)
> - [Monotone Deque Proof Intuition](../algorithm/monotone-deque-proof-intuition.md)
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
>
> retrieval-anchor-keywords: monotonic deque walkthrough, monotonic deque trace, monotonic queue walkthrough, sliding window maximum walkthrough, sliding window minimum walkthrough, sliding window maximum trace, sliding window minimum trace, monotonic deque beginner, plain deque to monotonic deque, deque candidate pruning, deque dominance, deque expiration, deque back pop, recent k maximum trace, recent k minimum trace, max in every window walkthrough, min in every window walkthrough, deque index trace, sliding window extrema tutorial, monotonic deque step by step, monotonic deque duplicates, deque duplicate tie break, value only vs index output deque, monotonic deque value vs index, monotonic deque strict vs or equal, monotonic deque operator quiz, sliding window duplicate operator quiz, window max duplicate tie break, window min duplicate tie break, sliding window min max duplicate quiz, monotonic deque duplicate representative quiz, monotonic deque vs monotonic stack, monotonic stack contrast, monotonic deque vs stack shared input drill, deque vs stack beginner choice, 단조 덱 스택 공통 입력 드릴, 단조 덱 풀이 순서, 단조 덱 추적, 슬라이딩 윈도우 최대값 추적, 슬라이딩 윈도우 최소값 추적, 일반 덱에서 단조 덱으로, 덱 만료 처리, 덱 뒤에서 pop, 값만 출력 index까지 출력, 단조 덱 중복 tie break, 단조 덱 strict or equal, 슬라이딩 윈도우 중복 연산자 퀴즈, 윈도우 최대 최소 중복 퀴즈, 윈도우 극값 입문

## 빠른 라우팅

- `sliding window maximum`, `window minimum`, `최근 k개 중 최대/최소`를 손으로 따라가며 이해하고 싶다면 이 문서가 직접 라우트다.
- 같은 배열에서 `deque`와 `stack` 선택 기준을 먼저 비교하고 싶다면 [Monotonic Deque vs Monotonic Stack Shared-Input Drill](./monotonic-deque-vs-stack-shared-input-drill.md)로 먼저 가면 된다.
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

### 작은 분기 박스: 값만 출력 vs index까지 출력

중복값이 있을 때 초보자가 가장 많이 헷갈리는 지점은 "`<`와 `<=` 중 뭐가 정답인가?"다.
먼저 이렇게 생각하면 쉽다.

- **값만 필요**하면: 같은 값 둘 중 누구를 남겨도 답의 값은 같다.
- **index도 의미가 있으면**: "왼쪽 것을 남길지, 오른쪽 것을 남길지"부터 정해야 한다.

즉 연산자를 먼저 외우기보다, **동점일 때 누구를 대표자로 남길지**를 먼저 정하면 된다.

| 출력 목표 | max deque 뒤쪽 pop 조건 | min deque 뒤쪽 pop 조건 | 동점에서 남는 쪽 |
|---|---|---|---|
| 값만 출력 | `<=` | `>=` | 새 값(오른쪽) |
| index까지 출력 + 왼쪽 tie-break | `<` | `>` | 옛 값(왼쪽) |

작은 예제로 보면 더 분명하다.

- 입력: `nums = [5, 5, 4]`, `k = 2`
- window별 최대값은 둘 다 `[5, 5]`

| 구현 | 첫 window `[0..1]` 뒤 deque | 첫 출력 |
|---|---|---|
| `while backValue <= cur` | `[(1:5)]` | 값은 `5`, index는 `1` |
| `while backValue < cur` | `[(0:5), (1:5)]` | 값은 `5`, index는 `0` |

최소값도 같은 방식이다.

- 입력: `nums = [2, 2, 3]`, `k = 2`
- 첫 window `[0..1]`의 최소값은 `2`

## 4. 최대값 trace (계속 2)

| 구현 | 첫 window `[0..1]` 뒤 deque | 첫 출력 |
|---|---|---|
| `while backValue >= cur` | `[(1:2)]` | 값은 `2`, index는 `1` |
| `while backValue > cur` | `[(0:2), (1:2)]` | 값은 `2`, index는 `0` |

헷갈릴 때는 이렇게 체크하면 된다.

- **슬라이딩 윈도우 최대/최소의 값만 반환**하는 전형 문제면 `max: <=`, `min: >=`로 두는 편이 가장 단순하다.
- **가장 왼쪽 index**, **가장 먼저 등장한 위치**까지 의미가 있으면 strict 비교(`max: <`, `min: >`)를 검토해야 한다.
- 문제에서 tie-break를 말하지 않았는데 구현 리뷰에서 연산자 질문이 나온다면, [Monotonic Operator Boundary Cheat Sheet](./monotonic-operator-boundary-cheat-sheet.md)로 연결해서 `strict vs or-equal` 기준을 다시 확인하면 된다.

바로 코드로 대조하면 차이는 한 줄이다.

```java
// window maximum: 값만 출력하면 equal도 pop해서 오른쪽 값을 대표로 둔다.
while (!dq.isEmpty() && nums[dq.peekLast()] <= nums[i]) {
    dq.pollLast();
}
dq.offerLast(i);
answer.add(nums[dq.peekFirst()]);
```

```java
// window maximum: 가장 왼쪽 index가 중요하면 equal은 남겨서 왼쪽 값을 대표로 둔다.
while (!dq.isEmpty() && nums[dq.peekLast()] < nums[i]) {
    dq.pollLast();
}
dq.offerLast(i);
answer.add(dq.peekFirst());
```

최소값은 비교만 반대로 뒤집으면 된다. 즉 `값만 출력`이면 `>=`, `왼쪽 index 유지`면 `>`다.

## 4.5. 미니 퀴즈: strict vs or-equal

아래 4문항은 모두 **중복값이 들어온 순간 뒤에서 무엇을 pop할지**를 묻는다.
먼저 답을 보기보다, `값만 필요? index tie-break도 필요?`를 먼저 고르면 훨씬 잘 맞는다.

| 번호 | 상황 | 고를 연산자 |
|---|---|---|
| 1 | `window maximum`의 **값만** 출력한다. 중복 `5, 5`가 오면 오른쪽 `5`만 남겨도 된다. | `backValue <= cur` 또는 `backValue < cur` |
| 2 | `window maximum`에서 **가장 왼쪽 index**도 의미 있다. 중복 `5, 5`면 왼쪽 `5`를 남기고 싶다. | `backValue <= cur` 또는 `backValue < cur` |
| 3 | `window minimum`의 **값만** 출력한다. 중복 `2, 2`가 오면 오른쪽 `2`만 남겨도 된다. | `backValue >= cur` 또는 `backValue > cur` |
| 4 | `window minimum`에서 **가장 왼쪽 index**도 의미 있다. 중복 `2, 2`면 왼쪽 `2`를 남기고 싶다. | `backValue >= cur` 또는 `backValue > cur` |

정답은 아래와 같다.

| 번호 | 정답 | 이유 |
|---|---|---|
| 1 | `backValue <= cur` | 값만 같으면 옛 후보를 지워도 최대값 자체는 안 바뀐다. |
| 2 | `backValue < cur` | 같은 값은 지우지 않아야 왼쪽 index가 front에 남는다. |
| 3 | `backValue >= cur` | 값만 같으면 옛 후보를 지워도 최소값 자체는 안 바뀐다. |
| 4 | `backValue > cur` | 같은 값은 지우지 않아야 왼쪽 index가 먼저 남는다. |

한 줄로 다시 묶으면 이렇다.

- **값만 출력**: `max <=`, `min >=`
- **왼쪽 index 유지**: `max <`, `min >`

아직 헷갈리면 [Sliding Window Duplicate Extrema Index Drill](./sliding-window-duplicate-extrema-index-drill.md), [Monotonic Duplicate Rule Micro-Drill](./monotonic-duplicate-rule-micro-drill.md), [Monotonic Operator Boundary Cheat Sheet](./monotonic-operator-boundary-cheat-sheet.md)를 이어서 보면 duplicate 규칙만 따로 다시 고정할 수 있다.

## 4.6. 미니 퀴즈 2: 실제로 누구를 남길까

위 4문항이 "어떤 연산자를 고를까"였다면, 이번 4문항은 "그래서 deque에 누가 남나"를 묻는다.
모두 첫 window가 막 완성된 순간만 본다.

| 번호 | 상황 | 남는 대표 |
|---|---|---|
| 1 | `nums = [5, 5, 4]`, `k = 2`, `window maximum`, 값만 출력, `backValue <= cur` | 왼쪽 `5` 또는 오른쪽 `5` |
| 2 | `nums = [5, 5, 4]`, `k = 2`, `window maximum`, 왼쪽 index 유지, `backValue < cur` | 왼쪽 `5` 또는 오른쪽 `5` |
| 3 | `nums = [2, 2, 3]`, `k = 2`, `window minimum`, 값만 출력, `backValue >= cur` | 왼쪽 `2` 또는 오른쪽 `2` |
| 4 | `nums = [2, 2, 3]`, `k = 2`, `window minimum`, 왼쪽 index 유지, `backValue > cur` | 왼쪽 `2` 또는 오른쪽 `2` |

정답은 아래와 같다.

| 번호 | 정답 | 이유 |
|---|---|---|
| 1 | 오른쪽 `5` | `<=`라서 같은 값도 pop한다. 새 값이 대표가 된다. |
| 2 | 왼쪽 `5` | `<`라서 같은 값은 안 지운다. 먼저 온 값이 남는다. |
| 3 | 오른쪽 `2` | `>=`라서 같은 값도 pop한다. 새 값이 대표가 된다. |
| 4 | 왼쪽 `2` | `>`라서 같은 값은 안 지운다. 먼저 온 값이 남는다. |

한 번 더 짧게 묶으면 이렇다.

| 목표 | max에서 duplicate 처리 | min에서 duplicate 처리 |
|---|---|---|
| 값만 맞으면 된다 | 오른쪽 대표 허용 | 오른쪽 대표 허용 |
| 가장 왼쪽 index가 중요하다 | 왼쪽 대표 유지 | 왼쪽 대표 유지 |

즉 `strict vs or-equal`은 어려운 연산자 암기가 아니라, **duplicate에서 왼쪽을 살릴지 오른쪽을 살릴지**를 고르는 문제다.

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
- 값만 출력하는 최대값은 보통 `<=`, 최소값은 보통 `>=`를 쓴다.
- index tie-break가 중요하면 최대값은 `<`도 가능하고, 최소값은 `>`도 가능하다.
- front가 답이 되는 이유는 deque가 이미 monotonic invariant를 유지하고 있기 때문이다.

## 한 줄 정리

plain deque가 "들어온 순서"를 기억한다면, monotonic deque는 "앞으로도 답이 될 후보만" 기억한다.
