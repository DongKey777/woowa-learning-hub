---
schema_version: 3
title: Spring @Async Context Propagation and RestClient / HTTP Interface Clients
concept_id: spring/async-context-propagation-restclient-http-interface-clients
canonical: true
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
review_feedback_tags:
- async-context-propagation
- restclient-http-interface
- clients
- taskdecorator
aliases:
- async context propagation
- TaskDecorator
- SecurityContext propagation
- MDC propagation
- RequestContextHolder ThreadLocal leak
- RestClient
- HTTP interface client
- @HttpExchange
intents:
- deep_dive
- troubleshooting
linked_paths:
- contents/spring/spring-scheduler-async-boundaries.md
- contents/spring/spring-taskexecutor-taskscheduler-overload-rejection-semantics.md
- contents/spring/spring-requestcontextholder-threadlocal-leakage-async-pools.md
- contents/spring/spring-security-architecture.md
- contents/spring/spring-observability-micrometer-tracing.md
- contents/spring/spring-webclient-vs-resttemplate.md
- contents/spring/spring-transaction-debugging-playbook.md
expected_queries:
- @Async에서 SecurityContext나 MDC가 사라지는 이유가 뭐야?
- TaskDecorator로 어떤 context를 옮겨야 해?
- RestClient와 HTTP interface client를 async 경계에서 쓸 때 주의할 점은?
- RequestContextHolder를 async pool로 넘기면 왜 leak 위험이 있어?
contextual_chunk_prefix: |
  이 문서는 @Async thread boundary와 RestClient/HTTP interface client 호출 경계를
  함께 다룬다. SecurityContext, MDC, Locale, RequestContextHolder,
  TransactionSynchronizationManager가 자동 전파되지 않는 문제, TaskDecorator,
  retry/fallback 책임 위치, ThreadLocal leakage를 설명하는 advanced deep dive다.
---
# Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients

> 한 줄 요약: `@Async`는 스레드 경계를 만들고, RestClient와 HTTP interface client는 호출 경계를 만든다. 둘 다 컨텍스트와 실패 처리를 설계하지 않으면 쉽게 새어 나간다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)
> - [Spring `TaskExecutor` / `TaskScheduler` Overload, Queue, and Rejection Semantics](./spring-taskexecutor-taskscheduler-overload-rejection-semantics.md)
> - [Spring `RequestContextHolder`, `ThreadLocal`, and Request Context Leakage Across Async Pools](./spring-requestcontextholder-threadlocal-leakage-async-pools.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring Observability with Micrometer Tracing](./spring-observability-micrometer-tracing.md)
> - [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)

retrieval-anchor-keywords: async context propagation, task decorator, security context, MDC, locale context, RestClient, HTTP interface client, @HttpExchange, proxy factory, RequestContextHolder, threadlocal leak, executor overload

## 핵심 개념

`@Async`와 HTTP 클라이언트는 둘 다 경계를 넘는다.

- `@Async`는 같은 JVM 안에서 다른 스레드로 넘어간다
- RestClient는 동기 HTTP 호출 경계를 넘는다
- HTTP interface client는 선언형 프록시로 HTTP 호출 경계를 감싼다

이 경계를 넘는 순간, 자동으로 따라오던 것들은 대부분 사라진다.

- `SecurityContext`
- `MDC`
- Locale
- 트랜잭션 컨텍스트
- retry/fallback의 책임 위치

즉, 이 문서의 핵심은 "어떤 API를 쓰느냐"보다 **어떤 컨텍스트가 어디까지 살아남는가**다.

## 깊이 들어가기

### 1. `@Async`는 실행 스레드를 바꾼다

`@Async`가 붙은 메서드는 호출 스레드가 아니라 executor 스레드에서 실행된다.

그래서 다음이 끊길 수 있다.

- `SecurityContextHolder`
- `MDC`
- `TransactionSynchronizationManager`
- request-scoped 객체

```text
caller thread
  -> async proxy
  -> executor thread
  -> task body
```

이 문맥은 [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)와 이어진다.

### 2. context propagation은 자동이 아니다

스레드가 바뀌어도 "같은 사용자 요청"이라는 의미가 유지되길 원하면, 직접 옮겨야 한다.

가장 흔한 수단은 `TaskDecorator`다.

```java
@Bean
public ThreadPoolTaskExecutor applicationTaskExecutor() {
    ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
    executor.setCorePoolSize(8);
    executor.setMaxPoolSize(32);
    executor.setQueueCapacity(500);
    executor.setTaskDecorator(new ContextCopyingTaskDecorator());
    executor.initialize();
    return executor;
}
```

### 3. `RestClient`는 동기식 HTTP 클라이언트다

`RestClient`는 Spring 6에서 제공하는 현대적인 동기 HTTP 클라이언트다.

좋은 점은 다음이다.

- API가 간결하다
- 요청/응답 커스터마이징이 쉽다
- `RestTemplate`보다 새 프로젝트에 맞다

하지만 동기식이라는 사실은 그대로다.

- 호출 스레드는 기다린다
- timeout이 중요하다
- retry를 무심코 붙이면 스레드 점유가 늘어난다

### 4. HTTP interface client는 선언형 프록시다

HTTP interface client는 인터페이스와 애너테이션으로 outbound client를 선언한다.

```java
@HttpExchange("/orders")
public interface OrderClient {

    @GetExchange("/{id}")
    OrderDto getOrder(@PathVariable Long id);

    @PostExchange
    void createOrder(@RequestBody CreateOrderRequest request);
}
```

이 인터페이스는 런타임에 proxy로 구현된다.

- 메서드 시그니처는 API 계약이 된다
- 구현 코드는 proxy factory가 생성한다
- 테스트 더블과 계약이 분리된다

이건 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)과 비슷한 감각으로 보면 이해가 쉽다.

### 5. async 안에서 HTTP 호출을 하면 컨텍스트 전파가 더 중요해진다

예를 들어 사용자 토큰을 헤더에 넣어야 하는데 `@Async`로 넘어가면, `SecurityContext`가 사라져 헤더를 만들 수 없다.

이 경우는 단순히 client 선택 문제가 아니라 다음이 같이 필요하다.

- executor context propagation
- outbound header mapping
- timeout
- fallback or retry ownership

즉, 비동기 처리와 HTTP 호출을 섞으면 boundary가 두 개가 된다.

## 실전 시나리오

### 시나리오 1: `@Async` 안에서 인증 정보가 사라진다

```java
@Async
public CompletableFuture<Void> sendMail() {
    Authentication auth = SecurityContextHolder.getContext().getAuthentication();
    // null일 수 있다
    return CompletableFuture.completedFuture(null);
}
```

이 문제는 TaskDecorator나 `DelegatingSecurityContextAsyncTaskExecutor` 계열로 해결해야 한다.

### 시나리오 2: async 작업의 실패가 호출자에게 전달되지 않는다

`@Async`는 호출자에게 결과를 동기적으로 던지지 않는다.

- 성공/실패를 따로 기록해야 한다
- future를 확인해야 한다
- fire-and-forget이면 관측성을 더 넣어야 한다

### 시나리오 3: RestClient 호출은 간단하지만 timeout이 없다

동기 HTTP 호출은 가장 흔한 병목이다.

- connect timeout
- read timeout
- write timeout
- connection pool timeout

이것들이 없으면 앱 스레드가 조용히 묶인다.

### 시나리오 4: HTTP interface client를 썼는데도 운영은 복잡하다

프록시가 API를 감싸주지만 다음은 여전히 직접 설계해야 한다.

- 에러 매핑
- retry 여부
- idempotency
- trace header 주입
- fallback 정책

즉, 인터페이스 client는 코드를 단순하게 만들지만 운영 책임을 지워 주지는 않는다.

## 코드로 보기

### context propagation decorator

```java
public class ContextCopyingTaskDecorator implements TaskDecorator {

    @Override
    public Runnable decorate(Runnable runnable) {
        Map<String, String> contextMap = MDC.getCopyOfContextMap();
        SecurityContext securityContext = SecurityContextHolder.getContext();

        return () -> {
            try {
                if (contextMap != null) {
                    MDC.setContextMap(contextMap);
                }
                SecurityContextHolder.setContext(securityContext);
                runnable.run();
            } finally {
                MDC.clear();
                SecurityContextHolder.clearContext();
            }
        };
    }
}
```

### `@Async` service

```java
@Service
public class NotificationService {

    @Async("applicationTaskExecutor")
    public CompletableFuture<Void> sendAsync(Long userId) {
        log.info("send notification to {}", userId);
        return CompletableFuture.completedFuture(null);
    }
}
```

### RestClient bean

```java
@Bean
public RestClient restClient(RestClient.Builder builder) {
    return builder
        .baseUrl("https://api.example.com")
        .requestInterceptor((request, body, execution) -> {
            request.getHeaders().add("X-Trace-Id", TraceContext.currentTraceId());
            return execution.execute(request, body);
        })
        .build();
}
```

### HTTP interface client factory

```java
@Bean
public OrderClient orderClient(RestClient restClient) {
    HttpServiceProxyFactory factory = HttpServiceProxyFactory
        .builderFor(RestClientAdapter.create(restClient))
        .build();
    return factory.createClient(OrderClient.class);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `@Async` | 간단히 비동기화할 수 있다 | 컨텍스트 전파와 실패 처리가 어렵다 | 부수 작업 |
| 큐/워크 큐 | 재시도와 복구가 쉽다 | 인프라가 늘어난다 | 중요한 비동기 |
| `RestClient` | 동기 호출이 단순하다 | 스레드를 점유한다 | 전통적인 blocking 서비스 |
| HTTP interface client | 계약이 명확하고 코드가 짧다 | 운영 정책이 숨겨질 수 있다 | outbound API가 많을 때 |

핵심은 도구가 아니라 **경계의 소유권**이다.

## 꼬리질문

> Q: `@Async` 안에서 `SecurityContext`가 왜 사라지는가?
> 의도: 스레드 로컬 컨텍스트 이해 확인
> 핵심: 실행 스레드가 바뀌기 때문이다.

> Q: `TaskDecorator`는 무엇을 해결하는가?
> 의도: 컨텍스트 전파 방법 이해 확인
> 핵심: MDC나 security context를 새 스레드로 복사한다.

> Q: RestClient와 HTTP interface client는 어떤 관계인가?
> 의도: 동기 클라이언트와 프록시 기반 선언형 client 구분 확인
> 핵심: interface client는 RestClient/WebClient 위에 얹는 프록시 계층이다.

> Q: `@Async`와 HTTP 호출을 함께 쓸 때 무엇이 가장 먼저 터질 수 있는가?
> 의도: 운영상 실패 모드 이해 확인
> 핵심: context loss, timeout 부족, 실패 관측성 부족이다.

## 한 줄 정리

`@Async`와 HTTP client는 둘 다 경계를 넘기 때문에, 컨텍스트 전파와 timeout, 에러 소유권을 같이 설계해야 한다.
