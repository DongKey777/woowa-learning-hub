---
schema_version: 3
title: Michael-Scott Lock-Free Queue
concept_id: data-structure/michael-scott-lock-free-queue
canonical: false
category: data-structure
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- michael-scott-queue
- lock-free-mpmc-queue
- cas-helping-reclamation
aliases:
- Michael-Scott Queue
- MS Queue
- lock-free MPMC queue
- CAS linked queue
- nonblocking queue
- head tail helping
- lock-free concurrent queue
symptoms:
- MPSC나 SPSC로 충분한 상황과 enqueue/dequeue 모두 다중 경쟁하는 MPMC 상황을 구분하지 않고 범용 queue를 고른다
- dummy node, head/tail lag, helping 패턴을 이해하지 못해 lock-free progress 보장의 핵심을 놓친다
- GC가 없는 환경에서 ABA와 memory reclamation이 MS Queue 구현의 본론이라는 점을 의사코드 밖 문제로 밀어둔다
intents:
- deep_dive
- comparison
prerequisites:
- data-structure/lock-free-mpsc-queue
- data-structure/hazard-pointers-vs-epoch-based-reclamation
next_docs:
- data-structure/aba-problem-tagged-pointers
- data-structure/bounded-mpmc-queue
- data-structure/work-stealing-deque
linked_paths:
- contents/data-structure/lock-free-mpsc-queue.md
- contents/data-structure/lock-free-spsc-ring-buffer.md
- contents/data-structure/hazard-pointers-vs-epoch-based-reclamation.md
- contents/data-structure/aba-problem-and-tagged-pointers.md
- contents/data-structure/work-stealing-deque.md
confusable_with:
- data-structure/lock-free-mpsc-queue
- data-structure/lock-free-spsc-ring-buffer
- data-structure/bounded-mpmc-queue
- data-structure/hazard-pointers-vs-epoch-based-reclamation
forbidden_neighbors: []
expected_queries:
- Michael-Scott Queue는 lock-free MPMC queue로 어떤 문제를 해결해?
- MS Queue에서 dummy node와 head tail helping이 필요한 이유는?
- MPSC SPSC MPMC queue를 producer consumer 수 기준으로 어떻게 구분해?
- CAS linked queue에서 ABA와 memory reclamation이 왜 어려운가?
- lock-free queue에서 helping이 progress 보장에 어떻게 기여해?
contextual_chunk_prefix: |
  이 문서는 Michael-Scott Queue를 CAS 기반 linked-list lock-free MPMC queue
  deep dive로 설명한다. dummy node, head/tail separation, helping, enqueue와
  dequeue 경쟁, ABA, hazard pointers, epoch-based reclamation을 다룬다.
---
# Michael-Scott Lock-Free Queue

> 한 줄 요약: Michael-Scott Queue는 CAS 기반 linked-list 알고리즘으로 다중 producer와 다중 consumer를 lock-free하게 처리하는 고전적인 MPMC queue 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Lock-Free MPSC Queue](./lock-free-mpsc-queue.md)
> - [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)
> - [Hazard Pointers vs Epoch-Based Reclamation](./hazard-pointers-vs-epoch-based-reclamation.md)
> - [ABA Problem and Tagged Pointers](./aba-problem-and-tagged-pointers.md)
> - [Work-Stealing Deque](./work-stealing-deque.md)

> retrieval-anchor-keywords: michael scott queue, ms queue, lock-free mpmc queue, multiple producer multiple consumer, cas queue, linked lock-free queue, nonblocking queue, concurrent queue, head tail helping, mpmc mailbox, hazard pointers, epoch based reclamation

## 핵심 개념

동시성 큐의 난이도는 참여자 수가 늘수록 급격히 올라간다.

- SPSC: 역할이 고정돼 가장 단순
- MPSC: enqueue만 다중 경쟁
- MPMC: enqueue와 dequeue 모두 경쟁

Michael-Scott Queue는 MPMC 상황을 위한 대표 lock-free 알고리즘이다.  
linked list와 CAS를 이용해 head/tail을 전진시키고, 필요하면 다른 스레드의 미완료 tail update를 도와준다.

즉 범용 concurrent queue가 필요할 때 떠올리는 **고전적인 비블로킹 큐 표준 해법**에 가깝다.

## 깊이 들어가기

### 1. 왜 MPMC가 이렇게 어려운가

producer도 여러 명이고 consumer도 여러 명이면 다음이 동시에 생긴다.

- tail append 경쟁
- head advance 경쟁
- empty 판정 race
- head/tail lag 보정

lock을 쓰면 모델은 단순하지만 contention hotspot이 금방 생긴다.  
MS Queue는 lock 대신 CAS와 helping으로 진행 보장을 노린다.

### 2. stub node와 head/tail 분리가 핵심이다

보통 MS Queue는 dummy node 하나로 시작한다.

- `head`는 dequeue 기준점
- `tail`은 enqueue 기준점
- 실제 데이터는 `head.next`부터 시작

producer는 보통 tail 뒤에 새 노드를 연결하려 시도하고,  
consumer는 head를 다음 노드로 옮겨 값을 가져간다.

이때 tail이 뒤처져 있으면 다른 스레드가 tail을 먼저 밀어주기도 한다.  
이 helping 패턴이 lock-free 진행의 핵심이다.

### 3. ABA와 메모리 회수 문제가 본론이다

알고리즘 의사코드만 보면 단순해 보이지만, 실제 구현은 memory reclamation이 어렵다.

- 한 consumer가 node를 읽는 동안
- 다른 consumer가 그 node를 제거하고 해제할 수 있다

GC 언어에서는 그나마 수월하지만, native 환경에서는 다음이 중요하다.

- hazard pointers
- epoch-based reclamation
- tagged pointer

즉 자료구조 이해와 안전한 메모리 회수는 분리해서 봐야 한다.

### 4. helping이 왜 필요한가

lock-free는 "내 작업만 끝내면 된다"보다  
"남의 중간 상태를 마저 정리하고 앞으로 나아간다"는 발상이 자주 나온다.

MS Queue에서도:

- enqueue 중 다른 스레드가 `next`는 연결했지만 `tail`을 못 옮겼다면
- 현재 스레드가 tail advance를 도와줄 수 있다

이 helping이 없으면 구조는 더 자주 불완전한 중간 상태에 머무른다.

### 5. backend에서 어디에 맞나

범용 concurrent handoff queue가 필요하지만,  
bounded ring 제약이나 single-consumer 제약을 둘 수 없는 경우에 맞는다.

- 다수 worker submit / 다수 worker consume
- 공유 executor work queue
- generic async pipeline handoff

다만 범용성은 큰 만큼 상수 비용도 크다.  
특정 형태가 명확하면 SPSC/MPSC가 더 빠를 수 있다.

## 실전 시나리오

### 시나리오 1: 범용 executor shared queue

submitter와 worker가 모두 다수인 shared queue는  
MS Queue 같은 MPMC 구조가 더 자연스럽다.

### 시나리오 2: 여러 network thread와 여러 worker thread 사이 handoff

fan-in / fan-out이 둘 다 큰 파이프라인에서는  
single-role queue보다 범용 MPMC가 필요할 수 있다.

### 시나리오 3: 잘못된 선택

실제로는 consumer가 하나인데 MPMC queue를 넣으면  
불필요한 CAS 경쟁과 구조 복잡도만 얹는 셈이 된다.

### 시나리오 4: 부적합한 경우

엄격한 우선순위, deadline ordering, bounded memory가 필수라면  
priority queue나 bounded ring 계열이 더 맞다.

## 코드로 보기

```java
import java.util.concurrent.atomic.AtomicReference;

public class MichaelScottQueue<E> {
    private final AtomicReference<Node<E>> head;
    private final AtomicReference<Node<E>> tail;

    public MichaelScottQueue() {
        Node<E> stub = new Node<>(null);
        this.head = new AtomicReference<>(stub);
        this.tail = new AtomicReference<>(stub);
    }

    public void offer(E value) {
        Node<E> node = new Node<>(value);
        while (true) {
            Node<E> currentTail = tail.get();
            Node<E> next = currentTail.next.get();

            if (currentTail == tail.get()) {
                if (next == null) {
                    if (currentTail.next.compareAndSet(null, node)) {
                        tail.compareAndSet(currentTail, node);
                        return;
                    }
                } else {
                    tail.compareAndSet(currentTail, next);
                }
            }
        }
    }

    public E poll() {
        while (true) {
            Node<E> currentHead = head.get();
            Node<E> currentTail = tail.get();
            Node<E> next = currentHead.next.get();

            if (currentHead == head.get()) {
                if (next == null) {
                    return null;
                }
                if (currentHead == currentTail) {
                    tail.compareAndSet(currentTail, next);
                    continue;
                }
                E value = next.value;
                if (head.compareAndSet(currentHead, next)) {
                    return value;
                }
            }
        }
    }

    private static final class Node<E> {
        private final E value;
        private final AtomicReference<Node<E>> next = new AtomicReference<>(null);

        private Node(E value) {
            this.value = value;
        }
    }
}
```

이 코드는 GC 언어 기준 설명용 스케치다.  
실전 non-GC 구현은 memory reclamation 없이는 안전하지 않다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Michael-Scott Lock-Free Queue | 범용 MPMC handoff를 lock-free하게 처리할 수 있다 | CAS 경합과 memory reclamation 난이도가 높다 | shared executor queue, generic MPMC handoff |
| Lock-Free MPSC Queue | ingress fan-in에 더 단순하고 빠르다 | consumer가 하나여야 한다 | actor mailbox, event loop submit |
| Lock-Free SPSC Ring Buffer | fast path와 locality가 가장 좋다 | 1:1 제약이 강하다 | 저지연 파이프라인 |
| Blocking Queue with Lock | 구현과 이해가 단순하다 | contention 시 latency가 커질 수 있다 | 단순성이 성능보다 중요할 때 |

중요한 질문은 "정말 MPMC가 필요한가"다.  
필요하지 않다면 더 좁은 계약의 큐가 거의 항상 더 쉽고 빠르다.

## 꼬리질문

> Q: Michael-Scott Queue가 MPSC보다 더 비싼 이유는 무엇인가요?
> 의도: 범용성과 경쟁 지점 수의 trade-off 이해 확인
> 핵심: enqueue와 dequeue 양쪽 모두에서 다수 스레드 경쟁을 처리해야 하기 때문이다.

> Q: helping이 왜 필요한가요?
> 의도: lock-free 알고리즘의 진행 방식 이해 확인
> 핵심: 다른 스레드가 남긴 중간 상태를 정리해 구조를 앞으로 진전시키기 위해서다.

> Q: GC가 없는 언어에서 추가로 어려운 점은 무엇인가요?
> 의도: lock-free 자료구조와 메모리 회수 문제를 연결하는지 확인
> 핵심: 제거된 node를 다른 스레드가 아직 볼 수 있어 safe reclamation이 필요하다는 점이다.

## 한 줄 정리

Michael-Scott Queue는 CAS와 helping으로 다중 producer/consumer를 처리하는 대표적인 lock-free MPMC queue지만, 범용성만큼 구현과 메모리 회수 난이도도 높은 구조다.
