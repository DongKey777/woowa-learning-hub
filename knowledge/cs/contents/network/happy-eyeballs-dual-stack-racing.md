# Happy Eyeballs, Dual-Stack Racing

> 한 줄 요약: Happy Eyeballs는 IPv6와 IPv4를 순차적으로 시험해 느린 첫 연결을 피하는 전략이고, 핵심은 "정확한 최적"보다 "빠른 체감"이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DNS, CDN, HTTP/2, HTTP/3](./dns-cdn-websocket-http2-http3.md)
> - [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)
> - [SYN Retransmission, Handshake Timeout Behavior](./syn-retransmission-handshake-timeout.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)

retrieval-anchor-keywords: Happy Eyeballs, dual-stack, IPv6 fallback, connection racing, address selection, RFC 8305, connect latency, v4/v6 preference

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

Happy Eyeballs는 클라이언트가 IPv6와 IPv4 후보를 순차적으로 시도해, **느린 주소 체계에만 묶여 있지 않게 하는 연결 전략**이다.

- IPv6가 빨라 보이면 IPv6를 쓴다
- IPv6가 막히면 곧바로 IPv4를 시도한다
- 사용자는 "가장 올바른 주소"보다 "빨리 열린 연결"을 원한다

### Retrieval Anchors

- `Happy Eyeballs`
- `dual-stack`
- `IPv6 fallback`
- `connection racing`
- `address selection`
- `RFC 8305`
- `connect latency`
- `v4/v6 preference`

## 깊이 들어가기

### 1. 왜 순차 시도만으로는 부족한가

DNS가 A와 AAAA를 모두 반환해도, 실제 네트워크 품질은 다를 수 있다.

- IPv6 경로는 살아 있지만 손실이 높을 수 있다
- IPv4는 더 안정적일 수 있다
- 한쪽만 오래 기다리면 초기 연결이 느려진다

Happy Eyeballs는 이런 지연을 줄이기 위해 **느린 후보를 오래 붙잡지 않는다**.

### 2. racing이 왜 효과적인가

연결 수립은 첫 RTT가 중요하다.

- 첫 주소가 실패하면 다음 주소를 기다리는 동안 체감이 나빠진다
- 약간의 오버헤드를 감수하고 둘을 가깝게 race하면 실패 대기 시간을 줄일 수 있다
- 실제 성공한 연결만 쓰면 된다

즉, 총 네트워크 비용보다 **첫 연결 성공 시간**이 우선이다.

### 3. IPv6가 늘 좋지 않은 이유

IPv6는 장기적으로 중요하지만, 특정 경로에서는 다음 문제가 생긴다.

- 방화벽 정책 차이
- 잘못된 라우팅
- ISP별 품질 차이
- MTU와 tunnel overhead

이때 Happy Eyeballs는 "IPv6가 안 된다"를 빨리 판단해 IPv4로 넘어간다.

### 4. 주소 선택이 왜 운영 이슈인가

DNS는 주소를 알려줄 뿐, 품질은 보장하지 않는다.

- 같은 이름이 여러 IP를 가질 수 있다
- 클라이언트마다 resolver cache 상태가 다르다
- 어떤 클라이언트는 IPv6를 선호하고 어떤 클라이언트는 그렇지 않다

그래서 이 문제는 앱 장애처럼 보이지만 실제론 **address selection policy** 문제인 경우가 많다.

## 실전 시나리오

### 시나리오 1: 사내망에서는 느린데 집에서는 빠르다

IPv6 path나 DNS resolver 상태가 환경마다 다를 수 있다.  
Happy Eyeballs가 없으면 느린 path에 더 오래 묶인다.

### 시나리오 2: connect timeout은 아니지만 첫 바이트가 늦다

한 후보를 너무 오래 기다리면 연결 수립 자체가 늦어진다.  
이건 [SYN Retransmission, Handshake Timeout Behavior](./syn-retransmission-handshake-timeout.md)와 같이 봐야 한다.

### 시나리오 3: 모바일 환경에서 주소 전환이 자주 일어난다

Happy Eyeballs는 네트워크 품질이 흔들릴 때 체감 개선이 크다.

## 코드로 보기

### 연결 타이밍 관찰

```bash
curl -w 'dns=%{time_namelookup} connect=%{time_connect} appconnect=%{time_appconnect}\n' \
  -o /dev/null -s https://example.com
```

### 주소 확인

```bash
dig example.com A
dig example.com AAAA
```

### 운영 감각

```text
- IPv6가 실패할 때 IPv4로 빨리 넘어가는가
- 주소별 connect latency가 크게 차이 나는가
- DNS 결과보다 경로 품질 차이가 더 큰가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| IPv6 우선 | 미래 친화적이다 | 일부 경로에서 느릴 수 있다 | 품질이 안정적일 때 |
| Happy Eyeballs | 체감 연결이 빠르다 | 약간의 연결 시도 오버헤드가 있다 | dual-stack 일반 환경 |
| 단일 스택 고정 | 단순하다 | 한 스택 문제에 취약하다 | 통제된 환경 |

핵심은 주소 체계의 "정확성"보다 **사용자 체감 연결 시간**이다.

## 꼬리질문

> Q: Happy Eyeballs는 왜 필요하나요?
> 핵심: IPv6와 IPv4 중 느린 쪽에 오래 묶이지 않기 위해서다.

> Q: IPv6를 항상 우선하면 안 되나요?
> 핵심: 경로 품질이 환경마다 달라 느려질 수 있다.

> Q: racing의 비용은 무엇인가요?
> 핵심: 약간의 추가 연결 시도와 구현 복잡도가 든다.

## 한 줄 정리

Happy Eyeballs는 dual-stack 환경에서 느린 주소 하나에 묶이지 않도록 연결을 race시켜 체감 latency를 줄이는 전략이다.
