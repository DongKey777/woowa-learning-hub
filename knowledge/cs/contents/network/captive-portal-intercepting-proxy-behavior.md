---
schema_version: 3
title: "Captive Portal, Intercepting Proxy Behavior"
concept_id: network/captive-portal-intercepting-proxy-behavior
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- captive-portal-diagnosis
- intercepting-proxy-dns-tls
- network-login-walled-garden
aliases:
- captive portal
- intercepting proxy
- network login
- DNS hijack
- HTTPS interception
- walled garden
symptoms:
- Wi-Fi는 연결됐지만 앱 HTTPS 요청은 인증서 mismatch나 TLS failure로 실패한다
- HTTP는 portal로 redirect되는데 HTTPS는 redirect 없이 깨져 앱 장애처럼 보인다
- DNS 응답이 portal IP나 이상한 IP로 강제되어 origin 장애로 오해한다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/dns-over-https-operational-tradeoffs
- network/http-proxy-connect-tunnels
next_docs:
- network/dns-negative-caching-nxdomain-behavior
- network/tls-certificate-chain-ocsp-stapling-failure-modes
- network/happy-eyeballs-dual-stack-racing
- network/http-proxy-connect-tunnels
linked_paths:
- contents/network/dns-over-https-operational-tradeoffs.md
- contents/network/dns-negative-caching-nxdomain-behavior.md
- contents/network/http-proxy-connect-tunnels.md
- contents/network/tls-certificate-chain-ocsp-stapling-failure-modes.md
- contents/network/happy-eyeballs-dual-stack-racing.md
confusable_with:
- network/dns-over-https-operational-tradeoffs
- network/dns-negative-caching-nxdomain-behavior
- network/http-proxy-connect-tunnels
- network/tls-certificate-chain-ocsp-stapling-failure-modes
forbidden_neighbors: []
expected_queries:
- "Captive portal 때문에 DNS와 HTTPS가 이상하게 실패하는 흐름을 설명해줘"
- "HTTP는 로그인 페이지로 redirect되는데 HTTPS는 certificate mismatch가 나는 이유가 뭐야?"
- "Intercepting proxy가 DNS hijack과 walled garden을 만들면 앱 장애와 어떻게 구분해?"
- "공용 Wi-Fi에서 인터넷 연결됨처럼 보이지만 API가 실패하면 무엇부터 봐?"
- "portal detection과 HTTPS interception을 운영 진단 관점으로 정리해줘"
contextual_chunk_prefix: |
  이 문서는 captive portal, intercepting proxy, network login, DNS hijack,
  HTTPS interception, walled garden 상태에서 HTTP redirect와 TLS/cert
  failure가 앱 장애처럼 보이는 증상을 진단하는 advanced playbook이다.
---
# Captive Portal, Intercepting Proxy Behavior

> 한 줄 요약: captive portal과 intercepting proxy는 네트워크가 "인터넷처럼 보이지만 아직 인터넷이 아닌" 상태를 만들기 때문에, DNS와 TLS 실패가 이상하게 보일 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DNS over HTTPS Operational Trade-offs](./dns-over-https-operational-tradeoffs.md)
> - [DNS Negative Caching, NXDOMAIN Behavior](./dns-negative-caching-nxdomain-behavior.md)
> - [HTTP Proxy CONNECT Tunnels](./http-proxy-connect-tunnels.md)
> - [TLS Certificate Chain, OCSP Stapling Failure Modes](./tls-certificate-chain-ocsp-stapling-failure-modes.md)
> - [Happy Eyeballs, Dual-Stack Racing](./happy-eyeballs-dual-stack-racing.md)

retrieval-anchor-keywords: captive portal, intercepting proxy, MITM, network login, DNS hijack, HTTPS interception, proxy auth, walled garden, portal detection

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

Captive portal은 Wi-Fi나 네트워크에 접속했을 때, 인증/동의 페이지를 통과해야 인터넷이 되는 구조다.  
Intercepting proxy는 DNS나 HTTP/TLS를 가로채서 portal 또는 정책 페이지로 유도할 수 있다.

- DNS가 엉뚱한 IP를 돌려줄 수 있다
- HTTP는 portal로 리다이렉트될 수 있다
- HTTPS는 인증서 에러나 연결 실패처럼 보일 수 있다

### Retrieval Anchors

- `captive portal`
- `intercepting proxy`
- `MITM`
- `network login`
- `DNS hijack`
- `HTTPS interception`
- `proxy auth`
- `walled garden`
- `portal detection`

## 깊이 들어가기

### 1. 왜 이상하게 보이나

사용자는 "인터넷에 연결됨"처럼 보는데 실제로는 제한된 네트워크일 수 있다.

- 일부 도메인만 열려 있다
- DNS가 portal로 유도될 수 있다
- HTTPS 요청은 인증서 mismatch로 실패할 수 있다

### 2. portal이 DNS에 주는 영향

네트워크는 DNS를 가로채서 로그인 페이지 주소를 알려줄 수 있다.

- NXDOMAIN처럼 보이거나
- 특정 IP로 강제되거나
- 특정 DNS만 허용될 수 있다

### 3. HTTPS가 왜 특히 민감한가

HTTPS는 인증서 검증 때문에 portal이나 intercepting proxy와 충돌하기 쉽다.

- cert mismatch
- TLS handshake failure
- redirect가 안 보임

즉, 웹 앱이 아니라 **네트워크 상태**가 문제인 경우가 많다.

### 4. portal detection이 왜 필요한가

클라이언트는 "지금 인터넷이 진짜 되는가"를 감지하려고 한다.

- captive portal인지 확인한다
- 제한적 walled garden인지 확인한다
- 로그인 후 정상 경로로 돌아왔는지 확인한다

### 5. 운영에서 봐야 할 것

- DNS 응답이 정상인지
- HTTP가 로그인 페이지로 리다이렉트되는지
- HTTPS가 인증서 오류인지 네트워크 차단인지

## 실전 시나리오

### 시나리오 1: 와이파이는 연결됐는데 앱은 다 실패한다

captve portal이나 intercepting proxy를 의심한다.

### 시나리오 2: 특정 도메인만 HTTP로 열리고 HTTPS는 실패한다

portal/walled garden 정책일 수 있다.

### 시나리오 3: DNS는 되는데 실제 접속이 안 된다

portal이 DNS를 허용하지만 외부 목적지는 아직 막았을 수 있다.

## 코드로 보기

### portal 감지 감각

```bash
curl -I http://example.com
curl -v https://example.com
```

### DNS 확인

```bash
dig example.com
nslookup example.com
```

### 체크 포인트

```text
- HTTP is redirected?
- HTTPS certificate mismatched?
- DNS answers are hijacked?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| captive portal | 네트워크 접근 제어가 쉽다 | 사용자 경험이 복잡하다 | 공용 Wi-Fi |
| intercepting proxy | 정책 적용이 가능하다 | TLS와 프라이버시 이슈가 크다 | 기업 네트워크 |
| open internet | 단순하다 | 제어가 약하다 | 일반 공개망 |

핵심은 "연결됨"과 "진짜 인터넷이 됨"을 분리해서 봐야 한다는 점이다.

## 꼬리질문

> Q: captive portal은 왜 문제를 만들나요?
> 핵심: 네트워크가 부분적으로만 열려 있어 DNS/TLS 실패가 애매하게 보이기 때문이다.

> Q: intercepting proxy와 MITM의 차이는?
> 핵심: 기능적으로는 비슷한 면이 있지만, 운영 정책상 정당한 제어인지가 다르다.

> Q: portal 여부를 어떻게 감지하나요?
> 핵심: HTTP redirect, DNS 이상, TLS 실패 패턴을 함께 본다.

## 한 줄 정리

Captive portal과 intercepting proxy는 네트워크를 부분적으로만 열어두기 때문에, DNS와 TLS 실패를 앱 오류처럼 보이게 만든다.
