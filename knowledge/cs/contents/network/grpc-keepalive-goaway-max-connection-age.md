---
schema_version: 3
title: "gRPC Keepalive, GOAWAY, Max Connection Age"
concept_id: network/grpc-keepalive-goaway-max-connection-age
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- grpc-keepalive-goaway
- max-connection-age-drain
- reconnect-storm-prevention
aliases:
- gRPC keepalive
- HTTP/2 PING
- GOAWAY max connection age
- keepalive without calls
- too_many_pings
- reconnect storm
symptoms:
- gRPC keepalive ping을 HTTP keep-alive 연결 재사용과 같은 개념으로 본다
- keepalive_without_calls를 공격적으로 설정해 too_many_pings나 reconnect storm을 만든다
- GOAWAY를 정상 drain/rotation 신호가 아니라 무조건 장애로 해석한다
- max connection age를 jitter 없이 동일하게 적용해 대량 재연결을 유발한다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- network/grpc-deadlines-cancellation-propagation
- network/connection-keepalive-loadbalancing-circuit-breaker
next_docs:
- network/idle-timeout-mismatch-lb-proxy-app
- network/lb-connection-draining-deployment-safe-close
- network/http2-rst-stream-goaway-streaming-failure-semantics
- network/grpc-keepalive-vs-http2-ping-vs-tcp-keepalive-beginner-bridge
linked_paths:
- contents/network/grpc-deadlines-cancellation-propagation.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/network/idle-timeout-mismatch-lb-proxy-app.md
- contents/network/lb-connection-draining-deployment-safe-close.md
- contents/network/http2-multiplexing-hol-blocking.md
- contents/network/http2-rst-stream-goaway-streaming-failure-semantics.md
confusable_with:
- network/grpc-keepalive-vs-http2-ping-vs-tcp-keepalive-beginner-bridge
- network/connection-keepalive-loadbalancing-circuit-breaker
- network/idle-timeout-mismatch-lb-proxy-app
- network/lb-connection-draining-deployment-safe-close
- network/http2-rst-stream-goaway-streaming-failure-semantics
forbidden_neighbors: []
expected_queries:
- "gRPC keepalive ping과 GOAWAY와 max connection age를 어떻게 같이 설계해?"
- "keepalive_without_calls가 너무 짧으면 too_many_pings와 reconnect storm이 왜 생겨?"
- "GOAWAY는 장애가 아니라 drain 신호일 수 있다는 점을 설명해줘"
- "LB idle timeout과 gRPC keepalive interval을 어떻게 맞춰야 해?"
- "max connection age에 jitter가 없으면 왜 모든 클라이언트가 동시에 재연결해?"
contextual_chunk_prefix: |
  이 문서는 gRPC keepalive PING, keepalive_without_calls, GOAWAY,
  max connection age, load balancer idle timeout, drain, reconnect storm을
  운영 설정 관점으로 다루는 advanced playbook이다.
---
# gRPC Keepalive, GOAWAY, Max Connection Age

> 한 줄 요약: gRPC keepalive ping, `GOAWAY`, `max connection age`는 모두 연결 생명주기를 다루지만, load balancer와 drain 정책과 엇갈리면 dead-peer detection이 아니라 reconnect storm을 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [gRPC Deadlines, Cancellation Propagation](./grpc-deadlines-cancellation-propagation.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
> - [Load Balancer Connection Draining, Deployment Safe Close](./lb-connection-draining-deployment-safe-close.md)
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)

retrieval-anchor-keywords: gRPC keepalive, HTTP/2 PING, GOAWAY, max connection age, load balancer idle timeout, keepalive without calls, reconnect storm, drain, too_many_pings, dead peer detection

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

gRPC 장기 연결은 한 번 열고 오래 쓰는 것이 이득이지만, 영원히 같은 연결만 쓰면 다음 문제가 생긴다.

- LB drain과 배포 이벤트를 반영하기 어렵다
- 죽은 peer를 늦게 감지할 수 있다
- 너무 오래된 연결에 stream이 과하게 몰릴 수 있다

그래서 gRPC는 다음 장치들을 둔다.

- `keepalive ping`: peer가 아직 살아 있는지 확인
- `GOAWAY`: 이 연결에 새 stream을 더 받지 않겠다는 신호
- `max connection age`: 연결을 너무 오래 붙잡지 않도록 주기적으로 회전

### Retrieval Anchors

- `gRPC keepalive`
- `HTTP/2 PING`
- `GOAWAY`
- `max connection age`
- `load balancer idle timeout`
- `keepalive without calls`
- `reconnect storm`
- `too_many_pings`

## 깊이 들어가기

### 1. gRPC keepalive는 HTTP keep-alive와 다르다

여기서 keepalive는 "연결 재사용"보다는 **죽은 연결을 감지하는 PING 정책**에 가깝다.

- 일정 시간 유휴면 PING을 보낸다
- 일정 시간 안에 ACK가 없으면 peer를 죽은 것으로 본다
- 필요하면 재연결한다

하지만 이것은 timeout budget 자체를 늘려 주는 기능이 아니다.  
느린 요청을 고치는 장치가 아니라, 죽은 transport를 빨리 드러내는 장치다.

### 2. `keepalive_without_calls`는 특히 조심해야 한다

active stream이 없을 때도 ping을 계속 허용하면 문제가 생길 수 있다.

- NAT나 LB idle timeout을 피하는 데는 도움이 된다
- 하지만 대규모 클라이언트 집단에서는 ping 트래픽이 그 자체로 부담이 된다
- 서버가 이를 싫어하면 `GOAWAY`나 `too_many_pings`류 거절을 보낼 수 있다

즉 keepalive는 "짧을수록 안전"이 아니라 **필요 이상으로 공격적이면 역효과**다.

### 3. `GOAWAY`는 실패가 아니라 연결 회전 신호일 수 있다

gRPC/HTTP2에서 `GOAWAY`는 보통 다음 뜻이다.

- 이 연결은 곧 닫을 것이다
- 새 stream은 다른 연결로 보내라
- 이미 진행 중인 stream은 가능한 한 마무리하자

배포, drain, max age 회전에서 정상적으로 볼 수 있다.  
문제는 클라이언트가 이를 "장애"로 오해하고 즉시 대량 재연결할 때다.

### 4. `max connection age`는 드레인과 같이 설계해야 한다

max age를 두는 이유는 다음과 같다.

- 특정 연결에 stream이 너무 오래 몰리는 것을 완화
- LB나 endpoint churn을 반영
- 인증서 회전, routing 변경, connection draining을 더 부드럽게 수행

하지만 모두가 같은 값으로 동시에 회전하면:

- 동일 시점에 `GOAWAY`가 몰리고
- 클라이언트가 재연결을 동시에 시도하고
- TLS handshake와 name resolution이 한꺼번에 증가한다

그래서 jitter나 분산된 age 정책이 중요하다.

### 5. LB idle timeout과 gRPC keepalive는 서로 덮어써서는 안 된다

LB idle timeout이 60초인데 client keepalive가 2분이면:

- LB가 먼저 연결을 조용히 끊는다
- 다음 stream이나 write 시점에 갑자기 실패로 드러난다

반대로 client keepalive가 10초로 너무 짧으면:

- 모든 장기 연결이 불필요하게 ping을 친다
- LB와 서버가 ping flood로 느낄 수 있다

핵심은 누가 liveness를 책임지는지 일관되게 정하는 것이다.

### 6. 운영에서는 request timeout과 transport rotation을 분리해 봐야 한다

다음 지표가 뒤섞이면 오판하기 쉽다.

- RPC deadline exceeded
- transport reconnects
- GOAWAY 수신 건수
- keepalive timeout
- LB connection drain 이벤트

요청 실패가 비즈니스 지연 때문인지, 연결 회전 타이밍 문제인지 분리해서 봐야 한다.

## 실전 시나리오

### 시나리오 1: 배포 때마다 gRPC client reconnect storm이 난다

가능한 원인:

- drain 직전에 `GOAWAY`가 한꺼번에 나간다
- 모든 클라이언트가 즉시 새 TLS 연결을 맺는다
- max connection age가 배포 이벤트와 같은 주기로 겹친다

### 시나리오 2: unary RPC는 짧은데 간헐적 `UNAVAILABLE`이 뜬다

이 경우 요청 본문보다 transport 회전을 먼저 봐야 할 수 있다.

- LB idle timeout이 먼저 끊었다
- keepalive interval이 너무 길다
- stale connection reuse 직후 첫 요청이 실패한다

### 시나리오 3: 서버는 정상인데 `too_many_pings` 비슷한 거절이 보인다

클라이언트 keepalive가 지나치게 공격적일 수 있다.

- active call도 없는데 주기적으로 ping을 보낸다
- 모바일/edge 환경의 수많은 client가 같은 설정을 쓴다
- 서버는 이를 방어적으로 차단한다

### 시나리오 4: max age를 켠 뒤 tail latency가 오히려 튄다

회전 자체는 필요했지만 jitter 없이 일제히 회전해 handshake, DNS, warm-up 비용이 동시에 커진 패턴이다.

## 코드로 보기

### Java Netty client 예시

```java
ManagedChannel channel = NettyChannelBuilder.forTarget(target)
    .keepAliveTime(60, TimeUnit.SECONDS)
    .keepAliveTimeout(10, TimeUnit.SECONDS)
    .keepAliveWithoutCalls(false)
    .build();
```

### 서버 쪽 회전 정책 감각

```text
max_connection_age: bounded with jitter
grace_period_after_goaway: enough for in-flight streams
idle_timeout_vs_ping_interval: aligned
```

### 관찰 포인트

```text
- GOAWAY received / sent count
- transport reconnect rate
- first request after reconnect latency
- keepalive timeout count
- drain event와 reconnect burst의 시점 상관관계
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 짧은 keepalive interval | dead peer를 빨리 찾는다 | ping 트래픽과 거절 위험이 커진다 | 불안정한 네트워크 |
| 긴 keepalive interval | 오버헤드가 적다 | stale connection을 늦게 감지한다 | 안정적인 내부망 |
| max connection age 사용 | drain과 endpoint churn 반영이 쉬워진다 | jitter 없으면 reconnect storm이 난다 | 장수명 gRPC 연결 |
| active call 없을 때 ping 금지 | 불필요한 ping을 줄인다 | idle LB timeout 대응이 어렵다 | 대규모 client fleet |

핵심은 keepalive를 "연결을 살리는 기능"보다 **연결 생명주기를 제어하는 운영 정책**으로 보는 것이다.

## 꼬리질문

> Q: `GOAWAY`는 항상 장애인가요?
> 핵심: 아니다. 정상적인 drain이나 connection rotation 신호일 수 있다.

> Q: keepalive interval을 짧게 하면 왜 위험한가요?
> 핵심: 대규모 client에서 ping flood와 불필요한 reconnect를 만들 수 있다.

> Q: max connection age는 왜 jitter가 필요한가요?
> 핵심: 동시에 회전하면 handshake와 reconnect가 한꺼번에 몰리기 때문이다.

## 한 줄 정리

gRPC keepalive와 `GOAWAY`, max connection age는 dead peer detection과 graceful rotation을 위한 장치지만, LB idle timeout과 drain 정책과 맞물리지 않으면 장애 감지가 아니라 reconnect storm이 된다.
