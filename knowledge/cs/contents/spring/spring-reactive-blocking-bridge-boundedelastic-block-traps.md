# Spring Reactive-Blocking Bridge: `block()`, `boundedElastic`, and Boundary Traps

> 한 줄 요약: reactive와 blocking을 섞는다고 무조건 잘못은 아니지만, 어디서 `block()`하고 어떤 작업을 `boundedElastic`로 밀어내는지 경계를 명확히 하지 않으면 event-loop를 막거나 reactive 장점 없이 복잡도만 가져오게 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring WebFlux vs MVC](./spring-webflux-vs-mvc.md)
> - [Spring RestClient vs WebClient Lifecycle Boundaries](./spring-restclient-vs-webclient-lifecycle-boundaries.md)
> - [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
> - [Spring SecurityContext Propagation Across Async and Reactive Boundaries](./spring-securitycontext-propagation-async-reactive-boundaries.md)
> - [Spring WebClient Connection Pool and Timeout Tuning](./spring-webclient-connection-pool-timeout-tuning.md)

retrieval-anchor-keywords: block, boundedElastic, reactive blocking bridge, WebFlux blocking call, event loop blocked, subscribeOn, publishOn, bridge boundary, legacy blocking integration

## 핵심 개념

실무에서는 reactive와 blocking을 완전히 분리하지 못하는 경우가 많다.

- WebFlux 위에서 legacy blocking client를 써야 한다
- WebClient를 쓰지만 결국 어떤 경계에서 `block()`해야 한다
- MVC 서비스가 reactive client를 일부만 도입한다

문제는 혼합 그 자체가 아니라, **경계를 어디에 두는지 불명확한 상태**다.

다음 같은 상태가 특히 위험하다.

- 아무 데서나 `block()`
- event-loop 위에서 blocking I/O
- `boundedElastic`로 밀었지만 다시 다른 지점에서 block
- reactive chain으로 감쌌지만 실질적으론 전부 blocking

즉 reactive-blocking bridge의 핵심은 "섞을 수 있느냐"가 아니라, **어디서 execution model을 바꾸고 그 비용을 누가 감당하는지 명시하는 것**이다.

## 깊이 들어가기

### 1. `block()`은 기술적으로 가능해도 경계 선언이 필요하다

`block()`은 나쁘다는 슬로건으로만 이해하면 실무 감각이 떨어진다.

정확히는:

- reactive chain 내부의 애매한 중간 지점에서 `block()` -> 매우 위험
- 끝단 boundary에서 명시적으로 `block()` -> 전환기에는 현실적인 선택일 수 있음

즉 `block()`의 문제는 호출 그 자체보다, **어디서 어떤 스레드 위에서 호출했는가**다.

### 2. event-loop 위의 blocking은 가장 비싼 실수다

WebFlux/Netty의 핵심은 event-loop thread를 오래 점유하지 않는 것이다.

그런데 다음이 끼면 곧장 장점이 무너진다.

- JDBC
- legacy SDK
- 파일 I/O
- remote call의 동기 대기

이걸 event-loop 위에서 직접 호출하면, 적은 수의 event-loop가 막혀 전체 처리량과 지연이 급격히 나빠질 수 있다.

### 3. `boundedElastic`은 만능 해결책이 아니라 blocking isolation zone이다

Reactor에서 blocking 호출을 감싸며 자주 등장하는 패턴:

```java
Mono.fromCallable(() -> legacyClient.call())
    .subscribeOn(Schedulers.boundedElastic());
```

이건 "reactive로 변환"이라기보다, **blocking 작업을 별도 scheduler 영역으로 격리하는 것**에 가깝다.

좋은 점:

- event-loop를 덜 막는다
- blocking bridge 위치를 코드에 드러낸다

주의할 점:

- downstream에서 다시 block하면 의미가 약해진다
- blocking call이 많아지면 boundedElastic도 자원이 필요하다
- context propagation과 timeout 설계는 여전히 필요하다

### 4. `subscribeOn`과 `publishOn`은 execution boundary 의미가 다르다

대략 감각은 이렇다.

- `subscribeOn`: source 쪽 실행 scheduler를 바꾸는 데 가깝다
- `publishOn`: 이후 체인의 실행 scheduler를 바꾸는 데 가깝다

혼합 시스템에서는 이 차이를 모르고 "일단 scheduler 하나 넣기"가 흔한데, 그러면 어떤 구간이 blocking isolation zone인지 불분명해진다.

즉 scheduler 변경은 성능 미세튜닝보다, **어느 구간이 어떤 실행 모델 위에 있는지 선언하는 작업**이다.

### 5. MVC에서 WebClient를 쓰고 끝에서 `block()`하는 건 전환기 패턴일 수 있다

MVC 서비스에서 WebClient를 쓰되 controller/service가 동기 API면, 끝에서 `block()`하는 구조가 생길 수 있다.

이건 자동으로 잘못은 아니다.

다만 분명히 해야 한다.

- 현재 이 경계는 blocking boundary다
- reactive 장점은 일부만 가져온다
- timeout/connection pool/관측은 still critical하다

즉 "WebClient를 썼으니 reactive 시스템이다"는 착각을 피해야 한다.

### 6. reactive-blocking bridge는 컨텍스트 전파와 에러 모델도 바꾼다

execution model이 바뀌면 다음도 함께 달라진다.

- `ThreadLocal` 기반 컨텍스트
- SecurityContext 모델
- MDC 로깅
- stack trace와 에러 전파 감각

즉 bridge는 I/O 방식 전환만이 아니라, **관측성/보안/디버깅 모델까지 같이 바꾸는 경계**다.

## 실전 시나리오

### 시나리오 1: WebFlux endpoint가 가끔씩만 심하게 느려진다

event-loop 위에 숨은 blocking call이 있는지 먼저 봐야 한다.

### 시나리오 2: WebClient를 썼는데 결국 service 끝에서 매번 `block()`한다

전환기엔 현실적일 수 있지만, 시스템 전체가 reactive가 된 것은 아니다.

이 경계를 명시하고 운영 비용을 따져야 한다.

### 시나리오 3: `boundedElastic`로 감쌌는데도 여전히 이상하다

blocking 구간은 옮겼지만,

- 다시 다른 지점에서 block했거나
- context propagation/timeout이 빠졌거나
- boundedElastic 자체도 과도하게 사용 중일 수 있다

### 시나리오 4: reactive chain 안 디버깅이 너무 어렵다

애매한 bridge가 많을수록 "어디서 모델이 바뀌는지"가 보이지 않아 장애 대응이 더 어려워진다.

## 코드로 보기

### 위험한 event-loop 위 blocking

```java
@GetMapping("/orders/{id}")
public Mono<OrderResponse> get(@PathVariable Long id) {
    Order order = legacyOrderClient.find(id); // blocking
    return Mono.just(OrderResponse.from(order));
}
```

### blocking isolation zone

```java
public Mono<OrderResponse> find(Long id) {
    return Mono.fromCallable(() -> legacyOrderClient.find(id))
        .subscribeOn(Schedulers.boundedElastic())
        .map(OrderResponse::from);
}
```

### MVC boundary에서 명시적 block

```java
public OrderResponse findSync(Long id) {
    return webClient.get()
        .uri("/orders/{id}", id)
        .retrieve()
        .bodyToMono(OrderResponse.class)
        .block();
}
```

이 코드는 blocking boundary를 분명히 인정한 전환기 패턴이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| pure MVC/blocking | 단순하고 디버깅이 쉽다 | 대기 시간이 긴 고동시성 I/O엔 약할 수 있다 | 대부분의 전통적 백엔드 |
| pure reactive | I/O concurrency에 강하다 | 학습과 운영 모델이 달라진다 | non-blocking 경계를 끝까지 유지할 수 있을 때 |
| bridge + `boundedElastic` | 전환기 현실성이 높다 | reactive 장점이 일부만 남고 경계 관리가 중요하다 | legacy blocking 통합 |
| 무분별한 `block()` 혼합 | 당장은 쉽다 | 병목과 모델 혼합이 숨어든다 | 가급적 피함 |

핵심은 reactive와 blocking을 섞지 말라는 구호보다, **bridge boundary를 코드와 운영 모델에 명시하는 것**이다.

## 꼬리질문

> Q: `block()`이 항상 나쁜 것은 아닌 이유는 무엇인가?
> 의도: 경계 중심 이해 확인
> 핵심: 끝단 경계에서 명시적으로 쓰는 전환기 패턴은 가능하지만, 중간에서 무분별하게 쓰는 것이 위험하다.

> Q: `boundedElastic`의 역할은 무엇인가?
> 의도: scheduler 의미 확인
> 핵심: blocking 작업을 event-loop 밖의 별도 scheduler 영역으로 격리하는 것이다.

> Q: WebClient를 쓰는데도 시스템이 reactive라고 보기 어려운 경우는 언제인가?
> 의도: client choice vs execution model 구분 확인
> 핵심: 결국 주요 경계에서 계속 `block()`하며 동기 모델로 쓰고 있을 때다.

> Q: reactive-blocking bridge가 디버깅을 어렵게 만드는 이유는 무엇인가?
> 의도: execution model 혼합의 비용 확인
> 핵심: 어느 지점에서 스레드, 컨텍스트, 에러 모델이 바뀌는지 흐려지기 때문이다.

## 한 줄 정리

reactive와 blocking을 섞는다고 틀린 것은 아니지만, `block()`과 scheduler 전환의 경계를 명시하지 않으면 복잡도만 늘고 모델 이점은 사라진다.
