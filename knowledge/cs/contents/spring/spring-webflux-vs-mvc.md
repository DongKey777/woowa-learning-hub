# Spring MVC vs WebFlux

> 한 줄 요약: Spring MVC는 요청마다 스레드를 쓰는 단순한 모델이고, WebFlux는 적은 수의 이벤트 루프 스레드로 많은 연결을 다루기 위해 backpressure까지 포함한 비동기 모델이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)
> - [Spring Reactive-Blocking Bridge: `block()`, `boundedElastic`, and Boundary Traps](./spring-reactive-blocking-bridge-boundedelastic-block-traps.md)
> - [I/O 모델과 이벤트 루프](../operating-system/io-models-and-event-loop.md)
> - [컨텍스트 스위칭, 데드락, lock-free](../operating-system/context-switching-deadlock-lockfree.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)

retrieval-anchor-keywords: Spring MVC vs WebFlux, thread per request, event loop model, reactive backpressure, blocking call in WebFlux, ThreadLocal in WebFlux, servlet vs reactive stack, Reactor context propagation, WebFlux event loop blocked, when to choose WebFlux, WebFlux SSE, SseEmitter vs WebFlux SSE, Flux<ServerSentEvent>, reactive cancellation, servlet async timeout vs reactive stream lifetime

---

## 핵심 개념

Spring MVC와 WebFlux의 차이는 단순히 "동기 vs 비동기"가 아니다. 더 정확히는 **서버가 요청을 처리하기 위해 스레드를 어떻게 쓰는가**의 차이다.

Spring MVC는 전형적인 `thread-per-request` 모델이다.

- 요청 하나가 들어오면 보통 스레드 하나가 그 요청을 끝까지 처리한다.
- 서블릿 기반이라 기존 Spring 생태계와 궁합이 좋다.
- 블로킹 I/O와 JDBC 같은 전통적인 기술과 자연스럽게 맞는다.

WebFlux는 Reactor 기반의 리액티브 스택이다.

- 적은 수의 event-loop 스레드가 많은 연결을 multiplexing한다.
- 데이터가 준비되는 대로 비동기적으로 흘려보낸다.
- `Publisher`/`Subscriber` 사이의 backpressure로 소비 속도를 제어한다.

중요한 점은 WebFlux가 항상 더 빠른 게 아니라는 것이다.  
대기 시간이 긴 외부 I/O가 많고, 동시 연결 수가 크고, 블로킹을 피할 수 있을 때 의미가 커진다.

---

## 깊이 들어가기

### 1. MVC는 스레드를 점유한다

Spring MVC의 기본 모델은 이해하기 쉽다.

1. 요청이 들어온다.
2. 스레드 하나가 컨트롤러를 호출한다.
3. JDBC, REST 호출, 파일 I/O 같은 작업을 끝까지 기다린다.
4. 응답을 만든다.

이 구조의 장점은 단순성이다.

- 디버깅이 쉽다
- Java 스택 트레이스를 읽기 쉽다
- `ThreadLocal`, `SecurityContext`, `MDC` 같은 기존 패턴이 잘 맞는다
- 동기 코드와 레거시 라이브러리 재사용이 쉽다

단점은 요청 수가 많아질수록 스레드가 병목이 된다는 점이다.  
스레드는 공짜가 아니고, 너무 많이 늘리면 컨텍스트 스위칭과 메모리 사용이 커진다.

### 2. WebFlux는 event-loop 위에서 동작한다

WebFlux의 대표 실행 모델은 Netty 기반 event-loop다.

- 소수의 이벤트 루프 스레드가 소켓 이벤트를 감시한다.
- 논블로킹 I/O가 준비되면 콜백 체인으로 이어진다.
- 스레드를 오래 점유하는 작업이 있으면 전체 루프가 막힌다.

이 구조를 제대로 쓰려면 "빨리 끝나는 코드"가 아니라 "잠기지 않는 코드"를 써야 한다.

여기서 관련되는 OS 개념이 [I/O 모델과 이벤트 루프](../operating-system/io-models-and-event-loop.md)다.  
WebFlux를 쓰면서 내부에서 블로킹 호출을 해버리면 이벤트 루프 모델의 장점이 사라진다.

### 3. backpressure는 느린 소비자를 보호한다

리액티브 스트림의 핵심은 생산 속도와 소비 속도를 맞추는 것이다.

예를 들어 DB에서 데이터를 읽어와서 HTTP로 흘려보내는 상황을 생각해보자.

- 생산자가 너무 빠르면 버퍼가 터진다.
- 소비자가 너무 느리면 지연이 쌓인다.
- backpressure는 "이만큼만 더 보내라"는 신호로 이를 조절한다.

Reactor에서는 대략 이런 흐름으로 이해하면 된다.

```text
Publisher -> Subscriber
             ^       |
             | request(n)
```

이 개념은 대용량 스트리밍, SSE, 이벤트 전파 같은 상황에서 특히 중요하다.

### 4. ThreadLocal이 항상 통하지 않는다

MVC에서는 요청당 스레드가 상대적으로 고정적이라 `ThreadLocal`과 `SecurityContextHolder`가 잘 맞는다.  
WebFlux에서는 스레드가 바뀌기 쉬워서 같은 방식이 기대대로 동작하지 않을 수 있다.

그래서 다음 같은 습관이 위험해진다.

- 비즈니스 정보를 `ThreadLocal`에 숨겨두는 방식
- 블로킹 라이브러리를 몰래 섞는 방식
- MDC 로깅이 자동으로 유지된다고 가정하는 방식

WebFlux에서는 context 전파와 비동기 체인에 맞는 설계가 필요하다.

### 5. MVC와 WebFlux는 데이터 접근 방식도 다르게 봐야 한다

WebFlux는 풀 리액티브 스택을 쓸 때 가장 의미가 있다.

- `WebClient`
- reactive database driver
- reactive repository
- non-blocking HTTP client/server

반대로 WebFlux 컨트롤러 안에서 JDBC를 호출하면, 결국 블로킹 호출을 event-loop 위에 얹는 셈이다.  
그건 스레드 모델만 복잡하게 만들고 이점을 깎는다.

---

## 실전 시나리오

### 시나리오 1: 블로킹 호출 때문에 WebFlux가 느려진다

```java
@RestController
public class FeedController {
    private final LegacyFeedRepository repository;

    public FeedController(LegacyFeedRepository repository) {
        this.repository = repository;
    }

    @GetMapping("/feed")
    public Mono<List<FeedItem>> feed() {
        return Mono.fromSupplier(repository::findLatestFeed); // 내부가 JDBC면 블로킹
    }
}
```

이 코드는 겉으로는 reactive지만, 내부가 블로킹이면 event-loop를 잡아먹을 수 있다.  
이 경우 WebFlux를 쓴 이유가 약해진다.

### 시나리오 2: 동시 연결이 많고 응답이 대기 시간에 묶인다

예를 들어 SSE나 외부 API fan-out이 많은 대시보드, 알림 서버, proxy형 API에서는 WebFlux가 이득이 될 수 있다.

이때 중요한 것은 처리량만이 아니라 다음이다.

- 연결 유지 비용
- 느린 클라이언트에 대한 버퍼링
- timeout과 backpressure 정책
- 외부 서비스 지연에 대한 격리

### 시나리오 3: 디버깅이 어려워진다

리액티브 체인은 스택이 한 줄로 쭉 보이지 않는 경우가 많다.

- 에러가 다른 스레드와 시점에서 전파된다
- 로그 순서가 코드 순서와 다를 수 있다
- `block()`을 어디선가 호출하면 병목을 찾기 어렵다

운영에서 이건 실제 비용이다. "코드가 멋있다"와 "장애 때 빨리 원인을 찾는다"는 다르다.

---

## 코드로 보기

### MVC 예시

```java
@RestController
public class OrderController {
    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @GetMapping("/orders/{id}")
    public OrderResponse get(@PathVariable Long id) {
        Order order = orderService.findById(id); // 스레드가 여기서 기다린다
        return new OrderResponse(order.getId(), order.getStatus());
    }
}
```

### WebFlux 예시

```java
@RestController
public class ReactiveOrderController {
    private final ReactiveOrderService orderService;

    public ReactiveOrderController(ReactiveOrderService orderService) {
        this.orderService = orderService;
    }

    @GetMapping("/orders/{id}")
    public Mono<OrderResponse> get(@PathVariable Long id) {
        return orderService.findById(id)
                .map(order -> new OrderResponse(order.getId(), order.getStatus()));
    }
}
```

### backpressure 감각 예시

```java
Flux.range(1, 100)
    .onBackpressureBuffer(10)
    .publishOn(Schedulers.boundedElastic())
    .subscribe(System.out::println);
```

이런 코드는 단순 예시지만, 핵심은 "무한정 밀어 넣지 않는다"는 점이다.  
실서비스에서는 버퍼 정책, drop 정책, timeout을 함께 정해야 한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Spring MVC | 단순, 안정적, 디버깅 쉬움 | 대량 동시 연결에서 스레드 비용이 커짐 | 일반 CRUD, 레거시 통합, JDBC 중심 서비스 |
| WebFlux | 적은 스레드로 많은 연결 처리, 스트리밍에 유리 | 학습 곡선, 디버깅 비용, 블로킹 호환성 문제 | SSE, proxy, fan-out, 높은 동시성 I/O |
| MVC + 일부 비동기 | 점진적 도입 쉬움 | 모델이 섞여 복잡해질 수 있음 | 기존 시스템을 점진적으로 개선할 때 |
| 완전 reactive stack | 일관성 있는 비동기 흐름 | 전면 교체 비용이 큼 | 새로 시작하거나 비동기 경로가 핵심일 때 |

선택 기준은 보통 이렇다.

- 데이터 접근이 대부분 JDBC와 동기 라이브러리인가
- 동시 연결 수가 정말 많고 대기가 긴가
- 팀이 reactive 디버깅을 감당할 수 있는가
- 운영에서 thread dump보다 reactive chain 관찰이 더 중요한가

---

## 꼬리질문

> Q: WebFlux를 쓰면 무조건 더 빠른가?
> 의도: 성능을 "스레드 수" 하나로만 보지 않는지 확인
> 핵심: 블로킹 호출이 섞이면 이점이 사라지고, 팀 생산성까지 포함해서 봐야 한다

> Q: event-loop에서 블로킹 호출을 하면 왜 위험한가?
> 의도: event-loop의 공유성 이해 여부 확인
> 핵심: 적은 수의 스레드가 많은 연결을 처리하므로 하나가 막히면 전체 처리량이 흔들린다

> Q: backpressure는 왜 필요한가?
> 의도: 단순 비동기가 아니라 흐름 제어를 이해하는지 확인
> 핵심: 생산자와 소비자의 속도 차이를 제어하지 않으면 버퍼 폭증이나 지연 누적이 생긴다

> Q: WebFlux에서 `ThreadLocal`이 덜 잘 맞는 이유는?
> 의도: 기존 Spring 관성에서 벗어났는지 확인
> 핵심: 요청 처리 중 스레드가 바뀔 수 있어 전통적인 스레드 바인딩이 기대대로 유지되지 않는다

## 한 줄 정리

Spring MVC는 단순하고 운영이 쉽다. WebFlux는 동시 연결과 스트리밍에 강하지만, 블로킹 I/O와 섞이면 장점이 사라지고 디버깅 비용이 커진다.
