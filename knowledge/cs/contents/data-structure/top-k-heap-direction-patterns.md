# Top-K Heap Direction Patterns

> 한 줄 요약: Java에서 `kth-largest`, `streaming top-k`, `median` 문제는 "루트가 무엇을 대표해야 하느냐"를 먼저 정하면 min-heap / max-heap 방향이 자연스럽게 나온다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [힙 기초](./heap-basics.md)
> - [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)
> - [Heap Variants](./heap-variants.md)
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
> - [Top-k Streaming and Heavy Hitters](../algorithm/top-k-streaming-heavy-hitters.md)
>
> retrieval-anchor-keywords: top-k heap direction, top k heap direction, top-k heap direction patterns, kth largest min heap, kth largest priority queue java, kth largest heap direction, streaming top-k heap java, streaming top k heap java, top-k frequent min heap java, median two heaps java, median priorityqueue java, min heap vs max heap top k, top-k largest min heap why, top-k smallest max heap, lower half max heap upper half min heap, two heap median pattern, java priorityqueue reverseOrder median, java priorityqueue heap direction, boundary heap pattern, weak boundary heap, 자바 kth largest 최소 힙, 자바 top-k 힙 방향, 자바 우선순위 큐 방향, 자바 median 두 힙, 최소 힙 최대 힙 선택, k번째 큰 수 힙, 스트리밍 top-k 힙, 중앙값 두 힙

## 먼저 정할 질문

힙 방향을 고를 때 문제 이름만 보면 자주 틀린다.
`kth-largest`라는 이름 때문에 max-heap을 떠올리기 쉽고, `median`도 한 개의 힙으로 해결하려고 하다가 꼬이기 쉽다.

먼저 이 질문부터 한다.

> "루트에서 바로 보고 싶은 값이 무엇인가?"

| 문제 | 루트가 대표해야 하는 값 | 보통 선택 | Java 선언 |
|---|---|---|---|
| `kth-largest`, `top-k largest` | 현재 `top-k` 안에서 가장 작은 값 | 크기 `k`의 min-heap | `new PriorityQueue<>()` |
| `kth-smallest`, `top-k smallest` | 현재 `bottom-k` 안에서 가장 큰 값 | 크기 `k`의 max-heap | `new PriorityQueue<>(Comparator.reverseOrder())` |
| median의 lower half | 아래 절반의 최댓값 | max-heap | `new PriorityQueue<>(Comparator.reverseOrder())` |
| median의 upper half | 위 절반의 최솟값 | min-heap | `new PriorityQueue<>()` |

핵심은 "가장 강한 후보"를 루트에 두는지가 아니라, **새 값이 들어왔을 때 비교해야 할 경계값을 루트에 두는가**다.

## 1. `kth-largest`는 왜 min-heap이 기본인가

`kth-largest`의 표준 패턴은 **크기 `k`의 min-heap**이다.

- 힙 안에는 "지금까지 본 값 중 상위 `k`개"만 남긴다.
- 루트는 그 `k`개 중 가장 작은 값이다.
- 그래서 루트가 바로 "`현재 kth-largest 경계`"가 된다.

```java
import java.util.PriorityQueue;

public int findKthLargest(int[] nums, int k) {
    PriorityQueue<Integer> topK = new PriorityQueue<>();

    for (int num : nums) {
        if (topK.size() < k) {
            topK.offer(num);
            continue;
        }

        if (num > topK.peek()) {
            topK.poll();
            topK.offer(num);
        }
    }

    return topK.peek();
}
```

왜 max-heap이 덜 자연스러운지도 같이 보자.

- max-heap 루트는 "가장 큰 값"이다.
- 하지만 새 값이 `top-k`에 들어갈지 판단하려면 "현재 `top-k` 중 가장 약한 값"을 봐야 한다.
- 그 경계는 max-heap 루트가 아니라 **min-heap 루트**에 있다.

즉 `kth-largest`는 "큰 값을 뽑는 문제"처럼 보여도, 유지 단계에서는 **작은 경계를 감시하는 min-heap**이 더 잘 맞는다.

### max-heap이 맞는 순간도 있다

배치 데이터 전체를 이미 들고 있고, 가장 큰 값부터 여러 번 꺼내야 하면 full max-heap도 가능하다.
다만 이것은 "`전체 후보를 다 보관하고 큰 것부터 소비`"하는 패턴이고, `streaming`이나 `O(k)` 공간 유지와는 결이 다르다.

## 2. streaming top-k는 "우승자 집합의 약한 경계"를 루트에 둔다

스트림에서 `top-k largest values`를 계속 유지할 때도 방향은 같다.
여전히 필요한 것은 "현재 우승자들 중 가장 약한 값"이기 때문이다.

- 큰 값 상위 `k`개 유지: 크기 `k`의 min-heap
- 작은 값 하위 `k`개 유지: 크기 `k`의 max-heap

이때 초보자가 자주 헷갈리는 지점은 "출력은 큰 순서인데 유지용 힙은 왜 min-heap인가?"다.

답은 간단하다.

- **유지 단계**에서는 경계 비교가 중요하다.
- **출력 단계**에서만 정렬 순서가 중요하다.

즉 결과를 큰 순서로 보여주고 싶어도, 유지용 자료구조는 min-heap일 수 있다.
출력은 마지막에 정렬하거나 복사본에서 `poll()` 하면 된다.

### 빈도 기반 streaming top-k도 방향은 같다

`top-k frequent items`, `heavy hitters`처럼 값 자체가 아니라 **빈도**로 경쟁할 때도 보통 min-heap을 쓴다.

- 힙 안에는 "현재 상위 `k`개 key"가 들어 있다.
- 루트는 그중 **빈도가 가장 낮은 key**다.
- 새 후보의 `count`가 루트보다 크면 교체한다.

```java
import java.util.Comparator;
import java.util.PriorityQueue;

record Entry(String item, long count) {}

PriorityQueue<Entry> topKByCount =
    new PriorityQueue<>(Comparator.comparingLong(Entry::count));
```

여기서 바뀌는 것은 heap 방향이 아니라 **비교 기준 필드**다.

- value top-k: 값으로 비교
- frequency top-k: count로 비교

동점에서 deterministic order가 필요하면 `thenComparing(...)`을 추가한다.

## 3. median은 힙 하나가 아니라 두 개가 필요하다

median 문제는 top-k와 다르게 경계가 두 개다.

- 아래 절반에서는 **가장 큰 값**을 바로 봐야 한다.
- 위 절반에서는 **가장 작은 값**을 바로 봐야 한다.

그래서 방향이 다른 힙 두 개를 같이 쓴다.

- lower half: max-heap
- upper half: min-heap

```java
import java.util.Comparator;
import java.util.PriorityQueue;

class MedianFinder {
    private final PriorityQueue<Integer> lower =
        new PriorityQueue<>(Comparator.reverseOrder());
    private final PriorityQueue<Integer> upper =
        new PriorityQueue<>();

    public void addNum(int num) {
        if (lower.isEmpty() || num <= lower.peek()) {
            lower.offer(num);
        } else {
            upper.offer(num);
        }

        if (lower.size() > upper.size() + 1) {
            upper.offer(lower.poll());
        } else if (upper.size() > lower.size()) {
            lower.offer(upper.poll());
        }
    }

    public double findMedian() {
        if (lower.size() == upper.size()) {
            return ((long) lower.peek() + upper.peek()) / 2.0;
        }
        return lower.peek();
    }
}
```

이 패턴의 invariant는 두 가지다.

- `lower.size() == upper.size()` 또는 `lower.size() == upper.size() + 1`
- `lower`의 모든 값 `<= upper`의 모든 값

이렇게 하면

- 원소 개수가 홀수일 때는 `lower.peek()`가 median
- 짝수일 때는 `lower.peek()`와 `upper.peek()` 평균이 median

즉 median은 "큰 것 하나"나 "작은 것 하나"가 아니라 **양쪽 경계 두 개**를 동시에 봐야 하므로 max-heap + min-heap 조합이 필요하다.

## 4. 헷갈릴 때 쓰는 선택 공식

아래 세 줄로 거의 정리된다.

1. `top-k largest`, `kth-largest`면 "우승자 집합의 최약체"가 루트여야 하므로 min-heap
2. `top-k smallest`, `kth-smallest`면 "생존 집합의 최강자"가 루트여야 하므로 max-heap
3. `median`이면 아래 절반의 최대와 위 절반의 최소를 동시에 봐야 하므로 max-heap + min-heap

Java 선언만 다시 적으면 이렇다.

```java
PriorityQueue<Integer> minHeap = new PriorityQueue<>();
PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Comparator.reverseOrder());
```

문제 이름보다 **루트가 경계값인지, 답 후보인지, 절반 경계인지**를 먼저 보면 방향 실수가 크게 줄어든다.

## 한 줄 정리

Java heap 방향 선택은 "`큰 값을 원하니 max-heap`"처럼 이름으로 고르는 게 아니라, **루트가 어떤 경계값을 즉시 보여줘야 하는가**로 고르는 것이 핵심이다.
