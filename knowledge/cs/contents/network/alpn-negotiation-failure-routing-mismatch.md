# ALPN Negotiation Failure, Routing Mismatch

> 한 줄 요약: ALPN은 TLS handshake에서 어떤 프로토콜을 쓸지 합의하는 단계라서, 여기서 어긋나면 HTTP/1.1, HTTP/2, gRPC 라우팅이 전부 틀어질 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TLS Certificate Chain, OCSP Stapling Failure Modes](./tls-certificate-chain-ocsp-stapling-failure-modes.md)
> - [TLS Session Resumption, 0-RTT, Replay Risk](./tls-session-resumption-0rtt-replay-risk.md)
> - [gRPC vs REST](./grpc-vs-rest.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)

retrieval-anchor-keywords: ALPN, protocol negotiation, h2, http/1.1, grpc, TLS handshake, routing mismatch, protocol fallback, ssl_preread

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

ALPN(Application-Layer Protocol Negotiation)은 TLS handshake 동안 **어떤 상위 프로토콜을 사용할지** 합의하는 메커니즘이다.

- `h2`를 선택하면 HTTP/2를 쓴다
- `http/1.1`을 선택하면 HTTP/1.1을 쓴다
- gRPC는 사실상 HTTP/2 위에 올라가므로 ALPN 결과가 중요하다

### Retrieval Anchors

- `ALPN`
- `protocol negotiation`
- `h2`
- `http/1.1`
- `grpc`
- `TLS handshake`
- `routing mismatch`
- `protocol fallback`
- `ssl_preread`

## 깊이 들어가기

### 1. ALPN이 왜 필요한가

TLS는 암호화만 하는 게 아니다.  
연결 이후 어떤 HTTP 계층을 쓸지도 같이 정해야 한다.

- 브라우저는 HTTP/2를 선호할 수 있다
- 일부 클라이언트는 HTTP/1.1만 지원한다
- gRPC는 HTTP/2가 없으면 성립하지 않는다

### 2. failure가 어떻게 보이나

ALPN 협상이 실패하면 흔히 이런 형태로 보인다.

- 의도한 프로토콜보다 낮은 버전으로 fallback된다
- gRPC 호출이 HTTP/1.1로 들어가 실패한다
- proxy가 HTTP/2를 못 받아 downstream mismatch가 생긴다

### 3. routing mismatch는 왜 생기나

앞단 LB나 proxy가 TLS를 종료하면서 프로토콜 판단을 잘못하면:

- HTTP/2 전용 backend로 보내야 할 요청이 다른 backend로 간다
- gRPC path가 REST path로 오인된다
- health check는 되는데 실제 트래픽만 실패한다

### 4. ssl_preread와의 관계

TLS를 종료하기 전에 SNI/ALPN을 보고 라우팅하는 경우가 있다.

- `ssl_preread`로 대략의 프로토콜을 읽는다
- 이후 backend 분기 여부를 결정한다
- 설정이 틀리면 프로토콜과 라우팅이 어긋난다

### 5. 운영에서 더 중요한 점

ALPN 문제는 종종 "네트워크"처럼 보이지만 실제론 라우팅/배포 문제다.

- LB 설정
- backend pool 분리
- TLS 종료 지점
- 프록시 패스스루 여부

## 실전 시나리오

### 시나리오 1: gRPC 호출만 실패한다

ALPN이 `h2`로 협상되지 않으면 gRPC는 성립하지 않는다.

### 시나리오 2: 브라우저는 되는데 API gateway 뒤에서만 이상하다

gateway가 ALPN으로 protocol fallback을 잘못 처리했을 수 있다.

### 시나리오 3: 일부 리전만 HTTP/2가 안 된다

리전별 LB 설정이나 cert bundle이 달라서 negotiation 결과가 달라질 수 있다.

## 코드로 보기

### openssl로 ALPN 확인

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com -alpn h2
```

### curl로 프로토콜 확인

```bash
curl -I --http2 https://api.example.com
```

### 관찰 포인트

```text
- negotiated protocol이 무엇인가
- 기대한 backend로 라우팅되었는가
- fallback이 의도된 것인가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| ALPN 기반 협상 | 프로토콜 선택이 자동화된다 | 설정 오류가 라우팅 문제로 번진다 | HTTPS 다중 프로토콜 |
| 고정 프로토콜 | 단순하다 | 유연성이 낮다 | 내부 통제 환경 |
| fallback 허용 | 호환성이 높다 | 성능/기능이 예상과 달라질 수 있다 | 점진 전환 |

핵심은 협상이 실패했을 때 **조용히 틀린 경로로 가지 않게** 하는 것이다.

## 꼬리질문

> Q: ALPN은 무엇을 결정하나요?
> 핵심: TLS handshake 이후 사용할 애플리케이션 프로토콜을 결정한다.

> Q: 왜 gRPC에 중요하나요?
> 핵심: gRPC는 HTTP/2가 사실상 필요하기 때문이다.

> Q: negotiation 실패가 왜 routing 문제로 보이나요?
> 핵심: TLS 종료 지점이 프로토콜에 따라 backend를 다르게 골라야 하기 때문이다.

## 한 줄 정리

ALPN은 TLS 위에서 사용할 프로토콜을 정하는 협상이므로, 실패하면 단순 암호화 문제가 아니라 라우팅과 backend 선택 문제로 이어진다.
