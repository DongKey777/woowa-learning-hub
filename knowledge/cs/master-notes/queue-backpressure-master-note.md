# Queue Backpressure Master Note

> 한 줄 요약: queue backpressure is how a system says "slow down" before the backlog becomes a failure cascade.

## 이 노트의 역할

이 노트는 `queue reliability` 군집의 **보조 노트**다.

- 먼저 [Queue Worker Reliability Master Note](./queue-worker-reliability-master-note.md)로 worker side의 안정성을 본다.
- 그 다음 이 노트에서 producer throttle, bounded queue, overload shedding, backlog control 같은 **압력 제어**를 본다.

**Difficulty: Advanced**

> retrieval-anchor-keywords: backpressure, queue depth, backlog, slow consumer, producer throttle, bounded queue, dead letter queue, retry storm, socket buffer, reconnect storm, admission control

> related docs:
> - [Socket Buffer Autotuning, Backpressure](../contents/operating-system/socket-buffer-autotuning-backpressure.md)
> - [WebSocket Heartbeat, Backpressure, Reconnect](../contents/network/websocket-heartbeat-backpressure-reconnect.md)
> - [Spring Batch Chunk Retry Skip](../contents/spring/spring-batch-chunk-retry-skip.md)
> - [Timeout, Retry, Backoff 실전](../contents/network/timeout-retry-backoff-practical.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](../contents/network/connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Backpressure is not just a network concept.
It is any signal that says the consumer cannot keep up and the producer must adapt.

The producer can respond by:

- slowing down
- batching
- dropping low-priority work
- rejecting excess work
- buffering in a bounded queue

## 깊이 들어가기

### 1. Bounded queues are a safety mechanism

An unbounded queue hides the problem until memory or latency explodes.

### 2. Backpressure must be explicit

If the producer ignores EAGAIN, 429, or queue-full signals, the system only moves the pressure elsewhere.

### 3. Retry can defeat backpressure

If retry happens too aggressively, the producer just reintroduces load at the worst possible time.

### 4. Backpressure exists at many layers

- TCP socket buffer
- WebSocket send queue
- app worker queue
- batch job queue
- message broker

Read with:

- [Socket Buffer Autotuning, Backpressure](../contents/operating-system/socket-buffer-autotuning-backpressure.md)
- [WebSocket Heartbeat, Backpressure, Reconnect](../contents/network/websocket-heartbeat-backpressure-reconnect.md)

## 실전 시나리오

### 시나리오 1: worker queue grows forever

Likely cause:

- producer faster than consumer
- no bounded queue
- no shedding policy

### 시나리오 2: slow client consumes all memory

Likely cause:

- no per-connection cap
- backpressure ignored

### 시나리오 3: retry storm follows queue saturation

Likely cause:

- timeout and retry policy amplify backlog

## 코드로 보기

### Bounded queue sketch

```java
BlockingQueue<Job> queue = new ArrayBlockingQueue<>(1000);
```

### Slow consumer handling

```java
if (!queue.offer(job)) {
    throw new TooBusyException("queue full");
}
```

### Backpressure signal sketch

```c
if (errno == EAGAIN) {
    // stop producing for now
}
```

## 트레이드-off

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Unbounded queue | Easy to code | Hidden failure | Rarely acceptable |
| Bounded queue | Protects memory | Drops/rejects work | Production systems |
| Shed low-priority work | Keeps core alive | Some loss accepted | Degraded mode |
| Slow down producer | More stable | Lower throughput | Cooperative systems |

## 꼬리질문

> Q: Why is backpressure a safety mechanism?
> Intent: checks overload containment.
> Core: it prevents the backlog from becoming an uncontrolled failure mode.

> Q: Why are unbounded queues dangerous?
> Intent: checks hidden latency and memory growth.
> Core: they delay failure until it is much larger and harder to recover.

> Q: How can retry break backpressure?
> Intent: checks amplification awareness.
> Core: retries inject more load when the system is already saturated.

## 한 줄 정리

Queue backpressure is the system's way of turning overload into a controlled slowdown instead of an uncontrolled collapse.
