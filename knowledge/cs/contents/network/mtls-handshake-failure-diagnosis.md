# mTLS Handshake Failure Diagnosis

> 한 줄 요약: mTLS 실패는 인증서만의 문제가 아니라 SNI, ALPN, trust store, 시간, 그리고 peer identity 매칭이 함께 어긋날 때 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TLS Certificate Chain, OCSP Stapling Failure Modes](./tls-certificate-chain-ocsp-stapling-failure-modes.md)
> - [ALPN Negotiation Failure, Routing Mismatch](./alpn-negotiation-failure-routing-mismatch.md)
> - [SNI, Routing Mismatch, Hostname Failure](./sni-routing-mismatch-hostname-failure.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](../security/service-to-service-auth-mtls-jwt-spiffe.md)
> - [Service Mesh, Sidecar Proxy](./service-mesh-sidecar-proxy.md)

retrieval-anchor-keywords: mTLS, handshake failure, client certificate, trust store, SAN, SNI, ALPN, peer identity, certificate rotation

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

mTLS는 서로 인증서를 제시해 양방향 신원을 확인하는 TLS다.  
실패 원인은 보통 아래가 섞여 나온다.

- client cert가 없거나 만료됨
- trust store가 맞지 않음
- SAN과 SNI가 어긋남
- ALPN이 맞지 않음
- 시간이 틀려 인증서가 유효하지 않게 보임

### Retrieval Anchors

- `mTLS`
- `handshake failure`
- `client certificate`
- `trust store`
- `SAN`
- `SNI`
- `ALPN`
- `peer identity`
- `certificate rotation`

## 깊이 들어가기

### 1. 어디서 깨지는가

mTLS handshake는 단계가 많다.

- 서버 인증서 검증
- client certificate 제시
- identity mapping
- ALPN/SNI 협상

따라서 실패 시점에 따라 원인이 다르다.

### 2. 가장 흔한 실패 원인

- client cert가 아예 없다
- 인증서 체인이 불완전하다
- SAN이 정책과 맞지 않는다
- trust store에 issuer가 없다
- clock skew로 아직 유효하지 않거나 이미 만료된 것으로 보인다

### 3. sidecar proxy가 끼면 복잡해지는 이유

서비스 메시에서는 앱과 proxy의 역할이 나뉜다.

- 앱은 요청 로직을 본다
- sidecar는 TLS/mTLS를 처리한다
- identity는 proxy 로그에서 더 잘 보일 수 있다

### 4. 진단 순서

1. handshake error 메시지 확인
2. client/server cert 체인 확인
3. SNI와 ALPN 확인
4. trust store와 clock 확인
5. proxy/sidecar 로그 확인

### 5. 운영에서 자주 놓치는 점

- 인증서 rotation 후 일부 pod만 새 bundle을 못 봄
- 내부 CA 교체 후 trust store 배포가 늦음
- mTLS가 HTTP 라우팅보다 먼저 실패함

## 실전 시나리오

### 시나리오 1: 개발 환경에서는 되는데 프로덕션에서 실패한다

issuer, trust store, ALPN, SNI 정책 차이를 의심한다.

### 시나리오 2: 일부 서비스만 서로 통신이 안 된다

peer identity policy나 SAN mapping이 좁아졌을 수 있다.

### 시나리오 3: handshake는 되지만 요청이 바로 끊긴다

mTLS 이후의 authorization policy나 proxy routing을 본다.

## 코드로 보기

### openssl로 검사

```bash
openssl s_client -connect inventory-api:8443 -servername inventory-api -showcerts
```

### sidecar 로그와 함께 보기

```bash
kubectl logs deploy/orders-api -c istio-proxy
kubectl describe peerauthentication -n payments
```

### 체크 포인트

```text
- cert chain complete
- SAN matches policy
- trust store includes issuer
- clock is in sync
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 강한 mTLS 정책 | 신뢰가 높다 | 실패 원인이 많아진다 | 내부 서비스 통신 |
| 느슨한 정책 | 운영이 쉽다 | 보안 경계가 약해진다 | 초기 도입 |
| 단계적 적용 | 리스크를 줄인다 | 구성 복잡도가 있다 | 대규모 전환 |

핵심은 mTLS 실패를 "TLS 에러" 하나로 보지 말고 **identity mismatch 문제**로 분해하는 것이다.

## 꼬리질문

> Q: mTLS handshake가 왜 실패하나요?
> 핵심: client cert, trust store, SAN/SNI, ALPN, 시간 조건이 어긋날 수 있다.

> Q: sidecar가 있으면 뭐가 달라지나요?
> 핵심: TLS 처리와 identity 확인이 proxy로 이동해 로그 위치가 달라진다.

> Q: 가장 먼저 볼 것은?
> 핵심: cert chain, trust store, SNI/ALPN, clock이다.

## 한 줄 정리

mTLS handshake 실패는 인증서 자체뿐 아니라 identity, SNI, ALPN, trust store가 동시에 맞아야 풀리는 문제다.
