---
schema_version: 3
title: Backend Resilience Timeout Retry Mission Bridge
concept_id: system-design/backend-resilience-timeout-retry-mission-bridge
canonical: false
category: system-design
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: mixed
source_priority: 78
mission_ids:
- missions/payment
- missions/shopping-cart
- missions/backend
review_feedback_tags:
- backend-resilience
- timeout
- retry
- circuit-breaker
aliases:
- backend resilience timeout retry bridge
- backend external API resilience mission bridge
- timeout retry circuit breaker mission bridge
- 결제 API 장애 resilience 브리지
- retry budget backpressure bridge
symptoms:
- 외부 API가 느릴 때 timeout, retry, circuit breaker, idempotency를 한 흐름으로 연결하지 못한다
- payment나 backend 미션에서 재시도만 늘려 장애를 키우는 코드를 작성한다
- queue backlog와 thread pool 고갈을 개별 버그로만 보고 retry amplification을 설명하지 못한다
intents:
- mission_bridge
- troubleshooting
- design
prerequisites:
- system-design/retry-amplification-and-backpressure-primer
- system-design/circuit-breaker-basics
next_docs:
- system-design/backend-timeout-retry-circuit-breaker-drill
- system-design/request-deadline-timeout-budget-primer
- network/timeout-retry-backoff-practical
linked_paths:
- contents/system-design/retry-amplification-and-backpressure-primer.md
- contents/system-design/circuit-breaker-basics.md
- contents/system-design/backend-timeout-retry-circuit-breaker-drill.md
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
- backend 미션에서 timeout retry circuit breaker를 한 흐름으로 설명해줘
- 결제 API가 느릴 때 retry만 늘리면 왜 위험한지 mission bridge로 알려줘
- queue backlog와 retry amplification을 backend resilience 관점으로 연결해줘
- circuit breaker open 상태를 미션 리뷰 대응으로 어떻게 설명해?
- external API 장애 대응을 timeout budget idempotency backpressure 순서로 정리해줘
contextual_chunk_prefix: |
  이 문서는 backend resilience timeout retry mission_bridge다. external API
  slowdown, payment API timeout, retry amplification, queue backlog, thread
  pool exhaustion, circuit breaker open, idempotent retry 같은 미션 리뷰
  문장을 system design resilience 개념으로 매핑한다.
---
# Backend Resilience Timeout Retry Mission Bridge

> 한 줄 요약: backend resilience 리뷰는 "재시도하자"가 아니라, 한 요청이 얼마나 오래 자원을 붙잡고 몇 번까지 재시도되며 실패가 계속될 때 언제 차단할지 정하는 문제다.

**난이도: Intermediate**

## 미션 진입 증상

| backend 장면 | system design 질문 |
|---|---|
| 외부 API가 느린데 thread가 계속 묶임 | timeout budget이 있는가 |
| timeout마다 즉시 재시도 | retry amplification을 막는가 |
| 실패율이 계속 높음 | circuit breaker로 fail-fast해야 하는가 |
| write 요청 재시도 | idempotency key가 있는가 |
| queue backlog 증가 | backpressure나 load shedding이 필요한가 |

## 리뷰 신호

- "retry 횟수를 늘렸습니다"는 개선이 아니라 전체 attempt 수와 deadline을 같이 설명하라는 신호일 수 있다.
- "간헐적 timeout이라 재시도하면 됩니다"는 같은 요청이 이미 처리 중일 수 있음을 보라는 말이다.
- "외부 API 장애 때 우리 서비스도 느려져요"는 circuit breaker와 thread pool 보호를 연결하라는 뜻이다.
- "queue에 쌓아 두면 안전합니다"는 queue age, bounded policy, consumer capacity를 같이 확인하라는 신호다.

## 판단 순서

1. 한 attempt의 timeout을 전체 request deadline 안에 둔다.
2. retry는 bounded, backoff, jitter, remaining budget 기준으로 제한한다.
3. write 부작용이 있으면 idempotency key 또는 status lookup을 먼저 둔다.
4. 실패가 계속되면 circuit breaker로 새 외부 호출을 줄인다.
5. backlog가 쌓이면 큐가 복구를 돕는지 장애를 연장하는지 본다.

이렇게 연결하면 backend 미션의 외부 API 장애 리뷰가 단순 예외 처리에서 resilience 설계로 올라간다.
