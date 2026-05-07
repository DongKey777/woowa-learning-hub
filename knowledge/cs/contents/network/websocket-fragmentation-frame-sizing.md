---
schema_version: 3
title: "WebSocket Fragmentation, Frame Sizing"
concept_id: network/websocket-fragmentation-frame-sizing
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- websocket
- frame-sizing
- fragmentation
aliases:
- WebSocket fragmentation
- WebSocket frame sizing
- continuation frame
- control frame
- message framing
- real-time stream chunking
- WebSocket large frame latency
symptoms:
- WebSocket 메시지가 항상 하나의 frame으로 한 번에 전달된다고 생각한다
- 큰 data frame이 heartbeat/control frame 체감 지연을 만들 수 있음을 놓친다
- frame을 너무 작게 쪼개 Nagle delayed ACK와 overhead를 키운다
- MTU, TLS record, proxy buffering과 frame sizing을 따로 보지 않는다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/websocket-heartbeat-backpressure-reconnect
- network/websocket-proxy-buffering-streaming-latency
next_docs:
- network/nagle-delayed-ack-small-packet-latency
- network/mtu-pmtud-icmp-blackhole-path-diagnostics
- network/tls-record-sizing-flush-streaming-latency
- network/packet-loss-jitter-reordering-diagnostics
linked_paths:
- contents/network/websocket-heartbeat-backpressure-reconnect.md
- contents/network/websocket-proxy-buffering-streaming-latency.md
- contents/network/nagle-delayed-ack-small-packet-latency.md
- contents/network/mtu-pmtud-icmp-blackhole-path-diagnostics.md
- contents/network/packet-loss-jitter-reordering-diagnostics.md
- contents/network/tls-record-sizing-flush-streaming-latency.md
confusable_with:
- network/websocket-proxy-buffering-streaming-latency
- network/nagle-delayed-ack-small-packet-latency
- network/mtu-pmtud-icmp-blackhole-path-diagnostics
- network/tls-record-sizing-flush-streaming-latency
forbidden_neighbors: []
expected_queries:
- "WebSocket fragmentation과 frame sizing이 latency에 어떤 영향을 줘?"
- "큰 WebSocket data frame이 ping pong 체감 지연을 만들 수 있는 이유는?"
- "작은 frame을 너무 많이 보내면 Nagle delayed ACK와 어떤 문제가 생겨?"
- "WebSocket continuation frame과 control frame을 어떻게 이해해야 해?"
- "frame size를 MTU TLS record proxy buffering과 같이 봐야 하는 이유는?"
contextual_chunk_prefix: |
  이 문서는 WebSocket message/frame fragmentation, continuation frame,
  control frame, frame size가 latency, buffering, heartbeat와 MTU/TLS record에
  미치는 영향을 다루는 advanced playbook이다.
---
# WebSocket Fragmentation, Frame Sizing

> 한 줄 요약: WebSocket은 메시지를 여러 frame으로 나눌 수 있지만, frame 크기와 분할 방식이 실시간성, buffering, 그리고 재전송 체감에 직접 영향을 준다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [WebSocket Heartbeat, Backpressure, Reconnect](./websocket-heartbeat-backpressure-reconnect.md)
> - [WebSocket Proxy Buffering, Streaming Latency](./websocket-proxy-buffering-streaming-latency.md)
> - [Nagle 알고리즘과 Delayed ACK](./nagle-delayed-ack-small-packet-latency.md)
> - [MTU, PMTUD, ICMP Blackhole Path Diagnostics](./mtu-pmtud-icmp-blackhole-path-diagnostics.md)
> - [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)
> - [TLS Record Sizing, Flush, Streaming Latency](./tls-record-sizing-flush-streaming-latency.md)

retrieval-anchor-keywords: WebSocket fragmentation, frame sizing, message framing, continuation frame, control frame, latency, buffering, chunking, real-time stream

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

WebSocket은 메시지를 frame 단위로 보낸다.

- 하나의 메시지가 여러 frame으로 나뉠 수 있다
- control frame과 data frame이 섞일 수 있다
- frame sizing이 너무 크거나 작으면 실시간성이 흔들린다

### Retrieval Anchors

- `WebSocket fragmentation`
- `frame sizing`
- `message framing`
- `continuation frame`
- `control frame`
- `latency`
- `buffering`
- `chunking`
- `real-time stream`

## 깊이 들어가기

### 1. fragmentation이 의미하는 것

WebSocket 메시지는 반드시 한 번에 다 보내지 않아도 된다.

- 큰 메시지를 여러 frame으로 나눌 수 있다
- continuation frame으로 이어 붙일 수 있다
- 하지만 중간 장비와 buffering이 개입하면 지연이 커질 수 있다

### 2. frame size가 왜 중요한가

너무 크면:

- serialization과 buffering 지연이 커진다
- MTU와 proxy buffering 문제를 더 쉽게 만난다

너무 작으면:

- frame 수가 많아져 overhead가 늘어난다
- Nagle/delayed ACK와 상호작용할 수 있다

### 3. control frame과의 관계

ping/pong이나 close 같은 control frame은 중요하다.

- heartbeat가 밀리지 않아야 한다
- 큰 data frame이 control frame을 체감상 가로막지 않게 해야 한다

### 4. 왜 실시간성이 흔들리나

- 앱이 큰 메시지를 한 번에 만들면 flush가 늦는다
- proxy buffering이 더 늦출 수 있다
- 작은 frame이 너무 많으면 오버헤드가 늘어난다

### 5. 운영에서 고려할 것

- 평균 메시지 크기
- 최대 메시지 크기
- heartbeat 주기
- proxy buffering 여부

## 실전 시나리오

### 시나리오 1: 채팅은 되는데 큰 이벤트만 늦는다

큰 frame과 buffering을 의심한다.

### 시나리오 2: ping/pong은 정상인데 사용자 메시지만 늦다

data frame sizing과 flush 정책을 봐야 한다.

### 시나리오 3: 모바일에서만 실시간성이 깨진다

loss/jitter와 frame sizing이 함께 영향을 줄 수 있다.

## 코드로 보기

### 프레임 감각

```text
message
-> one frame
or
-> multiple continuation frames
```

### 관찰 포인트

```text
- average frame size
- largest payload
- heartbeat delay
- proxy buffering
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 큰 frame | overhead가 적다 | 지연과 buffering이 커질 수 있다 | bulk message |
| 작은 frame | flush가 빠르다 | frame overhead가 늘어난다 | interactive stream |
| adaptive sizing | 균형이 좋다 | 구현이 복잡하다 | 실시간 서비스 |

핵심은 WebSocket이 메시지 경계만 있는 게 아니라 **frame 경계가 latency를 만든다**는 점이다.

## 꼬리질문

> Q: WebSocket fragmentation은 무엇인가요?
> 핵심: 하나의 메시지를 여러 frame으로 나누는 것이다.

> Q: frame size가 왜 중요하나요?
> 핵심: 실시간성, buffering, overhead가 함께 바뀌기 때문이다.

> Q: control frame은 왜 따로 봐야 하나요?
> 핵심: heartbeat와 close 처리가 지연되면 연결 상태 판단이 늦어진다.

## 한 줄 정리

WebSocket fragmentation과 frame sizing은 메시지를 어떻게 쪼개고 흘릴지의 문제라서, 실시간성과 buffering을 함께 고려해야 한다.
