---
schema_version: 3
title: "SNI, Routing Mismatch, Hostname Failure"
concept_id: network/sni-routing-mismatch-hostname-failure
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- sni-routing
- tls-hostname
- ingress-mismatch
aliases:
- SNI routing mismatch
- hostname routing
- virtual host
- certificate mismatch
- Host header mismatch
- TLS termination routing
- multi-tenant ingress
symptoms:
- 같은 IP/LB인데 특정 hostname만 certificate mismatch나 default backend로 빠진다
- SNI, Host header, path routing을 같은 계층의 신호로 본다
- health check는 통과하지만 실제 고객 hostname만 실패하는 이유를 놓친다
- 내부 클라이언트가 SNI를 안 보내 브라우저와 다른 결과를 본다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/tls-loadbalancing-proxy
- network/api-gateway-reverse-proxy-operational-points
next_docs:
- network/tls-certificate-chain-ocsp-stapling-failure-modes
- network/alpn-negotiation-failure-routing-mismatch
- network/load-balancer-healthcheck-failure-patterns
- network/http2-http3-connection-reuse-coalescing
linked_paths:
- contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md
- contents/network/tls-certificate-chain-ocsp-stapling-failure-modes.md
- contents/network/alpn-negotiation-failure-routing-mismatch.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/load-balancer-healthcheck-failure-patterns.md
confusable_with:
- network/alpn-negotiation-failure-routing-mismatch
- network/tls-certificate-chain-ocsp-stapling-failure-modes
- network/http2-http3-connection-reuse-coalescing
- network/proxy-header-normalization-chain-trust-boundary
forbidden_neighbors: []
expected_queries:
- "SNI routing mismatch 때문에 같은 IP에서 다른 서비스처럼 보이는 이유는?"
- "SNI와 Host header와 path routing은 각각 어느 단계 신호야?"
- "health check는 통과하는데 특정 hostname만 certificate mismatch가 나는 원인은?"
- "브라우저는 되는데 내부 클라이언트만 TLS/SNI 실패하는 패턴을 설명해줘"
- "multi-tenant ingress에서 SNI hostname backend 매칭을 어떻게 디버깅해?"
contextual_chunk_prefix: |
  이 문서는 SNI Server Name Indication, TLS certificate selection,
  Host header routing, virtual host, multi-tenant ingress의 hostname routing
  mismatch를 다루는 advanced playbook이다.
---
# SNI, Routing Mismatch, Hostname Failure

> 한 줄 요약: SNI는 TLS 단계에서 어떤 인증서와 라우팅을 쓸지 정하는 신호라서, hostname과 backend 매칭이 어긋나면 같은 IP에서도 전혀 다른 서비스처럼 보일 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Forwarded, X-Forwarded-For, X-Real-IP와 Trust Boundary](./forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
> - [TLS Certificate Chain, OCSP Stapling Failure Modes](./tls-certificate-chain-ocsp-stapling-failure-modes.md)
> - [ALPN Negotiation Failure, Routing Mismatch](./alpn-negotiation-failure-routing-mismatch.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)

retrieval-anchor-keywords: SNI, hostname routing, virtual host, certificate mismatch, host header, TLS termination, reverse proxy routing, multi-tenant ingress

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

SNI(Server Name Indication)는 TLS handshake에서 클라이언트가 "내가 접속하려는 호스트 이름"을 알려주는 신호다.

- 같은 IP에 여러 인증서를 둘 수 있다
- TLS 종료 지점이 호스트별로 분기할 수 있다
- 잘못된 SNI는 인증서 mismatch와 라우팅 mismatch를 함께 만든다

### Retrieval Anchors

- `SNI`
- `hostname routing`
- `virtual host`
- `certificate mismatch`
- `host header`
- `TLS termination`
- `reverse proxy routing`
- `multi-tenant ingress`

## 깊이 들어가기

### 1. SNI가 왜 필요한가

하나의 IP에 여러 사이트나 서비스가 붙을 수 있다.

- `api.example.com`
- `admin.example.com`
- `static.example.com`

TLS handshake 전에 서버는 아직 어떤 인증서를 줘야 할지 모를 수 있다.  
SNI가 그 힌트를 준다.

### 2. routing mismatch는 어떻게 생기나

SNI, Host header, backend route가 서로 다르면 이상해진다.

- TLS 단계에서는 A로 들어왔는데
- HTTP Host header는 B이고
- proxy는 C backend로 보낸다

이 경우 인증서는 맞는데 서비스는 틀리거나, 반대로 서비스는 맞는데 인증서가 틀릴 수 있다.

### 3. multi-tenant ingress에서 왜 민감한가

한 LB나 ingress에 여러 팀/서비스가 모이면:

- SNI 기반 인증서 선택
- Host 기반 라우팅
- path 기반 라우팅

이 셋이 같이 돌아간다.  
설정이 조금만 어긋나도 "가끔 다른 서비스로 보이는" 증상이 생긴다.

### 4. health check와 왜 엇갈리나

health check는 보통 단순한 host나 path를 본다.

- 실제 고객 트래픽의 SNI와 다를 수 있다
- health check는 통과하지만 특정 hostname만 실패할 수 있다
- ingress rule이 특정 도메인에만 잘못 적용될 수 있다

### 5. hostname failure가 주는 신호

- certificate mismatch
- 421 Misdirected Request
- default backend로 빠짐
- 잘못된 virtual host 응답

## 실전 시나리오

### 시나리오 1: 같은 LB인데 특정 도메인만 인증서 에러가 난다

SNI에 맞는 cert bundle이 없거나 routing table이 틀렸을 수 있다.

### 시나리오 2: 브라우저는 되는데 내부 클라이언트만 실패한다

내부 SDK가 SNI를 안 보내거나 잘못된 hostname을 넣고 있을 수 있다.

### 시나리오 3: 인증서는 맞는데 응답 내용이 이상하다

host header와 SNI가 달라 다른 backend로 라우팅됐을 수 있다.

## 코드로 보기

### SNI 확인

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com
```

### Host header 확인

```bash
curl -H 'Host: api.example.com' https://1.2.3.4/
```

### 프록시 라우팅 감각

```text
SNI -> certificate choice
Host header -> HTTP routing
path -> backend handler
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| SNI 기반 멀티테넌시 | IP를 아낄 수 있다 | 라우팅 실수가 복잡해진다 | 여러 도메인 운영 |
| 전용 IP/전용 cert | 단순하다 | 비용과 관리량이 늘어난다 | 민감한 서비스 |
| Host 기반 분기 | 유연하다 | TLS와 HTTP 설정이 어긋날 수 있다 | reverse proxy |

핵심은 SNI와 Host를 따로 보되, 운영에서는 둘이 같은 의도를 가리키는지 확인하는 것이다.

## 꼬리질문

> Q: SNI는 왜 필요한가요?
> 핵심: TLS handshake 전에 어떤 인증서를 줄지 서버가 알기 위해서다.

> Q: SNI와 Host header가 다르면 어떻게 되나요?
> 핵심: 인증서와 라우팅이 서로 다른 backend를 가리킬 수 있다.

> Q: multi-tenant ingress에서 왜 자주 깨지나요?
> 핵심: 인증서 선택, 라우팅 규칙, health check가 함께 맞아야 하기 때문이다.

## 한 줄 정리

SNI는 TLS 단계의 호스트 힌트이므로, hostname과 라우팅 규칙이 어긋나면 같은 IP에서도 인증서와 backend가 서로 다른 서비스를 가리킬 수 있다.
