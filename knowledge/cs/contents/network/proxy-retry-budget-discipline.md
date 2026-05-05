---
schema_version: 3
title: Proxy Retry Budget Discipline
concept_id: network/proxy-retry-budget-discipline
canonical: true
category: network
difficulty: advanced
doc_role: primer
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- idempotent-retry-boundary
- retry-amplification
- retry-budget-missing
aliases:
- retry budget
- proxy retry
- budget exhaustion
- backoff
- jitter
- amplification control
- idempotency
- upstream failover
- request storm
symptoms:
- 장애 때 재시도할수록 더 느려져
- 프록시와 앱이 둘 다 retry하는 것 같아
- 실패 순간 트래픽이 폭증해
intents:
- definition
prerequisites:
- network/timeout-retry-backoff-practical
- network/http-methods-rest-idempotency-basics
next_docs:
- network/timeout-budget-propagation-proxy-gateway-service-hop-chain
- network/retry-storm-containment-concurrency-limiter-load-shedding
linked_paths:
- contents/network/alb-elb-retry-amplification-proxy-chain.md
- contents/network/timeout-retry-backoff-practical.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/network/grpc-deadlines-cancellation-propagation.md
- contents/network/retry-storm-containment-concurrency-limiter-load-shedding.md
- contents/spring/spring-mvc-async-deferredresult-callable-dispatch.md
confusable_with:
- network/timeout-budget-propagation-proxy-gateway-service-hop-chain
- network/alb-elb-retry-amplification-proxy-chain
forbidden_neighbors:
- contents/network/browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge.md
expected_queries:
- proxy retry budget은 왜 필요하고 어디에서 소진되나요?
- 여러 계층이 같이 재시도할 때 트래픽 증폭을 어떻게 막나요?
- 멱등하지 않은 요청까지 프록시가 재시도하면 왜 위험한가요?
- retry budget을 다 쓰면 그냥 실패시키는 게 맞나요?
- 재시도 예산과 backoff를 같이 보는 이유가 궁금해요
contextual_chunk_prefix: |
  이 문서는 운영 학습자가 장애 순간 프록시와 애플리케이션의 재시도가 복구인지 증폭인지 판단하고 제한 규칙을 이해하도록 기초를 잡는 primer다. 실패할수록 더 느려짐, 여러 계층이 동시에 다시 보냄, 잠깐 흔들린 호출만 제한적으로 살리기, 멱등 요청만 조심해서 재전송하기, 복구 시도가 트래픽 폭증으로 번지는 장면 같은 자연어 paraphrase가 본 문서의 핵심 개념에 매핑된다.
---
# Proxy Retry Budget Discipline

> 한 줄 요약: retry budget은 프록시와 앱이 실패를 얼마나 재시도할지 정하는 안전장치로, 예산을 넘기면 복구가 아니라 증폭이 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [ALB, ELB Retry Amplification, Proxy Chain](./alb-elb-retry-amplification-proxy-chain.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [TCP Reset Storms, Idle Reuse, Stale Sockets](./tcp-reset-storms-idle-reuse-stale-sockets.md)
> - [gRPC Deadlines, Cancellation Propagation](./grpc-deadlines-cancellation-propagation.md)
> - [Retry Storm Containment, Concurrency Limiter, Load Shedding](./retry-storm-containment-concurrency-limiter-load-shedding.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../spring/spring-mvc-async-deferredresult-callable-dispatch.md)

retrieval-anchor-keywords: retry budget, proxy retry, budget exhaustion, backoff, jitter, amplification control, idempotency, upstream failover, request storm

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로 보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한 줄 정리)

</details>

## 핵심 개념

retry budget은 일정 시간이나 요청 수 안에서 재시도를 제한하는 규칙이다.

- proxy가 마음대로 무한 retry하지 않게 한다
- app retry와 합쳐져 폭증하지 않게 한다
- 실패를 빨리 숨기지 않고, 제한된 범위에서만 복구한다

### Retrieval Anchors

- `retry budget`
- `proxy retry`
- `budget exhaustion`
- `backoff`
- `jitter`
- `amplification control`
- `idempotency`
- `upstream failover`
- `request storm`

## 깊이 들어가기

### 1. 왜 budget이 필요한가

retry는 좋게 보면 복구, 나쁘게 보면 증폭이다.

- 잠깐의 네트워크 흔들림은 흡수할 수 있다
- 하지만 여러 계층이 동시에 retry하면 위험하다

### 2. 프록시가 왜 위험한가

프록시는 많은 요청을 한 번에 받는다.

- LB에서 retry
- gateway에서 retry
- app client에서 retry

이 셋이 겹치면 예산이 쉽게 바닥난다.

### 3. budget을 어디에 두나

- per-request budget
- per-connection budget
- per-minute or per-cluster budget

운영에서는 보통 요청과 시간 두 축을 함께 본다.

### 4. idempotency가 왜 같이 나오나

retry는 같은 요청을 다시 보낼 수 있다.

- 멱등 요청이면 비교적 안전하다
- 비멱등 요청이면 부작용이 커질 수 있다

### 5. budget이 바닥나면

retry를 멈추고 실패를 드러내는 편이 낫다.

- tail latency를 지킨다
- downstream을 보호한다
- circuit breaker와 함께 작동한다

## 실전 시나리오

### 시나리오 1: 장애가 커질수록 retry가 줄어들지 않는다

budget이 없거나 너무 넓을 수 있다.

### 시나리오 2: proxy와 app이 서로 retry한다

한 요청이 여러 번 증폭된다.

### 시나리오 3: 멱등하지 않은 요청이 두 번 처리됐다

retry 허용 범위가 잘못됐을 수 있다.

## 코드로 보기

### 정책 감각

```text
max retries: limited
budget window: bounded
retry only if idempotent
respect deadline
```

### 관찰 포인트

```bash
curl -w 'time_total=%{time_total}\n' -o /dev/null -s https://api.example.com
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 넉넉한 retry budget | transient failure를 흡수한다 | 폭증 위험이 있다 | 안정망이 있을 때 |
| 엄격한 retry budget | 시스템 보호가 된다 | 일부 실패를 사용자에게 드러낸다 | 장애 억제 우선 |
| no retry | 단순하다 | 작은 흔들림도 실패로 보인다 | 매우 민감한 작업 |

핵심은 retry를 없애는 것이 아니라 **예산 안에서만 허용하는 것**이다.

## 꼬리질문

> Q: retry budget은 왜 필요한가요?
> 핵심: 여러 계층의 retry가 합쳐져 폭증하는 것을 막기 위해서다.

> Q: idempotency는 왜 중요하나요?
> 핵심: 같은 요청을 다시 보내도 안전한지 판단해야 하기 때문이다.

> Q: budget이 다 쓰이면 어떻게 하나요?
> 핵심: 더 재시도하지 말고 실패를 드러내 downstream을 보호한다.

## 한 줄 정리

retry budget은 proxy와 app의 재시도를 제한하는 안전장치라서, 예산을 넘기면 복구가 아니라 트래픽 증폭이 된다.
