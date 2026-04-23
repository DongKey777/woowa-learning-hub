# Spring ApplicationEventMulticaster Internals

> 한 줄 요약: `ApplicationEventMulticaster`는 이벤트를 어디서 어떻게 fan-out할지 정하는 내부 허브이며, 동기/비동기/에러 처리 전략이 여기서 갈린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [옵저버, Pub/Sub, ApplicationEvent](../design-pattern/observer-pubsub-application-events.md)
> - [Spring EventListener, TransactionalEventListener, and Outbox](./spring-eventlistener-transaction-phase-outbox.md)
> - [Spring `@TransactionalEventListener` Outside Transactions and `fallbackExecution`](./spring-transactionaleventlistener-fallbackexecution-no-transaction-boundaries.md)
> - [Spring `@EventListener` Ordering and Async Traps](./spring-eventlistener-ordering-async-traps.md)
> - [Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls](./spring-transaction-synchronization-aftercommit-pitfalls.md)
> - [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)
> - [Spring SecurityContext Propagation Across Async and Reactive Boundaries](./spring-securitycontext-propagation-async-reactive-boundaries.md)

retrieval-anchor-keywords: ApplicationEventMulticaster, SimpleApplicationEventMulticaster, async event dispatch, event listener error handler, executor, event fan-out, application event publisher

## 핵심 개념

Spring 이벤트는 `ApplicationEventPublisher`가 던지고, `ApplicationEventMulticaster`가 받아서 여러 리스너로 나눈다.

즉, multicaster는 이벤트 처리의 중앙 허브다.

- 누구에게 보낼지
- 동기로 보낼지
- 비동기로 보낼지
- 실패를 어떻게 처리할지

이 결정을 담당한다.

## 깊이 들어가기

### 1. publisher와 multicaster는 다르다

Publisher는 이벤트 발행 API이고, multicaster는 실제 전달 전략이다.

### 2. `SimpleApplicationEventMulticaster`가 기본이다

기본 멀티캐스터는 대체로 단순하다.

- 리스너를 찾는다
- 순서대로 호출한다
- executor가 있으면 비동기로 보낼 수 있다

### 3. executor를 넣으면 전달 모델이 바뀐다

동기 실행은 호출자 스레드에서 이뤄지지만, executor가 있으면 별도 스레드에서 처리된다.

이 문맥은 [Spring `@EventListener` Ordering and Async Traps](./spring-eventlistener-ordering-async-traps.md)와 같이 봐야 한다.

### 4. 에러 핸들러가 없다면 장애가 숨어들 수 있다

이벤트 리스너가 실패하면 multicaster 설정에 따라 예외 전파와 로그 처리 양상이 달라진다.

### 5. 트랜잭션 이벤트와도 연결된다

`@TransactionalEventListener`는 결국 이벤트 전달 타이밍을 조절하는 상위 계약이다.

## 실전 시나리오

### 시나리오 1: 이벤트는 발행됐는데 리스너가 안 도는 것 같다

executor, listener registration, 조건부 bean 여부를 봐야 한다.

### 시나리오 2: 한 리스너 실패가 전체 발행을 망친다

동기 multicaster에서는 흔한 문제다.

### 시나리오 3: 비동기 리스너는 운영이 어렵다

fan-out은 쉬워지지만, 순서와 예외 관측이 어려워진다.

### 시나리오 4: 이벤트 폭주가 생긴다

multicaster는 메시지 큐가 아니므로 backpressure를 기대하면 안 된다.

## 코드로 보기

### custom multicaster bean

```java
@Bean
public ApplicationEventMulticaster applicationEventMulticaster(TaskExecutor executor) {
    SimpleApplicationEventMulticaster multicaster = new SimpleApplicationEventMulticaster();
    multicaster.setTaskExecutor(executor);
    return multicaster;
}
```

### event publish

```java
applicationEventPublisher.publishEvent(new OrderPlacedEvent(orderId));
```

### error handling hint

```java
multicaster.setErrorHandler(Throwable::printStackTrace);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 동기 multicaster | 단순하다 | 느린 리스너가 호출자를 막는다 | 작은 이벤트 |
| 비동기 multicaster | fan-out이 쉽다 | 순서/에러 추적이 어렵다 | 보조 후처리 |
| 큐 기반 전달 | 신뢰성이 높다 | 시스템이 하나 더 늘어난다 | 중요한 이벤트 |

핵심은 multicaster를 "이벤트 큐"가 아니라 **Spring 내부 전달 허브**로 보는 것이다.

## 꼬리질문

> Q: ApplicationEventPublisher와 ApplicationEventMulticaster의 차이는 무엇인가?
> 의도: 발행과 전달 구분 확인
> 핵심: publisher는 API, multicaster는 전달 전략이다.

> Q: executor가 multicaster에 붙으면 무엇이 바뀌는가?
> 의도: 동기/비동기 fan-out 이해 확인
> 핵심: 리스너 실행 스레드가 바뀐다.

> Q: 왜 multicaster에 backpressure를 기대하면 안 되는가?
> 의도: 이벤트 vs 큐 구분 확인
> 핵심: Spring 이벤트는 메시지 큐가 아니다.

> Q: 리스너 실패를 어디서 관측해야 하는가?
> 의도: 에러 핸들링 이해 확인
> 핵심: multicaster error handler와 리스너 로깅이 필요하다.

## 한 줄 정리

ApplicationEventMulticaster는 Spring 이벤트 fan-out의 내부 허브라서 동기/비동기/에러 정책을 여기서 먼저 결정해야 한다.
