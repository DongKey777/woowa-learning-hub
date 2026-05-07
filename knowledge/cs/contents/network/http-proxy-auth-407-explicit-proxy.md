---
schema_version: 3
title: "HTTP Proxy Auth, 407, Explicit Proxy"
concept_id: network/http-proxy-auth-407-explicit-proxy
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 83
mission_ids: []
review_feedback_tags:
- explicit-proxy
- proxy-auth
- connect-tunnel
aliases:
- HTTP proxy auth
- 407 Proxy Authentication Required
- explicit proxy
- Proxy-Authorization
- Proxy-Authenticate
- CONNECT tunnel auth
- enterprise proxy ACL
symptoms:
- 407을 origin 서버 인증 실패나 401로 오해한다
- 브라우저는 되는데 CLI나 앱은 Proxy-Authorization을 보내지 않아 실패한다
- CONNECT tunnel이 proxy auth 전에 열리는 것으로 착각한다
- proxy 인증 통과와 host/port ACL 허용을 같은 단계로 본다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/http-proxy-connect-tunnels
- network/proxy-header-normalization-chain-trust-boundary
next_docs:
- network/captive-portal-intercepting-proxy-behavior
- network/tls-loadbalancing-proxy
- network/alb-elb-retry-amplification-proxy-chain
- network/proxy-local-reply-vs-upstream-error-attribution
linked_paths:
- contents/network/http-proxy-connect-tunnels.md
- contents/network/proxy-header-normalization-chain-trust-boundary.md
- contents/network/tls-loadbalancing-proxy.md
- contents/network/captive-portal-intercepting-proxy-behavior.md
- contents/network/alb-elb-retry-amplification-proxy-chain.md
confusable_with:
- network/http-proxy-connect-tunnels
- network/captive-portal-intercepting-proxy-behavior
- network/tls-loadbalancing-proxy
- network/proxy-local-reply-vs-upstream-error-attribution
forbidden_neighbors: []
expected_queries:
- "407 Proxy Authentication Required는 401과 어떻게 달라?"
- "explicit proxy에서 CONNECT tunnel 전에 proxy auth가 필요한 이유는?"
- "브라우저는 proxy 인증 prompt로 되는데 curl이나 앱은 왜 실패해?"
- "Proxy-Authorization과 Proxy-Authenticate 헤더는 어디에서 쓰여?"
- "proxy auth 통과 후에도 host port ACL에서 막힐 수 있는 이유는?"
contextual_chunk_prefix: |
  이 문서는 explicit proxy, 407 Proxy Authentication Required,
  Proxy-Authenticate/Proxy-Authorization, CONNECT tunnel 인증, enterprise proxy
  ACL을 다루는 advanced playbook이다.
---
# HTTP Proxy Auth, 407, Explicit Proxy

> 한 줄 요약: explicit proxy는 CONNECT나 일반 HTTP 요청 전에 인증이 필요할 수 있고, 407은 그 경계가 아직 통과되지 않았다는 신호다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HTTP Proxy CONNECT Tunnels](./http-proxy-connect-tunnels.md)
> - [Proxy Header Normalization Chain, Trust Boundary](./proxy-header-normalization-chain-trust-boundary.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [Captive Portal, Intercepting Proxy Behavior](./captive-portal-intercepting-proxy-behavior.md)
> - [ALB, ELB Retry Amplification, Proxy Chain](./alb-elb-retry-amplification-proxy-chain.md)

retrieval-anchor-keywords: HTTP proxy auth, 407, explicit proxy, proxy authentication, proxy-authorization, connect tunnel, proxy ACL, enterprise proxy, credential prompt

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

explicit proxy는 클라이언트가 명시적으로 통과해야 하는 프록시다.

- 요청 전에 인증이 필요할 수 있다
- 인증 실패는 `407 Proxy Authentication Required`로 보인다
- CONNECT 터널과 일반 HTTP 요청 모두에 적용될 수 있다

### Retrieval Anchors

- `HTTP proxy auth`
- `407`
- `explicit proxy`
- `proxy authentication`
- `proxy-authorization`
- `connect tunnel`
- `proxy ACL`
- `enterprise proxy`
- `credential prompt`

## 깊이 들어가기

### 1. 407이 의미하는 것

407은 origin 서버가 아니라 **프록시가** 인증을 요구하는 응답이다.

- `WWW-Authenticate`가 아니라 `Proxy-Authenticate` 계열을 본다
- 클라이언트는 `Proxy-Authorization` 헤더를 보내야 한다
- 인증이 통과돼야 다음 단계로 간다

### 2. 왜 enterprise 환경에서 자주 보이나

사내 네트워크는 보통 outbound를 통제한다.

- 인터넷 접근을 감사해야 한다
- 허용된 사용자인지 확인해야 한다
- 특정 도메인/포트를 제한해야 한다

그래서 proxy auth가 흔하다.

### 3. CONNECT와 어떻게 엮이나

CONNECT도 proxy auth 뒤에서 열릴 수 있다.

- 먼저 proxy 인증
- 그 다음 터널 생성
- 이후 TLS handshake 또는 TCP 데이터 전송

즉, 인증이 안 되면 터널도 없다.

### 4. 왜 디버깅이 어려운가

- 브라우저는 credential prompt를 띄울 수 있다
- CLI는 환경변수나 옵션으로 proxy를 넘겨야 한다
- 앱은 proxy 인증 실패를 origin 실패처럼 보일 수 있다

### 5. proxy ACL과의 관계

인증만 통과해도 모든 목적지가 열리는 것은 아니다.

- 호스트/포트 ACL
- 카테고리 정책
- 시간대별 정책

이 겹치면 407 이후에 또 다른 거절이 있을 수 있다.

## 실전 시나리오

### 시나리오 1: 브라우저에서만 인터넷이 안 된다

explicit proxy 인증이 요구될 수 있다.

### 시나리오 2: curl은 되는데 앱은 안 된다

앱이 `Proxy-Authorization`을 전달하지 않거나 proxy 설정이 빠졌을 수 있다.

### 시나리오 3: CONNECT는 되는데 HTTPS가 실패한다

proxy auth는 통과했지만 downstream TLS/SNI 문제일 수 있다.

## 코드로 보기

### curl 예시

```bash
curl -x http://proxy.example.com:3128 --proxy-user user:pass https://example.com -v
```

### 407 응답 감각

```text
407 Proxy Authentication Required
Proxy-Authenticate: Basic realm="corp"
```

### 체크 포인트

```text
- is proxy auth enabled?
- does CONNECT require auth?
- are host/port ACLs separate?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| explicit proxy auth | 통제가 쉽다 | 설정과 디버깅이 복잡하다 | 기업망 |
| direct outbound | 단순하다 | 정책/감사가 약하다 | 신뢰망 |
| proxy + ACL | 유연하다 | 정책이 복잡해진다 | 보안 게이트 |

핵심은 407을 "에러"로만 보지 말고 **아직 신뢰 경계를 넘지 못했다는 신호**로 보는 것이다.

## 꼬리질문

> Q: 407은 무엇을 뜻하나요?
> 핵심: 프록시 인증이 필요하다는 뜻이다.

> Q: Proxy-Authorization은 어디에 쓰이나요?
> 핵심: 프록시 인증을 통과시키는 요청 헤더다.

> Q: CONNECT와의 관계는?
> 핵심: 인증이 먼저이고, 그 다음에 터널이 열린다.

## 한 줄 정리

HTTP proxy auth의 407은 explicit proxy 경계에서 인증이 아직 끝나지 않았다는 뜻이며, CONNECT와 ACL까지 같이 봐야 한다.
