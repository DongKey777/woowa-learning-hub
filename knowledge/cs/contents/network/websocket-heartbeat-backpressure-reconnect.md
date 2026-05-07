---
schema_version: 3
title: "WebSocket Heartbeat, Backpressure, Reconnect"
concept_id: network/websocket-heartbeat-backpressure-reconnect
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- websocket
- heartbeat
- backpressure
aliases:
- WebSocket heartbeat
- WebSocket backpressure
- reconnect policy
- slow consumer
- ping pong
- resume token
- send queue
- mobile reconnect
symptoms:
- WebSocket 연결만 열어 두면 운영에서 자동으로 안정적이라고 생각한다
- heartbeat가 없어 NAT timeout이나 mobile network change로 죽은 연결을 늦게 감지한다
- 느린 소비자 send queue가 쌓여 서버 메모리와 tail latency가 오른다
- reconnect에서 last seen message id나 resume token 없이 중복/누락을 만든다
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- network/sse-websocket-polling
- network/timeout-types-connect-read-write
next_docs:
- network/websocket-proxy-buffering-streaming-latency
- network/tcp-zero-window-persist-probe-receiver-backpressure
- network/upstream-queueing-connection-pool-wait-tail-latency
- network/sse-last-event-id-replay-window
linked_paths:
- contents/network/sse-websocket-polling.md
- contents/network/timeout-types-connect-read-write.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/network/websocket-proxy-buffering-streaming-latency.md
- contents/network/tcp-zero-window-persist-probe-receiver-backpressure.md
- contents/network/upstream-queueing-connection-pool-wait-tail-latency.md
confusable_with:
- network/sse-websocket-polling
- network/websocket-proxy-buffering-streaming-latency
- network/tcp-zero-window-persist-probe-receiver-backpressure
- network/upstream-queueing-connection-pool-wait-tail-latency
forbidden_neighbors: []
expected_queries:
- "WebSocket heartbeat backpressure reconnect를 어떻게 설계해야 해?"
- "느린 WebSocket consumer 때문에 서버 send queue가 쌓일 때 어떻게 대응해?"
- "모바일 네트워크에서 WebSocket reconnect가 반복될 때 heartbeat interval을 어떻게 봐?"
- "resume token과 last seen message id가 재연결 중복/누락을 줄이는 이유는?"
- "WebSocket 운영에서 ping pong만으로 충분하지 않은 이유는?"
contextual_chunk_prefix: |
  이 문서는 WebSocket long-lived connection의 heartbeat, ping/pong,
  slow consumer backpressure, per-connection send queue, reconnect, resume token,
  message id 중복/누락 복구를 다루는 advanced playbook이다.
---
# WebSocket Heartbeat, Backpressure, Reconnect

> 한 줄 요약: WebSocket은 연결을 오래 유지하는 기술이므로, heartbeat와 backpressure, reconnect 정책이 없으면 운영에서 쉽게 무너진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [SSE, WebSocket, Polling](./sse-websocket-polling.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [WebSocket Proxy Buffering, Streaming Latency](./websocket-proxy-buffering-streaming-latency.md)
> - [TCP Zero Window, Persist Probe, Receiver Backpressure](./tcp-zero-window-persist-probe-receiver-backpressure.md)
> - [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
> - [System Design](../system-design/README.md)

retrieval-anchor-keywords: WebSocket heartbeat, backpressure, reconnect, slow consumer, ping pong, resume token, send queue, mobile reconnect, connection liveness, streaming session

---

## 핵심 개념

WebSocket은 HTTP 업그레이드 후 장시간 양방향 통신을 제공한다.  
하지만 연결이 오래 간다는 사실 자체가 운영 부담이다.

핵심 운영 포인트:

- heartbeat로 죽은 연결을 빨리 감지
- backpressure로 느린 소비자를 분리
- reconnect 정책으로 네트워크 순간 단절을 흡수
- 메시지 순서와 중복을 앱 레벨에서 보정

### Retrieval Anchors

- `WebSocket heartbeat`
- `backpressure`
- `reconnect`
- `slow consumer`
- `ping pong`
- `resume token`
- `send queue`
- `connection liveness`

---

## 깊이 들어가기

### 1. Heartbeat가 필요한 이유

연결은 살아 보이는데 실제로는 반쯤 죽어 있는 경우가 있다.

- NAT timeout
- 모바일 네트워크 전환
- 방화벽 idle timeout
- 브라우저 탭 sleep

그래서 ping/pong 또는 heartbeat 메시지로 생존 여부를 확인한다.

### 2. Backpressure는 왜 필요한가

서버가 메시지를 너무 빨리 보내면 느린 클라이언트는 큐가 쌓인다.

문제:

- 메모리 증가
- 지연 누적
- 연결 폭주
- 일부 느린 클라이언트가 전체 서버 자원을 잡아먹음

해결:

- per-connection send buffer 제한
- slow consumer drop
- batch send
- server-side queue 분리

### 3. Reconnect는 어떻게 설계하는가

재연결은 "다시 붙기"가 아니다.  
중복/누락/순서 문제를 같이 설계해야 한다.

실무에서는 다음을 붙인다.

- connection id
- last seen message id
- exponential backoff
- jitter
- resume token

### 4. 메시지 순서와 중복

WebSocket은 네트워크 연결 자체를 유지하지만, 장애 후 재연결에서는 순서 보장이 깨질 수 있다.

그래서 보통:

- 서버가 monotonically increasing message id를 붙인다
- 클라이언트는 last ack를 보낸다
- 재연결 후 누락분을 다시 요청한다

---

## 실전 시나리오

### 시나리오 1: 한 사용자가 느려서 서버 메모리가 오른다

backpressure가 없으면 느린 소비자에게 메시지가 쌓여 전체 서버가 흔들린다.  
이때는 연결별 큐를 제한하고, 오래된 메시지를 버리거나 분리해야 한다.

### 시나리오 2: 모바일 앱이 계속 재연결한다

heartbeat가 너무 짧으면 네트워크 순간 흔들림에도 불필요하게 reconnect가 발생한다.  
반대로 너무 길면 죽은 연결을 늦게 발견한다.

### 시나리오 3: 메시지가 중복되어 보인다

재연결 시 last seen message id가 없으면 같은 메시지를 두 번 받을 수 있다.  
중복 제거는 서버/클라이언트 둘 중 한쪽이 책임져야 한다.

---

## 코드로 보기

### heartbeat 개념 예시

```text
client -> server: ping
server -> client: pong
```

### reconnect 정책 예시

```text
1s -> 2s -> 4s -> 8s -> 16s
with jitter and max cap
```

### backpressure 감각

```text
send queue > threshold:
  1. batch messages
  2. slow consumer downgrade
  3. disconnect if still saturated
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 짧은 heartbeat | 죽은 연결을 빨리 찾음 | 오탐이 늘 수 있음 | 실시간성이 중요할 때 |
| 긴 heartbeat | 네트워크 흔들림에 강함 | 장애 탐지가 늦음 | 모바일 환경 |
| 느린 소비자 드롭 | 서버 보호 | 일부 사용자는 메시지 유실 | 대규모 broadcast |
| 무제한 큐 | 단순해 보임 | 메모리 폭발 | 쓰면 안 됨 |

---

## 꼬리질문

> Q: WebSocket에서 heartbeat가 왜 필요한가?
> 의도: 연결이 살아있다고 메시지 통신도 정상이라는 착각을 하는지 확인
> 핵심: NAT/idle timeout 때문에 생존 확인이 필요하다

> Q: backpressure를 안 넣으면 어떤 일이 생기나?
> 의도: 느린 소비자가 전체 서버를 잡아먹는 문제를 이해하는지 확인
> 핵심: 큐가 쌓이고 메모리와 지연이 폭증한다

## 한 줄 정리

WebSocket은 연결 유지 자체보다 연결을 어떻게 감시하고, 느린 소비자를 어떻게 다루고, 끊겼을 때 어떻게 복구하느냐가 핵심이다.
