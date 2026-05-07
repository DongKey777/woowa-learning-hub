---
schema_version: 3
title: ALB, ELB Retry Amplification, Proxy Chain
concept_id: network/alb-elb-retry-amplification-proxy-chain
canonical: false
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- retry-amplification
- proxy-chain
- load-balancer-retry
aliases:
- ALB ELB retry amplification
- proxy chain retry
- load balancer retry storm
- upstream retry amplification
- request duplication
- tail latency retry
- circuit breaker backoff
symptoms:
- client, gateway, LB, app retry가 각각 한 번씩만 돈다고 보고 전체 요청 수 증폭과 tail latency 붕괴를 계산하지 않는다
- retry를 늘리면 transient failure가 모두 좋아진다고 생각해 backoff, jitter, circuit breaker, load shedding 없이 겹쳐 둔다
- idempotent하지 않은 작업에 LB/app retry가 겹쳐 같은 요청이 두 번 처리되는 부작용을 놓친다
intents:
- design
- troubleshooting
prerequisites:
- network/timeout-retry-backoff-practical
- network/api-gateway-reverse-proxy-operational-points
next_docs:
- network/retry-storm-containment-concurrency-limiter-load-shedding
- network/connection-keepalive-loadbalancing-circuit-breaker
- network/tcp-reset-storms-idle-reuse-stale-sockets
linked_paths:
- contents/network/load-balancer-healthcheck-failure-patterns.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/network/timeout-retry-backoff-practical.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/tcp-reset-storms-idle-reuse-stale-sockets.md
- contents/network/retry-storm-containment-concurrency-limiter-load-shedding.md
confusable_with:
- network/retry-storm-containment-concurrency-limiter-load-shedding
- network/timeout-retry-backoff-practical
- network/connection-keepalive-loadbalancing-circuit-breaker
- network/api-gateway-reverse-proxy-operational-points
forbidden_neighbors: []
expected_queries:
- ALB ELB gateway app retry가 겹치면 retry amplification이 어떻게 생겨?
- proxy chain에서 작은 5xx나 timeout이 request duplication과 tail latency 붕괴로 커지는 이유는?
- retry backoff jitter circuit breaker load shedding을 같이 써야 하는 이유는?
- LB retry와 app retry의 경계를 idempotency 관점에서 어떻게 정해야 해?
- retry storm을 막으려면 어느 계층에서 몇 번만 재시도하도록 제한해야 해?
contextual_chunk_prefix: |
  이 문서는 ALB/ELB와 proxy chain에서 client, gateway, load balancer, app retry가
  겹쳐 retry amplification과 request duplication, tail latency collapse를 만드는
  과정을 설명한다. backoff, jitter, circuit breaker, idempotency, load shedding을 함께 다룬다.
---
# ALB, ELB Retry Amplification, Proxy Chain

> 한 줄 요약: L4/L7 프록시와 로드밸런서에 retry가 여러 겹 쌓이면, 작은 실패가 트래픽 폭증과 tail latency 붕괴로 커질 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [TCP Reset Storms, Idle Reuse, Stale Sockets](./tcp-reset-storms-idle-reuse-stale-sockets.md)
> - [Retry Storm Containment, Concurrency Limiter, Load Shedding](./retry-storm-containment-concurrency-limiter-load-shedding.md)

retrieval-anchor-keywords: retry amplification, proxy chain, ALB, ELB, load balancer retry, upstream retry, tail latency, request duplication, circuit breaker, backoff

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

retry amplification은 한 홉의 실패를 다음 홉이 다시 시도하면서 **실제 요청 수가 기하급수적으로 늘어나는 현상**이다.

- client retry
- gateway retry
- LB retry
- app retry

이게 겹치면 작은 5xx나 timeout이 전체 시스템 부하를 키운다.

### Retrieval Anchors

- `retry amplification`
- `proxy chain`
- `ALB`
- `ELB`
- `load balancer retry`
- `upstream retry`
- `tail latency`
- `request duplication`
- `circuit breaker`
- `backoff`

## 깊이 들어가기

### 1. 왜 여러 겹이 위험한가

각 계층은 자신이 "한 번 더" 시도해도 된다고 생각할 수 있다.

- client는 네트워크가 잠깐 흔들렸다고 본다
- gateway는 upstream이 잠깐 느렸다고 본다
- LB는 다른 healthy node로 보내면 된다고 본다
- app은 내부 dependency retry를 붙인다

하지만 합치면 요청량이 크게 늘어난다.

### 2. retry는 왜 증폭되나

실패가 나면 retry가 새 connection과 새 큐잉을 만든다.

- 원래 실패한 요청을 다시 보낸다
- 그 사이 backlog와 pool이 더 밀린다
- 건강한 서버까지 느려진다

### 3. 어디서 가장 자주 생기나

- 502/503/504
- idle timeout mismatch
- transient network drop
- health check false positive

### 4. backoff만으로 충분한가

아니다.

- backoff는 폭발 속도를 늦춘다
- circuit breaker는 실패 구간에서 멈춘다
- idempotency는 중복 요청 부작용을 줄인다

이 셋을 같이 써야 한다.

### 5. LB retry와 app retry의 경계

LB retry는 transport/route 장애를 흡수할 수 있지만,
app retry는 비즈니스 부작용을 만들 수 있다.

그래서 **어디서 retry를 허용할지 한 번에 정해야 한다**.

## 실전 시나리오

### 시나리오 1: p99가 높아지자 retry가 더 늘었다

retry가 tail latency를 더 악화시켰을 수 있다.

### 시나리오 2: 한 backend가 느려지자 전체 클러스터가 같이 느려진다

proxy chain이 retry를 겹쳐 쓰면 건강한 노드까지 영향을 받는다.

### 시나리오 3: 같은 요청이 두 번 처리됐다

retry가 idempotent하지 않은 작업에 들어갔을 수 있다.

## 코드로 보기

### 지표로 보기

```text
retry count
5xx rate
upstream latency
pool saturation
```

### 구성 감각

```text
client retry: limited
gateway retry: selective
LB retry: cautious
app retry: idempotent only
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 다층 retry | transient failure를 흡수한다 | amplification 위험이 크다 | 신중하게 제한 |
| 단일 retry 계층 | 단순하다 | 일부 failure를 놓친다 | 안정성이 중요할 때 |
| retry + breaker + backoff | 균형이 좋다 | 설계가 복잡하다 | 일반 운영 |

핵심은 retry를 많이 두는 것이 아니라 **한 번만, 어디서, 어떤 조건으로** 할지 정하는 것이다.

## 꼬리질문

> Q: retry amplification이란 무엇인가요?
> 핵심: 여러 계층의 retry가 겹쳐 실제 요청량이 폭증하는 현상이다.

> Q: 왜 LB와 app retry를 같이 조심해야 하나요?
> 핵심: transport retry와 business retry가 합쳐지면 부작용이 커진다.

> Q: 어떻게 줄이나요?
> 핵심: retry 위치를 줄이고 backoff, jitter, circuit breaker를 같이 쓴다.

## 한 줄 정리

ALB/ELB와 proxy chain에서 retry가 겹치면 작은 실패가 증폭되므로, retry 위치와 횟수를 계층별로 제한해야 한다.
