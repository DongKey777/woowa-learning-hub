# Spring WebClient Connection Pool and Timeout Tuning

> 한 줄 요약: WebClient는 비동기라고 해서 자동으로 안전한 것이 아니며, connection pool과 timeout을 안 맞추면 느린 upstream을 더 오래 붙잡는 클라이언트가 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)
> - [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](./spring-resilience4j-retry-circuit-breaker-bulkhead.md)
> - [Spring Observability with Micrometer Tracing](./spring-observability-micrometer-tracing.md)
> - [Timeout types: connect/read/write](../network/timeout-types-connect-read-write.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](../network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [Connection Pool Starvation, Stale Idle Reuse, Debugging](../network/connection-pool-starvation-stale-idle-reuse-debugging.md)
> - [Upstream Queueing, Connection Pool Wait, Tail Latency](../network/upstream-queueing-connection-pool-wait-tail-latency.md)
> - [Service Mesh Local Reply, Timeout, Reset Attribution](../network/service-mesh-local-reply-timeout-reset-attribution.md)
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../network/network-spring-request-lifecycle-timeout-disconnect-bridge.md)

retrieval-anchor-keywords: WebClient, connection pool, Reactor Netty, response timeout, connect timeout, pending acquire timeout, max connections, proxy timeout, http client tuning, connection pool wait, stale idle reuse, upstream queueing, service mesh local reply

## 핵심 개념

WebClient는 reactive client이지만, 그 아래에는 실제 네트워크 자원 관리가 있다.

- connection pool
- connect timeout
- response timeout
- pending acquire timeout
- max connections

이 값들이 맞지 않으면 WebClient는 "비동기라서 빠르다"가 아니라 **느린 upstream을 더 오래 버티는 클라이언트**가 된다.

## 깊이 들어가기

### 1. WebClient는 Reactor Netty 설정에 크게 의존한다

실제 네트워크 성능은 `HttpClient` 설정에서 나온다.

```java
HttpClient httpClient = HttpClient.create()
    .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 2000)
    .responseTimeout(Duration.ofSeconds(3));
```

### 2. pool이 작으면 pending acquire가 늘어난다

동시 요청이 많아도 커넥션이 충분하지 않으면 대기열이 쌓인다.

- max connections
- pending acquire timeout
- idle timeout

이 값들을 함께 봐야 한다.

### 3. timeout은 종류가 다르다

`connect timeout`, `response timeout`, `read timeout`은 의미가 다르다.

이 차이를 섞으면 "왜 실패했는지"가 흐려진다.

### 4. retry보다 timeout이 먼저다

timeout 없이 retry를 늘리면 upstream을 더 오래 붙잡게 된다.

이 문맥은 [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](./spring-resilience4j-retry-circuit-breaker-bulkhead.md)와 같이 봐야 한다.

### 5. connection pool 튜닝은 트래픽 패턴에 맞춰야 한다

- fan-out이 많으면 pool이 더 필요할 수 있다
- API가 느리면 pool보다 timeout이 더 중요할 수 있다
- 한 upstream에 집중되면 bulkhead가 더 낫다

## 실전 시나리오

### 시나리오 1: WebClient를 썼는데도 느리다

원인 후보:

- 내부에서 block()을 했다
- pool이 작다
- timeout이 없다
- retry가 과하다

### 시나리오 2: 동시에 많이 호출하면 pending acquire가 늘어난다

커넥션 풀에서 커넥션을 빌리지 못하고 기다리는 것이다.

### 시나리오 3: upstream이 느릴 때 전체 요청이 밀린다

timeout이 없으면 스레드와 커넥션이 같이 묶인다.

### 시나리오 4: 장애는 아닌데 p99만 튄다

pool exhaustion이나 backpressure 없는 fan-out일 수 있다.

## 코드로 보기

### tuned WebClient bean

```java
@Bean
public WebClient webClient() {
    ConnectionProvider provider = ConnectionProvider.builder("app")
        .maxConnections(200)
        .pendingAcquireTimeout(Duration.ofSeconds(2))
        .build();

    HttpClient httpClient = HttpClient.create(provider)
        .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 2000)
        .responseTimeout(Duration.ofSeconds(3));

    return WebClient.builder()
        .clientConnector(new ReactorClientHttpConnector(httpClient))
        .build();
}
```

### timeout operator

```java
webClient.get()
    .uri("/feed")
    .retrieve()
    .bodyToMono(String.class)
    .timeout(Duration.ofSeconds(2));
```

### retry with caution

```java
webClient.get()
    .uri("/profile")
    .retrieve()
    .bodyToMono(Profile.class)
    .retry(1);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 작은 pool | 자원 사용이 적다 | 대기열이 빨리 찬다 | low traffic |
| 큰 pool | 동시성을 받는다 | upstream 압력이 커질 수 있다 | fan-out heavy |
| 짧은 timeout | 빠르게 실패한다 | transient failure에 민감하다 | latency-sensitive |
| 긴 timeout | 실패를 덜 낸다 | 자원을 오래 묶는다 | 느린 업스트림 허용 |

핵심은 WebClient를 "코드"가 아니라 **네트워크 자원 관리자**로 보는 것이다.

## 꼬리질문

> Q: WebClient가 느릴 때 가장 먼저 보는 것은 무엇인가?
> 의도: 네트워크 튜닝 순서 이해 확인
> 핵심: pool, timeout, block() 사용 여부다.

> Q: connect timeout과 response timeout의 차이는 무엇인가?
> 의도: timeout 종류 구분 확인
> 핵심: 연결 자체와 응답 대기 구간이 다르다.

> Q: pending acquire timeout은 무엇을 의미하는가?
> 의도: pool 대기 이해 확인
> 핵심: 커넥션을 빌리지 못하고 기다리는 시간 제한이다.

> Q: retry보다 timeout이 먼저인 이유는 무엇인가?
> 의도: retry storm 이해 확인
> 핵심: timeout이 없으면 실패를 빨리 감지하지 못한다.

## 한 줄 정리

WebClient는 비동기 호출 도구이지만, connection pool과 timeout이 맞지 않으면 결국 느린 upstream을 오래 기다리는 클라이언트가 된다.
