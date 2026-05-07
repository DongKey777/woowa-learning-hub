---
schema_version: 3
title: "TLS Certificate Chain, OCSP Stapling Failure Modes"
concept_id: network/tls-certificate-chain-ocsp-stapling-failure-modes
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- tls-certificate
- ocsp-stapling
- handshake-failure
aliases:
- TLS certificate chain
- OCSP stapling failure
- intermediate certificate missing
- certificate chain validation
- stapled OCSP freshness
- trust store mismatch
- TLS handshake cert error
symptoms:
- leaf certificate만 보고 intermediate chain 누락이나 trust store 차이를 놓친다
- OCSP stapling stale/expired가 일부 client handshake failure로 보이는 이유를 설명하지 못한다
- SNI에 따라 다른 certificate chain이 나가는 문제를 hostname routing과 연결하지 않는다
- certificate rotation 뒤 일부 edge나 pod만 old chain을 내보내는 문제를 놓친다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/tls-loadbalancing-proxy
- network/sni-routing-mismatch-hostname-failure
next_docs:
- network/ocsp-crl-revocation-tradeoffs
- network/certificate-rotation-sni-blast-radius
- network/mtls-handshake-failure-diagnosis
- network/tls-session-resumption-0rtt-replay-risk
linked_paths:
- contents/network/tls-session-resumption-0rtt-replay-risk.md
- contents/network/tls-loadbalancing-proxy.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/dns-cdn-websocket-http2-http3.md
- contents/network/timeout-types-connect-read-write.md
confusable_with:
- network/ocsp-crl-revocation-tradeoffs
- network/certificate-rotation-sni-blast-radius
- network/mtls-handshake-failure-diagnosis
- network/sni-routing-mismatch-hostname-failure
forbidden_neighbors: []
expected_queries:
- "TLS certificate chain failure를 leaf intermediate trust store 관점으로 진단해줘"
- "OCSP stapling이 stale하면 어떤 handshake failure가 생겨?"
- "SNI별 certificate chain mismatch를 어떻게 확인해?"
- "certificate rotation 후 일부 edge만 old intermediate를 내보내는 문제는?"
- "OCSP CRL revocation과 stapling failure는 어떻게 달라?"
contextual_chunk_prefix: |
  이 문서는 TLS certificate chain validation, intermediate certificate,
  trust store, OCSP stapling freshness, SNI별 certificate mismatch와 rotation failure를
  다루는 advanced playbook이다.
---
# TLS Certificate Chain, OCSP Stapling Failure Modes

> 한 줄 요약: TLS 인증서는 "있다/없다"보다 체인 검증, 만료, 중간 인증서, revocation 확인이 함께 맞아야 살아난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TLS Session Resumption, 0-RTT, Replay Risk](./tls-session-resumption-0rtt-replay-risk.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [DNS, CDN, HTTP/2, HTTP/3](./dns-cdn-websocket-http2-http3.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)

retrieval-anchor-keywords: certificate chain, intermediate certificate, root CA, OCSP stapling, revocation, SAN, SNI, certificate expiration, TLS alert, trust store

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

TLS 인증은 인증서 하나만 보는 문제가 아니다.

- 서버 인증서가 유효해야 한다
- 중간 인증서가 체인에 있어야 한다
- 클라이언트 trust store가 root CA를 신뢰해야 한다
- revocation 상태가 문제가 없어야 한다
- SNI와 SAN이 요청 호스트와 맞아야 한다

### Retrieval Anchors

- `certificate chain`
- `intermediate certificate`
- `root CA`
- `OCSP stapling`
- `revocation`
- `SAN`
- `SNI`
- `certificate expiration`
- `trust store`

## 깊이 들어가기

### 1. certificate chain이 왜 필요한가

브라우저와 클라이언트는 서버 인증서만 딱 보고 믿지 않는다.

- 서버 인증서
- intermediate CA
- root CA

이 체인이 이어져야 한다.  
중간 인증서가 빠지면 클라이언트는 "누가 이 인증서를 발급했는지"를 증명하지 못한다.

### 2. SAN과 SNI가 왜 자주 깨지나

인증서는 이제 보통 SAN(Subject Alternative Name)에 실제 호스트 이름을 넣는다.

- `api.example.com`
- `www.example.com`
- 와일드카드 도메인

클라이언트는 SNI로 "어떤 호스트의 인증서를 줄지"를 서버에 알려준다.  
이 둘이 어긋나면 이름 불일치 에러가 난다.

### 3. OCSP stapling은 무엇을 하는가

revocation 확인은 "이 인증서가 아직 취소되지 않았나"를 묻는 절차다.

- 서버가 OCSP 응답을 미리 받아 stapling한다
- 클라이언트는 별도 요청 없이 revocation 상태를 확인한다
- 지연과 프라이버시를 줄일 수 있다

하지만 stapling이 잘못되면:

- 응답이 만료된다
- 중간 장비가 OCSP 조회를 실패한다
- TLS handshake가 늦어지거나 실패할 수 있다

### 4. 체인 실패가 왜 운영에서 자주 보이나

많은 운영 사고는 인증서 자체보다 배포와 구성에서 난다.

- 새 인증서를 넣었는데 intermediate를 빼먹었다
- LB와 backend가 서로 다른 cert bundle을 쓴다
- cert rotation 후 stapling cache가 갱신되지 않는다
- 일부 리전만 오래된 trust chain을 본다

### 5. 만료보다 더 흔한 문제

인증서 만료는 쉽게 보이지만, 실제로는 아래가 더 자주 문제다.

- 잘못된 체인
- 잘못된 hostname
- trust store 불일치
- OCSP 실패
- 배포 중 인증서 파일 경로 오류

즉, "expire 전에 알림"만으로는 부족하다. **체인이 실제로 검증되는지**를 봐야 한다.

## 실전 시나리오

### 시나리오 1: 새 인증서를 넣었는데 일부 클라이언트만 실패한다

원인 후보:

- intermediate certificate 누락
- old proxy 캐시
- 특정 클라이언트 trust store 차이

### 시나리오 2: 브라우저는 되는데 일부 SDK만 실패한다

SDK의 trust store가 OS와 다를 수 있다.

- Java keystore
- mobile embedded trust store
- outdated CA bundle

### 시나리오 3: handshake가 갑자기 느려졌다

OCSP stapling이나 revocation check가 응답을 못 받아서 지연될 수 있다.

- OCSP responder 장애
- network path 차단
- stapling cache miss

### 시나리오 4: 특정 도메인만 SNI mismatch가 난다

LB 뒤에서 여러 인증서를 쓰는데 host routing이 틀어졌을 수 있다.

이 경우는 [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)와 같이 봐야 한다.

## 코드로 보기

### openssl로 체인 확인

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com -showcerts
```

### 만료일 확인

```bash
openssl x509 -in cert.pem -noout -dates -subject -issuer
```

### curl로 handshake와 인증 에러 보기

```bash
curl -v https://api.example.com/health
```

### Nginx 감각

```nginx
ssl_certificate     /etc/ssl/fullchain.pem;
ssl_certificate_key /etc/ssl/private.key;
ssl_stapling on;
ssl_stapling_verify on;
```

포인트:

- `fullchain.pem`을 써서 intermediate를 포함한다
- stapling을 켜면 revocation 상태를 더 효율적으로 전달할 수 있다

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| fullchain 배포 | 체인 누락을 줄인다 | 파일 관리가 필요하다 | 대부분의 운영 |
| OCSP stapling | revocation 확인 비용을 줄인다 | cache/응답 실패를 관리해야 한다 | 공개 서비스 |
| 단순 인증서만 배포 | 설정이 쉬워 보인다 | 체인 오류가 자주 난다 | 피해야 함 |

핵심은 인증서를 "갱신했다"가 아니라 **클라이언트가 실제로 검증할 수 있는 상태인가**다.

## 꼬리질문

> Q: 인증서 체인이 왜 중요한가요?
> 핵심: 중간 CA를 통해 root까지 신뢰 경로를 만들어야 하기 때문이다.

> Q: OCSP stapling은 왜 쓰나요?
> 핵심: revocation 확인을 빠르고 덜 노출되게 하기 위해서다.

> Q: SNI와 SAN이 왜 둘 다 필요한가요?
> 핵심: SNI는 어떤 인증서를 줄지 고르는 신호이고, SAN은 그 인증서가 어떤 이름을 커버하는지 보여준다.

## 한 줄 정리

TLS 인증 실패는 만료만이 아니라 체인, hostname, trust store, OCSP stapling이 함께 맞아야 하는 경로 문제로 봐야 한다.
