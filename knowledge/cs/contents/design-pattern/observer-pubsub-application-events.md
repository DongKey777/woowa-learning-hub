# 옵저버, Pub/Sub, ApplicationEvent

> 한 줄 요약: 상태 변화 통지를 느슨하게 연결하는 패턴이지만, 동기/비동기, 순서 보장, 실패 전파 방식에 따라 완전히 다른 시스템이 된다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [Observer(옵저버) 디자인 패턴](./observer.md)
> - [옵저버 vs Pub-Sub: 처음 읽을 때 바로 잡는 짧은 다리](./observer-vs-pubsub-quick-bridge.md)
> - [Mediator vs Observer vs Pub/Sub](./mediator-vs-observer-vs-pubsub.md)
> - [Observer Lifecycle Hygiene](./observer-lifecycle-hygiene.md)
> - [Spring `@EventListener` vs `@TransactionalEventListener`: Timing, Ordering, Rollback](./spring-eventlistener-vs-transactionaleventlistener-timing.md)
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
> - [Tolerant Reader for Event Contracts](./tolerant-reader-event-contract-pattern.md)
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
> - [Idempotent Consumer and Projection Dedup Pattern](./idempotent-consumer-projection-dedup-pattern.md)
> - [Spring EventListener, TransactionalEventListener, and Outbox](../spring/spring-eventlistener-transaction-phase-outbox.md)
> - [Spring `@EventListener` Ordering and Async Traps](../spring/spring-eventlistener-ordering-async-traps.md)
> - [Spring ApplicationEventMulticaster Internals](../spring/spring-applicationeventmulticaster-internals.md)
> - [Spring OAuth2 + JWT 통합](../spring/spring-oauth2-jwt-integration.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)
> - [Webhook Signature Verification / Replay Defense](../security/webhook-signature-verification-replay-defense.md)
> - [Event Bus Control Plane 설계](../system-design/event-bus-control-plane-design.md)
> - [캐시, 메시징, 관측성](../software-engineering/cache-message-observability.md)

retrieval-anchor-keywords: observer vs pubsub, observer vs pubsub beginner, same process notification vs broker async propagation, spring applicationevent, application event listener, synchronous vs asynchronous event, event ordering, event failure propagation, transactional event listener boundary, eventlistener vs transactionaleventlistener, after commit after rollback, event-driven decoupling, duplicate event handling, event publish subscribe semantics, observer pubsub application events basics

---

## 핵심 개념

옵저버 패턴은 한 객체의 변화가 다른 객체들에 자동으로 전파되도록 만드는 구조다.
Pub/Sub는 그 개념을 확장한 모델이고, `ApplicationEvent`는 Spring이 제공하는 내부 이벤트 전달 메커니즘이다.

이 셋은 겉모습은 비슷하지만 초점이 다르다.

- 옵저버: 객체 간 직접적인 상태 통지
- Pub/Sub: 발행자와 구독자를 주제(topic)로 느슨하게 분리
- ApplicationEvent: 스프링 컨테이너 내부에서 빈 간 이벤트 전달

중요한 것은 "누가 누구를 아느냐"가 아니라, **언제, 어떤 순서로, 실패를 어떻게 다룰 것이냐**다.
같은 프로세스 안에서 중앙 조율, 단순 notification, brokered messaging을 한 번에 비교하고 싶다면 [Mediator vs Observer vs Pub/Sub](./mediator-vs-observer-vs-pubsub.md)를 같이 보면 경계가 더 빨리 선다.

---

## 깊이 들어가기

### 1. 옵저버와 Pub/Sub는 같은 게 아니다

옵저버는 주체가 관찰자를 직접 알고 있는 경우가 많다.
Pub/Sub는 발행자와 구독자가 중간 브로커를 통해 분리된다.

| 구분 | 옵저버 | Pub/Sub |
|---|---|---|
| 결합도 | 비교적 낮음 | 더 낮음 |
| 전달 경로 | 직접 호출 | 브로커/버스 경유 |
| 실패 전파 | 호출 체인에 영향 | 브로커 정책에 따름 |
| 확장성 | 제한적 | 좋음 |

### 2. Spring `ApplicationEvent`는 어디에 가까운가

Spring 이벤트는 내부적으로는 옵저버 느낌이지만, 사용 감각은 Pub/Sub에 가깝다.
발행자는 리스너 구현을 직접 몰라도 된다.

문제는 이것이 "자동으로 안전한 비동기 처리"가 아니라는 점이다.

- 기본은 동기 처리다
- 비동기 리스너로 바꾸면 트랜잭션 경계가 바뀐다
- 실패 시 재시도/롤백 전략이 별도로 필요하다

특히 Spring 내부 옵저버를 쓸 때는 `@EventListener`와 `@TransactionalEventListener`가 같은 "이벤트 리스너"처럼 보여도
타이밍과 롤백 의미가 다르다. 이 부분은 [Spring `@EventListener` vs `@TransactionalEventListener`: Timing, Ordering, Rollback](./spring-eventlistener-vs-transactionaleventlistener-timing.md)에서 따로 정리했다.
반대로 UI, plugin host, 수동 emitter처럼 리스너 등록을 직접 관리하는 구조에서는 unsubscribe와 duplicate-registration hygiene를 직접 설계해야 한다. 이 부분은 [Observer Lifecycle Hygiene](./observer-lifecycle-hygiene.md)에서 다룬다.

### 3. 이벤트는 편하지만 순서를 잃기 쉽다

이벤트 기반 설계는 모듈 분리에는 좋지만, 다음 문제를 만든다.

- 순서가 중요할 때 깨질 수 있다
- 이벤트 중복이 생길 수 있다
- 리스너가 늘수록 장애 파악이 어려워진다
- "어떤 이벤트가 실제로 처리됐는가"를 추적해야 한다

그래서 이벤트는 기능보다 **운영 방식**이 먼저 정해져야 한다.

---

## 실전 시나리오

### 시나리오 1: 주문 완료 후 알림 발송

주문 서비스는 주문만 끝내고, 알림/포인트/로그는 이벤트로 분리할 수 있다.

장점:
- 주문 로직이 얇아진다
- 후속 처리를 독립적으로 바꿀 수 있다
- 기능 추가가 이벤트 리스너 추가로 끝난다

주의:
- 주문은 커밋됐는데 알림이 실패할 수 있다
- 반대로 알림만 중복 발송될 수 있다

### 시나리오 2: Spring Security 인증 성공 이벤트

인증 성공 후 감사 로그나 사용자 마지막 로그인 시간을 갱신하는 데 유용하다.
하지만 인증 흐름에 핵심적인 정합성은 이벤트에 맡기면 안 된다.

### 시나리오 3: 메트릭과 캐시 무효화

캐시 무효화나 메트릭 집계는 이벤트와 잘 맞는다.
실패해도 다시 계산 가능하고, 약간의 지연이 허용되기 때문이다.

---

## 코드로 보기

### 1. Spring ApplicationEvent

```java
public record OrderCompletedEvent(Long orderId, Long userId) {}

@Service
public class OrderService {
    private final ApplicationEventPublisher publisher;

    public OrderService(ApplicationEventPublisher publisher) {
        this.publisher = publisher;
    }

    @Transactional
    public void completeOrder(Long orderId, Long userId) {
        // 주문 상태 변경
        publisher.publishEvent(new OrderCompletedEvent(orderId, userId));
    }
}

@Component
public class OrderNotificationListener {
    @EventListener
    public void handle(OrderCompletedEvent event) {
        // 알림 전송
    }
}
```

### 2. 비동기 리스너 주의

```java
@Async
@EventListener
public void handle(OrderCompletedEvent event) {
    // 트랜잭션 스레드가 아니다
}
```

비동기로 바꾸는 순간:

- 실행 순서가 바뀔 수 있다
- 예외 전파 방식이 달라진다
- 트랜잭션 컨텍스트가 자동으로 따라오지 않는다

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| 직접 호출 | 단순하고 추적이 쉽다 | 결합도가 높다 | 핵심 정합성 처리 |
| 옵저버 | 구조가 분리된다 | 호출 체인이 길어진다 | 내부 상태 통지 |
| Pub/Sub | 확장성이 좋다 | 운영/추적 비용이 커진다 | 비동기 확장 |
| ApplicationEvent | Spring과 잘 맞는다 | 기본 동기 동작을 오해하기 쉽다 | 같은 컨테이너 내부 이벤트 |

핵심 기준은 간단하다.
**정합성이 중요한 일은 직접 호출, 느슨한 부가 작업은 이벤트**로 나누는 편이 안전하다.

---

## 꼬리질문

> Q: Spring 이벤트는 왜 발행자와 리스너를 느슨하게 분리하는데도 조심해서 써야 하나요?
> 의도: 이벤트를 구조 분리 도구로만 보고, 트랜잭션/순서/실패를 놓치지 않는지 확인
> 핵심: 결합도는 낮아지지만 운영 복잡도는 올라간다

> Q: 옵저버와 Pub/Sub를 같은 것으로 설명해도 되나요?
> 의도: 브로커 유무와 전달 경로 차이를 구분하는지 확인
> 핵심: 둘은 비슷하지만 결합 구조와 확장 방식이 다르다

## 한 줄 정리

옵저버, Pub/Sub, ApplicationEvent는 모두 "변화 전파"를 다루지만, 실제 설계에서는 결합도보다 순서, 실패, 트랜잭션 경계를 먼저 정해야 한다.
