# TLS Record Sizing, Flush, Streaming Latency

> 한 줄 요약: TLS는 바이트를 그대로 흘려보내는 투명한 래퍼가 아니다. write 크기, flush 타이밍, record coalescing에 따라 first byte와 chunk cadence가 달라져 streaming latency가 크게 흔들릴 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [WebSocket Proxy Buffering, Streaming Latency](./websocket-proxy-buffering-streaming-latency.md)
> - [WebSocket Fragmentation, Frame Sizing](./websocket-fragmentation-frame-sizing.md)
> - [Nagle 알고리즘과 Delayed ACK](./nagle-delayed-ack-small-packet-latency.md)
> - [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)
> - [TLS close_notify, FIN/RST, Truncation](./tls-close-notify-fin-rst-truncation.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)

retrieval-anchor-keywords: TLS record size, flush latency, record coalescing, small writes, streaming latency, first byte delay, SSL buffer, chunk cadence, TLS framing, interactive stream

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

TLS 위에서 애플리케이션이 `write()` 한 단위와, 실제 네트워크로 나가는 TLS record 단위는 같지 않을 수 있다.

- 여러 작은 write가 하나의 record로 모일 수 있다
- 큰 payload는 여러 record로 쪼개질 수 있다
- flush가 늦으면 first byte가 밀린다

그래서 streaming 경로에서는 "앱이 썼다"와 "클라이언트가 받는다" 사이에 TLS record 레이어가 하나 더 있다고 봐야 한다.

### Retrieval Anchors

- `TLS record size`
- `flush latency`
- `record coalescing`
- `small writes`
- `streaming latency`
- `first byte delay`
- `SSL buffer`
- `chunk cadence`

## 깊이 들어가기

### 1. TLS record는 메시지 경계와 다르다

애플리케이션 메시지, HTTP chunk, WebSocket frame, gRPC message는 각자 자기 경계를 가진다.  
TLS record는 그 아래에서 별도로 잘린다.

즉:

- 작은 앱 메시지 여러 개가 하나의 TLS record가 될 수 있다
- 하나의 큰 메시지가 여러 record가 될 수 있다
- TLS record 경계는 앱 프로토콜 경계와 일치한다고 기대하면 안 된다

### 2. 작은 write가 항상 low-latency인 것도 아니다

실시간성을 위해 작은 단위로 자주 쓰고 싶어질 수 있다.  
하지만 너무 작은 write는:

- syscall overhead 증가
- TLS 암복호화 호출 증가
- packet/record overhead 증가
- Nagle/delayed ACK와 상호작용

를 부를 수 있다.

즉 "작게 자주"와 "크게 모아서" 사이에서 서비스 특성에 맞는 균형이 필요하다.

### 3. 반대로 너무 크게 모으면 first byte와 chunk cadence가 나빠진다

buffering과 coalescing이 과하면:

- first byte가 늦다
- 중간 chunk가 묶여서 나온다
- heartbeat나 progress update가 늦게 보인다

이건 HTTP streaming, SSE, WebSocket, gRPC streaming에서 특히 체감된다.

### 4. proxy TLS termination 지점이 많을수록 원인 추적이 어렵다

예를 들어:

- app -> sidecar TLS
- sidecar -> edge proxy TLS
- edge proxy -> client TLS

각 홉의 write/flush 정책이 다를 수 있다.

- app은 자주 flush한다
- sidecar는 buffer를 모은다
- edge는 response buffering을 또 한다

이 경우 사용자는 "서버가 늦게 보냈다"고 느끼지만, 실제로는 중간 TLS termination hop이 cadence를 바꾸고 있을 수 있다.

### 5. TTFB와 TTLB 해석에도 영향을 준다

phase timing 관점에서 보면:

- TLS handshake는 빠르다
- app도 응답을 빨리 만든다
- 그런데 first byte나 body cadence가 이상하게 늦다

이때 TLS record coalescing, flush 지연, proxy buffering을 같이 봐야 한다.

### 6. streaming과 bulk transfer의 최적점은 다르다

bulk transfer에서는 큰 record와 효율이 중요할 수 있다.

- throughput
- CPU 효율
- packet overhead 감소

interactive streaming에서는 다르다.

- first byte latency
- heartbeat 지연
- progress update cadence
- slow consumer 반응 속도

즉 같은 TLS stack 설정이 모든 endpoint에 정답은 아니다.

## 실전 시나리오

### 시나리오 1: SSE는 연결되는데 이벤트가 묶여서 보인다

가능한 원인:

- proxy buffering
- TLS record coalescing
- app flush 주기 문제

### 시나리오 2: WebSocket ping/pong은 되는데 payload만 늦다

control frame은 작고 주기적이지만, data payload는 큰 write + buffer 경로를 타며 늦게 보일 수 있다.

### 시나리오 3: TLS termination을 프록시로 옮긴 뒤 TTFB가 흔들린다

핸드셰이크가 아니라 record flush/buffering 정책이 바뀐 것일 수 있다.

### 시나리오 4: 대용량 응답은 빨라졌는데 실시간 진행률 UI는 나빠졌다

bulk 효율 최적화가 interactive chunk cadence를 희생한 패턴일 수 있다.

## 코드로 보기

### phase timing 감각

```bash
curl -N -w 'ttfb=%{time_starttransfer} total=%{time_total}\n' https://api.example.com/stream
```

### 관찰 포인트

```text
- app write 이후 실제 first byte까지의 지연
- chunk 간격이 규칙적인가, 묶여서 오는가
- TLS termination hop마다 buffering/flush 정책이 다른가
- bulk endpoint와 interactive endpoint를 같은 정책으로 다루는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 큰 record / aggressive coalescing | throughput과 CPU 효율이 좋다 | first byte와 chunk cadence가 나빠질 수 있다 | bulk transfer |
| 작은 write / 빠른 flush | interactive latency가 좋다 | overhead와 CPU 비용이 커질 수 있다 | SSE, progress stream |
| endpoint별 정책 분리 | 용도에 맞는 최적화가 가능하다 | 운영 복잡도가 늘어난다 | mixed workload |
| 단일 공통 정책 | 단순하다 | 일부 워크로드엔 과최적/과악화가 된다 | 작은 단일 서비스 |

핵심은 TLS를 투명한 파이프처럼 보지 않고 **record와 flush가 latency를 만드는 계층**으로 보는 것이다.

## 꼬리질문

> Q: 앱이 flush했다고 바로 클라이언트가 받나요?
> 핵심: 아니다. TLS record 생성, proxy buffering, 커널 전송이 사이에 더 있다.

> Q: 작은 write를 많이 하면 항상 실시간성이 좋아지나요?
> 핵심: 아니다. overhead와 coalescing 상호작용 때문에 오히려 비효율적일 수 있다.

> Q: bulk transfer와 streaming endpoint를 같은 TLS/flush 정책으로 다뤄도 되나요?
> 핵심: 보통은 아니다. throughput 최적화와 interactive latency 최적화는 다를 수 있다.

## 한 줄 정리

TLS record와 flush 정책은 handshake 이후에도 latency를 만들기 때문에, streaming 경로가 느릴 때는 앱 write와 proxy buffering 사이에 있는 TLS framing 계층까지 같이 봐야 한다.
