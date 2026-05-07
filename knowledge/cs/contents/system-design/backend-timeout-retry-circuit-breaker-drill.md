---
schema_version: 3
title: Backend Timeout Retry Circuit Breaker Drill
concept_id: system-design/backend-timeout-retry-circuit-breaker-drill
canonical: false
category: system-design
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
- timeout
- retry-budget
- circuit-breaker
- backpressure
aliases:
- backend timeout retry circuit breaker drill
- timeout retry circuit breaker exercise
- backend retry storm drill
- 외부 API 장애 차단 드릴
- retry amplification circuit breaker drill
symptoms:
- 외부 API가 느릴 때 timeout, retry, circuit breaker 중 무엇을 먼저 봐야 하는지 헷갈린다
- 실패가 나면 재시도를 늘리면 된다고 생각해 retry amplification을 놓친다
- circuit breaker open 상태를 에러가 아니라 보호 동작으로 설명하지 못한다
intents:
- drill
- troubleshooting
- design
prerequisites:
- system-design/retry-amplification-and-backpressure-primer
- system-design/circuit-breaker-basics
next_docs:
- system-design/request-deadline-timeout-budget-primer
- network/timeout-retry-backoff-practical
- system-design/idempotency-key-store-dedup-window-replay-safe-retry-design
linked_paths:
- contents/system-design/retry-amplification-and-backpressure-primer.md
- contents/system-design/circuit-breaker-basics.md
- contents/system-design/request-deadline-timeout-budget-primer.md
- contents/network/timeout-retry-backoff-practical.md
- contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md
confusable_with:
- system-design/retry-amplification-and-backpressure-primer
- system-design/circuit-breaker-basics
- system-design/request-deadline-timeout-budget-primer
forbidden_neighbors:
- contents/algorithm/rate-limiter-algorithms.md
expected_queries:
- backend timeout retry circuit breaker를 문제로 연습하고 싶어
- 외부 API가 느릴 때 retry를 늘리면 왜 장애가 커지는지 드릴해줘
- circuit breaker open 상태를 미션 리뷰 문장으로 설명해줘
- payment API timeout 이후 재시도와 idempotency를 어떻게 같이 봐야 해?
- queue backlog가 있는데 계속 retry하는 코드가 왜 위험한지 문제로 풀어줘
contextual_chunk_prefix: |
  이 문서는 backend timeout retry circuit breaker drill이다. external API
  timeout, retry amplification, retry budget, circuit breaker open/half-open,
  backpressure, idempotent retry 같은 미션 리뷰 문장을 선택 문제로 매핑한다.
---
# Backend Timeout Retry Circuit Breaker Drill

> 한 줄 요약: timeout은 붙잡힌 요청을 끊고, retry는 일시 실패를 흡수하며, circuit breaker는 실패가 계속될 때 호출 자체를 줄인다.

**난이도: Beginner**

## 문제 1

상황:

```text
결제 API가 3초씩 느린데 client timeout은 10초이고, 요청마다 worker thread가 계속 묶인다.
```

답:

먼저 timeout budget을 줄여 붙잡힌 시간을 제한한다. retry나 circuit breaker 이전에 한 시도가 얼마 동안 자원을 점유하는지 닫아야 한다.

## 문제 2

상황:

```text
timeout이 나면 즉시 3번 재시도한다. 이전 시도는 아직 외부 서버에서 처리 중일 수 있다.
```

답:

retry amplification 위험이 있다. 남은 deadline과 backoff 없이 새 시도를 열면 같은 logical request가 여러 attempt로 겹친다.
write 요청이면 idempotency key도 함께 봐야 한다.

## 문제 3

상황:

```text
외부 API 실패율이 계속 80%인데 모든 요청이 계속 외부로 나가며 thread pool이 고갈된다.
```

답:

circuit breaker 후보 장면이다. 잠깐 Open으로 전환해 fail-fast/fallback을 주고, Half-Open에서 소수 요청으로 복구를 확인한다.

## 빠른 체크

| 증상 | 먼저 볼 장치 |
|---|---|
| 한 요청이 너무 오래 묶임 | timeout |
| 일시 실패를 한두 번 흡수 | bounded retry + backoff |
| 실패가 계속되어 내 서비스까지 느려짐 | circuit breaker |
| retry가 write 부작용을 두 번 만들 수 있음 | idempotency key |
