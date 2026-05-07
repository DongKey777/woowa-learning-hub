---
schema_version: 3
title: "Nagle Algorithm and Delayed ACK Small Packet Latency"
concept_id: network/nagle-delayed-ack-small-packet-latency
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- tcp-small-packet-latency
- nagle-delayed-ack
- streaming-flush
aliases:
- Nagle algorithm
- delayed ACK
- TCP_NODELAY
- small packet latency
- request response stall
- TCP corking
- interactive traffic latency
symptoms:
- 작은 RPC나 제어 메시지가 대역폭은 낮은데 왕복 지연만 크게 늘어난다
- Nagle과 delayed ACK가 서로 기다리는 stall을 네트워크 혼잡으로 오해한다
- TCP_NODELAY를 켜면 항상 빨라진다고 단정한다
- TLS record나 response compression buffering과 TCP small write 문제를 분리하지 못한다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/tcp-congestion-control
- network/request-timing-decomposition
next_docs:
- network/tls-record-sizing-flush-streaming-latency
- network/http-response-compression-buffering-streaming-tradeoffs
- network/http2-multiplexing-hol-blocking
- network/timeout-types-connect-read-write
linked_paths:
- contents/network/tcp-congestion-control.md
- contents/network/http2-multiplexing-hol-blocking.md
- contents/network/timeout-types-connect-read-write.md
- contents/network/mtu-fragmentation-mss-blackhole.md
- contents/network/fin-rst-half-close-eof-semantics.md
- contents/network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md
- contents/network/tls-record-sizing-flush-streaming-latency.md
- contents/network/http-response-compression-buffering-streaming-tradeoffs.md
confusable_with:
- network/tcp-congestion-control
- network/http2-multiplexing-hol-blocking
- network/tls-record-sizing-flush-streaming-latency
- network/http-response-compression-buffering-streaming-tradeoffs
forbidden_neighbors: []
expected_queries:
- "Nagle 알고리즘과 delayed ACK가 만나면 왜 작은 요청이 느려져?"
- "TCP_NODELAY를 켜면 small packet latency가 항상 해결돼?"
- "작은 RPC가 대역폭은 안 쓰는데 RTT가 늘어나는 이유를 설명해줘"
- "Nagle delayed ACK stall과 TCP congestion control은 어떻게 달라?"
- "TLS record flush와 HTTP compression buffering까지 같이 봐야 하는 이유는?"
contextual_chunk_prefix: |
  이 문서는 Nagle algorithm, delayed ACK, TCP_NODELAY, small packet latency,
  TCP corking, TLS record flush와 response buffering의 상호작용을 다루는
  advanced playbook이다.
---
# Nagle 알고리즘과 Delayed ACK

> 한 줄 요약: 작은 패킷을 아끼려는 Nagle과 ACK를 늦추는 Delayed ACK가 만나면, 대역폭은 안 써도 지연은 크게 늘 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TCP 혼잡 제어](./tcp-congestion-control.md)
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [MTU, Fragmentation, MSS, Blackhole](./mtu-fragmentation-mss-blackhole.md)
> - [FIN, RST, Half-Close, EOF](./fin-rst-half-close-eof-semantics.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
> - [TLS Record Sizing, Flush, Streaming Latency](./tls-record-sizing-flush-streaming-latency.md)
> - [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)

retrieval-anchor-keywords: Nagle algorithm, delayed ACK, TCP_NODELAY, small packet latency, coalescing, interactive traffic, request-response stall, TCP corking

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

TCP는 무작정 작은 세그먼트를 계속 보내면 비효율적이기 때문에, 소량의 데이터를 묶어서 보내려는 장치를 둔다.

- `Nagle algorithm`: 작은 보내기 요청을 합쳐서 더 큰 세그먼트로 만든다
- `Delayed ACK`: 수신 측이 ACK를 바로 보내지 않고 잠깐 기다린다
- `TCP_NODELAY`: Nagle을 끄고 바로 보내게 만든다

문제는 이 둘이 같이 있을 때다.

작은 요청-응답이 반복되는 패턴에서 sender는 "ACK 오면 보내자"고 기다리고, receiver는 "데이터가 조금 더 올지 보자"고 기다리면서, **서로를 기다리는 잠복 시간**이 생긴다.

### Retrieval Anchors

- `Nagle algorithm`
- `delayed ACK`
- `TCP_NODELAY`
- `small packet latency`
- `coalescing`
- `interactive traffic`
- `request-response stall`
- `TCP corking`

## 깊이 들어가기

### 1. Nagle이 왜 생겼나

작은 패킷을 너무 자주 보내면 아래 비용이 생긴다.

- 헤더 오버헤드가 커진다
- 네트워크가 잡음처럼 바빠진다
- 커널과 NIC 처리량이 불필요하게 늘어난다

그래서 Nagle은 기본적으로 이런 규칙으로 동작한다.

- 아직 ACK를 못 받은 미확인 데이터가 있으면
- 새로 생긴 작은 쓰기 데이터를 잠시 모은다
- 어느 정도 묶이거나 ACK가 오면 보낸다

대역폭 효율은 좋아지지만, 지연 민감 트래픽에는 불리해질 수 있다.

### 2. Delayed ACK가 왜 생겼나

수신 측도 매 세그먼트마다 ACK를 보내면 부담이 크다.

- ACK를 하나씩 즉시 보내지 않아도 된다
- 곧바로 보낼 데이터가 있으면 데이터와 ACK를 함께 보낼 수 있다
- 짧은 지연을 두면 불필요한 ACK 트래픽을 줄일 수 있다

하지만 이 "조금 기다리기"가 Nagle과 만나면 문제가 된다.

### 3. 왜 둘이 만나면 stall이 생기나

전형적인 흐름은 이렇다.

1. 클라이언트가 작은 request를 보낸다
2. 서버는 응답을 조금만 만들었다
3. 서버는 Nagle 때문에 더 쌓이길 기다린다
4. 클라이언트는 delayed ACK 때문에 ACK를 늦춘다
5. 양쪽이 서로를 기다린다

이게 바로 작은 RPC, 채팅, 제어 메시지, 폼 제출처럼 **짧고 자주 왕복하는 통신**에서 체감 지연을 만드는 원인이다.

### 4. TCP_NODELAY가 만능은 아니다

`TCP_NODELAY`를 켜면 Nagle은 끌 수 있다.

- 작은 패킷을 더 빨리 보낼 수 있다
- interactive latency가 줄 수 있다

하지만 이것만으로는 끝이 아니다.

- delayed ACK는 여전히 존재할 수 있다
- 애플리케이션이 너무 자주 write하면 packet burst가 생길 수 있다
- 프록시와 TLS 레코드가 다른 곳에서 다시 묶을 수 있다

즉, `TCP_NODELAY`는 "지연을 줄일 가능성"이지 "무조건 빨라짐"이 아니다.

### 5. 언제 좋은가, 언제 나쁜가

좋은 경우:

- CLI 상호작용
- 채팅/메신저
- 짧은 control plane 메시지
- 낮은 지연이 중요한 RPC

나쁜 경우:

- 대용량 전송
- throughput이 더 중요한 배치
- 이미 상위 계층에서 충분히 배치하는 경우

패킷을 덜 보내는 게 항상 좋은 것이 아니라, **어느 레벨에서 묶을지**가 중요하다.
특히 TLS record coalescing이나 응답 압축이 함께 있으면 작은 write의 체감은 [TLS Record Sizing, Flush, Streaming Latency](./tls-record-sizing-flush-streaming-latency.md), [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)와 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 작은 REST 호출이 이상하게 느리다

JSON 자체는 작고 서버도 빨리 끝났는데, 왕복 지연이 자꾸 튄다.

가능한 원인:

- 작은 write가 여러 번 나뉘어 전송된다
- Nagle과 delayed ACK가 겹친다
- proxy buffering이 응답을 더 늦게 푼다

### 시나리오 2: gRPC unary 호출은 빠른데 특정 환경에서만 튄다

동일한 코드인데 모바일, VPN, 원격망에서만 지연이 보이면, small packet latency를 의심해 볼 수 있다.

### 시나리오 3: 서버는 빠른데 첫 글자/첫 바이트가 늦다

`time_starttransfer`는 늦고, `time_total`은 그럭저럭일 수 있다.

이 경우는 TCP나 proxy 레벨에서 첫 바이트가 지연되는 패턴을 본다.

## 코드로 보기

### 소켓 옵션 예시

```java
Socket socket = new Socket();
socket.setTcpNoDelay(true);
```

```go
conn, _ := net.Dial("tcp", "api.example.com:443")
tcpConn := conn.(*net.TCPConn)
_ = tcpConn.SetNoDelay(true)
```

### 지연을 관찰하는 방법

```bash
ss -ti dst api.example.com
tcpdump -i eth0 host api.example.com and tcp
```

관찰 포인트:

- 아주 작은 세그먼트가 자주 나가는지
- ACK 지연이 반복되는지
- retransmission은 없는데 체감만 느린지

### 애플리케이션 레벨에서 묶는 예시

```text
나쁜 방식:
- write() 1바이트
- write() 1바이트
- write() 1바이트

좋은 방식:
- 충분히 모아서 한 번에 write()
```

핵심은 커널에 맡기기 전에 **애플리케이션에서 의미 있는 단위로 묶는 것**이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| Nagle on | 작은 패킷을 줄인다 | interactive latency가 늘 수 있다 | bulk transfer |
| Nagle off (`TCP_NODELAY`) | 작은 응답이 빨라진다 | 패킷 수가 늘 수 있다 | RPC, 채팅, 제어 메시지 |
| 앱에서 batching | 의미 단위로 묶을 수 있다 | 구현이 복잡하다 | 성능과 지연을 같이 볼 때 |

핵심은 "작게 보내지 말자"가 아니라 **언제 묶고 언제 즉시 보낼지**를 정하는 것이다.

## 꼬리질문

> Q: Nagle을 끄면 무조건 빨라지나요?
> 핵심: 아니다. 패킷 수와 지연의 trade-off가 있고, delayed ACK나 상위 버퍼링은 남을 수 있다.

> Q: delayed ACK는 왜 문제가 되나요?
> 핵심: 작은 request-response에서 ACK가 늦어지면 sender도 다음 데이터를 못 보내며 대기할 수 있다.

> Q: throughput과 latency 중 무엇을 우선해야 하나요?
> 핵심: 상호작용이 중요하면 latency, 대용량이면 throughput을 더 본다.

## 한 줄 정리

Nagle과 delayed ACK는 네트워크 효율을 위해 만든 장치지만, 작은 왕복이 많은 실전 서비스에서는 서로를 기다리며 체감 지연을 키울 수 있다.
