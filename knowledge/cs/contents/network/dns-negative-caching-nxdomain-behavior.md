---
schema_version: 3
title: "DNS Negative Caching, NXDOMAIN Behavior"
concept_id: network/dns-negative-caching-nxdomain-behavior
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- dns-negative-caching
- nxdomain-servfail
- resolver-cache-propagation
aliases:
- DNS negative caching
- NXDOMAIN behavior
- stale negative response
- resolver cache TTL
- SERVFAIL vs NXDOMAIN
- nonexistent name cache
symptoms:
- 새 DNS 레코드를 만들었는데 일부 resolver가 NXDOMAIN을 계속 반환한다
- NXDOMAIN과 SERVFAIL을 모두 없는 이름으로 읽어 resolver/upstream/DNSSEC 실패를 놓친다
- 삭제 후 복구 시 negative TTL과 SOA 기반 부정 응답 cache를 고려하지 않는다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/dns-ttl-cache-failure-patterns
- network/dns-basics
next_docs:
- network/dns-split-horizon-behavior
- network/connection-reuse-vs-service-discovery-churn
- network/load-balancer-healthcheck-failure-patterns
linked_paths:
- contents/network/dns-ttl-cache-failure-patterns.md
- contents/network/dns-cdn-websocket-http2-http3.md
- contents/network/dns-over-https-operational-tradeoffs.md
- contents/network/load-balancer-healthcheck-failure-patterns.md
- contents/network/connection-reuse-vs-service-discovery-churn.md
confusable_with:
- network/dns-ttl-cache-failure-patterns
- network/dns-split-horizon-behavior
- network/dns-over-https-operational-tradeoffs
- network/connection-reuse-vs-service-discovery-churn
forbidden_neighbors: []
expected_queries:
- "DNS negative caching 때문에 새 레코드를 만들었는데도 NXDOMAIN이 계속 보이는 이유는?"
- "NXDOMAIN과 SERVFAIL은 DNS 장애에서 어떻게 다르게 읽어야 해?"
- "SOA와 negative TTL이 nonexistent name cache에 어떤 영향을 줘?"
- "DNS 레코드 삭제 후 복구할 때 stale negative response를 어떻게 고려해?"
- "서비스 디스커버리 이름 변경 직후 일부 resolver만 안 붙는 현상을 설명해줘"
contextual_chunk_prefix: |
  이 문서는 DNS negative caching, NXDOMAIN, SERVFAIL, SOA negative TTL,
  recursive resolver cache, stale negative response가 새 레코드 론칭/삭제/복구
  중 보이는 운영 장애를 설명하는 advanced DNS playbook이다.
---
# DNS Negative Caching, NXDOMAIN Behavior

> 한 줄 요약: DNS negative caching은 없는 이름도 잠깐 캐시하기 때문에, 레코드가 늦게 생기거나 지워질 때 NXDOMAIN이 생각보다 오래 보일 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)
> - [DNS, CDN, HTTP/2, HTTP/3](./dns-cdn-websocket-http2-http3.md)
> - [DNS over HTTPS Operational Trade-offs](./dns-over-https-operational-tradeoffs.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)
> - [Connection Reuse vs Service Discovery Churn](./connection-reuse-vs-service-discovery-churn.md)

retrieval-anchor-keywords: negative caching, NXDOMAIN, SERVFAIL, SOA, TTL, resolver cache, DNS propagation, nonexistent name, stale negative response

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

DNS는 "존재하는 이름"만 캐시하는 게 아니다.  
**없다는 응답도 캐시**한다.

- NXDOMAIN: 이름이 없다
- SERVFAIL: 조회가 실패했다
- negative caching: 이런 부정 응답을 일정 시간 저장한다

### Retrieval Anchors

- `negative caching`
- `NXDOMAIN`
- `SERVFAIL`
- `SOA`
- `TTL`
- `resolver cache`
- `DNS propagation`
- `nonexistent name`
- `stale negative response`

## 깊이 들어가기

### 1. 왜 없는 이름을 캐시하나

같은 없는 이름을 반복 조회하면 resolver 부하만 늘어난다.

- 잘못된 도메인을 계속 치는 클라이언트를 줄인다
- 실패 응답도 TTL 동안 재사용할 수 있다
- authoritative 서버 부하를 낮춘다

### 2. 왜 운영에서 문제인가

레코드를 새로 만들었는데도 NXDOMAIN이 남을 수 있다.

- 이전 negative cache가 살아 있다
- 일부 resolver만 오래된 응답을 갖고 있다
- 사용자는 "아직 안 생겼다"고 느낀다

### 3. SOA가 왜 관련되나

negative caching은 보통 zone의 SOA 정보를 참고한다.

- negative response TTL이 어디서 왔는지 중요하다
- zone 정책에 따라 오래 남을 수 있다
- 레코드 생성 직후 전파가 예상보다 늦게 보일 수 있다

### 4. SERVFAIL과 왜 구분해야 하나

NXDOMAIN은 "없다"이고, SERVFAIL은 "실패했다"다.

- NXDOMAIN은 negative cache로 남을 수 있다
- SERVFAIL은 resolver, upstream, DNSSEC 문제일 수 있다

구분하지 않으면 장애 원인을 잘못 찾는다.

### 5. 언제 특히 아프나

- 새 서브도메인 론칭
- DNS 기반 blue-green 전환
- 서비스 디스커버리 이름 변경
- 잘못된 삭제 후 복구

## 실전 시나리오

### 시나리오 1: 레코드를 만들었는데 일부 지역에서만 안 보인다

negative cache가 아직 남아 있을 수 있다.

### 시나리오 2: 삭제한 이름이 계속 살아 있는 것처럼 보인다

resolver마다 cache 상태가 달라서 오래된 응답이 남을 수 있다.

### 시나리오 3: 새 서비스가 갑자기 안 붙는다

서비스 디스커버리 churn과 negative caching이 같이 문제일 수 있다.

## 코드로 보기

### 조회 확인

```bash
dig nonexistent.example.com
dig example.com SOA
```

### 캐시/전파 감각

```text
NXDOMAIN cached
negative TTL not expired
resolver still remembers nonexistence
```

### 운영 포인트

```text
- 새 도메인 론칭 전에 TTL 확인
- 삭제 후 복구 시 negative cache 고려
- authoritative와 recursive resolver를 분리해서 본다
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| negative caching 활성 | 부하가 줄어든다 | 새 레코드 전파가 늦어 보일 수 있다 | 기본 DNS |
| negative TTL 짧게 | 변화가 빨리 반영된다 | 반복 실패 조회가 늘 수 있다 | 자주 바뀌는 이름 |
| 검증된 이름만 변경 | 안정적이다 | 운영 유연성이 줄어든다 | 중요한 서비스 |

핵심은 "없는 이름"도 캐시된다는 사실을 운영 절차에 반영하는 것이다.

## 꼬리질문

> Q: NXDOMAIN과 SERVFAIL은 무엇이 다른가요?
> 핵심: NXDOMAIN은 이름이 없다는 뜻이고, SERVFAIL은 조회 자체가 실패했다는 뜻이다.

> Q: negative caching이 왜 필요하나요?
> 핵심: 반복 실패 조회를 줄여 resolver 부하를 낮추기 위해서다.

> Q: 새 도메인이 바로 안 보이는 이유는?
> 핵심: recursive resolver의 negative cache나 TTL이 남아 있을 수 있다.

## 한 줄 정리

DNS negative caching은 없는 이름도 잠깐 저장하므로, NXDOMAIN이 오래 남아 보이면 positive cache가 아니라 부정 캐시부터 의심해야 한다.
