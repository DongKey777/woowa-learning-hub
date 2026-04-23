# TLS, 로드밸런싱, 프록시

> 한 줄 요약: TLS, 로드밸런싱, 프록시는 각각 따로 배워도 되지만, 실제 장애는 인증서, 라우팅, 연결 재사용, timeout이 엉켜서 난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TLS Certificate Chain, OCSP Stapling Failure Modes](./tls-certificate-chain-ocsp-stapling-failure-modes.md)
> - [Certificate Rotation, SNI Blast Radius](./certificate-rotation-sni-blast-radius.md)
> - [ALPN Negotiation Failure, Routing Mismatch](./alpn-negotiation-failure-routing-mismatch.md)
> - [SNI, Routing Mismatch, Hostname Failure](./sni-routing-mismatch-hostname-failure.md)
> - [Proxy Header Normalization Chain, Trust Boundary](./proxy-header-normalization-chain-trust-boundary.md)
> - [HTTP Proxy CONNECT Tunnels](./http-proxy-connect-tunnels.md)
> - [LB Connection Draining, Deployment Safe Close](./lb-connection-draining-deployment-safe-close.md)
> - [TLS Session Resumption, 0-RTT, Replay Risk](./tls-session-resumption-0rtt-replay-risk.md)
> - [mTLS Handshake Failure Diagnosis](./mtls-handshake-failure-diagnosis.md)
> - [TLS Record Sizing, Flush, Streaming Latency](./tls-record-sizing-flush-streaming-latency.md)
> - [TLS close_notify, FIN/RST, Truncation](./tls-close-notify-fin-rst-truncation.md)
> - [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)

retrieval-anchor-keywords: TLS handshake, load balancing, reverse proxy, TLS termination, SNI, ALPN, certificate chain, backend routing, connection reuse, client IP, proxy timeout

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

이 문서는 TLS, 로드밸런싱, 프록시를 따로 보지 않고 **요청 경로 전체**로 본다.

- TLS는 연결의 신뢰와 암호화를 맡는다
- 로드밸런서는 요청을 여러 backend로 나눈다
- 프록시는 TLS 종료, 헤더 정리, timeout, buffering, routing을 담당한다

문제는 이 셋이 합쳐졌을 때 생긴다.

- 인증서 회전이 라우팅을 깨뜨린다
- keep-alive가 stale backend를 재사용한다
- proxy timeout이 upstream보다 먼저 끊는다
- SNI/ALPN/Host가 서로 다른 방향을 가리킨다

### Retrieval Anchors

- `TLS handshake`
- `load balancing`
- `reverse proxy`
- `TLS termination`
- `SNI`
- `ALPN`
- `certificate chain`
- `backend routing`
- `connection reuse`
- `client IP`
- `proxy timeout`

## 깊이 들어가기

### 1. TLS는 왜 앞단에서 자주 끝나는가

TLS 종료 지점은 보통 프록시나 LB다.

- backend가 직접 인증서를 관리하지 않아도 된다
- 트래픽 분산 전에 인증과 암호화를 끝낼 수 있다
- 하지만 종료 지점이 많을수록 설정 불일치가 생긴다

### 2. 로드밸런싱은 단순 분산이 아니다

실제 분산은 다음 요소에 의해 왜곡된다.

- keep-alive로 인해 connection 수와 request 수가 다르다
- long-lived connection이 있으면 least-connections가 흔들린다
- health check와 실제 요청 경로가 다를 수 있다
- drain 중인 backend로 새 요청이 가면 실패한다

### 3. 프록시는 경계 장치다

프록시는 단순 중계기가 아니라 운영 정책을 구현한다.

- TLS 종료
- 헤더 정리
- request/response buffering
- retry
- timeout
- routing

그래서 프록시 설정이 곧 서비스 정책이다.

### 4. 인증서와 라우팅이 왜 같이 깨지나

SNI로 인증서를 선택하고, Host나 path로 backend를 고른다.

- SNI와 SAN이 안 맞으면 handshake가 깨진다
- ALPN이 기대와 다르면 gRPC/HTTP2가 틀어진다
- 잘못된 host header는 다른 backend로 보낼 수 있다

이 부분은 [ALPN Negotiation Failure, Routing Mismatch](./alpn-negotiation-failure-routing-mismatch.md), [SNI, Routing Mismatch, Hostname Failure](./sni-routing-mismatch-hostname-failure.md)와 같이 봐야 한다.

### 5. keep-alive와 draining이 왜 함께 있어야 하나

연결 재사용은 성능을 높이지만, backend가 교체될 때 문제를 만든다.

- 오래된 연결이 살아 있다
- 새 요청이 죽은 backend로 간다
- 요청은 실패하고 retry가 붙는다

그래서 [LB Connection Draining, Deployment Safe Close](./lb-connection-draining-deployment-safe-close.md)가 필요하다.

### 6. 헤더와 IP는 신뢰 경계를 가진다

프록시 앞단에서는 client IP가 바뀐다.

- `X-Forwarded-For`가 필요하다
- 그러나 아무 값을 믿으면 안 된다
- trusted proxy chain으로만 해석해야 한다

이 부분은 [Proxy Header Normalization Chain, Trust Boundary](./proxy-header-normalization-chain-trust-boundary.md)와 맞물린다.

## 실전 시나리오

### 시나리오 1: HTTPS는 되는데 gRPC만 실패한다

ALPN이 `h2`로 협상되지 않았을 수 있다.

### 시나리오 2: 특정 도메인만 인증서 에러가 난다

SNI별 cert bundle 또는 rotation이 어긋났을 수 있다.

### 시나리오 3: 배포 중 502/504가 튄다

draining이 없거나 proxy timeout이 upstream보다 짧을 수 있다.

### 시나리오 4: 로그에 client IP가 이상하게 찍힌다

헤더 normalization이나 trust boundary가 깨졌을 수 있다.

## 코드로 보기

### TLS와 라우팅 확인

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com -showcerts
curl -I --http2 https://api.example.com
```

### 프록시 관찰

```bash
kubectl logs deploy/gateway -c proxy
ss -tan state established
```

### 운영 포인트

```text
- certificate chain complete
- SNI/SAN match
- ALPN matches expected protocol
- proxy timeout > upstream response budget
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| TLS termination at proxy | 중앙 관리가 쉽다 | 종료 지점이 병목이 된다 | 일반적인 웹 서비스 |
| pass-through TLS | end-to-end가 유지된다 | 라우팅과 관측이 어렵다 | 민감한 내부 통신 |
| per-service TLS | 경계가 명확하다 | 운영 비용이 커진다 | mTLS/zero-trust |

핵심은 TLS, LB, proxy를 각각 따로 설정하지 말고 **같은 요청 경로의 일부**로 설계하는 것이다.

## 꼬리질문

> Q: TLS와 로드밸런서는 왜 같이 보나요?
> 핵심: TLS 종료 지점이 LB/프록시인 경우가 많아서 인증과 분산 정책이 얽히기 때문이다.

> Q: 프록시가 왜 운영 정책인가요?
> 핵심: timeout, retry, buffering, header rewriting을 모두 정하기 때문이다.

> Q: 연결 재사용이 왜 문제를 만들 수 있나요?
> 핵심: 오래된 backend 연결이 새 요청의 목적지와 어긋날 수 있기 때문이다.

## 한 줄 정리

TLS, 로드밸런싱, 프록시는 따로 보면 쉬워 보이지만 실제로는 인증서, 라우팅, timeout, 연결 재사용이 하나의 요청 경로에서 함께 작동한다.
