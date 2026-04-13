# Network Failure Handling Master Note

> 한 줄 요약: network failure handling is about identifying which layer failed, then choosing the least harmful response before retries or timeouts turn the incident into an amplifier.

**Difficulty: Advanced**

> retrieval-anchor-keywords: connect timeout, read timeout, write timeout, SYN retransmission, handshake timeout, idle timeout, connection draining, stale socket, FIN, RST, half-close, EOF, keepalive, deadline, cancellation, packet loss, jitter, retry amplification

> related docs:
> - [Timeout Types: connect / read / write](../contents/network/timeout-types-connect-read-write.md)
> - [Timeout, Retry, Backoff Practical](../contents/network/timeout-retry-backoff-practical.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](../contents/network/connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Connection Draining vs FIN / RST / Graceful Close](../contents/network/connection-draining-vs-fin-rst-graceful-close.md)
> - [LB Connection Draining / Deployment Safe Close](../contents/network/lb-connection-draining-deployment-safe-close.md)
> - [gRPC Deadlines, Cancellation Propagation](../contents/network/grpc-deadlines-cancellation-propagation.md)
> - [TCP Reset Storms / Idle Reuse / Stale Sockets](../contents/network/tcp-reset-storms-idle-reuse-stale-sockets.md)
> - [Idle Timeout Mismatch: LB / Proxy / App](../contents/network/idle-timeout-mismatch-lb-proxy-app.md)
> - [SYN Retransmission / Handshake Timeout](../contents/network/syn-retransmission-handshake-timeout.md)
> - [Packet Loss / Jitter / Reordering Diagnostics](../contents/network/packet-loss-jitter-reordering-diagnostics.md)
> - [Connection Reuse vs Service Discovery Churn](../contents/network/connection-reuse-vs-service-discovery-churn.md)
> - [ALB / ELB Retry Amplification Proxy Chain](../contents/network/alb-elb-retry-amplification-proxy-chain.md)
> - [FIN / RST / Half-Close / EOF Semantics](../contents/network/fin-rst-half-close-eof-semantics.md)
> - [TCP Keepalive vs App Heartbeat](../contents/network/tcp-keepalive-vs-app-heartbeat.md)
> - [HTTP/2 Multiplexing and HOL Blocking](../contents/network/http2-multiplexing-hol-blocking.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)

## 핵심 개념

Network failures are not one thing.

The connection can fail at different stages:

- DNS resolution
- TCP handshake
- TLS handshake
- request upload
- response wait
- idle reuse
- proxy drain
- downstream cancellation

If we do not classify the failure stage, we usually fix the wrong layer.

## 깊이 들어가기

### 1. Timeout type should match the failure stage

Connect timeout, read timeout, and write timeout are different tools.

They answer different questions:

- did the connection ever form
- did the server stop responding
- did the request get stuck while being sent

### 2. Stale sockets are a real failure mode

Long-lived pools can reuse connections that look healthy but are no longer valid.

Typical symptoms:

- RST after idle reuse
- sporadic EOF
- bursts after deployment or LB rotation

The fix is usually a combination of keepalive, pool policy, and timeout alignment.

### 3. Drain before you cut over

If a server or load balancer is removed too abruptly:

- active requests are reset
- client retries spike
- downstreams see retry amplification

Graceful connection draining reduces that blast radius.

### 4. Deadlines are different from generic retries

An upstream timeout policy should know the total request budget.

If the request is already past deadline, retrying is wasteful.

Cancellation propagation matters because a completed user action should stop spending resources.

### 5. Packet loss and jitter can look like app bugs

Sometimes the application is fine but the network path is unstable.

Symptoms:

- uneven latency
- retransmission bursts
- occasional handshake slowdown
- throughput collapse under load

That is why network troubleshooting must include packet-level evidence, not only app logs.

## 실전 시나리오

### 시나리오 1: connect timeout spikes after a deploy

Check:

- LB health and draining
- DNS and routing churn
- SYN retransmission
- service discovery update timing

### 시나리오 2: requests fail only after being idle for a while

Check:

- stale connection reuse
- LB idle timeout mismatch
- proxy idle timeout mismatch
- app pool max idle settings

### 시나리오 3: gRPC calls stay busy after the client disconnects

Check:

- cancellation propagation
- context checks in the downstream
- deadline alignment across hops

### 시나리오 4: retry makes a partial outage worse

Check:

- backoff and jitter
- retry ownership
- connection pool pressure
- whether the failure is even retryable

## 코드로 보기

### Client-side timeout and keepalive sketch

```java
HttpClient httpClient = HttpClient.create()
    .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 1000)
    .responseTimeout(Duration.ofSeconds(2))
    .keepAlive(true);

WebClient client = WebClient.builder()
    .clientConnector(new ReactorClientHttpConnector(httpClient))
    .build();
```

### gRPC deadline propagation sketch

```java
UserServiceGrpc.UserServiceBlockingStub stub =
    UserServiceGrpc.newBlockingStub(channel)
        .withDeadlineAfter(500, TimeUnit.MILLISECONDS);
```

### Operational checks

```bash
ss -ant state established
curl --connect-timeout 1 --max-time 2 https://example.com/health
tcpdump -nn host 10.0.0.10 and port 443
```

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Short timeout + fail fast | Protects resources | More visible failures | External dependencies |
| Longer timeout | Fewer false negatives | More connection and thread occupancy | Rarely, if ever |
| Aggressive retry | Hides transient faults | Can amplify outages | Only with idempotency and budget control |
| Connection draining | Safer deploys | Slower cutover | LB or server replacement |
| Keepalive | Fewer stale sockets | More background traffic | Long-lived connections |

The main decision is whether the system should absorb or expose the failure.

## 꼬리질문

> Q: Why do connect timeout and read timeout solve different problems?
> Intent: checks stage-specific diagnosis.
> Core: one is about establishing the connection, the other is about waiting for data.

> Q: Why can stale sockets fail after idle reuse?
> Intent: checks connection-lifecycle awareness.
> Core: the socket looked alive when cached but was no longer valid when reused.

> Q: Why is connection draining important during deploys?
> Intent: checks cutover safety.
> Core: it reduces resets and retry storms while traffic moves to the new instance.

> Q: Why should deadline and cancellation be propagated?
> Intent: checks budget and resource control.
> Core: otherwise the system keeps spending work after the request is already dead.

## 한 줄 정리

Network failure handling works when we classify the stage of failure, align the timeout and retry policy to that stage, and drain or cancel work before it amplifies the incident.
