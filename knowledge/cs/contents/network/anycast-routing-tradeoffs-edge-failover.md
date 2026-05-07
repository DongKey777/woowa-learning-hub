---
schema_version: 3
title: Anycast Routing Trade-offs, Edge Failover
concept_id: network/anycast-routing-tradeoffs-edge-failover
canonical: false
category: network
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- anycast-routing
- edge-failover
- bgp-convergence
aliases:
- Anycast routing
- edge failover
- BGP route convergence
- nearest edge
- path asymmetry
- global load balancing
- failover blast radius
symptoms:
- anycast가 가장 가까운 edge를 고르므로 항상 가장 안정적인 path를 준다고 오해한다
- PoP 장애 후 일부 사용자만 계속 옛 경로를 보는 현상을 BGP convergence, DNS cache, route stability로 나눠 보지 않는다
- long-lived connection과 session 이동성이 필요한 서비스를 anycast failover만으로 해결하려 한다
intents:
- definition
- troubleshooting
prerequisites:
- network/dns-cdn-websocket-http2-http3
- network/load-balancer-healthcheck-failure-patterns
next_docs:
- network/dns-ttl-cache-failure-patterns
- network/quic-connection-migration-path-change
- network/http3-quic-practical-tradeoffs
linked_paths:
- contents/network/dns-cdn-websocket-http2-http3.md
- contents/network/dns-ttl-cache-failure-patterns.md
- contents/network/load-balancer-healthcheck-failure-patterns.md
- contents/network/quic-connection-migration-path-change.md
- contents/network/http3-quic-practical-tradeoffs.md
confusable_with:
- network/dns-ttl-cache-failure-patterns
- network/load-balancer-healthcheck-failure-patterns
- network/quic-connection-migration-path-change
- network/http3-quic-practical-tradeoffs
forbidden_neighbors: []
expected_queries:
- Anycast는 같은 IP로 가까운 edge에 붙게 하지만 안정성을 항상 보장하지 않는 이유는?
- Edge failover 후 일부 사용자만 오래된 PoP 경로를 계속 보는 원인은?
- BGP route convergence와 path asymmetry가 anycast 운영에서 왜 중요해?
- Anycast와 QUIC connection migration은 edge path change 관점에서 어떻게 같이 봐?
- 한 지역만 느린 글로벌 서비스에서 anycast PoP congestion을 어떻게 의심해?
contextual_chunk_prefix: |
  이 문서는 Anycast routing을 같은 IP를 여러 PoP에서 광고해 가까운 edge로 보내는 전략으로
  설명하되, BGP convergence, path asymmetry, edge failover blast radius, long-lived connection
  추적성을 함께 보는 advanced primer다.
---
# Anycast Routing Trade-offs, Edge Failover

> 한 줄 요약: Anycast는 같은 IP로 가장 가까운 edge에 붙게 하지만, 경로의 "가까움"이 곧 "안정성"은 아니라는 점이 운영의 핵심이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DNS, CDN, HTTP/2, HTTP/3](./dns-cdn-websocket-http2-http3.md)
> - [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)
> - [QUIC Connection Migration, Path Change](./quic-connection-migration-path-change.md)
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)

retrieval-anchor-keywords: anycast, edge failover, BGP, route convergence, global load balancing, nearest edge, path asymmetry, PoP, failover blast radius

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

Anycast는 여러 위치에서 같은 IP를 광고하고, 네트워크가 가장 가까운 edge로 트래픽을 보낸다.

- 글로벌 서비스에 유리하다
- 사용자와 가까운 PoP로 붙기 쉽다
- 한 IP로 failover를 단순화할 수 있다

하지만 경로가 항상 의도대로 converged 되는 건 아니고, 지역별 path asymmetry나 장애 전파 특성을 이해해야 한다.

### Retrieval Anchors

- `anycast`
- `edge failover`
- `BGP`
- `route convergence`
- `global load balancing`
- `nearest edge`
- `path asymmetry`
- `PoP`
- `failover blast radius`

## 깊이 들어가기

### 1. why anycast is attractive

사용자는 가장 가까운 edge로 가는 느낌을 받는다.

- latency가 줄 수 있다
- 장애 시 다른 PoP로 자연스럽게 빠질 수 있다
- 주소 관리가 단순해 보인다

### 2. 왜 가까움이 항상 안정성은 아닌가

가까운 경로가 꼭 좋은 경로는 아니다.

- 특정 PoP가 과부하일 수 있다
- BGP convergence가 느릴 수 있다
- path asymmetry 때문에 왕복 품질이 다를 수 있다

즉 anycast는 "가장 가까운 곳"으로 가지만, **가장 좋은 곳**을 항상 보장하지 않는다.

### 3. 장애 전파가 왜 까다로운가

한 PoP가 나쁘다고 해서 즉시 전체가 바뀌지 않는다.

- 라우트 수렴이 지연될 수 있다
- 일부 사용자는 오래된 경로를 계속 본다
- health check와 실제 라우팅 수렴이 다를 수 있다

### 4. edge failover의 양면성

장점:

- 지역 장애를 흡수한다
- 사용자 가까운 edge에서 계속 서빙할 수 있다

단점:

- 경로가 자주 바뀌면 observability가 어려워진다
- 세션 기반 서비스는 connection churn이 늘 수 있다
- long-lived connection이 어디에 붙는지 추적하기 복잡해진다

### 5. QUIC과 왜 같이 언급되나

QUIC은 path migration에 강하고, anycast는 edge failover에 강하다.

- 둘 다 path change를 자주 다룬다
- 둘 다 edge와 mobility 문제를 운영한다

그래서 [QUIC Connection Migration, Path Change](./quic-connection-migration-path-change.md)와 함께 보면 좋다.

## 실전 시나리오

### 시나리오 1: 한 지역만 유독 느리다

그 지역 PoP의 route convergence나 edge congestion을 의심할 수 있다.

### 시나리오 2: failover 후 일부 사용자는 계속 옛 경로를 본다

BGP convergence와 DNS cache, client route stability가 함께 작동할 수 있다.

### 시나리오 3: edge는 바뀌었는데 세션은 유지되고 싶다

장시간 연결과 세션 이동성은 anycast와 QUIC migration의 교집합이다.

## 코드로 보기

### 경로 관찰

```bash
traceroute api.example.com
mtr api.example.com
dig api.example.com
```

### 관찰 포인트

```text
- 어느 PoP로 붙는가
- 경로가 지역마다 다른가
- 장애 후 convergence가 얼마나 걸리는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| anycast | 글로벌 failover가 단순하다 | 경로 가시성이 낮다 | edge-heavy 서비스 |
| unicast + regional LB | 추적이 쉽다 | 글로벌 확장성이 덜하다 | 지역 고정 서비스 |
| 혼합 구조 | 유연하다 | 운영 복잡도가 높다 | 대규모 글로벌 서비스 |

핵심은 가장 가까운 edge를 쓰는 것보다 **장애 시 수렴과 추적 가능성**이다.

## 꼬리질문

> Q: anycast의 장점은 무엇인가요?
> 핵심: 가장 가까운 edge로 보내기 쉽고 failover를 단순화할 수 있다.

> Q: anycast의 단점은 무엇인가요?
> 핵심: route convergence와 path asymmetry 때문에 안정성이 일관되지 않을 수 있다.

> Q: 왜 QUIC과 같이 보나요?
> 핵심: 둘 다 경로 변경과 이동성을 다루기 때문이다.

## 한 줄 정리

Anycast는 edge failover와 지연 최적화에 강하지만, 경로 수렴과 가시성 문제를 함께 감수해야 하는 라우팅 전략이다.
