# Connection Pool Starvation, Stale Idle Reuse, Debugging

> 한 줄 요약: connection pool starvation은 단순히 `maxConnections`가 작아서만 생기지 않는다. long-lived stream, stale idle socket, borrow 검증 부재, idle timeout mismatch가 겹치면 pool은 비어 보이지 않는데도 새 요청이 굶는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
> - [HTTP Keep-Alive Timeout Mismatch, Deeper Cases](./http-keepalive-timeout-mismatch-deeper-cases.md)
> - [TCP Reset Storms, Idle Reuse, Stale Sockets](./tcp-reset-storms-idle-reuse-stale-sockets.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation](./http2-max-concurrent-streams-pending-queue-saturation.md)

retrieval-anchor-keywords: connection pool starvation, stale idle socket, borrow validation, idle reuse, pool starvation debugging, pending acquire, maxConnections, long-lived stream, keepalive mismatch, pool exhaustion

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

connection pool starvation은 "active connection이 가득 차서 새 요청이 못 들어가는 상태"처럼 보이지만, 실제 원인은 여러 종류다.

- 실제 active connection이 너무 많다
- long-lived stream이 slot을 오래 점유한다
- stale idle socket이 pool 품질을 망친다
- borrow 시 검증이 없어 첫 요청만 실패하고 다시 대기한다
- idle timeout mismatch로 재사용 후보가 사실상 죽어 있다

즉 pool 문제는 크기뿐 아니라 **연결의 질과 수명 관리 문제**다.

### Retrieval Anchors

- `connection pool starvation`
- `stale idle socket`
- `borrow validation`
- `idle reuse`
- `pending acquire`
- `maxConnections`
- `long-lived stream`
- `pool exhaustion`

## 깊이 들어가기

### 1. pool starvation과 pool exhaustion은 같은 말이 아니다

`maxConnections`를 꽉 채운 단순 exhaustion은 한 경우일 뿐이다.

starvation은 더 넓다.

- usable connection이 부족하다
- idle처럼 보이지만 실제론 dead socket이다
- retry와 timeout이 재사용 품질을 더 악화시킨다

그래서 active/idle 개수만 보면 놓치는 경우가 많다.

### 2. long-lived traffic이 short request를 굶길 수 있다

같은 pool에 다음이 섞이면 starvation이 잘 생긴다.

- gRPC streaming
- SSE / long polling
- 대용량 upload/download
- 짧은 unary API

pool은 "연결 수"만 제한하지만, 각 연결의 점유 시간은 다르다.  
오래 사는 연결 몇 개가 짧은 요청의 대기열을 빠르게 키울 수 있다.

### 3. stale idle socket은 free slot처럼 보여도 실제론 함정이다

idle 리스트에 connection이 있다고 해서 usable하다는 뜻은 아니다.

- peer가 이미 idle timeout으로 닫았다
- LB drain 이후 죽은 backend를 가리킨다
- middlebox가 조용히 세션을 정리했다

borrow 시 검증이 없으면:

- 첫 요청이 reset
- retry가 새 borrow를 만든다
- pending queue가 더 길어진다

결국 pool starvation은 개수보다 **good connection hit ratio** 문제로 바뀐다.

### 4. idle timeout mismatch는 starvation을 간접적으로 만든다

pool은 connection을 아끼려 하지만 peer는 더 빨리 정리할 수 있다.

- client pool idle TTL이 너무 길다
- proxy/LB/origin keepalive가 더 짧다
- dead idle socket 비율이 올라간다

이 상황에서 burst가 오면 usable connection이 부족해져 starvation처럼 보인다.

### 5. borrow validation과 eviction은 비용이 있지만 흔히 필요하다

유용한 장치:

- validation on borrow
- background idle eviction
- max idle / max life / max age 제한
- stale connection probe

문제는 이것들이 공짜가 아니라는 점이다.

- borrow latency가 약간 늘 수 있다
- 검증용 round trip이 필요할 수 있다
- 과하게 짧은 life는 handshake churn을 만든다

### 6. H2/H3 pool은 socket 수보다 stream slot이 먼저 막힐 수도 있다

HTTP/2/3에서는 "연결은 하나"인데 내부 슬롯이 병목일 수 있다.

- TCP connection pool은 한가하다
- 하지만 H2 `MAX_CONCURRENT_STREAMS`가 꽉 찼다
- 사용자 입장에선 여전히 pool starvation처럼 보인다

그래서 modern pool starvation은 socket pool과 stream pool을 함께 봐야 한다.

## 실전 시나리오

### 시나리오 1: idle connection은 많은데 p99가 높다

가능한 원인:

- idle 중 상당수가 stale socket
- borrow validation이 없다
- first request after idle failure가 재시도와 결합한다

### 시나리오 2: streaming 기능 추가 후 평범한 API도 느려졌다

shared pool의 long-lived stream이 scarce connection을 잡아먹는 패턴일 수 있다.

### 시나리오 3: 배포 직후 pool starvation처럼 보인다

실제로는:

- old connection이 drain된 backend를 가리킨다
- warm-up 전 새 backend는 service time이 길다
- pending acquire queue가 동시에 늘어난다

### 시나리오 4: `maxConnections`를 늘렸는데도 좋아지지 않는다

root cause가 stale reuse, stream slot saturation, retry churn일 수 있다.  
크기만 키우면 quality 문제는 남는다.

## 코드로 보기

### 관찰 포인트

```text
- active / idle / pending acquire count
- stale socket hit rate
- first request after idle reset ratio
- borrow validation miss/hit
- long-lived vs short-lived traffic mix
- H2 active streams per connection
```

### 현장 질문

```text
- usable idle connection 비율은 얼마나 되는가
- pool starvation이 socket shortage인가 quality problem인가
- 같은 pool에 streaming과 unary가 섞여 있는가
- idle timeout hierarchy가 정렬되어 있는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 큰 pool | burst를 더 흡수한다 | stale socket과 blast radius도 커질 수 있다 | 안정된 peer |
| 검증 후 재사용 | quality가 좋아진다 | borrow 비용이 늘 수 있다 | 외부/불안정 경로 |
| long-lived / short-lived pool 분리 | starvation 격리가 좋다 | 운영 복잡도가 늘어난다 | mixed traffic |
| 짧은 idle eviction | dead socket을 빨리 버린다 | handshake churn이 늘 수 있다 | timeout mismatch가 큰 경로 |

핵심은 pool starvation을 단순 용량 부족으로 보지 않고 **연결 수명 관리와 재사용 품질 문제**로 함께 보는 것이다.

## 꼬리질문

> Q: idle connection이 많은데도 pool starvation이 날 수 있나요?
> 핵심: 가능하다. idle 중 상당수가 stale하거나 usable하지 않을 수 있다.

> Q: `maxConnections`만 올리면 해결되나요?
> 핵심: 아니다. long-lived traffic, stale reuse, H2 stream slot 병목은 그대로 남을 수 있다.

> Q: borrow validation은 왜 필요한가요?
> 핵심: idle 리스트의 dead socket을 실제 요청 전에 걸러내기 위해서다.

## 한 줄 정리

connection pool starvation은 단순 pool size 문제가 아니라 stale idle reuse, timeout mismatch, long-lived stream 점유가 함께 만드는 품질 문제라서, usable connection 비율과 borrow 품질을 같이 봐야 한다.
