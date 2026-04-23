# HTTP/2 Flow Control, WINDOW_UPDATE, Stall

> 한 줄 요약: HTTP/2 멀티플렉싱이 있어도 `WINDOW_UPDATE`가 늦거나 connection window가 고갈되면 stream은 조용히 멈추고, 운영자는 이를 네트워크 불안정으로 오해하기 쉽다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [HTTP/2 Upload Early Reject, RST_STREAM, Flow-Control Cleanup](./http2-upload-early-reject-rst-stream-flow-control-cleanup.md)
> - [gRPC Deadlines, Cancellation Propagation](./grpc-deadlines-cancellation-propagation.md)
> - [HTTP/2, HTTP/3 Connection Reuse, Coalescing](./http2-http3-connection-reuse-coalescing.md)
> - [HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation](./http2-max-concurrent-streams-pending-queue-saturation.md)
> - [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)
> - [WebSocket Proxy Buffering, Streaming Latency](./websocket-proxy-buffering-streaming-latency.md)
> - [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)

retrieval-anchor-keywords: HTTP/2 flow control, WINDOW_UPDATE, connection window, stream window, SETTINGS_INITIAL_WINDOW_SIZE, SETTINGS_MAX_CONCURRENT_STREAMS, stalled stream, gRPC streaming, backpressure, receive window, discarded DATA after reset, RST_STREAM flow control, upload reject connection window

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

HTTP/2에는 TCP와 별도의 flow control이 있다.

- `stream window`: 각 stream마다 얼마를 더 보낼 수 있는지
- `connection window`: 해당 H2 연결 전체로 얼마를 더 보낼 수 있는지
- `WINDOW_UPDATE`: 수신자가 "이제 더 보내도 된다"고 credit를 돌려주는 프레임

즉, 패킷 손실이 없어도 **수신 측이 credit를 충분히 안 돌려주면 송신은 멈춘다**.

### Retrieval Anchors

- `HTTP/2 flow control`
- `WINDOW_UPDATE`
- `connection window`
- `stream window`
- `SETTINGS_INITIAL_WINDOW_SIZE`
- `SETTINGS_MAX_CONCURRENT_STREAMS`
- `stalled stream`
- `gRPC streaming`

## 깊이 들어가기

### 1. TCP 혼잡 제어와 HTTP/2 flow control은 다른 문제다

둘 다 "얼마나 보내도 되는가"를 다루지만 기준이 다르다.

- TCP는 네트워크 경로와 수신 버퍼를 본다
- HTTP/2는 애플리케이션 계층에서 stream별 credit를 본다

그래서 RTT와 손실률이 안정적이어도 H2 애플리케이션이 천천히 읽으면 stall이 생길 수 있다.

### 2. connection window와 stream window는 서로 막을 수 있다

자주 헷갈리는 지점이다.

- 특정 stream window가 바닥나면 그 stream만 멈춘다
- connection window가 바닥나면 같은 연결 위의 다른 stream도 함께 막힌다

그래서 큰 streaming response 하나가 작은 unary RPC까지 늦출 수 있다.

- TCP HOL blocking이 아니어도
- HTTP/2 connection-level credit starvation만으로
- shared connection latency가 나빠질 수 있다

large upload early reject도 여기에 걸린다.  
`RST_STREAM`으로 한 stream을 끊었더라도 reset 전에 이미 날아오던 DATA는 connection window를 잠깐 더 점유할 수 있어서, discard/credit accounting이 느리면 sibling stream이 같이 stall된다.

### 3. `SETTINGS_MAX_CONCURRENT_STREAMS`와 flow control은 다르다

둘 다 throughput을 줄일 수 있지만 병목 양상이 다르다.

- concurrent streams 제한은 "몇 개를 동시에 열 수 있는가"
- flow control window는 "열린 stream에서 얼마나 더 보낼 수 있는가"

증상도 다르다.

- concurrency limit이면 새 stream 생성이 막히거나 대기한다
- window starvation이면 stream은 열려 있는데 데이터가 안 흐른다

이 차이는 [HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation](./http2-max-concurrent-streams-pending-queue-saturation.md)와 같이 보면 더 분명해진다.

### 4. `WINDOW_UPDATE`가 늦는 이유는 보통 앱 쪽 backpressure다

운영에서 stall 원인은 네트워크보다 아래가 아닌 경우가 많다.

- 수신 애플리케이션이 메시지를 천천히 소비한다
- proxy가 body를 버퍼링하며 upstream read를 늦춘다
- 압축 해제나 디코딩 단계가 병목이다
- GC pause나 event loop stall이 credit 반환을 늦춘다

이때 송신자는 그냥 "상대가 아직 읽지 않았다"로 보게 된다.

### 5. gRPC streaming에서 특히 잘 드러난다

gRPC는 H2 위에서 streaming을 많이 쓴다.

- client streaming
- server streaming
- bidi streaming

한 stream이 오래 살아 있으면 window tuning, consumer 속도, max message size가 더 중요해진다.

특히 큰 메시지를 드물게 보내는 것보다, 적당한 chunk와 빠른 소비가 흐름 제어 측면에서 더 건강할 때가 많다.

### 6. stall은 timeout 문서와 함께 봐야 한다

flow control stall이 있으면 지표상 다음처럼 보일 수 있다.

- connect는 빠르다
- TLS handshake도 빠르다
- first byte는 왔다
- 이후 read timeout이나 deadline 초과가 난다

이 패턴은 단순 네트워크 손실보다 H2 credit starvation을 의심해 볼 신호다.

## 실전 시나리오

### 시나리오 1: 큰 server-streaming 하나 뒤에 작은 unary RPC들이 같이 느려진다

가능한 원인:

- 같은 H2 connection의 connection window가 바닥났다
- 작은 RPC는 stream이 작아도 shared connection credit를 기다린다

### 시나리오 2: 패킷 손실은 없는데 gRPC deadline 초과가 늘어난다

이 경우는 receiver가 천천히 읽고 있을 수 있다.

- 애플리케이션 consumer가 느리다
- proxy buffering이 끼어 있다
- downstream가 메시지를 너무 크게 묶어 보낸다

### 시나리오 3: `SETTINGS_MAX_CONCURRENT_STREAMS`를 늘렸는데도 throughput이 안 오른다

stream 개수는 늘었지만 window 크기나 receiver consume rate가 그대로라면 병목은 바뀌지 않는다.

### 시나리오 4: HTTP/3로 바꿨는데 일부 stall은 남아 있다

TCP HOL blocking은 줄어도, 애플리케이션 차원의 backpressure와 stream credit 문제까지 자동으로 사라지지는 않는다.

## 코드로 보기

### HTTP/2 프레임 흐름 감각 보기

```bash
nghttp -nv https://api.example.com
```

### stall을 분류할 때 보는 질문

```text
- stream은 열렸는데 DATA frame이 안 오는가
- WINDOW_UPDATE가 늦거나 적게 오는가
- connection window와 stream window 중 어느 쪽이 먼저 바닥나는가
- proxy buffering 또는 app consumer가 credit 반환을 늦추는가
```

### 운영 메트릭 예시

```text
- active streams
- queued streams waiting for MAX_CONCURRENT_STREAMS
- connection window remaining
- stream window remaining
- read timeout / deadline exceeded ratio
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 큰 initial window | 고대역폭 전송이 부드럽다 | 느린 소비자 앞에서 메모리 압력이 커질 수 있다 | 대용량 streaming |
| 작은 initial window | backpressure가 빠르게 걸린다 | throughput이 낮아질 수 있다 | 보호 우선 환경 |
| long stream 전용 연결 분리 | unary RPC 영향이 줄어든다 | 연결 수가 늘고 운영이 복잡해진다 | mixed workload |
| proxy buffering 최소화 | credit 반환이 빨라질 수 있다 | 느린 클라이언트 보호가 약해진다 | low-latency streaming |

핵심은 H2 stall을 "그냥 네트워크가 느리다"가 아니라 **credit가 어디서 막히는가**로 해석하는 것이다.

## 꼬리질문

> Q: HTTP/2 flow control과 TCP flow control의 차이는 무엇인가요?
> 핵심: TCP는 전송 경로와 수신 버퍼, HTTP/2는 stream/connection 단위 애플리케이션 credit를 다룬다.

> Q: `SETTINGS_MAX_CONCURRENT_STREAMS`와 `WINDOW_UPDATE` 부족은 어떻게 다른가요?
> 핵심: 하나는 stream 개수 제한, 다른 하나는 열린 stream의 전송량 제한이다.

> Q: 패킷 손실이 없는데도 gRPC deadline이 넘을 수 있나요?
> 핵심: 가능하다. receiver consume 지연과 H2 connection window 고갈만으로도 stall이 생긴다.

## 한 줄 정리

HTTP/2에서 stall은 손실뿐 아니라 `WINDOW_UPDATE`와 credit 반환 지연으로도 생기므로, shared connection 위의 작은 RPC가 왜 같이 느려지는지 flow control 관점으로 봐야 한다.
