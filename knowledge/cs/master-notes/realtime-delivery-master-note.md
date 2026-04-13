# Realtime Delivery Master Note

> 한 줄 요약: realtime delivery is the end-to-end design of pushing state changes quickly, safely, and in order enough for the product to trust them.

**Difficulty: Advanced**

> retrieval-anchor-keywords: realtime delivery, WebSocket, SSE, polling, heartbeat, reconnect, backpressure, last-event-id, resume token, message ordering, live updates, fan-out, push notification

> related docs:
> - [SSE, WebSocket, Polling](../contents/network/sse-websocket-polling.md)
> - [WebSocket Heartbeat, Backpressure, Reconnect](../contents/network/websocket-heartbeat-backpressure-reconnect.md)
> - [Socket Buffer Autotuning, Backpressure](../contents/operating-system/socket-buffer-autotuning-backpressure.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](../contents/network/connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Spring WebClient vs RestTemplate](../contents/spring/spring-webclient-vs-resttemplate.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Realtime delivery is more than transport.

It includes:

- notification generation
- push or stream transport
- reconnection
- deduplication
- ordering and freshness

The product only trusts realtime delivery if the update arrives fast enough and correctly enough.

## 깊이 들어가기

### 1. Pick the right transport for the semantics

Polling, SSE, and WebSocket each solve different shapes of realtime needs.

Read with:

- [SSE, WebSocket, Polling](../contents/network/sse-websocket-polling.md)

### 2. Heartbeat and reconnect are operational requirements

Long-lived connections need liveness checks and recovery policy.

Read with:

- [WebSocket Heartbeat, Backpressure, Reconnect](../contents/network/websocket-heartbeat-backpressure-reconnect.md)

### 3. Backpressure protects the server and the user experience

The delivery path must know when a client is too slow and how to degrade gracefully.

Read with:

- [Socket Buffer Autotuning, Backpressure](../contents/operating-system/socket-buffer-autotuning-backpressure.md)

### 4. Message identity is necessary for trust

Without ids or resume tokens, reconnect creates duplicates and gaps.

### 5. Realtime is also an upstream generation problem

The source of truth must emit events in a way that downstream delivery can replay safely.

Read with:

- [Domain Events, Outbox, Inbox](../contents/software-engineering/outbox-inbox-domain-events.md)

## 실전 시나리오

### 시나리오 1: live dashboard misses updates

Likely cause:

- reconnect lost state
- transport buffered too much

### 시나리오 2: chat duplicates messages after reconnect

Likely cause:

- no message id
- no resume token

### 시나리오 3: slow consumers crash the broadcaster

Likely cause:

- no backpressure
- unbounded per-client queue

## 코드로 보기

### SSE resume sketch

```text
server sends last-event-id
client reconnects with resume token
```

### WebSocket live stream sketch

```text
connect -> heartbeat -> message ids -> reconnect with last ack
```

### Backpressure guard

```java
if (sendQueue.size() > limit) {
    dropOrDisconnect();
}
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Polling | Simple | Wasteful | Low-frequency updates |
| SSE | Easy server push | One-way only | Notifications and streams |
| WebSocket | Full duplex | More state to manage | Chat and collaboration |
| Buffered delivery | Smooth spikes | Latency can hide | Burst-heavy streams |

## 꼬리질문

> Q: Why is realtime delivery not just a transport choice?
> Intent: checks end-to-end semantics.
> Core: it also needs identity, ordering, replay, and backpressure.

> Q: Why do reconnects create duplicates?
> Intent: checks idempotency of delivery.
> Core: the client may not know what the server already sent before the drop.

> Q: Why is backpressure essential in realtime systems?
> Intent: checks slow-consumer handling.
> Core: one slow client can otherwise poison the whole broadcaster.

## 한 줄 정리

Realtime delivery is the complete pipeline that pushes changes quickly while preserving enough identity, ordering, and backpressure to remain trustworthy.
