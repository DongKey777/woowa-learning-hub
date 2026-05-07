---
schema_version: 3
title: "HTTP Proxy CONNECT Tunnels"
concept_id: network/http-proxy-connect-tunnels
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 81
mission_ids: []
review_feedback_tags:
- http-connect-tunnel
- explicit-proxy-policy
- tls-proxy-boundary
aliases:
- HTTP CONNECT
- proxy tunnel
- HTTPS proxy
- CONNECT request
- explicit proxy
- TLS tunnel
symptoms:
- CONNECT 터널을 일반 HTTP proxy request처럼 보고 이후 TLS/SNI/ALPN 문제를 구분하지 못한다
- proxy auth나 host/port ACL 때문에 터널이 안 열리는 문제를 origin HTTPS 장애로 오해한다
- CONNECT MITM과 opaque tunnel을 같은 보안/관측 모델로 취급한다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- network/api-gateway-reverse-proxy-operational-points
- network/tls-loadbalancing-proxy
next_docs:
- network/http-proxy-auth-407-explicit-proxy
- network/captive-portal-intercepting-proxy-behavior
- network/forwarded-x-forwarded-for-x-real-ip-trust-boundary
- network/sni-routing-mismatch-hostname-failure
linked_paths:
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/tls-loadbalancing-proxy.md
- contents/network/proxy-protocol-client-ip-trust-boundary.md
- contents/network/http-methods-rest-idempotency.md
- contents/network/captive-portal-intercepting-proxy-behavior.md
confusable_with:
- network/http-proxy-auth-407-explicit-proxy
- network/captive-portal-intercepting-proxy-behavior
- network/tls-loadbalancing-proxy
- network/sni-routing-mismatch-hostname-failure
forbidden_neighbors: []
expected_queries:
- "HTTP CONNECT는 proxy에게 TCP tunnel을 열어 달라는 요청이라는 점을 설명해줘"
- "CONNECT 200 Connection Established 이후 TLS handshake 문제는 어디서 봐야 해?"
- "Explicit proxy에서 CONNECT host port ACL과 proxy auth 실패를 어떻게 구분해?"
- "CONNECT tunnel과 TLS MITM proxy는 보안과 관측 면에서 어떻게 달라?"
- "curl -x로 HTTPS proxy CONNECT 흐름을 확인하는 방법을 알려줘"
contextual_chunk_prefix: |
  이 문서는 HTTP CONNECT method, explicit proxy tunnel, 200 Connection
  Established, proxy auth/ACL, TLS tunnel, MITM interception, SNI/ALPN
  downstream failure를 다루는 advanced proxy playbook이다.
---
# HTTP Proxy CONNECT Tunnels

> 한 줄 요약: CONNECT는 HTTP 프록시를 통해 임의의 TCP 목적지로 터널을 여는 방식이라서, TLS와 사설 네트워크 접근에서 자주 보이지만 정책 통제가 중요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [Proxy Protocol, Client IP, Trust Boundary](./proxy-protocol-client-ip-trust-boundary.md)
> - [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md)
> - [Captive Portal, Intercepting Proxy Behavior](./captive-portal-intercepting-proxy-behavior.md)

retrieval-anchor-keywords: HTTP CONNECT, proxy tunnel, HTTPS proxy, tunneling, MITM, explicit proxy, TLS tunnel, proxy policy, CONNECT request

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

`CONNECT`는 HTTP 프록시에게 "이 호스트와 포트로 TCP 터널을 열어 달라"고 요청하는 메서드다.

- HTTP 프록시가 연결 중계자가 된다
- 이후 바이트는 거의 그대로 터널을 탄다
- HTTPS, 내부 사설망 접근, 사내 프록시 환경에서 자주 쓰인다

### Retrieval Anchors

- `HTTP CONNECT`
- `proxy tunnel`
- `HTTPS proxy`
- `tunneling`
- `MITM`
- `explicit proxy`
- `TLS tunnel`
- `proxy policy`
- `CONNECT request`

## 깊이 들어가기

### 1. CONNECT가 하는 일

일반 HTTP 요청은 프록시가 내용을 이해할 수 있다.

CONNECT는 다르다.

- 프록시가 목적지로 TCP 연결을 만든다
- 성공하면 `200 Connection Established`를 반환한다
- 이후 클라이언트와 목적지 사이를 바이트 터널로 이어준다

### 2. 왜 필요한가

- HTTPS 프록시를 통해 외부 접속을 해야 할 때
- 사내 정책상 explicit proxy를 통과해야 할 때
- 일부 비HTTP TCP 서비스에 proxy를 써야 할 때

### 3. 왜 정책 통제가 중요한가

CONNECT는 강력하다.

- 사실상 원하는 TCP 목적지로 나갈 수 있다
- 잘못 열면 보안 경계가 무너진다
- 승인되지 않은 포트나 호스트가 열릴 수 있다

그래서 프록시는 허용 대상과 포트를 제한한다.

### 4. MITM과 CONNECT의 차이

CONNECT는 터널이다.

- 프록시가 내용을 보지 않을 수 있다
- 반대로 프록시가 TLS를 종료해 MITM처럼 동작할 수도 있다
- 두 경우는 보안과 관측이 완전히 다르다

### 5. 운영에서 흔한 문제

- proxy auth 실패
- CONNECT 허용 포트 제한
- TLS handshake와 proxy timeout이 겹침
- downstream DNS나 SNI 문제가 CONNECT 뒤에서만 드러남

## 실전 시나리오

### 시나리오 1: 사내망에서만 HTTPS가 된다

explicit proxy를 통해 CONNECT가 허용되어 있기 때문일 수 있다.

### 시나리오 2: 프록시를 거치면 특정 사이트만 안 열린다

CONNECT ACL, 포트 제한, 인증 정책을 의심한다.

### 시나리오 3: 터널은 열리는데 TLS가 실패한다

CONNECT 이후의 SNI/ALPN/certificate 문제를 봐야 한다.

## 코드로 보기

### curl로 CONNECT 감각 보기

```bash
curl -x http://proxy.example.com:3128 https://example.com -v
```

### 프록시 응답 감각

```text
CONNECT example.com:443 HTTP/1.1
200 Connection Established
```

### 체크 포인트

```text
- proxy auth
- allowed host/port
- tunnel timeout
- downstream TLS succeeds
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| CONNECT tunnel | 어떤 TCP 목적지든 이어줄 수 있다 | 정책 통제가 어려울 수 있다 | explicit proxy |
| direct connect | 단순하다 | 통제/감사가 약하다 | 내부/신뢰망 |
| TLS termination proxy | 관측이 쉽다 | 프라이버시/보안 경계가 바뀐다 | 보안 게이트 |

핵심은 CONNECT를 "우회"가 아니라 **통제된 터널링**으로 보는 것이다.

## 꼬리질문

> Q: CONNECT는 무엇을 하나요?
> 핵심: HTTP 프록시를 통해 임의 TCP 목적지로 터널을 연다.

> Q: 왜 사내망에서 자주 쓰나요?
> 핵심: explicit proxy 정책과 인증, 감사가 필요하기 때문이다.

> Q: CONNECT와 MITM의 차이는?
> 핵심: CONNECT는 터널이고 MITM은 TLS를 종료해 내용을 본다.

## 한 줄 정리

HTTP CONNECT는 프록시를 통해 TCP 터널을 여는 방식이므로, 터널 정책과 downstream TLS 문제를 분리해서 봐야 한다.
