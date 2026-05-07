---
schema_version: 3
title: Backend Queue Handoff Selection Drill
concept_id: data-structure/backend-queue-handoff-selection-drill
canonical: false
category: data-structure
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/payment
- missions/shopping-cart
- missions/backend
review_feedback_tags:
- queue
- worker-handoff
- blockingqueue
- backpressure
aliases:
- backend queue handoff selection drill
- ArrayDeque BlockingQueue worker queue drill
- service handoff queue drill
- bounded queue backpressure drill
- 백엔드 큐 handoff 드릴
symptoms:
- queue라는 단어만 보고 BFS 큐, local FIFO, worker handoff를 같은 것으로 처리한다
- 여러 thread가 작업을 주고받는데 ArrayDeque를 그대로 써도 되는지 판단하지 못한다
- bounded queue가 꽉 찼을 때 reject, block, drop 중 어떤 정책인지 정하지 않는다
intents:
- drill
- comparison
- design
prerequisites:
- data-structure/backend-data-structure-starter-pack
- data-structure/arraydeque-vs-blockingqueue-service-handoff-primer
next_docs:
- data-structure/bounded-queue-policy-primer
- system-design/retry-amplification-and-backpressure-primer
- software-engineering/message-driven-adapter
linked_paths:
- contents/data-structure/backend-data-structure-starter-pack.md
- contents/data-structure/arraydeque-vs-blockingqueue-service-handoff-primer.md
- contents/data-structure/queue-basics.md
- contents/data-structure/bounded-queue-policy-primer.md
- contents/system-design/retry-amplification-and-backpressure-primer.md
- contents/software-engineering/message-driven-adapter-example.md
confusable_with:
- data-structure/arraydeque-vs-blockingqueue-service-handoff-primer
- data-structure/queue-basics
- system-design/job-queue-design
forbidden_neighbors:
- contents/algorithm/dfs-bfs-intro.md
expected_queries:
- backend queue handoff에서 ArrayDeque와 BlockingQueue를 문제로 연습하고 싶어
- service 코드에 queue가 나오면 자료구조인지 worker handoff인지 어떻게 구분해?
- bounded queue가 꽉 차면 reject block drop 중 무엇을 골라야 해?
- 결제 이벤트 worker queue를 BlockingQueue로 둘 때 backpressure를 어떻게 봐?
- BFS queue와 backend worker queue를 헷갈리지 않는 드릴을 줘
contextual_chunk_prefix: |
  이 문서는 backend queue handoff selection drill이다. ArrayDeque,
  BlockingQueue, worker handoff, bounded queue, backpressure, reject/block/drop
  policy, BFS queue confusion 같은 미션 질문을 자료구조 선택 문제로
  매핑한다.
---
# Backend Queue Handoff Selection Drill

> 한 줄 요약: backend에서 queue는 "순서대로 담는 자료구조"일 수도 있고, "thread 사이 작업 handoff 계약"일 수도 있다.

**난이도: Beginner**

## 문제 1

상황:

```text
한 메서드 안에서 요청 DTO를 순서대로 처리하려고 임시 queue를 쓴다.
thread는 하나다.
```

답:

local FIFO라면 `ArrayDeque`로 충분하다. blocking, wake-up, backpressure 계약이 필요하지 않다.

## 문제 2

상황:

```text
HTTP 요청 thread가 작업을 넣고 worker thread가 나중에 꺼내 처리한다.
```

답:

worker handoff다. thread-safe blocking queue나 더 명시적인 job queue를 봐야 한다.
여기서는 FIFO 자료구조보다 생산자/소비자 경계와 종료/실패 정책이 중요하다.

## 문제 3

상황:

```text
결제 후속 이벤트 queue가 가득 찼는데 요청 thread가 무한정 block된다.
```

답:

bounded queue policy가 빠졌다. reject, block, drop, overflow storage 중 무엇이 도메인에 맞는지 정해야 한다.
돈이나 주문 상태가 걸린 이벤트라면 단순 drop은 위험하다.

## 빠른 체크

| 질문 | 먼저 볼 문서 |
|---|---|
| 한 thread 안 임시 FIFO | queue basics / ArrayDeque |
| thread 사이 handoff | BlockingQueue |
| queue full 정책 | bounded queue policy |
| 외부 시스템까지 durable delivery | message adapter / outbox |
