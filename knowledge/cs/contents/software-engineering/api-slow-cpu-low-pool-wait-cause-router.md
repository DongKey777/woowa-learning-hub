---
schema_version: 3
title: API가 느린데 CPU는 낮을 때 pool wait부터 가르는 원인 라우터
concept_id: software-engineering/api-slow-cpu-low-pool-wait-cause-router
canonical: false
category: software-engineering
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 88
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- latency-triage
- thread-pool-vs-db-pool
- app-vs-db-bottleneck
aliases:
- api slow cpu low pool wait
- API 느린데 CPU 낮음
- app slow db fast
- thread pool vs connection pool starvation
- backend latency first split
- 요청은 느린데 쿼리는 빠름
- 커넥션 풀 대기인지 스레드 풀 대기인지
symptoms:
- API p95가 튀는데 CPU 사용률은 낮고 slow query도 뚜렷하지 않다
- DB 쿼리 자체는 빠른데 요청 전체 시간만 길어져 thread pool과 connection pool 중 어디를 볼지 모르겠다
- Hikari `threads awaiting connection`, executor queue, upstream pending acquire가 한 번에 보여 어느 대기열이 원인인지 헷갈린다
intents:
- symptom
- troubleshooting
prerequisites:
- software-engineering/test-strategy-basics
- operating-system/process-thread-memory-state-classification-practice-drill
next_docs:
- database/timeout-log-timeline-first-failure-checklist-card
- database/hikari-connection-pool-tuning
- database/pool-metrics-lock-wait-timeout-mini-bridge
- operating-system/blocking-io-thread-pool-backpressure-primer
- network/upstream-queueing-connection-pool-wait-tail-latency
- database/slow-query-analysis-playbook
- language/thread-dump-state-interpretation
linked_paths:
- contents/database/timeout-log-timeline-first-failure-checklist-card.md
- contents/database/hikari-connection-pool-tuning.md
- contents/database/pool-metrics-lock-wait-timeout-mini-bridge.md
- contents/operating-system/blocking-io-thread-pool-backpressure-primer.md
- contents/network/upstream-queueing-connection-pool-wait-tail-latency.md
- contents/database/slow-query-analysis-playbook.md
- contents/language/java/thread-dump-state-interpretation.md
- contents/spring/spring-taskexecutor-taskscheduler-overload-rejection-semantics.md
- contents/system-design/backpressure-and-load-shedding-design.md
confusable_with:
- database/hikari-connection-pool-tuning
- database/slow-query-analysis-playbook
- operating-system/blocking-io-thread-pool-backpressure-primer
- network/upstream-queueing-connection-pool-wait-tail-latency
forbidden_neighbors: []
expected_queries:
- API는 느린데 CPU가 낮고 DB 쿼리는 빠르면 어디부터 봐야 해?
- thread pool starvation이랑 DB connection pool starvation을 처음에 어떻게 구분해?
- Hikari active idle awaiting 지표와 executor queue가 같이 보일 때 원인 순서를 어떻게 잡아?
- 요청 p95가 늘었는데 slow query가 없으면 thread dump부터 봐야 해 pool metrics부터 봐야 해?
- upstream pending acquire와 DB pool wait 중 어느 대기열이 tail latency 원인인지 빠르게 가르는 표가 필요해
contextual_chunk_prefix: |
  이 문서는 API latency가 커졌지만 CPU는 낮고 slow query가 뚜렷하지 않을 때
  thread pool wait, DB connection pool wait, upstream connection pool wait,
  DB lock/query wait를 처음 가르는 symptom_router다. API slow but DB fast,
  p95 증가, threads awaiting connection, executor queue, pending acquire,
  thread dump WAITING/RUNNABLE 같은 신호를 어떤 순서로 볼지 안내한다.
---

# API가 느린데 CPU는 낮을 때 pool wait부터 가르는 원인 라우터

> 한 줄 요약: API가 느린데 CPU가 낮으면 "계산이 느리다"보다 **어딘가의 대기열에서 기다린다**는 신호일 수 있다. 먼저 request timeline에서 기다린 위치를 잡고, thread pool, DB connection pool, upstream connection pool, DB query/lock 중 하나로 보낸다.

**난이도: 🟢 Beginner**

관련 문서:

- [HikariCP 커넥션 풀 튜닝](../database/hikari-connection-pool-tuning.md)
- [Timeout 로그 타임라인 체크리스트 카드](../database/timeout-log-timeline-first-failure-checklist-card.md)
- [Pool 지표와 Lock Wait Timeout 미니 브리지](../database/pool-metrics-lock-wait-timeout-mini-bridge.md)
- [Blocking I/O Thread Pool Backpressure Primer](../operating-system/blocking-io-thread-pool-backpressure-primer.md)
- [Upstream Queueing / Connection Pool Wait Tail Latency](../network/upstream-queueing-connection-pool-wait-tail-latency.md)
- [느린 쿼리 분석 플레이북](../database/slow-query-analysis-playbook.md)
- [Java Thread Dump State Interpretation](../language/java/thread-dump-state-interpretation.md)
- [Spring TaskExecutor / TaskScheduler Overload Semantics](../spring/spring-taskexecutor-taskscheduler-overload-rejection-semantics.md)

## 먼저 붙일 질문

처음에는 "서버가 느리다"를 한 덩어리로 보지 말고 **요청이 어느 입구에서 줄을 섰는지**만 나눈다.

| 먼저 보이는 신호 | 더 가까운 원인 | 먼저 갈 문서 |
|---|---|---|
| executor queue가 늘고 worker가 계속 바쁘다 | thread pool / worker pool 포화 | [Blocking I/O Thread Pool Backpressure Primer](../operating-system/blocking-io-thread-pool-backpressure-primer.md) |
| Hikari `active ~= max`, `idle = 0`, `threads awaiting connection` | DB connection pool 대기 | [HikariCP 커넥션 풀 튜닝](../database/hikari-connection-pool-tuning.md) |
| WebClient/Reactor Netty `pending acquire`, upstream pool wait | HTTP client connection pool 대기 | [Upstream Queueing / Connection Pool Wait Tail Latency](../network/upstream-queueing-connection-pool-wait-tail-latency.md) |
| query 시간이 실제로 길고 `EXPLAIN` row가 크다 | DB query/plan 문제 | [느린 쿼리 분석 플레이북](../database/slow-query-analysis-playbook.md) |
| DB lock wait, blocker, `Lock wait timeout exceeded` | lock 대기 때문에 connection hold time 증가 | [Pool 지표와 Lock Wait Timeout 미니 브리지](../database/pool-metrics-lock-wait-timeout-mini-bridge.md) |

## 빠른 순서

1. 요청 전체 시간을 `controller 진입 전`, `service 내부`, `DB borrow`, `query`, `upstream call`, `response write`로 나눈다.
2. CPU가 낮으면 계산보다 대기열을 먼저 의심한다.
3. pool 지표는 원인 판결이 아니라 **어느 입구가 막혔는지**를 보여 주는 표지로 읽는다.
4. thread dump는 "worker가 어디서 기다리는지"를 확인할 때 연다.
5. pool size를 키우기 전에 hold time, timeout, retry, 외부 I/O in transaction을 확인한다.

## 흔한 오해

- `threads awaiting connection`이 보이면 Hikari maximumPoolSize만 올리면 된다고 본다. 실제 원인은 긴 트랜잭션, lock wait, 외부 API 호출을 트랜잭션 안에서 기다린 구조일 수 있다.
- slow query가 없으니 DB는 완전히 무관하다고 본다. query는 빨라도 connection을 빌리기 전 대기 시간이 길 수 있다.
- CPU가 낮으니 서버가 한가하다고 본다. thread가 socket, DB connection, lock, upstream 응답을 기다리면 CPU는 낮아도 p95는 커진다.
- thread pool과 connection pool을 같은 queue로 본다. thread pool은 실행 worker의 좌석이고, connection pool은 DB나 upstream과 통신할 연결 좌석이다.

## 한 문장 판단

`CPU 낮음 + p95 증가 + slow query 없음`이면 먼저 **대기 위치**를 찾고, `executor queue`, `threads awaiting connection`, `pending acquire`, `lock wait`, `query time` 중 가장 먼저 증가한 신호로 다음 문서를 고른다.
