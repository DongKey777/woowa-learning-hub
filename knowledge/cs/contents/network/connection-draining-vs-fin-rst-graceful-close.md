---
schema_version: 3
title: "Connection Draining vs FIN, RST, Graceful Close"
concept_id: network/connection-draining-vs-fin-rst-graceful-close
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- connection-draining
- fin-rst-graceful-close
- deployment-safe-shutdown
aliases:
- connection draining
- FIN RST graceful close
- deregistration delay
- half-close socket lifecycle
- close_notify shutdown
- deployment safe close
symptoms:
- 배포 중 reset이 생겼는데 readiness false와 draining window 없이 server shutdown만 본다
- FIN EOF 정상 종료와 RST 강제 종료를 모두 같은 connection closed로 처리한다
- TLS close_notify와 TCP FIN/RST, proxy close 변환을 구분하지 못한다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- network/fin-rst-half-close-eof-semantics
- network/lb-connection-draining-deployment-safe-close
next_docs:
- network/idle-timeout-mismatch-lb-proxy-app
- network/load-balancer-healthcheck-failure-patterns
- network/http2-rst-stream-goaway-streaming-failure-semantics
- network/connection-keepalive-loadbalancing-circuit-breaker
linked_paths:
- contents/network/lb-connection-draining-deployment-safe-close.md
- contents/network/fin-rst-half-close-eof-semantics.md
- contents/network/idle-timeout-mismatch-lb-proxy-app.md
- contents/network/load-balancer-healthcheck-failure-patterns.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/network/http2-rst-stream-goaway-streaming-failure-semantics.md
confusable_with:
- network/fin-rst-half-close-eof-semantics
- network/lb-connection-draining-deployment-safe-close
- network/idle-timeout-mismatch-lb-proxy-app
- network/http2-rst-stream-goaway-streaming-failure-semantics
- network/connection-keepalive-loadbalancing-circuit-breaker
forbidden_neighbors: []
expected_queries:
- "connection draining과 FIN RST graceful close는 각각 어떤 층의 개념이야?"
- "배포 중 reset을 줄이려면 readiness false와 deregistration delay를 어떻게 맞춰?"
- "FIN EOF 정상 종료와 RST 강제 종료를 tcpdump와 로그에서 어떻게 구분해?"
- "TLS close_notify와 TCP socket close는 왜 1:1로 안 보일 수 있어?"
- "keep-alive가 길 때 draining window와 pool lifetime을 어떻게 조정해?"
contextual_chunk_prefix: |
  이 문서는 connection draining, deregistration delay, graceful shutdown,
  FIN, RST, half-close, TLS close_notify를 배포 중 연결 종료와 reset
  최소화 관점으로 연결하는 advanced operations playbook이다.
---
# Connection Draining vs FIN, RST, Graceful Close

> 한 줄 요약: connection draining은 앱과 LB가 기존 연결을 마무리하게 해주는 운영 절차이고, FIN/RST는 그 절차가 실제 소켓에서 어떻게 보이는지다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [LB Connection Draining, Deployment Safe Close](./lb-connection-draining-deployment-safe-close.md)
> - [FIN, RST, Half-Close, EOF](./fin-rst-half-close-eof-semantics.md)
> - [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)

retrieval-anchor-keywords: connection draining, FIN, RST, graceful close, deregistration delay, half-close, close_notify, shutdown, socket lifecycle

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

connection draining은 새 연결은 다른 곳으로 보내고, 기존 연결은 끝까지 마무리하게 하는 것이다.

- FIN은 정상적인 종료 신호다
- RST는 강제 종료에 가깝다
- draining은 앱/LB가 FIN 쪽으로 유도하도록 만드는 운영 절차다

### Retrieval Anchors

- `connection draining`
- `FIN`
- `RST`
- `graceful close`
- `deregistration delay`
- `half-close`
- `close_notify`
- `shutdown`
- `socket lifecycle`

## 깊이 들어가기

### 1. draining과 FIN의 관계

draining이 잘 되면 기존 연결은 FIN 경로로 마무리된다.

- 새 요청은 더 이상 받지 않는다
- 이미 진행 중인 요청은 응답을 끝낸다
- 소켓은 정상적으로 종료된다

### 2. draining과 RST의 차이

RST는 보통 다음 상황에서 보인다.

- 서버가 강제 종료된다
- proxy가 세션을 버린다
- timeout이 너무 짧아 끊는다

draining이 없다면 shutdown 순간이 RST처럼 보일 수 있다.

### 3. half-close가 왜 관련되나

요청을 다 받은 뒤 응답만 보내는 프로토콜은 half-close 감각이 중요하다.

- 클라이언트는 더 보내지 않는다
- 서버는 아직 응답을 보낼 수 있다
- 종료 시점이 앞뒤로 다를 수 있다

### 4. TLS에서는 어떻게 보이나

TLS는 close_notify 같은 종료 신호가 관여할 수 있다.

- 평문 TCP와 소켓 종료가 1:1로 안 보일 수 있다
- proxy가 중간에서 종료를 변환할 수 있다
- 앱은 graceful close와 RST를 구분해야 한다

### 5. 운영 절차와 연결되는 지점

- readiness false
- 새 연결 차단
- 기존 연결 마무리
- 종료 후 reset 최소화

## 실전 시나리오

### 시나리오 1: 배포 중 reset이 생긴다

draining 없이 서버를 내렸을 가능성이 크다.

### 시나리오 2: client는 EOF를 보는데 server 로그는 정상이다

정상 종료 경로일 수 있다.

### 시나리오 3: keep-alive가 길어서 종료 타이밍이 늦다

draining window와 pool lifetime을 맞춰야 한다.

## 코드로 보기

### 상태 관찰

```bash
ss -tan state close-wait
ss -tan state time-wait
tcpdump -i eth0 'tcp[tcpflags] & (tcp-fin|tcp-rst) != 0'
```

### 종료 흐름 감각

```text
drain -> no new traffic
finish active requests
send FIN or close_notify
avoid RST unless force-close
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| graceful draining | 요청 손실이 적다 | 종료가 느릴 수 있다 | 일반 배포 |
| immediate close | 빠르다 | reset/EOF 혼선이 생긴다 | 비정상 종료 |
| long drain window | long-lived connection에 유리 | 자원 회수가 늦다 | streaming |

핵심은 운영 절차가 FIN/RST를 실제로 어떻게 만들지 이해하는 것이다.

## 꼬리질문

> Q: connection draining과 FIN의 관계는?
> 핵심: draining은 정상 FIN 종료로 유도하는 운영 절차다.

> Q: RST는 언제 보이나요?
> 핵심: 강제 종료, timeout, proxy discard에서 잘 보인다.

> Q: 왜 graceful close가 중요한가요?
> 핵심: 배포와 scale-in에서 불필요한 reset과 데이터 손실을 줄이기 위해서다.

## 한 줄 정리

connection draining은 종료를 부드럽게 만드는 운영 절차이고, FIN/RST는 그 결과가 소켓에서 어떻게 보이는지다.
