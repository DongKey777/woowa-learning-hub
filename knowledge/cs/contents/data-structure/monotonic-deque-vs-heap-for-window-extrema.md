# Monotonic Deque vs Heap for Window Extrema

> 한 줄 요약: 고정 길이 sliding-window 최대/최소는 보통 monotonic deque가 기본값이고, heap + lazy deletion은 더 일반적인 우선순위 큐 패턴을 재사용해야 할 때 쓰는 차선책이다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
> - [Monotonic Deque Walkthrough](./monotonic-deque-walkthrough.md)
> - [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)
> - [Sliding Window Patterns](../algorithm/sliding-window-patterns.md)
> - [Monotone Deque Proof Intuition](../algorithm/monotone-deque-proof-intuition.md)
>
> retrieval-anchor-keywords: monotonic deque vs heap, monotonic deque vs priority queue, sliding window maximum heap, sliding window minimum heap, sliding window maximum lazy deletion, sliding window minimum lazy deletion, heap lazy deletion window extrema, monotonic deque window extrema, deque vs heap sliding window, recent k maximum heap, recent k minimum heap, fixed window extrema deque, fixed window extrema heap, window maximum priority queue, window minimum priority queue, stale heap entry sliding window, stale top cleanup, heap buried stale entry, lazy deletion duplicate bug, priority queue duplicate expiration, monotonic deque duplicate handling, window extrema data structure choice, sliding window max min choose deque heap, 단조 덱 vs 힙, 슬라이딩 윈도우 최대값 힙, 슬라이딩 윈도우 최소값 힙, lazy deletion 윈도우 극값, 우선순위 큐 stale entry, 덱 힙 선택 기준, 최근 k개 최대 최소 자료구조

## 빠른 선택 표

| 질문 형태 | 먼저 고를 구조 | 이유 |
|---|---|---|
| `sliding window maximum/minimum`, `최근 k개 중 최대/최소`처럼 **고정 길이 FIFO window의 extrema 하나**가 필요하다 | **monotonic deque** | window 만료가 항상 `가장 오래된 index`부터 일어나고, 뒤쪽의 약한 후보를 미리 버릴 수 있어서 `O(n)`으로 끝난다 |
| 표준 `PriorityQueue` 패턴을 그대로 재사용하고 싶고, `O(log n)`과 stale entry 누적 비용을 감수할 수 있다 | **heap + lazy deletion** | 구현 감각은 익숙하지만, deque보다 느리고 stale cleanup 버그가 더 자주 난다 |
| leaving element가 항상 oldest가 아니거나, `max/min` 말고 더 일반적인 ordered delete / top query가 필요하다 | **heap / balanced BST / multiset 계열** | monotonic deque는 FIFO 만료를 전제로 하는 특화 구조라 arbitrary delete에는 맞지 않는다 |
| `median`, `kth`, `top-2`, `top-k`처럼 extrema 하나보다 richer order statistic이 필요하다 | **다른 구조를 검토** | monotonic deque는 max/min 하나에 특화돼 있고, plain heap 하나도 이런 질의를 바로 해결하지 못한다 |

핵심 문장은 간단하다.

- **고정 길이 window의 max/min 하나면 deque가 정답 쪽에 가깝다.**
- **heap은 "할 수는 있지만, 덜 특화된 구조"라서 lazy deletion 함정까지 함께 따라온다.**

## 1. 왜 monotonic deque가 기본값인가

sliding-window extrema는 삭제 패턴이 매우 특수하다.

- 새 원소는 항상 오른쪽 끝으로 들어온다.
- 만료되는 원소는 항상 왼쪽 끝, 즉 **가장 오래된 index**다.
- 답으로 필요한 값은 매 window마다 **최댓값 또는 최솟값 하나**다.

이 구조에서는 heap보다 deque가 더 직접적이다.

1. front에서는 `만료된 index`만 제거하면 된다.
2. back에서는 새 값에게 진 후보를 미리 제거할 수 있다.
3. 그래서 deque 안에는 "앞으로 답이 될 후보"만 남는다.

최대값 기준 불변식은 아래 한 줄이다.

- front에서 back으로 갈수록 값이 감소한다.

이 불변식 덕분에 `front`가 항상 현재 window의 최대값이다.
각 index는 한 번 들어오고, 많아야 한 번 나가므로 전체는 상각 `O(n)`이다.

| 구조 | 유지하는 것 | 전형적 시간복잡도 | 전형적 공간복잡도 | 이 문제와의 궁합 |
|---|---|---|---|---|
| Monotonic deque | 만료되지 않았고, 더 약한 후보에게 지배되지 않은 index들 | `O(n)` | `O(k)` | 가장 직접적 |
| Heap + lazy deletion | 현재/과거 원소를 우선순위순으로 쌓고, top이 stale이면 나중에 버림 | 순수 lazy deletion이면 worst-case `O(n log n)` | worst-case `O(n)` | 가능하지만 덜 특화됨 |

많이 헷갈리는 지점 하나:
인터뷰 해설에서 heap 풀이를 `O(n log k)`라고 뭉뚱그려 쓰는 경우가 많다.
하지만 **표준 binary heap에 stale entry를 그냥 남겨 두는 lazy deletion**이라면, stale한 작은 값들이 힙 아래에 오래 묻혀서 heap 크기가 `k`를 넘을 수 있다.

예를 들어 증가 수열 `1, 2, 3, 4, 5, ...`에 최대값 heap을 쓰면:

- 루트는 늘 최신의 큰 값이라 valid하다.
- 오래전에 만료된 작은 값들은 루트까지 올라올 기회가 없어 밑에 계속 남는다.
- 그래서 heap size는 입력 길이만큼 커질 수 있다.

즉 `PriorityQueue<(value, index)>` 하나에 stale top skip만 붙인 풀이는
deque처럼 `O(k)` 공간이라고 생각하면 안 된다.

## 2. heap + lazy deletion은 정확히 무엇을 하는가

window extrema에서 말하는 heap lazy deletion은 보통 이 패턴이다.

1. `(value, index)`를 heap에 넣는다.
2. window 밖으로 나간 원소를 즉시 삭제하지 않는다.
3. 대신 `peek()`가 stale index면 `poll()`로 버린다.
4. top이 살아 있을 때만 그 값을 답으로 쓴다.

최대값 Java 스케치는 이렇게 생긴다.

```java
PriorityQueue<int[]> pq =
    new PriorityQueue<>((a, b) -> Integer.compare(b[0], a[0]));

for (int i = 0; i < nums.length; i++) {
    pq.offer(new int[]{nums[i], i});

    while (!pq.isEmpty() && pq.peek()[1] <= i - k) {
        pq.poll(); // top이 stale이면 그때 버린다
    }

    if (i >= k - 1) {
        answer.add(pq.peek()[0]);
    }
}
```

이 방식이 성립하는 이유는 단 하나다.

- **답으로 읽는 위치가 top 하나뿐**이므로, top이 stale일 때만 청소해도 정답은 맞출 수 있다.

하지만 deque와 비교하면 약점도 분명하다.

- stale entry가 top 아래에 오래 묻힐 수 있다.
- comparator 방향을 잘못 잡기 쉽다.
- duplicate와 expiration을 값만으로 관리하면 바로 틀린다.
- "정답 읽기 전 cleanup" 순서를 빼먹으면 expired max/min을 그대로 출력한다.

## 3. 언제 heap 쪽이 그래도 낫나

고정 길이 window max/min만 보면 deque가 더 좋다.
그럼에도 heap 쪽을 고를 수 있는 상황은 있다.

### 1. 이미 generic priority queue 흐름으로 코드를 맞추고 있을 때

문제 풀이 플랫폼이나 팀 템플릿이 `PriorityQueue` 중심이고, 성능 여유가 충분하면 heap 풀이도 실용적일 수 있다.
특히 monotonic deque invariant가 아직 손에 안 익은 학습 초반에는 heap 풀이가 더 친숙하게 느껴질 수 있다.

다만 이건 **쉽다기보다 익숙하다**에 가깝다.
실수 포인트는 deque보다 오히려 많다.

### 2. 진짜 delete-by-id가 되는 ordered structure를 이미 가지고 있을 때

indexed heap, balanced BST, multiset처럼 "leaving element를 실제로 지울 수 있는 구조"가 있으면 이야기가 조금 달라진다.
이 경우는 pure lazy deletion이 아니라, 더 일반적인 ordered-set 풀이에 가깝다.

즉 비교 대상은 사실상:

- monotonic deque
- plain heap + lazy deletion
- real delete가 되는 ordered structure

이 셋을 따로 봐야 한다.

### 3. FIFO window가 아니라 삭제 패턴이 일반화될 때

monotonic deque는 "나가는 원소가 항상 oldest"라는 전제가 깨지면 바로 힘이 약해진다.
삭제가 임의 위치에서 일어나면 deque의 front/back 규칙만으로는 유지가 안 된다.
그때는 heap이나 tree 쪽이 더 일반적이다.

## 4. 가장 자주 틀리는 edge case

| 실수 | 왜 틀리나 | 바로 잡는 기준 |
|---|---|---|
| 값만 저장하고 index를 저장하지 않는다 | duplicate가 있을 때 어떤 원소가 만료됐는지 구분할 수 없다 | deque든 heap이든 sliding window extrema는 보통 `index`를 저장한다 |
| 답을 읽기 전에 stale cleanup을 안 한다 | 이미 window 밖으로 나간 최대/최소를 그대로 출력한다 | `peekFirst()`나 `peek()`를 답으로 쓰기 전에 먼저 만료 정리를 한다 |
| heap에서 `(value)`만으로 delayed-delete를 센다 | 같은 값이 여러 개면 어느 index가 나갔는지 구분이 안 된다 | extrema heap은 `(value, index)`로 넣고 index stale check를 한다 |
| max/min comparator 방향을 뒤집는다 | Java `PriorityQueue` 기본은 min-heap이라 최대값 문제에서 그대로 쓰면 틀린다 | max면 reverse comparator, min이면 natural/comparingInt를 쓴다 |
| deque에서 expiry 경계를 하나 밀린다 | `i - k + 1`이 window start인데 `<`, `<=`를 뒤섞으면 한 칸 오래 남거나 빨리 제거한다 | `index < start` 또는 같은 뜻의 `index <= i - k`를 일관되게 쓴다 |
| deque의 duplicate 처리 규칙을 이해하지 않고 `<`와 `<=`를 섞는다 | 동치는 둘 다 맞을 수 있지만, mental model이 흔들리면 expiration reasoning이 꼬인다 | max deque는 `<=`면 "새 equal 값이 옛 equal 값을 대체", `<`면 둘 다 유지라고 의식적으로 선택한다 |
| heap lazy deletion 풀이를 `O(k)` 공간으로 단정한다 | stale entry가 밑에 묻히면 heap이 `k`보다 훨씬 커질 수 있다 | pure lazy deletion이면 worst-case `O(n)` 공간까지 열어 둔다 |

duplicate 비교는 특히 자주 헷갈린다.

- 최대값 deque에서 `nums[dq.back] <= nums[i]`를 쓰면 **새로운 동점 값이 기존 동점 값을 대체**한다.
- `nums[dq.back] < nums[i]`를 쓰면 **동점 둘 다 유지**한다.

둘 다 정답은 맞을 수 있다.
하지만 어떤 규칙을 쓸지 정한 뒤 만료 reasoning까지 그 규칙에 맞춰 일관되게 써야 한다.

## 5. 최소 검증 세트

아래 입력은 구현 버그를 빨리 드러낸다.

| 목적 | 입력 | 기대 출력 |
|---|---|---|
| `k = 1` sanity check | `nums = [5, 4, 3], k = 1` | `[5, 4, 3]` |
| duplicate 처리 | `nums = [2, 2, 2, 2], k = 2` | `[2, 2, 2]` |
| stale cleanup 순서 | `nums = [9, 1, 2], k = 2` | `[9, 2]` |
| heap buried stale entry 직관 | `nums = [1, 2, 3, 4, 5], k = 2` | 정답은 `[2, 3, 4, 5]`이지만, pure lazy heap 내부에는 stale 작은 값이 계속 남을 수 있다 |

마지막 케이스는 correctness보다 complexity 감각을 보는 용도다.
정답은 맞아도 heap size가 작게 유지된다고 착각하기 쉽다.

## 6. 면접에서 한 문장으로 답하면

> sliding-window max/min처럼 window가 FIFO로 밀리고 extrema 하나만 필요하면 monotonic deque가 기본입니다. heap + lazy deletion도 가능하지만 stale entry cleanup, duplicate/index 관리, 그리고 pure lazy deletion의 worst-case `O(n)` space를 같이 감수해야 합니다.

## 한 줄 정리

`고정 길이 window extrema 하나`라는 signal이 보이면 deque를 먼저 고르고, heap은 generic priority queue 흐름이 꼭 필요할 때만 의식적으로 선택하는 편이 안전하다.
