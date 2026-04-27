# Ring Buffer

> 한 줄 요약: Ring Buffer는 고정 크기 배열을 원형으로 써서, 큐 연산을 빠르고 예측 가능하게 만드는 자료구조다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: ring buffer basics, ring buffer beginner, ring buffer intro, data structure basics, beginner data structure, 처음 배우는데 ring buffer, ring buffer 입문, ring buffer 기초, what is ring buffer, how to ring buffer
> 관련 문서:
> - [응용 자료 구조 개요](./applied-data-structures-overview.md)
> - [Queue (큐)](./basic.md#queue-큐)
> - [Circular Queue vs Ring Buffer Primer](./circular-queue-vs-ring-buffer-primer.md)
> - [Bounded Queue Policy Primer](./bounded-queue-policy-primer.md)
> - [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)
> - [Lock-Free MPSC Queue](./lock-free-mpsc-queue.md)
> - [Bounded MPMC Queue](./bounded-mpmc-queue.md)
> - [Sequencer-Based Ring Buffer Coordination](./sequencer-based-ring-buffer-coordination.md)
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
> - [Work-Stealing Deque](./work-stealing-deque.md)
> - [Hierarchical Timing Wheel](./hierarchical-timing-wheel.md)
> - [Amortized Analysis Pitfalls](../algorithm/amortized-analysis-pitfalls.md)

> retrieval-anchor-keywords: ring buffer, circular buffer, circular queue vs ring buffer, systems ring buffer, head tail, front rear, wraparound, producer consumer, bounded queue, fixed capacity queue, full queue policy, log buffer, logging ring buffer, telemetry buffer, observability buffer, audio ring buffer, real time audio buffer, producer consumer pipeline, staged pipeline buffer, reject policy, overwrite policy, blocking queue policy, backpressure, spsc queue, mpsc queue, bounded mpmc queue, sequencer ring buffer, bounded buffer, lock-free spsc

## 핵심 개념

Ring Buffer는 배열의 끝에 도달하면 다시 처음으로 돌아가서 쓰는 **원형 큐**다.

다만 여기서 말하는 `ring buffer`는 면접에서 자주 나오는 `circular queue`와 강조점이 조금 다르다.
`circular queue`가 `Front/Rear/isFull` 같은 queue 인터페이스 설계에 가깝다면, `ring buffer`는 producer/consumer, overwrite, backpressure, 예측 가능한 지연시간 같은 **시스템 운영 제약**을 더 강하게 본다.
꽉 찼을 때 `reject`, `overwrite`, `blocking`, `backpressure` 중 무엇이 맞는지부터 빠르게 비교하려면 [Bounded Queue Policy Primer](./bounded-queue-policy-primer.md)를 먼저 보는 편이 좋다.

핵심 아이디어는 간단하다.

- 배열 크기는 고정한다.
- `head`는 읽을 위치, `tail`은 쓸 위치를 가리킨다.
- 인덱스는 `% capacity` 또는 조건 분기로 감싼다.

이 구조는 다음 상황에서 특히 좋다.

- 메모리 사용량을 예측해야 할 때
- 할당/해제를 줄이고 싶을 때
- producer/consumer 흐름이 많을 때

## 깊이 들어가기

### 1. head / tail을 어떻게 해석할까

Ring Buffer는 보통 `head`와 `tail`만으로 상태를 표현한다.

대표적인 두 방식이 있다.

- 하나를 비워 두는 방식: empty와 full을 쉽게 구분
- `size`를 따로 두는 방식: 공간 활용이 더 좋음

실무에서는 "가득 찼는지" 판별이 중요하므로, 정책을 명확히 정해야 한다.

### 2. overwrite vs reject

버퍼가 꽉 찼을 때의 정책도 중요하다.

- reject: 새 데이터를 버린다
- overwrite: 가장 오래된 데이터를 덮어쓴다

producer가 기다릴 수 있는지, 상류 전체를 늦출지까지 포함해 정책 축을 넓게 보고 싶다면 [Bounded Queue Policy Primer](./bounded-queue-policy-primer.md)로 이어서 읽으면 된다.

로그나 센서 스트림처럼 최신값이 더 중요하면 overwrite가 맞고,
결제 이벤트처럼 유실이 치명적이면 reject나 backpressure가 맞다.

### 3. 왜 예측 가능성이 중요한가

Ring Buffer는 보통 동적 resize가 없다.

- 평균적으로 빠른 것이 아니라
- 매 연산이 거의 일정한 비용이라는 점이 강점이다

그래서 tail latency가 중요한 경로에서 좋다.

### 4. backend에서의 활용 감각

Ring Buffer는 큐 이상의 의미가 있다.

- 로그 수집 버퍼
- Kafka-like producer/consumer 내부 큐
- 이벤트 루프 작업 목록
- 고정 크기 샘플링 윈도우

### 5. use-case decision matrix

Ring Buffer를 볼 때는 "원형 배열인가?"보다 "어떤 운영 제약을 가장 먼저 만족해야 하나?"를 먼저 묻는 편이 정확하다.

## 깊이 들어가기 (계속 2)

| 시나리오 | 먼저 보는 축 | 기본 라우팅 | full/slow-path에서 먼저 고를 정책 | 다음 문서 |
|---|---|---|---|---|
| logging | burst 흡수, 최근 문맥 유지, flush thread 수 | producer가 여러 개면 `MPSC -> single flusher`, 하나면 plain ring도 충분 | 디버그 tail이면 `overwrite`/`reject`, 감사 로그면 ring을 staging으로만 두고 `backpressure`나 durable sink 필요 | [Bounded Queue Policy Primer](./bounded-queue-policy-primer.md), [Lock-Free MPSC Queue](./lock-free-mpsc-queue.md) |
| telemetry | fan-in 크기, drop 허용 여부, 메모리 상한 | 관측 이벤트 fan-in이면 [Bounded MPMC Queue](./bounded-mpmc-queue.md)나 `MPSC`를 먼저 본다 | `blocking`보다 `reject`, sampling, upstream throttle이 더 흔하다 | [Bounded MPMC Queue](./bounded-mpmc-queue.md), [Lock-Free MPSC Queue](./lock-free-mpsc-queue.md) |
| audio | callback thread의 실시간성, frame cadence, jitter budget | 대개 `single producer -> single consumer`라서 [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)가 기본값이다 | audio callback 안에서는 `blocking`을 피하고, overrun/underrun 계약을 별도로 둔다 | [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md) |
| producer-consumer pipeline | producer/consumer cardinality, fan-out, stage dependency | `1:1`이면 SPSC, `N:1`이면 MPSC, `N:M`이면 bounded MPMC, stage barrier가 있으면 sequencer까지 본다 | 가장 느린 stage가 상류를 늦춰야 하면 `backpressure`, stage별 독립 handoff면 queue 분리가 우선 | [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md), [Bounded MPMC Queue](./bounded-mpmc-queue.md), [Sequencer-Based Ring Buffer Coordination](./sequencer-based-ring-buffer-coordination.md) |

짧게 압축하면 이렇다.

## 깊이 들어가기 (계속 3)

- logging은 "최근 문맥을 살릴까, 절대 유실을 막을까"가 먼저다.
- telemetry는 "여러 producer를 어떻게 fan-in할까"와 "drop을 어디서 계수할까"가 먼저다.
- audio는 "callback을 절대 막지 않는다"가 거의 최우선 계약이다.
- producer-consumer pipeline은 queue API보다 `몇 명이 넣고 몇 명이 빼는가`, `느린 stage가 누구를 멈추게 하는가`가 더 중요하다.

## 실전 시나리오

### 시나리오 1: 로그 버퍼

짧은 시간 동안 로그를 모아서 배치 전송할 때, ring buffer는 메모리 할당을 줄이고 throughput을 안정화한다.
다만 로그라고 해서 항상 같은 선택은 아니다.

- 디버그용 최근 `N`개 tail이면 overwrite ring이 자연스럽다.
- 여러 스레드가 하나의 flush thread로 모인다면 `MPSC -> single flusher`가 더 맞다.
- 감사 로그처럼 유실이 치명적이면 ring buffer는 앞단 burst absorber로만 두고, 뒤에서는 backpressure나 durable queue를 붙여야 한다.

### 시나리오 2: telemetry fan-in

metric, trace, observability event는 대개 producer가 많고 일부 drop을 계수 가능한 경우가 많다.
그래서 단순 FIFO queue보다 "메모리 상한을 지키면서 drop/sampling을 어디서 할지"가 핵심이 된다.

- producer가 여러 개면 MPSC나 bounded MPMC를 먼저 본다.
- full 시 thread를 오래 막기보다 reject, sample, upstream throttle로 넘기는 편이 흔하다.
- queue occupancy, reject count, lag를 같이 보지 않으면 조용히 유실될 수 있다.

### 시나리오 3: audio handoff

audio callback과 worker thread 사이 handoff는 ring buffer가 특히 잘 맞는 고전적인 예다.
frame 크기와 cadence가 일정하고, allocation이나 lock 대기가 jitter로 바로 드러나기 때문이다.

- 보통은 SPSC 형태가 가장 자연스럽다.
- callback thread 안에서는 `blocking`을 피한다.
- overrun/underrun이 나면 drop, overwrite, zero-fill 중 무엇을 택할지 계약으로 분리해야 한다.

### 시나리오 4: producer-consumer pipeline

pipeline이라고 해서 무조건 같은 ring buffer를 쓰는 것은 아니다.

- `producer 1개 -> consumer 1개`면 SPSC ring이 가장 싸다.
- 여러 producer가 한 consumer로 몰리면 MPSC가 더 자연스럽다.
- 여러 producer와 consumer가 모두 경쟁하면 bounded MPMC가 필요하다.
- `decode -> validate -> enrich -> persist`처럼 stage dependency가 중요하면 queue보다 [Sequencer-Based Ring Buffer Coordination](./sequencer-based-ring-buffer-coordination.md) 쪽 모델이 더 잘 맞는다.

즉 ring buffer 질문은 자료구조 이름보다 **cardinality와 backpressure topology**를 먼저 적는 것이 실전적이다.

## 코드로 보기

```java
import java.util.NoSuchElementException;

public class RingBuffer<T> {
    private final Object[] data;
    private int head = 0;
    private int tail = 0;
    private int size = 0;

    public RingBuffer(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be positive");
        this.data = new Object[capacity];
    }

    public boolean offer(T value) {
        if (size == data.length) {
            return false;
        }
        data[tail] = value;
        tail = (tail + 1) % data.length;
        size++;
        return true;
    }

    public T poll() {
        if (size == 0) {
            return null;
        }
        @SuppressWarnings("unchecked")
        T value = (T) data[head];
        data[head] = null;
        head = (head + 1) % data.length;
        size--;
        return value;
    }

    public T peek() {
        if (size == 0) throw new NoSuchElementException();
        @SuppressWarnings("unchecked")
        T value = (T) data[head];
        return value;
    }

    public int size() {
        return size;
    }

    public boolean isEmpty() {
        return size == 0;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Ring Buffer | 고정 비용과 예측 가능성이 좋다 | 크기를 늘리기 어렵다 | 지연시간과 메모리 예측성이 중요할 때 |
| 동적 Queue | 유연하다 | resize와 GC 비용이 생긴다 | 입력량이 자주 바뀔 때 |
| Deque | 앞뒤 삽입이 편하다 | 큐 의미가 흐려질 수 있다 | 양방향 처리도 필요할 때 |

Ring Buffer는 "무조건 큐"가 아니라, **bounded queue**라는 점이 핵심이다.

## 꼬리질문

> Q: empty와 full을 어떻게 구분하나?
> 의도: 원형 인덱스 판별 이해 확인
> 핵심: size를 두거나, 한 칸을 비워 두는 방식으로 구분한다.

> Q: 왜 tail latency에 유리한가?
> 의도: 상수 비용과 할당 회피 감각 확인
> 핵심: resize가 없고, 연산이 단순해서 비용 예측이 쉽다.

> Q: overwrite가 항상 좋은가?
> 의도: 데이터 유실 정책 이해 확인
> 핵심: 아니다. 최신성보다 무결성이 중요하면 overwrite는 위험하다.

## 한 줄 정리

Ring Buffer는 고정 크기 원형 배열로 큐를 구현해, 예측 가능한 성능과 낮은 할당 비용을 얻는 자료구조다.
