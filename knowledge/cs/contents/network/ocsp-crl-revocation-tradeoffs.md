---
schema_version: 3
title: "OCSP, CRL Revocation Trade-offs"
concept_id: network/ocsp-crl-revocation-tradeoffs
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- tls-revocation
- ocsp-crl
- certificate-validation
aliases:
- OCSP
- CRL
- certificate revocation
- OCSP stapling
- soft fail hard fail
- revocation latency
- trust store
- certificate status
symptoms:
- 인증서가 만료 전이면 항상 신뢰해도 된다고 생각한다
- OCSP 조회 지연이나 stapling 실패를 TLS handshake latency와 연결하지 못한다
- revocation 조회 실패 시 soft fail과 hard fail trade-off를 설계하지 않는다
- CRL 배치성, OCSP 실시간성, privacy/availability 균형을 구분하지 못한다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/tls-certificate-chain-ocsp-stapling-failure-modes
- network/certificate-rotation-sni-blast-radius
next_docs:
- network/tls-session-resumption-0rtt-replay-risk
- network/api-gateway-reverse-proxy-operational-points
- network/dns-over-https-operational-tradeoffs
- network/mtls-handshake-failure-diagnosis
linked_paths:
- contents/network/tls-certificate-chain-ocsp-stapling-failure-modes.md
- contents/network/tls-session-resumption-0rtt-replay-risk.md
- contents/network/certificate-rotation-sni-blast-radius.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/dns-over-https-operational-tradeoffs.md
confusable_with:
- network/tls-certificate-chain-ocsp-stapling-failure-modes
- network/certificate-rotation-sni-blast-radius
- network/mtls-handshake-failure-diagnosis
- network/tls-session-resumption-0rtt-replay-risk
forbidden_neighbors: []
expected_queries:
- "OCSP와 CRL certificate revocation trade-off를 설명해줘"
- "OCSP stapling 실패가 TLS handshake latency를 늘리는 이유는?"
- "revocation check 실패 때 soft fail과 hard fail을 어떻게 선택해?"
- "인증서가 만료 전이어도 폐기된 인증서를 믿지 않게 하는 방법은?"
- "CRL과 OCSP는 실시간성, privacy, availability 측면에서 어떻게 달라?"
contextual_chunk_prefix: |
  이 문서는 certificate revocation에서 OCSP, CRL, OCSP stapling,
  soft fail/hard fail, trust store, latency와 privacy/availability trade-off를
  다루는 advanced playbook이다.
---
# OCSP, CRL Revocation Trade-offs

> 한 줄 요약: 인증서 revocation은 OCSP의 실시간성, CRL의 배치성, 그리고 장애 시 fallback 행동을 함께 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TLS Certificate Chain, OCSP Stapling Failure Modes](./tls-certificate-chain-ocsp-stapling-failure-modes.md)
> - [TLS Session Resumption, 0-RTT, Replay Risk](./tls-session-resumption-0rtt-replay-risk.md)
> - [Certificate Rotation, SNI Blast Radius](./certificate-rotation-sni-blast-radius.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [DNS over HTTPS Operational Trade-offs](./dns-over-https-operational-tradeoffs.md)

retrieval-anchor-keywords: OCSP, CRL, revocation, stapling, certificate status, offline validation, soft fail, hard fail, trust store, privacy, latency

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

인증서 revocation은 "만료 전이라도 폐기된 인증서를 믿지 않게" 하는 절차다.

- `OCSP`: 인증서 상태를 실시간에 가깝게 확인한다
- `CRL`: 폐기된 인증서 목록을 내려받아 확인한다
- `stapling`: 서버가 OCSP 응답을 미리 붙여준다

### Retrieval Anchors

- `OCSP`
- `CRL`
- `revocation`
- `stapling`
- `certificate status`
- `offline validation`
- `soft fail`
- `hard fail`
- `trust store`
- `privacy`
- `latency`

## 깊이 들어가기

### 1. OCSP가 하는 일

클라이언트가 인증서를 검증할 때, 그 인증서가 아직 유효한지 추가로 확인할 수 있다.

- 실시간에 가깝다
- 응답이 늦으면 handshake latency가 늘 수 있다
- 서버가 stapling하면 부담이 줄어든다

### 2. CRL이 하는 일

CRL은 취소된 인증서 목록 전체를 내려받아 확인하는 방식이다.

- 배치적이다
- 응답 지연은 덜할 수 있다
- 목록이 커질수록 관리가 번거롭다

### 3. hard fail과 soft fail

revocation 조회 실패 시 어떻게 할 것인가가 중요하다.

- `hard fail`: 확인이 안 되면 실패시킨다
- `soft fail`: 확인이 안 돼도 일단 통과시킨다

보안과 가용성의 균형이 달라진다.

### 4. stapling이 있어도 끝이 아닌 이유

OCSP stapling은 유용하지만:

- stapled response가 만료될 수 있다
- cache refresh가 필요하다
- 일부 클라이언트는 여전히 추가 검증을 시도할 수 있다

### 5. 운영에서 중요한 질문

- 실패 시 끊을 것인가
- 응답 지연을 감수할 것인가
- 프라이버시와 가용성을 어떻게 균형 잡을 것인가

## 실전 시나리오

### 시나리오 1: handshake가 갑자기 느려졌다

OCSP 조회가 지연되거나 stapling이 실패했을 수 있다.

### 시나리오 2: 일부 환경에서만 인증서 검증이 실패한다

trust store나 CRL 갱신 정책 차이일 수 있다.

### 시나리오 3: 가끔 revocation 때문에 연결이 끊긴다

soft fail/hard fail 정책이 서로 다르거나, stapling cache가 오래됐을 수 있다.

## 코드로 보기

### 인증서 상태 확인

```bash
openssl s_client -connect api.example.com:443 -status
```

### CRL/인증서 확인

```bash
openssl x509 -in cert.pem -noout -text | grep -i -E 'crl|ocsp|authority'
```

### 관찰 포인트

```text
- revocation lookup latency
- stapling freshness
- hard fail policy
- trust store update cadence
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| OCSP 중심 | 상태가 비교적 최신이다 | 네트워크 의존과 지연이 있다 | 공개 서비스 |
| CRL 중심 | 오프라인 검증이 가능하다 | 목록 관리가 번거롭다 | 통제된 환경 |
| soft fail | 가용성이 좋다 | revoked cert를 지나칠 수 있다 | 사용자 체감 우선 |
| hard fail | 보안이 강하다 | 장애 시 연결 실패가 늘 수 있다 | 고보안 서비스 |

핵심은 revocation을 "보안 기능"으로만 보지 말고 **지연과 실패 정책**까지 같이 보는 것이다.

## 꼬리질문

> Q: OCSP와 CRL의 차이는 무엇인가요?
> 핵심: OCSP는 실시간 상태 확인, CRL은 목록 다운로드 방식이다.

> Q: soft fail과 hard fail은 어떻게 다른가요?
> 핵심: 조회 실패 시 통과시키느냐 끊느냐의 차이다.

> Q: stapling이 왜 중요한가요?
> 핵심: revocation 확인 지연과 프라이버시 비용을 줄여주기 때문이다.

## 한 줄 정리

OCSP와 CRL은 둘 다 revocation을 다루지만, 실시간성·가용성·프라이버시의 균형이 달라 운영 정책까지 함께 정해야 한다.
