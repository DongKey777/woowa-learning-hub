---
schema_version: 3
title: "NAT Keepalive Tuning, Connection Lifetime"
concept_id: network/nat-keepalive-tuning-connection-lifetime
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- nat-keepalive
- conntrack-timeout
- connection-lifetime
aliases:
- NAT keepalive tuning
- conntrack timeout
- stale NAT mapping
- connection lifetime
- NAT rebinding
- heartbeat interval
- TCP keepalive tuning
symptoms:
- 한동안 조용한 뒤 NAT 뒤 첫 요청만 실패한다
- keepalive를 켰는데도 NAT나 LB timeout보다 주기가 길어 연결이 끊긴다
- probe를 너무 자주 보내 NAT gateway와 서버 비용이 늘어난다
- 외부 API나 모바일 클라이언트에서 stale mapping 재사용이 반복된다
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- network/nat-conntrack-ephemeral-port-exhaustion
- network/tcp-keepalive-vs-app-heartbeat
next_docs:
- network/idle-timeout-mismatch-lb-proxy-app
- network/connection-keepalive-loadbalancing-circuit-breaker
- network/timeout-retry-backoff-practical
- network/http-keepalive-timeout-mismatch-deeper-cases
linked_paths:
- contents/network/nat-conntrack-ephemeral-port-exhaustion.md
- contents/network/tcp-keepalive-vs-app-heartbeat.md
- contents/network/idle-timeout-mismatch-lb-proxy-app.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/network/timeout-retry-backoff-practical.md
confusable_with:
- network/nat-conntrack-ephemeral-port-exhaustion
- network/tcp-keepalive-vs-app-heartbeat
- network/idle-timeout-mismatch-lb-proxy-app
- network/http-keepalive-timeout-mismatch-deeper-cases
forbidden_neighbors: []
expected_queries:
- "NAT keepalive interval을 conntrack timeout보다 어떻게 짧게 잡아야 해?"
- "stale NAT mapping 때문에 idle 뒤 첫 요청이 실패하는 패턴을 설명해줘"
- "TCP keepalive와 app heartbeat 중 NAT mapping 유지에는 무엇을 봐야 해?"
- "connection lifetime을 제한하면 NAT rebinding 문제를 어떻게 줄여?"
- "probe를 너무 자주 보내지 않으면서 NAT timeout을 피하는 기준은?"
contextual_chunk_prefix: |
  이 문서는 NAT/conntrack timeout, stale NAT mapping, keepalive interval,
  app heartbeat, TCP keepalive, connection lifetime tuning을 다루는
  advanced playbook이다.
---
# NAT Keepalive Tuning, Connection Lifetime

> 한 줄 요약: NAT는 오래 조용한 연결을 먼저 잊어버리므로, keepalive와 connection lifetime을 NAT/conntrack/idle timeout에 맞춰 조정해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [NAT, Conntrack, Ephemeral Port Exhaustion](./nat-conntrack-ephemeral-port-exhaustion.md)
> - [TCP Keepalive vs App Heartbeat](./tcp-keepalive-vs-app-heartbeat.md)
> - [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)

retrieval-anchor-keywords: NAT keepalive, conntrack timeout, connection lifetime, idle timeout, NAT rebinding, stale mapping, heartbeat interval, TCP keepalive tuning

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

NAT 뒤의 연결은 "그냥 열려 있다"가 아니다.  
중간 장비는 일정 시간 트래픽이 없으면 매핑을 잊을 수 있다.

- NAT mapping이 사라질 수 있다
- conntrack entry가 expire될 수 있다
- keepalive가 너무 느리면 다음 패킷이 이미 죽은 경로로 간다

### Retrieval Anchors

- `NAT keepalive`
- `conntrack timeout`
- `connection lifetime`
- `idle timeout`
- `NAT rebinding`
- `stale mapping`
- `heartbeat interval`
- `TCP keepalive tuning`

## 깊이 들어가기

### 1. 왜 NAT가 연결을 잊나

NAT는 상태를 유지해야 한다.

- 내부 source IP/port
- 외부 destination
- 바뀐 public mapping

하지만 이 상태는 무한정 유지되지 않는다.

- 자원을 아끼기 위해 timeout이 있다
- idle connection이 길면 매핑이 사라진다
- 같은 포트를 다른 흐름에 재할당할 수 있다

### 2. keepalive를 왜 맞춰야 하나

keepalive가 NAT timeout보다 늦으면:

- 연결은 살아 있다고 보이는데
- NAT는 이미 매핑을 잊는다
- 다음 실제 request가 실패한다

반대로 너무 짧으면:

- 불필요한 probe가 늘어난다
- 네트워크와 서버가 쓸데없이 바빠진다

### 3. 어떤 값들을 같이 봐야 하나

보통 함께 보는 것은 다음이다.

- TCP keepalive 간격
- app heartbeat 간격
- LB idle timeout
- NAT/conntrack timeout
- client connection pool lifetime

핵심은 가장 느린 감지보다 **가장 먼저 죽는 경로를 기준으로 살리는 것**이다.

### 4. connection lifetime을 관리하는 이유

영원히 재사용하는 커넥션은 없다.

- 너무 오래 쓰면 stale mapping을 만난다
- 너무 빨리 바꾸면 handshake 비용이 늘어난다
- 적당한 lifetime이 운영 안정성과 효율을 같이 챙긴다

### 5. 언제 문제가 더 커지나

- 모바일 클라이언트
- 외부 API 호출이 많은 서비스
- NAT gateway 뒤의 많은 워커
- 장시간 idle 후 burst 트래픽

## 실전 시나리오

### 시나리오 1: 한동안 조용하다가 첫 요청만 실패한다

stale NAT mapping의 전형적인 패턴이다.

### 시나리오 2: keepalive를 켰는데도 연결이 자주 끊긴다

keepalive 주기가 NAT/LB timeout보다 길 수 있다.

### 시나리오 3: probe를 너무 자주 보내서 네트워크가 바빠진다

지나치게 짧은 keepalive는 운영 비용만 늘린다.

## 코드로 보기

### 커널 관찰

```bash
sysctl net.ipv4.tcp_keepalive_time
sysctl net.ipv4.tcp_keepalive_intvl
sysctl net.ipv4.tcp_keepalive_probes
```

### NAT/conntrack 확인

```bash
ss -tan state established
sudo conntrack -S
```

### 운영 감각

```text
keepalive interval < NAT timeout
heartbeat interval < LB idle timeout
connection lifetime < stale mapping window
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 짧은 keepalive | stale mapping을 빨리 잡는다 | probe 비용이 든다 | NAT가 엄격할 때 |
| 긴 keepalive | 네트워크 비용이 낮다 | 연결이 조용히 죽을 수 있다 | 내부망 |
| lifetime 제한 | stale connection을 줄인다 | 재연결 비용이 늘어난다 | 외부 API/모바일 |

핵심은 NAT가 잊기 전에 **우리가 먼저 생존 신호를 보내는 것**이다.

## 꼬리질문

> Q: NAT keepalive를 왜 튜닝하나요?
> 핵심: NAT/conntrack이 idle 연결을 먼저 잊어버릴 수 있기 때문이다.

> Q: 너무 짧게 두면 문제는 무엇인가요?
> 핵심: 불필요한 probe와 네트워크 비용이 늘어난다.

> Q: connection lifetime을 왜 제한하나요?
> 핵심: 오래된 mapping과 stale connection을 줄이기 위해서다.

## 한 줄 정리

NAT 뒤의 연결은 시간이 지나면 조용히 죽을 수 있으므로, keepalive와 lifetime을 NAT/conntrack timeout보다 앞서도록 맞춰야 한다.
