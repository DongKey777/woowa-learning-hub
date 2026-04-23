# Upstream Queueing, Connection Pool Wait, Tail Latency

> 한 줄 요약: 느린 요청의 상당수는 upstream이 응답을 늦게 해서가 아니라, 요청이 실제 네트워크 I/O를 시작하기도 전에 worker queue나 connection pool 대기열에서 시간을 태워서 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Accept Queue, SYN Backlog, Listen Overflow](./accept-queue-syn-backlog-listen-overflow.md)
> - [Proxy Retry Budget Discipline](./proxy-retry-budget-discipline.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation](./http2-max-concurrent-streams-pending-queue-saturation.md)
> - [Connection Pool Starvation, Stale Idle Reuse, Debugging](./connection-pool-starvation-stale-idle-reuse-debugging.md)
> - [Retry Storm Containment, Concurrency Limiter, Load Shedding](./retry-storm-containment-concurrency-limiter-load-shedding.md)
> - [Queue Saturation Attribution, Metrics, Runbook](./queue-saturation-attribution-metrics-runbook.md)

retrieval-anchor-keywords: upstream queueing, connection pool wait, pending requests, pool acquisition timeout, pending acquire, tail latency, queue length, concurrency limit, head of line in queue, fail-fast

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

요청이 느리다고 해서 곧바로 upstream 처리 시간이 긴 것은 아니다.

실제 지연은 종종 두 단계로 나뉜다.

- queue wait: 아직 연결도 못 잡고 대기하는 시간
- service time: 실제 connect, TLS, request/response에 쓰는 시간

connection pool, proxy worker, sidecar, event loop가 모두 queue를 만들 수 있다.

### Retrieval Anchors

- `upstream queueing`
- `connection pool wait`
- `pending requests`
- `pool acquisition timeout`
- `pending acquire`
- `tail latency`
- `queue length`
- `concurrency limit`

## 깊이 들어가기

### 1. connect latency와 "connect를 시작하기 전 대기"는 다르다

운영 대시보드가 `connect time`만 보여 주면 놓치는 구간이 있다.

- pool에 idle connection이 없어 기다린다
- max connections 제한 때문에 대기한다
- proxy worker queue에서 dispatch 자체가 늦는다

이 시간은 네트워크가 아니라 **로컬 자원 경쟁**이다.  
그런데 사용자 입장에서는 이미 요청이 느리다.

### 2. connection pool은 캐시이면서 동시성 제한기다

pool은 연결 재사용 도구이기도 하지만, 동시에 active connection 수를 제한하는 semaphore 역할도 한다.

- active connection이 가득 차면
- 새 요청은 pending queue에 선다
- queue가 길어질수록 tail latency가 급격히 악화된다

특히 per-host pool은 특정 upstream 하나가 느려질 때 그 호스트에 대한 대기열만 급증시키기도 한다.

### 3. queue는 평균보다 꼬리를 더 망친다

처리량이 한계에 가까워질수록 작은 흔들림도 queue를 빠르게 키운다.

- 평균 latency는 잠깐만 오른다
- p95 / p99는 급격히 튄다
- timeout budget은 queue에서 먼저 타 버린다

그래서 "upstream 평균 응답은 80ms라서 괜찮다"는 말이 tail latency를 설명하지 못한다.

### 4. pending queue를 크게 두면 장애를 숨길 수 있다

대기열을 크게 두면 순간 burst는 흡수한다.  
하지만 지속적인 overload에서는 다음 문제가 생긴다.

- 이미 불가능한 요청도 오래 기다린다
- budget이 바닥난 뒤에야 dispatch된다
- retry가 또 새 요청을 queue에 넣는다

즉 큰 queue는 완충재이면서 동시에 **지연 증폭기**다.

### 5. long-lived stream이 pool을 독점하면 unary RPC도 같이 느려진다

동일 pool에 다음이 섞이면 흔히 문제가 생긴다.

- 대용량 upload
- server streaming
- WebSocket / SSE 유사 장기 연결
- 짧은 unary API

활성 연결 수만 보면 적어 보여도, 오래 살아 있는 stream이 scarce connection을 붙잡아 pending queue를 만들 수 있다.

### 6. queue는 한 곳에만 있지 않다

실제 경로에는 여러 queue가 겹친다.

- gateway worker queue
- client-side connection pool pending queue
- H2 pending stream queue
- sidecar dispatch queue
- thread pool or event loop task queue

문제는 각 계층이 자기 queue만 보고 "나는 정상"이라고 말하기 쉽다는 점이다.  
end-to-end 관점에서는 모두 같은 예산을 태우는 대기 시간이다.

## 실전 시나리오

### 시나리오 1: upstream 서비스는 멀쩡한데 API gateway p99만 튄다

가능한 원인:

- gateway worker queue가 길다
- upstream connection pool이 포화됐다
- 실제 네트워크 I/O 전 대기 시간이 대부분이다

### 시나리오 2: 배포 직후 잠깐 504가 늘었다

새 인스턴스가 warm-up 전이라 service time이 잠깐 늘고, 그 결과 pending queue가 급증해 timeout budget을 먼저 태운 패턴일 수 있다.

### 시나리오 3: streaming 요청 추가 후 짧은 API도 느려졌다

같은 pool을 공유하고 있으면 long-lived stream이 scarce connection을 붙잡아 unary request 대기열을 만든다.

### 시나리오 4: retry를 넣었더니 성공률은 조금 오르는데 꼬리 지연이 폭발한다

기존 queue 위에 재시도 요청까지 얹어 overload를 증폭시킨 전형적인 패턴이다.

## 코드로 보기

### 관찰 포인트

```text
- active connections
- idle connections
- pending acquire count
- pending acquire wait ms
- queue wait vs upstream service time
- timeout before dispatch count
```

### 정책 감각

```text
max_connections: bounded
pending_queue: bounded
pending_acquire_timeout: shorter than remaining budget floor
separate pools for long-lived and short-lived traffic
```

### 현장 질문

```text
- 이 요청은 언제 socket을 실제로 잡았는가
- connect time 앞에 local queue wait가 있었는가
- 같은 pool에 streaming과 unary가 섞여 있는가
- timeout이 upstream 응답 전인지 dispatch 전인지 구분되는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 큰 pending queue | 순간 burst를 흡수한다 | 지속 overload에서 꼬리 지연과 zombie work가 늘어난다 | 짧은 burst가 잦을 때 |
| 작은 queue + fail-fast | tail latency와 자원 낭비를 줄인다 | 에러율이 더 빨리 드러난다 | 안정성 우선 경로 |
| shared pool | 단순하고 재사용 효율이 좋다 | long-lived traffic이 short request를 가로막을 수 있다 | 트래픽 특성이 비슷할 때 |
| pool 분리 | 격리가 잘 된다 | 설정과 운영 복잡도가 늘어난다 | streaming과 unary 혼합 경로 |

핵심은 tail latency를 upstream 응답 시간만으로 보지 않고 **I/O 시작 전 queueing 시간까지 포함해 해석하는 것**이다.

## 꼬리질문

> Q: connection pool wait는 왜 네트워크 문제처럼 보이나요?
> 핵심: 사용자 입장에서는 이미 요청이 느리지만, 실제로는 아직 네트워크 I/O도 시작하지 않았을 수 있기 때문이다.

> Q: pending queue를 크게 두면 왜 위험한가요?
> 핵심: 순간 burst는 흡수해도 지속 overload에서는 timeout budget과 retry를 더 많이 태운다.

> Q: streaming과 unary를 같은 pool에 넣으면 왜 안 좋은가요?
> 핵심: 장수명 연결이 scarce connection을 붙잡아 짧은 요청의 대기열을 키울 수 있다.

## 한 줄 정리

느린 요청의 원인을 정확히 찾으려면 upstream service time만 보지 말고, connection pool과 worker queue에서 I/O 시작 전 이미 얼마나 기다렸는지부터 분리해 봐야 한다.
