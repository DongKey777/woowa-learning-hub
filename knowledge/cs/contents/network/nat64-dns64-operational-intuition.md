# NAT64, DNS64 Intuition

> 한 줄 요약: NAT64와 DNS64는 IPv6-only 세계에서 IPv4 서비스를 이어주는 브리지지만, DNS와 주소 변환이 함께 맞아야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [IPv4 vs IPv6 Operational Trade-offs](./ipv4-vs-ipv6-operational-tradeoffs.md)
> - [Happy Eyeballs, Dual-Stack Racing](./happy-eyeballs-dual-stack-racing.md)
> - [DNS, CDN, HTTP/2, HTTP/3](./dns-cdn-websocket-http2-http3.md)
> - [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)
> - [DNS Negative Caching, NXDOMAIN Behavior](./dns-negative-caching-nxdomain-behavior.md)

retrieval-anchor-keywords: NAT64, DNS64, IPv6-only, IPv4 reachability, address synthesis, translator, prefix, dual-stack migration, transport translation

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

NAT64와 DNS64는 IPv6-only 클라이언트가 IPv4-only 목적지에 접속할 수 있게 하는 조합이다.

- `DNS64`: IPv4 주소를 IPv6 주소처럼 합성한다
- `NAT64`: 합성된 IPv6 트래픽을 IPv4 목적지로 변환한다

이 조합은 "IPv6만으로도 IPv4 세상에 접근"하게 만든다.

### Retrieval Anchors

- `NAT64`
- `DNS64`
- `IPv6-only`
- `IPv4 reachability`
- `address synthesis`
- `translator`
- `prefix`
- `dual-stack migration`
- `transport translation`

## 깊이 들어가기

### 1. 왜 이런 장치가 필요한가

IPv6-only 환경이 늘어나면, 아직 IPv4만 있는 서비스에 접근해야 할 수 있다.

- 외부 API가 IPv4 only일 수 있다
- 레거시 DB나 관리 도구가 IPv4만 지원할 수 있다
- 클라이언트는 IPv6-only로 유지하고 싶다

### 2. DNS64는 무엇을 하는가

IPv4 전용 이름이 조회되면, DNS64는 그 IPv4를 IPv6 형태로 합성한다.

- 실제 IPv6 주소처럼 보인다
- NAT64의 prefix를 붙인다
- 클라이언트는 IPv6로 접속하는 것처럼 느낀다

### 3. NAT64는 무엇을 하는가

NAT64는 그 IPv6 트래픽을 IPv4 목적지로 번역한다.

- 주소 family를 넘나든다
- 클라이언트는 IPv6-only여도 된다
- backend는 IPv4-only여도 된다

### 4. 왜 운영이 까다로운가

DNS64와 NAT64는 함께 가야 한다.

- DNS 결과가 맞아야 한다
- prefix와 translator가 일관돼야 한다
- 일부 앱은 합성 주소를 이상하게 볼 수 있다

### 5. 언제 특히 유용한가

- 모바일 네트워크
- 신규 IPv6-only 클라이언트
- 레거시 IPv4 서비스로의 브리지

## 실전 시나리오

### 시나리오 1: IPv6-only 망에서 어떤 사이트는 되고 어떤 사이트는 안 된다

DNS64가 없는 도메인이나 NAT64 경로가 막힌 경우다.

### 시나리오 2: 연결은 되는데 특정 API만 느리다

address synthesis와 translator 경로 품질이 원인일 수 있다.

### 시나리오 3: DNS는 합성했는데 backend가 연결을 거부한다

IPv4 only backend, prefix mismatch, routing 문제를 의심한다.

## 코드로 보기

### 확인 명령

```bash
dig AAAA example.com
dig A example.com
```

### 관찰 감각

```text
IPv6-only client
-> DNS64 synthesizes AAAA
-> NAT64 translates to IPv4
```

### 체크 포인트

```text
- DNS64 prefix is consistent
- NAT64 translator is reachable
- backend IPv4 path is healthy
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| dual-stack 직접 연결 | 단순하고 자연스럽다 | IPv4/IPv6 둘 다 운영해야 한다 | 호환성 우선 |
| NAT64/DNS64 | IPv6-only 전환이 쉽다 | 번역 계층이 생긴다 | 전환기/모바일 |
| IPv4 fallback | 구현이 쉽다 | IPv6 전환 이득이 줄어든다 | 임시 대응 |

핵심은 IPv6-only로 가는 동안 **IPv4 세상을 어떻게 안전하게 이어 붙일지**다.

## 꼬리질문

> Q: DNS64와 NAT64의 차이는 무엇인가요?
> 핵심: DNS64는 주소를 합성하고 NAT64는 실제 트래픽을 번역한다.

> Q: 왜 둘이 같이 필요하나요?
> 핵심: 하나는 이름 해석, 다른 하나는 연결 전달을 담당하기 때문이다.

> Q: 운영에서 조심할 점은?
> 핵심: prefix, translator, DNS 정책이 서로 어긋나지 않게 해야 한다.

## 한 줄 정리

NAT64와 DNS64는 IPv6-only 환경에서 IPv4 서비스를 이어주는 브리지이므로, 주소 합성과 번역 경로를 같이 운영해야 한다.
