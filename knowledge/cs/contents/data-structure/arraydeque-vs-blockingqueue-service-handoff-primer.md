---
schema_version: 3
title: ArrayDeque vs BlockingQueue 서비스 handoff 프라이머
concept_id: data-structure/arraydeque-vs-blockingqueue-service-handoff-primer
canonical: true
category: data-structure
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- local-queue-vs-worker-handoff
- blockingqueue-when-multithreaded
- queue-handoff-contract
aliases:
- arraydeque vs blockingqueue
- java fifo service handoff
- arraydeque local queue
- blockingqueue producer consumer
- blockingqueue beginner
- when to use blockingqueue
- arraydeque service code beginner
- queue handoff between threads
- java worker queue basics
- arraydeque vs blockingqueue primer
- 멀티스레드 큐 뭐 써요
- blockingqueue가 뭐예요
- queue가 보이는데 운영 문서로 가야 하나요
- worker queue 다음 단계
- message consumer 전 safe route
symptoms:
- 같은 queue라도 로컬 FIFO와 worker handoff를 언제 갈라야 하는지 모르겠다
- 여러 스레드가 작업을 주고받는데 ArrayDeque로도 되는지 헷갈린다
- blocking이 정확히 무엇을 기다린다는 뜻인지 timer 개념과 자꾸 섞인다
intents:
- definition
prerequisites:
- data-structure/queue-basics
- data-structure/arraydeque-vs-linkedlist-queue-choice-card
next_docs:
- data-structure/priorityblockingqueue-timer-misuse-primer
- language/blockingqueue-transferqueue-concurrentskiplistset-semantics
- software-engineering/message-driven-adapter-example
linked_paths:
- contents/data-structure/queue-basics.md
- contents/data-structure/arraydeque-vs-linkedlist-queue-choice-card.md
- contents/data-structure/priorityblockingqueue-timer-misuse-primer.md
- contents/language/java/blockingqueue-transferqueue-concurrentskiplistset-semantics.md
- contents/algorithm/dfs-bfs-intro.md
- contents/software-engineering/ports-and-adapters-beginner-primer.md
- contents/software-engineering/message-driven-adapter-example.md
confusable_with:
- data-structure/arraydeque-vs-linkedlist-queue-choice-card
- data-structure/priorityblockingqueue-timer-misuse-primer
- data-structure/queue-vs-deque-vs-priority-queue-primer
forbidden_neighbors:
- contents/data-structure/queue-basics.md
- contents/data-structure/arraydeque-vs-linkedlist-queue-choice-card.md
expected_queries:
- 같은 요청 흐름 안에서만 쓰는 큐와 worker 스레드에 넘기는 큐를 어디서 분리해?
- producer consumer 구조가 나오면 자료구조 기본값을 어떻게 바꿔야 하는지 궁금해
- 비었을 때 기다리는 계약이 필요하면 왜 일반 deque 설명으로는 부족해?
- 여러 스레드가 작업을 주고받는 서비스 큐를 생각할 때 먼저 체크할 질문이 뭐야?
- 로컬 FIFO 버퍼와 작업 handoff 큐를 한 번에 비교해서 정리해줘
- message consumer 앞단에서 queue 선택을 볼 때 초급자가 놓치기 쉬운 기준이 뭐야?
contextual_chunk_prefix: |
  이 문서는 자료구조를 막 배우는 학습자가 같은 스레드 안에서 잠깐
  쓰는 로컬 FIFO와 다른 스레드에 작업을 넘기는 handoff 큐를 왜
  분리해서 봐야 하는지 처음 잡는 primer다. 내가 넣고 내가 빼는 큐,
  worker에게 일 넘기기, 비면 기다리는 큐, 꽉 차면 속도 조절, 서비스
  작업 전달 통로, producer consumer 기본값 같은 자연어 paraphrase가
  본 문서의 핵심 구분에 매핑된다.
---
# ArrayDeque vs BlockingQueue 서비스 handoff 프라이머

> 한 줄 요약: 한 스레드 안에서 잠깐 쓰는 FIFO면 `ArrayDeque`가 기본값이고, 여러 스레드가 작업을 넘기며 비었을 때 기다리거나 꽉 찼을 때 조절해야 하면 `BlockingQueue`로 질문을 바꿔야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [큐 기초](./queue-basics.md)
- [ArrayDeque vs LinkedList 큐 선택 카드](./arraydeque-vs-linkedlist-queue-choice-card.md)
- [PriorityBlockingQueue Timer Misuse Primer](./priorityblockingqueue-timer-misuse-primer.md)
- [BlockingQueue, TransferQueue, and ConcurrentSkipListSet Semantics](../language/java/blockingqueue-transferqueue-concurrentskiplistset-semantics.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- [Ports and Adapters Beginner Primer](../software-engineering/ports-and-adapters-beginner-primer.md)
- [Message-Driven Adapter Example](../software-engineering/message-driven-adapter-example.md)
- [data-structure 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: arraydeque vs blockingqueue, java fifo service handoff, arraydeque local queue, blockingqueue producer consumer, blockingqueue beginner, when to use blockingqueue, arraydeque service code beginner, queue handoff between threads, java worker queue basics, arraydeque vs blockingqueue primer, 멀티스레드 큐 뭐 써요, blockingqueue가 뭐예요, queue가 보이는데 운영 문서로 가야 하나요, worker queue 다음 단계, message consumer 전 safe route

## 핵심 개념

처음에는 이렇게 자르면 된다.

- `ArrayDeque`: 지금 실행 중인 코드가 **자기 안에서** 순서대로 꺼내 쓰는 로컬 FIFO
- `BlockingQueue`: **다른 스레드에게 작업을 넘기고**, 비면 기다리거나 꽉 차면 조절해야 하는 handoff FIFO

즉 자료구조 이름보다 먼저 봐야 하는 질문은 이것이다.

> "이 큐를 같은 스레드가 직접 비우는가, 아니면 다른 스레드와 사이에 작업 전달 통로로 쓰는가?"

로컬 순회나 BFS처럼 내가 넣고 내가 바로 빼는 흐름이면 `ArrayDeque` 쪽이 자연스럽다.
반대로 producer 스레드가 넣고 worker 스레드가 꺼내는 구조라면, 이제는 "FIFO 자료구조"보다 "동시성 handoff 계약"이 더 중요해진다.

## beginner safe route: queue에서 adapter까지

이 문서는 `자료구조 queue` 다음 한 칸을 설명하는 follow-up이다. 여기서 바로 broker 운영, saga, distributed scheduler로 점프하지 말고 아래 사다리만 먼저 고정하면 된다.

| 지금 보이는 질문 | 여기서 먼저 끝낼 판단 | 다음 안전한 한 칸 |
|---|---|---|
| `같은 스레드에서 내가 넣고 내가 빼나?` | 로컬 FIFO면 `ArrayDeque` 쪽이다 | [큐 기초](./queue-basics.md)로 돌아가 FIFO 도구 감각만 잠근다 |
| `다른 스레드 worker에게 작업을 넘기나?` | handoff 계약이면 `BlockingQueue` 쪽이다 | 이 문서에서 `producer/consumer`, `blocking`, `bounded`만 먼저 구분한다 |
| `HTTP 말고 consumer도 같은 일을 여는 입구인가?` | 이제 자료구조가 아니라 유스케이스 입구 질문이다 | [Message-Driven Adapter Example](../software-engineering/message-driven-adapter-example.md) |

- 짧게 외우면 `queue 도구 -> handoff 계약 -> inbound adapter`다.
- `왜 queue 다음에 갑자기 Kafka 운영 문서가 나오죠?`, `처음인데 system design으로 가야 하나요` 같은 질문이면 여기서 멈추고 `Message-Driven Adapter Example`까지만 이어 가면 beginner-safe 하다.

## 한눈에 보기

| 장면 | 먼저 떠올릴 구조 | 이유 |
|---|---|---|
| BFS, 메서드 안의 임시 FIFO | `ArrayDeque` | 같은 흐름 안에서 순서만 지키면 된다 |
| 단일 스레드 후처리 목록 | `ArrayDeque` | `offer`/`poll`만 빠르게 쓰면 충분하다 |
| 여러 스레드가 작업을 넣고 worker가 꺼냄 | `BlockingQueue` | thread-safe handoff가 필요하다 |
| 큐가 비면 worker가 기다려야 함 | `BlockingQueue` | `take()` 같은 blocking 소비가 필요하다 |
| 큐가 꽉 찼을 때 생산 속도를 늦추거나 실패시켜야 함 | bounded `BlockingQueue` | backpressure 정책이 필요하다 |

짧게 외우면 이렇다.

| 질문 | `ArrayDeque` | `BlockingQueue` |
|---|---|---|
| 같은 스레드 안에서 쓰나 | 잘 맞음 | 보통 과하다 |
| 여러 스레드가 같이 만지나 | 직접 쓰기 위험 | 기본 후보 |
| 비었을 때 기다리나 | 직접 기다림 로직을 짜야 함 | API에 의미가 들어 있다 |
| 꽉 찼을 때 정책이 있나 | 용량/대기 정책이 중심이 아님 | bounded queue로 표현 가능 |

## 언제 `ArrayDeque`에 머물면 되나

아래처럼 생각하면 된다.

- 큐를 만드는 메서드와 소비하는 메서드가 사실상 같은 실행 흐름 안에 있다
- "없으면 잠깐 기다리자" 같은 스레드 대기 계약이 없다
- 멀티스레드 안전성보다 코드 안의 순서 보존이 핵심이다

대표 예시는 두 가지다.

### BFS

`Queue<Node> q = new ArrayDeque<>();`로 시작해
현재 노드를 `poll`하고 이웃을 `offer`하는 흐름이면 충분하다.
여기서 중요한 것은 거리 순서 확장이지, 스레드 사이 handoff가 아니다.

### 메서드 안의 로컬 FIFO

한 요청을 처리하는 동안
"먼저 발견한 후처리 작업을 차례대로 처리"하는 정도라면 `ArrayDeque`가 단순하다.
이 경우 큐는 shared work queue가 아니라 **지역 작업 상자**에 가깝다.

## 언제 `BlockingQueue`로 질문을 바꿔야 하나

아래 신호가 보이면 beginner 관점에서도 `ArrayDeque`만으로 밀고 가면 안 된다.

- producer / consumer 스레드가 분리되어 있다
- worker가 할 일이 없으면 새 작업이 올 때까지 기다려야 한다
- 큐가 너무 길어질 때 무한정 쌓이면 안 된다
- "받은 순서대로 넘긴다"보다 "어떻게 안전하게 넘기고 멈추는가"가 더 중요하다

예를 들어 웹 요청 스레드가 작업을 enqueue하고,
백그라운드 worker가 `take()`로 꺼내 처리한다면 핵심은 이제 FIFO 자체보다 **handoff 계약**이다.

즉 `BlockingQueue`는 "더 고급 queue"라기보다,
`ArrayDeque`가 다루지 않던 질문을 대신 맡는 구조라고 보는 편이 쉽다.

## 흔한 오해와 함정

- "`ArrayDeque`도 queue니까 synchronized만 조금 하면 된다" -> 입문 단계에서는 이렇게 수동 동기화하기보다 `BlockingQueue`처럼 의도가 드러나는 구조가 안전하다.
- "`BlockingQueue`는 그냥 느린 queue다" -> 아니다. 느림/빠름보다 다른 스레드와 작업을 주고받는 계약을 표현한다.
- "`BlockingQueue`면 무조건 대용량 서비스 정답이다" -> 아니다. 비었을 때 기다리기, 꽉 찼을 때 실패/대기 같은 정책이 필요한지부터 봐야 한다.
- "`ArrayDeque`는 서비스 코드에서 못 쓴다" -> 아니다. 로컬 FIFO 버퍼나 단일 스레드 단계에서는 여전히 기본값이다.
- "`blocking`이 timer처럼 특정 시각까지 막아 준다" -> 아니다. 보통은 "원소가 없으면 기다린다"는 뜻이다. deadline 대기는 다른 질문이다.

## 실무에서 쓰는 모습

### 로컬 단계 정리용 큐

주문 요청 하나를 처리하면서
후속 검증 작업을 순서대로 펼쳐야 할 때는 `ArrayDeque`가 자연스럽다.
이 큐는 다른 worker에게 넘기는 통로가 아니라, 현재 요청 안에서 순서를 정리하는 도구다.

### worker handoff 큐

API 스레드가 작업을 넣고,
별도 worker 스레드가 작업을 꺼내 비동기 처리한다면 `BlockingQueue`가 더 맞다.
이때는 보통 아래 질문이 같이 붙는다.

- 비었으면 worker는 얼마나 기다리나
- 꽉 차면 producer는 대기하나, 실패하나
- shutdown 때 `take()` 중인 worker를 어떻게 멈추나

이 질문들은 `ArrayDeque` 선택 문제라기보다, `BlockingQueue` 계약 문제다.

## 더 깊이 가려면

- Java에서 로컬 FIFO 기본 구현 감각을 더 짧게 보려면 [ArrayDeque vs LinkedList 큐 선택 카드](./arraydeque-vs-linkedlist-queue-choice-card.md)
- queue/deque/priority queue 경계를 먼저 자르고 싶다면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- `BlockingQueue`의 고급 의미와 `TransferQueue` 차이를 더 보려면 [BlockingQueue, TransferQueue, and ConcurrentSkipListSet Semantics](../language/java/blockingqueue-transferqueue-concurrentskiplistset-semantics.md)
- `blocking`과 `timer`를 같은 뜻으로 오해했다면 [PriorityBlockingQueue Timer Misuse Primer](./priorityblockingqueue-timer-misuse-primer.md)

## 면접/시니어 질문 미리보기

1. 왜 BFS 큐는 `ArrayDeque`로 충분한가요?
   같은 스레드 흐름에서 FIFO 순서만 만들면 되고, worker handoff나 blocking 계약이 필요 없기 때문이다.
2. 언제 `BlockingQueue`로 바꿔야 하나요?
   여러 스레드가 작업을 주고받고, 비었을 때 대기나 꽉 찼을 때 정책이 필요해질 때다.
3. `BlockingQueue`를 쓰면 서비스 큐 문제가 다 끝나나요?
   아니다. capacity, timeout, shutdown, rejection 같은 운영 정책까지 함께 정해야 한다.

## 한 줄 정리

`ArrayDeque`는 같은 흐름 안에서 쓰는 로컬 FIFO 기본값이고, 여러 스레드 사이에 작업을 안전하게 넘기며 기다림과 포화 정책까지 표현해야 하면 `BlockingQueue`로 사고를 전환해야 한다.
