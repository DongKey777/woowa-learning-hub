# Spring RestClient vs WebClient Lifecycle Boundaries

> 한 줄 요약: RestClient와 WebClient는 둘 다 HTTP 클라이언트지만, blocking lifecycle과 reactive lifecycle이 다르므로 같은 방식으로 설정하거나 관측하면 안 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)
> - [Spring `@JsonTest` and `@RestClientTest` Slice Boundaries](./spring-jsontest-restclienttest-slice-boundaries.md)
> - [Spring Reactive-Blocking Bridge: `block()`, `boundedElastic`, and Boundary Traps](./spring-reactive-blocking-bridge-boundedelastic-block-traps.md)
> - [Spring WebClient Connection Pool and Timeout Tuning](./spring-webclient-connection-pool-timeout-tuning.md)
> - [Spring SecurityContext Propagation Across Async and Reactive Boundaries](./spring-securitycontext-propagation-async-reactive-boundaries.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](../network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)

retrieval-anchor-keywords: RestClient, WebClient, lifecycle boundaries, blocking client, reactive client, request execution, exchange filters, client connector, outbound HTTP

## 핵심 개념

RestClient는 동기식 HTTP 호출 모델에 가깝고, WebClient는 reactive pipeline에 맞다.

- RestClient: 호출 스레드가 응답을 기다린다
- WebClient: 신호 체인과 scheduler/context가 중요하다

즉, 둘은 "새로운 HTTP 클라이언트"라는 공통점보다 **실행 수명 주기**가 다르다.

## 깊이 들어가기

### 1. RestClient는 blocking lifecycle이다

```java
RestClient client = RestClient.create();
String body = client.get().uri("/ping").retrieve().body(String.class);
```

이 흐름에서는 요청을 보낸 스레드가 응답을 기다린다.

### 2. WebClient는 reactive lifecycle이다

```java
Mono<String> body = webClient.get()
    .uri("/ping")
    .retrieve()
    .bodyToMono(String.class);
```

이 흐름은 publisher/subscriber 체인 안에서 의미가 있다.

### 3. 요청 lifecycle과 관측 포인트가 다르다

RestClient는 간단한 interceptor/logging으로 충분한 경우가 많다.

WebClient는 filter, reactor context, metrics, scheduler를 함께 봐야 한다.

### 4. timeout과 retry의 적용 위치가 다르다

동기 클라이언트는 호출 스레드 점유를 직접 고려해야 한다.

반응형 클라이언트는 signal chain과 backpressure를 고려해야 한다.

### 5. SecurityContext와 trace propagation도 다르다

이 문맥은 [Spring SecurityContext Propagation Across Async and Reactive Boundaries](./spring-securitycontext-propagation-async-reactive-boundaries.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: RestClient를 쓰는데도 느리다

timeout이 없거나 외부 API가 느린 경우다.

### 시나리오 2: WebClient를 썼는데 block()을 남발한다

reactive lifecycle의 장점이 무너진다.

### 시나리오 3: 동일한 인증 헤더를 두 클라이언트에 붙이려 한다

전파 전략이 다르므로 같은 방식으로 붙이면 안 된다.

### 시나리오 4: metrics가 두 클라이언트에서 다르게 나온다

blocking과 reactive instrumentation이 다르기 때문이다.

## 코드로 보기

### RestClient

```java
@Bean
public RestClient restClient(RestClient.Builder builder) {
    return builder.baseUrl("https://api.example.com").build();
}
```

### WebClient

```java
@Bean
public WebClient webClient(WebClient.Builder builder) {
    return builder.baseUrl("https://api.example.com").build();
}
```

### blocking use case

```java
String value = restClient.get().uri("/health").retrieve().body(String.class);
```

### reactive use case

```java
Mono<String> value = webClient.get().uri("/health").retrieve().bodyToMono(String.class);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| RestClient | 단순하다 | 스레드를 점유한다 | 동기 서비스 |
| WebClient | 확장성이 높다 | reactive 운영이 필요하다 | 비동기/팬아웃 |
| 둘 다 병행 | 유연하다 | 관측/표준화 비용이 든다 | 마이그레이션 기간 |

핵심은 둘을 기능 차이가 아니라 **생명주기 차이**로 보는 것이다.

## 꼬리질문

> Q: RestClient와 WebClient의 가장 큰 차이는 무엇인가?
> 의도: 실행 모델 구분 확인
> 핵심: RestClient는 blocking, WebClient는 reactive다.

> Q: WebClient에서 block()이 왜 위험한가?
> 의도: reactive lifecycle 이해 확인
> 핵심: 체인의 장점을 깨고 스레드를 묶을 수 있다.

> Q: 관측 포인트가 왜 서로 다른가?
> 의도: instrumentation 차이 이해 확인
> 핵심: 실행 모델이 다르기 때문이다.

> Q: 인증/trace 헤더 전파가 왜 더 까다로운가?
> 의도: context propagation 이해 확인
> 핵심: 실행 모델마다 전파 방식이 다르다.

## 한 줄 정리

RestClient와 WebClient는 둘 다 HTTP client지만 blocking과 reactive lifecycle이 달라서 설정, 관측, 컨텍스트 전파를 같은 방식으로 다루면 안 된다.
