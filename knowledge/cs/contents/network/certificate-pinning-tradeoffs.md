# Certificate Pinning Trade-offs

> 한 줄 요약: certificate pinning은 중간자 공격을 줄일 수 있지만, 인증서 회전과 복구 유연성을 크게 깎아 운영 리스크를 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TLS Certificate Chain, OCSP Stapling Failure Modes](./tls-certificate-chain-ocsp-stapling-failure-modes.md)
> - [Certificate Rotation, SNI Blast Radius](./certificate-rotation-sni-blast-radius.md)
> - [OCSP, CRL Revocation Trade-offs](./ocsp-crl-revocation-tradeoffs.md)
> - [TLS Session Resumption, 0-RTT, Replay Risk](./tls-session-resumption-0rtt-replay-risk.md)
> - [mTLS Handshake Failure Diagnosis](./mtls-handshake-failure-diagnosis.md)

retrieval-anchor-keywords: certificate pinning, SPKI pinning, public key pinning, rotation risk, backup pin, mobile client, trust anchor, TLS hardening, operational risk

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

certificate pinning은 클라이언트가 특정 인증서나 공개키 집합만 믿도록 하는 방식이다.

- 중간 CA 신뢰를 줄인다
- 잘못된 인증서 체인을 빠르게 차단할 수 있다
- 하지만 rotation이 매우 어렵다

### Retrieval Anchors

- `certificate pinning`
- `SPKI pinning`
- `public key pinning`
- `rotation risk`
- `backup pin`
- `mobile client`
- `trust anchor`
- `TLS hardening`
- `operational risk`

## 깊이 들어가기

### 1. 왜 pinning을 하는가

일반 trust store만 믿는 대신, 더 좁은 집합을 신뢰하고 싶을 수 있다.

- 모바일 앱 보안 강화
- 특정 백엔드 보호
- 신뢰 체인 축소

### 2. 왜 위험한가

인증서는 바뀐다.

- 만료된다
- 회전한다
- 재발급된다
- CA 체인이 바뀔 수 있다

핀을 너무 강하게 걸면 합법적인 교체도 막는다.

### 3. backup pin이 왜 중요한가

교체 경로를 남겨두지 않으면 장애 시 클라이언트가 영구적으로 막힐 수 있다.

- 기본 pin
- backup pin
- 교체 순서

이 셋을 함께 설계해야 한다.

### 4. SPKI pinning이 자주 언급되는 이유

전체 인증서보다 공개키 기준이 rotation에 조금 더 유연할 수 있다.

- 체인 전체보다 덜 자주 바뀔 수 있다
- 하지만 키 교체 정책은 여전히 어렵다

### 5. 언제 쓰고 언제 피하나

- 매우 민감한 모바일 클라이언트
- 고정된 backend 집합
- 보안팀이 rotation 절차를 통제할 수 있을 때

반대로 일반 웹 서비스는 운영 리스크가 더 클 수 있다.

## 실전 시나리오

### 시나리오 1: 인증서 교체 후 일부 앱이 전부 실패한다

pinning이 새 cert를 허용하지 않았을 수 있다.

### 시나리오 2: 보안은 좋아졌는데 장애 복구가 어려워졌다

backup pin이나 rollover 전략이 부족했을 수 있다.

### 시나리오 3: 중간 CA 교체 후 이상하다

pinning 범위가 너무 넓거나 너무 좁을 수 있다.

## 코드로 보기

### 개념 감각

```text
trusted set:
- primary pin
- backup pin

failure mode:
- rotation without backup => outage
```

### 체크 포인트

```text
- pin rotation plan exists
- backup pin tested
- rollback path defined
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| pinning strong | MITM 위험을 줄인다 | rotation 장애 위험이 크다 | 모바일/고보안 |
| pinning weak | 운영이 쉽다 | 보안 효과가 제한적이다 | 일반 서비스 |
| SPKI + backup | 균형이 좋다 | 설계가 필요하다 | 실무 타협 |

핵심은 pinning이 보안 기능이지만 동시에 **운영 장애 증폭 장치**가 될 수 있다는 점이다.

## 꼬리질문

> Q: certificate pinning의 장점은 무엇인가요?
> 핵심: 신뢰 범위를 줄여 중간자/오탐 위험을 낮춘다.

> Q: 왜 운영 리스크가 큰가요?
> 핵심: 인증서 회전과 롤백이 어려워지기 때문이다.

> Q: backup pin이 왜 필요한가요?
> 핵심: 합법적인 교체를 허용하는 안전장치이기 때문이다.

## 한 줄 정리

certificate pinning은 강한 보안 이득이 있지만, rotation과 rollback 경로를 잘못 설계하면 바로 장애로 이어진다.
