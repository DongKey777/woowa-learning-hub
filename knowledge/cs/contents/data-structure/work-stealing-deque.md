# Work-Stealing Deque

> 한 줄 요약: Work-Stealing Deque는 작업을 만든 owner thread는 한쪽 끝에서 빠르게 push/pop하고, idle worker는 반대쪽 끝에서 steal하도록 설계해 병렬 스케줄러의 load balancing 비용을 낮추는 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Ring Buffer](./ring-buffer.md)
> - [Lock-Free MPSC Queue](./lock-free-mpsc-queue.md)
> - [Michael-Scott Lock-Free Queue](./michael-scott-lock-free-queue.md)
> - [Heap Variants](./heap-variants.md)
> - [Hierarchical Timing Wheel](./hierarchical-timing-wheel.md)

> retrieval-anchor-keywords: work stealing deque, chase lev deque, fork join pool, task scheduler, owner push pop, steal from head, load balancing, parallel runtime, bounded deque, scheduler queue, fork join work queue

## 핵심 개념

병렬 실행기에서 가장 단순한 구조는 중앙 task queue 하나를 두는 것이다.  
하지만 worker 수가 늘수록 병목은 "어떤 task를 고르느냐"보다 **모두가 같은 queue를 두드린다**는 데서 온다.

Work-Stealing Deque는 이 문제를 다음처럼 푼다.

- 각 worker가 자기 전용 deque를 가진다
- owner는 보통 tail 쪽에서 push/pop 한다
- 일이 없는 다른 worker는 head 쪽에서 steal 한다

즉 fast path는 대부분 single-thread local이고,  
load balancing이 필요할 때만 cross-thread synchronization을 쓴다.

## 깊이 들어가기

### 1. 왜 중앙 queue가 먼저 무너지나

중앙 MPMC queue는 공정해 보이지만 contention이 금방 커진다.

- 모든 producer가 enqueue 경쟁
- 모든 worker가 dequeue 경쟁
- cache line bouncing
- lock 또는 CAS hotspot

task가 짧을수록 queue 병목이 더 두드러진다.  
계산보다 scheduler가 비싸지기 때문이다.

### 2. owner local fast path가 핵심이다

work-stealing deque에서 owner는 보통 자기 deque tail을 독점적으로 다룬다.

- 새 task spawn: `pushBottom`
- 바로 이어서 실행: `popBottom`
- 남의 worker가 훔칠 때만 `stealTop`

이 구조는 깊이 우선 실행 감각을 만든다.

- spawn한 하위 task를 바로 이어서 처리하기 쉽다
- cache locality가 좋아진다
- steal은 상대적으로 오래된 큰 작업을 가져가기 쉽다

즉 owner는 locality를, thief는 parallelism을 챙긴다.

### 3. Chase-Lev 스타일 deque가 자주 언급되는 이유

실무와 논문에서 자주 나오는 구현이 Chase-Lev 계열이다.

- 배열 기반 bounded deque
- `bottom`은 owner가 주로 갱신
- `top`은 thief가 CAS로 갱신
- 마지막 원소 하나를 두고 owner와 thief가 경합할 수 있다

어려운 지점은 여기다.

- empty/full 판정
- resize 중 steal
- memory ordering
- ABA와 stale read

즉 아이디어는 단순하지만, **정확한 lock-free 구현은 상당히 까다롭다**.

### 4. 왜 scheduler에 잘 맞나

fork-join, parallel DFS, recursive divide-and-conquer는 task가 계속 파생된다.  
이런 워크로드에서 중앙 priority queue보다 각 worker local deque가 더 자연스럽다.

대표 패턴:

- owner는 자기 하위 문제를 계속 밀고 들어감
- idle worker가 위쪽 task 하나를 훔쳐 병렬도를 늘림

이때 steal 대상이 "상대적으로 큰 미처리 작업"이 되기 쉬워  
세분화된 작은 task를 한꺼번에 뺏는 것보다 효율적이다.

### 5. backend에서 주의할 점

work-stealing deque는 만능 queue가 아니다.

- strict FIFO가 아니다
- 우선순위 보장이 없다
- delayed task 스케줄링에는 직접 맞지 않는다
- starvation, pinning, long-running task가 있으면 균형이 깨질 수 있다

또 CPU-bound fork-join에는 잘 맞지만, I/O blocking task가 섞이면  
worker가 deque를 오래 점유해 steal만으로는 회복이 어려울 수 있다.

그래서 실무 런타임은 보통 이것도 함께 둔다.

- global fallback queue
- external submit queue
- blocking task 보상 스레드
- steal 실패 시 backoff

## 실전 시나리오

### 시나리오 1: fork-join 계산

정렬, 그래프 탐색, recursive batch 처리처럼 task가 계속 쪼개지는 워크로드는  
work stealing이 locality와 병렬도를 같이 챙기기 좋다.

### 시나리오 2: 서버 내부 병렬 파이프라인

한 요청에서 fan-out된 subtask를 로컬 worker가 먼저 처리하고,  
남는 CPU가 있을 때만 다른 worker가 가져가게 하면 중앙 queue contention을 줄일 수 있다.

### 시나리오 3: scheduler의 tail latency 문제

task가 매우 짧고 수가 많으면 중앙 queue lock보다 steal deque가 유리하다.  
반대로 task가 길고 blocking이 많으면 queue보다 worker 관리가 병목이 된다.

### 시나리오 4: 부적합한 경우

엄격한 우선순위, deadline ordering, delayed job dispatch가 중요하면  
heap이나 timing wheel이 더 맞다.

## 코드로 보기

```java
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReferenceArray;

public class WorkStealingDeque<T> {
    private final AtomicReferenceArray<T> buffer;
    private final AtomicInteger top = new AtomicInteger(0);
    private int bottom = 0; // owner thread only

    public WorkStealingDeque(int capacity) {
        this.buffer = new AtomicReferenceArray<>(capacity);
    }

    public void pushBottom(T task) {
        int b = bottom;
        buffer.set(b % buffer.length(), task);
        bottom = b + 1;
    }

    public T popBottom() {
        int b = bottom - 1;
        bottom = b;
        int t = top.get();

        if (t > b) {
            bottom = t;
            return null;
        }

        T task = buffer.get(b % buffer.length());
        if (t == b) {
            if (!top.compareAndSet(t, t + 1)) {
                task = null;
            }
            bottom = t + 1;
        }
        return task;
    }

    public T stealTop() {
        int t = top.get();
        int b = bottom;
        if (t >= b) {
            return null;
        }

        T task = buffer.get(t % buffer.length());
        if (top.compareAndSet(t, t + 1)) {
            return task;
        }
        return null;
    }
}
```

이 코드는 개념 설명용 스케치다.  
실전 구현은 resize, memory fence, stale slot clearing, false sharing까지 고려해야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Work-Stealing Deque | owner local fast path가 빠르고 load balancing이 자연스럽다 | 정확한 구현이 복잡하고 strict ordering이 없다 | fork-join, parallel runtime, CPU-bound scheduler |
| 중앙 MPMC Queue | 모델이 단순하고 외부 submit이 쉽다 | contention hotspot이 생기기 쉽다 | worker 수가 작거나 공정성이 더 중요할 때 |
| Ring Buffer | bounded queue로 예측 가능성이 좋다 | 다수 worker load balancing은 별도 설계가 필요하다 | 단순 producer/consumer 파이프라인 |
| Priority Queue | deadline/priority가 명확하다 | 병렬 worker local fast path에는 약하다 | 우선순위와 earliest deadline이 중요할 때 |

핵심 질문은 "작업을 공평하게 나눌 것인가"보다 "대부분의 enqueue/dequeue를 local로 끝낼 수 있는가"다.

## 꼬리질문

> Q: work-stealing deque에서 왜 owner와 thief가 반대쪽 끝을 쓰나요?
> 의도: contention 회피와 locality 이해 확인
> 핵심: owner의 빠른 local 연산을 보장하고, thief는 충돌을 최소화하며 남는 일을 가져가기 위해서다.

> Q: 왜 중앙 queue 하나보다 빠를 수 있나요?
> 의도: 스케줄링 병목을 자료구조 관점으로 보는지 확인
> 핵심: 대부분의 연산이 worker 로컬에서 끝나고, cross-thread 동기화는 steal 시점에만 필요하기 때문이다.

> Q: 언제 priority queue가 더 맞나요?
> 의도: 스케줄링 요구사항을 구분하는지 확인
> 핵심: deadline ordering이나 strict priority가 중요할 때다.

## 한 줄 정리

Work-Stealing Deque는 병렬 scheduler에서 대부분의 작업 조작을 worker 로컬로 처리하고, 유휴 worker만 반대쪽 끝에서 steal하게 해 contention과 load imbalance를 함께 줄이는 자료구조다.
