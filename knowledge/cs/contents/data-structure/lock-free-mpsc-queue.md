---
schema_version: 3
title: Lock-Free MPSC Queue
concept_id: data-structure/lock-free-mpsc-queue
canonical: false
category: data-structure
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- lock-free-mpsc-queue
- actor-mailbox-queue
- producer-consumer-concurrency
aliases:
- Lock-Free MPSC Queue
- multiple producer single consumer
- MPSC linked queue
- actor mailbox queue
- event ingestion queue
- atomic exchange queue
- producer consumer queue
symptoms:
- 여러 producer와 단일 consumer만 필요한데 MPMC queue를 써서 dequeue 경합과 구현 복잡도를 불필요하게 키운다
- linked-node MPSC의 atomic exchange와 prev.next publish gap을 이해하지 못해 순간적으로 비어 보이는 race를 놓친다
- linked MPSC와 bounded ring MPSC의 unbounded mailbox vs fixed capacity backpressure 차이를 구분하지 못한다
intents:
- comparison
- design
prerequisites:
- data-structure/ring-buffer
- data-structure/lock-free-spsc-ring-buffer
next_docs:
- data-structure/michael-scott-lock-free-queue
- data-structure/hazard-pointers-vs-epoch-based-reclamation
- data-structure/work-stealing-deque
- data-structure/hierarchical-timing-wheel
linked_paths:
- contents/data-structure/ring-buffer.md
- contents/data-structure/lock-free-spsc-ring-buffer.md
- contents/data-structure/michael-scott-lock-free-queue.md
- contents/data-structure/hazard-pointers-vs-epoch-based-reclamation.md
- contents/data-structure/work-stealing-deque.md
- contents/data-structure/hierarchical-timing-wheel.md
confusable_with:
- data-structure/lock-free-spsc-ring-buffer
- data-structure/michael-scott-lock-free-queue
- data-structure/bounded-mpmc-queue
- data-structure/work-stealing-deque
forbidden_neighbors: []
expected_queries:
- Lock-Free MPSC Queue는 actor mailbox나 event ingestion에서 왜 MPMC보다 가벼울 수 있어?
- multiple producer single consumer 제약이 dequeue contention을 줄이는 이유는?
- linked-node MPSC에서 atomic exchange와 prev.next publish gap은 무엇을 조심해야 해?
- bounded ring MPSC와 linked unbounded MPSC를 어떻게 비교해?
- producer는 여러 명이고 consumer는 하나인 queue를 고를 때 무엇을 봐야 해?
contextual_chunk_prefix: |
  이 문서는 여러 producer와 단일 consumer만 필요한 actor mailbox, event
  ingestion, timer handoff 경로에서 MPMC보다 가벼운 Lock-Free MPSC Queue를
  고르는 chooser다. linked-node atomic exchange, publish gap, ring-based
  bounded MPSC와 backpressure를 다룬다.
---
# Lock-Free MPSC Queue

> 한 줄 요약: Lock-Free MPSC Queue는 여러 producer가 동시에 enqueue하고 단일 consumer가 dequeue하는 경로를 분리해, 중앙 락 없이 이벤트 수집과 mailbox 처리 비용을 낮추는 동시성 친화 큐 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Ring Buffer](./ring-buffer.md)
> - [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)
> - [Michael-Scott Lock-Free Queue](./michael-scott-lock-free-queue.md)
> - [Hazard Pointers vs Epoch-Based Reclamation](./hazard-pointers-vs-epoch-based-reclamation.md)
> - [Work-Stealing Deque](./work-stealing-deque.md)
> - [Hierarchical Timing Wheel](./hierarchical-timing-wheel.md)

> retrieval-anchor-keywords: lock-free mpsc queue, multiple producer single consumer, mpsc linked queue, atomic exchange queue, actor mailbox, event ingestion queue, producer consumer concurrency, intrusive queue, mailbox scheduler, append-only queue

## 핵심 개념

동시성 파이프라인에서 흔한 패턴은 "여러 스레드가 작업을 넣고, 한 스레드가 순서대로 처리한다"는 것이다.

- actor mailbox
- event loop submit queue
- log ingestion queue
- timer expiration handoff

이때 MPMC queue 하나로 다 해결하려고 하면 구현과 contention이 모두 무거워질 수 있다.  
Lock-Free MPSC Queue는 요구사항을 축소한다.

- producer는 여러 명
- consumer는 한 명
- dequeue 경합은 없다

즉 가장 비싼 부분을 일반화하지 않고, **실제 필요한 동시성 형태만 지원**해서 비용을 줄인다.

## 깊이 들어가기

### 1. 왜 single-consumer 제약이 오히려 강점이 되나

consumer가 하나뿐이면 tail 쪽 상태를 그 스레드가 독점적으로 다룰 수 있다.

- dequeue CAS 경쟁이 줄어든다
- 메모리 순서 보장이 단순해진다
- per-consumer bookkeeping이 쉬워진다

즉 MPMC보다 덜 범용적이지만, 그만큼 fast path가 더 작고 예측 가능해진다.

### 2. linked-node MPSC의 핵심 아이디어

실무에서 자주 보이는 형태는 "producer head, consumer tail"을 분리한 linked queue다.

- producer는 새 노드를 만들고 head를 atomic exchange
- 교체 전 마지막 노드의 `next`를 새 노드로 연결
- consumer는 자기 `tail.next`를 따라가며 순서대로 읽음

이 구조의 중요한 성질:

- producer끼리는 head 한 점에서만 동기화
- consumer는 tail을 혼자 전진
- enqueue는 append-only에 가깝다

다만 `head` 교체와 `prev.next` 연결 사이에 작은 publish gap이 생길 수 있어,  
consumer는 순간적으로 비어 보이는 상황을 조심해야 한다.

### 3. bounded ring 기반 MPSC와의 차이

MPSC는 linked-node와 bounded ring 두 계열로 많이 구현된다.

- linked-node MPSC: unbounded로 다루기 쉽고 mailbox에 잘 맞음
- ring-based MPSC: 고정 크기와 cache locality가 좋음

대신 ring 기반은 보통 다음을 더 신경 써야 한다.

- full 판정
- slot publication ordering
- slow consumer backpressure
- overwrite 금지

즉 "메모리 예측성"이 중요하면 ring,  
"외부 submit 유연성"이 중요하면 linked MPSC가 자주 선택된다.

### 4. scheduler에서 어디에 붙나

fork-join runtime이나 event loop도 외부에서 작업이 들어오는 경로가 필요하다.  
이때 내부 worker 구조는 work-stealing deque여도, 외부 submit은 MPSC queue를 함께 둘 수 있다.

대표 조합:

- worker local: work-stealing deque
- external submit: MPSC queue
- delayed task handoff: timing wheel -> MPSC mailbox

즉 MPSC queue는 단독 구조라기보다 **동시성 런타임의 ingress queue**로 자주 쓰인다.

### 5. lock-free라고 공짜는 아니다

lock-free queue도 운영 포인트가 있다.

- node allocation GC 비용
- false sharing
- producer burst 시 unbounded growth
- consumer stall 시 tail latency 누적

또 Java에서는 CAS만 보면 쉬워 보여도,  
메모리 visibility와 progress guarantee를 정확히 이해하지 못하면 미묘한 버그가 난다.

## 실전 시나리오

### 시나리오 1: actor mailbox

여러 스레드가 actor에게 메시지를 보내고, actor 스레드 하나가 순서대로 처리한다면  
MPSC queue가 자연스럽다.

### 시나리오 2: event loop external submit

이벤트 루프는 보통 소비자가 하나다.  
다른 worker가 task를 위임할 때 MPSC queue를 두면 중앙 락 큐보다 가볍게 ingress를 만들 수 있다.

### 시나리오 3: timer expiration handoff

timing wheel이나 scheduler가 만료 작업을 한 consumer thread로 넘길 때도  
MPSC queue가 glue 구조로 잘 맞는다.

### 시나리오 4: 부적합한 경우

여러 consumer가 동시에 작업을 가져가야 하거나 strict fairness가 매우 중요하면  
MPMC queue나 다른 구조가 더 맞다.

## 코드로 보기

```java
import java.util.concurrent.atomic.AtomicReference;

public class MpscLinkedQueue<E> {
    private final AtomicReference<Node<E>> head;
    private Node<E> tail; // consumer thread only

    public MpscLinkedQueue() {
        Node<E> stub = new Node<>(null);
        this.head = new AtomicReference<>(stub);
        this.tail = stub;
    }

    public void offer(E value) {
        Node<E> node = new Node<>(value);
        Node<E> previous = head.getAndSet(node);
        previous.next = node;
    }

    public E poll() {
        Node<E> next = tail.next;
        if (next == null) {
            return null;
        }

        E value = next.value;
        tail = next;
        return value;
    }

    private static final class Node<E> {
        private final E value;
        private volatile Node<E> next;

        private Node(E value) {
            this.value = value;
        }
    }
}
```

이 코드는 개념 스케치다.  
실전 구현은 stub 재사용, publish gap 처리, backoff, object pooling 여부까지 같이 고민해야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Lock-Free MPSC Queue | 여러 producer ingress를 가볍게 받고 single consumer 경로를 단순화한다 | single consumer 제약과 allocation 비용이 있다 | actor mailbox, event loop submit, ingestion handoff |
| 중앙 MPMC Queue | 범용성이 높다 | contention과 구현 복잡도가 크다 | producer/consumer가 모두 다수일 때 |
| Ring Buffer | bounded memory와 cache locality가 좋다 | 외부 다중 producer를 붙일 때 publication 설계가 복잡하다 | 고정 크기 파이프라인, low-latency path |
| Work-Stealing Deque | scheduler locality와 load balancing에 강하다 | 외부 ingress queue 역할에는 직접 맞지 않는다 | fork-join worker local queue |

중요한 질문은 "몇 명이 넣고 몇 명이 빼는가"다.  
동시성 큐는 이 형태를 좁힐수록 빠르고 단순해진다.

## 꼬리질문

> Q: 왜 MPSC queue가 MPMC보다 빠를 수 있나요?
> 의도: 범용성과 fast path 크기의 trade-off 이해 확인
> 핵심: consumer 경쟁을 제거해 dequeue 경로와 상태 관리가 더 단순해지기 때문이다.

> Q: linked-node MPSC에서 producer의 직렬화 지점은 어디인가요?
> 의도: atomic exchange 기반 append 구조 이해 확인
> 핵심: 보통 `head.getAndSet(node)` 한 지점에서 producer들이 순서를 정한다.

> Q: work-stealing deque가 있는데 왜 별도 MPSC queue가 또 필요할까요?
> 의도: 런타임 내부 queue 역할 분리를 이해하는지 확인
> 핵심: worker local queue와 외부 submit ingress는 요구사항이 다르기 때문이다.

## 한 줄 정리

Lock-Free MPSC Queue는 여러 producer의 ingress를 한 consumer로 안전하게 모으는 데 특화된 동시성 큐로, 범용 MPMC보다 제약은 크지만 그만큼 구현 경로와 contention 비용을 줄일 수 있다.
