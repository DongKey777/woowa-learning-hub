---
schema_version: 3
title: Lock-Free SPSC Ring Buffer
concept_id: data-structure/lock-free-spsc-ring-buffer
canonical: false
category: data-structure
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- lock-free-spsc-ring
- low-latency-queue
- memory-ordering-publication
aliases:
- Lock-Free SPSC Ring Buffer
- single producer single consumer queue
- SPSC queue
- bounded ring queue
- low latency queue
- wait-free fast path
- head tail padding
symptoms:
- producer와 consumer가 각각 하나뿐인데 CAS가 많은 범용 concurrent queue를 써서 latency와 contention을 키운다
- producer는 tail만, consumer는 head만 전진한다는 ownership 분리가 SPSC fast path를 단순하게 만든다는 점을 놓친다
- slot write와 tail publish 순서, tail read와 slot read 순서 같은 memory ordering을 구현 detail로만 보고 correctness 핵심으로 보지 않는다
intents:
- definition
- design
prerequisites:
- data-structure/ring-buffer
next_docs:
- data-structure/lock-free-mpsc-queue
- data-structure/bounded-mpmc-queue
- data-structure/work-stealing-deque
linked_paths:
- contents/data-structure/ring-buffer.md
- contents/data-structure/lock-free-mpsc-queue.md
- contents/data-structure/work-stealing-deque.md
confusable_with:
- data-structure/ring-buffer
- data-structure/lock-free-mpsc-queue
- data-structure/bounded-mpmc-queue
- data-structure/work-stealing-deque
forbidden_neighbors: []
expected_queries:
- Lock-Free SPSC Ring Buffer는 single producer single consumer 제약으로 왜 빠른가?
- SPSC queue에서 producer가 tail만 consumer가 head만 전진한다는 의미는?
- low latency bounded ring queue에서 publication order와 memory ordering이 왜 중요해?
- SPSC MPSC MPMC queue를 참여자 수 기준으로 어떻게 나눠?
- false sharing padding과 cached index가 SPSC ring buffer 성능에 주는 영향은?
contextual_chunk_prefix: |
  이 문서는 단일 producer와 단일 consumer 경로에서 head/tail ownership을
  분리해 CAS를 줄이는 Lock-Free SPSC Ring Buffer primer다. bounded ring,
  low latency, publication ordering, memory barrier, false sharing padding을
  다룬다.
---
# Lock-Free SPSC Ring Buffer

> 한 줄 요약: Lock-Free SPSC Ring Buffer는 단일 producer와 단일 consumer 경로를 전제로 head/tail 경합을 분리해, 매우 낮은 오버헤드와 예측 가능한 지연시간을 노리는 저지연 큐 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Ring Buffer](./ring-buffer.md)
> - [Lock-Free MPSC Queue](./lock-free-mpsc-queue.md)
> - [Work-Stealing Deque](./work-stealing-deque.md)

> retrieval-anchor-keywords: lock-free spsc ring buffer, single producer single consumer queue, spsc queue, bounded ring queue, cache-friendly queue, low latency queue, wait-free fast path, head tail padding, event pipeline queue

## 핵심 개념

모든 concurrent queue가 여러 producer와 여러 consumer를 동시에 지원할 필요는 없다.  
실제 backend 파이프라인에는 "한 스레드가 쓰고 한 스레드가 읽는" 경로가 자주 있다.

- I/O thread -> worker thread
- parser thread -> encoder thread
- ingest thread -> batcher thread

이 경우 SPSC Ring Buffer는 구조를 극단적으로 단순화한다.

- producer는 `tail`만 전진
- consumer는 `head`만 전진
- 둘은 서로의 위치를 읽기만 한다

즉 CAS 난전 대신 **역할 분리 자체로 contention을 줄이는 큐**다.

## 깊이 들어가기

### 1. 왜 SPSC 제약이 큰 이점이 되나

SPSC에서는 ownership이 명확하다.

- enqueue slot publication은 producer 책임
- dequeue slot reclamation은 consumer 책임

이 덕분에:

- head/tail CAS가 대부분 불필요하다
- false sharing 완화가 쉽다
- memory barrier가 상대적으로 단순하다

범용성은 줄지만 fast path가 매우 짧아진다.

### 2. bounded ring이 저지연에 잘 맞는 이유

배열 기반 고정 크기 구조는 다음 장점이 있다.

- 메모리 할당이 거의 없다
- locality가 좋다
- full/empty 판정이 단순하다

특히 tail latency가 중요한 경로에서는  
"평균적으로 빠름"보다 "**항상 비슷한 비용**"이 더 중요하다.

### 3. publication order가 핵심이다

producer는 보통 이렇게 동작한다.

1. slot에 값을 쓴다
2. 그 다음 tail을 공개한다

consumer는 반대로:

1. tail을 읽어 새 데이터가 있는지 확인
2. slot 값을 읽는다
3. 처리 후 head를 전진시킨다

이 순서가 깨지면 consumer가 아직 준비되지 않은 slot을 읽을 수 있다.  
즉 구현 포인트는 알고리즘보다 **memory ordering**인 경우가 많다.

### 4. padding과 cached index가 실전 포인트다

head와 tail이 같은 cache line에 있으면 cache ping-pong이 생길 수 있다.  
그래서 저지연 구현은 보통 다음을 한다.

- head/tail cache line padding
- 상대 포인터 값의 local cache
- power-of-two capacity와 mask 연산

즉 빅오보다 **하드웨어 친화성**이 성능을 좌우한다.

### 5. backend에서 어디에 맞나

SPSC Ring Buffer는 범용 메시지 브로커가 아니라  
프로세스 내부 파이프라인 연결 부품으로 생각하는 편이 맞다.

- 로그 인코딩 단계 연결
- 네트워크 프레임 처리 파이프
- observability event batcher
- low-latency trading/streaming 처리

반대로 producer나 consumer 수가 바뀔 가능성이 크면  
처음부터 MPSC/MPMC 구조가 더 현실적일 수 있다.

## 실전 시나리오

### 시나리오 1: 단일 수집 스레드 -> 단일 배치 스레드

telemetry/event ingest에서 수집 스레드와 flush 스레드가 1:1이면  
SPSC ring이 가장 단순하면서 빠른 선택이 될 수 있다.

### 시나리오 2: 네트워크 디코딩 파이프

소켓 읽기 스레드가 메시지를 파싱 스레드에 넘기는 경로처럼  
역할이 고정된 파이프라인에 잘 맞는다.

### 시나리오 3: 부적합한 producer 증가

나중에 producer가 둘 이상이 되면 SPSC 구현은 깨진다.  
이 경우 MPSC로 올리거나 sharding이 필요하다.

### 시나리오 4: 부적합한 경우

strict durability, large fan-in, dynamic backpressure orchestration이 중요하면  
이 구조만으로는 부족하다.

## 코드로 보기

```java
public class SpscRingBuffer<E> {
    private final Object[] buffer;
    private final int mask;

    private volatile long head = 0;
    private volatile long tail = 0;

    public SpscRingBuffer(int capacityPowerOfTwo) {
        if (Integer.bitCount(capacityPowerOfTwo) != 1) {
            throw new IllegalArgumentException("capacity must be power of two");
        }
        this.buffer = new Object[capacityPowerOfTwo];
        this.mask = capacityPowerOfTwo - 1;
    }

    public boolean offer(E value) {
        long currentTail = tail;
        if (currentTail - head == buffer.length) {
            return false;
        }
        buffer[(int) (currentTail & mask)] = value;
        tail = currentTail + 1;
        return true;
    }

    @SuppressWarnings("unchecked")
    public E poll() {
        long currentHead = head;
        if (currentHead == tail) {
            return null;
        }
        int index = (int) (currentHead & mask);
        E value = (E) buffer[index];
        buffer[index] = null;
        head = currentHead + 1;
        return value;
    }
}
```

이 코드는 개념 설명용이다.  
실전 저지연 구현은 padded field, local cached head/tail, stronger publication guarantees까지 고려한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Lock-Free SPSC Ring Buffer | fast path가 매우 짧고 allocation이 거의 없다 | producer/consumer 수가 고정되어야 한다 | 프로세스 내부 1:1 저지연 파이프라인 |
| Lock-Free MPSC Queue | 여러 producer ingress에 강하다 | allocation과 publish gap 고려가 필요하다 | actor mailbox, event loop submit |
| 일반 Ring Buffer | 개념이 단순하고 bounded queue로 유용하다 | concurrent correctness는 별도 설계가 필요하다 | 단일 스레드 또는 단순 큐 |
| MPMC Queue | 범용성이 높다 | 구현과 contention 비용이 크다 | 참여 스레드 수가 동적일 때 |

중요한 질문은 "범용성이 필요한가"보다 "1:1 경로를 얼마나 싸게 만들 수 있는가"다.

## 꼬리질문

> Q: SPSC queue가 왜 특히 빠를 수 있나요?
> 의도: ownership 분리와 CAS 회피를 이해하는지 확인
> 핵심: producer와 consumer가 서로 다른 포인터만 주로 갱신하므로 동기화 비용이 크게 줄어들기 때문이다.

> Q: 왜 power-of-two capacity를 자주 쓰나요?
> 의도: 구현 디테일과 하드웨어 친화성을 보는지 확인
> 핵심: `%` 대신 mask 연산으로 인덱스를 계산해 fast path를 줄이기 쉽기 때문이다.

> Q: producer가 둘이 되면 왜 바로 문제가 되나요?
> 의도: 동시성 계약의 경계를 이해하는지 확인
> 핵심: tail 갱신 ownership이 깨져 race condition이 생기기 때문이다.

## 한 줄 정리

Lock-Free SPSC Ring Buffer는 단일 producer와 단일 consumer라는 제약을 활용해, head/tail 경쟁과 할당 비용을 최소화하는 초경량 저지연 큐 구조다.
