---
schema_version: 3
title: Spring Request Lifecycle Timeout Disconnect Cancellation Bridges
concept_id: spring/request-lifecycle-timeout-disconnect-cancellation-bridges
canonical: true
category: spring
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 88
review_feedback_tags:
- request-lifecycle-timeout
- disconnect-cancellation-bridges
- request-timeout-disconnect
- cancellation
aliases:
- Spring request timeout disconnect cancellation
- client disconnect broken pipe Spring MVC
- 499 in Spring application
- AsyncRequestTimeoutException
- response commit timeout budget
- servlet cancellation boundary
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/spring/spring-mvc-request-lifecycle.md
- contents/spring/spring-mvc-async-deferredresult-callable-dispatch.md
- contents/spring/spring-handlermethodreturnvaluehandler-chain.md
- contents/spring/spring-requestbody-responsebodyadvice-pipeline.md
- contents/spring/spring-onceperrequestfilter-async-error-dispatch-traps.md
- contents/spring/spring-problemdetail-before-after-commit-matrix.md
- contents/spring/spring-servlet-container-disconnect-exception-mapping.md
- contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
confusable_with:
- spring/mvc-request-lifecycle
- spring/mvc-async-deferredresult-callable-dispatch
- spring/onceperrequestfilter-async-error-dispatch-traps
- spring/problemdetail-before-after-commit-matrix
symptoms:
- 애플리케이션 로그에는 broken pipe가 남지만 실제 원인은 client disconnect처럼 보인다.
- upstream timeout budget이 Spring async timeout보다 짧아 499 또는 gateway timeout이 먼저 난다.
- response commit 이후 예외가 ProblemDetail로 바뀌지 않고 write failure로 끝난다.
expected_queries:
- Spring MVC에서 499 broken pipe client disconnect를 어떻게 해석해?
- timeout budget과 Spring async timeout은 어떤 순서로 맞춰야 해?
- response commit 이후 cancel이나 disconnect가 나면 애플리케이션 버그로 봐야 해?
- Servlet lifecycle과 network lifecycle을 같이 봐야 하는 이유는?
contextual_chunk_prefix: |
  이 문서는 Spring MVC 요청 lifecycle을 controller code만이 아니라 timeout budget,
  async redispatch, response commit, client disconnect, proxy 499와 연결해서 진단한다.
  broken pipe를 애플리케이션 예외와 network cancellation으로 나누는 router 역할을 한다.
---
# Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges

> 한 줄 요약: Spring MVC 요청은 컨트롤러 로직만으로 끝나지 않고 timeout budget, async redispatch, response commit, client disconnect가 함께 얽히므로, 499나 broken pipe를 애플리케이션 버그와 구분하려면 Spring lifecycle과 네트워크 lifecycle을 같이 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
> - [Spring `HandlerMethodReturnValueHandler` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
> - [Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline](./spring-requestbody-responsebodyadvice-pipeline.md)
> - [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](./spring-onceperrequestfilter-async-error-dispatch-traps.md)
> - [Spring `BasicErrorController`, `ErrorAttributes`, and Whitelabel Error Boundaries](./spring-basicerrorcontroller-errorattributes-whitelabel-boundaries.md)
> - [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
> - [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [Network-Spring Request Lifecycle Timeout / Disconnect Bridge](../network/network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](../network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
> - [gRPC Deadlines, Cancellation Propagation](../network/grpc-deadlines-cancellation-propagation.md)
> - [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
> - [Spring WebClient Connection Pool and Timeout Tuning](./spring-webclient-connection-pool-timeout-tuning.md)

retrieval-anchor-keywords: request timeout, client disconnect, 499, broken pipe, cancellation, response commit, flushBuffer, async timeout, servlet request lifecycle, timeout budget, disconnect bridge, ttfb, zombie work, webclient timeout, grpc deadline propagation, StreamingResponseBody, SseEmitter, client abort, ClientAbortException, EofException, ClosedChannelException, AsyncRequestNotUsableException, DisconnectedClientHelper, ALB idle timeout, nginx proxy_read_timeout, CDN streaming timeout, EventSource retry

## 핵심 개념

요청 처리 실패를 볼 때 개발자는 보통 컨트롤러 예외부터 떠올린다.

하지만 실제 운영에서는 다음이 더 자주 얽힌다.

- upstream timeout budget 소진
- client disconnect
- servlet async timeout
- response commit 이후 write 실패
- proxy가 먼저 연결을 닫아 499처럼 보이는 상황

즉 Spring request lifecycle은 애플리케이션 메서드 호출만이 아니라, **네트워크 연결 수명과 timeout budget 위에 얹힌 실행 경로**다.

## 깊이 들어가기

### 1. 요청은 애플리케이션 안팎에서 동시에 끝날 수 있다

Spring 입장에서 요청은 `DispatcherServlet` 안에서 처리된다.

하지만 네트워크 입장에선 다음 계층도 함께 존재한다.

- browser/mobile client
- CDN / LB / gateway
- app server / servlet container

그래서 "요청이 왜 실패했나"를 볼 때는 Spring 내부 예외만이 아니라, **누가 먼저 timeout이나 disconnect를 결정했는지**를 같이 봐야 한다.

### 2. timeout budget는 app server에 도착할 때 이미 줄어든 상태일 수 있다

서비스 메서드가 3초 걸렸다고 해도 실제론:

- gateway timeout 2초
- app read timeout 5초
- async timeout 3초

처럼 여러 예산이 겹친다.

따라서 Spring에서 예외가 안 나도, upstream에서 먼저 끊으면 client 입장에선 실패다.

즉 timeout 디버깅은 메서드 실행 시간보다, **hop별 budget과 누가 먼저 포기했는지**를 보는 작업이다.

### 3. client disconnect와 broken pipe는 "응답 쓰는 중"에 자주 드러난다

서버 로직은 정상처럼 끝났는데 마지막 write 시점에 다음이 생길 수 있다.

- broken pipe
- connection reset
- write aborted

이건 대개 서버가 잘못 계산했다기보다, **클라이언트나 중간 프록시가 이미 연결을 닫았는데 서버가 늦게 쓰려 한 결과**다.

즉 비즈니스 예외와 같은 층으로 보면 안 된다.

특히 이 "응답 쓰는 중"은 컨트롤러 메서드 바깥에서 벌어진다.

- `HandlerMethodReturnValueHandler`가 body 또는 streaming 경로를 고른다
- `ResponseBodyAdvice`와 `HttpMessageConverter`가 실제 write를 진행한다
- 첫 flush나 다음 chunk write에서 disconnect가 드러난다

즉 disconnect 관측 지점은 controller return보다 뒤쪽이다.

### 4. MVC async에서는 timeout과 cancellation 경계가 더 분리된다

`DeferredResult`, `Callable`, `WebAsyncTask`를 쓰면:

- 원래 요청 스레드는 빨리 반환
- 나중에 다른 스레드에서 결과 준비
- timeout이나 disconnect는 그 사이에 먼저 올 수 있음

즉 async MVC에서는 "작업이 끝났다"와 "응답을 아직 쓸 수 있다"가 같은 말이 아니다.

그래서 async timeout handler, cancellation callback, disconnect observability가 중요해진다.

### 5. response commit 이후에는 에러 처리 방식이 달라진다

헤더/상태 코드가 이미 나간 뒤엔, 그 다음 실패를 보통 정상적인 JSON error contract로 바꾸기 어렵다.

즉 다음을 구분해야 한다.

- 응답 쓰기 전 실패 -> resolver/advice/error path가 개입 가능
- 응답 commit 후 실패 -> 이미 HTTP 계약 일부가 밖으로 나감

이 차이를 모르면 "왜 어떤 예외는 ProblemDetail인데 어떤 건 그냥 socket error지?"가 이해되지 않는다.

streaming 응답은 이 경계를 더 앞당긴다.

- `StreamingResponseBody`, `SseEmitter`는 첫 바이트를 일찍 보내며 commit될 수 있다
- 이후 실패는 애플리케이션 예외라기보다 열린 응답 채널의 write 실패처럼 보인다

### 6. cancellation은 실패이기도 하고 정상 종료이기도 하다

모든 disconnect를 서버 장애로 보면 noisy alert가 된다.

예:

- 사용자가 페이지를 닫았다
- upstream가 더 짧은 timeout으로 먼저 포기했다
- SSE/streaming 연결이 자연스럽게 종료됐다

즉 cancellation은 **비즈니스 실패, 인프라 실패, 정상 종료**를 구분해야 한다.

## 실전 시나리오

### 시나리오 1: 앱 로그는 정상인데 gateway에서는 504가 난다

app 내부보다 upstream timeout budget이 더 짧았을 수 있다.

### 시나리오 2: 비즈니스 로직은 성공했는데 broken pipe가 뜬다

응답 write 시점 이전에 client/proxy가 연결을 닫았을 가능성이 높다.

특히 controller는 이미 끝났고, converter나 stream writer가 나중에 실패했을 수 있다.

### 시나리오 3: async API에서 timeout handler가 먼저 실행되고 나중에 worker는 완료된다

async MVC에선 작업 완료와 응답 가능성이 같은 뜻이 아니기 때문이다.

### 시나리오 4: 499가 많이 보이는데 서버 CPU는 멀쩡하다

느린 응답, client impatience, gateway timeout, streaming disconnect를 함께 봐야 한다.

### 시나리오 5: SSE는 잘 시작되는데 몇 분 뒤 write error가 간헐적으로 난다

초기 commit 이후 client가 탭을 닫거나 중간 프록시 idle timeout이 먼저 만료됐을 수 있다.

## 코드로 보기

### async timeout 처리

```java
DeferredResult<ResponseEntity<OrderResponse>> result = new DeferredResult<>(2_000L);
result.onTimeout(() -> result.setErrorResult(ResponseEntity.status(504).build()));
```

### disconnect/broken pipe는 write 시점 문제일 수 있음

```text
business work done
-> response headers/body write
-> socket already closed
-> broken pipe / connection reset
```

### 관측 질문

```text
1. 누가 먼저 timeout을 결정했는가?
2. 응답은 commit 전이었는가 후였는가?
3. client/gateway disconnect였는가 app 예외였는가?
4. async worker 완료와 실제 response write 시점은 분리됐는가?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단순 app 예외 중심 디버깅 | 빠르게 시작할 수 있다 | timeout/disconnect 원인을 놓치기 쉽다 | 초기 가설 확인 |
| hop별 timeout budget 추적 | 진짜 종료 지점을 찾기 쉽다 | 관측 데이터가 더 필요하다 | p95/p99 timeout 문제 |
| async timeout/cancel callback 명시 | 늦은 응답을 더 잘 제어한다 | 상태 전이가 복잡해진다 | async MVC, streaming |
| disconnect를 전부 에러로 취급 | 보수적이다 | noisy alert와 오탐이 많아진다 | 권장하지 않음 |

핵심은 request failure를 "컨트롤러가 던진 예외"로만 보지 않고, **Spring lifecycle과 네트워크 lifecycle이 만나는 지점에서 해석하는 것**이다.

## 꼬리질문

> Q: 앱 로그엔 정상인데 gateway에서 timeout이 나는 이유는 무엇인가?
> 의도: hop별 timeout budget 이해 확인
> 핵심: upstream의 timeout budget이 앱 내부보다 먼저 소진될 수 있기 때문이다.

> Q: broken pipe는 왜 비즈니스 예외와 다르게 봐야 하는가?
> 의도: write-time disconnect 이해 확인
> 핵심: 응답을 쓰는 시점에 peer가 이미 연결을 닫았을 가능성이 크기 때문이다.

> Q: 왜 disconnect는 controller return 직후보다 converter/streaming write에서 더 자주 드러나는가?
> 의도: response commit과 관측 시점 이해 확인
> 핵심: 네트워크 peer 종료는 실제 바이트를 쓰거나 flush할 때 비로소 관측되는 경우가 많기 때문이다.

> Q: async MVC에서 작업 완료와 응답 가능성이 왜 같은 말이 아닌가?
> 의도: async lifecycle 이해 확인
> 핵심: worker 완료 전후에 timeout/disconnect가 먼저 올 수 있기 때문이다.

> Q: cancellation을 모두 장애로 보면 왜 안 좋은가?
> 의도: 정상 종료와 실패 구분 확인
> 핵심: 사용자 종료, upstream 포기, 자연스러운 stream 종료까지 모두 noisy error로 섞이기 때문이다.

## 한 줄 정리

Spring request failure는 애플리케이션 예외만이 아니라 timeout budget, disconnect, response commit 시점까지 같이 봐야 제대로 보인다.
