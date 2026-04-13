# DNS over HTTPS Operational Trade-offs

> 한 줄 요약: DoH는 DNS를 HTTPS로 숨겨 프라이버시와 무결성을 높이지만, 기업 네트워크의 가시성과 정책 제어를 약하게 만들 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DNS, CDN, HTTP/2, HTTP/3](./dns-cdn-websocket-http2-http3.md)
> - [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)
> - [TLS Session Resumption, 0-RTT, Replay Risk](./tls-session-resumption-0rtt-replay-risk.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [Forwarded, X-Forwarded-For, X-Real-IP와 Trust Boundary](./forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)

retrieval-anchor-keywords: DNS over HTTPS, DoH, DoT, resolver privacy, enterprise DNS policy, content filtering, resolver bootstrap, split-horizon DNS, observability trade-off

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

DNS over HTTPS(DoH)는 DNS 질의를 HTTPS로 감싸서 보낸다.

- 중간 네트워크가 질의를 쉽게 보거나 바꾸기 어렵다
- 외부 감청과 일부 변조를 줄일 수 있다
- 평문 DNS보다 프라이버시가 좋다

하지만 운영 관점에서는 새로운 문제가 생긴다.

- DNS 기반 보안 정책이 보이지 않을 수 있다
- 기업 프록시와 필터링이 약해질 수 있다
- 장애 시 진단 경로가 더 길어질 수 있다

### Retrieval Anchors

- `DNS over HTTPS`
- `DoH`
- `DoT`
- `resolver privacy`
- `enterprise DNS policy`
- `content filtering`
- `resolver bootstrap`
- `split-horizon DNS`
- `observability trade-off`

## 깊이 들어가기

### 1. DoH가 해결하려는 문제

평문 DNS는 중간 장비가 쉽게 볼 수 있다.

- 누가 어떤 도메인을 조회했는지 노출된다
- 네트워크 사업자나 공용 Wi-Fi가 쉽게 감시할 수 있다
- 위조나 조작에 취약할 수 있다

DoH는 이 질의를 HTTPS 안으로 넣어 보호한다.

### 2. DoH와 DoT는 어떻게 다른가

- `DoH`: HTTPS 위에서 DNS를 보낸다
- `DoT`: TLS 위에서 DNS를 보낸다

둘 다 DNS 보호를 강화하지만, DoH는 일반 HTTPS 트래픽처럼 보이기 때문에 네트워크 정책 입장에서 구분이 더 어려울 수 있다.

### 3. enterprise policy가 왜 어려워지나

회사 네트워크는 종종 DNS를 정책 지점으로 쓴다.

- 악성 도메인 차단
- 내부 도메인 split-horizon
- 로그 기반 추적
- 자산 제어

DoH가 클라이언트에서 직접 외부 resolver로 나가면, 이런 제어가 우회될 수 있다.  
그래서 기업은 자체 DoH endpoint를 두거나, 허용 resolver만 쓰게 하거나, 아예 정책을 다시 설계해야 한다.

### 4. bootstrap 문제가 왜 생기나

DoH도 resolver가 필요하다.

- DoH endpoint의 도메인을 먼저 알아야 한다
- 초기 DNS는 결국 평문 DNS나 다른 신뢰 체계에 의존할 수 있다
- bootstrap 단계가 느리거나 실패하면 전체 조회가 늦어진다

즉, "DNS를 DNS로 감쌌다"는 말이 모든 초기 의존성을 없애는 뜻은 아니다.

### 5. split-horizon DNS와 충돌할 수 있다

내부망과 외부망에서 같은 이름이 다른 IP로 해석되는 환경이 있다.

- 사내 API는 내부 IP를 써야 한다
- 외부 사용자는 public IP를 써야 한다
- DoH가 외부 resolver만 보게 하면 내부 이름 해석이 꼬일 수 있다

그래서 기업 환경에서는 DoH가 단순히 "더 안전한 DNS"가 아니다.  
**정책과 이름 공간을 어떻게 나눌지**의 문제다.

## 실전 시나리오

### 시나리오 1: 보안은 좋아졌는데 장애 분석이 어려워졌다

DoH를 쓰면 resolver 로그가 분산되거나 중앙에서 보기 어려울 수 있다.

- 누가 어떤 이름을 조회했는지 추적이 어렵다
- DNS 기반 문제를 앱 네트워크 문제와 구분하기 어렵다

### 시나리오 2: 회사망에서 일부 도메인만 안 열린다

기업 DNS 정책이 DoH 때문에 우회되었거나, 반대로 허용되지 않은 DoH resolver를 쓰고 있을 수 있다.

### 시나리오 3: 모바일 환경에서는 더 잘 되는데 사내에서는 오히려 불편하다

모바일은 프라이버시 이득이 크지만, 사내 네트워크는 정책과 가시성이 더 중요할 수 있다.

### 시나리오 4: DNS는 되는데 앱이 느리다

DoH는 DNS 질의 자체를 보호할 뿐이다.

- origin latency
- TLS handshake
- CDN 경로
- app timeout

이런 다른 병목은 그대로 남는다.

## 코드로 보기

### curl로 DoH를 때리는 감각

```bash
curl 'https://dns.google/resolve?name=example.com&type=A'
```

### dig로 비교하기

```bash
dig example.com
dig @1.1.1.1 example.com
```

### 운영에서 보는 포인트

```text
- resolver latency
- failure rate
- bootstrap delay
- policy bypass risk
- logging visibility
```

### 클라이언트 정책 감각

```text
trusted resolver only
private DNS allowed
corporate resolver preferred
fallback policy defined
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 평문 DNS | 단순하고 가시성이 좋다 | 노출과 변조 위험이 있다 | 내부 통제망 |
| DoT | DNS 보호가 된다 | 정책 우회 우려가 있다 | 제한된 신뢰망 |
| DoH | 프라이버시와 우회 방지에 유리 | 기업 정책과 모니터링이 어려워질 수 있다 | 개인/모바일 중심 |

핵심은 DoH가 "좋다/나쁘다"가 아니라 **누가 DNS 정책의 소유자인가**다.

## 꼬리질문

> Q: DoH를 왜 쓰나요?
> 핵심: DNS 질의를 HTTPS로 보호해 프라이버시와 무결성을 높이기 위해서다.

> Q: 기업 네트워크에서는 왜 논란이 되나요?
> 핵심: DNS 기반 필터링과 관측, split-horizon 정책이 약해질 수 있기 때문이다.

> Q: DoH가 DNS 장애를 모두 해결하나요?
> 핵심: 아니다. resolver와 bootstrap, latency, 정책 문제는 여전히 남는다.

## 한 줄 정리

DoH는 DNS 보호를 강화하지만, 그만큼 기업 정책, 가시성, split-horizon 운영과의 충돌을 함께 설계해야 한다.
