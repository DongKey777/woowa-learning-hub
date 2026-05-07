---
schema_version: 3
title: "TCP Fast Open Trade-offs"
concept_id: network/tcp-fast-open-tradeoffs
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- tcp-fast-open
- handshake-latency
- replay-risk
aliases:
- TCP Fast Open
- TFO
- data in SYN
- SYN data
- handshake RTT reduction
- TCP cookie
- replay risk
- middlebox compatibility
symptoms:
- TCP Fast Open을 단순 latency win으로만 보고 replay/compatibility 문제를 놓친다
- SYN data가 middlebox나 firewall에서 차단될 수 있음을 고려하지 않는다
- idempotent하지 않은 요청을 early data와 비슷하게 안전하다고 본다
intents:
- deep_dive
- comparison
- troubleshooting
prerequisites:
- network/syn-retransmission-handshake-timeout
- network/tcp-congestion-control
next_docs:
- network/tls-session-resumption-0rtt-replay-risk
- network/http3-quic-practical-tradeoffs
- network/packet-loss-jitter-reordering-diagnostics
- network/udp-fragmentation-quic-packetization
linked_paths:
- contents/network/tls-session-resumption-0rtt-replay-risk.md
- contents/network/syn-retransmission-handshake-timeout.md
- contents/network/tcp-congestion-control.md
- contents/network/http2-multiplexing-hol-blocking.md
- contents/network/timeout-types-connect-read-write.md
confusable_with:
- network/tls-session-resumption-0rtt-replay-risk
- network/syn-retransmission-handshake-timeout
- network/http3-quic-practical-tradeoffs
forbidden_neighbors: []
expected_queries:
- "TCP Fast Open은 data in SYN으로 어떤 latency를 줄여?"
- "TFO의 replay risk와 TLS 0-RTT replay risk는 어떻게 비슷하고 달라?"
- "TCP Fast Open이 middlebox 때문에 실패하거나 fallback될 수 있는 이유는?"
- "idempotent하지 않은 요청을 TFO early data로 보내면 왜 위험해?"
- "SYN handshake timeout과 TCP Fast Open trade-off를 같이 설명해줘"
contextual_chunk_prefix: |
  이 문서는 TCP Fast Open(TFO), data in SYN, TCP cookie,
  handshake RTT 절감, middlebox compatibility, replay risk trade-off를 다루는
  advanced playbook이다.
---
# TCP Fast Open Trade-offs

> 한 줄 요약: TCP Fast Open은 첫 데이터 전송을 앞당길 수 있지만, 재전송·호환성·보안 정책까지 같이 봐야 실제 이득이 난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TLS Session Resumption, 0-RTT, Replay Risk](./tls-session-resumption-0rtt-replay-risk.md)
> - [SYN Retransmission, Handshake Timeout Behavior](./syn-retransmission-handshake-timeout.md)
> - [TCP 혼잡 제어](./tcp-congestion-control.md)
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)

retrieval-anchor-keywords: TCP Fast Open, TFO, cookie, first data, 0-RTT, SYN data, handshake latency, replay risk, middlebox compatibility

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

TCP Fast Open(TFO)은 연결 수립 초기에 데이터를 더 빨리 보내는 최적화다.

- SYN에 데이터를 실어 보낼 수 있다
- 이전에 얻은 cookie를 재사용할 수 있다
- 첫 요청 지연을 줄일 수 있다

하지만 TFO는 모든 환경에서 안정적인 건 아니다.

- 중간 장비 호환성 문제가 있다
- 재전송과 재시도 흐름이 복잡해진다
- replay나 중복 요청 위험을 생각해야 한다

### Retrieval Anchors

- `TCP Fast Open`
- `TFO`
- `cookie`
- `first data`
- `0-RTT`
- `SYN data`
- `handshake latency`
- `replay risk`
- `middlebox compatibility`

## 깊이 들어가기

### 1. TFO가 줄이려는 것

TCP는 원래 연결을 맺고 나서 데이터를 보낸다.

- handshake RTT가 든다
- 짧은 요청일수록 비효율이 크다
- 모바일/고지연 환경에서 체감이 크다

TFO는 이 첫 RTT를 줄이려는 시도다.

### 2. cookie가 왜 필요한가

서버는 무작정 첫 SYN 데이터만 믿지 않는다.

- 이전에 정상 교신했던 클라이언트인지 확인해야 한다
- cookie로 재사용 가능 여부를 확인한다
- 재전송을 줄이면서도 악용을 막으려 한다

### 3. 왜 운영이 까다로운가

TFO는 네트워크 중간 장비를 많이 탄다.

- 일부 방화벽이나 proxy가 SYN data를 좋아하지 않는다
- 실패 시 fallback 경로가 필요하다
- 성능 이득이 환경마다 다르다

즉, TFO는 "켰다"보다 **실제 경로에서 유지되는가**가 더 중요하다.

### 4. TLS 0-RTT와 무엇이 다른가

둘 다 첫 데이터를 앞당긴다는 점은 비슷하다.

- TFO는 TCP 계층 최적화
- TLS 0-RTT는 암호화 계층 최적화

하지만 둘 다 **반복 전송과 replay 취급**을 조심해야 한다.

### 5. 어떤 요청에 맞나

좋은 후보:

- 짧은 idempotent 요청
- 재접속이 잦은 모바일 트래픽
- handshake 비용이 큰 환경

나쁜 후보:

- 상태 변경
- 재전송 시 부작용이 큰 요청
- 중간 장비가 불안정한 경로

## 실전 시나리오

### 시나리오 1: 연결은 빨라졌는데 간헐 실패가 생긴다

중간 장비가 TFO를 제대로 처리하지 못할 수 있다.

### 시나리오 2: 모바일에서는 좋아 보이는데 사내망에서는 이상하다

중간 NAT, proxy, firewall 차이로 호환성이 흔들릴 수 있다.

### 시나리오 3: 첫 요청만 빨라졌고 전체 시스템은 별 차이가 없다

TFO는 handshake 비용만 줄이므로, backend 처리 시간이 병목이면 전체 체감은 작다.

## 코드로 보기

### 커널 설정 감각

```bash
sysctl net.ipv4.tcp_fastopen
```

### 연결 관찰

```bash
ss -ti dst api.example.com
tcpdump -i eth0 host api.example.com and tcp
```

### 판단 포인트

```text
- 첫 RTT가 의미 있게 줄었는가
- 실패 시 fallback이 자연스러운가
- 중간 장비 호환성이 괜찮은가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| TFO 사용 | 첫 데이터 지연이 줄 수 있다 | 호환성과 실패 경로가 복잡하다 | 환경이 통제될 때 |
| TFO 미사용 | 단순하고 안전하다 | 첫 RTT를 그대로 쓴다 | 기본 운영 |
| 조건부 사용 | 효과와 안전성을 균형 잡는다 | 정책이 복잡하다 | 점진적 도입 |

핵심은 TFO를 성능 기능으로만 보지 말고 **경로 호환성 기능**으로 같이 보는 것이다.

## 꼬리질문

> Q: TCP Fast Open은 무엇을 줄이나요?
> 핵심: 첫 데이터 전송까지의 handshake 지연을 줄인다.

> Q: 왜 항상 쓰지 않나요?
> 핵심: 중간 장비 호환성과 replay/재전송 정책이 복잡해지기 때문이다.

> Q: TLS 0-RTT와 같은가요?
> 핵심: 아니다. 둘 다 빠른 시작을 돕지만 계층과 실패 특성이 다르다.

## 한 줄 정리

TCP Fast Open은 첫 RTT를 아끼는 강력한 최적화지만, 호환성과 재전송 의미를 함께 설계하지 않으면 운영에서 손해를 볼 수 있다.
