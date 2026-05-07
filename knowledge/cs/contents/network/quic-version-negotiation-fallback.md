---
schema_version: 3
title: "QUIC Version Negotiation, Fallback Behavior"
concept_id: network/quic-version-negotiation-fallback
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- quic
- http3-fallback
- version-negotiation
aliases:
- QUIC version negotiation
- HTTP/3 fallback
- version negotiation packet
- UDP blocked
- browser fallback
- Alt-Svc fallback
- QUIC compatibility
symptoms:
- HTTP/3가 안 붙으면 서비스 전체가 실패해야 한다고 생각한다
- QUIC version mismatch, UDP block, Alt-Svc stale cache, path validation 실패를 모두 같은 fallback으로 뭉갠다
- fallback이 조용히 일어나서 앱에는 느림으로만 보이는 점을 놓친다
- H3 attempted ratio와 fallback ratio를 따로 관측하지 않는다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/http3-quic-practical-tradeoffs
- network/http2-http3-downgrade-attribution-alt-svc-udp-block
next_docs:
- network/quic-connection-migration-path-change
- network/udp-fragmentation-quic-packetization
- network/happy-eyeballs-dual-stack-racing
- network/packet-loss-jitter-reordering-diagnostics
linked_paths:
- contents/network/http3-quic-practical-tradeoffs.md
- contents/network/quic-connection-migration-path-change.md
- contents/network/udp-fragmentation-quic-packetization.md
- contents/network/happy-eyeballs-dual-stack-racing.md
- contents/network/packet-loss-jitter-reordering-diagnostics.md
- contents/network/http2-http3-downgrade-attribution-alt-svc-udp-block.md
confusable_with:
- network/http2-http3-downgrade-attribution-alt-svc-udp-block
- network/h3-fallback-trace-bridge
- network/udp-fragmentation-quic-packetization
- network/http3-quic-practical-tradeoffs
forbidden_neighbors: []
expected_queries:
- "QUIC version negotiation 실패와 HTTP/3 fallback을 어떻게 봐야 해?"
- "특정 네트워크에서만 H3가 안 붙으면 UDP block과 version mismatch를 어떻게 구분해?"
- "Alt-Svc cache와 실제 QUIC 지원 버전이 안 맞으면 어떤 fallback이 생겨?"
- "HTTP/3 attempted ratio와 fallback ratio를 왜 따로 봐야 해?"
- "QUIC이 안 될 때 HTTP/2로 graceful fallback해야 하는 이유는?"
contextual_chunk_prefix: |
  이 문서는 QUIC version negotiation, version negotiation packet,
  HTTP/3 fallback to HTTP/2, UDP block, Alt-Svc cache mismatch와 관측 지표를
  다루는 advanced playbook이다.
---
# QUIC Version Negotiation, Fallback Behavior

> 한 줄 요약: QUIC은 버전 협상이 실패하면 fallback이 필요하고, 이때 HTTP/2나 다른 경로로 자연스럽게 돌아가는 설계가 중요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)
> - [QUIC Connection Migration, Path Change](./quic-connection-migration-path-change.md)
> - [UDP Fragmentation, QUIC Packetization](./udp-fragmentation-quic-packetization.md)
> - [Happy Eyeballs, Dual-Stack Racing](./happy-eyeballs-dual-stack-racing.md)
> - [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)
> - [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)

retrieval-anchor-keywords: QUIC version negotiation, fallback, HTTP/3 fallback, transport upgrade, UDP blocked, version negotiation packet, compatibility, browser fallback, alt-svc

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

QUIC version negotiation은 클라이언트와 서버가 어떤 QUIC 버전을 쓸지 맞추는 과정이다.

- 서로 버전이 다르면 협상이 필요하다
- 실패하면 fallback 경로가 필요하다
- HTTP/3를 항상 쓴다는 가정은 위험하다

### Retrieval Anchors

- `QUIC version negotiation`
- `fallback`
- `HTTP/3 fallback`
- `transport upgrade`
- `UDP blocked`
- `version negotiation packet`
- `compatibility`
- `browser fallback`
- `alt-svc`

## 깊이 들어가기

### 1. 왜 version negotiation이 필요한가

QUIC은 비교적 새 프로토콜이라 버전이 진화할 수 있다.

- 클라이언트와 서버가 같은 버전을 쓰지 않을 수 있다
- 구현체마다 지원 범위가 다를 수 있다
- middlebox나 방화벽이 특정 패턴을 막을 수 있다

### 2. fallback이 왜 중요하나

HTTP/3가 안 된다고 서비스 전체가 죽으면 안 된다.

- HTTP/2로 자연스럽게 내려간다
- 사용자는 느려질 수 있지만 연결은 이어진다
- 점진 전환이 가능해진다

### 3. 어떤 실패가 흔한가

- UDP 차단
- QUIC 버전 불일치
- alt-svc 캐시와 실제 지원 버전 불일치
- path validation 실패

### 4. 왜 관측이 어려운가

fallback은 대부분 조용히 일어난다.

- 브라우저는 다른 프로토콜로 넘어간다
- 앱은 그냥 느린 것처럼 보인다
- 운영자는 fallback 빈도를 따로 봐야 한다

### 5. 운영에서 봐야 할 것

- HTTP/3 시도 비율
- fallback 비율
- UDP 차단 구간
- 버전 협상 실패 패턴

## 실전 시나리오

### 시나리오 1: 어떤 네트워크에서만 HTTP/3가 안 붙는다

UDP 차단 또는 version negotiation 실패일 수 있다.

### 시나리오 2: 브라우저는 느려졌는데 장애는 아니다

fallback으로 HTTP/2를 쓰고 있을 수 있다.

### 시나리오 3: 새 버전 배포 후 일부 클라이언트만 깨진다

alt-svc cache나 지원 버전 불일치를 의심한다.

## 코드로 보기

### 확인 감각

```bash
curl --http3 -I https://example.com
curl --http2 -I https://example.com
```

### 관찰 포인트

```text
- HTTP/3 attempted?
- fallback to HTTP/2?
- UDP path blocked?
- version negotiation failure?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| HTTP/3 전용 | 단순할 수 있다 | fallback이 없으면 취약하다 | 통제된 환경 |
| graceful fallback | 호환성이 좋다 | 관측이 복잡하다 | 일반 브라우저 트래픽 |
| version pinning | 예측 가능하다 | 미래 호환성이 떨어진다 | 실험 환경 |

핵심은 QUIC이 안 될 때 **사용자 경로가 자연스럽게 내려가야** 한다는 것이다.

## 꼬리질문

> Q: QUIC version negotiation은 왜 필요한가요?
> 핵심: 클라이언트와 서버의 지원 버전이 다를 수 있기 때문이다.

> Q: fallback은 왜 중요하나요?
> 핵심: HTTP/3가 안 돼도 서비스가 계속 동작해야 하기 때문이다.

> Q: 관측은 어떻게 하나요?
> 핵심: HTTP/3 시도와 fallback 비율을 따로 본다.

## 한 줄 정리

QUIC version negotiation은 HTTP/3 호환성의 마지막 관문이며, 실패 시 HTTP/2로 자연스럽게 fallback되는 경로를 운영해야 한다.
