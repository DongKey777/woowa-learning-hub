---
schema_version: 3
title: Hazard Pointers vs Epoch-Based Reclamation
concept_id: data-structure/hazard-pointers-vs-epoch-based-reclamation
canonical: false
category: data-structure
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- memory-reclamation
- hazard-pointer-vs-ebr
- lock-free-memory-safety
aliases:
- hazard pointers vs epoch based reclamation
- EBR
- safe node reclamation
- retired nodes
- lock-free memory safety
- hazard pointer slot
- epoch reclamation
symptoms:
- lock-free 자료구조에서 node를 logical remove한 순간 바로 free해도 된다고 생각해 다른 thread의 stale pointer 접근 위험을 만든다
- Hazard Pointer의 precise pointer protection과 EBR의 batch epoch reclamation trade-off를 구분하지 못한다
- linked queue와 bounded ring에서 reclamation 부담이 드러나는 위치가 다르다는 점을 고려하지 않는다
intents:
- comparison
- deep_dive
prerequisites:
- data-structure/aba-problem-tagged-pointers
- data-structure/michael-scott-lock-free-queue
next_docs:
- data-structure/reclamation-cost-tradeoffs
- data-structure/bounded-mpmc-queue
- data-structure/lock-free-mpsc-queue
- data-structure/lock-free-spsc-ring-buffer
linked_paths:
- contents/data-structure/bounded-mpmc-queue.md
- contents/data-structure/michael-scott-lock-free-queue.md
- contents/data-structure/lock-free-mpsc-queue.md
- contents/data-structure/lock-free-spsc-ring-buffer.md
- contents/data-structure/aba-problem-and-tagged-pointers.md
- contents/data-structure/reclamation-cost-tradeoffs.md
confusable_with:
- data-structure/aba-problem-tagged-pointers
- data-structure/reclamation-cost-tradeoffs
- data-structure/michael-scott-lock-free-queue
- data-structure/bounded-mpmc-queue
forbidden_neighbors: []
expected_queries:
- Hazard Pointers와 Epoch-Based Reclamation은 lock-free node reclamation에서 어떻게 달라?
- lock-free queue에서 제거된 node를 바로 free하면 왜 memory safety 문제가 생겨?
- hazard pointer publish와 EBR epoch advance trade-off를 설명해줘
- 느린 thread가 epoch reclamation을 막을 수 있다는 뜻은?
- bounded ring과 linked lock-free queue에서 reclamation cost가 다르게 보이는 이유는?
contextual_chunk_prefix: |
  이 문서는 lock-free 자료구조에서 logical removal과 physical memory free를
  분리해야 하는 safe reclamation chooser다. Hazard Pointers는 pointer 단위
  protection, Epoch-Based Reclamation은 epoch batch reclamation이며, linked
  queue와 bounded ring에서 비용이 드러나는 위치를 비교한다.
---
# Hazard Pointers vs Epoch-Based Reclamation

> 한 줄 요약: Hazard Pointers와 Epoch-Based Reclamation은 lock-free 구조에서 제거된 노드를 언제 안전하게 회수할지 정하는 메모리 회수 지원 구조이며, linked queue와 bounded ring은 이 비용이 드러나는 위치가 다르다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Bounded MPMC Queue](./bounded-mpmc-queue.md)
> - [Michael-Scott Lock-Free Queue](./michael-scott-lock-free-queue.md)
> - [Lock-Free MPSC Queue](./lock-free-mpsc-queue.md)
> - [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)
> - [ABA Problem and Tagged Pointers](./aba-problem-and-tagged-pointers.md)
> - [Reclamation Cost Trade-offs](./reclamation-cost-tradeoffs.md)

> retrieval-anchor-keywords: hazard pointers, epoch based reclamation, ebr, memory reclamation, lock-free memory safety, hazard pointer vs epoch reclamation, safe node reclamation, lock-free queue support, concurrent memory management, retired nodes, bounded ring reclamation, pooled descriptor lifetime, linked queue memory safety

## 핵심 개념

lock-free 자료구조는 원소를 논리적으로 제거하는 것과  
메모리를 실제로 해제하는 것이 같은 순간에 일어나지 않는다.

문제는 이렇다.

- 스레드 A는 node를 제거했다
- 스레드 B는 아직 그 node 포인터를 읽고 있을 수 있다

그래서 safe reclamation이 필요하다.  
대표 선택지가 Hazard Pointers와 Epoch-Based Reclamation(EBR)이다.

## 깊이 들어가기

### 1. Hazard Pointers는 "지금 내가 보고 있다"를 명시한다

각 스레드는 자신이 현재 접근 중인 포인터를 hazard slot에 공개한다.

- 읽기 전 hazard publish
- 그 포인터가 아직 유효한지 재검증
- retire된 node는 hazard 목록에 없는 경우만 해제

장점:

- 특정 node 단위로 매우 정밀하다
- preempted thread가 전체 시스템 회수를 막는 문제를 줄일 수 있다

단점:

- 읽기 경로마다 publish/retry 비용이 있다
- hazard slot scan 비용이 있다

즉 fine-grained하고 보수적인 방식이다.

### 2. EBR은 "세대(epoch) 단위로 나중에 치운다"

EBR은 개별 포인터 대신 세대 개념을 쓴다.

- 각 스레드는 현재 들어온 epoch를 표시
- 제거된 node는 retire list에 넣고 현재 epoch를 붙임
- 모든 active thread가 더 뒤 epoch로 넘어간 뒤에야 오래된 retire list를 해제

장점:

- fast path가 비교적 가볍다
- retire batch 처리와 잘 맞는다

단점:

- 느리거나 멈춘 thread가 회수를 오래 막을 수 있다
- thread lifecycle 관리가 중요하다

즉 precise pointer safety보다  
**배치형 세대 관리**를 택하는 구조다.

### 3. queue topology에 따라 reclamation 부담이 드러나는 위치가 다르다

같은 concurrent queue라도 reclamation의 "핫패스 위치"가 다르다.

- Michael-Scott Queue 같은 linked MPMC: dequeue마다 제거된 node retire/free 후보가 생긴다
- bounded MPMC ring: core slot 배열은 preallocated라 slot 자체는 보통 retire하지 않는다
- SPSC ring: ownership이 명확하면 core buffer reclamation 문제가 더 줄어든다

즉 bounded ring은 reclamation을 없애기보다  
**문제를 queue core 밖으로 밀어내는 경우가 많다**.

예를 들어 다음은 여전히 별도 lifetime 관리가 필요하다.

- slot payload가 외부 object pool pointer일 때
- intrusive node를 다른 자료구조와 공유할 때
- parked producer/consumer waiter node를 동적으로 둘 때

### 4. lock-free 자료구조 선택 못지않게 중요하다

MS Queue 같은 알고리즘을 제대로 쓴다고 끝나지 않는다.  
safe reclamation이 없으면 ABA를 피했다 해도 use-after-free가 날 수 있다.

즉 구조를 이해할 때는 항상 둘을 함께 봐야 한다.

- queue/stack/list 알고리즘
- memory reclamation 전략

bounded ring도 예외는 아니다.  
core slot sequence가 wraparound는 막아줘도, slot 안에 담긴 외부 node의 생명주기까지 보장하지는 않는다.

### 5. backend에서 어떤 차이가 생기나

GC 언어 밖에서는 운영 특성이 크게 갈린다.

- 짧은 critical section이 많고 thread가 안정적이면 EBR이 매력적일 수 있다
- thread stop/resume, preemption, long reader가 많으면 Hazard Pointer가 더 안전할 수 있다

즉 reclamation 전략은 자료구조 선택이 아니라  
**runtime model 선택**에 가깝다.

### 6. 언제 무엇을 고르나

대략적인 감각:

- EBR: throughput 중심, thread lifecycle가 통제될 때
- Hazard Pointers: 더 정밀한 안전성과 stalled thread 내성이 필요할 때

구조별로 풀어보면 더 감각적이다.

- linked queue/stack에서 dequeue/free가 hot path면 reclamation 전략이 핵심 설계 포인트다
- bounded ring에서 core slot만 재사용하면 HP/EBR 필요성이 줄 수 있다
- 하지만 ring payload가 pooled descriptor라면 결국 외부 pool 쪽 reclamation이 다시 중요해진다

실무에서는 언어 런타임, thread model, pause 특성까지 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 고정 worker thread 기반 lock-free queue

worker 수가 고정되고 thread가 오래 살아 있다면  
EBR이 구현과 성능 면에서 매력적일 수 있다.

### 시나리오 2: bounded ring + pooled descriptor

queue core는 preallocated slot이라 안전해 보여도,  
slot 안의 descriptor를 freelist로 재사용한다면 그 freelist 쪽 reclamation/ABA를 따로 봐야 한다.

### 시나리오 3: stop-the-world 없는 native service

thread preemption과 long reader가 문제면  
Hazard Pointer가 더 정밀한 안전장치가 될 수 있다.

### 시나리오 4: retire burst

삭제가 몰리는 구조에선 EBR의 batch free가 좋을 수 있지만,  
느린 thread 하나가 메모리 회수를 오래 잡아둘 수 있다.

### 시나리오 5: 부적합한 이해

"lock-free algorithm을 썼으니 안전하다"는 생각이 가장 위험하다.  
reclamation 없는 lock-free는 production에서 쉽게 부서진다.

## 비교 표

| 항목 | Hazard Pointers | Epoch-Based Reclamation |
|---|---|---|
| 보호 단위 | 개별 포인터 | epoch 세대 |
| fast path 비용 | hazard publish/retry | 비교적 작음 |
| stalled thread 영향 | 상대적으로 작음 | 매우 클 수 있음 |
| batch free | 가능하지만 덜 자연스러움 | 매우 자연스러움 |
| 구현 포인트 | slot 관리, scan | epoch advance, thread 등록/해제 |
| 잘 맞는 구조 | long reader, preemption-heavy linked structure | fixed worker, throughput-oriented linked structure |

중요한 보정 하나가 더 있다.

- bounded ring core slot reuse는 위 표만으로 설명이 끝나지 않는다
- slot 자체를 안 free하면 HP/EBR가 안 보일 수 있다
- 대신 외부 object pool, freelist, waiter node가 진짜 reclamation 경계가 된다

## 꼬리질문

> Q: lock-free queue에 왜 memory reclamation이 따로 필요한가요?
> 의도: 논리적 삭제와 실제 메모리 해제를 구분하는지 확인
> 핵심: 다른 스레드가 아직 제거된 node 포인터를 읽고 있을 수 있기 때문이다.

> Q: bounded MPMC ring이면 reclamation 문제가 사라지나요?
> 의도: core slot reuse와 payload object lifetime을 구분하는지 확인
> 핵심: core slot retire는 줄어들지만, slot이 가리키는 외부 object나 side freelist의 생명주기는 여전히 별도 관리가 필요하다.

> Q: EBR의 가장 큰 운영 리스크는 무엇인가요?
> 의도: thread lifecycle과 reclamation 지연을 연결하는지 확인
> 핵심: 느리거나 멈춘 thread가 오래된 epoch 해제를 계속 막을 수 있다는 점이다.

> Q: Hazard Pointer가 더 정밀하다는 말은 무슨 뜻인가요?
> 의도: 포인터 단위 보호 개념 이해 확인
> 핵심: thread가 지금 보고 있는 개별 node를 명시적으로 보호하므로 회수 판단이 더 세밀하다는 뜻이다.

## 한 줄 정리

Hazard Pointers와 EBR은 lock-free 자료구조에서 제거된 node를 언제 안전하게 해제할지 결정하는 필수 지원 구조이며, linked queue와 bounded ring은 이 비용이 드러나는 층위가 다르므로 runtime/thread model과 object lifetime을 함께 봐야 한다.
