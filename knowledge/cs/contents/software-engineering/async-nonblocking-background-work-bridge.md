---
schema_version: 3
title: Async, Nonblocking, and Background Work Bridge
concept_id: software-engineering/async-nonblocking-background-work-bridge
canonical: true
category: software-engineering
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 84
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- async-background-work
- nonblocking-vs-background
- response-boundary
- coroutine-bridge
aliases:
- async nonblocking background work
- 비동기 논블로킹 백그라운드 작업
- background job vs nonblocking
- 응답 후 처리
- coroutine background work bridge
symptoms:
- 오래 걸리는 일을 비동기로 빼야 한다는 말과 nonblocking으로 바꿔야 한다는 말을 섞어 쓰고 있다
- HTTP 응답 전에 끝나야 하는 일과 응답 후 처리해도 되는 일을 구분하지 못한다
- coroutine, thread pool, queue, scheduler 중 무엇을 골라야 할지 모르겠다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- operating-system/sync-async-blocking-nonblocking-basics
- software-engineering/software-engineering-index
next_docs:
- system-design/sync-api-vs-async-job-decision-chooser
- operating-system/blocking-io-thread-pool-backpressure-primer
- language/coroutine-basics
linked_paths:
- contents/operating-system/sync-async-blocking-nonblocking-basics.md
- contents/system-design/sync-api-vs-async-job-decision-chooser.md
- contents/operating-system/blocking-io-thread-pool-backpressure-primer.md
- contents/language/coroutine.md
- contents/software-engineering/idempotency-retry-consistency-boundaries.md
- contents/system-design/consistency-idempotency-async-workflow-foundations.md
confusable_with:
- operating-system/sync-async-blocking-nonblocking-basics
- system-design/sync-api-vs-async-job-decision-chooser
- language/coroutine-basics
forbidden_neighbors: []
expected_queries:
- async와 nonblocking과 background job은 어떻게 달라?
- 오래 걸리는 작업을 응답 뒤로 넘기는 것과 nonblocking IO는 같은 말이야?
- coroutine을 쓰면 background queue가 필요 없어지는지 설명해줘
- HTTP 요청에서 꼭 지금 끝내야 하는 일과 나중에 처리할 일을 어떻게 나눠?
- 비동기 작업으로 빼면 retry와 idempotency를 왜 같이 봐야 해?
contextual_chunk_prefix: |
  이 문서는 async, nonblocking, background work를 software-engineering 관점에서
  구분하는 bridge다. 오래 걸리는 작업을 응답 뒤로 넘길지, blocking IO를
  thread pool로 격리할지, coroutine이 필요한지, queue와 retry/idempotency가
  필요한지 묻는 자연어 질문을 응답 경계와 작업 완료 책임 기준으로 연결한다.
---
# Async, Nonblocking, and Background Work Bridge

> 한 줄 요약: async는 "완료 시점을 분리한다"는 말이고, nonblocking은 "기다리는 동안 실행 자원을 붙잡지 않는다"는 말이며, background work는 "응답 경계 밖의 작업으로 운영 책임을 넘긴다"는 말이다.

**난이도: Beginner**

## 세 단어를 먼저 분리하기

| 단어 | 핵심 질문 | 예시 |
|---|---|---|
| async | 결과를 지금 받을 필요가 있는가 | 알림 발송을 주문 응답 뒤로 보냄 |
| nonblocking | 기다리는 동안 thread를 붙잡는가 | socket IO를 event loop로 처리 |
| background work | 실패, 재시도, 관측을 별도 작업으로 관리할 것인가 | outbox relay, email worker, batch job |

`async`라고 해서 자동으로 빠르고 안전해지는 것은 아니다.
응답 뒤로 넘긴 순간부터는 "실패하면 누가 다시 하나", "중복 실행되면 안전한가", "사용자는 완료 상태를 어디서 보나"가 설계 질문이 된다.

## 선택 순서

1. 사용자 응답 전에 반드시 끝나야 하는 일인지 확인한다.
2. 외부 I/O 대기인지 CPU 계산인지 나눈다.
3. 응답 뒤로 넘겨도 되면 idempotency와 retry key를 먼저 붙인다.
4. 대기 시간이 문제라면 thread pool 격리, nonblocking IO, queue 중 병목 위치에 맞춰 고른다.

## 흔한 오해

| 오해 | 교정 |
|---|---|
| `@Async`를 붙이면 nonblocking이 된다 | 별도 thread에서 blocking할 수 있다 |
| coroutine이면 background job이 필요 없다 | 완료 책임과 retry가 남으면 queue나 outbox가 필요할 수 있다 |
| 응답 뒤 작업은 실패해도 사용자와 무관하다 | 사용자에게 보이는 상태나 보상 경로가 필요하다 |
| 오래 걸리면 전부 비동기 처리한다 | 지금 완료되어야 하는 invariant는 동기로 남겨야 한다 |

## 다음 문서

- API 응답과 job 분리는 [Sync API vs Async Job](../system-design/sync-api-vs-async-job-decision-chooser.md)에서 고른다.
- thread pool 경합은 [Blocking I/O, 스레드 풀, 백프레셔 입문](../operating-system/blocking-io-thread-pool-backpressure-primer.md)으로 본다.
- 언어 수준 coroutine은 [Coroutine](../language/coroutine.md)으로 내려간다.
