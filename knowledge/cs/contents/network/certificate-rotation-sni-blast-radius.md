# Certificate Rotation, SNI Blast Radius

> 한 줄 요약: 인증서 회전은 단순 교체가 아니라 SNI별 라우팅과 bundle 배포가 함께 맞아야 하는 작업이라, 하나만 틀어져도 blast radius가 커진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TLS Certificate Chain, OCSP Stapling Failure Modes](./tls-certificate-chain-ocsp-stapling-failure-modes.md)
> - [ALPN Negotiation Failure, Routing Mismatch](./alpn-negotiation-failure-routing-mismatch.md)
> - [SNI, Routing Mismatch, Hostname Failure](./sni-routing-mismatch-hostname-failure.md)
> - [TLS Session Resumption, 0-RTT, Replay Risk](./tls-session-resumption-0rtt-replay-risk.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)

retrieval-anchor-keywords: certificate rotation, SNI blast radius, fullchain, cert renewal, cert bundle, ingress rollout, TLS termination, staged rotation, hot reload

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로 보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

인증서 회전은 "새 파일로 바꾸면 끝"이 아니다.

- SNI마다 다른 cert bundle이 있을 수 있다
- LB, proxy, ingress가 각자 다른 배포 주기를 가질 수 있다
- 잘못하면 특정 도메인만 대량 실패한다

### Retrieval Anchors

- `certificate rotation`
- `SNI blast radius`
- `fullchain`
- `cert renewal`
- `cert bundle`
- `ingress rollout`
- `TLS termination`
- `staged rotation`
- `hot reload`

## 깊이 들어가기

### 1. 왜 blast radius가 커지나

한 IP에서 여러 도메인을 호스팅하는 경우가 많다.

- SNI별로 인증서 선택
- host별로 backend routing
- 여러 리전/PoP에 동시에 배포

회전 한 번이 전체 경로를 건드릴 수 있다.

### 2. 어떤 실수가 흔한가

- 중간 인증서 누락
- 한 리전만 새 cert 적용
- hot reload가 일부 worker에만 반영
- SNI와 SAN이 안 맞는 bundle 배포

### 3. staged rotation이 왜 필요한가

한 번에 바꾸면 blast radius가 크다.

- 일부 트래픽만 새 인증서로 보낸다
- 일정 시간 동안 old/new를 함께 유지한다
- 문제가 없으면 전체를 전환한다

### 4. hot reload가 만능이 아닌 이유

hot reload는 편하지만, 설정 동기화가 느슨해질 수 있다.

- 일부 프로세스만 새 설정을 읽는다
- cache와 session resumption이 섞인다
- 롤백이 어려워질 수 있다

### 5. 어디서 특히 아픈가

- public ingress
- multi-tenant gateway
- gRPC/HTTP 혼합 endpoint
- CDN origin 인증서 교체

## 실전 시나리오

### 시나리오 1: 특정 도메인만 인증서 에러가 난다

SNI별 bundle 누락이나 SAN mismatch일 수 있다.

### 시나리오 2: 새 인증서로 바꿨는데 일부 리전만 실패한다

롤아웃이 완전히 끝나지 않았거나 hot reload가 일부만 반영됐을 수 있다.

### 시나리오 3: 회전 직후 TLS 세션 재개 비율이 떨어진다

ticket key나 bundle 교체로 resumption cache가 흔들릴 수 있다.

## 코드로 보기

### 인증서 확인

```bash
openssl x509 -in fullchain.pem -noout -dates -subject -issuer
openssl s_client -connect api.example.com:443 -servername api.example.com -showcerts
```

### 배포 감각

```text
stage 1: canary
stage 2: partial rollout
stage 3: full rollout
stage 4: verify chain and SNI mapping
```

### 운영 체크

```text
- 모든 SNI가 새 cert를 보는가
- intermediate가 포함됐는가
- resumption key가 리전별로 일관적인가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 한 번에 교체 | 단순하다 | blast radius가 크다 | 작은 환경 |
| staged rotation | 안전하다 | 운영 절차가 복잡하다 | 대규모 서비스 |
| hot reload | 무중단에 가깝다 | 반영 일관성 검증이 필요하다 | 상시 운영 |

핵심은 인증서 교체를 파일 작업이 아니라 **라우팅/배포 작업**으로 보는 것이다.

## 꼬리질문

> Q: 인증서 rotation에서 가장 위험한 점은 무엇인가요?
> 핵심: SNI별 bundle mismatch와 일부 리전만 반영되는 불일치다.

> Q: 왜 staged rotation이 필요한가요?
> 핵심: blast radius를 줄이고 문제가 있으면 빨리 되돌리기 위해서다.

> Q: resumption과는 어떤 관계가 있나요?
> 핵심: rotation이 resumption key와 bundle을 흔들어 세션 재개율을 바꿀 수 있다.

## 한 줄 정리

인증서 회전은 SNI와 배포 경로가 얽힌 작업이라, staged rollout과 chain 검증 없이 바꾸면 blast radius가 커진다.
