---
schema_version: 3
title: "WebSocket Proxy Buffering, Streaming Latency"
concept_id: network/websocket-proxy-buffering-streaming-latency
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- websocket
- proxy-buffering
- streaming-latency
aliases:
- WebSocket proxy buffering
- streaming latency
- response buffering
- low latency streaming
- SSE buffering
- chunked transfer flush
- reverse proxy buffering
symptoms:
- 서버 로그상 write는 됐는데 client는 메시지를 늦게 받는다
- WebSocket ping/pong은 되는데 사용자 payload만 묶여 늦게 온다
- SSE chunk가 proxy나 TLS record에서 모여 실시간성이 깨지는 문제를 놓친다
- proxy buffering을 끄면 항상 좋다고 보고 slow client backpressure 비용을 무시한다
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- network/websocket-heartbeat-backpressure-reconnect
- network/api-gateway-reverse-proxy-operational-points
next_docs:
- network/tls-record-sizing-flush-streaming-latency
- network/http-response-compression-buffering-streaming-tradeoffs
- network/tcp-zero-window-persist-probe-receiver-backpressure
- network/nagle-delayed-ack-small-packet-latency
linked_paths:
- contents/network/websocket-heartbeat-backpressure-reconnect.md
- contents/network/idle-timeout-mismatch-lb-proxy-app.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/tcp-keepalive-vs-app-heartbeat.md
- contents/network/nagle-delayed-ack-small-packet-latency.md
- contents/network/expect-100-continue-proxy-request-buffering.md
- contents/network/tls-record-sizing-flush-streaming-latency.md
- contents/network/http-response-compression-buffering-streaming-tradeoffs.md
confusable_with:
- network/websocket-heartbeat-backpressure-reconnect
- network/tls-record-sizing-flush-streaming-latency
- network/http-response-compression-buffering-streaming-tradeoffs
- network/tcp-zero-window-persist-probe-receiver-backpressure
forbidden_neighbors: []
expected_queries:
- "WebSocket이나 SSE가 proxy buffering 때문에 실시간성이 깨지는 패턴은?"
- "서버는 보냈는데 client는 늦게 받으면 proxy flush를 어떻게 확인해?"
- "ping pong은 정상인데 메시지만 늦는 이유가 buffering일 수 있어?"
- "proxy_buffering off가 streaming latency에는 좋지만 slow client에는 위험한 이유는?"
- "TLS record flush와 HTTP compression buffering까지 같이 봐야 하는 이유는?"
contextual_chunk_prefix: |
  이 문서는 WebSocket/SSE/chunked streaming에서 reverse proxy buffering,
  flush, TLS record sizing, compression buffering, slow client backpressure를
  다루는 advanced playbook이다.
---
# WebSocket Proxy Buffering, Streaming Latency

> 한 줄 요약: WebSocket과 streaming 트래픽은 proxy buffering이 켜져 있으면 실시간성이 무너질 수 있어서, 버퍼링 정책을 별도로 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [WebSocket Heartbeat, Backpressure, Reconnect](./websocket-heartbeat-backpressure-reconnect.md)
> - [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [TCP Keepalive vs App Heartbeat](./tcp-keepalive-vs-app-heartbeat.md)
> - [Nagle 알고리즘과 Delayed ACK](./nagle-delayed-ack-small-packet-latency.md)
> - [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)
> - [TLS Record Sizing, Flush, Streaming Latency](./tls-record-sizing-flush-streaming-latency.md)
> - [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)

retrieval-anchor-keywords: WebSocket proxy buffering, streaming latency, flush, chunked transfer, reverse proxy, SSE, low latency streaming, response buffering

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

WebSocket, SSE, chunked streaming은 "바로바로 흘러야 하는 데이터"가 핵심이다.  
그런데 proxy buffering이 켜져 있으면 중간 장비가 데이터를 모았다가 늦게 내보낼 수 있다.

- 실시간성이 늦어진다
- 첫 메시지와 후속 메시지 사이가 벌어진다
- heartbeat와 flush 정책이 중요해진다

### Retrieval Anchors

- `WebSocket proxy buffering`
- `streaming latency`
- `flush`
- `chunked transfer`
- `reverse proxy`
- `SSE`
- `low latency streaming`
- `response buffering`

## 깊이 들어가기

### 1. buffering이 왜 들어가나

proxy buffering은 일반 HTTP에선 유용하다.

- 느린 클라이언트에서 backend를 보호한다
- 응답을 효율적으로 모아 보낸다
- 메모리와 네트워크 사용을 최적화한다

하지만 streaming에서는 이 장점이 오히려 단점이 된다.

### 2. WebSocket과 SSE에서 왜 문제가 큰가

WebSocket과 SSE는 데이터가 생성되는 즉시 전달되는 느낌이 중요하다.

- 채팅 메시지
- 실시간 알림
- 진행률 업데이트
- 이벤트 스트림

buffering이 있으면 "받았는데 안 오는 것처럼" 보인다.

### 3. flush가 왜 중요한가

app이 데이터를 써도 proxy가 flush하지 않으면 클라이언트는 못 본다.

- 작은 메시지가 누적된다
- latency가 늘어난다
- ping/pong이나 heartbeat의 의미도 흐려진다

proxy buffering이 꺼져 있어도 [TLS Record Sizing, Flush, Streaming Latency](./tls-record-sizing-flush-streaming-latency.md)처럼 TLS termination hop의 record/flush 정책이 또 다른 지연층을 만들 수 있다.

### 4. buffering을 언제 꺼야 하나

다음 상황은 buffering을 줄이거나 끄는 편이 낫다.

- low latency가 핵심인 실시간 채팅
- SSE 이벤트를 즉시 보여줘야 할 때
- upstream이 이미 충분히 작은 chunk로 보낼 때

### 5. buffering을 완전히 없애면 안 되는 이유

무조건 끄면 비용이 늘 수 있다.

- 느린 클라이언트에 취약해진다
- backend가 더 직접적인 backpressure를 받는다
- 큰 응답에서 메모리 효율이 떨어질 수 있다

## 실전 시나리오

### 시나리오 1: 서버 로그상으로는 보냈는데 클라이언트는 늦게 받는다

proxy buffering을 의심한다.

### 시나리오 2: WebSocket ping/pong은 되는데 메시지만 늦는다

buffering이나 flush 지연이 있을 수 있다.

### 시나리오 3: SSE가 실시간이 아니라 묶여서 온다

중간 proxy가 chunk를 모아 두고 있을 가능성이 높다.

## 코드로 보기

### Nginx buffering 감각

```nginx
location /stream {
    proxy_buffering off;
    proxy_request_buffering off;
    proxy_read_timeout 3600s;
}
```

### streaming 확인

```bash
curl -N https://api.example.com/stream
```

### 관찰 포인트

```text
- first byte가 늦는가
- chunk 간격이 균일한가
- proxy buffering이 켜져 있는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| buffering on | backend와 네트워크를 보호한다 | streaming latency가 커진다 | 일반 HTTP |
| buffering off | 실시간성이 좋아진다 | 느린 클라이언트에 취약하다 | WebSocket, SSE |
| selective buffering | 균형이 좋다 | 설정이 복잡하다 | 혼합 트래픽 |

핵심은 모든 트래픽에 같은 buffering 정책을 쓰지 않는 것이다.

## 꼬리질문

> Q: WebSocket에서 proxy buffering이 왜 문제인가요?
> 핵심: 데이터를 즉시 전달해야 하는데 proxy가 모아두면 실시간성이 깨진다.

> Q: SSE와 일반 HTTP의 buffering 정책이 다른가요?
> 핵심: 그렇다. SSE는 chunk를 바로 흘려보내는 쪽이 유리하다.

> Q: buffering을 무조건 끄면 좋은가요?
> 핵심: 아니다. 느린 클라이언트 보호와 자원 효율을 고려해야 한다.

## 한 줄 정리

WebSocket과 streaming은 proxy buffering이 있으면 지연이 커지므로, 실시간성이 중요한 경로는 별도 flush/buffering 정책으로 다뤄야 한다.
