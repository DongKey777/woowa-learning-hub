# TCP Zero Window, Persist Probe, Receiver Backpressure

> 한 줄 요약: TCP 전송이 멈췄다고 해서 항상 혼잡인 것은 아니다. 수신 측이 더 못 받겠다고 `rwnd=0`을 광고하면 sender는 `persist probe`만 보내며 멈추고, 운영자는 이를 네트워크 장애나 write timeout 문제로 오해하기 쉽다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TCP 혼잡 제어](./tcp-congestion-control.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md)
> - [WebSocket Heartbeat, Backpressure, Reconnect](./websocket-heartbeat-backpressure-reconnect.md)
> - [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)

retrieval-anchor-keywords: TCP zero window, persist probe, receiver window, rwnd, receiver backpressure, write stall, app not reading socket, slow consumer, flow control, zero window probe

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

TCP sender가 더 보내지 못하는 이유는 크게 둘이다.

- 네트워크 혼잡 때문에 `cwnd`가 제한된다
- 수신 측이 받을 공간이 없어 `rwnd`를 줄인다

`rwnd`가 0이 되면 sender는 정상 데이터 전송을 멈추고, 가끔 `persist probe`를 보내 창이 다시 열렸는지 확인한다.

즉, 이 현상은 **패킷 손실이 없어도 생기는 receiver-side stall**이다.

### Retrieval Anchors

- `TCP zero window`
- `persist probe`
- `receiver window`
- `rwnd`
- `receiver backpressure`
- `write stall`
- `slow consumer`
- `flow control`

## 깊이 들어가기

### 1. `min(cwnd, rwnd)`에서 무엇이 병목인지 구분해야 한다

TCP는 대체로 다음 둘 중 더 작은 값만큼만 보낼 수 있다.

- `cwnd`: 네트워크 혼잡을 고려한 송신 상한
- `rwnd`: 수신자가 받을 수 있다고 광고한 상한

실무에서는 둘 다 그냥 "느리다"로 뭉개기 쉽다.  
하지만 해석은 다르다.

- `cwnd` 병목: 패킷 손실, RTT 증가, queue buildup 쪽을 본다
- `rwnd` 병목: 상대 프로세스가 못 읽는지, recv buffer가 찼는지 본다

### 2. zero window는 보통 "상대 앱이 못 읽는 상태"다

수신 측 커널 recv buffer가 찬다는 것은 대개 상위 애플리케이션이 제때 읽지 못한다는 뜻이다.

흔한 원인:

- 애플리케이션 consumer가 느리다
- 압축 해제, 암복호화, 디코딩이 병목이다
- proxy가 buffering하며 upstream read를 늦춘다
- GC pause나 event loop stall이 길다
- 디스크 flush나 downstream queue 포화 때문에 read loop가 멈춘다

즉 "네트워크가 막혔다"보다 **상대가 못 먹고 있다**에 가깝다.

### 3. persist probe는 deadlock을 피하기 위한 장치다

`rwnd=0`이라고 해서 sender가 영원히 조용히 있으면 안 된다.

- window reopen 알림이 유실될 수 있다
- 양쪽이 서로 기다리며 멈출 수 있다

그래서 sender는 작은 probe를 보내며 "이제 창이 열렸나?"를 확인한다.

이때 보이는 현상:

- 연결은 살아 있는 것처럼 보인다
- 소량의 트래픽만 가끔 흐른다
- 실제 payload throughput은 거의 0에 가깝다

### 4. zero window stall은 한 방향만 막히는 경우가 많다

양방향 전체가 죽는 것이 아니라, 주로 한 방향 데이터 흐름만 막힌다.

- upload만 멈추고 response는 아직 올 수 있다
- server streaming만 막히고 control traffic은 오갈 수 있다
- WebSocket heartbeat는 되는데 실제 payload는 늦을 수 있다

그래서 "ping은 되는데 업로드가 멈춘다" 같은 증상이 생긴다.

### 5. write timeout과 backpressure 문서와 함께 봐야 한다

zero window stall은 애플리케이션 입장에서 다음처럼 드러난다.

- write syscall이 오래 block된다
- write timeout이 난다
- flush가 안 끝난다
- 상위 스트리밍 프레임워크는 backpressure로 보인다

대용량 업로드, SSE, WebSocket, gRPC streaming에서 특히 헷갈린다.  
TCP 수준 zero window와 HTTP/2 flow control stall은 서로 다른 계층이지만 사용자 증상은 비슷할 수 있다.

### 6. proxy와 TLS termination이 끼면 원인 추적이 더 어려워진다

예를 들어:

- client는 edge proxy에 빠르게 쓴다
- edge proxy는 backend가 못 읽어 zero window를 받는다
- client는 proxy buffering 때문에 바로 문제를 못 본다

또는 TLS termination proxy가 record를 모아 처리하다가 app read를 늦추면, 실제 병목은 app인데 transport는 zero window로만 보일 수 있다.

## 실전 시나리오

### 시나리오 1: 파일 업로드가 중간에서 멈춘 듯 보이는데 패킷 손실은 거의 없다

가능한 원인:

- upstream이 body를 천천히 읽는다
- antivirus / decompression / object store write가 느리다
- proxy request buffering을 껐더니 app이 직접 slow client를 맞았다

### 시나리오 2: WebSocket ping/pong은 되는데 큰 메시지만 늦다

control frame은 오가지만 payload 소비가 느려 connection-level zero window 또는 app-level queue 포화가 생길 수 있다.

### 시나리오 3: gRPC streaming에서 `deadline exceeded`가 뜨는데 손실은 없다

receiver가 메시지를 충분히 빨리 consume하지 못해 zero window나 flow-control starvation이 숨어 있을 수 있다.

### 시나리오 4: CPU는 낮은데 write timeout이 늘어난다

네트워크 카드나 대역폭보다, 상대 서비스의 read loop 또는 proxy buffering을 먼저 의심할 만한 패턴이다.

## 코드로 보기

### 연결 상태 힌트 보기

```bash
ss -ti dst 203.0.113.10
```

### 패킷 캡처에서 zero window 흔적 보기

```bash
tcpdump -nnvv -i eth0 host 203.0.113.10 and tcp
```

### 관찰 포인트

```text
- packet loss는 낮은데 throughput만 멈추는가
- sender write timeout과 receiver app queue saturation이 같은 시점에 생기는가
- zero window / persist probe가 반복되는가
- proxy buffering 또는 app read loop stall이 있는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 큰 recv buffer | 순간 burst를 더 흡수한다 | 느린 소비자를 더 오래 숨길 수 있다 | 짧은 burst가 큰 경로 |
| 엄격한 slow-consumer cutoff | 전체 시스템을 보호한다 | 일부 연결을 더 빨리 끊게 된다 | broadcast, streaming |
| proxy buffering 사용 | 느린 client를 backend에서 분리한다 | 병목 위치가 더 늦게 드러난다 | 일반 HTTP 업로드 |
| buffering 최소화 | backpressure를 빨리 드러낸다 | app이 느린 소비자를 직접 감당해야 한다 | low-latency streaming |

핵심은 전송 정체를 무조건 혼잡으로 해석하지 않고 **receiver가 못 읽는 stall인지** 따로 보는 것이다.

## 꼬리질문

> Q: TCP zero window는 무엇을 의미하나요?
> 핵심: 수신 측이 더 이상 받을 공간이 없다고 광고해 sender가 정상 데이터 전송을 멈춘 상태다.

> Q: persist probe는 왜 필요한가요?
> 핵심: window reopen 신호 유실로 양쪽이 영원히 멈추는 것을 막기 위해서다.

> Q: packet loss가 거의 없는데 write timeout이 날 수 있나요?
> 핵심: 가능하다. receiver가 못 읽어 `rwnd=0`이 되면 sender는 막힐 수 있다.

## 한 줄 정리

TCP zero window stall은 네트워크 혼잡이 아니라 receiver-side backpressure일 수 있으므로, throughput 정체를 볼 때 `cwnd`뿐 아니라 `rwnd`와 persist probe도 함께 봐야 한다.
