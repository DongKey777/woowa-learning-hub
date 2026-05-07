---
schema_version: 3
title: "DNS TTL Cache Failure Patterns"
concept_id: network/dns-ttl-cache-failure-patterns
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- dns-ttl-cache
- stale-resolver-propagation
- blue-green-dns-failover
aliases:
- DNS TTL
- stale resolver
- cache propagation
- blue-green DNS
- authoritative recursive resolver
- DNS propagation delay
symptoms:
- DNS 레코드를 바꿨는데 일부 지역이나 일부 사용자만 오래된 IP를 계속 본다
- TTL을 짧게 하면 항상 장애 전환이 안전해진다고 단정한다
- authoritative DNS는 바뀌었지만 browser OS recursive resolver cache가 남은 상태를 구분하지 못한다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- network/dns-basics
- network/dns-split-horizon-behavior
next_docs:
- network/dns-negative-caching-nxdomain-behavior
- network/connection-reuse-vs-service-discovery-churn
- network/happy-eyeballs-dual-stack-racing
- network/anycast-routing-tradeoffs-edge-failover
- network/load-balancer-healthcheck-failure-patterns
linked_paths:
- contents/network/dns-split-horizon-behavior.md
- contents/network/dns-negative-caching-nxdomain-behavior.md
- contents/network/connection-reuse-vs-service-discovery-churn.md
- contents/network/happy-eyeballs-dual-stack-racing.md
- contents/network/anycast-routing-tradeoffs-edge-failover.md
- contents/network/load-balancer-healthcheck-failure-patterns.md
confusable_with:
- network/dns-negative-caching-nxdomain-behavior
- network/dns-split-horizon-behavior
- network/connection-reuse-vs-service-discovery-churn
- network/anycast-routing-tradeoffs-edge-failover
forbidden_neighbors: []
expected_queries:
- "DNS TTL 때문에 LB 전환 후 일부 사용자가 옛 IP를 계속 보는 이유는?"
- "authoritative는 바뀌었는데 recursive resolver와 browser cache가 stale인 장면을 어떻게 진단해?"
- "Blue-green DNS 전환 전에 TTL을 낮추는 운영 절차를 설명해줘"
- "TTL을 너무 짧게 하면 resolver 부하와 p99 latency가 왜 늘 수 있어?"
- "DNS propagation delay를 캐시 계층별로 나눠 확인하는 법을 알려줘"
contextual_chunk_prefix: |
  이 문서는 DNS TTL, browser/OS/recursive resolver cache, authoritative
  zone update, stale resolver, blue-green DNS, failover propagation delay를
  운영 장애 패턴으로 다루는 advanced DNS playbook이다.
---
# DNS TTL Cache Failure Patterns

> 한 줄 요약: DNS TTL은 "얼마나 빨리 바뀌는가"가 아니라, 여러 캐시 계층이 얼마나 오래 서로 다른 현실을 믿는가를 결정한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DNS Split-Horizon Behavior](./dns-split-horizon-behavior.md)
> - [DNS Negative Caching, NXDOMAIN Behavior](./dns-negative-caching-nxdomain-behavior.md)
> - [Connection Reuse vs Service Discovery Churn](./connection-reuse-vs-service-discovery-churn.md)
> - [Happy Eyeballs, Dual-Stack Racing](./happy-eyeballs-dual-stack-racing.md)
> - [Anycast Routing Trade-offs, Edge Failover](./anycast-routing-tradeoffs-edge-failover.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)

retrieval-anchor-keywords: DNS TTL, cache propagation, stale resolver, authoritative DNS, recursive resolver, blue-green DNS, cache invalidation, propagation delay, DNS failure pattern

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

DNS TTL은 응답이 얼마 동안 캐시될지 정한다.  
중요한 건 TTL 하나가 아니라 **캐시가 여러 층에 존재한다는 점**이다.

- 브라우저
- OS resolver
- 로컬 캐시 데몬
- recursive resolver
- authoritative zone view

이 층이 서로 다른 시간에 갱신되면, 일부 사용자는 오래된 IP를 계속 본다.

### Retrieval Anchors

- `DNS TTL`
- `cache propagation`
- `stale resolver`
- `authoritative DNS`
- `recursive resolver`
- `blue-green DNS`
- `cache invalidation`
- `propagation delay`
- `DNS failure pattern`

## 깊이 들어가기

### 1. TTL이 해결하는 것과 못하는 것

TTL은 캐시 효율과 변경 전파 속도를 조절한다.

- 길면 조회 부하를 줄인다
- 짧으면 전환이 빨라진다

하지만 TTL만으로 모든 전파 문제를 해결할 수는 없다.

- recursive resolver가 오래된 응답을 들고 있을 수 있다
- 클라이언트가 자체 캐시를 유지할 수 있다
- split-horizon이면 뷰 자체가 다를 수 있다

### 2. stale cache가 실제로 만드는 장애

- LB를 바꿨는데 일부 유저만 계속 옛 IP로 간다
- blue-green 전환이 느리게 보인다
- failover가 절반만 된 것처럼 보인다
- 재시도가 잘못된 노드로 몰린다

### 3. 캐시 층을 나누어 봐야 하는 이유

장애 분석은 "DNS가 안 바뀐다"가 아니라:

- 어느 resolver가 오래됐는가
- authoritative는 이미 바뀌었는가
- 브라우저/OS 캐시는 어떻게 남아 있는가

를 추적하는 일이다.

### 4. TTL이 너무 짧을 때의 함정

- resolver 부하가 늘어난다
- 외부 의존성이 많아진다
- p99가 DNS에 끌려간다

짧게 하는 게 무조건 좋은 건 아니다.

### 5. TTL을 낮추는 운영 절차

안전한 절차는 보통 다음과 같다.

1. 전환 전에 TTL을 충분히 낮춘다
2. 구/신 경로를 함께 운영한다
3. 전환 후 관찰한다
4. 안정화되면 TTL을 다시 올린다

이 부분은 [Anycast Routing Trade-offs, Edge Failover](./anycast-routing-tradeoffs-edge-failover.md)와도 맞물린다.

## 실전 시나리오

### 시나리오 1: LB 교체 후 일부 지역만 옛 서버를 본다

recursive resolver나 지역 캐시가 남아 있을 수 있다.

### 시나리오 2: 장애 복구 후에도 유입이 안 돌아온다

authoritative 변경은 되었지만 cache invalidation이 덜 끝났을 수 있다.

### 시나리오 3: TTL을 줄였더니 더 느려졌다

DNS 조회량이 늘어나 resolver와 네트워크 비용이 올라갔을 수 있다.

### 시나리오 4: 서비스 디스커버리와 엇갈린다

connection reuse나 discovery churn과 TTL이 서로 다른 시간축으로 움직일 수 있다.

## 코드로 보기

### 캐시 경로 확인

```bash
dig example.com
dig @8.8.8.8 example.com
dig @1.1.1.1 example.com
```

### TTL 확인

```bash
dig example.com +noall +answer
```

### 운영 감각

```text
low TTL:
- faster propagation
- more query load

high TTL:
- fewer queries
- slower change visibility
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 짧은 TTL | 전환이 빠르다 | 조회 부하가 늘어난다 | 장애 전환 민감 |
| 긴 TTL | 캐시 효율이 좋다 | stale risk가 커진다 | 주소 안정적 |
| 단계적 TTL 감소 | 전환이 안전하다 | 운영 준비가 필요하다 | 계획된 migration |

핵심은 TTL을 낮추는 것 자체가 아니라 **캐시 계층 전체의 시간차를 관리하는 것**이다.

## 꼬리질문

> Q: TTL을 낮추면 왜 좋은가요?
> 핵심: 주소 변경이 더 빨리 전파되기 때문이다.

> Q: TTL을 무조건 낮추면 안 되는 이유는?
> 핵심: resolver 부하와 외부 의존성이 늘어날 수 있기 때문이다.

> Q: DNS가 바뀌었는데 왜 바로 안 바뀌나요?
> 핵심: 여러 캐시 계층이 서로 다른 시간에 갱신되기 때문이다.

## 한 줄 정리

DNS TTL은 전파 속도와 조회 비용을 함께 바꾸며, 여러 캐시 계층이 동시에 서로 다른 현실을 믿는 시간이 길어질수록 장애가 길어진다.
