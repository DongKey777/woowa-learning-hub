# Calendar Queue

> 한 줄 요약: Calendar Queue는 미래 이벤트 시간을 bucket으로 나눠 담는 priority queue 변형으로, deadline 분포가 맞을 때 heap보다 더 싼 평균 이벤트 스케줄링을 노리는 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Heap Variants](./heap-variants.md)
> - [Hierarchical Timing Wheel](./hierarchical-timing-wheel.md)
> - [Radix Heap](./radix-heap.md)
> - [Timing Wheel Variants and Selection](./timing-wheel-variants-and-selection.md)
> - [Work-Stealing Deque](./work-stealing-deque.md)

> retrieval-anchor-keywords: calendar queue, bucketed priority queue, event scheduler, future event list, discrete event simulation, adaptive bucket width, deadline queue, timer queue, average O1 scheduler, delayed task structure

## 핵심 개념

heap은 가장 이른 deadline을 정확히 꺼내는 데 강하다.  
하지만 deadline이 많고 분포가 꽤 고르게 퍼져 있으면, 매번 `O(log n)` 정렬 비용이 아깝기도 하다.

Calendar Queue는 시간을 달력 칸처럼 bucket으로 나눈다.

- 각 bucket은 시간 구간 하나를 뜻한다
- 이벤트는 해당 구간 bucket에 들어간다
- dequeue는 현재 달력 위치부터 앞으로 훑으며 가장 이른 이벤트를 찾는다

즉 timing wheel과 비슷하게 bucket 사고를 쓰지만,  
**priority queue처럼 임의 deadline ordering을 더 자연스럽게 다루려는 구조**다.

## 깊이 들어가기

### 1. heap과 timing wheel 사이의 어딘가다

Calendar Queue를 이해하는 쉬운 방법은 양쪽과 비교하는 것이다.

- heap: 정렬은 정확하지만 삽입/삭제가 비쌈
- timing wheel: bucket은 싸지만 tick/round 관점이 강함
- calendar queue: 시간 bucket을 쓰되, event-time ordered queue로 사용

즉 "버킷화된 우선순위 큐"에 가깝다.

### 2. bucket width가 성능을 좌우한다

Calendar Queue의 가장 중요한 파라미터는 bucket width다.

- 너무 좁으면 bucket이 너무 많이 비어 있음
- 너무 넓으면 bucket 내부 비교가 많아짐

이상적으로는 bucket당 이벤트 수가 너무 많지도 적지도 않아야 한다.  
그래서 많은 구현이 workload를 보며 width와 bucket 수를 재조정한다.

### 3. 왜 평균 O(1) 같은 얘기가 나오나

deadline 분포가 구조의 가정에 잘 맞으면,

- enqueue는 bucket index 계산 후 append
- dequeue는 근처 bucket을 조금만 훑고 끝남

그래서 평균적으로 매우 싸게 동작할 수 있다.  
하지만 이건 **분포 가정이 맞을 때** 이야기다.

burst, skew, 긴 idle gap이 많으면 bucket 탐색 비용이 커지고  
heap보다 나을 이유가 줄어든다.

### 4. timing wheel과 어디서 갈리나

둘 다 시간을 bucket으로 나눈다는 점은 비슷하다.  
하지만 운영 감각은 다르다.

- timing wheel: tick/round/cascade 중심
- calendar queue: event time bucket width 중심

timing wheel은 timeout 관리처럼 "대략 이 시각쯤"이 자연스러운 곳에 잘 맞고,  
calendar queue는 priority queue 대체 관점에서 discrete-event scheduler에 더 가깝다.

### 5. backend에서 쓸 때 주의할 점

실무 workload는 deadline 분포가 자주 바뀐다.

- 특정 시각에 retry burst
- 동일한 delay 정책으로 같은 bucket에 몰림
- 장시간 비었다가 갑자기 이벤트 폭증

이 경우 calendar queue는 재조정이 필요하고,  
그 비용과 복잡도 때문에 heap이나 timing wheel이 더 단순한 선택이 되기도 한다.

즉 calendar queue는 강력하지만, **분포 적합성이 있어야 빛난다**.

## 실전 시나리오

### 시나리오 1: discrete event scheduler

이벤트 시간이 계속 증가하며 비교적 고르게 퍼진 시뮬레이션/스케줄러에서는  
calendar queue가 heap보다 가볍게 동작할 수 있다.

### 시나리오 2: delayed retry orchestration

retry deadline이 일정 범위 안에 넓게 퍼지고,  
strict nanosecond 정밀도보다 throughput이 중요하다면 검토할 수 있다.

### 시나리오 3: 부적합한 deadline burst

동일한 만료 시각에 이벤트가 몰리면 bucket 내부 mini-heap이나 정렬 비용이 커져  
calendar queue 장점이 줄어든다.

### 시나리오 4: 부적합한 경우

deadline 수가 적거나, 분포가 너무 변동적이거나,  
운영 단순성이 더 중요하면 binary heap이 더 낫다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class CalendarQueue {
    private final List<List<Event>> buckets;
    private final long bucketWidth;
    private long cursorTime = 0L;
    private int cursorBucket = 0;

    public CalendarQueue(int bucketCount, long bucketWidth) {
        this.bucketWidth = bucketWidth;
        this.buckets = new ArrayList<>(bucketCount);
        for (int i = 0; i < bucketCount; i++) {
            buckets.add(new ArrayList<>());
        }
    }

    public void offer(long deadline, Runnable task) {
        int bucket = bucketIndex(deadline);
        buckets.get(bucket).add(new Event(deadline, task));
    }

    public Runnable poll() {
        for (int scanned = 0; scanned < buckets.size(); scanned++) {
            List<Event> bucket = buckets.get(cursorBucket);
            if (!bucket.isEmpty()) {
                Event next = bucket.stream()
                        .min(Comparator.comparingLong(event -> event.deadline))
                        .orElseThrow();
                bucket.remove(next);
                cursorTime = next.deadline;
                return next.task;
            }
            cursorBucket = (cursorBucket + 1) % buckets.size();
            cursorTime += bucketWidth;
        }
        return null;
    }

    private int bucketIndex(long deadline) {
        return (int) Math.floorMod(deadline / bucketWidth, buckets.size());
    }

    private record Event(long deadline, Runnable task) {}
}
```

이 코드는 calendar queue의 bucket 감각만 보여준다.  
실전 구현은 bucket width 재조정, empty run skip, bucket 내부 ordering 최적화가 핵심이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Calendar Queue | deadline 분포가 맞으면 평균적으로 매우 싸게 동작할 수 있다 | bucket width tuning과 workload skew 대응이 어렵다 | event scheduler, discrete-event queue |
| Binary Heap | 구현이 단순하고 worst-case가 예측 가능하다 | 많은 event에서 정렬 비용이 누적된다 | 일반적인 priority queue, timer queue |
| Hierarchical Timing Wheel | timeout churn에 강하고 대량 만료 처리 비용이 낮다 | tick 기반 근사와 cascade 복잡도가 있다 | idle timeout, retry, lease expiry |
| Delay Queue | 쓰기 쉬운 blocking 모델을 제공한다 | 내부 비용은 heap 계열과 크게 다르지 않다 | 단일 JVM scheduler를 빠르게 만들 때 |

중요한 질문은 "정확히 가장 이른 것"보다 "deadline 분포를 bucket으로 잘 나눌 수 있는가"다.

## 꼬리질문

> Q: calendar queue가 heap보다 빠를 수 있는 조건은 무엇인가요?
> 의도: 분포 가정 기반 평균 성능 이해 확인
> 핵심: deadline이 bucket에 비교적 고르게 분포하고, bucket width가 적절할 때다.

> Q: timing wheel과 가장 큰 차이는 무엇인가요?
> 의도: 둘 다 bucket 구조라는 점을 넘어 operational model을 구분하는지 확인
> 핵심: timing wheel은 tick/round 중심이고, calendar queue는 event-time bucket priority queue에 더 가깝다.

> Q: 왜 실무에서 항상 calendar queue를 쓰지 않나요?
> 의도: 평균 성능과 운영 복잡도 균형 이해 확인
> 핵심: workload skew와 bucket tuning 실패 시 장점이 빠르게 사라지기 때문이다.

## 한 줄 정리

Calendar Queue는 미래 deadline을 시간 bucket으로 나눈 priority queue 변형으로, 분포가 맞는 scheduler에서는 heap보다 더 싼 평균 비용을 얻을 수 있지만 tuning 감각이 필요하다.
