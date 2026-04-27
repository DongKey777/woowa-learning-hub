# HTTP/3, QUIC Practical Trade-offs

> 한 줄 요약: HTTP/3는 TCP HOL blocking과 연결 지연이 실제 병목일 때 강력하지만, UDP 위 운영과 관측 비용을 같이 감수해야 한다.

**난이도: 🔴 Advanced**

> 이 문서는 QUIC 운영 판단을 위한 **advanced deep dive**다. beginner라면 여기서 바로 시작하지 말고, 먼저 아래 safe-entry 문서로 진입한 뒤 다시 오는 편이 이해 비용이 낮다.
>
> | 지금 상태 | 먼저 읽을 문서 | 이 문서로 돌아오는 타이밍 |
> |---|---|---|
> | H1/H2/H3 큰 그림부터 헷갈린다 | [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) | "`H3가 왜 QUIC까지 끌고 오지?`"가 궁금해졌을 때 |
> | 브라우저가 왜 H3를 쓰거나 포기하는지 먼저 보고 싶다 | [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md) | `Alt-Svc`, `fallback`, UDP 차단 감각을 잡은 뒤 |
> | "`HTTP/3가 항상 더 빠르나?`"부터 확인하고 싶다 | 이 문서 | 성능 이득과 운영 비용을 같이 비교하려는 지금 |

> 관련 문서:
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [QUIC Connection Migration, Path Change](./quic-connection-migration-path-change.md)
> - [UDP Fragmentation, QUIC Packetization](./udp-fragmentation-quic-packetization.md)
> - [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)
> - [ECN, Congestion Signal, Tail Latency](./ecn-congestion-signal-tail-latency.md)
> - [BBR vs CUBIC Congestion Intuition](./bbr-vs-cubic-congestion-intuition.md)
> - [Happy Eyeballs, Dual-Stack Racing](./happy-eyeballs-dual-stack-racing.md)
> - [TLS Session Resumption, 0-RTT, Replay Risk](./tls-session-resumption-0rtt-replay-risk.md)
> - [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)
> - [h2c, Cleartext Upgrade, Prior Knowledge, Routing](./h2c-cleartext-upgrade-prior-knowledge-routing.md)

retrieval-anchor-keywords: HTTP/3, QUIC, UDP, connection migration, HOL blocking, packet loss, latency, qpack, path validation, mobile network

<details>
<summary>Table of Contents</summary>

- [시작 전 30초 안전 가이드](#시작-전-30초-안전-가이드)
- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 시작 전 30초 안전 가이드

이 문서는 "HTTP/3가 좋다/나쁘다"를 판정하는 글이 아니라, **어떤 조건에서 이득이 보이고 어떤 비용이 따라오는지**를 나누는 글이다.

| 먼저 답할 질문 | 초보자용 짧은 답 | 더 궁금하면 |
|---|---|---|
| HTTP/3가 왜 등장했나 | TCP 기반 대기 전파를 더 줄이려는 방향이다 | [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md) |
| HTTP/3가 항상 더 빠른가 | 아니다. UDP 경로와 운영 환경이 맞아야 한다 | 이 문서 `왜 "항상 더 빠른" 게 아닌가` |
| 이 문서가 너무 깊게 느껴지면? | 먼저 beginner 비교/선택 문서로 돌아간다 | 위 safe-entry 표 참고 |

## 핵심 개념

HTTP/3는 HTTP를 QUIC 위로 옮긴 것이다.

- TCP 대신 UDP를 사용한다
- TLS와 transport가 더 강하게 통합된다
- packet loss와 path change에 더 유연하다
- 그러나 관측과 중간장비 호환성 비용이 있다

### Retrieval Anchors

- `HTTP/3`
- `QUIC`
- `UDP`
- `connection migration`
- `HOL blocking`
- `packet loss`
- `latency`
- `qpack`
- `path validation`
- `mobile network`

## 깊이 들어가기

### 1. HTTP/3가 주는 이점

HTTP/3는 TCP HOL blocking을 피하려고 설계됐다.

- 한 스트림의 loss가 다른 스트림에 덜 영향
- 연결 수립이 빨라질 수 있음
- 모바일/무선 환경에서 체감이 좋을 수 있음

### 2. 왜 "항상 더 빠른" 게 아닌가

운영 환경이 맞아야 한다.

- UDP가 막힐 수 있다
- middlebox가 QUIC을 잘 이해하지 못할 수 있다
- tracing과 packet capture가 복잡해진다

### 3. packet loss와 왜 같이 봐야 하나

HTTP/3의 장점은 loss가 있는 환경에서 더 드러난다.

- 손실이 적으면 차이가 작을 수 있다
- 손실과 지터가 큰 네트워크에서 이점이 커진다
- path validation과 migration이 살아난다

이 부분은 [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md), [UDP Fragmentation, QUIC Packetization](./udp-fragmentation-quic-packetization.md)와 연결된다.

### 4. BBR/ECN과의 관계

혼잡 제어와 packet pacing이 좋아야 QUIC 이점이 잘 드러난다.

- BBR은 pacing 감각과 잘 맞을 수 있다
- ECN은 손실 전에 혼잡을 알릴 수 있다
- 반대로 큐잉이 심하면 체감이 나빠진다

### 5. TLS와 연결 재개의 영향

HTTP/3는 TLS 1.3과 함께 움직인다.

- handshake 비용이 줄 수 있다
- 0-RTT를 쓸 수 있지만 replay 위험이 있다
- 연결 migration과 resumption을 함께 설계해야 한다

## 실전 시나리오

### 시나리오 1: 모바일에서만 HTTP/3가 확실히 좋다

무선 네트워크의 손실과 이동성이 원인일 수 있다.

### 시나리오 2: HTTP/2는 안정적인데 HTTP/3만 일부 네트워크에서 실패한다

UDP 차단, path MTU, middlebox 문제가 원인일 수 있다.

### 시나리오 3: 브라우저는 빠른데 운영자가 원인 추적을 못 한다

QUIC 계층의 관측 지점이 더 적기 때문이다.

### 시나리오 4: 연결은 이어지는데 p99가 흔들린다

경로 전환, packet loss, queueing 이슈를 봐야 한다.

## 코드로 보기

### 지원 여부 확인

```bash
curl --http3 -I https://example.com
nghttp -nv https://example.com
```

### 네트워크 관찰

```bash
tcpdump -i any udp port 443
ss -tunap
```

### 체크 포인트

```text
- UDP path allowed?
- path validation successful?
- packet loss under load?
- fallback to HTTP/2 works?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| HTTP/2 | 호환성이 좋다 | TCP HOL blocking이 남는다 | 일반적인 서버 환경 |
| HTTP/3 | 손실/이동성 환경에 강하다 | 관측과 중간장비 복잡도가 높다 | 모바일/edge-heavy |
| 혼합 운영 | 점진 전환 가능 | 운영 이중화가 필요하다 | 대규모 서비스 |

핵심은 HTTP/3가 최신이라서가 아니라 **우리 네트워크의 손실과 이동성 특성에 맞는가**다.

## 꼬리질문

> Q: HTTP/3는 왜 필요한가요?
> 핵심: TCP HOL blocking과 연결 지연을 줄이기 위해서다.

> Q: 왜 운영 비용이 늘어나나요?
> 핵심: UDP 호환성, 관측, middlebox 정책을 다시 봐야 하기 때문이다.

> Q: HTTP/3가 항상 더 좋은가요?
> 핵심: 아니다. 환경에 따라 HTTP/2가 더 안정적일 수 있다.

## 한 줄 정리

HTTP/3는 손실과 이동성이 큰 환경에서 큰 이득을 주지만, UDP 운영과 관측 복잡도를 감수할 준비가 있을 때 선택해야 한다.
